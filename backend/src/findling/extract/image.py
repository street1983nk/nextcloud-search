"""A picture as text, with an honest statement about what the caps in front can do.

There is no heuristic that separates a photographed set of minutes from a beach
picture without reading both, and pretending there is one would be the worse
answer. What the rules below really do is two things: they sort out what is
certainly not a document, and they cap the cost. Icons, avatars, banners and
preview thumbnails never reach the engine; a phone photograph is scaled down to
what an A4 page at 300 dpi costs; a picture that declares more pixels than the
extraction child could ever hold is a verdict instead of a memory death.

**The real answer to D-05 is the postcondition, not the preconditions.** A
holiday picture is allowed to cost one engine call. It is not allowed to enter
the index, so a run that comes back under the character threshold is
skipped(empty_text) while the caller still records that OCR ran. The two together
are what lets phase 4 say how much time went into files that are not searchable,
instead of hiding it behind a cap that pretends to be clever.

**Why the detour through Pillow at all.** Measurement 4 of ``docs/ocr.md`` showed
that the leptonica 1.84.1 of this image is built against libwebp and reads WebP,
TIFF and PNG from stdin byte for byte alike, so "otherwise it would not work at
all" is not the reason and is written down here as refuted. The reasons that
remain are the ones this module is made of: the EXIF rotation, the bomb guard
over ``Image.MAX_IMAGE_PIXELS``, the downscale and the plausibility rules all
need a look into the header before tesseract is started.

The engine itself is not called here. :mod:`findling.extract.ocr` owns the one
measured call form, and a second call site is a call form that drifts; this
module hands it an encoded page and reads its verdicts. That import costs pdfium
in a child that may only ever see pictures, which is the honest price of having
exactly one place where this project talks to tesseract.

Like every module of this package, this one never writes: the file is opened for
reading, every rotation and every scaling happens on a copy in memory, and the
original is not touched even on the error path (IDX-07, T-03-805).
"""

from __future__ import annotations

import time
from io import BytesIO
from typing import Final

from PIL import Image, ImageOps

from findling import config
from findling.config import Settings
from findling.extract import ocr
from findling.extract.dispatch import cap_text
from findling.extract.errors import ExtractionOutcome, Reason

# The bomb guard, in pixels, and the cost ceiling of this branch at the same
# time. Fifty megapixels is far above any scanner and above every phone camera
# this decade, and a picture that claims more of them in a few kilobytes is the
# classic decompression bomb (T-03-1001).
_MAX_PIXELS: Final = 50_000_000

# Pillow is told the same number, deliberately, and never told None. Switching
# the check off is the widespread advice and it removes exactly the guard this
# branch needs; setting it to our own budget keeps it and makes it ours. Pillow
# warns from this value on and raises at twice it, so both halves of the range
# are covered: the warning is caught by the explicit check below, the error by
# the handler around the open.
Image.MAX_IMAGE_PIXELS = _MAX_PIXELS

# Under this many pixels on the long edge nothing is a document. Icons, avatars,
# signature stamps and preview thumbnails all live far below it, and a scan of a
# postcard lives far above it (pitfall 6).
_MIN_LONG_EDGE_PIXELS: Final = 640

# Long edge divided by short edge. Above this a picture is a banner, a page
# divider or a panorama, whatever its resolution says. Exactly eight still
# passes, because the comparison below is strictly greater.
_MAX_ASPECT_RATIO: Final = 8

# What the engine is given at most on the long edge. A twelve megapixel phone
# photograph then costs what an A4 page at 300 dpi costs, which is the page this
# whole OCR path was measured against.
_MAX_EDGE_PIXELS: Final = 3500

# Below this many characters the picture counts as carrying no text.
#
# Twenty, and not the twenty five of ``ocr._MIN_OCR_CHARS``, because the unit is
# a different one. There the number judges a whole document of up to thirty
# pages; here it judges a single picture, where a stamp, a house number and a
# date are a plausible entire content. It is the start value of pitfall 6 and it
# is repeated rather than imported for the same reason the other two are.
_MIN_OCR_CHARS: Final = 20

# The picture travels through a pipe and is read once. Compressing it hard would
# spend CPU on bytes that live for milliseconds, exactly as in raster.py.
_PNG_COMPRESS_LEVEL: Final = 1


def extract_image(path: str) -> ExtractionOutcome:
    """The text of a picture, or the verdict that says why there is none.

    Defined at module level so it can be pickled into the extraction child, like
    ``pdf.extract_pdf`` and ``ocr.extract_pdf_ocr``; a closure or a method would
    not survive the process boundary of plan 02-05.

    Every exception this branch knows becomes a verdict here, in one place.
    Anything else belongs to ``ExtractionOutcome.from_exception`` at the process
    boundary, where it becomes failed(corrupt) rather than a guess made twice.
    """
    resolved = config.settings()
    try:
        opened = Image.open(path)
    except Image.DecompressionBombError:
        # Pillow's own refusal, which arrives at twice our budget and before a
        # single row is decoded. A decision and not a failure: nobody could have
        # read this file, and skipped(too_large) is what an admin can act on.
        return ExtractionOutcome.skipped(Reason.TOO_LARGE)
    except OSError:
        # UnidentifiedImageError is a subclass of this, and so is the truncated
        # file. A picture whose header does not parse beat the parser.
        return ExtractionOutcome.failed(Reason.CORRUPT)

    with opened as picture:
        refused = _implausible(picture)
        if refused is not None:
            return refused
        try:
            return _read_frames(picture, resolved)
        except ocr.EngineMissing:
            # Its own verdict, because "this image has no OCR" and "this file
            # beat the decoder" call for entirely different answers from an
            # admin (T-03-806).
            return ExtractionOutcome.failed(Reason.OCR_UNAVAILABLE)
        except ocr.EngineFailed:
            # Includes the death by signal of an exhausted address space: the
            # grandchild asked for the memory, so no MemoryError ever arrives in
            # this process (pitfall 10).
            return ExtractionOutcome.failed(Reason.OCR_FAILED)
        except OSError:
            # A header that parsed and pixels that did not, which is what a
            # truncated JPEG looks like from here.
            return ExtractionOutcome.failed(Reason.CORRUPT)


