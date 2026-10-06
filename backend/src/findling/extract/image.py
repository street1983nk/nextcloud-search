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

import struct
import time
from io import BytesIO
from pathlib import Path
from typing import Final

from PIL import Image, ImageOps, TiffImagePlugin

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

# The two first words of a classic TIFF, little and big endian.
_TIFF_MAGICS: Final = (b"II*\x00", b"MM\x00*")

# SampleFormat, and the one TIFF field type the specification gives it (SHORT).
_TAG_SAMPLE_FORMAT: Final = 339
_TIFF_SHORT: Final = 3

# The largest compressed SampleFormat 0 TIFF that is patched in memory (D-29-06,
# way (ii) of the probe in plan 29-07). Libtiff reads its tags from the bytes, so
# the value 0 has to be corrected in a copy of the file, and that copy lives
# under the same RLIMIT_AS as the decoded picture (T-29-23b). For a moment there
# are two copies, while the patched buffer becomes the immutable bytes BytesIO
# shares without copying again; 32 MiB keeps that moment at 64 MiB, an eighth of
# the default address space cap and below the 50 MiB file cap twice over. A
# larger file of this class gets the honest verdict instead of the copy.
_SF0_PATCH_MAX_BYTES: Final = 32 * 1024 * 1024


def _register_tiff_variants() -> frozenset[tuple[object, ...]]:
    """Teach Pillow the TIFF variants of #18 it cannot map, and only those.

    ``TiffImagePlugin.OPEN_INFO`` is the table ``_setup`` looks every file up
    in, and a key that is missing there is ``SyntaxError("unknown pixel mode")``,
    which ``Image.open`` reports as a file it cannot identify. Two classes are
    added (D-29-06, #18):

    Grey plus one extra channel declared as unspecified (ExtraSamples 0) or as
    associated alpha (1). Pillow 12.3.0 maps only the unassociated alpha (2). The
    target is ("LA", "LA"): the more exact looking grey mode with a sixteen bit
    big endian raw mode works on the raw path only, because the libtiff path
    rewrites that raw mode into the native order, and "La" does not convert to
    "L" (pitfall 2 of the phase research, reproduced).

    SampleFormat 0, which is not in the specification; 1 is its default, so
    every key Pillow has for 1 is offered for 0 as well. Floating point (3) is
    never touched: its bits read as integers are noise (T-29-23).

    Only ``setdefault``, so an entry Pillow ships is never changed, and the keys
    that were really added are returned so a test turns red on the Pillow bump
    that starts shipping one of them (pitfall 3). An upstream proposal is part
    of plan 29-15.
    """
    info = TiffImagePlugin.OPEN_INFO
    wanted: dict[tuple[object, ...], tuple[str, str]] = {}
    for order in (TiffImagePlugin.II, TiffImagePlugin.MM):
        for extra in (0, 1):
            wanted[(order, 1, (1,), 1, (8, 8), (extra,))] = ("LA", "LA")
    for key, value in [*info.items(), *wanted.items()]:
        if key[2] == (1,):
            wanted[(*key[:2], (0,), *key[3:])] = value
    added = frozenset(key for key in wanted if key not in info)
    for key, value in wanted.items():
        info.setdefault(key, value)
    return added


# A module side effect next to the bomb guard above, for the same reason: the
# extraction child imports this module before it opens a single picture.
_SHIM_KEYS: Final = _register_tiff_variants()

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
    except OSError as error:
        # UnidentifiedImageError is a subclass of this, and so is the truncated
        # file. A picture whose header does not parse beat the parser, unless it
        # is a TIFF whose variant Pillow has no mapping for: that file is fine,
        # and calling it broken was the wrong half of #18 (D-29-06).
        if _is_unsupported_tiff_variant(path):
            return ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)
        return ExtractionOutcome.failed(Reason.CORRUPT, detail=_class_of(error))

    with opened as picture:
        refused = _implausible(picture)
        if refused is not None:
            return refused
        if _has_compressed_sample_format_zero(picture):
            return _read_normalised(path, resolved)
        return _read(picture, resolved)


def _read(picture: Image.Image, resolved: Settings) -> ExtractionOutcome:
    """Read an opened picture and turn every exception this branch knows into a verdict."""
    try:
        return _read_frames(picture, resolved)
    except ocr.EngineMissing:
        # Its own verdict, because "this image has no OCR" and "this file beat
        # the decoder" call for entirely different answers from an admin
        # (T-03-806).
        return ExtractionOutcome.failed(Reason.OCR_UNAVAILABLE)
    except ocr.EngineFailed:
        # Includes the death by signal of an exhausted address space: the
        # grandchild asked for the memory, so no MemoryError ever arrives in
        # this process (pitfall 10). EngineKilled, the SIGKILL from outside, is
        # a sister of this class and passes through to the child loop, because
        # it is no verdict on the picture (D-26-16).
        return ExtractionOutcome.failed(Reason.OCR_FAILED)
    except OSError as error:
        # A header that parsed and pixels that did not, which is what a
        # truncated JPEG looks like from here.
        return ExtractionOutcome.failed(Reason.CORRUPT, detail=_class_of(error))


