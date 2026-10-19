<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\App\IAppManager;

/**
 * Whether the full text search framework runs next to Findling (UMST-02).
 *
 * The framework registers a unified search provider of its own, so with one of
 * its apps enabled the same file can show up twice in the search bar: once in
 * the group of Findling and once in the group of fulltextsearch. The admin page
 * names that consequence and links the migration page while this method answers
 * true (PE-34-1, PE-34-2).
 *
 * Exactly the two apps that bring results into the search bar count. A
 * platform app such as fulltextsearch_elasticsearch, fulltextsearch_sql or
 * fulltextsearch_postgresql on its own adds nothing to the search bar, so it
 * does not raise the hint.
 *
 * The question is asked through isEnabledForAnyone and never through
 * isEnabledForUser: an app enabled for a group only is enabled for somebody,
 * and the admin who reads the page need not be in that group, so the user
 * bound question would miss exactly the instances that restrict the old apps
 * to a group (T-34-11). isInstalled is deprecated and says nothing about
 * enabled. The answer is one bool, nothing is logged and nothing is configured
 * (T-34-12); the app manager reads a value it caches per request, so the five
 * second poll of the page costs two lookups (T-34-13).
 */
final class ParallelSearchService {
	/** The app ids whose results reach the search bar. */
	public const APP_IDS = ['fulltextsearch', 'files_fulltextsearch'];

	public function __construct(
		private IAppManager $appManager,
	) {
	}

	/** True as soon as one app of APP_IDS is enabled for everyone or a group. */
	public function active(): bool {
		foreach (self::APP_IDS as $appId) {
			if ($this->appManager->isEnabledForAnyone($appId)) {
				return true;
			}
		}

		return false;
	}
}
