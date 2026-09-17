<?php

declare(strict_types=1);

/**
 * The result page of Findling: head, banner, filter row, hit list, empty state,
 * pagination.
 *
 * Every one of the six blocks below is rendered server side with the real
 * values of this request. That is a requirement and not a style: with
 * JavaScript switched off the page has to stay complete, so there is no
 * skeleton, no spinner and no loading state anywhere, and searching, paging,
 * filtering, opening a hit and coming back all work without a single line of
 * script. The one thing the script adds is the return marker, and the page is
 * whole if it never runs.
 *
 * Every visible string runs through $l->t(). Every value that somebody else
 * wrote, a search term, a file name, a path, a piece of an excerpt, is printed
 * with p() and never with the unescaped printer. The highlight of an excerpt is
 * the one place where markup and data meet, and they meet here rather than in a
 * string: the mark element is written out as a literal by this file and each
 * piece of text goes through the escaping printer on its own, so no character a
 * container sent can ever become an element (T-09-02).
 *
 * There is no inline script, because the Nextcloud CSP blocks one, and no style
 * attribute, because one would ignore the theme. There is no live region
 * either, not even on the error block: this page loads whole and nothing on it
 * changes under the reader, so an assertive region would announce a sentence
 * that was already in the document order the moment it was read.
 *
 * @var array<string,mixed> $_ the nineteen parameters of PageController::index(), verbatim
 * @var \OCP\IL10N $l
 */

// The two calls belong here and not into the controller. The template is
// rendered before the layout collects its resource lists, so a call from the
// controller would arrive too late and the page would be served without either
// file. Same reason, same place as on the administration page.
\OCP\Util::addScript('findling', 'search');
\OCP\Util::addStyle('findling', 'search');

// The seven path data of the page, taken word for word from the pinned upstream
// commit of Material Design Icons that THIRD-PARTY.md names. Curve data and
// nothing else: no package, no runtime, no code.
//
// The seventh is close, and it is the only one this phase needed. It is not a
// new glyph in this repository either: the administration page has rendered the
// same curve on the button that removes a folder exclusion since phase 4, so
// THIRD-PARTY.md gains no row and the check loop gains no name, only the count
// in its sentence about this file moves.
$chevronLeftIcon = 'M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z';
$chevronRightIcon = 'M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z';
$fileSearchIcon = 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H13C12.59,21.75 12.2,21.44 11.86,21.1C11.53,20.77 11.25,20.4 11,20H6V4H13V9H18V10.18C18.71,10.34 19.39,10.61 20,11V8L14,2M20.31,18.9C21.64,16.79 21,14 18.91,12.68C16.8,11.35 14,12 12.69,14.08C11.35,16.19 12,18.97 14.09,20.3C15.55,21.23 17.41,21.23 18.88,20.32L22,23.39L23.39,22L20.31,18.9M16.5,19A2.5,2.5 0 0,1 14,16.5A2.5,2.5 0 0,1 16.5,14A2.5,2.5 0 0,1 19,16.5A2.5,2.5 0 0,1 16.5,19Z';
$magnifyIcon = 'M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z';
$alertIcon = 'M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z';
$infoIcon = 'M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z';
$closeIcon = 'M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z';

// The parameter set, read defensively. The controller hands over nineteen keys
// with checked types; reading them this way costs nothing and keeps a template
// that is opened with a half filled array from turning a missing key into a
// warning in the middle of the markup.
$query = is_string($_['query'] ?? null) ? $_['query'] : '';
$titleOnly = ($_['titleOnly'] ?? false) === true;
$page = is_int($_['page'] ?? null) ? $_['page'] : 1;
$maxPage = is_int($_['maxPage'] ?? null) ? $_['maxPage'] : 1;
$hits = is_array($_['hits'] ?? null) ? $_['hits'] : [];
$hasMore = ($_['hasMore'] ?? false) === true;
$degraded = ($_['degraded'] ?? false) === true;
$failure = is_string($_['failure'] ?? null) ? $_['failure'] : null;
$previousUrl = is_string($_['previousUrl'] ?? null) ? $_['previousUrl'] : null;
$nextUrl = is_string($_['nextUrl'] ?? null) ? $_['nextUrl'] : null;
$formAction = is_string($_['formAction'] ?? null) ? $_['formAction'] : '';

