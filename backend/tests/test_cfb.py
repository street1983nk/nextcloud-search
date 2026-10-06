"""The OLE sniff of plan 29-08: a compound file under an OOXML name gets its name.

Issue #18 counted 693 xlsx, 105 pptx and 70 docx files that came back as
failed(corrupt), and the one file the reporter checked had the streams
EncryptionInfo and EncryptedPackage: a password protected Office document,
which is a compound file and not a ZIP package. The other case of the same
shape is an old binary document renamed to the new extension.

Every file here is written by ``build_cfb`` in conftest from the specification
([MS-CFB] 2.2 and 2.6), and half of them are hostile on purpose: the reader
walks a structure a stranger wrote, so a cycle, a sector number past the end
and a truncated file all have to end in None, never in an exception and never
in a loop.
"""

from __future__ import annotations

import time
from pathlib import Path
from zipfile import ZipFile

import pytest

from conftest import CFB_END_OF_CHAIN, CFB_STREAM, build_cfb, cfb_entry
from findling.extract import cfb
from findling.extract.cfb import ole_verdict
from findling.extract.errors import ExtractionOutcome, Reason

SHIFTS = pytest.mark.parametrize("sector_shift", [9, 12], ids=["512", "4096"])


def _file(tmp_path: Path, payload: bytes, name: str = "job-4711.part") -> str:
    target = tmp_path / name
    target.write_bytes(payload)
    return str(target)


@SHIFTS
def test_a_password_protected_office_document_is_skipped_encrypted(tmp_path: Path, sector_shift: int) -> None:
    # The two streams budachst found in his file on 2026-10-04, plus the storage
    # every encrypted package carries next to them.
    payload = build_cfb(["\x06DataSpaces", "EncryptionInfo", "EncryptedPackage"], sector_shift=sector_shift)

    assert ole_verdict(_file(tmp_path, payload)) == ExtractionOutcome.skipped(Reason.ENCRYPTED)


@SHIFTS
@pytest.mark.parametrize("stream", ["Workbook", "Book", "WordDocument", "PowerPoint Document"])
def test_an_old_binary_document_is_skipped_legacy_format(tmp_path: Path, sector_shift: int, stream: str) -> None:
    payload = build_cfb(["\x05SummaryInformation", stream], sector_shift=sector_shift)

    assert ole_verdict(_file(tmp_path, payload)) == ExtractionOutcome.skipped(Reason.LEGACY_FORMAT)


def test_encryption_outranks_an_old_stream_in_the_same_directory(tmp_path: Path) -> None:
    payload = build_cfb(["Workbook", "EncryptionInfo", "EncryptedPackage"])

    assert ole_verdict(_file(tmp_path, payload)) == ExtractionOutcome.skipped(Reason.ENCRYPTED)


def test_a_directory_spread_over_several_sectors_is_read_to_its_end(tmp_path: Path) -> None:
    # Four entries per 512 byte sector: the stream that decides sits in the
    # third directory sector, so the chain has to be followed through the FAT.
    names = [f"Stream{number}" for number in range(9)] + ["WordDocument"]

    assert ole_verdict(_file(tmp_path, build_cfb(names))) == ExtractionOutcome.skipped(Reason.LEGACY_FORMAT)


@pytest.mark.parametrize("name", ["MyWorkbookCopy", "Books", "EncryptionInfoBackup", "workbook", "WordDocument2"])
def test_only_whole_names_count_and_never_a_part_of_one(tmp_path: Path, name: str) -> None:
    # The comparison is exact on the whole entry. A substring hit is how a byte
    # scan misfires, and a lower case "workbook" is not what Excel writes.
    payload = build_cfb(["\x05SummaryInformation", name])

    assert ole_verdict(_file(tmp_path, payload)) is None


def test_a_name_that_is_not_a_stream_does_not_count(tmp_path: Path) -> None:
    # A storage called Workbook is not the workbook stream of an .xls file.
    payload = build_cfb([], raw_entries=[cfb_entry("Workbook", object_type=1)])

    assert ole_verdict(_file(tmp_path, payload)) is None


def test_a_zip_package_is_none_and_left_to_the_office_reader(tmp_path: Path) -> None:
    target = tmp_path / "mappe.xlsx"
    with ZipFile(target, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")

    assert ole_verdict(str(target)) is None


@pytest.mark.parametrize("payload", [b"", b"\xd0\xcf\x11", b"PK\x03\x04" + bytes(600)], ids=["empty", "short", "zip"])
def test_a_file_without_the_full_signature_is_none(tmp_path: Path, payload: bytes) -> None:
    assert ole_verdict(_file(tmp_path, payload)) is None


def test_a_missing_file_is_none_and_not_an_exception(tmp_path: Path) -> None:
    assert ole_verdict(str(tmp_path / "gone.part")) is None


@pytest.mark.parametrize("cycle", [{1: 1}, {1: 2, 2: 1}], ids=["self", "two"])
def test_a_fat_chain_with_a_cycle_ends_in_none(tmp_path: Path, cycle: dict[int, int]) -> None:
    names = [f"Stream{number}" for number in range(6)] + ["EncryptionInfo"]
    payload = build_cfb(names, fat=cycle)

    started = time.monotonic()
    verdict = ole_verdict(_file(tmp_path, payload))

    assert verdict is None
    assert time.monotonic() - started < 1


def test_a_directory_longer_than_the_cap_ends_in_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cfb, "_MAX_DIRECTORY_SECTORS", 2)
    names = [f"Stream{number}" for number in range(10)] + ["WordDocument"]

    assert ole_verdict(_file(tmp_path, build_cfb(names))) is None


