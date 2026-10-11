"""ZIP files as documents (FMT-02, D-30-03, D-31-07, plan 31-08).

Every ZIP file here is built while the test runs; nothing comes from outside the
repository. Three kinds of case:

* **The count before ZipFile (blocker 2).** zipfile reads the central directory
  by its byte length and never looks at the entry count of the end record, so a
  count of 5 over 10 001 real headers would hand zipfile all of them. These
  cases rewrite the end record (and the ZIP64 end record) after writing and
  prove with a call counter on ``archive.ZipFile`` that zipfile is never asked.
* **The bomb corpus.** Quine, nesting, fifty inner ZIP files against the one
  shared budget, the ratio, overlapping entries, names that climb out of the
  scratch directory, encrypted members and code page names. Each of them runs in
  a spawned child that ends itself after 10 s (the lesson of plan 31-06: a
  regression that loops must not hang the test run) and has to come back with a
  named verdict in under 5 s, measured inside the child.
* **The text.** Sections of mark, display name, line break, member text; the
  mark stands nowhere else.

After every case the directory around the scratch file looks exactly as before:
nothing is left behind and nothing lands outside.
"""

from __future__ import annotations

import hashlib
import io
import logging
import multiprocessing
import os
import queue
import struct
import threading
import time
import zipfile
import zlib
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import docx
import pytest

from findling.config import ARCHIVE_MEMBER_MARK, settings
from findling.extract import archive
from findling.extract.archive import count_central_directory, extract_zip
from findling.extract.errors import ExtractionOutcome, Reason, State
from test_extract_edge_paths import _one_page_pdf

MARK = ARCHIVE_MEMBER_MARK
SCRATCH_NAME = "job-7.part"
LEGACY = Path(__file__).resolve().parent / "fixtures" / "legacy"

TIME_LIMIT_S = 5.0
CHILD_DEADLINE_S = 40.0
HANG_EXIT_AFTER_S = 2 * TIME_LIMIT_S
HANG_EXIT_CODE = 3

LIMIT = ExtractionOutcome.skipped(Reason.ARCHIVE_LIMIT)

# PKWARE APPNOTE 6.3.10, 4.3.12 to 4.3.16.
_EOCD = b"PK\x05\x06"
_EOCD64 = b"PK\x06\x06"
_LOCATOR64 = b"PK\x06\x07"
_CENTRAL = b"PK\x01\x02"
_LOCAL = b"PK\x03\x04"


@pytest.fixture(autouse=True)
def _fresh_settings() -> Iterator[None]:
    settings.cache_clear()
    yield
    settings.cache_clear()


# --- building ZIP files ------------------------------------------------------


def _zip(
    members: list[tuple[str, bytes]],
    *,
    compression: int = zipfile.ZIP_DEFLATED,
    comment: bytes = b"",
) -> bytes:
    sink = io.BytesIO()
    with zipfile.ZipFile(sink, "w", compression) as target:
        for name, data in members:
            target.writestr(name, data)
        target.comment = comment
    return sink.getvalue()


def _empty_entries(count: int, *, prefix: str = "leer") -> bytes:
    return _zip([(f"{prefix}/{number:05d}.txt", b"") for number in range(count)], compression=zipfile.ZIP_STORED)


def _end_record_at(raw: bytes) -> int:
    return raw.rindex(_EOCD)


def _claiming(raw: bytes, entries: int) -> bytes:
    """The same bytes, with both entry counts of the end record set to ``entries``."""
    at = _end_record_at(raw)
    return raw[: at + 8] + struct.pack("<HH", entries, entries) + raw[at + 12 :]


def _as_zip64(raw: bytes, entries: int) -> bytes:
    """The end record replaced by a ZIP64 end record, its locator and an end record of 0xFFFF fields."""
    at = _end_record_at(raw)
    size_cd, offset_cd = struct.unpack_from("<II", raw, at + 12)
    body = raw[:at]
    record = struct.pack("<4sQ2H2L4Q", _EOCD64, 44, 45, 45, 0, 0, entries, entries, size_cd, offset_cd)
    locator = struct.pack("<4sLQL", _LOCATOR64, 0, len(body), 1)
    end = struct.pack("<4s4H2LH", _EOCD, 0, 0, 0xFFFF, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0)
    return body + record + locator + end


def _central_headers(raw: bytes) -> list[int]:
    """Offsets of the central directory headers of a plain ZIP file built here."""
    at = _end_record_at(raw)
    size_cd, offset_cd = struct.unpack_from("<II", raw, at + 12)
    start = at - size_cd
    assert start == offset_cd
    offsets: list[int] = []
    position = start
    while position < at:
        offsets.append(position)
        name_len, extra_len, comment_len = struct.unpack_from("<HHH", raw, position + 28)
        position += 46 + name_len + extra_len + comment_len
    return offsets


