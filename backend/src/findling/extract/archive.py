"""ZIP files as documents: the text of every member, within measured limits.

FMT-02. One ZIP file is one hit (D-30-03): its text is the text of all members
together, each in a section of its own that starts with ARCHIVE_MEMBER_MARK
(U+001C), the display name of the member and a line break. The mark is removed
from every member text, so the snippet code of plan 31-09 can look for the last
mark before a hit and name the inner file without a field in the schema. Members
without readable text (pictures, unknown extensions, encrypted members) still
get their section, with the name alone: a search for the name of an inner file
finds the ZIP file.

**Three stages, and each one ends the whole ZIP file as skipped(archive_limit).**
The limits and the measurements behind them are in config.py and in
docs/measurements/2026-10-formate-v15/README.md, section "ZIP-Grenzwerte"
(D-31-07). Three attack signatures end it as skipped(blocked_malicious) with
their code instead (D-36-17, 36-WORTLAUT.md A3); a limit alone never does:

* ``zip_ratio``: a member from ARCHIVE_RATIO_MIN_BYTES on declares more than
  ARCHIVE_MALICIOUS_RATIO times its compressed size. Over ARCHIVE_MAX_RATIO up
  to and including that number it stays archive_limit (answer O12).
* ``zip_overlap``: zipfile reports overlapping entries, by its refusal or by its
  warning about two entries at one local header, on every level (answer O2).
* ``zip_traversal``: the raw name of a member, as the directory carries it,
  has a ``..`` segment (``/`` or ``\\`` as separator), starts with a separator
  or a drive letter, or holds NUL (answer O5). Judged before any member of the
  level is read; nothing is ever written under a member name anyway.

1. *The central directory, before zipfile sees it.* ``ZipFile()`` builds one
   ZipInfo per directory header before any loop of ours can count anything,
   and it reads the directory by its byte length: the entry count in the end
   record is never consulted (blocker 2 of the plan check). A count of 5 over
   10 001 real headers would hand zipfile all of them. So the end record is
   located exactly as CPython 3.13 does it (``_EndRecData``,
   ``_EndRecData64``, ``_RealGetContents``), the length of the directory is
   checked, and the headers are counted with zipfile's own loop, block by
   block, up to one past the limit. Only then is ZipFile opened.
2. *The declarations.* The declared uncompressed sizes are summed, each member
   from ARCHIVE_RATIO_MIN_BYTES on is held to ARCHIVE_MALICIOUS_RATIO and then
   to ARCHIVE_MAX_RATIO, the raw names are held to the traversal rule, and an
   inner ZIP file beyond ARCHIVE_MAX_DEPTH ends the whole file (a quine ends
   here). The order is the one of answer O7: a single lying size over the sum
   is a limit, not a ratio.
3. *Reading with a count.* A member is streamed into a scratch file named by a
   running number, never by its name, read by the reader its extension
   selects, and deleted at once. zipfile holds every read to the declared size
   (and refuses overlapping entries, CVE-2024-0450, but only warns about two
   entries at the same header, a warning that quotes the name and is therefore
   silenced in _copy); the bytes are counted again against the same budget.

**One budget for all levels (finding 10).** Entries, directory bytes, declared
and read bytes and the members handed to a reader are drawn from one
_ArchiveBudget that is created for the outer ZIP file and handed down to every
inner one. Fifty inner ZIP files just under a limit each are one ZIP file over
it; a budget per level would let them pass.

**No OCR.** One page of tesseract costs 300 to 600 MB and seconds, and the
extraction deadline of 120 s holds for the whole ZIP file. Pictures stay names,
a PDF is read for its text layer only (a scan ends as a name).

**What is not a limit.** A member over ``max_file_bytes`` is passed over (name
only) and the ZIP file goes on, as does a member a reader cannot read; the
member cap (ARCHIVE_MAX_TEXT_MEMBERS) and the time share of the deadline end
the loop with indexed(truncated), because a kill would lose everything read so
far. All members encrypted is skipped(encrypted), a broken directory
failed(corrupt).

This module does not log. Names and texts of members are content of a user's
file, and an exception message of zipfile quotes the member name: only class
names leave this module, as the detail of a failure.
"""

from __future__ import annotations

import lzma
import os
import re
import struct
import time
import warnings
import zlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Final
from zipfile import BadZipFile, ZipFile, ZipInfo

