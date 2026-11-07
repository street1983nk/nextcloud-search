<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Controller\GatewayController;
use OCA\Findling\Http\BoundedStreamReader;
use OCA\Findling\Http\BoundedStreamResponse;
use OCA\Findling\Service\ReaderContext;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\Http\IOutput;
use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\Files\Storage\IStorage;
use OCP\Files\StorageNotAvailableException;
use OCP\IRequest;
use OCP\IUser;
use OCP\IUserManager;
use OCP\IUserSession;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * Behaviour 9 of docs/testing.md, section "The gap", and it is the one that had
 * nowhere else to go.
 *
 * The route attribute answers "is this a registered external app", not "is this
 * our external app". Every other backend on the instance passes that test, so
 * the comparison of the EX-APP-ID header against the one backend app id of this
 * product is what stands between a container somebody installed last week and
 * the file content of every user. docs/testing.md says outright that the
 * integration job cannot reach this: it would need a second registered ExApp
 * calling the gateway under a foreign app id, which is a whole second
 * registration, a second image and a second daemon. Doubled here, it is a header
 * and four cases.
 *
 * What this suite does NOT replace is Gate B in backend/tests. That gate reads
 * the sources and holds the attributes of the route itself, so a route that lost
 * its ExAppRequired or its rejectForeignCaller call fails there. This file holds
 * the other half, what the method does once it runs, and neither of the two can
 * see what the other one sees.
 *
 * Everything is a double. No file system is touched, and the one stream below is
 * in memory.
 */
#[CoversClass(GatewayController::class)]
final class GatewayControllerTest extends TestCase {
	private IRootFolder&MockObject $rootFolder;
	private LoggerInterface&MockObject $logger;
	private IUserSession&MockObject $session;
	private IUserManager&MockObject $userManager;
	private ?IUser $active = null;
	private float $clock = 0.0;

	protected function setUp(): void {
		parent::setUp();
		ScriptedStream::register();
		$this->clock = 0.0;

		$this->rootFolder = $this->createMock(IRootFolder::class);
		$this->logger = $this->createMock(LoggerInterface::class);

		// Stateful, so the cases can observe who is active at each step.
		$this->session = $this->createMock(IUserSession::class);
		$this->session->method('getUser')->willReturnCallback(fn (): ?IUser => $this->active);
		$this->session->method('setVolatileActiveUser')->willReturnCallback(function (?IUser $user): void {
			$this->active = $user;
		});
		$this->userManager = $this->createMock(IUserManager::class);
		$this->userManager->method('get')->willReturnCallback(function (string $uid): ?IUser {
			if ($uid === 'ghost') {
				return null;
			}
			$user = $this->createMock(IUser::class);
			$user->method('getUID')->willReturn($uid);

			return $user;
		});
	}

	protected function tearDown(): void {
		ScriptedStream::unregister();
		parent::tearDown();
	}

	/**
	 * The app id of the container, read out of the class instead of copied.
	 *
	 * Both ids are frozen because the app certificate is bound to them, and a
	 * copy here would keep asserting the old one after a rename while the
	 * gateway had already started refusing the real backend.
	 */
	private function backendAppId(): string {
		$value = (new \ReflectionClass(Application::class))->getConstant('BACKEND_APP_ID');

		self::assertIsString($value, 'BACKEND_APP_ID is gone or is no longer a string');

		return $value;
	}

	/**
	 * The controller with one header staged. An absent header arrives as an empty
	 * string, which is what IRequest promises and what the fourth case uses.
	 */
	private function controller(string $callerAppId): GatewayController {
		$request = $this->createMock(IRequest::class);
		$request->method('getHeader')->willReturnCallback(
			static fn (string $name): string => $name === 'EX-APP-ID' ? $callerAppId : '',
		);

		return new GatewayController(
			$request,
			$this->rootFolder,
			$this->logger,
			new ReaderContext($this->session, $this->userManager),
			// The reader on a fake clock, so the thirty second deadline of the
			// first block costs no real time in the cases that run into it.
			new BoundedStreamReader(
				fn (): float => $this->clock,
				function (int $microseconds): void {
					$this->clock += $microseconds / 1_000_000;
				},
			),
		);
	}

