#!/usr/bin/env python3
"""Rebuild the reference corpus under testdata/corpus from scratch.

The corpus is committed as binary test data, but it is not hand made: every file
comes out of this script, so a reviewer can see what is inside a PDF instead of
trusting an opaque blob, and a later phase can regrow the set without hunting
for sample documents with unclear licences. Standard library only, no third
party writer, because a corpus that needs a dependency to exist is a corpus that
rots.

Run it from anywhere:

    python scripts/dev/build_corpus.py

With ``--check`` it builds the very same files in memory and compares them with
the bytes that lie in testdata/corpus, without writing a single one of them. That
is the reproducibility promise as a measurement rather than as a sentence, and it
is what the verification of a plan that touches this script runs.

Two files are broken on purpose. The zero byte PDF and the password protected
PDF are the error path, and the error path is where the predecessor app
(files_fulltextsearch_tesseract) destroyed user data. A corpus of well formed
documents would prove the pleasant half of the read only invariant only.

From phase 2 on the corpus has a second job. The files 09 to 12 carry German
administrative prose, and every one of the search terms the end to end job in
.github/workflows/integration.yml asserts on sits in exactly one of them. That
is not tidiness, it is what makes a green assertion mean something: in a corpus
where every word stands everywhere, a hit only proves that something was found.
The one deliberate exception is the word "Bescheid", which stands in 09 and in
10 so that the exclusion `bescheid -frist` has something to exclude.

Real umlauts in the German strings below are deliberate, exactly as in the
office part that has carried them since phase 1: an ASCII spelling would test the
one case that cannot go wrong. testdata/CORPUS.md holds the table of which
file carries which language case.

From phase 3 on the "standard library only" rule above is broken, once and on
purpose. OCR needs rendered text inside an image, and the standard library
cannot draw a glyph. The break is fenced in on three sides so it does not become
a habit. Pillow is the drawer, and it is already a pinned runtime dependency of
this project rather than a new one. The typeface is not taken from the machine
that happens to run the build: DejaVuSans.ttf was lifted out of
``fonts-dejavu-core`` 2.37-8 inside the pinned base image of backend/Dockerfile,
it is committed under testdata/fonts, and _font below refuses to render if its
SHA-256 has moved by a single byte. Every rendered pixel therefore comes from
one exact typeface, on every machine and in every year.

The built in default font of Pillow is explicitly not allowed here, not even as
a fallback. Aileron Regular carries, in Pillow's own words, "a more limited
character set", and it travels with the Pillow version. Umlauts and the sharp s
are the whole point of a DACH corpus, so a font that may silently drop them is
the one thing this corpus must not be built with. _assert_every_glyph_exists
turns that from a comment into a build failure, and testdata/CORPUS.md names the
rejected call so nobody has to guess which font is meant.
"""

from __future__ import annotations

import hashlib
import io
import struct
import sys
import zipfile
import zlib
from collections.abc import Sequence
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CORPUS_DIR = Path(__file__).resolve().parents[2] / "testdata" / "corpus"

# Fixed document id, so a rebuild produces the same encrypted PDF byte for byte.
DOC_ID = hashlib.md5(b"findling-reference-corpus", usedforsecurity=False).digest()

# These two are published on purpose: they are the passwords of a test fixture
# that is committed to a public repository, and the corpus README names them so
# a reviewer can open the file. S105 is muted here and only here.
USER_PASSWORD = "findling"  # noqa: S105
OWNER_PASSWORD = "findling-owner"  # noqa: S105

# The padding string of the standard security handler, PDF 32000-1 algorithm 2.
PASSWORD_PAD = bytes.fromhex("28bf4e5e4e758a4164004e56fffa01082e2e00b6d0683e802f0ca9fe6453697a")


def rc4(key: bytes, data: bytes) -> bytes:
    """RC4 as the PDF standard security handler defines it.

    Weak by today's standards and that is the point: the file has to be the kind
    of encrypted PDF that turns up in a real Nextcloud, not a modern one.
    """
    box = list(range(256))
    j = 0
    for i in range(256):
        j = (j + box[i] + key[i % len(key)]) % 256
        box[i], box[j] = box[j], box[i]

    out = bytearray()
    i = j = 0
    for byte in data:
        i = (i + 1) % 256
        j = (j + box[i]) % 256
        box[i], box[j] = box[j], box[i]
        out.append(byte ^ box[(box[i] + box[j]) % 256])
    return bytes(out)


def _padded(password: str) -> bytes:
    raw = password.encode("latin-1")[:32]
    return (raw + PASSWORD_PAD)[:32]


def _md5(payload: bytes) -> bytes:
    # Prescribed by the PDF specification for the standard security handler.
    # Not a security decision of this project, and it protects nothing here.
    return hashlib.md5(payload, usedforsecurity=False).digest()


def _stream_object(dictionary: str, data: bytes) -> bytes:
    return f"<< {dictionary} /Length {len(data)} >>\nstream\n".encode("ascii") + data + b"\nendstream"


def build_pdf(objects: list[bytes], extra_trailer: str = "") -> bytes:
    """Assemble numbered objects into a PDF with a correct cross reference table."""
    out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode("ascii") + body + b"\nendobj\n"

    xref_offset = len(out)
    size = len(objects) + 1
    out += f"xref\n0 {size}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("ascii")
    out += f"trailer\n<< /Size {size} /Root 1 0 R{extra_trailer} >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    return bytes(out)


def _page_objects(resources: str, content: bytes, media_box: str) -> list[bytes]:
    return [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox {media_box} /Resources {resources} /Contents 4 0 R >>".encode("ascii"),
        _stream_object("", content),
    ]


def build_text_layer_pdf() -> bytes:
    """A PDF whose text can be extracted without OCR."""
    content = (
        b"BT /F1 14 Tf 20 70 Td (Findling reference corpus) Tj ET\n"
        b"BT /F1 10 Tf 20 45 Td (This page carries a real text layer.) Tj ET\n"
    )
    objects = _page_objects("<< /Font << /F1 5 0 R >> >>", content, "[0 0 300 120]")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    return build_pdf(objects)


def build_scan_pdf() -> bytes:
    """A PDF that shows an image and contains no extractable text at all."""
    # An 8 by 8 grey ramp, hex encoded so the file stays free of stray binary.
    pixels = bytes((x * 28 + y * 3) % 256 for y in range(8) for x in range(8))
    image = _stream_object(
        "/Type /XObject /Subtype /Image /Width 8 /Height 8 /ColorSpace /DeviceGray"
        " /BitsPerComponent 8 /Filter /ASCIIHexDecode",
        pixels.hex().encode("ascii") + b">",
    )
    content = b"q 300 0 0 120 0 0 cm /Im1 Do Q\n"
    objects = _page_objects("<< /XObject << /Im1 5 0 R >> >>", content, "[0 0 300 120]")
    objects.append(image)
    return build_pdf(objects)


def build_encrypted_pdf() -> bytes:
    """A PDF that cannot be opened without the user password.

    Standard security handler, revision 2, 40 bit RC4. Old and weak, which is
    exactly what a decade of documents in a private Nextcloud looks like.
    """
    owner_entry = rc4(_md5(_padded(OWNER_PASSWORD))[:5], _padded(USER_PASSWORD))
    permissions = -1
    key = _md5(_padded(USER_PASSWORD) + owner_entry + struct.pack("<i", permissions) + DOC_ID)[:5]
    user_entry = rc4(key, PASSWORD_PAD)

    def object_key(number: int) -> bytes:
        return _md5(key + number.to_bytes(3, "little") + (0).to_bytes(2, "little"))[: min(len(key) + 5, 16)]

    content = b"BT /F1 14 Tf 20 70 Td (Locked away behind a user password.) Tj ET\n"
    objects = _page_objects("<< /Font << /F1 5 0 R >> >>", rc4(object_key(4), content), "[0 0 300 120]")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    # The strings of the encryption dictionary itself are never encrypted.
    objects.append(
        f"<< /Filter /Standard /V 1 /R 2 /O <{owner_entry.hex()}> /U <{user_entry.hex()}> /P {permissions} >>".encode(
            "ascii"
        )
    )
    return build_pdf(objects, extra_trailer=f" /Encrypt 6 0 R /ID [<{DOC_ID.hex()}> <{DOC_ID.hex()}>]")


