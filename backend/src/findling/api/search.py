"""POST /search: the first call of the two stage protocol, candidates only.

Four decisions are frozen here for the whole project, not just for this phase.
The first two are the ones phase 1 wrote down and they are unchanged.

First, text that reaches the user is plain text. The unified search UI renders
the subline as a Vue text interpolation without ``v-html``, so any tag would be
shown to the user verbatim instead of being rendered. Highlighting therefore
travels as character offsets, which the second call produces.

Second, the user identity comes from ``Depends(anc_app)`` and nothing else. The
AppAPI header is signed, a request body is not. ``SearchRequest`` forbids extra
fields so a body carrying ``userId`` fails validation, and the error handler in
:mod:`findling.main` turns that into an explicit 400.

Third, the answer carries no file name and no path. What leaves here has not been
through the permission recheck yet, and a name is already a statement about a
document this user may not be allowed to know exists. The title of a confirmed
hit is taken from the node the recheck resolved, which is both permitted and more
current than anything the index could offer.

Fourth, and this is the one the model itself enforces: :class:`Candidate` has no
text field. A snippet is file content, SRCH-02 says file content is produced
after the permission check and not before, and a text field in this model would
be the structural invitation to break that rule in a later refactoring
(pitfall 5). The one exception is the canary, which is a different class, has no
file behind it and therefore could never survive a recheck at all.

The canary itself is the diagnostic of phase 1 and it stays: host name, timestamp
and the user id out of the signed header, none of which can be fabricated outside
the running container. It answers to its own name and to nothing else, so an
ordinary search never sees it.
"""

import asyncio
import logging
import socket
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from findling.api import resources
from findling.config import (
    SEARCH_LIMIT_MAX,
    SEARCH_MTIME_MAX,
    SEARCH_OFFSET_MAX,
    SEARCH_QUERY_MAX_CHARS,
    SEARCH_TYPE_GROUPS_MAX,
    settings,
)
from findling.embed.engine import query_may_load, request_warm, warm, warm_wanted
from findling.index.search import SemanticSide
from findling.index.search import candidates as candidate_round
from findling.nc.client import AsyncNextcloudApp, anc_app, current_user_id
from findling.query.rewrite import build_query

LOGGER = logging.getLogger("findling.api.search")

ROUTER = APIRouter()

# The warm runs this process has in flight, and the only reason this set
# exists is that ``asyncio.create_task`` keeps no reference of its own: a
# task nobody holds may be collected while it runs, which is a documented
# trap of the function and a failure that leaves no line in any log
# (T-14-30). The entry is handed back by ``add_done_callback`` the moment
# the run ends, so the set is empty on an idle container.
_WARM_TASKS: set[asyncio.Task[Any]] = set()

# The exact title the PHP companion accepts for a hit without a file behind it.
# Every hit above file id 0 is resolved through the user's own folder over there
# and dropped when that resolution fails, which a hit with file id 0 always
# would. Frozen on both sides, see CANARY_TITLE in
# php/lib/Service/ExAppService.php.
CANARY_TITLE = "findling-canary"

# The same string in its other role. The canary is summoned by its own name, and
# the comparison against it is exact: "contains" would colour every search that
# happens to carry the word, and a diagnostic that shows up uninvited stops being
# evidence of anything.
CANARY_TERM = CANARY_TITLE


