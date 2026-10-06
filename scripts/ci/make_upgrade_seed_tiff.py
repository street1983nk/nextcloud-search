#!/usr/bin/env python3
"""Write the grey plus extra channel TIFF the upgrade proof sows (plan 29-11).

The upgrade proof of ``.github/workflows/deploy-harp.yml`` starts from v1.3.2
and has to show that the recheck of 1.4.0 (D-29-10, plan 29-09) judges files
again that 1.3.2 judged wrongly. One of the two seed files is this picture: grey
with one extra channel declared as unspecified (ExtraSamples 0), big endian,
uncompressed, eight bits per sample. That is the class of issue #18 the dump of
03.10.2026 showed, the key ``(MM, 1, (1,), 1, (8, 8), (0,))`` of the TIFF shim of
plan 29-07. Pillow 12.3.0 has no entry for it, so 1.3.2 books the file as
failed(corrupt); 1.4.0 reads it through the shim and finds the seed word.

The picture carries the seed word three times and one ordinary line, so the
text the engine reads is above the twenty characters a picture needs before it
counts as carrying text, and one misread line still leaves the word findable.

Deterministic on purpose: no date, no software tag, the default font of Pillow
at a fixed size, and the byte order turned by hand. A test renders the picture
again and compares it byte for byte with the committed fixture, so a fixture
nobody can reproduce never lands in the repository.

Run from the backend directory, which carries Pillow in its environment::

    cd backend && uv run python ../scripts/ci/make_upgrade_seed_tiff.py
"""

from __future__ import annotations

import struct
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# The word the upgrade proof searches for. Invented, so no file of the reference
# corpus, of the fill corpus or of the Spanish document carries it, and not a
# compound of any word they carry. deploy-harp.yml names the same value as
# SEED_WORD, and backend/tests/test_upgrade_seed_steps.py holds the two equal.
SEED_WORD = "quorvintax"

# Where the picture is committed, relative to the repository root.
FIXTURE = Path(".github") / "fixtures" / "upgrade-seed-grey-extra.tif"

# 960 by 400 pixels of two samples each is 768000 bytes of pixel data, below one
# megabyte, and the long edge stays above the 640 pixels under which
# findling.extract.image calls a picture an icon.
SIZE = (960, 400)
FONT_SIZE = 72
LINES = (SEED_WORD, "Kisten im Keller", SEED_WORD)

_TAG_EXTRA_SAMPLES = 338
_SHORT = 3
# Bytes per value of the TIFF field types Pillow writes for this picture.
_TYPE_BYTES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1}
_TYPE_CODES = {3: "H", 4: "I", 5: "II"}


def _little_endian_tiff() -> bytes:
    """The picture as Pillow writes it: little endian, ExtraSamples 2."""
    font = ImageFont.load_default(size=FONT_SIZE)
    sink = BytesIO()
    with Image.new("LA", SIZE, color=(255, 255)) as picture:
        draw = ImageDraw.Draw(picture)
        for number, line in enumerate(LINES):
            draw.text((40, 20 + number * 120), line, fill=(0, 255), font=font)
        picture.save(sink, format="TIFF", compression="raw")
    return sink.getvalue()


def _extra_samples_zero(data: bytes) -> bytes:
    """The same little endian TIFF with ExtraSamples set to 0 (unspecified)."""
    patched = bytearray(data)
    (ifd,) = struct.unpack_from("<I", data, 4)
    (count,) = struct.unpack_from("<H", data, ifd)
    for number in range(count):
        entry = ifd + 2 + 12 * number
        tag, kind, values = struct.unpack_from("<HHI", data, entry)
        if tag == _TAG_EXTRA_SAMPLES:
            if kind != _SHORT or values != 1:
                raise ValueError(f"ExtraSamples has type {kind} and {values} values, expected one SHORT")
            struct.pack_into("<H", patched, entry + 8, 0)
            return bytes(patched)
    raise ValueError("Pillow wrote no ExtraSamples tag")


def _big_endian(data: bytes) -> bytes:
    """A little endian TIFF rewritten as big endian, structure only.

    Every sample is eight bits wide and the data is uncompressed, so the pixel
    bytes stay as they are; the header, the IFD and the values it points to
    change their order. The same walk as _big_endian in backend/tests/test_ocr.py.
    """
    if data[:4] != b"II*\x00":
        raise ValueError("expected a little endian TIFF")
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
            if _TYPE_BYTES[kind] * values <= 4:
                at = entry + 8
            else:
                (at,) = struct.unpack_from("<I", data, entry + 8)
                struct.pack_into(">I", turned, entry + 8, at)
            code = _TYPE_CODES.get(kind)
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


def render() -> bytes:
    """The bytes of the fixture, the same on every run."""
    return _big_endian(_extra_samples_zero(_little_endian_tiff()))


def main() -> int:
    """Write the fixture next to the repository root this script lives in."""
    target = Path(__file__).resolve().parents[2] / FIXTURE
    target.parent.mkdir(parents=True, exist_ok=True)
    data = render()
    target.write_bytes(data)
    sys.stdout.write(f"{FIXTURE.as_posix()}: {len(data)} bytes\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
