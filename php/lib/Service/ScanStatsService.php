<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\AppFramework\Utility\ITimeFactory;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\IDBConnection;
use Psr\Log\LoggerInterface;

/**
 * The scan counters, and the only writer of findling_scan_stats.
 *
 * This class holds the denominator of the coverage figure. The numerator comes
 * from the container (indexed documents), the denominator from here: how many
 * files of this instance could be indexed at all. Both halves have to mean the
 * same set of files, which is why the counters are written by the crawl while
 * it walks the mount and never by a second pass over the file list. The crawl
 * sees every indexable file with its size and its mimetype before any
 * extraction happens, so it is the metadata scan; a scan job of its own would
 * be a second walk over the same file list, and the two would disagree.
 *
 * Nothing in here holds a path, a file name or a mimetype. The table carries
 * numbers and a storage id, and the log lines of this class carry the same,
 * because this is a table an administration page renders straight into the DOM
 * (T-04-19).
 *
 * Idempotency, and why it is a reset rather than a cursor comparison. The crawl
 * runs over the same storage again after occ findling:index --restart, and a
 * plain += would double the estimate. Two clean options existed: (a) reset the
 * row when a storage starts from the beginning (last_file_id === 0) and add
 * during the run, or (b) treat cursor_file_id as the truth and only add for
 * entries above it. Option (a) is implemented here, because it lines up with
 * the termination condition the crawl already has: one place decides that a
 * mount starts over and one place decides that it is done. Option (b) would
 * need a per entry comparison inside the loop, which is a decision per file for
 * a counter that is written once per transaction band, and it would silently do
 * nothing at all after a cap change that makes previously skipped files
 * countable again.
 */
final class ScanStatsService {
	public const TABLE_NAME = 'findling_scan_stats';

	/**
	 * The counter columns, in the order of the table, mapped onto the keys the
	 * page reads. The map exists so that totals() cannot answer with fewer keys
	 * than it promises: it is built from this list, not from the rows it found.
	 *
	 * @var array<string, string>
	 */
	private const COUNTERS = [
		'files_seen' => 'filesSeen',
		'bytes_seen' => 'bytesSeen',
		'ocr_candidates' => 'ocrCandidates',
		'pdf_seen' => 'pdfSeen',
		'over_cap' => 'overCap',
		'excluded' => 'excluded',
	];

	/**
	 * Counter of everything that was thrown away, for the log line below. The
	 * rejected value itself is never logged, the same rule FileStateService
	 * follows: an argument that arrived malformed is unvalidated input, and
	 * writing it into the log instead of the database would only move the leak.
	 */
	private int $rejected = 0;

