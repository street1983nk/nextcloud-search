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
 * Three properties carry this class. The first one is that a claim is a
 * conditional update and nothing else: candidates are read without any lock,
 * and then the batch is claimed with one update that repeats the free condition
 * in its WHERE clause. Only rows the statement actually affected were won, and
 * the claim token is how they are read back. Two collectors asking at the same
 * time therefore read the same candidates and still never get the same row, and
 * none of that needs a row locking clause of a specific dialect.
 *
 * The second one is that a claim expires. A container that is killed hard holds
 * its rows for LOCK_TIMEOUT and no longer, which is why that value is small.
 *
 * The third one is that an acknowledgement only deletes what did not change in
 * the meantime. A file that changes while its row is claimed marks the row
 * dirty instead of unlocking it, and the acknowledgement of the stale bytes
 * turns the mark into a fresh, free row.
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
		// Two attempts, because the conflict branch can find the row already
		// deleted by a concurrent acknowledgement, in which case the insert is
		// simply right again. A third collision within one call is not a race
		// any more, it is a defect worth an exception.
		for ($attempt = 0; $attempt < 2; $attempt++) {
			$insert = $this->db->getQueryBuilder();
			$insert->insert(self::TABLE_NAME)
				->values([
					'file_id' => $insert->createNamedParameter($fileId, IQueryBuilder::PARAM_INT),
					'storage_id' => $insert->createNamedParameter($storageId, IQueryBuilder::PARAM_INT),
					'root_id' => $insert->createNamedParameter($rootId, IQueryBuilder::PARAM_INT),
					'is_update' => $insert->createNamedParameter($isUpdate, IQueryBuilder::PARAM_BOOL),
					'size' => $insert->createNamedParameter($size, IQueryBuilder::PARAM_INT),
					'locked_at' => $insert->createNamedParameter($this->freeMark(), IQueryBuilder::PARAM_DATE),
				]);

			try {
				$insert->executeStatement();
				return;
			} catch (DbException $e) {
				if ($e->getReason() !== DbException::REASON_UNIQUE_CONSTRAINT_VIOLATION) {
					throw $e;
				}
			}

			if ($this->refreshExisting($fileId, $size, $isUpdate)) {
				return;
			}
		}

		throw new \RuntimeException('the queue row for this file keeps appearing and disappearing');
	}

	/**
	 * The conflict branch of enqueue: the row exists, so this file is queued
	 * again rather than twice.
	 *
	 * Which of the two updates applies is decided by the database, not by a
	 * read: a free row (or one whose claim expired) is refreshed and stays
	 * free, retries deliberately untouched so a row that keeps coming back can
	 * still reach its end state. A row that is claimed right now keeps its
	 * claim and is marked dirty instead. Clearing the lock here was the audit's
	 * H4: the acknowledgement of the old bytes then deleted the row, and the
	 * new version silently vanished from the queue. The dirty mark makes the
	 * acknowledgement requeue it, see acknowledge().
	 *
	 * @return bool false when the row vanished before either update could hit it
	 */
	private function refreshExisting(int $fileId, int $size, bool $isUpdate): bool {
		$cutoff = $this->lockCutoff($this->now());

		$free = $this->db->getQueryBuilder();
		$free->update(self::TABLE_NAME)
			->set('is_update', $free->createNamedParameter($isUpdate, IQueryBuilder::PARAM_BOOL))
			->set('size', $free->createNamedParameter($size, IQueryBuilder::PARAM_INT))
			->set('locked_at', $free->createNamedParameter($this->freeMark(), IQueryBuilder::PARAM_DATE))
			->set('dirty', $free->createNamedParameter(false, IQueryBuilder::PARAM_BOOL))
			->where($free->expr()->eq('file_id', $free->createNamedParameter($fileId, IQueryBuilder::PARAM_INT)))
			->andWhere($this->freeRowCondition($free, $cutoff));
		if ($free->executeStatement() >= 1) {
			return true;
		}

		$claimed = $this->db->getQueryBuilder();
		$claimed->update(self::TABLE_NAME)
			->set('is_update', $claimed->createNamedParameter($isUpdate, IQueryBuilder::PARAM_BOOL))
			->set('size', $claimed->createNamedParameter($size, IQueryBuilder::PARAM_INT))
			->set('dirty', $claimed->createNamedParameter(true, IQueryBuilder::PARAM_BOOL))
			->where($claimed->expr()->eq('file_id', $claimed->createNamedParameter($fileId, IQueryBuilder::PARAM_INT)));

		return $claimed->executeStatement() >= 1;
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
		$candidates->select('id', 'size')
			->from(self::TABLE_NAME)
			->where($this->freeRowCondition($candidates, $cutoff))
			->orderBy('id', 'ASC')
			->setMaxResults($limit);

		// The byte budget is decided on the candidate list, the ownership is
		// decided by the database below. A candidate is only a guess about a
		// row another collector may take in the meantime.
		$wanted = [];
		$bytes = 0;
		$result = $candidates->executeQuery();
		while (($row = $result->fetch()) !== false) {
			$size = is_numeric($row['size'] ?? null) ? (int)$row['size'] : 0;
			if ($wanted !== [] && ($bytes + $size) > $maxBytes) {
				break;
			}
			$bytes += $size;
			$wanted[] = (int)$row['id'];
		}
		$result->closeCursor();

		if ($wanted === []) {
			return [];
		}

		// One conditional update claims the whole band (the per-row version was
		// 34 round trips per batch, perf audit H4). The free condition in the
		// WHERE clause is still what decides ownership: a competitor that got
		// a row first leaves it out of the affected set. The token is what
		// makes the winners readable afterwards, because two collectors
		// claiming within the same second are indistinguishable by locked_at.
		//
		// Handing a row out is the attempt, so retries is counted here, in the
		// database: read-modify-write loses increments the moment two
		// collectors work at the same time, which is the normal case. The
		// identifier is unquoted because it is a reserved word in none of the
		// three dialects, and quoting it correctly would be the one thing that
		// differs between them. The claim also clears dirty: whatever the file
		// looked like before this moment is exactly what this claim is going
		// to read, so only a change AFTER now makes the row dirty again.
		$token = bin2hex(random_bytes(16));
		$claim = $this->db->getQueryBuilder();
		$claim->update(self::TABLE_NAME)
			->set('locked_at', $claim->createNamedParameter($now, IQueryBuilder::PARAM_DATE))
			->set('claim_token', $claim->createNamedParameter($token))
			->set('dirty', $claim->createNamedParameter(false, IQueryBuilder::PARAM_BOOL))
			->set('retries', $claim->createFunction('retries + 1'))
			->where($claim->expr()->in('id', $claim->createNamedParameter($wanted, IQueryBuilder::PARAM_INT_ARRAY)))
			->andWhere($this->freeRowCondition($claim, $cutoff));
		if ($claim->executeStatement() === 0) {
			return [];
		}

		$won = $this->db->getQueryBuilder();
		$won->select('*')
			->from(self::TABLE_NAME)
			->where($won->expr()->eq('claim_token', $won->createNamedParameter($token)))
			->orderBy('id', 'ASC');

		return $this->findEntities($won);
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
	 * The exception is a row whose file changed while it was being processed.
	 * The claim cleared its dirty mark, so a set mark can only mean "the bytes
	 * this acknowledgement is about are already stale". Deleting it would carry
	 * the old text into the index for good (bug audit H4); instead the mark is
	 * traded for a fresh, free row and the next collector reads the new bytes.
	 *
	 * @param int[] $ids
	 * @return int number of rows that were acknowledged away
	 */
	public function acknowledge(array $ids): int {
		if ($ids === []) {
			return 0;
		}

		$deleted = 0;
		foreach (array_chunk($ids, self::DELETE_BAND) as $band) {
			// The delete runs first. The other way round the requeue would
			// clear the dirty mark and the delete would then remove exactly
			// the rows the requeue had just saved.
			$qb = $this->db->getQueryBuilder();
			$qb->delete(self::TABLE_NAME)
				->where($qb->expr()->in('id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)))
				->andWhere($qb->expr()->eq('dirty', $qb->createNamedParameter(false, IQueryBuilder::PARAM_BOOL)));
			$deleted += $qb->executeStatement();

			$requeue = $this->db->getQueryBuilder();
			$requeue->update(self::TABLE_NAME)
				->set('locked_at', $requeue->createNamedParameter($this->freeMark(), IQueryBuilder::PARAM_DATE))
				->set('dirty', $requeue->createNamedParameter(false, IQueryBuilder::PARAM_BOOL))
				->where($requeue->expr()->in('id', $requeue->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)))
				->andWhere($requeue->expr()->eq('dirty', $requeue->createNamedParameter(true, IQueryBuilder::PARAM_BOOL)));
			$requeue->executeStatement();
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
				->set('locked_at', $qb->createNamedParameter($this->freeMark(), IQueryBuilder::PARAM_DATE))
				->where($qb->expr()->in('id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));
			$released += $qb->executeStatement();
		}

		return $released;
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
			->where($qb->expr()->gt('locked_at', $qb->createNamedParameter($cutoff, IQueryBuilder::PARAM_DATE)));

		return $this->countFrom($qb);
	}

	/**
	 * Free means marked with the epoch or claimed too long ago. One expression,
	 * used by the candidate query, by the claim, by the conflict refresh and by
	 * the counter, so they can never drift apart.
	 *
	 * A single closed range on purpose: the free mark used to be NULL, and the
	 * resulting OR condition was served by no index, so every claim walked the
	 * primary key (perf audit H3). The migration rewrote NULL to the epoch and
	 * nothing writes NULL since, which is what lets findling_q_free
	 * (locked_at, id) answer "the free rows, oldest first" directly.
	 */
	private function freeRowCondition(IQueryBuilder $qb, \DateTime $cutoff): string {
		return (string)$qb->expr()->lte('locked_at', $qb->createNamedParameter($cutoff, IQueryBuilder::PARAM_DATE));
	}

	/**
	 * The value that marks a row as free. The epoch rather than NULL, because a
	 * closed range is what the free index answers; and it is guaranteed to lie
	 * before every cutoff a clock can produce.
	 */
	private function freeMark(): \DateTime {
		return new \DateTime('@0');
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
