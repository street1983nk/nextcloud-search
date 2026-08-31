<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\FileStateService;
use OCA\Findling\Service\QueueService;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;
use Psr\Log\LoggerInterface;

/**
 * The work stock as seen from the container.
 *
 * Four endpoints: take work, acknowledge it, hand it back, count it. Nobody
 * pushes anything into the container, it collects when it can, and that single
 * property is what gives this app back pressure for free and lets a crashed
 * container pile work up instead of losing it.
 *
 * This is the only writing path from the ExApp into Nextcloud, and it writes
 * into the two tables this app owns and nowhere else. No method here touches a
 * user file, and there is no code path from here into the file system at all.
 * Because of that the read only gate on the Python side gets an explicit, named
 * exception for exactly the two write paths below, added in its own step in
 * plan 02-10 rather than as a side effect of a feature.
 *
 * Every method carries the ExApp attribute and the CSRF exemption, both spelled
 * out fully qualified for the same reason as in GatewayController: a grep gate
 * counts attributes that way and cannot be fooled by an import line. The CSRF
 * exemption is not a weakening; the credential on these routes is the signed
 * AppAPI header, and there is no session involved that a token could protect.
 */
class QueueController extends OCSController {
	/**
	 * Thirty two files or sixty four megabytes, whichever comes first. The byte
	 * budget exists because thirty two invoices and thirty two scans are not the
	 * same amount of memory on a four gigabyte box.
	 */
	private const DEFAULT_BATCH_FILES = 32;
	private const DEFAULT_BATCH_BYTES = 67108864;

	/**
	 * Hard bounds, not suggestions. The container is trusted, but this boundary
	 * is the cheapest place at which a defect in the worker stays a bad request
	 * instead of becoming database load. A batch of a million rows is never a
	 * legitimate request.
	 */
	private const MAX_BATCH_FILES = 256;
	private const MIN_BATCH_BYTES = 1048576;
	private const MAX_BATCH_BYTES = 1073741824;

	/**
	 * The acknowledgement is deleted in bands of a thousand anyway, so a longer
	 * list buys nothing and only makes a single request more expensive.
	 */
	private const MAX_LIST_LENGTH = 1000;

	public function __construct(
		IRequest $request,
		private QueueService $queueService,
		private LoggerInterface $logger,
	) {
		parent::__construct(Application::APP_ID, $request);
	}

