"""FMT-04: Excel 97 to 2003 workbooks (.xls), read with xlrd and the cell limit of XLSX.

Three kinds of input. The two files under fixtures/legacy were written by
LibreOffice 26.2 from own content (scripts/dev/make_legacy_fixtures.py, origin
in fixtures/legacy/README.md); their digests are pinned below. Encrypted and
unknown variants are BIFF records written here from [MS-XLS] 2.4.21 BOF and
2.4.117 FilePass into a compound file of conftest.build_cfb. The broken sector
chains of Befund 9 are built with conftest.build_cfb and cfb_with_difat or
patched into the LibreOffice file, whose Workbook stream lives in the mini
stream.

Every test of a broken chain runs the reader in a child process: a hang then
fails the test after a generous deadline instead of stopping the suite, and
the child measures the reader alone with time.monotonic against 5 s. Each one
has a control next to it: the same file without the defect is read.
"""

from __future__ import annotations

import hashlib
import io
import multiprocessing
import os
import queue
import struct
import subprocess
import sys
import threading
import time
import tracemalloc
from pathlib import Path
from typing import Any

import olefile
import openpyxl
import pytest

from conftest import CFB_END_OF_CHAIN, build_cfb, cfb_with_difat
from findling.config import settings
from findling.extract.errors import ExtractionOutcome, Reason, State
from findling.extract.legacy_xls import extract_msexcel, extract_xls

FIXTURES = Path(__file__).parent / "fixtures" / "legacy"
BACKEND = Path(__file__).resolve().parents[1]

# SHA-256 of the committed files. LibreOffice does not write the same bytes twice,
# so a new run of the fixture tool means new digests here, on purpose.
FIXTURE_DIGESTS = {
    "biff8-values.xls": "77c04f4d82efe8ca60ea9ec442f3b59ccc5bd872d1663bcb5ea0edabb65c7b48",
    "biff8-far-cell.xls": "eeb1697c38f926ba5d979a280fa48d8dc647e8d4eec50ea83ec226fea91aa4fb",
}

# What extract_xlsx returns for the same .fods source converted to .xlsx by the
# same LibreOffice (measured once in plan 31-06): whole numbers without ".0",
# the date as str(datetime), the error cell as its text, no sheet names.
VALUES_TEXT = (
    "Das zellquendel steht im ersten Blatt.\n"
    "3\n"
    "2.5\n"
    "2024-03-15 00:00:00\n"
    "neben der leeren Zelle\n"
    "#DIV/0!\n"
    "Das blattquendel steht im zweiten Blatt."
)
# Cells xlrd hands over for biff8-values.xls with ragged rows: one per row of the
# first sheet, two in the row with the empty cell, one in the second sheet.
VALUES_CELLS = 8

TIME_LIMIT_S = 5.0
# How long the parent waits for the child at all. Starting a spawned child and
# importing this module takes seconds on its own; the 5 s are measured inside.
CHILD_DEADLINE_S = 30.0
# A child still busy after this ends itself (see _extract_in_child).
HANG_EXIT_AFTER_S = 2 * TIME_LIMIT_S
HANG_EXIT_CODE = 3
FAR_CELL_PEAK_BYTES = 50 * 1024 * 1024

# [MS-XLS] 2.4.21 BOF, 2.4.117 FilePass, 2.4.103 EOF.
_BOF = 0x0809
_FILEPASS = 0x002F
_EOF = 0x000A
_BIFF8 = 0x0600
_GLOBALS = 0x0005
_WORKSPACE = 0x0100


def _record(code: int, data: bytes) -> bytes:
    return struct.pack("<HH", code, len(data)) + data


def _bof(version: int = _BIFF8, stream_type: int = _GLOBALS) -> bytes:
    # vers, dt, rupBuild, rupYear, then bfh and sfo as two 32 bit fields.
    return _record(_BOF, struct.pack("<4H2I", version, stream_type, 0x0DBB, 0x07CC, 0, 0x0206))


def _write(tmp_path: Path, payload: bytes, name: str = "tabelle.xls") -> str:
    path = tmp_path / name
    path.write_bytes(payload)
    return str(path)


def _fixture(name: str) -> str:
    return str(FIXTURES / name)


