<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\ScanStatsService;
use OCA\Findling\Service\SettingsService;
use OCP\IAppConfig;
use OCP\IDBConnection;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

/**
 * The patch step to 1.6.3: the one time hint after the switch to the per
 * document count (plan 43-06, D-43-06, D-43-12).
 *
 * Since 1.6.3 the coverage figure counts every document once, so on an
 * instance with external storage mounted once per user the figures go down
 * after the update. This step sets SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT
 * to pending on an instance that counted before, and the admin page explains
 * the drop once and lets the hint run out seven days after the first complete
 * count.
 *
 * The signal is a row in findling_scan_stats and not the installed version
 * (assumption A4 of 43-RESEARCH.md): on a fresh installation Nextcloud runs
 * every migration as well, and installed_version is not reliable enough at
 * that moment to tell an update from an installation. A fresh installation has
 * no scan row yet, so it never sees the hint. A table that cannot be read is
 * the same as no row: nothing is set and one warning without a value goes to
 * the output, because a hint is never worth a broken update (T-43-17).
 *
 * Only a read and one appconfig value, no schema step, nothing asked of the
 * container. Guarded so a second run is a no-op: a key that is already set
 * (pending or stamped) stays as it is.
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001603Date20261108000000 extends SimpleMigrationStep {
	public function __construct(
		private IDBConnection $db,
		private IAppConfig $appConfig,
	) {
	}

	/**
	 * After the schema, because this touches data and no table.
	 */
	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		if ($this->appConfig->getValueInt(Application::APP_ID, SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT, 0) !== 0) {
			$output->info('the per document hint is already set');

			return;
		}

		try {
			$counted = $this->hasScanRow();
		} catch (\Throwable) {
			$output->warning('the scan counters could not be read, the per document hint stays off');

			return;
		}

		if (!$counted) {
			$output->info('no scan counters yet, the per document hint stays off');

			return;
		}

		$this->appConfig->setValueInt(
			Application::APP_ID,
			SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT,
			SettingsService::COVERAGE_HINT_PENDING,
		);
		$output->info('the per document hint is pending until the first complete count');
	}

	/** Whether findling_scan_stats holds at least one row; one row is enough. */
	private function hasScanRow(): bool {
		$qb = $this->db->getQueryBuilder();
		$qb->select('storage_id')
			->from(ScanStatsService::TABLE_NAME)
			->setMaxResults(1);

		$result = $qb->executeQuery();
		try {
			return is_array($result->fetch());
		} finally {
			$result->closeCursor();
		}
	}
}
