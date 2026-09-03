"""GET /status: what this container has done, counted, and nothing beyond that.

Phase 4 builds the admin page, and this is where one half of its numbers comes
from. The split is deliberate and written out on both sides of it, because two
docstrings that each claim the whole page is how a page ends up reporting "no
errors" while a switched off container quietly answers nothing at all.

*From the Nextcloud side*, out of ``findling_file_state``: skipped, failed, the
reason codes behind them, and the per file error list. That is the half an admin
can still read when this container is off, which is exactly the moment they go
looking for it.

*From here*: indexed, indexed(truncated), the document count of the index, the
permission rows, the version marks, the space on the volume and the throughput.
Only this process sees the volume and the tantivy index, so nobody else can
count them.

Both views stay visible next to each other, each with its source named. A
difference between them is a diagnostic signal and not a defect of the page,
while a single number called "failed" without a source would hide precisely the
case that is worth seeing.

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
saying so. One value is handed out even then: ``maxFileBytes`` is read from the
environment and not from the database, and the page needs it to clamp its own
setting to the cap this container really enforces. An empty container is no
reason to show a setting that does not apply.

Who may ask. The route is declared with access level ADMIN in appinfo/info.xml,
and that is what the AppAPI proxy enforces, in
``ExAppProxyController::passesExAppProxyRouteAccessLevelCheck``. The path this
app itself uses is ``PublicFunctions::exAppRequest``, which does not go through
that check, so the effective protection of the admin page is its PHP route,
declared without ``NoAdminRequired``. The access level stays correct as defence
in depth for the proxy route. Either way nothing in here reads an identity: how
far the indexing has come is an operator's business, not every user's, and the
answer is the same for all of them.
"""

import asyncio
import logging
import sqlite3

from fastapi import APIRouter
from pydantic import BaseModel, Field

from findling.api import resources
from findling.config import settings
from findling.store.repo import Store, index_bytes, open_read_only

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
    # Contained in indexed above and never added next to it: a truncated
    # document is indexed, it is just indexed at the front only. D-08 of phase 3
    # asks for the number because "indexed" would otherwise be read as a promise
    # this container never made about the end of a long document.
    truncated: int = 0
    skipped: int = 0
    failed: int = 0
    # State to reason code to count, and the key for "no reason at all" is the
    # empty string. None is not a JSON object key, so normalising it here is what
    # keeps a page from having to guess which of two spellings it got. Declared
    # with a factory because a mutable default on a model is one object shared by
    # every instance of it.
    reasons: dict[str, dict[str, int]] = Field(default_factory=dict)
    aclRows: int = 0
    docs: int = 0
    indexVersion: int = 0
    analyzerVersion: int = 0
    wordlistHash: str = ""
    reindexRequired: bool = False
    lowDisk: bool = False
    # The three raw measurements the space estimate of the admin page is built
    # from, next to the flag above rather than instead of it: the flag carries a
    # threshold this container decided, these carry what the file system said.
    diskFreeBytes: int = 0
    diskTotalBytes: int = 0
    indexBytes: int = 0
    # The cap this container enforces a second time, after the PHP crawl already
    # enforced it. Reported so that the setting on the page can be clamped to it
    # instead of displaying a number that does not apply (pitfall 2).
    maxFileBytes: int = 0
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


def _named_reasons(breakdown: dict[str, dict[str | None, int]]) -> dict[str, dict[str, int]]:
    """The breakdown with the absent reason spelled as an empty string."""
    return {
        state: {("" if reason is None else reason): total for reason, total in per_state.items()}
        for state, per_state in breakdown.items()
    }


def _volume() -> StatusResponse:
    """Everything this container can say without opening the state database.

    Built as a whole answer rather than as four loose values, so the three
    branches of :func:`report` below add what they learned to it instead of
    repeating the volume part each time. Every one of these numbers comes from
    the environment or from the file system, which is why a container without a
    state database still reports them.
    """
    resolved = settings()
    free, total = resources.disk_bytes()
    return StatusResponse(
        lowDisk=resources.low_disk(),
        diskFreeBytes=free,
        diskTotalBytes=total,
        indexBytes=index_bytes(resolved.index_dir),
        maxFileBytes=resolved.max_file_bytes,
    )


def _of(store: Store, volume: StatusResponse) -> StatusResponse:
    """Read every number out of one open state database.

    Every field is named. Nothing here spreads a row of ``files`` into the
    answer, however convenient that would be on the day somebody adds a column:
    that table carries ``path`` and ``title``, and a spread would put both on the
    wire in the same commit that meant to add a counter (T-04-06).
    """
    counters = store.counts()
    breakdown = store.reasons_by_state()
    rows, documents = store.acl_totals()
    marks = store.read_meta()
    return StatusResponse(
        indexed=counters.get("indexed", 0),
        truncated=breakdown.get("indexed", {}).get("truncated", 0),
        skipped=counters.get("skipped", 0),
        failed=counters.get("failed", 0),
        reasons=_named_reasons(breakdown),
        aclRows=rows,
        docs=documents,
        indexVersion=_number(marks.get("index_version")),
        analyzerVersion=_number(marks.get("analyzer_version")),
        wordlistHash=marks.get("wordlist_hash", ""),
        # A drift means the index was built with a different tokenisation than
        # the one queries are parsed with, so hits vanish with nothing saying
        # why. Reported, never acted on: what follows is the poller's decision.
        reindexRequired=bool(resources.version_drift(store)),
        lowDisk=volume.lowDisk,
        diskFreeBytes=volume.diskFreeBytes,
        diskTotalBytes=volume.diskTotalBytes,
        indexBytes=volume.indexBytes,
        maxFileBytes=volume.maxFileBytes,
    )


def report() -> StatusResponse:
    """The state of this container. Runs in a worker thread, never raises.

    The whole function runs off the event loop, which is what lets it sum the
    size of the index directory: that walk grows with the number of segments and
    would otherwise stall every other request while an admin page polls
    (T-04-09).
    """
    resolved = settings()
    volume = _volume()
    if not resolved.state_db.is_file():
        return volume.model_copy(update={"note": NO_STATE_YET})

    # sqlite3.Error is caught next to OSError on both the open and the read,
    # because two realistic shapes of a broken state escape the open alone: a
    # file that is not a SQLite database raises DatabaseError from the first
    # PRAGMA, and a zero byte state.db, which a kill between connect and the
    # schema script leaves behind, opens cleanly and raises OperationalError on
    # the first query. Both are the same answer as an unreadable file: a state
    # of this container, never a 500 (review finding WR-01).
    try:
        store = open_read_only(resolved.state_db)
    except (OSError, sqlite3.Error) as error:
        LOGGER.warning("the state database could not be opened, an %s", type(error).__name__)
        return volume.model_copy(update={"note": STATE_UNREADABLE})

    try:
        return _of(store, volume)
    except sqlite3.Error as error:
        LOGGER.warning("the state database could not be read, an %s", type(error).__name__)
        return volume.model_copy(update={"note": STATE_UNREADABLE})
    finally:
        # Opened per call rather than kept: this route is asked rarely, by one
        # admin page, and a connection of its own is always current without a
        # cache anybody has to invalidate.
        store.close()


@ROUTER.get("/status")
async def read_status() -> StatusResponse:
    """Answer with the counters and the version marks of this container."""
    return await asyncio.to_thread(report)
