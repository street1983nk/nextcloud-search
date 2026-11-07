<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use Icewind\Streams\Wrapper;

/**
 * A stand in for the stream of server side encryption, for
 * BoundedStreamReaderTest.
 *
 * lib/private/Files/Stream/Encryption.php reads its source through
 * stream_read_block: it keeps reading until a block is full or one read brings
 * 0 bytes, and decrypts what it has. On a non blocking source the first empty
 * read would end that loop with half a cipher block (B1 of the research). This
 * class reproduces exactly that loop, without the cipher, and passes
 * stream_set_blocking on to its source the way every icewind wrapper does
 * (Wrapper::stream_set_option). That pass through is the reason the gateway
 * decides by storage and never by the stream layer it sees.
 */
final class BlockCollectingStream extends Wrapper {
	public const BLOCK_BYTES = 8192;

	/**
	 * @param resource $source
	 * @return resource
	 */
	public static function wrap($source) {
		$stream = self::wrapSource($source, [], null, null, 'r');
		if (!is_resource($stream)) {
			throw new \RuntimeException('the block collecting stream did not open');
		}

		return $stream;
	}

	public function stream_open($path, $mode, $options, &$opened_path) {
		$this->loadContext();

		return true;
	}

	public function stream_read($count) {
		$remaining = self::BLOCK_BYTES;
		$data = '';
		do {
			$chunk = parent::stream_read($remaining);
			if ($chunk === false) {
				return $data === '' ? false : $data;
			}
			$length = strlen($chunk);
			$data .= $chunk;
			$remaining -= $length;
		} while ($remaining > 0 && $length > 0);

		return $data;
	}
}
