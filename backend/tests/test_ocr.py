"""Rasterising a page, and reading it with an engine that may not be there.

Two modules, one test file, because they are one claim: a scan becomes text, or
it becomes a verdict that says why it did not. Splitting them would hide the
place where the two meet, which is the page loop with its caps. Since plan 03-09
the dispatcher is the third module in here, for the same reason: the route is the
only way the page loop is ever reached, and a group of tests that proved the loop
without proving the way in would be a machine nobody can start. Plan 03-10 adds
the fourth, ``extract.image``: a picture is the other kind of input the same
engine reads, it goes through the same stand in, and the caps in front of it only
mean something next to the ones behind it.

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

import ast
import hashlib
import logging
import shutil
import struct
import subprocess
import sys
import unicodedata
import zlib
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import pypdfium2
import pytest
from PIL import Image, ImageOps, JpegImagePlugin, TiffImagePlugin

from findling.config import settings
from findling.extract import dispatch, image, ocr, raster
from findling.extract.dispatch import Route
from findling.extract.errors import KILLED_EXIT_CODE, EngineKilled, Reason, State

CORPUS = Path(__file__).resolve().parents[2] / "testdata" / "corpus"

DISPATCH_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "extract" / "dispatch.py"

# Three A4 pages of German council prose that exist only as pixels. The one term
# that stands in no other file of the corpus is Bebauungsplan.
SCAN = str(CORPUS / "13-ratsvorlage-scan.pdf")

# The counterpart: a PDF that carries its text as text. D-06 says it is extracted
# and never OCR-t, and the decision falls in pdf.py, not on this route.
TEXT_LAYER = str(CORPUS / "01-text-layer.pdf")

# 14400 by 14400 points, the largest page the format allows. At 300 dpi that is
# 60000 pixels on an edge, or nine gigapixels in one channel.
HUGE = str(CORPUS / "31-riesenformat.pdf")

# The file that stops in the middle of its trailer.
BROKEN = str(CORPUS / "24-abgeschnittener-trailer.pdf")

# The pictures of plan 03-10, all of them 1000 by 260 pixels: over the minimum
# edge, well under the aspect ratio cap, and therefore plausible documents.
SLIP = str(CORPUS / "17-beleg.jpg")

# Three frames in one file, the shape a fax archive has.
FAX = str(CORPUS / "21-sendebericht.tif")

# 48 by 48 pixels. The one corpus file that must never reach the engine.
ICON = str(CORPUS / "22-icon.png")

# 260 by 1000 pixels with EXIF orientation 6: a page photographed sideways,
# which arrives at the engine rotated by ninety degrees unless it is uprighted.
SIDEWAYS = str(CORPUS / "23-gedreht.jpg")

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

    with _decode(png) as page:
        assert page.format == "PNG"
        # One channel, not four. A4 at 300 dpi is 8.7 MB in grey and 35 MB in
        # BGRA, and tesseract binarises internally either way.
        assert page.mode == "L"
        # 595 by 842 points at 300 dpi, so the ordinary page is rendered at full
        # resolution and the bomb guard below does not touch it.
        assert page.size == (2480, 3509)


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

    with _decode(raster._encode_page(padded)) as page:
        assert page.size == (3, 2)
        assert list(page.tobytes()) == [10, 20, 30, 40, 50, 60]


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

    with _decode(png) as page:
        # Bound, and bound exactly: a value below the cap would mean the guard
        # missed and something else made the page small.
        assert max(page.size) == raster.MAX_EDGE_PIXELS


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
    """One line of plausible page text per page.

    Long enough on purpose: a whole run under the character threshold of the
    module is skipped(empty_text), and a fixture that accidentally sits below it
    would assert the empty case while claiming to assert the full one.
    """
    return lambda number: _Finished(stdout=f"{text}, Seite {number} von drei\n".encode())


@needs_engine
@pytest.mark.parametrize(
    ("name", "term"),
    [
        ("13-ratsvorlage-scan.pdf", "Bebauungsplan"),
        ("15-schweiz-baubewilligung.pdf", "Strasse"),
        ("16-oesterreich-mitteilung.pdf", "Jänner"),
    ],
)
def test_a_scanned_document_becomes_the_terms_the_corpus_promises(name: str, term: str) -> None:
    # The acceptance of D-09 at the level of the module. Each of these three words
    # stands in exactly one file of the corpus and exists there only as pixels, so
    # a hit is proof that the engine read them and not that the corpus is chatty.
    # The Swiss ss and the Austrian wording are in the list because a DACH corpus
    # that only proves German is half a proof.
    outcome = ocr.extract_pdf_ocr(str(CORPUS / name))

    assert outcome.state is State.INDEXED
    assert term in outcome.text


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


def test_a_page_over_the_time_cap_is_dropped_and_the_document_says_truncated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def answers(number: int) -> _Finished:
        if number == 0:
            raise subprocess.TimeoutExpired(cmd="tesseract", timeout=30)
        return _Finished(stdout=f"Beschlussvorlage, Seite {number} von drei\n".encode())

    engine = _install_engine(monkeypatch, answers)

    outcome = ocr.extract_pdf_ocr(SCAN)

    # One page lost, the document kept, and the loss visible. A document that
    # silently dropped a page is exactly the quietly thin result D-08 rules
    # out (review finding WR-03): no later run fetches the lost page, because
    # the hash never changes, so the mark is the only trace the loss leaves.
    assert outcome.state is State.INDEXED
    assert outcome.reason is Reason.TRUNCATED
    assert outcome.truncated is True
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


def test_an_engine_killed_by_sigkill_is_engine_killed_and_not_engine_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    # D-26-16: under N slots the OOM killer takes whichever tesseract is largest,
    # and that says nothing about the page it was reading.
    _install_engine(monkeypatch, lambda number: _Finished(returncode=KILLED_EXIT_CODE))

    with pytest.raises(EngineKilled):
        ocr.read_page(b"png", "deu", 30)


def test_a_non_zero_exit_code_is_still_engine_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_engine(monkeypatch, lambda number: _Finished(returncode=1))

    with pytest.raises(ocr.EngineFailed):
        ocr.read_page(b"png", "deu", 30)


def test_engine_killed_is_a_sister_and_not_a_kind_of_engine_failed() -> None:
    # A subclass would be caught by every handler that maps EngineFailed to
    # failed(ocr_failed), which is exactly the verdict this exception avoids.
    assert not issubclass(EngineKilled, ocr.EngineFailed)


def test_a_killed_engine_leaves_the_scan_branch_without_a_verdict(monkeypatch: pytest.MonkeyPatch) -> None:
    # No handler of the scan branch may turn the kill into failed(ocr_failed):
    # it has to reach the child loop, which answers with its sentinel.
    _install_engine(monkeypatch, lambda number: _Finished(returncode=KILLED_EXIT_CODE))

    with pytest.raises(EngineKilled):
        ocr.extract_pdf_ocr(SCAN)


def test_a_killed_engine_leaves_the_picture_branch_without_a_verdict(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_engine(monkeypatch, lambda number: _Finished(returncode=KILLED_EXIT_CODE))

    with pytest.raises(EngineKilled):
        image.extract_image(SLIP)


def test_a_killed_engine_leaves_the_dispatcher_without_a_verdict(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_engine(monkeypatch, lambda number: _Finished(returncode=KILLED_EXIT_CODE))

    with pytest.raises(EngineKilled):
        dispatch.extract(SCAN, "application/pdf", Path(SCAN).stat().st_size, Route.OCR)


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
        return _Finished(stdout=f"Beschlussvorlage, Seite {number} von drei\n".encode())

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
    # deu+eng+fra since the owner decision of 2026-09-06. The joined string is
    # built from OCR_DEFAULT_LANGUAGES, so this line is the proof that the order
    # of the tuple survives into the argument list: the leading language is the
    # one the engine weighs most.
    assert argv[3:5] == ["-l", "deu+eng+fra"]
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
    _install_engine(monkeypatch, lambda number: _Finished(stdout=b"Ratsvorlage des Bauamtes\n", stderr=leak))

    with caplog.at_level(logging.DEBUG):
        ocr.extract_pdf_ocr(SCAN)

    assert "Steuerbescheid" not in caplog.text
    assert "Invalid resolution" not in caplog.text


def test_a_corrupt_pdf_becomes_a_verdict_instead_of_an_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_engine(monkeypatch, _page("nie erreicht"))

    outcome = ocr.extract_pdf_ocr(BROKEN)

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.CORRUPT


def _module_level_imports(source: Path) -> set[str]:
    """Every module name the file imports at module level, dotted and whole."""
    names: set[str] = set()
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def test_a_job_of_kind_ocr_takes_the_ocr_route_whatever_the_mimetype(monkeypatch: pytest.MonkeyPatch) -> None:
    # The second track is a property of the job, not of the file. A mimetype that
    # the allowlist rejects outright is the sharpest way to say so: judge would
    # answer skipped(mime_not_allowed), and the forced route still reads the page.
    monkeypatch.setenv("FINDLING_OCR_MAX_PAGES", "1")
    engine = _install_engine(monkeypatch, _page("Ratsvorlage"))

    outcome = dispatch.extract(SCAN, "application/x-findling-not-a-real-type", 4096, Route.OCR)

    assert outcome.state is State.INDEXED
    assert "Ratsvorlage" in outcome.text
    assert len(engine.calls) == 1


def test_a_pdf_with_a_text_layer_still_takes_the_pdf_route(monkeypatch: pytest.MonkeyPatch) -> None:
    # D-06, from the side of the dispatcher: a document that carries text is
    # extracted and never handed to the engine. This plan must not undo that
    # decision by running OCR in addition (T-03-906).
    engine = _install_engine(monkeypatch, _page("nie erreicht"))

    outcome = dispatch.extract(TEXT_LAYER, "application/pdf", Path(TEXT_LAYER).stat().st_size)

    assert outcome.state is State.INDEXED
    assert engine.calls == []


def test_the_ocr_route_imports_its_modules_inside_the_branch() -> None:
    # Same reason as every other route: the child is recycled every 200 files, so
    # an import at module level is paid on every recycle, even in a container
    # that never sees a single scan.
    body = DISPATCH_SOURCE.read_text(encoding="utf-8")
    branch = body.split("case Route.OCR:", 1)[1].split("case ", 1)[0]

    assert "from findling.extract import ocr" in branch

    imported = _module_level_imports(DISPATCH_SOURCE)
    assert "findling.extract.ocr" not in imported
    assert "findling.extract.raster" not in imported


def test_the_forced_ocr_route_without_an_engine_is_ocr_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    # The route reaches the verdict, not only the module. An image without OCR in
    # it has to say so, because "no engine here" and "this document beat the
    # parser" call for entirely different answers from an admin (T-03-806).
    def answers(number: int) -> _Finished:
        raise FileNotFoundError(2, "No such file or directory: 'tesseract'")

    _install_engine(monkeypatch, answers)

    outcome = dispatch.extract(SCAN, "application/pdf", 4096, Route.OCR)

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.OCR_UNAVAILABLE


def test_the_dispatcher_no_longer_calls_its_picture_path_missing() -> None:
    # The paragraph that said phase 3 would add the path and that a picture is
    # honestly reported as unsupported until then. Half of it is now false, and a
    # docstring that lies is worse than none.
    body = DISPATCH_SOURCE.read_text(encoding="utf-8").lower()

    assert "until then a picture is honestly reported as unsupported" not in " ".join(body.split())
    assert "image" in body


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


# ---------------------------------------------------------------------------
# The picture branch of plan 03-10. Everything above reads a PDF; from here on
# the input is a file that is nothing but pixels, and the question is which of
# them are worth an engine call at all.
# ---------------------------------------------------------------------------


def _drawn(tmp_path: Path, name: str, size: tuple[int, int]) -> str:
    """A plain grey picture of a given size, for the caps no corpus file hits.

    The corpus carries the plausible documents and the one icon; a banner and a
    picture the size of a decompression bomb are shapes, not documents, and a
    shape belongs next to the rule it exercises rather than in a directory that
    two CI jobs walk file by file.
    """
    path = tmp_path / name
    with Image.new("L", size, color=200) as picture:
        picture.save(path)
    return str(path)


def _declares(tmp_path: Path, name: str, width: int, height: int) -> str:
    """A PNG whose header claims a size its five bytes of pixel data cannot hold.

    This is the decompression bomb in its honest form, and it is the only way to
    assert that nothing was decoded: the pixel data is deliberately garbage, so a
    verdict of skipped(too_large) can only have come from the header. Writing a
    real fifty megapixel file instead would prove the same rule and would also
    allocate the very memory the rule exists to prevent.
    """

    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    # Width, height, eight bits per channel, colour type 0 (greyscale), and the
    # three zeroes for compression, filter and interlace.
    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    path = tmp_path / name
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", b"nope") + chunk(b"IEND", b""))
    return str(path)


def _folded(text: str) -> str:
    """The text the way the German analyzer chain ends up seeing a word.

    Measured in the shipping image on 2026-09-01: tesseract 5.5.0 reads the
    headline of ``19-uebermittlung.tif`` as "Ubermittlungsprotokoll", without the
    two dots over the first letter. The four lower case umlauts of the other
    corpus pictures come back intact; it is the capital one in a large headline
    that loses them.

    Asserting the raw glyph anyway would be exactly the test pitfall 8 of the
    phase research warns against: a comparison against the OCR raw text is a test
    against the tesseract version and goes red at the next Debian point release.
    What the product promises is findability, and there the difference does not
    exist: the Snowball stemmer of the German chain drops the umlaut accent in its
    postlude, so both spellings land on the same token. This folding is that step,
    and nothing beyond it, so a word the engine did not read still fails.
    """
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(sign for sign in decomposed if not unicodedata.combining(sign))


def _handed_over(engine: _Engine, number: int = 0) -> Image.Image:
    """The picture the engine was actually given, decoded back out of the pipe."""
    payload = engine.calls[number]["input"]
    assert isinstance(payload, bytes)
    return Image.open(BytesIO(payload))


@needs_engine
@pytest.mark.parametrize(
    ("name", "term"),
    [
        ("17-beleg.jpg", "Zahlungsavis"),
        ("18-aushang.png", "Sperrmüllabfuhr"),
        ("19-uebermittlung.tif", "Übermittlungsprotokoll"),
        ("20-rueckruf.webp", "Rückrufbitte"),
        ("21-sendebericht.tif", "Sendebericht"),
    ],
)
def test_a_photographed_document_becomes_the_terms_the_corpus_promises(name: str, term: str) -> None:
    # D-05 at the level of the module, over all four formats the allowlist opens
    # plus the multi frame file. Each of these words stands in exactly one file of
    # the corpus and exists there only as pixels, so a hit is proof that the
    # engine read them. WebP is in the list although measurement 4 of docs/ocr.md
    # showed that leptonica reads it directly: the detour through Pillow is about
    # EXIF rotation, the bomb guard and the caps, not about readability.
    outcome = image.extract_image(str(CORPUS / name))

    assert outcome.state is State.INDEXED
    assert _folded(term) in _folded(outcome.text)


def test_an_icon_under_the_minimum_edge_is_skipped_image_not_ocrable(monkeypatch: pytest.MonkeyPatch) -> None:
    # 48 by 48 pixels. There is no heuristic that tells a photographed document
    # from a holiday picture, but there is one that tells both from an avatar, and
    # this is it. The empty call list is half the assertion: the point of the cap
    # is that the engine is never started.
    engine = _install_engine(monkeypatch, _page("nie erreicht"))

    outcome = image.extract_image(ICON)

    assert outcome.state is State.SKIPPED
    assert outcome.reason is Reason.IMAGE_NOT_OCRABLE
    assert engine.calls == []


def test_a_banner_over_the_aspect_ratio_is_skipped_image_not_ocrable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 4000 by 400 is a ratio of ten, so a page divider, a panorama or a header
    # graphic. Long enough to pass the minimum edge, which is exactly why the
    # second rule exists next to the first.
    engine = _install_engine(monkeypatch, _page("nie erreicht"))

    outcome = image.extract_image(_drawn(tmp_path, "banner.png", (4000, 400)))

    assert outcome.state is State.SKIPPED
    assert outcome.reason is Reason.IMAGE_NOT_OCRABLE
    assert engine.calls == []


def test_a_picture_over_the_pixel_cap_is_too_large_without_being_decoded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Four hundred megapixels declared in eighty bytes. Pillow refuses this one
    # itself, because MAX_IMAGE_PIXELS is set to our own budget and not to None,
    # and the branch turns that refusal into a verdict instead of into a failure
    # (T-03-1001).
    engine = _install_engine(monkeypatch, _page("nie erreicht"))

    outcome = image.extract_image(_declares(tmp_path, "bombe.png", 20_000, 20_000))

    assert outcome.state is State.SKIPPED
    assert outcome.reason is Reason.TOO_LARGE
    assert engine.calls == []


def test_a_picture_just_over_the_pixel_cap_is_too_large_as_well(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Fifty six megapixels: over our cap and under the doubled one at which
    # Pillow raises by itself, so this is the range only our own check covers.
    # Pillow warns here, and the warning is the reason the check reads the header
    # rather than trusting the library to stop everything.
    engine = _install_engine(monkeypatch, _page("nie erreicht"))
    oversized = _declares(tmp_path, "riesig.png", 8000, 7000)

    with pytest.warns(Image.DecompressionBombWarning):
        outcome = image.extract_image(oversized)

    assert outcome.state is State.SKIPPED
    assert outcome.reason is Reason.TOO_LARGE
    assert engine.calls == []


def test_exif_rotated_photo_is_uprighted(monkeypatch: pytest.MonkeyPatch) -> None:
    # 260 by 1000 on disk, orientation 6 in the header, so 1000 by 260 the way a
    # human holds it. Without the transpose the page reaches tesseract turned by
    # ninety degrees and the result is character salad, which is a defect no
    # verdict would ever show.
    engine = _install_engine(monkeypatch, _page("Lieferschein"))

    image.extract_image(SIDEWAYS)

    with _handed_over(engine) as handed:
        assert handed.size == (1000, 260)
        # And in one channel, for the same reason the rasteriser uses one:
        # tesseract binarises internally either way.
        assert handed.mode == "L"


def test_a_large_photo_is_scaled_down_to_the_target_edge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A phone photograph costs as much as an A4 page at 300 dpi and not more.
    # Twenty megapixels in, three and a half thousand pixels on the long edge out.
    engine = _install_engine(monkeypatch, _page("Lieferschein"))

    image.extract_image(_drawn(tmp_path, "foto.png", (5000, 4000)))

    with _handed_over(engine) as handed:
        assert max(handed.size) == 3500
        assert handed.size == (3500, 2800)


def test_a_multi_frame_tiff_is_read_to_the_page_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    # A fax archive in one file. It gets the page cap of a PDF, because a cap that
    # a second container format walks around is not a cap (T-03-1004), and the cut
    # is visible as truncated rather than as a quietly thin document (D-08).
    monkeypatch.setenv("FINDLING_OCR_MAX_PAGES", "2")
    engine = _install_engine(monkeypatch, _page("Sendebericht"))

    outcome = image.extract_image(FAX)

    assert outcome.state is State.INDEXED
    assert outcome.reason is Reason.TRUNCATED
    assert len(engine.calls) == 2
    assert "Seite 0" in outcome.text
    assert "Seite 1" in outcome.text


def test_all_frames_of_a_multi_frame_tiff_are_read_under_the_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _install_engine(monkeypatch, _page("Sendebericht"))

    outcome = image.extract_image(FAX)

    # Three frames, three calls, and no truncation: the cut above was the cap and
    # not the file.
    assert outcome.state is State.INDEXED
    assert outcome.reason is None
    assert len(engine.calls) == 3


def test_a_lost_frame_of_a_multi_frame_tiff_is_visible_as_truncated(monkeypatch: pytest.MonkeyPatch) -> None:
    # The picture half of review finding WR-03: a fax archive that lost its
    # middle page to the page timeout is a partial result, and D-08 wants a
    # partial result visible as one instead of quietly thin.
    def answers(number: int) -> _Finished:
        if number == 1:
            raise subprocess.TimeoutExpired(cmd="tesseract", timeout=30)
        return _Finished(stdout=f"Sendebericht, Seite {number} von drei\n".encode())

    engine = _install_engine(monkeypatch, answers)

    outcome = image.extract_image(FAX)

    assert outcome.state is State.INDEXED
    assert outcome.reason is Reason.TRUNCATED
    assert outcome.truncated is True
    assert "Seite 0" in outcome.text
    assert "Seite 2" in outcome.text
    assert len(engine.calls) == 3


def test_a_picture_under_the_character_threshold_is_skipped_empty_text(monkeypatch: pytest.MonkeyPatch) -> None:
    # The real answer to D-05, and the reason the plausibility rules may stay as
    # coarse as they are: a holiday picture is allowed to cost an engine call, it
    # is not allowed to enter the index. The caller records that OCR ran, so the
    # time it took stays visible on the status page of phase 4.
    _install_engine(monkeypatch, lambda number: _Finished(stdout=b"Strand\n"))

    outcome = image.extract_image(SLIP)

    assert outcome.state is State.SKIPPED
    assert outcome.reason is Reason.EMPTY_TEXT
    assert outcome.text == ""


def test_a_picture_without_an_engine_is_failed_ocr_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def answers(number: int) -> _Finished:
        raise FileNotFoundError(2, "No such file or directory: 'tesseract'")

    _install_engine(monkeypatch, answers)

    outcome = image.extract_image(SLIP)

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.OCR_UNAVAILABLE


def test_a_picture_that_kills_the_engine_is_failed_ocr_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    # 134 is what a page that burst the address space looks like from here
    # (measurement 5 of docs/ocr.md). The picture branch reaches the same verdict
    # as the scan branch, because it is the same engine behind the same call.
    _install_engine(monkeypatch, lambda number: _Finished(returncode=134, stderr=b"std::bad_alloc"))

    outcome = image.extract_image(SLIP)

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.OCR_FAILED


def test_a_picture_over_the_time_cap_ends_as_failed_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def answers(number: int) -> _Finished:
        raise subprocess.TimeoutExpired(cmd="tesseract", timeout=30)

    _install_engine(monkeypatch, answers)

    outcome = image.extract_image(SLIP)

    # One frame, and it was lost: nothing was read at all, so this is a failure
    # and not a thin document.
    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.TIMEOUT


def test_a_file_that_is_not_a_picture_becomes_a_verdict_instead_of_an_exception(tmp_path: Path) -> None:
    broken = tmp_path / "kaputt.png"
    broken.write_bytes(b"\x89PNG\r\n\x1a\nand then nothing that parses")

    outcome = image.extract_image(str(broken))

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.CORRUPT


def test_image_file_is_unchanged_after_ocr() -> None:
    # The same invariant the read only gate measures from the outside, asserted at
    # the module that opens the file. No stand in and no skip mark, for the reason
    # the PDF counterpart above gives: inside the container this runs the real
    # engine, on the development machine it ends as ocr_unavailable, and the file
    # must be untouched on both paths (IDX-07, T-03-805).
    before = hashlib.sha256(Path(SLIP).read_bytes()).hexdigest()
    stat_before = Path(SLIP).stat()

    image.extract_image(SLIP)

    assert hashlib.sha256(Path(SLIP).read_bytes()).hexdigest() == before
    assert Path(SLIP).stat().st_size == stat_before.st_size
    assert Path(SLIP).stat().st_mtime == stat_before.st_mtime


def test_a_picture_mimetype_takes_the_ocr_route_through_the_picture_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The second way into the OCR route, and the first one that is a property of
    # the file rather than of the job: since plan 03-10 the four picture types are
    # in the allowlist. Which of the two decoders opens the file is decided by the
    # mimetype, because the route alone cannot say whether pdfium or Pillow is the
    # right one.
    engine = _install_engine(monkeypatch, _page("Zahlungsavis"))

    outcome = dispatch.extract(SLIP, "image/jpeg", Path(SLIP).stat().st_size)

    assert outcome.state is State.INDEXED
    assert "Zahlungsavis" in outcome.text
    assert len(engine.calls) == 1
    with _handed_over(engine) as handed:
        # The picture itself and not a rasterised PDF page, so the branch really
        # went through Pillow.
        assert handed.size == (1000, 260)


def test_an_icon_is_refused_by_the_route_and_not_only_by_the_module(monkeypatch: pytest.MonkeyPatch) -> None:
    # The cap has to hold where files actually arrive. An icon reaches the
    # dispatcher as image/png like every other picture, and it must leave it as a
    # verdict without an engine call (T-03-1002).
    engine = _install_engine(monkeypatch, _page("nie erreicht"))

    outcome = dispatch.extract(ICON, "image/png", Path(ICON).stat().st_size)

    assert outcome.state is State.SKIPPED
    assert outcome.reason is Reason.IMAGE_NOT_OCRABLE
    assert engine.calls == []


def test_a_forced_ocr_job_on_a_pdf_still_reaches_the_scan_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    # The other side of the same decision: the OCR track of plan 03-09 hands over
    # scanned PDFs, and those must not end up in the picture branch now that the
    # route is shared. The rasterised A4 page at 300 dpi is the proof.
    monkeypatch.setenv("FINDLING_OCR_MAX_PAGES", "1")
    engine = _install_engine(monkeypatch, _page("Ratsvorlage"))

    dispatch.extract(SCAN, "application/pdf", 4096, Route.OCR)

    with _handed_over(engine) as handed:
        assert handed.size == (2480, 3509)


def test_the_picture_caps_are_named_constants_and_the_bomb_guard_is_set() -> None:
    # Every cap of pitfall 6 with the start value the research names, read off the
    # module rather than off a literal in a comparison. The last line is the one
    # that matters most: the widespread advice is to switch MAX_IMAGE_PIXELS off,
    # and switching it off removes exactly the bomb guard this branch needs.
    assert image._MIN_LONG_EDGE_PIXELS == 640
    assert image._MAX_ASPECT_RATIO == 8
    assert image._MAX_PIXELS == 50_000_000
    assert image._MAX_EDGE_PIXELS == 3500
    assert image._MIN_OCR_CHARS == 20
    assert Image.MAX_IMAGE_PIXELS == image._MAX_PIXELS


# ---------------------------------------------------------------------------
# The TIFF variants of #18 (plan 29-07, D-29-06). Every file below is built in
# the test from a Pillow TIFF and a byte patch of one tag, so no binary lands in
# the repository and the exact variant is readable in the helper that makes it.
# ---------------------------------------------------------------------------

# TIFF field types and their byte width, for the two helpers that walk an IFD.
_TIFF_TYPE_BYTES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}

# The struct codes of the types whose values change with the byte order.
_TIFF_TYPE_CODES = {3: "H", 4: "I", 5: "II", 8: "h", 9: "i", 10: "ii", 11: "f", 12: "d"}

# The grey value every variant is drawn with, and therefore the one the engine
# has to be handed back.
_GREY = 200

# Over the minimum edge, under the aspect ratio cap: a plausible document.
_VARIANT_SIZE = (800, 600)

_TAG_EXTRA_SAMPLES = 338
_TAG_SAMPLE_FORMAT = 339


def _ifd_entries(data: bytes) -> Iterator[tuple[int, int, int, int]]:
    """Every SHORT entry of every IFD as (entry offset, tag, count, value offset)."""
    order = "<" if data[:2] == b"II" else ">"
    (ifd,) = struct.unpack_from(order + "I", data, 4)
    while ifd:
        (count,) = struct.unpack_from(order + "H", data, ifd)
        for number in range(count):
            entry = ifd + 2 + 12 * number
            tag, kind, values = struct.unpack_from(order + "HHI", data, entry)
            if kind != 3:
                continue
            at = entry + 8 if 2 * values <= 4 else struct.unpack_from(order + "I", data, entry + 8)[0]
            yield entry, tag, values, at
        (ifd,) = struct.unpack_from(order + "I", data, ifd + 2 + 12 * count)


def _retagged(data: bytes, tag: int, value: int) -> bytes:
    """The same TIFF with every value of one SHORT tag set to ``value``, in every IFD."""
    order = "<" if data[:2] == b"II" else ">"
    patched = bytearray(data)
    hits = 0
    for _entry, found, values, at in _ifd_entries(data):
        if found != tag:
            continue
        for number in range(values):
            struct.pack_into(order + "H", patched, at + 2 * number, value)
        hits += 1
    assert hits, f"tag {tag} is not in the file"
    return bytes(patched)


def _big_endian(data: bytes) -> bytes:
    """A little endian TIFF rewritten as big endian, structure only.

    Pillow writes II on this platform whatever it is asked, and the file of #18
    was MM. Every sample of the variants here is eight bits wide, and LZW and
    Deflate streams are byte streams, so the pixel data stays as it is; only the
    header, the IFDs and the values they point to change their order.
    """
    assert data[:4] == b"II*\x00"
    turned = bytearray(data)
    turned[:4] = b"MM\x00*"
    (ifd,) = struct.unpack_from("<I", data, 4)
    struct.pack_into(">I", turned, 4, ifd)
    while ifd:
        (count,) = struct.unpack_from("<H", data, ifd)
        struct.pack_into(">H", turned, ifd, count)
        for number in range(count):
            entry = ifd + 2 + 12 * number
            tag, kind, values = struct.unpack_from("<HHI", data, entry)
            struct.pack_into(">HHI", turned, entry, tag, kind, values)
            if _TIFF_TYPE_BYTES[kind] * values <= 4:
                at = entry + 8
            else:
                (at,) = struct.unpack_from("<I", data, entry + 8)
                struct.pack_into(">I", turned, entry + 8, at)
            code = _TIFF_TYPE_CODES.get(kind)
            if code is None:
                continue
            width = struct.calcsize("<" + code)
            for value in range(values):
                where = at + width * value
                struct.pack_into(">" + code, turned, where, *struct.unpack_from("<" + code, data, where))
        following = ifd + 2 + 12 * count
        (ifd,) = struct.unpack_from("<I", data, following)
        struct.pack_into(">I", turned, following, ifd)
    return bytes(turned)


def _tiff(mode: str, compression: str = "raw", *, sample_format: bool = False) -> bytes:
    """A plain TIFF of the variant size, with an explicit SampleFormat tag on request."""
    bands = Image.getmodebands(mode)
    colour: int | tuple[int, ...] = _GREY if bands == 1 else (_GREY,) * bands
    if mode == "LA":
        colour = (_GREY, 255)
    options: dict[str, object] = {"compression": compression}
    if sample_format:
        info = TiffImagePlugin.ImageFileDirectory_v2()
        info[_TAG_SAMPLE_FORMAT] = (1,) * bands
        info.tagtype[_TAG_SAMPLE_FORMAT] = 3
        options["tiffinfo"] = info
    sink = BytesIO()
    with Image.new(mode, _VARIANT_SIZE, color=colour) as picture:
        picture.save(sink, format="TIFF", **options)
    return sink.getvalue()


def _in_order(data: bytes, order: str) -> bytes:
    return _big_endian(data) if order == "MM" else data


def _written(tmp_path: Path, name: str, data: bytes) -> str:
    path = tmp_path / name
    path.write_bytes(data)
    return str(path)


_COMPRESSIONS = ("raw", "tiff_lzw", "tiff_adobe_deflate")
_COMPRESSED = ("tiff_lzw", "tiff_adobe_deflate")
_ORDERS = ("II", "MM")


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("compression", _COMPRESSIONS)
@pytest.mark.parametrize("extra", [0, 1])
def test_a_grey_tiff_with_an_extra_channel_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, extra: int, compression: str, order: str
) -> None:
    # The file of #18: grey plus one extra channel declared as unspecified (0)
    # or associated alpha (1). Pillow 12.3.0 only maps the unassociated alpha of
    # value 2, so without the shim this is UnidentifiedImageError and was booked
    # as a broken file.
    engine = _install_engine(monkeypatch, _page("Grauwert"))
    data = _in_order(_retagged(_tiff("LA", compression), _TAG_EXTRA_SAMPLES, extra), order)

    outcome = image.extract_image(_written(tmp_path, "grau.tif", data))

    assert outcome.state is State.INDEXED
    with _handed_over(engine) as handed:
        assert handed.mode == "L"
        assert handed.getpixel((5, 5)) == _GREY


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("mode", ["L", "RGB"])
def test_an_uncompressed_tiff_with_sample_format_zero_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, order: str
) -> None:
    # SampleFormat 0 is not in the specification, and 1 is its default. Read as
    # the default, the pixels are exactly the ones drawn.
    engine = _install_engine(monkeypatch, _page("Grauwert"))
    data = _in_order(_retagged(_tiff(mode, sample_format=True), _TAG_SAMPLE_FORMAT, 0), order)

    outcome = image.extract_image(_written(tmp_path, "sf0.tif", data))

    assert outcome.state is State.INDEXED
    with _handed_over(engine) as handed:
        assert handed.getpixel((5, 5)) == _GREY


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("compression", _COMPRESSED)
def test_sf0_compressed_probe(compression: str, order: str) -> None:
    # The probe of D-29-06(b), kept as a test so that its answer stays checked:
    # can a compressed SampleFormat 0 file be read when the tag says 1 before
    # libtiff sees it? Libtiff rejects the value 0 itself ("Bad value 0 for
    # SampleFormat"), and it reads the tags from the bytes, not from Pillow.
    # The shim is in place here, because the module is imported: without it the
    # open alone would already fail.
    data = _in_order(_retagged(_tiff("L", compression, sample_format=True), _TAG_SAMPLE_FORMAT, 0), order)

    # Way (i): set the tag in the opened picture and load. Libtiff never sees
    # the change, so the load dies at the decoder. If this ever starts to work,
    # the buffer copy of way (ii) can be retired.
    with Image.open(BytesIO(data)) as picture:
        assert isinstance(picture, TiffImagePlugin.TiffImageFile)
        picture.tag_v2[_TAG_SAMPLE_FORMAT] = (1,)
        picture.tag[_TAG_SAMPLE_FORMAT] = (1,)
        with pytest.raises(OSError, match="decoder error -2"):
            picture.load()

    # Way (ii): patch the value in a buffer and open the buffer. Correct pixels.
    with Image.open(BytesIO(_retagged(data, _TAG_SAMPLE_FORMAT, 1))) as picture:
        picture.load()
        assert picture.getpixel((5, 5)) == _GREY


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("compression", _COMPRESSED)
def test_a_compressed_tiff_with_sample_format_zero_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, compression: str, order: str
) -> None:
    # Way (ii) of the probe, as the product does it.
    engine = _install_engine(monkeypatch, _page("Grauwert"))
    data = _in_order(_retagged(_tiff("L", compression, sample_format=True), _TAG_SAMPLE_FORMAT, 0), order)
    path = _written(tmp_path, "sf0.tif", data)

    outcome = image.extract_image(path)

    assert outcome.state is State.INDEXED
    with _handed_over(engine) as handed:
        assert handed.getpixel((5, 5)) == _GREY
    # The buffer was patched, the file was not (IDX-07).
    assert Path(path).read_bytes() == data


def test_a_compressed_sample_format_zero_tiff_over_the_buffer_cap_is_an_honest_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The patched copy lives in memory next to the decoded picture (T-29-23b).
    # Over the cap there is no copy, and no decoder error either: the verdict.
    engine = _install_engine(monkeypatch, _page("nie erreicht"))
    monkeypatch.setattr(image, "_SF0_PATCH_MAX_BYTES", 16)
    data = _retagged(_tiff("L", "tiff_lzw", sample_format=True), _TAG_SAMPLE_FORMAT, 0)

    outcome = image.extract_image(_written(tmp_path, "sf0.tif", data))

    assert outcome.state is State.SKIPPED
    assert outcome.reason is Reason.UNSUPPORTED_VARIANT
    assert engine.calls == []


def test_a_sample_format_patch_never_reaches_outside_the_buffer() -> None:
    # A value offset that points past the end of the file is a broken file, and
    # the patch answers it with None instead of writing anywhere (T-29-23b).
    # RGB, so the three values do not fit into the entry and it holds an offset.
    data = bytearray(_retagged(_tiff("RGB", sample_format=True), _TAG_SAMPLE_FORMAT, 0))
    entry = next(entry for entry, tag, _values, _at in _ifd_entries(bytes(data)) if tag == _TAG_SAMPLE_FORMAT)
    struct.pack_into("<I", data, entry + 8, len(data) + 100)

    assert image._normalise_sample_format(bytearray(data)) is False


@pytest.mark.parametrize("mode", ["I;16", "RGB"])
def test_a_float_tiff_is_an_unsupported_variant_and_not_corrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    # SampleFormat 3 is floating point. Read as integers its bits are noise, so
    # it is never normalised (T-29-23); the half float grey of #18 and an eight
    # bit float RGB both get the honest verdict.
    engine = _install_engine(monkeypatch, _page("nie erreicht"))
    data = _retagged(_tiff(mode, sample_format=True), _TAG_SAMPLE_FORMAT, 3)

    outcome = image.extract_image(_written(tmp_path, "float.tif", data))

    assert outcome.state is State.SKIPPED
    assert outcome.reason is Reason.UNSUPPORTED_VARIANT
    assert engine.calls == []


def test_a_tiff_with_a_broken_ifd_is_corrupt_with_the_class(tmp_path: Path) -> None:
    # The TIFF magic and then garbage: a broken file, not a variant.
    outcome = image.extract_image(_written(tmp_path, "kaputt.tif", b"II*\x00" + b"\xff" * 64))

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.CORRUPT
    assert outcome.detail == "PIL.UnidentifiedImageError"


def test_garbage_without_any_magic_is_corrupt(tmp_path: Path) -> None:
    outcome = image.extract_image(_written(tmp_path, "muell.tif", b"nothing a decoder knows" * 8))

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.CORRUPT


def _pristine_open_info() -> dict[tuple[object, ...], tuple[str, str]]:
    """OPEN_INFO as Pillow ships it, read in a fresh interpreter that never saw the shim."""
    answer = subprocess.run(
        [sys.executable, "-c", "from PIL import TiffImagePlugin as T; print(repr(sorted(T.OPEN_INFO.items())))"],
        capture_output=True,
        check=True,
        text=True,
        timeout=60,
    )
    return dict(ast.literal_eval(answer.stdout))


def test_the_shim_adds_only_keys_pillow_does_not_ship() -> None:
    pristine = _pristine_open_info()

    assert image._SHIM_KEYS
    for key in image._SHIM_KEYS:
        assert key not in pristine, f"Pillow ships this key now, check and retire the shim: {key!r}"
        assert key in TiffImagePlugin.OPEN_INFO


def test_the_shim_changes_no_entry_pillow_ships() -> None:
    pristine = _pristine_open_info()

    for key, value in pristine.items():
        assert TiffImagePlugin.OPEN_INFO[key] == value


def _photo(tmp_path: Path, name: str, size: tuple[int, int], mode: str = "RGB", orientation: int = 6) -> str:
    """A uniform JPEG of a given size with an EXIF orientation, the shape of a phone photo."""
    exif = Image.Exif()
    exif[0x0112] = orientation
    path = tmp_path / name
    colour = (_GREY,) * Image.getmodebands(mode)
    with Image.new(mode, size, color=colour) as picture:
        picture.save(path, format="JPEG", exif=exif.tobytes(), quality=50)
    return str(path)


# The camera class of #18: 45 megapixels, under the pixel cap, over the edge.
_CAMERA = (8192, 5464)


def test_the_draft_target_keeps_the_aspect_ratio() -> None:
    # (3500, 3500) would give min(8192 // 3500, 5464 // 3500) = 1, so libjpeg
    # would not reduce at all. The target the picture really ends at gives 2.
    assert image._draft_target(*_CAMERA) == (3500, 2334)
    assert image._draft_target(*reversed(_CAMERA)) == (2334, 3500)


@pytest.mark.parametrize("mode", ["RGB", "CMYK"])
def test_a_large_jpeg_is_decoded_reduced_before_it_is_loaded(tmp_path: Path, mode: str) -> None:
    path = _photo(tmp_path, "kamera.jpg", _CAMERA, mode)

    with Image.open(path) as picture:
        image._decode_smaller(picture)

        # Still only the header: the tiles are not decoded yet.
        assert picture.tile
        assert picture.size == (4096, 2732)
        # libjpeg can hand out grey from colour, but CMYK stays CMYK.
        assert picture.mode == ("L" if mode == "RGB" else "CMYK")


@pytest.mark.parametrize("mode", ["RGB", "CMYK"])
def test_a_large_rotated_jpeg_reaches_the_engine_upright_and_scaled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    engine = _install_engine(monkeypatch, _page("Kamerafoto"))

    outcome = image.extract_image(_photo(tmp_path, "kamera.jpg", _CAMERA, mode))

    assert outcome.state is State.INDEXED
    with _handed_over(engine) as handed:
        assert handed.size == (2334, 3500)
        assert handed.mode == "L"


def test_a_small_jpeg_is_not_drafted(monkeypatch: pytest.MonkeyPatch) -> None:
    # Under the target edge there is nothing to reduce, and the picture reaches
    # the engine exactly as before plan 29-07.
    calls: list[object] = []
    original = JpegImagePlugin.JpegImageFile.draft

    def spy(
        picture: JpegImagePlugin.JpegImageFile, mode: str | None, size: tuple[int, int] | None
    ) -> tuple[str, tuple[int, int, float, float]] | None:
        calls.append(size)
        return original(picture, mode, size)

    monkeypatch.setattr(JpegImagePlugin.JpegImageFile, "draft", spy)
    engine = _install_engine(monkeypatch, _page("Zahlungsavis"))

    image.extract_image(SLIP)

    assert calls == []
    with _handed_over(engine) as handed:
        assert handed.size == (1000, 260)


def test_every_frame_of_a_rotated_multi_frame_tiff_is_upright(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Pitfall 10: the rotation now works on the open picture in place, so the
    # next frame has to arrive fresh after the seek, with its own orientation
    # and its own size. The reference is the copy the branch made before plan
    # 29-07, frame by frame; the two frames differ in size and pattern, so a
    # leftover of the first one in the second call would show.
    engine = _install_engine(monkeypatch, _page("Faxseite"))
    path = tmp_path / "fax.tif"
    first = Image.new("L", (1000, 700), color=255)
    second = Image.new("L", (900, 700), color=255)
    try:
        first.paste(0, (0, 0, 500, 700))
        second.paste(0, (0, 0, 900, 200))
        first.save(path, format="TIFF", save_all=True, append_images=[second], tiffinfo={0x0112: 6})
    finally:
        first.close()
        second.close()

    references: list[bytes] = []
    sizes: list[tuple[int, int]] = []
    with Image.open(path) as written:
        assert getattr(written, "n_frames", 1) == 2
        for number in range(2):
            written.seek(number)
            assert written.getexif().get(0x0112) == 6
            with ImageOps.exif_transpose(written) as copy, copy.convert("L") as grey:
                references.append(grey.tobytes())
                sizes.append(grey.size)

    outcome = image.extract_image(str(path))

    assert outcome.state is State.INDEXED
    assert sizes[0] != sizes[1]
    for number in range(2):
        with _handed_over(engine, number) as handed:
            assert handed.size == sizes[number]
            assert handed.tobytes() == references[number]


def test_a_picture_over_the_free_address_space_is_out_of_memory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A small artificial cap stands in for RLIMIT_AS minus VmSize, which only a
    # Linux child has. Over it, the verdict says memory and not broken (D-29-07).
    engine = _install_engine(monkeypatch, _page("nie erreicht"))
    monkeypatch.setattr(image, "_address_space_room", lambda: 1_000_000)

    outcome = image.extract_image(_photo(tmp_path, "kamera.jpg", _CAMERA))

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.OUT_OF_MEMORY
    assert outcome.detail == "findling.extract.image.HeaderEstimate"
    assert engine.calls == []


def test_the_estimate_counts_the_picture_after_the_draft(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 4096 by 2732 in one channel, twice: just under 22.4 million bytes. A room
    # of 23 million is enough, which it would not be for the undrafted colour
    # picture of 8192 by 5464 in four bytes a pixel.
    engine = _install_engine(monkeypatch, _page("Kamerafoto"))
    monkeypatch.setattr(image, "_address_space_room", lambda: 23_000_000)

    outcome = image.extract_image(_photo(tmp_path, "kamera.jpg", _CAMERA))

    assert outcome.state is State.INDEXED
    assert len(engine.calls) == 1


def test_without_a_readable_cap_there_is_no_estimate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _install_engine(monkeypatch, _page("Grauwert"))
    monkeypatch.setattr(image, "_address_space_room", lambda: None)

    outcome = image.extract_image(_drawn(tmp_path, "seite.png", (2000, 1500)))

    assert outcome.state is State.INDEXED
    assert len(engine.calls) == 1


def test_the_used_address_space_is_read_from_vmsize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    status = tmp_path / "status"
    status.write_text("Name:\tpython\nVmPeak:\t  9999 kB\nVmSize:\t  2048 kB\n")
    monkeypatch.setattr(image, "_PROC_STATUS", status)

    assert image._address_space_used() == 2048 * 1024


def test_without_a_status_file_the_used_address_space_is_unknown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(image, "_PROC_STATUS", tmp_path / "missing")

    assert image._address_space_used() is None


@pytest.mark.skipif(sys.platform != "win32", reason="the absence of RLIMIT_AS is a Windows property")
def test_on_windows_there_is_no_room_to_estimate_against() -> None:
    assert image._address_space_room() is None


def test_the_shim_maps_grey_with_an_extra_channel_to_la() -> None:
    # LA and not L;16B, which fails on the libtiff path, and not La, which does
    # not convert to L (pitfall 2 of the phase research).
    for order in (TiffImagePlugin.II, TiffImagePlugin.MM):
        for extra in (0, 1):
            assert TiffImagePlugin.OPEN_INFO[(order, 1, (1,), 1, (8, 8), (extra,))] == ("LA", "LA")
