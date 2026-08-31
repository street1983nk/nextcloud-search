"""POST /snippets: the second call, and the only content this container hands out.

An excerpt is document text. SRCH-02 says text is produced after the permission
check and never before, and the permission check runs in PHP, after the first
call answered. That is the whole reason there are two calls instead of one: with
one call the text of every candidate would already sit in the PHP process before
the security boundary ran, and a slip in the filter loop would be a content leak
rather than one hit too many.

The file ids arrive from outside. That the caller only sends what survived its
recheck is an assumption about a different process running correctly, so the
permission prefilter runs here as well, as the first action, before a byte of
text is read. Without it this endpoint would be a confused deputy: whoever
reaches the proxy could ask for the content of any document by its number. The
measured cost of not making that assumption is 0.2 ms.

A missing key is a complete answer. There is no error that would tell a caller
whether a file exists, is empty or belongs to somebody else, because all three
have to look the same from here.

The text is plain, always. The engine also offers the fragment with bold markup
around the matches, and nothing in this path ever asks for that form: the
unified search UI interpolates the subline as text, so a tag would reach the
user verbatim. Highlighting travels as character offsets instead, converted from
the byte ranges the engine reports.
"""

import asyncio
import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from findling.api import resources
from findling.config import SEARCH_LIMIT_MAX
from findling.index import search as index_search
from findling.nc.client import AsyncNextcloudApp, anc_app, current_user_id
from findling.query.rewrite import build_query

LOGGER = logging.getLogger("findling.api.snippets")

ROUTER = APIRouter()

# The measuring aid, and it is worth two sentences about what it is not.
#
# It exists so that the CI of plan 02-14 can show that the provider keeps its
# 2.5 second wall clock: with the container answering slowly, the hits have to
# appear with the path as their subline instead of disappearing. It can delay and
# nothing else, it works in this endpoint and in no other, its default is zero,
# and it is deliberately absent from appinfo/info.xml, so it is not an admin
# setting and no admin will ever be offered it.
#
# It is read here rather than in findling.config because that module is the home
# of the caps an operator may tune, and this is not one of them.
DELAY_VARIABLE = "FINDLING_ARTIFICIAL_DELAY_MS"

MILLISECONDS_PER_SECOND = 1000


class SnippetsRequest(BaseModel):
    """Request body of the excerpt call.

    The ceiling on the id list is the same number the candidate call accepts as
    its limit, and for the same reason: the provider never asks for more
    excerpts than it displays hits, so this only bounds a caller that has gone
    wrong. Two different numbers would be two places to change one decision.
    """

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    fileIds: list[int] = Field(max_length=SEARCH_LIMIT_MAX)
    # camelCase because the wire format belongs to the PHP side; see the same
    # field in findling.api.search for the whole reason.
    titleOnly: bool = False


class Snippet(BaseModel):
    """One excerpt: plain text, and the ranges inside it, counted in characters."""

    text: str
    highlights: list[tuple[int, int]] = Field(default_factory=list)


class SnippetsResponse(BaseModel):
    """File id to excerpt, and the keys are strings because JSON keys are.

    An id that was asked about and is not in here has no excerpt, which is a
    valid result rather than an error.
    """

    snippets: dict[str, Snippet]


def artificial_delay_seconds() -> float:
    """How long this endpoint waits before it answers. Zero unless asked.

    Anything that is not a whole number of milliseconds falls back to zero, the
    same rule every other variable of this container follows: an unusable value
    degrades, it never stops anything.
    """
    raw = os.environ.get(DELAY_VARIABLE, "").strip()
    if not raw.isdigit():
        return 0.0
    return int(raw) / MILLISECONDS_PER_SECOND


def excerpts(uid: str, text: str, file_ids: list[int], title_only: bool) -> list[index_search.SnippetText]:
    """Cut the excerpts this user is permitted to see. Runs in a worker thread.

    Synchronous and called through ``asyncio.to_thread`` for the same reason the
    candidate search is: a long commit of the poller would otherwise stall the
    event loop, and a stalled loop is a container that stops answering while its
    own log looks healthy.

    Every failure ends in an empty list. A hit without an excerpt is still a hit,
    the subline falls back to the path on the PHP side, and that is a far better
    outcome than an exception that costs the user the whole search.
    """
    try:
        side = resources.read_side()
        if side is None:
            return []
        rewritten = build_query(side.index, text, title_only=title_only)
        if rewritten.query is None:
            return []
        # The permission prefilter is the first action inside this call, and it
        # is not redundant here; see the module docstring for why.
        return index_search.snippets_for(side.index, side.store, uid, rewritten.query, file_ids)
    # Deliberately every exception, for the reason in the docstring above.
    except Exception as error:
        # The type name and nothing else: a traceback carries whatever a library
        # put into its message, and here that would be document text.
        LOGGER.warning("cutting the excerpts ended in an unexpected %s", type(error).__name__)
        return []


@ROUTER.post("/snippets")
async def snippets(
    body: SnippetsRequest,
    nc: Annotated[AsyncNextcloudApp, Depends(anc_app)],
) -> SnippetsResponse:
    """Answer with one excerpt per confirmed file id, and with nothing else."""
    user_id = await current_user_id(nc)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no user in the AppAPI header")

    # Before the work, so that the measurement holds for every answer this
    # endpoint gives, including the empty ones.
    await asyncio.sleep(artificial_delay_seconds())

    cut = await asyncio.to_thread(excerpts, user_id, body.query.strip(), body.fileIds, body.titleOnly)
    return SnippetsResponse(
        snippets={str(one.file_id): Snippet(text=one.text, highlights=one.highlights) for one in cut}
    )
