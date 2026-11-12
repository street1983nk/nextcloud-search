<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
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
 * after the update. This step sets the key coverage_per_document_hint
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
 * This file names no class of the app, on purpose (issue #51). An update runs
 * in the process that already loaded the classes of the OLD version, and the
 * autoloader never loads a class twice: a constant that came with this very
 * release is undefined there, and occ app:update died on it in 1.6.3. So the
 * app id, the key, its pending value and the table stand here as literals, and
 * Version001603Date20261108000000Test holds each of them against the constant
 * of the service it mirrors. MigrationSelfContainedTest keeps every later
 * migration to the same rule.
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
	/** Application::APP_ID, as a literal (see the class comment). */
	public const APP_ID = 'findling';

	/** SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT, as a literal. */
	public const HINT_KEY = 'coverage_per_document_hint';

	/** SettingsService::COVERAGE_HINT_PENDING, as a literal. */
	public const HINT_PENDING = 1;

	/** ScanStatsService::TABLE_NAME, as a literal. */
	public const SCAN_STATS_TABLE = 'findling_scan_stats';

	public function __construct(
		private IDBConnection $db,
		private IAppConfig $appConfig,
	) {
	}

	/**
	 * After the schema, because this touches data and no table.
	 */
	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		if ($this->appConfig->getValueInt(self::APP_ID, self::HINT_KEY, 0) !== 0) {
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
			self::APP_ID,
			self::HINT_KEY,
			self::HINT_PENDING,
		);
		$output->info('the per document hint is pending until the first complete count');
	}

	/** Whether findling_scan_stats holds at least one row; one row is enough. */
	private function hasScanRow(): bool {
		$qb = $this->db->getQueryBuilder();
		$qb->select('storage_id')
			->from(self::SCAN_STATS_TABLE)
			->setMaxResults(1);

		$result = $qb->executeQuery();
		try {
			return is_array($result->fetch());
		} finally {
			$result->closeCursor();
		}
	}
}
