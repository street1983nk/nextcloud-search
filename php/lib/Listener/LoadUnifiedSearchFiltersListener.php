<?php

declare(strict_types=1);

namespace OCA\Findling\Listener;

use OCA\Findling\AppInfo\Application;
use OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Util;

/**
 * Puts the seven filter entries of Findling into the menu of the unified search.
 *
 * **Why a script at all.** A custom filter a provider declares through
 * getCustomFilters() has no surface in the unified search of Nextcloud 33 to 35:
 * the modal renders its own three filters (places or type, date, person) and
 * nothing else. The only way an app gets a visible entry into that menu is the
 * frontend plugin API OCA.UnifiedSearch.registerFilterAction, which is what the
 * Files app uses for its "In folder" entry. js/unified-search.js registers six
 * type entries and one folder entry there and hands their values to the chip of
 * the Findling provider; the server half (the filters types and folder) is in
 * Search\Provider.
 *
 * **Why every page and not the search plugin event of the Files app.** The
 * unified search opens from the header of every page, not only from Files. The
 * Files app loads its own plugin through LoadSearchPlugins, which only its own
 * view dispatches, so an entry hung on that event would exist in Files and be
 * missing everywhere else. BeforeTemplateRenderedEvent is dispatched for every
 * TemplateResponse, which is every page with a header.
 *
 * **Why only for a logged in user.** The login page and a public share link
 * render templates too, and neither of them has a unified search that would ask
 * Findling: the provider answers logged in users only. Loading the script there
 * would be a request for nothing.
 *
 * **Why the translations explicitly.** On a page of another app the catalogue of
 * findling is not loaded, and t('findling', ...) would show the English source
 * strings. addScript() pulls the catalogue in on the servers this app supports
 * as a side effect; the explicit call states the dependency instead of relying
 * on it.
 *
 * **What this listener must never become.** It runs on every page view of every
 * user. No database query, no call into the container, no file system access and
 * no service from the container: two static calls that add two entries to the
 * page head and nothing else. The script itself checks for every API it touches
 * and does nothing where one is missing (the legacy search, a future core), so a
 * page never breaks because of it.
 *
 * @template-implements IEventListener<Event>
 */
class LoadUnifiedSearchFiltersListener implements IEventListener {
	/** The script under php/js, without the extension, as Util::addScript wants it. */
	public const SCRIPT = 'unified-search';

	public function handle(Event $event): void {
		if (!$event instanceof BeforeTemplateRenderedEvent || !$event->isLoggedIn()) {
			return;
		}

		Util::addScript(Application::APP_ID, self::SCRIPT);
		Util::addTranslations(Application::APP_ID);
	}
}
