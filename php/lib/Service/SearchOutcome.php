<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

/**
 * What one search run produced, in the language of the product rather than in
 * the language of one of its two callers.
 *
 * A run that ended normally carries a failure of null, and that stays true when
 * it found nothing at all: an empty list of hits is the honest answer to a term
 * nobody has a file for, and calling it a failure would turn "nothing found"
 * into "something is broken". The four reasons below are the cases in which the
 * run could not do what it was asked, and each of them is a different sentence
 * on the screen.
 *
 * FAILURE_BACKEND_SILENT is set only when not a single hit was collected and at
 * least one candidate call came back with nothing. A run that already has hits
 * shows them and keeps quiet about the silent follow up call: an incomplete
 * list beats an error message printed over hits the user can see (sight check
 * 10 of the 09-UI-SPEC).
 *
 * FAILURE_OFFSET_CEILING is set as soon as the paging ceiling ended the run,
 * whether or not hits were collected before it. hasMore is false in that case
 * and never anything else, because there is no honest way to page on: the
 * cursor behind the ceiling is one the container refuses, so a next page would
 * be a promise that cannot be kept.
 */
final class SearchOutcome {
	/**
	 * The container answered nothing at all, and nothing was collected before
	 * it did. A backend that is stopped, unreachable or answering with an error
	 * arrives here.
	 */
	public const FAILURE_BACKEND_SILENT = 'backend_silent';

	/**
	 * The two halves of this app report versions whose major or minor
	 * disagree (D-11). Not an error and not an empty index: a hit across a
	 * protocol break would be a guess presented as a finding.
	 */
	public const FAILURE_VERSION_DRIFT = 'version_drift';

	/**
	 * This user has no home folder, so the permission question cannot be asked
	 * at all, and the only safe answer to a question that cannot be asked is
	 * nothing.
	 */
	public const FAILURE_NO_HOME_FOLDER = 'no_home_folder';

	/**
	 * The cursor climbed past the paging ceiling of the container, so the run
	 * ended without asking. The caller shows the "there are more hits, narrow
	 * the search" line and never an error about the backend, because the
	 * backend is answering perfectly well.
	 */
	public const FAILURE_OFFSET_CEILING = 'offset_ceiling';

	/**
	 * @param list<ApprovedHit> $hits the hits that passed the permission
	 *                                decision, in the order the container
	 *                                ranked them
	 * @param array<int,array{text:string,highlights:list<array{int,int}>}> $excerpts
	 *        the excerpt of a hit, keyed by file id, and absent for every hit
	 *        the excerpt call did not cover
	 * @param int $nextCursor the container offset a following run continues
	 *                        from
	 * @param bool $hasMore whether the container said there is more behind the
	 *                      last page this run looked at
	 * @param bool $degraded whether the backend answered from a reduced state,
	 *                       for instance while its index is still being built
	 * @param string|null $failure one of the four reasons above, or null when
	 *                             the run ended normally
	 */
	public function __construct(
		public readonly array $hits,
		public readonly array $excerpts,
		public readonly int $nextCursor,
		public readonly bool $hasMore,
		public readonly bool $degraded,
		public readonly ?string $failure,
	) {
	}
}
