<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\LockingCheckService;
use OCP\IConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The detection behind the hint about file locking that cannot keep the
 * background jobs apart (plan 45-25, I-45-23-02 to I-45-23-05).
 *
 * The system configuration is a stub that knows a map of system values and
 * hands back the default for every key it does not know, the way IConfig
 * does for a config.php without the entry.
 */
#[CoversClass(LockingCheckService::class)]
final class LockingCheckServiceTest extends TestCase {
	/** @param array<string, mixed> $values */
	private function service(array $values): LockingCheckService {
		$config = $this->createMock(IConfig::class);
		$config->method('getSystemValueBool')->willReturnCallback(
			static fn (string $key, bool $default = false): bool => is_bool($values[$key] ?? null) ? $values[$key] : $default,
		);
		$config->method('getSystemValue')->willReturnCallback(
			static fn (string $key, mixed $default = ''): mixed => array_key_exists($key, $values) ? $values[$key] : $default,
		);

		return new LockingCheckService($config);
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
		self::assertTrue($this->service(['memcache.locking' => '\oc\memcache\apcu'])->unshared());
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
}
