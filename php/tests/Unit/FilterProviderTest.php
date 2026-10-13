<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCA\Findling\Search\FilterProvider;
use OCA\Findling\Search\Provider;
use OCA\Findling\Service\ApprovedHit;
use OCA\Findling\Service\SearchCaps;
use OCA\Findling\Service\SearchFilters;
use OCA\Findling\Service\SearchOutcome;
use OCA\Findling\Service\SearchService;
use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\IUser;
use OCP\Search\FilterDefinition;
use OCP\Search\IFilter;
use OCP\Search\ISearchQuery;
use OCP\Search\SearchResult;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

/**
 * The hidden provider of the filter chips (Befund A of plan 32-07).
 *
 * The real Provider is used as it is, with the shared service as the double,
 * because Provider is final and because the point of FilterProvider is that it
 * adds nothing to it: what reaches SearchService::run() is read off the
 * arguments of that call, never off a result a real run would produce. Who may
 * see a file is the subject of SearchServiceTest; here it is asserted that the
 * request reaches that one service with the user who asked, or does not reach
 * it at all.
 */
#[CoversClass(FilterProvider::class)]
final class FilterProviderTest extends TestCase {
	private IL10N&MockObject $l10n;
	private IURLGenerator&MockObject $urlGenerator;
	private SearchService&MockObject $searchService;

	protected function setUp(): void {
		parent::setUp();

		$this->l10n = $this->createMock(IL10N::class);
		$this->l10n->method('t')->willReturnCallback(static fn (string $text): string => 'de:' . $text);
		$this->urlGenerator = $this->createMock(IURLGenerator::class);
		$this->urlGenerator->method('linkToRoute')->willReturnCallback(
			static fn (string $route, array $parameters = []): string => '/' . $route . '?' . http_build_query($parameters),
		);
		$this->searchService = $this->createMock(SearchService::class);
	}

	private function provider(): Provider {
		return new Provider($this->l10n, $this->urlGenerator, $this->searchService, $this->createMock(LoggerInterface::class));
	}

	private function filterProvider(): FilterProvider {
		return new FilterProvider($this->provider());
	}

	private function user(string $uid = 'testuser'): IUser&MockObject {
		$user = $this->createMock(IUser::class);
		$user->method('getUID')->willReturn($uid);

		return $user;
	}

	/**
	 * A query whose filters are looked up by name; every name outside the map
	 * is a filter the dialog did not send.
	 *
	 * @param array<string,mixed> $values
	 */
	private function query(array $values, string $term = 'abnahme32'): ISearchQuery&MockObject {
		$query = $this->createMock(ISearchQuery::class);
		$query->method('getTerm')->willReturn($term);
		$query->method('getLimit')->willReturn(5);
		$query->method('getCursor')->willReturn(null);
		$query->method('getFilter')->willReturnCallback(
			function (string $name) use ($values): ?IFilter {
				if (!array_key_exists($name, $values)) {
					return null;
				}

				$filter = $this->createMock(IFilter::class);
				$filter->method('get')->willReturn($values[$name]);

				return $filter;
			},
		);

		return $query;
	}

	/**
	 * The arguments of every call of SearchService::run(), with one approved
	 * hit as the answer of each.
	 *
	 * @return \ArrayObject<int,array{user:IUser,filters:SearchFilters}>
	 */
	private function recordRuns(): \ArrayObject {
		/** @var \ArrayObject<int,array{user:IUser,filters:SearchFilters}> $runs */
		$runs = new \ArrayObject();
		$this->searchService->method('run')->willReturnCallback(
			static function (
				IUser $user,
				string $term,
				bool $titleOnly,
				int $startCursor,
				SearchCaps $caps,
				SearchFilters $filters,
			) use ($runs): SearchOutcome {
				$runs->append(['user' => $user, 'filters' => $filters]);

				return new SearchOutcome(
					[new ApprovedHit(1746, 'Bericht.pdf', 'Abnahme32/Bericht.pdf', 'application/pdf', 0)],
					[],
					0,
					false,
					false,
					null,
				);
			},
		);

		return $runs;
	}

	/**
	 * @return list<array<string,mixed>>
	 */
	private function entriesOf(SearchResult $result): array {
		/** @var list<\OCP\Search\SearchResultEntry> $entries */
		$entries = $result->jsonSerialize()['entries'];

		return array_map(static fn ($entry): array => $entry->jsonSerialize(), $entries);
	}

	// -- what the dialog sees of it -------------------------------------------

	public function testTheIdIsTheOneTheChipsAskAndNotTheRealProvider(): void {
		self::assertSame('findling-filter', $this->filterProvider()->getId());
		self::assertSame(FilterProvider::ID, $this->filterProvider()->getId());
		self::assertNotSame($this->provider()->getId(), $this->filterProvider()->getId());
	}

	public function testTheOrderIsNullOnEveryRouteSoTheDialogListsItNowhere(): void {
		// The real provider answers an int on the same routes; a null there is
		// the one way out of the provider list of SearchComposer::getProviders().
		foreach (['', 'files.view.index', 'dashboard.dashboard.index', 'findling.page.index'] as $route) {
			self::assertNull($this->filterProvider()->getOrder($route, []), $route);
			self::assertIsInt($this->provider()->getOrder($route, []), $route);
		}
	}

	public function testTheNameIsTheNameOfTheRealGroup(): void {
		self::assertSame('de:File contents', $this->filterProvider()->getName());
		self::assertSame($this->provider()->getName(), $this->filterProvider()->getName());
	}

