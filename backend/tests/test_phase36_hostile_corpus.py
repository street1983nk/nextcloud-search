"""The hostile format corpus of phase 36 (D-36-01, D-36-02, D-36-17), run through the real sandbox.

Every file comes from a generator of hostile.py, built at test time and
written only into the temporary directory of its case; no hostile file lives
in the repository. Each case goes through ``ExtractionWorker``, the spawned
child with its deadline (and RLIMIT_AS on Linux), and asks for three things: a
verdict with a name, a living worker afterwards and a short run. A case of the
signature class ``blocked_malicious`` asks for its detail code from the closed
list of 36-WORTLAUT.md A3 as well, and every case asks that nothing was written
next to the job file: no member is ever written under its own name.

"Without running out of memory" is proven by the Linux run of python.yml, where
the child lives under RLIMIT_AS and an exhausted address space would end as
failed(out_of_memory) instead of the expected verdict. Windows has no
RLIMIT_AS; there the corpus proves the verdict and the run time only.

**What is not built yet is marked, not left out.** A case whose detection
plan 36-08 or 36-09 builds stands in its table with the target verdict and an
``xfail(strict=True)`` that names the plan. Strict means an unexpected pass
fails the run, so the plan that builds the detection has to lift the mark, and
the corpus shows until then exactly what is missing.

Each family has at least one positive control: an honest file, or a hostile
looking one below the line of D-36-17, that keeps the verdict it had.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from typing import Any, NamedTuple

import pytest

from findling.config import ARCHIVE_MAX_RATIO
from findling.extract import sandbox
from findling.extract.errors import Reason, State
from hostile import (
    ATTACK_RATIO,
    CASE_SECONDS,
    CORPUS_DEADLINE_SECONDS,
    DOCX_DOCUMENT,
    ODT_CONTENT,
    PPTX_SLIDE,
    XLSX_SHEET,
    Member,
    _difat_cycle,
    _directory_cycle,
    _fat_cycle,
    _fat_declared_far_past_the_file,
    _minifat_cycle,
    billion_laughs_xml,
    build_doc,
    build_workbook,
    build_zip,
    corpus_case,
    deep_nesting_xml,
    docx_with,
    honest_large_jpeg,
    jpeg_zip_polyglot,
    nested_rfc822,
    odt_with,
    package_with_entries,
    pdf_with_text,
    pdf_zip_polyglot,
    png_bomb,
    png_text_bomb,
    pptx_with,
    quadratic_blowup_xml,
    text_member,
    tiff_ifd_cycle,
    tiff_many_ifds,
    xlsx_with,
    xml_text,
    zip_depth_three,
    zip_entries,
    zip_moderate_ratio_member,
    zip_overlap,
    zip_oversized_member,
    zip_ratio_member,
    zip_traversal,
)

ZIP = "application/zip"
MAIL = "message/rfc822"
DOC = "application/msword"
XLS = "application/vnd.ms-excel"
PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
ODT = "application/vnd.oasis.opendocument.text"
PNG = "image/png"
TIFF = "image/tiff"
JPEG = "image/jpeg"

# The closed list of detail codes of the signature class (36-WORTLAUT.md A3).
DETAIL_CODES = frozenset(
    {
        "zip_ratio",
        "zip_overlap",
        "zip_traversal",
        "package_entries",
        "xml_entities",
        "image_pixels",
        "mail_nesting",
        "cfb_cycle",
    }
)

Verdict = tuple[State, Reason | None]

BLOCKED: Verdict = (State.SKIPPED, Reason.BLOCKED_MALICIOUS)
LIMIT: Verdict = (State.SKIPPED, Reason.ARCHIVE_LIMIT)
INDEXED: Verdict = (State.INDEXED, None)
CORRUPT: Verdict = (State.FAILED, Reason.CORRUPT)
TOO_LARGE: Verdict = (State.SKIPPED, Reason.TOO_LARGE)

# A picture that reaches the engine: without one (this machine, python.yml)
# failed(ocr_unavailable), with one (the image) indexed or empty_text. All three
# are names; the point of these cases is the decoder, not the engine.
READABLE = frozenset({(State.FAILED, Reason.OCR_UNAVAILABLE), INDEXED, (State.SKIPPED, Reason.EMPTY_TEXT)})


class Case(NamedTuple):
    build: Callable[[], bytes]
    mime: str
    verdict: Verdict | frozenset[Verdict]
    detail: str | None  # the detail code, for a case of the signature class only
    why: str  # the decision or finding the case stands for
    contains: str = ""  # a word the text must hold
    seconds: float = CASE_SECONDS  # the run time the case may take


def _allowed(case: Case) -> frozenset[Verdict]:
    return case.verdict if isinstance(case.verdict, frozenset) else frozenset({case.verdict})


@pytest.fixture(scope="module")
def worker() -> Iterator[sandbox.ExtractionWorker]:
    started = sandbox.ExtractionWorker(max_files=1000, timeout_seconds=CORPUS_DEADLINE_SECONDS)
    yield started
    started.stop()


_JOB = "korpus.bin"


def _check(case: Case, worker: sandbox.ExtractionWorker, tmp_path: Path) -> None:
    ran, left = corpus_case(worker, tmp_path, _JOB, case.build(), case.mime)

    verdict = (ran.outcome.state, ran.outcome.reason)
    assert verdict in _allowed(case), (verdict, ran.outcome.detail)
    assert ran.seconds < case.seconds
    if ran.outcome.reason is Reason.BLOCKED_MALICIOUS:
        assert ran.outcome.detail == case.detail
    if case.contains:
        assert case.contains in ran.outcome.text
    # Members go into scratch files named by a number next to the job file and
    # are deleted at once; nothing is ever written under a member name.
    assert left == [_JOB]


def _params(table: Mapping[str, Case], pending: Mapping[str, Any]) -> list[Any]:
    assert set(pending) <= set(table)
    return [pytest.param(name, marks=pending.get(name, ()), id=name) for name in table]


# -- ZIP files -------------------------------------------------------------------------

_ARCHIVE_CASES: dict[str, Case] = {
    "plain": Case(lambda: build_zip([text_member("klarwort")]), ZIP, INDEXED, None, "control", "klarwort"),
    "ratio-over-the-attack-ratio": Case(zip_ratio_member, ZIP, BLOCKED, "zip_ratio", "D-36-17, O12: over 1000 to 1"),
    # Positive controls of O12: densely packed but no bomb, over ARCHIVE_MAX_RATIO
    # (100) and at most ATTACK_RATIO (1000), stays archive_limit.
    "ratio-about-150": Case(zip_moderate_ratio_member, ZIP, LIMIT, None, "D-36-17, O12: positive control"),
    "ratio-just-under-1000": Case(
        lambda: zip_moderate_ratio_member(950), ZIP, LIMIT, None, "O12: a case just under the owner's number"
    ),
    "overlap-outside": Case(zip_overlap, ZIP, BLOCKED, "zip_overlap", "D-36-17, A3"),
    "overlap-inside": Case(
        lambda: build_zip([Member(b"innen.zip", zip_overlap()), text_member("aussenwort")]),
        ZIP,
        BLOCKED,
        "zip_overlap",
        "O2 (a): every level",
    ),
    "traversal-dot-dot": Case(lambda: zip_traversal(b"../x.txt"), ZIP, BLOCKED, "zip_traversal", "D-36-17, A3"),
    "traversal-absolute": Case(lambda: zip_traversal(b"/etc/x"), ZIP, BLOCKED, "zip_traversal", "D-36-17, A3"),
    "traversal-drive-letter": Case(lambda: zip_traversal(b"C:\\x"), ZIP, BLOCKED, "zip_traversal", "D-36-17, A3"),
    "traversal-nul": Case(lambda: zip_traversal(b"a\x00b.txt"), ZIP, BLOCKED, "zip_traversal", "O5 (a)"),
    # Over max_file_bytes, under the ratio and under the sum: a name, not a bomb.
    "member-over-max-file-bytes": Case(zip_oversized_member, ZIP, INDEXED, None, "A3: name in the text", "riesig.txt"),
    "depth-three-without-zeros": Case(zip_depth_three, ZIP, LIMIT, None, "O4 (a): depth alone, positive control"),
    "10001-entries": Case(zip_entries, ZIP, LIMIT, None, "A3: honestly large, positive control"),
}

# Every signature of this table is built (plan 36-08, D-36-17).
_ARCHIVE_PENDING: dict[str, Any] = {}


@pytest.mark.parametrize("case", _params(_ARCHIVE_CASES, _ARCHIVE_PENDING))
def test_every_archive_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    _check(_ARCHIVE_CASES[case], worker, tmp_path)


# -- ODF and OOXML packages ----------------------------------------------------------------

_PACKAGE_CASES: dict[str, Case] = {
    "docx": Case(docx_with, DOCX, INDEXED, None, "control", "docxwort"),
    "pptx": Case(pptx_with, PPTX, INDEXED, None, "control", "pptxwort"),
    "xlsx": Case(xlsx_with, XLSX, INDEXED, None, "control", "xlsxwort"),
    "odt": Case(odt_with, ODT, INDEXED, None, "control", "odtwort"),
    # A directory of records without a single local header: the loader fails
    # on the first part it reads, so 10 000 records, the limit itself, stay corrupt.
    "docx-of-10000-records": Case(lambda: package_with_entries("docx", 10_000), DOCX, CORRUPT, None, "A3: the limit"),
    "docx-of-10001-records": Case(
        lambda: package_with_entries("docx", 10_001), DOCX, BLOCKED, "package_entries", "A3, F3"
    ),
    "odt-of-10001-records": Case(lambda: package_with_entries("odt", 10_001), ODT, BLOCKED, "package_entries", "A3"),
    "xlsx-of-10001-records": Case(lambda: package_with_entries("xlsx", 10_001), XLSX, BLOCKED, "package_entries", "A3"),
    "docx-of-a-million-records": Case(lambda: package_with_entries("docx"), DOCX, BLOCKED, "package_entries", "A3, F3"),
    "odt-of-a-million-records": Case(lambda: package_with_entries("odt"), ODT, BLOCKED, "package_entries", "A3"),
    "xlsx-of-a-million-records": Case(lambda: package_with_entries("xlsx"), XLSX, BLOCKED, "package_entries", "A3"),
}

# A million records run since plan 36-08 counts them before ZipFile: the count
# stops at the length of the directory, so no ZipInfo is ever built (before,
# ZipFile built one per record, about 560 MiB and half a minute per case).
_PACKAGE_PENDING: dict[str, Any] = {}


@pytest.mark.parametrize("case", _params(_PACKAGE_CASES, _PACKAGE_PENDING))
def test_every_package_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    _check(_PACKAGE_CASES[case], worker, tmp_path)


# -- XML bombs inside the packages ----------------------------------------------------------

_XML_CASES: dict[str, Case] = {
    "plain-odt": Case(lambda: odt_with(xml_text(b"klarwort", ODT_CONTENT)), ODT, INDEXED, None, "control", "klarwort"),
    "plain-xlsx": Case(
        lambda: xlsx_with(xml_text(b"klarwort", XLSX_SHEET)), XLSX, INDEXED, None, "control", "klarwort"
    ),
}
_XML_PENDING: dict[str, Any] = {}

for _kind, _mime, _wrap, _template in (
    ("odt", ODT, odt_with, ODT_CONTENT),
    ("docx", DOCX, docx_with, DOCX_DOCUMENT),
    ("pptx", PPTX, pptx_with, PPTX_SLIDE),
    ("xlsx", XLSX, xlsx_with, XLSX_SHEET),
):
    _XML_CASES[f"billion-laughs-{_kind}"] = Case(
        lambda wrap=_wrap, template=_template: wrap(billion_laughs_xml(template=template)),
        _mime,
        BLOCKED,
        "xml_entities",
        "A3, F3",
    )
    _XML_CASES[f"quadratic-blowup-{_kind}"] = Case(
        lambda wrap=_wrap, template=_template: wrap(quadratic_blowup_xml(template=template)),
        _mime,
        BLOCKED,
        "xml_entities",
        "A3, F3",
    )

# 10 000 nested elements: no signature, a named verdict (assumption A3 of the
# research, measured on 2026-10-21). libxml2 stops at a depth of 256 without
# XML_PARSE_HUGE ("Excessive depth in document"), so the three lxml readers end
# xml_invalid; expat has no depth limit and openpyxl reads only the direct text
# of a cell, so the word inside the nesting is dropped and the sheet is empty.
_DEEP_XML: Verdict = (State.FAILED, Reason.XML_INVALID)
_DEEP_XLSX: Verdict = (State.SKIPPED, Reason.EMPTY_TEXT)
_XML_CASES |= {
    "deep-nesting-odt": Case(lambda: odt_with(deep_nesting_xml(template=ODT_CONTENT)), ODT, _DEEP_XML, None, "A3"),
    "deep-nesting-docx": Case(lambda: docx_with(deep_nesting_xml(template=DOCX_DOCUMENT)), DOCX, _DEEP_XML, None, "A3"),
    "deep-nesting-pptx": Case(lambda: pptx_with(deep_nesting_xml(template=PPTX_SLIDE)), PPTX, _DEEP_XML, None, "A3"),
    "deep-nesting-xlsx": Case(lambda: xlsx_with(deep_nesting_xml(template=XLSX_SHEET)), XLSX, _DEEP_XLSX, None, "A3"),
}


@pytest.mark.parametrize("case", _params(_XML_CASES, _XML_PENDING))
def test_every_xml_bomb_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    _check(_XML_CASES[case], worker, tmp_path)


# -- pictures ----------------------------------------------------------------------------------

# The frame walk of a TIFF with 100 000 IFDs: Pillow's n_frames reads every IFD,
# and the walk grows faster than the count (measured on 2026-10-21 in this
# process: 10 000 IFDs 0.66 s, 20 000 1.81 s, 40 000 5.51 s; in the child
# 100 000 took 27.8 s of a 30 s case). A named verdict, but not a short run: a
# 10 MB file holds the child for half a minute, and twice as many IFDs end at
# the deadline. The case asks for the run of a frame walk bounded by the page
# cap.
_FRAME_WALK_SECONDS = 5.0

_IMAGE_CASES: dict[str, Case] = {
    "png-bomb": Case(png_bomb, PNG, BLOCKED, "image_pixels", "D-36-17, O6 (a)"),
    # 103 megapixels at about 49 pixels per byte: a real medium format picture.
    "honest-large-jpeg": Case(honest_large_jpeg, JPEG, TOO_LARGE, None, "A3: positive control"),
    # 60 megapixels: over the cap, under twice it; Pillow only warns.
    "png-of-60-megapixels": Case(lambda: png_bomb(8000, 7500), PNG, TOO_LARGE, None, "positive control"),
    # Pillow refuses a zTXt chunk over MAX_TEXT_CHUNK (1 MiB) with a ValueError.
    "png-text-bomb": Case(png_text_bomb, PNG, CORRUPT, None, "A3: a named verdict"),
    "tiff-ifd-cycle": Case(tiff_ifd_cycle, TIFF, READABLE, None, "A3: Pillow sees the cycle"),
    "tiff-of-100000-ifds": Case(
        tiff_many_ifds, TIFF, READABLE, None, "A3: frame walk under the deadline", seconds=_FRAME_WALK_SECONDS
    ),
}

_IMAGE_PENDING = {
    # Not in the plan of 36-09 yet: the frame walk has to stop at the page cap
    # (finding of 36-07, deferred-items.md).
    "tiff-of-100000-ifds": pytest.mark.xfail(strict=True, reason="built in 36-09"),
}


@pytest.mark.parametrize("case", _params(_IMAGE_CASES, _IMAGE_PENDING))
def test_every_picture_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    _check(_IMAGE_CASES[case], worker, tmp_path)


# -- mails ---------------------------------------------------------------------------------------

_MAIL_CASES: dict[str, Case] = {
    "rfc822-nested-32-times": Case(lambda: nested_rfc822(32), MAIL, INDEXED, None, "O6 (a): positive control"),
    "rfc822-nested-33-times": Case(lambda: nested_rfc822(33), MAIL, BLOCKED, "mail_nesting", "D-36-17, O6 (a)"),
    "rfc822-nested-1000-times": Case(lambda: nested_rfc822(1000), MAIL, BLOCKED, "mail_nesting", "A3"),
}

# Both signatures of this table are built (plan 36-09, D-36-17).
_MAIL_PENDING: dict[str, Any] = {}


@pytest.mark.parametrize("case", _params(_MAIL_CASES, _MAIL_PENDING))
def test_every_mail_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    _check(_MAIL_CASES[case], worker, tmp_path)


# -- compound files --------------------------------------------------------------------------------

_OLE_TEXT = b"olewort im text\r"

_CFB_CASES: dict[str, Case] = {
    "doc": Case(lambda: build_doc(_OLE_TEXT), DOC, INDEXED, None, "control", "olewort"),
    "doc-fat-cycle": Case(lambda: build_doc(_OLE_TEXT, edit=_fat_cycle), DOC, BLOCKED, "cfb_cycle", "A3"),
    "doc-minifat-cycle": Case(lambda: build_doc(_OLE_TEXT, edit=_minifat_cycle), DOC, BLOCKED, "cfb_cycle", "A3"),
    "doc-difat-cycle": Case(lambda: build_doc(_OLE_TEXT, edit=_difat_cycle), DOC, BLOCKED, "cfb_cycle", "A3"),
    "doc-directory-cycle": Case(lambda: build_doc(_OLE_TEXT, edit=_directory_cycle), DOC, BLOCKED, "cfb_cycle", "A3"),
    "xls-minifat-cycle": Case(
        lambda: build_workbook([(0, 0, 0)], ["zellwort"], edit=_minifat_cycle), XLS, BLOCKED, "cfb_cycle", "A3"
    ),
    # A structural error without a cycle stays corrupt (A3, positive control).
    "doc-fat-declared-far-past-the-file": Case(
        lambda: build_doc(_OLE_TEXT, edit=_fat_declared_far_past_the_file), DOC, CORRUPT, None, "A3"
    ),
}

_CFB_PENDING = {
    "doc-fat-cycle": pytest.mark.xfail(strict=True, reason="built in 36-09"),
    "doc-minifat-cycle": pytest.mark.xfail(strict=True, reason="built in 36-09"),
    "doc-difat-cycle": pytest.mark.xfail(strict=True, reason="built in 36-09"),
    "doc-directory-cycle": pytest.mark.xfail(strict=True, reason="built in 36-09"),
    "xls-minifat-cycle": pytest.mark.xfail(strict=True, reason="built in 36-09"),
}


@pytest.mark.parametrize("case", _params(_CFB_CASES, _CFB_PENDING))
def test_every_compound_file_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    _check(_CFB_CASES[case], worker, tmp_path)


# -- polyglots -------------------------------------------------------------------------------------

# Read by the reader of the mimetype, no verdict of their own (A3): a PDF with a
# ZIP file behind it is a PDF to pdfium and a ZIP file to zipfile.
_POLYGLOT_CASES: dict[str, Case] = {
    "pdf": Case(pdf_with_text, PDF, INDEXED, None, "control", "pdfwort"),
    "pdf-and-zip-as-pdf": Case(pdf_zip_polyglot, PDF, INDEXED, None, "A3", "pdfteilwort"),
    "pdf-and-zip-as-zip": Case(pdf_zip_polyglot, ZIP, INDEXED, None, "A3", "zipteilwort"),
    "jpeg-and-zip-as-jpeg": Case(jpeg_zip_polyglot, JPEG, READABLE, None, "A3"),
    "jpeg-and-zip-as-zip": Case(jpeg_zip_polyglot, ZIP, INDEXED, None, "A3", "zipteilwort"),
}


@pytest.mark.parametrize("case", list(_POLYGLOT_CASES))
def test_every_polyglot_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    _check(_POLYGLOT_CASES[case], worker, tmp_path)


# -- the tables themselves ------------------------------------------------------------------------

_TABLES: dict[str, tuple[dict[str, Case], Mapping[str, Any]]] = {
    "archive": (_ARCHIVE_CASES, _ARCHIVE_PENDING),
    "package": (_PACKAGE_CASES, _PACKAGE_PENDING),
    "xml": (_XML_CASES, _XML_PENDING),
    "image": (_IMAGE_CASES, _IMAGE_PENDING),
    "mail": (_MAIL_CASES, _MAIL_PENDING),
    "cfb": (_CFB_CASES, _CFB_PENDING),
    "polyglot": (_POLYGLOT_CASES, {}),
}


def test_a_case_names_a_detail_code_exactly_when_it_expects_the_signature_class() -> None:
    for name, (table, _) in _TABLES.items():
        for case_name, case in table.items():
            blocked = BLOCKED in _allowed(case)
            assert blocked == (case.detail is not None), (name, case_name)
            if blocked:
                assert _allowed(case) == {BLOCKED}, (name, case_name)
                assert case.detail in DETAIL_CODES, (name, case_name)


def test_every_family_has_a_positive_control_that_runs_today() -> None:
    for name, (table, pending) in _TABLES.items():
        controls = [case for case_name, case in table.items() if case_name not in pending and case.detail is None]
        assert controls, name


def test_the_ratio_cases_stand_where_o12_puts_them() -> None:
    # The corpus judges by the same arithmetic as archive.py, read back from the
    # bytes and not believed from the generator.
    import io
    import zipfile

    def largest_ratio(data: bytes) -> float:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            info = max(archive.infolist(), key=lambda entry: entry.file_size)
        return info.file_size / max(info.compress_size, 1)

    assert largest_ratio(zip_ratio_member()) > ATTACK_RATIO
    assert ARCHIVE_MAX_RATIO < largest_ratio(zip_moderate_ratio_member()) < 200
    assert 900 < largest_ratio(zip_moderate_ratio_member(950)) <= ATTACK_RATIO


def test_the_generators_are_deterministic() -> None:
    cheap = [
        zip_ratio_member,
        zip_moderate_ratio_member,
        zip_overlap,
        zip_oversized_member,
        lambda: zip_traversal(b"../x.txt"),
        lambda: package_with_entries("odt", 10_001),
        lambda: docx_with(billion_laughs_xml(template=DOCX_DOCUMENT)),
        lambda: xlsx_with(quadratic_blowup_xml(template=XLSX_SHEET)),
        png_bomb,
        png_text_bomb,
        tiff_ifd_cycle,
        honest_large_jpeg,
        pdf_zip_polyglot,
        jpeg_zip_polyglot,
        lambda: build_doc(_OLE_TEXT, edit=_fat_cycle),
    ]
    for build in cheap:
        assert build() == build()


# -- nothing of the corpus reaches a log -----------------------------------------------------------

# Every word a log line must never carry; each one is placed in a name or in the
# content of the log corpus below.
SECRETS = (
    "archivgeheim",
    "archivinhaltgeheim",
    "paketgeheim",
    "entitygeheim",
    "bildgeheim",
    "postgeheim",
    "kettegeheim",
    "polyglottgeheim",
)


def _log_corpus() -> dict[str, tuple[bytes, str]]:
    polyglot = pdf_with_text(b"polyglottgeheim steht auf dieser einen seite") + build_zip(
        [Member(b"polyglottgeheim.txt", b"polyglottgeheim")]
    )
    return {
        "traversal.zip": (zip_traversal(b"../archivgeheim.txt", b"archivinhaltgeheim"), ZIP),
        "overlap.zip": (zip_overlap(b"archivgeheim.txt", b"archivinhaltgeheim"), ZIP),
        "ratio.zip": (build_zip([Member(b"archivgeheim.bin", bytes(2 * 1024 * 1024), deflate=True)]), ZIP),
        "paket.docx": (docx_with(xml_text(b"paketgeheim", DOCX_DOCUMENT)), DOCX),
        "records.odt": (package_with_entries("odt", 10_001), ODT),
        "laughs.odt": (odt_with(billion_laughs_xml(template=ODT_CONTENT)), ODT),
        "laughs.xlsx": (xlsx_with(billion_laughs_xml(template=XLSX_SHEET)), XLSX),
        "text.png": (png_text_bomb(), PNG),
        "bomb.png": (png_bomb(), PNG),
        "post.eml": (b"Subject: postgeheim\r\n" + nested_rfc822(33), MAIL),
        "deep.eml": (b"Subject: postgeheim\r\n" + nested_rfc822(1000), MAIL),
        "kette.doc": (build_doc(b"kettegeheim im text\r", edit=_fat_cycle), DOC),
        "poly.pdf": (polyglot, PDF),
        "poly.zip": (polyglot, ZIP),
    }


# A PNG between the pixel cap of image.py (50 MP) and twice the cap: Pillow
# warns about a possible decompression bomb, with numbers and nothing else.
_CONTROL_WARNING = "DecompressionBombWarning"


def test_no_line_of_the_corpus_run_carries_a_name_or_a_word_of_the_content(
    tmp_path: Path, capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    # A worker of its own, so that the warning filters of a fresh child apply
    # and no case of another test has already used up a "print once" warning.
    fresh = sandbox.ExtractionWorker(max_files=1000, timeout_seconds=CORPUS_DEADLINE_SECONDS)
    try:
        for name, (data, mime) in _log_corpus().items():
            path = tmp_path / name
            path.write_bytes(data)
            assert fresh.run(str(path), mime, len(data)).reason is not Reason.TIMEOUT
        control = tmp_path / "control.png"
        control.write_bytes(png_bomb(8000, 7500))
        assert fresh.run(str(control), PNG, control.stat().st_size).reason is Reason.TOO_LARGE
    finally:
        fresh.stop()
    out, err = capfd.readouterr()

    # The positive control: the child's stderr reaches this probe.
    assert _CONTROL_WARNING in err
    seen = "\n".join((out, err, *(record.getMessage() for record in caplog.records)))
    assert [secret for secret in SECRETS if secret in seen] == []
