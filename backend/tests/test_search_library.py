"""Candidates: prefiltered, narrow, and paged one round at a time.

Two of the assertions below are about things that must *not* be there, and they
are the reason this file exists at all. A candidate that carries a file name is
a leak that no functional test notices, because the result the user finally sees
was filtered further down the line and looks perfectly correct. The same is true
for a total hit count: it is a statement about documents the asking user may
never learn anything about, and it is invisible in every screenshot.

The third one is the user with no permission row at all. It is half the security
statement of this module: an empty answer, not an exception, and above all not
the unfiltered list.
"""

import dataclasses
from collections.abc import Iterator
from pathlib import Path

import pytest
from tantivy import Document, Index, Query

from findling.index.open import open_index
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)
from findling.index.search import CandidatePage, candidates
from findling.query.rewrite import build_query
from findling.store.repo import Store, open_store

SEARCH_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "index" / "search.py"

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()

DOCUMENTS = 12

# alice sees the odd file ids, bob sees everything, carol has no row at all.
ALICE = "alice"
BOB = "bob"
CAROL = "carol"

# One timestamp for four documents, and the writing order of the measurement of
# 16.09.2026: with exactly this order tantivy answered 7, 3, 9, 1, so the second
# key of FILT-02 is red here unless it is made by hand.
TIED_MTIME = 1_800_000_000
TIED_IDS = (7, 3, 9, 1)

# One tie group that spans the 128-hit portion boundary of the sorted scan.
# Written evens first and odds second, so the engine's tie order (document
# address) matches neither direction of the file id and every portion re-sort
# actually moves documents. This is the shape of the finding of 18.09.2026:
# a mass upload with identical timestamps, paged past page five.
MASS_DOCUMENTS = 160
MASS_MTIME = 1_800_000_100
MASS_WRITE_ORDER = tuple(range(2, MASS_DOCUMENTS + 1, 2)) + tuple(range(1, MASS_DOCUMENTS + 1, 2))
MASS_PAGE = 25


def _body(file_id: int) -> str:
    """Bodies of different length, so that the ranking is not a coin toss."""
    tail = "Weitere Absätze folgen. " * (file_id % 4)
    return f"Die Kündigungsfrist im Vertrag Nummer {file_id}. {tail}"


@pytest.fixture(scope="module")
def index(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Index]:
    directory = tmp_path_factory.mktemp("candidate-index")
    built = open_index(directory, CONSTITUENTS)
    writer = built.writer(heap_size=15_000_000, num_threads=1)
    for file_id in range(1, DOCUMENTS + 1):
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, f"Akte-{file_id}.pdf")
        document.add_text(FIELD_TITLE, f"Akte {file_id}")
        document.add_text(FIELD_PATH, f"/Akten/Akte-{file_id}.pdf")
        document.add_text(FIELD_EXT, "pdf" if file_id % 2 else "docx")
        document.add_text(FIELD_BODY_DE, _body(file_id))
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
    built.reload()
    yield built
    writer.wait_merging_threads()


@pytest.fixture(scope="module")
def tied_index(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Index]:
    """Four documents that share one timestamp, so that only the tie decides.

    The bodies are the ones of the main fixture, so the same search line matches
    all four of them and the order of the answer can only come from the sort.
    """
    directory = tmp_path_factory.mktemp("tied-index")
    built = open_index(directory, CONSTITUENTS)
    writer = built.writer(heap_size=15_000_000, num_threads=1)
    for file_id in TIED_IDS:
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, f"Akte-{file_id}.pdf")
        document.add_text(FIELD_TITLE, f"Akte {file_id}")
        document.add_text(FIELD_PATH, f"/Akten/Akte-{file_id}.pdf")
        document.add_text(FIELD_EXT, "pdf")
        document.add_text(FIELD_BODY_DE, _body(file_id))
        document.add_integer(FIELD_MTIME, TIED_MTIME)
        writer.add_document(document)
    writer.commit()
    built.reload()
    yield built
    writer.wait_merging_threads()


@pytest.fixture(scope="module")
def mass_index(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Index]:
    """One hundred and sixty documents that share one timestamp.

    The tie group is larger than one scan portion on purpose: only then does the
    per-portion second key of FILT-02 have a boundary to fall apart at, and only
    then can two requests with different depths decompose the sequence
    differently.
    """
    directory = tmp_path_factory.mktemp("mass-index")
    built = open_index(directory, CONSTITUENTS)
    writer = built.writer(heap_size=15_000_000, num_threads=1)
    for file_id in MASS_WRITE_ORDER:
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, f"Akte-{file_id}.pdf")
        document.add_text(FIELD_TITLE, f"Akte {file_id}")
        document.add_text(FIELD_PATH, f"/Akten/Akte-{file_id}.pdf")
        document.add_text(FIELD_EXT, "pdf")
        document.add_text(FIELD_BODY_DE, _body(file_id))
        document.add_integer(FIELD_MTIME, MASS_MTIME)
        writer.add_document(document)
    writer.commit()
    built.reload()
    yield built
    writer.wait_merging_threads()


