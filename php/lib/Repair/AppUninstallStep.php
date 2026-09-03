<?php

declare(strict_types=1);

namespace OCA\Findling\Repair;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\PurgeService;
use OCP\IAppConfig;
use OCP\Migration\IOutput;
use OCP\Migration\IRepairStep;
use Psr\Log\LoggerInterface;

/**
 * The counterpart of AppInstallStep, and it carries the same trap in the other
 * direction: Nextcloud does not run this step when the app is removed, it runs
 * it every time the app is disabled.
 *
 * AppManager::disableApp() sets "enabled = no" and then executes
 * repair-steps/uninstall, word for word the same in the server branches 32, 33
 * and 34. And "occ app:remove" is that same disableApp() followed by a routine
 * that only deletes files. So an admin who switches the search off for a night
 * would go through this step, and an unconditional removal here would take the
 * exclusion rules, the size cap, the coverage counters and the whole queue with
 * it. That is a data loss in exactly the area the admin page just started to
 * make trustworthy.
 *
 * Hence the intent mark. Without it this step removes nothing and says so;
 * "occ findling:purge" is the one place where an administrator states the
 * intent, and only then does the step clear anything.
 *
 * The call counter next to it is a measuring instrument and not bookkeeping. A
 * line in the occ output stream is easy to miss, a number is not, so the
 * measurement of when the server really calls this step reads a counter instead
 * of a log. What was measured with it is written down in docs/uninstall.md.
 *
 * This step never breaks off with an error, for the same reason AppInstallStep
 * does not: a repair step that fails takes the whole operation down with it, and
 * "the search app refuses to be disabled" is a far worse outcome than a warning
 * that names the command which finishes the job by hand.
 */
class AppUninstallStep implements IRepairStep {
	/**
	 * The stated intent to remove the data of this app.
	 *
	 * Set by "occ findling:purge --arm", cleared by "--disarm". As long as it is
	 * absent, every disable and every remove of this app leaves the queue, the
	 * counters and the settings exactly where they are.
	 *
	 * The mark is used up by the very run it triggers, because the app config
	 * of this app goes with the removal and the mark lives in it. So a purge
	 * arms once and never twice, and the disable after the disable is a no-op
	 * again.
	 */
	public const PURGE_INTENT = 'purge_intent';

	/**
	 * How often this step has run since it was installed.
	 *
	 * The evidence behind the measurement in docs/uninstall.md: it answers the
	 * question which lifecycle events reach an uninstall repair step, on the
	 * running instance rather than out of the server sources.
	 *
	 * It counts up on every call, including the one that removes everything,
	 * and it disappears with the app config in that same run. A counter that
	 * starts at zero again is therefore the fingerprint of a purge that went
	 * through.
	 */
	public const PURGE_STEP_CALLS = 'purge_step_calls';

	public function __construct(
		private IAppConfig $appConfig,
		private PurgeService $purgeService,
		private LoggerInterface $logger,
	) {
	}

	public function getName(): string {
		return 'Remove the data of Findling, but only where that was asked for';
	}

	public function run(IOutput $output): void {
		try {
			$this->countCall();

			if (!$this->appConfig->getValueBool(Application::APP_ID, self::PURGE_INTENT)) {
				$output->info('Findling keeps its queue, its counters and its settings. "occ findling:purge" is the way to remove them.');

				return;
			}

			$output->info('Findling was asked to remove its data, so its tables, its background jobs and its settings go now.');

			// One routine, and this side holds no removal logic of its own.
			// PurgeService writes one line per item it found, and it takes a
			// second run without anything left to remove.
			$this->purgeService->run($output);
		} catch (\Throwable $e) {
			$this->logger->error('Findling: the uninstall step could not finish', ['exception' => $e]);
			$output->warning('Findling could not finish its uninstall step. Run "occ findling:purge --now" to remove its data by hand.');
		}
	}

	private function countCall(): void {
		$calls = $this->appConfig->getValueInt(Application::APP_ID, self::PURGE_STEP_CALLS);

		$this->appConfig->setValueInt(Application::APP_ID, self::PURGE_STEP_CALLS, $calls + 1);
	}
}
