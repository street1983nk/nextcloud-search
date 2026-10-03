<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Controller\ReconcileController;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Http;
use OCP\BackgroundJob\IJobList;
use OCP\IAppConfig;
use OCP\IRequest;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The excluded mark of the file slice (owner decision of 03.10.2026, part a).
 *
 * Run 7 of the 28-07 chain found 549 files under excluded folders handed to the
 * content track every ~300 s: the slice carried them without any mark, the
 * container knew no etag for them, describe() answered the claim with a delete
 * order and the next quiet round found them unknown again. The slice now marks
 * such a row live as skipped(excluded), and this suite holds the answer: no mark
 * without a rule, a mark only on the rows a rule matches, the row stays on the
 * page, the mark outranks a stored verdict, and the wire keeps its seven fields.
 *
 * ExclusionService is final and is built for real over a mocked app config, the
 * same way QueueServiceTest and StorageCrawlJobTest build it. StorageService is
 * mocked; its getFileSlice calls the predicate it was handed with invented
 * internal paths, which is what the real one does with the path of each cache
 * entry.
 */
#[CoversClass(ReconcileController::class)]
final class ReconcileControllerTest extends TestCase {
	private const STORAGE = 3;
	private const ROOT = 17;

	/** The seven fields of the wire, in the order the answer carries them. */
	private const WIRE_FIELDS = ['fileId', 'etag', 'size', 'mtime', 'mime', 'state', 'reason'];

	private StorageService&MockObject $storageService;
	private FileStateService&MockObject $fileStateService;

	protected function setUp(): void {
		parent::setUp();

		$this->storageService = $this->createMock(StorageService::class);
		$this->storageService->method('mountRootPath')->willReturn('files');
		$this->fileStateService = $this->createMock(FileStateService::class);
	}

	/**
	 * The app id of the container, read out of the class instead of copied,
	 * for the same reason as in QueueControllerTest.
	 */
	private function backendAppId(): string {
		$value = (new \ReflectionClass(Application::class))->getConstant('BACKEND_APP_ID');

		self::assertIsString($value, 'BACKEND_APP_ID is gone or is no longer a string');

		return $value;
	}

	/**
	 * @param list<string> $prefixes
	 */
	private function controller(array $prefixes): ReconcileController {
		$request = $this->createMock(IRequest::class);
		$callerAppId = $this->backendAppId();
		$request->method('getHeader')->willReturnCallback(
			static fn (string $name): string => $name === 'EX-APP-ID' ? $callerAppId : '',
		);

		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueArray')->willReturnCallback(
			static fn (string $app, string $key, array $default = []): array => $key === SettingsService::KEY_EXCLUSIONS ? $prefixes : $default,
		);
		$logger = $this->createMock(LoggerInterface::class);

		return new ReconcileController(
			$request,
			$this->storageService,
			$this->fileStateService,
			new ExclusionService($appConfig, $this->storageService, $this->createMock(IJobList::class), $logger),
			$logger,
		);
	}

	/**
	 * A slice of two files, one below files/loadtest and one below
	 * files/teilkorpus, with the predicate applied the way the real
	 * StorageService applies it.
	 */
	private function sliceOfTwo(): void {
		$paths = [1 => 'files/loadtest/x.pdf', 2 => 'files/teilkorpus/y.pdf'];
		$this->storageService->method('getFileSlice')->willReturnCallback(
			static function (int $storage, int $root, int $after, int $limit, ?\Closure $isExcludedPath = null) use ($paths): array {
				$rows = [];
				foreach ($paths as $fileId => $path) {
					$row = [
						'fileId' => $fileId,
						'etag' => 'etag-' . $fileId,
						'size' => 1024,
						'mtime' => 1700000000,
						'mime' => 'application/pdf',
					];
					if ($isExcludedPath !== null) {
						$row['excluded'] = $isExcludedPath($path);
					}
					$rows[] = $row;
				}
				return $rows;
			},
		);
	}

	/**
	 * @return list<array<string, mixed>>
	 */
	private function filesOf(ReconcileController $controller, int $limit = 500): array {
		$response = $controller->filesSlice(self::STORAGE, self::ROOT, 0, $limit);
		self::assertSame(Http::STATUS_OK, $response->getStatus());

		$data = $response->getData();
		self::assertIsArray($data);
		self::assertIsArray($data['files']);

		/** @var list<array<string, mixed>> */
		return $data['files'];
	}

	public function testWithoutPrefixesNoRowCarriesTheExcludedMark(): void {
		$this->sliceOfTwo();
		$this->fileStateService->method('verdictsFor')->willReturn([]);

		$files = $this->filesOf($this->controller([]));

		self::assertCount(2, $files);
		foreach ($files as $row) {
			self::assertSame('', $row['state']);
			self::assertSame('', $row['reason']);
		}
	}

	public function testOnlyTheRowsARuleMatchesCarryTheExcludedMark(): void {
		$this->sliceOfTwo();
		$this->fileStateService->method('verdictsFor')->willReturn([]);

		$files = $this->filesOf($this->controller(['loadtest']));

		self::assertSame(1, $files[0]['fileId']);
		self::assertSame(['skipped', 'excluded'], [$files[0]['state'], $files[0]['reason']]);
		self::assertSame(2, $files[1]['fileId']);
		self::assertSame(['', ''], [$files[1]['state'], $files[1]['reason']]);
	}

	public function testTheExcludedRowStaysOnThePageAndTheFinalMarkIsUnchanged(): void {
		// A filtered page would read as final, and a final page drops the upper
		// bound of the deletion rule in the container: the row has to stay.
		$this->sliceOfTwo();
		$this->fileStateService->method('verdictsFor')->willReturn([]);

		$response = $this->controller(['loadtest'])->filesSlice(self::STORAGE, self::ROOT, 0, 2);
		$data = $response->getData();

		self::assertIsArray($data);
		self::assertIsArray($data['files']);
		self::assertCount(2, $data['files']);
		self::assertFalse($data['final']);
	}

	public function testTheExcludedMarkOutranksAStoredVerdict(): void {
		$this->sliceOfTwo();
		$this->fileStateService->method('verdictsFor')->willReturn([
			1 => ['state' => 'failed', 'reason' => 'repeatedly_stuck'],
			2 => ['state' => 'failed', 'reason' => 'corrupt'],
		]);

		$files = $this->filesOf($this->controller(['loadtest']));

		self::assertSame(['skipped', 'excluded'], [$files[0]['state'], $files[0]['reason']]);
		self::assertSame(['failed', 'corrupt'], [$files[1]['state'], $files[1]['reason']]);
	}

	public function testTheAnswerCarriesTheSevenWireFieldsAndNoFlag(): void {
		// T-wxg-01: the flag is a detail of this side and never leaves it.
		$this->sliceOfTwo();
		$this->fileStateService->method('verdictsFor')->willReturn([]);

		foreach ($this->filesOf($this->controller(['loadtest'])) as $row) {
			self::assertSame(self::WIRE_FIELDS, array_keys($row));
		}
	}
}
