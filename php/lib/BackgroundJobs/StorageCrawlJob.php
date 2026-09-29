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
use OCP\Files\Cache\ICacheEntry;
use OCP\IAppConfig;
use OCP\IDBConnection;
use OCP\Lock\ILockingProvider;
use OCP\Lock\LockedException;
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
 *
 * Since quick task 260929-kii the same job has a counting mode (mode recount),
 * started by ScanRecountJob after the crawl is through. It is the same work
 * without the work stock: the same query (StorageService::getFilesInMount),
 * the same single decision (exclusion before cap, see verdict()) and the same
 * counting of a sighting (countSighting()), only that nothing is queued and no
 * verdict is recorded, and the sums replace the row of the mount at the end
 * instead of being added to it. So it is still one query and one rule, and
 * "the only one there will ever be" still holds: the recount is not a second
 * scan, it is this scan run again.
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
	 * The one lock every slice of every mount runs under, whichever door it came
	 * through. Two doors exist since the top-up route of the runtime finding of
	 * the v1.1 comparison run (the work stock ran dry for 5.85 of 26.6 hours
	 * because the system cron came around every 12 minutes): the cron, and a
	 * starved container asking for the next slice itself. Without the lock the
	 * two can meet on the same job row and crawl the same band twice, which the
	 * merge-safe enqueue would survive but a 4 GB box should not have to pay.
	 */
	public const LOCK_NAME = 'findling/crawl-slice';

	/**
	 * The floor of the wall clock budget a caller may ask for. Below this a
	 * slice would spend its whole life on the transaction it opens.
	 */
	private const MIN_BUDGET_SECONDS = 5;

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

	/**
	 * The value of the argument key 'mode' that makes a chain a recount of the
	 * denominator instead of a crawl. Any other value, and a missing key, is a
	 * crawl, so every argument written before this mode existed keeps its
	 * meaning.
	 */
	public const MODE_RECOUNT = 'recount';

	/**
	 * The six counter columns of findling_scan_stats, and the keys under which
	 * a recount chain carries its running sums from one slice to the next (the
	 * way the crawl carries its cursor).
	 *
	 * @var list<string>
	 */
	private const COUNTER_KEYS = ['files_seen', 'bytes_seen', 'ocr_candidates', 'pdf_seen', 'over_cap', 'excluded'];

	/** The three outcomes of the single decision about one entry. */
	private const VERDICT_EXCLUDED = 'excluded';
	private const VERDICT_OVER_CAP = 'over_cap';
	private const VERDICT_INDEXABLE = 'indexable';

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
		private ILockingProvider $lockingProvider,
		private LoggerInterface $logger,
	) {
		parent::__construct($time);
	}

	/**
	 * The wall clock budget of one slice, clamped between the floor and
	 * MAX_SECONDS. The cron path carries no budget_seconds and gets the full
	 * ceiling; the top-up route asks for less because its caller waits on an
	 * OCS request with a 30 s client timeout, and a slice that answers after
	 * the caller hung up helps nobody.
	 */
	public static function budgetSeconds(mixed $argument): int {
		$asked = is_array($argument) ? (int)($argument['budget_seconds'] ?? self::MAX_SECONDS) : self::MAX_SECONDS;
		return min(self::MAX_SECONDS, max(self::MIN_BUDGET_SECONDS, $asked));
	}

	protected function run($argument): void {
		$storageId = (int)($argument['storage_id'] ?? 0);
		$rootId = (int)($argument['root_id'] ?? 0);
		$overriddenRoot = (int)($argument['overridden_root'] ?? 0);
		$lastFileId = (int)($argument['last_file_id'] ?? 0);
		$recount = is_array($argument) && ($argument['mode'] ?? null) === self::MODE_RECOUNT;
		$sums = $recount ? self::sumsFrom($argument) : [];

		if ($storageId <= 0 || $overriddenRoot <= 0) {
			// A malformed argument would otherwise reschedule itself forever
			// against a mount that does not exist.
			$this->logger->warning('Findling: dropped a crawl job without a usable mount', ['storage_id' => $storageId]);
			return;
		}

		try {
			$this->lockingProvider->acquireLock(self::LOCK_NAME, ILockingProvider::LOCK_EXCLUSIVE);
		} catch (LockedException) {
			// Another slice is crawling right now, through the other door (the
			// cron and the top-up route can meet here). Nothing is crawled
			// twice, and the chain survives: being a QueuedJob this row was
			// removed before run(), so returning without the reschedule below
			// would end the crawl of this mount for good.
			$this->jobList->scheduleAfter(
				self::class,
				$this->time->getTime() + self::INTERVAL,
				self::successorArgument($storageId, $rootId, $overriddenRoot, $lastFileId, $recount, $sums),
			);
			return;
		}

		try {
			if ($recount) {
				$this->recountSlice(self::budgetSeconds($argument), $storageId, $rootId, $overriddenRoot, $lastFileId, $sums);
			} else {
				$this->crawlSlice(self::budgetSeconds($argument), $storageId, $rootId, $overriddenRoot, $lastFileId);
			}
		} finally {
			$this->lockingProvider->releaseLock(self::LOCK_NAME, ILockingProvider::LOCK_EXCLUSIVE);
		}
	}

	/**
	 * One slice of one mount, under the lock the caller holds.
	 */
	private function crawlSlice(int $budgetSeconds, int $storageId, int $rootId, int $overriddenRoot, int $lastFileId): void {
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

		$deadline = $this->time->getTime() + $budgetSeconds;
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
		$bandCounts = self::zeroSums();

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

				// The single decision (exclusion before cap) and the counting of
				// the sighting are two methods the counting mode of this job
				// calls as well, so the crawl and the recount cannot come to
				// different answers about the same file.
				$verdict = $this->verdict($entry, $mountRoot, $cap);
				$this->countSighting($entry, $verdict, $bandCounts);

				if ($verdict === self::VERDICT_EXCLUDED) {
					// Counted and not recorded. The scan counter takes the
					// sighting so that the Excluded tile of the page has a
					// number and the coverage denominator loses one, and no row
					// goes into findling_file_state: on an excluded archive
					// folder with two hundred thousand files that would be two
					// hundred thousand writes for an answer that follows from
					// one comparison, and the diagnosis works the reason out
					// live instead (stage two of the precedence rule).
					$skipped++;
				} elseif ($verdict === self::VERDICT_OVER_CAP) {
					// Counted as well as recorded: over_cap is one of the two
					// deliberate omissions that come out of the denominator,
					// which is what lets the coverage figure reach a hundred per
					// cent at all.
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
					// Once per band and never once per file. One counter update
					// per file would be exactly the doubling of write cost that
					// the band exists to avoid, and the update belongs inside
					// the band it counts, so it goes before the commit.
					$this->addBand($storageId, $bandCounts, $lastFileId);
					$bandCounts = self::zeroSums();

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
			$this->addBand($storageId, $bandCounts, $lastFileId);

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

		$this->jobList->scheduleAfter(
			self::class,
			$this->time->getTime() + self::INTERVAL,
			self::successorArgument($storageId, $rootId, $overriddenRoot, $lastFileId, false, []),
		);
	}

	/**
	 * One slice of a recount chain, under the lock the caller holds.
	 *
	 * The same walk as crawlSlice() without a single write per file: nothing is
	 * queued, no verdict is recorded, no transaction is opened. The six sums
	 * travel in the job argument from slice to slice, and the slice that finds
	 * nothing behind the cursor hands them to ScanStatsService::replaceStorage
	 * in one statement.
	 *
	 * The deadline is checked between pages only and not per entry. Without
	 * writes a page of BATCH_SIZE entries is quick, and a cursor that always
	 * stands at the end of a page keeps every page whole.
	 *
	 * LAST_JOB_RUN is not written. That value is the motion sensor of the
	 * indexing (stalledFor on the page reads it), and a count is not motion of
	 * the index: a recount on a stuck crawl would otherwise make a stalled
	 * instance look alive once a day.
	 *
	 * @param array<string, int> $sums
	 */
	private function recountSlice(int $budgetSeconds, int $storageId, int $rootId, int $overriddenRoot, int $lastFileId, array $sums): void {
		$row = $this->scanStats->forStorage($storageId);
		if ($row !== null && $row['finished'] === false) {
			// A real crawl is counting this mount right now (a restart, or the
			// first crawl of a mount that got its row a moment ago). Its row is
			// the truth that is being built, and this chain ends without a
			// successor; ScanRecountJob starts the next round once the crawl is
			// through.
			$this->logger->debug('Findling: skipped the recount of a mount that is being crawled', [
				'storage_id' => $storageId,
			]);
			return;
		}

		$cap = $this->settingsService->maxFileBytes();
		$mountRoot = $this->storageService->mountRootPath($storageId, $overriddenRoot);
		$deadline = $this->time->getTime() + $budgetSeconds;

		while (true) {
			$page = 0;
			foreach ($this->storageService->getFilesInMount($storageId, $overriddenRoot, $lastFileId, self::BATCH_SIZE) as $entry) {
				$lastFileId = max($lastFileId, $entry->getId());
				$page++;
				$this->countSighting($entry, $this->verdict($entry, $mountRoot, $cap), $sums);
			}

			if ($page === 0) {
				// The end of the mount: one complete measurement, assigned.
				$this->scanStats->replaceStorage($storageId, $sums, $lastFileId);
				$this->logger->info('Findling: recounted a mount', [
					'storage_id' => $storageId,
					'files_seen' => $sums['files_seen'] ?? 0,
				]);
				return;
			}

			if ($this->time->getTime() >= $deadline) {
				break;
			}
		}

		$this->jobList->scheduleAfter(
			self::class,
			$this->time->getTime() + self::INTERVAL,
			self::successorArgument($storageId, $rootId, $overriddenRoot, $lastFileId, true, $sums),
		);
	}

	/**
	 * The single decision about one entry, the one place it is made.
	 *
	 * The exclusion test comes BEFORE the size check, because a file an admin
	 * told this app to leave alone is left alone whatever its size is, and
	 * skipped(too_large) on a file inside an excluded folder would be a reason
	 * nobody can act on.
	 *
	 * Both the path and the comparison come from ExclusionService, which is the
	 * only place either of them exists. The event listener asks the same two
	 * methods with a root of its own, and the two land in the same space by
	 * construction: that is pitfall 4, and it is the difference between an
	 * exclusion that holds and one that the next save undoes without anybody
	 * noticing. The crawl and its counting mode both ask this method, so the
	 * denominator of a recount follows exactly the rule the crawl follows.
	 */
	private function verdict(ICacheEntry $entry, string $mountRoot, int $cap): string {
		if ($this->exclusionService->isExcluded(
			$this->exclusionService->mountRelativePath($entry->getPath(), $mountRoot),
		)) {
			return self::VERDICT_EXCLUDED;
		}

		return $entry->getSize() > $cap ? self::VERDICT_OVER_CAP : self::VERDICT_INDEXABLE;
	}

	/**
	 * Count one sighting into the six sums, the same way in both modes.
	 *
	 * @param array<string, int> $counts
	 */
	private function countSighting(ICacheEntry $entry, string $verdict, array &$counts): void {
		$counts['files_seen'] = ($counts['files_seen'] ?? 0) + 1;
		// The interface allows a float for a size beyond the integer range, and
		// a document of that size does not exist behind a cap of fifty
		// megabytes; the cast is the same one StorageService::getFileSlice makes
		// for the same reason.
		$counts['bytes_seen'] = ($counts['bytes_seen'] ?? 0) + max(0, (int)$entry->getSize());
		$mimeType = $entry->getMimeType();
		if (in_array($mimeType, self::OCR_CERTAIN_MIMETYPES, true)) {
			$counts['ocr_candidates'] = ($counts['ocr_candidates'] ?? 0) + 1;
		} elseif ($mimeType === 'application/pdf') {
			$counts['pdf_seen'] = ($counts['pdf_seen'] ?? 0) + 1;
		}

		if ($verdict === self::VERDICT_EXCLUDED) {
			$counts['excluded'] = ($counts['excluded'] ?? 0) + 1;
		} elseif ($verdict === self::VERDICT_OVER_CAP) {
			$counts['over_cap'] = ($counts['over_cap'] ?? 0) + 1;
		}
	}

	/**
	 * Hand one band of the crawl to ScanStatsService::add.
	 *
	 * @param array<string, int> $counts
	 */
	private function addBand(int $storageId, array $counts, int $cursor): void {
		$this->scanStats->add(
			$storageId,
			$counts['files_seen'] ?? 0,
			$counts['bytes_seen'] ?? 0,
			$counts['ocr_candidates'] ?? 0,
			$counts['pdf_seen'] ?? 0,
			$counts['over_cap'] ?? 0,
			$counts['excluded'] ?? 0,
			$cursor,
		);
	}

	/**
	 * Six zeros under the six counter keys.
	 *
	 * @return array<string, int>
	 */
	private static function zeroSums(): array {
		return array_fill_keys(self::COUNTER_KEYS, 0);
	}

	/**
	 * The running sums a recount chain carries, read back from its argument.
	 *
	 * Every value is cast and clamped at zero: oc_jobs is writable by a
	 * database admin only, and whatever such a value says, the next recount
	 * replaces it with a measurement (T-kii-03).
	 *
	 * @param array<mixed> $argument
	 * @return array<string, int>
	 */
	private static function sumsFrom(array $argument): array {
		$sums = [];
		foreach (self::COUNTER_KEYS as $key) {
			$sums[$key] = max(0, (int)($argument[$key] ?? 0));
		}
		return $sums;
	}

	/**
	 * The argument of the next slice of the same chain.
	 *
	 * A crawl gets exactly the four canonical keys: a budget_seconds of the
	 * top-up route must not travel into the cron chain, where it would shorten
	 * every following slice for no caller at all. A recount carries its mode and
	 * its six sums on top, because without them the successor would be a crawl
	 * or would start counting from zero in the middle of the mount.
	 *
	 * @param array<string, int> $sums
	 * @return array<string, int|string>
	 */
	private static function successorArgument(int $storageId, int $rootId, int $overriddenRoot, int $lastFileId, bool $recount, array $sums): array {
		$argument = [
			'storage_id' => $storageId,
			'root_id' => $rootId,
			'overridden_root' => $overriddenRoot,
			'last_file_id' => $lastFileId,
		];
		if (!$recount) {
			return $argument;
		}

		$argument['mode'] = self::MODE_RECOUNT;
		foreach (self::COUNTER_KEYS as $key) {
			$argument[$key] = max(0, (int)($sums[$key] ?? 0));
		}
		return $argument;
	}
}
