"""PDF text, with the encryption question answered before pdfium opens anything.

Two libraries, and the order between them is a decision rather than a habit.
pypdf is pure Python and answers whether a file is encrypted without touching a
single page; pypdfium2 wraps the PDF engine of Chrome and is the fast one. Asking
the cheap library first is what keeps a password protected document a deliberate
skipped(encrypted) instead of a failure: measured against the reference corpus,
``PdfReader(path)`` does not raise on such a file at all, the error only arrives
when the pages are read, and by then the verdict would already be the wrong one.

The second reason for this order is that pdfium is a C library. Everything it
hands out is a C resource, so every page and every text page is closed in a
``finally``. On a single document a missed close is invisible; over an initial
index of 100000 files inside a container with 4 GB of RAM it is a leak that ends
the process, and the error path is exactly where closing gets forgotten.

The third decision is the one that reaches furthest: a PDF without a text layer
is **not** a failure, it is skipped(no_text_layer). That verdict is the queue
phase 3 works through with OCR, and it has
to be recorded now, otherwise phase 3 needs a complete reindex just to find out
which files it is even about. The two numbers that separate the cases used to be
the softest thing in this module; since phase 3 they are measured over the whole
reference corpus, and the measurement stands at each of them.

The decision runs per page and then over the share of pages, never over the
document average. That is bug M2 of the phase 2 audit and pitfall 9 of the phase
3 research in one line of code: an average lets a cover page speak for nine
scanned ones, in whichever of the two directions the document happens to lean.

Like every module of this package, this one never writes: it opens documents for
reading, and the original file is not touched even on the error path (IDX-07).
"""

from __future__ import annotations

import pypdf
import pypdfium2
from pypdf.errors import EmptyFileError, PdfReadError

from findling import config
from findling.extract.dispatch import cap_text
from findling.extract.errors import ExtractionOutcome, Reason

# Measured on 2026-09-01 over the whole reference corpus, on the pypdfium2
# 5.13.0 of this lock file. The command line and the full table are in
# docs/ocr.md under "Die Textlayer-Erkennung"; the numbers are characters per
# page after strip():
#
#   14-pacht-mit-anhang.pdf   456, 442, 0, 0, 0   full A4 prose, then the annex
#   09-bescheid.pdf           123                 three short lines
#   01-text-layer.pdf          63                 two short lines
#   29-doppelt-komprimiert.pdf 29                 one line, the sparsest real one
#   31-riesenformat.pdf        12                 a headline and nothing else
#   13, 15, 16, 30 and the annex pages of 14: exactly 0 on every page
#
# So a rendered scan measures 0 and never something small: the separation is the
# whole range, and the corpus alone would allow any threshold between 1 and 12.
# The number therefore answers the question the corpus cannot: what does a page
# carry that is only a stamp? A measured prose line is 38 characters wide, a
# stamped "Seite 3 von 40" is 14, and the sparsest genuine text page measured is
# 29. Twenty five sits between those two, which is where it already sat as
# assumption A2; the assumption survives its measurement and stops being one.
#
# It stays low rather than high on purpose, and the reason flipped in phase 3. It
# used to be cheap to send a text PDF to OCR, because there was no OCR. From here
# on that mistake costs minutes of CPU per document on a 4 GB box, so the
# threshold errs towards "this page has text".
#
# Measured 2026-09-01 against 14-pacht-mit-anhang.pdf, 09-bescheid.pdf,
# 01-text-layer.pdf, 29-doppelt-komprimiert.pdf, 31-riesenformat.pdf and the nine
# rendered scan pages of 13, 15, 16, 30 and 14.
_MIN_CHARS_PER_PAGE = 25

# How much of a document may be scanned before the whole file is one.
#
# Counting per page is only half of the fix for bug M2 of the phase 2 audit; the
# other half is that a single page decides nothing. Two measured cases bracket
# this number: 14-pacht-mit-anhang.pdf is a readable agreement with three scanned
# annex pages behind two readable ones, 3 of 5 or 0.60, and it has to be
# extracted. A cover page in front of nine scans, 9 of 10 or 0.90, has to go to
# OCR. Two thirds is the value the phase research proposed, and it lies between
# the two.
#
# Exactly two thirds still counts as a document with a text layer: the comparison
# below is strictly greater, so 2 scanned pages out of 3 are extracted and 3 out
# of 4 are not.
_SCAN_PAGE_SHARE = 2 / 3


def extract_pdf(path: str) -> ExtractionOutcome:
    """The text of a PDF, or the verdict that says why there is none.

    Defined at module level so it can be pickled into the extraction child; a
    closure or a method would not survive the process boundary of plan 02-05.
    """
    try:
        reader = pypdf.PdfReader(path)
        protected = reader.is_encrypted
    except EmptyFileError:
        # A zero byte file. Its own reason, because "the parser choked" and "there
        # was nothing to parse" are different things on the status page.
        return ExtractionOutcome.failed(Reason.EMPTY_FILE)
    except PdfReadError:
        # PdfStreamError and the rest of the read errors are subclasses, so a
        # truncated or scrambled file lands here. EmptyFileError is a subclass as
        # well, which is why it is caught first.
        return ExtractionOutcome.failed(Reason.CORRUPT)

    if protected:
        return ExtractionOutcome.skipped(Reason.ENCRYPTED)

    cap = config.settings().max_pdf_pages
    try:
        document = pypdfium2.PdfDocument(path)
    except pypdfium2.PdfiumError:
        return ExtractionOutcome.failed(Reason.CORRUPT)

    try:
        page_count = len(document)
        read_pages = min(page_count, cap)
        parts = [_page_text(document, number) for number in range(read_pages)]
    except pypdfium2.PdfiumError:
        return ExtractionOutcome.failed(Reason.CORRUPT)
    finally:
        document.close()

    text = "\n".join(parts)
    scanned = sum(1 for part in parts if len(part.strip()) < _MIN_CHARS_PER_PAGE)
    if scanned / max(read_pages, 1) > _SCAN_PAGE_SHARE:
        # Deliberately not failed and not empty_text. This is the OCR queue, and
        # the text of the few readable pages is dropped here on purpose: OCR
        # reads those pages as well, so nothing is lost, and a file that arrived
        # in the OCR track carrying half its text already would make the later
        # verdict of that track meaningless.
        return ExtractionOutcome.skipped(Reason.NO_TEXT_LAYER)

    # Mixed, but under the share: the text is indexed and the scanned pages of
    # this document are not additionally OCR-ed in v1. One file has exactly one
    # verdict, and a second partial job per file would be a mechanism of its own,
    # with its own queue entry, its own retry counter and its own way of being
    # half done. The annex of an agreement is worth less than that machinery.

    outcome = cap_text(text)
    if page_count > cap:
        # The page cap cut the document just as the character cap would have, so
        # it produces the same visible state instead of a quiet half document.
        return ExtractionOutcome.indexed(outcome.text, truncated=True)
    return outcome


def _page_text(document: pypdfium2.PdfDocument, number: int) -> str:
    """One page of text, with both C objects released even when the page raises.

    The nesting is the point: whatever happens inside, the text page is closed
    before the page and the page is closed before the caller sees the exception.
    """
    page = document[number]
    try:
        textpage = page.get_textpage()
        try:
            return textpage.get_text_bounded()
        finally:
            textpage.close()
    finally:
        page.close()
