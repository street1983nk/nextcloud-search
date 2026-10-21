"""The OLE sniff: an Office file that is a compound file and not a ZIP package.

A file that arrives as DOCX, XLSX or PPTX and starts with the compound file
signature ``d0cf11e0a1b11ae1`` is not a broken package, it is one of two other
things. Either it is password protected, because an encrypted Office document is
a compound file carrying the streams ``EncryptionInfo`` and ``EncryptedPackage``,
or it is an old binary document (``Workbook``/``Book`` for .xls, ``WordDocument``
for .doc, ``PowerPoint Document`` for .ppt) under the new extension. Both used to
travel into the ZIP readers and come out as failed(corrupt), which is the wrong
word for a file that is perfectly whole (issue #18, decision D-29-08). This
module gives them their name before any reader is asked: a kind or None, and
None means "the old way".

**Since 1.5 (plan 31-06) Word and Excel are read**, by the readers of .doc and
.xls, and only PowerPoint and the rest keep the verdict legacy_format. Which
reader a file goes to is decided by the streams at the top of its directory
tree, the level both readers open: a .doc with an embedded Excel chart carries
a Workbook stream in a storage further down and is still a Word document. A
known name that is in the directory but not reachable from the root is such an
embedded object, or a tree too broken to tell; it stays legacy_format, the
verdict it had before. The stream decides and not the name the file arrived
under: a Word file under .xlsx is read as Word (T-31-19).

**Only the directory is read, never the content.** A byte scan of the whole file
for the four names would read megabytes per file and could hit inside the text
of a legacy document. The compound file directory is a short chain of sectors
that lists every stream by name, so the reader takes the 512 byte header, the
FAT sectors the chain passes through and the directory sectors themselves.
Names are compared exactly and as a whole: a stream called ``MyWorkbookCopy``
is not a workbook. Encryption is checked first, so a directory that somehow
names both is reported as the stronger statement. The top of the tree is found
from the child of the root entry over the left and right siblings, with a set
of visited entries, so a cycle in the tree ends the walk and not the sniff.

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

**The chain checks of the legacy readers** live here as well, so that the .doc
reader (plan 31-05) and the .xls reader (plan 31-06) hold a stranger's compound
file to the same rules. Both open it with olefile, and olefile has two gaps,
both measured on 0.47. It appends every FAT sector to an array by copying it,
so a FAT declared far past the file costs time with the square of the count
(20 000 sectors in 180 kB: 29 s) before it reports anything; check_fat_size
refuses that from the header alone. And it does not notice a cycle inside the
declared length of a stream: the repeated sectors come back as content. xlrd,
which has a compound file reader of its own, is worse at that spot: it follows
a chain in the mini stream without any record of the sectors it has seen, so a
cycle there is a loop without end (plan 31-06, measured). walk_stream follows
the chain of one stream, and of the mini stream it may live in, once with a set
of visited sectors and against the length of the table, which olefile has cut
to the size of the file. A defect is CorruptCompoundFile.

**A cycle is CompoundCycle (D-36-17, plan 36-09).** A sector chain of a valid
compound file never reaches a sector twice, so every cycle is an attack
signature and not damage: in the chain of a stream (FAT), of a small stream
(MiniFAT), including a chain that runs on past the end of its stream into a
cycle, in the chain of DIFAT sectors, in the chain of directory sectors and in
the tree of directory entries. CompoundCycle is a subclass of
CorruptCompoundFile, so a caller that knows only the parent keeps its verdict;
the legacy readers catch it first and answer skipped(blocked_malicious) with
the detail "cfb_cycle" (36-WORTLAUT.md A3). olefile notices a cycle in the
DIFAT chain and in the tree itself, but as an OleFileError like any other
defect, so check_cycles walks both before olefile opens the file. Every other
defect stays what it was: check_cycles raises for a cycle and for nothing
else, and leaves every other oddity to olefile. The sniff is unchanged: a
cycle ends its walk and the sniff answers None.
"""

from __future__ import annotations

