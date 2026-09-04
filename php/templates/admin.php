<?php

declare(strict_types=1);

/**
 * Block one of the administration page: what is true about the search now.
 *
 * Rendered server side with the real numbers, and that is a requirement rather
 * than a style: with JavaScript switched off this block has to stay fully
 * legible, so there is no skeleton, no loading state and no placeholder
 * anywhere below. The script of this app replaces text nodes in place; it never
 * builds this markup, which is why every element it updates carries an id.
 *
 * Every visible string runs through $l->t(). Every value that could carry data
 * somebody else wrote is printed with p() and never with the unescaped printer.
 * There is no inline script, because the Nextcloud CSP blocks one, and no style
 * attribute, because one would ignore the theme.
 *
 * @var array<string,mixed> $_ the overview of AdminViewService, verbatim
 * @var \OCP\IL10N $l
 */

// The two calls belong here and not into Admin::getForm(). The template is
// rendered before the layout collects its resource lists, so a call from the
// settings class would arrive too late and the page would be served without
// either file.
\OCP\Util::addScript('findling', 'admin');
\OCP\Util::addStyle('findling', 'admin');

// Fetched from the container rather than passed in as a parameter, and the
// reason is the initial state: Admin::getForm() hands the same array to this
// template and to provideInitialState(), which encodes it as JSON, so the array
// cannot carry an object. The formatter is what turns a timestamp into the
// sentence a human reads, in the admin's own language.
$formatter = \OCP\Server::get(\OCP\IDateTimeFormatter::class);

$backend = is_array($_['backend'] ?? null) ? $_['backend'] : [];
$whole = static fn (mixed $value): int => is_int($value) && $value >= 0 ? $value : 0;

$coverage = is_array($_['coverage'] ?? null) ? $_['coverage'] : [];

$indexable = $whole($coverage['indexable'] ?? 0);
$searchable = $whole($coverage['indexed'] ?? 0);
$leftOut = $whole($coverage['deliberatelyLeftOut'] ?? 0);
// Null and not zero when no honest percentage exists, which is why this one is
// not read through $whole: nought is a claim here and null is the absence of
// one.
$percent = is_int($coverage['percent'] ?? null) ? $coverage['percent'] : null;
$provisional = ($coverage['provisional'] ?? false) === true;
$mountsTotal = $whole($coverage['mountsTotal'] ?? 0);
$mountsFinished = $whole($coverage['mountsFinished'] ?? 0);

$indexed = $whole($_['indexedDisplay'] ?? 0);
$scheduled = $whole($_['scheduled'] ?? 0);
$running = $whole($_['running'] ?? 0);
$lastJobRun = $whole($_['lastJobRun'] ?? 0);
$stalledFor = $whole($_['stalledFor'] ?? 0);
$runState = is_string($_['runState'] ?? null) ? $_['runState'] : 'never_run';
$reachable = ($_['backendReachable'] ?? false) === true;

// The lockstep verdict of D-11, and the three states it can hold. Only "drift"
// shows anything: "match" is the normal case and "unknown" is a container that
// did not say, which the page must not turn into a claim about the pair.
$lockstep = is_array($_['lockstep'] ?? null) ? $_['lockstep'] : [];
$lockstepState = is_string($lockstep['state'] ?? null) ? $lockstep['state'] : 'unknown';
// Both numbers have passed the version pattern of ExAppService before they got
// here, and they are printed with the escaping printer all the same.
$companionVersion = is_string($lockstep['companion'] ?? null) ? $lockstep['companion'] : '';
$containerVersion = is_string($lockstep['container'] ?? null) ? $lockstep['container'] : '';

/**
 * A count in the admin's own notation, with the thousands separator of their
 * locale. The script formats the same numbers with Intl.NumberFormat, so both
 * halves of the page agree on what twelve thousand looks like.
 *
 * The guard is there because the intl extension is recommended and not
 * required by Nextcloud. Without it the number is printed plainly, which is
 * ugly and correct, and never an error.
 */
$count = static function (int $value) use ($l): string {
	if (!class_exists('NumberFormatter')) {
		return (string)$value;
	}

	$formatted = (new NumberFormatter($l->getLocaleCode(), NumberFormatter::DECIMAL))->format($value);

	return $formatted === false ? (string)$value : $formatted;
};

/**
 * A duration as one grain, never two.
 *
 * "Half an hour" is what an admin needs in order to decide whether the
 * indexing is stuck; "32 minutes and 14 seconds" is noise that changes on every
 * poll. Minutes are the smallest grain because the threshold behind the stalled
 * state is measured in them, and a floor of one minute keeps the sentence from
 * reading "for 0 minutes".
 */
$span = static function (int $seconds) use ($l): string {
	if ($seconds >= 86400) {
		return $l->n('%n day', '%n days', intdiv($seconds, 86400));
	}
	if ($seconds >= 3600) {
		return $l->n('%n hour', '%n hours', intdiv($seconds, 3600));
	}

	return $l->n('%n minute', '%n minutes', max(1, intdiv($seconds, 60)));
};