// The parts of the filter row, and every one of them arrives finished. Which
// chip is active, where it leads and whether there is a reset link at all are
// decisions of the controller; this file puts the words to them and decides
// none of them a second time.
$typeChips = is_array($_['typeChips'] ?? null) ? $_['typeChips'] : [];
$rangeChips = is_array($_['rangeChips'] ?? null) ? $_['rangeChips'] : [];
$sortLinks = is_array($_['sortLinks'] ?? null) ? $_['sortLinks'] : [];
$resetUrl = is_string($_['resetUrl'] ?? null) ? $_['resetUrl'] : null;
$filtersActive = ($_['filtersActive'] ?? false) === true;
$showModified = ($_['showModified'] ?? false) === true;

// The same filters once more, in the shape the search form needs: the five
// values it carries as hidden fields, already canonicalised, already without
// the ones nobody set and already without the default order. Read one by one
// and not walked over, because the field names have to stand in this file as
// literals: a loop would hide from every reader and from every gate which five
// names this form can send.
$formFilters = is_array($_['formFilters'] ?? null) ? $_['formFilters'] : [];
$filterTypes = is_string($formFilters['types'] ?? null) ? $formFilters['types'] : '';
$filterSort = is_string($formFilters['sort'] ?? null) ? $formFilters['sort'] : '';
$filterRange = is_string($formFilters['range'] ?? null) ? $formFilters['range'] : '';
$filterSince = is_string($formFilters['since'] ?? null) ? $formFilters['since'] : '';
$filterUntil = is_string($formFilters['until'] ?? null) ? $formFilters['until'] : '';

$hasQuery = $query !== '';

// The words of the ten chips and the three sort links, as a map from the wire
// name to its label.
//
// The map stands in the template and not in the controller because the
// extraction of the catalogues reads literal strings at the call site: a
// $l->t() over a variable is a key no extractor ever sees, and the sentence
// would then ship in English in every language. So the page knows six group
// names, four range names and three order names, and it knows not one file
// extension: those live in the backend, in one place, and a second type
// vocabulary in PHP is exactly what the research of this phase forbids.
$typeLabels = [
	'pdf' => $l->t('PDF'),
	'documents' => $l->t('Documents'),
	'spreadsheets' => $l->t('Spreadsheets'),
	'presentations' => $l->t('Presentations'),
	'images' => $l->t('Images'),
	'text' => $l->t('Text'),
];
$rangeLabels = [
	'today' => $l->t('Today'),
	'week' => $l->t('Last 7 days'),
	'month' => $l->t('Last 30 days'),
	'year' => $l->t('This year'),
];
$sortLabels = [
	'relevance' => $l->t('Relevance'),
	'newest' => $l->t('Last modified'),
	'oldest' => $l->t('Oldest first'),
];

// Which of the two banner kinds this request gets, decided once and here.
// Never both: the error block wins over the hint, because a page that says at
// the same time "the search is not answering" and "the index is still being
// built" says nothing at all.
$silent = $failure === \OCA\Findling\Service\SearchOutcome::FAILURE_BACKEND_SILENT;
$drift = $failure === \OCA\Findling\Service\SearchOutcome::FAILURE_VERSION_DRIFT;
$noHome = $failure === \OCA\Findling\Service\SearchOutcome::FAILURE_NO_HOME_FOLDER;
$ceiling = $failure === \OCA\Findling\Service\SearchOutcome::FAILURE_OFFSET_CEILING;

// The fifth state, and the one that deliberately enters neither of the two sums
// below. It is the only reason that says the search happened and went all the
// way, so a banner over it would ask the user to wait while the sentence under
// it tells them there is nothing left to wait for. That contradiction on one
// screen is exactly what the gate of phase 9 forbids, so this state speaks in
// the empty block and nowhere else (DI-07-03, decided as V-1a on 10.09.2026).
$allRejected = $failure === \OCA\Findling\Service\SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED;
$hasError = $silent || $drift || $noHome;
$hasHint = !$hasError && ($ceiling || $degraded);

