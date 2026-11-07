<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Controller\ReconcileController;
use OCA\Findling\Service\DocKeyService;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Http;
use OCP\BackgroundJob\IJobList;
use OCP\Files\Cache\ICacheEntry;
use OCP\Files\Cache\IFileAccess;
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
 *
 * Since plan 43-15 the same holds for the document key route, plus the two
 * promises of its answer: every asked id stands in exactly one of keys and
 * absent, and only ids and 64 hex characters travel (W8, T-43-46).
 */
#[CoversClass(ReconcileController::class)]
final class ReconcileControllerTest extends TestCase {
	private const STORAGE = 3;
	private const ROOT = 17;

	/** The seven fields of the wire, in the order the answer carries them. */
	private const WIRE_FIELDS = ['fileId', 'etag', 'size', 'mtime', 'mime', 'state', 'reason'];

	private StorageService&MockObject $storageService;
	private FileStateService&MockObject $fileStateService;
	private DocKeyService&MockObject $docKeyService;

	protected function setUp(): void {
		parent::setUp();

		$this->storageService = $this->createMock(StorageService::class);
		$this->storageService->method('mountRootPath')->willReturn('files');
		$this->fileStateService = $this->createMock(FileStateService::class);
		$this->docKeyService = $this->createMock(DocKeyService::class);
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
			$this->docKeyService,
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
	private function storageController(string $callerAppId, mixed $ids, ?DocKeyService $docKeys = null): ReconcileController {
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
			$docKeys ?? $this->docKeyService,
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

	// -- the document key route of plan 43-15 (D-43-14, W8, T-43-46 to T-43-48) --

	/**
	 * A real DocKeyService over a file cache double: the ids of $paths have an
	 * entry with that internal path, every other id has none.
	 *
	 * @param array<int, string> $paths
	 */
	private function docKeysOver(array $paths): DocKeyService {
		$access = $this->createMock(IFileAccess::class);
		$access->method('getByFileIds')->willReturnCallback(function (array $fileIds) use ($paths): array {
			$found = [];
			foreach ($fileIds as $fileId) {
				if (isset($paths[$fileId])) {
					$entry = $this->createMock(ICacheEntry::class);
					$entry->method('getPath')->willReturn($paths[$fileId]);
					$found[$fileId] = $entry;
				}
			}

			return $found;
		});

		return new DocKeyService($access);
	}

	public function testTheBandIsTwoHundred(): void {
		self::assertSame(200, ReconcileController::DOC_KEY_BAND);
	}

	public function testAForeignCallerNeverReachesTheDocumentKeys(): void {
		$this->docKeyService->expects($this->never())->method('docKeysFor');

		$response = $this->storageController('some_other_exapp', '9')->docKeys();

		self::assertSame(Http::STATUS_FORBIDDEN, $response->getStatus());
		self::assertSame(['error' => 'This route is reserved for the Findling backend.'], $response->getData());
	}

	public function testAMalformedOrTooLongIdListIsRefusedBeforeAnyLookup(): void {
		$this->docKeyService->expects($this->never())->method('docKeysFor');

		$malformed = [
			'missing' => null,
			'empty' => '',
			'one too many as a value' => implode(',', range(900001, 900201)),
			'one too many as a list' => range(900001, 900201),
			'an empty list' => [],
			'not a number' => 'secretvalue',
			'an empty entry' => '12,,13',
			'a space' => '12, 13',
			'a trailing comma' => '12,',
			'negative' => '-4711',
			'nought' => '0',
			'a leading nought' => '014',
			'past the largest integer' => '12345678901234567890',
			'a fraction' => [1.5],
			'a nested list' => [['77123']],
			'a value far too long' => str_repeat('9', 5000),
		];
		foreach ($malformed as $case => $ids) {
			$response = $this->storageController($this->backendAppId(), $ids)->docKeys();

			self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus(), $case);
			self::assertSame(['error' => 'File id list is not valid.'], $response->getData(), $case);
		}

		$log = (string)json_encode($this->logged);
		self::assertCount(count($malformed), $this->logged);
		foreach (['secretvalue', '4711', '900001', '900201', '77123'] as $value) {
			self::assertStringNotContainsString($value, $log);
		}
	}

	public function testExactlyTwoHundredIdsAreAnswered(): void {
		$ids = range(1, 200);
		$this->docKeyService->expects($this->once())->method('docKeysFor')
			->with($ids)
			->willReturn(['keys' => [], 'absent' => $ids]);

		$response = $this->storageController($this->backendAppId(), implode(',', $ids))->docKeys();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame($ids, $response->getData()['absent']);
	}

	public function testTheValueAndTheListFormAreTheSameQuestion(): void {
		$this->docKeyService->expects($this->exactly(2))->method('docKeysFor')
			->with([14, 15, 9])
			->willReturn(['keys' => [14 => str_repeat('a', 64)], 'absent' => [15, 9]]);

		foreach (['14,15,9,9', ['14', 15, 9, '9']] as $ids) {
			$response = $this->storageController($this->backendAppId(), $ids)->docKeys();

			self::assertSame(Http::STATUS_OK, $response->getStatus());
			self::assertSame(['keys' => [14 => str_repeat('a', 64)], 'absent' => [15, 9]], $response->getData());
		}
	}

	public function testEveryAskedIdStandsInExactlyOneListAndOnlyHexTravels(): void {
		$docKeys = $this->docKeysOver([
			11 => 'files/Geheim/Vertrag.pdf',
			12 => 'files_trashbin/files/Geheim.pdf.d1700000000',
			14 => 'Gemeinsam/Plan.xlsx',
		]);

		$response = $this->storageController($this->backendAppId(), '11,12,13,14', $docKeys)->docKeys();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		$data = $response->getData();
		self::assertSame([11, 14], array_keys($data['keys']));
		self::assertSame([12, 13], $data['absent']);

		$all = array_merge(array_keys($data['keys']), $data['absent']);
		sort($all);
		self::assertSame([11, 12, 13, 14], $all);

		foreach ($data['keys'] as $key) {
			self::assertMatchesRegularExpression('/^[0-9a-f]{64}$/D', $key);
		}
		self::assertSame(DocKeyService::docKeyOf('Gemeinsam/Plan.xlsx'), $data['keys'][14]);

		$wire = (string)json_encode($data);
		$log = (string)json_encode($this->logged);
		foreach (['Geheim', 'Vertrag', 'Gemeinsam', 'Plan', 'trashbin'] as $secret) {
			self::assertStringNotContainsString($secret, $wire);
			self::assertStringNotContainsString($secret, $log);
		}
		foreach ($data['keys'] as $key) {
			self::assertStringNotContainsString($key, $log);
		}

		$debug = array_values(array_filter($this->logged, static fn (array $entry): bool => $entry[0] === 'debug'));
		self::assertCount(1, $debug);
		self::assertSame(['asked' => 4, 'keys' => 2, 'absent' => 2], $debug[0][2]);
	}

	public function testAnAnswerWithoutKeysStillCarriesAMap(): void {
		$response = $this->storageController($this->backendAppId(), '13', $this->docKeysOver([]))->docKeys();

		self::assertSame('{"keys":{},"absent":[13]}', json_encode($response->getData()));
	}

	public function testAFailingKeyLookupAnswersWithAStaticSentenceAndLogsNoMessage(): void {
		$this->docKeyService->method('docKeysFor')
			->willThrowException(new \RuntimeException('SELECT path FROM oc_filecache: files/Geheim'));

		$response = $this->storageController($this->backendAppId(), '9')->docKeys();

		self::assertSame(Http::STATUS_INTERNAL_SERVER_ERROR, $response->getStatus());
		self::assertSame(['error' => 'Document keys are not available.'], $response->getData());

		$errors = array_values(array_filter($this->logged, static fn (array $entry): bool => $entry[0] === 'error'));
		self::assertCount(1, $errors);
		self::assertSame(['exception'], array_keys($errors[0][2]));
		self::assertStringNotContainsString('Geheim', $errors[0][1]);
	}
}
