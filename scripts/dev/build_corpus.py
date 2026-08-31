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
"""

from __future__ import annotations

import hashlib
import io
import struct
import zipfile
import zlib
from pathlib import Path

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
}


def main() -> int:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    for name, payload in FILES.items():
        target = CORPUS_DIR / name
        target.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        print(f"{name} bytes={len(payload)} sha256={digest}")
    print(f"total bytes={sum(len(payload) for payload in FILES.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