def _patched(raw: bytes, name: str, *, flag: int = 0, method: int | None = None) -> bytes:
    """Set a flag bit or a compression method in the local and the central header of one member."""
    data = bytearray(raw)
    encoded = name.encode("ascii")
    for header in _central_headers(raw):
        name_len = struct.unpack_from("<H", data, header + 28)[0]
        if bytes(data[header + 46 : header + 46 + name_len]) != encoded:
            continue
        local = struct.unpack_from("<I", data, header + 42)[0]
        for flag_at, method_at in ((header + 8, header + 10), (local + 6, local + 8)):
            struct.pack_into("<H", data, flag_at, struct.unpack_from("<H", data, flag_at)[0] | flag)
            if method is not None:
                struct.pack_into("<H", data, method_at, method)
    return bytes(data)


def _renamed(raw: bytes, placeholder: bytes, name: bytes) -> bytes:
    """Replace a member name of the same length in both headers, without touching the flags."""
    assert len(placeholder) == len(name)
    assert raw.count(placeholder) == 2
    return raw.replace(placeholder, name)


def _docx(text: str) -> bytes:
    document = docx.Document()
    document.add_paragraph(text)
    sink = io.BytesIO()
    document.save(sink)
    return sink.getvalue()


def _eml() -> bytes:
    return (
        b"From: Erika <erika@example.org>\r\n"
        b"To: Max <max@example.org>\r\n"
        b"Subject: briefquendel\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Der Text der Mail nennt das postquendel.\r\n"
    )


def _overlapping() -> bytes:
    """Two members, the data of the first quotes the local header of the second (Fifield 2019)."""
    inner_name = b"b.txt"
    inner_data = b"overlapquendel " * 4
    second = (
        struct.pack("<4s5H3L2H", _LOCAL, 20, 0, 0, 0, 0, zlib.crc32(inner_data), len(inner_data), len(inner_data), 5, 0)
        + inner_name
        + inner_data
    )
    first_name = b"a.txt"
    first = (
        struct.pack("<4s5H3L2H", _LOCAL, 20, 0, 0, 0, 0, zlib.crc32(second), len(second), len(second), 5, 0)
        + first_name
        + second
    )
    second_offset = 30 + len(first_name)

    def central(name: bytes, crc: int, size: int, offset: int) -> bytes:
        return (
            struct.pack("<4s6H3L5HLL", _CENTRAL, 20, 20, 0, 0, 0, 0, crc, size, size, len(name), 0, 0, 0, 0, 0, offset)
            + name
        )

    directory = central(first_name, zlib.crc32(second), len(second), 0) + central(
        inner_name, zlib.crc32(inner_data), len(inner_data), second_offset
    )
    end = struct.pack("<4s4H2LH", _EOCD, 0, 0, 2, 2, len(directory), len(first), 0)
    return first + directory + end


# --- a ZIP file that contains itself (Cox 2010, "Zip Files All The Way Down") ---
#
# A deflate stream that inflates to the whole file around it: local header,
# itself, central directory and end record. Built from stored blocks (literal)
# and fixed Huffman blocks with one or more copies (repeat), every block padded to
# one unit of 15 bytes so that a copied block is byte for byte the block it
# copies. The CRC field appears inside the data it covers; CRC-32 is affine over
# GF(2), so the fixed point is the solution of a 32 by 32 linear system.

_UNIT = 15
_QUINE_NAME = b"selbst-ich1.zip"


def _length_symbol(length: int) -> tuple[int, int, int]:
    if length == 258:
        return 285, 0, 0
    base, symbol = 3, 257
    table: list[tuple[int, int, int]] = [(257 + i, 3 + i, 0) for i in range(8)]
    base, symbol = 11, 265
    for extra in range(1, 6):
        for _ in range(4):
            table.append((symbol, base, extra))
            symbol += 1
            base += 1 << extra
    for code, start, extra in reversed(table):
        if length >= start:
            return code, length - start, extra
    raise ValueError(length)


