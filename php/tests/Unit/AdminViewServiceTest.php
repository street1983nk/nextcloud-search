<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\AdminViewService;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * The stall verdict of the status page, on both sides of its boundary
 * (DI-05-22).
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
}
