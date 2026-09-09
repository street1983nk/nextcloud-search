<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\ApprovedHit;
use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\SearchCaps;
use OCA\Findling\Service\SearchOutcome;
use OCA\Findling\Service\SearchService;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\IUser;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * Behaviours 4, 5, 10 and half of 11 of docs/testing.md, section "The twelve
 * behaviours of the PHP half".
 *
 * They used to be asserted against Provider and they moved here with plan
 * 09-03, without changing a single statement of the loop they are about: the
 * recheck now lives in one shared service, so the cases about the recheck live
 * next to it. What stayed in ProviderTest is what the provider still does,
 * which is translating and rendering.
 *
 * Behaviour 4 is the recheck: a candidate becomes a hit only when this user's
 * own folder resolves its file id, and the fields the user finally reads come
 * out of the resolved node rather than out of the answer of the container, so a
 * confused or compromised backend cannot put the name of a foreign file in
 * front of anyone. Behaviour 5 is the same rule at the point where it is
 * easiest to get wrong: a user without a home folder cannot be asked the
 * permission question at all, and the only safe answer to a question that
 * cannot be asked is nothing.
 *
 * Behaviour 10 is what keeps a search bounded: a limited number of questions, a
 * ceiling on the node resolutions, and a wall clock that ends the asking. Since
 * this plan all four of those are arguments rather than constants, so every
 * case below writes down the number it asserts against instead of reading it
 * out of the class: that is the whole point of the parametrisation, and a test
 * that read the caps back out of the service would agree with any number at
 * all. Behaviour 11 is the order in which the two calls happen, and it is
 * asserted over the order of the mock calls rather than over the result: an
 * excerpt is file content, and a result assertion would stay green if the two
 * calls swapped places.
 *
 * Four cases are new in this plan and are about the two states the own result
 * page has to tell apart: a cursor past the paging ceiling of the container,
 * which is not a broken backend, and a backend that really did answer nothing.
 * The fourth is the third field of a hit, the mime type, which is new here and
 * comes out of the same confirmed node as the other two.
 *
 * Everything below runs on mocks. No database, no file system, no network: the
 * user folder, the node, the mount cache and the service of the container are
 * all doubles, and that is what makes these statements about the code rather
 * than about an instance.
 */
#[CoversClass(SearchService::class)]
final class SearchServiceTest extends TestCase {
	private ExAppService&MockObject $exApp;
	private IRootFolder&MockObject $rootFolder;
	private IUserMountCache&MockObject $mountCache;
	private IFileAccess&MockObject $fileAccess;
	private LoggerInterface&MockObject $logger;

	protected function setUp(): void {
		parent::setUp();

		$this->exApp = $this->createMock(ExAppService::class);
		$this->rootFolder = $this->createMock(IRootFolder::class);
		$this->mountCache = $this->createMock(IUserMountCache::class);
		$this->fileAccess = $this->createMock(IFileAccess::class);
		$this->logger = $this->createMock(LoggerInterface::class);

		// No lockstep drift on record. Anything else and the service declines
		// before it gets anywhere near a candidate, which would make every
		// assertion below pass for the wrong reason.
		$this->exApp->method('driftOnRecord')->willReturn(null);
	}

	/**
	 * @param (\Closure(): float)|null $clock null keeps the real monotonic clock,
	 *                                        which is what every case that says
	 *                                        nothing about time wants
	 */
	private function service(?\Closure $clock = null): SearchService {
		return new SearchService(
			$this->exApp,
			$this->rootFolder,
			$this->mountCache,
			$this->fileAccess,
			$this->logger,
			$clock,
		);
	}

	/**
	 * The ceilings of one run, with the numbers of the search dialog as the
	 * default and every one of them overridable by the case that is about it.
	 */
	private function caps(
		int $pageSize = 20,
		int $maxRounds = 3,
		int $overfetch = 4,
		int $recheckPerHit = 2,
		int $recheckAbsolute = 64,
		float $budgetSeconds = 2.5,
		float $requestCeilingSeconds = 1.5,
	): SearchCaps {
		return new SearchCaps(
			$pageSize,
			$maxRounds,
			$overfetch,
			$recheckPerHit,
			$recheckAbsolute,
			$budgetSeconds,
			$requestCeilingSeconds,
		);
	}