// The status line, one sentence per run state and never green while nothing
// moves forward.
//
// The running case deliberately carries no estimate of the time left. The
// design contract forbids a guessed figure that looks like a measurement, and
// the throughput this app would need in order to estimate honestly is
// calibrated by a later plan. Until then the sentence says what is known, and
// the work stock below it says how much is waiting.
$status = match ($runState) {
	'running' => $l->t('Indexing is running.'),
	'idle' => $l->t('Up to date, last checked %s', [$formatter->formatTimeSpan($lastJobRun)]),
	// Both halves are named, because since plan 05-20 both of them have to have
	// stood still for this sentence to appear: the background jobs of this app
	// and the backend that keeps writing documents long after the last crawl.
	// Blaming the jobs alone was true of the measure and false of the situation,
	// and on the target hardware it was false for most of a run (DI-05-22).
	'stalled' => $l->t('Indexing has not progressed for %s. Neither a background job nor the backend finished anything in that time.', [$span($stalledFor)]),
	default => $l->t('No background job of this app has run yet. Background jobs may not be running.'),
};

// Which of the three shapes of the coverage block is the true one right now.
// All three are in the markup and the two that do not apply carry the hidden
// attribute, the same way the banners below do. The script then only flips an
// attribute and writes text nodes, so a figure that becomes available while the
// page is open appears without the script owning any markup. Nothing hidden is
// a skeleton either: the hidden elements hold real values, they are simply not
// the answer at this moment.
//
// The one rule behind all of it: no percentage without a named denominator, and
// a division by zero is never sold as nought per cent.
$hasDenominator = $indexable > 0;
$hasFraction = $hasDenominator && $percent !== null;

$tiles = [
	['id' => 'findling-tile-indexed', 'label' => $l->t('Indexed'), 'value' => $indexed],
	['id' => 'findling-tile-skipped', 'label' => $l->t('Skipped'), 'value' => $whole($_['skipped'] ?? 0)],
	['id' => 'findling-tile-failed', 'label' => $l->t('Failed'), 'value' => $whole($_['failed'] ?? 0)],
	// Out of the scan counters since this plan, so that the tile and the
	// denominator of the figure above agree on what excluded means.
	['id' => 'findling-tile-excluded', 'label' => $l->t('Excluded'), 'value' => $whole($_['excluded'] ?? 0)],
];

// Icon path data: Material Design Icons by Pictogrammers, Apache-2.0, pinned by
// commit in THIRD-PARTY.md. Data lines and no dependency, which is what keeps
// this app free of a bundler.
$alertIcon = 'M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z';
$clockIcon = 'M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z';

