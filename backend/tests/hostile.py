"""Generators of the hostile format corpus, shared by the audit modules (D-36-01, D-36-02).

Not a test module: the name carries no ``test_`` prefix, so pytest never
collects it, and the test modules import it like ``conftest`` (``from hostile
import build_zip``). There is one copy of every generator, here.

**No hostile file lives in the repository.** Every file of the corpus is built
at test time, in memory, by a function of this module, and written only into
the temporary directory of the test that runs it. Each function returns bytes,
takes its sizes as parameters with defaults, and is deterministic: no clock, no
``random``, no ``os.urandom``. Where a generator needs bytes that look random,
they come from a linear congruential sequence with a fixed seed.

**Bombs declare their size and do not carry it.** A ZIP member claims a
gigantic uncompressed size in its records, a PNG claims twenty thousand rows
in its header, a package claims a million directory records without a single
byte of payload behind them. The readers have to judge the declaration; the
corpus stays a few megabytes at most, and every case runs in seconds.

The sandbox helpers at the top (run_timed and its kin) read the monotonic clock
as a stopwatch of the run; no generator does.

Only ASCII in this file; umlauts would be escapes (the convention of the audit
modules).
"""

from __future__ import annotations

import io
import struct
import time
import zlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from findling.config import ARCHIVE_MAX_RATIO, ARCHIVE_RATIO_MIN_BYTES, MAX_FILE_BYTES
from findling.extract import sandbox
from findling.extract.errors import STATE_REASONS, ExtractionOutcome, Reason

# The owner's number for an extreme compression ratio (36-WORTLAUT.md, answer
# O12 (a), accepted 2026-10-20): above it a member is blocked as malicious
# (zip_ratio), between ARCHIVE_MAX_RATIO and it a member stays archive_limit.
# config.ARCHIVE_MALICIOUS_RATIO only arrives with plan 36-08, which proves by a
# test that both carry the same number.
ATTACK_RATIO: Final = 1000

# The deadline of the corpus worker and the time one case may take. Half the
# product deadline (120 s) for the worker, so that a hang costs one minute and
# not two; a quarter of it for a case, so that a reader that is merely slow on
# this machine shows up as well.
CORPUS_DEADLINE_SECONDS: Final = 60.0
CASE_SECONDS: Final = 30.0


# -- the sandbox ------------------------------------------------------------------


@dataclass(frozen=True)
class Ran:
    outcome: ExtractionOutcome
    seconds: float


def run_timed(worker: sandbox.ExtractionWorker, path: Path, mime: str) -> Ran:
    started = time.monotonic()
    outcome = worker.run(str(path), mime, path.stat().st_size)
    return Ran(outcome, time.monotonic() - started)


def named_and_quick(ran: Ran, worker: sandbox.ExtractionWorker) -> None:
    """The three promises of every case: a verdict with a name, a living worker, a short run."""
    assert ran.outcome.reason in STATE_REASONS[ran.outcome.state]
    assert ran.outcome.reason is not Reason.TIMEOUT
    assert ran.seconds < CASE_SECONDS
    # The next job is answered: by the same child, or by a fresh one after a recycle.
    assert worker.run(__file__, "application/x-not-allowed", 10).reason is Reason.MIME_NOT_ALLOWED


def corpus_case(
    worker: sandbox.ExtractionWorker, tmp_path: Path, name: str, data: bytes, mime: str
) -> tuple[Ran, list[str]]:
    """Write one case into its own directory, run it in the sandbox, and list what is left there."""
    path = tmp_path / name
    path.write_bytes(data)
    ran = run_timed(worker, path, mime)
    named_and_quick(ran, worker)
    return ran, sorted(entry.name for entry in tmp_path.iterdir())


# -- deterministic filler -------------------------------------------------------------


def lcg_bytes(count: int, seed: int = 36_07) -> bytes:
    """``count`` bytes of a linear congruential sequence (glibc constants), none of them zero."""
    out = bytearray(count)
    state = seed
    for index in range(count):
        state = (state * 1_103_515_245 + 12_345) & 0x7FFFFFFF
        out[index] = ((state >> 16) & 0xFF) | 0x01
    return bytes(out)


# -- ZIP files, written record by record (APPNOTE 4.3.7, 4.3.12, 4.3.16) ------------


@dataclass(frozen=True)
class Member:
    name: bytes
    data: bytes
    deflate: bool = False
    declared: int | None = None  # the uncompressed size the records claim, when not the true one
    offset: int | None = None  # the local header offset the directory claims, when not the true one


