<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\SearchCaps;
use OCA\Findling\Service\SearchFilters;
use OCA\Findling\Service\SearchOutcome;
use OCA\Findling\Service\SearchService;
use OCA\Findling\Text\Highlighter;
use OCA\Findling\Text\PlainText;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\Files\IMimeTypeDetector;
use OCP\IDateTimeFormatter;
use OCP\IDateTimeZone;
use OCP\IRequest;
use OCP\IURLGenerator;
use OCP\IUserSession;
use Psr\Log\LoggerInterface;

/**
 * The own result page of this app, and it is one address and no more.
 *
 * A second address would be a second way of searching, and the design contract
 * of this phase forbids it in as many words: everything the page shows is
 * rendered on the server into one document, so there is no route that hands out
 * hits as data, no format switch and no partial reload. Whoever wants the next
 * twenty five hits asks for this same address with a different page number.
 *
 * The route lives under /apps/findling/ and the class therefore extends the
 * plain controller rather than the OCS one, exactly like the settings page: the
 * write allowlist of the read-only gate on the Python side stands at three
 * entries with a test that says so, and a page that shows search results has no
 * business widening a security gate. This route writes nothing at all. There is
 * no appconfig key, no queue row and no job behind it.
 *
 * Three attributes stand above the method and their names are deliberately not
 * written out anywhere in this prose, exactly as the settings controller does
 * it and for the same mechanical reason: the anti vacuity clause of
 * backend/tests/test_php_trust_boundary.py counts the lines of this file that
 * mention a route attribute and compares them against the routes it found, so a
 * mention in a comment would turn a gate red without a route having changed
 * (pitfall 7 of the phase research).
 *
 * What those three amount to is worth a sentence even without their names. The
 * first two lower the admin requirement and the session token requirement,
 * which is what a page has to do that ordinary users open: without the first,
 * SecurityMiddleware::beforeController demands an administrator and throws
 * otherwise; without the second it demands the request token of the session in
 * the address, and a bookmark, the back button of a browser and the link out of
 * the search dialog all carry no token, so every one of the three would land on
 * an error page. That is safe here because this is a reading route that changes
 * nothing, and any writing action of a later phase needs a route of its own
 * outside this class (T-09-09). What is deliberately absent is the marker that
 * lets a registered container in and the marker that drops the session
 * requirement altogether: both are forbidden for this class of route by the
 * same gate, so a logged in session stays the price of admission (T-09-06).
 *
 * The page decides no permission question of its own. It reads ten values out
 * of the address, checks them, and hands the numbers and the filters of this
 * page to the shared search service; who may see which file is answered there and in exactly one
 * place in the whole tree, which backend/tests/test_php_acl_boundary.py holds by
 * counting call sites (UI-03, T-09-04). There is no second round of resolving
 * nodes here, no second readability question and no call into the proxy of the
 * container.
 *
 * The log of this class is one line for one thing the service cannot see: that a
 * page turned a failed run into an error block for a user. The service writes
 * the incident itself with its own detail, so nothing is written twice. The
 * sentence is static and carries no search term, no path and no user id
 * (T-09-08).
 */
final class PageController extends Controller {
	/**
	 * Twenty five hits per page.
	 *
	 * Twenty five times the overfetch of four is one hundred, which is exactly
	 * the largest number of candidates the container accepts in one call. So
	 * this page needs no new ceiling anywhere: the request that serves it fits
	 * into the limits that already exist, and the excerpt call for a full page
	 * stays under the hundred file ids that call accepts as well.
	 */
	public const PAGE_SIZE = 25;

	/**
	 * The highest page this address serves.
	 *
	 * Twenty pages of twenty five hits are five hundred, and five hundred is
	 * the honest end of what a result page is good for. Whoever is on page
	 * twenty one is not reading results any more, they are paging through an
	 * index, and the page says so with one sentence instead of offering a next
	 * page forever. The container has a paging ceiling of its own behind this
	 * one, and both are named rather than discovered.
	 */
	public const MAX_PAGE = 20;

	/**
	 * The same three numbers the search dialog uses, and they are the same on
	 * purpose: the recheck behaves the same way for both callers, so a page
	 * that asked for candidates differently would produce a different result
	 * for the same term and nobody could say which one was right.
	 */
	public const MAX_ROUNDS = 3;
	public const OVERFETCH = 4;

	/**
	 * The ceilings on node resolutions per run.
	 *
	 * Twenty five displayed hits times two resolutions each is fifty, and fifty
	 * is below the absolute ceiling of sixty four, so on this page the absolute
	 * one never binds. It stays written down anyway, because it is the ceiling
	 * that keeps a larger page size from quietly reopening the hole the per hit
	 * number closes: without it, raising PAGE_SIZE alone would raise the number
	 * of database queries one address can cause.
	 */
	public const MAX_RECHECKS_PER_HIT = 2;
	public const MAX_RECHECKS_ABSOLUTE = 64;

