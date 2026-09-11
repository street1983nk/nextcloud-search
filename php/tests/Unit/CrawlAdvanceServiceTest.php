<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCA\Findling\Service\CrawlAdvanceService;
use OCP\BackgroundJob\IJob;
use OCP\BackgroundJob\IJobList;
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

		$service = new CrawlAdvanceService($jobList, $this->createMock(LoggerInterface::class));

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

		$service = new CrawlAdvanceService($jobList, $this->createMock(LoggerInterface::class));

		self::assertSame(['ran' => true, 'pending' => false], $service->advance());
		self::assertSame(['removed', 'argument', 'started'], $sequence);
	}

	public function testTheAnswerSaysWhetherMoreSlicesWait(): void {
		$job = $this->createMock(IJob::class);
		$job->method('getArgument')->willReturn(self::CANONICAL);
		$successor = $this->createMock(IJob::class);

		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturnOnConsecutiveCalls([$job], [$successor]);

		$service = new CrawlAdvanceService($jobList, $this->createMock(LoggerInterface::class));

		self::assertSame(['ran' => true, 'pending' => true], $service->advance());
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
