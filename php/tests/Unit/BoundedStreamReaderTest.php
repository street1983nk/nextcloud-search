<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use Icewind\Streams\CallbackWrapper;
use OCA\Findling\Http\BoundedStreamReader;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The read with a deadline of the content gateway (plan 43-17, D-43-16).
 *
 * The hang it removes: in the wrapped mode of icewind/smb a file whose open
 * fails on the server (a DENY ACE, a sharing violation, a file deleted between
 * the stat and the get) leaves smbclient waiting for a line on stdin that
 * nobody writes, and the blocking read of the gateway waits for smbclient. A
 * PHP worker stays occupied for good (run 42404849768).
 *
 * The cases build the chains the gateway really meets instead of a single fake:
 * the CallbackWrapper the View puts around every stream when locking is on, the
 * CallbackWrapper of Wrapped/Share::read whose read callback nudges smbclient,
 * and a stand in for the encryption stream that collects blocks. The clock and
 * the pause are closures over one float, so the eighty second deadlines run in
 * microseconds of real time. One case at the end uses a real pipe and a real
 * process, because the nudge is a claim about pipes and processes and nothing
 * else proves it.
 */
#[CoversClass(BoundedStreamReader::class)]
final class BoundedStreamReaderTest extends TestCase {
	private float $clock = 0.0;

	/** @var list<int> */
	private array $pauses = [];

	protected function setUp(): void {
		parent::setUp();
		ScriptedStream::register();
		$this->clock = 0.0;
		$this->pauses = [];
	}

	protected function tearDown(): void {
		ScriptedStream::unregister();
		parent::tearDown();
	}

	/**
	 * A reader on the fake clock. The pause records its argument and moves the
	 * clock by it, which is all a sleep does as far as the reader can tell.
	 */
	private function reader(
		?\Closure $aborted = null,
		float $firstByteSeconds = BoundedStreamReader::FIRST_BYTE_SECONDS,
		float $idleSeconds = BoundedStreamReader::IDLE_SECONDS,
	): BoundedStreamReader {
		return new BoundedStreamReader(
			fn (): float => $this->clock,
			function (int $microseconds): void {
				$this->pauses[] = $microseconds;
				$this->clock += $microseconds / 1_000_000;
			},
			$aborted ?? static fn (): bool => false,
			$firstByteSeconds,
			$idleSeconds,
		);
	}

	/**
	 * The View layer: a CallbackWrapper with only a close callback, exactly the
	 * shape of View::basicOperation (View.php:1264-1275).
	 *
	 * @param resource $inner
	 * @return resource
	 */
	private static function viewLayer($inner) {
		$stream = CallbackWrapper::wrap($inner, null, null, static function (): void {
		});
		self::assertIsResource($stream);

		return $stream;
	}

	/**
	 * The wrapped SMB layer: a CallbackWrapper whose read callback runs after
	 * every read, empty or not (Wrapped/Share::read).
	 *
	 * @param resource $inner
	 * @return resource
	 */
	private static function smbLayer($inner, \Closure $nudge) {
		$stream = CallbackWrapper::wrap($inner, $nudge);
		self::assertIsResource($stream);

		return $stream;
	}

	public function testWithoutTheSwitchTheReaderNeverTouchesBlockingAndDeliversEverything(): void {
		// N1: the chain of an encrypted storage, View outside, the block
		// collecting stream in the middle. Empty reads between the data are what
		// a remote source produces, and the reader copes with them in both modes.
		$source = ScriptedStream::open('enc', ['abc', ScriptedStream::EMPTY, 'def', ScriptedStream::EMPTY, ScriptedStream::EMPTY, 'ghi', ScriptedStream::EOF]);
		$stream = self::viewLayer(BlockCollectingStream::wrap($source));
		$reader = $this->reader();

		$primed = $reader->prime($stream, false);
		self::assertSame(BoundedStreamReader::OUTCOME_DATA, $primed['outcome']);

		$out = '';
		$end = $reader->pump($stream, $primed['head'], 9, $primed['reads'], function (string $block) use (&$out): void {
			$out .= $block;
		});

		self::assertSame(BoundedStreamReader::END_COMPLETE, $end);
		self::assertSame('abcdefghi', $out);
		self::assertSame(0, ScriptedStream::blockingCalls('enc'), 'the reader switched blocking off on a storage it was told to read blocking');
		self::assertTrue(ScriptedStream::closed('enc'));
	}

