<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCA\Findling\AppInfo\Application;
use OCP\App\IAppManager;
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
 */
final class ExAppService {
	/**
	 * Two seconds, deliberately below the AppAPI default of three. The unified
	 * search calls every provider, so a slow provider slows down the whole
	 * search for the user.
	 */
	private const TIMEOUT_SECONDS = 2;

	public function __construct(
		private IAppManager $appManager,
		private IUserManager $userManager,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * @return list<array{fileId:int,title:string,snippet:string}>
	 */
	public function search(string $userId, string $term, int $limit): array {
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
			$this->logger->info('Findling: backend unreachable', ['error' => $response['error'] ?? 'unknown']);
			return [];
		}

		// Case 2. AppAPI hard sets http_errors to false, so 4xx and 5xx arrive
		// as an ordinary response object instead of throwing.
		/** @var IResponse $response */
		if ($response->getStatusCode() >= 400) {
			$this->logger->warning('Findling: backend returned an error', ['status' => $response->getStatusCode()]);
			return [];
		}

		// Case 3. A 2xx does not promise a body that parses.
		$body = $response->getBody();
		$decoded = is_string($body) ? json_decode($body, true) : null;
		if (!is_array($decoded) || !isset($decoded['results']) || !is_array($decoded['results'])) {
			$this->logger->warning('Findling: malformed backend response');
			return [];
		}

		return $this->filterHits($decoded['results']);
	}

	/**
	 * Case 4: the backend answered with valid JSON of the wrong shape. Anything
	 * that does not carry the three expected keys with the expected types is
	 * dropped here, so a faulty backend cannot push a type error into the
	 * search provider.
	 *
	 * @param array<mixed> $results
	 * @return list<array{fileId:int,title:string,snippet:string}>
	 */
	private function filterHits(array $results): array {
		$hits = [];
		$dropped = 0;

		foreach ($results as $result) {
			if (!is_array($result)
				|| !isset($result['fileId'], $result['title'], $result['snippet'])
				|| !is_int($result['fileId'])
				|| !is_string($result['title'])
				|| !is_string($result['snippet'])) {
				$dropped++;
				continue;
			}

			$hits[] = [
				'fileId' => $result['fileId'],
				'title' => $result['title'],
				'snippet' => $result['snippet'],
			];
		}

		if ($dropped > 0) {
			$this->logger->warning('Findling: dropped malformed hits', ['count' => $dropped]);
		}

		return $hits;
	}
}