def build_docx() -> bytes:
    """A minimal but valid DOCX: content types, relationships, one paragraph."""
    parts = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument'
            '.wordprocessingml.document.main+xml"/>'
            "</Types>"
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships'
            '/officeDocument" Target="word/document.xml"/>'
            "</Relationships>"
        ),
        "word/document.xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
            "<w:p><w:r><w:t>Findling reference corpus, office document part.</w:t></w:r></w:p>"
            # Real umlauts and a sharp s, because that is what the extractor will
            # meet. The ASCII spelling that stood here tested the one case that
            # cannot go wrong. The part is written as UTF-8 into the ZIP, exactly
            # as OOXML prescribes.
            "<w:p><w:r><w:t>Umlaute im Text: Grundstück, Ausschuss, Maßnahme.</w:t></w:r></w:p>"
            "</w:body></w:document>"
        ),
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, text in parts.items():
            # A fixed timestamp keeps the archive reproducible; the default would
            # stamp the build time into every entry.
            info = zipfile.ZipInfo(name, date_time=(2026, 8, 15, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, text)
    return buffer.getvalue()


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))


def build_png() -> bytes:
    """An 8 by 8 greyscale PNG, the image branch of the corpus."""
    width = height = 8
    raw = b"".join(b"\x00" + bytes((x * 30 + y * 7) % 256 for x in range(width)) for y in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + b"".join(
        (
            _png_chunk(b"IHDR", header),
            _png_chunk(b"IDAT", zlib.compress(raw, 9)),
            _png_chunk(b"IEND", b""),
        )
    )


def build_txt() -> bytes:
    """Plain text with German special characters, encoded as UTF-8."""
    lines = [
        "Findling reference corpus, plain text part.",
        "",
        "Deutscher Absatz mit echten Umlauten: Grundstück, Ausschuss, Maßnahme.",
        "Zweite Zeile für die Zeichensatzerkennung: Straßenbaubeitragssatzung.",
        "",
        "This file exists so the read path meets something that is not a container format.",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_cp1252_txt() -> bytes:
    """The same kind of text as build_txt, but in a German legacy encoding.

    Windows-1252 is what a decade of Windows tooling wrote, and a Nextcloud that
    has grown for years is full of it. Every umlaut here is a single byte, and
    that byte is invalid UTF-8, so a reader that assumes UTF-8 either raises or
    silently produces replacement characters. Both are indexing defects that a
    corpus of UTF-8 only files can never surface.

    Deliberately without a byte order mark: cp1252 has none, which is exactly why
    the encoding has to be detected rather than read off the first bytes.
    """
    lines = [
        "Findling reference corpus, legacy encoding part.",
        "",
        "Dieser Absatz ist Windows-1252 kodiert: Grundstück, Ausschuss, Maßnahme.",
        "Behördendeutsch für die Zeichensatzerkennung: Straßenbaubeitragssatzung.",
        "",
        "Every umlaut above is one single byte, and not one of them is valid UTF-8.",
    ]
    return ("\n".join(lines) + "\n").encode("cp1252")


# --------------------------------------------------------------------------
# The German language cases of phase 2.
#
# Every file below is new. Not one line above this block was touched, so the
# seven files of phase 1 and the legacy encoding file come out byte for byte as
# they did before, and gate B in integration.yml keeps comparing the very same
# checksums.
# --------------------------------------------------------------------------

# A fixed timestamp for every ZIP entry of the new archives, for the same reason
# the office part of phase 1 carries one: the default stamps the build time into
# the archive and a rebuild would differ from the committed file.
ZIP_TIMESTAMP = (2026, 9, 1, 12, 0, 0)


def _reproducible_zip(parts: dict[str, str], *, stored_first: str | None = None) -> bytes:
    """Pack named text parts into a ZIP that a rebuild reproduces exactly.

    ``stored_first`` names the one part that has to be written uncompressed and
    at the very beginning, which is what the OpenDocument specification demands
    of the ``mimetype`` entry.
    """
    order = list(parts)
    if stored_first is not None:
        order.remove(stored_first)
        order.insert(0, stored_first)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in order:
            info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED if name == stored_first else zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, parts[name])
    return buffer.getvalue()


def build_german_pdf() -> bytes:
    """A PDF with a German text layer, encoded the way a real one would be.

    ``/Encoding /WinAnsiEncoding`` is stated explicitly although it is not
    strictly needed: measured, pdfium reads the cp1252 umlauts of a standard
    library PDF correctly even without it. Leaving it out would make this test
    case depend on the leniency of the parser rather than on the file, and the
    day that leniency changes the failure would look like a broken indexer.

    The words carry two of the seven assertions: "Genehmigung" finds this file
    through one constituent of a compound, and "type:pdf bescheid" finds it
    because the second file with "Bescheid" in it is not a PDF.
    """
    lines = (
        "Bescheid der unteren Verwaltungsbehörde",
        "Die Grundstücksverkehrsgenehmigung wurde erteilt.",
        "Dieser Bescheid ist kostenfrei.",
    )
    content = bytearray()
    baseline = 130
    for line in lines:
        content += f"BT /F1 11 Tf 20 {baseline} Td (".encode("ascii")
        # cp1252 is what /WinAnsiEncoding means, so the bytes of the literal
        # string and the encoding declared on the font agree by construction.
        content += line.encode("cp1252")
        content += b") Tj ET\n"
        baseline -= 22
    objects = _page_objects("<< /Font << /F1 5 0 R >> >>", bytes(content), "[0 0 420 160]")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    return build_pdf(objects)


def build_german_docx() -> bytes:
    """An OOXML document with the compound, the phrase and the exclusion word.

    Three assertions live here: "Frist" finds it through the second constituent
    of "Kündigungsfrist", the phrase "drei Monate" finds it as a word sequence,
    and "bescheid -frist" must **not** find it, which is what proves the minus
    does something.
    """
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
        "<w:p><w:r><w:t>Bescheid über die Beendigung des Mietverhältnisses</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Die Kündigungsfrist beträgt drei Monate zum Quartalsende.</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Die Wohnung ist besenrein zu übergeben.</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    return _reproducible_zip(
        {
            "[Content_Types].xml": (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument'
                '.wordprocessingml.document.main+xml"/>'
                "</Types>"
            ),
            "_rels/.rels": (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships'
                '/officeDocument" Target="word/document.xml"/>'
                "</Relationships>"
            ),
            "word/document.xml": document,
        }
    )


def build_odt() -> bytes:
    """An OpenDocument text file, the format the office trio is missing so far.

    It carries the nominal inflection: the file says "Verträge", the search says
    "Vertrag", and the stemmer is what closes the gap. No other file of the
    corpus contains a word that stems to "vertrag", so the assertion cannot be
    green for another reason.
    """
    text_ns = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    office_ns = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<office:document-content xmlns:office="{office_ns}" xmlns:text="{text_ns}" office:version="1.3">'
        "<office:body><office:text>"
        "<text:h>Übersicht der laufenden Verträge</text:h>"
        "<text:p>Alle Verträge des Fachbereichs liegen im Original vor.</text:p>"
        "<text:p>Die Übersicht wird jährlich fortgeschrieben.</text:p>"
        "</office:text></office:body></office:document-content>"
    )
    manifest_ns = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<manifest:manifest xmlns:manifest="{manifest_ns}" manifest:version="1.3">'
        '<manifest:file-entry manifest:full-path="/"'
        ' manifest:media-type="application/vnd.oasis.opendocument.text"/>'
        '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
        "</manifest:manifest>"
    )
    return _reproducible_zip(
        {
            "mimetype": "application/vnd.oasis.opendocument.text",
            "content.xml": content,
            "META-INF/manifest.xml": manifest,
        },
        stored_first="mimetype",
    )


def build_umlaut_name_txt() -> bytes:
    """Windows-1252 text carrying the written out umlaut case.

    The file says "Müller" with the character, the search says "Mueller" with the
    two letters, and only the query side rewriting of plan 02-09 joins the two.
    The encoding is cp1252 for the same reason as in 08: this is what a decade of
    Windows tooling wrote, and it is the encoding in which the umlaut is a single
    byte that is invalid UTF-8.
    """
    lines = [
        "Aktenvermerk der Registratur.",
        "",
        "Zuständig für diese Akte ist Frau Müller.",
        "Rückfragen bitte an das Sekretariat richten.",
    ]
    return ("\n".join(lines) + "\n").encode("cp1252")


# --------------------------------------------------------------------------
# The OCR cases of phase 3.
#
# Nothing above this block was touched, so the twelve files of phase 1 and 2
# come out byte for byte as they did before and gate B keeps comparing the very
# same checksums for them.
#
# What is added here is everything OCR can be judged on: German administrative
# prose that exists only as pixels, the Swiss and the Austrian spelling, the
# four image formats of D-05, the two shapes that must never reach tesseract
# (an icon and a rotated photo) and ten more PDFs that are broken in ten
# different ways.
# --------------------------------------------------------------------------

FONT_DIR = Path(__file__).resolve().parents[2] / "testdata" / "fonts"
DEJAVU_SANS = FONT_DIR / "DejaVuSans.ttf"

# fonts-dejavu-core 2.37-8, read out of the base image pinned in
# backend/Dockerfile on 2026-09-01. The digest is checked before the first
# glyph is drawn: a different font file is a different corpus, and it would
# change what OCR reads without changing a single line of this script.
DEJAVU_SANS_SHA256 = "57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e"

