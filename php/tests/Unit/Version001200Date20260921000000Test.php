<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use Closure;
use OCA\Findling\Migration\Version001200Date20260921000000;
use OCA\Findling\Service\ExAppService;
use OCP\IAppConfig;
use OCP\Migration\IOutput;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The one statement of the minor step migration, and the one it must never make.
 *
 * It drops the recorded version of the container when this half moves from
 * 1.1.0 to 1.2.0, because that number was an answer about a container from
 * before the update and the search refuses to answer while it disagrees with
 * the version of this half. The statement it must never make is the opposite
 * one: writing a version in here would tell an instance whose container really
 * is a minor behind that the two halves agree, and the search would then answer
 * with hits that neither half can vouch for. That is why the third test below
 * expects setValueString to be called never, rather than expecting it to be
 * called with something sensible.
 *
 * The cases are the four of Version001100Date20260911000000Test plus two this
 * one adds, and they are added because the plan of this file names them as the
 * properties that have to hold rather than be believed: a second run is a no-op
 * and throws nothing, and the migration asks the container for nothing at all.
 * The second of those is checked on the constructor, which is the only place a
 * migration could get hold of a collaborator that talks to the container.
 *
 * The key is read out of ExAppService instead of copied into this file, for the
 * reason ExAppServiceTest gives about the canary title: a rename of the
 * constant has to break a test or keep it honest, never pass it quietly against
 * a string nobody writes any more.
 */
#[CoversClass(Version001200Date20260921000000::class)]
final class Version001200Date20260921000000Test extends TestCase {
	private function key(): string {
		$value = (new \ReflectionClass(ExAppService::class))->getConstant('KEY_BACKEND_VERSION');

		self::assertIsString($value, 'KEY_BACKEND_VERSION is gone or is no longer a string');

		return $value;
	}

	private function schemaClosure(): Closure {
		// The signature wants one and this migration never calls it. A closure
		// that fails loudly says so: if a later edit starts touching the schema
		// here, this test has to be where that is noticed.
		return static function (): never {
			self::fail('this migration must not touch the schema');
		};
	}

	public function testARecordedVersionIsDropped(): void {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturn('1.1.0');
		$appConfig->expects(self::once())
			->method('deleteKey')
			->with('findling', $this->key());

		$migration = new Version001200Date20260921000000($appConfig);

		$migration->postSchemaChange($this->createMock(IOutput::class), $this->schemaClosure(), []);
	}

	public function testAnInstanceThatNeverRecordedOneIsLeftAlone(): void {
		// Every fresh installation, and every instance whose settings page was
		// never opened. There is nothing to drop and nothing to report as
		// dropped.
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturn('');
		$appConfig->expects(self::never())->method('deleteKey');

		$output = $this->createMock(IOutput::class);
		$output->expects(self::once())
			->method('info')
			->with('no recorded backend version to drop');

		$migration = new Version001200Date20260921000000($appConfig);

		$migration->postSchemaChange($output, $this->schemaClosure(), []);
	}

	public function testTheMigrationNeverWritesAVersionOfItsOwn(): void {
		// The load bearing one. A migration that guessed here would not fail
		// anything visibly; it would quietly turn a real drift into a search
		// that answers across a protocol break.
		foreach (['1.1.0', ''] as $recorded) {
			$appConfig = $this->createMock(IAppConfig::class);
			$appConfig->method('getValueString')->willReturn($recorded);
			$appConfig->expects(self::never())->method('setValueString');

			$migration = new Version001200Date20260921000000($appConfig);

			$migration->postSchemaChange($this->createMock(IOutput::class), $this->schemaClosure(), []);
		}
	}

	public function testTheDroppedVersionIsNamedInTheOutput(): void {
		// The admin reading an upgrade log has to be able to see which number
		// went, because it is the number the search was refusing over.
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturn('1.1.0');

		$output = $this->createMock(IOutput::class);
		$output->expects(self::once())
			->method('info')
			->with(self::stringContains('1.1.0'));

		$migration = new Version001200Date20260921000000($appConfig);

		$migration->postSchemaChange($output, $this->schemaClosure(), []);
	}

	public function testASecondRunDropsNothingAndThrowsNothing(): void {
		// Nextcloud can replay a migration after a failed upgrade, and one that
		// threw on the second run would turn a recoverable upgrade into a
		// broken instance. The second reading is the empty string because the
		// first run deleted the key, so the second run has to take the no-op
		// branch and say so.
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturnOnConsecutiveCalls('1.1.0', '');
		$appConfig->expects(self::once())->method('deleteKey');

		$output = $this->createMock(IOutput::class);
		$output->expects(self::exactly(2))->method('info');

		$migration = new Version001200Date20260921000000($appConfig);

		$migration->postSchemaChange($output, $this->schemaClosure(), []);
		$migration->postSchemaChange($output, $this->schemaClosure(), []);
	}

	public function testTheMigrationAsksTheContainerForNothing(): void {
		// A migration runs in maintenance mode, without a logged in user, and
		// possibly while AppAPI is restarting the container. It can only reach
		// the container through a collaborator it was handed, so the honest
		// place to check that it reaches nothing is the constructor: one
		// parameter, and it is the app configuration.
		$constructor = (new \ReflectionClass(Version001200Date20260921000000::class))->getConstructor();

		self::assertNotNull($constructor);

		$parameters = $constructor->getParameters();

		self::assertCount(1, $parameters, 'the migration was handed a second collaborator');

		$type = $parameters[0]->getType();

		self::assertInstanceOf(\ReflectionNamedType::class, $type);
		self::assertSame(IAppConfig::class, $type->getName());
	}
}
