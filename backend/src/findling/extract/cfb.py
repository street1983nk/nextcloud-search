"""The OLE sniff: an Office file that is a compound file and not a ZIP package.

A file that arrives as DOCX, XLSX or PPTX and starts with the compound file
signature ``d0cf11e0a1b11ae1`` is not a broken package, it is one of two other
things. Either it is password protected, because an encrypted Office document is
a compound file carrying the streams ``EncryptionInfo`` and ``EncryptedPackage``,
or it is an old binary document (``Workbook``/``Book`` for .xls, ``WordDocument``
for .doc, ``PowerPoint Document`` for .ppt) under the new extension. Both used to
travel into the ZIP readers and come out as failed(corrupt), which is the wrong
word for a file that is perfectly whole (issue #18, decision D-29-08). This
module gives them their name before any reader is asked, in the shape of
office._too_large_to_read: a verdict or None, and None means "the old way".

**Only the directory is read, never the content.** A byte scan of the whole file
for the four names would read megabytes per file and could hit inside the text
of a legacy document. The compound file directory is a short chain of sectors
that lists every stream by name, so the reader takes the 512 byte header, the
FAT sectors the chain passes through and the directory sectors themselves.
Names are compared exactly and as a whole: a stream called ``MyWorkbookCopy``
is not a workbook. Encryption is checked first, so a directory that somehow
names both is reported as the stronger statement.

**The file is a stranger's.** Every sector number is checked against the file
size before it is read, the chain keeps a set of visited sectors against a
cycle and a hard cap on its length, and every read or structure error, of
whatever kind, ends in None. The sniff must never be the reason a file that
would have been reported before now raises.

**Known gap, deliberately left open.** Only the 109 FAT sector locations of the
header DIFAT are followed. A directory sector whose FAT entry lies further out
(sector numbers from 13952 on with 512 byte sectors, which needs a file of about
7 MB with the directory at its end) is not chased through DIFAT sectors; the
sniff gives up and the file takes the old way. Real Office files write their
directory early, and a second chain to walk is a second place to get wrong.

The offsets come from [MS-CFB] 2.2 (Compound File Header) and 2.6 (Directory
Entry) and were checked against the specification before this module was
written; the tests build their files from the same sections.
"""

from __future__ import annotations

import struct
from typing import BinaryIO, Final

from findling.extract.errors import ExtractionOutcome, Reason

_SIGNATURE: Final = bytes.fromhex("d0cf11e0a1b11ae1")
_HEADER_BYTES: Final = 512
_SECTOR_SHIFT_AT: Final = 0x1E
_FAT_SECTOR_COUNT_AT: Final = 0x2C
_FIRST_DIRECTORY_AT: Final = 0x30
_DIFAT_AT: Final = 0x4C
_HEADER_DIFAT_ENTRIES: Final = 109

# Version 3 writes 512 byte sectors (shift 9), version 4 writes 4096 (shift 12).
# The specification allows nothing else, and a shift outside the two would turn
# every offset below into a guess.
_ALLOWED_SHIFTS: Final = frozenset({9, 12})

# Sector numbers above this are markers (FREESECT, ENDOFCHAIN, FATSECT, ...).
_MAX_REGULAR_SECTOR: Final = 0xFFFFFFFA
_END_OF_CHAIN: Final = 0xFFFFFFFE

_ENTRY_BYTES: Final = 128
_NAME_FIELD_BYTES: Final = 64
_NAME_LENGTH_AT: Final = 0x40
_OBJECT_TYPE_AT: Final = 0x42
_STREAM_OBJECT: Final = 2

# How many directory sectors the chain may have before the sniff gives up. Real
# Office files have a handful: an encrypted package has one or two, a large
# legacy document with embedded objects a few dozen. 1024 sectors are 4096
# entries at 512 bytes and 32768 at 4096, far past any of them, and still bound
# the work on a hostile file to at most 4 MiB of directory reads.
_MAX_DIRECTORY_SECTORS: Final = 1024

_ENCRYPTED_STREAMS: Final = frozenset({"EncryptionInfo", "EncryptedPackage"})
_LEGACY_STREAMS: Final = frozenset({"Workbook", "Book", "WordDocument", "PowerPoint Document"})


class _Malformed(Exception):
    """A structure the specification does not allow; ends the sniff in None."""


