<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\BackgroundJobs\SubtreeExpandJob;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\Files\Cache\ICacheEntry;
use OCP\IAppConfig;
use OCP\IDBConnection;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The verdicts of a cleared subtree (plan 33-04, finding B2, owner answer G4).
 *
 * The clearing of a new prefix is this job with kind delete. Until plan 33-04
 * it queued a delete row per file and left the verdict rows of those files in
 * findling_file_state, so the tiles and the error list went on counting files
 * the rule had taken out of the index. The two cases below hold the fix and its
 * boundary: a band of kind delete forgets exactly the verdicts of that band,
 * and a band of any other kind forgets nothing.
 */
#[CoversClass(SubtreeExpandJob::class)]
final class SubtreeExpandJobTest extends TestCase {
	private const NOW = 1757600000;

	/** @var list<list<int>> every forgetVerdicts call */
	private array $forgotten = [];

	/** @var list<array{int, string}> every enqueueFile call: file id and kind */
	private array $enqueued = [];

	private function entry(int $id): ICacheEntry&MockObject {
		$entry = $this->createMock(ICacheEntry::class);
		$entry->method('getId')->willReturn($id);
		$entry->method('getSize')->willReturn(1000);

		return $entry;
	}

	private function job(): SubtreeExpandJob {
		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturn(self::NOW);

		$storage = $this->createMock(StorageService::class);
		$storage->method('getFilesInMount')->willReturn([$this->entry(501), $this->entry(502), $this->entry(503)]);

		$queue = $this->createMock(QueueService::class);
		$queue->method('enqueueFile')->willReturnCallback(
			function (int $fileId, int $storageId, int $rootId, int $size, bool $isUpdate, string $kind = QueueMapper::KIND_CONTENT): void {
				$this->enqueued[] = [$fileId, $kind];
			},
		);

		$fileState = $this->createMock(FileStateService::class);
		$fileState->method('forgetVerdicts')->willReturnCallback(
			function (array $fileIds): int {
				$this->forgotten[] = array_values($fileIds);

				return count($fileIds);
			},
		);

		return new SubtreeExpandJob(
			$time,
			$this->createMock(IJobList::class),
			$storage,
			$queue,
			$fileState,
			$this->createMock(IAppConfig::class),
			$this->createMock(IDBConnection::class),
			$this->createMock(LoggerInterface::class),
		);
	}

	private function runJob(SubtreeExpandJob $job, string $kind): void {
		$run = new \ReflectionMethod($job, 'run');
		$run->invoke($job, [
			'storage_id' => 3,
			'root_id' => 12,
			'ancestor_id' => 77,
			'kind' => $kind,
			'last_file_id' => 0,
		]);
	}

	public function testABandOfKindDeleteForgetsExactlyTheVerdictsOfThatBand(): void {
		$this->runJob($this->job(), QueueMapper::KIND_DELETE);

		self::assertSame([501, 502, 503], array_column($this->enqueued, 0));
		self::assertSame([[501, 502, 503]], $this->forgotten);
	}

	/** @return array<string, array{string}> */
	public static function kindsThatKeepTheVerdicts(): array {
		return [
			'content' => [QueueMapper::KIND_CONTENT],
			'acl' => [QueueMapper::KIND_ACL],
		];
	}

	#[DataProvider('kindsThatKeepTheVerdicts')]
	public function testABandOfAnotherKindForgetsNothing(string $kind): void {
		$this->runJob($this->job(), $kind);

		// The band was queued, so the job ran through, and nothing was forgotten.
		self::assertSame([501, 502, 503], array_column($this->enqueued, 0));
		self::assertSame([$kind, $kind, $kind], array_column($this->enqueued, 1));
		self::assertSame([], $this->forgotten);
	}
}
