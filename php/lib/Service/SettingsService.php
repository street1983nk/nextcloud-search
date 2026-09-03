<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCP\IAppConfig;
use Psr\Log\LoggerInterface;

/**
 * The four things an admin may change, and the only four (ADM-04, D-08).
 *
 * Folder exclusions, the size cap, Team Folders on or off and external storage
 * on or off. Nothing else on the page writes, and there is no "advanced"
 * section: a settings screen with twenty options contradicts the zero config
 * promise this app is built on, so the number of switches is a decision and not
 * an omission.
 *
 * None of the four needs a transport into the container, which is the central
 * finding of the phase research (pattern 8). Every one of them sits at a PHP
 * source the container pulls from: the mount list behind ``GET /mounts``, the
 * file slice behind ``GET /files/slice`` and the work stock behind
 * ``GET /queues/documents``. So the values are written here and the next run
 * reads them. Nothing restarts, and no container has to be touched.
 *
 * The keys live in appconfig of the app ``findling``, next to the existing
 * ``last_job_run`` of SchedulerJob, which stays untouched. IAppConfig caches per
 * request, so the crawl reads once per slice and the event listener once per
 * write operation. That is exactly the semantics D-08 promises, "the next run
 * applies it", and it needs no invalidation of its own. A cache on a service
 * field with a longer life would be wrong here.
 *
 * The code constants stay where they were measured. ``StorageCrawlJob::MAX_SIZE``
 * and the three provider lists of StorageService remain in the code as the
 * documented default, and this class hands out the value in force with exactly
 * those constants as its default. A default that only exists in a database row
 * cannot be read by somebody looking at the file that uses it.
 *
 * Nothing here logs a value that arrived from outside. A rejected input is
 * counted and the counter is logged, after the pattern of
 * FileStateService::reject(): what arrives in a prefix field is a folder name of
 * a private instance, and a log line is the one place where that would leave the
 * permission model (T-04-51).
 */
final class SettingsService {
	/**
	 * The four keys of D-08, and the fifth that makes the clamping of the cap
	 * survive a silent container.
	 *
	 * Public because ExclusionService reads and writes the exclusion list and
	 * the admin view reads the rest: one place names the keys, so a typo in a
	 * second spelling cannot create a key nobody reads.
	 */
	public const KEY_EXCLUSIONS = 'exclusions';
	public const KEY_MAX_FILE_BYTES = 'max_file_bytes';
	public const KEY_INDEX_TEAM_FOLDERS = 'index_team_folders';
	public const KEY_INDEX_EXTERNAL_STORAGE = 'index_external_storage';

	/**
	 * The ceiling the container last reported, remembered so that the clamping
	 * below still works while the container does not answer.
	 *
	 * Not one of the four switches and deliberately not on the page as an input:
	 * it is a measurement of the other side, written by the admin view whenever
	 * the container answered, and read by maxFileBytes(). An admin who wants a
	 * higher ceiling raises FINDLING_MAX_FILE_BYTES in the AppAPI app settings,
	 * which restarts the container, because that variable is read at start.
	 */
	public const KEY_CONTAINER_CAP = 'container_max_file_bytes';

	/**
	 * The last indexed count the container reported, another measurement of the
	 * other side. The banner over the coverage block promises "the last ones
	 * this app recorded" for a silent container, and this key is that record:
	 * without it the tile would fall back to the Nextcloud side of the state
	 * table, which holds no indexed rows by construction, and the figure would
	 * jump to zero at exactly the moment the admin needs it to hold still.
	 */
	public const KEY_LAST_INDEXED = 'last_indexed_count';

	/**
	 * The lower end of the size cap, one megabyte.
	 *
	 * Below it the setting would stop being a limit and start being an outage:
	 * essentially every scanned PDF of a German office is larger than a
	 * megabyte, so a cap under it would report almost the whole instance as
	 * skipped(too_large) while looking like a deliberate configuration.
	 */
	public const MIN_CAP_BYTES = 1048576;

