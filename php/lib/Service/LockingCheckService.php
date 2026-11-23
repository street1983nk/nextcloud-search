<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\IConfig;

/**
 * Whether the file locking of this server cannot keep the background jobs of
 * Findling apart (plan 45-25, I-45-23-02 to I-45-23-05, decision l1).
 *
 * The crawl serialises its slices through ILockingProvider: the slice lock
 * and the crawl marker of StorageCrawlJob, read by CrawlAdvanceService for
 * the refill route. Cron and `occ background-job:execute` run in the CLI,
 * the refill route runs in the web server. Their locks only meet when the
 * provider is shared between those processes. Under a locking cache that only
 * one PHP process sees they do not, and a slice can run twice at the same
 * time, silently. Present since 1.4.0 for the marker and since 1.2.0 for the
 * slice lock; the admin page names it and the remedy, see docs/admin-page.md
 * "Dateisperren und Hintergrundjobs".
 *
 * Sources, nextcloud/server stable33, stable34 and stable35 (line numbers in
 * 45-AUDIT.md, "RED und GREEN 45-25", "Locking-Hinweis"):
 *
 * - lib/private/Server.php: `filelocking.enabled` false (default true) gives
 *   the NoopLockingProvider; otherwise the memcache factory builds the
 *   locking cache through createLocking() and, unless that is a NullCache,
 *   a MemcacheLockingProvider on it, else the DBLockingProvider.
 * - lib/private/Memcache/Factory.php: a class in `memcache.locking` that does
 *   not exist, is no IMemcache or whose isAvailable() answers false becomes
 *   a NullCache ("don't fall back since the fallback might not be suitable
 *   for storing lock"), so the server locks in the database; the value is
 *   read with ltrim(..., '\\'). Its comment says that APCu cannot be shared
 *   between PHP instances, CLI and web.
 * - lib/private/Memcache/APCu.php: the store of the process or the FPM pool;
 *   in the CLI only with `apc.enable_cli`, and then one per CLI process.
 * - lib/private/Memcache/ArrayCache.php: an array in the memory of one
 *   request, isAvailable() always true; not even a second request of the
 *   same pool sees those locks.
 *
 * Why only these two classes: Redis, Memcached and the database provider are
 * shared between the CLI and the web server, so they keep the jobs apart.
 * Switched off file locking (NoopLockingProvider) has the same consequence,
 * but Nextcloud reports it itself as an error in its setup check
 * "Transactional File Locking" (apps/settings/lib/SetupChecks/FileLocking.php)
 * with the exact remedy; a second hint here would need a second remedy in the
 * same sentence (45-23, task 1, question (5)). This method answers false for
 * it, and the docs point at that check. MemcacheConfigured.php reads
 * `memcache.locking` only to report the wrong Memcached module, so APCu or
 * ArrayCache as the locking cache is reported by nobody but this class.
 *
 * The rule mirrors the class check of the memcache factory (I-45-25-01, plan
 * 45-26, task 5). The value of `memcache.locking` counts when, after
 * ltrim(..., '\\'), strcasecmp() finds it equal to one of UNSHARED_CLASSES,
 * and then only when class_exists() finds the class under the raw value of
 * config.php in the process of the admin page, as Factory.php checks it:
 * class_exists on the raw value in stable33 line 98, stable34 line 100,
 * stable35 line 101, the ltrim only after it in lines 106, 108, 109. The
 * classmap autoloader of Composer minds the case of a name, so a lower case
 * name of a class that is not loaded yet is no class there; the factory falls
 * back to NullCache, Server.php to the DBLockingProvider, and the locks are
 * shared. A name of a class that is loaded already is found under any case.
 * Not taken over: is_a($lockingCacheClass, IMemcache::class, true) (lines 99,
 * 101, 102), because both names of the list implement IMemcache in all three
 * branches (APCu.php line 13, 14, 15; ArrayCache.php line 12, 12, 13), so it
 * cannot change the answer for them. isAvailable() (lines 100, 102, 103),
 * because it is a static method of the private classes and because it
 * answers for the process that asks, the web server here and not the CLI:
 * APCu::isAvailable() (stable33 lines 111-116, stable34 122-127, stable35
 * 123-128) is false in the CLI without `apc.enable_cli`, the CLI then locks
 * through NullCache in the database while the web server locks in APCu, the
 * locks are apart, and the hint is right; that case stays unshared.
 * ArrayCache::isAvailable() is always true, so there is nothing to mirror.
 *
 * The limits: when the class of the locking cache exists in one SAPI only (for
 * example ext-redis in FPM but not in the CLI), that SAPI falls back through
 * NullCache to the database provider while the other locks in Redis. The
 * locks are apart then, and this method does not see it, because it reads
 * nothing but the system value. When APCu is not available in the web server
 * itself, the web server locks in the database, and whether the CLI locks in
 * an APCu of its own (with `apc.enable_cli`, apart) or in the database as well
 * (shared) the web process cannot see; the hint stands then, at worst
 * needless, never falsely reassuring. And class_exists() answers in the
 * request of the admin page, after the constructor of the factory: when
 * something in this request loads the class only later, a lower case name
 * finds it here though the factory did not; derived, not measured, and rare
 * (in the core of stable35 only Server.php names ArrayCache besides
 * Factory.php, and only without an installation or under PHPUNIT_RUN).
 *
 * The answer is one bool. Nothing is logged and nothing is thrown outward; a
 * value that is no string answers false.
 */
final class LockingCheckService {
	/** The locking caches whose locks only one PHP process sees, without the leading backslash. */
	public const UNSHARED_CLASSES = ['OC\Memcache\APCu', 'OC\Memcache\ArrayCache'];

	public function __construct(
		private IConfig $config,
		// The class check, a seam for the tests: production passes nothing
		// (the dependency injection of Nextcloud fills only the config) and
		// gets the real class_exists() below.
		private ?\Closure $classExists = null,
	) {
	}

	/**
	 * True when file locking is on, its cache is one of UNSHARED_CLASSES and
	 * PHP finds that class under the value of config.php.
	 */
	public function unshared(): bool {
		if (!$this->config->getSystemValueBool('filelocking.enabled', true)) {
			return false;
		}
		$raw = $this->config->getSystemValue('memcache.locking', '');
		if (!is_string($raw)) {
			return false;
		}
		$class = ltrim($raw, '\\');
		foreach (self::UNSHARED_CLASSES as $unshared) {
			if (strcasecmp($class, $unshared) === 0) {
				$classExists = $this->classExists ?? static fn (string $class): bool => class_exists($class);

				return (bool)$classExists($raw);
			}
		}

		return false;
	}
}
