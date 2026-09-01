"""Rasterising a page, and reading it with an engine that may not be there.

Two modules, one test file, because they are one claim: a scan becomes text, or
it becomes a verdict that says why it did not. Splitting them would hide the
place where the two meet, which is the page loop with its caps.

The corpus files are the input on purpose. A PDF built inside this test would
prove something about that PDF; the files under ``testdata/corpus`` are the ones
the read only gate copies into a throwaway Nextcloud and the ones the acceptance
of D-09 searches in, and the German terms in them exist nowhere else.

**The engine tests are skipped where there is no engine.** The development
machine of this project has no tesseract, the container has it, and a suite that
silently passes in both cases would be worth nothing in either. So the tests that
need the real binary are marked, and the failure paths that must hold everywhere
are driven through a stand in for ``subprocess.run`` instead. That stand in is
also the only way to reach the timeout and the non zero exit code deliberately:
both are outliers, and an outlier that is provoked by a real document is a test
about that document.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
import subprocess
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import pypdfium2
import pytest
from PIL import Image

from findling.config import settings
from findling.extract import ocr, raster
from findling.extract.errors import Reason, State

CORPUS = Path(__file__).resolve().parents[2] / "testdata" / "corpus"

# Three A4 pages of German council prose that exist only as pixels. The one term
# that stands in no other file of the corpus is Bebauungsplan.
SCAN = str(CORPUS / "13-ratsvorlage-scan.pdf")

# 14400 by 14400 points, the largest page the format allows. At 300 dpi that is
# 60000 pixels on an edge, or nine gigapixels in one channel.
HUGE = str(CORPUS / "31-riesenformat.pdf")

# The file that stops in the middle of its trailer.
BROKEN = str(CORPUS / "24-abgeschnittener-trailer.pdf")

DPI = 300

# The environment this suite has to start from cold, because the caps are read
# once per process and cached.
OCR_ENVIRONMENT = (
    "FINDLING_OCR_ENABLED",
    "FINDLING_OCR_LANGUAGES",
    "FINDLING_OCR_MAX_PAGES",
    "FINDLING_OCR_PAGE_SECONDS",
    "FINDLING_OCR_JOB_SECONDS",
    "FINDLING_OCR_DPI",
)

needs_engine = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="no tesseract on this machine; the container runs this test for real",
)


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Every test starts with an empty environment and a cold cap cache."""
    for name in OCR_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)
    settings.cache_clear()
    yield
    settings.cache_clear()


def _decode(png: bytes) -> Image.Image:
    return Image.open(BytesIO(png))


def test_a_corpus_page_becomes_a_grayscale_png() -> None:
    document = pypdfium2.PdfDocument(SCAN)
    try:
        png = raster.render_page_png(document, 0, dpi=DPI)
    finally:
        document.close()

    with _decode(png) as image:
        assert image.format == "PNG"
        # One channel, not four. A4 at 300 dpi is 8.7 MB in grey and 35 MB in
        # BGRA, and tesseract binarises internally either way.
        assert image.mode == "L"
        # 595 by 842 points at 300 dpi, so the ordinary page is rendered at full
        # resolution and the bomb guard below does not touch it.
        assert image.size == (2480, 3509)


@dataclass(frozen=True, slots=True)
class _PaddedBitmap:
    """A bitmap whose rows are wider than its pixels, which pdfium may hand out."""

    width: int
    height: int
    stride: int
    buffer: bytes


def test_the_padded_rows_are_cut_to_the_stride() -> None:
    # Three pixels per row, five bytes per row: the last two of each row are
    # padding and belong to no pixel. Reading the buffer as one block would shift
    # every row by two and turn the page into diagonal stripes, which is the one
    # rasterising bug that still produces a plausible looking image.
    padded = _PaddedBitmap(
        width=3,
        height=2,
        stride=5,
        buffer=bytes([10, 20, 30, 99, 99, 40, 50, 60, 99, 99]),
    )

    with _decode(raster._encode_page(padded)) as image:
        assert image.size == (3, 2)
        assert list(image.tobytes()) == [10, 20, 30, 40, 50, 60]


def test_both_pdfium_objects_are_released_when_the_encoding_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    # The error path is where a close is forgotten, and over an initial index of
    # 100000 files inside a container with 4 GB a forgotten close is not a leak,
    # it is the end of the process. The order is asserted too: the bitmap is a
    # child of the page, so it goes first.
    closed: list[str] = []
    # Captured as plain callables: the close of pypdfium2 takes a private second
    # argument and answers a bool, and pinning that shape here would make this
    # test fail on the day the library adds a keyword rather than on the day the
    # release stops happening.
    page_close: Callable[..., object] = pypdfium2.PdfPage.close
    bitmap_close: Callable[..., object] = pypdfium2.PdfBitmap.close

    def closing_page(page: pypdfium2.PdfPage) -> None:
        closed.append("page")
        page_close(page)

    def closing_bitmap(bitmap: pypdfium2.PdfBitmap) -> None:
        closed.append("bitmap")
        bitmap_close(bitmap)

    def boom(bitmap: object) -> bytes:
        raise RuntimeError("the encoder gave up")

    monkeypatch.setattr(pypdfium2.PdfPage, "close", closing_page)
    monkeypatch.setattr(pypdfium2.PdfBitmap, "close", closing_bitmap)
    monkeypatch.setattr(raster, "_encode_page", boom)

    document = pypdfium2.PdfDocument(SCAN)
    try:
        with pytest.raises(RuntimeError):
            raster.render_page_png(document, 0, dpi=DPI)
        assert closed == ["bitmap", "page"]
    finally:
        document.close()


