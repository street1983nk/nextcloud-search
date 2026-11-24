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
final class ProfileController extends OCSController {
	/**
	 * The generation of the verdict vocabulary this companion stores (K6).
	 *
	 * 2 means: this companion knows system_file, legacy_format and
	 * unsupported_variant under skipped (release 1.4.0). 3 means: also
	 * archive_limit and blocked_malicious, and the formats of 1.5 (mail, ZIP,
	 * .doc, .xls, HEIC) (D-31-03, D-31-08, D-36-03). blocked_malicious joins 3
	 * without a new generation, because 1.5.0 has not reached anyone yet. 4
	 * means: also failed(policy_blocked), a file a rule keeps from every user
	 * asked (release 1.7.0, issue #59). A container may send a code only to a
	 * companion that
	 * announces a generation which knows it, because QueueController refuses
	 * the whole failure or skip list with a 400 as soon as one code in it is
	 * unknown. A 1.3 companion sends no such field, and the container then maps
	 * the codes onto older ones on the wire; a 1.5 container still treats 2 as
	 * known and maps only archive_limit and blocked_malicious for it, and a 1.7
	 * container sends policy_blocked as gateway_error to a companion of 3 or
	 * less.
	 *
	 * It travels as "verdictsMax" since R-45-21-14 (plan 45-21), not as
	 * "verdicts": see VERDICTS_COMPATIBLE.
	 */
	public const VERDICTS_GENERATION = 4;

	/**
	 * The generation sent as "verdicts", for a container that predates
	 * "verdictsMax" (R-45-21-14, plan 45-21).
	 *
	 * An app store update often brings this companion before its container. A
	 * 1.6.x container knows the generations 2 and 3 and reads any other value
	 * of "verdicts" as no signal (backend/src/findling/nc/queue.py of v1.6.5,
	 * lines 148 and 219 to 227): it would send the codes of 1.4 and 1.5 as their
	 * substitutes of 1.3, which this companion stores as false reasons, and it
	 * would skip its re-check and catch-up. 3 is the highest generation such a
	 * container knows, and this companion stores every code of it. A 1.7
	 * container reads both fields and takes the highest generation it knows.
	 * Stays 3 for good; a later generation goes into VERDICTS_GENERATION only.
	 */
	public const VERDICTS_COMPATIBLE = 3;

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
	 * "verdicts": 3, "verdictsMax": 4, "paused": bool}. verdictsMax is the
	 * constant VERDICTS_GENERATION, the capability signal for the skipped codes
	 * of releases 1.4.0 and 1.5.0 and the failed code policy_blocked of release
	 * 1.7.0 (K6); verdicts is VERDICTS_COMPATIBLE, the generation an older
	 * container reads right (R-45-21-14).
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
	 *
	 * Since 1.6.2 the answer also carries "paused", the backup pause wish of
	 * issue #37 (SettingsService::paused()); the container reads it on every
	 * round, and a missing field of an older companion means "not paused".
	 * It is read in the same try, so a failed read never answers "not paused".
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
				'verdicts' => self::VERDICTS_COMPATIBLE,
				'verdictsMax' => self::VERDICTS_GENERATION,
				'paused' => $this->settingsService->paused(),
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
