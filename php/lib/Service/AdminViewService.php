<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\BackgroundJobs\SchedulerJob;
use OCA\Findling\Text\PlainText;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IAppConfig;
use OCP\IL10N;
use OCP\IUserSession;

/**
 * The one place where the numbers of Nextcloud and the numbers of the container
 * meet, and the only one.
 *
 * Two sources answer the same questions and they are allowed to disagree. The
 * split is therefore written down here rather than being discovered later:
 *
 * - Out of ``findling_file_state``, which is this side of the boundary:
 *   ``skipped`` and ``failed``, their breakdown by reason code and the example
 *   file ids of every group. These survive a stopped container, which is the
 *   whole reason the table exists, and they are what the page falls back to.
 *   The file ids become readable paths in PathResolverService and nowhere else,
 *   which is D-03: the container hands over numbers, this side turns them into
 *   names, in the permission model that owns that decision.
 * - Out of the container, under the key ``backend``: ``indexed``,
 *   ``truncated``, ``docs``, ``aclRows``, the version marks, the disk figures
 *   and the reason breakdown. Only the container knows what is in the index.
 * - Out of ``findling_queue`` through QueueService: ``scheduled`` and
 *   ``running``. Deliberately not over the HTTP routes: those carry the ExApp
 *   attribute and are unreachable from an admin session, and asking the
 *   container for the work stock of this side would invent a second answer to a
 *   question the database answers directly.
 * - Out of appconfig: ``lastJobRun``, which is the answer to "does the cron of
 *   this instance run at all", the failure mode the predecessor of this app died
 *   of quietly.
 * - Out of ``findling_scan_stats`` through ScanStatsService: the denominator of
 *   the coverage figure and the files that were deliberately left out. Only this
 *   side owns the Nextcloud file list, so only this side can say how many files
 *   could be indexed at all.
 *
 * The two views stay visible side by side and are never added into one figure.
 * A difference between them is a diagnostic signal, not a defect of the page: it
 * says the container and Nextcloud disagree about a file, which is exactly what
 * an admin needs to see. The one derived value below, ``indexedDisplay``, picks
 * one of the two as the number to show, and it picks rather than combines.
 *
 * When the container does not answer, ``backendReachable`` is false and
 * ``backend`` carries the zero structure with every key present. The page then
 * says "the backend does not answer" and never "not indexed". That distinction
 * is the point of this phase.
 *
 * Everything arriving from the container is unconfirmed input and is rebuilt
 * field by field below, never merged with a spread. A counter that arrives as a
 * string, a reason code that arrives as a sentence and a note the size of a
 * novel all end as a bounded value of the expected type, because every one of
 * them is on its way into the DOM of an administrator (T-04-14).
 *
 * The estimate of the first index, D-05, and what it is not. There is no
 * confirmation gate anywhere in this app: the first index starts on its own,
 * which is the core promise of a zero-config search, and nothing on the page
 * waits for an administrator to agree to it. The estimate is an informative
 * figure from the first minute and it gets more accurate as the run proceeds.
 * The success criterion of the roadmap says "before the first index", and D-05 is
 * the later, explicit decision that wins over that wording: the number appears
 * from minute one and the page labels it as provisional while the scan is still
 * walking, and it names how many of how many mounts are through.
 *
 * Duration and space calibrate themselves against the running pass instead of
 * being predicted from constants. Every rate this project has measured comes
 * from an amd64 laptop core, the hardware target is an ARM box, and the
 * measuring run for it is still outstanding, so a prediction out of the amd64
 * numbers would be wrong by an unknown factor on the machine that matters. The
 * constants below are the startup value of the first minute and nothing else,
 * and ``startupValues`` is the flag with which the page labels them as such.
 */
final class AdminViewService {
	/**
	 * How long the work stock may sit still before the page calls it a stall.
	 *
	 * Thirty minutes, and the number comes from the cron of the instance rather
	 * than from taste. Every job of this app is a QueuedJob that chains its own
	 * successor, so the cadence of the indexing is the cadence of the cron, and
	 * the system cron of Nextcloud runs every five minutes. Half an hour is six
	 * missed rounds: long enough that one slow document, a freshly restarted
	 * instance or a single skipped round is not slandered as a stall, short
	 * enough that an admin who opens the page because "search finds nothing"
	 * gets told the truth on the first look.
	 *
	 * With the default AJAX cron the threshold is crossed legitimately, and that
	 * is not a false positive but the message: with AJAX cron the background jobs
	 * only run while somebody is clicking around in the web interface, so the
	 * indexing really has stopped. The status line says so and names the cause.
	 */
	private const STALLED_AFTER_SECONDS = 1800;

	/**
	 * The run states, and there are exactly four. Anything the page wants to say
	 * about progress has to be one of them, so that a fifth case cannot appear
	 * as an empty status line.
	 */
	public const RUN_NEVER = 'never_run';
	public const RUN_STALLED = 'stalled';
	public const RUN_RUNNING = 'running';
	public const RUN_IDLE = 'idle';

	/**
	 * Ceiling for the two free text fields the container sends. Both are shown
	 * to an admin, so both are cut here and not in the template.
	 */
	private const MAX_TEXT_LENGTH = 500;