// Whether the empty state is allowed to speak, decided here next to the banner
// it depends on (bug audit A of phase 9, 09.09.2026).
//
// With a term the empty state says "no file contains X", and that is a statement
// about a search that happened and came back with nothing. If a banner above it
// already says that the search did not happen at all (silent backend, version
// drift, no home folder) or that it did not go all the way (the paging ceiling,
// an index still being built), then the sentence is not true, and the two blocks
// contradict each other on one screen: "the search is not answering right now"
// over "no file contains X, try another word". The first asks the user to wait,
// the second sends them off to rewrite their term. Whichever of the two they
// believe, the page has misled them.
//
// Without a term the empty state is an invitation and never a claim, so it
// stands under either banner. That is why this is not simply the absence of a
// banner: a page that a hint reached before the user typed anything must still
// say what it is for.
$showEmpty = $hits === [] && (!$hasQuery || (!$hasError && !$hasHint));

// Where "try again" points. The address of this request, asked of the framework
// rather than read out of the server array, and only when it is a path of this
// instance: a reference that begins with two slashes is a protocol relative
// address and would send somebody who wanted to retry a search to a host of
// somebody else's choosing. Anything else falls back to the address of the
// form, which is the same search from the top.
$here = \OCP\Server::get(\OCP\IRequest::class)->getRequestUri();
$retryUrl = ($here !== '' && $here[0] === '/' && !str_starts_with($here, '//')) ? $here : $formAction;

// The longest term the field accepts, read from the constant the controller
// clamps against rather than written out a second time. Two copies of the same
// number are two numbers, and they drift.
$maxQueryLength = \OCA\Findling\Controller\PageController::MAX_QUERY_LENGTH;

