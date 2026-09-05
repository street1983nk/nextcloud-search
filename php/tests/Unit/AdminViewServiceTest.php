<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\AdminViewService;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * The two pieces of arithmetic of the status page that can be asked without a
 * Nextcloud: the stall verdict (DI-05-22) and the coverage figures (D-16).
 *
 * Both are static and public for the same reason, and the reason is written out
 * at each of them: they are the arithmetic and nothing else, and the
 * alternative to reaching them directly is a unit test which builds a whole
 * admin view out of twelve doubles in order to ask what a fraction of two
 * numbers comes to. Everything around them, the reading and the writing of
 * appconfig and the assembly of the answer, stays in the page where it cannot
 * be tested without a server anyway.
 *
 * The first half of this file, the stall verdict:
 *
 * What this defends. The page used to measure one thing, how long ago the last
 * background job of this app ran, and it called everything above half an hour a
 * stall. In the full run of plan 05-14 the crawl finished at 01:30Z and the
 * container wrote roughly 6.500 more documents until 09:27Z, so for eight hours,
 * over the majority of the run, the page said "Indexing has not progressed"
 * while the coverage figure in the same row climbed from 82 to 99 per cent. On
 * an ordinary instance the two halves end together and nobody notices; on the
 * hardware this product is built for the OCR pass is 77 per cent of the run.
 *
 * Why this asks a static method instead of the page. The verdict is built out of
 * a background job stamp, a counter of the container and the counter this side
 * remembered from the poll before, and everything interesting about it is the
 * arithmetic over those numbers. Asking it through overview() would mean twelve
 * doubles, a status answer and a scan statistic in order to find out what a
 * counter that grew by one means, and the answer would be buried in the setup.
 * The reading and the writing of appconfig stay in the page, where they cannot
 * be tested without a Nextcloud anyway.
 *
 * The two sides of the boundary are the two groups below: a counter that grew is
 * progress and ends the stall, and everything else leaves the previous stamp
 * standing, which is what keeps the old verdict intact for the case it was
 * always right about.
 */
#[CoversClass(AdminViewService::class)]
final class AdminViewServiceTest extends TestCase {
	/** A poll, as a Unix timestamp. Any fixed number does; this one is readable. */
	private const NOW = 1_800_000_000;

	/** The stamp of an earlier progress, an hour before this poll. */
	private const EARLIER = self::NOW - 3600;

	// -- the first side: the counter grew, so it is not a stall ---------------

	public function testACounterThatGrewIsProgressAndStampsThisPoll(): void {
		// The OCR pass of the measured run, in one line: the crawl is long over,
		// no background job of this app has anything to do, and the container is
		// writing documents. That is the case the page accused for eight hours.
		$stamp = AdminViewService::progressStamp(true, 43_600, 43_599, self::EARLIER, self::NOW);

		self::assertSame(self::NOW, $stamp);
	}

	public function testProgressOutranksAnOldBackgroundJob(): void {
		// The verdict itself, as far as it can be asked here: the age the page
		// reports is the age of the LATER of the two movements. With the
		// container moving, the job stamp of eight hours ago does not decide.
		$jobRun = self::NOW - 30_000;
		$stamp = AdminViewService::progressStamp(true, 50_000, 43_600, self::EARLIER, self::NOW);

		self::assertSame(0, self::NOW - max($jobRun, $stamp));
	}

	// -- the other side: nothing moved, so the old verdict stands -------------

	/**
	 * Four ways of not being progress, and every one of them has to leave the
	 * previous stamp exactly as it was. An unchanged answer is also the signal
	 * that nothing has to be written, so a branch that returned the current time
	 * here would additionally turn a page that polls every five seconds into an
	 * appconfig write every five seconds.
	 *
	 * @return array<string,array{bool,int,int}>
	 */
	public static function everythingThatIsNotProgress(): array {
		return [
			'the counter stands still' => [true, 43_600, 43_600],
			'the counter fell, which is a reindex and not progress' => [true, 12, 43_600],
			'the container does not answer at all' => [false, 43_600, 43_599],
			'the first answer this instance has ever seen' => [true, 43_600, 0],
		];
	}