class SearchRequest(BaseModel):
    """Request body of the candidate call.

    ``extra="forbid"`` is a security control, not tidiness: it is what keeps a
    caller from smuggling an identity past the signed header.
    """

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=SEARCH_QUERY_MAX_CHARS)
    limit: int = Field(default=20, ge=1, le=SEARCH_LIMIT_MAX)
    # le= is a denial-of-service control (security audit C1): the offset sizes
    # the page the candidate scan has to fill before it can answer, so an
    # unbounded offset would be an unbounded amount of work per request. Counts
    # permitted candidates, never raw engine hits, see findling.index.search.
    offset: int = Field(default=0, ge=0, le=SEARCH_OFFSET_MAX)
    # camelCase because the wire format belongs to the PHP side. A rename here
    # would silently drop the field on the way in, and the naming rules of ruff
    # are not part of the configured rule set, so a noqa directive would itself
    # be a lint error (RUF100); this comment carries the reason instead.
    titleOnly: bool = False
    # A closed set and never free text. The route carries access_level USER, so
    # any signed-in account reaches it with a body of its own making, and a
    # str would be a second way into the query builder next to the search line.
    # The six names are wire vocabulary: they travel English and lower case in
    # the address bar of the result page, they are the keys of TYPE_GROUPS in
    # findling.query.rewrite, and the PHP side keeps no extension table of its
    # own. max_length bounds the list on top of the value set, because a caller
    # may repeat a name and the Should group grows with every arm.
    types: list[Literal["pdf", "documents", "spreadsheets", "presentations", "images", "text"]] = Field(
        default_factory=list, max_length=SEARCH_TYPE_GROUPS_MAX
    )
    # The three names stand a second time in findling.index.search.SORT_MODES,
    # and tests/test_search_fields_lockstep.py holds the two places together. A
    # pair that drifted apart would not be an error anywhere: SORT_MODES.get
    # answers None for a name it does not know, and None is the relevance
    # branch, so the page would quietly go back to relevance while the address
    # still says "newest".
    sort: Literal["relevance", "newest", "oldest"] = "relevance"
    # Both edges of the time range, inclusive, as the Unix epoch in seconds, and
    # both bounded for the reason written at SEARCH_MTIME_MAX. None means no
    # edge at all rather than "the epoch", which is why the default is not 0.
    since: int | None = Field(default=None, ge=0, le=SEARCH_MTIME_MAX)
    until: int | None = Field(default=None, ge=0, le=SEARCH_MTIME_MAX)


class Candidate(BaseModel):
    """One hit before the permission recheck: three values, and no fourth.

    Everything that is missing is the point, and a test asserts the field names
    as a set because their absence is invisible in every functional test. The
    extension left with the perf audit of the phase: the PHP side resolves every
    surviving id into a node that knows its current name and extension anyway,
    so the field carried stale data at the cost of a document-store read.
    """

    fileId: int
    score: float = 0.0
    mtime: int = 0


class CanaryCandidate(Candidate):
    """The one candidate that carries text, because it carries no file.

    A separate class rather than two optional fields on :class:`Candidate`: this
    way an ordinary candidate cannot hold a title or a snippet even by accident,
    and the promise is a property of the type instead of a rule somebody has to
    remember.
    """

    title: str
    snippet: str


class SearchResponse(BaseModel):
    """Envelope of the candidate answer.

    ``hasMore`` and ``nextOffset`` are the bounded repeat: the recheck on the PHP
    side can drop so many candidates that too few are left, and only that side
    knows how many survived. The loop therefore lives over there, at most three
    rounds; an unbounded loop in here would be a loop in the one place that
    cannot see its own stop condition.

    ``degraded`` says the container is answering out of an incomplete index, so
    the caller can stay quiet about it instead of guessing.
    """

    candidates: list[CanaryCandidate | Candidate]
    hasMore: bool = False
    nextOffset: int = 0
    degraded: bool = False


@dataclass(frozen=True, slots=True)
class _Round:
    """What one pass over the engine came to, before it becomes an answer."""

    candidates: list[Candidate]
    has_more: bool
    next_offset: int
    degraded: bool


def build_canary_hits(user_id: str) -> list[CanaryCandidate]:
    """Return the single hit that proves the answer was produced in the container.

    Host name and timestamp exist only inside the running container, and the user
    id arrives through the signed header, so the three together cannot be forged
    by whoever calls the proxy. Pure function, so the proof is testable without
    an HTTP round trip.
    """
    produced_at = datetime.now(UTC).replace(microsecond=0)
    text = f"produced inside container {socket.gethostname()} at {produced_at.isoformat()} for user {user_id}"
    return [
        CanaryCandidate(
            fileId=0,
            score=0.0,
            mtime=int(produced_at.timestamp()),
            title=CANARY_TITLE,
            snippet=text,
        )
    ]