# A4 at 150 dpi. Not 300: the pixels double the file size for a corpus whose
# job is to be committed, and 150 dpi still puts a 11 pt line at 23 pixels,
# which is inside the range tesseract is documented to work in.
A4_POINTS = (595, 842)
A4_PIXELS = (1240, 1754)

# The line that has to come out of the renderer without a single replacement
# box. Every character class this corpus depends on stands in it: the Swiss ss,
# the Austrian umlaut and a long compound with both.
GLYPH_PROBE = "Strasse Jänner Grundstücksverkehrsgenehmigung"


@cache
def _font(size: int) -> ImageFont.FreeTypeFont:
    """The one typeface of this corpus, refused if it is not the pinned one."""
    payload = DEJAVU_SANS.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != DEJAVU_SANS_SHA256:
        message = f"{DEJAVU_SANS} is not the pinned font: expected {DEJAVU_SANS_SHA256}, found {digest}"
        raise SystemExit(message)
    return ImageFont.truetype(io.BytesIO(payload), size=size)


def _glyph_bitmap(character: str, size: int) -> bytes:
    tile = Image.new("L", (size * 2, size * 2), color=255)
    ImageDraw.Draw(tile).text((size // 4, size // 4), character, font=_font(size), fill=0)
    return tile.tobytes()


def _assert_every_glyph_exists(text: str) -> None:
    """Fail the build if any character of ``text`` renders as a replacement box.

    A box in a scanned page is not a broken pixel, it is a test that proves the
    wrong thing: OCR would then be measured against a document that never
    contained the word the assertion looks for. U+E000 is in the private use
    area and no sane font maps it, so its bitmap is the shape of "missing".
    """
    missing = _glyph_bitmap(chr(0xE000), 48)
    for character in sorted(set(text)):
        if character.isspace():
            continue
        if _glyph_bitmap(character, 48) == missing:
            message = f"the pinned font has no glyph for {character!r}, the corpus would carry a box instead"
            raise SystemExit(message)


def _render_page(
    lines: Sequence[str],
    *,
    size: tuple[int, int] = A4_PIXELS,
    font_size: int = 23,
    margin: int = 110,
    leading: int = 38,
) -> Image.Image:
    """German prose as grey pixels, which is the only thing OCR can be tested on.

    Deliberately clean: no synthetic noise, no skew, no speckle. A corpus that
    carries generated dirt measures the dirt generator, and the day tesseract
    reads one word less nobody can tell whether the engine or the noise moved.
    Real world degradation belongs in a measurement, not in a fixture.
    """
    image = Image.new("L", size, color=255)
    draw = ImageDraw.Draw(image)
    font = _font(font_size)
    y = margin
    for line in lines:
        draw.text((margin, y), line, font=font, fill=0)
        y += leading
    return image


def _flate_image_object(image: Image.Image) -> bytes:
    """One greyscale page as a PDF image object, deflated at the highest level."""
    width, height = image.size
    return _stream_object(
        f"/Type /XObject /Subtype /Image /Width {width} /Height {height} /ColorSpace /DeviceGray"
        " /BitsPerComponent 8 /Filter /FlateDecode",
        zlib.compress(image.tobytes(), 9),
    )


def _pdf_string(line: str) -> bytes:
    """A literal string for a content stream, cp1252 as /WinAnsiEncoding means."""
    raw = line.encode("cp1252")
    for special, escaped in ((b"\\", b"\\\\"), (b"(", b"\\("), (b")", b"\\)")):
        raw = raw.replace(special, escaped)
    return raw


# A page is either a rendered image or a tuple of lines that becomes a real text
# layer. That distinction is the whole subject of the mixed document below.
Page = Image.Image | tuple[str, ...]


def _assemble_document(pages: Sequence[Page], *, media_box: tuple[int, int] = A4_POINTS) -> bytes:
    """Several pages of either kind into one PDF, numbered and cross referenced."""
    width, height = media_box
    # Object 1 is the catalogue and object 2 the page tree. Both are written at
    # the end, because the page tree can only name its children once they exist.
    objects: list[bytes] = [b"", b""]

    def add(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    font_number = 0
    if any(isinstance(page, tuple) for page in pages):
        font_number = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")

    page_numbers: list[int] = []
    for page in pages:
        if isinstance(page, tuple):
            content = bytearray()
            baseline = height - 60
            for line in page:
                content += f"BT /F1 11 Tf 50 {baseline} Td (".encode("ascii")
                content += _pdf_string(line)
                content += b") Tj ET\n"
                baseline -= 20
            contents = add(_stream_object("", bytes(content)))
            resources = f"<< /Font << /F1 {font_number} 0 R >> >>"
        else:
            image_number = add(_flate_image_object(page))
            contents = add(_stream_object("", f"q {width} 0 0 {height} 0 0 cm /Im1 Do Q\n".encode("ascii")))
            resources = f"<< /XObject << /Im1 {image_number} 0 R >> >>"
        page_numbers.append(
            add(
                (
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}]"
                    f" /Resources {resources} /Contents {contents} 0 R >>"
                ).encode("ascii")
            )
        )

    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{number} 0 R" for number in page_numbers)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_numbers)} >>".encode("ascii")
    return build_pdf(objects)


# --------------------------------------------------------------------------
# The German, Swiss and Austrian prose. Every one of these blocks is invented;
# not one line comes from a real document, which is the corpus answer to
# threat T-03-603.
# --------------------------------------------------------------------------

RATSVORLAGE_PAGES: tuple[tuple[str, ...], ...] = (
    (
        "Gemeinde Musterhausen",
        "Vorlage für den Gemeinderat",
        "",
        "Betreff: Aufstellung des Bebauungsplans Nummer 14",
        "Sitzung am 12. November 2026, öffentlicher Teil",
        "",
        "Sachverhalt",
        "",
        "Der Gemeinderat hat die Verwaltung im Frühjahr beauftragt, die",
        "planungsrechtlichen Voraussetzungen für die Erweiterung des",
        "Gewerbegebiets im nördlichen Ortsteil zu prüfen. Die Prüfung",
        "ist abgeschlossen. Die Flächen sind geeignet, die Erschließung",
        "ist über die vorhandene Zufahrt möglich und ein Ausbau der",
        "Zufahrt ist nach heutigem Stand nicht erforderlich.",
        "",
        "Die Untere Naturschutzbehörde hat auf zwei Gehölzbestände am",
        "östlichen Rand hingewiesen. Beide bleiben erhalten und werden",
        "als Fläche zum Erhalt von Bäumen und Sträuchern festgesetzt.",
    ),
    (
        "Vorlage für den Gemeinderat, Blatt 2",
        "",
        "Beteiligung der Träger öffentlicher Belange",
        "",
        "Die Beteiligung wurde im Sommer durchgeführt. Von den",
        "angeschriebenen Stellen haben sich elf geäußert. Die",
        "Stellungnahmen betreffen überwiegend die Entwässerung und",
        "den Anschluss an das öffentliche Kanalnetz.",
        "",
        "Das Wasserwirtschaftsamt bittet um einen Nachweis über die",
        "Rückhaltung des Niederschlagswassers auf den Grundstücken.",
        "Der Nachweis wird mit dem Erschließungsplan vorgelegt.",
        "",
        "Die Kosten der Planung trägt die Gemeinde. Sie sind im",
        "Haushalt des laufenden Jahres veranschlagt.",
    ),
    (
        "Vorlage für den Gemeinderat, Blatt 3",
        "",
        "Beschlussvorschlag",
        "",
        "Der Gemeinderat beschließt die Aufstellung des",
        "Bebauungsplans für das Gebiet nördlich der Feldwiese.",
        "Die Verwaltung wird beauftragt, die Offenlegung",
        "vorzubereiten und die Öffentlichkeit zu unterrichten.",
        "",
        "Anlagen: Übersichtskarte, Stellungnahmen, Kostenschätzung",
    ),
)

PACHT_TEXT_PAGES: tuple[tuple[str, ...], ...] = (
    (
        "Pachtvereinbarung über eine städtische Grünfläche",
        "",
        "Zwischen der Stadt Musterhausen und dem Kleingartenverein",
        "Sonnenhang wird die nachstehende Vereinbarung geschlossen.",
        "",
        "Paragraf 1 Gegenstand",
        "Verpachtet wird die Fläche südlich des Sportplatzes mit einer",
        "Größe von 2400 Quadratmetern zur gärtnerischen Nutzung.",
        "",
        "Paragraf 2 Laufzeit",
        "Die Nutzung beginnt am 1. April 2027 und läuft auf unbestimmte",
        "Zeit. Die Bedingungen der Beendigung stehen in Paragraf 8.",
    ),
    (
        "Paragraf 3 Pachtzins",
        "Der jährliche Zins beträgt 0,35 Euro je Quadratmeter und ist",
        "jeweils zum Ende des ersten Quartals zu entrichten.",
        "",
        "Paragraf 4 Unterhaltung",
        "Der Pächter hält die Wege frei und pflegt die Hecken an der",
        "Grenze zum Sportplatz. Bauliche Anlagen bedürfen der",
        "vorherigen schriftlichen Zustimmung der Stadt.",
        "",
        "Die Anlagen 1 bis 3 dieser Vereinbarung liegen als Kopie der",
        "unterschriebenen Ausfertigung bei und sind Bestandteil.",
    ),
)

PACHT_SCAN_PAGES: tuple[tuple[str, ...], ...] = (
    (
        "Anlage 1 zur Pachtvereinbarung",
        "",
        "Lageplan der Fläche, Maßstab 1 zu 1000",
        "",
        "Die schraffierte Fläche südlich des Sportplatzes ist der",
        "Gegenstand der Nutzung. Die gestrichelte Linie bezeichnet",
        "den vorhandenen Wirtschaftsweg, der freizuhalten ist.",
        "",
        "Aufgenommen durch das Vermessungsamt am 3. Februar 2026.",
    ),
    (
        "Anlage 2 zur Pachtvereinbarung",
        "",
        "Bestandsaufnahme der vorhandenen Anlagen",
        "",
        "Gerätehaus aus Holz, 6 Quadratmeter, Zustand einfach",
        "Wasseranschluss am nördlichen Rand, abgesperrt",
        "Zaun zur Feldwiese, 40 Meter, teilweise erneuert",
        "",
        "Die Aufnahme erfolgte im Beisein des Vorstands.",
    ),
    (
        "Anlage 3 zur Pachtvereinbarung",
        "",
        "Unterschriften der Beteiligten",
        "",
        "Für die Stadt Musterhausen, Amt für Liegenschaften",
        "Für den Kleingartenverein Sonnenhang, der Vorstand",
        "",
        "Die Ausfertigung wurde eingescannt und der Akte beigefügt.",
    ),
)

SCHWEIZ_PAGE: tuple[str, ...] = (
    "Gemeinde Musterikon, Kanton Zürich",
    "Bauamt",
    "",
    "Baubewilligung für den Umbau eines Wohnhauses",
    "",
    "Das Grundstück liegt an der Bahnhofstrasse 12. Die Zufahrt",
    "erfolgt weiterhin ab der Strasse zum Seeufer. Die Parzelle",
    "bleibt in ihrer bisherigen Grösse bestehen.",
    "",
    "Die Bauherrschaft hat die Arbeiten spätestens drei Jahre nach",
    "Rechtskraft dieser Bewilligung aufzunehmen. Die Gebühren",
    "betragen 1200 Franken und sind mit separater Rechnung zu",
    "begleichen.",
    "",
    "Die Rechtsmittelbelehrung steht auf der Rückseite.",
)

OESTERREICH_PAGE: tuple[str, ...] = (
    "Stadtgemeinde Musterdorf",
    "Bezirkshauptmannschaft Musterkreis",
    "",
    "Mitteilung vom 15. Jänner 2026",
    "",
    "Der Grundbuchsauszug zur Liegenschaft im Ortsteil Hangfeld",
    "liegt dieser Mitteilung bei. Die Erledigung der Anzeige",
    "erfolgt noch im Jänner, sobald die Vermessung vorliegt.",
    "",
    "Allfällige Rückfragen richten Sie bitte an die Kanzlei. Die",
    "Amtsstunden sind Montag bis Donnerstag von 8 bis 12 Uhr.",
    "",
    "Der Bezirkshauptmann",
)

ZAHLUNGSERINNERUNG_PAGE: tuple[str, ...] = (
    "Stadtkasse Musterhausen",
    "",
    "Zahlungserinnerung",
    "",
    "Zu der Rechnung vom 2. Juli 2026 ist bisher kein Eingang",
    "verbucht worden. Wir bitten Sie, den offenen Betrag von",
    "84,00 Euro innerhalb der nächsten zwei Wochen zu überweisen.",
    "",
    "Sollte sich Ihre Zahlung mit diesem Schreiben überschnitten",
    "haben, betrachten Sie es bitte als gegenstandslos.",
)

# The four image formats of D-05, plus the two shapes that must never reach
# tesseract. Short on purpose: an image file in a Nextcloud is a snapshot of a
# note, not a full page, and the plausibility check of a later plan has to see
# a realistic small image.
BELEG_LINES: tuple[str, ...] = (
    "Zahlungsavis",
    "Rechnungsnummer 2026-0815",
    "Betrag: 148,50 Euro",
    "Eingang am 4. März 2026",
)

AUSHANG_LINES: tuple[str, ...] = (
    "Aushang der Stadtreinigung",
    "Sperrmüllabfuhr am Dienstag",
    "Bitte die Gehwege freihalten",
)

UEBERMITTLUNG_LINES: tuple[str, ...] = (
    "Übermittlungsprotokoll",
    "Empfänger: Bauamt Musterhausen",
    "Seiten: 1, Status: erfolgreich",
)

RUECKRUF_LINES: tuple[str, ...] = (
    "Rückrufbitte",
    "Frau Sommer aus dem Ordnungsamt",
    "Durchwahl 4711, bis 16 Uhr",
)

SENDEBERICHT_PAGES: tuple[tuple[str, ...], ...] = (
    ("Sendebericht", "Übertragung vom 9. Mai 2026", "Blatt 1 von 3"),
    ("Zweites Blatt der Übertragung", "Anschluss und Uhrzeit geprüft", "Blatt 2 von 3"),
    ("Drittes Blatt der Übertragung", "Keine Störung aufgetreten", "Blatt 3 von 3"),
)

LIEFERSCHEIN_LINES: tuple[str, ...] = (
    "Lieferschein",
    "Aktenordner, 12 Stück",
    "Übergabe an die Registratur",
)

SNIPPET_SIZE = (1000, 260)


def _image_bytes(image: Image.Image, image_format: str, **options: object) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=image_format, **options)
    return buffer.getvalue()


