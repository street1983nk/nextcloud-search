<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\AdminViewService;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * The three judgements of the status page that can be asked without a
 * Nextcloud: the stall verdict (DI-05-22), the coverage figures (D-16) and the
 * state of the embedding engine (plan 07-04).
 *
 * Both are static and public for the same reason, and the reason is written out
 * at each of them: they are the arithmetic and nothing else, and the
 * alternative to reaching them directly is a unit test which builds a whole
 * admin view out of twelve doubles in order to ask what a fraction of two
 * numbers comes to. Everything around them, the reading and the writing of
 * appconfig and the assembly of the answer, stays in the page where it cannot
 * be tested without a server anyway.
 *
 * The first half of this file, the stall verdict:
 *
 * What this defends. The page used to measure one thing, how long ago the last
 * background job of this app ran, and it called everything above half an hour a
 * stall. In the full run of plan 05-14 the crawl finished at 01:30Z and the
 * container wrote roughly 6.500 more documents until 09:27Z, so for eight hours,
 * over the majority of the run, the page said "Indexing has not progressed"
 * while the coverage figure in the same row climbed from 82 to 99 per cent. On
 * an ordinary instance the two halves end together and nobody notices; on the
 * hardware this product is built for the OCR pass is 77 per cent of the run.
 *
 * Why this asks a static method instead of the page. The verdict is built out of
 * a background job stamp, a counter of the container and the counter this side
 * remembered from the poll before, and everything interesting about it is the
 * arithmetic over those numbers. Asking it through overview() would mean twelve
 * doubles, a status answer and a scan statistic in order to find out what a
 * counter that grew by one means, and the answer would be buried in the setup.
 * The reading and the writing of appconfig stay in the page, where they cannot
 * be tested without a Nextcloud anyway.
 *
 * The two sides of the boundary are the two groups below: a counter that grew is
 * progress and ends the stall, and everything else leaves the previous stamp
 * standing, which is what keeps the old verdict intact for the case it was
 * always right about.
 */
#[CoversClass(AdminViewService::class)]
final class AdminViewServiceTest extends TestCase {
	/** A poll, as a Unix timestamp. Any fixed number does; this one is readable. */
	private const NOW = 1_800_000_000;

	/** The stamp of an earlier progress, an hour before this poll. */
	private const EARLIER = self::NOW - 3600;

	// -- the first side: the counter grew, so it is not a stall ---------------

	public function testACounterThatGrewIsProgressAndStampsThisPoll(): void {
		// The OCR pass of the measured run, in one line: the crawl is long over,
		// no background job of this app has anything to do, and the container is
		// writing documents. That is the case the page accused for eight hours.
		$stamp = AdminViewService::progressStamp(true, 43_600, 43_599, self::EARLIER, self::NOW);

		self::assertSame(self::NOW, $stamp);
	}

	public function testProgressOutranksAnOldBackgroundJob(): void {
		// The verdict itself, as far as it can be asked here: the age the page
		// reports is the age of the LATER of the two movements. With the
		// container moving, the job stamp of eight hours ago does not decide.
		$jobRun = self::NOW - 30_000;
		$stamp = AdminViewService::progressStamp(true, 50_000, 43_600, self::EARLIER, self::NOW);

		self::assertSame(0, self::NOW - max($jobRun, $stamp));
	}

	// -- the other side: nothing moved, so the old verdict stands -------------

	/**
	 * Four ways of not being progress, and every one of them has to leave the
	 * previous stamp exactly as it was. An unchanged answer is also the signal
	 * that nothing has to be written, so a branch that returned the current time
	 * here would additionally turn a page that polls every five seconds into an
	 * appconfig write every five seconds.
	 *
	 * @return array<string,array{bool,int,int}>
	 */
	public static function everythingThatIsNotProgress(): array {
		return [
			'the counter stands still' => [true, 43_600, 43_600],
			'the counter fell, which is a reindex and not progress' => [true, 12, 43_600],
			'the container does not answer at all' => [false, 43_600, 43_599],
			'the first answer this instance has ever seen' => [true, 43_600, 0],
		];
	}

	#[DataProvider('everythingThatIsNotProgress')]
	public function testWithoutProgressTheEarlierStampStands(bool $reachable, int $indexed, int $remembered): void {
		$stamp = AdminViewService::progressStamp($reachable, $indexed, $remembered, self::EARLIER, self::NOW);

		self::assertSame(self::EARLIER, $stamp);
	}

	public function testWithoutProgressAnOldBackgroundJobStillDecides(): void {
		// The case the old verdict was right about, unchanged: work is waiting,
		// the last job is eight hours old and the container has finished nothing
		// in the meantime. The page has to keep saying so.
		$jobRun = self::NOW - 30_000;
		$stamp = AdminViewService::progressStamp(true, 43_600, 43_600, 0, self::NOW);

		self::assertSame(30_000, self::NOW - max($jobRun, $stamp));
	}

	public function testAnInstanceWithNoJobAndNoProgressHasNoAgeAtAll(): void {
		// Nought and not "since the epoch". A fresh installation has no movement
		// to measure the age of, and the page answers that with its own state,
		// never with a span of fifty five years.
		$stamp = AdminViewService::progressStamp(true, 0, 0, 0, self::NOW);

		self::assertSame(0, max(0, $stamp));
	}

	// -- the two coverage figures: one calculation, two numerators ------------

	/**
	 * What the page shows during the embedding pass, in one line: the full text
	 * half is complete and the semantic half is a quarter of the way through.
	 *
	 * The two figures come out of one call each of the same method, with the
	 * same denominator, and that is what makes putting them next to each other
	 * honest (D-16). Two calculations for one kind of number would agree on the
	 * day they are written and drift on the day one of them is corrected, and
	 * nothing on the page would show it.
	 */
	public function testBothFiguresComeOutOfOneCalculationOverOneDenominator(): void {
		$indexable = 200;

		$indexed = AdminViewService::coverageShare(200, $indexable, true);
		$embedded = AdminViewService::coverageShare(50, $indexable, true);

		self::assertSame(100, $indexed);
		self::assertSame(25, $embedded);
		// The property that makes the pair readable: as long as fewer documents
		// carry a vector than have been judged, the second figure cannot be the
		// larger one. It holds because both go through one calculation.
		self::assertLessThanOrEqual($indexed, $embedded);
	}

