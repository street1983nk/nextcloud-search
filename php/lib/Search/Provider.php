<?php

declare(strict_types=1);

namespace OCA\Findling\Search;

use OCA\Findling\Service\ExAppService;
use OCA\Findling\Service\SearchCaps;
use OCA\Findling\Service\SearchFilters;
use OCA\Findling\Service\SearchService;
use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\IUser;
use OCP\Search\FilterDefinition;
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

	/**
	 * The one filter this provider defines itself, the type groups of USRCH-01.
	 *
	 * The name is the address parameter of the own result page on purpose:
	 * the same word carries the same comma separated value in both places and
	 * goes through the same parser, SearchFilters::typesFrom(). It is free in
	 * the core, which reserves term, since, until, title-only, person, places
	 * and provider, and it satisfies the [-0-9a-z] rule of FilterDefinition.
	 */
	public const FILTER_TYPES = 'types';

	/**
	 * The second filter of our own, the folder of USRCH-02 (plan 32-02).
	 *
	 * Its own name and deliberately not path, the name the Files provider of
	 * the core uses: over there the value is a LIKE prefix without a
	 * separator, so /Projekte also matches /Projekte2. Here it is a folder and
	 * everything below it, resolved in the tree of the asking user. Free in
	 * the core and inside the [-0-9a-z] rule of FilterDefinition.
	 */
	public const FILTER_FOLDER = 'folder';

	/**
	 * The longest raw folder value folderOf() reads at all, in bytes.
	 *
	 * 4000 is the width of the path column of oc_filecache: no path the file
	 * cache can hold is longer, so a longer value is not a folder anybody
	 * picked but a value somebody built, and it is read as no folder at all.
	 */
	public const MAX_FOLDER_LENGTH = 4000;

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
	 * The two date bounds are the sentence this list was missing until plan
	 * 13-06. Whoever set a date in the dialog watched Findling disappear out of
	 * it, and there were two ways for that to happen: the surface reads the
	 * filter list of every provider and simply stopped asking this one, or the
	 * group ended in the HTTP 400 that an undeclared exclusive filter is
	 * answered with. Both looked the same to the user, a search without us in
	 * it, which is why the repair is one line here and its effect two screens
	 * below.
	 *
	 * The fifth name, types, is our own since plan 32-01 (USRCH-01) and the
	 * only one in this list that is not a core name. The core resolves every
	 * name of this list against a definition when it loads the providers and
	 * throws for a name without one, which costs the provider list of every
	 * app in the dialog; getCustomFilters() below is what keeps this name
	 * resolvable. The sixth, folder, joined with plan 32-02 (USRCH-02) under
	 * the same rule.
	 *
	 * @return list<string>
	 */
	#[\Override]
	public function getSupportedFilters(): array {
		return [
			IFilter::BUILTIN_TERM,
			IFilter::BUILTIN_TITLE_ONLY,
			IFilter::BUILTIN_SINCE,
			IFilter::BUILTIN_UNTIL,
			self::FILTER_TYPES,
			self::FILTER_FOLDER,
		];
	}

	/**
	 * No second id triggers this provider. Its two filters of its own are
	 * declared in getCustomFilters() below, with the definition a custom name
	 * cannot do without: a name without one turns the whole provider list into
	 * an error.
	 *
	 * @return list<string>
	 */
	#[\Override]
	public function getAlternateIds(): array {
		return [];
	}

	/**
	 * Exactly two filters of our own, the type groups and since plan 32-02 the
	 * folder, and their definitions are what keeps the provider list of the
	 * whole dialog valid.
	 *
	 * Until plan 32-01 this list was empty on purpose and the type filter lived
	 * on the own result page only (D-05). D-32-07 lifts that decision for the
	 * type groups and for nothing else; the sort mode stays on the page. The
	 * warning D-05 was built on still holds and is the reason for this method:
	 * a custom name in getSupportedFilters() without a definition here makes
	 * the core throw while it loads the providers, and that costs every
	 * provider in the dialog, not only this one.
	 *
	 * A string and not a list of strings, because the value travels as one
	 * comma separated word, exactly like the address parameter of the result
	 * page, and SearchFilters::typesFrom() reads it.
	 *
	 * Exclusive, which is the default of the constructor, and the choice is
	 * one of documentation rather than effect (SearchComposer, stable34). The
	 * core keeps a custom definition under the id of the provider that
	 * declared it, so no other provider ever resolves this name: a request
	 * that carries it to another provider drops it as unknown, and the
	 * exclusive check is only reached for this provider, which lists the name.
	 * Exclusive states what the filter is, a narrowing only Findling knows.
	 *
	 * The folder is a string for the same reason: one path relative to the
	 * user folder, read by folderOf() below. Same exclusive default, same
	 * effect.
	 *
	 * @return list<FilterDefinition>
	 */
	#[\Override]
	public function getCustomFilters(): array {
		return [
			new FilterDefinition(self::FILTER_TYPES, FilterDefinition::TYPE_STRING),
			new FilterDefinition(self::FILTER_FOLDER, FilterDefinition::TYPE_STRING),
		];
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
		$types = $this->typesOf($query);

		// What this dialog is able to narrow: the type groups and the two dates.
		// The type groups joined with plan 32-01 (USRCH-01; D-32-07 lifts D-05
		// for them), declared in getCustomFilters() with the definition a name
		// of our own cannot do without. The sort mode stays the default and is
		// offered on the own result page only; ordering the dialog is not part
		// of this phase. The folder joined with plan 32-02 (USRCH-02); it is
		// resolved in SearchService and never leaves PHP (D-32-06).
		//
		// The type groups are reduced to the closed set before they leave this
		// method and both bounds are clamped, so that neither a tampered value
		// nor an absurd date reaches the container as something it answers
		// with a 422 (D-32-03).
		$filters = new SearchFilters(
			$types,
			SearchFilters::SORT_DEFAULT,
			$this->epochWithin($this->epochOf($query, IFilter::BUILTIN_SINCE)),
			$this->epochWithin($this->epochOf($query, IFilter::BUILTIN_UNTIL)),
			$this->folderOf($query),
		);

		$outcome = $this->searchService->run(
			$user,
			$term,
			$titleOnly,
			$this->startOffset($query),
			$this->caps(max(1, $query->getLimit())),
			$filters,
		);

		if ($outcome->hits === []) {
			if ($outcome->failure !== null) {
				// One line and no more. The five reasons are a closed set of
				// constants and never user content, and the two that an admin
				// can act on have already been logged with their detail inside
				// the service; this is the trace that says which of them ended
				// this particular group.
				//
				// The fifth, all_candidates_rejected, is traced here like the
				// other four and gets no entry of its own either. An entry in
				// the dialog would be a hit that is none, and this dialog has
				// no room for a sentence: the result page is the one place
				// where the reasons are told apart, and that is the existing
				// line of this product rather than a decision of plan 11-13.
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
			$entries[] = $this->entryPoint($term, $titleOnly, $types);
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
	 * The type groups of the dialog, read through the one parser of the result
	 * page, or none at all.
	 *
	 * The same defensive shape as titleOnly() above. The value of a string
	 * filter is a string over there, so anything else is a defect on that side
	 * and counts as "not set". A string is reduced to the closed set by
	 * SearchFilters::typesFrom(): an unknown, empty, overlong or tampered value
	 * leaves no group behind, and the search runs exactly as it would without
	 * the filter (D-32-03, ROADMAP success criterion 3). Nothing here throws
	 * and nothing here logs the value.
	 *
	 * @return list<string>
	 */
	private function typesOf(ISearchQuery $query): array {
		$filter = $query->getFilter(self::FILTER_TYPES);
		if ($filter === null) {
			return [];
		}

		$value = $filter->get();

		return is_string($value) ? SearchFilters::typesFrom($value) : [];
	}

	/**
	 * The folder of the dialog as a path relative to the user folder, with a
	 * leading slash and without a trailing one, or no folder at all.
	 *
	 * The same defensive shape as typesOf() above: a value that is not a
	 * string, is longer than MAX_FOLDER_LENGTH or carries a control character
	 * is a value somebody built, and it is read as no folder (D-32-03, ROADMAP
	 * success criterion 3). The root of the user folder narrows nothing and is
	 * no folder either. An empty value never reaches this method, because the
	 * core answers it with HTTP 400 before any provider is asked (D-32-01); it
	 * is still read as no folder here.
	 *
	 * A value with '..' is not refused here but in SearchService, which
	 * resolves the path with Folder::get() and checks that the node lies
	 * inside the user folder. One place decides what a folder is, and it is
	 * the one that sees the tree. Nothing here throws and nothing here logs the
	 * value.
	 */
	private function folderOf(ISearchQuery $query): ?string {
		$filter = $query->getFilter(self::FILTER_FOLDER);
		if ($filter === null) {
			return null;
		}

		$value = $filter->get();
		if (!is_string($value) || strlen($value) > self::MAX_FOLDER_LENGTH || preg_match('/[\x00-\x1F\x7F]/', $value) !== 0) {
			return null;
		}

		$path = '/' . trim($value, '/');

		return $path === '/' ? null : $path;
	}

	/**
	 * One of the two built in date bounds as a Unix epoch, or nothing at all.
	 *
	 * The same defensive shape as titleOnly() above, and for the same reason.
	 * The value of a date filter is a \DateTimeImmutable over there, so
	 * anything else is a defect on that side, and a defect on that side counts
	 * as "not set" over here rather than as an exception: somebody who picked a
	 * date is owed an answer about the term, not an empty result group and not
	 * a stack trace.
	 *
	 * getTimestamp() carries no time zone and is therefore comparable against
	 * mtime without a conversion, which is why this path needs no time zone at
	 * all. The quick ranges of the own result page do need one, because a
	 * calendar word has to be told which midnight it meant.
	 */
	private function epochOf(ISearchQuery $query, string $name): ?int {
		$filter = $query->getFilter($name);
		if ($filter === null) {
			return null;
		}

		$value = $filter->get();

		return $value instanceof \DateTimeImmutable ? $value->getTimestamp() : null;
	}

	/**
	 * One time bound inside the range both halves of this app agree on.
	 *
	 * Clamped and never refused, the same way ExAppService does it for the
	 * values of the own result page, and against the same ceiling. A bound
	 * above SEARCH_MTIME_MAX is answered by the container with a 422, and a 422
	 * arrives here as an empty result group that reads like "nothing found";
	 * the honest answer to an absurd date is the search it was meant to narrow.
	 */
	private function epochWithin(?int $epoch): ?int {
		return $epoch === null ? null : max(0, min(SearchFilters::EPOCH_MAX, $epoch));
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
	 * The address carries the term, the built in file name filter if it was set
	 * and the type groups if any were set, and nothing else: no page and no
	 * cursor path, because the way in is always page one. Parameters that are
	 * not a placeholder of the route are appended as a query string by the url
	 * generator, which is what the page reads.
	 *
	 * The type groups travel since plan 32-01 because the page shows them as
	 * chips: a user arriving there sees the narrowing that produced the group
	 * and can take it off with one click. They arrive in the order of
	 * SearchFilters::TYPES, the canonical form the page reads back.
	 *
	 * The two date bounds of the dialog are knowingly left out of that address.
	 * The door leads to page one of a search nobody narrowed, and that is a
	 * decision rather than a forgotten parameter: the page owns its own filter
	 * row, and handing it a bound it does not show as a chip would leave a user
	 * in front of fewer hits than the dialog promised, with nothing on the page
	 * saying why. The folder of the dialog stays out for the same reason: the
	 * page has no folder filter (plan 32-02 defers it).
	 *
	 * @param list<string> $types the active type groups, already canonical
	 */
	private function entryPoint(string $term, bool $titleOnly, array $types): SearchResultEntry {
		$entry = new SearchResultEntry(
			thumbnailUrl: '',
			title: $this->l10n->t('Show all results'),
			subline: $this->l10n->t('Opens the Findling results page'),
			resourceUrl: $this->urlGenerator->linkToRoute(
				'findling.page.index',
				['query' => $term]
					+ ($titleOnly ? ['names' => '1'] : [])
					+ ($types === [] ? [] : ['types' => implode(',', $types)]),
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
