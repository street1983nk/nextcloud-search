<?php

declare(strict_types=1);

namespace OCA\Findling\Db;

use OCP\AppFramework\Db\QBMapper;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\DB\Exception as DbException;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\IDBConnection;

/**
 * The work stock, and the only place that decides who owns a row.
 *
 * Two properties carry this class. The first one is that a claim is a
 * conditional update and nothing else: candidates are read without any lock,
 * and then every single row is claimed with an update that repeats the free
 * condition in its WHERE clause. Only a statement that reported at least one
 * affected row won the row. Two collectors asking at the same time therefore
 * read the same candidates and still never get the same row, and none of that
 * needs a row locking clause of a specific dialect.
 *
 * The second one is that a claim expires. A container that is killed hard holds
 * its rows for LOCK_TIMEOUT and no longer, which is why that value is small.
 *
 * @template-extends QBMapper<QueueFile>
 */
class QueueMapper extends QBMapper {
	public const TABLE_NAME = 'findling_queue';

	/**
	 * Fifteen minutes, and this number is the whole reason this constant exists.
	 *
	 * The model this queue is built after waits a full day before it hands a
	 * claimed row back, which means the acceptance test "kill the container in
	 * the middle of the first index" looks like a dead instance until the next
	 * day. Fifteen minutes is far above the longest extraction we can produce
	 * without OCR, and OCR in phase 3 raises this value or splits it per kind of
	 * job. A graceful restart does not wait at all, it gives its rows back
	 * through the unlock endpoint.
	 *
	 * It is a named constant because the number standing directly in the query
	 * is the documented warning sign for exactly this defect.
	 */
	public const LOCK_TIMEOUT = 900;

	/**
	 * Acknowledgements arrive in one list and are deleted in bands, so a large
	 * acknowledgement never becomes a single statement with tens of thousands of
	 * bound parameters. Every dialect has a ceiling there, and they differ.
	 */
	private const DELETE_BAND = 1000;

	public function __construct(
		IDBConnection $db,
		private ITimeFactory $timeFactory,
	) {
		parent::__construct($db, self::TABLE_NAME, QueueFile::class);
	}

	/**
	 * Queue a file, or refresh the row that is already there.
	 *
	 * There is no select before this insert on purpose. Two crawl jobs looking
	 * at the same file at the same time would both see nothing and both insert;
	 * the unique index on file_id is what makes that impossible, and the conflict
	 * it raises is caught here and turned into an update of the existing row.
	 * The race is decided by the database, which is the only participant that
	 * can decide it.
	 *
	 * The conflict branch is written out instead of using a single upsert
	 * statement because the public query builder of Nextcloud has no upsert that
	 * is proven to behave the same on SQLite, MariaDB and PostgreSQL. Plan 02-14
	 * verifies the behaviour of this method against a second dialect; should it
	 * fail there, the fix is local to this method and nothing above it changes.
	 */
	public function enqueue(int $fileId, int $storageId, int $rootId, int $size, bool $isUpdate): void {
		$insert = $this->db->getQueryBuilder();
		$insert->insert(self::TABLE_NAME)
			->values([
				'file_id' => $insert->createNamedParameter($fileId, IQueryBuilder::PARAM_INT),
				'storage_id' => $insert->createNamedParameter($storageId, IQueryBuilder::PARAM_INT),
				'root_id' => $insert->createNamedParameter($rootId, IQueryBuilder::PARAM_INT),
				'is_update' => $insert->createNamedParameter($isUpdate, IQueryBuilder::PARAM_BOOL),
				'size' => $insert->createNamedParameter($size, IQueryBuilder::PARAM_INT),
			]);

		try {
			$insert->executeStatement();
			return;
		} catch (DbException $e) {
			if ($e->getReason() !== DbException::REASON_UNIQUE_CONSTRAINT_VIOLATION) {
				throw $e;
			}
		}

		// The row exists, so this file is queued again rather than twice. The
		// lock is cleared because a file that changed has to be processed again
		// even while an older claim of it is still open, and the size is
		// refreshed because the byte budget of the next batch is computed from
		// it. retries is deliberately left alone: a row that keeps coming back
		// through updates must still be able to reach its end state.
		$update = $this->db->getQueryBuilder();
		$update->update(self::TABLE_NAME)
			->set('is_update', $update->createNamedParameter($isUpdate, IQueryBuilder::PARAM_BOOL))
			->set('size', $update->createNamedParameter($size, IQueryBuilder::PARAM_INT))
			->set('locked_at', $update->createNamedParameter(null, IQueryBuilder::PARAM_NULL))
			->where($update->expr()->eq('file_id', $update->createNamedParameter($fileId, IQueryBuilder::PARAM_INT)));
		$update->executeStatement();
	}

