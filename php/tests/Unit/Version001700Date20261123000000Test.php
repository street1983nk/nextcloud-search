<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use Closure;
use OCA\Findling\AppInfo\Application;
use OCA\Findling\Migration\Version001700Date20261123000000;
use OCA\Findling\Service\ExAppService;
use OCP\IAppConfig;
use OCP\Migration\IOutput;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The one statement of the minor step migration of 1.7, and the one it must
 * never make (plan 45-26).
 *
 * It drops the recorded version of the container, as every minor step does
 * (Version001400Date20261006000000Test holds the reason): without it the search
 * answers no hits after the update 1.6.5 -> 1.7.0 until somebody opens the
 * settings page. The statement it must never make is a version of its own:
 * setValueString is expected never.
 *
 * The migration names no class of the app (issue #51) and carries the app id
 * and the key as literals; this test may name the classes, because here the
 * new ones are loaded, and holds each literal against its constant.
 */
#[CoversClass(Version001700Date20261123000000::class)]
final class Version001700Date20261123000000Test extends TestCase {
	private function schemaClosure(): Closure {
		return static function (): never {
			self::fail('this migration must not touch the schema');
		};
	}

	public function testTheClassNameIsTheFileName(): void {
		$file = (new \ReflectionClass(Version001700Date20261123000000::class))->getFileName();

		self::assertIsString($file);
		self::assertSame('Version001700Date20261123000000.php', basename($file));
	}

	public function testARecordedVersionIsDroppedAndNamedInTheOutput(): void {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturn('1.6.5');
		$appConfig->expects(self::once())
			->method('deleteKey')
			->with('findling', ExAppService::KEY_BACKEND_VERSION);
		$appConfig->expects(self::never())->method('setValueString');

		$output = $this->createMock(IOutput::class);
		$output->expects(self::once())
			->method('info')
			->with(self::stringContains('1.6.5'));

		$migration = new Version001700Date20261123000000($appConfig);

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

		$migration = new Version001700Date20261123000000($appConfig);

		$migration->postSchemaChange($output, $this->schemaClosure(), []);
	}

	public function testASecondRunDropsNothingAndThrowsNothing(): void {
		// A replay after a failed upgrade: the second reading is the empty
		// string because the first run deleted the key, so the second run has
		// to take the no-op branch and say so.
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturnOnConsecutiveCalls('1.6.5', '');
		$appConfig->expects(self::once())->method('deleteKey');
		$appConfig->expects(self::never())->method('setValueString');

		$said = [];
		$output = $this->createMock(IOutput::class);
		$output->expects(self::exactly(2))
			->method('info')
			->willReturnCallback(static function (string $message) use (&$said): void {
				$said[] = $message;
			});

		$migration = new Version001700Date20261123000000($appConfig);

		$migration->postSchemaChange($output, $this->schemaClosure(), []);
		$migration->postSchemaChange($output, $this->schemaClosure(), []);

		self::assertCount(2, $said);
		self::assertStringContainsString('1.6.5', $said[0]);
		self::assertSame('no recorded backend version to drop', $said[1]);
	}

	/**
	 * Issue #51: the migration names no class of the app, because an update
	 * runs with the classes of the old version loaded. The literals it carries
	 * instead are held against the constants here.
	 */
	public function testTheLiteralsMirrorTheConstantsOfTheApp(): void {
		self::assertSame(Application::APP_ID, Version001700Date20261123000000::APP_ID);
		self::assertSame(ExAppService::KEY_BACKEND_VERSION, Version001700Date20261123000000::BACKEND_VERSION_KEY);
	}

	public function testTheMigrationIsHandedTheAppConfigOnly(): void {
		// One collaborator, the app configuration: nothing that asks the
		// container, no settings service, no database.
		$constructor = (new \ReflectionClass(Version001700Date20261123000000::class))->getConstructor();
		self::assertNotNull($constructor);

		$types = [];
		foreach ($constructor->getParameters() as $parameter) {
			$type = $parameter->getType();
			self::assertInstanceOf(\ReflectionNamedType::class, $type);
			$types[] = $type->getName();
		}

		self::assertSame([IAppConfig::class], $types);
	}

	public function testTheMigrationHasNoSchemaStep(): void {
		$method = (new \ReflectionClass(Version001700Date20261123000000::class))->getMethod('changeSchema');

		self::assertNotSame(Version001700Date20261123000000::class, $method->getDeclaringClass()->getName());

		// And the step after the schema never calls the schema closure it is
		// handed: this one fails the test the moment it is called.
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturn('1.6.5');
		$migration = new Version001700Date20261123000000($appConfig);

		$migration->postSchemaChange($this->createMock(IOutput::class), $this->schemaClosure(), []);
	}
}