	/**
	 * What a reason code may look like before it is passed on. The taxonomy of
	 * FileStateService::REASONS is lower case and underscores, and a code that
	 * does not fit that shape has no row in the display table anyway. Filtering
	 * on the shape rather than on the list keeps a legitimate new code of a newer
	 * container visible, which is the drift signal, while a code carrying markup
	 * or a path never reaches the page.
	 */
	private const REASON_PATTERN = '/^[a-z][a-z_]{0,39}$/';

	/**
	 * The free space the container insists on keeping, in bytes.
	 *
	 * The value of MIN_FREE_BYTES in backend/src/findling/config.py. Below it the
	 * container pauses with paused_low_disk, so an index that is expected to grow
	 * into that reserve does not fail, it stops. This is the one place where a
	 * figure of this phase leads to an action: the page warns while there is
	 * still something an administrator can do about it, instead of reporting a
	 * halt after it happened.
	 *
	 * A second copy of a container constant, and deliberately so: the alternative
	 * would be a fifth field on a status answer that already carries the flag
	 * derived from it, and the number has not moved in three phases. If it ever
	 * does, the container reports lowDisk regardless and the page keeps saying
	 * the truth, only earlier or later than it could have.
	 */
	private const MIN_FREE_BYTES = 524288000;

	/**
	 * Pages read per scanned document, the default of FINDLING_OCR_MAX_PAGES.
	 *
	 * Used for one purpose only: turning the measured milliseconds per OCR page
	 * that the container reports into documents per hour, for the first minute in
	 * which nothing has been measured yet. An instance that raised or lowered the
	 * environment variable makes this startup value optimistic or pessimistic by
	 * exactly that factor, which is one more reason it is labelled as a startup
	 * value and replaced by measurement within the minute.
	 */
	private const OCR_PAGE_CAP = 30;

	/**
	 * Text documents per hour, the startup value, and it is an assumption.
	 *
	 * Unlike the OCR page rate, which is measured and comes from the container,
	 * this number has never been measured: the research of this phase records as
	 * assumption A2 that the HTTP fetch of the bytes dominates the cost of a text
	 * file, and it records that this was never verified. One document per second
	 * is the order of magnitude that follows from it, and the per file extraction
	 * timeout of 120 seconds is the outlier cutoff rather than the normal case.
	 *
	 * So this is exactly what the field name says: a startup value. It is used
	 * only while no rate has been measured, ``startupValues`` is true for as long
	 * as it is used, and the page says "startup value, being measured" rather
	 * than presenting it as a measurement. The moment the container has finished
	 * a handful of documents, the measurement replaces it.
	 */
	private const STARTUP_TEXT_DOCS_PER_HOUR = 3600;

	/**
	 * From which share of judged files the measured OCR count replaces the
	 * interval, in per cent.
	 *
	 * Before the run the OCR share is an interval and not a value: an image has
	 * no text layer and always needs OCR, and a PDF may or may not have one,
	 * which only the extraction finds out. So the lower bound is the images and
	 * the upper bound is the images plus every PDF. The measured value grows out
	 * of the documents the container reported without a text layer.
	 *
	 * While only a handful of files have a verdict, that measured value is a
	 * lower bound that keeps rising, and a figure that quietly corrects itself
	 * upwards looks like a defect. So the page keeps showing the interval until
	 * half of the indexable files have a verdict, and shows the measured number
	 * from then on. Half is a display decision and not a measurement, which is
	 * why it is a constant with this sentence next to it rather than a number
	 * inside an expression.
	 */
	private const MEASURED_OCR_FROM_JUDGED_PERCENT = 50;

	/**
	 * Ceiling on the estimated seconds, so that no sentence on the page claims a
	 * span nobody can act on.
	 *
	 * A thousand days. It is reached only when a rate is so small that the
	 * remainder divided by it overflows anything meaningful, and a page that says
	 * "about 400 years" has stopped informing and started entertaining.
	 */
	private const MAX_SECONDS_LEFT = 86400000;

	/**
	 * How many example paths one reason group carries at the most.
	 *
	 * Twenty, and it is a display decision with a visible remainder rather than
	 * a silent cut: every group also reports how many rows it did not show. The
	 * MAX_LIST_LENGTH gotcha of CR-01 does not apply here, because this list does
	 * not travel over the queue routes, so nobody may lower this number for that
	 * reason. What does bound it is the cost of the resolution: every example is
	 * a mount cache query plus a user lookup, so twenty per group on a page that
	 * polls is the ceiling this side can afford (T-04-34).
	 */
	private const EXAMPLES_PER_GROUP = 20;

