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

Phase 6 adds three values and none of them changes that line. ``chunks`` is a
count of passages, ``embedded`` is the boolean behind it, and ``origin`` is one
of four marks saying which half of the search found this document for one search
line. All three are numbers, flags or marks, and the offsets that would turn the
first two into a passage stay in the vector stock where the snippet route reads
them, behind the permission recheck.

``origin`` is the reason D-14 draws its line through this route rather than
through the search path. An origin mark is a statement about a search, and on
the search path it would be a fourth value about a document the PHP recheck has
not confirmed yet; the field set test of the candidate model goes red the day
somebody puts one there. Here it is an administrator asking about one file they
already named, admin side, and not once per hit. The key is absent when no
search line was given, and never null: a null would read as "this container
looked and found nothing", which is a different sentence from "nobody asked".

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

from findling.api import resources
from findling.config import settings
from findling.index.fusion import origins
from findling.index.search import SemanticSide, ranked_sides
from findling.query.rewrite import build_query
from findling.store.repo import open_read_only
from findling.store.vectors import VectorStoreError, open_vectors

LOGGER = logging.getLogger("findling.api.diagnose")

ROUTER = APIRouter()

# Names a state of this container and never a location on disk, like the two
# notes of the status route.
NOT_JUDGED = "this container has no verdict for that file"

# The fourth answer to "where did this hit come from", next to the three marks
# of findling.index.fusion. It lives here and not over there because it is not
# an origin: that module answers about the documents its two lists hold, and
# this is the name of a document standing in neither of them. For an admin it is
# the most informative of the four, because it is the one they are looking at
# when a file they expected is missing from a result list.
NO_ORIGIN = "none"


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
    # The second track for this one file. Both default like everything above,
    # so a container without a vector stock answers the same shape: false and
    # nought are the truth about such a container and not a missing value.
    embedded: bool = False
    chunks: int = 0
    # The one field of this model that is allowed to be absent, and the route
    # below is declared with exclude_none so that it really is. Null is not used
    # as a value anywhere on this model, so nothing else can disappear with it.
    origin: str | None = None
    note: str = ""


def _second_track(file_id: int) -> tuple[bool, int]:
    """How many passages of one document carry a vector. Never raises.

    The same shape and the same reasoning as ``status._embedded`` one file over:
    ``read_only=True`` refuses a missing stock rather than creating an empty one,
    and every way of not being able to read it ends in the honest pair (False, 0)
    rather than in a 500. A stock that is gone costs two fields of this answer
    and none of the verdict below it (review finding WR-01).

    ``chunks_of`` answers with the spans of a document and this function counts
    them and drops them. It is the read back the delete path uses, so the count
    comes out of the one place that knows rather than out of a second column
    somewhere that would agree with it until the first lost write.
    """
    resolved = settings()
    if not resolved.vectors_db.is_file():
        return (False, 0)

    try:
        vectors = open_vectors(resolved.vectors_db, read_only=True)
    except (OSError, sqlite3.Error, VectorStoreError) as error:
        LOGGER.warning("the vector database could not be opened, an %s", type(error).__name__)
        return (False, 0)

    try:
        spans = vectors.chunks_of([file_id])
    except sqlite3.Error as error:
        LOGGER.warning("the vector database could not be read, an %s", type(error).__name__)
        return (False, 0)
    finally:
        vectors.close()

    total = len(spans.get(file_id, []))
    return (total > 0, total)


