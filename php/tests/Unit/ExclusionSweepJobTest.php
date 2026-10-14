<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\BackgroundJobs\ExclusionSweepJob;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\Files\Cache\ICacheEntry;
use OCP\IAppConfig;
use OCP\IDBConnection;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * Way A of the patterns (plan 33-04, EXCL-02, PE-10): the sweep that clears
 * the files a new pattern covers, and the planning of it in savePatterns().
 *
 * Two mounts as an instance has them, a home and a Team Folder, each with a
 * file under ``*.key``, a control file next to it and the counter case
 * ``Vortrag.keynote``, whose name starts like the pattern and is not under it.
 * The sweep has to queue a delete row for exactly the two files under the
 * pattern and forget exactly their verdicts, walk on with a cursor in bands
 * and under a wall clock, and end without doing anything when the pattern set
 * it was planned for is no longer the one in force.
 *
 * ExclusionService is final and is built for real over a mocked app config,
 * the same way StorageCrawlJobTest builds it, so the decision about a file is
 * the real one. Everything the job writes goes into a double that records it.
 */
#[CoversClass(ExclusionSweepJob::class)]
final class ExclusionSweepJobTest extends TestCase {
	private const NOW = 1757600000;

	private const HOME = ['storage_id' => 3, 'root_id' => 12, 'overridden_root' => 12];
	private const TEAM = ['storage_id' => 9, 'root_id' => 40, 'overridden_root' => 41];

	/** The clock of the job, moved by the file doubles below. */
	private int $now = self::NOW;

	/** @var list<array{int, int, int, int, bool, string}> every enqueueFile call */
	private array $enqueued = [];

	/** @var list<list<int>> every forgetVerdicts call */
	private array $forgotten = [];

	/** @var list<array{string, int, mixed}> every successor the job planned */
	private array $scheduled = [];

	/** @var list<array{int, int, int, int}> every band the job asked for: storage, root, cursor, size */
	private array $bands = [];

	/** @var list<array{level: string, message: string, context: array<array-key, mixed>}> */
	private array $logLines = [];

	/** @var list<array{string, string, mixed}> what savePatterns did to the job list, in order */
	private array $jobCalls = [];

	/**
	 * The service over an app config that holds these two lists.
	 *
	 * @param list<string> $patterns
	 * @param list<string> $prefixes
	 */
	private function exclusions(array $patterns, array $prefixes = [], ?IJobList $jobList = null): ExclusionService {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueArray')->willReturnCallback(
			static fn (string $app, string $key, array $default = []): array => match ($key) {
				SettingsService::KEY_EXCLUSIONS => $prefixes,
				SettingsService::KEY_EXCLUSION_PATTERNS => $patterns,
				default => $default,
			},
		);

