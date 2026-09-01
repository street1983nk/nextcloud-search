<?php

declare(strict_types=1);

namespace OCA\Findling\Search;

use OCA\Findling\Service\ExAppService;
use OCA\Findling\Text\PlainText;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\File;
use OCP\Files\IRootFolder;
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
 * The search provider, and the security boundary of the whole product.
 *
 * IFilteringProvider rather than plain IProvider, and deliberately not
 * IExternalProvider: an external provider is a provider that asks a third
 * party, and the unified search dialog keeps those switched off by default.
 * That would break the zero-config promise on the first search a user ever
 * runs.
 *
 * The search runs in two stages. The container answers with candidates that
 * carry a file id and nothing else, this class decides which of them this user
 * may actually see, and only then does it ask for the text excerpts of the
 * survivors. The order is not an optimisation. An excerpt is file content, and
 * file content for a file the user cannot open must never enter this process in
 * the first place.
 *
 * The whole group runs against a wall clock of two and a half seconds. The
 * unified search asks every provider and waits for all of them, so a slow
 * provider does not cost its own result group, it costs the search.
 */
final class Provider implements IFilteringProvider {
	/**
	 * The wall clock for one result group, in nanoseconds. It is measured with
	 * hrtime() and not with microtime(), because a clock adjustment during a
	 * search would otherwise either double the budget or end it immediately.
	 */
	private const BUDGET_NANOSECONDS = 2_500_000_000;

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
	 * Every resolution below is a query against oc_filecache. With a limit of
	 * 20, an overfetch of four and three rounds there would be up to 240 of
	 * them in a single search, and on a small box the time budget is gone
	 * before the first excerpt has even been requested. Two per displayed hit
	 * leaves room for a user whose candidates are mostly revoked shares, and
	 * the absolute ceiling keeps a large limit from reopening the same hole.
	 *
	 * What is capped is how many candidates are examined. Whether a displayed
	 * hit was examined is not capped and cannot be: the loop below stops
	 * approving, it never approves without asking.
	 */
	private const MAX_RECHECKS_PER_HIT = 2;
	private const MAX_RECHECKS_ABSOLUTE = 64;

	/**
	 * Ceilings in characters for the two fields that come out of the file
	 * system. A file name from an external storage is not more trustworthy than
	 * a container answer.
	 */
	private const MAX_TITLE_LENGTH = 255;
	private const MAX_PATH_LENGTH = 255;