def _local(member: Member, payload: bytes, crc: int, declared: int) -> bytes:
    method = 8 if member.deflate else 0
    head = struct.pack(
        "<4sHHHHHIIIHH", b"PK\x03\x04", 20, 0, method, 0, 0x21, crc, len(payload), declared, len(member.name), 0
    )
    return head + member.name + payload


def _central(member: Member, payload: bytes, crc: int, declared: int, offset: int) -> bytes:
    method = 8 if member.deflate else 0
    fields = (b"PK\x01\x02", 0x031E, 20, 0, method, 0, 0x21, crc, len(payload), declared, len(member.name))
    return struct.pack("<4sHHHHHHIIIHHHHHII", *fields, 0, 0, 0, 0, 0o100644 << 16, offset) + member.name


def _end(count: int, size: int, offset: int, comment: bytes = b"") -> bytes:
    return struct.pack("<4sHHHHIIH", b"PK\x05\x06", 0, 0, count, count, size, offset, len(comment)) + comment


def _deflated(data: bytes) -> bytes:
    packer = zlib.compressobj(9, zlib.DEFLATED, -15)
    return packer.compress(data) + packer.flush()


def build_zip(members: Sequence[Member], *, comment: bytes = b"") -> bytes:
    body = b""
    directory = b""
    for member in members:
        payload = _deflated(member.data) if member.deflate else member.data
        crc = zlib.crc32(member.data)
        declared = len(member.data) if member.declared is None else member.declared
        at = len(body)
        body += _local(member, payload, crc, declared)
        directory += _central(member, payload, crc, declared, at if member.offset is None else member.offset)
    return body + directory + _end(len(members), len(directory), len(body), comment)


def _same_offset_twice(name: bytes, data: bytes) -> bytes:
    """Two directory entries for one local header: the overlap zipfile only warns about."""
    crc = zlib.crc32(data)
    body = _local(Member(name, data), data, crc, len(data))
    directory = _central(Member(name, data), data, crc, len(data), 0) * 2
    return body + directory + _end(2, len(directory), len(body))


def _with_end(plain: bytes, size: int, offset: int) -> bytes:
    return plain[:-22] + struct.pack("<4sHHHHIIH", b"PK\x05\x06", 0, 0, 1, 1, size, offset, 0)


def text_member(word: str) -> Member:
    return Member(f"{word}.txt".encode(), f"{word} steht hier".encode())


def zip_overlap(name: bytes = b"a.txt", word: bytes = b"ueberlappwort") -> bytes:
    """Two members, the data of the first quotes the local header of the second (Fifield 2019).

    zipfile refuses to read the first one with "Overlapped entries"
    (CVE-2024-0450); no packer writes such a file, it is the shape of the
    overlap bomb.
    """
    inner = word + b" steht hier"
    second = _local(Member(b"b.txt", inner), inner, zlib.crc32(inner), len(inner))
    return build_zip([Member(name, second), Member(b"b.txt", inner, offset=30 + len(name))])


def zip_traversal(name: bytes, word: bytes = b"fluchtwort") -> bytes:
    """A member under a name that climbs out (``..``, absolute, drive letter or NUL), next to a plain one."""
    return build_zip([Member(name, word + b" steht hier"), text_member("aussenwort")])


