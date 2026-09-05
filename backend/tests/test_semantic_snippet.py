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
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from tantivy import Document, Index, Query

from findling.config import settings
from findling.embed.model import EmbedOutcome
from findling.index import search as index_search
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
from findling.index.search import SemanticSide, SnippetText, snippets_for
from findling.query.rewrite import build_query
from findling.store.repo import Store, open_store
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


# ---------------------------------------------------------------------------
# The second excerpt path, behind the prefilter and behind the recheck
# ---------------------------------------------------------------------------

OWNER = "owner"
STRANGER = "stranger"
OTHER = "other"

GERMAN_FILE = 1
FRENCH_FILE = 2
LONG_FILE = 3
FOREIGN_FILE = 4

# Ten umlauts in front of the passage. Without them a character offset and a
# byte offset name the same place and the assertion below would be green either
# way, which is exactly how this class of bug survives review.
GERMAN_PREFIX = "Äpfel, Öl, Über, Ärger, Öfen, Übung, Ähre, Öse, Übel, Änderung. "
GERMAN_PASSAGE = "Die Kündigungsfrist im Vertrag beträgt drei Monate."
GERMAN_TAIL = " Weitere Absätze folgen ohne Belang."

# The second alphabet of the same problem: an accent and a cedilla are two byte
# characters as well, and a container in a French office meets them first.
FRENCH_PREFIX = "Le garçon a suivi la leçon à côté du café. "
FRENCH_PASSAGE = "Le délai de résiliation du contrat est de trois mois."
FRENCH_TAIL = " D'autres paragraphes suivent."

LONG_BODY = "Ein Absatz ohne jeden Belang. " * 50
FOREIGN_BODY = "Vertrauliche Notiz über die Gehälter der Abteilung."

BODIES = {
    GERMAN_FILE: GERMAN_PREFIX + GERMAN_PASSAGE + GERMAN_TAIL,
    FRENCH_FILE: FRENCH_PREFIX + FRENCH_PASSAGE + FRENCH_TAIL,
    LONG_FILE: LONG_BODY,
    FOREIGN_FILE: FOREIGN_BODY,
}

# A line that occurs in no document of this corpus, asserted rather than
# assumed by the floor case below. Whatever text comes back for it can only
# have come out of the vector half.
PARAPHRASE = "Weltraumbahnhof"

# A line that does occur, for the cases about what must not change.
TERM = "Kündigungsfrist"

# The direction of the passage chunks, and a second one for the case that shows
# the closest chunk of a document decides rather than the first one.
PASSAGE_AXIS = 1
PREFIX_AXIS = 3

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()


class Embedder:
    """A model that answers from a table, the one stand-in of these cases.

    Anything it has no answer for becomes the ``embedding_unavailable`` verdict,
    which is what the real wrapper does when the artifact is missing, so the "no
    model" case needs no second class.
    """

    def __init__(self, answers: dict[str, bytes]) -> None:
        self._answers = answers

    def embed_query(self, text: str) -> EmbedOutcome:
        vector = self._answers.get(text)
        if vector is None:
            return EmbedOutcome.unavailable()
        # Back to floats, because that is the shape the wrapper answers in and
        # the caller quantises it again. Signed bytes divided by 127 is the
        # inverse of to_int8 for the axis vectors above.
        return EmbedOutcome.ready([tuple(value / 127 for value in vector)])


class BrokenEmbedder:
    """A model whose engine raises, with the query inside the message.

    The query is in the message on purpose: the log assertion is only worth
    something if there is something to leak.
    """

    def embed_query(self, text: str) -> EmbedOutcome:
        raise RuntimeError(f"the engine choked while reading {text}")


@pytest.fixture(scope="module")
def index(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Index]:
    directory = tmp_path_factory.mktemp("semantic-snippet-index")
    built = open_index(directory, CONSTITUENTS)
    writer = built.writer(heap_size=15_000_000, num_threads=1)
    for file_id, body in BODIES.items():
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, f"Akte-{file_id}.pdf")
        document.add_text(FIELD_TITLE, f"Akte {file_id}")
        document.add_text(FIELD_PATH, f"/Akten/Akte-{file_id}.pdf")
        document.add_text(FIELD_EXT, "pdf")
        document.add_text(FIELD_BODY_DE, body)
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
    built.reload()
    yield built
    writer.wait_merging_threads()


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    """The owner sees three documents. The fourth belongs to somebody else."""
    opened = open_store(tmp_path / "state.db")
    for file_id in (GERMAN_FILE, FRENCH_FILE, LONG_FILE):
        opened.replace_acl(file_id, [OWNER])
    opened.replace_acl(FOREIGN_FILE, [OTHER])
    yield opened
    opened.close()