def build_beleg_jpg() -> bytes:
    """A photographed slip as JPEG, the format most phone uploads arrive in."""
    page = _render_page(BELEG_LINES, size=SNIPPET_SIZE, font_size=40, margin=40, leading=58)
    return _image_bytes(page, "JPEG", quality=88, optimize=False)


def build_aushang_png() -> bytes:
    page = _render_page(AUSHANG_LINES, size=SNIPPET_SIZE, font_size=40, margin=40, leading=58)
    return _image_bytes(page, "PNG", optimize=True)


def build_uebermittlung_tiff() -> bytes:
    page = _render_page(UEBERMITTLUNG_LINES, size=SNIPPET_SIZE, font_size=40, margin=40, leading=58)
    return _image_bytes(page, "TIFF", compression="tiff_deflate")


def build_rueckruf_webp() -> bytes:
    page = _render_page(RUECKRUF_LINES, size=SNIPPET_SIZE, font_size=40, margin=40, leading=58)
    return _image_bytes(page, "WEBP", lossless=True, quality=100, method=4)


def build_sendebericht_tiff() -> bytes:
    """A multi page TIFF, which is what a fax archive turns into.

    One file, three images, and only the first one is visible to a reader that
    never asks for the further frames. An extractor that stops after frame zero
    loses two thirds of the document and says nothing about it.
    """
    pages = [
        _render_page(lines, size=SNIPPET_SIZE, font_size=40, margin=40, leading=58) for lines in SENDEBERICHT_PAGES
    ]
    buffer = io.BytesIO()
    pages[0].save(buffer, format="TIFF", compression="tiff_deflate", save_all=True, append_images=pages[1:])
    return buffer.getvalue()


def build_icon_png() -> bytes:
    """48 by 48 pixels: below any plausibility threshold, and that is its job.

    Nextcloud is full of these. Running tesseract over an icon costs seconds and
    produces noise, so the OCR route has to refuse it on the short edge alone,
    before a single page is rendered.
    """
    icon = Image.new("L", (48, 48), color=255)
    draw = ImageDraw.Draw(icon)
    draw.rectangle((6, 6, 41, 41), outline=0, width=2)
    draw.text((17, 8), "i", font=_font(28), fill=0)
    return _image_bytes(icon, "PNG", optimize=True)


def build_gedreht_jpg() -> bytes:
    """A document photographed sideways, with EXIF orientation 6.

    The pixels lie on their side and the tag says "rotate 90 degrees clockwise
    for display". Every viewer honours it, and an OCR path that reads the raw
    pixels gets a column of characters that tesseract cannot line up. The file
    exists so that the rotation is applied somewhere in the pipeline instead of
    being assumed away.
    """
    upright = _render_page(LIEFERSCHEIN_LINES, size=SNIPPET_SIZE, font_size=40, margin=40, leading=58)
    # PIL rotates counter clockwise, so the stored pixels need the opposite of
    # what the tag asks a viewer to do.
    sideways = upright.rotate(90, expand=True)
    exif = Image.Exif()
    exif[0x0112] = 6
    return _image_bytes(sideways, "JPEG", quality=88, optimize=False, exif=exif.tobytes())


