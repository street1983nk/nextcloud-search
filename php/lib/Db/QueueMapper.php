<?php

declare(strict_types=1);

namespace OCA\Findling\Db;

use OCP\AppFramework\Db\QBMapper;
use OCP\AppFramework\Utility\ITimeFactory;
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
 * its rows for the lock timeout of their kind and no longer, which is why those
 * values are small.
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
	 * The five kinds of work a row can carry.
	 *
	 *   acl       share, unshare, group change   no download, permissions only
	 *   delete    NodeDeleted, reconcile finding no node needed, and none allowed
	 *   metadata  rename, move of a file         no download, the text is indexed
	 *   content   create, write, first index     download plus extraction
	 *   ocr       PDF without a text layer       download, rasterise, tesseract
	 *
	 * This list is the only truth about valid kinds in the whole app. The
	 * controller validates against it, the claim iterates over it, and the
	 * database default is one of its members.
	 */
	public const KIND_ACL = 'acl';
	public const KIND_DELETE = 'delete';
	public const KIND_METADATA = 'metadata';
	public const KIND_CONTENT = 'content';
	public const KIND_OCR = 'ocr';

	/**
	 * The closed list, in the order the claim asks for them: permissions and
	 * deletions before anything that downloads bytes (D-04), and OCR last
	 * because it is the trailing track of the first index (D-07).
	 *
	 * The order lives in this constant and not in an ORDER BY, because a
	 * priority column would devalue findling_q_free and findling_q_kind and buy
	 * nothing that a loop over five cheap queries does not buy as well.
	 *
	 * @var list<string>
	 */
	public const KINDS = [
		self::KIND_ACL,
		self::KIND_DELETE,
		self::KIND_METADATA,
		self::KIND_CONTENT,
		self::KIND_OCR,
	];

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
	 *
	 * Phase 3 took the second of the two options the paragraph above offered: it
	 * splits the value per kind (LOCK_TIMEOUTS) and this constant is what every
	 * kind gets that does not ask for something else.
	 */
	public const LOCK_TIMEOUT = 900;

	/**
	 * Seconds a claim of one kind survives without an acknowledgement.
	 *
	 * OCR is the one exception, and the number is arithmetic rather than taste:
	 * a single OCR job may run up to 600 s under the ceiling cascade of plan
	 * 03-05, two of them are one claim (KIND_BATCH), and 1200 s of legitimate
	 * work under a 900 s timeout would make the row reappear as free, count a
	 * retry, and end as failed(repeatedly_stuck) while it is being worked on
	 * correctly at that very moment.
	 *
	 * @var array<string, int>
	 */
	public const LOCK_TIMEOUTS = [
		self::KIND_ACL => self::LOCK_TIMEOUT,
		self::KIND_DELETE => self::LOCK_TIMEOUT,
		self::KIND_METADATA => self::LOCK_TIMEOUT,
		self::KIND_CONTENT => self::LOCK_TIMEOUT,
		self::KIND_OCR => 1800,
	];

	/**
	 * What outranks what when two kinds meet in one row, see refreshExisting.
	 *
	 * Upgrade always, downgrade never. delete absorbs everything, because a file
	 * that is gone has nothing left to extract. content and ocr share a rank on
	 * purpose: a write to a scanned PDF must not throw its row back from ocr to
	 * content, otherwise a text free PDF circles between the two kinds forever.
	 * The one path from content to ocr is requeueAs (plan 03-07), which the
	 * container calls after it looked for a text layer.
	 *
	 * @var array<string, int>
	 */
	private const KIND_RANK = [
		self::KIND_ACL => 0,
		self::KIND_METADATA => 1,
		self::KIND_CONTENT => 2,
		self::KIND_OCR => 2,
		self::KIND_DELETE => 3,
	];

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
	 * at the same file at the same time would both see nothing in such a select
	 * and both insert; the unique index on file_id is what makes that
	 * impossible, and the swallowed conflict is turned into an update of the
	 * existing row. The race is decided by the database, which is the only
	 * participant that can decide it.
	 *
	 * The conflict branch is written out instead of using a single upsert
	 * statement because the public query builder of Nextcloud has no upsert that
	 * is proven to behave the same on SQLite, MariaDB and PostgreSQL. Plan 02-14
	 * verifies the behaviour of this method against a second dialect; should it
	 * fail there, the fix is local to this method and nothing above it changes.
	 */
	public function enqueue(int $fileId, int $storageId, int $rootId, int $size, bool $isUpdate, string $kind = self::KIND_CONTENT): void {
		// insertIgnoreConflict rather than insert-and-catch, and that is a
		// transaction property, not taste: on PostgreSQL a caught constraint
		// violation still aborts the surrounding transaction, so the crawl
		// could never put its slices inside one (perf audit H2, bug audit M7).
		// The dialects answer "already there" as zero affected rows instead.
		//
		// Two attempts, because the conflict branch can find the row already
		// deleted by a concurrent acknowledgement, in which case the insert is
		// simply right again. A third collision within one call is not a race
		// any more, it is a defect worth an exception.
		for ($attempt = 0; $attempt < 2; $attempt++) {
			$inserted = $this->db->insertIgnoreConflict(self::TABLE_NAME, [
				'file_id' => $fileId,
				'storage_id' => $storageId,
				'root_id' => $rootId,
				'is_update' => $isUpdate ? 1 : 0,
				'size' => $size,
				'kind' => $kind,
				'locked_at' => $this->freeMark()->format('Y-m-d H:i:s'),
			]);
			if ($inserted > 0) {
				return;
			}

			if ($this->refreshExisting($fileId, $size, $isUpdate, $kind)) {
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
	 * The kind of the row is the third thing this method decides, and it is the
	 * only one of the three that is not simply overwritten: a row is upgraded to
	 * the incoming kind and never downgraded to it, see KIND_RANK. Written as
	 * its own conditional statement rather than as a CASE expression, because
	 * "only these kinds are outranked" is a list the database can answer with
	 * the unique index on file_id, and because a reader can see the rule.
	 *
	 * @return bool false when the row vanished before either update could hit it
	 */
	private function refreshExisting(int $fileId, int $size, bool $isUpdate, string $kind): bool {
		$rank = self::KIND_RANK[$kind] ?? self::KIND_RANK[self::KIND_CONTENT];
		$outranked = [];
		foreach (self::KIND_RANK as $present => $presentRank) {
			if ($presentRank < $rank) {
				$outranked[] = $present;
			}
		}

		if ($outranked !== []) {
			// Nothing outranks acl, so that statement is skipped rather than
			// sent with an empty list. The row may be claimed right now and the
			// upgrade still applies: the kind decides what the container does
			// with the row after the current claim ends, not what it is doing
			// at this moment.
			$raise = $this->db->getQueryBuilder();
			$raise->update(self::TABLE_NAME)
				->set('kind', $raise->createNamedParameter($kind))
				->where($raise->expr()->eq('file_id', $raise->createNamedParameter($fileId, IQueryBuilder::PARAM_INT)))
				->andWhere($raise->expr()->in('kind', $raise->createNamedParameter($outranked, IQueryBuilder::PARAM_STR_ARRAY)));
			$raise->executeStatement();
		}

		// Which timeout applies depends on the kind the row carries, and this
		// method deliberately does not read the row. The longest of them is the
		// safe side: being wrong in this direction marks a row dirty that was
		// free anyway, and the next claim clears that mark. Being wrong in the
		// other direction would clear the lock of a row a container is still
		// working on, which is bug H4 of the phase 2 audit.
		$cutoff = $this->lockCutoff($this->now(), max(self::LOCK_TIMEOUTS));

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
	 * One kind per call, and the caller asks for all of them in the order of
	 * KINDS. That is where the priority of D-04 lives: not in a sort column, but
	 * in the sequence of these calls, with a batch size and a lock timeout of
	 * their own per kind.
	 *
	 * @return QueueFile[] the rows this caller owns, in queue order
	 */
	public function claimBatch(int $limit, int $maxBytes, string $kind = self::KIND_CONTENT): array {
		$now = $this->now();
		$cutoff = $this->lockCutoff($now, $this->lockTimeoutFor($kind));

		// The kind filter sits next to freeRowCondition and not inside it:
		// "free" keeps one definition, shared by the candidate query, the claim,
		// the conflict refresh and the counters, and the kind is a second,
		// independent question. Both together are exactly findling_q_kind.
		$candidates = $this->db->getQueryBuilder();
		$candidates->select('id', 'size')
			->from(self::TABLE_NAME)
			->where($this->freeRowCondition($candidates, $cutoff))
			->andWhere($candidates->expr()->eq('kind', $candidates->createNamedParameter($kind)))
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
		// collectors work at the same time, which is the normal case. Since
		// plan 05-20 the sentence has a second half: unlock() takes the count
		// back down, because a row the container hands back unjudged was a
		// hand-out and not an attempt of the file (DI-05-23, and the reasoning
		// stands in full at that method). The identifier is unquoted because it
		// is a reserved word in none of the
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
			->andWhere($this->freeRowCondition($claim, $cutoff))
			->andWhere($claim->expr()->eq('kind', $claim->createNamedParameter($kind)));
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
	 * What the work stock holds for one file, or null when it holds nothing.
	 *
	 * The third stage of the per file diagnosis of plan 04-07, and it reads the
	 * table rather than the HTTP routes above it: those carry the ExApp attribute
	 * and are unreachable from an admin session, and asking the container about
	 * the work stock of this side would invent a second answer to a question this
	 * database answers directly.
	 *
	 * Waiting and running are not the two values of the lock column, and the
	 * difference matters here. A free row is marked with the epoch and not with
	 * NULL, for the index reason written at freeRowCondition, and a claim that
	 * has run past its timeout is free again without anybody having written to
	 * it. So the answer is the remaining claim time: above zero means a collector
	 * holds this row right now, zero means it is waiting, and the timeout is the
	 * one of its own kind because an OCR claim lives twice as long as the rest.
	 *
	 * @return array{kind:string, retries:int, running:bool, secondsLeft:int}|null
	 */
	public function statusOfFile(int $fileId): ?array {
		if ($fileId <= 0) {
			return null;
		}

		$qb = $this->db->getQueryBuilder();
		$qb->select('kind', 'retries', 'locked_at')
			->from(self::TABLE_NAME)
			->where($qb->expr()->eq('file_id', $qb->createNamedParameter($fileId, IQueryBuilder::PARAM_INT)))
			->setMaxResults(1);

		$result = $qb->executeQuery();
		$row = $result->fetch();
		$result->closeCursor();
		if (!is_array($row)) {
			return null;
		}

		$kind = is_string($row['kind'] ?? null) && $row['kind'] !== '' ? $row['kind'] : self::KIND_CONTENT;
		$claimed = $this->claimStamp($row['locked_at'] ?? null);
		$elapsed = $this->now()->getTimestamp() - $claimed;
		$secondsLeft = $claimed <= 0 ? 0 : max(0, $this->lockTimeoutFor($kind) - $elapsed);

		return [
			'kind' => $kind,
			'retries' => (int)($row['retries'] ?? 0),
			'running' => $secondsLeft > 0,
			'secondsLeft' => $secondsLeft,
		];
	}

	/**
	 * The lock column as a Unix timestamp, and zero for the free mark.
	 *
	 * Zero rather than the current time for a value that cannot be read: "we do
	 * not know when this was claimed" must not be rendered as "claimed just now",
	 * which would show a row as running for the length of a whole timeout.
	 */
	private function claimStamp(mixed $value): int {
		if (!is_string($value) || $value === '') {
			return 0;
		}

		try {
			return max(0, (new \DateTimeImmutable($value, new \DateTimeZone('UTC')))->getTimestamp());
		} catch (\Throwable) {
			return 0;
		}
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
	 * Put rows on another kind of job, and create the ones that are not there.
	 *
	 * This is the one path that may raise a row from content to ocr, and the
	 * reason the merge rule of refreshExisting may not: a scanned PDF is only
	 * recognised as one after the container looked for a text layer, and an
	 * ordinary write to that file must never throw the row back to content
	 * afterwards. KIND_RANK gives content and ocr the same rank for exactly that
	 * reason, so this method is the only way across.
	 *
	 * Three properties carry it.
	 *
	 * The attempt counter goes back to zero. Handing a row out counts as an
	 * attempt, so a row arriving here has already spent one, and the OCR track
	 * would start with a used try. Three of them end a row as
	 * failed(repeatedly_stuck), and it would end exactly the large scans, which
	 * are the files this whole track exists for (phase research, pitfall 11).
	 *
	 * A file without a row gets one. The reconcile of plan 03-12 finds files that
	 * were never queued at all, and a requeue that could only touch existing rows
	 * would leave it without a way to schedule them.
	 *
	 * A deletion is not undone. delete is the absorbing element of KIND_RANK
	 * because a file that is gone has nothing left to extract, and a requeue that
	 * overwrote it would leave the document in the index for good, which is the
	 * defect class of pitfall 3. The kind is therefore both filtered here and
	 * excluded in the WHERE clause, the second one for the row that becomes a
	 * deletion between the two statements.
	 *
	 * The rows that are there are read before they are written, rather than
	 * trusting the number of affected rows: MySQL reports changed rows and not
	 * matched ones, so a row that already carries the kind and a zero counter
	 * would look absent and the answer would be short of the truth.
	 *
	 * @param int[] $fileIds
	 * @return int rows that carry the requested kind because of this call
	 */
	public function requeueAs(array $fileIds, string $kind): int {
		if ($fileIds === []) {
			return 0;
		}

		$requeued = 0;
		foreach (array_chunk(array_values(array_unique($fileIds)), self::DELETE_BAND) as $band) {
			$present = $this->kindsByFileId($band);
			$switchable = array_keys(array_filter(
				$present,
				static fn (string $kindOfRow): bool => $kindOfRow !== self::KIND_DELETE,
			));

			if ($switchable !== []) {
				$switch = $this->db->getQueryBuilder();
				$switch->update(self::TABLE_NAME)
					->set('kind', $switch->createNamedParameter($kind))
					// Pitfall 11 in one line: without this the OCR track starts
					// with a used attempt and the third one gives up on the very
					// scans it was built for.
					->set('retries', $switch->createNamedParameter(0, IQueryBuilder::PARAM_INT))
					// The claim is released as well, so the row is collectable at
					// once instead of after the lock timeout of its old kind.
					->set('locked_at', $switch->createNamedParameter($this->freeMark(), IQueryBuilder::PARAM_DATE))
					->where($switch->expr()->in('file_id', $switch->createNamedParameter($switchable, IQueryBuilder::PARAM_INT_ARRAY)))
					->andWhere($switch->expr()->neq('kind', $switch->createNamedParameter(self::KIND_DELETE)));
				$switch->executeStatement();
				$requeued += count($switchable);
			}

			foreach (array_diff($band, array_keys($present)) as $fileId) {
				// storage and root are zero, and the caller of this route knows
				// no better: it hands over file ids and a kind. Everything the
				// container sees about the file is resolved from the node at
				// claim time; these two fields are the exception, they come from
				// the row. QueueService::describe therefore repairs a zero from
				// the mount point of the resolved node before a work order
				// leaves the house, so it never reaches the container and never
				// overwrites a correct storage_id in its state database (review
				// finding WR-01).
				$requeued += $this->db->insertIgnoreConflict(self::TABLE_NAME, [
					'file_id' => $fileId,
					'storage_id' => 0,
					'root_id' => 0,
					'is_update' => 0,
					'size' => 0,
					'kind' => $kind,
					'locked_at' => $this->freeMark()->format('Y-m-d H:i:s'),
				]);
			}
		}

		return $requeued;
	}

	/**
	 * The kind of every row of this band that exists, keyed by file id.
	 *
	 * @param int[] $band
	 * @return array<int, string>
	 */
	private function kindsByFileId(array $band): array {
		$qb = $this->db->getQueryBuilder();
		$qb->select('file_id', 'kind')
			->from(self::TABLE_NAME)
			->where($qb->expr()->in('file_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));

		$kinds = [];
		$result = $qb->executeQuery();
		while (($row = $result->fetch()) !== false) {
			$kinds[(int)$row['file_id']] = is_string($row['kind'] ?? null) ? $row['kind'] : self::KIND_CONTENT;
		}
		$result->closeCursor();

		return $kinds;
	}

	/**
	 * Give rows back without processing them, and give their delivery back with
	 * them. This is the graceful restart: a container that is asked to stop
	 * returns what it holds instead of letting LOCK_TIMEOUT run out.
	 *
	 * **The refund is the fix for DI-05-23, and it is the reason this method has
	 * two statements instead of one.** The claim counts a delivery when it hands
	 * a row out, which is right for the case the give-up rule exists for: a row
	 * that is handed out and never comes back reports no failure anywhere, so
	 * without a ceiling on the deliveries it circles forever instead of becoming
	 * a visible end state. A row that IS handed back is the opposite of that
	 * case. The container said out loud that it did not judge the file, and a
	 * hand-out that produced no judgement is not an attempt of the file.
	 *
	 * What it cost before this plan, measured twice on a four gigabyte box in
	 * the full run of plan 05-14 (docs/performance.md, "Drill 3, Nachtrag"):
	 * below MIN_FREE_BYTES the container pauses correctly and hands its whole
	 * load back as `paused_low_disk`, a pass takes seconds, and after roughly
	 * twenty seconds of a tight disk MAX_DELIVERIES was spent for every row that
	 * happened to be with the worker. Thirty of thirty rows in the second pass
	 * of that drill ended as failed(repeatedly_stuck), twenty eight of them
	 * without ever having been handed to the container, while the page said
	 * "Indexing is paused so the index stays intact". That sentence was true of
	 * the index and false of the work stock.
	 *
	 * DI-05-23 reads the fix as needing a third channel in the acknowledgement,
	 * because the container has no way of saying "I did not even start". It has
	 * one: this route. Handing a row back IS that statement, and it already
	 * exists for the graceful restart, so the honest change is to let it mean
	 * what it says rather than to invent a second way of saying it.
	 *
	 * The refund is deliberately not limited to the disk pause. Every caller of
	 * this route is the container returning rows it did not judge: the pause,
	 * the content gateway that did not answer, and the shutdown. All three are
	 * the same statement, and a rule that held for one of them would leave the
	 * other two writing off work for a reason that has nothing to do with the
	 * file. What is NOT refunded is the delivery of a row that is never handed
	 * back at all, which is exactly the row the ceiling was built for.
	 *
	 * A container that pauses forever therefore circles forever, and that is the
	 * intended reading: while the disk is tight the work stock is preserved, the
	 * status page shows the rows as scheduled and the banner names the cause.
	 * Nothing is lost and nothing is judged.
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
			// The refund runs BEFORE the release, and the order is the whole
			// safety of it: while the row is still claimed nobody else can take
			// it, so the counter this decrement takes down is the one this
			// caller put up. Released first, a competing collector could claim
			// the row in between and this statement would silently spend its
			// delivery instead.
			//
			// The floor is a condition and not a function, because GREATEST and
			// MAX differ across the three dialects this app runs on while a
			// WHERE clause does not. A row at zero cannot be a row somebody is
			// handing back anyway: the claim raised it to at least one before
			// the container ever saw it.
			$refund = $this->db->getQueryBuilder();
			$refund->update(self::TABLE_NAME)
				->set('retries', $refund->createFunction('retries - 1'))
				->where($refund->expr()->in('id', $refund->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)))
				->andWhere($refund->expr()->gt('retries', $refund->createNamedParameter(0, IQueryBuilder::PARAM_INT)));
			$refund->executeStatement();

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
	 *
	 * Counted per kind and summed, because since this phase "the claim expired"
	 * is a different moment for an OCR row than for the rest. One query with one
	 * cutoff would report an OCR row as waiting while the claim still refuses to
	 * hand it out, and the status page of phase 4 would show work that nobody
	 * can take. Five narrow counts against findling_q_kind are the price.
	 */
	public function countScheduled(): int {
		$now = $this->now();

		$scheduled = 0;
		foreach (self::KINDS as $kind) {
			$cutoff = $this->lockCutoff($now, $this->lockTimeoutFor($kind));

			$qb = $this->db->getQueryBuilder();
			$qb->select($qb->func()->count('*', 'rows'))
				->from(self::TABLE_NAME)
				->where($this->freeRowCondition($qb, $cutoff))
				->andWhere($qb->expr()->eq('kind', $qb->createNamedParameter($kind)));
			$scheduled += $this->countFrom($qb);
		}

		return $scheduled;
	}

	/**
	 * Held by a collector right now, with a claim that has not expired. Per kind
	 * for the same reason as above.
	 */
	public function countRunning(): int {
		$now = $this->now();

		$running = 0;
		foreach (self::KINDS as $kind) {
			$cutoff = $this->lockCutoff($now, $this->lockTimeoutFor($kind));

			$qb = $this->db->getQueryBuilder();
			$qb->select($qb->func()->count('*', 'rows'))
				->from(self::TABLE_NAME)
				->where($qb->expr()->gt('locked_at', $qb->createNamedParameter($cutoff, IQueryBuilder::PARAM_DATE)))
				->andWhere($qb->expr()->eq('kind', $qb->createNamedParameter($kind)));
			$running += $this->countFrom($qb);
		}

		return $running;
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

	/**
	 * The seconds are an argument and no longer read out of a constant here,
	 * because there is no single answer any more: every caller knows which kind
	 * it is asking about and therefore which timeout applies.
	 */
	private function lockCutoff(\DateTime $now, int $seconds): \DateTime {
		$cutoff = clone $now;

		return $cutoff->setTimestamp($now->getTimestamp() - $seconds);
	}

	/**
	 * A kind this app does not know cannot appear in a row, the column is
	 * written from KINDS only. The fallback exists for the row that a future
	 * version wrote and this one reads during a rolling upgrade, and the shorter
	 * timeout is the right guess there: it frees the row earlier rather than
	 * later.
	 */
	private function lockTimeoutFor(string $kind): int {
		return self::LOCK_TIMEOUTS[$kind] ?? self::LOCK_TIMEOUT;
	}

	private function countFrom(IQueryBuilder $qb): int {
		$result = $qb->executeQuery();
		$count = $result->fetchOne();
		$result->closeCursor();

		return is_numeric($count) ? (int)$count : 0;
	}
}
