<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Command\PauseCommand;
use OCA\Findling\Command\ResumeCommand;
use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IAppConfig;
use OCP\IGroup;
use OCP\IGroupManager;
use OCP\IUser;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;

/**
 * The backup pause from a shell, issue #37: `occ findling:pause [--wait]` and
 * `occ findling:resume` (D-41-01, D-41-18).
 *
 * A backup script calls the pause with --wait and copies the volume only after
 * exit 0, so the exit code is the contract: 0 only on the state "paused" read
 * from the backend, 1 on a timeout, on a silent backend and on a backend that
 * does not know the pause yet (an old backend would never say "paused", and a
 * script must not take its silence for consistency).
 *
 * SettingsService is final and is built for real on a doubled IAppConfig that
 * keeps its values in an array. The clock is a doubled ITimeFactory that the
 * sleeper of the command moves forward, so no test sleeps for real.
 */
#[CoversClass(PauseCommand::class)]
#[CoversClass(ResumeCommand::class)]
final class PauseCommandTest extends TestCase {
	private const NOW = 1790000000;

	/** @var array<string, bool> the stored keys of the app */
	private array $values = [];

	private int $clock = self::NOW;

	/** @var list<int> the seconds the command slept, in order */
	private array $slept = [];

	/** @var list<array<mixed>|null> the answers of /status, the last one repeats */
	private array $answers = [];

	private int $polls = 0;

	private IAppConfig&MockObject $appConfig;
	private ExAppService&MockObject $exApp;
	private IGroupManager&MockObject $groupManager;
	private ITimeFactory&MockObject $time;

	protected function setUp(): void {
		parent::setUp();

		$this->values = [];
		$this->clock = self::NOW;
		$this->slept = [];
		$this->answers = [];
		$this->polls = 0;

		$this->appConfig = $this->createMock(IAppConfig::class);
		$this->appConfig->method('getValueBool')->willReturnCallback(
			fn (string $app, string $key, bool $default = false): bool => $this->values[$key] ?? $default,
		);
		$this->appConfig->method('setValueBool')->willReturnCallback(
			function (string $app, string $key, bool $value): bool {
				self::assertSame(Application::APP_ID, $app);
				$this->values[$key] = $value;

				return true;
			},
		);

		$this->time = $this->createMock(ITimeFactory::class);
		$this->time->method('getTime')->willReturnCallback(fn (): int => $this->clock);

		$this->exApp = $this->createMock(ExAppService::class);
		$this->exApp->method('adminGet')->willReturnCallback(
			function (string $path, string $userId, array $params): ?array {
				self::assertSame('/status', $path);
				self::assertSame('admin', $userId);
				self::assertSame([], $params);
				$answer = $this->answers[min($this->polls, count($this->answers) - 1)] ?? null;
				$this->polls++;

				return $answer;
			},
		);

		$admin = $this->createMock(IUser::class);
		$admin->method('isEnabled')->willReturn(true);
		$admin->method('getUID')->willReturn('admin');
		$group = $this->createMock(IGroup::class);
		$group->method('getUsers')->willReturn([$admin]);
		$this->groupManager = $this->createMock(IGroupManager::class);
		$this->groupManager->method('get')->willReturn($group);
	}

	private function settings(): SettingsService {
		return new SettingsService($this->appConfig, $this->createMock(LoggerInterface::class), $this->time);
	}

	/** The pause command with a sleeper that only moves the doubled clock. */
	private function pause(): PauseCommand {
		$command = new class($this->settings(), $this->exApp, $this->groupManager, $this->time) extends PauseCommand {
			/** @var \Closure(int): void */
			public \Closure $onSleep;

			protected function sleepFor(int $seconds): void {
				($this->onSleep)($seconds);
			}
		};
		$command->onSleep = function (int $seconds): void {
			$this->slept[] = $seconds;
			$this->clock += $seconds;
		};

		return $command;
	}

	private function resume(): ResumeCommand {
		return new ResumeCommand($this->settings(), $this->exApp, $this->groupManager);
	}

	/**
	 * @param array<string, mixed> $input
	 * @return array{int, string}
	 */
	private function runCommand(Command $command, array $input = []): array {
		$output = new BufferedOutput();
		$code = $command->run(new ArrayInput($input), $output);

		return [$code, $output->fetch()];
	}

