<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;
use Psr\Log\LoggerInterface;

/**
 * What Nextcloud really has, so that the container can compare it against what
 * it indexed.
 *
 * Two routes, both reading, and that is the whole class. The comparison itself
 * runs in the container (plan 03-12), because findling_file_state holds no
 * indexed rows at all: phase 2 records failures and skips there and nothing
 * else, so this side cannot form "in the index, but no longer on disk" without
 * becoming a second source of truth about the same fact. A background job also
 * has no user, so the other direction would need a route with PUBLIC access and
 * the statement about the reachable surface of this app would fall. The price is
 * written down where it belongs: the reconcile cursor lives in the container,
 * unlike the crawl cursor (IDX-02). A lost reconcile cursor costs a repetition
 * and never work, because the reconcile is pure repair and idempotent.
 *
 * Nothing here writes. There is no code path from this class into the queue, into
 * the state table or into the file system, and the read-only gate on the Python
 * side needs no allowlist entry for either route, because it only judges writing
 * HTTP methods. That is deliberate and it stays that way: a GET entered into
 * OCS_WRITE_ALLOWLIST would widen a security gate for nothing.
 *
 * The answers carry file ids, etags, sizes, modification times, mimetypes and,
 * since plan 05-03, the end state this side holds for the file as two codes out
 * of the closed list both sides share. No path, no title, no user name, in the
 * answer as much as in the log (T-03-1102): counters, the storage id and the
 * cursor are enough to follow a reconcile.
 *
 * Every method carries the attribute trio fully qualified, in the spelling of
 * QueueController rather than the mixed one of GatewayController, because a grep
 * gate counts them that way and cannot be fooled by an import line. The CSRF
 * exemption is not a weakening: the credential on these routes is the signed
 * AppAPI header and no session is involved that a token could protect.
 */
class ReconcileController extends OCSController {
	/**
	 * Rows per page. Five hundred is the slice size the reconcile of plan 03-12
	 * walks with; it is small enough that one page stays a cheap query at midday
	 * and large enough that a mount of a hundred thousand files is not two
	 * hundred round trips.
	 */
	private const DEFAULT_SLICE = 500;

	/**
	 * A hard bound, not a suggestion. The container is trusted, but this boundary
	 * is the cheapest place at which a defect in the worker stays a clamped
	 * request instead of pulling a whole instance into a single answer
	 * (T-03-1103). Clamped rather than refused, for the same reason as in
	 * QueueController: a caller that asks for too much gets the maximum and makes
	 * progress, instead of looping over a rejection it cannot interpret.
	 */
	private const MAX_SLICE = 2000;

	public function __construct(
		IRequest $request,
		private StorageService $storageService,
		private FileStateService $fileStateService,
		private LoggerInterface $logger,
	) {
		parent::__construct(Application::APP_ID, $request);
	}