	/**
	 * The wall clock of one page, in seconds, and it is a measured number.
	 *
	 * Measured on 2026-09-08 and written up in
	 * docs/measurements/2026-09-seitenbudget/README.md, section 6.2. The rule of
	 * the plan would have given 1.5 seconds, and that number was refused there
	 * with a reason: it is below the budget of the search dialog, so a page that
	 * promises every hit and waits for nobody would have been less patient than
	 * the dialog it is opened from. The number taken instead is the worst
	 * observed single round of that report, 1.944 seconds for the container call
	 * plus about 0.59 seconds of PHP, rounded up to the next half second.
	 */
	public const BUDGET_SECONDS = 3.0;

	/**
	 * The longest search term this address accepts, in characters.
	 *
	 * Clamped and not refused, which is the opposite decision from the lookup
	 * field of the settings page and for a different reason: a cut path names a
	 * different file, while a cut search term is still a search, and answering
	 * it is friendlier than an error page for a bookmark somebody built by hand.
	 * The field on the page carries the same number as its maximum length, so
	 * the clamp only ever fires for an address that was edited.
	 */
	public const MAX_QUERY_LENGTH = 255;

	/**
	 * The four quick time ranges of the chip row, in the order of the surface.
	 *
	 * The six type group names and the three sort mode names are deliberately
	 * not repeated here. They are read out of SearchFilters::TYPES and
	 * SearchFilters::SORTS, because two lists of the same vocabulary drift
	 * apart in the direction nobody notices: a name this page still accepts
	 * after the value object stopped carrying it, or a name the object carries
	 * that this page silently drops.
	 *
	 * These four stand here for the opposite reason. They are no part of what a
	 * narrowed search is: they are a shorthand this page offers for a lower
	 * time bound it computes itself, and by the time the filters leave this
	 * class there is no quick range left, only a number of seconds.
	 *
	 * @var list<string>
	 */
	public const QUICK_RANGES = ['today', 'week', 'month', 'year'];

	/**
	 * Two of these seven are new with the filter row, and only one of them is
	 * used by this class today.
	 *
	 * The zone is what turns a quick range into a number of seconds, and the
	 * formatter is what turns the modification date of a hit into the line
	 * under its path (plan 13-08). The second one arrives here one plan early
	 * on purpose: both are constructor arguments of the same class, and pulling
	 * them in one at a time would make every test of this page grow its double
	 * list twice for one feature.
	 *
	 * Both interfaces are marked in the server as available since version 8.0,
	 * so both exist in every one of the three releases this app declares.
	 */
	public function __construct(
		IRequest $request,
		private SearchService $searchService,
		private IUserSession $userSession,
		private IMimeTypeDetector $mimeTypes,
		private IURLGenerator $urlGenerator,
		private IDateTimeZone $dateTimeZone,
		private IDateTimeFormatter $dateTimeFormatter,
		private LoggerInterface $logger,
	) {
		parent::__construct(Application::APP_ID, $request);
	}

	/**
	 * GET /apps/findling/
	 *
	 * The whole page in one answer: the form with the term that was searched
	 * for, the hits of the requested page with their excerpts, the state block
	 * if there is one, and the two neighbouring addresses. Rendered on the
	 * server with real values, so the page is complete before a single line of
	 * script has run.
	 *
	 * Every one of the ten values in the address is untrusted input, and every
	 * one of them falls back silently rather than producing a message: a term
	 * that is too long is clamped, a filter that is not the one word this page
	 * knows is not set, a page number outside the range is page one, a cursor
	 * path that does not check out is page one as well, a type group that is not
	 * one of the six names is left out of the list, a sort mode that is not one
	 * of the three is relevance, a quick range or a time bound of the wrong
	 * shape is simply not set, and a fingerprint that does not belong to this
	 * request state sends the path back to page one. The page makes no statement
	 * about its own address bar (T-09-09), because such a statement would only
	 * ever be read by somebody who edited it.
	 */
	#[\OCP\AppFramework\Http\Attribute\NoAdminRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'GET', url: '/')]
	public function index(): TemplateResponse {
		$address = $this->address();
		$filters = $this->filters($address);
		$page = $this->pageNumber();
		$fingerprint = $this->fingerprint($address);

		$raw = $this->request->getParam('cursors', '');
		$bound = $this->fingerprintParam() === $fingerprint;
		$cursors = is_string($raw) && $bound ? $this->cursorPath($raw, $page) : [0];
		if ($cursors === [0]) {
			// A path that did not check out is page one, and the page number
			// follows it rather than the other way round: a cursor of zero on
			// page seven would show the first hits under the seventh page
			// number, which is the one outcome worse than starting over.
			//
			// Since the filter row exists there are two ways of not checking
			// out, and the second one is the reason the first was never enough.
			// The shape of a path is what cursorPath reads, its origin is what
			// the fingerprint reads, and a path is only looked at once the
			// fingerprint of the address matches the one this page computes for
			// its own request state. A path that was pasted in out of another
			// search therefore never reaches the shape test at all. Both
			// verdicts are the same verdict, and both of them stay silent.
			$page = 1;
		}

		$outcome = $this->outcome($address['query'], $address['titleOnly'], (int)end($cursors), $filters);

		if ($outcome->failure === SearchOutcome::FAILURE_BACKEND_SILENT
			|| $outcome->failure === SearchOutcome::FAILURE_VERSION_DRIFT) {
			// One static sentence, and only for what the service cannot see:
			// the service logged the incident itself with its own detail, and
			// this line says that a page in front of a user turned it into an
			// error block rather than into a shorter list.
			$this->logger->warning('Findling: the result page is showing an error block instead of hits');
		}

		return new TemplateResponse(
			Application::APP_ID,
			'search',
			[
				'query' => $address['query'],
				'titleOnly' => $address['titleOnly'],
				'page' => $page,
				'maxPage' => self::MAX_PAGE,
				'hits' => $this->rows($outcome, $address['sort']),
				'hasMore' => $outcome->hasMore,
				'degraded' => $outcome->degraded,
				'failure' => $outcome->failure,
				'previousUrl' => $this->previousUrl($address, $page, $cursors, $fingerprint),
				'nextUrl' => $this->nextUrl($address, $page, $cursors, $fingerprint, $outcome),
				'formAction' => $this->urlGenerator->linkToRoute('findling.page.index'),
				// The filter row, finished down to the last address. The
				// template puts the labels to these values and asks nothing:
				// which chip is active, where it leads and whether the reset
				// link exists at all are decisions of this class, and a
				// template that decided any of them would be the second place
				// where the state of the address is interpreted.
				'typeChips' => $this->typeChips($address),
				'rangeChips' => $this->rangeChips($address),
				'sortLinks' => $this->sortLinks($address),
				'resetUrl' => $this->resetUrl($address, $filters),
				'sortMode' => $address['sort'],
				'filtersActive' => $filters->hasAny(),
				'showModified' => $this->showsModified($address['sort']),
			],
			TemplateResponse::RENDER_AS_USER,
		);
	}

