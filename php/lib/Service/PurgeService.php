<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\BackgroundJobs\SchedulerJob;
use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCA\Findling\BackgroundJobs\SubtreeExpandJob;
use OCA\Findling\Db\QueueMapper;
use OCP\BackgroundJob\IJobList;
use OCP\IAppConfig;
use OCP\IDBConnection;
use OCP\Migration\IOutput;

/**
 * The ONE routine that removes what this app owns in the Nextcloud database.
 *
 * That is a promise and not a description. Two callers reach this class, the
 * uninstall repair step and the occ command, and neither of them holds a line
 * of removal logic of its own. A second implementation inside a command would
 * be a second truth about what uninstalling means, and the two would drift
 * apart on the day somebody adds a fourth table to only one of them.
 *
 * What it owns: three tables, all app config values of this app, and three
 * background jobs. What it does not touch: the index volume of the container
 * (that belongs to AppAPI and goes with --rm-data), the pulled image, and the
 * files of the users. The read only invariant of this project has its own gate
 * and this class does not soften it.
 *
 * The order below is not a matter of taste. The jobs go first, because a job
 * left in the list after its tables are gone runs in the next cron pass and
 * fails there. The app config goes last, because removing it as a whole also
 * removes "enabled", "installed_version" and the intent mark itself, and after
 * that point nothing here could read a setting anymore.
 *
 * Between the two sits the migration bookkeeping, and it is there because of a
 * measurement and not because of a theory. Without it the rows of this app in
 * the core table "migrations" survive a removal, which is a leftover on its
 * own, and the next enable of the app then finds a schema that Nextcloud
 * believes to be up to date while its tables are gone. The app comes back
 * broken and no occ command puts it right. Removing those rows is what makes
 * a re enable run the migrations again, and it is why this class touches one
 * table that does not belong to it, by row and scoped to this app id.
 *
 * Every removal of a table is preceded by tableExists. That is a requirement
 * and not caution: the repair step runs on every disable of the app, so this
 * routine runs again and again, and it may run before the migrations have ever
 * created a table.
 */
class PurgeService {
	/**
	 * The three background jobs of this app.
	 *
	 * SubtreeExpandJob is in this list although IndexCommand::restart() does
	 * not know it. A restart only has to clear what carries a cursor, an
	 * uninstall has to leave nothing behind that Nextcloud would try to load.
	 */
	private const JOBS = [
		SchedulerJob::class,
		StorageCrawlJob::class,
		SubtreeExpandJob::class,
	];

	/**
	 * The three tables of this app, out of the constants that create them.
	 *
	 * Never as a literal. A table name written a second time in this file
	 * would be a name that is right until somebody renames the original, and a
	 * mistyped one here would remove a table that belongs to somebody else.
	 */
	private const TABLES = [
		QueueMapper::TABLE_NAME,
		ScanStatsService::TABLE_NAME,
		FileStateService::TABLE_NAME,
	];

	/**
	 * The core table that records which migration of which app has run.
	 *
	 * It belongs to Nextcloud and not to this app, only the rows carrying this
	 * app id do. There is no public API for them: MigrationService lives under
	 * OC and offers no way to forget a version, so the query builder is the
	 * one dialect neutral way in.
	 */
	private const MIGRATIONS_TABLE = 'migrations';

	public function __construct(
		private IDBConnection $db,
		private IJobList $jobList,
		private IAppConfig $appConfig,
	) {
	}

	/**
	 * What a removal would take with it, without taking anything.
	 *
	 * @return array{jobs: array<string, bool>, tables: array<string, bool>, migrations: int, settings: int}
	 */
	public function plan(): array {
		$jobs = [];
		foreach (self::JOBS as $job) {
			$jobs[$job] = $this->jobList->has($job, null);
		}

		$tables = [];
		foreach (self::TABLES as $table) {
			$tables[$table] = $this->db->tableExists($table);
		}

		return [
			'jobs' => $jobs,
			'tables' => $tables,
			'migrations' => $this->countMigrations(),
			'settings' => count($this->appConfig->getKeys(Application::APP_ID)),
		];
	}

	/**
	 * Remove it, and report what was actually there to remove.
	 *
	 * The same raster plan() returns, so a caller can print the announcement
	 * and the outcome through one formatter. A second run finds nothing left
	 * and reports false everywhere, which is what idempotent looks like from
	 * the outside.
	 *
	 * @return array{jobs: array<string, bool>, tables: array<string, bool>, migrations: int, settings: int}
	 */
	public function run(?IOutput $output = null): array {
		$jobs = [];
		foreach (self::JOBS as $job) {
			$present = $this->jobList->has($job, null);
			if ($present) {
				$this->jobList->remove($job);
				$output?->info(sprintf('Findling removed the background job %s.', $job));
			}
			$jobs[$job] = $present;
		}

		$tables = [];
		foreach (self::TABLES as $table) {
			// tableExists before every single removal, for the reason in the
			// class docblock: this runs on every disable and possibly before
			// the migrations ever ran.
			if (!$this->db->tableExists($table)) {
				$tables[$table] = false;
				continue;
			}

			$this->db->dropTable($table);
			$output?->info(sprintf('Findling removed the table %s.', $table));
			$tables[$table] = true;
		}

		$migrations = $this->forgetMigrations();
		if ($migrations > 0) {
			$output?->info(sprintf('Findling removed %d migration records, so a later install starts from an empty schema.', $migrations));
		}

		$settings = count($this->appConfig->getKeys(Application::APP_ID));
		$this->appConfig->deleteApp(Application::APP_ID);
		if ($settings > 0) {
			$output?->info(sprintf('Findling removed %d of its settings.', $settings));
		}

		return [
			'jobs' => $jobs,
			'tables' => $tables,
			'migrations' => $migrations,
			'settings' => $settings,
		];
	}

	/**
	 * How many migration records of this app the core table still holds.
	 */
	private function countMigrations(): int {
		if (!$this->db->tableExists(self::MIGRATIONS_TABLE)) {
			return 0;
		}

		$query = $this->db->getQueryBuilder();
		$query->select($query->func()->count('*', 'records'))
			->from(self::MIGRATIONS_TABLE)
			->where($query->expr()->eq('app', $query->createNamedParameter(Application::APP_ID)));

		$result = $query->executeQuery();
		$count = (int)$result->fetchOne();
		$result->closeCursor();

		return $count;
	}

	/**
	 * Forget that the migrations of this app ever ran, and say how many rows
	 * that was. Scoped to this app id, so no other app forgets anything.
	 */
	private function forgetMigrations(): int {
		$records = $this->countMigrations();
		if ($records === 0) {
			return 0;
		}

		$query = $this->db->getQueryBuilder();
		$query->delete(self::MIGRATIONS_TABLE)
			->where($query->expr()->eq('app', $query->createNamedParameter(Application::APP_ID)));
		$query->executeStatement();

		return $records;
	}
}
