<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Search\Provider;
use OCA\Findling\Service\ApprovedHit;
use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\SearchCaps;
use OCA\Findling\Service\SearchFilters;
use OCA\Findling\Service\SearchOutcome;
use OCA\Findling\Service\SearchService;
use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\IUser;
use OCP\Search\FilterDefinition;
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
	 * A query whose filters are looked up by name, so that a date bound and the
	 * file name switch can be set apart from one another. Every name that is
	 * not in the map is a filter the dialog did not send, which is the null the
	 * class under test reads as "not set".
	 *
	 * @param array<string,mixed> $values the value behind each filter name, and
	 *                                    deliberately mixed: the point of half
	 *                                    the cases below is a value of the
	 *                                    wrong kind arriving from over there
	 */
	private function filteredQuery(array $values, string $term = 'quarterly report'): ISearchQuery&MockObject {
		$query = $this->createMock(ISearchQuery::class);
		$query->method('getTerm')->willReturn($term);
		$query->method('getLimit')->willReturn(20);
		$query->method('getCursor')->willReturn(null);
		$query->method('getFilter')->willReturnCallback(
			function (string $name) use ($values): ?IFilter {
				if (!array_key_exists($name, $values)) {
					return null;
				}

				$filter = $this->createMock(IFilter::class);
				$filter->method('get')->willReturn($values[$name]);

				return $filter;
			},
		);

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

	/**
	 * The filters the provider handed down for one query, or null when it never
	 * asked at all. The counterpart of capsOf() above, and the only thing the
	 * date cases below assert against: what the dialog set is read off the
	 * object that left this class, never off a result a real run would produce.
	 */
	private function filtersOf(ISearchQuery&MockObject $query): ?SearchFilters {
		$filters = null;
		$this->searchService->method('run')->willReturnCallback(
			function (
				IUser $user,
				string $term,
				bool $titleOnly,
				int $startCursor,
				SearchCaps $caps,
				SearchFilters $handed,
			) use (&$filters): SearchOutcome {
				$filters = $handed;

				return $this->outcome();
			},
		);

		$this->provider()->search($this->user(), $query);

		return $filters;
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
		// Five reasons, one shape. The dialog has no room for a sentence of its
		// own, so it declines the same way for all of them; the result page of
		// this phase is where the five are told apart.
		$reasons = [
			SearchOutcome::FAILURE_BACKEND_SILENT,
			SearchOutcome::FAILURE_VERSION_DRIFT,
			SearchOutcome::FAILURE_NO_HOME_FOLDER,
			SearchOutcome::FAILURE_OFFSET_CEILING,
			SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED,
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

	public function testTheRunThatKeptNoCandidateIsAnEmptyGroupWithItsReasonInTheTrace(): void {
		// The fifth reason from the dialog's end, spelled out rather than left
		// to the enumeration above. It reaches the trace like the other four,
		// and it earns no entry of its own: an entry in the dialog would be a
		// hit that is none, and the sentence this reason exists for has no
		// room here. The result page is where it is read (DI-07-03, V-1a).
		$this->searchService->method('run')->willReturn(
			$this->outcome(failure: SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED),
		);
		$this->logger->expects(self::once())
			->method('debug')
			->with(self::anything(), ['reason' => SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED]);

		$result = $this->provider()->search($this->user(), $this->query());

		self::assertSame([], $this->entriesOf($result));
		self::assertFalse($result->jsonSerialize()['isPaginated']);
	}

	public function testAnOutcomeWithMoreBehindItBecomesAPaginatedGroupCarryingItsCursor(): void {
		$this->urlGenerator->method('linkToRoute')->willReturn('/index.php/f/11');
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf', 0)],
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
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf', 0)],
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
			hits: [new ApprovedHit(11, 'Quartalsbericht.pdf', 'Vorstand/Quartalsbericht.pdf', 'application/pdf', 0)],
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
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf', 0)],
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
			hits: [new ApprovedHit(0, 'findling-canary', 'answered by findling-backend', '', 0)],
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
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf', 0)],
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

	public function testTheEntryPointCarriesTheActiveTypeGroupsIntoThePage(): void {
		// Plan 32-01: the page shows the type groups as chips, so a user who
		// leaves the dialog through the door arrives in front of the narrowing
		// that produced the group. Canonical order, comma separated, exactly the
		// value the page reads back through the same parser. The dates and the
		// file name switch stay as they were: dates out, names only when set.
		$this->routingUrls();
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf', 0)],
			nextCursor: 137,
			hasMore: true,
		));

		$result = $this->provider()->search($this->user(), $this->filteredQuery([
			Provider::FILTER_TYPES => 'images,pdf',
			IFilter::BUILTIN_SINCE => new \DateTimeImmutable('@1757980800'),
		]));
		$entries = $this->entriesOf($result);

		self::assertCount(2, $entries);
		self::assertSame(
			'/index.php/apps/findling/?query=quarterly+report&types=pdf%2Cimages',
			$entries[1]['resourceUrl'],
		);
	}

	public function testTheEntryPointCarriesNoTypesParameterWithoutATypeGroup(): void {
		// An unknown value leaves no group behind, and no group means no
		// parameter at all rather than an empty one.
		$this->routingUrls();
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf', 0)],
			nextCursor: 137,
			hasMore: true,
		));

		$result = $this->provider()->search($this->user(), $this->filteredQuery([
			Provider::FILTER_TYPES => 'videos',
		]));
		$entries = $this->entriesOf($result);

		self::assertCount(2, $entries);
		self::assertSame('/index.php/apps/findling/?query=quarterly+report', $entries[1]['resourceUrl']);
	}

	public function testACompleteGroupHasNoEntryPointBecauseThePageWouldShowTheSameHits(): void {
		$this->routingUrls();
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf', 0)],
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
				new ApprovedHit(11, 'Report.pdf', 'Board/Report.pdf', 'application/pdf', 0),
				new ApprovedHit(12, 'Minutes.pdf', 'Board/Minutes.pdf', 'application/pdf', 0),
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

	// -- the filters of the dialog, declared and read ------------------------

	public function testTheProviderDeclaresAllFourBuiltinFiltersAndItsTypeFilterSoTheDialogNeverSkipsIt(): void {
		// Not one of the twelve, and one line, because a provider that is skipped
		// for an undeclared filter looks exactly like a broken backend: no error,
		// no entry, no hint. Until the two dates joined this list, every search
		// with a date set was such a search. The fifth name is our own since
		// plan 32-01 (USRCH-01).
		self::assertSame(
			[
				IFilter::BUILTIN_TERM,
				IFilter::BUILTIN_TITLE_ONLY,
				IFilter::BUILTIN_SINCE,
				IFilter::BUILTIN_UNTIL,
				'types',
				'folder',
			],
			$this->provider()->getSupportedFilters(),
		);
	}

	public function testTheProviderDefinesExactlyTheTypeAndTheFolderFilterOfItsOwn(): void {
		// D-05 lifted by USRCH-01 (D-32-07): the definition is what keeps the
		// provider list valid. This case asserted an empty list until plan
		// 32-01; it is turned round and not deleted, because the warning behind
		// it still holds: a name of our own without a FilterDefinition turns the
		// whole provider list of the dialog into an error. Two definitions since
		// plan 32-02 (USRCH-02), both strings: the type groups, named like the
		// address parameter of the result page, and the folder.
		$custom = $this->provider()->getCustomFilters();

		self::assertCount(2, $custom);
		self::assertInstanceOf(FilterDefinition::class, $custom[0]);
		self::assertSame('types', $custom[0]->name());
		self::assertSame(FilterDefinition::TYPE_STRING, $custom[0]->type());
		self::assertInstanceOf(FilterDefinition::class, $custom[1]);
		self::assertSame('folder', $custom[1]->name());
		self::assertSame(FilterDefinition::TYPE_STRING, $custom[1]->type());
	}

	public function testEverySupportedNameThatIsNoCoreNameHasADefinition(): void {
		// The check the core runs in SearchComposer::loadFilters() while it
		// loads every provider, written out here because a failure there throws
		// for the whole dialog and not for this group (T-32-02). The seven core
		// names are the ones SearchComposer defines itself.
		$core = [
			IFilter::BUILTIN_TERM,
			IFilter::BUILTIN_SINCE,
			IFilter::BUILTIN_UNTIL,
			IFilter::BUILTIN_TITLE_ONLY,
			IFilter::BUILTIN_PERSON,
			IFilter::BUILTIN_PLACES,
			IFilter::BUILTIN_PROVIDER,
		];
		$provider = $this->provider();
		$defined = array_map(static fn (FilterDefinition $definition): string => $definition->name(), $provider->getCustomFilters());

		$own = array_values(array_diff($provider->getSupportedFilters(), $core));

		self::assertSame(['types', 'folder'], $own);
		self::assertSame([], array_values(array_diff($own, $defined)));
		self::assertSame([], array_values(array_intersect($defined, $core)), 'a core name may not be defined again');
	}

	public function testATypeGroupInTheDialogTravelsIntoTheRun(): void {
		$filters = $this->filtersOf($this->filteredQuery([Provider::FILTER_TYPES => 'pdf']));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertSame(['pdf'], $filters->types);
		self::assertSame(SearchFilters::SORT_DEFAULT, $filters->sort);
	}

	public function testATypeGroupAndADateArriveTogether(): void {
		// D-32-02: type plus date has to work in the dialog.
		$filters = $this->filtersOf($this->filteredQuery([
			Provider::FILTER_TYPES => 'images,PDF',
			IFilter::BUILTIN_SINCE => new \DateTimeImmutable('@1757980800'),
		]));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertSame(['pdf', 'images'], $filters->types);
		self::assertSame(1757980800, $filters->since);
		self::assertNull($filters->until);
	}

	public function testATypeValueThatNamesNoGroupIsTheSearchWithoutAFilterAndThrowsNothing(): void {
		// D-32-03 and ROADMAP success criterion 3: whatever reaches the provider
		// and is not a group leaves the run exactly as it is without the filter,
		// none() in all four fields. The strings name no group, the rest are
		// values of the wrong kind from over there, where a string filter
		// carries a string.
		$wrong = ['videos', '', ',,,', "pdf\0", str_pad('pdf,', 5000, 'x'), 5, null, true, ['pdf'], new \stdClass()];

		foreach ($wrong as $index => $value) {
			$searchService = $this->createMock(SearchService::class);
			$handed = null;
			$searchService->method('run')->willReturnCallback(
				function (
					IUser $user,
					string $term,
					bool $titleOnly,
					int $startCursor,
					SearchCaps $caps,
					SearchFilters $filters,
				) use (&$handed): SearchOutcome {
					$handed = $filters;

					return $this->outcome();
				},
			);

			$provider = new Provider($this->l10n, $this->urlGenerator, $searchService, $this->logger);
			$provider->search($this->user(), $this->filteredQuery([Provider::FILTER_TYPES => $value]));

			self::assertInstanceOf(SearchFilters::class, $handed, 'value ' . $index . ' never reached the run');
			self::assertSame([], $handed->types, 'value ' . $index . ' became a type group');
			self::assertEquals(SearchFilters::none(), $handed, 'value ' . $index . ' narrowed the run');
		}
	}

	public function testADateInTheSinceFilterTravelsIntoTheRunAsItsEpoch(): void {
		$filters = $this->filtersOf($this->filteredQuery([
			IFilter::BUILTIN_SINCE => new \DateTimeImmutable('@1757980800'),
		]));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertSame(1757980800, $filters->since);
		self::assertNull($filters->until);
	}

	public function testADateInTheUntilFilterTravelsIntoTheRunAsItsEpoch(): void {
		$filters = $this->filtersOf($this->filteredQuery([
			IFilter::BUILTIN_UNTIL => new \DateTimeImmutable('@1760572800'),
		]));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertNull($filters->since);
		self::assertSame(1760572800, $filters->until);
	}

	public function testBothBoundsCarryTheirValueWhenBothAreSet(): void {
		$filters = $this->filtersOf($this->filteredQuery([
			IFilter::BUILTIN_SINCE => new \DateTimeImmutable('@1757980800'),
			IFilter::BUILTIN_UNTIL => new \DateTimeImmutable('@1760572800'),
		]));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertSame(1757980800, $filters->since);
		self::assertSame(1760572800, $filters->until);
	}

	public function testAQueryWithoutADateFilterNarrowsNothingAtAll(): void {
		// The state of every search the dialog sent before this plan, and it has
		// to stay exactly that: an object that is none() in all four of its
		// fields rather than one that merely looks empty in two of them.
		$filters = $this->filtersOf($this->filteredQuery([]));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertEquals(SearchFilters::none(), $filters);
		self::assertFalse($filters->hasAny());
	}

	public function testAFilterValueOfTheWrongKindCountsAsNotSetAndThrowsNothing(): void {
		// The value of a date filter is a DateTimeImmutable over there, so
		// anything else is a defect on that side. It costs the bound and never
		// the search: somebody who picked a date is owed an answer about the
		// term, not an empty result group and not a stack trace.
		$wrong = ['2026-09-16', 1757980800, null, true, new \stdClass()];

		foreach ($wrong as $index => $value) {
			$searchService = $this->createMock(SearchService::class);
			$handed = null;
			$searchService->method('run')->willReturnCallback(
				function (
					IUser $user,
					string $term,
					bool $titleOnly,
					int $startCursor,
					SearchCaps $caps,
					SearchFilters $filters,
				) use (&$handed): SearchOutcome {
					$handed = $filters;

					return $this->outcome();
				},
			);

			$provider = new Provider($this->l10n, $this->urlGenerator, $searchService, $this->logger);
			$provider->search($this->user(), $this->filteredQuery([
				IFilter::BUILTIN_SINCE => $value,
				IFilter::BUILTIN_UNTIL => $value,
			]));

			self::assertInstanceOf(SearchFilters::class, $handed, 'value ' . $index . ' never reached the run');
			self::assertNull($handed->since, 'value ' . $index . ' became a lower bound');
			self::assertNull($handed->until, 'value ' . $index . ' became an upper bound');
		}
	}

	public function testAnAbsurdlyLargeBoundIsClampedToTheCeilingBothHalvesAgreeOn(): void {
		// Above SEARCH_MTIME_MAX the container answers with a 422, and a 422
		// arrives here as an empty group that reads like "nothing found". The
		// bound is clamped and the search still happens.
		$filters = $this->filtersOf($this->filteredQuery([
			IFilter::BUILTIN_UNTIL => new \DateTimeImmutable('@' . (SearchFilters::EPOCH_MAX + 86400)),
		]));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertSame(SearchFilters::EPOCH_MAX, $filters->until);
	}

	public function testANegativeBoundIsClampedToZero(): void {
		$filters = $this->filtersOf($this->filteredQuery([
			IFilter::BUILTIN_SINCE => new \DateTimeImmutable('@-86400'),
		]));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertSame(0, $filters->since);
	}

	public function testTheDialogCarriesATypeGroupButNeverASortMode(): void {
		// D-05 lifted by USRCH-01 (D-32-07): the definition is what keeps the
		// provider list valid. Until plan 32-01 this case asserted that the
		// dialog carried neither a type group nor a sort mode; it is turned
		// round for the type group and kept for the sort mode, which stays on
		// the own result page. A sort value smuggled in under the name sort is
		// a name this provider never declared, so it never becomes a mode.
		$filters = $this->filtersOf($this->filteredQuery([
			IFilter::BUILTIN_SINCE => new \DateTimeImmutable('@1757980800'),
			IFilter::BUILTIN_TITLE_ONLY => true,
			Provider::FILTER_TYPES => 'pdf',
			'sort' => 'newest',
		]));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertSame(['pdf'], $filters->types);
		self::assertSame(SearchFilters::SORT_DEFAULT, $filters->sort);
	}

	// -- plan 32-02: the folder of the dialog --------------------------------

	/**
	 * @return array<string,array{string,string}>
	 */
	public static function foldersThatAreRead(): array {
		return [
			'a leading slash' => ['/Projekte', '/Projekte'],
			'a trailing slash' => ['Projekte/', '/Projekte'],
			'a nested folder with a trailing slash' => ['/Projekte/2026/', '/Projekte/2026'],
			'a folder with blanks and umlauts' => ['/Ablage Büro', '/Ablage Büro'],
		];
	}

	#[\PHPUnit\Framework\Attributes\DataProvider('foldersThatAreRead')]
	public function testAFolderInTheDialogTravelsIntoTheRunInItsCanonicalShape(string $raw, string $expected): void {
		$filters = $this->filtersOf($this->filteredQuery([Provider::FILTER_FOLDER => $raw]));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertSame($expected, $filters->folder);
		self::assertSame([], $filters->types);
	}

	public function testAFolderValueThatIsNoFolderIsTheSearchWithoutAFilterAndThrowsNothing(): void {
		// USRCH-03 at this end: the root, the empty value, values of the wrong
		// kind, control characters and an overlong value all leave the run
		// exactly as it is without the filter, none() in every field. The empty
		// value never arrives from the core (D-32-01), it is read as no folder
		// all the same. '..' is not decided here but in SearchService.
		$wrong = [
			'/',
			'//',
			'',
			5,
			null,
			true,
			['a'],
			new \stdClass(),
			"/Projekte\0",
			"/Projekte\n",
			"/Projekte\x7F",
			'/' . str_repeat('x', Provider::MAX_FOLDER_LENGTH),
		];

		foreach ($wrong as $index => $value) {
			$searchService = $this->createMock(SearchService::class);
			$handed = null;
			$searchService->method('run')->willReturnCallback(
				function (
					IUser $user,
					string $term,
					bool $titleOnly,
					int $startCursor,
					SearchCaps $caps,
					SearchFilters $filters,
				) use (&$handed): SearchOutcome {
					$handed = $filters;

					return $this->outcome();
				},
			);

			$provider = new Provider($this->l10n, $this->urlGenerator, $searchService, $this->logger);
			$provider->search($this->user(), $this->filteredQuery([Provider::FILTER_FOLDER => $value]));

			self::assertInstanceOf(SearchFilters::class, $handed, 'value ' . $index . ' never reached the run');
			self::assertNull($handed->folder, 'value ' . $index . ' became a folder');
			self::assertEquals(SearchFilters::none(), $handed, 'value ' . $index . ' narrowed the run');
		}
	}

	public function testAValueAtTheLengthBoundIsStillAFolder(): void {
		// The other edge of the same bound, so that it is a bound.
		$raw = '/' . str_repeat('x', Provider::MAX_FOLDER_LENGTH - 1);

		self::assertSame(Provider::MAX_FOLDER_LENGTH, strlen($raw));
		self::assertSame($raw, $this->filtersOf($this->filteredQuery([Provider::FILTER_FOLDER => $raw]))?->folder);
	}

	public function testAFolderAndADateArriveTogether(): void {
		// D-32-02: folder plus date has to work in the dialog.
		$filters = $this->filtersOf($this->filteredQuery([
			Provider::FILTER_FOLDER => '/Projekte',
			IFilter::BUILTIN_SINCE => new \DateTimeImmutable('@1757980800'),
		]));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertSame('/Projekte', $filters->folder);
		self::assertSame(1757980800, $filters->since);
	}

	public function testAFolderAndATypeGroupArriveTogether(): void {
		// The plugin never sends both at once; a hand built request may.
		$filters = $this->filtersOf($this->filteredQuery([
			Provider::FILTER_FOLDER => '/Projekte',
			Provider::FILTER_TYPES => 'pdf',
		]));

		self::assertInstanceOf(SearchFilters::class, $filters);
		self::assertSame('/Projekte', $filters->folder);
		self::assertSame(['pdf'], $filters->types);
	}

	public function testTheEntryPointNeverCarriesTheFolder(): void {
		// The result page has no folder filter, so the door leaves it out.
		$this->routingUrls();
		$this->searchService->method('run')->willReturn($this->outcome(
			hits: [new ApprovedHit(11, 'Report.pdf', 'Projekte/Report.pdf', 'application/pdf', 0)],
			nextCursor: 137,
			hasMore: true,
		));

		$result = $this->provider()->search($this->user(), $this->filteredQuery([
			Provider::FILTER_FOLDER => '/Projekte',
			Provider::FILTER_TYPES => 'pdf',
		]));
		$entries = $this->entriesOf($result);

		self::assertCount(2, $entries);
		self::assertSame('/index.php/apps/findling/?query=quarterly+report&types=pdf', $entries[1]['resourceUrl']);
	}
}
