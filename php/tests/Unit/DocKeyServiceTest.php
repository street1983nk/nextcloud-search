<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\DocKeyService;
use OCA\Findling\Service\StorageService;
use OCP\Files\Cache\ICacheEntry;
use OCP\Files\Cache\IFileAccess;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;

/**
 * The document key in format 2 (plan 43-22, D-43-15, D-43-17) against the
 * shared catalogue backend/tests/fixtures/doc_key_cases.json, whose keys were
 * computed by hand with sha256sum and are recomputed in Python by
 * backend/tests/test_share_identity_cases.py. The cases of format 1 stay in the
 * catalogue as history; here they only prove that no key of format 1 is
 * derived any more.
 *
 * The catalogue sits on the backend side of the repository. Locally that is
 * dirname(__DIR__, 3)/backend; in the phpunit job the php directory is moved
 * to apps/findling of the server checkout while the repository stays in
 * findling-src at the workspace root, which is dirname(__DIR__, 4)
 * (measured in the first CI run of 43-07). A missing catalogue fails the suite rather than
 * skipping it, because a skipped catalogue is a green run that proved nothing.
 */
#[CoversClass(DocKeyService::class)]
final class DocKeyServiceTest extends TestCase {
	private const CATALOGUE = 'backend/tests/fixtures/doc_key_cases.json';

	/**
	 * @return list<array<string, mixed>>
	 */
	private static function cases(int $format): array {
		$base = dirname(__DIR__, 3);
		$candidates = [];
		$root = getenv('FINDLING_REPO_ROOT');
		if (is_string($root) && $root !== '') {
			$candidates[] = rtrim($root, '/\\') . '/' . self::CATALOGUE;
		}
		$candidates[] = $base . '/' . self::CATALOGUE;
		$candidates[] = $base . '/findling-src/' . self::CATALOGUE;
		// The phpunit job: apps/findling/tests/Unit, the repository in
		// findling-src at the workspace root, one directory above $base.
		$candidates[] = dirname(__DIR__, 4) . '/findling-src/' . self::CATALOGUE;

		foreach ($candidates as $file) {
			if (!is_file($file)) {
				continue;
			}
			$decoded = json_decode((string)file_get_contents($file), true, 16, JSON_THROW_ON_ERROR);
			self::assertIsArray($decoded);
			self::assertIsArray($decoded['cases'] ?? null);

			return array_values(array_filter(
				$decoded['cases'],
				static fn (array $case): bool => ($case['format'] ?? null) === $format,
			));
		}

		self::fail('doc_key_cases.json not found, looked at: ' . implode(', ', $candidates));
	}

	/**
	 * @return array<string, mixed>
	 */
	private static function caseNamed(string $name): array {
		foreach (self::cases(2) as $case) {
			if ($case['name'] === $name) {
				return $case;
			}
		}

		self::fail('no catalogue case of that name');
	}

	/**
	 * The identity a case stands for: none for an empty share.
	 *
	 * @param array<string, mixed> $case
	 * @return array{share: string, root: string}|null
	 */
	private static function identityOf(array $case): ?array {
		if ($case['share'] === '') {
			return null;
		}

		return ['share' => $case['share'], 'root' => $case['root']];
	}

	/**
	 * @param array<string, mixed> $case
	 */
	private static function keyOf(array $case): string {
		return DocKeyService::docKeyOf($case['path'], self::identityOf($case));
	}

	public function testTheFormatIsTwo(): void {
		self::assertSame(2, DocKeyService::DOC_KEY_FORMAT);
	}

	public function testTheCatalogueHoldsBothFormats(): void {
		self::assertCount(13, self::cases(1));
		self::assertGreaterThanOrEqual(11, count(self::cases(2)));
	}

	public function testEveryFormatTwoCaseYieldsItsHandComputedKey(): void {
		foreach (self::cases(2) as $case) {
			self::assertMatchesRegularExpression('/^[0-9a-f]{64}$/D', $case['expected'], $case['name']);
			self::assertSame($case['expected'], self::keyOf($case), $case['name']);
		}
	}