	/**
	 * The display text of every reason code, in English, as the source strings.
	 *
	 * One label and one remedy per code, word for word out of the table "Grund
	 * Taxonomie: Label und Abhilfe" of the design contract, in the same order and
	 * in the same number. The German versions live in l10n/de.json under exactly
	 * these keys.
	 *
	 * Where there is no remedy the sentence says so out loud instead of leaving
	 * the field empty. An admin who reads a blank cell learns nothing, and a
	 * blank cell is also what a drift between the three reason lists would look
	 * like, so the two cases have to stay distinguishable.
	 *
	 * Twenty codes, which is one more than FileStateService::REASONS holds today:
	 * `excluded` is the reason of the exclusion rules of plan 04-08 and it is
	 * already in the contract, so its row is here from the start. The other
	 * direction is the one that would hurt, and it cannot happen unnoticed: a
	 * code without a row falls into the fallback of reasonText() and is shown as
	 * "Unknown reason (code)".
	 *
	 * The strings are read from here and handed to IL10N::t() rather than being
	 * written as literals at the call site. This app has no string extractor, its
	 * translation files are written by hand, and one table next to the contract
	 * it copies is easier to check against that contract than twenty calls spread
	 * over a match expression.
	 *
	 * @var array<string, array{0:string, 1:string}> reason code to label and remedy
	 */
	private const REASON_TEXT = [
		'truncated' => [
			'Text truncated',
			'The beginning of the document is searchable, the rest is not. Very long documents are cut on purpose.',
		],
		'too_large' => [
			'Too large',
			'Raise the value under "Largest file to read".',
		],
		'mime_not_allowed' => [
			'File type not supported',
			'None. Findling reads PDF, Office, OpenDocument, text and images.',
		],
		'encrypted' => [
			'Password protected',
			'None. Without the password the content cannot be read.',
		],
		'no_text_layer' => [
			'No text in the document',
			'None. The document carries neither a text layer nor recognisable writing.',
		],
		'empty_text' => [
			'No text content',
			'None. The file is readable but carries no text.',
		],
		'too_many_cells' => [
			'Spreadsheet too large',
			'None. Very large spreadsheets are skipped so the container does not fall over.',
		],
		'gone' => [
			'File no longer present',
			'None. The file was already deleted or moved when it was read.',
		],
		'image_not_ocrable' => [
			'Image without recognisable writing',
			'None.',
		],
		'excluded' => [
			'Excluded by a rule',
			'Remove the matching entry under "Excluded folders".',
		],
		'empty_file' => [
			'File is empty',
			'None. The file has 0 bytes.',
		],
		'corrupt' => [
			'File damaged',
			'Check the file outside of Nextcloud and upload it again.',
		],
		'xml_invalid' => [
			'Document structure faulty',
			'Open the document in the program it came from and save it again.',
		],
		'encoding_unknown' => [
			'Character set not recognised',
			'Save the file as UTF-8 and upload it again.',
		],
		'timeout' => [
			'Timed out while reading',
			'The next run tries again.',
		],
		'out_of_memory' => [
			'Not enough memory while reading',
			'The next run tries again. If it happens again, lower the size cap.',
		],
		'gateway_error' => [
			'File was not retrievable',
			'The next run tries again.',
		],
		'repeatedly_stuck' => [
			'Stuck repeatedly',
			'Findling does not try this file again. Use the lookup to check whether it opens outside of Nextcloud.',
		],
		'ocr_failed' => [
			'Text recognition failed',
			'The next run tries again.',
		],
		'ocr_unavailable' => [
			'Text recognition not available',
			'The backend could not start Tesseract. Check the log of the External App.',
		],
	];

	public function __construct(
		private FileStateService $fileStateService,
		private QueueService $queueService,
		private ExAppService $exAppService,
		private ScanStatsService $scanStats,
		private PathResolverService $pathResolver,
		private IAppConfig $appConfig,
		private IUserSession $userSession,
		private ITimeFactory $timeFactory,
		private IL10N $l10n,
	) {
	}

	/**
	 * Every number of the coverage block, in one structure with fixed keys.
	 *
	 * Fixed and never sparse: a caller that has to ask whether a key exists
	 * ends up writing a default in the template and a second, different default
	 * in the script, and the two disagree on the day it matters. Both consumers
	 * of this method read the same keys and get zero where there is nothing.
	 *
	 * @return array{
	 *     indexed:int, skipped:int, failed:int, excluded:int,
	 *     indexedDisplay:int, scheduled:int, running:int, lastJobRun:int,
	 *     stalledFor:int, runState:string, backendReachable:bool,
	 *     backend:array<string,mixed>, coverage:array<string,mixed>,
	 *     estimate:array<string,mixed>, errors:array<string,mixed>
	 * }
	 */
	public function overview(): array {
		$states = $this->fileStateService->counts();
		$queue = $this->queueService->stats();
		$scan = $this->scanStats->totals();

		$scheduled = (int)($queue['scheduled'] ?? 0);
		$running = (int)($queue['running'] ?? 0);

		// The denominator of the coverage figure and the file count of the
		// estimate are the same set of files, so the subtraction happens once,
		// here, and both subtrees below are handed the result. Two places
		// working it out would put two different numbers for one quantity on the
		// same page, and the page would be right about neither.
		$indexable = max(0, (int)$scan['filesSeen'] - max(0, (int)$scan['overCap']) - max(0, (int)$scan['excluded']));

		$lastJobRun = $this->appConfig->getValueInt(Application::APP_ID, SchedulerJob::LAST_JOB_RUN);
		$now = $this->timeFactory->getTime();
		$stalledFor = $lastJobRun === 0 ? 0 : max(0, $now - $lastJobRun);

		$answer = $this->exAppService->adminGet('/status', $this->userId(), []);
		$backendReachable = $answer !== null;
		$backend = $this->backend($answer);

		// The Nextcloud side of the table holds no indexed rows by construction:
		// phase 2 records skips and failures there and nothing else, so the
		// count below is zero on a healthy instance and stays in the answer as
		// the honest zero of this side rather than being hidden.
		$indexed = (int)($states['indexed'] ?? 0);

		return [
			'indexed' => $indexed,
			'skipped' => (int)($states['skipped'] ?? 0),
			'failed' => (int)($states['failed'] ?? 0),
			// Out of the scan counters and not out of findling_file_state: the
			// crawl decides which files it leaves alone, so it is the only side
			// that can count them. Zero until plan 04-08 introduces the
			// exclusion rules and with them the reason code; the tile exists
			// from the first day so that the number cannot appear later as one
			// that grew out of nowhere (IDX-06).
			'excluded' => (int)$scan['excluded'],
			// The one derived value, and it picks instead of adding. Only the
			// container knows how many documents are in the index; with the
			// container silent the last figure this side recorded is what an
			// admin gets, together with the banner that says exactly that.
			'indexedDisplay' => $backendReachable ? (int)$backend['indexed'] : $indexed,
			'scheduled' => $scheduled,
			'running' => $running,
			'lastJobRun' => $lastJobRun,
			'stalledFor' => $stalledFor,
			'runState' => $this->runState($lastJobRun, $stalledFor, $scheduled, $running),
			'backendReachable' => $backendReachable,
			'backend' => $backend,
			'coverage' => $this->coverage($scan, $backend, $backendReachable, $indexable),
			'estimate' => $this->estimate($scan, $backend, $backendReachable, $indexable, $scheduled + $running),
			'errors' => $this->errors(),
		];
	}

