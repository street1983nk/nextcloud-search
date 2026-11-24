<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\ExternalMountService;
use OCA\Findling\Service\StorageService;
use OCP\App\IAppManager;
use OCP\DB\IResult;
use OCP\DB\QueryBuilder\IExpressionBuilder;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\IDBConnection;
use OCP\IL10N;
use OCP\L10N\IFactory;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The list of admin mounts behind the storage selection of the admin page
 * (plan 45-03, EXCL-04, D-45-03).
 *
 * The database is a small fake over oc_external_mounts, the way
 * StorageServiceTest fakes its tables: the query is answered out of the rows
 * below, filtered by the type it was given, so a query without the type
 * filter shows up as a personal mount in the answer and not as a staged
 * answer in the wrong order.
 */
#[CoversClass(ExternalMountService::class)]
final class ExternalMountServiceTest extends TestCase {
	/** The rows of oc_external_mounts. @var list<array<string, mixed>> */
	private array $rows = [];

	private bool $failing = false;
	private int $queries = 0;
	private int $opened = 0;
	private int $closed = 0;

	/** The scalar parameters of the last query. @var list<mixed> */
	private array $scalars = [];

	/** Every log call as level, message and context. @var list<array{string, string, array<mixed>}> */
	private array $logs = [];

	/** The catalogue of files_external in the language of the page, source text to translation. @var array<string, string> */
	private array $catalogue = [];

	/** The apps whose catalogue was asked for. @var list<string> */
	private array $l10nApps = [];

	/** Every text handed to t(). @var list<string> */
	private array $translated = [];

	protected function setUp(): void {
		parent::setUp();

		$this->rows = [];
		$this->failing = false;
		$this->queries = 0;
		$this->opened = 0;
		$this->closed = 0;
		$this->scalars = [];
		$this->logs = [];
		$this->catalogue = [];
		$this->l10nApps = [];
		$this->translated = [];
	}

	private function service(bool $enabled = true): ExternalMountService {
		$appManager = $this->createMock(IAppManager::class);
		$appManager->method('isEnabledForAnyone')->willReturnCallback(
			static fn (string $appId): bool => $enabled && $appId === 'files_external',
		);
		$appManager->expects(self::never())->method('isEnabledForUser');

		$db = $this->createMock(IDBConnection::class);
		$db->method('getQueryBuilder')->willReturnCallback(fn (): IQueryBuilder => $this->queryBuilder());

		$factory = $this->createMock(IFactory::class);
		$factory->method('findLanguage')->willReturn('de');
		$factory->method('get')->willReturnCallback(function (string $app): IL10N {
			$this->l10nApps[] = $app;
			$l10n = $this->createMock(IL10N::class);
			$l10n->method('t')->willReturnCallback(function (string $text, array $parameters = []): string {
				$this->translated[] = $text;

				return $this->catalogue[$text] ?? $text;
			});

			return $l10n;
		});

		$logger = $this->createMock(LoggerInterface::class);
		foreach (['emergency', 'alert', 'critical', 'error', 'warning', 'notice', 'info', 'debug'] as $level) {
			$logger->method($level)->willReturnCallback(function (string|\Stringable $message, array $context = []) use ($level): void {
				$this->logs[] = [$level, (string)$message, $context];
			});
		}

		return new ExternalMountService($appManager, $db, $factory, $logger);
	}

