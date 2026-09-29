<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Controller\ProfileSettingsController;
use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\ProbeService;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Http;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IAppConfig;
use OCP\IDateTimeFormatter;
use OCP\IRequest;
use OCP\IUser;
use OCP\IUserSession;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The three admin routes of the profile choice, what they do once they run.
 *
 * Gate B in backend/tests holds the attributes; this suite holds the answers.
 * ProbeService and SettingsService are final, so real ones are built on a
 * doubled IAppConfig that keeps its values in an array and on a double of the
 * admin transport of ExAppService.
 */
#[CoversClass(ProfileSettingsController::class)]
final class ProfileSettingsControllerTest extends TestCase {
	private const ID = '0123456789abcdef';

	private IAppConfig&MockObject $appConfig;
	private LoggerInterface&MockObject $logger;
	private ExAppService&MockObject $exApp;

	/** @var array<string, mixed> */
	private array $values = [];

	/** @var list<string> */
	private array $writes = [];

	private bool $failWrites = false;

	protected function setUp(): void {
		parent::setUp();

		$this->values = [];
		$this->writes = [];
		$this->failWrites = false;
		$this->appConfig = $this->createMock(IAppConfig::class);
		$this->logger = $this->createMock(LoggerInterface::class);
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
				if ($this->failWrites) {
					throw new \RuntimeException('database gone');
				}
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

	private function controller(): ProfileSettingsController {
		$settings = new SettingsService($this->appConfig, $this->logger);
		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturn(1_800_000_000);

		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn('admin');
		$session = $this->createMock(IUserSession::class);
		$session->method('getUser')->willReturn($user);

		return new ProfileSettingsController(
			$this->createMock(IRequest::class),
			new ProbeService($this->exApp, $settings, $this->createMock(IDateTimeFormatter::class), $time, $this->logger),
			$settings,
			$session,
			$this->logger,
		);
	}

	// -- POST admin/profile/check -------------------------------------------

	/** @return array<string, array{string, string}> */
	public static function invalidChecks(): array {
		return [
			'unknown profile' => ['turbo', 'int8'],
			'unknown precision' => ['standard', 'fp16'],
			'empty' => ['', ''],
			'case' => ['STANDARD', 'int8'],
			'fp32 on economy' => ['economy', 'fp32'],
			'economy needs no probe' => ['economy', 'int8'],
		];
	}

	#[DataProvider('invalidChecks')]
	public function testAnInvalidCheckDoesNotReachTheContainer(string $profile, string $precision): void {
		$this->exApp->expects(self::never())->method('adminSend');

		$response = $this->controller()->startCheck($profile, $precision);

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertSame(['started' => false, 'code' => 'invalid'], $response->getData());
		self::assertSame([], $this->writes);
	}

	public function testTheSameProfileFromFp32ToInt8NeedsNoProbe(): void {
		$this->values[SettingsService::KEY_PROFILE] = 'standard';
		$this->values[SettingsService::KEY_MODEL_PRECISION] = 'fp32';
		$this->exApp->expects(self::never())->method('adminSend');

		$response = $this->controller()->startCheck('standard', 'int8');

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
	}

	public function testAProbeTargetStartsUnderTheSessionUser(): void {
		$this->exApp->expects(self::once())->method('adminSend')
			->with('/probe', 'admin', ['profile' => 'performance', 'precision' => 'fp32'])
			->willReturn(['kind' => ExAppService::ADMIN_OK, 'body' => ['id' => self::ID]]);

		$response = $this->controller()->startCheck('performance', 'fp32');

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['started' => true, 'code' => 'started'], $response->getData());
		self::assertSame(self::ID, $this->values[SettingsService::KEY_PROFILE_CHECK_PENDING]['id']);
		// Starting a probe stores no profile.
		self::assertArrayNotHasKey(SettingsService::KEY_PROFILE, $this->values);
	}

	// -- GET admin/profile/check --------------------------------------------

