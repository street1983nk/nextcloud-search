<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\Files\Cache\ICacheEntry;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\IMimeTypeLoader;
use Psr\Log\LoggerInterface;

/**
 * The only place in this app that enumerates mounts and files.
 *
 * Both enumerations go through IFileAccess and nothing else. There is no
 * hand written query against the file cache in here, and there is no second
 * code path for older servers either. Both methods used below are available
 * since 32.0.0, the app declares min-version 32, so the compatibility branch
 * that the model implementation carries would be roughly a hundred and fifty
 * lines of SQL that has to be kept working across SQLite, MariaDB and
 * PostgreSQL for the benefit of exactly nobody. Not writing it is the whole
 * point of the version floor.
 *
 * The two hard boundaries of the index are decided here and nowhere else:
 * which mounts are looked at, and which document types are considered. The
 * document types are a constant, because zero config means the default has to
 * be right rather than adjustable. Which mounts are looked at was a constant
 * until plan 04-08 and is now the default of two switches (ADM-04, D-08): the
 * three provider lists below are the documented default and providers()
 * composes the list in force out of them.
 */
class StorageService {
	/**
	 * The mounts that are always walked: user homes in both flavours.
	 *
	 * There is no switch for these and there is not going to be one. A search
	 * that does not read the home directories of the users is not a search, so
	 * an option for it would be an option for switching the app off, and the way
	 * to switch an app off is to disable it.
	 *
	 * @var list<string>
	 */
	private const HOME_MOUNT_PROVIDERS = [
		'OC\Files\Mount\LocalHomeMountProvider',   // user home, file backend
		'OC\Files\Mount\ObjectHomeMountProvider',  // user home, object storage backend
	];

	/**
	 * Team Folders, on by default.
	 *
	 * They are called that since NC 31, but the app id and the mount provider
	 * class are unchanged. Whether the app is installed does not need to be
	 * checked: if it is not, there are no mounts of that class.
	 *
	 * On by default because a Team Folder lives on local storage like a home
	 * does and is where the documents of a small organisation actually are.
	 * Leaving it out by default would make the search miss the half of the
	 * instance people search for most.
	 */
	private const TEAM_FOLDER_MOUNT_PROVIDER = 'OCA\GroupFolders\Mount\MountProvider';

	/**
	 * External storage, off by default, and live code since plan 04-08.
	 *
	 * This line stood commented out from phase 2 with the note that it becomes a
	 * switch in phase 4 (ADM-04), which is what happened: it is a constant now
	 * and SettingsService::indexExternalStorage() decides whether providers()
	 * puts it into the list.
	 *
	 * Off by default, and the reason is unchanged from phase 2: a remote drive
	 * blows up every assumption the first index makes about how long reading a
	 * file takes and how much of it there is, and an admin who mounted a multi
	 * terabyte share does not expect installing an app to start pulling it
	 * through HTTP. Switching it on is an explicit decision with the consequence
	 * written next to the switch (T-04-52).
	 */
	private const EXTERNAL_STORAGE_MOUNT_PROVIDER = 'OCA\Files_External\Config\ConfigAdapter';

