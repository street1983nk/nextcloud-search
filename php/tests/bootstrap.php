<?php

declare(strict_types=1);

/**
 * Bootstrap of the PHPUnit suite of the companion app.
 *
 * The suite mocks OCP interfaces, so OCP has to exist before the first test
 * class is loaded. There is exactly one supported way to get it: run inside a
 * checkout of nextcloud/server, with this app in apps/findling, and let the
 * bootstrap of the server define the world first. That is what every Nextcloud
 * app does and what docs/testing.md, section "What closes it", asks for.
 *
 * Order matters and is the reason this file exists at all. The server bootstrap
 * comes first, because it is what makes OCP resolvable; the composer autoloader
 * of this app comes second and adds two prefixes on top, OCA\Findling for the
 * code under test and OCA\Findling\Tests for the tests themselves.
 *
 * The failure this file is written to prevent is the one that costs an hour: a
 * missing or misplaced server checkout surfaces thirty lines later as "Class
 * OCP\Files\IRootFolder not found" inside a test case, which reads like a broken
 * test and is really a broken path. So the path is checked here, once, and the
 * message says what is missing and how it is set.
 */

/**
 * Where the server checkout is.
 *
 * The default is the position the CI job produces, and the job is what defines
 * it: the server sits at the root of the workspace, and the php directory of
 * this repository is MOVED to apps/findling rather than placed inside it. So
 * this file ends up at apps/findling/tests/bootstrap.php and the server root is
 * three levels above this directory, not four. The difference is one level and
 * it was measured rather than counted: run 33772152218 aborted here with the
 * message below, which is the guard doing its job on its first outing.
 *
 * NEXTCLOUD_SERVER_ROOT overrides the default for any other layout.
 */
$serverRoot = getenv('NEXTCLOUD_SERVER_ROOT');
if (!is_string($serverRoot) || $serverRoot === '') {
	$serverRoot = dirname(__DIR__, 3);
	$origin = 'the default layout, three levels above ' . __DIR__;
} else {
	$origin = 'the environment variable NEXTCLOUD_SERVER_ROOT';
}

$serverBootstrap = rtrim($serverRoot, '/\\') . '/tests/bootstrap.php';

if (!is_file($serverBootstrap)) {
	fwrite(STDERR, <<<MESSAGE

		Findling test bootstrap: no nextcloud/server checkout at this path.

		  looked for : {$serverBootstrap}
		  taken from : {$origin}

		This suite mocks OCP interfaces, so it can only run inside a checkout of
		nextcloud/server with this app placed in apps/findling. Point
		NEXTCLOUD_SERVER_ROOT at the root of that checkout, or move the app into
		apps/findling of one. The job "phpunit" in .github/workflows/php.yml is
		the reference layout; there is no PHP on the development machine, so the
		suite is CI only by design.


		MESSAGE);
	exit(1);
}

require_once $serverBootstrap;

/**
 * The autoloader of this app, second on purpose. It carries OCA\Findling from
 * the autoload section and OCA\Findling\Tests from autoload-dev, and it is the
 * same file PHPUnit itself was started through, so requiring it again is a no-op
 * for everything already registered.
 */
$appAutoload = dirname(__DIR__) . '/vendor/autoload.php';

if (!is_file($appAutoload)) {
	fwrite(STDERR, <<<MESSAGE

		Findling test bootstrap: no vendor/autoload.php next to this suite.

		  looked for : {$appAutoload}

		Run "composer install" in the php directory of this app first.


		MESSAGE);
	exit(1);
}

require_once $appAutoload;
