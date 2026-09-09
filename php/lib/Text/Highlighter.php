<?php

declare(strict_types=1);

namespace OCA\Findling\Text;

use OCA\Findling\Service\ExAppService;

/**
 * An excerpt and its highlight ranges become a list of text pieces, and no
 * piece is ever a piece of markup.
 *
 * This is the one place on the result page where data from the container turns
 * into anything with structure, and the shape of the answer is the whole point:
 * the method hands back plain text with a flag, the template puts the marking
 * element around a flagged piece and sends every piece through the escaping
 * printer. So there is not a single string on that page that builds structure
 * out of data, and gate C keeps its strictest form: the unescaping printer is
 * absent and there is no way around it (T-09-02).
 *
 * The order of the ranges is established here and not trusted, because the
 * filter on the sending side checks bounds and count and promises nothing about
 * the order. A range that reaches into an already consumed one is dropped
 * rather than trimmed to fit: a repaired range would be a statement about a
 * position in the text that nobody measured, and the honest answer to two
 * ranges that contradict each other is to keep the first and forget the second.
 * The same goes for a range that ends where it starts and for one that reaches
 * past the end of the text, which is what a container that shortened the
 * excerpt and not its ranges would send.
 *
 * Every offset is a character offset and never a byte offset. That is what the
 * container sends, and it survives the cleaning in {@see PlainText::bounded()}
 * because that cleaning replaces one character with one character and says so
 * in its own comment. A byte based cut would put the mark four characters early
 * in any German excerpt with an umlaut in front of the hit, and it would cut a
 * multi byte character in half, which is exactly the invalid input the whole
 * text path exists to keep out.
 */
final class Highlighter {
	/**
	 * The pieces of one excerpt, in reading order.
	 *
	 * The pieces always reassemble the input exactly: nothing is added, nothing
	 * is dropped, and no empty piece is produced, so a range at the very start
	 * or at the very end does not turn into an empty element on the page. An
	 * empty excerpt gives an empty list, which the template renders as no
	 * excerpt line at all.
	 *
	 * @param string $text the excerpt, already cleaned and bounded
	 * @param list<mixed> $ranges pairs of character offsets as the container
	 *                            sent them, in any order
	 * @return list<array{text:string,mark:bool}>
	 */
	public static function segments(string $text, array $ranges): array {
		$length = mb_strlen($text, 'UTF-8');
		$usable = self::usable($ranges, $length);
		usort($usable, static fn (array $a, array $b): int => $a[0] <=> $b[0]);

		$segments = [];
		$cursor = 0;
		$marked = 0;

		foreach ($usable as [$start, $end]) {
			if ($marked >= ExAppService::MAX_HIGHLIGHTS) {
				// The ceiling of the sender, read from the constant rather than
				// written down again. What is left over stays part of the
				// unmarked tail, so the excerpt is still complete and only its
				// marks stop.
				break;
			}

			if ($start < $cursor) {
				continue;
			}

			if ($start > $cursor) {
				$segments[] = ['text' => mb_substr($text, $cursor, $start - $cursor, 'UTF-8'), 'mark' => false];
			}

			$segments[] = ['text' => mb_substr($text, $start, $end - $start, 'UTF-8'), 'mark' => true];
			$cursor = $end;
			$marked++;
		}

		if ($cursor < $length) {
			$segments[] = ['text' => mb_substr($text, $cursor, null, 'UTF-8'), 'mark' => false];
		}

		return $segments;
	}

	/**
	 * The ranges that are a pair of integer character offsets inside the text,
	 * with everything else dropped without a word.
	 *
	 * Checked here and not while walking, so that the sort below can never be
	 * handed something that is not a pair. The bounds are checked again even
	 * though the sending side checks them too: this method is the last station
	 * before an offset is used to cut a string, and one check at the place where
	 * the value is used is worth more than two somewhere upstream.
	 *
	 * @param list<mixed> $ranges
	 * @return list<array{int,int}>
	 */
	private static function usable(array $ranges, int $length): array {
		$usable = [];

		foreach ($ranges as $range) {
			if (!is_array($range) || !isset($range[0], $range[1]) || !is_int($range[0]) || !is_int($range[1])) {
				continue;
			}

			$start = $range[0];
			$end = $range[1];
			if ($start < 0 || $end <= $start || $end > $length) {
				continue;
			}

			$usable[] = [$start, $end];
		}

		return $usable;
	}
}
