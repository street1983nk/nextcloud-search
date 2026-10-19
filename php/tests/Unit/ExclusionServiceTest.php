<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCP\BackgroundJob\IJobList;
use OCP\Exceptions\AppConfigTypeConflictException;
use OCP\IAppConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The patterns of D-30-01 next to the prefixes of 1.4.2 (plan 33-02).
 *
 * Four things are held here. The matcher hits what the help sentence on the
 * page promises and nothing next to it, with a positive control and a counter
 * case for every rule of PE-1. Every refused entry earns one closed code and the
 * answer never carries the value (T-33-06). The stored list is read defensively,
 * because occ config:app:set writes past the form (T-33-05). And the prefixes
 * stay what 1.4.2 stored and compared, byte for byte, including a prefix that
 * holds a literal star (T-33-07).
 *
 * ExclusionService is final, so it is built for real over a mocked app config
 * that answers per key, which is also what keeps a test from reading the prefix
 * list as the pattern list by accident. Every non ASCII value in this file is
 * written as an escape: the source stays ASCII, and the composed and the
 * decomposed form of the same name are told apart by what they are, not by how
 * an editor shows them.
 */
#[CoversClass(ExclusionService::class)]
final class ExclusionServiceTest extends TestCase {
	/**
	 * Every log line the service wrote, in order.
	 *
	 * @var list<array{level: string, message: string, context: array<array-key, mixed>}>
	 */
	private array $logLines = [];

	/**
	 * What the service wrote into the app config, keyed by app config key.
	 *
	 * @var array<string, list<mixed>>
	 */
	private array $written = [];

	/**
	 * @param list<mixed> $prefixes the stored value of the prefix key
	 * @param list<mixed>|null $patterns the stored value of the pattern key, null when the key is absent
	 * @param list<string> $conflicts keys that occ stored with another type than array, so the core
	 *                                throws on reading them as one (finding H-33-02 of audit 33-11)
	 */
	private function service(array $prefixes = [], ?array $patterns = [], array $conflicts = []): ExclusionService {
		$this->logLines = [];
		$this->written = [];

		$appConfig = $this->createMock(IAppConfig::class);
		$appConfig->method('getValueArray')->willReturnCallback(
			static function (string $app, string $key, array $default = []) use ($prefixes, $patterns, $conflicts): array {
				if (in_array($key, $conflicts, true)) {
					throw new AppConfigTypeConflictException('conflict with value type from database');
				}
				if ($key === SettingsService::KEY_EXCLUSIONS) {
					return $prefixes;
				}
				if ($key === SettingsService::KEY_EXCLUSION_PATTERNS && $patterns !== null) {
					return $patterns;
				}

				return $default;
			},
		);
		$appConfig->method('setValueArray')->willReturnCallback(
			function (string $app, string $key, array $value): bool {
				$this->written[$key] = array_values($value);

				return true;
			},
		);

		$logger = $this->createMock(LoggerInterface::class);
		foreach (['emergency', 'alert', 'critical', 'error', 'warning', 'notice', 'info', 'debug'] as $level) {
			$logger->method($level)->willReturnCallback(
				function (string|\Stringable $message, array $context = []) use ($level): void {
					$this->logLines[] = ['level' => $level, 'message' => (string)$message, 'context' => $context];
				},
			);
		}

		return new ExclusionService(
			$appConfig,
			$this->createMock(StorageService::class),
			$this->createMock(IJobList::class),
			$logger,
		);
	}

	// -- the matcher -------------------------------------------------------

	/**
	 * Positive controls: each pattern hits the path, on its own.
	 *
	 * @return array<string, array{string, string}>
	 */
	public static function hits(): array {
		return [
			'bundle folder in a subfolder' => ['*.photoslibrary', 'Fotos/Mediathek.photoslibrary'],
			'file deep inside the bundle' => ['*.photoslibrary', 'Fotos/Mediathek.photoslibrary/database/x.db'],
			'bundle at the top of the mount' => ['*.photoslibrary', 'Mediathek.photoslibrary/a'],
			'node_modules at the top of the home' => ['*/node_modules/*', 'node_modules/x.js'],
			'node_modules deep inside' => ['*/node_modules/*', 'src/app/node_modules/y/z.js'],
			'keynote bundle of issue 22' => ['*.key', 'AG_Beteiligungen/2024/Vortrag.key/Data/thumb.jpg'],
			'anchored pattern at the start' => ['Backups/*', 'Backups/a/b'],
			'question mark is one composed character' => ['Caf?', "Caf\u{00E9}"],
			'ancestor at a slash' => ['*/build', 'x/build/out.o'],
			'question mark inside a name' => ['a?b', 'acb'],
			'star across folders in the middle' => ['Abteilung/*/Exporte/*', 'Abteilung/Nord/2024/Exporte/x.csv'],
			'parentheses and dots are literals' => ['Fotos (2024)/*.tmp', 'Fotos (2024)/a.tmp'],
		];
	}

