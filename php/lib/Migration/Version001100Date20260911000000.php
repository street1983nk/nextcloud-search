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
 * The recorded version of the other half does not survive an update of this one.
 *
 * ``backend_app_version`` is the answer the container gave the last time
 * anything asked it, and the only thing that ever asks is the settings page
 * (AdminViewService reads ``GET /status`` and hands it to
 * ExAppService::lockstep, which records it). The value is compared against
 * ownVersion() by ExAppService::driftOnRecord(), and SearchService refuses to
 * answer at all when major or minor disagree, because a hit across a protocol
 * break would be a guess dressed up as a finding.
 *
 * That comparison has two sides, and until now only one of them could move
 * without anybody noticing. Updating this half changes ownVersion() and leaves
 * the recorded number where it was: an instance going from 1.0.3 to 1.1.0
 * compares 1.1 against a 1.0 that describes a container from before the update,
 * finds a drift that need not exist, and answers every search with no hits
 * until somebody happens to open the settings page. Measured, not reasoned: the
 * upgrade proof of deploy-harp.yml went from 1.0.3 to 1.1.0 with both halves
 * moved, and every one of the thirty canary searches came back empty with
 * ``companion 1.1.0, backend 1.0.3`` in the log while AppAPI reported the
 * container as 1.1.0.
 *
 * The five releases before this one were patches, where majorMinor is unchanged
 * and a stale value is harmless, which is why this only surfaces now. **The
 * next minor needs a migration of the same shape**, and that sentence is here
 * rather than in a plan because this file is what somebody reads when they
 * write it.
 *
 * So the value is dropped, and deliberately not replaced by a guess. Writing
 * ownVersion() here would be the one change that empties the guarantee: an
 * instance whose container really is a minor behind would be told the halves
 * agree, and the search would answer with hits that neither half can vouch for.
 * An absent value is not a guess. It is the documented state driftOnRecord()
 * already returns null for, and it is the state every installation is in until
 * it first opens the settings page.
 *
 * Nothing is asked of the container here. A migration runs inside occ upgrade,
 * with the instance in maintenance mode, without a logged in user, and at a
 * moment when AppAPI may be restarting the container: adminGet() needs a user
 * id and a proxy request needs a container that answers, so a migration that
 * waits on either can turn an app update into a failed one. The next answer of
 * the container settles the question, and it settles it with a measurement
 * instead of an assumption.
 *
 * What stays open and is not repaired here: between this update and the first
 * look at the settings page, the search has no recorded version and therefore
 * no drift verdict. Closing that means carrying the version in the answer the
 * search already fetches, which is a protocol change in both halves; it is
 * DI-11-06 with v1.2 as its address, and it is not worth a rushed change three
 * days before a release.
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001100Date20260911000000 extends SimpleMigrationStep {
	public function __construct(
		private IAppConfig $appConfig,
	) {
	}

	/**
	 * After the schema, because this touches data and no table.
	 *
	 * Guarded so a second run is a no-op, for the reason the migration of
	 * 04.09.2026 states: Nextcloud can replay a migration after a failed
	 * upgrade, and one that throws on the second run turns a recoverable
	 * upgrade into a broken instance. Here the guard costs nothing anyway,
	 * since a key that is gone stays gone.
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