	public function testTheStateIsPassedThrough(): void {
		$this->exApp->method('adminState')->with('/probe/state', 'admin')->willReturn([
			'kind' => ExAppService::ADMIN_OK,
			'body' => ['id' => self::ID, 'state' => 'running', 'step' => 'download', 'bytesDone' => 5, 'bytesTotal' => 9],
		]);

		$response = $this->controller()->checkState();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		$data = $response->getData();
		self::assertSame('ok', $data['code']);
		self::assertSame('running', $data['state']);
		self::assertSame('download', $data['step']);
		self::assertSame(5, $data['bytesDone']);
		self::assertSame(9, $data['bytesTotal']);
		self::assertNull($data['result']);
	}

	// -- POST admin/profile -------------------------------------------------

	public function testEconomyIsStoredWithoutAProbe(): void {
		$this->exApp->expects(self::never())->method('adminSend');

		$response = $this->controller()->saveProfile('economy', 'int8');

		self::assertSame(['saved' => true, 'code' => 'saved'], $response->getData());
		self::assertSame('economy', $this->values[SettingsService::KEY_PROFILE]);
		self::assertSame('int8', $this->values[SettingsService::KEY_MODEL_PRECISION]);
	}

	public function testStayingAtEconomyStoresEconomyAgain(): void {
		$this->values[SettingsService::KEY_PROFILE] = 'economy';

		$response = $this->controller()->saveProfile('economy', 'int8');

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertContains(SettingsService::KEY_PROFILE, $this->writes);
	}

	public function testFp32ToInt8OnTheSameProfileIsStored(): void {
		$this->values[SettingsService::KEY_PROFILE] = 'performance';
		$this->values[SettingsService::KEY_MODEL_PRECISION] = 'fp32';

		$response = $this->controller()->saveProfile('performance', 'int8');

		self::assertSame(['saved' => true, 'code' => 'saved'], $response->getData());
		self::assertSame('int8', $this->values[SettingsService::KEY_MODEL_PRECISION]);
	}

	/** @return array<string, array{string, string}> */
	public static function upwardTargets(): array {
		return [
			'economy to standard' => ['standard', 'int8'],
			'economy to performance' => ['performance', 'int8'],
			'int8 to fp32' => ['standard', 'fp32'],
		];
	}

	#[DataProvider('upwardTargets')]
	public function testAnUpwardTargetNeedsTheProbe(string $profile, string $precision): void {
		$this->values[SettingsService::KEY_PROFILE] = 'economy';

		$response = $this->controller()->saveProfile($profile, $precision);

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertSame(['saved' => false, 'code' => 'probe_required'], $response->getData());
		self::assertSame([], $this->writes);
	}

	/** @return array<string, array{string, string}> */
	public static function invalidSaves(): array {
		return [
			'unknown profile' => ['turbo', 'int8'],
			'unknown precision' => ['economy', 'fp16'],
			'fp32 on economy without fp32 stored' => ['economy', 'fp32'],
		];
	}

	#[DataProvider('invalidSaves')]
	public function testAnInvalidSaveWritesNothing(string $profile, string $precision): void {
		$response = $this->controller()->saveProfile($profile, $precision);

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertSame(['saved' => false, 'code' => 'invalid'], $response->getData());
		self::assertSame([], $this->writes);
	}

	public function testAFailedWriteAnswers500(): void {
		$this->failWrites = true;

		$response = $this->controller()->saveProfile('economy', 'int8');

		self::assertSame(Http::STATUS_INTERNAL_SERVER_ERROR, $response->getStatus());
		self::assertSame(['saved' => false, 'code' => 'failed'], $response->getData());
	}

	// -- Settings/Admin::getForm --------------------------------------------

	/**
	 * The admin form takes a finished probe over before it renders, inside a
	 * catch. Held textually, because the form needs a real AdminViewService,
	 * a final class with twelve collaborators, and the one statement worth
	 * checking here is the order of two lines.
	 */
	public function testTheAdminFormSettlesBeforeItRenders(): void {
		$source = file_get_contents(__DIR__ . '/../../lib/Settings/Admin.php');
		self::assertIsString($source);

		$settle = strpos($source, '$this->probeService->settle(');
		$overview = strpos($source, '$this->view->overview()');
		$catch = strpos($source, 'catch (\Throwable');

		self::assertIsInt($settle);
		self::assertIsInt($overview);
		self::assertIsInt($catch);
		self::assertLessThan($overview, $settle);
		self::assertLessThan($overview, $catch);
		self::assertSame(1, substr_count($source, 'settle('));
	}
}