	#[DataProvider('hits')]
	public function testAPatternHitsWhatItNames(string $pattern, string $path): void {
		self::assertTrue($this->service([], [$pattern])->isExcluded($path));
	}

	/**
	 * Counter cases: the path next to the one a pattern names.
	 *
	 * @return array<string, array{string, string}>
	 */
	public static function misses(): array {
		return [
			'bundle suffix inside a longer name' => ['*.photoslibrary', 'Notizen.photoslibrary.txt'],
			'node_modules as part of a longer name' => ['*/node_modules/*', 'my_node_modules/x.js'],
			'anchored pattern further down' => ['Backups/*', 'Archiv/Backups/x'],
			'question mark never matches a slash' => ['a?b', 'a/b'],
			'upper and lower case count' => ['*.key', 'Vortrag.KEY/x'],
			'question mark is exactly one character' => ['Caf?', 'Cafes'],
			'question mark needs a character' => ['Caf?', 'Caf'],
			'build as part of a longer name' => ['*/build', 'x/builder/out.o'],
		];
	}

	#[DataProvider('misses')]
	public function testAPatternLeavesItsNeighbourAlone(string $pattern, string $path): void {
		self::assertFalse($this->service([], [$pattern])->isExcluded($path));
	}

	public function testOnePathIsAskedAgainstEveryPattern(): void {
		$service = $this->service([], ['*.photoslibrary', '*/node_modules/*', '*.key']);

		self::assertTrue($service->isExcluded('src/node_modules/a.js'));
		self::assertTrue($service->isExcluded('Vortrag.key/b.jpg'));
		self::assertFalse($service->isExcluded('src/app.js'));
	}

	public function testTheEmptyPathIsNeverExcluded(): void {
		self::assertFalse($this->service([], ['*.key'])->isExcluded(''));
		self::assertFalse($this->service([], ['*.key'])->isExcluded('/'));
	}

	// -- refused entries -----------------------------------------------------

	/**
	 * One refused entry per code, the value and the code it earns.
	 *
	 * @return array<string, array{string, string}>
	 */
	public static function refusals(): array {
		return [
			'empty' => ['', ExclusionService::ERROR_EMPTY],
			'only blanks' => ['   ', ExclusionService::ERROR_EMPTY],
			'sixty one characters' => ['*' . str_repeat('a', 60), ExclusionService::ERROR_TOO_LONG],
			'dot dot segment' => ['*/../x*', ExclusionService::ERROR_TRAVERSAL],
			'dot segment' => ['*/./x*', ExclusionService::ERROR_TRAVERSAL],
			'double star' => ['**/x', ExclusionService::ERROR_DOUBLE_STAR],
			'character class' => ['[0-9]*', ExclusionService::ERROR_UNSUPPORTED_CHARACTER],
			'braces' => ['{a,b}*', ExclusionService::ERROR_UNSUPPORTED_CHARACTER],
			'escape' => ['a\\*', ExclusionService::ERROR_UNSUPPORTED_CHARACTER],
			'negation' => ['!*.tmp', ExclusionService::ERROR_NEGATION],
			'control character' => ["*.k\x01ey", ExclusionService::ERROR_CONTROL_CHARACTER],
			'only a star' => ['*', ExclusionService::ERROR_NO_LITERAL],
			'star slash star' => ['*/*', ExclusionService::ERROR_NO_LITERAL],
			'question mark and star' => ['?*', ExclusionService::ERROR_NO_LITERAL],
			'no wildcard' => ['node_modules', ExclusionService::ERROR_NO_WILDCARD],
		];
	}

	#[DataProvider('refusals')]
	public function testARefusedEntryEarnsItsCodeAndNotItsValue(string $value, string $code): void {
		$service = $this->service();

		$answer = $service->validatePatterns([$value]);

		self::assertSame([$code], $answer);
		self::assertNotContains($value, $answer);
		if (trim($value) !== '') {
			self::assertStringNotContainsString($value, json_encode($answer, JSON_THROW_ON_ERROR));
		}
		foreach ($this->logLines as $line) {
			if (trim($value) !== '') {
				self::assertStringNotContainsString($value, $line['message']);
			}
			self::assertNotContains($value, $line['context']);
		}
	}

