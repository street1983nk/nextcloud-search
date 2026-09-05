"""The vector store: three operations, one delete order, and no text on any path.

This file is the gate of the abstraction cut of D-08. The vector half of the
search is allowed to be exchanged later (bit vectors, usearch), and the price of
that freedom is that everything the rest of the container may ask of it is
named here, in one place, and nowhere else.

Four properties carry the rest:

* **A redelivery cannot double the stock.** ``replace_chunks`` deletes before it
  inserts, in one transaction, exactly like ``Store.replace_acl`` and
  ``IndexBatchWriter.add``. A batch that is interrupted after the commit and
  before the acknowledgement comes back, and without the deletion it would
  leave every chunk of that file twice (pitfall 5 of the phase research).
* **Nothing that leaves this module is text.** ``nearest`` answers with numbers
  only. A snippet is cut in ``snippets_for``, behind ``prefilter_visible`` and
  behind the PHP recheck, and the two character offsets stored here are what
  makes that possible for a purely semantic hit at all (D-13, T-06-15).
* **A missing extension is a state and not a stack trace.** The caller has to be
  able to answer a failed load with a degraded search rather than with a 500
  (D-19), so it gets a named exception of this module instead of whatever
  sqlite3 raised.
* **A wrong shape is loud.** A query vector of the wrong width is a defect in
  the caller, and a silently empty result would look like "nothing similar
  found" for as long as nobody measured recall.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Iterator
from dataclasses import fields
from pathlib import Path

import pytest

from findling.store.vectors import (
    EMBEDDING_DIMENSIONS,
    Chunk,
    DimensionMismatch,
    ExtensionUnavailable,
    Neighbour,
    VectorStore,
    embedding_mark,
    open_vectors,
)

SOURCE_DIR = Path(__file__).resolve().parents[1] / "src" / "findling" / "store"
MODULE = SOURCE_DIR / "vectors.py"
SCHEMA = SOURCE_DIR / "vectors.sql"

# Built from their code points rather than written as themselves, so that this
# file does not carry the two characters it exists to keep out. Same device as
# in test_store_metadata.py, and for the same reason.
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)


def a_vector(seed: int) -> bytes:
    """One deterministic int8 vector, the width the column is declared with.

    SHA-256 in counter mode, the same construction the wave 0 probe uses: an
    int8 vector is raw bytes to sqlite-vec, so no float conversion and no model
    has to exist for these tests to run.
    """
    raw = b""
    counter = 0
    while len(raw) < EMBEDDING_DIMENSIONS:
        raw += hashlib.sha256(f"vector-store:{seed}:{counter}".encode()).digest()
        counter += 1
    return raw[:EMBEDDING_DIMENSIONS]


def a_chunk(ordinal: int, *, seed: int | None = None) -> Chunk:
    """One chunk of a document, with plausible character offsets."""
    return Chunk(
        ordinal=ordinal,
        char_start=ordinal * 2048,
        char_end=ordinal * 2048 + 2000,
        embedding=a_vector(ordinal if seed is None else seed),
    )


@pytest.fixture
def vectors(tmp_path: Path) -> Iterator[VectorStore]:
    opened = open_vectors(tmp_path / "vectors.db")
    yield opened
    opened.close()


def counts(store: VectorStore) -> tuple[int, int]:
    """Rows in ``chunks`` and rows in ``chunk_vectors``, which have to agree."""
    return store.chunk_count(), store.vector_count()


# -- opening ---------------------------------------------------------------


def test_open_vectors_creates_the_schema_and_is_idempotent(tmp_path: Path) -> None:
    # Every statement of vectors.sql is IF NOT EXISTS, so open_vectors runs it on
    # every start, exactly like open_store does with schema.sql.
    path = tmp_path / "vectors.db"

    first = open_vectors(path)
    first.replace_chunks(1, [a_chunk(0)])
    first.close()

    second = open_vectors(path)
    try:
        assert path.exists()
        assert counts(second) == (1, 1)
    finally:
        second.close()


def test_an_unloadable_extension_is_a_named_error_of_this_module(tmp_path: Path) -> None:
    # The caller has to be able to treat this as a state (D-19). A raw
    # sqlite3.OperationalError would force every caller to know which sqlite
    # message means "no vector search on this box".
    decoy = tmp_path / "vec0.so"
    decoy.write_bytes(b"this is not a shared object")

    with pytest.raises(ExtensionUnavailable):
        open_vectors(tmp_path / "vectors.db", extension_path=str(decoy))


def test_a_missing_extension_file_is_the_same_named_error(tmp_path: Path) -> None:
    with pytest.raises(ExtensionUnavailable):
        open_vectors(tmp_path / "vectors.db", extension_path=str(tmp_path / "absent.so"))


def test_open_read_only_on_a_missing_file_raises(tmp_path: Path) -> None:
    # Same rule as open_read_only in repo.py: sqlite would happily create an
    # empty database here, and every semantic search would then answer "nothing
    # similar" instead of "the vector stock is gone".
    with pytest.raises(FileNotFoundError):
        open_vectors(tmp_path / "absent.db", read_only=True)


def test_the_read_connection_answers_knn_and_refuses_writes(tmp_path: Path) -> None:
    # Probe A12 of plan 06-01, as a property of this module rather than of a
    # measurement report: vec0 KNN runs under PRAGMA query_only = 1, so the
    # vector store is read the same way the rest of the read side is.
    path = tmp_path / "vectors.db"
    writer = open_vectors(path)
    writer.replace_chunks(4, [a_chunk(0), a_chunk(1)])
    writer.close()

    reader = open_vectors(path, read_only=True)
    try:
        assert len(reader.nearest(a_vector(0), 2)) == 2
        with pytest.raises(sqlite3.OperationalError):
            reader.replace_chunks(4, [a_chunk(0)])
    finally:
        reader.close()


# -- replace_chunks: the delete order --------------------------------------


def test_replace_chunks_writes_chunks_and_vectors_together(vectors: VectorStore) -> None:
    vectors.replace_chunks(7, [a_chunk(0), a_chunk(1)])

    assert counts(vectors) == (2, 2)
    spans = vectors.chunks_of([7])[7]
    assert [span.ordinal for span in spans] == [0, 1]
    assert [(span.char_start, span.char_end) for span in spans] == [(0, 2000), (2048, 4048)]


def test_the_same_call_twice_leaves_one_stock_and_not_two(vectors: VectorStore) -> None:
    # The redelivery. A batch that was interrupted after the commit and before
    # the acknowledgement comes back, and this is the whole reason the deletion
    # stands before the insert.
    chunks = [a_chunk(0), a_chunk(1)]

    vectors.replace_chunks(7, chunks)
    after_once = counts(vectors)
    vectors.replace_chunks(7, chunks)

    assert counts(vectors) == after_once == (2, 2)


def test_replace_chunks_touches_no_other_file(vectors: VectorStore) -> None:
    vectors.replace_chunks(7, [a_chunk(0), a_chunk(1)])
    vectors.replace_chunks(8, [a_chunk(0)])

    vectors.replace_chunks(7, [a_chunk(0)])

    assert counts(vectors) == (2, 2)
    assert len(vectors.chunks_of([8])[8]) == 1


def test_replace_chunks_with_an_empty_list_clears_the_file(vectors: VectorStore) -> None:
    # Not an error: a document whose text no longer produces a chunk, for
    # instance because it became empty, has to be able to lose its vectors
    # through the same call that would have written them.
    vectors.replace_chunks(7, [a_chunk(0), a_chunk(1)])

    vectors.replace_chunks(7, [])

    assert counts(vectors) == (0, 0)
    assert vectors.chunks_of([7]) == {}


def test_replace_chunks_on_an_unknown_file_is_no_error(vectors: VectorStore) -> None:
    vectors.replace_chunks(999, [])

    assert counts(vectors) == (0, 0)


def test_replace_chunks_deletes_more_than_one_band_of_vectors(vectors: VectorStore) -> None:
    # The rowid list of the deletion is banded like prefilter_visible, so a file
    # that carries more chunks than one band has to lose all of them. Without
    # the loop the tail would stay in chunk_vectors as an orphan that no delete
    # path ever reaches again.
    many = [a_chunk(ordinal, seed=ordinal % 32) for ordinal in range(1200)]
    vectors.replace_chunks(7, many)
    assert counts(vectors) == (1200, 1200)

    vectors.replace_chunks(7, [a_chunk(0)])

    assert counts(vectors) == (1, 1)


def test_a_rejected_batch_leaves_the_previous_stock_untouched(vectors: VectorStore) -> None:
    # Validation before the transaction, the rule repo.py states at
    # Store.record: a refused write leaves no trace and no open transaction.
    vectors.replace_chunks(7, [a_chunk(0), a_chunk(1)])
    broken = Chunk(ordinal=0, char_start=0, char_end=10, embedding=a_vector(0)[:-1])

    with pytest.raises(DimensionMismatch):
        vectors.replace_chunks(7, [a_chunk(0), broken])

    assert counts(vectors) == (2, 2)
    assert len(vectors.chunks_of([7])[7]) == 2


# -- the two delete paths --------------------------------------------------


def test_drop_vectors_removes_chunks_and_vectors_of_one_file(vectors: VectorStore) -> None:
    vectors.replace_chunks(7, [a_chunk(0), a_chunk(1)])
    vectors.replace_chunks(8, [a_chunk(0)])

    removed = vectors.drop_vectors(7)

    assert removed == 2
    assert counts(vectors) == (1, 1)
    assert vectors.chunks_of([7]) == {}


def test_drop_vectors_on_an_unknown_file_is_no_error(vectors: VectorStore) -> None:
    assert vectors.drop_vectors(999) == 0


def test_forget_all_empties_both_tables(vectors: VectorStore) -> None:
    # The reindex path. A rebuild that left the old vectors behind would answer
    # semantically out of a stock that belongs to another model.
    vectors.replace_chunks(7, [a_chunk(0), a_chunk(1)])
    vectors.replace_chunks(8, [a_chunk(0)])

    vectors.forget_all()

    assert counts(vectors) == (0, 0)
    assert vectors.nearest(a_vector(0), 5) == []


# -- nearest ---------------------------------------------------------------


def test_nearest_answers_up_to_k_neighbours_in_ascending_distance(vectors: VectorStore) -> None:
    vectors.replace_chunks(7, [a_chunk(ordinal) for ordinal in range(6)])

    found = vectors.nearest(a_vector(3), 3)

    assert len(found) == 3
    assert [neighbour.distance for neighbour in found] == sorted(neighbour.distance for neighbour in found)
    assert found[0].ordinal == 3
    assert found[0].distance == 0.0
    assert found[0].file_id == 7


def test_nearest_carries_the_span_of_its_chunk(vectors: VectorStore) -> None:
    # The reason char_start and char_end exist at all: a purely semantic hit has
    # no literal overlap, so the snippet generator would hand back an empty
    # fragment and the user would see a hit without any preview (D-13).
    vectors.replace_chunks(7, [a_chunk(0), a_chunk(1)])

    found = vectors.nearest(a_vector(1), 1)

    assert (found[0].char_start, found[0].char_end) == (2048, 4048)


def test_nearest_returns_numbers_and_never_text(vectors: VectorStore) -> None:
    # T-06-15. What this method answers is the raw material for everything that
    # later leaves the container, so the field set is checked rather than
    # trusted: no member of the answer may be able to carry content.
    vectors.replace_chunks(7, [a_chunk(0)])

    found = vectors.nearest(a_vector(0), 1)

    assert {field.type for field in fields(Neighbour)} == {"int", "float"}
    assert all(isinstance(getattr(found[0], field.name), int | float) for field in fields(Neighbour))


def test_nearest_on_an_empty_stock_is_empty_and_not_an_error(vectors: VectorStore) -> None:
    assert vectors.nearest(a_vector(0), 5) == []


def test_nearest_answers_fewer_than_k_when_the_stock_is_smaller(vectors: VectorStore) -> None:
    vectors.replace_chunks(7, [a_chunk(0), a_chunk(1)])

    assert len(vectors.nearest(a_vector(0), 50)) == 2


def test_the_cap_of_nearest_is_an_argument(vectors: VectorStore) -> None:
    # The cap is a parameter of the call and not a hidden ceiling: a caller that
    # wants a wider window says so, and the number it is measured against comes
    # from the wave 0 report.
    vectors.replace_chunks(7, [a_chunk(ordinal) for ordinal in range(10)])

    assert len(vectors.nearest(a_vector(0), 9, k_max=4)) == 4
    assert len(vectors.nearest(a_vector(0), 9, k_max=9)) == 9


def test_a_k_below_one_is_refused(vectors: VectorStore) -> None:
    vectors.replace_chunks(7, [a_chunk(0)])

    with pytest.raises(ValueError, match="k"):
        vectors.nearest(a_vector(0), 0)


def test_a_query_of_the_wrong_width_is_a_named_error(vectors: VectorStore) -> None:
    # 383 instead of 384. Silently answering nothing would look exactly like
    # "no similar document exists" until somebody measured recall.
    vectors.replace_chunks(7, [a_chunk(0)])

    with pytest.raises(DimensionMismatch):
        vectors.nearest(a_vector(0)[:-1], 5)


def test_a_stored_vector_of_the_wrong_width_is_a_named_error(vectors: VectorStore) -> None:
    broken = Chunk(ordinal=0, char_start=0, char_end=10, embedding=a_vector(0) + b"\x00")

    with pytest.raises(DimensionMismatch):
        vectors.replace_chunks(7, [broken])


# -- chunks_of -------------------------------------------------------------


def test_chunks_of_answers_per_file_and_in_ordinal_order(vectors: VectorStore) -> None:
    vectors.replace_chunks(7, [a_chunk(1), a_chunk(0)])
    vectors.replace_chunks(8, [a_chunk(0)])

    spans = vectors.chunks_of([7, 8])

    assert sorted(spans) == [7, 8]
    assert [span.ordinal for span in spans[7]] == [0, 1]
    assert [span.ordinal for span in spans[8]] == [0]


def test_chunks_of_bands_long_id_lists(vectors: VectorStore) -> None:
    # 2500 ids are three bands. Only three of them exist, which is the ordinary
    # shape of this question on the delete path: the caller asks about a page of
    # files and most of them carry no vectors at all.
    for file_id in (500, 1500, 2400):
        vectors.replace_chunks(file_id, [a_chunk(0)])

    spans = vectors.chunks_of(list(range(2500)))

    assert sorted(spans) == [500, 1500, 2400]


def test_chunks_of_without_ids_asks_nothing(vectors: VectorStore) -> None:
    # An empty IN list is a syntax error in SQL, and this case arrives on every
    # delete round that had nothing to delete.
    assert vectors.chunks_of([]) == {}


# -- the mark and the two artefacts ----------------------------------------


def test_the_embedding_mark_carries_model_quantisation_dimensions_and_cap() -> None:
    mark = embedding_mark("multilingual-e5-small", tokens=1024)

    assert mark == "multilingual-e5-small/int8/384/1024"
    assert embedding_mark("multilingual-e5-small", tokens=512) != mark


def test_every_statement_of_the_schema_is_if_not_exists() -> None:
    # The property open_vectors rests on: it applies the schema on every start,
    # so a statement without IF NOT EXISTS would turn the second start of a
    # container into an error.
    statements = [
        line for line in SCHEMA.read_text(encoding="utf-8").splitlines() if line.strip().upper().startswith("CREATE")
    ]

    assert statements != []
    assert all("IF NOT EXISTS" in line.upper() for line in statements)


def test_the_schema_says_characters_and_not_bytes() -> None:
    # The confusion has been measured in this project once already
    # (index/search.py: the engine reports (35, 51) where the character range is
    # (35, 50)), and a vector store that stores the wrong unit cuts every
    # semantic snippet in the wrong place.
    schema = SCHEMA.read_text(encoding="utf-8")
    comment = schema[: schema.index("char_start INTEGER")].lower()

    assert "character offsets" in comment
    assert "byte offsets" in comment


def test_the_module_reads_no_configuration() -> None:
    # Inherited from repo.py word for word: every path arrives as an argument,
    # which keeps the store testable without an environment and lets the caller
    # decide where its database lives.
    source = MODULE.read_text(encoding="utf-8")

    assert "from findling.config" not in source
    assert "from findling import config" not in source
    assert "import findling.config" not in source


def test_neither_artefact_carries_a_dash() -> None:
    for path in (MODULE, SCHEMA, Path(__file__)):
        source = path.read_text(encoding="utf-8")

        assert EM_DASH not in source, path.name
        assert EN_DASH not in source, path.name
