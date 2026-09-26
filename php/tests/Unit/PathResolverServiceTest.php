<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\PathResolverService;
use OCP\DB\IResult;
use OCP\DB\QueryBuilder\ICompositeExpression;
use OCP\DB\QueryBuilder\IExpressionBuilder;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\ICachedMountFileInfo;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\Files\NotFoundException;
use OCP\IDBConnection;
use OCP\IUser;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The lookup field of the admin page, and the paths it takes (issue #14).
 *
 * The complaint behind the issue: the result card printed a Team Folder path
 * without its user, ``admins-hh/Vertrag.pdf``, an admin typed exactly that back
 * into the field, and the field answered "No file at this path". Two things
 * changed. The card prints ``uid/files/rest`` now, which admin.js does and no
 * PHP test can see. And a path without a user is resolved over the mounts that
 * carry it, which is what this file holds: the pure half, which rows carry a
 * path, and the whole way through resolveReference() with the query and the
 * folders doubled.
 *
 * What must not change is held here as well: a home path without a user, a
 * path under two different roots and plain garbage are refused, and the
 * refusal is the same null in every case.
 */
#[CoversClass(PathResolverService::class)]
final class PathResolverServiceTest extends TestCase {
	private const FILE_ID = 4242;

	private IRootFolder&MockObject $rootFolder;
	private IDBConnection&MockObject $db;
	private IUserMountCache&MockObject $mountCache;

	/**
	 * What the queries of one lookup answer, in the order they are asked.
	 * The first is the DISTINCT root query, the second the member rows of the
	 * one root that survived it. A query nobody staged answers nothing.
	 *
	 * @var list<list<array<string, mixed>>>
	 */
	private array $answers = [];

	/** How many queries were executed. */
	private int $queries = 0;

	/** The limits the queries were given, in order. @var list<?int> */
	private array $limits = [];

	protected function setUp(): void {
		parent::setUp();

		$this->rootFolder = $this->createMock(IRootFolder::class);
		$this->db = $this->createMock(IDBConnection::class);
		$this->mountCache = $this->createMock(IUserMountCache::class);
		$this->db->method('escapeLikeParameter')->willReturnCallback(
			static fn (string $value): string => addcslashes($value, '\_%'),
		);

		$this->db->method('getQueryBuilder')->willReturnCallback(function (): IQueryBuilder {
			$expr = $this->createMock(IExpressionBuilder::class);
			$expr->method('like')->willReturn('mount_point LIKE :p');
			$expr->method('eq')->willReturn('root_id = :r');
			$expr->method('orX')->willReturn($this->createMock(ICompositeExpression::class));
			$qb = $this->createMock(IQueryBuilder::class);
			$limit = null;
			$qb->method('select')->willReturnSelf();
			$qb->method('selectDistinct')->willReturnSelf();
			$qb->method('from')->willReturnSelf();
			$qb->method('where')->willReturnSelf();
			$qb->method('andWhere')->willReturnSelf();
			$qb->method('orderBy')->willReturnSelf();
			$qb->method('setMaxResults')->willReturnCallback(function (?int $max) use ($qb, &$limit): IQueryBuilder {
				$limit = $max;

				return $qb;
			});
			$qb->method('expr')->willReturn($expr);
			$qb->method('createNamedParameter')->willReturn(':p');
			$qb->method('executeQuery')->willReturnCallback(function () use (&$limit): IResult {
				$this->queries++;
				$this->limits[] = $limit;
				$result = $this->createMock(IResult::class);
				$result->method('fetchAll')->willReturn(array_shift($this->answers) ?? []);

				return $result;
			});

			return $qb;
		});
	}

	/**
	 * The two answers of an owner-less lookup: the distinct roots of the
	 * member rows, then the member rows themselves.
	 *
	 * @param list<array<string, mixed>> $rows
	 */
	private function mounts(array $rows): void {
		$roots = array_values(array_unique(array_map(static fn (array $row): int => (int)$row['root_id'], $rows)));
		$this->answers = [
			array_map(static fn (int $root): array => ['root_id' => $root], $roots),
			$rows,
		];
	}

	private function resolver(): PathResolverService {
		return new PathResolverService(
			$this->mountCache,
			$this->createMock(IFileAccess::class),
			$this->rootFolder,
			$this->db,
			$this->createMock(LoggerInterface::class),
		);
	}

	/** @return array<string, mixed> */
	private static function row(string $uid, string $mountPoint, int $root): array {
		return ['user_id' => $uid, 'mount_point' => $mountPoint, 'root_id' => $root];
	}

	private function file(bool $readable): File&MockObject {
		$file = $this->createMock(File::class);
		$file->method('getId')->willReturn(self::FILE_ID);
		$file->method('isReadable')->willReturn($readable);

		return $file;
	}

	/**
	 * One home folder per user. A File is what get() and the id lookup hand
	 * out, null makes get() throw the way the ACL wrapper hides a node.
	 *
	 * @param array<string, ?File> $nodes
	 */
	private function folders(array $nodes): void {
		$folders = [];
		foreach ($nodes as $uid => $node) {
			$folder = $this->createMock(Folder::class);
			if ($node === null) {
				$folder->method('get')->willThrowException(new NotFoundException());
			} else {
				$folder->method('get')->willReturn($node);
			}
			$folder->method('getFirstNodeById')->willReturn($node);
			$folders[$uid] = $folder;
		}

		$this->rootFolder->method('getUserFolder')->willReturnCallback(
			static function (string $uid) use ($folders): Folder {
				if (!isset($folders[$uid])) {
					throw new NotFoundException();
				}

				return $folders[$uid];
			},
		);
	}

	// -- the reference the card prints (review finding) ----------------------

	/**
	 * The mount the owner of FILE_ID is found through, a home mount.
	 */
	private function ownerMount(string $uid, string $absolute): void {
		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn($uid);
		$mount = $this->createMock(ICachedMountFileInfo::class);
		$mount->method('getUser')->willReturn($user);
		$mount->method('getPath')->willReturn($absolute);
		$mount->method('getRootInternalPath')->willReturn('');
		$this->mountCache->method('getMountsForFileId')->with(self::FILE_ID)->willReturn([$mount]);
	}

	public function testAFileInTheFilesFolderIsReferencedWithUserAndFiles(): void {
		$this->ownerMount('anna', '/anna/files/admins-hh/Vertrag.pdf');

		$described = $this->resolver()->describe(self::FILE_ID);

		self::assertSame('admins-hh/Vertrag.pdf', $described['path'] ?? null);
		self::assertSame('anna/files/admins-hh/Vertrag.pdf', $described['reference'] ?? null);
	}

	public function testAFileOutsideTheFilesFolderIsReferencedByItsOwnPathAndNotDoubled(): void {
		// The finding: the card put anna/files/ in front of a path that
		// already starts with anna, and printed anna/files/anna/files_versions/...
		// The reference is the absolute path without its slash, once.
		$this->ownerMount('anna', '/anna/files_versions/admins-hh/Vertrag.pdf.v1727350000');

		$described = $this->resolver()->describe(self::FILE_ID);

		self::assertSame('anna/files_versions/admins-hh/Vertrag.pdf.v1727350000', $described['path'] ?? null);
		self::assertSame('anna/files_versions/admins-hh/Vertrag.pdf.v1727350000', $described['reference'] ?? null);
		self::assertStringNotContainsString('anna/files/anna', $described['reference'] ?? '');
	}

	public function testATrashedFileIsReferencedByItsTrashPath(): void {
		$this->ownerMount('anna', '/anna/files_trashbin/files/Vertrag.pdf.d1727350000');

		$described = $this->resolver()->describe(self::FILE_ID);

		self::assertTrue($described['trashed'] ?? false);
		self::assertSame('anna/files_trashbin/files/Vertrag.pdf.d1727350000', $described['reference'] ?? null);
	}

	public function testTheReferenceOfTheCardResolvesBackToTheSameFile(): void {
		// The round trip the card exists for: what describe() prints, the
		// lookup takes back.
		$this->ownerMount('anna', '/anna/files/Vertraege/Miete.pdf');
		$this->folders(['anna' => $this->file(true)]);
		$resolver = $this->resolver();

		$reference = $resolver->describe(self::FILE_ID)['reference'] ?? '';

		self::assertSame(self::FILE_ID, $resolver->resolveReference($reference));
	}

	// -- the pure half: which rows carry a path -------------------------------

	public function testTheMembersOfOneTeamFolderCarryAPathInsideIt(): void {
		$readers = PathResolverService::readersOfMountedPath([
			self::row('anna', '/anna/files/admins-hh/', 9),
			self::row('bernd', '/bernd/files/admins-hh/', 9),
		], 'admins-hh/Vertrag.pdf');

		self::assertSame(['anna', 'bernd'], $readers);
	}

	public function testAMountPointThatIsOnlyAPrefixOfASegmentCarriesNothing(): void {
		// admins is not admins-hh, and a comparison without the trailing slash
		// would say it is.
		$readers = PathResolverService::readersOfMountedPath([
			self::row('anna', '/anna/files/admins/', 9),
		], 'admins-hh/Vertrag.pdf');

		self::assertSame([], $readers);
	}

	public function testTwoRootsUnderOneNameAreAmbiguousAndCarryNothing(): void {
		// Two shares that happen to be mounted as "Shared" for two users are
		// two different files, and picking one of them would be a guess.
		$readers = PathResolverService::readersOfMountedPath([
			self::row('anna', '/anna/files/Shared/', 3),
			self::row('bernd', '/bernd/files/Shared/', 4),
		], 'Shared/Bericht.pdf');

		self::assertSame([], $readers);
	}

	public function testTheDeepestMountOfOneUserIsTheOneThatCounts(): void {
		$readers = PathResolverService::readersOfMountedPath([
			self::row('anna', '/anna/files/Projekte/', 3),
			self::row('anna', '/anna/files/Projekte/Bau/', 7),
		], 'Projekte/Bau/Plan.pdf');

		self::assertSame(['anna'], $readers);
	}

	public function testARowOfAnotherUserPathSpaceCarriesNothing(): void {
		// The LIKE of the query lets /x/files/y/files/admins-hh/ through; the
		// user id of the row has to be the user of its mount point.
		$readers = PathResolverService::readersOfMountedPath([
			self::row('anna', '/bernd/files/admins-hh/', 9),
		], 'admins-hh/Vertrag.pdf');

		self::assertSame([], $readers);
	}

	// -- the whole way through resolveReference() -----------------------------

	public function testATeamFolderPathWithoutUserResolvesThroughAMemberWhoMayRead(): void {
		// anna sorts first and the folder rules hide the file from her; bernd
		// may read it, so the path names a file after all.
		$this->mounts([
			self::row('anna', '/anna/files/admins-hh/', 9),
			self::row('bernd', '/bernd/files/admins-hh/', 9),
		]);
		$this->folders(['anna' => null, 'bernd' => $this->file(true)]);

		self::assertSame(self::FILE_ID, $this->resolver()->resolveReference('admins-hh/Vertrag.pdf'));
	}

	public function testANamedUserWhoDoesNotReachTheFileFallsBackToTheMounts(): void {
		// The reference the card prints for a Team Folder names one member, and
		// that member can be the one the rules hide the file from.
		// The third query asks anna's own mounts at the path, and she has the
		// same mount as bernd, so the file bernd reads is the file she named.
		$this->mounts([
			self::row('anna', '/anna/files/admins-hh/', 9),
			self::row('bernd', '/bernd/files/admins-hh/', 9),
		]);
		$this->answers[] = [self::row('anna', '/anna/files/admins-hh/', 9)];
		$this->folders(['anna' => null, 'bernd' => $this->file(true)]);

		self::assertSame(
			['fileId' => self::FILE_ID, 'namedUserMayNotRead' => true],
			$this->resolver()->resolve('anna/files/admins-hh/Vertrag.pdf'),
		);
		self::assertSame(3, $this->queries);
	}

	// -- the fallback of a named reference, restricted (review finding) -------

	public function testTheReportedTeamFolderWithTheFirstTwoOfFourMembersClosedResolves(): void {
		// The instance of the reporter of #14: four members of admins-hh, and
		// the ACL closes the file to the first two in alphabetical order. The
		// one is hidden from it, the other reaches it without the read bit;
		// carla may read it and is the one it is resolved through, dora is
		// never asked.
		$this->mounts([
			self::row('anna', '/anna/files/admins-hh/', 9),
			self::row('bernd', '/bernd/files/admins-hh/', 9),
			self::row('carla', '/carla/files/admins-hh/', 9),
			self::row('dora', '/dora/files/admins-hh/', 9),
		]);
		$this->folders([
			'anna' => null,
			'bernd' => $this->file(false),
			'carla' => $this->file(true),
		]);

		self::assertSame(
			['fileId' => self::FILE_ID, 'namedUserMayNotRead' => false],
			$this->resolver()->resolve('admins-hh/Vertrag.pdf'),
		);
	}

	public function testTheReporterNamingHimselfInFrontOfAFileHeMayNotReadGetsTheFileWithTheHint(): void {
		// The second half of the report: the path with the reporter's own uid in
		// front, anna/files/admins-hh/..., answered "no file" because the folder
		// rules hide the file from anna. Her own mount is the Team Folder, so
		// the fallback is the same file, carla may read it, and the card says
		// that the named user may not open it.
		$this->mounts([
			self::row('anna', '/anna/files/admins-hh/', 9),
			self::row('bernd', '/bernd/files/admins-hh/', 9),
			self::row('carla', '/carla/files/admins-hh/', 9),
			self::row('dora', '/dora/files/admins-hh/', 9),
		]);
		$this->answers[] = [self::row('anna', '/anna/files/admins-hh/', 9)];
		$this->folders([
			'anna' => null,
			'bernd' => $this->file(false),
			'carla' => $this->file(true),
		]);

		self::assertSame(
			['fileId' => self::FILE_ID, 'namedUserMayNotRead' => true],
			$this->resolver()->resolve('anna/files/admins-hh/Vertrag.pdf'),
		);
	}

	public function testANamedUserWhoReachesTheFileWithoutTheReadBitGetsTheFileWithTheHint(): void {
		// The other shape of the same ACL: the node is there for anna and the
		// read bit is not. It is the file she named, no mount is asked, and the
		// card still says she may not open it.
		$this->folders(['anna' => $this->file(false)]);
		$this->db->expects(self::never())->method('getQueryBuilder');

		self::assertSame(
			['fileId' => self::FILE_ID, 'namedUserMayNotRead' => true],
			$this->resolver()->resolve('anna/files/admins-hh/Vertrag.pdf'),
		);
	}

	public function testANamedUserWithoutTheMountDoesNotFallBackToSomebodyElsesFile(): void {
		// The review finding. anna has no admins-hh mount; whatever her home
		// holds or misses under that name, bernd's Team Folder file of the same
		// name is a different file, and the answer is the null of every other
		// refusal. bernd is never asked.
		$this->mounts([self::row('bernd', '/bernd/files/admins-hh/', 9)]);
		$this->answers[] = [];
		$this->folders(['anna' => null]);

		self::assertNull($this->resolver()->resolve('anna/files/admins-hh/Vertrag.pdf'));
		self::assertSame(3, $this->queries);
	}

	public function testANamedUserWhoDoesNotExistGetsTheSameNullAsANonMember(): void {
		// T-04-38: no answer here may tell a missing user from an existing one.
		$this->mounts([self::row('bernd', '/bernd/files/admins-hh/', 9)]);
		$this->answers[] = [];
		$this->folders([]);

		self::assertNull($this->resolver()->resolve('nobody/files/admins-hh/Vertrag.pdf'));
	}

	public function testANamedUserWhoseMountAtThePathIsDeeperDoesNotFallBack(): void {
		// anna sees another mount below admins-hh at that path, so her
		// admins-hh/Unter/Vertrag.pdf is not the file of the Team Folder.
		$this->mounts([self::row('bernd', '/bernd/files/admins-hh/', 9)]);
		$this->answers[] = [
			self::row('anna', '/anna/files/admins-hh/', 9),
			self::row('anna', '/anna/files/admins-hh/Unter/', 12),
		];
		$this->folders(['anna' => null, 'bernd' => $this->file(true)]);

		self::assertNull($this->resolver()->resolve('anna/files/admins-hh/Unter/Vertrag.pdf'));
	}

	public function testAMemberIsAskedAboutTheNodeInHandAndNotResolvedTwice(): void {
		// The efficiency finding: the node comes out of get() by path, and the
		// readability question is asked of that node. A second resolution by
		// id per member tried was a second lookup for the node already there.
		$this->mounts([self::row('anna', '/anna/files/admins-hh/', 9)]);
		$folder = $this->createMock(Folder::class);
		$folder->method('get')->willReturn($this->file(true));
		$folder->expects(self::never())->method('getFirstNodeById');
		$this->rootFolder->method('getUserFolder')->willReturn($folder);

		self::assertSame(self::FILE_ID, $this->resolver()->resolveReference('admins-hh/Vertrag.pdf'));
	}

	public function testAFileNoMemberMayReadIsRefused(): void {
		$this->mounts([self::row('anna', '/anna/files/admins-hh/', 9)]);
		$this->folders(['anna' => $this->file(false)]);

		self::assertNull($this->resolver()->resolveReference('admins-hh/Vertrag.pdf'));
	}

	public function testAHomePathWithoutUserIsStillRefused(): void {
		// Every user has a Documents folder, no mount row carries it, and the
		// folders are never asked.
		$this->answers = [[]];
		$this->rootFolder->expects(self::never())->method('getUserFolder');

		self::assertNull($this->resolver()->resolveReference('Documents/Bericht.pdf'));
		self::assertSame(1, $this->queries, 'no root, so no member rows are fetched');
	}

	// -- the roots are asked apart from the members (review finding) ----------

	public function testASecondRootIsSeenWhateverTheMembersOfTheFirstOne(): void {
		// The case of the finding. Two hundred members of root 9 used to fill
		// the row cap in user order, and the one member of root 4 behind them
		// never reached the refusal. The DISTINCT query sees both roots, the
		// path is refused, and neither the member rows nor a folder is asked.
		$this->answers = [[['root_id' => 9], ['root_id' => 4]]];
		$this->rootFolder->expects(self::never())->method('getUserFolder');

		self::assertNull($this->resolver()->resolveReference('Shared/Bericht.pdf'));
		self::assertSame(1, $this->queries);
	}

	public function testTheRootQueryStopsAtTwoAndOnlyTheMembersAreCapped(): void {
		$this->mounts([self::row('bernd', '/bernd/files/admins-hh/', 9)]);
		$this->folders(['bernd' => $this->file(true)]);

		self::assertSame(self::FILE_ID, $this->resolver()->resolveReference('admins-hh/Vertrag.pdf'));
		self::assertSame([2, 200], $this->limits);
	}

	public function testOneRootAtTwoDepthsIsAmbiguousAndCarriesNothing(): void {
		// The same root at a/ for anna and at a/b/ for bernd puts two
		// different files at a/b/c.pdf, root/b/c.pdf and root/c.pdf.
		$carriers = PathResolverService::carriersOfMountedPath([
			self::row('anna', '/anna/files/a/', 9),
			self::row('bernd', '/bernd/files/a/b/', 9),
		], 'a/b/c.pdf');

		self::assertNull($carriers);
	}

	public function testTheCarriersNameTheirRootAndTheirMountPoint(): void {
		$carriers = PathResolverService::carriersOfMountedPath([
			self::row('anna', '/anna/files/admins-hh/', 9),
			self::row('bernd', '/bernd/files/admins-hh/', 9),
		], 'admins-hh/Unterordner/Vertrag.pdf');

		self::assertSame(['root' => 9, 'inside' => 'admins-hh/', 'users' => ['anna', 'bernd']], $carriers);
	}

	public function testTheLeadingFoldersOfAPathAreItsPossibleMountPoints(): void {
		self::assertSame(['a/', 'a/b/'], PathResolverService::leadingFoldersOf('a/b/c.pdf'));
		self::assertSame([], PathResolverService::leadingFoldersOf('c.pdf'));
	}

	public function testGarbageIsRefused(): void {
		$this->rootFolder->expects(self::never())->method('getUserFolder');
		$resolver = $this->resolver();

		self::assertNull($resolver->resolveReference(''));
		self::assertNull($resolver->resolveReference('   '));
		self::assertNull($resolver->resolveReference('admins-hh/../etc/passwd'));
		self::assertNull($resolver->resolveReference('///'));
		self::assertNull($resolver->resolveReference(str_repeat('9', 20)));
	}

	public function testANumberIsStillAFileIdAndAsksNothing(): void {
		$this->rootFolder->expects(self::never())->method('getUserFolder');

		self::assertSame(self::FILE_ID, $this->resolver()->resolveReference((string)self::FILE_ID));
	}

	public function testANamedReferenceTheUserReachesResolvesAsBefore(): void {
		// The spelling of the error list, unchanged: the named user's folder
		// answers, and the mounts are not asked.
		$this->folders(['anna' => $this->file(true)]);
		$this->db->expects(self::never())->method('getQueryBuilder');

		self::assertSame(self::FILE_ID, $this->resolver()->resolveReference('anna/files/Vertraege/Miete.pdf'));
		self::assertSame(self::FILE_ID, $this->resolver()->resolveReference('anna:Vertraege/Miete.pdf'));
	}
}
