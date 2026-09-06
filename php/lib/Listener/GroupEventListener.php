<?php

declare(strict_types=1);

namespace OCA\Findling\Listener;

use OCA\Findling\BackgroundJobs\SubtreeExpandJob;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\StorageService;
use OCP\BackgroundJob\IJobList;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Config\IMountProviderCollection;
use OCP\Group\Events\UserAddedEvent;
use OCP\Group\Events\UserRemovedEvent;
use OCP\IGroup;
use OCP\IUser;
use Psr\Log\LoggerInterface;

/**
 * A membership change, on the same one way into the queue as everything else.
 *
 * **What a group change is.** It is a change to the set of people who may find
 * something, while not a single file moved: the bytes are the same bytes, the
 * name is the same name, the folder sits where it sat. In that respect it is
 * exactly what a share is, which is why it becomes kind 'acl' work here and
 * costs the container one declarative write of the permission table and not a
 * byte over the network. Being that cheap it is handed out before any content
 * job (D-04), so the effect is visible even while a long OCR backlog is being
 * worked off.
 *
 * **Why no share event carries it.** ShareEventListener subscribes to
 * ShareCreatedEvent, ShareDeletedEvent and ShareDeletedFromSelfEvent, and none
 * of the three fires when somebody joins or leaves a group, because the share
 * itself did not change. The events for that live in OCP\Group\Events, which is
 * a different namespace and therefore a different listener. This is the finding
 * DI-05-11 of phase 5 describes and the owner decided to fix in E-H3.
 *
 * **Why the ETag reconcile does not carry it either.** The reconcile compares
 * etags and acts on the ones that changed. A membership does not touch an etag
 * of anything, so the reconcile walks past every affected file without seeing a
 * reason to do anything. What used to carry the case was the next crawl pass,
 * which rewrites the access list of everything it walks: correct, and up to a
 * full crawl cadence late. A new colleague who searches on their first morning
 * and finds nothing is the zero config promise breaking in the one place where
 * nobody can tell them why.
 *
 * **What a delay here costs, and what it does not.** Nothing leaks while an acl
 * row waits, in either direction. A hit only becomes a snippet after the recheck
 * in Provider, and that recheck resolves the file through
 * getUserFolder()->getFirstNodeById(), so a user who left a group sees nothing
 * whatever the prefilter still holds. A stale prefilter costs result quality and
 * compute time, not confidentiality. That sentence stands in ShareEventListener
 * for the share case and it stands here unchanged for the group case: this is a
 * fix for the zero config promise and not a security fix.
 *
 * **Why both directions run down the same path.** The prefilter can go stale in
 * either direction, so the join and the departure ask the same question, namely
 * what the access list of these files has to say now. The job carries the target
 * state and never a delta, so there is nothing for the listener to decide.
 *
 * **Which mounts a group change is about, and why two probes.** A membership
 * change is the difference between two states, and no single account holds both
 * sides of it. The user holds the state after the change: right after a join
 * their live mount list contains the new Team Folder, which is what makes the
 * join case work even when the joining user is the first member the group ever
 * had. A member who stays holds what the group grants regardless of the change,
 * which is what makes the departure case work, because the account that just
 * left no longer reaches the folder it lost. Both probes are asked live, through
 * IMountProviderCollection, and not through the mount cache: the cache is
 * written when a filesystem is set up and therefore holds the state of the last
 * login rather than the state of this second, which is exactly the sort of
 * staleness this listener exists to remove.
 *
 * The union of the two answers contains the mount the change was about,
 * whichever way it went. It can contain more than that, namely the other Team
 * Folders of whichever accounts were probed, and that over approximation is
 * deliberate: an extra acl subtree costs a permission rewrite of files that
 * already had the right permissions, and the alternative would be a second,
 * drifting model of what a group grants.
 *
 * **What this listener deliberately does not cover: an ordinary share held by a
 * group.** A folder shared with a group reaches its members through the mount
 * provider of files_sharing, not through the one of Team Folders, and the root
 * of such a mount can be a single file rather than a folder, which the band
 * chain below has no case for. That half of DI-05-11 stays with the crawl pass
 * and is written down as a deferred item rather than left behind a listener list
 * that looks complete. Team Folders are the case the finding names, the case the
 * parity scenario measures, and the case a small organisation actually has.
 *
 * **The last member leaving is a no-op on purpose.** Once nobody is in the group
 * any more, neither probe returns the mount, so nothing is planned. There is
 * nobody left who could find the folder through this group, so the prefilter row
 * that stays behind costs the result quality of nobody, and the next crawl pass
 * rewrites it anyway.
 *
 * Nothing here logs a path, a file name or a user id, only counters and the type
 * name of an error. A log line is the one place where the content of a private
 * instance leaves the permission model, and a group event is made entirely of
 * names.
 *
 * @template-implements \OCP\EventDispatcher\IEventListener<Event>
 */
class GroupEventListener implements IEventListener {
	/**
	 * The mount providers a group membership can hand out.
	 *
	 * One entry, and the class name is written out as a string rather than
	 * referenced, for the reason the trash bin events are written out in
	 * Application.php: the groupfolders app may not be installed at all, and a
	 * string is compared without anything having to load a class. The identical
	 * constant lives privately in StorageService, where it decides what the crawl
	 * walks; both are the same decision and both carry the same spelling. If a
	 * Team Folder mount ever stopped coming from this provider, the crawl would
	 * stop seeing it in the same breath as this listener, so the two cannot drift
	 * apart quietly.
	 *
	 * @var list<class-string>
	 */
	private const GROUP_MOUNT_PROVIDERS = [
		'OCA\GroupFolders\Mount\MountProvider',
	];