@pytest.fixture
def mass_store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    for file_id in range(1, MASS_DOCUMENTS + 1):
        opened.replace_acl(file_id, [BOB])
    yield opened
    opened.close()


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    for file_id in range(1, DOCUMENTS + 1):
        visible = [BOB] if file_id % 2 == 0 else [ALICE, BOB]
        opened.replace_acl(file_id, visible)
    yield opened
    opened.close()


def _query(index: Index, text: str = "Kündigungsfrist") -> Query:
    rewritten = build_query(index, text)
    assert rewritten.query is not None
    return rewritten.query


def _unfiltered_order(index: Index, text: str = "Kündigungsfrist") -> list[int]:
    searcher = index.searcher()
    found: list[int] = []
    for _, address in searcher.search(_query(index, text), DOCUMENTS).hits:
        value = searcher.doc(address).get_first(FIELD_FILE_ID)
        assert value is not None
        found.append(int(value))
    return found


def test_candidates_hold_only_what_the_prefilter_confirmed(index: Index, store: Store) -> None:
    page = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS)

    assert [candidate.file_id for candidate in page.candidates] != []
    assert all(candidate.file_id % 2 == 1 for candidate in page.candidates)


def test_a_candidate_carries_no_name_no_path_and_no_text(index: Index, store: Store) -> None:
    page = candidates(index, store, BOB, _query(index), limit=1)

    names = {field.name for field in dataclasses.fields(page.candidates[0])}

    assert names == {"file_id", "score", "mtime"}


def test_the_candidate_model_cannot_grow_a_text_field_by_accident() -> None:
    # A structural check, because the leak this prevents is invisible in a
    # result: everything the user finally sees was filtered again in PHP.
    source = SEARCH_SOURCE.read_text(encoding="utf-8")

    for forbidden in ('"title"', '"path"', '"snippet"', '"body'):
        assert forbidden not in source


def test_the_page_says_whether_more_results_exist(index: Index, store: Store) -> None:
    page = candidates(index, store, BOB, _query(index), limit=4)

    assert len(page.candidates) == 4
    assert page.has_more is True
    assert page.next_offset == 4


def test_the_last_page_says_that_it_is_the_last(index: Index, store: Store) -> None:
    page = candidates(index, store, BOB, _query(index), limit=DOCUMENTS)

    assert page.has_more is False
    assert page.next_offset == DOCUMENTS


def test_the_next_page_does_not_repeat_the_first(index: Index, store: Store) -> None:
    first = candidates(index, store, BOB, _query(index), limit=4)
    second = candidates(index, store, BOB, _query(index), limit=4, offset=first.next_offset)

    first_ids = [candidate.file_id for candidate in first.candidates]
    second_ids = [candidate.file_id for candidate in second.candidates]

    assert len(second_ids) == 4
    assert set(first_ids).isdisjoint(second_ids)


def test_the_offset_counts_permitted_candidates_not_raw_hits(index: Index, store: Store) -> None:
    # alice sees every second document, so a cursor in raw engine hits would
    # advance twice as fast as her result list and skip half of her hits.
    everything = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS).candidates

    second = candidates(index, store, ALICE, _query(index), limit=2, offset=2)

    assert second.candidates == everything[2:4]


def test_paging_through_a_filtered_ranking_loses_no_hit(index: Index, store: Store) -> None:
    everything = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS).candidates

    walked = []
    offset = 0
    for _ in range(DOCUMENTS):
        page = candidates(index, store, ALICE, _query(index), limit=2, offset=offset)
        walked.extend(page.candidates)
        assert page.next_offset == offset + len(page.candidates)
        offset = page.next_offset
        if not page.has_more:
            break

    assert walked == everything


def test_user_without_acl_rows_gets_an_empty_list(index: Index, store: Store) -> None:
    page = candidates(index, store, CAROL, _query(index), limit=DOCUMENTS)

    assert page.candidates == []
    assert page.has_more is False


def test_no_total_hit_count_leaves_the_module(index: Index, store: Store) -> None:
    page = candidates(index, store, ALICE, _query(index), limit=2)

    names = {field.name for field in dataclasses.fields(page)}

    # hasMore is the only thing the caller learns about what it did not get.
    assert names == {"candidates", "has_more", "next_offset"}


