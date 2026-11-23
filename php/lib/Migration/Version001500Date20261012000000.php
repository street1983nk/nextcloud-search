<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IAppConfig;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

/**
 * The minor step from 1.4 to 1.5.0: the recorded version it invalidates, and
 * the denominator it marks as behind.
 *
 * The first half is the statement of Version001400Date20261006000000 for this
 * minor, and its class comment gives the whole reason. In short:
 * ``backend_app_version`` is the answer the container gave before the update,
 * SearchService refuses to answer while major or minor disagree with the
 * version of this half, and so the value is dropped and deliberately not
 * replaced by a guess. **Every minor step needs a migration of this shape, as
 * long as the recorded version is maintained the way it is today.**
 *
 * The second half is new with 1.5. This release widens the allowlist of
 * StorageService by mails, ZIP files, Word and Excel 97 to 2003 and HEIC
 * photos (plan 31-10). The denominator of the coverage figure on the settings
 * page counts allowlist types only, and it was counted under the old list. Left
 * alone, it would stay there until the daily recount, and the page would show
 * more files as searchable than it counts as indexable, the class of issue #25.
 * The mark is the one SettingsService::markScanStale() sets for a file
 * operation, written the same way: only on the change from zero to a time.
 * Since 1.7.0 a marked instance waits RECOUNT_MIN_INTERVAL_SECONDS of
 * SettingsService from the start of the last recount round (issue #25, plan
 * 45-23), and on a jump from 1.4.x that start is recorded. So this step also
 * forgets scan_recounted_at, and the round under the allowlist of 1.5 begins
 * in the next run of ScanRecountJob instead of up to six hours later (owner
 * decision m1 on I-45-23-07, plan 45-26). Both writes touch one app config
 * value each and nothing else, so they are as safe in maintenance mode as the
 * delete of the version.
 *
 * This file names no class of the app since plan 45-26 (issue #51,
 * I-45-26-01). It runs exactly on an update from a release before 1.5, in the
 * process that already loaded the classes of that release, and the autoloader
 * never loads a class twice: SettingsService::markScanStale() and
 * SettingsService::KEY_SCAN_RECOUNTED_AT do not exist in 1.3.2, and an update
 * from 1.3.2 died here with "Call to undefined method". So the app id, the
 * keys and the mark stand here as literals, and
 * Version001500Date20261012000000Test holds each of them against the constant
 * it mirrors. Changing a migration that shipped is safe here: Nextcloud runs a
 * migration of an app once (oc_migrations), so every instance that already
 * had it never runs this file again.
 *
 * Nothing is asked of the container here, for the reason given in
 * Version001400Date20261006000000: a migration runs inside occ upgrade, in
 * maintenance mode, possibly while AppAPI restarts the container. The way back
 * for the files of the new types that the instance already holds (D-31-01,
 * FMT-06) is deliberately not here either: it runs in the container after the
 * update, under its own mark recheck_1_5_0 (plan 31-11), and it does not
 * depend on this migration having run.
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001500Date20261012000000 extends SimpleMigrationStep {
	/** Application::APP_ID, as a literal (see the class comment). */
	public const APP_ID = 'findling';

	/** ExAppService::KEY_BACKEND_VERSION, as a literal. */
	public const BACKEND_VERSION_KEY = 'backend_app_version';

	/** SettingsService::KEY_SCAN_STALE_SINCE, as a literal. */
	public const STALE_KEY = 'scan_stale_since';

	/** SettingsService::KEY_SCAN_RECOUNTED_AT, as a literal. */
	public const RECOUNTED_AT_KEY = 'scan_recounted_at';

	public function __construct(
		private IAppConfig $appConfig,
		private ITimeFactory $timeFactory,
	) {
	}

	/**
	 * After the schema, because this touches data and no table.
	 *
	 * Guarded so a second run is a no-op: Nextcloud can replay a migration
	 * after a failed upgrade, and one that throws on the second run turns a
	 * recoverable upgrade into a broken instance. The mark is written only on
	 * the change from zero to a time, and forgetting a key that is gone is a
	 * no-op; at worst a replay costs one more recount round.
	 */
	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		if ($this->appConfig->getValueInt(self::APP_ID, self::STALE_KEY, 0) === 0) {
			$this->appConfig->setValueInt(self::APP_ID, self::STALE_KEY, max(1, $this->timeFactory->getTime()));
		}
		$output->info('marked the coverage denominator for a recount under the allowlist of 1.5');

		$this->appConfig->deleteKey(self::APP_ID, self::RECOUNTED_AT_KEY);
		$output->info('forgot when the last recount started, so the recount under the allowlist of 1.5 starts at once');

		$recorded = $this->appConfig->getValueString(self::APP_ID, self::BACKEND_VERSION_KEY, '');
		if ($recorded === '') {
			$output->info('no recorded backend version to drop');

			return;
		}

		$this->appConfig->deleteKey(self::APP_ID, self::BACKEND_VERSION_KEY);
		$output->info(sprintf('dropped the recorded backend version %s, it predates this update', $recorded));
	}
}
