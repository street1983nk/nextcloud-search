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
 * The minor step from 1.1.0 to 1.2.0, and the recorded version it invalidates.
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
 * where it was. An instance going from 1.1.0 to 1.2.0 compares 1.2 against a
 * 1.1 that describes a container from before the update, finds a drift that
 * need not exist, and answers every search with no hits until somebody happens
 * to open the settings page. That is not reasoned, it is measured: the upgrade
 * proof of deploy-harp.yml went from 1.0.3 to 1.1.0 with both halves moved, and
 * every one of the thirty canary searches came back empty with
 * ``companion 1.1.0, backend 1.0.3`` in the log while AppAPI reported the
 * container as 1.1.0. The migration of 11.09.2026,
 * Version001100Date20260911000000, is what closed that for the previous minor,
 * and this file is the same statement for this one.
 *
 * **Every minor step needs a migration of this shape, as long as the recorded
 * version is maintained the way it is today.** That sentence is inherited from
 * the class comment of the file above rather than copied out of a plan, and it
 * is the flip side of DI-11-06: the point was decided on the record in plan
 * 16-04 as passed on with a verdict and an address (its own milestone after
 * v1.2), and passing it on is precisely what obliges this file to exist. The
 * cheap repair is this migration once per minor; the expensive one is carrying
 * the version in the answer the search already fetches, which is a protocol
 * change in both halves and not a thing to rush before a release.
 *
 * So the value is dropped, and deliberately not replaced by a guess. Writing
 * the version of this half in here would be the one change that empties the
 * guarantee: an instance whose container really is a minor behind would be told
 * the halves agree, and the search would then answer with hits that neither
 * half can vouch for. An absent value is not a guess. It is the documented
 * state driftOnRecord() already returns null for, and it is the state every
 * installation is in until it first opens the settings page.
 *
 * Nothing is asked of the container here. A migration runs inside occ upgrade,
 * with the instance in maintenance mode, without a logged in user, and at a
 * moment when AppAPI may be restarting the container: adminGet() needs a user
 * id and a proxy request needs a container that answers, so a migration that
 * waits on either can turn an app update into a failed one. The next answer of
 * the container settles the question, and it settles it with a measurement
 * instead of an assumption.
 *
 * What stays open and is not repaired here is what stayed open the last time:
 * between this update and the first look at the settings page, the search has
 * no recorded version and therefore no drift verdict. That is DI-11-06, and its
 * address is the milestone after v1.2.
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001200Date20260921000000 extends SimpleMigrationStep {
	public function __construct(
		private IAppConfig $appConfig,
	) {
	}

	/**
	 * After the schema, because this touches data and no table.
	 *
	 * Guarded so a second run is a no-op, for the reason the migration of
	 * 04.09.2026 states and the one of 11.09.2026 repeats: Nextcloud can
	 * replay a migration after a failed upgrade, and one that throws on the
	 * second run turns a recoverable upgrade into a broken instance. Here
	 * the guard costs nothing anyway, since a key that is gone stays gone.
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