	/**
	 * The field error codes this class hands back, and codes rather than
	 * sentences on purpose.
	 *
	 * The page owns the wording, in the language of the admin and word for word
	 * out of the design contract. A code travels back instead, so the answer of
	 * this route can never carry a value somebody typed, which is the same rule
	 * the log follows one paragraph up.
	 */
	public const FIELD_MAX_FILE_BYTES = 'maxFileBytes';
	public const ERROR_OUT_OF_RANGE = 'out_of_range';

	/** Counter of everything that was refused, for the log line below. */
	private int $rejected = 0;

	public function __construct(
		private IAppConfig $appConfig,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * The size cap in force, clamped at both ends.
	 *
	 * Clamped and not merely validated, because the container enforces the same
	 * cap a second time and cannot be told about this one (pitfall 2):
	 * ``nc/client.py`` caps the download at ``settings().max_file_bytes`` and
	 * ``extract/dispatch.py`` checks the size once more, while ``settings()`` is
	 * lru_cached and reads nothing but environment variables. A PHP value above
	 * ``FINDLING_MAX_FILE_BYTES`` would therefore have no effect at all: the file
	 * would be queued, the container would break the download off and write
	 * skipped(too_large), and the page would show a cap of a hundred megabytes
	 * next to a file that was skipped for being too large. That is precisely the
	 * contradiction this phase exists to remove.
	 *
	 * So the value is clamped rather than warned about, and the page never shows
	 * a number that does not hold. Without a remembered container ceiling the
	 * upper end is the code default, which is the value both sides ship with.
	 */
	public function maxFileBytes(): int {
		$stored = $this->appConfig->getValueInt(
			Application::APP_ID,
			self::KEY_MAX_FILE_BYTES,
			StorageCrawlJob::MAX_SIZE,
		);

		return $this->clamped($stored);
	}

	/**
	 * The upper end of the cap: what the container last said it reads at the
	 * most, or the code default while it has never said anything.
	 *
	 * This is the ``max`` attribute of the input field as well, which is why it
	 * is public: the page has to be able to say what the ceiling is, otherwise
	 * an admin types a number, gets it silently lowered and learns nothing.
	 */
	public function containerCap(): int {
		$remembered = $this->appConfig->getValueInt(Application::APP_ID, self::KEY_CONTAINER_CAP, 0);

		return $remembered >= self::MIN_CAP_BYTES ? $remembered : StorageCrawlJob::MAX_SIZE;
	}

	/**
	 * Remember what the container reported as its own ceiling.
	 *
	 * Called by the admin view with ``backend.maxFileBytes`` whenever the
	 * container answered, so that the clamping still holds on the day it does
	 * not. A value below the floor is refused instead of remembered: it would
	 * clamp every setting into a cap that indexes nothing, and a container that
	 * reports it is either misconfigured or was not the container.
	 *
	 * Written only when it changed. The page polls every five seconds, and an
	 * unconditional write would be one appconfig update per poll for a value
	 * that moves when somebody restarts a container.
	 */
	public function rememberContainerCap(int $bytes): void {
		if ($bytes < self::MIN_CAP_BYTES) {
			$this->reject();
			return;
		}

		if ($bytes === $this->appConfig->getValueInt(Application::APP_ID, self::KEY_CONTAINER_CAP, 0)) {
			return;
		}

		$this->appConfig->setValueInt(Application::APP_ID, self::KEY_CONTAINER_CAP, $bytes);
	}

	/**
	 * The last indexed count the container reported, zero before the first
	 * answer. Read by the admin view when the container is silent, so that the
	 * tile shows the figure of the last answer instead of a zero it never
	 * reported.
	 */
	public function lastIndexedCount(): int {
		return max(0, $this->appConfig->getValueInt(Application::APP_ID, self::KEY_LAST_INDEXED, 0));
	}

	/**
	 * Remember the indexed count of a container answer. Written only when it
	 * changed, for the same reason as the cap above: the page polls every five
	 * seconds and the figure moves only while indexing makes progress.
	 */
	public function rememberIndexedCount(int $indexed): void {
		if ($indexed < 0) {
			return;
		}

		if ($indexed === $this->appConfig->getValueInt(Application::APP_ID, self::KEY_LAST_INDEXED, 0)) {
			return;
		}

		$this->appConfig->setValueInt(Application::APP_ID, self::KEY_LAST_INDEXED, $indexed);
	}

	/**
	 * Whether Team Folders are walked. On by default.
	 *
	 * A Team Folder is a shared workspace of the instance itself, its files live
	 * on local storage like a home does, and it is where the documents of a small
	 * organisation actually are. Leaving it out by default would make the search
	 * miss the half of the instance people search for most.
	 */
	public function indexTeamFolders(): bool {
		return $this->appConfig->getValueBool(Application::APP_ID, self::KEY_INDEX_TEAM_FOLDERS, true);
	}

	/**
	 * Whether external storage is walked. Off by default.
	 *
	 * A remote drive blows up every assumption the first index makes about how
	 * long reading a file takes and how much of it there is, and an admin who
	 * mounted a multi terabyte share does not expect installing an app to start
	 * pulling it through HTTP. Switching it on is an explicit decision with the
	 * consequence written next to the switch (T-04-52).
	 */
	public function indexExternalStorage(): bool {
		return $this->appConfig->getValueBool(Application::APP_ID, self::KEY_INDEX_EXTERNAL_STORAGE, false);
	}

	/**
	 * Judge an input without writing anything.
	 *
	 * Separate from save() because the write route has to be able to refuse the
	 * whole form before it has changed a single value. One invalid field and
	 * nothing at all is written, so there is no half state in which the cap moved
	 * and the exclusions did not, and the answer says so in as many words.
	 *
	 * The two booleans cannot be invalid: the route declares them as bool, so the
	 * framework has already decided what arrived. Only the cap has a range.
	 *
	 * @param array{maxFileBytes?: int} $input
	 * @return array<string, string> field name to error code, empty when it fits
	 */
	public function validate(array $input): array {
		$bytes = (int)($input[self::FIELD_MAX_FILE_BYTES] ?? 0);
		if ($bytes !== $this->clamped($bytes)) {
			$this->reject();

			return [self::FIELD_MAX_FILE_BYTES => self::ERROR_OUT_OF_RANGE];
		}

		return [];
	}

	/**
	 * Write the three values this class owns, or none of them.
	 *
	 * Validates again rather than trusting the caller. The route validates first
	 * so that it can refuse the whole form, and ``occ config:app:set`` is a second
	 * way in that this method never sees, so a method that wrote whatever it was
	 * handed would be one code path away from an unchecked value in appconfig.
	 *
	 * @param array{maxFileBytes?: int, indexTeamFolders?: bool, indexExternalStorage?: bool} $input
	 * @return array<string, string> field name to error code, empty when it was written
	 */
	public function save(array $input): array {
		$errors = $this->validate($input);
		if ($errors !== []) {
			return $errors;
		}

		$this->appConfig->setValueInt(
			Application::APP_ID,
			self::KEY_MAX_FILE_BYTES,
			(int)($input[self::FIELD_MAX_FILE_BYTES] ?? StorageCrawlJob::MAX_SIZE),
		);
		$this->appConfig->setValueBool(
			Application::APP_ID,
			self::KEY_INDEX_TEAM_FOLDERS,
			($input['indexTeamFolders'] ?? true) === true,
		);
		$this->appConfig->setValueBool(
			Application::APP_ID,
			self::KEY_INDEX_EXTERNAL_STORAGE,
			($input['indexExternalStorage'] ?? false) === true,
		);

		return [];
	}

	/**
	 * One value held inside the two ends of the range.
	 *
	 * The one place the range exists, so that the reader, the validator and the
	 * page cannot disagree about what is allowed.
	 */
	private function clamped(int $bytes): int {
		return max(self::MIN_CAP_BYTES, min($this->containerCap(), $bytes));
	}

	/**
	 * A refused value, counted and never written out.
	 *
	 * The same rule as FileStateService::reject(): the value itself is input
	 * somebody wrote, a folder name of a private instance arrives in exactly
	 * these fields, and writing it into the log instead of the database would
	 * only move the leak.
	 */
	private function reject(): void {
		$this->rejected++;
		$this->logger->warning(
			'Findling: refused a settings value that is outside its range',
			['rejected' => $this->rejected],
		);
	}
}
