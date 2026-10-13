<?php

declare(strict_types=1);

namespace OCA\Findling\Search;

use OCP\IUser;
use OCP\Search\IFilteringProvider;
use OCP\Search\ISearchQuery;
use OCP\Search\SearchResult;

/**
 * The provider the seven filter chips of Findling ask, and nobody else.
 *
 * Why a second provider at all (Befund A of plan 32-07). The unified search of
 * Nextcloud 33 to 35 treats every entry registered through
 * OCA.UnifiedSearch.registerFilterAction as a provider of its own: the modal
 * builds its provider list as [...providers, ...externalFilters], and a search
 * without a chip asks every entry of that list under
 * type: entry.searchFrom ?? entry.id, without the parameters of any chip. With
 * searchFrom 'findling' that was eight identical requests to the real provider
 * per search term, and seven groups named after the menu entries, each with
 * the same unfiltered hits. The entries now point at this provider instead, and
 * a request without types and without folder is exactly that chipless request:
 * it is answered with an empty group, without asking the backend, and the core
 * shows no group without a hit.
 *
 * Why the order is null. getProviders() of the SearchComposer leaves a provider
 * with a null order out of the list the dialog loads, so this one is no group of
 * its own and no entry of the menu. search() of the SearchComposer does not ask
 * the order, so the route /search/providers/findling-filter/search answers all
 * the same (stable33 to master, read on 2026-10-13).
 *
 * Everything else is the real provider. The filters are its filters, the name
 * of the group is its name, and a request with a chip parameter is handed to
 * Provider::search() as it came: the same SearchService, the same recheck, the
 * same rights. This class decides one thing, whether a request carries a chip,
 * and nothing about who may see what.
 *
 * A request that carries folder '/' is a chip: the root of the user folder was
 * chosen, and Provider::folderOf() reads it as no narrowing. The group appears
 * with the unfiltered hits, under the chip "File contents in /".
 */
final class FilterProvider implements IFilteringProvider {
	/**
	 * The id the filter entries of js/unified-search.js carry as searchFrom.
	 * Never 'findling', which is the real provider and stays the one group of a
	 * search without a chip.
	 */
	public const ID = 'findling-filter';

	public function __construct(
		private Provider $provider,
	) {
	}

	#[\Override]
	public function getId(): string {
		return self::ID;
	}

	#[\Override]
	public function getName(): string {
		return $this->provider->getName();
	}

	/**
	 * Always null: hidden from the provider list of the dialog, so neither a
	 * group of its own nor an entry of the menu. The route still answers.
	 */
	#[\Override]
	public function getOrder(string $route, array $routeParameters): ?int {
		return null;
	}

	/**
	 * The filters of the real provider, word for word. The core checks the
	 * filters of a request against the provider the request names, so a chip
	 * parameter this list lacked would cost the chip its group (HTTP 400).
	 *
	 * @return list<string>
	 */
	#[\Override]
	public function getSupportedFilters(): array {
		return $this->provider->getSupportedFilters();
	}

	/**
	 * @return list<string>
	 */
	#[\Override]
	public function getAlternateIds(): array {
		return [];
	}

	/**
	 * The definitions of types and folder, again those of the real provider.
	 * The core keeps a custom definition under the id of the provider that
	 * declared it, so this provider has to declare them itself: without them
	 * the names would be unknown here and dropped from every chip request.
	 *
	 * @return list<\OCP\Search\FilterDefinition>
	 */
	#[\Override]
	public function getCustomFilters(): array {
		return $this->provider->getCustomFilters();
	}

	#[\Override]
	public function search(IUser $user, ISearchQuery $query): SearchResult {
		// No chip parameter: the request the core sends for a menu entry while
		// no chip is set. Answered with nothing and without a backend call.
		if ($query->getFilter(Provider::FILTER_TYPES) === null && $query->getFilter(Provider::FILTER_FOLDER) === null) {
			return SearchResult::complete($this->getName(), []);
		}

		return $this->provider->search($user, $query);
	}
}
