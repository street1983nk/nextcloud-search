<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Text\PlainText;
use OCP\App\IAppManager;
use OCP\Http\Client\IResponse;
use OCP\IAppConfig;
use OCP\IUserManager;
use Psr\Container\ContainerExceptionInterface;
use Psr\Container\NotFoundExceptionInterface;
use Psr\Log\LoggerInterface;

/**
 * The one and only place in this app that talks to the container.
 *
 * Keeping the call in a single class keeps the timeout, the shape of an error
 * and the way this app degrades in exactly one spot. Every failure mode below
 * ends in an empty result: a missing, stopped or slow backend must cost the
 * user a result group, never the whole search.
 *
 * Nothing here writes user content into the log. Transport status codes and
 * transport error texts are logged, search terms, titles and snippets are not.
 *
 * This class deliberately makes no permission decision. It used to, and that is
 * the change of this plan: the recheck belongs into the search provider, which
 * is the only place that knows how many hits are going to be displayed. What is
 * left here is a boundary of a different kind. Everything arriving from the
 * container is unconfirmed until the provider has resolved it against the
 * user's own folder, so a candidate is stripped down to its file id on the way
 * in. A backend that volunteers a title or a snippet before the recheck has
 * happened does not get to have that field forwarded.
 *
 * The two calls are separate on purpose, see SRCH-02: a snippet is file
 * content, and file content is only ever fetched for hits that already survived
 * the recheck.
 *
 * Since phase 4 there is a third caller with a different clock. The admin page
 * reads counters rather than content, it has no unified search waiting behind
 * it, and it therefore gets its own timeout and its own method. What it shares
 * with the two above is the pre-flight and the four failure cases, because the
 * way this app degrades has to stay one answer no matter who asked.
 *
 * Phase 5 adds the lockstep check of D-11, and it is a boundary of a third
 * kind: not "may this user see it" and not "is this answer well formed", but
 * "are the two halves talking about the same protocol at all". Both halves carry
 * the same major and minor by release policy, this half reads its own version
 * out of IAppManager and the other one out of the ``appVersion`` field of
 * ``GET /status``, and a mismatch of major or minor makes the search answer
 * with nothing rather than with something. That is the one situation where a
 * silent hit is worse than no hit: neither half can say what the other one
 * meant, so a result would be a guess presented as a finding.
 *
 * The check is deliberately NOT an authentication. ``appVersion`` comes from
 * the environment AppAPI set, so it is as trustworthy as the registration, and
 * a container that wanted to lie about it could. What keeps a foreign container
 * out is the signed AppAPI path plus ``rejectForeignCaller`` on the routes of
 * this app, and nothing here (T-05-25).
 *
 * @final This class is not meant to be extended, and the keyword is gone for one
 *        reason only: PHPUnit cannot create a test double of a final class, and
 *        Provider takes this class by its concrete type. Behaviours 4 and 5 of
 *        docs/testing.md are statements about Provider::search over a controlled
 *        answer of this service, so without a double they cannot be asserted at
 *        all. The annotation is what static analysis and a reader go by; nothing
 *        in this repository extends this class, and nothing should.
 */
class ExAppService {
	/**
	 * One and a half seconds per call, and the arithmetic behind it.
	 *
	 * The AppAPI default is three seconds and AppAPI itself enforces no ceiling,
	 * so the value has to be chosen here. Two calls at 1.5 s stay under the
	 * 2.5 s wall clock the provider budgets for the whole result group, and the
	 * measured work inside the container is a few milliseconds for either call:
	 * what the timeout covers is the proxy round trip and a cold start, not the
	 * search. The previous value of two seconds was budgeted for a single call
	 * and would allow four seconds across the two.
	 *
	 * This is the ceiling per call, never the floor: every call shrinks it to
	 * what is left of the caller's budget (perf audit H5). A deadline that was
	 * only checked BEFORE a call let 2.49 s of spent budget plus a full 1.5 s
	 * timeout add up to four real seconds, and the unified search waits for
	 * every provider.
	 */
	private const REQUEST_TIMEOUT_SECONDS = 1.5;

