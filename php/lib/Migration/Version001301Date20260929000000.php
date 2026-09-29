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
 * The repair of the unreadable verdicts that the second round of issue #14 left
 * behind, the sibling of the gone repair of 1.3.0.
 *
 * Until ReaderContext the claim, the content gateway and the admin lookup set
 * up a member's folder in a request whose active user was somebody else, or
 * nobody. groupfolders builds the mount of a Team Folder as "in share" in that
 * case, and an ACL that grants read without share then hides every node from
 * every member. Such a file was written into findling_file_state as
 * skipped(unreadable) and never indexed, although all of its members may read
 * it. The fix reads as the member now, but only for files that reach the claim,
 * and these do not: they left the queue with their verdict, and nothing puts
 * them back short of a file event or a full crawl.
 *
 * So this migration does, once. Every file with a skipped(unreadable) verdict
 * is handed back to the content track through QueueMapper::requeueAs, which
 * keeps the precedence of a pending deletion and the dirty mark exactly as
 * every other requeue does, and the verdict itself is deleted in the same
 * transaction. The claim then sorts each file the way it sorts every file: a
 * file a member can read gets indexed, a file nobody asked may read is judged
 * unreadable again.
 *
 * The delete is deliberate even though revokeFailures takes back skips since
 * review WR-04 of phase 27. That only happens when the container reports the
 * file as processed; a file that stays unreadable would otherwise keep a
 * verdict that is older than the requeue, and a requeue whose verdict is not
 * cleared leaves the admin page counting the file as skipped while it waits.
 * Requeue and delete happen in one transaction per band, because half of it
 * is the worst outcome in either direction: a requeued file whose verdict still
 * says unreadable, or a deleted verdict for a file nobody requeued.
 *
 * A second run is harmless. After the first one the only skipped(unreadable)
 * rows are the ones the fixed code wrote, which are genuine; a replay requeues
 * them once more and the claim judges them unreadable again without
 * downloading a byte. On the usual second run, the replay of a failed upgrade
 * right after this one, there is nothing there at all and the step says so.
 *
 * Only unreadable. too_large, no_text_layer, gone and every failed verdict are
 * decisions this repair has no business with: the first is a cap, the second
 * the memo of the OCR handover, the third had its own repair in 1.3.0.
 *
 * Nothing is asked of the container here, for the reasons the gone repair
 * gives: a migration runs inside occ upgrade, in maintenance mode, without a
 * logged in user, while AppAPI may be restarting the container. The work this
 * step creates is picked up through the normal poller after the update. The
 * output is a number and nothing else: no file id, no path, no user name.
 *
 * The version 001301 names the release it came with, 1.3.1, and the same file
 * is carried on main so that an instance going from 1.3.0 straight to a later
 * minor runs it too; Nextcloud records a migration by its class name, so an
 * instance that already ran it under 1.3.1 does not run it again.
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001301Date20260929000000 extends SimpleMigrationStep {
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
		$fileIds = $this->unreadableFileIds();
		if ($fileIds === []) {
			$output->info('no unreadable verdicts to repair');

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
					->andWhere($qb->expr()->eq('reason', $qb->createNamedParameter('unreadable', IQueryBuilder::PARAM_STR)))
					->andWhere($qb->expr()->in('file_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));
				$qb->executeStatement();

				$this->db->commit();
			} catch (\Throwable $e) {
				$this->db->rollBack();
				throw $e;
			}

			$total += count($band);
		}

		$output->info(sprintf('requeued %d files once judged unreadable', $total));
	}

	/**
	 * Every file carrying skipped(unreadable), and no other verdict.
	 *
	 * @return list<int>
	 */
	private function unreadableFileIds(): array {
		$qb = $this->db->getQueryBuilder();
		$qb->select('file_id')
			->from(FileStateService::TABLE_NAME)
			->where($qb->expr()->eq('state', $qb->createNamedParameter('skipped', IQueryBuilder::PARAM_STR)))
			->andWhere($qb->expr()->eq('reason', $qb->createNamedParameter('unreadable', IQueryBuilder::PARAM_STR)))
			->orderBy('file_id');
		$result = $qb->executeQuery();

		// Row by row and not fetchAll(): the instance of the report carries
		// about 250 000 such verdicts, and a list of plain integers is a
		// fraction of the memory a list of row arrays takes inside occ upgrade.
		$fileIds = [];
		while (($row = $result->fetch()) !== false) {
			$fileId = (int)$row['file_id'];
			if ($fileId > 0) {
				$fileIds[] = $fileId;
			}
		}
		$result->closeCursor();

		return array_values(array_unique($fileIds));
	}
}
