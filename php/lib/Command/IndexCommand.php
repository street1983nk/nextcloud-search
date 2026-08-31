<?php

declare(strict_types=1);

namespace OCA\Findling\Command;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\BackgroundJobs\SchedulerJob;
use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCA\Findling\Repair\AppInstallStep;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\IAppConfig;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Helper\QuestionHelper;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Question\ConfirmationQuestion;

/**
 * The emergency lever: `occ findling:index [--restart|--status]`.
 *
 * Without it, rebuilding the index would mean uninstalling the app, because
 * the repair step only runs at installation time. It is also the cheapest way
 * for the CI and for support to look at the work stock without a database
 * client.
 *
 * Reading is the default and rebuilding needs the explicit option, plus a
 * confirmation when someone is sitting in front of the terminal. A rebuild
 * walks every mount and re-reads every document of the instance, so it must
 * not be the thing that happens when the command is typed without arguments.
 */
class IndexCommand extends Command {
	public function __construct(
		private IJobList $jobList,
		private IAppConfig $appConfig,
		private QueueService $queueService,
		private FileStateService $fileStateService,
		private ITimeFactory $timeFactory,
	) {
		parent::__construct();
	}

	protected function configure(): void {
		$this
			->setName('findling:index')
			->setDescription('Show the state of the Findling index, or start it over')
			->addOption(
				'restart',
				null,
				InputOption::VALUE_NONE,
				'Queue a fresh crawl of every mount. Expensive: every document is read again.',
			)
			->addOption(
				'status',
				null,
				InputOption::VALUE_NONE,
				'Show the counters of the work stock. This is the default.',
			);
	}

	protected function execute(InputInterface $input, OutputInterface $output): int {
		if ($input->getOption('restart')) {
			if (!$this->confirm($input, $output)) {
				$output->writeln('<comment>Nothing was changed.</comment>');
				return Command::SUCCESS;
			}

			$this->restart();
			$output->writeln('<info>The crawl was queued. It starts with the next run of the background jobs.</info>');
			$output->writeln('');
		}

		$this->status($output);

		return Command::SUCCESS;
	}

	/**
	 * Drop the mark, remove what is left of an earlier crawl and queue the
	 * scheduler again.
	 *
	 * The old crawl jobs have to go. Each of them carries the cursor of the
	 * mount it was walking, and leaving them in place would mean the instance
	 * runs two crawls per mount, an old one that continues in the middle and a
	 * new one that starts at the beginning.
	 */
	private function restart(): void {
		$this->appConfig->deleteKey(Application::APP_ID, AppInstallStep::FIRST_INDEX_SCHEDULED);

		$this->jobList->remove(StorageCrawlJob::class);
		$this->jobList->remove(SchedulerJob::class);

		$this->jobList->add(SchedulerJob::class);
		$this->appConfig->setValueBool(Application::APP_ID, AppInstallStep::FIRST_INDEX_SCHEDULED, true);
	}

	private function status(OutputInterface $output): void {
		$queue = $this->queueService->stats();
		$states = $this->fileStateService->counts();

		$output->writeln('Work stock');
		$output->writeln(sprintf('  scheduled            %d', $queue['scheduled']));
		$output->writeln(sprintf('  handed to the worker %d', $queue['running']));
		$output->writeln('');
		$output->writeln('End states');
		foreach ($states as $state => $count) {
			$output->writeln(sprintf('  %-20s %d', $state, $count));
		}
		$output->writeln('');

		$lastRun = $this->appConfig->getValueInt(Application::APP_ID, SchedulerJob::LAST_JOB_RUN);
		if ($lastRun === 0) {
			// The one failure mode that looks like a broken app but is a
			// broken setup: with the default AJAX cron the background jobs
			// only run while somebody is using the web interface.
			$output->writeln('<comment>No background job of this app has run yet. Check the cron setting of this instance.</comment>');
			return;
		}

		$output->writeln(sprintf(
			'Last background job of this app: %s (%d minutes ago)',
			date('Y-m-d H:i:s', $lastRun),
			intdiv(max(0, $this->timeFactory->getTime() - $lastRun), 60),
		));
	}

	private function confirm(InputInterface $input, OutputInterface $output): bool {
		if (!$input->isInteractive()) {
			return true;
		}

		$helper = $this->getHelper('question');
		if (!$helper instanceof QuestionHelper) {
			return true;
		}

		$output->writeln('<comment>This queues a crawl of every mount and reads every document of this instance again.</comment>');

		return (bool)$helper->ask($input, $output, new ConfirmationQuestion('Start over? [y/N] ', false));
	}
}
