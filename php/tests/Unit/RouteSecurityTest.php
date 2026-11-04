<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Tests\RouteSecurity\Fixture\ClassLevelFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\CsrfFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\PlainFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\PublicFixture;
use OCA\Findling\Tests\RouteSecurity\Fixture\RateLimitFixture;
use OCA\Findling\Tests\RouteSecurity\RouteProfiles;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

require_once dirname(__DIR__) . '/RouteSecurity/Fixtures.php';

/**
 * The route attribute gate (plan 42-02).
 *
 * Every public method under lib/Controller that carries a route attribute is
 * read by reflection, together with every attribute out of
 * OCP\AppFramework\Http\Attribute on the method and on its class, and the
 * result has to match tests/route-security.json exactly. A new route, a changed
 * attribute set, a changed verb or url and an orphaned allowlist entry each
 * turn this red with the Controller::method in the message, so a change to the
 * attack surface of the app is always a visible line in a review.
 *
 * Two rules hold independently of the allowlist: PublicPage only together with
 * AnonRateLimit or BruteForceProtection, and NoCSRFRequired only on GET or
 * together with ExAppRequired.
 *
 * What this does not claim: it reads attributes, not method bodies. The check
 * rejectForeignCaller inside the ExApp endpoints stays the business of the
 * textual gate backend/tests/test_php_trust_boundary.py.
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
			'ClassLevelFixture::first' => ['route' => 'FrontpageRoute GET /first', 'attributes' => ['NoAdminRequired']],
			'ClassLevelFixture::second' => ['route' => 'FrontpageRoute POST /second', 'attributes' => ['NoAdminRequired']],
			'RateLimitFixture::limited' => ['route' => 'FrontpageRoute POST /limited', 'attributes' => ['UserRateLimit(limit=5, period=60)']],
			'CsrfFixture::post' => ['route' => 'FrontpageRoute POST /post', 'attributes' => ['NoCSRFRequired']],
			'CsrfFixture::get' => ['route' => 'FrontpageRoute GET /get', 'attributes' => ['NoCSRFRequired']],
			'CsrfFixture::exapp' => ['route' => 'FrontpageRoute POST /exapp', 'attributes' => ['ExAppRequired', 'NoCSRFRequired']],
		];
	}

	/** @return array<string, array{route: string, attributes: list<string>}> */
	private static function fixtureProfiles(): array {
		return array_merge(
			RouteProfiles::ofClass(PlainFixture::class),
			RouteProfiles::ofClass(PublicFixture::class),
			RouteProfiles::ofClass(ClassLevelFixture::class),
			RouteProfiles::ofClass(RateLimitFixture::class),
			RouteProfiles::ofClass(CsrfFixture::class),
		);
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

	public function testAClassAttributeCountsForEveryRouteMethod(): void {
		$profiles = RouteProfiles::ofClass(ClassLevelFixture::class);

		$this->assertSame(['ClassLevelFixture::first', 'ClassLevelFixture::second'], array_keys($profiles));
		$this->assertSame(['NoAdminRequired'], $profiles['ClassLevelFixture::first']['attributes']);
		$this->assertSame(['NoAdminRequired'], $profiles['ClassLevelFixture::second']['attributes']);
	}

	public function testPublicPageNeedsARateLimitOrBruteForceProtection(): void {
		$violations = RouteProfiles::violations(RouteProfiles::ofClass(PublicFixture::class));

		$this->assertCount(1, $violations);
		$this->assertStringContainsString('PublicFixture::open', $violations[0]);
		$this->assertStringContainsString('PublicPage', $violations[0]);
	}

	public function testNoCsrfRequiredNeedsGetOrExAppRequired(): void {
		$violations = RouteProfiles::violations(RouteProfiles::ofClass(CsrfFixture::class));

		$this->assertCount(1, $violations);
		$this->assertStringContainsString('CsrfFixture::post', $violations[0]);
		$this->assertStringContainsString('NoCSRFRequired', $violations[0]);
	}

	public function testForeignAttributesAndMethodsWithoutARouteStayOut(): void {
		$profiles = RouteProfiles::ofClass(PlainFixture::class);

		$this->assertSame(['PlainFixture::route'], array_keys($profiles));
		$this->assertSame(['NoAdminRequired'], $profiles['PlainFixture::route']['attributes']);
	}

	private static function controllerDir(): string {
		return dirname(__DIR__, 2) . '/lib/Controller';
	}

	/** @return array<string, array{route: string, attributes: list<string>}> */
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

	public function testNoControllerRouteBreaksTheTwoRules(): void {
		$violations = RouteProfiles::violations(self::realProfiles());

		$this->assertSame([], $violations, implode("\n", $violations));
	}

	/**
	 * Anti vacuity: a reader that silently finds nothing would make both tests
	 * above green. Seven controllers and twenty routes on 04.11.2026, the same
	 * floor as in test_php_trust_boundary.py; every new route moves the
	 * allowlist and this floor with it.
	 */
	public function testTheReaderSeesEveryControllerAndEveryRoute(): void {
		$files = glob(self::controllerDir() . '/*.php');
		$this->assertIsArray($files);

		$classes = RouteProfiles::classesIn(self::controllerDir(), 'OCA\\Findling\\Controller');
		$this->assertCount(count($files), $classes);
		$this->assertCount(7, $classes);
		$this->assertGreaterThanOrEqual(20, count(self::realProfiles()));
	}

	/** A route declared in appinfo/routes.php would bypass this gate entirely. */
	public function testAppinfoRoutesDeclaresNoRoute(): void {
		$routes = require dirname(__DIR__, 2) . '/appinfo/routes.php';

		$this->assertSame(['routes' => [], 'ocs' => []], $routes);
	}

	/**
	 * The gate fires on the real tree, not only on fixtures: a missing entry is
	 * reported as unlisted, an added PublicPage as changed, each by its key.
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
	}
}
