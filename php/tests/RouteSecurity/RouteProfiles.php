<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\RouteSecurity;

use OCP\AppFramework\Http\Attribute\Route;

/**
 * Reader, comparison and rules of the route attribute gate (plans 42-02 and
 * 42-04).
 *
 * Enumeration is the one of Router::getAttributeRoutes, the code that turns
 * attributes into routes on the server: only the files lib/Controller/
 * *Controller.php, each class with getMethods() and no filter, so inherited
 * methods, trait methods, every visibility and static methods are seen, route
 * attributes matched with IS_INSTANCEOF, and the key built from the short name
 * of the concrete class. Every other entry of the controller directory is
 * reported by strayEntries().
 *
 * What the server makes of a route method is not rebuilt here. For every route
 * method the gate asks the ControllerMethodReflector of the server checkout the
 * suite runs against, the oracle: its annotations, and for each pair of
 * annotation and attribute the security middlewares of stable34 read, whether
 * hasAnnotationOrAttribute() says yes. Without that class the reader throws,
 * it never falls back to an empty answer.
 *
 * A profile is keyed "ShortClassName::method" and has these parts:
 * "route" is "<route attribute short name> [<type>] <VERB> <url>", the type
 * only for the base class Route itself, followed by the canonical JSON of every
 * further key of Route::toArray() (requirements, defaults, root, postfix), so
 * a loosened requirement is a change as well; "verb" and "extras" (which of
 * defaults, root and postfix are set) come from the same toArray(). "attributes"
 * is the sorted, unique list of every other attribute on the method, read by
 * its canonical class name and not by its spelling in the source (plan 42-05):
 * an OCP\AppFramework\Http\Attribute as its short name, any other one by its
 * full name, each followed, if it has arguments, by "(key=value, ...)" with
 * sorted keys and JSON values. Override, ReturnTypeWillChange and Deprecated
 * drop out. "foreign" lists every attribute outside OCP, "unknown" every one
 * that cannot be loaded; both are R6. Attributes on the class are not part of
 * any profile: the server reads only method attributes (stable33 to 35), so
 * a class attribute counts for nothing and is forbidden as R4 (plan 42-06).
 * "annotations" is every docblock annotation the oracle reads plus every one
 * of SERVER_ANNOTATION_NAMES in a form the server ignores today. "effective"
 * is the sorted list of security markers the oracle reports as set; R1, R2
 * and R8 read it. "visibility", "static", "declaredIn" and "outside" describe
 * where and how the method is declared. compare() looks at route and
 * attributes only; the other parts feed the rules.
 *
 * Nothing is instantiated but route attributes, whose constructors only store
 * their arguments, and the oracle.
 */
final class RouteProfiles {
	private const ATTRIBUTE_NAMESPACE = 'OCP\\AppFramework\\Http\\Attribute\\';

	private const REFLECTOR = 'OC\\AppFramework\\Utility\\ControllerMethodReflector';

	private const NULL_LOGGER = 'Psr\\Log\\NullLogger';

	/**
	 * Pairs of annotation name and attribute short name, exactly as the
	 * middlewares of stable34 hand them to hasAnnotationOrAttribute(). The
	 * annotation of StrictCookiesRequired is singular, and
	 * AppApiAdminAccessWithoutUser has no annotation at all.
	 */
	private const ORACLE_PAIRS = [
		['PublicPage', 'PublicPage'],
		['NoCSRFRequired', 'NoCSRFRequired'],
		['NoAdminRequired', 'NoAdminRequired'],
		['ExAppRequired', 'ExAppRequired'],
		['AuthorizedAdminSetting', 'AuthorizedAdminSetting'],
		['SubAdminRequired', 'SubAdminRequired'],
		['CORS', 'CORS'],
		['PasswordConfirmationRequired', 'PasswordConfirmationRequired'],
		['NoTwoFactorRequired', 'NoTwoFactorRequired'],
		['NoSameSiteCookieRequired', 'NoSameSiteCookieRequired'],
		['UseSession', 'UseSession'],
		['StrictCookieRequired', 'StrictCookiesRequired'],
		[null, 'AppApiAdminAccessWithoutUser'],
	];

	/**
	 * Throttle annotations and the attribute they override in
	 * RateLimitingMiddleware::readLimitFromAnnotationOrAttribute.
	 */
	private const THROTTLES = [
		'AnonRateThrottle' => 'AnonRateLimit',
		'UserRateThrottle' => 'UserRateLimit',
	];