// Every banner is rendered, and the ones that do not apply right now are hidden
// with the hidden attribute rather than left out. The script only has to flip
// the attribute then, so a banner that becomes true while the page is open
// appears without the script owning any markup.
$banners = [
	[
		'id' => 'findling-banner-unreachable',
		'kind' => 'error',
		'icon' => $alertIcon,
		'text' => $l->t('The Findling backend does not answer. The numbers below are the last ones this app recorded. Check under Apps that the External App "Findling Backend" is installed and running.'),
		'shown' => !$reachable,
	],
	[
		// The version break of D-11, and it stands directly under the
		// unreachable banner because the two are the same kind of trouble: the
		// halves of this app are not working together. The sentence names what
		// is true, what follows from it and the one thing that fixes it, with
		// the numbers that were actually reported rather than with a general
		// remark about versions.
		'id' => 'findling-banner-lockstep',
		'kind' => 'error',
		'icon' => $alertIcon,
		'text' => $l->t('The two halves of Findling report different versions: this app is %1$s, the backend is %2$s. While they disagree the search answers with no results, because a wrong answer without a word would be worse. Bring both halves to the same version.', [$companionVersion, $containerVersion]),
		'shown' => $lockstepState === 'drift',
	],
	[
		'id' => 'findling-banner-stale',
		'kind' => 'error',
		'icon' => $alertIcon,
		'text' => $l->t('The numbers could not be refreshed. The figures below are the last ones this page received.'),
		'shown' => false,
	],
	[
		'id' => 'findling-banner-lowdisk',
		'kind' => 'warning',
		'icon' => $alertIcon,
		'text' => $l->t('Little disk space left. Indexing is paused so the index stays intact. Search keeps working.'),
		'shown' => ($backend['lowDisk'] ?? false) === true,
	],
	[
		'id' => 'findling-banner-reindex',
		'kind' => 'warning',
		'icon' => $alertIcon,
		'text' => $l->t('The index was built with an older text analysis. Run "occ findling:index --restart" to rebuild it, otherwise some hits stay missing.'),
		'shown' => ($backend['reindexRequired'] ?? false) === true,
	],
];
?>
<div id="findling-coverage" class="section">
	<h2 id="findling-coverage-heading"><?php p($l->t('Search coverage')); ?></h2>

	<div id="findling-coverage-banners">
		<?php foreach ($banners as $banner) { ?>
			<p class="findling-banner findling-banner--<?php p($banner['kind']); ?>" id="<?php p($banner['id']); ?>"<?php if (!$banner['shown']) { ?> hidden<?php } ?>>
				<svg class="findling-banner__icon" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($banner['icon']); ?>"/></svg>
				<?php
				/*
				 * The text of a banner carries an id of its own, derived from
				 * the id of the banner. The script writes into it rather than
				 * into the paragraph, which holds the icon as well: a
				 * textContent on the paragraph would delete that icon, and a
				 * banner whose sentence changes while the page is open is
				 * exactly what the version state below needs.
				 */
				?>
				<span class="findling-banner__text" id="<?php p($banner['id']); ?>-text"><?php p($banner['text']); ?></span>
			</p>
		<?php } ?>
	</div>

	<p class="findling-figure" id="findling-coverage-figure"<?php if (!$hasFraction) { ?> hidden<?php } ?>>
		<?php
		/*
		 * U+00A0 between the figure and the sign, spelled as an escape on both
		 * sides of the page so that the agreement is visible in a diff (IN-03).
		 * The script writes the same character when it takes over on the first
		 * poll, which is what keeps the number from changing its shape three
		 * seconds after the page opened. Non-breaking because a percent sign
		 * must not wrap onto the next line away from its number; whoever
		 * changes it here changes coverageBlock() in the same commit, and a
		 * test in test_admin_ui_contract.py holds the two together.
		 */
		?>
		<span class="findling-figure__value" id="findling-coverage-percent"><?php p($count($percent ?? 0) . "\u{00A0}%"); ?></span>
	</p>
	<progress id="findling-coverage-bar" max="100" value="<?php p((string)($percent ?? 0)); ?>" aria-labelledby="findling-coverage-heading"<?php if (!$hasFraction) { ?> hidden<?php } ?>></progress>
	<p class="settings-hint" id="findling-coverage-subline"<?php if (!$hasFraction) { ?> hidden<?php } ?>><?php p($l->t('%1$s of %2$s indexable files are searchable', [$count($searchable), $count($indexable)])); ?></p>

	<p class="settings-hint" id="findling-coverage-unknown"<?php if (!$hasDenominator || $hasFraction) { ?> hidden<?php } ?>><?php p($l->t('The share cannot be worked out right now because the backend does not answer. %s files of this instance are indexable.', [$count($indexable)])); ?></p>

	<p class="settings-hint" id="findling-coverage-leftout"<?php if (!$hasDenominator) { ?> hidden<?php } ?>>
		<span id="findling-coverage-leftout-count"><?php p($l->t('Deliberately left out: %s', [$count($leftOut)])); ?></span>
		<?php p($l->t('Those files are too large, of a type Findling does not read, or excluded by a rule. They are not in the denominator above, so the coverage figure can reach a hundred per cent.')); ?>
	</p>

	<p class="settings-hint" id="findling-coverage-provisional"<?php if (!$hasDenominator || !$provisional) { ?> hidden<?php } ?>><?php p($l->t('Provisional figure, %1$s of %2$s storages have been counted through.', [$count($mountsFinished), $count($mountsTotal)])); ?></p>

	<div id="findling-coverage-empty"<?php if ($hasDenominator) { ?> hidden<?php } ?>>
		<h3 class="findling-subheading"><?php p($l->t('No numbers yet')); ?></h3>
		<p class="settings-hint"><?php p($l->t('The first indexing pass has not finished. Findling started on its own, there is nothing to configure.')); ?></p>
	</div>

	<p class="findling-run-state" id="findling-run-state" role="status" aria-live="polite"><?php p($status); ?></p>

	<p class="findling-chips">
		<span class="findling-chip findling-chip--queued">
			<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($clockIcon); ?>"/></svg>
			<span><?php p($l->t('Waiting in the queue')); ?></span>
			<span class="findling-chip__value" id="findling-scheduled"><?php p($count($scheduled)); ?></span>
		</span>
		<span class="findling-chip findling-chip--processing" id="findling-processing-chip"<?php if ($running === 0) { ?> hidden<?php } ?>>
			<span class="icon-loading-small"></span>
			<span><?php p($l->t('Being processed')); ?></span>
			<span class="findling-chip__value" id="findling-running"><?php p($count($running)); ?></span>
		</span>
	</p>

	<ul class="findling-tiles">
		<?php foreach ($tiles as $tile) { ?>
			<li class="findling-tile">
				<span class="findling-tile__value" id="<?php p($tile['id']); ?>"><?php p($count($tile['value'])); ?></span>
				<span class="findling-tile__label"><?php p($tile['label']); ?></span>
			</li>
		<?php } ?>
	</ul>

	<p class="settings-hint"><?php p($l->t('Excluded files are not part of the coverage figure. They are files you told Findling to leave alone.')); ?></p>
</div>
<?php
/*
 * Block two: what the first index still costs.
 *
 * D-05 made visible. There is no confirmation gate anywhere on this page: the
 * first index started on its own, and the last line of this block says so in
 * as many words. The block is informative from minute one and it gets more
 * accurate while the run proceeds, which is why every figure in it is labelled
 * as measured, as a startup value or as provisional.
 *
 * Rendered only while the first index is not through. Afterwards an advance
 * estimate has nothing left to say, so the block does not exist in the markup
 * at all rather than sitting there hidden.
 *
 * Two shapes of the estimate line, and the reason for the second one: the
 * design contract carries one sentence with four placeholders, and two of them
 * are a duration and a size that only exist once something has been measured.
 * A sentence with a hole in it is worse than a shorter sentence, so the full
 * line is used when both figures exist and the short one when they do not, and
 * the missing figure is explained by its own sentence below instead of being
 * guessed at.
 */
$estimate = is_array($_['estimate'] ?? null) ? $_['estimate'] : [];

$estimateFiles = $whole($estimate['files'] ?? 0);
$estimateOcrMin = $whole($estimate['ocrMin'] ?? 0);
$estimateOcrMax = $whole($estimate['ocrMax'] ?? 0);
// Null while the interval is still both numbers moving at once, and a figure
// once the run has measured it. Not read through $whole for that reason: nought
// measured documents is a statement and null is the absence of one.
$estimateOcrMeasured = is_int($estimate['ocrMeasured'] ?? null) ? $estimate['ocrMeasured'] : null;
$estimateSeconds = is_int($estimate['secondsLeft'] ?? null) ? $estimate['secondsLeft'] : null;
$estimateBytes = is_int($estimate['bytesExpected'] ?? null) ? $estimate['bytesExpected'] : null;
$estimateProvisional = ($estimate['provisional'] ?? false) === true;
$estimateStartup = ($estimate['startupValues'] ?? false) === true;
$estimateSpaceWarning = ($estimate['spaceWarning'] ?? false) === true;
$estimateDone = ($estimate['firstIndexDone'] ?? false) === true;
$estimateMountsTotal = $whole($estimate['mountsTotal'] ?? 0);
$estimateMountsFinished = $whole($estimate['mountsFinished'] ?? 0);