	public function testTheSecondFigureStaysBelowAHundredWhileDocumentsWithoutVectorsAreLeft(): void {
		// One document of two hundred is missing, and floor() alone would round
		// that to a hundred. A page that says a hundred per cent with files left
		// over is the failure this whole phase exists to make impossible.
		self::assertSame(99, AdminViewService::coverageShare(199, 200, true));
		self::assertSame(99, AdminViewService::coverageShare(1_999, 2_000, true));
		self::assertSame(100, AdminViewService::coverageShare(200, 200, true));
	}

	/**
	 * Four ways of having no honest figure, and all four answer null.
	 *
	 * The second row carries two readings of this plan and they are one argument
	 * here on purpose: a container that is silent and a container that does not
	 * report the embedded count at all both leave this method without a
	 * numerator, and both have to answer null rather than nought. Which of the
	 * two happened is decided in coverage(), where the missing key becomes the
	 * false this row passes in.
	 *
	 * @return array<string,array{int,int,bool}>
	 */
	public static function everythingWithoutAnHonestFigure(): array {
		return [
			'no denominator, because nothing has been counted yet' => [0, 0, true],
			'no numerator, because the container is silent or did not report it' => [0, 200, false],
			// Quick task 260929-kii: more indexed than the denominator holds is
			// the window until the next recount, and it is no share at all, least
			// of all a hundred per cent.
			'more counted than indexable, because the recount has not caught up' => [300, 200, true],
			'one more counted than indexable' => [201, 200, true],
		];
	}

	#[DataProvider('everythingWithoutAnHonestFigure')]
	public function testWithoutAnHonestFigureTheAnswerIsNullAndNotNought(
		int $counted,
		int $indexable,
		bool $available,
	): void {
		self::assertNull(AdminViewService::coverageShare($counted, $indexable, $available));
	}

	public function testAFigureIsNeverNegativeAndNeverAboveAHundred(): void {
		// A negative input cannot legitimately occur, and it would be visible as
		// a defect of the page rather than of whatever produced it. A progress
		// bar with a negative value renders as an empty bar and says nothing.
		// The other end, a counter above the denominator, is null since quick
		// task 260929-kii and sits in the provider above; a hundred is reached
		// exactly when the two are equal.
		self::assertSame(0, AdminViewService::coverageShare(-5, 200, true));
		self::assertSame(100, AdminViewService::coverageShare(200, 200, true));
		self::assertSame(99, AdminViewService::coverageShare(199, 200, true));
	}

	// -- the state of the engine: six words, and null for everything else -----

	/**
	 * The six words the container may send, each of them passed through.
	 *
	 * They are the protocol and they are decided in the container, in
	 * backend/src/findling/embed/engine.py. This side does not translate them
	 * and does not shorten them; it decides whether the value is one of them,
	 * and the page picks the sentence an admin reads.
	 *
	 * @return array<string,array{string}>
	 */
	public static function everyStateOfTheEngine(): array {
		return [
			'the weights are in memory' => ['loaded'],
			'nothing has asked for a vector yet' => ['cold'],
			'the semantic half is switched off' => ['disabled'],
			'there is no model in the image' => ['missing'],
			'a load threw and the cooldown is running' => ['waiting_for_retry'],
			'the weights were given back in an idle span' => ['unloaded'],
		];
	}

	#[DataProvider('everyStateOfTheEngine')]
	public function testAWordOfTheClosedListIsPassedThrough(string $state): void {
		self::assertSame($state, AdminViewService::engineState($state));
	}

	public function testAContainerThatDoesNotReportTheStateDoesNotProduceColdOnThePage(): void {
		// T-07-03, and the reason this judgement answers null rather than a
		// word. A container older than this app leaves the key out, so what
		// arrives here is null, and cold would promise a load on first demand
		// on an instance that has not said anything at all. An update in the
		// wrong order is the ordinary way to be in this state, and the page has
		// a sentence of its own for it.
		self::assertNull(AdminViewService::engineState(null));
	}

	/**
	 * Everything that is not one of the six words, and none of it is cast.
	 *
	 * The last three rows are the ones a cast would ruin quietly: (string)3 is
	 * "3", (string)true is "1", and both would look like a value this side
	 * decided rather than like a value it refused.
	 *
	 * @return array<string,array{mixed}>
	 */
	public static function everythingThatIsNotAStateOfTheEngine(): array {
		return [
			'a word from a later release' => ['unloading'],
			'the empty string' => [''],
			'a sentence instead of a state' => ['the model is fine'],
			'markup' => ['<b>cold</b>'],
			'a word of the list in the wrong case' => ['Cold'],
			'a number' => [3],
			'a boolean' => [true],
			'a list' => [['cold']],
		];
	}

	#[DataProvider('everythingThatIsNotAStateOfTheEngine')]
	public function testAValueOutsideTheClosedListIsRefusedAndNeverCast(mixed $value): void {
		// T-07-02. This value decides which sentence an admin reads as a
		// recommendation, and it comes from across the trust boundary.
		self::assertNull(AdminViewService::engineState($value));
	}

	// -- the precision of the model and the re-embedding run (plan 25-04) -----

	public function testAValidPrecisionAndARunningReEmbeddingArePassedThrough(): void {
		// The contract of plan 25-12: an object "model" in the status answer,
		// read here for exactly two of its fields.
		$answer = ['model' => ['precisionActive' => 'fp32', 'reembedRunning' => true]];

		self::assertSame('fp32', AdminViewService::precision(AdminViewService::modelField($answer, 'precisionActive')));
		self::assertTrue(AdminViewService::strictFlag(AdminViewService::modelField($answer, 'reembedRunning')));
		self::assertSame('int8', AdminViewService::precision('int8'));
		self::assertFalse(AdminViewService::strictFlag(false));
	}

