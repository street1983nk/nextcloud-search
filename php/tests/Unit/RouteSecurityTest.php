<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Tests\RouteSecurity\Fixture\AnnotationFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\BaseRouteFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\CaseFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\ClassLevelFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\ClassRateLimitFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\CsrfFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\ExtrasFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\ForeignAttributeFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\InheritedFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\LooseLimitFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\LooseningFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\PlainFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\PublicFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\RateLimitFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\StaticMagicFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\VisibilityFixture;
use OCA\Findling\Tests\RouteSecurity\RouteProfiles;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

require_once dirname(__DIR__) . '/RouteSecurity/Fixtures.php';

/**
 * The route attribute gate (plans 42-02 and 42-04).
 *
 * The controllers are enumerated exactly like Router::getAttributeRoutes does
 * it: only files lib/Controller/*Controller.php, every method of each class
 * without a filter (inherited, from a trait, any visibility, static), route
 * attributes matched by instanceof, keyed by the short name of the concrete
 * class. Any other entry of lib/Controller is a finding of its own.
 *
 * Each route method, together with every attribute on the method, read by its
 * canonical class name, has to match
 * tests/route-security.json exactly. A new route, a changed attribute set, a
 * changed verb or url and an orphaned allowlist entry each turn this red with
 * the Controller::method in the message, so a change to the attack surface of
 * the app is always a visible line in a review.
 *
 * What the server makes of a method is not rebuilt here: the gate asks the
 * ControllerMethodReflector of the server checkout the suite runs against, the
 * oracle, and records its annotations and the security markers it reports as
 * effective.
 *
 * Rules that hold independently of the allowlist, R1, R2 and R8 on what the
 * oracle reports as effective: R1, PublicPage only together with an
 * AnonRateLimit attribute on the method; R2, NoCSRFRequired only on GET or
 * together with ExAppRequired; R3, no docblock annotation of a security marker
 * on a route method, in any form; R4, no attribute on a controller class,
 * because the server never reads it; R5, a route method is public, not static
 * and declared inside the controller directory, and no controller defines
 * __call or __callStatic; R6, every attribute is a loadable OCP attribute,
 * whatever its spelling; R7, no defaults, root or postfix in a route; R8, none
 * of the loosening attributes Findling does not use, and never PublicPage
 * together with ExAppRequired.
 *
 * What this does not claim: it reads attributes and docblocks, not method
 * bodies. The check rejectForeignCaller inside the ExApp endpoints stays the
 * business of the textual gate backend/tests/test_php_trust_boundary.py.
 *
 * The first half runs against the fixtures in tests/RouteSecurity, which is
 * what proves each finding is reported at all; the second half runs against
 * the real controllers.
 */
#[CoversNothing]
final class RouteSecurityTest extends TestCase {
	/**
	 * The allowlist that matches the fixtures exactly, as the positive control.
	 *
	 * @return array<string, array{route: string, attributes: list<string>}>
	 */
	private static function fixtureAllowlist(): array {
		return [
			'PlainFixture::route' => ['route' => 'FrontpageRoute GET /plain', 'attributes' => ['NoAdminRequired']],
			'PublicFixture::open' => ['route' => 'FrontpageRoute GET /open', 'attributes' => ['PublicPage']],
			'PublicFixture::limited' => ['route' => 'FrontpageRoute GET /limited', 'attributes' => ['AnonRateLimit(limit=5, period=60)', 'PublicPage']],
			'PublicFixture::guarded' => ['route' => 'FrontpageRoute GET /guarded', 'attributes' => ['BruteForceProtection(action="x")', 'PublicPage']],
			'ClassLevelFixture::first' => ['route' => 'FrontpageRoute GET /first', 'attributes' => []],
			'ClassLevelFixture::second' => ['route' => 'FrontpageRoute POST /second', 'attributes' => []],
			'RateLimitFixture::limited' => ['route' => 'FrontpageRoute POST /limited', 'attributes' => ['UserRateLimit(limit=5, period=60)']],
			'CsrfFixture::post' => ['route' => 'FrontpageRoute POST /post', 'attributes' => ['NoCSRFRequired']],
			'CsrfFixture::get' => ['route' => 'FrontpageRoute GET /get', 'attributes' => ['NoCSRFRequired']],
			'CsrfFixture::exapp' => ['route' => 'FrontpageRoute POST /exapp', 'attributes' => ['ExAppRequired', 'NoCSRFRequired']],
		];
	}