@pytest.fixture
def stocked(vectors: VectorStore) -> VectorStore:
    """The real vector store, with the rank chunk of every document in it.

    The German document carries two chunks, one over the umlaut prefix and one
    over the passage, so the case about the closest chunk has something to
    choose between.
    """
    vectors.replace_chunks(
        GERMAN_FILE,
        [
            a_chunk(0, axis=PREFIX_AXIS, start=0, end=len(GERMAN_PREFIX)),
            a_chunk(
                1,
                axis=PASSAGE_AXIS,
                start=len(GERMAN_PREFIX),
                end=len(GERMAN_PREFIX) + len(GERMAN_PASSAGE),
            ),
        ],
    )
    vectors.replace_chunks(
        FRENCH_FILE,
        [
            a_chunk(
                0,
                axis=PASSAGE_AXIS,
                start=len(FRENCH_PREFIX),
                end=len(FRENCH_PREFIX) + len(FRENCH_PASSAGE),
            )
        ],
    )
    vectors.replace_chunks(LONG_FILE, [a_chunk(0, axis=PASSAGE_AXIS, start=0, end=len(LONG_BODY))])
    vectors.replace_chunks(FOREIGN_FILE, [a_chunk(0, axis=PASSAGE_AXIS, start=0, end=len(FOREIGN_BODY))])
    return vectors


def _query(index: Index, text: str) -> Query:
    rewritten = build_query(index, text)
    assert rewritten.query is not None
    return rewritten.query


def _side(vectors: VectorStore, text: str, *, axis: int = PASSAGE_AXIS) -> SemanticSide:
    return SemanticSide(vectors=vectors, model=Embedder({text: axis_vector(axis)}), text=text)


def _one(found: list[SnippetText]) -> SnippetText:
    assert len(found) == 1
    return found[0]


def test_the_generator_answers_nothing_to_a_line_that_is_not_in_the_corpus(index: Index, store: Store) -> None:
    # The floor under every case below. Without it a green semantic excerpt
    # could just mean that the line matched lexically after all.
    found = _one(snippets_for(index, store, OWNER, _query(index, PARAPHRASE), [GERMAN_FILE]))

    assert found.text == ""
    assert found.highlights == []


def test_a_purely_semantic_hit_gets_the_passage_of_its_rank_chunk(
    index: Index,
    store: Store,
    stocked: VectorStore,
) -> None:
    # Ten umlauts stand in front of this passage, so a cut on bytes would start
    # ten characters too far to the right and would run past the end of the
    # passage into the tail. The two conventions genuinely differ here, which is
    # what the second assertion states.
    found = _one(
        snippets_for(
            index,
            store,
            OWNER,
            _query(index, PARAPHRASE),
            [GERMAN_FILE],
            semantic=_side(stocked, PARAPHRASE),
        )
    )

    assert found.text == GERMAN_PASSAGE
    assert len(GERMAN_PREFIX.encode()) != len(GERMAN_PREFIX)


def test_a_hit_without_a_literal_match_carries_no_marks(
    index: Index,
    store: Store,
    stocked: VectorStore,
) -> None:
    # There is nothing to mark: the query does not occur in the document. A mark
    # here would point at a word the user never searched for.
    found = _one(
        snippets_for(
            index,
            store,
            OWNER,
            _query(index, PARAPHRASE),
            [GERMAN_FILE],
            semantic=_side(stocked, PARAPHRASE),
        )
    )

    assert found.text != ""
    assert found.highlights == []


def test_the_cut_lands_in_the_same_place_behind_an_accent_and_a_cedilla(
    index: Index,
    store: Store,
    stocked: VectorStore,
) -> None:
    found = _one(
        snippets_for(
            index,
            store,
            OWNER,
            _query(index, PARAPHRASE),
            [FRENCH_FILE],
            semantic=_side(stocked, PARAPHRASE),
        )
    )

    assert found.text == FRENCH_PASSAGE


def test_the_closest_chunk_of_the_document_decides_the_passage(
    index: Index,
    store: Store,
    stocked: VectorStore,
) -> None:
    # The same document, a query pointing at its other chunk. Without this the
    # cases above would stay green for an implementation that always takes the
    # first chunk of a document.
    found = _one(
        snippets_for(
            index,
            store,
            OWNER,
            _query(index, PARAPHRASE),
            [GERMAN_FILE],
            semantic=_side(stocked, PARAPHRASE, axis=PREFIX_AXIS),
        )
    )

    assert found.text == GERMAN_PREFIX


def test_a_passage_longer_than_the_cap_is_shortened_to_it(
    index: Index,
    store: Store,
    stocked: VectorStore,
) -> None:
    # A chunk is up to 1024 tokens and the subline of the unified search is one
    # line, so the second path answers to the same cap the generator does.
    cap = settings().snippet_chars

    found = _one(
        snippets_for(
            index,
            store,
            OWNER,
            _query(index, PARAPHRASE),
            [LONG_FILE],
            semantic=_side(stocked, PARAPHRASE),
        )
    )

    assert len(found.text) == cap
    assert found.text == LONG_BODY[:cap]


