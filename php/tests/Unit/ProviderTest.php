<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Search\Provider;
use OCA\Findling\Service\ExAppService;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\IUser;
use OCP\Search\IFilter;
use OCP\Search\ISearchQuery;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * Behaviours 4, 5, 10 and 11 of docs/testing.md, section "The gap".
 *
 * These two are the security boundary of the product itself. Behaviour 4 is the
 * recheck: a candidate becomes a hit only when this user's own folder resolves
 * its file id, and the two fields the user finally reads come out of the
 * resolved node rather than out of the answer of the container, so a confused or
 * compromised backend cannot put the name of a foreign file in front of anyone.
 * Behaviour 5 is the same rule at the point where it is easiest to get wrong: a
 * user without a home folder cannot be asked the permission question at all, and
 * the only safe answer to a question that cannot be asked is nothing.
 *
 * Behaviours 10 and 11 arrived with plan 05-16 and are about cost and order.
 * Behaviour 10 is what keeps a search bounded: three questions at most, a
 * ceiling on the node resolutions, and a wall clock that ends the asking. The
 * clock is stood still and moved by hand through the optional clock argument of
 * the provider, because a case that waited two and a half real seconds would
 * make this suite slow and would go flaky on a loaded runner. Behaviour 11 is
 * the order in which the two calls happen, and it is asserted over the order of
 * the mock calls rather than over the result: an excerpt is file content, and a
 * result assertion would stay green if the two calls swapped places.
 *
 * Everything below runs on mocks. No database, no file system, no network: the
 * user folder, the node, the mount cache and the service are all doubles, and
 * that is what makes these statements about the code rather than about an
 * instance.
 */
#[CoversClass(Provider::class)]
final class ProviderTest extends TestCase {
	private IL10N&MockObject $l10n;
	private IURLGenerator&MockObject $urlGenerator;
	private ExAppService&MockObject $exApp;
	private IRootFolder&MockObject $rootFolder;
	private IUserMountCache&MockObject $mountCache;
	private IFileAccess&MockObject $fileAccess;
	private LoggerInterface&MockObject $logger;

	protected function setUp(): void {
		parent::setUp();

		$this->l10n = $this->createMock(IL10N::class);
		$this->l10n->method('t')->willReturnArgument(0);
		$this->urlGenerator = $this->createMock(IURLGenerator::class);
		$this->exApp = $this->createMock(ExAppService::class);
		$this->rootFolder = $this->createMock(IRootFolder::class);
		$this->mountCache = $this->createMock(IUserMountCache::class);
		$this->fileAccess = $this->createMock(IFileAccess::class);
		$this->logger = $this->createMock(LoggerInterface::class);

		// No lockstep drift on record. Anything else and the provider declines
		// before it gets anywhere near a candidate, which would make every
		// assertion below pass for the wrong reason.
		$this->exApp->method('driftOnRecord')->willReturn(null);
	}

	/**
	 * @param (\Closure(): float)|null $clock null keeps the real monotonic clock,
	 *                                        which is what every case that says
	 *                                        nothing about time wants
	 */
	private function provider(?\Closure $clock = null): Provider {
		return new Provider(
			$this->l10n,
			$this->urlGenerator,
			$this->exApp,
			$this->rootFolder,
			$this->mountCache,
			$this->fileAccess,
			$this->logger,
			$clock,
		);
	}

	private function user(string $uid = 'testuser'): IUser&MockObject {
		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn($uid);

		return $user;
	}