def _origin_of(file_id: int, text: str) -> str | None:
    """Which half of the search found this document for this line, or None.

    The two lists come from :func:`findling.index.search.ranked_sides`, which is
    the same function a candidate round builds its own two lists with. That is
    the point of asking it rather than ranking again in here: a second way of
    producing either list would answer this question about a search this
    container never ran, and the answer would look right most of the time.

    No permission prefilter is asked, and the reason is the whole of D-14. This
    route is an administrator asking about one file they already named, it runs
    admin side and not once per hit, and the answer says which list a document
    stood in rather than anything about its content. The search path gets none
    of this: a candidate carries three values and no fourth, because a fourth
    would be a statement about a document the PHP recheck has not confirmed yet
    (T-06-30, T-06-43).

    None on every failure and on a line that held no searchable word, because
    the absence of the field says "this container cannot answer that" while a
    mark would be a claim. The log line carries the type name and nothing else:
    the search line is user content and a library message quotes what it read
    (T-06-27).
    """
    try:
        side = resources.read_side()
        if side is None:
            return None
        rewritten = build_query(side.index, text, title_only=False)
        if rewritten.query is None:
            # A line that held only a file type filter, for instance. No search
            # ran, so there is no origin, and nought found is not the answer.
            return None
        semantic = None
        if side.vectors is not None and settings().embed_enabled:
            semantic = SemanticSide(vectors=side.vectors, model=resources.query_model(), text=text)
        sides = ranked_sides(side.index, rewritten.query, semantic=semantic)
    # Deliberately every exception: this route answers with a state and never
    # with an error, which the docstring of _report promises for the whole call.
    except Exception as error:
        LOGGER.warning("the origin of a document could not be worked out, an unexpected %s", type(error).__name__)
        return None

    return origins(sides.lexical, sides.semantic).get(file_id, NO_ORIGIN)


def _report(file_id: int, query: str) -> DiagnoseResponse:
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
    if file_id <= 0:
        return DiagnoseResponse(fileId=file_id, note=NOT_JUDGED)

    # Asked before the state database and independently of it, because the two
    # live in two files: a verdict that cannot be read says nothing about the
    # vectors of that document, and the second track of an instance whose state
    # database is broken is still worth reporting.
    embedded, chunks = _second_track(file_id)
    answer = DiagnoseResponse(
        fileId=file_id,
        embedded=embedded,
        chunks=chunks,
        origin=_origin_of(file_id, query) if query else None,
    )

    if not resolved.state_db.is_file():
        return answer.model_copy(update={"note": NOT_JUDGED})

    # sqlite3.Error is caught next to OSError on both the open and the read, for
    # the reason written at status.report(): a non-database file fails the first
    # PRAGMA and a zero byte state.db fails the first query, and both have to be
    # the no-verdict answer rather than a 500, or the docstring above would lie
    # about never raising (review finding WR-01).
    try:
        store = open_read_only(resolved.state_db)
    except (OSError, sqlite3.Error) as error:
        LOGGER.warning("the state database could not be opened, an %s", type(error).__name__)
        return answer.model_copy(update={"note": NOT_JUDGED})

    try:
        row = store.file_row(file_id)
    except sqlite3.Error as error:
        LOGGER.warning("the state database could not be read, an %s", type(error).__name__)
        return answer.model_copy(update={"note": NOT_JUDGED})
    finally:
        # Opened per call rather than kept: this route is asked by one admin who
        # typed something into a field, and a connection of its own is always
        # current without a cache anybody has to invalidate.
        store.close()

    if row is None:
        return answer.model_copy(update={"note": NOT_JUDGED})

    # Field by field and never a row spread into the model: the row carries path
    # and title, and a spread would put both on the wire the day somebody adds a
    # field to the table (T-04-40). The three values of the second track are
    # carried over one by one for the same reason, and because they come out of
    # another file entirely.
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
        embedded=answer.embedded,
        chunks=answer.chunks,
        origin=answer.origin,
    )


@ROUTER.get("/diagnose", response_model_exclude_none=True)
async def read_diagnosis(fileId: int, query: str = "") -> DiagnoseResponse:
    """Answer with the verdict of one file, by number, and where a hit came from.

    ``fileId`` is typed as an int, so FastAPI refuses anything else with a 422
    before the handler runs. The spelling follows the wire format of the other
    routes of this container rather than the naming rules of this language: the
    PHP side reads these names, and one field renamed on one side only is a value
    that silently arrives as nothing.

    ``query`` is optional and a line an admin left empty arrives as an empty
    string, so a blank one is no search at all: answering it with "neither half
    found it" would be a verdict about a search nobody ran.

    ``response_model_exclude_none`` is what makes the origin absent rather than
    null. It is safe to declare here because ``origin`` is the only field of the
    model that may be None; every other one defaults to a number, a flag or an
    empty string, so nothing else can disappear with it.
    """
    return await asyncio.to_thread(_report, fileId, query.strip())
