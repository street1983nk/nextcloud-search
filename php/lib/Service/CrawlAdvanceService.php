<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCP\BackgroundJob\IJobList;
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
	) {
	}

	/**
	 * Execute at most one due crawl slice and say what the crawl looks like now.
	 *
	 * @return array{ran: bool, pending: bool}
	 */
	public function advance(): array {
		$ran = false;

		foreach ($this->jobList->getJobsIterator(StorageCrawlJob::class, 1, 0) as $job) {
			$argument = $job->getArgument();

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
		}

		$pending = false;
		foreach ($this->jobList->getJobsIterator(StorageCrawlJob::class, 1, 0) as $job) {
			$pending = true;
		}

		if ($ran) {
			$this->logger->debug('Findling: advanced the crawl by one slice on request', ['pending' => $pending]);
		}

		return ['ran' => $ran, 'pending' => $pending];
	}
}
