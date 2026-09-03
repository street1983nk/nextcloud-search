<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\ExAppService;
use OCP\App\IAppManager;
use OCP\IAppConfig;
use OCP\IUserManager;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * Behaviours 1 to 3 of docs/testing.md, section "The gap".
 *
 * What they defend, in one sentence, because the test names below say what holds
 * and not why: the container has no way of knowing what a user may see, so
 * everything it sends is a proposal, and a proposal that reaches the screen
 * before the recheck in Provider is the information disclosure the whole two
 * stage protocol exists to prevent. Behaviour 3 is the load bearing one of the
 * three. Behaviours 1 and 2 keep the diagnostic exception narrow; behaviour 3 is
 * what makes an ordinary candidate unable to carry anything displayable at all.
 *
 * filterCandidates is private, so it is reached through reflection rather than
 * through searchCandidates. That is deliberate: going through the public method
 * would mean going through AppAPI, which is a round trip, a container and a
 * registration, and none of those are what these three statements are about.
 *
 * The four constructor arguments are mocks and are never used by the method
 * under test except for the logger, which counts the drops.
 */
#[CoversClass(ExAppService::class)]
final class ExAppServiceTest extends TestCase {
	/**
	 * The canary title, read out of the class instead of copied into this file.
	 *
	 * Copying it would make a rename of the constant a silent pass: the test
	 * would keep asserting the old string, the container and the app would agree
	 * on a new one, and the one candidate that is allowed through without a file
	 * behind it would quietly become a different one. Reading it here means a
	 * rename either keeps the tests honest or breaks them loudly.
	 */
	private function canaryTitle(): string {
		$value = (new \ReflectionClass(ExAppService::class))->getConstant('CANARY_TITLE');

		self::assertIsString($value, 'CANARY_TITLE is gone or is no longer a string');

		return $value;
	}

	/**
	 * @param array<mixed> $candidates
	 * @return list<array{fileId:int,title?:string,snippet?:string}>
	 */
	private function filter(array $candidates, ?LoggerInterface $logger = null): array {
		$service = new ExAppService(
			$this->createMock(IAppManager::class),
			$this->createMock(IUserManager::class),
			$this->createMock(IAppConfig::class),
			$logger ?? $this->createMock(LoggerInterface::class),
		);

		$method = new \ReflectionMethod(ExAppService::class, 'filterCandidates');

		/** @var list<array{fileId:int,title?:string,snippet?:string}> $kept */
		$kept = $method->invoke($service, $candidates);

		return $kept;
	}

	// -- behaviour 1 ---------------------------------------------------------

	public function testACandidateWithNoFileIdAtAllIsDropped(): void {
		self::assertSame([], $this->filter([['title' => 'anything', 'snippet' => 'anything']]));
	}

	/**
	 * @return array<string,array{mixed}>
	 */
	public static function fileIdsThatAreNotIntegers(): array {
		return [
			'a string, even a numeric one' => ['7'],
			'a float that happens to be whole' => [7.0],
			'null' => [null],
			'an array' => [[7]],
			'a bool' => [true],
		];
	}

	#[DataProvider('fileIdsThatAreNotIntegers')]
	public function testACandidateWhoseFileIdIsNotAnIntegerIsDropped(mixed $fileId): void {
		self::assertSame([], $this->filter([['fileId' => $fileId, 'title' => 'anything']]));
	}

	public function testSomethingThatIsNotACandidateShapeAtAllIsDropped(): void {
		self::assertSame([], $this->filter(['a bare string', 42, null]));
	}

	// -- behaviour 2 ---------------------------------------------------------

	/**
	 * @return array<string,array{int}>
	 */
	public static function nonPositiveFileIds(): array {
		return [
			'zero' => [0],
			'negative' => [-1],
		];
	}

	#[DataProvider('nonPositiveFileIds')]
	public function testACandidateWithoutAFileBehindItIsDroppedUnlessItIsTheCanary(int $fileId): void {
		$kept = $this->filter([[
			'fileId' => $fileId,
			'title' => 'a title that is not the canary',
			'snippet' => 'and a snippet to go with it',
		]]);

		self::assertSame([], $kept);
	}

	public function testTheCanaryIsTheOneCandidateWithoutAFileBehindItThatSurvives(): void {
		$canary = $this->canaryTitle();

		$kept = $this->filter([[
			'fileId' => 0,
			'title' => $canary,
			'snippet' => 'answered by findling-backend on host at 12:00',
		]]);

		self::assertSame([[
			'fileId' => 0,
			'title' => $canary,
			'snippet' => 'answered by findling-backend on host at 12:00',
		]], $kept);
	}

	public function testTheCanaryWithoutASnippetIsDroppedLikeAnyOtherMalformedCandidate(): void {
		$kept = $this->filter([[
			'fileId' => 0,
			'title' => $this->canaryTitle(),
		]]);

		self::assertSame([], $kept);
	}

	// -- behaviour 3, the load bearing one -----------------------------------

	public function testEveryCandidateWithAPositiveFileIdLosesItsTitleAndItsSnippet(): void {
		// Both fields are set in the input on purpose. A container that sends
		// them is not a hypothetical: the answer model has room for them, and
		// what this asserts is that having room is not the same as being
		// displayed. Nothing the container volunteers before the recheck can
		// reach the screen, because nothing of it survives this method.
		$kept = $this->filter([[
			'fileId' => 4711,
			'title' => 'Salary of the board.pdf',
			'snippet' => 'the part of a foreign document a user must not see',
		]]);

		self::assertSame([['fileId' => 4711]], $kept);
		self::assertArrayNotHasKey('title', $kept[0]);
		self::assertArrayNotHasKey('snippet', $kept[0]);
	}

	public function testTheStrippingHoldsForEveryCandidateOfAPageAndNotOnlyTheFirst(): void {
		$kept = $this->filter([
			['fileId' => 1, 'title' => 'first.pdf', 'snippet' => 'first excerpt'],
			['fileId' => 2, 'title' => 'second.pdf', 'snippet' => 'second excerpt'],
			['fileId' => 3, 'title' => 'third.pdf', 'snippet' => 'third excerpt'],
		]);

		self::assertSame([['fileId' => 1], ['fileId' => 2], ['fileId' => 3]], $kept);
	}

	public function testAPageMixingTheCanaryWithOrdinaryHitsKeepsBothRulesApart(): void {
		$canary = $this->canaryTitle();

		$kept = $this->filter([
			['fileId' => 9, 'title' => 'volunteered.pdf', 'snippet' => 'volunteered excerpt'],
			['fileId' => 0, 'title' => $canary, 'snippet' => 'diagnostic text'],
			['fileId' => 0, 'title' => 'not the canary', 'snippet' => 'dropped'],
		]);

		self::assertSame([
			['fileId' => 9],
			['fileId' => 0, 'title' => $canary, 'snippet' => 'diagnostic text'],
		], $kept);
	}

	public function testTheDroppedCandidatesAreCountedInOneLogLineAndNotNamed(): void {
		// The counter is the only trace a malformed page leaves, and it carries a
		// number rather than the candidates: a log line with container supplied
		// text in it would move the disclosure from the search dialog into the
		// Nextcloud log instead of preventing it.
		$logger = $this->createMock(LoggerInterface::class);
		$logger->expects(self::once())
			->method('warning')
			->with('Findling: dropped malformed candidates', ['count' => 2]);

		$this->filter([
			['fileId' => 5],
			['fileId' => 'not an integer'],
			['fileId' => 0, 'title' => 'not the canary', 'snippet' => 'dropped'],
		], $logger);
	}
}
