<?php

declare(strict_types=1);

/**
 * The driver of scripts/ci/update_in_process_proof.sh (issue #51).
 *
 * It does inside ONE PHP process what occ app:update and the update button of
 * the apps page do: the installed release of the app is loaded, its files are
 * replaced by the new ones, and AppManager::upgradeApp() runs the migrations.
 * That is the path Installer::updateAppstoreApp() takes after the download,
 * and it is the path on which 1.6.3 died with "Undefined constant", because
 * the classes of the old release were the loaded ones.
 *
 * To be stricter than a real update, every class of the installed release is
 * loaded before the files are swapped. A real update loads only what the
 * request touched; here nothing of the new release can slip in through the
 * autoloader, so a migration that needs a symbol of its own release fails for
 * certain and not by chance.
 *
 * Usage, as the web server user, inside a Nextcloud container:
 *
 *     php update_in_process_driver.php <app id> <directory with the new app>
 *
 * Exit code 0 and a line "UPDATE-PROOF ok ..." when the update went through
 * and the facts hold; exit code 1 and a line "UPDATE-PROOF failed ..." with
 * the class and the message of what was thrown otherwise. The caller decides
 * which of the two it expected.
 */

if ($argc !== 3) {
	fwrite(STDERR, "usage: php update_in_process_driver.php <app id> <directory with the new app>\n");
	exit(2);
}
[$script, $appId, $newDir] = $argv;

require_once '/var/www/html/lib/base.php';

use OCP\App\IAppManager;
use OCP\IAppConfig;
use OCP\IDBConnection;
use OCP\Server;

function proofFail(string $what): never {
	echo 'UPDATE-PROOF failed ' . $what . "\n";
	exit(1);
}

function removeTree(string $dir): void {
	$items = new RecursiveIteratorIterator(
		new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS),
		RecursiveIteratorIterator::CHILD_FIRST,
	);
	foreach ($items as $item) {
		$item->isDir() && !$item->isLink() ? rmdir($item->getPathname()) : unlink($item->getPathname());
	}
	rmdir($dir);
}

function copyTree(string $from, string $to): void {
	mkdir($to, 0o755, true);
	$items = new RecursiveIteratorIterator(
		new RecursiveDirectoryIterator($from, FilesystemIterator::SKIP_DOTS),
		RecursiveIteratorIterator::SELF_FIRST,
	);
	foreach ($items as $item) {
		$target = $to . '/' . substr($item->getPathname(), strlen($from) + 1);
		$item->isDir() ? mkdir($target, 0o755, true) : copy($item->getPathname(), $target);
	}
}

/** @return list<string> the applied migration versions of the app */
function appliedMigrations(string $appId): array {
	$qb = Server::get(IDBConnection::class)->getQueryBuilder();
	$qb->select('version')->from('migrations')->where($qb->expr()->eq('app', $qb->createNamedParameter($appId)));
	$result = $qb->executeQuery();
	$versions = array_map(static fn (array $row): string => (string)$row['version'], $result->fetchAll());
	$result->closeCursor();
	sort($versions);

	return $versions;
}

$appManager = Server::get(IAppManager::class);
if (!$appManager->isEnabledForAnyone($appId)) {
	proofFail("the app {$appId} is not enabled, so there is nothing to update");
}
$appManager->loadApp($appId);
$appPath = $appManager->getAppPath($appId);
$oldVersion = $appManager->getAppVersion($appId);
$before = appliedMigrations($appId);

// Every class of the installed release, loaded while its files are still there.
$loaded = 0;
$notLoadable = 0;
$libDir = $appPath . '/lib';
$namespace = 'OCA\\' . ucfirst($appId) . '\\';
foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator($libDir, FilesystemIterator::SKIP_DOTS)) as $file) {
	if ($file->getExtension() !== 'php') {
		continue;
	}
	$class = $namespace . str_replace('/', '\\', substr($file->getPathname(), strlen($libDir) + 1, -4));
	try {
		// A class whose parent lives in an app that is not installed here
		// (AppAPI) cannot be loaded, and a real update would not load it either.
		class_exists($class) || interface_exists($class) || trait_exists($class) || enum_exists($class) ? $loaded++ : $notLoadable++;
	} catch (Throwable) {
		$notLoadable++;
	}
}
if ($loaded < 10) {
	proofFail("only {$loaded} classes of the installed release could be loaded, the proof would measure nothing");
}
echo "UPDATE-PROOF installed {$appId} {$oldVersion}, {$loaded} classes of it loaded, {$notLoadable} not loadable, " . count($before) . " migrations applied\n";

// The swap of the files, as Installer::updateAppstoreApp() does it.
if (!is_file($newDir . '/appinfo/info.xml')) {
	proofFail("{$newDir} holds no appinfo/info.xml");
}
removeTree($appPath);
copyTree($newDir, $appPath);
if (function_exists('opcache_reset')) {
	opcache_reset();
}
if (method_exists($appManager, 'clearAppsCache')) {
	$appManager->clearAppsCache();
}
// Read with a pattern and not with an XML parser: the file carries long
// comments, and the element itself is the only place the pattern can match.
$newVersion = preg_match('#<version>([^<\s]+)</version>#', (string)file_get_contents($appPath . '/appinfo/info.xml'), $m) === 1 ? $m[1] : '';
if ($newVersion === '') {
	proofFail('the new appinfo/info.xml carries no version');
}

try {
	$appManager->upgradeApp($appId);
} catch (Throwable $e) {
	proofFail(get_class($e) . ': ' . $e->getMessage() . ' in ' . basename($e->getFile()) . ':' . $e->getLine());
}

// The facts after the update, read from the database and not from the caches.
$after = appliedMigrations($appId);
$expected = array_map(
	static fn (string $path): string => substr(basename($path, '.php'), strlen('Version')),
	glob($appPath . '/lib/Migration/Version*.php') ?: [],
);
sort($expected);
$missing = array_values(array_diff($expected, $after));
if ($missing !== []) {
	proofFail('these migrations of the new release were not applied: ' . implode(', ', $missing));
}
$appConfig = Server::get(IAppConfig::class);
$appConfig->clearCache();
$installed = $appConfig->getValueString($appId, 'installed_version', '');
if ($installed !== $newVersion) {
	proofFail("installed_version is {$installed} and not {$newVersion}");
}
$new = array_values(array_diff($after, $before));
echo "UPDATE-PROOF ok {$appId} {$oldVersion} -> {$newVersion}, migrations applied in this run: " . ($new === [] ? 'none' : implode(', ', $new)) . "\n";
