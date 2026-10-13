<?php

declare(strict_types=1);

/**
 * A driver that runs one ExclusionService source file outside Nextcloud.
 *
 * Written for plan 33-02 and meant to be used again unchanged (plan 33-11 uses
 * it as the oracle and the stopwatch of the audit). It loads the class from the
 * source file named on the command line, so the same driver builds the service
 * of v1.4.2 out of backend/tests/fixtures/exclusion_v1_4_2/ and the service of
 * today out of php/lib/Service/, one per process, because both declare the same
 * class name.
 *
 * Call, from the root of the repository:
 *
 *   MSYS_NO_PATHCONV=1 docker run --rm -i -v "$PWD":/app -w /app php:8.3-cli \
 *     php backend/tests/drivers/exclusion_driver.php <source> <mode> < input.json
 *
 * Input on stdin, one JSON object:
 *
 *   {"config": {"exclusions": [...], "exclusion_patterns": [...]},
 *    "paths": ["Archiv/x.pdf", ...],                       (mode answers)
 *    "groups": {"1000": ["...", ...], ...}, "repeat": 50}  (mode timing)
 *
 * The keys of "config" are app config keys of the app; a key that is absent
 * answers with the default the service asks for, which is how a fresh instance
 * and an instance of 1.4.2 without the pattern key look.
 *
 * Modes, output on stdout, one JSON object:
 *
 *   answers  {"prefixes": [...], "patterns": [...] or null when the source has
 *            no patterns(), "isExcluded": [bool per path, in input order],
 *            "log": [{"level", "message", "context"}, ...], "jobs": int}
 *   timing   {"groups": {"<name>": {"median_ms": float, "max_ms": float,
 *            "calls": int}}}; every path of a group is asked "repeat" times
 *            with hrtime(true) around each single isExcluded() call, after one
 *            warm up call, so the request caches of the service are filled and
 *            the figure is the comparison and not the read of the list.
 *
 * Stubs, each declared only when the name does not exist yet, so the driver
 * also runs where a real autoloader is present:
 *
 *   OCP\IAppConfig                     interface: getValueArray, setValueArray
 *   OCP\BackgroundJob\IJobList          interface: add, remove, has
 *   Psr\Log\LoggerInterface             interface: the eight levels and log
 *   OCA\Findling\AppInfo\Application    class: APP_ID = 'findling'
 *   OCA\Findling\Service\SettingsService class: KEY_EXCLUSIONS and
 *                                       KEY_EXCLUSION_PATTERNS, the values of
 *                                       php/lib/Service/SettingsService.php
 *   OCA\Findling\Service\StorageService class without constructor; every
 *                                       method throws, because prefixes(),
 *                                       patterns() and isExcluded() need none
 *                                       of them and an unexpected call has to
 *                                       show up instead of answering quietly
 *
 * The other use targets of the source file (BackgroundJobs\SubtreeExpandJob,
 * Db\QueueMapper) are not declared: a use statement loads nothing, and only
 * scheduleCleanup() would touch them, which this driver never calls.
 *
 * The constructor is read by reflection and every parameter gets the double of
 * its type name; a type this driver does not know ends the run with exit code
 * 3 rather than a guess.
 */

namespace OCP {
	if (!interface_exists(IAppConfig::class)) {
		interface IAppConfig {
			/** @return array<array-key, mixed> */
			public function getValueArray(string $app, string $key, array $default = [], bool $lazy = false): array;

			public function setValueArray(string $app, string $key, array $value, bool $lazy = false, bool $sensitive = false): bool;
		}
	}
}

namespace OCP\BackgroundJob {
	if (!interface_exists(IJobList::class)) {
		interface IJobList {
			public function add($job, mixed $argument = null, ?int $firstCheck = null): void;

			public function remove($job, mixed $argument = null): void;

			public function has($job, mixed $argument): bool;
		}
	}
}

