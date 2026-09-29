<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCP\AppFramework\Utility\ITimeFactory;
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
	 * The performance profile the container runs with (D-24-01, path B).
	 *
	 * Public because ProfileController hands it to the container and the admin
	 * page writes it: one place names the key, so a second spelling cannot
	 * create a key nobody reads. The admin page writes it through saveProfile()
	 * after the probe; ``occ config:app:set findling profile --value=standard``
	 * stays the documented second way in, and that one skips the probe
	 * (D-27-13). The container pulls the value once per round, nothing pushes it.
	 */
	public const KEY_PROFILE = 'profile';

	/**
	 * The closed set of profile names, and the only names profile() hands out.
	 *
	 * Has to stay identical to PROFILE_NAMES in backend/src/findling/profile.py.
	 * A parity test on the Python side compares the two textually, which is why
	 * this list keeps exactly this one line spelling.
	 */
	public const PROFILES = ['economy', 'standard', 'performance'];

	/**
	 * The profile of a fresh install and of every value outside the set: the
	 * frugal one, because the hardware target is a small box and a wrong guess
	 * upwards costs memory, a wrong guess downwards only speed.
	 */
	public const PROFILE_DEFAULT = 'economy';

	/**
	 * The precision of the embedding model (D-25-02), a key of its own.
	 *
	 * Separate from KEY_PROFILE on purpose: a profile is a question of speed
	 * and memory, the precision decides which vectors are in the index, and a
	 * change of it means a reindex of the vector track. Coupling the two would
	 * turn a harmless profile change into exactly that. Handed to the container
	 * through the profile route, in the same answer and the same round
	 * (D-24-01). The admin page writes it through saveProfile() after the
	 * probe; ``occ config:app:set findling model_precision --value=fp32`` stays
	 * the documented second way in, and that one skips the probe (D-27-13).
	 */
	public const KEY_MODEL_PRECISION = 'model_precision';

	/**
	 * The closed set of precision names, and the only names modelPrecision()
	 * hands out.
	 *
	 * Has to stay identical to PRECISION_NAMES in backend/src/findling/precision.py.
	 * A parity test on the Python side compares the two textually, which is why
	 * this list keeps exactly this one line spelling.
	 */
	public const PRECISIONS = ['int8', 'fp32'];

	/**
	 * The precision of a fresh install: the int8 model baked into the image,
	 * which needs no download and fits the small box.
	 */
	public const PRECISION_DEFAULT = 'int8';

	/**
	 * The confirmation token of the admin (D-26-04), the way back after the
	 * memory guard of the container lowered its profile.
	 *
	 * The token is not made up here. The container shows it on its status
	 * route when the guard lowered a profile (D-26-01), 32 lowercase hex
	 * characters. The admin confirms with the "check again" button of the admin
	 * page, which stores the token through saveConfirmation() once the probe
	 * said it fits (D-27-12); ``occ config:app:set findling profile_confirmed
	 * --value=<token>`` stays the second way in without a probe (D-27-13). The
	 * container lifts the lowering as soon as the stored token equals its own;
	 * nothing raises the profile again automatically. Read-only for the
	 * container: there is no write path from the container into this key.
	 */
	public const KEY_PROFILE_CONFIRMED = 'profile_confirmed';

	/**
	 * The result of the last probe (D-27-04, D-27-10), an array of its own.
	 *
	 * Written by the probe flow of the admin page when a probe ended, read by
	 * the admin view to render the last verdict card. In appconfig and not in
	 * the state.db of the container, because the page renders on the PHP side
	 * and has to show the verdict while the container is silent, and because a
	 * verdict does not expire: it holds for the moment of saving, and later
	 * hardware changes are the business of the effective level and the guard.
	 * Nothing in the container reads it.
	 */
	public const KEY_PROFILE_CHECK = 'profile_check';

	/**
	 * The probe that is running right now, or absent.
	 *
	 * Written when the admin page started a probe, deleted when its verdict was
	 * taken over into KEY_PROFILE_CHECK. Read by the page so that a second tab,
	 * or a reload in the middle of a probe, joins the running one instead of
	 * starting another. appconfig for the same reason as above: the page has to
	 * know about it without asking the container first.
	 */
	public const KEY_PROFILE_CHECK_PENDING = 'profile_check_pending';

	/**
	 * Since when the files of this instance changed without the denominator of
	 * the coverage figure having been counted again, as a unix time; zero means
	 * nothing changed since the last recount (quick task 260929-kii).
	 *
	 * Written by the event listener and by save(), read and cleared by
	 * ScanRecountJob. A mark and not a counter on purpose: the listener cannot
	 * tell reliably what an event does to the denominator (the docblock of
	 * ScanRecountJob lists why), so it only says "something changed" and the
	 * recount measures what.
	 */
	public const KEY_SCAN_STALE_SINCE = 'scan_stale_since';

	/**
	 * When ScanRecountJob last started a recount, as a unix time; zero before
	 * the first one.
	 */
	public const KEY_SCAN_RECOUNTED_AT = 'scan_recounted_at';

	/**
	 * The longest a quiet instance goes without a recount, one day.
	 *
	 * A change that no event announced (occ files:scan, a file written straight
	 * into the data directory, an external storage changing on its own side)
	 * still reaches the denominator within this time, and on a quiet instance a
	 * recount costs one metadata walk per mount and day.
	 */
	public const RECOUNT_FLOOR_SECONDS = 86400;

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
		private ITimeFactory $timeFactory,
	) {
	}

	/**
	 * Mark the denominator as behind the files of the instance.
	 *
	 * Called by the event listener for every file operation on an indexed mount
	 * and by save(). Writes only on the change from zero to a time: the read is
	 * a cached appconfig lookup, so a busy instance pays one write per recount
	 * round and not one per upload.
	 */
	public function markScanStale(): void {
		if ($this->appConfig->getValueInt(Application::APP_ID, self::KEY_SCAN_STALE_SINCE, 0) !== 0) {
			return;
		}

		$this->appConfig->setValueInt(Application::APP_ID, self::KEY_SCAN_STALE_SINCE, max(1, $this->timeFactory->getTime()));
	}

	/**
	 * Whether a recount is due: something changed since the last one, or the
	 * last one is a day old (or there never was one).
	 */
	public function scanRecountDue(int $now): bool {
		if ($this->appConfig->getValueInt(Application::APP_ID, self::KEY_SCAN_STALE_SINCE, 0) !== 0) {
			return true;
		}

		$last = $this->appConfig->getValueInt(Application::APP_ID, self::KEY_SCAN_RECOUNTED_AT, 0);

		return $now - $last >= self::RECOUNT_FLOOR_SECONDS;
	}

	/**
	 * A recount starts now: the mark goes back to zero and the time is
	 * remembered.
	 *
	 * Called by ScanRecountJob BEFORE it plans the chains, so that an event
	 * arriving while the recount walks marks the instance again and triggers
	 * the next round instead of being swallowed by this one.
	 */
	public function beginRecount(int $now): void {
		$this->appConfig->setValueInt(Application::APP_ID, self::KEY_SCAN_STALE_SINCE, 0);
		$this->appConfig->setValueInt(Application::APP_ID, self::KEY_SCAN_RECOUNTED_AT, $now);
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
	 * The profile in force, always a name out of PROFILES.
	 *
	 * Validated on read and not only on write, because the write path of phase
	 * 24 is ``occ config:app:set``, the unchecked second way in that the save()
	 * docblock names: a typo there must not reach the container as a profile it
	 * does not know. A value outside the set falls back to PROFILE_DEFAULT and
	 * is counted by reject(), which never logs the value itself.
	 */
	public function profile(): string {
		$stored = $this->appConfig->getValueString(
			Application::APP_ID,
			self::KEY_PROFILE,
			self::PROFILE_DEFAULT,
		);

		if (!in_array($stored, self::PROFILES, true)) {
			$this->reject();

			return self::PROFILE_DEFAULT;
		}

		return $stored;
	}

	/**
	 * The model precision in force, a name out of PRECISIONS, or null.
	 *
	 * An absent key is PRECISION_DEFAULT. A stored value outside the set is
	 * counted by reject(), which never logs the value, and answered with null,
	 * and that is the one deliberate difference to profile() above. A profile
	 * that falls back to its default costs speed for one round; a precision that
	 * fell back to int8 on a fp32 box would make the container reindex the
	 * vector track and delete the fp32 model it downloaded, for a typo in occ.
	 * null tells the container "not readable", and its rule for that is to keep
	 * the last known precision (D-24-02, D-25-03).
	 */
	public function modelPrecision(): ?string {
		$stored = $this->appConfig->getValueString(
			Application::APP_ID,
			self::KEY_MODEL_PRECISION,
			self::PRECISION_DEFAULT,
		);

		if (!in_array($stored, self::PRECISIONS, true)) {
			$this->reject();

			return null;
		}

		return $stored;
	}

	/**
	 * The confirmation token the admin stored, or null.
	 *
	 * An absent key is null without a warning: that is the ordinary state of
	 * every instance whose guard never lowered anything. A stored value that is
	 * not exactly 32 lowercase hex characters is counted by reject(), which
	 * never logs the value, and answered with null as well, the same rule as
	 * modelPrecision(): the only effect a token can have is lifting a lowering,
	 * so a typo must fall on the side that keeps the lowering (T-26-05).
	 */
	public function profileConfirmed(): ?string {
		$stored = $this->appConfig->getValueString(
			Application::APP_ID,
			self::KEY_PROFILE_CONFIRMED,
			'',
		);

		if ($stored === '') {
			return null;
		}

		// D: without it $ also matches before a trailing newline, and a token
		// with a newline appended would pass.
		if (preg_match('/^[0-9a-f]{32}$/D', $stored) !== 1) {
			$this->reject();

			return null;
		}

		return $stored;
	}

	/**
	 * Whether an admin ever stored a profile, as opposed to running on the
	 * default.
	 *
	 * profile() cannot tell the two apart, and must not: both answer economy
	 * (SC1, without a click the box stays frugal). The page can, and has to,
	 * because "nothing chosen yet" and "economy chosen" are different lines on
	 * it. hasKey() and not a sentinel default, so no string can be mistaken for
	 * the absence of one.
	 */
	public function profileStored(): bool {
		return $this->appConfig->hasKey(Application::APP_ID, self::KEY_PROFILE);
	}

	/**
	 * Whether a change to this profile and precision has to go through the
	 * probe first (D-27-09), decided here and never in the browser.
	 *
	 * No probe exactly when the target is economy, or when the target profile
	 * is the stored one and the one change is fp32 to int8: less load cannot
	 * fail to fit, and that is also the way back after a "does not fit".
	 * Everything else needs the probe, performance to standard included, which
	 * is not a safe way down. A stored precision that is unreadable counts as
	 * int8, so an unreadable fp32 never opens a way without a probe. A value
	 * outside the closed sets always needs the probe, and the writer refuses it
	 * anyway.
	 */
	public function needsProbe(string $profile, string $precision): bool {
		if (!$this->validPair($profile, $precision)) {
			return true;
		}

		if ($profile === self::PROFILE_DEFAULT) {
			return false;
		}

		$storedPrecision = $this->modelPrecision() ?? self::PRECISION_DEFAULT;

		return !($profile === $this->profile() && $storedPrecision === 'fp32' && $precision === 'int8');
	}

	/**
	 * The downward way of D-27-09: a valid target that needs no probe. The
	 * write route stores without a probe only when this is true (T-27-09).
	 */
	public function isDownward(string $profile, string $precision): bool {
		return $this->validPair($profile, $precision) && !$this->needsProbe($profile, $precision);
	}

	/**
	 * Store profile and precision together, or neither (D-24-01, path B).
	 *
	 * Validates again rather than trusting the controller, the same rule as
	 * save(): strict against the closed sets, so a value of another type or
	 * another case never reaches appconfig (T-27-08). fp32 next to economy is
	 * accepted only as the state that is already stored, because switching to
	 * economy keeps the precision (D-25-10), while setting fp32 on an economy
	 * box is a change the page does not offer (D-27-01).
	 *
	 * The profile is written first. If the second write fails, what is left is
	 * the new profile with the old precision, and that is never heavier than the
	 * pair the probe checked. The log line is static and carries the exception
	 * only, no value.
	 */
	public function saveProfile(string $profile, string $precision): bool {
		if (!$this->validPair($profile, $precision)) {
			$this->reject();

			return false;
		}

		if ($profile === self::PROFILE_DEFAULT && $precision === 'fp32' && $this->modelPrecision() !== 'fp32') {
			$this->reject();

			return false;
		}

		try {
			$this->appConfig->setValueString(Application::APP_ID, self::KEY_PROFILE, $profile);
			$this->appConfig->setValueString(Application::APP_ID, self::KEY_MODEL_PRECISION, $precision);
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not store the profile', ['exception' => $e]);

			return false;
		}

		return true;
	}

	/**
	 * Store the confirmation token of the container (D-26-04, D-27-12).
	 *
	 * Only exactly 32 lowercase hex characters, the same form profileConfirmed()
	 * reads, with the same D anchor: without it a token with a trailing newline
	 * would pass here and be refused on the way out.
	 */
	public function saveConfirmation(string $token): bool {
		if (preg_match('/^[0-9a-f]{32}$/D', $token) !== 1) {
			$this->reject();

			return false;
		}

		try {
			$this->appConfig->setValueString(Application::APP_ID, self::KEY_PROFILE_CONFIRMED, $token);
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not store the confirmation', ['exception' => $e]);

			return false;
		}

		return true;
	}

	/**
	 * The result of the last probe, or null when there never was one.
	 *
	 * A read that fails is null as well, which renders as "no probe yet" and
	 * never as a verdict nobody reached.
	 *
	 * @return array<mixed>|null
	 */
	public function profileCheck(): ?array {
		return $this->storedArray(self::KEY_PROFILE_CHECK);
	}

	/**
	 * Remember the result of a probe. It stays until the next probe replaces
	 * it; a verdict does not expire (D-27-10).
	 *
	 * @param array<mixed> $check
	 */
	public function rememberProfileCheck(array $check): void {
		$this->appConfig->setValueArray(Application::APP_ID, self::KEY_PROFILE_CHECK, $check);
	}

	/**
	 * The probe that is running, or null.
	 *
	 * @return array<mixed>|null
	 */
	public function profileCheckPending(): ?array {
		return $this->storedArray(self::KEY_PROFILE_CHECK_PENDING);
	}

	/**
	 * Remember the probe that was just started.
	 *
	 * @param array<mixed> $pending
	 */
	public function rememberPending(array $pending): void {
		$this->appConfig->setValueArray(Application::APP_ID, self::KEY_PROFILE_CHECK_PENDING, $pending);
	}

	/** Forget the running probe once its verdict was taken over. */
	public function forgetPending(): void {
		$this->appConfig->deleteKey(Application::APP_ID, self::KEY_PROFILE_CHECK_PENDING);
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

		// The cap and both switches decide what the denominator holds (and the
		// exclusions saved next to this call as well), so the next recount has
		// to measure again instead of waiting a day.
		$this->markScanStale();

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

	/** Both names out of their closed sets, compared strictly. */
	private function validPair(string $profile, string $precision): bool {
		return in_array($profile, self::PROFILES, true) && in_array($precision, self::PRECISIONS, true);
	}

	/**
	 * One stored array, null when absent, empty or unreadable. The log line of
	 * a failed read is static: what the key holds is a probe record, and none of
	 * it belongs into the log.
	 *
	 * @return array<mixed>|null
	 */
	private function storedArray(string $key): ?array {
		try {
			$stored = $this->appConfig->getValueArray(Application::APP_ID, $key, []);
		} catch (\Throwable $e) {
			$this->logger->warning('Findling: could not read the probe record', ['exception' => $e]);

			return null;
		}

		return $stored === [] ? null : $stored;
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