	private function query(string $term = 'quarterly report', int $limit = 20): ISearchQuery&MockObject {
		$query = $this->createMock(ISearchQuery::class);
		$query->method('getTerm')->willReturn($term);
		$query->method('getLimit')->willReturn($limit);
		$query->method('getFilter')->willReturn(null);
		$query->method('getCursor')->willReturn(null);

		return $query;
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
	 * @return list<array<string,mixed>>
	 */
	private function entriesOf(\OCP\Search\SearchResult $result): array {
		$serialised = $result->jsonSerialize();

		/** @var list<\OCP\Search\SearchResultEntry> $entries */
		$entries = $serialised['entries'];

		return array_map(static fn ($entry): array => $entry->jsonSerialize(), $entries);
	}

	// -- behaviour 4 ---------------------------------------------------------

	public function testACandidateWhoseNodeTheUsersOwnFolderCannotResolveNeverBecomesAHit(): void {
		$file = $this->createMock(File::class);
		$file->method('isReadable')->willReturn(true);
		$file->method('getName')->willReturn('Report.pdf');
		$file->method('getPath')->willReturn('/testuser/files/Board/Report.pdf');

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
		$this->urlGenerator->method('linkToRoute')->willReturn('/index.php/f/11');

		$entries = $this->entriesOf($this->provider()->search($this->user(), $this->query()));

		self::assertCount(1, $entries);
		self::assertSame('11', $entries[0]['attributes']['fileId']);
	}

	public function testTheTitleAndTheLinkComeOutOfTheResolvedNodeAndNotOutOfTheContainerAnswer(): void {
		$file = $this->createMock(File::class);
		$file->method('isReadable')->willReturn(true);
		$file->method('getName')->willReturn('Quartalsbericht.pdf');
		$file->method('getPath')->willReturn('/testuser/files/Vorstand/Quartalsbericht.pdf');

		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->willReturn($file);
		$userFolder->method('getRelativePath')->willReturn('/Vorstand/Quartalsbericht.pdf');

		$this->rootFolder->method('getUserFolder')->willReturn($userFolder);
		$this->mountCache->method('getMountsForUser')->willReturn([]);

		// The candidate carries a name and a text of its own. A well behaved
		// container does not send them, filterCandidates strips them if it does,
		// and this is the third line of the same defence: even handed straight to
		// the provider they change nothing about what the user reads.
		$this->exApp->method('searchCandidates')->willReturn($this->page([
			['fileId' => 11, 'title' => 'Gehaltsliste des Vorstands.pdf', 'snippet' => 'a foreign excerpt'],
		]));
		$this->exApp->method('snippets')->willReturn([]);

		// The link is built from the confirmed file id through the url generator,
		// which is asserted here rather than pattern matched on the string: what
		// matters is which id was routed, not how the route renders.
		$this->urlGenerator->expects(self::once())
			->method('linkToRoute')
			->with('files.View.showFile', ['fileid' => 11])
			->willReturn('/index.php/apps/files/?fileid=11');

		$entries = $this->entriesOf($this->provider()->search($this->user(), $this->query()));

		self::assertCount(1, $entries);
		self::assertSame('Quartalsbericht.pdf', $entries[0]['title']);
		self::assertSame('Vorstand/Quartalsbericht.pdf', $entries[0]['subline']);
		self::assertSame('/index.php/apps/files/?fileid=11', $entries[0]['resourceUrl']);
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

		self::assertSame([], $this->entriesOf($this->provider()->search($this->user(), $this->query())));
	}

	// -- behaviour 5 ---------------------------------------------------------

	public function testAUserWithoutAHomeFolderGetsAnEmptyResultAndNotUncheckedHits(): void {
		// Every failure of getUserFolder means the same thing here: no permission
		// decision is possible. The bug this asserts against is not an exception
		// escaping into the unified search, it is the tempting alternative of
		// showing what the container proposed.
		$this->rootFolder->method('getUserFolder')
			->willThrowException(new \RuntimeException('no home folder for this user'));

		// The load bearing half of the assertion. An empty entry list could also
		// come from a container that found nothing; that the container is never
		// asked at all is what makes an unchecked hit impossible rather than
		// merely absent.
		$this->exApp->expects(self::never())->method('searchCandidates');
		$this->exApp->expects(self::never())->method('snippets');

		$result = $this->provider()->search($this->user(), $this->query());

		self::assertSame([], $this->entriesOf($result));
		self::assertFalse($result->jsonSerialize()['isPaginated']);
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

		$this->provider()->search($this->user(), $this->query());
	}

	public function testAnEmptyTermIsNotEvenAskedAbout(): void {
		// The cheapest neighbour of behaviour 5, and it belongs next to it: the
		// dialog sends an empty term while the user is still typing, and neither
		// the home folder nor the container is touched for it.
		$this->rootFolder->expects(self::never())->method('getUserFolder');
		$this->exApp->expects(self::never())->method('searchCandidates');

		$result = $this->provider()->search($this->user(), $this->query('   '));

		self::assertSame([], $this->entriesOf($result));
	}

	// -- behaviour 10: three questions, a resolution ceiling, a wall clock ----

	/**
	 * A constant of the class under test, read rather than copied. Same rule and
	 * same reason as in ExAppServiceTest: a bound written into this file is a
	 * bound that keeps being asserted after somebody moved it in the class.
	 */
	private function constantInt(string $name, string $class = Provider::class): int {
		$value = (new \ReflectionClass($class))->getConstant($name);

		self::assertIsInt($value, $name . ' is gone or is no longer an int');

		return $value;
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
	 * A page that says there is more behind it, which is what keeps the loop
	 * asking until one of the three bounds ends it.
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

	public function testTheProviderAsksAtMostThreeTimes(): void {
		$rounds = $this->constantInt('MAX_ROUNDS');
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

		$this->provider()->search($this->user(), $this->query());

		self::assertSame($rounds, $asked);
	}

	/**
	 * How many nodes one search resolved for a given display limit.
	 */
	private function resolutionsFor(int $limit): int {
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

		$this->provider()->search($this->user(), $this->query('quarterly report', $limit));

		return $resolved;
	}

	public function testTheProviderResolvesAtMostTwoNodesPerDisplayedHitWhenTheLimitIsSmall(): void {
		$perHit = $this->constantInt('MAX_RECHECKS_PER_HIT');
		$absolute = $this->constantInt('MAX_RECHECKS_ABSOLUTE');

		// Every resolution is a query against oc_filecache, and the arithmetic the
		// ceiling prevents is the one without it: a limit of 20, an overfetch of
		// four and three rounds would be up to 240 of them in a single search.
		$expected = min($absolute, 10 * $perHit);
		self::assertLessThan($absolute, $expected, 'the small limit no longer sits below the absolute ceiling');

		self::assertSame($expected, $this->resolutionsFor(10));
	}

	public function testTheProviderResolvesAtMostTheAbsoluteCeilingWhenTheLimitIsLarge(): void {
		$perHit = $this->constantInt('MAX_RECHECKS_PER_HIT');
		$absolute = $this->constantInt('MAX_RECHECKS_ABSOLUTE');

		// The other side of the same min(): a large limit must not reopen the hole
		// the per hit rule closed.
		self::assertGreaterThan($absolute, 100 * $perHit, 'the large limit no longer reaches the absolute ceiling');

		self::assertSame($absolute, $this->resolutionsFor(100));
	}

	public function testTheProviderStopsAskingWhenTheWallClockIsUsedUp(): void {
		$budget = $this->constantInt('BUDGET_NANOSECONDS');
		$rounds = $this->constantInt('MAX_ROUNDS');
		self::assertGreaterThan(1, $rounds, 'with a single round the case below would prove nothing about the clock');

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
			function () use (&$asked, &$now, $budget): array {
				$asked++;
				$now += $budget;

				return $this->pageWithMore($this->candidates(3), $asked * 3);
			},
		);

		$this->provider($clock)->search($this->user(), $this->query());

		// One question and not three, even though two rounds are left and the
		// backend said there is more. The unified search waits for every provider,
		// so a fourth second spent here is a fourth second of the whole search.
		self::assertSame(1, $asked);
	}

	// -- behaviour 11: excerpts come after the recheck, and only then ---------

	/**
	 * A file that resolves and may be read, with a name and a path of its own.
	 */
	private function readableFile(string $name = 'Report.pdf'): File&MockObject {
		$file = $this->createMock(File::class);
		$file->method('isReadable')->willReturn(true);
		$file->method('getName')->willReturn($name);
		$file->method('getPath')->willReturn('/testuser/files/Board/' . $name);

		return $file;
	}

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
		$this->urlGenerator->method('linkToRoute')->willReturn('/index.php/f/11');

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

		$this->provider()->search($this->user(), $this->query());

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
		$this->urlGenerator->method('linkToRoute')->willReturn('/index.php/f/11');
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

		$this->provider()->search($this->user(), $this->query());

		self::assertSame([11], $asked);
	}