	/**
	 * Answers without a usable model object, and every one of them is null.
	 *
	 * A container older than this app leaves the object out, and null is the
	 * only value that keeps that apart from a container that reported int8 and
	 * no running re-embedding (T-07-03). The line on the page stays hidden then.
	 *
	 * @return array<string,array{array<mixed>}>
	 */
	public static function everyAnswerWithoutAModelObject(): array {
		return [
			'no answer at all' => [[]],
			'an answer of an older container' => [['indexed' => 3, 'engineState' => 'loaded']],
			'a model that is a string' => [['model' => 'e5-small fp32']],
			'a model that is a number' => [['model' => 3]],
			'a model without the two fields' => [['model' => ['precisionChosen' => 'fp32']]],
		];
	}

	/** @param array<mixed> $answer */
	#[DataProvider('everyAnswerWithoutAModelObject')]
	public function testAnAnswerWithoutAModelObjectGivesNullAndNeverAGuess(array $answer): void {
		self::assertNull(AdminViewService::precision(AdminViewService::modelField($answer, 'precisionActive')));
		self::assertNull(AdminViewService::strictFlag(AdminViewService::modelField($answer, 'reembedRunning')));
		self::assertNull(AdminViewService::precisionVerdict(AdminViewService::modelField($answer, 'precisionVerdict')));
	}

	// -- the verdict of the precision (phase 27, state Z13) -----------------

	public function testEveryKnownPrecisionVerdictIsPassedThrough(): void {
		foreach (['downloading', 'fp32_unavailable', 'fp32_not_in_economy', 'fp32_on_a_tight_box', 'fp32_active_in_economy'] as $verdict) {
			$answer = ['model' => ['precisionVerdict' => $verdict]];
			self::assertSame($verdict, AdminViewService::precisionVerdict(AdminViewService::modelField($answer, 'precisionVerdict')));
		}
	}

	public function testTheEmptyAndEveryUnknownPrecisionVerdictGiveNull(): void {
		foreach (['', 'FP32_UNAVAILABLE', 'fp32', '<b>x</b>', 3, true, null, ['fp32_unavailable']] as $value) {
			self::assertNull(AdminViewService::precisionVerdict($value));
		}
	}

	/**
	 * Everything that is not one of the two precisions, and none of it is cast.
	 *
	 * @return array<string,array{mixed}>
	 */
	public static function everythingThatIsNotAPrecision(): array {
		return [
			'a precision this page does not know' => ['fp16'],
			'the empty string' => [''],
			'a number' => [3],
			'a precision in the wrong case' => ['FP32'],
			'markup' => ['<b>fp32</b>'],
			'a boolean' => [true],
			'a list' => [['fp32']],
		];
	}

	#[DataProvider('everythingThatIsNotAPrecision')]
	public function testAValueOutsideTheTwoPrecisionsIsRefused(mixed $value): void {
		// T-25-13. The value becomes part of a line an admin reads, and it comes
		// from across the trust boundary.
		self::assertNull(AdminViewService::precision($value));
	}

	/**
	 * Everything that is not a real boolean, and none of it is read as one.
	 *
	 * @return array<string,array{mixed}>
	 */
	public static function everythingThatIsNotAFlag(): array {
		return [
			'a word' => ['yes'],
			'the string of true' => ['true'],
			'a one' => [1],
			'a nought' => [0],
			'null' => [null],
		];
	}

	#[DataProvider('everythingThatIsNotAFlag')]
	public function testAReEmbeddingFlagThatIsNotABooleanIsRefused(mixed $value): void {
		self::assertNull(AdminViewService::strictFlag($value));
	}

	// -- the memory guard and the OCR slots (plan 26-05) ----------------------

	/**
	 * The seven guard fields exactly as backend() builds them.
	 *
	 * @param array<mixed> $answer
	 * @return array<string,mixed>
	 */
	private static function guardFields(array $answer): array {
		return [
			'guardChosen' => AdminViewService::profileName(AdminViewService::guardField($answer, 'chosen')),
			'guardEffective' => AdminViewService::profileName(AdminViewService::guardField($answer, 'effective')),
			'guardCause' => AdminViewService::guardCause(AdminViewService::guardField($answer, 'cause')),
			'guardConfirmable' => AdminViewService::hexToken(AdminViewService::guardField($answer, 'token')) !== null,
			'slotsTarget' => AdminViewService::guardCounter(AdminViewService::guardField($answer, 'slotsTarget')),
			'slotsInForce' => AdminViewService::guardCounter(AdminViewService::guardField($answer, 'slotsInForce')),
			'slotsThrottled' => AdminViewService::strictFlag(AdminViewService::guardField($answer, 'throttled')),
		];
	}

	/**
	 * Answers without a usable guard object, and every field is null for them.
	 *
	 * @return array<string,array{array<mixed>}>
	 */
	public static function everyAnswerWithoutAGuardObject(): array {
		return [
			'no answer at all' => [[]],
			'an answer of a container older than 1.4' => [['indexed' => 3, 'engineState' => 'loaded']],
			'a guard that is a string' => [['guard' => 'performance']],
			'a guard that is a number' => [['guard' => 3]],
		];
	}

	/** @param array<mixed> $answer */
	#[DataProvider('everyAnswerWithoutAGuardObject')]
	public function testAnAnswerWithoutAGuardObjectLeavesEveryGuardFieldNull(array $answer): void {
		// D-26-01: a container older than 1.4 leaves the object out, and the
		// guard lines on the page stay hidden.
		foreach (self::guardFields($answer) as $field => $value) {
			if ($field === 'guardConfirmable') {
				// D-27-12: a flag, never null, and false without a token.
				self::assertFalse($value, $field);
				continue;
			}
			self::assertNull($value, $field);
		}
	}

	public function testAValidGuardObjectIsPassedThrough(): void {
		$token = str_repeat('0123456789abcdef', 2);
		$answer = ['guard' => [
			'chosen' => 'performance',
			'effective' => 'standard',
			'cap' => 'standard',
			'cause' => 'oom_kill',
			'since' => 1790000000,
			'token' => $token,
			'slotsTarget' => 4,
			'slotsInForce' => 2,
			'throttled' => true,
		]];

		self::assertSame([
			'guardChosen' => 'performance',
			'guardEffective' => 'standard',
			'guardCause' => 'oom_kill',
			'guardConfirmable' => true,
			'slotsTarget' => 4,
			'slotsInForce' => 2,
			'slotsThrottled' => true,
		], self::guardFields($answer));
		self::assertSame('memory_max_repeated', AdminViewService::guardCause('memory_max_repeated'));
		self::assertSame('unclean_end', AdminViewService::guardCause('unclean_end'));
		self::assertSame('economy', AdminViewService::profileName('economy'));
	}