def test_a_confirmed_document_without_vectors_stays_a_hit_without_text(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    # The sentence that stays true: a hit without a snippet is still a hit, and
    # the subline falls back to the path on the PHP side.
    found = _one(
        snippets_for(
            index,
            store,
            OWNER,
            _query(index, PARAPHRASE),
            [GERMAN_FILE],
            semantic=_side(vectors, PARAPHRASE),
        )
    )

    assert found.text == ""
    assert found.highlights == []


def test_a_fragment_that_is_not_empty_is_left_exactly_as_it_was(
    index: Index,
    store: Store,
    stocked: VectorStore,
) -> None:
    # The first excerpt path keeps the last word wherever it has one. The
    # comparison is element for element against the answer of the same call
    # without the vector half, over the document this line really occurs in and
    # that carries a chunk as well, so both paths could have answered.
    asked = [GERMAN_FILE]
    query = _query(index, TERM)

    before = snippets_for(index, store, OWNER, query, asked)
    after = snippets_for(index, store, OWNER, query, asked, semantic=_side(stocked, TERM))

    assert after == before
    assert before[0].highlights != []


def test_without_the_vector_half_the_answer_is_what_it_was_before_this_plan(
    index: Index,
    store: Store,
) -> None:
    # The state of an installation without semantics, and the failure path in
    # one: no store, no model, no keyword argument.
    asked = [GERMAN_FILE, FRENCH_FILE, LONG_FILE]
    query = _query(index, PARAPHRASE)

    plain = snippets_for(index, store, OWNER, query, asked)
    passed_nothing = snippets_for(index, store, OWNER, query, asked, semantic=None)

    assert passed_nothing == plain
    assert [snippet.text for snippet in plain] == ["", "", ""]


def test_a_model_that_raises_costs_the_semantics_and_never_the_answer(
    index: Index,
    store: Store,
    stocked: VectorStore,
    caplog: pytest.LogCaptureFixture,
) -> None:
    side = SemanticSide(vectors=stocked, model=BrokenEmbedder(), text=PARAPHRASE)

    with caplog.at_level(logging.DEBUG, logger="findling.index.search"):
        found = _one(snippets_for(index, store, OWNER, _query(index, PARAPHRASE), [GERMAN_FILE], semantic=side))

    assert found.text == ""
    assert found.highlights == []
    assert any("RuntimeError" in record.getMessage() for record in caplog.records)


def test_no_log_line_of_the_cut_carries_the_query(
    index: Index,
    store: Store,
    stocked: VectorStore,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The raw search line is user content (T-06-39). The stand-in puts it into
    # the exception message, so a caught exception that is logged with its
    # message would drag it into the log; only the type name may travel.
    side = SemanticSide(vectors=stocked, model=BrokenEmbedder(), text=PARAPHRASE)

    with caplog.at_level(logging.DEBUG):
        snippets_for(index, store, OWNER, _query(index, PARAPHRASE), [GERMAN_FILE], semantic=side)

    assert caplog.records
    for record in caplog.records:
        assert PARAPHRASE not in record.getMessage()
        assert PARAPHRASE not in str(record.args or "")


def test_the_prefilter_decides_before_a_chunk_is_asked_for_or_a_text_is_read(
    index: Index,
    store: Store,
    stocked: VectorStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # T-06-37 and T-06-38, and the reason this is a stand-in case rather than a
    # result case: an excerpt path that asked the vector store first and dropped
    # the refused documents afterwards would produce exactly the same answer and
    # would still have read the text of a document this user may not see.
    asked_about: list[list[int]] = []
    read_for: list[int] = []
    real_chunks = stocked.best_chunk_for
    real_document = index_search._document_for

    def recording_chunks(file_ids: list[int], vector: bytes) -> dict[int, BestChunk]:
        asked_about.append(list(file_ids))
        return real_chunks(file_ids, vector)

    def recording_document(index: Index, file_id: int) -> Document | None:
        read_for.append(file_id)
        return real_document(index, file_id)

    monkeypatch.setattr(stocked, "best_chunk_for", recording_chunks)
    monkeypatch.setattr(index_search, "_document_for", recording_document)

    found = snippets_for(
        index,
        store,
        OWNER,
        _query(index, PARAPHRASE),
        [GERMAN_FILE, FOREIGN_FILE],
        semantic=_side(stocked, PARAPHRASE),
    )

    assert [snippet.file_id for snippet in found] == [GERMAN_FILE]
    assert asked_about == [[GERMAN_FILE]]
    assert read_for == [GERMAN_FILE]
    assert all(FOREIGN_BODY not in snippet.text for snippet in found)


def test_a_user_the_prefilter_refuses_entirely_gets_no_chunk_question_at_all(
    index: Index,
    store: Store,
    stocked: VectorStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asked_about: list[list[int]] = []
    real_chunks = stocked.best_chunk_for

    def recording_chunks(file_ids: list[int], vector: bytes) -> dict[int, BestChunk]:
        asked_about.append(list(file_ids))
        return real_chunks(file_ids, vector)

    monkeypatch.setattr(stocked, "best_chunk_for", recording_chunks)

    found = snippets_for(
        index,
        store,
        STRANGER,
        _query(index, PARAPHRASE),
        [GERMAN_FILE, FRENCH_FILE],
        semantic=_side(stocked, PARAPHRASE),
    )

    assert found == []
    assert asked_about == []
