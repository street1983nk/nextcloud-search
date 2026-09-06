<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\BackgroundJobs\SubtreeExpandJob;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Listener\GroupEventListener;
use OCA\Findling\Service\StorageService;
use OCP\BackgroundJob\IJobList;
use OCP\EventDispatcher\Event;
use OCP\Files\Config\IMountProviderCollection;
use OCP\Files\Mount\IMountPoint;
use OCP\Group\Events\UserAddedEvent;
use OCP\Group\Events\UserRemovedEvent;
use OCP\IGroup;
use OCP\IUser;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The six behaviours of the group listener, the fix E-H3 decided for DI-05-11.
 *
 * What they defend, in one sentence, because the test names below say what holds
 * and not why: a membership change moves nobody's bytes and changes everybody's
 * access, so the one honest answer to it is acl work over the mounts the group
 * hands out, planned in bands, and never a single download and never one insert
 * per file.
 *
 * Everything below runs on mocks. No database, no file system, no group backend:
 * the mount providers, the mount points, the group, the accounts and the job
 * list are all doubles, and that is what makes these statements about the code
 * rather than about an instance.
 *
 * The two probes of the listener are visible in every fixture here, and they are
 * the reason the mount provider double answers per account rather than once: the
 * account the event is about holds the state after the change and a member who
 * stays holds what the group grants, and each of the two cases below rests on a
 * different one of the two.
 */
#[CoversClass(GroupEventListener::class)]
final class GroupEventListenerTest extends TestCase {
	/**
	 * The account the events below are about. A recognisable string on purpose:
	 * the log case at the end of this file looks for it.
	 */
	private const AFFECTED_UID = 'newcomer';

	/** The member who stays in the group and answers the second probe. */
	private const REMAINING_UID = 'oldhand';

	/** The group id, recognisable for the same reason the uid is. */
	private const GROUP_ID = 'team-of-the-second-floor';

	private IMountProviderCollection&MockObject $mountProviders;
	private StorageService&MockObject $storageService;
	private IJobList&MockObject $jobList;
	private LoggerInterface&MockObject $logger;

	/**
	 * Every job the listener planned, in order.
	 *
	 * @var list<array{class: string, argument: array<string, mixed>}>
	 */
	private array $planned = [];

	/**
	 * Every log line the listener wrote, in order.
	 *
	 * @var list<array{level: string, message: string, context: array<string, mixed>}>
	 */
	private array $logLines = [];

	protected function setUp(): void {
		parent::setUp();

		$this->mountProviders = $this->createMock(IMountProviderCollection::class);
		$this->storageService = $this->createMock(StorageService::class);
		$this->jobList = $this->createMock(IJobList::class);
		$this->logger = $this->createMock(LoggerInterface::class);

		$this->planned = [];
		$this->logLines = [];

		$this->jobList->method('add')->willReturnCallback(
			function (string $class, mixed $argument): void {
				$this->planned[] = [
					'class' => $class,
					'argument' => is_array($argument) ? $argument : [],
				];
			},
		);

		// Every level, because "no log line carries a path" is a statement about
		// all of them and not about the two the listener happens to use today.
		foreach (['emergency', 'alert', 'critical', 'error', 'warning', 'notice', 'info', 'debug'] as $level) {
			$this->logger->method($level)->willReturnCallback(
				function (string|\Stringable $message, array $context = []) use ($level): void {
					$this->logLines[] = [
						'level' => $level,
						'message' => (string)$message,
						'context' => $context,
					];
				},
			);
		}

		// Unless a case says otherwise every storage the doubles hand out is one
		// this app indexes. The case that says otherwise is further down.
		$this->storageService->method('isIndexedStorage')->willReturn(true);
	}

	private function listener(): GroupEventListener {
		return new GroupEventListener(
			$this->mountProviders,
			$this->storageService,
			$this->jobList,
			$this->logger,
		);
	}

	private function user(string $uid): IUser&MockObject {
		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn($uid);

		return $user;
	}

	/**
	 * A group whose member list is exactly the accounts handed in.
	 *
	 * @param list<IUser> $members
	 */
	private function group(array $members): IGroup&MockObject {
		$group = $this->createMock(IGroup::class);
		$group->method('getGID')->willReturn(self::GROUP_ID);
		$group->method('searchUsers')->willReturnCallback(
			static fn (string $search, ?int $limit = null): array => $limit === null
				? $members
				: array_slice($members, 0, $limit),
		);

		return $group;
	}

