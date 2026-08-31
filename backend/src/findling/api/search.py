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
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from findling.api import resources
from findling.config import SEARCH_LIMIT_MAX
from findling.index.search import candidates as candidate_round
from findling.nc.client import AsyncNextcloudApp, anc_app, current_user_id
from findling.query.rewrite import build_query

LOGGER = logging.getLogger("findling.api.search")

ROUTER = APIRouter()

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

    query: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=SEARCH_LIMIT_MAX)
    offset: int = Field(default=0, ge=0)
    # camelCase because the wire format belongs to the PHP side. A rename here
    # would silently drop the field on the way in, and the naming rules of ruff
    # are not part of the configured rule set, so a noqa directive would itself
    # be a lint error (RUF100); this comment carries the reason instead.
    titleOnly: bool = False


class Candidate(BaseModel):
    """One hit before the permission recheck: four values, and no fifth.

    The three that are missing are the point, and a test asserts the field names
    as a set because their absence is invisible in every functional test.
    """

    fileId: int
    score: float = 0.0
    mtime: int = 0
    ext: str = ""


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
            ext="",
            title=CANARY_TITLE,
            snippet=text,
        )
    ]


def one_round(uid: str, text: str, limit: int, offset: int, title_only: bool) -> _Round:
    """Ask the engine once, drop what the prefilter does not confirm, mark the page.

    Synchronous, and called through ``asyncio.to_thread``: tantivy releases the
    GIL, but a long commit of the poller would still stall the event loop, and a
    stalled loop is a container that stops answering ``/heartbeat`` while it looks
    perfectly healthy in its own log.

    Every failure ends in an empty round with ``degraded`` set. There is no error
    an HTTP status could usefully carry here: the unified search asks every
    provider at once, and the one that raises costs the user the whole search
    instead of one result group.
    """
    try:
        side = resources.read_side()
        if side is None:
            return _Round([], False, offset, True)
        is_degraded = resources.degraded(side)
        rewritten = build_query(side.index, text, title_only=title_only)
        if rewritten.query is None:
            # Nothing left to search for, for instance a line that held only a
            # file type filter. A normal answer, and the engine was never asked.
            return _Round([], False, offset, is_degraded)
        page = candidate_round(side.index, side.store, uid, rewritten.query, limit, offset)
    # Deliberately every exception, for the reason in the docstring above.
    except Exception as error:
        # The type name and nothing else: a traceback carries whatever a library
        # put into its message, and the search text is the usual content.
        LOGGER.warning("the candidate search ended in an unexpected %s", type(error).__name__)
        return _Round([], False, offset, True)

    return _Round(
        [Candidate(fileId=hit.file_id, score=hit.score, mtime=hit.mtime, ext=hit.ext) for hit in page.candidates],
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
    found = await asyncio.to_thread(one_round, user_id, text, body.limit, body.offset, body.titleOnly)

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