	/**
	 * Every annotation name stable34 reads anywhere, lowercased. The oracle
	 * reports everything the server reads; this list and BROAD_ANNOTATION only
	 * add the forms the server ignores today (single line docblocks, a lower
	 * case first letter), because annotations are forbidden in Findling
	 * altogether. backend/tests/test_php_surface_bans.py reads this list.
	 */
	public const SERVER_ANNOTATION_NAMES = [
		'anonratethrottle',
		'authorizedadminsetting',
		'bruteforceprotection',
		'cors',
		'exapprequired',
		'noadminrequired',
		'nocsrfrequired',
		'noincomingfederatedsharingrequired',
		'nooutgoingfederatedsharingrequired',
		'nosamesitecookierequired',
		'nosubadminrequired',
		'notwofactorrequired',
		'passwordconfirmationrequired',
		'publicpage',
		'strictcookierequired',
		'subadminrequired',
		'usesession',
		'userratethrottle',
	];

	/**
	 * PHP attributes without a meaning for routing or security; they leave the
	 * profile and are no finding. Compared case insensitively, without a leading
	 * backslash, as global names only.
	 */
	private const HARMLESS_ATTRIBUTES = ['Override', 'ReturnTypeWillChange', 'Deprecated'];

	/** The keys of Route::toArray() that R7 forbids. */
	private const ROUTE_EXTRAS = ['defaults', 'root', 'postfix'];

	/**
	 * Exceptions to R7, keyed "ShortClassName::method" to the list of route
	 * argument names that route may carry. Empty on purpose: root can lay a
	 * route over a core OCS route, and every entry here is a deliberate line a
	 * review reads.
	 */
	private const ALLOWED_ROUTE_EXTRAS = [];

	/**
	 * Attributes that loosen a check of the server and that Findling does not
	 * use (R8), as the short names the oracle reports in effective.
	 */
	private const FORBIDDEN_MARKERS = [
		'CORS',
		'AppApiAdminAccessWithoutUser',
		'NoTwoFactorRequired',
		'NoSameSiteCookieRequired',
		'SubAdminRequired',
		'AuthorizedAdminSetting',
		'UseSession',
	];

	private const BROAD_ANNOTATION = '/@(?P<annotation>[A-Za-z]\w*)/';

	/**
	 * The route profiles of one class, every method the router would see.
	 *
	 * $controllerDir is the directory the class counts as a controller of; a
	 * route method declared in a file elsewhere is marked as outside.
	 *
	 * @param class-string $class
	 * @return array<string, array<string, mixed>>
	 */
	public static function ofClass(string $class, ?string $controllerDir = null): array {
		$reflection = new \ReflectionClass($class);
		$short = $reflection->getShortName();
		$appRoot = null;
		$controllerPath = null;
		if ($controllerDir !== null) {
			$controllerPath = self::realPath($controllerDir);
			$appRoot = self::realPath(dirname($controllerDir, 2));
		}

		$profiles = [];
		foreach ($reflection->getMethods() as $method) {
			$routes = $method->getAttributes(Route::class, \ReflectionAttribute::IS_INSTANCEOF);
			if ($routes === []) {
				continue;
			}
			$methodAttributes = self::readAttributes($method->getAttributes());
			$attributes = self::sortedUnique($methodAttributes['described']);
			$foreign = self::sortedUnique($methodAttributes['foreign']);
			$unknown = self::sortedUnique($methodAttributes['unknown']);

			$oracle = self::oracle($class, $method->getName());
			$file = self::realPath((string)$method->getFileName());
			if ($appRoot !== null && str_starts_with($file, $appRoot . '/')) {
				$declaredIn = substr($file, strlen($appRoot) + 1);
			} elseif ($appRoot !== null) {
				$declaredIn = $file;
			} else {
				$declaredIn = basename($file);
			}

			$common = [
				'attributes' => $attributes,
				'foreign' => $foreign,
				'unknown' => $unknown,
				'annotations' => self::annotationsOf($method, $oracle),
				'effective' => self::effectiveOf($method, $oracle),
				'visibility' => $method->isPrivate() ? 'private' : ($method->isProtected() ? 'protected' : 'public'),
				'static' => $method->isStatic(),
				'declaredIn' => $declaredIn,
				'outside' => $controllerPath !== null && dirname($file) !== $controllerPath,
			];

			$key = $short . '::' . $method->getName();
			$multiple = count($routes) > 1;
			foreach ($routes as $index => $route) {
				$instance = self::routeInstance($route);
				$serialised = $instance->toArray();
				$profiles[$multiple ? $key . '#' . ($index + 1) : $key] = [
					'route' => self::describeRoute($instance),
					'verb' => strtoupper((string)$serialised['verb']),
					'extras' => array_values(array_intersect(self::ROUTE_EXTRAS, array_keys($serialised))),
				] + $common;
			}
		}
		ksort($profiles, SORT_STRING);
		return $profiles;
	}

