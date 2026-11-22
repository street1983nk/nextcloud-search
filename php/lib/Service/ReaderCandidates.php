<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\Files\Config\IUserMountCache;
use Psr\Log\LoggerInterface;

/**
 * Who sees a file, and in which order they are asked to read it.
 *
 * One service for both questions, because the queue (QueueService::readerOf)
 * and the content gateway ask them about the same file and must not answer
 * them differently: a list here and another order there is how a file ends up
 * read by one person in the claim and by another in the gateway.
 *
 * Nothing here logs a name. Counters and class names only.
 */
final class ReaderCandidates {
	/**
	 * How many users of one file are asked whether they may read it, before
	 * the row is given up as skipped(unreadable) (issue #14).
	 *
	 * Twenty, and the argument is at QueueService::readerOf(). The ordinary
	 * file is read by the first name of its order; the number only matters on a
	 * Team Folder whose advanced permissions close a file to most of its
	 * members. The owner first, and the owner counts (issue #59): twenty names
	 * in all, not the owner plus twenty.
	 *
	 * The one source of this number: QueueService and the content gateway read
	 * it from here, and the gate on the remedy text binds to this constant.
	 */
	public const MAX_READER_TRIES = 20;

	/**
	 * How many users of one file travel in a work order (perf audit M5).
	 *
	 * Without a ceiling an instance wide team folder puts the complete user list
	 * of the instance on every single file: five thousand users times thirty two
	 * files in one batch measured at roughly sixteen megabytes of heap on the PHP
	 * side and three and a half megabytes of JSON on the wire, per claim, for a
	 * list that is identical for every one of those files.
	 *
	 * Five hundred is chosen so that an ordinary instance never meets it. What
	 * happens beyond it is the interesting half, and it is a design decision
	 * rather than a truncation: the job is marked, the container writes one
	 * reserved collective row instead of the shortened list, and the prefilter
	 * treats the file as a candidate for anybody. The prefilter may be more
	 * generous than the truth and never stricter, because the security boundary
	 * is the final recheck in SearchService (COMP-04); writing the first five hundred
	 * names as if they were the whole list would be the strict direction and
	 * would hide the file from everybody behind the cap.
	 */
	private const MAX_USERS = 500;

	/**
	 * The mount providers of the server that build a home mount, as strings so
	 * that nothing is loaded (issue #59).
	 *
	 * Both build the mount point '/' . uid of their user (nextcloud/server
	 * stable33, stable34 and stable35, lib/private/Files/Mount/
	 * LocalHomeMountProvider.php and ObjectHomeMountProvider.php, getHomeMountForUser
	 * with self::class as provider), which the mount cache stores as '/<uid>/'
	 * (45-AUDIT.md, Mount-Cache-Probe on NC 35.0.3: '130 | bob | /bob/ |
	 * OC\Files\Mount\LocalHomeMountProvider'). ICachedMountInfo::getMountProvider()
	 * exists since NC 24.
	 */
	private const HOME_MOUNT_PROVIDERS = [
		'OC\Files\Mount\LocalHomeMountProvider',
		'OC\Files\Mount\ObjectHomeMountProvider',
	];

