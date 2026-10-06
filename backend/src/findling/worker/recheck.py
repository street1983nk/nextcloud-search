"""The one time re-check of the old stock after the upgrade to 1.4.0 (D-29-10).

Release 1.4.0 fixes classes of files that 1.3.x judged wrongly: sidecars of
macOS and Office that ended as failed(corrupt) by the thousand (#18, #22), old
OLE containers under an OOXML extension, TIFF variants and large JPEGs that ran
out of memory. The release promised publicly that these are "re-checked after
the upgrade, no manual cleanup". A verdict sticks to the etag, and an unchanged
file is never read again on its own (``Store.is_unchanged`` only skips indexed
rows, so a failed row that is handed back really is extracted anew), which is
why the container hands them back itself, once.

**What is selected.** Living rows of failed(corrupt) and failed(out_of_memory),
skipped(system_file), skipped(legacy_format) and skipped(unsupported_variant),
and every living row whose base name is a sidecar name, whatever its verdict.
The three skipped codes are in the list although they are already right in
state.db: a companion older than 1.4.0 refused them, and the fallback of plan
29-01 stored skipped(mime_not_allowed) or skipped(image_not_ocrable) on the
PHP side instead. Handing them back once lets the 1.4.0 companion store the real
code. failed(ocr_failed) is deliberately not selected (Research Open Question
4): no fix of this release touches the engine, a second run would burn OCR time
for the same verdict.

**What it never does.** It does not raise the index generation and does not
touch the vector marks: that would forget every verdict, or every vector, of the
whole instance to fix a few classes of files (T-29-30). It opens no route of its
own; the handover is the requeue every other track uses (T-29-32).

**How it runs.** In bands of REQUEUE_BAND, below the list ceiling of the PHP
controller (T-29-29), with a cursor in the meta key RECHECK_MARK that moves only
after a band really reached the queue, judged on ``ok`` and never on ``count``
(bug audit M1 of plan 06.1-17). A restart resumes at the cursor, and after the
last band the mark says "done" and the run never comes back (T-29-31). The
poller starts it only once the companion announces VERDICTS_GENERATION (K6):
before that, the companion would only store the old codes again.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Final

from findling.extract.errors import Reason, State, is_sidecar_name
from findling.nc.queue import KIND_CONTENT, DocumentQueue
from findling.store.repo import RECHECK_MARK, Store
from findling.worker.reconcile import REQUEUE_BAND

LOGGER = logging.getLogger("findling.worker.recheck")

# The value of RECHECK_MARK once the sweep is over.
RECHECK_DONE: Final = "done"

# How many rows one read of state.db takes. Rows and not candidates: most rows
# of an instance are healthy documents, and the block bounds what one read holds
# in memory, while the bands below bound what one request carries.
_SCAN_BLOCK: Final = 2000

# The fix classes, as the store spells them. What stays out on purpose, and
# why, stands in the module docstring.
_RECHECK_FAILED: Final = frozenset({Reason.CORRUPT.value, Reason.OUT_OF_MEMORY.value})
_RECHECK_SKIPPED: Final = frozenset(
    {Reason.SYSTEM_FILE.value, Reason.LEGACY_FORMAT.value, Reason.UNSUPPORTED_VARIANT.value}
)


def select_candidates(rows: Iterable[tuple[int, str, str | None, str]]) -> list[int]:
    """The file ids of one block that belong to the fix classes, in the order read.

    A sidecar counts by its base name alone and in every state, because an
    indexed sidecar is exactly the case a 1.3 container left behind in the
    index; ``/.hidden`` and ``a._b`` are documents (is_sidecar_name).
    """
    chosen: list[int] = []
    for file_id, state, reason, path in rows:
        if (
            (state == State.FAILED and reason in _RECHECK_FAILED)
            or (state == State.SKIPPED and reason in _RECHECK_SKIPPED)
            or is_sidecar_name(PurePosixPath(path).name)
        ):
            chosen.append(file_id)
    return chosen


def _cursor(mark: str) -> int:
    """Where to resume. A value nobody could have written restarts at zero."""
    return int(mark) if mark.isdigit() else 0


async def recheck_step(store: Store, queue: DocumentQueue) -> bool:
    """Run the re-check to its end, or up to a band that did not arrive.

    True when the mark says "done" afterwards, False when a band failed; the
    cursor then stands behind the last band that arrived and the next call
    resumes there. Repeating a band is harmless: requeueAs refreshes the rows
    rather than duplicating them.
    """
    meta = await asyncio.to_thread(store.read_meta)
    mark = meta.get(RECHECK_MARK, "")
    if mark == RECHECK_DONE:
        return True

    after = _cursor(mark)
    handed = 0
    bands = 0
    while True:
        rows, last = await asyncio.to_thread(store.recheck_scan, after=after, limit=_SCAN_BLOCK)
        if last is None:
            break
        candidates = select_candidates(rows)
        for start in range(0, len(candidates), REQUEUE_BAND):
            band = candidates[start : start + REQUEUE_BAND]
            if not (await queue.requeue(band, kind=KIND_CONTENT)).ok:
                # Numbers only, never a path (T-02-56).
                LOGGER.warning(
                    "the re-check of the fix classes could not hand %d files to the queue after %d bands, "
                    "trying again next round",
                    len(band),
                    bands,
                )
                return False
            bands += 1
            handed += len(band)
            await asyncio.to_thread(store.write_meta, RECHECK_MARK, str(band[-1]))
        await asyncio.to_thread(store.write_meta, RECHECK_MARK, str(last))
        after = last

    await asyncio.to_thread(store.write_meta, RECHECK_MARK, RECHECK_DONE)
    LOGGER.info("re-checked %d files of the fix classes in %d bands", handed, bands)
    return True
