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

*The two halves of the search are merged in here and nowhere else.* Phase 6 adds
a vector ranking beside the engine ranking, and it is joined to it inside
:func:`candidates`, above the one call that asks about permissions (D-20). That
is not tidiness. This function is the only place a candidate leaves the
container from, so a merge in here inherits the permission chain, the offset
semantics and the parity test of phase 5 by construction, while a route of its
own would have had to be given all three again and would have been believed
without them.

Measured for the phase: the engine search costs 0.1 ms, the prefilter 0.18 ms for
400 candidates, an overfetch of 400 candidates 4.2 ms. The expensive part of a
search is neither of them, it is the two proxy round trips and the recheck.
"""

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final, Protocol

from tantivy import DocAddress, Document, Index, Occur, Order, Query, Schema, Searcher, SnippetGenerator

from findling.config import SEARCH_SCAN_MAX, settings
from findling.embed.model import EmbedOutcome, to_int8
from findling.index.fusion import ChunkHit, documents_from_chunks, near_enough, reciprocal_rank_fusion
from findling.index.schema import FIELD_BODY_DE, FIELD_FILE_ID, FIELD_MTIME
from findling.store.repo import Store
from findling.store.vectors import BestChunk, VectorStore

LOGGER = logging.getLogger("findling.index.search")

# Selectivity, honestly: in the synthetic case of the phase research only 31 of
# 400 candidates survived the permission check. Real instances look friendlier,
# users mostly see what lies in their own mounts, but the case exists. The answer
# to it is the bounded repeat on the PHP side, never a larger first request: a
# larger request pays the full ranking cost for hits nobody is allowed to see.

# The smallest raw chunk the relevance scan below asks the engine for. Small
# pages of a sparsely visible corpus would otherwise crawl through the ranking a
# handful of hits at a time, and every chunk pays the fixed cost of a search.
# The sorted round uses it as its FIXED stride rather than a minimum, because
# there the portion boundaries decide where a tie group is cut for the re-sort,
# and boundaries that move with the request produce duplicates and gaps at page
# transitions (finding of 18.09.2026 in _sorted_round).
_SCAN_CHUNK_MIN: Final = 128

# How many merged documents are handed to the permission prefilter at a time.
# The window is 100 by default, so in practice this is one band and the constant
# looks pointless; it is not. An operator who deepens the window is the person
# who would otherwise pay the prefilter for six hundred documents on a page that
# was full after twenty.
_PREFILTER_BAND: Final = 128

# The three orders a page can be asked for, and None does not mean "no order".
# It means "the relevance order of the fusion", which is the order this module
# has always produced and the only one that has a score behind it.
#
# This table is the one place the wire vocabulary is defined. The Literal values
# of the request model in api/search.py are held against these keys rather than
# written out a second time, because two lists of three words drift apart on the
# day somebody adds a fourth (plan 13-03 builds the gate for it).
SORT_MODES: Final[Mapping[str, Order | None]] = {
    "relevance": None,
    "newest": Order.Desc,
    "oldest": Order.Asc,
}


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


class QueryEmbedder(Protocol):
    """Whatever can turn one search line into one vector.

    Written as a protocol rather than as :class:`findling.embed.model.EmbeddingModel`
    itself for the same reason :class:`ByteRange` below is one: the loop can then
    be exercised without 118 MB of weights on the machine that runs the suite,
    and the wrapper is free to change shape without this module noticing.

    ``may_load`` travels with the call because the reason not to load lies with
    the caller and never with the model: a round that runs under the 1.5 second
    ceiling of a user route says so here, and one that has all the time in the
    world says nothing and gets the behaviour of every round before this phase.
    """

    def embed_query(self, text: str, *, may_load: bool = True) -> EmbedOutcome: ...


@dataclass(frozen=True, slots=True)
class SemanticSide:
    """The vector half of one candidate round.

    ``text`` is the raw search line and not the rewritten engine query, because
    the model needs words and a rewritten query is not text any more.

    **That text is user content, and no log line of this module may carry it.**
    It arrives here beside a vector store and a model that both have opinions
    about what went wrong, and the two failure branches below are exactly where
    a library message would drag the search somebody typed into the log
    (T-06-27). Both of them print a type name and nothing else.

    ``may_load`` is what this round lets the model spend. False means: answer
    out of the engine you are holding or give the ``embedding_unavailable``
    verdict, but do not go and fetch 118 MB of weights while somebody is
    waiting. **Its default is True on purpose.** A round that says nothing
    about the matter behaves exactly as it did before this phase, which keeps
    every caller that does not know about the release, the diagnosis route
    among them, on the path it has always taken. Who sets it to False, and on
    what grounds, is decided in ``embed/engine.py::query_may_load`` and never
    here: this module reads no setting.
    """

    vectors: VectorStore
    model: QueryEmbedder
    text: str
    may_load: bool = True


def _ranked(
    searcher: Searcher,
    hits: Sequence[tuple[float, DocAddress]],
    *,
    scored: bool = True,
) -> list[tuple[int, float, int]]:
    """Turn engine hits into id, score and timestamp, dropping the unusable ones.

    ``scored=False`` puts 0.0 where the first element of the tuple would go, and
    that is not a nicety. Under ``order_by_field`` tantivy hands back the field
    value in that position instead of the score (measured 16.09.2026: 500, 400,
    300 instead of 0.087), so a sorted round that took the value as it comes
    would ship a timestamp in the order of 1.7e9 out of this container as a
    relevance value. The sorted branch has no relevance to report, and 0.0 is the
    honest way of saying so (D-04).
    """
    # The columns, never the document store. searcher.doc() hands back the whole
    # stored document including the full text, and that read was 99.9% of the
    # candidate round: measured 20.5 ms per hit at the 512k cap against 0.02 ms
    # for the two fast-field columns, independent of size.
    addresses = [address for _, address in hits]
    file_ids = searcher.fast_field_values(FIELD_FILE_ID, addresses)
    mtimes = searcher.fast_field_values(FIELD_MTIME, addresses)

    ranked: list[tuple[int, float, int]] = []
    for (score, _), file_id, mtime in zip(hits, file_ids, mtimes, strict=True):
        if file_id is None:
            # A hit without the key cannot be rechecked and cannot be resolved
            # into a node, so it is not a result. Skipped rather than raised:
            # one damaged document must not take the whole search down with it.
            LOGGER.warning("skipping a hit without a file id")
            continue
        # A missing modification time is a display detail, so it degrades to
        # zero rather than ending the search.
        ranked.append((int(file_id), float(score) if scored else 0.0, int(mtime) if mtime is not None else 0))
    return ranked


def _permit(store: Store, uid: str, ranked: Sequence[Candidate]) -> list[Candidate]:
    """Keep the candidates the prefilter confirms, in the order they arrived.

    From the candidates to the permissions, never the other way round. Building
    the list of everything a user may see is the inverse question, and its cost
    grows with the instance instead of with the query.

    One function rather than two call sites, and that is an assertion and not a
    style: a test greps this file for the name of the prefilter and expects to
    find it exactly twice, here and in the snippet cut. The vector branch merges
    above this line, so it passes through the same one gate every lexical hit
    passes through (T-06-25, D-20).
    """
    if not ranked:
        return []
    visible = store.prefilter_visible(uid, [candidate.file_id for candidate in ranked])
    return [candidate for candidate in ranked if candidate.file_id in visible]


def _semantic_documents(
    semantic: SemanticSide | None,
    *,
    window: int,
    scan_max: int,
    ceiling: float,
    band: float,
) -> list[int]:
    """The vector ranking of one query as file ids, or an empty list.

    **The distance gate runs in here, before the aggregation.** A kNN query
    answers k neighbours whether or not any of them is near, so without it every
    document of a small holding becomes a semantic candidate of every search
    (CI run 34031891300). Gating the chunks rather than the documents is
    equivalent, because the value the aggregation keeps per document is its
    smallest distance, and it is the cheaper of the two: it works on the list
    that is already in hand and leaves D-11 untouched.

    **The try below is the point of this function, and its position is the point
    of the try.** ``one_round`` in the API layer already catches everything, and
    that catch answers with an EMPTY round: a missing model, an extension that
    will not load or a damaged vector file would therefore take the full text
    answer down with them, which is word for word what criterion 3 forbids. So
    the vector branch carries its own, narrower net, one level further in, and
    everything it catches ends as an empty list. The merge then becomes the
    identity on the engine ranking and the user gets full text results (D-19).

    The log line follows the shape of the one in ``api/search.py``: the type
    name and nothing else. A traceback carries whatever a library put into its
    message, and the search text is sitting right next to it.
    """
    if semantic is None:
        return []
    try:
        # The switch of the round, handed on and never decided here. Is the
        # answer ``EmbedOutcome.unavailable()``, this function returns an empty
        # list, the merge becomes the identity on the lexical ranking and the
        # user gets full text hits. That is D-19, the path exists, it is tested,
        # and a container without a model walks it every day. A release
        # therefore enters no new branch, it enters an old one.
        outcome = semantic.model.embed_query(semantic.text, may_load=semantic.may_load)
        if not outcome.available or not outcome.vectors:
            # The honest verdict of the wrapper rather than an exception, and it
            # is the ordinary state of a container built without the model. Same
            # answer as a failure, without a warning that would repeat per search.
            return []
        neighbours = semantic.vectors.nearest(to_int8(outcome.vectors[0]), scan_max, k_max=scan_max)
    # Deliberately every exception, for the reason in the docstring above.
    except Exception as error:
        LOGGER.warning("the vector branch of the search ended in an unexpected %s", type(error).__name__)
        return []

    if len(neighbours) >= scan_max:
        # Only the fact, never the query and never the counts: both are content.
        # An honestly truncated neighbour list, the same answer the raw ceiling
        # of the engine scan gives.
        LOGGER.info("the vector scan hit its own ceiling and answered a truncated neighbour list")

    # The ceiling line above is decided against the RAW neighbour list on
    # purpose: it says something about the scan and not about the gate, and a
    # truncated scan is a truncated scan whether or not anything survived the
    # distance afterwards.
    near = near_enough(
        [
            ChunkHit(file_id=neighbour.file_id, chunk_id=neighbour.chunk_id, distance=neighbour.distance)
            for neighbour in neighbours
        ],
        ceiling=ceiling,
        band=band,
    )
    documents = documents_from_chunks(near)
    return [document.file_id for document in documents[:window]]


@dataclass(frozen=True, slots=True)
class RankedSides:
    """The two ranked lists of one query, before anything merges them.

    File ids and no scores, because the one caller outside this module is the
    admin diagnosis and what it asks is which list a document stands in. A rank
    or a distance would be a statement about how well a document matched, and
    this project keeps those out of everything that leaves the container (D-14).
    """

    lexical: list[int]
    semantic: list[int]


def _sides(
    searcher: Searcher,
    query: Query,
    *,
    window: int,
    semantic: SemanticSide | None,
    scan_max: int,
    ceiling: float,
    band: float,
) -> tuple[list[tuple[int, float, int]], list[int], int]:
    """Both rankings of one query, plus the number of raw engine hits behind them.

    One function and two callers, and that is the point rather than an economy
    of lines. :func:`candidates` merges these two lists into the answer a user
    gets; :func:`ranked_sides` hands them to the admin diagnosis so it can say
    which of them a document came from. A second way of building either list
    would answer that question about a search this container never ran, and the
    difference would show up as a mark that is right most of the time.

    The third value is ``len(hits)`` and it never leaves :func:`candidates`: the
    continuation behind the window needs the raw cursor, and a raw cursor is the
    counting oracle of T-02-93 the moment it crosses a process boundary.
    """
    hits = searcher.search(query, window).hits
    lexical = _ranked(searcher, hits)
    documents = _semantic_documents(semantic, window=window, scan_max=scan_max, ceiling=ceiling, band=band)
    return (lexical, documents, len(hits))


def ranked_sides(index: Index, query: Query, *, semantic: SemanticSide | None = None) -> RankedSides:
    """The two rankings of one query, for the admin diagnosis and for nobody else.

    The same window and the same two lists a search builds, through the same
    function, which is what makes the answer of the diagnosis a statement about
    this container's search rather than about a reconstruction of it.

    No permission prefilter, and that is a property of the caller and not an
    omission here: the diagnosis is an administrator asking about one file they
    already named, admin side and not once per hit, which is the whole reason
    D-14 puts the origin mark over there instead of on the search path.
    """
    resolved = settings()
    searcher = index.searcher()
    window = min(resolved.search_rrf_window, SEARCH_SCAN_MAX)
    lexical, documents, _ = _sides(
        searcher,
        query,
        window=window,
        semantic=semantic,
        scan_max=resolved.vector_scan_max,
        ceiling=resolved.vector_max_distance,
        band=resolved.vector_distance_band,
    )
    return RankedSides(lexical=[file_id for file_id, _, _ in lexical], semantic=documents)


def _mtimes_of(
    searcher: Searcher,
    schema: Schema,
    file_ids: Sequence[int],
    *,
    filter_query: Query | None = None,
) -> dict[int, int]:
    """Timestamps of the documents only the vector half contributed.

    One search for all of them rather than one per document: a term query per id
    would pay the fixed cost of a search a hundred times for a page of a hundred.

    A document the index does not know is absent from the answer, and that is
    the second job of this function. A file id that lives in the vector stock
    but no longer in the index is a leftover of a delete path, and handing it
    out as a candidate would produce a hit that nothing on the other side can
    ever resolve.

    ``filter_query`` is the third job, and it is the whole reason the clause of
    query/rewrite.py is handed out separately. The vector stock knows neither an
    extension nor a timestamp; its hits never pass through the parser, and this
    lookup is the only place they meet the index at all. What falls out here is
    missing from ``known`` and therefore drops out of ``merged`` a few lines
    down. A filter that lives in the engine query alone lets hits of a foreign
    type through the semantic side, which on the page reads as docx results under
    the chip "PDF" (13-RESEARCH finding 1).

    The price is worth naming, because it is visible rather than hidden:
    ``VECTOR_SCAN_MAX`` pulls its chunks BEFORE this cut, so under a narrow
    filter the semantic half shrinks noticeably and sometimes to nothing. That is
    a property of a deadline on the scan, not a defect, and the value is not
    raised in this phase.
    """
    if not file_ids:
        return {}
    clauses = [(Occur.Should, Query.term_query(schema, FIELD_FILE_ID, file_id)) for file_id in file_ids]
    wanted = Query.boolean_query(clauses)
    if filter_query is not None:
        wanted = Query.boolean_query([(Occur.Must, wanted), (Occur.Must, filter_query)])
    hits = searcher.search(wanted, len(file_ids)).hits
    addresses = [address for _, address in hits]
    found = searcher.fast_field_values(FIELD_FILE_ID, addresses)
    times = searcher.fast_field_values(FIELD_MTIME, addresses)
    return {
        int(file_id): int(mtime) if mtime is not None else 0
        for file_id, mtime in zip(found, times, strict=True)
        if file_id is not None
    }


def _sorted_round(
    searcher: Searcher,
    query: Query,
    *,
    order: Order,
    scan_cap: int,
    needed: int,
    store: Store,
    uid: str,
) -> tuple[list[Candidate], int]:
    """One round by modification time: purely lexical, no merge, no score.

    The order is built by the engine over the fast column and never by sorting a
    ranked list afterwards. Re-sorting the hundred most relevant documents would
    answer "the newest of the most relevant", which is a different question from
    the one the user asked, and on a large holding it is a wrong answer rather
    than an approximate one.

    ``semantic`` has no place in here, and that is a decision rather than a
    forgotten branch. Without a fusion there is no window to continue behind, and
    a vector list put in date order would be a relevance list without relevance.
    The caller switches the vector half off anyway (plan 13-03); this branch
    simply never asks for it, which is the second, defensive half of the same
    promise.
    """
    permitted: list[Candidate] = []
    raw_cursor = 0
    reverse = order is Order.Desc
    while len(permitted) < needed and raw_cursor < scan_cap:
        # The portion size is a constant and never a function of the request.
        # Its predecessor, ``max(needed, _SCAN_CHUNK_MIN)``, shifted the portion
        # boundaries with the requested depth, and together with the re-sort
        # below that decomposed one sequence differently per page: measured on
        # 18.09.2026 at the running instance, 300 rows over twelve pages held
        # only 273 distinct documents, the duplicates starting exactly where
        # ``needed`` first exceeded the minimum. A deep page now pays a handful
        # of engine calls instead of one, bounded by ``scan_cap``; that is the
        # price of every request reproducing the same overall sequence.
        chunk_limit = min(_SCAN_CHUNK_MIN, scan_cap - raw_cursor)
        hits = searcher.search(query, chunk_limit, order_by_field=FIELD_MTIME, order=order, offset=raw_cursor).hits
        if not hits:
            break
        portion = [
            Candidate(file_id=file_id, score=score, mtime=mtime)
            for file_id, score, mtime in _ranked(searcher, hits, scored=False)
        ]
        # The second key of FILT-02 is handwork. Measured on 16.09.2026 against
        # the installed tantivy 0.26.0: a tie is handed back in segment and
        # document address order, not by file id (insertion order 7, 3, 9, 1 came
        # back as 7, 3, 9, 1). The honest limit of doing it per portion: a group
        # of equal timestamps that falls apart exactly at a portion boundary is
        # ordered within each portion and not across both. With the fixed stride
        # above every request cuts the sequence at the same multiples of
        # ``_SCAN_CHUNK_MIN``, so the offset slices of neighbouring pages carry
        # neither duplicates nor gaps; with a request-dependent stride they did
        # (finding of 18.09.2026, see the loop head).
        portion.sort(key=lambda candidate: (candidate.mtime, candidate.file_id), reverse=reverse)
        permitted.extend(_permit(store, uid, portion))
        raw_cursor += len(hits)
        if len(hits) < chunk_limit:
            break
    return permitted, raw_cursor


def candidates(
    index: Index,
    store: Store,
    uid: str,
    query: Query,
    limit: int,
    offset: int = 0,
    *,
    semantic: SemanticSide | None = None,
    filter_query: Query | None = None,
    sort: str = "relevance",
) -> CandidatePage:
    """Return one page of permitted candidates, engine and vectors merged into one.

    ``offset`` and ``next_offset`` count permitted candidates, never raw engine
    hits: the caller asks to continue behind the last candidate it consumed, and
    what it consumed is by definition something it was allowed to see. That is
    the property the rebuild of this loop had to carry over, because an offset in
    engine-hit space is a counting oracle for documents of other people
    (T-02-93), and it is asserted by a test that compares two pages against one
    page of twice the size.

    The work happens in two sections, and they exist for two different reasons.

    Section one is the fusion window. A rank exists only relative to a list, so
    both lists have to be complete before a single score can be computed: the
    first ``SEARCH_RRF_WINDOW`` engine hits and at most ``VECTOR_SCAN_MAX``
    chunk hits, the latter aggregated onto documents by their best chunk. The
    merged list then goes through the prefilter in bands until the page is full,
    one permitted hit further than it needs, and that one extra hit only ever
    becomes ``has_more``.

    Section two is the continuation behind the window, and it is the answer to
    the reservation of D-12 rather than a completeness exercise. Behind the
    window the order is purely lexical, which is not a defect but the definition
    of a window: a document that is semantically strong stands inside it, and
    one that sits at semantic rank 500 would contribute nothing at a deeper
    window either. The section exists because the window interacts with the
    selectivity of the prefilter, measured at 31 of 400 candidates in the
    synthetic worst case, and at that selectivity a window of 100 per source
    yields fewer than ten permitted hits.

    Both sections are bounded by ``SEARCH_SCAN_MAX`` raw hits, for the
    pathological case of a user who may see almost nothing on an instance where
    almost everything matches. Hitting the ceiling answers ``has_more=False``:
    an honestly truncated result, and the log line below is the trace it leaves.

    ``sort`` replaces both sections with a single one (:func:`_sorted_round`),
    and it brings one consequence that is the normal case of that mode rather
    than a defect: on an instance with a large foreign holding, a user with few
    files of their own gets systematically empty pages by date, because the
    newest documents very probably belong to somebody else. There is no extra
    round for it, no larger window and no permission aware prefilter; the answer
    to it is the bounded repeat on the PHP side, exactly as under relevance.
    """
    resolved = settings()
    searcher = index.searcher()
    # One permitted hit more than the page needs, and it only ever becomes a
    # boolean. It replaces the engine's total: a total counts documents BEFORE
    # the permission filter, so comparing against it told whoever varies offset
    # and limit how many documents of other people match a term (a counting
    # oracle, T-02-93). CandidatePage still carries no total, and this is the
    # number that keeps it from needing one.
    needed = offset + limit + 1
    scan_cap = SEARCH_SCAN_MAX
    window = min(resolved.search_rrf_window, scan_cap)

    # The switch, and it is deliberately silent about a name it does not know:
    # the route already holds its three values against the table, and a second
    # exception in here would turn a typo in an address into an HTTP 500.
    order = SORT_MODES.get(sort)
    if order is not None:
        sorted_hits, sorted_cursor = _sorted_round(
            searcher,
            query,
            order=order,
            scan_cap=scan_cap,
            needed=needed,
            store=store,
            uid=uid,
        )
        if len(sorted_hits) < needed and sorted_cursor >= scan_cap:
            # Only the fact, never the query or the counts: both are content.
            LOGGER.info("the candidate scan hit its raw ceiling and answered a truncated page")
        sorted_page = sorted_hits[offset : offset + limit]
        return CandidatePage(
            candidates=sorted_page,
            has_more=len(sorted_hits) > offset + limit,
            next_offset=offset + len(sorted_page),
        )

    # Section 1, the fusion window. Both lists come out of the one function the
    # admin diagnosis asks as well, so the mark it hands an operator names the
    # list a document really stood in here.
    lexical, semantic_documents, raw_hits = _sides(
        searcher,
        query,
        window=window,
        semantic=semantic,
        scan_max=resolved.vector_scan_max,
        ceiling=resolved.vector_max_distance,
        band=resolved.vector_distance_band,
    )
    fused = reciprocal_rank_fusion(
        [file_id for file_id, _, _ in lexical],
        semantic_documents,
        k=resolved.search_rrf_k,
        lexical_weight=resolved.search_lexical_weight,
        semantic_weight=resolved.search_semantic_weight,
    )

    known = {file_id: mtime for file_id, _, mtime in lexical}
    known.update(
        _mtimes_of(
            searcher,
            index.schema,
            [file_id for file_id, _ in fused if file_id not in known],
            filter_query=filter_query,
        )
    )
    # Everything the merge produced is remembered, including what the index
    # could not resolve, so that the continuation below cannot deliver a
    # document this section already decided about a second time.
    seen = {file_id for file_id, _ in fused}

    permitted: list[Candidate] = []
    merged = [(file_id, score) for file_id, score in fused if file_id in known]
    for start in range(0, len(merged), _PREFILTER_BAND):
        if len(permitted) >= needed:
            break
        band = [
            Candidate(file_id=file_id, score=score, mtime=known[file_id])
            for file_id, score in merged[start : start + _PREFILTER_BAND]
        ]
        permitted.extend(_permit(store, uid, band))

    # Section 2, the continuation behind the window. The score stays on the
    # scale of the merge instead of falling back to the raw engine score: a
    # document at lexical rank r contributes lexical_weight / (k + r) in the
    # window, and continuing that count is what keeps the numbers of one answer
    # comparable across the boundary. Every hit advances the rank, including the
    # ones already delivered, because the rank belongs to the lexical list and
    # not to what survived the prefilter.
    lexical_rank = len(lexical)
    raw_cursor = raw_hits
    exhausted = raw_hits < window
    while not exhausted and len(permitted) < needed and raw_cursor < scan_cap:
        chunk_limit = min(max(needed, _SCAN_CHUNK_MIN), scan_cap - raw_cursor)
        more = searcher.search(query, chunk_limit, offset=raw_cursor).hits
        if not more:
            break
        tail: list[Candidate] = []
        for file_id, _, mtime in _ranked(searcher, more):
            lexical_rank += 1
            if file_id in seen:
                continue
            seen.add(file_id)
            score = resolved.search_lexical_weight / (resolved.search_rrf_k + lexical_rank)
            tail.append(Candidate(file_id=file_id, score=score, mtime=mtime))
        permitted.extend(_permit(store, uid, tail))
        raw_cursor += len(more)
        if len(more) < chunk_limit:
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


def _inside(bound: int, limit: int) -> int:
    """Keep a reported byte offset inside the fragment it claims to describe."""
    return min(max(bound, 0), limit)


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
    limit = len(data)
    # The prefix of the fragment is decoded once for the whole conversion, not
    # once per reported bound. The earlier form built data[:bound] for every
    # number that arrived, so ten ranges decoded the same leading bytes ten
    # times over; the walk below reads every byte at most once and answers the
    # same character positions.
    #
    # errors="ignore" is the robustness of this function rather than a detail. A
    # bound may land in the middle of a multi byte character, and a decode that
    # insists on a clean prefix ends the entire search with an exception at that
    # point (T-05-22). A snippet that loses one character to a badly placed
    # bound is a far smaller failure than a search that answers nothing at all.
    wanted = {_inside(edge, limit) for reported in ranges for edge in (reported.start, reported.end)}
    chars_before: dict[int, int] = {}
    cursor = 0
    seen = 0
    for bound in sorted(wanted):
        seen += len(data[cursor:bound].decode("utf-8", errors="ignore"))
        chars_before[bound] = seen
        cursor = bound

    spans = sorted(
        (chars_before[_inside(reported.start, limit)], chars_before[_inside(reported.end, limit)])
        for reported in ranges
    )
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        # Strictly less, and that is the whole distinction. Ranges that overlap
        # are the same word seen through several constituents of a compound and
        # belong together; a range that merely begins where the previous one
        # ended is the next match and stays its own highlight. The earlier form
        # compared with <= and turned two neighbouring hits into one mark.
        if merged and start < merged[-1][1]:
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


def _rank_chunks(semantic: SemanticSide | None, file_ids: Sequence[int]) -> dict[int, BestChunk]:
    """Where the passage of each confirmed document sits, or nothing at all.

    **Every argument of this function is already confirmed, and that is its
    whole position in the file.** It is called once, after the prefilter has
    answered, with the documents that survived it. Asking the vector store
    first and dropping the refused documents afterwards would produce the same
    answer and would have spent the embedding, the scan and the read on
    documents this user may not see (T-06-37).

    The try is the same narrow net ``_semantic_documents`` carries and it is
    there for the same reason: a missing model, an extension that will not load
    or a damaged vector file must cost the semantic excerpt and never the
    answer. Everything it catches ends as an empty mapping, and every document
    then takes the first path, which is the behaviour of this function before
    plan 06-08 (D-13, D-19).

    The log line prints a type name and nothing else. The raw search line sits
    in ``semantic.text`` right beside a library that has an opinion about what
    went wrong, and that line is user content (T-06-39).
    """
    if semantic is None:
        return {}
    try:
        outcome = semantic.model.embed_query(semantic.text, may_load=semantic.may_load)
        if not outcome.available or not outcome.vectors:
            # The honest verdict of the wrapper rather than an exception, and
            # the ordinary state of a container built without the model. Same
            # answer as a failure, without a warning that would repeat per call.
            return {}
        return semantic.vectors.best_chunk_for(file_ids, to_int8(outcome.vectors[0]))
    # Deliberately every exception, for the reason in the docstring above.
    except Exception as error:
        LOGGER.warning("the vector branch of the excerpt cut ended in an unexpected %s", type(error).__name__)
        return {}


def _passage_of(document: Document, chunk: BestChunk | None, *, limit: int) -> str:
    """The stored text between two character offsets, cut to the excerpt cap.

    ``body_de`` is the only stored copy of the extracted text in the whole
    system, and this reads it exactly the way
    :meth:`findling.index.writer.IndexBatchWriter.stored_body` does, out of the
    document the caller is already holding.

    **The two offsets are characters and the slice below counts characters.**
    This project has measured the confusion once already, at
    :func:`char_ranges`: the engine reports (35, 51) where the character range
    is (35, 50). A slice on bytes would move the excerpt of every document with
    an umlaut in front of the passage, silently, and in German that is all of
    them (T-06-40).

    The cap is the same number the generator gets. Its meaning differs slightly
    on the two paths, because ``set_max_num_chars`` compares bytes inside the
    fragmenter while this one counts characters, and the direction of that
    difference is the harmless one: an excerpt of this path is never longer
    than the number an operator set.
    """
    if chunk is None:
        return ""
    values = document.to_dict().get(FIELD_BODY_DE, [])
    if not values:
        return ""
    return str(values[0])[chunk.char_start : chunk.char_end][:limit]


def snippets_for(
    index: Index,
    store: Store,
    uid: str,
    query: Query,
    file_ids: Sequence[int],
    *,
    semantic: SemanticSide | None = None,
) -> list[SnippetText]:
    """Cut one text excerpt per confirmed file id, in the order they were asked for.

    The prefilter runs as the first action of this function, before a single byte
    of text is read. Without it this path would be a confused deputy: a snippet is
    file content, and whoever reaches the proxy could otherwise ask for the
    content of any document by its id. That the caller already dropped everything
    the recheck refused is not an argument, it is an assumption about a different
    process running correctly, and the cost of not making that assumption was
    measured at 0.2 ms. **The second excerpt path lies behind that same line.**
    The query is embedded and the rank chunks are asked for only once the
    confirmed set is known, and the cut itself happens in the same loop body as
    the first path, so both kinds of excerpt pass the one gate (T-06-37).

    A document the index does not know is skipped. A document the query does not
    match inside the text field yields an empty excerpt rather than an error: a
    hit without a snippet is still a hit, and the subline falls back to the path
    on the PHP side.

    ``semantic`` is what turns that last sentence from the whole story into the
    first half of it. A hit only the vector branch found has by definition no
    literal overlap with the query, so the generator answers an empty fragment,
    and for such a hit that is the normal case rather than the exception. When
    the bundle is present, an empty fragment is replaced by the passage of the
    chunk that matched, carrying no highlights because there is no literal match
    to mark (D-13). Without the bundle, and whenever the vector branch fails,
    this function behaves exactly as it did before plan 06-08.
    """
    visible = store.prefilter_visible(uid, file_ids)
    if not visible:
        return []

    # Everything below this line is about documents the prefilter confirmed.
    confirmed = [file_id for file_id in file_ids if file_id in visible]
    ranked = _rank_chunks(semantic, confirmed)

    generator = SnippetGenerator.create(index.searcher(), query, index.schema, FIELD_BODY_DE)
    # Despite its name this is a byte comparison inside the fragmenter, so a
    # German sentence fits into slightly less than the number suggests. The value
    # is the one cap of this module and lives in findling.config with the rest.
    cap = settings().snippet_chars
    generator.set_max_num_chars(cap)

    excerpts: list[SnippetText] = []
    for file_id in confirmed:
        document = _document_for(index, file_id)
        if document is None:
            continue
        snippet = generator.snippet_from_doc(document)
        fragment = snippet.fragment()
        if fragment:
            excerpts.append(
                SnippetText(file_id=file_id, text=fragment, highlights=char_ranges(fragment, snippet.highlighted()))
            )
            continue
        # The second path, and it produces text without marks on purpose: there
        # is no literal match in this document, so a highlight would point at a
        # word the user never searched for. Without a rank chunk this is the
        # empty excerpt of before, which is still a hit.
        excerpts.append(SnippetText(file_id=file_id, text=_passage_of(document, ranked.get(file_id), limit=cap)))
    return excerpts