	/**
	 * The files that were not indexed, grouped by the reason they were not.
	 *
	 * Out of findling_file_state and deliberately not out of backend.reasons.
	 * This is the half of the taxonomy that survives a stopped container, which
	 * is exactly the moment an admin goes looking for it, and it is the only
	 * half whose file ids this side can turn into paths. The view of the
	 * container stays visible next to it under its own key and the two are never
	 * added together: a difference between them says the container and Nextcloud
	 * disagree about a file, which is a diagnostic signal and not a defect of the
	 * page.
	 *
	 * Only skipped and failed appear, plus one exception: indexed(truncated).
	 * Those files are in the index, so they do not belong in a list of files
	 * that were not indexed, but D-08 of phase 3 says a cut document has to be
	 * declared rather than counted as a clean hit, so it gets a group of its own
	 * with its own label. Everything else under indexed is left out, and a group
	 * whose count is nought is left out as well, because a list of errors with
	 * nineteen empty rows hides the one row that has something in it.
	 *
	 * Sorted by count descending, and alphabetically by label where two groups
	 * are the same size, so the order is stable across polls instead of being
	 * whatever the database felt like returning.
	 *
	 * @return array{groups:list<array<string,mixed>>}
	 */
	private function errors(): array {
		$groups = [];
		foreach ($this->fileStateService->reasonsByState() as $state => $perReason) {
			foreach ($perReason as $reason => $count) {
				if ($count <= 0 || !$this->belongsInTheErrorList($state, $reason)) {
					continue;
				}

				[$label, $remedy] = $this->reasonText($reason);
				$examples = $this->examples($state, $reason);

				$groups[] = [
					'state' => $state,
					'reason' => $reason,
					'count' => $count,
					'label' => $label,
					'remedy' => $remedy,
					'examples' => $examples,
					// The remainder is a field of its own and it is rendered as
					// a line of its own. A list that is cut without saying so
					// leaves an admin counting the rows and believing the total
					// (T-04-35).
					'remaining' => max(0, $count - count($examples)),
				];
			}
		}

		usort($groups, static function (array $a, array $b): int {
			$bigger = $b['count'] <=> $a['count'];

			return $bigger !== 0 ? $bigger : strcmp((string)$a['label'], (string)$b['label']);
		});

		return ['groups' => $groups];
	}

	/**
	 * Whether this verdict is one of the ones the error list is about.
	 *
	 * The whole of skipped and failed, and out of indexed exactly the truncated
	 * rows. Written as its own method because the exception needs a sentence and
	 * a condition inside a loop does not have room for one.
	 */
	private function belongsInTheErrorList(string $state, string $reason): bool {
		if ($state === 'skipped' || $state === 'failed') {
			return true;
		}

		return $state === 'indexed' && $reason === 'truncated';
	}

	/**
	 * Up to twenty example paths of one group, resolved in the owner's view.
	 *
	 * One page out of the state table, then one batch resolution over it. Never
	 * more than one page, and never the whole table: the cost of a resolution is
	 * written down in PathResolverService::describeMany and it is the reason both
	 * numbers here are constants rather than parameters.
	 *
	 * A row whose file id no longer resolves stays in the list with resolved
	 * false. The template renders the replacement text for it, because a line
	 * that disappears takes its count with it and "the file is gone" is itself
	 * the answer to why it was never indexed.
	 *
	 * @return list<array<string,mixed>>
	 */
	private function examples(string $state, string $reason): array {
		if ($reason === '') {
			// A row without a reason code cannot be paged for: page() reads a
			// null reason as "no filter at all", which would answer with the
			// rows of every other group of this state and put foreign examples
			// under this label. No writer of this app produces such a row, so
			// the honest answer is the count with the whole group as the
			// remainder.
			return [];
		}

		$rows = $this->fileStateService->page($state, $reason, self::EXAMPLES_PER_GROUP, 0);
		if ($rows === []) {
			return [];
		}

		$described = $this->pathResolver->describeMany(
			array_map(static fn (array $row): int => $row['fileId'], $rows),
		);

		$examples = [];
		foreach ($rows as $row) {
			$one = is_array($described[$row['fileId']] ?? null) ? $described[$row['fileId']] : [];

			$examples[] = [
				'fileId' => $row['fileId'],
				'path' => is_string($one['path'] ?? null) ? $one['path'] : '',
				'uid' => is_string($one['uid'] ?? null) ? $one['uid'] : '',
				'shares' => is_int($one['shares'] ?? null) ? max(0, $one['shares']) : 0,
				'trashed' => ($one['trashed'] ?? false) === true,
				'resolved' => ($one['resolved'] ?? false) === true,
				'updatedAt' => $row['updatedAt'],
			];
		}

		return $examples;
	}

