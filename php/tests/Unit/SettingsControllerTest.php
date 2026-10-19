<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\BackgroundJobs\ExclusionSweepJob;
use OCA\Findling\BackgroundJobs\SubtreeExpandJob;
use OCA\Findling\Controller\SettingsController;
use OCA\Findling\Service\AdminViewService;
use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\ParallelSearchService;
use OCA\Findling\Service\PathResolverService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\ReaderContext;
use OCA\Findling\Service\ScanStatsService;
use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCP\App\IAppManager;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\IRootFolder;
use OCP\IAppConfig;
use OCP\IDateTimeFormatter;
use OCP\IDBConnection;
use OCP\IL10N;
use OCP\IRequest;
use OCP\IUserManager;
use OCP\IUserSession;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The two rules routes of the admin page with both lists (plan 33-05).
 *
 * The prefix list of D-06 and the pattern list of D-30-01 travel in one form,
 * and the promise of that form is the one the route has made since phase 4:
 * judged as a whole before anything is written, so one bad entry in either list
 * leaves every key as it was (T-33-19). The answer names codes and never a value
 * somebody typed, and the log counts and never quotes (T-33-20).
 *
 * SettingsService, ExclusionService and AdminViewService are final, so real
 * ones are built on a doubled IAppConfig that keeps its values in an array and
 * records every write, and on a doubled job list that records every entry it is
 * handed. Everything AdminViewService needs beyond the two services is a bare
 * double, because the rules routes ask it for rules() only; the overview case
 * of plan 34-03 runs over the same doubles and reads one key of the answer.
 */
#[CoversClass(SettingsController::class)]
final class SettingsControllerTest extends TestCase {
	/** Ten megabytes, inside the range the default container ceiling allows. */
	private const CAP = 10 * 1024 * 1024;

	/** @var array<string, mixed> */
	private array $values = [];

	/** @var list<string> every key a setValue* call reached, in order */
	private array $writes = [];

	/** @var list<array{string, mixed}> every job entry, class and argument */
	private array $jobs = [];

	/** @var list<array{level: string, message: string, context: array<array-key, mixed>}> */
	private array $logLines = [];

	protected function setUp(): void {
		parent::setUp();

		$this->values = [];
		$this->writes = [];
		$this->jobs = [];
		$this->logLines = [];
	}

	private function controller(): SettingsController {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueInt')->willReturnCallback(
			fn (string $app, string $key, int $default = 0): int => is_int($this->values[$key] ?? null) ? $this->values[$key] : $default,
		);
		$appConfig->method('getValueBool')->willReturnCallback(
			fn (string $app, string $key, bool $default = false): bool => is_bool($this->values[$key] ?? null) ? $this->values[$key] : $default,
		);
		$appConfig->method('getValueString')->willReturnCallback(
			fn (string $app, string $key, string $default = ''): string => is_string($this->values[$key] ?? null) ? $this->values[$key] : $default,
		);
		$appConfig->method('getValueArray')->willReturnCallback(
			fn (string $app, string $key, array $default = []): array => is_array($this->values[$key] ?? null) ? $this->values[$key] : $default,
		);
		foreach (['setValueInt', 'setValueBool', 'setValueString', 'setValueArray'] as $setter) {
			$appConfig->method($setter)->willReturnCallback(
				function (string $app, string $key, mixed $value): bool {
					$this->values[$key] = $value;
					$this->writes[] = $key;

					return true;
				},
			);
		}

		$logger = $this->createMock(LoggerInterface::class);
		foreach (['emergency', 'alert', 'critical', 'error', 'warning', 'notice', 'info', 'debug'] as $level) {
			$logger->method($level)->willReturnCallback(
				function (string|\Stringable $message, array $context = []) use ($level): void {
					$this->logLines[] = ['level' => $level, 'message' => (string)$message, 'context' => $context];
				},
			);
		}

		$jobList = $this->createMock(IJobList::class);
		$jobList->method('add')->willReturnCallback(
			function (mixed $job, mixed $argument = null): void {
				$this->jobs[] = [is_string($job) ? $job : get_class($job), $argument];
			},
		);

		$storage = $this->createMock(StorageService::class);
		$storage->method('getMounts')->willReturn([]);

		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturn(1_800_000_000);

		$settings = new SettingsService($appConfig, $logger, $time);
		$exclusions = new ExclusionService($appConfig, $storage, $jobList, $logger);
		$session = $this->createMock(IUserSession::class);