	/**
	 * The seven values of the address that describe WHAT is being searched for,
	 * read exactly once per request and handed on as one named value.
	 *
	 * Seven and not ten: the page number, the cursor path and the fingerprint
	 * describe WHERE inside a result the visitor stands, and they are
	 * deliberately not in here. Every one of the seven below goes into the
	 * fingerprint and into every link of the filter row; not one of the other
	 * three may. Keeping the two groups apart in the type is what makes that
	 * rule readable rather than a sentence somebody has to remember.
	 *
	 * Read once and not per caller, for a reason that only shows itself at
	 * midnight: the four quick ranges are calendar windows computed from the
	 * moment of the request, and two readings of the same address a few
	 * microseconds apart can fall on either side of a day boundary. One reading
	 * per request means the filter that ran, the fingerprint that was compared
	 * and the links that were built all describe the same search.
	 *
	 * @return array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int}
	 */
	private function address(): array {
		return [
			'query' => $this->term(),
			'titleOnly' => $this->request->getParam('names') === '1',
			'types' => $this->typeGroups(),
			'sort' => $this->sortMode(),
			'range' => $this->quickRange(),
			// The raw bounds of the address and not the effective ones. What
			// the effective lower bound is depends on the quick range, and a
			// link that carried the computed value would freeze today's
			// midnight into an address somebody bookmarks.
			'since' => $this->epochParam('since'),
			'until' => $this->epochParam('until'),
		];
	}

	/**
	 * The search term of this address, cleaned, clamped and trimmed.
	 *
	 * Invalid UTF-8 counts as no term at all rather than as a term that could
	 * not be cleaned, which is the same verdict the shared text helper reaches
	 * for every other field of this app. The value travels to the template
	 * unescaped on purpose: the template escapes every value it prints, and a
	 * value that had been escaped twice would show the escaping to the user
	 * (T-09-01).
	 */
	private function term(): string {
		$raw = $this->request->getParam('query', '');
		if (!is_string($raw)) {
			return '';
		}

		return trim(PlainText::bounded($raw, self::MAX_QUERY_LENGTH) ?? '');
	}

	/**
	 * The requested page, or page one for everything that is not a page number
	 * of this address. Zero, a negative number, a number above the ceiling and
	 * a word all arrive at the same place, because all four mean the same thing
	 * here: there is no such page.
	 */
	private function pageNumber(): int {
		$raw = $this->request->getParam('page', '');
		if (!is_string($raw) || !ctype_digit($raw)) {
			return 1;
		}

		$page = (int)$raw;

		return $page >= 1 && $page <= self::MAX_PAGE ? $page : 1;
	}