	/**
	 * A storage double that answers instanceOfStorage for the two classes the
	 * gateway asks about. Everything else is not this storage.
	 */
	private function storage(bool $smb, bool $encrypted): IStorage&MockObject {
		$storage = $this->createMock(IStorage::class);
		$storage->method('instanceOfStorage')->willReturnCallback(
			static fn (string $class): bool => match ($class) {
				'OCA\\Files_External\\Lib\\Storage\\SMB' => $smb,
				'OC\\Files\\Storage\\Wrapper\\Encryption' => $encrypted,
				default => false,
			},
		);

		return $storage;
	}

	public function testACallFromTheBackendUnderItsOwnAppIdDeliversTheFileContents(): void {
		$stream = fopen('php://memory', 'rb+');
		self::assertIsResource($stream);

		$file = $this->createMock(File::class);
		// The 'r' is the entire read only guarantee of this route, so the mode is
		// part of the assertion and not an implementation detail. Gate A in
		// backend/tests holds the allowlist of ways to open a file at all.
		$file->expects(self::once())->method('fopen')->with('r')->willReturn($stream);
		$file->method('isReadable')->willReturn(true);
		$file->method('getStorage')->willReturn($this->storage(false, false));

		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->with(11)->willReturn($file);
		$this->rootFolder->method('getUserFolder')->with('alice')->willReturn($userFolder);

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertInstanceOf(BoundedStreamResponse::class, $response);

		fclose($stream);
	}

	public function testAFileTheUserReachesAndMayNotReadIsNotServed(): void {
		// Issue #14 from the gateway side. A Team Folder member whose advanced
		// permissions take the read bit away still resolves the node; the bytes
		// must not travel in their name, and the answer is word for word the
		// one for a file that does not exist, so it cannot be used to probe.
		$closed = $this->createMock(File::class);
		$closed->method('isReadable')->willReturn(false);
		$closed->expects(self::never())->method('fopen');

		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->willReturnCallback(
			static fn (int $fileId): ?File => $fileId === 11 ? $closed : null,
		);
		$this->rootFolder->method('getUserFolder')->with('alice')->willReturn($userFolder);

		$controller = $this->controller($this->backendAppId());
		$unreadable = $controller->getFileContents(11, 'alice');
		$missing = $controller->getFileContents(999999, 'alice');

		self::assertInstanceOf(DataResponse::class, $unreadable);
		self::assertInstanceOf(DataResponse::class, $missing);
		self::assertSame(Http::STATUS_NOT_FOUND, $unreadable->getStatus());
		self::assertSame($missing->getStatus(), $unreadable->getStatus());
		self::assertSame($missing->getData(), $unreadable->getData());
	}

	public function testACallFromAForeignExAppIsRefused(): void {
		// The threat in one case: an assistant, a chat backend or anything else
		// AppAPI has registered is an external app too, and without this
		// comparison it would read any file of any user through this route.
		$this->rootFolder->expects(self::never())->method('getUserFolder');

		$response = $this->controller('some_other_backend')->getFileContents(11, 'alice');

		self::assertInstanceOf(DataResponse::class, $response);
		self::assertSame(Http::STATUS_FORBIDDEN, $response->getStatus());
	}

	public function testACallWithoutTheHeaderIsRefusedAndDoesNotFail(): void {
		// A missing header is a refusal and never a server error. The difference
		// is not cosmetic: a 500 is an outage an admin chases, and it would also
		// be a way to tell "no header" apart from "wrong header" from the outside.
		$response = $this->controller('')->getFileContents(11, 'alice');

		self::assertInstanceOf(DataResponse::class, $response);
		self::assertSame(Http::STATUS_FORBIDDEN, $response->getStatus());
		self::assertNotSame(Http::STATUS_INTERNAL_SERVER_ERROR, $response->getStatus());
	}

