<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\AdminViewService;
use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\ExternalMountService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\LockingCheckService;
use OCA\Findling\Service\ParallelSearchService;
use OCA\Findling\Service\PathResolverService;
use OCA\Findling\Service\ProbeService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\ReaderContext;
use OCA\Findling\Service\ScanStatsService;
use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCA\Findling\Settings\Admin;
use OCP\App\IAppManager;
use OCP\AppFramework\Services\IInitialState;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\DB\IResult;
use OCP\DB\QueryBuilder\IExpressionBuilder;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\IRootFolder;
use OCP\IAppConfig;
use OCP\ICacheFactory;
use OCP\IConfig;
use OCP\IDateTimeFormatter;
use OCP\IDBConnection;
use OCP\IL10N;
use OCP\IUserManager;
use OCP\IUserSession;
use OCP\L10N\IFactory;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The form of the admin page and where the list of admin mounts travels
 * (plan 45-03, EXCL-04).
 *
 * The list goes into the template parameters only. The initial state
 * 'bootstrap' stays the overview as it was, so neither the script nor the
 * poll of five seconds ever carries a mount point (T-45-12). A failure while
 * reading the list renders the page with an empty, switched off list and one
 * warning that carries a counter and nothing else.
 *
 * AdminViewService, ProbeService and ExternalMountService are final and are
 * built for real over doubles, the way SettingsControllerTest builds the view.
 */
#[CoversClass(Admin::class)]
final class AdminSettingsTest extends TestCase {
	/** @var array<string, mixed> every initial state by key */
	private array $initialStates = [];

	/** @var list<array{level: string, message: string, context: array<array-key, mixed>}> */
	private array $logLines = [];

	/** The rows of oc_external_mounts. @var list<array<string, mixed>> */
	private array $externalMounts = [];

	protected function setUp(): void {
		parent::setUp();

		$this->initialStates = [];
		$this->logLines = [];
		$this->externalMounts = [];
	}

	private function logger(): LoggerInterface {
		$logger = $this->createMock(LoggerInterface::class);
		foreach (['emergency', 'alert', 'critical', 'error', 'warning', 'notice', 'info', 'debug'] as $level) {
			$logger->method($level)->willReturnCallback(
				function (string|\Stringable $message, array $context = []) use ($level): void {
					$this->logLines[] = ['level' => $level, 'message' => (string)$message, 'context' => $context];
				},
			);
		}

		return $logger;
	}

	/** A database whose only table is oc_external_mounts, filtered by type. */
	private function mountDb(): IDBConnection {
		$db = $this->createMock(IDBConnection::class);
		$db->method('getQueryBuilder')->willReturnCallback(function (): IQueryBuilder {
			$scalars = [];
			$qb = $this->createMock(IQueryBuilder::class);
			foreach (['select', 'from', 'where', 'andWhere'] as $method) {
				$qb->method($method)->willReturnSelf();
			}
			$qb->method('expr')->willReturn($this->createMock(IExpressionBuilder::class));
			$qb->method('createNamedParameter')->willReturnCallback(static function (mixed $value) use (&$scalars): string {
				$scalars[] = $value;

				return ':p';
			});
			$qb->method('executeQuery')->willReturnCallback(function () use (&$scalars): IResult {
				$rows = array_values(array_filter(
					$this->externalMounts,
					static fn (array $row): bool => in_array($row['type'], $scalars, true),
				));
				$result = $this->createMock(IResult::class);
				$result->method('fetch')->willReturnCallback(static function () use (&$rows): mixed {
					return array_shift($rows) ?? false;
				});

				return $result;
			});

			return $qb;
		});

		return $db;
	}