	/** @param list<array<mixed>|null> $answers */
	private function backendAnswers(array $answers): void {
		$this->answers = $answers;
	}

	// -- names -----------------------------------------------------------------

	public function testTheCommandsCarryTheirNames(): void {
		self::assertSame('findling:pause', $this->pause()->getName());
		self::assertSame('findling:resume', $this->resume()->getName());
		self::assertSame(2400, PauseCommand::DEFAULT_WAIT_SECONDS);
		self::assertSame(5, PauseCommand::POLL_SECONDS);
	}

	// -- pause -----------------------------------------------------------------

	public function testPauseStoresTheWishAndPrintsTheStatus(): void {
		$this->backendAnswers([['pause' => 'pausing', 'pausedSince' => null]]);

		[$code, $text] = $this->runCommand($this->pause());

		self::assertSame(Command::SUCCESS, $code);
		self::assertTrue($this->values[SettingsService::KEY_PAUSED]);
		self::assertStringContainsString(
			'Pause requested. Indexing stops after the current batch. Start the backup when the status says paused.',
			$text,
		);
		self::assertStringContainsString('Status: pausing', $text);
		self::assertSame([], $this->slept);
	}

	public function testPauseWaitEndsWhenTheBackendSaysPaused(): void {
		$this->backendAnswers([
			['pause' => 'pausing'],
			['pause' => 'pausing'],
			['pause' => 'paused', 'pausedSince' => self::NOW + 10],
		]);

		[$code, $text] = $this->runCommand($this->pause(), ['--wait' => null]);

		self::assertSame(Command::SUCCESS, $code);
		self::assertStringContainsString(
			'Paused. Indexing has stopped and everything is flushed to disk; search keeps working.',
			$text,
		);
		self::assertSame(3, $this->polls);
		self::assertSame([5, 5], $this->slept);
	}

	public function testPauseWaitTimesOut(): void {
		$this->backendAnswers([['pause' => 'pausing']]);

		[$code, $text] = $this->runCommand($this->pause(), ['--wait' => '10']);

		self::assertSame(1, $code);
		self::assertStringContainsString(
			'Still pausing after 10 seconds. The current batch has not finished yet; run the command again or check the admin page.',
			$text,
		);
		self::assertStringNotContainsString('Paused.', $text);
		self::assertSame(10, array_sum($this->slept));
		// The wish stays: a second call picks up where this one stopped.
		self::assertTrue($this->values[SettingsService::KEY_PAUSED]);
	}

	public function testPauseWaitWithoutAValueWaitsTheDefault(): void {
		$this->backendAnswers([['pause' => 'pausing']]);

		[$code, $text] = $this->runCommand($this->pause(), ['--wait' => null]);

		self::assertSame(1, $code);
		self::assertStringContainsString('Still pausing after 2400 seconds.', $text);
		self::assertSame(2400, array_sum($this->slept));
	}

	#[DataProvider('malformedWaits')]
	public function testAMalformedWaitIsRefusedBeforeAnythingIsStored(string $wait): void {
		[$code, $text] = $this->runCommand($this->pause(), ['--wait' => $wait]);

		self::assertSame(Command::INVALID, $code);
		self::assertArrayNotHasKey(SettingsService::KEY_PAUSED, $this->values);
		self::assertSame(0, $this->polls);
		self::assertStringContainsString('--wait takes a number of seconds.', $text);
	}

	/** @return array<string, array{string}> */
	public static function malformedWaits(): array {
		return ['zero' => ['0'], 'negative' => ['-5'], 'word' => ['soon'], 'fraction' => ['1.5'], 'empty' => ['']];
	}

	public function testPauseAgainstAnOldBackendFails(): void {
		// A 1.6.1 backend answers /status without the field pause and would
		// never say paused: exit 1 with the sentence, the wish stays stored.
		$this->backendAnswers([['indexed' => 12, 'queued' => 0]]);

		foreach ([[], ['--wait' => '60']] as $input) {
			[$code, $text] = $this->runCommand($this->pause(), $input);

			self::assertSame(1, $code);
			self::assertStringContainsString(
				'The backend does not know the pause yet. Update both apps to the same version.',
				$text,
			);
			self::assertTrue($this->values[SettingsService::KEY_PAUSED]);
		}
		self::assertSame([], $this->slept);
	}

