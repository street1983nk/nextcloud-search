"""The allowlist, the caps, and the map from a mimetype to an extractor.

This module answers one question before a single byte of a document is read: do
we touch this file at all, and if so, with which library. Everything a parser
never sees is a class of bugs that cannot happen, so the list is an allowlist and
never a blocklist. An unknown type is not supported, full stop.

What is deliberately absent, and why:

* Moving pictures and sound carry no text. There is nothing to index and nothing
  a text extractor could do except waste a process slot.
* Archive formats other than ZIP are not opened at all. Since plan 31-10 a ZIP
  file is read (FMT-02), by archive.py and never unpacked to disk: its central
  directory is counted before ZipFile sees it, one budget holds over every
  nesting level, and no member is sent to OCR. 7z, rar, tar and gz would each
  be a parser of their own for the same path traversal and decompression bomb
  questions, and no decision opened them.
* Pictures need OCR to mean anything, and since plan 03-09 that path exists:
  ``Route.OCR`` hands a page to the engine and comes back with text or with a
  verdict that says why there is none. There are two ways onto that route and
  they are different in kind. A scanned PDF gets there through the kind of its
  job, because a second attempt at the same file is a property of the order and
  not of the file. The picture formats of D-05 get there through this table,
  because being a picture is a property of the file and nothing else. Which
  decoder opens it is therefore read off the mimetype: pdfium for a document,
  Pillow for a picture. Since plan 31-10 HEIC and HEIF are two of the picture
  formats (FMT-05); BMP and GIF are not, and the reason is written down in both
  allowlists rather than in one.
* Word and Excel 97 to 2003 (extensions doc and xls) are read since plan 31-10
  (FMT-03, FMT-04), by olefile and xlrd in the sandbox child and without a
  headless office suite. The PowerPoint format before 2007 (ppt) has no reader
  and lands as skipped(mime_not_allowed), because documented non support is
  more honest than a shaky crutch.

The size cap is checked here for the second time. The PHP crawl enforces it when
a file is queued, which is the cheap place, and this is the line that still holds
on the day somebody raises the cap on one side only.

Like every module of this package, this one imports the standard library and the
sibling modules of the extraction path only. The analysis half of Findling, with
its 23 MB automaton, has no business in the extraction child.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Final

from findling import config
from findling.extract.errors import ExtractionOutcome, Reason


class Route(StrEnum):
    """The extractor a file is handed to once it passed the allowlist."""

    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    ODF = "odf"
    HTML = "html"
    RTF = "rtf"
    PLAIN = "plain"
    # The fourth kind of branch, and the only one that is reached in two ways:
    # by the kind of the job, for a scanned PDF that the text pass handed over,
    # and by the mimetype, for the picture formats below. The first of the
    # two is why there is no pseudo mimetype for scans: it would make every
    # reader of the table believe Nextcloud can hand one over, and judge would
    # have to know about job kinds to keep it out. A picture is not that case,
    # it really does arrive with a type of its own.
    OCR = "ocr"
    # The four document routes of 1.5 (plan 31-10). Each one has a reader of its
    # own: mail.py (31-04), archive.py (31-08), legacy_doc.py (31-05) and
    # legacy_xls.py (31-06).
    MAIL = "mail"
    ZIP = "zip"
    DOC = "doc"
    XLS = "xls"


# The picture formats of D-05, kept as a set of their own because two places need
# them: the allowlist below, and the branch that decides which decoder opens the
# file. Six in, two deliberately out.
#
# In, and why these: JPEG is what a phone upload is, PNG is what a screenshot and
# most exported notices are, TIFF is what a scanner and a fax gateway write, and
# WebP is what a browser saves today. All four are read by the Pillow and the
# leptonica of this image, measured, with the WebP result written up as
# measurement 4 of docs/ocr.md. HEIC and HEIF are what an iPhone camera writes;
# they joined with plan 31-10, read by pillow-heif in the sandbox child (plan
# 31-07, measured in docs/measurements/2026-10-formate-v15).
#
# The two that stay outside, and why, are part of the paragraph above the
# allowlist below, which stands identically next to the PHP list, because a
# decision that is readable in one place only is a decision the other place will
# undo.
IMAGE_MIMETYPES: Final[frozenset[str]] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/webp",
        "image/heic",
        "image/heif",
    }
)


# The allowlist. Nextcloud hands the mimetype over with the queue entry, so this
# is the type the server determined, not one we guessed from a file name.
#
# Since 1.5 (plan 31-10) the allowlist reads five more kinds of file. A mail
# (message/rfc822) gives its subject, its senders and recipients, its text part
# and the names of its attachments, never their content. A ZIP file
# (application/zip) gives the text of its members, without OCR inside the
# archive and inside limits that are counted before the archive is opened. Word
# and Excel 97 to 2003 (application/msword, application/vnd.ms-excel) are read
# by olefile and xlrd in the sandbox child, without a headless office suite.
# HEIC and HEIF photos (image/heic, image/heif) are decoded by pillow-heif in the
# same child and go to OCR like the other pictures. What stays outside, and why:
# BMP and GIF carry documents essentially never, so a further decoder that a
# picture from a stranger's phone gets to reach would be bought for nothing; the
# PowerPoint format before 2007 has no reader; further archive formats (7z, rar,
# tar, gz) and Outlook .msg files would each be a parser of its own that no
# decision opened. This paragraph stands identically next to both lists, and
# backend/tests/test_allowlist_parity.py compares the two.
ALLOWED_MIMETYPES: Final[Mapping[str, Route]] = {
    "application/pdf": Route.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": Route.DOCX,
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": Route.PPTX,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": Route.XLSX,
    "application/vnd.oasis.opendocument.text": Route.ODF,
    "application/vnd.oasis.opendocument.spreadsheet": Route.ODF,
    "application/vnd.oasis.opendocument.presentation": Route.ODF,
    "text/html": Route.HTML,
    "application/xhtml+xml": Route.HTML,
    "application/rtf": Route.RTF,
    "text/rtf": Route.RTF,
    "text/plain": Route.PLAIN,
    "text/markdown": Route.PLAIN,
    "text/csv": Route.PLAIN,
    "message/rfc822": Route.MAIL,
    "application/zip": Route.ZIP,
    "application/msword": Route.DOC,
    "application/vnd.ms-excel": Route.XLS,
    # Spread rather than written out again, so that the set above stays the one
    # place the six types are named. Two literal lists would be the same drift
    # this file already warns about, one file further in.
    **dict.fromkeys(IMAGE_MIMETYPES, Route.OCR),
}


def judge(mime: str, size: int) -> Route | ExtractionOutcome:
    """Decide before the first byte: a route to follow, or a finished verdict.

    The order is meaning, not taste. The type comes first because it says what a
    file is, and a large film should be reported as an unsupported type rather
    than as an oversized document. Emptiness comes before the size cap because a
    zero byte file is a failure and not a decision.
    """
    route = ALLOWED_MIMETYPES.get(mime)
    if route is None:
        return ExtractionOutcome.skipped(Reason.MIME_NOT_ALLOWED)
    if size <= 0:
        return ExtractionOutcome.failed(Reason.EMPTY_FILE)
    if size > config.settings().max_file_bytes:
        return ExtractionOutcome.skipped(Reason.TOO_LARGE)
    return route


def cap_text(text: str, *, member_marks: bool = False) -> ExtractionOutcome:
    """Turn a raw extracted string into a verdict, with the character cap applied.

    The single place where extracted text becomes an outcome, for two reasons.
    The cap is one of them: the 50 MB file limit says nothing about how much text
    is inside, and a handful of long PDFs will otherwise fill the volume the
    user's own data lives on (pitfall 12). A cut is not silent, it becomes
    indexed(truncated).

    The other reason is emptiness. Every extractor can come back with nothing,
    and skipped(empty_text) is the honest state for that. Whitespace counts as
    nothing; an index entry consisting of three line breaks helps no one.

    ARCHIVE_MEMBER_MARK (U+001C) is removed from every text here, unless
    ``member_marks`` is set, and only the ZIP reader sets it (plan 31-09,
    finding 15). The excerpt code reads the line after the last mark as the
    name of an inner file; a text file that carried the character itself would
    otherwise put a line of its own text in that place. Because this is the one
    place every extractor passes, no format can forget it.
    """
    if not member_marks:
        text = text.replace(config.ARCHIVE_MEMBER_MARK, "")
    if not text.strip():
        return ExtractionOutcome.skipped(Reason.EMPTY_TEXT)
    cap = config.settings().max_text_chars
    if len(text) > cap:
        return ExtractionOutcome.indexed(text[:cap], truncated=True)
    return ExtractionOutcome.indexed(text)


def extension_of(name: str) -> str:
    """The lowercase suffix of a file name without its dot, empty when there is none.

    Feeds the ``ext`` field of the index, which is what the file type filter of
    SRCH-03 searches on. A dot file without a suffix has no extension: the
    leading dot of ``.gitignore`` starts a name, it does not end one.
    """
    return PurePosixPath(name).suffix.removeprefix(".").lower()


def extract(path: str, mime: str, size: int, route: Route | None = None) -> ExtractionOutcome:
    """Judge a file and, if it passed, run its extractor. Called in the child.

    Raises whatever the extraction library raises. The translation into a verdict
    happens once, in ExtractionOutcome.from_exception, at the process boundary, so
    that no format module has to know the taxonomy.

    ``route`` is how a job overrules the mimetype, and the OCR track is the one
    caller that does. It is cleaner than a pseudo mimetype for two reasons. A
    second track is a property of the order and not of the file, so a table that
    maps types to extractors is the wrong place to write it down; and judge stays
    exactly what it is, the one place that forms a verdict out of type and size,
    instead of growing a case for a type Nextcloud never sends.

    The size cap is not lost with the override, it has already been paid: an OCR
    job only exists because a content job for the same file went through judge
    and through the gateway, where a file that grew past the cap in the meantime
    becomes skipped(too_large) before a single byte is extracted.
    """
    if route is None:
        verdict = judge(mime, size)
        if isinstance(verdict, ExtractionOutcome):
            return verdict
        route = verdict
    return _run_route(route, path, mime)


def _run_route(route: Route, path: str, mime: str) -> ExtractionOutcome:
    """Hand the file to its extractor.

    The format module is imported here rather than at the top of this file, and
    that is deliberate: a plain text file then never pays for loading lxml and
    striprtf, and a child that only ever sees text never loads pypdf and pdfium
    either. In a process that is recycled every 200 files, an import that is not
    needed is an import paid over and over.

    Every route of the allowlist arrives at an extractor from here on. While the
    document formats were still missing, this function raised for them rather than
    reporting them as skipped, because a missing extractor was a hole in this
    container and not a property of the document. That guard is gone with plan
    02-08, and there is a test that walks the whole allowlist so it cannot be
    needed again unnoticed.
    """
    match route:
        case Route.PDF:
            from findling.extract import pdf

            return pdf.extract_pdf(path)
        case Route.OCR:
            # One route, two decoders, and the mimetype is what tells them apart.
            # The route says "this file has to be read as pixels"; whether those
            # pixels come out of pdfium or out of Pillow is a property of the
            # file, and the forced route of an OCR job carries the mimetype of
            # its scan along, so the same question answers both callers.
            #
            # Both imports stay inside the branch. ocr pulls raster and pdfium,
            # image pulls Pillow and ocr behind it, and a container that never
            # sees a scan or a picture would otherwise carry all of it in every
            # one of its children, which is what this deferral is about.
            if mime in IMAGE_MIMETYPES:
                from findling.extract import image

                return image.extract_image(path)

            from findling.extract import ocr

            return ocr.extract_pdf_ocr(path)
        case Route.ODF:
            from findling.extract import odf

            return odf.extract_odf(path)
        case Route.DOCX | Route.PPTX | Route.XLSX:
            return _run_ooxml_route(route, path)
        case Route.MAIL | Route.ZIP | Route.DOC | Route.XLS:
            return _run_format_of_1_5(route, path)
        case _:
            return _run_text_route(route, path)


def _run_ooxml_route(route: Route, path: str) -> ExtractionOutcome:
    """The three ZIP packages of the Office world, after the OLE sniff.

    A password protected Office document and an old binary one renamed to the
    new extension are compound files and not ZIP packages; they get their name
    here, before any ZIP reader can call them corrupt (D-29-08, issue #18). Only
    these three routes ask, because only their extensions are worn by such files.
    The sidecar skip does not belong here: this function never sees the path in
    Nextcloud, only the scratch file, and that check stands in the poller.

    Since 1.5 (plan 31-06) an old Word or Excel document under the new name is
    read, by the .doc and the .xls reader, whichever its streams say it is and
    whatever the route says (cfb.py). skipped(legacy_format) is left for
    PowerPoint and for the old binary files the sniff cannot place.
    """
    from findling.extract import cfb

    match cfb.ole_kind(path):
        case "encrypted":
            return ExtractionOutcome.skipped(Reason.ENCRYPTED)
        case "word":
            from findling.extract import legacy_doc

            return legacy_doc.extract_doc(path)
        case "excel":
            from findling.extract import legacy_xls

            return legacy_xls.extract_xls(path)
        case "legacy":
            return ExtractionOutcome.skipped(Reason.LEGACY_FORMAT)
        case None:
            pass

    from findling.extract import office

    match route:
        case Route.DOCX:
            return office.extract_docx(path)
        case Route.PPTX:
            return office.extract_pptx(path)
        case _:
            return office.extract_xlsx(path)


def _run_format_of_1_5(route: Route, path: str) -> ExtractionOutcome:
    """The four document routes of 1.5 (plan 31-10), each with its own reader.

    Imported in the branch like every other format module, so that a child that
    never sees a mail or an old Office file never loads olefile or xlrd. The two
    Office readers sniff the first bytes themselves: a .doc that is really RTF,
    HTML or a DOCX, and an .xls that is really XLSX, markup or text, goes to the
    reader of what it is.
    """
    match route:
        case Route.MAIL:
            from findling.extract import mail

            return mail.extract_eml(path)
        case Route.ZIP:
            from findling.extract import archive

            return archive.extract_zip(path)
        case Route.DOC:
            from findling.extract import legacy_doc

            return legacy_doc.extract_msword(path)
        case _:
            from findling.extract import legacy_xls

            return legacy_xls.extract_msexcel(path)


def _run_text_route(route: Route, path: str) -> ExtractionOutcome:
    """The three formats that need no container opened."""
    from findling.extract import text

    match route:
        case Route.PLAIN:
            return text.extract_plain(path)
        case Route.HTML:
            return text.extract_html(path)
        case _:
            return text.extract_rtf(path)
