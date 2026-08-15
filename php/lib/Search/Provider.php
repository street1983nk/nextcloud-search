<?php

declare(strict_types=1);

namespace OCA\Findling\Search;

use OCA\Findling\Service\ExAppService;
use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\IUser;
use OCP\Search\IProvider;
use OCP\Search\ISearchQuery;
use OCP\Search\SearchResult;
use OCP\Search\SearchResultEntry;

/**
 * IProvider, deliberately not IExternalProvider. An external provider is a
 * provider that asks a third party, and the unified search dialog keeps those
 * switched off by default. That would break the zero-config promise on the
 * first search a user ever runs.
 */
final class Provider implements IProvider {
	public function __construct(
		private IL10N $l10n,
		private IURLGenerator $urlGenerator,
		private ExAppService $exApp,
	) {
	}

	#[\Override]
	public function getId(): string {
		return 'findling';
	}

	#[\Override]
	public function getName(): string {
		return $this->l10n->t('File contents');
	}

	/**
	 * Always an int, never a null. A null order hides the provider in the user
	 * interface and the search API is never called, which is indistinguishable
	 * from a registration that did not happen.
	 */
	#[\Override]
	public function getOrder(string $route, array $routeParameters): ?int {
		return str_starts_with($route, 'files.') ? -5 : 25;
	}

	#[\Override]
	public function search(IUser $user, ISearchQuery $query): SearchResult {
		$hits = $this->exApp->search($user->getUID(), $query->getTerm(), $query->getLimit());

		$entries = array_map(
			fn (array $hit): SearchResultEntry => new SearchResultEntry(
				thumbnailUrl: '',
				title: $hit['title'],
				// Plain text. The dialog interpolates the subline as text, so
				// any markup would be shown to the user verbatim.
				subline: $hit['snippet'],
				resourceUrl: $this->resourceUrl($hit['fileId']),
				icon: 'icon-search',
			),
			$hits,
		);

		return SearchResult::complete($this->getName(), $entries);
	}

	/**
	 * The walking skeleton answers with a hit that has no file behind it, and
	 * that hit carries the file id 0. Pointing it at the files list keeps the
	 * link from resolving to nothing.
	 */
	private function resourceUrl(int $fileId): string {
		if ($fileId <= 0) {
			return $this->urlGenerator->linkToRoute('files.view.index');
		}

		return $this->urlGenerator->linkToRoute('files.View.showFile', ['fileid' => $fileId]);
	}
}
