"""Word 97 to 2003 documents (.doc), read without LibreOffice in the image.

FMT-03. A .doc is a compound file (OLE2, [MS-CFB]) with a stream called
``WordDocument`` and a table stream. olefile 0.47 reads the compound file; the
text is found the way [MS-DOC] 2.4.1 "Retrieving Text" describes it, and that
part is ours, because no maintained pure Python reader exists and the image
carries no LibreOffice, antiword or catdoc (31-RESEARCH, "Don't Hand-Roll").

Sources, all read on learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc:
2.5.1 Fib (9aeaa2e7-4a45-468e-ab13-3f6193eb9394), 2.5.2 FibBase
(26fb6c06-4e5c-4778-ab4e-edbf26a545bb), 2.5.6 FibRgFcLcb97
(0c9df81f-98d0-454e-ad84-b612cd05b1a4), 2.9.38 Clx
(bad26767-b575-44d3-9da3-96378d56ce14), 2.9.209 Prc, 2.9.210 PrcData, 2.9.178
Pcdt, 2.8.35 PlcPcd, 2.9.177 Pcd, 2.9.73 FcCompressed
(aa2e55a2-f4f2-4795-bab5-6d9d7a0ed249), 2.8.25 Plcfld
(751b09bb-72f0-45ef-8e87-666dea68219f), 2.4.3 Overview of Tables and sprmCFSpec
in 2.6.1 Character Properties.

**The way to the text.** The FibBase opens the WordDocument stream. Behind it
come three counted arrays whose counts the specification fixes for every Word
from 97 on (csw 0x000E, cslw 0x0016, cbRgFcLcb at least 0x005D), so fcClx and
lcbClx sit at 0x01A2 and 0x01A6: pair 33 of FibRgFcLcb97, which starts at 0x9A.
They point into the table stream at the Clx: property blocks (Prc, skipped)
followed by the Pcdt, whose PlcPcd lists the pieces of the text in character
order. A piece is either UTF-16LE or compressed 8 bit text.

**Compressed text is not cp1252.** A compressed piece is Latin-1 except for the
bytes of the table in 2.9.73, and that table lacks 0x80, 0x8E and 0x9E, which
cp1252 maps to the euro sign and to the two Z with caron. A byte 0x80 in a
compressed piece is U+0080; the euro sign of a real document is stored in a
Unicode piece.

**What becomes of the special characters.** Paragraph marks (0x0D), line breaks
(0x0B) and page or section breaks (0x0C) become line breaks; the cell and row
marks of a table (0x07) become tabs. A field is "begin 0x13, instructions,
separator 0x14, result, end 0x15", the separator optional and fields nested
(Plcfld): the instructions go, the result stays, a field without separator goes
whole. Picture and drawing anchors (0x01, 0x08), footnote and annotation
references (0x02, 0x05) and the other control characters go. Two are not in
the specification but measured on LibreOffice output: 0x1F is the soft hyphen
and goes, so the word stays whole, 0x1E is the non-breaking hyphen and becomes
a hyphen.

**All the text of the piece table**, which includes footnotes, headers, comments
and text boxes after the main text, because a search for a word in a footnote
should find the document. Text deleted under tracked changes is part of the
pieces too and is indexed with it; telling it apart needs the character
properties, which this reader does not read.

**Named verdicts (D-31-03).** No WordDocument stream: skipped(unsupported_variant).
fEncrypted: skipped(encrypted), which covers XOR obfuscation too, since
fObfuscated only means something when fEncrypted is set and otherwise MUST be
ignored (FibBase). nFib below 0x00C1, which is Word 6 and 95 and older, and the
FIB identifier 0xA5DC of Word 6 and 95 itself: skipped(unsupported_variant).
Every structure the specification does not allow
raises CorruptDocument, and that and every exception of olefile go through
ExtractionOutcome.from_exception, which keeps the class name and nothing else.

**The file is a stranger's.** olefile reads every chain in a loop of fixed
length, so a cycle cannot hang it, but it does not notice one either: a cycle
inside the declared length gives back repeated sectors as if they were the
stream. So the chains of both streams we read, and the chain of the mini stream
they may live in, are walked once more with a set of visited sectors, and a
sector seen twice is CorruptCompoundFile. Before olefile opens the file, the
declared number of FAT sectors is held against the size of the file: olefile
appends every FAT sector to an array by copying it, and measured on 0.47,
20 000 declared FAT sectors in a file of 180 kB cost 29 s before it reports
anything, growing with the square of the count. Both checks live in cfb.py
since plan 31-06, which holds the .xls reader to the same rules. Every offset and length from
the file is checked against the stream it points into before a byte is read,
the number of pieces is bounded by lcbClx, and reading ends at twice the
character cap (field codes go after reading, so the cap alone could leave a
document of field codes empty), after which the outcome is marked truncated.

The sniff in front of it all: many .doc files are not Word binary files at all
but RTF, Word's HTML export or a DOCX that was renamed (31-RESEARCH, pitfall
10). They go to the reader of what they are; anything else is
skipped(unsupported_variant).

This module does not log. Everything it reads is content of a user's file.
"""