def _workbook_stream() -> bytes:
    with olefile.OleFileIO(_fixture("biff8-values.xls")) as ole:
        return ole.openstream("Workbook").read()


def _with_cells(monkeypatch: pytest.MonkeyPatch, limit: int) -> None:
    monkeypatch.setenv("FINDLING_MAX_CELLS", str(limit))
    settings.cache_clear()


@pytest.fixture(autouse=True)
def _fresh_settings() -> Any:
    settings.cache_clear()
    yield
    settings.cache_clear()


# --- the LibreOffice files ---------------------------------------------------


@pytest.mark.parametrize(("name", "digest"), sorted(FIXTURE_DIGESTS.items()))
def test_every_fixture_is_the_committed_file(name: str, digest: str) -> None:
    assert hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest() == digest


def test_values_dates_and_both_sheets_read_like_xlsx() -> None:
    outcome = extract_xls(_fixture("biff8-values.xls"))

    assert outcome == ExtractionOutcome.indexed(VALUES_TEXT)


def test_a_whole_number_has_no_decimal_point() -> None:
    lines = extract_xls(_fixture("biff8-values.xls")).text.splitlines()

    assert "3" in lines
    assert "3.0" not in lines


def test_the_cell_limit_of_xlsx_holds_for_xls(monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cells(monkeypatch, 3)

    assert extract_xls(_fixture("biff8-values.xls")) == ExtractionOutcome.skipped(Reason.TOO_MANY_CELLS)


def test_a_workbook_with_exactly_the_limit_is_read(monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cells(monkeypatch, VALUES_CELLS)
    assert extract_xls(_fixture("biff8-values.xls")).state is State.INDEXED

    _with_cells(monkeypatch, VALUES_CELLS - 1)
    assert extract_xls(_fixture("biff8-values.xls")) == ExtractionOutcome.skipped(Reason.TOO_MANY_CELLS)


def test_one_far_cell_costs_no_millions_of_entries() -> None:
    # Without ragged rows xlrd pads every row to the widest one: 65000 rows of
    # 200 cells, 13 million entries for one value (31-RESEARCH, pitfall 9).
    tracemalloc.start()
    try:
        started = time.monotonic()
        outcome = extract_xls(_fixture("biff8-far-cell.xls"))
        elapsed = time.monotonic() - started
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert outcome == ExtractionOutcome.indexed("fernquendel")
    assert peak < FAR_CELL_PEAK_BYTES
    assert elapsed < TIME_LIMIT_S


# --- verdicts from the BIFF records ------------------------------------------


@pytest.mark.parametrize("stream", ["Workbook", "Book"])
def test_a_filepass_record_is_encrypted(tmp_path: Path, stream: str) -> None:
    workbook = _bof() + _record(_FILEPASS, struct.pack("<3H", 1, 1, 1) + bytes(48)) + _record(_EOF, b"")
    path = _write(tmp_path, build_cfb([], streams={stream: workbook}))

    assert extract_xls(path) == ExtractionOutcome.skipped(Reason.ENCRYPTED)


@pytest.mark.parametrize(
    "workbook",
    [_bof(version=0x1234), _bof(stream_type=_WORKSPACE), b"\x00\x01kein BOF"],
    ids=["unknown-biff-version", "workspace", "no-bof"],
)
def test_a_variant_xlrd_does_not_read_is_unsupported(tmp_path: Path, workbook: bytes) -> None:
    path = _write(tmp_path, build_cfb([], streams={"Workbook": workbook}))

    assert extract_xls(path) == ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)


def test_a_compound_file_without_a_workbook_is_unsupported(tmp_path: Path) -> None:
    path = _write(tmp_path, build_cfb([], streams={"Inhalt": b"kein Arbeitsblatt"}))

    assert extract_xls(path) == ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)


def test_a_failure_names_the_class_and_nothing_of_the_sheet(tmp_path: Path) -> None:
    # Cut inside the second sheet: xlrd says "Sheet 1 ('geheimblatt') missing EOF
    # record", and that message must not travel.
    workbook = _workbook_stream()
    cut = workbook.rindex(_record(_EOF, b""))
    path = _write(tmp_path, build_cfb([], streams={"Workbook": workbook[:cut]}))

    outcome = extract_xls(path)

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.CORRUPT
    assert outcome.detail is not None
    assert "geheimblatt" not in outcome.detail
    assert str(tmp_path) not in outcome.detail


