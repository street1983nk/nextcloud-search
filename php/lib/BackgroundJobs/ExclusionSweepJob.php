<?php

declare(strict_types=1);

namespace OCA\Findling\BackgroundJobs;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJobList;
use OCP\BackgroundJob\QueuedJob;
use OCP\IAppConfig;
use OCP\IDBConnection;
use Psr\Log\LoggerInterface;

/**
 * Takes the files a new exclusion pattern covers out of the index, in bands
 * (way A of plan 33-04, EXCL-02).
 *
 * A prefix names a folder, so its clearing is one SubtreeExpandJob per mount the
 * folder resolves in. A pattern names no folder: ``*.key`` is a Keynote bundle
 * in any folder of any home, and there is no cheap way from the text of a
 * pattern to the folder ids it covers (a LIKE on the file cache with a leading
 * wildcard is a table scan per storage, and the collation differs per database
 * in exactly the question of upper and lower case). So this job walks every
 * file of every mount the crawl walks, in the order of StorageService::getMounts()
 * and with the same enumeration, and asks the rule of today for each of them
 * through ExclusionService::isExcluded on the path out of mountRelativePath(),
 * the fifth call site of that one helper (gate D in
 * backend/tests/test_exclusion_path_space.py).
 *
 * A file under a rule gets one queue row of kind delete, which the poller turns
 * into _forget (document, permission rows, tombstone, each of them idempotent),
 * and loses its verdict row in findling_file_state (finding B2): the tiles and
 * the error list would otherwise keep counting a file the rule has taken out of
 * the index. The cost is one walk over all indexable files of the instance per
 * change of the pattern set; for issue #22 that is 266 thousand delete rows,
 * and a delete row for a file the container never indexed costs one idempotent
 * forget and nothing else. Files under a prefix are cleared again on the way,
 * which is the same idempotent write.
 *
 * The argument carries a fingerprint of the pattern set the run was planned for
 * (PE-10), and every run compares it first. ExclusionService::savePatterns()
 * removes and replans this job on every change of the set, a pattern taken back
 * as much as a pattern added; a run that was already under way, or an entry the
 * removal did not catch, then finds a fingerprint that is no longer in force and
 * ends without a successor. A pattern that was taken back therefore clears
 * nothing more, and the newer set has its own run from the start.
 *
 * The net under this job is way C (plan 33-03): the reconcile clears every file
 * the container knows and a rule of today covers, which catches what this job
 * cannot see, a mount that appears later or a rule written with occ past the
 * form. A run that fails ends the chain, being a QueuedJob, and the net is what
 * finishes the clearing then.
 *
 * Nothing here logs a path, a pattern, a file name or the fingerprint. Counters,
 * the storage id and the cursor are enough to follow a sweep (T-33-14).
 */
final class ExclusionSweepJob extends QueuedJob {
	/**
	 * Files looked at per run, across mounts. A thousand, half a crawl slice:
	 * every file costs one comparison against every rule, and a hit costs a
	 * queue write, so a run of a bundle heavy instance is a thousand inserts at
	 * most. Small enough that the wall clock ceiling below is the usual end of a
	 * run on a slow disk and not the band.
	 */
	public const BATCH_SIZE = 1000;

	/**
	 * Wall clock ceiling of one run, the same as the crawl and the subtree
	 * expansion: a cron slot is shared with every other job of the instance,
	 * and a sweep that holds it for minutes is a denial of service against the
	 * rest of the server (T-33-13).
	 */
	public const MAX_SECONDS = 30;

	/**
	 * Seconds until the next run of the same sweep. Small, so that the files of a
	 * new pattern leave the index while the admin still looks at the page;
	 * nonzero, so that the sweep does not take consecutive cron slots for itself.
	 */
	public const INTERVAL = 5;

	/**
	 * Writes per transaction, the measurement of the crawl (perf audit H2): one
	 * commit per file made the commit the main cost on slow disks, and one
	 * transaction for a whole run would block the single writer of a SQLite
	 * instance for its entire length.
	 */
	private const TX_BAND = 250;