	/** @return array<string, array<string, mixed>> */
	private static function fixtureProfiles(): array {
		return array_merge(
			RouteProfiles::ofClass(PlainFixture::class),
			RouteProfiles::ofClass(PublicFixture::class),
			RouteProfiles::ofClass(ClassLevelFixture::class),
			RouteProfiles::ofClass(RateLimitFixture::class),
			RouteProfiles::ofClass(CsrfFixture::class),
		);
	}

	/** The directory the fixtures count as their controller directory. */
	private static function fixtureDir(): string {
		return dirname(__DIR__) . '/RouteSecurity';
	}

	public function testAnExactAllowlistReportsNothing(): void {
		$this->assertSame([], RouteProfiles::compare(self::fixtureProfiles(), self::fixtureAllowlist()));
	}

	public function testARouteWithoutAnAllowlistEntryIsReported(): void {
		$allowed = self::fixtureAllowlist();
		unset($allowed['PlainFixture::route']);

		$this->assertSame(
			['unlisted route PlainFixture::route (FrontpageRoute GET /plain)'],
			RouteProfiles::compare(self::fixtureProfiles(), $allowed),
		);
	}

	public function testAnAddedAttributeIsAChange(): void {
		$allowed = self::fixtureAllowlist();
		$allowed['PublicFixture::open']['attributes'] = [];

		$findings = RouteProfiles::compare(self::fixtureProfiles(), $allowed);
		$this->assertCount(1, $findings);
		$this->assertStringStartsWith('changed route PublicFixture::open', $findings[0]);
		$this->assertStringContainsString('expected FrontpageRoute GET /open []', $findings[0]);
		$this->assertStringContainsString('actual FrontpageRoute GET /open [PublicPage]', $findings[0]);
	}

	public function testAnotherVerbOrUrlIsAChange(): void {
		$allowed = self::fixtureAllowlist();
		$allowed['ClassLevelFixture::first']['route'] = 'FrontpageRoute POST /first';
		$allowed['ClassLevelFixture::second']['route'] = 'FrontpageRoute POST /elsewhere';

		$findings = RouteProfiles::compare(self::fixtureProfiles(), $allowed);
		$this->assertCount(2, $findings);
		$this->assertStringStartsWith('changed route ClassLevelFixture::first', $findings[0]);
		$this->assertStringStartsWith('changed route ClassLevelFixture::second', $findings[1]);
	}

	public function testAnAllowlistEntryWithoutAMethodIsStale(): void {
		$allowed = self::fixtureAllowlist();
		$allowed['PlainFixture::gone'] = ['route' => 'FrontpageRoute GET /gone', 'attributes' => []];

		$this->assertSame(
			['stale allowlist entry PlainFixture::gone'],
			RouteProfiles::compare(self::fixtureProfiles(), $allowed),
		);
	}

	public function testTheArgumentsOfARateLimitArePartOfTheProfile(): void {
		$allowed = self::fixtureAllowlist();
		$allowed['RateLimitFixture::limited']['attributes'] = ['UserRateLimit(limit=5, period=120)'];

		$findings = RouteProfiles::compare(self::fixtureProfiles(), $allowed);
		$this->assertCount(1, $findings);
		$this->assertStringStartsWith('changed route RateLimitFixture::limited', $findings[0]);
		$this->assertStringContainsString('UserRateLimit(limit=5, period=60)', $findings[0]);
	}

	/** The server reads only method attributes, so a class attribute protects nothing. */
	public function testAClassAttributeIsAViolationAndCountsForNothing(): void {
		$profiles = RouteProfiles::ofClass(ClassLevelFixture::class);

		$this->assertSame(['ClassLevelFixture::first', 'ClassLevelFixture::second'], array_keys($profiles));
		$this->assertSame([], $profiles['ClassLevelFixture::first']['attributes']);
		$this->assertSame([], $profiles['ClassLevelFixture::second']['attributes']);
		$this->assertSame(
			['R4 ClassLevelFixture: class attribute NoAdminRequired has no effect on routes'],
			RouteProfiles::classViolations(ClassLevelFixture::class),
		);
	}

