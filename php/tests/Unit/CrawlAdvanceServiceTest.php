<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\BackgroundJobs\SchedulerJob;
use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCA\Findling\Service\CrawlAdvanceService;
use OCP\BackgroundJob\IJob;
use OCP\BackgroundJob\IJobList;
use OCP\Lock\ILockingProvider;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The top-up of a starved container, the fix of the v1.1 comparison finding
 * (DI-10-04: 5.85 of 26.6 hours starved because the crawl advanced only with
 * the system cron).
 *
 * Three statements hold. A container that asks while no crawl job exists gets
 * the honest "idle" answer and nothing runs. A pending job is executed exactly
 * once, with its row removed under the CANONICAL argument before the run, and
 * with the shorter budget in the argument the run sees, because the caller
 * waits on an OCS request with a 30 s client timeout. And the answer says
 * whether more slices wait, because that is what the container's pause length
 * hangs on.
 */
#[CoversClass(CrawlAdvanceService::class)]
final class CrawlAdvanceServiceTest extends TestCase {
	private const CANONICAL = [
		'storage_id' => 3,
		'root_id' => 12,
		'overridden_root' => 12,
		'last_file_id' => 4711,
	];

	public function testNoCrawlJobAnswersIdleAndRunsNothing(): void {
		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturn([]);
		$jobList->expects($this->never())->method('remove');

		$service = $this->service($jobList);

		self::assertSame(['ran' => false, 'pending' => false], $service->advance());
	}

	public function testAPendingJobIsRemovedUnderItsCanonicalArgumentBeforeItRuns(): void {
		$job = $this->createMock(IJob::class);
		$job->method('getArgument')->willReturn(self::CANONICAL);

		// The order is the whole point of the removal: QueuedJob::start removes
		// under the argument the job carries at that moment, which is the
		// modified one and matches no row, so a row not removed here first is a
		// slice the cron crawls a second time.
		$sequence = [];

		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturnOnConsecutiveCalls([$job], []);
		$jobList->expects($this->once())->method('remove')
			->with($job, self::CANONICAL)
			->willReturnCallback(function () use (&$sequence): void {
				$sequence[] = 'removed';
			});

		$job->expects($this->once())->method('setArgument')
			->with(array_merge(self::CANONICAL, ['budget_seconds' => CrawlAdvanceService::BUDGET_SECONDS]))
			->willReturnCallback(function () use (&$sequence): void {
				$sequence[] = 'argument';
			});
		$job->expects($this->once())->method('start')
			->with($jobList)
			->willReturnCallback(function () use (&$sequence): void {
				$sequence[] = 'started';
			});

		$service = $this->service($jobList);

		self::assertSame(['ran' => true, 'pending' => false], $service->advance());
		self::assertSame(['removed', 'argument', 'started'], $sequence);
	}

	public function testTheAnswerSaysWhetherMoreSlicesWait(): void {
		$job = $this->createMock(IJob::class);
		$job->method('getArgument')->willReturn(self::CANONICAL);
		$successor = $this->createMock(IJob::class);

		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturnOnConsecutiveCalls([$job], [$successor]);

		$service = $this->service($jobList);

		self::assertSame(['ran' => true, 'pending' => true], $service->advance());
	}

	public function testARecountAtTheHeadIsNoWorkTheContainerWaitsFor(): void {
		// Quick task 260929-kii: a recount chain queues nothing, so the top-up
		// neither runs it nor reports it as pending.
		$job = $this->createMock(IJob::class);
		$job->method('getArgument')->willReturn(array_merge(self::CANONICAL, [
			'mode' => StorageCrawlJob::MODE_RECOUNT,
			'files_seen' => 10,
		]));
		$job->expects($this->never())->method('setArgument');
		$job->expects($this->never())->method('start');

		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturn([$job]);
		$jobList->expects($this->never())->method('remove');

		$service = $this->service($jobList);

		self::assertSame(['ran' => false, 'pending' => false], $service->advance());
	}

	public function testACrawlRowBehindARecountRowStillRuns(): void {
		// Review WR-01 of phase 27: a recount row at the head used to end the
		// search with "nothing pending" while a crawl row waited behind it.
		$recount = $this->createMock(IJob::class);
		$recount->method('getArgument')->willReturn(array_merge(self::CANONICAL, [
			'mode' => StorageCrawlJob::MODE_RECOUNT,
		]));
		$recount->expects($this->never())->method('start');

		$crawl = $this->createMock(IJob::class);
		$crawl->method('getArgument')->willReturn(self::CANONICAL);
		$crawl->expects($this->once())->method('start');
		$successor = $this->createMock(IJob::class);
		$successor->method('getArgument')->willReturn(self::CANONICAL);

		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturnOnConsecutiveCalls(
			[$recount, $crawl],
			[$recount, $successor],
		);
		$jobList->expects($this->once())->method('remove')->with($crawl, self::CANONICAL);

		$service = $this->service($jobList);

		self::assertSame(['ran' => true, 'pending' => true], $service->advance());
	}

