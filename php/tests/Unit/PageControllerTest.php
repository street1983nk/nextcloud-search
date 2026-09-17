<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Controller\PageController;
use OCA\Findling\Service\ApprovedHit;
use OCA\Findling\Service\SearchCaps;
use OCA\Findling\Service\SearchFilters;
use OCA\Findling\Service\SearchOutcome;
use OCA\Findling\Service\SearchService;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\Files\IMimeTypeDetector;
use OCP\IDateTimeFormatter;
use OCP\IDateTimeZone;
use OCP\IRequest;
use OCP\IURLGenerator;
use OCP\IUser;
use OCP\IUserSession;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * What the result page decides on its own, and nothing else.
 *
 * The shared search service is a double in every case below, and that is the
 * point rather than a shortcut: whether a run finds the right files is decided
 * in OCA\Findling\Service\SearchService and asserted in SearchServiceTest, and
 * a second suite that made statements about it here would be the second opinion
 * on a question this page is explicitly not allowed to have (UI-03).
 *
 * What is left for this file is the address bar. Nine values arrive from
 * outside, every one of them editable by hand, and each has a rule and a silent
 * fallback. One case per line of the URL contract of the 09-UI-SPEC and of its
 * continuation in the 13-UI-SPEC, plus the two directions of the paging
 * contract and the states of the state inventory that the controller itself
 * produces.
 *
 * The numbers of the page are read out of the class with reflection and never
 * written down here. A copy in this file would keep asserting the old page size
 * after somebody changed the real one, which is the failure mode where a test
 * suite is worse than none.
 */
#[CoversClass(PageController::class)]
final class PageControllerTest extends TestCase {
	/**
	 * The zone of the staged user, and it is on purpose not UTC.
	 *
	 * The quick range cases below assert a midnight, and a midnight is the one
	 * thing that proves nothing when the test zone and the default zone of the
	 * machine agree: a controller that had forgotten the zone of the user
	 * entirely would pass every one of them on a runner set to UTC. Central
	 * European time is one or two hours off UTC depending on the season, so
	 * either way the two midnights are different numbers.
	 */
	private const TEST_ZONE = 'Europe/Berlin';

	private SearchService&MockObject $searchService;
	private IUserSession&MockObject $userSession;
	private IMimeTypeDetector&MockObject $mimeTypes;
	private IURLGenerator&MockObject $urlGenerator;
	private IDateTimeZone&MockObject $dateTimeZone;
	private IDateTimeFormatter&MockObject $dateTimeFormatter;
	private LoggerInterface&MockObject $logger;

	protected function setUp(): void {
		parent::setUp();

		$this->searchService = $this->createMock(SearchService::class);
		$this->userSession = $this->createMock(IUserSession::class);
		$this->mimeTypes = $this->createMock(IMimeTypeDetector::class);
		$this->urlGenerator = $this->createMock(IURLGenerator::class);
		$this->dateTimeZone = $this->createMock(IDateTimeZone::class);
		$this->dateTimeFormatter = $this->createMock(IDateTimeFormatter::class);
		$this->logger = $this->createMock(LoggerInterface::class);

		$this->dateTimeZone->method('getTimeZone')->willReturn(new \DateTimeZone(self::TEST_ZONE));

		// A readable recipe instead of a real date. What the cases below decide
		// is which timestamp reached the formatter and under which format, and
		// a real month name would put the language settings of a test runner
		// into an assertion that is not about them.
		$this->dateTimeFormatter->method('formatDate')->willReturnCallback(
			static fn (int $timestamp, string $format = 'long'): string => "formatted:{$timestamp}:{$format}",
		);

		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn('testuser');
		$this->userSession->method('getUser')->willReturn($user);

		$this->mimeTypes->method('mimeTypeIcon')->willReturn('/icon.svg');

		// A predictable address rather than a real one: the assertions below are
		// about which values the page puts into a link, not about how Nextcloud
		// spells a web root.
		$this->urlGenerator->method('linkToRoute')->willReturnCallback(
			static fn (string $route, array $arguments = []): string => $arguments === []
				? "/{$route}"
				: "/{$route}?" . http_build_query($arguments),
		);
	}

	/**
	 * The controller with one address staged. A parameter that is not in the
	 * array is absent, which is what IRequest reports for a query string that
	 * does not carry it.
	 *
	 * @param array<string,mixed> $params
	 */
	private function controller(array $params = []): PageController {
		$request = $this->createMock(IRequest::class);
		$request->method('getParam')->willReturnCallback(
			static fn (string $key, mixed $default = null): mixed => $params[$key] ?? $default,
		);

		return new PageController(
			$request,
			$this->searchService,
			$this->userSession,
			$this->mimeTypes,
			$this->urlGenerator,
			$this->dateTimeZone,
			$this->dateTimeFormatter,
			$this->logger,
		);
	}

