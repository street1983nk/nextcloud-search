<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\Files\Cache\ICacheEntry;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\ICachedMountFileInfo;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\IRootFolder;
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
 * The direction from a file id to a path goes through getMountsForFileId, and
 * deliberately not through the node lookup by id that getUserFolder() offers:
 * the node variant needs the owner before it can start and then sets up that
 * user's filesystem, which is expensive and buys nothing here, because nothing
 * below reads any content. This is a query over oc_mounts joined with
 * oc_filecache and nothing else. It sets up no filesystem, checks no permission
 * and therefore answers for a file the administrator may not open, which is the
 * point: an admin is allowed to be told the name of a file on their own
 * instance, and the search results of SRCH-02 remain the only place where
 * content is ever handed out.
 *
 * The opposite direction, a path back to a file id, is the one thing that cannot
 * be done that way, and that is why getUserFolder() is injected here since plan
 * 04-07. A relative path exists once per user on the instance, so it names a
 * file only together with an owner, and the mounts of that owner have to be set
 * up before their shares and Team Folders are reachable at all. Asking the root
 * folder for the absolute path instead would answer for the home storage and
 * quietly miss everything mounted into it.
 *
 * So there is no file handle, no stream, no content and no snippet in this file,
 * and there is no path in any of its log lines either (T-04-32). A diagnostic
 * class that leaked into the log what it refuses to leak into an answer would
 * only have moved the leak. The grep for the four calls that would break that
 * promise stays at zero over this file, which is why none of the four is
 * spelled out anywhere above.
 */
final class PathResolverService {
	/**
	 * The longest run of digits that can still be a file id.
	 *
	 * Nineteen, which is the width of a signed 64 bit integer, and it comes out
	 * of the design contract: rein numerisch bis 19 Ziffern is treated as a file
	 * id and everything else as a path. A longer run of digits is neither: it
	 * cannot be an id and it is not a path either, so it is refused rather than
	 * cut, because a cut number would answer about a different file.
	 */
	private const MAX_ID_DIGITS = 19;

	/**
	 * How many lookup references were refused since this process started.
	 *
	 * Counted and never logged with its value. The field an administrator types
	 * into carries a file name, so the value is exactly the thing the log of this
	 * app does not take (T-04-38). The number is a counter and counters are what
	 * the log is for.
	 */
	private int $refused = 0;