	public function testWithTheSwitchBlockingTravelsThroughEveryLayerToTheSource(): void {
		// The counter half of N1 and the reason the storage decides: the switch
		// on the outermost View layer arrives at the source below the block
		// collecting stream. Under encryption that would make stream_read_block
		// stop at the first empty read with a part of a cipher block (B1).
		$source = ScriptedStream::open('enc', ['abc', ScriptedStream::EMPTY, 'def', ScriptedStream::EOF]);
		$stream = self::viewLayer(BlockCollectingStream::wrap($source));

		$primed = $this->reader()->prime($stream, true);

		self::assertSame(1, ScriptedStream::blockingCalls('enc'));
		self::assertSame(BoundedStreamReader::OUTCOME_DATA, $primed['outcome']);
		self::assertSame('abc', $primed['head'], 'the block was cut at the empty read, the shape that breaks decryption');
		fclose($stream);
	}

	public function testThroughTheViewAndTheSmbLayerDataAfterThreeEmptyReadsArrivesWhole(): void {
		$nudges = 0;
		$source = ScriptedStream::open('smb', [ScriptedStream::EMPTY, ScriptedStream::EMPTY, ScriptedStream::EMPTY, 'hello', ScriptedStream::EOF]);
		$stream = self::viewLayer(self::smbLayer($source, static function () use (&$nudges): void {
			$nudges++;
		}));
		$reader = $this->reader();

		$primed = $reader->prime($stream, true);
		self::assertSame(BoundedStreamReader::OUTCOME_DATA, $primed['outcome']);
		self::assertSame('hello', $primed['head']);
		self::assertSame(1, ScriptedStream::blockingCalls('smb'));

		$out = '';
		$end = $reader->pump($stream, $primed['head'], 5, $primed['reads'], function (string $block) use (&$out): void {
			$out .= $block;
		});

		self::assertSame(BoundedStreamReader::END_COMPLETE, $end);
		self::assertSame('hello', $out);
		self::assertTrue(ScriptedStream::closed('smb'));
		// Every read nudges, the empty ones included: that is what makes a
		// waiting smbclient read its buffered exit.
		self::assertSame(ScriptedStream::reads('smb'), $nudges);
		self::assertGreaterThanOrEqual(5, $nudges);
	}

	public function testAStreamThatNeverDeliversTimesOutAtTheFirstByteDeadline(): void {
		$stream = ScriptedStream::open('stuck', static fn (): string => ScriptedStream::EMPTY);
		$started = hrtime(true);

		$primed = $this->reader()->prime($stream, true);

		self::assertSame(BoundedStreamReader::OUTCOME_TIMEOUT, $primed['outcome']);
		self::assertSame('', $primed['head']);
		self::assertGreaterThanOrEqual(BoundedStreamReader::FIRST_BYTE_SECONDS, $this->clock);
		self::assertLessThan(BoundedStreamReader::FIRST_BYTE_SECONDS + 0.021, $this->clock);
		self::assertSame(BoundedStreamReader::PAUSE_MIN_MICROSECONDS, $this->pauses[0]);
		self::assertSame(BoundedStreamReader::PAUSE_FIRST_BYTE_MAX_MICROSECONDS, max($this->pauses));
		self::assertGreaterThanOrEqual(BoundedStreamReader::PAUSE_MIN_MICROSECONDS, min($this->pauses));
		self::assertSame(ScriptedStream::reads('stuck'), $primed['reads']);
		self::assertLessThan(1.0, (hrtime(true) - $started) / 1e9, 'the fake clock is not in charge');
		fclose($stream);
	}

