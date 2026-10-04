<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Controller\QueueController;
use OCA\Findling\Service\CrawlAdvanceService;
use OCA\Findling\Service\QueueService;
use OCP\AppFramework\Http;
use OCP\IRequest;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The lane of a claim, as the controller answers it (PAR-01, K6).
 *
 * Gate B in backend/tests holds the attributes and the position of
 * rejectForeignCaller; this suite holds the answers: a lane out of the closed
 * set reaches the service unchanged and comes back as an echo, an unknown lane
 * is a 400 whose value never reaches the log, and a foreign ExApp is refused
 * before the lane is even looked at.
 *
 * The echo is the point of the whole change on this side. The Nextcloud
 * dispatcher binds declared parameters and drops unknown ones silently, so a
 * companion of 1.3 answers a claim with lane=embed as if it had been asked for
 * everything. Only the echo lets the container tell the two apart.
 */
#[CoversClass(QueueController::class)]
final class QueueControllerTest extends TestCase {
	private QueueService&MockObject $queueService;
	private LoggerInterface&MockObject $logger;

	protected function setUp(): void {
		parent::setUp();

		$this->queueService = $this->createMock(QueueService::class);
		$this->logger = $this->createMock(LoggerInterface::class);
	}

	/**
	 * The app id of the container, read out of the class instead of copied,
	 * for the same reason as in GatewayControllerTest.
	 */
	private function backendAppId(): string {
		$value = (new \ReflectionClass(Application::class))->getConstant('BACKEND_APP_ID');

		self::assertIsString($value, 'BACKEND_APP_ID is gone or is no longer a string');

		return $value;
	}

	private function controller(string $callerAppId, ?CrawlAdvanceService $crawlAdvance = null): QueueController {
		$request = $this->createMock(IRequest::class);
		$request->method('getHeader')->willReturnCallback(
			static fn (string $name): string => $name === 'EX-APP-ID' ? $callerAppId : '',
		);

		return new QueueController(
			$request,
			$this->queueService,
			$crawlAdvance ?? $this->createMock(CrawlAdvanceService::class),
			$this->logger,
		);
	}

	/**
	 * Run 8 of the 28-07 chain: the reconcile of the container read an empty
	 * queue as a quiet instance while the crawl was still running, walked ahead
	 * and requeued the whole partial corpus, which the crawl then queued a second
	 * time. The counters therefore carry whether the crawl is unfinished, and the
	 * three counters themselves stay what they were.
	 */
	public function testTheStatsCarryWhetherTheCrawlIsUnfinished(): void {
		$this->queueService->method('stats')->willReturn(['scheduled' => 0, 'running' => 0, 'failed' => 2]);
		$crawlAdvance = $this->createMock(CrawlAdvanceService::class);
		$crawlAdvance->expects(self::once())->method('crawling')->willReturn(true);

		$response = $this->controller($this->backendAppId(), $crawlAdvance)->documentStats();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['scheduled' => 0, 'running' => 0, 'failed' => 2, 'crawling' => true], $response->getData());
	}

	public function testAForeignExAppGetsNoStats(): void {
		$crawlAdvance = $this->createMock(CrawlAdvanceService::class);
		$crawlAdvance->expects(self::never())->method('crawling');
		$this->queueService->expects(self::never())->method('stats');

		$response = $this->controller('some_other_app', $crawlAdvance)->documentStats();

		self::assertSame(Http::STATUS_FORBIDDEN, $response->getStatus());
	}

	public function testAClaimWithoutALaneIsEchoedAsAll(): void {
		$this->queueService->expects(self::once())->method('claim')
			->with(32, 67108864, QueueService::LANE_ALL)
			->willReturn([]);

		$response = $this->controller($this->backendAppId())->getDocuments();

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['files' => [], 'lane' => 'all'], $response->getData());
	}

	public function testTheEmbedLaneReachesTheServiceAndIsEchoed(): void {
		$this->queueService->expects(self::once())->method('claim')
			->with(32, 67108864, QueueService::LANE_EMBED)
			->willReturn([]);

		$response = $this->controller($this->backendAppId())->getDocuments(32, 67108864, 'embed');

		self::assertSame(Http::STATUS_OK, $response->getStatus());
		self::assertSame(['files' => [], 'lane' => 'embed'], $response->getData());
	}

	public function testTheIndexLaneReachesTheServiceAndIsEchoed(): void {
		$this->queueService->expects(self::once())->method('claim')
			->with(32, 67108864, QueueService::LANE_INDEX)
			->willReturn([]);

		$response = $this->controller($this->backendAppId())->getDocuments(32, 67108864, 'index');

		self::assertSame(['files' => [], 'lane' => 'index'], $response->getData());
	}

	public function testAnUnknownLaneIsA400AndIsNotLogged(): void {
		$this->queueService->expects(self::never())->method('claim');
		$this->logger->expects(self::once())->method('warning')->with(
			self::callback(static fn (string $message): bool => !str_contains($message, 'turbo')),
			self::callback(static fn (array $context): bool => !str_contains(json_encode($context, JSON_THROW_ON_ERROR), 'turbo')),
		);

		$response = $this->controller($this->backendAppId())->getDocuments(32, 67108864, 'turbo');

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
		self::assertSame(['error' => 'Unknown lane.'], $response->getData());
	}

	public function testALaneIsComparedStrictly(): void {
		// 'Embed' is not 'embed': the set is closed and compared with ===.
		$this->queueService->expects(self::never())->method('claim');

		$response = $this->controller($this->backendAppId())->getDocuments(32, 67108864, 'Embed');

		self::assertSame(Http::STATUS_BAD_REQUEST, $response->getStatus());
	}

	public function testAForeignExAppIsRefusedBeforeTheLaneIsLookedAt(): void {
		// An unknown lane on purpose: the foreign caller gets the 403 and not
		// the 400, which proves rejectForeignCaller runs first (T-25-07).
		$this->queueService->expects(self::never())->method('claim');

		$response = $this->controller('some_other_backend')->getDocuments(32, 67108864, 'turbo');

		self::assertSame(Http::STATUS_FORBIDDEN, $response->getStatus());
		$data = $response->getData();
		self::assertIsArray($data);
		self::assertArrayNotHasKey('lane', $data);
		self::assertArrayNotHasKey('files', $data);
	}
}
