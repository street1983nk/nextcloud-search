<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\ExAppService;
use OCA\Findling\Text\Highlighter;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The one place of the result page where data turns into anything a browser
 * treats as structure, and therefore the one that gets a suite of its own.
 *
 * Every case below asserts pieces of plain text with a flag, never a string
 * that carries a tag. That is the whole point of the class under test: the
 * template puts the marking element around a piece and sends the piece itself
 * through the escaping printer, so no assertion here may ever be allowed to
 * pass by comparing markup. A test that expected a tag would be a test that had
 * already accepted the construction this class exists to avoid.
 *
 * The second half of the suite is about offsets. They arrive as character
 * offsets from the container, they survive the cleaning of PlainText because
 * that cleaning is length preserving, and a single byte based cut here would
 * put the mark on the wrong word for every German text with an umlaut in front
 * of the hit. So both directions are asserted, in a text with umlauts and with
 * a character outside the Basic Multilingual Plane whose byte offset and
 * character offset differ by four.
 */
#[CoversClass(Highlighter::class)]
final class HighlighterTest extends TestCase {
	/**
	 * The ceiling of the sender, read rather than copied. Same rule and same
	 * reason as in ProviderTest: a bound written into this file is a bound that
	 * keeps being asserted after somebody moved it in the class.
	 */
	private function highlightCeiling(): int {
		$value = (new \ReflectionClass(ExAppService::class))->getConstant('MAX_HIGHLIGHTS');

		self::assertIsInt($value, 'MAX_HIGHLIGHTS is gone or is no longer an int');

		return $value;
	}

	/**
	 * The text of every piece, in order, glued back together.
	 *
	 * @param list<array{text:string,mark:bool}> $segments
	 */
	private function rejoin(array $segments): string {
		return implode('', array_column($segments, 'text'));
	}

	/**
	 * How many pieces of a result carry the mark.
	 *
	 * @param list<array{text:string,mark:bool}> $segments
	 */
	private function marked(array $segments): int {
		return count(array_filter($segments, static fn (array $piece): bool => $piece['mark']));
	}

	// -- the shape of the result ---------------------------------------------

	public function testATextWithoutRangesIsOneUnmarkedPiece(): void {
		// The ordinary case of a hit whose excerpt the container could not
		// highlight. It is still an excerpt and it is still shown.
		$segments = Highlighter::segments('Die Rechtsmittelbelehrung fehlt.', []);

		self::assertSame(
			[['text' => 'Die Rechtsmittelbelehrung fehlt.', 'mark' => false]],
			$segments,
		);
	}

	public function testARangeInTheMiddleBecomesThreePieces(): void {
		// Before, the hit, after. Three pieces and not one string, because the
		// template is what decides what a marked piece looks like.
		$segments = Highlighter::segments('abc DEF ghi', [[4, 7]]);

		self::assertSame(
			[
				['text' => 'abc ', 'mark' => false],
				['text' => 'DEF', 'mark' => true],
				['text' => ' ghi', 'mark' => false],
			],
			$segments,
		);
	}

	public function testARangeAtTheStartProducesNoEmptyPieceInFront(): void {
		// An empty piece would render as an empty element in the template, which
		// a screen reader announces and a reader never sees.
		$segments = Highlighter::segments('DEF ghi', [[0, 3]]);

		self::assertSame(
			[
				['text' => 'DEF', 'mark' => true],
				['text' => ' ghi', 'mark' => false],
			],
			$segments,
		);
	}

	public function testARangeAtTheEndProducesNoEmptyPieceBehind(): void {
		$segments = Highlighter::segments('abc DEF', [[4, 7]]);

		self::assertSame(
			[
				['text' => 'abc ', 'mark' => false],
				['text' => 'DEF', 'mark' => true],
			],
			$segments,
		);
	}

	// -- what the sender does not promise ------------------------------------

