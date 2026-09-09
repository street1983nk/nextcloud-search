<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

/**
 * One hit that has passed the permission decision, and the three fields a
 * caller may render out of it.
 *
 * Title, path and mime type come out of the confirmed node and never out of the
 * answer of the container: a confused or a compromised backend can otherwise
 * put the name of a foreign file in front of the user, and it would be believed
 * because it arrived through the same field as a true one.
 *
 * A fileId of 0 is the canary path of phase 1 and the one named exception to
 * the sentence above. There is no file behind that id, so nothing can be
 * confirmed for it; its title and its path are the text the container composed
 * out of host name, timestamp and the user id of the signed header, and its
 * mime type stays empty because a text without a file has no type.
 *
 * A caller that renders the canary links it to the file list and never to a
 * fileid, because a link to file 0 resolves to nothing.
 */
final class ApprovedHit {
	/**
	 * @param int $fileId the confirmed file id, or 0 for the canary
	 * @param string $title the name of the confirmed node, bounded
	 * @param string $path the path of the confirmed node relative to the home
	 *                     folder, bounded
	 * @param string $mimeType the mime type of the confirmed node, empty for
	 *                         the canary
	 */
	public function __construct(
		public readonly int $fileId,
		public readonly string $title,
		public readonly string $path,
		public readonly string $mimeType,
	) {
	}
}
