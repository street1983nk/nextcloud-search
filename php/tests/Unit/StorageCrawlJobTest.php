<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\ScanStatsService;
use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\IAppConfig;
use OCP\IDBConnection;
use OCP\Lock\ILockingProvider;
use OCP\Lock\LockedException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The crawl slice lock, the concurrency half of the top-up route (DI-10-04).
 *
 * Two doors lead into a slice since the top-up exists, the cron and a starved
 * container, and the lock is what keeps them from crawling the same band twice.
 * The statement that has to hold and can go red: the entrant that loses the
 * lock crawls NOTHING and reschedules the very argument it arrived with, in its
 * canonical shape, because being a QueuedJob its row was removed before run()
 * and a return without the reschedule would end the crawl of this mount for
 * good.
 *
 * The three final services of the constructor are built without their
 * constructors. That is not a shortcut around mocking: the branch under test
 * must never touch them, and an uninitialised typed property is the loudest
 * possible failure if it ever does.
 */
#[CoversClass(StorageCrawlJob::class)]
final class StorageCrawlJobTest extends TestCase {
	private const NOW = 1757600000;

	/**
	 * @param array<string, mixed> $argument
	 */
	private function runJob(StorageCrawlJob $job, array $argument): void {
		$run = new \ReflectionMethod($job, 'run');
		$run->invoke($job, $argument);
	}

	public function testALostLockCrawlsNothingAndReschedulesTheCanonicalArgument(): void {
		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturn(self::NOW);

		$locking = $this->createMock(ILockingProvider::class);
		$locking->method('acquireLock')
			->with(StorageCrawlJob::LOCK_NAME, ILockingProvider::LOCK_EXCLUSIVE)
			->willThrowException(new LockedException(StorageCrawlJob::LOCK_NAME));
		// A lock that was never taken is never given back: a release here would
		// free the lock of the OTHER entrant, which is the slice running right
		// now.
		$locking->expects($this->never())->method('releaseLock');

		$jobList = $this->createMock(IJobList::class);
		// The canonical shape and not the arriving one: a budget_seconds from
		// the top-up route must not travel into the cron chain, where it would
		// shorten every following slice for no caller at all.
		$jobList->expects($this->once())->method('scheduleAfter')
			->with(StorageCrawlJob::class, self::NOW + 5, [
				'storage_id' => 3,
				'root_id' => 12,
				'overridden_root' => 12,
				'last_file_id' => 4711,
			]);

		$storageService = $this->createMock(StorageService::class);
		$storageService->expects($this->never())->method('getFilesInMount');

		$db = $this->createMock(IDBConnection::class);
		$db->expects($this->never())->method('beginTransaction');

		$job = new StorageCrawlJob(
			$time,
			$jobList,
			$storageService,
			$this->createMock(QueueService::class),
			$this->createMock(FileStateService::class),
			(new \ReflectionClass(ScanStatsService::class))->newInstanceWithoutConstructor(),
			(new \ReflectionClass(SettingsService::class))->newInstanceWithoutConstructor(),
			(new \ReflectionClass(ExclusionService::class))->newInstanceWithoutConstructor(),
			$this->createMock(IAppConfig::class),
			$db,
			$locking,
			$this->createMock(LoggerInterface::class),
		);

		$this->runJob($job, [
			'storage_id' => 3,
			'root_id' => 12,
			'overridden_root' => 12,
			'last_file_id' => 4711,
			'budget_seconds' => 20,
		]);
	}

	public function testAMalformedMountNeverAsksForTheLock(): void {
		// The guard of the very first line stays in front of the lock: a job
		// without a usable mount is dropped, not serialised.
		$locking = $this->createMock(ILockingProvider::class);
		$locking->expects($this->never())->method('acquireLock');

		$jobList = $this->createMock(IJobList::class);
		$jobList->expects($this->never())->method('scheduleAfter');

		$job = new StorageCrawlJob(
			$this->createMock(ITimeFactory::class),
			$jobList,
			$this->createMock(StorageService::class),
			$this->createMock(QueueService::class),
			$this->createMock(FileStateService::class),
			(new \ReflectionClass(ScanStatsService::class))->newInstanceWithoutConstructor(),
			(new \ReflectionClass(SettingsService::class))->newInstanceWithoutConstructor(),
			(new \ReflectionClass(ExclusionService::class))->newInstanceWithoutConstructor(),
			$this->createMock(IAppConfig::class),
			$this->createMock(IDBConnection::class),
			$locking,
			$this->createMock(LoggerInterface::class),
		);

		$this->runJob($job, ['storage_id' => 0, 'root_id' => 0, 'overridden_root' => 0]);
	}
}
