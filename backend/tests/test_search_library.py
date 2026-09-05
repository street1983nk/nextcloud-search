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
from findling.index.search import candidates
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


def test_the_merge_never_asks_who_may_see_a_document() -> None:
    # The other half of the same statement. index/fusion.py takes two ranked
    # lists of numbers and answers one, and a permission question in there
    # would be a third authority nobody asked for.
    fusion = SEARCH_SOURCE.with_name("fusion.py").read_text(encoding="utf-8")

    assert "prefilter_visible" not in fusion
    assert "uid" not in fusion
