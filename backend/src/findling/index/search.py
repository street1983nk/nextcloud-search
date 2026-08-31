"""The reading half of the index: candidates now, snippets after the recheck.

Two things about this module are decisions rather than implementation details.

*The loop is not here.* One call is one round: ask the engine once, drop what the
prefilter does not confirm, hand out what is left together with a mark for the
next round. Whether another round is worth it can only be judged where the real
permission check runs, which is the PHP companion, because only it knows how many
candidates survived the recheck. A loop in here would be an unbounded loop in the
one place that cannot see its own stop condition, and that is precisely the
failure that gives query time permission filtering its bad reputation.

*The prefilter is a speed-up, not a boundary.* It over-approximates on team
folders with advanced permissions, and that is the safe direction: a candidate
too many is dropped by the recheck a moment later, while a candidate too few is a
result the user never sees and never learns about.

Measured for the phase: the engine search costs 0.1 ms, the prefilter 0.18 ms for
400 candidates, an overfetch of 400 candidates 4.2 ms. The expensive part of a
search is neither of them, it is the two proxy round trips and the recheck.
"""

import logging
from dataclasses import dataclass
from typing import Final

from tantivy import Index, Query, SearchResult

from findling.index.schema import FIELD_EXT, FIELD_FILE_ID, FIELD_MTIME
from findling.store.repo import Store

LOGGER = logging.getLogger("findling.index.search")

# Selectivity, honestly: in the synthetic case of the phase research only 31 of
# 400 candidates survived the permission check. Real instances look friendlier,
# users mostly see what lies in their own mounts, but the case exists. The answer
# to it is the bounded repeat on the PHP side, never a larger first request: a
# larger request pays the full ranking cost for hits nobody is allowed to see.
_UNKNOWN_EXTENSION: Final = ""


@dataclass(frozen=True, slots=True)
class Candidate:
    """One hit before the permission check, and deliberately nothing more.

    Four values, and the three that are missing are the point. No file name, no
    location, no text: before the recheck has run, nothing may leave this process
    that tells a user anything about a document they might not be allowed to see.

    There is a second reason for the file name in particular. The PHP side
    resolves every surviving id into a node of the user's own folder anyway, and
    that node carries the current name. A name from the index would be the older
    of the two.
    """

    file_id: int
    score: float
    mtime: int
    ext: str


@dataclass(frozen=True, slots=True)
class CandidatePage:
    """One round of candidates plus the mark for the next one.

    There is no total. The number of hits before filtering is a statement about
    documents of other people, and ``has_more`` is everything a caller needs in
    order to decide whether to ask again.
    """

    candidates: list[Candidate]
    has_more: bool
    next_offset: int


def _hits_in_total(result: SearchResult) -> int:
    """How many documents matched, before any filtering. Never leaves this module.

    The type stub shipped with tantivy 0.26.0 declares only ``hits`` on the
    result, while the extension does return this number when the search was asked
    to count. Read once, in one place, and deliberately without a fallback value:
    a default here would turn a renamed attribute into a page that always claims
    to be the last one, and the lost results would never be noticed by anybody.
    """
    return result.count  # pyright: ignore[reportAttributeAccessIssue]


def _stored_int(value: object) -> int:
    """Read a stored number back, and answer 0 when the field is absent.

    The document store hands values back as ``Any``. A missing modification time
    is a display detail, so it degrades to zero rather than ending the search.
    """
    return int(value) if isinstance(value, int | float | str) else 0


def candidates(
    index: Index,
    store: Store,
    uid: str,
    query: Query,
    limit: int,
    offset: int = 0,
) -> CandidatePage:
    """Return one round of permitted candidates in the order the engine ranked them.

    One call, one pass over the engine. ``offset`` is where the caller wants the
    round to start, ``next_offset`` is where the following one has to start so
    that no hit is seen twice and none is skipped.
    """
    searcher = index.searcher()
    # The only place a total is asked for, and it stays inside this function: it
    # decides whether asking again could produce anything, and nothing else.
    result = searcher.search(query, limit, count=True, offset=offset)

    ranked: list[tuple[int, float, int, str]] = []
    for score, address in result.hits:
        document = searcher.doc(address)
        file_id = document.get_first(FIELD_FILE_ID)
        if file_id is None:
            # A hit without the key cannot be rechecked and cannot be resolved
            # into a node, so it is not a result. Skipped rather than raised: one
            # damaged document must not take the whole search down with it.
            LOGGER.warning("skipping a hit without a file id")
            continue
        extension = document.get_first(FIELD_EXT)
        ranked.append(
            (
                int(file_id),
                float(score),
                _stored_int(document.get_first(FIELD_MTIME)),
                extension if isinstance(extension, str) else _UNKNOWN_EXTENSION,
            )
        )

    # From the candidates to the permissions, never the other way round. Building
    # the list of everything a user may see is the inverse question, and its cost
    # grows with the instance instead of with the query.
    visible = store.prefilter_visible(uid, [file_id for file_id, _, _, _ in ranked])

    permitted = [
        Candidate(file_id=file_id, score=score, mtime=mtime, ext=extension)
        for file_id, score, mtime, extension in ranked
        if file_id in visible
    ]
    seen = offset + len(result.hits)
    return CandidatePage(candidates=permitted, has_more=seen < _hits_in_total(result), next_offset=seen)