	public function __construct(
		private IUserMountCache $userMountCache,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * Everyone who sees this file, asked once per file.
	 *
	 * This is the simple variant, deliberately. The known optimisation asks once
	 * per storage instead and assigns files by path prefix afterwards, which
	 * saves roughly two hundred thousand queries on an instance with a hundred
	 * thousand files. It is not built here for two reasons. During the first
	 * index the HTTP fetch of every single file dominates the cost by orders of
	 * magnitude, so the saving would not be visible. And rebuilding the prefix
	 * logic of the mount cache is exactly the kind of cleverness that produces a
	 * systematically too wide prefilter, which is unsafe in the sense that it
	 * hands the search more candidates than it should. That optimisation belongs
	 * behind a measurement in phase 5, together with the parity test against
	 * this variant that is planned there anyway.
	 *
	 * This paragraph is here so the simple version is read as a decision rather
	 * than as an oversight.
	 *
	 * The answer is a list plus a mark and not a bare list, because a caller has
	 * no way of telling a capped list from a complete one by looking at it. Five
	 * hundred names are a plausible team folder either way, and guessing from the
	 * length would break the moment the ceiling moves.
	 *
	 * The owner (issue #59) is the user whose HOME mount carries the file:
	 * mount point exactly '/<uid>/' and a provider of HOME_MOUNT_PROVIDERS,
	 * nothing else. A share, a Team Folder and an external storage name no
	 * owner, and neither does a mount whose provider is unknown or empty. The
	 * owner is read in the same loop and costs no query of its own.
	 * Node::getOwner() was weighed and not taken: it needs a node, so a mount
	 * setup and a lookup per file before the reader is even chosen, and for a
	 * Team Folder it answers a user who may not read the file at all.
	 *
	 * The ceiling ends the loop, and that holds for the owner as well: a home
	 * mount that comes after five hundred other mounts is not looked at, the
	 * file then has no owner and is read in alphabetical order, as before. The
	 * ceiling bounds the user objects that are resolved per file (perf audit
	 * M5), and a file whose owner shares it with five hundred people is not the
	 * case of #59.
	 *
	 * A user the mount cache does not know yet (somebody who never logged in
	 * since a Team Folder was given to their group, I-45-17-04) is in no list
	 * and therefore no reader either.
	 *
	 * @return array{users: list<string>, truncated: bool, owner: ?string}
	 */
	public function forFile(int $fileId): array {
		$userIds = [];
		$truncated = false;
		$owner = null;
		try {
			// The user behind a mount can be gone between the mount cache and
			// this line, and that throws rather than returning null, so the loop
			// stays inside the guard.
			foreach ($this->userMountCache->getMountsForFileId($fileId) as $mount) {
				if (count($userIds) >= self::MAX_USERS) {
					// The ceiling is reached inside the loop rather than applied
					// to the finished list on purpose (perf audit M5): the point
					// is not to send a shorter answer, it is to stop building the
					// long one. An instance wide team folder has thousands of
					// mounts for one file, and every iteration resolves a user
					// object.
					$truncated = true;
					break;
				}

				$uid = $mount->getUser()->getUID();
				$userIds[] = $uid;
				if ($owner === null
					&& $mount->getMountPoint() === '/' . $uid . '/'
					&& in_array($mount->getMountProvider(), self::HOME_MOUNT_PROVIDERS, true)) {
					$owner = $uid;
				}
			}
		} catch (\Throwable $e) {
			$this->logger->warning('Findling: could not resolve who sees a queued file', ['exception' => $e]);
			return ['users' => [], 'truncated' => false, 'owner' => null];
		}

		if ($truncated) {
			// A counter and a file id, never a name. Worth a line because a file
			// that hits this ceiling is a file the prefilter stops narrowing down,
			// and an admin who wonders why a search got slower deserves to find
			// the reason in the log.
			$this->logger->info('Findling: capped the user list of a queued file', ['count' => count($userIds)]);
		}

		// Sorted and deduplicated: a file that is mounted twice for the same user
		// must not appear twice in the access payload, and a stable order means
		// a retried row is fetched in the same context as before.
		$userIds = array_values(array_unique($userIds));
		sort($userIds);

		return ['users' => $userIds, 'truncated' => $truncated, 'owner' => $owner];
	}

	/**
	 * The names that are asked to read the file, in the order they are asked:
	 * the owner first when the owner is among them, then the others in the
	 * order given, MAX_READER_TRIES names in all (issue #59).
	 *
	 * The queue and the gateway both ask this one method, so a file is read
	 * in the claim and opened again in the gateway in the same order. An owner
	 * who is not in the list changes nothing; the list is not widened by a
	 * name the mount cache did not give.
	 *
	 * @param list<string> $users sorted, as forFile() hands them out
	 * @return list<string>
	 */
	public static function readingOrder(array $users, ?string $owner): array {
		if ($owner !== null && in_array($owner, $users, true)) {
			$users = [$owner, ...array_values(array_filter($users, static fn (string $user): bool => $user !== $owner))];
		}

		return array_slice($users, 0, self::MAX_READER_TRIES);
	}
}
