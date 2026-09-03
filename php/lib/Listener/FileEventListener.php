<?php

declare(strict_types=1);

namespace OCA\Findling\Listener;

use OCA\Findling\BackgroundJobs\SubtreeExpandJob;
use OCA\Findling\Db\QueueMapper;
use OCA\Findling\Service\ExclusionService;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCA\Findling\Service\SettingsService;
use OCA\Findling\Service\StorageService;
use OCA\Files_Trashbin\Events\MoveToTrashEvent;
use OCA\Files_Trashbin\Events\NodeRestoredEvent;
use OCP\BackgroundJob\IJobList;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeCopiedEvent;
use OCP\Files\Events\Node\NodeCreatedEvent;
use OCP\Files\Events\Node\NodeDeletedEvent;
use OCP\Files\Events\Node\NodeRenamedEvent;
use OCP\Files\Events\Node\NodeTouchedEvent;
use OCP\Files\Events\Node\NodeWrittenEvent;
use OCP\Files\File;
use OCP\Files\Folder;
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
		private SettingsService $settingsService,
		private ExclusionService $exclusionService,
		private IJobList $jobList,
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
				// target carries the name and the path the index has to hold. The
				// source is needed for one question all the same: whether the node
				// crossed a mount boundary on its way.
				$this->queueRename($event->getSource(), $event->getTarget());
				return;
			}

			if ($event instanceof NodeDeletedEvent) {
				// Queued as kind 'delete', the one job that needs no node on the
				// far side. The mimetype filter does not run for it, see queue():
				// a file that reports a different type now than it did when it
				// was indexed still has to leave the index.
				$this->queueDeletion($event->getNode());
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
				$this->queueDeletion($event->getNode());
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
				$this->queueRestore($event->getTarget());
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
	 * see the subtree. That is a permission change and it is handled below, with
	 * a subtree job that hands every descendant an acl row.
	 */
	private function queueRename(Node $source, Node $target): void {
		if ($target instanceof Folder) {
			$this->expandMovedFolder($source, $target);
			return;
		}

		if (!$target instanceof File) {
			return;
		}

		// isUpdate is true: whatever the container has for this file id, it has
		// it from before the rename.
		$this->queue($target, true, QueueMapper::KIND_METADATA);
	}

	/**
	 * A folder that was renamed or moved, in the two cases pitfall 1 separates.
	 *
	 * **Inside the same mount nothing happens, and that is the decision from plan
	 * 03-02.** The descendants keep their name, their content, their file id and
	 * their permissions. Only files.path in the container goes stale, and that
	 * field is written into the index but read by no query and shown by no
	 * provider, because a result takes its title and its path from the Nextcloud
	 * node at display time. Expanding the subtree for it would be thousands of
	 * queue rows for no effect at all.
	 *
	 * **Across a mount boundary everything changes.** Moving a folder into a Team
	 * Folder or out of one rewrites who may see every file inside it, and none of
	 * those files raises an event of its own. That is what the subtree job is
	 * for: it resolves the descendants in bands and gives each of them an acl
	 * row.
	 *
	 * The numeric storage id is the mount identity here. Comparing mount points
	 * by their path would answer a different question, since a rename changes the
	 * path of a folder that never left its mount.
	 */
	private function expandMovedFolder(Node $source, Folder $target): void {
		$storageId = (int)$target->getMountPoint()->getNumericStorageId();
		if ($storageId <= 0 || (int)$source->getMountPoint()->getNumericStorageId() === $storageId) {
			return;
		}

		$this->expandFolder($target, QueueMapper::KIND_ACL);
	}

	/**
	 * A deletion, for a file directly and for a folder through its subtree.
	 *
	 * A deleted folder raises one event and takes its whole subtree with it, so
	 * without the expansion every descendant would stay in the index and in the
	 * prefilter until somebody reindexed the instance.
	 *
	 * That the descendants can still be enumerated after the deletion is a
	 * property of the trash bin: it keeps their file ids and their cache entries
	 * under a different parent of the same storage, so an ancestor query still
	 * finds them. Where the trash bin is switched off, or where it was emptied
	 * before the job ran, they are really gone and the query comes back empty. In
	 * that case the ETag reconcile of plan 03-12 carries the result, which is
	 * exactly what it is for. Both events of a deletion route through here, and
	 * IJobList::add deduplicates over the argument, so a trashed folder plans one
	 * job and not two.
	 */
	private function queueDeletion(Node $node): void {
		if (!$node instanceof Folder) {
			$this->queue($node, true, QueueMapper::KIND_DELETE);
			return;
		}

		$this->expandFolder($node, QueueMapper::KIND_DELETE);
	}

	/**
	 * A restoration out of the trash bin, for a file directly and for a folder
	 * through its subtree.
	 *
	 * A restored folder raises one event and brings its whole subtree back with
	 * it, exactly as the deletion took it away, and none of the descendants
	 * raises an event of its own. They need their text back, because the
	 * deletion dropped every one of them out of the index and left a tombstone
	 * behind, so what they need is content jobs and the subtree job is what
	 * hands them out in bands.
	 *
	 * **Why this is not left to the reconcile.** It was, until this plan, and
	 * measured on a local instance the result is nothing at all: a restored
	 * folder produced zero queue rows and its files stayed unfindable until the
	 * next reconcile cycle, which is up to a day on the default cadence. That is
	 * not the promise of IDX-04, and restoring a folder is a deliberate user
	 * action and not a repair case. The reconcile stays what it is, the safety
	 * net for the events nobody sent, and it keeps covering the cases this
	 * branch cannot see: the trash bin emptied while the container was down, a
	 * restore during an update with the listener unregistered, a row that was
	 * lost on the way.
	 *
	 * **It is the same subtree job the other three folder operations use.** A
	 * second mechanism for a re-crawl would be the one thing worth avoiding
	 * here: this job has its band, its wall clock ceiling, its cursor and its
	 * self planned successor, so the subtree of a restored archive folder cannot
	 * become an unbounded amount of work inside a user's click.
	 */
	private function queueRestore(Node $node): void {
		if (!$node instanceof Folder) {
			$this->queue($node, true);
			return;
		}

		$this->expandFolder($node, QueueMapper::KIND_CONTENT);
	}

	/**
	 * The four questions a folder has to answer before its subtree is planned.
	 *
	 * One method for the three callers that need them, so that a fourth folder
	 * operation cannot arrive with three of the four. Every one of them is a
	 * reason to do nothing at all rather than to plan a job: a node without a
	 * usable mount or file id names no subtree, and a mount this app does not
	 * index has no descendants to correct.
	 */
	private function expandFolder(Folder $node, string $kind): void {
		$mount = $node->getMountPoint();
		$storageId = (int)$mount->getNumericStorageId();
		$rootId = (int)$mount->getStorageRootId();
		$ancestorId = (int)$node->getId();
		if ($storageId <= 0 || $rootId <= 0 || $ancestorId <= 0) {
			return;
		}

		if (!$this->storageService->isIndexedStorage($storageId)) {
			return;
		}

		$this->expand($storageId, $rootId, $ancestorId, $kind);
	}

	/**
	 * Plan the subtree of one folder operation, never walk it here.
	 *
	 * The walk is unbounded by definition: one event stands for as many files as
	 * the folder holds. Doing it inside the user's action would put that whole
	 * amount into a single web request, which is the difference between a click
	 * that answers and a click that times out.
	 */
	private function expand(int $storageId, int $rootId, int $ancestorId, string $kind): void {
		$this->jobList->add(SubtreeExpandJob::class, [
			'storage_id' => $storageId,
			'root_id' => $rootId,
			'ancestor_id' => $ancestorId,
			'kind' => $kind,
			'last_file_id' => 0,
		]);
	}

	/**
	 * Four questions before a row is written, in this order because each one is
	 * cheaper than the one after it.
	 *
	 * The fourth joined with plan 04-08, the folder exclusions, and it sits
	 * where it does for that reason: after the mount question, which is a
	 * request cached lookup, and before the size check, which is the one that
	 * writes a verdict.
	 */
	private function queue(Node $node, bool $isUpdate, string $kind = QueueMapper::KIND_CONTENT): void {
		// 1. A file, never a folder. A folder operation is exactly one event
		// over a whole subtree, so queueing the folder node would queue one row
		// for something that has no content and none of the rows that actually
		// changed. Subtrees are resolved by SubtreeExpandJob, which is the only
		// thing that can band them, and the two callers that need it hand their
		// folder to it before they ever reach this method.
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
		// because someone saved a file on it. Since plan 04-08 that default is
		// a switch, and this question still answers it, because it reads the
		// same composed mount list the crawl walks.
		if (!$this->storageService->isIndexedStorage($storageId)) {
			return;
		}

		// 4. A rule of today, through the one helper the crawl uses, on the one
		// path space (ADM-04, D-06). This is the question pitfall 4 is about:
		// the crawl compares against the internal path of a cache entry and
		// this method against the path of a node, so if each of them built its
		// own comparison, a prefix would hit in one and miss in the other, the
		// crawl would leave the folder alone, and every save inside it would
		// queue the file again. The index would fill up slowly with exactly
		// what was supposed to be left out, and nothing on the page would say
		// so. Both call paths therefore ask ExclusionService for the path AND
		// for the verdict, and backend/tests/test_exclusion_path_space.py
		// reports any second comparison.
		//
		// The list is asked first so that the root lookup does not happen at
		// all on an instance without exclusions, which is the default of a zero
		// config app and therefore the overwhelmingly common case: this method
		// runs inside every single write on the instance.
		//
		// A deletion skips this question, and that is the third exception of
		// this kind rather than a forgotten branch. An excluded file that gets
		// deleted has to leave the index, and an exclusion branch in front of
		// the deletion would drop the delete row and keep the document
		// findable for good.
		if (!$isDeletion && $this->exclusionService->prefixes() !== []) {
			$relative = $this->exclusionService->mountRelativePath(
				$node->getInternalPath(),
				$this->storageService->mountRootPath($storageId, $rootId),
			);
			if ($this->exclusionService->isExcluded($relative)) {
				// No verdict row, for the reason written at the same branch of
				// the crawl: the diagnosis works excluded out live, and a row
				// per excluded file would be a write per save on a folder
				// somebody excluded precisely because it is large.
				return;
			}
		}

		// 5. The size, and a deletion is not asked for one (Gruppe-B-IN-02). The
		// call used to stand in front of this exception, so every deletion paid
		// it for an answer that is discarded twice over: the ceiling below does
		// not apply to a deletion, and the queue row of a deletion carries a
		// zero by the rule at the enqueue below. What the call costs is a look at
		// the cache entry of a node that is on its way out, and depending on the
		// event that node is not fully available any more: MoveToTrashEvent and
		// NodeDeletedEvent fire around the moment the entry moves, and asking a
		// vanishing node for a number nobody uses is the kind of question that
		// turns into a warning in a log nobody can act on.
		$size = $isDeletion ? 0 : (int)$node->getSize();
		if (!$isDeletion && $size > $this->settingsService->maxFileBytes()) {
			// The same ceiling and the same end state as the crawl, and since
			// plan 04-08 the same source for it: SettingsService hands out the
			// value in force, clamped at what the container reported, while
			// StorageCrawlJob keeps the constant as the documented default. A
			// file above the ceiling is a visible decision with a reason and not
			// a silent omission, which is the whole content of IDX-06.
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
		// would let a handful of large deletions fill a whole batch. The zero is
		// set where the size is read, one branch above, so this line has one
		// meaning for every kind of job.
		$this->queueService->enqueueFile($fileId, $storageId, $rootId, $size, $isUpdate, $kind);
	}
}