		return new ExclusionService(
			$appConfig,
			$this->createMock(StorageService::class),
			$jobList ?? $this->createMock(IJobList::class),
			$this->createMock(LoggerInterface::class),
		);
	}

	/** @param list<string> $patterns */
	private function fingerprintOf(array $patterns): string {
		return $this->exclusions($patterns)->patternFingerprint();
	}

	private function entry(int $id, string $path): ICacheEntry&MockObject {
		$entry = $this->createMock(ICacheEntry::class);
		$entry->method('getId')->willReturn($id);
		$entry->method('getPath')->willReturn($path);
		$entry->method('getSize')->willReturn(1000);

		return $entry;
	}

	/**
	 * A storage double over the given mounts. Each mount carries its root path
	 * and its files as id => internal path; the enumeration answers like the
	 * real one, ordered by id, behind the cursor, at most the band size. A file
	 * id in $tickAfter moves the clock by that many seconds once it was handed
	 * out, which is how a run reaches its wall clock without a sleep.
	 *
	 * @param list<array{mount: array{storage_id: int, root_id: int, overridden_root: int}, root: string, files: array<int, string>}> $mounts
	 * @param array<int, int> $tickAfter
	 */
	private function storage(array $mounts, array $tickAfter = []): StorageService&MockObject {
		$storage = $this->createMock(StorageService::class);
		$storage->method('getMounts')->willReturn(array_map(static fn (array $m): array => $m['mount'], $mounts));
		$storage->method('mountRootPath')->willReturnCallback(
			static function (int $storageId, int $overriddenRoot) use ($mounts): string {
				foreach ($mounts as $m) {
					if ($m['mount']['storage_id'] === $storageId && $m['mount']['overridden_root'] === $overriddenRoot) {
						return $m['root'];
					}
				}

				return '';
			},
		);
		$storage->method('getFilesInMount')->willReturnCallback(
			function (int $storageId, int $overriddenRoot, int $lastFileId, int $batchSize) use ($mounts, $tickAfter): \Generator {
				$this->bands[] = [$storageId, $overriddenRoot, $lastFileId, $batchSize];
				foreach ($mounts as $m) {
					if ($m['mount']['storage_id'] !== $storageId || $m['mount']['overridden_root'] !== $overriddenRoot) {
						continue;
					}
					$files = $m['files'];
					ksort($files);
					$handed = 0;
					foreach ($files as $id => $path) {
						if ($id <= $lastFileId || $handed >= $batchSize) {
							continue;
						}
						$handed++;
						yield $this->entry($id, $path);
						$this->now += $tickAfter[$id] ?? 0;
					}
				}
			},
		);

		return $storage;
	}

	private function job(ExclusionService $exclusions, StorageService $storage): ExclusionSweepJob {
		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturnCallback(fn (): int => $this->now);

		$jobList = $this->createMock(IJobList::class);
		$jobList->method('scheduleAfter')->willReturnCallback(
			function (string $class, int $runAfter, mixed $argument = null): void {
				$this->scheduled[] = [$class, $runAfter, $argument];
			},
		);

		$queue = $this->createMock(QueueService::class);
		$queue->method('enqueueFile')->willReturnCallback(
			function (int $fileId, int $storageId, int $rootId, int $size, bool $isUpdate, string $kind = QueueMapper::KIND_CONTENT): void {
				$this->enqueued[] = [$fileId, $storageId, $rootId, $size, $isUpdate, $kind];
			},
		);

		$fileState = $this->createMock(FileStateService::class);
		$fileState->method('forgetVerdicts')->willReturnCallback(
			function (array $fileIds): int {
				$this->forgotten[] = array_values($fileIds);

				return count($fileIds);
			},
		);

		$logger = $this->createMock(LoggerInterface::class);
		foreach (['emergency', 'alert', 'critical', 'error', 'warning', 'notice', 'info', 'debug'] as $level) {
			$logger->method($level)->willReturnCallback(
				function (string|\Stringable $message, array $context = []) use ($level): void {
					$this->logLines[] = ['level' => $level, 'message' => (string)$message, 'context' => $context];
				},
			);
		}

		return new ExclusionSweepJob(
			$time,
			$jobList,
			$storage,
			$exclusions,
			$queue,
			$fileState,
			$this->createMock(IAppConfig::class),
			$this->createMock(IDBConnection::class),
			$logger,
		);
	}

	/** @param array<string, mixed> $argument */
	private function runJob(ExclusionSweepJob $job, array $argument): void {
		$run = new \ReflectionMethod($job, 'run');
		$run->invoke($job, $argument);
	}

	/**
	 * The home and the Team Folder of the class docblock. The Team Folder comes
	 * first in the answer of getMounts on purpose: the sweep orders the mounts
	 * itself, by storage id.
	 *
	 * @return list<array{mount: array{storage_id: int, root_id: int, overridden_root: int}, root: string, files: array<int, string>}>
	 */
	private static function twoMounts(): array {
		return [
			[
				'mount' => self::TEAM,
				'root' => '__groupfolders/1',
				'files' => [
					201 => '__groupfolders/1/AG/2024/X.key/b.txt',
					202 => '__groupfolders/1/AG/2024/Bericht.pdf',
				],
			],
			[
				'mount' => self::HOME,
				'root' => 'files',
				'files' => [
					101 => 'files/Vortrag.key/Data/a.jpg',
					102 => 'files/Kontrolle.pdf',
					103 => 'files/Vortrag.keynote/c.txt',
				],
			],
		];
	}

	/** @return list<int> every id forgetVerdicts was handed, in order */
	private function forgottenIds(): array {
		return array_merge([], ...$this->forgotten);
	}

	// -- the sweep -----------------------------------------------------------

	public function testExactlyTheTwoFilesUnderThePatternAreClearedAndForgotten(): void {
		$exclusions = $this->exclusions(['*.key']);
		$job = $this->job($exclusions, $this->storage(self::twoMounts()));

		$this->runJob($job, ExclusionSweepJob::startArgument($exclusions->patternFingerprint()));

		self::assertSame(
			[
				[101, 3, 12, 0, true, QueueMapper::KIND_DELETE],
				[201, 9, 40, 0, true, QueueMapper::KIND_DELETE],
			],
			$this->enqueued,
			'a delete row for the bundle file of the home and the one of the Team Folder, nothing else',
		);
		self::assertSame([101, 201], $this->forgottenIds());
		// Both mounts are behind the cursor: the sweep is done.
		self::assertSame([], $this->scheduled);
	}

	public function testTheControlAndTheKeynoteCounterCaseAreNeitherQueuedNorForgotten(): void {
		$exclusions = $this->exclusions(['*.key']);
		$job = $this->job($exclusions, $this->storage(self::twoMounts()));

		$this->runJob($job, ExclusionSweepJob::startArgument($exclusions->patternFingerprint()));

		$queued = array_column($this->enqueued, 0);
		foreach ([102, 103, 202] as $untouched) {
			self::assertNotContains($untouched, $queued);
			self::assertNotContains($untouched, $this->forgottenIds());
		}
	}

	public function testAFullBandPlansTheSuccessorAtItsCursorAndTheLastBandEndsTheChain(): void {
		$files = [];
		for ($id = 1; $id <= ExclusionSweepJob::BATCH_SIZE + 5; $id++) {
			$files[$id] = 'files/doc-' . $id . '.pdf';
		}
		$files[ExclusionSweepJob::BATCH_SIZE + 3] = 'files/Vortrag.key/late.jpg';
		$exclusions = $this->exclusions(['*.key']);
		$fingerprint = $exclusions->patternFingerprint();
		$storage = $this->storage([['mount' => self::HOME, 'root' => 'files', 'files' => $files]]);

		$this->runJob($this->job($exclusions, $storage), ExclusionSweepJob::startArgument($fingerprint));

		self::assertSame([], $this->enqueued, 'the hit lies behind the first band');
		self::assertCount(1, $this->scheduled);
		self::assertSame(ExclusionSweepJob::class, $this->scheduled[0][0]);
		self::assertSame(self::NOW + ExclusionSweepJob::INTERVAL, $this->scheduled[0][1]);
		self::assertSame(
			['storage' => 3, 'root' => 12, 'cursor' => ExclusionSweepJob::BATCH_SIZE, 'fingerprint' => $fingerprint],
			$this->scheduled[0][2],
		);

		// The successor, run with exactly the argument the first run planned.
		$successor = $this->scheduled[0][2];
		self::assertIsArray($successor);
		$this->scheduled = [];
		$this->runJob($this->job($exclusions, $storage), $successor);

		self::assertSame([3, 12, ExclusionSweepJob::BATCH_SIZE, ExclusionSweepJob::BATCH_SIZE], $this->bands[1]);
		self::assertSame([ExclusionSweepJob::BATCH_SIZE + 3], array_column($this->enqueued, 0));
		self::assertSame([ExclusionSweepJob::BATCH_SIZE + 3], $this->forgottenIds());
		self::assertSame([], $this->scheduled, 'the rest of the last mount is empty, so the chain ends');
	}

	public function testTheWallClockPlansTheSuccessorWhereTheRunStood(): void {
		$exclusions = $this->exclusions(['*.key']);
		$fingerprint = $exclusions->patternFingerprint();
		// The clock reaches the ceiling right after the first file was handed out.
		$storage = $this->storage(self::twoMounts(), [101 => ExclusionSweepJob::MAX_SECONDS]);

		$this->runJob($this->job($exclusions, $storage), ExclusionSweepJob::startArgument($fingerprint));

		self::assertSame([101], array_column($this->enqueued, 0), 'the file before the ceiling is cleared');
		self::assertSame([101], $this->forgottenIds());
		self::assertCount(1, $this->scheduled);
		self::assertSame(self::NOW + ExclusionSweepJob::MAX_SECONDS + ExclusionSweepJob::INTERVAL, $this->scheduled[0][1]);
		self::assertSame(
			['storage' => 3, 'root' => 12, 'cursor' => 101, 'fingerprint' => $fingerprint],
			$this->scheduled[0][2],
		);
	}

	public function testARunForAnEarlierPatternSetClearsNothingAndPlansNothing(): void {
		// PE-10. The run was planned for *.key alone; *.app has been added since,
		// and the set in force has its own run from the start.
		$storage = $this->storage(self::twoMounts());
		$storage->expects($this->never())->method('getMounts');

		$this->runJob(
			$this->job($this->exclusions(['*.key', '*.app']), $storage),
			ExclusionSweepJob::startArgument($this->fingerprintOf(['*.key'])),
		);

		self::assertSame([], $this->enqueued);
		self::assertSame([], $this->forgotten);
		self::assertSame([], $this->scheduled);
	}

	public function testTheSameRunWithTheFingerprintInForceClears(): void {
		// The positive control of the case above: same files, same set in
		// force, the fingerprint of that set.
		$exclusions = $this->exclusions(['*.key', '*.app']);

		$this->runJob(
			$this->job($exclusions, $this->storage(self::twoMounts())),
			ExclusionSweepJob::startArgument($this->fingerprintOf(['*.key', '*.app'])),
		);

		self::assertSame([101, 201], array_column($this->enqueued, 0));
		self::assertSame([101, 201], $this->forgottenIds());
	}

	public function testTheFingerprintIsSha256OverTheSortedNormalisedSet(): void {
		// Worked out here by hand and not through the service, so the definition
		// is held and not only its agreement with itself.
		self::assertSame(hash('sha256', "*.app\n*.key"), $this->fingerprintOf(['*.key', '*.app']));
		self::assertSame(hash('sha256', "*.app\n*.key"), $this->fingerprintOf(['/files/*.app/', '*.key']));
		self::assertNotSame($this->fingerprintOf(['*.key']), $this->fingerprintOf(['*.key', '*.app']));
	}

	public function testWithoutAnyRuleTheJobEndsAtOnce(): void {
		$storage = $this->storage(self::twoMounts());
		$storage->expects($this->never())->method('getMounts');
		$storage->expects($this->never())->method('getFilesInMount');

		$this->runJob(
			$this->job($this->exclusions([]), $storage),
			ExclusionSweepJob::startArgument($this->fingerprintOf([])),
		);

		self::assertSame([], $this->enqueued);
		self::assertSame([], $this->forgotten);
		self::assertSame([], $this->scheduled);
	}

	public function testTheLogCarriesCountersStorageAndCursorAndNothingElse(): void {
		$exclusions = $this->exclusions(['*.key']);
		$fingerprint = $exclusions->patternFingerprint();

		// A run that clears, a run cut by the clock and a stale run, so every
		// log line of the job is written at least once.
		$this->runJob($this->job($exclusions, $this->storage(self::twoMounts())), ExclusionSweepJob::startArgument($fingerprint));
		$this->runJob(
			$this->job($exclusions, $this->storage(self::twoMounts(), [101 => ExclusionSweepJob::MAX_SECONDS])),
			ExclusionSweepJob::startArgument($fingerprint),
		);
		$this->runJob(
			$this->job($exclusions, $this->storage(self::twoMounts())),
			ExclusionSweepJob::startArgument($this->fingerprintOf(['*.app'])),
		);

		self::assertNotSame([], $this->logLines);
		foreach ($this->logLines as $line) {
			self::assertStringNotContainsString('.key', $line['message']);
			self::assertStringNotContainsString($fingerprint, $line['message']);
			foreach ($line['context'] as $key => $value) {
				self::assertContains($key, ['storage', 'cursor', 'cleared', 'seen']);
				self::assertIsInt($value, 'a log value is a number and never a path, a pattern or a fingerprint');
			}
		}
	}

	// -- the planning in savePatterns ---------------------------------------

	/**
	 * A service over a stored pattern list and a job list that records what
	 * savePatterns() does to it, in order.
	 *
	 * @param list<string> $stored
	 */
	private function planner(array $stored): ExclusionService {
		$jobList = $this->createMock(IJobList::class);
		$jobList->method('remove')->willReturnCallback(
			function (mixed $job, mixed $argument = null): void {
				$this->jobCalls[] = ['remove', is_string($job) ? $job : get_class($job), $argument];
			},
		);
		$jobList->method('add')->willReturnCallback(
			function (mixed $job, mixed $argument = null): void {
				$this->jobCalls[] = ['add', is_string($job) ? $job : get_class($job), $argument];
			},
		);
		$jobList->method('scheduleAfter')->willReturnCallback(
			function (string $job, int $runAfter, mixed $argument = null): void {
				$this->jobCalls[] = ['scheduleAfter', $job, $argument];
			},
		);

		return $this->exclusions($stored, [], $jobList);
	}

	public function testAFirstPatternPlansOneSweepFromTheStartAfterRemovingAnyOther(): void {
		self::assertSame([], $this->planner([])->savePatterns(['*.key']));

		self::assertSame(
			[
				['remove', ExclusionSweepJob::class, null],
				['add', ExclusionSweepJob::class, ['storage' => 0, 'root' => 0, 'cursor' => 0, 'fingerprint' => hash('sha256', '*.key')]],
			],
			$this->jobCalls,
		);
	}

	public function testRemovingAPatternReplacesThePlannedRunByOneFromTheStart(): void {
		// N3. Only a removal: *.app goes, *.key stays. The planned run of the
		// old set is removed and exactly one run of the new set is planned from
		// the start, with the fingerprint of *.key alone.
		self::assertSame([], $this->planner(['*.key', '*.app'])->savePatterns(['*.key']));

		self::assertSame(
			[
				['remove', ExclusionSweepJob::class, null],
				['add', ExclusionSweepJob::class, ExclusionSweepJob::startArgument($this->fingerprintOf(['*.key']))],
			],
			$this->jobCalls,
		);

		// The old run, had it been under way, ends at its fingerprint against
		// the set in force now and plans no successor.
		$this->runJob(
			$this->job($this->exclusions(['*.key']), $this->storage(self::twoMounts())),
			['storage' => 3, 'root' => 12, 'cursor' => 101, 'fingerprint' => $this->fingerprintOf(['*.key', '*.app'])],
		);
		self::assertSame([], $this->enqueued);
		self::assertSame([], $this->scheduled);
	}

	public function testAnEmptySetRemovesTheSweepAndPlansNone(): void {
		self::assertSame([], $this->planner(['*.key'])->savePatterns([]));

		self::assertSame([['remove', ExclusionSweepJob::class, null]], $this->jobCalls);
	}

	public function testAnUnchangedSetInAnotherOrderAndSpellingPlansNothing(): void {
		self::assertSame([], $this->planner(['*.key', '*.app'])->savePatterns(['*.app', '/files/*.key/']));

		self::assertSame([], $this->jobCalls);
	}

	public function testARefusedSetPlansNothing(): void {
		self::assertSame([ExclusionService::ERROR_DOUBLE_STAR], $this->planner(['*.key'])->savePatterns(['**.key']));

		self::assertSame([], $this->jobCalls);
	}
}
