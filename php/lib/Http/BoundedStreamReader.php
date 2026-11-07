<?php

declare(strict_types=1);

namespace OCA\Findling\Http;

/**
 * Reads a file stream for the content gateway with deadlines instead of a
 * blocking copy (plan 43-17, D-43-16).
 *
 * The hang this class exists for: in the wrapped mode of icewind/smb,
 * Wrapped/Share::read sends "get" and "exit" to a smbclient process and hands
 * out its file descriptor 5 as the stream. When the open fails on the server
 * (a DENY ACE, a sharing violation, a storage that went offline, a file deleted
 * between the stat and the get), smbclient prints its error and waits for the
 * next line on stdin, and a blocking read of descriptor 5 waits for smbclient.
 * Neither side ever moves, and the PHP worker serving the gateway stays
 * occupied for good (run 42404849768).
 *
 * The way out is the read callback that Wrapped/Share::read hangs on the
 * stream: after every read, empty or not, it writes one line to the stdin of
 * smbclient (RawConnection::write, a blocking fwrite plus fflush). A read that
 * does not block therefore nudges smbclient on every turn, smbclient reads the
 * buffered "exit", ends, and the stream reports its end (research section
 * 1.5). So the reader switches the stream to non blocking, but only when the
 * caller asks for it: whether that is safe is a property of the storage and
 * not of the stream layer this class sees. The View puts a CallbackWrapper
 * around nearly every stream (View.php:1264-1275), and stream_set_blocking
 * travels through every icewind wrapper down to the source, through the
 * stream of server side encryption as well, whose stream_read_block would then
 * hand half a cipher block to the decryption at the first empty read. The
 * gateway asks the storage and passes the answer in.
 *
 * The same nudge is the reason for the cap on reads. smbclient does not read
 * stdin while a get runs, and a pipe holds 65536 bytes, so every read writes
 * one more byte into a pipe nobody empties. Once it is full, the fwrite of the
 * read callback blocks and the hang is back, one level lower. MAX_READS keeps
 * the number of reads of one answer, data and empty reads together, below the
 * size of that pipe. The pauses between empty reads keep a slow line far away
 * from the cap: 50 MiB (the default size limit of the container) are 6400
 * reads of 8 KiB with data. On a line of a little over 100 KB/s that delivers
 * 64 KiB pieces 0.6 s apart, the pause after data grows 20, 40, 80, 160, 200 ms
 * and the next piece is there after five or six empty reads, about 11000 reads
 * in all, far under 60000. The cap is a limit on size as well: 60000 reads of
 * at most 8 KiB are about 469 MiB, and a larger file read this way ends short.
 * It only applies when the reader really reads non blocking; a blocking read
 * nudges nothing that could fill up, and the native mode of icewind/smb has no
 * pipe at all (NativeStream refuses the switch, so it stays blocking).
 *
 * Both deadlines lie under the 90 seconds the backend waits for an answer, so
 * the container always hears from the gateway before it gives up on its own.
 *
 * The clock, the pause and the check for a client that went away are closures
 * with defaults, so the tests can run thirty second deadlines on a fake clock.
 */
final class BoundedStreamReader {
	public const FIRST_BYTE_SECONDS = 30.0;
	public const IDLE_SECONDS = 30.0;

	public const PAUSE_MIN_MICROSECONDS = 1000;
	public const PAUSE_FIRST_BYTE_MAX_MICROSECONDS = 20000;
	public const PAUSE_AFTER_DATA_MIN_MICROSECONDS = 20000;
	public const PAUSE_AFTER_DATA_MAX_MICROSECONDS = 200000;

	public const BLOCK_BYTES = 8192;
	public const MAX_READS = 60000;

	/** The first block arrived, it is in head. */
	public const OUTCOME_DATA = 'data';
	/** The stream ended without a single byte. */
	public const OUTCOME_EMPTY = 'empty';
	/** Nothing arrived within FIRST_BYTE_SECONDS. */
	public const OUTCOME_TIMEOUT = 'timeout';
	/** A read failed before any data. */
	public const OUTCOME_ERROR = 'error';

	/** The stream ended at or after the expected size. */
	public const END_COMPLETE = 'complete';
	/** No data for IDLE_SECONDS, or the cap on reads was reached. */
	public const END_STALLED = 'stalled';
	/** The stream ended before the expected size, or a read failed. */
	public const END_SHORT = 'short';
	/** The client went away; the rest is not read. */
	public const END_ABORTED = 'aborted';

	private \Closure $now;
	private \Closure $pause;
	private \Closure $aborted;

