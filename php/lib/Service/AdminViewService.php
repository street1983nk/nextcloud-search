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
 * - Out of both at once, under the key ``lockstep``: whether the version of the
 *   container and the version of this app agree in major and minor (D-11), and
 *   the two numbers the verdict was made from. It is the one field on this page
 *   that is neither a measurement of one side nor a count, but a statement about
 *   the pair, and it is built in ExAppService out of the status answer above.
 * - Out of ``findling_queue`` through QueueService: ``scheduled`` and
 *   ``running``. Deliberately not over the HTTP routes: those carry the ExApp
 *   attribute and are unreachable from an admin session, and asking the
 *   container for the work stock of this side would invent a second answer to a
 *   question the database answers directly.
 * - Out of appconfig: ``lastJobRun``, which is the answer to "does the cron of
 *   this instance run at all", the failure mode the predecessor of this app died
 *   of quietly, and since plan 04-08 the ``rules`` subtree, which is the four
 *   switches of ADM-04 as they are in force. Those five fields are the only ones
 *   on this page an admin can change, and they are readable and writable with the
 *   container switched off, because appconfig lives in Nextcloud.
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
	 * When the container last reported more indexed documents than it had at the
	 * poll before, as a Unix timestamp.
	 *
	 * The second half of the stall verdict and the fix for DI-05-22. It lives in
	 * appconfig and not in SettingsService, next to the reading of
	 * SchedulerJob::LAST_JOB_RUN above, because it is the same kind of value: a
	 * measurement of when something last happened, written by this page and read
	 * by nobody else. The four switches over there are the fields an admin can
	 * change, and this is not one of them.
	 */
	private const KEY_INDEX_PROGRESS = 'last_index_progress';

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
	 * The states of a single file that no verdict table holds.
	 *
	 * Four names, and each of them is a state the diagnosis can reach without a
	 * row anywhere saying so. ``unknown`` is "nothing on this instance knows this
	 * file", ``queued`` and ``processing`` come out of the work stock, and
	 * ``pending_crawl`` is the one that had to be given a name: a file that keeps
	 * every rule, has no verdict and no queue row has not been reached by the
	 * crawl yet. Rendering that as "not indexed, reason unknown" is exactly the
	 * silent failure this whole phase exists to remove, so it gets a state of its
	 * own and a sentence of its own.
	 *
	 * ``excluded`` is the fifth and it is deliberately not in this list: the
	 * reason taxonomy already carries it, and a file left out by a rule of today
	 * is reported with that code so that label and remedy come from the same
	 * table as every other reason.
	 */
	public const STATE_UNKNOWN = 'unknown';
	public const STATE_QUEUED = 'queued';
	public const STATE_PROCESSING = 'processing';
	public const STATE_PENDING_CRAWL = 'pending_crawl';

	/** The state of a file that a rule of today leaves alone. */
	public const STATE_EXCLUDED = 'excluded';

	/**
	 * The mimetype Nextcloud gives a directory. It is a node like any other, so a
	 * path one segment short of a file resolves without complaint, and the answer
	 * has to name that rather than judge the type.
	 */
	private const MIME_FOLDER = 'httpd/unix-directory';

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
	 * How long the comparison run holds itself back, in hours.
	 *
	 * The default of ``FINDLING_RECONCILE_MIN_INTERVAL_HOURS`` in
	 * backend/src/findling/config.py, and the second copy of a container constant
	 * on this page, next to MIN_FREE_BYTES and for the same reason: the
	 * alternative would be one more field on a status answer, and the page needs
	 * the figure with the container switched off as well, because taking an
	 * exclusion back is exactly the moment somebody wants to know how long it
	 * takes. An instance that changed the variable waits a different span, and the
	 * sentence on the page is an order of magnitude rather than a promise; without
	 * a figure at all the page would leave an admin unable to tell waiting from
	 * broken.
	 */
	private const RECONCILE_INTERVAL_HOURS = 24;

	/**
	 * The way to skip that wait, spelled the way an admin types it.
	 *
	 * The same command the reindex banner names, and it is a constant here because
	 * two places on one page must not disagree about it. It queues everything
	 * again, so it is the answer to "I do not want to wait a day" for a prefix
	 * that was taken back as well.
	 */
	private const RESTART_COMMAND = 'occ findling:index --restart';

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
		private StorageService $storageService,
		private SettingsService $settingsService,
		private ExclusionService $exclusionService,
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
	 *     backend:array<string,mixed>, lockstep:array<string,string>,
	 *     coverage:array<string,mixed>, estimate:array<string,mixed>,
	 *     errors:array<string,mixed>, rules:array<string,mixed>
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
		//
		// The third subtrahend is new in plan 05-11 and it is a consequence of
		// DI-04-03 rather than a change of the figure's meaning. The files the
		// container refuses by type were always part of deliberatelyLeftOut in
		// coverage() below, and the sentence next to that number says word for
		// word that those files are NOT in the denominator, so that the coverage
		// figure can reach a hundred per cent. Until this plan the counter behind
		// it was always nought, because nothing on this side ever wrote
		// skipped(mime_not_allowed); now the container reports it, the number
		// becomes real, and without this line the promise of that sentence would
		// break on the same day: an instance with one video would sit at 99 per
		// cent for good, waiting for a file nobody will ever index.
		//
		// Asked once and handed down for the same reason as the difference
		// itself: coverage() names the number as deliberately left out and this
		// line takes it out of the denominator, and the two have to be the same
		// number or the sentence stops describing the figure above it.
		$refusedByType = $this->fileStateService->countByReason('skipped', 'mime_not_allowed');
		$indexable = max(
			0,
			(int)$scan['filesSeen']
				- max(0, (int)$scan['overCap'])
				- max(0, (int)$scan['excluded'])
				- $refusedByType,
		);

		$lastJobRun = $this->appConfig->getValueInt(Application::APP_ID, SchedulerJob::LAST_JOB_RUN);
		$now = $this->timeFactory->getTime();

		$answer = $this->exAppService->adminGet('/status', $this->userId(), []);
		$backendReachable = $answer !== null;
		$backend = $this->backend($answer);

		// Read BEFORE the remembering below overwrites it. The difference between
		// this figure and the one in the answer is the only evidence this side has
		// that the container is working, and the write two lines down destroys it
		// (DI-05-22, and the whole argument stands at backendProgressAt).
		$rememberedIndexed = $this->settingsService->lastIndexedCount();

		// The one write of this reading method, and it is what makes the size cap
		// honest. The container enforces the cap a second time out of an
		// environment variable it read at start (pitfall 2), so the value it
		// reports is the real ceiling, and the page has to clamp its input at it.
		// Remembering the figure is what keeps that clamp working while the
		// container is down, which is exactly when an admin is looking at this
		// page. SettingsService writes only when the number actually changed, so a
		// page polling every five seconds is not one appconfig write every five
		// seconds.
		if ($backendReachable) {
			$this->settingsService->rememberContainerCap((int)$backend['maxFileBytes']);
			// The second remembered measurement, and the one the banner promises:
			// "the last ones this app recorded" has to exist somewhere for the
			// tile below to hold still while the container is down.
			$this->settingsService->rememberIndexedCount((int)$backend['indexed']);
		}

		// Since when nothing has moved forward, and BOTH halves count as movement.
		// The background job is the half this side can see directly; the indexed
		// counter of the container is the other one, and on the target hardware it
		// is the half that runs longest (DI-05-22).
		$movedAt = max(
			$lastJobRun,
			$this->backendProgressAt($backendReachable, (int)$backend['indexed'], $rememberedIndexed, $now),
		);
		$stalledFor = $movedAt === 0 ? 0 : max(0, $now - $movedAt);

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
			// admin gets, together with the banner that says exactly that. The
			// record is the remembered count above, never the state table: that
			// side holds no indexed rows by construction, and reading it here
			// made the tile jump to zero the moment the container went silent.
			'indexedDisplay' => $backendReachable ? (int)$backend['indexed'] : $this->settingsService->lastIndexedCount(),
			'scheduled' => $scheduled,
			'running' => $running,
			'lastJobRun' => $lastJobRun,
			// How long ago EITHER half last moved, which is what the sentence on
			// the page says word for word since plan 05-20. The background job
			// alone was the measure before, and during a long OCR pass that is the
			// half which legitimately stands still (DI-05-22).
			'stalledFor' => $stalledFor,
			'runState' => $this->runState($lastJobRun, $stalledFor, $scheduled, $running),
			'backendReachable' => $backendReachable,
			'backend' => $backend,
			// The lockstep verdict of D-11, out of the same answer and without a
			// second call. It is not part of ``backend`` on purpose: everything
			// under that key is a number or a flag the container measured, and
			// this is a comparison between the container and this app, with the
			// two versions it was made from. The page renders the state and the
			// two numbers; nothing here decides what happens to the search,
			// which is ExAppService and the search provider.
			'lockstep' => $this->exAppService->lockstep($answer),
			'coverage' => $this->coverage($scan, $backend, $backendReachable, $indexable, $refusedByType),
			'estimate' => $this->estimate($scan, $backend, $backendReachable, $indexable, $scheduled + $running),
			'errors' => $this->errors(),
			'rules' => $this->rules(),
		];
	}

	/**
	 * The four switches of ADM-04 as they are in force, plus the ceiling of the
	 * cap.
	 *
	 * Public because two callers need exactly this and nothing else: the page
	 * renders it, and the write route answers with it so that the form can show
	 * the value that HOLDS rather than the one that was typed. Everything else on
	 * the page is a measurement; these five fields are the only ones an admin can
	 * change.
	 *
	 * ``maxFileBytesCeiling`` is the upper bound of the input field, and it is a
	 * figure of the container rather than of this app. For more than that,
	 * ``FINDLING_MAX_FILE_BYTES`` has to be raised in the AppAPI app settings,
	 * which restarts the container, because the variable is read at start and
	 * ``settings()`` is lru_cached over it. Naming the ceiling is what keeps this
	 * page from showing a cap the container would ignore (pitfall 2, T-04-50);
	 * without it the field would accept a hundred megabytes, the crawl would queue
	 * an eighty megabyte PDF, and the container would answer
	 * skipped(too_large) next to a page claiming the file was within the limit.
	 *
	 * The exclusions come out of ExclusionService and are therefore normalised,
	 * which matters for the second way in: a list written by
	 * ``occ config:app:set`` is shown here the way it will be compared, not the
	 * way it was typed.
	 *
	 * ``cleanupLatencyHours`` and ``restartCommand`` are the two fields the page
	 * needs in order to name the one thing this phase cannot make immediate. A new
	 * exclusion clears the index while the admin is still on the page, because the
	 * expansion job starts within a cron round. Taking an exclusion BACK heals
	 * itself and does so slowly: the files are enumerated again, but they are
	 * picked up by the comparison run, and that run holds itself back for as long
	 * as this figure says. Saying so is the point of this phase; leaving it out
	 * would have an admin remove a prefix, reload the page and see nothing happen,
	 * with no way of telling waiting from broken. The command is the way to skip
	 * the wait, and it is the same one the reindex banner names.
	 *
	 * @return array{
	 *     exclusions:list<string>, maxFileBytes:int, maxFileBytesCeiling:int,
	 *     indexTeamFolders:bool, indexExternalStorage:bool,
	 *     cleanupLatencyHours:int, restartCommand:string
	 * }
	 */
	public function rules(): array {
		return [
			'exclusions' => $this->exclusionService->prefixes(),
			'maxFileBytes' => $this->settingsService->maxFileBytes(),
			'maxFileBytesCeiling' => $this->settingsService->containerCap(),
			'indexTeamFolders' => $this->settingsService->indexTeamFolders(),
			'indexExternalStorage' => $this->settingsService->indexExternalStorage(),
			'cleanupLatencyHours' => self::RECONCILE_INTERVAL_HOURS,
			'restartCommand' => self::RESTART_COMMAND,
		];
	}

	/**
	 * One file, one state, one reason: the precedence rule over three sources.
	 *
	 * ADM-02, and the technical core of this phase. A file holds its state in up
	 * to three places and in none of them completely. ``findling_queue`` knows
	 * what is waiting and what is running. ``findling_file_state`` knows what was
	 * skipped or failed, with a reason, and it survives a switched off container.
	 * The ``files`` table inside the container knows what is indexed, whether OCR
	 * ran and whether a tombstone lies on the row. The three contradict each
	 * other legitimately, which is why this is a merge with a fixed order and not
	 * a summary: without an order the page shows both answers and the
	 * administrator knows less than before.
	 *
	 * Six stages, from "is true now" to "was true then", first answer wins, one
	 * named method each so that the order is readable in the code rather than
	 * being an emergent property of a long conditional:
	 *
	 * 1. Does the file exist at all? Nothing means unknown, and a tombstone in
	 *    the container then means it really was deleted.
	 * 2. Does it break a rule of TODAY, computed live and out of no database row?
	 *    This stage has to be live, because ``mime_not_allowed`` is never written:
	 *    the crawl filters the mimetype inside its query and therefore never sees
	 *    an unsuitable file, and the event listener returns without a verdict
	 *    (pitfall 1). Writing a row per excluded file instead would be two
	 *    hundred thousand rows on one excluded archive folder for an answer that
	 *    follows from four comparisons.
	 * 3. Is there a queue row? Then it is waiting or being worked on right now.
	 * 4. Is there a verdict on this side? That is the one that survives a stopped
	 *    container.
	 * 5. Is there a verdict in the container? Only there does "it is findable"
	 *    exist.
	 * 6. None of that? Then the file keeps every rule, nothing has judged it and
	 *    nothing is waiting for it, so the crawl has not reached it yet. That is
	 *    ``pending_crawl`` and it is a state with a name, not an absence.
	 *
	 * Degradation. When stage five falls out, the page SAYS so: backendReachable
	 * is false and the note names it. "The state is unknown right now because the
	 * backend does not answer" is honest, "not indexed" would be the lie that the
	 * predecessor of this app was known for, and it is never claimed here.
	 *
	 * A tombstone is read as a deletion only after stage one has confirmed that
	 * no cache entry is left (pitfall 6). The clearing after an exclusion is
	 * mechanically a deletion in the container and semantically none: the file
	 * lies untouched on the disk. So a file that exists and keeps the rules is
	 * ``pending_crawl`` with the note that it was indexed and will be picked up
	 * again, and never "gone".
	 *
	 * No text excerpt, ever. A snippet is file content, it stays bound to SRCH-02
	 * where it is only built for a hit that already survived the permission
	 * recheck, and blurring that line here is the way an administration tool
	 * turns into a content leak. The container reports a character count and this
	 * method does not even pass that on: a number could be shown, a text could
	 * not, and the shortest way to keep the two apart is to carry neither.
	 *
	 * @return array{
	 *     found:bool, fileId:int, path:string, uid:string, trashed:bool,
	 *     shares:int, state:string, reason:string, label:string, remedy:string,
	 *     checkedAt:int, backendReachable:bool, note:string
	 * }
	 */
	public function diagnose(string $input, string $userId): array {
		$fileId = $this->pathResolver->resolveReference($input);
		if ($fileId === null) {
			// Nothing was asked of the container, so nothing was missed either:
			// this answer comes entirely from this side and does not depend on a
			// container being up. Reporting it as unreachable would raise an
			// outage banner for an input that was simply not a file.
			return $this->diagnosis(0, null, true, []);
		}

		$facts = $this->pathResolver->inspect($fileId);

		// Asked once, ahead of the chain, and handed to the two stages that need
		// it. Stage one needs the tombstone in order to tell "was indexed, is
		// deleted" from "never seen", and stage five needs the verdict; two calls
		// for one lookup would be a second round trip for the same answer.
		// The identity of the call travels in from the caller and is not read out
		// of the session here. The route of the container reads no identity at
		// all, but exAppRequest demands one and AppAPI signs the header with it,
		// and a service that reached for the session itself would answer
		// differently depending on who happened to be logged in when it ran.
		$answer = $this->exAppService->adminGet('/diagnose', $userId, ['fileId' => $fileId]);
		$reachable = $answer !== null;
		$container = $this->containerVerdict($answer);

		$verdict = $this->stageOneDoesItExist($facts, $container)
			?? $this->stageTwoRulesOfToday($facts)
			?? $this->stageThreeWorkStock($fileId)
			?? $this->stageFourVerdictOfThisSide($fileId)
			?? $this->stageFiveVerdictOfTheContainer($container, $reachable)
			?? $this->stageSixNotSeenYet($container);

		return $this->diagnosis($fileId, $facts, $reachable, $verdict);
	}

	/**
	 * The thirteen keys of a diagnosis, never sparse and never partial.
	 *
	 * Same rule as overview(): a caller that has to ask whether a key exists ends
	 * up writing one default in the template and a different one in the script,
	 * and the two disagree on the day it matters. Everything the stages did not
	 * fill is an empty string, a nought or false, and the state falls back to
	 * unknown rather than to an empty string, because the card has a chip for
	 * unknown and none for nothing.
	 *
	 * @param array{uid:string,path:string,shares:int,trashed:bool,storageId:int,mime:string,size:int,internalPath:string}|null $facts
	 * @param array<string,mixed> $verdict whatever the stage that answered filled in
	 * @return array{
	 *     found:bool, fileId:int, path:string, uid:string, trashed:bool,
	 *     shares:int, state:string, reason:string, label:string, remedy:string,
	 *     checkedAt:int, backendReachable:bool, note:string
	 * }
	 */
	private function diagnosis(int $fileId, ?array $facts, bool $reachable, array $verdict): array {
		return [
			'found' => $facts !== null,
			'fileId' => max(0, $fileId),
			// The path is the one field of this answer that a user wrote, and it
			// leaves this method exactly as the mount cache spelled it. The
			// template prints it with the escaping printer and the script writes
			// it into a text node, so there is no third rule for it here.
			'path' => is_string($facts['path'] ?? null) ? $facts['path'] : '',
			'uid' => is_string($facts['uid'] ?? null) ? $facts['uid'] : '',
			'trashed' => ($facts['trashed'] ?? false) === true,
			'shares' => is_int($facts['shares'] ?? null) ? max(0, $facts['shares']) : 0,
			'state' => is_string($verdict['state'] ?? null) && $verdict['state'] !== ''
				? $verdict['state']
				: self::STATE_UNKNOWN,
			'reason' => is_string($verdict['reason'] ?? null) ? $verdict['reason'] : '',
			'label' => is_string($verdict['label'] ?? null) ? $verdict['label'] : '',
			'remedy' => is_string($verdict['remedy'] ?? null) ? $verdict['remedy'] : '',
			'checkedAt' => is_int($verdict['checkedAt'] ?? null) ? max(0, $verdict['checkedAt']) : 0,
			'backendReachable' => $reachable,
			'note' => is_string($verdict['note'] ?? null) ? $verdict['note'] : '',
		];
	}

	/**
	 * Stage one: does this file exist on this instance at all?
	 *
	 * Null means "yes, carry on with the next stage". An answer means the file
	 * has no cache entry and no mount row any more, so it is either deleted or a
	 * file id that never existed, and those two are one answer on purpose: three
	 * distinguishable answers here would make this field a way of probing the
	 * instance.
	 *
	 * The one thing that can be added is a tombstone in the container. With the
	 * absence of the cache entry confirmed HERE, and only here, the mark may be
	 * read as a deletion, which is what makes "it was indexed and has since been
	 * deleted" an honest sentence instead of the misreading of pitfall 6.
	 *
	 * @param array{uid:string,path:string,shares:int,trashed:bool,storageId:int,mime:string,size:int,internalPath:string}|null $facts
	 * @param array<string,mixed> $container
	 * @return array<string,mixed>|null
	 */
	private function stageOneDoesItExist(?array $facts, array $container): ?array {
		if ($facts !== null) {
			return null;
		}

		$deletedAt = is_int($container['deletedAt'] ?? null) ? max(0, $container['deletedAt']) : 0;
		if ($deletedAt > 0) {
			return [
				'state' => self::STATE_UNKNOWN,
				'checkedAt' => $deletedAt,
				'note' => $this->l10n->t('This file was indexed and has since been deleted. It is out of the index with it.'),
			];
		}

		return ['state' => self::STATE_UNKNOWN];
	}

	/**
	 * Stage two: does the file break a rule that applies today?
	 *
	 * Computed live, out of the file and the rules, and out of no database row at
	 * all. That is not an optimisation, it is the only way this stage can be
	 * right for the files it is asked about most: this side never writes
	 * ``mime_not_allowed`` itself, because the crawl filters the mimetype inside
	 * its query and never sees an unsuitable file, and the event listener returns
	 * without writing a verdict (pitfall 1). A file of an unsupported type
	 * therefore has no row from this half at all, and an admin who asks about it
	 * would be told "not seen yet" for a file that will never be seen.
	 *
	 * Since plan 05-11 the container writes such a row for the files that reach
	 * it and are refused by ITS allowlist, which is stricter than the query of
	 * the crawl (DI-04-03). That does not move this stage: it stands ahead of the
	 * stored verdict on purpose, it answers with the same code out of the same
	 * table, and it answers it for files that never reached the container as
	 * well. A rule of today beats a row from yesterday, and where both exist they
	 * say the same sentence.
	 *
	 * Four comparisons and their order is the order of certainty: where the file
	 * lies decides more than what it is, and what it is decides more than how
	 * large it is.
	 *
	 * @param array{uid:string,path:string,shares:int,trashed:bool,storageId:int,mime:string,size:int,internalPath:string} $facts
	 * @return array<string,mixed>|null
	 */
	private function stageTwoRulesOfToday(array $facts): ?array {
		if ($facts['trashed'] === true) {
			// A file in the trash bin still has a cache entry, so it resolves and
			// looks perfectly ordinary. The search drops it on purpose (phase 3,
			// D-10), and saying so is a diagnosis rather than a detail: without
			// this branch the file would fall through to "not seen yet", which
			// would be a promise that it is about to be indexed.
			return [
				'state' => self::STATE_EXCLUDED,
				'label' => $this->l10n->t('In the trash bin'),
				'remedy' => $this->l10n->t('Restore the file. The next comparison run picks it up.'),
			];
		}

		if ($facts['storageId'] > 0 && !$this->storageService->isIndexedStorage($facts['storageId'])) {
			return [
				'state' => self::STATE_EXCLUDED,
				'label' => $this->l10n->t('Storage is not indexed'),
				'remedy' => $this->l10n->t('Findling reads the home directories of your users. Team Folders and external storage are settings of their own.'),
			];
		}

		if ($facts['mime'] === self::MIME_FOLDER) {
			// A folder resolves like any other node and has no state of its own,
			// and it is the input an administrator produces by pasting a path one
			// segment short. Without this branch the answer would be "file type
			// not supported", which is true of the mimetype and useless as an
			// answer to what was actually asked.
			return [
				'state' => self::STATE_EXCLUDED,
				'label' => $this->l10n->t('This is a folder'),
				'remedy' => $this->l10n->t('Enter the path of a file. A folder has no state of its own.'),
			];
		}

		if ($facts['mime'] !== '' && !in_array($facts['mime'], StorageService::ALLOWED_MIMETYPES, true)) {
			return $this->reasonVerdict('skipped', 'mime_not_allowed');
		}

		if ($facts['size'] > $this->settingsService->maxFileBytes()) {
			// The cap IN FORCE and not the constant. This stage is "does the file
			// break a rule of today", and a rule of today is what an admin set
			// today: reading the code default here would tell somebody who just
			// raised the cap that their file is still too large, which is the
			// contradiction between page and behaviour that this phase exists to
			// remove.
			return $this->reasonVerdict('skipped', 'too_large');
		}

		return $this->excludedByAPrefix($facts['storageId'], $facts['internalPath']);
	}

	/**
	 * The exclusion prefix test of this stage, and the last comparison of it.
	 *
	 * It answers with ``skipped(excluded)``, so the label and the remedy come out
	 * of the same closed table every other reason uses and the card reads
	 * "Excluded by a rule" with "Remove the matching entry under Excluded
	 * folders" underneath. No row anywhere says so: this is the one verdict of
	 * the app that is worked out at the moment it is asked, because a row per
	 * excluded file would be two hundred thousand writes on one archive folder
	 * and every one of them wrong again the moment the rule is taken back.
	 *
	 * The internal path and the storage go in, and not the display path, which is
	 * the hazard plan 04-08 wrote down when it left this body empty:
	 * ExclusionService::mountRelativePathInStorage is the one place that turns
	 * them into the space the crawl compares in, so a Team Folder file is judged
	 * by the rule that really applies to it rather than by its mount point name.
	 *
	 * Where this stands in the order is the sharp edge of pitfall 6. Stage one has
	 * already established that the file EXISTS, so an excluded file is reported as
	 * excluded even when the container carries a tombstone for it, and that
	 * tombstone is the clearing this rule caused rather than a deletion of the
	 * file. Only stage one, where no cache entry was found at all, may read a
	 * tombstone as "was indexed and has since been deleted", and a file that keeps
	 * every rule and carries one is ``pending_crawl`` with the note that it was
	 * indexed before (stage six).
	 *
	 * @return array<string,mixed>|null
	 */
	private function excludedByAPrefix(int $storageId, string $internalPath): ?array {
		$relative = $this->exclusionService->mountRelativePathInStorage($storageId, $internalPath);
		if ($relative === null || !$this->exclusionService->isExcluded($relative)) {
			return null;
		}

		return $this->reasonVerdict('skipped', 'excluded');
	}

	/**
	 * Stage three: is this file in the work stock right now?
	 *
	 * Read through QueueService and not over the HTTP routes of the queue: those
	 * carry the ExApp attribute and are unreachable from an admin session.
	 *
	 * Waiting and running are told apart by the remaining claim time and not by
	 * the lock column being empty, because a free row is marked with the epoch
	 * rather than with NULL and a claim that ran past its timeout is free again
	 * without anybody having written to it. The remaining time is also the one
	 * number worth showing here: an administrator who sees "being processed" wants
	 * to know how long that may still be true before something is wrong.
	 *
	 * @return array<string,mixed>|null
	 */
	private function stageThreeWorkStock(int $fileId): ?array {
		$row = $this->queueService->forFile($fileId);
		if ($row === null) {
			return null;
		}

		$attempts = max(0, $row['retries']);
		$note = $attempts > 0
			? $this->l10n->t('Attempts so far: %s', [(string)$attempts])
			: '';

		if ($row['running']) {
			return [
				'state' => self::STATE_PROCESSING,
				'label' => $this->l10n->t('Being processed'),
				'remedy' => $this->l10n->n(
					'A worker holds this file. The claim runs out in %n second if nothing acknowledges it.',
					'A worker holds this file. The claim runs out in %n seconds if nothing acknowledges it.',
					$row['secondsLeft'],
				),
				'note' => $note,
			];
		}

		return [
			'state' => self::STATE_QUEUED,
			'label' => $this->l10n->t('Waiting in the queue'),
			'remedy' => $this->l10n->t('The next background run picks this file up (%s).', [$row['kind']]),
			'note' => $note,
		];
	}

	/**
	 * Stage four: the verdict of this side, out of findling_file_state.
	 *
	 * The one source that survives a switched off container, which is exactly the
	 * moment an administrator comes looking for it. It carries skipped and failed
	 * with their reason and the time it was written, and its label and remedy come
	 * out of the same closed table the error list of plan 04-06 uses, so a code
	 * cannot read one way in the list and another way in the card.
	 *
	 * @return array<string,mixed>|null
	 */
	private function stageFourVerdictOfThisSide(int $fileId): ?array {
		$row = $this->fileStateService->forFile($fileId);
		if ($row === null || $row['state'] === '') {
			return null;
		}

		return $this->reasonVerdict($row['state'], $row['reason'], $row['updatedAt']);
	}

	/**
	 * Stage five: the verdict of the container, and the one place "findable" exists.
	 *
	 * Three outcomes and every one of them is an answer. A silent container
	 * returns the honest one: the state is unknown right now BECAUSE the backend
	 * does not answer, and the note says that word for word. Nothing here ever
	 * claims "not indexed" for a container that did not speak (T-04-42).
	 *
	 * A row carrying a tombstone falls through to stage six instead of being
	 * reported as the verdict it holds. The mark means the file left the index,
	 * so the verdict next to it is what WAS true, and stage one has already
	 * confirmed that the file itself still exists. Reporting "indexed" there
	 * would be the page telling an administrator a document is searchable while
	 * it is not (pitfall 6).
	 *
	 * @param array<string,mixed> $container
	 * @return array<string,mixed>|null
	 */
	private function stageFiveVerdictOfTheContainer(array $container, bool $reachable): ?array {
		if (!$reachable) {
			return [
				'state' => self::STATE_UNKNOWN,
				'note' => $this->l10n->t('The state of this file is unknown right now because the backend does not answer.'),
			];
		}

		$state = is_string($container['state'] ?? null) ? $container['state'] : '';
		$deletedAt = is_int($container['deletedAt'] ?? null) ? max(0, $container['deletedAt']) : 0;
		if ($state === '' || $deletedAt > 0) {
			return null;
		}

		$reason = is_string($container['reason'] ?? null) ? $container['reason'] : '';
		$indexedAt = is_int($container['indexedAt'] ?? null) ? max(0, $container['indexedAt']) : 0;
		if ($state === 'indexed' && $reason === '') {
			return [
				'state' => 'indexed',
				'label' => $this->l10n->t('Indexed'),
				'remedy' => $this->l10n->t('The content of this file is searchable.'),
				'checkedAt' => $indexedAt,
			];
		}

		return $this->reasonVerdict($state, $reason, $indexedAt);
	}

	/**
	 * Stage six: the file keeps every rule and nothing has looked at it yet.
	 *
	 * A state with a name, and that is the whole point of it. "Not indexed,
	 * reason unknown" is the sentence this app exists to make impossible: it
	 * leaves an administrator with a file, no explanation and nothing to do. This
	 * says what is true instead, that the crawl has not arrived, and what happens
	 * next, which is the comparison run picking it up.
	 *
	 * The one variant is a tombstone on a file that still exists, which is the
	 * clearing after an exclusion or after a delete event that the file survived.
	 * The state is the same, and the note says it was in the index before, so that
	 * a figure dropping by one is explained rather than surprising.
	 *
	 * @param array<string,mixed> $container
	 * @return array<string,mixed>
	 */
	private function stageSixNotSeenYet(array $container): array {
		$deletedAt = is_int($container['deletedAt'] ?? null) ? max(0, $container['deletedAt']) : 0;

		return [
			'state' => self::STATE_PENDING_CRAWL,
			'label' => $this->l10n->t('Not seen yet'),
			'remedy' => $this->l10n->t('This file has not reached the queue. The next comparison run picks it up.'),
			'checkedAt' => $deletedAt,
			'note' => $deletedAt > 0
				? $this->l10n->t('It was indexed before and is recorded again on the next comparison run.')
				: '',
		];
	}

	/**
	 * A state and a reason code as a verdict with its label and its remedy.
	 *
	 * Every stage that has a reason code ends here, so the card and the error
	 * list read a code the same way, down to the fallback for a code neither of
	 * them knows.
	 *
	 * @return array<string,mixed>
	 */
	private function reasonVerdict(string $state, string $reason, int $checkedAt = 0): array {
		[$label, $remedy] = $this->reasonText($reason);

		return [
			'state' => $state,
			'reason' => $reason,
			'label' => $label,
			'remedy' => $remedy,
			'checkedAt' => $checkedAt,
		];
	}

	/**
	 * The verdict of the container, rebuilt field by field.
	 *
	 * Called with null as well, which is what a silent container looks like, and
	 * then every field is a zero or an empty string. Same rule as backend()
	 * above: one shape for both cases is what keeps the caller free of a second
	 * code path.
	 *
	 * The state has to be one of the three this app knows, because there is
	 * nowhere to put a fourth, and the reason only has to have the shape of a
	 * code: a code that is in the container and not yet in the taxonomy is the
	 * drift the three lists are tested against, and hiding it here would hide the
	 * only symptom. ``textChars`` is deliberately not read at all: it is a number
	 * and could be shown, but nothing on the page needs it, and a field that is
	 * not carried cannot be widened into the text next to it (T-04-39).
	 *
	 * @param array<mixed>|null $answer the decoded body, or null when there was none
	 * @return array<string,mixed>
	 */
	private function containerVerdict(?array $answer): array {
		$answer ??= [];

		$state = $answer['state'] ?? null;
		$reason = $answer['reason'] ?? null;

		return [
			'state' => is_string($state) && in_array($state, FileStateService::STATES, true) ? $state : '',
			'reason' => is_string($reason) && preg_match(self::REASON_PATTERN, $reason) === 1 ? $reason : '',
			'indexedAt' => $this->counter($answer, 'indexedAt'),
			'attempts' => $this->counter($answer, 'attempts'),
			'deletedAt' => $this->counter($answer, 'deletedAt'),
			'note' => $this->text($answer, 'note'),
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
	 * refused by type, and all three are out of the denominator, which is what
	 * the sentence next to the number on the page says as well. The third one was
	 * always nought until plan 05-11, because nothing on this side wrote
	 * skipped(mime_not_allowed) before the container started reporting its own
	 * decisions (DI-04-03). skipped(no_text_layer) is expressly not part of it:
	 * that reason is the hand over point to the OCR track and not a final
	 * verdict, so counting it as left out would write off files that are on their
	 * way into the index.
	 *
	 * ``percent`` is null in the two cases where no honest percentage exists,
	 * and the template renders a sentence rather than a number for both of them.
	 * With no denominator there is nothing to divide by, and a division by zero
	 * is not sold as nought per cent. With the container silent there is no
	 * numerator either, and the numerator of this side is zero by construction,
	 * so a figure would read "nothing is searchable" when the truth is "nobody
	 * asked the index" (T-04-23).
	 *
	 * ``embeddedPercent`` is the second track of D-16 and it is a second CALL of
	 * coverageShare() with another numerator, never a second calculation. The
	 * denominator is the same indexable set, so the two figures are comparable
	 * by construction, which is the only thing that makes showing them next to
	 * each other honest. It is null in a third case on top of the two above: a
	 * container that did not report the figure at all, which is a container
	 * older than this app. Nought per cent semantic coverage would be a claim
	 * about a container that never said anything about it.
	 *
	 * @param array<string,int> $scan
	 * @param array<string,mixed> $backend
	 * @param int $indexable the denominator, worked out once in overview()
	 * @param int $refusedByType skipped(mime_not_allowed), counted once in overview()
	 * @return array{
	 *     indexed:int, indexable:int, deliberatelyLeftOut:int, percent:int|null,
	 *     embedded:int, embeddedPercent:int|null,
	 *     provisional:bool, mountsTotal:int, mountsFinished:int
	 * }
	 */
	private function coverage(
		array $scan,
		array $backend,
		bool $backendReachable,
		int $indexable,
		int $refusedByType,
	): array {
		$overCap = max(0, (int)$scan['overCap']);
		$excluded = max(0, (int)$scan['excluded']);

		$indexed = $backendReachable ? max(0, (int)$backend['indexed']) : 0;
		$mountsTotal = max(0, (int)$scan['mountsTotal']);
		$mountsFinished = max(0, (int)$scan['mountsFinished']);

		// The number of documents that carry a vector, and whether the container
		// said anything about it at all. A container older than this app leaves
		// the key out, and that is a third state next to "nought" and "some":
		// the two have to stay apart, or an update in the wrong order would show
		// nought per cent semantic coverage on an instance whose semantic half
		// is perfectly complete.
		$embedded = $backend['embedded'] ?? null;
		$embeddedKnown = is_int($embedded) && $embedded >= 0;

		$percent = self::coverageShare($indexed, $indexable, $backendReachable);
		// A second call and not a second calculation, and that is the whole
		// design of this figure. Two ways of working out one kind of number
		// agree on the day they are written and drift on the day one of them is
		// corrected, which is exactly what phase 4 avoided by working the
		// denominator out once (D-16).
		$embeddedPercent = self::coverageShare(
			$embeddedKnown ? $embedded : 0,
			$indexable,
			$backendReachable && $embeddedKnown,
		);

		return [
			'indexed' => $indexed,
			'indexable' => $indexable,
			'deliberatelyLeftOut' => $overCap + $excluded + $refusedByType,
			'percent' => $percent,
			'embedded' => $embeddedKnown ? $embedded : 0,
			'embeddedPercent' => $embeddedPercent,
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
	 * One coverage figure: a counter over the indexable set, as a percentage.
	 *
	 * The one place this page turns two numbers into a share, and it is called
	 * twice: once with the documents the container has judged, once with the
	 * documents that carry a vector (D-16). The denominator is the same both
	 * times, which is what makes the two figures comparable, and the arithmetic
	 * is the same both times, which is what keeps them comparable a year from
	 * now. A second calculation for the second track would agree with this one
	 * on the day it is written and drift on the day one of them is corrected,
	 * and nothing on the page would show it.
	 *
	 * Rounded down, and held below a hundred while anything is still missing. A
	 * page that says a hundred per cent with files left over is the failure this
	 * whole phase exists to make impossible.
	 *
	 * Null and not nought where no honest percentage exists. With no denominator
	 * there is nothing to divide by, and with the figure unavailable there is no
	 * numerator either: nought per cent would be read as "nothing is findable"
	 * where the truth is "nobody could ask" (T-04-23). The template renders a
	 * sentence for that case and never a number.
	 *
	 * Static and public for the reason progressStamp() above is: it is the
	 * arithmetic and nothing else, and the alternative is a unit test that
	 * builds a whole admin view out of twelve doubles in order to ask what a
	 * fraction of two numbers comes to.
	 */
	public static function coverageShare(int $counted, int $indexable, bool $available): ?int {
		if ($indexable <= 0 || !$available) {
			return null;
		}

		$counted = max(0, $counted);

		return $indexable - $counted > 0
			? min(99, max(0, (int)floor($counted * 100 / $indexable)))
			: 100;
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
	 *
	 * ``$stalledFor`` is the age of the LAST MOVEMENT of either half since plan
	 * 05-20, not the age of the last background job, and the difference is the
	 * whole of DI-05-22: during a long OCR pass the job half stands still by
	 * construction while the container writes thousands of documents, and a
	 * verdict built on one half alone accused it of a stall for eight hours.
	 * ``$lastJobRun`` stays what it was and keeps deciding one question only,
	 * whether anything of this app has ever executed at all.
	 */
	/**
	 * When the container last finished something, or nought if it never did.
	 *
	 * **The finding this method exists for, DI-05-22.** ``runState`` used to ask
	 * one question, how long ago the last background job of this app ran, and it
	 * called everything above half an hour a stall. On an ordinary instance the
	 * crawl and the content work end at about the same time, so the question was
	 * good enough. On the hardware this product is built for it is not: the OCR
	 * pass runs on after the crawl, and in the full run of plan 05-14 it ran on
	 * for eight hours, which was seventy seven per cent of the whole run. The
	 * crawl finished at 01:30Z, the container wrote roughly 6.500 more documents
	 * until 09:27Z, and over all of that time the page said "Indexing has not
	 * progressed" while the coverage figure in the same row climbed from 82 to 99
	 * per cent. That is not a cosmetic defect: an admin who reads it stops the
	 * container, restarts it or files a bug, all three of which cost more than
	 * the eight hours would have.
	 *
	 * **Why the counter and not a timestamp from the container.** The container
	 * knows exactly when it last judged a file, and a field in the status answer
	 * would be the direct measurement. It would also be a measurement taken by a
	 * second clock: two containers, two time zones, a host whose clock drifts,
	 * and the comparison against the Nextcloud clock silently answers "in the
	 * future" or "eight hours ago" for no reason anybody can see. The counter is
	 * a number this page can compare against a number it wrote itself, and both
	 * timestamps in the comparison come from the clock of Nextcloud.
	 *
	 * **Only growth counts.** A counter that fell is a reindex or a data
	 * directory that was cleared, and neither is progress. A counter that stands
	 * still says nothing at all, which is exactly the situation in which the
	 * background job half decides.
	 *
	 * **The first observation of an instance is deliberately not progress.** The
	 * remembered value is nought before the page has ever seen an answer, so a
	 * container that has been indexing for a week and is now genuinely stuck
	 * would look like a jump from nought to fifty thousand and buy itself half an
	 * hour of silence. Requiring a previous figure costs one poll, five seconds,
	 * on a fresh installation and nothing afterwards.
	 *
	 * The write follows the same rule as the two remembered figures above: only
	 * when the value changes, so a page polling every five seconds writes only
	 * while the indexing is actually moving.
	 *
	 * The decision itself is in progressStamp below, which is the same method
	 * without the reading and the writing. Splitting it is what makes it
	 * testable at all: this one needs an appconfig and a container, and that one
	 * needs four numbers.
	 */
	private function backendProgressAt(bool $reachable, int $indexed, int $remembered, int $now): int {
		$stamp = max(0, $this->appConfig->getValueInt(Application::APP_ID, self::KEY_INDEX_PROGRESS));
		$moved = self::progressStamp($reachable, $indexed, $remembered, $stamp, $now);
		if ($moved !== $stamp) {
			$this->appConfig->setValueInt(Application::APP_ID, self::KEY_INDEX_PROGRESS, $moved);
		}

		return $moved;
	}

	/**
	 * The stamp of the last container progress, decided out of five numbers.
	 *
	 * Static and public because it is the arithmetic of DI-05-22 and nothing
	 * else, and because the alternative to that is a unit test which builds a
	 * whole admin view out of twelve doubles in order to ask what a counter that
	 * grew by one means. The reasoning behind every branch is at
	 * backendProgressAt above, which is this method plus the appconfig around
	 * it.
	 *
	 * Returns the previous stamp when nothing moved, so an unchanged answer is
	 * also the signal that nothing has to be written.
	 */
	public static function progressStamp(bool $reachable, int $indexed, int $remembered, int $stamp, int $now): int {
		if (!$reachable || $remembered <= 0 || $indexed <= $remembered) {
			return $stamp;
		}

		return $now;
	}

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
	 * The eighteen status fields of the container, rebuilt one by one.
	 *
	 * Called with null as well, and then it returns the same eighteen keys as
	 * zeros, false and empty strings. That is what keeps the caller free of a
	 * second code path: a page that renders "container silent" out of the same
	 * shape it renders a healthy container from cannot forget one of the two.
	 *
	 * ``embedded`` is the one exception to that rule and it is deliberate. It is
	 * null when the container did not report it, which is what a container older
	 * than this app looks like, and null is the only value that keeps that state
	 * apart from a container whose second track has not started. Nought would
	 * merge the two into "no document is findable by meaning", which is a claim
	 * about an instance nobody asked (D-16).
	 *
	 * @param array<mixed>|null $answer the decoded body, or null when there was none
	 * @return array<string,mixed>
	 */
	private function backend(?array $answer): array {
		$answer ??= [];

		return [
			'indexed' => $this->counter($answer, 'indexed'),
			'truncated' => $this->counter($answer, 'truncated'),
			'embedded' => $this->optionalCounter($answer, 'embedded'),
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
	 * One counter of the container answer that may be missing, as null.
	 *
	 * The same judgement as counter() above with one difference: a value that is
	 * not there and a value of nought are two different findings here, and the
	 * caller decides what to do with each. Used for exactly one field, and the
	 * reason it exists rather than being a nullable branch inside counter() is
	 * that every other counter of this protocol is a number this container can
	 * always answer, so making them all nullable would put a null check on
	 * seventeen call sites in order to serve one.
	 *
	 * @param array<mixed> $answer
	 */
	private function optionalCounter(array $answer, string $key): ?int {
		$value = $answer[$key] ?? null;

		return is_int($value) && $value >= 0 ? $value : null;
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