	/**
	 * Claim up to $limit rows, but never more than $maxBytes worth of files.
	 *
	 * The byte budget is the second ceiling next to the count, because 32 large
	 * scans are a different amount of memory than 32 invoices. It can never
	 * shrink a batch to nothing though: the first row is always delivered, even
	 * when it alone is over the budget. Otherwise a single oversized file would
	 * sit at the head of the queue and stall the run forever.
	 *
	 * @return QueueFile[] the rows this caller owns, in queue order
	 */
	public function claimBatch(int $limit, int $maxBytes): array {
		$now = $this->now();
		$cutoff = $this->lockCutoff($now);

		$candidates = $this->db->getQueryBuilder();
		$candidates->select('*')
			->from(self::TABLE_NAME)
			->where($this->freeRowCondition($candidates, $cutoff))
			->orderBy('id', 'ASC')
			->addOrderBy('is_update', 'ASC')
			->setMaxResults($limit);

		$claimed = [];
		$bytes = 0;

		foreach ($this->findEntities($candidates) as $row) {
			$size = $row->getSize() ?? 0;
			if ($claimed !== [] && ($bytes + $size) > $maxBytes) {
				break;
			}

			// The row is only ours if the database says so. Everything before
			// this line was a guess about a row that another collector may have
			// taken in the meantime.
			if (!$this->claimRow($row->getId(), $now, $cutoff)) {
				continue;
			}

			$bytes += $size;
			$claimed[] = $row;
		}

		if ($claimed !== []) {
			// Handing a row out is the attempt, so it is counted here and not
			// somewhere in the caller. A row that is handed out and never
			// acknowledged is the case retries exists for.
			$ids = array_map(static fn (QueueFile $row): int => $row->getId(), $claimed);
			$this->bumpRetries($ids);
			foreach ($claimed as $row) {
				$row->setRetries($row->getRetries() + 1);
			}
		}

		return $claimed;
	}