	/**
	 * The label and the remedy of one reason code, translated.
	 *
	 * The fallback is the whole point of this method. A code that has no row in
	 * the table is the visible symptom of a drift between the three reason lists
	 * of this project, and the design contract forbids showing a raw code on its
	 * own or an empty cell for it: the admin gets "Unknown reason (code)" with
	 * the code in brackets, which names the case instead of hiding it (T-04-33).
	 * A code that arrived empty is shown with a dash in the brackets rather than
	 * with nothing, because empty brackets read like a defect of the page.
	 *
	 * @return array{0:string, 1:string} label and remedy
	 */
	private function reasonText(string $reason): array {
		$row = self::REASON_TEXT[$reason] ?? null;
		if ($row === null) {
			return [
				$this->l10n->t('Unknown reason (%s)', [$reason === '' ? '-' : $reason]),
				$this->l10n->t('This app does not know this code. It may come from a newer version of the backend.'),
			];
		}

		return [$this->l10n->t($row[0]), $this->l10n->t($row[1])];
	}

	/**
	 * The headline figure of the page: a fraction whose denominator is written
	 * out in the sentence next to it.
	 *
	 * The numerator is the container's ``indexed`` and deliberately not its
	 * ``docs``. Those two are two sources on purpose, and their being equal is
	 * the proof that the upsert of the index works; the fraction takes the one
	 * that counts judged files, and both stay visible side by side.
	 *
	 * The denominator is filesSeen minus overCap minus excluded, worked out once
	 * in overview() and handed in here, so that this figure and the file count of
	 * the estimate cannot drift apart. It is word for
	 * word the set the crawl walked: the mimetype filter and the two encryption
	 * booleans are already in its query, and the cap and the exclusions are the
	 * two conditions it applies itself. So the denominator comes out of the same
	 * work as the numerator and never out of a second query, which is what would
	 * otherwise leave the reconcile repairing the difference between two counts
	 * every night.
	 *
	 * ``deliberatelyLeftOut`` is those two omissions plus the files the container
	 * refused by type. skipped(no_text_layer) is expressly not part of it: that
	 * reason is the hand over point to the OCR track and not a final verdict, so
	 * counting it as left out would write off files that are on their way into
	 * the index.
	 *
	 * ``percent`` is null in the two cases where no honest percentage exists,
	 * and the template renders a sentence rather than a number for both of them.
	 * With no denominator there is nothing to divide by, and a division by zero
	 * is not sold as nought per cent. With the container silent there is no
	 * numerator either, and the numerator of this side is zero by construction,
	 * so a figure would read "nothing is searchable" when the truth is "nobody
	 * asked the index" (T-04-23).
	 *
	 * @param array<string,int> $scan
	 * @param array<string,mixed> $backend
	 * @param int $indexable the denominator, worked out once in overview()
	 * @return array{
	 *     indexed:int, indexable:int, deliberatelyLeftOut:int, percent:int|null,
	 *     provisional:bool, mountsTotal:int, mountsFinished:int
	 * }
	 */
	private function coverage(array $scan, array $backend, bool $backendReachable, int $indexable): array {
		$overCap = max(0, (int)$scan['overCap']);
		$excluded = max(0, (int)$scan['excluded']);

		$indexed = $backendReachable ? max(0, (int)$backend['indexed']) : 0;
		$mountsTotal = max(0, (int)$scan['mountsTotal']);
		$mountsFinished = max(0, (int)$scan['mountsFinished']);

		$percent = null;
		if ($indexable > 0 && $backendReachable) {
			// Rounded down, and held below a hundred while anything is still
			// missing. A page that says a hundred per cent with files left over
			// is the failure this whole phase exists to make impossible.
			$percent = $indexable - $indexed > 0
				? min(99, max(0, (int)floor($indexed * 100 / $indexable)))
				: 100;
		}

		return [
			'indexed' => $indexed,
			'indexable' => $indexable,
			'deliberatelyLeftOut' => $overCap + $excluded
				+ $this->fileStateService->countByReason('skipped', 'mime_not_allowed'),
			'percent' => $percent,
			// A scan that has not walked every mount to its end has counted a
			// lower bound, and the page has to say so and name both figures. An
			// estimate that quietly corrects itself upwards looks like a defect.
			// No row at all is the same case and not a finished scan.
			'provisional' => $mountsTotal === 0 || $mountsFinished < $mountsTotal,
			'mountsTotal' => $mountsTotal,
			'mountsFinished' => $mountsFinished,
		];
	}