from findling import config
from findling.config import (
    ARCHIVE_MALICIOUS_RATIO,
    ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES,
    ARCHIVE_MAX_DEPTH,
    ARCHIVE_MAX_ENTRIES,
    ARCHIVE_MAX_RATIO,
    ARCHIVE_MAX_TEXT_MEMBERS,
    ARCHIVE_MEMBER_MARK,
    ARCHIVE_RATIO_MIN_BYTES,
    ARCHIVE_TIME_SHARE,
    EXTRACT_ARCHIVE_TOTAL_MAX_BYTES,
)
from findling.extract.dispatch import cap_text, extension_of
from findling.extract.errors import ExtractionOutcome, Reason, State
from findling.extract.mail import clean_display_name

# PKWARE APPNOTE 6.3.10: end of central directory record (4.3.16, 22 bytes plus
# a comment of at most 65 535), ZIP64 end record (4.3.14, 56 bytes fixed) and
# its locator (4.3.15, 20 bytes, directly in front of the end record), central
# directory header (4.3.12, 46 bytes fixed, then name, extra field, comment).
_END = b"PK\x05\x06"
_END64 = b"PK\x06\x06"
_LOCATOR64 = b"PK\x06\x07"
_CENTRAL = b"PK\x01\x02"
_END_SIZE = 22
_END64_SIZE = 56
_LOCATOR64_SIZE = 20
_CENTRAL_SIZE = 46
_COMMENT_MAX = 0xFFFF

# The block the directory is read in while it is counted.
_READ_BLOCK = 64 * 1024

# Compression methods zipfile reads: stored, deflate, bzip2, lzma. Deflate64 (9)
# and AES (99) raise NotImplementedError inside zipfile; such a member stays a name.
_READABLE_METHODS: Final = frozenset({0, 8, 12, 14})
_ENCRYPTED_FLAG = 0x1

# What reading a member can raise when its data is broken, as opposed to its
# declarations: the member keeps its name and loses its text.
_BROKEN_MEMBER: Final = (BadZipFile, zlib.error, EOFError, lzma.LZMAError, OSError)

# The first words of zipfile's overlap refusal (CVE-2024-0450). The message is
# compared, never logged: it quotes the member name.
_OVERLAP = "Overlapped entries"

# The signature codes this module raises (36-WORTLAUT.md A3).
_ZIP_RATIO: Final = "zip_ratio"
_ZIP_OVERLAP: Final = "zip_overlap"
_ZIP_TRAVERSAL: Final = "zip_traversal"

# A drive letter in front of a raw member name; the separators of both worlds.
_DRIVE: Final = re.compile(r"[A-Za-z]:")
_SEPARATORS: Final = re.compile(r"[/\\]")


class CorruptDirectory(Exception):
    """The end record or the central directory is not what zipfile could read."""


class OverLimit(Exception):
    """A limit of D-31-07 is reached, or an attack signature of D-36-17 is found.

    Without a signature the whole ZIP file is skipped(archive_limit). With one
    it is skipped(blocked_malicious), and ``signature`` is the detail code: a
    code of the closed list of 36-WORTLAUT.md A3 and never a name, a size or a
    message, because it leaves the child as the detail of the verdict.
    """

    def __init__(self, signature: str | None = None) -> None:
        super().__init__()
        self.signature = signature


class _Stop(Exception):
    """The member cap or the time share is reached; what was read so far is kept."""


# What opening a ZIP file can raise beyond the count: our own verdict on the
# directory, and what zipfile raises while it builds the ZipInfo objects (a bad
# extra field, an unknown format version, a name flagged UTF-8 that is not).
_UNREADABLE_DIRECTORY: Final = (CorruptDirectory, BadZipFile, NotImplementedError, UnicodeDecodeError)


def _is_overlap(error: Exception) -> bool:
    """True for zipfile's refusal of overlapping entries. The message is compared, never logged."""
    return isinstance(error, BadZipFile) and str(error).startswith(_OVERLAP)


def _is_traversal(raw_name: str) -> bool:
    """True for a raw member name that climbs out of the folder it would be unpacked to.

    A ``..`` segment between ``/`` or ``\\``, a separator or a drive letter in
    front, or a NUL anywhere: no packer writes such a name, it aims at an
    unpacker that writes under it (D-36-17, answer O5). The raw name is the
    one the directory carries (``ZipInfo.orig_filename``): zipfile cuts
    ``ZipInfo.filename`` at NUL. Dots that are no segment of their own
    (``..x.txt``, ``a..b``) are names like any other.
    """
    if "\x00" in raw_name or raw_name.startswith(("/", "\\")) or _DRIVE.match(raw_name):
        return True
    return ".." in _SEPARATORS.split(raw_name)


