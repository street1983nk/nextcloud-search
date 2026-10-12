<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use Closure;
use OCA\Findling\Migration\Version001500Date20261012000000;
use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IAppConfig;
use OCP\Migration\IOutput;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The two statements of the minor step migration of 1.5, and the one it must
 * never make.
 *
 * It drops the recorded version of the container, as every minor step does
 * (Version001400Date20261006000000Test holds the reason), and it marks the
 * denominator of the coverage figure as behind, because 1.5 widens the
 * allowlist and the denominator was counted under the old one (plan 31-10,
 * the class of issue #25). The statement it must never make is a version of
 * its own: setValueString is expected never.
 *
 * SettingsService is final and is therefore not mocked: the real service runs
 * on the mocked app configuration, and the mark is observed where it lands, as
 * a setValueInt of KEY_SCAN_STALE_SINCE. Both keys are read out of their
 * classes instead of copied into this file, so a rename breaks this test
 * rather than passing it against a string nobody writes any more.
 */
#[CoversClass(Version001500Date20261012000000::class)]
final class Version001500Date20261012000000Test extends TestCase {
	private const NOW = 1791800000;

	private function schemaClosure(): Closure {
		return static function (): never {
			self::fail('this migration must not touch the schema');
		};
	}

	private function versionKey(): string {
		$value = (new \ReflectionClass(ExAppService::class))->getConstant('KEY_BACKEND_VERSION');

		self::assertIsString($value, 'KEY_BACKEND_VERSION is gone or is no longer a string');

		return $value;
	}

	private function settings(IAppConfig $appConfig): SettingsService {
		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturn(self::NOW);

		return new SettingsService($appConfig, $this->createMock(LoggerInterface::class), $time);
	}

	/** An app configuration with a recorded version and no recount mark yet. */
	private function appConfig(string $recorded, int $staleSince = 0): IAppConfig&MockObject {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturn($recorded);
		$appConfig->method('getValueInt')->willReturn($staleSince);

		return $appConfig;
	}

	private function migration(IAppConfig $appConfig): Version001500Date20261012000000 {
		return new Version001500Date20261012000000($appConfig, $this->settings($appConfig));
	}

	public function testTheClassNameIsTheFileName(): void {
		$file = (new \ReflectionClass(Version001500Date20261012000000::class))->getFileName();

		self::assertIsString($file);
		self::assertSame('Version001500Date20261012000000.php', basename($file));
	}

	public function testARecordedVersionIsDroppedAndTheDenominatorIsMarkedStale(): void {
		// The two statements of this migration in one run, observed where they
		// land: the key is deleted, and the recount mark is written with the
		// time of the run.
		$appConfig = $this->appConfig('1.4.2');
		$appConfig->expects(self::once())
			->method('deleteKey')
			->with('findling', $this->versionKey());
		$appConfig->expects(self::once())
			->method('setValueInt')
			->with('findling', SettingsService::KEY_SCAN_STALE_SINCE, self::NOW);

		$this->migration($appConfig)->postSchemaChange($this->createMock(IOutput::class), $this->schemaClosure(), []);
	}

	public function testAnInstanceThatNeverRecordedAVersionIsStillMarkedStale(): void {
		// A fresh installation has nothing to drop, but it may well have counted
		// a denominator under the old list before this update.
		$appConfig = $this->appConfig('');
		$appConfig->expects(self::never())->method('deleteKey');
		$appConfig->expects(self::once())
			->method('setValueInt')
			->with('findling', SettingsService::KEY_SCAN_STALE_SINCE, self::NOW);

		$output = $this->createMock(IOutput::class);
		$output->expects(self::exactly(2))->method('info');

		$this->migration($appConfig)->postSchemaChange($output, $this->schemaClosure(), []);
	}

	public function testAnExistingMarkIsKept(): void {
		// An event already marked the instance; the earlier time stays, which is
		// the rule of markScanStale() itself and holds here as well.
		$appConfig = $this->appConfig('1.4.2', 42);
		$appConfig->expects(self::never())->method('setValueInt');

		$this->migration($appConfig)->postSchemaChange($this->createMock(IOutput::class), $this->schemaClosure(), []);
	}

	public function testTheMigrationNeverWritesAVersionOfItsOwn(): void {
		foreach (['1.4.2', ''] as $recorded) {
			$appConfig = $this->appConfig($recorded);
			$appConfig->expects(self::never())->method('setValueString');

			$this->migration($appConfig)->postSchemaChange($this->createMock(IOutput::class), $this->schemaClosure(), []);
		}
	}

	public function testTheDroppedVersionIsNamedInTheOutput(): void {
		$output = $this->createMock(IOutput::class);
		$output->expects(self::exactly(2))
			->method('info')
			->with(self::logicalOr(self::stringContains('recount'), self::stringContains('1.4.2')));

		$this->migration($this->appConfig('1.4.2'))->postSchemaChange($output, $this->schemaClosure(), []);
	}

	public function testASecondRunDropsNothingAndThrowsNothing(): void {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturnOnConsecutiveCalls('1.4.2', '');
		$appConfig->method('getValueInt')->willReturnOnConsecutiveCalls(0, self::NOW);
		$appConfig->expects(self::once())->method('deleteKey');
		$appConfig->expects(self::once())->method('setValueInt');

		$migration = $this->migration($appConfig);
		$output = $this->createMock(IOutput::class);

		$migration->postSchemaChange($output, $this->schemaClosure(), []);
		$migration->postSchemaChange($output, $this->schemaClosure(), []);
	}

	public function testTheMigrationAsksTheContainerForNothing(): void {
		// Two collaborators, and neither of them talks to the container: the
		// app configuration and the settings service, which itself holds the
		// app configuration, a logger and a clock.
		$constructor = (new \ReflectionClass(Version001500Date20261012000000::class))->getConstructor();

		self::assertNotNull($constructor);

		$types = [];
		foreach ($constructor->getParameters() as $parameter) {
			$type = $parameter->getType();
			self::assertInstanceOf(\ReflectionNamedType::class, $type);
			$types[] = $type->getName();
		}

		self::assertSame([IAppConfig::class, SettingsService::class], $types);
	}
}
