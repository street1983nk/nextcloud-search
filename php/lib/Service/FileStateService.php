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

	private function reject(): void {
		$this->rejected++;
		$this->logger->warning(
			'Findling: rejected a file state that is not in the closed list',
			['rejected' => $this->rejected],
		);
	}
}
