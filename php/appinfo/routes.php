<?php

declare(strict_types=1);

/**
 * Both arrays stay empty on purpose. Every route this app exposes, the content
 * gateway, the queue endpoints and the reconcile routes (GET /mounts,
 * GET /storages/gone, GET /files/slice and, since plan 43-15, GET
 * /reconcile/doc-keys), is declared with an ApiRoute attribute on the
 * controller method that implements it, and tests/route-security.json lists
 * every one of them. The file itself has to exist, otherwise Nextcloud reports
 * a missing routes file for the app.
 */
return [
	'routes' => [],
	'ocs' => [],
];
