<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

/**
 * The four values of a narrowed search, as one named value rather than as four
 * more positional arguments on three methods.
 *
 * An object and not a parameter list, for the same reason SearchCaps is one.
 * Type groups, sort mode and the two time bounds would otherwise travel through
 * SearchService and through both calls of ExAppService as four more positions,
 * and a call site reading run($user, $term, false, 0, $caps, [], 'newest', null,
 * 1757980800) tells no reader which value means what. Written out once here,
 * every caller names the field it sets.
 *
 * Unlike SearchCaps this class does have a factory, and the difference is
 * deliberate rather than an oversight. There a default would have been a number
 * nobody has to think about, which is exactly why that class refuses one. Here
 * "nothing is narrowed" is not a convenient number but a named state of the
 * product: the unified search dialog has no chips at all, and neither has any
 * other caller that narrows nothing. none() gives that state its name instead of
 * making every such call site spell out four empty values.
 *
 * Two rules hold for everything below.
 *
 * First, this object knows group names and not a single file extension. The
 * mapping from a group to the extensions behind it lives in
 * backend/src/findling/query/rewrite.py::TYPE_GROUPS and nowhere else. A second
 * table over here would be a second filter vocabulary, and two vocabularies
 * drift apart in the direction nobody notices: a file type the page offers and
 * the index never answers for.
 *
 * Second, this class validates nothing and throws nothing. It takes what the
 * caller has already checked. The address of the result page is read in
 * PageController and the filter values of the dialog are read in the search
 * provider, both with a silent fallback, because a value somebody edited into
 * the address bar has to cost a chip and never an error page. What happens
 * further down is clamping and still not refusing: ExAppService bounds every one
 * of these four values again on its way into the request body, so that an object
 * built by hand cannot reach the container with something it answers with a 422.
 */
final class SearchFilters {
	/**
	 * The closed set of type groups, in the order of the surface.
	 *
	 * Same shape and same reason as MIN_LIMIT and MAX_LIMIT in ExAppService: a
	 * bound that is written down once, carries its reasoning, and is read rather
	 * than copied. The order is the one of ROADMAP success criterion 1, of
	 * FILT-01 and of the chip row, so that roadmap, requirement and surface name
	 * the same sequence, and it is the order a value list is canonicalised into.
	 *
	 * Six names and not seven: the set is the whole list of what the index can
	 * group, not a policy about what a user may ask for.
	 *
	 * @var list<string>
	 */
	public const TYPES = ['pdf', 'documents', 'spreadsheets', 'presentations', 'images', 'text'];

	/**
	 * The three sort modes, and there is no fourth.
	 *
	 * The same three names the container accepts, see SORT_MODES in
	 * backend/src/findling/index/search.py. A name outside this list is not an
	 * error over here, it is a value that falls back to the default below.
	 *
	 * @var list<string>
	 */
	public const SORTS = ['relevance', 'newest', 'oldest'];

	/**
	 * The mode of a search nobody sorted, and the one mode that is never written
	 * into an address and never into a request body. Everything the product did
	 * before this phase is this value.
	 */
	public const SORT_DEFAULT = 'relevance';

	/**
	 * The ceiling of a time bound, and it is the same number as SEARCH_MTIME_MAX
	 * in backend/src/findling/config.py: 4102444800 is 1 January 2100, 00:00 UTC.
	 *
	 * Both halves have to carry the same ceiling, and the sentence is written
	 * here because only one of the two can be read from the other. Over there the
	 * number is what the wire model validates, and a larger value is answered
	 * with a 422, which arrives on this side as an empty result group and looks
	 * exactly like "nothing found". Over here the number is what a value is
	 * clamped to. A ceiling only one half knew would turn a hand built address
	 * into an error page instead of into an answer.
	 */
	public const EPOCH_MAX = 4102444800;

	/**
	 * @param list<string> $types the active type groups, canonicalised and free
	 *                            of duplicates, every one of them a name out of
	 *                            TYPES; an empty list means no type filter
	 * @param string $sort one of SORTS, and SORT_DEFAULT for a search nobody
	 *                     sorted
	 * @param int|null $since lower bound of the modification date, Unix epoch in
	 *                        seconds, or null for no lower bound
	 * @param int|null $until upper bound of the modification date, Unix epoch in
	 *                        seconds, or null for no upper bound
	 */
	public function __construct(
		public readonly array $types,
		public readonly string $sort,
		public readonly ?int $since,
		public readonly ?int $until,
	) {
	}

	/**
	 * A search that narrows nothing and sorts by relevance.
	 *
	 * The state of every caller that has no chips to offer, and of the unified
	 * search dialog before FILT-03 hands it its two date bounds. It is a factory
	 * and not a default argument on purpose: a default would let a caller that
	 * forgot to pass its filters look exactly like a caller that has none.
	 */
	public static function none(): self {
		return new self([], self::SORT_DEFAULT, null, null);
	}

	/**
	 * Whether anything is narrowed, and the sort mode expressly does not count.
	 *
	 * This is the one place where the reset link (D-06) and the empty filter
	 * state (D-07) decide whether they appear at all. A sort mode takes nothing
	 * away: it puts the same hits in another order, so a reset link that offered
	 * to remove it would point at something that is not hiding a single result.
	 */
	public function hasAny(): bool {
		return $this->types !== [] || $this->since !== null || $this->until !== null;
	}
}
