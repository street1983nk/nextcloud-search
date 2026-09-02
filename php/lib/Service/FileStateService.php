<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\AppFramework\Utility\ITimeFactory;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\IDBConnection;
use Psr\Log\LoggerInterface;

/**
 * The return channel, and the only writer of findling_file_state.
 *
 * Everything that was not indexed lands here with a reason code, and this table
 * is one of the two sources the status page of phase 4 reads. The split between
 * them is written down on both sides, here and in the module docstring of
 * backend/src/findling/api/status.py, because two docblocks that each claimed
 * the whole page is how a page ends up reporting "no errors" while a switched
 * off container quietly answers nothing at all.
 *
 * This table is the source for skipped, failed, the reason codes behind them and
 * the per file error list. That is the half an admin can still read when the
 * container is down, which is exactly the moment they go looking for it.
 *
 * The container is the source for indexed, indexed(truncated), the document
 * count of the index, the permission rows, the version marks, the space on the
 * volume and the throughput. Only the container sees the volume and the Tantivy
 * index, so nobody else can count those.
 *
 * The status page shows both views separately and names the source of each. A
 * difference between them is a diagnostic signal and not a defect of the page.
 * What must not happen: a single number called "failed" without a source, or two
 * counters that get combined into one value; either one hides precisely the case
 * that is worth seeing.
 *
 * Two callers exist. The crawl of plan 02-04 writes skipped(too_large) before a
 * file is ever queued, and the acknowledgement endpoint writes whatever the
 * container reports it could not process.
 *
 * The state and the reason are checked against a closed list here. The
 * container is trusted, but a trusted component with a defect must not be able
 * to write a file name into a database column, and free text as a reason is
 * exactly how that would happen.
 */
class FileStateService {
	public const TABLE_NAME = 'findling_file_state';

	/**
	 * indexed means the text is in the index, skipped means we decided not to
	 * index this file, failed means we wanted to and could not. Only failed is
	 * an error in the sense of the status page, and that distinction is the
	 * actual payload of IDX-06.
	 *
	 * @var list<string>
	 */
	public const STATES = [
		'indexed',
		'skipped',
		'failed',
	];

	/**
	 * The closed list of reasons, identical to the table in the phase research.
	 * Anything outside of it is dropped rather than stored.
	 *
	 * This list is the third copy of the same taxonomy, next to
	 * backend/src/findling/extract/errors.py and
	 * backend/src/findling/store/repo.py, and it is the one whose absence is
	 * silent: record() below drops a reason it does not know, so a code that
	 * only the container knows leaves the file with no verdict at all. Since
	 * phase 3 a Python test reads this constant and compares it with the other
	 * two in both directions, so the three cannot drift apart unnoticed.
	 *
	 * The display text of every code lives in
	 * .planning/phases/04-admin-sichtbarkeit-und-diagnose/04-UI-SPEC.md as a
	 * binding table, one German label and one remedy per reason. A code that
	 * arrives here without a row in that table is shown as "Unbekannter Grund
	 * (%s)" with the code in brackets, never as an empty field and never as the
	 * raw code on its own: an admin who reads a blank cell learns nothing, and a
	 * blank cell is also what a drift between the three lists would look like.
	 *
	 * @var list<string>
	 */
	public const REASONS = [
		// indexed
		'truncated',
		// skipped
		'too_large',
		'mime_not_allowed',
		'encrypted',
		'no_text_layer',
		'empty_text',
		'too_many_cells',
		'gone',
		'image_not_ocrable',
		// failed
		'empty_file',
		'corrupt',
		'xml_invalid',
		'encoding_unknown',
		'timeout',
		'out_of_memory',
		'gateway_error',
		'repeatedly_stuck',
		'ocr_failed',
		'ocr_unavailable',
	];

