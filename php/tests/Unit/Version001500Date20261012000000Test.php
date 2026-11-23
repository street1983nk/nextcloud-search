<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use Closure;
use OCA\Findling\AppInfo\Application;
use OCA\Findling\Migration\Version001500Date20261012000000;
use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IAppConfig;
use OCP\Migration\IOutput;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The three statements of the minor step migration of 1.5, and the one it must
 * never make.
 *
 * It drops the recorded version of the container, as every minor step does
 * (Version001400Date20261006000000Test holds the reason), and it marks the
 * denominator of the coverage figure as behind, because 1.5 widens the
 * allowlist and the denominator was counted under the old one (plan 31-10,
 * the class of issue #25). Since plan 45-26 it also forgets when the last
 * recount started, so the round under the allowlist of 1.5 starts in the next
 * run of ScanRecountJob and does not wait RECOUNT_MIN_INTERVAL_SECONDS (owner
 * decision m1 on I-45-23-07). The statement it must never make is a version of
 * its own: setValueString is expected never.
 *
 * Since plan 45-26 the migration names no class of the app (issue #51,
 * I-45-26-01: SettingsService::markScanStale() does not exist in 1.3.2, whose
 * classes are the loaded ones on an update from there). The app configuration
 * is a small store here, so every statement is observed where it lands, and
 * the literals of the migration are held against the constants of the app.
 */
#[CoversClass(Version001500Date20261012000000::class)]
final class Version001500Date20261012000000Test extends TestCase {
	private const NOW = 1791800000;

	/** @var array<string, string> the stored string keys of the app */
	private array $strings = [];

	/** @var array<string, int> the stored int keys of the app */
	private array $ints = [];

	/** @var list<string> every key handed to deleteKey, in order */
	private array $deleted = [];

	/** @var list<string> every key handed to setValueInt, in order */
	private array $intWrites = [];

	/** @var list<string> every key handed to setValueString, in order */
	private array $stringWrites = [];

	/** @var list<string> every line the migration put to the output */
	private array $said = [];

	private function schemaClosure(): Closure {
		return static function (): never {
			self::fail('this migration must not touch the schema');
		};
	}

	private function time(): ITimeFactory {
		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturn(self::NOW);

		return $time;
	}

	/** The app configuration as a small store of the keys of this app. */
	private function appConfig(): IAppConfig {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturnCallback(
			function (string $app, string $key, string $default = ''): string {
				self::assertSame('findling', $app);

				return $this->strings[$key] ?? $default;
			},
		);
		$appConfig->method('getValueInt')->willReturnCallback(
			function (string $app, string $key, int $default = 0): int {
				self::assertSame('findling', $app);

				return $this->ints[$key] ?? $default;
			},
		);
		$appConfig->method('setValueInt')->willReturnCallback(
			function (string $app, string $key, int $value): bool {
				self::assertSame('findling', $app);
				$this->intWrites[] = $key;
				$this->ints[$key] = $value;

				return true;
			},
		);
		$appConfig->method('setValueString')->willReturnCallback(
			function (string $app, string $key, string $value): bool {
				$this->stringWrites[] = $key;
				$this->strings[$key] = $value;

				return true;
			},
		);
		$appConfig->method('deleteKey')->willReturnCallback(
			function (string $app, string $key): void {
				self::assertSame('findling', $app);
				$this->deleted[] = $key;
				unset($this->strings[$key], $this->ints[$key]);
			},
		);

		return $appConfig;
	}

	private function recordingOutput(): IOutput {
		$output = $this->createMock(IOutput::class);
		$output->method('info')->willReturnCallback(function (string $message): void {
			$this->said[] = $message;
		});

		return $output;
	}

	private function migrate(?IAppConfig $appConfig = null): IAppConfig {
		$appConfig ??= $this->appConfig();
		(new Version001500Date20261012000000($appConfig, $this->time()))
			->postSchemaChange($this->recordingOutput(), $this->schemaClosure(), []);

		return $appConfig;
	}

	/** @return list<string> */
	private function deletedOf(string $key): array {
		return array_values(array_filter($this->deleted, static fn (string $k): bool => $k === $key));
	}

	public function testTheClassNameIsTheFileName(): void {
		$file = (new \ReflectionClass(Version001500Date20261012000000::class))->getFileName();

		self::assertIsString($file);
		self::assertSame('Version001500Date20261012000000.php', basename($file));
	}

	public function testARecordedVersionIsDroppedAndTheDenominatorIsMarkedStale(): void {
		// The statements of this migration in one run, observed where they
		// land: the key is deleted, and the recount mark is written with the
		// time of the run.
		$this->strings[ExAppService::KEY_BACKEND_VERSION] = '1.4.2';

		$this->migrate();

		self::assertSame([ExAppService::KEY_BACKEND_VERSION], $this->deletedOf(ExAppService::KEY_BACKEND_VERSION));
		self::assertArrayNotHasKey(ExAppService::KEY_BACKEND_VERSION, $this->strings);
		self::assertSame(self::NOW, $this->ints[SettingsService::KEY_SCAN_STALE_SINCE] ?? null);
	}

	public function testAnInstanceThatNeverRecordedAVersionIsStillMarkedStale(): void {
		// A fresh installation has nothing to drop, but it may well have counted
		// a denominator under the old list before this update.
		$this->migrate();

		self::assertSame([], $this->deletedOf(ExAppService::KEY_BACKEND_VERSION));
		self::assertSame([SettingsService::KEY_SCAN_STALE_SINCE], $this->intWrites);
		self::assertSame(self::NOW, $this->ints[SettingsService::KEY_SCAN_STALE_SINCE] ?? null);
		self::assertContains('no recorded backend version to drop', $this->said);
		self::assertCount(3, $this->said);
	}

	public function testAnExistingMarkIsKept(): void {
		// An event already marked the instance; the earlier time stays, which is
		// the rule of SettingsService::markScanStale() and holds here as well.
		$this->strings[ExAppService::KEY_BACKEND_VERSION] = '1.4.2';
		$this->ints[SettingsService::KEY_SCAN_STALE_SINCE] = 42;

		$this->migrate();

		self::assertSame([], $this->intWrites);
		self::assertSame(42, $this->ints[SettingsService::KEY_SCAN_STALE_SINCE]);
	}

	public function testTheMigrationNeverWritesAVersionOfItsOwn(): void {
		foreach (['1.4.2', ''] as $recorded) {
			$this->strings = $recorded === '' ? [] : [ExAppService::KEY_BACKEND_VERSION => $recorded];

			$this->migrate();
		}

		self::assertSame([], $this->stringWrites);
	}

	public function testTheDroppedVersionIsNamedInTheOutput(): void {
		$this->strings[ExAppService::KEY_BACKEND_VERSION] = '1.4.2';

		$this->migrate();

		self::assertCount(3, $this->said);
		self::assertStringContainsString('recount', $this->said[0]);
		self::assertStringContainsString('1.4.2', $this->said[2]);
	}

	public function testAnUpdateFromBeforeOneFiveRecountsAtOnce(): void {
		// A jump from 1.4.x: the last round started an hour ago and nothing is
		// marked. Without the forgetting, the marked instance would wait for
		// RECOUNT_MIN_INTERVAL_SECONDS since that start (I-45-23-07).
		$this->ints[SettingsService::KEY_SCAN_RECOUNTED_AT] = self::NOW - 3600;
		$appConfig = $this->appConfig();

		$this->migrate($appConfig);

		self::assertArrayNotHasKey(SettingsService::KEY_SCAN_RECOUNTED_AT, $this->ints);
		self::assertSame(self::NOW, $this->ints[SettingsService::KEY_SCAN_STALE_SINCE] ?? null);
		$settings = new SettingsService($appConfig, $this->createMock(LoggerInterface::class), $this->time());
		self::assertTrue($settings->scanRecountDue(self::NOW));

		// A replay forgets nothing more and throws nothing.
		$this->migrate($appConfig);
		self::assertTrue($settings->scanRecountDue(self::NOW));
	}

	public function testASecondRunDropsNothingAndThrowsNothing(): void {
		// The second run sees the version gone and the mark set: it drops no
		// version, sets no mark, and forgetting the start of the last round a
		// second time is no error either.
		$this->strings[ExAppService::KEY_BACKEND_VERSION] = '1.4.2';
		$this->ints[SettingsService::KEY_SCAN_RECOUNTED_AT] = self::NOW - 3600;
		$appConfig = $this->appConfig();

		$this->migrate($appConfig);
		$this->migrate($appConfig);

		self::assertCount(1, $this->deletedOf(ExAppService::KEY_BACKEND_VERSION));
		self::assertCount(2, $this->deletedOf(SettingsService::KEY_SCAN_RECOUNTED_AT));
		self::assertSame([SettingsService::KEY_SCAN_STALE_SINCE], $this->intWrites);
		self::assertSame([], $this->stringWrites);
		self::assertContains('no recorded backend version to drop', $this->said);
	}

	/**
	 * Issue #51: the migration names no class of the app, because an update
	 * runs with the classes of the old version loaded. The literals it carries
	 * instead are held against the constants here.
	 */
	public function testTheLiteralsMirrorTheConstantsOfTheApp(): void {
		self::assertSame(Application::APP_ID, Version001500Date20261012000000::APP_ID);
		self::assertSame(ExAppService::KEY_BACKEND_VERSION, Version001500Date20261012000000::BACKEND_VERSION_KEY);
		self::assertSame(SettingsService::KEY_SCAN_STALE_SINCE, Version001500Date20261012000000::STALE_KEY);
		self::assertSame(SettingsService::KEY_SCAN_RECOUNTED_AT, Version001500Date20261012000000::RECOUNTED_AT_KEY);
	}

	public function testTheMigrationAsksTheContainerForNothing(): void {
		// Two collaborators, and neither of them talks to the container: the
		// app configuration and the clock.
		$constructor = (new \ReflectionClass(Version001500Date20261012000000::class))->getConstructor();

		self::assertNotNull($constructor);

		$types = [];
		foreach ($constructor->getParameters() as $parameter) {
			$type = $parameter->getType();
			self::assertInstanceOf(\ReflectionNamedType::class, $type);
			$types[] = $type->getName();
		}

		self::assertSame([IAppConfig::class, ITimeFactory::class], $types);
	}
}
