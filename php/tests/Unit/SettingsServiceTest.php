<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IAppConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The profile half of SettingsService that phase 27 added: the stored state,
 * the downward rule of D-27-09, the two writers and the probe record.
 *
 * SettingsService is final, so it is not doubled. A real one is built on a
 * doubled IAppConfig that keeps its values in an array, the same seam as in
 * ProfileControllerTest, so a write is visible to the read that follows it.
 */
#[CoversClass(SettingsService::class)]
final class SettingsServiceTest extends TestCase {
	private const TOKEN = '0123456789abcdef0123456789abcdef';

	private IAppConfig&MockObject $appConfig;
	private LoggerInterface&MockObject $logger;

	private const NOW = 1790000000;

	private ITimeFactory&MockObject $time;

	/** @var array<string, int|string|array<mixed>> the stored keys of the app */
	private array $values = [];

	protected function setUp(): void {
		parent::setUp();

		$this->values = [];
		$this->appConfig = $this->createMock(IAppConfig::class);
		$this->logger = $this->createMock(LoggerInterface::class);
		$this->time = $this->createMock(ITimeFactory::class);
		$this->time->method('getTime')->willReturn(self::NOW);

		$this->appConfig->method('getValueInt')->willReturnCallback(
			function (string $app, string $key, int $default = 0): int {
				$value = $this->values[$key] ?? $default;

				return is_int($value) ? $value : $default;
			},
		);
		$this->appConfig->method('setValueInt')->willReturnCallback(
			function (string $app, string $key, int $value): bool {
				$this->values[$key] = $value;

				return true;
			},
		);

		$this->appConfig->method('hasKey')->willReturnCallback(
			fn (string $app, string $key): bool => $app === Application::APP_ID && array_key_exists($key, $this->values),
		);
		$this->appConfig->method('getValueString')->willReturnCallback(
			function (string $app, string $key, string $default = ''): string {
				$value = $this->values[$key] ?? $default;

				return is_string($value) ? $value : $default;
			},
		);
		$this->appConfig->method('setValueString')->willReturnCallback(
			function (string $app, string $key, string $value): bool {
				$this->values[$key] = $value;

				return true;
			},
		);
		$this->appConfig->method('getValueArray')->willReturnCallback(
			function (string $app, string $key, array $default = []): array {
				$value = $this->values[$key] ?? $default;

				return is_array($value) ? $value : $default;
			},
		);
		$this->appConfig->method('setValueArray')->willReturnCallback(
			function (string $app, string $key, array $value): bool {
				$this->values[$key] = $value;

				return true;
			},
		);
		$this->appConfig->method('deleteKey')->willReturnCallback(
			function (string $app, string $key): void {
				unset($this->values[$key]);
			},
		);
	}

	private function settings(): SettingsService {
		return new SettingsService($this->appConfig, $this->logger, $this->time);
	}

	private function stored(?string $profile, ?string $precision = null): void {
		if ($profile !== null) {
			$this->values[SettingsService::KEY_PROFILE] = $profile;
		}
		if ($precision !== null) {
			$this->values[SettingsService::KEY_MODEL_PRECISION] = $precision;
		}
	}

	// -- profileStored ---------------------------------------------------------

	public function testNoStoredProfileIsNotStored(): void {
		self::assertFalse($this->settings()->profileStored());
		// SC1: without a click the box stays on economy.
		self::assertSame('economy', $this->settings()->profile());
	}

	public function testAStoredEconomyIsStored(): void {
		$this->stored('economy');

		self::assertTrue($this->settings()->profileStored());
	}

	// -- needsProbe and isDownward (D-27-09) ------------------------------------

	/** @return array<string, array{?string, ?string, string, string, bool}> */
	public static function probeCases(): array {
		return [
			'standard from nothing stored' => [null, null, 'standard', 'int8', true],
			'economy from nothing stored' => [null, null, 'economy', 'int8', false],
			'economy from performance fp32' => ['performance', 'fp32', 'economy', 'fp32', false],
			'economy with int8 from standard fp32' => ['standard', 'fp32', 'economy', 'int8', false],
			'only fp32 to int8 on performance' => ['performance', 'fp32', 'performance', 'int8', false],
			'performance to standard is no safe way down' => ['performance', 'int8', 'standard', 'int8', true],
			'int8 to fp32 on standard' => ['standard', 'int8', 'standard', 'fp32', true],
			'fp32 to int8 together with a profile change' => ['performance', 'fp32', 'standard', 'int8', true],
			'invalid stored precision counts as int8' => ['standard', 'fp16', 'standard', 'int8', true],
		];
	}