	/**
	 * What the first index still costs: files, OCR share, time left, space.
	 *
	 * Always all thirteen keys, for the same reason overview() is never sparse.
	 * Three of them are deliberately nullable, and null means "there is no honest
	 * number for this yet" rather than nought: a duration of nought reads as
	 * "done" and a space requirement of nought reads as "free", and both would be
	 * a claim this method cannot back.
	 *
	 * ``files`` is the same set as coverage.indexable and comes from the same
	 * subtraction, handed in from overview().
	 *
	 * The OCR share is an interval before the run and not a value. ocrMin is the
	 * images, because an image has no text layer at all; ocrMax adds every PDF,
	 * because a PDF may or may not carry one and only the extraction finds out.
	 * ocrMeasured is what the run itself produced, the images plus the documents
	 * the container reported as skipped(no_text_layer), and it stays null until
	 * enough files have a verdict for it to have stopped climbing. A single
	 * guessed percentage would be a number without a basis, and the audience of
	 * this product has believed a status screen that knew nothing before.
	 *
	 * ``secondsLeft`` divides the remainder by the measured throughput, one track
	 * at a time, because a page of OCR and a page of text cost orders of
	 * magnitude apart. Where no rate has been measured yet the startup value
	 * steps in and ``startupValues`` turns true, which is the signal the page
	 * needs in order to label the figure instead of selling it as a measurement.
	 * With the container silent there is no rate and no startup rate either, so
	 * the answer is null: an unreachable backend must not produce an invented
	 * number.
	 *
	 * ``spaceWarning`` is the one place in this phase where a figure leads to an
	 * action, and it fires before the index stops rather than after.
	 *
	 * ``firstIndexDone`` ends the block. Once every mount is walked through and
	 * no work is waiting, an advance estimate has nothing left to say, so the
	 * page does not render it at all. That is also why the throughput of the
	 * container is not even asked for in that state: a resting instance is polled
	 * every thirty seconds and a call whose answer nobody renders is a round trip
	 * for nothing.
	 *
	 * @param array<string,int> $scan
	 * @param array<string,mixed> $backend
	 * @param int $indexable the same figure as coverage.indexable
	 * @param int $openWork queue entries waiting plus queue entries running
	 * @return array{
	 *     files:int, ocrMin:int, ocrMax:int, ocrMeasured:int|null,
	 *     secondsLeft:int|null, bytesExpected:int|null, bytesPerDoc:int|null,
	 *     spaceWarning:bool, provisional:bool, mountsTotal:int,
	 *     mountsFinished:int, startupValues:bool, firstIndexDone:bool
	 * }
	 */
	private function estimate(array $scan, array $backend, bool $backendReachable, int $indexable, int $openWork): array {
		$mountsTotal = max(0, (int)$scan['mountsTotal']);
		$mountsFinished = max(0, (int)$scan['mountsFinished']);
		$provisional = $mountsTotal === 0 || $mountsFinished < $mountsTotal;
		$firstIndexDone = $mountsTotal > 0 && $mountsFinished === $mountsTotal && $openWork === 0;

		// Held inside the file count, because both bounds are counted over
		// everything the crawl saw while the file count leaves out what is over
		// the cap or excluded. An upper bound above its own denominator would
		// read as "more files need OCR than exist".
		$ceiling = static fn (int $bound): int => $indexable > 0 ? min($bound, $indexable) : $bound;
		$ocrMin = $ceiling(max(0, (int)$scan['ocrCandidates']));
		$ocrMax = $ceiling($ocrMin + max(0, (int)$scan['pdfSeen']));

		$shape = [
			'files' => $indexable,
			'ocrMin' => $ocrMin,
			'ocrMax' => $ocrMax,
			'ocrMeasured' => null,
			'secondsLeft' => null,
			'bytesExpected' => null,
			'bytesPerDoc' => null,
			'spaceWarning' => false,
			'provisional' => $provisional,
			'mountsTotal' => $mountsTotal,
			'mountsFinished' => $mountsFinished,
			// True until something is measured, so that a page which renders the
			// block before the first rate exists labels what it shows.
			'startupValues' => true,
			'firstIndexDone' => $firstIndexDone,
		];

		if ($firstIndexDone || !$backendReachable) {
			// Nothing to estimate, or nothing to estimate it from. Either way the
			// keys are all here and none of them carries an invented value.
			return $shape;
		}

		$judged = max(0, (int)$backend['indexed']) + max(0, (int)$backend['skipped']) + max(0, (int)$backend['failed']);
		$shape['ocrMeasured'] = $this->measuredOcr($backend, $ocrMin, $ocrMax, $indexable, $judged);

		$rest = max(0, $indexable - $judged);
		$rates = $this->rates($this->exAppService->adminGet('/rates', $this->userId(), []));
		[$shape['secondsLeft'], $shape['startupValues']] = $this->timeLeft($rest, $rates, $shape);

		$docs = max(0, (int)$backend['docs']);
		if ($docs > 0) {
			// Out of the two operands of the status answer this page already
			// holds, and not out of the quotient the throughput route also
			// carries: the space figure then survives a throughput call that
			// failed, and there is no second rule for one number.
			$shape['bytesPerDoc'] = intdiv(max(0, (int)$backend['indexBytes']), $docs);
			$shape['bytesExpected'] = $shape['bytesPerDoc'] * $indexable;
			$usable = max(0, (int)$backend['diskFreeBytes']) - self::MIN_FREE_BYTES;
			$shape['spaceWarning'] = $shape['bytesExpected'] > $usable;
		}

		return $shape;
	}