	public function testTheRelationsOfTheCatalogueHold(): void {
		$same = 0;
		$differs = 0;
		foreach (self::cases(2) as $case) {
			if (isset($case['sameAs'])) {
				self::assertSame(self::keyOf(self::caseNamed($case['sameAs'])), self::keyOf($case), $case['name']);
				$same++;
			}
			if (isset($case['differsFrom'])) {
				self::assertNotSame(self::keyOf(self::caseNamed($case['differsFrom'])), self::keyOf($case), $case['name']);
				$differs++;
			}
		}

		self::assertGreaterThanOrEqual(7, $same);
		self::assertGreaterThanOrEqual(4, $differs);
	}

	public function testNoKeyOfFormatOneIsDerivedAnyMore(): void {
		// The keys of rc.1 are not comparable with format 2; the container
		// builds them all anew (43-24). A format 1 key must never come out.
		foreach (self::cases(1) as $case) {
			self::assertNotSame($case['expected'], DocKeyService::docKeyOf($case['path']), $case['name']);
		}
	}

	public function testOneFileUnderEveryRootOfItsShareHasOneKey(): void {
		$share = ['share' => 'smb::192.168.98.246//daten', 'root' => ''];
		$expected = self::caseNamed('share at its top')['expected'];

		self::assertSame($expected, DocKeyService::docKeyOf('Projekte/a.doc', $share));
		self::assertSame($expected, DocKeyService::docKeyOf('a.doc', ['root' => 'Projekte'] + $share));
		self::assertSame($expected, DocKeyService::docKeyOf('/a.doc', ['root' => 'Projekte'] + $share));
	}

	public function testRootAndPathAreNeverFolded(): void {
		$share = ['share' => 'smb::192.168.98.246//daten', 'root' => ''];

		self::assertNotSame(DocKeyService::docKeyOf('Projekte/Bericht.txt', $share), DocKeyService::docKeyOf('Projekte/bericht.txt', $share));
		self::assertNotSame(
			DocKeyService::docKeyOf('a.doc', ['root' => 'Projekte'] + $share),
			DocKeyService::docKeyOf('a.doc', ['root' => 'projekte'] + $share),
		);
	}

	public function testAKeyWithoutIdentityNeverMeetsAKeyWithIdentity(): void {
		self::assertNotSame(
			DocKeyService::docKeyOf('Projekte/a.doc'),
			DocKeyService::docKeyOf('Projekte/a.doc', ['share' => 'smb::192.168.98.246//daten', 'root' => '']),
		);
		// The share is set apart by NUL: moving a part from share to path is
		// another key.
		self::assertNotSame(
			DocKeyService::docKeyOf('b/c', ['share' => 'smb::h//a', 'root' => '']),
			DocKeyService::docKeyOf('a/b/c', ['share' => 'smb::h//', 'root' => '']),
		);
	}

	public function testTheFilesPrefixIsNotCut(): void {
		// W2: an external path that starts with files/ stays apart from the
		// same path without it.
		self::assertNotSame(DocKeyService::docKeyOf('files/Rechnung.pdf'), DocKeyService::docKeyOf('Rechnung.pdf'));
		self::assertSame(
			self::caseNamed('a home storage keeps its files/ prefix')['expected'],
			DocKeyService::docKeyOf('files/Projekte/Vertrag.pdf'),
		);
	}

	public function testOnlyLeadingSlashesGoAndTheRestStays(): void {
		self::assertSame(DocKeyService::docKeyOf('files/a.pdf'), DocKeyService::docKeyOf('/files/a.pdf'));
		self::assertSame(DocKeyService::docKeyOf('files/a.pdf'), DocKeyService::docKeyOf('//files/a.pdf'));
		self::assertNotSame(DocKeyService::docKeyOf('files/a.pdf'), DocKeyService::docKeyOf('files/a.pdf/'));
		self::assertNotSame(DocKeyService::docKeyOf('files/a.pdf'), DocKeyService::docKeyOf('files/ a.pdf'));
	}

	// -- docKeysFor ----------------------------------------------------------