	public function testAClassRateLimitDoesNotSatisfyR1(): void {
		$this->assertSame(
			['R1 ClassRateLimitFixture::open: PublicPage without AnonRateLimit'],
			RouteProfiles::violations(RouteProfiles::ofClass(ClassRateLimitFixture::class)),
		);
		$this->assertSame(
			['R4 ClassRateLimitFixture: class attribute AnonRateLimit has no effect on routes'],
			RouteProfiles::classViolations(ClassRateLimitFixture::class),
		);
	}

	/** BruteForceProtection registers an attempt only when the response calls throttle(). */
	public function testBruteForceProtectionAloneDoesNotSatisfyR1(): void {
		$violations = RouteProfiles::violations(RouteProfiles::ofClass(PublicFixture::class));

		$this->assertContains('R1 PublicFixture::guarded: PublicPage without AnonRateLimit', $violations);
		$this->assertNotContains('R1 PublicFixture::limited: PublicPage without AnonRateLimit', $violations);
	}

	public function testRootPostfixOrDefaultsInARouteIsAViolation(): void {
		$this->assertSame([
			'R7 ExtrasFixture::defaulted: route argument defaults is not allowed',
			'R7 ExtrasFixture::positional: route argument root is not allowed',
			'R7 ExtrasFixture::postfixed: route argument postfix is not allowed',
			'R7 ExtrasFixture::rooted: route argument root is not allowed',
		], RouteProfiles::violations(RouteProfiles::ofClass(ExtrasFixture::class)));
	}

	public function testALooseningAttributeIsForbidden(): void {
		$this->assertSame([
			'R8 LooseningFixture::cors: CORS is not allowed in Findling',
			'R8 LooseningFixture::delegated: AuthorizedAdminSetting is not allowed in Findling',
			'R8 LooseningFixture::noSameSite: NoSameSiteCookieRequired is not allowed in Findling',
			'R8 LooseningFixture::noTwoFactor: NoTwoFactorRequired is not allowed in Findling',
			'R8 LooseningFixture::publicExApp: PublicPage together with ExAppRequired',
			'R8 LooseningFixture::session: UseSession is not allowed in Findling',
			'R8 LooseningFixture::subAdmin: SubAdminRequired is not allowed in Findling',
			'R8 LooseningFixture::withoutUser: AppApiAdminAccessWithoutUser is not allowed in Findling',
		], RouteProfiles::violations(RouteProfiles::ofClass(LooseningFixture::class)));
	}

	public function testPublicPageNeedsAnAnonRateLimit(): void {
		$this->assertSame([
			'R1 PublicFixture::guarded: PublicPage without AnonRateLimit',
			'R1 PublicFixture::open: PublicPage without AnonRateLimit',
		], RouteProfiles::violations(RouteProfiles::ofClass(PublicFixture::class)));
	}

	public function testNoCsrfRequiredNeedsGetOrExAppRequired(): void {
		$violations = RouteProfiles::violations(RouteProfiles::ofClass(CsrfFixture::class));

		$this->assertCount(1, $violations);
		$this->assertStringContainsString('CsrfFixture::post', $violations[0]);
		$this->assertStringContainsString('NoCSRFRequired', $violations[0]);
	}

	public function testMethodsWithoutARouteStayOut(): void {
		$profiles = RouteProfiles::ofClass(PlainFixture::class);

		$this->assertSame(['PlainFixture::route'], array_keys($profiles));
		$this->assertSame(['NoAdminRequired'], $profiles['PlainFixture::route']['attributes']);
		$this->assertSame([], RouteProfiles::violations($profiles));
	}

	/**
	 * PHP resolves attribute class names case insensitively, so a lower case
	 * namespace or short name acts on the server; the profile has to name the
	 * canonical class.
	 */
	public function testALowercaseAttributeNamespaceIsCanonicalisedAndEffective(): void {
		$profiles = RouteProfiles::ofClass(CaseFixture::class);

		$this->assertSame(['PublicPage'], $profiles['CaseFixture::lowerNamespace']['attributes']);
		$this->assertSame(['PublicPage'], $profiles['CaseFixture::lowerShortName']['attributes']);
		$this->assertContains('PublicPage', $profiles['CaseFixture::lowerNamespace']['effective']);
		$this->assertContains('PublicPage', $profiles['CaseFixture::lowerShortName']['effective']);
		$this->assertSame([
			'R1 CaseFixture::lowerNamespace: PublicPage without AnonRateLimit',
			'R1 CaseFixture::lowerShortName: PublicPage without AnonRateLimit',
		], RouteProfiles::violations($profiles));
	}