	/**
	 * Rows for the given queue ids, so the acknowledgement path can translate a
	 * queue id into the file id it has to write a state for.
	 *
	 * @param int[] $ids
	 * @return QueueFile[]
	 */
	public function findByIds(array $ids): array {
		if ($ids === []) {
			return [];
		}

		$rows = [];
		foreach (array_chunk($ids, self::DELETE_BAND) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->select('*')
				->from(self::TABLE_NAME)
				->where($qb->expr()->in('id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));
			foreach ($this->findEntities($qb) as $row) {
				$rows[] = $row;
			}
		}

		return $rows;
	}

	/**
	 * Remove acknowledged rows. Deleting is the acknowledgement: a row that is
	 * gone cannot be delivered a second time.
	 *
	 * @param int[] $ids
	 * @return int number of rows that were still there
	 */
	public function acknowledge(array $ids): int {
		if ($ids === []) {
			return 0;
		}

		$deleted = 0;
		foreach (array_chunk($ids, self::DELETE_BAND) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->delete(self::TABLE_NAME)
				->where($qb->expr()->in('id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));
			$deleted += $qb->executeStatement();
		}

		return $deleted;
	}

	/**
	 * Give rows back without processing them. This is the graceful restart: a
	 * container that is asked to stop returns what it holds instead of letting
	 * LOCK_TIMEOUT run out.
	 *
	 * @param int[] $ids
	 * @return int number of rows that were actually released
	 */
	public function unlock(array $ids): int {
		if ($ids === []) {
			return 0;
		}

		$released = 0;
		foreach (array_chunk($ids, self::DELETE_BAND) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->update(self::TABLE_NAME)
				->set('locked_at', $qb->createNamedParameter(null, IQueryBuilder::PARAM_NULL))
				->where($qb->expr()->in('id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));
			$released += $qb->executeStatement();
		}

		return $released;
	}

	/**
	 * @param int[] $ids
	 */
	public function bumpRetries(array $ids): void {
		if ($ids === []) {
			return;
		}

		foreach (array_chunk($ids, self::DELETE_BAND) as $band) {
			$qb = $this->db->getQueryBuilder();
			// Counted in the database, not read, incremented and written back.
			// The read modify write version loses increments the moment two
			// collectors work at the same time, which is the normal case here.
			// The identifier is unquoted because it is a reserved word in none of
			// the three dialects, and quoting it correctly would be the one thing
			// that differs between them.
			$qb->update(self::TABLE_NAME)
				->set('retries', $qb->createFunction('retries + 1'))
				->where($qb->expr()->in('id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));
			$qb->executeStatement();
		}
	}

	/**
	 * Waiting for a collector: never claimed, or claimed by someone who did not
	 * come back in time. Both are the same thing from the outside, which is why
	 * they are one number.
	 */
	public function countScheduled(): int {
		$qb = $this->db->getQueryBuilder();
		$qb->select($qb->func()->count('*', 'rows'))
			->from(self::TABLE_NAME)
			->where($this->freeRowCondition($qb, $this->lockCutoff($this->now())));

		return $this->countFrom($qb);
	}

	/**
	 * Held by a collector right now, with a claim that has not expired.
	 */
	public function countRunning(): int {
		$cutoff = $this->lockCutoff($this->now());

		$qb = $this->db->getQueryBuilder();
		$qb->select($qb->func()->count('*', 'rows'))
			->from(self::TABLE_NAME)
			->where($qb->expr()->isNotNull('locked_at'))
			->andWhere($qb->expr()->gt('locked_at', $qb->createNamedParameter($cutoff, IQueryBuilder::PARAM_DATE)));

		return $this->countFrom($qb);
	}

	/**
	 * The conditional update that is the actual lock.
	 *
	 * The free condition of the candidate query is repeated here in the WHERE
	 * clause. Whatever happened between reading the candidate and this statement
	 * is decided by the database: a competitor that got there first leaves zero
	 * affected rows behind, and this method reports the loss instead of handing
	 * the same file to two collectors.
	 */
	private function claimRow(int $id, \DateTime $now, \DateTime $cutoff): bool {
		$qb = $this->db->getQueryBuilder();
		$qb->update(self::TABLE_NAME)
			->set('locked_at', $qb->createNamedParameter($now, IQueryBuilder::PARAM_DATE))
			->where($qb->expr()->eq('id', $qb->createNamedParameter($id, IQueryBuilder::PARAM_INT)))
			->andWhere($this->freeRowCondition($qb, $cutoff));

		return $qb->executeStatement() >= 1;
	}

	/**
	 * Free means never claimed or claimed too long ago. One expression, used by
	 * the candidate query, by the claim and by the counter, so the three can
	 * never drift apart.
	 */
	private function freeRowCondition(IQueryBuilder $qb, \DateTime $cutoff): string {
		return (string)$qb->expr()->orX(
			$qb->expr()->isNull('locked_at'),
			$qb->expr()->lte('locked_at', $qb->createNamedParameter($cutoff, IQueryBuilder::PARAM_DATE)),
		);
	}

	/**
	 * UTC on purpose. The stored value and the value it is compared against have
	 * to follow the same convention, and a local time zone shifts by an hour
	 * twice a year, which would silently stretch or shorten every open claim
	 * exactly once each time.
	 */
	private function now(): \DateTime {
		return $this->timeFactory->getDateTime('now', new \DateTimeZone('UTC'));
	}

	private function lockCutoff(\DateTime $now): \DateTime {
		$cutoff = clone $now;

		return $cutoff->setTimestamp($now->getTimestamp() - self::LOCK_TIMEOUT);
	}

	private function countFrom(IQueryBuilder $qb): int {
		$result = $qb->executeQuery();
		$count = $result->fetchOne();
		$result->closeCursor();

		return is_numeric($count) ? (int)$count : 0;
	}
}
