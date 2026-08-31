<?php

declare(strict_types=1);

namespace OCA\Findling\BackgroundJobs;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\BackgroundJob\QueuedJob;
use OCP\IAppConfig;
use Psr\Log\LoggerInterface;

/**
 * Runs once and turns the mount list into one crawl job per mount.
 *
 * This is the job the repair step queues after the installation, and the job
 * `occ findling:index --restart` queues again. It does no work itself, which
 * is deliberate: enumerating mounts is cheap and bounded, walking them is
 * neither, and mixing the two would put an unbounded amount of work into a
 * single cron slot.
 *
 * Being a QueuedJob, it takes itself out of the job list before it runs, so a
 * failure inside it does not leave a job behind that tries again forever.
 */
class SchedulerJob extends QueuedJob {
	/**
	 * Timestamp of the last time a job of this app was actually executed.
	 *
	 * A background job only runs when the cron of the instance runs. With the
	 * default setting AJAX that happens while someone is clicking around in
	 * the web interface and not otherwise, so an instance can look like the
	 * first index is broken when in truth nothing ever ran. The status page of
	 * phase 4 shows this value, but it has to be collected from the first
	 * release on, because a timestamp cannot be reconstructed afterwards.
	 */
	public const LAST_JOB_RUN = 'last_job_run';

	public function __construct(
		ITimeFactory $time,
		private IJobList $jobList,
		private StorageService $storageService,
		private IAppConfig $appConfig,
		private LoggerInterface $logger,
	) {
		parent::__construct($time);
	}

	protected function run($argument): void {
		$mounts = 0;

		foreach ($this->storageService->getMounts() as $mount) {
			$this->jobList->add(StorageCrawlJob::class, [
				'storage_id' => (int)$mount['storage_id'],
				'root_id' => (int)$mount['root_id'],
				'overridden_root' => (int)$mount['overridden_root'],
				'last_file_id' => 0,
			]);
			$mounts++;
		}

		$this->appConfig->setValueInt(Application::APP_ID, self::LAST_JOB_RUN, $this->time->getTime());

		$this->logger->info('Findling: scheduled the crawl of every mount', ['mounts' => $mounts]);
	}
}
