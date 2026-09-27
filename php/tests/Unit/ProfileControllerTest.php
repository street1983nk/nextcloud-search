<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Controller\ProfileController;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Http;
use OCP\IAppConfig;
use OCP\IRequest;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The profile route of path B (D-24-01), what the method does once it runs.
 *
 * Gate B in backend/tests holds the attributes and the position of
 * rejectForeignCaller; this suite holds the answers: the own backend gets a
 * name out of the closed set, a foreign ExApp gets a 403 without one, and a
 * value that arrived through occ and is not a profile turns into economy
 * without appearing in the log.
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

	/** Stage the stored profile; null means the key is absent. */
	private function storedProfile(?string $value): void {
		// An absent key is what IAppConfig answers with the default it was
		// handed, so the double returns exactly that.
		$this->appConfig->method('getValueString')->willReturnCallback(
			static fn (string $app, string $key, string $default = ''): string => ($value !== null && $key === SettingsService::KEY_PROFILE) ? $value : $default,
		);
	}

	private function controller(string $callerAppId): ProfileController {
		$request = $this->createMock(IRequest::class);
		$request->method('getHeader')->willReturnCallback(
			static fn (string $name): string => $name === 'EX-APP-ID' ? $callerAppId : '',
		);

		$settings = new SettingsService($this->appConfig, $this->logger);

		return new ProfileController($request, $settings, $this->logger);
	}

	public function testTheBackendGetsTheStoredProfile(): void {
		$this->storedProfile('standard');

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['profile' => 'standard'], $response->getData());
	}

	public function testAMissingKeyMeansEconomy(): void {
		$this->storedProfile(null);

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['profile' => 'economy'], $response->getData());
	}

	public function testAValueOutsideTheSetMeansEconomyAndIsNotLogged(): void {
		$this->storedProfile('turbo');

		$this->logger->expects(self::once())->method('warning')->with(
			self::isType('string'),
			self::callback(static function (array $context): bool {
				return !str_contains(json_encode($context, JSON_THROW_ON_ERROR), 'turbo');
			}),
		);

		$response = $this->controller($this->backendAppId())->profile();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['profile' => 'economy'], $response->getData());
	}

	public function testAForeignExAppIsRefusedWithoutAProfileName(): void {
		$this->storedProfile('performance');
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
}
