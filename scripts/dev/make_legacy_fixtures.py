"""Write the Word 97 and Excel 97 test files of plans 31-05 and 31-06 with LibreOffice.

The .doc reader of FMT-03 is tested against files that a real writer of the
format produced, not only against bytes the tests assemble themselves: a reader
that only ever saw its own test builder would share every misreading of the
specification with it. LibreOffice is the writer at hand, it is free software,
and the content is own work (the search words are made up), so the outputs fall
under the "**" annotation of REUSE.toml like every other file of this tree.

What it does: it writes small flat ODF documents (.fodt for text, .fods for
spreadsheets) into a temporary directory, lets ``soffice --headless
--convert-to`` turn each into a .doc ("MS Word 97") or an .xls ("MS Excel 97",
BIFF8), copies the results into backend/tests/fixtures/legacy/ and prints the
SHA-256 of each. LibreOffice does not write the same bytes twice
(time stamps, ids), so the tests pin the digest of the committed file and not of
a fresh run; running this tool again means pinning the new digests.

The three sources and what each one is for:

- word97-latin: German text with umlauts, typographic quotes, the euro sign,
  a soft hyphen and a non-breaking hyphen. Search word "wortquendel".
- word97-unicode: Czech and Greek text, characters outside any 8 bit code page,
  so the writer has to store Unicode text. Search word "glyphquendel".
- word97-table-field: a table of two rows and two columns, a page number field
  and a fixed date field. Search word "zellquendel".
- biff8-values (plan 31-06, FMT-04): two sheets. The first holds a text with
  "zellquendel", the whole number 3, the number 2.5, a date, an empty cell and
  an error cell (1/0); the second, named "geheimblatt", holds the text
  "blattquendel", so a test can look for the sheet name in the log.
- biff8-far-cell (plan 31-06): a single cell at row 65000, column 200 (counted
  from 1) with "fernquendel", the file that turns xlrd's padding of rows into
  millions of entries unless ragged_rows is on.
- word97-ole-seed (plan 31-12, FMT-06): a short Word 97 document with
  "hullequendel". The upgrade proof of deploy-harp.yml sows it under a .docx
  name (.github/fixtures/upgrade-seed-formats/seed-ole-under-docx.docx, a byte
  for byte copy), where 1.4.2 books it as skipped(legacy_format) and 1.5 reads
  it with the .doc reader.

``--only doc`` or ``--only xls`` writes one family alone, so the digests of the
other one stay where they are. ``--name word97-ole-seed`` writes one source
alone, for the same reason.

Security rule, carried unchanged from T-02-14: the tool writes its own sources
and reads nothing but what LibreOffice made of them. It never reads state.db,
never an index and never a user file.

A private LibreOffice profile in the temporary directory keeps the run away
from the profile of the desktop session (a lock file there makes soffice wait
silently) and from its settings.

Usage: make_legacy_fixtures.py [--soffice PATH] [--output DIR] [--only doc|xls] [--name SOURCE]
"""

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOFFICE = Path(r"C:\Program Files\LibreOffice\program\soffice.exe")
DEFAULT_OUTPUT = REPO_ROOT / "backend" / "tests" / "fixtures" / "legacy"

# One conversion of a tiny document takes a few seconds; a minute means that
# soffice is waiting for something that will not come.
CONVERT_TIMEOUT_S = 120

_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
    ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"'
    ' xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"'
    ' xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"'
    ' office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">\n'
    "<office:body><office:text>\n"
)
_TAIL = "</office:text></office:body></office:document>\n"

_SHEET_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
    ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"'
    ' xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"'
    ' xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"'
    ' xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"'
    ' xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2"'
    ' office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.spreadsheet">\n'
    "<office:automatic-styles>"
    '<number:date-style style:name="N1">'
    '<number:year number:style="long"/><number:text>-</number:text>'
    '<number:month number:style="long"/><number:text>-</number:text>'
    '<number:day number:style="long"/>'
    "</number:date-style>"
    '<style:style style:name="ce1" style:family="table-cell" style:data-style-name="N1"/>'
    "</office:automatic-styles>\n"
    "<office:body><office:spreadsheet>\n"
)
_SHEET_TAIL = "</office:spreadsheet></office:body></office:document>\n"


def _text_cell(value: str) -> str:
    return f'<table:table-cell office:value-type="string"><text:p>{value}</text:p></table:table-cell>'


def _row(*cells: str) -> str:
    return "<table:table-row>" + "".join(cells) + "</table:table-row>"


_VALUES = (
    '<table:table table:name="Daten">'
    + _row(_text_cell("Das zellquendel steht im ersten Blatt."))
    + _row('<table:table-cell office:value-type="float" office:value="3"><text:p>3</text:p></table:table-cell>')
    + _row('<table:table-cell office:value-type="float" office:value="2.5"><text:p>2.5</text:p></table:table-cell>')
    + _row(
        '<table:table-cell table:style-name="ce1" office:value-type="date" office:date-value="2024-03-15">'
        "<text:p>2024-03-15</text:p></table:table-cell>"
    )
    + _row("<table:table-cell/>", _text_cell("neben der leeren Zelle"))
    + _row('<table:table-cell table:formula="of:=1/0"/>')
    + "</table:table>\n"
    + '<table:table table:name="geheimblatt">'
    + _row(_text_cell("Das blattquendel steht im zweiten Blatt."))
    + "</table:table>\n"
)

