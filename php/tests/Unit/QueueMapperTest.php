<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Db\QueueMapper;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\DB\IResult;
use OCP\DB\QueryBuilder\IExpressionBuilder;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\IDBConnection;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The answer of requeueAs, held against a simulated database (#25, F3).
 *
 * The database is an array of rows, after the pattern of
 * FileStateServiceCoverageTest and extended by updates: every query builder
 * records its sets and its conditions (eq, neq, in as tokens with the values
 * caught by createNamedParameter), executeStatement applies the sets to the
 * array table and answers with the number of matched rows, and executeQuery
 * answers the two selects of requeueAs out of the CURRENT array state. That
 * last word is the point of the whole file: the defect of finding F3 was a
 * dirty list read after the $stale statement had already cleared the mark, so
 * only a simulation whose selects see the effect of earlier updates can tell
 * the fixed order of reads from the broken one.
 */
#[CoversClass(QueueMapper::class)]
final class QueueMapperTest extends TestCase {
	/** The simulated table, file id to row. @var array<int, array<string, mixed>> */
	private array $table = [];

	/** Every row insertIgnoreConflict was asked to create. @var list<array<string, mixed>> */
	private array $inserts = [];

	private function mapper(): QueueMapper {
		$db = $this->createMock(IDBConnection::class);
		$db->method('getQueryBuilder')->willReturnCallback(fn (): IQueryBuilder => $this->queryBuilder());
		$db->method('insertIgnoreConflict')->willReturnCallback(function (string $table, array $values): int {
			$this->inserts[] = $values;
			$fileId = (int)$values['file_id'];
			if (isset($this->table[$fileId])) {
				return 0;
			}
			$this->table[$fileId] = [
				'file_id' => $fileId,
				'kind' => (string)$values['kind'],
				'retries' => 0,
				'dirty' => false,
			];

			return 1;
		});

		return new QueueMapper($db, $this->createMock(ITimeFactory::class));
	}

	private function queryBuilder(): IQueryBuilder {
		$parameters = [];
		$select = [];
		$sets = [];
		$conditions = [];

		$qb = $this->createMock(IQueryBuilder::class);
		$expr = $this->createMock(IExpressionBuilder::class);

		$condition = static function (string $operator, string $column, string $placeholder) use (&$conditions, &$parameters): string {
			$conditions[] = [$operator, $column, $parameters[$placeholder] ?? null];

			return $operator;
		};
		$expr->method('eq')->willReturnCallback(static fn (string $column, mixed $placeholder): string => $condition('eq', $column, (string)$placeholder));
		$expr->method('neq')->willReturnCallback(static fn (string $column, mixed $placeholder): string => $condition('neq', $column, (string)$placeholder));
		$expr->method('in')->willReturnCallback(static fn (string $column, mixed $placeholder): string => $condition('in', $column, (string)$placeholder));

		$qb->method('expr')->willReturn($expr);
		$qb->method('createNamedParameter')->willReturnCallback(static function (mixed $value) use (&$parameters): string {
			$placeholder = ':p' . count($parameters);
			$parameters[$placeholder] = $value;

			return $placeholder;
		});
		$qb->method('select')->willReturnCallback(static function (mixed ...$columns) use (&$select, $qb): IQueryBuilder {
			$select = array_merge($select, array_map(strval(...), $columns));

			return $qb;
		});
		$qb->method('from')->willReturnSelf();
		$qb->method('update')->willReturnSelf();
		$qb->method('set')->willReturnCallback(static function (string $column, mixed $placeholder) use (&$sets, &$parameters, $qb): IQueryBuilder {
			$sets[$column] = $parameters[(string)$placeholder] ?? null;

			return $qb;
		});
		$qb->method('where')->willReturnSelf();
		$qb->method('andWhere')->willReturnSelf();
		$qb->method('executeStatement')->willReturnCallback(function () use (&$sets, &$conditions): int {
			$matched = 0;
			foreach ($this->table as $fileId => $row) {
				if (!self::rowMatches($row, $conditions)) {
					continue;
				}
				foreach ($sets as $column => $value) {
					$row[$column] = $value;
				}
				$this->table[$fileId] = $row;
				$matched++;
			}

			return $matched;
		});
		$qb->method('executeQuery')->willReturnCallback(function () use (&$select, &$conditions): IResult {
			$rows = [];
			foreach ($this->table as $row) {
				if (!self::rowMatches($row, $conditions)) {
					continue;
				}
				$answer = [];
				foreach ($select as $column) {
					$answer[$column] = $row[$column];
				}
				$rows[] = $answer;
			}

			return $this->resultOf($rows);
		});

		return $qb;
	}

	/**
	 * @param array<string, mixed> $row
	 * @param list<array{0: string, 1: string, 2: mixed}> $conditions
	 */
	private static function rowMatches(array $row, array $conditions): bool {
		foreach ($conditions as [$operator, $column, $value]) {
			$actual = $row[$column] ?? null;
			$holds = match ($operator) {
				'in' => in_array($actual, (array)$value, true),
				'eq' => $actual === $value,
				'neq' => $actual !== $value,
				default => false,
			};
			if (!$holds) {
				return false;
			}
		}

		return true;
	}

	/** @param list<array<string, mixed>> $rows */
	private function resultOf(array $rows): IResult {
		$result = $this->createMock(IResult::class);
		$result->method('fetch')->willReturnCallback(static function () use (&$rows): mixed {
			return array_shift($rows) ?? false;
		});
		$result->method('closeCursor')->willReturn(true);

		return $result;
	}

	private function row(int $fileId, string $kind, bool $dirty, int $retries): void {
		$this->table[$fileId] = [
			'file_id' => $fileId,
			'kind' => $kind,
			'retries' => $retries,
			'dirty' => $dirty,
		];
	}

	public function testTheAnswerCountsNoRowThatWasOnlyHandedBack(): void {
		$this->row(1, QueueMapper::KIND_CONTENT, false, 2);
		$this->row(2, QueueMapper::KIND_CONTENT, true, 1);

		$requeued = $this->mapper()->requeueAs([1, 2], QueueMapper::KIND_OCR);

		// File 2 was dirty, so it was handed back where it is and does not
		// carry ocr because of this call. An answer of 2 is the F3 defect:
		// the dirty list was read after the $stale statement had cleared the
		// very mark it asks for, and was therefore always empty.
		self::assertSame(1, $requeued);

		self::assertSame(QueueMapper::KIND_OCR, $this->table[1]['kind']);
		self::assertSame(0, $this->table[1]['retries']);
		self::assertFalse($this->table[1]['dirty']);

		self::assertSame(QueueMapper::KIND_CONTENT, $this->table[2]['kind']);
		self::assertSame(0, $this->table[2]['retries']);
		self::assertFalse($this->table[2]['dirty']);
	}

	public function testADeleteRowIsNeitherMovedNorCounted(): void {
		$this->row(3, QueueMapper::KIND_DELETE, false, 1);
		$before = $this->table[3];

		$requeued = $this->mapper()->requeueAs([3], QueueMapper::KIND_OCR);

		self::assertSame(0, $requeued);
		self::assertSame($before, $this->table[3]);
		self::assertSame([], $this->inserts);
	}

	public function testAMissingRowIsCreatedWithTheKindAndCounted(): void {
		$requeued = $this->mapper()->requeueAs([9], QueueMapper::KIND_OCR);

		self::assertSame(1, $requeued);
		self::assertCount(1, $this->inserts);
		self::assertSame(9, $this->inserts[0]['file_id']);
		self::assertSame(QueueMapper::KIND_OCR, $this->inserts[0]['kind']);
		self::assertSame(0, $this->inserts[0]['storage_id']);
	}
}