	/**
	 * The active type groups of this address, canonicalised, free of duplicates
	 * and empty for everything that names no group at all.
	 *
	 * The names are checked against SearchFilters::TYPES and against nothing
	 * else, so this page knows six words and not a single file extension: the
	 * mapping from a group to the extensions behind it lives in the container,
	 * and a second one over here would be the second filter vocabulary that the
	 * value object refuses in as many words.
	 *
	 * Canonicalised into the order of that closed list rather than kept in the
	 * order somebody wrote it, and the reason lies one plan further on: the
	 * cursor path of a filtered search is bound to a fingerprint of the request
	 * state (plan 13-08), and without this step a user who picks the same two
	 * groups in the other order would produce another fingerprint and land back
	 * on page one for no reason he could see.
	 *
	 * The loop over the closed list does four things at once, which is why
	 * there is no sorting step, no deduplicating step and no counting step: it
	 * leaves out what is unknown, it leaves out what is empty, it keeps a name
	 * that was written twice exactly once, and it cannot yield more entries
	 * than the closed list has, so six is the ceiling whatever arrives.
	 *
	 * @return list<string>
	 */
	private function typeGroups(): array {
		$raw = $this->request->getParam('types', '');
		if (!is_string($raw) || $raw === '') {
			return [];
		}

		$asked = [];
		foreach (explode(',', $raw) as $part) {
			$asked[strtolower(trim($part))] = true;
		}

		$groups = [];
		foreach (SearchFilters::TYPES as $group) {
			if (isset($asked[$group])) {
				$groups[] = $group;
			}
		}

		return $groups;
	}

	/**
	 * The sort mode of this address, and relevance for everything else.
	 *
	 * Relevance is the mode of a search nobody sorted, and it is the one mode
	 * this page never writes into an address. A value that arrives here anyway
	 * is either a mode somebody typed out or a word that was never a mode, and
	 * both mean the same thing here: sort by relevance.
	 */
	private function sortMode(): string {
		$raw = $this->request->getParam('sort', '');
		if (!is_string($raw) || !in_array($raw, SearchFilters::SORTS, true)) {
			return SearchFilters::SORT_DEFAULT;
		}

		return $raw;
	}

	/**
	 * The quick range of this address, or none for everything that is not one
	 * of the four names.
	 *
	 * One value and never a list, which is the one place where this row of
	 * chips behaves differently from the row above it. Two time ranges at once
	 * give either the larger of the two, and then the smaller one had no
	 * effect, or an empty set, and then the page cannot be explained to the
	 * person looking at it (13-UI-SPEC, D-01). So a click on another range
	 * replaces the one before it, and the address carries at most one.
	 */
	private function quickRange(): ?string {
		$raw = $this->request->getParam('range', '');
		if (!is_string($raw) || !in_array($raw, self::QUICK_RANGES, true)) {
			return null;
		}

		return $raw;
	}

	/**
	 * One of the two time bounds of this address, in seconds of the Unix epoch,
	 * or none for everything that is not such a number.
	 *
	 * Exactly the shape of pageNumber(), down to the digit test: a value that
	 * is not a string of digits is not a bound, and neither is one above the
	 * ceiling both halves of this app carry. A negative number never reaches
	 * the range test at all, because the digit test refuses the sign, and that
	 * is the intended verdict rather than a side effect.
	 *
	 * The ceiling matters more than it looks. A larger value is answered by the
	 * container with a 422, which arrives over here as an empty result group
	 * and looks exactly like "nothing found", so an address somebody built by
	 * hand would get an empty page instead of an answer.
	 */
	private function epochParam(string $name): ?int {
		$raw = $this->request->getParam($name, '');
		if (!is_string($raw) || !ctype_digit($raw)) {
			return null;
		}

		$value = (int)$raw;

		// The digit test has already refused the sign, so the lower end of the
		// interval needs no second look: zero is the smallest value that gets
		// this far, and zero is a bound this app accepts.
		return $value <= SearchFilters::EPOCH_MAX ? $value : null;
	}

	/**
	 * The lower bound of one quick range, in seconds of the Unix epoch, or none
	 * for a name that is not one of the four.
	 *
	 * Every line of this method hangs off the zone of the signed in user, and
	 * that is the whole point of it. A modification date is an epoch value and
	 * therefore free of any zone, but "today" is not an epoch value: it is a
	 * statement about a calendar day, and a calendar day begins in the zone of
	 * the person who says the word. Computed without a zone, the value would be
	 * the one of the default zone of the server, frequently UTC, and for a user
	 * in central Europe it would sit one or two hours beside the day he means.
	 * At night that is not a rounding difference but a missing result: "today"
	 * would leave out the files of the last few hours, and the page would look
	 * correct while being wrong.
	 *
	 * The four windows are calendar windows and not rolling ones. "Today" and
	 * "this year" are calendar terms to begin with, and two models side by side
	 * on one row of chips is something nobody can explain to the person reading
	 * it: seven days that end at midnight next to seven days that end now would
	 * be two different promises in the same typeface.
	 *
	 * All four set a lower bound and none of them sets an upper one, so every
	 * one of them means "since", never "between".
	 */
	private function quickRangeStart(string $range): ?int {
		$now = new \DateTimeImmutable('now', $this->dateTimeZone->getTimeZone());
		$midnight = $now->setTime(0, 0);

		return match ($range) {
			'today' => $midnight->getTimestamp(),
			'week' => $midnight->sub(new \DateInterval('P6D'))->getTimestamp(),
			'month' => $midnight->sub(new \DateInterval('P29D'))->getTimestamp(),
			'year' => $midnight->setDate((int)$now->format('Y'), 1, 1)->getTimestamp(),
			default => null,
		};
	}

