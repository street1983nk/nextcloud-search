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
use OCP\AppFramework\Http\Attribute\ApiRoute;
use OCP\AppFramework\Http\Attribute\AppApiAdminAccessWithoutUser;
use OCP\AppFramework\Http\Attribute\AuthorizedAdminSetting;
use OCP\AppFramework\Http\Attribute\BruteForceProtection;
use OCP\AppFramework\Http\Attribute\CORS;
use OCP\AppFramework\Http\Attribute\ExAppRequired;
use OCP\AppFramework\Http\Attribute\FrontpageRoute;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\AppFramework\Http\Attribute\NoSameSiteCookieRequired;
use OCP\AppFramework\Http\Attribute\NoTwoFactorRequired;
use OCP\AppFramework\Http\Attribute\PublicPage;
use OCP\AppFramework\Http\Attribute\Route;
use OCP\AppFramework\Http\Attribute\SubAdminRequired;
use OCP\AppFramework\Http\Attribute\UseSession;
use OCP\AppFramework\Http\Attribute\UserRateLimit;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\IRequest;
use OCP\Settings\IDelegatedSettings;

require_once __DIR__ . '/Outside/BaseFixture.php';

/** An attribute from outside OCP\AppFramework\Http\Attribute, which the profile has to ignore. */
#[\Attribute(\Attribute::TARGET_CLASS | \Attribute::TARGET_METHOD)]
final class Foreign {
}

/** One plain route, one public method without a route, and a harmless PHP attribute. */
final class PlainFixture {
	#[NoAdminRequired]
	#[\ReturnTypeWillChange]
	#[FrontpageRoute(verb: 'GET', url: '/plain')]
	public function route(): void {
	}

	#[NoAdminRequired]
	public function helper(): void {
	}
}

/**
 * PublicPage without a rate limit, with one, and with BruteForceProtection
 * alone, which registers an attempt only when the response calls throttle(),
 * for rule R1.
 */
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

	#[PublicPage]
	#[BruteForceProtection(action: 'x')]
	#[FrontpageRoute(verb: 'GET', url: '/guarded')]
	public function guarded(): void {
	}
}

/** An attribute on the class, which the server never reads: R4, and it counts for no route method. */
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

/**
 * Attribute names in another spelling (plan 42-05). PHP resolves class names
 * case insensitively, so both act as PublicPage on the server.
 */
final class CaseFixture {
	#[\ocp\appframework\http\attribute\PublicPage]
	#[FrontpageRoute(verb: 'GET', url: '/lower-namespace')]
	public function lowerNamespace(): void {
	}

	#[\OCP\AppFramework\Http\Attribute\publicpage]
	#[FrontpageRoute(verb: 'GET', url: '/lower-short')]
	public function lowerShortName(): void {
	}
}

/** A foreign attribute, one that cannot be loaded, and a harmless PHP one. */
final class ForeignAttributeFixture {
	#[Foreign]
	#[FrontpageRoute(verb: 'GET', url: '/foreign')]
	public function foreign(): void {
	}

	#[\OCA\Findling\Tests\RouteSecurity\Fixture\DoesNotExist]
	#[FrontpageRoute(verb: 'GET', url: '/missing')]
	public function missing(): void {
	}

	#[\ReturnTypeWillChange]
	#[FrontpageRoute(verb: 'GET', url: '/harmless')]
	public function harmless(): void {
	}
}

/**
 * A rate limit that never applies: RateLimitingMiddleware takes subclasses of
 * AnonRateLimit by IS_INSTANCEOF and asks shouldApply().
 */
#[\Attribute(\Attribute::TARGET_METHOD)]
final class LooseLimit extends AnonRateLimit {
	public function shouldApply(IRequest $request): bool {
		return false;
	}
}

/** PublicPage behind the loose limit. */
final class LooseLimitFixture {
	#[PublicPage]
	#[LooseLimit(limit: 5, period: 60)]
	#[FrontpageRoute(verb: 'GET', url: '/loose')]
	public function open(): void {
	}
}

/**
 * A rate limit on the class (plan 42-06). The server reads only method
 * attributes, so it limits nothing, and PublicPage on the method stays open.
 */
#[AnonRateLimit(limit: 5, period: 60)]
final class ClassRateLimitFixture {
	#[PublicPage]
	#[FrontpageRoute(verb: 'GET', url: '/class-limited')]
	public function open(): void {
	}
}

/** root, postfix and defaults in a route attribute, named and positional. */
final class ExtrasFixture {
	#[ApiRoute(verb: 'GET', url: '/rooted', root: '/cloud')]
	public function rooted(): void {
	}

	#[ApiRoute(verb: 'GET', url: '/postfixed', postfix: 'x')]
	public function postfixed(): void {
	}

	#[ApiRoute(verb: 'GET', url: '/defaulted', defaults: ['a' => 1])]
	public function defaulted(): void {
	}

	#[ApiRoute('GET', '/positional', null, null, '/cloud', null)]
	public function positional(): void {
	}

	#[ApiRoute(verb: 'GET', url: '/constrained/{id}', requirements: ['id' => '\d+'])]
	public function constrained(): void {
	}
}

/** Loosening attributes Findling does not use, one per method. */
final class LooseningFixture {
	#[CORS]
	#[FrontpageRoute(verb: 'GET', url: '/cors')]
	public function cors(): void {
	}

	#[AppApiAdminAccessWithoutUser]
	#[FrontpageRoute(verb: 'GET', url: '/without-user')]
	public function withoutUser(): void {
	}

	#[NoTwoFactorRequired]
	#[FrontpageRoute(verb: 'GET', url: '/no-two-factor')]
	public function noTwoFactor(): void {
	}

	#[NoSameSiteCookieRequired]
	#[FrontpageRoute(verb: 'GET', url: '/no-same-site')]
	public function noSameSite(): void {
	}

	#[SubAdminRequired]
	#[FrontpageRoute(verb: 'GET', url: '/sub-admin')]
	public function subAdmin(): void {
	}

	#[AuthorizedAdminSetting(settings: 'X')]
	#[FrontpageRoute(verb: 'GET', url: '/delegated')]
	public function delegated(): void {
	}

	#[UseSession]
	#[FrontpageRoute(verb: 'GET', url: '/session')]
	public function session(): void {
	}

	#[PublicPage]
	#[ExAppRequired]
	#[AnonRateLimit(limit: 5, period: 60)]
	#[FrontpageRoute(verb: 'GET', url: '/public-exapp')]
	public function publicExApp(): void {
	}
}

/**
 * A controller that is not final (plan 42-07): a subclass could replace it
 * through the container under its short name and change every route behind
 * the pinned attributes.
 */
class OpenFixture {
	#[FrontpageRoute(verb: 'GET', url: '/open-class')]
	public function index(): void {
	}
}

/** An admin setting whose form a delegated non admin could open (C3). */
final class DelegatedFixture implements IDelegatedSettings {
	public function getForm(): TemplateResponse {
		return new TemplateResponse('findling', 'admin');
	}

	public function getSection(): ?string {
		return 'findling';
	}

	public function getPriority(): int {
		return 0;
	}

	public function getName(): ?string {
		return null;
	}

	public function getAuthorizedAppConfig(): array {
		return [];
	}
}
