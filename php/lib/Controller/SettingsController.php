<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\AdminViewService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\IRequest;
use Psr\Log\LoggerInterface;

/**
 * The one address the admin page asks, and the only one.
 *
 * The class extends the plain Controller and not OCSController, so the route
 * lives under /apps/findling/ and stays outside the OCS space. That is a
 * deliberate boundary and not a preference: the write allowlist of the
 * read-only gate on the Python side stands at exactly three entries, and every
 * route added to the OCS space is a route that gate has to judge. A settings
 * page has no business widening a security gate.
 *
 * The protection of this route is what is *missing* from it, and the four
 * attribute names are deliberately not written out anywhere in this file so
 * that a grep for them over this class stays at zero. Without the attribute
 * that lifts the admin requirement, SecurityMiddleware::beforeController
 * demands a logged in administrator and throws NotAdminException otherwise.
 * Without the one that lifts the token check it demands the request token of
 * the session. Without the public marker it demands a session at all. And
 * without the external app marker no registered container reaches this route,
 * which is the direction that matters here: pointing that marker at an admin
 * page would lock the admin out and let every foreign container in. Less code
 * is the stricter variant, which is precisely why it is easy to weaken by
 * accident, and why backend/tests/test_php_trust_boundary.py judges an admin
 * route by the list of attributes it may never carry and names the four there.
 *
 * What does *not* protect this page: the ADMIN access level of the container
 * route in backend/appinfo/info.xml. That check sits in the proxy path browser
 * to AppAPI to ExApp, and PublicFunctions::exAppRequest, which is the path this
 * app uses, never passes it. The access level stays declared over there as
 * defense in depth for a path this app does not walk; the effective protection
 * of the admin page is this controller.
 *
 * Nothing here writes, and there is no code path from this class into the
 * queue, the state table or the file system. The log follows the rule of the
 * other controllers of this app: a static sentence outwards, the exception in
 * the exception field where Nextcloud renders it under the admin's own log
 * level, and never a path, a file name or a library message.
 */
final class SettingsController extends Controller {
	public function __construct(
		IRequest $request,
		private AdminViewService $view,
		private LoggerInterface $logger,
	) {
		parent::__construct(Application::APP_ID, $request);
	}

	/**
	 * GET /apps/findling/admin/overview
	 *
	 * Answers with the whole coverage structure of AdminViewService: the counts
	 * of this side, the work stock, the timestamp of the last background job,
	 * the derived run state and the view of the container under its own key,
	 * with a flag saying whether it answered.
	 *
	 * One address for the whole page, and that is the shape the design contract
	 * asks for: the browser polls a single route, and the merging of the two
	 * sources happens on this side where both are reachable. A page that asked
	 * the container directly would need a second credential, a second timeout
	 * and a second story about what happens when one of the two is silent.
	 *
	 * A failure answers 500 with a static sentence rather than a half filled
	 * structure. The script keeps the numbers it already shows and raises its
	 * banner, which is the honest reading of "this request did not work" and is
	 * never the same as "there is nothing indexed".
	 */
	#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'GET', url: '/admin/overview')]
	public function overview(): DataResponse {
		try {
			return new DataResponse($this->view->overview());
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not assemble the admin overview', ['exception' => $e]);

			return new DataResponse(
				['error' => 'Status is not available.'],
				Http::STATUS_INTERNAL_SERVER_ERROR,
			);
		}
	}
}
