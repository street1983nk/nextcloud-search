<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\SearchFilters;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * The one parser of the type groups, SearchFilters::typesFrom() (plan 32-01).
 *
 * Two readers go through it since USRCH-01: the address of the own result page
 * and the type filter of the unified search dialog. Both cases below are about
 * the second promise of D-32-03 and of ROADMAP success criterion 3: whatever
 * reaches this parser and is not one of the six names leaves no group behind,
 * so the search runs as if no filter had been set, and nothing throws. The
 * container would answer an unknown name with a 422, and a 422 arrives in the
 * dialog as an empty result group; this parser is what keeps such a name from
 * ever being sent.
 */
#[CoversClass(SearchFilters::class)]
final class SearchFiltersTest extends TestCase {
	public function testOneKnownNameIsThatGroup(): void {
		self::assertSame(['pdf'], SearchFilters::typesFrom('pdf'));
	}

	public function testCaseAndBlanksAroundANameAreForgiven(): void {
		// What a person types into the filter field: a capital and a space after
		// the comma. Both are a slip and not a different name.
		self::assertSame(['pdf', 'images'], SearchFilters::typesFrom('PDF, images'));
	}

	public function testTheOutputIsCanonicalAndFreeOfDuplicates(): void {
		// The order of TYPES and not the order written, because the cursor path
		// of a filtered search is bound to a fingerprint of this list.
		self::assertSame(['pdf', 'images'], SearchFilters::typesFrom('images,pdf,pdf'));
	}

	public function testAnUnknownNameNextToAKnownOneFallsAwayAndTheKnownOneStays(): void {
		// D-32-03 in one line: the unknown name costs itself and nothing else,
		// and it never reaches the container, which would refuse the whole body.
		self::assertSame(['pdf'], SearchFilters::typesFrom('pdf,videos'));
	}

	/**
	 * @return array<string,array{string}>
	 */
	public static function valuesThatNameNoGroup(): array {
		return [
			'an unknown name' => ['videos'],
			'the empty value' => [''],
			'commas only' => [',,,'],
			'a blank' => [' '],
			'a NUL byte after a name' => ["pdf\0"],
			'a line break after a name' => ["pdf\n"],
			'a foreign separator' => ['pdf;images'],
			'a name inside a longer word' => ['pdfs'],
			'a regex fragment' => ['.*'],
		];
	}

	#[DataProvider('valuesThatNameNoGroup')]
	public function testAValueThatNamesNoGroupLeavesNoGroupBehind(string $raw): void {
		// "pdf;images" is one token and not two: there is no second separator
		// and no substring match, so a value somebody built cannot smuggle a
		// known name past the comparison.
		self::assertSame([], SearchFilters::typesFrom($raw));
	}

	public function testAnOverlongValueIsNotEvenSplitAndNamesNoGroup(): void {
		// It begins with a real name on purpose: the bound is checked before the
		// split, so a known name at the front does not survive a value that is
		// not a list anybody picked.
		$raw = str_pad('pdf,', 5000, 'x');

		self::assertSame(5000, strlen($raw));
		self::assertSame([], SearchFilters::typesFrom($raw));
	}

	public function testAValueAtTheBoundIsStillRead(): void {
		// The other edge of the same bound, so that it is a bound and not an
		// accident: a value of exactly MAX_TYPES_LENGTH bytes is still a list.
		$raw = str_pad('pdf,', SearchFilters::MAX_TYPES_LENGTH, ',');

		self::assertSame(SearchFilters::MAX_TYPES_LENGTH, strlen($raw));
		self::assertSame(['pdf'], SearchFilters::typesFrom($raw));
		self::assertSame([], SearchFilters::typesFrom($raw . ','));
	}

	public function testAllSixNamesTwiceAreTheSixNamesOnce(): void {
		// Six is the ceiling whatever arrives, because the loop runs over the
		// closed list and not over the value.
		$raw = implode(',', [...SearchFilters::TYPES, ...SearchFilters::TYPES]);

		self::assertSame(SearchFilters::TYPES, SearchFilters::typesFrom($raw));
	}
}
