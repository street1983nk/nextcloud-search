<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\Files\Cache\ICacheEntry;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\ICachedMountFileInfo;
use OCP\Files\Config\IUserMountCache;
use Psr\Log\LoggerInterface;

/**
 * Where a file id becomes something a human can read, and the only place.
 *
 * D-03 is the reason this class exists. The container answers with file ids,
 * states, reason codes and counters, and with no path and no file name at all,
 * although its own tables hold both. Nextcloud is the side that knows the
 * mounts, the owners and the mount points, so Nextcloud is the side that turns
 * a number back into a path, at display time, inside the permission model that
 * owns that decision.
 *
 * getMountsForFileId, and deliberately not the node lookup by id that
 * getUserFolder() offers: the node variant needs the owner before it can start
 * and then sets up that user's filesystem, which is expensive and buys nothing
 * here, because nothing below reads any content. This is a query over oc_mounts
 * joined with oc_filecache and nothing else. It sets up no filesystem, checks no
 * permission and therefore answers for a file the administrator may not open,
 * which is the point: an admin is allowed to be told the name of a file on their
 * own instance, and the search results of SRCH-02 remain the only place where
 * content is ever handed out.
 *
 * So there is no file handle, no stream, no content and no snippet in this file,
 * and there is no path in any of its log lines either (T-04-32). A diagnostic
 * class that leaked into the log what it refuses to leak into an answer would
 * only have moved the leak. The grep for the four calls that would break that
 * promise stays at zero over this file, which is why none of the four is
 * spelled out anywhere above.
 */
final class PathResolverService {
	public function __construct(
		private IUserMountCache $mountCache,
		private IFileAccess $fileAccess,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * The owner and the readable path of one file id, or null.
	 *
	 * This is a query over oc_mounts joined with oc_filecache and nothing
	 * else. It sets up no filesystem, checks no permission and therefore
	 * answers for a file the admin may not open himself, which is exactly
	 * what D-03 asks for: the container hands over a number, this side turns
	 * it into something a human can read.
	 *
	 * An empty answer means the file has no cache entry any more, so it is
	 * really gone rather than merely invisible.
	 *
	 * @return array{uid:string,path:string,shares:int,trashed:bool}|null
	 */
	public function describe(int $fileId): ?array {
		if ($fileId <= 0) {
			return null;
		}

		try {
			$mounts = $this->mountCache->getMountsForFileId($fileId);
			if ($mounts === []) {
				return null;
			}

			$owner = $this->ownerMountOf($mounts);
			$uid = $owner->getUser()->getUID();
			// getPath() is mountPoint . internalPath, so /alice/files/Ordner/x.pdf
			// for a home mount. The prefix is stripped for the display and the uid
			// is shown in its own column.
			$absolute = $owner->getPath();
			$prefix = '/' . $uid . '/files/';
			$trashed = str_starts_with($absolute, '/' . $uid . '/files_trashbin/');

			return [
				'uid' => $uid,
				'path' => str_starts_with($absolute, $prefix)
					? substr($absolute, strlen($prefix))
					: ltrim($absolute, '/'),
				'shares' => count($mounts) - 1,
				// A file in the trash bin still has a cache entry, and saying so is
				// a diagnosis rather than a detail: the search dropped it on
				// purpose (phase 3, D-10) and it is not a failure.
				'trashed' => $trashed,
			];
		} catch (\Throwable $e) {
			// Degraded to "not resolvable" and never to an error page. A mount
			// row pointing at a user who no longer exists throws here, and that
			// is a diagnosis of one line in the list rather than the end of the
			// whole list. The exception goes into its own field, where Nextcloud
			// renders it under the admin's own log level; no file id and no path
			// go into the message.
			$this->logger->debug('Findling: could not resolve a file id to a path', ['exception' => $e]);

			return null;
		}
	}

	/**
	 * One whole page of file ids, resolved in as few queries as possible.
	 *
	 * The cost, written down because it decides how this may be called: one
	 * batch query over the cache for the whole page, then per file id one mount
	 * cache query and the user lookup that getUser() performs behind it. So a
	 * page of twenty rows is roughly forty queries and a page of the whole table
	 * is a query storm. The consequence is a rule: resolve one page, never the
	 * table, and never more than MAX_PAGE rows in one call (T-04-34).
	 *
	 * The batch query comes first because it answers existence, mimetype and
	 * size for every id at once, and existence is the field that decides how a
	 * row is rendered. A file id with no cache entry is kept in the answer with
	 * resolved false rather than dropped: a line that vanishes from a diagnostic
	 * list takes its count with it, and the missing entry is itself the answer
	 * to "why is this file not indexed" (T-04-35).
	 *
	 * @param list<int> $fileIds
	 * @return array<int, array{
	 *     resolved:bool, uid:string, path:string, shares:int, trashed:bool,
	 *     exists:bool, mime:string, size:int
	 * }> keyed by file id, one entry per positive id that was asked for
	 */
	public function describeMany(array $fileIds): array {
		$wanted = [];
		foreach ($fileIds as $fileId) {
			if ($fileId > 0) {
				$wanted[$fileId] = true;
			}
		}
		if ($wanted === []) {
			return [];
		}

		$entries = [];
		try {
			$entries = $this->fileAccess->getByFileIds(array_keys($wanted));
		} catch (\Throwable $e) {
			// The batch query is the cheap half and losing it costs three
			// fields, not the answer: every row below still gets its path out
			// of the mount cache, and existence falls back to whether that
			// lookup found anything.
			$this->logger->debug('Findling: bulk cache lookup for the error list failed', ['exception' => $e]);
		}

		$described = [];
		foreach (array_keys($wanted) as $fileId) {
			$entry = $entries[$fileId] ?? null;
			$owner = $this->describe($fileId);

			$described[$fileId] = [
				'resolved' => $owner !== null,
				'uid' => $owner['uid'] ?? '',
				'path' => $owner['path'] ?? '',
				'shares' => $owner['shares'] ?? 0,
				'trashed' => $owner['trashed'] ?? false,
				'exists' => $entry instanceof ICacheEntry || $owner !== null,
				'mime' => $entry instanceof ICacheEntry ? $entry->getMimeType() : '',
				'size' => $entry instanceof ICacheEntry ? max(0, $entry->getSize()) : 0,
			];
		}

		return $described;
	}

	/**
	 * The home mount of the owner, or the first mount when there is none.
	 *
	 * A home mount is the one whose root has no internal path of its own;
	 * everything else is a share or a Team Folder. Guessing by the shortest
	 * path would break for a team folder mounted at the top level.
	 *
	 * Taken with reset() and not with index nought, because the server filters
	 * this array before handing it over and a filtered array keeps the keys of
	 * the one it came from. An index would work on most instances and throw on
	 * the one where the first mount of a file was dropped.
	 *
	 * @param array<int, ICachedMountFileInfo> $mounts non empty
	 */
	private function ownerMountOf(array $mounts): ICachedMountFileInfo {
		foreach ($mounts as $mount) {
			if ($mount->getRootInternalPath() === '') {
				return $mount;
			}
		}

		return reset($mounts);
	}
}
