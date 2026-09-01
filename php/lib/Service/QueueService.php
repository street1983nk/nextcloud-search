<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\Db\QueueFile;
use OCA\Findling\Db\QueueMapper;
use OCP\Files\Cache\ICacheEntry;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\IDBConnection;
use Psr\Log\LoggerInterface;

/**
 * Turns rows of the work stock into work orders, and work orders back into
 * end states.
 *
 * A claimed batch carries metadata and no content. The bytes are fetched one by
 * one through the content gateway when a worker is actually free, so the answer
 * to a claim stays small no matter how large the documents behind it are.
 *
 * Nothing here logs a path or a file name. Counters, storage ids and reason
 * codes are enough to see what is happening, and a log line is the one place
 * where the content of a private instance leaves the permission model.
 */
class QueueService {
	/**
	 * How often a row may be handed out before it is given up as
	 * failed(repeatedly_stuck). A row that is claimed and never acknowledged
	 * comes back after the lock expires, and without this ceiling it would
	 * circle forever instead of becoming a visible end state.
	 */
	public const MAX_ATTEMPTS = 3;

	/**
	 * How many rows of one kind a single claim may take.
	 *
	 * The cheap kinds are large, because a permission change is a row and not a
	 * download, and a hundred of them are still less work than one invoice.
	 * content keeps the value the queue had before this phase.
	 *
	 * ocr is two, and that number is arithmetic. An OCR job may run up to 600 s
	 * under the ceiling cascade of plan 03-05; a batch of 32 would be more than
	 * five hours against a claim that expires after 1800 s, so the rows would
	 * come back as free, count a retry each and end as failed(repeatedly_stuck)
	 * while a worker is legitimately still working on them (phase research,
	 * pitfall 11). Two of them stay under the timeout with room to spare.
	 *
	 * @var array<string, int>
	 */
	private const KIND_BATCH = [
		QueueMapper::KIND_ACL => 128,
		QueueMapper::KIND_DELETE => 128,
		QueueMapper::KIND_METADATA => 64,
		QueueMapper::KIND_CONTENT => 32,
		QueueMapper::KIND_OCR => 2,
	];

