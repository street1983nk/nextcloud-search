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
use OCP\DB\IResult;
use OCP\DB\QueryBuilder\IExpressionBuilder;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\Files\Cache\ICacheEntry;
use OCP\IAppConfig;
use OCP\IDBConnection;
use OCP\Lock\ILockingProvider;
use OCP\Lock\LockedException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
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

	// -- the counting mode (quick task 260929-kii) -------------------------------

	/** @var list<array{string, array<string, mixed>}> every statement the scan counters sent */
	private array $statements = [];

	/**
	 * A real ScanStatsService (it is final) on a doubled connection that
	 * records every statement with the values it set, and answers a select
	 * with the given row.
	 *
	 * @param array<string, mixed>|null $row
	 */
	private function scanStats(?array $row, int $updateHits = 1): ScanStatsService {
		$db = $this->createMock(IDBConnection::class);
		$db->method('getQueryBuilder')->willReturnCallback(function () use ($row, $updateHits): IQueryBuilder {
			$record = ['kind' => 'select', 'params' => [], 'sets' => []];

			$expr = $this->createMock(IExpressionBuilder::class);
			$expr->method('eq')->willReturn('eq');
			$expr->method('isNotNull')->willReturn('is not null');

			$qb = $this->createMock(IQueryBuilder::class);
			$qb->method('expr')->willReturn($expr);
			$qb->method('select')->willReturnSelf();
			$qb->method('from')->willReturnSelf();
			$qb->method('where')->willReturnSelf();
			$qb->method('andWhere')->willReturnSelf();
			$qb->method('setMaxResults')->willReturnSelf();
			$qb->method('update')->willReturnCallback(function () use ($qb, &$record): IQueryBuilder {
				$record['kind'] = 'update';

				return $qb;
			});
			$qb->method('createNamedParameter')->willReturnCallback(function (mixed $value) use (&$record): string {
				$name = ':p' . count($record['params']);
				$record['params'][$name] = $value;

				return $name;
			});
			$qb->method('set')->willReturnCallback(function (string $key, mixed $value) use ($qb, &$record): IQueryBuilder {
				$record['sets'][$key] = is_string($value) && array_key_exists($value, $record['params'])
					? $record['params'][$value]
					: $value;

				return $qb;
			});
			$qb->method('executeStatement')->willReturnCallback(function () use (&$record, $updateHits): int {
				$this->statements[] = [$record['kind'], $record['sets']];

				return $updateHits;
			});
			$qb->method('executeQuery')->willReturnCallback(function () use ($row): IResult {
				$this->statements[] = ['select', []];
				$result = $this->createMock(IResult::class);
				$result->method('fetch')->willReturn($row ?? false);

				return $result;
			});

			return $qb;
		});
		$db->method('insertIgnoreConflict')->willReturnCallback(function (string $table, array $values): int {
			$this->statements[] = ['insert', $values];

			return 1;
		});

		$time = $this->createMock(ITimeFactory::class);
		$time->method('getDateTime')->willReturn(new \DateTime('@' . self::NOW));

		return new ScanStatsService($db, $time, $this->createMock(LoggerInterface::class));
	}

	private function entry(int $id, string $path, int $size, string $mimeType): ICacheEntry&MockObject {
		$entry = $this->createMock(ICacheEntry::class);
		$entry->method('getId')->willReturn($id);
		$entry->method('getPath')->willReturn($path);
		$entry->method('getSize')->willReturn($size);
		$entry->method('getMimeType')->willReturn($mimeType);

		return $entry;
	}

	/**
	 * The job with real final services and doubles that fail loudly on every
	 * write a recount must never make.
	 */
	private function recountJob(
		ITimeFactory $time,
		IJobList $jobList,
		StorageService $storageService,
		ScanStatsService $scanStats,
	): StorageCrawlJob {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueInt')->willReturnCallback(
			static fn (string $app, string $key, int $default = 0): int => $default,
		);
		$appConfig->method('getValueArray')->willReturnCallback(
			static fn (string $app, string $key, array $default = []): array => $key === SettingsService::KEY_EXCLUSIONS ? ['Archiv'] : $default,
		);
		// No LAST_JOB_RUN: a count is not motion of the index.
		$appConfig->expects($this->never())->method('setValueInt');

		$queue = $this->createMock(QueueService::class);
		$queue->expects($this->never())->method('enqueue');
		$fileState = $this->createMock(FileStateService::class);
		$fileState->expects($this->never())->method('record');

		$db = $this->createMock(IDBConnection::class);
		$db->expects($this->never())->method('beginTransaction');

		$logger = $this->createMock(LoggerInterface::class);

		return new StorageCrawlJob(
			$time,
			$jobList,
			$storageService,
			$queue,
			$fileState,
			$scanStats,
			new SettingsService($appConfig, $logger, $time),
			new ExclusionService($appConfig, $storageService, $jobList, $logger),
			$appConfig,
			$db,
			$this->createMock(ILockingProvider::class),
			$logger,
		);
	}

	/**
	 * @param array<string, int> $sums
	 * @return array<string, int|string>
	 */
	private static function recountArgument(int $lastFileId, array $sums = []): array {
		return [
			'storage_id' => 3,
			'root_id' => 12,
			'overridden_root' => 12,
			'last_file_id' => $lastFileId,
			'mode' => StorageCrawlJob::MODE_RECOUNT,
			'files_seen' => $sums['files_seen'] ?? 0,
			'bytes_seen' => $sums['bytes_seen'] ?? 0,
			'ocr_candidates' => $sums['ocr_candidates'] ?? 0,
			'pdf_seen' => $sums['pdf_seen'] ?? 0,
			'over_cap' => $sums['over_cap'] ?? 0,
			'excluded' => $sums['excluded'] ?? 0,
		];
	}

	/** @return array<string, mixed> a finished row as the database holds it */
	private static function finishedRow(): array {
		return [
			'storage_id' => 3,
			'files_seen' => 587,
			'bytes_seen' => 1,
			'ocr_candidates' => 1,
			'pdf_seen' => 1,
			'over_cap' => 0,
			'excluded' => 0,
			'cursor_file_id' => 900,
			'finished_at' => '2026-09-01 00:00:00',
		];
	}

	public function testARecountWalksEveryPageAndReplacesTheRowOnceAtTheEnd(): void {
		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturn(self::NOW);

		$storageService = $this->createMock(StorageService::class);
		$storageService->method('mountRootPath')->willReturn('files');
		$storageService->expects($this->exactly(3))->method('getFilesInMount')->willReturnOnConsecutiveCalls(
			[
				$this->entry(10, 'files/Report.pdf', 1000, 'application/pdf'),
				// Excluded AND over the cap: exclusion comes first.
				$this->entry(11, 'files/Archiv/Scan.jpg', 60 * 1024 * 1024, 'image/jpeg'),
			],
			[
				$this->entry(12, 'files/Big.txt', 60 * 1024 * 1024, 'text/plain'),
				$this->entry(13, 'files/Photo.png', 200, 'image/png'),
			],
			[],
		);

		$jobList = $this->createMock(IJobList::class);
		$jobList->expects($this->never())->method('scheduleAfter');

		$this->runJob(
			$this->recountJob($time, $jobList, $storageService, $this->scanStats(self::finishedRow())),
			self::recountArgument(0),
		);

		// One select (is a crawl counting this mount?) and exactly one update
		// with absolute values: no beginStorage, no add, no finishStorage.
		self::assertCount(2, $this->statements);
		self::assertSame('select', $this->statements[0][0]);
		self::assertSame('update', $this->statements[1][0]);
		$sets = $this->statements[1][1];
		self::assertSame(4, $sets['files_seen']);
		self::assertSame(1000 + 2 * 60 * 1024 * 1024 + 200, $sets['bytes_seen']);
		self::assertSame(2, $sets['ocr_candidates']);
		self::assertSame(1, $sets['pdf_seen']);
		self::assertSame(1, $sets['over_cap']);
		self::assertSame(1, $sets['excluded']);
		self::assertSame(13, $sets['cursor_file_id']);
		self::assertInstanceOf(\DateTimeInterface::class, $sets['finished_at']);
	}

	public function testARecountLeavesAMountThatIsBeingCrawledAlone(): void {
		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturn(self::NOW);

		$storageService = $this->createMock(StorageService::class);
		$storageService->expects($this->never())->method('getFilesInMount');

		$jobList = $this->createMock(IJobList::class);
		$jobList->expects($this->never())->method('scheduleAfter');

		$row = self::finishedRow();
		$row['finished_at'] = null;

		$this->runJob(
			$this->recountJob($time, $jobList, $storageService, $this->scanStats($row)),
			self::recountArgument(0),
		);

		self::assertSame([['select', []]], $this->statements);
	}

	public function testARecountOutOfBudgetCarriesItsSumsToTheSuccessor(): void {
		// The first reading sets the deadline, every later one is past it.
		$readings = 0;
		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturnCallback(function () use (&$readings): int {
			return $readings++ === 0 ? self::NOW : self::NOW + 100;
		});

		$storageService = $this->createMock(StorageService::class);
		$storageService->method('mountRootPath')->willReturn('files');
		$storageService->expects($this->once())->method('getFilesInMount')
			->with(3, 12, 4711, StorageCrawlJob::BATCH_SIZE)
			->willReturn([$this->entry(4800, 'files/Letter.pdf', 1000, 'application/pdf')]);

		$jobList = $this->createMock(IJobList::class);
		$jobList->expects($this->once())->method('scheduleAfter')
			->with(StorageCrawlJob::class, self::NOW + 105, self::recountArgument(4800, [
				'files_seen' => 6,
				'bytes_seen' => 6000,
				'ocr_candidates' => 1,
				'pdf_seen' => 3,
				'over_cap' => 1,
				'excluded' => 1,
			]));

		$this->runJob(
			$this->recountJob($time, $jobList, $storageService, $this->scanStats(self::finishedRow())),
			self::recountArgument(4711, [
				'files_seen' => 5,
				'bytes_seen' => 5000,
				'ocr_candidates' => 1,
				'pdf_seen' => 2,
				'over_cap' => 1,
				'excluded' => 1,
			]),
		);

		// Only the select: nothing is replaced before the end of the mount.
		self::assertSame([['select', []]], $this->statements);
	}

	public function testALostLockInARecountReschedulesItsModeAndItsSums(): void {
		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturn(self::NOW);

		$locking = $this->createMock(ILockingProvider::class);
		$locking->method('acquireLock')->willThrowException(new LockedException(StorageCrawlJob::LOCK_NAME));

		$sums = ['files_seen' => 5, 'bytes_seen' => 5000, 'ocr_candidates' => 1, 'pdf_seen' => 2, 'over_cap' => 1, 'excluded' => 1];

		$jobList = $this->createMock(IJobList::class);
		$jobList->expects($this->once())->method('scheduleAfter')
			->with(StorageCrawlJob::class, self::NOW + 5, self::recountArgument(4711, $sums));

		$storageService = $this->createMock(StorageService::class);
		$storageService->expects($this->never())->method('getFilesInMount');

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
			$this->createMock(IDBConnection::class),
			$locking,
			$this->createMock(LoggerInterface::class),
		);

		$this->runJob($job, array_merge(self::recountArgument(4711, $sums), ['budget_seconds' => 20]));
	}
}
