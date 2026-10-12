#!/usr/bin/env python3
"""Write the seed of the new formats the upgrade proof sows (plan 31-12, FMT-06).

The upgrade proof of ``.github/workflows/deploy-harp.yml`` starts from v1.4.2
and has to show that 1.5 catches up, once and without a full crawl, on files an
installation of 1.4.2 already holds: the six new types 1.4.2 never queued, a
Word file under a .docx name that 1.4.2 booked as skipped(legacy_format), and a
file 1.4.2 gave up on as failed(repeatedly_stuck). "Store upgrade 2b" sows these
files on the released installation; this script writes them.

Eight files, each with a word of its own that stands nowhere else in the
repository, so a hit after the upgrade names exactly one file (SEED_WORDS):

- ``seed-mail.eml``, a mail whose word stands only in its HTML part. There is
  no text/plain part, so the HTML route of the mail reader is what finds it.
- ``seed-archive.zip``, a ZIP file with the word in ``innen/notiz.txt``.
- ``seed-word.doc`` and ``seed-excel.xls``, byte for byte copies of the unit
  fixtures ``word97-latin.doc`` and ``biff8-values.xls`` of plans 31-05 and
  31-06 (backend/tests/fixtures/legacy/).
- ``seed-photo.heic``, a picture with the word drawn on it, large enough for a
  safe reading by the engine.
- ``seed-ole-under-docx.docx``, a copy of ``word97-ole-seed.doc``: an old Word
  document under the new name, which 1.4.2 books as skipped(legacy_format).
- ``seed-stale-size.txt``, a short text. The workflow makes its size in the
  file cache stale, and that is what lets 1.4.2 give up on it.
- ``seed-bomb.zip`` (BOMB), a small ZIP bomb without any word: a ZIP in a ZIP
  in a ZIP that ends in a text file, one level past ARCHIVE_MAX_DEPTH, and next
  to it one member of zero bytes compressed far past ARCHIVE_MAX_RATIO. Both
  limits are independent of any measured rate, and either one alone makes the
  file skipped(archive_limit) for the code of this phase.

Deterministic where the format allows it: the mail, the two ZIP files and the
text file are written byte for byte the same on every run, and a test writes
them again and compares. The ZIP files are put together by hand, with fixed
dates, a fixed system byte and the zero member as a deflate stream encoded here
with the fixed Huffman table, so neither the zlib of the machine nor the
platform of the zipfile module changes a byte. The photo is encoded by libheif
and the three copies come from LibreOffice; neither promises the same bytes
twice, so the test pins their SHA-256 instead. The photo is rendered only when
it is missing or when ``--render-photo`` asks for it, so an ordinary run leaves
the pinned bytes alone.

Run from the backend directory, which carries Pillow and pillow-heif::

    cd backend && uv run python ../scripts/ci/make_upgrade_seed_formats.py
"""

from __future__ import annotations

import argparse
import shutil
import struct
import sys
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Where the seed is committed, relative to the repository root.
FIXTURE_DIR = Path(".github") / "fixtures" / "upgrade-seed-formats"
LEGACY_DIR = Path("backend") / "tests" / "fixtures" / "legacy"

# File name to seed word. Invented words, one per file; deploy-harp.yml names
# the same values, and backend/tests/test_upgrade_seed_steps.py holds them equal.
SEED_WORDS = {
    "seed-mail.eml": "mailquendel",
    "seed-archive.zip": "archivquendel",
    "seed-word.doc": "wortquendel",
    "seed-excel.xls": "zellquendel",
    "seed-photo.heic": "fotoquendel",
    "seed-ole-under-docx.docx": "hullequendel",
    "seed-stale-size.txt": "cachequendel",
}

# The ZIP bomb, the one file of the seed without a word.
BOMB = "seed-bomb.zip"

# The copies and the unit fixtures they are copied from.
COPIES = {
    "seed-word.doc": "word97-latin.doc",
    "seed-excel.xls": "biff8-values.xls",
    "seed-ole-under-docx.docx": "word97-ole-seed.doc",
}