def _distance_symbol(distance: int) -> tuple[int, int, int]:
    base = 1
    table: list[tuple[int, int, int]] = []
    for code in range(30):
        extra = max(0, code // 2 - 1)
        table.append((code, base, extra))
        base += 1 << extra
    for code, start, extra in reversed(table):
        if distance >= start:
            return code, distance - start, extra
    raise ValueError(distance)


class _Bits:
    def __init__(self) -> None:
        self.value = 0
        self.count = 0

    def put(self, value: int, count: int) -> None:
        self.value |= value << self.count
        self.count += count

    def huffman(self, code: int, count: int) -> None:
        for shift in reversed(range(count)):
            self.put((code >> shift) & 1, 1)

    def bytes(self) -> bytes:
        return self.value.to_bytes((self.count + 7) // 8, "little")


def _copy_bits(parts: list[int], distance: int) -> int:
    total = 0
    for length in parts:
        code, _, extra = _length_symbol(length)
        total += (7 if code <= 279 else 8) + extra + 5 + _distance_symbol(distance)[2]
    return total


def _repeat(count: int, *, final: bool = False) -> bytes:
    """One unit that repeats the last ``count`` bytes, padded with empty stored blocks."""
    candidates = (
        [[count]] + [[3] * j + [count - 3 * j] for j in range(1, 8)] + [[x, count - x] for x in range(3, count - 2)]
    )
    for parts in candidates:
        if min(parts) < 3:
            continue
        body = -(-(13 + _copy_bits(parts, count)) // 8) + 4
        for pads in range(4):
            if body + 5 * pads != _UNIT:
                continue
            bits = _Bits()
            bits.put(0, 1)
            bits.put(1, 2)
            for length in parts:
                code, value, extra = _length_symbol(length)
                bits.huffman(code - 256 if code <= 279 else 0xC0 + code - 280, 7 if code <= 279 else 8)
                bits.put(value, extra)
                distance_code, distance_value, distance_extra = _distance_symbol(count)
                bits.huffman(distance_code, 5)
                bits.put(distance_value, distance_extra)
            bits.huffman(0, 7)
            bits.put(1 if final and pads == 0 else 0, 1)
            bits.put(0, 2)
            unit = bits.bytes() + b"\x00\x00\xff\xff"
            for pad in range(pads):
                unit += (b"\x01" if final and pad == pads - 1 else b"\x00") + b"\x00\x00\xff\xff"
            return unit
    raise ValueError(count)


def _literal(count: int) -> bytes:
    return b"\x00\x00\x00\xff\xff" * (_UNIT // 5 - 1) + b"\x00" + struct.pack("<HH", count, count ^ 0xFFFF)


def _quine_with(crc: int) -> bytes:
    p, s = 3, 6  # local header and trailer in units of 15 bytes

    def stream(head: bytes, tail: bytes) -> bytes:
        lp, rp = _literal((p + 1) * _UNIT), _repeat((p + 1) * _UNIT)
        l1, l4, r4, l0 = _literal(_UNIT), _literal(4 * _UNIT), _repeat(4 * _UNIT), _literal(0)
        ls, rs = _literal((s + 1) * _UNIT), _repeat((s + 1) * _UNIT, final=True)
        return b"".join(
            [
                *(lp, head, lp, rp, l1, rp, l1, l1, l4, rp, l1, l1, l4, r4, l4, r4, l4, r4, l4, r4),
                *(l4, r4, l0, l0, ls, r4, l0, l0, ls, rs, tail, rs),
            ]
        )

    length = len(stream(bytes(p * _UNIT), bytes(s * _UNIT)))
    whole = p * _UNIT + length + s * _UNIT
    head = struct.pack("<4s5H3L2H", _LOCAL, 20, 0, 8, 0, 0x21, crc, length, whole, len(_QUINE_NAME), 0) + _QUINE_NAME
    central = (
        struct.pack(
            "<4s6H3L5HLL", _CENTRAL, 20, 20, 0, 8, 0, 0x21, crc, length, whole, len(_QUINE_NAME), 0, 0, 0, 0, 0, 0
        )
        + _QUINE_NAME
    )
    tail = central + struct.pack("<4s4H2LH", _EOCD, 0, 0, 1, 1, len(central), p * _UNIT + length, 7) + b"selbst!"
    assert len(head) == p * _UNIT
    assert len(tail) == s * _UNIT
    return head + stream(head, tail) + tail


def _quine() -> bytes:
    base = zlib.crc32(_quine_with(0))
    columns = [zlib.crc32(_quine_with(1 << bit)) ^ base ^ (1 << bit) for bit in range(32)]
    rows = [[sum(1 << i for i in range(32) if (columns[i] >> bit) & 1), (base >> bit) & 1] for bit in range(32)]
    pivot_row = 0
    pivots: dict[int, int] = {}
    for column in range(32):
        found = next((r for r in range(pivot_row, 32) if (rows[r][0] >> column) & 1), None)
        if found is None:
            continue
        rows[pivot_row], rows[found] = rows[found], rows[pivot_row]
        for other in range(32):
            if other != pivot_row and (rows[other][0] >> column) & 1:
                rows[other][0] ^= rows[pivot_row][0]
                rows[other][1] ^= rows[pivot_row][1]
        pivots[column] = pivot_row
        pivot_row += 1
    crc = sum(1 << column for column, row in pivots.items() if rows[row][1])
    raw = _quine_with(crc)
    assert zlib.crc32(raw) == crc
    return raw


# --- running the reader ------------------------------------------------------


def _tree(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)) for path in root.rglob("*"))


def _place(tmp_path: Path, raw: bytes) -> Path:
    # Two levels deep, so that a name climbing two levels up still lands inside
    # tmp_path, where the tree comparison of the callers can see it.
    scratch = tmp_path / "a" / "b" / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    target = scratch / SCRATCH_NAME
    target.write_bytes(raw)
    return target


def _run(tmp_path: Path, raw: bytes) -> ExtractionOutcome:
    """extract_zip in this process, with the directory around the scratch file checked."""
    target = _place(tmp_path, raw)
    before = _tree(tmp_path)
    outcome = extract_zip(str(target))
    assert _tree(tmp_path) == before
    return outcome


@pytest.fixture
def zip_opens(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []
    real = zipfile.ZipFile

    def counting(*args: Any, **kwargs: Any) -> zipfile.ZipFile:
        calls.append("ZipFile")
        return real(*args, **kwargs)

    monkeypatch.setattr(archive, "ZipFile", counting)
    return calls


def _in_child(path: str, limits: dict[str, int], environment: dict[str, str], answers: Any) -> None:
    """Run in a spawned child: verdict, ZipFile calls and time, or the class that escaped.

    The timer ends the process after twice the limit, so a regression that loops
    (a reader without the depth limit unpacks the quine forever) cannot hang the
    run; the parent then fails the test with the exit code.
    """
    watchdog = threading.Timer(HANG_EXIT_AFTER_S, os._exit, args=(HANG_EXIT_CODE,))
    watchdog.daemon = True
    watchdog.start()
    os.environ.update(environment)
    settings.cache_clear()
    for name, value in limits.items():
        setattr(archive, name, value)
    calls = [0]
    real = zipfile.ZipFile

    def counting(*args: Any, **kwargs: Any) -> zipfile.ZipFile:
        calls[0] += 1
        return real(*args, **kwargs)

    setattr(archive, "ZipFile", counting)  # noqa: B010 - the attribute is the point
    started = time.monotonic()
    try:
        outcome = extract_zip(path)
    except BaseException as error:  # the test wants to see what escaped
        answers.put(("raised", f"{type(error).__module__}.{type(error).__qualname__}", time.monotonic() - started, 0))
        return
    finally:
        watchdog.cancel()
    answers.put(("outcome", outcome, time.monotonic() - started, calls[0]))


def _guarded(
    tmp_path: Path,
    raw: bytes,
    *,
    limits: dict[str, int] | None = None,
    environment: dict[str, str] | None = None,
) -> tuple[ExtractionOutcome, int]:
    """extract_zip in a spawned child: a named verdict in under 5 s and the ZipFile calls, or a failed test."""
    target = _place(tmp_path, raw)
    before = _tree(tmp_path)
    context = multiprocessing.get_context("spawn")
    answers = context.Queue()
    child = context.Process(target=_in_child, args=(str(target), limits or {}, environment or {}, answers), daemon=True)
    child.start()
    deadline = time.monotonic() + CHILD_DEADLINE_S
    try:
        while True:
            try:
                kind, value, elapsed, calls = answers.get(timeout=0.5)
                break
            except queue.Empty:
                if child.is_alive() and time.monotonic() < deadline:
                    continue
            try:
                kind, value, elapsed, calls = answers.get(timeout=2)
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
    assert elapsed < TIME_LIMIT_S, f"{elapsed:.2f} s"
    assert _tree(tmp_path) == before
    return value, calls


def _sections(outcome: ExtractionOutcome) -> dict[str, str]:
    """Display name to member text, read off the text the way plan 31-09 will read it."""
    assert outcome.text.startswith(MARK)
    sections: dict[str, str] = {}
    for section in outcome.text.split(MARK)[1:]:
        name, _, text = section.partition("\n")
        sections[name] = text.strip("\n")
    return sections


# --- blocker 2: the count before ZipFile -------------------------------------


def test_an_end_record_that_claims_5_entries_over_10001_headers_never_reaches_zipfile(tmp_path: Path) -> None:
    raw = _claiming(_empty_entries(10_001), 5)
    assert struct.unpack_from("<HH", raw, _end_record_at(raw) + 8) == (5, 5)

    outcome, calls = _guarded(tmp_path, raw)

    assert outcome == LIMIT
    assert calls == 0


def test_a_zip64_end_record_that_claims_5_entries_over_10001_headers_never_reaches_zipfile(tmp_path: Path) -> None:
    raw = _as_zip64(_empty_entries(10_001), 5)
    with zipfile.ZipFile(io.BytesIO(raw)) as check:  # zipfile itself reads all of them
        assert len(check.infolist()) == 10_001

    outcome, calls = _guarded(tmp_path, raw)

    assert outcome == LIMIT
    assert calls == 0


def test_a_central_directory_over_its_byte_limit_never_reaches_zipfile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, zip_opens: list[str]
) -> None:
    monkeypatch.setattr(archive, "ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES", 1000)
    raw = _zip([(f"{number}-{'n' * 400}.txt", b"x") for number in range(3)])

    assert _run(tmp_path, raw) == LIMIT
    assert zip_opens == []


def test_a_central_directory_just_under_its_byte_limit_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, zip_opens: list[str]
) -> None:
    raw = _zip([(f"{number}-{'n' * 400}.txt", b"x") for number in range(3)])
    at = _end_record_at(raw)
    monkeypatch.setattr(archive, "ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES", struct.unpack_from("<I", raw, at + 12)[0])

    assert _run(tmp_path, raw).state is State.INDEXED
    assert zip_opens == ["ZipFile"]


def test_an_entry_count_exactly_at_the_limit_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, zip_opens: list[str]
) -> None:
    monkeypatch.setattr(archive, "ARCHIVE_MAX_ENTRIES", 20)
    raw = _zip([("grenze.txt", b"grenzquendel"), *((f"leer-{n}.txt", b"") for n in range(19))])

    outcome = _run(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert "grenzquendel" in outcome.text
    assert zip_opens == ["ZipFile"]


def test_one_entry_over_the_limit_never_reaches_zipfile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, zip_opens: list[str]
) -> None:
    monkeypatch.setattr(archive, "ARCHIVE_MAX_ENTRIES", 20)
    raw = _zip([("grenze.txt", b"grenzquendel"), *((f"leer-{n}.txt", b"") for n in range(20))])

    assert _run(tmp_path, raw) == LIMIT
    assert zip_opens == []