def test_a_page_with_an_absurd_area_is_bound_to_the_maximum_edge() -> None:
    document = pypdfium2.PdfDocument(HUGE)
    try:
        png = raster.render_page_png(document, 0, dpi=DPI)
    finally:
        document.close()

    with _decode(png) as image:
        # Bound, and bound exactly: a value below the cap would mean the guard
        # missed and something else made the page small.
        assert max(image.size) == raster.MAX_EDGE_PIXELS


def test_the_corpus_file_is_unchanged_by_rasterising() -> None:
    # The same invariant the read only gate measures from the outside, asserted
    # here at the module that opens the file (IDX-07).
    before = hashlib.sha256(Path(SCAN).read_bytes()).hexdigest()

    document = pypdfium2.PdfDocument(SCAN)
    try:
        raster.render_page_png(document, 0, dpi=DPI)
    finally:
        document.close()

    assert hashlib.sha256(Path(SCAN).read_bytes()).hexdigest() == before


@dataclass(frozen=True, slots=True)
class _Finished:
    """What the engine answers, reduced to the three fields the branch reads."""

    returncode: int = 0
    stdout: bytes = b""
    stderr: bytes = b""


@dataclass(slots=True)
class _Engine:
    """A stand in for the engine, one answer per page, with every call recorded.

    The three interesting outcomes of a page are an outlier by nature: a timeout,
    a death by signal and a missing binary. Provoking them with a real document
    would mean building a document that hangs tesseract, which is a test about
    that document. Here the page loop is driven directly, and the assertions are
    about the loop.
    """

    answers: Callable[[int], _Finished]
    calls: list[dict[str, object]] = field(default_factory=list)

    def run(self, argv: list[str], **options: object) -> _Finished:
        self.calls.append({"argv": argv, **options})
        return self.answers(len(self.calls) - 1)


def _install_engine(monkeypatch: pytest.MonkeyPatch, answers: Callable[[int], _Finished]) -> _Engine:
    engine = _Engine(answers)
    monkeypatch.setattr(ocr.subprocess, "run", engine.run)
    return engine


def _page(text: str) -> Callable[[int], _Finished]:
    return lambda number: _Finished(stdout=f"{text} {number}\n".encode())


@needs_engine
def test_a_scanned_document_becomes_the_term_the_corpus_promises() -> None:
    # The acceptance of D-09, at the level of the module: Bebauungsplan stands in
    # this file and in no other one of the corpus, and it exists only as pixels.
    outcome = ocr.extract_pdf_ocr(SCAN)

    assert outcome.state is State.INDEXED
    assert "Bebauungsplan" in outcome.text


def test_a_document_over_the_page_cap_is_indexed_and_says_truncated(monkeypatch: pytest.MonkeyPatch) -> None:
    # D-08: the first pages searchable beats nothing searchable. The three upper
    # caps therefore end the loop and keep the text, they do not discard it.
    monkeypatch.setenv("FINDLING_OCR_MAX_PAGES", "1")
    engine = _install_engine(monkeypatch, _page("Ratsvorlage"))

    outcome = ocr.extract_pdf_ocr(SCAN)

    assert outcome.state is State.INDEXED
    assert outcome.reason is Reason.TRUNCATED
    assert outcome.truncated is True
    assert "Ratsvorlage" in outcome.text
    assert len(engine.calls) == 1


def test_a_page_over_the_time_cap_is_dropped_and_the_loop_goes_on(monkeypatch: pytest.MonkeyPatch) -> None:
    def answers(number: int) -> _Finished:
        if number == 0:
            raise subprocess.TimeoutExpired(cmd="tesseract", timeout=30)
        return _Finished(stdout=f"Seite {number}\n".encode())

    engine = _install_engine(monkeypatch, answers)

    outcome = ocr.extract_pdf_ocr(SCAN)

    # One page lost, the document kept. A hanging page costs the page.
    assert outcome.state is State.INDEXED
    assert outcome.reason is None
    assert "Seite 1" in outcome.text
    assert "Seite 2" in outcome.text
    assert len(engine.calls) == 3


def test_every_page_over_the_time_cap_ends_as_failed_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def answers(number: int) -> _Finished:
        raise subprocess.TimeoutExpired(cmd="tesseract", timeout=30)

    _install_engine(monkeypatch, answers)

    outcome = ocr.extract_pdf_ocr(SCAN)

    # Nothing was read at all, so this is not a thin document, it is a failure.
    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.TIMEOUT