	#[DataProvider('probeCases')]
	public function testNeedsProbeFollowsTheDownwardRule(
		?string $storedProfile,
		?string $storedPrecision,
		string $profile,
		string $precision,
		bool $expected,
	): void {
		$this->stored($storedProfile, $storedPrecision);
		$settings = $this->settings();

		self::assertSame($expected, $settings->needsProbe($profile, $precision));
		self::assertSame(!$expected, $settings->isDownward($profile, $precision));
	}

	public function testAnInvalidTargetIsNeverDownward(): void {
		$settings = $this->settings();

		self::assertTrue($settings->needsProbe('turbo', 'int8'));
		self::assertFalse($settings->isDownward('turbo', 'int8'));
		self::assertFalse($settings->isDownward('economy', 'fp16'));
	}

	// -- saveProfile ------------------------------------------------------------

	public function testSaveProfileWritesBothKeys(): void {
		self::assertTrue($this->settings()->saveProfile('standard', 'fp32'));

		self::assertSame('standard', $this->values[SettingsService::KEY_PROFILE]);
		self::assertSame('fp32', $this->values[SettingsService::KEY_MODEL_PRECISION]);
	}

	/** @return array<string, array{string, string}> */
	public static function invalidPairs(): array {
		return [
			'unknown profile' => ['turbo', 'int8'],
			'wrong case profile' => ['Standard', 'int8'],
			'unknown precision' => ['standard', 'fp16'],
			'wrong case precision' => ['standard', 'FP32'],
		];
	}

	#[DataProvider('invalidPairs')]
	public function testSaveProfileRefusesAnInvalidPairAndWritesNothing(string $profile, string $precision): void {
		$this->logger->expects(self::atLeastOnce())->method('warning')->with(
			self::isString(),
			self::callback(static function (array $context) use ($profile, $precision): bool {
				$written = json_encode($context, JSON_THROW_ON_ERROR);

				return !str_contains($written, $profile) && !str_contains($written, $precision);
			}),
		);

		self::assertFalse($this->settings()->saveProfile($profile, $precision));
		self::assertSame([], $this->values);
	}

	public function testEconomyWithFp32IsRefusedAsAChange(): void {
		$this->stored('standard', 'int8');

		self::assertFalse($this->settings()->saveProfile('economy', 'fp32'));
		self::assertSame('standard', $this->values[SettingsService::KEY_PROFILE]);
		self::assertSame('int8', $this->values[SettingsService::KEY_MODEL_PRECISION]);
	}

	public function testEconomyKeepsAnFp32ThatIsAlreadyStored(): void {
		// D-25-10: the precision stays when the profile goes down to economy.
		$this->stored('performance', 'fp32');

		self::assertTrue($this->settings()->saveProfile('economy', 'fp32'));
		self::assertSame('economy', $this->values[SettingsService::KEY_PROFILE]);
		self::assertSame('fp32', $this->values[SettingsService::KEY_MODEL_PRECISION]);
	}

	public function testAFailedWriteAnswersFalseWithoutValues(): void {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturnCallback(
			static fn (string $app, string $key, string $default = ''): string => $default,
		);
		$appConfig->method('setValueString')->willThrowException(new \RuntimeException('storage gone'));
		$this->logger->expects(self::once())->method('error')->with(
			self::isString(),
			self::callback(static function (array $context): bool {
				// The exception and nothing else: no profile, no precision.
				return array_keys($context) === ['exception'];
			}),
		);

		self::assertFalse((new SettingsService($appConfig, $this->logger, $this->time))->saveProfile('standard', 'int8'));
	}

	// -- saveConfirmation ------------------------------------------------------

	public function testSaveConfirmationStoresAWellFormedToken(): void {
		self::assertTrue($this->settings()->saveConfirmation(self::TOKEN));
		self::assertSame(self::TOKEN, $this->values[SettingsService::KEY_PROFILE_CONFIRMED]);
		self::assertSame(self::TOKEN, $this->settings()->profileConfirmed());
	}

	/** @return array<string, array{string}> */
	public static function tokensOutsideTheForm(): array {
		return [
			'empty' => [''],
			'not hex' => ['XYZ'],
			'31 characters' => [substr(self::TOKEN, 0, 31)],
			'33 characters' => [self::TOKEN . '0'],
			'upper case' => [strtoupper(self::TOKEN)],
			'trailing newline' => [self::TOKEN . "\n"],
		];
	}