	/**
	 * @param array<string,mixed> $params
	 * @return array<string,mixed>
	 */
	private function paramsOf(array $params): array {
		return $this->controller($params)->index()->getParams();
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
	 * A fresh double for every staged answer.
	 *
	 * Fresh and not restaged, because a second willReturn on the same method of
	 * the same double never takes effect: the first stub wins, and a case that
	 * staged its answer after another one had already staged one would silently
	 * assert the answer of its predecessor.
	 */
	private function answering(SearchOutcome $outcome): void {
		$searchService = $this->createMock(SearchService::class);
		$searchService->method('run')->willReturn($outcome);
		$this->searchService = $searchService;
	}

	/**
	 * The start cursor the page handed down for one address, and null when it
	 * never asked at all.
	 *
	 * @param array<string,mixed> $params
	 */
	private function startCursorOf(array $params): ?int {
		$startCursor = null;
		$searchService = $this->createMock(SearchService::class);
		$searchService->method('run')->willReturnCallback(
			function (IUser $user, string $term, bool $titleOnly, int $handed, SearchCaps $caps) use (&$startCursor): SearchOutcome {
				$startCursor = $handed;

				return $this->outcome();
			},
		);
		$this->searchService = $searchService;

		$this->controller($params)->index();

		return $startCursor;
	}

	/**
	 * The filter object the page handed down for one address.
	 *
	 * The counterpart of startCursorOf, and built the same way: a fresh double
	 * that catches one argument of the one call. Every case of the section
	 * below asserts against the object that really reached the service and not
	 * against a value the controller returned to its template, because the
	 * template side of these five values is built one plan later and a case
	 * that waited for it would assert nothing today.
	 *
	 * @param array<string,mixed> $params
	 */
	private function filtersOf(array $params): SearchFilters {
		$filters = null;
		$searchService = $this->createMock(SearchService::class);
		$searchService->method('run')->willReturnCallback(
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
		$this->searchService = $searchService;

		$this->controller($params + ['query' => 'akte'])->index();

		self::assertInstanceOf(SearchFilters::class, $filters);

		return $filters;
	}

	/**
	 * The calendar day a quick range begins on, as a date in the test zone.
	 *
	 * Deliberately not built the way the controller builds it: the controller
	 * takes midnight first and subtracts an interval, this one reads the day
	 * off the current moment and formats it. A counter check that repeats the
	 * pattern of the thing it checks agrees with it even when both are wrong.
	 */
	private function dayOf(string $range): string {
		$now = new \DateTimeImmutable('now', new \DateTimeZone(self::TEST_ZONE));

		return match ($range) {
			'today' => $now->format('Y-m-d'),
			'week' => $now->modify('-6 days')->format('Y-m-d'),
			'month' => $now->modify('-29 days')->format('Y-m-d'),
			'year' => $now->format('Y') . '-01-01',
			default => '',
		};
	}

	/**
	 * That a lower bound is midnight of an expected calendar day in the zone of
	 * the user, read back out of the epoch value rather than compared as a bare
	 * number: a number that is off by an hour is hard to read, while a time of
	 * 23:00:00 on the day before says what went wrong.
	 */
	private function assertMidnightOf(string $day, ?int $since): void {
		self::assertIsInt($since, "there is no lower bound at all, expected midnight of {$day}");

		$read = (new \DateTimeImmutable('@' . $since))->setTimezone(new \DateTimeZone(self::TEST_ZONE));

		self::assertSame("{$day} 00:00:00", $read->format('Y-m-d H:i:s'));
	}

	/**
	 * A constant of the class under test, read rather than copied, after the
	 * pattern of ProviderTest and ExAppServiceTest.
	 */
	private function constantOf(string $name): mixed {
		return (new \ReflectionClass(PageController::class))->getConstant($name);
	}

	/**
	 * The fingerprint the page computes for one address, read off a link the
	 * page built rather than computed a second time over here.
	 *
	 * The same road dayOf() takes and for the same reason: a counter check that
	 * repeats the recipe of the thing it checks agrees with it even when both
	 * are wrong. Here it is also the only road at all, because the value is
	 * never returned and never displayed; it exists in two places, in the link
	 * the page hands out and in the comparison on the way back in, and one of
	 * those two is readable from outside.
	 *
	 * The next link is the one that carries it, so the double staged here
	 * reports more hits. The position of the address is stripped before the
	 * question is asked, because a position never goes into the fingerprint and
	 * an address with a broken one would produce no next link to read.
	 *
	 * @param array<string,mixed> $params
	 */
	private function fingerprintOf(array $params): string {
		$standing = $this->searchService;

		$searchService = $this->createMock(SearchService::class);
		$searchService->method('run')->willReturn($this->outcome(nextCursor: 40, hasMore: true));
		$this->searchService = $searchService;

		$address = $params;
		unset($address['page'], $address['cursors'], $address['fp']);
		$next = $this->controller($address + ['query' => 'akte'])->index()->getParams()['nextUrl'];

		$this->searchService = $standing;

		self::assertIsString($next, 'there is no next link to read a fingerprint off');
		self::assertSame(1, preg_match('/[?&]fp=([0-9a-f]{8})(?:&|$)/', $next, $found));

		return $found[1];
	}

	/**
	 * The same address with the fingerprint that belongs to it.
	 *
	 * Every case that hands the page a cursor path needs one since this plan.
	 * The page looks at a path only once the fingerprint of the address matches
	 * its own request state, so a path without one is a path out of nowhere and
	 * lands on page one by design, which would make every paging case below
	 * pass for the wrong reason or fail for the wrong one.
	 *
	 * @param array<string,mixed> $params
	 * @return array<string,mixed>
	 */
	private function bound(array $params): array {
		return $params + ['fp' => $this->fingerprintOf($params)];
	}

	/**
	 * Every link of the filter row of one address as one flat list: six type
	 * chips, four range chips, three sort links and, when it exists, the reset
	 * link. Keyed by what each one is, so a failure names the link.
	 *
	 * @param array<string,mixed> $params
	 * @return array<string,string>
	 */
	private function controlLinksOf(array $params): array {
		$page = $this->paramsOf($params + ['query' => 'akte']);

		$links = [];
		foreach ($page['typeChips'] as $chip) {
			$links["type:{$chip['key']}"] = $chip['url'];
		}
		foreach ($page['rangeChips'] as $chip) {
			$links["range:{$chip['key']}"] = $chip['url'];
		}
		foreach ($page['sortLinks'] as $link) {
			$links["sort:{$link['key']}"] = $link['url'];
		}
		if ($page['resetUrl'] !== null) {
			$links['reset'] = $page['resetUrl'];
		}

		return $links;
	}

	/**
	 * One row of the filter bar of one address, keyed by the wire name of its
	 * parts.
	 *
	 * @param array<string,mixed> $params
	 * @return array<string,array{key:string,active:bool,url:string}>
	 */
	private function partsOf(array $params, string $row): array {
		$parts = [];
		foreach ($this->paramsOf($params + ['query' => 'akte'])[$row] as $part) {
			$parts[$part['key']] = $part;
		}

		return $parts;
	}

	// -- the search term -----------------------------------------------------

	public function testAnEmptyTermIsNotEvenAskedAbout(): void {
		// An address without a term is the entry point of the page, and it
		// cannot produce a hit, so it costs the container nothing.
		$this->searchService->expects(self::never())->method('run');

		$params = $this->paramsOf([]);

		self::assertSame([], $params['hits']);
		self::assertNull($params['failure']);
		self::assertFalse($params['hasMore']);
	}

	public function testATermBeyondTheCeilingIsClamped(): void {
		// Clamped and not refused: a cut term is still a search, and an error
		// page for a bookmark somebody built by hand would help nobody.
		$this->answering($this->outcome());
		$ceiling = $this->constantOf('MAX_QUERY_LENGTH');
		self::assertIsInt($ceiling);

		$params = $this->paramsOf(['query' => str_repeat('a', $ceiling + 45)]);

		self::assertSame($ceiling, mb_strlen($params['query'], 'UTF-8'));
	}

	public function testATermThatIsNotValidUtf8CountsAsNoTermAtAll(): void {
		// The shared text helper answers invalid UTF-8 with null, and the page
		// reads that as no term rather than as a term it could not clean.
		$this->searchService->expects(self::never())->method('run');

		$params = $this->paramsOf(['query' => "Beleh\xC3\x28rung"]);

		self::assertSame('', $params['query']);
		self::assertSame([], $params['hits']);
	}

	// -- the filter ----------------------------------------------------------

	public function testTheFilterIsSetOnlyByTheOneWordTheAddressKnows(): void {
		// The built in title-only filter of the dialog, spelled the way the
		// dialog link spells it. Everything else is not set, including the two
		// spellings somebody would try by hand.
		$this->answering($this->outcome());

		self::assertTrue($this->paramsOf(['query' => 'akte', 'names' => '1'])['titleOnly']);

		foreach (['true', 'yes', 'on', '0', ''] as $other) {
			self::assertFalse(
				$this->paramsOf(['query' => 'akte', 'names' => $other])['titleOnly'],
				"names={$other} must not set the filter",
			);
		}

		self::assertFalse($this->paramsOf(['query' => 'akte'])['titleOnly']);
	}

	// -- the five values of the filter row -----------------------------------

	public function testTheTypeGroupsOfTheAddressReachTheSearch(): void {
		$filters = $this->filtersOf(['types' => 'pdf,images']);

		self::assertSame(['pdf', 'images'], $filters->types);
	}

	public function testTheTwoSortModesOfTheAddressReachTheSearch(): void {
		self::assertSame('newest', $this->filtersOf(['sort' => 'newest'])->sort);
		self::assertSame('oldest', $this->filtersOf(['sort' => 'oldest'])->sort);
	}

	public function testTheTwoTimeBoundsOfTheAddressReachTheSearchAsNumbers(): void {
		// Two different numbers on purpose: one number in both fields would
		// pass even if the page read the same parameter twice.
		$filters = $this->filtersOf(['since' => '1757980800', 'until' => '1758585600']);

		self::assertSame(1757980800, $filters->since);
		self::assertSame(1758585600, $filters->until);
	}

	public function testTheFourQuickRangesAreCalendarWindowsInTheZoneOfTheUser(): void {
		// The four windows of the chip row, each read back into the zone of the
		// staged user. All four set a lower bound and none of them sets an
		// upper one, so every one of them means "since" and never "between".
		$ranges = $this->constantOf('QUICK_RANGES');
		self::assertSame(['today', 'week', 'month', 'year'], $ranges);

		foreach ($ranges as $range) {
			$filters = $this->filtersOf(['range' => $range]);

			$this->assertMidnightOf($this->dayOf($range), $filters->since);
			self::assertNull($filters->until, "{$range} must not set an upper bound");
		}
	}

	public function testTheTypeListIsLowercasedAndTrimmed(): void {
		// Capitals out of a hand written address and a space out of a link
		// somebody encoded by hand, and neither of the two costs a group.
		$filters = $this->filtersOf(['types' => 'PDF, images']);

		self::assertSame(['pdf', 'images'], $filters->types);
	}

	public function testAnUnknownGroupIsLeftOutAndARepeatedOneIsKeptOnce(): void {
		$filters = $this->filtersOf(['types' => 'pdf,xyz,pdf']);

		self::assertSame(['pdf'], $filters->types);
	}

	public function testTheTypeListIsCanonicalisedIntoTheOrderOfTheSurface(): void {
		// The same two groups in the other order are the same filter and have
		// to arrive as the same list: one plan further on the cursor path is
		// bound to a fingerprint of this state, and two orders would be two
		// fingerprints for one selection.
		self::assertSame(
			$this->filtersOf(['types' => 'pdf,images'])->types,
			$this->filtersOf(['types' => 'images,pdf'])->types,
		);
	}

	public function testAListLongerThanTheClosedOneStaysWithinIt(): void {
		// Twice the closed list, so twelve entries of which six are names, and
		// the answer is the closed list itself and not a list of twelve.
		$types = SearchFilters::TYPES;

		$filters = $this->filtersOf(['types' => implode(',', [...$types, ...$types])]);

		self::assertSame($types, $filters->types);
	}

	public function testASortModeTheAddressDoesNotKnowIsRelevance(): void {
		foreach (['quatsch', 'NEWEST', 'date', '', '1'] as $other) {
			self::assertSame(
				SearchFilters::SORT_DEFAULT,
				$this->filtersOf(['sort' => $other])->sort,
				"sort={$other} must fall back to the default mode",
			);
		}
	}

	public function testAQuickRangeTheAddressDoesNotKnowSetsNoBoundAtAll(): void {
		foreach (['quatsch', 'TODAY', 'week,month', ''] as $other) {
			$filters = $this->filtersOf(['range' => $other]);

			self::assertNull($filters->since, "range={$other} must set no lower bound");
			self::assertNull($filters->until, "range={$other} must set no upper bound");
		}
	}

	public function testATimeBoundThatIsNotOneIsNotSet(): void {
		// A word, a negative number, a number above the ceiling both halves of
		// this app carry, a fraction and a leading space. All five mean the
		// same thing here: there is no such bound, and the search runs on.
		$ceiling = SearchFilters::EPOCH_MAX;

		foreach (['quatsch', '-5', (string)($ceiling + 1), '1.5', ' 17'] as $bad) {
			$filters = $this->filtersOf(['since' => $bad, 'until' => $bad]);

			self::assertNull($filters->since, "since={$bad} must not be a bound");
			self::assertNull($filters->until, "until={$bad} must not be a bound");
		}
	}

	public function testTheNarrowerOfTheTwoLowerBoundsWins(): void {
		// Both ways to a lower bound narrow and neither of them widens, so the
		// later of the two is the one that counts. Both cases below hold on
		// every day of the year, which the obvious pair of "this year" and
		// "yesterday" would not: on the first of January yesterday is earlier
		// than the first of January.
		$now = new \DateTimeImmutable('now', new \DateTimeZone(self::TEST_ZONE));

		// A bound inside the running year is never earlier than the first of
		// January, so here the raw value of the address is the narrower one.
		$inThisYear = $now->getTimestamp();
		self::assertSame(
			$inThisYear,
			$this->filtersOf(['range' => 'year', 'since' => (string)$inThisYear])->since,
		);

		// And a bound a whole year back is never later than midnight of today,
		// so there the boundary of the chip is the narrower one.
		$this->assertMidnightOf(
			$this->dayOf('today'),
			$this->filtersOf([
				'range' => 'today',
				'since' => (string)$now->modify('-1 year')->getTimestamp(),
			])->since,
		);
	}

	public function testNotOneBrokenValueOfTheFilterRowProducesAMessage(): void {
		// Every wrong value of the row in one address, and the page answers
		// with a search rather than with a statement about its own address bar
		// (T-09-09, T-13-34): no error state, no log line, no exception, and
		// the term the user typed is still the term of the page.
		$this->logger->expects(self::never())->method('warning');
		$this->answering($this->outcome());

		$params = $this->paramsOf([
			'query' => 'akte',
			'types' => 'xyz,,%%%',
			'sort' => 'quatsch',
			'range' => 'gestern',
			'since' => '-5',
			'until' => 'morgen',
		]);

		self::assertNull($params['failure']);
		self::assertSame([], $params['hits']);
		self::assertSame('akte', $params['query']);
	}

	// -- the page number -----------------------------------------------------

	public function testEveryPageNumberOutsideTheRangeIsPageOne(): void {
		// Zero, a negative number, one above the ceiling and a word all mean the
		// same thing to this address: there is no such page.
		$this->answering($this->outcome());
		$maxPage = $this->constantOf('MAX_PAGE');
		self::assertIsInt($maxPage);

		foreach (['0', '-3', (string)($maxPage + 1), 'abc', '1.5', ' 2'] as $bad) {
			self::assertSame(
				1,
				$this->paramsOf(['query' => 'akte', 'page' => $bad])['page'],
				"page={$bad} must fall back to the first page",
			);
		}
	}

	// -- the cursor path -----------------------------------------------------

	public function testACursorPathThatDoesNotCheckOutIsPageOne(): void {
		// Four ways of being wrong, one verdict, and never an exception: the
		// wrong number of entries, an entry that does not ascend, a first entry
		// that is not zero, and an entry that is not a number at all (T-09-09).
		$broken = [
			'the wrong number of entries' => ['page' => '3', 'cursors' => '0.40'],
			'an entry that does not ascend' => ['page' => '2', 'cursors' => '0.0'],
			'a first entry that is not zero' => ['page' => '2', 'cursors' => '5.40'],
			'an entry that is not a number' => ['page' => '2', 'cursors' => '0.x'],
		];

		// Every one of the four carries the fingerprint that belongs to its
		// address, so the shape is the only thing left that can be wrong here.
		// The origin of a path has a case of its own further down.
		foreach ($broken as $why => $address) {
			self::assertSame(0, $this->startCursorOf($this->bound(['query' => 'akte'] + $address)), $why);
		}

		$this->answering($this->outcome());
		foreach ($broken as $why => $address) {
			self::assertSame(1, $this->paramsOf($this->bound(['query' => 'akte'] + $address))['page'], $why);
		}
	}

	public function testAValidCursorPathHandsItsLastElementDown(): void {
		// The last entry is where the displayed page begins. The ones in front
		// of it are the way back and are never handed to the service.
		//
		// This is also the case for a fingerprint that fits: a path whose shape
		// checks out and whose origin checks out is used as it stands, and the
		// page number of the address stays where the visitor left it.
		$address = $this->bound(['query' => 'akte', 'page' => '3', 'cursors' => '0.40.95']);

		self::assertSame(95, $this->startCursorOf($address));

		$this->answering($this->outcome());
		self::assertSame(3, $this->paramsOf($address)['page']);
	}

	// -- the two neighbouring addresses --------------------------------------

	public function testThereIsNoPreviousAddressOnPageOne(): void {
		$this->answering($this->outcome());

		self::assertNull($this->paramsOf(['query' => 'akte'])['previousUrl']);
	}

	public function testThePreviousAddressDropsTheLastElementOfTheCursorPath(): void {
		// Where the previous page began was already known when this one was
		// asked for, so the way back costs no run and no guess.
		$this->answering($this->outcome());

		$previous = $this->paramsOf($this->bound(['query' => 'akte', 'page' => '3', 'cursors' => '0.40.95']))['previousUrl'];

		self::assertIsString($previous);
		self::assertStringContainsString('page=2', $previous);
		self::assertStringContainsString('cursors=0.40', $previous);
		self::assertStringNotContainsString('0.40.95', $previous);
	}

	public function testThereIsNoNextAddressWithoutMoreHits(): void {
		$this->answering($this->outcome(nextCursor: 60, hasMore: false));

		self::assertNull($this->paramsOf(['query' => 'akte'])['nextUrl']);
	}

	public function testThereIsNoNextAddressOnTheLastPage(): void {
		// The page says the sentence about narrowing the search instead, which
		// is the template's job; what matters here is that there is no link.
		$this->answering($this->outcome(nextCursor: 900, hasMore: true));
		$maxPage = $this->constantOf('MAX_PAGE');
		self::assertIsInt($maxPage);

		$cursors = implode('.', range(0, $maxPage - 1));
		$params = $this->paramsOf($this->bound([
			'query' => 'akte',
			'page' => (string)$maxPage,
			'cursors' => $cursors,
		]));

		self::assertSame($maxPage, $params['page']);
		self::assertNull($params['nextUrl']);
	}

	public function testThereIsNoNextAddressWhenTheRunFailed(): void {
		// The paging ceiling of the container arrives as a failure with hits
		// already on the table, and a next page from there would be a promise
		// the container refuses to keep.
		$this->answering($this->outcome(
			nextCursor: 1300,
			hasMore: true,
			failure: SearchOutcome::FAILURE_OFFSET_CEILING,
		));

		self::assertNull($this->paramsOf($this->bound([
			'query' => 'akte',
			'page' => '2',
			'cursors' => '0.40',
		]))['nextUrl']);
	}

	public function testTheRunThatKeptNoCandidateStillOffersItsNextAddress(): void {
		// The one reason that is not a failure of the run, and the one place
		// where the difference is worth a line of code. The run finished, it
		// just kept nothing, and the user's own files may be lying behind the
		// foreign ones on the very next page. Taking the link away here would
		// take it away in exactly the state DI-07-03 is about.
		$this->answering($this->outcome(
			nextCursor: 95,
			hasMore: true,
			failure: SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED,
		));

		$next = $this->paramsOf($this->bound([
			'query' => 'akte',
			'page' => '2',
			'cursors' => '0.40',
		]))['nextUrl'];

		self::assertIsString($next);
		self::assertStringContainsString('page=3', $next);
		self::assertStringContainsString('cursors=0.40.95', $next);
	}

	public function testTheNextAddressExtendsTheCursorPath(): void {
		// The ordinary case, and the one assertion that shows the path grows by
		// exactly the cursor the run reported.
		$this->answering($this->outcome(nextCursor: 95, hasMore: true));

		$next = $this->paramsOf($this->bound([
			'query' => 'akte',
			'page' => '2',
			'cursors' => '0.40',
		]))['nextUrl'];

		self::assertIsString($next);
		self::assertStringContainsString('page=3', $next);
		self::assertStringContainsString('cursors=0.40.95', $next);
	}

	public function testANextCursorThatDoesNotAdvanceOffersNoNextAddress(): void {
		// A path that is not strictly ascending is refused on the way back in,
		// so a link built from a cursor that stood still would drop the visitor
		// on page one. No link at all is the honest answer.
		$this->answering($this->outcome(nextCursor: 40, hasMore: true));

		self::assertNull($this->paramsOf($this->bound([
			'query' => 'akte',
			'page' => '2',
			'cursors' => '0.40',
		]))['nextUrl']);
	}

	// -- the links of the filter row -----------------------------------------

	public function testNotOneLinkOfTheFilterRowCanCarryAPosition(): void {
		// All fourteen and not one example: six type chips, four range chips,
		// three sort links and the reset link. A link of this row that took the
		// position along would land a click on the seventh screen of one result
		// on the seventh screen of another one, which shows some hits twice and
		// skips others without a word (T-13-37, pitfall D).
		$this->answering($this->outcome(nextCursor: 95, hasMore: true));

		$links = $this->controlLinksOf($this->bound([
			'query' => 'akte',
			'types' => 'pdf',
			'page' => '3',
			'cursors' => '0.40.95',
		]));

		self::assertCount(14, $links);

		foreach ($links as $what => $url) {
			self::assertStringNotContainsString('page=', $url, "{$what} carries a page number");
			self::assertStringNotContainsString('cursors=', $url, "{$what} carries a cursor path");
			self::assertStringNotContainsString('fp=', $url, "{$what} carries a fingerprint");
		}
	}

	public function testATypeChipSwitchesItsOwnGroupAndLeavesTheOthersAlone(): void {
		// Every chip of the row is a switch of its own (D-01): the inactive one
		// leads to the same search with its group added, the active one to the
		// same search with its group taken away, and both keep the term and the
		// order of the page.
		$this->answering($this->outcome());

		$chips = $this->partsOf(['query' => 'akte', 'types' => 'pdf', 'sort' => 'newest'], 'typeChips');

		self::assertCount(count(SearchFilters::TYPES), $chips);
		self::assertTrue($chips['pdf']['active']);
		self::assertFalse($chips['images']['active']);

		// Added in the order of the closed list and not in the order of the
		// click, because that list is what the fingerprint is computed over.
		self::assertStringContainsString('types=' . urlencode('pdf,images'), $chips['images']['url']);
		self::assertStringContainsString('query=akte', $chips['images']['url']);
		self::assertStringContainsString('sort=newest', $chips['images']['url']);

		// And the active one leads to a search with no type at all, because it
		// was the only one.
		self::assertStringNotContainsString('types=', $chips['pdf']['url']);
		self::assertStringContainsString('sort=newest', $chips['pdf']['url']);

		// With two groups active, switching one off leaves the other standing.
		$both = $this->partsOf(['query' => 'akte', 'types' => 'pdf,images'], 'typeChips');

		self::assertStringContainsString('types=images', $both['pdf']['url']);
		self::assertStringContainsString('types=pdf&', $both['images']['url'] . '&');
	}

	public function testATimeRangeChipReplacesTheOneBeforeItAndTheActiveOneRemovesIt(): void {
		// The one row where at most one part can be active. Two ranges at once
		// give either the wider of the two or an empty set, and neither can be
		// explained to the person looking at the page.
		$this->answering($this->outcome());

		$ranges = $this->constantOf('QUICK_RANGES');
		self::assertIsArray($ranges);

		$chips = $this->partsOf(['query' => 'akte', 'range' => 'week'], 'rangeChips');

		self::assertCount(count($ranges), $chips);
		self::assertTrue($chips['week']['active']);

		foreach (['today', 'month', 'year'] as $other) {
			self::assertFalse($chips[$other]['active'], $other);
			self::assertStringContainsString("range={$other}", $chips[$other]['url'], $other);
			self::assertStringNotContainsString('range=week', $chips[$other]['url'], $other);
			self::assertStringNotContainsString('until=', $chips[$other]['url'], $other);
		}

		// And the active one takes the range away rather than replacing it.
		self::assertStringNotContainsString('range=', $chips['week']['url']);
	}

	public function testTheDefaultSortModeIsNeverWrittenIntoAnAddress(): void {
		// Relevance is the mode of a search nobody sorted, and the address of
		// such a search looks exactly as it did before this phase. The link of
		// the default mode exists all the same: it is the way back out of a
		// sorted view.
		$this->answering($this->outcome(nextCursor: 95, hasMore: true));
		$default = 'sort=' . SearchFilters::SORT_DEFAULT;

		$addresses = [
			'an ordinary search' => [],
			'a sorted search' => ['sort' => 'oldest'],
			'a narrowed and sorted search' => ['types' => 'pdf', 'range' => 'today', 'sort' => 'newest'],
		];

		foreach ($addresses as $why => $address) {
			$links = $this->controlLinksOf($address);
			self::assertArrayHasKey('sort:' . SearchFilters::SORT_DEFAULT, $links, $why);

			foreach ($links as $what => $url) {
				self::assertStringNotContainsString($default, $url, "{$why}: {$what}");
			}
		}
	}

	public function testThereIsNoResetLinkWhileNothingIsNarrowed(): void {
		// A sort mode takes nothing away, so it does not bring the link out
		// either: resetting removes what is hiding results, and an order hides
		// none of them (D-06).
		$this->answering($this->outcome());

		foreach ([[], ['sort' => 'newest']] as $address) {
			$params = $this->paramsOf($address + ['query' => 'akte']);

			self::assertNull($params['resetUrl']);
			self::assertFalse($params['filtersActive']);
		}
	}

	public function testTheResetLinkDropsEveryFilterAndKeepsTheOrder(): void {
		$this->answering($this->outcome());

		$params = $this->paramsOf([
			'query' => 'akte',
			'types' => 'pdf,images',
			'range' => 'week',
			'since' => '1757980800',
			'until' => '1758585600',
			'sort' => 'oldest',
		]);

		self::assertTrue($params['filtersActive']);

		$reset = $params['resetUrl'];
		self::assertIsString($reset);
		self::assertStringContainsString('query=akte', $reset);
		self::assertStringContainsString('sort=oldest', $reset);

		foreach (['types=', 'range=', 'since=', 'until='] as $gone) {
			self::assertStringNotContainsString($gone, $reset, "the reset link still carries {$gone}");
		}

		// A bound out of the search dialog highlights no chip at all, and it
		// still brings the link out: there is no state in which the page shows
		// less than it searches (FILT-04).
		self::assertIsString($this->paramsOf(['query' => 'akte', 'since' => '1757980800'])['resetUrl']);
	}

	// -- the fingerprint of the request state --------------------------------

	public function testACursorPathOutOfAnotherSearchIsPageOne(): void {
		// The path of an unfiltered search, pasted by hand into a filtered
		// address. Its shape checks out perfectly, and that is the whole point
		// of this case: only its origin gives it away, and until this plan
		// nobody asked about the origin (13-UI-SPEC, sample 6).
		$foreign = $this->fingerprintOf(['query' => 'akte']);
		self::assertNotSame($foreign, $this->fingerprintOf(['query' => 'akte', 'types' => 'pdf']));

		$address = [
			'query' => 'akte',
			'types' => 'pdf',
			'page' => '3',
			'cursors' => '0.40.95',
			'fp' => $foreign,
		];

		self::assertSame(0, $this->startCursorOf($address));

		// Silently, and that is a statement of its own: no message, no log line
		// and no exception, because the address bar is not something this page
		// makes statements about (T-09-09).
		$this->logger->expects(self::never())->method('warning');
		$this->answering($this->outcome());

		$params = $this->paramsOf($address);

		self::assertSame(1, $params['page']);
		self::assertNull($params['failure']);
	}

	public function testTheSameSelectionInAnotherOrderHasTheSameFingerprint(): void {
		// The guard on the canonicalisation, and the reason it stands before
		// the hashing: two type groups picked in the other order are the same
		// search, and a visitor who reordered nothing would otherwise be thrown
		// back to page one for a reason nobody could see.
		self::assertSame(
			$this->fingerprintOf(['types' => 'pdf,images']),
			$this->fingerprintOf(['types' => 'images,pdf']),
		);
	}

	public function testEveryValueOfTheSearchGoesIntoTheFingerprint(): void {
		// The counterpart of the case above, and the one that keeps it honest:
		// a fingerprint that always returned the same eight characters would
		// pass that one and would bind nothing at all.
		$plain = $this->fingerprintOf([]);

		$others = [
			'another term' => ['query' => 'belehrung'],
			'the title only filter' => ['names' => '1'],
			'a type group' => ['types' => 'pdf'],
			'a sort mode' => ['sort' => 'newest'],
			'a quick range' => ['range' => 'today'],
			'a lower bound' => ['since' => '1757980800'],
			'an upper bound' => ['until' => '1758585600'],
		];

		foreach ($others as $why => $address) {
			self::assertNotSame($plain, $this->fingerprintOf($address), $why);
		}
	}

	public function testAFingerprintThatIsNotOneIsPageOne(): void {
		// The shape is read before the comparison, exactly as every other value
		// of this address is. Five ways of not being eight hexadecimal
		// characters, one verdict, and never an exception.
		$right = $this->fingerprintOf(['query' => 'akte']);

		$broken = [
			'none at all' => null,
			'seven characters' => substr($right, 0, 7),
			'nine characters' => $right . '0',
			'a character that is not hexadecimal' => substr($right, 0, 7) . 'z',
			'hexadecimal in capitals' => 'ABCDEF12',
		];

		foreach ($broken as $why => $claim) {
			$address = ['query' => 'akte', 'page' => '3', 'cursors' => '0.40.95'];
			if ($claim !== null) {
				$address['fp'] = $claim;
			}

			self::assertSame(0, $this->startCursorOf($address), $why);
		}
	}

	public function testThePagingLinksCarryTheFingerprintAndTheActiveFilters(): void {
		// The two links that may hand a position on are the two that have to
		// prove where it came from. They carry the filters with it, because a
		// next page of another selection would be a next page into a different
		// result than the one on the screen.
		$this->answering($this->outcome(nextCursor: 95, hasMore: true));

		$address = [
			'query' => 'akte',
			'types' => 'pdf',
			'sort' => 'oldest',
			'page' => '2',
			'cursors' => '0.40',
		];
		$params = $this->paramsOf($this->bound($address));

		foreach (['previousUrl', 'nextUrl'] as $which) {
			$url = $params[$which];

			self::assertIsString($url, $which);
			self::assertStringContainsString('fp=' . $this->fingerprintOf($address), $url, $which);
			self::assertStringContainsString('types=pdf', $url, $which);
			self::assertStringContainsString('sort=oldest', $url, $which);
		}

		self::assertStringContainsString('cursors=0.40.95', $params['nextUrl']);
		self::assertStringContainsString('page=1', $params['previousUrl']);
	}

	// -- the date of a row ---------------------------------------------------

	public function testUnderDateSortingEveryRowCarriesItsModifiedDate(): void {
		// Two different timestamps on purpose: one date in both rows would pass
		// even if the page formatted the same hit twice. The format is the long
		// one and the formatter takes zone and language out of the settings of
		// the signed in user, which is why no date format appears here.
		$this->answering($this->outcome(hits: [
			new ApprovedHit(7, 'akte.pdf', 'Recht/akte.pdf', 'application/pdf', 1757980800),
			new ApprovedHit(8, 'notiz.txt', 'Recht/notiz.txt', 'text/plain', 1758585600),
		]));

		foreach (['newest', 'oldest'] as $mode) {
			$params = $this->paramsOf(['query' => 'akte', 'sort' => $mode]);

			self::assertTrue($params['showModified'], $mode);
			self::assertSame($mode, $params['sortMode']);
			self::assertSame('formatted:1757980800:long', $params['hits'][0]['modified'], $mode);
			self::assertSame('formatted:1758585600:long', $params['hits'][1]['modified'], $mode);
		}
	}

	public function testUnderRelevanceNotOneRowCarriesADate(): void {
		// D-04 without a loophole: not shown, not hidden, not there. A date
		// under relevance would be the one number on this page that a reader
		// could take for a measure of how well a hit fits, and the page shows
		// no score at all (T-13-40).
		$this->answering($this->outcome(hits: [
			new ApprovedHit(7, 'akte.pdf', 'Recht/akte.pdf', 'application/pdf', 1757980800),
			new ApprovedHit(8, 'notiz.txt', 'Recht/notiz.txt', 'text/plain', 1758585600),
		]));

		$params = $this->paramsOf(['query' => 'akte']);

		self::assertFalse($params['showModified']);
		self::assertSame(SearchFilters::SORT_DEFAULT, $params['sortMode']);

		foreach ($params['hits'] as $index => $row) {
			self::assertSame('', $row['modified'], "row {$index} carries a date under relevance");
		}
	}

	public function testAHitWithoutAModificationDateShowsNoneUnderSortingEither(): void {
		// The canary of the walking skeleton carries the file id zero and has
		// no node behind it, so there is nothing to ask for a date. It stays
		// empty rather than becoming the first of January 1970.
		$this->answering($this->outcome(hits: [new ApprovedHit(0, 'findling', 'findling', '', 0)]));

		$params = $this->paramsOf(['query' => 'akte', 'sort' => 'newest']);

		self::assertTrue($params['showModified']);
		self::assertSame('', $params['hits'][0]['modified']);
	}

	// -- the states ----------------------------------------------------------

	public function testEveryFailureReasonReachesTheTemplateUnchanged(): void {
		// Five reasons, five different sentences on the page, and the controller
		// translates none of them: it hands the reason through and the template
		// decides what a user reads.
		$reasons = [
			SearchOutcome::FAILURE_BACKEND_SILENT,
			SearchOutcome::FAILURE_VERSION_DRIFT,
			SearchOutcome::FAILURE_NO_HOME_FOLDER,
			SearchOutcome::FAILURE_OFFSET_CEILING,
			SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED,
		];

		foreach ($reasons as $reason) {
			$this->answering($this->outcome(failure: $reason));

			self::assertSame($reason, $this->paramsOf(['query' => 'akte'])['failure'], $reason);
		}
	}

	public function testARequestWithoutASessionUserIsNotSearchedForAtAll(): void {
		// Unreachable through the attributes of the route, handled rather than
		// assumed away: without a user there is no folder to ask the permission
		// question against, and the only safe answer to a question that cannot
		// be asked is nothing.
		$this->userSession = $this->createMock(IUserSession::class);
		$this->userSession->method('getUser')->willReturn(null);
		$this->searchService->expects(self::never())->method('run');

		$params = $this->paramsOf(['query' => 'akte']);

		self::assertSame(SearchOutcome::FAILURE_NO_HOME_FOLDER, $params['failure']);
		self::assertSame([], $params['hits']);
	}

	public function testAHitWithAnExcerptCarriesPiecesAndOneWithoutCarriesNone(): void {
		// The excerpt becomes text pieces with a flag and never a string with
		// markup in it (T-09-02). A hit the excerpt call did not cover gets an
		// empty list, and the template puts the path in that place.
		$this->answering($this->outcome(
			hits: [
				new ApprovedHit(7, 'akte.pdf', 'Recht/akte.pdf', 'application/pdf', 0),
				new ApprovedHit(8, 'notiz.txt', 'Recht/notiz.txt', 'text/plain', 0),
			],
			excerpts: [7 => ['text' => 'Die Belehrung', 'highlights' => [[4, 13]]]],
		));

		$hits = $this->paramsOf(['query' => 'Belehrung'])['hits'];

		self::assertCount(2, $hits);
		self::assertSame(
			[
				['text' => 'Die ', 'mark' => false],
				['text' => 'Belehrung', 'mark' => true],
			],
			$hits[0]['segments'],
		);
		self::assertSame([], $hits[1]['segments']);
		self::assertSame('/icon.svg', $hits[0]['iconUrl']);
		self::assertStringContainsString('fileid=7', $hits[0]['url']);
	}

	// -- the numbers of the page ---------------------------------------------

	public function testTheCapsCarryTheConstantsOfThePage(): void {
		// The test that keeps the page from quietly running on different numbers
		// than the ones its own constants document. Every value is read out of
		// the class, so moving a constant moves this assertion with it.
		$caps = null;
		$this->searchService->method('run')->willReturnCallback(
			function (IUser $user, string $term, bool $titleOnly, int $startCursor, SearchCaps $handed) use (&$caps): SearchOutcome {
				$caps = $handed;

				return $this->outcome();
			},
		);

		$this->controller(['query' => 'akte'])->index();

		self::assertInstanceOf(SearchCaps::class, $caps);
		self::assertSame($this->constantOf('PAGE_SIZE'), $caps->pageSize);
		self::assertSame($this->constantOf('MAX_ROUNDS'), $caps->maxRounds);
		self::assertSame($this->constantOf('OVERFETCH'), $caps->overfetch);
		self::assertSame($this->constantOf('MAX_RECHECKS_PER_HIT'), $caps->recheckPerHit);
		self::assertSame($this->constantOf('MAX_RECHECKS_ABSOLUTE'), $caps->recheckAbsolute);
		self::assertSame($this->constantOf('BUDGET_SECONDS'), $caps->budgetSeconds);
		self::assertSame(
			(new \ReflectionClass(\OCA\Findling\Service\ExAppService::class))->getConstant('PAGE_REQUEST_TIMEOUT_SECONDS'),
			$caps->requestCeilingSeconds,
		);
	}

	public function testTheAnswerIsAPageAndNotAFragment(): void {
		// One route, one output path, and it is a whole document inside the
		// Nextcloud user shell. A second render mode would be the beginning of a
		// second way of getting hits out of this app, which the design contract
		// of the phase rules out.
		$this->answering($this->outcome());

		$response = $this->controller(['query' => 'akte'])->index();

		self::assertInstanceOf(TemplateResponse::class, $response);
		self::assertSame(TemplateResponse::RENDER_AS_USER, $response->getRenderAs());
		self::assertSame('search', $response->getTemplateName());
		self::assertSame(
			$this->constantOf('MAX_PAGE'),
			$response->getParams()['maxPage'],
		);
	}
}
