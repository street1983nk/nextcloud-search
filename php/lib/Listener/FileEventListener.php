<?php

declare(strict_types=1);

namespace OCA\Findling\Listener;

use OCA\Findling\BackgroundJobs\StorageCrawlJob;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\StorageService;
use OCA\Files_Trashbin\Events\MoveToTrashEvent;
use OCA\Files_Trashbin\Events\NodeRestoredEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeCopiedEvent;
use OCP\Files\Events\Node\NodeCreatedEvent;
use OCP\Files\Events\Node\NodeDeletedEvent;
use OCP\Files\Events\Node\NodeRenamedEvent;
use OCP\Files\Events\Node\NodeTouchedEvent;
use OCP\Files\Events\Node\NodeWrittenEvent;
use OCP\Files\File;
use OCP\Files\Node;
use Psr\Log\LoggerInterface;

/**
 * The one way a file event becomes work, and there is deliberately only one.
 *
 * The events are taken from the Nextcloud event dispatcher inside the Nextcloud
 * process, and not from the AppAPI bridge that pushes node events into an
 * ExApp. That bridge would be a second path into the same queue, which COMP-03
 * rules out in so many words; on top of that it does not carry share events at
 * all, and the Nextcloud documentation itself describes it as asynchronous and
 * "more like a notification system", which is not what an index that claims a
 * latency may be built on.
 *
 * One listener class for every node event rather than one class per event, so
 * that the number of paths into the queue is a number one can count: it is the
 * length of the list in Application::register plus the branches below.
 *
 * This path covers every way a file can be written, because OC\Files\Node\
 * HookConnector translates the old filesystem signals of View into exactly
 * these typed events, and View is what WebDAV, the desktop client, the web
 * interface and occ all write through.
 *
 * Nothing here logs a path or a file name, only counters, a storage id and the
 * type name of an error. A log line is the one place where the content of a
 * private instance leaves the permission model.
 *
 * @template-implements \OCP\EventDispatcher\IEventListener<Event>
 */