def zip_oversized_member(declared: int = 60 * 1024 * 1024, name: bytes = b"riesig.txt") -> bytes:
    """A member that declares more than max_file_bytes, under the ratio and under the sum of the archive.

    Stored, with just enough deterministic payload that the declared size over
    the stored size stays under ARCHIVE_MAX_RATIO: the reader passes it over and
    keeps its name, it is no bomb. A plain member next to it carries text.
    """
    payload = lcg_bytes(-(-declared // ARCHIVE_MAX_RATIO) + 4096)
    assert declared > MAX_FILE_BYTES
    assert declared / len(payload) <= ARCHIVE_MAX_RATIO
    return build_zip([Member(name, payload, declared=declared), text_member("kleinwort")])


def deflate_ratio(data: bytes) -> float:
    """The ratio archive.py judges: uncompressed size over the size of the deflate payload."""
    return len(data) / max(len(_deflated(data)), 1)


def zip_ratio_member(size: int = 2 * 1024 * 1024) -> bytes:
    """A member of zero bytes over ARCHIVE_RATIO_MIN_BYTES whose ratio is above ATTACK_RATIO.

    Deflate ends at about 1032 to 1 by its format (258 bytes per match); 2 MiB
    of zeros measured 1023.5 to 1 on 2026-10-20, so deflate is enough for the
    owner's 1000 and no bzip2 or LZMA member is needed. The ratio is measured
    here and not believed.
    """
    data = bytes(size)
    assert size >= ARCHIVE_RATIO_MIN_BYTES
    assert deflate_ratio(data) > ATTACK_RATIO
    return build_zip([text_member("vornwort"), Member(b"nullen.bin", data, deflate=True)])


def _sparse(size: int, spacing: int) -> bytes:
    """Zero bytes with one byte of the fixed sequence every ``spacing`` bytes."""
    data = bytearray(size)
    marks = lcg_bytes(-(-size // spacing))
    data[::spacing] = marks[: len(range(0, size, spacing))]
    return bytes(data)


def zip_moderate_ratio_member(target: int = 150, size: int = ARCHIVE_RATIO_MIN_BYTES + 4096) -> bytes:
    """A densely packed member that is no bomb: measured ratio near ``target``, between the two numbers.

    Zeros with bytes of a fixed seed spread in at a spacing found by bisection;
    the deflate ratio grows with the spacing. The generator checks the measured
    ratio itself: above ARCHIVE_MAX_RATIO (so the member is judged at all) and
    at most ATTACK_RATIO (so it stays archive_limit, D-36-17, answer O12).
    """
    low, high = 2, 1 << 16
    while high - low > 1:
        middle = (low + high) // 2
        if deflate_ratio(_sparse(size, middle)) < target:
            low = middle
        else:
            high = middle
    data = _sparse(size, high)
    ratio = deflate_ratio(data)
    assert size >= ARCHIVE_RATIO_MIN_BYTES
    assert ARCHIVE_MAX_RATIO < ratio <= ATTACK_RATIO, ratio
    return build_zip([text_member("vornwort"), Member(b"dicht.bin", data, deflate=True)])


def zip_depth_three(word: str = "tiefwort") -> bytes:
    """Three levels of honest ZIP files, no zero filler: archive_limit by depth alone."""
    return build_zip([Member(b"e2.zip", build_zip([Member(b"e3.zip", build_zip([text_member(word)]))]))])


def zip_entries(count: int = 10_001) -> bytes:
    return build_zip([Member(f"x{index}.txt".encode(), b"") for index in range(count)])


def package_with_entries(suffix: str, count: int = 1_000_000) -> bytes:
    """An Office or OpenDocument package of nothing but central directory records and the end record.

    The first record carries the name the loader of ``suffix`` looks for, the
    others a one byte name, so a million records stay under max_file_bytes and
    the case tests the count and not the size cap. No local header and no byte
    of payload: the directory is the whole attack (ZipFile builds one ZipInfo
    per record before anything can count them).
    """
    first = {"docx": b"[Content_Types].xml", "xlsx": b"[Content_Types].xml", "odt": b"content.xml"}[suffix]

    def record(name: bytes) -> bytes:
        fields = (b"PK\x01\x02", 0x031E, 20, 0, 0, 0, 0x21, 0, 0, 0, len(name))
        return struct.pack("<4sHHHHHHIIIHHHHHII", *fields, 0, 0, 0, 0, 0o100644 << 16, 0) + name

    directory = record(first) + record(b"x") * (count - 1)
    shown = min(count, 0xFFFF)
    end = struct.pack("<4sHHHHIIH", b"PK\x05\x06", 0, 0, shown, shown, len(directory), 0, 0)
    data = directory + end
    assert len(data) <= MAX_FILE_BYTES
    return data


# -- XML bombs and the packages that carry them ----------------------------------------

# Each template marks the one place a text goes with @TEXT@. No XML declaration:
# the generators put theirs, and the document type, in front.
_TEXT: Final = b"@TEXT@"

PLAIN_XML: Final = b"<r>@TEXT@</r>"

ODT_CONTENT: Final = (
    b'<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
    b' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2">'
    b"<office:body><office:text><text:p>@TEXT@</text:p></office:text></office:body></office:document-content>"
)

_W: Final = b"http://schemas.openxmlformats.org/wordprocessingml/2006/main"
DOCX_DOCUMENT: Final = (
    b'<w:document xmlns:w="' + _W + b'"><w:body><w:p><w:r><w:t>@TEXT@</w:t></w:r></w:p></w:body></w:document>'
)

PPTX_SLIDE: Final = (
    b'<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
    b' xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
    b' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    b'<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
    b'<p:grpSpPr/><p:sp><p:nvSpPr><p:cNvPr id="2" name="t"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr/>'
    b"<p:txBody><a:bodyPr/><a:p><a:r><a:t>@TEXT@</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>"
)

_S: Final = b"http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX_SHEET: Final = (
    b'<worksheet xmlns="' + _S + b'"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>@TEXT@</t></is></c>'
    b"</row></sheetData></worksheet>"
)


def xml_text(text: bytes, template: bytes = PLAIN_XML) -> bytes:
    """An honest document of the template's vocabulary with ``text`` at its one place."""
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + template.replace(_TEXT, text)


def _with_entities(subset: bytes, body: bytes, template: bytes) -> bytes:
    return b'<?xml version="1.0"?>\n<!DOCTYPE r [' + subset + b"]>\n" + template.replace(_TEXT, body)


def billion_laughs_xml(levels: int = 10, fanout: int = 10, *, template: bytes = PLAIN_XML) -> bytes:
    """Billion Laughs: each entity holds ``fanout`` references to the one below, ``levels`` deep.

    The file is a few hundred bytes; expanded it would be fanout ** (levels - 1)
    copies of the innermost word.
    """
    subset = b'<!ENTITY e0 "entitygeheim">' + b"".join(
        b'<!ENTITY e%d "%s">' % (level, (b"&e%d;" % (level - 1)) * fanout) for level in range(1, levels)
    )
    return _with_entities(subset, b"&e%d;" % (levels - 1), template)


def quadratic_blowup_xml(entity_bytes: int = 20_000, repeats: int = 20_000, *, template: bytes = PLAIN_XML) -> bytes:
    """One flat entity of ``entity_bytes`` referenced ``repeats`` times: no nesting, the same amplification."""
    subset = b'<!ENTITY a "' + b"a" * entity_bytes + b'">'
    return _with_entities(subset, b"&a;" * repeats, template)


def deep_nesting_xml(depth: int = 10_000, *, template: bytes = PLAIN_XML) -> bytes:
    """``depth`` nested elements around one word at the template's text place."""
    return xml_text(b"<d>" * depth + b"tiefwort" + b"</d>" * depth, template)


def _content_types(overrides: Sequence[tuple[bytes, bytes]]) -> bytes:
    return (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        b'<Default Extension="xml" ContentType="application/xml"/>'
        + b"".join(b'<Override PartName="%s" ContentType="%s"/>' % pair for pair in overrides)
        + b"</Types>"
    )


def _relationships(targets: Sequence[tuple[bytes, bytes]]) -> bytes:
    return (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + b"".join(
            b'<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/%s" Target="%s"/>'
            % (index, kind, target)
            for index, (kind, target) in enumerate(targets, 1)
        )
        + b"</Relationships>"
    )


_OFFICE_DOCUMENT: Final = b"officeDocument/2006/relationships/officeDocument"


def odt_with(content_xml: bytes | None = None) -> bytes:
    """A minimal OpenDocument text: mimetype first and stored, content.xml, manifest."""
    content = xml_text(b"odtwort", ODT_CONTENT) if content_xml is None else content_xml
    manifest = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
        b'<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>'
        b'<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
        b"</manifest:manifest>"
    )
    return build_zip(
        [
            Member(b"mimetype", b"application/vnd.oasis.opendocument.text"),
            Member(b"content.xml", content, deflate=True),
            Member(b"META-INF/manifest.xml", manifest, deflate=True),
        ]
    )


def docx_with(document_xml: bytes | None = None) -> bytes:
    """A minimal Word package: content types, the package relationship, the main document."""
    document = xml_text(b"docxwort", DOCX_DOCUMENT) if document_xml is None else document_xml
    main = b"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
    return build_zip(
        [
            Member(b"[Content_Types].xml", _content_types([(b"/word/document.xml", main)]), deflate=True),
            Member(b"_rels/.rels", _relationships([(_OFFICE_DOCUMENT, b"word/document.xml")]), deflate=True),
            Member(b"word/document.xml", document, deflate=True),
        ]
    )


def pptx_with(slide_xml: bytes | None = None) -> bytes:
    """A minimal PowerPoint package: the presentation part and one slide, no master and no layout."""
    slide = xml_text(b"pptxwort", PPTX_SLIDE) if slide_xml is None else slide_xml
    ml = b"application/vnd.openxmlformats-officedocument.presentationml."
    presentation = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        b'<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
        b' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        b'<p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst>'
        b'<p:sldSz cx="9144000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>'
    )
    types = _content_types(
        [(b"/ppt/presentation.xml", ml + b"presentation.main+xml"), (b"/ppt/slides/slide1.xml", ml + b"slide+xml")]
    )
    return build_zip(
        [
            Member(b"[Content_Types].xml", types, deflate=True),
            Member(b"_rels/.rels", _relationships([(_OFFICE_DOCUMENT, b"ppt/presentation.xml")]), deflate=True),
            Member(b"ppt/presentation.xml", presentation, deflate=True),
            Member(
                b"ppt/_rels/presentation.xml.rels",
                _relationships([(b"officeDocument/2006/relationships/slide", b"slides/slide1.xml")]),
                deflate=True,
            ),
            Member(b"ppt/slides/slide1.xml", slide, deflate=True),
        ]
    )


def xlsx_with(sheet_xml: bytes | None = None) -> bytes:
    """A minimal Excel package: workbook, one sheet of inline strings, no styles and no shared strings."""
    sheet = xml_text(b"xlsxwort", XLSX_SHEET) if sheet_xml is None else sheet_xml
    ml = b"application/vnd.openxmlformats-officedocument.spreadsheetml."
    workbook = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        b'<workbook xmlns="' + _S + b'" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        b'<sheets><sheet name="blatt" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    types = _content_types(
        [(b"/xl/workbook.xml", ml + b"sheet.main+xml"), (b"/xl/worksheets/sheet1.xml", ml + b"worksheet+xml")]
    )
    return build_zip(
        [
            Member(b"[Content_Types].xml", types, deflate=True),
            Member(b"_rels/.rels", _relationships([(_OFFICE_DOCUMENT, b"xl/workbook.xml")]), deflate=True),
            Member(b"xl/workbook.xml", workbook, deflate=True),
            Member(
                b"xl/_rels/workbook.xml.rels",
                _relationships([(b"officeDocument/2006/relationships/worksheet", b"worksheets/sheet1.xml")]),
                deflate=True,
            ),
            Member(b"xl/worksheets/sheet1.xml", sheet, deflate=True),
        ]
    )


# -- pictures: PNG, TIFF and a JPEG header ----------------------------------------------


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def _png(width: int, height: int, idat: bytes, extra: bytes = b"") -> bytes:
    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)  # 8 bit grey, no interlace
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + extra
        + _png_chunk(b"IDAT", idat)
        + _png_chunk(b"IEND", b"")
    )


