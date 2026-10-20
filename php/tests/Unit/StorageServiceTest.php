<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\DB\IResult;
use OCP\DB\QueryBuilder\IExpressionBuilder;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\IMimeTypeLoader;
use OCP\IAppConfig;
use OCP\IDBConnection;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The storage question of the reconcile (plan 36-03, D-36-14, M-32-02).
 *
 * classifyAbsent() tells the container which of its storages that dropped out of
 * the mount list are deleted (no row in oc_storages) and which are only switched
 * off (carried by a provider a Findling switch turned off, and by nothing in the
 * mount list in force). Everything else stays in neither list, so the container
 * keeps its grace period for it.
 *
 * The database is a small fake over two tables rather than a list of staged
 * answers: every query is answered out of the rows below, filtered by the IN
 * parameters it was given, so a wrong column or a forgotten band shows up as a
 * wrong answer and not as an answer that was staged in the wrong order.
 * SettingsService is final and is built for real over a mocked app config, the
 * way the other suites build it.
 */
#[CoversClass(StorageService::class)]
final class StorageServiceTest extends TestCase {
	private const TEAM = 'OCA\GroupFolders\Mount\MountProvider';
	private const EXTERNAL = 'OCA\Files_External\Config\ConfigAdapter';
	private const HOME = 'OC\Files\Mount\LocalHomeMountProvider';

	private IDBConnection&MockObject $db;
	private IFileAccess&MockObject $fileAccess;

	/** The numeric ids oc_storages holds. @var list<int> */
	private array $storages = [];

	/** The rows of oc_mounts. @var list<array{storage_id: int, mount_provider_class: string}> */
	private array $mounts = [];

	/** The storage ids the mount list in force carries. @var list<int> */
	private array $listed = [];

	/** Every executed query as table and number of ids in its band. @var list<array{string, int}> */
	private array $bands = [];

	private int $opened = 0;
	private int $closed = 0;

	protected function setUp(): void {
		parent::setUp();

		$this->fileAccess = $this->createMock(IFileAccess::class);
		$this->fileAccess->method('getDistinctMounts')->willReturnCallback(
			fn (): \Generator => $this->listedMounts(),
		);

		$this->db = $this->createMock(IDBConnection::class);
		$this->db->method('getQueryBuilder')->willReturnCallback(fn (): IQueryBuilder => $this->queryBuilder());
	}

	/** @return \Generator<int, array{storage_id: int, root_id: int, overridden_root: int}> */
	private function listedMounts(): \Generator {
		foreach ($this->listed as $storageId) {
			yield ['storage_id' => $storageId, 'root_id' => 1000 + $storageId, 'overridden_root' => 2000 + $storageId];
		}
	}

	/**
	 * One query builder over the two fake tables. It remembers the table and the
	 * two kinds of IN parameter and answers executeQuery() out of them.
	 */
	private function queryBuilder(): IQueryBuilder {
		$table = '';
		$ints = null;
		$strings = null;

		$qb = $this->createMock(IQueryBuilder::class);
		$expr = $this->createMock(IExpressionBuilder::class);
		$expr->method('in')->willReturn('x IN (:p)');

		$qb->method('select')->willReturnSelf();
		$qb->method('selectDistinct')->willReturnSelf();
		$qb->method('where')->willReturnSelf();
		$qb->method('andWhere')->willReturnSelf();
		$qb->method('expr')->willReturn($expr);
		$qb->method('from')->willReturnCallback(function (mixed $from) use ($qb, &$table): IQueryBuilder {
			$table = (string)$from;

			return $qb;
		});
		$qb->method('createNamedParameter')->willReturnCallback(
			static function (mixed $value, mixed $type = null) use (&$ints, &$strings): string {
				if ($type === IQueryBuilder::PARAM_INT_ARRAY) {
					$ints = $value;
				} elseif ($type === IQueryBuilder::PARAM_STR_ARRAY) {
					$strings = $value;
				}

				return ':p';
			},
		);
		$qb->method('executeQuery')->willReturnCallback(function () use (&$table, &$ints, &$strings): IResult {
			self::assertIsArray($ints, 'every query of classifyAbsent carries its band as an int array');
			$this->bands[] = [$table, count($ints)];

			$rows = match ($table) {
				'storages' => array_map(
					static fn (int $id): array => ['numeric_id' => (string)$id],
					array_values(array_intersect($this->storages, $ints)),
				),
				'mounts' => array_values(array_filter(
					$this->mounts,
					static fn (array $row): bool => in_array($row['storage_id'], $ints, true)
						&& in_array($row['mount_provider_class'], (array)$strings, true),
				)),
				default => self::fail('a query against an unexpected table: ' . $table),
			};

			return $this->resultOf($rows);
		});

		return $qb;
	}