	public function testTheRefusalForAForeignExAppSaysNothingAboutWhetherTheFileExists(): void {
		// Not in the list of twelve by name, and it follows from the rule of this
		// project that a refusal says nothing about the stock. Here it holds
		// structurally rather than by care: the comparison is the first statement
		// of the route, so nothing has asked the file system by the time the
		// answer is built. The never expectation below is the load bearing half,
		// the equality of the two answers is what an outside caller would see.
		$this->rootFolder->expects(self::never())->method('getUserFolder');

		$controller = $this->controller('some_other_backend');
		$existing = $controller->getFileContents(11, 'alice');
		$missing = $controller->getFileContents(999999, 'alice');

		self::assertInstanceOf(DataResponse::class, $existing);
		self::assertInstanceOf(DataResponse::class, $missing);
		self::assertSame($existing->getStatus(), $missing->getStatus());
		self::assertSame($existing->getData(), $missing->getData());
	}

	public function testTheRefusalIsLoggedWithTheCallerAppIdAndWithNothingElse(): void {
		// The app id is the one thing worth logging here and the only thing that
		// is logged: no user id, no file id, no path. A gateway refusal that
		// carried the path would move the disclosure it prevents into the
		// Nextcloud log.
		$this->logger->expects(self::once())
			->method('warning')
			->with(
				'Findling: content gateway called by a foreign ExApp',
				['app' => 'some_other_backend'],
			);

		$this->controller('some_other_backend')->getFileContents(11, 'alice');
	}

	public function testTheFolderAndTheLookupRunAsTheUserAndTheOpenAfterTheRestore(): void {
		// The second round of #14. groupfolders builds a member's mount as "in
		// share" when somebody else is active, so the folder and the lookup run
		// with alice active. The open runs after the restore, so read hooks see
		// the identity of the request and not alice.
		$stream = fopen('php://memory', 'rb+');
		self::assertIsResource($stream);
		$steps = [];

		$file = $this->createMock(File::class);
		$file->method('isReadable')->willReturn(true);
		$file->method('getStorage')->willReturn($this->storage(false, false));
		$file->method('fopen')->willReturnCallback(function () use ($stream, &$steps) {
			$steps[] = ['fopen', $this->active?->getUID()];

			return $stream;
		});
		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->willReturnCallback(function () use ($file, &$steps): File {
			$steps[] = ['lookup', $this->active?->getUID()];

			return $file;
		});
		$this->rootFolder->method('getUserFolder')->willReturnCallback(function () use ($userFolder, &$steps): Folder {
			$steps[] = ['folder', $this->active?->getUID()];

			return $userFolder;
		});

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertInstanceOf(BoundedStreamResponse::class, $response);
		self::assertSame([['folder', 'alice'], ['lookup', 'alice'], ['fopen', null]], $steps);
		self::assertNull($this->active);

		fclose($stream);
	}

	/**
	 * A readable file of alice whose open behaves as the closure says, of the
	 * given size, on a storage of the given kind (local unless said otherwise).
	 */
	private function fileOpeningAs(\Closure $open, int $size = 0, bool $smb = false, bool $encrypted = false): void {
		$file = $this->createMock(File::class);
		$file->method('isReadable')->willReturn(true);
		$file->method('getSize')->willReturn($size);
		$file->method('getStorage')->willReturn($this->storage($smb, $encrypted));
		$file->method('fopen')->with('r')->willReturnCallback($open);
		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->with(11)->willReturn($file);
		$this->rootFolder->method('getUserFolder')->with('alice')->willReturn($userFolder);
	}

	public function testAFileThatCannotBeOpenedAnswers422AndLeavesOneLogLine(): void {
		// Befund E of issue #36: the branch used to leave no trace on the
		// Nextcloud side. One static sentence and the file id, nothing else.
		$this->fileOpeningAs(static fn () => false);
		$this->logger->expects(self::once())
			->method('warning')
			->with('Findling: a file could not be opened for reading, answered 422', ['fileId' => 11]);
		$this->logger->expects(self::never())->method('error');

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertInstanceOf(DataResponse::class, $response);
		self::assertSame(Http::STATUS_UNPROCESSABLE_ENTITY, $response->getStatus());
		self::assertSame(['error' => 'File could not be opened for reading.'], $response->getData());
	}

