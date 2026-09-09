<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\Text\PlainText;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\File;
use OCP\Files\IRootFolder;
use OCP\IUser;
use Psr\Log\LoggerInterface;

/**
 * One search run, and the security boundary of the whole product.
 *
 * There is exactly one of these in the tree, and that is the point of the
 * class. The search dialog and the own result page ask the same question and
 * must get the same answer, and a second implementation of this loop would be a
 * second surface that has to be given the permission chain, the paging
 * semantics and the parity job all over again. What holds the sentence is not
 * discipline but a counting gate:
 * ``backend/tests/test_php_acl_boundary.py`` reads every source under php/lib
 * with comments and string literals removed and counts the places that ask the
 * two questions this class asks below. A second caller is a red test, and a
 * functional test could not show its absence.
 *
 * The run happens in two stages. The container answers with candidates that
 * carry a file id and nothing else, this class decides which of them this user
 * may actually see, and only then does it ask for the text excerpts of the
 * survivors. The order is not an optimisation. An excerpt is file content, and
 * file content for a file the user cannot open must never enter this process in
 * the first place.
 *
 * The resolution through the user's own folder answers "is it reachable for
 * them", and the readability question right behind it answers "may they read
 * it". On an ordinary share the two are the same; on a team folder they are
 * not, because the ACL wrapper of groupfolders hands out a node that resolves
 * perfectly well while the per folder rules take the read bit away. Both are
 * asked in one block, one line apart, and everything a caller finally renders
 * is read after them.
 *
 * The wall clock is measured with a callable rather than with a bare hrtime()
 * call, and the seam exists for the tests: a case that waited the whole budget
 * in real seconds would make the suite slow and would go flaky on a loaded
 * runner. Nextcloud resolves the argument to its default, because the container
 * cannot build a Closure and falls back to the declared default when it cannot.
 * hrtime() and not microtime() stays the rule: a clock adjustment during a
 * search would otherwise either double the budget or end it at once.
 *
 * Every ceiling of a run arrives as an argument in {@see SearchCaps}, because
 * the two callers are allowed to be differently patient. What does not arrive
 * from outside are the two character ceilings below: they are properties of the
 * file system this class reads, not of whoever is asking.
 *
 * @final This class is not meant to be extended, and the keyword is gone for
 *        the same one reason it is gone on ExAppService: PHPUnit cannot create
 *        a test double of a final class, and both callers take this class by
 *        its concrete type. Without a double, "the provider hands its own
 *        constants down and renders what comes back" could not be asserted at
 *        all. The annotation is what static analysis and a reader go by;
 *        nothing in this repository extends this class, and nothing should.
 */
class SearchService {
	/**
	 * The deepest paging offset the container accepts, mirrored here so that a
	 * cursor beyond it ends the run with a reason of its own instead of with a
	 * refused request.
	 *
	 * The number is SEARCH_LIMIT_MAX times SEARCH_OVERFETCH times SEARCH_ROUNDS,
	 * so 100 * 4 * 3 = 1200, and it is a mirror of
	 * backend/src/findling/config.py and not a decision of this file. What keeps
	 * the two equal is backend/tests/test_search_limits_lockstep.py, which reads
	 * both sides as text and goes red when either one moves. Raising the
	 * container constant is deliberately not part of this phase: it is a
	 * security ceiling with an argument of its own, and paging past it is a
	 * paging problem rather than a limit problem.
	 *
	 * What a cursor past this line means for the user is one sentence and never
	 * an error: there are more hits, and narrowing the search is how to reach
	 * them.
	 */
	public const MAX_CONTAINER_OFFSET = 1200;

	/**
	 * Ceilings in characters for the two fields that come out of the file
	 * system. A file name from an external storage is not more trustworthy than
	 * a container answer.
	 */
	private const MAX_TITLE_LENGTH = 255;
	private const MAX_PATH_LENGTH = 255;

	/**
	 * The same ceiling for the third field of a hit (T-09-03). A mime type is
	 * written by the file cache and is short by every definition, so this is
	 * defence in depth and nothing else; unlike the two above it never drops a
	 * hit, because a hit whose type could not be cleaned is still a hit and the
	 * caller can render it without an icon.
	 */
	private const MAX_MIME_LENGTH = 255;

	/**
	 * The monotonic clock of a run, in nanoseconds, as a callable.
	 *
	 * @var \Closure(): float
	 */
	private \Closure $clock;