def _implausible(picture: Image.Image) -> ExtractionOutcome | None:
    """The three questions asked of the header, before a single row is decoded.

    ``Image.open`` has read the header and nothing else at this point, which is
    the whole reason these rules are cheap: a picture refused here costs one file
    handle and no memory at all.

    The order is meaning rather than taste. The pixel count comes first because
    it is the memory guard, and a guard that only holds while the two plausibility
    rules below stay in place is not a guard. The rotation of the picture does not
    enter into any of the three: turning a page by ninety degrees changes neither
    its area, nor its long edge, nor the ratio between its edges.
    """
    width, height = picture.size
    longest, shortest = max(width, height), min(width, height)

    if width * height > _MAX_PIXELS:
        return ExtractionOutcome.skipped(Reason.TOO_LARGE)
    if longest < _MIN_LONG_EDGE_PIXELS:
        return ExtractionOutcome.skipped(Reason.IMAGE_NOT_OCRABLE)
    if longest > shortest * _MAX_ASPECT_RATIO:
        # Multiplied rather than divided, which also answers the picture with an
        # edge of zero: every ratio is above the cap then, and it is refused
        # instead of dividing by nothing.
        return ExtractionOutcome.skipped(Reason.IMAGE_NOT_OCRABLE)
    return None


def _read_frames(picture: Image.Image, resolved: Settings) -> ExtractionOutcome:
    """Walk the frames of the file under the same caps a scanned PDF gets.

    A TIFF may carry many pictures, which is the shape a fax archive has, so the
    page cap of a PDF applies here as well: a cap that a second container format
    walks around is not a cap (T-03-1004). The soft deadline is the same one for
    the same reason, and both cuts stay visible as indexed(truncated) rather than
    as a quietly thin result (D-08).
    """
    frame_count = getattr(picture, "n_frames", 1)
    read_frames = min(frame_count, resolved.ocr_max_pages)
    deadline = time.monotonic() + resolved.ocr_job_seconds
    languages = "+".join(resolved.ocr_languages)

    parts: list[str] = []
    attempted = 0
    lost = 0
    cut = frame_count > read_frames

    for number in range(read_frames):
        if time.monotonic() >= deadline:
            cut = True
            break
        if frame_count > 1:
            picture.seek(number)
        attempted += 1
        try:
            parts.append(ocr.read_page(_encode_frame(picture), languages, resolved.ocr_page_seconds))
        except ocr.PageTimeout:
            lost += 1

    if attempted > 0 and lost == attempted:
        # Nothing was read at all, so this is not a thin picture, it is a failure.
        return ExtractionOutcome.failed(Reason.TIMEOUT)
    # A frame lost to its timeout counts as a cut, for the reason the scan
    # branch gives (review finding WR-03): D-08 wants a partial result visible
    # as one, and a fax archive missing a page is a partial result.
    return _verdict("\n".join(parts), truncated=cut or lost > 0)


def _encode_frame(picture: Image.Image) -> bytes:
    """One frame, upright, scaled and greyscale, as encoded PNG bytes.

    The order is the point. The orientation from the header is applied before
    everything else: a page photographed sideways carries orientation 6, and
    without the transpose it reaches tesseract rotated by ninety degrees. The
    result of that is character salad, which no verdict would ever show, because
    the run itself succeeds.

    Then the downscale, then the single channel. Greyscale for the reason
    raster.py gives: tesseract binarises internally either way, so three further
    channels are paid for and thrown away.
    """
    transposed = ImageOps.exif_transpose(picture)
    # Pillow answers None only when it was asked to work in place, which this
    # call does not do. The branch is here because the signature allows it, and
    # the frame the loop is standing on is the honest fallback.
    frame = picture if transposed is None else transposed

    try:
        # thumbnail keeps the aspect ratio and never scales up, so a picture that
        # is already small is left exactly as it is. It works on the transposed
        # image in memory; nothing of this reaches the file on disk.
        frame.thumbnail((_MAX_EDGE_PIXELS, _MAX_EDGE_PIXELS))
        grey = frame.convert("L")
        try:
            sink = BytesIO()
            grey.save(sink, format="PNG", compress_level=_PNG_COMPRESS_LEVEL)
        finally:
            grey.close()
    finally:
        if frame is not picture:
            # The open file of the caller stays open, the working image does not.
            frame.close()
    return sink.getvalue()


def _verdict(text: str, *, truncated: bool) -> ExtractionOutcome:
    """Turn what the engine read into a verdict, with the character cap applied.

    The threshold is where D-05 is really answered: the engine ran, the time was
    spent, and the picture still does not enter the index. The caller sets
    ``ocr_used`` for it, so the cost of a folder full of holiday pictures is
    visible on the status page of phase 4 instead of being invisible in a cap
    that claimed to recognise them beforehand.
    """
    if len(text.strip()) < _MIN_OCR_CHARS:
        return ExtractionOutcome.skipped(Reason.EMPTY_TEXT)

    outcome = cap_text(text)
    if truncated and not outcome.truncated:
        # A cap that was reached is visible as one, whichever of them it was.
        return ExtractionOutcome.indexed(outcome.text, truncated=True)
    return outcome
