<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\AdminViewService;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\IRequest;
use OCP\IUserSession;
use Psr\Log\LoggerInterface;

/**
 * The four addresses the admin page asks, and the only four.
 *
 * One reads the whole page and is polled; one looks up a single file and is
 * asked when somebody types into a field; one previews what a new exclusion
 * would remove; one writes the rules. The first two are two routes and not one
 * with a parameter, because the first answers the same thing for every
 * administrator and the second answers about a string somebody wrote, and
 * folding the two together would put a user supplied path into the request that
 * refreshes the numbers every five seconds.
 *
 * The preview is a route of its own and a reading one, which is a decision worth
 * writing down: the form has to name the number of documents a new exclusion
 * takes out of the index BEFORE it writes anything, and a write route that
 * sometimes only previews would be exactly the route where somebody eventually
 * takes the wrong branch. So it is a GET, it touches nothing, and the writing
 * route stays a route that always writes.
 *
 * The fourth one is the only writing route of this phase, and like the other two
 * it lives under /apps/findling/ rather than in the OCS space. That is a
 * boundary and not a preference: the write allowlist of the read-only gate on
 * the Python side stands at exactly three entries with a test that says so, and
 * the clearing that a new exclusion causes is queued on this side through
 * SubtreeExpandJob (research pattern 9). So no fourth OCS write is needed and
 * none is added. The attribute name of these routes is deliberately written
 * only above the four methods themselves, because the anti vacuity clause of
 * backend/tests/test_php_trust_boundary.py counts the lines that mention it and
 * compares them against the number of routes it found: a mention in prose would
 * break that gate without a route having changed (pitfall 7).
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
 * The same absence is what protects the writing route, where it matters most
 * (T-04-45, T-04-46). Without the attribute that lifts the token check, a page
 * on another host cannot make the browser of a logged in administrator change
 * the indexing rules of the instance; without the one that lifts the admin
 * requirement, an ordinary user cannot either.
 *
 * What does *not* protect this page: the ADMIN access level of the container
 * route in backend/appinfo/info.xml. That check sits in the proxy path browser
 * to AppAPI to ExApp, and PublicFunctions::exAppRequest, which is the path this
 * app uses, never passes it. The access level stays declared over there as
 * defense in depth for a path this app does not walk; the effective protection
 * of the admin page is this controller.
 *
 * Only the last route writes, and it writes appconfig plus one job entry per
 * newly excluded subtree: the clearing of D-07 is planned in the background job
 * list of Nextcloud and never carried out inside this request. There is no code
 * path from this class into the index, and none into the file system at all.
 * The log follows the rule of the other controllers of this app: a static
 * sentence outwards, the exception in the exception field where Nextcloud
 * renders it under the admin's own log level, and never a path, a file name or a
 * library message. A refused rules form is counted in the log and its values are
 * not written out, because a folder name of a private instance arrives in
 * exactly that field (T-04-51).
 */
final class SettingsController extends Controller {
	/**
	 * The longest lookup reference this route accepts, in characters.
	 *
	 * Four thousand and ninety six, which is well above any path Nextcloud can
	 * hold and far below anything that costs this request memory. The point is
	 * not the number, it is that there is one: without a ceiling a single field
	 * on an administration page is a way of handing this app a megabyte to
	 * normalise, split and compare (T-04-44).
	 *
	 * Refused and not cut. A cut path names a different file, or a folder instead
	 * of a file, and answering about that would be worse than answering nothing.
	 */
	private const MAX_REFERENCE_LENGTH = 4096;

