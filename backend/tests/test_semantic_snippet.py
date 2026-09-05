"""The excerpt of a purely semantic hit: the rank chunk, cut behind the prefilter.

A hit that only the vector branch found has by definition no literal overlap
with the query, so the SnippetGenerator answers an empty fragment and the user
sees a hit without any preview. D-13 says that hit still gets text: the two
character offsets stored beside every vector name the passage that matched, and
the passage is cut out of the stored body.

Three properties carry this file, and two of them are about order rather than
about text.

**The order is the security property.** ``snippets_for`` asks the prefilter as
its first action, before a byte of text is read, because an excerpt is file
content and whoever reaches the proxy could otherwise ask for the content of any
document by its number (T-06-37, T-06-38). The second excerpt path lives inside
the same loop body as the first one, behind the same check, and the cases below
assert that with stand-ins that fail the test the moment they are called for a
document the prefilter refused.

**The offsets are characters and never bytes.** This project has measured the
confusion once already (the engine reports (35, 51) where the character range is
(35, 50)), and an offset in the wrong unit cuts every semantic excerpt in the
wrong place, silently, and only in documents that carry non ascii text, which in
German is all of them (T-06-40). Two cases put ten umlauts and a French sentence
with an accent and a cedilla in front of the passage.

**A failure of the vector branch costs the semantics and never the search.**
Without a vector store, without a model, or with a model that raises,
``snippets_for`` behaves element for element as it did before this plan, and no
log line carries the query (T-06-39).
"""

from __future__ import annotations

import dataclasses
import hashlib
from collections.abc import Iterator
from pathlib import Path

import pytest

from findling.store.vectors import (
    EMBEDDING_DIMENSIONS,
    BestChunk,
    Chunk,
    DimensionMismatch,
    VectorStore,
    open_vectors,
)


def a_vector(seed: int) -> bytes:
    """One deterministic int8 vector, the width the column is declared with.

    SHA-256 in counter mode, the construction test_vector_store.py uses: an int8
    vector is raw bytes to sqlite-vec, so no float conversion and no model has
    to exist for these cases to run.
    """
    raw = b""
    counter = 0
    while len(raw) < EMBEDDING_DIMENSIONS:
        raw += hashlib.sha256(f"semantic-snippet:{seed}:{counter}".encode()).digest()
        counter += 1
    return raw[:EMBEDDING_DIMENSIONS]


def axis_vector(axis: int) -> bytes:
    """One int8 vector that points along a single axis.

    Readable distances: two vectors on the same axis are identical, two on
    different axes are as far apart as this construction gets. The same device
    test_semantic_search.py uses, without the float detour.
    """
    return bytes(127 if index == axis else 0 for index in range(EMBEDDING_DIMENSIONS))


def a_chunk(ordinal: int, *, axis: int, start: int, end: int) -> Chunk:
    """One chunk with an explicit place in the text and an explicit direction."""
    return Chunk(ordinal=ordinal, char_start=start, char_end=end, embedding=axis_vector(axis))


@pytest.fixture
def vectors(tmp_path: Path) -> Iterator[VectorStore]:
    opened = open_vectors(tmp_path / "vectors.db")
    yield opened
    opened.close()


def selects(statements: list[str]) -> list[str]:
    """The SELECT statements of a traced call, the counter of the band cases."""
    return [line for line in statements if line.lstrip().upper().startswith("SELECT")]


# ---------------------------------------------------------------------------
# best_chunk_for: the fourth operation of the vector store
# ---------------------------------------------------------------------------


def test_best_chunk_for_answers_the_closest_chunk_of_each_file(vectors: VectorStore) -> None:
    # Two chunks per document and the query points at the second one of file 7
    # and at the first one of file 8, so the answer cannot be "the first chunk"
    # by accident.
    vectors.replace_chunks(7, [a_chunk(0, axis=1, start=0, end=100), a_chunk(1, axis=2, start=100, end=200)])
    vectors.replace_chunks(8, [a_chunk(0, axis=2, start=0, end=50), a_chunk(1, axis=1, start=50, end=120)])

    best = vectors.best_chunk_for([7, 8], axis_vector(2))

    assert sorted(best) == [7, 8]
    assert (best[7].char_start, best[7].char_end) == (100, 200)
    assert (best[8].char_start, best[8].char_end) == (0, 50)


def test_best_chunk_for_answers_at_most_one_entry_per_file(vectors: VectorStore) -> None:
    vectors.replace_chunks(
        7, [a_chunk(ordinal, axis=1, start=ordinal * 10, end=ordinal * 10 + 8) for ordinal in range(5)]
    )

    best = vectors.best_chunk_for([7], axis_vector(1))

    assert list(best) == [7]


