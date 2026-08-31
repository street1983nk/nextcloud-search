"""Highlight positions: characters on the wire, bytes from the engine.

The test that matters most in this file is the first one, and it only matters
because of one detail: it has an umlaut **before** the match. Without that, the
byte count and the character count are the same number, the test stays green
whether or not anything is converted, and it documents nothing. That is exactly
why this class of bug survives for years: the highlight sits one character too
far right, the text around it is correct, and nobody reports it.

The second recurring theme is that the engine reports the same range several
times. Every part of a split compound inherits the offsets of the whole word, so
a search for one constituent produces one range per part, all of them identical
or overlapping. Merging them is not cosmetic: a client that renders each range on
its own would wrap the same word two or three times.
"""

from collections.abc import Iterator
from dataclasses import dataclass
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
from findling.index.search import char_ranges, snippets_for
from findling.query.rewrite import build_query
from findling.store.repo import Store, open_store

SEARCH_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "index" / "search.py"

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()

OWNER = "owner"
STRANGER = "stranger"

CORPUS = (
    (1, "Kündigung.pdf", "Sehr geehrte Damen und Herren, die Kündigungsfrist für Ihren Vertrag beträgt drei Monate."),
    (2, "Antrag.pdf", "Herr Müller hat die Grundstücksverkehrsgenehmigung im März beantragt."),
    (3, "Notiz.txt", "Diese Notiz enthält nichts von Belang."),
)


@dataclass(frozen=True, slots=True)
class _Range:
    """Stands in for a tantivy Range in the tests of the pure function."""

    start: int
    end: int


@pytest.fixture(scope="module")
def index(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Index]:
    directory = tmp_path_factory.mktemp("snippet-index")
    built = open_index(directory, CONSTITUENTS)
    writer = built.writer(heap_size=15_000_000, num_threads=1)
    for file_id, name, body in CORPUS:
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, name)
        document.add_text(FIELD_TITLE, name.rsplit(".", maxsplit=1)[0])
        document.add_text(FIELD_PATH, f"/Akten/{name}")
        document.add_text(FIELD_EXT, name.rsplit(".", maxsplit=1)[1])
        document.add_text(FIELD_BODY_DE, body)
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
    built.reload()
    yield built
    writer.wait_merging_threads()


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    for file_id, _, _ in CORPUS:
        opened.replace_acl(file_id, [OWNER])
    yield opened
    opened.close()


def _query(index: Index, text: str) -> Query:
    rewritten = build_query(index, text)
    assert rewritten.query is not None
    return rewritten.query


def test_umlaut_before_the_match_shifts_nothing() -> None:
    # Two multi byte characters before the match. Without the conversion the
    # naive slice would be off by exactly those two bytes, and the assertion
    # below is the only thing that can tell the difference.
    fragment = "Die Kündigung für die Frist"
    byte_start = len("Die Kündigung für die ".encode())

    got = char_ranges(fragment, [_Range(byte_start, byte_start + len("Frist"))])

    assert fragment[got[0][0] : got[0][1]] == "Frist"
    assert got[0][0] != byte_start


def test_a_range_reported_twice_appears_once() -> None:
    # What a split compound produces: one identical range per constituent.
    fragment = "Die Kündigungsfrist läuft."

    got = char_ranges(fragment, [_Range(4, 24), _Range(4, 24)])

    assert got == [(4, 22)]


def test_overlapping_ranges_are_merged_into_one() -> None:
    fragment = "Kuendigungsfrist"

    got = char_ranges(fragment, [_Range(0, 11), _Range(10, 16)])

    assert got == [(0, 16)]


def test_ranges_that_do_not_touch_stay_apart() -> None:
    fragment = "Frist und Frist"

    got = char_ranges(fragment, [_Range(10, 15), _Range(0, 5)])

    assert got == [(0, 5), (10, 15)]


def test_searching_one_constituent_marks_the_whole_compound(index: Index, store: Store) -> None:
    found = snippets_for(index, store, OWNER, _query(index, "Genehmigung"), [2])

    assert len(found) == 1
    start, end = found[0].highlights[0]

    assert found[0].text[start:end] == "Grundstücksverkehrsgenehmigung"


def test_the_fragment_is_plain_text_without_markup(index: Index, store: Store) -> None:
    found = snippets_for(index, store, OWNER, _query(index, "Kündigungsfrist"), [1])

    assert "<" not in found[0].text
    assert "Kündigungsfrist" in found[0].text


def test_the_module_never_asks_for_the_html_form() -> None:
    # The unified search subline is rendered as text, so any tag would reach the
    # user verbatim. A static check, because the wrong call would look fine in
    # every unit test and only break in the browser.
    assert "to_html" not in SEARCH_SOURCE.read_text(encoding="utf-8")


def test_a_document_without_a_match_yields_an_empty_snippet(index: Index, store: Store) -> None:
    found = snippets_for(index, store, OWNER, _query(index, "Kündigungsfrist"), [3])

    assert len(found) == 1
    assert found[0].text == ""
    assert found[0].highlights == []


def test_snippets_are_produced_only_for_confirmed_file_ids(index: Index, store: Store) -> None:
    # The confused deputy case: whoever reaches this function must not be able to
    # cut text out of a document they were never allowed to see.
    found = snippets_for(index, store, STRANGER, _query(index, "Kündigungsfrist"), [1, 2, 3])

    assert found == []


def test_an_empty_list_of_file_ids_is_not_an_error(index: Index, store: Store) -> None:
    assert snippets_for(index, store, OWNER, _query(index, "Kündigungsfrist"), []) == []


def test_the_answer_keeps_the_order_of_the_requested_ids(index: Index, store: Store) -> None:
    found = snippets_for(index, store, OWNER, _query(index, "Frist"), [2, 1])

    assert [snippet.file_id for snippet in found] == [2, 1]