	public function testAStorageThatIsNotAvailableAtTheOpenStaysA500AndNeverA404(): void {
		// The case of issue #36, and the regression guard of "Warum kein
		// PHP-404" (plan 40-06, E-40-06-03 struck): a 404 would be a lasting
		// skipped(gone) for every file of a storage that is only down for a
		// while. The answer stays the 500 of the catch-all branch, and the
		// container judges the one file failed(gateway_error).
		$this->fileOpeningAs(static function (): never {
			throw new StorageNotAvailableException('File by id 11 not found');
		});
		$this->logger->expects(self::once())
			->method('error')
			->with('Findling: unknown error reading a file', self::callback(
				static fn (array $context): bool => array_keys($context) === ['exception']
					&& $context['exception'] instanceof StorageNotAvailableException,
			));

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertInstanceOf(DataResponse::class, $response);
		self::assertSame(Http::STATUS_INTERNAL_SERVER_ERROR, $response->getStatus());
		self::assertNotSame(Http::STATUS_NOT_FOUND, $response->getStatus());
		self::assertSame(['error' => 'Unknown error occurred.'], $response->getData());
	}

	public function testAnyOtherThrowableAtTheOpenIsStillA500(): void {
		$this->fileOpeningAs(static function (): never {
			throw new \RuntimeException('something else broke');
		});
		$this->logger->expects(self::once())->method('error')->with('Findling: unknown error reading a file', self::anything());

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertInstanceOf(DataResponse::class, $response);
		self::assertSame(Http::STATUS_INTERNAL_SERVER_ERROR, $response->getStatus());
		self::assertSame(['error' => 'Unknown error occurred.'], $response->getData());
	}

	public function testAnUnknownUserStillGetsTheNotFoundBodyAndIsNotSwitchedTo(): void {
		// No switch for a name the user manager does not know, so the answer is
		// the unchanged NoUserException path: the same 404 body as "no such file".
		$this->session->expects(self::never())->method('setVolatileActiveUser');
		$this->rootFolder->method('getUserFolder')->willThrowException(new \OC\User\NoUserException('ghost'));

		$unknown = $this->controller($this->backendAppId())->getFileContents(11, 'ghost');

		self::assertInstanceOf(DataResponse::class, $unknown);
		self::assertSame(Http::STATUS_NOT_FOUND, $unknown->getStatus());
		self::assertSame(['error' => 'Node is not a file or could not be found.'], $unknown->getData());
	}

	/**
	 * Everything the response writes, by running its callback against an
	 * output double, the way App.php does after the headers.
	 */
	private function body(BoundedStreamResponse $response): string {
		$body = '';
		$output = $this->createStub(IOutput::class);
		$output->method('setOutput')->willReturnCallback(static function (string $block) use (&$body): void {
			$body .= $block;
		});
		$response->callback($output);

		return $body;
	}

	/**
	 * The one answer every refusal before the headers has to be: the 422 of the
	 * branch that existed before plan 43-17, with its one log line.
	 */
	private function expectTheCannotOpenAnswer(): void {
		$this->logger->expects(self::once())
			->method('warning')
			->with('Findling: a file could not be opened for reading, answered 422', ['fileId' => 11]);
		$this->logger->expects(self::never())->method('error');
	}

	private static function assertTheCannotOpenAnswer(mixed $response): void {
		self::assertInstanceOf(DataResponse::class, $response);
		self::assertSame(Http::STATUS_UNPROCESSABLE_ENTITY, $response->getStatus());
		self::assertSame(['error' => 'File could not be opened for reading.'], $response->getData());
	}

	public function testAnUnencryptedSmbStorageIsReadNonBlocking(): void {
		// D-43-16: the storage decides, through instanceOfStorage, which sees
		// through every wrapper of the storage (Jail, Shared). The switch reached
		// the source of the stream, so the reader was told to read non blocking.
		$stream = ScriptedStream::open('smb', ['hello', ScriptedStream::EOF]);
		$this->fileOpeningAs(static fn () => $stream, 5, smb: true);

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertInstanceOf(BoundedStreamResponse::class, $response);
		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(1, ScriptedStream::blockingCalls('smb'));
		self::assertSame('hello', $this->body($response));
		self::assertTrue(ScriptedStream::closed('smb'));
	}

