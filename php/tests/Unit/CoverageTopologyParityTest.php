<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\AdminViewService;
use OCA\Findling\Service\ScanStatsService;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The PHP half of the per document coverage against the shared topology
 * backend/tests/fixtures/coverage_topology.json (plan 43-05, D-43-08, D-43-11).
 *
 * The Python half (backend/tests/test_coverage_counts.py and
 * test_coverage_endpoint.py) holds the container figures of the same file
 * against its expected block; this file takes those figures as the answer of
 * POST /coverage, the scan counters and the PHP only figures of expected.php,
 * and holds the arithmetic of the page against the hand derived denominator,
 * numerator, notReadable and shares. Two halves, one truth, and neither half
 * computes the expected numbers.
 *
 * The fixture sits on the backend side of the repository: locally that is
 * dirname(__DIR__, 3)/backend, in the phpunit job the repository stays in
 * findling-src at the workspace root (the lookup of DocKeyServiceTest). A
 * missing fixture fails, it is never skipped.
 */
#[CoversClass(AdminViewService::class)]
#[CoversClass(ScanStatsService::class)]
final class CoverageTopologyParityTest extends TestCase {
	private const FIXTURE = 'backend/tests/fixtures/coverage_topology.json';

	/** @return array<string, mixed> */
	private static function topology(): array {
		$base = dirname(__DIR__, 3);
		$candidates = [];
		$root = getenv('FINDLING_REPO_ROOT');
		if (is_string($root) && $root !== '') {
			$candidates[] = rtrim($root, '/\\') . '/' . self::FIXTURE;
		}
		$candidates[] = $base . '/' . self::FIXTURE;
		$candidates[] = $base . '/findling-src/' . self::FIXTURE;
		// The phpunit job: apps/findling/tests/Unit, the repository in
		// findling-src at the workspace root, one directory above $base.
		$candidates[] = dirname(__DIR__, 4) . '/findling-src/' . self::FIXTURE;

		foreach ($candidates as $file) {
			if (!is_file($file)) {
				continue;
			}
			$decoded = json_decode((string)file_get_contents($file), true, 32, JSON_THROW_ON_ERROR);
			self::assertIsArray($decoded);

			return $decoded;
		}

		self::fail('coverage_topology.json not found, looked at: ' . implode(', ', $candidates));
	}

	/**
	 * A JSON object with numeric keys, as an int keyed array.
	 *
	 * @return array<int, mixed>
	 */
	private static function byId(mixed $value): array {
		self::assertIsArray($value);
		$out = [];
		foreach ($value as $key => $entry) {
			$out[(int)$key] = $entry;
		}

		return $out;
	}

	/** @return array{mounted: list<int>, groups: list<list<int>>} */
	private static function body(array $topology): array {
		return AdminViewService::coverageBody($topology['mounted'], $topology['groups']);
	}

	/** The answer of POST /coverage for the topology, out of expected. @return array<string, mixed> */
	private static function containerAnswer(array $expected): array {
		$pairs = static function (array $map): array {
			$list = [];
			foreach (self::byId($map) as $storageId => $figure) {
				$list[] = [$storageId, (int)$figure];
			}

			return $list;
		};

		return [
			'documents' => $expected['documents'],
			'embeddedDocuments' => $expected['embeddedDocuments'],
			'judgedDocuments' => $expected['judgedDocuments'],
			'documentsByGroup' => $expected['documentsByGroup'],
			'judgedByGroup' => $expected['judgedByGroup'],
			'documentsByStorage' => $pairs($expected['documentsByStorage']),
			'judgedByStorage' => $pairs($expected['judgedByStorage']),
			'counting' => false,
			'docKeysMissing' => 0,
			'docKeysUnresolved' => 0,
			'docKeysCorrected' => 0,
		];
	}

	/** The scan counters of expected.php as the rows of findling_scan_stats. @return array<int, array<string, int|bool>> */
	private static function rows(array $php): array {
		$rows = [];
		foreach (self::byId($php['scanStats']) as $storageId => $row) {
			$rows[$storageId] = [
				'filesSeen' => (int)$row['filesSeen'],
				'overCap' => (int)$row['overCap'],
				'excluded' => (int)$row['excluded'],
				'finished' => $row['finished'] === true,
			];
		}

		return $rows;
	}

