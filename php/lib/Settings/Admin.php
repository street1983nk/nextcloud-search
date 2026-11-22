<?php

declare(strict_types=1);

namespace OCA\Findling\Settings;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\AdminViewService;
use OCA\Findling\Service\ExternalMountService;
use OCA\Findling\Service\ProbeService;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Services\IInitialState;
use OCP\IUserSession;
use OCP\Settings\ISettings;
use Psr\Log\LoggerInterface;

/**
 * The form of the section, which is the whole admin page of this app.
 *
 * The numbers are handed over twice on purpose, and the duplication is the
 * feature: the initial state is the short cut for the script, and the template
 * parameters are what makes the page readable without any script at all. The
 * UI contract of this phase demands that block one is fully legible with
 * JavaScript switched off, so the server has to render the real values, not a
 * placeholder that a fetch fills in later.
 *
 * The initial state carries numbers, booleans and reason codes and nothing
 * else. Every label is translated in the template, which is why the question
 * whether base64 and atob survive an umlaut never comes up: the payload is
 * plain ASCII because there is no prose in it.
 *
 * The Override attribute is absent here as well, for the reason written out in
 * Section: it is PHP 8.3 and this app supports PHP 8.2.
 *
 * The list of external storage an admin set up (EXCL-04, plan 45-03) is the
 * one exception to the duplication: it goes into the template parameters as
 * externalMounts and never into the initial state. It can be long, its mount
 * points are data of the instance that only the rendered form for an admin
 * needs, and the initial state is the shape the poll of five seconds keeps
 * refreshing, which has no use for a list that only changes when an admin
 * sets up a storage. The script reads the ids out of the rendered rows; the
 * rules in the initial state carry the excluded ids only (T-45-12).
 */
final class Admin implements ISettings {
	public function __construct(
		private IInitialState $initialState,
		private AdminViewService $view,
		private ProbeService $probeService,
		private ExternalMountService $externalMountService,
		private IUserSession $userSession,
		private LoggerInterface $logger,
	) {
	}

	public function getForm(): TemplateResponse {
		// A probe that finished while no tab was open is taken over before the
		// page renders, so a closed tab never loses a "fits" (D-27-04). The
		// take-over is idempotent, and a failure in it must not break the page.
		try {
			$this->probeService->settle($this->userSession->getUser()?->getUID() ?? '');
		} catch (\Throwable $e) {
			$this->logger->warning('Findling: could not take a probe result over', ['exception' => $e]);
		}

		// One aggregation, two consumers. Asking the service twice would let
		// the rendered page and the script disagree about the same moment.
		$overview = $this->view->overview();

		$this->initialState->provideInitialState('bootstrap', $overview);

		// RENDER_AS_BLANK renders the form body alone; the settings page
		// supplies the navigation, the heading area and the frame. Any other
		// mode produces a page inside a page.
		return new TemplateResponse(
			Application::APP_ID,
			'admin',
			$overview + ['externalMounts' => $this->externalMounts()],
			TemplateResponse::RENDER_AS_BLANK,
		);
	}

	/**
	 * The admin mounts for the storage selection, or an empty, switched off
	 * list when reading them failed. A failure here must not break the page,
	 * the same rule as the probe take-over above; the warning carries a
	 * counter and no value, because a message of the failure could name a
	 * mount point (T-04-51).
	 *
	 * @return array{enabled: bool, mounts: list<array{id: int, mountPoint: string, backend: string, duplicate: bool}>}
	 */
	private function externalMounts(): array {
		try {
			return [
				'enabled' => $this->externalMountService->enabled(),
				'mounts' => $this->externalMountService->adminMounts(),
			];
		} catch (\Throwable) {
			$this->logger->warning('Findling: could not list the external storage for the admin page', ['failed' => 1]);

			return ['enabled' => false, 'mounts' => []];
		}
	}

	public function getSection(): ?string {
		return Application::APP_ID;
	}

	public function getPriority(): int {
		// Between 0 and 100, see the interface docblock. This is the only form
		// in the section, so the value only matters the day a second one joins.
		return 50;
	}
}