	/**
	 * The narrowing of this address as one named value, written out in full
	 * after the manner of caps().
	 *
	 * The quick range and a hand written lower bound are two ways to the same
	 * field, and when both are set the narrower one wins: the effective lower
	 * bound is the larger of the two, because both of them narrow and neither
	 * of them widens. Taking the smaller one would let an address somebody
	 * pasted together widen the range the visible chip promises, which is the
	 * one outcome where the page would show less than it searches. The upper
	 * bound has no quick range behind it and is therefore the raw value or
	 * nothing.
	 *
	 * The effective lower bound stays inside this method and never travels back
	 * into a link. What a chip, a sort link and the reset link carry is the raw
	 * state of the address, so that the quick range keeps meaning "since the
	 * beginning of today" rather than the number today's midnight happened to
	 * be when the page was drawn.
	 *
	 * @param array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int} $address
	 */
	private function filters(array $address): SearchFilters {
		$quickSince = $address['range'] === null ? null : $this->quickRangeStart($address['range']);
		$since = $address['since'];

		if ($quickSince !== null && $since !== null) {
			$since = max($quickSince, $since);
		} elseif ($quickSince !== null) {
			$since = $quickSince;
		}

		return new SearchFilters(
			$address['types'],
			$address['sort'],
			$since,
			$address['until'],
		);
	}

	/**
	 * The container offset at which every display page so far began.
	 *
	 * The last element is where the displayed page starts, the ones in front of
	 * it are the way back. A path and not a calculation, because a display page
	 * is a page of approved hits and between two approved hits there can be any
	 * number of candidates the recheck dropped: multiplying the page number by
	 * the page size would show some hits twice and skip others, differently for
	 * every user.
	 *
	 * Every deviation gives the path of page one, and none of them is an error.
	 * The address is editable, an old path points somewhere else after the index
	 * has moved, and neither is worth a message.
	 *
	 * @return list<int> exactly $page entries, or [0] when anything is off
	 */
	private function cursorPath(string $raw, int $page): array {
		$parts = $raw === '' ? [] : explode('.', $raw);
		if (count($parts) !== $page || $page > self::MAX_PAGE) {
			return [0];
		}

		$path = [];
		$previous = -1;
		foreach ($parts as $part) {
			if (!ctype_digit($part)) {
				return [0];
			}

			$value = (int)$part;
			if ($value <= $previous) {
				return [0];
			}

			if ($path === [] && $value !== 0) {
				return [0];
			}

			$previous = $value;
			$path[] = $value;
		}

		return $path;
	}

	/**
	 * One run of the shared service, or the reason why there was none.
	 *
	 * Two cases never ask. An empty term cannot produce a hit, so the page shows
	 * its empty state without costing the container a request. A request without
	 * a session user cannot be answered at all, because the permission question
	 * is asked against that user's own folder; the attributes of the route make
	 * that case unreachable, and it is handled rather than assumed away.
	 */
	private function outcome(string $query, bool $titleOnly, int $startCursor, SearchFilters $filters): SearchOutcome {
		if ($query === '') {
			return new SearchOutcome([], [], $startCursor, false, false, null);
		}

		$user = $this->userSession->getUser();
		if ($user === null) {
			return new SearchOutcome([], [], $startCursor, false, false, SearchOutcome::FAILURE_NO_HOME_FOLDER);
		}

		return $this->searchService->run($user, $query, $titleOnly, $startCursor, $this->caps(), $filters);
	}

	/**
	 * The ceilings of one page, written out rather than defaulted, in the same
	 * spirit as the dialog does it: every one of these seven is a number
	 * somebody had to think about once, and a default would be a number nobody
	 * has to think about again.
	 *
	 * The per call ceiling is the one of the page and not the one of the dialog.
	 * It is referenced with its full name on purpose, without an import: the
	 * acceptance rule of this plan allows this file exactly one line that names
	 * that service, and an import line would be a second one.
	 */
	private function caps(): SearchCaps {
		return new SearchCaps(
			self::PAGE_SIZE,
			self::MAX_ROUNDS,
			self::OVERFETCH,
			self::MAX_RECHECKS_PER_HIT,
			self::MAX_RECHECKS_ABSOLUTE,
			self::BUDGET_SECONDS,
			\OCA\Findling\Service\ExAppService::PAGE_REQUEST_TIMEOUT_SECONDS,
		);
	}