	public function testSmbUnderServerSideEncryptionIsReadBlockingAsBefore(): void {
		// B1: the switch would travel through the encryption stream to the
		// source, and stream_read_block would hand half a cipher block to the
		// decryption at the first empty read.
		$stream = ScriptedStream::open('enc', ['hello', ScriptedStream::EOF]);
		$this->fileOpeningAs(static fn () => $stream, 5, smb: true, encrypted: true);

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertInstanceOf(BoundedStreamResponse::class, $response);
		self::assertSame(0, ScriptedStream::blockingCalls('enc'));
		self::assertSame('hello', $this->body($response));
	}

	public function testALocalStorageIsReadBlockingAsBefore(): void {
		$stream = ScriptedStream::open('local', ['hello', ScriptedStream::EOF]);
		$this->fileOpeningAs(static fn () => $stream, 5);

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertInstanceOf(BoundedStreamResponse::class, $response);
		self::assertSame(0, ScriptedStream::blockingCalls('local'));
		self::assertSame('hello', $this->body($response));
	}

	public function testAFileThatNeverDeliversItsFirstBlockAnswers422AndIsClosed(): void {
		// The hang of run 42404849768: smbclient waits, nothing arrives. The
		// deadline ends it before the headers, so the answer can still be the
		// 422 of the existing branch.
		$stream = ScriptedStream::open('stuck', static fn (): string => ScriptedStream::EMPTY);
		$this->fileOpeningAs(static fn () => $stream, 100, smb: true);
		$this->expectTheCannotOpenAnswer();

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertTheCannotOpenAnswer($response);
		self::assertTrue(ScriptedStream::closed('stuck'));
		self::assertGreaterThanOrEqual(BoundedStreamReader::FIRST_BYTE_SECONDS, $this->clock);
	}

	public function testANonEmptyFileThatEndsWithoutAByteAnswers422(): void {
		// The nudged smbclient read its exit and ended: zero bytes of a file the
		// cache says has 100.
		$stream = ScriptedStream::open('denied', [ScriptedStream::EMPTY, ScriptedStream::EOF]);
		$this->fileOpeningAs(static fn () => $stream, 100, smb: true);
		$this->expectTheCannotOpenAnswer();

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertTheCannotOpenAnswer($response);
		self::assertTrue(ScriptedStream::closed('denied'));
	}

	public function testAFailedFirstReadAnswers422(): void {
		$stream = ScriptedStream::open('broken', [ScriptedStream::ERROR]);
		$this->fileOpeningAs(static fn () => $stream, 100, smb: true);
		$this->expectTheCannotOpenAnswer();

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertTheCannotOpenAnswer($response);
		self::assertTrue(ScriptedStream::closed('broken'));
	}

	public function testAnEmptyFileIsAnEmptyOkWithoutWaiting(): void {
		$stream = ScriptedStream::open('zero', [ScriptedStream::EOF]);
		$this->fileOpeningAs(static fn () => $stream, 0, smb: true);
		$this->logger->expects(self::never())->method('warning');

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertInstanceOf(BoundedStreamResponse::class, $response);
		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame('', $this->body($response));
		self::assertSame(0.0, $this->clock);
	}

	public function testASharingViolationAtTheOpenAnswers422WithoutTheExceptionText(): void {
		// Native mode: libsmbclient reports EBUSY, icewind/smb throws
		// FileInUseException, and SMB::fopen does not catch it. It is a
		// statement about this one file, so it is the 422 of a file that cannot
		// be opened and not the 500 of a storage. Its message carries the path,
		// which is why there is no error line with the exception (L6).
		$class = 'Icewind\\SMB\\Exception\\FileInUseException';
		if (!class_exists($class)) {
			self::markTestSkipped('icewind/smb is not in the autoload space of this server checkout');
		}
		$this->fileOpeningAs(static function () use ($class): never {
			throw new $class('/secret/share/path.docx');
		});
		$this->expectTheCannotOpenAnswer();

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertTheCannotOpenAnswer($response);
	}
}