import array
import struct
from pathlib import Path
from typing import Any, BinaryIO, Final, Literal, NamedTuple

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
_LEFT_SIBLING_AT: Final = 0x44  # right sibling at 0x48, child at 0x4C
_STREAM_OBJECT: Final = 2

# How many directory sectors the chain may have before the sniff gives up. Real
# Office files have a handful: an encrypted package has one or two, a large
# legacy document with embedded objects a few dozen. 1024 sectors are 4096
# entries at 512 bytes and 32768 at 4096, far past any of them, and still bound
# the work on a hostile file to at most 4 MiB of directory reads.
_MAX_DIRECTORY_SECTORS: Final = 1024

_ENCRYPTED_STREAMS: Final = frozenset({"EncryptionInfo", "EncryptedPackage"})
_LEGACY_STREAMS: Final = frozenset({"Workbook", "Book", "WordDocument", "PowerPoint Document"})
_WORD_STREAM: Final = "WordDocument"
_EXCEL_STREAMS: Final = frozenset({"Workbook", "Book"})

# What the sniff says about a compound file: password protected, a Word or an
# Excel document to read, or an old binary file this image does not read
# (PowerPoint, or a known name outside the tree of the root).
OleKind = Literal["encrypted", "word", "excel", "legacy"]


# How many FAT sectors more than the file needs are still accepted: one, for a
# writer that allocates the next FAT sector before the sectors it describes.
_FAT_SLACK_SECTORS: Final = 1


class _Malformed(Exception):
    """A structure the specification does not allow; ends the sniff in None."""


class _Entry(NamedTuple):
    """One directory entry as the sniff needs it: the name of a stream and the tree links."""

    stream_name: str | None
    left: int
    right: int
    child: int


class CorruptCompoundFile(Exception):
    """A sector chain or FAT of a compound file that the specification does not allow."""


class CompoundCycle(CorruptCompoundFile):
    """A sector chain or the directory tree of a compound file reaches an element twice.

    A valid compound file cannot have one, so a cycle is an attack signature
    (D-36-17) and the legacy readers report it as cfb_cycle.
    """


_DIFAT_START_AT: Final = 0x44


def check_cycles(path: str) -> None:
    """Raise CompoundCycle for a cycle in the DIFAT chain, the directory chain or the directory tree.

    Run before olefile opens the file, after check_fat_size. Only a cycle
    raises: a link out of the file, a short read or any other structure the
    walk cannot follow ends the check silently, so that olefile reports it as
    before. The walks are bounded by the sectors of the file and the entries of
    the directory.
    """
    try:
        with Path(path).open("rb") as handle:
            size = handle.seek(0, 2)
            header = _read_at(handle, 0, _HEADER_BYTES, size)
            if header[: len(_SIGNATURE)] != _SIGNATURE:
                return
            (shift,) = struct.unpack_from("<H", header, _SECTOR_SHIFT_AT)
            if shift not in _ALLOWED_SHIFTS:
                return
            _walk_difat(handle, size, 1 << shift, header)
            entries = _directory(handle, size)
    except (OSError, struct.error, UnicodeDecodeError, ValueError, _Malformed):
        return
    if entries:
        _walk_tree(entries)


def _walk_difat(handle: BinaryIO, size: int, sector: int, header: bytes) -> None:
    """Follow the chain of DIFAT sectors to its end; a sector seen twice is a cycle.

    The last four bytes of a DIFAT sector name the next one ([MS-CFB] 2.5). The
    chain is followed whatever the count in the header says, because a link is
    what a reader follows; it ends at the first marker (ENDOFCHAIN, FREESECT),
    and a link out of the file ends it through _read_at.
    """
    (current,) = struct.unpack_from("<I", header, _DIFAT_START_AT)
    seen: set[int] = set()
    sectors_in_file = size // sector
    while current <= _MAX_REGULAR_SECTOR:
        if current in seen:
            raise CompoundCycle
        if len(seen) > sectors_in_file:
            return
        seen.add(current)
        link = _read_at(handle, (current + 1) * sector + sector - 4, 4, size)
        (current,) = struct.unpack("<I", link)