def png_bomb(width: int = 20_000, height: int = 20_000) -> bytes:
    """A PNG that declares ``width`` x ``height`` grey pixels and carries the deflate zeros of 16 rows.

    Pillow refuses it from the header alone (over twice MAX_IMAGE_PIXELS); the
    rows behind the first 16 are declared, never carried, so a few hundred bytes
    stand for 400 megapixels.
    """
    rows = zlib.compress(bytes((1 + width) * min(height, 16)), 9)
    return _png(width, height, rows)


def png_text_bomb(uncompressed: int = 2 * 1024 * 1024) -> bytes:
    """An ordinary 640 x 200 PNG with a zTXt chunk that inflates to ``uncompressed`` bytes."""
    width, height = 640, 200
    text = b"bildgeheim\x00\x00" + zlib.compress(bytes(uncompressed), 9)
    return _png(width, height, zlib.compress(bytes((1 + width) * height), 9), _png_chunk(b"zTXt", text))


# A strip of 640 x 80 grey pixels: an OCR-able long edge (640) at the largest
# aspect ratio image.py lets through (8), the smallest picture that reaches the
# frame walk instead of an early refusal.
_TIFF_WIDTH: Final = 640
_TIFF_HEIGHT: Final = 80


def _tiff_ifd(strip_at: int, next_at: int) -> bytes:
    """One IFD of eight tags, all pointing at the one shared strip."""
    tags = (
        (256, 3, 1, _TIFF_WIDTH),  # ImageWidth
        (257, 3, 1, _TIFF_HEIGHT),  # ImageLength
        (258, 3, 1, 8),  # BitsPerSample
        (259, 3, 1, 1),  # Compression: none
        (262, 3, 1, 1),  # PhotometricInterpretation: black is zero
        (273, 4, 1, strip_at),  # StripOffsets
        (278, 3, 1, _TIFF_HEIGHT),  # RowsPerStrip
        (279, 4, 1, _TIFF_WIDTH * _TIFF_HEIGHT),  # StripByteCounts
    )
    entries = b"".join(
        struct.pack("<HHIHH", tag, kind, count, value, 0)
        if kind == 3
        else struct.pack("<HHII", tag, kind, count, value)
        for tag, kind, count, value in tags
    )
    return struct.pack("<H", len(tags)) + entries + struct.pack("<I", next_at)