	public function testTheEmptyCauseMeansNoReduction(): void {
		// The protocol reports "" while the guard lowered nothing.
		self::assertNull(AdminViewService::guardCause(''));
	}

	/**
	 * Values from outside the closed sets, and none of them is cut or cast.
	 *
	 * @return array<string,array{string,mixed}>
	 */
	public static function everyGuardValueOutsideItsSet(): array {
		return [
			'a cause with markup' => ['cause', 'evil<script>'],
			'a cause in the wrong case' => ['cause', 'OOM_KILL'],
			'a profile this page does not know' => ['chosen', 'turbo'],
			'an effective profile with markup' => ['effective', '<b>standard</b>'],
			'a token in upper case and too short' => ['token', 'ABC'],
			'a token one digit too long' => ['token', str_repeat('a', 33)],
			'a token with a newline' => ['token', str_repeat('a', 32) . "\n"],
			'a slot target as a string' => ['slotsTarget', '4'],
			'a negative slot count' => ['slotsInForce', -1],
			'a throttle flag of one' => ['throttled', 1],
		];
	}

	#[DataProvider('everyGuardValueOutsideItsSet')]
	public function testAGuardValueOutsideItsSetIsRefused(string $key, mixed $value): void {
		// T-26-15, T-26-16. These values become parts of lines an admin reads
		// and of a command an admin copies.
		$field = [
			'cause' => 'guardCause',
			'chosen' => 'guardChosen',
			'effective' => 'guardEffective',
			'token' => 'guardConfirmable',
			'slotsTarget' => 'slotsTarget',
			'slotsInForce' => 'slotsInForce',
			'throttled' => 'slotsThrottled',
		][$key];

		$judged = self::guardFields(['guard' => [$key => $value]])[$field];
		if ($field === 'guardConfirmable') {
			self::assertFalse($judged);
			return;
		}
		self::assertNull($judged);
	}

	// -- the profile surface of phase 27 (plan 27-08, UI-01) -------------------

	/**
	 * A status answer of a phase 27 container, with every object the surface
	 * reads.
	 *
	 * @return array<string,mixed>
	 */
	private static function profileAnswer(): array {
		return [
			'profile' => [
				'chosen' => 'performance',
				'suggested' => 'standard',
				'effective' => 'standard',
				'hardware' => [
					'cores' => 7.5,
					'coresWhole' => 7,
					'memoryLimitBytes' => 8_000_000_000,
					'memoryTotalBytes' => 16_000_000_000,
				],
				'values' => [
					'ocrDpi' => 200,
					'ocrMaxPages' => 50,
					'embedBatchSize' => 16,
					'writerHeapBytes' => 64_000_000,
					'ocrSlots' => 3,
				],
				'sources' => [
					'ocrDpi' => 'env',
					'ocrMaxPages' => 'profile',
					'embedBatchSize' => 'env',
					'writerHeapBytes' => 'env',
					'ocrSlots' => 'env',
				],
			],
			'probe' => ['supported' => true, 'running' => true, 'step' => 'ocr_one'],
			'model' => ['chunks' => 12_345],
		];
	}

	public function testTheProfileFieldsComeOnlyOutOfTheClosedSet(): void {
		$answer = self::profileAnswer();

		self::assertSame('performance', AdminViewService::profileName(AdminViewService::profileField($answer, 'chosen')));
		self::assertSame('standard', AdminViewService::profileName(AdminViewService::profileField($answer, 'suggested')));
		self::assertNull(AdminViewService::profileName(AdminViewService::profileField(['profile' => ['chosen' => 'turbo']], 'chosen')));
		self::assertNull(AdminViewService::profileField(['profile' => 'economy'], 'chosen'));
		self::assertNull(AdminViewService::profileField([], 'effective'));
	}

	public function testTheHardwareIsTakenOverOnlyAsNonNegativeIntegers(): void {
		$answer = self::profileAnswer();

		self::assertSame(7, AdminViewService::hardwareCores($answer));
		// The smaller of limit and physical memory, as the suggestion reads it.
		self::assertSame(8_000_000_000, AdminViewService::hardwareMemory($answer));
		self::assertNull(AdminViewService::hardwareCores(['profile' => ['hardware' => ['coresWhole' => '8']]]));
		self::assertNull(AdminViewService::hardwareCores(['profile' => ['hardware' => ['coresWhole' => -1]]]));
		self::assertNull(AdminViewService::hardwareMemory(['profile' => ['hardware' => ['memoryTotalBytes' => 1.5]]]));
		self::assertSame(4096, AdminViewService::hardwareMemory(['profile' => ['hardware' => ['memoryTotalBytes' => 4096]]]));
		self::assertNull(AdminViewService::hardwareMemory([]));
	}

	public function testEveryValueOfAnAdminVariableGetsOneLineWithTheNameOfTheMap(): void {
		// D-27-14: the variable name comes out of the PHP map, never out of the
		// answer; ocrSlots has source env but is not one of the four fields.
		self::assertSame([
			['field' => 'dpi', 'value' => 200, 'variable' => 'FINDLING_OCR_DPI'],
			['field' => 'batch', 'value' => 16, 'variable' => 'FINDLING_EMBED_BATCH_SIZE'],
			['field' => 'writer_heap', 'value' => 64_000_000, 'variable' => 'FINDLING_WRITER_HEAP_BYTES'],
		], AdminViewService::profileEnv(self::profileAnswer()));
	}

	public function testAForeignSourceOrAForeignValueProducesNoLine(): void {
		$answer = ['profile' => [
			'values' => ['ocrDpi' => '200', 'ocrMaxPages' => 50, 'embedBatchSize' => 8, 'foreign' => 1],
			'sources' => ['ocrDpi' => 'env', 'ocrMaxPages' => 'ENV', 'embedBatchSize' => '<b>env</b>', 'foreign' => 'env'],
		]];

		self::assertSame([], AdminViewService::profileEnv($answer));
		self::assertSame([], AdminViewService::profileEnv([]));
		self::assertSame([], AdminViewService::profileEnv(['profile' => ['values' => 'x', 'sources' => []]]));
	}

