<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Controller\ProfileController;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Http;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IAppConfig;
use OCP\IRequest;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The profile route of path B (D-24-01), what the method does once it runs.
 *
 * Gate B in backend/tests holds the attributes and the position of
 * rejectForeignCaller; this suite holds the answers: the own backend gets a
 * name out of the closed set, a foreign ExApp gets a 403 without one, a
 * value that arrived through occ and is not a profile turns into economy
 * without appearing in the log, and a read that throws answers 500 without a
 * name, so the container keeps the last known profile (D-24-02).
 *
 * Since phase 25 the same answer carries the model precision (D-25-02), and
 * a stored precision outside the set travels as null instead of the default
 * (D-25-03), so the container keeps the last known one.
 *
 * SettingsService is final, so it is not doubled. A real one is built on a
 * doubled IAppConfig, which is the seam the value arrives through anyway.
 */
#[CoversClass(ProfileController::class)]
final class ProfileControllerTest extends TestCase {
	private IAppConfig&MockObject $appConfig;
	private LoggerInterface&MockObject $logger;

	protected function setUp(): void {
		parent::setUp();

		$this->appConfig = $this->createMock(IAppConfig::class);
		$this->logger = $this->createMock(LoggerInterface::class);
	}

	/**
	 * The app id of the container, read out of the class instead of copied,
	 * for the same reason as in GatewayControllerTest.
	 */
	private function backendAppId(): string {
		$value = (new \ReflectionClass(Application::class))->getConstant('BACKEND_APP_ID');

		self::assertIsString($value, 'BACKEND_APP_ID is gone or is no longer a string');

		return $value;
	}

	/**
	 * Stage the stored values; null means the key is absent.
	 *
	 * One map over both keys, because the route reads both in one request and
	 * a double that answered the profile for every key would hand the profile
	 * name out as a precision.
	 */
	private function stored(?string $profile, ?string $precision = null, ?string $confirmed = null): void {
		// An absent key is what IAppConfig answers with the default it was
		// handed, so the double returns exactly that.
		$values = array_filter(
			[
				SettingsService::KEY_PROFILE => $profile,
				SettingsService::KEY_MODEL_PRECISION => $precision,
				SettingsService::KEY_PROFILE_CONFIRMED => $confirmed,
			],
			static fn (?string $value): bool => $value !== null,
		);
		$this->appConfig->method('getValueString')->willReturnCallback(
			static fn (string $app, string $key, string $default = ''): string => $values[$key] ?? $default,
		);
	}

	private function controller(string $callerAppId): ProfileController {
		$request = $this->createMock(IRequest::class);
		$request->method('getHeader')->willReturnCallback(
			static fn (string $name): string => $name === 'EX-APP-ID' ? $callerAppId : '',
		);

		$settings = new SettingsService($this->appConfig, $this->logger, $this->createMock(ITimeFactory::class));

		return new ProfileController($request, $settings, $this->logger);
	}