	#[DataProvider('tokensOutsideTheForm')]
	public function testSaveConfirmationRefusesATokenOutsideTheForm(string $token): void {
		self::assertFalse($this->settings()->saveConfirmation($token));
		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE_CONFIRMED, $this->values);
	}

	// -- the probe record (D-27-04, D-27-10) -----------------------------------

	public function testTheProbeKeysAreTheirOwn(): void {
		self::assertSame('profile_check', SettingsService::KEY_PROFILE_CHECK);
		self::assertSame('profile_check_pending', SettingsService::KEY_PROFILE_CHECK_PENDING);
	}

	public function testNoProbeRecordIsNull(): void {
		self::assertNull($this->settings()->profileCheck());
		self::assertNull($this->settings()->profileCheckPending());
	}

	public function testARememberedCheckIsReadBack(): void {
		$check = ['verdict' => 'fits', 'profile' => 'standard', 'precision' => 'int8', 'at' => 1790000000];

		$this->settings()->rememberProfileCheck($check);

		self::assertSame($check, $this->values[SettingsService::KEY_PROFILE_CHECK]);
		// D-27-10: a new service, as after a reload, still sees it.
		self::assertSame($check, $this->settings()->profileCheck());
	}

	public function testAPendingProbeIsRememberedAndForgotten(): void {
		$pending = ['profile' => 'performance', 'precision' => 'fp32', 'startedAt' => 1790000000];
		$settings = $this->settings();

		$settings->rememberPending($pending);
		self::assertSame($pending, $settings->profileCheckPending());

		$settings->forgetPending();
		self::assertNull($settings->profileCheckPending());
		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE_CHECK_PENDING, $this->values);
	}

	// -- the recount mark (quick task 260929-kii) -------------------------------

	public function testMarkScanStaleWritesTheFirstTimeOnly(): void {
		$settings = $this->settings();

		$settings->markScanStale();
		self::assertSame(self::NOW, $this->values[SettingsService::KEY_SCAN_STALE_SINCE]);

		// A second event keeps the first mark: one write per round, not per
		// upload.
		$this->values[SettingsService::KEY_SCAN_STALE_SINCE] = 42;
		$settings->markScanStale();
		self::assertSame(42, $this->values[SettingsService::KEY_SCAN_STALE_SINCE]);
	}

	public function testMarkScanStaleDoesNotWriteAnExistingMark(): void {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueInt')->willReturn(42);
		$appConfig->expects(self::never())->method('setValueInt');

		(new SettingsService($appConfig, $this->logger, $this->time))->markScanStale();
	}

	public function testANeverRunRecountIsDue(): void {
		self::assertTrue($this->settings()->scanRecountDue(self::NOW));
	}

	public function testARecentRecountIsNotDueWithoutAMark(): void {
		$this->values[SettingsService::KEY_SCAN_RECOUNTED_AT] = self::NOW - 3600;

		self::assertFalse($this->settings()->scanRecountDue(self::NOW));
	}

	public function testAMarkMakesTheRecountDue(): void {
		$this->values[SettingsService::KEY_SCAN_RECOUNTED_AT] = self::NOW - 60;
		$this->values[SettingsService::KEY_SCAN_STALE_SINCE] = self::NOW - 30;

		self::assertTrue($this->settings()->scanRecountDue(self::NOW));
	}

	public function testADayOldRecountIsDueWithoutAMark(): void {
		$this->values[SettingsService::KEY_SCAN_RECOUNTED_AT] = self::NOW - SettingsService::RECOUNT_FLOOR_SECONDS;

		self::assertTrue($this->settings()->scanRecountDue(self::NOW));
	}

	public function testBeginRecountClearsTheMarkAndRemembersTheTime(): void {
		$this->values[SettingsService::KEY_SCAN_STALE_SINCE] = self::NOW - 30;

		$settings = $this->settings();
		$settings->beginRecount(self::NOW);

		self::assertSame(0, $this->values[SettingsService::KEY_SCAN_STALE_SINCE]);
		self::assertSame(self::NOW, $this->values[SettingsService::KEY_SCAN_RECOUNTED_AT]);
		self::assertFalse($settings->scanRecountDue(self::NOW + 60));
	}

	public function testSavingTheRulesMarksTheScanStale(): void {
		$errors = $this->settings()->save([
			SettingsService::FIELD_MAX_FILE_BYTES => SettingsService::MIN_CAP_BYTES,
			'indexTeamFolders' => true,
			'indexExternalStorage' => false,
		]);

		self::assertSame([], $errors);
		self::assertSame(self::NOW, $this->values[SettingsService::KEY_SCAN_STALE_SINCE]);
	}
}