	/**
	 * The document allowlist of the zero config guard rails: PDF, the OOXML
	 * trio, OpenDocument, plain text and Markdown, RTF and HTML, and since
	 * plan 03-10 the four picture formats that OCR can read.
	 *
	 * Everything else, and that includes video, audio and archives, is not a
	 * document and is never queued. Two spellings are listed for RTF because
	 * instances disagree on which one they store, and an entry this instance
	 * has never seen simply drops out below.
	 *
	 * The pictures, and why exactly these four: JPEG is what a phone upload is,
	 * PNG is what a screenshot and most exported notices are, TIFF is what a
	 * scanner and a fax gateway write, and WebP is what a browser saves today.
	 * All four are read by the Pillow and the leptonica of the container image,
	 * measured, with the WebP result written up as measurement 4 of
	 * docs/ocr.md.
	 *
	 * HEIC, BMP and GIF stay out. HEIC needs a further decoder inside the
	 * sandbox child, and every decoder is attack surface that a picture from a
	 * stranger's phone gets to reach; BMP and GIF carry documents essentially
	 * never, so the same surface would be bought for nothing at all.
	 *
	 * This list is kept twice on purpose, here and in the container's
	 * dispatch.ALLOWED_MIMETYPES, because each side has to hold on the day the
	 * other one is changed alone. Since plan 03-10 a gate compares the two in
	 * both directions: backend/tests/test_allowlist_parity.py reads this
	 * constant out of this file, so the identical paragraph above stands next
	 * to the Python list as well.
	 *
	 * @var list<string>
	 */
	public const ALLOWED_MIMETYPES = [
		'application/pdf',
		'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
		'application/vnd.openxmlformats-officedocument.presentationml.presentation',
		'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		'application/vnd.oasis.opendocument.text',
		'application/vnd.oasis.opendocument.spreadsheet',
		'application/vnd.oasis.opendocument.presentation',
		'text/plain',
		'text/markdown',
		'text/csv',
		'text/html',
		'application/xhtml+xml',
		'application/rtf',
		'text/rtf',
		'image/jpeg',
		'image/png',
		'image/tiff',
		'image/webp',
	];

	/**
	 * Resolved once per process. The translation is three queries at most and
	 * the crawl asks for it on every batch.
	 *
	 * @var list<int>|null
	 */
	private ?array $mimeIds = null;

	/**
	 * The storage ids of the mount list in force, resolved once per request and
	 * kept as a lookup rather than a list. The event listener asks this question
	 * for every single write on the instance, and getMounts() is a query plus one
	 * more per home mount.
	 *
	 * @var array<int, true>|null
	 */
	private ?array $indexedStorages = null;

	/**
	 * The internal path of a mount root, per storage and root, for the request.
	 *
	 * One cache query each, and the event listener would otherwise ask for the
	 * same root on every write of the same request. The same lifetime as the
	 * lookup above and never longer.
	 *
	 * @var array<string, string>
	 */
	private array $rootPaths = [];