	public function testAMissingProbeObjectMeansNoProbeSupport(): void {
		// Z15: a container older than phase 27.
		self::assertFalse(AdminViewService::probeField([], 'supported') === true);
		self::assertFalse(AdminViewService::probeField(['probe' => 'yes'], 'supported') === true);
		self::assertFalse(AdminViewService::probeField(['probe' => ['supported' => 1]], 'supported') === true);
		self::assertTrue(AdminViewService::probeField(self::profileAnswer(), 'supported') === true);
		self::assertTrue(AdminViewService::probeField(self::profileAnswer(), 'running') === true);
	}

	public function testTheStepComesOnlyOutOfTheStepSet(): void {
		foreach (['pause', 'download', 'digest', 'model', 'ocr_one', 'calc', 'ocr_n', 'cleanup'] as $step) {
			self::assertSame($step, AdminViewService::stepCode($step));
		}
		self::assertSame('', AdminViewService::stepCode('warp'));
		self::assertSame('', AdminViewService::stepCode('OCR_ONE'));
		self::assertSame('', AdminViewService::stepCode(3));
		self::assertSame('', AdminViewService::stepCode(null));
	}

	/**
	 * A stored verdict as the probe flow writes it.
	 *
	 * @return array<string,mixed>
	 */
	private static function storedCheck(): array {
		return [
			'id' => '0123456789abcdef',
			'profile' => 'standard',
			'precision' => 'fp32',
			'verdict' => 'fits',
			'cause' => '',
			'numbers' => ['slots' => 2, 'need' => 900, 'rateInt8' => 40_000, 'rateFp32' => 12_500],
			'at' => 1_800_000_000,
			'committed' => true,
			'fp32Deleted' => false,
		];
	}

	public function testTheReindexDurationComesOnlyOutOfAMeasuredRate(): void {
		$check = AdminViewService::judgedCheck(self::storedCheck());

		// ceil(12345 / 12.5) = 988 and ceil(12345 / 40) = 309.
		self::assertSame(988, AdminViewService::reindexSeconds(12_345, AdminViewService::checkRate($check, 'rateFp32')));
		self::assertSame(309, AdminViewService::reindexSeconds(12_345, AdminViewService::checkRate($check, 'rateInt8')));
		self::assertSame(0, AdminViewService::reindexSeconds(0, 5));
		self::assertNull(AdminViewService::reindexSeconds(12_345, null));
		self::assertNull(AdminViewService::reindexSeconds(12_345, 0));
		self::assertNull(AdminViewService::checkRate(null, 'rateFp32'));

		$withoutRate = self::storedCheck();
		unset($withoutRate['numbers']['rateFp32']);
		self::assertNull(AdminViewService::checkRate(AdminViewService::judgedCheck($withoutRate), 'rateFp32'));
	}

	public function testAStoredVerdictIsJudgedAgainstItsSets(): void {
		self::assertSame([
			'profile' => 'standard',
			'precision' => 'fp32',
			'verdict' => 'fits',
			'cause' => '',
			'numbers' => ['slots' => 2, 'need' => 900, 'rateInt8' => 40_000, 'rateFp32' => 12_500],
			'at' => 1_800_000_000,
			'committed' => true,
			'fp32Deleted' => false,
		], AdminViewService::judgedCheck(self::storedCheck()));

		self::assertNull(AdminViewService::judgedCheck(null));
		foreach (['profile' => 'turbo', 'precision' => 'fp16', 'verdict' => 'maybe'] as $key => $value) {
			$stored = self::storedCheck();
			$stored[$key] = $value;
			self::assertNull(AdminViewService::judgedCheck($stored), $key);
		}

		// T-27-25: an occ-written cause, number or flag of another shape.
		$tampered = self::storedCheck();
		$tampered['cause'] = '<script>';
		$tampered['numbers'] = ['slots' => '2', 'need' => -1, 'evil' => 3, 'seconds' => 60];
		$tampered['committed'] = 1;
		$tampered['at'] = 'yesterday';
		$judged = AdminViewService::judgedCheck($tampered);
		self::assertNotNull($judged);
		self::assertSame('', $judged['cause']);
		self::assertSame(['seconds' => 60], $judged['numbers']);
		self::assertFalse($judged['committed']);
		self::assertSame(0, $judged['at']);
	}

	public function testTheFp32DownloadSizeIsTheReleaseSize(): void {
		self::assertSame(470268510, AdminViewService::FP32_DOWNLOAD_BYTES);
	}

	// -- the class of the reader error of one file (plan 29-06, D-29-09) ------

	public function testTheErrorClassOfTheContainerIsPassedThrough(): void {
		self::assertSame('zipfile.BadZipFile', AdminViewService::errorClass(['errorClass' => 'zipfile.BadZipFile']));
		self::assertSame('PIL.UnidentifiedImageError', AdminViewService::errorClass(['errorClass' => 'PIL.UnidentifiedImageError']));
	}

	public function testAContainerWithoutTheFieldGivesTheEmptyString(): void {
		// An older container leaves the key out, and a silent one answers with
		// nothing at all. Both read as "no class recorded" and never as an error.
		self::assertSame('', AdminViewService::errorClass([]));
		self::assertSame('', AdminViewService::errorClass(null));
	}

	/**
	 * Everything that is not the shape of a class name, and none of it is cast.
	 *
	 * @return array<string,array{mixed}>
	 */
	public static function everythingThatIsNotAnErrorClass(): array {
		return [
			'a path' => ['/geheim/pfad/Vertrag.pdf'],
			'a message' => ['zipfile.BadZipFile: File is not a zip file'],
			'markup' => ['<b>zipfile.BadZipFile</b>'],
			'too long' => [str_repeat('a', 201)],
			'a number' => [3],
			'a boolean' => [true],
			'a list' => [['zipfile.BadZipFile']],
		];
	}

	#[DataProvider('everythingThatIsNotAnErrorClass')]
	public function testAValueOutsideTheShapeOfAClassNameIsRefused(mixed $value): void {
		// T-29-18: the value comes from across the trust boundary and is printed
		// on the admin card and in a terminal.
		self::assertSame('', AdminViewService::errorClass(['errorClass' => $value]));
	}