	public function testAnEmptyReadThenTheEndOfANonEmptyFileIsEmpty(): void {
		$stream = ScriptedStream::open('denied', [ScriptedStream::EMPTY, ScriptedStream::EOF]);

		$primed = $this->reader()->prime($stream, true);

		self::assertSame(BoundedStreamReader::OUTCOME_EMPTY, $primed['outcome']);
		self::assertSame('', $primed['head']);
		self::assertSame(2, $primed['reads']);
		fclose($stream);
	}

	public function testAnEmptyFileIsEmptyAndPumpsCompleteWithoutWaiting(): void {
		$stream = ScriptedStream::open('zero', [ScriptedStream::EOF]);
		$reader = $this->reader();

		$primed = $reader->prime($stream, true);
		self::assertSame(BoundedStreamReader::OUTCOME_EMPTY, $primed['outcome']);

		$writes = 0;
		$end = $reader->pump($stream, $primed['head'], 0, $primed['reads'], static function () use (&$writes): void {
			$writes++;
		});

		self::assertSame(BoundedStreamReader::END_COMPLETE, $end);
		self::assertSame(0, $writes);
		self::assertSame([], $this->pauses);
		self::assertTrue(ScriptedStream::closed('zero'));
	}

	public function testAFailedReadBeforeTheFirstDataIsAnError(): void {
		$stream = ScriptedStream::open('broken', [ScriptedStream::EMPTY, ScriptedStream::ERROR]);

		$primed = $this->reader()->prime($stream, true);

		self::assertSame(BoundedStreamReader::OUTCOME_ERROR, $primed['outcome']);
		fclose($stream);
	}

	public function testAFailedReadAfterDataEndsTheAnswerShort(): void {
		$stream = ScriptedStream::open('broken', ['abc', ScriptedStream::ERROR]);
		$reader = $this->reader();

		$primed = $reader->prime($stream, true);
		$out = '';
		$end = $reader->pump($stream, $primed['head'], 100, $primed['reads'], function (string $block) use (&$out): void {
			$out .= $block;
		});

		self::assertSame(BoundedStreamReader::END_SHORT, $end);
		self::assertSame('abc', $out);
		self::assertTrue(ScriptedStream::closed('broken'));
	}

	public function testDataThenTheEndBeforeTheSizeIsShort(): void {
		$stream = ScriptedStream::open('shrunk', ['abc', ScriptedStream::EOF]);
		$reader = $this->reader();

		$primed = $reader->prime($stream, true);
		$end = $reader->pump($stream, $primed['head'], 10, $primed['reads'], static function (): void {
		});

		self::assertSame(BoundedStreamReader::END_SHORT, $end);
		self::assertTrue(ScriptedStream::closed('shrunk'));
	}

	public function testAStreamThatStopsAfterDataStallsAtTheIdleDeadlineWithGrowingPauses(): void {
		$calls = 0;
		$stream = ScriptedStream::open('stall', static function () use (&$calls): string {
			return $calls++ === 0 ? 'abc' : ScriptedStream::EMPTY;
		});
		$reader = $this->reader();

		$primed = $reader->prime($stream, true);
		self::assertSame(BoundedStreamReader::OUTCOME_DATA, $primed['outcome']);
		self::assertSame([], $this->pauses);
		$dataAt = $this->clock;

		$end = $reader->pump($stream, $primed['head'], 100, $primed['reads'], static function (): void {
		});

		self::assertSame(BoundedStreamReader::END_STALLED, $end);
		self::assertSame([20000, 40000, 80000, 160000, 200000], array_slice($this->pauses, 0, 5));
		self::assertSame(BoundedStreamReader::PAUSE_AFTER_DATA_MAX_MICROSECONDS, max($this->pauses));
		self::assertGreaterThanOrEqual(BoundedStreamReader::IDLE_SECONDS, $this->clock - $dataAt);
		self::assertLessThan(BoundedStreamReader::IDLE_SECONDS + 0.201, $this->clock - $dataAt);
		self::assertTrue(ScriptedStream::closed('stall'));
	}

