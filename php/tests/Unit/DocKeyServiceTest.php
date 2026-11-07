<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\DocKeyService;
use OCP\Files\Cache\ICacheEntry;
use OCP\Files\Cache\IFileAccess;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;

/**
 * The document key of plan 43-15 (D-43-14) against the shared catalogue
 * backend/tests/fixtures/doc_key_cases.json, whose keys were computed by hand
 * with sha256sum and are recomputed in Python by the verify of the plan.
 *
 * The catalogue sits on the backend side of the repository. Locally that is
 * dirname(__DIR__, 3)/backend; in the phpunit job the php directory is moved
 * to apps/findling of the server checkout while the repository stays in
 * findling-src at the workspace root, which is the same dirname(__DIR__, 3)
 * one directory further down. A missing catalogue fails the suite rather than
 * skipping it, because a skipped catalogue is a green run that proved nothing.
 */
#[CoversClass(DocKeyService::class)]
final class DocKeyServiceTest extends TestCase {
	private const CATALOGUE = 'backend/tests/fixtures/doc_key_cases.json';

	/**
	 * @return list<array{name: string, path: string, expected: string, derivation: string, differsFrom?: string, sameAs?: string}>
	 */
	private static function cases(): array {
		$base = dirname(__DIR__, 3);
		$candidates = [];
		$root = getenv('FINDLING_REPO_ROOT');
		if (is_string($root) && $root !== '') {
			$candidates[] = rtrim($root, '/\\') . '/' . self::CATALOGUE;
		}
		$candidates[] = $base . '/' . self::CATALOGUE;
		$candidates[] = $base . '/findling-src/' . self::CATALOGUE;

		foreach ($candidates as $file) {
			if (!is_file($file)) {
				continue;
			}
			$decoded = json_decode((string)file_get_contents($file), true, 16, JSON_THROW_ON_ERROR);
			self::assertIsArray($decoded);
			self::assertIsArray($decoded['cases'] ?? null);

			return $decoded['cases'];
		}

		self::fail('doc_key_cases.json not found, looked at: ' . implode(', ', $candidates));
	}

	private static function caseByPath(string $path): array {
		foreach (self::cases() as $case) {
			if ($case['path'] === $path) {
				return $case;
			}
		}

		self::fail('no catalogue case for the asked path');
	}

	public function testTheCatalogueHoldsAtLeastEightCases(): void {
		self::assertGreaterThanOrEqual(8, count(self::cases()));
	}

	public function testEveryCatalogueCaseYieldsItsHandComputedKey(): void {
		foreach (self::cases() as $case) {
			self::assertMatchesRegularExpression('/^[0-9a-f]{64}$/D', $case['expected'], $case['name']);
			self::assertSame($case['expected'], DocKeyService::docKeyOf($case['path']), $case['name']);
		}
	}

	public function testTheRelationsOfTheCatalogueHold(): void {
		$related = 0;
		foreach (self::cases() as $case) {
			if (isset($case['sameAs'])) {
				self::assertNotSame($case['sameAs'], $case['path'], $case['name']);
				self::assertSame(DocKeyService::docKeyOf($case['sameAs']), DocKeyService::docKeyOf($case['path']), $case['name']);
				$related++;
			}
			if (isset($case['differsFrom'])) {
				self::assertNotSame(DocKeyService::docKeyOf($case['differsFrom']), DocKeyService::docKeyOf($case['path']), $case['name']);
				$related++;
			}
		}

		// NFD equals NFC, files/ is not cut, case is kept: three relations.
		self::assertGreaterThanOrEqual(3, $related);
	}

	public function testTheFilesPrefixIsNotCut(): void {
		// W2: an external path that starts with files/ stays apart from the
		// same path without it.
		self::assertNotSame(DocKeyService::docKeyOf('files/Rechnung.pdf'), DocKeyService::docKeyOf('Rechnung.pdf'));
		self::assertSame(self::caseByPath('files/Rechnung.pdf')['expected'], DocKeyService::docKeyOf('files/Rechnung.pdf'));
	}

	public function testOnlyLeadingSlashesGoAndTheRestStays(): void {
		self::assertSame(DocKeyService::docKeyOf('files/a.pdf'), DocKeyService::docKeyOf('/files/a.pdf'));
		self::assertSame(DocKeyService::docKeyOf('files/a.pdf'), DocKeyService::docKeyOf('//files/a.pdf'));
		self::assertNotSame(DocKeyService::docKeyOf('files/a.pdf'), DocKeyService::docKeyOf('files/a.pdf/'));
		self::assertNotSame(DocKeyService::docKeyOf('files/a.pdf'), DocKeyService::docKeyOf('files/ a.pdf'));
	}