def one_round(
    uid: str,
    text: str,
    limit: int,
    offset: int,
    title_only: bool,
    *,
    groups: Sequence[str] = (),
    since: int | None = None,
    until: int | None = None,
    sort: str = "relevance",
) -> _Round:
    """Ask the engine once, drop what the prefilter does not confirm, mark the page.

    Synchronous, and called through ``asyncio.to_thread``: tantivy releases the
    GIL, but a long commit of the poller would still stall the event loop, and a
    stalled loop is a container that stops answering ``/heartbeat`` while it looks
    perfectly healthy in its own log.

    Every failure ends in an empty round with ``degraded`` set. There is no error
    an HTTP status could usefully carry here: the unified search asks every
    provider at once, and the one that raises costs the user the whole search
    instead of one result group.

    ``groups``, ``since``, ``until`` and ``sort`` are the structured half of the
    result page. The first three are handed to the query builder, which turns
    them into the one filter clause both halves of the search are cut with; the
    fourth never reaches the query at all, because a sort order is not part of
    the question. All four are keyword arguments with a default so that a caller
    who filters and sorts nothing stays exactly as it was.
    """
    try:
        side = resources.read_side()
        if side is None:
            return _Round([], False, offset, True)
        is_degraded = resources.degraded(side)
        rewritten = build_query(side.index, text, title_only=title_only, groups=groups, since=since, until=until)
        if rewritten.query is None:
            # Nothing left to search for, for instance a line that held only a
            # file type filter. A normal answer, and the engine was never asked.
            return _Round([], False, offset, is_degraded)
        # The vector half, handed over as a bundle and never as a second route:
        # the merge lives inside the candidate round, above its one permission
        # prefilter, so a semantic hit travels the same way a lexical one does
        # and Provider.php does not learn that anything changed (D-20). The raw
        # text goes along because the model needs words and the rewritten query
        # is not text any more.
        # The operator rule. A line with quotation marks, a minus, a field, a
        # file type or a grammar word of the parser is a request for precision,
        # and the model cannot honour one: it sees words. A second list that
        # does not know about the request can only undercut it, so it is not
        # built at all. titleOnly is here for the same reason and for a second
        # one: the vector stock lies over the text and not over the name, so
        # every semantic hit under that filter would answer a different question
        # than the one that was asked.
        #
        # The one term rule, on the same switch and out of the measurement of
        # plan 06.1-20: a line that holds a single word is answered by the word
        # index alone. The report of that plan measured both distributions on
        # one scale and they overlap, the one word probes at 68 to 77 and the
        # paraphrase at 79.5487 from its own document, so no distance gate can
        # keep one word from dragging the whole holding in without also losing
        # the paraphrase. For one word the compound splitter, the stemmer and
        # the umlaut variant already do the work of the second list, and one
        # word gives the model nothing to read a meaning out of. Two words and
        # more stay hybrid: that is the case the semantics were built for.
        #
        # Nothing else moves. The merge, the prefilter and the shape of a
        # candidate are untouched (D-20, D-14); the vector branch simply does
        # not happen, which is the path a missing model already takes and which
        # criterion 3 covers.
        # A sort order joins that same line and gets no switch of its own. Under
        # a date order there is no fusion for a vector list to enter: the sorted
        # branch of the candidate round ranks by the mtime field and hands every
        # hit a score of 0.0, so a semantic list could only be built, embedded
        # and then dropped. Worse, a timestamp read as relevance is exactly the
        # value that would appear on the page if it were not dropped. The engine
        # side is deliberately indifferent to the bundle as well (plan 13-02);
        # this line is the promise and that indifference is its second half.
        #
        # What the round lets the model spend rides on that same line, and the
        # answer is asked for rather than worked out here.
        # ``ExAppService::REQUEST_TIMEOUT_SECONDS`` is 1.5, and on 2026-09-10
        # the first semantic search of a cold container took 1838.4 ms against
        # it: cURL error 28 in the Nextcloud log, HTTP 200 out of here, an
        # answer group without the container half and nought hits, with the
        # unified search asking again at every keystroke. So with the release
        # switched on this round answers out of the lexical list and the
        # weights are fetched back in the background instead of while somebody
        # waits. The rule itself lives in ``embed/engine.py::query_may_load``
        # and is not repeated here.
        may_load = query_may_load()
        semantic = None
        lexical_only = bool(rewritten.operators) or rewritten.one_term or title_only or sort != "relevance"
        if not lexical_only and side.vectors is not None and settings().embed_enabled:
            semantic = SemanticSide(
                vectors=side.vectors,
                model=resources.query_model(),
                text=text,
                may_load=may_load,
            )
            if not may_load:
                # This round was meant to be hybrid and is about to answer
                # without the weights, and this is the one place in the
                # container that knows both halves of that sentence. The
                # handler above cannot: ``one_round`` hands back candidates and
                # not the reason there are no vectors among them. So the
                # request is made where the occasion arises, and the handler,
                # which is the half that owns an event loop, only has to ask
                # ``warm_wanted()``. Nothing is loaded and nothing is built by
                # this call: it takes one lock for one assignment, inside a
                # request that has already spent its budget.
                request_warm()
        page = candidate_round(
            side.index,
            side.store,
            uid,
            rewritten.query,
            limit,
            offset,
            semantic=semantic,
            filter_query=rewritten.filter_query,
            sort=sort,
        )
    # Deliberately every exception, for the reason in the docstring above.
    except Exception as error:
        # The type name and nothing else: a traceback carries whatever a library
        # put into its message, and the search text is the usual content.
        LOGGER.warning("the candidate search ended in an unexpected %s", type(error).__name__)
        return _Round([], False, offset, True)

    return _Round(
        [Candidate(fileId=hit.file_id, score=hit.score, mtime=hit.mtime) for hit in page.candidates],
        page.has_more,
        page.next_offset,
        is_degraded,
    )


