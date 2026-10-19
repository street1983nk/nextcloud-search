<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\ParallelSearchService;
use OCP\App\IAppManager;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The detection behind the hint of UMST-02 (plan 34-03, D-34-02).
 *
 * The app manager is a stub that knows a set of enabled app ids and records
 * every id it was asked about. It answers isEnabledForAnyone only; the two
 * questions that would be wrong here, isEnabledForUser (misses an app enabled
 * for a group) and isInstalled (deprecated, says nothing about enabled), are
 * expected never, so a service that asked either one fails every case below
 * (T-34-11).
 */
#[CoversClass(ParallelSearchService::class)]
final class ParallelSearchServiceTest extends TestCase {
	/** @var list<string> every app id isEnabledForAnyone was asked about, in order */
	private array $asked = [];

	protected function setUp(): void {
		parent::setUp();

		$this->asked = [];
	}

	/** @param list<string> $enabled */
	private function service(array $enabled): ParallelSearchService {
		$appManager = $this->createMock(IAppManager::class);
		$appManager->method('isEnabledForAnyone')->willReturnCallback(
			function (string $appId) use ($enabled): bool {
				$this->asked[] = $appId;

				return in_array($appId, $enabled, true);
			},
		);
		$appManager->expects(self::never())->method('isEnabledForUser');
		$appManager->expects(self::never())->method('isInstalled');

		return new ParallelSearchService($appManager);
	}

	public function testNoAppOfTheFrameworkEnabledIsNoHint(): void {
		self::assertFalse($this->service([])->active());
	}

	public function testOnlyFulltextsearchEnabledIsTheHint(): void {
		self::assertTrue($this->service(['fulltextsearch'])->active());
	}

	public function testOnlyFilesFulltextsearchEnabledIsTheHint(): void {
		self::assertTrue($this->service(['files_fulltextsearch'])->active());
	}

	public function testBothAppsEnabledIsTheHint(): void {
		self::assertTrue($this->service(['fulltextsearch', 'files_fulltextsearch'])->active());
	}

	public function testOnlyTheIdsOfTheFrameworkAreAskedAndOnlyThroughIsEnabledForAnyone(): void {
		self::assertFalse($this->service([])->active());

		self::assertSame(ParallelSearchService::APP_IDS, $this->asked);
	}

	public function testTheAppIdsAreTheTwoAppsThatReachTheSearchBar(): void {
		self::assertSame(['fulltextsearch', 'files_fulltextsearch'], ParallelSearchService::APP_IDS);
	}

	public function testAPlatformAppAloneIsNoHint(): void {
		self::assertFalse($this->service(['fulltextsearch_elasticsearch', 'fulltextsearch_sql', 'fulltextsearch_postgresql'])->active());
	}
}