	/**
	 * Every controller class of a directory, the way the router finds them:
	 * one class per file whose name ends in Controller.php, in sorted order.
	 * Entries that start with a dot and do not end in .php (markers of other
	 * tools) are skipped here and in strayEntries(). A file whose class cannot
	 * be loaded is an error and never skipped.
	 *
	 * @return list<class-string>
	 */
	public static function classesIn(string $dir, string $namespace): array {
		$dir = rtrim($dir, '/');
		$classes = [];
		foreach (self::entries($dir) as $name) {
			if (str_starts_with($name, '.') || !str_ends_with($name, 'Controller.php') || !is_file($dir . '/' . $name)) {
				continue;
			}
			$class = rtrim($namespace, '\\') . '\\' . basename($name, '.php');
			if (!class_exists($class)) {
				throw new \RuntimeException("{$dir}/{$name} does not declare the class {$class}");
			}
			$classes[] = $class;
		}
		if ($classes === []) {
			throw new \RuntimeException("no controller file in {$dir}");
		}
		return $classes;
	}

	/**
	 * Every entry of the controller directory that is not a controller file:
	 * other files, files that start with a dot and end in .php, and
	 * subdirectories, as base names in sorted order. Dot entries that do not end
	 * in .php are markers of other tools and ignored.
	 *
	 * @return list<string>
	 */
	public static function strayEntries(string $dir): array {
		$dir = rtrim($dir, '/');
		$stray = [];
		foreach (self::entries($dir) as $name) {
			if (str_starts_with($name, '.') && !str_ends_with($name, '.php')) {
				continue;
			}
			if (!str_starts_with($name, '.') && str_ends_with($name, 'Controller.php') && is_file($dir . '/' . $name)) {
				continue;
			}
			$stray[] = $name;
		}
		sort($stray, SORT_STRING);
		return $stray;
	}

	/**
	 * The profiles of every controller class of a directory.
	 *
	 * @return array<string, array<string, mixed>>
	 */
	public static function ofDirectory(string $dir, string $namespace): array {
		$profiles = [];
		foreach (self::classesIn($dir, $namespace) as $class) {
			foreach (self::ofClass($class, $dir) as $key => $profile) {
				if (isset($profiles[$key])) {
					throw new \RuntimeException("the key {$key} exists twice");
				}
				$profiles[$key] = $profile;
			}
		}
		ksort($profiles, SORT_STRING);
		return $profiles;
	}

	/**
	 * Actual profiles against the allowlist: unlisted, changed and stale, sorted.
	 *
	 * @param array<string, array<string, mixed>> $actual
	 * @param array<string, array{route: string, attributes: list<string>}> $allowed
	 * @return list<string>
	 */
	public static function compare(array $actual, array $allowed): array {
		$findings = [];
		foreach ($actual as $key => $profile) {
			if (!array_key_exists($key, $allowed)) {
				$findings[] = "unlisted route {$key} ({$profile['route']})";
				continue;
			}
			$expected = $allowed[$key];
			if ($expected['route'] !== $profile['route'] || $expected['attributes'] !== $profile['attributes']) {
				$findings[] = "changed route {$key}: expected " . self::describeProfile($expected)
					. ', actual ' . self::describeProfile($profile);
			}
		}
		foreach (array_keys($allowed) as $key) {
			if (!array_key_exists($key, $actual)) {
				$findings[] = "stale allowlist entry {$key}";
			}
		}
		sort($findings, SORT_STRING);
		return $findings;
	}