	/**
	 * The OCR count the run itself produced, or null while it is still climbing.
	 *
	 * Images always need OCR, and on top of them come the PDFs the container
	 * found without a text layer. That sum is the true value, and it is only
	 * worth showing once it has stopped being a lower bound, which is what the
	 * threshold constant decides. Held inside the interval in any case: a
	 * measurement above the upper bound would mean the crawl and the container
	 * disagree about the file stock, and a page is not the place to resolve that.
	 *
	 * @param array<string,mixed> $backend
	 */
	private function measuredOcr(array $backend, int $ocrMin, int $ocrMax, int $indexable, int $judged): ?int {
		if ($indexable <= 0 || $judged * 100 < $indexable * self::MEASURED_OCR_FROM_JUDGED_PERCENT) {
			return null;
		}

		$reasons = is_array($backend['reasons'] ?? null) ? $backend['reasons'] : [];
		$skipped = is_array($reasons['skipped'] ?? null) ? $reasons['skipped'] : [];
		$withoutTextLayer = is_int($skipped['no_text_layer'] ?? null) ? max(0, $skipped['no_text_layer']) : 0;

		return min($ocrMax, $ocrMin + $withoutTextLayer);
	}

	/**
	 * Seconds left, and whether a startup value had to be used for them.
	 *
	 * One division per track, because the two tracks cost orders of magnitude
	 * apart. The remainder is split by the OCR share of the whole file stock,
	 * measured where a measurement exists and the middle of the interval
	 * otherwise, which is an approximation and is meant as one: the share of the
	 * remaining files is not knowable without judging them, and the alternative
	 * is no figure at all.
	 *
	 * A track with nothing left in it needs no rate, so a missing rate there
	 * does not label the whole figure as a startup value. A track that does have
	 * work left and no measured rate uses the startup value and says so. If even
	 * the startup value is missing, which is what a silent container looks like,
	 * the answer is null rather than a number nobody can back.
	 *
	 * @param array{docsPerHourText:int,docsPerHourOcr:int,startupRateOcrMs:int} $rates
	 * @param array<string,mixed> $shape the estimate so far, for the OCR share
	 * @return array{0:int|null,1:bool}
	 */
	private function timeLeft(int $rest, array $rates, array $shape): array {
		$files = (int)$shape['files'];
		if ($files <= 0) {
			// Nothing has been counted yet, so there is no remainder to divide.
			// Zero seconds would read as "done" while the scan has not even
			// started, which is the opposite of the truth.
			return [null, true];
		}
		if ($rest <= 0) {
			// Every counted file has a verdict. Zero is exact here and not a
			// startup value, so the page shows it without a label.
			return [0, false];
		}

		$ocrShare = is_int($shape['ocrMeasured'])
			? $shape['ocrMeasured']
			: intdiv((int)$shape['ocrMin'] + (int)$shape['ocrMax'], 2);
		$restOcr = min($rest, (int)round($rest * min($files, max(0, $ocrShare)) / $files));
		$restText = $rest - $restOcr;

		$startupValues = false;
		$textPerHour = max(0, $rates['docsPerHourText']);
		if ($restText > 0 && $textPerHour === 0) {
			$textPerHour = self::STARTUP_TEXT_DOCS_PER_HOUR;
			$startupValues = true;
		}

		$ocrPerHour = max(0, $rates['docsPerHourOcr']);
		if ($restOcr > 0 && $ocrPerHour === 0) {
			$perPage = max(0, $rates['startupRateOcrMs']);
			if ($perPage === 0) {
				// The container never told us its measured page rate, which is
				// what a silent backend looks like. No number then, and the page
				// says the backend does not answer.
				return [null, true];
			}
			$ocrPerHour = max(1, intdiv(3600 * 1000, $perPage * self::OCR_PAGE_CAP));
			$startupValues = true;
		}

		$seconds = 0.0;
		if ($restText > 0) {
			$seconds += $restText * 3600 / $textPerHour;
		}
		if ($restOcr > 0) {
			$seconds += $restOcr * 3600 / $ocrPerHour;
		}

		return [min(self::MAX_SECONDS_LEFT, (int)ceil($seconds)), $startupValues];
	}

	/**
	 * The three throughput fields of the container, rebuilt one by one.
	 *
	 * Called with null as well, which is what an unreachable container looks
	 * like, and then every field is a zero. The caller reads a zero as "not
	 * measured" and falls back to a labelled startup value or to no figure at
	 * all, which is the only honest pair of answers here.
	 *
	 * @param array<mixed>|null $answer the decoded body, or null when there was none
	 * @return array{docsPerHourText:int,docsPerHourOcr:int,startupRateOcrMs:int}
	 */
	private function rates(?array $answer): array {
		$answer ??= [];

		return [
			'docsPerHourText' => $this->counter($answer, 'docsPerHourText'),
			'docsPerHourOcr' => $this->counter($answer, 'docsPerHourOcr'),
			'startupRateOcrMs' => $this->counter($answer, 'startupRateOcrMs'),
		];
	}

