<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\SnippetPolicy;
use OCP\Constants;
use OCP\Files\Cache\ICacheEntry;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\ICachedMountInfo;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\File;
use OCP\Files\Folder;
use OCP\IAppConfig;
use OCP\IGroupManager;
use OCP\IUser;
use OCP\SystemTag\ISystemTagObjectMapper;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * E3 of plan 45-22: a hit of a file that the searching user may only see
 * under the watermark of Nextcloud Office gets no text excerpt.
 *
 * The way is the owner decision `Entscheid E3-Weg 45-22` (S3): with the
 * watermark on, a file the user does not own gets no excerpt under shareAll,
 * shareRead and shareDisabledDownload, an own file loses it under shareRead
 * when either its raw cache permissions or its node lack UPDATE, allGroups
 * takes the excerpts of every member of a listed group, allTags those of every
 * file with a listed tag, and a watermark mode this class does not know takes
 * them all. Whatever throws costs the excerpts of the page, never the hits.
 *
 * The world of every case: alice has her home on storage 1, bob on storage 2,
 * a Team Folder lives on storage 7. File 11 is bob's and reaches alice as a
 * share, file 12 is alice's own, file 13 lies in the Team Folder.
 *
 * Everything runs on mocks; the counters on the mocks are the statement that a
 * search without the watermark costs no query of its own.
 */
#[CoversClass(SnippetPolicy::class)]
final class SnippetPolicyTest extends TestCase {
	private const HOME_PROVIDER = 'OC\Files\Mount\LocalHomeMountProvider';

	private IAppConfig&MockObject $appConfig;
	private IFileAccess&MockObject $fileAccess;
	private IUserMountCache&MockObject $mountCache;
	private ISystemTagObjectMapper&MockObject $tagMapper;
	private IGroupManager&MockObject $groupManager;
	private LoggerInterface&MockObject $logger;

	/** @var array<string,string> */
	private array $config = [];

	/** @var list<string> keys of $config stored as lazy */
	private array $lazyKeys = [];

	/** @var array<int,array{int,int}> file id => storage id, permissions */
	private array $entries = [];

	/** @var array<int,bool> file id => isUpdateable() of the node */
	private array $updateable = [];

	protected function setUp(): void {
		parent::setUp();

		$this->appConfig = $this->createMock(IAppConfig::class);
		$this->fileAccess = $this->createMock(IFileAccess::class);
		$this->mountCache = $this->createMock(IUserMountCache::class);
		$this->tagMapper = $this->createMock(ISystemTagObjectMapper::class);
		$this->groupManager = $this->createMock(IGroupManager::class);
		$this->logger = $this->createMock(LoggerInterface::class);

		// As AppConfig of the server while its lazy values are not loaded: a
		// lazy key read without the lazy flag answers the default
		// (AppConfig.php stable34 l. 561-566, the lazy cache stays empty until
		// a lazy read asks for it); a lazy read also finds a key that is not lazy.
		$this->appConfig->method('getValueString')->willReturnCallback(
			fn (string $app, string $key, string $default = '', bool $lazy = false): string => $app === 'files' && array_key_exists($key, $this->config)
				&& ($lazy || !in_array($key, $this->lazyKeys, true))
				? $this->config[$key]
				: $default,
		);
		$this->appConfig->method('getKeys')->willReturnCallback(
			fn (string $app): array => $app === 'files' ? array_keys($this->config) : [],
		);
		$this->appConfig->method('isLazy')->willReturnCallback(
			fn (string $app, string $key): bool => $app === 'files' && in_array($key, $this->lazyKeys, true),
		);

		$this->fileAccess->method('getByFileIds')->willReturnCallback(
			function (array $fileIds): array {
				$entries = [];
				foreach ($fileIds as $fileId) {
					if (!isset($this->entries[$fileId])) {
						continue;
					}
					[$storageId, $permissions] = $this->entries[$fileId];
					$entry = $this->createMock(ICacheEntry::class);
					$entry->method('getStorageId')->willReturn($storageId);
					$entry->method('getPermissions')->willReturn($permissions);
					$entries[$fileId] = $entry;
				}

				return $entries;
			},
		);

		$this->mountCache->method('getMountsForUser')->willReturnCallback(
			fn (IUser $user): array => match ($user->getUID()) {
				'alice' => [$this->mount('/alice/files/Shared/', 'OCA\Files_Sharing\MountProvider', 2), $this->mount('/alice/', self::HOME_PROVIDER, 1), $this->mount('/alice/files/Team/', 'OCA\GroupFolders\Mount\MountProvider', 7)],
				'bob' => [$this->mount('/bob/', self::HOME_PROVIDER, 2)],
				default => [],
			},
		);

		$this->entries = [
			11 => [2, Constants::PERMISSION_ALL],
			12 => [1, Constants::PERMISSION_ALL],
			13 => [7, Constants::PERMISSION_ALL],
		];
		$this->updateable = [11 => true, 12 => true, 13 => true];
	}