	/**
	 * The rules that hold whatever the allowlist says.
	 *
	 * R1: PublicPage, as the oracle sees it, only together with an exact
	 * AnonRateLimit attribute on the method; BruteForceProtection alone does
	 * not count, it registers an attempt only when the response calls
	 * throttle().
	 * R2: NoCSRFRequired, as the oracle sees it, only on GET or together with
	 * ExAppRequired.
	 * R3: no docblock annotation on a route method, in any form.
	 * R5: a route method is public, not static and declared in the controller
	 * directory.
	 * R6: every attribute is a loadable OCP attribute or a harmless PHP one.
	 * R7: no defaults, root or postfix in a route attribute, except as listed
	 * in ALLOWED_ROUTE_EXTRAS.
	 * R8: none of FORBIDDEN_MARKERS, and never PublicPage together with
	 * ExAppRequired.
	 *
	 * @param array<string, array<string, mixed>> $profiles
	 * @return list<string>
	 */
	public static function violations(array $profiles): array {
		$violations = [];
		foreach ($profiles as $key => $profile) {
			$names = array_map(
				static fn (string $attribute): string => explode('(', $attribute, 2)[0],
				$profile['attributes'],
			);
			$effective = $profile['effective'];
			$verb = $profile['verb'];

			if (in_array('PublicPage', $effective, true) && !in_array('AnonRateLimit', $names, true)) {
				$violations[] = "R1 {$key}: PublicPage without AnonRateLimit";
			}
			if (in_array('NoCSRFRequired', $effective, true)
				&& $verb !== 'GET'
				&& !in_array('ExAppRequired', $effective, true)) {
				$violations[] = "R2 {$key}: NoCSRFRequired on {$verb} without ExAppRequired";
			}
			$allowedExtras = self::ALLOWED_ROUTE_EXTRAS[explode('#', $key, 2)[0]] ?? [];
			foreach ($profile['extras'] as $extra) {
				if (!in_array($extra, $allowedExtras, true)) {
					$violations[] = "R7 {$key}: route argument {$extra} is not allowed";
				}
			}
			foreach (self::FORBIDDEN_MARKERS as $marker) {
				if (in_array($marker, $effective, true)) {
					$violations[] = "R8 {$key}: {$marker} is not allowed in Findling";
				}
			}
			if (in_array('PublicPage', $effective, true) && in_array('ExAppRequired', $effective, true)) {
				$violations[] = "R8 {$key}: PublicPage together with ExAppRequired";
			}
			foreach ($profile['annotations'] as $annotation) {
				$violations[] = "R3 {$key}: docblock annotation @{$annotation}";
			}
			if ($profile['static']) {
				$violations[] = "R5 {$key}: route method is static";
			}
			if ($profile['visibility'] !== 'public') {
				$violations[] = "R5 {$key}: route method is {$profile['visibility']}";
			}
			if ($profile['outside']) {
				$violations[] = "R5 {$key}: route method is declared in {$profile['declaredIn']}, outside the controller directory";
			}
			foreach ($profile['foreign'] as $name) {
				$violations[] = "R6 {$key}: attribute {$name} is not an OCP attribute";
			}
			foreach ($profile['unknown'] as $name) {
				$violations[] = "R6 {$key}: attribute {$name} cannot be loaded";
			}
		}
		sort($violations, SORT_STRING);
		return $violations;
	}

	/**
	 * The rules on the class. R4: no attribute on a controller class at all;
	 * stable33 to 35 read only method attributes, so a class attribute counts
	 * for no route and only pretends a protection. R5: a controller with
	 * __call or __callStatic of its own would let the dispatcher reach methods
	 * no route attribute names. C1 (plan 42-07): a controller is final, so no
	 * subclass can take its place through the container.
	 *
	 * @param class-string $class
	 * @return list<string>
	 */
	public static function classViolations(string $class): array {
		$reflection = new \ReflectionClass($class);
		$short = $reflection->getShortName();
		$violations = [];
		$read = self::readAttributes($reflection->getAttributes());
		foreach (array_merge($read['described'], $read['routes']) as $described) {
			$name = explode('(', $described, 2)[0];
			$violations[] = "R4 {$short}: class attribute {$name} has no effect on routes";
		}
		if (!$reflection->isFinal()) {
			$violations[] = "C1 {$short}: controller is not final";
		}
		foreach (['__call', '__callStatic'] as $magic) {
			if ($reflection->hasMethod($magic)
				&& !str_starts_with($reflection->getMethod($magic)->getDeclaringClass()->getName(), 'OCP\\')) {
				$violations[] = "R5 {$short}: defines {$magic}";
			}
		}
		return $violations;
	}

