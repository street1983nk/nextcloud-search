<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

/**
 * The four families of ceilings one search run is bounded by, as one named
 * value rather than as seven optional arguments.
 *
 * An object and not a parameter list because there are two callers with two
 * different sets of numbers: the unified search dialog waits for every provider
 * in parallel and is therefore the impatient one, and the own result page waits
 * for nobody and may take longer. With optional arguments the dialog would call
 * run($user, $term, $titleOnly) and the page would call run($user, $term,
 * $titleOnly, 25, $cursor, 3.0, 1.5), and no reader could tell from either call
 * site which number applies where. Every field is written out at both call
 * sites on purpose, and there is no default and no factory: a default is a
 * number nobody has to think about, and every one of these seven is a number
 * somebody had to think about once.
 */
final class SearchCaps {
	/**
	 * @param int $pageSize how many approved hits one run may return
	 * @param int $maxRounds how often the container may be asked in one run
	 * @param int $overfetch how many candidates are asked for per displayed hit
	 * @param int $recheckPerHit how many resolutions one displayed hit may cost
	 * @param int $recheckAbsolute the ceiling on resolutions per run, whatever
	 *                             the page size says
	 * @param float $budgetSeconds the wall clock of the whole run
	 * @param float $requestCeilingSeconds the ceiling of a single call to the
	 *                                     container, never the floor: every
	 *                                     call still shrinks to what is left of
	 *                                     the wall clock above
	 */
	public function __construct(
		public readonly int $pageSize,
		public readonly int $maxRounds,
		public readonly int $overfetch,
		public readonly int $recheckPerHit,
		public readonly int $recheckAbsolute,
		public readonly float $budgetSeconds,
		public readonly float $requestCeilingSeconds,
	) {
	}
}
