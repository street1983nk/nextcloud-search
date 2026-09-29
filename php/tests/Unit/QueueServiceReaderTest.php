<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Db\QueueFile;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\ReaderContext;
use OCA\Findling\Service\StorageService;
use OCP\BackgroundJob\IJobList;
use OCP\Files\Config\ICachedMountFileInfo;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\IAppConfig;
use OCP\IDBConnection;
use OCP\IUser;
use OCP\IUserManager;
use OCP\IUserSession;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * Who reads a queued file, and what the row says when nobody may (issue #14).
 *
 * The defect in one sentence: the reader of a file used to be the first name
 * of its user list in alphabetical order, whether that name could read the
 * file or not. On a Team Folder with advanced permissions every member has a
 * mount on every file, so the first member was often somebody the ACL closed
 * the file to, and the row ended as skipped(gone), "File no longer present",
 * for a file that was there all along.
 *
 * The cases below go through claim(), the one public way into describe(), and
 * they stage exactly one content row. Everything around it is a double except
 * ExclusionService, which is final and is built for real over an app config
 * that holds no exclusion, so its prefix check costs nothing and decides
 * nothing here.
 */
#[CoversClass(QueueService::class)]
final class QueueServiceReaderTest extends TestCase {
	private const FILE_ID = 4242;
	private const ROW_ID = 17;

	private QueueMapper&MockObject $queueMapper;
	private FileStateService&MockObject $fileStateService;
	private IUserMountCache&MockObject $mountCache;
	private IRootFolder&MockObject $rootFolder;
	private IUserSession&MockObject $session;
	private ?IUser $active = null;

	protected function setUp(): void {
		parent::setUp();

		// A stateful session: getUser() answers what setVolatileActiveUser()
		// stored last, so the ordering cases below observe who is active at the
		// moment a folder is set up and a node is looked up.
		$this->session = $this->createMock(IUserSession::class);
		$this->session->method('getUser')->willReturnCallback(fn (): ?IUser => $this->active);
		$this->session->method('setVolatileActiveUser')->willReturnCallback(function (?IUser $user): void {
			$this->active = $user;
		});

		$this->queueMapper = $this->createMock(QueueMapper::class);
		$this->fileStateService = $this->createMock(FileStateService::class);
		$this->mountCache = $this->createMock(IUserMountCache::class);
		$this->rootFolder = $this->createMock(IRootFolder::class);

		$row = new QueueFile();
		$row->setId(self::ROW_ID);
		$row->setFileId(self::FILE_ID);
		// Non zero on purpose: a zero would send describe() to the mount point
		// of the node for the two ids, which is a different question.
		$row->setStorageId(3);
		$row->setRootId(5);
		$row->setSize(100);
		$row->setRetries(1);
		$row->setKind(QueueMapper::KIND_CONTENT);

		$this->queueMapper->method('claimBatch')->willReturnCallback(
			static fn (int $limit, int $maxBytes, string $kind): array => $kind === QueueMapper::KIND_CONTENT ? [$row] : [],
		);
	}

	private function service(): QueueService {
		$storageService = $this->createMock(StorageService::class);
		$exclusions = new ExclusionService(
			$this->createMock(IAppConfig::class),
			$storageService,
			$this->createMock(IJobList::class),
			$this->createMock(LoggerInterface::class),
		);

		return new QueueService(
			$this->queueMapper,
			$this->fileStateService,
			$exclusions,
			$storageService,
			$this->mountCache,
			$this->rootFolder,
			$this->createMock(IDBConnection::class),
			$this->createMock(LoggerInterface::class),
			$this->readerContext(),
		);
	}

	private function readerContext(): ReaderContext {
		$userManager = $this->createMock(IUserManager::class);
		$userManager->method('get')->willReturnCallback(function (string $uid): IUser {
			$user = $this->createMock(IUser::class);
			$user->method('getUID')->willReturn($uid);

			return $user;
		});

		return new ReaderContext($this->session, $userManager);
	}

	private function activeUid(): ?string {
		return $this->active?->getUID();
	}

	/**
	 * The mount list of the file, one mount per name, in the order given.
	 *
	 * @param list<string> $userIds
	 */
	private function mountsFor(array $userIds): void {
		$mounts = [];
		foreach ($userIds as $userId) {
			$user = $this->createMock(IUser::class);
			$user->method('getUID')->willReturn($userId);
			$mount = $this->createMock(ICachedMountFileInfo::class);
			$mount->method('getUser')->willReturn($user);
			$mounts[] = $mount;
		}

		$this->mountCache->method('getMountsForFileId')->with(self::FILE_ID)->willReturn($mounts);
	}

	/**
	 * A home folder per name. null resolves nothing, a File is handed out as is.
	 *
	 * @param array<string, ?File> $nodes
	 */
	private function foldersResolving(array $nodes): void {
		$folders = [];
		foreach ($nodes as $userId => $node) {
			$folder = $this->createMock(Folder::class);
			$folder->method('getFirstNodeById')->with(self::FILE_ID)->willReturn($node);
			$folder->method('getRelativePath')->willReturn('/admins-hh/Vertrag.pdf');
			$folders[$userId] = $folder;
		}

		$this->rootFolder->method('getUserFolder')->willReturnCallback(
			static fn (string $userId): Folder => $folders[$userId],
		);
	}

	private function file(bool $readable): File&MockObject {
		$file = $this->createMock(File::class);
		$file->method('isReadable')->willReturn($readable);
		$file->method('getName')->willReturn('Vertrag.pdf');
		$file->method('getPath')->willReturn('/whoever/files/admins-hh/Vertrag.pdf');
		$file->method('getMimetype')->willReturn('application/pdf');
		$file->method('getSize')->willReturn(100);
		$file->method('getMTime')->willReturn(1_700_000_000);
		$file->method('getEtag')->willReturn('etag');

		return $file;
	}

	public function testAMemberTheAclClosesTheFileToIsPassedOverForTheNextOne(): void {
		// The case of the issue. anna sorts first and reaches a node without
		// the read bit, bernd may read it; bernd reads the bytes, and the access
		// list still names both, because who may find a file is the question
		// of the recheck and not of this choice.
		$this->mountsFor(['bernd', 'anna']);
		$this->foldersResolving(['anna' => $this->file(false), 'bernd' => $this->file(true)]);
		$this->fileStateService->expects(self::never())->method('record');

		$sources = $this->service()->claim(32, 1_000_000);

		self::assertArrayHasKey(self::ROW_ID, $sources);
		self::assertSame('bernd', $sources[self::ROW_ID]['fetchAs']);
		self::assertSame(['anna', 'bernd'], $sources[self::ROW_ID]['userIds']);
	}

	public function testAMemberWhoDoesNotReachTheFileAtAllIsPassedOverAsWell(): void {
		// The other shape of the same ACL: the wrapper hides the node, so the
		// lookup answers nothing for anna instead of a closed node.
		$this->mountsFor(['anna', 'bernd']);
		$this->foldersResolving(['anna' => null, 'bernd' => $this->file(true)]);

		$sources = $this->service()->claim(32, 1_000_000);

		self::assertSame('bernd', $sources[self::ROW_ID]['fetchAs'] ?? null);
	}

	public function testTheReportedTeamFolderWithTheFirstTwoOfFourMembersClosedIsReadByTheThird(): void {
		// The instance of the reporter of #14: four members of admins-hh, and
		// the ACL closes the file to the first two in alphabetical order, one
		// by hiding the node and one by taking the read bit away. carla reads
		// it, dora is not asked, and the access list still names all four.
		$this->mountsFor(['dora', 'carla', 'bernd', 'anna']);
		$this->foldersResolving([
			'anna' => null,
			'bernd' => $this->file(false),
			'carla' => $this->file(true),
			'dora' => $this->file(true),
		]);
		$this->fileStateService->expects(self::never())->method('record');

		$sources = $this->service()->claim(32, 1_000_000);

		self::assertSame('carla', $sources[self::ROW_ID]['fetchAs'] ?? null);
		self::assertSame(['anna', 'bernd', 'carla', 'dora'], $sources[self::ROW_ID]['userIds'] ?? null);
	}

	public function testTheFirstNameStaysTheReaderWhenItMayRead(): void {
		// The ordinary file, and the order is unchanged: a retried row is read
		// in the same context as before the fix.
		$this->mountsFor(['anna', 'bernd']);
		$this->foldersResolving(['anna' => $this->file(true), 'bernd' => $this->file(true)]);

		$sources = $this->service()->claim(32, 1_000_000);

		self::assertSame('anna', $sources[self::ROW_ID]['fetchAs'] ?? null);
	}

	public function testAFileThereAndClosedToEveryoneAskedIsUnreadableAndNotGone(): void {
		// The new sentence. Nobody asked may read it, somebody reaches it, so
		// the remedy is a permission setting and not "it was deleted".
		$this->mountsFor(['anna', 'bernd']);
		$this->foldersResolving(['anna' => $this->file(false), 'bernd' => null]);
		$this->fileStateService->expects(self::once())
			->method('record')
			->with(self::FILE_ID, 'skipped', 'unreadable');
		$this->queueMapper->expects(self::once())->method('acknowledge')->with([self::ROW_ID]);

		self::assertSame([], $this->service()->claim(32, 1_000_000));
	}

	public function testAFileTheWrapperHidesFromEveryMemberIsUnreadableAndNotGone(): void {
		// The review finding behind the second fix of #14. The ACL wrapper can
		// hide a node entirely, and then the lookup answers nothing for every
		// member, exactly as for a deleted file. The mount cache still names
		// anna and bernd, and it only does so for an id the file cache still
		// holds, so the file is there and gone would be a claim nobody checked.
		$this->mountsFor(['anna', 'bernd']);
		$this->foldersResolving(['anna' => null, 'bernd' => null]);
		$this->fileStateService->expects(self::once())
			->method('record')
			->with(self::FILE_ID, 'skipped', 'unreadable');

		self::assertSame([], $this->service()->claim(32, 1_000_000));
	}

	public function testAReaderBehindTheTryLimitMakesTheFileUnreadableAndNotGone(): void {
		// Twenty one members, and only the last one in alphabetical order may
		// read the file. The first twenty are asked and the twenty first is
		// not, because each name costs a mount setup. The verdict is
		// unreadable, which is true, and never gone, which the truncated list
		// cannot know.
		$userIds = [];
		$nodes = [];
		for ($i = 1; $i <= 21; $i++) {
			$userId = sprintf('member%02d', $i);
			$userIds[] = $userId;
			$nodes[$userId] = $i === 21 ? $this->file(true) : $this->file(false);
		}
		$this->mountsFor($userIds);
		$this->foldersResolving($nodes);
		$this->fileStateService->expects(self::once())
			->method('record')
			->with(self::FILE_ID, 'skipped', 'unreadable');

		self::assertSame([], $this->service()->claim(32, 1_000_000));
	}

	public function testAMemberWhoseFolderCannotBeSetUpMakesTheFileUnreadableAndNotGone(): void {
		// A mount row whose user is gone since it was written: the folder of
		// that name cannot be built, and the file is still in the file cache.
		$this->mountsFor(['anna']);
		$this->rootFolder->method('getUserFolder')->willThrowException(new \RuntimeException('no such user'));
		$this->fileStateService->expects(self::once())
			->method('record')
			->with(self::FILE_ID, 'skipped', 'unreadable');

		self::assertSame([], $this->service()->claim(32, 1_000_000));
	}

	public function testAFileWithoutAnyMountIsGone(): void {
		$this->mountsFor([]);
		$this->rootFolder->expects(self::never())->method('getUserFolder');
		$this->fileStateService->expects(self::once())
			->method('record')
			->with(self::FILE_ID, 'skipped', 'gone');

		self::assertSame([], $this->service()->claim(32, 1_000_000));
	}

	public function testEveryMemberIsTheActiveUserWhileTheirFolderIsSetUpAndTheNodeIsLookedUp(): void {
		// The second round of #14. groupfolders decides "in share" from the
		// active user when the mount is built, so the folder setup and the
		// lookup of every member tried must happen with that member active, and
		// the one who was active before is active again after the claim.
		$before = $this->createMock(IUser::class);
		$before->method('getUID')->willReturn('admin');
		$this->active = $before;
		$this->mountsFor(['anna', 'bernd', 'carla']);

		$setUpAs = [];
		$lookedUpAs = [];
		$nodes = ['anna' => null, 'bernd' => $this->file(false), 'carla' => $this->file(true)];
		$folders = [];
		foreach ($nodes as $userId => $node) {
			$folder = $this->createMock(Folder::class);
			$folder->method('getFirstNodeById')->willReturnCallback(function () use ($userId, $node, &$lookedUpAs): ?File {
				$lookedUpAs[] = [$userId, $this->activeUid()];

				return $node;
			});
			$folder->method('getRelativePath')->willReturn('/admins-hh/Vertrag.pdf');
			$folders[$userId] = $folder;
		}
		$this->rootFolder->method('getUserFolder')->willReturnCallback(
			function (string $userId) use ($folders, &$setUpAs): Folder {
				$setUpAs[] = [$userId, $this->activeUid()];

				return $folders[$userId];
			},
		);

		$sources = $this->service()->claim(32, 1_000_000);

		self::assertSame('carla', $sources[self::ROW_ID]['fetchAs'] ?? null);
		self::assertSame([['anna', 'anna'], ['bernd', 'bernd'], ['carla', 'carla']], $setUpAs);
		self::assertSame([['anna', 'anna'], ['bernd', 'bernd'], ['carla', 'carla']], $lookedUpAs);
		self::assertSame($before, $this->active);
	}

	public function testASecondFileOfTheSameMemberIsLookedUpAsThatMemberFromTheFolderCache(): void {
		// Two rows, one reader. The folder is set up once and served from the
		// per claim cache for the second row, and the lookup of that second row
		// still runs with the member active.
		$second = new QueueFile();
		$second->setId(self::ROW_ID + 1);
		$second->setFileId(self::FILE_ID + 1);
		$second->setStorageId(3);
		$second->setRootId(5);
		$second->setSize(100);
		$second->setRetries(1);
		$second->setKind(QueueMapper::KIND_CONTENT);
		$first = new QueueFile();
		$first->setId(self::ROW_ID);
		$first->setFileId(self::FILE_ID);
		$first->setStorageId(3);
		$first->setRootId(5);
		$first->setSize(100);
		$first->setRetries(1);
		$first->setKind(QueueMapper::KIND_CONTENT);
		$this->queueMapper = $this->createMock(QueueMapper::class);
		$this->queueMapper->method('claimBatch')->willReturnCallback(
			static fn (int $limit, int $maxBytes, string $kind): array => $kind === QueueMapper::KIND_CONTENT ? [$first, $second] : [],
		);

		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn('anna');
		$mount = $this->createMock(ICachedMountFileInfo::class);
		$mount->method('getUser')->willReturn($user);
		$this->mountCache->method('getMountsForFileId')->willReturn([$mount]);

		$lookedUpAs = [];
		$file = $this->file(true);
		$folder = $this->createMock(Folder::class);
		$folder->method('getFirstNodeById')->willReturnCallback(function (int $fileId) use ($file, &$lookedUpAs): File {
			$lookedUpAs[] = [$fileId, $this->activeUid()];

			return $file;
		});
		$folder->method('getRelativePath')->willReturn('/admins-hh/Vertrag.pdf');
		$this->rootFolder->expects(self::once())->method('getUserFolder')->with('anna')->willReturn($folder);

		$sources = $this->service()->claim(32, 1_000_000);

		self::assertCount(2, $sources);
		self::assertSame([[self::FILE_ID, 'anna'], [self::FILE_ID + 1, 'anna']], $lookedUpAs);
		self::assertNull($this->active);
	}

	public function testAFolderSetupThatThrowsStillRestoresThePreviousUser(): void {
		$before = $this->createMock(IUser::class);
		$before->method('getUID')->willReturn('admin');
		$this->active = $before;
		$this->mountsFor(['anna']);
		$this->rootFolder->method('getUserFolder')->willThrowException(new \RuntimeException('no home'));

		self::assertSame([], $this->service()->claim(32, 1_000_000));
		self::assertSame($before, $this->active);
	}
}
