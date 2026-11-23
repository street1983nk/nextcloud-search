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
 * The comparison ignores case (strcasecmp) because PHP resolves class names
 * without regard to case and the server loads the value as it stands.
 *
 * The limit: when the class of the locking cache exists in one SAPI only (for
 * example ext-redis in FPM but not in the CLI), that SAPI falls back through
 * NullCache to the database provider while the other locks in Redis. The
 * locks are apart then, and this method does not see it, because it reads
 * nothing but the system value.
 *
 * The answer is one bool. Nothing is logged and nothing is thrown outward; a
 * value that is no string answers false.
 */
final class LockingCheckService {
	/** The locking caches whose locks only one PHP process sees, without the leading backslash. */
	public const UNSHARED_CLASSES = ['OC\Memcache\APCu', 'OC\Memcache\ArrayCache'];

	public function __construct(
		private IConfig $config,
	) {
	}

	/** True when file locking is on and its cache is one of UNSHARED_CLASSES. */
	public function unshared(): bool {
		if (!$this->config->getSystemValueBool('filelocking.enabled', true)) {
			return false;
		}
		$class = $this->config->getSystemValue('memcache.locking', '');
		if (!is_string($class)) {
			return false;
		}
		$class = ltrim($class, '\\');
		foreach (self::UNSHARED_CLASSES as $unshared) {
			if (strcasecmp($class, $unshared) === 0) {
				return true;
			}
		}

		return false;
	}
}
