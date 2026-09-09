<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Search\Provider;
use OCA\Findling\Service\ApprovedHit;
use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\SearchCaps;
use OCA\Findling\Service\SearchOutcome;
use OCA\Findling\Service\SearchService;
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
 * What the provider still does after plan 09-03, which is nothing that decides.
 *
 * The recheck and every question about permissions moved into
 * OCA\Findling\Service\SearchService, and the cases about them moved with it
 * into SearchServiceTest. Three jobs are left here and all three are
 * translations: a query of the dialog becomes arguments of the shared service,
 * the constants of the dialog become a SearchCaps, and what comes back becomes
 * SearchResultEntry. Behaviour 11 of docs/testing.md keeps one half here, the
 * subline that falls back to the path when no excerpt arrived, because that is
 * a rendering decision and not a search one.
 *
 * The shared service is a double in every case below, which is the point: the
 * provider is asserted over what it hands down and what it renders, and never
 * over what a real run would find. Whether the run is right is the subject of
 * SearchServiceTest, of the parity job and of the recheck itself.
 */
#[CoversClass(Provider::class)]
final class ProviderTest extends TestCase {
	private IL10N&MockObject $l10n;
	private IURLGenerator&MockObject $urlGenerator;
	private SearchService&MockObject $searchService;
	private LoggerInterface&MockObject $logger;

	protected function setUp(): void {
		parent::setUp();

		$this->l10n = $this->createMock(IL10N::class);
		$this->l10n->method('t')->willReturnArgument(0);
		$this->urlGenerator = $this->createMock(IURLGenerator::class);
		$this->searchService = $this->createMock(SearchService::class);
		$this->logger = $this->createMock(LoggerInterface::class);
	}

	private function provider(): Provider {
		return new Provider($this->l10n, $this->urlGenerator, $this->searchService, $this->logger);
	}

	private function user(string $uid = 'testuser'): IUser&MockObject {
		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn($uid);

		return $user;
	}

	private function query(
		string $term = 'quarterly report',
		int $limit = 20,
		int|string|null $cursor = null,
		?bool $titleOnly = null,
	): ISearchQuery&MockObject {
		$query = $this->createMock(ISearchQuery::class);
		$query->method('getTerm')->willReturn($term);
		$query->method('getLimit')->willReturn($limit);
		$query->method('getCursor')->willReturn($cursor);

		if ($titleOnly === null) {
			$query->method('getFilter')->willReturn(null);

			return $query;
		}

		$filter = $this->createMock(IFilter::class);
		$filter->method('get')->willReturn($titleOnly);
		$query->method('getFilter')->willReturn($filter);

		return $query;
	}

