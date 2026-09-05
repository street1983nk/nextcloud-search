"""Two ranked lists become one, and three of the assertions are about arithmetic.

Two of the properties below are the ones that go wrong quietly, which is the
reason this file exists at all.

**The rank starts at 1.** Counting from zero is the natural thing to write and
it moves every weight by a whole rank: the first document of a list gets
``1/k`` instead of ``1/(k+1)``, and the answers stay plausible while the merge
no longer does what the formula says. So one case below computes the expected
score by hand rather than against the implementation, and it goes red on a
zero based count without anybody having to notice a reordering.

**An empty vector list is the identity.** That is criterion 3 of the phase
expressed as arithmetic: when the model is gone the semantic list is empty, and
the merge has to hand the lexical ranking back element for element rather than
answer nothing.

The third one is determinism. Equal scores are not exotic here, they are what
two lists of the same length produce all the time, and a merge whose order
depends on dictionary iteration would give two runs of the same query two
different pages.

Twelve numbers and no index: that is the whole point of the module under test
living next to the search rather than inside it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from findling.index.fusion import (
    BOTH,
    LEXICAL,
    SEMANTIC,
    ChunkHit,
    documents_from_chunks,
    origins,
    reciprocal_rank_fusion,
)

MODULE = Path(__file__).resolve().parents[1] / "src" / "findling" / "index" / "fusion.py"

# Built from their code points rather than written as themselves, so that this
# file does not carry the two characters it exists to keep out. Same device as
# in test_vector_store.py, and for the same reason.
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)

# The documented default of the formula. Spelled out here rather than imported
# from the settings, because a test that reads the value under test out of the
# code under test asserts nothing.
K = 60


def fuse(
    lexical: list[int],
    semantic: list[int],
    *,
    lexical_weight: float = 1.0,
    semantic_weight: float = 1.0,
) -> list[tuple[int, float]]:
    """The call with the measured parameters, so the cases stay readable."""
    return reciprocal_rank_fusion(
        lexical,
        semantic,
        k=K,
        lexical_weight=lexical_weight,
        semantic_weight=semantic_weight,
    )


def ids(fused: list[tuple[int, float]]) -> list[int]:
    return [file_id for file_id, _ in fused]


# ---------------------------------------------------------------------------
# Chunks to documents (D-11)
# ---------------------------------------------------------------------------


def test_every_document_appears_exactly_once() -> None:
    hits = [
        ChunkHit(file_id=7, chunk_id=100, distance=0.10),
        ChunkHit(file_id=7, chunk_id=101, distance=0.20),
        ChunkHit(file_id=9, chunk_id=200, distance=0.30),
        ChunkHit(file_id=7, chunk_id=102, distance=0.40),
    ]

    documents = documents_from_chunks(hits)

    assert [document.file_id for document in documents] == [7, 9]


def test_the_best_chunk_decides_the_rank_of_its_document() -> None:
    # The document whose best chunk is closest comes first, even though the
    # other one has more chunks in the list. That is the whole difference
    # between maximum aggregation and counting.
    hits = [
        ChunkHit(file_id=7, chunk_id=100, distance=0.40),
        ChunkHit(file_id=9, chunk_id=200, distance=0.10),
        ChunkHit(file_id=7, chunk_id=101, distance=0.50),
        ChunkHit(file_id=7, chunk_id=102, distance=0.60),
    ]

    documents = documents_from_chunks(hits)

    assert [document.file_id for document in documents] == [9, 7]


def test_the_document_carries_the_chunk_that_earned_its_rank() -> None:
    # The reason this field exists: the chunk that decided the rank is the one
    # whose excerpt the user is going to be shown (D-13).
    hits = [
        ChunkHit(file_id=7, chunk_id=100, distance=0.40),
        ChunkHit(file_id=7, chunk_id=101, distance=0.05),
        ChunkHit(file_id=7, chunk_id=102, distance=0.60),
    ]

    documents = documents_from_chunks(hits)

    assert [(document.chunk_id, document.distance) for document in documents] == [(101, 0.05)]


def test_two_chunks_of_the_same_document_at_the_same_distance_pick_one() -> None:
    # Equal distances are not exotic in a quantised stock. The lower chunk id
    # wins, so a rebuilt stock answers the same excerpt as the one before it.
    hits = [
        ChunkHit(file_id=7, chunk_id=205, distance=0.25),
        ChunkHit(file_id=7, chunk_id=104, distance=0.25),
    ]

    documents = documents_from_chunks(hits)

    assert [document.chunk_id for document in documents] == [104]


def test_no_chunks_is_no_documents() -> None:
    assert documents_from_chunks([]) == []


# ---------------------------------------------------------------------------
# The formula (D-12)
# ---------------------------------------------------------------------------


def test_the_rank_of_the_first_element_is_one() -> None:
    # The case that is computed by hand, and the one that goes red on a rank
    # counted from zero. Document 30 sits at lexical rank 3 and semantic rank
    # 1, so its score is 1/(60+3) + 1/(60+1). Counted from zero it would be
    # 1/(60+2) + 1/(60+0), which is a different number and still a plausible
    # looking order.
    fused = fuse([10, 20, 30], [30, 40])

    scores = dict(fused)

    assert scores[30] == pytest.approx(1 / 63 + 1 / 61)
    assert scores[10] == pytest.approx(1 / 61)
    assert scores[20] == pytest.approx(1 / 62)
    assert scores[40] == pytest.approx(1 / 62)


def test_a_document_in_both_lists_gets_the_sum_of_both_contributions() -> None:
    fused = fuse([10, 20], [20, 10])

    scores = dict(fused)

    assert scores[10] == pytest.approx(1 / 61 + 1 / 62)
    assert scores[20] == pytest.approx(1 / 62 + 1 / 61)


def test_the_merged_list_is_ordered_by_descending_score() -> None:
    fused = fuse([10, 20, 30], [30, 40])

    assert ids(fused) == [30, 10, 20, 40]
    assert [score for _, score in fused] == sorted((score for _, score in fused), reverse=True)


def test_an_empty_semantic_list_is_the_identity_on_the_lexical_order() -> None:
    # Criterion 3 as arithmetic: the model is gone, the vector list is empty,
    # and the lexical ranking comes back element for element.
    lexical = [4, 8, 15, 16, 23, 42]

    fused = fuse(lexical, [])

    assert ids(fused) == lexical


def test_an_empty_lexical_list_is_the_identity_on_the_semantic_order() -> None:
    semantic = [4, 8, 15, 16, 23, 42]

    fused = fuse([], semantic)

    assert ids(fused) == semantic


def test_two_empty_lists_are_an_empty_answer() -> None:
    assert fuse([], []) == []


def test_a_semantic_weight_of_zero_removes_the_semantic_list() -> None:
    # Damping down to nothing has to produce exactly the lexical result set,
    # otherwise a document that is only in the vector list would ride along
    # with a score of zero and the setting would not be a setting but a
    # reordering.
    lexical = [10, 20]

    fused = fuse(lexical, [30, 10], semantic_weight=0.0)

    assert ids(fused) == lexical
    assert dict(fused)[10] == pytest.approx(1 / 61)


def test_a_lowered_semantic_weight_still_ranks_but_ranks_less() -> None:
    full = dict(fuse([10], [20]))
    damped = dict(fuse([10], [20], semantic_weight=0.5))

    assert damped[20] == pytest.approx(full[20] / 2)
    assert damped[10] == pytest.approx(full[10])


def test_equal_scores_produce_the_same_order_in_two_runs() -> None:
    # Two lists of the same length give every pair of ranks the same score, so
    # this is the ordinary case and not the exotic one. The documented rule is
    # the lower file id first.
    first = fuse([90, 80, 70], [93, 83, 73])
    second = fuse([90, 80, 70], [93, 83, 73])

    assert ids(first) == ids(second)
    assert ids(first) == [90, 93, 80, 83, 70, 73]


def test_a_document_named_twice_in_one_list_counts_once_at_its_best_rank() -> None:
    # A defensive property rather than a likely input: the caller hands over
    # ranked ids, and a duplicate would otherwise pay twice for one list.
    fused = fuse([10, 20, 10], [])

    assert ids(fused) == [10, 20]
    assert dict(fused)[10] == pytest.approx(1 / 61)


# ---------------------------------------------------------------------------
# The origin marks (D-14)
# ---------------------------------------------------------------------------


def test_the_origin_of_every_document_is_one_of_three_marks() -> None:
    marks = origins([10, 20], [20, 30])

    assert marks == {10: LEXICAL, 20: BOTH, 30: SEMANTIC}


def test_the_origin_marks_stay_out_of_the_search_path() -> None:
    # D-14 as a grep. The merge is called by the candidate search; this
    # function is not, and the diagnosis route is the only caller it may ever
    # have. A mark on the search path would be a statement about a document the
    # recheck has not confirmed yet.
    source = Path(MODULE.parent / "search.py").read_text(encoding="utf-8")

    assert "origins" not in source


# ---------------------------------------------------------------------------
# What the module must not know
# ---------------------------------------------------------------------------


def test_the_module_knows_neither_engine() -> None:
    # The reason the merge lives next to the search instead of inside it: it
    # takes numbers and answers numbers, so the cases above need no index and
    # no database.
    source = MODULE.read_text(encoding="utf-8")

    assert "tantivy" not in source
    assert "sqlite3" not in source


def test_the_module_says_where_the_rank_begins() -> None:
    # The comment is load bearing here, not decoration: it is the only warning
    # a reader gets before writing the most common bug of this formula.
    source = MODULE.read_text(encoding="utf-8")

    assert "rank" in source
    assert "begins at 1" in source


def test_the_prefilter_is_not_called_from_here() -> None:
    # T-06-25. The merge runs above the one prefilter call of the search, and
    # a second call in here would be a second place that decides what a user
    # may see.
    source = MODULE.read_text(encoding="utf-8")

    assert "prefilter_visible" not in source


def test_neither_artefact_carries_a_dash() -> None:
    for path in (MODULE, Path(__file__)):
        source = path.read_text(encoding="utf-8")

        assert EM_DASH not in source, path.name
        assert EN_DASH not in source, path.name
