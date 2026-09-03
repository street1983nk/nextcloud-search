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
 * Behaviours 4 and 5 of docs/testing.md, section "The gap".
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

	private function provider(): Provider {
		return new Provider(
			$this->l10n,
			$this->urlGenerator,
			$this->exApp,
			$this->rootFolder,
			$this->mountCache,
			$this->fileAccess,
			$this->logger,
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
