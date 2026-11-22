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
	 * file is read by the first name of its list; the number only matters on a
	 * Team Folder whose advanced permissions close a file to most of its
	 * members.
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
	 * @return array{users: list<string>, truncated: bool, owner: ?string}
	 */
	public function forFile(int $fileId): array {
		$userIds = [];
		$truncated = false;
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

				$userIds[] = $mount->getUser()->getUID();
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

		return ['users' => $userIds, 'truncated' => $truncated, 'owner' => null];
	}

	/**
	 * The names that are asked to read the file, in the order they are asked.
	 *
	 * @param list<string> $users sorted, as forFile() hands them out
	 * @return list<string>
	 */
	public static function readingOrder(array $users, ?string $owner): array {
		return array_slice($users, 0, self::MAX_READER_TRIES);
	}
}