from __future__ import annotations

import re
import struct
from itertools import pairwise
from pathlib import Path
from typing import Final, NamedTuple

import olefile

from findling import config
from findling.extract import cfb, office, text
from findling.extract.dispatch import cap_text
from findling.extract.errors import ExtractionOutcome, Reason, State

_OLE_SIGNATURE: Final = bytes.fromhex("d0cf11e0a1b11ae1")
_RTF_SIGNATURE: Final = b"{\\rtf"
_ZIP_SIGNATURE: Final = b"PK\x03\x04"
_UTF8_BOM: Final = b"\xef\xbb\xbf"
_SNIFF_BYTES: Final = 4096

_WORD_STREAM: Final = "WordDocument"

# [MS-DOC] 2.5.2 FibBase and 2.5.1 Fib.
_FIB_BASE_BYTES: Final = 32
_W_IDENT: Final = 0xA5EC
# The identifier of Word 6.0 and Word 95, which [MS-DOC] does not describe (it
# starts at Word 97). Measured on a real Word 6 file of an Office installation
# in the audit of plan 31-15 (finding M-31-02): wIdent 0xA5DC, nFib 0x0068, no
# table stream, fEncrypted at the same bit as in Word 97. Before the fix such a
# file was failed(corrupt), although the docstring and D-31-03 name it
# skipped(unsupported_variant).
_W_IDENT_WORD6: Final = 0xA5DC
_FLAGS_AT: Final = 0x0A
_F_ENCRYPTED: Final = 0x0100
_F_WHICH_TBL_STM: Final = 0x0200
_NFIB_WORD97: Final = 0x00C1
_CSW_AT: Final = 0x20
_CSW: Final = 0x000E
_CSLW_AT: Final = 0x3E
_CSLW: Final = 0x0016
_CB_RG_FC_LCB_AT: Final = 0x98
_CB_RG_FC_LCB_97: Final = 0x005D
_FC_CLX_AT: Final = 0x01A2  # lcbClx follows at 0x01A6

# [MS-DOC] 2.9.38 Clx, 2.9.209 Prc, 2.9.210 PrcData, 2.9.178 Pcdt, 2.8.35 PlcPcd.
_CLXT_PRC: Final = 0x01
_CLXT_PCDT: Final = 0x02
_MAX_CB_GRPPRL: Final = 0x3FA2
_CP_BYTES: Final = 4
_PCD_BYTES: Final = 8
_PCD_FC_AT: Final = 2

# [MS-DOC] 2.9.73 FcCompressed: bit 30 is fCompressed, bit 31 MUST be ignored.
_FC_COMPRESSED: Final = 0x40000000
_FC_MASK: Final = 0x3FFFFFFF

# The bytes of a compressed piece that are not Latin-1 (2.9.73), as escapes:
# the source of this repository is ASCII.
_SPECIAL_BYTES: Final = {
    0x82: "\u201a", 0x83: "\u0192", 0x84: "\u201e", 0x85: "\u2026", 0x86: "\u2020", 0x87: "\u2021",
    0x88: "\u02c6", 0x89: "\u2030", 0x8A: "\u0160", 0x8B: "\u2039", 0x8C: "\u0152", 0x91: "\u2018",
    0x92: "\u2019", 0x93: "\u201c", 0x94: "\u201d", 0x95: "\u2022", 0x96: "\u2013", 0x97: "\u2014",
    0x98: "\u02dc", 0x99: "\u2122", 0x9A: "\u0161", 0x9B: "\u203a", 0x9C: "\u0153", 0x9F: "\u0178",
}  # fmt: skip
_COMPRESSED_TABLE: Final = str.maketrans({chr(byte): char for byte, char in _SPECIAL_BYTES.items()})

