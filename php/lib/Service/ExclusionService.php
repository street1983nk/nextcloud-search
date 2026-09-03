<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\BackgroundJobs\SubtreeExpandJob;
use OCA\Findling\Db\QueueMapper;
use OCP\BackgroundJob\IJobList;
use OCP\IAppConfig;
use Psr\Log\LoggerInterface;

/**
 * The folder exclusions, and the one comparison that decides them.
 *
 * A prefix match on the path, without wildcards and without patterns. That is
 * D-06 and it is a decision about the audience rather than about the code: an
 * admin of a small instance can say what "Backups" leaves out, and nobody has to
 * find out what a glob does to a folder whose name contains a bracket. A pattern
 * language would be one line more here and a support case for every instance
 * that guessed wrong.
 *
 * Where the prefixes apply, in full, and this paragraph was made precise in plan
 * 04-09 because the clearing and the diagnosis both had to rely on it. A prefix
 * is compared relative to the ROOT OF THE MOUNT a file lies on, in every mount
 * this app walks, and mountRelativePath() below is the one place that space is
 * built. In a user home that root is the ``files`` folder of the user, so
 * ``Archiv``, ``Backups`` and ``.stversions`` mean what an admin expects and mean
 * it in every home at once, which is the reading of D-06. On a Team Folder or an
 * external mount the root is the mount root, so the same prefix names a folder at
 * the top of that mount; those two mounts additionally have their own all or
 * nothing switch in SettingsService, so an instance that does not want them
 * indexed at all does not need a prefix for them.
 *
 * The earlier wording of this paragraph said the prefixes apply in homes only.
 * That was never what the code did, and the difference is not cosmetic: whatever
 * the crawl leaves out, the clearing has to remove and the diagnosis has to
 * explain, or the index keeps content the rules say is not in it and the page
 * says a file is about to be indexed when nothing will ever index it. So there is
 * one rule for all three, mountRelativePathInStorage() puts the diagnosis on the
 * same space as the crawl, and scheduleCleanup() plans one subtree per mount the
 * prefix resolves in.
 *
 * An excluded file is not a file that vanished. It shows up in the diagnosis
 * with the reason ``excluded``, with the label and the remedy of the same closed
 * table every other reason uses, because a file that silently stops being
 * findable is the whole failure this phase removes (IDX-06).
 *
 * What is deliberately NOT done: no row per excluded file in
 * ``findling_file_state``. On an excluded archive folder holding two hundred
 * thousand files that would be two hundred thousand rows for an answer that
 * follows from four comparisons, and it would also be wrong the moment the
 * prefix is taken away again. The diagnosis works the reason out live instead,
 * which is stage two of the precedence rule of plan 04-07, and the crawl counts
 * the files it left alone in the scan counters so that the tile on the page has
 * a number.
 *
 * Nothing here logs a prefix, a path or a file name. A refused entry is counted
 * and the counter is logged, after the pattern of FileStateService::reject():
 * what arrives in a prefix field is a folder name of a private instance
 * (T-04-51).
 */
final class ExclusionService {
	/**
	 * How many prefixes the list may hold, and how long one of them may be.
	 *
	 * Sixty four and two hundred and fifty six, and both are a cost rather than
	 * a taste. Every write on the instance runs isExcluded() once, so the list
	 * length is a factor on the write path of the whole server, and the entry
	 * length is what one comparison costs (T-04-48). Named constants because
	 * both numbers appear in the validation and in the defensive read, and two
	 * literals would drift the day one of them is raised.
	 */
	public const MAX_PREFIXES = 64;
	public const MAX_PREFIX_LENGTH = 256;