	/** @param \Closure(string): bool $enabled the answer of isEnabledForAnyone */
	private function admin(\Closure $enabled): Admin {
		$logger = $this->logger();

		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueInt')->willReturnCallback(static fn (string $app, string $key, int $default = 0): int => $default);
		$appConfig->method('getValueBool')->willReturnCallback(static fn (string $app, string $key, bool $default = false): bool => $default);
		$appConfig->method('getValueString')->willReturnCallback(static fn (string $app, string $key, string $default = ''): string => $default);
		$appConfig->method('getValueArray')->willReturnCallback(static fn (string $app, string $key, array $default = []): array => $default);

		$time = $this->createMock(ITimeFactory::class);
		$time->method('getTime')->willReturn(1_800_000_000);

		$storage = $this->createMock(StorageService::class);
		$storage->method('getMounts')->willReturn([]);
		$jobList = $this->createMock(IJobList::class);
		$session = $this->createMock(IUserSession::class);
		$settings = new SettingsService($appConfig, $logger, $time);
		$exApp = $this->createMock(ExAppService::class);
		$exApp->method('adminSend')->willReturn(['kind' => ExAppService::ADMIN_UNREACHABLE, 'body' => null]);

		$view = new AdminViewService(
			$this->createMock(FileStateService::class),
			$this->createMock(QueueService::class),
			$exApp,
			new ScanStatsService($this->createMock(IDBConnection::class), $time, $logger),
			new PathResolverService(
				$this->createMock(IUserMountCache::class),
				$this->createMock(IFileAccess::class),
				$this->createMock(IRootFolder::class),
				$this->createMock(IDBConnection::class),
				$logger,
				new ReaderContext($session, $this->createMock(IUserManager::class)),
			),
			$storage,
			$settings,
			new ExclusionService($appConfig, $storage, $jobList, $logger),
			$appConfig,
			$session,
			$time,
			$this->createMock(IL10N::class),
			$this->createMock(IDateTimeFormatter::class),
			new ParallelSearchService($this->createMock(IAppManager::class)),
			new LockingCheckService($this->createMock(IConfig::class)),
			$jobList,
			$logger,
			$this->createMock(ICacheFactory::class),
		);

		$initialState = $this->createMock(IInitialState::class);
		$initialState->method('provideInitialState')->willReturnCallback(
			function (string $key, mixed $data): void {
				$this->initialStates[$key] = $data;
			},
		);

		$appManager = $this->createMock(IAppManager::class);
		$appManager->method('isEnabledForAnyone')->willReturnCallback($enabled);
		$factory = $this->createMock(IFactory::class);
		$factory->method('findLanguage')->willReturn('en');
		// The type names go through the catalogue of files_external (finding
		// V-45-10-01); English keeps them as they are.
		$factory->method('get')->willReturnCallback(function (string $app): IL10N {
			$l10n = $this->createMock(IL10N::class);
			$l10n->method('t')->willReturnCallback(static fn (string $text, array $parameters = []): string => $text);

			return $l10n;
		});

		return new Admin(
			$initialState,
			$view,
			new ProbeService($exApp, $settings, $this->createMock(IDateTimeFormatter::class), $time, $logger),
			new ExternalMountService($appManager, $this->mountDb(), $factory, $logger),
			$session,
			$logger,
		);
	}

	public function testTheMountListIsATemplateParameterAndNeverInTheInitialState(): void {
		$this->externalMounts = [
			['mount_id' => 4, 'mount_point' => '/Share', 'storage_backend' => 'smb', 'type' => 1],
			['mount_id' => 9, 'mount_point' => '/Mine', 'storage_backend' => 'smb', 'type' => 2],
		];

		$response = $this->admin(static fn (string $appId): bool => $appId === 'files_external')->getForm();
		$params = $response->getParams();

		self::assertSame(
			['enabled' => true, 'mounts' => [['id' => 4, 'mountPoint' => '/Share', 'backend' => 'SMB/CIFS', 'duplicate' => false]]],
			$params['externalMounts'] ?? null,
		);

		self::assertArrayHasKey('bootstrap', $this->initialStates);
		$bootstrap = $this->initialStates['bootstrap'];
		self::assertIsArray($bootstrap);
		self::assertArrayNotHasKey('externalMounts', $bootstrap);
		self::assertStringNotContainsString('/Share', json_encode($bootstrap, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES));

		// The rest of the parameters is the overview the script got as well.
		$withoutList = $params;
		unset($withoutList['externalMounts']);
		self::assertSame(array_keys($bootstrap), array_keys($withoutList));
		self::assertSame([], $this->initialStates['bootstrap']['rules']['excludedExternalMounts'] ?? null);
	}

	public function testWithoutFilesExternalTheListIsEmptyAndSwitchedOff(): void {
		$this->externalMounts = [['mount_id' => 4, 'mount_point' => '/Share', 'storage_backend' => 'smb', 'type' => 1]];

		$params = $this->admin(static fn (string $appId): bool => false)->getForm()->getParams();

		self::assertSame(['enabled' => false, 'mounts' => []], $params['externalMounts'] ?? null);
	}

	public function testAFailureWhileReadingTheListStillRendersThePage(): void {
		$params = $this->admin(static function (string $appId): bool {
			throw new \RuntimeException('the app manager is gone /Secret');
		})->getForm()->getParams();

		self::assertSame(['enabled' => false, 'mounts' => []], $params['externalMounts'] ?? null);
		self::assertArrayHasKey('bootstrap', $this->initialStates);

		$warnings = array_values(array_filter($this->logLines, static fn (array $line): bool => $line['level'] === 'warning'));
		self::assertCount(1, $warnings);
		self::assertSame('Findling: could not list the external storage for the admin page', $warnings[0]['message']);
		self::assertSame(['failed' => 1], $warnings[0]['context']);
		self::assertStringNotContainsString('Secret', json_encode($this->logLines, JSON_THROW_ON_ERROR));
	}
}
