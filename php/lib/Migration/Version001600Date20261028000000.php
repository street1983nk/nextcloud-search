<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\ExAppService;
use OCP\IAppConfig;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

/**
 * The minor step from 1.5 to 1.6.0: the recorded version it invalidates.
 *
 * This is the statement of Version001400Date20261006000000 for this minor, and
 * its class comment gives the whole reason. In short: ``backend_app_version``
 * is the answer the container gave before the update, SearchService refuses to
 * answer while major or minor disagree with the version of this half, and so
 * the value is dropped and deliberately not replaced by a guess. **Every minor
 * step needs a migration of this shape, as long as the recorded version is
 * maintained the way it is today.**
 *
 * There is no second half as in Version001500Date20261012000000, and no
 * SettingsService::markScanStale() call: Weg C (plan 39-01) groups in
 * ScanStatsService::totals() at read time, so the stored counters stay valid
 * and nothing has to be counted again under a new rule.
 *
 * Nothing is asked of the container here, for the reason given in
 * Version001400Date20261006000000: a migration runs inside occ upgrade, in
 * maintenance mode, possibly while AppAPI restarts the container.
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001600Date20261028000000 extends SimpleMigrationStep {
	public function __construct(
		private IAppConfig $appConfig,
	) {
	}

	/**
	 * After the schema, because this touches data and no table.
	 *
	 * Guarded so a second run is a no-op: Nextcloud can replay a migration
	 * after a failed upgrade, and one that throws on the second run turns a
	 * recoverable upgrade into a broken instance.
	 */
	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		$recorded = $this->appConfig->getValueString(Application::APP_ID, ExAppService::KEY_BACKEND_VERSION, '');
		if ($recorded === '') {
			$output->info('no recorded backend version to drop');

			return;
		}

		$this->appConfig->deleteKey(Application::APP_ID, ExAppService::KEY_BACKEND_VERSION);
		$output->info(sprintf('dropped the recorded backend version %s, it predates this update', $recorded));
	}
}