	/**
	 * How far the preview of affectedDocuments() counts before it stops.
	 *
	 * Five thousand, and the ceiling is the whole point of the method. The number
	 * is shown while an admin waits for a form to save, and counting the true
	 * total means walking the subtree of every new prefix in every mount, which is
	 * minutes on an instance with a large archive folder (T-04-57). A number the
	 * page shows as "at least 5000" is honest and immediate; an exact number
	 * nobody waits for is neither.
	 *
	 * Reaching the ceiling is reported as reached, so the page can say "at least".
	 * A subtree of exactly this size is therefore announced with "at least 5000"
	 * as well, which is true, and the alternative would be one more band of
	 * queries to tell two identical sentences apart.
	 */
	public const PREVIEW_CAP = 5000;

	/**
	 * Entries per query while the preview counts.
	 *
	 * Five hundred, so the ceiling above is ten queries per subtree at the very
	 * most and one query for the ordinary case of a folder with a handful of
	 * documents in it. The enumeration is ordered by file id, so a band is a
	 * range and not a sample, and the cursor is the last id of the previous band.
	 */
	private const PREVIEW_BAND = 500;

	/**
	 * The error codes of the list, and codes rather than sentences for the same
	 * reason as in SettingsService: the answer of the write route must never
	 * carry a value somebody typed.
	 */
	public const FIELD_EXCLUSIONS = 'exclusions';
	public const ERROR_EMPTY = 'empty';
	public const ERROR_TOO_LONG = 'too_long';
	public const ERROR_TRAVERSAL = 'traversal';
	public const ERROR_DUPLICATE = 'duplicate';
	public const ERROR_TOO_MANY = 'too_many';

	/**
	 * The folder every home mount carries between the storage root and the files
	 * of the user. Named once, because it is stripped in two places below and a
	 * second literal is how the two would stop agreeing.
	 */
	private const HOME_FILES_FOLDER = 'files';

	/**
	 * The normalised list, resolved once per request.
	 *
	 * The same lifetime as the storage lookup of StorageService and never
	 * longer. IAppConfig caches per request already, so this field saves the
	 * normalisation and not the read, and a longer lived cache would break the
	 * one promise of D-08: the next run applies the new rules.
	 *
	 * @var list<string>|null
	 */
	private ?array $cached = null;

	/** Counter of everything that was refused, for the log line below. */
	private int $rejected = 0;

