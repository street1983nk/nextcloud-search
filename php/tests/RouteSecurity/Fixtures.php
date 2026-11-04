<?php

declare(strict_types=1);

/**
 * Fixture classes of RouteSecurityTest, several in one file on purpose.
 *
 * They carry the real OCP attributes and nothing else: none of them extends
 * Controller, because reflection needs no constructor and no container. The
 * file is loaded with require_once by the test and not over PSR-4, which is why
 * the namespace does not match the path.
 */

namespace OCA\Findling\Tests\RouteSecurity\Fixture;

use OCP\AppFramework\Http\Attribute\AnonRateLimit;
use OCP\AppFramework\Http\Attribute\ExAppRequired;
use OCP\AppFramework\Http\Attribute\FrontpageRoute;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\AppFramework\Http\Attribute\PublicPage;
use OCP\AppFramework\Http\Attribute\UserRateLimit;

/** An attribute from outside OCP\AppFramework\Http\Attribute, which the profile has to ignore. */
#[\Attribute(\Attribute::TARGET_CLASS | \Attribute::TARGET_METHOD)]
final class Foreign {
}

/** One plain route, one public method without a route, and two foreign attributes. */
final class PlainFixture {
	#[NoAdminRequired]
	#[Foreign]
	#[\ReturnTypeWillChange]
	#[FrontpageRoute(verb: 'GET', url: '/plain')]
	public function route(): void {
	}

	#[NoAdminRequired]
	public function helper(): void {
	}
}

/** PublicPage once without and once with a rate limit, for rule R1. */
final class PublicFixture {
	#[PublicPage]
	#[FrontpageRoute(verb: 'GET', url: '/open')]
	public function open(): void {
	}

	#[PublicPage]
	#[AnonRateLimit(limit: 5, period: 60)]
	#[FrontpageRoute(verb: 'GET', url: '/limited')]
	public function limited(): void {
	}
}

/** An attribute on the class, which has to reach the profile of every route method. */
#[NoAdminRequired]
final class ClassLevelFixture {
	#[FrontpageRoute(verb: 'GET', url: '/first')]
	public function first(): void {
	}

	#[FrontpageRoute(verb: 'POST', url: '/second')]
	public function second(): void {
	}
}

/** The arguments of a rate limit are part of the profile. */
final class RateLimitFixture {
	#[UserRateLimit(limit: 5, period: 60)]
	#[FrontpageRoute(verb: 'POST', url: '/limited')]
	public function limited(): void {
	}
}

/** NoCSRFRequired on POST without ExAppRequired, on GET, and on POST with ExAppRequired, for rule R2. */
final class CsrfFixture {
	#[NoCSRFRequired]
	#[FrontpageRoute(verb: 'POST', url: '/post')]
	public function post(): void {
	}

	#[NoCSRFRequired]
	#[FrontpageRoute(verb: 'GET', url: '/get')]
	public function get(): void {
	}

	#[ExAppRequired]
	#[NoCSRFRequired]
	#[FrontpageRoute(verb: 'POST', url: '/exapp')]
	public function exapp(): void {
	}
}
