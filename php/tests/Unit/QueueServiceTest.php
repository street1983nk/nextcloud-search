<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\ReaderContext;
use OCA\Findling\Service\StorageService;
use OCP\BackgroundJob\IJobList;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\IRootFolder;
use OCP\IAppConfig;
use OCP\IDBConnection;
use OCP\IUserManager;
use OCP\IUserSession;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

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

	// -- 5. the lanes of a claim (PAR-01) -------------------------------------

	/**
	 * The kinds a claim asks the mapper for, in the order it asks.
	 *
	 * The mapper answers every kind with an empty batch, so nothing is charged
	 * against either ceiling and the loop visits every kind the lane allows.
	 * That is exactly the question: which kinds the lane lets through, and in
	 * which order.
	 *
	 * @return list<string>
	 */
	private function kindsAskedFor(?string $lane): array {
		return array_keys($this->limitsAskedFor($lane, 32));
	}

	/**
	 * The row limit a claim hands the mapper for every kind, in the order it
	 * asks (D-26-14).
	 *
	 * Same empty mapper as above, so the claim ceiling $limit is never spent
	 * and every kind sees min(its own ceiling, $limit).
	 *
	 * @return array<string, int> kind to the limit asked for
	 */
	private function limitsAskedFor(?string $lane, int $limit): array {
		$asked = [];
		$mapper = $this->createMock(QueueMapper::class);
		$mapper->method('claimBatch')->willReturnCallback(
			static function (int $limit, int $maxBytes, string $kind) use (&$asked): array {
				$asked[$kind] = $limit;
				return [];
			},
		);

		// ExclusionService is final and built for real over an empty app config,
		// the same way QueueServiceReaderTest builds it.
		$storageService = $this->createMock(StorageService::class);
		$service = new QueueService(
			$mapper,
			$this->createMock(FileStateService::class),
			new ExclusionService(
				$this->createMock(IAppConfig::class),
				$storageService,
				$this->createMock(IJobList::class),
				$this->createMock(LoggerInterface::class),
			),
			$storageService,
			$this->createMock(IUserMountCache::class),
			$this->createMock(IRootFolder::class),
			$this->createMock(IDBConnection::class),
			$this->createMock(LoggerInterface::class),
			new ReaderContext($this->createMock(IUserSession::class), $this->createMock(IUserManager::class)),
		);

		if ($lane === null) {
			$service->claim($limit, 67_108_864);
		} else {
			$service->claim($limit, 67_108_864, $lane);
		}

		return $asked;
	}

	public function testTheEmbedLaneAsksForEmbedRowsOnly(): void {
		self::assertSame([QueueMapper::KIND_EMBED], $this->kindsAskedFor(QueueService::LANE_EMBED));
	}

	public function testTheIndexLaneNeverAsksForEmbedRows(): void {
		$expected = array_values(array_filter(
			QueueMapper::KINDS,
			static fn (string $kind): bool => $kind !== QueueMapper::KIND_EMBED,
		));

		self::assertSame($expected, $this->kindsAskedFor(QueueService::LANE_INDEX));
	}

	public function testTheAllLaneIsTheClaimOfOnePointThree(): void {
		// Default all behaves like 1.3: every kind, in the order of KINDS, and
		// the same with or without the third parameter (T-25-11).
		self::assertSame(QueueMapper::KINDS, $this->kindsAskedFor(QueueService::LANE_ALL));
		self::assertSame(QueueMapper::KINDS, $this->kindsAskedFor(null));
	}

	public function testTheLanesAreAClosedSetOfThree(): void {
		self::assertSame(['all', 'index', 'embed'], QueueService::LANES);
	}

	// -- 6. the OCR ceiling per lane (D-26-05, D-26-14) -----------------------

	public function testTheIndexLaneAsksForUpToThirtyTwoOcrRows(): void {
		// Two rows for each of at most sixteen OCR slots of a 1.4 container.
		$asked = $this->limitsAskedFor(QueueService::LANE_INDEX, 64);

		self::assertSame(32, $asked[QueueMapper::KIND_OCR]);
	}

	public function testTheAllLaneStillAsksForTwoOcrRows(): void {
		// A 1.3 container only knows the lane all and runs one OCR worker; it
		// must never receive thirty two OCR rows at once (T-26-06).
		self::assertSame(2, $this->limitsAskedFor(QueueService::LANE_ALL, 64)[QueueMapper::KIND_OCR]);
		self::assertSame(2, $this->limitsAskedFor(null, 64)[QueueMapper::KIND_OCR]);
	}

	public function testTheEmbedLaneIsUntouched(): void {
		self::assertSame(
			[QueueMapper::KIND_EMBED => 8],
			$this->limitsAskedFor(QueueService::LANE_EMBED, 64),
		);
	}

	public function testTheOtherKindsKeepTheirCeilingInTheIndexLane(): void {
		// A claim ceiling above every per kind value, so each kind shows its own.
		self::assertSame(
			[
				QueueMapper::KIND_ACL => 128,
				QueueMapper::KIND_DELETE => 128,
				QueueMapper::KIND_METADATA => 64,
				QueueMapper::KIND_CONTENT => 32,
				QueueMapper::KIND_OCR => 32,
			],
			$this->limitsAskedFor(QueueService::LANE_INDEX, 256),
		);
	}

	public function testTheOcrCeilingOfTheIndexLaneStillYieldsToTheClaimCeiling(): void {
		// min(..., $rows) stays: a small claim is not inflated to thirty two.
		self::assertSame(16, $this->limitsAskedFor(QueueService::LANE_INDEX, 16)[QueueMapper::KIND_OCR]);
	}
}