PHOTO = "seed-photo.heic"
# 1600 by 600 pixels: the long edge well above the 640 under which the image
# path calls a picture an icon, and letters of about 100 pixels.
PHOTO_SIZE = (1600, 600)
PHOTO_FONT_SIZE = 110
PHOTO_LINES = ("fotoquendel", "Urlaub am See", "fotoquendel")
PHOTO_FONT = Path("testdata") / "fonts" / "DejaVuSans.ttf"
PHOTO_QUALITY = 90

# One mebibyte of zeros plus a little, chosen so that everything after the
# first literal is a whole number of matches of 258 bytes: 1 + 258 * 4065. It
# is at least ARCHIVE_RATIO_MIN_BYTES (1 MiB), the size from which the ratio is
# asked at all.
ZERO_MATCHES = 4065
ZERO_BYTES = 1 + 258 * ZERO_MATCHES

# 1980-01-01 00:00:00 in the DOS format of the ZIP headers, the earliest date the
# format can carry and the same on every machine.
_DOS_TIME = 0
_DOS_DATE = (0 << 9) | (1 << 5) | 1
# Unix as the system that made the archive, and a plain file with mode 0644.
_MADE_BY = (3 << 8) | 20
_NEEDED = 20
_EXTERNAL = 0o100644 << 16
_STORED = 0
_DEFLATED = 8


def _mail() -> bytes:
    """A mail with one HTML part and no text part; the word stands only in the HTML."""
    word = SEED_WORDS["seed-mail.eml"]
    lines = [
        "From: Hausverwaltung <verwaltung@example.org>",
        "To: Mieter <mieter@example.org>",
        "Subject: Notiz zum Keller",
        "Date: Thu, 01 Oct 2026 09:00:00 +0200",
        "Message-ID: <seed-mail@example.org>",
        "MIME-Version: 1.0",
        "Content-Type: text/html; charset=utf-8",
        "Content-Transfer-Encoding: 7bit",
        "",
        "<html><body>",
        f"<p>Das {word} steht nur im HTML-Teil dieser Nachricht.</p>",
        "<p>Bitte den Keller bis Freitag leeren.</p>",
        "</body></html>",
        "",
    ]
    return "\r\n".join(lines).encode("ascii")


def _stale_text() -> bytes:
    word = SEED_WORDS["seed-stale-size.txt"]
    return f"Das {word} steht in einer kleinen Notiz im Keller.\n".encode("ascii")


class _Bits:
    """A bit writer in the order of RFC 1951: least significant bit first."""

    def __init__(self) -> None:
        self._out = bytearray()
        self._value = 0
        self._count = 0

    def put(self, value: int, count: int) -> None:
        """Write ``count`` bits of ``value``, least significant first (header, extra bits)."""
        for shift in range(count):
            self._value |= ((value >> shift) & 1) << self._count
            self._count += 1
            if self._count == 8:
                self._out.append(self._value)
                self._value = 0
                self._count = 0

    def code(self, value: int, count: int) -> None:
        """Write a Huffman code, most significant bit first (RFC 1951, 3.1.1)."""
        for shift in range(count - 1, -1, -1):
            self.put((value >> shift) & 1, 1)

    def done(self) -> bytes:
        if self._count:
            self._out.append(self._value)
        return bytes(self._out)


def _zeros_deflated() -> bytes:
    """ZERO_BYTES zeros as one raw deflate block with the fixed Huffman table.

    One literal 0, then ZERO_MATCHES matches of length 258 at distance 1, then
    the end of the block. In the fixed table literal 0 is the eight bit code
    0x30, length 258 is symbol 285 with the eight bit code 0xC5 and no extra
    bits, distance 1 is the five bit code 0, the end of the block the seven bit
    code 0 (RFC 1951, 3.2.6).
    """
    bits = _Bits()
    bits.put(1, 1)  # BFINAL
    bits.put(1, 2)  # BTYPE 01, fixed Huffman codes
    bits.code(0x30, 8)  # literal 0
    for _ in range(ZERO_MATCHES):
        bits.code(0xC5, 8)  # length 258
        bits.code(0, 5)  # distance 1
    bits.code(0, 7)  # end of block
    return bits.done()