class FileEventListener implements IEventListener {
	public function __construct(
		private QueueService $queueService,
		private StorageService $storageService,
		private FileStateService $fileStateService,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * Everything in here is inside one guard, and that is not defensive
	 * programming, it is the contract of a listener: this method runs inside the
	 * user's write, so an exception escaping it turns a successful upload into a
	 * failed one. The worst case of swallowing it is one row that was not
	 * queued, and that is an up-to-dateness problem which the ETag reconcile of
	 * plan 03-12 repairs on its next pass.
	 */
	public function handle(Event $event): void {
		try {
			// isUpdate says whether the container is looking at a file it may
			// already have text for. A copy is a new file id, so its target is
			// as new as a creation, even though the bytes are not.
			if ($event instanceof NodeCreatedEvent) {
				$this->queue($event->getNode(), false);
				return;
			}

			if ($event instanceof NodeCopiedEvent) {
				// The source did not change, only the target exists now.
				$this->queue($event->getTarget(), false);
				return;
			}

			if ($event instanceof NodeWrittenEvent) {
				$this->queue($event->getNode(), true);
				return;
			}

			if ($event instanceof NodeTouchedEvent) {
				$this->queue($event->getNode(), true);
				return;
			}

			if ($event instanceof NodeRenamedEvent) {
				// Renaming and moving are the same event. The source is where the
				// node used to be, the target is what it is now, and only the
				// target carries the name and the path the index has to hold.
				$this->queueRename($event->getTarget());
				return;
			}

			if ($event instanceof NodeDeletedEvent) {
				// Queued as kind 'delete', the one job that needs no node on the
				// far side. The mimetype filter does not run for it, see queue():
				// a file that reports a different type now than it did when it
				// was indexed still has to leave the index.
				$this->queue($event->getNode(), true, QueueMapper::KIND_DELETE);
				return;
			}

			if ($event instanceof MoveToTrashEvent) {
				// D-10: for the search the trash bin is a deletion, exactly as in
				// the native Files search. A file a user threw away has to stop
				// being findable at once, and waiting for the bin to be emptied
				// would leave it in the results for another thirty days. The
				// mimetype filter is skipped here as well, for the same reason.
				//
				// This fires alongside NodeDeletedEvent for one and the same
				// operation, and that costs nothing: enqueue is idempotent over
				// the file id, so the second call refreshes the row the first one
				// wrote instead of adding a second one. Both branches are here
				// anyway, because a deletion on an instance with the trash bin
				// switched off raises only the other one.
				$this->queue($event->getNode(), true, QueueMapper::KIND_DELETE);
				return;
			}

			if ($event instanceof NodeRestoredEvent) {
				// The other direction of D-10, and it goes in as content rather
				// than as metadata. The container dropped the document out of the
				// index when the file was deleted, so there is no stored text left
				// to write again under a different name and the metadata job would
				// fall through to the content route anyway. The tombstone is what
				// makes this work at all: without it the unchanged content hash
				// would let the container acknowledge the row without writing
				// anything, and the restored file would stay lost.
				$this->queue($event->getTarget(), true);
				return;
			}
		} catch (\Throwable $e) {
			// The type name and nothing else. The message of a filesystem
			// exception carries the path of the file it failed on.
			$this->logger->warning('Findling: an event could not be turned into queued work', [
				'error' => get_class($e),
			]);
		}
	}

	/**
	 * A renamed or moved node, queued as the cheap job.
	 *
	 * A file goes in as kind 'metadata': the container reads the text back out of
	 * the index and writes the document again with the new name, without
	 * fetching a single byte. Queueing it as content instead would achieve
	 * nothing at all, because the bytes did not change and the container
	 * acknowledges an unchanged file without touching the index.
	 *
	 * A folder is deliberately not queued at all, and this is the whole reason:
	 * FIELD_PATH is written into the index but read by no query and shown by no
	 * provider, because a search result takes its title and its path from the
	 * Nextcloud node at display time. The children keep their name, their content
	 * and their file id, so a folder rename inside the same mount changes nothing
	 * the index can answer on. There is no index write to do here, neither one
	 * per child nor one at all, and expanding the subtree would be thousands of
	 * queue rows for no effect.
	 *
	 * The one exception is a move across a mount boundary, which changes who may
	 * see the subtree. That is a permission change, it belongs to the acl jobs of
	 * plan 03-04, and it is named here so the gap stays visible instead of being
	 * forgotten behind a folder check that looks complete.
	 */
	private function queueRename(Node $target): void {
		if (!$target instanceof File) {
			return;
		}

		// isUpdate is true: whatever the container has for this file id, it has
		// it from before the rename.
		$this->queue($target, true, QueueMapper::KIND_METADATA);
	}

	/**
	 * Three questions before a row is written, in this order because each one is
	 * cheaper than the one after it.
	 */
	private function queue(Node $node, bool $isUpdate, string $kind = QueueMapper::KIND_CONTENT): void {
		// 1. A file, never a folder. A folder operation is exactly one event
		// over a whole subtree, so queueing the folder node would queue one row
		// for something that has no content and none of the rows that actually
		// changed. Subtrees are resolved by a background job of their own in
		// plan 03-04, which is also the only thing that can band them.
		//
		// For a deleted folder that leaves a gap, and it is a known one. The
		// trash bin keeps the file ids and the cache entries of the descendants
		// under a different parent of the same storage, so the subtree job of
		// plan 03-04 can still enumerate them. With the trash bin switched off,
		// or once it has been emptied, they are really gone, and then the ETag
		// reconcile of plan 03-12 carries the result. That is what it is for.
		if (!$node instanceof File) {
			return;
		}

		// A deletion answers two of the three questions below differently, and
		// both exceptions are decisions rather than forgotten branches.
		$isDeletion = $kind === QueueMapper::KIND_DELETE;

		// 2. The document allowlist, read from the same constant the crawl
		// filters its query with. Without it every uploaded video and every
		// archive would be a queue row that the container fetches only to throw
		// it away, on the machine class this project targets.
		//
		// A deletion skips this question. The allowlist decides what gets into
		// the index, never what gets out of it: a file that reports a different
		// mimetype at deletion time than it did when it was indexed, because it
		// was overwritten or because the detection changed with an update, would
		// otherwise stay in the index for good.
		if (!$isDeletion && !in_array($node->getMimetype(), StorageService::ALLOWED_MIMETYPES, true)) {
			return;
		}

		$fileId = (int)$node->getId();
		if ($fileId <= 0) {
			// A node whose id is not usable cannot be acknowledged later and
			// would sit in the queue forever. Dropping it is better than a row
			// nobody can finish; the reconcile finds the file again.
			return;
		}

		$mount = $node->getMountPoint();
		$storageId = (int)$mount->getNumericStorageId();
		$rootId = (int)$mount->getStorageRootId();
		if ($storageId <= 0 || $rootId <= 0) {
			return;
		}

		// 3. A mount this app indexes. Without this question an event would pull
		// external storage into the index although IDX-01 leaves it out by
		// default, which is the one boundary an admin never explicitly agreed
		// to: a multi terabyte remote share would start flowing through HTTP
		// because someone saved a file on it.
		if (!$this->storageService->isIndexedStorage($storageId)) {
			return;
		}

		$size = (int)$node->getSize();
		if (!$isDeletion && $size > StorageCrawlJob::MAX_SIZE) {
			// The same ceiling and the same end state as the crawl. A file above
			// it is a visible decision with a reason and not a silent omission,
			// which is the whole content of IDX-06, and the constant lives with
			// the crawl because that is where it was measured.
			//
			// The second exception for a deletion. This ceiling writes a verdict,
			// and skipped(too_large) is a statement about a file that is present
			// and was not indexed. Writing it over a file that is gone would put
			// the wrong reason on the admin page and, worse, drop the deletion.
			$this->fileStateService->record($fileId, 'skipped', 'too_large');
			return;
		}

		// A deletion moves no bytes, so it takes no share of the byte budget a
		// claim spends. Handing over the size of the file that used to be there
		// would let a handful of large deletions fill a whole batch.
		$this->queueService->enqueueFile($fileId, $storageId, $rootId, $isDeletion ? 0 : $size, $isUpdate, $kind);
	}
}