@dataclass(slots=True)
class _ArchiveBudget:
    """What is left for the whole ZIP file, shared by every nesting level."""

    entries: int
    directory_bytes: int
    declared_bytes: int
    read_bytes: int
    text_members: int
    deadline: float
    scratch: str
    serial: int = 0
    files: int = 0
    encrypted: int = 0
    chars: int = 0

    @classmethod
    def start(cls, path: str) -> _ArchiveBudget:
        share = ARCHIVE_TIME_SHARE * config.settings().extract_timeout_seconds
        return cls(
            entries=ARCHIVE_MAX_ENTRIES,
            directory_bytes=ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES,
            declared_bytes=EXTRACT_ARCHIVE_TOTAL_MAX_BYTES,
            read_bytes=EXTRACT_ARCHIVE_TOTAL_MAX_BYTES,
            text_members=ARCHIVE_MAX_TEXT_MEMBERS,
            deadline=_now() + share,
            scratch=path,
        )

    def take_directory(self, length: int) -> None:
        if length > self.directory_bytes:
            raise OverLimit
        self.directory_bytes -= length

    def take_entries(self, count: int) -> None:
        if count > self.entries:
            raise OverLimit
        self.entries -= count

    def take_declared(self, size: int) -> None:
        if size > self.declared_bytes:
            raise OverLimit
        self.declared_bytes -= size

    def take_read(self, size: int) -> None:
        if size > self.read_bytes:
            raise OverLimit
        self.read_bytes -= size

    def take_text_member(self) -> None:
        """One more member for a reader, or _Stop: member cap, character cap or time share reached."""
        if self.text_members <= 0 or self.chars > config.settings().max_text_chars or _now() > self.deadline:
            raise _Stop
        self.text_members -= 1

    def next_scratch(self) -> Path:
        """A file next to the scratch file of the job, named by a number and never by a member.

        The ``.part`` ending is the one of the poller's scratch files, so a file
        left behind by a killed child goes with the sweep of the next start.
        """
        self.serial += 1
        return Path(f"{self.scratch}.m{self.serial}.part")


def _now() -> float:
    return time.monotonic()


def extract_zip(path: str) -> ExtractionOutcome:
    """The text of a ZIP file, or the verdict that says why there is none."""
    budget = _ArchiveBudget.start(path)
    sections: list[str] = []
    truncated = False
    try:
        _read_zip(Path(path), "", 1, budget, sections)
    except OverLimit as over:
        if over.signature is not None:
            return ExtractionOutcome.skipped(Reason.BLOCKED_MALICIOUS, detail=over.signature)
        return ExtractionOutcome.skipped(Reason.ARCHIVE_LIMIT)
    except _UNREADABLE_DIRECTORY as error:
        if _is_overlap(error):
            return ExtractionOutcome.skipped(Reason.BLOCKED_MALICIOUS, detail=_ZIP_OVERLAP)
        return ExtractionOutcome.from_exception(error)
    except _Stop:
        truncated = True

    if budget.files and budget.encrypted == budget.files:
        return ExtractionOutcome.skipped(Reason.ENCRYPTED)
    # The one caller that keeps the marks: they are what the excerpt code of
    # plan 31-09 reads the name of the inner file from.
    outcome = cap_text("".join(sections), member_marks=True)
    if truncated and outcome.state is State.INDEXED:
        return ExtractionOutcome.indexed(outcome.text, truncated=True)
    return outcome


def count_central_directory(handle: BinaryIO, size: int, *, limit: int) -> int:
    """The number of headers zipfile would read from this directory, at most ``limit + 1``.

    Located and walked exactly like CPython 3.13 does it, so the number is what
    ``len(ZipFile(path).infolist())`` would be without building a single
    ZipInfo. Raises CorruptDirectory where zipfile would raise BadZipFile, and
    OverLimit when the directory is longer than ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES.
    """
    start, length = _central_directory(handle, size)
    if length > ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES:
        raise OverLimit
    window = _Window(handle, start, min(length, max(size - start, 0)))
    total = 0
    count = 0
    # zipfile, _RealGetContents: "while total < size_cd", one 46 byte header with
    # its signature, then name, extra field and comment by their declared lengths.
    while total < length:
        header = window.take(_CENTRAL_SIZE)
        if len(header) != _CENTRAL_SIZE or header[:4] != _CENTRAL:
            raise CorruptDirectory
        name_len, extra_len, comment_len = struct.unpack_from("<HHH", header, 28)
        window.skip(name_len + extra_len + comment_len)
        total += _CENTRAL_SIZE + name_len + extra_len + comment_len
        count += 1
        if count > limit:
            break
    return count