def build_ratsvorlage_scan() -> bytes:
    """Three pages of German council prose that exist only as pixels."""
    return _assemble_document([_render_page(lines) for lines in RATSVORLAGE_PAGES])


def build_pacht_with_annex() -> bytes:
    """Two pages with a real text layer and three scanned annex pages.

    This is the document that both extremes get wrong. A per document average
    over five pages drowns the two readable ones; a rule that says "one page
    without text means scan" sends a perfectly readable agreement into OCR.
    """
    pages: list[Page] = [*PACHT_TEXT_PAGES, *(_render_page(lines) for lines in PACHT_SCAN_PAGES)]
    return _assemble_document(pages)


def build_schweiz_scan() -> bytes:
    """The Swiss spelling, and only here: Strasse instead of Straße."""
    return _assemble_document([_render_page(SCHWEIZ_PAGE)])


def build_oesterreich_scan() -> bytes:
    """The Austrian month name, and only here: Jänner."""
    return _assemble_document([_render_page(OESTERREICH_PAGE)])


def build_image_only_a4() -> bytes:
    """One A4 page, one image, no text object anywhere in the file."""
    return _assemble_document([_render_page(ZAHLUNGSERINNERUNG_PAGE)])


# --------------------------------------------------------------------------
# Ten ways a PDF can be broken. Each one is a different failure path, and each
# one has a line in testdata/CORPUS.md that says which.
# --------------------------------------------------------------------------


def build_truncated_trailer() -> bytes:
    """A file that stops in the middle of its trailer, as an aborted copy does."""
    intact = build_text_layer_pdf()
    return intact[: intact.rindex(b"trailer") + 20]


def build_broken_xref() -> bytes:
    """Every cross reference offset points somewhere else than the object does."""
    intact = bytearray(build_text_layer_pdf())
    start = intact.index(b"xref")
    tail = bytes(intact[start:]).replace(b"00000 n", b"00000 x")
    return bytes(intact[:start]) + tail


def build_huge_page_count() -> bytes:
    """Nine hundred bytes that declare one hundred thousand pages.

    Threat T-03-601. A reader that trusts /Count and allocates per page dies on
    a file that fits into a network packet, and the page cap plus RLIMIT_AS are
    exactly what has to hold here. It must not hang the test run either.
    """
    content = b"BT /F1 12 Tf 20 70 Td (One page, one hundred thousand promised.) Tj ET\n"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 100000 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 120] /Resources << /Font << /F1 5 0 R >> >>"
            b" /Contents 4 0 R >>"
        ),
        _stream_object("", content),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    return build_pdf(objects)


def build_null_bytes_header() -> bytes:
    """A PDF header followed by a block of NUL bytes instead of objects."""
    return b"%PDF-1.7\n" + bytes(512) + b"%%EOF\n"


def build_no_pages() -> bytes:
    """Structurally valid, correctly cross referenced, and empty of pages."""
    return build_pdf(
        [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [] /Count 0 >>",
        ]
    )


def build_double_compressed_stream() -> bytes:
    """A content stream behind two chained Flate filters.

    Legal per the specification and rare in the wild, which is why it is here:
    a decoder that applies only the first filter of the array hands the parser
    compressed rubbish and reports a corrupt document.
    """
    inner = b"BT /F1 12 Tf 20 70 Td (Zweimal komprimierter Inhalt.) Tj ET\n"
    payload = zlib.compress(zlib.compress(inner, 9), 9)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 120] /Resources << /Font << /F1 5 0 R >> >>"
            b" /Contents 4 0 R >>"
        ),
        _stream_object("/Filter [/FlateDecode /FlateDecode]", payload),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    return build_pdf(objects)


def build_odd_page_size() -> bytes:
    """A page of 14400 by 14400 points, the largest the format allows.

    Two hundred inches on a side. Rendering it at 150 dpi would be nine
    gigapixels, so this file is the reason the OCR route has to cap the raster
    by pixels and not only by page count.
    """
    content = b"BT /F1 400 Tf 400 7000 Td (Riesenformat) Tj ET\n"
    objects = _page_objects("<< /Font << /F1 5 0 R >> >>", content, "[0 0 14400 14400]")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    return build_pdf(objects)


def build_startxref_into_nothing() -> bytes:
    """Correct objects, correct xref table, and a startxref that points past the end."""
    intact = build_text_layer_pdf()
    start = intact.rindex(b"startxref\n") + len(b"startxref\n")
    end = intact.index(b"\n", start)
    return intact[:start] + b"999999999" + intact[end:]