def test_xlrd_writes_nothing_and_no_sheet_name_reaches_a_log(tmp_path: Path) -> None:
    # A fresh interpreter, so that xlrd's default logfile (sys.stdout, bound when
    # xlrd is imported) is the real stdout of a process we read whole, and every
    # logger of the process writes to its stderr. The trailing bytes make xlrd
    # write a warning about the file size, which goes nowhere only if the reader
    # hands xlrd a sink.
    path = _write(tmp_path, (FIXTURES / "biff8-values.xls").read_bytes() + b"x" * 100, "geheim.xls")
    program = (
        "import logging, sys\n"
        "logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)\n"
        "from findling.extract.legacy_xls import extract_xls\n"
        f"outcome = extract_xls({path!r})\n"
        "print('STATE', outcome.state.value, 'blattquendel' in outcome.text)\n"
    )

    run = subprocess.run(  # noqa: S603  (fixed argument list, the interpreter of this test)
        [sys.executable, "-c", program], cwd=BACKEND, capture_output=True, text=True, timeout=120, check=True
    )

    assert run.stdout == "STATE indexed True\n"
    assert "geheimblatt" not in run.stderr
    assert run.stderr == ""


# --- the sniff in front of xlrd ------------------------------------------------


def test_an_ole_file_under_an_excel_name_goes_to_xlrd() -> None:
    assert extract_msexcel(_fixture("biff8-values.xls")) == ExtractionOutcome.indexed(VALUES_TEXT)


def test_xlsx_under_an_xls_name_is_read_as_xlsx(tmp_path: Path) -> None:
    workbook = openpyxl.Workbook()
    sheet: Any = workbook.active
    sheet["A1"] = "xlsxquendel"
    buffer = io.BytesIO()
    workbook.save(buffer)

    assert "xlsxquendel" in extract_msexcel(_write(tmp_path, buffer.getvalue())).text


@pytest.mark.parametrize(
    "payload",
    [
        b"<html><body><table><tr><td>htmlquendel</td></tr></table><script>skript()</script></body></html>",
        (
            b'\xef\xbb\xbf<?xml version="1.0"?>\n<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet">'
            b"<Worksheet><Table><Row><Cell><Data>htmlquendel</Data></Cell></Row></Table></Worksheet></Workbook>"
        ),
    ],
    ids=["html", "xml-spreadsheet-2003"],
)
def test_html_and_xml_spreadsheet_under_an_xls_name_are_read_as_markup(tmp_path: Path, payload: bytes) -> None:
    outcome = extract_msexcel(_write(tmp_path, payload))

    assert "htmlquendel" in outcome.text
    assert "skript" not in outcome.text
    assert "<" not in outcome.text


def test_a_csv_export_under_an_xls_name_is_read_as_text(tmp_path: Path) -> None:
    outcome = extract_msexcel(_write(tmp_path, b"Name;Wert\ncsvquendel;3\n"))

    assert "csvquendel" in outcome.text


@pytest.mark.parametrize("payload", [b"", bytes(range(256)) * 4, bytes(4096)], ids=["empty", "binary", "zeros"])
def test_anything_else_under_an_xls_name_is_an_unsupported_variant(tmp_path: Path, payload: bytes) -> None:
    assert extract_msexcel(_write(tmp_path, payload)) == ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)


# --- Befund 9: broken sector chains --------------------------------------------


def _extract_in_child(path: str, answers: Any) -> None:
    """Run in the child: the verdict or the class that escaped, and the time it took.

    A reader caught in a loop may grow its memory with every turn (xlrd's loop
    over a mini stream cycle appends to a list), so the child does not wait for
    the parent to end it: a timer thread ends the process after twice the limit.
    The loop is pure Python, so the timer gets the interpreter lock in time.
    """
    watchdog = threading.Timer(HANG_EXIT_AFTER_S, os._exit, args=(HANG_EXIT_CODE,))
    watchdog.daemon = True
    watchdog.start()
    started = time.monotonic()
    try:
        outcome = extract_xls(path)
    except BaseException as error:  # the test wants to see what escaped
        answers.put(("raised", f"{type(error).__module__}.{type(error).__qualname__}", time.monotonic() - started))
        return
    finally:
        watchdog.cancel()
    answers.put(("outcome", outcome, time.monotonic() - started))