def test_a_wrong_signature_inside_the_central_directory_is_corrupt_without_zipfile(
    tmp_path: Path, zip_opens: list[str]
) -> None:
    raw = _zip([(f"teil-{n}.txt", b"x") for n in range(5)])
    third = _central_headers(raw)[2]
    broken = raw[:third] + b"PK\x09\x09" + raw[third + 4 :]

    outcome = _run(tmp_path, broken)

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.CORRUPT
    assert zip_opens == []


def test_a_cut_off_file_without_an_end_record_is_corrupt_without_zipfile(tmp_path: Path, zip_opens: list[str]) -> None:
    raw = _zip([("rest.txt", b"restquendel" * 10)])

    outcome = _run(tmp_path, raw[:-30])

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.CORRUPT
    assert zip_opens == []


def _forced_zip64() -> bytes:
    sink = io.BytesIO()
    with zipfile.ZipFile(sink, "w", zipfile.ZIP_DEFLATED) as target:
        with target.open("gross.txt", "w", force_zip64=True) as member:
            member.write(b"zip64quendel " * 50)
        target.writestr("klein.txt", b"klein")
    return sink.getvalue()


def _with_extras() -> bytes:
    sink = io.BytesIO()
    with zipfile.ZipFile(sink, "w", zipfile.ZIP_DEFLATED) as target:
        for number in range(4):
            info = zipfile.ZipInfo(f"extra-{number}.txt")
            info.extra = struct.pack("<HHB", 0x5455, 5, 1) + struct.pack("<I", 1_700_000_000 + number)
            info.comment = f"Kommentar {number}".encode("ascii")
            target.writestr(info, b"extraquendel")
    return sink.getvalue()


