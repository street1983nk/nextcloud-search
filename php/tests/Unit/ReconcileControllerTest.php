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
 *
 * Since plan 36-03 the suite also holds the storage question at its boundary:
 * a foreign caller never reaches it, a malformed list is refused without its
 * values in the log, a valid list is answered out of the service, and a
 * failing lookup answers with a static sentence.
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
	 * @param list<string> $patterns
	 */
	private function controller(array $prefixes, array $patterns = []): ReconcileController {
		$request = $this->createMock(IRequest::class);
		$callerAppId = $this->backendAppId();
		$request->method('getHeader')->willReturnCallback(
			static fn (string $name): string => $name === 'EX-APP-ID' ? $callerAppId : '',
		);

		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueArray')->willReturnCallback(
			static fn (string $app, string $key, array $default = []): array => match ($key) {
				SettingsService::KEY_EXCLUSIONS => $prefixes,
				SettingsService::KEY_EXCLUSION_PATTERNS => $patterns,
				default => $default,
			},
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

	public function testWithPatternsOnlyTheRowAPatternMatchesCarriesTheExcludedMark(): void {
		// Pitfall 1 of the phase 33 research at the slice: the predicate used to
		// be null whenever the prefix list was empty, so an instance whose only
		// rule is a pattern marked nothing. No prefix is stored here.
		$this->sliceOfTwo();
		$this->fileStateService->method('verdictsFor')->willReturn([]);

		$files = $this->filesOf($this->controller([], ['load*']));

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

	// -- the verdicts of excluded rows (plan 33-04, PE-9) ---------------------

	public function testTheVerdictOfAnExcludedRowIsForgottenAndTheControlKeepsItsOwn(): void {
		// The slice knows nothing about the container, so this is also the case
		// of a file the container never held as a living row: describe() never
		// sees such a file, and the slice is where its verdict goes.
		$this->sliceOfTwo();
		$this->fileStateService->method('verdictsFor')->willReturn([
			1 => ['state' => 'skipped', 'reason' => 'image_not_ocrable'],
			2 => ['state' => 'failed', 'reason' => 'corrupt'],
		]);
		$forgotten = [];
		$this->fileStateService->expects($this->once())->method('forgetVerdicts')->willReturnCallback(
			function (array $fileIds) use (&$forgotten): int {
				$forgotten[] = array_values($fileIds);

				return count($fileIds);
			},
		);

		$response = $this->controller(['loadtest'])->filesSlice(self::STORAGE, self::ROOT, 0, 2);
		$data = $response->getData();

		self::assertSame([[1]], $forgotten, 'the excluded row loses its verdict, the control does not');
		self::assertIsArray($data);
		self::assertIsArray($data['files']);
		self::assertSame(['skipped', 'excluded'], [$data['files'][0]['state'], $data['files'][0]['reason']]);
		self::assertSame(['failed', 'corrupt'], [$data['files'][1]['state'], $data['files'][1]['reason']]);
		self::assertFalse($data['final']);
	}

	public function testAnExcludedRowWithoutAStoredVerdictCostsNoWrite(): void {
		$this->sliceOfTwo();
		$this->fileStateService->method('verdictsFor')->willReturn([
			2 => ['state' => 'failed', 'reason' => 'corrupt'],
		]);
		$this->fileStateService->expects($this->never())->method('forgetVerdicts');

		$files = $this->filesOf($this->controller(['loadtest']));

		self::assertSame(['skipped', 'excluded'], [$files[0]['state'], $files[0]['reason']]);
	}

	public function testWithoutARuleNoVerdictIsForgotten(): void {
		$this->sliceOfTwo();
		$this->fileStateService->method('verdictsFor')->willReturn([
			1 => ['state' => 'skipped', 'reason' => 'image_not_ocrable'],
		]);
		$this->fileStateService->expects($this->never())->method('forgetVerdicts');

		$files = $this->filesOf($this->controller([]));

		self::assertSame(['skipped', 'image_not_ocrable'], [$files[0]['state'], $files[0]['reason']]);
	}

	public function testAFailingCleanupStillAnswersTheSliceUnchanged(): void {
		// The cleanup is retried on the next round; a reconcile that stopped
		// over it would stop the repair it exists for.
		$this->sliceOfTwo();
		$this->fileStateService->method('verdictsFor')->willReturn([
			1 => ['state' => 'skipped', 'reason' => 'image_not_ocrable'],
		]);
		$this->fileStateService->method('forgetVerdicts')->willThrowException(new \RuntimeException('database gone'));

		$files = $this->filesOf($this->controller(['loadtest']));

		self::assertCount(2, $files);
		self::assertSame(['skipped', 'excluded'], [$files[0]['state'], $files[0]['reason']]);
		self::assertSame(['', ''], [$files[1]['state'], $files[1]['reason']]);
	}

	// -- the storage question of plan 36-03 (D-36-14, M-32-02, T-36-09 to T-36-12) --

	/** Every log call of the storage controller, as level, message and context. @var list<array{string, string, array<mixed>}> */
	private array $logged = [];

	/**
	 * A controller whose request carries the given caller and the given ids
	 * parameter, and whose logger records everything it is handed.
	 */
	private function storageController(string $callerAppId, mixed $ids): ReconcileController {
		$request = $this->createMock(IRequest::class);
		$request->method('getHeader')->willReturnCallback(
			static fn (string $name): string => $name === 'EX-APP-ID' ? $callerAppId : '',
		);
		$request->method('getParam')->willReturnCallback(
			static fn (string $key, mixed $default = null): mixed => $key === 'ids' ? $ids : $default,
		);

		$logger = $this->createMock(LoggerInterface::class);
		foreach (['debug', 'info', 'notice', 'warning', 'error'] as $level) {
			$logger->method($level)->willReturnCallback(
				function (string|\Stringable $message, array $context = []) use ($level): void {
					$this->logged[] = [$level, (string)$message, $context];
				},
			);
		}

		return new ReconcileController(
			$request,
			$this->storageService,
			$this->fileStateService,
			new ExclusionService($this->createMock(IAppConfig::class), $this->storageService, $this->createMock(IJobList::class), $logger),
			$logger,
		);
	}

	public function testAForeignCallerNeverReachesTheStorageQuestion(): void {
		$this->storageService->expects($this->never())->method('classifyAbsent');

		$response = $this->storageController('some_other_exapp', ['9'])->goneStorages();

		self::assertSame(Http::STATUS_FORBIDDEN, $response->getStatus());
		self::assertSame(['error' => 'This route is reserved for the Findling backend.'], $response->getData());
	}

	public function testAMalformedStorageListIsRefusedWithoutItsValues(): void {
		$this->storageService->expects($this->never())->method('classifyAbsent');

		$malformed = [
			'too long' => range(900001, 900257),
			'not a number' => ['secretvalue'],
			'negative' => [-4711],
			'nought' => ['0'],
			'a fraction' => [1.5],
			'a nested list' => [['77123']],
			'not a list' => 'secretvalue',
			// L-36-02: digits that do not read back as themselves.
			'past the largest integer' => ['12345678901234567890'],
			'a leading nought' => ['014'],
		];
		foreach ($malformed as $case => $ids) {
			$response = $this->storageController($this->backendAppId(), $ids)->goneStorages();

			self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus(), $case);
			self::assertSame(['error' => 'Storage list is not valid.'], $response->getData(), $case);
		}

		$log = (string)json_encode($this->logged);
		self::assertCount(count($malformed), $this->logged);
		foreach (['secretvalue', '4711', '900001', '900257', '77123'] as $value) {
			self::assertStringNotContainsString($value, $log);
		}
	}

	public function testAValidListIsAnsweredOutOfTheService(): void {
		$this->storageService->expects($this->once())->method('classifyAbsent')
			->with([14, 15, 9])
			->willReturn(['gone' => [14, 15], 'deselected' => [9]]);

		$response = $this->storageController($this->backendAppId(), ['14', 15, 9, '9'])->goneStorages();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['gone' => [14, 15], 'deselected' => [9]], $response->getData());
	}

	public function testAFailingLookupAnswersWithAStaticSentenceAndLogsNoMessage(): void {
		$this->storageService->method('classifyAbsent')
			->willThrowException(new \RuntimeException('SELECT secretcolumn FROM oc_storages'));

		$response = $this->storageController($this->backendAppId(), [9])->goneStorages();

		self::assertSame(Http::STATUS_INTERNAL_SERVER_ERROR, $response->getStatus());
		self::assertSame(['error' => 'Storage state is not available.'], $response->getData());

		$errors = array_values(array_filter($this->logged, static fn (array $entry): bool => $entry[0] === 'error'));
		self::assertCount(1, $errors);
		self::assertSame(['exception'], array_keys($errors[0][2]));
		self::assertStringNotContainsString('secretcolumn', $errors[0][1]);
	}
}