def too_many_entries(path: str) -> bool:
    """True when the directory holds more than ARCHIVE_MAX_ENTRIES records, counted before ZipFile.

    The package readers of odf.py and office.py ask this before they open a
    ZipFile (package_entries, D-36-17, finding F3). It lives here, next to the
    count and its two exceptions, so the refusal rule is written once (IN-03 of
    the phase 36 review). A directory the count calls corrupt, or a file that
    does not open, is left to the reader's own ZipFile or loader, whose
    exception carries the better diagnosis; a directory longer than
    ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES is too many entries as well.
    """
    try:
        with Path(path).open("rb") as handle:
            size = os.fstat(handle.fileno()).st_size
            return count_central_directory(handle, size, limit=ARCHIVE_MAX_ENTRIES) > ARCHIVE_MAX_ENTRIES
    except OverLimit:
        return True
    except (CorruptDirectory, OSError):
        return False


def _central_directory(handle: BinaryIO, size: int) -> tuple[int, int]:
    """Start and byte length of the central directory, as zipfile computes them."""
    location, length, offset = _end_record(handle, size)
    # _RealGetContents: concat = location - size_cd - offset_cd, and the
    # directory starts at offset_cd + concat, which is location - size_cd.
    start = offset + (location - length - offset)
    if start < 0:
        raise CorruptDirectory
    return start, length


def _end_record(handle: BinaryIO, size: int) -> tuple[int, int, int]:
    """Location of the end record, directory length and offset; zipfile's _EndRecData."""
    if size < _END_SIZE:
        raise CorruptDirectory
    handle.seek(size - _END_SIZE)
    data = handle.read(_END_SIZE)
    if len(data) == _END_SIZE and data[:4] == _END and data[-2:] == b"\x00\x00":
        location = size - _END_SIZE
    else:
        earliest = max(size - _COMMENT_MAX - _END_SIZE, 0)
        handle.seek(earliest)
        tail = handle.read(_COMMENT_MAX + _END_SIZE)
        found = tail.rfind(_END)
        if found < 0:
            raise CorruptDirectory
        data = tail[found : found + _END_SIZE]
        if len(data) != _END_SIZE:
            raise CorruptDirectory
        location = earliest + found
    length, offset = struct.unpack_from("<II", data, 12)
    return _end_record64(handle, location, length, offset)


def _end_record64(handle: BinaryIO, location: int, length: int, offset: int) -> tuple[int, int, int]:
    """zipfile's _EndRecData64: a locator in front of the end record overrides it, whatever its fields say."""
    at = location - _LOCATOR64_SIZE
    if at < 0:
        return location, length, offset
    handle.seek(at)
    data = handle.read(_LOCATOR64_SIZE)
    if len(data) != _LOCATOR64_SIZE:
        raise CorruptDirectory
    signature, disk, relative, disks = struct.unpack("<4sLQL", data)
    if signature != _LOCATOR64:
        return location, length, offset
    if disk != 0 or disks > 1:
        raise CorruptDirectory
    at -= _END64_SIZE
    if relative > at:
        raise CorruptDirectory
    handle.seek(relative)
    extra = at - relative
    record = handle.read(_END64_SIZE)
    if len(record) != _END64_SIZE:
        raise CorruptDirectory
    if not record.startswith(_END64) and relative != at:
        # Data in front of the ZIP file: zipfile assumes no extensible data sector.
        handle.seek(at)
        extra = 0
        record = handle.read(_END64_SIZE)
        if len(record) != _END64_SIZE:
            raise CorruptDirectory
    if not record.startswith(_END64):
        raise CorruptDirectory
    record_size = struct.unpack_from("<Q", record, 4)[0]
    length64, offset64 = struct.unpack_from("<QQ", record, 40)
    if offset64 + length64 != relative or record_size + 12 != _END64_SIZE + extra:
        raise CorruptDirectory
    return at - extra, length64, offset64


