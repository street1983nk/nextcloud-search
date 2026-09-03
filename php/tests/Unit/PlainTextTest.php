<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Text\PlainText;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * Behaviour 6 of docs/testing.md, section "The gap", in five separate cases.
 *
 * What this defends: the search dialog interpolates title and subline as text,
 * so markup reaches the user verbatim instead of being rendered, and that is the
 * primary control. What text interpolation does not help against is what is
 * asserted here. Control characters can reorder a line through a bidi override,
 * fake a second line in the Nextcloud log or cut a string short in a terminal,
 * and length is a rendering problem in the dialog and a memory problem in the
 * answer. Both apply to a file name out of an external storage exactly as much
 * as to a container answer, which is why this class has two callers.
 */
#[CoversClass(PlainText::class)]
final class PlainTextTest extends TestCase {
	// -- case 1: the replacement is one character for one character ----------

	public function testEveryControlCharacterBecomesExactlyOneSpaceSoTheLengthIsPreserved(): void {
		// The length is not cosmetics and this case is not interchangeable with
		// the one below it. ExAppService compares the length of the cleaned
		// excerpt against the length of the raw one to decide whether the
		// highlight offsets still point at the right characters, which is
		// behaviour 12 of the same list. A cleaning that folded a run of
		// whitespace into a single space would read better and would silently
		// move every offset behind the first line break. If this case falls, the
		// handling of the highlight ranges falls with it.
		$raw = "Verwaltungsbehoerde\r\nDie Grundstuecke\x00liegen dort";

		$clean = PlainText::bounded($raw, 1000);

		self::assertNotNull($clean);
		self::assertSame('Verwaltungsbehoerde  Die Grundstuecke liegen dort', $clean);
		self::assertSame(mb_strlen($raw, 'UTF-8'), mb_strlen($clean, 'UTF-8'));
	}

	/**
	 * @return array<string,array{string}>
	 */
	public static function controlCharactersThatAreNotTheTab(): array {
		return [
			'null byte' => ["\x00"],
			'carriage return' => ["\r"],
			'line feed' => ["\n"],
			'escape' => ["\x1b"],
			'a bidi override, which can reorder a whole line' => ["\u{202E}"],
			'a zero width joiner' => ["\u{200D}"],
			'a line separator' => ["\u{2028}"],
			'a paragraph separator' => ["\u{2029}"],
		];
	}

	#[DataProvider('controlCharactersThatAreNotTheTab')]
	public function testAControlCharacterIsReplacedRatherThanRemoved(string $character): void {
		$clean = PlainText::bounded('a' . $character . 'b', 100);

		self::assertSame('a b', $clean);
	}

	// -- case 2: the tab survives --------------------------------------------

	public function testTheTabIsTheOneCharacterOfThatRangeThatIsKept(): void {
		$clean = PlainText::bounded("Spalte\tWert", 100);

		self::assertSame("Spalte\tWert", $clean);
	}

	// -- case 3: it caps at the given length ---------------------------------

	public function testItCapsAtTheGivenLengthAndLeavesAShorterValueAlone(): void {
		self::assertSame('abcd', PlainText::bounded('abcdefghij', 4));
		self::assertSame('abc', PlainText::bounded('abc', 4));
		self::assertSame('', PlainText::bounded('abcdefghij', 0));
	}

	// -- case 4: it cuts on a character boundary -----------------------------

	public function testItCutsOnACharacterBoundaryAndNeverInsideAMultibyteCharacter(): void {
		// Four characters, eight bytes. Cutting at a byte offset would produce
		// half a character, which is exactly the invalid input this method exists
		// to keep out: it would break the JSON and the XML rendering of the OCS
		// answer and cost the whole unified search rather than one result.
		$clean = PlainText::bounded('äöüß', 2);

		self::assertSame('äö', $clean);
		self::assertSame(2, mb_strlen((string)$clean, 'UTF-8'));
		self::assertSame(4, strlen((string)$clean));
		self::assertTrue(mb_check_encoding((string)$clean, 'UTF-8'));
	}

	public function testTheBoundaryHoldsForCharactersOutsideTheBasicPlaneToo(): void {
		// An emoji is four bytes in UTF-8 and one character. The corpus of this
		// project has file names with them, and a half emoji is a broken answer.
		$clean = PlainText::bounded('ab😀cd', 3);

		self::assertSame('ab😀', $clean);
		self::assertTrue(mb_check_encoding((string)$clean, 'UTF-8'));
	}

	// -- case 5: invalid UTF-8 is refused, not repaired ----------------------

	/**
	 * @return array<string,array{string}>
	 */
	public static function invalidUtf8(): array {
		return [
			'a lead byte with no continuation' => ["Report\xC3\x28.pdf"],
			'a bare continuation byte' => ["Report\x80.pdf"],
			'a truncated three byte sequence' => ["Report\xE2\x82.pdf"],
			'an overlong encoding of the null byte' => ["Report\xC0\x80.pdf"],
		];
	}

	#[DataProvider('invalidUtf8')]
	public function testInvalidUtf8IsRefusedAndNotRepaired(string $raw): void {
		// Null and not a best effort string. The caller drops the value, which is
		// one lost hit; passing on a repaired guess would be a file name the user
		// never had, and passing on the raw bytes would break the answer for
		// every other hit in it.
		self::assertNull(PlainText::bounded($raw, 255));
	}

	public function testValidUtf8ThatMerelyLooksExoticIsNotRefused(): void {
		// The counter sample of the case above. Without it a method that returned
		// null for everything would pass all four rows of the provider.
		self::assertSame('Grundstücksübertragung 東京 😀', PlainText::bounded('Grundstücksübertragung 東京 😀', 255));
	}
}