	public function __construct(
		ITimeFactory $time,
		private IJobList $jobList,
		private StorageService $storageService,
		private ExclusionService $exclusionService,
		private QueueService $queueService,
		private FileStateService $fileStateService,
		private IAppConfig $appConfig,
		private IDBConnection $db,
		private LoggerInterface $logger,
	) {
		parent::__construct($time);
	}

	/**
	 * The argument of the first run of a sweep: before the first mount, with the
	 * fingerprint of the set it was planned for. One place for the shape, so the
	 * planner in ExclusionService and the successor below cannot disagree.
	 *
	 * @return array{storage: int, root: int, cursor: int, fingerprint: string}
	 */
	public static function startArgument(string $fingerprint): array {
		return self::argument(0, 0, 0, $fingerprint);
	}

	/**
	 * @return array{storage: int, root: int, cursor: int, fingerprint: string}
	 */
	private static function argument(int $storage, int $root, int $cursor, string $fingerprint): array {
		return [
			'storage' => $storage,
			'root' => $root,
			'cursor' => $cursor,
			'fingerprint' => $fingerprint,
		];
	}

	protected function run($argument): void {
		$storage = (int)($argument['storage'] ?? 0);
		$root = (int)($argument['root'] ?? 0);
		$cursor = (int)($argument['cursor'] ?? 0);
		$fingerprint = (string)($argument['fingerprint'] ?? '');

		// First, before a single mount is read: is the set this run was planned
		// for still the set in force? A newer set has planned its own run, and a
		// pattern that was taken back must not clear anything more (PE-10).
		if ($fingerprint === '' || !hash_equals($this->exclusionService->patternFingerprint(), $fingerprint)) {
			$this->logger->debug('Findling: ended a sweep planned for an earlier set of exclusion patterns', [
				'storage' => $storage,
				'cursor' => $cursor,
			]);
			return;
		}

		if (!$this->exclusionService->hasRules()) {
			return;
		}

		$deadline = $this->time->getTime() + self::MAX_SECONDS;
		$budget = self::BATCH_SIZE;
		$seen = 0;
		$cleared = 0;
		$next = null;

		foreach ($this->mountsFrom($storage, $root) as $mount) {
			$storageId = $mount['storage_id'];
			$overriddenRoot = $mount['overridden_root'];
			$from = ($storageId === $storage && $overriddenRoot === $root) ? $cursor : 0;

			$walked = $this->sweepMount($mount, $from, $budget, $deadline);
			$seen += $walked['seen'];
			$cleared += $walked['cleared'];
			$budget -= $walked['seen'];

			if ($walked['stopped'] || $walked['seen'] >= $walked['asked']) {
				// The wall clock ran out, or the band was full and the mount may
				// hold more behind the cursor: the successor starts exactly here.
				$next = self::argument($storageId, $overriddenRoot, $walked['cursor'], $fingerprint);
				break;
			}

			// Fewer files than asked for: nothing is left behind the cursor of
			// this mount, and the rest of the budget goes to the next one.
		}

		if ($seen > 0) {
			$this->appConfig->setValueInt(Application::APP_ID, SchedulerJob::LAST_JOB_RUN, $this->time->getTime());
		}

		$this->logger->debug('Findling: swept a band for the exclusion patterns', [
			'storage' => $next['storage'] ?? 0,
			'cursor' => $next['cursor'] ?? 0,
			'seen' => $seen,
			'cleared' => $cleared,
		]);

		if ($next === null) {
			// Every mount is behind the cursor: the sweep is done and gets no
			// successor, the only way the chain ends besides the fingerprint.
			return;
		}

		$this->jobList->scheduleAfter(self::class, $this->time->getTime() + self::INTERVAL, $next);
	}

