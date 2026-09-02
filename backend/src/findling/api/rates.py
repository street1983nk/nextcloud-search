"""GET /rates: how fast this container is working right now, and nothing about what it read.

Phase 4 puts an estimate of the first index on the admin page, and this is the
measurement it stands on. The estimate deliberately does not predict from
constants. Every rate this project has measured comes from an amd64 laptop core,
the hardware target is an ARM box with slower cores, and the measuring run for it
is still outstanding: a prediction out of the amd64 numbers would be wrong by an
unknown factor on the machine that matters. An extrapolation from the running
pass does not need that factor at all, which is why this route reports what
happened in a window rather than what should happen per document.

Everything here is a number or a note. No file name, no location, no search term,
although the ``files`` table this counts over carries a path and a title for every
row. Each field of the answer is assigned by name below and the row is never
spread into the model, so a column added to that table cannot arrive on the wire
in the same commit that meant to add a counter (T-04-24).

Text documents and scanned ones are two rates and never one. A page of OCR was
measured at about two seconds while a page of text costs nothing measurable, so a
single combined figure would be wrong for every instance whose mix of documents
differs from the corpus it was measured on. The startup value below travels with
the answer for the same reason it is called a startup value: the page has to be
able to label the number it shows as measured or as assumed, and a constant kept
on the other side as well would be a second copy to keep in step.

The numbers come out of the state database through its read-only connection, and
the counting itself is one grouped query in the store. There is no second
counting logic in here and there is not going to be one.

A missing state database is not a server error. It is what an installation looks
like for the first few minutes, and the honest answer to it is zeros plus a line
saying so.

Who may ask. The route is declared with access level ADMIN in appinfo/info.xml,
and that is what the AppAPI proxy enforces. The path this app itself uses is
``PublicFunctions::exAppRequest``, which does not pass through that check, so the
effective protection is the admin-only PHP route in front of it. The access level
stays correct as defence in depth for the proxy route.
"""

import asyncio
import logging
import time

from fastapi import APIRouter
from pydantic import BaseModel

from findling.config import settings
from findling.store.repo import Store, index_bytes, open_read_only

LOGGER = logging.getLogger("findling.api.rates")

ROUTER = APIRouter()

# Both notes name a state of this container and never a location on disk.
NO_STATE_YET = "no state database yet, nothing has been measured"
STATE_UNREADABLE = "the state database exists but could not be opened"
NOTHING_INDEXED_YET = "no document is in the index yet, the size per document is measured once one is"

# The window an admin page may ask for, in seconds. A minute is the shortest span
# in which a rate means anything on a queue that works in batches, and a day is
# the longest one the index behind the query can serve cheaply. A value outside
# the range is clamped and never refused: a page asking for a window length does
# not need an error message for it (T-04-25).
WINDOW_SECONDS_MIN = 60
WINDOW_SECONDS_MAX = 86_400
WINDOW_SECONDS_DEFAULT = 3_600

SECONDS_PER_HOUR = 3_600

# The measured startup value, in milliseconds per OCR page: the median of a clean
# A4 page at 300 dpi with OMP_THREAD_LIMIT=1, on an amd64 laptop core, taken in
# the delivered image (docs/ocr.md, measurement 3). It is handed out so that the
# page can show a labelled number in its first minute, and it is labelled as a
# startup value because it is one: the ARM factor against amd64 is unknown, and a
# constant sold as a measurement is the failure this whole route avoids.
STARTUP_OCR_PAGE_MS = 1_984