# Field characters (2.8.25 Plcfld), split off with the text between them.
_FIELD_BEGIN: Final = "\x13"
_FIELD_SEPARATOR: Final = "\x14"
_FIELD_END: Final = "\x15"
_FIELD_MARKS: Final = re.compile("([\x13\x14\x15])")

# What the remaining control characters become: breaks, tabs, the hyphen, or
# nothing. Tab (0x09) and line feed (0x0A) stay as they are.
_KEPT_CONTROLS: Final = frozenset({0x09, 0x0A})
_CONTROL_TABLE: Final = str.maketrans(
    {
        **{chr(code): None for code in range(0x20) if code not in _KEPT_CONTROLS},
        "\r": "\n",
        "\x0b": "\n",
        "\x0c": "\n",
        "\x07": "\t",
        "\x1e": "-",
    }
)

# How much raw text is read for each character the cap allows (see above).
_RAW_PER_CAPPED_CHAR: Final = 2


class CorruptDocument(Exception):
    """A structure of the document or of its compound file that the specification does not allow."""


class _Fib(NamedTuple):
    table_stream: str
    fc_clx: int
    lcb_clx: int


def extract_msword(path: str) -> ExtractionOutcome:
    """A file under a Word name, sent to the reader of what its first bytes say it is."""
    with Path(path).open("rb") as handle:
        head = handle.read(_SNIFF_BYTES)
    if head.startswith(_OLE_SIGNATURE):
        return extract_doc(path)
    if head.startswith(_RTF_SIGNATURE):
        return text.extract_rtf(path)
    if head.startswith(_ZIP_SIGNATURE):
        return office.extract_docx(path)
    if head.removeprefix(_UTF8_BOM).lstrip().startswith(b"<"):
        return text.extract_html(path)
    return ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)


def extract_doc(path: str) -> ExtractionOutcome:
    """The text of a Word 97 to 2003 binary document, or a named verdict."""
    cap = config.settings().max_text_chars
    try:
        cfb.check_fat_size(path)
        with olefile.OleFileIO(path, raise_defects=olefile.DEFECT_INCORRECT) as ole:
            if not ole.exists(_WORD_STREAM):
                return ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)
            word = _read_stream(ole, _WORD_STREAM)
            fib = _read_fib(word)
            if isinstance(fib, ExtractionOutcome):
                return fib
            if not ole.exists(fib.table_stream):
                raise CorruptDocument
            table = _read_stream(ole, fib.table_stream)
        raw, complete = _piece_text(word, table, fib, cap * _RAW_PER_CAPPED_CHAR)
    except (OSError, ValueError, struct.error, RecursionError, CorruptDocument, cfb.CorruptCompoundFile) as error:
        return ExtractionOutcome.from_exception(error)

    outcome = cap_text(_visible(raw))
    if not complete and outcome.state is State.INDEXED and not outcome.truncated:
        return ExtractionOutcome.indexed(outcome.text, truncated=True)
    return outcome


def decode_compressed(raw: bytes) -> str:
    """The characters of a compressed piece: Latin-1 with the table of 2.9.73."""
    return raw.decode("latin-1").translate(_COMPRESSED_TABLE)


def _read_stream(ole: olefile.OleFileIO, name: str) -> bytes:
    """The bytes of a top level stream, after its sector chain was walked once."""
    data = ole.openstream(name).read()
    cfb.walk_stream(ole, name)
    return data