/**
 * A size in the notation of this admin, unit and all.
 *
 * Written here rather than taken from Util::humanFileSize, which always puts a
 * full stop before the decimal no matter what the session language is. The
 * script formats the same number with Intl.NumberFormat and the same unit
 * table, so both halves of the page agree on what one and a half gigabytes
 * looks like. The unit names are not translated, in Nextcloud either: they are
 * symbols and they read the same in every language this app ships.
 */
$size = static function (int $bytes) use ($l): string {
	$units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
	$value = (float)max(0, $bytes);
	$unit = 0;
	while ($value >= 1024 && $unit < count($units) - 1) {
		$value /= 1024;
		$unit++;
	}

	// Whole bytes and whole kilobytes, one decimal from megabytes upwards. A
	// tenth of a kilobyte is precision this figure does not have.
	$digits = $unit < 2 ? 0 : 1;
	if (!class_exists('NumberFormatter')) {
		return number_format($value, $digits, '.', '') . ' ' . $units[$unit];
	}

	$formatter = new NumberFormatter($l->getLocaleCode(), NumberFormatter::DECIMAL);
	$formatter->setAttribute(NumberFormatter::FRACTION_DIGITS, $digits);
	$formatted = $formatter->format($value);

	return ($formatted === false ? number_format($value, $digits, '.', '') : $formatted) . ' ' . $units[$unit];
};

// The OCR share: an interval as long as nothing better is known, a single
// figure once the run has measured one. A single guessed percentage would be a
// number without a basis.
$estimateOcrText = $estimateOcrMeasured === null
	? $l->t('%1$s to %2$s', [$count($estimateOcrMin), $count($estimateOcrMax)])
	: $count($estimateOcrMeasured);

// Nothing counted yet means no sentence about files, not a sentence full of
// noughts. "0 files, 0 to 0 of them need OCR" is exactly the placeholder figure
// the design contract forbids for this block; the counting hint below is the
// whole answer in that minute.
$estimateHasFiles = $estimateFiles > 0;
$estimateComplete = $estimateHasFiles && $estimateSeconds !== null && $estimateBytes !== null;
$estimateFullLine = $l->t('%1$s files, %2$s of them need OCR. About %3$s and about %4$s of index.', [
	$count($estimateFiles),
	$estimateOcrText,
	$span($estimateSeconds ?? 0),
	$size($estimateBytes ?? 0),
]);
$estimateShortLine = $l->t('%1$s files, %2$s of them need OCR.', [$count($estimateFiles), $estimateOcrText]);

// Icon path data: Material Design Icons by Pictogrammers, Apache-2.0, pinned by
// commit in THIRD-PARTY.md.
$infoIcon = 'M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z';

if (!$estimateDone) { ?>
<div id="findling-estimate" class="section">
	<h2><?php p($l->t('Estimate for the first index')); ?></h2>

	<p id="findling-estimate-line"<?php if (!$estimateComplete) { ?> hidden<?php } ?>><?php p($estimateFullLine); ?></p>
	<p id="findling-estimate-line-short"<?php if (!$estimateHasFiles || $estimateComplete) { ?> hidden<?php } ?>><?php p($estimateShortLine); ?></p>

	<p class="settings-hint findling-progress-hint" id="findling-estimate-counting"<?php if (!$estimateProvisional) { ?> hidden<?php } ?>>
		<span class="icon-loading-small"></span>
		<span id="findling-estimate-counting-text"><?php p($l->t('Counting the files, this takes a moment.') . ' ' . $l->t('Provisional figure, %1$s of %2$s storages have been counted through.', [$count($estimateMountsFinished), $count($estimateMountsTotal)])); ?></span>
	</p>

	<p class="settings-hint" id="findling-estimate-space-unknown"<?php if (!$estimateHasFiles || $estimateBytes !== null) { ?> hidden<?php } ?>><?php p($l->t('The space needed is measured as soon as the first documents are in the index.')); ?></p>

	<p class="settings-hint" id="findling-estimate-startup"<?php if (!$estimateStartup || $estimateSeconds === null) { ?> hidden<?php } ?>><?php p($l->t('Startup value, being measured.')); ?></p>

	<p class="findling-banner findling-banner--warning" id="findling-estimate-space-warning"<?php if (!$estimateSpaceWarning) { ?> hidden<?php } ?>>
		<svg class="findling-banner__icon" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($infoIcon); ?>"/></svg>
		<span class="findling-banner__text"><?php p($l->t('The index is expected to need more space than this volume has free. Indexing pauses before the volume fills up, and search keeps working.')); ?></span>
	</p>

	<p class="settings-hint"><?php p($l->t('Findling does not wait for a confirmation. The first index has already started.')); ?></p>
</div>
<?php }
/*
 * Block three: which files were not indexed, why, and what changes that.
 *
 * The second half of ADM-01, and the place where a number turns into an action.
 * Every group carries a label, a remedy and up to twenty example paths, and the
 * remedy says "none" out loud where there is none, because an empty cell is
 * indistinguishable from a defect of the page.
 *
 * A real table with a caption and column headers, not a grid of divs: the rows
 * are data with three columns, and a screen reader has to be able to say which
 * column a cell belongs to.
 *
 * Paths are the payload of this list, so they are never shortened and never
 * printed unescaped. A path can contain every character a user can type into a
 * file name, which is why p() is the only printer used below (T-04-30). The
 * expand buttons carry the hidden attribute and are shown by the script: with
 * JavaScript switched off every group stays open and readable, and a control
 * that could not do anything is not offered.
 */
