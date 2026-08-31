<?php

declare(strict_types=1);

namespace OCA\Findling\Text;

/**
 * Bounded plain text, in one place for both halves of the search path.
 *
 * Two callers need exactly the same cleaning and must not drift apart: the
 * proxy, which bounds what the container sends, and the search provider, which
 * bounds the file name and the path of a node. A file name out of an external
 * storage is no more trustworthy than a container answer.
 *
 * Defense in depth, not the primary control. The primary control is that the
 * search dialog interpolates title and subline as text, so markup reaches the
 * user verbatim instead of being rendered. What is left over are the two things
 * text interpolation does not help against: control characters, which can
 * reorder a line (bidi overrides), fake a second line in the Nextcloud log or
 * cut a string short in a terminal, and length, which is a rendering problem in
 * the dialog and a memory problem in the answer.
 */
final class PlainText {
	/**
	 * The tab survives, everything else in that range does not. A snippet from
	 * the container is a single line by construction, so nothing legitimate is
	 * lost; should a later phase want to keep newlines, they belong folded into
	 * spaces here rather than passed through.
	 *
	 * Invalid UTF-8 is a null and the caller drops the value. Passing it on
	 * would break the JSON and the XML rendering of the OCS answer, which costs
	 * the whole unified search instead of one result.
	 *
	 * @return string|null null when the input is not valid UTF-8
	 */
	public static function bounded(string $value, int $maxLength): ?string {
		$clean = preg_replace('/(?!\t)[\p{Cc}\p{Cf}\p{Zl}\p{Zp}]/u', '', $value);
		if ($clean === null) {
			return null;
		}

		// Characters, not bytes: cutting a UTF-8 string at a byte offset
		// produces half a character, which is exactly the invalid input this
		// method exists to keep out.
		return mb_substr($clean, 0, $maxLength, 'UTF-8');
	}
}
