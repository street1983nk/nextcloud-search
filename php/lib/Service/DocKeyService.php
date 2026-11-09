<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\Files\Cache\IFileAccess;

/**
 * The document key of a file: one value per document of a share, no matter
 * who reads it, where it is mounted and under which root or spelling of the
 * share its storage was configured (D-43-14, D-43-15, D-43-17).
 *
 * Why a key of its own. The container counted documents by the path a job
 * carries, and that path is relative to the home folder of the READER
 * (QueueService::describe, the field path). Two readers of the same file under
 * two mount points, or a reader who sees a folder of a SMB mount through a
 * Nextcloud share because they sort before its owner, produced two paths for
 * one document, and the coverage counted it twice (research A1).
 *
 * Why the share path and not the internal path alone. oc_filecache.path is
 * relative to the root of the storage. Two storages of one share with the
 * roots / and /Projekte name the same file Projekte/a.doc and a.doc, which
 * were two keys. The key is therefore taken over the share identity of the
 * storage (StorageService::shareIdentities): the share, and the root joined in
 * front of the internal path. A storage without identity (a home, a team
 * folder, any backend that is never grouped) keeps its internal path with an
 * empty share.
 *
 * Why the share is part of the hash. Even a wrong grouping can then never
 * merge files of two shares, and a key without identity never meets one with
 * identity (empty share against a share that never is empty). NUL sets the
 * parts apart, because no share and no path holds it, so no part can slide
 * into the next one.
 *
 * Why root and path are never folded. Bericht.txt and bericht.txt are two files
 * on a Linux server and two rows in Nextcloud (OE-1 a); folding them would merge
 * two documents. Only host and share name are folded, inside the identity.
 *
 * Why NFC. Nextcloud writes the file cache in NFC (lib/private/Files/Cache/
 * Cache.php normalize, stable34 :1253-1255), so NFC and NFD twins are one row
 * there already; the root out of an id or a configuration is not normalised by
 * Nextcloud, which is why the share path is composed here as a whole. The
 * prefix files/ is NOT cut (W2): home storages are never grouped, and an
 * external storage whose tree starts with a folder called files must stay
 * apart from the same path without it.
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
 * the container, and no path, share or root in the key the container stores or
 * in anything it logs (T-36-17, T-43-65).
 *
 * backend/tests/fixtures/doc_key_cases.json holds the cases with keys computed
 * by hand; DocKeyServiceTest and backend/tests/test_share_identity_cases.py
 * hold this class to it.
 */
class DocKeyService {
	/**
	 * The format of the keys this class derives, handed out next to every key
	 * (the field docKeyFormat of a job, format in the answer of the backfill
	 * route). Format 2 is the key over the share path; the keys of format 1
	 * (1.6.3-rc.1, the internal path alone) are not comparable with it, and the
	 * container builds all of them anew once it takes format 2 (plan 43-24,
	 * OE-5 a). A container that does not know a format must not count with it.
	 */
	public const DOC_KEY_FORMAT = 2;

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
		private StorageService $storageService,
	) {
	}

	/**
	 * The key of one internal path on a storage with this share identity:
	 * sha256 hex over '2' NUL share NUL share path.
	 *
	 * The share path is the internal path without leading slashes, behind the
	 * root and a slash; an empty root gives the path alone, an empty path the
	 * root alone. Without identity the share is empty and the share path is the
	 * internal path. The share path is composed to NFC.
	 *
	 * Static, because it is string arithmetic and a test can ask it without a
	 * file cache. A value that cannot be composed (no intl and no polyfill, or
	 * not valid UTF-8) is hashed as it came; Nextcloud writes the file cache in
	 * form C itself, so that fallback only matters for a path that is broken
	 * anyway, and it still yields one stable key for it.
	 *
	 * @param array{share: string, root: string}|null $identity
	 */
	public static function docKeyOf(string $filecachePath, ?array $identity = null): string {
		$path = ltrim($filecachePath, '/');
		$share = '';
		if ($identity !== null) {
			$share = $identity['share'];
			$root = $identity['root'];
			if ($root !== '') {
				$path = $path === '' ? $root : $root . '/' . $path;
			}
		}

		if (class_exists(\Normalizer::class)) {
			$composed = \Normalizer::normalize($path, \Normalizer::FORM_C);
			if (is_string($composed)) {
				$path = $composed;
			}
		}

		return hash('sha256', self::DOC_KEY_FORMAT . "\0" . $share . "\0" . $path);
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
	 * of ids. Per band the share identities of its storages are asked once,
	 * from the same source as the grouping of the coverage. A failing lookup
	 * fails the whole answer rather than handing out a key without the share of
	 * its storage; the claim then travels without keys and the route answers
	 * with an error. Nothing is logged here, and paths and identities never
	 * leave this method: the answer holds ids and hex values only.
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

			$found = [];
			$storages = [];
			foreach ($band as $fileId) {
				$entry = $entries[$fileId] ?? null;
				$path = $entry?->getPath();
				if ($entry === null || !is_string($path) || self::inTrash($path)) {
					$absent[] = $fileId;
					continue;
				}

				$storageId = (int)$entry->getStorageId();
				$found[$fileId] = [$path, $storageId];
				$storages[$storageId] = true;
			}

			if ($found === []) {
				continue;
			}

			$identities = $this->storageService->shareIdentities(array_keys($storages));
			foreach ($found as $fileId => [$path, $storageId]) {
				$keys[$fileId] = self::docKeyOf($path, $identities[$storageId] ?? null);
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
