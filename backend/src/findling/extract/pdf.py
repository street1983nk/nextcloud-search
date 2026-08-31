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
which files it is even about. The threshold that separates the two cases carries
its own reasoning below, because it is the softest number in this module.

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

# Assumption A2 of the phase research, and the softest number here.
#
# The research proposes "under 100 characters in the whole document". That number
# cannot be used as written: the reference corpus file with a real text layer
# carries 63 characters, so a document wide threshold of 100 would file the one
# PDF the research itself calls indexed as an OCR candidate. The measured pair is
# 63 characters on one page against 0 characters on the scanned page, so any
# threshold between them separates the two.
#
# It is counted per page instead of per document, which is what the research names
# as the better shape: a PDF with one line of text on the cover and forty scanned
# pages behind it would pass a document wide threshold and would then never be
# OCR-ed. Twenty five characters is roughly one short line of text; a scanned page
# whose only text object is a stamped "Seite 3 von 40" stays below it and remains
# a candidate.
#
# The error is asymmetric, which is why the threshold sits high rather than low. A
# text PDF wrongly sent to OCR still ends up with its text in phase 3. A scan
# wrongly called indexed is never looked at again. Phase 3 adjusts this number
# with measurements against real documents; until then it is an assumption and
# says so.
_MIN_CHARS_PER_PAGE = 25


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
    if len(text.strip()) < _MIN_CHARS_PER_PAGE * max(read_pages, 1):
        # Deliberately not failed and not empty_text. This is the OCR queue.
        return ExtractionOutcome.skipped(Reason.NO_TEXT_LAYER)

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