	public function __construct(
		private QueueMapper $queueMapper,
		private FileStateService $fileStateService,
		private IUserMountCache $userMountCache,
		private IRootFolder $rootFolder,
		private IDBConnection $db,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * Claim a batch and describe every row in it.
	 *
	 * The keys of the returned map are queue row ids, because that is exactly
	 * what comes back on acknowledgement. A row that cannot be described any
	 * more, because the file disappeared between queueing and collecting, is not
	 * delivered: it is deleted and recorded as skipped(gone). Leaving it in place
	 * would mean it travels through the lock timeout again and again until the
	 * end of time.
	 *
	 * The kinds are asked for one after the other, in the order of
	 * QueueMapper::KINDS: acl, delete, metadata, content, ocr. This loop is
	 * where the priority of D-04 lives. A permission change overtakes any
	 * content backlog, however long it is, because the content query is not even
	 * sent before the acl query came back empty. The alternative, a priority
	 * column in ORDER BY, would have cost both indexes of the queue.
	 *
	 * An empty answer for one kind ends that kind and nothing else.
	 *
	 * @return array<int, array<string, mixed>> queue row id to source object
	 */
	public function claim(int $limit, int $maxBytes): array {
		$sources = [];
		$gone = 0;
		$givenUp = 0;

		// Both ceilings of the caller are spent across the kinds and not handed
		// out again per kind, otherwise one round would fetch five times the
		// batch and five times the budget the collector asked for.
		//
		// A kind is never skipped because the budget ran out, though: claimBatch
		// always delivers its first row, budget or not, and that floor is what
		// keeps the trailing OCR track from starving behind a content backlog
		// that fills the budget in every single round (D-07).
		$rows = $limit;
		$budget = $maxBytes;

		foreach (QueueMapper::KINDS as $kind) {
			if ($rows <= 0) {
				break;
			}

			$batch = min(self::KIND_BATCH[$kind] ?? $limit, $rows);
			foreach ($this->queueMapper->claimBatch($batch, $budget, $kind) as $row) {
				$rows--;
				$budget = max(0, $budget - (int)$row->getSize());

				if ($row->getRetries() > self::MAX_ATTEMPTS) {
					$this->finish($row, 'failed', 'repeatedly_stuck');
					$givenUp++;
					continue;
				}

				$source = $this->describe($row);
				if ($source === null) {
					$this->finish($row, 'skipped', 'gone');
					$gone++;
					continue;
				}

				$sources[$row->getId()] = $source;
			}
		}

		if ($gone > 0) {
			$this->logger->info('Findling: dropped queued files that are gone', ['count' => $gone]);
		}

		if ($givenUp > 0) {
			// warning, not info: a row that was handed out three times without
			// ever coming back is the signature of a worker that dies on a
			// specific file, and that is worth an admin's attention.
			$this->logger->warning('Findling: gave up on repeatedly stuck files', ['count' => $givenUp]);
		}

		return $sources;
	}

	/**
	 * Put a file into the work stock, or refresh the row that is already there.
	 *
	 * The size ceiling is not applied here. It belongs to the crawl of plan
	 * 02-04, which sees the entry before it decides to queue it and records
	 * skipped(too_large) instead of queueing, so that an oversized file is a
	 * visible decision and not a silent omission.
	 */
	public function enqueue(ICacheEntry $entry, int $storageId, int $rootId, bool $isUpdate = false): void {
		$size = $entry->getSize();

		$this->queueMapper->enqueue(
			$entry->getId(),
			$storageId,
			$rootId,
			$size > 0 ? (int)$size : 0,
			$isUpdate,
		);
	}

	/**
	 * Acknowledge a batch: remove what was processed, and record a reason for
	 * everything the container could not process.
	 *
	 * Both lists are handled in one transaction. Half an acknowledgement is the
	 * worst of the possible outcomes: rows deleted without their reason recorded
	 * would vanish from the queue and from the diagnosis at the same time.
	 *
	 * @param int[] $queueIds rows that are done
	 * @param array<int, string> $failures queue row id to reason code
	 * @return array{acknowledged:int, recorded:int}
	 */
	public function acknowledge(array $queueIds, array $failures): array {
		$failedIds = array_keys($failures);
		$allIds = array_values(array_unique(array_merge($queueIds, $failedIds)));
		if ($allIds === []) {
			return ['acknowledged' => 0, 'recorded' => 0];
		}

		// The container knows queue ids, the state table knows file ids. The
		// translation has to happen before the rows are deleted, because after
		// the delete the connection between the two is gone.
		$fileIds = [];
		foreach ($this->queueMapper->findByIds($failedIds) as $row) {
			$fileIds[$row->getId()] = $row->getFileId();
		}

		$recorded = 0;
		$this->db->beginTransaction();
		try {
			foreach ($failures as $queueId => $reason) {
				$fileId = $fileIds[$queueId] ?? 0;
				if ($fileId === 0) {
					// The row is already gone, most likely because the lock
					// expired and someone else finished it. Nothing to record.
					continue;
				}

				if ($this->fileStateService->record($fileId, 'failed', $reason)) {
					$recorded++;
				}
			}

			$acknowledged = $this->queueMapper->acknowledge($allIds);
			$this->db->commit();
		} catch (\Throwable $e) {
			$this->db->rollBack();
			throw $e;
		}

		if ($recorded > 0) {
			$this->logger->info('Findling: recorded files the container could not process', ['count' => $recorded]);
		}

		return ['acknowledged' => $acknowledged, 'recorded' => $recorded];
	}

	/**
	 * Hand rows back unprocessed. This is the graceful restart of the container:
	 * what it holds becomes collectable immediately instead of after the lock
	 * timeout.
	 *
	 * @param int[] $queueIds
	 */
	public function unlock(array $queueIds): int {
		return $this->queueMapper->unlock($queueIds);
	}

	/**
	 * @return array{scheduled:int, running:int, failed:int}
	 */
	public function stats(): array {
		return [
			'scheduled' => $this->queueMapper->countScheduled(),
			'running' => $this->queueMapper->countRunning(),
			'failed' => $this->fileStateService->counts()['failed'] ?? 0,
		];
	}

	/**
	 * Build the source object of one row, or null when the file cannot be
	 * resolved any more.
	 *
	 * @return array<string, mixed>|null
	 */
	private function describe(QueueFile $row): ?array {
		$fileId = $row->getFileId();

		// The one place where the kind of a row decides what its source object
		// looks like. Today every kind takes the same route below, and that is
		// correct as long as every queued row belongs to a file that is still
		// there: only create and write reach the queue in this plan.
		//
		// The two kinds that do not fit that route hang their early return here,
		// each together with its counterpart in the container: delete in plan
		// 03-03, which must not resolve a node because the node is gone, and acl
		// in plan 03-04, where an empty user list is the legitimate payload of an
		// unshare and not a reason to drop the row. Both would be a silent
		// skipped(gone) below. One branch point that they attach to is the whole
		// reason this variable is read here and not five lines further down;
		// five special cases scattered through this method later would be the
		// alternative.
		$kind = $row->getKind();

		$userIds = $this->usersFor($fileId);
		if ($userIds === []) {
			return null;
		}

		// Two different questions, and therefore two fields. userIds is the
		// access payload the container writes into its prefilter, so that a
		// search can narrow candidates down before the authoritative recheck in
		// PHP happens. fetchAs is the single user in whose context the bytes are
		// read. Who may read a file in order to index it and who may find it are
		// not the same question, and collapsing them into one field is how a
		// prefilter silently turns into a permission model.
		$fetchAs = $userIds[0];

		$userFolder = $this->userFolder($fetchAs);
		if ($userFolder === null) {
			return null;
		}

		$node = $userFolder->getFirstNodeById($fileId);
		if ($node === null) {
			return null;
		}

		$size = $node->getSize();

		return [
			'fileId' => $fileId,
			'storageId' => $row->getStorageId(),
			'rootId' => $row->getRootId(),
			'path' => ltrim((string)$userFolder->getRelativePath($node->getPath()), '/'),
			'title' => $node->getName(),
			'mime' => $node->getMimetype(),
			'size' => (int)$size,
			'mtime' => $node->getMTime(),
			// Without a function in phase 2 and part of the protocol anyway, so
			// that the reconcile of phase 3 does not have to change the shape of
			// this object to get it.
			'etag' => $node->getEtag(),
			// What the container has to do with this row. Next to etag on
			// purpose: both are the fields phase 3 needs, and the shape of this
			// object stays what it was otherwise.
			'kind' => $kind,
			'userIds' => $userIds,
			'fetchAs' => $fetchAs,
			'isUpdate' => $row->getIsUpdate(),
		];
	}

	/**
	 * Everyone who sees this file, asked once per file.
	 *
	 * This is the simple variant, deliberately. The known optimisation asks once
	 * per storage instead and assigns files by path prefix afterwards, which
	 * saves roughly two hundred thousand queries on an instance with a hundred
	 * thousand files. It is not built here for two reasons. During the first
	 * index the HTTP fetch of every single file dominates the cost by orders of
	 * magnitude, so the saving would not be visible. And rebuilding the prefix
	 * logic of the mount cache is exactly the kind of cleverness that produces a
	 * systematically too wide prefilter, which is unsafe in the sense that it
	 * hands the search more candidates than it should. That optimisation belongs
	 * behind a measurement in phase 5, together with the parity test against
	 * this variant that is planned there anyway.
	 *
	 * This paragraph is here so the simple version is read as a decision rather
	 * than as an oversight.
	 *
	 * @return list<string>
	 */
	private function usersFor(int $fileId): array {
		$userIds = [];
		try {
			// The user behind a mount can be gone between the mount cache and
			// this line, and that throws rather than returning null, so the loop
			// stays inside the guard.
			foreach ($this->userMountCache->getMountsForFileId($fileId) as $mount) {
				$userIds[] = $mount->getUser()->getUID();
			}
		} catch (\Throwable $e) {
			$this->logger->warning('Findling: could not resolve who sees a queued file', ['exception' => $e]);
			return [];
		}

		// Sorted and deduplicated: a file that is mounted twice for the same user
		// must not appear twice in the access payload, and a stable order means
		// a retried row is fetched in the same context as before.
		$userIds = array_values(array_unique($userIds));
		sort($userIds);

		return $userIds;
	}

	private function userFolder(string $userId): ?Folder {
		try {
			return $this->rootFolder->getUserFolder($userId);
		} catch (\Throwable $e) {
			$this->logger->warning('Findling: no home folder for the fetch user of a queued file', ['exception' => $e]);
			return null;
		}
	}

	/**
	 * Take a row out of the queue and write down why.
	 */
	private function finish(QueueFile $row, string $state, string $reason): void {
		$this->fileStateService->record($row->getFileId(), $state, $reason);
		$this->queueMapper->acknowledge([$row->getId()]);
	}
}
