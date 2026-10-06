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
 * profile name, the model precision and, since phase 26, the confirmation
 * token of the admin (D-26-04, SettingsService::profileConfirmed()) and
 * nothing else. The first two values live in
 * appconfig of this app under keys of their own and are validated by
 * SettingsService::profile() and SettingsService::modelPrecision(), so the
 * container only ever sees names out of the two closed sets, or null for a
 * precision that is not one (D-25-02, D-25-03). One request per round carries
 * both, so the precision needs no second polling path (D-24-01).
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
	/**
	 * The generation of the verdict vocabulary this companion stores (K6).
	 *
	 * 2 means: this companion knows system_file, legacy_format and
	 * unsupported_variant under skipped. A container may send those three codes
	 * only to a companion that announces this value, because
	 * QueueController refuses the whole failure or skip list with a 400 as soon
	 * as one code in it is unknown. A 1.3 companion sends no such field, and
	 * the container then maps the three codes onto older ones on the wire.
	 */
	public const VERDICTS_GENERATION = 2;

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
	 * Answers with {"profile": "economy" | "standard" | "performance",
	 * "precision": "int8" | "fp32" | null, "confirmed": "<32 hex>" | null,
	 * "verdicts": 2}. verdicts is the constant VERDICTS_GENERATION, the
	 * capability signal for the three skipped codes of release 1.4.0 (K6).
	 * null is a stored precision outside the set; the container keeps its last
	 * known precision on it rather than reindexing for a typo. confirmed is the
	 * token the admin stored to lift a lowering of the memory guard (D-26-04),
	 * null when none is stored or the stored one is not 32 lowercase hex. A 1.3
	 * container reads only the profile field and ignores the other two. A
	 * failure to read answers as a failure (500 with an error field and neither
	 * a profile nor a precision name),
	 * because the container's rule for a failed read is to keep the LAST KNOWN
	 * profile (D-24-02). A valid-looking default here would downgrade a running
	 * standard or performance box to economy for at least one polling round.
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
			return new DataResponse([
				'profile' => $this->settingsService->profile(),
				'precision' => $this->settingsService->modelPrecision(),
				'confirmed' => $this->settingsService->profileConfirmed(),
				'verdicts' => self::VERDICTS_GENERATION,
			]);
		} catch (\Throwable $e) {
			// A static sentence; the exception travels in its own field, which
			// Nextcloud renders under the admin's log level. The stored value is
			// never part of the log. The answer carries no profile name: the
			// container turns the 500 into "not readable" and keeps the last
			// known profile (D-24-02).
			$this->logger->error('Findling: the profile could not be read', ['exception' => $e]);

			return new DataResponse(['error' => 'profile unreadable'], Http::STATUS_INTERNAL_SERVER_ERROR);
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