	public function testWhenTheBudgetIsGoneNoExcerptCanBeFetchedAndTheSublineIsThePath(): void {
		$budget = $this->constantInt('BUDGET_NANOSECONDS');
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
		$this->urlGenerator->method('linkToRoute')->willReturn('/index.php/f/11');

		// The one round trip of this search spends the whole wall clock.
		$this->exApp->method('searchCandidates')->willReturnCallback(
			function () use (&$now, $budget): array {
				$now += $budget;

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

		$entries = $this->entriesOf($this->provider($clock)->search($this->user(), $this->query()));

		// This class hands down what is left of its wall clock, and below the floor
		// of ExAppService no call is placed at all; the case that asserts the
		// refusal itself is
		// ExAppServiceTest::testASpentBudgetCostsNoRoundTripForCandidatesAndNoneForExcerpts.
		// Splitting it that way is not a weakening: the two halves live in two
		// classes, and a case that claimed both here would have to pretend the
		// provider decides something it does not.
		self::assertIsFloat($handedDown, 'the excerpt call was never reached, so nothing was handed down');
		self::assertLessThan($floor, $handedDown);

		// A hit without an excerpt beats no hit at all, so the path takes over.
		self::assertCount(1, $entries);
		self::assertSame('Board/Report.pdf', $entries[0]['subline']);
	}

	public function testTheProviderDeclaresBothBuiltinFiltersSoTheDialogNeverSkipsIt(): void {
		// Not one of the twelve, and one line, because a provider that is skipped
		// for an undeclared filter looks exactly like a broken backend: no error,
		// no entry, no hint.
		self::assertSame(
			[IFilter::BUILTIN_TERM, IFilter::BUILTIN_TITLE_ONLY],
			$this->provider()->getSupportedFilters(),
		);
	}
}