CONSISTENCY_CASES: dict[str, Callable[[], bytes]] = {
    "small": lambda: _zip([("a.txt", b"a"), ("b/c.txt", b"c"), ("b/", b"")]),
    "prepended": lambda: b"MZ" * 700 + _zip([("a.txt", b"a"), ("b.txt", b"b")]),
    "force-zip64": _forced_zip64,
    "comment": lambda: _zip([("a.txt", b"a"), ("b.txt", b"b")], comment=b"ein Kommentar am Ende"),
    "extra-fields": _with_extras,
    "zip64-end-record": lambda: _as_zip64(_zip([(f"z{n}.txt", b"z") for n in range(7)]), 7),
    "zip64-prepended": lambda: b"\x7fELF" * 64 + _as_zip64(_zip([(f"z{n}.txt", b"z") for n in range(3)]), 3),
}


@pytest.mark.parametrize("case", sorted(CONSISTENCY_CASES))
def test_the_own_count_equals_what_zipfile_reads(case: str) -> None:
    raw = CONSISTENCY_CASES[case]()
    with zipfile.ZipFile(io.BytesIO(raw)) as check:
        expected = len(check.infolist())

    assert count_central_directory(io.BytesIO(raw), len(raw), limit=1_000_000) == expected


def test_the_count_stops_one_past_the_limit() -> None:
    raw = _empty_entries(50)

    assert count_central_directory(io.BytesIO(raw), len(raw), limit=3) == 4


