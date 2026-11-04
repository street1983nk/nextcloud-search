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
use OCP\AppFramework\Http\Attribute\Route;
use OCP\AppFramework\Http\Attribute\UserRateLimit;

require_once __DIR__ . '/Outside/BaseFixture.php';

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

/**
 * Docblock annotations on route methods (plan 42-04). The server reads the
 * multi line form through ControllerMethodReflector; the gate reports every
 * form, the single line one the server ignores included.
 */
final class AnnotationFixture {
	/**
	 * Opens the route to the world.
	 *
	 * @PublicPage
	 */
	#[FrontpageRoute(verb: 'GET', url: '/annotated-open')]
	public function open(): void {
	}

	/**
	 * Drops the CSRF check.
	 *
	 * @NoCSRFRequired
	 */
	#[FrontpageRoute(verb: 'POST', url: '/annotated-post')]
	public function post(): void {
	}

	/** @PublicPage */
	#[FrontpageRoute(verb: 'GET', url: '/inline')]
	public function inline(): void {
	}

	/**
	 * Shouted, the server lowercases the name.
	 *
	 * @NOCSRFREQUIRED
	 */
	#[FrontpageRoute(verb: 'POST', url: '/shouted')]
	public function shouted(): void {
	}

	/**
	 * A sentence that happens to start with an annotation.
	 *
	 * @PublicPage is not used here, says this sentence.
	 */
	#[FrontpageRoute(verb: 'GET', url: '/prose')]
	public function prose(): void {
	}

	/**
	 * The singular annotation name of the attribute StrictCookiesRequired.
	 *
	 * @StrictCookieRequired
	 */
	#[FrontpageRoute(verb: 'GET', url: '/strict')]
	public function strict(): void {
	}

	/**
	 * The annotation wins over the attribute in RateLimitingMiddleware.
	 *
	 * @AnonRateThrottle(limit=1, period=1)
	 */
	#[AnonRateLimit(limit: 5, period: 60)]
	#[FrontpageRoute(verb: 'POST', url: '/throttled')]
	public function throttled(): void {
	}

	/**
	 * Plain documentation, nothing the server reads as a security marker.
	 *
	 * @param string $value
	 * @return void
	 * @since 1.0.0
	 * @psalm-suppress MixedAssignment
	 */
	#[FrontpageRoute(verb: 'GET', url: '/documented')]
	public function documented(string $value = ''): void {
	}

	/**
	 * Not a route, so not a profile.
	 *
	 * @PublicPage
	 */
	public function helper(): void {
	}
}

/** A route method that comes in through a trait. */
trait RouteTrait {
	#[FrontpageRoute(verb: 'GET', url: '/trait')]
	public function fromTrait(): void {
	}
}

/** Inherited, trait and own route methods, all under the concrete class. */
final class InheritedFixture extends BaseFixture {
	use RouteTrait;

	#[FrontpageRoute(verb: 'GET', url: '/own')]
	public function own(): void {
	}
}

/** Route methods the dispatcher reaches although they are static or not public. */
final class VisibilityFixture {
	#[FrontpageRoute(verb: 'GET', url: '/shared')]
	public static function shared(): void {
	}

	#[FrontpageRoute(verb: 'POST', url: '/hidden')]
	protected function hidden(): void {
	}

	#[FrontpageRoute(verb: 'POST', url: '/secret')]
	private function secret(): void {
	}

	public function __call(string $name, array $arguments): mixed {
		return null;
	}
}

/** A static magic method next to a route. */
final class StaticMagicFixture {
	public static function __callStatic(string $name, array $arguments): mixed {
		return null;
	}

	#[FrontpageRoute(verb: 'GET', url: '/static-magic')]
	public function index(): void {
	}
}

/** The base class Route itself, whose type has to be part of the profile. */
final class BaseRouteFixture {
	#[Route(Route::TYPE_API, verb: 'GET', url: '/base-route')]
	public function index(): void {
	}
}