	public function __construct(
		?\Closure $now = null,
		?\Closure $pause = null,
		?\Closure $aborted = null,
		private float $firstByteSeconds = self::FIRST_BYTE_SECONDS,
		private float $idleSeconds = self::IDLE_SECONDS,
	) {
		$this->now = $now ?? static fn (): float => microtime(true);
		$this->pause = $pause ?? static function (int $microseconds): void {
			usleep($microseconds);
		};
		$this->aborted = $aborted ?? static fn (): bool => connection_aborted() === 1;
	}

	/**
	 * Reads up to the first block, before the answer is decided.
	 *
	 * Nothing has been sent at this point, so whatever comes out here can still
	 * become a 422. nonBlocking in the result says whether the switch really
	 * happened; pump() needs it for the cap.
	 *
	 * @param resource $stream
	 * @return array{outcome: string, head: string, reads: int, nonBlocking: bool}
	 */
	public function prime($stream, bool $nonBlocking): array {
		// false means the stream refused (NativeStream does); it is then read
		// blocking, which is what it was before this class.
		$switched = $nonBlocking && stream_set_blocking($stream, false);

		$reads = 0;
		$pause = self::PAUSE_MIN_MICROSECONDS;
		$started = ($this->now)();
		while (true) {
			if ($switched && $reads >= self::MAX_READS) {
				return ['outcome' => self::OUTCOME_TIMEOUT, 'head' => '', 'reads' => $reads, 'nonBlocking' => $switched];
			}
			$block = fread($stream, self::BLOCK_BYTES);
			$reads++;
			if ($block === false) {
				return ['outcome' => self::OUTCOME_ERROR, 'head' => '', 'reads' => $reads, 'nonBlocking' => $switched];
			}
			if ($block !== '') {
				return ['outcome' => self::OUTCOME_DATA, 'head' => $block, 'reads' => $reads, 'nonBlocking' => $switched];
			}
			if (feof($stream)) {
				return ['outcome' => self::OUTCOME_EMPTY, 'head' => '', 'reads' => $reads, 'nonBlocking' => $switched];
			}
			if (($this->now)() - $started >= $this->firstByteSeconds) {
				return ['outcome' => self::OUTCOME_TIMEOUT, 'head' => '', 'reads' => $reads, 'nonBlocking' => $switched];
			}
			($this->pause)($pause);
			$pause = min($pause * 2, self::PAUSE_FIRST_BYTE_MAX_MICROSECONDS);
		}
	}

	/**
	 * Writes the head and the rest of the stream, after the headers.
	 *
	 * An answer that is already under way cannot change its status any more,
	 * so every way this ends early ends the body short. The container sees a
	 * body shorter than the size it expects, a ShortRead about this one file,
	 * and not a dropped connection, which it would judge an outage of the
	 * gateway. The stream is closed on every way out.
	 *
	 * @param resource $stream
	 * @param \Closure(string): void $write
	 * @param bool $capReads whether the cap on reads applies, from the
	 *                       nonBlocking field of prime()
	 */
	public function pump($stream, string $head, int $size, int $readsSoFar, \Closure $write, bool $capReads = true): string {
		try {
			$written = 0;
			if ($head !== '') {
				$write($head);
				$written += strlen($head);
				if (($this->aborted)()) {
					return self::END_ABORTED;
				}
			}

			$reads = $readsSoFar;
			$pause = self::PAUSE_AFTER_DATA_MIN_MICROSECONDS;
			$lastData = ($this->now)();
			while (true) {
				if ($capReads && $reads >= self::MAX_READS) {
					return self::END_STALLED;
				}
				$block = fread($stream, self::BLOCK_BYTES);
				$reads++;
				if ($block === false) {
					return self::END_SHORT;
				}
				if ($block !== '') {
					$write($block);
					$written += strlen($block);
					if (($this->aborted)()) {
						return self::END_ABORTED;
					}
					$pause = self::PAUSE_AFTER_DATA_MIN_MICROSECONDS;
					$lastData = ($this->now)();
					continue;
				}
				if (feof($stream)) {
					return ($size === 0 || $written >= $size) ? self::END_COMPLETE : self::END_SHORT;
				}
				if (($this->now)() - $lastData >= $this->idleSeconds) {
					return self::END_STALLED;
				}
				($this->pause)($pause);
				$pause = min($pause * 2, self::PAUSE_AFTER_DATA_MAX_MICROSECONDS);
			}
		} finally {
			if (is_resource($stream)) {
				fclose($stream);
			}
		}
	}
}