def _walk_tree(entries: list[_Entry]) -> None:
    """Walk the directory tree from the root; an entry reached again below itself is a cycle.

    Depth first over child, left and right, with the entries on the current
    path marked, so an entry shared by two branches is not mistaken for a
    cycle; a link outside the directory (NOSTREAM among them) ends its branch.
    Iterative, so a deep hostile tree costs a list and not the stack.
    """
    on_path: set[int] = set()
    done: set[int] = set()
    stack: list[tuple[int, bool]] = [(0, False)]
    while stack:
        number, leaving = stack.pop()
        if leaving:
            on_path.discard(number)
            done.add(number)
            continue
        if number >= len(entries) or number in done:
            continue
        if number in on_path:
            raise CompoundCycle
        on_path.add(number)
        stack.append((number, True))
        entry = entries[number]
        stack.extend((link, False) for link in (entry.child, entry.left, entry.right))


def check_fat_size(path: str) -> None:
    """Refuse a FAT that declares more sectors than the file could need (see above).

    Run before olefile opens the file. Raises CorruptCompoundFile.
    """
    with Path(path).open("rb") as handle:
        size = handle.seek(0, 2)
        handle.seek(0)
        header = handle.read(_HEADER_BYTES)
    if len(header) != _HEADER_BYTES:
        raise CorruptCompoundFile
    (shift,) = struct.unpack_from("<H", header, _SECTOR_SHIFT_AT)
    if shift not in _ALLOWED_SHIFTS:
        raise CorruptCompoundFile
    sector = 1 << shift
    sectors_in_file = -(-size // sector) - 1
    needed = -(-sectors_in_file // (sector // 4))
    (declared,) = struct.unpack_from("<I", header, _FAT_SECTOR_COUNT_AT)
    if declared > needed + _FAT_SLACK_SECTORS:
        raise CorruptCompoundFile


def walk_stream(ole: object, name: str) -> None:
    """Follow the chain of the top level stream ``name`` once (see above).

    ``ole`` is an open olefile.OleFileIO. Its chain tables (fat, minifat, the
    sector sizes, the start and size of an entry) are not part of its typed
    interface in typeshed; they are read untyped and checked for their type
    before use. olefile is pinned at 0.47, and the LibreOffice fixtures of both
    readers turn red if a version moves them. Raises CorruptCompoundFile.
    """
    internals: Any = ole
    root = internals.root
    if root is None:
        raise CorruptCompoundFile
    entry = root.kids_dict.get(name.lower())
    if entry is None:
        raise CorruptCompoundFile
    if entry.is_minifat:
        if internals.minifat is None:
            # olefile reads the MiniFAT when the first small stream is opened;
            # a caller that has not read one yet gets it read here.
            internals.loadminifat()
        _visit_once(internals.fat, root.isectStart, root.size, internals.sectorsize)
        _visit_once(internals.minifat, entry.isectStart, entry.size, internals.minisectorsize)
    else:
        _visit_once(internals.fat, entry.isectStart, entry.size, internals.sectorsize)


def _visit_once(table: object, start: object, size: object, sector: object) -> None:
    """Follow the links of a stream of ``size`` bytes; a sector seen twice is a cycle.

    The chain has to end where the stream ends, with ENDOFCHAIN ([MS-CFB],
    FAT and MiniFAT sectors).
    olefile reads only as many sectors as the size asks for and would not care,
    but xlrd follows a chain to its end marker whatever the size says, so a
    link past the last sector is where a cycle hides from a walk bound by size.

    A sector seen twice is CompoundCycle. A chain that does not end with its
    stream is followed on, bounded by the length of the table, to tell the two
    defects apart: one that runs into a sector it already passed is a cycle,
    one that ends anywhere else (another stream, a marker, a link out of the
    table) stays CorruptCompoundFile.
    """
    if not (
        isinstance(table, array.array) and isinstance(start, int) and isinstance(size, int) and isinstance(sector, int)
    ):
        raise CorruptCompoundFile
    seen: set[int] = set()
    current = start
    for _ in range(-(-size // sector)):
        if current in seen:
            raise CompoundCycle
        if current >= len(table):
            raise CorruptCompoundFile
        seen.add(current)
        current = table[current]
    if current != _END_OF_CHAIN:
        _run_on(table, current, seen)
        raise CorruptCompoundFile


def _run_on(table: array.array[int], current: int, seen: set[int]) -> None:
    """Follow a chain past the end of its stream; CompoundCycle if it comes back to a sector it passed."""
    while 0 <= current < len(table):
        if current in seen:
            raise CompoundCycle
        seen.add(current)
        current = table[current]


def ole_kind(path: str) -> OleKind | None:
    """The kind of a compound file under an OOXML name, or None for the old way.

    None covers three cases on purpose: the file is no compound file at all (the
    ordinary ZIP package), it is one without any of the six names, or its
    structure could not be read within the caps. In all three the Office reader
    decides, exactly as before this module existed.
    """
    try:
        with open(path, "rb") as handle:
            size = handle.seek(0, 2)
            entries = _directory(handle, size)
    except (OSError, struct.error, UnicodeDecodeError, ValueError, _Malformed, CompoundCycle):
        return None
    if entries is None:
        return None
    names = {entry.stream_name for entry in entries if entry.stream_name is not None}
    top = _top_level_names(entries)
    if names & _ENCRYPTED_STREAMS:
        return "encrypted"
    if _WORD_STREAM in top:
        return "word"
    if top & _EXCEL_STREAMS:
        return "excel"
    if names & _LEGACY_STREAMS:
        return "legacy"
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


def _directory(handle: BinaryIO, size: int) -> list[_Entry] | None:
    """Every entry of the directory in order, or None when this is no compound file."""
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

    entries: list[_Entry] = []
    visited: set[int] = set()
    while current != _END_OF_CHAIN:
        if current in visited:
            # The directory chain comes back to a sector: a cycle (plan 36-09).
            # The sniff answers None for it like for every other defect.
            raise CompoundCycle
        if current > _MAX_REGULAR_SECTOR or len(visited) >= _MAX_DIRECTORY_SECTORS:
            raise _Malformed
        visited.add(current)
        entries += _entries_in(chain.sector(current))
        current = chain.next_of(current)
    return entries


def _top_level_names(entries: list[_Entry]) -> set[str]:
    """The stream names directly below the root: its child and that one's siblings.

    The entry number is the position in the directory ([MS-CFB] 2.6), the root
    is entry 0. A link outside the directory (NOSTREAM among them) ends its
    branch; a link already followed ends it too, so the walk is bounded by the
    number of entries whatever the tree looks like.
    """
    if not entries:
        return set()
    names: set[str] = set()
    visited: set[int] = set()
    pending = [entries[0].child]
    while pending:
        number = pending.pop()
        if number >= len(entries) or number in visited:
            continue
        visited.add(number)
        entry = entries[number]
        if entry.stream_name is not None:
            names.add(entry.stream_name)
        pending += [entry.left, entry.right]
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


def _entries_in(directory_sector: bytes) -> list[_Entry]:
    """The entries of one directory sector, with the names of the stream entries."""
    entries: list[_Entry] = []
    for start in range(0, len(directory_sector), _ENTRY_BYTES):
        entry = directory_sector[start : start + _ENTRY_BYTES]
        left, right, child = struct.unpack_from("<3I", entry, _LEFT_SIBLING_AT)
        name = None
        if entry[_OBJECT_TYPE_AT] == _STREAM_OBJECT:
            (length,) = struct.unpack_from("<H", entry, _NAME_LENGTH_AT)
            # The length counts the terminating null and is even, at most 64 bytes.
            if length < 2 or length > _NAME_FIELD_BYTES or length % 2:
                raise _Malformed
            name = entry[: length - 2].decode("utf-16-le")
        entries.append(_Entry(name, left, right, child))
    return entries