class _Window:
    """A bounded region of the file, read in blocks; reads past its end come back short, like BytesIO."""

    def __init__(self, handle: BinaryIO, start: int, length: int) -> None:
        handle.seek(start)
        self._handle = handle
        self._left = length
        self._buffer = b""
        self._at = 0

    def take(self, count: int) -> bytes:
        while len(self._buffer) - self._at < count and self._left > 0:
            block = self._handle.read(min(_READ_BLOCK, self._left))
            if not block:
                self._left = 0
                break
            self._left -= len(block)
            self._buffer = self._buffer[self._at :] + block
            self._at = 0
        piece = self._buffer[self._at : self._at + count]
        self._at += len(piece)
        return piece

    def skip(self, count: int) -> None:
        buffered = len(self._buffer) - self._at
        if count <= buffered:
            self._at += count
            return
        count -= buffered
        self._buffer = b""
        self._at = 0
        jump = min(count, self._left)
        self._handle.seek(jump, 1)
        self._left -= jump


def _read_zip(path: Path, prefix: str, depth: int, budget: _ArchiveBudget, sections: list[str]) -> None:
    """One level: count, open, judge the declarations, read the members."""
    with path.open("rb") as handle:
        size = handle.seek(0, 2)
        _, length = _central_directory(handle, size)
        budget.take_directory(length)
        count = count_central_directory(handle, size, limit=budget.entries)
        budget.take_entries(count)

    with ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > count:
            raise OverLimit
        budget.take_declared(sum(info.file_size for info in members))
        _judge_ratios(members)
        for info in members:
            if _is_traversal(info.orig_filename):
                raise OverLimit(_ZIP_TRAVERSAL)
        for info in members:
            if not info.is_dir():
                _read_member(archive, info, prefix, depth, budget, sections)


def _judge_ratios(members: list[ZipInfo]) -> None:
    """The ratio of every member from ARCHIVE_RATIO_MIN_BYTES on, in two steps (answer O12).

    The signature is looked for in all members first, so a member over the
    attack ratio is named even behind one that is merely over the limit.
    """
    judged = [
        (info.file_size, max(info.compress_size, 1)) for info in members if info.file_size >= ARCHIVE_RATIO_MIN_BYTES
    ]
    if any(size > ARCHIVE_MALICIOUS_RATIO * packed for size, packed in judged):
        raise OverLimit(_ZIP_RATIO)
    if any(size > ARCHIVE_MAX_RATIO * packed for size, packed in judged):
        raise OverLimit


def _read_member(
    archive: ZipFile, info: ZipInfo, prefix: str, depth: int, budget: _ArchiveBudget, sections: list[str]
) -> None:
    """One member: a section with its name, and its text when a reader is there for it."""
    budget.files += 1
    name = clean_display_name(f"{prefix}{info.filename}")
    extension = extension_of(info.filename)
    nested = extension == "zip"
    reader = _MEMBER_READERS.get(extension)
    if nested and depth >= ARCHIVE_MAX_DEPTH:
        raise OverLimit

    if info.flag_bits & _ENCRYPTED_FLAG:
        budget.encrypted += 1
        sections.append(_section(name, ""))
        return
    if (
        info.compress_type not in _READABLE_METHODS
        or (reader is None and not nested)
        or info.file_size > config.settings().max_file_bytes
    ):
        sections.append(_section(name, ""))
        return

    budget.take_text_member()
    member = budget.next_scratch()
    try:
        if not _copy(archive, info, member, budget):
            sections.append(_section(name, ""))
            return
        if nested:
            sections.append(_section(name, ""))
            _read_inner(member, f"{name}/", depth, budget, sections)
            return
        if reader is not None:
            sections.append(_section(name, _member_text(reader, str(member), budget)))
    finally:
        member.unlink(missing_ok=True)


