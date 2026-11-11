<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\Files\Cache\ICacheEntry;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\FileInfo;
use OCP\Files\IMimeTypeLoader;
use OCP\IDBConnection;
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
 *
 * One question is answered with two queries of their own, and neither of them
 * touches the file cache: classifyAbsent() reads oc_storages and oc_mounts to
 * tell the container which of its storages are deleted and which are only
 * switched off (plan 36-03, D-36-14). The reason it cannot go through the mount
 * list stands at the method. Since plan 43-21 shareIdentities() reads
 * oc_storages as well and, for ids Nextcloud stored as their md5 only,
 * oc_mounts, oc_external_mounts and five keys of oc_external_config, read
 * only, to tell which storages show one share; that answer feeds the coverage
 * figure and nothing else.
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
	 * trio, OpenDocument, plain text and Markdown, RTF and HTML, since plan
	 * 03-10 the picture formats that OCR can read, and since plan 31-10 mails,
	 * ZIP files, Word and Excel 97 to 2003 and HEIC photos.
	 *
	 * Everything else, and that includes video, audio and every archive format
	 * but ZIP, is not a document and is never queued. Two spellings are listed
	 * for RTF because instances disagree on which one they store, and an entry
	 * this instance has never seen simply drops out below.
	 *
	 * The pictures, and why exactly these four: JPEG is what a phone upload is,
	 * PNG is what a screenshot and most exported notices are, TIFF is what a
	 * scanner and a fax gateway write, and WebP is what a browser saves today.
	 * All four are read by the Pillow and the leptonica of the container image,
	 * measured, with the WebP result written up as measurement 4 of
	 * docs/ocr.md.
	 *
	 * Since 1.5 (plan 31-10) the allowlist reads five more kinds of file. A
	 * mail (message/rfc822) gives its subject, its senders and recipients, its
	 * text part and the names of its attachments, never their content. A ZIP
	 * file (application/zip) gives the text of its members, without OCR inside
	 * the archive and inside limits that are counted before the archive is
	 * opened. Word and Excel 97 to 2003 (application/msword,
	 * application/vnd.ms-excel) are read by olefile and xlrd in the sandbox
	 * child, without a headless office suite. HEIC and HEIF photos
	 * (image/heic, image/heif) are decoded by pillow-heif in the same child
	 * and go to OCR like the other pictures. What stays outside, and why: BMP
	 * and GIF carry documents essentially never, so a further decoder that a
	 * picture from a stranger's phone gets to reach would be bought for
	 * nothing; the PowerPoint format before 2007 has no reader; further
	 * archive formats (7z, rar, tar, gz) and Outlook .msg files would each be
	 * a parser of its own that no decision opened. This paragraph stands
	 * identically next to both lists, and
	 * backend/tests/test_allowlist_parity.py compares the two.
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
		'image/heic',
		'image/heif',
		'message/rfc822',
		'application/zip',
		'application/msword',
		'application/vnd.ms-excel',
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

	/**
	 * Storage ids per IN query of classifyAbsent().
	 *
	 * The band exists for the dialects and not for the size of the answer, the
	 * same reasoning as FileStateService::verdictsFor: every database has a
	 * ceiling on bound parameters and they differ. The route in front of this
	 * method takes at most 256 ids, so a request is two bands at most.
	 */
	private const ABSENT_LOOKUP_BAND = 200;

	/**
	 * The share part of a document key for a storage whose id is an md5 and
	 * has no share identity, in front of its storage number (see
	 * docKeyIdentities()). No share identity starts like this: they start
	 * with 'smb::' or 'sftp::'.
	 */
	public const HASHED_WITHOUT_IDENTITY = '#';

	/**
	 * The backends whose storage id is known to read '<user>@<host>//<rest>'.
	 *
	 * Read in nextcloud/server, branch stable34 (head 4ce36f88, 28.10.2026):
	 * - SMB, apps/files_external/lib/Lib/Storage/SMB.php:137-142, getId() is
	 *   'smb::' . <auth user> . '@' . <host> . '//' . <share> . '/' . <root>,
	 *   and lines 114-116 give the root a leading and a trailing slash.
	 * - SFTP, apps/files_external/lib/Lib/Storage/SFTP.php:157-167, getId() is
	 *   'sftp::' . <user> . '@' . <host>[':' . <port>] . '/' . <root>, and lines
	 *   94-98 give the root a leading slash, so the host is followed by '//'.
	 *
	 * WebDAV and ownCloud are not in the list: their getId() (lib/private/Files/
	 * Storage/DAV.php:201-203) puts a host that may carry a path in front of a
	 * single slash, so host and root cannot be told apart in the id. A backend
	 * that is not in the list is never grouped, which is the counting of 1.5.
	 */
	private const COUNTING_KEY_BACKENDS = ['smb::', 'sftp::'];

	/**
	 * The files_external backends whose hashed ids shareIdentities() rebuilds,
	 * by their identifiers in oc_external_mounts.storage_backend
	 * (apps/files_external/lib/Lib/Backend/SMB.php :30, SFTP.php :20).
	 *
	 * @var list<string>
	 */
	private const REBUILT_BACKENDS = ['smb', 'sftp'];

	/**
	 * The only keys of oc_external_config that are ever read (exception A-3 of
	 * plan 43-21). The password is not among them and is never asked for; it
	 * is the only value files_external encrypts (DBConfigService setConfig),
	 * and the identity does not need it.
	 *
	 * @var list<string>
	 */
	private const REBUILT_CONFIG_KEYS = ['host', 'share', 'root', 'user', 'port'];

	/**
	 * The counters of the last shareIdentities() call, numbers only. Not a
	 * cache: the identities themselves are never kept over a call.
	 *
	 * @var array{parsed: int, hashedVerified: int, hashedUngrouped: int, placeholder: int, excluded: int}
	 */
	private array $identityStats = ['parsed' => 0, 'hashedVerified' => 0, 'hashedUngrouped' => 0, 'placeholder' => 0, 'excluded' => 0];

	public function __construct(
		private IFileAccess $fileAccess,
		private IMimeTypeLoader $mimeTypeLoader,
		private SettingsService $settingsService,
		private IDBConnection $db,
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
	 * The folder at one internal path of one storage, as a file id, or nought.
	 *
	 * The counterpart of mountRootPath(): that one turns a root into a path, this
	 * one turns a path back into a node, and both live here because this class is
	 * the only one in the app that reaches into the file cache. The clearing of a
	 * new exclusion needs it: a prefix is a path and the expansion job needs an
	 * ancestor file id, and this is the one step between the two.
	 *
	 * Nought for anything that is not a folder, and that is the guard rather than
	 * a detail. The id travels into a job argument that expands a whole subtree
	 * as deletions, so handing that job a file instead of a folder would plan a
	 * subtree walk over a node that has no descendants, and handing it a nought
	 * is what the job itself refuses with a warning. A path that does not exist
	 * on this storage is nought as well: a prefix an admin typed for a folder
	 * that only exists in some other home is not an error, it is a prefix that
	 * has nothing to clear here.
	 *
	 * One query per call and no cache. Both callers ask once per prefix and mount
	 * while an admin waits for a form to save, which is a handful of queries on a
	 * human action, and a cache would only hold values that a rename invalidates.
	 */
	public function folderIdAtPath(int $storageId, string $internalPath): int {
		if ($storageId <= 0 || $internalPath === '') {
			return 0;
		}

		$entry = $this->fileAccess->getByPathInStorage($internalPath, $storageId);
		if ($entry === null || $entry->getMimeType() !== FileInfo::MIMETYPE_FOLDER) {
			return 0;
		}

		return max(0, $entry->getId());
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
	 * Which of the asked storages are deleted, and which are only switched off.
	 *
	 * The container asks this for storages it still holds rows of and no longer
	 * finds in the mount list (plan 36-03, M-32-02). Three classes come out of it
	 * there, and this method answers the two that allow a deletion in the same
	 * reconcile round:
	 *
	 * - gone: the storage has no row in oc_storages any more. The user or the
	 *   external storage was deleted, and nothing will ever mount it again.
	 * - deselected: the storage still exists, at least one row of oc_mounts
	 *   carries it through a provider that a Findling switch turned off (Team
	 *   Folders or external storage), and the mount list in force does not
	 *   carry it through any other provider. D-36-14: a switch turned off is a
	 *   decision of the admin like an exclusion, so it clears without a grace
	 *   period.
	 *
	 * Everything else stays out of both lists, and the container keeps its
	 * grace period for it (D-36-05): a storage that exists and is mounted
	 * nowhere is just as likely a mount that is about to come back.
	 *
	 * Why oc_mounts and not the mount list. getMounts() answers which mounts are
	 * IN, composed out of providers(), and a storage that a switch left out is by
	 * definition not in that answer, so it cannot say why the storage is absent.
	 * oc_mounts holds the provider class every mount was set up by, which is
	 * exactly the reason. The composed list is still consulted, through
	 * isIndexedStorage(), so a storage that a listed provider carries as well is
	 * never reported as switched off; and backend/tests/test_exclusion_path_space.py
	 * keeps the mount query at its one call site.
	 *
	 * Nothing but the asked numbers leaves this method: no path, no mount point,
	 * no storage key and no user. Ids that are not positive are dropped, so an
	 * answer never names a storage the caller did not ask about.
	 *
	 * @param list<int> $storageIds
	 * @return array{gone: list<int>, deselected: list<int>}
	 */
	public function classifyAbsent(array $storageIds): array {
		$wanted = [];
		foreach ($storageIds as $storageId) {
			if (is_int($storageId) && $storageId > 0) {
				$wanted[$storageId] = true;
			}
		}
		$wanted = array_keys($wanted);
		sort($wanted);

		if ($wanted === []) {
			return ['gone' => [], 'deselected' => []];
		}

		$existing = [];
		foreach (array_chunk($wanted, self::ABSENT_LOOKUP_BAND) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->select('numeric_id')
				->from('storages')
				->where($qb->expr()->in('numeric_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));

			$result = $qb->executeQuery();
			try {
				while (($row = $result->fetch()) !== false) {
					$existing[(int)($row['numeric_id'] ?? 0)] = true;
				}
			} finally {
				$result->closeCursor();
			}
		}

		$gone = array_values(array_filter($wanted, static fn (int $storageId): bool => !isset($existing[$storageId])));

		return ['gone' => $gone, 'deselected' => $this->deselected(array_keys($existing))];
	}

	/**
	 * Groups of storages that show the same share, for the coverage figure only.
	 *
	 * Weg C of 35-DEDUP-NOTIZ (owner decision D-37-03): an external storage that
	 * connects with the credentials of each user gets one storage id per user,
	 * because the login name is part of the id (F1), and so the crawl counts the
	 * same share once per user. Since 1.6.3 (plan 43-21, D-43-15, D-43-17) the
	 * key of a group is the share of shareIdentity(), without the root and with
	 * host and share name folded: one share mounted with different roots or in
	 * two spellings is one group. The roots stay apart in the identity, and the
	 * document key of 43-22 carries them, so two different files never become
	 * one document. Storages without an identity are never grouped.
	 *
	 * Only groups of two or more come back, each in ascending order, and the
	 * list is sorted by its first member. The identities come from one call of
	 * shareIdentities(), whose queries are banded. Nothing but numbers leaves
	 * this method: no host, no share and no user in the answer and in no log
	 * line (T-39-01). The answer feeds a figure on the admin page and nothing
	 * else; crawl, index and permissions never see it (T-39-03, T-39-05).
	 *
	 * The overview asks shareIdentities() once and hands the answer in
	 * (plan 43-23), so the grouping and the per document count work on the
	 * same identities and the configuration is read once per page. Only the
	 * identities of the asked ids are taken.
	 *
	 * @param list<int> $storageIds
	 * @param array<int, array{share: string, root: string}>|null $identities the answer of shareIdentities($storageIds)
	 * @return list<list<int>>
	 */
	public function countingKeyGroups(array $storageIds, ?array $identities = null): array {
		$asked = self::positiveIds($storageIds);
		if (count($asked) < 2) {
			return [];
		}

		$identities ??= $this->shareIdentities($storageIds);
		$byShare = [];
		foreach ($asked as $storageId) {
			$identity = $identities[$storageId] ?? null;
			if (is_array($identity) && is_string($identity['share'] ?? null) && $identity['share'] !== '') {
				$byShare[$identity['share']][] = $storageId;
			}
		}

		$groups = [];
		foreach ($byShare as $members) {
			if (count($members) < 2) {
				continue;
			}
			sort($members);
			$groups[] = $members;
		}
		usort($groups, static fn (array $a, array $b): int => $a[0] <=> $b[0]);

		return $groups;
	}

	/**
	 * The counting key of one storage id, or null when it must not be grouped.
	 *
	 * Since 1.6.3 this is the share of shareIdentity(): backend, host and share
	 * name folded to ASCII lower case, for SFTP the login name in front of the
	 * host, and no root (plan 43-21). Until 1.6.2 the key carried the root as
	 * written into the id and compared it character by character.
	 *
	 * Static and public for the reason coverageShare() of AdminViewService is:
	 * it is string arithmetic, and a test can ask it without a database.
	 */
	public static function countingKey(string $storageId): ?string {
		return self::shareIdentity($storageId)['share'] ?? null;
	}

	/**
	 * The share identity of one written out storage id, or null when the id
	 * must never be grouped.
	 *
	 * The leading rule of plans 43-21 to 43-29: two different files must never
	 * become one document. Every doubt therefore ends in null, which is the
	 * counting of 1.5 (a figure too high, never a merge). The identity serves
	 * the counting only and never search, paths, permissions or the gateway
	 * (backend/tests/test_share_identity_cases.py holds the callers).
	 *
	 * The forms, read in nextcloud/server stable33 4dd6d385, stable34 350ee0c4
	 * and stable35 b3adc84c (09.11.2026):
	 * - SMB, apps/files_external/lib/Lib/Storage/SMB.php getId (stable33
	 *   :136-141, stable34/35 :137-142): 'smb::' . <login> . '@' . <host> .
	 *   '//' . <share name> . '/' . <root>; the root always reads '/x/' and the
	 *   root '/' stays '/' (:114-116), so 'smb::u@h//Daten//' and
	 *   'smb::u@h//Daten//Projekte/'; the share name is trim(share, '/')
	 *   (:112); the login carries no workgroup (splitUser :126-134).
	 * - SFTP, SFTP.php getId (stable33 :155-163, stable34 :157-166, stable35
	 *   :164-173): 'sftp::' . <login> . '@' . <host> [':' . <port> unless 22]
	 *   . '/' . <root>, root cleaned and written as '/x/'.
	 *
	 * The identity: share is 'smb::' . host . '//' . share name, both in ASCII
	 * lower case, because Samba section names and host names ignore case
	 * (smb.conf(5), RFC 4343; OE-1 a); for SFTP 'sftp::' . login . '@' .
	 * host[:port], the host folded and the login as written, so that two logins
	 * on one host, a chroot per user among them, never merge (OE-4 a). root is
	 * the root without leading and trailing slashes, doubled slashes and '.'
	 * segments removed, never folded (Bericht.txt and bericht.txt are two files
	 * on a Linux server and two rows in Nextcloud), in Unicode NFC like the
	 * file cache of Nextcloud (lib/private/Files/Cache/Cache.php normalize,
	 * stable34 :1253-1255), which normalises paths but not the root of an id.
	 *
	 * Null for a backend outside COUNTING_KEY_BACKENDS (WebDAV and ownCloud
	 * cannot tell host and root apart in their id), for an id Nextcloud
	 * shortened to its md5 (only shareIdentities() can resolve it), for an id
	 * without '@' in front of the first '//' or without '//', for an empty host
	 * or share name, a share name with '/' or a backslash, a root with a '..'
	 * segment or a backslash, and for the Samba share 'homes' or a share named
	 * like the login of the id, which give every user an own tree under one
	 * name (OE-3 a). The host is the text after the LAST '@' in front of the
	 * first '//', so a login with an '@' of its own stays out of it whole.
	 *
	 * @return array{share: string, root: string}|null
	 */
	public static function shareIdentity(string $storageId): ?array {
		if (preg_match('/^[0-9a-f]{32}$/D', $storageId) === 1) {
			return null;
		}

		$prefix = null;
		foreach (self::COUNTING_KEY_BACKENDS as $backend) {
			if (str_starts_with($storageId, $backend)) {
				$prefix = $backend;
				break;
			}
		}
		if ($prefix === null) {
			return null;
		}

		$rest = substr($storageId, strlen($prefix));
		$split = strpos($rest, '//');
		if ($split === false || $split === 0) {
			return null;
		}

		$loginAndHost = substr($rest, 0, $split);
		$behind = substr($rest, $split + 2);
		$at = strrpos($loginAndHost, '@');
		if ($at === false) {
			return null;
		}
		$login = substr($loginAndHost, 0, $at);
		$host = substr($loginAndHost, $at + 1);
		if ($host === '') {
			return null;
		}

		if ($prefix === 'smb::') {
			$shareEnd = strpos($behind, '//');
			if ($shareEnd === false || $shareEnd === 0) {
				return null;
			}
			$shareName = substr($behind, 0, $shareEnd);
			if (str_contains($shareName, '/') || str_contains($shareName, '\\')) {
				return null;
			}
			$folded = strtolower($shareName);
			if ($folded === 'homes' || $folded === strtolower($login)) {
				return null;
			}
			$share = 'smb::' . strtolower($host) . '//' . $folded;
			$rootPart = substr($behind, $shareEnd + 2);
		} else {
			$share = 'sftp::' . $login . '@' . strtolower($host);
			$rootPart = $behind;
		}

		$root = self::cleanRoot($rootPart);
		if ($root === null) {
			return null;
		}

		return ['share' => $share, 'root' => $root];
	}

	/**
	 * The root part of an id without edge slashes, doubled slashes and '.'
	 * segments, in NFC; null for a '..' segment or a backslash, which could
	 * leave the tree or split a name on the server.
	 */
	private static function cleanRoot(string $rootPart): ?string {
		if (str_contains($rootPart, '\\')) {
			return null;
		}

		$segments = [];
		foreach (explode('/', $rootPart) as $segment) {
			if ($segment === '' || $segment === '.') {
				continue;
			}
			if ($segment === '..') {
				return null;
			}
			$segments[] = $segment;
		}
		$root = implode('/', $segments);

		// The same fallback as DocKeyService::docKeyOf: without intl the root
		// stays as it is, and an id that is not valid UTF-8 as well.
		if (class_exists(\Normalizer::class)) {
			$composed = \Normalizer::normalize($root, \Normalizer::FORM_C);
			if (is_string($composed)) {
				$root = $composed;
			}
		}

		return $root;
	}

	/**
	 * The share identities of the asked storages, keyed and ordered by storage
	 * id; storages without an identity are left out.
	 *
	 * A written out id goes through shareIdentity(). An id above 64 characters
	 * Nextcloud stores as its md5 (lib/private/Files/Cache/Storage.php
	 * adjustStorageId, stable33 :85-90, stable34 :100-105, stable35 :102-107),
	 * and such an id is resolved over the configuration of the external
	 * storage (OE-2 a, exception A-3), read only and with five keys:
	 * - oc_mounts gives storage_id, user_id and mount_id of the mounts of
	 *   files_external (mount_provider_class ConfigAdapter); the mount id is
	 *   the id of the storage configuration (UserMountCache, ConfigAdapter
	 *   storageConfigToMount).
	 * - oc_external_mounts gives the backend, only 'smb' and 'sftp'.
	 * - oc_external_config gives host, share, root, user and port, never the
	 *   password and never another key.
	 * Per mount the login candidates are the configured user (for SMB without
	 * workgroup, like SMB.php splitUser) and the user id of the mount; '$user'
	 * is replaced by the user id the way files_external does it (str_ireplace,
	 * SimpleSubstitutionTrait :65), and any other '$' left in a value means
	 * no identity, because another placeholder may stand there. The id is
	 * rebuilt like SMB.php and SFTP.php getId, and only when its md5 is the
	 * stored id exactly does it count, with the identity of the rebuilt id. A
	 * wrong guess therefore never merges anything, it stays ungrouped.
	 * Global, user provided and Kerberos credentials and a login name other
	 * than the user id (LDAP, AD) cannot be rebuilt and stay ungrouped.
	 *
	 * No cache over the call: cron.php lives over many jobs and a stored
	 * answer would outlive a changed configuration. The overview gets one
	 * answer by asking once and handing it on (43-23). The counters of the call
	 * are kept for shareIdentityStats(). The values read stay inside this call;
	 * a failing query of the configuration leaves the hashed ids ungrouped and
	 * logs counters only.
	 *
	 * @param list<int> $storageIds
	 * @return array<int, array{share: string, root: string}>
	 */
	public function shareIdentities(array $storageIds): array {
		return $this->identitiesOf($storageIds, false);
	}

	/**
	 * What DocKeyService::docKeysFor takes the share and the root of a key
	 * from: shareIdentities() with two differences, both because a key is
	 * stored in the container and outlives the moment it was asked in (audit
	 * finding F-43B-01).
	 *
	 * A failing query of the configuration throws. The grouping may go on
	 * without the hashed ids, which costs a figure too high for one overview;
	 * a key taken from an error would stay.
	 *
	 * A hashed id without identity gets the share HASHED_WITHOUT_IDENTITY and
	 * its storage number, with an empty root. Its identity depends on the
	 * moment: out of the mount list while its rows wait for the sweep, a
	 * configuration that changed, a login that cannot be rebuilt. With an
	 * empty share two such members of one share under two roots gave two
	 * files with the same rest path one key, and back in their group the two
	 * files were one document. With its number in the share the key of such a
	 * storage meets no key of another storage: it counts per storage, like
	 * every hashed id that cannot be resolved (43-21), too much at worst and
	 * never merged, and the verify pass puts the keys right once the identity
	 * is back. A written out id needs none of this, its identity is in the id
	 * and never changes.
	 *
	 * The number is no identity: the grouping never asks this method, and
	 * shareIdentityStats() counts as after shareIdentities().
	 *
	 * @param list<int> $storageIds
	 * @return array<int, array{share: string, root: string}>
	 */
	public function docKeyIdentities(array $storageIds): array {
		return $this->identitiesOf($storageIds, true);
	}

	/**
	 * @param list<int> $storageIds
	 * @return array<int, array{share: string, root: string}>
	 */
	private function identitiesOf(array $storageIds, bool $forDocKeys): array {
		$this->identityStats = self::emptyIdentityStats();
		$wanted = self::positiveIds($storageIds);
		if ($wanted === []) {
			return [];
		}

		$identities = [];
		$hashed = [];
		foreach (array_chunk($wanted, self::ABSENT_LOOKUP_BAND) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->select('numeric_id', 'id')
				->from('storages')
				->where($qb->expr()->in('numeric_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));

			$result = $qb->executeQuery();
			try {
				while (is_array($row = $result->fetch())) {
					$numericId = (int)($row['numeric_id'] ?? 0);
					$id = (string)($row['id'] ?? '');
					if ($numericId <= 0) {
						continue;
					}
					if (preg_match('/^[0-9a-f]{32}$/D', $id) === 1) {
						$hashed[$numericId] = $id;
						continue;
					}
					$identity = self::shareIdentity($id);
					if ($identity !== null) {
						$identities[$numericId] = $identity;
						$this->identityStats['parsed']++;
					} elseif (self::isCountingBackend($id)) {
						$this->identityStats['excluded']++;
					}
				}
			} finally {
				$result->closeCursor();
			}
		}

		if ($hashed !== []) {
			try {
				$resolved = $this->resolveHashed($hashed);
			} catch (\Exception $e) {
				if ($forDocKeys) {
					throw $e;
				}
				$this->identityStats['hashedUngrouped'] += count($hashed);
				$this->logger->warning(
					'Findling: the configuration of external storages could not be read, hashed={hashed} storage ids stay ungrouped',
					['hashed' => count($hashed), 'exception' => get_class($e)],
				);
				$resolved = [];
			}
			foreach ($resolved as $numericId => $identity) {
				$identities[$numericId] = $identity;
			}
			if ($forDocKeys) {
				foreach (array_keys($hashed) as $numericId) {
					$identities[$numericId] ??= ['share' => self::HASHED_WITHOUT_IDENTITY . $numericId, 'root' => ''];
				}
			}
		}

		ksort($identities);

		return $identities;
	}

	/**
	 * The counters of the last shareIdentities() call, numbers only.
	 *
	 * parsed: written out ids with an identity. hashedVerified: hashed ids
	 * whose rebuilt id has the stored md5 and an identity. hashedUngrouped:
	 * hashed ids with at least one smb or sftp mount of files_external and no
	 * match, or all hashed ids when the configuration could not be read.
	 * placeholder: those of hashedUngrouped for which a candidate was given up
	 * because a '$' other than '$user' was left. excluded: smb and sftp ids,
	 * written out or rebuilt with a matching md5, that shareIdentity() refuses
	 * (homes, a share named like the login, '..', a backslash, a malformed id).
	 *
	 * @return array{parsed: int, hashedVerified: int, hashedUngrouped: int, placeholder: int, excluded: int}
	 */
	public function shareIdentityStats(): array {
		return $this->identityStats;
	}

	/**
	 * Resolves hashed ids over the configuration of files_external, see
	 * shareIdentities(). Throws when a query throws; the caller counts.
	 *
	 * @param array<int, string> $hashed md5 per storage id
	 * @return array<int, array{share: string, root: string}>
	 */
	private function resolveHashed(array $hashed): array {
		// storage id => list of [user id, mount id]
		$mountsOf = [];
		foreach (array_chunk(array_keys($hashed), self::ABSENT_LOOKUP_BAND) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->select('storage_id', 'user_id', 'mount_id', 'mount_provider_class')
				->from('mounts')
				->where($qb->expr()->in('storage_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)))
				->andWhere($qb->expr()->eq('mount_provider_class', $qb->createNamedParameter(self::EXTERNAL_STORAGE_MOUNT_PROVIDER, IQueryBuilder::PARAM_STR)))
				->andWhere($qb->expr()->isNotNull('mount_id'));

			$result = $qb->executeQuery();
			try {
				while (is_array($row = $result->fetch())) {
					$storageId = (int)($row['storage_id'] ?? 0);
					$mountId = (int)($row['mount_id'] ?? 0);
					$userId = (string)($row['user_id'] ?? '');
					if (!isset($hashed[$storageId]) || $mountId <= 0 || $userId === ''
						|| (string)($row['mount_provider_class'] ?? '') !== self::EXTERNAL_STORAGE_MOUNT_PROVIDER) {
						continue;
					}
					$mountsOf[$storageId][] = [$userId, $mountId];
				}
			} finally {
				$result->closeCursor();
			}
		}

		$mountIds = [];
		foreach ($mountsOf as $mounts) {
			foreach ($mounts as [, $mountId]) {
				$mountIds[$mountId] = true;
			}
		}
		$mountIds = array_keys($mountIds);
		sort($mountIds);

		$backendOf = [];
		foreach (array_chunk($mountIds, self::ABSENT_LOOKUP_BAND) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->select('mount_id', 'storage_backend')
				->from('external_mounts')
				->where($qb->expr()->in('mount_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)))
				->andWhere($qb->expr()->in('storage_backend', $qb->createNamedParameter(self::REBUILT_BACKENDS, IQueryBuilder::PARAM_STR_ARRAY)));

			$result = $qb->executeQuery();
			try {
				while (is_array($row = $result->fetch())) {
					$backend = (string)($row['storage_backend'] ?? '');
					if (in_array($backend, self::REBUILT_BACKENDS, true)) {
						$backendOf[(int)($row['mount_id'] ?? 0)] = $backend;
					}
				}
			} finally {
				$result->closeCursor();
			}
		}

		$configOf = [];
		$configured = array_keys($backendOf);
		sort($configured);
		foreach (array_chunk($configured, self::ABSENT_LOOKUP_BAND) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->select('mount_id', 'key', 'value')
				->from('external_config')
				->where($qb->expr()->in('mount_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)))
				->andWhere($qb->expr()->in('key', $qb->createNamedParameter(self::REBUILT_CONFIG_KEYS, IQueryBuilder::PARAM_STR_ARRAY)));

			$result = $qb->executeQuery();
			try {
				while (is_array($row = $result->fetch())) {
					$key = (string)($row['key'] ?? '');
					if (in_array($key, self::REBUILT_CONFIG_KEYS, true)) {
						$configOf[(int)($row['mount_id'] ?? 0)][$key] = (string)($row['value'] ?? '');
					}
				}
			} finally {
				$result->closeCursor();
			}
		}

		$identities = [];
		foreach ($hashed as $storageId => $stored) {
			$relevant = false;
			$placeholder = false;
			$matched = null;
			foreach ($mountsOf[$storageId] ?? [] as [$userId, $mountId]) {
				if (!isset($backendOf[$mountId])) {
					continue;
				}
				$relevant = true;
				foreach (self::rebuiltIds($backendOf[$mountId], $configOf[$mountId] ?? [], $userId, $placeholder) as $rebuilt) {
					if (hash_equals($stored, md5($rebuilt))) {
						$matched = $rebuilt;
						break 2;
					}
				}
			}

			if ($matched !== null) {
				$identity = self::shareIdentity($matched);
				if ($identity !== null) {
					$identities[$storageId] = $identity;
					$this->identityStats['hashedVerified']++;
				} else {
					$this->identityStats['excluded']++;
				}
			} elseif ($relevant) {
				$this->identityStats['hashedUngrouped']++;
				if ($placeholder) {
					$this->identityStats['placeholder']++;
				}
			}
		}

		return $identities;
	}

	/**
	 * The storage ids files_external would build out of one configuration for
	 * one user, one per login candidate. Sets $placeholder when a '$' other
	 * than '$user' is left, and gives nothing then.
	 *
	 * @param array<string, string> $config
	 * @return list<string>
	 */
	private static function rebuiltIds(string $backend, array $config, string $userId, bool &$placeholder): array {
		$values = [];
		foreach (self::REBUILT_CONFIG_KEYS as $key) {
			if (isset($config[$key])) {
				$values[$key] = str_ireplace('$user', $userId, $config[$key]);
			}
		}
		foreach ($values as $value) {
			if (str_contains($value, '$')) {
				$placeholder = true;

				return [];
			}
		}
		if (($values['host'] ?? '') === '') {
			return [];
		}

		$logins = [];
		if (isset($values['user']) && $values['user'] !== '') {
			$logins[] = $backend === 'smb' ? self::smbLogin($values['user']) : $values['user'];
		}
		$logins[] = $userId;
		$logins = array_values(array_unique($logins));

		$ids = [];
		if ($backend === 'smb') {
			if (!isset($values['share'])) {
				return [];
			}
			// SMB.php :112-116.
			$root = '/' . ltrim($values['root'] ?? '/', '/');
			$root = rtrim($root, '/') . '/';
			foreach ($logins as $login) {
				$ids[] = 'smb::' . $login . '@' . $values['host'] . '//' . trim($values['share'], '/') . '/' . $root;
			}

			return $ids;
		}

		// SFTP.php splitHost, port and root (stable34 :49-64, :94-98).
		$parsed = parse_url(str_contains($values['host'], '://') ? $values['host'] : 'http://' . $values['host']);
		if (!is_array($parsed) || !isset($parsed['host'])) {
			return [];
		}
		$host = $parsed['host'];
		$port = isset($values['port']) && is_numeric($values['port'])
			? (int)$values['port']
			: (int)($parsed['port'] ?? 22);
		$root = isset($values['root']) ? self::sftpCleanPath($values['root']) : '/';
		$root = '/' . ltrim($root, '/');
		$root = rtrim($root, '/') . '/';
		foreach ($logins as $login) {
			$ids[] = 'sftp::' . $login . '@' . $host . ($port !== 22 ? ':' . $port : '') . '/' . $root;
		}

		return $ids;
	}

	/** The login of SMB.php splitUser: without a workgroup in front of '/' or '\'. */
	private static function smbLogin(string $user): string {
		if (str_contains($user, '/')) {
			return explode('/', $user, 2)[1];
		}
		if (str_contains($user, '\\')) {
			return explode('\\', $user)[1];
		}

		return $user;
	}

	/** lib/private/Files/Storage/Common.php cleanPath (stable34 :433-448), which SFTP uses for its root. */
	private static function sftpCleanPath(string $path): string {
		if ($path === '' || $path[0] !== '/') {
			$path = '/' . $path;
		}
		$output = [];
		foreach (explode('/', $path) as $chunk) {
			if ($chunk === '..') {
				array_pop($output);
			} elseif ($chunk !== '.') {
				$output[] = $chunk;
			}
		}

		return implode('/', $output);
	}

	private static function isCountingBackend(string $storageId): bool {
		foreach (self::COUNTING_KEY_BACKENDS as $prefix) {
			if (str_starts_with($storageId, $prefix)) {
				return true;
			}
		}

		return false;
	}

	/**
	 * @param list<mixed> $storageIds
	 * @return list<int> positive, without doubles, ascending
	 */
	private static function positiveIds(array $storageIds): array {
		$wanted = [];
		foreach ($storageIds as $storageId) {
			if (is_int($storageId) && $storageId > 0) {
				$wanted[$storageId] = true;
			}
		}
		$wanted = array_keys($wanted);
		sort($wanted);

		return $wanted;
	}

	/** @return array{parsed: int, hashedVerified: int, hashedUngrouped: int, placeholder: int, excluded: int} */
	private static function emptyIdentityStats(): array {
		return ['parsed' => 0, 'hashedVerified' => 0, 'hashedUngrouped' => 0, 'placeholder' => 0, 'excluded' => 0];
	}

	/**
	 * The existing storages among the asked ones that only a switched off
	 * provider carries. The second half of classifyAbsent().
	 *
	 * The provider filter travels into the query, so that a Team Folder with
	 * hundreds of members comes back as one row and not as one row per member,
	 * and it is checked once more on every row, so that the decision does not
	 * rest on the dialect getting the comparison right.
	 *
	 * @param list<int> $existing
	 * @return list<int>
	 */
	private function deselected(array $existing): array {
		$switchedOff = [];
		if (!$this->settingsService->indexTeamFolders()) {
			$switchedOff[] = self::TEAM_FOLDER_MOUNT_PROVIDER;
		}
		if (!$this->settingsService->indexExternalStorage()) {
			$switchedOff[] = self::EXTERNAL_STORAGE_MOUNT_PROVIDER;
		}

		$existing = array_values(array_filter($existing, static fn (int $storageId): bool => $storageId > 0));
		if ($switchedOff === [] || $existing === []) {
			return [];
		}

		$deselected = [];
		foreach (array_chunk($existing, self::ABSENT_LOOKUP_BAND) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->selectDistinct(['storage_id', 'mount_provider_class'])
				->from('mounts')
				->where($qb->expr()->in('storage_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)))
				->andWhere($qb->expr()->in('mount_provider_class', $qb->createNamedParameter($switchedOff, IQueryBuilder::PARAM_STR_ARRAY)));

			$result = $qb->executeQuery();
			try {
				while (($row = $result->fetch()) !== false) {
					$storageId = (int)($row['storage_id'] ?? 0);
					$provider = (string)($row['mount_provider_class'] ?? '');
					if ($storageId > 0 && in_array($provider, $switchedOff, true)) {
						$deselected[$storageId] = true;
					}
				}
			} finally {
				$result->closeCursor();
			}
		}

		$ids = [];
		foreach (array_keys($deselected) as $storageId) {
			if (!$this->isIndexedStorage($storageId)) {
				$ids[] = $storageId;
			}
		}
		sort($ids);

		return $ids;
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
	 * What the reconcile does need is to know which rows a rule of today keeps
	 * out, and that is what the optional predicate is for (owner decision of
	 * 03.10.2026, part a, after run 7 of the 28-07 chain). Given one, every row
	 * carries an ``excluded`` flag next to the five fields: the row is marked and
	 * never dropped, for the reason in the paragraph above. The predicate gets the
	 * internal path of the cache entry and answers with the rule; it is handed in
	 * rather than asked for because ExclusionService depends on this class, and
	 * injecting it here would be a cycle. The path never leaves this method, and
	 * no prefix is compared here: the caller builds the predicate out of
	 * ExclusionService::isExcluded on the one path space.
	 *
	 * @param (\Closure(string): bool)|null $isExcludedPath
	 * @return list<array{fileId: int, etag: string, size: int, mtime: int, mime: string, excluded?: bool}>
	 */
	public function getFileSlice(int $storageId, int $overriddenRoot, int $lastFileId, int $batchSize, ?\Closure $isExcludedPath = null): array {
		$rows = [];
		foreach ($this->getFilesInMount($storageId, $overriddenRoot, $lastFileId, $batchSize) as $entry) {
			$row = [
				'fileId' => $entry->getId(),
				'etag' => $entry->getEtag(),
				// int on every ordinary file; the interface allows a float for
				// sizes beyond the integer range, and a document of that size
				// does not exist in an index capped at fifty megabytes.
				'size' => (int)$entry->getSize(),
				'mtime' => $entry->getMTime(),
				'mime' => $entry->getMimeType(),
			];
			if ($isExcludedPath !== null) {
				$row['excluded'] = (bool)$isExcludedPath($entry->getPath());
			}
			$rows[] = $row;
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
