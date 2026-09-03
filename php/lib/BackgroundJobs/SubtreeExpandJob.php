<?php

declare(strict_types=1);

namespace OCA\Findling\BackgroundJobs;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\BackgroundJob\QueuedJob;
use OCP\IAppConfig;
use OCP\IDBConnection;
use Psr\Log\LoggerInterface;

/**
 * Turns one folder operation into one work order per descendant, in bands.
 *
 * This job exists because of a single property of the Nextcloud event system: a
 * folder operation raises exactly one event for the folder node and none for its
 * children. A user who moves a folder with ten thousand documents into a Team
 * Folder produces one NodeRenamedEvent, and whoever queues only the node from
 * that event has 9999 files with the wrong permissions in the prefilter.
 *
 * The shape is the one StorageCrawlJob already proved: a band of entries, a wall
 * clock ceiling, a cursor in the job argument and a successor the job plans
 * itself. Being a QueuedJob it removes itself from the job list before it runs,
 * so the successor is the only entry that exists afterwards and a subtree can
 * never accumulate expansion jobs.
 *
 * Nothing here logs a path or a file name. Counters, the storage id, the
 * ancestor and the cursor are enough to follow an expansion, and a log line is
 * the one place where the content of a private instance leaves the permission
 * model.
 */
class SubtreeExpandJob extends QueuedJob {
	/**
	 * Entries per band. The API orders by file id, so a band is a well defined
	 * range and not a sample.
	 *
	 * A quarter of the crawl's band, and on purpose: this job runs after a user
	 * action rather than during a planned first index, so it shares its cron slot
	 * with whatever else that instance is doing at that moment. 250 rows are a
	 * few tens of milliseconds of inserts, small enough that the wall clock
	 * ceiling below is what ends a run and not the band.
	 */
	public const BATCH_SIZE = 250;

	/**
	 * Wall clock ceiling for a single run. Whichever of the two ceilings is
	 * reached first ends the run. A cron slot is shared with every other job of
	 * the instance, and an expansion that holds it for minutes is a denial of
	 * service against the rest of the server, not a fast prefilter.
	 */
	private const MAX_SECONDS = 30;

	/**
	 * Seconds until the next band of the same subtree. Small enough that a
	 * withdrawn share stops being a candidate quickly, large enough that the
	 * expansion does not monopolise consecutive cron runs.
	 */
	private const INTERVAL = 5;

	/**
	 * Writes per transaction. Same measurement as the crawl (perf audit H2): one
	 * commit per file made the commit the run's main cost on slow disks, and one
	 * transaction for the whole run would block the single writer of a SQLite
	 * instance for its entire length.
	 */
	private const TX_BAND = 250;

	/**
	 * The kinds a subtree operation can hand to its descendants.
	 *
	 * Three, and the list stays closed because the other two make no sense here.
	 * metadata would rewrite names that did not change, since the descendants of
	 * a renamed folder keep their own name and the path field of the index is
	 * read by nobody's query (plan 03-02); and ocr is never handed out by an
	 * event at all, it is what the container requeues a file as once it has
	 * looked into it.
	 *
	 * **Why content is in the list since plan 05-04.** Until then it was out,
	 * with the argument that a subtree of content jobs is a re-crawl and the
	 * thing that re-crawls is the ETag reconcile. That argument holds for the
	 * three folder operations it was written for, whose descendants keep their
	 * bytes and their place in the index. It does not hold for the fourth one: a
	 * folder that comes back out of the trash bin has descendants the container
	 * dropped out of the index and tombstoned when they were deleted, so the
	 * only thing that gets them back is a content job each. Without it a
	 * restored folder waits for the next reconcile cycle, measured up to a day
	 * on the default cadence, and IDX-04 promises otherwise.
	 *
	 * The caller side is where this stays narrow: the listener asks for content
	 * on the restore branch and nowhere else, so this kind never expands a
	 * subtree whose bytes nobody touched.
	 *
	 * @var list<string>
	 */
	private const EXPANDABLE_KINDS = [
		QueueMapper::KIND_ACL,
		QueueMapper::KIND_DELETE,
		QueueMapper::KIND_CONTENT,
	];

	public function __construct(
		ITimeFactory $time,
		private IJobList $jobList,
		private StorageService $storageService,
		private QueueService $queueService,
		private IAppConfig $appConfig,
		private IDBConnection $db,
		private LoggerInterface $logger,
	) {
		parent::__construct($time);
	}