	/**
	 * A file cache double and a storage service double: the ids of $files have
	 * an entry with that internal path on that storage, every other id has
	 * none; the storages of $identities have that identity. Every band handed
	 * to getByFileIds lands in $bands, every list handed to shareIdentities in
	 * $asked.
	 *
	 * @param array<int, array{string, int}> $files
	 * @param array<int, array{share: string, root: string}> $identities
	 * @param list<list<int>> $bands
	 * @param list<list<int>> $asked
	 */
	private function service(array $files, array $identities = [], ?array &$bands = null, ?array &$asked = null): DocKeyService {
		$bands = [];
		$asked = [];
		$access = $this->createMock(IFileAccess::class);
		$access->method('getByFileIds')->willReturnCallback(
			function (array $fileIds) use ($files, &$bands): array {
				$bands[] = $fileIds;
				$found = [];
				foreach ($fileIds as $fileId) {
					if (isset($files[$fileId])) {
						$found[$fileId] = $this->entry(...$files[$fileId]);
					}
				}

				return $found;
			},
		);

		$storages = $this->createMock(StorageService::class);
		$storages->method('shareIdentities')->willReturnCallback(
			static function (array $storageIds) use ($identities, &$asked): array {
				$asked[] = $storageIds;

				return array_intersect_key($identities, array_flip($storageIds));
			},
		);

		return new DocKeyService($access, $storages);
	}

	private function entry(string $path, int $storageId): ICacheEntry&MockObject {
		$entry = $this->createMock(ICacheEntry::class);
		$entry->method('getPath')->willReturn($path);
		$entry->method('getStorageId')->willReturn($storageId);

		return $entry;
	}

	public function testEveryAskedIdEndsInExactlyOneList(): void {
		$answer = $this->service([
			11 => ['files/Projekte/Vertrag.pdf', 1],
			12 => ['files_trashbin/files/Alt.pdf.d1700000000', 1],
			13 => ['__groupfolders/trash/4/Alt.odt.d1700000000', 2],
			14 => ['Gemeinsam/Plan.xlsx', 3],
		])->docKeysFor([11, 12, 13, 14, 15]);

		self::assertSame([11, 14], array_keys($answer['keys']));
		self::assertSame([12, 13, 15], $answer['absent']);

		$all = array_merge(array_keys($answer['keys']), $answer['absent']);
		sort($all);
		self::assertSame([11, 12, 13, 14, 15], $all);
	}

	public function testTheKeysAreTheKeysOfShareAndPath(): void {
		$answer = $this->service(
			[
				11 => ['files/Projekte/Vertrag.pdf', 1],
				14 => ['a.doc', 7],
			],
			[7 => ['share' => 'smb::192.168.98.246//daten', 'root' => 'Projekte']],
		)->docKeysFor([11, 14]);

		self::assertSame(self::caseNamed('a home storage keeps its files/ prefix')['expected'], $answer['keys'][11]);
		self::assertSame(self::caseNamed('share at its top')['expected'], $answer['keys'][14]);
	}

	public function testOneFileUnderEveryRootAndSpellingOfItsShareGetsOneKey(): void {
		// The identities come out of the parser of 43-21 itself: the share
		// name folded, the root apart and as written.
		$ids = [
			1 => 'smb::anna@192.168.98.246//Daten//',
			2 => 'smb::bernd@192.168.98.246//Daten//Projekte/',
			3 => 'smb::carla@192.168.98.246//daten//',
			4 => 'smb::anna@fs.example//Daten//',
		];
		$identities = [];
		foreach ($ids as $numericId => $storageId) {
			$identity = StorageService::shareIdentity($storageId);
			self::assertNotNull($identity, $storageId);
			$identities[$numericId] = $identity;
		}

		$answer = $this->service(
			[
				11 => ['Projekte/a.doc', 1],
				12 => ['a.doc', 2],
				13 => ['Projekte/a.doc', 3],
				14 => ['Projekte/A.doc', 1],
				15 => ['Projekte/a.doc', 4],
				16 => ['Projekte/a.doc', 9],
			],
			$identities,
		)->docKeysFor([11, 12, 13, 14, 15, 16]);

		$keys = $answer['keys'];
		self::assertSame(self::caseNamed('share at its top')['expected'], $keys[11]);
		self::assertSame($keys[11], $keys[12]);
		self::assertSame($keys[11], $keys[13]);
		// Another spelling of the file, another share, a storage without
		// identity: three other keys.
		self::assertCount(4, array_unique([$keys[11], $keys[14], $keys[15], $keys[16]]));
		self::assertSame(self::caseNamed('a storage without share identity')['expected'], $keys[16]);
	}