	public function __construct(
		IRequest $request,
		private AdminViewService $view,
		private SettingsService $settingsService,
		private ExclusionService $exclusionService,
		private IUserSession $userSession,
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

	/**
	 * GET /apps/findling/admin/diagnose
	 *
	 * One file, one state, one reason. The reference is a path or a numeric file
	 * id in the same parameter, which is D-04: an administrator who has a path
	 * does not want to look up an id first, and one who copied an id out of the
	 * error list does not want to build a path.
	 *
	 * Protected by the same absence of attributes as the route above, and that is
	 * the whole guard: without them SecurityMiddleware demands a logged in
	 * administrator and the request token of the session. This route reaches the
	 * file system of the instance through a string somebody typed, so it is the
	 * one on this page where that absence is worth reading twice.
	 *
	 * An empty or oversized reference is refused with a static sentence, and the
	 * value never reaches the log, in the same spirit as
	 * ReconcileController::badMount: what arrives in this field is a file name,
	 * and the log of this app carries counters and reason codes and never
	 * something somebody else wrote (T-04-38).
	 *
	 * A file that does not exist and a reference naming a user that does not
	 * exist give word for word the same answer, which is what keeps this field
	 * from becoming a way of asking which users an instance has.
	 */
	#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'GET', url: '/admin/diagnose')]
	public function diagnose(string $ref = ''): DataResponse {
		$reference = trim($ref);
		if ($reference === '' || strlen($reference) > self::MAX_REFERENCE_LENGTH) {
			$this->logger->warning('Findling: rejected a lookup without a usable reference');

			return new DataResponse(
				['error' => 'Malformed file reference.'],
				Http::STATUS_BAD_REQUEST,
			);
		}

		try {
			return new DataResponse($this->view->diagnose($reference, $this->userId()));
		} catch (\Throwable $e) {
			// The exception travels in the exception field, where Nextcloud
			// renders it under the admin's own log level, and the message of this
			// app stays a static sentence: the file system layer of Nextcloud
			// puts absolute paths into its exceptions, and this route is reached
			// with a path of any user on the instance.
			$this->logger->error('Findling: could not diagnose a single file', ['exception' => $e]);

			return new DataResponse(
				['error' => 'Lookup is not available.'],
				Http::STATUS_INTERNAL_SERVER_ERROR,
			);
		}
	}

	/**
	 * GET /apps/findling/admin/rules/preview
	 *
	 * What the list in the form would remove from the index, before anything is
	 * written. The answer is the prefixes of the list that are not in force yet,
	 * the number of indexed documents under them and whether that number ran into
	 * its ceiling; the page turns those three into the inline confirmation of D-07
	 * and shows the number with "at least" in front of it when the ceiling was
	 * reached.
	 *
	 * A reading route, and it writes nothing at all: no appconfig, no queue row,
	 * no job. That is why it is a GET and why it is separate from the write, see
	 * the class docblock.
	 *
	 * The new prefixes travel back, and they are the one value of this page that
	 * comes back the way somebody typed it, normalised. That is deliberate and it
	 * is narrow: the confirmation has to name the path whose content is about to
	 * leave the index, otherwise it asks an admin to confirm a consequence without
	 * naming what it applies to. The value came out of this same request, from the
	 * same admin session, and it goes into a text node on the page. It does not
	 * reach the log, for the reason the whole class follows (T-04-51).
	 *
	 * An invalid list is refused with the same codes the write uses rather than
	 * being previewed. A preview of a list that cannot be saved would be a number
	 * for a consequence that will not happen.
	 *
	 * @param list<mixed> $exclusions the prefix list as the form holds it
	 */
	#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'GET', url: '/admin/rules/preview')]
	public function previewRules(array $exclusions = []): DataResponse {
		$list = array_values($exclusions);

		$listErrors = $this->exclusionService->validate($list);
		if ($listErrors !== []) {
			$this->logger->warning('Findling: refused to preview a list of exclusions that did not validate', [
				'exclusions' => count($listErrors),
			]);

			return new DataResponse(
				['exclusions' => $listErrors, 'error' => 'The rules were not saved.'],
				Http::STATUS_BAD_REQUEST,
			);
		}

		try {
			$newPrefixes = $this->exclusionService->newPrefixes($list);
			$affected = $this->exclusionService->affectedDocuments($newPrefixes);

			return new DataResponse([
				'newPrefixes' => $newPrefixes,
				'affectedDocuments' => $affected,
				'capped' => $affected >= ExclusionService::PREVIEW_CAP,
			]);
		} catch (\Throwable $e) {
			// A failed preview may not block the save. The page falls back to the
			// confirmation without a number, which still names the path and still
			// says the files stay on disk, because the consequence is the same
			// whether or not this count succeeded.
			$this->logger->error('Findling: could not preview the effect of an exclusion', ['exception' => $e]);

			return new DataResponse(
				['error' => 'Preview is not available.'],
				Http::STATUS_INTERNAL_SERVER_ERROR,
			);
		}
	}

	/**
	 * POST /apps/findling/admin/rules
	 *
	 * The four switches of ADM-04 in one call, and the only writing route of this
	 * phase. All four travel together because they are one form: an admin presses
	 * one button, and a route per switch would make a half saved form a state this
	 * page can reach.
	 *
	 * Validated before anything is written, and refused as a whole. With one bad
	 * field NOTHING is written, so the page can say "nothing has changed" and mean
	 * it: a form that had saved the cap and refused the list would leave an
	 * administrator guessing which half held. The answer names the fields that
	 * failed, by field name and error code, and never by value.
	 *
	 * The two services validate again inside their own save(), which is not
	 * redundancy for its own sake: ``occ config:app:set findling ...`` is a second
	 * way into the same keys that never passes through this method.
	 *
	 * The answer carries the rules as they are in force AFTER the write, which is
	 * what lets the page show the clamped cap rather than the number that was
	 * typed. Clamping without saying so would be the page showing a value that
	 * does not hold, one screen further along than pitfall 2.
	 *
	 * The confirmation of D-07 is not asked for HERE, and that is not the same as
	 * not being asked at all. A new exclusion clears the documents under it out of
	 * the index, ExclusionService::save() plans that clearing, and the admin has
	 * to have seen the number before this route is called: the page previews it
	 * over the route above and only then posts here. The confirmation lives where
	 * the consequence is shown rather than in the request that carries it out,
	 * because a route that judged its own confirmation flag would trust a value
	 * from the same form it is judging.
	 *
	 * A prefix that is taken back triggers nothing here, deliberately. The
	 * comparison run picks those files up again by itself, which takes up to the
	 * latency AdminViewService::rules() reports, and the page names both the wait
	 * and the command that skips it.
	 *
	 * @param list<mixed> $exclusions the prefix list as the form holds it
	 */
	#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'POST', url: '/admin/rules')]
	public function saveRules(
		array $exclusions = [],
		int $maxFileBytes = 0,
		bool $indexTeamFolders = true,
		bool $indexExternalStorage = false,
	): DataResponse {
		$list = array_values($exclusions);

		$fieldErrors = $this->settingsService->validate([
			SettingsService::FIELD_MAX_FILE_BYTES => $maxFileBytes,
		]);
		$listErrors = $this->exclusionService->validate($list);

		if ($fieldErrors !== [] || $listErrors !== []) {
			// Counted, never quoted. What arrives in the list is a folder name of
			// a private instance, and the log of this app carries counters and
			// codes and nothing somebody else wrote.
			$this->logger->warning('Findling: refused a set of rules that did not validate', [
				'fields' => count($fieldErrors),
				'exclusions' => count($listErrors),
			]);

			return new DataResponse(
				[
					'saved' => false,
					'fields' => $fieldErrors,
					'exclusions' => $listErrors,
					'error' => 'The rules were not saved.',
				],
				Http::STATUS_BAD_REQUEST,
			);
		}

		try {
			$this->settingsService->save([
				SettingsService::FIELD_MAX_FILE_BYTES => $maxFileBytes,
				'indexTeamFolders' => $indexTeamFolders,
				'indexExternalStorage' => $indexExternalStorage,
			]);
			$this->exclusionService->save($list);
		} catch (\Throwable $e) {
			// The only way to get here is the database itself, because both
			// values were judged above. The page says nothing was saved, which
			// may understate a failure between the two writes; the honest part is
			// that appconfig is the whole of what either call touches, so the
			// worst case is one of two keys and the next save fixes it.
			$this->logger->error('Findling: could not save the rules', ['exception' => $e]);

			return new DataResponse(
				['saved' => false, 'error' => 'The rules could not be saved.'],
				Http::STATUS_INTERNAL_SERVER_ERROR,
			);
		}

		return new DataResponse([
			'saved' => true,
			'fields' => [],
			'exclusions' => [],
			'rules' => $this->view->rules(),
		]);
	}

	/**
	 * The identity the call to the container travels under.
	 *
	 * The session user, and this method is only ever reached from an admin
	 * session because the route above carries no attribute that would let anybody
	 * else in. An empty string is left empty rather than substituted with a fixed
	 * name, so that a call without a session fails in ExAppService, where the
	 * failure has a log line, instead of succeeding under an identity nobody
	 * chose.
	 */
	private function userId(): string {
		return $this->userSession->getUser()?->getUID() ?? '';
	}
}
