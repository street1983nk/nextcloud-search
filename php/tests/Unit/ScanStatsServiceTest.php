<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\ScanStatsService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\DB\IResult;
use OCP\DB\QueryBuilder\IExpressionBuilder;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\IDBConnection;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The denominator of the coverage figure, per counting key (plan 39-01, Weg C).
 *
 * totals() answers twice since this plan: the eight keys of 1.5 on the top level,
 * ungrouped and unchanged, and the same eight keys under ``grouped``, where every
 * group of storages that show one tree counts once, through its representative.
 * Which of the two the page shows is decided by AdminViewService once the
 * container answered; this file holds the arithmetic.
 *
 * The database is a small fake over findling_scan_stats: every query is answered
 * out of the rows below, filtered by the IN band it was given, so a forgotten
 * band or a wrong column shows up as a wrong sum.
 */
#[CoversClass(ScanStatsService::class)]
final class ScanStatsServiceTest extends TestCase {
	private IDBConnection&MockObject $db;

	/** Rows of findling_scan_stats by storage id. @var array<int, array<string, mixed>> */
	private array $rows = [];

	/** The size of the IN band of every executed query. @var list<int> */
	private array $bands = [];

	private int $opened = 0;
	private int $closed = 0;

	protected function setUp(): void {
		parent::setUp();

		$this->db = $this->createMock(IDBConnection::class);
		$this->db->method('getQueryBuilder')->willReturnCallback(fn (): IQueryBuilder => $this->queryBuilder());
	}

	private function queryBuilder(): IQueryBuilder {
		$ints = null;

		$qb = $this->createMock(IQueryBuilder::class);
		$expr = $this->createMock(IExpressionBuilder::class);
		$expr->method('in')->willReturn('storage_id IN (:p)');

		$qb->method('select')->willReturnSelf();
		$qb->method('from')->willReturnSelf();
		$qb->method('where')->willReturnSelf();
		$qb->method('andWhere')->willReturnSelf();
		$qb->method('expr')->willReturn($expr);
		$qb->method('createNamedParameter')->willReturnCallback(
			static function (mixed $value, mixed $type = null) use (&$ints): string {
				if ($type === IQueryBuilder::PARAM_INT_ARRAY) {
					$ints = $value;
				}

				return ':p';
			},
		);
		$qb->method('executeQuery')->willReturnCallback(function () use (&$ints): IResult {
			self::assertIsArray($ints, 'every query of totals carries its band as an int array');
			$this->bands[] = count($ints);

			$rows = [];
			foreach ($ints as $storageId) {
				if (isset($this->rows[$storageId])) {
					$rows[] = $this->rows[$storageId];
				}
			}

			return $this->resultOf($rows);
		});

		return $qb;
	}

	/** @param list<array<string, mixed>> $rows */
	private function resultOf(array $rows): IResult {
		$this->opened++;
		$result = $this->createMock(IResult::class);
		$result->method('fetch')->willReturnCallback(static function () use (&$rows): mixed {
			$row = array_shift($rows);

			return $row ?? false;
		});
		$result->method('closeCursor')->willReturnCallback(function (): bool {
			$this->closed++;

			return true;
		});

		return $result;
	}

	private function service(): ScanStatsService {
		return new ScanStatsService(
			$this->db,
			$this->createMock(ITimeFactory::class),
			$this->createMock(LoggerInterface::class),
		);
	}

	/** One row as the database hands it out: strings, and null for an open mount. */
	private function row(int $storageId, int $filesSeen, bool $finished, int $overCap = 0, int $excluded = 0): void {
		$this->rows[$storageId] = [
			'storage_id' => (string)$storageId,
			'files_seen' => (string)$filesSeen,
			'bytes_seen' => (string)($filesSeen * 1000),
			'ocr_candidates' => '1',
			'pdf_seen' => '2',
			'over_cap' => (string)$overCap,
			'excluded' => (string)$excluded,
			'finished_at' => $finished ? '2026-10-28 12:00:00' : null,
		];
	}

	/** @return array<string, int> */
	private static function eight(int $files, int $bytes, int $ocr, int $pdf, int $overCap, int $excluded, int $total, int $finished): array {
		return [
			'filesSeen' => $files,
			'bytesSeen' => $bytes,
			'ocrCandidates' => $ocr,
			'pdfSeen' => $pdf,
			'overCap' => $overCap,
			'excluded' => $excluded,
			'mountsTotal' => $total,
			'mountsFinished' => $finished,
		];
	}

