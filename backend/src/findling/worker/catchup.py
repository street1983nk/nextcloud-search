"""The one time catch-up after the upgrade to 1.5 (FMT-06, D-31-01, D-31-02).

Release 1.5 reads five more kinds of file: mails, ZIP files, Word and Excel 97
to 2003 and HEIC/HEIF photos, and since plan 31-06 Word and Excel containers
under an OOXML name as well. The release promises that the stock an instance
already has is found without an admin doing anything, and without a full
reindex. Two facts of 1.4.2 make that promise harder than it sounds
(31-RESEARCH, pattern 8, pitfalls 1 to 3):

* The new types never had a row in state.db. Crawl, listener and reconcile of
  the 1.4.2 companion filter by mimetype in their query, so a .eml, .zip, .doc,
  .xls or .heic never reached the queue and never reached this container. A
  walk over state.db alone finds none of them.
* A full crawl would find them, and it would also download every other file of
  the instance once more: the fast path compares the content hash only after
  the download (poller.py, ``_fetch_file`` then ``is_unchanged``). On a weak box
  that is days of work to find a few files.

**So the catch-up has two parts, under the meta key CATCHUP_MARK.**

Part A, this module, walks state.db in blocks and hands back, in bands of
REQUEUE_BAND, the rows 1.5 judges differently:

* skipped(legacy_format) that is not PowerPoint. Word and Excel under an OOXML
  name are read by content since 31-06; an old PowerPoint container stays
  legacy_format, so handing it back would be idle work.
* every row in the state skipped or failed whose type is one of the six new
  ones (NEW_MIMETYPES). They exist only from the mixed window in which a 1.5
  companion queued the new types in front of a 1.4.2 container, which stored
  mime_not_allowed against the etag (pitfall 3). Without this the reconcile
  would later read "known, same etag" and leave them for good.
* every row failed(repeatedly_stuck), once (D-31-02). The cause behind most of
  them, a stale file cache size, is fixed in 31-03 (POL-02); without a new etag
  such a file would never come back.

Indexed rows are never chosen, and nothing here writes a verdict, the index
generation or a vector mark: the handover is the requeue every other track
uses. After the last band the mark says CATCHUP_RECONCILE.

Part B is one reconcile cycle that the mark makes due at once
(worker/reconcile.py, ``_is_due``), only over metadata: file id, etag, size,
mimetype and time from the file list, compared against ``known_etags``. It
finds the files part A cannot see because they have no row: every file of a new
type, and every file Nextcloud wrote off as repeatedly_stuck after the last
1.4.2 cycle. That last group needs a rule of its own, because the ordinary
comparison writes such a file off here as well (review finding IN-03 of phase 3)
instead of handing it over; while the mark says CATCHUP_RECONCILE, ``_compare``
hands it over instead. The same cycle re-judges the files of the mixed window
"companion first" (31-02, docs/formats.md "Upgrade order"): this container holds
system_file, legacy_format or unsupported_variant, the Nextcloud row the 1.3
substitute out of SKIPPED_FALLBACK_WITHOUT_SIGNAL. Only then, and never as a
blanket rule. The quiet gate of the reconcile stays, so the cycle waits for an
empty queue, and the cycle runs once even where the admin switched the
reconcile off (main.py). After the first cycle that ran to its end under the
mark, the mark says CATCHUP_DONE and nothing of this ever runs again.

The poller starts part A only on generation 3 of the companion and only after
the re-check of 1.4 (RECHECK_MARK) is done: a 1.3.x stock gets that one first,
and a companion of generation 2 would refuse to store the new types at all.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import Final

from findling.extract.dispatch import extension_of
from findling.extract.errors import Reason, State
from findling.nc.queue import KIND_CONTENT, DocumentQueue
from findling.store.repo import CATCHUP_DONE, CATCHUP_MARK, CATCHUP_RECONCILE, RECHECK_MARK, Store
from findling.worker.recheck import RECHECK_DONE, resume_after
from findling.worker.reconcile import REQUEUE_BAND

LOGGER = logging.getLogger("findling.worker.catchup")

# How many rows one read of state.db takes, as in worker/recheck.py and for the
# same reason: the block bounds memory, the bands bound a request.
_SCAN_BLOCK: Final = 2000

# The six types the allowlist reads since 1.5 (plan 31-10). Written out rather
# than derived from the allowlist, because the allowlist does not say which of
# its types are new; a test holds them inside it.
NEW_MIMETYPES: Final[frozenset[str]] = frozenset(
    {
        "message/rfc822",
        "application/zip",
        "application/msword",
        "application/vnd.ms-excel",
        "image/heic",
        "image/heif",
    }
)

# The same six types by file name, for a row whose mimetype is empty. Nextcloud
# maps exactly these extensions onto them (mimetypemapping.dist.json, checked in
# 31-RESEARCH): dot and xlt are the templates of Word and Excel.
_NEW_EXTENSIONS: Final = frozenset({"eml", "zip", "doc", "dot", "xls", "xlt", "heic", "heif"})

# PowerPoint, by type and by name. An old PowerPoint container under .pptx stays
# legacy_format in 1.5 (31-06), so handing it back would cost a pass for the
# same verdict.
_POWERPOINT_MIMETYPES: Final = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-powerpoint",
    }
)
_POWERPOINT_EXTENSIONS: Final = frozenset({"pptx", "ppt", "pps", "ppsx", "pot", "potx"})

_NOT_INDEXED: Final = frozenset({State.SKIPPED.value, State.FAILED.value})


def _is_new_type(path: str, mime: str) -> bool:
    """One of the six types; the stored mimetype decides, the extension only without one."""
    if mime:
        return mime in NEW_MIMETYPES
    return extension_of(path) in _NEW_EXTENSIONS


def _is_powerpoint(path: str, mime: str) -> bool:
    """PowerPoint by type or, without a stored one, by name."""
    if mime:
        return mime in _POWERPOINT_MIMETYPES
    return extension_of(path) in _POWERPOINT_EXTENSIONS


def select_catchup_candidates(rows: Iterable[tuple[int, str, str | None, str, str]]) -> list[int]:
    """The file ids of one block that 1.5 judges differently, in the order read.

    Rows of file id, state, reason, path and mimetype (Store.catchup_scan). What
    is chosen and why stands in the module docstring. system_file and
    unsupported_variant are not chosen: state.db holds the right code already,
    and whether the Nextcloud row is wrong only part B can see.
    """
    chosen: list[int] = []
    for file_id, state, reason, path, mime in rows:
        if (
            (state == State.SKIPPED and reason == Reason.LEGACY_FORMAT and not _is_powerpoint(path, mime))
            or (state in _NOT_INDEXED and _is_new_type(path, mime))
            or (state == State.FAILED and reason == Reason.REPEATEDLY_STUCK)
        ):
            chosen.append(file_id)
    return chosen


async def catchup_step(store: Store, queue: DocumentQueue) -> bool:
    """Run part A to its end, or up to a band that did not arrive.

    True once part A is over: the mark then says CATCHUP_RECONCILE (part B is
    due) or CATCHUP_DONE, and a call changes nothing. False while the re-check
    of 1.4 is not done, or when a band failed; the cursor then stands behind the
    last band that arrived and the next call resumes there. Repeating a band is
    harmless: requeueAs refreshes the rows rather than duplicating them.
    """
    meta = await asyncio.to_thread(store.read_meta)
    if meta.get(RECHECK_MARK, "") != RECHECK_DONE:
        return False
    mark = meta.get(CATCHUP_MARK, "")
    if mark in (CATCHUP_RECONCILE, CATCHUP_DONE):
        return True

    # A value nobody could have written restarts at zero (L-31-01, recheck.py).
    after = resume_after(mark)
    handed = 0
    bands = 0
    while True:
        rows, last = await asyncio.to_thread(store.catchup_scan, after=after, limit=_SCAN_BLOCK)
        if last is None:
            break
        candidates = select_catchup_candidates(rows)
        for start in range(0, len(candidates), REQUEUE_BAND):
            band = candidates[start : start + REQUEUE_BAND]
            if not (await queue.requeue(band, kind=KIND_CONTENT)).ok:
                # Numbers only, never a path (T-02-56).
                LOGGER.warning(
                    "the catch-up after the upgrade could not hand %d files to the queue after %d bands, "
                    "trying again next round",
                    len(band),
                    bands,
                )
                return False
            bands += 1
            handed += len(band)
            await asyncio.to_thread(store.write_meta, CATCHUP_MARK, str(band[-1]))
        await asyncio.to_thread(store.write_meta, CATCHUP_MARK, str(last))
        after = last

    await asyncio.to_thread(store.write_meta, CATCHUP_MARK, CATCHUP_RECONCILE)
    LOGGER.info(
        "the catch-up after the upgrade handed %d files back in %d bands, one reconcile cycle follows",
        handed,
        bands,
    )
    return True


__all__ = ["NEW_MIMETYPES", "REQUEUE_BAND", "catchup_step", "select_catchup_candidates"]