	/** @param list<array<string, mixed>> $rows */
	private function resultOf(array $rows): IResult {
		$this->opened++;
		$result = $this->createMock(IResult::class);
		$result->method('fetch')->willReturnCallback(static function () use (&$rows): mixed {
			$row = array_shift($rows);

			return $row ?? false;
		});
		$result->method('closeCursor')->willReturnCallback(function (): bool {
			$this->closed++;

			return true;
		});

		return $result;
	}

	private function service(bool $teamFolders = true, bool $external = false): StorageService {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueBool')->willReturnCallback(
			static fn (string $app, string $key, bool $default = false): bool => match ($key) {
				SettingsService::KEY_INDEX_TEAM_FOLDERS => $teamFolders,
				SettingsService::KEY_INDEX_EXTERNAL_STORAGE => $external,
				default => $default,
			},
		);
		$logger = $this->createMock(LoggerInterface::class);

		return new StorageService(
			$this->fileAccess,
			$this->createMock(IMimeTypeLoader::class),
			new SettingsService($appConfig, $logger, $this->createMock(ITimeFactory::class)),
			$this->db,
			$logger,
		);
	}

	public function testDeletedAndSwitchedOffStoragesAreToldApart(): void {
		// 7 exists and is mounted nowhere: the grace case, in neither list.
		// 9 exists and only external storage carries it, which is switched off.
		$this->storages = [7, 9, 40];
		$this->mounts = [
			['storage_id' => 9, 'mount_provider_class' => self::EXTERNAL],
			['storage_id' => 40, 'mount_provider_class' => self::HOME],
		];

		$answer = $this->service(external: false)->classifyAbsent([14, 15, 7, 9]);

		self::assertSame(['gone' => [14, 15], 'deselected' => [9]], $answer);
		self::assertSame($this->opened, $this->closed, 'every cursor is closed');
	}

	public function testAStorageOfASwitchThatIsOnIsNeverDeselected(): void {
		$this->storages = [7, 9];
		$this->mounts = [['storage_id' => 9, 'mount_provider_class' => self::EXTERNAL]];
		$this->listed = [9];

		$answer = $this->service(teamFolders: true, external: true)->classifyAbsent([14, 15, 7, 9]);

		self::assertSame(['gone' => [14, 15], 'deselected' => []], $answer);
		// Both switches on: there is no provider to look for, so oc_mounts is not asked.
		self::assertSame([['storages', 4]], $this->bands);
	}

	public function testAnEmptyQuestionAsksNothing(): void {
		$this->db->expects(self::never())->method('getQueryBuilder');

		self::assertSame(['gone' => [], 'deselected' => []], $this->service()->classifyAbsent([]));
		self::assertSame(['gone' => [], 'deselected' => []], $this->service()->classifyAbsent([0, -3]));
	}

	public function testThreeHundredIdsAreAskedInBandsAndAnsweredInFull(): void {
		$wanted = range(1, 300);
		// Every even id exists, every odd one is gone; 42 and 244 are Team Folders
		// with the switch off, 244 is carried by the mount list as well.
		$this->storages = array_values(array_filter($wanted, static fn (int $id): bool => $id % 2 === 0));
		$this->mounts = [
			['storage_id' => 42, 'mount_provider_class' => self::TEAM],
			['storage_id' => 244, 'mount_provider_class' => self::TEAM],
			['storage_id' => 244, 'mount_provider_class' => self::HOME],
		];
		$this->listed = [244];

		$answer = $this->service(teamFolders: false)->classifyAbsent(array_reverse($wanted));

		self::assertSame(array_values(array_filter($wanted, static fn (int $id): bool => $id % 2 === 1)), $answer['gone']);
		self::assertSame([42], $answer['deselected']);
		self::assertSame([['storages', 200], ['storages', 100], ['mounts', 150]], $this->bands);
		self::assertSame($this->opened, $this->closed, 'every cursor is closed');
	}

	public function testAStorageTheMountListStillCarriesIsNotDeselected(): void {
		// Team Folders switched off; 12 only through the Team Folder provider,
		// 9 through it as well but still in the mount list in force.
		$this->storages = [9, 12];
		$this->mounts = [
			['storage_id' => 9, 'mount_provider_class' => self::TEAM],
			['storage_id' => 12, 'mount_provider_class' => self::TEAM],
		];
		$this->listed = [9];

		$answer = $this->service(teamFolders: false, external: true)->classifyAbsent([12, 9, 12]);

		self::assertSame(['gone' => [], 'deselected' => [12]], $answer);
	}
}
