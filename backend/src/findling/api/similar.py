"""POST /similar: the documents that lie near one document (STR-01, plan 35-05).

A content route, and it is treated like one. The answer is a list of file ids,
which looks harmless, but which ids lie near a document is a statement about
that document's text. So the route is not declared in appinfo/info.xml (the
companion reaches it over the signed AppAPI path, which never consults the
route table), and it is held off that list by the same test that holds /search
and /snippets off it.

The file id arrives from outside. That the caller only asks about a file its
user may open is an assumption about a different process running correctly, so
the permission prefilter runs here first, on the source, before a single vector
of it is read. Without it this route would be a confused deputy: whoever reaches
the proxy could learn which documents resemble any file by its number. The
neighbours pass the same prefilter before they leave, and the PHP side rechecks
them once more; the prefilter is a speed-up there and never the boundary.

An empty list is a complete answer. A foreign source, an unknown one, one
without vectors and one with nothing near it all look the same from outside,
because telling them apart would tell a caller whether somebody else's file
exists.

No model is involved. The source document is already in the vector stock, so
the mean of its stored chunks is the query and one scan answers it; the view
works on a box where the embedder is switched off or still loading. No distance
and no score leave this route, only ids in rank order (D-14).
"""

import asyncio
import logging
from functools import partial
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from findling.api import resources
from findling.config import SEARCH_LIMIT_MAX
from findling.index import search as index_search
from findling.nc.client import AsyncNextcloudApp, anc_app, current_user_id

LOGGER = logging.getLogger("findling.api.similar")

ROUTER = APIRouter()


class SimilarRequest(BaseModel):
    """Request body of the neighbour call: one source document and a page size.

    camelCase because the wire format belongs to the PHP side. No user field:
    identity comes from the AppAPI header alone, and a body that names one is
    refused with 400 by the handler in main.py, which extra="forbid" feeds.
    """

    model_config = ConfigDict(extra="forbid")

    fileId: int = Field(ge=1)
    limit: int = Field(ge=1, le=SEARCH_LIMIT_MAX)


class SimilarCandidate(BaseModel):
    """One neighbour, as its id and nothing else."""

    fileId: int


class SimilarResponse(BaseModel):
    """The neighbours in rank order, nearest first, never the source itself."""

    candidates: list[SimilarCandidate]
    degraded: bool = False


def neighbours(user_id: str, file_id: int, limit: int) -> tuple[list[int], bool]:
    """Find the confirmed neighbours of one document. Runs in a worker thread.

    Synchronous and called through ``asyncio.to_thread`` for the reason every
    read route of this container is: a long commit of the poller would otherwise
    stall the event loop.

    Every failure ends in an empty list. The companion shows the view without
    entries and the rest of the page is unaffected, which is a far better
    outcome than an exception.
    """
    try:
        side = resources.read_side()
        if side is None:
            return [], True
        is_degraded = resources.degraded(side)
        if side.vectors is None:
            return [], is_degraded
        return index_search.similar_candidates(side.store, side.vectors, user_id, file_id, limit), is_degraded
    # Deliberately every exception, for the reason in the docstring above.
    except Exception as error:
        # The type name and nothing else: a traceback carries whatever a library
        # put into its message, and here that could be a file id or a user.
        LOGGER.warning("finding similar documents ended in an unexpected %s", type(error).__name__)
        return [], True


@ROUTER.post("/similar")
async def similar(
    body: SimilarRequest,
    nc: Annotated[AsyncNextcloudApp, Depends(anc_app)],
) -> SimilarResponse:
    """Answer with the confirmed neighbours of one confirmed document, and nothing else."""
    user_id = await current_user_id(nc)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no user in the AppAPI header")

    found, is_degraded = await asyncio.to_thread(partial(neighbours, user_id, body.fileId, body.limit))
    return SimilarResponse(candidates=[SimilarCandidate(fileId=one) for one in found], degraded=is_degraded)
