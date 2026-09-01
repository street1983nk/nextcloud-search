<?php

declare(strict_types=1);

namespace OCA\Findling\Listener;

use OCA\Findling\BackgroundJobs\SubtreeExpandJob;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\StorageService;
use OCP\BackgroundJob\IJobList;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Share\Events\ShareCreatedEvent;
use OCP\Share\Events\ShareDeletedEvent;
use OCP\Share\Events\ShareDeletedFromSelfEvent;
use OCP\Share\IShare;
use Psr\Log\LoggerInterface;

/**
 * Sharing and unsharing, on the same one way into the queue as everything else.
 *
 * A share changes who may find a file, and nothing else: the bytes are the same
 * bytes, the name is the same name. That is why these events become kind 'acl'
 * rows, which cost the container one declarative write of the permission table
 * and not a single byte over the network. Because they are that cheap they are
 * handed out before any content job (D-04), so their effect is visible even
 * while a long OCR backlog is being worked off.
 *
 * **What a delay here costs, and what it does not.** Nothing leaks while an acl
 * row waits. A hit only becomes a snippet after the recheck in Provider, and
 * that recheck resolves the file through getUserFolder()->getFirstNodeById(),
 * so a user who lost a share sees nothing whatever the prefilter still holds. A
 * stale prefilter costs result quality and compute time, not confidentiality.
 * The sentence stands here because both other readings are wrong: treating this
 * as a security control invites panic, and treating it as cosmetics invites a
 * latency nobody measures.
 *
 * **A folder share is one event over a whole subtree.** It is not queued as a
 * row but planned as a SubtreeExpandJob, which resolves the descendants in
 * bands. A folder with ten thousand documents would otherwise be ten thousand
 * inserts inside the user's click on "Share".
 *
 * **What this listener deliberately does not cover: group membership.** A user
 * who joins a group that holds a share gains access without any share event
 * being raised, because the share itself did not change. The event for that
 * lives outside OCP\Share\Events, and the ETag reconcile of plan 03-12 carries
 * the case on its next pass. This boundary is named here so that it stays a
 * decision instead of turning into a gap behind a listener list that looks
 * complete.
 *
 * Nothing here logs a path, a file name or a user id, only the type name of an
 * error. A log line is the one place where the content of a private instance
 * leaves the permission model, and a share event is made entirely of names.
 *
 * @template-implements \OCP\EventDispatcher\IEventListener<Event>
 */
class ShareEventListener implements IEventListener {
	public function __construct(
		private QueueService $queueService,
		private StorageService $storageService,
		private IJobList $jobList,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * One guard around everything, for the reason the file listener states: this
	 * method runs inside the user's action, so an exception escaping it turns a
	 * successful share into a failed one. The worst case of swallowing it is a
	 * prefilter that stays stale until the reconcile of plan 03-12 repairs it.
	 */
	public function handle(Event $event): void {
		try {
			// The three events are one branch, because the answer to all of them
			// is the same: whoever may see this node now is what the prefilter has
			// to hold. Which direction the change went does not matter, since the
			// job carries the target state and never a delta.
			//
			// ShareDeletedFromSelfEvent is the recipient removing a share from
			// their own view rather than the owner withdrawing it. It is a
			// separate class in Nextcloud and it has to be a separate line here,
			// otherwise exactly that user keeps getting the file offered.
			if ($event instanceof ShareCreatedEvent) {
				$this->refresh($event->getShare());
				return;
			}

			if ($event instanceof ShareDeletedEvent) {
				$this->refresh($event->getShare());
				return;
			}

			if ($event instanceof ShareDeletedFromSelfEvent) {
				$this->refresh($event->getShare());
				return;
			}
		} catch (\Throwable $e) {
			// The type name and nothing else. The message of a share exception
			// carries the path of the shared node and often the recipient.
			$this->logger->warning('Findling: a share event could not be turned into queued work', [
				'error' => get_class($e),
			]);
		}
	}

	/**
	 * Write the permission change of one share into the work stock.
	 *
	 * getNode() throws when the node behind the share cannot be resolved any
	 * more, which happens when the file was deleted in the same breath. The
	 * caller catches it: a deletion has its own event and its own kind, so there
	 * is nothing for this listener to add in that case.
	 */
	private function refresh(IShare $share): void {
		$node = $share->getNode();

		$fileId = (int)$node->getId();
		if ($fileId <= 0) {
			// A node whose id is not usable cannot be acknowledged later and would
			// sit in the queue forever. The reconcile finds the file again.
			return;
		}

		$mount = $node->getMountPoint();
		$storageId = (int)$mount->getNumericStorageId();
		$rootId = (int)$mount->getStorageRootId();
		if ($storageId <= 0 || $rootId <= 0) {
			return;
		}

		// The same mount question the file listener asks, against the same source
		// the crawl walks. Without it a share on external storage would pull a
		// mount into the prefilter that IDX-01 leaves out of the index entirely.
		if (!$this->storageService->isIndexedStorage($storageId)) {
			return;
		}

		if ($node instanceof Folder) {
			$this->expand($fileId, $storageId, $rootId);
			return;
		}

		if (!$node instanceof File) {
			return;
		}

		// The document allowlist, and it applies here because a file that is never
		// indexed needs no prefilter row either. This is the opposite of the
		// deletion case, where the allowlist is skipped on purpose: the list
		// decides what gets into the index, and a permission change is a statement
		// about something that is in it.
		if (!in_array($node->getMimetype(), StorageService::ALLOWED_MIMETYPES, true)) {
			return;
		}

		$this->queue($fileId, $storageId, $rootId);
	}

	/**
	 * A folder share, planned rather than done.
	 *
	 * One event stands for every descendant, so the work is unbounded by
	 * definition and must not happen inside the request that raised the event.
	 * The job resolves the subtree in bands, keeps its cursor in its own
	 * argument and plans its successor, which is the same shape the crawl has.
	 *
	 * IJobList::add deduplicates over the argument, so sharing the same folder
	 * twice before the job ran leaves one job and not two.
	 */
	private function expand(int $fileId, int $storageId, int $rootId): void {
		$this->jobList->add(SubtreeExpandJob::class, [
			'storage_id' => $storageId,
			'root_id' => $rootId,
			'ancestor_id' => $fileId,
			'kind' => QueueMapper::KIND_ACL,
			'last_file_id' => 0,
		]);
	}

	/**
	 * One file, as the cheapest kind there is.
	 *
	 * The size is zero because a permission change moves no bytes and must not
	 * take a share of the byte budget a claim spends; the same reasoning the
	 * deletion follows. isUpdate is true because whatever the container holds for
	 * this file, it holds it from before the share.
	 *
	 * An acl row never downgrades a row that is already waiting: KIND_RANK in
	 * QueueMapper keeps the more expensive kind, and a content job writes the
	 * permissions anyway, on the fast path included since bug audit M1 was closed.
	 * So the two kinds cannot lose each other's work whichever order they arrive in.
	 */
	private function queue(int $fileId, int $storageId, int $rootId): void {
		$this->queueService->enqueueFile($fileId, $storageId, $rootId, 0, true, QueueMapper::KIND_ACL);
	}
}