def _zip(members: list[tuple[str, bytes, int, bytes]]) -> bytes:
    """A ZIP file of (name, data, method, stored bytes), local headers then the directory."""
    body = bytearray()
    directory = bytearray()
    for name, data, method, stored in members:
        encoded = name.encode("ascii")
        crc = zlib.crc32(data) & 0xFFFFFFFF
        offset = len(body)
        body += struct.pack(
            "<IHHHHHIIIHH",
            0x04034B50,
            _NEEDED,
            0,
            method,
            _DOS_TIME,
            _DOS_DATE,
            crc,
            len(stored),
            len(data),
            len(encoded),
            0,
        )
        body += encoded + stored
        directory += struct.pack(
            "<IHHHHHHIIIHHHHHII",
            0x02014B50,
            _MADE_BY,
            _NEEDED,
            0,
            method,
            _DOS_TIME,
            _DOS_DATE,
            crc,
            len(stored),
            len(data),
            len(encoded),
            0,
            0,
            0,
            0,
            _EXTERNAL,
            offset,
        )
        directory += encoded
    end = struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, len(members), len(members), len(directory), len(body), 0)
    return bytes(body + directory + end)


def _stored(name: str, data: bytes) -> tuple[str, bytes, int, bytes]:
    return (name, data, _STORED, data)


def _archive() -> bytes:
    word = SEED_WORDS["seed-archive.zip"]
    note = f"Das {word} steht in der inneren Notiz des Archivs.\n".encode("ascii")
    return _zip([_stored("innen/notiz.txt", note)])


def _bomb() -> bytes:
    """Three levels of ZIP and a zero member past the ratio, no word anywhere."""
    level_three = _zip([_stored("notiz.txt", b"Ganz unten liegt nur eine kurze Notiz.\n")])
    level_two = _zip([_stored("ebene3.zip", level_three)])
    zeros = _zeros_deflated()
    if zlib.decompress(zeros, -15) != b"\0" * ZERO_BYTES:
        raise ValueError("the hand made deflate stream does not inflate to the zeros it stands for")
    return _zip([_stored("ebene2.zip", level_two), ("nullen.bin", b"\0" * ZERO_BYTES, _DEFLATED, zeros)])


def render_deterministic() -> dict[str, bytes]:
    """The four files that are the same on every run, by file name."""
    return {
        "seed-mail.eml": _mail(),
        "seed-archive.zip": _archive(),
        BOMB: _bomb(),
        "seed-stale-size.txt": _stale_text(),
    }


def render_photo() -> bytes:
    """The photo, encoded by the libheif of pillow-heif. Not byte stable, so pinned."""
    from io import BytesIO

    import pillow_heif
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.truetype(str(REPO_ROOT / PHOTO_FONT), PHOTO_FONT_SIZE)
    sink = BytesIO()
    with Image.new("RGB", PHOTO_SIZE, color="white") as picture:
        draw = ImageDraw.Draw(picture)
        for number, line in enumerate(PHOTO_LINES):
            draw.text((60, 40 + number * 180), line, fill="black", font=font)
        pillow_heif.from_pillow(picture).save(sink, quality=PHOTO_QUALITY)
    return sink.getvalue()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--render-photo", action="store_true", help="encode the photo again (new pin)")
    args = parser.parse_args(argv)

    target = REPO_ROOT / FIXTURE_DIR
    target.mkdir(parents=True, exist_ok=True)
    for name, data in render_deterministic().items():
        (target / name).write_bytes(data)
        sys.stdout.write(f"{name}: {len(data)} bytes\n")
    for name, original in COPIES.items():
        shutil.copyfile(REPO_ROOT / LEGACY_DIR / original, target / name)
        sys.stdout.write(f"{name}: copy of {original}\n")
    photo = target / PHOTO
    if args.render_photo or not photo.exists():
        data = render_photo()
        photo.write_bytes(data)
        sys.stdout.write(f"{PHOTO}: {len(data)} bytes, rendered\n")
    else:
        sys.stdout.write(f"{PHOTO}: kept, --render-photo encodes it again\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
