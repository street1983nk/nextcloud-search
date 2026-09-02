<?php

declare(strict_types=1);

namespace OCA\Findling\Settings;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\AdminViewService;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Services\IInitialState;
use OCP\Settings\ISettings;

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
 */
final class Admin implements ISettings {
	public function __construct(
		private IInitialState $initialState,
		private AdminViewService $view,
	) {
	}

	public function getForm(): TemplateResponse {
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
			$overview,
			TemplateResponse::RENDER_AS_BLANK,
		);
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