	private function mount(string $mountPoint, string $provider, int $storageId): ICachedMountInfo&MockObject {
		$mount = $this->createMock(ICachedMountInfo::class);
		$mount->method('getMountPoint')->willReturn($mountPoint);
		$mount->method('getMountProvider')->willReturn($provider);
		$mount->method('getStorageId')->willReturn($storageId);

		return $mount;
	}

	private function user(string $uid): IUser&MockObject {
		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn($uid);

		return $user;
	}

	/**
	 * The user folder of the run, resolving every known file id to a readable
	 * node whose isUpdateable() answers what $this->updateable says.
	 */
	private function userFolder(?int &$resolved = null): Folder&MockObject {
		$folder = $this->createMock(Folder::class);
		$folder->method('getFirstNodeById')->willReturnCallback(
			function (int $fileId) use (&$resolved): ?File {
				$resolved = ($resolved ?? 0) + 1;
				if (!isset($this->updateable[$fileId])) {
					return null;
				}
				$file = $this->createMock(File::class);
				$file->method('isReadable')->willReturn(true);
				$file->method('isUpdateable')->willReturn($this->updateable[$fileId]);

				return $file;
			},
		);

		return $folder;
	}

	private function policy(): SnippetPolicy {
		return new SnippetPolicy(
			$this->appConfig,
			$this->fileAccess,
			$this->mountCache,
			$this->tagMapper,
			$this->groupManager,
			$this->logger,
		);
	}

	/**
	 * @param array<string,string> $modes
	 */
	private function watermark(array $modes): void {
		$this->config = ['watermark_enabled' => 'yes', 'watermark_text' => '{userId}'] + $modes;
	}

	// -- without the watermark ---------------------------------------------

	public function testWithoutTheWatermarkEveryExcerptStaysAndNothingIsAsked(): void {
		$this->config = ['watermark_enabled' => 'no', 'watermark_shareAll' => 'yes'];

		$this->fileAccess->expects(self::never())->method('getByFileIds');
		$this->mountCache->expects(self::never())->method('getMountsForUser');
		$this->tagMapper->expects(self::never())->method('getTagIdsForObjects');
		$this->groupManager->expects(self::never())->method('getUserGroupIds');
		$this->groupManager->expects(self::never())->method('isInGroup');
		$this->appConfig->expects(self::never())->method('getKeys');
		$resolved = 0;

		self::assertSame([11, 12, 13], $this->policy()->allowed($this->user('alice'), $this->userFolder($resolved), [11, 12, 13]));
		self::assertSame(0, $resolved);
	}

