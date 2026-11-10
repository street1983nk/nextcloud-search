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
 * The storage questions of the reconcile and of the coverage figure.
 *
 * classifyAbsent() tells the container which of its storages that dropped out of
 * the mount list are deleted (no row in oc_storages) and which are only switched
 * off (carried by a provider a Findling switch turned off, and by nothing in the
 * mount list in force). Everything else stays in neither list, so the container
 * keeps its grace period for it (plan 36-03, D-36-14, M-32-02).
 *
 * shareIdentity(), shareIdentities() and countingKeyGroups() give each storage
 * of the smb and sftp backends one share identity, host and share name folded,
 * the root apart and unfolded (plan 43-21, D-43-15, D-43-17, OE-1 a to OE-4 a),
 * against the shared catalogue backend/tests/fixtures/share_identity_cases.json,
 * which was typed by hand and whose md5 values backend/tests/
 * test_share_identity_cases.py recomputes. The catalogue is looked for the way
 * DocKeyServiceTest looks for its own: FINDLING_REPO_ROOT, dirname(__DIR__, 3)
 * locally, findling-src one directory above apps/ in the phpunit job. A missing
 * catalogue fails the suite.
 *
 * The database is a small fake over the tables rather than a list of staged
 * answers: every query is answered out of the rows below, filtered by the
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
	private const CATALOGUE = 'backend/tests/fixtures/share_identity_cases.json';
	private const CONFIG_KEYS = ['host', 'port', 'root', 'share', 'user'];

	private IDBConnection&MockObject $db;
	private IFileAccess&MockObject $fileAccess;

	/** The numeric ids oc_storages holds. @var list<int> */
	private array $storages = [];

	/** The string id of oc_storages per numeric id. @var array<int, string> */
	private array $storageKeys = [];

	/**
	 * The rows of oc_mounts; user_id and mount_id only where the share
	 * identity needs them.
	 *
	 * @var list<array<string, mixed>>
	 */
	private array $mounts = [];

	/** The rows of oc_external_mounts. @var list<array{mount_id: int, storage_backend: string}> */
	private array $externalMounts = [];

	/** The rows of oc_external_config. @var list<array{mount_id: int, key: string, value: string}> */
	private array $externalConfig = [];

	/** A table whose query throws, to stand for a missing app or a broken dialect. */
	private ?string $failing = null;

	/** The storage ids the mount list in force carries. @var list<int> */
	private array $listed = [];

	/** Every executed query as table and number of ids in its band. @var list<array{string, int}> */
	private array $bands = [];

	/** Every named parameter of every query. @var list<mixed> */
	private array $parameters = [];

	/** The columns each table was asked for. @var array<string, list<mixed>> */
	private array $selected = [];

	/** The string parameters of the IN clauses per table. @var array<string, list<string>> */
	private array $stringsPerTable = [];

	/** Every log call as level, message and context. @var list<array{string, string, array<mixed>}> */
	private array $logs = [];

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
	 * One query builder over the fake tables. It remembers the table, the
	 * selected columns and every parameter, and answers executeQuery() out of
	 * them.
	 */
	private function queryBuilder(): IQueryBuilder {
		$table = '';
		$ints = null;
		$strings = null;
		$scalars = [];
		$columns = [];

		$qb = $this->createMock(IQueryBuilder::class);
		$expr = $this->createMock(IExpressionBuilder::class);
		$expr->method('in')->willReturn('x IN (:p)');
		$expr->method('eq')->willReturn('x = :p');
		$expr->method('isNotNull')->willReturn('x IS NOT NULL');

		$record = static function (mixed ...$args) use ($qb, &$columns): IQueryBuilder {
			foreach ($args as $arg) {
				foreach ((array)$arg as $column) {
					$columns[] = $column;
				}
			}

			return $qb;
		};
		$qb->method('select')->willReturnCallback($record);
		$qb->method('selectDistinct')->willReturnCallback($record);
		$qb->method('where')->willReturnSelf();
		$qb->method('andWhere')->willReturnSelf();
		$qb->method('expr')->willReturn($expr);
		$qb->method('from')->willReturnCallback(function (mixed $from) use ($qb, &$table): IQueryBuilder {
			$table = (string)$from;

			return $qb;
		});
		$qb->method('createNamedParameter')->willReturnCallback(
			function (mixed $value, mixed $type = null) use (&$ints, &$strings, &$scalars): string {
				$this->parameters[] = $value;
				if ($type === IQueryBuilder::PARAM_INT_ARRAY) {
					$ints = $value;
				} elseif ($type === IQueryBuilder::PARAM_STR_ARRAY) {
					$strings = $value;
				} else {
					$scalars[] = $value;
				}

				return ':p';
			},
		);
		$qb->method('executeQuery')->willReturnCallback(function () use (&$table, &$ints, &$strings, &$scalars, &$columns): IResult {
			self::assertIsArray($ints, 'every query carries its band as an int array');
			$this->bands[] = [$table, count($ints)];
			$this->selected[$table] = $columns;
			if (is_array($strings)) {
				$this->stringsPerTable[$table] = array_values(array_map('strval', $strings));
			}
			if ($this->failing === $table) {
				throw new \RuntimeException('the table is not there');
			}

			$rows = match ($table) {
				'storages' => array_map(
					fn (int $id): array => ['numeric_id' => (string)$id, 'id' => $this->storageKeys[$id] ?? 'home::user' . $id],
					array_values(array_intersect(
						array_values(array_unique(array_merge($this->storages, array_keys($this->storageKeys)))),
						$ints,
					)),
				),
				// Two questions to oc_mounts: the provider list of classifyAbsent
				// (a string array) and the external mounts of a hashed id (one
				// provider and a mount id).
				'mounts' => is_array($strings)
					? array_values(array_filter(
						$this->mounts,
						static fn (array $row): bool => in_array($row['storage_id'], $ints, true)
							&& in_array($row['mount_provider_class'], $strings, true),
					))
					: array_values(array_filter(
						$this->mounts,
						static fn (array $row): bool => in_array($row['storage_id'], $ints, true)
							&& in_array($row['mount_provider_class'], $scalars, true)
							&& ($row['mount_id'] ?? null) !== null,
					)),
				'external_mounts' => array_values(array_filter(
					$this->externalMounts,
					static fn (array $row): bool => in_array($row['mount_id'], $ints, true)
						&& in_array($row['storage_backend'], (array)$strings, true),
				)),
				'external_config' => array_values(array_filter(
					$this->externalConfig,
					static fn (array $row): bool => in_array($row['mount_id'], $ints, true)
						&& in_array($row['key'], (array)$strings, true),
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
		foreach (['emergency', 'alert', 'critical', 'error', 'warning', 'notice', 'info', 'debug'] as $level) {
			$logger->method($level)->willReturnCallback(
				function (mixed $message, array $context = []) use ($level): void {
					$this->logs[] = [$level, (string)$message, $context];
				},
			);
		}

		return new StorageService(
			$this->fileAccess,
			$this->createMock(IMimeTypeLoader::class),
			new SettingsService($appConfig, $logger, $this->createMock(ITimeFactory::class)),
			$this->db,
			$logger,
		);
	}

	/** @return array<string, mixed> */
	private static function catalogue(): array {
		$base = dirname(__DIR__, 3);
		$candidates = [];
		$root = getenv('FINDLING_REPO_ROOT');
		if (is_string($root) && $root !== '') {
			$candidates[] = rtrim($root, '/\\') . '/' . self::CATALOGUE;
		}
		$candidates[] = $base . '/' . self::CATALOGUE;
		$candidates[] = $base . '/findling-src/' . self::CATALOGUE;
		// The phpunit job: apps/findling/tests/Unit, the repository in
		// findling-src at the workspace root, one directory above $base.
		$candidates[] = dirname(__DIR__, 4) . '/findling-src/' . self::CATALOGUE;

		foreach ($candidates as $file) {
			if (!is_file($file)) {
				continue;
			}
			$decoded = json_decode((string)file_get_contents($file), true, 32, JSON_THROW_ON_ERROR);
			self::assertIsArray($decoded);
			self::assertIsArray($decoded['cases'] ?? null);
			self::assertIsArray($decoded['hashed'] ?? null);

			return $decoded;
		}

		self::fail('share_identity_cases.json not found, looked at: ' . implode(', ', $candidates));
	}

	/**
	 * Puts one hashed catalogue entry into the fake tables: its stored md5 in
	 * oc_storages, one external mount of the user, its backend and its
	 * configuration.
	 *
	 * @param array<string, mixed> $entry
	 */
	private function stageHashed(int $storageId, int $mountId, array $entry): void {
		$this->storageKeys[$storageId] = (string)$entry['stored'];
		$this->mounts[] = [
			'storage_id' => $storageId,
			'user_id' => (string)$entry['mount_user'],
			'mount_id' => $mountId,
			'mount_provider_class' => self::EXTERNAL,
		];
		$this->externalMounts[] = ['mount_id' => $mountId, 'storage_backend' => (string)$entry['backend']];
		foreach ($entry['config'] as $key => $value) {
			$this->externalConfig[] = ['mount_id' => $mountId, 'key' => (string)$key, 'value' => (string)$value];
		}
	}

	/** @return array{parsed: int, hashedVerified: int, hashedUngrouped: int, placeholder: int, excluded: int} */
	private static function stats(int $parsed = 0, int $verified = 0, int $ungrouped = 0, int $placeholder = 0, int $excluded = 0): array {
		return [
			'parsed' => $parsed,
			'hashedVerified' => $verified,
			'hashedUngrouped' => $ungrouped,
			'placeholder' => $placeholder,
			'excluded' => $excluded,
		];
	}

	/**
	 * No log line of this service may carry a host, a share name, a root or a
	 * login name (T-43-61): every string out of the configuration and the ids
	 * is looked for in every message and every context value.
	 *
	 * @param list<string> $secrets
	 */
	private function assertNoLogCarries(array $secrets): void {
		foreach ($this->logs as [$level, $message, $context]) {
			$text = $message . ' ' . json_encode($context, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
			foreach ($secrets as $secret) {
				if (strlen($secret) < 3) {
					continue;
				}
				self::assertStringNotContainsStringIgnoringCase($secret, $text, 'a ' . $level . ' line carries a value of a storage');
			}
		}
	}

	// -- classifyAbsent (plan 36-03) --

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

	// -- one share identity per storage (plan 43-21, D-43-15, D-43-17) --

	public function testEveryCatalogueCaseYieldsItsHandTypedIdentity(): void {
		$cases = self::catalogue()['cases'];
		self::assertGreaterThanOrEqual(30, count($cases));

		foreach ($cases as $case) {
			$expected = $case['expected'];
			self::assertSame($expected, StorageService::shareIdentity((string)$case['id']), (string)$case['why']);
			// The counting key of 1.6.3 is the share without the root.
			self::assertSame($expected['share'] ?? null, StorageService::countingKey((string)$case['id']), (string)$case['why']);
		}
	}

	public function testEveryHashedCatalogueEntryNeedsAMatchingMd5(): void {
		foreach (self::catalogue()['hashed'] as $entry) {
			$this->storageKeys = [];
			$this->mounts = [];
			$this->externalMounts = [];
			$this->externalConfig = [];
			$this->stageHashed(17, 900, $entry);
			$service = $this->service(external: true);

			$expected = $entry['expected'] === null ? [] : [17 => $entry['expected']];
			self::assertSame($expected, $service->shareIdentities([17]), (string)$entry['name']);

			$want = match ((string)$entry['outcome']) {
				'verified' => self::stats(verified: 1),
				'excluded' => self::stats(excluded: 1),
				'ungrouped' => self::stats(ungrouped: 1),
				'placeholder' => self::stats(ungrouped: 1, placeholder: 1),
				default => self::fail('unknown outcome ' . (string)$entry['outcome']),
			};
			self::assertSame($want, $service->shareIdentityStats(), (string)$entry['name']);
		}
		self::assertSame($this->opened, $this->closed, 'every cursor is closed');
	}

	public function testTheMbozemSituationIsOneShareOfFortySevenStorages(): void {
		$groups = self::catalogue()['groups'];
		$ids = [];
		foreach ($groups['storages'] as $storage) {
			$this->storageKeys[(int)$storage['numeric_id']] = (string)$storage['id'];
			$ids[] = (int)$storage['numeric_id'];
		}

		$answer = $this->service(external: true)->countingKeyGroups(array_reverse($ids));

		self::assertSame($groups['expected'], $answer);
		self::assertCount(47, $answer[0]);
	}

	public function testTheCountersOfOneCallMatchTheCatalogue(): void {
		$catalogue = self::catalogue();
		$ids = [];
		$storageId = 1;
		foreach ($catalogue['cases'] as $case) {
			$this->storageKeys[$storageId] = (string)$case['id'];
			$ids[] = $storageId++;
		}
		$storageId = 1001;
		foreach ($catalogue['hashed'] as $entry) {
			$this->stageHashed($storageId, $storageId + 4000, $entry);
			$ids[] = $storageId++;
		}

		$service = $this->service(external: true);
		$identities = $service->shareIdentities($ids);

		self::assertSame($catalogue['stats'], $service->shareIdentityStats());
		self::assertCount($catalogue['stats']['parsed'] + $catalogue['stats']['hashedVerified'], $identities);
		$keys = array_keys($identities);
		$sorted = $keys;
		sort($sorted);
		self::assertSame($sorted, $keys, 'the answer is ordered by storage id');
		self::assertSame($this->opened, $this->closed, 'every cursor is closed');
	}

	public function testAHashedStorageWithAMatchingMd5JoinsItsShare(): void {
		$entry = self::catalogue()['hashed'][0];
		self::assertSame('verified', $entry['outcome']);
		$this->stageHashed(17, 900, $entry);
		$this->storageKeys[31] = 'smb::u01@192.168.98.246//Daten//';
		$this->storageKeys[40] = 'smb::u02@192.168.98.246//Archiv//';

		self::assertSame([[17, 31]], $this->service(external: true)->countingKeyGroups([40, 31, 17]));
	}

	public function testASecondCallReadsTheConfigurationAfresh(): void {
		// cron.php lives over many jobs, so there is no cache over the call.
		$entry = self::catalogue()['hashed'][0];
		$this->stageHashed(17, 900, $entry);
		$service = $this->service(external: true);

		self::assertSame([17 => $entry['expected']], $service->shareIdentities([17]));
		self::assertSame(self::stats(verified: 1), $service->shareIdentityStats());

		foreach ($this->externalConfig as $i => $row) {
			if ($row['key'] === 'root') {
				$this->externalConfig[$i]['value'] = '/Anderswo';
			}
		}

		self::assertSame([], $service->shareIdentities([17]));
		self::assertSame(self::stats(ungrouped: 1), $service->shareIdentityStats());
	}

	public function testTheConfigurationIsAskedForFiveKeysAndNeverForAPassword(): void {
		$entry = self::catalogue()['hashed'][0];
		$this->stageHashed(17, 900, $entry);
		$this->externalConfig[] = ['mount_id' => 900, 'key' => 'password', 'value' => 'never-read'];

		$this->service(external: true)->shareIdentities([17]);

		$keys = $this->stringsPerTable['external_config'] ?? [];
		sort($keys);
		self::assertSame(self::CONFIG_KEYS, $keys);
		self::assertNotContains('*', $this->selected['external_config'] ?? ['*']);
		self::assertNotContains('value', $this->selected['external_mounts'] ?? []);
		foreach ($this->parameters as $parameter) {
			foreach ((array)$parameter as $value) {
				self::assertNotSame('password', $value, 'no query names the password');
			}
		}
		self::assertSame([['storages', 1], ['mounts', 1], ['external_mounts', 1], ['external_config', 1]], $this->bands);
	}

	public function testOnlyExternalMountsOfSmbAndSftpAreRebuilt(): void {
		$entry = self::catalogue()['hashed'][0];
		$this->stageHashed(17, 900, $entry);
		// The same configuration on a WebDAV mount and on a mount of another provider.
		$this->stageHashed(18, 901, $entry);
		$this->externalMounts[1]['storage_backend'] = 'dav';
		$this->stageHashed(19, 902, $entry);
		$this->mounts[2]['mount_provider_class'] = self::TEAM;

		$service = $this->service(external: true);
		self::assertSame([17 => $entry['expected']], $service->shareIdentities([17, 18, 19]));
		// 18 and 19 are no smb or sftp mount of files_external: outside, like a home.
		self::assertSame(self::stats(verified: 1), $service->shareIdentityStats());
	}

	public function testAFailingConfigurationQueryLeavesHashedIdsUngroupedAndLogsCountersOnly(): void {
		$catalogue = self::catalogue();
		$entry = $catalogue['hashed'][0];
		$this->stageHashed(17, 900, $entry);
		$this->storageKeys[31] = 'smb::u01@192.168.98.246//Daten//';
		$this->failing = 'external_config';

		$service = $this->service(external: true);
		$answer = $service->shareIdentities([17, 31]);

		self::assertSame([31 => ['share' => 'smb::192.168.98.246//daten', 'root' => '']], $answer);
		self::assertSame(self::stats(parsed: 1, ungrouped: 1), $service->shareIdentityStats());
		$warnings = array_values(array_filter($this->logs, static fn (array $log): bool => $log[0] === 'warning'));
		self::assertCount(1, $warnings);
		foreach ($warnings[0][2] as $value) {
			self::assertTrue(is_int($value) || (is_string($value) && preg_match('/^[A-Za-z\\\\]+$/', $value) === 1), 'a context value that is no counter');
		}
		self::assertSame($this->opened, $this->closed, 'every cursor is closed');
	}

	public function testNoLogLineCarriesAHostAShareARootOrALogin(): void {
		$catalogue = self::catalogue();
		$secrets = ['192.168.98.246', 'Daten', 'daten'];
		$storageId = 1001;
		foreach ($catalogue['hashed'] as $entry) {
			$this->stageHashed($storageId, $storageId + 4000, $entry);
			$storageId++;
			$secrets[] = (string)$entry['mount_user'];
			foreach ($entry['config'] as $value) {
				$secrets[] = trim((string)$value, '/');
			}
		}
		$service = $this->service(external: true);

		$service->shareIdentities(range(1001, $storageId - 1));
		$this->failing = 'external_config';
		$service->shareIdentities(range(1001, $storageId - 1));
		$this->failing = 'mounts';
		$service->shareIdentities(range(1001, $storageId - 1));

		self::assertNotSame([], $this->logs, 'the failing rounds log, so the scan below has something to read');
		$this->assertNoLogCarries($secrets);
	}

	public function testUnhashedIdsAskNothingButTheStorages(): void {
		$this->storageKeys = [
			17 => 'smb::anna@fs.example//team//',
			31 => 'sftp::anna@fs.example//data/',
			5 => 'home::anna',
		];

		$service = $this->service(external: true);
		$service->shareIdentities([31, 5, 17, 17, 0, -4]);

		self::assertSame([['storages', 3]], $this->bands);
		self::assertSame(self::stats(parsed: 2), $service->shareIdentityStats());
	}

	public function testAnEmptyCallAsksNothingAndCountsNothing(): void {
		$this->db->expects(self::never())->method('getQueryBuilder');
		$service = $this->service(external: true);

		self::assertSame([], $service->shareIdentities([]));
		self::assertSame([], $service->shareIdentities([0, -3]));
		self::assertSame(self::stats(), $service->shareIdentityStats());
	}

	// -- Weg C, grouped by share since 1.6.3 (plans 39-01, 43-21) --

	public function testOneShareMountedForTwoUsersIsOneGroup(): void {
		// Root '/' as SMB.php writes it: share, slash, root with both slashes.
		$this->storageKeys = [
			31 => 'smb::bert@fs.example//team//',
			17 => 'smb::anna@fs.example//team//',
			5 => 'home::anna',
		];

		$groups = $this->service(external: true)->countingKeyGroups([31, 5, 17]);

		self::assertSame([[17, 31]], $groups);
		self::assertSame($this->opened, $this->closed, 'every cursor is closed');
	}

	public function testRootsWithTheUserInThemAreOneShareWithTwoRoots(): void {
		// $user in the root is replaced per user before the id is built: two
		// sub trees of one share. Since 1.6.3 they are one group, and the
		// roots stay apart in the identity, which is what keeps the documents
		// of the two trees apart in the document key (43-22).
		$this->storageKeys = [
			17 => 'smb::anna@fs.example//team//anna/',
			31 => 'smb::bert@fs.example//team//bert/',
		];

		self::assertSame([[17, 31]], $this->service(external: true)->countingKeyGroups([17, 31]));
		self::assertSame('anna', StorageService::shareIdentity($this->storageKeys[17])['root'] ?? null);
		self::assertSame('bert', StorageService::shareIdentity($this->storageKeys[31])['root'] ?? null);
	}

	public function testAnotherHostOrAnotherShareIsNeverAGroup(): void {
		$this->storageKeys = [
			17 => 'smb::anna@fs.example//team//',
			31 => 'smb::bert@fs2.example//team//',
			40 => 'smb::carl@fs.example//archive//',
		];

		self::assertSame([], $this->service(external: true)->countingKeyGroups([17, 31, 40]));
	}

	public function testALoginNameWithAnAtSignKeepsTheHostAfterTheLastOne(): void {
		self::assertSame('smb::fs.example//team', StorageService::countingKey('smb::anna@corp.example@fs.example//team//'));

		$this->storageKeys = [
			17 => 'smb::anna@corp.example@fs.example//team//',
			31 => 'smb::bert@fs.example//team//',
		];

		self::assertSame([[17, 31]], $this->service(external: true)->countingKeyGroups([17, 31]));
	}

	public function testSftpIsGroupedPerLoginWithItsPortAndOtherBackendsAreNot(): void {
		self::assertSame('sftp::anna@fs.example:2222', StorageService::countingKey('sftp::anna@fs.example:2222//data/'));
		self::assertNotSame(
			StorageService::countingKey('sftp::anna@fs.example:2222//data/'),
			StorageService::countingKey('sftp::bert@fs.example//data/'),
		);

		foreach ([
			'home::anna',
			'local::/var/www/data/',
			'object::store:amazon::bucket',
			'object::user:anna',
			'webdav::anna@dav.example/remote.php/webdav//',
			'owncloud::anna@cloud.example//',
			'amazon::bucket',
			'smb::fs.example//team//',
			'smb::@//team//',
			'smb::anna@fs.example',
			'',
		] as $storageId) {
			self::assertNull(StorageService::countingKey($storageId), $storageId);
			self::assertNull(StorageService::shareIdentity($storageId), $storageId);
		}
	}

	public function testAHashedIdWithoutAConfigurationIsNeverAGroup(): void {
		// Ids above 64 characters are stored as their md5 (Storage.php
		// adjustStorageId); without a configuration whose rebuilt id has the
		// same md5 they are never grouped.
		$hashedA = md5('smb::anna@fs.example//' . str_repeat('x', 80));
		$hashedB = md5('smb::bert@fs.example//' . str_repeat('x', 80));
		self::assertNull(StorageService::countingKey($hashedA));
		self::assertNull(StorageService::shareIdentity($hashedA));

		$this->storageKeys = [17 => $hashedA, 31 => $hashedB, 40 => $hashedA];

		self::assertSame([], $this->service(external: true)->countingKeyGroups([17, 31, 40]));
	}

	public function testADoubleSlashInTheLoginNameIsNeverAGroupAndOneInTheRootCollapses(): void {
		// Audit 40-01, B1: the first '//' ends the host part. A login name with
		// a '//' of its own leaves no '@' in front of it, so the id is not
		// grouped, which is the safe direction; a '//' further down the root
		// collapses, and different roots are one share with two roots.
		self::assertNull(StorageService::countingKey('smb::corp//anna@fs.example//team//'));
		self::assertSame(
			['share' => 'smb::fs.example//team', 'root' => 'a/b'],
			StorageService::shareIdentity('smb::anna@fs.example//team//a//b/'),
		);
		self::assertSame(
			StorageService::countingKey('smb::anna@fs.example//team//a/'),
			StorageService::countingKey('smb::bert@fs.example//team//b/'),
		);
		// SFTP per login (OE-4 a): a domain login is another login.
		self::assertNotSame(
			StorageService::countingKey('sftp::anna@fs.example:22//data/'),
			StorageService::countingKey('sftp::bert@corp.example@fs.example:22//data/'),
		);
	}

	public function testTheAnswerCarriesNumbersOnlyAndAsksInBands(): void {
		// 250 users of one share: one group of 250 storage ids, two bands.
		$this->storageKeys = [];
		foreach (range(1, 250) as $storageId) {
			$this->storageKeys[$storageId] = 'smb::user' . $storageId . '@fs.example//team//';
		}

		$groups = $this->service(external: true)->countingKeyGroups(array_reverse(range(1, 250)));

		self::assertSame([range(1, 250)], $groups);
		foreach ($groups as $group) {
			foreach ($group as $member) {
				self::assertIsInt($member);
			}
		}
		self::assertSame([['storages', 200], ['storages', 50]], $this->bands);
	}

	public function testFewerThanTwoStoragesAskNothing(): void {
		$this->db->expects(self::never())->method('getQueryBuilder');

		self::assertSame([], $this->service(external: true)->countingKeyGroups([]));
		self::assertSame([], $this->service(external: true)->countingKeyGroups([17]));
		self::assertSame([], $this->service(external: true)->countingKeyGroups([0, -3, 17]));
	}

	public function testHandedInIdentitiesAreGroupedWithoutAQuery(): void {
		// Plan 43-23: the overview asks shareIdentities() once and hands the
		// answer in; the grouping then reads nothing and takes only the
		// identities of the asked ids.
		$this->db->expects(self::never())->method('getQueryBuilder');
		$identities = [
			11 => ['share' => 'smb::fs.example//daten', 'root' => ''],
			14 => ['share' => 'smb::fs.example//daten', 'root' => 'projekt'],
			15 => ['share' => 'smb::fs.example//daten', 'root' => ''],
			21 => ['share' => 'smb::fs.example//archiv', 'root' => ''],
			22 => ['share' => 'smb::fs.example//archiv', 'root' => ''],
			99 => ['share' => 'smb::fs.example//archiv', 'root' => ''],
		];

		$groups = $this->service(external: true)->countingKeyGroups([22, 15, 11, 14, 21, 31], $identities);

		self::assertSame([[11, 14, 15], [21, 22]], $groups);
		self::assertSame([], $this->service(external: true)->countingKeyGroups([21, 31], $identities));
	}
}
