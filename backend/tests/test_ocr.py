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
from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pypdfium2
import pytest
from PIL import Image

from findling.extract import raster

CORPUS = Path(__file__).resolve().parents[2] / "testdata" / "corpus"

# Three A4 pages of German council prose that exist only as pixels. The one term
# that stands in no other file of the corpus is Bebauungsplan.
SCAN = str(CORPUS / "13-ratsvorlage-scan.pdf")

# 14400 by 14400 points, the largest page the format allows. At 300 dpi that is
# 60000 pixels on an edge, or nine gigapixels in one channel.
HUGE = str(CORPUS / "31-riesenformat.pdf")

DPI = 300


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
        assert list(image.getdata()) == [10, 20, 30, 40, 50, 60]


def test_both_pdfium_objects_are_released_when_the_encoding_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    # The error path is where a close is forgotten, and over an initial index of
    # 100000 files inside a container with 4 GB a forgotten close is not a leak,
    # it is the end of the process. The order is asserted too: the bitmap is a
    # child of the page, so it goes first.
    closed: list[str] = []
    page_close: Callable[[pypdfium2.PdfPage], None] = pypdfium2.PdfPage.close
    bitmap_close: Callable[[pypdfium2.PdfBitmap], None] = pypdfium2.PdfBitmap.close

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
