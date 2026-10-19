<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

/**
 * What one look at the neighbours of a document produced (STR-01, plan 35-06).
 *
 * A value of its own and not a SearchOutcome with empty fields, because the two
 * answers say different things. A search run has a cursor, a next page and a
 * reason why its result is empty although the term exists elsewhere; the view
 * of similar documents has none of the three. It shows at most ten neighbours
 * on one page, it has no paging (PE-35-1), and it never says that something
 * was found and then withheld.
 *
 * That last sentence is why this class has no counting field, and the absence
 * is the design rather than an omission (T-35-22). How many neighbours the
 * container proposed and how many the recheck threw away is a number about
 * files this user may not open: "three of ten" on the screen would tell them
 * that seven documents near theirs exist somewhere in the instance. So the
 * outcome carries the confirmed hits and nothing about the rest, and an empty
 * list reads the same whether the container proposed nothing or proposed only
 * foreign files.
 *
 * The source is an ApprovedHit like every neighbour, built out of the confirmed
 * node, so the heading of the view names the file with the same bounded title
 * a hit would carry. It is null exactly when the source could not be confirmed,
 * and in that case nothing else is set: no neighbours were asked for.
 *
 * Failure reasons. FAILURE_SOURCE_UNAVAILABLE is the one state for every source
 * that did not pass the recheck: unknown, foreign, deleted, not readable, or
 * a file whose name could not be cleaned. Telling them apart would tell a user
 * whether somebody else's file exists (PE-35-3 (b), T-35-19). The other three
 * reasons are the values of SearchOutcome and mean the same here, named through
 * its constants so that the page can branch on one vocabulary for both views.
 */
final class SimilarOutcome {
	/**
	 * The source could not be confirmed for this user, for whatever reason.
	 * One state on purpose, see the class comment.
	 */
	public const FAILURE_SOURCE_UNAVAILABLE = 'source_unavailable';

	/** The container answered nothing usable; the source is known. */
	public const FAILURE_BACKEND_SILENT = SearchOutcome::FAILURE_BACKEND_SILENT;

	/** The two halves report different versions; the container was not asked. */
	public const FAILURE_VERSION_DRIFT = SearchOutcome::FAILURE_VERSION_DRIFT;

	/** No home folder, so no permission question can be asked at all. */
	public const FAILURE_NO_HOME_FOLDER = SearchOutcome::FAILURE_NO_HOME_FOLDER;

	/**
	 * @param ApprovedHit|null $source the confirmed source, or null when it did
	 *                                 not pass the recheck or was never asked
	 *                                 about
	 * @param list<ApprovedHit> $hits the confirmed neighbours in the order the
	 *                                container ranked them, never the source,
	 *                                at most SearchService::SIMILAR_MAX_HITS
	 * @param bool $degraded whether the backend answered from a reduced state
	 * @param string|null $failure one of the four reasons above, or null when
	 *                             the look ended normally, which includes an
	 *                             empty list of neighbours
	 */
	public function __construct(
		public readonly ?ApprovedHit $source,
		public readonly array $hits,
		public readonly bool $degraded,
		public readonly ?string $failure,
	) {
	}
}
