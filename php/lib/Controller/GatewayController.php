<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Http\BoundedStreamReader;
use OCA\Findling\Http\BoundedStreamResponse;
use OCA\Findling\Service\ReaderContext;
use OCA\Findling\Service\SearchService;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\Files\File;
use OCP\Files\IRootFolder;
use OCP\IRequest;
use Psr\Log\LoggerInterface;

/**
 * The read only channel the container uses to get at file content.
 *
 * The permission decision happens here and nowhere else. The container names a
 * user, this class resolves the file through that user's own folder, so the
 * real Nextcloud permission model answers the question. There is no second,
 * drifting permission model in Python.
 */
final class GatewayController extends OCSController {
	/**
	 * The three classes the gateway asks about, as strings on purpose:
	 * files_external does not have to be enabled, icewind/smb does not have to
	 * be in the autoload space, and instanceOfStorage and is_a take a name and
	 * do not load anything that is not there.
	 */
	private const SMB_STORAGE = 'OCA\Files_External\Lib\Storage\SMB';
	private const ENCRYPTED_STORAGE = 'OC\Files\Storage\Wrapper\Encryption';
	private const SMB_FILE_IN_USE = 'Icewind\SMB\Exception\FileInUseException';

	/**
	 * The reader comes from the container like every other collaborator. Its
	 * constructor takes nothing but closures and floats with defaults, and the
	 * container of Nextcloud falls back to the default value of a parameter it
	 * cannot resolve (SimpleContainer::buildClassConstructorParameters), so it
	 * builds the reader with the real clock, usleep and connection_aborted.
	 */
	public function __construct(
		IRequest $request,
		private IRootFolder $rootFolder,
		private LoggerInterface $logger,
		private ReaderContext $readerContext,
		private BoundedStreamReader $streamReader,
	) {
		parent::__construct(Application::APP_ID, $request);
	}

