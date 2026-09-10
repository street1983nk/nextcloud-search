<?php

declare(strict_types=1);

/**
 * The result page of Findling: head, banner, hit list, empty state, pagination.
 *
 * Every one of the five blocks below is rendered server side with the real
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
 * @var array<string,mixed> $_ the eleven parameters of PageController::index(), verbatim
 * @var \OCP\IL10N $l
 */

// The two calls belong here and not into the controller. The template is
// rendered before the layout collects its resource lists, so a call from the
// controller would arrive too late and the page would be served without either
// file. Same reason, same place as on the administration page.
\OCP\Util::addScript('findling', 'search');
\OCP\Util::addStyle('findling', 'search');

// The six path data of the page, taken word for word from the pinned upstream
// commit of Material Design Icons that THIRD-PARTY.md names. Curve data and
// nothing else: no package, no runtime, no code.
$chevronLeftIcon = 'M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z';
$chevronRightIcon = 'M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z';
$fileSearchIcon = 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H13C12.59,21.75 12.2,21.44 11.86,21.1C11.53,20.77 11.25,20.4 11,20H6V4H13V9H18V10.18C18.71,10.34 19.39,10.61 20,11V8L14,2M20.31,18.9C21.64,16.79 21,14 18.91,12.68C16.8,11.35 14,12 12.69,14.08C11.35,16.19 12,18.97 14.09,20.3C15.55,21.23 17.41,21.23 18.88,20.32L22,23.39L23.39,22L20.31,18.9M16.5,19A2.5,2.5 0 0,1 14,16.5A2.5,2.5 0 0,1 16.5,14A2.5,2.5 0 0,1 19,16.5A2.5,2.5 0 0,1 16.5,19Z';
$magnifyIcon = 'M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z';
$alertIcon = 'M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z';
$infoIcon = 'M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z';

// The parameter set, read defensively. The controller hands over eleven keys
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

$hasQuery = $query !== '';

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
				?>
				<li class="findling-hit" id="findling-hit-<?php p((string)$hitId); ?>">
					<a class="findling-hit__link" href="<?php p($url); ?>" target="_self"
						aria-label="<?php p($l->t('%1$s in %2$s', [$title, $path])); ?>">
						<img class="findling-hit__icon" src="<?php p($iconUrl); ?>" width="32" height="32" alt="" aria-hidden="true">
						<span class="findling-hit__text">
							<span class="findling-hit__title"><?php p($title); ?></span>
							<span class="findling-hit__path"><?php p($path); ?></span>
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

		         With a term the heading is true in both variants and therefore
		         does not move; only the line under it does. The second variant
		         belongs to $allRejected and is the whole of DI-07-03: this run
		         was handed candidates and kept none of them, so the old line
		         would send the user off to rewrite a term that was never the
		         problem.

		         Neither variant names a file, a path or a number. A count of
		         the dropped candidates would let anybody measure a stranger's
		         folder one term at a time (T-11-50); the sentence says only
		         what every user of a shared instance knows anyway, and it says
		         nothing at all about which files those are. */ ?>
		<div class="findling-empty">
			<?php if ($hasQuery) { ?>
				<svg class="findling-empty__icon" viewBox="0 0 24 24" width="64" height="64" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($fileSearchIcon); ?>"/></svg>
				<h2 class="findling-empty__heading"><?php p($l->t('No file contains "%s"', [$query])); ?></h2>
				<?php if ($allRejected) { ?>
					<p class="findling-empty__text"><?php p($l->t('Other files contain this word, but none that you may open.')); ?></p>
				<?php } else { ?>
					<p class="findling-empty__text"><?php p($l->t('Try another word, a part of a compound word, or check the spelling.')); ?></p>
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
