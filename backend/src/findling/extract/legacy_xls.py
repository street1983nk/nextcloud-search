"""Excel 97 to 2003 workbooks (.xls), read with xlrd under the cell limit of XLSX.

FMT-04. A .xls of Excel 5 to 2003 is a compound file (OLE2, [MS-CFB]) with a
stream called ``Workbook`` (BIFF8) or ``Book`` (BIFF5) of BIFF records. xlrd
2.0.2 reads them; since 2.0 it reads nothing else, which is what we want from a
library that sees a stranger's file.

**The same limit as XLSX.** Cells are counted against settings().max_cells and a
workbook over it ends as skipped(too_many_cells), the verdict extract_xlsx
gives: half a workbook in the index looks like a whole one. The rule of the
count is the same in both readers: every cell the library hands over counts,
empty ones included. What they hand over differs. openpyxl in read only mode
pads every row to the width of the sheet and yields the empty rows in between,
so it counts the rectangle of the sheet; xlrd with ragged rows hands over each
row up to its last cell with a value and an empty row as nothing. A single
value at row 65000, column 200 is 13 million cells to extract_xlsx and 200 to
this reader (measured on the same source converted both ways, plan 31-06). The
limit guards the index and the work per file, and the work here is what xlrd
built.

**ragged_rows=True is not tuning.** Without it xlrd pads every row to the
widest one while it reads (put_cell_unragged, sheet.py), and that one far cell
becomes 13 million list entries before the first one is counted. With it the
same file costs a few megabytes (test with tracemalloc).

**The honest limit.** xlrd parses a whole sheet before nrows is known, so the
cell limit protects the index, not the memory of one huge sheet: that is held by
RLIMIT_AS of the extraction child, which ends it as failed(out_of_memory).
on_demand loads one sheet at a time and unload_sheet lets it go again.

**Values as extract_xlsx writes them.** Text as it is; numbers through repr with
a trailing ".0" removed, so the whole number 3 is "3" as openpyxl gives it and a
large one keeps the exponent openpyxl reads from the XML; dates as
str(datetime); booleans as True and False; error cells as their text (#DIV/0!),
which is what openpyxl returns for them. Empty cells and sheet names give
nothing.

**Named verdicts (D-31-03).** A FILEPASS record: xlrd raises "Workbook is
encrypted", which is skipped(encrypted). A BOF that names no BIFF version xlrd
reads, a workspace file or a stream that does not start with a BOF: xlrd's
messages begin with "BIFF version", "Can't determine file's BIFF version" or
"Unsupported format", and that is skipped(unsupported_variant). A compound file
with neither stream is skipped(unsupported_variant) too. Everything else xlrd
raises becomes ExtractionOutcome.from_exception, which keeps the class name and
nothing else: xlrd's messages quote sheet names.

**The compound file is a stranger's (Befund 9).** xlrd reads the compound file
with a reader of its own, and that reader has a hole: a chain in the mini
stream is followed without a record of the sectors seen, until a negative
sector number, so a cycle there is a loop without end, and a chain that runs on
past the length of its stream the same. A sector number past the end of the file
is an IndexError deep inside it. So before xlrd opens the file, cfb.py checks
it the way it checks a .doc: the FAT size against the file size, then olefile
(which follows the DIFAT with a check for cycles), then the chain of the stream
xlrd will read, once, with a set of visited sectors, against the size of the
file, and to its ENDOFCHAIN. A defect there is failed(corrupt).

The sniff in front of it all: a file under an Excel name is often not a BIFF
workbook but an XLSX that was renamed, an HTML table or an XML Spreadsheet 2003
that Excel saves with the old extension, or a CSV export. They go to the reader
of what they are; bytes that are none of these are skipped(unsupported_variant).

This module does not log, and xlrd writes into a sink: everything it would say
is about the content of a user's file.
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Final, Literal

import olefile
import xlrd
from xlrd.biffh import XLRDError
from xlrd.compdoc import CompDocError

from findling import config
from findling.extract import cfb, office, text
from findling.extract.dispatch import cap_text
from findling.extract.errors import ExtractionOutcome, Reason, State

_OLE_SIGNATURE: Final = bytes.fromhex("d0cf11e0a1b11ae1")
_ZIP_SIGNATURE: Final = b"PK\x03\x04"
_UTF8_BOM: Final = b"\xef\xbb\xbf"
_SNIFF_BYTES: Final = 4096

# The two stream names, in the order xlrd asks for them (book.py).
_WORKBOOK_STREAMS: Final = ("Workbook", "Book")

# The fixed messages of xlrd 2.0.2 (book.py) that name a verdict. They carry no
# content of the file at their start; the rest of a message is never read.
_ENCRYPTED: Final = "Workbook is encrypted"
_VARIANT_PREFIXES: Final = ("BIFF version", "Can't determine file's BIFF version", "Unsupported format")

# What xlrd raises for a file it cannot read. Besides its own two classes it
# checks structures with assert and indexes tables with numbers from the file.
_XLRD_FAILURES: Final = (
    XLRDError,
    CompDocError,
    AssertionError,
    IndexError,
    KeyError,
    ValueError,
    struct.error,
)

# What the checks in front of xlrd raise for a broken compound file.
_CONTAINER_FAILURES: Final = (OSError, ValueError, struct.error, RecursionError, cfb.CorruptCompoundFile)


def extract_msexcel(path: str) -> ExtractionOutcome:
    """A file under an Excel name, sent to the reader of what its first bytes say it is."""
    with Path(path).open("rb") as handle:
        head = handle.read(_SNIFF_BYTES)
    if head.startswith(_OLE_SIGNATURE):
        return extract_xls(path)
    if head.startswith(_ZIP_SIGNATURE):
        return office.extract_xlsx(path)
    if head.removeprefix(_UTF8_BOM).lstrip().startswith(b"<"):
        return text.extract_html(path)
    outcome = text.extract_plain(path)
    if outcome.state is State.INDEXED:
        return outcome
    return ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)


def extract_xls(path: str) -> ExtractionOutcome:
    """The cell values of every sheet of a BIFF workbook, or a named verdict."""
    try:
        if not _checked_workbook(path):
            return ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)
    except _CONTAINER_FAILURES as error:
        return ExtractionOutcome.from_exception(error)

    try:
        book = xlrd.open_workbook(path, on_demand=True, formatting_info=False, ragged_rows=True, logfile=_SINK)
    except _XLRD_FAILURES as error:
        return _verdict(error)
    try:
        return _read_book(book, config.settings().max_cells)
    except _XLRD_FAILURES as error:
        return _verdict(error)
    finally:
        book.release_resources()


class _Sink:
    """xlrd's logfile: takes every write and keeps nothing.

    An object in memory rather than os.devnull, because opening a file for
    writing in the extraction path is what the file travel gate counts
    (test_extract_edge_paths), and a sink needs no file to be one.
    """

    def write(self, data: str) -> int:
        return len(data)


_SINK: Final = _Sink()


def _checked_workbook(path: str) -> bool:
    """Check the compound file before xlrd sees it; False when it holds no workbook.

    Every one of the two streams that exists is walked, because xlrd reads
    Workbook first and falls back to Book only when that comes back empty.
    """
    cfb.check_fat_size(path)
    with olefile.OleFileIO(path, raise_defects=olefile.DEFECT_INCORRECT) as ole:
        present = [name for name in _WORKBOOK_STREAMS if ole.exists(name)]
        for name in present:
            cfb.walk_stream(ole, name)
        return any(ole.get_size(name) > 0 for name in present)


def _verdict(error: Exception) -> ExtractionOutcome:
    """skipped for the two xlrd messages that name a property of the file, else from_exception."""
    if isinstance(error, XLRDError):
        message = str(error)
        if message == _ENCRYPTED:
            return ExtractionOutcome.skipped(Reason.ENCRYPTED)
        if message.startswith(_VARIANT_PREFIXES):
            return ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)
    return ExtractionOutcome.from_exception(error)


def _read_book(book: xlrd.Book, limit: int) -> ExtractionOutcome:
    """Every sheet, one at a time, with the cells counted as extract_xlsx counts them."""
    parts: list[str] = []
    seen = 0
    for index in range(book.nsheets):
        sheet = book.sheet_by_index(index)
        for row in range(sheet.nrows):
            values = sheet.row_values(row)
            seen += len(values)
            if seen > limit:
                # Stop here rather than deliver half a workbook, as extract_xlsx does.
                return ExtractionOutcome.skipped(Reason.TOO_MANY_CELLS)
            types = sheet.row_types(row)
            parts += [_cell_text(kind, value, book.datemode) for kind, value in zip(types, values, strict=True)]
        book.unload_sheet(index)
    return cap_text("\n".join(part for part in parts if part.strip()))


def _cell_text(kind: int, value: object, datemode: Literal[0, 1]) -> str:
    """One cell as extract_xlsx would write the same cell of an XLSX (see above)."""
    if kind == xlrd.XL_CELL_TEXT and isinstance(value, str):
        return value
    if kind == xlrd.XL_CELL_NUMBER and isinstance(value, float):
        return _number(value)
    if kind == xlrd.XL_CELL_DATE and isinstance(value, float):
        try:
            return str(xlrd.xldate_as_datetime(value, datemode))
        except (xlrd.xldate.XLDateError, OverflowError, ValueError):
            # A date format on a number no calendar has: the number is the value.
            return _number(value)
    if kind == xlrd.XL_CELL_BOOLEAN:
        return str(bool(value))
    if kind == xlrd.XL_CELL_ERROR and isinstance(value, int):
        return xlrd.error_text_from_code.get(value, "")
    return ""


def _number(value: float) -> str:
    """repr without a trailing ".0": 3.0 is "3", 2.5 stays, 1e+20 keeps its exponent."""
    return repr(value).removesuffix(".0")
