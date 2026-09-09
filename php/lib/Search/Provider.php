<?php

declare(strict_types=1);

namespace OCA\Findling\Search;

use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\SearchCaps;
use OCA\Findling\Service\SearchService;
use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\IUser;
use OCP\Search\IFilter;
use OCP\Search\IFilteringProvider;
use OCP\Search\ISearchQuery;
use OCP\Search\SearchResult;
use OCP\Search\SearchResultEntry;
use Psr\Log\LoggerInterface;

/**
 * The search provider of the unified search dialog, and since plan 09-03 it
 * decides nothing.
 *
 * Three jobs are left and they are all translations. It turns an ISearchQuery
 * into the language of the shared service, it writes out the ceilings the
 * dialog wants, and it renders what comes back into SearchResultEntry. Who may
 * see a file is answered in OCA\Findling\Service\SearchService and nowhere
 * else, because the own result page of phase 9 asks the same question and two
 * answers to one question are one answer too many (UI-03).
 *
 * IFilteringProvider rather than plain IProvider, and deliberately not
 * IExternalProvider: an external provider is a provider that asks a third
 * party, and the unified search dialog keeps those switched off by default.
 * That would break the zero-config promise on the first search a user ever
 * runs.
 *
 * The whole group runs against a wall clock of two and a half seconds. The
 * unified search asks every provider and waits for all of them, so a slow
 * provider does not cost its own result group, it costs the search. That is
 * also why this caller stays the impatient one of the two: its per call ceiling
 * is the unchanged ExAppService::REQUEST_TIMEOUT_SECONDS, while the result page
 * waits for nobody and may name a larger one of its own.
 *
 * Since phase 5 there is one more way for this group to be empty, and it is a
 * decision rather than a failure. When the two halves of this app report
 * versions whose major or minor disagree, the search answers with nothing at
 * all: the protocol between them is what a hit is built out of, so a hit across
 * a version break would be a guess presented as a finding (D-11). The state is
 * named on the admin page with both version numbers, and this class only
 * declines.
 */
final class Provider implements IFilteringProvider {
	/**
	 * The wall clock for one result group, in seconds.
	 *
	 * The number is unchanged since plan 05-16 and only its unit moved: the
	 * conversion into the nanoseconds of hrtime() now happens in the shared
	 * service, together with the clock it is compared against. hrtime() and not
	 * microtime() stays the rule over there, because a clock adjustment during
	 * a search would otherwise either double the budget or end it immediately.
	 */
	private const BUDGET_SECONDS = 2.5;

	/**
	 * At most three rounds of asking, each with four times the display limit.
	 * The recheck can drop enough candidates that too few are left, so asking
	 * again is necessary; asking without a limit is the failure mode that makes
	 * query time permission filtering unusable.
	 */
	private const MAX_ROUNDS = 3;
	private const OVERFETCH = 4;

	/**
	 * The ceiling on node resolutions per search, and the arithmetic that
	 * forces it.
	 *
	 * Every resolution in the shared service is a query against oc_filecache.
	 * With a limit of 20, an overfetch of four and three rounds there would be
	 * up to 240 of them in a single search, and on a small box the time budget
	 * is gone before the first excerpt has even been requested. Two per
	 * displayed hit leaves room for a user whose candidates are mostly revoked
	 * shares, and the absolute ceiling keeps a large limit from reopening the
	 * same hole.
	 *
	 * What is capped is how many candidates are examined. Whether a displayed
	 * hit was examined is not capped and cannot be: the service stops
	 * approving, it never approves without asking.
	 */
	private const MAX_RECHECKS_PER_HIT = 2;
	private const MAX_RECHECKS_ABSOLUTE = 64;

