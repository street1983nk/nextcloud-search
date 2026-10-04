<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\BackgroundJobs\SchedulerJob;
use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCP\BackgroundJob\IJobList;
use OCP\Lock\ILockingProvider;
use Psr\Log\LoggerInterface;

/**
 * Runs the next due crawl slice on request instead of waiting for the cron.
 *
 * Why this exists. The v1.1 comparison run indexed 52,111 documents in 26 h 37
 * min against 18 h 56 min for the same corpus on v1.0, and the whole difference
 * was supply: the work stock ran completely dry for 5.85 of those hours (194 of
 * 812 status readings) because StorageCrawlJob only advanced when the system
 * cron came around, which on that instance was every 12 minutes rather than
 * every 5. The container was never slower, it was starving. The measurement
 * sits in docs/measurements/2026-09-vergleichsmessung-m7g/ and the analysis was
 * carried as DI-10-04.
 *
 * What it does. The container, on a pass that found the queue empty, asks this
 * service to advance the crawl by exactly one slice. The slice is the same
 * StorageCrawlJob the cron runs, executed through the same start() path a
 * manual occ background-job:execute would take, with two differences: the row
 * is removed under the canonical argument first, so the cron cannot run the
 * same slice again, and the argument carries a shorter wall clock budget,
 * because the caller waits on an OCS request with a 30 s client timeout.
 *
 * What it does NOT do. It invents no work: when no crawl job exists, the crawl
 * is finished (or never started) and the answer says so, which is what lets the
 * container fall back to its ordinary idle backoff. It also takes no lock of
 * its own: the lock lives inside StorageCrawlJob::run, where both doors, the
 * cron and this one, pass through it. When the cron is mid-slice at this
 * moment, the executed job hits that lock, reschedules itself unchanged and
 * returns without crawling; the answer still says pending, and the caller tries
 * again after its short pause.
 */
class CrawlAdvanceService {
	/**
	 * The wall clock budget handed to an inline slice. Twenty of the thirty
	 * seconds of the job's own ceiling: the OCS client of the container times
	 * out at 30 s (NPA_TIMEOUT), and a slice that finishes after the caller
	 * hung up still costs the database the work but tells nobody about it.
	 */
	public const BUDGET_SECONDS = 20;

	public function __construct(
		private IJobList $jobList,
		private LoggerInterface $logger,
		private ILockingProvider $lockingProvider,
	) {
	}

	/**
	 * Whether the crawl of the file cache is still under way.
	 *
	 * Read by the reconcile of the container through the queue stats (run 8 of
	 * the 28-07 chain, abort 71 at 5427 of 5000): fifteen slots drained the work
	 * stock faster than the cron paced crawl filled it, the reconcile read the
	 * empty queue as a quiet instance, walked ahead and requeued every file the
	 * crawl had not reached yet, and the crawl queued all 5000 of them a second
	 * time. An empty queue during a crawl is not a quiet instance.
	 *
	 * Three answers count as unfinished. A SchedulerJob row: a restart or a
	 * fresh install plans the crawl, and until it ran the whole crawl is ahead.
	 * A crawl row of StorageCrawlJob: the chain of a mount waits for its next
	 * slice. A held slice lock: a QueuedJob removes its row before it runs and
	 * the successor is only planned at the end of the slice, so for those
	 * seconds the last chain of the instance has no row at all. A recount row
	 * alone is no crawl; it queues nothing and only starts once the crawl is
	 * through.
	 */
	public function crawling(): bool {
		foreach ($this->jobList->getJobsIterator(SchedulerJob::class, 1, 0) as $job) {
			return true;
		}
		foreach ($this->jobList->getJobsIterator(StorageCrawlJob::class, null, 0) as $job) {
			if (!self::isRecount($job->getArgument())) {
				return true;
			}
		}
		return $this->lockingProvider->isLocked(StorageCrawlJob::LOCK_NAME, ILockingProvider::LOCK_EXCLUSIVE);
	}

	/**
	 * Execute at most one due crawl slice and say what the crawl looks like now.
	 *
	 * @return array{ran: bool, pending: bool}
	 */
	public function advance(): array {
		$ran = false;

		// Every row, not only the first: a recount row at the head must not
		// hide a crawl row behind it.
		foreach ($this->jobList->getJobsIterator(StorageCrawlJob::class, null, 0) as $job) {
			$argument = $job->getArgument();

			if (self::isRecount($argument)) {
				// A recount of the denominator (quick task 260929-kii), not a
				// crawl. It queues nothing, so a hungry container has nothing to
				// wait for from it: running it here would spend the OCS budget of
				// the caller on counting, and "pending" would keep the container
				// polling for work that never arrives. ScanRecountJob plans only
				// when neither a StorageCrawlJob nor a SchedulerJob row exists,
				// so the two should never meet; should they anyway, the recount
				// row is passed over and a crawl row behind it still runs.
				continue;
			}

			// Removed under the canonical argument BEFORE the run, mirroring
			// what QueuedJob::start would have done: the start() below removes
			// under the modified argument, which matches no row, and a row
			// left behind is a slice the cron crawls a second time.
			$this->jobList->remove($job, $argument);

			$job->setArgument(array_merge(
				is_array($argument) ? $argument : [],
				['budget_seconds' => self::BUDGET_SECONDS],
			));
			// start() logs a throwing run itself; nothing to catch here. A
			// slice that hits the lock inside run() reschedules itself
			// unchanged, so the chain survives every path out of this call.
			$job->start($this->jobList);
			$ran = true;
			// Exactly one slice per request.
			break;
		}

		// Only crawl rows are work the container can wait for.
		$pending = false;
		foreach ($this->jobList->getJobsIterator(StorageCrawlJob::class, null, 0) as $job) {
			if (!self::isRecount($job->getArgument())) {
				$pending = true;
				break;
			}
		}

		if ($ran) {
			$this->logger->debug('Findling: advanced the crawl by one slice on request', ['pending' => $pending]);
		}

		return ['ran' => $ran, 'pending' => $pending];
	}

	private static function isRecount(mixed $argument): bool {
		return is_array($argument) && ($argument['mode'] ?? null) === StorageCrawlJob::MODE_RECOUNT;
	}
}
