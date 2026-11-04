<?php

declare(strict_types=1);

namespace OCA\Findling\Command;

use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\SettingsService;
use OCP\IGroupManager;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

/**
 * The end of the backup pause: `occ findling:resume` (issue #37, D-41-01).
 *
 * Clears the wish and prints the state /status reports. That state may still
 * read "paused" for one round, because the backend reads the wish on its next
 * round and not at once; the pause is over as soon as the wish is cleared.
 * A second call is harmless and says so. Exit 0 in every case, a silent
 * backend included: the wish is cleared either way, and the backend reads
 * "not paused" when it answers again.
 */
class ResumeCommand extends Command {
	public function __construct(
		private SettingsService $settingsService,
		private ExAppService $exAppService,
		private IGroupManager $groupManager,
	) {
		parent::__construct();
	}

	protected function configure(): void {
		$this
			->setName('findling:resume')
			->setDescription('Resume indexing after a backup pause.');
	}

	protected function execute(InputInterface $input, OutputInterface $output): int {
		if (!$this->settingsService->paused()) {
			$output->writeln('Already running.');
		} else {
			$this->settingsService->setPaused(false);
			$output->writeln('Resumed. Indexing continues.');
		}

		$status = $this->exAppService->adminGet('/status', PauseCommand::adminUserId($this->groupManager), []);
		$pause = $status === null ? null : PauseCommand::pauseOf($status);
		$output->writeln('Status: ' . ($pause ?? 'unknown'));

		return Command::SUCCESS;
	}
}