def _copy(archive: ZipFile, info: ZipInfo, member: Path, budget: _ArchiveBudget) -> bool:
    """Stream one member into its scratch file, counted. False when its data is broken.

    Two answers of ``archive.open`` are handled here besides the overlap
    refusal (security audit 31-15). zipfile only warns, instead of refusing,
    when the next entry starts at the very same local header, and its warning
    quotes the member name; a warning goes to stderr, which is the container
    log (H-31-02). It is recorded and never shown: an overlap warning is the
    same signature as the refusal (two directory entries for one local header
    are written by no packer) and ends the file as zip_overlap (D-36-17,
    answer O2); any other warning is dropped. And a directory that claims
    to sit behind the end of the file makes zipfile shift every local header
    below zero, so ``seek`` raises OSError; that member is broken, not the ZIP
    file around it (L-31-02).
    """
    with member.open("wb") as sink:
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                source = archive.open(info)
        except BadZipFile as error:
            if _is_overlap(error):
                raise OverLimit(_ZIP_OVERLAP) from None
            return False
        except OSError:
            return False
        if any(str(warning.message).startswith(_OVERLAP) for warning in caught):
            source.close()
            raise OverLimit(_ZIP_OVERLAP)
        with source:
            while True:
                try:
                    block = source.read(_READ_BLOCK)
                except _BROKEN_MEMBER:
                    return False
                if not block:
                    return True
                budget.take_read(len(block))
                sink.write(block)


def _read_inner(member: Path, prefix: str, depth: int, budget: _ArchiveBudget, sections: list[str]) -> None:
    """An inner ZIP file, one level down, with the same budget. A broken one stays a name."""
    try:
        _read_zip(member, prefix, depth + 1, budget, sections)
    except _UNREADABLE_DIRECTORY as error:
        if _is_overlap(error):
            raise OverLimit(_ZIP_OVERLAP) from None


def _member_text(reader: Callable[[str], ExtractionOutcome], path: str, budget: _ArchiveBudget) -> str:
    """The text a reader finds in one member, without the mark; empty when it finds none or fails.

    A reader raises what its library raises (the translation happens at the
    sandbox boundary for a single file). Inside a ZIP file a member that beats
    its reader costs that member and not the file. MemoryError is the
    exception: the address space of the child is spent, which is the whole job.
    """
    try:
        outcome = reader(path)
    except MemoryError:
        raise
    except Exception:
        return ""
    if outcome.state is not State.INDEXED:
        return ""
    text = outcome.text.replace(ARCHIVE_MEMBER_MARK, "")
    # Past the character cap the next member is not read any more; cap_text
    # cuts the text and says so.
    budget.chars += len(text)
    return text


def _section(name: str, text: str) -> str:
    return f"{ARCHIVE_MEMBER_MARK}{name}\n{text}\n\n"


# The readers of the members, by extension. Imported when a member needs them,
# like the routes of dispatch.py: a ZIP file of text files never loads pdfium.
# Pictures are not here (no OCR inside a ZIP file); a PDF is read for its text
# layer only, a scan is skipped(no_text_layer) there and stays a name here.


def _pdf(path: str) -> ExtractionOutcome:
    from findling.extract import pdf

    return pdf.extract_pdf(path)


def _ooxml(route: str) -> Callable[[str], ExtractionOutcome]:
    def read(path: str) -> ExtractionOutcome:
        from findling.extract.dispatch import Route, _run_ooxml_route

        return _run_ooxml_route(Route(route), path)

    return read


def _odf(path: str) -> ExtractionOutcome:
    from findling.extract import odf

    return odf.extract_odf(path)


def _html(path: str) -> ExtractionOutcome:
    from findling.extract import text

    return text.extract_html(path)


def _rtf(path: str) -> ExtractionOutcome:
    from findling.extract import text

    return text.extract_rtf(path)


def _plain(path: str) -> ExtractionOutcome:
    from findling.extract import text

    return text.extract_plain(path)


def _eml(path: str) -> ExtractionOutcome:
    from findling.extract import mail

    return mail.extract_eml(path)


def _doc(path: str) -> ExtractionOutcome:
    from findling.extract import legacy_doc

    return legacy_doc.extract_msword(path)


def _xls(path: str) -> ExtractionOutcome:
    from findling.extract import legacy_xls

    return legacy_xls.extract_msexcel(path)


_MEMBER_READERS: Final[Mapping[str, Callable[[str], ExtractionOutcome]]] = {
    "pdf": _pdf,
    "docx": _ooxml("docx"),
    "pptx": _ooxml("pptx"),
    "xlsx": _ooxml("xlsx"),
    "odt": _odf,
    "ods": _odf,
    "odp": _odf,
    "html": _html,
    "htm": _html,
    "xhtml": _html,
    "rtf": _rtf,
    "txt": _plain,
    "md": _plain,
    "csv": _plain,
    "eml": _eml,
    "doc": _doc,
    "xls": _xls,
}