	/**
	 * How many members of the group are asked for the second probe.
	 *
	 * Two rather than one, because the first account a group returns may be the
	 * very account this event is about: on a join that account is a member by the
	 * time the event fires, and probing it twice would leave the second question
	 * unasked. Two guarantees one answer from somebody else if somebody else
	 * exists.
	 *
	 * Not "all members", and that is the difference between a listener and an
	 * outage: a group with ten thousand accounts would otherwise mean ten
	 * thousand live mount resolutions inside the click of an administrator, and
	 * every one of them would answer with the same Team Folders as the first.
	 */
	private const PROBE_LIMIT = 2;

	public function __construct(
		private IMountProviderCollection $mountProviders,
		private StorageService $storageService,
		private IJobList $jobList,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * One guard around everything, for the reason the two other listeners state:
	 * this method runs inside the administrator's action, so an exception
	 * escaping it turns a successful group change into a failed one. The worst
	 * case of swallowing it is a prefilter that stays stale until the next crawl
	 * pass repairs it, which is precisely the state this listener improves on and
	 * never worse than it.
	 */
	public function handle(Event $event): void {
		try {
			// The two events are one branch, because the answer to both of them
			// is the same: whoever may see these files now is what the prefilter
			// has to hold. Which direction the membership moved does not matter,
			// since the job carries the target state and never a delta.
			if ($event instanceof UserAddedEvent) {
				$this->refresh($event->getGroup(), $event->getUser());
				return;
			}

			if ($event instanceof UserRemovedEvent) {
				$this->refresh($event->getGroup(), $event->getUser());
				return;
			}
		} catch (\Throwable $e) {
			// The type name and nothing else. The message of a group exception
			// carries the group name and usually the account it was about.
			$this->logger->warning('Findling: a group event could not be turned into queued work', [
				'error' => get_class($e),
			]);
		}
	}

	/**
	 * Write the permission change of one membership into the work stock.
	 *
	 * One job per mount and never a row per file, which is the whole of
	 * T-06.1-32: a Team Folder with ten thousand documents would otherwise be ten
	 * thousand inserts inside the click on "Add to group".
	 */
	private function refresh(IGroup $group, IUser $user): void {
		$mounts = $this->mountsOfGroup($group, $user);

		foreach ($mounts as $mount) {
			$this->expand($mount['storage_id'], $mount['root_id']);
		}

		// Counters only. How many mounts a group change touched is enough to
		// follow one, and the group name, the account and the folder are all
		// content of a private instance.
		$this->logger->debug('Findling: planned the permission refresh of a group change', [
			'mounts' => count($mounts),
		]);
	}

	/**
	 * The mounts a membership in this group hands out, from the two live probes.
	 *
	 * Keyed by storage and root, so a mount both probes report is planned once.
	 * The class docblock has the reasoning for the pair; what matters here is
	 * that both answers come from the mount providers themselves and not from the
	 * mount cache.
	 *
	 * @return array<string, array{storage_id: int, root_id: int}>
	 */
	private function mountsOfGroup(IGroup $group, IUser $user): array {
		$mounts = [];

		// The state after the change, as the account it happened to sees it.
		$this->collect($mounts, $user);

		// What the group grants, as an account that is unaffected by the change
		// sees it. searchUsers with an empty needle is "any member", and the
		// account this event is about is skipped because it answers the first
		// question and not this one.
		foreach ($group->searchUsers('', self::PROBE_LIMIT) as $member) {
			if ($member->getUID() === $user->getUID()) {
				continue;
			}

			$this->collect($mounts, $member);
			break;
		}

		return $mounts;
	}

	/**
	 * Add the Team Folder mounts of one account to the map.
	 *
	 * The mount question the file listener and the share listener both ask,
	 * against the same source the crawl walks. Without it a group change on an
	 * instance where Team Folders are switched off (ADM-04, D-08) would pull
	 * mounts into the prefilter that the crawl was told to leave alone.
	 *
	 * @param array<string, array{storage_id: int, root_id: int}> $mounts
	 */
	private function collect(array &$mounts, IUser $user): void {
		foreach ($this->mountProviders->getUserMountsForProviderClasses($user, self::GROUP_MOUNT_PROVIDERS) as $mount) {
			$storageId = (int)$mount->getNumericStorageId();
			$rootId = (int)$mount->getStorageRootId();
			if ($storageId <= 0 || $rootId <= 0) {
				// A mount whose storage or root cannot be resolved would hand the
				// expansion job an argument it refuses with a warning, so it is
				// dropped one step earlier and in silence.
				continue;
			}

			if (!$this->storageService->isIndexedStorage($storageId)) {
				continue;
			}

			$mounts[$storageId . ':' . $rootId] = [
				'storage_id' => $storageId,
				'root_id' => $rootId,
			];
		}
	}

	/**
	 * One mount, planned rather than done.
	 *
	 * The same shape a folder share takes: one event stands for every descendant,
	 * so the work is unbounded by definition and must not happen inside the
	 * request that raised the event. The job resolves the subtree in bands, keeps
	 * its cursor in its own argument and plans its successor.
	 *
	 * The ancestor is the root of the mount, because a membership is a statement
	 * about the whole Team Folder and not about a node inside it.
	 *
	 * IJobList::add deduplicates over the argument, so two people joining the
	 * same group before the job ran leave one job and not two.
	 */
	private function expand(int $storageId, int $rootId): void {
		$this->jobList->add(SubtreeExpandJob::class, [
			'storage_id' => $storageId,
			'root_id' => $rootId,
			'ancestor_id' => $rootId,
			'kind' => QueueMapper::KIND_ACL,
			'last_file_id' => 0,
		]);
	}
}