_IFD_SIZE: Final = 2 + 8 * 12 + 4


def tiff_many_ifds(count: int = 100_000) -> bytes:
    """A chain of ``count`` IFDs, each a page of the same 51 KB strip: a fax archive gone wild."""
    strip_at = 8
    first = strip_at + _TIFF_WIDTH * _TIFF_HEIGHT
    ifds = b"".join(
        _tiff_ifd(strip_at, first + (index + 1) * _IFD_SIZE if index + 1 < count else 0) for index in range(count)
    )
    return b"II*\x00" + struct.pack("<I", first) + bytes(_TIFF_WIDTH * _TIFF_HEIGHT) + ifds


def tiff_ifd_cycle() -> bytes:
    """Two IFDs, the second points back at the first: the next-IFD chain never ends."""
    strip_at = 8
    first = strip_at + _TIFF_WIDTH * _TIFF_HEIGHT
    second = first + _IFD_SIZE
    return (
        b"II*\x00"
        + struct.pack("<I", first)
        + bytes(_TIFF_WIDTH * _TIFF_HEIGHT)
        + _tiff_ifd(strip_at, second)
        + _tiff_ifd(strip_at, first)
    )


def honest_large_jpeg(width: int = 12_000, height: int = 8_600, padding: int = 2 * 1024 * 1024) -> bytes:
    """The header of a real 103 megapixel grey JPEG and ``padding`` bytes of scan data behind it.

    The positive control of too_large: over twice MAX_IMAGE_PIXELS, so Pillow
    refuses it at the header, but with far fewer than 1000 pixels per byte of
    file, the density of a real medium format picture and not of a bomb. The
    scan data is the fixed sequence with every 0xFF dropped, so no marker
    appears inside it.
    """
    sof = struct.pack(">BHHB", 8, height, width, 1) + b"\x01\x11\x00"
    sos = struct.pack(">B", 1) + b"\x01\x00" + b"\x00\x3f\x00"
    scan = lcg_bytes(padding).replace(b"\xff", b"\x7f")
    jpeg = (
        b"\xff\xd8"
        b"\xff\xc0"
        + struct.pack(">H", 2 + len(sof))
        + sof
        + b"\xff\xda"
        + struct.pack(">H", 2 + len(sos))
        + sos
        + scan
        + b"\xff\xd9"
    )
    assert width * height < 1000 * len(jpeg)
    return jpeg


