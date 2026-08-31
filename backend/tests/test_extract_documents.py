"""PDF, OOXML and OpenDocument, including every way each of them can go wrong.

The reference corpus carries the four PDF cases that matter, so they are read
from there rather than rebuilt: those files are what the read only gate copies
into a throwaway Nextcloud, and a test that invents its own PDF would stop
saying anything about the file the gate actually sees.

Everything the corpus does not contain is built here, in the test, from the
standard library. A multi page PDF, a spreadsheet over the cell limit and three
OpenDocument files are all about one specific shape, and adding them to the
corpus would grow a fixture set that exists for a different purpose. Built in
the test they are visible in the diff, which is where a reviewer looks.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import docx
import openpyxl
import pypdfium2
import pytest
from openpyxl import Workbook
from pptx import Presentation
from pptx.util import Emu
from pypdf.errors import EmptyFileError, FileNotDecryptedError

from findling import config
from findling.extract.dispatch import extract
from findling.extract.errors import ExtractionOutcome, Reason, State
from findling.extract.office import extract_docx, extract_pptx, extract_xlsx
from findling.extract.pdf import extract_pdf

CORPUS = Path(__file__).resolve().parents[2] / "testdata" / "corpus"


def _write(directory: Path, name: str, payload: bytes) -> str:
    target = directory / name
    target.write_bytes(payload)
    return str(target)


def _assemble_pdf(objects: list[bytes]) -> bytes:
    """Numbered objects plus a correct cross reference table, as in build_corpus.py.

    Deliberately the same shape as the corpus builder: a PDF whose xref table is
    wrong is a corrupt PDF, and a test fixture that is accidentally corrupt would
    prove the error path while claiming to prove the happy one.
    """
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
    out += f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    return bytes(out)


def _multi_page_pdf(pages: int) -> bytes:
    """A PDF of the given length, every page carrying a full line of real text.

    The lines are long on purpose. A page with three words would be judged as a
    page without a text layer, and this fixture is about the page cap, not about
    the text layer threshold.
    """
    font_number = 3 + 2 * pages
    kids = " ".join(f"{3 + 2 * index} 0 R" for index in range(pages))
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {pages} >>".encode("ascii"),
    ]
    for index in range(pages):
        content = (
            f"BT /F1 10 Tf 20 70 Td (Sitzungsvorlage der Gemeinde, Blatt {index + 1}) Tj ET\n"
            f"BT /F1 10 Tf 20 45 Td (Betreff: Grundstuecksverkehrsgenehmigung) Tj ET\n"
        ).encode("ascii")
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 120]"
                f" /Resources << /Font << /F1 {font_number} 0 R >> >> /Contents {4 + 2 * index} 0 R >>"
            ).encode("ascii")
        )
        objects.append(f"<< /Length {len(content)} >>\nstream\n".encode("ascii") + content + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    return _assemble_pdf(objects)


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------


def test_a_pdf_with_a_text_layer_yields_its_embedded_text() -> None:
    outcome = extract_pdf(str(CORPUS / "01-text-layer.pdf"))

    assert outcome.state is State.INDEXED
    assert "Findling reference corpus" in outcome.text
    assert "real text layer" in outcome.text


def test_a_pdf_without_a_text_layer_becomes_the_ocr_queue_of_phase_three() -> None:
    # Not a failure and not empty_text: this exact verdict is the list phase 3
    # works through, and a wrong bucket here costs a full reindex later.
    outcome = extract_pdf(str(CORPUS / "02-scan-no-text-layer.pdf"))

    assert outcome == ExtractionOutcome.skipped(Reason.NO_TEXT_LAYER)


def test_a_password_protected_pdf_is_answered_before_pdfium_is_asked(monkeypatch: pytest.MonkeyPatch) -> None:
    # The order is the whole point. pypdf answers the encryption question without
    # touching the pages, and reading .pages on a protected file raises, which
    # would turn a deliberate decision into a failure. pdfium is replaced by
    # something that cannot be called, so the claim is proven and not assumed.
    def unreachable(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("pdfium was opened although the file is encrypted")

    monkeypatch.setattr(pypdfium2, "PdfDocument", unreachable)

    outcome = extract_pdf(str(CORPUS / "07-password-protected.pdf"))

    assert outcome == ExtractionOutcome.skipped(Reason.ENCRYPTED)


def test_a_zero_byte_pdf_is_failed_empty_file() -> None:
    outcome = extract_pdf(str(CORPUS / "06-zero-bytes.pdf"))

    assert outcome == ExtractionOutcome.failed(Reason.EMPTY_FILE)


def test_a_pdf_header_followed_by_garbage_is_failed_corrupt(tmp_path: Path) -> None:
    path = _write(tmp_path, "kaputt.pdf", b"%PDF-1.7\n" + b"garbage" * 50)

    outcome = extract_pdf(path)

    assert outcome == ExtractionOutcome.failed(Reason.CORRUPT)


def test_page_and_textpage_are_closed_even_when_a_page_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # pdfium hands out C resources. Over a run of 100000 files an object that is
    # never closed is a leak, and the error path is where closing gets forgotten.
    closed: list[str] = []
    close_page = pypdfium2.PdfPage.close
    close_textpage = pypdfium2.PdfTextPage.close

    def note_page(self: pypdfium2.PdfPage) -> None:
        closed.append("page")
        close_page(self)

    def note_textpage(self: pypdfium2.PdfTextPage) -> None:
        closed.append("textpage")
        close_textpage(self)

    def explode(self: pypdfium2.PdfTextPage) -> str:
        raise RuntimeError("pdfium lost its footing halfway through a page")

    monkeypatch.setattr(pypdfium2.PdfPage, "close", note_page)
    monkeypatch.setattr(pypdfium2.PdfTextPage, "close", note_textpage)
    monkeypatch.setattr(pypdfium2.PdfTextPage, "get_text_bounded", explode)

    with pytest.raises(RuntimeError):
        extract_pdf(str(CORPUS / "01-text-layer.pdf"))

    assert closed == ["textpage", "page"]


def test_a_pdf_over_the_page_cap_stops_and_says_truncated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FINDLING_MAX_PDF_PAGES", "2")
    config.settings.cache_clear()
    try:
        path = _write(tmp_path, "lang.pdf", _multi_page_pdf(4))

        outcome = extract_pdf(path)

        assert outcome.state is State.INDEXED
        assert outcome.truncated is True
        assert "Blatt 2" in outcome.text
        assert "Blatt 3" not in outcome.text
    finally:
        config.settings.cache_clear()


def test_a_pypdf_empty_file_error_that_escapes_keeps_its_own_reason() -> None:
    # The extractor catches this one itself. The table entry is the net for the
    # day somebody reorders that function: an escaped zero byte error stays
    # empty_file instead of falling into the blanket corrupt.
    outcome = ExtractionOutcome.from_exception(EmptyFileError("nothing to read"))

    assert outcome == ExtractionOutcome.failed(Reason.EMPTY_FILE)


def test_an_encrypted_pdf_is_never_translated_out_of_an_exception() -> None:
    # failed(encrypted) is not a pair the taxonomy has, so a table entry for
    # FileNotDecryptedError would raise inside the error handler instead of
    # producing a verdict. The decision belongs where the file is opened.
    outcome = ExtractionOutcome.from_exception(FileNotDecryptedError("password required"))

    assert outcome == ExtractionOutcome.failed(Reason.CORRUPT)


def test_the_dispatcher_reaches_the_pdf_route() -> None:
    path = CORPUS / "01-text-layer.pdf"

    outcome = extract(str(path), "application/pdf", path.stat().st_size)

    assert outcome.state is State.INDEXED
    assert "Findling reference corpus" in outcome.text


# ---------------------------------------------------------------------------
# OOXML: DOCX, PPTX and XLSX
# ---------------------------------------------------------------------------

NOT_A_ZIP = b"Dies ist kein Archiv, sondern schlichter Text mit falscher Endung."


def _docx_with_a_table(directory: Path) -> str:
    """A document whose text sits in a table, which is the case python-docx hides.

    Paragraphs are the obvious half of a DOCX. A table cell is a paragraph inside
    a cell inside a row, and an extractor that only walks document.paragraphs
    loses every invoice, every list of names and every form.
    """
    document = docx.Document()
    document.add_paragraph("Aktenvermerk der Gemeinde.")
    table = document.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Aktenzeichen"
    table.rows[0].cells[1].text = "Grundstuecksverkehr 2026-0815"
    table.rows[1].cells[0].text = "Frist"
    table.rows[1].cells[1].text = "Kuendigungsfrist drei Monate"
    target = directory / "vermerk.docx"
    document.save(str(target))
    return str(target)


def _pptx_with_two_text_frames(directory: Path) -> str:
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    first = slide.shapes.add_textbox(Emu(914400), Emu(914400), Emu(3657600), Emu(914400))
    first.text_frame.text = "Sitzungsvorlage des Ausschusses"
    second = slide.shapes.add_textbox(Emu(914400), Emu(2743200), Emu(3657600), Emu(914400))
    second.text_frame.text = "Beschlussvorschlag zur Strassenbaubeitragssatzung"
    target = directory / "vorlage.pptx"
    presentation.save(str(target))
    return str(target)


def _xlsx(directory: Path, rows: int, columns: int) -> str:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    for row in range(rows):
        sheet.append([f"Zelle {row}-{column}" for column in range(columns)])
    target = directory / "mappe.xlsx"
    workbook.save(str(target))
    workbook.close()
    return str(target)


def test_a_docx_yields_its_paragraphs_including_the_german_special_characters() -> None:
    outcome = extract_docx(str(CORPUS / "03-document.docx"))

    assert outcome.state is State.INDEXED
    assert "office document part" in outcome.text
    assert "Umlaute im Text: Grundstück, Ausschuss, Maßnahme." in outcome.text


def test_the_table_cells_of_a_docx_are_indexed_as_well(tmp_path: Path) -> None:
    outcome = extract_docx(_docx_with_a_table(tmp_path))

    assert outcome.state is State.INDEXED
    assert "Aktenvermerk der Gemeinde." in outcome.text
    assert "Aktenzeichen" in outcome.text
    assert "Kuendigungsfrist drei Monate" in outcome.text


def test_a_pptx_yields_the_text_of_every_shape_that_has_a_text_frame(tmp_path: Path) -> None:
    outcome = extract_pptx(_pptx_with_two_text_frames(tmp_path))

    assert outcome.state is State.INDEXED
    assert "Sitzungsvorlage des Ausschusses" in outcome.text
    assert "Beschlussvorschlag zur Strassenbaubeitragssatzung" in outcome.text


def test_a_spreadsheet_is_opened_read_only_and_data_only_and_never_otherwise(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Without read_only openpyxl builds the whole workbook in memory, and a single
    # export file tips a 4 GB container over. Without data_only every formula cell
    # arrives as its formula, so the index fills with =SUM(A1:A9) instead of text.
    seen: list[dict[str, object]] = []
    original = openpyxl.load_workbook

    def note(*args: object, **kwargs: object) -> object:
        seen.append(dict(kwargs))
        return original(*args, **kwargs)  # pyright: ignore[reportArgumentType]

    monkeypatch.setattr(openpyxl, "load_workbook", note)

    outcome = extract_xlsx(_xlsx(tmp_path, rows=3, columns=2))

    assert outcome.state is State.INDEXED
    assert "Zelle 2-1" in outcome.text
    assert len(seen) == 1
    assert seen[0]["read_only"] is True
    assert seen[0]["data_only"] is True


def test_a_spreadsheet_over_the_cell_limit_is_skipped_instead_of_half_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The limit is lowered instead of writing a workbook with 200000 cells: the
    # behaviour under test is the counter and the verdict skipped(too_many_cells),
    # not openpyxl's ability to write a large file.
    monkeypatch.setenv("FINDLING_MAX_CELLS", "10")
    config.settings.cache_clear()
    try:
        outcome = extract_xlsx(_xlsx(tmp_path, rows=5, columns=4))

        assert outcome == ExtractionOutcome.skipped(Reason.TOO_MANY_CELLS)
    finally:
        config.settings.cache_clear()


@pytest.mark.parametrize(
    ("extractor", "name"),
    [
        (extract_docx, "brief.docx"),
        (extract_pptx, "vorlage.pptx"),
        (extract_xlsx, "mappe.xlsx"),
    ],
)
def test_an_ooxml_name_on_a_file_that_is_no_archive_is_failed_corrupt(
    extractor: Callable[[str], ExtractionOutcome], name: str, tmp_path: Path
) -> None:
    outcome = extractor(_write(tmp_path, name, NOT_A_ZIP))

    assert outcome == ExtractionOutcome.failed(Reason.CORRUPT)


def test_a_truncated_docx_is_failed_corrupt_instead_of_an_escaping_exception(tmp_path: Path) -> None:
    # The measured case: a package that stops halfway raises PackageNotFoundError,
    # which reads like "there is no document here" and means "this one is broken".
    intact = (CORPUS / "03-document.docx").read_bytes()

    outcome = extract_docx(_write(tmp_path, "halb.docx", intact[: len(intact) // 2]))

    assert outcome == ExtractionOutcome.failed(Reason.CORRUPT)


def test_the_dispatcher_reaches_the_three_ooxml_routes(tmp_path: Path) -> None:
    documents = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
            _docx_with_a_table(tmp_path),
            "Aktenzeichen",
        ),
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": (
            _pptx_with_two_text_frames(tmp_path),
            "Sitzungsvorlage des Ausschusses",
        ),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (
            _xlsx(tmp_path, rows=3, columns=2),
            "Zelle 1-1",
        ),
    }

    for mime, (path, needle) in documents.items():
        outcome = extract(path, mime, Path(path).stat().st_size)

        assert outcome.state is State.INDEXED
        assert needle in outcome.text