class RatesResponse(BaseModel):
    """What this container finished in a window, and what it cost on disk.

    Every field defaults, so the answer for a container that has nothing yet is
    the same shape as the answer for one that has been running for a month. An
    output whose fields come and go cannot be read by a page that has to render
    both.
    """

    # Documents per hour, extrapolated from the window and nothing else. Two
    # rates and never one: see the module docstring.
    docsPerHourText: int = 0
    docsPerHourOcr: int = 0
    # The window the two rates above were counted over, after clamping. Echoed
    # back so that the page shows a rate whose basis it knows instead of the one
    # it happened to ask for.
    windowSeconds: int = 0
    # The measured cost of one document on disk, and the two numbers it comes
    # from, next to it rather than instead of it: a page that only got the
    # quotient could not tell a small index from an empty one.
    bytesPerDoc: int = 0
    docs: int = 0
    indexBytes: int = 0
    # The documented amd64 startup value, travelling with the measurement so that
    # the page does not have to keep a second copy of it.
    startupRateOcrMs: int = STARTUP_OCR_PAGE_MS
    note: str = ""


def _clamped(window_seconds: int) -> int:
    """The requested window brought into the range this route can serve."""
    return max(WINDOW_SECONDS_MIN, min(WINDOW_SECONDS_MAX, window_seconds))


def _per_hour(counted: int, window_seconds: int) -> int:
    """Documents per hour out of a count over a window, and 0 for an empty one.

    An empty window is an answer and not a failure: an instance whose first pass
    finished last week has no throughput right now, and the page falls back to
    its labelled startup value. Dividing by the window without this guard would
    still be safe, but a zero that arrives as a zero cannot become a rounding
    artefact of a very long window either.
    """
    if counted <= 0:
        return 0
    return counted * SECONDS_PER_HOUR // window_seconds


def _of(store: Store, window_seconds: int) -> RatesResponse:
    """Read every number out of one open state database.

    Every field is named. Nothing here spreads a row of ``files`` into the
    answer, however convenient that would be on the day somebody adds a column:
    that table carries ``path`` and ``title`` (T-04-24).
    """
    resolved = settings()
    counted = store.throughput(window_seconds, int(time.time()))
    _, documents = store.acl_totals()
    total_bytes = index_bytes(resolved.index_dir)

    return RatesResponse(
        docsPerHourText=_per_hour(counted["text"], window_seconds),
        docsPerHourOcr=_per_hour(counted["ocr"], window_seconds),
        windowSeconds=window_seconds,
        # Integer division on purpose. A fraction of a byte per document is
        # precision this figure does not have, and the page multiplies the value
        # by a file count where the difference disappears anyway.
        bytesPerDoc=total_bytes // documents if documents > 0 else 0,
        docs=documents,
        indexBytes=total_bytes,
        note="" if documents > 0 else NOTHING_INDEXED_YET,
    )


def _report(window_seconds: int) -> RatesResponse:
    """The throughput of this container. Runs in a worker thread, never raises.

    The whole function runs off the event loop, which is what lets it sum the
    size of the index directory: that walk grows with the number of segments and
    would otherwise stall every other request while an admin page polls
    (T-04-09).
    """
    resolved = settings()
    window_seconds = _clamped(window_seconds)
    empty = RatesResponse(windowSeconds=window_seconds)
    if not resolved.state_db.is_file():
        return empty.model_copy(update={"note": NO_STATE_YET})

    try:
        store = open_read_only(resolved.state_db)
    except OSError as error:
        LOGGER.warning("the state database could not be opened, an %s", type(error).__name__)
        return empty.model_copy(update={"note": STATE_UNREADABLE})

    try:
        return _of(store, window_seconds)
    finally:
        # Opened per call rather than kept: this route is asked by one admin
        # page, and a connection of its own is always current without a cache
        # anybody has to invalidate.
        store.close()


@ROUTER.get("/rates")
async def read_rates(windowSeconds: int = WINDOW_SECONDS_DEFAULT) -> RatesResponse:
    """Answer with the measured throughput and the measured size per document.

    The parameter is an ``int`` in the signature, so anything that is not a whole
    number is a 422 from FastAPI before this body runs. A number outside the
    range is a different case and is clamped in the report: a window length is
    not a request an admin page needs an error message for.
    """
    return await asyncio.to_thread(_report, windowSeconds)