	public function testMoreReadsThanTheCapStallBeforeTheCapIsPassed(): void {
		// W1 and W1b: in wrapped mode every read writes one line into the stdin
		// pipe of smbclient, which does not read stdin during a get. A trickle of
		// one byte between empty reads never runs into the idle deadline, so the
		// cap on reads is the only thing that ends it before the pipe is full.
		$calls = 0;
		$stream = ScriptedStream::open('trickle', static function () use (&$calls): string {
			return $calls++ % 2 === 0 ? 'x' : ScriptedStream::EMPTY;
		});
		$reader = $this->reader();

		$primed = $reader->prime($stream, true);
		$end = $reader->pump($stream, $primed['head'], 1_000_000_000, $primed['reads'], static function (): void {
		});

		self::assertSame(BoundedStreamReader::END_STALLED, $end);
		self::assertLessThanOrEqual(BoundedStreamReader::MAX_READS, ScriptedStream::reads('trickle'));
		self::assertGreaterThan(BoundedStreamReader::MAX_READS - 10, ScriptedStream::reads('trickle'));
		self::assertTrue(ScriptedStream::closed('trickle'));
	}

	public function testASlowLineDeliversFiftyMegabytesWellUnderTheCap(): void {
		// 50 MiB in 64 KiB pieces, one piece every 0.6 s, a little over 100 KB/s:
		// the slowest line the default size limit of the container is meant to
		// survive. The source looks at the fake clock to decide what has arrived.
		$piece = 65536;
		$total = 800 * $piece;
		$delivered = 0;
		$stream = ScriptedStream::open('slow', function (int $count) use (&$delivered, $piece, $total): string {
			if ($delivered >= $total) {
				return ScriptedStream::EOF;
			}
			$arrived = min($total, ((int)floor($this->clock / 0.6) + 1) * $piece);
			if ($delivered >= $arrived) {
				return ScriptedStream::EMPTY;
			}
			$length = min($count, $arrived - $delivered);
			$delivered += $length;

			return str_repeat('a', $length);
		});
		$reader = $this->reader();

		$primed = $reader->prime($stream, true);
		$bytes = 0;
		$end = $reader->pump($stream, $primed['head'], $total, $primed['reads'], static function (string $block) use (&$bytes): void {
			$bytes += strlen($block);
		});

		self::assertSame(BoundedStreamReader::END_COMPLETE, $end);
		self::assertSame($total, $bytes);
		self::assertLessThan(BoundedStreamReader::MAX_READS, ScriptedStream::reads('slow'));
		// The arithmetic of the comment in BoundedStreamReader: 6400 reads with
		// data and about six empty ones per piece.
		self::assertLessThan(12_000, ScriptedStream::reads('slow'));
	}

	public function testBothDeadlinesAreEightySecondsUnderTheNinetyOfTheContainer(): void {
		// Fix round 1 of 43-18 (run 42418778026): smbclient hands the data of a
		// get on in blocks of the SMB2 read size, 8 MiB by default, so a slow
		// line shows long silences before the first byte and between blocks.
		// Eighty seconds wait for a whole block and stay under the 90 s read
		// timeout of the container (backend nc/client.py).
		self::assertSame(80.0, BoundedStreamReader::FIRST_BYTE_SECONDS);
		self::assertSame(80.0, BoundedStreamReader::IDLE_SECONDS);
	}