	/**
	 * Two seconds for a reading call of the admin page, and the arithmetic is a
	 * different one from the search above.
	 *
	 * An admin page may wait longer than the unified search: nobody is typing,
	 * there is no second provider whose result group is delayed by this one, and
	 * the page is opened when something is already suspected to be wrong, which
	 * is exactly when a container is slow to answer. So the ceiling is higher
	 * than the 1.5 s of a search call.
	 *
	 * It stays small all the same, and that is the other half of the reasoning.
	 * A hung container must not take the administration of the instance with it:
	 * the settings page has to render, say "the backend does not answer" and
	 * keep the numbers it does have (T-04-15). Two seconds is the longest an
	 * admin waits without deciding that the page itself is broken.
	 */
	private const ADMIN_REQUEST_TIMEOUT_SECONDS = 2.0;

	/**
	 * Below this remaining budget a call is not placed at all. An answer that
	 * arrives after the unified search stopped waiting costs a round trip and
	 * buys nothing.
	 */
	private const MIN_CALL_SECONDS = 0.3;

	/**
	 * The one title that is allowed to arrive without a file behind it. It is
	 * the diagnostic path of phase 1 and it stays: a hit whose text is composed
	 * inside the container out of host name, timestamp and the user id from the
	 * signed header is the shortest possible answer to "does the answer come
	 * from the running backend". The container only produces it for the search
	 * term that is its own name, so ordinary searches never see it. The string
	 * is frozen on both sides, see CANARY_TITLE in
	 * backend/src/findling/api/search.py.
	 */
	private const CANARY_TITLE = 'findling-canary';

	/**
	 * Hard ceiling on the answer before it is parsed. One megabyte is orders of
	 * magnitude above the largest legitimate answer, and json_decode() on an
	 * unbounded string is the cheapest way to turn a broken backend into an out
	 * of memory of the whole PHP request.
	 */
	private const MAX_BODY_BYTES = 1048576;

	/**
	 * Ceilings in characters, not bytes. Both are defense in depth: the search
	 * dialog renders the fields as text, and the backend is expected to send
	 * short strings anyway. A backend that sends a megabyte long snippet is a
	 * defect, and this is where the defect stops being the user's problem.
	 */
	private const MAX_TITLE_LENGTH = 255;
	private const MAX_SNIPPET_LENGTH = 1000;

	/**
	 * How many highlight ranges of a single snippet are forwarded. A German
	 * compound is split into parts and every part inherits the offsets of the
	 * whole word, so a handful of ranges per snippet is normal and thirty two
	 * is already generous.
	 */
	private const MAX_HIGHLIGHTS = 32;

	/**
	 * The range the backend accepts, see the request models in
	 * backend/src/findling/api/. Outside of it the request fails validation with
	 * a 422, which arrives here as an empty result group and looks exactly like
	 * "nothing found". Clamping instead means the user gets the first hits of a
	 * too large request rather than silence.
	 */
	private const MIN_LIMIT = 1;
	private const MAX_LIMIT = 100;

	/**
	 * How many file ids one snippet request may carry. The provider never asks
	 * for more than its display limit, so this only bounds a caller that has
	 * gone wrong.
	 */
	private const MAX_SNIPPET_IDS = 100;

	/**
	 * The three verdicts of the lockstep check, and there is no fourth.
	 *
	 * ``unknown`` is not a weaker ``drift`` and it is not a weaker ``match``
	 * either: it is the answer for a container that did not say, and the only
	 * one that changes nothing about the search. A container of a version older
	 * than this field reaches exactly this verdict, once, on the update that
	 * introduces it (T-05-27).
	 */
	public const LOCKSTEP_MATCH = 'match';
	public const LOCKSTEP_DRIFT = 'drift';
	public const LOCKSTEP_UNKNOWN = 'unknown';

