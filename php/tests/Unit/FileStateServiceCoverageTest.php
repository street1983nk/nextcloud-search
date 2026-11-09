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
 * failed/repeatedly_stuck, skipped/gone) per share group by document key over
 * the share path (plan 43-23), so a file no member can read is one document
 * whatever root or spelling of the share a member was configured with, and
 * drops a document that another member holds under its own path below its
 * root without such a verdict (N1 per member).
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

	/** Rows of the PHP only verdicts. @var list<array{storage: int, path: string, path_hash: string, state: string, reason: string}> */
	private array $phpOnly = [];

	/** Internal paths a member holds without a PHP only verdict, per storage. @var array<int, list<string>> */
	private array $heldWithoutVerdict = [];

	private const SHARE = 'smb::fs.example//daten';

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
				foreach ($this->heldWithoutVerdict[$storageId] ?? [] as $path) {
					if (in_array(md5($path), $hashes, true)) {
						$rows[] = ['path_hash' => md5($path)];
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

	/** A PHP only verdict on an internal path; path_hash is its md5, as Cache.php writes it. */
	private function verdict(int $storageId, string $path, string $state, string $reason): void {
		$this->phpOnly[] = ['storage' => $storageId, 'path' => $path, 'path_hash' => md5($path), 'state' => $state, 'reason' => $reason];
	}

	/**
	 * One identity per storage of the share SHARE, all with the root ''
	 * unless named.
	 *
	 * @param list<int> $storageIds
	 * @param array<int, string> $roots
	 * @return array<int, array{share: string, root: string}>
	 */
	private static function identities(array $storageIds, array $roots = [], string $share = self::SHARE): array {
		$identities = [];
		foreach ($storageIds as $storageId) {
			$identities[$storageId] = ['share' => $share, 'root' => $roots[$storageId] ?? ''];
		}

		return $identities;
	}

	/** The identities of the main topology: two shares, every root ''. @return array<int, array{share: string, root: string}> */
	private static function mainIdentities(): array {
		return self::identities([11, 12, 13]) + self::identities([21, 22], [], 'smb::fs.example//archiv');
	}

	/** @return list<array<string, mixed>> */
	private function fileCacheChecks(): array {
		return array_values(array_filter($this->queries, static fn (array $query): bool => $query['from'] === 'filecache'));
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
		$this->verdict(11, 'x/u1.txt', 'skipped', 'unreadable');
		$this->verdict(12, 'x/u1.txt', 'skipped', 'unreadable');
		$this->verdict(13, 'x/u1.txt', 'skipped', 'unreadable');
		$this->verdict(12, 'x/st1.txt', 'failed', 'repeatedly_stuck');
		$this->verdict(11, 'x/g1.txt', 'skipped', 'gone');
		// N1: carl cannot read it, anna holds it without such a verdict.
		$this->verdict(13, 'n/a12.txt', 'skipped', 'unreadable');
		$this->heldWithoutVerdict[11] = ['n/a12.txt'];
		$this->verdict(22, 'b/u2.txt', 'skipped', 'unreadable');
		$this->verdict(31, 'files/Dokumente/st2.txt', 'failed', 'repeatedly_stuck');
		$this->verdict(32, 'files/u3.txt', 'skipped', 'unreadable');
		$this->verdict(41, 'u4.txt', 'skipped', 'unreadable');
	}

	public function testTheTopologyGivesTheHandDerivedPhpOnlyFigures(): void {
		$this->topology();

		$answer = $this->service()->distinctPathsByReasons([[11, 12, 13], [21, 22]], [31, 32, 33], self::mainIdentities());

		self::assertSame([3, 1], $answer['byGroup']);
		self::assertSame([2, 1], $answer['notReadableByGroup']);
		self::assertSame([31 => 1, 32 => 1], $answer['byStorage']);
		self::assertSame([31 => 1, 32 => 1], $answer['notReadableByStorage']);
	}

	public function testUnreadableForOneMemberIndexedForAnotherCountsOnceAndIsNotInNotReadable(): void {
		$this->verdict(13, 'n/a12.txt', 'skipped', 'unreadable');
		$this->heldWithoutVerdict[11] = ['n/a12.txt'];

		$answer = $this->service()->distinctPathsByReasons([[11, 12, 13]], [], self::identities([11, 12, 13]));

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

		$answer = $this->service()->distinctPathsByReasons([[11, 12, 13], [21, 22]], [31], self::mainIdentities());

		self::assertSame([1, 1], $answer['byGroup']);
		$checks = $this->fileCacheChecks();
		self::assertCount(2, $checks);
		self::assertSame([11, 12, 13], $checks[0]['in']['fc.storage']);
		self::assertSame([md5('h')], $checks[0]['in']['fc.path_hash']);
		self::assertSame([21, 22], $checks[1]['in']['fc.storage']);
		self::assertContains(['left', FileStateService::TABLE_NAME], $checks[0]['joins']);
	}

	public function testEveryQueryOfThePhpOnlyCountNamesItsStorages(): void {
		$this->topology();

		$this->service()->distinctPathsByReasons([[11, 12, 13], [21, 22]], [31, 32], self::mainIdentities());

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
		// The share path is built from the internal path, so the query reads it.
		self::assertContains('fc.path', $verdicts[0]['select']);
	}

	public function testTwentyFiveHundredSingleStoragesAreAskedInThreeBands(): void {
		$this->service()->distinctPathsByReasons([], range(1, 2500), []);

		self::assertSame([1000, 1000, 500], array_map(static fn (array $query): int => count($query['in']['fc.storage']), $this->queries));
	}

	public function testASingleStorageNeedsNoN1Check(): void {
		$this->verdict(31, 'a', 'skipped', 'unreadable');
		$this->verdict(31, 'b', 'skipped', 'gone');

		$answer = $this->service()->distinctPathsByReasons([], [31], []);

		self::assertSame([31 => 2], $answer['byStorage']);
		self::assertSame([31 => 1], $answer['notReadableByStorage']);
		self::assertSame([], $this->fileCacheChecks());
	}

	public function testASingleStorageCountsPerStorageWhateverItsIdentity(): void {
		// Two single storages with the same internal path and even an identity
		// stay two documents: a single storage is counted per storage.
		$this->verdict(31, 'a.txt', 'skipped', 'unreadable');
		$this->verdict(32, 'a.txt', 'skipped', 'unreadable');

		$answer = $this->service()->distinctPathsByReasons([], [31, 32], self::identities([31, 32]));

		self::assertSame([31 => 1, 32 => 1], $answer['byStorage']);
	}

	public function testTheAnswerCarriesCountsOnly(): void {
		$this->topology();

		$answer = $this->service()->distinctPathsByReasons([[11, 12, 13], [21, 22]], [31, 32], self::mainIdentities());

		array_walk_recursive($answer, static function (mixed $value, mixed $key): void {
			self::assertIsInt($value);
			self::assertIsInt($key);
		});
	}

	public function testNothingToAskAsksNothing(): void {
		$answer = $this->service()->distinctPathsByReasons([], [], []);

		self::assertSame(['byGroup' => [], 'byStorage' => [], 'notReadableByGroup' => [], 'notReadableByStorage' => []], $answer);
		self::assertSame([], $this->queries);
	}

	// -- one share under several roots and spellings (plan 43-23, D-43-15, D-43-17)

	public function testOneUnreadableFileUnderTwoRootsIsOneDocument(): void {
		// /Daten holds it as projekt/x, /Daten/projekt as x: one share path.
		$this->verdict(11, 'projekt/x', 'skipped', 'unreadable');
		$this->verdict(14, 'x', 'skipped', 'unreadable');

		$answer = $this->service()->distinctPathsByReasons([[11, 14]], [], self::identities([11, 14], [14 => 'projekt']));

		self::assertSame([1], $answer['byGroup']);
		self::assertSame([1], $answer['notReadableByGroup']);
	}

	public function testTwoFilesWithOneInternalPathUnderTwoRootsStayTwoDocuments(): void {
		// The control: x at the top of the share and x below projekt.
		$this->verdict(11, 'x', 'skipped', 'unreadable');
		$this->verdict(14, 'x', 'skipped', 'unreadable');

		$answer = $this->service()->distinctPathsByReasons([[11, 14]], [], self::identities([11, 14], [14 => 'projekt']));

		self::assertSame([2], $answer['byGroup']);
	}

	public function testN1ForAMemberUnderARootAsksThePathBelowItsRoot(): void {
		// Unreadable for anna as projekt/x, indexed for dora, whose root is
		// projekt, under x.
		$this->verdict(11, 'projekt/x', 'skipped', 'unreadable');
		$this->heldWithoutVerdict[14] = ['x'];

		$answer = $this->service()->distinctPathsByReasons([[11, 14]], [], self::identities([11, 14], [14 => 'projekt']));

		self::assertSame([0], $answer['byGroup']);
		$asked = [];
		foreach ($this->fileCacheChecks() as $check) {
			foreach ($check['in']['fc.storage'] as $storageId) {
				$asked[$storageId] = array_merge($asked[$storageId] ?? [], $check['in']['fc.path_hash']);
			}
		}
		self::assertSame([md5('x')], $asked[14]);
		self::assertSame([md5('projekt/x')], $asked[11]);
	}

	public function testN1ForAMemberAtTheTopFindsAFileOfAMemberUnderARoot(): void {
		$this->verdict(14, 'n6.txt', 'skipped', 'unreadable');
		$this->heldWithoutVerdict[11] = ['projekt/n6.txt'];

		$answer = $this->service()->distinctPathsByReasons([[11, 14]], [], self::identities([11, 14], [14 => 'projekt']));

		self::assertSame([0], $answer['byGroup']);
	}

	public function testAMemberWhoseRootDoesNotHoldThePathIsNotAsked(): void {
		$this->verdict(11, 'projekt/x', 'skipped', 'unreadable');
		$this->verdict(11, 'projekt2/y', 'skipped', 'unreadable');
		// archiv-alt cannot see projekt/x, and projekt2 is not below projekt.
		$this->heldWithoutVerdict[16] = ['x', 'projekt/x'];

		$answer = $this->service()->distinctPathsByReasons(
			[[11, 14, 16]],
			[],
			self::identities([11, 14, 16], [14 => 'projekt', 16 => 'archiv-alt']),
		);

		self::assertSame([2], $answer['byGroup']);
		foreach ($this->fileCacheChecks() as $check) {
			self::assertNotContains(16, $check['in']['fc.storage']);
			if (in_array(14, $check['in']['fc.storage'], true)) {
				self::assertSame([md5('x')], $check['in']['fc.path_hash']);
			}
		}
	}

	public function testTheSpellingOfTheShareChangesNothing(): void {
		// 15 is the share spelled DATEN; its identity is the folded share.
		$this->verdict(14, 's8.txt', 'failed', 'repeatedly_stuck');
		$this->verdict(15, 'projekt/s8.txt', 'failed', 'repeatedly_stuck');

		$answer = $this->service()->distinctPathsByReasons([[14, 15]], [], self::identities([14, 15], [14 => 'projekt']));

		self::assertSame([1], $answer['byGroup']);
		self::assertSame([1], $answer['notReadableByGroup']);
	}

	public function testAMemberWithoutIdentityIsCountedAndCheckedOnItsOwn(): void {
		// Groups come out of identities, so this cannot happen; should it, the
		// member never merges with another one (the leading rule of 43-21).
		$this->verdict(11, 'x', 'skipped', 'unreadable');
		$this->verdict(17, 'x', 'skipped', 'unreadable');
		$this->heldWithoutVerdict[12] = ['x'];

		$answer = $this->service()->distinctPathsByReasons([[11, 12, 17]], [], self::identities([11, 12]));

		// 11 is dropped by N1 over 12; 17 stays a document of its own.
		self::assertSame([1], $answer['byGroup']);
		foreach ($this->fileCacheChecks() as $check) {
			if (in_array(17, $check['in']['fc.storage'], true)) {
				self::assertSame([17], $check['in']['fc.storage']);
			}
		}
	}

	public function testTheN1HashesOfAGroupGoOutInBandsOfAThousand(): void {
		foreach (range(1, 2500) as $number) {
			$this->verdict(11, 'projekt/f' . $number, 'skipped', 'unreadable');
		}

		$this->service()->distinctPathsByReasons([[11, 14]], [], self::identities([11, 14], [14 => 'projekt']));

		$counts = [];
		foreach ($this->fileCacheChecks() as $check) {
			self::assertLessThanOrEqual(1000, count($check['in']['fc.path_hash']));
			self::assertLessThanOrEqual(1000, count($check['in']['fc.storage']));
			foreach ($check['in']['fc.storage'] as $storageId) {
				$counts[$storageId] = ($counts[$storageId] ?? 0) + count($check['in']['fc.path_hash']);
			}
		}
		ksort($counts);
		self::assertSame([11 => 2500, 14 => 2500], $counts);
	}

	public function testTheIdentitiesComeAsAParameterAndAreNeverAskedHere(): void {
		// Allowlist of plan 43-21: only StorageService, DocKeyService and
		// AdminViewService ask shareIdentities(); this class gets them handed in.
		$constructor = (new \ReflectionClass(FileStateService::class))->getConstructor();
		self::assertNotNull($constructor);
		foreach ($constructor->getParameters() as $parameter) {
			self::assertNotSame(\OCA\Findling\Service\StorageService::class, (string)$parameter->getType());
		}
		$method = new \ReflectionMethod(FileStateService::class, 'distinctPathsByReasons');
		self::assertSame('identities', $method->getParameters()[2]->getName());
	}

	// -- the variant roots of the shared topology --------------------------------

	private const FIXTURE = 'backend/tests/fixtures/coverage_topology.json';

	/** @return array<string, mixed> the lookup of CoverageTopologyParityTest */
	private static function sharedTopology(): array {
		$base = dirname(__DIR__, 3);
		$candidates = [];
		$root = getenv('FINDLING_REPO_ROOT');
		if (is_string($root) && $root !== '') {
			$candidates[] = rtrim($root, '/\\') . '/' . self::FIXTURE;
		}
		$candidates[] = $base . '/' . self::FIXTURE;
		$candidates[] = $base . '/findling-src/' . self::FIXTURE;
		$candidates[] = dirname(__DIR__, 4) . '/findling-src/' . self::FIXTURE;
		foreach ($candidates as $file) {
			if (is_file($file)) {
				$decoded = json_decode((string)file_get_contents($file), true, 32, JSON_THROW_ON_ERROR);
				self::assertIsArray($decoded);

				return $decoded;
			}
		}

		self::fail('coverage_topology.json not found, looked at: ' . implode(', ', $candidates));
	}

	public function testTheRootsVariantGivesTheHandDerivedPhpOnlyFigures(): void {
		$topology = self::sharedTopology();
		$variant = null;
		foreach ($topology['variants'] as $candidate) {
			if ($candidate['name'] === 'roots') {
				$variant = $candidate;
			}
		}
		self::assertIsArray($variant);
		$php = $variant['expected']['php'];
		foreach ([...$topology['expected']['php']['phpOnlyRows'], ...$php['extraPhpOnlyRows']] as $row) {
			// filecache false: the inner join drops it (W-b).
			if ($row['filecache'] === true) {
				$this->verdict((int)$row['storage_id'], (string)$row['internalPath'], (string)$row['state'], (string)$row['reason']);
			}
		}
		foreach ($php['fileCacheWithoutVerdict'] as $row) {
			$this->heldWithoutVerdict[(int)$row['storage_id']][] = (string)$row['internalPath'];
		}
		$identities = [];
		foreach ($variant['identities'] as $storageId => $identity) {
			$identities[(int)$storageId] = ['share' => (string)$identity['share'], 'root' => (string)$identity['root']];
		}
		$inGroup = array_merge(...$variant['groups']);
		$singles = array_values(array_diff($variant['mounted'], $inGroup));

		$answer = $this->service()->distinctPathsByReasons($variant['groups'], $singles, $identities);

		$byId = static function (array $map): array {
			$out = [];
			foreach ($map as $key => $value) {
				$out[(int)$key] = (int)$value;
			}

			return $out;
		};
		self::assertSame($php['phpOnly']['byGroup'], $answer['byGroup']);
		self::assertSame($php['phpOnly']['notReadableByGroup'], $answer['notReadableByGroup']);
		self::assertSame($byId($php['phpOnly']['byStorage']), $answer['byStorage']);
		self::assertSame($byId($php['phpOnly']['notReadableByStorage']), $answer['notReadableByStorage']);
	}
}