	public function testTheFirstDataAfterSeventyNineSecondsStillArriveWhole(): void {
		$sent = false;
		$stream = ScriptedStream::open('late', function () use (&$sent): string {
			if ($sent) {
				return ScriptedStream::EOF;
			}
			if ($this->clock < 79.0) {
				return ScriptedStream::EMPTY;
			}
			$sent = true;

			return 'late';
		});
		$reader = $this->reader();

		$primed = $reader->prime($stream, true);
		self::assertSame(BoundedStreamReader::OUTCOME_DATA, $primed['outcome']);
		self::assertSame('late', $primed['head']);

		$out = '';
		$end = $reader->pump($stream, $primed['head'], 4, $primed['reads'], function (string $block) use (&$out): void {
			$out .= $block;
		});
		self::assertSame(BoundedStreamReader::END_COMPLETE, $end);
		self::assertSame('late', $out);
		self::assertGreaterThanOrEqual(79.0, $this->clock);
		self::assertTrue(ScriptedStream::closed('late'));
	}

	public function testNoDataForEightyOneSecondsIsATimeout(): void {
		$stream = ScriptedStream::open('silent', function (): string {
			return $this->clock >= 81.0 ? 'too late' : ScriptedStream::EMPTY;
		});

		$primed = $this->reader()->prime($stream, true);

		self::assertSame(BoundedStreamReader::OUTCOME_TIMEOUT, $primed['outcome']);
		self::assertSame('', $primed['head']);
		self::assertGreaterThanOrEqual(80.0, $this->clock);
		self::assertLessThan(81.0, $this->clock);
		fclose($stream);
	}

	public function testAGapOfSeventyNineSecondsBetweenBlocksCompletesAndEightyOneStalls(): void {
		foreach ([[79.0, BoundedStreamReader::END_COMPLETE], [81.0, BoundedStreamReader::END_STALLED]] as [$gap, $expected]) {
			$this->clock = 0.0;
			$this->pauses = [];
			$step = 0;
			$id = 'gap' . (int)$gap;
			$secondAt = null;
			$stream = ScriptedStream::open($id, function () use (&$step, &$secondAt, $gap): string {
				if ($step === 0) {
					$step = 1;
					$secondAt = $this->clock + $gap;

					return 'abcd';
				}
				if ($step === 1) {
					if ($this->clock < $secondAt) {
						return ScriptedStream::EMPTY;
					}
					$step = 2;

					return 'efgh';
				}

				return ScriptedStream::EOF;
			});
			$reader = $this->reader();

			$primed = $reader->prime($stream, true);
			self::assertSame(BoundedStreamReader::OUTCOME_DATA, $primed['outcome']);
			$out = '';
			$end = $reader->pump($stream, $primed['head'], 8, $primed['reads'], function (string $block) use (&$out): void {
				$out .= $block;
			});

			self::assertSame($expected, $end, 'gap of ' . $gap . ' s');
			self::assertSame($expected === BoundedStreamReader::END_COMPLETE ? 'abcdefgh' : 'abcd', $out);
			self::assertTrue(ScriptedStream::closed($id));
		}
	}

	public function testFiftyMegabytesInEightMegabyteBlocksSeventyNineSecondsApartStayUnderTheCap(): void {
		// The shape smbclient produces (source3/libsmb/clireadwrite.c:363-366 of
		// Samba 4.19.5): a whole SMB2 read block of 8 MiB, then a silence until
		// the next one is complete. Block k is there at 79 s * (k + 1), a line
		// of about 106 KB/s. The first wait costs about 4000 empty reads at the
		// 20 ms pause, each later gap about 400 at the 200 ms pause, the data
		// 6400 reads of 8 KiB.
		$block = 8 * 1024 * 1024;
		$total = 50 * 1024 * 1024;
		$delivered = 0;
		$stream = ScriptedStream::open('blocks', function (int $count) use (&$delivered, $block, $total): string {
			if ($delivered >= $total) {
				return ScriptedStream::EOF;
			}
			$arrived = min($total, (int)floor($this->clock / 79.0) * $block);
			if ($delivered >= $arrived) {
				return ScriptedStream::EMPTY;
			}
			$length = min($count, $arrived - $delivered);
			$delivered += $length;

			return str_repeat('a', $length);
		});
		$reader = $this->reader();

		$primed = $reader->prime($stream, true);
		self::assertSame(BoundedStreamReader::OUTCOME_DATA, $primed['outcome']);
		$bytes = 0;
		$end = $reader->pump($stream, $primed['head'], $total, $primed['reads'], static function (string $data) use (&$bytes): void {
			$bytes += strlen($data);
		});

		self::assertSame(BoundedStreamReader::END_COMPLETE, $end);
		self::assertSame($total, $bytes);
		self::assertLessThan(15_000, ScriptedStream::reads('blocks'));
		self::assertLessThan(BoundedStreamReader::MAX_READS, ScriptedStream::reads('blocks'));
	}