	/**
	 * The version of the other half, as it was last reported.
	 *
	 * Written whenever something read ``GET /status``, which is the admin page,
	 * and read by the search path, which has no status call of its own. Without
	 * this the drift could only be noticed by a request that asked for it, and
	 * asking for it once per keystroke of the unified search would be a round
	 * trip per keystroke for a value that moves when a container restarts.
	 *
	 * The consequence is written down rather than glossed over: on an instance
	 * where nobody ever opened the settings page there is nothing on record, the
	 * search therefore behaves exactly as it did before, and the page is what
	 * turns the drift into a verdict. An admin whose search stopped finding
	 * things opens that page, which is the same route by which every other
	 * diagnosis of this app is reached.
	 */
	public const KEY_BACKEND_VERSION = 'backend_app_version';

	/**
	 * What a version has to look like before it is compared or shown.
	 *
	 * Major and minor are mandatory, the patch part is optional, and a prerelease
	 * tail is allowed because the store schema allows one. The pattern is not
	 * cosmetics: the value arrives from across the trust boundary and is printed
	 * on an admin page, so anything that is not a version is refused here rather
	 * than bounded later, and the verdict for it is ``unknown`` and never
	 * ``drift``. A container that answers nonsense is a broken container, not a
	 * reason to switch the search off.
	 */
	private const VERSION_PATTERN = '/^\d{1,5}\.\d{1,5}(?:\.[0-9A-Za-z][0-9A-Za-z.-]{0,19})?$/';

