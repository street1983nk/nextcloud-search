<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\Http\StreamResponse;
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
class GatewayController extends OCSController {
	public function __construct(
		IRequest $request,
		private IRootFolder $rootFolder,
		private LoggerInterface $logger,
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
	public function getFileContents(int $fileId, string $userId): DataResponse|StreamResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		try {
			$file = $this->rootFolder->getUserFolder($userId)->getFirstNodeById($fileId);
			// Not visible to this user and not existing at all deliberately give
			// the same answer, so the gateway cannot be used to probe for files
			// the user is not allowed to see.
			if (!$file || !$file instanceof File) {
				return new DataResponse(['error' => 'Node is not a file or could not be found.'], Http::STATUS_NOT_FOUND);
			}

			// The 'r' is the entire read only guarantee at this spot. It must
			// never become 'r+', 'w', 'a' or 'x'.
			$stream = $file->fopen('r');
			if (!$stream) {
				return new DataResponse(['error' => 'File could not be opened for reading.'], Http::STATUS_UNPROCESSABLE_ENTITY);
			}

			return new StreamResponse($stream);
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