def test_the_same_directory_under_the_cap_is_read(tmp_path: Path) -> None:
    # The positive control of the case above: the file itself is sound.
    names = [f"Stream{number}" for number in range(10)] + ["WordDocument"]

    assert ole_verdict(_file(tmp_path, build_cfb(names))) == ExtractionOutcome.skipped(Reason.LEGACY_FORMAT)


@pytest.mark.parametrize(
    ("first_directory", "fat_sector_count"),
    [(0x7FFFFFF0, 1), (0x7FFFFFF0, 0xFFFFFFFF), (CFB_END_OF_CHAIN, 1), (1, 0)],
    ids=["directory-past-the-end", "absurd-fat-count", "no-directory", "no-fat"],
)
def test_absurd_header_fields_end_in_none(tmp_path: Path, first_directory: int, fat_sector_count: int) -> None:
    payload = build_cfb(["EncryptionInfo"], first_directory=first_directory, fat_sector_count=fat_sector_count)

    assert ole_verdict(_file(tmp_path, payload)) is None


def test_an_absurd_fat_count_alone_reads_no_more_than_the_header_difat(tmp_path: Path) -> None:
    # 0xFFFFFFFF FAT sectors declared, one used: the reader takes the entries of
    # the header DIFAT it needs and never tries to honour the declared count.
    payload = build_cfb(["EncryptionInfo"], fat_sector_count=0xFFFFFFFF)

    assert ole_verdict(_file(tmp_path, payload)) == ExtractionOutcome.skipped(Reason.ENCRYPTED)


@SHIFTS
def test_a_truncated_compound_file_ends_in_none(tmp_path: Path, sector_shift: int) -> None:
    names = [f"Stream{number}" for number in range(40)] + ["EncryptionInfo"]
    whole = build_cfb(names, sector_shift=sector_shift)

    assert ole_verdict(_file(tmp_path, whole[: len(whole) - 100])) is None


@pytest.mark.parametrize("shift", [0, 8, 10, 16, 0xFFFF])
def test_a_sector_shift_outside_the_specification_ends_in_none(tmp_path: Path, shift: int) -> None:
    payload = bytearray(build_cfb(["EncryptionInfo"]))
    payload[0x1E:0x20] = shift.to_bytes(2, "little")

    assert ole_verdict(_file(tmp_path, bytes(payload))) is None


@pytest.mark.parametrize("length", [0, 1, 66, 0xFFFF], ids=["zero", "odd", "over-64", "huge"])
def test_a_stream_entry_with_an_impossible_name_length_ends_in_none(tmp_path: Path, length: int) -> None:
    payload = build_cfb([], raw_entries=[cfb_entry("EncryptionInfo", CFB_STREAM, name_length=length)])

    assert ole_verdict(_file(tmp_path, payload)) is None


def test_a_name_that_is_no_valid_utf16_ends_in_none(tmp_path: Path) -> None:
    # A lone high surrogate, then the terminator.
    broken = bytearray(cfb_entry("ab"))
    broken[0:2] = b"\x00\xd8"
    payload = build_cfb([], raw_entries=[bytes(broken)])

    assert ole_verdict(_file(tmp_path, payload)) is None


def test_a_directory_chain_past_the_header_difat_is_the_named_gap(tmp_path: Path) -> None:
    # 109 FAT sectors of 128 entries each cover sector numbers below 13952. The
    # directory jumps to sector 13952, whose successor sits in FAT sector 110,
    # which only a DIFAT sector would name: the reader does not follow those
    # (module docstring, "Known gap") and falls back instead of guessing.
    far = 109 * (512 // 4)
    payload = bytearray(build_cfb(["Stream0", "Stream1", "Stream2"], fat={1: far}, fat_sector_count=110))
    second = build_cfb(["EncryptionInfo", "EncryptedPackage", "Stream3"])[1024:1536]
    offset = (far + 1) * 512
    payload.extend(bytes(offset - len(payload)))
    payload.extend(second)

    assert ole_verdict(_file(tmp_path, bytes(payload))) is None


def test_only_the_directory_is_read_and_never_the_whole_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Eight MB of stream content behind a directory of one sector: the sniff
    # reads the header, one FAT sector and one directory sector.
    payload = build_cfb(["WordDocument"]) + bytes(8 * 1024 * 1024)
    path = _file(tmp_path, payload)
    requested: list[int] = []
    real_read = cfb._read_at  # noqa: SLF001 - counting the reads is the point

    def counting(handle: cfb.BinaryIO, offset: int, length: int, size: int) -> bytes:
        requested.append(length)
        return real_read(handle, offset, length, size)

    monkeypatch.setattr(cfb, "_read_at", counting)

    assert ole_verdict(path) == ExtractionOutcome.skipped(Reason.LEGACY_FORMAT)
    assert sum(requested) <= 3 * 512
