<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\FileStateService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\DB\IResult;
use OCP\DB\QueryBuilder\ICompositeExpression;
use OCP\DB\QueryBuilder\IExpressionBuilder;
use OCP\DB\QueryBuilder\IFunctionBuilder;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\DB\QueryBuilder\IQueryFunction;
use OCP\IDBConnection;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The two sources of the per document denominator on the PHP side (plan 43-05,
 * D-43-11, finding B1).
 *
 * countByReasonPerStorage() counts refused files per storage and only over the
 * storages it is given, in bands of STORAGE_BAND. distinctPathsByReasons()
 * counts the documents only PHP judged (skipped/unreadable,
 * failed/repeatedly_stuck, skipped/gone) per share group by internal path, so a
 * file no member can read is one document, and drops a path that another
 * member of the group holds without such a verdict (N1).
 *
 * The database is a small fake: every query records its table, its selected
 * columns, its joins and the lists of its IN conditions, and answers out of
 * rows given per kind of query. A forgotten band, a missing storage condition
 * or a join on the wrong table shows up as a wrong count or a failed assertion.
 */
#[CoversClass(FileStateService::class)]
final class FileStateServiceCoverageTest extends TestCase {
	/** @var list<array{from: string, select: list<string>, joins: list<array{0: string, 1: string}>, in: array<string, list<mixed>>, grouped: bool}> */
	private array $queries = [];

	/** Rows of the per storage count: storage => total. @var array<int, int> */
	private array $perStorage = [];

	/** Rows of the PHP only verdicts. @var list<array{storage: int, path_hash: string, state: string, reason: string}> */
	private array $phpOnly = [];

	/** Path hashes a member holds without a PHP only verdict, per storage. @var array<int, list<string>> */
	private array $heldWithoutVerdict = [];

	private function service(): FileStateService {
		$db = $this->createMock(IDBConnection::class);
		$db->method('getQueryBuilder')->willReturnCallback(fn (): IQueryBuilder => $this->queryBuilder());

		return new FileStateService($db, $this->createMock(ITimeFactory::class), $this->createMock(LoggerInterface::class));
	}

	private function queryBuilder(): IQueryBuilder {
		$query = ['from' => '', 'select' => [], 'joins' => [], 'in' => [], 'grouped' => false];
		$parameters = [];

		$qb = $this->createMock(IQueryBuilder::class);
		$expr = $this->createMock(IExpressionBuilder::class);
		$functions = $this->createMock(IFunctionBuilder::class);
		$functions->method('count')->willReturn($this->createMock(IQueryFunction::class));

		$expr->method('eq')->willReturn('eq');
		$expr->method('notLike')->willReturn('notLike');
		$expr->method('isNull')->willReturn('isNull');
		$expr->method('andX')->willReturn($this->createMock(ICompositeExpression::class));
		$expr->method('orX')->willReturn($this->createMock(ICompositeExpression::class));
		$expr->method('in')->willReturnCallback(static function (string $column, mixed $placeholder) use (&$query, &$parameters): string {
			$query['in'][$column] = $parameters[$placeholder] ?? null;

			return 'in';
		});

		$qb->method('expr')->willReturn($expr);
		$qb->method('func')->willReturn($functions);
		$qb->method('createNamedParameter')->willReturnCallback(static function (mixed $value) use (&$parameters): string {
			$placeholder = ':p' . count($parameters);
			$parameters[$placeholder] = $value;

			return $placeholder;
		});
		$qb->method('select')->willReturnCallback(static function (mixed ...$columns) use (&$query, $qb): IQueryBuilder {
			$query['select'] = array_merge($query['select'], array_map(strval(...), $columns));

			return $qb;
		});
		$qb->method('selectAlias')->willReturnSelf();
		$qb->method('from')->willReturnCallback(static function (string $table) use (&$query, $qb): IQueryBuilder {
			$query['from'] = $table;

			return $qb;
		});
		$qb->method('innerJoin')->willReturnCallback(static function (string $from, string $table) use (&$query, $qb): IQueryBuilder {
			$query['joins'][] = ['inner', $table];

			return $qb;
		});
		$qb->method('leftJoin')->willReturnCallback(static function (string $from, string $table) use (&$query, $qb): IQueryBuilder {
			$query['joins'][] = ['left', $table];

			return $qb;
		});
		$qb->method('where')->willReturnSelf();
		$qb->method('andWhere')->willReturnSelf();
		$qb->method('groupBy')->willReturnCallback(static function () use (&$query, $qb): IQueryBuilder {
			$query['grouped'] = true;

			return $qb;
		});
		$qb->method('executeQuery')->willReturnCallback(function () use (&$query): IResult {
			$this->queries[] = $query;

			return $this->resultOf($this->answer($query));
		});

		return $qb;
	}