namespace Psr\Log {
	if (!interface_exists(LoggerInterface::class)) {
		interface LoggerInterface {
			public function emergency(string|\Stringable $message, array $context = []): void;

			public function alert(string|\Stringable $message, array $context = []): void;

			public function critical(string|\Stringable $message, array $context = []): void;

			public function error(string|\Stringable $message, array $context = []): void;

			public function warning(string|\Stringable $message, array $context = []): void;

			public function notice(string|\Stringable $message, array $context = []): void;

			public function info(string|\Stringable $message, array $context = []): void;

			public function debug(string|\Stringable $message, array $context = []): void;

			public function log($level, string|\Stringable $message, array $context = []): void;
		}
	}
}

namespace OCA\Findling\AppInfo {
	if (!class_exists(Application::class)) {
		class Application {
			public const APP_ID = 'findling';
		}
	}
}

namespace OCA\Findling\Service {
	if (!class_exists(SettingsService::class)) {
		class SettingsService {
			public const KEY_EXCLUSIONS = 'exclusions';
			public const KEY_EXCLUSION_PATTERNS = 'exclusion_patterns';
		}
	}

	if (!class_exists(StorageService::class)) {
		class StorageService {
			public function __call(string $name, array $arguments): never {
				throw new \LogicException('StorageService::' . $name . ' is not expected in this driver');
			}

			public function getMounts(): never {
				throw new \LogicException('StorageService::getMounts is not expected in this driver');
			}

			public function mountRootPath(int $storageId, int $rootId): never {
				throw new \LogicException('StorageService::mountRootPath is not expected in this driver');
			}

			public function folderIdAtPath(int $storageId, string $path): never {
				throw new \LogicException('StorageService::folderIdAtPath is not expected in this driver');
			}

			public function getFilesInMount(int $storageId, int $ancestorId, int $after, int $limit): never {
				throw new \LogicException('StorageService::getFilesInMount is not expected in this driver');
			}
		}
	}
}

namespace FindlingDriver {
	use OCA\Findling\Service\StorageService;
	use OCP\BackgroundJob\IJobList;
	use OCP\IAppConfig;
	use Psr\Log\LoggerInterface;

	/** The app config, answered out of the "config" object of the input. */
	final class Config implements IAppConfig {
		/** @param array<string, mixed> $values */
		public function __construct(private array $values) {
		}

		public function getValueArray(string $app, string $key, array $default = [], bool $lazy = false): array {
			$value = $this->values[$key] ?? null;

			return is_array($value) ? $value : $default;
		}

		public function setValueArray(string $app, string $key, array $value, bool $lazy = false, bool $sensitive = false): bool {
			$this->values[$key] = $value;

			return true;
		}
	}

	/** A job list that plans nothing and counts what it was asked to plan. */
	final class Jobs implements IJobList {
		public int $calls = 0;

		public function add($job, mixed $argument = null, ?int $firstCheck = null): void {
			$this->calls++;
		}

		public function remove($job, mixed $argument = null): void {
			$this->calls++;
		}

		public function has($job, mixed $argument): bool {
			$this->calls++;

			return false;
		}
	}

	/** A logger that writes nothing anywhere and keeps every line it got. */
	final class Log implements LoggerInterface {
		/** @var list<array{level: string, message: string, context: array<array-key, mixed>}> */
		public array $lines = [];

		public function emergency(string|\Stringable $message, array $context = []): void {
			$this->log('emergency', $message, $context);
		}

		public function alert(string|\Stringable $message, array $context = []): void {
			$this->log('alert', $message, $context);
		}

		public function critical(string|\Stringable $message, array $context = []): void {
			$this->log('critical', $message, $context);
		}

		public function error(string|\Stringable $message, array $context = []): void {
			$this->log('error', $message, $context);
		}

		public function warning(string|\Stringable $message, array $context = []): void {
			$this->log('warning', $message, $context);
		}

		public function notice(string|\Stringable $message, array $context = []): void {
			$this->log('notice', $message, $context);
		}

