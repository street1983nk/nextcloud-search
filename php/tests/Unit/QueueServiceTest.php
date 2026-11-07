<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Db\QueueFile;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\DocKeyService;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\ReaderContext;
use OCA\Findling\Service\StorageService;
use OCP\BackgroundJob\IJobList;
use OCP\Files\Cache\ICacheEntry;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\ICachedMountFileInfo;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\Files\Mount\IMountPoint;
use OCP\IAppConfig;
use OCP\IDBConnection;
use OCP\IUser;
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
			$this->createMock(DocKeyService::class),
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

	// -- 7. the document key of every job (plan 43-15, D-43-14) ---------------

	/** The file of the document key cases, on a storage of a SMB group. */
	private const SHARED_FILE = 5150;

	/** Its internal path, oc_filecache.path, relative to the storage root. */
	private const SHARED_INTERNAL = 'Gemeinsam/Plan.xlsx';

	/** @var list<array{string, string, array<string, mixed>}> */
	private array $logged = [];

	private ?IUser $active = null;

	/**
	 * A queue row of one kind for one file, on a real storage and root so
	 * that describe() never asks the node for its mount ids.
	 */
	private static function row(int $rowId, int $fileId, string $kind): QueueFile {
		$row = new QueueFile();
		$row->setId($rowId);
		$row->setFileId($fileId);
		$row->setStorageId(31);
		$row->setRootId(32);
		$row->setSize(100);
		$row->setRetries(1);
		$row->setKind($kind);

		return $row;
	}

	/**
	 * A claim over the given rows, read by the given world.
	 *
	 * $readers maps a file id to the members of its mount list, the first of
	 * whom reads it; $nodes maps a member to the node they reach for every
	 * file and the path relative to their home folder. The file cache answers
	 * with $internal, so the document key comes out of a real DocKeyService
	 * unless $docKeys replaces it.
	 *
	 * @param list<QueueFile> $rows
	 * @param array<int, list<string>> $readers
	 * @param array<string, array{File, string}> $nodes
	 * @param array<int, string> $internal
	 */
	private function claimWith(array $rows, array $readers, array $nodes, array $internal, ?DocKeyService $docKeys = null): array {
		$this->logged = [];
		$this->active = null;

		$mapper = $this->createMock(QueueMapper::class);
		$mapper->method('claimBatch')->willReturnCallback(
			static fn (int $limit, int $maxBytes, string $kind): array => array_values(array_filter(
				$rows,
				static fn (QueueFile $row): bool => $row->getKind() === $kind,
			)),
		);

		$mountCache = $this->createMock(IUserMountCache::class);
		$mountCache->method('getMountsForFileId')->willReturnCallback(function (int $fileId) use ($readers): array {
			$mounts = [];
			foreach ($readers[$fileId] ?? [] as $userId) {
				$user = $this->createMock(IUser::class);
				$user->method('getUID')->willReturn($userId);
				$mount = $this->createMock(ICachedMountFileInfo::class);
				$mount->method('getUser')->willReturn($user);
				$mounts[] = $mount;
			}

			return $mounts;
		});

		$folders = [];
		foreach ($nodes as $userId => [$node, $relative]) {
			$folder = $this->createMock(Folder::class);
			$folder->method('getFirstNodeById')->willReturn($node);
			$folder->method('getRelativePath')->willReturn('/' . $relative);
			$folders[$userId] = $folder;
		}
		$rootFolder = $this->createMock(IRootFolder::class);
		$rootFolder->method('getUserFolder')->willReturnCallback(static fn (string $userId): Folder => $folders[$userId]);

		if ($docKeys === null) {
			$fileAccess = $this->createMock(IFileAccess::class);
			$fileAccess->method('getByFileIds')->willReturnCallback(function (array $fileIds) use ($internal): array {
				$found = [];
				foreach ($fileIds as $fileId) {
					if (isset($internal[$fileId])) {
						$entry = $this->createMock(ICacheEntry::class);
						$entry->method('getPath')->willReturn($internal[$fileId]);
						$found[$fileId] = $entry;
					}
				}

				return $found;
			});
			$docKeys = new DocKeyService($fileAccess);
		}

		$session = $this->createMock(IUserSession::class);
		$session->method('getUser')->willReturnCallback(fn (): ?IUser => $this->active);
		$session->method('setVolatileActiveUser')->willReturnCallback(function (?IUser $user): void {
			$this->active = $user;
		});
		$userManager = $this->createMock(IUserManager::class);
		$userManager->method('get')->willReturnCallback(function (string $uid): IUser {
			$user = $this->createMock(IUser::class);
			$user->method('getUID')->willReturn($uid);

			return $user;
		});

		$logger = $this->createMock(LoggerInterface::class);
		foreach (['debug', 'info', 'notice', 'warning', 'error'] as $level) {
			$logger->method($level)->willReturnCallback(
				function (string|\Stringable $message, array $context = []) use ($level): void {
					$this->logged[] = [$level, (string)$message, $context];
				},
			);
		}

		$storageService = $this->createMock(StorageService::class);
		$service = new QueueService(
			$mapper,
			$this->createMock(FileStateService::class),
			new ExclusionService(
				$this->createMock(IAppConfig::class),
				$storageService,
				$this->createMock(IJobList::class),
				$logger,
			),
			$storageService,
			$mountCache,
			$rootFolder,
			$this->createMock(IDBConnection::class),
			$logger,
			new ReaderContext($session, $userManager),
			$docKeys,
		);

		return $service->claim(32, 67_108_864);
	}

	/**
	 * A readable file node. $internal is what getInternalPath() of THIS node
	 * answers, which for a node on a SharedMount is relative to the shared
	 * folder; $mountType is the type of its mount point.
	 */
	private function node(string $internal, string $mountType): File {
		$mount = $this->createMock(IMountPoint::class);
		$mount->method('getMountType')->willReturn($mountType);
		$mount->method('getNumericStorageId')->willReturn(31);
		$mount->method('getStorageRootId')->willReturn(32);

		$file = $this->createMock(File::class);
		$file->method('isReadable')->willReturn(true);
		$file->method('getName')->willReturn('Plan.xlsx');
		$file->method('getPath')->willReturn('/irrelevant/' . $internal);
		$file->method('getInternalPath')->willReturn($internal);
		$file->method('getMountPoint')->willReturn($mount);
		$file->method('getMimetype')->willReturn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
		$file->method('getSize')->willReturn(100);
		$file->method('getMTime')->willReturn(1_700_000_000);
		$file->method('getEtag')->willReturn('etag');

		return $file;
	}

	public function testEveryJobWithAFileCarriesTheKeyOfItsInternalPath(): void {
		$sources = $this->claimWith(
			[self::row(1, self::SHARED_FILE, QueueMapper::KIND_CONTENT)],
			[self::SHARED_FILE => ['anna']],
			['anna' => [$this->node(self::SHARED_INTERNAL, 'external'), 'Abteilung/Plan.xlsx']],
			[self::SHARED_FILE => self::SHARED_INTERNAL],
		);

		self::assertSame(DocKeyService::docKeyOf(self::SHARED_INTERNAL), $sources[1]['docKey'] ?? null);
		// The path of the reader still travels, unchanged, next to the key.
		self::assertSame('Abteilung/Plan.xlsx', $sources[1]['path'] ?? null);
	}

	public function testReaderViaSharedMountYieldsTheSameDocKeyAsTheOwner(): void {
		// The case of research A1 (b): bernd owns the SMB mount and shares the
		// folder Gemeinsam with aaron, who sorts first and becomes the reader.
		// aaron's node lives on a SharedMount, so getInternalPath() of it is
		// relative to the share ('Plan.xlsx') and the path relative to his
		// home differs as well. The key must not move.
		$owner = $this->claimWith(
			[self::row(1, self::SHARED_FILE, QueueMapper::KIND_CONTENT)],
			[self::SHARED_FILE => ['bernd']],
			['bernd' => [$this->node(self::SHARED_INTERNAL, 'external'), 'SMB/Gemeinsam/Plan.xlsx']],
			[self::SHARED_FILE => self::SHARED_INTERNAL],
		);
		$viaShare = $this->claimWith(
			[self::row(1, self::SHARED_FILE, QueueMapper::KIND_CONTENT)],
			[self::SHARED_FILE => ['aaron', 'bernd']],
			[
				'aaron' => [$this->node('Plan.xlsx', 'shared'), 'Gemeinsam/Plan.xlsx'],
				'bernd' => [$this->node(self::SHARED_INTERNAL, 'external'), 'SMB/Gemeinsam/Plan.xlsx'],
			],
			[self::SHARED_FILE => self::SHARED_INTERNAL],
		);

		self::assertSame('bernd', $owner[1]['fetchAs'] ?? null);
		self::assertSame('aaron', $viaShare[1]['fetchAs'] ?? null);
		self::assertNotSame($owner[1]['path'] ?? null, $viaShare[1]['path'] ?? null);
		self::assertSame($owner[1]['docKey'] ?? null, $viaShare[1]['docKey'] ?? null);
		self::assertSame(DocKeyService::docKeyOf(self::SHARED_INTERNAL), $viaShare[1]['docKey'] ?? null);
		self::assertNotSame(DocKeyService::docKeyOf('Plan.xlsx'), $viaShare[1]['docKey'] ?? null);
	}

	public function testTwoMountPointsOfOneGroupYieldOneKey(): void {
		// Two members of one counting key, mounted at different points: two
		// files ids, one internal path, one key.
		$sources = $this->claimWith(
			[
				self::row(1, 61, QueueMapper::KIND_CONTENT),
				self::row(2, 62, QueueMapper::KIND_CONTENT),
				self::row(3, 63, QueueMapper::KIND_CONTENT),
			],
			[61 => ['anna'], 62 => ['bernd'], 63 => ['bernd']],
			[
				'anna' => [$this->node(self::SHARED_INTERNAL, 'external'), 'Abteilung/Gemeinsam/Plan.xlsx'],
				'bernd' => [$this->node(self::SHARED_INTERNAL, 'external'), 'Projekte/SMB/Gemeinsam/Plan.xlsx'],
			],
			[61 => self::SHARED_INTERNAL, 62 => self::SHARED_INTERNAL, 63 => 'Gemeinsam/Andere.xlsx'],
		);

		self::assertSame($sources[1]['docKey'] ?? null, $sources[2]['docKey'] ?? null);
		self::assertNotSame($sources[1]['docKey'] ?? null, $sources[3]['docKey'] ?? null);
	}

	public function testTheKeysAreReadOncePerClaim(): void {
		$docKeys = $this->createMock(DocKeyService::class);
		$docKeys->expects(self::once())->method('docKeysFor')
			->with([71, 72, 73])
			->willReturn(['keys' => [71 => str_repeat('a', 64), 72 => str_repeat('b', 64), 73 => str_repeat('c', 64)], 'absent' => []]);

		$sources = $this->claimWith(
			[
				self::row(1, 71, QueueMapper::KIND_ACL),
				self::row(2, 72, QueueMapper::KIND_METADATA),
				self::row(3, 73, QueueMapper::KIND_CONTENT),
			],
			[71 => ['anna'], 72 => ['anna'], 73 => ['anna']],
			['anna' => [$this->node(self::SHARED_INTERNAL, 'home'), 'Plan.xlsx']],
			[],
			$docKeys,
		);

		// acl and metadata carry it too: a rename arrives as metadata (W4).
		self::assertSame(str_repeat('a', 64), $sources[1]['docKey'] ?? null);
		self::assertSame(str_repeat('b', 64), $sources[2]['docKey'] ?? null);
		self::assertSame(str_repeat('c', 64), $sources[3]['docKey'] ?? null);
	}

	public function testADeleteOrderCarriesNoKeyAndAsksForNone(): void {
		$docKeys = $this->createMock(DocKeyService::class);
		$docKeys->expects(self::never())->method('docKeysFor');

		$sources = $this->claimWith([self::row(1, 81, QueueMapper::KIND_DELETE)], [], [], [], $docKeys);

		self::assertSame(QueueMapper::KIND_DELETE, $sources[1]['kind'] ?? null);
		self::assertArrayNotHasKey('docKey', $sources[1]);
	}

	public function testAFileWithoutACacheRowTravelsWithoutAKey(): void {
		// The container keeps the key it holds and its backfill asks again.
		$sources = $this->claimWith(
			[self::row(1, self::SHARED_FILE, QueueMapper::KIND_CONTENT)],
			[self::SHARED_FILE => ['anna']],
			['anna' => [$this->node(self::SHARED_INTERNAL, 'external'), 'Plan.xlsx']],
			[],
		);

		self::assertArrayHasKey(1, $sources);
		self::assertArrayNotHasKey('docKey', $sources[1]);
	}

	public function testAFailingKeyLookupNeitherStopsTheClaimNorLogsAPath(): void {
		$docKeys = $this->createMock(DocKeyService::class);
		$docKeys->method('docKeysFor')->willThrowException(new \RuntimeException('SELECT path FROM oc_filecache WHERE path = Gemeinsam/Plan.xlsx'));

		$sources = $this->claimWith(
			[self::row(1, self::SHARED_FILE, QueueMapper::KIND_CONTENT)],
			[self::SHARED_FILE => ['anna']],
			['anna' => [$this->node(self::SHARED_INTERNAL, 'external'), 'Abteilung/Plan.xlsx']],
			[],
			$docKeys,
		);

		self::assertArrayHasKey(1, $sources);
		self::assertArrayNotHasKey('docKey', $sources[1]);

		$warnings = array_values(array_filter($this->logged, static fn (array $entry): bool => $entry[0] === 'warning'));
		self::assertCount(1, $warnings);
		self::assertSame(['exception', 'count'], array_keys($warnings[0][2]));
		self::assertSame(1, $warnings[0][2]['count']);
		self::assertStringNotContainsString('Plan', $warnings[0][1]);
	}

	public function testNoLogLineOfAClaimCarriesAPathOrAKey(): void {
		$sources = $this->claimWith(
			[self::row(1, self::SHARED_FILE, QueueMapper::KIND_CONTENT), self::row(2, 91, QueueMapper::KIND_CONTENT)],
			[self::SHARED_FILE => ['anna']],
			['anna' => [$this->node(self::SHARED_INTERNAL, 'external'), 'Abteilung/Plan.xlsx']],
			[self::SHARED_FILE => self::SHARED_INTERNAL],
		);

		self::assertArrayHasKey(1, $sources);
		$log = (string)json_encode(array_map(
			static fn (array $entry): array => [$entry[1], array_map(
				static fn (mixed $value): mixed => $value instanceof \Throwable ? $value->getMessage() : $value,
				$entry[2],
			)],
			$this->logged,
		));
		foreach (['Gemeinsam', 'Plan.xlsx', 'Abteilung', DocKeyService::docKeyOf(self::SHARED_INTERNAL)] as $secret) {
			self::assertStringNotContainsString($secret, $log);
		}
	}
}