# -- polyglots ---------------------------------------------------------------------------


def pdf_with_text(text: bytes = b"pdfwort steht auf dieser einen seite") -> bytes:
    """A one page PDF 1.4 with ``text`` in Helvetica, offsets of the cross reference table computed.

    The default text is longer than the 25 characters pdf.py asks of a page
    with a text layer, so the page is read and not taken for a scan.
    """
    stream = b"BT /F1 24 Tf 72 720 Td (" + text + b") Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return out


def pdf_zip_polyglot() -> bytes:
    """A PDF with a ZIP file appended: a PDF to pdfium, a ZIP file to zipfile (offsets shifted by the PDF)."""
    return pdf_with_text(b"pdfteilwort steht auf dieser einen seite") + build_zip([text_member("zipteilwort")])


def jpeg_zip_polyglot() -> bytes:
    """A 640 x 200 JPEG from Pillow's encoder with a ZIP file appended behind its end marker."""
    from PIL import Image

    picture = io.BytesIO()
    Image.new("L", (640, 200), 255).save(picture, format="JPEG", quality=75)
    return picture.getvalue() + build_zip([text_member("zipteilwort")])


# -- mails, as raw bytes ------------------------------------------------------------

_HEAD = b"From: a@b.de\r\nTo: c@d.de\r\nSubject: hallo\r\n"


def nested_rfc822(levels: int) -> bytes:
    """A mail inside a mail, ``levels`` times, each wrapper a message/rfc822 part."""
    mail = _HEAD + b"Content-Type: text/plain\r\n\r\nkern\r\n"
    for _ in range(levels):
        mail = b"Subject: s\r\nContent-Type: message/rfc822\r\n\r\n" + mail
    return mail


# -- compound files, written sector by sector ([MS-CFB] 2.2, 2.3, 2.6) -----------------

_SECTOR = 512
_MINI = 64
_END_OF_CHAIN = 0xFFFFFFFE
_FREE = 0xFFFFFFFF
_FAT_SECTOR = 0xFFFFFFFD
_NO_STREAM = 0xFFFFFFFF


@dataclass
class Layout:
    """What a compound file is made of, editable before it is written."""

    fat: list[int]
    minifat: list[int]
    entries: list[list[Any]]  # name, type, left, right, child, start, size
    header: dict[str, Any]
    tail: bytes = b""


def _entry(name: str, kind: int, left: int, right: int, child: int, start: int, size: int) -> bytes:
    raw = name.encode("utf-16-le") + b"\0\0" if name else b""
    return (
        raw.ljust(64, b"\0")
        + struct.pack("<HBB3I", len(raw), kind, 1, left, right, child)
        + b"\0" * 36
        + struct.pack("<IQ", start, size)
    )


