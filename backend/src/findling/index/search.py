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
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from tantivy import Document, Index, Query, SearchResult, SnippetGenerator

from findling.config import settings
from findling.index.schema import FIELD_BODY_DE, FIELD_FILE_ID, FIELD_MTIME
from findling.store.repo import Store

LOGGER = logging.getLogger("findling.index.search")

# Selectivity, honestly: in the synthetic case of the phase research only 31 of
# 400 candidates survived the permission check. Real instances look friendlier,
# users mostly see what lies in their own mounts, but the case exists. The answer
# to it is the bounded repeat on the PHP side, never a larger first request: a
# larger request pays the full ranking cost for hits nobody is allowed to see.


@dataclass(frozen=True, slots=True)
class Candidate:
    """One hit before the permission check, and deliberately nothing more.

    Three values, and everything that is missing is the point. No file name, no
    location, no text, not even the extension: before the recheck has run,
    nothing may leave this process that tells a user anything about a document
    they might not be allowed to see.

    There is a second reason for the file name in particular. The PHP side
    resolves every surviving id into a node of the user's own folder anyway, and
    that node carries the current name, location and extension. A value from the
    index would be the older of the two, which is why ``ext`` lives only inside
    the index for the ``type:`` filter and never rides along here.
    """

    file_id: int
    score: float
    mtime: int


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

    # The columns, never the document store. searcher.doc() hands back the whole
    # stored document including the full text, and that read was 99.9% of the
    # candidate round: measured 20.5 ms per hit at the 512k cap against 0.02 ms
    # for the two fast-field columns, independent of document size.
    addresses = [address for _, address in result.hits]
    file_ids = searcher.fast_field_values(FIELD_FILE_ID, addresses)
    mtimes = searcher.fast_field_values(FIELD_MTIME, addresses)

    ranked: list[tuple[int, float, int]] = []
    for (score, _), file_id, mtime in zip(result.hits, file_ids, mtimes, strict=True):
        if file_id is None:
            # A hit without the key cannot be rechecked and cannot be resolved
            # into a node, so it is not a result. Skipped rather than raised: one
            # damaged document must not take the whole search down with it.
            LOGGER.warning("skipping a hit without a file id")
            continue
        # A missing modification time is a display detail, so it degrades to
        # zero rather than ending the search.
        ranked.append((int(file_id), float(score), int(mtime) if mtime is not None else 0))

    # From the candidates to the permissions, never the other way round. Building
    # the list of everything a user may see is the inverse question, and its cost
    # grows with the instance instead of with the query.
    visible = store.prefilter_visible(uid, [file_id for file_id, _, _ in ranked])

    permitted = [
        Candidate(file_id=file_id, score=score, mtime=mtime)
        for file_id, score, mtime in ranked
        if file_id in visible
    ]
    seen = offset + len(result.hits)
    return CandidatePage(candidates=permitted, has_more=seen < _hits_in_total(result), next_offset=seen)


class ByteRange(Protocol):
    """The two numbers a highlighted range consists of.

    Written as a protocol rather than as the engine's own type so that the pure
    conversion below can be exercised with a handful of numbers instead of a
    whole index. The offsets it describes are byte positions.
    """

    @property
    def start(self) -> int: ...

    @property
    def end(self) -> int: ...


@dataclass(frozen=True, slots=True)
class SnippetText:
    """One text excerpt, with highlight positions counted in characters."""

    file_id: int
    text: str
    highlights: list[tuple[int, int]] = field(default_factory=list)


def char_ranges(fragment: str, ranges: Sequence[ByteRange]) -> list[tuple[int, int]]:
    """Convert byte ranges of a fragment into character ranges, merged and sorted.

    Two separate corrections happen here, and both are measured rather than
    assumed.

    The engine counts UTF-8 bytes while the wire protocol of this project
    promises characters. Measured on a German sentence: the engine reports
    (35, 51) where the character range is (35, 50), so a naive slice takes one
    character too many and every umlaut in front of the match shifts the
    highlight further. The text stays correct, only the marking moves, which is
    why this bug survives review and testing so reliably.

    The ranges also repeat and overlap, because every part of a split compound
    inherits the offsets of the whole word. Sorting and merging them is what
    turns three identical marks around one word into one.

    A pure function, and it lives next to the search rather than in the endpoint
    so that it can be tested with a fragment and two numbers.
    """
    data = fragment.encode("utf-8")
    spans = sorted(
        (len(data[: reported.start].decode("utf-8")), len(data[: reported.end].decode("utf-8"))) for reported in ranges
    )
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _document_for(index: Index, file_id: int) -> Document | None:
    """Fetch one stored document by its key, or None when the index has no such row."""
    searcher = index.searcher()
    result = searcher.search(Query.term_query(index.schema, FIELD_FILE_ID, file_id), 1)
    if not result.hits:
        return None
    return searcher.doc(result.hits[0][1])


def snippets_for(
    index: Index,
    store: Store,
    uid: str,
    query: Query,
    file_ids: Sequence[int],
) -> list[SnippetText]:
    """Cut one text excerpt per confirmed file id, in the order they were asked for.

    The prefilter runs as the first action of this function, before a single byte
    of text is read. Without it this path would be a confused deputy: a snippet is
    file content, and whoever reaches the proxy could otherwise ask for the
    content of any document by its id. That the caller already dropped everything
    the recheck refused is not an argument, it is an assumption about a different
    process running correctly, and the cost of not making that assumption was
    measured at 0.2 ms.

    A document the index does not know is skipped. A document the query does not
    match inside the text field yields an empty excerpt rather than an error: a
    hit without a snippet is still a hit, and the subline falls back to the path
    on the PHP side.
    """
    visible = store.prefilter_visible(uid, file_ids)
    if not visible:
        return []

    generator = SnippetGenerator.create(index.searcher(), query, index.schema, FIELD_BODY_DE)
    # Despite its name this is a byte comparison inside the fragmenter, so a
    # German sentence fits into slightly less than the number suggests. The value
    # is the one cap of this module and lives in findling.config with the rest.
    generator.set_max_num_chars(settings().snippet_chars)

    excerpts: list[SnippetText] = []
    for file_id in file_ids:
        if file_id not in visible:
            continue
        document = _document_for(index, file_id)
        if document is None:
            continue
        snippet = generator.snippet_from_doc(document)
        fragment = snippet.fragment()
        excerpts.append(
            SnippetText(file_id=file_id, text=fragment, highlights=char_ranges(fragment, snippet.highlighted()))
        )
    return excerpts
