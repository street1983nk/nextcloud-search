<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\RouteSecurity;

use OCA\Findling\AppInfo\Application;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;

/**
 * The surfaces of the app that are not a controller route (plan 42-08).
 *
 * appinfo/routes.php is included by Router::requireRouteFile inside a method
 * of the router, so $this in that file is the router, and a route created
 * through it runs without the app framework and without any middleware. The
 * file may therefore consist of nothing but literal tokens: an opening tag,
 * declare(strict_types=1), comments, return, array brackets, commas, "=>" and
 * string and number literals. routesFileFindings() reports every other token.
 *
 * sourceFindings() reports, per file under lib/, every name that reaches the
 * router or the container: IRouter, getRouter, actionInclude, any name under
 * OC\Route, registerService, registerServiceAlias, registerParameter,
 * registerMiddleware and getContainer. It reads PHP tokens, not text, so a
 * comment or a string does not count, and simple, qualified and fully
 * qualified names all do.
 *
 * register() and boot() run the bootstrap of the app against a recording
 * double that the test builds from the interface of the server checkout; the
 * recorded calls are held against tests/app-surface.json by
 * compareRegistrations(). Application is created without its constructor, so
 * no app container comes into being.
 */
final class AppSurface {
	private const ROUTES_FILE_CHARS = ['(', ')', '[', ']', ',', ';', '='];

	private const ROUTES_FILE_TOKENS = [
		T_OPEN_TAG,
		T_WHITESPACE,
		T_COMMENT,
		T_DOC_COMMENT,
		T_DECLARE,
		T_LNUMBER,
		T_CONSTANT_ENCAPSED_STRING,
		T_RETURN,
		T_DOUBLE_ARROW,
	];

	private const NAME_TOKENS = [T_STRING, T_NAME_QUALIFIED, T_NAME_FULLY_QUALIFIED, T_NAME_RELATIVE];

	private const BANNED_NAMES = [
		'IRouter',
		'getRouter',
		'actionInclude',
		'registerService',
		'registerServiceAlias',
		'registerParameter',
		'registerMiddleware',
		'getContainer',
	];

	private const BANNED_NAMESPACE = 'oc\\route\\';

	/**
	 * Every token of a routes file outside the literal whitelist, as
	 * "<token name> <text> at line N", or "char <c> at line N" for a single
	 * character.
	 *
	 * @return list<string>
	 */
	public static function routesFileFindings(string $source): array {
		$findings = [];
		$significant = [];
		$line = 1;
		foreach (token_get_all($source) as $token) {
			if (is_string($token)) {
				if (!in_array($token, self::ROUTES_FILE_CHARS, true)) {
					$findings[] = "char {$token} at line {$line}";
				}
				$significant[] = $token;
				continue;
			}
			[$id, $text, $line] = $token;
			$allowed = in_array($id, self::ROUTES_FILE_TOKENS, true);
			if ($id === T_STRING) {
				$count = count($significant);
				$allowed = $text === 'strict_types'
					&& $count >= 2
					&& $significant[$count - 1] === '('
					&& $significant[$count - 2] === T_DECLARE;
			}
			if (!$allowed) {
				$findings[] = token_name($id) . " {$text} at line {$line}";
			}
			if (!in_array($id, [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT], true)) {
				$significant[] = $id;
			}
			$line += substr_count($text, "\n");
		}
		return $findings;
	}

	/**
	 * Every name in one source file that reaches the router or the container,
	 * as "{path}:{line}: {name}".
	 *
	 * @return list<string>
	 */
	public static function sourceFindings(string $relativePath, string $source): array {
		$findings = [];
		foreach (token_get_all($source) as $token) {
			if (!is_array($token) || !in_array($token[0], self::NAME_TOKENS, true)) {
				continue;
			}
			$name = $token[1];
			$segments = explode('\\', $name);
			$last = end($segments);
			$normalised = strtolower(ltrim($name, '\\'));
			if (in_array($last, self::BANNED_NAMES, true) || str_starts_with($normalised, self::BANNED_NAMESPACE)) {
				$findings[] = "{$relativePath}:{$token[2]}: {$name}";
			}
		}
		return $findings;
	}

	/** Application::register() against the given registration context. */
	public static function register(IRegistrationContext $context): void {
		self::application()->register($context);
	}

	/** Application::boot() against the given boot context. */
	public static function boot(IBootContext $context): void {
		self::application()->boot($context);
	}

	/**
	 * One recorded call as "name(arg, ...)": strings as they are, class names
	 * without a leading backslash, booleans as true and false, null as null,
	 * arrays as canonical JSON, closures as "closure".
	 *
	 * @param list<mixed> $arguments
	 */
	public static function describeCall(string $method, array $arguments): string {
		$parts = [];
		foreach ($arguments as $argument) {
			$parts[] = match (true) {
				is_string($argument) => ltrim($argument, '\\'),
				is_bool($argument) => $argument ? 'true' : 'false',
				$argument === null => 'null',
				is_int($argument), is_float($argument) => (string)$argument,
				is_array($argument) => self::canonicalJson($argument),
				$argument instanceof \Closure => 'closure',
				is_object($argument) => get_class($argument),
				default => get_debug_type($argument),
			};
		}
		return $method . '(' . implode(', ', $parts) . ')';
	}

	/**
	 * Recorded calls against the allowlist as multisets: "unlisted
	 * registration ..." for a call more, "missing registration ..." for a call
	 * less, sorted.
	 *
	 * @param list<string> $actual
	 * @param list<string> $allowed
	 * @return list<string>
	 */
	public static function compareRegistrations(array $actual, array $allowed): array {
		$counts = [];
		foreach ($actual as $call) {
			$counts[$call] = ($counts[$call] ?? 0) + 1;
		}
		foreach ($allowed as $call) {
			$counts[$call] = ($counts[$call] ?? 0) - 1;
		}
		$findings = [];
		foreach ($counts as $call => $count) {
			for ($i = 0; $i < $count; $i++) {
				$findings[] = "unlisted registration {$call}";
			}
			for ($i = 0; $i < -$count; $i++) {
				$findings[] = "missing registration {$call}";
			}
		}
		sort($findings, SORT_STRING);
		return $findings;
	}

	/**
	 * The "registrations" list of tests/app-surface.json; the top level
	 * "_comment" is documentation and ignored.
	 *
	 * @return list<string>
	 */
	public static function loadRegistrations(string $path): array {
		$raw = file_get_contents($path);
		if ($raw === false) {
			throw new \RuntimeException("{$path} is not readable");
		}
		$data = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
		if (!is_array($data) || !isset($data['registrations']) || !is_array($data['registrations'])
			|| !array_is_list($data['registrations']) || $data['registrations'] === []) {
			throw new \RuntimeException("{$path} has no registrations list");
		}
		$registrations = [];
		foreach ($data['registrations'] as $entry) {
			if (!is_string($entry)) {
				throw new \RuntimeException("{$path} has a registration that is not a string");
			}
			$registrations[] = $entry;
		}
		return $registrations;
	}

	private static function application(): Application {
		return (new \ReflectionClass(Application::class))->newInstanceWithoutConstructor();
	}

	/** @param array<mixed> $value */
	private static function canonicalJson(array $value): string {
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
