#!/usr/bin/env python3
"""Write the synthetic load corpus of phase 5: 50.000 files, about 20 GB.

The reference corpus under testdata/corpus is 33 files that a reviewer can read.
This is its opposite: a set nobody will ever look at, whose only job is to keep a
4 GB ARM box busy for the better part of a day while the resident memory of the
indexer is measured. Both are generated, and for the same reason, but the scale
changes the design in one decisive place.

scripts/dev/build_corpus.py builds a dict of finished payloads and writes it at
the end. At 33 files of a few kilobytes that is the clearest possible shape. At
50.000 files and 20 GB it is impossible, so this script streams: one file at a
time, written to a temporary neighbour, hashed while it is written, renamed when
it is complete. Nothing is collected but the running checksum, and an abort
therefore leaves no half written file that looks finished.

Everything else is inherited from build_corpus.py rather than invented: the
typeface pinned by SHA-256 and the glyph assert that runs before the first byte,
the fixed timestamp in every ZIP entry, the cross reference table builder, and
the rule that all checks happen before anything is written. Those parts are
copied and not imported, because importing build_corpus builds the whole
reference corpus at module level, which is several seconds of rendering for
functions this script could otherwise borrow.

**Nothing in here is read from the outside.** The prose comes from the word list
below and from nowhere else. That is decision D-02 of the phase and the answer to
T-05-18 in the threat register: the corpus lands on a rented machine, and a
rented machine must never see a real document. The seed and the checksum over the
file list, both printed at the end, are what turns "synthetic" from a claim into
a record: the same seed produces the same 50.000 files, byte for byte, on any
machine and in any year.

Run it, from anywhere, with the environment of the backend because Pillow lives
there:

    cd backend
    uv run python ../scripts/dev/build_load_corpus.py --seed phase5 --out /mnt/corpus
    uv run python ../scripts/dev/build_load_corpus.py --seed phase5-dry --dry-run-files --out /tmp/dry

The second form is the 500 file dry run that goes through the whole chain on the
box before twenty hours are invested in the first.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
import zipfile
import zlib
from array import array
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import TextIO

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class Rng:
    """Deterministic pseudo random numbers, SHA-256 in counter mode.

    Not the standard library generator: the Mersenne Twister behind it is stable
    across releases in practice, but nothing in the language promises that, and
    this corpus has to be reproducible years after the measurement it feeds. A
    hash function is specified outside this project and cannot drift with an
    interpreter upgrade. No claim of cryptographic strength is made or needed
    here; what is needed is a function that never changes its mind.
    """

    __slots__ = ("_buffer", "_counter", "_root", "_used")

    def __init__(self, *parts: object) -> None:
        material = "|".join(str(part) for part in parts).encode("utf-8")
        self._root = hashlib.sha256(material).digest()
        self._counter = 0
        self._buffer = b""
        self._used = 0

    def raw(self, count: int) -> bytes:
        """The next ``count`` bytes of the stream."""
        while len(self._buffer) - self._used < count:
            self._buffer = (
                self._buffer[self._used :] + hashlib.sha256(self._root + self._counter.to_bytes(8, "big")).digest()
            )
            self._counter += 1
            self._used = 0
        chunk = self._buffer[self._used : self._used + count]
        self._used += count
        return chunk

    def below(self, bound: int) -> int:
        """A number in ``range(bound)``.

        The modulo of a four byte draw is minimally biased towards the small end
        for bounds that are not powers of two. The bias is below one in a million
        for every bound this script uses, and it is named here so that a reader
        does not have to wonder whether it was overlooked.
        """
        return int.from_bytes(self.raw(4), "big") % bound

    def between(self, low: int, high: int) -> int:
        """A number in ``[low, high]``, both ends included."""
        return low + self.below(high - low + 1)

    def pick(self, items: Sequence[str]) -> str:
        return items[self.below(len(items))]

    def token(self) -> str:
        """Sixteen bytes as hex, to seed a derived generator."""
        return self.raw(16).hex()

    def draw_words(self, vocabulary: Sequence[str], count: int) -> list[str]:
        """Many words in one go, because a page of prose is a thousand draws.

        Two bytes per word rather than four: the vocabulary has a few hundred
        entries, and halving the hash traffic halves the cost of the largest loop
        in this script. The draw goes through an array rather than through a
        slice per word, which is six times faster, and the byte order is forced
        to little endian afterwards so that the corpus does not depend on the
        machine it is built on.
        """
        size = len(vocabulary)
        numbers = array("H")
        numbers.frombytes(self.raw(count * 2))
        if sys.byteorder != "little":
            numbers.byteswap()
        return [vocabulary[number % size] for number in numbers]


# ---------------------------------------------------------------------------
# The vocabulary. German administrative prose, invented word by word, so that a
# generated document reads like an office document without a single line of it
# coming from one (D-02, T-05-18).
# ---------------------------------------------------------------------------

WORDS: tuple[str, ...] = (
    "Abteilung",
    "Aktenzeichen",
    "Amtsblatt",
    "Anlage",
    "Antrag",
    "Anhörung",
    "Auflage",
    "Aufwendungen",
    "Ausschuss",
    "Bauleitplanung",
    "Bearbeitung",
    "Bebauungsplan",
    "Bedarfsermittlung",
    "Beitragssatzung",
    "Bekanntmachung",
    "Bemessungsgrundlage",
    "Bescheid",
    "Beschluss",
    "Bestandsaufnahme",
    "Betrag",
    "Bewilligung",
    "Buchungsstelle",
    "Bürgermeisterin",
    "Dienststelle",
    "Eingang",
    "Einwendung",
    "Entwässerung",
    "Erschliessung",
    "Erschliessungsbeitrag",
    "Fachbereich",
    "Festsetzung",
    "Flächennutzungsplan",
    "Förderung",
    "Frist",
    "Gebühr",
    "Gemeinderat",
    "Genehmigung",
    "Geschäftszeichen",
    "Gewerbegebiet",
    "Grundstück",
    "Grundstücksverkehrsgenehmigung",
    "Haushaltsjahr",
    "Haushaltsplan",
    "Hinweis",
    "Instandhaltung",
    "Jahresrechnung",
    "Kalenderjahr",
    "Kassenzeichen",
    "Kostenübernahme",
    "Kündigungsfrist",
    "Landesbehörde",
    "Liegenschaft",
    "Massnahme",
    "Mietverhältnis",
    "Mitteilung",
    "Nachweis",
    "Naturschutzbehörde",
    "Niederschrift",
    "Ordnungsamt",
    "Personalstelle",
    "Planungsrecht",
    "Protokoll",
    "Prüfung",
    "Rechnung",
    "Rechtsbehelf",
    "Registratur",
    "Sachverhalt",
    "Satzung",
    "Schlussrechnung",
    "Sitzung",
    "Stellungnahme",
    "Strassenbau",
    "Teilnehmer",
    "Termin",
    "Übergabe",
    "Überprüfung",
    "Umlage",
    "Unterlagen",
    "Verfahren",
    "Vergabe",
    "Verkehrsfläche",
    "Vermerk",
    "Verordnung",
    "Vertrag",
    "Verwaltung",
    "Vorgang",
    "Vorlage",
    "Wasserwirtschaft",
    "Widerspruch",
    "Wirtschaftsplan",
    "Zahlungseingang",
    "Zuständigkeit",
    "Zuwendung",
    "abgeschlossen",
    "beantragt",
    "beigefügt",
    "bewilligt",
    "eingereicht",
    "erforderlich",
    "erteilt",
    "festgestellt",
    "fortgeschrieben",
    "geprüft",
    "massgeblich",
    "mitgeteilt",
    "unverzüglich",
    "vorgelegt",
    "zugestellt",
    "zurückgestellt",
    "und",
    "der",
    "die",
    "das",
    "des",
    "für",
    "über",
    "nach",
    "durch",
    "gemäss",
    "wurde",
    "wird",
    "ist",
    "sind",
    "im",
    "zum",
    "einer",
    "eines",
)

# The words that become file names. ASCII on purpose: the corpus is copied into a
# Nextcloud data directory over ssh and scanned by occ, and a file name is the one
# place where a special character buys nothing and can cost an hour.
SLUGS: tuple[str, ...] = (
    "aktenvermerk",
    "anlage",
    "antrag",
    "ausschreibung",
    "bericht",
    "bescheid",
    "beschluss",
    "gutachten",
    "haushalt",
    "kostenaufstellung",
    "mitteilung",
    "niederschrift",
    "protokoll",
    "rechnung",
    "satzung",
    "schriftwechsel",
    "stellungnahme",
    "uebersicht",
    "vergabe",
    "vermerk",
    "vertrag",
    "vorlage",
    "widerspruch",
    "zuwendung",
)

# One sentence every so many words. Prose without full stops would be a word
# cloud, and a sentence boundary is what a snippet generator cuts on.
SENTENCE_WORDS = 12


def prose_lines(rng: Rng, line_count: int, width: int) -> list[str]:
    """``line_count`` lines of German prose, none wider than ``width``.

    Lines are packed by hand rather than through textwrap: this is the innermost
    loop of the whole script, it runs a few million times for the full corpus,
    and the standard library wrapper does five times the work for a result that
    would look the same.
    """
    # Six characters per word plus the space is the measured average of the list
    # above; a quarter more than that is drawn so the packing never runs dry.
    estimate = line_count * width // 6 + line_count
    words = rng.draw_words(WORDS, estimate)
    lines: list[str] = []
    current: list[str] = []
    length = 0
    for position, word in enumerate(words):
        piece = word + ("." if position % SENTENCE_WORDS == SENTENCE_WORDS - 1 else "")
        if current and length + len(piece) + 1 > width:
            lines.append(" ".join(current))
            if len(lines) == line_count:
                return lines
            current = []
            length = 0
        current.append(piece)
        length += len(piece) + 1
    if current and len(lines) < line_count:
        lines.append(" ".join(current))
    return lines


# ---------------------------------------------------------------------------
# The typeface, inherited from build_corpus.py including its reasons: a different
# font file is a different corpus, and it would change what OCR reads without
# changing a line of this script.
# ---------------------------------------------------------------------------

FONT_DIR = Path(__file__).resolve().parents[2] / "testdata" / "fonts"
DEJAVU_SANS = FONT_DIR / "DejaVuSans.ttf"
DEJAVU_SANS_SHA256 = "57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e"

# The line every character class of this corpus stands in, taken from
# build_corpus.py so that both corpora fail on the same missing glyph.
GLYPH_PROBE = "Strasse Jänner Grundstücksverkehrsgenehmigung"


@cache
def load_font(size: int) -> ImageFont.FreeTypeFont:
    """The one typeface of this corpus, refused if it is not the pinned one."""
    payload = DEJAVU_SANS.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != DEJAVU_SANS_SHA256:
        message = f"{DEJAVU_SANS} is not the pinned font: expected {DEJAVU_SANS_SHA256}, found {digest}"
        raise SystemExit(message)
    return ImageFont.truetype(io.BytesIO(payload), size=size)


def _glyph_bitmap(character: str, size: int) -> bytes:
    tile = Image.new("L", (size * 2, size * 2), color=255)
    ImageDraw.Draw(tile).text((size // 4, size // 4), character, font=load_font(size), fill=0)
    return tile.tobytes()


def assert_every_glyph_exists(text: str) -> None:
    """Refuse to build if any character renders as a replacement box.

    A box in a scanned page is not a cosmetic defect. Tesseract would read
    something else than the document contains, and the whole run would measure a
    corpus that is not the one the report describes. U+E000 sits in the private
    use area and no sane font maps it, so its bitmap is the shape of "missing".
    """
    missing = _glyph_bitmap(chr(0xE000), 48)
    for character in sorted(set(text)):
        if character.isspace():
            continue
        if _glyph_bitmap(character, 48) == missing:
            message = f"the pinned font has no glyph for {character!r}, the corpus would carry a box instead"
            raise SystemExit(message)


def assert_ready_to_write() -> None:
    """Every check this script knows, all of them before the first byte.

    The font is verified by loading it, and every character that can ever reach
    the renderer is verified to exist in it. Running this after the first file
    would mean throwing away hours of writing to learn something that costs a
    second.
    """
    alphabet = GLYPH_PROBE + "".join(WORDS) + "".join(SLUGS) + "0123456789.,;:()-/"
    assert_every_glyph_exists(alphabet)


# ---------------------------------------------------------------------------
# PDF primitives, inherited from build_corpus.py.
# ---------------------------------------------------------------------------

A4_POINTS = (595, 842)

# A4 at 300 dpi. The reference corpus renders at 150 to keep committed files
# small; this one has no such constraint and 300 dpi is the resolution D-02 names
# and the one the OCR budget of the phase is calculated against.
A4_PIXELS = (2480, 3508)

FONT_OBJECT = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"

# What one page costs in the assembled file beyond its content stream: the page
# dictionary, the stream wrapper and three cross reference entries. Used to stop
# growing a document one page before it overshoots, never for a size that is
# reported: the report always carries the counted bytes.
PAGE_OVERHEAD_BYTES = 260


def stream_object(dictionary: str, data: bytes) -> bytes:
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


def pdf_string(line: str) -> bytes:
    """A literal string for a content stream, cp1252 as /WinAnsiEncoding means."""
    raw = line.encode("cp1252")
    for special, escaped in ((b"\\", b"\\\\"), (b"(", b"\\("), (b")", b"\\)")):
        raw = raw.replace(special, escaped)
    return raw


def text_content_stream(lines: Sequence[str]) -> bytes:
    """One page of a text layer, the kind of PDF that never reaches tesseract."""
    content = bytearray()
    baseline = A4_POINTS[1] - 60
    for line in lines:
        content += f"BT /F1 11 Tf 50 {baseline} Td (".encode("ascii")
        content += pdf_string(line)
        content += b") Tj ET\n"
        baseline -= 20
    return bytes(content)


def render_page(lines: Sequence[str]) -> Image.Image:
    """German prose as grey pixels at 300 dpi, which is what OCR is measured on.

    Clean on purpose, for the reason build_corpus.py states: a corpus that
    carries generated dirt measures the dirt generator, and the day tesseract
    reads one word less nobody could tell whether the engine or the noise moved.
    """
    image = Image.new("L", A4_PIXELS, color=255)
    draw = ImageDraw.Draw(image)
    font = load_font(46)
    y = 240
    for line in lines:
        draw.text((240, y), line, font=font, fill=0)
        y += 62
    return image


def flate_image_object(image: Image.Image) -> bytes:
    """One greyscale page as a PDF image object.

    Compression level 6 and not 9: the reference corpus is committed and pays
    once for the smallest possible file, this one is written fifty thousand times
    and the last few percent are not worth a third of the run time.
    """
    width, height = image.size
    return stream_object(
        f"/Type /XObject /Subtype /Image /Width {width} /Height {height} /ColorSpace /DeviceGray"
        f" /BitsPerComponent 8 /Filter /FlateDecode",
        zlib.compress(image.tobytes(), 6),
    )


def assemble_pdf(pages: Sequence[tuple[str, bytes]]) -> bytes:
    """Text pages and image pages into one document, numbered and cross referenced.

    A page is a pair of a kind and a payload. For a text page the payload is the
    content stream, for an image page it is the finished image object, already
    compressed: the raw bitmap of a 300 dpi A4 page is nine megabytes, and a
    thirty page scan would hold a quarter of a gigabyte if the pages were kept as
    images until the end.
    """
    width, height = A4_POINTS
    objects: list[bytes] = [b"", b""]

    def add(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    font_number = 0
    if any(kind == "text" for kind, _ in pages):
        font_number = add(FONT_OBJECT)

    page_numbers: list[int] = []
    for kind, payload in pages:
        if kind == "text":
            contents = add(stream_object("", payload))
            resources = f"<< /Font << /F1 {font_number} 0 R >> >>"
        else:
            image_number = add(payload)
            contents = add(stream_object("", f"q {width} 0 0 {height} 0 0 cm /Im1 Do Q\n".encode("ascii")))
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


# ---------------------------------------------------------------------------
# ZIP primitives, inherited from build_corpus.py: the default stamps the build
# time into every entry and a second run would differ from the first.
# ---------------------------------------------------------------------------

ZIP_TIMESTAMP = (2026, 9, 1, 12, 0, 0)


def reproducible_zip(parts: dict[str, str | bytes], *, stored_first: str | None = None) -> bytes:
    """Pack named parts into an archive that a second run reproduces exactly.

    A part given as text is deflated, a part given as bytes is stored. That is
    not a detail: the picture inside an office document is what gives the file
    the size its category promises, and a picture that deflates to nothing would
    leave the file at a tenth of it.
    """
    order = list(parts)
    if stored_first is not None:
        order.remove(stored_first)
        order.insert(0, stored_first)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in order:
            payload = parts[name]
            info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
            stored = name == stored_first or isinstance(payload, bytes)
            info.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, payload)
    return buffer.getvalue()


def escape(text: str) -> str:
    """The three characters that must not stand raw in XML content.

    Hand written rather than taken from xml.sax.saxutils, because importing that
    module trips the security ruleset of this project over the parser that comes
    with it, and three replacements are not worth an exemption.
    """
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# The scanned annex, which is where the byte weight of a document comes from.
#
# A 350 KB office document in the real world is not a hundred pages of prose. It
# is two pages of text and a picture, and the picture is nine tenths of the file.
# Reproducing that is not a shortcut, it is the difference between a corpus that
# looks like a Nextcloud and one that does not: prose deflates by a factor of
# six, so reaching 350 KB with words alone would take two megabytes of text per
# file, and fifteen thousand such files would put forty gigabytes of text into an
# index that the phase budget expects to hold three to six.
#
# The picture is an uncompressed greyscale TIFF, which is what a scanner and a
# fax gateway actually write, and its size is therefore exactly its pixel count.
# That is what lets a category hit its byte target without a single padding byte
# that no reader would ever see.
# ---------------------------------------------------------------------------

# The lines the annex shows. Fixed and not drawn from the seed: the picture is
# cached across the whole run, and fifty thousand different pictures would be an
# hour of rendering and a gigabyte of memory for pixels no extractor ever reads.
# Nothing about the load depends on them differing, because the bytes are the
# load. What is measured over these pixels is the OCR of the scan categories, and
# those render their own pages from the seed.
FIGURE_LINES: tuple[str, ...] = (
    "Anlage zum Vorgang",
    "",
    "Der beigefügte Auszug wurde eingescannt und dem Vorgang beigelegt.",
    "Die Urschrift liegt in der Registratur.",
)

# What one stored part costs beyond its own bytes: the TIFF header, the local
# file header and the entry in the central directory. Used only to decide how
# large the picture has to be, never for a size that is reported: the report
# always carries the counted bytes of the finished file.
MEDIA_OVERHEAD_BYTES = 340


@cache
def figure_image(width: int, height: int) -> Image.Image:
    page = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(page)
    font = load_font(max(width // 30, 8))
    y = height // 8
    for line in FIGURE_LINES:
        draw.text((width // 12, y), line, font=font, fill=0)
        y += width // 22
    return page


@cache
def figure_pixels(width: int, height: int) -> bytes:
    """The annex as raw greyscale bytes, which is exactly ``width * height``."""
    return figure_image(width, height).tobytes()


@cache
def figure_tiff(width: int, height: int) -> bytes:
    """The annex as an uncompressed TIFF, for the packages that carry media."""
    buffer = io.BytesIO()
    figure_image(width, height).save(buffer, format="TIFF", compression="raw")
    return buffer.getvalue()


def figure_size(target: int, base: int, width: int) -> tuple[int, int]:
    """The picture that lifts a document from ``base`` to the target of its category.

    The height is rounded down to a multiple of eight so that a run of fifty
    thousand files needs one or two pictures instead of fifty thousand: they are
    cached, and one cache entry per file would hold twenty gigabytes. The price is
    that a file may fall up to eight rows of pixels short of its target, which is
    about one percent and below the "about" of the distribution table.
    """
    remaining = target - base - MEDIA_OVERHEAD_BYTES
    return width, max(remaining // width // 8, 1) * 8


def raw_image_object(width: int, height: int, pixels: bytes) -> bytes:
    """An uncompressed greyscale image object, the PDF form of the same annex."""
    return stream_object(
        f"/Type /XObject /Subtype /Image /Width {width} /Height {height} /ColorSpace /DeviceGray /BitsPerComponent 8",
        pixels,
    )


# ---------------------------------------------------------------------------
# OOXML and OpenDocument boilerplate. Written out rather than produced by
# python-docx or python-pptx: those libraries stamp the current time into every
# ZIP entry, which is exactly the property this corpus may not have.
# ---------------------------------------------------------------------------

PACKAGE_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOCUMENT_RELS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

OFFICE_DOCUMENT = "application/vnd.openxmlformats-officedocument"
DOCX_MAIN = f"{OFFICE_DOCUMENT}.wordprocessingml.document.main+xml"
XLSX_MAIN = f"{OFFICE_DOCUMENT}.spreadsheetml.sheet.main+xml"
XLSX_SHEET = f"{OFFICE_DOCUMENT}.spreadsheetml.worksheet+xml"
XLSX_STYLES = f"{OFFICE_DOCUMENT}.spreadsheetml.styles+xml"
PPTX_MAIN = f"{OFFICE_DOCUMENT}.presentationml.presentation.main+xml"
PPTX_SLIDE = f"{OFFICE_DOCUMENT}.presentationml.slide+xml"
PPTX_MASTER = f"{OFFICE_DOCUMENT}.presentationml.slideMaster+xml"
PPTX_LAYOUT = f"{OFFICE_DOCUMENT}.presentationml.slideLayout+xml"
PPTX_THEME = f"{OFFICE_DOCUMENT}.theme+xml"

XML_HEADER = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'


def _relationships(entries: Sequence[tuple[str, str, str]]) -> str:
    """A .rels part from triples of id, type and target."""
    return "".join(
        (
            XML_HEADER,
            f'<Relationships xmlns="{PACKAGE_RELS}">',
            *(
                f'<Relationship Id="{identifier}" Type="{DOCUMENT_RELS}/{kind}" Target="{target}"/>'
                for identifier, kind, target in entries
            ),
            "</Relationships>",
        )
    )


def _content_types(defaults: Sequence[tuple[str, str]], overrides: Sequence[tuple[str, str]]) -> str:
    return "".join(
        (
            XML_HEADER,
            f'<Types xmlns="{CONTENT_TYPES_NS}">',
            *(f'<Default Extension="{extension}" ContentType="{kind}"/>' for extension, kind in defaults),
            *(f'<Override PartName="{part}" ContentType="{kind}"/>' for part, kind in overrides),
            "</Types>",
        )
    )


RELS_TYPE = "application/vnd.openxmlformats-package.relationships+xml"
DEFAULT_TYPES = (("rels", RELS_TYPE), ("xml", "application/xml"), ("tif", "image/tiff"))

# The picture is a hundred rows of pixels wider than it is high, and the width is
# fixed so that the height alone carries the size arithmetic of figure_size.
MEDIA_WIDTH = 570

# The amount of prose. Two to three pages worth of text in a document of 350 KB,
# which is the ratio a real office document has, and the ratio the index budget of
# the phase was calculated with.
DOCX_LINES = 400
XLSX_ROWS = 200
PPTX_LINES = 60
ODT_LINES = 400
ODS_ROWS = 200

# The name the annex carries inside a package. One name for all of them, so a
# reader of a generated file finds the same part in every format.
MEDIA_PART = "media/anlage.tif"


def _with_annex(parts: dict[str, str | bytes], name: str, target: int) -> bytes:
    """Zip the text parts, measure, add the annex that reaches the target, zip again.

    Two archives instead of one, and the first one is thrown away. It costs a few
    milliseconds and it removes the one thing a fixed estimate could not survive:
    the day a boilerplate part grows, the file size stays on target by itself.
    """
    base = reproducible_zip(parts)
    width, height = figure_size(target, len(base), MEDIA_WIDTH)
    parts[name] = figure_tiff(width, height)
    return reproducible_zip(parts)


def build_docx_bytes(rng: Rng, target: int) -> bytes:
    body = "".join(f"<w:p><w:r><w:t>{escape(line)}</w:t></w:r></w:p>" for line in prose_lines(rng, DOCX_LINES, 95))
    document = "".join((XML_HEADER, f'<w:document xmlns:w="{WORD_NS}"><w:body>', body, "</w:body></w:document>"))
    parts: dict[str, str | bytes] = {
        "[Content_Types].xml": _content_types(DEFAULT_TYPES, (("/word/document.xml", DOCX_MAIN),)),
        "_rels/.rels": _relationships((("rId1", "officeDocument", "word/document.xml"),)),
        "word/document.xml": document,
    }
    return _with_annex(parts, f"word/{MEDIA_PART}", target)


XLSX_COLUMNS = ("A", "B", "C", "D", "E", "F")

XLSX_STYLESHEET = "".join(
    (
        XML_HEADER,
        f'<styleSheet xmlns="{SHEET_NS}">',
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>',
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>',
        '<borders count="1"><border/></borders>',
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>',
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>',
        # The named default style is not decoration either: without it openpyxl
        # warns "Workbook contains no default style" on every single file, and
        # ten thousand of those warnings in the log of the load run would bury
        # the lines that matter.
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>',
        "</styleSheet>",
    )
)


def build_xlsx_bytes(rng: Rng, target: int) -> bytes:
    words = rng.draw_words(WORDS, XLSX_ROWS * len(XLSX_COLUMNS))
    rows: list[str] = []
    for number in range(1, XLSX_ROWS + 1):
        cells = "".join(
            f'<c r="{column}{number}" t="inlineStr"><is><t>'
            f"{escape(words[(number - 1) * len(XLSX_COLUMNS) + at])}</t></is></c>"
            for at, column in enumerate(XLSX_COLUMNS)
        )
        rows.append(f'<row r="{number}">{cells}</row>')
    # The dimension element is not decoration: openpyxl in read only mode, which
    # is the mode the backend uses, refuses to iterate a sheet whose extent it
    # cannot read.
    sheet = "".join(
        (
            XML_HEADER,
            f'<worksheet xmlns="{SHEET_NS}">',
            f'<dimension ref="A1:{XLSX_COLUMNS[-1]}{XLSX_ROWS}"/><sheetData>',
            *rows,
            "</sheetData></worksheet>",
        )
    )
    workbook = "".join(
        (
            XML_HEADER,
            f'<workbook xmlns="{SHEET_NS}" xmlns:r="{DOCUMENT_RELS}">',
            '<sheets><sheet name="Vorgaenge" sheetId="1" r:id="rId1"/></sheets>',
            "</workbook>",
        )
    )
    parts: dict[str, str | bytes] = {
        "[Content_Types].xml": _content_types(
            DEFAULT_TYPES,
            (
                ("/xl/workbook.xml", XLSX_MAIN),
                ("/xl/worksheets/sheet1.xml", XLSX_SHEET),
                ("/xl/styles.xml", XLSX_STYLES),
            ),
        ),
        "_rels/.rels": _relationships((("rId1", "officeDocument", "xl/workbook.xml"),)),
        "xl/_rels/workbook.xml.rels": _relationships(
            (
                ("rId1", "worksheet", "worksheets/sheet1.xml"),
                ("rId2", "styles", "styles.xml"),
            )
        ),
        "xl/workbook.xml": workbook,
        "xl/styles.xml": XLSX_STYLESHEET,
        "xl/worksheets/sheet1.xml": sheet,
    }
    return _with_annex(parts, f"xl/{MEDIA_PART}", target)


PPTX_SLIDES = 6

PPTX_SLIDE_MASTER = "".join(
    (
        XML_HEADER,
        f'<p:sldMaster xmlns:a="{DML_NS}" xmlns:r="{DOCUMENT_RELS}" xmlns:p="{PML_NS}">',
        '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>',
        "<p:grpSpPr/></p:spTree></p:cSld>",
        '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" hlink="hlink" folHlink="folHlink"/>',
        '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>',
        "</p:sldMaster>",
    )
)

PPTX_SLIDE_LAYOUT = "".join(
    (
        XML_HEADER,
        f'<p:sldLayout xmlns:a="{DML_NS}" xmlns:r="{DOCUMENT_RELS}" xmlns:p="{PML_NS}" type="blank" preserve="1">',
        '<p:cSld name="Leer"><p:spTree>',
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>',
        "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>",
    )
)

PPTX_THEME_PART = "".join(
    (
        XML_HEADER,
        f'<a:theme xmlns:a="{DML_NS}" name="Findling"><a:themeElements/></a:theme>',
    )
)


def _pptx_slide(lines: Sequence[str]) -> str:
    paragraphs = "".join(f"<a:p><a:r><a:t>{escape(line)}</a:t></a:r></a:p>" for line in lines)
    return "".join(
        (
            XML_HEADER,
            f'<p:sld xmlns:a="{DML_NS}" xmlns:r="{DOCUMENT_RELS}" xmlns:p="{PML_NS}">',
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>',
            "<p:grpSpPr/>",
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Textfeld"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>',
            "<p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>",
            paragraphs,
            "</p:txBody></p:sp></p:spTree></p:cSld></p:sld>",
        )
    )


def build_pptx_bytes(rng: Rng, target: int) -> bytes:
    slide_ids = "".join(
        f'<p:sldId id="{255 + number}" r:id="rId{number + 1}"/>' for number in range(1, PPTX_SLIDES + 1)
    )
    presentation = "".join(
        (
            XML_HEADER,
            f'<p:presentation xmlns:a="{DML_NS}" xmlns:r="{DOCUMENT_RELS}" xmlns:p="{PML_NS}">',
            '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>',
            f"<p:sldIdLst>{slide_ids}</p:sldIdLst>",
            '<p:sldSz cx="9144000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/>',
            "</p:presentation>",
        )
    )
    parts: dict[str, str | bytes] = {
        "[Content_Types].xml": _content_types(
            DEFAULT_TYPES,
            (
                ("/ppt/presentation.xml", PPTX_MAIN),
                ("/ppt/slideMasters/slideMaster1.xml", PPTX_MASTER),
                ("/ppt/slideLayouts/slideLayout1.xml", PPTX_LAYOUT),
                ("/ppt/theme/theme1.xml", PPTX_THEME),
                *((f"/ppt/slides/slide{number}.xml", PPTX_SLIDE) for number in range(1, PPTX_SLIDES + 1)),
            ),
        ),
        "_rels/.rels": _relationships((("rId1", "officeDocument", "ppt/presentation.xml"),)),
        "ppt/_rels/presentation.xml.rels": _relationships(
            (
                ("rId1", "slideMaster", "slideMasters/slideMaster1.xml"),
                *((f"rId{number + 1}", "slide", f"slides/slide{number}.xml") for number in range(1, PPTX_SLIDES + 1)),
            )
        ),
        "ppt/presentation.xml": presentation,
        "ppt/slideMasters/slideMaster1.xml": PPTX_SLIDE_MASTER,
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": _relationships(
            (
                ("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"),
                ("rId2", "theme", "../theme/theme1.xml"),
            )
        ),
        "ppt/slideLayouts/slideLayout1.xml": PPTX_SLIDE_LAYOUT,
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": _relationships(
            (("rId1", "slideMaster", "../slideMasters/slideMaster1.xml"),)
        ),
        "ppt/theme/theme1.xml": PPTX_THEME_PART,
    }
    for number in range(1, PPTX_SLIDES + 1):
        parts[f"ppt/slides/slide{number}.xml"] = _pptx_slide(prose_lines(rng, PPTX_LINES, 80))
        parts[f"ppt/slides/_rels/slide{number}.xml.rels"] = _relationships(
            (("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"),)
        )
    return _with_annex(parts, f"ppt/{MEDIA_PART}", target)


ODF_TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
ODF_OFFICE_NS = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
ODF_TABLE_NS = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
ODF_MANIFEST_NS = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
ODT_MEDIA_TYPE = "application/vnd.oasis.opendocument.text"
ODS_MEDIA_TYPE = "application/vnd.oasis.opendocument.spreadsheet"


ODF_MEDIA_PART = "Pictures/anlage.tif"


def _odf_manifest(media_type: str) -> str:
    return "".join(
        (
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<manifest:manifest xmlns:manifest="{ODF_MANIFEST_NS}" manifest:version="1.3">',
            f'<manifest:file-entry manifest:full-path="/" manifest:media-type="{media_type}"/>',
            '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>',
            f'<manifest:file-entry manifest:full-path="{ODF_MEDIA_PART}" manifest:media-type="image/tiff"/>',
            "</manifest:manifest>",
        )
    )


def _odf_document(media_type: str, content: str, target: int) -> bytes:
    parts: dict[str, str | bytes] = {
        "mimetype": media_type,
        "content.xml": content,
        "META-INF/manifest.xml": _odf_manifest(media_type),
    }
    base = reproducible_zip(parts, stored_first="mimetype")
    width, height = figure_size(target, len(base), MEDIA_WIDTH)
    parts[ODF_MEDIA_PART] = figure_tiff(width, height)
    return reproducible_zip(parts, stored_first="mimetype")


def build_odt_bytes(rng: Rng, target: int) -> bytes:
    body = "".join(f"<text:p>{escape(line)}</text:p>" for line in prose_lines(rng, ODT_LINES, 95))
    content = "".join(
        (
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<office:document-content xmlns:office="{ODF_OFFICE_NS}" xmlns:text="{ODF_TEXT_NS}"',
            ' office:version="1.3"><office:body><office:text>',
            "<text:h>Vorgang der Verwaltung</text:h>",
            body,
            "</office:text></office:body></office:document-content>",
        )
    )
    return _odf_document(ODT_MEDIA_TYPE, content, target)


ODS_COLUMNS = 6


def build_ods_bytes(rng: Rng, target: int) -> bytes:
    words = rng.draw_words(WORDS, ODS_ROWS * ODS_COLUMNS)
    rows: list[str] = []
    for number in range(ODS_ROWS):
        cells = "".join(
            f'<table:table-cell office:value-type="string"><text:p>'
            f"{escape(words[number * ODS_COLUMNS + at])}</text:p></table:table-cell>"
            for at in range(ODS_COLUMNS)
        )
        rows.append(f"<table:table-row>{cells}</table:table-row>")
    content = "".join(
        (
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<office:document-content xmlns:office="{ODF_OFFICE_NS}" xmlns:text="{ODF_TEXT_NS}"',
            f' xmlns:table="{ODF_TABLE_NS}" office:version="1.3">',
            '<office:body><office:spreadsheet><table:table table:name="Vorgaenge">',
            *rows,
            "</table:table></office:spreadsheet></office:body></office:document-content>",
        )
    )
    return _odf_document(ODS_MEDIA_TYPE, content, target)


# ---------------------------------------------------------------------------
# The builders of the distribution. Every one of them yields chunks rather than
# returning a payload, because the largest category cannot fit in memory twice.
# ---------------------------------------------------------------------------

SCAN_LINES = 48
SCAN_WIDTH = 78
TEXT_LINES = 38
TEXT_WIDTH = 88
TEXT_PDF_PAGES = 10


def _scan_pdf(rng: Rng, pages: int) -> bytes:
    rendered: list[tuple[str, bytes]] = []
    for _ in range(pages):
        page = render_page(prose_lines(rng, SCAN_LINES, SCAN_WIDTH))
        rendered.append(("image", flate_image_object(page)))
    return assemble_pdf(rendered)


def build_scan_single(rng: Rng, extension: str, target: int) -> Iterator[bytes]:
    """One scanned page. This category is what the run time of the load test is."""
    del extension, target
    yield _scan_pdf(rng, 1)


# How many pages a multi page scan has. Not uniform between 2 and 30, and that
# is the whole point of the table: a uniform draw averages sixteen pages, and the
# run time calculation of 05-RESEARCH.md is built on an average of eight. Every
# page multiplies straight into the OCR hours, so the shape of this draw is worth
# more than its range. Most enclosures are three or four pages, a few are a dozen,
# and one in ten is the fat one that keeps a single job busy for two minutes.
SCAN_PAGE_BANDS: tuple[tuple[int, int, int], ...] = (
    (60, 2, 6),
    (30, 7, 14),
    (10, 15, 30),
)


def _scan_page_count(rng: Rng) -> int:
    draw = rng.below(sum(share for share, _, _ in SCAN_PAGE_BANDS))
    seen = 0
    for share, low, high in SCAN_PAGE_BANDS:
        seen += share
        if draw < seen:
            return rng.between(low, high)
    return SCAN_PAGE_BANDS[-1][2]


def build_scan_multi(rng: Rng, extension: str, target: int) -> Iterator[bytes]:
    """Two to thirty scanned pages, the files that push a single job into minutes."""
    del extension, target
    yield _scan_pdf(rng, _scan_page_count(rng))


def build_text_pdf(rng: Rng, extension: str, target: int) -> Iterator[bytes]:
    """Prose with a real text layer plus one scanned annex at the back.

    Ten pages of text and one picture, which is what a notice with an enclosure
    looks like. The annex is one page in eleven, far below the share at which
    findling.extract.pdf declares a whole document scanned, so this category
    stays on the text route and does not quietly become an eleventh hour of OCR.
    """
    del extension
    pages: list[tuple[str, bytes]] = [
        ("text", text_content_stream(prose_lines(rng, TEXT_LINES, TEXT_WIDTH))) for _ in range(TEXT_PDF_PAGES)
    ]
    base = assemble_pdf(pages)
    width, height = figure_size(target, len(base), MEDIA_WIDTH)
    pages.append(("image", raw_image_object(width, height, figure_pixels(width, height))))
    yield assemble_pdf(pages)


def build_ooxml(rng: Rng, extension: str, target: int) -> Iterator[bytes]:
    if extension == "docx":
        yield build_docx_bytes(rng, target)
    elif extension == "xlsx":
        yield build_xlsx_bytes(rng, target)
    else:
        yield build_pptx_bytes(rng, target)


def build_opendocument(rng: Rng, extension: str, target: int) -> Iterator[bytes]:
    if extension == "odt":
        yield build_odt_bytes(rng, target)
    else:
        yield build_ods_bytes(rng, target)


# Every fourth plain text file is written in the legacy encoding, for the reason
# build_corpus.py gives for its two: a Nextcloud that has grown for a decade is
# full of Windows-1252, every umlaut in it is a single byte, and that byte is
# invalid UTF-8.
LEGACY_ENCODING_IN = 4


def build_plain(rng: Rng, extension: str, target: int) -> Iterator[bytes]:
    encoding = "cp1252" if rng.below(LEGACY_ENCODING_IN) == 0 else "utf-8"
    written = 0
    heading = f"Vorgang {rng.token()[:8]}\n\n" if extension == "md" else ""
    if extension == "csv":
        heading = "nummer,vorgang,stelle,vermerk\n"
    if heading:
        yield heading.encode(encoding)
        written = len(heading)
    while written < target:
        lines = prose_lines(rng, 40, 96)
        if extension == "csv":
            block = "\n".join(f"{number},{line.replace(',', ' ')}" for number, line in enumerate(lines)) + "\n"
        elif extension == "md":
            block = "## Abschnitt\n\n" + "\n\n".join(lines) + "\n"
        else:
            block = "\n".join(lines) + "\n"
        payload = block.encode(encoding)
        written += len(payload)
        yield payload


IMAGE_OPTIONS: dict[str, dict[str, object]] = {
    # The same four formats and the same encoder settings as the reference
    # corpus, so that a difference between the two corpora can never be an
    # encoder setting nobody wrote down.
    "jpg": {"format": "JPEG", "quality": 88, "optimize": False},
    "png": {"format": "PNG", "optimize": True},
    "tif": {"format": "TIFF", "compression": "tiff_deflate"},
    "webp": {"format": "WEBP", "lossless": True, "quality": 100, "method": 4},
}


def build_image(rng: Rng, extension: str, target: int) -> Iterator[bytes]:
    """A page as a picture, which is the second way a document reaches tesseract."""
    del target
    page = render_page(prose_lines(rng, SCAN_LINES, SCAN_WIDTH))
    options = dict(IMAGE_OPTIONS[extension])
    image_format = str(options.pop("format"))
    buffer = io.BytesIO()
    page.save(buffer, format=image_format, **options)
    yield buffer.getvalue()


OVERSIZE_KEY = "oversize"
OVERSIZE_BYTES = 55_000_000
CHUNK_BYTES = 1_048_576


def build_oversize(rng: Rng, extension: str, target: int) -> Iterator[bytes]:
    """The twenty files above the size cap, written a megabyte at a time.

    They are the reason the coverage figure of the admin page can be judged under
    load at all: on 33 files there was never a denominator large enough to see
    what a handful of too_large verdicts does to it. Streamed, because holding
    55 MB in memory to write 55 MB is exactly the habit this script exists to
    break.
    """
    del extension
    header = "nummer,vorgang,stelle,betrag,vermerk\n"
    yield header.encode("utf-8")
    written = len(header)

    # One megabyte of rows is generated and then repeated. Fifty five megabytes of
    # fresh prose would cost eight seconds a file, and it would buy nothing: this
    # is the one category that is never extracted at all. It is refused on its
    # size before a byte of it is read, which is precisely the verdict it is here
    # to produce.
    block: list[str] = []
    size = 0
    while size < CHUNK_BYTES:
        for line in prose_lines(rng, 64, 110):
            row = f"{line.replace(',', ' ')}\n"
            block.append(row)
            size += len(row)
    payload = "".join(block).encode("utf-8")

    while written < target:
        written += len(payload)
        yield payload


# ---------------------------------------------------------------------------
# The distribution. Straight out of 05-RESEARCH.md pitfall 5, and steered by the
# amount of OCR rather than by the amount of bytes, because OCR is the bottleneck
# and the page count of a scan multiplies directly into the run time.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Category:
    """One row of the distribution table."""

    key: str
    weight: int
    extensions: tuple[str, ...]
    target_bytes: int
    build: Callable[[Rng, str, int], Iterator[bytes]]
    why: str


CATEGORIES: tuple[Category, ...] = (
    Category(
        key="scan_single",
        weight=9_900,
        extensions=("pdf",),
        target_bytes=350_000,
        build=build_scan_single,
        why="Twenty percent of the set and fifteen of the twenty hours: this is the load test.",
    ),
    Category(
        key="scan_multi",
        weight=100,
        extensions=("pdf",),
        target_bytes=2_000_000,
        build=build_scan_multi,
        why="A hundred files of up to thirty pages, so the page cap and a long single job are exercised.",
    ),
    Category(
        key="text_pdf",
        weight=22_500,
        extensions=("pdf",),
        target_bytes=450_000,
        build=build_text_pdf,
        why="The largest category by bytes and the cheapest by time: the text layer path under volume.",
    ),
    Category(
        key="ooxml",
        weight=10_000,
        extensions=("docx", "xlsx", "pptx"),
        target_bytes=350_000,
        build=build_ooxml,
        why="The three Office formats, so the three python extractors are measured under volume.",
    ),
    Category(
        key="opendocument",
        weight=5_000,
        extensions=("odt", "ods"),
        target_bytes=300_000,
        build=build_opendocument,
        why="The ZIP and XPath path of the ODF extractor, which has no library behind it.",
    ),
    Category(
        key="plain_text",
        weight=2_300,
        extensions=("txt", "md", "csv"),
        target_bytes=100_000,
        build=build_plain,
        why="The cheap files, a quarter of them in the legacy encoding, for the charset detection.",
    ),
    Category(
        key="image",
        weight=100,
        extensions=("jpg", "png", "tif", "webp"),
        target_bytes=500_000,
        build=build_image,
        why="The second road into tesseract, one that arrives with an image mimetype of its own.",
    ),
    Category(
        key=OVERSIZE_KEY,
        weight=20,
        extensions=("csv",),
        target_bytes=OVERSIZE_BYTES,
        build=build_oversize,
        why="Above the 50 MB cap on purpose: too_large and the lowered denominator of the coverage figure.",
    ),
)


def allocate(files: int) -> dict[str, int]:
    """Spread ``files`` over the categories so the shares hold and the sum is exact.

    Largest remainder, then a floor of one file per category. Without the floor a
    dry run of 500 files would silently lose the rare categories, and the dry run
    would then prove the chain for a corpus that is not the one the full run
    writes. The floor is paid for by the largest category, which can spare a file.
    """
    if files < len(CATEGORIES):
        message = f"a corpus of {files} files cannot carry the {len(CATEGORIES)} categories of the distribution"
        raise SystemExit(message)

    total_weight = sum(category.weight for category in CATEGORIES)
    quotas = {category.key: category.weight * files / total_weight for category in CATEGORIES}
    counts = {key: int(quota) for key, quota in quotas.items()}

    remainder = files - sum(counts.values())
    by_fraction = sorted(quotas, key=lambda key: (quotas[key] - counts[key], key), reverse=True)
    for key in by_fraction[:remainder]:
        counts[key] += 1

    for key, count in counts.items():
        if count == 0:
            donor = max((other for other in counts if counts[other] >= 2), key=lambda other: (counts[other], other))
            counts[donor] -= 1
            counts[key] = 1

    if sum(counts.values()) != files:
        message = f"the allocation produced {sum(counts.values())} files instead of {files}"
        raise SystemExit(message)
    return counts


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

PART_SUFFIX = ".part"


def write_file(target: Path, chunks: Iterator[bytes]) -> tuple[int, str]:
    """Write one file through a temporary neighbour and hash it on the way.

    The rename is the point. A run that is killed after nineteen hours must not
    leave a truncated PDF behind that looks like a finished one: the indexer would
    read it, report it as corrupt, and the failure would be counted against the
    app rather than against the interrupted copy.
    """
    temporary = target.with_name(target.name + PART_SUFFIX)
    digest = hashlib.sha256()
    size = 0
    try:
        with temporary.open("wb") as stream:
            for chunk in chunks:
                stream.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        temporary.replace(target)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return size, digest.hexdigest()


@dataclass(frozen=True)
class Summary:
    """What the run has to be able to state about itself afterwards."""

    seed: str
    files: int
    total_bytes: int
    checksum: str
    counts: dict[str, int]


def generate(out: Path, seed: str, files: int, report: TextIO) -> Summary:
    """Write the whole corpus and return the record of what was written."""
    assert_ready_to_write()
    counts = allocate(files)

    out.mkdir(parents=True, exist_ok=True)
    writer = csv.writer(report, lineterminator="\n")
    writer.writerow(("name", "bytes", "sha256"))

    listing: list[str] = []
    total = 0
    index = 0
    for category in CATEGORIES:
        for _ in range(counts[category.key]):
            index += 1
            rng = Rng(seed, category.key, index)
            extension = rng.pick(category.extensions)
            name = f"{index:05d}-{rng.pick(SLUGS)}.{extension}"
            size, digest = write_file(out / name, category.build(rng, extension, category.target_bytes))
            writer.writerow((name, size, digest))
            listing.append(f"{name},{size},{digest}")
            total += size

    # The checksum is taken over the sorted list and not over the writing order,
    # so it stays the same if the order of the categories is ever rearranged. It
    # is the one line of the report the measurement document quotes.
    checksum = hashlib.sha256("\n".join(sorted(listing)).encode("ascii")).hexdigest()
    return Summary(seed=seed, files=files, total_bytes=total, checksum=checksum, counts=counts)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

DEFAULT_FILES = 50_000
DRY_RUN_FILES = 500


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write the synthetic load corpus of phase 5, deterministically and streaming."
    )
    parser.add_argument("--seed", required=True, help="the seed; the same seed writes the same corpus")
    parser.add_argument("--files", type=int, default=DEFAULT_FILES, help=f"how many files, default {DEFAULT_FILES}")
    parser.add_argument("--out", type=Path, required=True, help="the directory the corpus is written into")
    parser.add_argument(
        "--dry-run-files",
        type=int,
        nargs="?",
        const=DRY_RUN_FILES,
        default=None,
        help=f"short for --files {DRY_RUN_FILES}, the run that proves the chain before the full one",
    )
    parser.add_argument("--report", type=Path, default=None, help="where the CSV of written files goes, default stdout")
    arguments = parser.parse_args(argv)
    if arguments.dry_run_files is not None:
        arguments.files = arguments.dry_run_files
    return arguments


def main(argv: Sequence[str] | None = None) -> int:
    """Write the corpus and state seed, count, size and checksum.

    Zero for a corpus that was written, and nothing else: the failures this script
    knows all raise, because there is no half success worth reporting when the
    next step is a twenty hour run.
    """
    arguments = parse_arguments(argv)

    if arguments.report is None:
        summary = generate(out=arguments.out, seed=arguments.seed, files=arguments.files, report=sys.stdout)
    else:
        with arguments.report.open("w", encoding="utf-8", newline="") as handle:
            summary = generate(out=arguments.out, seed=arguments.seed, files=arguments.files, report=handle)

    for key, count in summary.counts.items():
        print(f"build_load_corpus: category={key} files={count}")
    print(
        f"build_load_corpus: seed={summary.seed} files={summary.files}"
        f" bytes={summary.total_bytes} checksum={summary.checksum}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