	public function __construct(
		private IFileAccess $fileAccess,
		private IMimeTypeLoader $mimeTypeLoader,
		private SettingsService $settingsService,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * The mount providers in force: the homes plus whatever the two switches say.
	 *
	 * The one place the list is composed, which is what keeps getMounts(),
	 * isIndexedStorage() and the mounts route of the reconcile giving the same
	 * answer. A second composition anywhere would be a second answer to "which
	 * mounts are in", and the two would disagree the day one of the switches is
	 * flipped: events would keep indexing what the crawl was told to leave
	 * alone. backend/tests/test_exclusion_path_space.py reports any second call
	 * of the mount query and any argument that is not this method.
	 *
	 * Read fresh on every call and deliberately not cached on a field.
	 * IAppConfig caches per request already, so this is a lookup and not a
	 * query, and a longer lived cache would break the one promise of D-08: the
	 * next run applies the new rules, with nothing restarted.
	 *
	 * @return list<string>
	 */
	private function providers(): array {
		$providers = self::HOME_MOUNT_PROVIDERS;

		if ($this->settingsService->indexTeamFolders()) {
			$providers[] = self::TEAM_FOLDER_MOUNT_PROVIDER;
		}

		if ($this->settingsService->indexExternalStorage()) {
			$providers[] = self::EXTERNAL_STORAGE_MOUNT_PROVIDER;
		}

		return $providers;
	}

	/**
	 * Every mount the crawl is allowed to walk, once per mount and not once
	 * per user. A file that ten users see lives on one mount and is therefore
	 * enumerated exactly once, which is the entire content of IDX-01.
	 *
	 * onlyUserFilesMounts rewrites the root of a home mount to the files
	 * folder, so files_trashbin and files_versions never show up in the first
	 * place. That is a deletion of an entire class of wrong index entries, not
	 * an optimisation.
	 *
	 * @return iterable<array{storage_id: int, root_id: int, overridden_root: int}>
	 */
	public function getMounts(): iterable {
		return $this->fileAccess->getDistinctMounts($this->providers(), true);
	}

	/**
	 * The internal path of one mount root, or the empty string.
	 *
	 * The raw material of the one exclusion path space, and it exists here
	 * because this class is the only one in the app that reaches into the file
	 * cache. Both callers of ExclusionService::mountRelativePath ask this
	 * method for the root, so neither of them has to know how a root becomes a
	 * path.
	 *
	 * The two callers hand in two different roots, and both are correct. The
	 * crawl passes the overridden root of the mount, the files folder, because
	 * that is the node its query walks; the answer is ``files``. The event
	 * listener passes the storage root of the mount point, because that is what
	 * IMountPoint offers; the answer is the empty string. mountRelativePath()
	 * lands both of them in the same space, which is the entire content of
	 * pitfall 4.
	 *
	 * An unresolvable root is the empty string and not an exception. It is the
	 * fail open direction on purpose: without a root the path keeps its
	 * ``files`` vanguard, which the one path space method strips anyway, so a
	 * root that could not be read costs no correctness. Throwing here would turn
	 * a missing cache row into a failed upload.
	 */
	public function mountRootPath(int $storageId, int $rootId): string {
		if ($storageId <= 0 || $rootId <= 0) {
			return '';
		}

		$key = $storageId . ':' . $rootId;
		if (isset($this->rootPaths[$key])) {
			return $this->rootPaths[$key];
		}

		$entry = $this->fileAccess->getByFileIdInStorage($rootId, $storageId);
		$this->rootPaths[$key] = $entry === null ? '' : $entry->getPath();

		return $this->rootPaths[$key];
	}

	/**
	 * Does this app index the mount a file lives on?
	 *
	 * Asked by the event listener before it queues anything, and asked against
	 * getMounts(), which is the same source the crawl walks. A second list of
	 * providers here would be a second answer to "which mounts are in", and the
	 * two would disagree the day external storage becomes a switch (ADM-04):
	 * events would keep indexing what the crawl was told to leave alone.
	 *
	 * That day is plan 04-08, and this warning is the reason nothing had to be
	 * changed in this method for it. Both switches are composed in providers(),
	 * getMounts() reads that one list and this method reads getMounts(), so
	 * flipping a switch moves the crawl and the events together. The warning
	 * stays because it is what has to keep being true, not because it was a
	 * prediction that has now expired.
	 *
	 * What this cannot answer is where inside a storage a file sits. The
	 * trashbin and the version folder of a home live on the same storage as the
	 * files folder, so a write there passes this check. Those rows resolve to
	 * nothing in QueueService::describe, which acknowledges them as
	 * skipped(gone); keeping the check cheap is worth that handful of rows,
	 * because the alternative is an ancestor query on every write of the
	 * instance.
	 */
	public function isIndexedStorage(int $storageId): bool {
		if ($this->indexedStorages === null) {
			$storages = [];
			foreach ($this->getMounts() as $mount) {
				$storages[(int)$mount['storage_id']] = true;
			}

			$this->indexedStorages = $storages;
		}

		return isset($this->indexedStorages[$storageId]);
	}

	/**
	 * One slice of one mount, ordered by file id and starting behind the
	 * cursor.
	 *
	 * The type filter travels into the query. Filtering after the transfer
	 * would mean reading every video and every zip archive of the instance out
	 * of the database in order to throw it away again.
	 *
	 * The two booleans at the end: do not take end to end encrypted files,
	 * because all that could be read from them is ciphertext, and do take
	 * server side encrypted ones, because the content gateway hands those over
	 * decrypted.
	 *
	 * There is no size filter in this API. The cap lives in the crawl job,
	 * which sees the size in the cache entry and records the decision instead
	 * of hiding it.
	 *
	 * There is no exclusion filter either, and that is a decision of plan 04-08
	 * with three reasons, each of which is on its own enough (deviation, see
	 * 04-08-SUMMARY.md). First, every caller of this method reads "nothing behind
	 * the cursor" from an empty result: StorageCrawlJob ends the mount when it
	 * saw nothing, and SubtreeExpandJob does the same. One excluded folder
	 * holding a full batch would therefore stop the crawl in the middle of the id
	 * range, for good. Second, the crawl has to SEE an excluded file in order to
	 * count it: the ``Excluded`` tile of the page is the promise that nothing
	 * disappears quietly (IDX-06), and a filter here would keep that number at
	 * nought forever. Third, SubtreeExpandJob walks the subtree of a newly
	 * excluded folder in order to clear it from the index (plan 04-09, research
	 * pattern 9), and it walks it through this very method, so a filter here
	 * would make that clearing a no-op against exactly the folder it is for.
	 *
	 * The exclusion is therefore applied by the callers, through the one helper
	 * ExclusionService::isExcluded on the one path space, and
	 * backend/tests/test_exclusion_path_space.py holds that both of them do it.
	 *
	 * @return iterable<ICacheEntry>
	 */
	public function getFilesInMount(int $storageId, int $overriddenRoot, int $lastFileId, int $batchSize): iterable {
		return $this->fileAccess->getByAncestorInStorage(
			$storageId,
			$overriddenRoot,
			$lastFileId,
			$batchSize,
			$this->getAllowedMimeIds(),
			false,
			true,
		);
	}

	/**
	 * One page of the same slice, reduced to the five fields the reconcile
	 * compares against (IDX-04).
	 *
	 * Deliberately built on getFilesInMount and not on a query of its own.
	 * Reconcile and crawl have to see the same files, including the same
	 * mimetype filter and the same two encryption booleans: a second query here
	 * would be a second answer to "what is in this mount", and the reconcile
	 * would spend every night repairing the difference between the two.
	 *
	 * Only the projection is new, because the crawl needs the cache entry and the
	 * reconcile needs five values it can put into a JSON answer. No path, no
	 * name, no owner: the comparison in the container works on file id and etag,
	 * and everything beyond that would be content of a private instance crossing
	 * the boundary for no reason.
	 *
	 * The exclusion is not filtered out here either, and this one is worth a
	 * sentence of its own because it looks harmless. ReconcileController works
	 * out its final mark as "fewer rows than asked for", and a final page lets
	 * the deletion rule of the reconcile drop its upper bound. So a page that
	 * lost three rows to a prefix would be declared final, and every file the
	 * container knows above the cursor would be reported as deleted: an exclusion
	 * on one folder would empty the index of a whole mount. Clearing what a new
	 * prefix leaves behind is done deliberately and in bands instead, through
	 * SubtreeExpandJob with kind delete (plan 04-09, research pattern 9).
	 *
	 * @return list<array{fileId: int, etag: string, size: int, mtime: int, mime: string}>
	 */
	public function getFileSlice(int $storageId, int $overriddenRoot, int $lastFileId, int $batchSize): array {
		$rows = [];
		foreach ($this->getFilesInMount($storageId, $overriddenRoot, $lastFileId, $batchSize) as $entry) {
			$rows[] = [
				'fileId' => $entry->getId(),
				'etag' => $entry->getEtag(),
				// int on every ordinary file; the interface allows a float for
				// sizes beyond the integer range, and a document of that size
				// does not exist in an index capped at fifty megabytes.
				'size' => (int)$entry->getSize(),
				'mtime' => $entry->getMTime(),
				'mime' => $entry->getMimeType(),
			];
		}

		return $rows;
	}

	/**
	 * The allowlist as the numeric ids the file cache stores.
	 *
	 * Unknown types are skipped rather than thrown over: IMimeTypeLoader::getId
	 * creates the row when it is missing, so asking for a type this instance
	 * has never seen would write into the mimetype table as a side effect of a
	 * read. And a type no file here has cannot narrow the query anyway.
	 *
	 * @return list<int>
	 */
	public function getAllowedMimeIds(): array {
		if ($this->mimeIds !== null) {
			return $this->mimeIds;
		}

		$ids = [];
		$unknown = 0;
		foreach (self::ALLOWED_MIMETYPES as $mimeType) {
			if (!$this->mimeTypeLoader->exists($mimeType)) {
				$unknown++;
				continue;
			}

			$ids[] = $this->mimeTypeLoader->getId($mimeType);
		}

		if ($unknown > 0) {
			$this->logger->debug('Findling: document types this instance has never stored', ['count' => $unknown]);
		}

		$this->mimeIds = array_values(array_unique($ids));

		return $this->mimeIds;
	}
}
