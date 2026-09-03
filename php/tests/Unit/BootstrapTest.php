<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCP\App\IAppManager;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\IRootFolder;
use OCP\IAppConfig;
use OCP\IUserManager;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The anti vacuity test of the scaffold, and the first thing that has to be
 * green before any behaviour is worth asserting.
 *
 * It answers one question and no other: does the bootstrap path work. A suite
 * that cannot mock an OCP interface fails inside every real test with a class
 * not found, thirty lines away from the cause, and the cause is always the same
 * one, namely that the server bootstrap did not run. Asking that question once,
 * on its own, is what keeps six behaviour tests from all reporting the same
 * infrastructure defect in six different disguises.
 *
 * The six interfaces below are the exact list docs/testing.md names as the ones
 * the suite has to be able to mock, plus IAppConfig, which the constructor of
 * ExAppService takes and the document does not mention.
 */
#[CoversNothing]
final class BootstrapTest extends TestCase {
	public function testTheServerBootstrapRanAndOcpIsAvailable(): void {
		self::assertTrue(
			interface_exists(IRootFolder::class),
			'OCP is not on the autoload path, so tests/bootstrap.php did not reach the server bootstrap',
		);
	}

	public function testEveryOcpInterfaceTheSuiteDependsOnCanBeDoubled(): void {
		foreach ([
			IRootFolder::class,
			IUserManager::class,
			IAppManager::class,
			IUserMountCache::class,
			IFileAccess::class,
			IAppConfig::class,
			LoggerInterface::class,
		] as $interface) {
			self::assertInstanceOf($interface, $this->createMock($interface));
		}
	}

	public function testTheAutoloaderOfTheAppItselfIsRegistered(): void {
		// The second half of the bootstrap, and a separate question from the one
		// above: the server can be present while the composer autoloader of this
		// app is not, which is what a missing composer install looks like.
		self::assertSame('findling', Application::APP_ID);
		self::assertSame('findling_backend', Application::BACKEND_APP_ID);
	}
}
