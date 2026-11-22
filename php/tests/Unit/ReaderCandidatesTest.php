<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\ReaderCandidates;
use OCP\Files\Config\ICachedMountFileInfo;
use OCP\Files\Config\IUserMountCache;
use OCP\IUser;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * Who sees a file, who owns it, and the order they are asked in (issue #59).
 *
 * The reporter of #59 had a file shared without download under the watermark
 * of Nextcloud Office. Findling read it as the alphabetically first user who
 * sees it, the recipient, whose fetch the secure view refused; the owner, who
 * reads it through the home mount without a share, was never asked. The owner
 * is recognised by exactly one shape of mount, measured on the reproduction of
 * 45-17 (45-AUDIT.md, "Mount-Cache-Probe"): the mount point '/<uid>/' of a home
 * mount provider of the server.
 */
#[CoversClass(ReaderCandidates::class)]
final class ReaderCandidatesTest extends TestCase {
	private const FILE_ID = 4242;
	private const LOCAL_HOME = 'OC\\Files\\Mount\\LocalHomeMountProvider';
	private const OBJECT_HOME = 'OC\\Files\\Mount\\ObjectHomeMountProvider';
	private const SHARING = 'OCA\\Files_Sharing\\MountProvider';
	private const GROUPFOLDERS = 'OCA\\GroupFolders\\Mount\\MountProvider';
	private const EXTERNAL = 'OCA\\Files_External\\Config\\ConfigAdapter';

	private IUserMountCache&MockObject $mountCache;
	private LoggerInterface&MockObject $logger;

	protected function setUp(): void {
		parent::setUp();
		$this->mountCache = $this->createMock(IUserMountCache::class);
		$this->logger = $this->createMock(LoggerInterface::class);
	}

	private function candidates(): ReaderCandidates {
		return new ReaderCandidates($this->mountCache, $this->logger);
	}

	/**
	 * One mount of the file: the user, the mount point, the provider class.
	 */
	private function mount(string $uid, string $mountPoint, string $provider): ICachedMountFileInfo&MockObject {
		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn($uid);
		$mount = $this->createMock(ICachedMountFileInfo::class);
		$mount->method('getUser')->willReturn($user);
		$mount->method('getMountPoint')->willReturn($mountPoint);
		$mount->method('getMountProvider')->willReturn($provider);

		return $mount;
	}

	/**
	 * @param list<ICachedMountFileInfo> $mounts
	 */
	private function mounts(array $mounts): void {
		$this->mountCache->method('getMountsForFileId')->with(self::FILE_ID)->willReturn($mounts);
	}

	public function testTheListIsSortedAndDeduplicatedAsBefore(): void {
		$this->mounts([
			$this->mount('carol', '/carol/files/TF/', self::GROUPFOLDERS),
			$this->mount('alice', '/alice/files/TF/', self::GROUPFOLDERS),
			$this->mount('alice', '/alice/files/again/', self::SHARING),
		]);

		self::assertSame(
			['users' => ['alice', 'carol'], 'truncated' => false, 'owner' => null],
			$this->candidates()->forFile(self::FILE_ID),
		);
	}

	public function testWithoutAnOwnerTheOrderIsTheFirstTwentyOfTheList(): void {
		$users = [];
		for ($i = 1; $i <= 30; $i++) {
			$users[] = sprintf('member%02d', $i);
		}

		self::assertSame(array_slice($users, 0, 20), ReaderCandidates::readingOrder($users, null));
		self::assertSame(20, ReaderCandidates::MAX_READER_TRIES);
	}

	public function testTheOwnerIsAskedFirstAndTheOthersKeepTheirOrder(): void {
		self::assertSame(['bob', 'alice', 'carol'], ReaderCandidates::readingOrder(['alice', 'bob', 'carol'], 'bob'));
	}

	public function testAnOwnerWhoIsNotInTheListChangesNothing(): void {
		self::assertSame(['alice', 'carol'], ReaderCandidates::readingOrder(['alice', 'carol'], 'bob'));
	}

	public function testAnOwnerBehindTheCapIsFirstAndTheOwnerCounts(): void {
		$users = [];
		for ($i = 1; $i <= 30; $i++) {
			$users[] = sprintf('member%02d', $i);
		}

		$order = ReaderCandidates::readingOrder($users, 'member25');

		self::assertCount(20, $order);
		self::assertSame(['member25', ...array_slice($users, 0, 19)], $order);
	}

	public function testTheHomeMountOfTheLocalProviderNamesTheOwner(): void {
		$this->mounts([
			$this->mount('bob', '/bob/', self::LOCAL_HOME),
			$this->mount('alice', '/alice/files/wz59-b1.odt/', self::SHARING),
		]);

		self::assertSame(
			['users' => ['alice', 'bob'], 'truncated' => false, 'owner' => 'bob'],
			$this->candidates()->forFile(self::FILE_ID),
		);
	}

	public function testTheHomeMountOfTheObjectStoreProviderNamesTheOwner(): void {
		$this->mounts([$this->mount('dave', '/dave/', self::OBJECT_HOME)]);

		self::assertSame('dave', $this->candidates()->forFile(self::FILE_ID)['owner']);
	}

	public function testAShareMountNamesNoOwner(): void {
		$this->mounts([$this->mount('alice', '/alice/files/x/', self::SHARING)]);

		self::assertNull($this->candidates()->forFile(self::FILE_ID)['owner']);
	}

	public function testTeamFolderAndExternalMountsNameNoOwner(): void {
		$this->mounts([
			$this->mount('alice', '/alice/files/TF-lesen/', self::GROUPFOLDERS),
			$this->mount('bob', '/bob/files/Extern/', self::EXTERNAL),
			// The mount point alone is not enough: a provider other than the
			// two home providers is no owner, whatever its mount point says.
			$this->mount('carol', '/carol/', self::GROUPFOLDERS),
		]);

		self::assertNull($this->candidates()->forFile(self::FILE_ID)['owner']);
	}

	public function testAHomeMountWithoutAProviderNamesNoOwner(): void {
		$this->mounts([$this->mount('bob', '/bob/', '')]);

		self::assertNull($this->candidates()->forFile(self::FILE_ID)['owner']);
	}

	public function testAHomeMountOfAnotherUserNamesNoOwner(): void {
		// The mount point must be exactly the one of its own user.
		$this->mounts([
			$this->mount('alice', '/bob/', self::LOCAL_HOME),
			$this->mount('bob', '/bob/files/', self::LOCAL_HOME),
		]);

		self::assertNull($this->candidates()->forFile(self::FILE_ID)['owner']);
	}

	public function testAHomeMountBehindTheCeilingIsNotSeenAndTheOrderStaysAlphabetical(): void {
		// The ceiling ends the loop (perf audit M5), so a home mount listed
		// after five hundred other mounts is never looked at. Decided and
		// written down in the docblock of forFile().
		$mounts = [];
		for ($i = 1; $i <= 500; $i++) {
			$uid = sprintf('member%03d', $i);
			$mounts[] = $this->mount($uid, '/' . $uid . '/files/TF/', self::GROUPFOLDERS);
		}
		$mounts[] = $this->mount('aaron', '/aaron/', self::LOCAL_HOME);
		$this->mounts($mounts);

		$access = $this->candidates()->forFile(self::FILE_ID);

		self::assertTrue($access['truncated']);
		self::assertNull($access['owner']);
		self::assertCount(500, $access['users']);
		self::assertNotContains('aaron', $access['users']);
		self::assertSame(array_slice($access['users'], 0, 20), ReaderCandidates::readingOrder($access['users'], $access['owner']));
	}

	public function testAMountCacheThatThrowsGivesTheEmptyListAsBefore(): void {
		$this->mountCache->method('getMountsForFileId')->willThrowException(new \RuntimeException('/secret/path'));
		$this->logger->expects(self::once())->method('warning')->with(
			'Findling: could not resolve who sees a queued file',
			self::callback(static fn (array $context): bool => array_keys($context) === ['exception']),
		);

		self::assertSame(
			['users' => [], 'truncated' => false, 'owner' => null],
			$this->candidates()->forFile(self::FILE_ID),
		);
	}
}