	public function testPauseWithoutAnAnsweringBackendKeepsTheWish(): void {
		$this->backendAnswers([null]);
		$sentence = 'The backend did not answer, the pause request is stored and takes effect when it answers.';

		[$code, $text] = $this->runCommand($this->pause());
		self::assertSame(Command::SUCCESS, $code);
		self::assertStringContainsString($sentence, $text);
		self::assertTrue($this->values[SettingsService::KEY_PAUSED]);

		[$code, $text] = $this->runCommand($this->pause(), ['--wait' => '60']);
		self::assertSame(1, $code);
		self::assertStringContainsString($sentence, $text);
		self::assertTrue($this->values[SettingsService::KEY_PAUSED]);
	}

	public function testPauseTwiceSaysAlreadyPaused(): void {
		$this->backendAnswers([['pause' => 'paused', 'pausedSince' => self::NOW]]);
		$this->values[SettingsService::KEY_PAUSED] = true;

		[$code, $text] = $this->runCommand($this->pause());

		self::assertSame(Command::SUCCESS, $code);
		self::assertStringContainsString('Already paused.', $text);
		self::assertStringNotContainsString('Pause requested.', $text);
		self::assertStringContainsString('Status: paused', $text);

		// With --wait the second call still waits for the state.
		[$code, $text] = $this->runCommand($this->pause(), ['--wait' => '60']);
		self::assertSame(Command::SUCCESS, $code);
		self::assertStringContainsString('Already paused.', $text);
		self::assertStringContainsString('Paused. Indexing has stopped', $text);
	}

	/** @return array<string, array{mixed}> */
	public static function oddStates(): array {
		return [
			'upper case' => ['PAUSED'],
			'one' => [1],
			'true' => [true],
			'padded' => [' paused'],
			'list' => [['paused']],
		];
	}

	#[DataProvider('oddStates')]
	public function testAnOddStatusValueIsNotTakenAsPaused(mixed $state): void {
		// A closed set compared strictly (T-41-21): nothing but the exact
		// string paused lets a backup script go on.
		$this->backendAnswers([['pause' => $state]]);

		[$code, $text] = $this->runCommand($this->pause(), ['--wait' => '10']);

		self::assertSame(1, $code);
		self::assertStringNotContainsString('Paused. Indexing has stopped', $text);
		self::assertStringContainsString('Still pausing after 10 seconds.', $text);

		[$code, $text] = $this->runCommand($this->pause());
		self::assertSame(Command::SUCCESS, $code);
		self::assertStringContainsString('Status: unknown', $text);
	}

	// -- resume ----------------------------------------------------------------

	public function testResumeClearsTheWish(): void {
		$this->values[SettingsService::KEY_PAUSED] = true;
		$this->backendAnswers([['pause' => 'running', 'pausedSince' => null]]);

		[$code, $text] = $this->runCommand($this->resume());

		self::assertSame(Command::SUCCESS, $code);
		self::assertFalse($this->values[SettingsService::KEY_PAUSED]);
		self::assertStringContainsString('Resumed. Indexing continues.', $text);
		self::assertStringContainsString('Status: running', $text);
	}

	public function testResumeTwiceSaysAlreadyRunning(): void {
		$this->backendAnswers([['pause' => 'running']]);

		[$code, $text] = $this->runCommand($this->resume());

		self::assertSame(Command::SUCCESS, $code);
		self::assertStringContainsString('Already running.', $text);
		self::assertStringNotContainsString('Resumed.', $text);
		self::assertFalse($this->values[SettingsService::KEY_PAUSED] ?? false);
	}

	public function testResumeWithASilentBackendStillClearsTheWish(): void {
		$this->values[SettingsService::KEY_PAUSED] = true;
		$this->backendAnswers([null]);

		[$code, $text] = $this->runCommand($this->resume());

		self::assertSame(Command::SUCCESS, $code);
		self::assertFalse($this->values[SettingsService::KEY_PAUSED]);
		self::assertStringContainsString('Resumed. Indexing continues.', $text);
		self::assertStringContainsString('Status: unknown', $text);
	}
}