def build_page_tree_cycle() -> bytes:
    """A page tree that contains itself, which is a loop for a naive walker."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [2 0 R 3 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 120] /Contents 4 0 R >>",
        _stream_object("", b"BT ET\n"),
    ]
    return build_pdf(objects)


# --------------------------------------------------------------------------
# The edge paths of the launch hardening. Everything above this line is a file
# that is broken; everything below it is a file that wants something.
# --------------------------------------------------------------------------

# The declared size a single archive member may reach before the extractor
# refuses to hand it to a loader. Mirrored from
# backend/src/findling/config.py, EXTRACT_ARCHIVE_MEMBER_MAX_BYTES, and
# deliberately a second spelling instead of an import: this script has no
# dependency on the backend package, and a corpus file that silently followed a
# changed cap would stop being a test of the cap. The two numbers are compared
# in backend/tests/test_extract_documents.py, so the duplicate cannot drift.
ARCHIVE_MEMBER_CAP_BYTES = 64 * 1024 * 1024

_BOMB_HEAD = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
    "<w:p><w:r><w:t>"
).encode("ascii")

_BOMB_TAIL = b"</w:t></w:r></w:p></w:body></w:document>"

# One mebibyte of the same byte, written over and over. Deflate needs to see the
# repetition inside its 32 kB window, so any block size well above that gives the
# same ratio; a megabyte keeps the number of write calls small.
_BOMB_BLOCK = b"A" * (1 << 20)


def build_zip_bomb_docx() -> bytes:
    """A DOCX whose single part expands to one byte more than the cap allows.

    The part is written as a stream and never as one string, so building the
    corpus does not hold the unpacked 64 MiB in memory at any moment; the deflate
    window does the work and the file that lands in the repository is 65 kB.

    Those 65 kB are a floor and not a choice. Deflate cannot beat 1032 to 1: a
    length code carries at most 258 bytes and costs at least two bits (RFC 1951),
    so a member of 64 MiB plus one byte cannot compress below roughly 65 kB.
    The two ZIP methods that would do better were measured on 2026-09-06 and
    rejected: bzip2 lands at 410 bytes and LZMA at 9848, but neither is a
    compression method an OPC package may carry, so the file would stop being a
    document a reader can open, and both would stake the byte for byte
    reproducibility of the corpus on a compressor this repository has never
    staked it on, where zlib already carries the PNG and the PDF streams above.

    The two small parts beside it are what makes this a package rather than a
    ZIP with one entry: the guard walks the whole directory, and a bomb that
    arrived without the parts a DOCX has would be refused for the wrong reason.
    """
    filler = ARCHIVE_MEMBER_CAP_BYTES + 1 - len(_BOMB_HEAD) - len(_BOMB_TAIL)
    parts = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument'
            '.wordprocessingml.document.main+xml"/>'
            "</Types>"
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships'
            '/officeDocument" Target="word/document.xml"/>'
            "</Relationships>"
        ),
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, text in parts.items():
            info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, text)

        info = zipfile.ZipInfo("word/document.xml", date_time=ZIP_TIMESTAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        with archive.open(info, "w") as member:
            member.write(_BOMB_HEAD)
            written = 0
            while written < filler:
                block = _BOMB_BLOCK[: min(len(_BOMB_BLOCK), filler - written)]
                member.write(block)
                written += len(block)
            member.write(_BOMB_TAIL)
    return buffer.getvalue()


WINANSI_FONT = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"


def _winansi_content(lines: Sequence[str]) -> bytes:
    """A content stream of German lines for a page 420 by 160 points.

    Same construction as build_german_pdf above and for the same reason: the
    bytes of the literal string and the encoding declared on the font agree by
    construction instead of by the leniency of the parser.
    """
    content = bytearray()
    baseline = 120
    for line in lines:
        content += f"BT /F1 11 Tf 20 {baseline} Td (".encode("ascii")
        content += line.encode("cp1252")
        content += b") Tj ET\n"
        baseline -= 22
    return bytes(content)


def build_open_action_javascript_pdf() -> bytes:
    """A document that asks a reader to run a script the moment it is opened.

    ``/OpenAction`` plus a name tree of document level JavaScript is the shape
    that carried a decade of PDF malware, and it is the reason the text route of
    this project goes through pypdf and pypdfium2 rather than through a viewer:
    neither of them carries a script engine, and nothing in this repository ever
    looks at ``/OpenAction``. The word Skriptmarke stands inside the script and
    nowhere else, so a test can say the difference between "the script did not
    run" and "the script ran and left no trace".
    """
    content = _winansi_content(
        (
            "Startaktion mit einem Skriptobjekt",
            "Diese Seite wird gelesen, das Skript wird nie ausgeführt.",
        )
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R /OpenAction 6 0 R /Names << /JavaScript 7 0 R >> >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 160] /Resources << /Font << /F1 5 0 R >> >>"
            b" /Contents 4 0 R >>"
        ),
        _stream_object("", content),
        WINANSI_FONT,
        b'<< /Type /Action /S /JavaScript /JS (app.alert\\("Skriptmarke"\\);) >>',
        b"<< /Names [(start) 6 0 R] >>",
    ]
    return build_pdf(objects)


def build_embedded_file_pdf() -> bytes:
    """A document with a second file inside it.

    An attachment is the quiet half of the same threat as the archive bomb: a
    reader that unpacks one puts an attacker chosen name on the disk of the
    container, and an extractor that reads one puts the content of a document
    nobody attached into the index of the document somebody did attach. The
    marker word sits in the attachment alone.
    """
    attachment = b"Anlagenmarke: this attachment must never be unpacked and never be indexed.\n"
    content = _winansi_content(
        (
            "Eine Anlage hängt an dieser Seite",
            "Die eingebettete Datei wird beim Lesen nicht ausgepackt.",
        )
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R /Names << /EmbeddedFiles << /Names [(anlage.txt) 6 0 R] >> >> >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 160] /Resources << /Font << /F1 5 0 R >> >>"
            b" /Contents 4 0 R >>"
        ),
        _stream_object("", content),
        WINANSI_FONT,
        b"<< /Type /Filespec /F (anlage.txt) /UF (anlage.txt) /EF << /F 7 0 R >> >>",
        _stream_object("/Type /EmbeddedFile /Subtype /text#2Fplain", attachment),
    ]
    return build_pdf(objects)


def build_uri_action_pdf() -> bytes:
    """A document with a link annotation that names an address.

    The address is data and has to stay data. It points at the discard port of
    the loopback interface, so even a run that did try to reach it would fail
    fast and locally instead of touching anything outside the machine, and the
    marker word inside the address is what a test can look for in the index.
    """
    content = _winansi_content(
        (
            "Verweis auf eine Netzadresse",
            "Die Adresse bleibt eine Zeichenkette und wird nie aufgerufen.",
        )
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 160] /Resources << /Font << /F1 5 0 R >> >>"
            b" /Contents 4 0 R /Annots [6 0 R] >>"
        ),
        _stream_object("", content),
        WINANSI_FONT,
        (
            b"<< /Type /Annot /Subtype /Link /Rect [20 110 400 130] /Border [0 0 0]"
            b" /A << /Type /Action /S /URI /URI (http://127.0.0.1:9/Netzmarke) >> >>"
        ),
    ]
    return build_pdf(objects)


# How deep the nested structure of file 39 goes.
#
# Measured on 2026-09-06 with pypdfium2 5.13.0 at the depths 100, 400, 500, 512,
# 600, 1000, 5000 and 50000, once nested into the page dictionary and once into
# the catalog: every single one of them ends in `indexed`, because the parser
# refuses the nested object past its own recursion limit and reads the page
# regardless, and the whole run takes 13 to 38 milliseconds, growing with the
# size of the file and not with the depth.
#
# A thousand is the value this file carries because the case has to sit
# unambiguously on one side of the caps and never near them: a thousand levels
# are far more than any document a person produces, the verdict arrives four
# orders of magnitude inside the extraction timeout of 120 seconds, and the file
# stays under three kilobytes. A depth that landed near a cap would be a coin
# toss between a fast machine and a loaded CI runner rather than a test.
NESTING_DEPTH = 1000


def build_deeply_nested_pdf() -> bytes:
    """A page dictionary with a thousand levels of nested arrays inside it.

    Inline and not behind an indirect reference, which is the whole point: an
    object nobody dereferences is never parsed, so a nested blob in an object of
    its own would measure nothing at all. Written into the page dictionary, the
    structure is on the road the parser has to walk to reach the page.
    """
    nest = b"[" * NESTING_DEPTH + b"0" + b"]" * NESTING_DEPTH
    content = _winansi_content(
        (
            "Tief verschachtelte Objektstruktur",
            "Der Text dieser Seite bleibt trotzdem lesbar.",
        )
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 160] /Resources << /Font << /F1 5 0 R >> >>"
        b" /Contents 4 0 R /FindlingNest " + nest + b" >>",
        _stream_object("", content),
        WINANSI_FONT,
    ]
    return build_pdf(objects)


# --------------------------------------------------------------------------
# AES, in the standard library alone, for the one corpus file that needs it.
#
# The corpus has carried RC4 with 40 bits since phase 1, which is what a decade
# old document looks like. What it lacked is what a current office suite writes,
# and that is AES with 256 bits under revision 6 of the standard security
# handler. Building one means encrypting, and no dependency of this project can
# do it: the lock file carries neither cryptography nor pycryptodome, on purpose,
# because this app never decrypts anything, and adding a package to build a test
# fixture is the kind of supply chain growth the phase forbids outright.
#
# So AES stands here, in about a hundred lines, and it is checked rather than
# trusted: _assert_aes_matches_the_standard runs the two known answer vectors of
# FIPS 197 appendix C, which are published test data and not something this file
# produced. Measured on 2026-09-06, the hash of algorithm 2.B computed here also
# agrees byte for byte with the implementation pypdf carries, driven by the AES
# below. Two independent implementations of two different layers, which is what
# makes the agreement mean something.
# --------------------------------------------------------------------------


def _aes_substitution_box() -> bytes:
    """The AES substitution box, computed rather than typed out.

    A table of 256 hand written hexadecimal numbers is a table with a typo in
    it, and the typo would show up as a corpus file nobody can open. The
    generator loop below is the one from the standard: walk the multiplicative
    group of GF(2^8) and apply the affine transformation.
    """
    table = bytearray(256)
    table[0] = 0x63
    pointer = inverse = 1
    while True:
        # pointer is multiplied by three, inverse is divided by three, so the two
        # walk the group in opposite directions and meet at every pair.
        pointer = (pointer ^ ((pointer << 1) & 0xFF) ^ (0x1B if pointer & 0x80 else 0)) & 0xFF
        inverse = (inverse ^ (inverse << 1)) & 0xFF
        inverse = (inverse ^ (inverse << 2)) & 0xFF
        inverse = (inverse ^ (inverse << 4)) & 0xFF
        if inverse & 0x80:
            inverse ^= 0x09
        rotated = [((inverse << bits) | (inverse >> (8 - bits))) & 0xFF for bits in (1, 2, 3, 4)]
        table[pointer] = (inverse ^ rotated[0] ^ rotated[1] ^ rotated[2] ^ rotated[3] ^ 0x63) & 0xFF
        if pointer == 1:
            return bytes(table)


AES_SBOX = _aes_substitution_box()


def _xtime(value: int) -> int:
    """Multiplication by two in GF(2^8), the one field operation AES needs."""
    doubled = value << 1
    return (doubled ^ 0x1B) & 0xFF if doubled & 0x100 else doubled


def _aes_key_schedule(key: bytes) -> list[list[int]]:
    """The round keys of an AES key of 128 or 256 bits, as four byte words."""
    words_in_key = len(key) // 4
    rounds = words_in_key + 6
    words = [list(key[4 * index : 4 * index + 4]) for index in range(words_in_key)]
    round_constant = 1
    for index in range(words_in_key, 4 * (rounds + 1)):
        word = list(words[index - 1])
        if index % words_in_key == 0:
            word = [AES_SBOX[byte] for byte in word[1:] + word[:1]]
            word[0] ^= round_constant
            round_constant = _xtime(round_constant)
        elif words_in_key > 6 and index % words_in_key == 4:
            word = [AES_SBOX[byte] for byte in word]
        words.append([left ^ right for left, right in zip(words[index - words_in_key], word, strict=True)])
    return words


def _aes_encrypt_block(block: bytes, words: list[list[int]], rounds: int) -> bytes:
    """One sixteen byte block through the four steps of every AES round."""
    state = list(block)

    def add_round_key(number: int) -> None:
        for column in range(4):
            word = words[number * 4 + column]
            for row in range(4):
                state[row + 4 * column] ^= word[row]

    add_round_key(0)
    for number in range(1, rounds + 1):
        state[:] = [AES_SBOX[byte] for byte in state]
        shifted = list(state)
        for row in range(1, 4):
            for column in range(4):
                shifted[row + 4 * column] = state[row + 4 * ((column + row) % 4)]
        state[:] = shifted
        if number != rounds:
            # MixColumns, written out over the column rather than as a matrix
            # multiplication: the sum of the four bytes plus one doubled
            # difference is the same thing and needs no second table.
            for column in range(4):
                cell = state[4 * column : 4 * column + 4]
                total = cell[0] ^ cell[1] ^ cell[2] ^ cell[3]
                for row in range(4):
                    state[4 * column + row] = cell[row] ^ total ^ _xtime(cell[row] ^ cell[(row + 1) % 4])
        add_round_key(number)
    return bytes(state)


def aes_cbc_encrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    """AES in cipher block chaining mode, without padding of its own."""
    words = _aes_key_schedule(key)
    rounds = len(key) // 4 + 6
    out = bytearray()
    previous = iv
    for offset in range(0, len(data), 16):
        block = bytes(left ^ right for left, right in zip(data[offset : offset + 16], previous, strict=True))
        previous = _aes_encrypt_block(block, words, rounds)
        out += previous
    return bytes(out)


def aes_ecb_encrypt(key: bytes, data: bytes) -> bytes:
    """AES block by block, which is what the /Perms entry of the PDF asks for."""
    words = _aes_key_schedule(key)
    rounds = len(key) // 4 + 6
    return b"".join(_aes_encrypt_block(data[offset : offset + 16], words, rounds) for offset in range(0, len(data), 16))


# FIPS 197, appendix C.1 and C.3: one plaintext, two keys, two published
# ciphertexts. Nothing in this file produced these numbers.
FIPS_197_PLAINTEXT = bytes.fromhex("00112233445566778899aabbccddeeff")
FIPS_197_VECTORS: tuple[tuple[bytes, str], ...] = (
    (bytes(range(16)), "69c4e0d86a7b0430d8cdb78070b4c55a"),
    (bytes(range(32)), "8ea2b7ca516745bfeafc49904b496089"),
)


def _assert_aes_matches_the_standard() -> None:
    """Refuse to build a corpus with an AES that is off by one bit.

    An encryption that is subtly wrong produces a file that looks encrypted, is
    committed, and can never be opened by anybody with the password this
    repository publishes. That is a fixture that lies, and a lying fixture is
    worse than a missing one.
    """
    for key, expected in FIPS_197_VECTORS:
        produced = aes_ecb_encrypt(key, FIPS_197_PLAINTEXT).hex()
        if produced != expected:
            message = f"AES with a {len(key) * 8} bit key produced {produced}, FIPS 197 says {expected}"
            raise SystemExit(message)


def _hash_revision_6(password: bytes, salt: bytes, extra: bytes) -> bytes:
    """Algorithm 2.B of ISO 32000-2, the hardened password hash of revision 6.

    Deliberately expensive, and it is the reason building this one file takes
    about four seconds: the loop runs at least sixty four rounds, and every round
    encrypts forty times the password block. ``extra`` is empty for the user
    password and carries the /U entry for the owner password.
    """
    digest = hashlib.sha256(password + salt + extra).digest()
    round_number = 0
    while True:
        block = (password + digest + extra) * 64
        encrypted = aes_cbc_encrypt(digest[:16], digest[16:32], block)
        chosen = (hashlib.sha256, hashlib.sha384, hashlib.sha512)[sum(encrypted[:16]) % 3]
        digest = chosen(encrypted).digest()
        round_number += 1
        if round_number >= 64 and encrypted[-1] <= round_number - 32:
            return digest[:32]


# Every value that a real encryptor would draw at random, derived from a fixed
# string instead. A random salt or a random initialisation vector would make the
# file different on every build, and a corpus that is not byte identical is a
# corpus readonly-gate cannot measure. Nothing here is protected by any of them.
AES_FILE_KEY = hashlib.sha256(b"findling-corpus-aes-file-key").digest()
AES_USER_VALIDATION_SALT = hashlib.sha256(b"findling-corpus-user-validation").digest()[:8]
AES_USER_KEY_SALT = hashlib.sha256(b"findling-corpus-user-key").digest()[:8]
AES_OWNER_VALIDATION_SALT = hashlib.sha256(b"findling-corpus-owner-validation").digest()[:8]
AES_OWNER_KEY_SALT = hashlib.sha256(b"findling-corpus-owner-key").digest()[:8]
AES_STREAM_IV = hashlib.sha256(b"findling-corpus-aes-stream-iv").digest()[:16]


def build_aes_encrypted_pdf() -> bytes:
    """A PDF encrypted the way a current office suite encrypts one.

    Standard security handler, version 5, revision 6, AES with 256 bits on both
    strings and streams. The passwords are the same two the RC4 file of phase 1
    carries and testdata/CORPUS.md publishes, so a reviewer needs one password
    for both encrypted files.

    Algorithms 8, 9 and 10 of ISO 32000-2 in order: /U and /UE from the user
    password, /O and /OE from the owner password over the finished /U, and
    /Perms as the permission bits encrypted with the file key so that a reader
    can tell a tampered permission set from an honest one.
    """
    user_password = USER_PASSWORD.encode("utf-8")
    owner_password = OWNER_PASSWORD.encode("utf-8")

    user_entry = _hash_revision_6(user_password, AES_USER_VALIDATION_SALT, b"")
    user_entry += AES_USER_VALIDATION_SALT + AES_USER_KEY_SALT
    user_key = aes_cbc_encrypt(_hash_revision_6(user_password, AES_USER_KEY_SALT, b""), bytes(16), AES_FILE_KEY)

    owner_entry = _hash_revision_6(owner_password, AES_OWNER_VALIDATION_SALT, user_entry)
    owner_entry += AES_OWNER_VALIDATION_SALT + AES_OWNER_KEY_SALT
    owner_key = aes_cbc_encrypt(
        _hash_revision_6(owner_password, AES_OWNER_KEY_SALT, user_entry), bytes(16), AES_FILE_KEY
    )

    permissions = -1
    # Algorithm 10: the permission bits, four filler bytes the specification
    # prescribes as 0xFF, the flag that the metadata is encrypted too, the magic
    # word adb, and four bytes a writer may choose.
    perms_block = struct.pack("<i", permissions) + b"\xff\xff\xff\xffTadb" + b"find"

    content = _winansi_content(
        (
            "Hinter AES 256 und Revision 6",
            "Dieser Satz wird nie im Index landen.",
        )
    )
    padding = 16 - len(content) % 16
    padded = content + bytes([padding]) * padding
    encrypted_content = AES_STREAM_IV + aes_cbc_encrypt(AES_FILE_KEY, AES_STREAM_IV, padded)

    objects = _page_objects("<< /Font << /F1 5 0 R >> >>", encrypted_content, "[0 0 420 160]")
    objects.append(WINANSI_FONT)
    # The strings of the encryption dictionary itself are never encrypted.
    objects.append(
        (
            "<< /Filter /Standard /V 5 /R 6 /Length 256"
            " /CF << /StdCF << /CFM /AESV3 /AuthEvent /DocOpen /Length 32 >> >>"
            " /StmF /StdCF /StrF /StdCF"
            f" /O <{owner_entry.hex()}> /U <{user_entry.hex()}>"
            f" /OE <{owner_key.hex()}> /UE <{user_key.hex()}>"
            f" /P {permissions} /Perms <{aes_ecb_encrypt(AES_FILE_KEY, perms_block).hex()}> >>"
        ).encode("ascii")
    )
    return build_pdf(objects, extra_trailer=f" /Encrypt 6 0 R /ID [<{DOC_ID.hex()}> <{DOC_ID.hex()}>]")


# --------------------------------------------------------------------------
# The rule that carries every assertion of the integration job: one term, one
# file. It is checked here rather than trusted, because the words below are now
# spread over pixels, over compressed streams and over ZIP members, and no
# reviewer can hold that in their head.
# --------------------------------------------------------------------------

# Text that a grep over the built file cannot find, because it is either pixels
# or a deflated stream. Declared here so the uniqueness check sees it anyway.
RENDERED_TEXT: dict[str, tuple[str, ...]] = {
    "13-ratsvorlage-scan.pdf": tuple(line for page in RATSVORLAGE_PAGES for line in page),
    "14-pacht-mit-anhang.pdf": tuple(line for page in PACHT_SCAN_PAGES for line in page),
    "15-schweiz-baubewilligung.pdf": SCHWEIZ_PAGE,
    "16-oesterreich-mitteilung.pdf": OESTERREICH_PAGE,
    "17-beleg.jpg": BELEG_LINES,
    "18-aushang.png": AUSHANG_LINES,
    "19-uebermittlung.tif": UEBERMITTLUNG_LINES,
    "20-rueckruf.webp": RUECKRUF_LINES,
    "21-sendebericht.tif": tuple(line for page in SENDEBERICHT_PAGES for line in page),
    "23-gedreht.jpg": LIEFERSCHEIN_LINES,
    "30-nur-ein-bild.pdf": ZAHLUNGSERINNERUNG_PAGE,
}

# Term, and the one file it may stand in. Compared case insensitively, so a
# compound counts: "genehmigung" inside Grundstücksverkehrsgenehmigung is what
# the search actually finds.
UNIQUE_TERMS: dict[str, str] = {
    "Genehmigung": "09-bescheid.pdf",
    "Frist": "10-kuendigung.docx",
    "drei Monate": "10-kuendigung.docx",
    "Vertr": "11-uebersicht.odt",
    "Müller": "12-aktenvermerk.txt",
    "Bebauungsplan": "13-ratsvorlage-scan.pdf",
    "Pachtvereinbarung": "14-pacht-mit-anhang.pdf",
    "Strasse": "15-schweiz-baubewilligung.pdf",
    "Baubewilligung": "15-schweiz-baubewilligung.pdf",
    "Jänner": "16-oesterreich-mitteilung.pdf",
    "Grundbuchsauszug": "16-oesterreich-mitteilung.pdf",
    "Zahlungsavis": "17-beleg.jpg",
    "Sperrmüllabfuhr": "18-aushang.png",
    "Übermittlungsprotokoll": "19-uebermittlung.tif",
    "Rückrufbitte": "20-rueckruf.webp",
    "Sendebericht": "21-sendebericht.tif",
    "Lieferschein": "23-gedreht.jpg",
    "Zahlungserinnerung": "30-nur-ein-bild.pdf",
}


def _searchable_text(name: str, payload: bytes) -> str:
    """Everything a search could ever find in one corpus file, pixels included."""
    parts = [" ".join(RENDERED_TEXT.get(name, ()))]
    if payload[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for info in archive.infolist():
                if info.file_size > ARCHIVE_MEMBER_CAP_BYTES:
                    # The one member the extractor refuses to read. Reading it
                    # here would materialise exactly the 64 MiB that the cap
                    # exists to keep out of memory, and a word inside a part
                    # nothing ever opens is not a word a search can find.
                    continue
                parts.append(archive.read(info).decode("utf-8", "ignore"))
    else:
        parts.append(payload.decode("cp1252", "ignore"))
    return " ".join(parts).lower()


def _assert_terms_stand_in_one_file(files: dict[str, bytes]) -> None:
    texts = {name: _searchable_text(name, payload) for name, payload in files.items()}
    for term, owner in UNIQUE_TERMS.items():
        carriers = sorted(name for name, text in texts.items() if term.lower() in text)
        if carriers != [owner]:
            message = f"the term {term!r} belongs to {owner} alone, but it stands in {carriers}"
            raise SystemExit(message)


FILES: dict[str, bytes] = {
    "01-text-layer.pdf": build_text_layer_pdf(),
    "02-scan-no-text-layer.pdf": build_scan_pdf(),
    "03-document.docx": build_docx(),
    "04-notes.txt": build_txt(),
    "05-picture.png": build_png(),
    # Zero bytes on purpose. Every extractor has to survive this one.
    "06-zero-bytes.pdf": b"",
    "07-password-protected.pdf": build_encrypted_pdf(),
    "08-legacy-encoding.txt": build_cp1252_txt(),
    # The four German language cases of phase 2. Flat in the same directory and
    # numbered onwards on purpose: the readonly gate resolves file ids over
    # basename in a flat WebDAV path and would not follow a subdirectory.
    "09-bescheid.pdf": build_german_pdf(),
    "10-kuendigung.docx": build_german_docx(),
    "11-uebersicht.odt": build_odt(),
    "12-aktenvermerk.txt": build_umlaut_name_txt(),
    # The OCR cases of phase 3, flat and numbered onwards for the same reason as
    # the four above: the readonly gate resolves file ids over the basename in a
    # flat WebDAV path and would not follow a subdirectory.
    "13-ratsvorlage-scan.pdf": build_ratsvorlage_scan(),
    "14-pacht-mit-anhang.pdf": build_pacht_with_annex(),
    "15-schweiz-baubewilligung.pdf": build_schweiz_scan(),
    "16-oesterreich-mitteilung.pdf": build_oesterreich_scan(),
    "17-beleg.jpg": build_beleg_jpg(),
    "18-aushang.png": build_aushang_png(),
    "19-uebermittlung.tif": build_uebermittlung_tiff(),
    "20-rueckruf.webp": build_rueckruf_webp(),
    "21-sendebericht.tif": build_sendebericht_tiff(),
    "22-icon.png": build_icon_png(),
    "23-gedreht.jpg": build_gedreht_jpg(),
    # Ten broken PDFs, ten different failure paths. Together with the zero byte
    # file 06 and the encrypted file 07 they are the twelve of gate B.
    "24-abgeschnittener-trailer.pdf": build_truncated_trailer(),
    "25-kaputte-xref.pdf": build_broken_xref(),
    "26-riesige-seitenzahl.pdf": build_huge_page_count(),
    "27-nullbytes-im-kopf.pdf": build_null_bytes_header(),
    "28-ohne-seiten.pdf": build_no_pages(),
    "29-doppelt-komprimiert.pdf": build_double_compressed_stream(),
    "30-nur-ein-bild.pdf": build_image_only_a4(),
    "31-riesenformat.pdf": build_odd_page_size(),
    "32-startxref-ins-leere.pdf": build_startxref_into_nothing(),
    "33-seitenbaum-zyklus.pdf": build_page_tree_cycle(),
    # The edge paths of the launch hardening. Not broken files: files that want
    # something. The first one is the decompression bomb the cap of phase 2 has
    # been holding against a 65 byte fixture until now.
    "34-zip-bombe.docx": build_zip_bomb_docx(),
    # Five PDF structures that describe an action. Not one of them is broken:
    # every one of them is a well formed document, and the question each of them
    # asks is whether anything of the action happens on the way to the verdict.
    "35-startaktion-javascript.pdf": build_open_action_javascript_pdf(),
    "36-eingebettete-datei.pdf": build_embedded_file_pdf(),
    "37-verweis-ins-netz.pdf": build_uri_action_pdf(),
    "38-aes256-verschluesselt.pdf": build_aes_encrypted_pdf(),
    "39-tief-verschachtelt.pdf": build_deeply_nested_pdf(),
}


def _check() -> int:
    """Rebuild every file in memory and compare it with the bytes on disk.

    The reproducibility promise of this script is the load bearing part of the
    corpus, because ``readonly-gate`` compares committed checksums: a builder
    whose output drifts turns that gate from a statement about the read path
    into a statement about the weather. Reading the claim out of the docstring
    is not the same as measuring it, so this mode measures it, and it writes
    nothing at all while doing so. A verification that repairs what it finds
    would be green on the second run of a broken build.
    """
    problems: list[str] = []
    for name, payload in FILES.items():
        target = CORPUS_DIR / name
        if not target.is_file():
            problems.append(f"{name} is missing from {CORPUS_DIR}")
            continue
        on_disk = target.read_bytes()
        if on_disk != payload:
            problems.append(
                f"{name} differs: on disk {len(on_disk)} bytes"
                f" sha256={hashlib.sha256(on_disk).hexdigest()},"
                f" rebuilt {len(payload)} bytes sha256={hashlib.sha256(payload).hexdigest()}"
            )
    # The other direction, and it is not symmetry for its own sake: a file that
    # nothing builds any more is exactly the downloaded sample the corpus rules
    # forbid, and comparing only the built names would never see it.
    for target in sorted(CORPUS_DIR.iterdir()):
        if target.is_file() and target.name not in FILES:
            problems.append(f"{target.name} lies in the corpus and comes out of no builder")

    for problem in problems:
        print(f"check failed: {problem}")
    if problems:
        return 1

    total = sum(len(payload) for payload in FILES.values())
    print(f"check ok: {len(FILES)} files, {total} bytes, every one of them byte identical with a fresh build")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    # Both checks run before the first byte is written. A corpus with a
    # replacement box in it, or with a search term in two files, is worse than
    # no corpus: it turns green assertions into statements about nothing.
    _assert_every_glyph_exists(GLYPH_PROBE)
    _assert_aes_matches_the_standard()
    _assert_terms_stand_in_one_file(FILES)

    if "--check" in list(sys.argv[1:] if argv is None else argv):
        return _check()

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    for name, payload in FILES.items():
        target = CORPUS_DIR / name
        target.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        print(f"{name} bytes={len(payload)} sha256={digest}")
    print(f"files={len(FILES)} total bytes={sum(len(payload) for payload in FILES.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