	public function testTheFiltersAreTheFiltersOfTheRealProviderWordForWord(): void {
		$filter = $this->filterProvider();

		self::assertSame(
			[
				IFilter::BUILTIN_TERM,
				IFilter::BUILTIN_TITLE_ONLY,
				IFilter::BUILTIN_SINCE,
				IFilter::BUILTIN_UNTIL,
				'types',
				'folder',
			],
			$filter->getSupportedFilters(),
		);
		self::assertSame($this->provider()->getSupportedFilters(), $filter->getSupportedFilters());
		self::assertSame([], $filter->getAlternateIds());

		$custom = array_map(
			static fn (FilterDefinition $definition): array => [$definition->name(), $definition->type()],
			$filter->getCustomFilters(),
		);
		self::assertSame([['types', FilterDefinition::TYPE_STRING], ['folder', FilterDefinition::TYPE_STRING]], $custom);
	}

	// -- the request without a chip --------------------------------------------

	/**
	 * @return array<string,array{array<string,mixed>}>
	 */
	public static function requestsWithoutAChip(): array {
		$since = new \DateTimeImmutable('@1760313600');

		return [
			'the term alone' => [[]],
			'a date range of the core' => [[IFilter::BUILTIN_SINCE => $since, IFilter::BUILTIN_UNTIL => $since]],
			'the file name switch' => [[IFilter::BUILTIN_TITLE_ONLY => true]],
		];
	}

	/**
	 * @param array<string,mixed> $values
	 */
	#[\PHPUnit\Framework\Attributes\DataProvider('requestsWithoutAChip')]
	public function testARequestWithoutTypesAndFolderIsAnEmptyGroupWithoutABackendCall(array $values): void {
		// The request the core sends for each of the seven menu entries while no
		// chip is set (Befund A). It must not reach the shared service: that was
		// seven extra rounds through PHP, the recheck and the container per term.
		$this->searchService->expects(self::never())->method('run');

		$result = $this->filterProvider()->search($this->user(), $this->query($values));

		self::assertSame([], $this->entriesOf($result));
		self::assertSame('de:File contents', $result->jsonSerialize()['name']);
		self::assertFalse($result->jsonSerialize()['isPaginated']);
	}

	// -- the request with a chip -----------------------------------------------

	public function testATypeChipIsHandedToTheRealProviderWithTheUserWhoAsked(): void {
		$runs = $this->recordRuns();
		$user = $this->user('alice');

		$entries = $this->entriesOf($this->filterProvider()->search($user, $this->query([Provider::FILTER_TYPES => 'pdf'])));

		self::assertCount(1, $runs);
		// The rights are those of the user who asked, decided in the one shared
		// service and nowhere in this class.
		self::assertSame($user, $runs[0]['user']);
		self::assertSame(['pdf'], $runs[0]['filters']->types);
		self::assertNull($runs[0]['filters']->folder);
		self::assertSame(['Bericht.pdf'], array_column($entries, 'title'));
		self::assertSame('1746', $entries[0]['attributes']['fileId']);
	}

	public function testAFolderChipIsHandedOnInItsCanonicalShape(): void {
		$runs = $this->recordRuns();

		$this->filterProvider()->search($this->user(), $this->query([Provider::FILTER_FOLDER => '/Abnahme32/']));

		self::assertCount(1, $runs);
		self::assertSame('/Abnahme32', $runs[0]['filters']->folder);
		self::assertSame([], $runs[0]['filters']->types);
	}

	public function testTheRootFolderIsAChipThatNarrowsNothing(): void {
		// The root of the user folder was chosen: the group appears, with the
		// hits of the search without a folder, and nothing is narrowed.
		$runs = $this->recordRuns();

		$entries = $this->entriesOf($this->filterProvider()->search($this->user(), $this->query([Provider::FILTER_FOLDER => '/'])));

		self::assertCount(1, $runs);
		self::assertNull($runs[0]['filters']->folder);
		self::assertSame([], $runs[0]['filters']->types);
		self::assertSame(['Bericht.pdf'], array_column($entries, 'title'));
	}

	public function testAChipAndADateArriveTogether(): void {
		$runs = $this->recordRuns();

		$this->filterProvider()->search($this->user(), $this->query([
			Provider::FILTER_TYPES => 'pdf',
			IFilter::BUILTIN_SINCE => new \DateTimeImmutable('@1760313600'),
			IFilter::BUILTIN_UNTIL => new \DateTimeImmutable('@1760399999'),
		]));

		self::assertCount(1, $runs);
		self::assertSame(['pdf'], $runs[0]['filters']->types);
		self::assertSame(1760313600, $runs[0]['filters']->since);
		self::assertSame(1760399999, $runs[0]['filters']->until);
	}

	public function testWhatTheSharedServiceRejectsStaysRejected(): void {
		// No hit of its own: when the recheck approves nothing, the chip shows
		// nothing, the same empty group as the real provider.
		$this->searchService->expects(self::once())->method('run')->willReturn(
			new SearchOutcome([], [], 0, false, false, 'all_candidates_rejected'),
		);

		$result = $this->filterProvider()->search($this->user(), $this->query([Provider::FILTER_TYPES => 'pdf']));

		self::assertSame([], $this->entriesOf($result));
	}

	public function testTheClassHoldsNothingButTheRealProvider(): void {
		// No service, no file system, no user session: the class cannot decide
		// about rights because it has nothing to decide with.
		$constructor = (new \ReflectionClass(FilterProvider::class))->getConstructor();
		self::assertNotNull($constructor);
		$types = array_map(
			static fn (\ReflectionParameter $parameter): string => (string)$parameter->getType(),
			$constructor->getParameters(),
		);

		self::assertSame([Provider::class], $types);
	}
}