	public function __construct(
		private IAppConfig $appConfig,
		private StorageService $storageService,
		private IJobList $jobList,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * The prefixes in force, normalised.
	 *
	 * Normalised defensively on the way out, not only on the way in, because
	 * appconfig has a second writer: ``occ config:app:set findling exclusions``
	 * is a scriptable way in that never passes through save() below. An entry
	 * this method cannot make sense of is dropped and counted rather than
	 * compared, so a malformed row cannot turn into a prefix that matches
	 * everything.
	 *
	 * @return list<string>
	 */
	public function prefixes(): array {
		if ($this->cached !== null) {
			return $this->cached;
		}

		$stored = $this->appConfig->getValueArray(Application::APP_ID, SettingsService::KEY_EXCLUSIONS, []);

		$prefixes = [];
		foreach ($stored as $entry) {
			if (!is_string($entry)) {
				$this->reject();
				continue;
			}

			$normalised = $this->normalise($entry);
			if ($normalised === null) {
				$this->reject();
				continue;
			}

			// Keyed by the value, so a list that holds the same folder twice
			// costs one comparison and not two.
			$prefixes[$normalised] = true;
			if (count($prefixes) >= self::MAX_PREFIXES) {
				break;
			}
		}

		$this->cached = array_keys($prefixes);

		return $this->cached;
	}

	/**
	 * One prefix as it is stored and compared, or null when it is not usable.
	 *
	 * The steps, in order: collapse repeated slashes, drop the leading and
	 * trailing ones, drop a ``files/`` vanguard so that both spellings an admin
	 * might use end in the same value, and refuse the rest.
	 *
	 * A segment ``..`` is REFUSED and not filtered out. Filtering would turn
	 * ``Archiv/../..`` into ``Archiv`` and quietly exclude something the admin
	 * did not name; worse, a filter invites the belief that the value is
	 * sanitised, and the next reader hands it to a file system call. This value
	 * never reaches a file system call at all, it only ever reaches
	 * str_starts_with, and the refusal is what keeps that true by making the
	 * intent visible (T-04-47).
	 */
	public function normalise(string $prefix): ?string {
		$value = trim($prefix);
		if ($value === '' || strlen($value) > self::MAX_PREFIX_LENGTH) {
			return null;
		}

		$value = $this->withoutTheFilesFolder($this->trimmed($value));
		if ($value === '') {
			return null;
		}

		foreach (explode('/', $value) as $segment) {
			if ($segment === '..') {
				return null;
			}
		}

		return $value;
	}

	/**
	 * Judge a whole list without writing anything.
	 *
	 * Separate from save() for the same reason as in SettingsService: the write
	 * route refuses the whole form before it has changed a value, so an invalid
	 * prefix cannot leave the cap moved and the list untouched.
	 *
	 * The answer is a list of codes and not a mapping per entry. The page knows
	 * which row it just added, and a per entry answer would have to name the
	 * entry, which is exactly the value that may not travel back.
	 *
	 * @param list<mixed> $prefixes
	 * @return list<string> error codes, empty when the list fits
	 */
	public function validate(array $prefixes): array {
		$errors = [];
		if (count($prefixes) > self::MAX_PREFIXES) {
			$errors[] = self::ERROR_TOO_MANY;
		}

		$seen = [];
		foreach ($prefixes as $entry) {
			if (!is_string($entry) || trim($entry) === '') {
				$errors[] = self::ERROR_EMPTY;
				continue;
			}
			if (strlen($entry) > self::MAX_PREFIX_LENGTH) {
				$errors[] = self::ERROR_TOO_LONG;
				continue;
			}

			$normalised = $this->normalise($entry);
			if ($normalised === null) {
				// Everything left over at this point failed on a segment or on
				// being nothing but slashes, and both are the same answer to an
				// admin: this is not a folder path.
				$errors[] = self::ERROR_TRAVERSAL;
				continue;
			}

			if (isset($seen[$normalised])) {
				$errors[] = self::ERROR_DUPLICATE;
				continue;
			}
			$seen[$normalised] = true;
		}

		if ($errors !== []) {
			$this->reject();
		}

		return array_values(array_unique($errors));
	}

	/**
	 * Write the whole list, or none of it.
	 *
	 * Validates again rather than trusting the caller, for the reason written at
	 * SettingsService::save(): there is a second way into appconfig that this
	 * method never sees.
	 *
	 * A prefix that is NEW in this call also starts the clearing of D-07: the
	 * index has to mirror the rules, so documents that were indexed under a path
	 * that is excluded from now on leave the index. The new prefixes are worked
	 * out before the write, because the stored list is what "new" is measured
	 * against and this method replaces it.
	 *
	 * A prefix that DISAPPEARS from the list starts nothing, and that is not an
	 * omission. Taking a rule back heals itself: the files are enumerated again,
	 * the container has no etag for a tombstoned row, so the comparison run
	 * queues them, and the unchanged content hash cannot wave them through
	 * because the "unchanged" test demands a row without a deletion mark. It
	 * takes until the next comparison run rather than seconds, which is the
	 * latency AdminViewService::rules() reports to the page instead of leaving
	 * an admin to notice it.
	 *
	 * @param list<mixed> $prefixes
	 * @return list<string> error codes, empty when the list was written
	 */
	public function save(array $prefixes): array {
		$errors = $this->validate($prefixes);
		if ($errors !== []) {
			return $errors;
		}

		$added = $this->newPrefixes($prefixes);

		$clean = [];
		foreach ($prefixes as $entry) {
			$normalised = $this->normalise((string)$entry);
			if ($normalised !== null) {
				$clean[$normalised] = true;
			}
		}

		$this->cached = array_keys($clean);
		$this->appConfig->setValueArray(Application::APP_ID, SettingsService::KEY_EXCLUSIONS, $this->cached);

		$this->scheduleCleanup($added);

		return [];
	}

	/**
	 * The prefixes of a list that are not in force yet, normalised.
	 *
	 * The one place "new" is decided, and both callers need exactly this: the
	 * preview route counts what these prefixes would remove, and save() clears
	 * them. A page that worked "new" out for itself would ask about the value an
	 * admin typed while the comparison happens on the normalised one, so
	 * ``/Archiv/`` next to a stored ``Archiv`` would announce a clearing that
	 * then does not happen.
	 *
	 * A nested pair is reduced to its shortest member: with ``Archiv`` and
	 * ``Archiv/2024`` both new, the second names a subtree of the first, so
	 * counting it would count the same documents twice and clearing it would plan
	 * a second job over ground the first one already walks.
	 *
	 * @param list<mixed> $prefixes
	 * @return list<string>
	 */
	public function newPrefixes(array $prefixes): array {
		$inForce = $this->prefixes();

		$added = [];
		foreach ($prefixes as $entry) {
			if (!is_string($entry)) {
				continue;
			}

			$normalised = $this->normalise($entry);
			if ($normalised === null || in_array($normalised, $inForce, true)) {
				continue;
			}

			$added[$normalised] = true;
		}

		return $this->withoutNested(array_keys($added));
	}

	/**
	 * How many indexed documents these prefixes would take out of the index.
	 *
	 * The number the inline confirmation names, and the reason the confirmation
	 * exists at all: "this also removes 1240 documents from the index" is a
	 * consequence somebody can weigh, and "are you sure" is not (T-04-59).
	 *
	 * Counted through the same enumeration the crawl walks, so it counts the
	 * documents this app would index under that path: the mimetype filter of
	 * getFilesInMount is part of the count, and a folder full of videos therefore
	 * reports nought rather than its file count. It is an upper bound on what
	 * leaves the index rather than a reading of the index itself, because the
	 * exact figure lives in the container and a preview may not depend on the
	 * container answering; a document under the path that was skipped or has not
	 * been reached yet is counted here and has nothing to remove.
	 *
	 * Capped at PREVIEW_CAP, and the ceiling is named in the answer rather than
	 * hidden: the caller compares the result with the constant and the page says
	 * "at least" when it was reached. A gedeckelte number with "at least" in
	 * front of it is more honest than an exact one nobody waits for.
	 *
	 * @param list<string> $newPrefixes as newPrefixes() hands them out
	 */
	public function affectedDocuments(array $newPrefixes): int {
		$total = 0;

		foreach ($this->withoutNested($newPrefixes) as $prefix) {
			foreach ($this->subtreesOfPrefix($prefix) as $subtree) {
				$cursor = 0;
				while ($total < self::PREVIEW_CAP) {
					$seen = 0;
					foreach ($this->storageService->getFilesInMount(
						$subtree['storageId'],
						$subtree['ancestorId'],
						$cursor,
						self::PREVIEW_BAND,
					) as $entry) {
						$cursor = max($cursor, $entry->getId());
						$seen++;
						$total++;
						if ($total >= self::PREVIEW_CAP) {
							break;
						}
					}

					if ($seen < self::PREVIEW_BAND) {
						// Fewer rows than asked for means nothing is left behind
						// the cursor, which is how every band walker of this app
						// ends. The same test after the cap break is harmless:
						// the outer condition ends the loop either way.
						break;
					}
				}
			}
		}

		return $total;
	}

	/**
	 * Plan the clearing of the subtrees these prefixes cover, and count the jobs.
	 *
	 * Not one line of new clearing code, and that is the design rather than a
	 * saving. The whole mechanism exists since phase 3: SubtreeExpandJob walks a
	 * subtree in bands of 250 under a wall clock ceiling, carries its cursor in
	 * its own job argument, plans its own successor and enqueues one row per
	 * descendant with kind delete, and the poller turns such a row into _forget,
	 * which drops the document, forgets the permission rows and leaves a
	 * tombstone, in that order and each of them idempotent. So this method is one
	 * job entry per subtree and nothing else (research pattern 9, way A).
	 *
	 * Way B is the net underneath, and it is worth naming because it is the half
	 * that catches what this method misses: a folder that did not resolve while
	 * the admin was saving, a mount that only appears later, a home that was
	 * created afterwards. Those files drop out of the enumeration the comparison
	 * run reads, the container finds them locally known and absent from the page
	 * and turns them into deletions by itself. It costs no code here and it takes
	 * up to FINDLING_RECONCILE_MIN_INTERVAL_HOURS, which is why way A exists: it
	 * makes the effect visible while the admin is still looking at the page.
	 *
	 * And why there is no fourth writing container route for any of this: the
	 * three writes of a forget are already idempotent and already in the right
	 * order inside the poller, reached through the queue rows this method causes.
	 * A route would be a second way to delete index content, judged by the write
	 * allowlist of the read only gate, which stands at exactly three entries with
	 * a test that says so. The MAX_LIST_LENGTH ceiling of the queue controller
	 * does not apply either, because nothing here crosses the HTTP boundary: this
	 * is PHP writing a job argument into the Nextcloud database.
	 *
	 * A prefix that resolves in no mount is counted and not written out. What
	 * would be written out is a folder name of a private instance, and the log of
	 * this app carries counters and codes (T-04-60).
	 *
	 * @param list<string> $newPrefixes as newPrefixes() hands them out
	 * @return int how many expansion jobs were planned
	 */
	public function scheduleCleanup(array $newPrefixes): int {
		$planned = 0;
		$unresolved = 0;

		foreach ($this->withoutNested($newPrefixes) as $prefix) {
			$subtrees = $this->subtreesOfPrefix($prefix);
			if ($subtrees === []) {
				$unresolved++;
				continue;
			}

			foreach ($subtrees as $subtree) {
				// IJobList::add deduplicates over the whole argument, so saving
				// the same new prefix twice in a row plans one job and not two,
				// and a job already walking this subtree keeps its cursor.
				$this->jobList->add(SubtreeExpandJob::class, [
					'storage_id' => $subtree['storageId'],
					'root_id' => $subtree['rootId'],
					'ancestor_id' => $subtree['ancestorId'],
					'kind' => QueueMapper::KIND_DELETE,
					'last_file_id' => 0,
				]);
				$planned++;
			}
		}

		if ($planned > 0 || $unresolved > 0) {
			$this->logger->info('Findling: planned the clearing of new exclusions', [
				'planned' => $planned,
				'unresolved' => $unresolved,
			]);
		}

		return $planned;
	}

	/**
	 * Every subtree one prefix names, one entry per mount it resolves in.
	 *
	 * The prefix lives in the space of mountRelativePath(), so the path of the
	 * folder is the root of the mount with the prefix behind it, which is the
	 * inverse of that method and stands next to it for that reason. A prefix that
	 * names no folder on a mount yields nothing for that mount, which is the
	 * ordinary case: ``Archiv`` exists in one home and not in the other four.
	 *
	 * @return list<array{storageId:int, rootId:int, ancestorId:int}>
	 */
	private function subtreesOfPrefix(string $prefix): array {
		if ($prefix === '') {
			return [];
		}

		$subtrees = [];
		foreach ($this->storageService->getMounts() as $mount) {
			$storageId = (int)$mount['storage_id'];
			$rootId = (int)$mount['root_id'];
			$overriddenRoot = (int)$mount['overridden_root'];

			$root = $this->storageService->mountRootPath($storageId, $overriddenRoot);
			$folderPath = $root === '' ? $prefix : $root . '/' . $prefix;

			$ancestorId = $this->storageService->folderIdAtPath($storageId, $folderPath);
			if ($ancestorId <= 0) {
				continue;
			}

			$subtrees[] = [
				'storageId' => $storageId,
				'rootId' => $rootId,
				'ancestorId' => $ancestorId,
			];
		}

		return $subtrees;
	}

	/**
	 * One list of prefixes without the entries another entry already covers.
	 *
	 * Shared by the preview and the clearing so that the number and the jobs
	 * describe the same set of files.
	 *
	 * @param list<string> $prefixes
	 * @return list<string>
	 */
	private function withoutNested(array $prefixes): array {
		$kept = [];
		foreach ($prefixes as $prefix) {
			$covered = false;
			foreach ($prefixes as $other) {
				if ($other !== $prefix && str_starts_with($prefix, $other . '/')) {
					$covered = true;
					break;
				}
			}

			if (!$covered) {
				$kept[$prefix] = true;
			}
		}

		return array_keys($kept);
	}

	/**
	 * Does a rule of today leave this file alone?
	 *
	 * THE helper, and the only one. The crawl, the event listener and the claim
	 * of QueueService::describe all call this method with a path built by
	 * mountRelativePath() below, and none of them compares a prefix itself. The
	 * third call site exists because the reconcile of plan 03-12 is a third way
	 * into the queue that never sees a path, so the hand-out of the bytes is the
	 * last point the rules of today can be applied (review finding CR-01).
	 * Call sites with comparisons of their
	 * own are pitfall 4 of the phase research, and the failure mode is quiet: the crawl
	 * leaves the folder alone, every save inside it queues the file again, and
	 * the index fills up slowly with exactly what was supposed to be left out
	 * while nothing on the page says so. The warning has been standing in
	 * StorageService::isIndexedStorage since phase 2, and
	 * backend/tests/test_exclusion_path_space.py reports any second comparison.
	 *
	 * The comparison is str_starts_with against ``<prefix>`` and ``<prefix>/``,
	 * both shapes, so ``Archiv`` matches the folder and everything inside it and
	 * does not match ``Archivar.pdf``. Deliberately no glob and no regular
	 * expression: it is explainable, and there is no way to mis-enter it for the
	 * zero config audience this app is for (D-06).
	 */
	public function isExcluded(string $mountRelativePath): bool {
		$path = $this->trimmed($mountRelativePath);
		if ($path === '') {
			return false;
		}

		foreach ($this->prefixes() as $prefix) {
			if ($path === $prefix || str_starts_with($path, $prefix . '/')) {
				return true;
			}
		}

		return false;
	}

	/**
	 * The one path space of the exclusions, produced here and nowhere else.
	 *
	 * The internal path of a cache entry minus the internal path of the mount
	 * root, minus a ``files`` vanguard, which leaves the path relative to the
	 * files folder of the user. That is the space D-06 names and the space the
	 * page shows.
	 *
	 * Why both subtractions, and why they are one method: the two callers hand in
	 * two different roots. The crawl walks with the overridden root of the mount,
	 * whose internal path is ``files`` because getMounts() asks with
	 * onlyUserFilesMounts, so the first subtraction already lands in the space.
	 * The event listener has the storage root of the mount point, whose internal
	 * path is the empty string, so for it the second subtraction is the one that
	 * does the work. Both end at the same value for the same file, which is the
	 * entire content of pitfall 4: the crawl comparing against
	 * ``files/Archiv/x.pdf`` while the listener compares against
	 * ``/alice/files/Archiv/x.pdf`` is how one prefix hits in one place and
	 * misses in the other.
	 *
	 * A pair that does not fit, a path that is not below the root it was handed,
	 * keeps the path and loses only the vanguard. Guessing at the difference
	 * would be a third space.
	 */
	public function mountRelativePath(string $internalPath, string $rootInternalPath): string {
		$path = $this->trimmed($internalPath);
		$root = $this->trimmed($rootInternalPath);

		if ($root !== '') {
			if ($path === $root) {
				return '';
			}
			if (str_starts_with($path, $root . '/')) {
				$path = substr($path, strlen($root) + 1);
			}
		}

		return $this->withoutTheFilesFolder($path);
	}

	/**
	 * The same space, for a caller that has a storage and an internal path and no
	 * mount root, or null when no mount of this app holds the path.
	 *
	 * The diagnosis is that caller, and this method is the answer to the one
	 * hazard plan 04-08 left open. What the diagnosis has in hand is the display
	 * path of the owner, and for a file in a home that is the exclusion space
	 * exactly, while for a file on a Team Folder mount it is not: the display path
	 * carries the name of the mount point in the home of the user
	 * (``TeamX/x.pdf``) and the crawl compares the same file in the space of its
	 * own mount root (``x.pdf``). Reading the display path as the exclusion space
	 * would therefore be a second path space inside the diagnosis, which is
	 * precisely the failure the gate over the other two call sites exists to
	 * prevent one layer down: one prefix would hit in the diagnosis and miss in
	 * the crawl, or the other way round, and the page would explain a file with a
	 * rule that does not apply to it.
	 *
	 * So the mount is looked up instead of guessed. The internal path out of the
	 * file cache is the same value the crawl reads, the deepest mount root of this
	 * app that the path lies under is the root that mount walks with, and
	 * mountRelativePath() above does the rest. Deepest, not first: several mounts
	 * of one storage are the ordinary case for Team Folders, and the shallower one
	 * would strip too little.
	 *
	 * Null means no mount holds this path, which the caller reads as "no rule of
	 * this kind applies" rather than as "not excluded": the version folder and the
	 * trash bin of a home live on the storage of that home and outside its files
	 * folder, and neither is a place a folder exclusion has anything to say about.
	 *
	 * One mount query per call, and that is affordable here and nowhere else: the
	 * diagnosis is a single file on a human action, while the crawl and the event
	 * listener are per file and per write and therefore get the root handed to
	 * them by their caller.
	 */
	public function mountRelativePathInStorage(int $storageId, string $internalPath): ?string {
		$path = $this->trimmed($internalPath);
		if ($storageId <= 0 || $path === '') {
			return null;
		}

		$deepest = null;
		foreach ($this->storageService->getMounts() as $mount) {
			if ((int)$mount['storage_id'] !== $storageId) {
				continue;
			}

			$root = $this->trimmed($this->storageService->mountRootPath(
				$storageId,
				(int)$mount['overridden_root'],
			));

			if ($root !== '' && $path !== $root && !str_starts_with($path, $root . '/')) {
				continue;
			}

			if ($deepest === null || strlen($root) > strlen($deepest)) {
				$deepest = $root;
			}
		}

		return $deepest === null ? null : $this->mountRelativePath($path, $deepest);
	}

	/**
	 * One path with repeated slashes collapsed and the outer ones gone.
	 *
	 * Backslashes are left exactly as they are. A backslash is a legal character
	 * in a Nextcloud file name, so treating it as a separator would exclude
	 * folders nobody named.
	 */
	private function trimmed(string $path): string {
		$collapsed = preg_replace('#/+#', '/', $path);

		return trim($collapsed ?? $path, '/');
	}

	/**
	 * One path without the ``files`` folder of a home mount in front of it.
	 *
	 * Applies to a stored prefix and to a resolved path alike, which is what
	 * makes ``files/Backups`` and ``Backups`` the same rule. A value that is
	 * nothing but the folder itself becomes the empty string and is refused by
	 * the caller: a prefix that excluded the whole home of every user is not a
	 * folder exclusion, it is switching the app off, and there is no switch for
	 * that on this page.
	 */
	private function withoutTheFilesFolder(string $path): string {
		if ($path === self::HOME_FILES_FOLDER) {
			return '';
		}

		$vanguard = self::HOME_FILES_FOLDER . '/';

		return str_starts_with($path, $vanguard) ? substr($path, strlen($vanguard)) : $path;
	}

	/**
	 * A refused entry, counted and never written out.
	 *
	 * The same rule as FileStateService::reject() and SettingsService::reject():
	 * what arrives here is a folder name of a private instance, and the log of
	 * this app carries counters and codes and nothing somebody else wrote.
	 */
	private function reject(): void {
		$this->rejected++;
		$this->logger->warning(
			'Findling: refused an exclusion entry that is not a usable folder path',
			['rejected' => $this->rejected],
		);
	}
}