$errors = is_array($_['errors'] ?? null) ? $_['errors'] : [];
$errorGroups = is_array($errors['groups'] ?? null) ? $errors['groups'] : [];

// Icon path data: Material Design Icons by Pictogrammers, Apache-2.0, pinned by
// commit in THIRD-PARTY.md. One per state of the state inventory, so that
// colour is never the only carrier of the verdict.
$skippedIcon = 'M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M7,13H17V11H7';
$failedIcon = $alertIcon;
$truncatedIcon = 'M19,3L13,9L15,11L22,4V3M12,12.5A0.5,0.5 0 0,1 11.5,12A0.5,0.5 0 0,1 12,11.5A0.5,0.5 0 0,1 12.5,12A0.5,0.5 0 0,1 12,12.5M6,20A2,2 0 0,1 4,18C4,16.89 4.9,16 6,16A2,2 0 0,1 8,18C8,19.11 7.1,20 6,20M6,8A2,2 0 0,1 4,6C4,4.89 4.9,4 6,4A2,2 0 0,1 8,6C8,7.11 7.1,8 6,8M9.64,7.64C9.87,7.14 10,6.59 10,6A4,4 0 0,0 6,2A4,4 0 0,0 2,6A4,4 0 0,0 6,10C6.59,10 7.14,9.87 7.64,9.64L10,12L7.64,14.36C7.14,14.13 6.59,14 6,14A4,4 0 0,0 2,18A4,4 0 0,0 6,22A4,4 0 0,0 10,18C10,17.41 9.87,16.86 9.64,16.36L12,14L19,21H22V20L9.64,7.64Z';
$excludedIcon = 'M2.39 1.73L1.11 3L2.64 4.53C2.25 4.9 2 5.42 2 6V18C2 19.11 2.9 20 4 20H18.11L20.84 22.73L22.11 21.46L2.39 1.73M4 18V8H6.11L16.11 18H4M11.2 8L7.2 4H10L12 6H20C21.1 6 22 6.89 22 8V18C22 18.24 21.96 18.47 21.88 18.68L20 16.8V8H11.2Z';

/**
 * The state chip of one reason group: modifier, icon and text label.
 *
 * Four shapes and not three, because two of the reason codes are a state of
 * their own in the state inventory: a truncated document is indexed and cut,
 * and an excluded file was skipped on purpose rather than refused. Both would
 * read as a defect under the plain "skipped" label, so both get their own icon
 * and their own sentence.
 *
 * @return array{0:string, 1:string, 2:string}
 */
