<?php

declare(strict_types=1);

namespace OCA\Findling\Settings;

use OCA\Findling\AppInfo\Application;
use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\Settings\IIconSection;

/**
 * The entry "Findling" in the administration navigation.
 *
 * IIconSection and not ISection: OCP\Settings\ISection does not exist in
 * Nextcloud 30 and later, and this app declares min-version 32, so the
 * interface an older tutorial names here cannot be implemented at all. The
 * four methods below are the whole of IIconSection, which inherits from
 * nothing.
 *
 * The Override attribute is deliberately absent from every method here, and
 * that is a decision and not an oversight. It is engine-checked from PHP 8.3
 * on, while php/appinfo/info.xml declares php min-version="8.2", so across the
 * version span this app supports the attribute is a promise the oldest instance
 * does not keep: on 8.2 it is parsed and ignored rather than enforced, so a
 * method that stopped overriding anything would be caught on 8.3 and pass in
 * silence on 8.2. It goes in once the floor is 8.3 and not before.
 *
 * php/lib/Search/Provider.php does carry it and stays untouched, for the same
 * reason in the other direction: it is harmless there, being ignored on 8.2 and
 * correct on 8.3. The asymmetry is named here so that nobody harmonises the two
 * sides on the strength of a guess about what the attribute does on 8.2. It is
 * not a parse error there, which an earlier version of this docblock claimed
 * (phase 4 finding IN-05).
 */
final class Section implements IIconSection {
	public function __construct(
		private IL10N $l,
		private IURLGenerator $url,
	) {
	}

	public function getID(): string {
		// This string is the address of the page as well: the section renders
		// under /settings/admin/findling and nowhere else.
		return Application::APP_ID;
	}

	public function getName(): string {
		// The one visible string of this class, and the only one in the whole
		// app that is identical in English and in German.
		return $this->l->t('Findling');
	}

	public function getPriority(): int {
		// Between 0 and 99, see the interface docblock. Seventy five puts the
		// section into the lower half of the list, where the sections of
		// installed apps belong, and not among the ones of the server itself.
		return 75;
	}

	public function getIcon(): string {
		// Themed by the navigation, which is why the file carries no colour of
		// its own. See THIRD-PARTY.md for where the path data comes from.
		return $this->url->imagePath(Application::APP_ID, 'app-dark.svg');
	}
}
