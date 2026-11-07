<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\Files\Cache\IFileAccess;

/**
 * The document key of a file: one value per document of a storage group, no
 * matter who reads it and where it is mounted (plan 43-15, D-43-14).
 *
 * Why a key of its own. The container counted documents by the path a job
 * carries, and that path is relative to the home folder of the READER
 * (QueueService::describe, the field path). Two readers of the same file under
 * two mount points, or a reader who sees a folder of a SMB mount through a
 * Nextcloud share because they sort before its owner, produced two paths for
 * one document, and the coverage counted it twice (research A1). The internal
 * path out of oc_filecache.path is relative to the root of the storage, and the
 * members of one storage group (StorageService::countingKey) share host, share
 * and root, so it is the same for every member and every reader.
 *
 * Why the key is read from the file cache and never from a node. The node a job
 * is built from is the node of the reader, and for a reader behind a share its
 * internal path is relative to the shared folder (SharedMount, see readerOf in
 * QueueService and the lookup in SearchService). Taking it from there would
 * reintroduce exactly the reader dependence this key removes. docKeysFor is the
 * one source for both the jobs and the backfill route, so the two can never
 * disagree.
 *
 * Why a hash. A fixed length of 64 hex characters for a column and an index in
 * the container, and no path in the key the container stores or in anything it
 * logs (T-36-17). The normalisation is deliberately small: composed Unicode
 * (NFC) and no leading slash, nothing else. No lower casing, because two names
 * that differ in case are two files on most backends. And the prefix files/ is
 * NOT cut (W2): home storages are never grouped, so cutting it gains nothing,
 * while an external storage whose own tree starts with a folder called files
 * would then share keys with the same path without that folder.
 *
 * backend/tests/fixtures/doc_key_cases.json holds the cases with keys computed
 * by hand; DocKeyServiceTest and the verify of the plan hold this class to it.
 */
class DocKeyService {
	/**
	 * File ids per file cache lookup. The same band as the route of the
	 * container (ReconcileController::DOC_KEY_BAND) and as the storage lookups
	 * of StorageService; it exists for the bound parameters of the dialects,
	 * a claim of a few hundred rows takes two or three lookups.
	 */
	private const LOOKUP_BAND = 200;

	/**
	 * The two trash trees the crawl never enters, the same pair
	 * FileStateService::countByReason leaves out. A file in a trash bin still
	 * has a cache entry, but it is no document of the index any more.
	 *
	 * @var list<string>
	 */
	private const TRASH_PREFIXES = ['files_trashbin/', '__groupfolders/trash/'];

	public function __construct(
		private IFileAccess $fileAccess,
	) {
	}

	/**
	 * The key of one internal path: sha256 hex over the path in form C without
	 * a leading slash.
	 *
	 * Static, because it is string arithmetic and a test can ask it without a
	 * file cache. A value that cannot be composed (no intl and no polyfill, or
	 * not valid UTF-8) is hashed as it came; Nextcloud writes the file cache in
	 * form C itself, so that fallback only matters for a path that is broken
	 * anyway, and it still yields one stable key for it.
	 */
	public static function docKeyOf(string $filecachePath): string {
		$path = ltrim($filecachePath, '/');
		if (class_exists(\Normalizer::class)) {
			$composed = \Normalizer::normalize($path, \Normalizer::FORM_C);
			if (is_string($composed)) {
				$path = $composed;
			}
		}

		return hash('sha256', $path);
	}

	/**
	 * The keys of these files out of the file cache, and the ids that have none.
	 *
	 * Every asked id that is a positive integer ends in exactly one of the two
	 * lists (W8): keys when the file cache holds a row outside the trash, absent
	 * when it holds no row or the row lies in a trash bin. Ids that are not
	 * positive are not asked and appear in neither list; the route refuses
	 * them before they get here.
	 *
	 * Banded internally to LOOKUP_BAND ids, so a claim may hand in any number
	 * of ids. Nothing is logged here, and the paths never leave this method:
	 * the answer holds ids and hex values only.
	 *
	 * @param list<int> $fileIds
	 * @return array{keys: array<int, string>, absent: list<int>}
	 */
	public function docKeysFor(array $fileIds): array {
		$wanted = [];
		foreach ($fileIds as $fileId) {
			if (is_int($fileId) && $fileId > 0) {
				$wanted[$fileId] = true;
			}
		}
		$wanted = array_keys($wanted);

		$keys = [];
		$absent = [];
		foreach (array_chunk($wanted, self::LOOKUP_BAND) as $band) {
			$entries = $this->fileAccess->getByFileIds($band);
			foreach ($band as $fileId) {
				$entry = $entries[$fileId] ?? null;
				$path = $entry?->getPath();
				if (!is_string($path) || self::inTrash($path)) {
					$absent[] = $fileId;
					continue;
				}

				$keys[$fileId] = self::docKeyOf($path);
			}
		}

		return ['keys' => $keys, 'absent' => $absent];
	}

	private static function inTrash(string $path): bool {
		$path = ltrim($path, '/');
		foreach (self::TRASH_PREFIXES as $prefix) {
			if (str_starts_with($path, $prefix)) {
				return true;
			}
		}

		return false;
	}
}