	public function testAMissingSwitchIsAWatermarkThatIsOff(): void {
		$this->config = [];
		$this->fileAccess->expects(self::never())->method('getByFileIds');

		self::assertSame([11, 12], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11, 12]));
	}

	public function testAnEmptySwitchIsAWatermarkThatIsOnAsInRichdocuments(): void {
		// PermissionManager.php line 175: everything but 'no' switches it on.
		$this->config = ['watermark_enabled' => '', 'watermark_shareAll' => 'yes'];

		self::assertSame([12], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11, 12, 13]));
	}

	public function testTheWatermarkWithoutAModeThatReachesASearchKeepsEveryExcerpt(): void {
		// Link modes and shareTalkPublic need a link or no user, and a search
		// always has a user.
		$this->watermark(['watermark_linkAll' => 'yes', 'watermark_linkSecure' => 'yes', 'watermark_shareTalkPublic' => 'yes']);

		self::assertSame([11, 12, 13], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11, 12, 13]));
	}

	// -- shareAll ----------------------------------------------------------

	public function testUnderShareAllAFileTheUserDoesNotOwnGetsNoExcerpt(): void {
		$this->watermark(['watermark_shareAll' => 'yes']);

		self::assertSame([12], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11, 12, 13]));
	}

	public function testAModeStoredAsLazyStillTakesTheExcerpt(): void {
		// R-45-21-02: richdocuments reads its modes through IConfig, which
		// answers non lazy values only (AllConfig.php stable34 l. 163-165,
		// AppConfig::getValue l. 1489-1494), so a mode an admin stored lazy
		// with occ does not watermark there. Findling reads it all the same and
		// suppresses the excerpt: one excerpt too few, never one too many.
		$this->watermark(['watermark_shareAll' => 'yes']);
		$this->lazyKeys = ['watermark_shareAll'];

		self::assertSame([12], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11, 12, 13]));
	}

	public function testAListStoredAsLazyStillCounts(): void {
		// The same for the list of a mode (R-45-21-02).
		$this->watermark(['watermark_allTags' => 'yes', 'watermark_allTagsList' => '5,9']);
		$this->lazyKeys = ['watermark_allTagsList'];
		$this->tagMapper->method('getTagIdsForObjects')->willReturn(['11' => ['9'], '12' => [], '13' => ['4']]);

		self::assertSame([12, 13], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11, 12, 13]));
	}

	public function testUnderShareAllTheOwnerKeepsTheExcerptOfTheSameFile(): void {
		$this->watermark(['watermark_shareAll' => 'yes']);

		self::assertSame([11], $this->policy()->allowed($this->user('bob'), $this->userFolder(), [11]));
	}

	public function testAUserWithoutAHomeMountOwnsNothing(): void {
		// No home mount in the mount cache means no file can be called theirs,
		// so every file is a foreign one: the strict direction.
		$this->watermark(['watermark_shareAll' => 'yes']);

		self::assertSame([], $this->policy()->allowed($this->user('carol'), $this->userFolder(), [11, 12]));
	}

	public function testAFileWithoutACacheEntryIsAForeignFile(): void {
		$this->watermark(['watermark_shareAll' => 'yes']);
		unset($this->entries[12]);

		self::assertSame([], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [12]));
	}

	// -- shareDisabledDownload ---------------------------------------------

	public function testUnderShareDisabledDownloadAShareWithoutDownloadGetsNoExcerptAndTheOwnerKeepsIt(): void {
		$this->watermark(['watermark_shareDisabledDownload' => 'yes']);

		self::assertSame([], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11]));
		self::assertSame([11], $this->policy()->allowed($this->user('bob'), $this->userFolder(), [11]));
	}

	public function testUnderShareDisabledDownloadAShareWithDownloadLosesItsExcerptAsWell(): void {
		// The fallback of the owner decision, see 45-AUDIT.md, section "E3
		// Erkennung an der Quelle": the attributes of the share that richdocuments
		// reads (the super share of the mount) cannot be reached with public OCP
		// APIs, so every foreign file loses its excerpt under this mode, also a
		// share that allows the download. Over-suppression, permitted by E3.
		$this->watermark(['watermark_shareDisabledDownload' => 'yes']);
		$this->entries[14] = [2, Constants::PERMISSION_READ];

		self::assertSame([], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11, 14]));
	}

	public function testUnderShareDisabledDownloadATeamFolderFileLosesItsExcerptAsWell(): void {
		// A Team Folder has no share at all, so richdocuments never watermarks
		// it under this mode; the fallback does not tell it from a share.
		$this->watermark(['watermark_shareDisabledDownload' => 'yes']);

		self::assertSame([12], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [12, 13]));
	}

	// -- shareRead ---------------------------------------------------------

	public function testUnderShareReadForeignFilesGetNoExcerptAndAnUpdatableOwnFileKeepsIt(): void {
		$this->watermark(['watermark_shareRead' => 'yes']);

		self::assertSame([12], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11, 12, 13]));
	}

	public function testUnderShareReadAnOwnFileWhoseRawPermissionsLackUpdateGetsNoExcerpt(): void {
		// (a) of the decision: the raw row out of getByFileIds.
		$this->watermark(['watermark_shareRead' => 'yes']);
		$this->entries[12] = [1, Constants::PERMISSION_READ];

		self::assertSame([], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [12]));
	}

	public function testUnderShareReadAnOwnFileWhoseNodeIsNotUpdateableGetsNoExcerpt(): void {
		// (b) of the decision: the wrapped view of the user, read off the node
		// out of SearchService::readableFile, even with a writable raw row.
		$this->watermark(['watermark_shareRead' => 'yes']);
		$this->updateable[12] = false;

		self::assertSame([], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [12]));
	}

	public function testUnderShareReadAnOwnFileWhoseNodeDoesNotResolveGetsNoExcerpt(): void {
		$this->watermark(['watermark_shareRead' => 'yes']);
		unset($this->updateable[12]);

		self::assertSame([], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [12]));
	}

	public function testUnderShareReadAThrowingNodeCostsOnlyItsOwnExcerpt(): void {
		$this->watermark(['watermark_shareRead' => 'yes']);
		$this->entries[15] = [1, Constants::PERMISSION_ALL];
		$folder = $this->createMock(Folder::class);
		$folder->method('getFirstNodeById')->willReturnCallback(
			function (int $fileId): ?File {
				if ($fileId === 15) {
					throw new \RuntimeException('storage gone');
				}
				$file = $this->createMock(File::class);
				$file->method('isReadable')->willReturn(true);
				$file->method('isUpdateable')->willReturn(true);

				return $file;
			},
		);

		self::assertSame([12], $this->policy()->allowed($this->user('alice'), $folder, [12, 15]));
	}

	public function testWithoutShareReadNoNodeIsResolved(): void {
		$this->watermark(['watermark_shareAll' => 'yes']);
		$resolved = 0;

		$this->policy()->allowed($this->user('alice'), $this->userFolder($resolved), [11, 12, 13]);

		self::assertSame(0, $resolved);
	}

	// -- allGroups ---------------------------------------------------------

	public function testUnderAllGroupsAMemberOfAListedGroupGetsNoExcerptEvenForOwnFiles(): void {
		$this->watermark(['watermark_allGroups' => 'yes', 'watermark_allGroupsList' => 'board,secure']);
		$this->groupManager->method('getUserGroupIds')->willReturnCallback(
			fn (IUser $user): array => $user->getUID() === 'alice' ? ['staff', 'secure'] : ['staff'],
		);

		self::assertSame([], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11, 12, 13]));
		self::assertSame([11], $this->policy()->allowed($this->user('bob'), $this->userFolder(), [11]));
	}

	public function testUnderAllGroupsAnEmptyListTakesNothing(): void {
		$this->watermark(['watermark_allGroups' => 'yes', 'watermark_allGroupsList' => '']);
		$this->groupManager->method('getUserGroupIds')->willReturn(['']);

		self::assertSame([12], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [12]));
	}

	// -- allTags -----------------------------------------------------------

	public function testUnderAllTagsAFileWithAListedTagGetsNoExcerptForAnybodyAndTheQueryIsBanded(): void {
		$this->watermark(['watermark_allTags' => 'yes', 'watermark_allTagsList' => '5,9']);
		$this->entries[16] = [1, Constants::PERMISSION_ALL];
		$this->tagMapper->expects(self::exactly(2))->method('getTagIdsForObjects')->willReturnCallback(
			static function (array $objectIds, string $type): array {
				self::assertSame('files', $type);
				$all = ['11' => ['5'], '12' => ['6'], '16' => [], '13' => ['9', '1']];

				return array_intersect_key($all, array_flip($objectIds));
			},
		);

		self::assertSame([12, 16], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11, 12, 16, 13]));
		self::assertSame([], $this->policy()->allowed($this->user('bob'), $this->userFolder(), [11]));
	}

	// -- several modes, unknown modes, failures ----------------------------

	public function testSeveralModesTakeTheUnionOfTheirSuppressions(): void {
		$this->watermark([
			'watermark_shareDisabledDownload' => 'yes',
			'watermark_allTags' => 'yes',
			'watermark_allTagsList' => '5',
		]);
		$this->entries[16] = [1, Constants::PERMISSION_ALL];
		$this->tagMapper->method('getTagIdsForObjects')->willReturn(['12' => ['5'], '16' => []]);

		self::assertSame([16], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [11, 12, 13, 16]));
	}

	public function testAWatermarkModeThisClassDoesNotKnowTakesEveryExcerpt(): void {
		$this->watermark(['watermark_shareFuture' => 'yes']);

		self::assertSame([], $this->policy()->allowed($this->user('bob'), $this->userFolder(), [11]));
	}

	public function testAnUnknownWatermarkKeyThatIsNotYesTakesNothing(): void {
		$this->watermark(['watermark_shareFuture' => 'no', 'watermark_futureList' => 'a,b']);

		self::assertSame([11], $this->policy()->allowed($this->user('bob'), $this->userFolder(), [11]));
	}

	public function testAWatermarkTextThatReadsYesIsNotAMode(): void {
		$this->config = ['watermark_enabled' => 'yes', 'watermark_text' => 'yes', 'watermark_allGroupsList' => 'yes', 'watermark_allTagsList' => 'yes', 'watermark_linkTagsList' => 'yes'];

		self::assertSame([11], $this->policy()->allowed($this->user('bob'), $this->userFolder(), [11]));
	}

	public function testADetectionThatThrowsCostsTheExcerptsOfThePageAndLogsNoName(): void {
		$this->watermark(['watermark_shareAll' => 'yes']);
		$fileAccess = $this->createMock(IFileAccess::class);
		$fileAccess->method('getByFileIds')->willThrowException(new \RuntimeException('database gone for alice, file Report.pdf'));
		$this->logger->expects(self::once())->method('warning')->with(
			self::stringStartsWith('Findling: '),
			self::callback(static fn (array $context): bool => array_keys($context) === ['count', 'class']
				&& $context['count'] === 3
				&& $context['class'] === \RuntimeException::class),
		);

		$policy = new SnippetPolicy($this->appConfig, $fileAccess, $this->mountCache, $this->tagMapper, $this->groupManager, $this->logger);

		self::assertSame([], $policy->allowed($this->user('bob'), $this->userFolder(), [11, 12, 13]));
	}

	public function testAConfigThatThrowsCostsEveryExcerpt(): void {
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willThrowException(new \RuntimeException('type conflict'));

		$policy = new SnippetPolicy($appConfig, $this->fileAccess, $this->mountCache, $this->tagMapper, $this->groupManager, $this->logger);

		self::assertSame([], $policy->allowed($this->user('bob'), $this->userFolder(), [11]));
	}

	public function testTheOrderOfTheIdsIsKept(): void {
		$this->watermark(['watermark_shareAll' => 'yes']);
		$this->entries[17] = [1, Constants::PERMISSION_ALL];

		self::assertSame([17, 12], $this->policy()->allowed($this->user('alice'), $this->userFolder(), [17, 11, 12]));
	}

	public function testOneRequestAsksForTheConfigAndTheHomeMountOnce(): void {
		$this->watermark(['watermark_shareAll' => 'yes']);
		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueString')->willReturnCallback(
			fn (string $app, string $key, string $default = ''): string => $this->config[$key] ?? $default,
		);
		$appConfig->expects(self::once())->method('getKeys')->willReturn(array_keys($this->config));
		$mountCache = $this->createMock(IUserMountCache::class);
		$mountCache->expects(self::once())->method('getMountsForUser')->willReturn([$this->mount('/alice/', self::HOME_PROVIDER, 1)]);

		$policy = new SnippetPolicy($appConfig, $this->fileAccess, $mountCache, $this->tagMapper, $this->groupManager, $this->logger);
		$alice = $this->user('alice');

		self::assertSame([12], $policy->allowed($alice, $this->userFolder(), [11, 12]));
		self::assertSame([12], $policy->allowed($alice, $this->userFolder(), [12, 13]));
	}

	public function testNoIdsAskNothing(): void {
		$this->watermark(['watermark_shareAll' => 'yes']);
		$this->fileAccess->expects(self::never())->method('getByFileIds');

		self::assertSame([], $this->policy()->allowed($this->user('alice'), $this->userFolder(), []));
	}
}