def _guarded(path: str) -> ExtractionOutcome:
    """extract_xls in a spawned child: a named verdict in under 5 s, or the test fails."""
    context = multiprocessing.get_context("spawn")
    answers = context.Queue()
    child = context.Process(target=_extract_in_child, args=(path, answers), daemon=True)
    child.start()
    deadline = time.monotonic() + CHILD_DEADLINE_S
    try:
        while True:
            try:
                kind, value, elapsed = answers.get(timeout=0.5)
                break
            except queue.Empty:
                if child.is_alive() and time.monotonic() < deadline:
                    continue
            # The child is gone or out of time; an answer may still be in the pipe.
            try:
                kind, value, elapsed = answers.get(timeout=2)
                break
            except queue.Empty:
                child.kill()
                child.join()
                pytest.fail(f"no verdict, child exit code {child.exitcode}: the reader hangs")
    finally:
        child.join(timeout=10)
        if child.is_alive():
            child.kill()
            child.join()
    assert kind == "outcome", f"an exception escaped the reader: {value}"
    assert elapsed < TIME_LIMIT_S
    return value


def _corrupt(outcome: ExtractionOutcome) -> bool:
    return outcome.state is State.FAILED and outcome.reason is Reason.CORRUPT


def _fat_payload(**cfb: object) -> bytes:
    """The LibreOffice workbook in the FAT: build_cfb pads it to 4096 bytes, eight sectors."""
    return build_cfb([], streams={"Workbook": _workbook_stream()}, **cfb)  # pyright: ignore[reportArgumentType]


def _start_of(payload: bytes, name: str) -> int:
    with olefile.OleFileIO(io.BytesIO(payload)) as opened:
        ole: Any = opened
        return ole.root.kids_dict[name.lower()].isectStart


def test_the_workbook_in_the_fat_is_read(tmp_path: Path) -> None:
    # The control of the FAT cases below: the builder alone does not break it.
    assert _guarded(_write(tmp_path, _fat_payload())).text == VALUES_TEXT


def test_a_fat_cycle_is_corrupt_in_time(tmp_path: Path) -> None:
    start = _start_of(_fat_payload(), "Workbook")

    assert _corrupt(_guarded(_write(tmp_path, _fat_payload(fat={start + 5: start + 1}))))


def test_a_fat_chain_past_the_end_of_the_file_is_corrupt_in_time(tmp_path: Path) -> None:
    # Sector 100 lies behind the last sector of the file but inside the one FAT
    # sector of 128 entries, so only a check against the size of the file sees it.
    payload = _fat_payload()
    start = _start_of(payload, "Workbook")
    assert len(payload) // 512 - 1 < 100 < 128

    assert _corrupt(_guarded(_write(tmp_path, _fat_payload(fat={start + 2: 100}))))


@pytest.mark.parametrize("last_next", [None, CFB_END_OF_CHAIN], ids=["cycle", "control"])
def test_a_difat_cycle_is_corrupt_in_time(tmp_path: Path, last_next: int | None) -> None:
    # 110 FAT sectors need a file of about 7 MB before a DIFAT sector is due at all.
    payload = cfb_with_difat(_fat_payload(), sectors=13_960, fat_count=110, last_next=last_next)

    outcome = _guarded(_write(tmp_path, payload))

    if last_next is None:
        assert _corrupt(outcome)
    else:
        assert outcome.text == VALUES_TEXT


