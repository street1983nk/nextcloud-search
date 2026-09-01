"""Text out of a scan, with four caps deciding when a long document becomes a part.

The engine runs as a child process and not as a library binding, and that is not
a matter of taste. A binding that dies takes the extraction child with it, and
the ``setsid`` and ``killpg`` construction phase 2 built for exactly this moment
would lose its purpose: it exists so that a hung grandchild can be ended without
ending the process that owns the worker slot.

Input and output travel over stdin and stdout, which is what the two dashes in
the call are. That saves one file of user content on disk per page and, with it,
a whole class of cleanup mistakes on the error path, where cleanup is forgotten.

**The cap cascade, and why its order is the whole statement.** Three caps end the
page loop and keep what was read, two end the job:

* pages per document, and the verdict is ``indexed(truncated)``
* seconds per page, enforced by the child process call; the page is dropped and
  the loop goes on, and only if every page went that way is it ``failed(timeout)``
* the soft overall deadline, checked before each page, again ``indexed(truncated)``
* the hard deadline of the parent and ``RLIMIT_AS`` sit outside this module

D-08 is the reason for the split: the first pages searchable beats nothing
searchable, and a partial result is visible as such rather than quietly thin. The
numbers themselves are in :mod:`findling.config`, measured, with the full table
and the measurement protocol in ``docs/ocr.md``.

**What is deliberately not in here.** No decision about whether a file belongs in
the OCR track: that is made where the text layer is measured, in
:mod:`findling.extract.pdf`. No ``ocr_used`` flag either; the verdict is what this
module produces, and recording that OCR was spent on a file is the caller's job.

Like every module of this package, this one never writes: the engine answers on a
pipe, no page is ever put on disk, and the original file is not touched even on
the error path (IDX-07, T-03-805).
"""

from __future__ import annotations

import os
import subprocess
import time
from typing import Final

import pypdfium2

from findling import config
from findling.config import Settings
from findling.extract import raster
from findling.extract.dispatch import cap_text
from findling.extract.errors import ExtractionOutcome, Reason

# The binary, by name and not by path. Which directory it lives in is a property
# of the image and of the distribution, and a hard coded path would make the
# honest ocr_unavailable verdict below depend on that path staying true.
_ENGINE: Final = "tesseract"

# The call form of docs/ocr.md, measured in the shipping image on 2026-09-01.
# The two dashes are stdin and stdout. --oem 1 is LSTM only and is set explicitly
# although the Debian language data carry nothing else: --oem 3 means "take what
# is there", which is the same thing right up to the day somebody adds a legacy
# model, and then the recognition quality of every scanned document shifts with
# nothing in any diff. The last pair switches the second pass over an inverted
# page off, which the tesseract FAQ names as extra speed.
_ENGINE_OPTIONS: Final = ("--oem", "1", "--psm", "3", "-c", "tessedit_do_invert=0")

# What one thread is worth, and it is not a tuning knob. Measured: one thread is
# 18 percent faster than the default on twelve visible cores, and without this
# variable the very same page dies at 128 MB of address space with exit code 134,
# because OpenMP reserves a stack and an arena per thread and RLIMIT_AS counts
# virtual address space rather than resident memory. It is part of the memory
# guarantee (measurement 3 of docs/ocr.md).
_THREAD_LIMIT: Final = {"OMP_THREAD_LIMIT": "1"}

# Below this many characters the whole OCR run counts as having found nothing.
#
# The same number ``pdf._MIN_CHARS_PER_PAGE`` uses to decide that a page carries
# text, applied once to the finished document instead of to every page: a
# measured line of prose is 38 characters wide and a stamped "Seite 3 von 40" is
# 14. It is repeated here rather than imported, for two reasons. The unit is a
# different one, a document instead of a page, and importing the text extractor
# would pull pypdf into a child that is recycled every 200 files and does not
# otherwise need it.
_MIN_OCR_CHARS: Final = 25


class _PageTimeout(Exception):
    """One page did not finish inside its budget. Costs the page, not the job."""


class _EngineFailed(Exception):
    """The engine ended with a non zero code or was killed by a signal."""


class _EngineMissing(Exception):
    """There is no engine in this image, which is a different thing entirely."""