	/**
	 * @param list<ApprovedHit> $hits
	 * @param array<int,array{text:string,highlights:list<array{int,int}>}> $excerpts
	 */
	private function outcome(
		array $hits = [],
		array $excerpts = [],
		int $nextCursor = 0,
		bool $hasMore = false,
		?string $failure = null,
	): SearchOutcome {
		return new SearchOutcome($hits, $excerpts, $nextCursor, $hasMore, false, $failure);
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

	/**
	 * A constant of the class under test, read rather than copied. Same rule and
	 * same reason as in ExAppServiceTest: a bound written into this file is a
	 * bound that keeps being asserted after somebody moved it in the class.
	 */
	private function constantOf(string $name, string $class = Provider::class): mixed {
		return (new \ReflectionClass($class))->getConstant($name);
	}

	/**
	 * The caps the provider handed down for one query, or null when it never
	 * asked at all.
	 */
	private function capsOf(ISearchQuery&MockObject $query): ?SearchCaps {
		$caps = null;
		$this->searchService->method('run')->willReturnCallback(
			function (IUser $user, string $term, bool $titleOnly, int $startCursor, SearchCaps $handed) use (&$caps): SearchOutcome {
				$caps = $handed;

				return $this->outcome();
			},
		);

		$this->provider()->search($this->user(), $query);

		return $caps;
	}

	// -- translating a query into a run --------------------------------------

	public function testAnEmptyTermIsNotEvenAskedAbout(): void {
		// The dialog sends an empty term while the user is still typing, and it
		// cannot produce a hit, so nothing downstream is touched for it.
		$this->searchService->expects(self::never())->method('run');

		$result = $this->provider()->search($this->user(), $this->query('   '));

		self::assertSame([], $this->entriesOf($result));
	}

	public function testTheCapsCarryTheConstantsOfTheDialogAndTheLimitOfTheQuery(): void {
		// Read out of the class rather than written down here, because the whole
		// reason these four are arguments now is that a second caller uses
		// different ones: what has to stay true is that the dialog hands down its
		// own, not that they carry a particular value.
		$caps = $this->capsOf($this->query(limit: 25));

		self::assertInstanceOf(SearchCaps::class, $caps);
		self::assertSame(25, $caps->pageSize);
		self::assertSame($this->constantOf('MAX_ROUNDS'), $caps->maxRounds);
		self::assertSame($this->constantOf('OVERFETCH'), $caps->overfetch);
		self::assertSame($this->constantOf('MAX_RECHECKS_PER_HIT'), $caps->recheckPerHit);
		self::assertSame($this->constantOf('MAX_RECHECKS_ABSOLUTE'), $caps->recheckAbsolute);
		self::assertSame($this->constantOf('BUDGET_SECONDS'), $caps->budgetSeconds);

		// The dialog stays the impatient one of the two callers: it waits for
		// every provider in parallel, so its per call ceiling is the unchanged
		// one of the service and not the larger one the result page may name.
		self::assertSame(ExAppService::REQUEST_TIMEOUT_SECONDS, $caps->requestCeilingSeconds);
	}

	public function testALimitOfZeroStillAsksForOneHit(): void {
		// A dialog that asks for nothing would otherwise get a run with a page
		// size of zero, which approves nothing and looks exactly like an empty
		// index.
		$caps = $this->capsOf($this->query(limit: 0));

		self::assertInstanceOf(SearchCaps::class, $caps);
		self::assertSame(1, $caps->pageSize);
	}

	public function testTheCursorAndTheTitleOnlyFilterOfTheQueryTravelIntoTheRun(): void {
		$seen = [];
		$this->searchService->method('run')->willReturnCallback(
			function (IUser $user, string $term, bool $titleOnly, int $startCursor, SearchCaps $caps) use (&$seen): SearchOutcome {
				$seen = ['term' => $term, 'titleOnly' => $titleOnly, 'cursor' => $startCursor];

				return $this->outcome();
			},
		);

		// A cursor of the dialog arrives as a string of digits often enough that
		// reading it as one is not an edge case.
		$this->provider()->search($this->user(), $this->query('  quarterly report  ', 20, '120', true));

		self::assertSame(['term' => 'quarterly report', 'titleOnly' => true, 'cursor' => 120], $seen);
	}

	public function testACursorThatIsNotANumberStartsOverAtTheTop(): void {
		$seen = null;
		$this->searchService->method('run')->willReturnCallback(
			function (IUser $user, string $term, bool $titleOnly, int $startCursor, SearchCaps $caps) use (&$seen): SearchOutcome {
				$seen = $startCursor;

				return $this->outcome();
			},
		);

		$this->provider()->search($this->user(), $this->query(cursor: 'page-two'));

		self::assertSame(0, $seen);
	}

	// -- mapping an outcome onto a result group ------------------------------

	public function testEveryFailureOfTheServiceBecomesTheSameEmptyGroup(): void {
		// Four reasons, one shape. The dialog has no room for a sentence of its
		// own, so it declines the same way for all of them; the result page of
		// this phase is where the four are told apart.
		$reasons = [
			SearchOutcome::FAILURE_BACKEND_SILENT,
			SearchOutcome::FAILURE_VERSION_DRIFT,
			SearchOutcome::FAILURE_NO_HOME_FOLDER,
			SearchOutcome::FAILURE_OFFSET_CEILING,
		];

		foreach ($reasons as $reason) {
			$searchService = $this->createMock(SearchService::class);
			$searchService->method('run')->willReturn($this->outcome(failure: $reason));

			$provider = new Provider($this->l10n, $this->urlGenerator, $searchService, $this->logger);
			$result = $provider->search($this->user(), $this->query());

			self::assertSame([], $this->entriesOf($result), $reason . ' produced entries');
			self::assertFalse($result->jsonSerialize()['isPaginated'], $reason . ' produced a paginated group');
		}
	}

	public function testAnOutcomeWithMoreBehindItBecomesAPaginatedGroupCarryingItsCursor(): void {
		$this->urlGenerator->method('linkToRoute')->willReturn('/index.php/f/11');
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf')],
			nextCursor: 137,
			hasMore: true,
		));

