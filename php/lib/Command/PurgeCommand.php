<?php

declare(strict_types=1);

namespace OCA\Findling\Command;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Repair\AppUninstallStep;
use OCA\Findling\Service\PurgeService;
use OCP\IAppConfig;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Helper\QuestionHelper;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Question\ConfirmationQuestion;

/**
 * The place where an administrator states the intent to remove the data of
 * this app: `occ findling:purge [--arm|--disarm|--now]`.
 *
 * It exists because Nextcloud runs the uninstall repair steps on every disable
 * of an app, which docs/uninstall.md measures rather than claims. An
 * unconditional removal in that step would empty the settings of anybody who
 * switches the search off for a night. So the step asks for a mark, and this
 * command is the one way to set it.
 *
 * Reading is the default, as in IndexCommand: without an option this prints
 * what a removal would take with it and changes nothing. The destructive paths
 * need the explicit option and a confirmation, and a non interactive call
 * counts as confirmed, because that is how CI calls it.
 *
 * The output names tables and numbers and never a path or a file name. Table
 * names are metadata of this app and an administrator on the machine could
 * read them off the database anyway; a path is content of somebody's account
 * and stays out of a terminal that is usually being logged (T-04-38).
 */
class PurgeCommand extends Command {
	/** Width of the label column, the same one IndexCommand prints with. */
	private const LABEL_WIDTH = 20;

	public function __construct(
		private PurgeService $purgeService,
		private IAppConfig $appConfig,
	) {
		parent::__construct();
	}

	protected function configure(): void {
		$this
			->setName('findling:purge')
			->setDescription('Show what removing the data of Findling would take with it, and state the intent to do it')
			->addOption(
				'arm',
				null,
				InputOption::VALUE_NONE,
				'State the intent. The next disable or remove of this app clears its tables, jobs and settings.',
			)
			->addOption(
				'disarm',
				null,
				InputOption::VALUE_NONE,
				'Take the intent back. Disabling the app leaves everything in place again.',
			)
			->addOption(
				'now',
				null,
				InputOption::VALUE_NONE,
				'Clear it right now, without removing the app files. The app switches itself off in the process, '
					. 'because "enabled" is one of the settings that go. The search keeps answering out of the '
					. 'container, and "occ app:enable findling" runs the migrations again and brings this half back.',
			);
	}

	protected function execute(InputInterface $input, OutputInterface $output): int {
		if ($input->getOption('disarm')) {
			$this->appConfig->deleteKey(Application::APP_ID, AppUninstallStep::PURGE_INTENT);
			$output->writeln('<info>The intent was taken back. Disabling or removing this app leaves its data in place.</info>');
			$output->writeln('');

			return $this->report($output);
		}

		if ($input->getOption('now')) {
			if (!$this->confirm($input, $output, 'This removes the tables, the background jobs and the settings of this app right now.')) {
				$output->writeln('<comment>Nothing was changed.</comment>');

				return Command::SUCCESS;
			}

			$this->appConfig->setValueBool(Application::APP_ID, AppUninstallStep::PURGE_INTENT, true);
			$removed = $this->purgeService->run();

			$output->writeln('<info>Removed</info>');
			$this->raster($output, $removed);
			$output->writeln('');
			$output->writeln('This app is switched off now, because "enabled" was one of the settings that went.');
			$output->writeln('The search keeps answering out of the container. "occ app:enable findling" runs the');
			$output->writeln('migrations again and brings the queue, the counters and the settings back empty.');

			return Command::SUCCESS;
		}

		if ($input->getOption('arm')) {
			if (!$this->confirm($input, $output, 'This marks the data of this app for removal by the next disable or remove.')) {
				$output->writeln('<comment>Nothing was changed.</comment>');

				return Command::SUCCESS;
			}

			$this->appConfig->setValueBool(Application::APP_ID, AppUninstallStep::PURGE_INTENT, true);
			$output->writeln('<info>The intent is set. The next "occ app:disable findling" or "occ app:remove findling" removes what is listed below.</info>');
			$output->writeln('');
		}

		return $this->report($output);
	}

	/**
	 * The plan, the state of the mark and what happens next. Changes nothing.
	 */
	private function report(OutputInterface $output): int {
		$output->writeln('<info>What a removal would take with it</info>');
		$this->raster($output, $this->purgeService->plan());
		$output->writeln('');

		if ($this->appConfig->getValueBool(Application::APP_ID, AppUninstallStep::PURGE_INTENT)) {
			$output->writeln('The intent is set. The next disable or remove of this app removes the above.');
			$output->writeln('"occ findling:purge --disarm" takes that back.');

			return Command::SUCCESS;
		}

		$output->writeln('The intent is not set, so a disable or a remove of this app leaves all of it in place.');
		$output->writeln('"occ findling:purge --arm" states the intent, "--now" removes it without removing the app.');

		return Command::SUCCESS;
	}

	/**
	 * Jobs, tables and the number of settings, in the column form of
	 * IndexCommand. Every entry, including the ones that are not there, because
	 * a line that disappears when it has nothing behind it leaves the reader
	 * unable to tell "already gone" from "this command does not look at it".
	 *
	 * @param array{jobs: array<string, bool>, tables: array<string, bool>, migrations: int, settings: int} $raster
	 */
	private function raster(OutputInterface $output, array $raster): void {
		$output->writeln('  background jobs');
		foreach ($raster['jobs'] as $job => $present) {
			$this->line($output, $this->shortName($job), $present ? 'yes' : 'no');
		}

		$output->writeln('  tables');
		foreach ($raster['tables'] as $table => $present) {
			$this->line($output, $table, $present ? 'yes' : 'no');
		}

		$output->writeln('  schema');
		$this->line($output, 'migration records', (string)$raster['migrations']);

		$output->writeln('  settings');
		$this->line($output, 'stored values', (string)$raster['settings']);
	}

	private function line(OutputInterface $output, string $label, string $value): void {
		$output->writeln(sprintf('    %-' . self::LABEL_WIDTH . 's %s', $label, $value));
	}

	/**
	 * The class name without its namespace. The full name says nothing a reader
	 * of this output needs and pushes the column off the width of a terminal.
	 */
	private function shortName(string $class): string {
		$position = strrpos($class, '\\');

		return $position === false ? $class : substr($class, $position + 1);
	}

	private function confirm(InputInterface $input, OutputInterface $output, string $warning): bool {
		if (!$input->isInteractive()) {
			return true;
		}

		$helper = $this->getHelper('question');
		if (!$helper instanceof QuestionHelper) {
			return true;
		}

		$output->writeln('<comment>' . $warning . '</comment>');

		return (bool)$helper->ask($input, $output, new ConfirmationQuestion('Go ahead? [y/N] ', false));
	}
}