	/**
	 * Which of the four sentences the status line shows.
	 *
	 * Order matters and it goes from the most damning to the most harmless. A
	 * page that reports "up to date" while nothing has ever run is the exact
	 * failure the predecessor of this app was known for, so "never run" is
	 * answered first and the pending work stock decides the rest.
	 */
	private function runState(int $lastJobRun, int $stalledFor, int $scheduled, int $running): string {
		if ($lastJobRun === 0) {
			// Not "idle" and not "stalled": nothing of this app has executed
			// even once. With the default AJAX cron of an instance that is the
			// normal state until somebody uses the web interface, and it is the
			// difference between hours and weeks for the first index.
			return self::RUN_NEVER;
		}

		$open = $scheduled + $running;
		if ($open === 0) {
			// Nothing waiting and a job ran at some point: the work stock is
			// empty, which is the only honest reading of "up to date" this page
			// has. It says when it last looked, not that everything is indexed.
			return self::RUN_IDLE;
		}

		if ($stalledFor > self::STALLED_AFTER_SECONDS) {
			// Work is waiting and nothing has run for half an hour. Never green
			// while nothing moves forward.
			return self::RUN_STALLED;
		}

		return self::RUN_RUNNING;
	}

	/**
	 * The seventeen status fields of the container, rebuilt one by one.
	 *
	 * Called with null as well, and then it returns the same seventeen keys as
	 * zeros, false and empty strings. That is what keeps the caller free of a
	 * second code path: a page that renders "container silent" out of the same
	 * shape it renders a healthy container from cannot forget one of the two.
	 *
	 * @param array<mixed>|null $answer the decoded body, or null when there was none
	 * @return array<string,mixed>
	 */
	private function backend(?array $answer): array {
		$answer ??= [];

		return [
			'indexed' => $this->counter($answer, 'indexed'),
			'truncated' => $this->counter($answer, 'truncated'),
			'skipped' => $this->counter($answer, 'skipped'),
			'failed' => $this->counter($answer, 'failed'),
			'reasons' => $this->reasons($answer['reasons'] ?? null),
			'aclRows' => $this->counter($answer, 'aclRows'),
			'docs' => $this->counter($answer, 'docs'),
			'indexVersion' => $this->counter($answer, 'indexVersion'),
			'analyzerVersion' => $this->counter($answer, 'analyzerVersion'),
			'wordlistHash' => $this->text($answer, 'wordlistHash'),
			'reindexRequired' => ($answer['reindexRequired'] ?? false) === true,
			'lowDisk' => ($answer['lowDisk'] ?? false) === true,
			'diskFreeBytes' => $this->counter($answer, 'diskFreeBytes'),
			'diskTotalBytes' => $this->counter($answer, 'diskTotalBytes'),
			'indexBytes' => $this->counter($answer, 'indexBytes'),
			'maxFileBytes' => $this->counter($answer, 'maxFileBytes'),
			'note' => $this->text($answer, 'note'),
		];
	}

	/**
	 * One counter of the container answer, as a non negative integer.
	 *
	 * A value that is not an integer is a zero and not a cast, because casting
	 * turns a sentence into a nought while looking like arithmetic. Negative is
	 * refused for the same reason: there is no counter in this protocol that can
	 * legitimately be below zero, and a negative one on the page would read as a
	 * defect of the page.
	 *
	 * @param array<mixed> $answer
	 */
	private function counter(array $answer, string $key): int {
		$value = $answer[$key] ?? null;

		return is_int($value) && $value >= 0 ? $value : 0;
	}

	/**
	 * One free text field of the container answer, cleaned and cut.
	 *
	 * Both fields this applies to are shown to an admin, and both come from
	 * across the trust boundary. PlainText::bounded is the same cleaning the
	 * search results go through, so a control character or a megabyte of text
	 * cannot reach the page from here either.
	 *
	 * @param array<mixed> $answer
	 */
	private function text(array $answer, string $key): string {
		$value = $answer[$key] ?? null;
		if (!is_string($value)) {
			return '';
		}

		return PlainText::bounded($value, self::MAX_TEXT_LENGTH) ?? '';
	}

	/**
	 * The reason breakdown of the container, state by state and code by code.
	 *
	 * The state has to be one of the three this app knows, because the page has
	 * a column for each and nowhere to put a fourth. The reason code only has to
	 * have the shape of a code: a code that is in the container and not yet in
	 * FileStateService::REASONS is the drift the three lists are tested against,
	 * and hiding it here would hide the only symptom. What is refused is a key
	 * that is not a code at all, which is where a path or a fragment of markup
	 * would arrive.
	 *
	 * @return array<string,array<string,int>>
	 */
	private function reasons(mixed $reasons): array {
		if (!is_array($reasons)) {
			return [];
		}

		$clean = [];
		foreach (FileStateService::STATES as $state) {
			$breakdown = $reasons[$state] ?? null;
			if (!is_array($breakdown)) {
				continue;
			}

			$perState = [];
			foreach ($breakdown as $reason => $count) {
				if (!is_string($reason) || preg_match(self::REASON_PATTERN, $reason) !== 1) {
					continue;
				}
				if (!is_int($count) || $count < 0) {
					continue;
				}
				$perState[$reason] = $count;
			}

			if ($perState !== []) {
				$clean[$state] = $perState;
			}
		}

		return $clean;
	}

	/**
	 * The identity the call to the container travels under.
	 *
	 * The status route of the container reads no identity at all, but
	 * exAppRequest demands one and AppAPI signs the header with it. The session
	 * user is the honest answer: this method is only ever reached from an admin
	 * session, because the only route into it carries no attribute that would
	 * let anybody else in. An empty string is left as an empty string rather
	 * than substituted with a fixed name, so that a call without a session fails
	 * in ExAppService, where the failure has a log line, instead of succeeding
	 * under an identity nobody chose.
	 */
	private function userId(): string {
		return $this->userSession->getUser()?->getUID() ?? '';
	}
}