$chip = static function (string $state, string $reason) use ($l, $skippedIcon, $failedIcon, $truncatedIcon, $excludedIcon): array {
	if ($state === 'indexed') {
		return ['truncated', $truncatedIcon, $l->t('Indexed, text truncated')];
	}
	if ($reason === 'excluded') {
		return ['excluded', $excludedIcon, $l->t('Excluded')];
	}
	if ($state === 'failed') {
		return ['failed', $failedIcon, $l->t('Failed')];
	}

	return ['skipped', $skippedIcon, $l->t('Skipped')];
};
?>
<div id="findling-errors" class="section">
	<h2><?php p($l->t('Files that were not indexed')); ?></h2>

	<?php if ($errorGroups === []) { ?>
		<p class="settings-hint"><?php p($l->t('Every file was indexed. Nothing was skipped and nothing failed.')); ?></p>
	<?php } else { ?>
		<table class="findling-errors">
			<caption class="hidden-visually"><?php p($l->t('Files that were not indexed, grouped by reason')); ?></caption>
			<thead>
				<tr>
					<th scope="col"><?php p($l->t('Reason')); ?></th>
					<th scope="col"><?php p($l->t('Files')); ?></th>
					<th scope="col"><?php p($l->t('State')); ?></th>
				</tr>
			</thead>
			<tbody>
				<?php foreach ($errorGroups as $group) {
					$reason = is_string($group['reason'] ?? null) ? $group['reason'] : '';
					$state = is_string($group['state'] ?? null) ? $group['state'] : '';
					$examples = is_array($group['examples'] ?? null) ? $group['examples'] : [];
					$remaining = $whole($group['remaining'] ?? 0);
					// The region id of the design contract, one per group. Keyed
					// by state AND reason (review finding WR-02): the groups come
					// grouped by both, so a reason alone would mint the same id
					// twice the day one code shows up under two states, and
					// aria-controls would point every button at the first region.
					// Both values are validated against the closed lists before
					// they ever reach this template, so they are safe as an id,
					// and they are printed escaped all the same.
					$regionId = 'findling-errors-' . $state . '-' . $reason;
					[$chipKind, $chipIcon, $chipLabel] = $chip($state, $reason);
					?>
					<tr class="findling-errors__group">
						<th scope="row" class="findling-errors__label"><?php p(is_string($group['label'] ?? null) ? $group['label'] : ''); ?></th>
						<td class="findling-errors__count" id="findling-errors-count-<?php p($state . '-' . $reason); ?>"><?php p($count($whole($group['count'] ?? 0))); ?></td>
						<td>
							<span class="findling-chip findling-chip--<?php p($chipKind); ?>">
								<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($chipIcon); ?>"/></svg>
								<span><?php p($chipLabel); ?></span>
							</span>
						</td>
					</tr>
					<tr class="findling-errors__detail">
						<td colspan="3">
							<p class="settings-hint"><?php p(is_string($group['remedy'] ?? null) ? $group['remedy'] : ''); ?></p>

							<?php if ($examples !== []) { ?>
								<button type="button" class="findling-errors__toggle" aria-expanded="false" aria-controls="<?php p($regionId); ?>" hidden><?php p($l->t('Show example paths')); ?></button>

								<div id="<?php p($regionId); ?>">
									<ul class="findling-errors__examples">
										<?php foreach ($examples as $example) {
											$fileId = $whole($example['fileId'] ?? 0);
											$path = is_string($example['path'] ?? null) ? $example['path'] : '';
											$resolved = ($example['resolved'] ?? false) === true;
											$trashed = ($example['trashed'] ?? false) === true;
											// A file id without a cache entry keeps its
											// line and says what happened to it. A line
											// that disappeared would take its count with
											// it, and "the file is gone" is itself the
											// answer to why it was never indexed.
											$uid = is_string($example['uid'] ?? null) ? $example['uid'] : '';
											$shown = !$resolved
												? $l->t('File no longer exists (ID %s)', [(string)$fileId])
												: ($trashed ? $l->t('%s (in the trash bin)', [$path]) : $path);
											// The lookup takes a path in the shape the
											// placeholder teaches, uid/files/rest, and a
											// trashed or vanished file is not at that
											// path any more: those rows carry only the
											// id, which the lookup resolves either way.
											$lookupPath = ($resolved && !$trashed && $uid !== '' && $path !== '')
												? $uid . '/files/' . $path
												: '';
											?>
											<li>
												<button type="button" class="findling-errors__example findling-path" data-findling-path="<?php p($lookupPath); ?>" data-findling-file-id="<?php p((string)$fileId); ?>"><?php p($shown); ?></button>
											</li>
										<?php } ?>
									</ul>

									<?php if ($remaining > 0) { ?>
										<p class="settings-hint"><?php p($l->n('and %n more', 'and %n more', $remaining)); ?></p>
									<?php } ?>
								</div>
							<?php } elseif ($remaining > 0) { ?>
								<p class="settings-hint"><?php p($l->n('and %n more', 'and %n more', $remaining)); ?></p>
							<?php } ?>
						</td>
					</tr>
				<?php } ?>
			</tbody>
		</table>
	<?php } ?>
</div>
<?php
/*
 * Block four: one file, one state, one reason.
 *
 * ADM-02 and the second half of D-04. The field takes a path or a numeric file
 * id, because an administrator who has a path does not want to look up an id
 * first and one who copied an id out of the list above does not want to build a
 * path, and every example path of that list fills this field, scrolls here and
 * runs the lookup with one click.
 *
 * The field lies in a form so that Enter submits without a keyboard handler of
 * our own, and the form has no action: the script cancels the submit and asks
 * the JSON route. Without JavaScript the card stays empty and the sentence under
 * the field says so, which is the documented, deliberate boundary of this page
 * (the design contract, "Erstes Rendern ohne JavaScript"): blocks one to three
 * are complete without a script, this one and the rules block are not.
 *
 * The card is built here and never in the script, like every other part of this
 * page. That is why all seven state icons are in the markup at once, hidden, and
 * the script shows one of them and sets the modifier class of the chip. A script
 * that assembled an icon out of a string would be the one place on this page
 * where a reason code from the container could become markup.
 */

// Icon path data: Material Design Icons by Pictogrammers, Apache-2.0, pinned by
// commit in THIRD-PARTY.md. One per state of the state inventory, plus the
// magnifier of the button, so that colour is never the only carrier of a
// verdict and the script never has to compose one.
$diagnosisIcons = [
	'indexed' => 'M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M12 20C7.59 20 4 16.41 4 12S7.59 4 12 4 20 7.59 20 12 16.41 20 12 20M16.59 7.58L10 14.17L7.41 11.59L6 13L10 17L18 9L16.59 7.58Z',
	'truncated' => $truncatedIcon,
	'queued' => $clockIcon,
	'skipped' => $skippedIcon,
	'excluded' => $excludedIcon,
	'failed' => $failedIcon,
	'unknown' => $infoIcon,
];