	public function testWithoutGroupsBothSetsAreTheFigureOfOneFive(): void {
		$this->row(5, 40, true, 3, 1);
		$this->row(17, 100, true);
		$this->row(31, 100, false);

		$totals = $this->service()->totals([5, 17, 31, 99]);

		$expected = self::eight(240, 240_000, 3, 6, 3, 1, 3, 2);
		foreach ($expected as $key => $value) {
			self::assertSame($value, $totals[$key], $key);
		}
		self::assertSame($expected, $totals['grouped']);
		self::assertSame([], $totals['leftOutStorageIds']);
		self::assertSame(0, $totals['groupsApplied']);
		self::assertSame([4], $this->bands, 'one query per band');
		self::assertSame($this->opened, $this->closed, 'every cursor is closed');
	}

	public function testAGroupCountsOnceThroughItsRepresentative(): void {
		// One share for two users, both counted through, plus a home.
		$this->row(5, 40, true);
		$this->row(17, 100, true);
		$this->row(31, 100, true);

		$totals = $this->service()->totals([5, 17, 31], [[17, 31]]);

		self::assertSame(240, $totals['filesSeen'], 'the top level stays ungrouped');
		self::assertSame(3, $totals['mountsTotal']);
		self::assertSame(self::eight(140, 140_000, 2, 4, 0, 0, 2, 2), $totals['grouped']);
		self::assertSame([31], $totals['leftOutStorageIds']);
		self::assertSame(1, $totals['groupsApplied']);
	}

	public function testTheRepresentativeIsTheSmallestFinishedMember(): void {
		// 17 is still walking, 31 is through: 31 represents the group and the
		// grouped figure is not provisional because of 17.
		$this->row(17, 10, false);
		$this->row(31, 100, true);
		$this->row(40, 100, true);

		$totals = $this->service()->totals([17, 31, 40], [[17, 31, 40]]);

		self::assertSame(self::eight(100, 100_000, 1, 2, 0, 0, 1, 1), $totals['grouped']);
		self::assertSame([17, 40], $totals['leftOutStorageIds']);
	}

	public function testWithoutAFinishedMemberTheSmallestCountedOneRepresents(): void {
		// 9 has no row yet, 17 and 31 are walking: 17 represents.
		$this->row(17, 10, false);
		$this->row(31, 30, false);

		$totals = $this->service()->totals([9, 17, 31], [[9, 17, 31]]);

		self::assertSame(self::eight(10, 10_000, 1, 2, 0, 0, 1, 0), $totals['grouped']);
		self::assertSame([9, 31], $totals['leftOutStorageIds']);
	}

	public function testMembersOutsideTheMountListTakeNoPart(): void {
		// 31 is grouped with 17 but no longer mounted: nothing is left out.
		$this->row(17, 100, true);
		$this->row(31, 100, true);

		$totals = $this->service()->totals([17], [[17, 31]]);

		self::assertSame(self::eight(100, 100_000, 1, 2, 0, 0, 1, 1), $totals['grouped']);
		self::assertSame([], $totals['leftOutStorageIds']);
		self::assertSame(0, $totals['groupsApplied']);
	}

	public function testANothingMountedAnswerIsZerosAndAsksNothing(): void {
		$this->db->expects(self::never())->method('getQueryBuilder');

		$totals = $this->service()->totals([], [[1, 2]]);

		self::assertSame(self::eight(0, 0, 0, 0, 0, 0, 0, 0), $totals['grouped']);
		self::assertSame(0, $totals['filesSeen']);
		self::assertSame(0, $totals['mountsTotal']);
		self::assertSame([], $totals['leftOutStorageIds']);
	}

	public function testSixHundredStoragesAreAskedInTwoBands(): void {
		foreach (range(1, 600) as $storageId) {
			$this->row($storageId, 1, true);
		}

		$totals = $this->service()->totals(range(1, 600), [range(101, 600)]);

		self::assertSame(600, $totals['filesSeen']);
		self::assertSame(101, $totals['grouped']['filesSeen']);
		self::assertSame(101, $totals['grouped']['mountsTotal']);
		self::assertCount(499, $totals['leftOutStorageIds']);
		self::assertSame([500, 100], $this->bands);
	}
}
