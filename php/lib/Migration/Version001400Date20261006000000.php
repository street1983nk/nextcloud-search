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
 * The minor step from 1.3 to 1.4.0, and the recorded version it invalidates.
 *
 * ``backend_app_version`` is the answer the container gave the last time
 * anything asked it, and the only thing that ever asks is the settings page
 * (AdminViewService reads ``GET /status`` and hands it to
 * ExAppService::lockstep, which records it). ExAppService::driftOnRecord()
 * compares that number against the version of this half, and SearchService
 * refuses to answer at all while major or minor disagree, because a hit across
 * a protocol break would be a guess dressed up as a finding.
 *
 * Updating this half moves one side of that comparison and leaves the other
 * where it was. An instance going from 1.3.2 to 1.4.0 compares 1.4 against a
 * 1.3 that describes a container from before the update, finds a drift that
 * need not exist, and answers every search with no hits until somebody happens
 * to open the settings page. That was measured once, on the step from 1.0.3 to
 * 1.1.0, and Version001200Date20260921000000 and
 * Version001300Date20260924000000 closed it for the two minors after that. This
 * file is the same statement for this one.
 *
 * **Every minor step needs a migration of this shape, as long as the recorded
 * version is maintained the way it is today.** The sentence is inherited from
 * the class comment of Version001300Date20260924000000, and it stays the flip
 * side of DI-11-06: the cheap repair is this migration once per minor, the
 * expensive one is carrying the version in the answer the search already
 * fetches, which is a protocol change in both halves.
 *
 * So the value is dropped, and deliberately not replaced by a guess. Writing
 * the version of this half in here would tell an instance whose container
 * really is a minor behind that the halves agree, and the search would then
 * answer with hits that neither half can vouch for. An absent value is the
 * documented state driftOnRecord() already returns null for.
 *
 * Nothing is asked of the container here. A migration runs inside occ upgrade,
 * with the instance in maintenance mode, without a logged in user, and at a
 * moment when AppAPI may be restarting the container, so a migration that waits
 * on the container can turn an app update into a failed one. The second look
 * that 1.4.0 brings with it, the recheck of every failed(corrupt) and
 * skipped(unreadable) verdict under the readers of this release (D-29-10, plan
 * 29-09), is deliberately not here either: it runs in the container, after the
 * update is over and the instance is back, and it is marked done there under
 * its own mark. This file stays what it is: a few lines that drop one key.
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001400Date20261006000000 extends SimpleMigrationStep {
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
