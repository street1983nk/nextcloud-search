<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use Closure;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Migration\Version001300Date20260927000000;
use OCP\DB\IResult;
use OCP\DB\QueryBuilder\IExpressionBuilder;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\IDBConnection;
use OCP\Migration\IOutput;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;

/**
 * The gone repair of issue #14, and the rows it must leave alone (D-04).
 *
 * Before 257caac the container judged a Team Folder file gone whenever the one
 * reader it had picked could not reach it, and those verdicts sit in
 * findling_file_state as skipped(gone). This migration hands every such file
 * back to the content track once and deletes its verdict, band by band, each
 * band in one transaction.
 *
 * The cases hold what the plan names as properties rather than beliefs: an
 * empty table is a quiet no-op, the query and the delete select skipped AND
 * gone and nothing else, a failure inside a band rolls that band back and is
 * thrown on, 2500 rows are three bands, a second run is a no-op, the migration
 * is handed nothing that could reach the container, and the schema stays
 * untouched.
 *
 * The database is doubled at the query builder, in the shape of
 * PathResolverServiceTest: every builder records the kind of statement, the
 * columns it compared and the parameters it bound, and a SELECT answers out of
 * a list staged by the test, one answer per query in the order they are asked.
 */
#[CoversClass(Version001300Date20260927000000::class)]
final class Version001300Date20260927000000Test extends TestCase {
	private IDBConnection&MockObject $db;
	private QueueMapper&MockObject $queueMapper;

	/**
	 * What the SELECTs answer, in order. A query nobody staged answers
	 * nothing, which is the state of a fresh instance.
	 *
	 * @var list<list<array<string, mixed>>>
	 */
	private array $answers = [];

	/**
	 * One entry per builder that ran: its statement kind, the columns its
	 * conditions compared and the parameters it bound.
	 *
	 * @var list<array{kind: string, columns: list<string>, params: list<mixed>}>
	 */
	private array $statements = [];

	/** The order things happened in, across the database and the mapper. @var list<string> */
	private array $events = [];

	protected function setUp(): void {
		parent::setUp();

		$this->db = $this->createMock(IDBConnection::class);
		$this->queueMapper = $this->createMock(QueueMapper::class);

		$this->db->method('beginTransaction')->willReturnCallback(function (): void {
			$this->events[] = 'begin';
		});
		$this->db->method('commit')->willReturnCallback(function (): void {
			$this->events[] = 'commit';
		});
		$this->db->method('rollBack')->willReturnCallback(function (): void {
			$this->events[] = 'rollBack';
		});

		$this->db->method('getQueryBuilder')->willReturnCallback(function (): IQueryBuilder {
			$record = ['kind' => '', 'columns' => [], 'params' => []];

			$expr = $this->createMock(IExpressionBuilder::class);
			$expr->method('eq')->willReturnCallback(function (string $column, mixed $param) use (&$record): string {
				$record['columns'][] = $column;

				return $column . ' = ' . (string)$param;
			});
			$expr->method('in')->willReturnCallback(function (string $column, mixed $param) use (&$record): string {
				$record['columns'][] = $column;

				return $column . ' IN ' . (string)$param;
			});

			$qb = $this->createMock(IQueryBuilder::class);
			$qb->method('select')->willReturnCallback(function () use ($qb, &$record): IQueryBuilder {
				$record['kind'] = 'select';

				return $qb;
			});
			$qb->method('delete')->willReturnCallback(function () use ($qb, &$record): IQueryBuilder {
				$record['kind'] = 'delete';

				return $qb;
			});
			$qb->method('from')->willReturnSelf();
			$qb->method('where')->willReturnSelf();
			$qb->method('andWhere')->willReturnSelf();
			$qb->method('orderBy')->willReturnSelf();
			$qb->method('expr')->willReturn($expr);
			$qb->method('createNamedParameter')->willReturnCallback(function (mixed $value) use (&$record): string {
				$record['params'][] = $value;

				return ':p' . count($record['params']);
			});
			$qb->method('executeQuery')->willReturnCallback(function () use (&$record): IResult {
				$this->statements[] = $record;
				$result = $this->createMock(IResult::class);
				$result->method('fetchAll')->willReturn(array_shift($this->answers) ?? []);

				return $result;
			});
			$qb->method('executeStatement')->willReturnCallback(function () use (&$record): int {
				$this->statements[] = $record;
				$this->events[] = 'delete';

				return 0;
			});

			return $qb;
		});
	}