def test_a_non_zero_exit_code_ends_as_failed_ocr_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    # 134 is what a page that burst the address space looks like from here: the
    # grandchild died of SIGABRT after a bad_alloc, and no MemoryError ever
    # arrived in this process (measurement 5 of docs/ocr.md).
    engine = _install_engine(monkeypatch, lambda number: _Finished(returncode=134, stderr=b"std::bad_alloc"))

    outcome = ocr.extract_pdf_ocr(SCAN)

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.OCR_FAILED
    # And it stops. Whatever killed page one kills page two as well.
    assert len(engine.calls) == 1


def test_a_missing_engine_ends_as_failed_ocr_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def answers(number: int) -> _Finished:
        raise FileNotFoundError(2, "No such file or directory: 'tesseract'")

    _install_engine(monkeypatch, answers)

    outcome = ocr.extract_pdf_ocr(SCAN)

    # Its own verdict, because "this image has no OCR" and "this document beat
    # the parser" call for entirely different answers from an admin.
    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.OCR_UNAVAILABLE


def test_a_result_under_the_character_threshold_is_skipped_empty_text(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_engine(monkeypatch, lambda number: _Finished(stdout=b"  \n\f\n"))

    outcome = ocr.extract_pdf_ocr(SCAN)

    assert outcome.state is State.SKIPPED
    assert outcome.reason is Reason.EMPTY_TEXT
    assert outcome.text == ""


def test_the_soft_deadline_ends_the_loop_and_keeps_the_pages_already_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = {"now": 0.0}
    monkeypatch.setattr(ocr.time, "monotonic", lambda: clock["now"])

    def answers(number: int) -> _Finished:
        # The first page alone eats the whole job budget.
        clock["now"] += settings().ocr_job_seconds + 1
        return _Finished(stdout=f"Seite {number}\n".encode())

    engine = _install_engine(monkeypatch, answers)

    outcome = ocr.extract_pdf_ocr(SCAN)

    assert outcome.state is State.INDEXED
    assert outcome.reason is Reason.TRUNCATED
    assert "Seite 0" in outcome.text
    assert len(engine.calls) == 1


def test_the_call_is_an_argument_list_with_the_measured_options(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_OCR_MAX_PAGES", "1")
    engine = _install_engine(monkeypatch, _page("Ratsvorlage"))

    ocr.extract_pdf_ocr(SCAN)

    call = engine.calls[0]
    argv = call["argv"]
    assert isinstance(argv, list)
    # The call form of docs/ocr.md, argument by argument. stdin and stdout are
    # the two dashes, so no page of user content is ever written to disk.
    assert argv[:3] == ["tesseract", "-", "-"]
    assert argv[3:5] == ["-l", "deu+eng"]
    assert argv[5:7] == ["--oem", "1"]
    assert argv[7:9] == ["--psm", "3"]
    assert argv[9:] == ["-c", "tessedit_do_invert=0"]

    # A list and never a shell, which is what makes the language list unable to
    # become a command (T-03-801).
    assert "shell" not in call

    environment = call["env"]
    assert isinstance(environment, dict)
    # Part of the memory guarantee, not a tuning knob: without it the same run
    # dies at 128 MB with exit code 134 (measurement 3 of docs/ocr.md).
    assert environment["OMP_THREAD_LIMIT"] == "1"

    assert call["timeout"] == settings().ocr_page_seconds
    assert call["check"] is False
    assert call["capture_output"] is True
    payload = call["input"]
    assert isinstance(payload, bytes)
    assert payload.startswith(b"\x89PNG")


def test_the_engine_stderr_reaches_no_log(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    # Tesseract writes file names and content related warnings there, and the log
    # of this project carries counters and reason codes, nothing else (T-02-107).
    leak = b"Warning: Invalid resolution 0 dpi in /home/anna/Steuerbescheid-2026.pdf"
    _install_engine(monkeypatch, lambda number: _Finished(stdout=b"Ratsvorlage\n", stderr=leak))

    with caplog.at_level(logging.DEBUG):
        ocr.extract_pdf_ocr(SCAN)

    assert "Steuerbescheid" not in caplog.text
    assert "Invalid resolution" not in caplog.text


def test_a_corrupt_pdf_becomes_a_verdict_instead_of_an_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_engine(monkeypatch, _page("nie erreicht"))

    outcome = ocr.extract_pdf_ocr(BROKEN)

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.CORRUPT


def test_original_file_is_unchanged_after_ocr() -> None:
    # No stand in and no skip mark on purpose: inside the image this runs the
    # real engine over three pages, on the development machine it ends as
    # ocr_unavailable, and in both cases the document was opened and rasterised.
    # The read only invariant has to hold on both paths (IDX-07, T-03-805).
    before = hashlib.sha256(Path(SCAN).read_bytes()).hexdigest()
    stat_before = Path(SCAN).stat()

    ocr.extract_pdf_ocr(SCAN)

    assert hashlib.sha256(Path(SCAN).read_bytes()).hexdigest() == before
    assert Path(SCAN).stat().st_size == stat_before.st_size
    assert Path(SCAN).stat().st_mtime == stat_before.st_mtime