	/**
	 * GET /ocs/v2.php/apps/findling/mounts
	 *
	 * Answers with {"mounts": [{storageId, rootId, overriddenRoot}]}, straight out
	 * of StorageService::getMounts() and therefore out of the same source the
	 * crawl walks. A second list of mounts here would be a second answer to
	 * "which mounts are in", and the two would disagree the day external storage
	 * becomes a switch (ADM-04): the reconcile would keep repairing what the crawl
	 * was told to leave alone.
	 */
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'GET', url: '/mounts')]
	public function mounts(): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		try {
			$mounts = [];
			foreach ($this->storageService->getMounts() as $mount) {
				$mounts[] = [
					'storageId' => (int)$mount['storage_id'],
					'rootId' => (int)$mount['root_id'],
					'overriddenRoot' => (int)$mount['overridden_root'],
				];
			}
		} catch (\Throwable $e) {
			// A static sentence and a generic verdict outside; the exception itself
			// travels in the exception field, which Nextcloud renders under the
			// admin's own log level (security audit L6). The rule of this project is
			// that the log carries counters and reason codes and nothing else, and a
			// library message is exactly where a path or an SQL fragment turns up:
			// the mount query names storages and roots of a private instance.
			$this->logger->error('Findling: could not list the mounts', ['exception' => $e]);
			return new DataResponse(['error' => 'Mount list is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}

		return new DataResponse(['mounts' => $mounts]);
	}

	/**
	 * GET /ocs/v2.php/apps/findling/files/slice?storage=&root=&after=&limit=
	 *
	 * Answers with {"files": [{fileId, etag, size, mtime, mime, state, reason}],
	 * "final": bool}, ordered by file id and starting behind the cursor.
	 *
	 * state and reason are the end state findling_file_state holds for the file,
	 * two empty strings for a file it has never heard of. They are what stops the
	 * comparison from requeueing a file this side gave up on; the reasoning sits
	 * at withVerdicts below.
	 *
	 * The final mark is the reason this route exists in this shape. The deletion
	 * rule of the reconcile reads "known locally in the range (after, last id of
	 * the page], but not in the page". Without an upper bound every file behind
	 * the end of the page would be declared deleted, and on the last page there is
	 * no upper bound to have. A page that brought fewer rows than it was allowed
	 * to is the last one, and saying so is cheaper than a second query that counts
	 * (T-03-1104).
	 *
	 * The mimetype filter of the underlying query stays in place, and that has two
	 * consequences worth naming. A file whose type changed to one this app does
	 * not index drops out of the page and is treated as deleted, which is exactly
	 * right: it no longer belongs in the index. But a type that the PHP side
	 * accepts and the Python side does not would be cleaned up and queued again
	 * every single night, and that is precisely what the allowlist gate of plan
	 * 03-10 exists to prevent. The two lists have to stay one list.
	 */
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'GET', url: '/files/slice')]
	public function filesSlice(int $storage = 0, int $root = 0, int $after = 0, int $limit = self::DEFAULT_SLICE): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		// A mount that is not a mount is refused rather than clamped: a storage id
		// of zero names nothing, and the query below would answer it with an
		// exception about a root it could not fetch, which would read like a
		// broken instance instead of a broken request.
		if ($storage <= 0 || $root <= 0) {
			return $this->badMount();
		}

		$size = max(1, min(self::MAX_SLICE, $limit));
		$cursor = max(0, $after);

		try {
			$files = $this->storageService->getFileSlice($storage, $root, $cursor, $size);
			$files = $this->withVerdicts($files);
		} catch (\Throwable $e) {
			// Same rule as in mounts(): no library message in the log.
			$this->logger->error('Findling: could not read a slice of a mount', ['exception' => $e]);
			return new DataResponse(['error' => 'File list is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}

		// Fewer rows than allowed means there is nothing behind this page. The
		// underlying query caps at exactly $size, so the comparison is a decision
		// and not an estimate.
		$final = count($files) < $size;

		$this->logger->debug('Findling: handed out a slice of a mount', [
			'storage_id' => $storage,
			'cursor' => $cursor,
			'rows' => count($files),
			'final' => $final,
		]);

		return new DataResponse(['files' => $files, 'final' => $final]);
	}

	/**
	 * Add the end state this side holds to every row of a page.
	 *
	 * One query for the whole page, next to the one that read the page, and the
	 * reason it is worth the second statement stands at
	 * FileStateService::verdictsFor: the give-up rule lives on this side and the
	 * comparison lives in the container, so without these two codes a file that
	 * was written off as failed(repeatedly_stuck) is requeued every single night
	 * (review finding IN-03 of phase 3). A call per row was the alternative and
	 * would have cost more than the work it saves, because the reconcile walks in
	 * bands of up to MAX_SLICE rows.
	 *
	 * A file without a row carries two empty strings, which is what the container
	 * reads as "no verdict". Empty and absent are deliberately the same value
	 * here: the two fields are new in plan 05-03, and a container of an older
	 * release ignores them, so neither side has to know which release the other
	 * one is.
	 *
	 * @param list<array<string, mixed>> $files
	 * @return list<array<string, mixed>>
	 */
	private function withVerdicts(array $files): array {
		if ($files === []) {
			return [];
		}

		$verdicts = $this->fileStateService->verdictsFor(
			array_map(static fn (array $row): int => (int)($row['fileId'] ?? 0), $files),
		);

		$rows = [];
		foreach ($files as $row) {
			$verdict = $verdicts[(int)($row['fileId'] ?? 0)] ?? ['state' => '', 'reason' => ''];
			$rows[] = $row + $verdict;
		}

		return $rows;
	}

	/**
	 * The attribute on both methods above answers "is this a registered external
	 * app", not "is this our external app". Every other backend on the instance
	 * passes that test, so without this comparison an unrelated container could
	 * read the file list of the whole instance through these two routes
	 * (T-03-1101). AppAPI puts the calling app id into this header.
	 *
	 * The same deliberate residual risk as in GatewayController and
	 * QueueController applies: this trusts AppAPI to have authenticated the caller
	 * before the request arrives. Whoever can forge that header has broken the
	 * AppAPI trust model itself.
	 */
	private function rejectForeignCaller(): ?DataResponse {
		$callerAppId = $this->request->getHeader('EX-APP-ID');
		if ($callerAppId === Application::BACKEND_APP_ID) {
			return null;
		}

		$this->logger->warning('Findling: reconcile called by a foreign ExApp', ['app' => $callerAppId]);

		return new DataResponse(
			['error' => 'This route is reserved for the Findling backend.'],
			Http::STATUS_FORBIDDEN,
		);
	}

	/**
	 * A slice request that names no mount, refused before it reaches the database.
	 *
	 * The offending values are deliberately not logged, in the same spirit as
	 * badList in QueueController: they are unvalidated input, and the log of this
	 * app carries counters and codes and never something somebody else wrote.
	 */
	private function badMount(): DataResponse {
		$this->logger->warning('Findling: rejected a slice request without a usable mount');

		return new DataResponse(
			['error' => 'Malformed mount reference.'],
			Http::STATUS_BAD_REQUEST,
		);
	}
}