	public function testAForeignOrUnknownAttributeIsAViolation(): void {
		$this->assertSame([
			'R6 ForeignAttributeFixture::foreign: attribute OCA\\Findling\\Tests\\RouteSecurity\\Fixture\\Foreign is not an OCP attribute',
			'R6 ForeignAttributeFixture::missing: attribute OCA\\Findling\\Tests\\RouteSecurity\\Fixture\\DoesNotExist cannot be loaded',
		], RouteProfiles::violations(RouteProfiles::ofClass(ForeignAttributeFixture::class)));
	}

	/** A subclass of AnonRateLimit acts as a rate limit on the server and can switch itself off. */
	public function testARateLimitSubclassIsAViolation(): void {
		$profiles = RouteProfiles::ofClass(LooseLimitFixture::class);

		$this->assertSame([
			'R1 LooseLimitFixture::open: PublicPage without AnonRateLimit',
			'R6 LooseLimitFixture::open: attribute OCA\\Findling\\Tests\\RouteSecurity\\Fixture\\LooseLimit is not an OCP attribute',
		], RouteProfiles::violations($profiles));
		$this->assertContains('AnonRateLimit', $profiles['LooseLimitFixture::open']['effective']);
	}

	/**
	 * Every form of a docblock annotation on a route method is a finding: the
	 * multi line ones the server reads, the single line one it ignores, the
	 * shouted one, the one that starts a sentence and the throttle that would
	 * override a pinned attribute. Documentation tags are not.
	 */
	public function testADocblockAnnotationOnARouteMethodIsAViolation(): void {
		$profiles = RouteProfiles::ofClass(AnnotationFixture::class);

		$this->assertSame([
			'R1 AnnotationFixture::open: PublicPage without AnonRateLimit',
			'R1 AnnotationFixture::prose: PublicPage without AnonRateLimit',
			'R2 AnnotationFixture::post: NoCSRFRequired on POST without ExAppRequired',
			'R2 AnnotationFixture::shouted: NoCSRFRequired on POST without ExAppRequired',
			'R3 AnnotationFixture::inline: docblock annotation @publicpage',
			'R3 AnnotationFixture::open: docblock annotation @publicpage',
			'R3 AnnotationFixture::post: docblock annotation @nocsrfrequired',
			'R3 AnnotationFixture::prose: docblock annotation @publicpage',
			'R3 AnnotationFixture::shouted: docblock annotation @nocsrfrequired',
			'R3 AnnotationFixture::strict: docblock annotation @strictcookierequired',
			'R3 AnnotationFixture::throttled: docblock annotation @anonratethrottle',
		], RouteProfiles::violations($profiles));
		$this->assertSame([], $profiles['AnnotationFixture::documented']['annotations']);
		$this->assertArrayNotHasKey('AnnotationFixture::helper', $profiles);
	}

	/** The oracle is the server itself, so its verdict is what the middleware does. */
	public function testTheServerOracleTreatsTheAnnotationAsEffective(): void {
		$this->assertTrue(class_exists(\OC\AppFramework\Utility\ControllerMethodReflector::class));

		$profiles = RouteProfiles::ofClass(AnnotationFixture::class);
		$this->assertContains('PublicPage', $profiles['AnnotationFixture::open']['effective']);
		$this->assertNotContains('PublicPage', $profiles['AnnotationFixture::inline']['effective']);
		$this->assertContains('NoCSRFRequired', $profiles['AnnotationFixture::shouted']['effective']);
		$this->assertContains('StrictCookiesRequired', $profiles['AnnotationFixture::strict']['effective']);
		$this->assertContains('AnonRateLimit', $profiles['AnnotationFixture::throttled']['effective']);

		// The annotation wins over the pinned attribute with limit 5.
		$this->assertSame(
			['limit' => '1', 'period' => '1'],
			RouteProfiles::oracleThrottle(AnnotationFixture::class, 'throttled', 'AnonRateThrottle'),
		);
		// Positive control: without an annotation the attribute counts.
		$this->assertSame(
			['limit' => '5', 'period' => '60'],
			RouteProfiles::oracleThrottle(PublicFixture::class, 'limited', 'AnonRateThrottle'),
		);
	}

