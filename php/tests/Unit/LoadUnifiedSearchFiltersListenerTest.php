<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Listener\LoadUnifiedSearchFiltersListener;
use OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\EventDispatcher\Event;
use OCP\Util;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

/**
 * The three behaviours of the page listener of plan 32-04.
 *
 * What they defend: the script with the filter entries of the unified search
 * reaches every page of a logged in user and no other page, and the listener
 * never breaks a page it was not meant for.
 *
 * **How "loaded" is observed.** Util::addScript writes into a static list of the
 * server, and Util::getScripts(), public since Nextcloud 24, is how the page
 * template reads it back. That list lives for the whole PHPUnit process and
 * getScripts() removes duplicates, so a test that only asked "is the script in
 * the list" would pass on a script some earlier test had added, and the
 * executionOrder "defects" of phpunit.xml reorders tests between runs. Every case
 * therefore compares the raw static lists of OCP\Util before and after its one
 * call (read through reflection, never written), which counts every entry and
 * does not depend on what ran before. The positive case asks getScripts() on top,
 * so the statement is also made in the words the page template uses.
 */
#[CoversClass(LoadUnifiedSearchFiltersListener::class)]
final class LoadUnifiedSearchFiltersListenerTest extends TestCase {
	private const SCRIPT_PATH = 'findling/js/unified-search';

	public function testALoggedInPageLoadsTheScriptAndTheTranslationsOfFindling(): void {
		$before = self::scriptState();

		(new LoadUnifiedSearchFiltersListener())->handle($this->pageEvent(true));

		$after = self::scriptState();
		$added = self::addedEntries($before, $after);

		self::assertSame(
			1,
			count(array_keys($added, self::SCRIPT_PATH, true)),
			'the script has to be added exactly once per page',
		);
		self::assertNotSame(
			[],
			array_values(array_filter($added, static fn (string $entry): bool => str_starts_with($entry, 'findling/l10n/'))),
			'the catalogue of findling has to come with the script, or t() shows English on pages of other apps',
		);
		foreach ($added as $entry) {
			self::assertStringStartsWith('findling/', $entry, 'the listener adds nothing that is not findling');
		}
		self::assertContains(self::SCRIPT_PATH, Util::getScripts());
	}

	public function testAPageWithoutALoggedInUserLoadsNothing(): void {
		// The login page and a public share link: both render a template, neither
		// has a unified search that asks Findling.
		$before = self::scriptState();

		(new LoadUnifiedSearchFiltersListener())->handle($this->pageEvent(false));

		self::assertSame($before, self::scriptState());
	}

	public function testAForeignEventIsIgnoredWithoutAnError(): void {
		$before = self::scriptState();

		(new LoadUnifiedSearchFiltersListener())->handle(new Event());

		self::assertSame($before, self::scriptState());
	}

	private function pageEvent(bool $loggedIn): BeforeTemplateRenderedEvent {
		return new BeforeTemplateRenderedEvent($loggedIn, $this->createMock(TemplateResponse::class));
	}

	/**
	 * The raw static lists of OCP\Util, read and never written.
	 *
	 * @return array{scripts: array<string, list<string>>, init: list<string>}
	 */
	private static function scriptState(): array {
		/** @var array<string, list<string>> $scripts */
		$scripts = (new \ReflectionProperty(Util::class, 'scripts'))->getValue();
		/** @var list<string> $init */
		$init = (new \ReflectionProperty(Util::class, 'scriptsInit'))->getValue();

		return ['scripts' => $scripts, 'init' => $init];
	}

	/**
	 * Every entry that is in the after state and was not counted in the before
	 * state, as a multiset difference, so a second copy of an existing entry is
	 * an added entry too.
	 *
	 * @param array{scripts: array<string, list<string>>, init: list<string>} $before
	 * @param array{scripts: array<string, list<string>>, init: list<string>} $after
	 * @return list<string>
	 */
	private static function addedEntries(array $before, array $after): array {
		$flatten = static fn (array $state): array => array_merge($state['init'], ...array_values($state['scripts']));

		$remaining = array_count_values($flatten($before));
		$added = [];
		foreach ($flatten($after) as $entry) {
			if (($remaining[$entry] ?? 0) > 0) {
				$remaining[$entry]--;
				continue;
			}
			$added[] = $entry;
		}

		return $added;
	}
}