	protected function run($argument): void {
		$storageId = (int)($argument['storage_id'] ?? 0);
		$rootId = (int)($argument['root_id'] ?? 0);
		$ancestorId = (int)($argument['ancestor_id'] ?? 0);
		$kind = (string)($argument['kind'] ?? '');
		$lastFileId = (int)($argument['last_file_id'] ?? 0);

		if ($storageId <= 0 || $ancestorId <= 0 || !in_array($kind, self::EXPANDABLE_KINDS, true)) {
			// A malformed argument would otherwise reschedule itself forever
			// against a subtree that does not exist, or fill the queue with a kind
			// no branch of the container can run. Dropping it with a warning is
			// the whole of T-03-404, and it is the same guard the crawl carries.
			$this->logger->warning('Findling: dropped a subtree job without a usable argument', [
				'storage_id' => $storageId,
				'ancestor_id' => $ancestorId,
			]);
			return;
		}

		$deadline = $this->time->getTime() + self::MAX_SECONDS;
		$seen = 0;
		$queued = 0;
		$band = 0;

		// The writes of a run go in transaction bands rather than one commit per
		// file, see TX_BAND. Nothing in the band throws for "already there", which
		// is what makes this safe on PostgreSQL: a caught constraint violation
		// inside an open transaction would abort the whole band over there.
		$this->db->beginTransaction();
		try {
			// getFilesInMount asks getByAncestorInStorage, so the second argument
			// is an ancestor and not necessarily a mount root. Here it is the file
			// id of the folder the event was raised for, which is exactly the
			// subtree that has to be resolved. The type filter of that method
			// applies as well, and it is right for both kinds: a file that is
			// never indexed has no prefilter row to correct and no document to
			// drop.
			foreach ($this->storageService->getFilesInMount($storageId, $ancestorId, $lastFileId, self::BATCH_SIZE) as $entry) {
				// The deadline is asked before the entry is handled and not after,
				// so a run cannot overshoot its ceiling by one more write (bug
				// audit M4, found on the crawl).
				if ($this->time->getTime() >= $deadline) {
					break;
				}

				// The cursor moves for every entry that was looked at. This is the
				// PHP half of IDX-02 for this job: the progress lives in the job
				// argument and therefore in the Nextcloud database, so a crash in
				// the middle of a large subtree costs the current band and nothing
				// else.
				$lastFileId = max($lastFileId, $entry->getId());
				$seen++;

				// Size zero for the two kinds that move no bytes. Neither an acl
				// job nor a deletion reads the file, so neither may take a share
				// of the byte budget a claim spends; otherwise a subtree of large
				// documents would fill a whole batch with work that costs nothing.
				//
				// A content job is the opposite case and carries its real weight,
				// which the cache entry of this band already knows. A subtree of
				// restored files with a zero in that column would let one claim
				// take thirty two documents of any size at all, past the byte
				// ceiling the batch exists to keep, and the batch would run into
				// the lock timeout of its kind.
				//
				// Idempotent by the unique index on file_id, and never a
				// downgrade: KIND_RANK in QueueMapper keeps the more expensive kind
				// when a row is already waiting, so an expansion cannot throw away
				// a pending content job.
				$moves = $kind === QueueMapper::KIND_CONTENT;
				$this->queueService->enqueueFile(
					(int)$entry->getId(),
					$storageId,
					$rootId,
					$moves ? max(0, (int)$entry->getSize()) : 0,
					true,
					$kind,
				);
				$queued++;

				if (++$band >= self::TX_BAND) {
					$this->db->commit();
					$this->db->beginTransaction();
					$band = 0;
				}
			}
			$this->db->commit();
		} catch (\Throwable $e) {
			$this->db->rollBack();
			throw $e;
		}

		$this->appConfig->setValueInt(Application::APP_ID, SchedulerJob::LAST_JOB_RUN, $this->time->getTime());

		if ($seen === 0) {
			// Nothing behind the cursor any more, so this subtree is done and gets
			// no successor. This is the only way the chain terminates, exactly as
			// in the crawl.
			$this->logger->debug('Findling: finished expanding a subtree', [
				'storage_id' => $storageId,
				'ancestor_id' => $ancestorId,
				'kind' => $kind,
				'cursor' => $lastFileId,
			]);
			return;
		}

		$this->logger->debug('Findling: expanded a band of a subtree', [
			'storage_id' => $storageId,
			'ancestor_id' => $ancestorId,
			'kind' => $kind,
			'queued' => $queued,
			'cursor' => $lastFileId,
		]);

		$this->jobList->scheduleAfter(self::class, $this->time->getTime() + self::INTERVAL, [
			'storage_id' => $storageId,
			'root_id' => $rootId,
			'ancestor_id' => $ancestorId,
			'kind' => $kind,
			'last_file_id' => $lastFileId,
		]);
	}
}