	/**
	 * Full path from the outside:
	 * GET /ocs/v2.php/apps/findling/files/{fileId}?userId=<uid>
	 *
	 * The first attribute below locks browsers and ordinary users out. The
	 * signed AppAPI header is the credential here, which is also why session
	 * CSRF does not apply. All three are spelled out fully qualified, in the
	 * spelling of QueueController and ReconcileController: the trust boundary
	 * gate of plan 03-14 counts route attributes by reading the sources, and an
	 * import line would count as a route without being one. One spelling in
	 * every controller is what keeps that count exact.
	 *
	 * The file id is an int and there is no path string anywhere in this
	 * signature, so path traversal is structurally impossible rather than
	 * filtered.
	 *
	 * The requirement on the placeholder is not cosmetic. Nextcloud collects
	 * attribute routes with a DirectoryIterator over lib/Controller, so the order
	 * in which two routes enter the Symfony collection is file system order, and
	 * the first match wins. Without the digit rule this route would match
	 * /files/slice as well, and the reading slice route of the reconcile (plan
	 * 03-11) would work or not work depending on how the file system happened to
	 * list this directory.
	 */
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'GET', url: '/files/{fileId}', requirements: ['fileId' => '\d+'])]
	public function getFileContents(int $fileId, string $userId): DataResponse|BoundedStreamResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		try {
			// Reachable and readable, both asked in the one place that asks them
			// (issue #14). A Team Folder member the advanced permissions close a
			// file to reaches a node without the read bit, and the bytes must not
			// travel in the name of somebody who may not open them. The queue
			// already names a reader who may, so this refusal is the backstop for
			// a permission that changed between the claim and the fetch.
			//
			// The folder and the lookup run with the named user as the active
			// user of the request (second round of #14, see ReaderContext):
			// groupfolders builds the mount of a member as "in share" when the
			// active user is somebody else, here nobody, and a +read -share ACL
			// then hides the file from the very member the queue chose.
			$file = $this->readerContext->actAs(
				$userId,
				fn (): ?File => SearchService::readableFile($this->rootFolder->getUserFolder($userId), $fileId),
			);
			// Not visible to this user, not readable for them and not existing at
			// all deliberately give the same answer, so the gateway cannot be used
			// to probe for files the user is not allowed to see.
			if ($file === null) {
				return new DataResponse(['error' => 'Node is not a file or could not be found.'], Http::STATUS_NOT_FOUND);
			}

			// The 'r' is the entire read only guarantee at this spot. It must
			// never become 'r+', 'w', 'a' or 'x'.
			//
			// Deliberately after the switch above has been undone. The mount is
			// already built with the member's view, so the open does not need the
			// switch, and read hooks (admin_audit, activity) must not attribute a
			// read of Findling to the member: they see the same identity as
			// before the fix.
			//
			// The size and the storage are asked before the open. The size is the
			// one of the file cache and only tells an empty file from one whose
			// open failed; it is never promised to the client (see
			// BoundedStreamResponse).
			//
			// Non blocking only for an SMB storage without server side
			// encryption (D-43-16). The decision is the storage's and not the
			// stream's (N1): the View wraps nearly every stream in a
			// CallbackWrapper when locking is on, so the outermost layer says
			// nothing about the storage, and stream_set_blocking travels through
			// the encryption stream down to the source, where the first empty read
			// would cut a cipher block in half (B1). instanceOfStorage looks
			// through the whole wrapper chain of the storage, Jail and Shared
			// included. Every other storage is read blocking, as before.
			$size = max(0, (int)$file->getSize());
			$storage = $file->getStorage();
			$nonBlocking = $storage->instanceOfStorage(self::SMB_STORAGE)
				&& !$storage->instanceOfStorage(self::ENCRYPTED_STORAGE);
			$stream = $file->fopen('r');
			if (!$stream) {
				return $this->cannotOpen($fileId);
			}

			// The answer is decided after the first block and before any header.
			// An SMB open that failed on the server does not fail in fopen in the
			// wrapped mode: it is a stream that never delivers (the hang of run
			// 42404849768) or, once smbclient has been nudged into reading its
			// exit, a stream that ends without a byte. Either is the 422 of the
			// branch above, and so is a read that fails. Zero bytes of a file the
			// cache says is empty are a complete answer.
			$primed = $this->streamReader->prime($stream, $nonBlocking);
			$outcome = $primed['outcome'];
			if ($outcome === BoundedStreamReader::OUTCOME_ERROR
				|| $outcome === BoundedStreamReader::OUTCOME_TIMEOUT
				|| ($outcome === BoundedStreamReader::OUTCOME_EMPTY && $size > 0)) {
				fclose($stream);
				return $this->cannotOpen($fileId);
			}

			return new BoundedStreamResponse(
				$stream,
				$primed['head'],
				$size,
				$primed['reads'],
				$primed['nonBlocking'],
				$fileId,
				$this->streamReader,
				$this->logger,
			);
		} catch (\OC\User\NoUserException) {
			// Word for word the answer of the not-found branch above, on purpose.
			// A 500 for "no such user" next to a 404 for "not your file" is
			// exactly the difference a script needs to enumerate the user names of
			// an instance through this route.
			//
			// getUserFolder() throws this from the private namespace of the server
			// and there is no OCP alias for it. If it is ever renamed upstream,
			// this catch stops matching and the answer falls back to the generic
			// 500 below, which is the behaviour before this commit rather than a
			// new failure.
			$this->logger->debug('Findling: content gateway asked for a user that does not exist');
			return new DataResponse(['error' => 'Node is not a file or could not be found.'], Http::STATUS_NOT_FOUND);
		} catch (\Throwable $e) {
			// A sharing violation (EBUSY in the native mode of icewind/smb) is a
			// statement about this one file, not about the storage: SMB::fopen
			// does not catch it, and it lands here. It gets the 422 of a file that
			// cannot be opened, and deliberately no error line with the exception:
			// its message carries the path on the share (security audit L6).
			// is_a with a string, so icewind/smb need not be loaded.
			if (is_a($e, self::SMB_FILE_IN_USE)) {
				return $this->cannotOpen($fileId);
			}

			// This is where the case of issue #36 lands: a file on a mount whose
			// storage is not available, fopen throws StorageNotAvailableException,
			// and the answer is this 500 on purpose. The container judges the one
			// file failed(gateway_error) and goes on with the pass (plan 40-06,
			// task 1). A 404 here would be a lasting skipped(gone), a quiet write
			// off of every file of a storage that is only down for an hour, and it
			// is deliberately not introduced (E-40-06-03 struck).
			//
			// The exception travels in the exception field, which Nextcloud
			// renders itself, and the message of this app is a static sentence
			// (security audit L6). The rule of this project is that the log
			// carries counters and reason codes and nothing else, and a library
			// message is precisely where a path or an SQL fragment shows up: the
			// file system layer of Nextcloud puts absolute paths into its
			// exceptions, and this route is reached with a file id of any user
			// on the instance.
			$this->logger->error('Findling: unknown error reading a file', ['exception' => $e]);
			return new DataResponse(['error' => 'Unknown error occurred.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}
	}

	/**
	 * The one 422 of this route, for every file that cannot be opened for
	 * reading: fopen false, a first block that never comes or is empty while
	 * the file is not, a failed read, a sharing violation.
	 *
	 * Befund E of issue #36: this branch used to leave no trace on the
	 * Nextcloud side, while the container only saw a 422. A static sentence and
	 * the file id, never a path or a user (security audit L6): the id is what an
	 * admin looks the file up by.
	 */
	private function cannotOpen(int $fileId): DataResponse {
		$this->logger->warning('Findling: a file could not be opened for reading, answered 422', ['fileId' => $fileId]);
		return new DataResponse(['error' => 'File could not be opened for reading.'], Http::STATUS_UNPROCESSABLE_ENTITY);
	}

	/**
	 * The attribute on the method above answers "is this a registered external
	 * app", not "is this our external app". Every other backend on the instance
	 * passes that test, so without this comparison any other container, for
	 * instance an AI assistant a user installed last week, could read any file of
	 * any user through this route. AppAPI puts the calling app id into this
	 * header.
	 *
	 * Threat model note, and a deliberate residual risk: this trusts AppAPI to
	 * have authenticated the caller before the request arrives, exactly as the
	 * attribute does. Whoever can forge that header has broken the AppAPI trust
	 * model itself and then owns the gateway of every other ExApp on the instance
	 * too. The alternative would be a second implementation of AppAPI's shared
	 * secret handling inside this app, with a second copy of the secret store.
	 * Not worth it, so it is written down instead of pretended away.
	 *
	 * It is a method of its own rather than an inline comparison since plan
	 * 03-14, and that is not cosmetics. The trust boundary gate reads the first
	 * statement of every route and asks for this call by name; a boundary that
	 * exists in three different shapes cannot be checked, and the one shape that
	 * differed was this one.
	 */
	private function rejectForeignCaller(): ?DataResponse {
		$callerAppId = $this->request->getHeader('EX-APP-ID');
		if ($callerAppId === Application::BACKEND_APP_ID) {
			return null;
		}

		$this->logger->warning('Findling: content gateway called by a foreign ExApp', ['app' => $callerAppId]);

		return new DataResponse(
			['error' => 'This route is reserved for the Findling backend.'],
			Http::STATUS_FORBIDDEN,
		);
	}
}