	/** The dispatcher calls a public static method, and a hidden one through __call. */
	public function testAStaticOrNonPublicRouteMethodIsAViolation(): void {
		$profiles = RouteProfiles::ofClass(VisibilityFixture::class);

		$this->assertSame(
			['VisibilityFixture::hidden', 'VisibilityFixture::secret', 'VisibilityFixture::shared'],
			array_keys($profiles),
		);
		$this->assertSame([
			'R5 VisibilityFixture::hidden: route method is protected',
			'R5 VisibilityFixture::secret: route method is private',
			'R5 VisibilityFixture::shared: route method is static',
		], RouteProfiles::violations($profiles));
		$this->assertSame(['R5 VisibilityFixture: defines __call'], RouteProfiles::classViolations(VisibilityFixture::class));
		$this->assertSame(['R5 StaticMagicFixture: defines __callStatic'], RouteProfiles::classViolations(StaticMagicFixture::class));
		$this->assertSame([], RouteProfiles::classViolations(PlainFixture::class));

		$base = RouteProfiles::ofClass(BaseRouteFixture::class);
		$this->assertSame('Route ocs GET /base-route', $base['BaseRouteFixture::index']['route']);
	}

	public function testAnInheritedRouteMethodIsProfiledUnderTheConcreteClass(): void {
		$profiles = RouteProfiles::ofClass(InheritedFixture::class, self::fixtureDir());

		$this->assertSame([
			'InheritedFixture::annotated',
			'InheritedFixture::fromTrait',
			'InheritedFixture::inherited',
			'InheritedFixture::own',
		], array_keys($profiles));
		$this->assertSame(['NoAdminRequired'], $profiles['InheritedFixture::inherited']['attributes']);
		$this->assertContains(
			'R3 InheritedFixture::annotated: docblock annotation @nocsrfrequired',
			RouteProfiles::violations($profiles),
		);
		$this->assertContains(
			'R2 InheritedFixture::annotated: NoCSRFRequired on POST without ExAppRequired',
			RouteProfiles::violations($profiles),
		);
	}

	public function testAnInheritedRouteWithoutAnAllowlistEntryIsReported(): void {
		$allowed = [
			'InheritedFixture::annotated' => ['route' => 'FrontpageRoute POST /base-annotated', 'attributes' => []],
			'InheritedFixture::fromTrait' => ['route' => 'FrontpageRoute GET /trait', 'attributes' => []],
			'InheritedFixture::own' => ['route' => 'FrontpageRoute GET /own', 'attributes' => []],
		];

		$this->assertSame(
			['unlisted route InheritedFixture::inherited (FrontpageRoute GET /inherited)'],
			RouteProfiles::compare(RouteProfiles::ofClass(InheritedFixture::class, self::fixtureDir()), $allowed),
		);
	}

	public function testARouteMethodDeclaredOutsideTheControllerDirectoryIsAViolation(): void {
		$profiles = RouteProfiles::ofClass(InheritedFixture::class, self::fixtureDir());
		$r5 = array_values(array_filter(
			RouteProfiles::violations($profiles),
			static fn (string $violation): bool => str_starts_with($violation, 'R5 '),
		));

		$this->assertSame([
			'R5 InheritedFixture::annotated: route method is declared in tests/RouteSecurity/Outside/BaseFixture.php, outside the controller directory',
			'R5 InheritedFixture::inherited: route method is declared in tests/RouteSecurity/Outside/BaseFixture.php, outside the controller directory',
		], $r5);
		$this->assertSame('tests/RouteSecurity/Fixtures.php', $profiles['InheritedFixture::own']['declaredIn']);
		$this->assertSame('tests/RouteSecurity/Fixtures.php', $profiles['InheritedFixture::fromTrait']['declaredIn']);
	}