# Row 65000 and column 200, counted from 1: 64999 empty rows, then 199 empty
# cells before the one with a value. Both repeats are how ODF writes a gap.
_FAR_CELL = (
    '<table:table table:name="Weit">'
    '<table:table-row table:number-rows-repeated="64999"><table:table-cell/></table:table-row>'
    + _row('<table:table-cell table:number-columns-repeated="199"/>', _text_cell("fernquendel"))
    + "</table:table>\n"
)

# Non-ASCII characters stand as escapes: the code of this repository is ASCII.
# U+00AD is the soft hyphen, U+2011 the non-breaking hyphen, U+201E and U+201C
# the German quotes, U+2018 and U+2019 the single ones, U+20AC the euro sign.
_LATIN = (
    "<text:p>Das wortquendel steht in einem Brief mit herzlichen Gr\u00fc\u00dfen.</text:p>\n"
    "<text:p>\u201eZitat\u201c und \u2018einfach\u2019, Preis 42 \u20ac, "
    "\u00e4\u00f6\u00fc \u00c4\u00d6\u00dc \u00df.</text:p>\n"
    "<text:p>Silben\u00adtrennung und Bindestrich\u2011fest.</text:p>\n"
)

# Czech (with the caron letters of the 1.4 language work) and Greek.
_UNICODE = (
    "<text:p>Das glyphquendel in fremden Schriften.</text:p>\n"
    "<text:p>P\u0159\u00edli\u0161 \u017elu\u0165ou\u010dk\u00fd k\u016f\u0148 "
    "\u00fap\u011bl \u010f\u00e1belsk\u00e9 \u00f3dy.</text:p>\n"
    "<text:p>\u039a\u03b1\u03bb\u03b7\u03bc\u03ad\u03c1\u03b1 \u03ba\u03cc\u03c3\u03bc\u03b5.</text:p>\n"
)

_TABLE_FIELD = (
    "<text:p>Das zellquendel steht vor der Tabelle.</text:p>\n"
    '<table:table table:name="Tabelle1">'
    '<table:table-column table:number-columns-repeated="2"/>'
    "<table:table-row>"
    '<table:table-cell office:value-type="string"><text:p>Apfel</text:p></table:table-cell>'
    '<table:table-cell office:value-type="string"><text:p>Birne</text:p></table:table-cell>'
    "</table:table-row>"
    "<table:table-row>"
    '<table:table-cell office:value-type="string"><text:p>Kirsche</text:p></table:table-cell>'
    '<table:table-cell office:value-type="string"><text:p>Pflaume</text:p></table:table-cell>'
    "</table:table-row>"
    "</table:table>\n"
    '<text:p>Seite <text:page-number text:select-page="current">1</text:page-number> von hier.</text:p>\n'
    '<text:p>Stand <text:date text:fixed="true" text:date-value="2026-10-11">11.10.2026</text:date>'
    " ist fest.</text:p>\n"
)

# The seed of the upgrade proof (plan 31-12). One word that stands in no other
# file of the repository, so a hit in the upgrade proof names exactly this file.
_OLE_SEED = (
    "<text:p>Das hullequendel steht in einem alten Word-Dokument.</text:p>\n"
    "<text:p>Es tr\u00e4gt den Namen eines neuen, und das ist der ganze Trick.</text:p>\n"
)

# Per family: suffix of the source, its head and tail, the conversion filter of
# soffice and the suffix of the result.
_FAMILIES = {
    "doc": (".fodt", _HEAD, _TAIL, "doc:MS Word 97", ".doc"),
    "xls": (".fods", _SHEET_HEAD, _SHEET_TAIL, "xls:MS Excel 97", ".xls"),
}

SOURCES = {
    "word97-latin": ("doc", _LATIN),
    "word97-unicode": ("doc", _UNICODE),
    "word97-table-field": ("doc", _TABLE_FIELD),
    "biff8-values": ("xls", _VALUES),
    "biff8-far-cell": ("xls", _FAR_CELL),
    "word97-ole-seed": ("doc", _OLE_SEED),
}


def convert(soffice: Path, source: Path, work: Path, target_filter: str, suffix: str) -> Path:
    """One flat ODF source to one legacy file, with a private profile and a hard timeout."""
    profile = (work / "profile").as_uri()
    subprocess.run(  # noqa: S603  (fixed argument list, the path is the operator's)
        [
            str(soffice),
            f"-env:UserInstallation={profile}",
            "--headless",
            "--norestore",
            "--convert-to",
            target_filter,
            "--outdir",
            str(work / "out"),
            str(source),
        ],
        check=True,
        timeout=CONVERT_TIMEOUT_S,
        capture_output=True,
    )
    result = work / "out" / f"{source.stem}{suffix}"
    if not result.is_file():
        raise SystemExit(f"soffice wrote no {result.name}")
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--soffice", type=Path, default=DEFAULT_SOFFICE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--only", choices=sorted(_FAMILIES), default=None)
    parser.add_argument("--name", choices=sorted(SOURCES), default=None)
    args = parser.parse_args(argv)

    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name, (family, body) in SOURCES.items():
            if args.only is not None and family != args.only:
                continue
            if args.name is not None and name != args.name:
                continue
            source_suffix, head, tail, target_filter, suffix = _FAMILIES[family]
            source = work / f"{name}{source_suffix}"
            source.write_text(head + body + tail, encoding="utf-8")
            target = args.output / f"{name}{suffix}"
            shutil.copyfile(convert(args.soffice, source, work, target_filter, suffix), target)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            print(f"{digest}  {target.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