		$serialised = $this->provider()->search($this->user(), $this->query())->jsonSerialize();

		self::assertTrue($serialised['isPaginated']);
		self::assertSame(137, $serialised['cursor']);
	}

	public function testAnOutcomeThatHitThePagingCeilingIsShownWithItsHitsAndWithoutANextPage(): void {
		// The one failure that arrives with hits in it. complete() is the honest
		// shape: it says "there is no next page from here", which is exactly what
		// a cursor the container refuses amounts to.
		$this->urlGenerator->method('linkToRoute')->willReturn('/index.php/f/11');
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf')],
			nextCursor: 1200,
			hasMore: false,
			failure: SearchOutcome::FAILURE_OFFSET_CEILING,
		));

		$result = $this->provider()->search($this->user(), $this->query());

		self::assertCount(1, $this->entriesOf($result));
		self::assertFalse($result->jsonSerialize()['isPaginated']);
	}

	// -- rendering -----------------------------------------------------------

	public function testAnEntryIsBuiltOutOfTheApprovedHitAndItsExcerpt(): void {
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(11, 'Quartalsbericht.pdf', 'Vorstand/Quartalsbericht.pdf', 'application/pdf')],
			excerpts: [11 => ['text' => 'der Quartalsbericht des Vorstands', 'highlights' => [[4, 19]]]],
		));

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
		self::assertSame('der Quartalsbericht des Vorstands', $entries[0]['subline']);
		self::assertSame('/index.php/apps/files/?fileid=11', $entries[0]['resourceUrl']);
		self::assertSame('11', $entries[0]['attributes']['fileId']);

		// The ranges travel as character offsets in an attribute and are never
		// turned into markup here: the dialog interpolates the subline as text,
		// so a tag would be shown to the user verbatim.
		self::assertSame('[[4,19]]', $entries[0]['attributes']['highlights']);
	}

	public function testTheSublineIsThePathOfTheHitWhenNoExcerptArrived(): void {
		// Half of behaviour 11 of docs/testing.md, and the half that is a
		// rendering decision: a hit without an excerpt beats no hit at all.
		$this->urlGenerator->method('linkToRoute')->willReturn('/index.php/f/11');
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf')],
		));

		$entries = $this->entriesOf($this->provider()->search($this->user(), $this->query()));

		self::assertCount(1, $entries);
		self::assertSame('Board/Report.pdf', $entries[0]['subline']);
		self::assertArrayNotHasKey('highlights', $entries[0]['attributes']);
	}

	public function testTheCanaryIsLinkedToTheFileListAndNotToAFileId(): void {
		// There is no file behind the id 0, so a link to a fileid would resolve
		// to nothing.
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(0, 'findling-canary', 'answered by findling-backend', '')],
		));

		$this->urlGenerator->expects(self::once())
			->method('linkToRoute')
			->with('files.view.index')
			->willReturn('/index.php/apps/files/');

		$entries = $this->entriesOf($this->provider()->search($this->user(), $this->query()));

		self::assertCount(1, $entries);
		self::assertSame('/index.php/apps/files/', $entries[0]['resourceUrl']);
		self::assertSame('0', $entries[0]['attributes']['fileId']);
	}

	// -- the entry point onto the own result page ----------------------------

	/**
	 * A url generator that can be told apart by what it was asked to route, so
	 * that a test can read the address of the entry point instead of asserting
	 * against a fixed string that every route returns.
	 */
	private function routingUrls(): void {
		$this->urlGenerator->method('linkToRoute')->willReturnCallback(
			static function (string $route, array $arguments = []): string {
				if ($route !== 'findling.page.index') {
					return '/index.php/f/11';
				}

				return '/index.php/apps/findling/' . ($arguments === [] ? '' : '?' . http_build_query($arguments));
			},
		);
	}

	public function testAPaginatedGroupCarriesTheEntryPointAsItsLastEntry(): void {
		// The limit is one and the group has two entries afterwards, which is the
		// property in one line: the door is appended after the hits are built and
		// never counts against what the dialog asked for.
		$this->routingUrls();
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf')],
			nextCursor: 137,
			hasMore: true,
		));

		$result = $this->provider()->search($this->user(), $this->query(limit: 1, titleOnly: true));
		$entries = $this->entriesOf($result);

		self::assertCount(2, $entries);
		self::assertSame('Show all results', $entries[1]['title']);
		self::assertSame('Opens the Findling results page', $entries[1]['subline']);
		self::assertSame('icon-search', $entries[1]['icon']);
		self::assertSame('', $entries[1]['thumbnailUrl']);

		// The term and the built in filter travel into the address, and nothing
		// else does: the way in is always page one, so no page and no cursor path.
		self::assertSame('/index.php/apps/findling/?query=quarterly+report&names=1', $entries[1]['resourceUrl']);

		// And the answer stays the paginated one with its cursor, so the cursor
		// semantics of the dialog are untouched by the extra entry.
		self::assertTrue($result->jsonSerialize()['isPaginated']);
		self::assertSame(137, $result->jsonSerialize()['cursor']);
	}

	public function testACompleteGroupHasNoEntryPointBecauseThePageWouldShowTheSameHits(): void {
		$this->routingUrls();
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf')],
			hasMore: false,
		));

		$entries = $this->entriesOf($this->provider()->search($this->user(), $this->query()));

		self::assertCount(1, $entries);
		self::assertSame('Report.pdf', $entries[0]['title']);
	}

	public function testAGroupWithoutASingleApprovedHitHasNoEntryPointEither(): void {
		// Even when the service reports that there is more behind the cursor. A
		// user whose candidates were all revoked shares is shown nothing at all,
		// and a door into a page that would show them nothing is worse than no
		// door: it would be the one visible sign that something was there.
		$this->routingUrls();
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [],
			nextCursor: 137,
			hasMore: true,
		));

		$result = $this->provider()->search($this->user(), $this->query());

		self::assertSame([], $this->entriesOf($result));
		self::assertFalse($result->jsonSerialize()['isPaginated']);
	}

	public function testTheEntryPointCarriesNoFileIdWhileEveryHitCarriesOne(): void {
		// The property the parity job depends on. Every entry of this group is
		// read as a permission answer through its fileId attribute, so a door
		// that carried one would be compared against the file list of a user as
		// if it were a file.
		$this->routingUrls();
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [
				new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf'),
				new ApprovedHit(12, 'Minutes.pdf', 'Board/Minutes.pdf', 'application/pdf'),
			],
			nextCursor: 137,
			hasMore: true,
		));

		$entries = $this->entriesOf($this->provider()->search($this->user(), $this->query()));

		self::assertCount(3, $entries);
		self::assertSame('11', $entries[0]['attributes']['fileId']);
		self::assertSame('12', $entries[1]['attributes']['fileId']);
		self::assertArrayNotHasKey('fileId', $entries[2]['attributes']);
		// And it is recognisable by the one mark a reader of this group may use
		// to skip it, which is its address.
		self::assertStringStartsWith('/index.php/apps/findling/', $entries[2]['resourceUrl']);
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