# --- the one shared budget (finding 10) --------------------------------------


def test_fifty_inner_zip_files_just_under_the_entry_limit_are_over_it_together(tmp_path: Path) -> None:
    inner = _empty_entries(99)
    raw = _zip([(f"teil-{n:02d}.zip", inner) for n in range(50)])

    outcome, _ = _guarded(tmp_path, raw, limits={"ARCHIVE_MAX_ENTRIES": 100})

    assert outcome == LIMIT


def test_one_inner_zip_file_just_under_the_entry_limit_is_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(archive, "ARCHIVE_MAX_ENTRIES", 100)
    raw = _zip([("teil-00.zip", _empty_entries(99))])

    assert _run(tmp_path, raw).state is State.INDEXED


def test_fifty_inner_zip_files_just_under_the_byte_limit_are_over_it_together(tmp_path: Path) -> None:
    inner = _zip([("nullen.bin", bytes(99_000))])
    raw = _zip([(f"teil-{n:02d}.zip", inner) for n in range(50)])

    outcome, _ = _guarded(tmp_path, raw, limits={"EXTRACT_ARCHIVE_TOTAL_MAX_BYTES": 100_000})

    assert outcome == LIMIT


def test_one_inner_zip_file_just_under_the_byte_limit_is_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(archive, "EXTRACT_ARCHIVE_TOTAL_MAX_BYTES", 100_000)
    raw = _zip([("teil-00.zip", _zip([("nullen.bin", bytes(99_000))]))])

    outcome = _run(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert "teil-00.zip/nullen.bin" in _sections(outcome)


def test_a_declared_total_over_the_limit_is_an_archive_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(archive, "EXTRACT_ARCHIVE_TOTAL_MAX_BYTES", 10_000)
    raw = _zip([("a.txt", b"a" * 6_000), ("b.txt", b"b" * 6_000)])

    assert _run(tmp_path, raw) == LIMIT


# --- the bomb corpus ---------------------------------------------------------


def test_the_quine_is_a_zip_file_that_contains_itself() -> None:
    raw = _quine()
    with zipfile.ZipFile(io.BytesIO(raw)) as check:
        assert check.namelist() == [_QUINE_NAME.decode("ascii")]
        assert check.read(_QUINE_NAME.decode("ascii")) == raw


def test_the_quine_ends_at_the_depth_limit(tmp_path: Path) -> None:
    outcome, calls = _guarded(tmp_path, _quine())

    assert outcome == LIMIT
    assert calls == 2  # the file itself and its copy at level 2, never a third


def test_an_inner_zip_file_is_read_with_its_path(tmp_path: Path) -> None:
    raw = _zip([("innen.zip", _zip([("datei.txt", b"tiefenquendel")]))])

    outcome, _ = _guarded(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert _sections(outcome)["innen.zip/datei.txt"] == "tiefenquendel"


def test_a_zip_file_inside_an_inner_one_ends_the_whole_file(tmp_path: Path) -> None:
    third = _zip([("x.txt", b"drittquendel")])
    raw = _zip([("oben.txt", b"obenquendel"), ("innen.zip", _zip([("tiefer.zip", third)]))])

    outcome, _ = _guarded(tmp_path, raw)

    assert outcome == LIMIT


def test_a_member_over_the_ratio_is_an_archive_limit(tmp_path: Path) -> None:
    raw = _zip([("vorn.txt", b"vornquendel"), ("nullen.txt", bytes(2 * 1024 * 1024))])

    outcome, _ = _guarded(tmp_path, raw)

    assert outcome == LIMIT


def test_a_large_member_of_ordinary_text_is_under_the_ratio(tmp_path: Path) -> None:
    vocabulary = ["Miete", "Vertrag", "Grundbuch", "Frist", "Zahlung", "Bescheid"]
    stream = hashlib.shake_128(b"31-08").digest(300_000)
    text = " ".join(vocabulary[byte % len(vocabulary)] for byte in stream).encode("ascii")
    assert len(text) > 1024 * 1024

    outcome = _run(tmp_path, _zip([("lang.txt", text)]))

    assert outcome.state is State.INDEXED


def test_a_small_member_is_not_judged_by_its_ratio(tmp_path: Path) -> None:
    outcome = _run(tmp_path, _zip([("klein.txt", b"a" * (512 * 1024))]))

    assert outcome.state is State.INDEXED


def test_overlapping_entries_are_an_archive_limit(tmp_path: Path) -> None:
    raw = _overlapping()
    with zipfile.ZipFile(io.BytesIO(raw)) as check, pytest.raises(zipfile.BadZipFile, match="Overlapped"):
        check.read("a.txt")

    outcome, _ = _guarded(tmp_path, raw)

    assert outcome == LIMIT


def test_names_that_climb_out_stay_text(tmp_path: Path) -> None:
    absolute = f"{tmp_path.as_posix()}/flucht.txt"
    raw = _zip(
        [
            ("../../etc/passwd", b"pfadquendel"),
            ("../../etc/passwd.txt", b"kletterquendel"),
            (absolute, b"absquendel"),
        ]
    )

    outcome, _ = _guarded(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert _sections(outcome) == {
        "../../etc/passwd": "",
        "../../etc/passwd.txt": "kletterquendel",
        absolute: "absquendel",
    }


def test_an_encrypted_member_stays_a_name_next_to_a_readable_one(tmp_path: Path) -> None:
    raw = _patched(_zip([("offen.txt", b"offenquendel"), ("geheim.txt", b"geheimquendel")]), "geheim.txt", flag=0x1)

    outcome, _ = _guarded(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert _sections(outcome) == {"offen.txt": "offenquendel", "geheim.txt": ""}


def test_only_encrypted_members_are_skipped_as_encrypted(tmp_path: Path) -> None:
    raw = _zip([("eins.txt", b"einsquendel"), ("zwei.txt", b"zweiquendel")])
    raw = _patched(_patched(raw, "eins.txt", flag=0x1), "zwei.txt", flag=0x1)

    outcome, _ = _guarded(tmp_path, raw)

    assert outcome == ExtractionOutcome.skipped(Reason.ENCRYPTED)


def test_aes_and_deflate64_members_stay_names(tmp_path: Path) -> None:
    raw = _zip([("offen.txt", b"offenquendel"), ("aes.txt", b"aesquendel"), ("d64.txt", b"d64quendel")])
    raw = _patched(_patched(raw, "aes.txt", flag=0x1, method=99), "d64.txt", method=9)

    outcome, _ = _guarded(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert _sections(outcome) == {"offen.txt": "offenquendel", "aes.txt": "", "d64.txt": ""}


def test_a_name_without_the_utf8_flag_is_read_as_cp437(tmp_path: Path) -> None:
    placeholder = b"Gr__e.txt"
    cp437 = bytes([0x47, 0x72, 0x94, 0xE1, 0x65]) + b".txt"
    raw = _renamed(_zip([(placeholder.decode("ascii"), b"umlautquendel")]), placeholder, cp437)
    expected = "Gr" + chr(0xF6) + chr(0xDF) + "e.txt"

    outcome, _ = _guarded(tmp_path, raw)

    assert _sections(outcome) == {expected: "umlautquendel"}


def test_a_name_with_the_utf8_flag_keeps_its_umlauts_and_loses_its_bidi_override(tmp_path: Path) -> None:
    name = "Gr" + chr(0xF6) + chr(0xDF) + "e-rechnung" + chr(0x202E) + "fdp.txt"
    raw = _zip([(name, b"bidiquendel")])

    outcome, _ = _guarded(tmp_path, raw)

    assert _sections(outcome) == {"Gr" + chr(0xF6) + chr(0xDF) + "e-rechnungfdp.txt": "bidiquendel"}


# --- the text ----------------------------------------------------------------


def test_the_text_is_marked_sections_and_a_picture_is_a_name(tmp_path: Path) -> None:
    raw = _zip([("rechnung.txt", b"packquendel"), ("bild.png", b"\x89PNG\r\n\x1a\n" + bytes(64))])

    outcome = _run(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert outcome.text.startswith(MARK + "rechnung.txt\npackquendel")
    assert MARK + "bild.png\n" in outcome.text
    assert _sections(outcome) == {"rechnung.txt": "packquendel", "bild.png": ""}


def test_the_mark_stands_only_at_the_sections(tmp_path: Path) -> None:
    member = b"Der Satz vor der Marke " + MARK.encode("ascii") + b"und der Satz nach der Marke."
    raw = _zip([("a.txt", member), ("b" + MARK + "c.txt", b"Das zweite Mitglied.")])

    outcome = _run(tmp_path, raw)

    assert outcome.text.count(MARK) == 2
    assert _sections(outcome) == {
        "a.txt": "Der Satz vor der Marke und der Satz nach der Marke.",
        "bc.txt": "Das zweite Mitglied.",
    }


def test_office_mail_and_legacy_members_are_read_under_their_names(tmp_path: Path) -> None:
    raw = _zip(
        [
            ("brief.docx", _docx("Das docxquendel steht im Brief.")),
            ("post.eml", _eml()),
            ("alt.doc", (LEGACY / "word97-latin.doc").read_bytes()),
            ("tabelle.xls", (LEGACY / "biff8-values.xls").read_bytes()),
            ("text.pdf", _one_page_pdf()),
        ]
    )

    outcome = _run(tmp_path, raw)

    sections = _sections(outcome)
    assert "docxquendel" in sections["brief.docx"]
    assert "briefquendel" in sections["post.eml"]
    assert "postquendel" in sections["post.eml"]
    assert "wortquendel" in sections["alt.doc"]
    assert "zellquendel" in sections["tabelle.xls"]
    assert "Mietverhaeltnisses" in sections["text.pdf"]


def test_no_member_ever_reaches_ocr(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from findling.extract import image, ocr

    def refuse(_path: str) -> ExtractionOutcome:
        raise AssertionError("OCR inside a ZIP file")

    monkeypatch.setattr(image, "extract_image", refuse)
    monkeypatch.setattr(ocr, "extract_pdf_ocr", refuse)
    raw = _zip([("scan.png", b"\x89PNG\r\n\x1a\n" + bytes(64)), ("foto.jpg", b"\xff\xd8\xff" + bytes(64))])

    assert _sections(_run(tmp_path, raw)) == {"scan.png": "", "foto.jpg": ""}


def test_a_member_over_the_file_size_cap_is_passed_over(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_MAX_FILE_BYTES", "1000")
    settings.cache_clear()
    raw = _zip([("gross.txt", b"grossquendel " * 200), ("klein.txt", b"kleinquendel")])

    outcome = _run(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert _sections(outcome) == {"gross.txt": "", "klein.txt": "kleinquendel"}


def test_the_member_cap_ends_with_truncated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(archive, "ARCHIVE_MAX_TEXT_MEMBERS", 2)
    raw = _zip([(f"{n}.txt", f"teil{n}quendel".encode("ascii")) for n in range(4)])

    outcome = _run(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert outcome.reason is Reason.TRUNCATED
    assert _sections(outcome) == {"0.txt": "teil0quendel", "1.txt": "teil1quendel"}


def test_the_character_cap_ends_the_loop_before_the_next_member(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FINDLING_MAX_TEXT_CHARS", "60")
    settings.cache_clear()
    calls: list[str] = []
    real = archive._MEMBER_READERS["txt"]

    def counting(path: str) -> ExtractionOutcome:
        calls.append(path)
        return real(path)

    monkeypatch.setitem(archive._MEMBER_READERS, "txt", counting)  # pyright: ignore[reportArgumentType]
    raw = _zip([(f"{n}.txt", f"Teil {n} des Textes mit dem zeichenquendel.".encode("ascii")) for n in range(4)])

    outcome = _run(tmp_path, raw)

    assert outcome.reason is Reason.TRUNCATED
    assert len(outcome.text) == 60
    assert len(calls) == 2


def test_the_time_budget_ends_with_truncated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    readings = iter([0.0, 0.0])
    monkeypatch.setattr(archive, "_now", lambda: next(readings, 1e9))
    raw = _zip([("a.txt", b"erstquendel"), ("b.txt", b"zweitquendel")])

    outcome = _run(tmp_path, raw)

    assert outcome.reason is Reason.TRUNCATED
    assert _sections(outcome) == {"a.txt": "erstquendel"}


def test_an_empty_zip_file_is_empty_text(tmp_path: Path) -> None:
    assert _run(tmp_path, _zip([])) == ExtractionOutcome.skipped(Reason.EMPTY_TEXT)


def test_directories_are_no_sections(tmp_path: Path) -> None:
    raw = _zip([("ordner/", b""), ("ordner/a.txt", b"ordnerquendel")])

    assert _sections(_run(tmp_path, raw)) == {"ordner/a.txt": "ordnerquendel"}


def test_a_broken_member_costs_its_text_and_not_the_file(tmp_path: Path) -> None:
    raw = bytearray(_zip([("kaputt.txt", b"kaputtquendel " * 40), ("heil.txt", b"heilquendel")]))
    data_at = raw.index(b"kaputt.txt") + len("kaputt.txt")
    raw[data_at : data_at + 8] = b"\xff" * 8

    outcome = _run(tmp_path, bytes(raw))

    assert _sections(outcome) == {"kaputt.txt": "", "heil.txt": "heilquendel"}


def test_no_member_name_reaches_the_log(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    cases = [
        _zip([("geheimname.txt", b"inhalt"), ("geheimname.png", b"x")]),
        _patched(_zip([("geheimname.txt", b"inhalt")]), "geheimname.txt", flag=0x1),
        _zip([("geheimname.zip", _zip([("geheimname.zip", _zip([("x.txt", b"x")]))]))]),
        _zip([("geheimname.txt", b"inhalt")])[:-10],
    ]
    for raw in cases:
        _run(tmp_path, raw)

    assert "geheimname" not in caplog.text


def test_the_module_never_writes_under_a_member_name() -> None:
    source = Path(archive.__file__).read_text(encoding="utf-8")

    assert "extractall" not in source
    assert ".extract(" not in source
    assert "PK\\x01\\x02" in source
