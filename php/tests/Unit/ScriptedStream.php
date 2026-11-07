<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

/**
 * A stream that answers every read from a script, for BoundedStreamReaderTest.
 *
 * The source end of the chains under test. In production that end is the
 * stdout pipe of smbclient (wrapped mode) or a libsmbclient handle (native
 * mode), and what matters about either is not the bytes but the shape of the
 * reads: data, an empty read that is not the end, the end, or a failed read.
 * A script spells that shape out step by step, so a test can stage exactly the
 * sequence a stuck smbclient or a slow line produces.
 *
 * A script is either a list of steps, consumed one per read, or a closure that
 * is asked for the next step on every read (used where the answer depends on
 * a fake clock). A step is a non empty string of bytes or one of the markers
 * below; a list that runs out reads as the end. Bytes longer than the read
 * asked for are handed out over several reads, as a pipe would.
 *
 * It counts its reads and the attempts to switch its blocking mode, which is
 * how a test sees whether stream_set_blocking travelled through the wrappers
 * above it. In native mode it refuses that switch the way NativeStream of
 * icewind/smb does (stream_set_option answers false).
 *
 * The wrapper is registered in setUp and unregistered in tearDown of the test.
 */
final class ScriptedStream {
	public const PROTOCOL = 'findling-scripted';

	/** An empty read that is not the end of the stream. */
	public const EMPTY = "\0scripted-empty";

	/** The end of the stream: an empty read with feof() true. */
	public const EOF = "\0scripted-eof";

	/** A failed read: fread() answers false. */
	public const ERROR = "\0scripted-error";

	/** @var array<string, array{script: list<string>|\Closure, native: bool}> */
	private static array $scripts = [];

	/** @var array<string, array{reads: int, blocking: int, closed: bool}> */
	private static array $stats = [];

	/** @var resource|null */
	public $context;

	private string $id = '';
	private int $position = 0;
	private string $pending = '';
	private bool $eof = false;

	public static function register(): void {
		if (!in_array(self::PROTOCOL, stream_get_wrappers(), true)) {
			stream_wrapper_register(self::PROTOCOL, self::class);
		}
	}

	public static function unregister(): void {
		if (in_array(self::PROTOCOL, stream_get_wrappers(), true)) {
			stream_wrapper_unregister(self::PROTOCOL);
		}
		self::$scripts = [];
		self::$stats = [];
	}

	/**
	 * @param list<string>|\Closure(int): string $script
	 * @return resource
	 */
	public static function open(string $id, array|\Closure $script, bool $native = false) {
		self::$scripts[$id] = ['script' => $script, 'native' => $native];
		self::$stats[$id] = ['reads' => 0, 'blocking' => 0, 'closed' => false];
		$stream = fopen(self::PROTOCOL . '://' . $id, 'r');
		if (!is_resource($stream)) {
			throw new \RuntimeException('the scripted stream did not open');
		}

		return $stream;
	}

	public static function reads(string $id): int {
		return self::$stats[$id]['reads'];
	}

	public static function blockingCalls(string $id): int {
		return self::$stats[$id]['blocking'];
	}

	public static function closed(string $id): bool {
		return self::$stats[$id]['closed'];
	}

	public function stream_open(string $path, string $mode, int $options, ?string &$openedPath): bool {
		$this->id = substr($path, strlen(self::PROTOCOL . '://'));

		return isset(self::$scripts[$this->id]);
	}

	public function stream_read(int $count): string|false {
		self::$stats[$this->id]['reads']++;

		if ($this->pending !== '') {
			return $this->handOut($count);
		}

		$script = self::$scripts[$this->id]['script'];
		if ($script instanceof \Closure) {
			$step = $script($count);
		} else {
			$step = $script[$this->position] ?? self::EOF;
			$this->position++;
		}

		if ($step === self::EOF) {
			$this->eof = true;

			return '';
		}
		if ($step === self::EMPTY) {
			return '';
		}
		if ($step === self::ERROR) {
			return false;
		}

		$this->pending = $step;

		return $this->handOut($count);
	}

	private function handOut(int $count): string {
		$chunk = substr($this->pending, 0, $count);
		$this->pending = substr($this->pending, strlen($chunk));

		return $chunk;
	}

	public function stream_eof(): bool {
		return $this->eof && $this->pending === '';
	}

	public function stream_set_option(int $option, mixed $arg1, mixed $arg2): bool {
		if ($option === STREAM_OPTION_BLOCKING) {
			self::$stats[$this->id]['blocking']++;

			return !self::$scripts[$this->id]['native'];
		}

		return false;
	}

	/**
	 * @return array<int|string, int>
	 */
	public function stream_stat(): array {
		return [];
	}

	public function stream_close(): void {
		self::$stats[$this->id]['closed'] = true;
	}
}
