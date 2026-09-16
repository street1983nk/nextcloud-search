<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

/**
 * One hit that has passed the permission decision, and the four fields a
 * caller may render out of it.
 *
 * Title, path, mime type and modification date come out of the confirmed node
 * and never out of the answer of the container: a confused or a compromised
 * backend can otherwise put the name of a foreign file in front of the user,
 * and it would be believed because it arrived through the same field as a true
 * one.
 *
 * The date is the newest of the four and the one where the shorter road is the
 * wrong one, so the reason is written down rather than left to be rediscovered.
 * The Candidate model of the container does carry an mtime of its own, and
 * ExAppService::filterCandidates() drops it, as it drops everything a candidate
 * carries besides its file id. That stays so. Anything that arrives before the
 * recheck is a proposal, and a proposal that reaches the display is exactly the
 * disclosure the two stage protocol was built against. A timestamp out of the
 * index would on top of that be older than the node: the node is what the file
 * system says right now, the index is what it said when it was last read.
 *
 * A fileId of 0 is the canary path of phase 1 and the one named exception to
 * the sentences above. There is no file behind that id, so nothing can be
 * confirmed for it; its title and its path are the text the container composed
 * out of host name, timestamp and the user id of the signed header, its mime
 * type stays empty because a text without a file has no type, and its date
 * stays 0 because there is no node to ask. A caller that renders a date reads
 * the file id first, in the same way it already does for the link.
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
	 * @param int $mtime the modification date of the confirmed node, Unix epoch
	 *                   in seconds, and 0 when there is no node, which is the
	 *                   canary and nothing else
	 */
	public function __construct(
		public readonly int $fileId,
		public readonly string $title,
		public readonly string $path,
		public readonly string $mimeType,
		public readonly int $mtime,
	) {
	}
}
