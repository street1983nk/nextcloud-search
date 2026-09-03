"""GET /diagnose: the verdict this container holds for one file, and nothing else.

Same contract as :mod:`findling.api.status`, one row narrower: the answer carries
the state, the reason code, whether OCR was used, when it was indexed, how many
attempts it took and whether a tombstone is on the row. It carries no path, no
title and no text, although the ``files`` table holds a path and a title for
every row. That is the whole point of D-03: the number travels, the name stays,
and the PHP side turns the number back into something a human can read, in the
permission model that owns that decision.

``textChars`` is the one figure that touches the content, and it is a count and
never the text. A snippet is file content and stays bound to SRCH-02, where it is
only ever built for a hit that already survived the permission recheck. Blurring
that line here is the way an administration tool turns into a content leak, so
there is no text field on this model and there is not going to be one.

``deletedAt`` is handed over as the number it is and is translated into no label
at all. A tombstone means "removed from the index" mechanically and something
else semantically: the clearing after an exclusion writes one for a file that
still lies untouched on disk. Only the Nextcloud side can tell the two apart,
because only it can see whether the file still has a cache entry, so the reading
of that number belongs over there and not in here (pitfall 6).

Declared with access level ADMIN in appinfo/info.xml, which guards the AppAPI
proxy path in ``ExAppProxyController::passesExAppProxyRouteAccessLevelCheck``.
The path this app actually uses is ``PublicFunctions::exAppRequest``, and that one
does not pass through the proxy's access level check: the effective guard there is
the admin-only PHP route in front of it. The access level stays declared as
defence in depth for the path this app does not walk (pitfall 10).
"""

import asyncio
import logging
import sqlite3

from fastapi import APIRouter
from pydantic import BaseModel

from findling.config import settings
from findling.store.repo import open_read_only

LOGGER = logging.getLogger("findling.api.diagnose")

ROUTER = APIRouter()

# Names a state of this container and never a location on disk, like the two
# notes of the status route.
NOT_JUDGED = "this container has no verdict for that file"


class DiagnoseResponse(BaseModel):
    """What one container knows about one file id.

    Every field defaults, so a file nobody judged answers with the same shape as
    one that has been indexed twice. ``state`` empty plus the note is the honest
    answer to "never seen".
    """

    fileId: int = 0
    state: str = ""
    reason: str = ""
    ocrUsed: bool = False
    indexedAt: int = 0
    attempts: int = 0
    textChars: int = 0
    deletedAt: int = 0
    indexVersion: int = 0
    note: str = ""


def _report(file_id: int) -> DiagnoseResponse:
    """The verdict of one file. Runs in a worker thread, never raises.

    A file id that cannot name a file, so nought or a negative number, is
    answered with the note rather than with an error: an admin page needs no
    error message for a number, and the answer to "is there a verdict for this"
    is no in both cases.

    A missing state database is the same answer for the same reason. It is what
    an installation looks like for the first few minutes, and a 500 there would
    send an admin looking for a defect that is a normal state.
    """
    resolved = settings()
    if file_id <= 0 or not resolved.state_db.is_file():
        return DiagnoseResponse(fileId=file_id, note=NOT_JUDGED)

    # sqlite3.Error is caught next to OSError on both the open and the read, for
    # the reason written at status.report(): a non-database file fails the first
    # PRAGMA and a zero byte state.db fails the first query, and both have to be
    # the no-verdict answer rather than a 500, or the docstring above would lie
    # about never raising (review finding WR-01).
    try:
        store = open_read_only(resolved.state_db)
    except (OSError, sqlite3.Error) as error:
        LOGGER.warning("the state database could not be opened, an %s", type(error).__name__)
        return DiagnoseResponse(fileId=file_id, note=NOT_JUDGED)

    try:
        row = store.file_row(file_id)
    except sqlite3.Error as error:
        LOGGER.warning("the state database could not be read, an %s", type(error).__name__)
        return DiagnoseResponse(fileId=file_id, note=NOT_JUDGED)
    finally:
        # Opened per call rather than kept: this route is asked by one admin who
        # typed something into a field, and a connection of its own is always
        # current without a cache anybody has to invalidate.
        store.close()

    if row is None:
        return DiagnoseResponse(fileId=file_id, note=NOT_JUDGED)

    # Field by field and never a row spread into the model: the row carries path
    # and title, and a spread would put both on the wire the day somebody adds a
    # field to the table (T-04-40).
    return DiagnoseResponse(
        fileId=file_id,
        state=str(row["state"]),
        reason="" if row["reason"] is None else str(row["reason"]),
        ocrUsed=bool(row["ocr_used"]),
        indexedAt=int(row["indexed_at"] or 0),
        attempts=int(row["attempts"] or 0),
        textChars=int(row["text_chars"] or 0),
        deletedAt=int(row["deleted_at"] or 0),
        indexVersion=int(row["index_version"] or 0),
    )


@ROUTER.get("/diagnose")
async def read_diagnosis(fileId: int) -> DiagnoseResponse:
    """Answer with the verdict of one file, by number.

    ``fileId`` is typed as an int, so FastAPI refuses anything else with a 422
    before the handler runs. The spelling follows the wire format of the other
    routes of this container rather than the naming rules of this language: the
    PHP side reads these names, and one field renamed on one side only is a value
    that silently arrives as nothing.
    """
    return await asyncio.to_thread(_report, fileId)