	#[DataProvider('everythingThatIsNotProgress')]
	public function testWithoutProgressTheEarlierStampStands(bool $reachable, int $indexed, int $remembered): void {
		$stamp = AdminViewService::progressStamp($reachable, $indexed, $remembered, self::EARLIER, self::NOW);

		self::assertSame(self::EARLIER, $stamp);
	}

	public function testWithoutProgressAnOldBackgroundJobStillDecides(): void {
		// The case the old verdict was right about, unchanged: work is waiting,
		// the last job is eight hours old and the container has finished nothing
		// in the meantime. The page has to keep saying so.
		$jobRun = self::NOW - 30_000;
		$stamp = AdminViewService::progressStamp(true, 43_600, 43_600, 0, self::NOW);

		self::assertSame(30_000, self::NOW - max($jobRun, $stamp));
	}

	public function testAnInstanceWithNoJobAndNoProgressHasNoAgeAtAll(): void {
		// Nought and not "since the epoch". A fresh installation has no movement
		// to measure the age of, and the page answers that with its own state,
		// never with a span of fifty five years.
		$stamp = AdminViewService::progressStamp(true, 0, 0, 0, self::NOW);

		self::assertSame(0, max(0, $stamp));
	}

	// -- the two coverage figures: one calculation, two numerators ------------

	/**
	 * What the page shows during the embedding pass, in one line: the full text
	 * half is complete and the semantic half is a quarter of the way through.
	 *
	 * The two figures come out of one call each of the same method, with the
	 * same denominator, and that is what makes putting them next to each other
	 * honest (D-16). Two calculations for one kind of number would agree on the
	 * day they are written and drift on the day one of them is corrected, and
	 * nothing on the page would show it.
	 */
	public function testBothFiguresComeOutOfOneCalculationOverOneDenominator(): void {
		$indexable = 200;

		$indexed = AdminViewService::coverageShare(200, $indexable, true);
		$embedded = AdminViewService::coverageShare(50, $indexable, true);

		self::assertSame(100, $indexed);
		self::assertSame(25, $embedded);
		// The property that makes the pair readable: as long as fewer documents
		// carry a vector than have been judged, the second figure cannot be the
		// larger one. It holds because both go through one calculation.
		self::assertLessThanOrEqual($indexed, $embedded);
	}

	public function testTheSecondFigureStaysBelowAHundredWhileDocumentsWithoutVectorsAreLeft(): void {
		// One document of two hundred is missing, and floor() alone would round
		// that to a hundred. A page that says a hundred per cent with files left
		// over is the failure this whole phase exists to make impossible.
		self::assertSame(99, AdminViewService::coverageShare(199, 200, true));
		self::assertSame(99, AdminViewService::coverageShare(1_999, 2_000, true));
		self::assertSame(100, AdminViewService::coverageShare(200, 200, true));
	}

	/**
	 * Three ways of having no honest figure, and all three answer null.
	 *
	 * The second row carries two readings of this plan and they are one argument
	 * here on purpose: a container that is silent and a container that does not
	 * report the embedded count at all both leave this method without a
	 * numerator, and both have to answer null rather than nought. Which of the
	 * two happened is decided in coverage(), where the missing key becomes the
	 * false this row passes in.
	 *
	 * @return array<string,array{int,int,bool}>
	 */
	public static function everythingWithoutAnHonestFigure(): array {
		return [
			'no denominator, because nothing has been counted yet' => [0, 0, true],
			'no numerator, because the container is silent or did not report it' => [0, 200, false],
		];
	}

	#[DataProvider('everythingWithoutAnHonestFigure')]
	public function testWithoutAnHonestFigureTheAnswerIsNullAndNotNought(
		int $counted,
		int $indexable,
		bool $available,
	): void {
		self::assertNull(AdminViewService::coverageShare($counted, $indexable, $available));
	}

	public function testAFigureIsNeverNegativeAndNeverAboveAHundred(): void {
		// Neither input can legitimately occur, and both would be visible as a
		// defect of the page rather than of whatever produced them. A progress
		// bar with a negative value renders as an empty bar and says nothing.
		self::assertSame(0, AdminViewService::coverageShare(-5, 200, true));
		self::assertSame(100, AdminViewService::coverageShare(300, 200, true));
	}
}