$magnifyIcon = 'M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z';
?>
<div id="findling-diagnosis" class="section">
	<h2><?php p($l->t('Look up one file')); ?></h2>

	<form class="findling-lookup" id="findling-diagnosis-form">
		<label for="findling-diagnosis-input"><?php p($l->t('Path or file ID')); ?></label>
		<input type="text" id="findling-diagnosis-input" name="ref" autocomplete="off"
			aria-describedby="findling-diagnosis-help" placeholder="alice/files/Vertraege/Miete.pdf">
		<button type="submit" id="findling-diagnosis-submit">
			<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($magnifyIcon); ?>"/></svg>
			<span class="icon-loading-small" id="findling-diagnosis-spinner" hidden></span>
			<span><?php p($l->t('Look up file')); ?></span>
		</button>
	</form>

	<p class="settings-hint" id="findling-diagnosis-help"><?php p($l->t('A path as Nextcloud stores it, or the numeric ID from the list above.')); ?></p>
	<p class="settings-hint" id="findling-diagnosis-nojs"><?php p($l->t('Looking up a single file needs JavaScript. Everything above stays complete without it.')); ?></p>

	<div class="findling-card" id="findling-diagnosis-result" role="status" aria-live="polite" hidden>
		<p class="findling-chip" id="findling-diagnosis-chip">
			<?php foreach ($diagnosisIcons as $state => $icon) { ?>
				<svg id="findling-diagnosis-icon-<?php p($state); ?>" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false" hidden><path fill="currentColor" d="<?php p($icon); ?>"/></svg>
			<?php } ?>
			<span class="icon-loading-small" id="findling-diagnosis-icon-processing" hidden></span>
			<span id="findling-diagnosis-chip-label"></span>
		</p>

		<p class="findling-path" id="findling-diagnosis-path" hidden></p>
		<p id="findling-diagnosis-label" hidden></p>
		<p class="settings-hint" id="findling-diagnosis-remedy" hidden></p>
		<p class="settings-hint" id="findling-diagnosis-note" hidden></p>
		<p class="settings-hint" id="findling-diagnosis-id" hidden></p>
		<p class="settings-hint" id="findling-diagnosis-checked" hidden></p>
	</div>
</div>
<?php
/*
 * Block five: the four things an admin may change.
 *
 * ADM-04 and D-08, and the only writing part of this page. Four switches and no
 * "advanced" section: a settings screen with twenty options contradicts the zero
 * config promise this app is built on, so the number of controls is a decision.
 *
 * Every value is rendered server side out of the rules subtree, so the form
 * shows what is IN FORCE and not what a default would be. The size cap carries a
 * max attribute out of the ceiling the container reported, because a field
 * without an upper bound would accept a number the container ignores, and the
 * page would then be showing a limit that does not hold (pitfall 2).
 *
 * This block and the lookup above it are the two parts of the page that need
 * JavaScript, which is the documented boundary of the design contract. Blocks
 * one to three are complete without a script.
 *
 * The row template at the end is the one piece of markup the script uses: it
 * clones it and fills text nodes and attributes. That is what keeps the rule "the
 * script never builds markup" true for a list that can grow. The alternative
 * would be assembling a list item out of a string that contains a folder name,
 * which is exactly what Gate C in backend/tests/test_admin_ui_contract.py
 * forbids the script to do.
 */
$rules = is_array($_['rules'] ?? null) ? $_['rules'] : [];

$prefixes = is_array($rules['exclusions'] ?? null) ? $rules['exclusions'] : [];
$capBytes = $whole($rules['maxFileBytes'] ?? 0);
$ceilingBytes = $whole($rules['maxFileBytesCeiling'] ?? 0);
$teamFolders = ($rules['indexTeamFolders'] ?? false) === true;
$externalStorage = ($rules['indexExternalStorage'] ?? false) === true;

// The two halves of the one sentence this block owes an admin about time. A new
// exclusion clears the index within a cron round, and taking one back waits for
// the comparison run, which holds itself back for this many hours. Naming the
// wait and the way around it is the difference between a page an admin trusts
// and one where removing an entry looks like nothing happened.
$latencyHours = $whole($rules['cleanupLatencyHours'] ?? 0);
$restartCommand = is_string($rules['restartCommand'] ?? null) ? $rules['restartCommand'] : '';

// Megabytes in the field and bytes in appconfig. An admin thinks in megabytes,
// and a field holding 52428800 is a field nobody can check at a glance. The
// script converts back with the same divisor, which is named on both sides.
$megabyte = 1048576;
$capMb = max(1, intdiv($capBytes, $megabyte));
$ceilingMb = max(1, intdiv($ceilingBytes, $megabyte));