	public function __construct(
		private IL10N $l10n,
		private IURLGenerator $urlGenerator,
		private SearchService $searchService,
		private LoggerInterface $logger,
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

	/**
	 * The filters this provider understands, and the list has to be complete
	 * rather than sparse.
	 *
	 * A provider is skipped without a word when a client sends a filter it does
	 * not declare, and a skipped provider looks exactly like a broken backend:
	 * no error, no entry, no hint. The built in title-only filter is our
	 * "file name instead of content", and term is the search term itself.
	 *
	 * @return list<string>
	 */
	#[\Override]
	public function getSupportedFilters(): array {
		return [IFilter::BUILTIN_TERM, IFilter::BUILTIN_TITLE_ONLY];
	}

	/**
	 * No second id triggers this provider, and it defines no filter of its own.
	 * A custom filter would have to be registered with a definition, and a name
	 * without one turns the whole provider list into an error.
	 *
	 * @return list<string>
	 */
	#[\Override]
	public function getAlternateIds(): array {
		return [];
	}

	/**
	 * @return list<\OCP\Search\FilterDefinition>
	 */
	#[\Override]
	public function getCustomFilters(): array {
		return [];
	}

	#[\Override]
	public function search(IUser $user, ISearchQuery $query): SearchResult {
		$term = trim($query->getTerm());

		// An empty search line is not asked about at all. It is what the dialog
		// sends while the user is still typing, and it cannot produce a hit.
		if ($term === '') {
			return SearchResult::complete($this->getName(), []);
		}

		$titleOnly = $this->titleOnly($query);

		$outcome = $this->searchService->run(
			$user,
			$term,
			$titleOnly,
			$this->startOffset($query),
			$this->caps(max(1, $query->getLimit())),
		);

		if ($outcome->hits === []) {
			if ($outcome->failure !== null) {
				// One line and no more. The four reasons are a closed set of
				// constants and never user content, and the two that an admin
				// can act on have already been logged with their detail inside
				// the service; this is the trace that says which of them ended
				// this particular group.
				$this->logger->debug('Findling: the shared search returned no hits', ['reason' => $outcome->failure]);
			}

			return SearchResult::complete($this->getName(), []);
		}

		$entries = $this->toEntries($outcome->hits, $outcome->excerpts);

		// The way out of the dialog and onto the own page, and it is offered at
		// exactly one moment: when there is more behind this group than the
		// dialog shows. A complete group adds nothing by sending somebody to a
		// page that would show the same hits again, and a group without a single
		// approved hit has already left this method above.
		//
		// It is appended after the entries are built, so it never counts against
		// the limit the dialog asked for, and the answer stays the paginated one
		// so that the cursor semantics of the dialog are untouched.
		//
		// Knowingly accepted: NC 33 and 34 show their own "load more" button when
		// the number of results equals the limit, so the extra entry replaces
		// that button with this one. That is the direction of this phase, one way
		// of paging rather than two, and the page is the one that survives a
		// bookmark.
		if ($outcome->hasMore && $entries !== []) {
			$entries[] = $this->entryPoint($term, $titleOnly);
		}

		// A run that hit the paging ceiling is complete() with the hits it has,
		// and that is the honest shape rather than a concession: complete()
		// means "there is no next page from here", which is exactly what a
		// cursor the container refuses amounts to. The result page of this
		// phase says the same thing in a sentence, because it has room for one.
		return $outcome->hasMore
			? SearchResult::paginated($this->getName(), $entries, $outcome->nextCursor)
			: SearchResult::complete($this->getName(), $entries);
	}

	/**
	 * The ceilings of a dialog search, written out rather than defaulted.
	 *
	 * Every number here belongs to the dialog and to no other caller. The page
	 * size is what the dialog asked for, the four caps are the constants above,
	 * and the per call ceiling is the unchanged one of ExAppService: the unified
	 * search waits for every provider in parallel, so this caller is the
	 * impatient one and stays it.
	 */
	private function caps(int $limit): SearchCaps {
		return new SearchCaps(
			$limit,
			self::MAX_ROUNDS,
			self::OVERFETCH,
			self::MAX_RECHECKS_PER_HIT,
			self::MAX_RECHECKS_ABSOLUTE,
			self::BUDGET_SECONDS,
			ExAppService::REQUEST_TIMEOUT_SECONDS,
		);
	}

	/**
	 * "File name instead of content", the built in filter of the dialog. The
	 * value of a boolean filter is a bool, so anything else is a defect over
	 * there and is read as "not set".
	 */
	private function titleOnly(ISearchQuery $query): bool {
		$filter = $query->getFilter(IFilter::BUILTIN_TITLE_ONLY);

		return $filter !== null && $filter->get() === true;
	}

	/**
	 * Where the next page starts. The dialog hands back the cursor of the
	 * previous answer, which is the offset the container asked us to continue
	 * from. Anything that is not a plain number starts over at the top.
	 */
	private function startOffset(ISearchQuery $query): int {
		$cursor = $query->getCursor();
		if (is_int($cursor) && $cursor > 0) {
			return $cursor;
		}

		if (is_string($cursor) && ctype_digit($cursor)) {
			return (int)$cursor;
		}

		return 0;
	}

	/**
	 * Rendering, and nothing else. Everything in here has passed the recheck.
	 *
	 * The subline stays plain text. The dialog interpolates it as text, so any
	 * markup would be shown to the user verbatim; the highlight ranges
	 * therefore travel as character offsets in the attributes and are never
	 * translated into tags here.
	 *
	 * @param list<\OCA\Findling\Service\ApprovedHit> $approved
	 * @param array<int,array{text:string,highlights:list<array{int,int}>}> $excerpts
	 * @return list<SearchResultEntry>
	 */
	private function toEntries(array $approved, array $excerpts): array {
		$entries = [];

		foreach ($approved as $hit) {
			$fileId = $hit->fileId;
			$excerpt = $excerpts[$fileId] ?? null;

			$entry = new SearchResultEntry(
				thumbnailUrl: '',
				title: $hit->title,
				subline: $excerpt === null ? $hit->path : $excerpt['text'],
				resourceUrl: $this->resourceUrl($fileId),
				icon: 'icon-search',
			);
			$entry->addAttribute('fileId', (string)$fileId);

			if ($excerpt !== null && $excerpt['highlights'] !== []) {
				$encoded = json_encode($excerpt['highlights']);
				if (is_string($encoded)) {
					$entry->addAttribute('highlights', $encoded);
				}
			}

			$entries[] = $entry;
		}

		return $entries;
	}

	/**
	 * The last entry of the group, which is not a hit but a door.
	 *
	 * The address carries the term and, if it was set, the built in filter, and
	 * nothing else: no page and no cursor path, because the way in is always page
	 * one. Parameters that are not a placeholder of the route are appended as a
	 * query string by the url generator, which is what the page reads.
	 */
	private function entryPoint(string $term, bool $titleOnly): SearchResultEntry {
		$entry = new SearchResultEntry(
			thumbnailUrl: '',
			title: $this->l10n->t('Show all results'),
			subline: $this->l10n->t('Opens the Findling results page'),
			resourceUrl: $this->urlGenerator->linkToRoute(
				'findling.page.index',
				['query' => $term] + ($titleOnly ? ['names' => '1'] : []),
			),
			icon: 'icon-search',
		);

		// Deliberately no fileId attribute. This entry is not a hit, and it must
		// never be counted as one: the parity job reads the attribute of every
		// entry of this group as a permission answer, and a door with a file id
		// would be compared against the file list of a user as if it were a file.
		// Whoever teaches a reader of this group to skip it recognises it by its
		// address, never by the missing attribute, because "no attribute means
		// skip" would switch off the very check that guard exists for.

		return $entry;
	}

	/**
	 * The canary of the walking skeleton has no file behind it and carries the
	 * file id 0. Pointing it at the files list keeps the link from resolving to
	 * nothing.
	 */
	private function resourceUrl(int $fileId): string {
		if ($fileId <= 0) {
			return $this->urlGenerator->linkToRoute('files.view.index');
		}

		return $this->urlGenerator->linkToRoute('files.View.showFile', ['fileid' => $fileId]);
	}
}
