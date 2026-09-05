"""The through cut: a paraphrase finds the document, through the same chain.

This file makes the three success criteria of phase 6 into three tests, and two
of them are about what must NOT happen.

**Criterion 1.** A query whose content words do not occur in the document finds
it anyway, because the vector branch contributes it and the merge puts both
lists together. The counter case stands right next to it: the same query with
the vector branch switched off finds nothing. Without that second case the
first one would stay green on a search that simply matched lexically after all.

**Criterion 2.** That candidate goes through exactly the same permission chain
as every lexical one. carol has no permission row at all and gets nothing, and
alice gets nothing for a document that is not hers, however close its vector
sits to the query. The merge runs above the one prefilter call, which is what
makes this a property of the structure rather than of anybody's discipline.

**Criterion 3.** When the model is gone, the extension refuses to load or the
vector query raises, the vector list is empty, the merge becomes the identity
on the lexical ranking, and the search answers full text hits rather than
nothing. The failure is visible as a log line with a type name and as the
degraded flag, and never as an empty answer.

Two further properties of the module survive the rebuild and are asserted here
because a rebuilt loop is exactly where they would be lost: the offset counts
permitted candidates and never raw hits (the counting oracle of T-02-93), and
the page still carries no total.

**The vector store here is the real one.** That is the conftest rule of this
repository: a stand-in would answer every question except whether the pieces
are wired together. The model is the one stand-in, for the reason test_ocr.py
splits on as well: the artifact does not exist on a development machine, and a
384 byte vector is raw bytes to the store either way.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from tantivy import Document, Index, Query

from conftest import Corpus
from findling.config import settings
from findling.embed.model import DIMENSIONS, EmbedOutcome, to_int8
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
from findling.index.search import Candidate, CandidatePage, SemanticSide, candidates
from findling.query.rewrite import build_query
from findling.store.repo import Store, open_store
from findling.store.vectors import Chunk, VectorStore, open_vectors

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()

DOCUMENTS = 12

# alice sees the odd file ids, bob sees everything, carol has no row at all.
ALICE = "alice"
BOB = "bob"
CAROL = "carol"

# The document the vector branch is going to contribute, and it is an odd id, so
# alice may see it. The second one is even, which is how the permission half of
# criterion 2 gets a case that is not just "the user has no rows".
SEMANTIC_FILE = 5
HIDDEN_FILE = 6

# Two lines that do not occur in any document of this corpus. The lexical half
# answers nothing to either of them, which is asserted rather than assumed, so
# whatever comes back can only have come from the vector half.
PARAPHRASE = "Weltraumbahnhof"
OTHER_PARAPHRASE = "Raumfahrtzentrum"

# A line that matches every document, for the cases that are about the loop
# rather than about the semantics.
TERM = "Kündigungsfrist"

Sign = Callable[[str], dict[str, str]]


def _body(file_id: int) -> str:
    """Bodies of different length, so that the ranking is not a coin toss."""
    tail = "Weitere Absätze folgen. " * (file_id % 4)
    return f"Die Kündigungsfrist im Vertrag Nummer {file_id}. {tail}"


def unit_vector(axis: int) -> tuple[float, ...]:
    """One normalised vector that points along a single axis.

    Normalised because that is what the model answers and what ``to_int8``
    assumes, and along one axis because it makes the distances in the cases
    below readable: two vectors on the same axis are identical, two on
    different axes are as far apart as this construction gets.
    """
    return tuple(1.0 if index == axis else 0.0 for index in range(DIMENSIONS))


class Embedder:
    """The one stand-in in this file: a model that answers from a table.

    Anything it has no answer for becomes the ``embedding_unavailable``
    verdict, which is exactly what the real wrapper does when the artifact is
    missing, so the "no model" case needs no second class.
    """

    def __init__(self, answers: dict[str, tuple[float, ...]]) -> None:
        self._answers = answers

    def embed_query(self, text: str) -> EmbedOutcome:
        vector = self._answers.get(text)
        if vector is None:
            return EmbedOutcome.unavailable()
        return EmbedOutcome.ready([vector])


class BrokenEmbedder:
    """A model whose engine raises, with user content inside the message.

    The content is in the message on purpose: the log assertion below is only
    worth something if there is something to leak.
    """

    def embed_query(self, text: str) -> EmbedOutcome:
        raise RuntimeError(f"the engine choked while reading {text}")


@pytest.fixture(autouse=True)
def _cold_settings() -> Iterator[None]:
    """A cold settings cache on both sides, because these cases turn knobs."""
    settings.cache_clear()
    yield
    settings.cache_clear()


@pytest.fixture(scope="module")
def index(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Index]:
    directory = tmp_path_factory.mktemp("semantic-index")
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
        opened.replace_acl(file_id, [BOB] if file_id % 2 == 0 else [ALICE, BOB])
    yield opened
    opened.close()


@pytest.fixture
def vectors(tmp_path: Path) -> Iterator[VectorStore]:
    """The real vector store, with one chunk for each of the two documents."""
    opened = open_vectors(tmp_path / "vectors.db")
    for file_id, axis in ((SEMANTIC_FILE, 1), (HIDDEN_FILE, 2)):
        opened.replace_chunks(
            file_id,
            [Chunk(ordinal=0, char_start=0, char_end=40, embedding=to_int8(unit_vector(axis)))],
        )
    yield opened
    opened.close()


def _query(index: Index, text: str = TERM) -> Query:
    rewritten = build_query(index, text)
    assert rewritten.query is not None
    return rewritten.query


def _side(vectors: VectorStore, text: str, *, answers: dict[str, tuple[float, ...]] | None = None) -> SemanticSide:
    table = answers if answers is not None else {PARAPHRASE: unit_vector(1), OTHER_PARAPHRASE: unit_vector(2)}
    return SemanticSide(vectors=vectors, model=Embedder(table), text=text)


def _ids(page: CandidatePage) -> list[int]:
    return [candidate.file_id for candidate in page.candidates]


# ---------------------------------------------------------------------------
# Criterion 1: the paraphrase
# ---------------------------------------------------------------------------


def test_the_lexical_half_answers_nothing_to_the_paraphrase(index: Index, store: Store) -> None:
    # The floor under the next case. Without it a green criterion 1 could just
    # mean that the line matched lexically after all.
    page = candidates(index, store, BOB, _query(index, PARAPHRASE), limit=DOCUMENTS)

    assert page.candidates == []


def test_a_paraphrase_finds_the_document_its_words_do_not_occur_in(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    page = candidates(
        index,
        store,
        BOB,
        _query(index, PARAPHRASE),
        limit=DOCUMENTS,
        semantic=_side(vectors, PARAPHRASE),
    )

    # The lexical half answered nothing to this line, so everything here came
    # out of the vector half. Both documents that carry a vector come back,
    # because a brute force neighbour search ranks the whole stock and has no
    # notion of "close enough"; the one the query points at leads.
    assert _ids(page) == [SEMANTIC_FILE, HIDDEN_FILE]


def test_the_closer_vector_is_the_one_that_leads(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    # Both documents carry a vector, so this asserts that the query decides the
    # order rather than the order the chunks were written in.
    page = candidates(
        index,
        store,
        BOB,
        _query(index, OTHER_PARAPHRASE),
        limit=DOCUMENTS,
        semantic=_side(vectors, OTHER_PARAPHRASE),
    )

    assert _ids(page) == [HIDDEN_FILE, SEMANTIC_FILE]


# ---------------------------------------------------------------------------
# Criterion 2: the same permission chain
# ---------------------------------------------------------------------------


def test_a_user_without_a_permission_row_gets_no_semantic_hit_either(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    page = candidates(
        index,
        store,
        CAROL,
        _query(index, PARAPHRASE),
        limit=DOCUMENTS,
        semantic=_side(vectors, PARAPHRASE),
    )

    assert page.candidates == []
    assert page.has_more is False


def test_a_semantic_hit_of_a_document_the_user_may_not_see_is_dropped(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    # alice has rows, so this is not the empty user case. The nearest vector to
    # this query belongs to a document she may not see, and no closeness makes
    # up for that: bob gets it in front, she does not get it at all.
    for_bob = candidates(
        index, store, BOB, _query(index, OTHER_PARAPHRASE), limit=DOCUMENTS, semantic=_side(vectors, OTHER_PARAPHRASE)
    )
    page = candidates(
        index,
        store,
        ALICE,
        _query(index, OTHER_PARAPHRASE),
        limit=DOCUMENTS,
        semantic=_side(vectors, OTHER_PARAPHRASE),
    )

    assert _ids(for_bob)[0] == HIDDEN_FILE
    assert _ids(page) == [SEMANTIC_FILE]


def test_a_candidate_from_the_vector_branch_carries_the_same_three_values(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    # D-14. A hit that came out of the vector half is a Candidate like every
    # other one, and it says nothing about where it came from.
    page = candidates(
        index,
        store,
        BOB,
        _query(index, PARAPHRASE),
        limit=DOCUMENTS,
        semantic=_side(vectors, PARAPHRASE),
    )

    hit = page.candidates[0]
    assert isinstance(hit, Candidate)
    assert hit.file_id == SEMANTIC_FILE
    assert hit.mtime == 1_700_000_000 + SEMANTIC_FILE
    assert hit.score > 0.0


# ---------------------------------------------------------------------------
# Criterion 3: the failure costs the semantics and not the search
# ---------------------------------------------------------------------------


def test_a_failing_vector_branch_leaves_the_lexical_answer_untouched(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    expected = _ids(candidates(index, store, BOB, _query(index), limit=DOCUMENTS))

    broken = SemanticSide(vectors=vectors, model=BrokenEmbedder(), text=TERM)
    page = candidates(index, store, BOB, _query(index), limit=DOCUMENTS, semantic=broken)

    assert expected != []
    assert _ids(page) == expected


def test_the_failure_of_the_vector_branch_names_neither_query_nor_message(
    index: Index,
    store: Store,
    vectors: VectorStore,
    caplog: pytest.LogCaptureFixture,
) -> None:
    broken = SemanticSide(vectors=vectors, model=BrokenEmbedder(), text=TERM)

    with caplog.at_level(logging.WARNING, logger="findling.index.search"):
        candidates(index, store, BOB, _query(index), limit=DOCUMENTS, semantic=broken)

    assert "RuntimeError" in caplog.text
    assert TERM not in caplog.text
    assert "choked" not in caplog.text


def test_a_model_that_is_not_there_is_not_a_failure(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    # The wrapper answers embedding_unavailable rather than raising, and that
    # path has to end in the same place the exception does: an empty vector
    # list and an unchanged lexical answer.
    expected = _ids(candidates(index, store, BOB, _query(index), limit=DOCUMENTS))

    absent = SemanticSide(vectors=vectors, model=Embedder({}), text=TERM)
    page = candidates(index, store, BOB, _query(index), limit=DOCUMENTS, semantic=absent)

    assert _ids(page) == expected


def test_a_paraphrase_without_a_model_finds_nothing_and_does_not_raise(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    absent = SemanticSide(vectors=vectors, model=Embedder({}), text=PARAPHRASE)

    page = candidates(index, store, BOB, _query(index, PARAPHRASE), limit=DOCUMENTS, semantic=absent)

    assert page.candidates == []
    assert page.has_more is False


# ---------------------------------------------------------------------------
# The properties that had to survive the rebuild
# ---------------------------------------------------------------------------


def test_two_pages_of_five_are_the_page_of_ten(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    # The counting oracle of T-02-93 with the vector branch switched on. An
    # offset counted in raw engine hits would leave a gap here, and a merge
    # that reordered between two calls would produce a repetition.
    whole = candidates(index, store, BOB, _query(index), limit=10, semantic=_side(vectors, PARAPHRASE)).candidates

    first = candidates(index, store, BOB, _query(index), limit=5, semantic=_side(vectors, PARAPHRASE))
    second = candidates(
        index, store, BOB, _query(index), limit=5, offset=first.next_offset, semantic=_side(vectors, PARAPHRASE)
    )

    assert len(whole) == 10
    assert first.candidates + second.candidates == whole


def test_the_page_still_carries_no_total(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    page = candidates(index, store, ALICE, _query(index), limit=2, semantic=_side(vectors, PARAPHRASE))

    names = {field.name for field in dataclasses.fields(page)}

    assert names == {"candidates", "has_more", "next_offset"}
    assert page.has_more is True


def test_the_vector_branch_does_not_lose_a_permitted_lexical_hit(
    index: Index,
    store: Store,
    vectors: VectorStore,
) -> None:
    # Every document alice may see is still in the answer; the vector branch
    # only moves one of them forward.
    page = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS, semantic=_side(vectors, PARAPHRASE))

    assert sorted(_ids(page)) == [file_id for file_id in range(1, DOCUMENTS + 1) if file_id % 2 == 1]
    assert _ids(page)[0] == SEMANTIC_FILE


def test_a_semantic_weight_of_zero_answers_like_a_container_without_vectors(
    index: Index,
    store: Store,
    vectors: VectorStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    without = _ids(candidates(index, store, BOB, _query(index), limit=DOCUMENTS))

    monkeypatch.setenv("FINDLING_SEARCH_SEMANTIC_WEIGHT", "0")
    settings.cache_clear()

    damped = candidates(index, store, BOB, _query(index), limit=DOCUMENTS, semantic=_side(vectors, PARAPHRASE))
    paraphrase = candidates(
        index, store, BOB, _query(index, PARAPHRASE), limit=DOCUMENTS, semantic=_side(vectors, PARAPHRASE)
    )

    assert _ids(damped) == without
    assert paraphrase.candidates == []


def test_a_reached_vector_ceiling_is_reported_without_the_query(
    index: Index,
    store: Store,
    vectors: VectorStore,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("FINDLING_VECTOR_SCAN_MAX", "1")
    settings.cache_clear()

    with caplog.at_level(logging.INFO, logger="findling.index.search"):
        page = candidates(
            index,
            store,
            BOB,
            _query(index, PARAPHRASE),
            limit=DOCUMENTS,
            semantic=_side(vectors, PARAPHRASE),
        )

    # An honest answer, and a line that carries neither the query nor a count.
    assert _ids(page) == [SEMANTIC_FILE]
    reported = [message for message in caplog.messages if "the vector scan hit its own ceiling" in message]
    assert reported, caplog.text
    assert PARAPHRASE not in reported[0]
    assert not any(character.isdigit() for character in reported[0])


# ---------------------------------------------------------------------------
# The same criteria at the route the user really takes
# ---------------------------------------------------------------------------


def _post(client: TestClient, headers: dict[str, str], text: str) -> dict[str, Any]:
    response = client.post("/search", json={"query": text, "limit": 20}, headers=headers)

    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.usefixtures("appapi_environment")
def test_a_container_without_a_vector_stock_answers_full_text_and_says_degraded(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    (indexed_volume.root / "vectors.db").unlink()
    settings.cache_clear()

    answer = _post(client, sign(indexed_volume.bob), TERM)

    assert answer["candidates"], "the corpus matches this term, so this must not be empty"
    assert answer["degraded"] is True


@pytest.mark.usefixtures("appapi_environment")
def test_a_missing_model_leaves_the_full_text_answer_unchanged(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The acceptance test of D-19, pointed at an empty model directory rather
    # than at a renamed file, which is the same state and needs no artifact.
    monkeypatch.setenv("FINDLING_EMBED_MODEL_DIR", str(tmp_path / "no-model"))
    settings.cache_clear()

    with_vectors = _post(client, sign(indexed_volume.bob), TERM)

    monkeypatch.setenv("FINDLING_EMBED_ENABLED", "false")
    settings.cache_clear()
    without_embedding = _post(client, sign(indexed_volume.bob), TERM)

    ids = [hit["fileId"] for hit in with_vectors["candidates"]]
    assert ids != []
    assert ids == [hit["fileId"] for hit in without_embedding["candidates"]]