	/**
	 * The hits of this page as the template wants them: seven finished values
	 * per row and no object the template would have to ask questions of.
	 *
	 * The excerpt becomes a list of text pieces and never a string with markup
	 * in it, which is the whole construction of the highlighting on this page
	 * (T-09-02). A hit the excerpt call did not cover gets an empty list, and
	 * the template puts the path in that place: a hit without an excerpt is
	 * better than no hit.
	 *
	 * The date is the seventh value and it is empty outside a date order. Not
	 * hidden and not rendered as an empty line: the value is not there, because
	 * a modification date shown under relevance would be the one number on this
	 * page that a reader could mistake for a measure of how well a hit fits
	 * (D-04, T-13-40). The page shows no score at all, and this is the reason
	 * it can say so.
	 *
	 * The formatter takes the time zone and the language out of the settings of
	 * the signed in user, which is why there is no date format here and no
	 * format string in the catalogue: the catalogue carries the label and the
	 * label alone. A date of zero is the canary of the walking skeleton, which
	 * has no node behind it and therefore no date to ask for, and it stays
	 * empty as well rather than becoming the first of January 1970.
	 *
	 * @return list<array{fileId:int,title:string,path:string,iconUrl:string,url:string,modified:string,segments:list<array{text:string,mark:bool}>}>
	 */
	private function rows(SearchOutcome $outcome, string $sort): array {
		$showModified = $this->showsModified($sort);
		$rows = [];

		foreach ($outcome->hits as $hit) {
			$excerpt = $outcome->excerpts[$hit->fileId] ?? null;
			$rows[] = [
				'fileId' => $hit->fileId,
				'title' => $hit->title,
				'path' => $hit->path,
				'iconUrl' => $this->mimeTypes->mimeTypeIcon($hit->mimeType),
				'url' => $this->fileUrl($hit->fileId),
				'modified' => $showModified && $hit->mtime > 0
					? $this->dateTimeFormatter->formatDate($hit->mtime, 'long')
					: '',
				'segments' => $excerpt === null ? [] : Highlighter::segments($excerpt['text'], $excerpt['highlights']),
			];
		}

		return $rows;
	}

	/**
	 * Where a row points. The canary of the walking skeleton carries the file id
	 * zero and has no file behind it, so it points at the file list instead: a
	 * link to file zero resolves to nothing.
	 */
	private function fileUrl(int $fileId): string {
		if ($fileId <= 0) {
			return $this->urlGenerator->linkToRoute('files.view.index');
		}

		return $this->urlGenerator->linkToRoute('files.View.showFile', ['fileid' => $fileId]);
	}

	/**
	 * The address of the previous page, which is this one with the last element
	 * of the cursor path taken off. It exists whenever there is a page in front
	 * of this one, and it needs nothing from the run: where the previous page
	 * began was already known when this one was asked for.
	 *
	 * This one and its counterpart below are the only two links of this page
	 * that hand a cursor path on, and therefore the only two that carry a
	 * fingerprint. The asymmetry to filterUrl() is the whole mechanism rather
	 * than an oversight: paging keeps the search and moves inside it, while a
	 * chip changes the search, and a position inside one result set means
	 * nothing inside another one.
	 *
	 * @param array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int} $address
	 * @param list<int> $cursors
	 */
	private function previousUrl(array $address, int $page, array $cursors, string $fingerprint): ?string {
		if ($page <= 1) {
			return null;
		}

		return $this->pageUrl($address, $page - 1, array_slice($cursors, 0, -1), $fingerprint);
	}

	/**
	 * The address of the next page, and never a link into nothing.
	 *
	 * Four conditions, and the fourth is the one that is easy to forget: the
	 * cursor the run reports has to lie strictly behind the one this page
	 * started at, otherwise the path built from it would not be strictly
	 * ascending and the check on the way back in would drop the visitor on page
	 * one. A next button that lands on page one is worse than no next button,
	 * and the design contract says outright that there is never a next into the
	 * void.
	 *
	 * A run that ended in a failure offers no next page either. The paging
	 * ceiling of the container is one of those failures, and the page turns it
	 * into the sentence about narrowing the search rather than into a button:
	 * the cursor behind that ceiling is one the container refuses, so a next
	 * page would be a promise nobody can keep.
	 *
	 * Four of the five, and the fifth is the exception this method spells out.
	 * A run that was handed candidates and kept none of them did not fall
	 * short: it asked, it decided, and its answer is empty. Taking the next
	 * page away from it would take it away in exactly the state in which the
	 * user's own files may be lying behind the foreign ones, which is the
	 * state DI-07-03 is about (decided as V-1a on 10.09.2026).
	 *
	 * @param array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int} $address
	 * @param list<int> $cursors
	 */
	private function nextUrl(array $address, int $page, array $cursors, string $fingerprint, SearchOutcome $outcome): ?string {
		$runFellShort = $outcome->failure !== null
			&& $outcome->failure !== SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED;

		if (!$outcome->hasMore || $page >= self::MAX_PAGE || $runFellShort) {
			return null;
		}

		if ($outcome->nextCursor <= (int)end($cursors)) {
			return null;
		}

		return $this->pageUrl($address, $page + 1, [...$cursors, $outcome->nextCursor], $fingerprint);
	}

