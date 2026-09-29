<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\FileStateService;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\IDBConnection;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

/**
 * The repair of the gone verdicts that issue #14 left behind (D-04).
 *
 * Before 257caac the container judged a file gone as soon as the one reader it
 * had picked could not reach it. For a file in a Team Folder that reader was
 * often somebody without access to that folder, so a file that was perfectly
 * there and readable by its members was written into findling_file_state as
 * skipped(gone) and never indexed. The ACL code of 257caac asks the right
 * readers now, but it only asks for files that reach it, and these do not: they
 * are not in the queue any more, and nothing puts them back.
 *
 * So this migration does, once. Every file with a skipped(gone) verdict is
 * handed back to the content track through QueueMapper::requeueAs, which keeps
 * the precedence of a pending deletion and the dirty mark exactly as every
 * other requeue does, and the verdict itself is deleted in the same
 * transaction. The claim then sorts each file the way it sorts every file: a
 * file that is readable gets indexed, a file that really is gone is judged gone
 * again.
 *
 * The delete is not optional. revokeFailures took back failed verdicts only
 * when this migration was written (review WR-04 of phase 27 widened it to
 * skips later), and this side of the app never writes indexed. A file that is indexed after the requeue would therefore
 * carry skipped(gone) for good, and the status page would count a findable file
 * as one that went. Requeue and delete happen in one transaction per band,
 * because half of it is the worst outcome in either direction: a requeued file
 * whose verdict still says gone, or a deleted verdict for a file nobody
 * requeued.
 *
 * A second run is harmless. After the first one the only skipped(gone) rows are
 * the ones the new code wrote, which are genuine; a replay requeues them once
 * more, and the claim judges them gone again through usersFor() without
 * downloading a byte. On the usual second run, the replay of a failed upgrade
 * right after this one, there is nothing there at all and the step says so.
 *
 * Nothing is asked of the container here. A migration runs inside occ upgrade,
 * with the instance in maintenance mode, without a logged in user, and at a
 * moment when AppAPI may be restarting the container: a proxy request needs a
 * container that answers, so a migration that waits on one can turn an app
 * update into a failed one. The work this step creates is picked up by the
 * container through the normal poller after the update is over. The output is
 * a number and nothing else: no file id, no path, no user name.
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001300Date20260927000000 extends SimpleMigrationStep {
	/**
	 * The band, for the dialects and not for the size of the answer: every
	 * database has a ceiling on bound parameters and they differ. The same
	 * value as QueueMapper::DELETE_BAND, which is private and cannot be
	 * referenced from here.
	 */
	private const BAND = 1000;

	public function __construct(
		private IDBConnection $db,
		private QueueMapper $queueMapper,
	) {
	}

	/**
	 * After the schema, because this touches data and no table.
	 */
	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		$fileIds = $this->goneFileIds();
		if ($fileIds === []) {
			$output->info('no gone verdicts to repair');

			return;
		}

		$total = 0;
		foreach (array_chunk($fileIds, self::BAND) as $band) {
			$this->db->beginTransaction();
			try {
				$this->queueMapper->requeueAs($band, QueueMapper::KIND_CONTENT);

				$qb = $this->db->getQueryBuilder();
				$qb->delete(FileStateService::TABLE_NAME)
					->where($qb->expr()->eq('state', $qb->createNamedParameter('skipped', IQueryBuilder::PARAM_STR)))
					->andWhere($qb->expr()->eq('reason', $qb->createNamedParameter('gone', IQueryBuilder::PARAM_STR)))
					->andWhere($qb->expr()->in('file_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));
				$qb->executeStatement();

				$this->db->commit();
			} catch (\Throwable $e) {
				$this->db->rollBack();
				throw $e;
			}

			$total += count($band);
		}

		$output->info(sprintf('requeued %d files once judged gone', $total));
	}

	/**
	 * Every file carrying skipped(gone), and no other verdict.
	 *
	 * @return list<int>
	 */
	private function goneFileIds(): array {
		$qb = $this->db->getQueryBuilder();
		$qb->select('file_id')
			->from(FileStateService::TABLE_NAME)
			->where($qb->expr()->eq('state', $qb->createNamedParameter('skipped', IQueryBuilder::PARAM_STR)))
			->andWhere($qb->expr()->eq('reason', $qb->createNamedParameter('gone', IQueryBuilder::PARAM_STR)))
			->orderBy('file_id');
		$result = $qb->executeQuery();
		$rows = $result->fetchAll();
		$result->closeCursor();

		$fileIds = [];
		foreach ($rows as $row) {
			$fileId = (int)$row['file_id'];
			if ($fileId > 0) {
				$fileIds[] = $fileId;
			}
		}

		return array_values(array_unique($fileIds));
	}
}
