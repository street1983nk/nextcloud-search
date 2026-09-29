<?php

declare(strict_types=1);

namespace OCA\Findling\BackgroundJobs;

use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\BackgroundJob\TimedJob;
use Psr\Log\LoggerInterface;

/**
 * Keeps the denominator of the coverage figure in step with the files of the
 * instance (quick task 260929-kii).
 *
 * Why this exists. findling_scan_stats is filled once per mount by the crawl.
 * Files that appear afterwards are indexed by the event listener, so the
 * numerator grows while the denominator stays at the value of the first crawl
 * for the life of the instance; the harness showed "607 of 587 indexable files
 * are searchable". This job starts, when a recount is due, one chain of
 * StorageCrawlJob in its counting mode per mount. That chain walks the same
 * query with the same single decision as the crawl and replaces the row of the
 * mount at the end, so the denominator is a fresh measurement after every
 * round.
 *
 * Why a mark and a recount, and not the listener counting. Every kind of event
 * has a drift of its own: Created and Written arrive for the same new file, a
 * copied folder arrives as one event, a rename can move a file into or out of
 * an exclusion, an overwrite can push a file over the cap or change its
 * mimetype, a folder is deleted and restored as a whole subtree, and occ
 * files:scan or a change on an external storage arrives with no event at all.
 * Increments would carry every one of those errors forward for good and never
 * correct them, and they would add a write inside the transaction of every
 * upload. The listener therefore only marks the instance as changed
 * (SettingsService::markScanStale), and this job measures what changed.
 *
 * Why a TimedJob every 15 minutes and a floor of 24 hours. A recount is one
 * metadata walk per mount without a single write per file, on a large
 * instance with a million files some 500 pages of 2000 entries, the same query
 * the nightly reconcile of the container pages through anyway. After an event
 * the next run of this job starts it, so the window in which the page cannot
 * show a share is 15 minutes plus the walk; on a quiet instance nothing starts
 * more than once a day, which still catches the changes no event announced.
 *
 * Why it never runs next to a crawl. A crawl row of a mount without a
 * finished_at is the truth being built, and a recount that replaced it would
 * throw away the bands already added. So nothing is planned while any
 * StorageCrawlJob row exists, crawl or recount, or while a SchedulerJob row
 * is still waiting to plan the crawl, and replaceStorage refuses to touch a
 * row without a finished_at as a second line.
 *
 * What it deliberately does not do: delete the rows of mounts that left the
 * mount list (a deleted user, a switch turned off). The container keeps the
 * documents of such a mount as things stand today, because its reconcile only
 * walks listed mounts, so the row and the documents stay consistent with each
 * other; deleting the row here would make the numerator larger than the
 * denominator for good. docs/admin-page.md names this as a limit.
 *
 * Nothing here logs a path or a name. The number of mounts is the whole log.
 */
class ScanRecountJob extends TimedJob {
	/** How often this job asks whether a recount is due, in seconds. */
	public const INTERVAL_SECONDS = 15 * 60;

	public function __construct(
		ITimeFactory $time,
		private IJobList $jobList,
		private StorageService $storageService,
		private SettingsService $settingsService,
		private LoggerInterface $logger,
	) {
		parent::__construct($time);
		$this->setInterval(self::INTERVAL_SECONDS);
	}

	protected function run($argument): void {
		// Any StorageCrawlJob row means a crawl or a recount is under way. A
		// crawl must not be overtaken, and a recount that is still walking must
		// not get a second chain beside it, which would count the same mount
		// twice in parallel and waste the walk.
		foreach ($this->jobList->getJobsIterator(StorageCrawlJob::class, 1, 0) as $job) {
			return;
		}
		// A pending SchedulerJob is a crawl about to be planned. On a fresh
		// install this job is registered before the repair step queues the
		// scheduler, and occ findling:index --restart queues it again; a
		// recount planned in that window would put recount rows beside the
		// crawl rows the scheduler adds next.
		foreach ($this->jobList->getJobsIterator(SchedulerJob::class, 1, 0) as $job) {
			return;
		}

		$now = $this->time->getTime();
		if (!$this->settingsService->scanRecountDue($now)) {
			return;
		}

		// Before the chains are planned, so that an event arriving while the
		// recount walks marks the instance again and triggers the next round.
		$this->settingsService->beginRecount($now);

		$mounts = 0;
		foreach ($this->storageService->getMounts() as $mount) {
			$this->jobList->add(StorageCrawlJob::class, [
				'storage_id' => $mount['storage_id'],
				'root_id' => $mount['root_id'],
				'overridden_root' => $mount['overridden_root'],
				'last_file_id' => 0,
				'mode' => StorageCrawlJob::MODE_RECOUNT,
				'files_seen' => 0,
				'bytes_seen' => 0,
				'ocr_candidates' => 0,
				'pdf_seen' => 0,
				'over_cap' => 0,
				'excluded' => 0,
			]);
			$mounts++;
		}

		$this->logger->info('Findling: started a recount of the coverage denominator', ['mounts' => $mounts]);
	}
}
