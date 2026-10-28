<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use Closure;
use OCA\Findling\Migration\Version001600Date20261028000000;
use OCA\Findling\Service\ExAppService;
use OCP\IAppConfig;
use OCP\Migration\IOutput;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The one statement of the minor step migration of 1.6, and the one it must
 * never make.
 *
 * It drops the recorded version of the container, as every minor step does
 * (Version001400Date20261006000000Test holds the reason). Unlike 1.5 it marks
 * no recount: Weg C (plan 39-01) groups in ScanStatsService::totals() at read
 * time, so the stored counters stay valid across this update. The statement it
 * must never make is a version of its own: setValueString is expected never.
 *
 * The key is read out of ExAppService instead of copied into this file, so a
 * rename breaks this test rather than passing it against a string nobody
 * writes any more.
 */
#[CoversClass(Version001600Date20261028000000::class)]
final class Version001600Date20261028000000Test extends TestCase {
	private function key(): string {
		$value = (new \ReflectionClass(ExAppService::class))->getConstant('KEY_BACKEND_VERSION');

		self::assertIsString($value, 'KEY_BACKEND_VERSION is gone or is no longer a string');

		return $value;
	}

	private function schemaClosure(): Closure {
		return static function (): never {
			self::fail('this migration must not touch the schema');
		};
	}

	public function testTheClassNameIsTheFileName(): void {
		$file = (new \ReflectionClass(Version001600Date20261028000000::class))->getFileName();

		self::assertIsString($file);
		self::assertSame('Version001600Date20261028000000.php', basename($file));
	}

	public function testARecordedVersionIsDroppedAndNamedInTheOutput(): void {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturn('1.5.1');
		$appConfig->expects(self::once())
			->method('deleteKey')
			->with('findling', $this->key());
		$appConfig->expects(self::never())->method('setValueString');

		$output = $this->createMock(IOutput::class);
		$output->expects(self::once())
			->method('info')
			->with(self::stringContains('1.5.1'));

		$migration = new Version001600Date20261028000000($appConfig);

		$migration->postSchemaChange($output, $this->schemaClosure(), []);
	}

	public function testAnInstanceThatNeverRecordedOneIsLeftAlone(): void {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturn('');
		$appConfig->expects(self::never())->method('deleteKey');
		$appConfig->expects(self::never())->method('setValueString');

		$output = $this->createMock(IOutput::class);
		$output->expects(self::once())
			->method('info')
			->with('no recorded backend version to drop');

		$migration = new Version001600Date20261028000000($appConfig);

		$migration->postSchemaChange($output, $this->schemaClosure(), []);
	}

	public function testASecondRunDropsNothingAndThrowsNothing(): void {
		// The second reading is the empty string because the first run deleted
		// the key, so the second run has to take the no-op branch and say so.
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturnOnConsecutiveCalls('1.5.1', '');
		$appConfig->expects(self::once())->method('deleteKey');

		$output = $this->createMock(IOutput::class);
		$output->expects(self::exactly(2))
			->method('info')
			->with(self::logicalOr(
				self::stringContains('1.5.1'),
				self::identicalTo('no recorded backend version to drop'),
			));

		$migration = new Version001600Date20261028000000($appConfig);

		$migration->postSchemaChange($output, $this->schemaClosure(), []);
		$migration->postSchemaChange($output, $this->schemaClosure(), []);
	}

	public function testTheMigrationAsksTheContainerForNothing(): void {
		// One collaborator, the app configuration: no recount mark this time,
		// so no settings service either.
		$constructor = (new \ReflectionClass(Version001600Date20261028000000::class))->getConstructor();

		self::assertNotNull($constructor);

		$types = [];
		foreach ($constructor->getParameters() as $parameter) {
			$type = $parameter->getType();
			self::assertInstanceOf(\ReflectionNamedType::class, $type);
			$types[] = $type->getName();
		}

		self::assertSame([IAppConfig::class], $types);
	}
}