	/**
	 * classViolations() of every controller class of a directory, sorted.
	 *
	 * @return list<string>
	 */
	public static function classViolationsOfDirectory(string $dir, string $namespace): array {
		$violations = [];
		foreach (self::classesIn($dir, $namespace) as $class) {
			$violations = array_merge($violations, self::classViolations($class));
		}
		sort($violations, SORT_STRING);
		return $violations;
	}

	/**
	 * Every class of a directory, one class per *.php file, sorted; for
	 * directories that are not enumerated by the router, such as lib/Settings.
	 * A file whose class cannot be loaded is an error.
	 *
	 * @return list<class-string>
	 */
	public static function classesOf(string $dir, string $namespace): array {
		$files = glob(rtrim($dir, '/') . '/*.php');
		if ($files === false || $files === []) {
			throw new \RuntimeException("no PHP file in {$dir}");
		}
		sort($files, SORT_STRING);
		$classes = [];
		foreach ($files as $file) {
			$class = rtrim($namespace, '\\') . '\\' . basename($file, '.php');
			if (!class_exists($class)) {
				throw new \RuntimeException("{$file} does not declare the class {$class}");
			}
			$classes[] = $class;
		}
		return $classes;
	}

	/**
	 * The class profile of each controller (plan 42-07), keyed by short name:
	 * whether it is final, its parent chain up to the root, the traits of the
	 * class and of every parent, and its interfaces, each by canonical name.
	 *
	 * @param list<class-string> $classes
	 * @return array<string, array{final: bool, parents: list<string>, traits: list<string>, interfaces: list<string>}>
	 */
	public static function classProfiles(array $classes): array {
		$profiles = [];
		foreach ($classes as $class) {
			$reflection = new \ReflectionClass($class);
			$parents = [];
			$traits = $reflection->getTraitNames();
			for ($parent = $reflection->getParentClass(); $parent !== false; $parent = $parent->getParentClass()) {
				$parents[] = $parent->getName();
				$traits = array_merge($traits, $parent->getTraitNames());
			}
			$interfaces = $reflection->getInterfaceNames();
			$short = $reflection->getShortName();
			if (isset($profiles[$short])) {
				throw new \RuntimeException("the class {$short} exists twice");
			}
			$profiles[$short] = [
				'final' => $reflection->isFinal(),
				'parents' => $parents,
				'traits' => self::sortedUnique($traits),
				'interfaces' => self::sortedUnique($interfaces),
			];
		}
		ksort($profiles, SORT_STRING);
		return $profiles;
	}

	/**
	 * Class profiles against the "classes" allowlist: unlisted, changed and
	 * stale, sorted.
	 *
	 * @param array<string, array<string, mixed>> $actual
	 * @param array<string, array<string, mixed>> $allowed
	 * @return list<string>
	 */
	public static function compareClasses(array $actual, array $allowed): array {
		$findings = [];
		foreach ($actual as $short => $profile) {
			if (!array_key_exists($short, $allowed)) {
				$findings[] = "unlisted class {$short}";
				continue;
			}
			$expected = self::canonicalJson($allowed[$short]);
			$found = self::canonicalJson($profile);
			if ($expected !== $found) {
				$findings[] = "changed class {$short}: expected {$expected}, actual {$found}";
			}
		}
		foreach (array_keys($allowed) as $short) {
			if (!array_key_exists($short, $actual)) {
				$findings[] = "stale class entry {$short}";
			}
		}
		sort($findings, SORT_STRING);
		return $findings;
	}