	public function __construct(
		private ExAppService $exApp,
		private IRootFolder $rootFolder,
		private IUserMountCache $mountCache,
		private IFileAccess $fileAccess,
		private LoggerInterface $logger,
		?\Closure $clock = null,
	) {
		$this->clock = $clock ?? static fn (): float => (float)hrtime(true);
	}

	/**
	 * One run: ask, decide, and only then fetch the text of the survivors.
	 *
	 * @param IUser $user whose folder answers the permission question
	 * @param string $term the search term, already trimmed by the caller
	 * @param bool $titleOnly file name instead of content
	 * @param int $startCursor the container offset this run continues from
	 * @param SearchCaps $caps every ceiling of this run, written out by the
	 *                         caller
	 */
	public function run(IUser $user, string $term, bool $titleOnly, int $startCursor, SearchCaps $caps): SearchOutcome {
		$deadline = ($this->clock)() + $caps->budgetSeconds * 1_000_000_000.0;
		$uid = $user->getUID();
		$pageSize = max(1, $caps->pageSize);

		// D-11: the two halves have to agree on their major and minor, and when
		// the last answer of the container said otherwise this run stays empty.
		// Same shape as a missing backend one screen below, and for a sharper
		// reason: a protocol break is the one case in which a hit would be a
		// guess dressed up as a finding, because neither half can say what the
		// other one meant by its answer. So the run costs its result and says
		// so in the log, the admin page names the state with both version
		// numbers, and nothing here throws: a mismatch between two installed
		// apps is an operating state and never an error of the search.
		//
		// No round trip is spent on the question. What is read is the version
		// the container reported the last time anything asked it, which is what
		// the settings page does whenever it is open; see
		// ExAppService::KEY_BACKEND_VERSION for what follows from that.
		$drift = $this->exApp->driftOnRecord();
		if ($drift !== null) {
			// Both numbers in the line, because "the versions differ" without
			// them is a sentence an admin cannot act on. Neither of them is
			// user content: both passed the version pattern of ExAppService,
			// and anything that did not is treated as unknown rather than as
			// drift.
			$this->logger->warning('Findling: the two halves report different versions, answering with no hits', [
				'companion' => $drift['companion'],
				'backend' => $drift['container'],
			]);

			return $this->nothing($startCursor, SearchOutcome::FAILURE_VERSION_DRIFT);
		}

		try {
			$userFolder = $this->rootFolder->getUserFolder($uid);
		} catch (\Throwable $e) {
			// Every failure is caught on purpose. getUserFolder() signals a
			// missing user with a class from the private namespace of the
			// server and a missing home directory with a different one again;
			// both mean the same thing here, and neither may reach a caller as
			// an exception. Without a home folder no permission decision is
			// possible, and handing out unchecked hits instead would be the
			// actual bug.
			$this->logger->warning('Findling: no home folder for this user, dropping every hit', ['exception' => $e]);

			return $this->nothing($startCursor, SearchOutcome::FAILURE_NO_HOME_FOLDER);
		}

		$storageIds = $this->storageIdsOfUser($user);
		$recheckBudget = min($caps->recheckAbsolute, $pageSize * $caps->recheckPerHit);
		$rechecks = 0;
		$offset = max(0, $startCursor);
		$exhausted = true;
		$degraded = false;
		$silent = false;
		$ceilingReached = false;
		/** @var list<ApprovedHit> $approved */
		$approved = [];

		for ($round = 0; $round < $caps->maxRounds; $round++) {
			if (count($approved) >= $pageSize || $rechecks >= $recheckBudget || ($this->clock)() >= $deadline) {
				break;
			}

			if ($offset > self::MAX_CONTAINER_OFFSET) {
				// The paging ceiling, checked before the call and not after the
				// refusal. The container answers a deeper offset with a 422,
				// which arrives here as nothing at all and is indistinguishable
				// from a backend that is down; reporting that would be a false
				// statement about the state of the server.
				$ceilingReached = true;
				$exhausted = true;
				break;
			}

			// Fetching more than the recheck budget could ever examine buys
			// nothing (perf audit M4): the overfetch is capped at what is left
			// of the budget plus one display page for the candidates that cost
			// no recheck. The remaining wall clock travels with the call, so
			// the request timeout can never overdraw the deadline (perf H5),
			// and the per call ceiling of this caller travels with it as well.
			$fetchLimit = min($pageSize * $caps->overfetch, $recheckBudget - $rechecks + $pageSize);
			$page = $this->exApp->searchCandidates(
				$uid,
				$term,
				$fetchLimit,
				$offset,
				$titleOnly,
				$this->secondsLeft($deadline),
				$caps->requestCeilingSeconds,
			);
			if ($page === null) {
				$silent = true;
				break;
			}

			if ($page['degraded']) {
				// The backend answered from a reduced state, for instance while
				// the index is still being built. Worth a line, not worth
				// hiding the hits it did find.
				$degraded = true;
				$this->logger->debug('Findling: backend answered in a degraded state');
			}

			$candidates = $page['candidates'];
			if ($candidates === []) {
				// An empty page is only the end when the backend says so. The
				// cheap reduction over there can empty a page whose successors
				// still hold this user's hits, and breaking here would silently
				// swallow every hit behind it; the round counter above bounds
				// how often this is retried.
				$exhausted = !$page['hasMore'];
				if ($exhausted) {
					break;
				}
				$offset = $page['nextOffset'];
				continue;
			}

			$keptIds = $this->reduceIds($candidates, $storageIds);

			// The one and only permission decision of this product. A candidate
			// becomes a hit when this user's own folder resolves its file id to
			// a file, and it is dropped otherwise: never visible, no longer
			// visible, moved into the trash and deleted are deliberately the
			// same outcome, so a hit cannot be used to probe for files this
			// user is not allowed to see.
			//
			// The two counters above this loop cap how many candidates are
			// examined, never whether a displayed one was. A hit that reaches
			// the screen without having passed this line does not exist.
			//
			// $consumed counts the candidates this loop has decided about, and
			// only those. When a budget ends the page early, the cursor resumes
			// exactly behind the last decided candidate, so the better ranked
			// remainder of the page shows up on the next page instead of
			// vanishing between two cursors.
			$consumed = 0;
			$stopped = false;
			foreach ($candidates as $candidate) {
				if (count($approved) >= $pageSize) {
					$stopped = true;
					break;
				}

				if ($candidate['fileId'] <= 0) {
					// The diagnostic path of phase 1. There is no file behind
					// this id, so there is nothing to resolve: the text was
					// composed inside the container out of host name,
					// timestamp and the user id of the signed header and
					// carries no user content. The proxy accepts it under one
					// exact title and under no other.
					$consumed++;
					$approved[] = new ApprovedHit(
						0,
						$candidate['title'] ?? '',
						$candidate['snippet'] ?? '',
						'',
					);
					continue;
				}

				if ($keptIds !== null && !isset($keptIds[$candidate['fileId']])) {
					// Decided, not skipped: the file lives on a storage this
					// user has no mount on, so the recheck could only repeat
					// the verdict at a higher price.
					$consumed++;
					continue;
				}

				if ($rechecks >= $recheckBudget) {
					$stopped = true;
					break;
				}

				$rechecks++;
				$consumed++;
				$node = $userFolder->getFirstNodeById($candidate['fileId']);
				if (!$node instanceof File) {
					continue;
				}

				// The stricter question, asked right after the type check
				// (security audit L5). Reaching a node is not the same as being
				// allowed to read it, and a hit for a document whose content
				// the user may not open is the one outcome this class exists to
				// prevent. It belongs here rather than anywhere further down:
				// two lines later a title and a path of that node would already
				// have been read, and one call later a snippet of its content
				// would exist.
				if (!$node->isReadable()) {
					continue;
				}

				$title = PlainText::bounded($node->getName(), self::MAX_TITLE_LENGTH);
				$path = PlainText::bounded(
					ltrim((string)$userFolder->getRelativePath($node->getPath()), '/'),
					self::MAX_PATH_LENGTH,
				);
				if ($title === null || $path === null) {
					continue;
				}

				// Title, path and type come out of the confirmed node, never
				// out of the container answer. A confused or compromised
				// backend can otherwise put the name of a foreign file in front
				// of the user.
				$approved[] = new ApprovedHit(
					$candidate['fileId'],
					$title,
					$path,
					PlainText::bounded($node->getMimetype(), self::MAX_MIME_LENGTH) ?? '',
				);
			}

			if ($stopped) {
				$offset += $consumed;
				$exhausted = false;
				break;
			}

			$offset = $page['nextOffset'];
			$exhausted = !$page['hasMore'];
			if ($exhausted) {
				break;
			}
		}

		if ($approved === []) {
			// A run that collected nothing and was answered with nothing is the
			// one case in which the silence is worth reporting. With hits on
			// the table it is not: an incomplete list beats an error message
			// printed over hits the user can see.
			$failure = $ceilingReached
				? SearchOutcome::FAILURE_OFFSET_CEILING
				: ($silent ? SearchOutcome::FAILURE_BACKEND_SILENT : null);

			return new SearchOutcome([], [], $offset, !$exhausted && !$ceilingReached, $degraded, $failure);
		}

		// Only now, and only for the survivors. If the budget is used up the
		// caller falls back to the path of the hit instead: a hit without an
		// excerpt beats no hit at all.
		$fileIds = [];
		foreach ($approved as $hit) {
			if ($hit->fileId > 0) {
				$fileIds[] = $hit->fileId;
			}
		}

		$excerpts = $fileIds !== []
			? $this->exApp->snippets(
				$uid,
				$term,
				$fileIds,
				$titleOnly,
				$this->secondsLeft($deadline),
				$caps->requestCeilingSeconds,
			)
			: [];

		return new SearchOutcome(
			$approved,
			$excerpts,
			$offset,
			!$exhausted && !$ceilingReached,
			$degraded,
			$ceilingReached ? SearchOutcome::FAILURE_OFFSET_CEILING : null,
		);
	}

