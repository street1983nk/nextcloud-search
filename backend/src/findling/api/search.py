"""POST /search: the walking skeleton endpoint and the frozen wire protocol.

Two decisions are frozen here for the whole project, not just for this phase.

First, ``snippet`` is plain text. The unified search UI renders the subline as a
Vue text interpolation without ``v-html``, so any tag would be shown to the user
verbatim instead of being rendered. Highlighting therefore travels as character
offsets in ``highlights``, which stays empty until phase 2 produces real hits.

Second, the user identity comes from ``Depends(anc_app)`` and nothing else. The
AppAPI header is signed, a request body is not. ``SearchRequest`` forbids extra
fields so a body carrying ``userId`` fails validation, and the error handler in
:mod:`findling.main` turns that into an explicit 400.

The single hit this endpoint returns is the point of the phase: it names the
container host, the moment it was produced and the user the header carried. None
of the three can be fabricated outside the container, which is what makes the
result a proof rather than a demo.
"""

import socket
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from findling.nc.client import AsyncNextcloudApp, anc_app, current_user_id

ROUTER = APIRouter()

CANARY_TITLE = "Findling canary"


class SearchRequest(BaseModel):
    """Request body of the search endpoint.

    ``extra="forbid"`` is a security control, not tidiness: it is what keeps a
    caller from smuggling an identity past the signed header.
    """

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=100)


class Hit(BaseModel):
    """One result in the wire format the PHP companion expects."""

    # fileId stays camelCase: the wire format belongs to the PHP side, and a
    # rename here would silently drop the field on the way out. The naming rules
    # of ruff are not part of the configured rule set, so a noqa directive would
    # itself be a lint error (RUF100); this comment carries the reason instead.
    fileId: int
    path: str = ""
    title: str
    snippet: str
    highlights: list[tuple[int, int]] = Field(default_factory=list)
    score: float = 0.0
    mtime: int = 0


class SearchResponse(BaseModel):
    """Envelope of the search answer."""

    results: list[Hit]


def build_canary_hits(user_id: str) -> list[Hit]:
    """Return the single hit that proves the answer was produced in the container.

    Host name and timestamp exist only inside the running container, and the user
    id arrives through the signed header, so the three together cannot be forged
    by whoever calls the proxy. Pure function, so the proof is testable without
    an HTTP round trip.
    """
    produced_at = datetime.now(UTC).replace(microsecond=0)
    snippet = f"produced inside container {socket.gethostname()} at {produced_at.isoformat()} for user {user_id}"
    return [
        Hit(
            fileId=0,
            path="",
            title=CANARY_TITLE,
            snippet=snippet,
            highlights=[],
            score=0.0,
            mtime=int(produced_at.timestamp()),
        )
    ]


@ROUTER.post("/search")
async def search(
    body: SearchRequest,
    nc: Annotated[AsyncNextcloudApp, Depends(anc_app)],
) -> SearchResponse:
    """Answer with the container proof for the user named in the AppAPI header."""
    # Phase 1 ignores the query text: this endpoint proves the path, not the
    # ranking. Reading it here would suggest a search that does not exist yet.
    del body
    user_id = await current_user_id(nc)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no user in the AppAPI header")
    return SearchResponse(results=build_canary_hits(user_id))
