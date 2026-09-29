<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\AppFramework\Utility\ITimeFactory;
use OCP\IDateTimeFormatter;
use Psr\Log\LoggerInterface;

/**
 * The PHP half of the probe of phase 27: start it, read its state, and take a
 * verdict over into appconfig (PRUEF-01, D-27-08).
 *
 * This is the one place where a probe result can turn into a stored profile,
 * and the rule is short: only a "fits" the container reported for the probe
 * this side started, with the same id and the same target, is saved. The
 * browser never hands a verdict to any route, so it cannot claim one
 * (T-27-19). "Narrow" and "does not fit" save nothing, and there is no way to
 * take them over anyway (D-27-08).
 *
 * Every verdict is remembered as the last probe result, with its cause, its
 * numbers, the moment and whether it was committed, and it does not expire
 * (D-27-04, D-27-10). The take-over is idempotent: once a verdict is taken
 * over, the running probe record is deleted, so a second call finds nothing to
 * take over. It runs on the state route and when the admin page renders, so a
 * closed tab does not lose a "fits".
 *
 * Every field of the container answer is judged against its closed set before
 * it is used, and an unknown word is dropped rather than shown or cast
 * (T-27-22). The sets have to stay identical to the ones in
 * backend/src/findling/probe.py, and a parity test on the Python side reads
 * them textually, which is why each keeps exactly its one line spelling.
 *
 * Nothing here logs a value: no id, no token, no profile. Every log line is a
 * static sentence, at most with a count next to it.
 */
final class ProbeService {
	private const PROBE_STATES = ['idle', 'running', 'done'];
	private const PROBE_STEPS = ['pause', 'download', 'digest', 'model', 'ocr_one', 'calc', 'ocr_n', 'cleanup'];
	private const PROBE_VERDICTS = ['fits', 'narrow', 'nofit'];
	private const PROBE_CAUSES = ['reserve_thin', 'memory_short', 'model_memory', 'memory_unknown', 'slot_killed', 'timeout', 'pause_timeout', 'download_failed', 'download_slow', 'digest_mismatch', 'disk_short', 'interrupted', 'probe_failed'];
	private const PROBE_NUMBERS = ['slots', 'need', 'available', 'reserve', 'required', 'seconds', 'rateInt8', 'rateFp32'];

	/**
	 * How long a started probe may go without a matching answer before it is
	 * recorded as interrupted, in seconds.
	 *
	 * The longest probe the container can run: up to 1800 seconds waiting for
	 * the indexing to pause, up to 600 seconds for the fp32 download and up to
	 * 120 seconds of measurement, 2520 in all, plus a margin for a slow box
	 * and a slow poll. After that the container restarted or lost the probe,
	 * and waiting longer would only leave the page spinning.
	 */
	private const PENDING_STALE_SECONDS = 3000;

	/** The answer codes of a start, the words the page knows. */
	public const START_STARTED = 'started';
	public const START_BUSY = 'busy';
	public const START_UNREACHABLE = 'unreachable';
	public const START_UNSUPPORTED = 'unsupported';
	public const START_REBUILDING = 'rebuilding';
	public const START_INVALID = 'invalid';

	/** The answer codes of the state route. */
	public const STATE_OK = 'ok';
	public const STATE_UNREACHABLE = 'unreachable';
	public const STATE_UNSUPPORTED = 'unsupported';

	private const VERDICT_FITS = 'fits';
	private const VERDICT_NOFIT = 'nofit';
	private const CAUSE_INTERRUPTED = 'interrupted';
	private const STATE_DONE = 'done';

	/** Profiles a probe may target with fp32 (D-25-01). */
	private const FP32_PROFILES = ['standard', 'performance'];