	/**
	 * How many rows one call of page() may hand out at the most.
	 *
	 * Fifty, and the number is a cost and not a taste. Every row of a page ends
	 * up in PathResolverService, where it costs one mount cache query and one
	 * userExists() call, so a page is worth roughly three queries per row. Fifty
	 * rows stay under a hundred and fifty queries, which is a page an
	 * administrator waits out; the error list of the status page asks for twenty
	 * per reason group and therefore never reaches this ceiling.
	 *
	 * A limit above it is clamped rather than refused. A caller asking for a
	 * thousand rows is not an attack and not a defect, it is a caller that does
	 * not know the ceiling, and answering fifty rows is more useful than
	 * answering none.
	 */
	public const MAX_PAGE = 50;

	/**
	 * Counter of everything that was thrown away, for the log line below. The
	 * rejected value itself is never logged: it is unvalidated input from the
	 * container, and a file name arriving as a reason is precisely the case this
	 * class defends against, so writing it into the log instead of the database
	 * would only move the leak.
	 */
	private int $rejected = 0;

	public function __construct(
		private IDBConnection $db,
		private ITimeFactory $timeFactory,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * Record the end state of one file. There is exactly one row per file, so a
	 * later state replaces an earlier one instead of piling up.
	 *
	 * @return bool false when the input was rejected, which the caller may count
	 */
	public function record(int $fileId, string $state, ?string $reason): bool {
		if ($fileId <= 0 || !in_array($state, self::STATES, true)) {
			$this->reject();
			return false;
		}

		if ($reason !== null && !in_array($reason, self::REASONS, true)) {
			$this->reject();
			return false;
		}

		$now = $this->timeFactory->getDateTime('now', new \DateTimeZone('UTC'));

		// Update first, insert only when nothing was there. On the mass paths
		// (re-crawl, acknowledgement) the row almost always exists, and the old
		// insert-and-catch order produced one caught constraint violation per
		// file (bug audit M7). Worse than the cost: this method runs inside the
		// acknowledgement transaction, and on PostgreSQL a caught violation
		// still aborts that whole transaction. insertIgnoreConflict answers
		// "already there" as zero affected rows instead of throwing, and the
		// primary key keeps deciding the race, not a select.
		for ($attempt = 0; $attempt < 2; $attempt++) {
			$update = $this->db->getQueryBuilder();
			$update->update(self::TABLE_NAME)
				->set('state', $update->createNamedParameter($state, IQueryBuilder::PARAM_STR))
				->set('reason', $update->createNamedParameter($reason, $reason === null ? IQueryBuilder::PARAM_NULL : IQueryBuilder::PARAM_STR))
				->set('updated_at', $update->createNamedParameter($now, IQueryBuilder::PARAM_DATE))
				->where($update->expr()->eq('file_id', $update->createNamedParameter($fileId, IQueryBuilder::PARAM_INT)));
			if ($update->executeStatement() >= 1) {
				return true;
			}

			$inserted = $this->db->insertIgnoreConflict(self::TABLE_NAME, [
				'file_id' => $fileId,
				'state' => $state,
				'reason' => $reason,
				'updated_at' => $now->format('Y-m-d H:i:s'),
			]);
			if ($inserted > 0) {
				return true;
			}
			// Zero rows twice means somebody inserted between the two
			// statements; the update of the next attempt wins over their value.
		}

		return true;
	}

	/**
	 * One number per state, zero for the states nothing was written for yet.
	 * The status page needs a complete row, not a sparse one.
	 *
	 * @return array<string, int>
	 */
	public function counts(): array {
		$counts = array_fill_keys(self::STATES, 0);

		$qb = $this->db->getQueryBuilder();
		$qb->select('state')
			->selectAlias($qb->func()->count('*'), 'total')
			->from(self::TABLE_NAME)
			->groupBy('state');

		$result = $qb->executeQuery();
		while (($row = $result->fetch()) !== false) {
			$state = (string)($row['state'] ?? '');
			if (array_key_exists($state, $counts)) {
				$counts[$state] = (int)($row['total'] ?? 0);
			}
		}
		$result->closeCursor();

		return $counts;
	}

	/**
	 * One number per state and reason code, and never a sparse answer.
	 *
	 * All three states are always keys, with an empty map under a state nothing
	 * was written for yet. That is the same rule counts() follows and it exists
	 * for the same reason: a status answer that leaves out an empty value makes
	 * "nothing failed" and "the counter is broken" indistinguishable, and this
	 * app exists because its predecessor reported the first while meaning the
	 * second.
	 *
	 * A row without a reason is normalised to the empty string rather than
	 * carrying null into the answer, so that the structure is the same shape
	 * whether it is read in PHP or decoded from JSON. Such a row cannot arise
	 * from any writer of this app, every one of them passes a code, so the empty
	 * key is the honest place for a row that came from somewhere else.
	 *
	 * @return array<string, array<string, int>> state to reason code to count
	 */
	public function reasonsByState(): array {
		$breakdown = array_fill_keys(self::STATES, []);

		$qb = $this->db->getQueryBuilder();
		$qb->select('state', 'reason')
			->selectAlias($qb->func()->count('*'), 'total')
			->from(self::TABLE_NAME)
			->groupBy('state', 'reason');

		$result = $qb->executeQuery();
		while (($row = $result->fetch()) !== false) {
			$state = (string)($row['state'] ?? '');
			if (!array_key_exists($state, $breakdown)) {
				continue;
			}
			$breakdown[$state][(string)($row['reason'] ?? '')] = (int)($row['total'] ?? 0);
		}
		$result->closeCursor();

		return $breakdown;
	}

	/**
	 * One page of rows carrying this verdict, the most recent ones first.
	 *
	 * Ordered by updated_at descending and by file_id descending after it. The
	 * second key is not decoration: a crawl writes hundreds of rows within the
	 * same second, and an order that is only defined down to the second hands
	 * out the same row twice across two pages on some dialects and drops another
	 * one. The index findling_fs_upd of migration 20260904 answers the state and
	 * the sort together.
	 *
	 * The limit is clamped and the offset is floored instead of being refused,
	 * because both are display decisions of a caller and neither can be an
	 * attack: MAX_PAGE is the ceiling and one row is the floor.
	 *
	 * A state outside STATES or a reason outside REASONS is a rejected call and
	 * answers with an empty list. The rejected value is counted and never
	 * logged, for the reason written above reject(): a file name can arrive in
	 * exactly this argument.
	 *
	 * A null reason means no filter on the reason at all, which is what a caller
	 * asking for "the failed rows" rather than "the failed rows of one code"
	 * needs. It is deliberately not read as "the rows without a reason": no
	 * writer of this app produces one, so a filter for it would be a query
	 * nobody can trigger.
	 *
	 * @return list<array{fileId:int,state:string,reason:string,updatedAt:int}>
	 */
	public function page(string $state, ?string $reason, int $limit, int $offset): array {
		if (!in_array($state, self::STATES, true)) {
			$this->reject();
			return [];
		}
		if ($reason !== null && !in_array($reason, self::REASONS, true)) {
			$this->reject();
			return [];
		}

		$qb = $this->db->getQueryBuilder();
		$qb->select('file_id', 'state', 'reason', 'updated_at')
			->from(self::TABLE_NAME)
			->where($qb->expr()->eq('state', $qb->createNamedParameter($state, IQueryBuilder::PARAM_STR)))
			->orderBy('updated_at', 'DESC')
			->addOrderBy('file_id', 'DESC')
			->setMaxResults(max(1, min(self::MAX_PAGE, $limit)))
			->setFirstResult(max(0, $offset));

		if ($reason !== null) {
			$qb->andWhere($qb->expr()->eq('reason', $qb->createNamedParameter($reason, IQueryBuilder::PARAM_STR)));
		}

		$rows = [];
		$result = $qb->executeQuery();
		while (($row = $result->fetch()) !== false) {
			$rows[] = $this->shape($row);
		}
		$result->closeCursor();

		return $rows;
	}

	/**
	 * The verdict this side holds for exactly one file, or null.
	 *
	 * The same row shape page() hands out, because both end up in the same
	 * renderer: the per file diagnosis of ADM-02 shows what a row of the error
	 * list shows, for one file instead of twenty. Null means this table has
	 * never heard of the file, which is a different answer from "indexed" and
	 * from "failed" and has to stay distinguishable from both.
	 *
	 * @return array{fileId:int,state:string,reason:string,updatedAt:int}|null
	 */
	public function forFile(int $fileId): ?array {
		if ($fileId <= 0) {
			$this->reject();
			return null;
		}

		$qb = $this->db->getQueryBuilder();
		$qb->select('file_id', 'state', 'reason', 'updated_at')
			->from(self::TABLE_NAME)
			->where($qb->expr()->eq('file_id', $qb->createNamedParameter($fileId, IQueryBuilder::PARAM_INT)))
			->setMaxResults(1);

		$result = $qb->executeQuery();
		$row = $result->fetch();
		$result->closeCursor();

		return is_array($row) ? $this->shape($row) : null;
	}

	/**
	 * One database row as the four fields every reader of this class hands out.
	 *
	 * @param array<string, mixed> $row
	 * @return array{fileId:int,state:string,reason:string,updatedAt:int}
	 */
	private function shape(array $row): array {
		return [
			'fileId' => (int)($row['file_id'] ?? 0),
			'state' => (string)($row['state'] ?? ''),
			'reason' => (string)($row['reason'] ?? ''),
			'updatedAt' => $this->stamp($row['updated_at'] ?? null),
		];
	}

	/**
	 * A datetime column as a Unix timestamp, or zero when it cannot be read.
	 *
	 * Zero rather than the current time for an unreadable value: "we do not know
	 * when" must not be rendered as "just now", which is the shape of every
	 * status page that claims to be up to date while knowing nothing.
	 */
	private function stamp(mixed $value): int {
		if (!is_string($value) || $value === '') {
			return 0;
		}

		try {
			return (new \DateTimeImmutable($value, new \DateTimeZone('UTC')))->getTimestamp();
		} catch (\Throwable) {
			return 0;
		}
	}

	/**
	 * How many files carry exactly this verdict.
	 *
	 * Asked for one pair at a time and validated against the two closed lists
	 * first, so that a caller cannot count a state or a reason this app does not
	 * have and get a zero that reads like an answer. A pair outside the lists is
	 * a rejected call and is counted as such.
	 *
	 * The coverage figure needs this for skipped(mime_not_allowed): those files
	 * are not indexable by definition and therefore belong next to the fraction
	 * as deliberately left out, never into its denominator. The reason travels
	 * in as an argument rather than being fixed here, because a second caller
	 * with a second reason would otherwise copy this query.
	 */
	public function countByReason(string $state, string $reason): int {
		if (!in_array($state, self::STATES, true) || !in_array($reason, self::REASONS, true)) {
			$this->reject();
			return 0;
		}

		$qb = $this->db->getQueryBuilder();
		$qb->selectAlias($qb->func()->count('*'), 'total')
			->from(self::TABLE_NAME)
			->where($qb->expr()->eq('state', $qb->createNamedParameter($state, IQueryBuilder::PARAM_STR)))
			->andWhere($qb->expr()->eq('reason', $qb->createNamedParameter($reason, IQueryBuilder::PARAM_STR)));

		$result = $qb->executeQuery();
		$row = $result->fetch();
		$result->closeCursor();

		return is_array($row) ? (int)($row['total'] ?? 0) : 0;
	}

	private function reject(): void {
		$this->rejected++;
		$this->logger->warning(
			'Findling: rejected a file state that is not in the closed list',
			['rejected' => $this->rejected],
		);
	}
}
