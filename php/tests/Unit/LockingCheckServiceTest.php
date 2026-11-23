<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\LockingCheckService;
use OCP\IConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The detection behind the hint about file locking that cannot keep the
 * background jobs apart (plan 45-25, I-45-23-02 to I-45-23-05), with the class
 * check of the memcache factory (plan 45-26, I-45-25-01).
 *
 * The system configuration is a stub that knows a map of system values and
 * hands back the default for every key it does not know, the way IConfig
 * does for a config.php without the entry. The class check is always a test
 * double, never the real class_exists: by default one that behaves like the
 * classmap autoloader of Composer before the class was first loaded, where
 * the case of the name counts. No case hangs on a real class of OC.
 */
#[CoversClass(LockingCheckService::class)]
final class LockingCheckServiceTest extends TestCase {
	/** @var list<string> the names the spying class check was asked about */
	private array $asked = [];

	/** @param array<string, mixed> $values */
	private function service(array $values, ?\Closure $classExists = null): LockingCheckService {
		$config = $this->createMock(IConfig::class);
		$config->method('getSystemValueBool')->willReturnCallback(
			static fn (string $key, bool $default = false): bool => is_bool($values[$key] ?? null) ? $values[$key] : $default,
		);
		$config->method('getSystemValue')->willReturnCallback(
			static fn (string $key, mixed $default = ''): mixed => array_key_exists($key, $values) ? $values[$key] : $default,
		);

		// Like the classmap of Composer before the first load: the case counts.
		$classExists ??= static fn (string $class): bool => in_array(ltrim($class, '\\'), LockingCheckService::UNSHARED_CLASSES, true);

		return new LockingCheckService($config, $classExists);
	}

	/** A class check that records what it was asked and finds every class. */
	private function spy(): \Closure {
		return function (string $class): bool {
			$this->asked[] = $class;

			return true;
		};
	}

	public function testDefaultLockingIsShared(): void {
		// Neither entry in config.php: Nextcloud locks in the database, which
		// cron and the web server share.
		self::assertFalse($this->service([])->unshared());
	}

	public function testSwitchedOffFileLockingIsLeftToTheNextcloudCheck(): void {
		// NoopLockingProvider: the setup check "Transactional File Locking" of
		// Nextcloud already reports it as an error with its own remedy.
		self::assertFalse($this->service(['filelocking.enabled' => false])->unshared());
		self::assertFalse($this->service([
			'filelocking.enabled' => false,
			'memcache.locking' => '\OC\Memcache\APCu',
		])->unshared());
	}

	public function testApcuAsTheLockingCacheIsUnshared(): void {
		self::assertTrue($this->service(['memcache.locking' => '\OC\Memcache\APCu'])->unshared());
		self::assertTrue($this->service(['memcache.locking' => 'OC\Memcache\APCu'])->unshared());
		self::assertTrue($this->service([
			'filelocking.enabled' => true,
			'memcache.locking' => '\OC\Memcache\APCu',
		])->unshared());
	}

	public function testArrayCacheAsTheLockingCacheIsUnshared(): void {
		self::assertTrue($this->service(['memcache.locking' => '\OC\Memcache\ArrayCache'])->unshared());
		self::assertTrue($this->service(['memcache.locking' => 'OC\Memcache\ArrayCache'])->unshared());
	}

	public function testRedisAsTheLockingCacheIsShared(): void {
		self::assertFalse($this->service(['memcache.locking' => '\OC\Memcache\Redis'])->unshared());
		self::assertFalse($this->service(['memcache.locking' => '\OC\Memcache\Memcached'])->unshared());
	}

	public function testAValueThatIsNoStringIsShared(): void {
		self::assertFalse($this->service(['memcache.locking' => 42])->unshared());
		self::assertFalse($this->service(['memcache.locking' => ['\OC\Memcache\APCu']])->unshared());
		self::assertFalse($this->service(['memcache.locking' => null])->unshared());
	}

	public function testALowercaseNameThatNoAutoloaderResolvesIsShared(): void {
		// The factory finds no class under the name, falls back to NullCache,
		// and Server.php locks in the database: the locks are shared.
		self::assertFalse($this->service(['memcache.locking' => '\oc\memcache\apcu'])->unshared());
		self::assertFalse($this->service(['memcache.locking' => 'oc\memcache\arraycache'])->unshared());
	}

	public function testALowercaseNameOfALoadedClassIsUnshared(): void {
		// The class is loaded already (for example because memcache.local is
		// APCu and the factory checks the local cache first), so PHP finds it
		// under any case, and the locks live in APCu or the array.
		$loaded = static fn (string $class): bool => true;

		self::assertTrue($this->service(['memcache.locking' => '\oc\memcache\apcu'], $loaded)->unshared());
		self::assertTrue($this->service(['memcache.locking' => 'oc\memcache\arraycache'], $loaded)->unshared());
	}

	public function testTheClassCheckSeesTheValueAsConfigPhpHoldsIt(): void {
		// The factory checks the raw value and trims the backslash only after.
		self::assertTrue($this->service(['memcache.locking' => '\OC\Memcache\APCu'], $this->spy())->unshared());
		self::assertTrue($this->service(['memcache.locking' => 'OC\Memcache\ArrayCache'], $this->spy())->unshared());

		self::assertSame(['\OC\Memcache\APCu', 'OC\Memcache\ArrayCache'], $this->asked);
	}

	public function testTheClassCheckIsOnlyAskedForAnUnsharedName(): void {
		$spy = $this->spy();

		self::assertFalse($this->service([], $spy)->unshared());
		self::assertFalse($this->service([
			'filelocking.enabled' => false,
			'memcache.locking' => '\OC\Memcache\APCu',
		], $spy)->unshared());
		self::assertFalse($this->service(['memcache.locking' => '\OC\Memcache\Redis'], $spy)->unshared());
		self::assertFalse($this->service(['memcache.locking' => '\OC\Memcache\Memcached'], $spy)->unshared());
		self::assertFalse($this->service(['memcache.locking' => 42], $spy)->unshared());
		self::assertSame([], $this->asked);

		self::assertTrue($this->service(['memcache.locking' => '\OC\Memcache\APCu'], $spy)->unshared());
		self::assertCount(1, $this->asked);
	}
}