	#[DataProvider('refusals')]
	public function testARefusedEntryIsNotWritten(string $value, string $code): void {
		$service = $this->service();

		self::assertSame([$code], $service->savePatterns([$value]));
		self::assertSame([], $this->written);
	}

	public function testSixtyCharactersOfTwoBytesEachAreAllowed(): void {
		// Counted in characters and not in bytes: 1 + 59 characters, 119 bytes.
		$pattern = '*' . str_repeat("\u{00E9}", 59);

		self::assertSame(60, mb_strlen($pattern));
		self::assertSame([], $this->service()->validatePatterns([$pattern]));
	}

	public function testThirtyThreePatternsAreTooMany(): void {
		$patterns = [];
		for ($i = 0; $i < 33; $i++) {
			$patterns[] = '*.ext' . $i;
		}

		self::assertSame([ExclusionService::ERROR_TOO_MANY], $this->service()->validatePatterns($patterns));
		self::assertSame([], $this->service()->validatePatterns(array_slice($patterns, 0, 32)));
	}

	public function testTheSamePatternTwiceAfterNormalisationIsADuplicate(): void {
		self::assertSame(
			[ExclusionService::ERROR_DUPLICATE],
			$this->service()->validatePatterns(['*.key', ' /*.key/ ']),
		);
	}

	public function testAnEntryThatIsNotAStringIsEmpty(): void {
		self::assertSame([ExclusionService::ERROR_EMPTY], $this->service()->validatePatterns([7]));
	}

	// -- normalisation and saving -------------------------------------------

	public function testAPatternIsNormalisedLikeAPrefixBeforeItIsStored(): void {
		$service = $this->service();

		self::assertSame([], $service->savePatterns(['  /files/Fotos//*.photoslibrary/ ']));
		self::assertSame(['Fotos/*.photoslibrary'], $this->written[SettingsService::KEY_EXCLUSION_PATTERNS] ?? null);
		self::assertArrayNotHasKey(SettingsService::KEY_EXCLUSIONS, $this->written);
	}

	public function testADecomposedPatternIsStoredComposed(): void {
		$service = $this->service();

		self::assertSame([], $service->savePatterns(["Cafe\u{0301}?"]));
		self::assertSame(["Caf\u{00E9}?"], $this->written[SettingsService::KEY_EXCLUSION_PATTERNS] ?? null);
	}

	public function testASavedPatternIsInForceInTheSameRequest(): void {
		$service = $this->service([], []);

		self::assertFalse($service->isExcluded('Vortrag.key/x.jpg'));
		self::assertSame([], $service->savePatterns(['*.key']));
		self::assertSame(['*.key'], $service->patterns());
		self::assertTrue($service->isExcluded('Vortrag.key/x.jpg'));
	}

	public function testNewPatternsAreTheNormalisedOnesNotStoredYet(): void {
		$service = $this->service([], ['*.key']);

		self::assertSame(['*.pages'], $service->newPatterns(['*.key', '/*.pages', '*.pages', 'node_modules', 7]));
	}

	// -- the defensive read ----------------------------------------------------

	public function testAStoredListBeyondTheCeilingIsCutAndTheCutIsNamedInNumbers(): void {
		$stored = [];
		for ($i = 0; $i < 40; $i++) {
			$stored[] = '*.ext' . $i;
		}

		$patterns = $this->service([], $stored)->patterns();

		self::assertCount(ExclusionService::MAX_PATTERNS, $patterns);
		self::assertSame(array_slice($stored, 0, 32), $patterns);
		$warnings = array_values(array_filter($this->logLines, static fn (array $line): bool => $line['level'] === 'warning'));
		self::assertCount(1, $warnings);
		foreach ($warnings[0]['context'] as $value) {
			self::assertIsInt($value);
		}
	}

	public function testUnusableStoredEntriesAreDroppedAndCounted(): void {
		$stored = ['*.key', '**/x', '*' . str_repeat('a', 60), 'node_modules', 7, null, ['*.x'], '*.pages'];

		$patterns = $this->service([], $stored)->patterns();

		self::assertSame(['*.key', '*.pages'], $patterns);
		self::assertCount(1, $this->logLines);
		self::assertSame(['unusable' => 6, 'inForce' => 2], $this->logLines[0]['context']);
	}

	public function testAMissingPatternKeyReadsAsAnEmptyList(): void {
		$service = $this->service(['Archiv'], null);

		self::assertSame([], $service->patterns());
		self::assertSame([], $this->logLines);
	}

