<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\EventDispatcher\IEventDispatcher;
use OCP\Files\File;
use OCP\Files\ForbiddenException;
use OCP\Files\IRootFolder;
use OCP\Log\Audit\CriticalActionPerformedEvent;
use Psr\Log\LoggerInterface;

/**
 * Opens a file for the content gateway, and opens it once more when the secure
 * view of Nextcloud Office refused the first open (issue #59).
 *
 * The first open runs outside actAs, as it did in 1.6.5: the folder and the
 * lookup of the named user run with that user active (issue #14, see
 * ReaderContext), the open after the restore, so the read hooks of
 * admin_audit and activity see the identity of the request (decision E1).
 *
 * richdocuments puts SecureViewWrapper around every mount except '/' whenever
 * a watermark is configured (Application.php v12.0.2 l. 153), and its fopen
 * refuses with 'Download blocked due the secure view policy' when
 * SecureViewService::shouldSecure holds (SecureViewWrapper.php l. 90-97).
 * Outside actAs the active user is null, and with null shareAll refuses even
 * the owner (PermissionManager.php l. 217-224), while shareDisabledDownload
 * and shareRead refuse only through the share or the read only mount the
 * file was asked through. Measured on 1.6.5 in five modes (45-AUDIT.md,
 * "Modus x Leser -> Ergebnis vorher").
 *
 * Only a refusal that provably comes from there opens the file again: an OCP
 * ForbiddenException with exactly that message AND the first frame of its
 * trace, getTrace()[0], in SecureViewWrapper::checkFileAccess, compared as
 * strings so that the class of richdocuments is never loaded (unchanged in
 * richdocuments v10.3.3, v11.1.3 and v12.0.2). A frame further up does not
 * count. The second open runs inside actAs of the reader, so the secure view
 * judges the reader and not nobody:
 *
 * - with an owner (ReaderCandidates: the home mount '/<uid>/'), the owner and
 *   nobody else. A refusal of the owner means that the watermark applies to the
 *   owner as well (allTags, a group of allGroups that holds the owner), and an
 *   owner who does not resolve the file leaves no safe reader; both end with
 *   policy and no further reader (decision E2). Findling does not work round
 *   a watermark.
 * - without an owner (a Team Folder, an external storage), the users of the
 *   file in reading order, at most ReaderCandidates::MAX_READER_TRIES. A
 *   reader whose folder or lookup throws or answers nothing is passed over
 *   with at most a debug line carrying the class name; a reader the secure
 *   view refuses as well is followed by the next one.
 *
 * Every other ForbiddenException, at the first open or at any later one, ends
 * with policy at once (fail closed; files_accesscontrol throws one, see
 * I-45-17-03). Every other Throwable of an open travels up to the controller
 * as before: 422 for a sharing violation, 500 otherwise. Only the named user
 * can produce not_found or a NoUserException, and only before any second
 * open, so the second round adds no answer an outside caller could tell a
 * missing user or file by (T-45-58).
 *
 * What changes for an admin (T-45-74, accepted with E1): for a file whose
 * first open the secure view refused, the read hooks name the reader of the
 * second open, usually the owner. That is written in the CHANGELOG of 1.7.0.
 *
 * allGroups is decided as G1: it refuses only with a user set, the first open
 * runs without one, so an allGroups rule does not stop indexing, as in 1.6.5.
 *
 * The answer is an array: outcome (ok, not_found, policy) and asked, the
 * number of readers of the second round; with ok also the file, its stream
 * (false when fopen returned false), the size of the file cache, the storage
 * and the reader. The reader stays inside the app and is never logged.
 */
final class GatewayReader {
	public const OUTCOME_OK = 'ok';
	public const OUTCOME_NOT_FOUND = 'not_found';
	public const OUTCOME_POLICY = 'policy';

	public const SECURE_VIEW_MESSAGE = 'Download blocked due the secure view policy';
	public const SECURE_VIEW_WRAPPER = 'OCA\Richdocuments\Storage\SecureViewWrapper';
	public const SECURE_VIEW_FUNCTION = 'checkFileAccess';

	/**
	 * The line admin_audit writes for a read inside actAs (plan 45-20, a4).
	 *
	 * admin_audit names the session user of a request (LogDetails takes
	 * OC_User::getUser(), the session value user_id), and actAs only sets the
	 * volatile active user, so its own line of such a read says "--". The
	 * public audit event CriticalActionPerformedEvent (OCP since 22) is written
	 * by admin_audit with its parameters in this order: file id, path, the uid
	 * of the reading user. Never a byte of the content. Without admin_audit
	 * nobody listens and the dispatch does nothing.
	 */
	public const AUDIT_MESSAGE = 'Findling read the file with id "%s" at "%s" as the user "%s" after the secure view of Nextcloud Office refused it without a user';

	public function __construct(
		private IRootFolder $rootFolder,
		private ReaderContext $readerContext,
		private ReaderCandidates $readerCandidates,
		private LoggerInterface $logger,
		private IEventDispatcher $eventDispatcher,
	) {
	}

