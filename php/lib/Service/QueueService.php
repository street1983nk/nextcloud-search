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
	 * How many times a row may be DELIVERED to the container before it is given
	 * up as failed(repeatedly_stuck).
	 *
	 * Deliveries, not failures, and the difference is the whole reason this
	 * docblock is this long. A row that is claimed and never acknowledged comes
	 * back after the lock expires, so nothing ever reports a failure for it;
	 * without a ceiling on the deliveries it would circle forever instead of
	 * becoming a visible end state.
	 *
	 * The counter is raised by the claim itself, in the database
	 * (QueueMapper::claimBatch), and lowered again by QueueMapper::unlock, so the
	 * value on a row is the number of hand-outs the container never came back
	 * from plus the one that is happening at this moment. A row that was handed
	 * back unjudged is not among them, which is the fix of DI-05-23: before it, a
	 * disk pause of half a minute spent the whole budget of every row that
	 * happened to be with the worker, and thirty of thirty rows of a measured
	 * drill ended as failed(repeatedly_stuck) without ever having been delivered.
	 *
	 * Written out, because this is the arithmetic somebody shifted by one before
	 * (phase 2 perf audit) and would otherwise shift again:
	 *
	 *   claim 1 -> retries 1 -> delivered, attempt 1 of 3
	 *   claim 2 -> retries 2 -> delivered, attempt 2 of 3
	 *   claim 3 -> retries 3 -> delivered, attempt 3 of 3
	 *   claim 4 -> retries 4 -> NOT delivered, this is the give-up
	 *
	 * So the comparison below is "greater than", and three deliveries happen. The
	 * fourth claim is the one that discovers the exhaustion and writes the end
	 * state; it hands nothing to the container, and since this plan it also costs
	 * the batch neither a row of its budget nor a byte of it, so a doomed row
	 * cannot displace real work any more. Changing the comparison to "greater or
	 * equal" would cut the deliveries to two, which is the off-by-one in the
	 * other direction.
	 */
	public const MAX_DELIVERIES = 3;

	/**
	 * How many users of one file travel in a work order (perf audit M5).
	 *
	 * Without a ceiling an instance wide team folder puts the complete user list
	 * of the instance on every single file: five thousand users times thirty two
	 * files in one batch measured at roughly sixteen megabytes of heap on the PHP
	 * side and three and a half megabytes of JSON on the wire, per claim, for a
	 * list that is identical for every one of those files.
	 *
	 * Five hundred is chosen so that an ordinary instance never meets it. What
	 * happens beyond it is the interesting half, and it is a design decision
	 * rather than a truncation: the job is marked, the container writes one
	 * reserved collective row instead of the shortened list, and the prefilter
	 * treats the file as a candidate for anybody. The prefilter may be more
	 * generous than the truth and never stricter, because the security boundary
	 * is the final recheck in Provider (COMP-04); writing the first five hundred
	 * names as if they were the whole list would be the strict direction and
	 * would hide the file from everybody behind the cap.
	 */
	private const MAX_USERS = 500;

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
		private ExclusionService $exclusionService,
		private StorageService $storageService,
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

		// The home folders resolved during this claim, keyed by user id (perf
		// audit M8). getUserFolder() sets up a mount for the user, and a batch of
		// thirty two files of the same person paid that setup thirty two times.
		//
		// It lives exactly as long as the claim and is handed down rather than
		// kept on the object on purpose: a longer lived cache would be a second
		// source of truth about the mount setup of a user, and nobody would ever
		// invalidate it. A request is short enough that the mounts cannot change
		// underneath it in a way that matters, and if they do, the next claim
		// starts with an empty cache.
		$folders = [];

		foreach (QueueMapper::KINDS as $kind) {
			if ($rows <= 0) {
				break;
			}

			$batch = min(self::KIND_BATCH[$kind] ?? $limit, $rows);
			foreach ($this->queueMapper->claimBatch($batch, $budget, $kind) as $row) {
				// The two write-offs are decided before the row is charged
				// against either ceiling, and that order is the fix rather than
				// a detail. A row that is given up hands nothing to the
				// container and a row whose file is gone hands nothing either,
				// so charging them would spend a slot of the batch and a share
				// of the byte budget on work that does not exist. On an instance
				// with a handful of permanently stuck files that is a smaller
				// batch of real work in every single round.
				if ($row->getRetries() > self::MAX_DELIVERIES) {
					$this->finish($row, 'failed', 'repeatedly_stuck');
					$givenUp++;
					continue;
				}

				$source = $this->describe($row, $folders);
				if ($source === null) {
					$this->finish($row, 'skipped', 'gone');
					$gone++;
					continue;
				}

				$rows--;
				$budget = max(0, $budget - (int)$row->getSize());
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

		$this->enqueueFile(
			$entry->getId(),
			$storageId,
			$rootId,
			$size > 0 ? (int)$size : 0,
			$isUpdate,
		);
	}

	/**
	 * The same work stock, for a caller that holds a node instead of a cache
	 * entry.
	 *
	 * The event listener is that caller. An event carries an OCP\Files\Node, and
	 * the cache entry behind it is only reachable through FileInfo::getData,
	 * which exists since Nextcloud 34 while this app declares 32. Reading the
	 * entry out of the cache by internal path instead would be one query per
	 * write on the instance for four numbers the node already knows.
	 */
	public function enqueueFile(int $fileId, int $storageId, int $rootId, int $size, bool $isUpdate, string $kind = QueueMapper::KIND_CONTENT): void {
		$this->queueMapper->enqueue($fileId, $storageId, $rootId, max(0, $size), $isUpdate, $kind);
	}

	/**
	 * Acknowledge a batch: remove what was processed, record a reason for
	 * everything the container could not process, and record the decisions it
	 * made on its own.
	 *
	 * Three lists, two of which write a verdict, and the split between them is
	 * the split between "we wanted to and could not" and "we decided not to".
	 * Only the first is an error on the status page; the second is what makes the
	 * error list group the four reasons the container decides per file, namely
	 * encrypted, no text layer, empty text and a picture without readable writing
	 * (DI-04-03). Until they crossed this boundary the aggregation was missing
	 * while the per file diagnosis knew them perfectly well.
	 *
	 * The skips are keyed by FILE id and the failures by queue row id. That is
	 * not an inconsistency: a failed row has to be translated before it is
	 * deleted, and a skipped file is acknowledged in the same call anyway, so
	 * there is nothing left to translate and nothing to look up.
	 *
	 * All three are handled in one transaction. Half an acknowledgement is the
	 * worst of the possible outcomes: rows deleted without their reason recorded
	 * would vanish from the queue and from the diagnosis at the same time.
	 *
	 * A skip that is not a `skipped` reason at all is dropped by
	 * FileStateService::record, which judges the pair, counts the rejection and
	 * writes nothing. The batch is still acknowledged, because a defective code
	 * for one file must not leave thirty one healthy rows locked.
	 *
	 * What this does NOT do is take a verdict back. A file that was skipped and
	 * is indexed later keeps its row until something writes over it, exactly as a
	 * file that failed and succeeded later does today. The container therefore
	 * never reports a verdict for a file it handed over to the OCR track, which
	 * is the one case where that staleness would be the normal path rather than
	 * an edge of it.
	 *
	 * @param int[] $queueIds rows that are done
	 * @param array<int, string> $failures queue row id to reason code
	 * @param array<int, string> $skips file id to reason code
	 * @return array{acknowledged:int, recorded:int}
	 */
	public function acknowledge(array $queueIds, array $failures, array $skips = []): array {
		$failedIds = array_keys($failures);
		$allIds = array_values(array_unique(array_merge($queueIds, $failedIds)));
		if ($allIds === [] && $skips === []) {
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

			// The decisions of the container, inside the same transaction as the
			// failures above and as the delete below. There is one row per file,
			// so a file that is judged again overwrites its earlier verdict
			// instead of adding a second row.
			foreach ($skips as $fileId => $reason) {
				if ($this->fileStateService->record($fileId, 'skipped', $reason)) {
					$recorded++;
				}
			}

			$acknowledged = $allIds === [] ? 0 : $this->queueMapper->acknowledge($allIds);
			$this->db->commit();
		} catch (\Throwable $e) {
			$this->db->rollBack();
			throw $e;
		}

		if ($recorded > 0) {
			// One counter for both lists. Which verdict a file carries is in the
			// state table a query away, and a log line per list would be two
			// lines per batch on an instance whose scans all take the same route.
			$this->logger->info('Findling: recorded verdicts the container reported', ['count' => $recorded]);
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
	 * Put files on another kind of job, and create the rows that are missing.
	 *
	 * A pass through with nothing of its own to decide, so that the controller
	 * keeps knowing only this service. What it means is written down at
	 * QueueMapper::requeueAs, because the rules it follows are rules about rows:
	 * the attempt counter goes back to zero, a deletion is never overwritten, and
	 * this is the only way a row moves from content to ocr.
	 *
	 * Note that the ids here are file ids and not queue row ids. The container
	 * knows the file id of the PDF it just found no text layer in, and the
	 * reconcile of plan 03-12 knows nothing else at all: a file it discovers as
	 * missing has no queue row yet.
	 *
	 * @param int[] $fileIds
	 */
	public function requeue(array $fileIds, string $kind): int {
		return $this->queueMapper->requeueAs($fileIds, $kind);
	}

	/**
	 * What the work stock holds for one file, for the per file diagnosis.
	 *
	 * A pass through to the mapper, because the lock arithmetic belongs to the
	 * class that writes the lock, and the admin page reads the queue through this
	 * service and never through a mapper of its own.
	 *
	 * @return array{kind:string, retries:int, running:bool, secondsLeft:int}|null
	 */
	public function forFile(int $fileId): ?array {
		return $this->queueMapper->statusOfFile($fileId);
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
	 * The folder cache of the running claim travels in by reference (perf audit
	 * M8). It is a parameter and not a field so that its lifetime is visible at
	 * the call site: it lives for one claim and not a second longer.
	 *
	 * @param array<string, ?Folder> $folders home folders resolved during this claim
	 * @return array<string, mixed>|null
	 */
	private function describe(QueueFile $row, array &$folders): ?array {
		$fileId = $row->getFileId();

		// The one place where the kind of a row decides what its source object
		// looks like.
		//
		// metadata takes the route below unchanged, and that is a decision rather
		// than an omission. A renamed file is still there, still readable and
		// still owned by the same people, so it needs exactly the same source
		// object as a content job; what differs is only what the container does
		// with it. The one property that must survive any rewrite of this method
		// is that title and path are read from the node resolved here and not
		// from the queue row, because the node carries the new name and the row
		// carries nothing but a file id. Take those two fields from the row one
		// day and a rename would travel the whole queue to write the old name
		// back into the index, without a single error anywhere.
		//
		// The kinds that do not fit the route hang their early return here,
		// together with their counterpart in the container: delete below, which
		// must not resolve a node because the node is gone, and acl below it,
		// where an empty user list is the legitimate payload of an unshare and
		// not a reason to drop the row. Both would be a silent skipped(gone)
		// further down. One branch point that they attach to is the whole reason
		// this variable is read here and not five lines lower; five special cases
		// scattered through this method later would be the alternative.
		$kind = $row->getKind();

		// A delete order needs no node, no mount and no user list, and it must
		// not go looking for any of them. This is the inversion of everything
		// below, which is why it is spelled out rather than left to the reader:
		// for every other kind "the file is gone" is a reason to give up, and the
		// method answers null, the row is written off as skipped(gone) and the
		// container never learns of it. For a deletion "the file is gone" is the
		// order itself. Resolving a node first would make the outcome depend on
		// whether the trash bin still happens to hold a cache entry, and the
		// document would stay in the index for good on every instance where it
		// does not (IDX-05, pitfall 3).
		//
		// The source object is therefore the file id, the storage it lived on and
		// the kind. storageId comes from the queue row rather than from a node,
		// so it survives the deletion; the container carries it for the per mount
		// view and needs nothing else to forget a document.
		if ($kind === QueueMapper::KIND_DELETE) {
			return [
				'fileId' => $fileId,
				'storageId' => $row->getStorageId(),
				'kind' => $kind,
			];
		}

		// A permission change, and the one branch where an empty user list is the
		// answer rather than a failure. It sits here, directly next to the delete
		// branch, because both are the same defect seen twice: the null return of
		// this method used to mean two different things at once, "there is nothing
		// to do" and "the file cannot be described any more", and claim() turns
		// both into skipped(gone). After an unshare usersFor() legitimately
		// answers with nothing, the row was written off, and the old permission
		// rows stayed in the container for good. The empty list is the payload of
		// the job: the container hands it to replace_acl, which removes the last
		// row of that file (pitfall 4).
		//
		// No node is resolved for it either. The permissions come from the mount
		// cache, which is the same source the crawl uses, so the container never
		// forms a permission of its own; and asking a node for a size and a
		// mimetype would be work for fields this job does not carry.
		//
		// What this branch is worth, and what it is not: nothing leaks while an
		// acl row waits in the queue. A hit becomes a snippet only after the
		// recheck in Provider, and that recheck resolves the file through
		// getUserFolder()->getFirstNodeById(). A stale prefilter costs result
		// quality and compute time, not confidentiality. That is the reason this
		// kind is cheap and first in the claim order (D-04) rather than a reason
		// to treat it as a security control.
		if ($kind === QueueMapper::KIND_ACL) {
			$access = $this->usersFor($fileId);

			return [
				'fileId' => $fileId,
				'storageId' => $row->getStorageId(),
				'kind' => $kind,
				'userIds' => $access['users'],
				'userIdsTruncated' => $access['truncated'],
			];
		}

		$access = $this->usersFor($fileId);
		$userIds = $access['users'];
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

		$userFolder = $this->userFolder($fetchAs, $folders);
		if ($userFolder === null) {
			return null;
		}

		$node = $userFolder->getFirstNodeById($fileId);
		if ($node === null) {
			return null;
		}

		$size = $node->getSize();

		// Rows created by requeueAs carry storage_id and root_id 0, because the
		// requeue route only knows file ids; the reconcile of plan 03-12 is the
		// caller that produces them. Letting the zero travel poisoned the state
		// of every file the reconcile repaired: the container upserts
		// storage_id over the previously correct value, gone_in_range asks per
		// real storage, and a later eventless deletion of that file was never
		// found again, so IDX-05 broke exactly for the files the repair had
		// touched (review finding WR-01). The mount point of the node resolved
		// above is the same source the event listeners read these two ids
		// from, so a zero is replaced here and never travels further.
		$storageId = $row->getStorageId();
		$rootId = $row->getRootId();
		if ($storageId === 0 || $rootId === 0) {
			$mount = $node->getMountPoint();
			$storageId = $storageId !== 0 ? $storageId : (int)$mount->getNumericStorageId();
			$rootId = $rootId !== 0 ? $rootId : (int)$mount->getStorageRootId();
		}

		// A rule of TODAY, asked one last time before the bytes travel. The
		// reconcile of plan 03-12 is a third way into this queue, next to the
		// crawl and the event listener: it requeues every file whose etag the
		// container cannot match, it never sees a path, and the slice it reads
		// deliberately carries excluded files (see the docblocks of
		// StorageService::getFileSlice). Without a check here a fresh exclusion
		// is undone within one reconcile interval: the container reads every
		// tombstoned row of the cleared subtree as a restore, requeues it as
		// content, and this method would hand out its bytes again (review
		// finding CR-01). The same helper on the same path space as the other
		// two call sites, so a prefix cannot hit in one place and miss in
		// another (pitfall 4), and backend/tests/test_exclusion_path_space.py
		// holds this call site alongside the other two.
		//
		// The outcome is a delete order and not a dropped row. Dropping the row
		// as skipped(gone) would leave the document in the index whenever the
		// file was indexed before the rule arrived, and it would leave the row
		// travelling through the lock timeout again. The delete order is what
		// the container needs to clear the file and keep it clear: _forget is
		// idempotent, so re-deleting an already cleared file costs one write and
		// nothing else. The shape is the same as the delete branch above,
		// because the node must not matter to the container for a file it is
		// about to forget.
		//
		// The list is asked first so that the root lookup costs nothing on an
		// instance without exclusions, same as in the event listener.
		if ($this->exclusionService->prefixes() !== []) {
			$relative = $this->exclusionService->mountRelativePath(
				$node->getInternalPath(),
				$this->storageService->mountRootPath($storageId, $rootId),
			);
			if ($this->exclusionService->isExcluded($relative)) {
				return [
					'fileId' => $fileId,
					'storageId' => $storageId,
					'kind' => QueueMapper::KIND_DELETE,
				];
			}
		}

		return [
			'fileId' => $fileId,
			'storageId' => $storageId,
			'rootId' => $rootId,
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
			// The mark that says the list above is a prefix of the truth rather
			// than the truth (perf audit M5). It travels next to the list it
			// belongs to, because the container has no other way of telling a
			// short list from a complete one, and writing a short list as if it
			// were complete is what would hide the file from everybody behind the
			// cap.
			'userIdsTruncated' => $access['truncated'],
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
	 * The answer is a list plus a mark and not a bare list, because a caller has
	 * no way of telling a capped list from a complete one by looking at it. Five
	 * hundred names are a plausible team folder either way, and guessing from the
	 * length would break the moment the ceiling moves.
	 *
	 * @return array{users: list<string>, truncated: bool}
	 */
	private function usersFor(int $fileId): array {
		$userIds = [];
		$truncated = false;
		try {
			// The user behind a mount can be gone between the mount cache and
			// this line, and that throws rather than returning null, so the loop
			// stays inside the guard.
			foreach ($this->userMountCache->getMountsForFileId($fileId) as $mount) {
				if (count($userIds) >= self::MAX_USERS) {
					// The ceiling is reached inside the loop rather than applied
					// to the finished list on purpose (perf audit M5): the point
					// is not to send a shorter answer, it is to stop building the
					// long one. An instance wide team folder has thousands of
					// mounts for one file, and every iteration resolves a user
					// object.
					$truncated = true;
					break;
				}

				$userIds[] = $mount->getUser()->getUID();
			}
		} catch (\Throwable $e) {
			$this->logger->warning('Findling: could not resolve who sees a queued file', ['exception' => $e]);
			return ['users' => [], 'truncated' => false];
		}

		if ($truncated) {
			// A counter and a file id, never a name. Worth a line because a file
			// that hits this ceiling is a file the prefilter stops narrowing down,
			// and an admin who wonders why a search got slower deserves to find
			// the reason in the log.
			$this->logger->info('Findling: capped the user list of a queued file', ['count' => count($userIds)]);
		}

		// Sorted and deduplicated: a file that is mounted twice for the same user
		// must not appear twice in the access payload, and a stable order means
		// a retried row is fetched in the same context as before.
		$userIds = array_values(array_unique($userIds));
		sort($userIds);

		return ['users' => $userIds, 'truncated' => $truncated];
	}

	/**
	 * The home folder of one user, resolved once per claim (perf audit M8).
	 *
	 * getUserFolder() sets a mount up, and a batch of thirty two files belonging
	 * to the same person used to pay that setup thirty two times. The cache is
	 * handed in by reference and lives exactly as long as the claim; a field on
	 * this service would be a second source of truth about the mounts of a user
	 * that nobody ever invalidates.
	 *
	 * A failure is cached as well. Without that, a user without a home directory
	 * would be looked up again for every row of the batch, and every one of those
	 * lookups would throw, be caught and be logged.
	 *
	 * @param array<string, ?Folder> $folders
	 */
	private function userFolder(string $userId, array &$folders): ?Folder {
		if (array_key_exists($userId, $folders)) {
			return $folders[$userId];
		}

		try {
			$folder = $this->rootFolder->getUserFolder($userId);
		} catch (\Throwable $e) {
			$this->logger->warning('Findling: no home folder for the fetch user of a queued file', ['exception' => $e]);
			$folder = null;
		}

		$folders[$userId] = $folder;

		return $folder;
	}

	/**
	 * Take a row out of the queue and write down why.
	 */
	private function finish(QueueFile $row, string $state, string $reason): void {
		$this->fileStateService->record($row->getFileId(), $state, $reason);
		$this->queueMapper->acknowledge([$row->getId()]);
	}
}
