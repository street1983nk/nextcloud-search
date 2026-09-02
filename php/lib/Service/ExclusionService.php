<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\AppInfo\Application;
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
 * Where the prefixes apply, in full: only in user homes, and relative to the
 * ``files`` folder of the user, so ``Archiv``, ``Backups``, ``.stversions``. They
 * apply in every home at once. Team Folders and external storage are steered by
 * their own all or nothing switch in SettingsService and carry no prefixes,
 * because a prefix that meant one thing in a home and another thing in a Team
 * Folder would be a second path space, and a second path space is the failure
 * this class exists to prevent.
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
	 * @param list<mixed> $prefixes
	 * @return list<string> error codes, empty when the list was written
	 */
	public function save(array $prefixes): array {
		$errors = $this->validate($prefixes);
		if ($errors !== []) {
			return $errors;
		}

		$clean = [];
		foreach ($prefixes as $entry) {
			$normalised = $this->normalise((string)$entry);
			if ($normalised !== null) {
				$clean[$normalised] = true;
			}
		}

		$this->cached = array_keys($clean);
		$this->appConfig->setValueArray(Application::APP_ID, SettingsService::KEY_EXCLUSIONS, $this->cached);

		return [];
	}

	/**
	 * Does a rule of today leave this file alone?
	 *
	 * THE helper, and the only one. The crawl and the event listener both call
	 * this method with a path built by mountRelativePath() below, and neither of
	 * them compares a prefix itself. Two call sites with two comparisons is
	 * pitfall 4 of the phase research, and the failure mode is quiet: the crawl
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
