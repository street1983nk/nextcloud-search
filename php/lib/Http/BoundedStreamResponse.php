<?php

declare(strict_types=1);

namespace OCA\Findling\Http;

use OCP\AppFramework\Http;
use OCP\AppFramework\Http\ICallbackResponse;
use OCP\AppFramework\Http\IOutput;
use OCP\AppFramework\Http\Response;
use Psr\Log\LoggerInterface;

/**
 * The 200 of the content gateway once the first block is in (plan 43-17).
 *
 * It takes the place of StreamResponse, whose callback hands the stream to
 * readfile and with it to a blocking copy that waits as long as the source
 * does. This one writes the block the gateway read ahead and then the rest
 * through BoundedStreamReader::pump(), block by block through setOutput, with
 * the idle deadline and the cap on reads of that class. The stream is closed on
 * every way out, by pump().
 *
 * Deliberately no length header. The size the gateway knows is the one of the
 * file cache, which can be out of date (POL-02), and a body that ends before a
 * promised length is a broken connection to the container, which it counts as
 * an outage of the gateway. Without the header a short body is a ShortRead
 * about this one file. The limit of that (W10): when the container expects 0
 * bytes, which an entry handed over by requeueAs can carry, it cannot tell a
 * short body from a complete one.
 *
 * The log lines are static sentences with the file id and nothing else
 * (security audit L6). A client that went away gets no line: that is the
 * container ending a fetch, not a problem of the file.
 *
 * @template-extends Response<Http::STATUS_OK, array<string, mixed>>
 */
final class BoundedStreamResponse extends Response implements ICallbackResponse {
	/**
	 * @param resource $stream
	 */
	public function __construct(
		private $stream,
		private string $head,
		private int $size,
		private int $readsSoFar,
		private bool $capReads,
		private int $fileId,
		private BoundedStreamReader $reader,
		private LoggerInterface $logger,
	) {
		parent::__construct(Http::STATUS_OK);
	}

	#[\Override]
	public function callback(IOutput $output) {
		$end = $this->reader->pump(
			$this->stream,
			$this->head,
			$this->size,
			$this->readsSoFar,
			static function (string $block) use ($output): void {
				$output->setOutput($block);
			},
			$this->capReads,
		);

		if ($end === BoundedStreamReader::END_STALLED) {
			$this->logger->warning('Findling: a file stalled while it was served, the answer ended short', ['fileId' => $this->fileId]);
		} elseif ($end === BoundedStreamReader::END_SHORT) {
			$this->logger->warning('Findling: a file ended before its size while it was served', ['fileId' => $this->fileId]);
		}
	}
}
