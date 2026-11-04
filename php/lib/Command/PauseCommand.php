<?php

declare(strict_types=1);

namespace OCA\Findling\Command;

use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IGroupManager;
use OCP\IUser;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;

/**
 * The backup pause from a shell: `occ findling:pause [--wait[=SECONDS]]`
 * (issue #37, D-41-01).
 *
 * The command stores the wish (SettingsService::setPaused(), the one source of
 * it, D-41-05) and reads the state the backend reports on /status. The backend
 * reads the wish on its next round, lets the current batch finish, flushes
 * every database to disk and reports "paused"; only then is the volume safe to
 * copy (D-41-18). A backup script therefore calls this with --wait and copies
 * after exit 0, and the exit code is the whole contract:
 *
 * - 0 without --wait once the wish is stored, with --wait only when the
 *   backend said exactly "paused";
 * - 1 when --wait ran out, when the backend did not answer while the script
 *   waits, and when the answer carries no field pause at all. The last case is
 *   a backend before 1.6.2: it never reports "paused", and a script must not
 *   read its silence as a consistent volume.
 *
 * The state is compared against a closed set with strict string comparison
 * (T-41-21), so "PAUSED", 1 or true are not paused. The identity of the
 * call is the first enabled member of the admin group, for the reason the
 * docblock of DiagnoseCommand gives: adminGet signs with a user id and occ has
 * no session.
 *
 * The pause stays until `occ findling:resume`; a timeout does not take it
 * back, so a second call picks up where the first one stopped.
 */
class PauseCommand extends Command {
	/**
	 * How long --wait waits without a value, 40 minutes.
	 *
	 * The backend lets the current batch finish before it pauses, and the
	 * longest batch is one OCR pass over a large scan, which may take up to 30
	 * minutes on a small box (D-41-18). Ten minutes on top for the round in
	 * which the backend reads the wish and for the flush.
	 */
	public const DEFAULT_WAIT_SECONDS = 2400;

	/** The distance between two reads of /status while waiting. */
	public const POLL_SECONDS = 5;

	/** The states /status reports since 1.6.2 (plan 41-04), a closed set. */
	public const STATES = ['running', 'pausing', 'paused', 'unknown'];

	/** The group whose members Nextcloud treats as administrators. */
	private const ADMIN_GROUP = 'admin';

	public function __construct(
		private SettingsService $settingsService,
		private ExAppService $exAppService,
		private IGroupManager $groupManager,
		private ITimeFactory $timeFactory,
	) {
		parent::__construct();
	}

	protected function configure(): void {
		$this
			->setName('findling:pause')
			->setDescription('Pause indexing for a backup; search keeps working.')
			->addOption(
				'wait',
				null,
				InputOption::VALUE_OPTIONAL,
				'Wait until the backend says paused, at most this many seconds (default '
					. self::DEFAULT_WAIT_SECONDS . '). Exit 0 only when it did.',
				false,
			);
	}

	protected function execute(InputInterface $input, OutputInterface $output): int {
		$wait = $this->waitSeconds($input->getOption('wait'));
		if ($wait === 0) {
			// Refused before anything is stored, so a typo in a backup script
			// does not leave a pause behind that nobody waited for.
			$output->writeln('<error>--wait takes a number of seconds.</error>');

			return Command::INVALID;
		}

		if ($this->settingsService->paused()) {
			$output->writeln('Already paused.');
		} else {
			$this->settingsService->setPaused(true);
			$output->writeln('Pause requested. Indexing stops after the current batch. Start the backup when the status says paused.');
		}

		if ($wait === null) {
			return $this->report($output);
		}

		return $this->waitForThePause($output, $wait);
	}

	/**
	 * The state of the pause out of one /status answer.
	 *
	 * null when the answer carries no field pause (a backend before 1.6.2),
	 * the value when it is one of STATES, and "unknown" for anything else, so
	 * that no odd value can ever read as paused.
	 *
	 * @param array<mixed> $status
	 */
	public static function pauseOf(array $status): ?string {
		if (!array_key_exists('pause', $status)) {
			return null;
		}

		$pause = $status['pause'];

		return is_string($pause) && in_array($pause, self::STATES, true) ? $pause : 'unknown';
	}

	/**
	 * The first enabled member of the admin group, or an empty string; the
	 * same rule as DiagnoseCommand::adminUserId() and for the same reasons.
	 */
	public static function adminUserId(IGroupManager $groupManager): string {
		$group = $groupManager->get(self::ADMIN_GROUP);
		if ($group === null) {
			return '';
		}

		foreach ($group->getUsers() as $user) {
			if ($user instanceof IUser && $user->isEnabled()) {
				return $user->getUID();
			}
		}

		return '';
	}

	/** Wait for real; a test replaces this with a clock that only moves. */
	protected function sleepFor(int $seconds): void {
		sleep($seconds);
	}

	/**
	 * The seconds --wait asks for: null without the option, the default for
	 * the option without a value, and 0 for anything that is not a positive
	 * whole number.
	 */
	private function waitSeconds(mixed $option): ?int {
		if ($option === false) {
			return null;
		}
		if ($option === null) {
			return self::DEFAULT_WAIT_SECONDS;
		}
		if (!is_string($option) || preg_match('/^[1-9][0-9]{0,8}$/D', $option) !== 1) {
			return 0;
		}

		return (int)$option;
	}

	/** One read of /status, printed; without --wait. */
	private function report(OutputInterface $output): int {
		$status = $this->status();
		if ($status === null) {
			$output->writeln('The backend did not answer, the pause request is stored and takes effect when it answers.');

			return Command::SUCCESS;
		}

		$pause = self::pauseOf($status);
		if ($pause === null) {
			return $this->oldBackend($output);
		}

		$output->writeln('Status: ' . $pause);

		return Command::SUCCESS;
	}

	/** Read /status until it says paused or the time is up. */
	private function waitForThePause(OutputInterface $output, int $wait): int {
		$deadline = $this->timeFactory->getTime() + $wait;

		while (true) {
			$status = $this->status();
			if ($status === null) {
				$output->writeln('The backend did not answer, the pause request is stored and takes effect when it answers.');

				return Command::FAILURE;
			}

			$pause = self::pauseOf($status);
			if ($pause === null) {
				return $this->oldBackend($output);
			}

			if ($pause === 'paused') {
				$output->writeln('Paused. Indexing has stopped and everything is flushed to disk; search keeps working.');

				return Command::SUCCESS;
			}

			$left = $deadline - $this->timeFactory->getTime();
			if ($left <= 0) {
				$output->writeln(sprintf(
					'Still pausing after %d seconds. The current batch has not finished yet; run the command again or check the admin page.',
					$wait,
				));

				return Command::FAILURE;
			}

			$this->sleepFor(min(self::POLL_SECONDS, $left));
		}
	}

	private function oldBackend(OutputInterface $output): int {
		$output->writeln('<error>The backend does not know the pause yet. Update both apps to the same version.</error>');

		return Command::FAILURE;
	}

	/** @return array<mixed>|null */
	private function status(): ?array {
		return $this->exAppService->adminGet('/status', self::adminUserId($this->groupManager), []);
	}
}