	public function testTheBackendGetsTheStoredProfile(): void {
		$this->stored('standard');

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['profile' => 'standard', 'precision' => 'int8', 'confirmed' => null], $response->getData());
	}

	public function testAMissingKeyMeansEconomy(): void {
		$this->stored(null);

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['profile' => 'economy', 'precision' => 'int8', 'confirmed' => null], $response->getData());
	}

	public function testAValueOutsideTheSetMeansEconomyAndIsNotLogged(): void {
		$this->stored('turbo');

		$this->logger->expects(self::once())->method('warning')->with(
			self::isString(),
			self::callback(static function (array $context): bool {
				return !str_contains(json_encode($context, JSON_THROW_ON_ERROR), 'turbo');
			}),
		);

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['profile' => 'economy', 'precision' => 'int8', 'confirmed' => null], $response->getData());
	}

	public function testAFailedReadAnswersAsAFailureWithoutAProfileName(): void {
		// D-24-02: the container keeps the LAST KNOWN profile when a read
		// fails. A 200 with a default here would look like a valid answer and
		// downgrade a running standard or performance box, so the failure has
		// to travel as a failure.
		$this->appConfig->method('getValueString')->willThrowException(new \RuntimeException('storage gone'));

		$this->logger->expects(self::once())->method('error')->with(
			self::isString(),
			self::arrayHasKey('exception'),
		);

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_INTERNAL_SERVER_ERROR, $response->getStatus());
		$data = $response->getData();
		self::assertIsArray($data);
		self::assertArrayNotHasKey('profile', $data);
		self::assertArrayNotHasKey('precision', $data);
		foreach ([...SettingsService::PROFILES, ...SettingsService::PRECISIONS] as $name) {
			self::assertStringNotContainsString($name, json_encode($data, JSON_THROW_ON_ERROR));
		}
	}

	public function testAForeignExAppIsRefusedWithoutAProfileName(): void {
		$this->stored('performance', 'fp32');
		$this->appConfig->expects(self::never())->method('getValueString');

		$response = $this->controller('some_other_backend')->profile();

		self::assertSame(Http::STATUS_FORBIDDEN, $response->getStatus());
		$data = $response->getData();
		self::assertIsArray($data);
		self::assertArrayNotHasKey('profile', $data);
		foreach (SettingsService::PROFILES as $name) {
			self::assertStringNotContainsString($name, json_encode($data, JSON_THROW_ON_ERROR));
		}
	}

	// -- the precision key (MOD-02, D-25-02) ----------------------------------

	public function testTheStoredPrecisionTravelsNextToTheProfile(): void {
		$this->stored('standard', 'fp32');

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['profile' => 'standard', 'precision' => 'fp32', 'confirmed' => null], $response->getData());
	}

	/** @return array<string, array{string}> */
	public static function precisionsOutsideTheSet(): array {
		return [
			'wrong case' => ['FP32'],
			'unknown precision' => ['fp16'],
			'empty' => [''],
		];
	}

	#[DataProvider('precisionsOutsideTheSet')]
	public function testAPrecisionOutsideTheSetIsNullAndIsNotLogged(string $stored): void {
		// null and not the default, the one deliberate difference to the profile
		// (D-25-03): a typo in occ must not turn a fp32 box into int8, which
		// would mean a reindex and the deletion of the fp32 model. The container
		// keeps its last known precision on null.
		$this->stored('standard', $stored);

		$this->logger->expects(self::once())->method('warning')->with(
			self::isString(),
			self::callback(static function (array $context) use ($stored): bool {
				return $stored === '' || !str_contains(json_encode($context, JSON_THROW_ON_ERROR), $stored);
			}),
		);

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['profile' => 'standard', 'precision' => null, 'confirmed' => null], $response->getData());
	}

	// -- the confirmation token (D-26-04) --------------------------------------

	private const TOKEN = '0123456789abcdef0123456789abcdef';

	public function testAStoredTokenTravelsAsConfirmed(): void {
		$this->stored('standard', 'int8', self::TOKEN);
		$this->logger->expects(self::never())->method('warning');

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(
			['profile' => 'standard', 'precision' => 'int8', 'confirmed' => self::TOKEN],
			$response->getData(),
		);
	}

	public function testNoStoredTokenIsNullWithoutAWarning(): void {
		// The ordinary state of every instance whose guard never lowered
		// anything, so it must not count as a rejection.
		$this->stored('standard');
		$this->logger->expects(self::never())->method('warning');

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		$data = $response->getData();
		self::assertIsArray($data);
		self::assertArrayHasKey('confirmed', $data);
		self::assertNull($data['confirmed']);
	}

	/** @return array<string, array{string}> */
	public static function tokensOutsideTheForm(): array {
		return [
			'not hex' => ['XYZ'],
			'31 characters' => [substr(self::TOKEN, 0, 31)],
			'33 characters' => [self::TOKEN . '0'],
			'upper case' => [strtoupper(self::TOKEN)],
			'trailing newline' => [self::TOKEN . "\n"],
		];
	}

	#[DataProvider('tokensOutsideTheForm')]
	public function testATokenOutsideTheFormIsNullAndIsNotLogged(string $stored): void {
		// T-26-05: a token can only lift a lowering, so anything that is not
		// exactly 32 lowercase hex falls on the side that keeps the lowering.
		$this->stored('standard', 'int8', $stored);

		$this->logger->expects(self::once())->method('warning')->with(
			self::isString(),
			self::callback(static function (array $context) use ($stored): bool {
				return !str_contains(json_encode($context, JSON_THROW_ON_ERROR), trim($stored));
			}),
		);

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(
			['profile' => 'standard', 'precision' => 'int8', 'confirmed' => null],
			$response->getData(),
		);
	}

	public function testAFailedReadCarriesNoToken(): void {
		$this->appConfig->method('getValueString')->willThrowException(new \RuntimeException('storage gone'));

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_INTERNAL_SERVER_ERROR, $response->getStatus());
		self::assertSame(['error' => 'profile unreadable'], $response->getData());
	}

	public function testThePrecisionsAreAClosedSetWithInt8AsDefault(): void {
		self::assertSame(['int8', 'fp32'], SettingsService::PRECISIONS);
		self::assertSame('int8', SettingsService::PRECISION_DEFAULT);
		self::assertNotSame(SettingsService::KEY_PROFILE, SettingsService::KEY_MODEL_PRECISION);
	}
}
