<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\ProbeService;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\IRequest;
use OCP\IUserSession;
use Psr\Log\LoggerInterface;

/**
 * The three addresses of the profile choice on the admin page (PRUEF-01,
 * UI-01): start a probe, read its state, and store a way down.
 *
 * None of them takes a verdict from the browser. A profile that needs the
 * probe is stored only by ProbeService, once the container reported "fits"
 * for the probe this side started (D-27-08). The one route that stores
 * directly stores only the ways down of D-27-09, decided on this side by
 * SettingsService::isDownward(); everything else is answered with
 * probe_required and writes nothing (D-27-11).
 *
 * Like SettingsController, the class extends the plain Controller, so the
 * routes live under /apps/findling/ and outside the OCS space, and their
 * protection is what is missing from them: none of the attributes that lift
 * the admin requirement, the token check, the session or point the route at
 * registered containers. SecurityMiddleware therefore demands a logged in
 * administrator and the request token of the session, for the reading route
 * as well, because the middleware makes no exception for a verb. That is why
 * the reading route may carry out the idempotent take-over. The attribute
 * name of the routes is written only above the three methods, because
 * backend/tests/test_php_trust_boundary.py counts the lines that mention it.
 *
 * Refusals are counted in the log and never quoted.
 */
final class ProfileSettingsController extends Controller {
	/** Profiles a probe may target with fp32 (D-25-01). */
	private const FP32_PROFILES = ['standard', 'performance'];

	/** Counter of refused inputs, for the log line. */
	private int $refused = 0;

	public function __construct(
		IRequest $request,
		private ProbeService $probeService,
		private SettingsService $settingsService,
		private IUserSession $userSession,
		private LoggerInterface $logger,
	) {
		parent::__construct(Application::APP_ID, $request);
	}

	/**
	 * POST /apps/findling/admin/profile/check
	 *
	 * Starts a probe for a target that needs one. A target outside the closed
	 * sets, fp32 below standard, or a target that needs no probe is invalid:
	 * the page stores a way down through the route below.
	 */
	#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'POST', url: '/admin/profile/check')]
	public function startCheck(string $profile = '', string $precision = ''): DataResponse {
		if (!$this->validTarget($profile, $precision) || !$this->settingsService->needsProbe($profile, $precision)) {
			$this->refuse();

			return new DataResponse(['started' => false, 'code' => ProbeService::START_INVALID], Http::STATUS_BAD_REQUEST);
		}

		return new DataResponse($this->probeService->start($profile, $precision, $this->userId()));
	}

	/**
	 * GET /apps/findling/admin/profile/check
	 *
	 * The state of the probe and the last result, after the take-over.
	 */
	#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'GET', url: '/admin/profile/check')]
	public function checkState(): DataResponse {
		return new DataResponse($this->probeService->state($this->userId()));
	}

	/**
	 * POST /apps/findling/admin/profile
	 *
	 * Stores a way down without a probe, and nothing else. "Stay at economy"
	 * stores economy even when economy is already in force, so the choice is
	 * on record (D-27-11).
	 */
	#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'POST', url: '/admin/profile')]
	public function saveProfile(string $profile = '', string $precision = ''): DataResponse {
		if (!in_array($profile, SettingsService::PROFILES, true) || !in_array($precision, SettingsService::PRECISIONS, true)) {
			$this->refuse();

			return new DataResponse(['saved' => false, 'code' => 'invalid'], Http::STATUS_BAD_REQUEST);
		}

		// fp32 next to economy only as the precision already stored (D-25-10).
		if ($precision === 'fp32' && !in_array($profile, self::FP32_PROFILES, true) && $this->settingsService->modelPrecision() !== 'fp32') {
			$this->refuse();

			return new DataResponse(['saved' => false, 'code' => 'invalid'], Http::STATUS_BAD_REQUEST);
		}

		if (!$this->settingsService->isDownward($profile, $precision)) {
			$this->refuse();

			return new DataResponse(['saved' => false, 'code' => 'probe_required'], Http::STATUS_BAD_REQUEST);
		}

		if (!$this->settingsService->saveProfile($profile, $precision)) {
			return new DataResponse(['saved' => false, 'code' => 'failed'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}

		return new DataResponse(['saved' => true, 'code' => 'saved']);
	}

	/** Closed sets, strict, and fp32 only as the target above economy. */
	private function validTarget(string $profile, string $precision): bool {
		if (!in_array($profile, SettingsService::PROFILES, true) || !in_array($precision, SettingsService::PRECISIONS, true)) {
			return false;
		}

		return $precision !== 'fp32' || in_array($profile, self::FP32_PROFILES, true);
	}

	/** A refused input, counted and never quoted. */
	private function refuse(): void {
		$this->refused++;
		$this->logger->warning('Findling: refused a profile request', ['refused' => $this->refused]);
	}

	/**
	 * The identity the call to the container travels under, the session
	 * user; empty stays empty so that ExAppService fails with a log line.
	 */
	private function userId(): string {
		return $this->userSession->getUser()?->getUID() ?? '';
	}
}