	/**
	 * @return array{outcome: string, asked: int, file?: File, stream?: resource|false, size?: int, storage?: \OCP\Files\Storage\IStorage, reader?: string}
	 */
	public function open(int $fileId, string $userId): array {
		// A NoUserException of the named user travels up unchanged: the
		// controller answers it word for word like a missing file.
		$file = $this->readerContext->actAs(
			$userId,
			fn (): ?File => SearchService::readableFile($this->rootFolder->getUserFolder($userId), $fileId),
		);
		if ($file === null) {
			return ['outcome' => self::OUTCOME_NOT_FOUND, 'asked' => 0];
		}

		try {
			// Outside actAs, as before (E1).
			return $this->opened($file, $userId, 0);
		} catch (ForbiddenException $e) {
			if (!self::isSecureViewRefusal($e)) {
				return ['outcome' => self::OUTCOME_POLICY, 'asked' => 0];
			}
		}

		return $this->openAgain($fileId);
	}

	/**
	 * Whether a refusal comes from the secure view of richdocuments: an OCP
	 * ForbiddenException, the exact message, and the first frame of its trace
	 * in SecureViewWrapper::checkFileAccess. All three, compared as strings.
	 */
	public static function isSecureViewRefusal(\Throwable $e): bool {
		if (!$e instanceof ForbiddenException || $e->getMessage() !== self::SECURE_VIEW_MESSAGE) {
			return false;
		}

		$origin = $e->getTrace()[0] ?? [];

		return ($origin['class'] ?? null) === self::SECURE_VIEW_WRAPPER
			&& ($origin['function'] ?? null) === self::SECURE_VIEW_FUNCTION;
	}

	/**
	 * The second round, after a refusal of the secure view.
	 *
	 * @return array{outcome: string, asked: int, file?: File, stream?: resource|false, size?: int, storage?: \OCP\Files\Storage\IStorage, reader?: string}
	 */
	private function openAgain(int $fileId): array {
		$candidates = $this->readerCandidates->forFile($fileId);
		$owner = $candidates['owner'];
		if ($owner !== null) {
			// The owner alone (E2): any end other than an open is policy.
			$result = $this->openAs($owner, $fileId, 1);

			return $result ?? ['outcome' => self::OUTCOME_POLICY, 'asked' => 1];
		}

		$asked = 0;
		foreach (ReaderCandidates::readingOrder($candidates['users'], null) as $reader) {
			$asked++;
			// null passes on to the next reader; ok and policy both end here.
			$result = $this->openAs($reader, $fileId, $asked);
			if ($result !== null) {
				return $result;
			}
		}

		return ['outcome' => self::OUTCOME_POLICY, 'asked' => $asked];
	}

	/**
	 * One reader of the second round, all of it inside actAs: folder, lookup
	 * and open.
	 *
	 * null: the reader did not resolve the file, or the secure view refused
	 * the reader as well. policy: another ForbiddenException. ok: opened.
	 * Every other Throwable of the open travels up.
	 *
	 * @return array{outcome: string, asked: int, file?: File, stream?: resource|false, size?: int, storage?: \OCP\Files\Storage\IStorage, reader?: string}|null
	 */
	private function openAs(string $reader, int $fileId, int $asked): ?array {
		return $this->readerContext->actAs($reader, function () use ($reader, $fileId, $asked): ?array {
			try {
				$file = SearchService::readableFile($this->rootFolder->getUserFolder($reader), $fileId);
			} catch (\Throwable $e) {
				// A class name and the file id, never the text: the message of
				// a folder that cannot be built names the user or a path.
				$this->logger->debug('Findling: passed over a reader whose folder or lookup failed', ['fileId' => $fileId, 'class' => $e::class]);

				return null;
			}
			if ($file === null) {
				return null;
			}

			try {
				$opened = $this->opened($file, $reader, $asked);
			} catch (ForbiddenException $e) {
				return self::isSecureViewRefusal($e) ? null : ['outcome' => self::OUTCOME_POLICY, 'asked' => $asked];
			}

			// Only a read that happened, and only here, inside actAs: a plain
			// read outside it keeps the line admin_audit writes itself (a4).
			$this->eventDispatcher->dispatchTyped(new CriticalActionPerformedEvent(
				self::AUDIT_MESSAGE,
				['id' => $fileId, 'path' => $file->getPath(), 'reader' => $reader],
			));

			return $opened;
		});
	}

	/**
	 * The open itself. The size and the storage are asked before it, as the
	 * controller always did: the size of the file cache only tells an empty
	 * file from one whose open failed, and the storage decides how the stream
	 * is read. The 'r' is the entire read only guarantee of the gateway.
	 *
	 * @return array{outcome: string, asked: int, file: File, stream: resource|false, size: int, storage: \OCP\Files\Storage\IStorage, reader: string}
	 */
	private function opened(File $file, string $reader, int $asked): array {
		$size = max(0, (int)$file->getSize());
		$storage = $file->getStorage();
		$stream = $file->fopen('r');

		return [
			'outcome' => self::OUTCOME_OK,
			'asked' => $asked,
			'file' => $file,
			'stream' => $stream,
			'size' => $size,
			'storage' => $storage,
			'reader' => $reader,
		];
	}
}
