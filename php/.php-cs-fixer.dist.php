<?php

/**
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

declare(strict_types=1);

// Style gate of the companion app (job php-cs in .github/workflows/php.yml,
// script scripts/ci/php_cs_gate.sh): the rule set of nextcloud/coding-standard
// as it is, over every PHP directory of the app. No rule is overridden here.
require_once __DIR__ . '/tools/php-cs-fixer/vendor/autoload.php';

use Nextcloud\CodingStandard\Config;

$config = new Config();
$config
	->getFinder()
	->in([
		__DIR__ . '/lib',
		__DIR__ . '/appinfo',
		__DIR__ . '/templates',
		__DIR__ . '/tests',
	]);

return $config;