	// -- the signature code of a refused file (plan 36-06, D-36-03) ----------

	public function testTheRowOfBlockedMaliciousCarriesTheAcceptedWording(): void {
		// 36-WORTLAUT A2, character for character.
		$table = (new \ReflectionClassConstant(AdminViewService::class, 'REASON_TEXT'))->getValue();

		self::assertIsArray($table);
		self::assertSame(
			[
				'File blocked as malicious',
				'None. The file carries the signature of an attack (see the detail) and is not read any further, so the container keeps running. Remove or replace the file if it is not meant to be there.',
			],
			$table['blocked_malicious'] ?? null,
		);
	}

	public function testASignatureCodeHasTheShapeOfAnErrorClass(): void {
		self::assertSame('zip_ratio', AdminViewService::errorClass(['errorClass' => 'zip_ratio']));
		self::assertSame('', AdminViewService::errorClass(['errorClass' => '../x']));
	}

	public function testASkippedCardCarriesTheSignatureCodeWhenTheContainerAgrees(): void {
		$container = ['state' => 'skipped', 'reason' => 'blocked_malicious', 'errorClass' => 'zip_ratio'];

		self::assertSame(
			'zip_ratio',
			AdminViewService::detailOfVerdict(['state' => 'skipped', 'reason' => 'blocked_malicious'], $container),
		);
	}

	public function testAFailedCardStillCarriesTheClassOfTheReaderError(): void {
		$container = ['state' => 'failed', 'reason' => 'corrupt', 'errorClass' => 'zipfile.BadZipFile'];

		self::assertSame(
			'zipfile.BadZipFile',
			AdminViewService::detailOfVerdict(['state' => 'failed', 'reason' => 'corrupt'], $container),
		);
	}

	/**
	 * Pairs of card and container that do not describe the same verdict.
	 *
	 * @return array<string,array{array<string,string>,array<string,string>}>
	 */
	public static function verdictsThatDisagree(): array {
		return [
			'skipped against failed' => [
				['state' => 'skipped', 'reason' => 'blocked_malicious'],
				['state' => 'failed', 'reason' => 'corrupt', 'errorClass' => 'zip_ratio'],
			],
			'another skipped reason' => [
				['state' => 'skipped', 'reason' => 'too_large'],
				['state' => 'skipped', 'reason' => 'blocked_malicious', 'errorClass' => 'zip_ratio'],
			],
			'indexed against skipped' => [
				['state' => 'indexed', 'reason' => ''],
				['state' => 'skipped', 'reason' => 'blocked_malicious', 'errorClass' => 'zip_ratio'],
			],
			'a code outside the shape' => [
				['state' => 'skipped', 'reason' => 'blocked_malicious'],
				['state' => 'skipped', 'reason' => 'blocked_malicious', 'errorClass' => '../x'],
			],
		];
	}

	/**
	 * @param array<string,string> $verdict
	 * @param array<string,string> $container
	 */
	#[DataProvider('verdictsThatDisagree')]
	public function testADetailNeverStandsNextToAVerdictItDidNotCause(array $verdict, array $container): void {
		self::assertSame('', AdminViewService::detailOfVerdict($verdict, $container));
	}

	// -- the diagnosis of an excluded file names both lists (plan 33-05) ----

	public function testTheRemedyOfAnExcludedFileNamesBothListsOfThePage(): void {
		// Read off the table the diagnosis translates, because the diagnosis
		// itself needs a file system. A file under a pattern is "excluded" like
		// a file under a prefix, and a remedy that named only the folder list
		// would send the admin to a list where no entry matches.
		$table = (new \ReflectionClassConstant(AdminViewService::class, 'REASON_TEXT'))->getValue();

		self::assertIsArray($table);
		self::assertSame(
			['Excluded by a rule', 'Remove the matching entry under "Excluded folders" or "Excluded patterns".'],
			$table['excluded'] ?? null,
		);
	}

	// -- the limits per file, read only (POL-01, plan 33-06) -----------------

	/**
	 * The judged view of backend() for one status answer.
	 *
	 * backend() is private and reads nothing but the answer, so it is asked
	 * through reflection on an instance without its constructor, instead of
	 * building the whole overview out of a dozen doubles.
	 *
	 * @param array<mixed>|null $answer
	 * @return array<string,mixed>
	 */
	private static function backendView(?array $answer): array {
		$service = (new \ReflectionClass(AdminViewService::class))->newInstanceWithoutConstructor();
		$view = (new \ReflectionMethod(AdminViewService::class, 'backend'))->invoke($service, $answer);
		self::assertIsArray($view);

		return $view;
	}

	public function testTheTwoNewLimitsOfTheContainerArePassedThrough(): void {
		$view = self::backendView(['maxFileBytes' => 52_428_800, 'maxCells' => 200_000, 'extractAddressSpaceBytes' => 536_870_912]);

		self::assertSame(200_000, $view['maxCells']);
		self::assertSame(536_870_912, $view['extractAddressSpaceBytes']);
	}

	public function testAContainerWithoutTheTwoFieldsGivesNullAndNotNought(): void {
		// A container of 1.4.x reports maxFileBytes and nothing of plan 33-03.
		// Nought would read as "no spreadsheet cell is read"; null hides the line.
		$view = self::backendView(['maxFileBytes' => 52_428_800]);

		self::assertNull($view['maxCells']);
		self::assertNull($view['extractAddressSpaceBytes']);
		self::assertNull(self::backendView(null)['maxCells']);
	}

	/**
	 * The judgement of optionalCounter(): a non negative integer or null, and
	 * nothing is cast (T-33-21).
	 *
	 * @return array<string,array{mixed}>
	 */
	public static function everythingThatIsNotALimit(): array {
		return [
			'a numeric string' => ['200000'],
			'a negative number' => [-1],
			'a fraction' => [1.5],
			'a boolean' => [true],
			'markup' => ['<b>200000</b>'],
			'a list' => [[200_000]],
		];
	}

	#[DataProvider('everythingThatIsNotALimit')]
	public function testALimitThatIsNotAWholeNumberIsRefused(mixed $value): void {
		$view = self::backendView(['maxCells' => $value, 'extractAddressSpaceBytes' => $value]);

		self::assertNull($view['maxCells']);
		self::assertNull($view['extractAddressSpaceBytes']);
	}

