<?php

declare(strict_types=1);

namespace OCA\Findling\BackgroundJobs;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\BackgroundJob\QueuedJob;
use OCP\IAppConfig;
use OCP\IDBConnection;
use Psr\Log\LoggerInterface;

/**
 * Walks one mount in slices and puts what it finds into the work stock.
 *
 * One job instance handles one slice of one mount and then plans its own
 * successor. Being a QueuedJob it removes itself from the job list before it
 * runs, so the successor is the only entry that exists afterwards and a mount
 * can never accumulate crawl jobs.
 *
 * Nothing here logs a path or a file name. Counters, the storage id and the
 * cursor are enough to follow a crawl, and a log line is the one place where
 * the content of a private instance leaves the permission model.
 */
class StorageCrawlJob extends QueuedJob {
	/**
	 * Entries per slice. The API orders by file id, so a slice is a well
	 * defined range and not a sample.
	 */
	public const BATCH_SIZE = 2000;

	/**
	 * Wall clock ceiling for a single slice. Whichever of the two ceilings is
	 * reached first ends the slice. A cron slot is shared with every other job
	 * of the instance, and a crawl that holds it for minutes is a denial of
	 * service against the rest of the server, not a fast index.
	 */
	private const MAX_SECONDS = 30;

	/**
	 * Seconds until the next slice of the same mount. Small enough that the
	 * first index makes visible progress, large enough that the crawl does not
	 * monopolise consecutive cron runs.
	 */
	private const INTERVAL = 5;

	/**
	 * 50 MB, the extraction cap of the zero config guard rails. A file above it
	 * is not queued and not silently dropped either: it gets an end state with
	 * a reason, because the diagnosis of phase 4 reads exactly that table and
	 * "the file is simply not in the index" is the answer we are building this
	 * app to avoid (IDX-06).
	 */
	public const MAX_SIZE = 50 * 1024 * 1024;

	/**
	 * Writes per transaction. One commit per file made the commit the slice's
	 * main cost on slow disks (perf audit H2: 2-6 s of pure commit time out of
	 * a 30 s budget); one transaction for the whole slice of 2000 would block
	 * the single writer of a SQLite instance for the entire slice. A band of a
	 * few hundred is where neither end hurts.
	 */
	private const TX_BAND = 250;

	public function __construct(
		ITimeFactory $time,
		private IJobList $jobList,
		private StorageService $storageService,
		private QueueService $queueService,
		private FileStateService $fileStateService,
		private IAppConfig $appConfig,
		private IDBConnection $db,
		private LoggerInterface $logger,
	) {
		parent::__construct($time);
	}

	protected function run($argument): void {
		$storageId = (int)($argument['storage_id'] ?? 0);
		$rootId = (int)($argument['root_id'] ?? 0);
		$overriddenRoot = (int)($argument['overridden_root'] ?? 0);
		$lastFileId = (int)($argument['last_file_id'] ?? 0);

		if ($storageId <= 0 || $overriddenRoot <= 0) {
			// A malformed argument would otherwise reschedule itself forever
			// against a mount that does not exist.
			$this->logger->warning('Findling: dropped a crawl job without a usable mount', ['storage_id' => $storageId]);
			return;
		}

		$deadline = $this->time->getTime() + self::MAX_SECONDS;
		$seen = 0;
		$queued = 0;
		$skipped = 0;
		$band = 0;

		// The writes of a slice run in transaction bands rather than one commit
		// per file, see TX_BAND. Nothing in the band throws for "already
		// there", which is what makes this safe on PostgreSQL: a caught
		// constraint violation inside an open transaction would abort the
		// whole band over there.
		$this->db->beginTransaction();
		try {
			foreach ($this->storageService->getFilesInMount($storageId, $overriddenRoot, $lastFileId, self::BATCH_SIZE) as $entry) {
				// The cursor moves for every entry that was looked at, including
				// the ones that were too large. Moving it only for queued files
				// would hand the same oversized file to every following slice.
				//
				// This assignment is the PHP half of IDX-02. The cursor lives in
				// the job argument and therefore in the Nextcloud database, which
				// is the reason the container holds no crawl state at all: a
				// docker kill in the middle of the first index costs the current
				// slice and nothing else, because the last_file_id of the next
				// slice was written before the container was ever involved.
				$lastFileId = max($lastFileId, $entry->getId());
				$seen++;

				$size = $entry->getSize();
				if ($size > self::MAX_SIZE) {
					$this->fileStateService->record($entry->getId(), 'skipped', 'too_large');
					$skipped++;
				} else {
					// Idempotent by the unique index on file_id: a file that ten
					// users see is one row, and a second crawl of the same mount
					// refreshes that row instead of duplicating it.
					$this->queueService->enqueue($entry, $storageId, $rootId);
					$queued++;
				}

				if (++$band >= self::TX_BAND) {
					$this->db->commit();
					$this->db->beginTransaction();
					$band = 0;
				}

				if ($this->time->getTime() >= $deadline) {
					break;
				}
			}
			$this->db->commit();
		} catch (\Throwable $e) {
			$this->db->rollBack();
			throw $e;
		}

		$this->appConfig->setValueInt(Application::APP_ID, SchedulerJob::LAST_JOB_RUN, $this->time->getTime());

		if ($seen === 0) {
			// Nothing behind the cursor any more, so this mount is done and
			// gets no successor. This is the only way the crawl terminates.
			$this->logger->info('Findling: finished crawling a mount', [
				'storage_id' => $storageId,
				'cursor' => $lastFileId,
			]);
			return;
		}

		$this->logger->debug('Findling: crawled a slice of a mount', [
			'storage_id' => $storageId,
			'queued' => $queued,
			'skipped' => $skipped,
			'cursor' => $lastFileId,
		]);

		$this->jobList->scheduleAfter(self::class, $this->time->getTime() + self::INTERVAL, [
			'storage_id' => $storageId,
			'root_id' => $rootId,
			'overridden_root' => $overriddenRoot,
			'last_file_id' => $lastFileId,
		]);
	}
}