	/**
	 * A run that never got as far as asking, with the reason why.
	 *
	 * The cursor travels back unchanged: a run that asked nothing has moved
	 * nothing, and a caller that retries later starts where it meant to start.
	 */
	private function nothing(int $cursor, string $failure): SearchOutcome {
		return new SearchOutcome([], [], max(0, $cursor), false, false, $failure);
	}

	/**
	 * The cheap reduction that runs before the first node is resolved.
	 *
	 * Two queries instead of one per candidate: the mounts of this user were
	 * fetched once for the whole run, and the cache entries of a whole page of
	 * candidates are fetched in a single call. Whatever lives on a storage this
	 * user has no mount on cannot be theirs, and is dropped before it can cost
	 * a resolution.
	 *
	 * This is a reduction and not a boundary, and the difference matters. It is
	 * an over-approximation: a storage can carry files of a mount this user
	 * does not have, and a team folder with per folder permissions is not
	 * resolved here at all. Everything it lets through is still decided by the
	 * recheck.
	 *
	 * Null and an empty array are two different answers. Null means the
	 * reduction cannot decide anything, so every candidate goes to the capped
	 * recheck; the caps and the recheck are both still in force, so falling
	 * back is safe. An array is a verdict per positive file id: present means
	 * "worth a recheck", absent means "cannot be this user's file".
	 *
	 * @param list<array{fileId:int,title?:string,snippet?:string}> $candidates
	 * @param array<int,true> $storageIds
	 * @return array<int,true>|null
	 */
	private function reduceIds(array $candidates, array $storageIds): ?array {
		$fileIds = [];
		foreach ($candidates as $candidate) {
			if ($candidate['fileId'] > 0) {
				$fileIds[] = $candidate['fileId'];
			}
		}

		if ($fileIds === [] || $storageIds === []) {
			return null;
		}

		try {
			$entries = $this->fileAccess->getByFileIds($fileIds);
		} catch (\Throwable $e) {
			$this->logger->debug('Findling: bulk cache lookup failed, falling back to the capped recheck', ['exception' => $e]);
			return null;
		}

		$kept = [];
		foreach ($fileIds as $fileId) {
			$entry = $entries[$fileId] ?? null;
			if ($entry !== null && isset($storageIds[$entry->getStorageId()])) {
				$kept[$fileId] = true;
			}
		}

		return $kept;
	}

	/**
	 * The numeric storage ids this user has a mount on, fetched once per run
	 * and keyed by id for the lookup in the reduction. An empty map means the
	 * reduction is skipped, not that the user sees nothing.
	 *
	 * @return array<int,true>
	 */
	private function storageIdsOfUser(IUser $user): array {
		try {
			$mounts = $this->mountCache->getMountsForUser($user);
		} catch (\Throwable $e) {
			$this->logger->debug('Findling: mount list unavailable, skipping the cheap reduction', ['exception' => $e]);
			return [];
		}

		$storageIds = [];
		foreach ($mounts as $mount) {
			$storageIds[$mount->getStorageId()] = true;
		}

		return $storageIds;
	}

	/**
	 * What is left of the wall clock, in seconds. Negative once the deadline
	 * has passed, which the callee reads as "do not call at all".
	 */
	private function secondsLeft(int|float $deadline): float {
		return ((float)$deadline - ($this->clock)()) / 1_000_000_000.0;
	}
}