	private function mount(int $storageId, int $rootId): IMountPoint&MockObject {
		$mount = $this->createMock(IMountPoint::class);
		$mount->method('getNumericStorageId')->willReturn($storageId);
		$mount->method('getStorageRootId')->willReturn($rootId);

		return $mount;
	}

	/**
	 * What the live mount providers answer, per account.
	 *
	 * @param array<string, list<IMountPoint>> $byUid
	 */
	private function mountsPerAccount(array $byUid): void {
		$this->mountProviders->method('getUserMountsForProviderClasses')->willReturnCallback(
			static fn (IUser $user, array $classes): array => $byUid[$user->getUID()] ?? [],
		);
	}

	// -- behaviour 1: a join reaches the prefilter at once --------------------

	public function testAJoinPlansThePermissionRefreshOfTheGroupsMounts(): void {
		$affected = $this->user(self::AFFECTED_UID);
		$this->mountsPerAccount([self::AFFECTED_UID => [$this->mount(7, 4711)]]);

		$this->listener()->handle(new UserAddedEvent($this->group([$affected]), $affected));

		self::assertCount(1, $this->planned, 'a join has to plan the refresh of the mount it granted');
		self::assertSame(SubtreeExpandJob::class, $this->planned[0]['class']);
		self::assertSame(7, $this->planned[0]['argument']['storage_id']);
		self::assertSame(4711, $this->planned[0]['argument']['root_id']);
		self::assertSame(4711, $this->planned[0]['argument']['ancestor_id']);
	}

	/**
	 * The case the second probe exists for, and the one the first probe cannot
	 * answer: the account is out of the group by the time the event fires, so its
	 * own live mount list no longer contains the folder it just lost.
	 */
	public function testADepartureIsPlannedThroughAMemberWhoStayed(): void {
		$affected = $this->user(self::AFFECTED_UID);
		$remaining = $this->user(self::REMAINING_UID);
		$this->mountsPerAccount([
			self::AFFECTED_UID => [],
			self::REMAINING_UID => [$this->mount(7, 4711)],
		]);

		$this->listener()->handle(new UserRemovedEvent($this->group([$remaining]), $affected));

		self::assertCount(1, $this->planned, 'a departure has to plan the refresh of the mount it withdrew');
		self::assertSame(4711, $this->planned[0]['argument']['ancestor_id']);
	}

	/**
	 * The first probe on its own, for the case the second one cannot answer: the
	 * account that joins is the first member the group ever had, so there is
	 * nobody else to ask.
	 */
	public function testAJoinIsPlannedEvenWhenTheJoiningAccountIsTheOnlyMember(): void {
		$affected = $this->user(self::AFFECTED_UID);
		$this->mountsPerAccount([self::AFFECTED_UID => [$this->mount(9, 88)]]);

		$this->listener()->handle(new UserAddedEvent($this->group([$affected]), $affected));

		self::assertCount(1, $this->planned);
		self::assertSame(88, $this->planned[0]['argument']['ancestor_id']);
	}

	// -- behaviour 2: both directions run down the same path ------------------

	/**
	 * @return array<string, array{class-string}>
	 */
	public static function bothDirections(): array {
		return [
			'a join' => [UserAddedEvent::class],
			'a departure' => [UserRemovedEvent::class],
		];
	}

	#[DataProvider('bothDirections')]
	public function testBothDirectionsPlanTheSameKindOfWork(string $eventClass): void {
		$affected = $this->user(self::AFFECTED_UID);
		$remaining = $this->user(self::REMAINING_UID);
		$this->mountsPerAccount([
			self::AFFECTED_UID => [$this->mount(7, 4711)],
			self::REMAINING_UID => [$this->mount(7, 4711)],
		]);

		/** @var Event $event */
		$event = new $eventClass($this->group([$remaining, $affected]), $affected);
		$this->listener()->handle($event);

		self::assertCount(1, $this->planned);
		self::assertSame(QueueMapper::KIND_ACL, $this->planned[0]['argument']['kind']);
	}

	// -- behaviour 3: a change without a mount is a no-op ---------------------