	/**
	 * GET /ocs/v2.php/apps/findling/queues/documents?n=32&max_bytes=67108864
	 *
	 * Answers with {"files": {queueId: source}}. The key is the queue row id
	 * because that is what has to come back on acknowledgement, and the source
	 * carries metadata only: the bytes are a separate request per file, so this
	 * answer stays small even for a batch of large scans.
	 *
	 * An empty queue is an empty files container and not an error. The collector
	 * treats it as "nothing to do" and backs off.
	 */
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'GET', url: '/queues/documents')]
	public function getDocuments(int $n = self::DEFAULT_BATCH_FILES, int $max_bytes = self::DEFAULT_BATCH_BYTES): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		$limit = max(1, min(self::MAX_BATCH_FILES, $n));
		$budget = max(self::MIN_BATCH_BYTES, min(self::MAX_BATCH_BYTES, $max_bytes));

		try {
			$files = $this->queueService->claim($limit, $budget);
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not hand out a batch: ' . $e->getMessage(), ['exception' => $e]);
			return new DataResponse(['error' => 'Queue is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}

		return new DataResponse(['files' => $files]);
	}

	/**
	 * DELETE /ocs/v2.php/apps/findling/queues/documents
	 *
	 * Body: {"files": [queueId], "failed": [{"queueId": id, "reason": code}]}
	 *
	 * The second list is the return channel and the reason this endpoint takes
	 * two lists instead of one. Without it the status page of phase 4 would have
	 * to ask the container which files it could not process, and that would be a
	 * second place holding the truth about the same fact. Two of those always
	 * disagree eventually, and the one on the Nextcloud side is the one an admin
	 * can still read when the container is down.
	 *
	 * Both lists are processed in one transaction: rows removed without their
	 * reason recorded would disappear from the queue and from the diagnosis at
	 * the same moment.
	 *
	 * Nextcloud binds OCS parameters from the query string and from the request
	 * body alike, so the Python client can send this as a DELETE with a JSON
	 * body and does not need a POST override. That is written down here because
	 * plan 02-10 builds that client and the question would otherwise be raised a
	 * second time.
	 *
	 * @param array<mixed> $files
	 * @param array<mixed> $failed
	 */
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'DELETE', url: '/queues/documents')]
	public function acknowledgeDocuments(array $files = [], array $failed = []): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		$done = $this->intList($files);
		if ($done === null) {
			return $this->badList();
		}

		$failures = $this->failureList($failed);
		if ($failures === null) {
			return $this->badList();
		}

		try {
			$result = $this->queueService->acknowledge($done, $failures);
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not acknowledge a batch: ' . $e->getMessage(), ['exception' => $e]);
			return new DataResponse(['error' => 'Queue is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}

		return new DataResponse($result);
	}

	/**
	 * POST /ocs/v2.php/apps/findling/queues/documents/unlock
	 *
	 * Body: {"ids": [queueId]}
	 *
	 * The graceful shutdown path. A container that is asked to stop hands back
	 * what it holds, so a restart is productive immediately instead of waiting
	 * out the lock timeout. Only a hard kill pays that timeout.
	 *
	 * @param array<mixed> $ids
	 */
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'POST', url: '/queues/documents/unlock')]
	public function unlockDocuments(array $ids = []): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		$queueIds = $this->intList($ids);
		if ($queueIds === null) {
			return $this->badList();
		}

		try {
			$released = $this->queueService->unlock($queueIds);
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not release a batch: ' . $e->getMessage(), ['exception' => $e]);
			return new DataResponse(['error' => 'Queue is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}

		return new DataResponse(['released' => $released]);
	}

	/**
	 * GET /ocs/v2.php/apps/findling/queues/documents/stats
	 *
	 * Three numbers: waiting, held right now, and how many files ended as
	 * failed. The third one comes out of the state table, not out of the queue,
	 * which is why it survives a container that is switched off.
	 */
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'GET', url: '/queues/documents/stats')]
	public function documentStats(): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		try {
			return new DataResponse($this->queueService->stats());
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not count the queue: ' . $e->getMessage(), ['exception' => $e]);
			return new DataResponse(['error' => 'Queue is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}
	}

	/**
	 * The attribute on every method above answers "is this a registered external
	 * app", not "is this our external app". Every other backend on the instance
	 * passes that test, so without this comparison an unrelated container could
	 * drain the work stock or write states for files it has never seen. AppAPI
	 * puts the calling app id into this header.
	 *
	 * The same deliberate residual risk as in GatewayController applies: this
	 * trusts AppAPI to have authenticated the caller before the request arrives.
	 * Whoever can forge that header has broken the AppAPI trust model itself.
	 */
	private function rejectForeignCaller(): ?DataResponse {
		$callerAppId = $this->request->getHeader('EX-APP-ID');
		if ($callerAppId === Application::BACKEND_APP_ID) {
			return null;
		}

		$this->logger->warning('Findling: queue called by a foreign ExApp', ['app' => $callerAppId]);

		return new DataResponse(
			['error' => 'This route is reserved for the Findling backend.'],
			Http::STATUS_FORBIDDEN,
		);
	}

	/**
	 * A list of positive integers, or null when the input is not one.
	 *
	 * Rejecting instead of silently filtering is on purpose. A worker that sends
	 * a malformed list has a defect, and a partially accepted acknowledgement
	 * would leave it believing that rows were removed which are still there.
	 *
	 * @param array<mixed> $raw
	 * @return int[]|null
	 */
	private function intList(array $raw): ?array {
		if (count($raw) > self::MAX_LIST_LENGTH) {
			return null;
		}

		$ids = [];
		foreach ($raw as $value) {
			$id = $this->queueId($value);
			if ($id === null) {
				return null;
			}

			$ids[] = $id;
		}

		return array_values(array_unique($ids));
	}

	/**
	 * The failure list, mapped from queue id to reason code.
	 *
	 * The reason is checked against the closed list of the state service before
	 * it goes anywhere near the database. That check is what makes it impossible
	 * for free text, and therefore for a file name, to be stored as a reason.
	 *
	 * @param array<mixed> $raw
	 * @return array<int, string>|null
	 */
	private function failureList(array $raw): ?array {
		if (count($raw) > self::MAX_LIST_LENGTH) {
			return null;
		}

		$failures = [];
		foreach ($raw as $entry) {
			if (!is_array($entry)) {
				return null;
			}

			$id = $this->queueId($entry['queueId'] ?? null);
			$reason = $entry['reason'] ?? null;
			if ($id === null || !is_string($reason) || !in_array($reason, FileStateService::REASONS, true)) {
				return null;
			}

			$failures[$id] = $reason;
		}

		return $failures;
	}

	/**
	 * OCS delivers numbers from a JSON body as integers and the same numbers
	 * from a query string as strings, so both are accepted, and nothing else is.
	 */
	private function queueId(mixed $value): ?int {
		if (is_int($value)) {
			return $value > 0 ? $value : null;
		}

		if (is_string($value) && ctype_digit($value)) {
			$id = (int)$value;

			return $id > 0 ? $id : null;
		}

		return null;
	}

	private function badList(): DataResponse {
		// The offending value is deliberately not logged: it is unvalidated
		// input, and a file name arriving in it is one of the cases this
		// validation exists for.
		$this->logger->warning('Findling: rejected a malformed queue list');

		return new DataResponse(
			['error' => 'Malformed list of queue ids.'],
			Http::STATUS_BAD_REQUEST,
		);
	}
}
