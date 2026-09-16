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

Since plan 06-08 there is a second way an excerpt can come about, and it hangs
on exactly the same check as the first one. A hit that only the vector branch
found has no literal overlap with the query, so the generator answers an empty
fragment and the user would see a hit without any preview; for such a hit the
text is cut out of the stored body between the two character offsets of the
chunk that matched (D-13). That cut happens inside ``snippets_for``, behind the
permission prefilter and behind the PHP recheck, which is why this route hands
over the raw search line and the vector stock and decides nothing itself.
"""

import asyncio
import logging
import os
from collections.abc import Sequence
from functools import partial
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from findling.api import resources
from findling.config import (
    SEARCH_LIMIT_MAX,
    SEARCH_MTIME_MAX,
    SEARCH_QUERY_MAX_CHARS,
    SEARCH_TYPE_GROUPS_MAX,
    settings,
)
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

    query: str = Field(min_length=1, max_length=SEARCH_QUERY_MAX_CHARS)
    fileIds: list[int] = Field(max_length=SEARCH_LIMIT_MAX)
    # camelCase because the wire format belongs to the PHP side; see the same
    # field in findling.api.search for the whole reason.
    titleOnly: bool = False
    # The three fields that touch the query builder, and they are here because
    # this call builds the very same query a second time. A field that reached
    # only one of the two models would be an extra field to the other, and
    # extra="forbid" answers that with a 422 that arrives in PHP as null: the
    # page would then show the error block instead of excerpts, for hits it had
    # already found. tests/test_search_fields_lockstep.py holds the two models
    # together for exactly that reason. Same value set and same bounds as in
    # findling.api.search, and the arguments for both stand over there.
    types: list[Literal["pdf", "documents", "spreadsheets", "presentations", "images", "text"]] = Field(
        default_factory=list, max_length=SEARCH_TYPE_GROUPS_MAX
    )
    since: int | None = Field(default=None, ge=0, le=SEARCH_MTIME_MAX)
    until: int | None = Field(default=None, ge=0, le=SEARCH_MTIME_MAX)
    # And there is deliberately no sort field. An excerpt call asks about named
    # fileIds and answers a mapping, so it has no order to change; a sort field
    # here would be a field that does nothing today and something at the next
    # rebuild. It is the one named entry in FIELDS_THAT_MAY_DIFFER of the
    # lockstep gate, so its absence is checked rather than merely intended.


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


def excerpts(
    uid: str,
    text: str,
    file_ids: list[int],
    title_only: bool,
    *,
    groups: Sequence[str] = (),
    since: int | None = None,
    until: int | None = None,
) -> list[index_search.SnippetText]:
    """Cut the excerpts this user is permitted to see. Runs in a worker thread.

    Synchronous and called through ``asyncio.to_thread`` for the same reason the
    candidate search is: a long commit of the poller would otherwise stall the
    event loop, and a stalled loop is a container that stops answering while its
    own log looks healthy.

    Every failure ends in an empty list. A hit without an excerpt is still a hit,
    the subline falls back to the path on the PHP side, and that is a far better
    outcome than an exception that costs the user the whole search.

    ``groups``, ``since`` and ``until`` travel through to the query builder, so
    the query an excerpt is cut against carries the same filter clause the
    candidate round was cut with. That is the whole of what this path needs: the
    clause sits inside the query the snippet generator is created from, and the
    second excerpt path never chooses a document, it only quotes ids the caller
    already had confirmed. A second cut over those ids would refuse an excerpt
    to a hit the search itself handed out.
    """
    try:
        side = resources.read_side()
        if side is None:
            return []
        rewritten = build_query(side.index, text, title_only=title_only, groups=groups, since=since, until=until)
        if rewritten.query is None:
            return []
        # The vector half, handed over as the same bundle the candidate round
        # takes. The raw line goes along because the model needs words and the
        # rewritten query is not text any more, and it is the line the user
        # typed rather than a stored one, so no log line of this module or of
        # snippets_for may carry it (T-06-39).
        #
        # The two rules of the search path (operators, one term) are not read
        # here, for the reason D-13 already gives the distance gate: this call
        # quotes documents the search has already handed out and the PHP side
        # has already confirmed. It chooses no candidate, so holding the vector
        # half back would take a confirmed hit its excerpt away and hand back
        # nothing in return. The rules decide who gets into the list; this
        # decides what the entry reads like.
        semantic = None
        if side.vectors is not None and settings().embed_enabled:
            semantic = index_search.SemanticSide(vectors=side.vectors, model=resources.query_model(), text=text)
        # The permission prefilter is the first action inside this call, and it
        # is not redundant here; see the module docstring for why. Both excerpt
        # paths lie behind it.
        return index_search.snippets_for(side.index, side.store, uid, rewritten.query, file_ids, semantic=semantic)
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

    cut = await asyncio.to_thread(
        partial(
            excerpts,
            user_id,
            body.query.strip(),
            body.fileIds,
            body.titleOnly,
            groups=body.types,
            since=body.since,
            until=body.until,
        )
    )
    return SnippetsResponse(
        snippets={str(one.file_id): Snippet(text=one.text, highlights=one.highlights) for one in cut}
    )