		$view = new AdminViewService(
			$this->createMock(FileStateService::class),
			$this->createMock(QueueService::class),
			$this->createMock(ExAppService::class),
			new ScanStatsService($this->createMock(IDBConnection::class), $time, $logger),
			new PathResolverService(
				$this->createMock(IUserMountCache::class),
				$this->createMock(IFileAccess::class),
				$this->createMock(IRootFolder::class),
				$this->createMock(IDBConnection::class),
				$logger,
				new ReaderContext($session, $this->createMock(IUserManager::class)),
			),
			$storage,
			$settings,
			$exclusions,
			$appConfig,
			$session,
			$time,
			$this->createMock(IL10N::class),
			$this->createMock(IDateTimeFormatter::class),
			// Final, so built for real over a doubled app manager that answers
			// false for every app (plan 34-03).
			new ParallelSearchService($this->createMock(IAppManager::class)),
		);

		return new SettingsController(
			$this->createMock(IRequest::class),
			$view,
			$settings,
			$exclusions,
			$session,
			$logger,
		);
	}

	/** @return array<array-key, mixed> */
	private static function body(DataResponse $response): array {
		$data = $response->getData();
		self::assertIsArray($data);

		return $data;
	}

	/** The classes of the planned jobs, in order. @return list<string> */
	private function jobClasses(): array {
		return array_map(static fn (array $job): string => $job[0], $this->jobs);
	}

	/**
	 * Every context value of every log line is a counter. A path, a folder or a
	 * pattern would arrive as a string (T-33-20).
	 */
	private function assertTheLogOnlyCounts(): void {
		self::assertNotSame([], $this->logLines);
		foreach ($this->logLines as $line) {
			foreach ($line['context'] as $key => $value) {
				self::assertIsInt($value, sprintf('log context %s of "%s" is not a counter', (string)$key, $line['message']));
			}
		}
	}

	// -- POST admin/rules -----------------------------------------------------

	public function testAPrefixAndAPatternAreBothSavedAndThePrefixListStaysByteForByte(): void {
		$this->values[SettingsService::KEY_EXCLUSIONS] = ['Archiv'];

		$response = $this->controller()->saveRules(['Archiv'], self::CAP, true, false, ['*.key']);
		$body = self::body($response);

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertTrue($body['saved']);
		self::assertSame([], $body['fields']);
		self::assertSame([], $body['exclusions']);
		self::assertSame([], $body[ExclusionService::FIELD_PATTERNS]);
		self::assertSame(['Archiv'], $this->values[SettingsService::KEY_EXCLUSIONS]);
		self::assertSame(['*.key'], $this->values[SettingsService::KEY_EXCLUSION_PATTERNS]);

		$rules = $body['rules'];
		self::assertIsArray($rules);
		self::assertSame(['Archiv'], $rules['exclusions']);
		self::assertSame(['*.key'], $rules['exclusionPatterns']);
		self::assertSame(ExclusionService::MAX_PATTERNS, $rules['maxPatterns']);
		self::assertSame(ExclusionService::MAX_PATTERN_LENGTH, $rules['maxPatternLength']);
		self::assertSame(ExclusionService::MAX_PREFIXES, $rules['maxPrefixes']);
		self::assertSame(ExclusionService::MAX_PREFIX_LENGTH, $rules['maxPrefixLength']);
	}

	public function testAnInvalidPatternNextToAValidPrefixWritesNothingAtAll(): void {
		$this->values[SettingsService::KEY_EXCLUSIONS] = ['Alt'];

		$response = $this->controller()->saveRules(['Archiv'], self::CAP, true, false, ['[0-9]*']);
		$body = self::body($response);

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertFalse($body['saved']);
		self::assertSame([ExclusionService::ERROR_UNSUPPORTED_CHARACTER], $body[ExclusionService::FIELD_PATTERNS]);
		self::assertSame(ExclusionService::ERROR_UNSUPPORTED_CHARACTER, $body[ExclusionService::FIELD_PATTERNS][0]);
		self::assertSame([], $body['exclusions']);
		self::assertSame([], $body['fields']);
		self::assertSame('The rules were not saved.', $body['error']);

		self::assertSame([], $this->writes, 'a refused form wrote a key');
		self::assertNotContains(SettingsService::KEY_EXCLUSIONS, $this->writes);
		self::assertNotContains(SettingsService::KEY_EXCLUSION_PATTERNS, $this->writes);
		self::assertSame(['Alt'], $this->values[SettingsService::KEY_EXCLUSIONS]);
		self::assertSame([], $this->jobs);
		$this->assertTheLogOnlyCounts();
	}

	public function testAnInvalidPrefixNextToAValidPatternWritesNothingAtAll(): void {
		$response = $this->controller()->saveRules(['Archiv/../Privat'], self::CAP, true, false, ['*.key']);
		$body = self::body($response);

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertFalse($body['saved']);
		self::assertSame([ExclusionService::ERROR_TRAVERSAL], $body['exclusions']);
		self::assertSame([], $body[ExclusionService::FIELD_PATTERNS]);

		self::assertSame([], $this->writes, 'a refused form wrote a key');
		self::assertArrayNotHasKey(SettingsService::KEY_EXCLUSION_PATTERNS, $this->values);
		self::assertSame([], $this->jobs);
		$this->assertTheLogOnlyCounts();
	}

	public function testAnInvalidCapNextToAValidPatternWritesNoPattern(): void {
		$response = $this->controller()->saveRules([], 0, true, false, ['*.key']);
		$body = self::body($response);

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertSame([SettingsService::FIELD_MAX_FILE_BYTES => SettingsService::ERROR_OUT_OF_RANGE], $body['fields']);
		self::assertSame([], $this->writes);
		self::assertSame([], $this->jobs);
	}

	public function testASaveThatOnlyAddsAPatternLeavesThePrefixesAndPlansNoSubtreeClearing(): void {
		$this->values[SettingsService::KEY_EXCLUSIONS] = ['Archiv', 'Backups/2024'];

		$response = $this->controller()->saveRules(['Archiv', 'Backups/2024'], self::CAP, true, false, ['*/node_modules/*']);

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		// The form of today for an unchanged list: written once, with the same
		// content in the same order.
		self::assertSame(['Archiv', 'Backups/2024'], $this->values[SettingsService::KEY_EXCLUSIONS]);
		self::assertSame(1, count(array_keys($this->writes, SettingsService::KEY_EXCLUSIONS, true)));
		self::assertNotContains(SubtreeExpandJob::class, $this->jobClasses());
		self::assertSame([ExclusionSweepJob::class], $this->jobClasses());
	}

	public function testARefusalOfEitherListNeverCarriesTheValueThatWasTyped(): void {
		$pattern = '[geheim]*';
		$prefix = 'Privat/../Geheim';

		$refusedPattern = $this->controller()->saveRules(['Archiv'], self::CAP, true, false, [$pattern]);
		$refusedPrefix = $this->controller()->saveRules([$prefix], self::CAP, true, false, ['*.key']);
		$refusedPreview = $this->controller()->previewRules([$prefix], [$pattern]);

		foreach ([$refusedPattern, $refusedPrefix, $refusedPreview] as $response) {
			self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
			$encoded = json_encode($response->getData(), JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
			self::assertStringNotContainsString($pattern, $encoded);
			self::assertStringNotContainsString('geheim', $encoded);
			self::assertStringNotContainsString('Geheim', $encoded);
			self::assertStringNotContainsString('Privat', $encoded);
		}

		foreach ($this->logLines as $line) {
			$logged = json_encode($line, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
			self::assertStringNotContainsString('geheim', $logged);
			self::assertStringNotContainsString('Geheim', $logged);
			self::assertStringNotContainsString('Privat', $logged);
		}
		$this->assertTheLogOnlyCounts();
	}

	/**
	 * A list that is not a list at all, as only a built request can send it.
	 * Before audit 33-11 the native array type made the core call saveRules()
	 * into a TypeError: HTTP 500, and the trace of the log line carried every
	 * argument, the prefix list and the pattern value included (H-33-01). Both
	 * lists are taken as they come now and a value that is not a list is refused
	 * with the code a value that is not text already earns, in both routes.
	 *
	 * @return iterable<string, array{mixed}>
	 */
	public static function notAList(): iterable {
		yield 'a string' => ['*.q33jd'];
		yield 'an empty string' => [''];
		yield 'a number' => [7];
		yield 'null' => [null];
		yield 'true' => [true];
	}

	#[DataProvider('notAList')]
	public function testAPatternListThatIsNoListIsRefusedWithACodeAndWritesNothing(mixed $value): void {
		$this->values[SettingsService::KEY_EXCLUSIONS] = ['Alt'];

		$response = $this->controller()->saveRules(['Alt'], self::CAP, true, false, $value);
		$body = self::body($response);

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertFalse($body['saved']);
		self::assertSame([ExclusionService::ERROR_EMPTY], $body[ExclusionService::FIELD_PATTERNS]);
		self::assertSame([], $body['exclusions']);
		self::assertSame([], $this->writes, 'a refused form wrote a key');
		self::assertSame([], $this->jobs);
		self::assertStringNotContainsString('q33', json_encode($response->getData(), JSON_THROW_ON_ERROR));
		$this->assertTheLogOnlyCounts();
	}

	#[DataProvider('notAList')]
	public function testAPrefixListThatIsNoListIsRefusedWithACodeAndWritesNothing(mixed $value): void {
		$response = $this->controller()->saveRules($value, self::CAP, true, false, ['*.key']);
		$body = self::body($response);

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertFalse($body['saved']);
		self::assertSame([ExclusionService::ERROR_EMPTY], $body['exclusions']);
		self::assertSame([], $body[ExclusionService::FIELD_PATTERNS]);
		self::assertSame([], $this->writes, 'a refused form wrote a key');
		self::assertSame([], $this->jobs);
		$this->assertTheLogOnlyCounts();
	}

	#[DataProvider('notAList')]
	public function testThePreviewRefusesEitherListThatIsNoList(mixed $value): void {
		$patterns = $this->controller()->previewRules(['Archiv'], $value);
		$prefixes = $this->controller()->previewRules($value, ['*.key']);

		self::assertSame(Http::STATUS_BAD_REQUEST, $patterns->getStatus());
		self::assertSame([ExclusionService::ERROR_EMPTY], self::body($patterns)[ExclusionService::FIELD_PATTERNS]);
		self::assertSame([], self::body($patterns)['exclusions']);
		self::assertSame(Http::STATUS_BAD_REQUEST, $prefixes->getStatus());
		self::assertSame([ExclusionService::ERROR_EMPTY], self::body($prefixes)['exclusions']);
		self::assertSame([], self::body($prefixes)[ExclusionService::FIELD_PATTERNS]);
		self::assertSame([], $this->writes);
		$this->assertTheLogOnlyCounts();
	}

	/** An object instead of a list stays what it was: its values, in order. */
	public function testAnObjectInsteadOfAListIsReadAsItsValues(): void {
		$response = $this->controller()->saveRules(['a' => 'Archiv'], self::CAP, true, false, ['x' => '*.key']);

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['Archiv'], $this->values[SettingsService::KEY_EXCLUSIONS]);
		self::assertSame(['*.key'], $this->values[SettingsService::KEY_EXCLUSION_PATTERNS]);
	}

	public function testEveryCodeOfAPatternTravelsWithoutItsEntry(): void {
		$response = $this->controller()->saveRules([], self::CAP, true, false, ['**.key', '!*.tmp', 'Ordner', '*', '*.key', '*.key']);
		$body = self::body($response);

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertSame(
			[
				ExclusionService::ERROR_DOUBLE_STAR,
				ExclusionService::ERROR_NEGATION,
				ExclusionService::ERROR_NO_WILDCARD,
				ExclusionService::ERROR_NO_LITERAL,
				ExclusionService::ERROR_DUPLICATE,
			],
			$body[ExclusionService::FIELD_PATTERNS],
		);
		self::assertSame([], $this->writes);
	}

	// -- POST admin/rules/preview ---------------------------------------------

	/**
	 * Finding L-33-09-01 of plan 33-09: the lists travel in the body.
	 *
	 * A GET carried every prefix and every pattern in the query string, and
	 * Nextcloud writes the address of the request into the url field of each
	 * log line, so a refused preview put the rules of the instance into
	 * nextcloud.log. The verb is read off the route attribute itself, and the
	 * request token check stays on like on the writing route next to it.
	 */
	public function testThePreviewIsAPostRouteSoNoRuleTravelsInAnAddress(): void {
		$route = self::routeOf('previewRules');
		self::assertSame('POST', $route['verb'] ?? null);
		self::assertSame('/admin/rules/preview', $route['url'] ?? null);
		self::assertSame(self::routeOf('saveRules')['verb'] ?? null, $route['verb'] ?? null);

		$method = new \ReflectionMethod(SettingsController::class, 'previewRules');
		foreach ($method->getAttributes() as $attribute) {
			self::assertStringNotContainsString('CSRF', $attribute->getName());
			self::assertStringNotContainsString('NoAdminRequired', $attribute->getName());
		}
	}

	public function testARefusedPatternIsLoggedAsAPatternAndARefusedPrefixAsAFolder(): void {
		$this->controller()->previewRules(['Archiv'], ['[0-9]*']);
		$patternLines = array_column($this->logLines, 'message');
		$this->assertTheLogOnlyCounts();

		$this->logLines = [];
		$this->controller()->previewRules(['./Archiv'], ['*.key']);
		$folderLines = array_column($this->logLines, 'message');
		$this->assertTheLogOnlyCounts();

		self::assertContains('Findling: refused an exclusion pattern that is not a usable pattern', $patternLines);
		self::assertNotContains('Findling: refused an exclusion entry that is not a usable folder path', $patternLines);
		self::assertContains('Findling: refused an exclusion entry that is not a usable folder path', $folderLines);
		self::assertNotContains('Findling: refused an exclusion pattern that is not a usable pattern', $folderLines);
		foreach (array_merge($patternLines, $folderLines) as $message) {
			foreach (['Archiv', '[0-9]', '*.key'] as $value) {
				self::assertStringNotContainsString($value, $message);
			}
		}
	}

	/**
	 * The arguments of the route attribute of one method, by name.
	 *
	 * @return array<array-key, mixed>
	 */
	private static function routeOf(string $method): array {
		$reflection = new \ReflectionMethod(SettingsController::class, $method);
		foreach ($reflection->getAttributes() as $attribute) {
			if (str_ends_with($attribute->getName(), '\FrontpageRoute')) {
				return $attribute->getArguments();
			}
		}
		self::fail('no route attribute on ' . $method);
	}


	public function testThePreviewNamesTheNewPatternsAndCountsOnlyThePrefixes(): void {
		$this->values[SettingsService::KEY_EXCLUSIONS] = ['Archiv'];
		$this->values[SettingsService::KEY_EXCLUSION_PATTERNS] = ['*.photoslibrary'];

		$response = $this->controller()->previewRules(['Archiv'], ['*.photoslibrary', '*.key']);
		$body = self::body($response);

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['*.key'], $body['newPatterns']);
		self::assertSame([], $body['newPrefixes']);
		self::assertSame(0, $body['affectedDocuments']);
		self::assertFalse($body['capped']);
		// One number in the answer and it is the one of the prefixes (PE-5).
		self::assertSame(['newPrefixes', 'affectedDocuments', 'capped', 'newPatterns'], array_keys($body));
		self::assertSame([], $this->writes, 'the preview wrote a key');
		self::assertSame([], $this->jobs, 'the preview planned a job');
	}

	public function testThePreviewRefusesAnInvalidPatternWithItsCodeAndWritesNothing(): void {
		$response = $this->controller()->previewRules(['Archiv'], ['[0-9]*']);
		$body = self::body($response);

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertSame([ExclusionService::ERROR_UNSUPPORTED_CHARACTER], $body[ExclusionService::FIELD_PATTERNS]);
		self::assertSame([], $body['exclusions']);
		self::assertArrayNotHasKey('newPatterns', $body);
		self::assertSame([], $this->writes);
		$this->assertTheLogOnlyCounts();
	}

	public function testThePreviewRefusesAnInvalidPrefixNextToAValidPattern(): void {
		$response = $this->controller()->previewRules(['./Archiv'], ['*.key']);
		$body = self::body($response);

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertSame([ExclusionService::ERROR_TRAVERSAL], $body['exclusions']);
		self::assertSame([], $body[ExclusionService::FIELD_PATTERNS]);
		self::assertSame([], $this->writes);
	}

	public function testTheOverviewCarriesParallelSearchAsFalseWithoutTheFramework(): void {
		// UMST-02, plan 34-03: the key is always there and a bool. The app
		// manager double answers false for every app, which is an instance
		// without fulltextsearch and files_fulltextsearch.
		$response = $this->controller()->overview();
		$body = self::body($response);

		self::assertSame(Http::STATUS_OK, $response->getStatus(), json_encode($this->logLines) ?: '');
		self::assertArrayHasKey('parallelSearch', $body);
		self::assertFalse($body['parallelSearch']);
	}
}