	public function testOnlyControllerFilesAreEnumeratedAndStrayEntriesAreReported(): void {
		$dir = sys_get_temp_dir() . '/findling-stray-' . uniqid();
		mkdir($dir);
		try {
			mkdir($dir . '/sub');
			foreach (['AController.php', 'Helper.php', '.x.php', '.marker', '.claude-active'] as $name) {
				file_put_contents($dir . '/' . $name, "<?php\n");
			}

			$this->assertSame(['.x.php', 'Helper.php', 'sub'], RouteProfiles::strayEntries($dir));
		} finally {
			foreach (['AController.php', 'Helper.php', '.x.php', '.marker', '.claude-active'] as $name) {
				@unlink($dir . '/' . $name);
			}
			@rmdir($dir . '/sub');
			@rmdir($dir);
		}

		$this->assertSame([], RouteProfiles::strayEntries(self::controllerDir()));
	}

	private static function controllerDir(): string {
		return dirname(__DIR__, 2) . '/lib/Controller';
	}

	/** @return array<string, array<string, mixed>> */
	private static function realProfiles(): array {
		return RouteProfiles::ofDirectory(self::controllerDir(), 'OCA\\Findling\\Controller');
	}

	/** @return array<string, array{route: string, attributes: list<string>}> */
	private static function realAllowlist(): array {
		return RouteProfiles::loadAllowlist(dirname(__DIR__) . '/route-security.json');
	}

	public function testEveryControllerRouteMatchesTheAllowlist(): void {
		$findings = RouteProfiles::compare(self::realProfiles(), self::realAllowlist());

		$this->assertSame([], $findings, "the routes and tests/route-security.json disagree:\n" . implode("\n", $findings));
	}

	public function testNoControllerRouteBreaksTheRules(): void {
		$violations = array_merge(
			RouteProfiles::violations(self::realProfiles()),
			RouteProfiles::classViolationsOfDirectory(self::controllerDir(), 'OCA\\Findling\\Controller'),
		);

		$this->assertSame([], $violations, implode("\n", $violations));
	}

	/**
	 * Anti vacuity: a reader that silently finds nothing would make both tests
	 * above green. Seven controllers and twenty routes on 04.11.2026, the same
	 * floor as in test_php_trust_boundary.py; every new route moves the
	 * allowlist and this floor with it. Nothing else may sit in lib/Controller.
	 */
	public function testTheReaderSeesEveryControllerAndEveryRoute(): void {
		$files = glob(self::controllerDir() . '/*.php');
		$this->assertIsArray($files);

		$classes = RouteProfiles::classesIn(self::controllerDir(), 'OCA\\Findling\\Controller');
		$this->assertCount(count($files), $classes);
		$this->assertCount(7, $classes);
		$this->assertGreaterThanOrEqual(20, count(self::realProfiles()));
		$this->assertSame([], RouteProfiles::strayEntries(self::controllerDir()));
	}

	/** A route declared in appinfo/routes.php would bypass this gate entirely. */
	public function testAppinfoRoutesDeclaresNoRoute(): void {
		$routes = require dirname(__DIR__, 2) . '/appinfo/routes.php';

		$this->assertSame(['routes' => [], 'ocs' => []], $routes);
	}

	/**
	 * The gate fires on the real tree, not only on fixtures: a missing entry is
	 * reported as unlisted, an added PublicPage as changed, a docblock
	 * annotation as R3, each by its key.
	 */
	public function testTheGateFiresOnTheRealTree(): void {
		$profiles = self::realProfiles();

		$shortened = self::realAllowlist();
		unset($shortened['SettingsController::setPause']);
		$unlisted = RouteProfiles::compare($profiles, $shortened);
		$this->assertCount(1, $unlisted);
		$this->assertStringStartsWith('unlisted route SettingsController::setPause ', $unlisted[0]);

		$widened = self::realAllowlist();
		$widened['QueueController::requeue']['attributes'][] = 'PublicPage';
		sort($widened['QueueController::requeue']['attributes'], SORT_STRING);
		$changed = RouteProfiles::compare($profiles, $widened);
		$this->assertCount(1, $changed);
		$this->assertStringStartsWith('changed route QueueController::requeue:', $changed[0]);

		$annotated = $profiles;
		$annotated['SettingsController::setPause']['annotations'] = ['publicpage'];
		$this->assertSame(
			['R3 SettingsController::setPause: docblock annotation @publicpage'],
			RouteProfiles::violations($annotated),
		);
	}
}