	/**
	 * One address of the filter row, and it is a second method next to
	 * pageUrl() rather than a flag on the first one.
	 *
	 * Every chip, every sort link and the reset link is built from here, and
	 * the property that matters is a property of the method and not of a call
	 * site: this one does not take a position inside a result, so it cannot
	 * write one. A flag would have put the same promise into the hands of every
	 * future caller, and a flag is what gets set wrong at the next rebuild,
	 * quietly and with a link that still looks right.
	 *
	 * Why it has to be watertight: a chip is an ordinary link carrying the
	 * values of the current address. If it took the position along, a click on
	 * the seventh screen of one result would land on the seventh screen of
	 * another one, which shows some hits twice and skips others, silently and
	 * differently for every user (13-RESEARCH pitfall D).
	 *
	 * @param array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int} $address
	 */
	private function filterUrl(array $address): string {
		return $this->urlGenerator->linkToRoute('findling.page.index', $this->filterArguments($address));
	}

	/**
	 * The fingerprint of one request state: eight hex characters over the seven
	 * values that decide WHAT is searched for.
	 *
	 * This is a confusion lock and not a security feature. There is no secret,
	 * no signature and nothing to forge: anybody can compute this value for any
	 * address, and that is fine, because it answers the question "does this
	 * position belong to this search" and no other question. A collision is
	 * harmless for the same reason. The cursor counts approved candidates and
	 * nothing else, so the worst a collision can buy is one screen further into
	 * a result the visitor is allowed to see, never a hit, never a name and
	 * never a count of anything.
	 *
	 * The canonicalisation stands BEFORE the hashing, and it is the half that
	 * is easy to leave out. Two type groups picked in the other order are the
	 * same search; hashed as written they would be two values, and a visitor
	 * who reordered nothing would be thrown back to the first screen for a
	 * reason nobody could see. The list arrives already canonicalised out of
	 * typeGroups(), the two bounds arrive as numbers or as nothing, and the
	 * three remaining values are words out of closed lists.
	 *
	 * The separator is the unit separator, and it is picked rather than found:
	 * the shared text helper turns every control character except the tab into
	 * a space before a term reaches this class, so this one character cannot
	 * occur inside any of the seven values. A separator that could occur would
	 * let two different states hash to one string without a collision being
	 * involved at all.
	 *
	 * @param array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int} $address
	 */
	private function fingerprint(array $address): string {
		$state = implode("\x1f", [
			$address['query'],
			$address['titleOnly'] ? '1' : '0',
			implode(',', $address['types']),
			$address['sort'],
			$address['range'] ?? '',
			$address['since'] === null ? '' : (string)$address['since'],
			$address['until'] === null ? '' : (string)$address['until'],
		]);

		return substr(hash('sha256', $state), 0, 8);
	}

	/**
	 * The fingerprint this address claims, or none for everything that does not
	 * have the shape of one.
	 *
	 * Shape first and comparison afterwards, in the same order and for the same
	 * reason as every other value of this address: a value that is not eight hex
	 * characters was never written by this page, and a value that was never
	 * written by this page cannot belong to a path this page handed out.
	 */
	private function fingerprintParam(): ?string {
		$raw = $this->request->getParam('fp', '');
		if (!is_string($raw) || preg_match('/^[0-9a-f]{8}$/', $raw) !== 1) {
			return null;
		}

		return $raw;
	}

	/**
	 * The part of an address that says what is being searched for, as arguments
	 * for the url generator.
	 *
	 * Shared by both builders on purpose, so that a filter cannot be carried by
	 * one of them and dropped by the other: a next link that lost the active
	 * chips would page through a different result than the one on the screen.
	 * What is not shared is the position, and it lives at exactly one of the
	 * two call sites below.
	 *
	 * A value that is not set is not written as an empty parameter, it is not
	 * written at all, and the default sort mode is not written either. The
	 * address of an ordinary search therefore looks exactly as it did before
	 * this phase.
	 *
	 * @param array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int} $address
	 * @return array<string,string>
	 */
	private function filterArguments(array $address): array {
		$arguments = ['query' => $address['query']];

		if ($address['titleOnly']) {
			$arguments['names'] = '1';
		}
		if ($address['types'] !== []) {
			$arguments['types'] = implode(',', $address['types']);
		}
		if ($address['sort'] !== SearchFilters::SORT_DEFAULT) {
			$arguments['sort'] = $address['sort'];
		}
		if ($address['range'] !== null) {
			$arguments['range'] = $address['range'];
		}
		if ($address['since'] !== null) {
			$arguments['since'] = (string)$address['since'];
		}
		if ($address['until'] !== null) {
			$arguments['until'] = (string)$address['until'];
		}

		return $arguments;
	}

