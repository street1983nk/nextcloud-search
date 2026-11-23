<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\GatewayReader;
use OCA\Findling\Service\ReaderCandidates;
use OCA\Findling\Service\ReaderContext;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventDispatcher;
use OCP\Files\Config\ICachedMountFileInfo;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\ForbiddenException;
use OCP\Files\IRootFolder;
use OCP\Files\Storage\IStorage;
use OCP\Files\StorageNotAvailableException;
use OCP\IUser;
use OCP\IUserManager;
use OCP\IUserSession;
use OCP\Log\Audit\CriticalActionPerformedEvent;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * Opening a file for the container, and opening it again when the secure view
 * of Nextcloud Office refused the first open (issue #59, decisions E1 and E2).
 *
 * E1: the first open runs without an active user, as before; only a refusal
 * that provably comes from the secure view (exact message AND first frame of
 * the trace SecureViewWrapper::checkFileAccess) opens the file again, inside
 * actAs: the owner alone when there is one, otherwise the users of the file in
 * reading order, twenty at most. E2: a refusal of the owner ends at once with
 * policy; Findling does not work round a watermark that applies to the owner.
 * Any other ForbiddenException ends with policy without a further try.
 *
 * Everything is a double. The steps record who was active at each folder
 * setup, lookup and open.
 */
#[CoversClass(GatewayReader::class)]
final class GatewayReaderTest extends TestCase {
	private const FILE_ID = 11;
	private const LOCAL_HOME = 'OC\\Files\\Mount\\LocalHomeMountProvider';
	private const SHARING = 'OCA\\Files_Sharing\\MountProvider';
	private const GROUPFOLDERS = 'OCA\\GroupFolders\\Mount\\MountProvider';

	private IRootFolder&MockObject $rootFolder;
	private IUserMountCache&MockObject $mountCache;
	private LoggerInterface&MockObject $logger;
	private IUserSession&MockObject $session;
	private ?IUser $active = null;

	/** @var list<array{Event, ?string}> event, active user at the dispatch */
	private array $events = [];

	/** @var list<array{string, string, ?string}> step, user, active user */
	private array $steps = [];

	/** @var array<string, \Closure(): (Folder)> */
	private array $folders = [];

	protected function setUp(): void {
		parent::setUp();
		$this->steps = [];
		$this->folders = [];
		$this->active = null;

		$this->session = $this->createMock(IUserSession::class);
		$this->session->method('getUser')->willReturnCallback(fn (): ?IUser => $this->active);
		$this->session->method('setVolatileActiveUser')->willReturnCallback(function (?IUser $user): void {
			$this->active = $user;
		});

		$this->rootFolder = $this->createMock(IRootFolder::class);
		$this->rootFolder->method('getUserFolder')->willReturnCallback(function (string $uid): Folder {
			$this->steps[] = ['folder', $uid, $this->active?->getUID()];
			if (!isset($this->folders[$uid])) {
				throw new \OC\User\NoUserException('/secret/' . $uid);
			}

			return ($this->folders[$uid])();
		});
		$this->mountCache = $this->createMock(IUserMountCache::class);
		$this->logger = $this->createMock(LoggerInterface::class);
		$this->events = [];
	}

	private function reader(): GatewayReader {
		$userManager = $this->createMock(IUserManager::class);
		$userManager->method('get')->willReturnCallback(function (string $uid): IUser {
			$user = $this->createMock(IUser::class);
			$user->method('getUID')->willReturn($uid);

			return $user;
		});

		return new GatewayReader(
			$this->rootFolder,
			new ReaderContext($this->session, $userManager),
			new ReaderCandidates($this->mountCache, $this->logger),
			$this->logger,
			$this->dispatcher(),
		);
	}

	private function dispatcher(): IEventDispatcher {
		$dispatcher = $this->createMock(IEventDispatcher::class);
		$dispatcher->method('dispatchTyped')->willReturnCallback(function (Event $event): void {
			$this->events[] = [$event, $this->active?->getUID()];
		});

		return $dispatcher;
	}

	/**
	 * The audit events, as message, parameters and obfuscation.
	 *
	 * @return list<array{string, array<array-key, mixed>, bool}>
	 */
	private function auditEvents(): array {
		$events = [];
		foreach ($this->events as [$event]) {
			self::assertInstanceOf(CriticalActionPerformedEvent::class, $event);
			$events[] = [$event->getLogMessage(), $event->getParameters(), $event->getObfuscateParameters()];
		}

		return $events;
	}

	/**
	 * The mounts of the file: name, mount point, provider.
	 *
	 * @param list<array{string, string, string}> $mounts
	 */
	private function mounts(array $mounts): void {
		$list = [];
		foreach ($mounts as [$uid, $mountPoint, $provider]) {
			$user = $this->createMock(IUser::class);
			$user->method('getUID')->willReturn($uid);
			$mount = $this->createMock(ICachedMountFileInfo::class);
			$mount->method('getUser')->willReturn($user);
			$mount->method('getMountPoint')->willReturn($mountPoint);
			$mount->method('getMountProvider')->willReturn($provider);
			$list[] = $mount;
		}
		$this->mountCache->method('getMountsForFileId')->with(self::FILE_ID)->willReturn($list);
	}

	/**
	 * The file as $uid sees it: its open returns a stream or throws.
	 *
	 * @param resource|\Throwable $opens
	 */
	private function sees(string $uid, mixed $opens): void {
		$file = $this->createMock(File::class);
		$file->method('isReadable')->willReturn(true);
		$file->method('getSize')->willReturn(5);
		$file->method('getPath')->willReturn('/' . $uid . '/files/a.odt');
		$file->method('getStorage')->willReturn($this->createMock(IStorage::class));
		$file->method('fopen')->with('r')->willReturnCallback(function () use ($uid, $opens) {
			$this->steps[] = ['fopen', $uid, $this->active?->getUID()];
			if ($opens instanceof \Throwable) {
				throw $opens;
			}

			return $opens;
		});
		$this->folderOf($uid, $file);
	}

	/**
	 * A folder of $uid whose lookup answers $node.
	 */
	private function folderOf(string $uid, ?File $node): void {
		$this->folders[$uid] = function () use ($uid, $node): Folder {
			$folder = $this->createMock(Folder::class);
			$folder->method('getFirstNodeById')->willReturnCallback(function () use ($uid, $node): ?File {
				$this->steps[] = ['lookup', $uid, $this->active?->getUID()];

				return $node;
			});

			return $folder;
		};
	}

	/**
	 * A folder of $uid that cannot be built.
	 */
	private function brokenFolderOf(string $uid, \Throwable $error): void {
		$this->folders[$uid] = static function () use ($error): never {
			throw $error;
		};
	}

	/**
	 * @return resource
	 */
	private static function stream(string $bytes) {
		$stream = fopen('php://memory', 'rb+');
		self::assertIsResource($stream);
		fwrite($stream, $bytes);
		rewind($stream);

		return $stream;
	}

	/**
	 * Who was asked to open the file, in order.
	 *
	 * @return list<array{string, ?string}>
	 */
	private function opens(): array {
		$opens = [];
		foreach ($this->steps as [$step, $uid, $active]) {
			if ($step === 'fopen') {
				$opens[] = [$uid, $active];
			}
		}

		return $opens;
	}

	public function testAReadInActAsTellsTheAuditLogWhoRead(): void {
		// a4 (plan 45-20, owner decision): the identity admin_audit takes for a
		// read is the session user, which actAs does not set. The gateway names
		// the reading user itself, through the public audit event: file id,
		// path and uid, never a byte of the content.
		$this->mounts([['alice', '/alice/files/a.odt/', self::SHARING], ['bob', '/bob/', self::LOCAL_HOME]]);
		$this->sees('alice', SecureViewRefusal::real());
		$this->sees('bob', self::stream('bobs bytes'));

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(GatewayReader::OUTCOME_OK, $opened['outcome']);
		self::assertSame([[
			GatewayReader::AUDIT_MESSAGE,
			['id' => self::FILE_ID, 'path' => '/bob/files/a.odt', 'reader' => 'bob'],
			false,
		]], $this->auditEvents());
		self::assertStringContainsString('"%s"', GatewayReader::AUDIT_MESSAGE);
		self::assertSame(3, substr_count(GatewayReader::AUDIT_MESSAGE, '%s'));
	}

	public function testAReadOfAnotherReaderWithoutAnOwnerNamesThatReader(): void {
		$this->mounts([
			['member01', '/member01/files/TF/', self::GROUPFOLDERS],
			['member02', '/member02/files/TF/', self::GROUPFOLDERS],
		]);
		$this->sees('member01', SecureViewRefusal::real());
		$this->sees('member02', self::stream('member02'));

		$opened = $this->reader()->open(self::FILE_ID, 'member01');

		self::assertSame('member02', $opened['reader']);
		self::assertSame([[
			GatewayReader::AUDIT_MESSAGE,
			['id' => self::FILE_ID, 'path' => '/member02/files/a.odt', 'reader' => 'member02'],
			false,
		]], $this->auditEvents());
	}

	public function testAnOpenOutsideActAsTellsTheAuditLogNothingOfItsOwn(): void {
		// A plain read stays as in 1.6.5: admin_audit writes its own line.
		$this->mounts([['alice', '/alice/files/a.odt/', self::SHARING], ['bob', '/bob/', self::LOCAL_HOME]]);
		$this->sees('alice', self::stream('alice'));

		$this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame([], $this->events);
	}

	public function testARefusalInActAsTellsTheAuditLogNothing(): void {
		// Nothing was read, so nothing is named as read.
		$this->mounts([['alice', '/alice/files/a.odt/', self::SHARING], ['bob', '/bob/', self::LOCAL_HOME]]);
		$this->sees('alice', SecureViewRefusal::real());
		$this->sees('bob', SecureViewRefusal::real());

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(GatewayReader::OUTCOME_POLICY, $opened['outcome']);
		self::assertSame([], $this->events);
	}

	public function testAnotherForbiddenExceptionCarriesOnlyTheOriginOfItsFirstFrame(): void {
		$this->mounts([['alice', '/alice/files/a.odt/', self::SHARING], ['bob', '/bob/', self::LOCAL_HOME]]);
		$this->sees('alice', SecureViewRefusal::withAPathInMessageAndArguments('/alice/files/Geheim.odt'));

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(['outcome' => GatewayReader::OUTCOME_POLICY, 'asked' => 0, 'origin' => 'OCA\\FilesAccessControl\\Operation::checkFileAccess'], $opened);
	}

	public function testAnOpenThatSucceedsOutsideActAsIsNotRepeated(): void {
		$this->mounts([['alice', '/alice/files/a.odt/', self::SHARING], ['bob', '/bob/', self::LOCAL_HOME]]);
		$this->sees('alice', self::stream('alice'));
		$this->sees('bob', self::stream('bob'));
		$this->mountCache->expects(self::never())->method('getMountsForFileId');

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(GatewayReader::OUTCOME_OK, $opened['outcome']);
		self::assertSame(0, $opened['asked']);
		self::assertSame('alice', $opened['reader']);
		self::assertSame([['alice', null]], $this->opens());
		self::assertSame('alice', stream_get_contents($opened['stream']));
	}

	public function testASecureViewRefusalOpensTheFileAgainAsTheOwnerInsideActAs(): void {
		$this->mounts([['alice', '/alice/files/a.odt/', self::SHARING], ['bob', '/bob/', self::LOCAL_HOME]]);
		$this->sees('alice', SecureViewRefusal::real());
		$this->sees('bob', self::stream('bobs bytes'));

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(GatewayReader::OUTCOME_OK, $opened['outcome']);
		self::assertSame(1, $opened['asked']);
		self::assertSame('bob', $opened['reader']);
		self::assertSame('bobs bytes', stream_get_contents($opened['stream']));
		self::assertSame(5, $opened['size']);
		// The first open without an active user, the second as bob, and the
		// folder and the lookup of bob inside the same switch.
		self::assertSame([['alice', null], ['bob', 'bob']], $this->opens());
		self::assertContains(['folder', 'bob', 'bob'], $this->steps);
		self::assertContains(['lookup', 'bob', 'bob'], $this->steps);
		self::assertNull($this->active);
	}

	public function testAnOwnerTheSecureViewRefusesAsWellEndsWithPolicyAndNobodyElseIsAsked(): void {
		// allTags: the watermark applies to every reader, the owner included (E2).
		$this->mounts([
			['alice', '/alice/files/a.odt/', self::SHARING],
			['bob', '/bob/', self::LOCAL_HOME],
			['dave', '/dave/files/a.odt/', self::SHARING],
		]);
		$this->sees('alice', SecureViewRefusal::real());
		$this->sees('bob', SecureViewRefusal::real());
		$this->sees('dave', self::stream('dave'));

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(GatewayReader::OUTCOME_POLICY, $opened['outcome']);
		self::assertSame(1, $opened['asked']);
		self::assertSame([['alice', null], ['bob', 'bob']], $this->opens());
		self::assertNull($this->active);
	}

	public function testWithoutAnOwnerAtMostTwentyReadersAreAskedAndThenPolicy(): void {
		$mounts = [];
		for ($i = 1; $i <= 25; $i++) {
			$uid = sprintf('member%02d', $i);
			$mounts[] = [$uid, '/' . $uid . '/files/TF/', self::GROUPFOLDERS];
			$this->sees($uid, SecureViewRefusal::real());
		}
		$this->mounts($mounts);

		$opened = $this->reader()->open(self::FILE_ID, 'member01');

		self::assertSame(GatewayReader::OUTCOME_POLICY, $opened['outcome']);
		self::assertSame(20, $opened['asked']);
		$opens = $this->opens();
		self::assertCount(21, $opens);
		self::assertSame(['member01', null], $opens[0]);
		self::assertSame(['member20', 'member20'], $opens[20]);
	}

	public function testTheSameMessageWithTheFrameOnlyFurtherUpIsPolicyWithoutAnotherOpen(): void {
		$this->mounts([['alice', '/alice/files/a.odt/', self::SHARING], ['bob', '/bob/', self::LOCAL_HOME]]);
		$this->sees('alice', SecureViewRefusal::frameFurtherUp());
		$this->sees('bob', self::stream('bob'));

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(GatewayReader::OUTCOME_POLICY, $opened['outcome']);
		self::assertSame(0, $opened['asked']);
		self::assertSame([['alice', null]], $this->opens());
	}

	public function testTheRightFrameWithAnotherMessageIsPolicyWithoutAnotherOpen(): void {
		$this->mounts([['alice', '/alice/files/a.odt/', self::SHARING], ['bob', '/bob/', self::LOCAL_HOME]]);
		$this->sees('alice', SecureViewRefusal::otherMessage());
		$this->sees('bob', self::stream('bob'));

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(GatewayReader::OUTCOME_POLICY, $opened['outcome']);
		self::assertSame(0, $opened['asked']);
		self::assertSame([['alice', null]], $this->opens());
	}

	public function testARefusalOfAccessControlIsPolicyWithoutAnotherOpen(): void {
		$this->mounts([['alice', '/alice/files/a.odt/', self::SHARING], ['bob', '/bob/', self::LOCAL_HOME]]);
		$this->sees('alice', SecureViewRefusal::accessControl());
		$this->sees('bob', self::stream('bob'));

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(GatewayReader::OUTCOME_POLICY, $opened['outcome']);
		self::assertSame([['alice', null]], $this->opens());
	}

	public function testAnotherForbiddenExceptionAtTheSecondReaderEndsWithoutAThird(): void {
		$this->mounts([
			['anna', '/anna/files/TF/', self::GROUPFOLDERS],
			['bert', '/bert/files/TF/', self::GROUPFOLDERS],
			['cora', '/cora/files/TF/', self::GROUPFOLDERS],
		]);
		$this->sees('anna', SecureViewRefusal::real());
		$this->sees('bert', SecureViewRefusal::accessControl());
		$this->sees('cora', self::stream('cora'));

		$opened = $this->reader()->open(self::FILE_ID, 'anna');

		self::assertSame(GatewayReader::OUTCOME_POLICY, $opened['outcome']);
		self::assertSame(2, $opened['asked']);
		self::assertSame([['anna', null], ['anna', 'anna'], ['bert', 'bert']], $this->opens());
	}

	public function testAnOwnerWhoDoesNotResolveTheFileInActAsEndsWithPolicy(): void {
		$this->mounts([
			['alice', '/alice/files/a.odt/', self::SHARING],
			['bob', '/bob/', self::LOCAL_HOME],
			['dave', '/dave/files/a.odt/', self::SHARING],
		]);
		$this->sees('alice', SecureViewRefusal::real());
		$this->folderOf('bob', null);
		$this->sees('dave', self::stream('dave'));

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(GatewayReader::OUTCOME_POLICY, $opened['outcome']);
		self::assertSame(1, $opened['asked']);
		self::assertSame([['alice', null]], $this->opens());
	}

	public function testAnOwnerWhoseFolderCannotBeBuiltEndsWithPolicy(): void {
		$this->mounts([
			['alice', '/alice/files/a.odt/', self::SHARING],
			['bob', '/bob/', self::LOCAL_HOME],
			['dave', '/dave/files/a.odt/', self::SHARING],
		]);
		$this->sees('alice', SecureViewRefusal::real());
		$this->brokenFolderOf('bob', new \RuntimeException('/secret/bob'));
		$this->sees('dave', self::stream('dave'));

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(GatewayReader::OUTCOME_POLICY, $opened['outcome']);
		self::assertSame([['alice', null]], $this->opens());
		self::assertNull($this->active);
	}

	public function testWithoutAnOwnerAReaderWhoDoesNotResolveIsPassedOver(): void {
		$this->mounts([
			['anna', '/anna/files/TF/', self::GROUPFOLDERS],
			['bert', '/bert/files/TF/', self::GROUPFOLDERS],
			['cora', '/cora/files/TF/', self::GROUPFOLDERS],
		]);
		$this->sees('anna', SecureViewRefusal::real());
		$this->folderOf('bert', null);
		$this->sees('cora', self::stream('cora'));

		$opened = $this->reader()->open(self::FILE_ID, 'anna');

		self::assertSame(GatewayReader::OUTCOME_OK, $opened['outcome']);
		self::assertSame('cora', $opened['reader']);
		self::assertSame(3, $opened['asked']);
		self::assertSame([['anna', null], ['anna', 'anna'], ['cora', 'cora']], $this->opens());
	}

	public function testADeletedReaderIsPassedOverAndNeverTurnsIntoNotFound(): void {
		// The folder of bert throws NoUserException: the user is gone since the
		// mount cache was written. Only the named user may produce a not-found
		// answer; a reader of the second round is skipped, and the debug line
		// carries the class and never the text.
		$this->mounts([
			['anna', '/anna/files/TF/', self::GROUPFOLDERS],
			['bert', '/bert/files/TF/', self::GROUPFOLDERS],
		]);
		$this->sees('anna', SecureViewRefusal::real());
		$this->logger->expects(self::never())->method('error');
		$this->logger->expects(self::atLeastOnce())->method('debug')->with(
			self::isString(),
			self::callback(static fn (array $context): bool => array_keys($context) === ['fileId', 'class']
				&& $context['fileId'] === self::FILE_ID
				&& $context['class'] === \OC\User\NoUserException::class),
		);

		$opened = $this->reader()->open(self::FILE_ID, 'anna');

		self::assertSame(GatewayReader::OUTCOME_POLICY, $opened['outcome']);
		self::assertNotSame(GatewayReader::OUTCOME_NOT_FOUND, $opened['outcome']);
	}

	public function testAStorageThatIsNotAvailableAtTheOpenOfTheOwnerTravelsUp(): void {
		$this->mounts([['alice', '/alice/files/a.odt/', self::SHARING], ['bob', '/bob/', self::LOCAL_HOME]]);
		$this->sees('alice', SecureViewRefusal::real());
		$this->sees('bob', new StorageNotAvailableException('down'));

		try {
			$this->reader()->open(self::FILE_ID, 'alice');
			self::fail('the exception of the owner\'s open must reach the controller');
		} catch (StorageNotAvailableException) {
			$this->addToAssertionCount(1);
		}
		self::assertNull($this->active);
	}

	public function testAStorageThatIsNotAvailableAtTheOpenOfAReaderTravelsUp(): void {
		$this->mounts([['anna', '/anna/files/TF/', self::GROUPFOLDERS], ['bert', '/bert/files/TF/', self::GROUPFOLDERS]]);
		$this->sees('anna', SecureViewRefusal::real());
		$this->sees('bert', new StorageNotAvailableException('down'));
		// anna is asked again in actAs first and refused again, then bert.
		$this->expectException(StorageNotAvailableException::class);

		$this->reader()->open(self::FILE_ID, 'anna');
	}

	public function testANamedUserWhoDoesNotResolveTheFileIsNotFoundWithoutAnotherOpen(): void {
		$this->mounts([['bob', '/bob/', self::LOCAL_HOME]]);
		$this->folderOf('alice', null);
		$this->sees('bob', self::stream('bob'));
		$this->mountCache->expects(self::never())->method('getMountsForFileId');

		$opened = $this->reader()->open(self::FILE_ID, 'alice');

		self::assertSame(GatewayReader::OUTCOME_NOT_FOUND, $opened['outcome']);
		self::assertSame(0, $opened['asked']);
		self::assertSame([], $this->opens());
	}

	public function testANamedUserThatDoesNotExistTravelsUpAsNoUserException(): void {
		$this->mountCache->expects(self::never())->method('getMountsForFileId');
		$this->expectException(\OC\User\NoUserException::class);

		$this->reader()->open(self::FILE_ID, 'ghost');
	}

	public function testTheRecognitionAsksForTheExceptionClassTheMessageAndTheFirstFrame(): void {
		self::assertTrue(GatewayReader::isSecureViewRefusal(SecureViewRefusal::real()));
		self::assertFalse(GatewayReader::isSecureViewRefusal(SecureViewRefusal::frameFurtherUp()));
		self::assertFalse(GatewayReader::isSecureViewRefusal(SecureViewRefusal::otherMessage()));
		self::assertFalse(GatewayReader::isSecureViewRefusal(SecureViewRefusal::accessControl()));
		self::assertFalse(GatewayReader::isSecureViewRefusal(new \RuntimeException(SecureViewRefusal::MESSAGE)));
		self::assertFalse(GatewayReader::isSecureViewRefusal(new ForbiddenException(SecureViewRefusal::MESSAGE, false)));
	}
}
