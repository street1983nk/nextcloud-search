<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\ProbeService;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IAppConfig;
use OCP\IDateTimeFormatter;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The PHP half of the probe (PRUEF-01, D-27-08): only an own, fully judged
 * "fits" is saved, and every verdict is remembered.
 *
 * SettingsService is final, so a real one is built on a doubled IAppConfig
 * that keeps its values in an array, the seam of SettingsServiceTest. The
 * transport is a double of the three admin methods of ExAppService, which is
 * not final for exactly this reason (see its @final note).
 */
#[CoversClass(ProbeService::class)]
final class ProbeServiceTest extends TestCase {
	private const ID = '0123456789abcdef';
	private const OTHER_ID = 'fedcba9876543210';
	private const TOKEN = '0123456789abcdef0123456789abcdef';
	private const NOW = 1_800_000_000;

	private IAppConfig&MockObject $appConfig;
	private LoggerInterface&MockObject $logger;
	private ExAppService&MockObject $exApp;
	private IDateTimeFormatter&MockObject $formatter;
	private ITimeFactory&MockObject $time;

	/** @var array<string, mixed> the stored keys of the app */
	private array $values = [];

	/** @var list<string> keys in the order they were written */
	private array $writes = [];

	private int $now = self::NOW;

	protected function setUp(): void {
		parent::setUp();

		$this->values = [];
		$this->writes = [];
		$this->now = self::NOW;
		$this->appConfig = $this->createMock(IAppConfig::class);
		$this->logger = $this->createMock(LoggerInterface::class);
		$this->formatter = $this->createMock(IDateTimeFormatter::class);
		$this->formatter->method('formatDateTime')->willReturn('formatted');
		$this->time = $this->createMock(ITimeFactory::class);
		$this->time->method('getTime')->willReturnCallback(fn (): int => $this->now);
		$this->exApp = $this->getMockBuilder(ExAppService::class)
			->disableOriginalConstructor()
			->onlyMethods(['adminSend', 'adminState', 'adminGet'])
			->getMock();

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
				$this->writes[] = $key;

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
				$this->writes[] = $key;

				return true;
			},
		);
		$this->appConfig->method('deleteKey')->willReturnCallback(
			function (string $app, string $key): void {
				unset($this->values[$key]);
				$this->writes[] = 'delete:' . $key;
			},
		);
	}

	private function service(): ProbeService {
		return new ProbeService(
			$this->exApp,
			new SettingsService($this->appConfig, $this->logger, $this->createMock(ITimeFactory::class)),
			$this->formatter,
			$this->time,
			$this->logger,
		);
	}

	private function pending(string $profile = 'standard', string $precision = 'int8', ?int $startedAt = null): void {
		$this->values[SettingsService::KEY_PROFILE_CHECK_PENDING] = [
			'id' => self::ID,
			'profile' => $profile,
			'precision' => $precision,
			'uid' => 'admin',
			'startedAt' => $startedAt ?? self::NOW - 60,
		];
	}

	/**
	 * A finished state answer of the container, overridable key by key.
	 *
	 * @param array<string, mixed> $overrides
	 * @return array<string, mixed>
	 */
	private function done(array $overrides = []): array {
		return array_merge([
			'id' => self::ID,
			'state' => 'done',
			'step' => 'cleanup',
			'bytesDone' => 10,
			'bytesTotal' => 10,
			'verdict' => 'fits',
			'cause' => '',
			'numbers' => ['slots' => 2, 'need' => 100, 'available' => 500],
			'targetProfile' => 'standard',
			'targetPrecision' => 'int8',
			'fp32Fetched' => false,
			'fp32Deleted' => false,
			'startedAt' => self::NOW - 50,
			'finishedAt' => self::NOW - 5,
		], $overrides);
	}

	/** @param array<string, mixed>|null $body */
	private function stateAnswer(string $kind, ?array $body): void {
		$this->exApp->method('adminState')->willReturn(['kind' => $kind, 'body' => $body]);
	}

	// -- start ------------------------------------------------------------

	public function testStartRemembersTheProbeTheContainerAccepted(): void {
		$this->exApp->expects(self::once())->method('adminSend')
			->with('/probe', 'admin', ['profile' => 'standard', 'precision' => 'int8'])
			->willReturn(['kind' => ExAppService::ADMIN_OK, 'body' => ['id' => self::ID]]);

		$answer = $this->service()->start('standard', 'int8', 'admin');

		self::assertSame(['started' => true, 'code' => 'started'], $answer);
		self::assertSame([
			'id' => self::ID,
			'profile' => 'standard',
			'precision' => 'int8',
			'uid' => 'admin',
			'startedAt' => self::NOW,
			'inForce' => ['profile' => 'economy', 'precision' => 'int8', 'stored' => false],
		], $this->values[SettingsService::KEY_PROFILE_CHECK_PENDING]);
	}

	/** @return array<string, array{string, ?array<mixed>, string}> */
	public static function refusedStarts(): array {
		return [
			'busy' => [ExAppService::ADMIN_BUSY, ['state' => 'busy', 'id' => self::OTHER_ID], 'busy'],
			'busy without body' => [ExAppService::ADMIN_BUSY, null, 'busy'],
			'rebuilding' => [ExAppService::ADMIN_BUSY, ['state' => 'rebuilding'], 'rebuilding'],
			'old container' => [ExAppService::ADMIN_MISSING, null, 'unsupported'],
			'unreachable' => [ExAppService::ADMIN_UNREACHABLE, null, 'unreachable'],
			'refused' => [ExAppService::ADMIN_REFUSED, null, 'unreachable'],
			'ok without id' => [ExAppService::ADMIN_OK, ['id' => 'not-an-id'], 'unreachable'],
			'ok with id and newline' => [ExAppService::ADMIN_OK, ['id' => self::ID . "\n"], 'unreachable'],
		];
	}

	/** @param array<mixed>|null $body */
	#[DataProvider('refusedStarts')]
	public function testARefusedStartWritesNothing(string $kind, ?array $body, string $code): void {
		$this->pending('performance', 'fp32');
		$before = $this->values;
		$this->exApp->method('adminSend')->willReturn(['kind' => $kind, 'body' => $body]);

		$answer = $this->service()->start('standard', 'int8', 'admin');

		self::assertSame(['started' => false, 'code' => $code], $answer);
		self::assertSame($before, $this->values);
		self::assertSame([], $this->writes);
	}

	/** @return array<string, array{string, string}> */
	public static function invalidTargets(): array {
		return [
			'unknown profile' => ['turbo', 'int8'],
			'unknown precision' => ['standard', 'fp16'],
			'case' => ['Standard', 'int8'],
			'fp32 on economy' => ['economy', 'fp32'],
		];
	}

	#[DataProvider('invalidTargets')]
	public function testStartJudgesTheTargetAgain(string $profile, string $precision): void {
		$this->exApp->expects(self::never())->method('adminSend');

		$answer = $this->service()->start($profile, $precision, 'admin');

		self::assertSame(['started' => false, 'code' => 'invalid'], $answer);
		self::assertSame([], $this->writes);
	}

	// -- take-over ----------------------------------------------------------

	public function testAnOwnFitsIsSavedOnceAndRemembered(): void {
		$this->values[SettingsService::KEY_PROFILE] = 'economy';
		$this->pending();
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done());
		$this->exApp->method('adminGet')->willReturn(['guard' => ['chosen' => 'economy', 'token' => '']]);

		$service = $this->service();
		$answer = $service->state('admin');

		self::assertSame('standard', $this->values[SettingsService::KEY_PROFILE]);
		self::assertSame('int8', $this->values[SettingsService::KEY_MODEL_PRECISION]);
		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE_CHECK_PENDING, $this->values);
		$check = $this->values[SettingsService::KEY_PROFILE_CHECK];
		self::assertTrue($check['committed']);
		self::assertSame('fits', $check['verdict']);
		self::assertSame(self::ID, $check['id']);
		self::assertSame(self::NOW - 5, $check['at']);
		self::assertSame('ok', $answer['code']);
		self::assertSame('done', $answer['state']);
		self::assertIsArray($answer['result']);
		self::assertTrue($answer['result']['committed']);
		self::assertSame('formatted', $answer['result']['atText']);
		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE_CONFIRMED, $this->values);

		// A second call of both entry points writes nothing again.
		$this->writes = [];
		$service->state('admin');
		$service->settle('admin');
		self::assertSame([], $this->writes);
	}

	public function testAFitsIsSavedWhenNothingChangedSinceTheStart(): void {
		$this->values[SettingsService::KEY_PROFILE] = 'economy';
		$this->pending();
		$this->values[SettingsService::KEY_PROFILE_CHECK_PENDING]['inForce'] = [
			'profile' => 'economy',
			'precision' => 'int8',
			'stored' => true,
		];
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done());
		$this->exApp->method('adminGet')->willReturn(null);

		$this->service()->state('admin');

		self::assertSame('standard', $this->values[SettingsService::KEY_PROFILE]);
		self::assertTrue($this->values[SettingsService::KEY_PROFILE_CHECK]['committed']);
	}

	/** @return array<string, array{array<string, string>}> */
	public static function savesDuringTheProbe(): array {
		return [
			// Review WR-06 of phase 27: economy stored explicitly while the
			// default was in force, through occ or another tab.
			'economy stored over the default' => [[SettingsService::KEY_PROFILE => 'economy']],
			// fp32 taken back to int8 on the stored profile, the other way down.
			'precision lowered' => [[SettingsService::KEY_PROFILE => 'standard', SettingsService::KEY_MODEL_PRECISION => 'int8']],
		];
	}

	/** @param array<string, string> $saved */
	#[DataProvider('savesDuringTheProbe')]
	public function testAFitsDoesNotOverwriteASaveMadeWhileItRan(array $saved): void {
		$this->pending('performance', 'int8');
		$this->values[SettingsService::KEY_PROFILE_CHECK_PENDING]['inForce'] = isset($saved[SettingsService::KEY_MODEL_PRECISION])
			? ['profile' => 'standard', 'precision' => 'fp32', 'stored' => true]
			: ['profile' => 'economy', 'precision' => 'int8', 'stored' => false];
		foreach ($saved as $key => $value) {
			$this->values[$key] = $value;
		}
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done(['targetProfile' => 'performance']));
		$this->exApp->expects(self::never())->method('adminGet');

		$answer = $this->service()->state('admin');

		self::assertSame($saved[SettingsService::KEY_PROFILE], $this->values[SettingsService::KEY_PROFILE]);
		self::assertSame($saved[SettingsService::KEY_MODEL_PRECISION] ?? null, $this->values[SettingsService::KEY_MODEL_PRECISION] ?? null);
		$check = $this->values[SettingsService::KEY_PROFILE_CHECK];
		self::assertSame('fits', $check['verdict']);
		self::assertFalse($check['committed']);
		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE_CHECK_PENDING, $this->values);
		self::assertIsArray($answer['result']);
		self::assertFalse($answer['result']['committed']);
	}

	public function testAnUnreadableInForceNeverCommits(): void {
		$this->pending();
		$this->values[SettingsService::KEY_PROFILE_CHECK_PENDING]['inForce'] = 'economy';
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done());

		$this->service()->state('admin');

		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE, $this->values);
		self::assertFalse($this->values[SettingsService::KEY_PROFILE_CHECK]['committed']);
	}

	public function testTheSameIdOnRecordIsNotTakenOverTwice(): void {
		$this->pending();
		$this->values[SettingsService::KEY_PROFILE_CHECK] = ['id' => self::ID, 'verdict' => 'fits'];
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done());

		$this->service()->state('admin');

		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE, $this->values);
		self::assertSame(['delete:' . SettingsService::KEY_PROFILE_CHECK_PENDING], $this->writes);
	}

	/** @return array<string, array{array<string, mixed>}> */
	public static function foreignAnswers(): array {
		return [
			'other id' => [['id' => self::OTHER_ID]],
			'other profile' => [['targetProfile' => 'performance']],
			'other precision' => [['targetPrecision' => 'fp32']],
			'still running' => [['state' => 'running', 'verdict' => '']],
			'unknown verdict' => [['verdict' => 'maybe']],
			'malformed id' => [['id' => 'ABCDEF0123456789']],
		];
	}

	/** @param array<string, mixed> $overrides */
	#[DataProvider('foreignAnswers')]
	public function testAFitsOfAnotherProbeSavesNothing(array $overrides): void {
		$this->pending();
		$before = $this->values;
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done($overrides));

		$this->service()->state('admin');

		self::assertSame($before, $this->values);
		self::assertSame([], $this->writes);
	}

	/** @return array<string, array{string, string, array<string, int>}> */
	public static function negativeVerdicts(): array {
		return [
			'narrow' => ['narrow', 'reserve_thin', ['reserve' => 10, 'required' => 400]],
			'nofit' => ['nofit', 'memory_short', ['slots' => 2, 'need' => 900, 'available' => 500]],
		];
	}

	/** @param array<string, int> $numbers */
	#[DataProvider('negativeVerdicts')]
	public function testNarrowAndNofitSaveNothingButAreRemembered(string $verdict, string $cause, array $numbers): void {
		$this->pending();
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done([
			'verdict' => $verdict,
			'cause' => $cause,
			'numbers' => $numbers,
			'fp32Deleted' => true,
		]));
		$this->exApp->expects(self::never())->method('adminGet');

		$this->service()->state('admin');

		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE, $this->values);
		self::assertArrayNotHasKey(SettingsService::KEY_MODEL_PRECISION, $this->values);
		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE_CHECK_PENDING, $this->values);
		$check = $this->values[SettingsService::KEY_PROFILE_CHECK];
		self::assertFalse($check['committed']);
		self::assertSame($verdict, $check['verdict']);
		self::assertSame($cause, $check['cause']);
		self::assertSame($numbers, $check['numbers']);
		self::assertTrue($check['fp32Deleted']);
	}

	public function testAFitsForTheChosenProfileStoresTheConfirmation(): void {
		$this->pending();
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done());
		$this->exApp->expects(self::once())->method('adminGet')->with('/status', 'admin', [])
			->willReturn(['guard' => ['chosen' => 'standard', 'effective' => 'economy', 'token' => self::TOKEN]]);

		$answer = $this->service()->state('admin');

		self::assertSame(self::TOKEN, $this->values[SettingsService::KEY_PROFILE_CONFIRMED]);
		// The token never travels back to the browser.
		self::assertStringNotContainsString(self::TOKEN, (string)json_encode($answer));
	}

	/** @return array<string, array{array<mixed>|null}> */
	public static function statusWithoutConfirmation(): array {
		return [
			'other chosen profile' => [['guard' => ['chosen' => 'performance', 'token' => self::TOKEN]]],
			'token with newline' => [['guard' => ['chosen' => 'standard', 'token' => self::TOKEN . "\n"]]],
			'no guard' => [[]],
			'status silent' => [null],
		];
	}

	/** @param array<mixed>|null $status */
	#[DataProvider('statusWithoutConfirmation')]
	public function testNoConfirmationWithoutAMatchingGuard(?array $status): void {
		$this->pending();
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done());
		$this->exApp->method('adminGet')->willReturn($status);

		$this->service()->state('admin');

		self::assertSame('standard', $this->values[SettingsService::KEY_PROFILE]);
		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE_CONFIRMED, $this->values);
	}

	// -- field judgement ----------------------------------------------------

	public function testUnknownFieldsAreDropped(): void {
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done([
			'state' => 'exploded',
			'step' => '<script>',
			'bytesDone' => -4,
			'bytesTotal' => '10',
		]));

		$answer = $this->service()->state('admin');

		self::assertSame('ok', $answer['code']);
		self::assertSame('', $answer['state']);
		self::assertSame('', $answer['step']);
		self::assertSame(0, $answer['bytesDone']);
		self::assertSame(0, $answer['bytesTotal']);
	}

	public function testUnknownCausesAndNumbersAreDroppedFromTheRecord(): void {
		$this->pending();
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done([
			'verdict' => 'nofit',
			'cause' => 'rm -rf',
			'numbers' => ['slots' => 2, 'need' => -1, 'bogus' => 5, 'available' => '9'],
		]));

		$this->service()->state('admin');

		$check = $this->values[SettingsService::KEY_PROFILE_CHECK];
		self::assertSame('', $check['cause']);
		self::assertSame(['slots' => 2], $check['numbers']);
	}

	// -- stale pending and silent container ---------------------------------

	public function testAStalePendingIsRecordedAsInterrupted(): void {
		$this->pending('standard', 'int8', self::NOW - 3001);
		$this->stateAnswer(ExAppService::ADMIN_UNREACHABLE, null);

		$answer = $this->service()->state('admin');

		self::assertSame('unreachable', $answer['code']);
		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE_CHECK_PENDING, $this->values);
		$check = $this->values[SettingsService::KEY_PROFILE_CHECK];
		self::assertSame('nofit', $check['verdict']);
		self::assertSame('interrupted', $check['cause']);
		self::assertFalse($check['committed']);
		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE, $this->values);
	}

	public function testAFreshPendingSurvivesASilentContainer(): void {
		$this->pending('standard', 'int8', self::NOW - 2999);
		$before = $this->values;
		$this->stateAnswer(ExAppService::ADMIN_UNREACHABLE, null);

		$this->service()->state('admin');

		self::assertSame($before, $this->values);
	}

	public function testAnOldContainerIsUnsupported(): void {
		$this->stateAnswer(ExAppService::ADMIN_MISSING, null);

		$answer = $this->service()->state('admin');

		self::assertSame('unsupported', $answer['code']);
		self::assertNull($answer['result']);
	}

	public function testSettleWithoutPendingDoesNotAskTheContainer(): void {
		$this->exApp->expects(self::never())->method('adminState');

		$this->service()->settle('admin');

		self::assertSame([], $this->writes);
	}

	public function testSettleTakesAFitsOverWithoutAnyAnswer(): void {
		$this->pending();
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done());
		$this->exApp->method('adminGet')->willReturn(null);

		$this->service()->settle('admin');

		self::assertSame('standard', $this->values[SettingsService::KEY_PROFILE]);
		self::assertTrue($this->values[SettingsService::KEY_PROFILE_CHECK]['committed']);
	}

	public function testAnUnreadablePendingIsForgotten(): void {
		$this->values[SettingsService::KEY_PROFILE_CHECK_PENDING] = ['id' => '../etc', 'profile' => 'standard'];
		$this->stateAnswer(ExAppService::ADMIN_OK, $this->done());

		$this->service()->state('admin');

		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE_CHECK_PENDING, $this->values);
		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE, $this->values);
	}
}
