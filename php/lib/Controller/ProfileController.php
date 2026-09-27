<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;
use Psr\Log\LoggerInterface;

/**
 * The performance profile, handed to the container on request (D-24-01, path B).
 *
 * The container asks once per round and nothing pushes, the same backpressure
 * rule the queue follows. One route, reading only, and the answer carries the
 * profile name and nothing else. The value lives in appconfig of this app and is
 * validated by SettingsService::profile(), so the container only ever sees a
 * name out of the closed set.
 *
 * This is a companion change and travels with release 1.4.0. A 1.3 companion
 * without this route is an expected state: the container treats the missing
 * route as "not readable" and keeps running on its own default (D-24-02).
 *
 * The attribute trio is written fully qualified, in the spelling of
 * ReconcileController, because a grep gate counts it that way. The CSRF
 * exemption is not a weakening: the credential is the signed AppAPI header and
 * no session is involved.
 */
class ProfileController extends OCSController {
	public function __construct(
		IRequest $request,
		private SettingsService $settingsService,
		private LoggerInterface $logger,
	) {
		parent::__construct(Application::APP_ID, $request);
	}

	/**
	 * GET /ocs/v2.php/apps/findling/profile
	 *
	 * Answers with {"profile": "economy" | "standard" | "performance"}. A failure
	 * to read answers with the default instead of an error, because the frugal
	 * profile is the safe one on every box and an error would only make the
	 * container fall back to the same value one step later.
	 */
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'GET', url: '/profile')]
	public function profile(): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		try {
			return new DataResponse(['profile' => $this->settingsService->profile()]);
		} catch (\Throwable $e) {
			// A static sentence; the exception travels in its own field, which
			// Nextcloud renders under the admin's log level. The stored value is
			// never part of the log.
			$this->logger->error('Findling: the profile could not be read', ['exception' => $e]);

			return new DataResponse(['profile' => SettingsService::PROFILE_DEFAULT]);
		}
	}

	/**
	 * ExAppRequired answers "is this a registered external app", not "is this
	 * our external app". Without this comparison any other backend on the
	 * instance could read the profile. A copy of the guard in
	 * ReconcileController rather than a shared trait, the smallest change to
	 * released code; the same residual trust in AppAPI applies.
	 */
	private function rejectForeignCaller(): ?DataResponse {
		$callerAppId = $this->request->getHeader('EX-APP-ID');
		if ($callerAppId === Application::BACKEND_APP_ID) {
			return null;
		}

		$this->logger->warning('Findling: profile called by a foreign ExApp', ['app' => $callerAppId]);

		return new DataResponse(
			['error' => 'This route is reserved for the Findling backend.'],
			Http::STATUS_FORBIDDEN,
		);
	}
}