@ROUTER.post("/search")
async def search(
    body: SearchRequest,
    nc: Annotated[AsyncNextcloudApp, Depends(anc_app)],
) -> SearchResponse:
    """Answer with the candidates this user may see, one page at a time."""
    user_id = await current_user_id(nc)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no user in the AppAPI header")

    text = body.query.strip()
    found = await asyncio.to_thread(
        partial(
            one_round,
            user_id,
            text,
            body.limit,
            body.offset,
            body.titleOnly,
            groups=body.types,
            since=body.since,
            until=body.until,
            sort=body.sort,
        )
    )

    if warm_wanted():
        # The weights come back on the event loop this handler is already
        # running on, and the answer below does not wait for them. The four
        # alternatives were weighed in 14-RESEARCH.md 5.3 and all of them cost
        # more: the unload task alone ticks every 30 seconds, so the user's
        # second search would still be cold; a ``threading.Thread`` would be a
        # second lifecycle beside the lifespan with no stop event of its own;
        # and ``BackgroundTasks`` runs only after the response has gone out.
        # ``create_task`` on the loop that is already here adds no coupling at
        # all. The run itself blocks, like every load, so it goes through
        # ``asyncio.to_thread`` (T-14-23).
        task = asyncio.create_task(asyncio.to_thread(warm))
        _WARM_TASKS.add(task)
        task.add_done_callback(_WARM_TASKS.discard)

    hits: list[CanaryCandidate | Candidate] = []
    if text == CANARY_TERM:
        hits.extend(build_canary_hits(user_id))
    hits.extend(found.candidates)
    return SearchResponse(
        candidates=hits,
        hasMore=found.has_more,
        nextOffset=found.next_offset,
        degraded=found.degraded,
    )