	public function testOnlyRecountRowsLeftIsNotPending(): void {
		$crawl = $this->createMock(IJob::class);
		$crawl->method('getArgument')->willReturn(self::CANONICAL);
		$recount = $this->createMock(IJob::class);
		$recount->method('getArgument')->willReturn(array_merge(self::CANONICAL, [
			'mode' => StorageCrawlJob::MODE_RECOUNT,
		]));

		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturnOnConsecutiveCalls([$crawl], [$recount]);

		$service = $this->service($jobList);

		self::assertSame(['ran' => true, 'pending' => false], $service->advance());
	}

	/**
	 * The jobs of the instance by class, the way IJobList answers a filtered
	 * iterator.
	 *
	 * @param array<class-string, list<IJob>> $rows
	 */
	private function jobListWith(array $rows): IJobList {
		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturnCallback(
			static fn ($job): array => is_string($job) ? ($rows[$job] ?? []) : [],
		);
		return $jobList;
	}

	private function service(IJobList $jobList, bool $sliceLocked = false): CrawlAdvanceService {
		$locks = $this->createMock(ILockingProvider::class);
		$locks->method('isLocked')->willReturnCallback(
			static fn (string $path, int $type): bool => $sliceLocked
				&& $path === StorageCrawlJob::LOCK_NAME
				&& $type === ILockingProvider::LOCK_EXCLUSIVE,
		);
		return new CrawlAdvanceService($jobList, $this->createMock(LoggerInterface::class), $locks);
	}

	/*
	 * Whether the crawl is unfinished, for the reconcile of the container
	 * (run 8 of the 28-07 chain, abort 71 at 5427 of 5000). Fifteen slots drained
	 * the work stock faster than the cron paced crawl filled it, the reconcile
	 * read the empty queue as a quiet instance, walked ahead and requeued every
	 * file the crawl had not reached yet, and the crawl queued all 5000 of them a
	 * second time. An empty queue during a crawl is not a quiet instance, and
	 * this is the one answer that says so.
	 */

	public function testNothingPlannedAndNoSliceRunningIsNoCrawl(): void {
		self::assertFalse($this->service($this->jobListWith([]))->crawling());
	}

	public function testACrawlRowIsAnUnfinishedCrawl(): void {
		$crawl = $this->createMock(IJob::class);
		$crawl->method('getArgument')->willReturn(self::CANONICAL);

		self::assertTrue($this->service($this->jobListWith([StorageCrawlJob::class => [$crawl]]))->crawling());
	}

	public function testAWaitingSchedulerIsAnUnfinishedCrawl(): void {
		// occ findling:index --restart and a fresh install queue the scheduler
		// first; until it ran there is no crawl row, and the crawl is all ahead.
		$scheduler = $this->createMock(IJob::class);

		self::assertTrue($this->service($this->jobListWith([SchedulerJob::class => [$scheduler]]))->crawling());
	}

	public function testARunningSliceIsAnUnfinishedCrawl(): void {
		// A QueuedJob removes its row before it runs, and the successor is only
		// planned at the end of the slice: for those seconds the last chain of
		// the instance has no row at all. The slice lock is held exactly then.
		self::assertTrue($this->service($this->jobListWith([]), sliceLocked: true)->crawling());
	}

	public function testARecountRowAloneIsNoCrawl(): void {
		// Quick task 260929-kii: a recount queues nothing and only starts once
		// the crawl is through, so the reconcile has nothing to wait for.
		$recount = $this->createMock(IJob::class);
		$recount->method('getArgument')->willReturn(array_merge(self::CANONICAL, [
			'mode' => StorageCrawlJob::MODE_RECOUNT,
		]));

		self::assertFalse($this->service($this->jobListWith([StorageCrawlJob::class => [$recount]]))->crawling());
	}

	public function testTheBudgetIsClampedBetweenTheFloorAndTheCeiling(): void {
		// The clamp lives in the job, but the service is what hands the budget
		// over, so the agreement between the two is asserted where both ends
		// are visible: the constant fits under the ceiling, and the clamp
		// refuses budgets that would starve or overrun a slice.
		self::assertSame(CrawlAdvanceService::BUDGET_SECONDS, StorageCrawlJob::budgetSeconds(['budget_seconds' => CrawlAdvanceService::BUDGET_SECONDS]));
		self::assertSame(30, StorageCrawlJob::budgetSeconds([]));
		self::assertSame(30, StorageCrawlJob::budgetSeconds('not an array'));
		self::assertSame(30, StorageCrawlJob::budgetSeconds(['budget_seconds' => 999]));
		self::assertSame(5, StorageCrawlJob::budgetSeconds(['budget_seconds' => 1]));
	}
}
