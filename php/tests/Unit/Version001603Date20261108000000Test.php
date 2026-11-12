<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use Closure;
use OCA\Findling\Migration\Version001603Date20261108000000;
use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\ScanStatsService;
use OCA\Findling\Service\SettingsService;
use OCP\DB\IResult;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\IAppConfig;
use OCP\IDBConnection;
use OCP\Migration\IOutput;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The patch step to 1.6.3 (plan 43-06, D-43-06): the one time hint is pending
 * on an instance that counted before and stays off on a fresh installation.
 *
 * The signal is a row in findling_scan_stats (assumption A4). The cases: a row
 * sets the key to pending, no row sets nothing, a second run changes nothing,
 * a table that cannot be read sets nothing and does not throw (T-43-17), and
 * the migration touches no schema.
 */
#[CoversClass(Version001603Date20261108000000::class)]
final class Version001603Date20261108000000Test extends TestCase {
	/** @var array<string, int> the stored int keys of the app */
	private array $values = [];

	/** @var list<string> the tables the migration read */
	private array $tables = [];

	private function schemaClosure(): Closure {
		return static function (): never {
			self::fail('this migration must not touch the schema');
		};
	}

	private function appConfig(): IAppConfig {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueInt')->willReturnCallback(
			fn (string $app, string $key, int $default = 0): int => $this->values[$key] ?? $default,
		);
		$appConfig->method('setValueInt')->willReturnCallback(
			function (string $app, string $key, int $value): bool {
				self::assertSame('findling', $app);
				$this->values[$key] = $value;

				return true;
			},
		);

		return $appConfig;
	}

	/** A connection whose findling_scan_stats holds rows, none, or cannot be read. */
	private function db(?bool $hasRow): IDBConnection {
		$db = $this->createMock(IDBConnection::class);
		$db->method('getQueryBuilder')->willReturnCallback(function () use ($hasRow): IQueryBuilder {
			$qb = $this->createMock(IQueryBuilder::class);
			$qb->method('select')->willReturnSelf();
			$qb->method('from')->willReturnCallback(function (string $table) use ($qb): IQueryBuilder {
				$this->tables[] = $table;

				return $qb;
			});
			$qb->method('setMaxResults')->willReturnSelf();
			if ($hasRow === null) {
				$qb->method('executeQuery')->willThrowException(new \RuntimeException('no such table'));
			} else {
				$result = $this->createMock(IResult::class);
				$result->method('fetch')->willReturn($hasRow ? ['storage_id' => 7] : false);
				$qb->method('executeQuery')->willReturn($result);
			}

			return $qb;
		});

		return $db;
	}

	public function testAnInstanceThatCountedBeforeGetsThePendingHint(): void {
		$migration = new Version001603Date20261108000000($this->db(true), $this->appConfig());

		$migration->postSchemaChange($this->createMock(IOutput::class), $this->schemaClosure(), []);

		self::assertSame(SettingsService::COVERAGE_HINT_PENDING, $this->values[SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT] ?? null);
		self::assertSame(['findling_scan_stats'], $this->tables);
	}

	public function testAFreshInstallationGetsNoHint(): void {
		$migration = new Version001603Date20261108000000($this->db(false), $this->appConfig());

		$migration->postSchemaChange($this->createMock(IOutput::class), $this->schemaClosure(), []);

		self::assertArrayNotHasKey(SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT, $this->values);
	}

	public function testASecondRunChangesNothing(): void {
		$migration = new Version001603Date20261108000000($this->db(true), $this->appConfig());
		$output = $this->createMock(IOutput::class);

		$migration->postSchemaChange($output, $this->schemaClosure(), []);
		self::assertSame(1, $this->values[SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT]);

		// A stamp written by the page between the two runs stays as it is.
		$this->values[SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT] = 1_800_000_000;
		$this->tables = [];
		$migration->postSchemaChange($output, $this->schemaClosure(), []);

		self::assertSame(1_800_000_000, $this->values[SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT]);
		self::assertSame([], $this->tables, 'the second run read the table again');
	}

	public function testATableThatCannotBeReadSetsNothingAndThrowsNothing(): void {
		$output = $this->createMock(IOutput::class);
		$output->expects(self::once())
			->method('warning')
			->with(self::logicalNot(self::stringContains('no such table')));

		$migration = new Version001603Date20261108000000($this->db(null), $this->appConfig());

		$migration->postSchemaChange($output, $this->schemaClosure(), []);

		self::assertArrayNotHasKey(SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT, $this->values);
	}

	/**
	 * Issue #51: the migration names no class of the app, because an update
	 * runs with the classes of the old version loaded. The literals it carries
	 * instead are held against the constants here, where the new classes are
	 * the loaded ones.
	 */
	public function testTheLiteralsMirrorTheConstantsOfTheApp(): void {
		self::assertSame(Application::APP_ID, Version001603Date20261108000000::APP_ID);
		self::assertSame(SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT, Version001603Date20261108000000::HINT_KEY);
		self::assertSame(SettingsService::COVERAGE_HINT_PENDING, Version001603Date20261108000000::HINT_PENDING);
		self::assertSame(ScanStatsService::TABLE_NAME, Version001603Date20261108000000::SCAN_STATS_TABLE);
	}

	public function testTheMigrationHasNoSchemaStep(): void {
		$method = (new \ReflectionClass(Version001603Date20261108000000::class))->getMethod('changeSchema');

		self::assertNotSame(Version001603Date20261108000000::class, $method->getDeclaringClass()->getName());
	}

	public function testTheMigrationIsHandedTheDatabaseAndTheAppConfigOnly(): void {
		$constructor = (new \ReflectionClass(Version001603Date20261108000000::class))->getConstructor();
		self::assertNotNull($constructor);

		$types = [];
		foreach ($constructor->getParameters() as $parameter) {
			$type = $parameter->getType();
			self::assertInstanceOf(\ReflectionNamedType::class, $type);
			$types[] = $type->getName();
		}

		self::assertSame([IDBConnection::class, IAppConfig::class], $types);
	}
}
