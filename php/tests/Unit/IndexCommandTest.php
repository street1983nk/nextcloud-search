<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\BackgroundJobs\SchedulerJob;
use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCA\Findling\Command\IndexCommand;
use OCA\Findling\Repair\AppInstallStep;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\IAppConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * What the emergency lever has to take with it: the work stock (BLOCKER-28-07).
 *
 * The finding this defends, three times over in run 3 of the acceptance trip
 * (f09504ae): `occ findling:index --restart` removed the crawl jobs and raised
 * the first-index mark again, and it left 3420 orders of the earlier run
 * standing in findling_queue. The crawl only pushes itself forward while the
 * stock is empty (CrawlAdvanceService), so the fresh crawl starved in the cron
 * interval behind work nobody wanted any more. An admin pulling the documented
 * emergency lever on a wedged instance kept the old stock, did every file
 * twice, and watched the same starving crawl again.
 *
 * The order of the clearing is the second half of the contract and the reason
 * these tests record a protocol instead of counting calls. The stock is cleared
 * AFTER both job removals, because an old StorageCrawlJob that still runs would
 * refill the stock between a clearing and its removal; and BEFORE the new
 * SchedulerJob is added, so the new crawl never competes with leftovers. The
 * private method is reached over reflection, which has its precedent in
 * QueueServiceTest::testTheExtractionKindsAreContentAndOcrAndNothingElse: the
 * interesting half is the arithmetic of restart() and not the console plumbing
 * of execute(), whose confirmation question cannot be asked without a terminal.
 */
#[CoversClass(IndexCommand::class)]
final class IndexCommandTest extends TestCase {
	/**
	 * Everything restart() touches, in the order it touches it.
	 *
	 * @param list<string> $protocol written by the callbacks of the mocks below
	 */
	private function commandWritingTo(array &$protocol): IndexCommand {
		$jobList = $this->createMock(IJobList::class);
		$jobList->method('remove')->willReturnCallback(static function (string $job) use (&$protocol): void {
			$protocol[] = 'remove ' . $job;
		});
		$jobList->method('add')->willReturnCallback(static function (string $job) use (&$protocol): void {
			$protocol[] = 'add ' . $job;
		});

		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('deleteKey')->willReturnCallback(static function (string $app, string $key) use (&$protocol): void {
			$protocol[] = 'deleteKey ' . $app . ' ' . $key;
		});
		$appConfig->method('setValueBool')->willReturnCallback(static function (string $app, string $key, bool $value) use (&$protocol): bool {
			$protocol[] = 'setValueBool ' . $app . ' ' . $key . ' ' . ($value ? 'true' : 'false');
			return true;
		});

		$queueService = $this->createMock(QueueService::class);
		$queueService->expects(self::once())->method('clear')->willReturnCallback(static function () use (&$protocol): int {
			$protocol[] = 'clear';
			return 3420;
		});

		return new IndexCommand(
			$jobList,
			$appConfig,
			$queueService,
			$this->createMock(FileStateService::class),
			$this->createMock(ITimeFactory::class),
		);
	}

	private function restart(IndexCommand $command): void {
		(new \ReflectionMethod(IndexCommand::class, 'restart'))->invoke($command);
	}

	public function testRestartClearsTheStockBetweenTheRemovalsAndTheNewScheduler(): void {
		// The one acceptable moment for the clearing, pinned as a sequence: both
		// removals first, so no old crawl job refills the stock afterwards, and
		// the new SchedulerJob only after the stock is gone.
		$protocol = [];
		$command = $this->commandWritingTo($protocol);

		$this->restart($command);

		$jobSteps = array_values(array_filter($protocol, static fn (string $step): bool => $step === 'clear' || str_starts_with($step, 'remove ') || str_starts_with($step, 'add ')));
		self::assertSame([
			'remove ' . StorageCrawlJob::class,
			'remove ' . SchedulerJob::class,
			'clear',
			'add ' . SchedulerJob::class,
		], $jobSteps);
	}

	public function testRestartStillDropsAndRaisesTheFirstIndexMark(): void {
		// The contract that was already there and must survive the fix: the mark
		// is deleted first and raised again at the end, so the repair step of a
		// reinstall and the restart cannot disagree about whether a first index
		// was scheduled.
		$protocol = [];
		$command = $this->commandWritingTo($protocol);

		$this->restart($command);

		$markSteps = array_values(array_filter($protocol, static fn (string $step): bool => str_contains($step, AppInstallStep::FIRST_INDEX_SCHEDULED)));
		self::assertSame([
			'deleteKey ' . Application::APP_ID . ' ' . AppInstallStep::FIRST_INDEX_SCHEDULED,
			'setValueBool ' . Application::APP_ID . ' ' . AppInstallStep::FIRST_INDEX_SCHEDULED . ' true',
		], $markSteps);
	}
}