	/** @return array{byGroup: list<int>, byStorage: array<int,int>, notReadableByGroup: list<int>, notReadableByStorage: array<int,int>} */
	private static function phpOnly(array $php): array {
		$ints = static fn (array $map): array => array_map(intval(...), self::byId($map));

		return [
			'byGroup' => array_map(intval(...), $php['phpOnly']['byGroup']),
			'byStorage' => $ints($php['phpOnly']['byStorage']),
			'notReadableByGroup' => array_map(intval(...), $php['phpOnly']['notReadableByGroup']),
			'notReadableByStorage' => $ints($php['phpOnly']['notReadableByStorage']),
		];
	}

	public function testTheBodyIsTheMountListAndTheGroupsOfTheTopology(): void {
		$topology = self::topology();
		$body = self::body($topology);

		self::assertSame($topology['mounted'], $body['mounted']);
		self::assertSame($topology['groups'], $body['groups']);
	}

	public function testTheContainerAnswerHoldsUp(): void {
		$topology = self::topology();

		$answer = AdminViewService::perDocumentAnswer(self::containerAnswer($topology['expected']), self::body($topology));

		self::assertIsArray($answer);
		self::assertFalse($answer['counting']);
	}

	public function testThePhpPartsAreTheHandDerivedOnes(): void {
		$topology = self::topology();
		$php = $topology['expected']['php'];
		$body = self::body($topology);

		$parts = ScanStatsService::partsOf($body['mounted'], self::rows($php), $body['groups'], array_map(intval(...), self::byId($php['refusedPerStorage'])));

		self::assertSame($php['groupParts']['groups'], $parts['groups']);
		self::assertSame(array_map(intval(...), self::byId($php['groupParts']['singles'])), $parts['singles']);
	}

	public function testARefusedFileOfAStorageThatIsNotMountedShrinksNoPart(): void {
		// B1: 41 is not mounted; its refused file must leave every part alone.
		$topology = self::topology();
		$php = $topology['expected']['php'];
		$body = self::body($topology);
		$refused = array_map(intval(...), self::byId($php['refusedPerStorage']));
		$withForeign = $refused + array_map(intval(...), self::byId($php['refusedNotMounted']));

		self::assertSame(
			ScanStatsService::partsOf($body['mounted'], self::rows($php), $body['groups'], $refused),
			ScanStatsService::partsOf($body['mounted'], self::rows($php), $body['groups'], $withForeign),
		);
	}

	public function testTheDenominatorNumeratorNotReadableAndSharesAreTheHandDerivedOnes(): void {
		$topology = self::topology();
		$php = $topology['expected']['php'];
		$body = self::body($topology);
		$answer = AdminViewService::perDocumentAnswer(self::containerAnswer($topology['expected']), $body);
		self::assertIsArray($answer);
		$parts = ScanStatsService::partsOf($body['mounted'], self::rows($php), $body['groups'], array_map(intval(...), self::byId($php['refusedPerStorage'])));

		$figures = AdminViewService::perDocumentFigures(['grouped' => []], ['indexed' => 0, 'embedded' => 0], $answer, $parts, self::phpOnly($php));

		self::assertSame($php['denominator'], AdminViewService::perDocumentDenominator($parts, $answer, self::phpOnly($php)));
		self::assertSame($php['denominator'], $figures['indexable']);
		self::assertSame($php['counted'], $figures['backend']['indexed']);
		self::assertSame($php['embedded'], $figures['backend']['embedded']);
		self::assertSame($php['notReadable'], $figures['notReadable']);
		self::assertSame($php['percent'], AdminViewService::coverageShare($figures['backend']['indexed'], $figures['indexable'], true));
		self::assertSame($php['embeddedPercent'], AdminViewService::coverageShare($figures['backend']['embedded'], $figures['indexable'], true));
	}