	private function user(string $uid = 'testuser'): IUser&MockObject {
		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn($uid);

		return $user;
	}

	/**
	 * @param list<array<string,mixed>> $candidates
	 * @return array{candidates:list<array<string,mixed>>,hasMore:bool,nextOffset:int,degraded:bool}
	 */
	private function page(array $candidates): array {
		return [
			'candidates' => $candidates,
			'hasMore' => false,
			'nextOffset' => count($candidates),
			'degraded' => false,
		];
	}

	/**
	 * A page that says there is more behind it, which is what keeps the loop
	 * asking until one of the bounds ends it.
	 *
	 * @param list<array<string,mixed>> $candidates
	 * @return array{candidates:list<array<string,mixed>>,hasMore:bool,nextOffset:int,degraded:bool}
	 */
	private function pageWithMore(array $candidates, int $nextOffset): array {
		return [
			'candidates' => $candidates,
			'hasMore' => true,
			'nextOffset' => $nextOffset,
			'degraded' => false,
		];
	}

	/**
	 * @return list<array{fileId:int}>
	 */
	private function candidates(int $count): array {
		$candidates = [];
		for ($i = 0; $i < $count; $i++) {
			$candidates[] = ['fileId' => 1000 + $i];
		}

		return $candidates;
	}

	/**
	 * A constant of the class under test, read rather than copied. Same rule and
	 * same reason as in ExAppServiceTest: a bound written into this file is a
	 * bound that keeps being asserted after somebody moved it in the class. It
	 * is used for the one number that is still a constant of the service, the
	 * mirrored paging ceiling; the four caps are arguments now and are written
	 * out by the case that asserts them.
	 */
	private function constantInt(string $name, string $class = SearchService::class): int {
		$value = (new \ReflectionClass($class))->getConstant($name);

		self::assertIsInt($value, $name . ' is gone or is no longer an int');

		return $value;
	}

	/**
	 * A file that resolves and may be read, with a name, a path and a type of
	 * its own.
	 */
	private function readableFile(
		string $name = 'Report.pdf',
		string $mimeType = 'application/pdf',
		string $folder = 'Board',
	): File&MockObject {
		$file = $this->createMock(File::class);
		$file->method('isReadable')->willReturn(true);
		$file->method('getName')->willReturn($name);
		$file->method('getPath')->willReturn('/testuser/files/' . $folder . '/' . $name);
		$file->method('getMimetype')->willReturn($mimeType);

		return $file;
	}