def test_the_score_order_survives_the_filter(index: Index, store: Store) -> None:
    expected = [file_id for file_id in _unfiltered_order(index) if file_id % 2 == 1]

    page = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS)

    assert [candidate.file_id for candidate in page.candidates] == expected


def test_a_query_without_hits_is_not_an_error(index: Index, store: Store) -> None:
    page = candidates(index, store, BOB, _query(index, "Weltraumbahnhof"), limit=10)

    assert page.candidates == []
    assert page.has_more is False
    assert page.next_offset == 0


def test_every_candidate_carries_its_modification_time(index: Index, store: Store) -> None:
    page = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS)

    for candidate in page.candidates:
        assert candidate.mtime == 1_700_000_000 + candidate.file_id
        assert candidate.score > 0.0


def test_the_permission_prefilter_is_called_at_exactly_two_places() -> None:
    # T-06-25, and the reason it is a source read rather than a behaviour test:
    # a second call site would be a second place that decides what a user may
    # see, and it would be perfectly green in every functional test. The two
    # that are allowed are the candidate round and the snippet cut, and the
    # merge of the vector branch runs above the first of them.
    source = SEARCH_SOURCE.read_text(encoding="utf-8")

    assert source.count("prefilter_visible") == 2


# ---------------------------------------------------------------------------
# The sorted mode: order out of the engine, and no relevance to report
# ---------------------------------------------------------------------------


def _ids(page: CandidatePage) -> list[int]:
    return [candidate.file_id for candidate in page.candidates]


def _filtered(index: Index, groups: list[str], text: str = "Kündigungsfrist") -> tuple[Query, Query | None]:
    """The engine query and the same filter once more, the way a route builds them."""
    rewritten = build_query(index, text, groups=groups)
    assert rewritten.query is not None
    return rewritten.query, rewritten.filter_query


def test_the_newest_sort_answers_by_falling_modification_time(index: Index, store: Store) -> None:
    # The timestamps of the fixture rise with the file id, so the expected order
    # is readable without a second lookup.
    page = candidates(index, store, BOB, _query(index), limit=DOCUMENTS, sort="newest")

    assert _ids(page) == list(range(DOCUMENTS, 0, -1))
    assert [candidate.mtime for candidate in page.candidates] == sorted(
        (1_700_000_000 + file_id for file_id in range(1, DOCUMENTS + 1)), reverse=True
    )


def test_the_oldest_sort_answers_by_rising_modification_time(index: Index, store: Store) -> None:
    page = candidates(index, store, BOB, _query(index), limit=DOCUMENTS, sort="oldest")

    assert _ids(page) == list(range(1, DOCUMENTS + 1))


def test_a_sort_changes_the_order_and_never_the_set(index: Index, store: Store) -> None:
    # Two searches with the same line have to answer the same documents; only
    # their sequence may differ. A set that moves with the sort would mean the
    # sorted branch searches something else than the relevance branch.
    relevance = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS)
    newest = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS, sort="newest")
    oldest = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS, sort="oldest")

    assert sorted(_ids(newest)) == sorted(_ids(relevance)) != []
    assert sorted(_ids(oldest)) == sorted(_ids(relevance))
    assert _ids(newest) == list(reversed(_ids(oldest)))


@pytest.mark.parametrize("sort", ["newest", "oldest"])
def test_no_hit_of_a_sorted_page_carries_a_relevance_value(index: Index, store: Store, sort: str) -> None:
    # D-04, and the failure it prevents is a loud one: under order_by_field the
    # engine hands back the field value in the place of the score, so a hit that
    # took it as it comes would show a timestamp of about 1.7e9 as its relevance.
    page = candidates(index, store, BOB, _query(index), limit=DOCUMENTS, sort=sort)

    assert page.candidates != []
    assert all(candidate.score == 0.0 for candidate in page.candidates)


def test_a_tie_is_broken_by_the_file_id(tied_index: Index, store: Store) -> None:
    # All four documents carry one timestamp, so tantivy alone would answer them
    # in the order they were written (7, 3, 9, 1). The second key is handwork,
    # and this is the case that says so.
    newest = candidates(tied_index, store, BOB, _query(tied_index), limit=DOCUMENTS, sort="newest")
    oldest = candidates(tied_index, store, BOB, _query(tied_index), limit=DOCUMENTS, sort="oldest")

    assert _ids(newest) == [9, 7, 3, 1]
    assert _ids(oldest) == [1, 3, 7, 9]


