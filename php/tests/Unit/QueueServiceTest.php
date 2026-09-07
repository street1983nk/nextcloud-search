<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\QueueService;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The one piece of arithmetic of the acknowledgement that can be asked without a
 * Nextcloud: which failed verdicts a batch takes back (DI-06.1-34).
 *
 * What this defends, and it is a sentence an owner said out loud rather than a
 * hypothesis. After the Office fix of plan 06.1-19 the status page of a fresh
 * instance showed "4 failed" and an error group "File damaged, 4" with the
 * remedy "upload the file again", while all four of those files were findable
 * through their content. The cause was a decision taken half way: this side
 * writes `indexed` never, on purpose, so a row that once said `failed` had
 * nobody who could contradict it. Nothing aged it out either. The first
 * impression of every freshly installed instance was therefore a page
 * contradicting itself, permanently.
 *
 * Why this asks a static method instead of the service. The interesting half is
 * the set arithmetic: three subtractions, each of which is a way to get the
 * repair wrong, and the worst of them silently erases a true failure. Asking it
 * through acknowledge() would mean a database, a queue mapper, a state table and
 * a transaction in order to find out which of four ids is left in a set, and the
 * answer would be buried in the setup. The reading and the writing stay in the
 * service, where they cannot be tested without a server anyway. That is the same
 * split AdminViewServiceTest documents for the coverage figures.
 *
 * The four groups below are the rule and its three exceptions:
 *
 * 1. a success outranks a failed verdict,
 * 2. a verdict this very call wrote is left alone,
 * 3. a row that extracted nothing may not revoke anything,
 * 4. an id that cannot be resolved is answered with "not yet", never a guess.
 */
#[CoversClass(QueueService::class)]
final class QueueServiceTest extends TestCase {
	/**
	 * The file id of the sight check, kept because it is the case this exists
	 * for: ref=183 answered `state failed, reason corrupt` with a timestamp from
	 * before the fix while the same document was findable.
	 */
	private const REPAIRED_FILE = 183;

	/** The queue row that carried it, on the ordinary content track. */
	private const REPAIRED_ROW = 9_001;

	// -- 1. the rule: a success outranks a failed verdict ---------------------

	public function testAFileThatFailedAndSucceededLaterIsRevoked(): void {
		// The sight check in one line: the row comes back done and the container
		// judges nothing about it, which is how it reports an indexed file.
		$revocable = QueueService::revocableFileIds(
			[self::REPAIRED_ROW],
			[self::REPAIRED_ROW => self::REPAIRED_FILE],
			[],
			[],
		);

		self::assertSame([self::REPAIRED_FILE], $revocable);
	}

	public function testTheAnswerIsASetAndNotAListOfRows(): void {
		// Two rows of the same file cannot exist while findling_q_fileid is a
		// unique index, but the answer feeds an IN query and a doubled id would
		// bind a parameter twice for nothing.
		$revocable = QueueService::revocableFileIds(
			[self::REPAIRED_ROW, self::REPAIRED_ROW, 9_002],
			[self::REPAIRED_ROW => self::REPAIRED_FILE, 9_002 => 184],
			[],
			[],
		);

		self::assertSame([self::REPAIRED_FILE, 184], $revocable);
	}

	public function testNothingAcknowledgedRevokesNothing(): void {
		self::assertSame([], QueueService::revocableFileIds([], [], [], []));
	}

	// -- 2. a verdict this call wrote is left alone ---------------------------

	public function testASkipRecordedInTheSameCallIsNotRevokedAgain(): void {
		// The subtraction that is necessary rather than theoretical: a skipped
		// file travels in the done list as well, so without it the transaction
		// would delete the verdict it had just written.
		$revocable = QueueService::revocableFileIds(
			[self::REPAIRED_ROW],
			[self::REPAIRED_ROW => self::REPAIRED_FILE],
			[],
			[self::REPAIRED_FILE => 'no_text_layer'],
		);

		self::assertSame([], $revocable);
	}

	public function testAFailureRecordedInTheSameCallIsNotRevokedAgain(): void {
		// Failures are keyed by queue row id, so they have to be translated
		// through the same map before they can be subtracted. A container that
		// reports one row as done and failed at once is defective; the verdict
		// it wrote still has to survive this method.
		$revocable = QueueService::revocableFileIds(
			[self::REPAIRED_ROW],
			[self::REPAIRED_ROW => self::REPAIRED_FILE],
			[self::REPAIRED_ROW => 'corrupt'],
			[],
		);

		self::assertSame([], $revocable);
	}

	public function testOneJudgedFileDoesNotBlockTheRepairOfAnother(): void {
		$revocable = QueueService::revocableFileIds(
			[self::REPAIRED_ROW, 9_002],
			[self::REPAIRED_ROW => self::REPAIRED_FILE, 9_002 => 184],
			[9_002 => 'corrupt'],
			[],
		);

		self::assertSame([self::REPAIRED_FILE], $revocable);
	}

	// -- 3. a row that extracted nothing may not revoke anything --------------

	public function testARowThatIsNotAnExtractionCannotRevokeAVerdict(): void {
		// The one way this repair could hide something: an unshare of a file that
		// really is corrupt is a done row too. Such a row never reaches the map,
		// which is what this asserts from the caller's side.
		$revocable = QueueService::revocableFileIds([7_777], [], [], []);

		self::assertSame([], $revocable);
	}

	public function testTheExtractionKindsAreContentAndOcrAndNothingElse(): void {
		// The four exclusions are the payload of the constant, so they are
		// pinned here: acl writes permissions, metadata rewrites an etag, embed
		// reports done without any text, and delete is the opposite of a
		// success. A fifth kind added to this list has to be a decision.
		$kinds = (new \ReflectionClass(QueueService::class))->getConstant('EXTRACTION_KINDS');

		self::assertSame([QueueMapper::KIND_CONTENT, QueueMapper::KIND_OCR], $kinds);
	}

	// -- 4. an unresolvable id is answered with "not yet" ---------------------

	public function testARowWhoseFileIdIsGoneIsSkippedAndNotGuessed(): void {
		// The row whose lock expired and that somebody else finished: the
		// connection between queue id and file id went with it. The redelivery
		// reports the file again and the next acknowledgement revokes it.
		$revocable = QueueService::revocableFileIds(
			[self::REPAIRED_ROW, 9_002],
			[9_002 => 184],
			[],
			[],
		);

		self::assertSame([184], $revocable);
	}

	public function testAFileIdOfZeroIsNotARevocation(): void {
		// A defective mapping must not turn into a delete over file_id 0.
		$revocable = QueueService::revocableFileIds(
			[self::REPAIRED_ROW],
			[self::REPAIRED_ROW => 0],
			[],
			[],
		);

		self::assertSame([], $revocable);
	}
}