	/**
	 * The "classes" object of the allowlist file. Missing or malformed is an
	 * error, never an empty allowlist.
	 *
	 * @return array<string, array{final: bool, parents: list<string>, traits: list<string>, interfaces: list<string>}>
	 */
	public static function loadClassAllowlist(string $path): array {
		$raw = file_get_contents($path);
		if ($raw === false) {
			throw new \RuntimeException("{$path} is not readable");
		}
		$data = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
		if (!is_array($data) || !isset($data['classes']) || !is_array($data['classes']) || $data['classes'] === []) {
			throw new \RuntimeException("{$path} has no classes object");
		}
		$classes = [];
		foreach ($data['classes'] as $short => $entry) {
			if (!is_string($short) || !is_array($entry) || !isset($entry['final'], $entry['parents'], $entry['traits'], $entry['interfaces'])
				|| !is_bool($entry['final'])) {
				throw new \RuntimeException("{$path}: the class entry {$short} is malformed");
			}
			$lists = [];
			foreach (['parents', 'traits', 'interfaces'] as $field) {
				if (!is_array($entry[$field]) || !array_is_list($entry[$field])) {
					throw new \RuntimeException("{$path}: {$field} of the class entry {$short} is not a list");
				}
				foreach ($entry[$field] as $value) {
					if (!is_string($value)) {
						throw new \RuntimeException("{$path}: {$field} of the class entry {$short} has a non string value");
					}
				}
				$lists[$field] = $entry[$field];
			}
			$classes[$short] = [
				'final' => $entry['final'],
				'parents' => $lists['parents'],
				'traits' => $lists['traits'],
				'interfaces' => $lists['interfaces'],
			];
		}
		return $classes;
	}

	/**
	 * C3: no admin setting may be delegable to a non admin.
	 *
	 * @param list<class-string> $classes
	 * @return list<string>
	 */
	public static function delegatedSettings(array $classes): array {
		$findings = [];
		foreach ($classes as $class) {
			$reflection = new \ReflectionClass($class);
			if ($reflection->implementsInterface('OCP\\Settings\\IDelegatedSettings')) {
				$findings[] = "C3 {$reflection->getShortName()}: implements IDelegatedSettings";
			}
		}
		sort($findings, SORT_STRING);
		return $findings;
	}

	/**
	 * The limit and period RateLimitingMiddleware would apply for a throttle
	 * annotation name, as the oracle reads them: the annotation when it has both
	 * values, otherwise the attribute (IS_INSTANCEOF), otherwise empty strings.
	 *
	 * @param class-string $class
	 * @return array{limit: string, period: string}
	 */
	public static function oracleThrottle(string $class, string $method, string $annotation): array {
		if (!isset(self::THROTTLES[$annotation])) {
			throw new \RuntimeException("{$annotation} is not a throttle annotation");
		}
		$oracle = self::oracle($class, $method);
		$limit = $oracle->getAnnotationParameter($annotation, 'limit');
		$period = $oracle->getAnnotationParameter($annotation, 'period');
		if ($limit !== '' && $period !== '') {
			return ['limit' => $limit, 'period' => $period];
		}

		$attributes = (new \ReflectionMethod($class, $method))->getAttributes(
			self::ATTRIBUTE_NAMESPACE . self::THROTTLES[$annotation],
			\ReflectionAttribute::IS_INSTANCEOF,
		);
		if ($attributes !== []) {
			$instance = $attributes[0]->newInstance();
			return ['limit' => (string)$instance->getLimit(), 'period' => (string)$instance->getPeriod()];
		}
		return ['limit' => '', 'period' => ''];
	}

	/**
	 * The "routes" object of the allowlist file; the top level "_comment" is
	 * documentation and ignored.
	 *
	 * @return array<string, array{route: string, attributes: list<string>}>
	 */
	public static function loadAllowlist(string $path): array {
		$raw = file_get_contents($path);
		if ($raw === false) {
			throw new \RuntimeException("{$path} is not readable");
		}
		$data = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
		if (!is_array($data) || !isset($data['routes']) || !is_array($data['routes'])) {
			throw new \RuntimeException("{$path} has no routes object");
		}
		unset($data['_comment']);

		$routes = [];
		foreach ($data['routes'] as $key => $entry) {
			if (!is_string($key) || !is_array($entry)
				|| !isset($entry['route'], $entry['attributes'])
				|| !is_string($entry['route']) || !is_array($entry['attributes'])
				|| !array_is_list($entry['attributes'])) {
				throw new \RuntimeException("{$path}: the entry {$key} is malformed");
			}
			$attributes = [];
			foreach ($entry['attributes'] as $attribute) {
				if (!is_string($attribute)) {
					throw new \RuntimeException("{$path}: the entry {$key} has a non string attribute");
				}
				$attributes[] = $attribute;
			}
			$routes[$key] = ['route' => $entry['route'], 'attributes' => $attributes];
		}
		return $routes;
	}

