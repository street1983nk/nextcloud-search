<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\ExclusionService;
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
 * Three routes, all reading, and that is the whole class. The third one, the
 * storage question of plan 36-03, answers which storages the container no longer
 * finds in the mount list are deleted or only switched off. The comparison itself
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
 * Nothing here writes, with one narrow exception since plan 33-04. There is no
 * code path from this class into the queue or into the file system, and the
 * read-only gate on the Python side needs no allowlist entry for any route of
 * it, because it only judges writing HTTP methods. That is deliberate and it stays
 * that way: a GET entered into OCS_WRITE_ALLOWLIST would widen a security gate
 * for nothing. The exception is forgetExcludedVerdicts(): the slice removes the
 * stored verdict rows of the files on its page that a rule of today covers
 * (PE-9), which leaves the answer of the route unchanged; its docblock says why
 * that write lives here.
 *
 * The answers carry file ids, etags, sizes, modification times, mimetypes and,
 * since plan 05-03, the end state this side holds for the file as two codes out
 * of the closed list both sides share. No path, no title, no user name, in the
 * answer as much as in the log (T-03-1102): counters, the storage id and the
 * cursor are enough to follow a reconcile. Since the owner decision of
 * 03.10.2026 a row that an exclusion rule of today matches carries
 * skipped(excluded) in those two codes, worked out live on every page and never
 * stored, so that the container leaves it alone instead of requeueing it.
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

	/**
	 * The mark of a row an exclusion rule of today matches, two codes out of the
	 * closed list FileStateService::REASONS (owner decision of 03.10.2026, part a).
	 *
	 * Live and never written into findling_file_state. The container skips a row
	 * with this mark as long as it knows nothing about the file, and it stores
	 * nothing for it either; a stored verdict on either side would outlive a
	 * lifted rule, and the file would stay out of the index for good. Worked out
	 * on every page, the mark disappears with the rule, and the next round reads
	 * the file as ordinary work.
	 */
	private const EXCLUDED_STATE = 'skipped';
	private const EXCLUDED_REASON = 'excluded';

	/**
	 * Storage ids per question of the storage route, the same ceiling as the
	 * lists of QueueController. The container asks only for storages it holds
	 * rows of and no longer finds in the mount list, which is a handful on any
	 * real instance; a list beyond this is a defect and is refused, not clamped,
	 * because a clamped answer would read as "the rest is not gone".
	 */
	private const MAX_STORAGE_IDS = 256;

	public function __construct(
		IRequest $request,
		private StorageService $storageService,
		private FileStateService $fileStateService,
		private ExclusionService $exclusionService,
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
	 * GET /ocs/v2.php/apps/findling/storages/gone?ids[]=...
	 *
	 * Answers with {"gone": [...], "deselected": [...]}, both lists out of the
	 * asked ids and nothing else (plan 36-03, D-36-14, M-32-02). gone is a storage
	 * without a row in oc_storages, deselected one that only a provider a Findling
	 * switch turned off still carries; the reasoning stands at
	 * StorageService::classifyAbsent.
	 *
	 * Only this side sees oc_storages and oc_mounts, and the container must never
	 * delete out of an empty or disturbed mount list alone. So it deletes at once
	 * only what this route confirms and keeps its grace period for the rest. A
	 * companion of an older release answers 404 here, and the container reads
	 * that as "nothing confirmed", which is the safe direction.
	 *
	 * No path, no mount point, no storage key and no user name in the answer or
	 * in the log; a malformed list is refused without naming its values.
	 */
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'GET', url: '/storages/gone')]
	public function goneStorages(): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		$ids = $this->storageIdList($this->request->getParam('ids', []));
		if ($ids === null) {
			return $this->badStorageList();
		}

		try {
			$answer = $this->storageService->classifyAbsent($ids);
		} catch (\Throwable $e) {
			// Same rule as in mounts(): no library message in the log, the
			// exception travels in its own field.
			$this->logger->error('Findling: could not classify the absent storages', ['exception' => $e]);
			return new DataResponse(['error' => 'Storage state is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}

		$this->logger->debug('Findling: classified absent storages', [
			'asked' => count($ids),
			'gone' => count($answer['gone']),
			'deselected' => count($answer['deselected']),
		]);

		return new DataResponse(['gone' => $answer['gone'], 'deselected' => $answer['deselected']]);
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
	 * at withVerdicts below. A file an exclusion rule of today matches carries
	 * skipped(excluded) instead, worked out live through ExclusionService on the
	 * one path space and never stored; the row stays on the page, because a
	 * filtered page would read as final below.
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
			$files = $this->storageService->getFileSlice($storage, $root, $cursor, $size, $this->exclusionPredicate($storage, $root));
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
	 * A row the exclusion predicate flagged carries skipped(excluded) instead,
	 * and that mark outranks whatever findling_file_state holds for the file: the
	 * rule of today is what decides whether the container may fetch it at all.
	 * The flag itself is taken off the row before the answer, so the wire stays
	 * at its seven fields and a container of an older release sees nothing new
	 * but two codes it already ignores.
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
		$stale = [];
		foreach ($files as $row) {
			$excluded = ($row['excluded'] ?? false) === true;
			unset($row['excluded']);
			$fileId = (int)($row['fileId'] ?? 0);
			if ($excluded && isset($verdicts[$fileId])) {
				$stale[] = $fileId;
			}
			$verdict = $excluded
				? ['state' => self::EXCLUDED_STATE, 'reason' => self::EXCLUDED_REASON]
				: ($verdicts[$fileId] ?? ['state' => '', 'reason' => '']);
			$rows[] = $row + $verdict;
		}

		$this->forgetExcludedVerdicts($stale);

		return $rows;
	}

	/**
	 * Remove the stored verdicts of the rows on this page a rule of today covers.
	 *
	 * The one write of this class, and the reason it is here and not in the
	 * crawl (plan 33-04, PE-9, decided after reading both). This is the place
	 * that already holds both halves of the question, the live mark and the
	 * stored verdict, for every file of every mount once per reconcile round,
	 * one statement per page and only for the ids that have a row. It reaches
	 * the two cases way C leaves behind otherwise: a no_text_layer row, which
	 * the acknowledgement of the container never revokes, and a file the
	 * container never knew, which describe() never sees. The crawl would reach
	 * them only on the next recount, which may be days away.
	 *
	 * Why a write under a GET is acceptable here, and stays narrow. No gate
	 * forbids it: the read only gate judges writing HTTP calls of the container
	 * and its allowlist concerns routes that delete index content, while this
	 * deletes rows of this app's own table over the ordinary connection. The
	 * answer of the route does not change by it, because an excluded row
	 * carries skipped(excluded) whatever the table held, so the GET stays
	 * idempotent for its caller. And the ids come from the page this request
	 * read and from isExcluded() on the one path space, never from the caller
	 * (T-33-38).
	 *
	 * A failure here costs this round and not the slice: the verdict is removed
	 * on the next one, and a reconcile that stopped over a cleanup would stop
	 * the repair it exists for.
	 *
	 * @param list<int> $fileIds
	 */
	private function forgetExcludedVerdicts(array $fileIds): void {
		if ($fileIds === []) {
			return;
		}

		try {
			$forgotten = $this->fileStateService->forgetVerdicts($fileIds);
		} catch (\Throwable $e) {
			$this->logger->warning('Findling: could not remove the verdicts of excluded files', ['exception' => $e]);
			return;
		}

		$this->logger->debug('Findling: removed the verdicts of excluded files', ['forgotten' => $forgotten]);
	}

	/**
	 * The rule of today as a question about one internal path, or null.
	 *
	 * Null while no rule is in force, neither a prefix nor a pattern, so an
	 * instance without exclusions pays nothing for this, the same stance as the
	 * event listener and describe(). Both lists since plan 33-02: a guard on the
	 * prefixes alone would leave every row of an instance with patterns only
	 * unmarked (pitfall 1 of the phase 33 research).
	 * Otherwise the root of the mount is resolved once per page and every row
	 * is asked through the one helper on the one path space, exactly the shape of
	 * the crawl (StorageCrawlJob), so that the slice, the crawl, the listener and
	 * describe() cannot disagree about a file. Nothing of the path reaches the
	 * log or the answer (T-03-1102).
	 *
	 * @return (\Closure(string): bool)|null
	 */
	private function exclusionPredicate(int $storage, int $root): ?\Closure {
		if (!$this->exclusionService->hasRules()) {
			return null;
		}

		$mountRoot = $this->storageService->mountRootPath($storage, $root);
		$exclusions = $this->exclusionService;

		return static fn (string $path): bool => $exclusions->isExcluded($exclusions->mountRelativePath($path, $mountRoot));
	}

	/**
	 * The attribute on every route of this class answers "is this a registered
	 * external app", not "is this our external app". Every other backend on the
	 * instance passes that test, so without this comparison an unrelated
	 * container could read the file list of the whole instance or ask about its
	 * storages through these routes (T-03-1101, T-36-09). AppAPI puts the
	 * calling app id into this header.
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

	/**
	 * The ids of the storage route as a list of positive integers, or null.
	 *
	 * The shape of QueueController::intList: at most MAX_STORAGE_IDS entries,
	 * each a positive int or a string of digits, and the whole request refused
	 * on the first entry that is not. A partially answered question would let
	 * the container read an id that was dropped here as "not gone".
	 *
	 * A string of digits counts only in its canonical form, the one that reads
	 * back as itself (launch audit L-36-02): the cast clamps a number past
	 * PHP_INT_MAX and drops leading noughts, and the answer would then name a
	 * storage nobody asked about.
	 *
	 * @return list<int>|null
	 */
	private function storageIdList(mixed $raw): ?array {
		if (!is_array($raw) || count($raw) > self::MAX_STORAGE_IDS) {
			return null;
		}

		$ids = [];
		foreach ($raw as $value) {
			if (is_int($value)) {
				$id = $value;
			} elseif (is_string($value) && ctype_digit($value)) {
				$id = (int)$value;
				if ((string)$id !== $value) {
					return null;
				}
			} else {
				return null;
			}

			if ($id <= 0) {
				return null;
			}

			$ids[$id] = true;
		}

		return array_keys($ids);
	}

	/**
	 * A storage question that is not a list of storage ids, refused before it
	 * reaches the database. The values are not logged, for the same reason as
	 * in badMount().
	 */
	private function badStorageList(): DataResponse {
		$this->logger->warning('Findling: rejected a storage question without a usable id list');

		return new DataResponse(
			['error' => 'Storage list is not valid.'],
			Http::STATUS_BAD_REQUEST,
		);
	}
}
