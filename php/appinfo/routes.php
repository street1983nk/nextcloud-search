<?php

declare(strict_types=1);

/**
 * Both arrays stay empty on purpose. The only route this app exposes is the
 * content gateway, and that one is declared with an ApiRoute attribute on the
 * controller method. The file itself has to exist, otherwise Nextcloud reports
 * a missing routes file for the app.
 */
return [
	'routes' => [],
	'ocs' => [],
];
