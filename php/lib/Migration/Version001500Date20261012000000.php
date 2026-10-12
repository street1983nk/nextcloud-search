<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\SettingsService;
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
 * SettingsService::markScanStale() is the same call the event listener makes
 * for a file operation: ScanRecountJob sees the mark within its interval and
 * counts again under the new list. The call writes one app config value and
 * nothing else, so it is as safe in maintenance mode as the delete above it.
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
	public function __construct(
		private IAppConfig $appConfig,
		private SettingsService $settingsService,
	) {
	}

	/**
	 * After the schema, because this touches data and no table.
	 *
	 * Guarded so a second run is a no-op: Nextcloud can replay a migration
	 * after a failed upgrade, and one that throws on the second run turns a
	 * recoverable upgrade into a broken instance. markScanStale() writes only on
	 * the change from zero to a time, so a second call is a no-op as well.
	 */
	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		$this->settingsService->markScanStale();
		$output->info('marked the coverage denominator for a recount under the allowlist of 1.5');

		$recorded = $this->appConfig->getValueString(Application::APP_ID, ExAppService::KEY_BACKEND_VERSION, '');
		if ($recorded === '') {
			$output->info('no recorded backend version to drop');

			return;
		}

		$this->appConfig->deleteKey(Application::APP_ID, ExAppService::KEY_BACKEND_VERSION);
		$output->info(sprintf('dropped the recorded backend version %s, it predates this update', $recorded));
	}
}