	public function testAClientThatWentAwayEndsTheAnswerAfterTheBlockInFlight(): void {
		$writes = 0;
		$stream = ScriptedStream::open('gone', ['abc', 'def', 'ghi', ScriptedStream::EOF]);
		$reader = $this->reader(static function () use (&$writes): bool {
			return $writes >= 1;
		});

		$primed = $reader->prime($stream, true);
		$out = '';
		$end = $reader->pump($stream, $primed['head'], 9, $primed['reads'], function (string $block) use (&$out, &$writes): void {
			$out .= $block;
			$writes++;
		});

		self::assertSame(BoundedStreamReader::END_ABORTED, $end);
		self::assertSame('abc', $out);
		self::assertTrue(ScriptedStream::closed('gone'));
	}

	public function testTheNudgeThroughARealPipeEndsAWaitingProcess(): void {
		// The claim of research section 1.5 with a real process: a process that
		// waits for one line on stdin, as smbclient waits after a failed open,
		// ends when every read writes an empty line, and the reader sees the end
		// of its stdout instead of waiting forever. The counter case below
		// leaves the nudge out and runs into the deadline.
		if (!function_exists('proc_open') || !is_executable('/bin/sh')) {
			self::markTestSkipped('proc_open or /bin/sh is not available here');
		}

		[$process, $stdin, $stdout] = self::waitingProcess();
		$stream = self::viewLayer(self::smbLayer($stdout, static function () use ($stdin): void {
			// The spelling of Wrapped/RawConnection::write.
			@fwrite($stdin, PHP_EOL);
			fflush($stdin);
		}));
		$started = hrtime(true);

		$primed = (new BoundedStreamReader(firstByteSeconds: 5.0))->prime($stream, true);

		$elapsed = (hrtime(true) - $started) / 1e9;
		fclose($stream);
		fclose($stdin);
		proc_close($process);
		self::assertSame(BoundedStreamReader::OUTCOME_EMPTY, $primed['outcome']);
		self::assertLessThan(2.0, $elapsed);
	}

	public function testWithoutTheNudgeTheRealPipeRunsIntoTheDeadline(): void {
		if (!function_exists('proc_open') || !is_executable('/bin/sh')) {
			self::markTestSkipped('proc_open or /bin/sh is not available here');
		}

		[$process, $stdin, $stdout] = self::waitingProcess();
		$stream = self::viewLayer(self::smbLayer($stdout, static function (): void {
		}));

		$primed = (new BoundedStreamReader(firstByteSeconds: 0.5))->prime($stream, true);

		proc_terminate($process);
		fclose($stream);
		fclose($stdin);
		proc_close($process);
		self::assertSame(BoundedStreamReader::OUTCOME_TIMEOUT, $primed['outcome']);
	}

	/**
	 * @return array{0: resource, 1: resource, 2: resource}
	 */
	private static function waitingProcess(): array {
		$pipes = [];
		$process = proc_open(['/bin/sh', '-c', 'read line; exit 0'], [0 => ['pipe', 'r'], 1 => ['pipe', 'w']], $pipes);
		self::assertIsResource($process);

		return [$process, $pipes[0], $pipes[1]];
	}
}