def test_best_chunk_for_asks_about_the_given_files_and_not_about_the_stock(vectors: VectorStore) -> None:
    # The direction of prefilter_visible: given candidates, which of them are
    # permitted. Searching the whole stock and filtering afterwards would spend
    # ranking time on documents the recheck has already refused, and here it
    # would answer with the wrong document as well: file 9 sits exactly on the
    # query and is not asked about.
    vectors.replace_chunks(7, [a_chunk(0, axis=1, start=0, end=40)])
    vectors.replace_chunks(9, [a_chunk(0, axis=2, start=0, end=40)])

    best = vectors.best_chunk_for([7], axis_vector(2))

    assert list(best) == [7]
    assert best[7].file_id == 7


def test_best_chunk_for_without_file_ids_asks_nothing(vectors: VectorStore) -> None:
    # An empty IN list is a syntax error in SQL, and this case arrives on every
    # snippet call whose ids the prefilter refused in full.
    statements: list[str] = []
    vectors.trace(statements.append)
    try:
        assert vectors.best_chunk_for([], a_vector(0)) == {}
    finally:
        vectors.trace(None)

    assert statements == []


def test_a_file_without_chunks_is_absent_and_not_an_error(vectors: VectorStore) -> None:
    # The ordinary shape of this question: the caller asks about a page of
    # confirmed files and most of them carry no vectors at all.
    vectors.replace_chunks(7, [a_chunk(0, axis=1, start=0, end=40)])

    best = vectors.best_chunk_for([7, 8, 999], axis_vector(1))

    assert list(best) == [7]


def test_best_chunk_for_bands_long_id_lists(vectors: VectorStore) -> None:
    # 2500 ids are three bands, the same band size prefilter_visible uses: the
    # parameter limit of a SQLite build is a compile time option and our lists
    # are not.
    for file_id in (500, 1500, 2400):
        vectors.replace_chunks(file_id, [a_chunk(0, axis=1, start=0, end=40)])

    statements: list[str] = []
    vectors.trace(statements.append)
    try:
        best = vectors.best_chunk_for(list(range(2500)), axis_vector(1))
    finally:
        vectors.trace(None)

    assert sorted(best) == [500, 1500, 2400]
    assert len(selects(statements)) == 3


def test_the_answer_carries_numbers_and_nothing_else(vectors: VectorStore) -> None:
    # The privacy contract of this module: nothing that leaves it is text. The
    # field set is checked rather than trusted, exactly as it is for Neighbour.
    vectors.replace_chunks(7, [a_chunk(0, axis=1, start=0, end=40)])

    best = vectors.best_chunk_for([7], axis_vector(1))

    assert {field.type for field in dataclasses.fields(BestChunk)} == {"int"}
    assert all(isinstance(getattr(best[7], field.name), int) for field in dataclasses.fields(BestChunk))


def test_a_vector_of_the_wrong_width_is_the_named_error_of_this_module(vectors: VectorStore) -> None:
    # The same refusal nearest gives, and for the same reason: an empty answer
    # would be indistinguishable from "this document has no chunks".
    vectors.replace_chunks(7, [a_chunk(0, axis=1, start=0, end=40)])

    with pytest.raises(DimensionMismatch):
        vectors.best_chunk_for([7], a_vector(0)[:-1])


def test_the_module_header_names_four_operations() -> None:
    # The abstraction cut of D-08 is only worth something while the header of
    # the module is the list of everything the container may ask of a vector
    # store. A fourth operation that is not in that list is a fifth one waiting
    # to be written somewhere else.
    header = (Path(__file__).resolve().parents[1] / "src" / "findling" / "store" / "vectors.py").read_text(
        encoding="utf-8"
    )

    assert "four operations" in header
    assert "best_chunk_for" in header


def test_no_dash_of_either_kind_in_the_two_files_of_this_task() -> None:
    # Built from their code points so that this assertion does not carry the
    # characters it exists to keep out.
    em_dash = chr(0x2014)
    en_dash = chr(0x2013)
    backend = Path(__file__).resolve().parents[1]
    touched = [
        backend / "src" / "findling" / "store" / "vectors.py",
        backend / "src" / "findling" / "index" / "search.py",
        backend / "src" / "findling" / "api" / "snippets.py",
        Path(__file__),
    ]

    for source in touched:
        text = source.read_text(encoding="utf-8")
        assert em_dash not in text, source.name
        assert en_dash not in text, source.name
