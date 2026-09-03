<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\ExAppService;
use OCP\App\IAppManager;
use OCP\Http\Client\IResponse;
use OCP\IAppConfig;
use OCP\IUserManager;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * Behaviours 1 to 3, 7, 8 and 12 of docs/testing.md, section "The gap".
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
 *
 * Behaviours 7, 8 and 12 arrived with plan 05-16 and go through the public
 * methods instead, because all three are statements about a round trip: that one
 * does not happen (7), that an answer is refused before it is parsed (8), and
 * what survives of an answer that was parsed (12). What stands in for the
 * transport is a test double of ExAppService::proxyRequest, which is the one
 * method of this class that reaches AppAPI. Doubling it rather than the class
 * behind it is not a shortcut: OCA\AppAPI\PublicFunctions belongs to another app
 * and is absent from the autoload space of this suite, so there is nothing there
 * to double.
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

	// -- the transport double, shared by behaviours 7, 8 and 12 ---------------

	/**
	 * The service with its one outbound method replaced and nothing else.
	 *
	 * Everything above the transport is the real code: the empty term check, the
	 * clamping, the budget gate, the four failure cases and both filters. What is
	 * scripted is only what the container would have answered.
	 *
	 * @return ExAppService&MockObject
	 */
	private function service(?LoggerInterface $logger = null): ExAppService&MockObject {
		return $this->getMockBuilder(ExAppService::class)
			->setConstructorArgs([
				$this->createMock(IAppManager::class),
				$this->createMock(IUserManager::class),
				$this->createMock(IAppConfig::class),
				$logger ?? $this->createMock(LoggerInterface::class),
			])
			->onlyMethods(['proxyRequest'])
			->getMock();
	}

	/**
	 * An answer of the container: a status code and a body, and nothing else of
	 * the response object is ever read by the code under test.
	 *
	 * @return IResponse&MockObject
	 */
	private function answer(string $body, int $status = 200): IResponse&MockObject {
		$response = $this->createMock(IResponse::class);
		$response->method('getStatusCode')->willReturn($status);
		$response->method('getBody')->willReturn($body);

		return $response;
	}

	/**
	 * A constant of the class under test, read rather than copied.
	 *
	 * The same rule as the canary title above and for the same reason: a number
	 * written into this file is a number that keeps being asserted after somebody
	 * changed it in the class, and a bound that silently stopped being the bound
	 * is worse than no test of it.
	 */
	private function constantInt(string $name): int {
		$value = (new \ReflectionClass(ExAppService::class))->getConstant($name);

		self::assertIsInt($value, $name . ' is gone or is no longer an int');

		return $value;
	}

	private function constantFloat(string $name): float {
		$value = (new \ReflectionClass(ExAppService::class))->getConstant($name);

		self::assertIsFloat($value, $name . ' is gone or is no longer a float');

		return $value;
	}

	// -- behaviour 7: no round trip for an empty term, and a clamped limit ----

	public function testAnEmptyTermIsRefusedWithoutASingleRoundTrip(): void {
		$service = $this->service();

		// The load bearing half of this case. A test that only looked at the null
		// could not tell "refused here" from "asked and got nothing back", and
		// "without a round trip" is the whole property: the unified search sends
		// the term of the moment on every keystroke, so an empty one that reached
		// the container would be one proxy round trip per key pressed for a
		// request that can only ever answer 422.
		$service->expects(self::never())->method('proxyRequest');

		self::assertNull($service->searchCandidates('alice', '   ', 20, 0, false));
	}

	/**
	 * The limit that actually reached the container for a given requested one.
	 */
	private function limitThatReachedTheContainer(int $requested): int {
		$service = $this->service();
		$seen = null;

		$service->method('proxyRequest')->willReturnCallback(
			function (string $path, string $userId, string $method, array $params, float $timeout) use (&$seen): IResponse {
				$seen = $params['limit'] ?? null;

				return $this->answer('{"candidates":[],"hasMore":false,"nextOffset":0}');
			},
		);

		$service->searchCandidates('alice', 'quarterly report', $requested, 0, false);

		self::assertIsInt($seen, 'the container was never asked, so no limit reached it');

		return $seen;
	}

	public function testALimitBelowTheAcceptedRangeIsClampedToTheLowerBound(): void {
		$min = $this->constantInt('MIN_LIMIT');

		// Clamping rather than passing on, because the range is the one the
		// backend validates: outside it the request fails over there with a 422,
		// which arrives here as an empty result group and is indistinguishable
		// from "nothing found".
		self::assertLessThan($min, 0);
		self::assertSame($min, $this->limitThatReachedTheContainer(0));
	}

	public function testALimitAboveTheAcceptedRangeIsClampedToTheUpperBound(): void {
		$max = $this->constantInt('MAX_LIMIT');

		self::assertGreaterThan($max, 1000);
		self::assertSame($max, $this->limitThatReachedTheContainer(1000));
	}

	public function testALimitInsideTheAcceptedRangeIsPassedOnUnchanged(): void {
		$min = $this->constantInt('MIN_LIMIT');
		$max = $this->constantInt('MAX_LIMIT');

		// The two guards keep this case from quietly turning into a third copy of
		// one of the two above should the bounds ever move around the 50.
		self::assertGreaterThan($min, 50);
		self::assertLessThan($max, 50);

		self::assertSame(50, $this->limitThatReachedTheContainer(50));
	}

	// -- behaviour 11, the half that lives in this class ----------------------

	public function testASpentBudgetCostsNoRoundTripForCandidatesAndNoneForExcerpts(): void {
		// Behaviour 11 says excerpts are not requested at all once the budget is
		// gone. The provider hands down what is left of its wall clock, and this
		// is the end that refuses: below the floor no call is placed, because an
		// answer that arrives after the unified search stopped waiting costs a
		// round trip and buys nothing. ProviderTest asserts the other end, that
		// the number handed down really is below this floor.
		$floor = $this->constantFloat('MIN_CALL_SECONDS');
		$service = $this->service();
		$service->expects(self::never())->method('proxyRequest');

		self::assertNull($service->searchCandidates('alice', 'quarterly report', 20, 0, false, $floor / 2));
		self::assertSame([], $service->snippets('alice', 'quarterly report', [11, 22], false, $floor / 2));
	}

	// -- behaviour 8: the cap on the answer body, before the parser -----------

	/**
	 * A well formed JSON answer of exactly the requested number of bytes.
	 */
	private function jsonBodyOfExactly(int $bytes): string {
		$prefix = '{"candidates":[],"pad":"';
		$suffix = '"}';
		$padding = $bytes - strlen($prefix) - strlen($suffix);

		self::assertGreaterThan(0, $padding, 'the cap is too small for this helper to build a body');

		$body = $prefix . str_repeat('x', $padding) . $suffix;
		self::assertSame($bytes, strlen($body));

		return $body;
	}

	/**
	 * What one answer body costs: the return value, and every warning it left.
	 *
	 * @return array{result:?array<mixed>,warnings:list<array{0:string,1:array<mixed>}>}
	 */
	private function outcomeFor(string $body): array {
		$warnings = [];
		$logger = $this->createMock(LoggerInterface::class);
		$logger->method('warning')->willReturnCallback(
			function (string|\Stringable $message, array $context = []) use (&$warnings): void {
				$warnings[] = [(string)$message, $context];
			},
		);

		$service = $this->service($logger);
		$service->method('proxyRequest')->willReturn($this->answer($body));

		return [
			'result' => $service->searchCandidates('alice', 'quarterly report', 20, 0, false),
			'warnings' => $warnings,
		];
	}

	public function testAnAnswerAtTheBodyCapIsStillParsed(): void {
		$outcome = $this->outcomeFor($this->jsonBodyOfExactly($this->constantInt('MAX_BODY_BYTES')));

		self::assertNotNull($outcome['result'], 'the cap is a ceiling and not a smaller number in disguise');
		self::assertSame([], $outcome['result']['candidates']);
		self::assertSame([], $outcome['warnings']);
	}

	public function testAnAnswerAboveTheBodyCapIsRefusedBeforeItIsParsed(): void {
		$cap = $this->constantInt('MAX_BODY_BYTES');

		$wellFormed = $this->outcomeFor($this->jsonBodyOfExactly($cap + 1));
		$garbage = $this->outcomeFor(str_repeat('x', $cap + 1));

		self::assertNull($wellFormed['result']);
		self::assertNull($garbage['result']);

		// The statement of behaviour 8 in one assertion. Both bodies are one byte
		// over the cap and are the same number of bytes long, and only one of
		// them is JSON. Had either of them reached json_decode, the one that is
		// not JSON would have taken the other exit and left the other line
		// behind. Identical outcomes mean the length was judged first.
		self::assertSame($wellFormed['warnings'], $garbage['warnings']);
		self::assertCount(1, $garbage['warnings']);
	}

	public function testAnAnswerBelowTheCapThatIsNotJsonTakesTheOtherExit(): void {
		// The counter proof to the case above, and it is what keeps that case
		// from being green for the wrong reason: without it, "the two oversized
		// bodies left the same line" would also hold if both of them had reached
		// the parser.
		$cap = $this->constantInt('MAX_BODY_BYTES');

		$small = $this->outcomeFor('this is not JSON either, and it fits');
		$large = $this->outcomeFor(str_repeat('x', $cap + 1));

		self::assertNull($small['result']);
		self::assertNull($large['result']);
		self::assertCount(1, $small['warnings']);
		self::assertNotSame(
			$small['warnings'][0][0],
			$large['warnings'][0][0],
			'a body that was parsed and a body that was refused before the parser leave the same line, so the order is not observable',
		);
	}

	// -- behaviour 12: which excerpts survive, and which highlights -----------

	/**
	 * @param list<int> $wanted
	 * @param array<int,mixed> $answer
	 * @return array<int,array{text:string,highlights:list<array{int,int}>}>
	 */
	private function snippetsFor(array $wanted, array $answer): array {
		$service = $this->service();
		$body = json_encode(['snippets' => $answer]);
		self::assertIsString($body);
		$service->method('proxyRequest')->willReturn($this->answer($body));

		return $service->snippets('alice', 'quarterly report', $wanted, false);
	}

	public function testAnExcerptForAFileIdThatWasNotAskedForIsDropped(): void {
		// The container runs an access prefilter of its own, and that prefilter is
		// not the boundary. An excerpt for a file this request never confirmed has
		// no way of reaching the screen from here.
		$result = $this->snippetsFor([11], [
			11 => ['text' => 'the excerpt that was asked for', 'highlights' => []],
			22 => ['text' => 'an excerpt for a file nobody asked about', 'highlights' => []],
		]);

		self::assertSame([11], array_keys($result));
	}

	public function testTheHighlightRangesOfATextTheCleaningShortenedAreDropped(): void {
		$cap = $this->constantInt('MAX_SNIPPET_LENGTH');
		$raw = str_repeat('a', $cap + 10);

		$result = $this->snippetsFor([11], [11 => ['text' => $raw, 'highlights' => [[0, 5]]]]);

		self::assertSame(str_repeat('a', $cap), $result[11]['text']);

		// The range above would still sit inside the shortened text, and it goes
		// all the same. Once the cleaning has cut, nothing here can tell which
		// offsets still point at the character they were measured against, so the
		// only answer that cannot mislead is none of them.
		self::assertSame([], $result[11]['highlights']);
	}

	public function testTheHighlightRangesOfATextThatOnlyChangedCharactersSurvive(): void {
		// The everyday case, and the reason the comparison is length and not
		// identity: pypdfium2 joins the lines of a page with CR LF, so an excerpt
		// out of an ordinary two line PDF carries control characters, and the
		// cleaning turns each of them into exactly one space. One character for
		// one character moves no offset, so these ranges still point at the word
		// they were measured against.
		$raw = "Line one\r\nLine two";

		$result = $this->snippetsFor([11], [11 => ['text' => $raw, 'highlights' => [[0, 4]]]]);

		self::assertSame('Line one  Line two', $result[11]['text']);
		self::assertSame([[0, 4]], $result[11]['highlights']);
		self::assertSame(
			mb_strlen($raw, 'UTF-8'),
			mb_strlen($result[11]['text'], 'UTF-8'),
			'the cleaning stopped preserving the length, which is what these offsets rely on',
		);
	}
}