	public function testTheFourLimitsComeOutOfTheReadingsThatAlreadyExist(): void {
		$answer = self::profileAnswer();
		$backend = self::backendView($answer + ['maxCells' => 200_000, 'extractAddressSpaceBytes' => 536_870_912]);

		self::assertSame([
			'file' => ['value' => 52_428_800, 'variable' => 'FINDLING_MAX_FILE_BYTES', 'shown' => true],
			'address_space' => ['value' => 536_870_912, 'variable' => 'FINDLING_EXTRACT_ADDRESS_SPACE_BYTES', 'shown' => true],
			'cells' => ['value' => 200_000, 'variable' => 'FINDLING_MAX_CELLS', 'shown' => true],
			// Source profile: the entry names the profile in force.
			'pages' => ['value' => 50, 'variable' => 'FINDLING_OCR_MAX_PAGES', 'shown' => true, 'source' => 'profile', 'profile' => 'standard'],
		], AdminViewService::limits(52_428_800, $backend, $answer));
	}

	public function testAContainerOfOneFourHidesTheTwoNewLinesAndKeepsTheCeiling(): void {
		// The ceiling is the remembered one and stays; the two new limits and a
		// container without the object profile leave their lines hidden.
		$limits = AdminViewService::limits(52_428_800, self::backendView(['maxFileBytes' => 52_428_800]), []);

		self::assertSame(['value' => 52_428_800, 'variable' => 'FINDLING_MAX_FILE_BYTES', 'shown' => true], $limits['file']);
		self::assertSame(['value' => null, 'variable' => 'FINDLING_EXTRACT_ADDRESS_SPACE_BYTES', 'shown' => false], $limits['address_space']);
		self::assertSame(['value' => null, 'variable' => 'FINDLING_MAX_CELLS', 'shown' => false], $limits['cells']);
		self::assertSame(['value' => null, 'variable' => 'FINDLING_OCR_MAX_PAGES', 'shown' => false, 'source' => '', 'profile' => ''], $limits['pages']);
	}

	public function testAPageLimitSetByTheEnvironmentNamesNoProfile(): void {
		$answer = self::profileAnswer();
		$answer['profile']['sources']['ocrMaxPages'] = 'env';

		self::assertSame(
			['value' => 50, 'variable' => 'FINDLING_OCR_MAX_PAGES', 'shown' => true, 'source' => 'env', 'profile' => ''],
			AdminViewService::limits(52_428_800, [], $answer)['pages'],
		);
	}

	// -- Weg C: the coverage per counting key (plan 39-01, D-37-03) -----------

	/** One private method of the service, on an instance without its constructor. */
	private static function invokePrivate(string $method, mixed ...$arguments): mixed {
		$service = (new \ReflectionClass(AdminViewService::class))->newInstanceWithoutConstructor();

		return (new \ReflectionMethod(AdminViewService::class, $method))->invoke($service, ...$arguments);
	}

	/**
	 * The coverage block exactly as overview() assembles it, for one totals()
	 * answer and one status answer: leaveOutParameters, figures, coverage.
	 *
	 * @param array<string,mixed> $scan
	 * @param array<mixed>|null $answer
	 * @return array<string,mixed>
	 */
	private static function coverageOf(array $scan, ?array $answer, int $refused = 0, int $refusedLeftOut = 0, bool $rulesPending = false): array {
		$parameters = AdminViewService::leaveOutParameters($scan);
		$figures = self::invokePrivate('figures', $scan, $answer, $parameters, $refused, $refusedLeftOut);
		self::assertIsArray($figures);
		$coverage = self::invokePrivate(
			'coverage',
			$figures['scan'],
			$figures['backend'],
			$answer !== null,
			$figures['indexable'],
			$figures['refusedByType'],
			true,
			true,
			0,
			$figures['deduplicated'],
			$rulesPending,
		);
		self::assertIsArray($coverage);

		return $coverage;
	}

	/**
	 * A totals() answer: two storages of one share, both counted through, 100
	 * indexable files each, and the grouped set that keeps one of them.
	 *
	 * @param list<int> $leftOut
	 * @return array<string,mixed>
	 */
	private static function groupedScan(array $leftOut = [31]): array {
		$eight = static fn (int $files, int $mounts): array => [
			'filesSeen' => $files, 'bytesSeen' => $files * 1000, 'ocrCandidates' => 0, 'pdfSeen' => 0,
			'overCap' => 0, 'excluded' => 0, 'mountsTotal' => $mounts, 'mountsFinished' => $mounts,
		];

		return $eight(200, 2) + [
			'grouped' => $eight(100, 1),
			'leftOutStorageIds' => $leftOut,
			'groupsApplied' => $leftOut === [] ? 0 : 1,
		];
	}

	public function testOneShareForTwoUsersCountsOnceWhenTheContainerAnswersForTheOther(): void {
		$coverage = self::coverageOf(self::groupedScan(), [
			'indexed' => 200,
			'embedded' => 120,
			'indexedLeftOut' => 100,
			'embeddedLeftOut' => 60,
		]);

		self::assertSame(100, $coverage['indexable']);
		self::assertSame(100, $coverage['indexed']);
		self::assertSame(100, $coverage['percent']);
		self::assertFalse($coverage['duplicates']);
		self::assertTrue($coverage['deduplicated']);
		// The second figure over the same denominator, with the documents of
		// the left out storage taken out of its numerator as well.
		self::assertSame(60, $coverage['embedded']);
		self::assertSame(60, $coverage['embeddedPercent']);
		self::assertSame(1, $coverage['mountsTotal']);
		self::assertFalse($coverage['provisional']);
	}

	public function testAnOldContainerWithoutTheCountersGetsTheFigureOfOneFive(): void {
		// The same instance, a container of 1.5: no indexedLeftOut in the answer.
		$coverage = self::coverageOf(self::groupedScan(), ['indexed' => 150, 'embedded' => 0]);

		self::assertSame(200, $coverage['indexable']);
		self::assertSame(150, $coverage['indexed']);
		self::assertSame(75, $coverage['percent']);
		self::assertFalse($coverage['deduplicated']);
		// Settled, external storages on, a gap no failure explains: the
		// sentence of issue #25 as before.
		self::assertTrue($coverage['duplicates']);
	}