	public function __construct(
		private IDBConnection $db,
		private ITimeFactory $timeFactory,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * A storage starts over: every counter back to zero and finished_at back to
	 * null.
	 *
	 * Called by the crawl when it begins a mount at last_file_id === 0, which is
	 * a fresh installation or occ findling:index --restart. Without this call a
	 * second run would add its sightings on top of the first ones and the page
	 * would report roughly twice as many indexable files as the instance has
	 * (T-04-21).
	 */
	public function beginStorage(int $storageId): void {
		if ($storageId <= 0) {
			$this->reject();
			return;
		}

		$now = $this->timeFactory->getDateTime('now', new \DateTimeZone('UTC'));

		for ($attempt = 0; $attempt < 2; $attempt++) {
			$update = $this->db->getQueryBuilder();
			$update->update(self::TABLE_NAME);
			foreach (array_keys(self::COUNTERS) as $column) {
				$update->set($column, $update->createNamedParameter(0, IQueryBuilder::PARAM_INT));
			}
			$update->set('cursor_file_id', $update->createNamedParameter(0, IQueryBuilder::PARAM_INT))
				->set('finished_at', $update->createNamedParameter(null, IQueryBuilder::PARAM_NULL))
				->set('updated_at', $update->createNamedParameter($now, IQueryBuilder::PARAM_DATE))
				->where($update->expr()->eq('storage_id', $update->createNamedParameter($storageId, IQueryBuilder::PARAM_INT)));
			if ($update->executeStatement() >= 1) {
				return;
			}

			if ($this->insertFresh($storageId, $now) > 0) {
				return;
			}
			// Zero rows twice means somebody inserted between the two
			// statements; the update of the next attempt wins over their value.
		}
	}

	/**
	 * A zero row for a mount that has no row yet.
	 *
	 * insertIgnoreConflict rather than insert and catch, for the same reason the
	 * counter upsert uses it: beginStorage runs from the crawl, which is inside
	 * an open transaction, and on PostgreSQL a caught constraint violation would
	 * abort that transaction rather than just this statement.
	 */
	private function insertFresh(int $storageId, \DateTimeInterface $now): int {
		return $this->db->insertIgnoreConflict(self::TABLE_NAME, array_merge(
			array_fill_keys(array_keys(self::COUNTERS), 0),
			[
				'storage_id' => $storageId,
				'cursor_file_id' => 0,
				'updated_at' => $now->format('Y-m-d H:i:s'),
			],
		));
	}

	/**
	 * Add the counters of one transaction band.
	 *
	 * Called once per TX_BAND of the crawl and once more before the closing
	 * commit, never once per file: one update per file would be exactly the
	 * doubling of cost that the band exists to avoid (T-04-22).
	 *
	 * The addition happens in the database and not in PHP, so two crawl slices
	 * of the same mount cannot read the same value and write it back twice. The
	 * upsert follows FileStateService::record: update first, insert only when
	 * nothing was there, and insertIgnoreConflict rather than insert and catch,
	 * because this method runs inside the transaction band of the crawl and on
	 * PostgreSQL a caught constraint violation aborts that whole band (bug audit
	 * M7).
	 *
	 * cursor_file_id is assigned and not maximised. The caller passes the cursor
	 * of the slice it just walked, and that cursor only ever moves forward
	 * inside one mount; a GREATEST() here would buy nothing and is not spelled
	 * the same way on all three databases.
	 */
	public function add(
		int $storageId,
		int $filesSeen,
		int $bytesSeen,
		int $ocrCandidates,
		int $pdfSeen,
		int $overCap,
		int $excluded,
		int $cursorFileId,
	): void {
		if ($storageId <= 0) {
			$this->reject();
			return;
		}

		$deltas = [
			'files_seen' => max(0, $filesSeen),
			'bytes_seen' => max(0, $bytesSeen),
			'ocr_candidates' => max(0, $ocrCandidates),
			'pdf_seen' => max(0, $pdfSeen),
			'over_cap' => max(0, $overCap),
			'excluded' => max(0, $excluded),
		];
		$cursor = max(0, $cursorFileId);
		$now = $this->timeFactory->getDateTime('now', new \DateTimeZone('UTC'));

		for ($attempt = 0; $attempt < 2; $attempt++) {
			$update = $this->db->getQueryBuilder();
			$update->update(self::TABLE_NAME);
			foreach ($deltas as $column => $delta) {
				$update->set($column, $update->func()->add(
					$column,
					$update->createNamedParameter($delta, IQueryBuilder::PARAM_INT),
				));
			}
			$update->set('cursor_file_id', $update->createNamedParameter($cursor, IQueryBuilder::PARAM_INT))
				->set('updated_at', $update->createNamedParameter($now, IQueryBuilder::PARAM_DATE))
				->where($update->expr()->eq('storage_id', $update->createNamedParameter($storageId, IQueryBuilder::PARAM_INT)));
			if ($update->executeStatement() >= 1) {
				return;
			}

			// No row yet, so the deltas are the whole truth about this mount so
			// far and the insert carries them as they are.
			$inserted = $this->db->insertIgnoreConflict(self::TABLE_NAME, array_merge($deltas, [
				'storage_id' => $storageId,
				'cursor_file_id' => $cursor,
				'updated_at' => $now->format('Y-m-d H:i:s'),
			]));
			if ($inserted > 0) {
				return;
			}
		}
	}

	/**
	 * This mount is through: finished_at gets a value.
	 *
	 * The only place a mount counts as complete, and the counterpart of the
	 * termination condition in StorageCrawlJob. Without this mark the page has
	 * to call its number provisional, which is the honest answer while a scan is
	 * still walking.
	 */
	public function finishStorage(int $storageId, int $cursorFileId): void {
		if ($storageId <= 0) {
			$this->reject();
			return;
		}

		$now = $this->timeFactory->getDateTime('now', new \DateTimeZone('UTC'));

		for ($attempt = 0; $attempt < 2; $attempt++) {
			$update = $this->db->getQueryBuilder();
			$update->update(self::TABLE_NAME)
				->set('cursor_file_id', $update->createNamedParameter(max(0, $cursorFileId), IQueryBuilder::PARAM_INT))
				->set('finished_at', $update->createNamedParameter($now, IQueryBuilder::PARAM_DATE))
				->set('updated_at', $update->createNamedParameter($now, IQueryBuilder::PARAM_DATE))
				->where($update->expr()->eq('storage_id', $update->createNamedParameter($storageId, IQueryBuilder::PARAM_INT)));
			if ($update->executeStatement() >= 1) {
				return;
			}

			// A mount that terminates without ever having been counted is an
			// empty mount. It still gets a row, because a mount missing from
			// this table would make mountsFinished smaller than mountsTotal
			// forever and the page would call a finished scan provisional.
			$inserted = $this->db->insertIgnoreConflict(self::TABLE_NAME, [
				'storage_id' => $storageId,
				'cursor_file_id' => max(0, $cursorFileId),
				'finished_at' => $now->format('Y-m-d H:i:s'),
				'updated_at' => $now->format('Y-m-d H:i:s'),
			]);
			if ($inserted > 0) {
				return;
			}
		}
	}

	/**
	 * The sum of every counter over every mount, plus how many mounts are
	 * through.
	 *
	 * Always all eight keys, zero for the ones nothing was written for yet. The
	 * shape follows FileStateService::counts(): a status answer that leaves an
	 * empty value out makes "nothing was counted" and "the counter is broken"
	 * indistinguishable, and this figure is the headline number of the page.
	 *
	 * mountsTotal is the number of rows and mountsFinished the number of rows
	 * with a finished_at. As long as the two differ the number is a lower bound,
	 * and the caller has to label it as provisional and name both figures.
	 *
	 * @return array{
	 *     filesSeen:int, bytesSeen:int, ocrCandidates:int, pdfSeen:int,
	 *     overCap:int, excluded:int, mountsTotal:int, mountsFinished:int
	 * }
	 */
	public function totals(): array {
		$totals = array_fill_keys(array_values(self::COUNTERS), 0);
		$totals['mountsTotal'] = 0;
		$totals['mountsFinished'] = 0;

		$qb = $this->db->getQueryBuilder();
		$qb->selectAlias($qb->func()->count('*'), 'mounts_total');
		foreach (array_keys(self::COUNTERS) as $column) {
			$qb->selectAlias($qb->func()->sum($column), 'sum_' . $column);
		}
		$qb->from(self::TABLE_NAME);

		$result = $qb->executeQuery();
		$row = $result->fetch();
		$result->closeCursor();

		if (is_array($row)) {
			$totals['mountsTotal'] = (int)($row['mounts_total'] ?? 0);
			foreach (self::COUNTERS as $column => $key) {
				// A sum over an empty table is null on all three databases, and
				// null cast to int is the zero this method promises.
				$totals[$key] = (int)($row['sum_' . $column] ?? 0);
			}
		}

		$finished = $this->db->getQueryBuilder();
		$finished->selectAlias($finished->func()->count('*'), 'mounts_finished')
			->from(self::TABLE_NAME)
			->where($finished->expr()->isNotNull('finished_at'));

		$result = $finished->executeQuery();
		$row = $result->fetch();
		$result->closeCursor();

		if (is_array($row)) {
			$totals['mountsFinished'] = (int)($row['mounts_finished'] ?? 0);
		}

		return $totals;
	}

	/**
	 * The counters of one mount, or null when this mount has never been walked.
	 *
	 * Null and not a row of zeros, because the two mean different things here:
	 * a mount with zeros was walked and holds no document, a mount without a row
	 * has not been reached yet. The per mount view of a later plan needs that
	 * distinction, and totals() above is the place that answers with zeros.
	 *
	 * @return array{
	 *     storageId:int, filesSeen:int, bytesSeen:int, ocrCandidates:int,
	 *     pdfSeen:int, overCap:int, excluded:int, cursorFileId:int,
	 *     finished:bool
	 * }|null
	 */
	public function forStorage(int $storageId): ?array {
		if ($storageId <= 0) {
			$this->reject();
			return null;
		}

		$qb = $this->db->getQueryBuilder();
		$qb->select('*')
			->from(self::TABLE_NAME)
			->where($qb->expr()->eq('storage_id', $qb->createNamedParameter($storageId, IQueryBuilder::PARAM_INT)))
			->setMaxResults(1);

		$result = $qb->executeQuery();
		$row = $result->fetch();
		$result->closeCursor();

		if (!is_array($row)) {
			return null;
		}

		$mount = ['storageId' => (int)($row['storage_id'] ?? 0)];
		foreach (self::COUNTERS as $column => $key) {
			$mount[$key] = (int)($row[$column] ?? 0);
		}
		$mount['cursorFileId'] = (int)($row['cursor_file_id'] ?? 0);
		$mount['finished'] = ($row['finished_at'] ?? null) !== null;

		return $mount;
	}

	private function reject(): void {
		$this->rejected++;
		$this->logger->warning(
			'Findling: rejected a scan counter without a usable storage',
			['rejected' => $this->rejected],
		);
	}
}
