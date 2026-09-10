<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\SearchCaps;
use OCA\Findling\Service\SearchOutcome;
use OCA\Findling\Service\SearchService;
use OCA\Findling\Text\Highlighter;
use OCA\Findling\Text\PlainText;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\Files\IMimeTypeDetector;
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
 * The page decides no permission question of its own. It reads four values out
 * of the address, checks them, and hands the numbers of this page to the shared
 * search service; who may see which file is answered there and in exactly one
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

	public function __construct(
		IRequest $request,
		private SearchService $searchService,
		private IUserSession $userSession,
		private IMimeTypeDetector $mimeTypes,
		private IURLGenerator $urlGenerator,
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
	 * Every one of the four values in the address is untrusted input, and every
	 * one of them falls back silently rather than producing a message: a term
	 * that is too long is clamped, a filter that is not the one word this page
	 * knows is not set, a page number outside the range is page one, and a
	 * cursor path that does not check out is page one as well. The page makes no
	 * statement about its own address bar (T-09-09), because such a statement
	 * would only ever be read by somebody who edited it.
	 */
	#[\OCP\AppFramework\Http\Attribute\NoAdminRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'GET', url: '/')]
	public function index(): TemplateResponse {
		$query = $this->term();
		$titleOnly = $this->request->getParam('names') === '1';
		$page = $this->pageNumber();

		$raw = $this->request->getParam('cursors', '');
		$cursors = is_string($raw) ? $this->cursorPath($raw, $page) : [0];
		if ($cursors === [0]) {
			// A path that did not check out is page one, and the page number
			// follows it rather than the other way round: a cursor of zero on
			// page seven would show the first hits under the seventh page
			// number, which is the one outcome worse than starting over.
			$page = 1;
		}

		$outcome = $this->outcome($query, $titleOnly, (int)end($cursors));

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
				'query' => $query,
				'titleOnly' => $titleOnly,
				'page' => $page,
				'maxPage' => self::MAX_PAGE,
				'hits' => $this->rows($outcome),
				'hasMore' => $outcome->hasMore,
				'degraded' => $outcome->degraded,
				'failure' => $outcome->failure,
				'previousUrl' => $this->previousUrl($query, $titleOnly, $page, $cursors),
				'nextUrl' => $this->nextUrl($query, $titleOnly, $page, $cursors, $outcome),
				'formAction' => $this->urlGenerator->linkToRoute('findling.page.index'),
			],
			TemplateResponse::RENDER_AS_USER,
		);
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
	private function outcome(string $query, bool $titleOnly, int $startCursor): SearchOutcome {
		if ($query === '') {
			return new SearchOutcome([], [], $startCursor, false, false, null);
		}

		$user = $this->userSession->getUser();
		if ($user === null) {
			return new SearchOutcome([], [], $startCursor, false, false, SearchOutcome::FAILURE_NO_HOME_FOLDER);
		}

		return $this->searchService->run($user, $query, $titleOnly, $startCursor, $this->caps());
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
	 * The hits of this page as the template wants them: six finished values per
	 * row and no object the template would have to ask questions of.
	 *
	 * The excerpt becomes a list of text pieces and never a string with markup
	 * in it, which is the whole construction of the highlighting on this page
	 * (T-09-02). A hit the excerpt call did not cover gets an empty list, and
	 * the template puts the path in that place: a hit without an excerpt is
	 * better than no hit.
	 *
	 * @return list<array{fileId:int,title:string,path:string,iconUrl:string,url:string,segments:list<array{text:string,mark:bool}>}>
	 */
	private function rows(SearchOutcome $outcome): array {
		$rows = [];

		foreach ($outcome->hits as $hit) {
			$excerpt = $outcome->excerpts[$hit->fileId] ?? null;
			$rows[] = [
				'fileId' => $hit->fileId,
				'title' => $hit->title,
				'path' => $hit->path,
				'iconUrl' => $this->mimeTypes->mimeTypeIcon($hit->mimeType),
				'url' => $this->fileUrl($hit->fileId),
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
	 * @param list<int> $cursors
	 */
	private function previousUrl(string $query, bool $titleOnly, int $page, array $cursors): ?string {
		if ($page <= 1) {
			return null;
		}

		return $this->pageUrl($query, $titleOnly, $page - 1, array_slice($cursors, 0, -1));
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
	 * @param list<int> $cursors
	 */
	private function nextUrl(string $query, bool $titleOnly, int $page, array $cursors, SearchOutcome $outcome): ?string {
		$runFellShort = $outcome->failure !== null
			&& $outcome->failure !== SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED;

		if (!$outcome->hasMore || $page >= self::MAX_PAGE || $runFellShort) {
			return null;
		}

		if ($outcome->nextCursor <= (int)end($cursors)) {
			return null;
		}

		return $this->pageUrl($query, $titleOnly, $page + 1, [...$cursors, $outcome->nextCursor]);
	}

	/**
	 * One address of this route with all four values in it, built by the url
	 * generator rather than glued together, so that the query string is encoded
	 * correctly and a rewritten web root is honoured.
	 *
	 * @param list<int> $cursors
	 */
	private function pageUrl(string $query, bool $titleOnly, int $page, array $cursors): string {
		$arguments = [
			'query' => $query,
			'page' => (string)$page,
			'cursors' => implode('.', $cursors),
		];
		if ($titleOnly) {
			$arguments['names'] = '1';
		}

		return $this->urlGenerator->linkToRoute('findling.page.index', $arguments);
	}
}
