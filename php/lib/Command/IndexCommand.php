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
	 *
	 * **Where this command ends and the other half begins (DI-04-04).** Queueing
	 * the crawl is everything this side can do. The reindex banner names this
	 * command as its remedy, and the banner is raised and lowered by the
	 * container: it compares the version marks in its own state database against
	 * what the running code expects. Until plan 05-11 nothing ever wrote those
	 * marks again, so this command could never clear the banner, and it could
	 * not even rebuild, because the container read every requeued file as
	 * unchanged. Both halves of that live over there now, in
	 * findling/index/open.py: the drift raises the local generation so that this
	 * crawl reads the documents again, and the marks are stamped once the last
	 * of them has been judged. Stamping deliberately sits at the END of the
	 * rebuild and not in the seed of the state database, because seeding is a
	 * first operation that must never overwrite a mark that is there.
	 */
	private function restart(): void {
		$this->appConfig->deleteKey(Application::APP_ID, AppInstallStep::FIRST_INDEX_SCHEDULED);

		$this->jobList->remove(StorageCrawlJob::class);
		$this->jobList->remove(SchedulerJob::class);

		$this->jobList->add(SchedulerJob::class);
		$this->appConfig->setValueBool(Application::APP_ID, AppInstallStep::FIRST_INDEX_SCHEDULED, true);
	}

	/**
	 * The counters of this half, and the answer to assumption A8.
	 *
	 * Bug-L4 of the phase 2 audit reads "--status always shows indexed 0", and
	 * this command was suspected of having outgrown it because it asks
	 * FileStateService::counts() today. It has not, and the zero is not a
	 * defect: findling_file_state is the source for skipped and failed, and
	 * indexed belongs to the container, which is the only half that can see the
	 * index. Nothing on this side ever writes an indexed row, so the counter is
	 * structurally nought and always will be.
	 *
	 * So the fix is the label and not the number, which is what the division of
	 * the truth from phase 4 prescribes: the block says whose view it is, and
	 * the line under it names the half that counts the documents and where to
	 * ask it. Printing a number that cannot be anything but nought without
	 * saying so is how a status command teaches an admin to distrust all of its
	 * output.
	 */
	private function status(OutputInterface $output): void {
		$queue = $this->queueService->stats();
		$states = $this->fileStateService->counts();

		$output->writeln('Work stock');
		$output->writeln(sprintf('  scheduled            %d', $queue['scheduled']));
		$output->writeln(sprintf('  handed to the worker %d', $queue['running']));
		$output->writeln('');
		$output->writeln('End states as Nextcloud recorded them');
		foreach ($states as $state => $count) {
			$output->writeln(sprintf('  %-20s %d', $state, $count));
		}
		$output->writeln('<comment>  indexed is counted by the backend container and never written here, so it stays 0.</comment>');
		$output->writeln('<comment>  The admin settings page of Findling shows the counters of both halves side by side.</comment>');
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