	/**
	 * A fresh ControllerMethodReflector of the server, reflected on one method.
	 * Fail closed: without the class there is no answer, not an empty one.
	 *
	 * @param class-string $class
	 */
	private static function oracle(string $class, string $method): object {
		if (!class_exists(self::REFLECTOR) || !class_exists(self::NULL_LOGGER)) {
			throw new \RuntimeException('the ControllerMethodReflector of the server checkout is not loadable, the gate cannot ask the server');
		}
		$reflectorClass = self::REFLECTOR;
		$loggerClass = self::NULL_LOGGER;
		$reflector = new $reflectorClass(new $loggerClass());
		$reflector->reflect($class, $method);
		return $reflector;
	}

	/**
	 * The annotations of the oracle plus every server annotation name the broad
	 * pattern finds in the docblock, lowercased, unique and sorted.
	 *
	 * @return list<string>
	 */
	private static function annotationsOf(\ReflectionMethod $method, object $oracle): array {
		$names = array_map('strval', array_keys($oracle->annotations));
		$docs = $method->getDocComment();
		if ($docs !== false && preg_match_all(self::BROAD_ANNOTATION, $docs, $matches) > 0) {
			foreach ($matches['annotation'] as $name) {
				$lower = strtolower($name);
				if (in_array($lower, self::SERVER_ANNOTATION_NAMES, true)) {
					$names[] = $lower;
				}
			}
		}
		$names = array_values(array_unique($names));
		sort($names, SORT_STRING);
		return $names;
	}

	/**
	 * The security markers the oracle reports as set, as attribute short names.
	 *
	 * @return list<string>
	 */
	private static function effectiveOf(\ReflectionMethod $method, object $oracle): array {
		$effective = [];
		foreach (self::ORACLE_PAIRS as [$annotation, $attribute]) {
			if ($oracle->hasAnnotationOrAttribute($annotation, self::ATTRIBUTE_NAMESPACE . $attribute)) {
				$effective[] = $attribute;
			}
		}
		foreach (self::THROTTLES as $annotation => $attribute) {
			$fromAnnotation = $oracle->getAnnotationParameter($annotation, 'limit') !== ''
				&& $oracle->getAnnotationParameter($annotation, 'period') !== '';
			$fromAttribute = $method->getAttributes(self::ATTRIBUTE_NAMESPACE . $attribute, \ReflectionAttribute::IS_INSTANCEOF) !== [];
			if ($fromAnnotation || $fromAttribute) {
				$effective[] = $attribute;
			}
		}
		if ($oracle->hasAnnotation('BruteForceProtection')
			|| $method->getAttributes(self::ATTRIBUTE_NAMESPACE . 'BruteForceProtection') !== []) {
			$effective[] = 'BruteForceProtection';
		}
		sort($effective, SORT_STRING);
		return $effective;
	}

	/** @return list<string> */
	private static function entries(string $dir): array {
		$entries = is_dir($dir) ? scandir($dir) : false;
		if ($entries === false) {
			throw new \RuntimeException("{$dir} is not a readable directory");
		}
		return array_values(array_filter($entries, static fn (string $name): bool => $name !== '.' && $name !== '..'));
	}

	private static function realPath(string $path): string {
		$real = realpath($path);
		if ($real === false) {
			throw new \RuntimeException("{$path} does not exist");
		}
		return str_replace('\\', '/', $real);
	}

	/**
	 * @param list<string> $values
	 * @return list<string>
	 */
	private static function sortedUnique(array $values): array {
		$values = array_values(array_unique($values));
		sort($values, SORT_STRING);
		return $values;
	}

	/**
	 * Every class of OCP\AppFramework\Http\Attribute in the server checkout,
	 * loaded under its real name and keyed by its lowercased name (plan 42-05).
	 * The autoloader looks names up case sensitively, so a lower case spelling
	 * in an attribute is resolved here and not by class_exists(). An empty table
	 * is an error, never an empty answer.
	 *
	 * @return array<string, string>
	 */
	private static function ocpAttributes(): array {
		static $table = null;
		if ($table !== null) {
			return $table;
		}
		$files = glob(\OC::$SERVERROOT . '/lib/public/AppFramework/Http/Attribute/*.php');
		$table = [];
		foreach ($files === false ? [] : $files as $file) {
			$class = self::ATTRIBUTE_NAMESPACE . basename($file, '.php');
			if (class_exists($class)) {
				$table[strtolower($class)] = (new \ReflectionClass($class))->getName();
			}
		}
		if ($table === []) {
			$table = null;
			throw new \RuntimeException('no class of OCP\\AppFramework\\Http\\Attribute is loadable from the server checkout');
		}
		return $table;
	}

