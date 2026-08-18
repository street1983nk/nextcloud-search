<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\AppInfo\Application;
use OCP\App\IAppManager;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\Http\Client\IResponse;
use OCP\IUserManager;
use Psr\Container\ContainerExceptionInterface;
use Psr\Container\NotFoundExceptionInterface;
use Psr\Log\LoggerInterface;

/**
 * The one and only place in this app that talks to the container.
 *
 * Keeping the call in a single class keeps the timeout, the shape of an error
 * and the way this app degrades in exactly one spot. Every failure mode below
 * ends in an empty list: a missing, stopped or slow backend must cost the user
 * a result group, never the whole search.
 *
 * Nothing here writes user content into the log. Transport status codes and
 * transport error texts are logged, search terms, titles and snippets are not.
 *
 * This class is also the place where the permission decision is made. The index
 * inside the container is a second data set and it drifts: a share is revoked, a
 * file is moved into a folder the user cannot reach, a document lands in the
 * trash. None of that reaches the container the moment it happens, so every hit
 * is resolved once more against the user's own folder before it becomes a search
 * result.
 */
final class ExAppService {
	/**
	 * Two seconds, deliberately below the AppAPI default of three. The unified
	 * search calls every provider, so a slow provider slows down the whole
	 * search for the user.
	 */
	private const TIMEOUT_SECONDS = 2;

	/**
	 * The one title that is allowed to arrive without a file behind it. Phase 1
	 * proves the whole path with a hit the container invents, and an invented hit
	 * has no node to resolve. The string is frozen on both sides, see
	 * CANARY_TITLE in backend/src/findling/api/search.py, and both go away
	 * together when phase 2 answers with real files.
	 */
	private const CANARY_TITLE = 'findling-canary';

	/**
	 * Hard ceiling on the answer before it is parsed. One megabyte is orders of
	 * magnitude above the largest legitimate answer (100 hits, a snippet each),
	 * and json_decode() on an unbounded string is the cheapest way to turn a
	 * broken backend into an out of memory of the whole PHP request.
	 */
	private const MAX_BODY_BYTES = 1048576;

	/**
	 * Ceilings in characters, not bytes. Both are defense in depth: the search
	 * dialog renders the two fields as text, and the backend is expected to send
	 * short strings anyway. A backend that sends a megabyte long title is a
	 * defect, and this is where the defect stops being the user's problem.
	 */
	private const MAX_TITLE_LENGTH = 255;
	private const MAX_SNIPPET_LENGTH = 1000;

	/**
	 * The range the backend accepts, see SearchRequest in
	 * backend/src/findling/api/search.py. Outside of it the request fails
	 * validation with a 422, which arrives here as an empty result group and
	 * looks exactly like "nothing found". Clamping instead means the user gets
	 * the first hits of a too large request rather than silence.
	 */
	private const MIN_LIMIT = 1;
	private const MAX_LIMIT = 100;