	/**
	 * The six chips of the type row, finished, and all six of them every time.
	 *
	 * Each one carries the address of the search WITHOUT itself when it is
	 * active and the address WITH itself when it is not, so one chip switches
	 * one group and leaves the other five where they are (D-01). The row is a
	 * set of switches and not a choice of one.
	 *
	 * All six are always in the list, including the ones behind which there is
	 * not a single hit, and that is a decision rather than a simplification. A
	 * chip that was greyed out or left out would tell the visitor that this
	 * group holds nothing, and that is the same piece of information a counter
	 * on the chip would give. It would be a counting oracle in front of the
	 * permission decision, because what the page can see before the recheck is
	 * the candidates of the index and not the files of this user (T-13-39). So
	 * a chip over an empty group looks like every other chip and leads to the
	 * empty state.
	 *
	 * @param array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int} $address
	 * @return list<array{key:string,active:bool,url:string}>
	 */
	private function typeChips(array $address): array {
		$chips = [];

		foreach (SearchFilters::TYPES as $group) {
			// The selection of the other address, built by walking the closed
			// list rather than by adding to or removing from the current one:
			// the outcome is then canonical because of how it was made, and a
			// canonical list is what the fingerprint of that address is
			// computed over on the way back in.
			$toggled = [];
			foreach (SearchFilters::TYPES as $name) {
				$keep = in_array($name, $address['types'], true);
				if ($name === $group) {
					$keep = !$keep;
				}
				if ($keep) {
					$toggled[] = $name;
				}
			}

			$chips[] = [
				'key' => $group,
				'active' => in_array($group, $address['types'], true),
				'url' => $this->filterUrl(['types' => $toggled] + $address),
			];
		}

		return $chips;
	}

	/**
	 * The four chips of the time row, finished, and at most one of them active.
	 *
	 * The one place where this row behaves differently from the one above it. A
	 * click on another range REPLACES the one before it and a click on the
	 * active one removes it, because two ranges at once give either the wider
	 * of the two, and then the narrower one did nothing, or an empty set, and
	 * then nobody can explain the page to the person looking at it.
	 *
	 * Not one of the four ever writes an upper bound. All four mean "since" and
	 * never "between", so a visitor who picks a range can only ever see more of
	 * the recent past and never lose the present out of the result.
	 *
	 * @param array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int} $address
	 * @return list<array{key:string,active:bool,url:string}>
	 */
	private function rangeChips(array $address): array {
		$chips = [];

		foreach (self::QUICK_RANGES as $name) {
			$active = $address['range'] === $name;

			$chips[] = [
				'key' => $name,
				'active' => $active,
				'url' => $this->filterUrl(['range' => $active ? null : $name] + $address),
			];
		}

		return $chips;
	}

	/**
	 * The three sort links, finished, and exactly one of them active.
	 *
	 * Three and never two: the default mode is a link like the other two, and
	 * its address is the way back out of a sorted view. The link of the active
	 * mode points at the view the visitor is already looking at, and that is
	 * not a dead link but the ordinary state of a segmented switch: all three
	 * segments stay operable so that the set of choices can be read off the row
	 * itself instead of being remembered.
	 *
	 * @param array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int} $address
	 * @return list<array{key:string,active:bool,url:string}>
	 */
	private function sortLinks(array $address): array {
		$links = [];

		foreach (SearchFilters::SORTS as $mode) {
			$links[] = [
				'key' => $mode,
				'active' => $address['sort'] === $mode,
				'url' => $this->filterUrl(['sort' => $mode] + $address),
			];
		}

		return $links;
	}

	/**
	 * The way out of every filter at once, or none when there is nothing to
	 * come out of.
	 *
	 * The sort mode survives this link, and that is the whole difference
	 * between the two halves of the row. Resetting takes away what is HIDING
	 * results; an order hides nothing, it puts the same hits in another
	 * sequence. D-06 says filters in as many words, and hasAny() is where that
	 * distinction is already written down, so this method asks it rather than
	 * deciding a second time.
	 *
	 * @param array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int} $address
	 */
	private function resetUrl(array $address, SearchFilters $filters): ?string {
		if (!$filters->hasAny()) {
			return null;
		}

		return $this->filterUrl([
			'types' => [],
			'range' => null,
			'since' => null,
			'until' => null,
		] + $address);
	}

	/**
	 * Whether the rows of this page carry their modification date.
	 *
	 * Everything that is not the default mode is a date order, and the sentence
	 * is written that way round on purpose: the three names live in
	 * SearchFilters and are read from there rather than repeated over here, the
	 * same rule the type groups follow. An unknown mode never reaches this
	 * method, because the address falls back to the default before it.
	 */
	private function showsModified(string $sort): bool {
		return $sort !== SearchFilters::SORT_DEFAULT;
	}

	/**
	 * One address of this route with the whole state in it, built by the url
	 * generator rather than glued together, so that the query string is encoded
	 * correctly and a rewritten web root is honoured.
	 *
	 * The three values this one adds to the filter arguments are the position
	 * and the proof that the position belongs here. They travel together and
	 * they are only ever written here.
	 *
	 * @param array{query:string,titleOnly:bool,types:list<string>,sort:string,range:?string,since:?int,until:?int} $address
	 * @param list<int> $cursors
	 */
	private function pageUrl(array $address, int $page, array $cursors, string $fingerprint): string {
		$arguments = $this->filterArguments($address) + [
			'page' => (string)$page,
			'cursors' => implode('.', $cursors),
			'fp' => $fingerprint,
		];

		return $this->urlGenerator->linkToRoute('findling.page.index', $arguments);
	}
}
