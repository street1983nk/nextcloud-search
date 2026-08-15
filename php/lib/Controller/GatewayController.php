<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\Attribute\ApiRoute;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
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
	 * CSRF does not apply. It is spelled out fully qualified so that the file
	 * carries exactly one occurrence of it and a grep gate stays meaningful,
	 * the same way the read only fopen mode is gated.
	 *
	 * The file id is an int and there is no path string anywhere in this
	 * signature, so path traversal is structurally impossible rather than
	 * filtered.
	 */
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[NoCSRFRequired]
	#[ApiRoute(verb: 'GET', url: '/files/{fileId}')]
	public function getFileContents(int $fileId, string $userId): DataResponse|StreamResponse {
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
		} catch (\Throwable $e) {
			// The message of the exception only, never any file content.
			$this->logger->error('Findling: unknown error reading a file: ' . $e->getMessage(), ['exception' => $e]);
			return new DataResponse(['error' => 'Unknown error occurred.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}
	}
}
