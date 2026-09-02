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

$indexable = $whole($_['indexable'] ?? 0);
$indexed = $whole($_['indexedDisplay'] ?? 0);
$scheduled = $whole($_['scheduled'] ?? 0);
$running = $whole($_['running'] ?? 0);
$lastJobRun = $whole($_['lastJobRun'] ?? 0);
$stalledFor = $whole($_['stalledFor'] ?? 0);
$runState = is_string($_['runState'] ?? null) ? $_['runState'] : 'never_run';
$reachable = ($_['backendReachable'] ?? false) === true;

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
	'stalled' => $l->t('Indexing has not progressed for %s. Background jobs may not be running.', [$span($stalledFor)]),
	default => $l->t('No background job of this app has run yet. Background jobs may not be running.'),
};

// The coverage figure, and the one rule that decides whether it exists at all:
// no percentage without a named denominator. The denominator is the number of
// indexable files, which the metadata scan of a later plan counts; until then
// it is zero and this block shows the empty state instead of dividing by it.
$percent = 0;
if ($indexable > 0) {
	// Rounded down, and capped below a hundred while anything is still missing.
	// A page that says "100 %" with files left over is the failure this whole
	// phase exists to make impossible.
	$percent = (int)floor($indexed * 100 / $indexable);
	$percent = $indexed >= $indexable ? 100 : min(99, max(0, $percent));
}

$tiles = [
	['id' => 'findling-tile-indexed', 'label' => $l->t('Indexed'), 'value' => $indexed],
	['id' => 'findling-tile-skipped', 'label' => $l->t('Skipped'), 'value' => $whole($_['skipped'] ?? 0)],
	['id' => 'findling-tile-failed', 'label' => $l->t('Failed'), 'value' => $whole($_['failed'] ?? 0)],
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
				<span class="findling-banner__text"><?php p($banner['text']); ?></span>
			</p>
		<?php } ?>
	</div>

	<?php if ($indexable > 0) { ?>
		<p class="findling-figure">
			<span class="findling-figure__value" id="findling-coverage-percent"><?php p($count($percent) . "\u{00A0}%"); ?></span>
		</p>
		<progress id="findling-coverage-bar" max="100" value="<?php p((string)$percent); ?>" aria-labelledby="findling-coverage-heading"></progress>
		<p class="settings-hint" id="findling-coverage-subline"><?php p($l->t('%1$s of %2$s indexable files are searchable', [$count($indexed), $count($indexable)])); ?></p>
	<?php } else { ?>
		<div id="findling-coverage-empty">
			<h3 class="findling-subheading"><?php p($l->t('No numbers yet')); ?></h3>
			<p class="settings-hint"><?php p($l->t('The first indexing pass has not finished. Findling started on its own, there is nothing to configure.')); ?></p>
		</div>
	<?php } ?>

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