	/**
	 * The attributes of a method or class, each by its canonical class name:
	 * the OCP table first, then ReflectionClass::getName() of a loadable class,
	 * so the spelling in the source never decides. Route attributes go to
	 * "routes" only, the harmless PHP attributes drop out. OCP attributes are described by their
	 * short name, every other one by its full canonical name and is also listed
	 * as foreign; a name that cannot be loaded is listed as unknown.
	 *
	 * @param list<\ReflectionAttribute<object>> $attributes
	 * @return array{described: list<string>, foreign: list<string>, unknown: list<string>, routes: list<string>}
	 */
	private static function readAttributes(array $attributes): array {
		$read = ['described' => [], 'foreign' => [], 'unknown' => [], 'routes' => []];
		$harmless = array_map('strtolower', self::HARMLESS_ATTRIBUTES);
		foreach ($attributes as $attribute) {
			$raw = ltrim($attribute->getName(), '\\');
			$lower = strtolower($raw);
			if (in_array($lower, $harmless, true)) {
				continue;
			}
			$ocp = self::ocpAttributes();
			if (isset($ocp[$lower])) {
				$name = $ocp[$lower];
			} elseif (class_exists($raw)) {
				$name = (new \ReflectionClass($raw))->getName();
			} else {
				$read['unknown'][] = $raw;
				$read['described'][] = $raw;
				continue;
			}
			if (is_a($name, Route::class, true)) {
				$read['routes'][] = str_starts_with($name, self::ATTRIBUTE_NAMESPACE)
					? substr($name, strlen(self::ATTRIBUTE_NAMESPACE))
					: $name;
				continue;
			}

			$isOcp = str_starts_with($name, self::ATTRIBUTE_NAMESPACE);
			$label = $isOcp ? substr($name, strlen(self::ATTRIBUTE_NAMESPACE)) : $name;
			if (!$isOcp) {
				$read['foreign'][] = $name;
			}
			$arguments = $attribute->getArguments();
			if ($arguments === []) {
				$read['described'][] = $label;
				continue;
			}
			$pairs = [];
			foreach ($arguments as $key => $value) {
				$pairs[(string)$key] = (string)$key . '=' . self::canonicalJson($value);
			}
			ksort($pairs, SORT_STRING);
			$read['described'][] = $label . '(' . implode(', ', $pairs) . ')';
		}
		return $read;
	}

	/** @param \ReflectionAttribute<object> $route */
	private static function routeInstance(\ReflectionAttribute $route): Route {
		$instance = $route->newInstance();
		if (!$instance instanceof Route) {
			throw new \RuntimeException('a route attribute is not a ' . Route::class);
		}
		return $instance;
	}

	/**
	 * The route as the router serialises it: Route::toArray() of the instance,
	 * which normalises positional and named arguments alike.
	 */
	private static function describeRoute(Route $instance): string {
		$name = get_class($instance);
		$short = str_starts_with($name, self::ATTRIBUTE_NAMESPACE)
			? substr($name, strlen(self::ATTRIBUTE_NAMESPACE))
			: $name;

		$array = $instance->toArray();
		$verb = (string)$array['verb'];
		$url = (string)$array['url'];
		unset($array['verb'], $array['url']);

		$description = $short;
		if ($name === Route::class) {
			$description .= ' ' . $instance->getType();
		}
		$description .= ' ' . $verb . ' ' . $url;
		if ($array !== []) {
			$description .= ' ' . self::canonicalJson($array);
		}
		return $description;
	}

	/** @param array<string, mixed> $profile */
	private static function describeProfile(array $profile): string {
		return $profile['route'] . ' [' . implode(', ', $profile['attributes']) . ']';
	}

	private static function canonicalJson(mixed $value): string {
		return json_encode(self::canonical($value), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
	}

	private static function canonical(mixed $value): mixed {
		if (!is_array($value)) {
			return $value;
		}
		$value = array_map(self::canonical(...), $value);
		if (!array_is_list($value)) {
			ksort($value, SORT_STRING);
		}
		return $value;
	}
}