	public function testHalfAnAnswerIsNoDeduplication(): void {
		// The vector stock could not be read, so embeddedLeftOut is missing.
		$coverage = self::coverageOf(self::groupedScan(), ['indexed' => 200, 'embedded' => 0, 'indexedLeftOut' => 100]);

		self::assertSame(200, $coverage['indexable']);
		self::assertSame(200, $coverage['indexed']);
		self::assertFalse($coverage['deduplicated']);

		foreach ([-1, '100', 1.5, null, true] as $value) {
			self::assertNull(AdminViewService::leftOutCounts(['indexedLeftOut' => $value, 'embeddedLeftOut' => 0], true));
		}
		self::assertNull(AdminViewService::leftOutCounts(['indexedLeftOut' => 1, 'embeddedLeftOut' => 0], false));
		self::assertSame(['indexed' => 1, 'embedded' => 0], AdminViewService::leftOutCounts(['indexedLeftOut' => 1, 'embeddedLeftOut' => 0], true));
	}

	public function testAboveAThousandLeftOutStoragesThePageAsksWithoutTheParameter(): void {
		$scan = self::groupedScan(range(2, 1002));

		self::assertSame([], AdminViewService::leaveOutParameters($scan));

		// Even an answer that carried the counters is not used then.
		$coverage = self::coverageOf($scan, ['indexed' => 150, 'embedded' => 0, 'indexedLeftOut' => 50, 'embeddedLeftOut' => 0]);
		self::assertSame(200, $coverage['indexable']);
		self::assertSame(150, $coverage['indexed']);
		self::assertFalse($coverage['deduplicated']);
		self::assertTrue($coverage['duplicates']);
	}

	public function testWithoutAGroupTheCallAndTheFigureAreThoseOfOneFive(): void {
		$scan = self::groupedScan([]);
		$scan['grouped'] = array_intersect_key($scan, array_flip(['filesSeen', 'bytesSeen', 'ocrCandidates', 'pdfSeen', 'overCap', 'excluded', 'mountsTotal', 'mountsFinished']));

		self::assertSame([], AdminViewService::leaveOutParameters($scan));
		self::assertSame(['leaveOut' => '31,40'], AdminViewService::leaveOutParameters(self::groupedScan([31, 40])));

		$coverage = self::coverageOf($scan, ['indexed' => 200, 'embedded' => 200]);
		self::assertSame(200, $coverage['indexable']);
		self::assertSame(100, $coverage['percent']);
		self::assertSame(100, $coverage['embeddedPercent']);
		self::assertFalse($coverage['deduplicated']);
		self::assertFalse($coverage['duplicates']);
	}

	public function testFilesRefusedByTypeOnALeftOutStorageLeaveTheSubtrahend(): void {
		// Ten refused files on each of the two storages: twenty in all, ten on
		// the storage the group leaves out.
		$answer = ['indexed' => 180, 'embedded' => 0, 'indexedLeftOut' => 90, 'embeddedLeftOut' => 0];

		$deduplicated = self::coverageOf(self::groupedScan(), $answer, 20, 10);
		self::assertSame(90, $deduplicated['indexable']);
		self::assertSame(10, $deduplicated['deliberatelyLeftOut']);
		self::assertSame(100, $deduplicated['percent']);

		$fallback = self::coverageOf(self::groupedScan(), ['indexed' => 180, 'embedded' => 0], 20, 10);
		self::assertSame(180, $fallback['indexable']);
		self::assertSame(20, $fallback['deliberatelyLeftOut']);
	}

	// -- the hint after a rule change (plan 39-01, ANZE-02, L-36-06) ----------

	public function testTheHintStandsFromTheChangeUntilRecountAndSweepAreThrough(): void {
		$changed = self::NOW - 600;

		// Saved, the recount has not started since.
		self::assertTrue(AdminViewService::rulesPending($changed, $changed - 3600, false));
		// The recount started after the change and its chains are walking, or
		// the sweep of the new rule is still queued.
		self::assertTrue(AdminViewService::rulesPending($changed, $changed + 60, true));
		// Both through: the hint goes.
		self::assertFalse(AdminViewService::rulesPending($changed, $changed + 60, false));
		self::assertFalse(AdminViewService::rulesPending($changed, $changed, false));
		// No change was ever remembered: a crawl alone is no reason for it.
		self::assertFalse(AdminViewService::rulesPending(0, 0, true));
		self::assertFalse(AdminViewService::rulesPending(0, self::NOW, false));
	}

	public function testTheHintTravelsInTheCoverageBlockNextToEveryOtherState(): void {
		// Even while the figure is provisional or recounting, the hint is a
		// flag of its own and is not swallowed by either.
		$scan = self::groupedScan([]);
		$scan['mountsFinished'] = 1;
		$pending = self::coverageOf($scan, ['indexed' => 300, 'embedded' => 0], 0, 0, true);

		self::assertTrue($pending['rulesPending']);
		self::assertTrue($pending['provisional']);
		self::assertTrue($pending['recounting']);
		self::assertFalse(self::coverageOf($scan, ['indexed' => 300, 'embedded' => 0])['rulesPending']);
	}

	public function testANumeratorNeverFallsBelowNought(): void {
		$coverage = self::coverageOf(self::groupedScan(), ['indexed' => 10, 'embedded' => 5, 'indexedLeftOut' => 50, 'embeddedLeftOut' => 9]);

		self::assertSame(0, $coverage['indexed']);
		self::assertSame(0, $coverage['embedded']);
	}

	public function testAForeignSourceOrAnUnknownProfileHidesThePageLimit(): void {
		$foreign = self::profileAnswer();
		$foreign['profile']['sources']['ocrMaxPages'] = '<b>env</b>';
		$unknown = self::profileAnswer();
		$unknown['profile']['effective'] = 'turbo';
		$cast = self::profileAnswer();
		$cast['profile']['values']['ocrMaxPages'] = '50';

		foreach ([$foreign, $unknown, $cast] as $answer) {
			$pages = AdminViewService::limits(52_428_800, [], $answer)['pages'];
			self::assertFalse($pages['shown']);
			self::assertSame('', $pages['source']);
			self::assertSame('', $pages['profile']);
		}
	}
}