	/**
	 * occ config:app:set findling exclusion_patterns --value=42 --type=integer is
	 * accepted by occ, and reading the key as an array then throws in the core.
	 * Before audit 33-11 that stopped the listener for every write of the
	 * instance and broke the page (H-33-02). The key reads as an empty list now,
	 * named in numbers like any other unusable value, the prefixes keep working,
	 * and the line is written once per request, not once per question.
	 */
	public function testAPatternKeyOfAnotherTypeReadsAsAnEmptyListAndIsCounted(): void {
		$service = $this->service(['Archiv'], [], [SettingsService::KEY_EXCLUSION_PATTERNS]);

		self::assertSame([], $service->patterns());
		self::assertSame([], $service->patterns());
		self::assertSame(['Archiv'], $service->prefixes());
		self::assertTrue($service->isExcluded('Archiv/x.pdf'));
		self::assertFalse($service->isExcluded('Vortrag.key'));
		self::assertTrue($service->hasRules());
		self::assertCount(1, $this->logLines);
		self::assertSame('warning', $this->logLines[0]['level']);
		self::assertSame(['unusable' => 1, 'inForce' => 0], $this->logLines[0]['context']);
	}

	/** The twin of the case above on the prefix key, which 1.4.2 read the same way. */
	public function testAPrefixKeyOfAnotherTypeReadsAsAnEmptyListAndIsCounted(): void {
		$service = $this->service([], ['*.key'], [SettingsService::KEY_EXCLUSIONS]);

		self::assertSame([], $service->prefixes());
		self::assertSame([], $service->prefixes());
		self::assertSame(['*.key'], $service->patterns());
		self::assertTrue($service->isExcluded('Vortrag.key'));
		self::assertFalse($service->isExcluded('Archiv/x.pdf'));
		self::assertCount(1, $this->logLines);
		self::assertSame('warning', $this->logLines[0]['level']);
		self::assertSame(['unusable' => 1, 'inForce' => 0], $this->logLines[0]['context']);
	}

	/** Both keys of another type: no rule at all, and nothing that throws. */
	public function testBothKeysOfAnotherTypeLeaveNoRuleAndNoThrow(): void {
		$service = $this->service(['Archiv'], ['*.key'], [SettingsService::KEY_EXCLUSIONS, SettingsService::KEY_EXCLUSION_PATTERNS]);

		self::assertFalse($service->hasRules());
		self::assertFalse($service->isExcluded('Archiv/x.pdf'));
		self::assertFalse($service->isExcluded('Vortrag.key'));
		self::assertCount(2, $this->logLines);
		foreach ($this->logLines as $line) {
			self::assertSame(['unusable' => 1, 'inForce' => 0], $line['context']);
		}
	}

	// -- the prefixes of 1.4.2 ------------------------------------------------

	public function testStoredPrefixesStayByteForByteAndAStarInThemIsLiteral(): void {
		$service = $this->service(['Archiv', 'a*b'], null);

		self::assertSame(['Archiv', 'a*b'], $service->prefixes());
		self::assertSame([], $service->patterns());
		self::assertTrue($service->isExcluded('a*b'));
		self::assertTrue($service->isExcluded('a*b/x.pdf'));
		self::assertFalse($service->isExcluded('axxb'));
		self::assertFalse($service->isExcluded('axxb/x.pdf'));
		self::assertTrue($service->isExcluded('Archiv/x.pdf'));
		self::assertFalse($service->isExcluded('Archivar.pdf'));
	}

	public function testSavingPatternsLeavesThePrefixesAlone(): void {
		$service = $this->service(['Archiv'], []);

		self::assertSame([], $service->savePatterns(['*.key']));
		self::assertSame(['Archiv'], $service->prefixes());
		self::assertArrayNotHasKey(SettingsService::KEY_EXCLUSIONS, $this->written);
	}

	// -- hasRules -------------------------------------------------------------

	public function testHasRulesIsTrueForPatternsOnly(): void {
		self::assertTrue($this->service([], ['*.key'])->hasRules());
	}

	public function testHasRulesIsTrueForPrefixesOnly(): void {
		self::assertTrue($this->service(['Archiv'], [])->hasRules());
	}

	public function testHasRulesIsTrueForBoth(): void {
		self::assertTrue($this->service(['Archiv'], ['*.key'])->hasRules());
	}

	public function testHasRulesIsFalseWithoutAnyRule(): void {
		self::assertFalse($this->service([], [])->hasRules());
	}
}
