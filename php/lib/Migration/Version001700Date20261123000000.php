<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCP\IAppConfig;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

/**
 * The minor step from 1.6 to 1.7.0: the recorded version it invalidates.
 *
 * This is the statement of Version001400Date20261006000000 for this minor, and
 * its class comment gives the whole reason. In short: ``backend_app_version``
 * is the answer the container gave before the update, and
 * ExAppService::driftOnRecord() compares its major and minor with the version
 * of this half. SearchService refuses to answer while they disagree, so after
 * the update every search came back empty until somebody opened the settings
 * page (measured on 1.0.3 -> 1.1.0: 30 of 30 canary searches empty). So the
 * value is dropped and deliberately not replaced by a guess. **Every minor
 * step needs a migration of this shape, as long as the recorded version is
 * maintained the way it is today.**
 *
 * There is no second half as in Version001500Date20261012000000: 1.7.0 needs no
 * mark for the coverage denominator. The allowlist of StorageService, the way
 * StorageCrawlJob counts and the rules are unchanged; the new list of excluded
 * admin storages is empty after the update, so the same storages are counted;
 * RECOUNT_MIN_INTERVAL_SECONDS (plan 45-23) only decides when a recount round
 * starts, not what it counts. The one time renewal of the refusal streaks runs
 * in the container under the mark refusal_streaks_1_7_0 (plan 45-18).
 *
 * This file names no class of the app, on purpose (issue #51). An update runs
 * in the process that already loaded the classes of the OLD version, and the
 * autoloader never loads a class twice: a constant that came with a later
 * release is undefined there. So the app id and the key stand here as
 * literals, and Version001700Date20261123000000Test holds each of them against
 * the constant it mirrors. MigrationSelfContainedTest keeps every later
 * migration to the same rule.
 *
 * The update proof scripts/ci/update_in_process_proof.sh (job "Store update in
 * one process (issue 51)") plants a recorded version before it swaps the files
 * and demands it gone after every minor step; its control 2 runs the candidate
 * without the migrations of its own release, without this file, and has to
 * fail on exactly that (plan 45-26).
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
class Version001700Date20261123000000 extends SimpleMigrationStep {
	/** Application::APP_ID, as a literal (see the class comment). */
	public const APP_ID = 'findling';

	/** ExAppService::KEY_BACKEND_VERSION, as a literal. */
	public const BACKEND_VERSION_KEY = 'backend_app_version';

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
		$recorded = $this->appConfig->getValueString(self::APP_ID, self::BACKEND_VERSION_KEY, '');
		if ($recorded === '') {
			$output->info('no recorded backend version to drop');

			return;
		}

		$this->appConfig->deleteKey(self::APP_ID, self::BACKEND_VERSION_KEY);
		$output->info(sprintf('dropped the recorded backend version %s, it predates this update', $recorded));
	}
}
