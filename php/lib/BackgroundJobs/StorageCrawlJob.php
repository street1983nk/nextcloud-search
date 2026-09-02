<?php

declare(strict_types=1);

namespace OCA\Findling\BackgroundJobs;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\ScanStatsService;
use OCA\Findling\Service\SettingsService;
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
 *
 * This job is also the metadata scan of the coverage figure, and it is the only
 * one there will ever be. It already sees every indexable file with its size
 * and its mimetype, before any extraction has happened, so the counters it
 * needs are the ones it is producing anyway. Until now they lived in local
 * variables and ended in a log line; since this plan they go into
 * findling_scan_stats and become the denominator of the coverage figure. A scan
 * job of its own would be a second walk over the same file list, and the two
 * walks would disagree the moment one of them was interrupted.
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
	 *
	 * From plan 04-08 on this value is the default of a cap an admin can change,
	 * not the cap itself. The line therefore stays here as the documented
	 * default rather than moving into the settings: zero config means the
	 * default has to be right, and a default that only exists in a database row
	 * cannot be read by somebody looking at this file.
	 */
	public const MAX_SIZE = 50 * 1024 * 1024;

	/**
	 * The mimetypes OCR is certain for, because a picture carries no text layer
	 * at all.
	 *
	 * application/pdf is deliberately not in this list. Whether a PDF needs OCR
	 * is decided by its text layer, and that is only visible inside the
	 * container. So the OCR share is an interval before a run and not a value:
	 * the lower bound is this list, the upper bound is this list plus every PDF,
	 * and pdf_seen is counted separately so that the two ends stay tellable
	 * apart. A single guessed percentage would be a number nobody can account
	 * for, and the audience of this app has believed a status screen that knew
	 * nothing once already.
	 *
	 * @var list<string>
	 */
	private const OCR_CERTAIN_MIMETYPES = [
		'image/jpeg',
		'image/png',
		'image/tiff',
		'image/webp',
	];

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
		private ScanStatsService $scanStats,
		private SettingsService $settingsService,
		private ExclusionService $exclusionService,
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

		if ($lastFileId === 0) {
			// This mount starts from the beginning: a fresh installation or occ
			// findling:index --restart. The scan counters of this storage go
			// back to zero here, because a second walk over the same mount
			// would otherwise add its sightings on top of the first ones and
			// the page would claim roughly twice as many indexable files as the
			// instance has. This is the one place a storage starts over, the
			// termination branch below is the one place it is done.
			$this->scanStats->beginStorage($storageId);
		}

		// The two rules in force, read once before the loop and never once per
		// file. IAppConfig caches per request, so this is about not asking the
		// same question two thousand times rather than about the query; and a
		// value read once per slice is exactly what "the next run applies it"
		// means, because a slice is what a run of this job is.
		$cap = $this->settingsService->maxFileBytes();
		$mountRoot = $this->storageService->mountRootPath($storageId, $overriddenRoot);

		$deadline = $this->time->getTime() + self::MAX_SECONDS;
		$seen = 0;
		$queued = 0;
		$skipped = 0;
		$band = 0;

		// The scan counters of the current transaction band. They are separate
		// from the three above because they are handed to ScanStatsService and
		// then set back to zero, while $seen decides whether this mount is done
		// and $queued and $skipped belong to the log line of the whole slice.
		//
		// excluded was counted here from plan 04-04 on and stayed at zero until
		// plan 04-08 gave it the exclusion rules to count. It is the one
		// omission that has no row in findling_file_state, which is why the
		// counter is the whole record of it: without this number an excluded
		// file would be a file that quietly stopped being findable.
		$bandFiles = 0;
		$bandBytes = 0;
		$bandOcr = 0;
		$bandPdf = 0;
		$bandOverCap = 0;
		$bandExcluded = 0;

		// The writes of a slice run in transaction bands rather than one commit
		// per file, see TX_BAND. Nothing in the band throws for "already
		// there", which is what makes this safe on PostgreSQL: a caught
		// constraint violation inside an open transaction would abort the
		// whole band over there.
		$this->db->beginTransaction();
		try {
			foreach ($this->storageService->getFilesInMount($storageId, $overriddenRoot, $lastFileId, self::BATCH_SIZE) as $entry) {
				// The cursor moves for every entry that was looked at, including
				// the ones that were too large and the ones a rule left alone.
				// Moving it only for queued files would hand the same oversized
				// file to every following slice, and it would leave the crawl
				// standing in front of an excluded folder for good.
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

				$bandFiles++;
				// The interface allows a float for a size beyond the integer
				// range, and a document of that size does not exist behind a cap
				// of fifty megabytes; the cast is the same one
				// StorageService::getFileSlice makes for the same reason.
				$bandBytes += max(0, (int)$size);
				$mimeType = $entry->getMimeType();
				if (in_array($mimeType, self::OCR_CERTAIN_MIMETYPES, true)) {
					$bandOcr++;
				} elseif ($mimeType === 'application/pdf') {
					$bandPdf++;
				}

				// The exclusion test comes BEFORE the size check, because a file
				// an admin told this app to leave alone is left alone whatever
				// its size is, and skipped(too_large) on a file inside an
				// excluded folder would be a reason nobody can act on.
				//
				// Both the path and the comparison come from ExclusionService,
				// which is the only place either of them exists. The event
				// listener asks the same two methods with a root of its own, and
				// the two land in the same space by construction: that is
				// pitfall 4, and it is the difference between an exclusion that
				// holds and one that the next save undoes without anybody
				// noticing.
				if ($this->exclusionService->isExcluded(
					$this->exclusionService->mountRelativePath($entry->getPath(), $mountRoot),
				)) {
					// Counted and not recorded. The scan counter takes the
					// sighting so that the Excluded tile of the page has a
					// number and the coverage denominator loses one, and no row
					// goes into findling_file_state: on an excluded archive
					// folder with two hundred thousand files that would be two
					// hundred thousand writes for an answer that follows from
					// one comparison, and the diagnosis works the reason out
					// live instead (stage two of the precedence rule).
					$bandExcluded++;
					$skipped++;
				} elseif ($size > $cap) {
					$this->fileStateService->record($entry->getId(), 'skipped', 'too_large');
					$skipped++;
					// The same decision as the line above, counted as well as
					// recorded: over_cap is one of the two deliberate omissions
					// that come out of the denominator, which is what lets the
					// coverage figure reach a hundred per cent at all.
					$bandOverCap++;
				} else {
					// Idempotent by the unique index on file_id: a file that ten
					// users see is one row, and a second crawl of the same mount
					// refreshes that row instead of duplicating it.
					$this->queueService->enqueue($entry, $storageId, $rootId);
					$queued++;
				}

				if (++$band >= self::TX_BAND) {
					// Once per band and never once per file. One counter update
					// per file would be exactly the doubling of write cost that
					// the band exists to avoid, and the update belongs inside
					// the band it counts, so it goes before the commit.
					$this->scanStats->add($storageId, $bandFiles, $bandBytes, $bandOcr, $bandPdf, $bandOverCap, $bandExcluded, $lastFileId);
					$bandFiles = 0;
					$bandBytes = 0;
					$bandOcr = 0;
					$bandPdf = 0;
					$bandOverCap = 0;
					$bandExcluded = 0;

					$this->db->commit();
					$this->db->beginTransaction();
					$band = 0;
				}

				if ($this->time->getTime() >= $deadline) {
					break;
				}
			}

			// The remainder of the last, incomplete band. Called without a
			// condition on purpose: with zero deltas this is one update that
			// changes nothing but the timestamp, and a condition here would be a
			// second place deciding what a band is.
			$this->scanStats->add($storageId, $bandFiles, $bandBytes, $bandOcr, $bandPdf, $bandOverCap, $bandExcluded, $lastFileId);

			$this->db->commit();
		} catch (\Throwable $e) {
			$this->db->rollBack();
			throw $e;
		}

		$this->appConfig->setValueInt(Application::APP_ID, SchedulerJob::LAST_JOB_RUN, $this->time->getTime());

		if ($seen === 0) {
			// Nothing behind the cursor any more, so this mount is done and
			// gets no successor. This is the only way the crawl terminates.
			//
			// It is therefore also the only place a mount is marked as counted
			// through. Without that mark the page has to label its coverage
			// figure as provisional and say how many of how many mounts are
			// done, because the number is a lower bound until every mount
			// carries a finished_at.
			$this->scanStats->finishStorage($storageId, $lastFileId);

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