	public function __construct(
		private ExAppService $exAppService,
		private SettingsService $settingsService,
		private IDateTimeFormatter $dateTimeFormatter,
		private ITimeFactory $timeFactory,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * Start a probe for this profile and precision.
	 *
	 * The controller judged both values already; they are judged again here,
	 * because this method is what reaches the container. Only a start the
	 * container accepted with a well formed id is remembered as the running
	 * probe; every other answer writes nothing.
	 *
	 * @return array{started: bool, code: string}
	 */
	public function start(string $profile, string $precision, string $uid): array {
		if (!$this->validTarget($profile, $precision)) {
			return ['started' => false, 'code' => self::START_INVALID];
		}

		$outcome = $this->exAppService->adminSend('/probe', $uid, [
			'profile' => $profile,
			'precision' => $precision,
		]);

		switch ($outcome['kind']) {
			case ExAppService::ADMIN_OK:
				$id = self::probeId($outcome['body']['id'] ?? null);
				if ($id === '') {
					$this->logger->warning('Findling: the backend accepted a probe without a readable id');

					return ['started' => false, 'code' => self::START_UNREACHABLE];
				}

				$this->settingsService->rememberPending([
					'id' => $id,
					'profile' => $profile,
					'precision' => $precision,
					'uid' => $uid,
					'startedAt' => $this->timeFactory->getTime(),
					// What was in force when the probe started, so that a
					// save during the probe is not overwritten by its "fits"
					// (review WR-06 of phase 27).
					'inForce' => $this->inForce(),
				]);

				return ['started' => true, 'code' => self::START_STARTED];

			case ExAppService::ADMIN_BUSY:
				$state = $outcome['body']['state'] ?? null;
				if ($state === self::START_REBUILDING) {
					return ['started' => false, 'code' => self::START_REBUILDING];
				}

				return $this->adopt($profile, $precision, $uid)
					? ['started' => true, 'code' => self::START_STARTED]
					: ['started' => false, 'code' => self::START_BUSY];

			case ExAppService::ADMIN_MISSING:
				return ['started' => false, 'code' => self::START_UNSUPPORTED];

			case ExAppService::ADMIN_UNREACHABLE:
				return $this->adopt($profile, $precision, $uid)
					? ['started' => true, 'code' => self::START_STARTED]
					: ['started' => false, 'code' => self::START_UNREACHABLE];

			default:
				return ['started' => false, 'code' => self::START_UNREACHABLE];
		}
	}

	/**
	 * Take over a probe the container runs but this side has no record of
	 * (review WR-07 of phase 27).
	 *
	 * A start the two second admin timeout cut off reads as unreachable here
	 * while the container started the probe anyway, and the next click reads
	 * busy. Without a record its verdict would never be taken over and never
	 * shown. So when no record exists, the state route is asked once, and a
	 * running probe with exactly the requested target and a well formed id is
	 * adopted as the pending one. A probe of another target is somebody else's
	 * and stays busy; the verdict of that one is not this click's to take.
	 */
	private function adopt(string $profile, string $precision, string $uid): bool {
		if ($this->settingsService->profileCheckPending() !== null) {
			return false;
		}

		$outcome = $this->exAppService->adminState('/probe/state', $uid);
		if ($outcome['kind'] !== ExAppService::ADMIN_OK || !is_array($outcome['body'])) {
			return false;
		}

		$snapshot = $this->snapshot($outcome['body']);
		if ($snapshot['state'] !== 'running'
			|| $snapshot['id'] === ''
			|| $snapshot['targetProfile'] !== $profile
			|| $snapshot['targetPrecision'] !== $precision) {
			return false;
		}

		$this->settingsService->rememberPending([
			'id' => $snapshot['id'],
			'profile' => $profile,
			'precision' => $precision,
			'uid' => $uid,
			'startedAt' => $this->timeFactory->getTime(),
			'inForce' => $this->inForce(),
		]);
		$this->logger->info('Findling: took over a probe whose start answer was lost');

		return true;
	}

	/**
	 * The state of the probe for the page, after taking a finished verdict
	 * over.
	 *
	 * @return array{code: string, state: string, step: string, bytesDone: int, bytesTotal: int, result: ?array<string, mixed>}
	 */
	public function state(string $uid): array {
		$outcome = $this->exAppService->adminState('/probe/state', $uid);
		$snapshot = $outcome['kind'] === ExAppService::ADMIN_OK && is_array($outcome['body'])
			? $this->snapshot($outcome['body'])
			: null;

		$this->takeOver($snapshot, $uid);

		$code = match (true) {
			$snapshot !== null => self::STATE_OK,
			$outcome['kind'] === ExAppService::ADMIN_MISSING => self::STATE_UNSUPPORTED,
			default => self::STATE_UNREACHABLE,
		};

		return [
			'code' => $code,
			'state' => $snapshot['state'] ?? '',
			'step' => $snapshot['step'] ?? '',
			'bytesDone' => $snapshot['bytesDone'] ?? 0,
			'bytesTotal' => $snapshot['bytesTotal'] ?? 0,
			'result' => $this->result(),
		];
	}

	/**
	 * Take a finished verdict over without answering anything, for the admin
	 * page as it renders.
	 *
	 * Asks the container only while a probe is running, so an ordinary page
	 * load without a probe costs no call.
	 */
	public function settle(string $uid): void {
		if ($this->settingsService->profileCheckPending() === null) {
			return;
		}

		$outcome = $this->exAppService->adminState('/probe/state', $uid);
		$snapshot = $outcome['kind'] === ExAppService::ADMIN_OK && is_array($outcome['body'])
			? $this->snapshot($outcome['body'])
			: null;

		$this->takeOver($snapshot, $uid);
	}

	/**
	 * The last probe result as the page shows it, judged again on the way
	 * out because appconfig is also writable through occ.
	 *
	 * @return array<string, mixed>|null
	 */
	public function result(): ?array {
		$check = $this->settingsService->profileCheck();
		if ($check === null) {
			return null;
		}

		$verdict = self::member($check['verdict'] ?? null, self::PROBE_VERDICTS);
		$profile = self::member($check['profile'] ?? null, SettingsService::PROFILES);
		$precision = self::member($check['precision'] ?? null, SettingsService::PRECISIONS);
		if ($verdict === '' || $profile === '' || $precision === '') {
			return null;
		}

		$at = is_int($check['at'] ?? null) && $check['at'] > 0 ? $check['at'] : 0;

		return [
			'id' => self::probeId($check['id'] ?? null),
			'profile' => $profile,
			'precision' => $precision,
			'verdict' => $verdict,
			'cause' => $verdict === self::VERDICT_FITS ? '' : self::member($check['cause'] ?? null, self::PROBE_CAUSES),
			'numbers' => self::numbers($check['numbers'] ?? null),
			'at' => $at,
			'atText' => $at > 0 ? $this->dateTimeFormatter->formatDateTime($at, 'long', 'short') : '',
			'committed' => ($check['committed'] ?? false) === true,
			'fp32Deleted' => ($check['fp32Deleted'] ?? false) === true,
		];
	}

	/**
	 * The one take-over, shared by state() and settle().
	 *
	 * Saves only when the container reports the probe done, with the id this
	 * side remembered (compared with hash_equals) and with exactly the target
	 * this side asked for, and only on "fits". Every verdict is remembered.
	 *
	 * A "fits" is remembered but not committed when the stored profile or
	 * precision changed after the start (review WR-06 of phase 27): an admin
	 * who stored economy through occ, another tab or the write route while the
	 * probe ran took the safe way down (D-27-09), and a probe nobody waits for
	 * any more must not raise the profile again.
	 * A running probe that never reports back within PENDING_STALE_SECONDS is
	 * recorded as interrupted.
	 *
	 * @param array<string, mixed>|null $snapshot
	 */
	private function takeOver(?array $snapshot, string $uid): void {
		$pending = $this->pending();
		if ($pending === null) {
			return;
		}

		$now = $this->timeFactory->getTime();

		if ($snapshot !== null && $this->matches($snapshot, $pending)) {
			// Idempotent over the id: a verdict already on record for this id
			// is not taken over a second time.
			$stored = $this->settingsService->profileCheck();
			if (is_string($stored['id'] ?? null) && hash_equals($stored['id'], $pending['id'])) {
				$this->settingsService->forgetPending();

				return;
			}

			$verdict = $snapshot['verdict'];
			$committed = false;
			if ($verdict === self::VERDICT_FITS && $this->unchangedSince($pending)) {
				$committed = $this->settingsService->saveProfile($pending['profile'], $pending['precision']);
				if ($committed) {
					$this->confirm($pending['profile'], $uid);
				}
			}

			$this->settingsService->rememberProfileCheck([
				'id' => $pending['id'],
				'profile' => $pending['profile'],
				'precision' => $pending['precision'],
				'verdict' => $verdict,
				'cause' => $verdict === self::VERDICT_FITS ? '' : $snapshot['cause'],
				'numbers' => $snapshot['numbers'],
				'at' => $snapshot['finishedAt'] > 0 && $snapshot['finishedAt'] <= $now ? $snapshot['finishedAt'] : $now,
				'committed' => $committed,
				'fp32Deleted' => $snapshot['fp32Deleted'],
			]);
			$this->settingsService->forgetPending();

			return;
		}

		if ($now - $pending['startedAt'] > self::PENDING_STALE_SECONDS) {
			$this->logger->warning('Findling: a probe did not report back and is recorded as interrupted');
			$this->settingsService->rememberProfileCheck([
				'id' => $pending['id'],
				'profile' => $pending['profile'],
				'precision' => $pending['precision'],
				'verdict' => self::VERDICT_NOFIT,
				'cause' => self::CAUSE_INTERRUPTED,
				'numbers' => [],
				'at' => $now,
				'committed' => false,
				'fp32Deleted' => false,
			]);
			$this->settingsService->forgetPending();
		}
	}

	/**
	 * The way back after a lowering by the memory guard (D-27-12, D-26-04).
	 *
	 * Reads a fresh status on this side and stores its token only when the
	 * guard chose exactly the profile that was just found to fit. The token
	 * never leaves the server: it is read here, judged, written, and appears
	 * in no answer and no log line (T-27-21).
	 */
	private function confirm(string $profile, string $uid): void {
		$status = $this->exAppService->adminGet('/status', $uid, []);
		if ($status === null) {
			return;
		}

		$answer = $status;
		$token = AdminViewService::hexToken(AdminViewService::guardField($answer, 'token'));
		$chosen = AdminViewService::profileName(AdminViewService::guardField($answer, 'chosen'));
		if ($token === null || $chosen !== $profile) {
			return;
		}

		if (!$this->settingsService->saveConfirmation($token)) {
			$this->logger->warning('Findling: the confirmation after a probe was not stored');
		}
	}

	/**
	 * The stored profile, precision and whether a profile was ever stored,
	 * the three facts a save during the probe would change.
	 *
	 * @return array{profile: string, precision: string, stored: bool}
	 */
	private function inForce(): array {
		return [
			'profile' => $this->settingsService->profile(),
			'precision' => $this->settingsService->modelPrecision() ?? '',
			'stored' => $this->settingsService->profileStored(),
		];
	}

	/**
	 * Whether nothing was stored since the probe started. A record from before
	 * this check carries no inForce and keeps the take-over it always had.
	 *
	 * @param array{id: string, profile: string, precision: string, startedAt: int, inForce: ?array{profile: string, precision: string, stored: bool}} $pending
	 */
	private function unchangedSince(array $pending): bool {
		if ($pending['inForce'] === null) {
			return true;
		}
		if ($pending['inForce'] === $this->inForce()) {
			return true;
		}

		$this->logger->info('Findling: a probe fitted, but the profile was changed while it ran; nothing was saved');

		return false;
	}

	/**
	 * @param array<string, mixed> $snapshot
	 * @param array{id: string, profile: string, precision: string, startedAt: int, inForce: ?array{profile: string, precision: string, stored: bool}} $pending
	 */
	private function matches(array $snapshot, array $pending): bool {
		return $snapshot['state'] === self::STATE_DONE
			&& $snapshot['verdict'] !== ''
			&& $snapshot['id'] !== ''
			&& hash_equals($pending['id'], $snapshot['id'])
			&& $snapshot['targetProfile'] === $pending['profile']
			&& $snapshot['targetPrecision'] === $pending['precision'];
	}

	/**
	 * The running probe record, judged; a record that does not hold is
	 * forgotten, because it can never match an answer.
	 *
	 * @return array{id: string, profile: string, precision: string, startedAt: int, inForce: ?array{profile: string, precision: string, stored: bool}}|null
	 */
	private function pending(): ?array {
		$pending = $this->settingsService->profileCheckPending();
		if ($pending === null) {
			return null;
		}

		$id = self::probeId($pending['id'] ?? null);
		$profile = self::member($pending['profile'] ?? null, SettingsService::PROFILES);
		$precision = self::member($pending['precision'] ?? null, SettingsService::PRECISIONS);
		$startedAt = $pending['startedAt'] ?? null;
		if ($id === '' || $profile === '' || $precision === '' || !is_int($startedAt) || $startedAt < 0) {
			$this->logger->warning('Findling: dropped an unreadable probe record');
			$this->settingsService->forgetPending();

			return null;
		}

		return [
			'id' => $id,
			'profile' => $profile,
			'precision' => $precision,
			'startedAt' => $startedAt,
			'inForce' => self::inForceOf($pending['inForce'] ?? null),
		];
	}

	/**
	 * The inForce part of a pending record, judged; null when it is absent or
	 * unreadable. An unreadable one can never equal a fresh reading, so it is
	 * judged into a value that never matches rather than into null, which would
	 * take the old path and commit.
	 *
	 * @return array{profile: string, precision: string, stored: bool}|null
	 */
	private static function inForceOf(mixed $value): ?array {
		if ($value === null) {
			return null;
		}
		if (!is_array($value)) {
			return ['profile' => '', 'precision' => '', 'stored' => false];
		}

		return [
			'profile' => self::member($value['profile'] ?? null, SettingsService::PROFILES),
			'precision' => is_string($value['precision'] ?? null) ? self::member($value['precision'], SettingsService::PRECISIONS) : '',
			'stored' => ($value['stored'] ?? null) === true,
		];
	}

	/**
	 * The container answer of the state route, every field judged against its
	 * closed set. Unknown words become the empty string, unknown number keys
	 * and negative values are dropped.
	 *
	 * @param array<mixed> $body
	 * @return array{id: string, state: string, step: string, bytesDone: int, bytesTotal: int, verdict: string, cause: string, numbers: array<string, int>, targetProfile: string, targetPrecision: string, fp32Deleted: bool, finishedAt: int}
	 */
	private function snapshot(array $body): array {
		$finishedAt = $body['finishedAt'] ?? null;

		return [
			'id' => self::probeId($body['id'] ?? null),
			'state' => self::member($body['state'] ?? null, self::PROBE_STATES),
			'step' => self::member($body['step'] ?? null, self::PROBE_STEPS),
			'bytesDone' => self::counter($body['bytesDone'] ?? null),
			'bytesTotal' => self::counter($body['bytesTotal'] ?? null),
			'verdict' => self::member($body['verdict'] ?? null, self::PROBE_VERDICTS),
			'cause' => self::member($body['cause'] ?? null, self::PROBE_CAUSES),
			'numbers' => self::numbers($body['numbers'] ?? null),
			'targetProfile' => self::member($body['targetProfile'] ?? null, SettingsService::PROFILES),
			'targetPrecision' => self::member($body['targetPrecision'] ?? null, SettingsService::PRECISIONS),
			'fp32Deleted' => ($body['fp32Deleted'] ?? false) === true,
			'finishedAt' => is_int($finishedAt) || is_float($finishedAt) ? max(0, (int)$finishedAt) : 0,
		];
	}

	/** A valid target of a probe: closed sets, fp32 only above economy. */
	private function validTarget(string $profile, string $precision): bool {
		if (!in_array($profile, SettingsService::PROFILES, true) || !in_array($precision, SettingsService::PRECISIONS, true)) {
			return false;
		}

		return $precision !== 'fp32' || in_array($profile, self::FP32_PROFILES, true);
	}

	/** A probe id, 16 lowercase hex digits, or the empty string. */
	private static function probeId(mixed $value): string {
		return is_string($value) && preg_match('/^[0-9a-f]{16}$/D', $value) === 1 ? $value : '';
	}

	/**
	 * One word out of a closed set, or the empty string.
	 *
	 * @param list<string> $set
	 */
	private static function member(mixed $value, array $set): string {
		return is_string($value) && in_array($value, $set, true) ? $value : '';
	}

	/** A non negative integer, or zero. */
	private static function counter(mixed $value): int {
		return is_int($value) && $value >= 0 ? $value : 0;
	}

	/**
	 * The numbers of a verdict, only known keys with non negative integers.
	 *
	 * @return array<string, int>
	 */
	private static function numbers(mixed $value): array {
		if (!is_array($value)) {
			return [];
		}

		$numbers = [];
		foreach (self::PROBE_NUMBERS as $key) {
			$number = $value[$key] ?? null;
			if (is_int($number) && $number >= 0) {
				$numbers[$key] = $number;
			}
		}

		return $numbers;
	}
}