def _chain(table: list[int], start: int, count: int) -> None:
    for index in range(count):
        table[start + index] = start + index + 1 if index < count - 1 else _END_OF_CHAIN


def build_cfb_sectors(streams: dict[str, bytes], edit: Callable[[Layout], None] | None = None) -> bytes:
    """Version 3, 512 byte sectors. Streams under 4096 bytes go into the mini stream, as the specification wants.

    Not conftest.build_cfb: this writer lays out FAT, MiniFAT and directory
    itself and hands the Layout to ``edit`` before writing, which is how the
    cycle cases below are made.
    """
    names = list(streams)
    small = [name for name in names if 0 < len(streams[name]) < 4096]
    minifat: list[int] = []
    container = b""
    mini_start: dict[str, int] = {}
    for name in small:
        data = streams[name]
        count = -(-len(data) // _MINI)
        mini_start[name] = len(minifat)
        minifat += [_FREE] * count
        _chain(minifat, mini_start[name], count)
        container += data.ljust(count * _MINI, b"\0")
    minifat_sectors = -(-len(minifat) * 4 // _SECTOR)
    container_sectors = -(-len(container) // _SECTOR)
    big = [name for name in names if len(streams[name]) >= 4096]
    big_sectors = sum(-(-len(streams[name]) // _SECTOR) for name in big)
    dir_sectors = -(-(1 + len(names)) * 128 // _SECTOR)
    fat_sectors = 1
    while fat_sectors * 128 < fat_sectors + dir_sectors + minifat_sectors + container_sectors + big_sectors:
        fat_sectors += 1
    fat = [_FREE] * (fat_sectors * 128)
    for index in range(fat_sectors):
        fat[index] = _FAT_SECTOR
    at = fat_sectors
    _chain(fat, at, dir_sectors)
    dir_start, at = at, at + dir_sectors
    _chain(fat, at, minifat_sectors)
    minifat_start, at = (at if minifat_sectors else _END_OF_CHAIN), at + minifat_sectors
    _chain(fat, at, container_sectors)
    container_start, at = (at if container_sectors else _END_OF_CHAIN), at + container_sectors
    body = b""
    starts: dict[str, int] = {}
    for name in big:
        count = -(-len(streams[name]) // _SECTOR)
        _chain(fat, at, count)
        starts[name] = at
        body += streams[name].ljust(count * _SECTOR, b"\0")
        at += count
    entries: list[list[Any]] = [["Root Entry", 5, _NO_STREAM, _NO_STREAM, 1 if names else _NO_STREAM]]
    entries[0] += [container_start, len(container)]
    for index, name in enumerate(names):
        start = mini_start.get(name, starts.get(name, _END_OF_CHAIN))
        right = index + 2 if index + 1 < len(names) else _NO_STREAM
        entries.append([name, 2, _NO_STREAM, right, _NO_STREAM, start, len(streams[name])])
    layout = Layout(
        fat,
        minifat,
        entries,
        {
            "fat_sectors": fat_sectors,
            "dir_start": dir_start,
            "minifat_start": minifat_start,
            "minifat_sectors": minifat_sectors,
            "difat_start": _END_OF_CHAIN,
            "difat_sectors": 0,
            "next_sector": at,
        },
    )
    if edit is not None:
        edit(layout)
    header = layout.header
    difat = ([*range(fat_sectors)] + [_FREE] * 109)[:109]
    head = (
        bytes.fromhex("d0cf11e0a1b11ae1")
        + b"\0" * 16
        + struct.pack("<5H", 0x3E, 3, 0xFFFE, 9, 6)
        + b"\0" * 6
        + struct.pack("<4I", 0, header["fat_sectors"], header["dir_start"], 0)
        + struct.pack("<4I", 4096, header["minifat_start"], header["minifat_sectors"], header["difat_start"])
        + struct.pack("<I", header["difat_sectors"])
        + struct.pack("<109I", *difat)
    )
    directory = b"".join(_entry(*entry) for entry in layout.entries).ljust(dir_sectors * _SECTOR, b"\0")
    minifat_bytes = struct.pack(f"<{len(layout.minifat)}I", *layout.minifat).ljust(minifat_sectors * _SECTOR, b"\xff")
    return (
        head
        + struct.pack(f"<{len(layout.fat)}I", *layout.fat)
        + directory
        + minifat_bytes
        + container.ljust(container_sectors * _SECTOR, b"\0")
        + body
        + layout.tail
    )


# Word: a FibBase with the counts every Word from 97 on writes ([MS-DOC] 2.5.1),
# the Clx at the front of the table stream, one compressed piece at 0x800.
_TEXT_AT = 0x800
_COMPRESSED = 0x40000000


def _word_stream(n_fib: int, lcb_clx: int, text: bytes, at: int = _TEXT_AT) -> bytes:
    word = bytearray(0x1000)
    struct.pack_into("<HH", word, 0, 0xA5EC, n_fib)
    struct.pack_into("<H", word, 0x0A, 0x0200)  # fWhichTblStm: 1Table
    struct.pack_into("<H", word, 0x20, 0x000E)
    struct.pack_into("<H", word, 0x3E, 0x0016)
    struct.pack_into("<H", word, 0x98, 0x005D)
    struct.pack_into("<II", word, 0x01A2, 0, lcb_clx)
    word[at : at + len(text)] = text
    return bytes(word)


def _clx(pieces: Sequence[int], cps: Sequence[int]) -> bytes:
    plc = struct.pack(f"<{len(cps)}I", *cps) + b"".join(struct.pack("<HIH", 0, fc, 0) for fc in pieces)
    return b"\x02" + struct.pack("<I", len(plc)) + plc


def build_doc(
    text: bytes = b"olegeheim im text\r",
    *,
    n_fib: int = 0x00C1,
    pieces: Sequence[int] | None = None,
    cps: Sequence[int] | None = None,
    lcb_clx: int | None = None,
    at: int = _TEXT_AT,
    edit: Callable[[Layout], None] | None = None,
) -> bytes:
    table = _clx([(at * 2) | _COMPRESSED] if pieces is None else pieces, [0, len(text)] if cps is None else cps)
    word = _word_stream(n_fib, len(table) if lcb_clx is None else lcb_clx, text, at)
    return build_cfb_sectors({"WordDocument": word, "1Table": table}, edit)


def _difat_cycle(layout: Layout) -> None:
    sector = layout.header["next_sector"]
    layout.header["difat_start"] = sector
    layout.header["difat_sectors"] = 1
    layout.tail = struct.pack("<128I", *([_FREE] * 127), sector)


def _minifat_cycle(layout: Layout) -> None:
    last = max(index for index, link in enumerate(layout.minifat) if link == _END_OF_CHAIN)
    layout.minifat[last] = 0


def _directory_cycle(layout: Layout) -> None:
    layout.entries[1][3] = 1


def _fat_cycle(layout: Layout) -> None:
    start = layout.entries[1][5]
    layout.fat[start + 3] = start


def _fat_declared_far_past_the_file(layout: Layout) -> None:
    layout.header["fat_sectors"] = 20_000


# Excel: BIFF8 records ([MS-XLS] 2.4), one sheet of LABELSST cells.


def _record(opcode: int, data: bytes = b"") -> bytes:
    return struct.pack("<HH", opcode, len(data)) + data


def _bof(kind: int, version: int) -> bytes:
    return _record(0x0809, struct.pack("<HHHHII", version, kind, 0x0DBB, 0x07CC, 0, 0x0006))


def _short_string(text: str) -> bytes:
    raw = text.encode("latin-1")
    return struct.pack("<HB", len(raw), 0) + raw


def _sst(strings: Sequence[str], unique: int | None) -> bytes:
    """SST and CONTINUE records, split between strings, each at most 8224 bytes."""
    records = [struct.pack("<II", len(strings), len(strings) if unique is None else unique)]
    for text in strings:
        piece = _short_string(text)
        if len(records[-1]) + len(piece) > 8224:
            records.append(b"")
        records[-1] += piece
    return _record(0x00FC, records[0]) + b"".join(_record(0x003C, more) for more in records[1:])


def build_workbook(
    cells: Sequence[tuple[int, int, int]],
    strings: Sequence[str],
    *,
    unique: int | None = None,
    after_bof: bytes = b"",
    version: int = 0x0600,
    edit: Callable[[Layout], None] | None = None,
) -> bytes:
    """Globals (BOF, BOUNDSHEET, SST, EOF) and one sheet of LABELSST cells, in a compound file."""
    sheet_name = struct.pack("<BB", len("blattgeheim"), 0) + b"blattgeheim"
    sst = _sst(strings, unique)
    head = _bof(0x0005, version) + after_bof
    sheet_at = len(head) + 4 + 6 + len(sheet_name) + len(sst) + 4
    head += _record(0x0085, struct.pack("<IBB", sheet_at, 0, 0) + sheet_name) + sst + _record(0x000A)
    sheet = _bof(0x0010, version)
    sheet += b"".join(_record(0x00FD, struct.pack("<HHHI", row, col, 0, index)) for row, col, index in cells)
    return build_cfb_sectors({"Workbook": head + sheet + _record(0x000A)}, edit)