	public function __construct(
		private IAppManager $appManager,
		private IUserManager $userManager,
		private IRootFolder $rootFolder,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * @return list<array{fileId:int,path:string,title:string,snippet:string}>
	 */
	public function search(string $userId, string $term, int $limit): array {
		// Both bounds of the backend are enforced before the request is built. An
		// empty term is not an error, it is what the unified search sends while
		// the user is still typing, and it can only ever produce a 422 over
		// there. A round trip per keystroke for a request that cannot succeed is
		// the expensive half of that.
		$term = trim($term);
		if ($term === '') {
			return [];
		}
		$limit = max(self::MIN_LIMIT, min(self::MAX_LIMIT, $limit));

		$user = $this->userManager->get($userId);
		if ($user === null) {
			// Without a user object the app check below would silently fall
			// back to the session user, which is a different question.
			$this->logger->info('Findling: unknown user, returning no results');
			return [];
		}

		// info.xml has no way to declare an app to app dependency, so the bond
		// to app_api is a runtime check. Without it the whole unified search of
		// this user dies with a container error, not just our result group.
		if (!$this->appManager->isEnabledForUser('app_api', $user)) {
			$this->logger->info('Findling: app_api is not enabled, returning no results');
			return [];
		}

		try {
			$appApi = \OCP\Server::get(\OCA\AppAPI\PublicFunctions::class);
		} catch (ContainerExceptionInterface|NotFoundExceptionInterface) {
			$this->logger->info('Findling: AppAPI public functions unavailable');
			return [];
		}

		$response = $appApi->exAppRequest(
			Application::BACKEND_APP_ID,
			'/search',
			$userId,
			'POST',
			['query' => $term, 'limit' => $limit],
			['timeout' => self::TIMEOUT_SECONDS],
		);

		// Case 1 first, always. AppAPI catches every transport exception and
		// hands back an array, so an unknown, unreachable or timed out backend
		// arrives here. Calling a method on that array would be a fatal error
		// and would destroy the entire search request.
		if (is_array($response)) {
			// warning, not info, and deliberately the same level as the malformed
			// answer below: an unreachable backend is the one failure mode that
			// costs the user a whole result group without anything on screen
			// saying so. An info line is not what an admin looks at when a user
			// reports that the search finds nothing.
			//
			// The unified search asks once per keystroke, so this line can repeat.
			// Damping it needs state that outlives the request (ICacheFactory),
			// which is not worth a dependency here: phase 4 builds the status page
			// out of exactly this signal and owns the aggregation then.
			$this->logger->warning('Findling: backend unreachable', ['error' => $response['error'] ?? 'unknown']);
			return [];
		}

		// Case 2. AppAPI hard sets http_errors to false, so 4xx and 5xx arrive
		// as an ordinary response object instead of throwing.
		/** @var IResponse $response */
		if ($response->getStatusCode() >= 400) {
			$this->logger->warning('Findling: backend returned an error', ['status' => $response->getStatusCode()]);
			return [];
		}

		// Case 3. A 2xx does not promise a body that parses, and it does not
		// promise a body that fits into memory either. The length is checked
		// before the parser sees it, because json_decode() builds the whole tree.
		$body = $response->getBody();
		if (!is_string($body) || strlen($body) > self::MAX_BODY_BYTES) {
			$this->logger->warning(
				'Findling: backend answer is not a bounded string body',
				['bytes' => is_string($body) ? strlen($body) : -1],
			);
			return [];
		}

		$decoded = json_decode($body, true);
		if (!is_array($decoded) || !isset($decoded['results']) || !is_array($decoded['results'])) {
			$this->logger->warning('Findling: malformed backend response');
			return [];
		}

		return $this->filterHits($decoded['results'], $userId);
	}

	/**
	 * Case 4 and the permission recheck, in one pass over the answer.
	 *
	 * Two questions per hit. The first one is the shape: anything that does not
	 * carry the three expected keys with the expected types is dropped, so a
	 * faulty backend cannot push a type error into the search provider.
	 *
	 * The second one is the one that matters. A hit is only a hit if this user
	 * may see this file, and the only authority on that is Nextcloud itself, so
	 * the file id is resolved through the user's own folder. No node, no result.
	 * Title and path are then taken from that node and never from the backend
	 * answer: a compromised or simply confused container can otherwise put the
	 * name of a foreign file in front of the user. The snippet is the one field
	 * that has to come from the container, because only the container has read
	 * the text.
	 *
	 * @param array<mixed> $results
	 * @return list<array{fileId:int,path:string,title:string,snippet:string}>
	 */
	private function filterHits(array $results, string $userId): array {
		$hits = [];
		$dropped = 0;
		$unresolved = 0;
		$userFolder = null;

		foreach ($results as $result) {
			if (!is_array($result)
				|| !isset($result['fileId'], $result['title'], $result['snippet'])
				|| !is_int($result['fileId'])
				|| !is_string($result['title'])
				|| !is_string($result['snippet'])) {
				$dropped++;
				continue;
			}

			$fileId = $result['fileId'];
			$snippet = $this->plainText($result['snippet'], self::MAX_SNIPPET_LENGTH);
			if ($snippet === null) {
				$dropped++;
				continue;
			}

			if ($fileId <= 0) {
				// A file id that cannot point at a file is only accepted for the
				// phase 1 canary, and only under its exact title. Everything
				// else with such an id is a defect and is dropped.
				if ($result['title'] !== self::CANARY_TITLE) {
					$dropped++;
					continue;
				}

				$hits[] = [
					'fileId' => 0,
					'path' => '',
					'title' => self::CANARY_TITLE,
					'snippet' => $snippet,
				];
				continue;
			}

			// Resolved once per answer, not once per hit, and only when a hit
			// actually needs it. The canary above never touches the filesystem.
			$userFolder ??= $this->userFolder($userId);
			if ($userFolder === null) {
				// No home folder means no permission decision is possible.
				// Handing out unchecked hits instead would be the actual bug.
				return [];
			}

			$node = $userFolder->getFirstNodeById($fileId);
			if ($node === null) {
				// Never visible, no longer visible, deleted: deliberately the
				// same outcome for all three, so a hit cannot be used to probe
				// for files this user is not allowed to see.
				$unresolved++;
				continue;
			}

			// The node name and the path come from the file system, not from the
			// container, and they still go through the same cleaning: a file name
			// out of an external storage can carry anything.
			$relativePath = ltrim((string)$userFolder->getRelativePath($node->getPath()), '/');
			$title = $this->plainText($node->getName(), self::MAX_TITLE_LENGTH);
			$path = $this->plainText($relativePath, self::MAX_TITLE_LENGTH);
			if ($title === null || $path === null) {
				$dropped++;
				continue;
			}

			$hits[] = [
				'fileId' => $fileId,
				'path' => $path,
				'title' => $title,
				'snippet' => $snippet,
			];
		}

		if ($dropped > 0) {
			$this->logger->warning('Findling: dropped malformed hits', ['count' => $dropped]);
		}

		if ($unresolved > 0) {
			// Not a defect: an index that lags behind a revoked share is the
			// normal state of the world. The counter is what shows that the
			// recheck is doing work instead of waving everything through.
			$this->logger->debug('Findling: dropped hits this user cannot see', ['count' => $unresolved]);
		}

		return $hits;
	}

	/**
	 * Bounded plain text, or null when the input is not valid UTF-8.
	 *
	 * Defense in depth, not the primary control. The primary control is that the
	 * search dialog interpolates title and subline as text, so markup reaches the
	 * user verbatim instead of being rendered. What is left over are the two
	 * things text interpolation does not help against: control characters, which
	 * can reorder a line (bidi overrides), fake a second line in the Nextcloud
	 * log or cut a string short in a terminal, and length, which is a rendering
	 * problem in the dialog and a memory problem in the answer.
	 *
	 * The tab survives, everything else in that range does not. A snippet from
	 * the container is a single line by construction, so nothing legitimate is
	 * lost; should phase 2 ever want to keep newlines, they belong folded into
	 * spaces here rather than passed through.
	 *
	 * Invalid UTF-8 is a null and the caller drops the hit. Passing it on would
	 * break the JSON and the XML rendering of the OCS answer, which costs the
	 * whole unified search instead of one result.
	 */
	private function plainText(string $value, int $maxLength): ?string {
		$clean = preg_replace('/(?!\t)[\p{Cc}\p{Cf}\p{Zl}\p{Zp}]/u', '', $value);
		if ($clean === null) {
			return null;
		}

		// Characters, not bytes: cutting a UTF-8 string at a byte offset produces
		// half a character, which is exactly the invalid input this method exists
		// to keep out.
		return mb_substr($clean, 0, $maxLength, 'UTF-8');
	}

	/**
	 * The user's home folder, or null when there is none.
	 *
	 * Every failure is caught on purpose. getUserFolder() signals a missing user
	 * with a class from the private namespace of the server, and a missing home
	 * directory with a different one again; both mean exactly the same thing
	 * here, and neither may reach the unified search as an exception.
	 */
	private function userFolder(string $userId): ?Folder {
		try {
			return $this->rootFolder->getUserFolder($userId);
		} catch (\Throwable $e) {
			$this->logger->warning('Findling: no home folder for this user, dropping every hit', ['exception' => $e]);
			return null;
		}
	}
}