	private function schemaClosure(): Closure {
		// The signature wants one and this migration never calls it. A closure
		// that fails loudly says so: if a later edit starts touching the schema
		// here, this test has to be where that is noticed.
		return static function (): never {
			self::fail('this migration must not touch the schema');
		};
	}

	/**
	 * @param list<int> $fileIds
	 */
	private function stage(array $fileIds): void {
		$this->answers[] = array_map(static fn (int $fileId): array => ['file_id' => $fileId], $fileIds);
	}

	private function migration(): Version001300Date20260927000000 {
		return new Version001300Date20260927000000($this->db, $this->queueMapper);
	}

	/**
	 * @return list<array{kind: string, columns: list<string>, params: list<mixed>}>
	 */
	private function statementsOf(string $kind): array {
		return array_values(array_filter($this->statements, static fn (array $s): bool => $s['kind'] === $kind));
	}

	public function testAnEmptyTableIsAQuietNoOp(): void {
		// Every fresh installation, and every instance that never ran into
		// issue #14. Nothing to requeue, no transaction opened for nothing.
		$this->queueMapper->expects(self::never())->method('requeueAs');
		$this->db->expects(self::never())->method('beginTransaction');

		$output = $this->createMock(IOutput::class);
		$output->expects(self::once())
			->method('info')
			->with('no gone verdicts to repair');

		$this->migration()->postSchemaChange($output, $this->schemaClosure(), []);

		self::assertSame([], $this->statementsOf('delete'));
	}

	public function testGoneFilesAreRequeuedAsContentAndTheirVerdictsDeleted(): void {
		$this->stage([11, 12, 13]);

		$this->queueMapper->expects(self::once())
			->method('requeueAs')
			->with([11, 12, 13], QueueMapper::KIND_CONTENT)
			->willReturnCallback(function (): int {
				$this->events[] = 'requeue';

				return 3;
			});
		$this->db->expects(self::once())->method('commit');
		$this->db->expects(self::never())->method('rollBack');

		$output = $this->createMock(IOutput::class);
		$output->expects(self::once())
			->method('info')
			->with('requeued 3 files once judged gone');

		$this->migration()->postSchemaChange($output, $this->schemaClosure(), []);

		// Requeue and delete inside one transaction, in that order.
		self::assertSame(['begin', 'requeue', 'delete', 'commit'], $this->events);

		$deletes = $this->statementsOf('delete');
		self::assertCount(1, $deletes);
		self::assertSame(['state', 'reason', 'file_id'], $deletes[0]['columns']);
		self::assertSame(['skipped', 'gone', [11, 12, 13]], $deletes[0]['params']);
	}

	public function testOnlySkippedGoneIsSelectedAndOtherReasonsStay(): void {
		// unreadable, too_large, no_text_layer and every failed verdict are
		// decisions this repair has no business with. The SELECT binds exactly
		// skipped and gone, and the DELETE repeats both, so a row that is not
		// skipped(gone) is neither requeued nor deleted.
		$this->stage([21]);
		$this->queueMapper->method('requeueAs')->willReturn(1);

		$this->migration()->postSchemaChange($this->createMock(IOutput::class), $this->schemaClosure(), []);

		$selects = $this->statementsOf('select');
		self::assertCount(1, $selects);
		self::assertSame(['state', 'reason'], $selects[0]['columns']);
		self::assertSame(['skipped', 'gone'], $selects[0]['params']);

		foreach ($this->statementsOf('delete') as $delete) {
			self::assertContains('skipped', $delete['params']);
			self::assertContains('gone', $delete['params']);
			self::assertNotContains('unreadable', $delete['params']);
			self::assertNotContains('too_large', $delete['params']);
			self::assertNotContains('failed', $delete['params']);
		}
	}