def _class_of(error: BaseException) -> str:
    """The class of an exception as module.qualname, the form plan 29-06 stores.

    Never the message: it can carry a path or bytes of the file (T-29-24).
    """
    raised = type(error)
    return f"{raised.__module__}.{raised.__qualname__}"


def _is_unsupported_tiff_variant(path: str) -> bool:
    """Whether a file Pillow refused is a well formed TIFF it has no mapping for.

    ``Image.open`` swallows the cause, so the TIFF plugin is asked directly. A
    variant ends in ``SyntaxError("unknown pixel mode")`` from ``_setup``; a
    broken IFD ends in any other error, and so does every file without the TIFF
    magic, which is not asked at all. Whatever goes wrong in here is an answer
    of no, because the caller then says corrupt, which is what it said before.
    """
    try:
        with Path(path).open("rb") as handle:
            if handle.read(4) not in _TIFF_MAGICS:
                return False
        TiffImagePlugin.TiffImageFile(path).close()
    except SyntaxError as error:
        return str(error) == "unknown pixel mode"
    except Exception:
        # Any other failure is the broken file the caller reports.
        return False
    return False


def _has_compressed_sample_format_zero(picture: Image.Image) -> bool:
    """Whether the opened picture is a compressed TIFF that declares SampleFormat 0.

    The shim opens it, but libtiff, which decodes every compressed TIFF, rejects
    the value 0 itself ("Bad value 0 for SampleFormat") and the load ends in a
    decoder error. Uncompressed files are decoded by Pillow and need nothing.
    """
    if not isinstance(picture, TiffImagePlugin.TiffImageFile):
        return False
    declared = picture.tag_v2.get(_TAG_SAMPLE_FORMAT)
    if not isinstance(declared, tuple) or 0 not in declared:
        return False
    return picture.info.get("compression") != "raw"


def _read_normalised(path: str, resolved: Settings) -> ExtractionOutcome:
    """Read a compressed SampleFormat 0 TIFF from a copy with the value set to 1.

    Way (ii) of the probe in plan 29-07, the only one that gave correct pixels:
    setting the tag on the opened picture (way (i)) never reaches libtiff, which
    reads the tags from the bytes. The copy is bounded by _SF0_PATCH_MAX_BYTES,
    and the file on disk is only ever read (IDX-07).
    """
    size = Path(path).stat().st_size
    if size > _SF0_PATCH_MAX_BYTES:
        return ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)
    buffer = bytearray(size)
    with Path(path).open("rb") as handle:
        complete = handle.readinto(buffer) == size
    if not complete or not _normalise_sample_format(buffer):
        return ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)
    # BytesIO shares immutable bytes instead of copying them, and so does its
    # getvalue, which is what the libtiff path hands the decoder. The patched
    # bytearray is dropped right after, so one copy is left.
    stream = BytesIO(bytes(buffer))
    del buffer
    try:
        opened = Image.open(stream)
    except OSError:
        return ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)
    with opened as picture:
        return _read(picture, resolved)


def _normalise_sample_format(buffer: bytearray) -> bool:
    """Set every SampleFormat value 0 in every IFD of a classic TIFF to 1, in place.

    Only exactly 0 is changed; a 3 next to it stays a 3 and the file then fails
    to open as the variant it is (T-29-23). Every offset is checked against the
    buffer before it is read or written, a loop of IFDs ends at the first repeat,
    and the entries walked are bounded by what the buffer can hold, so a hostile
    file costs at most one pass over its own bytes (T-29-23b). False means the
    structure did not hold or there was nothing to patch, and the caller answers
    with the honest verdict.
    """
    length = len(buffer)
    if length < 8:
        return False
    magic = bytes(buffer[:4])
    if magic not in _TIFF_MAGICS:
        return False
    order = "<" if magic == _TIFF_MAGICS[0] else ">"
    budget = length // 12
    seen: set[int] = set()
    patched = False
    (ifd,) = struct.unpack_from(order + "I", buffer, 4)
    while ifd:
        if ifd in seen or ifd + 2 > length:
            return False
        seen.add(ifd)
        (count,) = struct.unpack_from(order + "H", buffer, ifd)
        following = ifd + 2 + 12 * count
        budget -= count
        if following + 4 > length or budget < 0:
            return False
        for number in range(count):
            entry = ifd + 2 + 12 * number
            tag, kind, values = struct.unpack_from(order + "HHI", buffer, entry)
            if tag != _TAG_SAMPLE_FORMAT:
                continue
            if kind != _TIFF_SHORT:
                return False
            at = entry + 8 if values <= 2 else struct.unpack_from(order + "I", buffer, entry + 8)[0]
            if at + 2 * values > length:
                return False
            for value in range(values):
                where = at + 2 * value
                if struct.unpack_from(order + "H", buffer, where)[0] == 0:
                    struct.pack_into(order + "H", buffer, where, 1)
                    patched = True
        (ifd,) = struct.unpack_from(order + "I", buffer, following)
    return patched


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
