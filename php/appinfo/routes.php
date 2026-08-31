<?php

declare(strict_types=1);

/**
 * Both arrays stay empty on purpose. Every route this app exposes, the content
 * gateway and the four queue endpoints, is declared with an ApiRoute attribute
 * on the controller method that implements it. The file itself has to exist,
 * otherwise Nextcloud reports a missing routes file for the app.
 */
return [
	'routes' => [],
	'ocs' => [],
];