def extract_pdf_ocr(path: str) -> ExtractionOutcome:
    """The text of a scanned PDF, or the verdict that says why there is none.

    Defined at module level so it can be pickled into the extraction child, like
    ``pdf.extract_pdf``; a closure or a method would not survive the process
    boundary of plan 02-05.

    Every exception this branch knows is turned into a verdict here, in one
    place, and nothing else is caught: an exception nobody predicted belongs to
    ``ExtractionOutcome.from_exception`` at the process boundary, where it becomes
    ``failed(corrupt)`` rather than a guess made twice.
    """
    resolved = config.settings()
    try:
        document = pypdfium2.PdfDocument(path)
    except pypdfium2.PdfiumError:
        return ExtractionOutcome.failed(Reason.CORRUPT)

    try:
        return _read_document(document, resolved)
    except _EngineMissing:
        # Its own verdict, because "this image has no OCR" and "this document
        # beat the parser" call for entirely different answers from an admin.
        return ExtractionOutcome.failed(Reason.OCR_UNAVAILABLE)
    except _EngineFailed:
        # Includes the death by signal that an exhausted address space produces:
        # the grandchild asked for the memory, so no MemoryError ever arrives in
        # this process and the recycling rule for it never fires (pitfall 10).
        return ExtractionOutcome.failed(Reason.OCR_FAILED)
    except pypdfium2.PdfiumError:
        return ExtractionOutcome.failed(Reason.CORRUPT)
    finally:
        document.close()


def _read_document(document: pypdfium2.PdfDocument, resolved: Settings) -> ExtractionOutcome:
    """Walk the pages under all three soft caps and collect what came back."""
    page_count = len(document)
    read_pages = min(page_count, resolved.ocr_max_pages)
    deadline = time.monotonic() + resolved.ocr_job_seconds
    languages = "+".join(resolved.ocr_languages)

    parts: list[str] = []
    attempted = 0
    lost = 0
    cut = page_count > read_pages

    for number in range(read_pages):
        if time.monotonic() >= deadline:
            # The soft deadline of the child. It sits strictly below the hard one
            # of the parent, and the distance between them is the window in which
            # the text collected so far is pushed through the pipe.
            cut = True
            break
        png = raster.render_page_png(document, number, dpi=resolved.ocr_dpi)
        attempted += 1
        try:
            parts.append(_read_page(png, languages, resolved.ocr_page_seconds))
        except _PageTimeout:
            lost += 1

    if attempted > 0 and lost == attempted:
        # Not a thin document: nothing was read at all, and that is a failure.
        return ExtractionOutcome.failed(Reason.TIMEOUT)
    return _verdict("\n".join(parts), truncated=cut)


def _read_page(png: bytes, languages: str, seconds: int) -> str:
    """One page through the engine, as an argument list and never through a shell.

    The language list has passed the allowlist of installed languages in the
    configuration before it gets here, so no argument of this call can start with
    a dash that the engine would read as an option (T-03-801).

    ``stderr`` is collected and dropped, never logged. Tesseract writes file names
    and content related warnings there, and the log of this project carries
    counters and reason codes, nothing else (T-02-107).
    """
    # The inherited environment plus the one variable, rather than an environment
    # built from scratch: PATH and TESSDATA_PREFIX decide whether the engine is
    # found and whether it sees its language data. The extraction child has
    # already shed the Nextcloud credentials, so there is nothing here that a
    # grandchild could spend.
    environment = {**os.environ, **_THREAD_LIMIT}
    try:
        finished = subprocess.run(  # noqa: S603 - an argument list, never a shell
            [_ENGINE, "-", "-", "-l", languages, *_ENGINE_OPTIONS],
            input=png,
            capture_output=True,
            timeout=seconds,
            env=environment,
            check=False,
        )
    except subprocess.TimeoutExpired as expired:
        raise _PageTimeout from expired
    except FileNotFoundError as absent:
        raise _EngineMissing from absent

    if finished.returncode != 0:
        # Whatever ended page one ends page two as well, so this stops the job
        # instead of spending the remaining budget on the same wall.
        raise _EngineFailed
    return finished.stdout.decode("utf-8", errors="replace")


def _verdict(text: str, *, truncated: bool) -> ExtractionOutcome:
    """Turn the collected text into a verdict, with the character cap applied.

    A run that produced almost nothing is ``skipped(empty_text)`` and not a
    failure: the engine did its work, the page simply carried no readable text.
    The caller records that OCR was spent on the file, so the two together say how
    much time went into a document that is not in the index.
    """
    if len(text.strip()) < _MIN_OCR_CHARS:
        return ExtractionOutcome.skipped(Reason.EMPTY_TEXT)

    outcome = cap_text(text)
    if truncated and not outcome.truncated:
        # A cap that was reached is visible as one, whichever of them it was.
        return ExtractionOutcome.indexed(outcome.text, truncated=True)
    return outcome