		public function info(string|\Stringable $message, array $context = []): void {
			$this->log('info', $message, $context);
		}

		public function debug(string|\Stringable $message, array $context = []): void {
			$this->log('debug', $message, $context);
		}

		public function log($level, string|\Stringable $message, array $context = []): void {
			$this->lines[] = ['level' => (string)$level, 'message' => (string)$message, 'context' => $context];
		}
	}

	function fail(string $message, int $code): never {
		fwrite(STDERR, $message . "\n");
		exit($code);
	}

	/**
	 * The service out of one source file, with one double per constructor
	 * parameter chosen by the name of its type.
	 *
	 * @param array<string, object> $doubles
	 */
	function build(string $source, array $doubles): object {
		if (!is_file($source)) {
			fail('no such source: ' . $source, 2);
		}
		require $source;

		$class = new \ReflectionClass('OCA\\Findling\\Service\\ExclusionService');
		$constructor = $class->getConstructor();
		$arguments = [];
		foreach ($constructor?->getParameters() ?? [] as $parameter) {
			$type = $parameter->getType();
			$name = $type instanceof \ReflectionNamedType ? $type->getName() : '';
			if (!isset($doubles[$name])) {
				fail('no double for constructor parameter of type ' . ($name === '' ? '(none)' : $name), 3);
			}
			$arguments[] = $doubles[$name];
		}

		return $class->newInstanceArgs($arguments);
	}

	/** The median of a non empty list of numbers. */
	function median(array $values): float {
		sort($values);
		$count = count($values);
		$middle = intdiv($count, 2);

		return $count % 2 === 1 ? (float)$values[$middle] : ($values[$middle - 1] + $values[$middle]) / 2.0;
	}

	$source = $argv[1] ?? '';
	$mode = $argv[2] ?? '';
	if (!in_array($mode, ['answers', 'timing'], true)) {
		fail('usage: exclusion_driver.php <source> answers|timing < input.json', 2);
	}

	$input = json_decode((string)stream_get_contents(STDIN), true, 512, JSON_THROW_ON_ERROR);
	if (!is_array($input)) {
		fail('the input is not a JSON object', 2);
	}
	$config = is_array($input['config'] ?? null) ? $input['config'] : [];

	$log = new Log();
	$jobs = new Jobs();
	$service = build($source, [
		IAppConfig::class => new Config($config),
		StorageService::class => (new \ReflectionClass(StorageService::class))->newInstanceWithoutConstructor(),
		IJobList::class => $jobs,
		LoggerInterface::class => $log,
	]);

	if ($mode === 'answers') {
		$paths = is_array($input['paths'] ?? null) ? $input['paths'] : [];
		$answers = [];
		foreach ($paths as $path) {
			$answers[] = $service->isExcluded((string)$path);
		}

		$out = [
			'prefixes' => $service->prefixes(),
			'patterns' => method_exists($service, 'patterns') ? $service->patterns() : null,
			'isExcluded' => $answers,
			'log' => $log->lines,
			'jobs' => $jobs->calls,
		];
	} else {
		$groups = is_array($input['groups'] ?? null) ? $input['groups'] : [];
		$repeat = max(1, (int)($input['repeat'] ?? 50));

		// One call before the clock runs: it fills the request caches of the
		// lists, which a real request pays once and not per file.
		$service->isExcluded('warm/up');

		$result = [];
		foreach ($groups as $name => $paths) {
			$times = [];
			foreach ((array)$paths as $path) {
				$path = (string)$path;
				for ($round = 0; $round < $repeat; $round++) {
					$started = hrtime(true);
					$service->isExcluded($path);
					$times[] = hrtime(true) - $started;
				}
			}
			if ($times === []) {
				continue;
			}
			$result[(string)$name] = [
				'median_ms' => median($times) / 1e6,
				'max_ms' => max($times) / 1e6,
				'calls' => count($times),
			];
		}

		$out = ['groups' => $result];
	}

	echo json_encode($out, JSON_THROW_ON_ERROR), "\n";
}
