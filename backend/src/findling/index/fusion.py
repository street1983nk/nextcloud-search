"""Two ranked lists into one, and chunk ranks into document ranks.

A pure module, and it lives next to the search rather than inside it for the
same reason :func:`findling.index.search.char_ranges` does: everything in here
can be exercised with a dozen numbers instead of an index, a vector database
and a model. Nothing in this file knows what an engine hit or a database row
is, and a test asserts that rather than trusting it: it greps for the names of
both engines and expects to find neither.

**The formula**, word for word from the Elasticsearch reference (retrieved
2026-09-04)::

    score = 0.0
    for q in queries:
        if d in result(q):
            score += 1.0 / ( k + rank( result(q), d ) )
    return score

The parameters this project adds to it are the two weights, which Elasticsearch
does not have ("each child retriever carries an equal weight"). They exist so
that an administrator can damp the semantic half down without switching it off
(D-12). Their values, the constant ``k`` and the window depth live in
:mod:`findling.config` with the reasoning that produced them.

**What this module deliberately does not do.** It never asks who may see a
document. The merge runs above the one permission prefilter call of
:func:`findling.index.search.candidates`, which is what makes criterion 2 of the
phase a property of the structure rather than of anybody's discipline: there is
no second exit from the container for a candidate, and no second place that
decides what a user is allowed to see (T-06-25, D-20).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Sequence

# The three origin marks. Named constants rather than literals for the reason
# every allowlist in this project is one: a literal at the second call site can
# be spelled differently, and here the difference would be invisible.
LEXICAL: Final = "lexical"
SEMANTIC: Final = "semantic"
BOTH: Final = "both"


@dataclass(frozen=True, slots=True)
class ChunkHit:
    """One neighbour of the query vector, as three numbers.

    Written as a class of this module rather than as the store's own
    :class:`findling.store.vectors.Neighbour` so that the aggregation below can
    be exercised without a database. The caller converts, which costs one list
    comprehension and keeps this file free of the vector half.
    """

    file_id: int
    chunk_id: int
    distance: float


@dataclass(frozen=True, slots=True)
class DocumentHit:
    """One document, represented by the chunk that earned it its rank."""

    file_id: int
    chunk_id: int
    distance: float


def documents_from_chunks(hits: Sequence[ChunkHit]) -> list[DocumentHit]:
    """Aggregate chunk hits onto documents by their best chunk (D-11).

    Every document appears exactly once, and the order is the order of its best
    chunk. Three aggregations were available and this is the maximum, for two
    reasons that are worth keeping together.

    The first is that it is the only one of the three without a systematic
    length bias. Summing over the best n chunks rewards a document for matching
    repeatedly, counting the chunks inside the top k does the same more
    bluntly, and under the capped chunking of D-01 that reward would mostly
    measure how long a document is. Under that cap a document carries two or
    three chunks (measured 2026-09-05), so sum and count add very little
    information over the maximum anyway.

    The second is that the chunk which decides the rank is the chunk whose
    excerpt the user is later shown (D-13). Any other aggregation would rank a
    document by one thing and quote it from another.

    **The store answers distances, so the best chunk is the smallest number.**
    This inversion is the one place in this function that can be wrong exactly
    once and stay plausible afterwards: a maximum taken over distances puts the
    least similar chunk of every document in front, and the result is still a
    full, ordered, believable list of documents. Ties go to the lower chunk id,
    so that a rebuilt stock answers the same excerpt as the one before it.
    """
    best: dict[int, DocumentHit] = {}
    for hit in hits:
        current = best.get(hit.file_id)
        if current is None or (hit.distance, hit.chunk_id) < (current.distance, current.chunk_id):
            best[hit.file_id] = DocumentHit(file_id=hit.file_id, chunk_id=hit.chunk_id, distance=hit.distance)
    return sorted(best.values(), key=lambda document: (document.distance, document.file_id))


def reciprocal_rank_fusion(
    lexical: Sequence[int],
    semantic: Sequence[int],
    *,
    k: int,
    lexical_weight: float,
    semantic_weight: float,
) -> list[tuple[int, float]]:
    """Merge two ranked lists of file ids into one, descending by score.

    Both arguments are ranked best first, and a document that stands in both
    lists collects both contributions. An empty list contributes nothing, which
    makes the merge the identity on the other one: that is criterion 3 of this
    phase expressed as arithmetic, because a failed vector branch hands an empty
    list in here and the lexical answer has to come back unchanged.

    **The rank begins at 1, not at 0.** It is the most common implementation
    error of this formula and it moves every weight by a whole rank: counted
    from zero the first document of a list scores ``1/k`` where the formula says
    ``1/(k+1)``, the second scores what the first should have, and so on all the
    way down. Nothing fails, the order inside one list even stays the same, and
    only the balance between the two lists moves, which is the one thing this
    function exists to get right.

    **A weight of zero removes its list rather than scoring it with zero.** The
    difference matters at exactly one point: a document that stands only in the
    damped list would otherwise ride along with a score of nothing and change
    the result set, so the setting would not be a damping but a reordering. With
    the semantic weight at zero the answer is the lexical result set, which is
    what an administrator who turns it down to zero is asking for.

    Equal scores are the ordinary case rather than the exotic one, because two
    lists of the same length hand out the same rank twice. The documented
    tie break is the lower file id, so two runs of one query answer one order.
    """
    scores: dict[int, float] = {}
    for ranked, weight in ((lexical, lexical_weight), (semantic, semantic_weight)):
        if weight == 0.0:
            continue
        # start=1 is the whole warning above turned into one keyword. A
        # duplicate inside one list would let one document pay twice for one
        # source, so dict.fromkeys drops it and keeps its first, best rank.
        for rank, file_id in enumerate(dict.fromkeys(ranked), start=1):
            scores[file_id] = scores.get(file_id, 0.0) + weight / (k + rank)
    return sorted(scores.items(), key=lambda entry: (-entry[1], entry[0]))


def origins(lexical: Sequence[int], semantic: Sequence[int]) -> dict[int, str]:
    """Where each document of the two lists came from, for the diagnosis route.

    **This function does not belong on the search path, and that is the whole
    point of it living here.** The candidate the search hands out carries three
    values and no fourth, which is a documented security property: an origin
    mark would be a statement about a document the PHP recheck has not confirmed
    yet, and the field set test of the candidate model goes red the day somebody
    puts one there (D-14, T-06-30).

    The diagnosis route of phase 4 is a different question with a different
    answer. It is an administrator asking about one file they already named, not
    a user being told something about a document they may not be allowed to know
    exists.
    """
    marks: dict[int, str] = {}
    for file_id in lexical:
        marks[file_id] = LEXICAL
    for file_id in semantic:
        marks[file_id] = BOTH if marks.get(file_id) == LEXICAL else SEMANTIC
    return marks