	// -- docKeysFor ----------------------------------------------------------

	/**
	 * A file cache double: the ids of $paths have an entry with that internal
	 * path, every other id has none. Every band handed to getByFileIds is
	 * recorded in $bands.
	 *
	 * @param array<int, string> $paths
	 * @param list<list<int>> $bands
	 */
	private function service(array $paths, ?array &$bands = null): DocKeyService {
		$bands = [];
		$access = $this->createMock(IFileAccess::class);
		$access->method('getByFileIds')->willReturnCallback(
			function (array $fileIds) use ($paths, &$bands): array {
				$bands[] = $fileIds;
				$found = [];
				foreach ($fileIds as $fileId) {
					if (isset($paths[$fileId])) {
						$found[$fileId] = $this->entry($paths[$fileId]);
					}
				}

				return $found;
			},
		);

		return new DocKeyService($access);
	}

	private function entry(string $path): ICacheEntry&MockObject {
		$entry = $this->createMock(ICacheEntry::class);
		$entry->method('getPath')->willReturn($path);

		return $entry;
	}

	public function testEveryAskedIdEndsInExactlyOneList(): void {
		$answer = $this->service([
			11 => 'files/Projekte/Vertrag.pdf',
			12 => 'files_trashbin/files/Alt.pdf.d1700000000',
			13 => '__groupfolders/trash/4/Alt.odt.d1700000000',
			14 => 'Gemeinsam/Plan.xlsx',
		])->docKeysFor([11, 12, 13, 14, 15]);

		self::assertSame([11, 14], array_keys($answer['keys']));
		self::assertSame([12, 13, 15], $answer['absent']);

		$all = array_merge(array_keys($answer['keys']), $answer['absent']);
		sort($all);
		self::assertSame([11, 12, 13, 14, 15], $all);
	}

	public function testTheKeysAreTheKeysOfTheInternalPaths(): void {
		$answer = $this->service([
			11 => 'files/Projekte/Vertrag.pdf',
			14 => 'Gemeinsam/Plan.xlsx',
		])->docKeysFor([11, 14]);

		self::assertSame(self::caseByPath('files/Projekte/Vertrag.pdf')['expected'], $answer['keys'][11]);
		self::assertSame(self::caseByPath('Gemeinsam/Plan.xlsx')['expected'], $answer['keys'][14]);
	}

	public function testTwoMembersOfAGroupWithTheSameInternalPathGetTheSameKey(): void {
		// Two storages of one counting key share host, share and root, so the
		// file has one internal path on both, whatever its mount points are.
		$answer = $this->service([21 => 'Gemeinsam/Plan.xlsx', 22 => 'Gemeinsam/Plan.xlsx', 23 => 'Gemeinsam/Andere.xlsx'])
			->docKeysFor([21, 22, 23]);

		self::assertSame($answer['keys'][21], $answer['keys'][22]);
		self::assertNotSame($answer['keys'][21], $answer['keys'][23]);
	}

	public function testTheAnswerCarriesNoPathOnlyHex(): void {
		$answer = $this->service([11 => 'files/Geheim/Vertrag.pdf'])->docKeysFor([11, 12]);

		$wire = (string)json_encode($answer);
		self::assertStringNotContainsString('Geheim', $wire);
		self::assertStringNotContainsString('Vertrag', $wire);
		foreach ($answer['keys'] as $key) {
			self::assertMatchesRegularExpression('/^[0-9a-f]{64}$/D', $key);
		}
	}

	public function testALongListIsAskedInBandsOfTwoHundred(): void {
		$paths = [];
		foreach (range(1, 450) as $fileId) {
			$paths[$fileId] = 'files/f' . $fileId . '.txt';
		}

		$answer = $this->service($paths, $bands)->docKeysFor(range(1, 450));

		self::assertCount(450, $answer['keys']);
		self::assertSame([200, 200, 50], array_map('count', $bands));
	}

	public function testNonPositiveAndDoubledIdsAreNotAsked(): void {
		$answer = $this->service([5 => 'files/a.pdf'], $bands)->docKeysFor([0, -3, 5, 5]);

		self::assertSame([[5]], $bands);
		self::assertSame([5], array_keys($answer['keys']));
		self::assertSame([], $answer['absent']);
	}

	public function testNothingAskedAsksTheFileCacheNothing(): void {
		$answer = $this->service([], $bands)->docKeysFor([]);

		self::assertSame([], $bands);
		self::assertSame(['keys' => [], 'absent' => []], $answer);
	}
}