	/**
	 * @param array{from: string, select: list<string>, joins: list<array{0: string, 1: string}>, in: array<string, list<mixed>>, grouped: bool} $query
	 * @return list<array<string, mixed>>
	 */
	private function answer(array $query): array {
		$storages = array_map(intval(...), (array)($query['in']['fc.storage'] ?? []));
		if ($query['grouped']) {
			$rows = [];
			foreach ($storages as $storageId) {
				if (isset($this->perStorage[$storageId])) {
					$rows[] = ['storage' => (string)$storageId, 'total' => (string)$this->perStorage[$storageId]];
				}
			}

			return $rows;
		}
		if ($query['from'] === FileStateService::TABLE_NAME) {
			return array_values(array_filter(
				$this->phpOnly,
				static fn (array $row): bool => in_array($row['storage'], $storages, true),
			));
		}
		if ($query['from'] === 'filecache') {
			$hashes = (array)($query['in']['fc.path_hash'] ?? []);
			$rows = [];
			foreach ($storages as $storageId) {
				foreach ($this->heldWithoutVerdict[$storageId] ?? [] as $hash) {
					if (in_array($hash, $hashes, true)) {
						$rows[] = ['path_hash' => $hash];
					}
				}
			}

			return $rows;
		}

		self::fail('a query of an unexpected shape');
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

	private function verdict(int $storageId, string $hash, string $state, string $reason): void {
		$this->phpOnly[] = ['storage' => $storageId, 'path_hash' => $hash, 'state' => $state, 'reason' => $reason];
	}

	// -- countByReasonPerStorage ------------------------------------------------

	public function testTwentyFiveHundredStoragesAreAskedInThreeBands(): void {
		$this->perStorage = [1 => 2, 1500 => 3, 2500 => 4];

		$counts = $this->service()->countByReasonPerStorage('skipped', 'mime_not_allowed', range(1, 2500));

		self::assertCount(3, $this->queries);
		self::assertSame([1000, 1000, 500], array_map(static fn (array $query): int => count($query['in']['fc.storage']), $this->queries));
		self::assertSame([1 => 2, 1500 => 3, 2500 => 4], $counts);
	}

	public function testEveryPerStorageQueryNamesItsStoragesAndJoinsTheFileCache(): void {
		$this->service()->countByReasonPerStorage('skipped', 'mime_not_allowed', [3, 4]);

		self::assertCount(1, $this->queries);
		self::assertSame([3, 4], $this->queries[0]['in']['fc.storage']);
		self::assertContains(['inner', 'filecache'], $this->queries[0]['joins']);
		self::assertTrue($this->queries[0]['grouped']);
	}

	public function testAnEmptyListOrOnlyInvalidIdsAskNothing(): void {
		self::assertSame([], $this->service()->countByReasonPerStorage('skipped', 'mime_not_allowed', []));
		self::assertSame([], $this->service()->countByReasonPerStorage('skipped', 'mime_not_allowed', [0, -3]));

		self::assertSame([], $this->queries);
	}

	public function testAPairOutsideTheClosedListsIsRejectedWithoutAQuery(): void {
		self::assertSame([], $this->service()->countByReasonPerStorage('skipped', 'no_such_reason', [1]));

		self::assertSame([], $this->queries);
	}

	// -- distinctPathsByReasons -------------------------------------------------

	/** The PHP only rows of backend/tests/fixtures/coverage_topology.json, group 0 and the single storages. */
	private function topology(): void {
		// u1: unreadable for every member, one row each, one document.
		$this->verdict(11, 'u1', 'skipped', 'unreadable');
		$this->verdict(12, 'u1', 'skipped', 'unreadable');
		$this->verdict(13, 'u1', 'skipped', 'unreadable');
		$this->verdict(12, 'st1', 'failed', 'repeatedly_stuck');
		$this->verdict(11, 'g1', 'skipped', 'gone');
		// N1: carl cannot read it, anna holds it without such a verdict.
		$this->verdict(13, 'n-a12', 'skipped', 'unreadable');
		$this->heldWithoutVerdict[11] = ['n-a12'];
		$this->verdict(22, 'u2', 'skipped', 'unreadable');
		$this->verdict(31, 'st2', 'failed', 'repeatedly_stuck');
		$this->verdict(32, 'u3', 'skipped', 'unreadable');
		$this->verdict(41, 'u4', 'skipped', 'unreadable');
	}

	public function testTheTopologyGivesTheHandDerivedPhpOnlyFigures(): void {
		$this->topology();

		$answer = $this->service()->distinctPathsByReasons([[11, 12, 13], [21, 22]], [31, 32, 33]);

		self::assertSame([3, 1], $answer['byGroup']);
		self::assertSame([2, 1], $answer['notReadableByGroup']);
		self::assertSame([31 => 1, 32 => 1], $answer['byStorage']);
		self::assertSame([31 => 1, 32 => 1], $answer['notReadableByStorage']);
	}

	public function testUnreadableForOneMemberIndexedForAnotherCountsOnceAndIsNotInNotReadable(): void {
		$this->verdict(13, 'n-a12', 'skipped', 'unreadable');
		$this->heldWithoutVerdict[11] = ['n-a12'];

		$answer = $this->service()->distinctPathsByReasons([[11, 12, 13]], []);

		// The container counts it over member 11 (judged); here it is neither
		// a PHP only document nor not readable.
		self::assertSame([0], $answer['byGroup']);
		self::assertSame([0], $answer['notReadableByGroup']);
	}

	public function testTheN1CheckRunsOverTheMembersOfTheSameGroupOnly(): void {
		$this->verdict(13, 'h', 'skipped', 'unreadable');
		$this->verdict(22, 'k', 'skipped', 'unreadable');
		// 21 holds 'h' without a verdict, but 21 is in another group.
		$this->heldWithoutVerdict[21] = ['h'];

		$answer = $this->service()->distinctPathsByReasons([[11, 12, 13], [21, 22]], [31]);

		self::assertSame([1, 1], $answer['byGroup']);
		$checks = array_values(array_filter($this->queries, static fn (array $query): bool => $query['from'] === 'filecache'));
		self::assertCount(2, $checks);
		self::assertSame([11, 12, 13], $checks[0]['in']['fc.storage']);
		self::assertSame(['h'], $checks[0]['in']['fc.path_hash']);
		self::assertSame([21, 22], $checks[1]['in']['fc.storage']);
		self::assertContains(['left', FileStateService::TABLE_NAME], $checks[0]['joins']);
	}

	public function testEveryQueryOfThePhpOnlyCountNamesItsStorages(): void {
		$this->topology();

		$this->service()->distinctPathsByReasons([[11, 12, 13], [21, 22]], [31, 32]);

		self::assertNotSame([], $this->queries);
		foreach ($this->queries as $query) {
			self::assertIsArray($query['in']['fc.storage'] ?? null);
			self::assertNotSame([], $query['in']['fc.storage']);
		}
		$verdicts = array_values(array_filter($this->queries, static fn (array $query): bool => $query['from'] === FileStateService::TABLE_NAME));
		// W-b: the verdicts are read through an inner join on the file cache,
		// so a verdict whose file left Nextcloud counts nowhere.
		self::assertContains(['inner', 'filecache'], $verdicts[0]['joins']);
		self::assertNotContains(41, $verdicts[0]['in']['fc.storage']);
	}

	public function testTwentyFiveHundredSingleStoragesAreAskedInThreeBands(): void {
		$this->service()->distinctPathsByReasons([], range(1, 2500));

		self::assertSame([1000, 1000, 500], array_map(static fn (array $query): int => count($query['in']['fc.storage']), $this->queries));
	}

	public function testASingleStorageNeedsNoN1Check(): void {
		$this->verdict(31, 'a', 'skipped', 'unreadable');
		$this->verdict(31, 'b', 'skipped', 'gone');

		$answer = $this->service()->distinctPathsByReasons([], [31]);

		self::assertSame([31 => 2], $answer['byStorage']);
		self::assertSame([31 => 1], $answer['notReadableByStorage']);
		self::assertSame([], array_filter($this->queries, static fn (array $query): bool => $query['from'] === 'filecache'));
	}

	public function testTheAnswerCarriesCountsOnly(): void {
		$this->topology();

		$answer = $this->service()->distinctPathsByReasons([[11, 12, 13], [21, 22]], [31, 32]);

		array_walk_recursive($answer, static function (mixed $value, mixed $key): void {
			self::assertIsInt($value);
			self::assertIsInt($key);
		});
	}

	public function testNothingToAskAsksNothing(): void {
		$answer = $this->service()->distinctPathsByReasons([], []);

		self::assertSame(['byGroup' => [], 'byStorage' => [], 'notReadableByGroup' => [], 'notReadableByStorage' => []], $answer);
		self::assertSame([], $this->queries);
	}
}