	private function queryBuilder(): IQueryBuilder {
		$table = '';
		$scalars = [];

		$qb = $this->createMock(IQueryBuilder::class);
		$expr = $this->createMock(IExpressionBuilder::class);
		$expr->method('eq')->willReturn('x = :p');
		$qb->method('select')->willReturnSelf();
		$qb->method('where')->willReturnSelf();
		$qb->method('andWhere')->willReturnSelf();
		$qb->method('expr')->willReturn($expr);
		$qb->method('from')->willReturnCallback(static function (mixed $from) use ($qb, &$table): IQueryBuilder {
			$table = (string)$from;

			return $qb;
		});
		$qb->method('createNamedParameter')->willReturnCallback(static function (mixed $value) use (&$scalars): string {
			$scalars[] = $value;

			return ':p';
		});
		$qb->method('executeQuery')->willReturnCallback(function () use (&$table, &$scalars): IResult {
			$this->queries++;
			$this->scalars = $scalars;
			self::assertSame('external_mounts', $table);
			if ($this->failing) {
				throw new \RuntimeException('the table is not there');
			}

			$rows = array_values(array_filter(
				$this->rows,
				static fn (array $row): bool => in_array($row['type'], $scalars, true),
			));

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

	private function mount(int $id, string $mountPoint, string $backend, int $type = 1): void {
		$this->rows[] = ['mount_id' => $id, 'mount_point' => $mountPoint, 'storage_backend' => $backend, 'type' => $type];
	}

	public function testWithoutFilesExternalTheListIsEmptyWithoutAQuery(): void {
		$this->mount(4, '/Share', 'smb');
		$service = $this->service(false);

		self::assertFalse($service->enabled());
		self::assertSame([], $service->adminMounts());
		self::assertSame(0, $this->queries);
	}

	public function testOnlyAdminMountsAreListedSortedByMountPoint(): void {
		$this->mount(4, '/Zeta', 'smb');
		$this->mount(9, '/alpha', 'sftp');
		$this->mount(12, '/Private', 'smb', 2);

		$service = $this->service();
		self::assertTrue($service->enabled());
		self::assertSame([
			['id' => 9, 'mountPoint' => '/alpha', 'backend' => 'SFTP', 'duplicate' => false],
			['id' => 4, 'mountPoint' => '/Zeta', 'backend' => 'SMB/CIFS', 'duplicate' => false],
		], $service->adminMounts());

		self::assertSame(1, $this->queries);
		self::assertSame([StorageService::ADMIN_MOUNT_TYPE], $this->scalars);
		self::assertSame($this->opened, $this->closed);
	}

	/**
	 * One rule for the list and the confirmation (V-45-10-02, owner decision c
	 * of plan 45-19): a mount is a duplicate as soon as another entry shows the
	 * same mount point, whatever its type, because the confirmation names the
	 * mount point only and reads the same flag. Two mount points of the same
	 * type are no duplicates.
	 */
	public function testMountsThatShareAMountPointAreDuplicatesWhateverTheBackend(): void {
		$this->mount(17, '/Share', 'smb');
		$this->mount(5, '/Share', 'smb');
		$this->mount(8, '/Share', 'sftp');
		$this->mount(4, '/Beta', 'smb');
		$this->mount(3, '/Alpha', 'smb');

		self::assertSame([
			['id' => 3, 'mountPoint' => '/Alpha', 'backend' => 'SMB/CIFS', 'duplicate' => false],
			['id' => 4, 'mountPoint' => '/Beta', 'backend' => 'SMB/CIFS', 'duplicate' => false],
			['id' => 5, 'mountPoint' => '/Share', 'backend' => 'SMB/CIFS', 'duplicate' => true],
			['id' => 8, 'mountPoint' => '/Share', 'backend' => 'SFTP', 'duplicate' => true],
			['id' => 17, 'mountPoint' => '/Share', 'backend' => 'SMB/CIFS', 'duplicate' => true],
		], $this->service()->adminMounts());
	}

	public function testAnUnknownBackendIsShownByItsIdentifier(): void {
		$this->mount(3, '/Cloud', 'acme');

		self::assertSame('acme', $this->service()->adminMounts()[0]['backend']);
	}

	public function testAMountPointWithMarkupComesBackUnchanged(): void {
		$this->mount(3, '/<img src=x onerror=alert(1)>', 'local');

		$mounts = $this->service()->adminMounts();
		self::assertSame('/<img src=x onerror=alert(1)>', $mounts[0]['mountPoint']);
		self::assertSame('Local', $mounts[0]['backend']);
	}

	/**
	 * The type is shown in the language of the page, out of the catalogue of
	 * files_external (finding V-45-10-01): under German the list said "Local"
	 * where Nextcloud itself says "Lokal". The short texts of BACKEND_NAMES are
	 * keys of that catalogue in 34.0.3.
	 */
	public function testTheTypeIsShownInTheLanguageOfThePage(): void {
		$this->catalogue = ['Local' => 'Lokal', 'SMB/CIFS' => 'SMB/CIFS'];
		$this->mount(3, '/Daten', 'local');
		$this->mount(4, '/Share', 'smb');

		$mounts = $this->service()->adminMounts();
		self::assertSame(['Lokal', 'SMB/CIFS'], array_column($mounts, 'backend'));
		self::assertSame(['files_external'], array_values(array_unique($this->l10nApps)));
	}

	public function testTwoTranslatedTypesStillMarkTheirDuplicates(): void {
		$this->catalogue = ['Local' => 'Lokal'];
		$this->mount(11, '/Gemeinsam', 'local');
		$this->mount(12, '/Gemeinsam', 'local');

		self::assertSame([
			['id' => 11, 'mountPoint' => '/Gemeinsam', 'backend' => 'Lokal', 'duplicate' => true],
			['id' => 12, 'mountPoint' => '/Gemeinsam', 'backend' => 'Lokal', 'duplicate' => true],
		], $this->service()->adminMounts());
	}

	/** An identifier outside the table is no text of the catalogue and is never handed to t(). */
	public function testAnUnknownIdentifierIsNotTranslated(): void {
		$this->catalogue = ['acme' => 'Fremd'];
		$this->mount(3, '/Cloud', 'acme');

		self::assertSame('acme', $this->service()->adminMounts()[0]['backend']);
		self::assertNotContains('acme', $this->translated);
	}

	public function testARowWithoutAPositiveIdIsSkipped(): void {
		$this->mount(0, '/Zero', 'smb');
		$this->mount(-3, '/Negative', 'smb');
		$this->mount(6, '/Kept', 'smb');

		self::assertSame([6], array_column($this->service()->adminMounts(), 'id'));
	}

	public function testADatabaseErrorTravelsUpAndIsNoEmptyList(): void {
		// R-45-21-13: an empty list here was read as "no storage set up", the
		// page rendered an empty list, and the next save sent no excluded id
		// and lifted every exclusion. The error goes to the caller, which shows
		// no list at all; nothing is logged here, the caller logs a counter.
		$this->mount(4, '/Secret share', 'smb');
		$this->failing = true;

		try {
			$this->service()->adminMounts();
			self::fail('a failed read came back as a list');
		} catch (\Throwable $e) {
			self::assertNotInstanceOf(\PHPUnit\Framework\AssertionFailedError::class, $e);
		}
		self::assertSame([], $this->logs);
	}

	public function testTheBackendNamesCoverTheIdentifiersOfFilesExternal(): void {
		foreach (['amazons3', 'dav', 'ftp', 'local', 'owncloud', 'sftp', 'smb', 'swift', '\OC\Files\Storage\SFTP_Key', '\OC\Files\Storage\SMB_OC'] as $identifier) {
			self::assertArrayHasKey($identifier, ExternalMountService::BACKEND_NAMES);
		}
		self::assertSame('files_external', ExternalMountService::APP_ID_FILES_EXTERNAL);
	}
}