	public function __construct(
		private IL10N $l10n,
		private IURLGenerator $urlGenerator,
		private ExAppService $exApp,
		private IRootFolder $rootFolder,
		private IUserMountCache $mountCache,
		private IFileAccess $fileAccess,
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
		$deadline = hrtime(true) + self::BUDGET_NANOSECONDS;
		$uid = $user->getUID();
		$term = trim($query->getTerm());
		$limit = max(1, $query->getLimit());

		// An empty search line is not asked about at all. It is what the dialog
		// sends while the user is still typing, and it cannot produce a hit.
		if ($term === '') {
			return SearchResult::complete($this->getName(), []);
		}

		$titleOnly = $this->titleOnly($query);

		try {
			$userFolder = $this->rootFolder->getUserFolder($uid);
		} catch (\Throwable $e) {
			// Every failure is caught on purpose. getUserFolder() signals a
			// missing user with a class from the private namespace of the
			// server and a missing home directory with a different one again;
			// both mean the same thing here, and neither may reach the unified
			// search as an exception. Without a home folder no permission
			// decision is possible, and handing out unchecked hits instead
			// would be the actual bug.
			$this->logger->warning('Findling: no home folder for this user, dropping every hit', ['exception' => $e]);
			return SearchResult::complete($this->getName(), []);
		}

		$storageIds = $this->storageIdsOfUser($user);
		$recheckBudget = min(self::MAX_RECHECKS_ABSOLUTE, $limit * self::MAX_RECHECKS_PER_HIT);
		$rechecks = 0;
		$offset = $this->startOffset($query);
		$exhausted = true;
		$approved = [];

		for ($round = 0; $round < self::MAX_ROUNDS; $round++) {
			if (count($approved) >= $limit || $rechecks >= $recheckBudget || hrtime(true) >= $deadline) {
				break;
			}

			// Fetching more than the recheck budget could ever examine buys
			// nothing (perf audit M4): the overfetch is capped at what is left
			// of the budget plus one display page for the candidates that cost
			// no recheck. The remaining wall clock travels with the call, so
			// the request timeout can never overdraw the deadline (perf H5).
			$fetchLimit = min($limit * self::OVERFETCH, $recheckBudget - $rechecks + $limit);
			$page = $this->exApp->searchCandidates($uid, $term, $fetchLimit, $offset, $titleOnly, $this->secondsLeft($deadline));
			if ($page === null) {
				break;
			}

			if ($page['degraded']) {
				// The backend answered from a reduced state, for instance while
				// the index is still being built. Worth a line, not worth
				// hiding the hits it did find.
				$this->logger->debug('Findling: backend answered in a degraded state');
			}

			$candidates = $page['candidates'];
			if ($candidates === []) {
				// An empty page is only the end when the backend says so. The
				// cheap reduction over there can empty a page whose successors
				// still hold this user's hits, and breaking here would silently
				// swallow every hit behind it; the round counter above bounds
				// how often this is retried.
				$exhausted = !$page['hasMore'];
				if ($exhausted) {
					break;
				}
				$offset = $page['nextOffset'];
				continue;
			}

			$keptIds = $this->reduceIds($candidates, $storageIds);

			// The one and only permission decision of this product. A candidate
			// becomes a hit when this user's own folder resolves its file id to
			// a file, and it is dropped otherwise: never visible, no longer
			// visible, moved into the trash and deleted are deliberately the
			// same outcome, so a hit cannot be used to probe for files this
			// user is not allowed to see.
			//
			// The two counters above this loop cap how many candidates are
			// examined, never whether a displayed one was. A hit that reaches
			// the screen without having passed this line does not exist.
			//
			// $consumed counts the candidates this loop has decided about, and
			// only those. When a budget ends the page early, the cursor resumes
			// exactly behind the last decided candidate, so the better ranked
			// remainder of the page shows up on the next unified search page
			// instead of vanishing between two cursors.
			$consumed = 0;
			$stopped = false;
			foreach ($candidates as $candidate) {
				if (count($approved) >= $limit) {
					$stopped = true;
					break;
				}

				if ($candidate['fileId'] <= 0) {
					// The diagnostic path of phase 1. There is no file behind
					// this id, so there is nothing to resolve: the text was
					// composed inside the container out of host name,
					// timestamp and the user id of the signed header and
					// carries no user content. The proxy accepts it under one
					// exact title and under no other.
					$consumed++;
					$approved[] = [
						'fileId' => 0,
						'title' => $candidate['title'] ?? '',
						'subline' => $candidate['snippet'] ?? '',
					];
					continue;
				}

				if ($keptIds !== null && !isset($keptIds[$candidate['fileId']])) {
					// Decided, not skipped: the file lives on a storage this
					// user has no mount on, so the recheck could only repeat
					// the verdict at a higher price.
					$consumed++;
					continue;
				}

				if ($rechecks >= $recheckBudget) {
					$stopped = true;
					break;
				}

				$rechecks++;
				$consumed++;
				$node = $userFolder->getFirstNodeById($candidate['fileId']);
				if (!$node instanceof File) {
					continue;
				}

				$title = PlainText::bounded($node->getName(), self::MAX_TITLE_LENGTH);
				$path = PlainText::bounded(
					ltrim((string)$userFolder->getRelativePath($node->getPath()), '/'),
					self::MAX_PATH_LENGTH,
				);
				if ($title === null || $path === null) {
					continue;
				}

				// Title and link come out of the confirmed node, never out of
				// the container answer. A confused or compromised backend can
				// otherwise put the name of a foreign file in front of the
				// user.
				$approved[] = [
					'fileId' => $candidate['fileId'],
					'title' => $title,
					'subline' => $path,
				];
			}

			if ($stopped) {
				$offset += $consumed;
				$exhausted = false;
				break;
			}

			$offset = $page['nextOffset'];
			$exhausted = !$page['hasMore'];
			if ($exhausted) {
				break;
			}
		}

		if ($approved === []) {
			return SearchResult::complete($this->getName(), []);
		}

		// Only now, and only for the survivors. If the budget is used up the
		// hits are shown with their path as the subline instead: a hit without
		// an excerpt beats no hit at all.
		$fileIds = [];
		foreach ($approved as $hit) {
			if ($hit['fileId'] > 0) {
				$fileIds[] = $hit['fileId'];
			}
		}

		$excerpts = $fileIds !== []
			? $this->exApp->snippets($uid, $term, $fileIds, $titleOnly, $this->secondsLeft($deadline))
			: [];

		$entries = $this->toEntries($approved, $excerpts);

		return $exhausted
			? SearchResult::complete($this->getName(), $entries)
			: SearchResult::paginated($this->getName(), $entries, $offset);
	}