	public function testTheMaximumPerPartIsTheOneOfTheFixture(): void {
		$topology = self::topology();
		$php = $topology['expected']['php'];
		$body = self::body($topology);
		$answer = AdminViewService::perDocumentAnswer(self::containerAnswer($topology['expected']), $body);
		self::assertIsArray($answer);
		$parts = ScanStatsService::partsOf($body['mounted'], self::rows($php), $body['groups'], array_map(intval(...), self::byId($php['refusedPerStorage'])));
		$phpOnly = self::phpOnly($php);

		foreach ($php['denominatorParts']['groups'] as $index => $expected) {
			$single = ['groups' => [$parts['groups'][$index]], 'singles' => []];
			$part = ['judgedByGroup' => [$answer['judgedByGroup'][$index]], 'judgedByStorage' => []];
			self::assertSame($expected, AdminViewService::perDocumentDenominator($single, $part, ['byGroup' => [$phpOnly['byGroup'][$index]], 'byStorage' => []]));
		}
		foreach (self::byId($php['denominatorParts']['singles']) as $storageId => $expected) {
			$single = ['groups' => [], 'singles' => [$storageId => $parts['singles'][$storageId]]];
			$part = ['judgedByGroup' => [], 'judgedByStorage' => $answer['judgedByStorage']];
			self::assertSame($expected, AdminViewService::perDocumentDenominator($single, $part, ['byGroup' => [], 'byStorage' => $phpOnly['byStorage']]));
		}
	}

	public function testTheShareNeverPassesAHundredPerCentInAnyPart(): void {
		$topology = self::topology();
		$expected = $topology['expected'];
		$php = $expected['php'];

		foreach ($expected['documentsByGroup'] as $index => $documents) {
			self::assertLessThanOrEqual($php['denominatorParts']['groups'][$index], $documents);
		}
		foreach (self::byId($expected['documentsByStorage']) as $storageId => $documents) {
			self::assertLessThanOrEqual(self::byId($php['denominatorParts']['singles'])[$storageId], $documents);
		}
	}

	/**
	 * The case of plan 43-18 (D-43-16 with D-43-11): the container judges a
	 * gateway 422 as skipped/unreadable and leaves it out of judged, the PHP
	 * side counts it out of oc_findling_file_state with N1. Every document
	 * stands in the denominator exactly once, the unreadable one in
	 * notReadable and never in the numerator, and no part passes a hundred
	 * per cent.
	 */
	public function testAGatewayUnreadableFileCountsOnceAndAsNotReadable(): void {
		$variant = null;
		foreach (self::topology()['variants'] as $candidate) {
			if ($candidate['name'] === 'gateway_unreadable') {
				$variant = $candidate;
			}
		}
		self::assertIsArray($variant);
		$expected = $variant['expected'];
		$php = $expected['php'];
		$body = self::body($variant);
		$answer = AdminViewService::perDocumentAnswer(self::containerAnswer($expected), $body);
		self::assertIsArray($answer);
		$parts = ScanStatsService::partsOf($body['mounted'], self::rows($php), $body['groups'], array_map(intval(...), self::byId($php['refusedPerStorage'])));
		$phpOnly = self::phpOnly($php);

		self::assertSame($php['groupParts']['groups'], $parts['groups']);
		self::assertSame(array_map(intval(...), self::byId($php['groupParts']['singles'])), $parts['singles']);

		$figures = AdminViewService::perDocumentFigures(['grouped' => []], ['indexed' => 0, 'embedded' => 0], $answer, $parts, $phpOnly);

		self::assertSame($php['denominator'], AdminViewService::perDocumentDenominator($parts, $answer, $phpOnly));
		self::assertSame($php['denominator'], $figures['indexable']);
		self::assertSame($php['counted'], $figures['backend']['indexed']);
		self::assertSame($php['notReadable'], $figures['notReadable']);
		self::assertSame($php['percent'], AdminViewService::coverageShare($figures['backend']['indexed'], $figures['indexable'], true));
		self::assertLessThanOrEqual($figures['indexable'], $figures['backend']['indexed']);
		foreach ($expected['documentsByGroup'] as $index => $documents) {
			self::assertLessThanOrEqual($php['denominatorParts']['groups'][$index], $documents);
		}
		foreach (self::byId($expected['documentsByStorage']) as $storageId => $documents) {
			self::assertLessThanOrEqual(self::byId($php['denominatorParts']['singles'])[$storageId], $documents);
		}
	}
}
