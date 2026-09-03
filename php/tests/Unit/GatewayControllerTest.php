<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Controller\GatewayController;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\Http\StreamResponse;
use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\IRequest;
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

	protected function setUp(): void {
		parent::setUp();

		$this->rootFolder = $this->createMock(IRootFolder::class);
		$this->logger = $this->createMock(LoggerInterface::class);
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

		return new GatewayController($request, $this->rootFolder, $this->logger);
	}

	public function testACallFromTheBackendUnderItsOwnAppIdDeliversTheFileContents(): void {
		$stream = fopen('php://memory', 'rb+');
		self::assertIsResource($stream);

		$file = $this->createMock(File::class);
		// The 'r' is the entire read only guarantee of this route, so the mode is
		// part of the assertion and not an implementation detail. Gate A in
		// backend/tests holds the allowlist of ways to open a file at all.
		$file->expects(self::once())->method('fopen')->with('r')->willReturn($stream);

		$userFolder = $this->createMock(Folder::class);
		$userFolder->method('getFirstNodeById')->with(11)->willReturn($file);
		$this->rootFolder->method('getUserFolder')->with('alice')->willReturn($userFolder);

		$response = $this->controller($this->backendAppId())->getFileContents(11, 'alice');

		self::assertInstanceOf(StreamResponse::class, $response);

		fclose($stream);
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
}
