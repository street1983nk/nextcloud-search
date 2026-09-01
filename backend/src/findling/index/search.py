"""The reading half of the index: candidates now, snippets after the recheck.

Two things about this module are decisions rather than implementation details.

*The recheck loop is not here.* One call is one page of prefiltered candidates.
Whether another page is worth asking for can only be judged where the real
permission check runs, which is the PHP companion, because only it knows how many
candidates survived the recheck. A loop over rechecks in here would be an
unbounded loop in the one place that cannot see its own stop condition, and that
is precisely the failure that gives query time permission filtering its bad
reputation. The bounded scan loop inside :func:`candidates` is a different
animal: its stop condition, "enough prefiltered candidates for this page", is
fully visible right here.

*Offsets count permitted candidates, not engine hits.* An offset in engine-hit
space tells whoever varies it how many documents of other people match a term:
the gap between two raw cursors minus the candidates delivered in between is a
count of foreign documents, page by page (the counting oracle of T-02-93). So the
cursor that crosses the process boundary counts only what the caller was allowed
to see, and the raw cursor stays inside this function.

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
from typing import Final, Protocol

from tantivy import Document, Index, Query, SnippetGenerator

from findling.config import SEARCH_SCAN_MAX, settings
from findling.index.schema import FIELD_BODY_DE, FIELD_FILE_ID, FIELD_MTIME
from findling.store.repo import Store

LOGGER = logging.getLogger("findling.index.search")

# Selectivity, honestly: in the synthetic case of the phase research only 31 of
# 400 candidates survived the permission check. Real instances look friendlier,
# users mostly see what lies in their own mounts, but the case exists. The answer
# to it is the bounded repeat on the PHP side, never a larger first request: a
# larger request pays the full ranking cost for hits nobody is allowed to see.

# The smallest raw chunk the scan below asks the engine for. Small pages of a
# sparsely visible corpus would otherwise crawl through the ranking a handful of
# hits at a time, and every chunk pays the fixed cost of a search.
_SCAN_CHUNK_MIN: Final = 128


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


def candidates(
    index: Index,
    store: Store,
    uid: str,
    query: Query,
    limit: int,
    offset: int = 0,
) -> CandidatePage:
    """Return one page of permitted candidates in the order the engine ranked them.

    ``offset`` and ``next_offset`` count permitted candidates, never raw engine
    hits: the caller asks to continue behind the last candidate it consumed, and
    what it consumed is by definition something it was allowed to see. The scan
    below walks the raw ranking in chunks until the page is full, one hit further
    than the page needs, and that one extra hit only ever becomes ``has_more``.

    The scan is bounded twice. It ends when the engine runs out of hits, and it
    ends at ``SEARCH_SCAN_MAX`` raw hits for the pathological case of a user who
    may see almost nothing on an instance where almost everything matches. Hitting
    the cap answers ``has_more=False``: an honestly truncated result, and the log
    line below is the trace it leaves.
    """
    searcher = index.searcher()
    # One permitted hit more than the page needs, and it only ever becomes a
    # boolean. It replaces the engine's total: a total counts documents BEFORE
    # the permission filter, so comparing against it told whoever varies offset
    # and limit how many documents of other people match a term (a counting
    # oracle, T-02-93).
    needed = offset + limit + 1
    permitted: list[Candidate] = []
    raw_cursor = 0
    scan_cap = SEARCH_SCAN_MAX

    while len(permitted) < needed and raw_cursor < scan_cap:
        chunk_limit = min(max(needed, _SCAN_CHUNK_MIN), scan_cap - raw_cursor)
        result = searcher.search(query, chunk_limit, offset=raw_cursor)
        hits = result.hits
        if not hits:
            break

        # The columns, never the document store. searcher.doc() hands back the
        # whole stored document including the full text, and that read was 99.9%
        # of the candidate round: measured 20.5 ms per hit at the 512k cap
        # against 0.02 ms for the two fast-field columns, independent of size.
        addresses = [address for _, address in hits]
        file_ids = searcher.fast_field_values(FIELD_FILE_ID, addresses)
        mtimes = searcher.fast_field_values(FIELD_MTIME, addresses)

        ranked: list[tuple[int, float, int]] = []
        for (score, _), file_id, mtime in zip(hits, file_ids, mtimes, strict=True):
            if file_id is None:
                # A hit without the key cannot be rechecked and cannot be
                # resolved into a node, so it is not a result. Skipped rather
                # than raised: one damaged document must not take the whole
                # search down with it.
                LOGGER.warning("skipping a hit without a file id")
                continue
            # A missing modification time is a display detail, so it degrades
            # to zero rather than ending the search.
            ranked.append((int(file_id), float(score), int(mtime) if mtime is not None else 0))

        # From the candidates to the permissions, never the other way round.
        # Building the list of everything a user may see is the inverse
        # question, and its cost grows with the instance instead of the query.
        visible = store.prefilter_visible(uid, [file_id for file_id, _, _ in ranked])
        permitted.extend(
            Candidate(file_id=file_id, score=score, mtime=mtime)
            for file_id, score, mtime in ranked
            if file_id in visible
        )

        raw_cursor += len(hits)
        if len(hits) < chunk_limit:
            break

    if len(permitted) < needed and raw_cursor >= scan_cap:
        # Only the fact, never the query or the counts: both are content.
        LOGGER.info("the candidate scan hit its raw ceiling and answered a truncated page")

    page = permitted[offset : offset + limit]
    return CandidatePage(
        candidates=page,
        has_more=len(permitted) > offset + limit,
        next_offset=offset + len(page),
    )


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