def ole_verdict(path: str) -> ExtractionOutcome | None:
    """A verdict for a compound file under an OOXML name, or None for the old way.

    None covers three cases on purpose: the file is no compound file at all (the
    ordinary ZIP package), it is one without any of the six names, or its
    structure could not be read within the caps. In all three the Office reader
    decides, exactly as before this module existed.
    """
    try:
        with open(path, "rb") as handle:
            size = handle.seek(0, 2)
            names = _stream_names(handle, size)
    except (OSError, struct.error, UnicodeDecodeError, ValueError, _Malformed):
        return None
    if names is None:
        return None
    if names & _ENCRYPTED_STREAMS:
        return ExtractionOutcome.skipped(Reason.ENCRYPTED)
    if names & _LEGACY_STREAMS:
        return ExtractionOutcome.skipped(Reason.LEGACY_FORMAT)
    return None


def _read_at(handle: BinaryIO, offset: int, length: int, size: int) -> bytes:
    """Exactly ``length`` bytes at ``offset``, or _Malformed if the file is shorter."""
    if offset < 0 or offset + length > size:
        raise _Malformed
    handle.seek(offset)
    data = handle.read(length)
    if len(data) != length:
        raise _Malformed
    return data


def _stream_names(handle: BinaryIO, size: int) -> set[str] | None:
    """Every stream name of the directory, or None when this is no compound file."""
    if size < _HEADER_BYTES:
        return None
    header = _read_at(handle, 0, _HEADER_BYTES, size)
    if header[: len(_SIGNATURE)] != _SIGNATURE:
        return None

    (shift,) = struct.unpack_from("<H", header, _SECTOR_SHIFT_AT)
    if shift not in _ALLOWED_SHIFTS:
        raise _Malformed
    sector = 1 << shift
    (fat_count,) = struct.unpack_from("<I", header, _FAT_SECTOR_COUNT_AT)
    (current,) = struct.unpack_from("<I", header, _FIRST_DIRECTORY_AT)
    difat = struct.unpack_from(f"<{_HEADER_DIFAT_ENTRIES}I", header, _DIFAT_AT)
    fat_locations = difat[: min(fat_count, _HEADER_DIFAT_ENTRIES)]
    chain = _Chain(handle, size, sector, fat_locations)

    names: set[str] = set()
    visited: set[int] = set()
    while current != _END_OF_CHAIN:
        if current > _MAX_REGULAR_SECTOR or current in visited or len(visited) >= _MAX_DIRECTORY_SECTORS:
            raise _Malformed
        visited.add(current)
        names.update(_names_in(chain.sector(current)))
        current = chain.next_of(current)
    return names


class _Chain:
    """Sectors and FAT lookups of one open file, every location checked first."""

    def __init__(self, handle: BinaryIO, size: int, sector: int, fat_locations: tuple[int, ...]) -> None:
        self._handle = handle
        self._size = size
        self._sector = sector
        self._fat_locations = fat_locations
        self._fat_cache: dict[int, tuple[int, ...]] = {}

    def sector(self, number: int) -> bytes:
        """The bytes of sector ``number``; sector 0 starts right after the header sector."""
        if number > _MAX_REGULAR_SECTOR:
            raise _Malformed
        return _read_at(self._handle, (number + 1) * self._sector, self._sector, self._size)

    def next_of(self, number: int) -> int:
        """The FAT entry of ``number``, read only from the FAT sector that holds it."""
        per_sector = self._sector // 4
        index = number // per_sector
        if index >= len(self._fat_locations):
            # Past the header DIFAT (or past the declared FAT): the named gap.
            raise _Malformed
        table = self._fat_cache.get(index)
        if table is None:
            table = struct.unpack(f"<{per_sector}I", self.sector(self._fat_locations[index]))
            self._fat_cache[index] = table
        return table[number % per_sector]


def _names_in(directory_sector: bytes) -> list[str]:
    """The names of the stream entries in one directory sector."""
    names: list[str] = []
    for start in range(0, len(directory_sector), _ENTRY_BYTES):
        entry = directory_sector[start : start + _ENTRY_BYTES]
        if entry[_OBJECT_TYPE_AT] != _STREAM_OBJECT:
            continue
        (length,) = struct.unpack_from("<H", entry, _NAME_LENGTH_AT)
        # The length counts the terminating null and is even, at most 64 bytes.
        if length < 2 or length > _NAME_FIELD_BYTES or length % 2:
            raise _Malformed
        names.append(entry[: length - 2].decode("utf-16-le"))
    return names
