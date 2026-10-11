"""Write the three Word 97 test documents of plan 31-05 with a local LibreOffice.

The .doc reader of FMT-03 is tested against files that a real writer of the
format produced, not only against bytes the tests assemble themselves: a reader
that only ever saw its own test builder would share every misreading of the
specification with it. LibreOffice is the writer at hand, it is free software,
and the content is own work (the search words are made up), so the outputs fall
under the "**" annotation of REUSE.toml like every other file of this tree.

What it does: it writes three small flat ODF text documents (.fodt) into a
temporary directory, lets ``soffice --headless --convert-to doc:"MS Word 97"``
turn each into a .doc, copies the results into backend/tests/fixtures/legacy/
and prints the SHA-256 of each. LibreOffice does not write the same bytes twice
(time stamps, ids), so the tests pin the digest of the committed file and not of
a fresh run; running this tool again means pinning the new digests.

The three sources and what each one is for:

- word97-latin: German text with umlauts, typographic quotes, the euro sign,
  a soft hyphen and a non-breaking hyphen. Search word "wortquendel".
- word97-unicode: Czech and Greek text, characters outside any 8 bit code page,
  so the writer has to store Unicode text. Search word "glyphquendel".
- word97-table-field: a table of two rows and two columns, a page number field
  and a fixed date field. Search word "zellquendel".

Security rule, carried unchanged from T-02-14: the tool writes its own sources
and reads nothing but what LibreOffice made of them. It never reads state.db,
never an index and never a user file.

A private LibreOffice profile in the temporary directory keeps the run away
from the profile of the desktop session (a lock file there makes soffice wait
silently) and from its settings.

Usage: make_legacy_fixtures.py [--soffice PATH] [--output DIR]
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

SOURCES = {
    "word97-latin": _LATIN,
    "word97-unicode": _UNICODE,
    "word97-table-field": _TABLE_FIELD,
}


def convert(soffice: Path, source: Path, work: Path) -> Path:
    """One .fodt to one .doc, with a private profile and a hard timeout."""
    profile = (work / "profile").as_uri()
    subprocess.run(  # noqa: S603  (fixed argument list, the path is the operator's)
        [
            str(soffice),
            f"-env:UserInstallation={profile}",
            "--headless",
            "--norestore",
            "--convert-to",
            "doc:MS Word 97",
            "--outdir",
            str(work / "out"),
            str(source),
        ],
        check=True,
        timeout=CONVERT_TIMEOUT_S,
        capture_output=True,
    )
    result = work / "out" / f"{source.stem}.doc"
    if not result.is_file():
        raise SystemExit(f"soffice wrote no {result.name}")
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--soffice", type=Path, default=DEFAULT_SOFFICE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name, body in SOURCES.items():
            source = work / f"{name}.fodt"
            source.write_text(_HEAD + body + _TAIL, encoding="utf-8")
            target = args.output / f"{name}.doc"
            shutil.copyfile(convert(args.soffice, source, work), target)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            print(f"{digest}  {target.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