// Icon path data: Material Design Icons by Pictogrammers, Apache-2.0, pinned by
// commit in THIRD-PARTY.md. The cross of a remove button, which is the only
// icon-only control on this page and therefore the one that has to carry its
// label in an aria-label with the path in it.
$closeIcon = 'M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z';
?>
<div id="findling-rules" class="section">
	<h2><?php p($l->t('Rules and limits')); ?></h2>

	<?php
	/*
	 * One label for the group and for the field that adds to it, and that is
	 * deliberate rather than economical. The design contract carries exactly one
	 * label for this control, "Excluded folders", so inventing a second string
	 * for the input would be a string nobody signed off; the list is named by the
	 * same label through aria-labelledby, which is what a screen reader needs in
	 * order to say what the list is a list of.
	 */
	?>
	<label class="findling-rules__label" id="findling-rules-exclusions-label" for="findling-rules-new"><?php p($l->t('Excluded folders')); ?></label>
	<p class="settings-hint" id="findling-rules-exclusions-help"><?php p($l->t('Prefix match on the path as the lists on this page show it, no wildcards and no patterns. Example: Backups')); ?></p>

	<p class="settings-hint" id="findling-rules-exclusions-empty"<?php if ($prefixes !== []) { ?> hidden<?php } ?>><?php p($l->t('No folder is excluded.')); ?></p>

	<ul class="findling-rules__list" id="findling-rules-list" aria-labelledby="findling-rules-exclusions-label">
		<?php foreach ($prefixes as $prefix) {
			$prefix = is_string($prefix) ? $prefix : '';
			?>
			<li class="findling-rules__row">
				<span class="findling-path findling-rules__prefix"><?php p($prefix); ?></span>
				<button type="button" class="findling-rules__remove" aria-label="<?php p($l->t('Remove exclusion %s', [$prefix])); ?>">
					<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($closeIcon); ?>"/></svg>
				</button>
			</li>
		<?php } ?>
	</ul>

	<div class="findling-rules__add">
		<input type="text" id="findling-rules-new" name="exclusion" autocomplete="off"
			aria-describedby="findling-rules-exclusions-help findling-rules-new-error" placeholder="Backups">
		<button type="button" id="findling-rules-add"><?php p($l->t('Add exclusion')); ?></button>
	</div>
	<p class="findling-rules__error" id="findling-rules-new-error" hidden></p>

	<div class="findling-rules__field">
		<label class="findling-rules__label" for="findling-rules-cap"><?php p($l->t('Largest file to read')); ?></label>
		<input type="number" id="findling-rules-cap" name="maxFileBytes" inputmode="numeric"
			min="1" max="<?php p((string)$ceilingMb); ?>" step="1" value="<?php p((string)$capMb); ?>"
			aria-describedby="findling-rules-cap-unit findling-rules-cap-help findling-rules-cap-error">
		<span class="findling-rules__unit" id="findling-rules-cap-unit">MB</span>
	</div>
	<p class="settings-hint" id="findling-rules-cap-help"><?php p($l->t('Files above this size are recorded as skipped (too large) and never read.')); ?>
		<?php p($l->t('The backend of this instance reads at most %s MB. For more, raise FINDLING_MAX_FILE_BYTES in the app settings of AppAPI, which restarts the container.', [$count($ceilingMb)])); ?></p>
	<p class="findling-rules__error" id="findling-rules-cap-error" hidden></p>

	<div class="findling-rules__toggle">
		<input type="checkbox" class="checkbox" id="findling-rules-team-folders" name="indexTeamFolders"<?php if ($teamFolders) { ?> checked<?php } ?>>
		<label for="findling-rules-team-folders"><?php p($l->t('Index Team Folders')); ?></label>
	</div>

	<div class="findling-rules__toggle">
		<input type="checkbox" class="checkbox" id="findling-rules-external-storage" name="indexExternalStorage"<?php if ($externalStorage) { ?> checked<?php } ?>>
		<label for="findling-rules-external-storage"><?php p($l->t('Index external storage')); ?></label>
	</div>
	<p class="settings-hint" id="findling-rules-external-help"><?php p($l->t('External storage can be slow or charged per request. Indexing reads every file once.')); ?></p>

	<p class="settings-hint" id="findling-rules-effect"><?php p($l->t('The next run applies the new rules. Nothing restarts.')); ?></p>

	<?php if ($latencyHours > 0 && $restartCommand !== '') { ?>
		<p class="settings-hint" id="findling-rules-latency"><?php p($l->t('Removing an entry takes effect within %1$s hours, when the next comparison run picks those files up again. Run "%2$s" to apply it at once.', [$count($latencyHours), $restartCommand])); ?></p>
	<?php } ?>

	<?php
	/*
	 * The inline confirmation of D-07, empty until the script fills it.
	 *
	 * It sits directly above the button it holds back, which is the place where
	 * the consequence belongs: excluding a folder also removes the documents
	 * already indexed under it from the index, and that is a loss somebody has
	 * to be able to weigh before it happens. The number of documents and the
	 * path arrive from the reading preview route; the sentence says as well that
	 * the files themselves stay on the disk, because "remove" is the word an
	 * admin fears here and the fear is unfounded.
	 *
	 * Inline and not a dialog, for two reasons. The core helper for a
	 * destructive dialog is deprecated since Nextcloud 30 while this app carries
	 * max-version 35, so a dialog would be a bet on a version window it may not
	 * survive. And inline is where the consequence stands anyway: over the
	 * button, under the list it is about.
	 *
	 * role="group" with aria-labelledby on its own text, so a screen reader
	 * reads the consequence when the focus arrives, which the script moves to
	 * the harmless of the two buttons.
	 *
	 * Icon path data: Material Design Icons by Pictogrammers, Apache-2.0, pinned
	 * by commit in THIRD-PARTY.md. alert-circle-outline, the same path the
	 * banners of block one carry, in the destructive icon colour here.
	 */
	?>
	<div class="findling-rules__confirm" id="findling-rules-confirm" role="group" aria-labelledby="findling-rules-confirm-text" hidden>
		<p class="findling-rules__confirm-text" id="findling-rules-confirm-text">
			<svg class="findling-rules__confirm-icon" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($alertIcon); ?>"/></svg>
			<span id="findling-rules-confirm-message"></span>
		</p>
		<div class="findling-rules__confirm-actions">
			<button type="button" class="findling-rules__confirm-accept" id="findling-rules-confirm-accept"><?php p($l->t('Exclude and remove')); ?></button>
			<button type="button" id="findling-rules-confirm-cancel"><?php p($l->t('Keep files indexed')); ?></button>
		</div>
	</div>

	<button type="button" class="primary" id="findling-rules-save"><?php p($l->t('Save rules')); ?></button>

	<p class="findling-rules__feedback" id="findling-rules-feedback" role="status" aria-live="polite" hidden></p>

	<template id="findling-rules-row">
		<li class="findling-rules__row">
			<span class="findling-path findling-rules__prefix"></span>
			<button type="button" class="findling-rules__remove">
				<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($closeIcon); ?>"/></svg>
			</button>
		</li>
	</template>
</div>