def test_two_sorted_pages_are_the_one_deep_page(index: Index, store: Store) -> None:
    # The offset of the sorted branch counts permitted candidates as well, and a
    # tie that falls apart at a portion boundary must produce neither a
    # duplicate nor a gap.
    deep = candidates(index, store, BOB, _query(index), limit=DOCUMENTS, sort="newest")

    first = candidates(index, store, BOB, _query(index), limit=5, sort="newest")
    second = candidates(index, store, BOB, _query(index), limit=5, offset=first.next_offset, sort="newest")

    assert first.has_more is True
    assert first.candidates + second.candidates == deep.candidates[:10]


@pytest.mark.parametrize("sort", ["newest", "oldest"])
def test_pages_of_unequal_depth_repeat_and_lose_nothing_across_a_portion_boundary(
    mass_index: Index, mass_store: Store, sort: str
) -> None:
    # The finding of 18.09.2026 at the running instance: 300 rows over twelve
    # pages held only 273 distinct documents, and the duplicates began exactly
    # where ``needed`` first exceeded the minimum portion size. A portion
    # boundary that depends on the requested depth decomposes one tie group
    # differently per request, so the offset slices of neighbouring pages
    # overlap and skip. Every page, whatever its depth, must reproduce the one
    # sequence the deep read answers.
    deep = candidates(mass_index, mass_store, BOB, _query(mass_index), limit=MASS_DOCUMENTS, sort=sort)
    assert len(deep.candidates) == MASS_DOCUMENTS

    paged: list[int] = []
    offset = 0
    for _ in range(MASS_DOCUMENTS // MASS_PAGE + 2):
        page = candidates(mass_index, mass_store, BOB, _query(mass_index), limit=MASS_PAGE, offset=offset, sort=sort)
        paged.extend(_ids(page))
        if not page.has_more:
            break
        offset = page.next_offset

    assert len(paged) == len(set(paged)), "a page transition repeated a document"
    assert paged == _ids(deep)


def test_an_unknown_sort_name_answers_the_relevance_order(index: Index, store: Store) -> None:
    # The route already holds its three values against the table, so a word that
    # arrives here anyway is a typo in an address and not a reason for an
    # exception that would leave the page with a server error.
    expected = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS)

    page = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS, sort="neueste")

    assert _ids(page) == _ids(expected) != []


def test_a_user_without_a_permission_row_gets_nothing_under_a_sort_either(index: Index, store: Store) -> None:
    # Pitfall G in its smallest form: an empty answer is the normal case of this
    # mode on a large foreign holding, and it stays an empty page rather than an
    # error or an unfiltered list.
    page = candidates(index, store, CAROL, _query(index), limit=DOCUMENTS, sort="newest")

    assert page.candidates == []
    assert page.has_more is False
    assert page.next_offset == 0


# ---------------------------------------------------------------------------
# The filter, before the window rather than behind it
# ---------------------------------------------------------------------------


def test_a_type_filter_answers_only_documents_of_that_type(index: Index, store: Store) -> None:
    # The odd ids carry pdf, the even ones docx. Filtering behind the window
    # would leave the page half empty instead; it is full here, which is the
    # second half of success criterion 1.
    query, filter_query = _filtered(index, ["pdf"])

    page = candidates(index, store, BOB, query, limit=4, filter_query=filter_query)

    assert len(page.candidates) == 4
    assert all(candidate.file_id % 2 == 1 for candidate in page.candidates)
    assert page.has_more is True


def test_a_type_filter_holds_under_a_sort_as_well(index: Index, store: Store) -> None:
    query, filter_query = _filtered(index, ["pdf"])

    page = candidates(index, store, BOB, query, limit=DOCUMENTS, filter_query=filter_query, sort="newest")

    assert _ids(page) == [file_id for file_id in range(DOCUMENTS, 0, -1) if file_id % 2 == 1]


def test_a_filter_that_matches_nothing_is_an_empty_page_and_not_an_error(index: Index, store: Store) -> None:
    # no_data: the fixture holds no presentation at all, and the answer is a
    # valid page rather than an exception.
    query, filter_query = _filtered(index, ["presentations"])

    page = candidates(index, store, BOB, query, limit=DOCUMENTS, filter_query=filter_query)

    assert page.candidates == []
    assert page.has_more is False
    assert page.next_offset == 0


def test_the_merge_never_asks_who_may_see_a_document() -> None:
    # The other half of the same statement. index/fusion.py takes two ranked
    # lists of numbers and answers one, and a permission question in there
    # would be a third authority nobody asked for.
    fusion = SEARCH_SOURCE.with_name("fusion.py").read_text(encoding="utf-8")

    assert "prefilter_visible" not in fusion
    assert "uid" not in fusion