def test_a_fat_declared_larger_than_the_file_is_corrupt_in_time(tmp_path: Path) -> None:
    # The cost that olefile pays for a FAT declared far past the file (31-05:
    # 29 s for 20 000 sectors), now that the .xls reader asks olefile too.
    grown = bytearray(cfb_with_difat(_fat_payload(), sectors=200, fat_count=20_000, last_next=CFB_END_OF_CHAIN))
    for difat in range(200, len(grown) // 512 - 1):
        struct.pack_into("<127I", grown, (difat + 1) * 512, *([0] * 127))

    assert _corrupt(_guarded(_write(tmp_path, bytes(grown))))


def _mini_chain(path: str) -> tuple[int, list[int]]:
    """File offset of the MiniFAT and the mini sector chain of the Workbook stream."""
    with olefile.OleFileIO(path) as opened:
        ole: Any = opened
        entry = ole.root.kids_dict["workbook"]
        assert entry.is_minifat
        ole.openstream("Workbook").read()
        assert ole.num_mini_fat_sectors == 1
        chain = [entry.isectStart]
        for _ in range(-(-entry.size // 64) - 1):
            chain.append(ole.minifat[chain[-1]])
        return (ole.first_mini_fat_sector + 1) * ole.sectorsize, chain


@pytest.mark.parametrize("cycle", [True, False], ids=["cycle", "control"])
def test_a_minifat_cycle_is_corrupt_in_time(tmp_path: Path, cycle: bool) -> None:
    # xlrd follows a chain in the mini stream without a set of seen sectors, so
    # a cycle there is a loop without end, not an error.
    minifat_at, chain = _mini_chain(_fixture("biff8-values.xls"))
    assert len(chain) > 30
    data = bytearray((FIXTURES / "biff8-values.xls").read_bytes())
    if cycle:
        struct.pack_into("<I", data, minifat_at + 4 * chain[30], chain[20])

    outcome = _guarded(_write(tmp_path, bytes(data)))

    if cycle:
        assert _corrupt(outcome)
    else:
        assert outcome.text == VALUES_TEXT


@pytest.mark.parametrize("back", [0, 20], ids=["to-the-start", "into-the-middle"])
def test_a_minifat_chain_that_runs_on_past_its_stream_into_a_cycle_is_corrupt_in_time(
    tmp_path: Path, back: int
) -> None:
    # The cycle hides behind the last sector of the stream: a walk bound by the
    # size of the stream (and olefile's read) never gets there, xlrd does.
    minifat_at, chain = _mini_chain(_fixture("biff8-values.xls"))
    data = bytearray((FIXTURES / "biff8-values.xls").read_bytes())
    struct.pack_into("<I", data, minifat_at + 4 * chain[-1], chain[back])

    assert _corrupt(_guarded(_write(tmp_path, bytes(data))))


def test_a_fat_chain_that_runs_on_past_its_stream_is_corrupt_in_time(tmp_path: Path) -> None:
    payload = _fat_payload()
    start = _start_of(payload, "Workbook")

    assert _corrupt(_guarded(_write(tmp_path, _fat_payload(fat={start + 7: start}))))


def _rename_entry(data: bytearray, old: str, new: str, *, start: int | None = None, size: int | None = None) -> None:
    """Give the directory entry called ``old`` the name ``new`` ([MS-CFB] 2.6), optionally a new place."""
    encoded = old.encode("utf-16-le") + b"\0\0"
    assert bytes(data).count(encoded) == 1
    at = bytes(data).find(encoded)
    assert at % 128 == 0
    name = new.encode("utf-16-le") + b"\0\0"
    data[at : at + 64] = name.ljust(64, b"\0")
    struct.pack_into("<H", data, at + 0x40, len(name))
    if start is not None:
        struct.pack_into("<I", data, at + 0x74, start)
    if size is not None:
        struct.pack_into("<Q", data, at + 0x78, size)


@pytest.mark.parametrize("cycle", [True, False], ids=["cycle", "control"])
def test_the_book_stream_behind_an_empty_workbook_is_checked_too(tmp_path: Path, cycle: bool) -> None:
    # xlrd reads Workbook first and takes Book when that one is empty, so the
    # chain of Book is read as well and has to be walked as well. Built from the
    # LibreOffice file: its workbook becomes "Book", its stream "\x01Ole"
    # becomes an empty "Workbook".
    minifat_at, chain = _mini_chain(_fixture("biff8-values.xls"))
    data = bytearray((FIXTURES / "biff8-values.xls").read_bytes())
    _rename_entry(data, "Workbook", "Book")
    _rename_entry(data, "\x01Ole", "Workbook", start=CFB_END_OF_CHAIN, size=0)
    if cycle:
        struct.pack_into("<I", data, minifat_at + 4 * chain[30], chain[20])

    outcome = _guarded(_write(tmp_path, bytes(data)))

    if cycle:
        assert _corrupt(outcome)
    else:
        assert outcome.text == VALUES_TEXT