	public function __construct(
		private IAppManager $appManager,
		private IUserManager $userManager,
		private IAppConfig $appConfig,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * The lockstep verdict for one answer of ``GET /status`` (D-11).
	 *
	 * No round trip of its own: the caller already has the status answer, this
	 * reads one field out of it and compares. Null is accepted and means the
	 * container did not answer at all, which is ``unknown`` and not ``drift``,
	 * because the page already says "the backend does not answer" and two
	 * statements about one silence would leave an admin choosing between them.
	 *
	 * Major and minor are compared exactly and the patch part is expressly NOT
	 * compared. The protocol between the halves changes with a minor by release
	 * policy, never with a patch, so comparing patches would force two releases
	 * where one is enough and would turn every hotfix of one half into an
	 * instance whose search answers nothing.
	 *
	 * A missing ``appVersion`` is the container of an older release, which is
	 * exactly what an instance looks like for the minutes between updating one
	 * half and the other. It is ``unknown``: the search keeps working, the page
	 * says nothing about it, and the next answer of a current container settles
	 * the question.
	 *
	 * @param array<mixed>|null $status the decoded body of GET /status, or null
	 * @return array{state:string, companion:string, container:string}
	 */
	public function lockstep(?array $status): array {
		$answer = $status ?? [];
		$companion = $this->ownVersion();
		$container = $this->versionOrNothing(is_string($answer['appVersion'] ?? null) ? $answer['appVersion'] : '');

		if ($companion === '' || $container === '') {
			return [
				'state' => self::LOCKSTEP_UNKNOWN,
				'companion' => $companion,
				'container' => $container,
			];
		}

		$this->rememberBackendVersion($container);

		return [
			'state' => $this->majorMinor($companion) === $this->majorMinor($container)
				? self::LOCKSTEP_MATCH
				: self::LOCKSTEP_DRIFT,
			'companion' => $companion,
			'container' => $container,
		];
	}

	/**
	 * The drift that is on record, for a caller that cannot ask the container.
	 *
	 * Null means "nothing to act on", and it covers both of the two harmless
	 * cases: the versions agree, or no version was ever recorded. Only a
	 * recorded version that disagrees in major or minor with this half produces
	 * an answer, and the two numbers travel with it so that whoever reports the
	 * outage can name them.
	 *
	 * @return array{companion:string, container:string}|null
	 */
	public function driftOnRecord(): ?array {
		$container = $this->versionOrNothing(
			$this->appConfig->getValueString(Application::APP_ID, self::KEY_BACKEND_VERSION, ''),
		);
		if ($container === '') {
			return null;
		}

		$companion = $this->ownVersion();
		if ($companion === '' || $this->majorMinor($companion) === $this->majorMinor($container)) {
			return null;
		}

		return ['companion' => $companion, 'container' => $container];
	}

	/**
	 * The version of this half, out of the app info Nextcloud already holds.
	 *
	 * ``getAppVersion`` answers out of the loaded app info, so this costs no
	 * query. An app that Nextcloud does not know answers ``0``, which the
	 * pattern refuses, and the verdict for it is ``unknown``: whatever that
	 * would be, it is not a statement about the container.
	 */
	private function ownVersion(): string {
		return $this->versionOrNothing($this->appManager->getAppVersion(Application::APP_ID));
	}

	/**
	 * A version string that has the shape of a version, or an empty string.
	 *
	 * Trimmed and then matched as a whole. Everything else is an empty string,
	 * which every reader of this class treats as "not known": that is the safe
	 * direction, because the alternative is either comparing two things that are
	 * not versions or printing a container's free text on an admin page.
	 */
	private function versionOrNothing(string $version): string {
		$candidate = trim($version);

		return preg_match(self::VERSION_PATTERN, $candidate) === 1 ? $candidate : '';
	}

	/**
	 * Major and minor of a version that has already passed the pattern, as one
	 * string. The pattern guarantees both parts, so there is nothing to default.
	 */
	private function majorMinor(string $version): string {
		$parts = explode('.', $version);

		return $parts[0] . '.' . $parts[1];
	}

	/**
	 * Remember the version of the other half, and only when it changed.
	 *
	 * The admin page polls every five seconds, so an unconditional write would
	 * be one appconfig update per poll for a value that moves when somebody
	 * restarts a container. Same shape and same reason as
	 * SettingsService::rememberContainerCap.
	 */
	private function rememberBackendVersion(string $version): void {
		if ($version === $this->appConfig->getValueString(Application::APP_ID, self::KEY_BACKEND_VERSION, '')) {
			return;
		}

		$this->appConfig->setValueString(Application::APP_ID, self::KEY_BACKEND_VERSION, $version);
	}

	/**
	 * Stage one: candidates, without a single byte of file content.
	 *
	 * Null and an empty candidate list are two different answers and the caller
	 * has to be able to tell them apart. Null means "no usable answer", so a
	 * missing backend, a timeout or a malformed body, and the caller stops
	 * asking. An empty list means the index has nothing more to offer for this
	 * page, which is an ordinary result.
	 *
	 * @return array{candidates:list<array{fileId:int,title?:string,snippet?:string}>,hasMore:bool,nextOffset:int,degraded:bool}|null
	 */
	public function searchCandidates(string $userId, string $term, int $limit, int $offset, bool $titleOnly, float $secondsLeft = self::REQUEST_TIMEOUT_SECONDS): ?array {
		// An empty term is not an error, it is what the unified search sends
		// while the user is still typing, and it can only ever produce a 422
		// over there. A round trip per keystroke for a request that cannot
		// succeed is the expensive half of that.
		$term = trim($term);
		if ($term === '') {
			return null;
		}

		$limit = max(self::MIN_LIMIT, min(self::MAX_LIMIT, $limit));
		$offset = max(0, $offset);

		$decoded = $this->call('/search', $userId, [
			'query' => $term,
			'limit' => $limit,
			'offset' => $offset,
			'titleOnly' => $titleOnly,
		], $secondsLeft);
		if ($decoded === null) {
			return null;
		}

		$candidates = $decoded['candidates'] ?? null;
		if (!is_array($candidates)) {
			$this->logger->warning('Findling: malformed candidate answer');
			return null;
		}

		$hasMore = ($decoded['hasMore'] ?? false) === true;
		$nextOffset = $decoded['nextOffset'] ?? null;
		if (!is_int($nextOffset) || $nextOffset < 0) {
			// A cursor that is not a cursor ends the paging instead of being
			// guessed at: a guessed offset either repeats a page or skips one,
			// and both are invisible in the result.
			$nextOffset = $offset;
			$hasMore = false;
		}

		if ($hasMore && $nextOffset <= $offset) {
			// A cursor that does not advance would make the caller ask for the
			// same page again. The round limit over there would catch it, this
			// keeps it from costing a round at all.
			$this->logger->warning('Findling: backend cursor did not advance, treating the page as the last one');
			$hasMore = false;
		}

		return [
			'candidates' => $this->filterCandidates($candidates),
			'hasMore' => $hasMore,
			'nextOffset' => $nextOffset,
			'degraded' => ($decoded['degraded'] ?? false) === true,
		];
	}

	/**
	 * Stage two: the text excerpt, for confirmed file ids only.
	 *
	 * Every failure ends in an empty array rather than in a null, because there
	 * is nothing the caller could do differently: the hits are already
	 * confirmed, and they are shown with the path as their subline instead of
	 * an excerpt. A hit without a snippet beats no hit at all.
	 *
	 * @param list<int> $fileIds file ids that have passed the permission recheck
	 * @return array<int,array{text:string,highlights:list<array{int,int}>}>
	 */
	public function snippets(string $userId, string $term, array $fileIds, bool $titleOnly, float $secondsLeft = self::REQUEST_TIMEOUT_SECONDS): array {
		$term = trim($term);
		if ($term === '') {
			return [];
		}

		$wanted = [];
		foreach ($fileIds as $fileId) {
			if (is_int($fileId) && $fileId > 0) {
				$wanted[$fileId] = true;
			}
		}
		$wanted = array_slice(array_keys($wanted), 0, self::MAX_SNIPPET_IDS);
		if ($wanted === []) {
			return [];
		}

		$decoded = $this->call('/snippets', $userId, [
			'query' => $term,
			'fileIds' => array_values($wanted),
			'titleOnly' => $titleOnly,
		], $secondsLeft);
		if ($decoded === null) {
			return [];
		}

		$snippets = $decoded['snippets'] ?? null;
		if (!is_array($snippets)) {
			$this->logger->warning('Findling: malformed snippet answer');
			return [];
		}

		return $this->filterSnippets($snippets, array_flip($wanted));
	}

	/**
	 * A reading GET against the container, for the admin page and nothing else.
	 *
	 * Separate from call() above rather than a parameter on it, and the reason
	 * is the budget and not the verb. A search call shrinks its timeout to what
	 * is left of the wall clock the unified search grants a provider; an admin
	 * page has no such clock and its own, larger ceiling, and folding both into
	 * one method would mean one of the two callers reading a rule that is not
	 * its own. The four failure cases below are the same four, in the same
	 * order, for the same reasons.
	 *
	 * For GET, AppAPI appends the parameters with http_build_query, so this is
	 * a query string call and there is no JSON body on the way out.
	 *
	 * @param array<string,mixed> $params appended to the URL as a query string
	 * @return array<mixed>|null null on every failure, so that the caller can
	 *                           say "not reachable" instead of "not indexed"
	 */
	public function adminGet(string $path, string $userId, array $params): ?array {
		$response = $this->proxyRequest($path, $userId, 'GET', $params, self::ADMIN_REQUEST_TIMEOUT_SECONDS);
		if ($response === null) {
			return null;
		}

		// Case 1 first, always, and here it matters even more than in the
		// search: AppAPI catches every transport exception and hands back an
		// array, so a stopped, unknown or timed out backend arrives at this
		// line. A method call on that array would be a fatal error, and the
		// page that was supposed to report the outage would be the outage.
		if (is_array($response)) {
			$this->logger->warning('Findling: backend unreachable for the admin page', [
				'path' => $path,
				'error' => $response['error'] ?? 'unknown',
			]);
			return null;
		}

		// Case 2. AppAPI hard sets http_errors to false, so 4xx and 5xx arrive
		// as an ordinary response object instead of throwing.
		/** @var IResponse $response */
		if ($response->getStatusCode() >= 400) {
			$this->logger->warning('Findling: backend returned an error for the admin page', [
				'path' => $path,
				'status' => $response->getStatusCode(),
			]);
			return null;
		}

		// Case 3. A 2xx promises neither a body that parses nor one that fits
		// into memory, and the length is checked before the parser sees it.
		$responseBody = $response->getBody();
		if (!is_string($responseBody) || strlen($responseBody) > self::MAX_BODY_BYTES) {
			$this->logger->warning('Findling: backend answer for the admin page is not a bounded string body', [
				'path' => $path,
				'bytes' => is_string($responseBody) ? strlen($responseBody) : -1,
			]);
			return null;
		}

		// Case 4.
		$decoded = json_decode($responseBody, true);
		if (!is_array($decoded)) {
			$this->logger->warning('Findling: malformed backend response for the admin page', ['path' => $path]);
			return null;
		}

		return $decoded;
	}

	/**
	 * The one outbound request of this app, in one method for all three callers.
	 *
	 * Everything that leaves this process towards the container goes through
	 * here: the pre-flight, the app id both halves are registered under, and the
	 * timeout of this particular call. Written once rather than three times,
	 * because "this app talks to exactly one container and only through AppAPI"
	 * is a statement a reader should be able to check by reading a single method.
	 *
	 * It is protected rather than private, and that is the one concession this
	 * class makes to the unit suite. ``OCA\AppAPI\PublicFunctions`` is a class of
	 * another app: it is absent from the autoload space the suite runs in, so it
	 * cannot be doubled, and without a double every statement about what happens
	 * to an answer would need a registered container behind it. This method has a
	 * signature of our own and a return type of our own, so a test double of it
	 * is a double of the transport and of nothing else. Nothing in this
	 * repository overrides it, and nothing should; see the ``@final`` note on the
	 * class.
	 *
	 * @param array<string,mixed> $params body for POST, query string for GET
	 * @return array<mixed>|IResponse|null null when the pre-flight refused, an
	 *                                     array when AppAPI turned a transport
	 *                                     failure into one, a response otherwise
	 */
	protected function proxyRequest(string $path, string $userId, string $method, array $params, float $timeout): array|IResponse|null {
		$appApi = $this->publicFunctions($userId);
		if ($appApi === null) {
			return null;
		}

		return $appApi->exAppRequest(
			Application::BACKEND_APP_ID,
			$path,
			$userId,
			$method,
			$params,
			['timeout' => $timeout],
		);
	}

	/**
	 * The pre-flight both call paths share: a real user, app_api enabled for
	 * them, and the public functions of AppAPI actually resolvable.
	 *
	 * Extracted rather than written twice, because these three checks are not
	 * about a single request: they are the statement that this app talks to
	 * exactly one container and only through AppAPI. info.xml has no way to
	 * declare an app to app dependency, so the bond to app_api is a runtime
	 * check, and without it a missing AppAPI would not cost a result group but
	 * the whole request that touched it.
	 */
	private function publicFunctions(string $userId): ?\OCA\AppAPI\PublicFunctions {
		$user = $this->userManager->get($userId);
		if ($user === null) {
			// Without a user object the app check below would silently fall
			// back to the session user, which is a different question.
			$this->logger->info('Findling: unknown user, no call to the backend');
			return null;
		}

		if (!$this->appManager->isEnabledForUser('app_api', $user)) {
			$this->logger->info('Findling: app_api is not enabled, no call to the backend');
			return null;
		}

		try {
			return \OCP\Server::get(\OCA\AppAPI\PublicFunctions::class);
		} catch (ContainerExceptionInterface|NotFoundExceptionInterface) {
			$this->logger->info('Findling: AppAPI public functions unavailable');
			return null;
		}
	}

	/**
	 * The four silent failure paths of phase 1, in one place for both calls.
	 *
	 * Array with an error key, status code 400 and above, a body that is not a
	 * bounded string, a body that does not parse into an array. None of them
	 * throws, every one of them ends in a null.
	 *
	 * @param array<string,mixed> $body
	 * @param float $secondsLeft what is left of the caller's wall clock; the
	 *                           timeout of this call never exceeds it
	 * @return array<mixed>|null
	 */
	private function call(string $path, string $userId, array $body, float $secondsLeft = self::REQUEST_TIMEOUT_SECONDS): ?array {
		$timeout = min(self::REQUEST_TIMEOUT_SECONDS, $secondsLeft);
		if ($timeout < self::MIN_CALL_SECONDS) {
			// Not an error: the budget is spent, and the caller shows what it
			// already has instead of waiting for an answer nobody displays.
			return null;
		}

		$response = $this->proxyRequest($path, $userId, 'POST', $body, $timeout);
		if ($response === null) {
			// Unknown user, app_api switched off, or AppAPI not resolvable. All
			// three cost this user a result group and never the whole search.
			return null;
		}

		// Case 1 first, always. AppAPI catches every transport exception and
		// hands back an array, so an unknown, unreachable or timed out backend
		// arrives here. Calling a method on that array would be a fatal error
		// and would destroy the entire search request.
		if (is_array($response)) {
			// warning, not info, and deliberately the same level as the
			// malformed answer below: an unreachable backend is the one failure
			// mode that costs the user a whole result group without anything on
			// screen saying so. An info line is not what an admin looks at when
			// a user reports that the search finds nothing.
			//
			// The unified search asks once per keystroke, so this line can
			// repeat. Damping it needs state that outlives the request
			// (ICacheFactory), which is not worth a dependency here: phase 4
			// builds the status page out of exactly this signal and owns the
			// aggregation then.
			$this->logger->warning('Findling: backend unreachable', [
				'path' => $path,
				'error' => $response['error'] ?? 'unknown',
			]);
			return null;
		}

		// Case 2. AppAPI hard sets http_errors to false, so 4xx and 5xx arrive
		// as an ordinary response object instead of throwing.
		/** @var IResponse $response */
		if ($response->getStatusCode() >= 400) {
			$this->logger->warning('Findling: backend returned an error', [
				'path' => $path,
				'status' => $response->getStatusCode(),
			]);
			return null;
		}

		// Case 3. A 2xx does not promise a body that parses, and it does not
		// promise a body that fits into memory either. The length is checked
		// before the parser sees it, because json_decode() builds the whole
		// tree.
		$responseBody = $response->getBody();
		if (!is_string($responseBody) || strlen($responseBody) > self::MAX_BODY_BYTES) {
			$this->logger->warning('Findling: backend answer is not a bounded string body', [
				'path' => $path,
				'bytes' => is_string($responseBody) ? strlen($responseBody) : -1,
			]);
			return null;
		}

		// Case 4.
		$decoded = json_decode($responseBody, true);
		if (!is_array($decoded)) {
			$this->logger->warning('Findling: malformed backend response', ['path' => $path]);
			return null;
		}

		return $decoded;
	}

	/**
	 * What survives of a candidate: its file id, and nothing else.
	 *
	 * The container has no way of knowing what this user may see, so what it
	 * sends is a proposal. Anything that carries a name or a text at this point
	 * would be shown before the recheck has run, and a proposal that reaches
	 * the screen without the recheck is exactly the information disclosure this
	 * whole two stage protocol exists to prevent. Title and path of a confirmed
	 * hit come out of the node, the excerpt comes out of the second call.
	 *
	 * The one exception is the canary, which has no file behind it and could
	 * therefore never survive a recheck. It is accepted under its exact title
	 * and under no other, and everything else with a file id that cannot point
	 * at a file is a defect and is dropped.
	 *
	 * @param array<mixed> $candidates
	 * @return list<array{fileId:int,title?:string,snippet?:string}>
	 */
	private function filterCandidates(array $candidates): array {
		$kept = [];
		$dropped = 0;

		foreach ($candidates as $candidate) {
			if (!is_array($candidate) || !isset($candidate['fileId']) || !is_int($candidate['fileId'])) {
				$dropped++;
				continue;
			}

			$fileId = $candidate['fileId'];
			if ($fileId > 0) {
				$kept[] = ['fileId' => $fileId];
				continue;
			}

			$title = is_string($candidate['title'] ?? null)
				? PlainText::bounded($candidate['title'], self::MAX_TITLE_LENGTH)
				: null;
			$snippet = is_string($candidate['snippet'] ?? null)
				? PlainText::bounded($candidate['snippet'], self::MAX_SNIPPET_LENGTH)
				: null;
			if ($title !== self::CANARY_TITLE || $snippet === null) {
				$dropped++;
				continue;
			}

			$kept[] = [
				'fileId' => 0,
				'title' => self::CANARY_TITLE,
				'snippet' => $snippet,
			];
		}

		if ($dropped > 0) {
			$this->logger->warning('Findling: dropped malformed candidates', ['count' => $dropped]);
		}

		return $kept;
	}

	/**
	 * Excerpts for the ids that were asked for, and for no others.
	 *
	 * An answer that carries a file id nobody asked about is dropped rather
	 * than passed on. The container applies its own access prefilter, but that
	 * prefilter is not the boundary, and an excerpt for a file this request
	 * never confirmed has no way of reaching the screen from here.
	 *
	 * @param array<mixed> $snippets
	 * @param array<int,int> $wanted file id as key
	 * @return array<int,array{text:string,highlights:list<array{int,int}>}>
	 */
	private function filterSnippets(array $snippets, array $wanted): array {
		$result = [];
		$dropped = 0;

		foreach ($snippets as $key => $snippet) {
			$fileId = is_int($key) ? $key : (is_string($key) && ctype_digit($key) ? (int)$key : 0);
			if ($fileId <= 0 || !isset($wanted[$fileId]) || !is_array($snippet)) {
				$dropped++;
				continue;
			}

			$raw = $snippet['text'] ?? null;
			if (!is_string($raw)) {
				$dropped++;
				continue;
			}

			$text = PlainText::bounded($raw, self::MAX_SNIPPET_LENGTH);
			if ($text === null) {
				$dropped++;
				continue;
			}

			// The highlights count characters of exactly the string the
			// container sent, so an offset survives only as long as every
			// character kept its position. PlainText::bounded does exactly two
			// things: it replaces single characters one for one, which moves
			// nothing, and it cuts at the ceiling, which moves nothing either
			// but drops the tail. Equal length therefore means equal positions,
			// and equal length is what is compared.
			//
			// The comparison used to be identity. That was correct while the
			// cleaning deleted characters, and it became too strict the moment
			// it started replacing them: every excerpt out of a multi line PDF
			// carries a line break, and identity would throw away the
			// highlights of exactly those documents this phase is about. What
			// stays out of bounds is guessing an offset that has moved.
			$length = mb_strlen($text, 'UTF-8');
			$highlights = $length === mb_strlen($raw, 'UTF-8')
				? $this->filterHighlights($snippet['highlights'] ?? null, $length)
				: [];

			$result[$fileId] = ['text' => $text, 'highlights' => $highlights];
		}

		if ($dropped > 0) {
			$this->logger->warning('Findling: dropped malformed snippets', ['count' => $dropped]);
		}

		return $result;
	}

	/**
	 * Ranges as two character offsets, inside the text and in ascending order.
	 *
	 * They travel to the client as an attribute and are never turned into
	 * markup, so a wrong range cannot inject anything; it can only point at the
	 * wrong word. Checking them anyway costs nothing and keeps a defect in the
	 * container from looking like a defect in the dialog.
	 *
	 * @return list<array{int,int}>
	 */
	private function filterHighlights(mixed $highlights, int $length): array {
		if (!is_array($highlights)) {
			return [];
		}

		$ranges = [];
		foreach ($highlights as $range) {
			if (count($ranges) >= self::MAX_HIGHLIGHTS) {
				break;
			}

			if (!is_array($range) || !isset($range[0], $range[1]) || !is_int($range[0]) || !is_int($range[1])) {
				continue;
			}

			$start = $range[0];
			$end = $range[1];
			if ($start < 0 || $end <= $start || $end > $length) {
				continue;
			}

			$ranges[] = [$start, $end];
		}

		return $ranges;
	}
}
