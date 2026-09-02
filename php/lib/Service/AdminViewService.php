<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\BackgroundJobs\SchedulerJob;
use OCA\Findling\Text\PlainText;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IAppConfig;
use OCP\IUserSession;

/**
 * The one place where the numbers of Nextcloud and the numbers of the container
 * meet, and the only one.
 *
 * Two sources answer the same questions and they are allowed to disagree. The
 * split is therefore written down here rather than being discovered later:
 *
 * - Out of ``findling_file_state``, which is this side of the boundary:
 *   ``skipped`` and ``failed``. These survive a stopped container, which is the
 *   whole reason the table exists, and they are what the page falls back to.
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

	public function __construct(
		private FileStateService $fileStateService,
		private QueueService $queueService,
		private ExAppService $exAppService,
		private ScanStatsService $scanStats,
		private IAppConfig $appConfig,
		private IUserSession $userSession,
		private ITimeFactory $timeFactory,
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
	 *     backend:array<string,mixed>, coverage:array<string,mixed>
	 * }
	 */
	public function overview(): array {
		$states = $this->fileStateService->counts();
		$queue = $this->queueService->stats();
		$scan = $this->scanStats->totals();

		$scheduled = (int)($queue['scheduled'] ?? 0);
		$running = (int)($queue['running'] ?? 0);

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
			'coverage' => $this->coverage($scan, $backend, $backendReachable),
		];
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
	 * The denominator is filesSeen minus overCap minus excluded, and that
	 * subtraction happens here and exactly once in this file. It is word for
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
	 * @return array{
	 *     indexed:int, indexable:int, deliberatelyLeftOut:int, percent:int|null,
	 *     provisional:bool, mountsTotal:int, mountsFinished:int
	 * }
	 */
	private function coverage(array $scan, array $backend, bool $backendReachable): array {
		$overCap = max(0, (int)$scan['overCap']);
		$excluded = max(0, (int)$scan['excluded']);
		$indexable = max(0, (int)$scan['filesSeen'] - $overCap - $excluded);

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
