<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Db\QueueFile;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
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

	protected function setUp(): void {
		parent::setUp();

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
		);
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

	public function testAFileNobodyReachesAnyMoreStaysGone(): void {
		// The old meaning of gone, kept: every name was asked and none of them
		// resolved the id to a file.
		$this->mountsFor(['anna', 'bernd']);
		$this->foldersResolving(['anna' => null, 'bernd' => null]);
		$this->fileStateService->expects(self::once())
			->method('record')
			->with(self::FILE_ID, 'skipped', 'gone');

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
}
