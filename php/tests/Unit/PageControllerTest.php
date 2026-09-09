<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Controller\PageController;
use OCA\Findling\Service\ApprovedHit;
use OCA\Findling\Service\SearchCaps;
use OCA\Findling\Service\SearchOutcome;
use OCA\Findling\Service\SearchService;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\Files\IMimeTypeDetector;
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
 * What is left for this file is the address bar. Four values arrive from
 * outside, every one of them editable by hand, and each has a rule and a silent
 * fallback. One case per line of the URL contract of the 09-UI-SPEC, plus the
 * two directions of the paging contract and the states of the state inventory
 * that the controller itself produces.
 *
 * The numbers of the page are read out of the class with reflection and never
 * written down here. A copy in this file would keep asserting the old page size
 * after somebody changed the real one, which is the failure mode where a test
 * suite is worse than none.
 */
#[CoversClass(PageController::class)]
final class PageControllerTest extends TestCase {
	private SearchService&MockObject $searchService;
	private IUserSession&MockObject $userSession;
	private IMimeTypeDetector&MockObject $mimeTypes;
	private IURLGenerator&MockObject $urlGenerator;
	private LoggerInterface&MockObject $logger;

	protected function setUp(): void {
		parent::setUp();

		$this->searchService = $this->createMock(SearchService::class);
		$this->userSession = $this->createMock(IUserSession::class);
		$this->mimeTypes = $this->createMock(IMimeTypeDetector::class);
		$this->urlGenerator = $this->createMock(IURLGenerator::class);
		$this->logger = $this->createMock(LoggerInterface::class);

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
	 * A constant of the class under test, read rather than copied, after the
	 * pattern of ProviderTest and ExAppServiceTest.
	 */
	private function constantOf(string $name): mixed {
		return (new \ReflectionClass(PageController::class))->getConstant($name);
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

		foreach ($broken as $why => $address) {
			self::assertSame(0, $this->startCursorOf(['query' => 'akte'] + $address), $why);
		}

		$this->answering($this->outcome());
		foreach ($broken as $why => $address) {
			self::assertSame(1, $this->paramsOf(['query' => 'akte'] + $address)['page'], $why);
		}
	}

	public function testAValidCursorPathHandsItsLastElementDown(): void {
		// The last entry is where the displayed page begins. The ones in front
		// of it are the way back and are never handed to the service.
		self::assertSame(
			95,
			$this->startCursorOf(['query' => 'akte', 'page' => '3', 'cursors' => '0.40.95']),
		);
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

		$previous = $this->paramsOf(['query' => 'akte', 'page' => '3', 'cursors' => '0.40.95'])['previousUrl'];

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
		$params = $this->paramsOf(['query' => 'akte', 'page' => (string)$maxPage, 'cursors' => $cursors]);

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

		self::assertNull($this->paramsOf(['query' => 'akte', 'page' => '2', 'cursors' => '0.40'])['nextUrl']);
	}

	public function testTheNextAddressExtendsTheCursorPath(): void {
		// The ordinary case, and the one assertion that shows the path grows by
		// exactly the cursor the run reported.
		$this->answering($this->outcome(nextCursor: 95, hasMore: true));

		$next = $this->paramsOf(['query' => 'akte', 'page' => '2', 'cursors' => '0.40'])['nextUrl'];

		self::assertIsString($next);
		self::assertStringContainsString('page=3', $next);
		self::assertStringContainsString('cursors=0.40.95', $next);
	}

	public function testANextCursorThatDoesNotAdvanceOffersNoNextAddress(): void {
		// A path that is not strictly ascending is refused on the way back in,
		// so a link built from a cursor that stood still would drop the visitor
		// on page one. No link at all is the honest answer.
		$this->answering($this->outcome(nextCursor: 40, hasMore: true));

		self::assertNull($this->paramsOf(['query' => 'akte', 'page' => '2', 'cursors' => '0.40'])['nextUrl']);
	}

	// -- the states ----------------------------------------------------------

	public function testEveryFailureReasonReachesTheTemplateUnchanged(): void {
		// Four reasons, four different sentences on the page, and the controller
		// translates none of them: it hands the reason through and the template
		// decides what a user reads.
		$reasons = [
			SearchOutcome::FAILURE_BACKEND_SILENT,
			SearchOutcome::FAILURE_VERSION_DRIFT,
			SearchOutcome::FAILURE_NO_HOME_FOLDER,
			SearchOutcome::FAILURE_OFFSET_CEILING,
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
				new ApprovedHit(7, 'akte.pdf', 'Recht/akte.pdf', 'application/pdf'),
				new ApprovedHit(8, 'notiz.txt', 'Recht/notiz.txt', 'text/plain'),
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
