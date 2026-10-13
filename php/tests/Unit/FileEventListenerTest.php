<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Listener\FileEventListener;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\Files\Events\Node\NodeDeletedEvent;
use OCP\Files\Events\Node\NodeWrittenEvent;
use OCP\Files\File;
use OCP\Files\Mount\IMountPoint;
use OCP\IAppConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The exclusion branch of the event listener on an instance with patterns only.
 *
 * Pitfall 1 of the phase 33 research in one sentence: the listener used to skip
 * its exclusion question whenever the prefix list was empty, so on an instance
 * whose only rule is a pattern every save inside a Keynote bundle queued the
 * file again, right after the crawl had left it alone. The guard asks
 * ExclusionService::hasRules() since plan 33-02, and these cases hold the
 * answer: a written file under the pattern is not queued, a control file next
 * to it is, and a deletion under the pattern still goes through, because an
 * excluded file that is deleted has to leave the index.
 *
 * ExclusionService and SettingsService are final and are built for real over
 * a mocked app config that answers per key; the queue, the storage service, the
 * state table and the job list are doubles. The storage root of the mount has
 * the empty internal path, which is what the listener hands in for a home, so
 * the ``files`` vanguard is the part mountRelativePath() strips.
 */
#[CoversClass(FileEventListener::class)]
final class FileEventListenerTest extends TestCase {
	private const STORAGE_ID = 3;
	private const ROOT_ID = 5;

	private QueueService&MockObject $queueService;
	private StorageService&MockObject $storageService;
	private LoggerInterface&MockObject $logger;

	/**
	 * Every enqueue the listener asked for, as file id and kind.
	 *
	 * @var list<array{int, string}>
	 */
	private array $enqueued = [];

	protected function setUp(): void {
		parent::setUp();

		$this->enqueued = [];
		$this->queueService = $this->createMock(QueueService::class);
		$this->queueService->method('enqueueFile')->willReturnCallback(
			function (int $fileId, int $storageId, int $rootId, int $size, bool $isUpdate, string $kind = QueueMapper::KIND_CONTENT): void {
				$this->enqueued[] = [$fileId, $kind];
			},
		);

		$this->storageService = $this->createMock(StorageService::class);
		$this->storageService->method('isIndexedStorage')->willReturn(true);
		$this->storageService->method('mountRootPath')->willReturn('');

		// A failure inside handle() is caught and logged as a warning, which
		// would make "not queued" pass for the wrong reason. No case below may
		// see one.
		$this->logger = $this->createMock(LoggerInterface::class);
		$this->logger->expects(self::never())->method('warning');
		$this->logger->expects(self::never())->method('error');
	}

	/**
	 * @param list<string> $prefixes
	 * @param list<string> $patterns
	 */
	private function listener(array $prefixes, array $patterns): FileEventListener {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueArray')->willReturnCallback(
			static fn (string $app, string $key, array $default = []): array => match ($key) {
				SettingsService::KEY_EXCLUSIONS => $prefixes,
				SettingsService::KEY_EXCLUSION_PATTERNS => $patterns,
				default => $default,
			},
		);
		$appConfig->method('getValueInt')->willReturnCallback(
			static fn (string $app, string $key, int $default = 0): int => $default,
		);

		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturn(1_700_000_000);
		$jobList = $this->createMock(IJobList::class);

		return new FileEventListener(
			$this->queueService,
			$this->storageService,
			$this->createMock(FileStateService::class),
			new SettingsService($appConfig, $this->logger, $time),
			new ExclusionService($appConfig, $this->storageService, $jobList, $this->logger),
			$jobList,
			$this->logger,
		);
	}

	private function file(int $fileId, string $internalPath): File&MockObject {
		$mount = $this->createMock(IMountPoint::class);
		$mount->method('getNumericStorageId')->willReturn(self::STORAGE_ID);
		$mount->method('getStorageRootId')->willReturn(self::ROOT_ID);

		$file = $this->createMock(File::class);
		$file->method('getId')->willReturn($fileId);
		$file->method('getMimetype')->willReturn('application/pdf');
		$file->method('getMountPoint')->willReturn($mount);
		$file->method('getSize')->willReturn(1024);
		$file->method('getInternalPath')->willReturn($internalPath);

		return $file;
	}

	public function testWithPatternsOnlyAWrittenFileUnderAPatternIsNotQueued(): void {
		$listener = $this->listener([], ['*.key']);

		$listener->handle(new NodeWrittenEvent($this->file(41, 'files/Vortrag.key/Data/notes.pdf')));

		self::assertSame([], $this->enqueued);
	}

	public function testWithPatternsOnlyAControlFileNextToItIsQueued(): void {
		// The positive control of the case above: same listener, same rule, a
		// file the pattern does not name, and it reaches the queue.
		$listener = $this->listener([], ['*.key']);

		$listener->handle(new NodeWrittenEvent($this->file(42, 'files/Vortraege/notes.pdf')));

		self::assertSame([[42, QueueMapper::KIND_CONTENT]], $this->enqueued);
	}

	public function testWithPatternsOnlyADeletionUnderAPatternStillGoesThrough(): void {
		$listener = $this->listener([], ['*.key']);

		$listener->handle(new NodeDeletedEvent($this->file(43, 'files/Vortrag.key/Data/notes.pdf')));

		self::assertSame([[43, QueueMapper::KIND_DELETE]], $this->enqueued);
	}

	public function testWithoutAnyRuleTheRootIsNotLookedUp(): void {
		// The other half of the guard: an instance without rules pays nothing
		// for the exclusion question, which is why the guard exists.
		$this->storageService->expects(self::never())->method('mountRootPath');
		$listener = $this->listener([], []);

		$listener->handle(new NodeWrittenEvent($this->file(44, 'files/Vortrag.key/Data/notes.pdf')));

		self::assertSame([[44, QueueMapper::KIND_CONTENT]], $this->enqueued);
	}

	public function testAPrefixStillLeavesAWrittenFileAlone(): void {
		$listener = $this->listener(['Archiv'], []);

		$listener->handle(new NodeWrittenEvent($this->file(45, 'files/Archiv/2024/notes.pdf')));

		self::assertSame([], $this->enqueued);
	}
}