	/**
	 * The mounts of the crawl, in a fixed order, from the given one on.
	 *
	 * Ordered by storage id and then by the overridden root, because one storage
	 * carries several mounts (every Team Folder of an instance lives on one
	 * storage), and the cursor is a file id within one mount. A mount that
	 * vanished between two runs is not an error: the walk goes on with the next
	 * one in the order, from its start.
	 *
	 * @return list<array{storage_id: int, root_id: int, overridden_root: int}>
	 */
	private function mountsFrom(int $storage, int $root): array {
		$mounts = [];
		foreach ($this->storageService->getMounts() as $mount) {
			$entry = [
				'storage_id' => (int)$mount['storage_id'],
				'root_id' => (int)$mount['root_id'],
				'overridden_root' => (int)$mount['overridden_root'],
			];
			if ($entry['storage_id'] <= 0 || $entry['overridden_root'] <= 0) {
				continue;
			}
			if ($entry['storage_id'] < $storage || ($entry['storage_id'] === $storage && $entry['overridden_root'] < $root)) {
				continue;
			}
			$mounts[] = $entry;
		}

		usort(
			$mounts,
			static fn (array $a, array $b): int => [$a['storage_id'], $a['overridden_root']] <=> [$b['storage_id'], $b['overridden_root']],
		);

		return $mounts;
	}

	/**
	 * One band of one mount: every file behind the cursor, at most $budget of
	 * them, until the wall clock says stop.
	 *
	 * @param array{storage_id: int, root_id: int, overridden_root: int} $mount
	 * @return array{seen: int, asked: int, cleared: int, cursor: int, stopped: bool}
	 */
	private function sweepMount(array $mount, int $cursor, int $budget, int $deadline): array {
		$storageId = $mount['storage_id'];
		$mountRoot = $this->storageService->mountRootPath($storageId, $mount['overridden_root']);

		$seen = 0;
		$cleared = 0;
		$stopped = false;
		$hits = [];

		foreach ($this->storageService->getFilesInMount($storageId, $mount['overridden_root'], $cursor, $budget) as $entry) {
			// Asked before the entry is handled, so a run cannot overshoot its
			// ceiling by one more write (bug audit M4 of the crawl).
			if ($this->time->getTime() >= $deadline) {
				$stopped = true;
				break;
			}

			$cursor = max($cursor, (int)$entry->getId());
			$seen++;

			if ($this->exclusionService->isExcluded(
				$this->exclusionService->mountRelativePath($entry->getPath(), $mountRoot),
			)) {
				$hits[] = (int)$entry->getId();
				if (count($hits) >= self::TX_BAND) {
					$cleared += $this->clear($hits, $storageId, $mount['root_id']);
					$hits = [];
				}
			}
		}

		$cleared += $this->clear($hits, $storageId, $mount['root_id']);

		return ['seen' => $seen, 'asked' => $budget, 'cleared' => $cleared, 'cursor' => $cursor, 'stopped' => $stopped];
	}

	/**
	 * One transaction band: a delete row per file, then their verdict rows gone.
	 *
	 * Size zero, because a delete moves no bytes and must not take a share of
	 * the byte budget of a claim; idempotent by the unique index on file_id, and
	 * KIND_RANK keeps a more expensive kind already waiting, exactly as in
	 * SubtreeExpandJob. Both writes in one transaction, so a band is either
	 * queued and forgotten or neither.
	 *
	 * @param list<int> $fileIds
	 */
	private function clear(array $fileIds, int $storageId, int $rootId): int {
		if ($fileIds === []) {
			return 0;
		}

		$this->db->beginTransaction();
		try {
			foreach ($fileIds as $fileId) {
				$this->queueService->enqueueFile($fileId, $storageId, $rootId, 0, true, QueueMapper::KIND_DELETE);
			}
			$this->fileStateService->forgetVerdicts($fileIds);
			$this->db->commit();
		} catch (\Throwable $e) {
			$this->db->rollBack();
			throw $e;
		}

		return count($fileIds);
	}
}