	/**
	 * The cheap reduction that runs before the first node is resolved.
	 *
	 * Two queries instead of one per candidate: the mounts of this user were
	 * fetched once for the whole search, and the cache entries of a whole page
	 * of candidates are fetched in a single call. Whatever lives on a storage
	 * this user has no mount on cannot be theirs, and is dropped before it can
	 * cost a resolution.
	 *
	 * This is a reduction and not a boundary, and the difference matters. It is
	 * an over-approximation: a storage can carry files of a mount this user
	 * does not have, and a team folder with per folder permissions is not
	 * resolved here at all. Everything it lets through is still decided by the
	 * recheck.
	 *
	 * Null and an empty array are two different answers. Null means the
	 * reduction cannot decide anything, so every candidate goes to the capped
	 * recheck; the caps and the recheck are both still in force, so falling
	 * back is safe. An array is a verdict per positive file id: present means
	 * "worth a recheck", absent means "cannot be this user's file".
	 *
	 * @param list<array{fileId:int,title?:string,snippet?:string}> $candidates
	 * @param array<int,true> $storageIds
	 * @return array<int,true>|null
	 */
	private function reduceIds(array $candidates, array $storageIds): ?array {
		$fileIds = [];
		foreach ($candidates as $candidate) {
			if ($candidate['fileId'] > 0) {
				$fileIds[] = $candidate['fileId'];
			}
		}

		if ($fileIds === [] || $storageIds === []) {
			return null;
		}

		try {
			$entries = $this->fileAccess->getByFileIds($fileIds);
		} catch (\Throwable $e) {
			$this->logger->debug('Findling: bulk cache lookup failed, falling back to the capped recheck', ['exception' => $e]);
			return null;
		}

		$kept = [];
		foreach ($fileIds as $fileId) {
			$entry = $entries[$fileId] ?? null;
			if ($entry !== null && isset($storageIds[$entry->getStorageId()])) {
				$kept[$fileId] = true;
			}
		}

		return $kept;
	}

	/**
	 * The numeric storage ids this user has a mount on, fetched once per
	 * search and keyed by id for the lookup in the reduction. An empty map
	 * means the reduction is skipped, not that the user sees nothing.
	 *
	 * @return array<int,true>
	 */
	private function storageIdsOfUser(IUser $user): array {
		try {
			$mounts = $this->mountCache->getMountsForUser($user);
		} catch (\Throwable $e) {
			$this->logger->debug('Findling: mount list unavailable, skipping the cheap reduction', ['exception' => $e]);
			return [];
		}

		$storageIds = [];
		foreach ($mounts as $mount) {
			$storageIds[$mount->getStorageId()] = true;
		}

		return $storageIds;
	}

	/**
	 * What is left of the wall clock, in seconds. Negative once the deadline
	 * has passed, which the callee reads as "do not call at all".
	 */
	private function secondsLeft(int|float $deadline): float {
		return ((float)$deadline - (float)hrtime(true)) / 1_000_000_000.0;
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
	 * @param list<array{fileId:int,title:string,subline:string}> $approved
	 * @param array<int,array{text:string,highlights:list<array{int,int}>}> $excerpts
	 * @return list<SearchResultEntry>
	 */
	private function toEntries(array $approved, array $excerpts): array {
		$entries = [];

		foreach ($approved as $hit) {
			$fileId = $hit['fileId'];
			$excerpt = $excerpts[$fileId] ?? null;

			$entry = new SearchResultEntry(
				thumbnailUrl: '',
				title: $hit['title'],
				subline: $excerpt === null ? $hit['subline'] : $excerpt['text'],
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