// The pagination shows up when there is a neighbouring page, and also on the
// last page that still reports more, because there the hint line about the
// ceiling takes the place of the forward link. Not tied to the hit list: a page
// that approved nothing still needs its way back.
$showPager = $previousUrl !== null || $nextUrl !== null || ($page >= $maxPage && $hasMore);
?>
<div class="findling-search">

	<?php /* Block 1: the head. Exactly one h1 on this page, and without a term
	         it is the title of the empty state below, which is why that block
	         does not repeat it. The form carries neither page nor cursors, so
	         every new search starts on page one. */ ?>
	<div class="findling-search__head">
		<h1 class="findling-search__title">
			<?php if ($hasQuery) { ?>
				<?php p($l->t('Results for "%s"', [$query])); ?>
			<?php } else { ?>
				<?php p($l->t('Search your file contents')); ?>
			<?php } ?>
		</h1>

		<form class="findling-search__form" method="get" action="<?php p($formAction); ?>">
			<div class="findling-search__field">
				<label for="findling-search-query"><?php p($l->t('Search term')); ?></label>
				<input type="text" id="findling-search-query" name="query" maxlength="<?php p((string)$maxQueryLength); ?>"
					autocomplete="off" value="<?php p($query); ?>"
					placeholder="<?php p($l->t('invoice 2026')); ?>"<?php if (!$hasQuery) { ?> autofocus<?php } ?>>
			</div>

			<?php /* A plain native checkbox and no core class: the class of the
			         server hides the input and draws a substitute out of the
			         label, which is a contract this page cannot verify against
			         three server versions offline. The label belongs to the box
			         by for and id, which is what the accessibility contract
			         asks for. */ ?>
			<div class="findling-search__filter">
				<input type="checkbox" id="findling-search-names" name="names" value="1"<?php if ($titleOnly) { ?> checked<?php } ?>>
				<label for="findling-search-names"><?php p($l->t('Search file names only')); ?></label>
			</div>

			<?php /* The active filters travel with the term, as hidden fields and
			         not as a second address. Somebody who makes their term more
			         precise keeps their narrowing and lands on page one, which is
			         where a new term belongs: the position is deliberately absent
			         here, there is no page, no cursors and no fingerprint in this
			         form, because the first screen of the new result is the only
			         screen that exists yet.

			         A value nobody set is not rendered at all rather than sent as
			         an empty field, so the address after the submit stays as short
			         as the selection. The controller decided which of the five
			         that is; this file only asks whether there is anything to
			         write. */ ?>
			<?php if ($filterTypes !== '') { ?>
				<input type="hidden" name="types" value="<?php p($filterTypes); ?>">
			<?php } ?>
			<?php if ($filterSort !== '') { ?>
				<input type="hidden" name="sort" value="<?php p($filterSort); ?>">
			<?php } ?>
			<?php if ($filterRange !== '') { ?>
				<input type="hidden" name="range" value="<?php p($filterRange); ?>">
			<?php } ?>
			<?php if ($filterSince !== '') { ?>
				<input type="hidden" name="since" value="<?php p($filterSince); ?>">
			<?php } ?>
			<?php if ($filterUntil !== '') { ?>
				<input type="hidden" name="until" value="<?php p($filterUntil); ?>">
			<?php } ?>

			<button type="submit" class="primary findling-search__submit">
				<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($magnifyIcon); ?>"/></svg>
				<span><?php p($l->t('Search')); ?></span>
			</button>
		</form>
	</div>

	<?php /* Block 2: the banner line. One of the two kinds or neither, never
	         both. The block of a missing home folder carries the heading of the
	         drift block and no sentence of its own, because the only sentence
	         the copy contract holds for that heading talks about versions, and
	         a page that names the wrong cause sends an administrator after a
	         problem nobody has. The copy table is closed: what is not in it is
	         not on this page. */ ?>
	<?php if ($hasError) { ?>
		<div class="findling-banner findling-banner--error">
			<svg class="findling-banner__icon" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($alertIcon); ?>"/></svg>
			<div class="findling-banner__body">
				<p class="findling-banner__heading">
					<?php if ($silent) { ?>
						<?php p($l->t('The search is not answering right now')); ?>
					<?php } else { ?>
						<?php p($l->t('Findling is not ready to search')); ?>
					<?php } ?>
				</p>
				<?php if ($silent) { ?>
					<p><?php p($l->t('Findling could not reach its backend. Your files are unchanged. Try again in a moment, and tell your administrator if it stays that way.')); ?></p>
					<p><a class="findling-banner__retry" href="<?php p($retryUrl); ?>"><?php p($l->t('Try again')); ?></a></p>
				<?php } elseif ($drift) { ?>
					<p><?php p($l->t('The two halves of Findling report different versions. Your administrator has to update both together.')); ?></p>
				<?php } ?>
			</div>
		</div>
	<?php } elseif ($hasHint) { ?>
		<p class="findling-banner findling-banner--info">
			<svg class="findling-banner__icon" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($infoIcon); ?>"/></svg>
			<span>
				<?php if ($ceiling) { ?>
					<?php p($l->t('More results exist. Narrow the search to see them.')); ?>
				<?php } else { ?>
					<?php p($l->t('The index is still being built, so results can be missing.')); ?>
				<?php } ?>
			</span>
		</p>
	<?php } ?>

	<?php /* Block 2b: the filter row, and it is the sixth block of this page.
	         Fourteen controls, and every single one of them is an ordinary link
	         carrying a finished address out of the controller, so the whole row
	         works with script switched off and a middle click opens any of them
	         in a tab. There is no select, no second form and no listener on this
	         page: a click on a chip is a navigation like every other one here.

	         Only with a term, and that is the whole condition. Without one there
	         is no set that could be narrowed, so ten chips over an invitation
	         would be ten switches with nothing behind them. With a term the row
	         stands even when the search returned nothing and even under a
	         banner, because that is exactly where the way back out of a filter
	         is needed.

	         All ten chips are always here, including the ones behind which there
	         is not a single hit. No count, no dot and no greyed out chip: all
	         three would be the same piece of information, and it would be a
	         counting oracle in front of the permission decision (T-13-42). A
	         chip over an empty group looks like every other chip and leads to
	         the empty state. */ ?>
	<?php if ($hasQuery) { ?>
		<div class="findling-filters">
			<?php /* Three rows, three visible labels, three groups. The label is
			         a span and never a heading, because this page has exactly one
			         first level heading and the row is not a section of it; it is
			         the accessible name of its group at the same time, so what is
			         read out is what is on the screen and there is no second,
			         invisible truth. The group is a div with role group and not a
			         list, because the chips are a set of switches and not an
			         enumeration, and not a nav either, because three navigation
			         landmarks on one page make the landmark list useless. */ ?>
			<div class="findling-filters__row">
				<span class="findling-filters__label" id="findling-filter-types"><?php p($l->t('File type')); ?></span>
				<div class="findling-filters__group" role="group" aria-labelledby="findling-filter-types">
					<?php /* The active chip is ONE stop of the keyboard and not two.
					         It carries the meaning "remove this filter" itself instead
					         of nesting a button of its own, which would be invalid
					         markup and a second tab stop for every active filter. Its
					         accessible name contains its visible text, so somebody who
					         says "PDF" into a voice control hits this chip (WCAG 2.5.3).

					         Why the state is written as aria-current and not as the
					         pressed marker of a button: that marker belongs to a
					         button role, an a element with an href is a link, and a
					         pressed link is nothing. What is announced here is "this
					         one of the group is the one in force", and that is what
					         aria-current means. The state never rests on colour alone:
					         area, close symbol and the announcement are three carriers
					         for one fact. */ ?>
					<?php foreach ($typeChips as $chip) {
						$chipKey = is_string($chip['key'] ?? null) ? $chip['key'] : '';
						$chipUrl = is_string($chip['url'] ?? null) ? $chip['url'] : '';
						$chipActive = ($chip['active'] ?? false) === true;
						$chipLabel = is_string($typeLabels[$chipKey] ?? null) ? $typeLabels[$chipKey] : $chipKey;
						?>
						<?php if ($chipActive) { ?>
							<a class="findling-chip-link findling-chip-link--active" aria-current="true"
								aria-label="<?php p($l->t('Remove filter %s', [$chipLabel])); ?>" href="<?php p($chipUrl); ?>">
								<span><?php p($chipLabel); ?></span>
								<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($closeIcon); ?>"/></svg>
							</a>
						<?php } else { ?>
							<a class="findling-chip-link" href="<?php p($chipUrl); ?>"><span><?php p($chipLabel); ?></span></a>
						<?php } ?>
					<?php } ?>
				</div>
			</div>

			<div class="findling-filters__row">
				<span class="findling-filters__label" id="findling-filter-range"><?php p($l->t('Time range')); ?></span>
				<div class="findling-filters__group" role="group" aria-labelledby="findling-filter-range">
					<?php foreach ($rangeChips as $chip) {
						$chipKey = is_string($chip['key'] ?? null) ? $chip['key'] : '';
						$chipUrl = is_string($chip['url'] ?? null) ? $chip['url'] : '';
						$chipActive = ($chip['active'] ?? false) === true;
						$chipLabel = is_string($rangeLabels[$chipKey] ?? null) ? $rangeLabels[$chipKey] : $chipKey;
						?>
						<?php if ($chipActive) { ?>
							<a class="findling-chip-link findling-chip-link--active" aria-current="true"
								aria-label="<?php p($l->t('Remove filter %s', [$chipLabel])); ?>" href="<?php p($chipUrl); ?>">
								<span><?php p($chipLabel); ?></span>
								<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($closeIcon); ?>"/></svg>
							</a>
						<?php } else { ?>
							<a class="findling-chip-link" href="<?php p($chipUrl); ?>"><span><?php p($chipLabel); ?></span></a>
						<?php } ?>
					<?php } ?>
				</div>

				<?php /* The last element of the time row, and it is there only when
				         something is actually narrowed. A bound that came out of the
				         search dialog highlights no chip at all and still brings this
				         link out, so there is no state in which the page shows less
				         than it searches (FILT-04). */ ?>
				<?php if ($resetUrl !== null) { ?>
					<a class="findling-filters__reset" href="<?php p($resetUrl); ?>"><?php p($l->t('Reset all filters')); ?></a>
				<?php } ?>
			</div>

			<div class="findling-filters__row">
				<span class="findling-filters__label" id="findling-filter-sort"><?php p($l->t('Sort by')); ?></span>
				<?php /* Three links, always all three, always exactly one of them in
				         force. The link of the active one points at the view that is
				         already on the screen, and that is not a dead link but the
				         ordinary state of a segmented switch: the whole set of
				         choices can be read off the row instead of being remembered. */ ?>
				<div class="findling-sort" role="group" aria-labelledby="findling-filter-sort">
					<?php foreach ($sortLinks as $link) {
						$sortKey = is_string($link['key'] ?? null) ? $link['key'] : '';
						$sortUrl = is_string($link['url'] ?? null) ? $link['url'] : '';
						$sortActive = ($link['active'] ?? false) === true;
						$sortLabel = is_string($sortLabels[$sortKey] ?? null) ? $sortLabels[$sortKey] : $sortKey;
						?>
						<?php if ($sortActive) { ?>
							<a class="findling-sort__link findling-sort__link--active" aria-current="true" href="<?php p($sortUrl); ?>"><?php p($sortLabel); ?></a>
						<?php } else { ?>
							<a class="findling-sort__link" href="<?php p($sortUrl); ?>"><?php p($sortLabel); ?></a>
						<?php } ?>
					<?php } ?>
				</div>
			</div>
		</div>
	<?php } ?>

	<?php /* Block 3: the hit list. One list entry per hit, and the whole row is
	         one link, so a keyboard reaches every hit with a single stop and a
	         middle click opens it in a tab. Ordered, because the order is a
	         ranking. */ ?>
	<?php if ($hits !== []) { ?>
		<ol class="findling-hits" aria-label="<?php p($l->t('Search results')); ?>">
			<?php foreach ($hits as $hit) {
				$hitId = is_int($hit['fileId'] ?? null) ? $hit['fileId'] : 0;
				$title = is_string($hit['title'] ?? null) ? $hit['title'] : '';
				$path = is_string($hit['path'] ?? null) ? $hit['path'] : '';
				$iconUrl = is_string($hit['iconUrl'] ?? null) ? $hit['iconUrl'] : '';
				$url = is_string($hit['url'] ?? null) ? $hit['url'] : '';
				$segments = is_array($hit['segments'] ?? null) ? $hit['segments'] : [];
				$modified = is_string($hit['modified'] ?? null) ? $hit['modified'] : '';
				// Whether this row carries its date, and one answer serves the
				// visible line and the spoken name alike. Under relevance the
				// line does not exist, neither empty nor hidden, because a date
				// under relevance would be the one number on this page a reader
				// could mistake for a measure of how well a hit fits (D-04).
				$dated = $showModified && $modified !== '';
				?>
				<li class="findling-hit" id="findling-hit-<?php p((string)$hitId); ?>">
					<?php /* Two forms of one name, and the second one exists because
					         an aria-label REPLACES the content for a screen reader:
					         without the dated form the date would be inaudible under
					         exactly the order that is about dates. */ ?>
					<a class="findling-hit__link" href="<?php p($url); ?>" target="_self"
						aria-label="<?php p($dated ? $l->t('%1$s in %2$s, modified on %3$s', [$title, $path, $modified]) : $l->t('%1$s in %2$s', [$title, $path])); ?>">
						<img class="findling-hit__icon" src="<?php p($iconUrl); ?>" width="32" height="32" alt="" aria-hidden="true">
						<span class="findling-hit__text">
							<span class="findling-hit__title"><?php p($title); ?></span>
							<span class="findling-hit__path"><?php p($path); ?></span>
							<?php /* A line of its own under the path and above the
							         excerpt, never appended to the path: the path is
							         one line with an ellipsis, so an appendix would be
							         the first thing to be cut off. */ ?>
							<?php if ($dated) { ?>
								<span class="findling-hit__modified"><?php p($l->t('Modified on %s', [$modified])); ?></span>
							<?php } ?>
							<?php if ($segments !== []) { ?>
								<span class="findling-hit__excerpt"><?php foreach ($segments as $segment) {
									$text = is_string($segment['text'] ?? null) ? $segment['text'] : '';
									if (($segment['mark'] ?? false) === true) { ?><mark><?php p($text); ?></mark><?php } else {
										p($text);
									}
								} ?></span>
							<?php } ?>
							<?php /* Rendered here and switched on by the script, so that the
							         one sentence a screen reader hears on this page comes out
							         of the translation catalogue and not out of a string in
							         JavaScript. */ ?>
							<span class="hidden-visually findling-hit__returned" hidden><?php p($l->t('last opened')); ?></span>
						</span>
					</a>
				</li>
			<?php } ?>
		</ol>
	<?php } elseif ($showEmpty) { ?>
		<?php /* Block 4: the empty state. It replaces the list and never stands
		         beside it, and it stays away entirely when a banner above has
		         already explained the emptiness: see $showEmpty. Without a term
		         the heading of this block is the h1 above, which is what keeps
		         the page at exactly one first level heading.

		         With a term and without a filter the heading is true in both
		         variants and therefore does not move; only the line under it
		         does. The second of those two belongs to $allRejected and is
		         the whole of DI-07-03: this run was handed candidates and kept
		         none of them, so the old line would send the user off to
		         rewrite a term that was never the problem.

		         The third variant with a term belongs to an active filter, and
		         it is a BRANCH IN HERE and never a block beside it. Beside it,
		         "no results with the active filters" would stand over a banner
		         that says the search is not answering at all, which is the very
		         contradiction $showEmpty exists to prevent. The filter row above
		         stays on the screen in this state, so the way back out of the
		         filter is visible while this block speaks.

		         And it wins over the $allRejected variant while a filter is in
		         force. Both sentences are true in that state, but only one of
		         them names a lever the visitor holds: "other files contain this
		         word, but none that you may open" has no next step, "remove a
		         filter" has one, and it is one click away and reversible.
		         Without an active filter the $allRejected variant is unchanged
		         the one from V-1a.

		         No variant names a file, a path or a number. A count of the
		         dropped candidates would let anybody measure a stranger's
		         folder one term at a time (T-11-50), and the filter variant
		         never says how many hits another filter would have had, for
		         exactly the same reason. Neither of them says a word about
		         permissions. */ ?>
		<div class="findling-empty">
			<?php if ($hasQuery) { ?>
				<svg class="findling-empty__icon" viewBox="0 0 24 24" width="64" height="64" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($fileSearchIcon); ?>"/></svg>
				<?php if ($filtersActive) { ?>
					<h2 class="findling-empty__heading"><?php p($l->t('No results with the active filters')); ?></h2>
					<p class="findling-empty__text"><?php p($l->t('Remove a filter or widen the time range.')); ?></p>
					<?php /* One decision of the controller, read twice: the reset
					         link exists exactly when a filter is in force, so this
					         second question can only be answered yes here. It is
					         asked anyway because the sentence above promises a next
					         step, and a promise without the link would be the one
					         empty state on this page with no way out of itself. */ ?>
					<?php if ($resetUrl !== null) { ?>
						<p><a class="findling-empty__reset" href="<?php p($resetUrl); ?>"><?php p($l->t('Reset filters')); ?></a></p>
					<?php } ?>
				<?php } else { ?>
					<h2 class="findling-empty__heading"><?php p($l->t('No file contains "%s"', [$query])); ?></h2>
					<?php if ($allRejected) { ?>
						<p class="findling-empty__text"><?php p($l->t('Other files contain this word, but none that you may open.')); ?></p>
					<?php } else { ?>
						<p class="findling-empty__text"><?php p($l->t('Try another word, a part of a compound word, or check the spelling.')); ?></p>
					<?php } ?>
				<?php } ?>
			<?php } else { ?>
				<svg class="findling-empty__icon" viewBox="0 0 24 24" width="64" height="64" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($magnifyIcon); ?>"/></svg>
				<p class="findling-empty__text"><?php p($l->t('Type a word from a document. Findling searches the text inside your files, scanned PDFs included.')); ?></p>
			<?php } ?>
		</div>
	<?php } ?>

	<?php /* Block 5: the pagination. Two ordinary links with the look of a
	         button, so that they work without script and a middle click opens a
	         tab. No total, no page count and no jump to the last page: all three
	         would need a sum nobody measured. */ ?>
	<?php if ($showPager) { ?>
		<div class="findling-pager">
			<div class="findling-pager__row">
				<?php if ($previousUrl !== null) { ?>
					<a class="findling-pager__step findling-pager__step--previous" href="<?php p($previousUrl); ?>">
						<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($chevronLeftIcon); ?>"/></svg>
						<span><?php p($l->t('Previous page')); ?></span>
					</a>
				<?php } ?>

				<span class="findling-pager__mark"><?php p($l->t('Page %s', [(string)$page])); ?></span>

				<?php if ($nextUrl !== null) { ?>
					<a class="findling-pager__step findling-pager__step--next" href="<?php p($nextUrl); ?>">
						<span><?php p($l->t('Next page')); ?></span>
						<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($chevronRightIcon); ?>"/></svg>
					</a>
				<?php } ?>
			</div>

			<?php if ($nextUrl === null && $page >= $maxPage && $hasMore) { ?>
				<p class="findling-pager__hint">
					<svg class="findling-banner__icon" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($infoIcon); ?>"/></svg>
					<span><?php p($l->t('More results exist. Narrow the search to see them.')); ?></span>
				</p>
			<?php } ?>
		</div>
	<?php } ?>

</div>
