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

**HEIC and HEIF are readable since plan 31-07 (FMT-05).** pillow-heif is
registered as a Pillow plugin when this module is imported, so a phone photograph
in HEIC takes the same way as a JPEG: the bomb guard, the plausibility rules, the
estimate against the address space and the EXIF rotation. What differs is
written next to the place it differs at: the options of the registration, the
ValueError of a truncated file, and the larger working copies of the estimate.
Whether a HEIC is handed to this module at all is the allowlist of dispatch.py,
which opens for it in plan 31-10.

Like every module of this package, this one never writes: the file is opened for
reading, every rotation, every scaling and every patched TIFF tag happens in
memory, and the original is not touched even on the error path (IDX-07,
T-03-805).
"""

from __future__ import annotations

import struct
import sys
import time
from io import BytesIO
from pathlib import Path
from typing import Final

import pillow_heif
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
# the handler around the open. The one sanctioned exception is
# _refused_by_pillow: after Pillow refused a picture it re-reads only the
# header with MAX_IMAGE_PIXELS = None and puts the value back in a finally.
Image.MAX_IMAGE_PIXELS = _MAX_PIXELS

# Pixels a picture may declare per byte of its file before a refusal of Pillow
# (over twice _MAX_PIXELS, so over 100 MP) is read as an attack and not as an
# honestly large picture (D-36-17, 36-WORTLAUT.md A3, owner answer O6 (a)). A
# white 1 bit scan in CCITT G4 reaches several thousand pixels per byte only at
# sizes far under 100 MP; a real medium format photograph over 100 MP lies at
# tens of pixels per byte. Assumption A1 of the phase research, not a
# measurement. Above it: skipped(blocked_malicious) with "image_pixels"; at or
# under it: skipped(too_large) as before.
IMAGE_BOMB_PIXELS_PER_BYTE: Final = 1000

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
    """Teach Pillow the TIFF variant of #18 it cannot map, and only that one.

    ``TiffImagePlugin.OPEN_INFO`` is the table ``_setup`` looks every file up
    in, and a key that is missing there is ``SyntaxError("unknown pixel mode")``,
    which ``Image.open`` reports as a file it cannot identify. One class is
    added (D-29-06, #18): SampleFormat 0, which is not in the specification; 1
    is its default, so every key Pillow has for 1 is offered for 0 with the
    value Pillow gives it. Floating point (3) is never touched: its bits read
    as integers are noise (T-29-23).

    Grey plus one extra channel declared as unspecified (ExtraSamples 0) or as
    associated alpha (1) was the second class until plan 36-17. Pillow 12.3.0
    mapped only the unassociated alpha (2), so the shim mapped both to ("LA",
    "LA"). Pillow 13.0.0 maps them itself (python-pillow#10139, fixed by PR
    #10140, which the tag 13.0.0 contains): 0 to ("L", "LX"), which skips the
    channel, and 1 to ("La", "La"), whose first band ``_grey_of`` hands on.
    Those keys left the shim, and their SampleFormat 0 mirrors now carry
    Pillow's values like every other mirror.

    Only ``setdefault``, so an entry Pillow ships is never changed, and the keys
    that were really added are returned so a test turns red on the Pillow bump
    that starts shipping one of them (pitfall 3).
    """
    info = TiffImagePlugin.OPEN_INFO
    wanted: dict[tuple[object, ...], tuple[str, str]] = {}
    for key, value in info.items():
        if key[2] == (1,):
            wanted[(*key[:2], (0,), *key[3:])] = value
    added = frozenset(key for key in wanted if key not in info)
    for key, value in wanted.items():
        info.setdefault(key, value)
    return added


# A module side effect next to the bomb guard above, for the same reason: the
# extraction child imports this module before it opens a single picture.
_SHIM_KEYS: Final = _register_tiff_variants()

# HEIC and HEIF as a Pillow plugin (FMT-05, D-31-06), registered here for the
# reason the TIFF shim is: before the first picture is opened. Four options,
# each against a default of the library:
#
# thumbnails=False. Since pillow-heif 1.8.0 a draft may pick an embedded
# preview picture instead of the image (pitfall 11 of the phase research). At
# the draft target of today no preview would be large enough, but OCR on a
# preview is never the intent, and the option makes it independent of any
# later target.
# depth_images=False and aux_images=False. A depth map and an alpha or gain map
# are pictures this branch never reads; not decoding them keeps libheif out of
# code paths and memory this branch has no use for (T-31-20).
# decode_threads=1. The extraction child decodes one file at a time under
# RLIMIT_AS, and every decoder thread wants a stack inside that address space,
# which is the OpenBLAS lesson of sandbox.py (assumption A5, measured in the
# image probe of plan 31-07).
#
# DISABLE_SECURITY_LIMITS is left at its default, False: the limits libheif
# brings for image size and box counts stay in force next to the bomb guard.
pillow_heif.register_heif_opener(thumbnails=False, depth_images=False, aux_images=False, decode_threads=1)

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

# The header estimate of D-29-07 (#18): the decoded picture is counted twice,
# once as loaded and once as the working copy the scaling and the conversion to
# grey make next to it. Assumption A5 of the phase research: the factor comes
# from the measured peaks on an 8192 by 5464 picture (131 MiB for CMYK, 48 MiB
# for RGB after the draft), and RLIMIT_AS counts address space rather than the
# working set measured there, so it is a floor and is checked in the field at the
# next visit (D-29-11), not claimed as exact. Every format except HEIF.
_WORKING_COPIES: Final = 2

# HEIF is estimated by a model measured in the image, not by a factor (plan
# 31-07, owner decision at its checkpoint, D-31-06). libheif holds the decoded
# planes, pillow-heif an RGB buffer of its own while Pillow fills its picture
# from it, and there is no draft that brings a HEIC down before the decode, so
# the cost is a fixed part plus a part per pixel, and a factor on the picture
# alone was wrong at both ends: 3 missed the fixed part at 12 MP and let 36 to
# 38 MP through that do not fit, 5.5 (what covers 12 MP) refused 24 MP that do.
#
# The figures, docker.yml run 38124726627 on 2026-10-11, 12, 24 and 48 MP HEIC
# as a grid of 512 pixel tiles, medians of three children, amd64 and arm64
# within 0.2 MiB of each other, with the malloc arenas of the extraction child
# limited to one (sandbox.py, _limit_malloc_arenas):
#
#   growth of VmPeak while loading:   113.4, 195.4, 357.6 MiB
#   growth over the whole branch:     154.0, 217.6, 357.6 MiB (cap in place)
#
# The load lies on a line, 32.0 MiB plus 7.00 bytes per pixel, exactly at all
# three sizes. Below 48 MP the scaled working copy for the engine (3500 pixels
# on the long edge, about 35 MiB, plus its grey copy) comes after the load and
# raises the whole branch above it; the most it adds over the line is 72.6 MiB
# at 12 MP (154.0 - 81.4). The model takes the slope as measured and a fixed
# part of 80 MiB over those 72.6, so it lies over every measured value, over the
# load line and over the line through the whole branch at 12 and 24 MP (90.9 MiB
# plus 5.43 bytes per pixel) at every size up to the pixel cap: there is no size
# at which the estimate says "fits" and the branch does not.
#
# Measured on RGB, the mode every 8 bit HEIC without alpha opens in. A picture
# with alpha decodes a fourth plane and a four byte buffer, two more bytes a
# pixel by the same arithmetic; not measured, so it is taken as the upper bound
# for every other mode.
_HEIF_FIXED_BYTES: Final = 80 * 1024 * 1024
_HEIF_BYTES_PER_PIXEL: Final = 7
_HEIF_BYTES_PER_PIXEL_OTHER_MODES: Final = 9

# What the estimate writes as detail, a fixed name and never a number from the
# file (T-29-24). It reads like the class names plan 29-06 stores, on purpose.
_HEADER_ESTIMATE: Final = "findling.extract.image.HeaderEstimate"

# Where Linux states the address space of this process (the VmSize line).
_PROC_STATUS: Final = Path("/proc/self/status")

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
        # read this file, and skipped(too_large) is what an admin can act on,
        # unless the header declares far more pixels than the file has bytes
        # for, which is the signature of a bomb (D-36-17).
        return _refused_by_pillow(path)
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


def _refused_by_pillow(path: str) -> ExtractionOutcome:
    """The verdict on a picture Pillow refused as a decompression bomb: image_pixels or too_large.

    Width and height are read from the header a second time with Pillow's
    check switched off, and nothing else: ``.size`` decodes no row. The
    switch is global to Pillow, which is why it lives only inside the
    try/finally and is put back even when the second open raises; the
    extraction child reads one file at a time on one thread, so no other
    picture can open while it is off. Whatever goes wrong on the second open
    keeps the verdict this branch gave before, too_large.
    """
    previous = Image.MAX_IMAGE_PIXELS
    try:
        Image.MAX_IMAGE_PIXELS = None
        # The mode spelled out, so the write ratchet of test_extract_edge_paths
        # reads this open as the read it is.
        with Image.open(path, mode="r") as header:
            width, height = header.size
        size = Path(path).stat().st_size
    except Exception:
        # The second look is a refinement of a refusal, never a new failure.
        return ExtractionOutcome.skipped(Reason.TOO_LARGE)
    finally:
        Image.MAX_IMAGE_PIXELS = previous
    if width * height > IMAGE_BOMB_PIXELS_PER_BYTE * max(size, 1):
        return ExtractionOutcome.skipped(Reason.BLOCKED_MALICIOUS, detail="image_pixels")
    return ExtractionOutcome.skipped(Reason.TOO_LARGE)


def _read(picture: Image.Image, resolved: Settings) -> ExtractionOutcome:
    """Read an opened picture and turn every exception this branch knows into a verdict.

    The draft comes first because it decides the size the decoder allocates,
    and the estimate second because it has to judge that size and not the one
    the header declared (D-29-07).
    """
    _decode_smaller(picture)
    refused = _over_address_space(picture)
    if refused is not None:
        return refused
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


def _draft_target(width: int, height: int) -> tuple[int, int]:
    """The size a picture ends at on the way to the engine, aspect ratio kept.

    This and not (3500, 3500) is what the draft is asked for: libjpeg picks the
    largest of the scales 1/8, 1/4, 1/2 and 1 that still reaches the requested
    size on both edges, so a square target answers min(8192 // 3500, 5464 //
    3500) = 1 for a 45 megapixel camera and nothing is reduced.
    """
    factor = _MAX_EDGE_PIXELS / max(width, height)
    return max(1, round(width * factor)), max(1, round(height * factor))


def _decode_smaller(picture: Image.Image) -> None:
    """Ask the decoder for a reduced picture before a single row is decoded.

    Only a JPEG answers, through the DCT scaling of libjpeg; every other format
    ignores the request. Measured on an 8192 by 5464 picture with orientation 6
    (D-29-07, #18): together with the rotation in place this lowers the peak
    from 467 to 131 MiB for CMYK and from 466 to 48 MiB for RGB. Asking for
    grey lets libjpeg hand out one channel of a colour picture; CMYK stays CMYK
    and is reduced all the same. A picture of many frames is left alone, the
    draft holds for the whole file and a fax archive is not a camera (pitfall
    10). Neither is a picture that is already small enough.

    Whether there is a second frame is asked by a probe and not by n_frames,
    which walks every IFD of a TIFF (F-36-07-1, plan 36-09). The probe of a TIFF
    loads the tags of frame 1, so the picture is sent back to frame 0 before
    anything else is read; for a picture of one frame that seek does nothing,
    and the draft is set after it, never before.
    """
    several = _has_frame(picture, 1)
    picture.seek(0)
    if several:
        return
    width, height = picture.size
    if max(width, height) <= _MAX_EDGE_PIXELS:
        return
    picture.draft("L", _draft_target(width, height))


def _pixel_bytes(mode: str) -> int:
    """What one pixel of a mode costs in Pillow's memory, not on disk.

    Pillow keeps every picture of more than one band in four bytes a pixel,
    RGB included, so the count of bands times their width would undercount
    by a quarter; a single band costs its own width.
    """
    if Image.getmodebands(mode) > 1:
        return 4
    if mode in ("I", "F"):
        return 4
    if mode.startswith("I;16"):
        return 2
    return 1


def _address_space_used() -> int | None:
    """The address space of this process in bytes, from VmSize, or None where unreadable."""
    try:
        status = _PROC_STATUS.read_text(encoding="ascii", errors="replace")
    except OSError:
        return None
    for line in status.splitlines():
        if line.startswith("VmSize:"):
            fields = line.split()
            if len(fields) >= 2 and fields[1].isdigit():
                return int(fields[1]) * 1024
            return None
    return None


def _address_space_room() -> int | None:
    """What is left of RLIMIT_AS in this process, or None where there is nothing to read.

    RLIMIT_AS is POSIX and the extraction child sets it on Linux (sandbox.py);
    on Windows, where the tests also run, there is neither the limit nor
    /proc/self/status, and no estimate is made.
    """
    if sys.platform == "win32":
        return None
    import resource

    soft, _hard = resource.getrlimit(resource.RLIMIT_AS)
    if soft == resource.RLIM_INFINITY:
        return None
    used = _address_space_used()
    if used is None:
        return None
    return soft - used


def _over_address_space(picture: Image.Image) -> ExtractionOutcome | None:
    """The fourth question asked of the header: does the decoded picture fit at all.

    Without it a picture too large for the address space dies in the decoder,
    and that death reads as a broken file (#18). With it the verdict says what
    happened. The size is the one after the draft, so a camera picture that the
    draft brings down is judged at its reduced size.

    A HEIF over the estimate is skipped(too_large) rather than
    failed(out_of_memory). It has no draft, so its decoded size is the size the
    file declares, and no other child under the same cap would read it: that is
    a property of the file against the configuration, which an admin can act on
    through FINDLING_EXTRACT_ADDRESS_SPACE_BYTES, the same kind of decision as
    the pixel cap (pitfall 12). The verdict of every other format is the one of
    D-29-07 and stays as it was.
    """
    room = _address_space_room()
    if room is None:
        return None
    if _estimated_bytes(picture) > room:
        if picture.format == "HEIF":
            return ExtractionOutcome.skipped(Reason.TOO_LARGE)
        return ExtractionOutcome.failed(Reason.OUT_OF_MEMORY, detail=_HEADER_ESTIMATE)
    return None


def _estimated_bytes(picture: Image.Image) -> int:
    """What decoding the picture at its present size costs, by the header alone.

    A HEIF by the measured model above; every other format as width times
    height times the bytes Pillow keeps per pixel, times the working copies.
    """
    width, height = picture.size
    if picture.format == "HEIF":
        return _heif_estimate(width, height, picture.mode)
    return width * height * _pixel_bytes(picture.mode) * _WORKING_COPIES


def _heif_estimate(width: int, height: int, mode: str) -> int:
    """The address space a HEIF of this size and mode costs on its way through this branch."""
    per_pixel = _HEIF_BYTES_PER_PIXEL if mode == "RGB" else _HEIF_BYTES_PER_PIXEL_OTHER_MODES
    return _HEIF_FIXED_BYTES + width * height * per_pixel


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
        # The mode spelled out, so the write ratchet of test_extract_edge_paths
        # can read this open as the read of a buffer it is.
        opened = Image.open(stream, mode="r")
    except OSError:
        return ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)
    with opened as picture:
        return _read(picture, resolved)


def _normalise_sample_format(buffer: bytearray) -> bool:
    """Set every SampleFormat value 0 in every IFD of a classic TIFF to 1, in place.

    Only exactly 0 is changed; a 3 next to it stays a 3 and the file then fails
    to open as the variant it is (T-29-23). Every offset is checked against the
    buffer before it is read or written, a loop of IFDs ends at the first repeat,
    and both the IFDs with their entries and the SampleFormat values behind
    them are bounded by what the buffer can hold, so a hostile file costs at
    most one pass over its own bytes (T-29-23b). The second bound is audit
    finding F-29-01 of plan 29-14: many IFDs may point at one shared array, and
    without a budget of its own each of them walked it again, which made a
    crafted file quadratic. False means the structure did not hold, the budget
    ran out, or there was nothing to patch, and the caller answers with the
    honest verdict.
    """
    length = len(buffer)
    if length < 8:
        return False
    magic = bytes(buffer[:4])
    if magic not in _TIFF_MAGICS:
        return False
    order = "<" if magic == _TIFF_MAGICS[0] else ">"
    # The bytes of the IFDs walked, header and link included, so a chain of
    # empty IFDs is bounded as well: an honest file holds each of them once.
    budget = length
    # SampleFormat values, two bytes each: no honest file walks more of them
    # than it holds bytes for (F-29-01).
    values_left = length // 2
    seen: set[int] = set()
    patched = False
    (ifd,) = struct.unpack_from(order + "I", buffer, 4)
    while ifd:
        if ifd in seen or ifd + 2 > length:
            return False
        seen.add(ifd)
        (count,) = struct.unpack_from(order + "H", buffer, ifd)
        following = ifd + 2 + 12 * count
        budget -= 6 + 12 * count
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
            values_left -= values
            if at + 2 * values > length or values_left < 0:
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


def _has_frame(picture: Image.Image, index: int) -> bool:
    """Whether the picture has a frame ``index``, answered by seeking to it.

    Pillow answers n_frames of a TIFF by reading every IFD of the chain, and
    that walk grows faster than the chain: 5 000 IFDs 0.38 s, 10 000 0.66 s,
    20 000 1.81 s, 40 000 5.51 s in the process, 100 000 27.8 s in the
    extraction child (deferred-items.md F-36-07-1, measured on 2026-10-21).
    ``seek(index)`` reads the IFDs up to ``index`` and no further. A cycle in
    the chain is seen by Pillow at the seek and reads as the end.

    EOFError is the end of the frames. OSError, SyntaxError, ValueError,
    struct.error and the TypeError and KeyError of Pillow's ``_setup`` ("Missing
    dimensions" of an IFD read from past the end of the file, measured) are
    what a broken IFD raises on the way; a frame that cannot be reached is no
    frame, and the caller ends with the pages it has. The probe does not seek
    back: the caller decides where the picture stands.
    """
    try:
        picture.seek(index)
    except (EOFError, OSError, SyntaxError, ValueError, TypeError, KeyError, struct.error):
        return False
    return True


def _read_frames(picture: Image.Image, resolved: Settings) -> ExtractionOutcome:
    """Walk the frames of the file under the same caps a scanned PDF gets.

    A TIFF may carry many pictures, which is the shape a fax archive has, so the
    page cap of a PDF applies here as well: a cap that a second container format
    walks around is not a cap (T-03-1004). The soft deadline is the same one for
    the same reason, and both cuts stay visible as indexed(truncated) rather than
    as a quietly thin result (D-08).

    The frames are asked for one by one with a probe, never counted by n_frames
    (F-36-07-1, plan 36-09): Pillow walks every IFD of the chain for that number,
    and the walk grows faster than the chain (40 000 IFDs 5.51 s in the process,
    100 000 IFDs 27.8 s in the extraction child, measured on 2026-10-21). A
    probe reads the IFDs up to the frame it asks for, so a file costs at most
    the page cap plus one probe beyond it, which is what tells a cut from the
    end of the file. Many pages are no attack signature (36-WORTLAUT.md A3):
    the verdict stays the one of D-08.
    """
    deadline = time.monotonic() + resolved.ocr_job_seconds
    languages = "+".join(resolved.ocr_languages)

    parts: list[str] = []
    attempted = 0
    lost = 0
    cut = False
    walked = 0

    for number in range(resolved.ocr_max_pages):
        if time.monotonic() >= deadline:
            cut = True
            break
        if number > 0 and not _has_frame(picture, number):
            break
        walked += 1
        try:
            # Spelled out here and nowhere else, so the handler is as narrow as
            # the one call it is about. libheif reports pixel data that ends
            # before the picture does as a ValueError from load() (pillow-heif
            # 1.8.0, measured in plan 31-07), where every other decoder of this
            # branch raises an OSError; without this, a truncated HEIC would leave
            # the branch as an exception instead of a verdict (T-31-22). The
            # transpose below would call load() anyway, so nothing is decoded
            # that was not decoded before.
            picture.load()
        except ValueError as error:
            return ExtractionOutcome.failed(Reason.CORRUPT, detail=_class_of(error))
        attempted += 1
        try:
            parts.append(ocr.read_page(_encode_frame(picture), languages, resolved.ocr_page_seconds))
        except ocr.PageTimeout:
            lost += 1

    if walked == resolved.ocr_max_pages and not cut:
        # Every frame the cap allows was read: one probe beyond it tells a file
        # that has more from one that ends exactly at the cap.
        cut = _has_frame(picture, resolved.ocr_max_pages)

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

    The rotation works in place since plan 29-07 (D-29-07). Without in_place,
    Pillow loads the picture and returns a full copy even when nothing is to be
    turned, and that copy next to the loaded picture was the peak that killed a
    camera picture of #18 before the scaling could help. In place changes the
    pixels of the open picture in memory and nothing on disk; for a file of many
    frames the next seek decodes its frame afresh with its own orientation, so a
    turn of one frame never leaks into the next (pitfall 10).
    """
    ImageOps.exif_transpose(picture, in_place=True)
    # thumbnail keeps the aspect ratio and never scales up, so a picture that is
    # already small is left exactly as it is. It works in memory as well.
    picture.thumbnail((_MAX_EDGE_PIXELS, _MAX_EDGE_PIXELS))
    grey = _grey_of(picture)
    try:
        sink = BytesIO()
        grey.save(sink, format="PNG", compress_level=_PNG_COMPRESS_LEVEL)
    finally:
        grey.close()
    return sink.getvalue()


def _grey_of(picture: Image.Image) -> Image.Image:
    """The single grey channel of a frame, a new picture the caller closes.

    Grey with associated alpha opens as "La" since Pillow 13.0.0 (python-pillow
    PR #10140, plan 36-17), and Pillow has no conversion from "La" to "L". Its
    first band is the stored grey, which is exactly what this branch handed the
    engine under Pillow 12.3.0, when the shim opened the same file as "LA" and
    the conversion dropped the alpha: the picture as it lies on black. Undoing
    the premultiplication instead would brighten every half transparent stroke
    and change what is read. Every other mode converts as before.
    """
    if picture.mode == "La":
        return picture.getchannel(0)
    return picture.convert("L")


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
