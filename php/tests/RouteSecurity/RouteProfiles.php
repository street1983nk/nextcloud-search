<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\RouteSecurity;

use OCP\AppFramework\Http\Attribute\Route;

/**
 * Reader, comparison and rules of the route attribute gate (plan 42-02).
 *
 * Pure static functions over reflection. Nothing is instantiated, neither a
 * controller nor an attribute: ReflectionAttribute::getName() and
 * getArguments() read the attribute as PHP resolved it, imports, aliases and
 * attributes over several lines included, without running a constructor.
 *
 * A profile is keyed "ShortClassName::method" and has two parts. "route" is
 * "<route attribute short name> <VERB> <url>", followed by the canonical JSON
 * of every further route argument (requirements, defaults, root, postfix), so a
 * loosened requirement is a change as well. "attributes" is the sorted, unique
 * list of every other attribute out of OCP\AppFramework\Http\Attribute on the
 * method and on its class, each as its short name and, if it has arguments,
 * "Name(key=value, ...)" with sorted keys and JSON values. Class attributes
 * count for every method, because the security middleware reads them there
 * too.
 */
final class RouteProfiles {
	private const ATTRIBUTE_NAMESPACE = 'OCP\\AppFramework\\Http\\Attribute\\';

	/**
	 * The route profiles of one class, its own public instance methods only.
	 *
	 * @param class-string $class
	 * @return array<string, array{route: string, attributes: list<string>}>
	 */
	public static function ofClass(string $class): array {
		$reflection = new \ReflectionClass($class);
		$short = $reflection->getShortName();
		$classAttributes = self::securityAttributes($reflection->getAttributes());

		$profiles = [];
		foreach ($reflection->getMethods(\ReflectionMethod::IS_PUBLIC) as $method) {
			if ($method->isStatic() || $method->getDeclaringClass()->getName() !== $class) {
				continue;
			}
			$routes = $method->getAttributes(Route::class, \ReflectionAttribute::IS_INSTANCEOF);
			if ($routes === []) {
				continue;
			}
			$attributes = array_values(array_unique(array_merge(
				$classAttributes,
				self::securityAttributes($method->getAttributes()),
			)));
			sort($attributes, SORT_STRING);

			$key = $short . '::' . $method->getName();
			$multiple = count($routes) > 1;
			foreach ($routes as $index => $route) {
				$profiles[$multiple ? $key . '#' . ($index + 1) : $key] = [
					'route' => self::describeRoute($route),
					'attributes' => $attributes,
				];
			}
		}
		ksort($profiles, SORT_STRING);
		return $profiles;
	}

	/**
	 * Every class of a directory, one class per *.php file, in sorted order.
	 * A file whose class cannot be loaded is an error and never skipped.
	 *
	 * @return list<class-string>
	 */
	public static function classesIn(string $dir, string $namespace): array {
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
	 * The profiles of every class of a directory.
	 *
	 * @return array<string, array{route: string, attributes: list<string>}>
	 */
	public static function ofDirectory(string $dir, string $namespace): array {
		$profiles = [];
		foreach (self::classesIn($dir, $namespace) as $class) {
			foreach (self::ofClass($class) as $key => $profile) {
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
	 * @param array<string, array{route: string, attributes: list<string>}> $actual
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
	 * The two rules that hold whatever the allowlist says.
	 *
	 * R1: PublicPage only together with AnonRateLimit or BruteForceProtection.
	 * R2: NoCSRFRequired only on GET or together with ExAppRequired.
	 *
	 * @param array<string, array{route: string, attributes: list<string>}> $profiles
	 * @return list<string>
	 */
	public static function violations(array $profiles): array {
		$violations = [];
		foreach ($profiles as $key => $profile) {
			$names = array_map(
				static fn (string $attribute): string => explode('(', $attribute, 2)[0],
				$profile['attributes'],
			);
			$verb = explode(' ', $profile['route'], 3)[1] ?? '';

			if (in_array('PublicPage', $names, true)
				&& !in_array('AnonRateLimit', $names, true)
				&& !in_array('BruteForceProtection', $names, true)) {
				$violations[] = "R1 {$key}: PublicPage without AnonRateLimit or BruteForceProtection";
			}
			if (in_array('NoCSRFRequired', $names, true)
				&& $verb !== 'GET'
				&& !in_array('ExAppRequired', $names, true)) {
				$violations[] = "R2 {$key}: NoCSRFRequired on {$verb} without ExAppRequired";
			}
		}
		sort($violations, SORT_STRING);
		return $violations;
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
	 * @param list<\ReflectionAttribute<object>> $attributes
	 * @return list<string>
	 */
	private static function securityAttributes(array $attributes): array {
		$described = [];
		foreach ($attributes as $attribute) {
			$name = $attribute->getName();
			if (!str_starts_with($name, self::ATTRIBUTE_NAMESPACE) || is_a($name, Route::class, true)) {
				continue;
			}
			$short = substr($name, strlen(self::ATTRIBUTE_NAMESPACE));
			$arguments = $attribute->getArguments();
			if ($arguments === []) {
				$described[] = $short;
				continue;
			}
			$pairs = [];
			foreach ($arguments as $key => $value) {
				$pairs[(string)$key] = (string)$key . '=' . self::canonicalJson($value);
			}
			ksort($pairs, SORT_STRING);
			$described[] = $short . '(' . implode(', ', $pairs) . ')';
		}
		return $described;
	}

	/** @param \ReflectionAttribute<object> $route */
	private static function describeRoute(\ReflectionAttribute $route): string {
		$name = $route->getName();
		$short = str_starts_with($name, self::ATTRIBUTE_NAMESPACE)
			? substr($name, strlen(self::ATTRIBUTE_NAMESPACE))
			: $name;
		$arguments = $route->getArguments();

		// The base class Route takes the type first, its subclasses start with the verb.
		$offset = $name === Route::class ? 1 : 0;
		$verb = $arguments['verb'] ?? $arguments[$offset] ?? '';
		$url = $arguments['url'] ?? $arguments[$offset + 1] ?? '';
		unset($arguments['verb'], $arguments['url'], $arguments[$offset], $arguments[$offset + 1]);

		$description = $short . ' ' . (string)$verb . ' ' . (string)$url;
		if ($arguments !== []) {
			$description .= ' ' . self::canonicalJson($arguments);
		}
		return $description;
	}

	/** @param array{route: string, attributes: list<string>} $profile */
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