	public function testAGroupChangeWithoutASingleMountPlansNothingAndDoesNotThrow(): void {
		$affected = $this->user(self::AFFECTED_UID);
		$remaining = $this->user(self::REMAINING_UID);
		$this->mountsPerAccount([self::AFFECTED_UID => [], self::REMAINING_UID => []]);

		$this->listener()->handle(new UserAddedEvent($this->group([$remaining, $affected]), $affected));

		self::assertSame([], $this->planned, 'a group without a team folder has nothing to refresh');
	}

	public function testAMountOnAStorageThisAppDoesNotIndexIsSkipped(): void {
		$affected = $this->user(self::AFFECTED_UID);
		$this->mountsPerAccount([self::AFFECTED_UID => [$this->mount(7, 4711)]]);

		// A fresh double, because the one from setUp already answers true and the
		// switches of ADM-04 are exactly what this case is about.
		$this->storageService = $this->createMock(StorageService::class);
		$this->storageService->method('isIndexedStorage')->willReturn(false);

		$this->listener()->handle(new UserAddedEvent($this->group([$affected]), $affected));

		self::assertSame([], $this->planned, 'a mount the crawl was told to leave alone must not reach the queue');
	}

	/**
	 * @return array<string, array{int, int}>
	 */
	public static function unusableMounts(): array {
		return [
			'no numeric storage id' => [0, 4711],
			'a negative storage id' => [-1, 4711],
			'no storage root' => [7, 0],
			'a negative root' => [7, -1],
		];
	}

	#[DataProvider('unusableMounts')]
	public function testAMountWithoutAUsableStorageOrRootIsSkipped(int $storageId, int $rootId): void {
		$affected = $this->user(self::AFFECTED_UID);
		$this->mountsPerAccount([self::AFFECTED_UID => [$this->mount($storageId, $rootId)]]);

		$this->listener()->handle(new UserAddedEvent($this->group([$affected]), $affected));

		self::assertSame([], $this->planned, 'an argument the expansion job refuses must not be planned at all');
	}

	// -- behaviour 4: acl work only, never a download -------------------------

	/**
	 * The kind is the whole statement. Any other kind of the queue would make the
	 * container fetch bytes for files whose bytes did not change, which is the
	 * one thing a membership change must never cost.
	 */
	public function testTheOnlyWorkAGroupChangeCreatesIsAclWork(): void {
		$affected = $this->user(self::AFFECTED_UID);
		$this->mountsPerAccount([self::AFFECTED_UID => [$this->mount(7, 4711), $this->mount(8, 99)]]);

		$this->listener()->handle(new UserAddedEvent($this->group([$affected]), $affected));

		self::assertCount(2, $this->planned);
		foreach ($this->planned as $job) {
			self::assertSame(QueueMapper::KIND_ACL, $job['argument']['kind']);
			self::assertNotSame(QueueMapper::KIND_CONTENT, $job['argument']['kind']);
			self::assertNotSame(QueueMapper::KIND_OCR, $job['argument']['kind']);
			self::assertNotSame(QueueMapper::KIND_EMBED, $job['argument']['kind']);
			self::assertNotSame(QueueMapper::KIND_METADATA, $job['argument']['kind']);
		}
	}

	// -- behaviour 5: bands, never one insert per file ------------------------

	/**
	 * A Team Folder with ten thousand documents is one job and not ten thousand
	 * rows, which is T-06.1-32. The listener never learns how many files are
	 * behind the mount, and that is the point of the assertion: whatever the
	 * folder holds, the click of the administrator pays for one entry in the job
	 * list, and the band chain of SubtreeExpandJob pays for the rest.
	 */
	public function testALargeTeamFolderIsPlannedThroughTheBandChain(): void {
		$affected = $this->user(self::AFFECTED_UID);
		$remaining = $this->user(self::REMAINING_UID);
		$this->mountsPerAccount([
			self::AFFECTED_UID => [$this->mount(7, 4711)],
			self::REMAINING_UID => [$this->mount(7, 4711)],
		]);

		$this->listener()->handle(new UserAddedEvent($this->group([$remaining, $affected]), $affected));

		self::assertCount(1, $this->planned, 'one mount is one job, whatever it holds');
		self::assertSame(SubtreeExpandJob::class, $this->planned[0]['class']);
		self::assertSame(0, $this->planned[0]['argument']['last_file_id'], 'the band chain starts at the beginning of the subtree');
	}