	public function testAFailureInsideABandRollsItBackAndIsThrownOn(): void {
		// Half a band would be the worst outcome: files requeued whose verdict
		// still says gone, or verdicts deleted for files nobody requeued.
		$this->stage([31, 32]);

		$this->queueMapper->method('requeueAs')->willThrowException(new \RuntimeException('database went away'));
		$this->db->expects(self::once())->method('beginTransaction');
		$this->db->expects(self::once())->method('rollBack');
		$this->db->expects(self::never())->method('commit');

		$this->expectException(\RuntimeException::class);
		$this->expectExceptionMessage('database went away');

		try {
			$this->migration()->postSchemaChange($this->createMock(IOutput::class), $this->schemaClosure(), []);
		} finally {
			self::assertSame([], $this->statementsOf('delete'), 'a verdict was deleted although its requeue failed');
		}
	}

	public function testTwentyFiveHundredRowsAreThreeBandsInThreeTransactions(): void {
		// The band exists for the ceilings on bound parameters, and each band
		// is its own transaction so a large instance never holds one lock for
		// the whole repair.
		$this->stage(range(1, 2500));

		$sizes = [];
		$this->queueMapper->expects(self::exactly(3))
			->method('requeueAs')
			->willReturnCallback(function (array $band, string $kind) use (&$sizes): int {
				self::assertSame(QueueMapper::KIND_CONTENT, $kind);
				$sizes[] = count($band);

				return count($band);
			});
		$this->db->expects(self::exactly(3))->method('beginTransaction');
		$this->db->expects(self::exactly(3))->method('commit');

		$output = $this->createMock(IOutput::class);
		$output->expects(self::once())
			->method('info')
			->with('requeued 2500 files once judged gone');

		$this->migration()->postSchemaChange($output, $this->schemaClosure(), []);

		self::assertSame([1000, 1000, 500], $sizes);

		$deletes = $this->statementsOf('delete');
		self::assertCount(3, $deletes);
		self::assertSame(range(1, 1000), $deletes[0]['params'][2]);
		self::assertSame(range(1001, 2000), $deletes[1]['params'][2]);
		self::assertSame(range(2001, 2500), $deletes[2]['params'][2]);
	}

	public function testASecondRunIsANoOpAndThrowsNothing(): void {
		// Nextcloud can replay a migration after a failed upgrade. The first
		// run deleted every gone row, so the second finds nothing and says so.
		$this->answers = [[['file_id' => 41]], []];

		$this->queueMapper->expects(self::once())->method('requeueAs')->willReturn(1);

		$output = $this->createMock(IOutput::class);
		$output->expects(self::exactly(2))->method('info');

		$migration = $this->migration();
		$migration->postSchemaChange($output, $this->schemaClosure(), []);
		$migration->postSchemaChange($output, $this->schemaClosure(), []);

		self::assertCount(1, $this->statementsOf('delete'));
	}

	public function testTheMigrationAsksTheContainerForNothing(): void {
		// A migration runs in maintenance mode, without a logged in user, and
		// possibly while AppAPI is restarting the container. It can only reach
		// the container through a collaborator it was handed, so the honest
		// place to check that it reaches nothing is the constructor: two
		// parameters, the database and the queue.
		$constructor = (new \ReflectionClass(Version001300Date20260927000000::class))->getConstructor();

		self::assertNotNull($constructor);

		$parameters = $constructor->getParameters();

		self::assertCount(2, $parameters, 'the migration was handed a third collaborator');

		$types = array_map(static function (\ReflectionParameter $parameter): string {
			$type = $parameter->getType();
			self::assertInstanceOf(\ReflectionNamedType::class, $type);

			return $type->getName();
		}, $parameters);

		self::assertSame([IDBConnection::class, QueueMapper::class], $types);
	}

	public function testTheSchemaIsLeftAlone(): void {
		// changeSchema is not overridden, so the inherited one answers null and
		// never calls the closure. The closure fails the test if it is called.
		$migration = $this->migration();

		self::assertNull($migration->changeSchema($this->createMock(IOutput::class), $this->schemaClosure(), []));

		$this->stage([51]);
		$this->queueMapper->method('requeueAs')->willReturn(1);
		$migration->postSchemaChange($this->createMock(IOutput::class), $this->schemaClosure(), []);
	}
}
