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
 * which mounts are looked at, and which document types are considered. Both
 * are constants rather than configuration, because zero config means the
 * defaults have to be right, not adjustable.
 */
class StorageService {
	/**
	 * Which mounts the crawl walks.
	 *
	 * User homes in both flavours and Team Folders are in. External storage is
	 * out: a remote drive blows up every assumption the first index makes about
	 * how long reading a file takes and how much of it there is, and an admin
	 * who mounts a multi terabyte share does not expect an app installation to
	 * start pulling it through HTTP. It becomes a switch in phase 4 (ADM-04),
	 * which is why the line stays here instead of being deleted.
	 *
	 * Team Folders are called that since NC 31, but the app id and the mount
	 * provider class are unchanged. Whether the app is installed does not need
	 * to be checked: if it is not, there are no mounts of that class.
	 *
	 * @var list<string>
	 */
	private const MOUNT_PROVIDERS = [
		'OC\Files\Mount\LocalHomeMountProvider',   // user home, file backend
		'OC\Files\Mount\ObjectHomeMountProvider',  // user home, object storage backend
		'OCA\GroupFolders\Mount\MountProvider',    // Team Folders
		// 'OCA\Files_External\Config\ConfigAdapter' -- external storage, off by default
	];

	/**
	 * The document allowlist of the zero config guard rails: PDF, the OOXML
	 * trio, OpenDocument, plain text and Markdown, RTF and HTML.
	 *
	 * Everything else, and that includes video, audio and archives, is not a
	 * document and is never queued. Two spellings are listed for RTF because
	 * instances disagree on which one they store, and an entry this instance
	 * has never seen simply drops out below.
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
		'application/rtf',
		'text/rtf',
	];

	/**
	 * Resolved once per process. The translation is three queries at most and
	 * the crawl asks for it on every batch.
	 *
	 * @var list<int>|null
	 */
	private ?array $mimeIds = null;

	public function __construct(
		private IFileAccess $fileAccess,
		private IMimeTypeLoader $mimeTypeLoader,
		private LoggerInterface $logger,
	) {
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
		return $this->fileAccess->getDistinctMounts(self::MOUNT_PROVIDERS, true);
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
