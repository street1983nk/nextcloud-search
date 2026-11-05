<?php

declare(strict_types=1);

/**
 * A base class with two route methods, declared outside the fixture directory
 * on purpose (plan 42-04).
 *
 * The router enumerates every method of a controller class, inherited ones
 * included, so a route method in a base class elsewhere in lib/ serves a route
 * under the name of the concrete controller. The gate profiles it under the
 * concrete class and reports the file it is declared in. Loaded with
 * require_once by Fixtures.php, not over PSR-4.
 */

namespace OCA\Findling\Tests\RouteSecurity\Fixture;

use OCP\AppFramework\Http\Attribute\FrontpageRoute;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;

abstract class BaseFixture {
	#[NoAdminRequired]
	#[FrontpageRoute(verb: 'GET', url: '/inherited')]
	public function inherited(): void {
	}

	/**
	 * A route method with a docblock annotation, inherited by a fixture.
	 *
	 * @NoCSRFRequired
	 */
	#[FrontpageRoute(verb: 'POST', url: '/base-annotated')]
	public function annotated(): void {
	}
}