	/**
	 * A user folder that resolves nothing, so no candidate ever becomes a hit and
	 * the loop is only ever stopped by one of its bounds.
	 */
	private function folderResolvingNothing(?int &$resolved = null): void {
		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->willReturnCallback(
			static function () use (&$resolved): ?File {
				$resolved = ($resolved ?? 0) + 1;

				return null;
			},
		);

		$this->rootFolder->method('getUserFolder')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);
	}

	// -- behaviour 4 ---------------------------------------------------------

	public function testACandidateWhoseNodeTheUsersOwnFolderCannotResolveNeverBecomesAHit(): void {
		$file = $this->readableFile();

		$userFolder = $this->createMock(Folder::class);
		// 11 resolves, 22 does not. Not visible, no longer visible, moved to the
		// trash and never existed are deliberately the same answer here, so a hit
		// cannot be used to probe for files this user may not see.
		$userFolder->method('getFirstNodeById')->willReturnMap([
			[11, $file],
			[22, null],
		]);
		$userFolder->method('getRelativePath')->willReturn('/Board/Report.pdf');

		$this->rootFolder->method('getUserFolder')->with('testuser')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);
		$this->exApp->method('searchCandidates')->willReturn($this->page([
			['fileId' => 11],
			['fileId' => 22],
		]));
		$this->exApp->method('snippets')->willReturn([]);

		$outcome = $this->service()->run($this->user(), 'quarterly report', false, 0, $this->caps());

		self::assertCount(1, $outcome->hits);
		self::assertSame(11, $outcome->hits[0]->fileId);
		self::assertNull($outcome->failure);
	}

	public function testTheTitleAndThePathComeOutOfTheResolvedNodeAndNotOutOfTheContainerAnswer(): void {
		$file = $this->readableFile('Quartalsbericht.pdf', 'application/pdf', 'Vorstand');

		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->willReturn($file);
		$userFolder->method('getRelativePath')->willReturn('/Vorstand/Quartalsbericht.pdf');

		$this->rootFolder->method('getUserFolder')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);

		// The candidate carries a name and a text of its own. A well behaved
		// container does not send them, filterCandidates strips them if it does,
		// and this is the third line of the same defence: even handed straight to
		// the service they change nothing about what the user reads.
		$this->exApp->method('searchCandidates')->willReturn($this->page([
			['fileId' => 11, 'title' => 'Gehaltsliste des Vorstands.pdf', 'snippet' => 'a foreign excerpt'],
		]));
		$this->exApp->method('snippets')->willReturn([]);

		$outcome = $this->service()->run($this->user(), 'quarterly report', false, 0, $this->caps());

		self::assertCount(1, $outcome->hits);
		self::assertSame('Quartalsbericht.pdf', $outcome->hits[0]->title);
		self::assertSame('Vorstand/Quartalsbericht.pdf', $outcome->hits[0]->path);
	}

	public function testTheMimeTypeOfAHitComesOutOfTheNodeAndNotOutOfTheContainerAnswer(): void {
		// New with plan 09-03, and the same statement as the two fields above:
		// the result page picks the file type icon from this string, so a
		// container that could set it could decide which icon a foreign name is
		// shown with.
		$file = $this->readableFile('Vertrag.odt', 'application/vnd.oasis.opendocument.text');

		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->willReturn($file);
		$userFolder->method('getRelativePath')->willReturn('/Board/Vertrag.odt');

		$this->rootFolder->method('getUserFolder')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);
		$this->exApp->method('searchCandidates')->willReturn($this->page([
			['fileId' => 11, 'mimeType' => 'application/x-executable'],
		]));
		$this->exApp->method('snippets')->willReturn([]);

		$outcome = $this->service()->run($this->user(), 'vertrag', false, 0, $this->caps());

		self::assertCount(1, $outcome->hits);
		self::assertSame('application/vnd.oasis.opendocument.text', $outcome->hits[0]->mimeType);
		self::assertStringNotContainsString('executable', $outcome->hits[0]->mimeType);
	}

	public function testANodeThatResolvesButIsNotReadableIsStillNotAHit(): void {
		// The stricter question of the same behaviour, and the one a team folder
		// makes necessary: the ACL wrapper of groupfolders hands out a node that
		// resolves perfectly well while the per folder rules take the read bit
		// away.
		$file = $this->createMock(File::class);
		$file->method('isReadable')->willReturn(false);
		$file->expects(self::never())->method('getName');

		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->willReturn($file);

		$this->rootFolder->method('getUserFolder')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);
		$this->exApp->method('searchCandidates')->willReturn($this->page([['fileId' => 11]]));

		$outcome = $this->service()->run($this->user(), 'quarterly report', false, 0, $this->caps());

		self::assertSame([], $outcome->hits);
	}

	// -- behaviour 5 ---------------------------------------------------------

	public function testAUserWithoutAHomeFolderGetsNoHitsAndNotUncheckedOnes(): void {
		// Every failure of getUserFolder means the same thing here: no permission
		// decision is possible. The bug this asserts against is not an exception
		// escaping into a caller, it is the tempting alternative of passing on
		// what the container proposed.
		$this->rootFolder->method('getUserFolder')
			->willThrowException(new \RuntimeException('no home folder for this user'));

		// The load bearing half of the assertion. An empty hit list could also
		// come from a container that found nothing; that the container is never
		// asked at all is what makes an unchecked hit impossible rather than
		// merely absent.
		$this->exApp->expects(self::never())->method('searchCandidates');
		$this->exApp->expects(self::never())->method('snippets');

		$outcome = $this->service()->run($this->user(), 'quarterly report', false, 0, $this->caps());

		self::assertSame([], $outcome->hits);
		self::assertSame(SearchOutcome::FAILURE_NO_HOME_FOLDER, $outcome->failure);
		self::assertFalse($outcome->hasMore);
	}

	public function testTheMissingHomeFolderIsLoggedWithoutNamingAnythingTheUserSearchedFor(): void {
		$this->rootFolder->method('getUserFolder')
			->willThrowException(new \RuntimeException('no home folder for this user'));

		$this->logger->expects(self::once())
			->method('warning')
			->with(
				'Findling: no home folder for this user, dropping every hit',
				self::callback(static fn (array $context): bool => array_keys($context) === ['exception']),
			);

		$this->service()->run($this->user(), 'quarterly report', false, 0, $this->caps());
	}

	public function testAVersionDriftOnRecordCostsTheRunAndIsNamedAsThat(): void {
		// D-11 as a state of this service rather than of one caller: with a
		// protocol break on record nothing is asked at all, and the reason
		// travels back so that a caller can say which of the empty answers this
		// one is.
		$exApp = $this->createMock(ExAppService::class);
		$exApp->method('driftOnRecord')->willReturn(['companion' => '1.0.3', 'container' => '1.1.0']);
		$exApp->expects(self::never())->method('searchCandidates');

		$service = new SearchService(
			$exApp,
			$this->rootFolder,
			$this->mountCache,
			$this->fileAccess,
			$this->logger,
			null,
		);

		$outcome = $service->run($this->user(), 'quarterly report', false, 0, $this->caps());

		self::assertSame([], $outcome->hits);
		self::assertSame(SearchOutcome::FAILURE_VERSION_DRIFT, $outcome->failure);
	}

	// -- behaviour 10: bounded questions, resolutions and a wall clock --------

	public function testTheServiceAsksAtMostAsOftenAsTheCapsAllow(): void {
		$rounds = 3;
		$this->folderResolvingNothing();

		// Every page is full, no candidate survives, and the backend keeps saying
		// there is more. Asking again is necessary, because the recheck can drop
		// enough candidates that too few are left; asking without a bound is the
		// failure mode that makes query time permission filtering unusable.
		$asked = 0;
		$this->exApp->method('searchCandidates')->willReturnCallback(
			function () use (&$asked): array {
				$asked++;

				return $this->pageWithMore($this->candidates(3), $asked * 3);
			},
		);

		$this->service()->run($this->user(), 'quarterly report', false, 0, $this->caps(maxRounds: $rounds));

		self::assertSame($rounds, $asked);
	}

	public function testALowerRoundCapReallyLowersTheNumberOfQuestions(): void {
		// The counter sample of the case above, and the reason it exists: with
		// only one number asserted, a service that ignored the cap and always
		// asked three times would look perfectly healthy.
		$this->folderResolvingNothing();

		$asked = 0;
		$this->exApp->method('searchCandidates')->willReturnCallback(
			function () use (&$asked): array {
				$asked++;

				return $this->pageWithMore($this->candidates(3), $asked * 3);
			},
		);

		$this->service()->run($this->user(), 'quarterly report', false, 0, $this->caps(maxRounds: 1));

		self::assertSame(1, $asked);
	}

	/**
	 * How many nodes one run resolved for a given set of caps.
	 */
	private function resolutionsFor(SearchCaps $caps): int {
		$resolved = 0;
		$this->folderResolvingNothing($resolved);

		// Far more candidates per page than any ceiling allows, so what stops the
		// loop can only be the ceiling and never the supply.
		$offset = 0;
		$this->exApp->method('searchCandidates')->willReturnCallback(
			function () use (&$offset): array {
				$offset += 500;

				return $this->pageWithMore($this->candidates(500), $offset);
			},
		);

		$this->service()->run($this->user(), 'quarterly report', false, 0, $caps);

		return $resolved;
	}

	public function testTheServiceResolvesAtMostTwoNodesPerDisplayedHitWhenThePageIsSmall(): void {
		$perHit = 2;
		$absolute = 64;

		// Every resolution is a query against oc_filecache, and the arithmetic the
		// ceiling prevents is the one without it: a page of 20, an overfetch of
		// four and three rounds would be up to 240 of them in a single run.
		$expected = min($absolute, 10 * $perHit);
		self::assertLessThan($absolute, $expected, 'the small page no longer sits below the absolute ceiling');

		self::assertSame($expected, $this->resolutionsFor($this->caps(
			pageSize: 10,
			recheckPerHit: $perHit,
			recheckAbsolute: $absolute,
		)));
	}

	public function testTheServiceResolvesAtMostTheAbsoluteCeilingWhenThePageIsLarge(): void {
		$perHit = 2;
		$absolute = 64;

		// The other side of the same min(): a large page must not reopen the hole
		// the per hit rule closed.
		self::assertGreaterThan($absolute, 100 * $perHit, 'the large page no longer reaches the absolute ceiling');

		self::assertSame($absolute, $this->resolutionsFor($this->caps(
			pageSize: 100,
			recheckPerHit: $perHit,
			recheckAbsolute: $absolute,
		)));
	}

	public function testTheServiceStopsAskingWhenTheWallClockIsUsedUp(): void {
		$budgetSeconds = 2.5;

		// The clock stands still except for the one thing that costs time here,
		// the round trip. No case in this suite waits: two and a half real seconds
		// would make the suite slow and would go flaky on a loaded runner.
		$now = 0.0;
		$clock = static function () use (&$now): float {
			return $now;
		};

		$this->folderResolvingNothing();

		$asked = 0;
		$this->exApp->method('searchCandidates')->willReturnCallback(
			function () use (&$asked, &$now, $budgetSeconds): array {
				$asked++;
				$now += $budgetSeconds * 1_000_000_000.0;

				return $this->pageWithMore($this->candidates(3), $asked * 3);
			},
		);

		$this->service($clock)->run(
			$this->user(),
			'quarterly report',
			false,
			0,
			$this->caps(maxRounds: 3, budgetSeconds: $budgetSeconds),
		);

		// One question and not three, even though two rounds are left and the
		// backend said there is more. The unified search waits for every provider,
		// so a fourth second spent here is a fourth second of the whole search.
		self::assertSame(1, $asked);
	}

	// -- behaviour 11: excerpts come after the recheck, and only then ---------

	public function testExcerptsAreOnlyRequestedAfterTheRecheck(): void {
		$file = $this->readableFile();

		$order = [];
		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->willReturnCallback(
			static function () use (&$order, $file): File {
				$order[] = 'recheck';

				return $file;
			},
		);
		$userFolder->method('getRelativePath')->willReturn('/Board/Report.pdf');

		$this->rootFolder->method('getUserFolder')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);

		$this->exApp->method('searchCandidates')->willReturnCallback(
			function () use (&$order): array {
				$order[] = 'candidates';

				return $this->page([['fileId' => 11], ['fileId' => 12]]);
			},
		);
		$this->exApp->method('snippets')->willReturnCallback(
			static function () use (&$order): array {
				$order[] = 'excerpts';

				return [];
			},
		);

		$this->service()->run($this->user(), 'quarterly report', false, 0, $this->caps());

		// The order and not the result, which is the whole point of this case. An
		// excerpt is file content, so it may not even exist before the permission
		// question has been answered; a case that only looked at what the user
		// finally reads would stay green if the two calls swapped places.
		self::assertSame(['candidates', 'recheck', 'recheck', 'excerpts'], $order);
	}

	public function testExcerptsAreRequestedOnlyForTheFileIdsThatSurvivedTheRecheck(): void {
		$readable = $this->readableFile();
		$unreadable = $this->createMock(File::class);
		$unreadable->method('isReadable')->willReturn(false);

		$userFolder = $this->createMock(Folder::class);
		// 11 survives, 22 does not resolve at all, 33 resolves without the read
		// bit, which is the team folder case.
		$userFolder->method('getFirstNodeById')->willReturnMap([
			[11, $readable],
			[22, null],
			[33, $unreadable],
		]);
		$userFolder->method('getRelativePath')->willReturn('/Board/Report.pdf');

		$this->rootFolder->method('getUserFolder')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);
		$this->exApp->method('searchCandidates')->willReturn($this->page([
			['fileId' => 11],
			['fileId' => 22],
			['fileId' => 33],
		]));

		$asked = null;
		$this->exApp->method('snippets')->willReturnCallback(
			static function (string $userId, string $term, array $fileIds) use (&$asked): array {
				$asked = $fileIds;

				return [];
			},
		);

		$this->service()->run($this->user(), 'quarterly report', false, 0, $this->caps());

		self::assertSame([11], $asked);
	}

	public function testWhenTheBudgetIsGoneNothingIsLeftToHandDownToTheExcerptCall(): void {
		$budgetSeconds = 2.5;
		$floor = (new \ReflectionClass(ExAppService::class))->getConstant('MIN_CALL_SECONDS');
		self::assertIsFloat($floor, 'MIN_CALL_SECONDS is gone or is no longer a float');

		$now = 0.0;
		$clock = static function () use (&$now): float {
			return $now;
		};

		$file = $this->readableFile();
		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->willReturn($file);
		$userFolder->method('getRelativePath')->willReturn('/Board/Report.pdf');

		$this->rootFolder->method('getUserFolder')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);

		// The one round trip of this run spends the whole wall clock.
		$this->exApp->method('searchCandidates')->willReturnCallback(
			function () use (&$now, $budgetSeconds): array {
				$now += $budgetSeconds * 1_000_000_000.0;

				return $this->page([['fileId' => 11]]);
			},
		);

		$handedDown = null;
		$this->exApp->method('snippets')->willReturnCallback(
			static function (string $userId, string $term, array $fileIds, bool $titleOnly, float $secondsLeft) use (&$handedDown): array {
				$handedDown = $secondsLeft;

				return [];
			},
		);

		$outcome = $this->service($clock)->run(
			$this->user(),
			'quarterly report',
			false,
			0,
			$this->caps(budgetSeconds: $budgetSeconds),
		);

		// This class hands down what is left of its wall clock, and below the floor
		// of ExAppService no call is placed at all; the case that asserts the
		// refusal itself is
		// ExAppServiceTest::testASpentBudgetCostsNoRoundTripForCandidatesAndNoneForExcerpts.
		// Splitting it that way is not a weakening: the two halves live in two
		// classes, and a case that claimed both here would have to pretend this
		// class decides something it does not.
		self::assertIsFloat($handedDown, 'the excerpt call was never reached, so nothing was handed down');
		self::assertLessThan($floor, $handedDown);

		// A hit without an excerpt beats no hit at all, so the hit survives and
		// the caller falls back to its path.
		self::assertCount(1, $outcome->hits);
		self::assertSame('Board/Report.pdf', $outcome->hits[0]->path);
	}

	public function testThePerCallCeilingOfTheCapsTravelsWithBothCalls(): void {
		// The caller decides how patient a single call may be, and both calls of
		// a run get the same answer. Without this case the field could be carried
		// around and never handed over, which is the shape a larger page budget
		// had before plan 09-01.
		$file = $this->readableFile();
		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->willReturn($file);
		$userFolder->method('getRelativePath')->willReturn('/Board/Report.pdf');

		$this->rootFolder->method('getUserFolder')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);

		$ceilings = [];
		$this->exApp->method('searchCandidates')->willReturnCallback(
			function (
				string $userId,
				string $term,
				int $limit,
				int $offset,
				bool $titleOnly,
				float $secondsLeft,
				float $ceilingSeconds,
			) use (&$ceilings): array {
				$ceilings[] = $ceilingSeconds;

				return $this->page([['fileId' => 11]]);
			},
		);
		$this->exApp->method('snippets')->willReturnCallback(
			static function (
				string $userId,
				string $term,
				array $fileIds,
				bool $titleOnly,
				float $secondsLeft,
				float $ceilingSeconds,
			) use (&$ceilings): array {
				$ceilings[] = $ceilingSeconds;

				return [];
			},
		);

		$this->service()->run(
			$this->user(),
			'quarterly report',
			false,
			0,
			$this->caps(requestCeilingSeconds: 4.5),
		);

		self::assertSame([4.5, 4.5], $ceilings);
	}

	// -- the paging ceiling and the silent backend, new with plan 09-03 -------

	public function testACursorBeyondTheOffsetCeilingEndsTheRunWithoutAskingAtAll(): void {
		$ceiling = $this->constantInt('MAX_CONTAINER_OFFSET');

		// Not one round trip, and that is the whole statement. The container
		// answers a deeper offset with a 422, which arrives here as nothing and
		// is indistinguishable from a backend that is down.
		$this->exApp->expects(self::never())->method('searchCandidates');
		$this->exApp->expects(self::never())->method('snippets');
		$this->rootFolder->method('getUserFolder')->willReturn($this->createMock(Folder::class));
		$this->mountCache->method('getMountsForUser')->willReturn([]);

		$outcome = $this->service()->run($this->user(), 'quarterly report', false, $ceiling + 1, $this->caps());

		self::assertSame(SearchOutcome::FAILURE_OFFSET_CEILING, $outcome->failure);
		self::assertSame([], $outcome->hits);

		// No next page is promised, because there is none that the container
		// would answer.
		self::assertFalse($outcome->hasMore);
	}

	public function testACursorAtTheOffsetCeilingIsStillAsked(): void {
		// The other side of the comparison, and the reason it is written down:
		// the container accepts the ceiling itself and refuses only what is
		// above it, so an off by one here would cost a whole page of hits.
		$ceiling = $this->constantInt('MAX_CONTAINER_OFFSET');
		$this->folderResolvingNothing();

		$asked = 0;
		$this->exApp->method('searchCandidates')->willReturnCallback(
			function () use (&$asked): array {
				$asked++;

				return $this->page([]);
			},
		);

		$outcome = $this->service()->run($this->user(), 'quarterly report', false, $ceiling, $this->caps());

		self::assertSame(1, $asked);
		self::assertNull($outcome->failure);
	}

	public function testABackendSilentOnTheFirstCallIsNamedAsThat(): void {
		$this->folderResolvingNothing();
		$this->exApp->method('searchCandidates')->willReturn(null);
		$this->exApp->expects(self::never())->method('snippets');

		$outcome = $this->service()->run($this->user(), 'quarterly report', false, 0, $this->caps());

		self::assertSame([], $outcome->hits);
		self::assertSame(SearchOutcome::FAILURE_BACKEND_SILENT, $outcome->failure);
	}

	public function testABackendThatGoesSilentAfterHitsCostsTheFollowUpAndNotTheHits(): void {
		$file = $this->readableFile();
		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->willReturn($file);
		$userFolder->method('getRelativePath')->willReturn('/Board/Report.pdf');

		$this->rootFolder->method('getUserFolder')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);

		// The first page carries a hit and says there is more, the second call
		// answers nothing at all.
		$asked = 0;
		$this->exApp->method('searchCandidates')->willReturnCallback(
			function () use (&$asked): ?array {
				$asked++;

				return $asked === 1 ? $this->pageWithMore([['fileId' => 11]], 1) : null;
			},
		);
		$this->exApp->method('snippets')->willReturn([]);

		$outcome = $this->service()->run($this->user(), 'quarterly report', false, 0, $this->caps());

		// An incomplete list beats an error message printed over hits the user
		// can see, so the silence is swallowed and the hit is shown.
		self::assertSame(2, $asked);
		self::assertCount(1, $outcome->hits);
		self::assertNull($outcome->failure);
	}

	public function testTheCanaryTravelsAsAHitOfItsOwnWithoutATypeAndWithoutAResolution(): void {
		// The diagnostic path of phase 1, and the one named exception to "every
		// field comes out of the node": there is no node, so its two fields are
		// the text the container composed and its type stays empty.
		$userFolder = $this->createMock(Folder::class);
		$userFolder->expects(self::never())->method('getFirstNodeById');

		$this->rootFolder->method('getUserFolder')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);
		$this->exApp->method('searchCandidates')->willReturn($this->page([
			['fileId' => 0, 'title' => 'findling-canary', 'snippet' => 'answered by findling-backend'],
		]));
		$this->exApp->expects(self::never())->method('snippets');

		$outcome = $this->service()->run($this->user(), 'findling-canary', false, 0, $this->caps());

		self::assertCount(1, $outcome->hits);
		self::assertInstanceOf(ApprovedHit::class, $outcome->hits[0]);
		self::assertSame(0, $outcome->hits[0]->fileId);
		self::assertSame('findling-canary', $outcome->hits[0]->title);
		self::assertSame('', $outcome->hits[0]->mimeType);
	}
}