	public function testTwoRangesArrivingOutOfOrderAreBothMarked(): void {
		// The filter on the sending side checks bounds and count and says
		// nothing about the order, so the order is established here. Both hits
		// are marked and the later one does not swallow the earlier one.
		$segments = Highlighter::segments('aaa BBB ccc DDD eee', [[12, 15], [4, 7]]);

		self::assertSame(
			[
				['text' => 'aaa ', 'mark' => false],
				['text' => 'BBB', 'mark' => true],
				['text' => ' ccc ', 'mark' => false],
				['text' => 'DDD', 'mark' => true],
				['text' => ' eee', 'mark' => false],
			],
			$segments,
		);
	}

	public function testARangeReachingIntoAConsumedOneIsDiscarded(): void {
		// Discarded and not trimmed to fit. A repaired range would be a
		// statement about a position nobody measured, and the honest answer to
		// two ranges that contradict each other is to keep the first one.
		$segments = Highlighter::segments('abcdefghij', [[2, 6], [4, 8]]);

		self::assertSame(
			[
				['text' => 'ab', 'mark' => false],
				['text' => 'cdef', 'mark' => true],
				['text' => 'ghij', 'mark' => false],
			],
			$segments,
		);
	}

	public function testARangeThatEndsWhereItStartsIsDiscarded(): void {
		// Zero length and backwards are the same verdict: there is no piece of
		// text behind either of them.
		$segments = Highlighter::segments('abcdefghij', [[3, 3], [7, 5]]);

		self::assertSame(
			[['text' => 'abcdefghij', 'mark' => false]],
			$segments,
		);
	}

	public function testARangeReachingPastTheEndOfTheTextIsDiscarded(): void {
		// The excerpt and its ranges travel in two fields of the same answer, so
		// a container that shortened one and not the other lands here (T-09-02).
		$segments = Highlighter::segments('kurz', [[2, 99]]);

		self::assertSame(
			[['text' => 'kurz', 'mark' => false]],
			$segments,
		);
	}

	// -- characters, not bytes -----------------------------------------------

	public function testTheOffsetsAreCountedInCharactersAndNotInBytes(): void {
		// German prose in the test datum on purpose: the sharp s costs two bytes
		// and the compass costs four, so the character offset of the marked word
		// is ten while its byte offset is fourteen. A byte based cut would put
		// the mark four characters early, inside the word in front of it.
		$segments = Highlighter::segments('Maßstab 🧭 Belehrung', [[10, 19]]);

		self::assertSame(
			[
				['text' => 'Maßstab 🧭 ', 'mark' => false],
				['text' => 'Belehrung', 'mark' => true],
			],
			$segments,
		);
	}

	public function testThePiecesReassembleTheInputExactly(): void {
		// The property that makes the whole construction safe to render: nothing
		// is added, nothing is dropped, and the excerpt the user reads is the
		// excerpt the container sent.
		$text = 'Größe: 12 Zeichen, Maß: 3 🧭 Belehrung über Rechtsmittel';

		foreach ([[], [[0, 5]], [[7, 9], [28, 37]], [[54, 55]]] as $ranges) {
			self::assertSame($text, $this->rejoin(Highlighter::segments($text, $ranges)));
		}
	}

	// -- the ceiling ---------------------------------------------------------

	public function testMoreRangesThanTheCeilingAreCutOffAtIt(): void {
		// Forty non overlapping ranges arrive, the ceiling of the sender is
		// thirty two, and the remaining eight stay part of the unmarked tail.
		$ceiling = $this->highlightCeiling();
		$text = str_repeat('ab', 100);
		$ranges = [];
		for ($index = 0; $index < 40; $index++) {
			$ranges[] = [$index * 2, $index * 2 + 1];
		}

		$segments = Highlighter::segments($text, $ranges);

		self::assertSame($ceiling, $this->marked($segments));
		self::assertSame($text, $this->rejoin($segments));
	}
}
