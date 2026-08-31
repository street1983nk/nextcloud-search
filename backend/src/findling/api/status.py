"""GET /status: what this container has done, counted, and nothing beyond that.

Phase 4 builds the admin page; this is where its numbers come from. Both halves
of that split are deliberate. The data has to exist now because it is produced by
the indexing this phase builds, and the display has to wait because a page is a
different piece of work from a counter.

Everything here is a number, a version mark or a flag. No file name, no location,
no search term, ever. An admin page is a place where such a value is easy to add
"just for support" and impossible to take back, and the counters this app exists
for say everything that is needed: how many documents were indexed, how many were
deliberately left out, and how many could not be read.

The numbers come out of the state database through its read-only connection.
There is no second counting logic in here and there is not going to be one: two
places that count the same rows agree on the day they are written.

A missing state database is not a server error. It is what an installation looks
like for the first few minutes, and the honest answer to it is zeros plus a line
saying so. This route is declared with access level ADMIN in appinfo/info.xml,
which is where that decision is enforced: how far the indexing has come is an
operator's business, not every user's, and the answer is the same for all of
them, so nothing here reads an identity.
"""

import asyncio
import logging

from fastapi import APIRouter
from pydantic import BaseModel

from findling.api import resources
from findling.config import settings
from findling.store.repo import Store, open_read_only

LOGGER = logging.getLogger("findling.api.status")

ROUTER = APIRouter()

# Both notes name a state of this container and never a location on disk.
NO_STATE_YET = "no state database yet, the first indexing pass has not finished"
STATE_UNREADABLE = "the state database exists but could not be opened"


class StatusResponse(BaseModel):
    """The operating state of one container.

    Every field defaults, so the answer for a container that has nothing yet is
    the same shape as the answer for one that has been running for a month. A
    status output whose fields come and go cannot be read by a page that has to
    render both.
    """

    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    aclRows: int = 0
    docs: int = 0
    indexVersion: int = 0
    analyzerVersion: int = 0
    wordlistHash: str = ""
    reindexRequired: bool = False
    lowDisk: bool = False
    note: str = ""


def _number(mark: str | None) -> int:
    """A version mark as a number, and 0 for the placeholder of an unnamed one.

    An index whose analyzer never identified itself carries the placeholder, and
    it shows up here as a zero next to ``reindexRequired`` being true, which
    together say exactly what happened.
    """
    if mark is None:
        return 0
    try:
        return int(mark)
    except ValueError:
        return 0


def _of(store: Store) -> StatusResponse:
    """Read every number out of one open state database."""
    counters = store.counts()
    rows, documents = store.acl_totals()
    marks = store.read_meta()
    return StatusResponse(
        indexed=counters.get("indexed", 0),
        skipped=counters.get("skipped", 0),
        failed=counters.get("failed", 0),
        aclRows=rows,
        docs=documents,
        indexVersion=_number(marks.get("index_version")),
        analyzerVersion=_number(marks.get("analyzer_version")),
        wordlistHash=marks.get("wordlist_hash", ""),
        # A drift means the index was built with a different tokenisation than
        # the one queries are parsed with, so hits vanish with nothing saying
        # why. Reported, never acted on: what follows is the poller's decision.
        reindexRequired=bool(resources.version_drift(store)),
        lowDisk=resources.low_disk(),
    )


def report() -> StatusResponse:
    """The state of this container. Runs in a worker thread, never raises."""
    resolved = settings()
    if not resolved.state_db.is_file():
        return StatusResponse(note=NO_STATE_YET, lowDisk=resources.low_disk())

    try:
        store = open_read_only(resolved.state_db)
    except OSError as error:
        LOGGER.warning("the state database could not be opened, an %s", type(error).__name__)
        return StatusResponse(note=STATE_UNREADABLE, lowDisk=resources.low_disk())

    try:
        return _of(store)
    finally:
        # Opened per call rather than kept: this route is asked rarely, by one
        # admin page, and a connection of its own is always current without a
        # cache anybody has to invalidate.
        store.close()


@ROUTER.get("/status")
async def read_status() -> StatusResponse:
    """Answer with the counters and the version marks of this container."""
    return await asyncio.to_thread(report)