def _read_fib(word: bytes) -> _Fib | ExtractionOutcome:
    """The table stream and the Clx location, or the verdict the FibBase decides."""
    if len(word) < _FIB_BASE_BYTES:
        raise CorruptDocument
    w_ident, n_fib = struct.unpack_from("<HH", word, 0)
    (flags,) = struct.unpack_from("<H", word, _FLAGS_AT)
    if w_ident not in (_W_IDENT, _W_IDENT_WORD6):
        raise CorruptDocument
    if flags & _F_ENCRYPTED:
        return ExtractionOutcome.skipped(Reason.ENCRYPTED)
    if w_ident == _W_IDENT_WORD6 or n_fib < _NFIB_WORD97:
        return ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)
    if len(word) < _FC_CLX_AT + 8:
        raise CorruptDocument
    (csw,) = struct.unpack_from("<H", word, _CSW_AT)
    (cslw,) = struct.unpack_from("<H", word, _CSLW_AT)
    (cb_rg_fc_lcb,) = struct.unpack_from("<H", word, _CB_RG_FC_LCB_AT)
    if csw != _CSW or cslw != _CSLW or cb_rg_fc_lcb < _CB_RG_FC_LCB_97:
        raise CorruptDocument
    fc_clx, lcb_clx = struct.unpack_from("<II", word, _FC_CLX_AT)
    table_stream = "1Table" if flags & _F_WHICH_TBL_STM else "0Table"
    return _Fib(table_stream, fc_clx, lcb_clx)


def _plc_pcd(table: bytes, fib: _Fib) -> bytes:
    """The PlcPcd of the Clx, with every length checked against what holds it."""
    if fib.lcb_clx == 0 or fib.fc_clx + fib.lcb_clx > len(table):
        raise CorruptDocument
    clx = table[fib.fc_clx : fib.fc_clx + fib.lcb_clx]
    position = 0
    while position < len(clx) and clx[position] == _CLXT_PRC:
        if position + 3 > len(clx):
            raise CorruptDocument
        (cb_grpprl,) = struct.unpack_from("<h", clx, position + 1)
        if cb_grpprl < 0 or cb_grpprl > _MAX_CB_GRPPRL:
            raise CorruptDocument
        position += 3 + cb_grpprl
    if position + 5 > len(clx) or clx[position] != _CLXT_PCDT:
        raise CorruptDocument
    (lcb,) = struct.unpack_from("<I", clx, position + 1)
    plc = clx[position + 5 : position + 5 + lcb]
    if len(plc) != lcb or lcb < _CP_BYTES + _CP_BYTES + _PCD_BYTES or (lcb - _CP_BYTES) % (_CP_BYTES + _PCD_BYTES):
        raise CorruptDocument
    return plc


def _piece_text(word: bytes, table: bytes, fib: _Fib, budget: int) -> tuple[str, bool]:
    """The raw text of the pieces in CP order, at most ``budget`` characters.

    The flag says whether every piece was read in full.
    """
    plc = _plc_pcd(table, fib)
    count = (len(plc) - _CP_BYTES) // (_CP_BYTES + _PCD_BYTES)
    positions = struct.unpack_from(f"<{count + 1}I", plc, 0)
    if any(following <= current for current, following in pairwise(positions)):
        raise CorruptDocument
    pcd_at = (count + 1) * _CP_BYTES

    parts: list[str] = []
    for index in range(count):
        if budget == 0:
            return "".join(parts), False
        (fc,) = struct.unpack_from("<I", plc, pcd_at + index * _PCD_BYTES + _PCD_FC_AT)
        chars = positions[index + 1] - positions[index]
        take = min(chars, budget)
        parts.append(_one_piece(word, fc, chars, take))
        budget -= take
        if take < chars:
            return "".join(parts), False
    return "".join(parts), True


def _one_piece(word: bytes, fc: int, chars: int, take: int) -> str:
    """The first ``take`` of ``chars`` characters of one piece (2.4.1, 2.9.73)."""
    if fc & _FC_COMPRESSED:
        start = (fc & _FC_MASK) // 2
        if start + chars > len(word):
            raise CorruptDocument
        return decode_compressed(word[start : start + take])
    start = fc & _FC_MASK
    if start + 2 * chars > len(word):
        raise CorruptDocument
    return word[start : start + 2 * take].decode("utf-16-le", errors="replace")


def _visible(raw: str) -> str:
    """The text a reader sees: field instructions out, special characters mapped."""
    kept: list[str] = []
    # One entry per open field, True while it is still in its instructions.
    fields: list[bool] = []
    hidden = 0
    for part in _FIELD_MARKS.split(raw):
        if part == _FIELD_BEGIN:
            fields.append(True)
            hidden += 1
        elif part == _FIELD_SEPARATOR:
            if fields and fields[-1]:
                fields[-1] = False
                hidden -= 1
        elif part == _FIELD_END:
            if fields and fields.pop():
                hidden -= 1
        elif hidden == 0:
            kept.append(part)
    return "".join(kept).translate(_CONTROL_TABLE)
