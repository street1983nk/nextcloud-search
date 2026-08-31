<?php

declare(strict_types=1);

namespace OCA\Findling\Repair;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\BackgroundJobs\SchedulerJob;
use OCP\BackgroundJob\IJobList;
use OCP\IAppConfig;
use OCP\Migration\IOutput;
use OCP\Migration\IRepairStep;
use Psr\Log\LoggerInterface;

/**
 * The one thing that has to happen by itself: after the installation, the
 * first index starts.
 *
 * Zero config is not a promise about the settings dialog, it is a promise that
 * nobody has to know a command. This step is registered under
 * <repair-steps><install> and puts the scheduler into the job list, once.
 *
 * The mark in the app config is what makes it once. Disabling and enabling the
 * app runs the install steps again, and without the mark that would queue a
 * full crawl of every mount every time an admin toggles the app while
 * debugging something else.
 *
 * This step never throws. A repair step that fails takes the installation of
 * the app down with it, and "the search app refuses to install" is a far worse
 * outcome than "the first index has to be started with occ findling:index
 * --restart", which is exactly what the log line below says.
 */
class AppInstallStep implements IRepairStep {
	/**
	 * Set once the scheduler has been queued for the first time. The occ
	 * command deletes it in order to allow a deliberate rebuild.
	 */
	public const FIRST_INDEX_SCHEDULED = 'first_index_scheduled';

	public function __construct(
		private IJobList $jobList,
		private IAppConfig $appConfig,
		private LoggerInterface $logger,
	) {
	}

	public function getName(): string {
		return 'Schedule the first index of Findling';
	}

	public function run(IOutput $output): void {
		try {
			if ($this->appConfig->getValueBool(Application::APP_ID, self::FIRST_INDEX_SCHEDULED)) {
				$output->info('Findling has already scheduled its first index, leaving it alone.');
				return;
			}

			$this->jobList->add(SchedulerJob::class);
			$this->appConfig->setValueBool(Application::APP_ID, self::FIRST_INDEX_SCHEDULED, true);

			$output->info('Findling will start indexing with the next run of the background jobs.');
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not schedule the first index during the installation', ['exception' => $e]);
			$output->warning('Findling could not schedule its first index. Run "occ findling:index --restart" to start it by hand.');
		}
	}
}