	public function __construct(
		private IUserMountCache $mountCache,
		private IFileAccess $fileAccess,
		private IRootFolder $rootFolder,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * One line of admin input as a file id, or null when it names nothing.
	 *
	 * D-04 in one method: the same field takes a path or a number, because an
	 * administrator who has a path does not want to look up an id first and one
	 * who copied an id out of the error list does not want to build a path. The
	 * split is the shape of the input and nothing else: a run of digits is an id,
	 * anything else is a path.
	 *
	 * A path is resolved through the user's own folder and never through the root
	 * folder directly. IRootFolder::get('/alice/files/x') looks like the shorter
	 * way and is not the same thing: the mounts of a user are set up by
	 * getUserFolder($uid), so the direct call answers for the home storage and
	 * misses every share and every Team Folder of that user.
	 *
	 * Null is the only failure answer, and it is the same null for a path that
	 * does not exist, a path under a user that does not exist and a path this app
	 * refuses to interpret. That is deliberate: three distinguishable answers
	 * here would turn this field into a way of asking which user names exist on
	 * the instance (T-04-38).
	 */
	public function resolveReference(string $input): ?int {
		$reference = trim($input);
		if ($reference === '') {
			$this->refuse();

			return null;
		}

		if (ctype_digit($reference)) {
			if (strlen($reference) > self::MAX_ID_DIGITS) {
				$this->refuse();

				return null;
			}

			$fileId = (int)$reference;

			return $fileId > 0 ? $fileId : null;
		}

		return $this->fileIdOfPath($reference);
	}

	/**
	 * Everything the diagnosis needs about one file: where it is and what it is.
	 *
	 * Two lookups behind one answer, and they answer different halves. The cache
	 * entry carries the storage, the mimetype and the size, which is what the
	 * live rule check of the diagnosis compares against the rules of today. The
	 * mount lookup carries the owner and the readable path, which is what a human
	 * needs in order to recognise the file they asked about.
	 *
	 * Null means the file has no cache entry and no mount row any more, so it is
	 * really gone rather than merely invisible to the administrator. That
	 * distinction is the first stage of the precedence rule and it is the reason
	 * a tombstone in the container may not be read as a deletion on its own
	 * (pitfall 6).
	 *
	 * @return array{
	 *     uid:string, path:string, shares:int, trashed:bool,
	 *     storageId:int, mime:string, size:int
	 * }|null
	 */
	public function inspect(int $fileId): ?array {
		if ($fileId <= 0) {
			return null;
		}

		$entry = null;
		try {
			$entries = $this->fileAccess->getByFileIds([$fileId]);
			$entry = $entries[$fileId] ?? null;
		} catch (\Throwable $e) {
			// The cheap half, and losing it costs three fields rather than the
			// answer: the path below still comes out of the mount cache.
			$this->logger->debug('Findling: cache lookup for a single file failed', ['exception' => $e]);
		}

		$owner = $this->describe($fileId);
		if (!$entry instanceof ICacheEntry && $owner === null) {
			return null;
		}

		return [
			'uid' => $owner['uid'] ?? '',
			'path' => $owner['path'] ?? '',
			'shares' => $owner['shares'] ?? 0,
			'trashed' => $owner['trashed'] ?? false,
			'storageId' => $entry instanceof ICacheEntry ? $entry->getStorageId() : 0,
			'mime' => $entry instanceof ICacheEntry ? $entry->getMimeType() : '',
			'size' => $entry instanceof ICacheEntry ? max(0, $entry->getSize()) : 0,
		];
	}

	/**
	 * A path in the notation Nextcloud keeps, as a file id.
	 *
	 * Two spellings are accepted, and both name a user, because a path without
	 * one cannot be resolved at all: a relative path exists once per user on the
	 * instance. ``alice/files/Ordner/x.pdf`` is the spelling the error list of
	 * this page shows next to the owner, and ``alice:Ordner/x.pdf`` is the short
	 * form for somebody who has the owner and the relative path in front of them.
	 *
	 * A segment of two dots is refused and not filtered. Filtering would answer
	 * about a file the administrator did not ask about, which is worse than
	 * answering nothing, and the resolution below walks a Folder rather than a
	 * file system path, so there is no traversal to defend against in the first
	 * place: this refusal exists so that a request carrying one is not answered
	 * as though it had made sense (T-04-37).
	 */
	private function fileIdOfPath(string $input): ?int {
		$candidate = str_replace('\\', '/', $input);
		$candidate = (string)preg_replace('#/+#', '/', $candidate);
		$candidate = trim($candidate, '/');
		if ($candidate === '') {
			$this->refuse();

			return null;
		}

		if (in_array('..', explode('/', $candidate), true)) {
			$this->refuse();

			return null;
		}

		[$uid, $relative] = $this->splitOwner($candidate);
		if ($uid === '' || $relative === '') {
			$this->refuse();

			return null;
		}

		try {
			// Every failure caught on purpose. getUserFolder() signals a missing
			// user with a class from the private namespace of the server and a
			// missing home directory with a different one again, NoUserException
			// being the first of the two, and both mean the same thing here. The
			// answer is word for word the answer of "no such file", so that this
			// field cannot be used to find out which users exist.
			$node = $this->rootFolder->getUserFolder($uid)->get($relative);
		} catch (\Throwable $e) {
			$this->logger->debug('Findling: a lookup reference resolved to nothing', ['exception' => $e]);
			$this->refuse();

			return null;
		}

		$fileId = $node->getId();

		return $fileId > 0 ? $fileId : null;
	}

	/**
	 * The owner and the path relative to their files folder, or two empty
	 * strings when the input names no owner.
	 *
	 * @return array{0:string, 1:string}
	 */
	private function splitOwner(string $candidate): array {
		$segments = explode('/', $candidate);
		if (count($segments) > 2 && $segments[1] === 'files') {
			return [$segments[0], implode('/', array_slice($segments, 2))];
		}

		$colon = strpos($segments[0], ':');
		if ($colon === false || $colon === 0) {
			return ['', ''];
		}

		$uid = substr($segments[0], 0, $colon);
		$segments[0] = substr($segments[0], $colon + 1);
		$relative = trim(implode('/', $segments), '/');

		return $relative === '' ? ['', ''] : [$uid, $relative];
	}

	/**
	 * Count one refused reference. The value never travels with it.
	 */
	private function refuse(): void {
		$this->refused++;
		$this->logger->debug('Findling: refused a lookup reference', ['refused' => $this->refused]);
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
