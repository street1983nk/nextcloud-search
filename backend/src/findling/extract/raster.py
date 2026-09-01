"""One page of a PDF as a picture an OCR engine can read, and nothing else.

The order of questions is the same one :mod:`findling.extract.pdf` asks, because
it is the same engine underneath: how large is this page, at what scale may it be
drawn, and only then is a single page turned into pixels. The answer is handed
back as encoded bytes rather than as an image object, so the caller never holds a
second copy of the page in another representation.

**Why greyscale.** A4 at 300 dpi is 2480 by 3508 pixels. In one channel that is
8.7 MB, in BGRA it is 35 MB, and tesseract binarises internally with Otsu either
way, so the three extra channels are paid for and then thrown away. On the 4 GB
box this project targets, four times the peak for no gain is the difference
between a page that renders and a container that is killed.

**Why 300 dpi.** "Tesseract works best on images which have a DPI of at least
300 dpi". The value itself is not written here, it comes from the configuration,
where it is bounded to a measured range: the rasterised page grows with the
square of the resolution, so a dpi an admin typed by hand is a memory decision.

**Why the rows are cut.** pdfium pads every row of its bitmap to a stride that
may be wider than the page. Reading the buffer as one block shifts each row
against the one above it, which does not produce an error, it produces diagonal
stripes that still look like a scan. So the rows are sliced one by one, and the
guard against that mistake is a test with a deliberately padded bitmap.

**Why this module knows nothing about tesseract.** Rasterising is testable
without an OCR engine, and the development machine of this project has none.
Keeping the two apart is what lets the assertions about pixels run everywhere
instead of only inside the image, and a grep gate keeps this file free of any
child process at all.

Like every module of this package, this one never writes: it opens a document for
reading, and the original file is not touched even on the error path (IDX-07).
"""

from __future__ import annotations

from collections.abc import Buffer
from io import BytesIO
from typing import Final, Protocol

import pypdfium2
from PIL import Image

# PDF user space. A point is a seventy second of an inch, which is what turns a
# resolution into the scale factor pdfium expects.
_POINTS_PER_INCH: Final = 72

# The longest edge a rasterised page may have, whatever its size in points says.
#
# This is the guard against the PDF bomb, and it sits here rather than at
# RLIMIT_AS because the address space limit is the last stop, not the first one:
# a page that bursts it costs the whole job and a recycled child, while a page
# that is scaled down costs resolution on a document that has no business being
# 14400 points wide. The corpus carries exactly that file, and at a fixed 300 dpi
# it would render to 60000 pixels on an edge, or nine gigapixels in one channel.
#
# 5000 is chosen so that no ordinary format is touched: A4 at 300 dpi is 3508
# pixels on its long edge and A3 is 4961, so both are still drawn at full
# resolution. A page that does reach the cap is 25 MB in one channel, which
# leaves the rest of the extraction child's 512 MB to the encoder and to Python.
MAX_EDGE_PIXELS: Final = 5000

# The picture is written to a pipe and read once, it is never stored. Compressing
# it hard would spend CPU on bytes that live for milliseconds, and tesseract
# decodes both the same way.
_PNG_COMPRESS_LEVEL: Final = 1


class _Bitmap(Protocol):
    """The four properties of a pdfium bitmap this module actually depends on.

    Named rather than taken as given, because the padding of ``stride`` is the
    whole difficulty of the encoder below and a test needs to be able to build a
    padded bitmap without a PDF that produces one.
    """

    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...

    @property
    def stride(self) -> int: ...

    @property
    def buffer(self) -> Buffer: ...


def render_page_png(document: pypdfium2.PdfDocument, number: int, *, dpi: int) -> bytes:
    """One page as an encoded greyscale PNG, with both C resources released.

    The nesting of the two ``finally`` blocks is the point, and it is the pattern
    of ``pdf._page_text``: whatever happens inside, the bitmap is closed before
    the page and the page is closed before the caller sees the exception. Over an
    initial index of 100000 files a forgotten close is not a leak, it is the end
    of the process, and the error path is where it gets forgotten.
    """
    page = document[number]
    try:
        # pypdfium2 carries no type information, so pyright reads the type of
        # scale off its default value of 1 and then refuses the float this
        # function computes. A whole page at scale 1 would be 72 dpi.
        bitmap = page.render(
            scale=_scale_for(page, dpi),  # pyright: ignore[reportArgumentType]
            grayscale=True,
            draw_annots=False,
        )
        try:
            return _encode_page(bitmap)
        finally:
            bitmap.close()
    finally:
        page.close()


def _scale_for(page: pypdfium2.PdfPage, dpi: int) -> float:
    """The requested resolution, or as much of it as the edge cap allows."""
    longest = max(page.get_width(), page.get_height())
    if longest <= 0:
        # A page without an extent. pdfium would still draw a minimal bitmap;
        # asking it for a scale computed from zero would not.
        return 1.0
    return min(dpi / _POINTS_PER_INCH, MAX_EDGE_PIXELS / longest)


def _encode_page(bitmap: _Bitmap) -> bytes:
    """The bitmap as PNG bytes, with every padded row cut back to the page width.

    ``Image.frombytes`` over the sliced rows, never over the raw block: the rows
    are padded to ``stride``, and the shortcut is the rasterising bug that still
    produces a plausible looking image.
    """
    raw = bytes(bitmap.buffer)
    width, height, stride = bitmap.width, bitmap.height, bitmap.stride
    # Measured: an A4 page at 300 dpi comes back unpadded, so the slicing is the
    # exception and not the rule. The unpadded case keeps the raw block, because
    # the join would copy 8.7 MB a second time to produce the same bytes.
    padded = stride != width
    rows = b"".join(raw[start : start + width] for start in range(0, stride * height, stride)) if padded else raw

    sink = BytesIO()
    image = Image.frombytes("L", (width, height), rows)
    try:
        image.save(sink, format="PNG", compress_level=_PNG_COMPRESS_LEVEL)
    finally:
        image.close()
    return sink.getvalue()
