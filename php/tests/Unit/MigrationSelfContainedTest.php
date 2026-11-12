<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * A migration names no class of the app (issue #51).
 *
 * Nextcloud runs an update in the process that started with the OLD version of
 * the app: occ app:update and the update button of the apps page load the app,
 * replace its files and then run the new migrations, all in one PHP process.
 * The autoloader never loads a class twice, so a migration that touches a
 * service sees the class as the old release shipped it. A constant or a method
 * that came with the very release the migration belongs to does not exist
 * there. The migration to 1.6.3 read SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT,
 * new in 1.6.3, and every update from the store died on "Undefined constant".
 * The suite did not see it, because here the new classes are the loaded ones,
 * and the upgrade jobs did not see it, because they ran occ upgrade in a fresh
 * process.
 *
 * So the rule is on the source and not on the behaviour: a file under
 * lib/Migration imports nothing out of OCA\Findling and names no such class in
 * its code. What it needs from the app it carries as a literal, and its own
 * test holds the literal against the constant.
 *
 * The migrations that shipped before the rule keep the imports they have, as a
 * frozen list. They are safe by measurement and not by construction: every
 * symbol they use existed in the release before their own. The list may get
 * shorter and never longer; a migration that is not on it is held to nothing
 * at all.
 */
#[CoversNothing]
final class MigrationSelfContainedTest extends TestCase {
	/**
	 * The imports of the migrations that shipped before 1.6.4, exactly.
	 *
	 * @var array<string, list<string>>
	 */
	private const GRANDFATHERED = [
		'Version001100Date20260911000000.php' => ['OCA\Findling\AppInfo\Application', 'OCA\Findling\Service\ExAppService'],
		'Version001200Date20260921000000.php' => ['OCA\Findling\AppInfo\Application', 'OCA\Findling\Service\ExAppService'],
		'Version001300Date20260924000000.php' => ['OCA\Findling\AppInfo\Application', 'OCA\Findling\Service\ExAppService'],
		'Version001300Date20260927000000.php' => ['OCA\Findling\Db\QueueMapper', 'OCA\Findling\Service\FileStateService'],
		'Version001301Date20260929000000.php' => ['OCA\Findling\Db\QueueMapper', 'OCA\Findling\Service\FileStateService'],
		'Version001400Date20261006000000.php' => ['OCA\Findling\AppInfo\Application', 'OCA\Findling\Service\ExAppService'],
		'Version001500Date20261012000000.php' => ['OCA\Findling\AppInfo\Application', 'OCA\Findling\Service\ExAppService', 'OCA\Findling\Service\SettingsService'],
		'Version001600Date20261028000000.php' => ['OCA\Findling\AppInfo\Application', 'OCA\Findling\Service\ExAppService'],
	];

	private static function migrationDir(): string {
		return dirname(__DIR__, 2) . '/lib/Migration';
	}

	/**
	 * The classes of the app a piece of migration source names, comments and
	 * strings left out: the use statements, and every qualified name in code.
	 *
	 * @return list<string>
	 */
	private static function appClassesNamedIn(string $source): array {
		$found = [];
		$inNamespace = false;
		foreach (\PhpToken::tokenize($source) as $token) {
			if ($token->is(T_NAMESPACE)) {
				$inNamespace = true;

				continue;
			}
			if ($inNamespace) {
				// The namespace line itself is not a reference to a class.
				if ($token->text === ';' || $token->text === '{') {
					$inNamespace = false;
				}

				continue;
			}
			if (!$token->is([T_NAME_QUALIFIED, T_NAME_FULLY_QUALIFIED])) {
				continue;
			}
			$name = ltrim($token->text, '\\');
			if (str_starts_with($name, 'OCA\Findling\\')) {
				$found[] = $name;
			}
		}
		$found = array_values(array_unique($found));
		sort($found);

		return $found;
	}

	/** @return iterable<string, array{string}> */
	public static function migrationFiles(): iterable {
		$files = glob(self::migrationDir() . '/Version*.php');
		self::assertIsArray($files);
		foreach ($files as $file) {
			yield basename($file) => [$file];
		}
	}

	#[DataProvider('migrationFiles')]
	public function testAMigrationNamesNoClassOfTheApp(string $file): void {
		$source = file_get_contents($file);
		self::assertIsString($source);

		$allowed = self::GRANDFATHERED[basename($file)] ?? [];
		sort($allowed);

		self::assertSame(
			$allowed,
			self::appClassesNamedIn($source),
			basename($file) . ' names a class of the app. An update runs with the classes of the old '
			. 'release loaded, so a migration carries what it needs as a literal (issue #51).',
		);
	}

	public function testTheDirectoryIsTheOneWithTheMigrations(): void {
		// Positive control: an empty glob would make the rule above pass on nothing.
		$names = array_map('basename', glob(self::migrationDir() . '/Version*.php') ?: []);

		self::assertContains('Version001603Date20261108000000.php', $names);
		self::assertGreaterThanOrEqual(count(self::GRANDFATHERED) + 1, count($names));
		foreach (array_keys(self::GRANDFATHERED) as $name) {
			self::assertContains($name, $names, 'the frozen list names a migration that is gone');
		}
	}

	public function testTheScannerSeesAnImportAndAQualifiedName(): void {
		// Planted counter samples: the shape of the bug of 1.6.3, and the same
		// reference without an import. A scanner that misses either is no rule.
		$withImport = "<?php\nnamespace OCA\\Findling\\Migration;\nuse OCA\\Findling\\Service\\SettingsService;\n"
			. "class X { function f() { return SettingsService::KEY_NEW; } }\n";
		$qualified = "<?php\nnamespace OCA\\Findling\\Migration;\n"
			. "class X { function f() { return \\OCA\\Findling\\Service\\SettingsService::KEY_NEW; } }\n";
		$clean = "<?php\nnamespace OCA\\Findling\\Migration;\nuse OCP\\IAppConfig;\n"
			. "/** mentions OCA\\Findling\\Service\\SettingsService in a comment */\n"
			. "class X { const K = 'OCA\\\\Findling\\\\Service\\\\SettingsService'; }\n";

		self::assertSame(['OCA\Findling\Service\SettingsService'], self::appClassesNamedIn($withImport));
		self::assertSame(['OCA\Findling\Service\SettingsService'], self::appClassesNamedIn($qualified));
		self::assertSame([], self::appClassesNamedIn($clean));
	}
}
