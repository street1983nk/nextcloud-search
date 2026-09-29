<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\BackgroundJobs\ScanRecountJob;
use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJob;
use OCP\BackgroundJob\IJobList;
use OCP\IAppConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The recount of the coverage denominator (quick task 260929-kii): when it is
 * due, that it never starts next to a crawl, and that it plans exactly one
 * counting chain per mount.
 *
 * SettingsService is final, so a real one is built on a doubled IAppConfig
 * that keeps its values in an array, the seam SettingsServiceTest uses.
 */
#[CoversClass(ScanRecountJob::class)]
final class ScanRecountJobTest extends TestCase {
	private const NOW = 1790000000;

	/** @var array<string, int> the stored int keys of the app */
	private array $values = [];

	private IAppConfig&MockObject $appConfig;
	private ITimeFactory&MockObject $time;

	protected function setUp(): void {
		parent::setUp();

		$this->values = [];
		$this->appConfig = $this->createMock(IAppConfig::class);
		$this->appConfig->method('getValueInt')->willReturnCallback(
			fn (string $app, string $key, int $default = 0): int => $this->values[$key] ?? $default,
		);
		$this->appConfig->method('setValueInt')->willReturnCallback(
			function (string $app, string $key, int $value): bool {
				$this->values[$key] = $value;

				return true;
			},
		);

		$this->time = $this->createMock(ITimeFactory::class);
		$this->time->method('getTime')->willReturn(self::NOW);
	}

	private function job(IJobList $jobList, StorageService $storageService): ScanRecountJob {
		return new ScanRecountJob(
			$this->time,
			$jobList,
			$storageService,
			new SettingsService($this->appConfig, $this->createMock(LoggerInterface::class), $this->time),
			$this->createMock(LoggerInterface::class),
		);
	}

	private function runJob(ScanRecountJob $job): void {
		$run = new \ReflectionMethod($job, 'run');
		$run->invoke($job, null);
	}

	/**
	 * @return array<string, int|string>
	 */
	private static function recountArgument(int $storageId, int $rootId): array {
		return [
			'storage_id' => $storageId,
			'root_id' => $rootId,
			'overridden_root' => $rootId,
			'last_file_id' => 0,
			'mode' => StorageCrawlJob::MODE_RECOUNT,
			'files_seen' => 0,
			'bytes_seen' => 0,
			'ocr_candidates' => 0,
			'pdf_seen' => 0,
			'over_cap' => 0,
			'excluded' => 0,
		];
	}

	public function testNothingIsPlannedWhileACrawlRowExists(): void {
		$this->values[SettingsService::KEY_SCAN_STALE_SINCE] = self::NOW - 60;

		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturn([$this->createMock(IJob::class)]);
		$jobList->expects($this->never())->method('add');

		$storageService = $this->createMock(StorageService::class);
		$storageService->expects($this->never())->method('getMounts');

		$this->runJob($this->job($jobList, $storageService));

		// The mark survives for the round after the crawl.
		self::assertSame(self::NOW - 60, $this->values[SettingsService::KEY_SCAN_STALE_SINCE]);
	}

	public function testNothingIsPlannedWhenNotMarkedAndRecentlyRecounted(): void {
		$this->values[SettingsService::KEY_SCAN_RECOUNTED_AT] = self::NOW - 3600;

		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturn([]);
		$jobList->expects($this->never())->method('add');

		$storageService = $this->createMock(StorageService::class);
		$storageService->expects($this->never())->method('getMounts');

		$this->runJob($this->job($jobList, $storageService));
	}

	public function testAMarkPlansOneRecountChainPerMount(): void {
		$this->values[SettingsService::KEY_SCAN_RECOUNTED_AT] = self::NOW - 3600;
		$this->values[SettingsService::KEY_SCAN_STALE_SINCE] = self::NOW - 60;

		$added = [];
		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturn([]);
		$jobList->expects($this->exactly(2))->method('add')
			->willReturnCallback(function (string $class, mixed $argument) use (&$added): void {
				$added[] = [$class, $argument];
			});

		$storageService = $this->createMock(StorageService::class);
		$storageService->method('getMounts')->willReturn([
			['storage_id' => 3, 'root_id' => 12, 'overridden_root' => 12],
			['storage_id' => 7, 'root_id' => 40, 'overridden_root' => 40],
		]);

		$this->runJob($this->job($jobList, $storageService));

		self::assertSame([
			[StorageCrawlJob::class, self::recountArgument(3, 12)],
			[StorageCrawlJob::class, self::recountArgument(7, 40)],
		], $added);
		// The mark is cleared and the time remembered before the chains run.
		self::assertSame(0, $this->values[SettingsService::KEY_SCAN_STALE_SINCE]);
		self::assertSame(self::NOW, $this->values[SettingsService::KEY_SCAN_RECOUNTED_AT]);
	}

	public function testAQuietInstanceIsRecountedAfterADay(): void {
		$this->values[SettingsService::KEY_SCAN_RECOUNTED_AT] = self::NOW - SettingsService::RECOUNT_FLOOR_SECONDS;

		$jobList = $this->createMock(IJobList::class);
		$jobList->method('getJobsIterator')->willReturn([]);
		$jobList->expects($this->once())->method('add')
			->with(StorageCrawlJob::class, self::recountArgument(3, 12));

		$storageService = $this->createMock(StorageService::class);
		$storageService->method('getMounts')->willReturn([
			['storage_id' => 3, 'root_id' => 12, 'overridden_root' => 12],
		]);

		$this->runJob($this->job($jobList, $storageService));
	}

	public function testTheIntervalIsAQuarterOfAnHour(): void {
		self::assertSame(900, ScanRecountJob::INTERVAL_SECONDS);
	}
}