	public function testAMountBothProbesReportIsPlannedOnce(): void {
		$affected = $this->user(self::AFFECTED_UID);
		$remaining = $this->user(self::REMAINING_UID);
		$this->mountsPerAccount([
			self::AFFECTED_UID => [$this->mount(7, 4711)],
			self::REMAINING_UID => [$this->mount(7, 4711), $this->mount(7, 4712)],
		]);

		$this->listener()->handle(new UserAddedEvent($this->group([$remaining, $affected]), $affected));

		self::assertCount(2, $this->planned, 'the shared mount is planned once and the second one as well');
		$ancestors = array_map(static fn (array $job): int => (int)$job['argument']['ancestor_id'], $this->planned);
		sort($ancestors);
		self::assertSame([4711, 4712], $ancestors);
	}

	/**
	 * The skip that keeps the second probe a second question. On a join the
	 * account the event is about is a member by the time the event fires, so the
	 * group would offer it as the first answer and the second probe would repeat
	 * the first one.
	 */
	public function testTheSecondProbeSkipsTheAccountTheEventIsAbout(): void {
		$affected = $this->user(self::AFFECTED_UID);
		$remaining = $this->user(self::REMAINING_UID);
		$this->mountsPerAccount([
			self::AFFECTED_UID => [],
			self::REMAINING_UID => [$this->mount(7, 4711)],
		]);

		// The group offers the affected account first, which is what a real group
		// backend does after an addition.
		$this->listener()->handle(new UserAddedEvent($this->group([$affected, $remaining]), $affected));

		self::assertCount(1, $this->planned, 'the member who stays has to be reached past the account that just joined');
		self::assertSame(4711, $this->planned[0]['argument']['ancestor_id']);
	}

	// -- behaviour 6: nothing identifying in a log line -----------------------

	public function testNoLogLineOfASuccessfulGroupChangeCarriesAnIdentifier(): void {
		$affected = $this->user(self::AFFECTED_UID);
		$remaining = $this->user(self::REMAINING_UID);
		$this->mountsPerAccount([
			self::AFFECTED_UID => [$this->mount(7, 4711)],
			self::REMAINING_UID => [$this->mount(7, 4711)],
		]);

		$this->listener()->handle(new UserAddedEvent($this->group([$remaining, $affected]), $affected));

		self::assertNotSame([], $this->logLines, 'a group change that planned work has to leave a trace');
		$this->assertNothingIdentifyingWasLogged();
	}

	public function testAFailingProbeIsSwallowedAndLogsNothingButATypeName(): void {
		$affected = $this->user(self::AFFECTED_UID);
		$group = $this->createMock(IGroup::class);
		$group->method('getGID')->willReturn(self::GROUP_ID);
		$group->method('searchUsers')->willThrowException(
			new \RuntimeException('the group backend is unreachable for ' . self::AFFECTED_UID . ' in ' . self::GROUP_ID),
		);
		$this->mountsPerAccount([self::AFFECTED_UID => []]);

		// No exception escapes: this runs inside the administrator's action, and
		// a group change that fails because the search index wanted a refresh
		// would be the worse outcome by a wide margin.
		$this->listener()->handle(new UserAddedEvent($group, $affected));

		self::assertSame([], $this->planned);
		self::assertCount(1, $this->logLines);
		self::assertSame('warning', $this->logLines[0]['level']);
		self::assertSame(['error' => \RuntimeException::class], $this->logLines[0]['context']);
		$this->assertNothingIdentifyingWasLogged();
	}

	public function testAnEventThisListenerIsNotAboutPlansNothing(): void {
		$this->mountsPerAccount([self::AFFECTED_UID => [$this->mount(7, 4711)]]);

		$this->listener()->handle(new Event());

		self::assertSame([], $this->planned);
		self::assertSame([], $this->logLines);
	}

	/**
	 * No account, no group and nothing that looks like a path in any log line,
	 * neither in the message nor anywhere in the context.
	 */
	private function assertNothingIdentifyingWasLogged(): void {
		foreach ($this->logLines as $line) {
			$written = $line['message'] . ' ' . json_encode($line['context'], JSON_THROW_ON_ERROR);
			foreach ([self::AFFECTED_UID, self::REMAINING_UID, self::GROUP_ID, '/files/', '.txt'] as $identifier) {
				self::assertStringNotContainsString(
					$identifier,
					$written,
					'a log line of this listener carries an identifier: ' . $written,
				);
			}
		}
	}
}
