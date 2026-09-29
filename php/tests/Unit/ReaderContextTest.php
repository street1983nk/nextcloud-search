<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Service\ReaderContext;
use OCP\IUser;
use OCP\IUserManager;
use OCP\IUserSession;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;

/**
 * The one place that changes the active user of a request (issue #14).
 *
 * The session double is stateful on purpose: getUser() answers whatever
 * setVolatileActiveUser() stored last, so "who is active while the work runs"
 * and "who is active afterwards" are real observations and not expectations
 * of a call count.
 */
#[CoversClass(ReaderContext::class)]
final class ReaderContextTest extends TestCase {
	private IUserSession&MockObject $session;
	private IUserManager&MockObject $userManager;
	private ?IUser $active = null;
	/** @var list<?string> */
	private array $switches = [];

	protected function setUp(): void {
		parent::setUp();

		$this->session = $this->createMock(IUserSession::class);
		$this->session->method('getUser')->willReturnCallback(fn (): ?IUser => $this->active);
		$this->session->method('setVolatileActiveUser')->willReturnCallback(function (?IUser $user): void {
			$this->active = $user;
			$this->switches[] = $user?->getUID();
		});
		$this->userManager = $this->createMock(IUserManager::class);
	}

	private function user(string $uid): IUser&MockObject {
		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn($uid);

		return $user;
	}

	private function context(): ReaderContext {
		return new ReaderContext($this->session, $this->userManager);
	}

	public function testTheWorkRunsAsTheMemberAndThePreviousUserObjectIsRestored(): void {
		$admin = $this->user('admin');
		$anna = $this->user('anna');
		$this->active = $admin;
		$this->userManager->method('get')->with('anna')->willReturn($anna);

		$seen = null;
		$result = $this->context()->actAs('anna', function () use (&$seen): string {
			$seen = $this->active?->getUID();

			return 'value';
		});

		self::assertSame('value', $result);
		self::assertSame('anna', $seen);
		self::assertSame($admin, $this->active);
		self::assertSame(['anna', 'admin'], $this->switches);
	}

	public function testANullPreviousUserIsHandedBackAsNull(): void {
		// The ExApp request: nobody is active. The restore passes back exactly
		// what getUser() answered, which is null, and not a guess.
		$anna = $this->user('anna');
		$this->userManager->method('get')->with('anna')->willReturn($anna);

		$seen = null;
		$this->context()->actAs('anna', function () use (&$seen): void {
			$seen = $this->active?->getUID();
		});

		self::assertSame('anna', $seen);
		self::assertNull($this->active);
		self::assertSame(['anna', null], $this->switches);
	}

	public function testAThrowingWorkStillRestoresThePreviousUser(): void {
		$admin = $this->user('admin');
		$this->active = $admin;
		$this->userManager->method('get')->with('anna')->willReturn($this->user('anna'));
		$thrown = new \RuntimeException('lookup failed');

		try {
			$this->context()->actAs('anna', static function () use ($thrown): never {
				throw $thrown;
			});
			self::fail('The exception of the work must propagate.');
		} catch (\RuntimeException $e) {
			self::assertSame($thrown, $e);
		}

		self::assertSame($admin, $this->active);
		self::assertSame(['anna', 'admin'], $this->switches);
	}

	public function testAnUnknownUserIsNotSwitchedToAndTheWorkStillRuns(): void {
		// The work runs unchanged, so its own "no such user" answer (the
		// NoUserException of getUserFolder) stays what it was.
		$this->userManager->method('get')->with('ghost')->willReturn(null);
		$this->session->expects(self::never())->method('setVolatileActiveUser');

		$ran = false;
		$this->context()->actAs('ghost', static function () use (&$ran): void {
			$ran = true;
		});

		self::assertTrue($ran);
	}

	public function testTheActiveUserAlreadyBeingTheMemberCausesNoSwitch(): void {
		$this->active = $this->user('anna');
		$this->userManager->expects(self::never())->method('get');
		$this->session->expects(self::never())->method('setVolatileActiveUser');

		self::assertSame(7, $this->context()->actAs('anna', static fn (): int => 7));
	}
}