	public function testTheIdentitiesAreAskedOncePerBandWithTheDistinctStorages(): void {
		$files = [];
		foreach (range(1, 450) as $fileId) {
			$files[$fileId] = ['f' . $fileId . '.txt', 100 + $fileId % 3];
		}

		$answer = $this->service($files, [], $bands, $asked)->docKeysFor(range(1, 450));

		self::assertCount(450, $answer['keys']);
		self::assertSame([200, 200, 50], array_map('count', $bands));
		self::assertCount(3, $asked);
		foreach ($asked as $storageIds) {
			self::assertSame($storageIds, array_values(array_unique($storageIds)));
			$sorted = $storageIds;
			sort($sorted);
			self::assertSame([100, 101, 102], $sorted);
		}
	}

	public function testAnEntryWithoutIdentityGetsTheFormWithAnEmptyShare(): void {
		$answer = $this->service([21 => ['Projekte/a.doc', 5]])->docKeysFor([21]);

		self::assertSame(hash('sha256', "2\0\0Projekte/a.doc"), $answer['keys'][21]);
		self::assertSame(DocKeyService::docKeyOf('Projekte/a.doc'), $answer['keys'][21]);
	}

	public function testABandOfTrashAndMissingRowsAsksForNoIdentity(): void {
		$answer = $this->service([12 => ['files_trashbin/files/Alt.pdf.d1700000000', 1]], [], $bands, $asked)
			->docKeysFor([12, 13]);

		self::assertSame([], $answer['keys']);
		self::assertSame([12, 13], $answer['absent']);
		self::assertSame([], $asked);
	}

	public function testAFailingIdentityLookupFailsTheWholeAnswer(): void {
		// Never a key without the share of its storage: the claim then travels
		// without keys and the route answers 500, both already handled there.
		$access = $this->createMock(IFileAccess::class);
		$access->method('getByFileIds')->willReturn([31 => $this->entry('a.doc', 1)]);
		$storages = $this->createMock(StorageService::class);
		$storages->method('shareIdentities')->willThrowException(new \RuntimeException('storages'));

		$this->expectException(\RuntimeException::class);
		(new DocKeyService($access, $storages))->docKeysFor([31]);
	}

	public function testTheAnswerCarriesNoPathNoShareOnlyHex(): void {
		$answer = $this->service(
			[11 => ['Geheim/Vertrag.pdf', 1]],
			[1 => ['share' => 'smb::fileserver.intern//vorstand', 'root' => 'Personal']],
		)->docKeysFor([11, 12]);

		$wire = (string)json_encode($answer);
		foreach (['Geheim', 'Vertrag', 'fileserver', 'vorstand', 'Personal'] as $secret) {
			self::assertStringNotContainsString($secret, $wire);
		}
		foreach ($answer['keys'] as $key) {
			self::assertMatchesRegularExpression('/^[0-9a-f]{64}$/D', $key);
		}
	}

	public function testNonPositiveAndDoubledIdsAreNotAsked(): void {
		$answer = $this->service([5 => ['files/a.pdf', 1]], [], $bands, $asked)->docKeysFor([0, -3, 5, 5]);

		self::assertSame([[5]], $bands);
		self::assertSame([[1]], $asked);
		self::assertSame([5], array_keys($answer['keys']));
		self::assertSame([], $answer['absent']);
	}

	public function testNothingAskedAsksNothing(): void {
		$answer = $this->service([], [], $bands, $asked)->docKeysFor([]);

		self::assertSame([], $bands);
		self::assertSame([], $asked);
		self::assertSame(['keys' => [], 'absent' => []], $answer);
	}
}
