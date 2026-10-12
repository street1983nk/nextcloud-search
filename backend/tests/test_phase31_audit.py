"""The malicious format corpus and the boundary probes of the phase 31 audit (31-AUDIT.md).

Phase 31 opened the largest new attack surface of the milestone: mails, ZIP
files, Word and Excel 97 to 2003 compound files and a native HEIF decoder, all
read in the sandbox child, plus a one time catch-up that hands files back to
the queue. This module holds the audit probes as regression tests.

**The corpus is built here, at test time, and differently from the build
plans.** The tests of plans 31-04 to 31-08 build their ZIP files with zipfile
and patch them, their compound files with helpers of their own and their mails
with the email package, and they call the readers in this process. Here every
ZIP file is written byte by byte from the PKWARE records, every compound file
by the small writer below (FAT, MiniFAT, directory, DIFAT), every workbook
record by record, every mail as raw bytes, and every HEIC is encoded by
pillow-heif and then cut or patched box by box. Every file goes through the
real sandbox path, ``ExtractionWorker``: a spawned child with RLIMIT_AS (on
Linux) and a deadline. Each case asserts a named verdict, a living worker and
a run time well under the deadline. Bombs declare their size and do not carry
it, so the corpus stays small.

**Logs.** The corpus carries made up names, subjects, addresses and sheet
names, all ending in "geheim". The log probe runs them through the child and
reads caplog and the file descriptors of this process, which the spawned child
inherits for stderr. A positive control (a picture between the pixel cap and
twice the cap makes Pillow warn without any content) shows that the probe sees
what the child writes there.

The other groups follow the behavior block of plan 31-15: the wire codes
towards every companion generation, the catch-up mark under manipulation, the
mark changing in the middle of a cycle, the one cycle where the reconcile is
switched off, the targeted re-judging of the mixed window, the mirror check of
the corresponding source, the import hygiene of the search process and the
pattern checks in front of GITHUB_ENV.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import re
import struct
import subprocess
import sys
import time
import zlib
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest

from findling.extract import sandbox
from findling.extract.errors import STATE_REASONS, ExtractionOutcome, Reason, State
from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import FileRow, Mount, MountResult, SliceResult
from findling.nc.queue import (
    _FAILED_FALLBACK_BY_GENERATION,
    _SKIPPED_FALLBACK_BY_GENERATION,
    KIND_CONTENT,
    SKIPPED_FALLBACK_WITHOUT_SIGNAL,
    CallResult,
    QueueStats,
    _wire_reason,
)
from findling.store.repo import CATCHUP_DONE, CATCHUP_MARK, CATCHUP_RECONCILE, RECHECK_MARK, FileMeta, Store, open_store
from findling.worker.catchup import catchup_step
from findling.worker.reconcile import GIVEN_UP_REASON, GIVEN_UP_STATE, ROUND_WALKED, Reconcile

REPO = Path(__file__).resolve().parents[2]
DEPLOY_HARP = REPO / ".github" / "workflows" / "deploy-harp.yml"
CORRESPONDING_SOURCE = REPO / "scripts" / "release" / "corresponding_source.py"

# The deadline of the corpus worker and the time one case may take. Half the
# product deadline (120 s) for the worker, so that a hang costs one minute and
# not two; a quarter of it for a case, so that a reader that is merely slow on
# this machine shows up as well.
CORPUS_DEADLINE_SECONDS = 60.0
CASE_SECONDS = 30.0

ZIP = "application/zip"
MAIL = "message/rfc822"
DOC = "application/msword"
XLS = "application/vnd.ms-excel"
HEIC = "image/heic"

# Everything a log line must never carry. Each one stands in the log corpus below.
SECRETS = (
    "mitgliedgeheim",
    "ueberlappgeheim",
    "betreffgeheim",
    "absendergeheim",
    "anhanggeheim",
    "blattgeheim",
    "zellgeheim",
    "olegeheim",
)


# -- the sandbox ------------------------------------------------------------------


@pytest.fixture(scope="module")
def worker() -> Iterator[sandbox.ExtractionWorker]:
    started = sandbox.ExtractionWorker(max_files=1000, timeout_seconds=CORPUS_DEADLINE_SECONDS)
    yield started
    started.stop()


@dataclass(frozen=True)
class Ran:
    outcome: ExtractionOutcome
    seconds: float


def _run(worker: sandbox.ExtractionWorker, path: Path, mime: str) -> Ran:
    started = time.monotonic()
    outcome = worker.run(str(path), mime, path.stat().st_size)
    return Ran(outcome, time.monotonic() - started)


def _named_and_quick(ran: Ran, worker: sandbox.ExtractionWorker) -> None:
    """The three promises of every case: a verdict with a name, a living worker, a short run."""
    assert ran.outcome.reason in STATE_REASONS[ran.outcome.state]
    assert ran.outcome.reason is not Reason.TIMEOUT
    assert ran.seconds < CASE_SECONDS
    # The next job is answered: by the same child, or by a fresh one after a recycle.
    assert worker.run(__file__, "application/x-not-allowed", 10).reason is Reason.MIME_NOT_ALLOWED


def _expect(ran: Ran, state: State, reason: Reason | None = None, *, contains: str = "", lacks: str = "") -> None:
    assert (ran.outcome.state, ran.outcome.reason) == (state, reason), ran.outcome.detail
    if contains:
        assert contains in ran.outcome.text
    if lacks:
        assert lacks not in ran.outcome.text


def _corpus_case(
    worker: sandbox.ExtractionWorker, tmp_path: Path, name: str, data: bytes, mime: str
) -> tuple[Ran, list[str]]:
    path = tmp_path / name
    path.write_bytes(data)
    ran = _run(worker, path, mime)
    _named_and_quick(ran, worker)
    return ran, sorted(entry.name for entry in tmp_path.iterdir())


# -- ZIP files, written record by record (APPNOTE 4.3.7, 4.3.12, 4.3.16) ------------


@dataclass(frozen=True)
class Member:
    name: bytes
    data: bytes
    deflate: bool = False
    declared: int | None = None  # the uncompressed size the records claim, when not the true one
    offset: int | None = None  # the local header offset the directory claims, when not the true one


def _local(member: Member, payload: bytes, crc: int, declared: int) -> bytes:
    method = 8 if member.deflate else 0
    head = struct.pack(
        "<4sHHHHHIIIHH", b"PK\x03\x04", 20, 0, method, 0, 0x21, crc, len(payload), declared, len(member.name), 0
    )
    return head + member.name + payload


def _central(member: Member, payload: bytes, crc: int, declared: int, offset: int) -> bytes:
    method = 8 if member.deflate else 0
    fields = (b"PK\x01\x02", 0x031E, 20, 0, method, 0, 0x21, crc, len(payload), declared, len(member.name))
    return struct.pack("<4sHHHHHHIIIHHHHHII", *fields, 0, 0, 0, 0, 0o100644 << 16, offset) + member.name


def _end(count: int, size: int, offset: int, comment: bytes = b"") -> bytes:
    return struct.pack("<4sHHHHIIH", b"PK\x05\x06", 0, 0, count, count, size, offset, len(comment)) + comment


def _deflated(data: bytes) -> bytes:
    packer = zlib.compressobj(9, zlib.DEFLATED, -15)
    return packer.compress(data) + packer.flush()


def build_zip(members: Sequence[Member], *, comment: bytes = b"") -> bytes:
    body = b""
    directory = b""
    for member in members:
        payload = _deflated(member.data) if member.deflate else member.data
        crc = zlib.crc32(member.data)
        declared = len(member.data) if member.declared is None else member.declared
        at = len(body)
        body += _local(member, payload, crc, declared)
        directory += _central(member, payload, crc, declared, at if member.offset is None else member.offset)
    return body + directory + _end(len(members), len(directory), len(body), comment)


def _same_offset_twice(name: bytes, data: bytes) -> bytes:
    """Two directory entries for one local header: the overlap zipfile only warns about."""
    crc = zlib.crc32(data)
    body = _local(Member(name, data), data, crc, len(data))
    directory = _central(Member(name, data), data, crc, len(data), 0) * 2
    return body + directory + _end(2, len(directory), len(body))


def _text(word: str) -> Member:
    return Member(f"{word}.txt".encode(), f"{word} steht hier".encode())


def _end_record_in_comment() -> bytes:
    """A second end record with lying numbers inside the comment; zipfile takes the last one it finds."""
    plain = build_zip([_text("kommentarwort")])
    lying = struct.pack("<4sHHHHIIH", b"PK\x05\x06", 0, 0, 5, 5, 999_999, 3, 0)
    comment = b"xx" + lying + b"yy"
    return plain[:-2] + struct.pack("<H", len(comment)) + comment


def _zip64_locator_that_lies() -> bytes:
    plain = build_zip([_text("y")])
    return plain[:-22] + struct.pack("<4sLQL", b"PK\x06\x07", 0, 10**12, 1) + plain[-22:]


def _with_end(plain: bytes, size: int, offset: int) -> bytes:
    return plain[:-22] + struct.pack("<4sHHHHIIH", b"PK\x05\x06", 0, 0, 1, 1, size, offset, 0)


_ZIP_CASES: dict[str, tuple[Callable[[], bytes], tuple[State, Reason | None], str, str | None]] = {
    # name: (builder, verdict, a word the text must hold, the finding the case stands for)
    # Declared small, real 20 MiB of zeros: zipfile stops at the declaration, the
    # CRC fails, the member keeps its name and the next member is read.
    "lying-small": (
        lambda: build_zip([Member(b"a.txt", b"\0" * (20 << 20), deflate=True, declared=1000), _text("kleinwort")]),
        (State.INDEXED, None),
        "kleinwort",
        None,
    ),
    "lying-huge": (
        lambda: build_zip([Member(b"a.txt", b"hallo", declared=0xFFFFFFF0)]),
        (State.SKIPPED, Reason.ARCHIVE_LIMIT),
        "",
        None,
    ),
    "end-record-in-comment": (_end_record_in_comment, (State.FAILED, Reason.CORRUPT), "", None),
    "zip64-locator-contradicts": (_zip64_locator_that_lies, (State.FAILED, Reason.CORRUPT), "", None),
    "offsets-overflow": (
        lambda: _with_end(build_zip([_text("x")]), 0xFFFFFFFF, 0xFFFFFFFF),
        (State.FAILED, Reason.CORRUPT),
        "",
        None,
    ),
    # The directory claims an offset far behind its real place: zipfile adds the
    # difference to every local offset and the member offset turns negative.
    "directory-offset-past-the-end": (
        lambda: _with_end(build_zip([Member(b"a.txt", b"x")]), 46 + 5, 0x7FFFFFFF),
        (State.INDEXED, None),
        "a.txt",
        "L-31-02",
    ),
    "local-header-past-the-end": (
        lambda: build_zip([Member(b"weg.txt", b"x", offset=10_000_000), _text("bleibwort")]),
        (State.INDEXED, None),
        "bleibwort",
        None,
    ),
    "name-64-kib": (
        lambda: build_zip([Member(b"n" * 65_000 + b".txt", b"langnamewort")]),
        (State.INDEXED, None),
        "langnamewort",
        None,
    ),
    "name-nul-and-both-separators": (
        lambda: build_zip(
            [Member(b"..\\..\\boese/../x\x00.txt.bin", b"nulwort"), Member(b"/abs/../../y.txt", b"abswort")]
        ),
        (State.INDEXED, None),
        "abswort",
        None,
    ),
    "10000-entries-of-one-name": (
        lambda: build_zip([Member(b"gleich.txt", b"gleichwort")] * 10_000),
        (State.INDEXED, Reason.TRUNCATED),
        "gleichwort",
        None,
    ),
    "10001-entries": (
        lambda: build_zip([Member(f"x{i}.txt".encode(), b"") for i in range(10_001)]),
        (State.SKIPPED, Reason.ARCHIVE_LIMIT),
        "",
        None,
    ),
    "inner-zip-with-overlap": (
        lambda: build_zip([Member(b"innen.zip", _same_offset_twice(b"o.txt", b"overlapwort")), _text("aussenwort")]),
        (State.INDEXED, None),
        "aussenwort",
        None,
    ),
    "inner-zip-with-a-negative-member": (
        lambda: build_zip(
            [
                Member(b"innen.zip", _with_end(build_zip([Member(b"a.txt", b"x")]), 46 + 5, 0x7FFFFFFF)),
                _text("aussenwort"),
            ]
        ),
        (State.INDEXED, None),
        "aussenwort",
        "L-31-02",
    ),
    "depth-three": (
        lambda: build_zip([Member(b"e2.zip", build_zip([Member(b"e3.zip", build_zip([_text("tiefwort")]))]))]),
        (State.SKIPPED, Reason.ARCHIVE_LIMIT),
        "",
        None,
    ),
    "mail-in-zip-in-zip": (
        lambda: build_zip(
            [Member(b"e2.zip", build_zip([Member(b"m.eml", b"From: a@b.de\r\nSubject: tiefpost\r\n\r\ntext\r\n")]))]
        ),
        (State.INDEXED, None),
        "tiefpost",
        None,
    ),
}


@pytest.mark.parametrize("case", list(_ZIP_CASES))
def test_every_zip_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    build, (state, reason), word, _ = _ZIP_CASES[case]

    ran, left = _corpus_case(worker, tmp_path, "korpus.zip", build(), ZIP)

    _expect(ran, state, reason, contains=word)
    # Members go into scratch files named by a number next to the job file and are
    # deleted at once; nothing is ever written under a member name.
    assert left == ["korpus.zip"]


def test_a_zip_as_attachment_of_a_mail_is_never_opened(worker: sandbox.ExtractionWorker, tmp_path: Path) -> None:
    import base64

    inner = base64.b64encode(build_zip([_text("anhanginhaltwort")]))
    mail = (
        b"From: a@b.de\r\nSubject: postmitzip\r\nMIME-Version: 1.0\r\n"
        b'Content-Type: multipart/mixed; boundary="g"\r\n\r\n--g\r\nContent-Type: text/plain\r\n\r\ntext\r\n'
        b'--g\r\nContent-Type: application/zip\r\nContent-Disposition: attachment; filename="paket.zip"\r\n'
        b"Content-Transfer-Encoding: base64\r\n\r\n" + inner + b"\r\n--g--\r\n"
    )

    ran, _ = _corpus_case(worker, tmp_path, "post.eml", mail, MAIL)

    _expect(ran, State.INDEXED, contains="paket.zip", lacks="anhanginhaltwort")


# -- mails, as raw bytes ------------------------------------------------------------

_HEAD = b"From: a@b.de\r\nTo: c@d.de\r\nSubject: hallo\r\n"


def _nested_rfc822(levels: int) -> bytes:
    mail = _HEAD + b"Content-Type: text/plain\r\n\r\nkern\r\n"
    for _ in range(levels):
        mail = b"Subject: s\r\nContent-Type: message/rfc822\r\n\r\n" + mail
    return mail


_MAIL_CASES: dict[str, tuple[Callable[[], bytes], tuple[State, Reason | None], str, str | None]] = {
    "5000-header-lines": (
        lambda: b"".join(b"X-H%d: v\r\n" % i for i in range(5000)) + _HEAD + b"\r\nbody\r\n",
        (State.INDEXED, None),
        "hallo",
        None,
    ),
    "subject-of-1-mib": (
        lambda: b"Subject: " + b"wort " * 200_000 + b"\r\nFrom: a@b.de\r\n\r\nkoerperwort\r\n",
        (State.INDEXED, Reason.TRUNCATED),
        "koerperwort",
        "H-31-01",
    ),
    "to-of-1-mib": (
        lambda: b"To: " + b",".join(b"u%d@x.de" % i for i in range(100_000)) + b"\r\n\r\nkoerperwort\r\n",
        (State.INDEXED, Reason.TRUNCATED),
        "u0@x.de",
        "H-31-01",
    ),
    "to-of-1-mib-with-names": (
        lambda: b"To: " + b",".join(b'"N %d" <u%d@x.de>' % (i, i) for i in range(60_000)) + b"\r\n\r\nkoerperwort\r\n",
        (State.INDEXED, Reason.TRUNCATED),
        "u0@x.de",
        "H-31-01",
    ),
    "broken-base64": (
        lambda: _HEAD + b"Content-Type: text/plain\r\nContent-Transfer-Encoding: base64\r\n\r\n!!!!@@@@====abc$$\r\n",
        (State.INDEXED, None),
        "hallo",
        None,
    ),
    "broken-quoted-printable": (
        lambda: (
            _HEAD
            + b"Content-Type: text/plain\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\nfoo=ZZ=\r\n=4 bar=\r\n"
        ),
        (State.INDEXED, None),
        "foo",
        None,
    ),
    "rfc2231-name-with-traversal-and-bidi": (
        lambda: (
            _HEAD + b'MIME-Version: 1.0\r\nContent-Type: multipart/mixed; boundary="b"\r\n\r\n'
            b"--b\r\nContent-Type: text/plain\r\n\r\n"
            b"text\r\n--b\r\nContent-Type: application/octet-stream\r\nContent-Disposition: attachment; "
            b"filename*=utf-8''..%2F..%2Fetc%2Fpasswd%E2%80%AEfdp.exe%00x\r\n\r\nAAAA\r\n--b--\r\n"
        ),
        (State.INDEXED, None),
        "../../etc/passwdfdp.exex",
        None,
    ),
    "content-type-with-10000-parameters": (
        lambda: (
            _HEAD
            + b"Content-Type: text/plain; "
            + b"; ".join(b"p%d=v" % i for i in range(10_000))
            + b"\r\n\r\nbody\r\n"
        ),
        # 89 KB of Content-Type: cut to MAX_HEADER_CHARS since H-31-01, so the
        # text is still read and the verdict says that a header was shortened.
        (State.INDEXED, Reason.TRUNCATED),
        "body",
        "H-31-01",
    ),
    "boundary-collision": (
        lambda: (
            _HEAD + b'Content-Type: multipart/mixed; boundary="b"\r\n\r\n--b\r\nContent-Type: multipart/alternative; '
            b'boundary="b"\r\n\r\n--b\r\nContent-Type: text/plain\r\n\r\ninnen\r\n--b--\r\n--b--\r\n'
        ),
        (State.INDEXED, None),
        "hallo",
        None,
    ),
    "rfc822-nested-1000-times": (lambda: _nested_rfc822(1000), (State.FAILED, Reason.CORRUPT), "", None),
    # The structural headers are parsed by the email package itself, part by
    # part and more than once, so a limit on the four indexed headers alone
    # would leave these two.
    "content-type-of-1-mib": (
        lambda: (
            _HEAD + b"Content-Type: text/plain; " + b"; ".join(b"p%d=v" % i for i in range(100_000)) + b"\r\n\r\nx\r\n"
        ),
        (State.INDEXED, Reason.TRUNCATED),
        "hallo",
        "H-31-01",
    ),
    "600-parts-with-8-kib-content-types": (
        lambda: (
            _HEAD
            + b'MIME-Version: 1.0\r\nContent-Type: multipart/mixed; boundary="b"\r\n\r\n'
            + b"".join(
                b"--b\r\nContent-Type: text/plain; " + b"; ".join(b"p%d=v" % i for i in range(1000)) + b"\r\n\r\nx\r\n"
                for _ in range(600)
            )
            + b"--b--\r\n"
        ),
        (State.INDEXED, Reason.TRUNCATED),
        "hallo",
        "H-31-01",
    ),
}


@pytest.mark.parametrize("case", list(_MAIL_CASES))
def test_every_mail_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    build, (state, reason), word, _ = _MAIL_CASES[case]

    ran, _ = _corpus_case(worker, tmp_path, "korpus.eml", build(), MAIL)

    _expect(ran, state, reason, contains=word)


def test_a_mail_with_999_ordinary_attachments_stays_whole(tmp_path: Path) -> None:
    # The control of the header budget of H-31-01: a real mail at the part limit,
    # with ordinary headers, is read to its end and not marked truncated.
    from findling.extract.mail import extract_eml

    attachments = b"".join(
        b'--b\r\nContent-Type: application/pdf; name="Rechnung_2026_%06d.pdf"\r\n'
        b'Content-Disposition: attachment; filename="Rechnung_2026_%06d.pdf"\r\n'
        b"Content-Transfer-Encoding: base64\r\n\r\nJVBERi0xLjQK\r\n" % (index, index)
        for index in range(999)
    )
    path = tmp_path / "anhaenge.eml"
    path.write_bytes(
        b"From: Anna <anna@example.de>\r\nTo: Bernd <b@example.de>, Carla <c@example.de>\r\nSubject: Akte\r\n"
        b'MIME-Version: 1.0\r\nContent-Type: multipart/mixed; boundary="b"\r\n\r\n'
        b"--b\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nHallo\r\n" + attachments + b"--b--\r\n"
    )

    outcome = extract_eml(str(path))

    assert (outcome.state, outcome.reason) == (State.INDEXED, None)
    assert outcome.text.count("Rechnung_2026_") == 999


def test_an_html_part_reads_no_entity_and_no_doctype(worker: sandbox.ExtractionWorker, tmp_path: Path) -> None:
    canary = tmp_path / "kanarie.txt"
    canary.write_text("kanarienwort", encoding="utf-8")
    target = canary.as_uri().encode()
    xml = (
        _HEAD
        + b'Content-Type: text/html\r\n\r\n<?xml version="1.0"?><!DOCTYPE h [<!ENTITY e SYSTEM "'
        + target
        + b'">]>'
        b"<html><body>&e; sichtbarwort</body></html>\r\n"
    )
    html = (
        _HEAD + b'Content-Type: text/html\r\n\r\n<!DOCTYPE html SYSTEM "' + target + b'"><html><body>'
        b"sichtbarwort</body></html>\r\n"
    )

    for name, mail in (("xml.eml", xml), ("html.eml", html)):
        ran, _ = _corpus_case(worker, tmp_path, name, mail, MAIL)
        assert ran.outcome.state is State.INDEXED
        assert "kanarienwort" not in ran.outcome.text
        assert "hallo" in ran.outcome.text


# -- compound files, written sector by sector ([MS-CFB] 2.2, 2.3, 2.6) -----------------

_SECTOR = 512
_MINI = 64
_END_OF_CHAIN = 0xFFFFFFFE
_FREE = 0xFFFFFFFF
_FAT_SECTOR = 0xFFFFFFFD
_NO_STREAM = 0xFFFFFFFF


@dataclass
class Layout:
    """What a compound file is made of, editable before it is written."""

    fat: list[int]
    minifat: list[int]
    entries: list[list[Any]]  # name, type, left, right, child, start, size
    header: dict[str, Any]
    tail: bytes = b""


def _entry(name: str, kind: int, left: int, right: int, child: int, start: int, size: int) -> bytes:
    raw = name.encode("utf-16-le") + b"\0\0" if name else b""
    return (
        raw.ljust(64, b"\0")
        + struct.pack("<HBB3I", len(raw), kind, 1, left, right, child)
        + b"\0" * 36
        + struct.pack("<IQ", start, size)
    )


def _chain(table: list[int], start: int, count: int) -> None:
    for index in range(count):
        table[start + index] = start + index + 1 if index < count - 1 else _END_OF_CHAIN


def build_cfb(streams: dict[str, bytes], edit: Callable[[Layout], None] | None = None) -> bytes:
    """Version 3, 512 byte sectors. Streams under 4096 bytes go into the mini stream, as the specification wants."""
    names = list(streams)
    small = [name for name in names if 0 < len(streams[name]) < 4096]
    minifat: list[int] = []
    container = b""
    mini_start: dict[str, int] = {}
    for name in small:
        data = streams[name]
        count = -(-len(data) // _MINI)
        mini_start[name] = len(minifat)
        minifat += [_FREE] * count
        _chain(minifat, mini_start[name], count)
        container += data.ljust(count * _MINI, b"\0")
    minifat_sectors = -(-len(minifat) * 4 // _SECTOR)
    container_sectors = -(-len(container) // _SECTOR)
    big = [name for name in names if len(streams[name]) >= 4096]
    big_sectors = sum(-(-len(streams[name]) // _SECTOR) for name in big)
    dir_sectors = -(-(1 + len(names)) * 128 // _SECTOR)
    fat_sectors = 1
    while fat_sectors * 128 < fat_sectors + dir_sectors + minifat_sectors + container_sectors + big_sectors:
        fat_sectors += 1
    fat = [_FREE] * (fat_sectors * 128)
    for index in range(fat_sectors):
        fat[index] = _FAT_SECTOR
    at = fat_sectors
    _chain(fat, at, dir_sectors)
    dir_start, at = at, at + dir_sectors
    _chain(fat, at, minifat_sectors)
    minifat_start, at = (at if minifat_sectors else _END_OF_CHAIN), at + minifat_sectors
    _chain(fat, at, container_sectors)
    container_start, at = (at if container_sectors else _END_OF_CHAIN), at + container_sectors
    body = b""
    starts: dict[str, int] = {}
    for name in big:
        count = -(-len(streams[name]) // _SECTOR)
        _chain(fat, at, count)
        starts[name] = at
        body += streams[name].ljust(count * _SECTOR, b"\0")
        at += count
    entries: list[list[Any]] = [["Root Entry", 5, _NO_STREAM, _NO_STREAM, 1 if names else _NO_STREAM]]
    entries[0] += [container_start, len(container)]
    for index, name in enumerate(names):
        start = mini_start.get(name, starts.get(name, _END_OF_CHAIN))
        right = index + 2 if index + 1 < len(names) else _NO_STREAM
        entries.append([name, 2, _NO_STREAM, right, _NO_STREAM, start, len(streams[name])])
    layout = Layout(
        fat,
        minifat,
        entries,
        {
            "fat_sectors": fat_sectors,
            "dir_start": dir_start,
            "minifat_start": minifat_start,
            "minifat_sectors": minifat_sectors,
            "difat_start": _END_OF_CHAIN,
            "difat_sectors": 0,
            "next_sector": at,
        },
    )
    if edit is not None:
        edit(layout)
    header = layout.header
    difat = ([*range(fat_sectors)] + [_FREE] * 109)[:109]
    head = (
        bytes.fromhex("d0cf11e0a1b11ae1")
        + b"\0" * 16
        + struct.pack("<5H", 0x3E, 3, 0xFFFE, 9, 6)
        + b"\0" * 6
        + struct.pack("<4I", 0, header["fat_sectors"], header["dir_start"], 0)
        + struct.pack("<4I", 4096, header["minifat_start"], header["minifat_sectors"], header["difat_start"])
        + struct.pack("<I", header["difat_sectors"])
        + struct.pack("<109I", *difat)
    )
    directory = b"".join(_entry(*entry) for entry in layout.entries).ljust(dir_sectors * _SECTOR, b"\0")
    minifat_bytes = struct.pack(f"<{len(layout.minifat)}I", *layout.minifat).ljust(minifat_sectors * _SECTOR, b"\xff")
    return (
        head
        + struct.pack(f"<{len(layout.fat)}I", *layout.fat)
        + directory
        + minifat_bytes
        + container.ljust(container_sectors * _SECTOR, b"\0")
        + body
        + layout.tail
    )


# Word: a FibBase with the counts every Word from 97 on writes ([MS-DOC] 2.5.1),
# the Clx at the front of the table stream, one compressed piece at 0x800.
_TEXT_AT = 0x800
_COMPRESSED = 0x40000000


def _word_stream(n_fib: int, lcb_clx: int, text: bytes, at: int = _TEXT_AT) -> bytes:
    word = bytearray(0x1000)
    struct.pack_into("<HH", word, 0, 0xA5EC, n_fib)
    struct.pack_into("<H", word, 0x0A, 0x0200)  # fWhichTblStm: 1Table
    struct.pack_into("<H", word, 0x20, 0x000E)
    struct.pack_into("<H", word, 0x3E, 0x0016)
    struct.pack_into("<H", word, 0x98, 0x005D)
    struct.pack_into("<II", word, 0x01A2, 0, lcb_clx)
    word[at : at + len(text)] = text
    return bytes(word)


def _clx(pieces: Sequence[int], cps: Sequence[int]) -> bytes:
    plc = struct.pack(f"<{len(cps)}I", *cps) + b"".join(struct.pack("<HIH", 0, fc, 0) for fc in pieces)
    return b"\x02" + struct.pack("<I", len(plc)) + plc


def build_doc(
    text: bytes = b"olegeheim im text\r",
    *,
    n_fib: int = 0x00C1,
    pieces: Sequence[int] | None = None,
    cps: Sequence[int] | None = None,
    lcb_clx: int | None = None,
    at: int = _TEXT_AT,
    edit: Callable[[Layout], None] | None = None,
) -> bytes:
    table = _clx([(at * 2) | _COMPRESSED] if pieces is None else pieces, [0, len(text)] if cps is None else cps)
    word = _word_stream(n_fib, len(table) if lcb_clx is None else lcb_clx, text, at)
    return build_cfb({"WordDocument": word, "1Table": table}, edit)


def _difat_cycle(layout: Layout) -> None:
    sector = layout.header["next_sector"]
    layout.header["difat_start"] = sector
    layout.header["difat_sectors"] = 1
    layout.tail = struct.pack("<128I", *([_FREE] * 127), sector)


def _minifat_cycle(layout: Layout) -> None:
    last = max(index for index, link in enumerate(layout.minifat) if link == _END_OF_CHAIN)
    layout.minifat[last] = 0


def _directory_cycle(layout: Layout) -> None:
    layout.entries[1][3] = 1


def _fat_cycle(layout: Layout) -> None:
    start = layout.entries[1][5]
    layout.fat[start + 3] = start


def _fat_declared_far_past_the_file(layout: Layout) -> None:
    layout.header["fat_sectors"] = 20_000


_MILLIONS = 3_000_000
_OVERLAPPING = 100_000

_DOC_CASES: dict[str, tuple[Callable[[], bytes], tuple[State, Reason | None], str]] = {
    "control": (build_doc, (State.INDEXED, None), "olegeheim"),
    "millions-of-pieces-declared": (
        lambda: build_doc(lcb_clx=12 * _MILLIONS + 4),
        (State.FAILED, Reason.CORRUPT),
        "",
    ),
    "100000-overlapping-pieces": (
        lambda: build_doc(pieces=[(_TEXT_AT * 2) | _COMPRESSED] * _OVERLAPPING, cps=range(_OVERLAPPING + 1)),
        (State.INDEXED, None),
        "ooo",
    ),
    "fc-ends-on-the-stream-end": (lambda: build_doc(b"endwort", at=0x1000 - 7), (State.INDEXED, None), "endwort"),
    "fc-one-past-the-stream-end": (
        lambda: build_doc(b"endwort", pieces=[((0x1000 - 6) * 2) | _COMPRESSED], cps=[0, 7], at=0x1000 - 7),
        (State.FAILED, Reason.CORRUPT),
        "",
    ),
    "unicode-fc-past-the-stream-end": (
        lambda: build_doc(b"endwort", pieces=[0x1000 - 4], cps=[0, 7]),
        (State.FAILED, Reason.CORRUPT),
        "",
    ),
    "nfib-00c0": (lambda: build_doc(n_fib=0x00C0), (State.SKIPPED, Reason.UNSUPPORTED_VARIANT), ""),
    "nfib-00c1": (lambda: build_doc(n_fib=0x00C1), (State.INDEXED, None), "olegeheim"),
    "nfib-ffff": (lambda: build_doc(n_fib=0xFFFF), (State.INDEXED, None), "olegeheim"),
    "worddocument-of-0-bytes": (
        lambda: build_cfb({"WordDocument": b"", "1Table": _clx([0], [0, 1])}),
        (State.FAILED, Reason.CORRUPT),
        "",
    ),
    "difat-cycle": (lambda: build_doc(edit=_difat_cycle), (State.FAILED, Reason.CORRUPT), ""),
    "minifat-cycle": (lambda: build_doc(edit=_minifat_cycle), (State.FAILED, Reason.CORRUPT), ""),
    "directory-cycle": (lambda: build_doc(edit=_directory_cycle), (State.FAILED, Reason.CORRUPT), ""),
    "fat-cycle": (lambda: build_doc(edit=_fat_cycle), (State.FAILED, Reason.CORRUPT), ""),
    "fat-declared-far-past-the-file": (
        lambda: build_doc(edit=_fat_declared_far_past_the_file),
        (State.FAILED, Reason.CORRUPT),
        "",
    ),
}


@pytest.mark.parametrize("case", list(_DOC_CASES))
def test_every_word_file_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    build, (state, reason), word = _DOC_CASES[case]

    ran, _ = _corpus_case(worker, tmp_path, "korpus.doc", build(), DOC)

    _expect(ran, state, reason, contains=word)
    if case in _REFUSED_BY_THE_READER:
        # The reader's own length check refuses these, not a struct.error that
        # happens to land on the same verdict further down.
        assert ran.outcome.detail == "findling.extract.legacy_doc.CorruptDocument"


_REFUSED_BY_THE_READER = frozenset(
    {
        "millions-of-pieces-declared",
        "fc-one-past-the-stream-end",
        "unicode-fc-past-the-stream-end",
        "worddocument-of-0-bytes",
    }
)


def _word6_stream(flags: int = 0) -> bytes:
    """The FIB head of Word 6 and Word 95: wIdent 0xA5DC, nFib 0x0065 to 0x0068, no table stream.

    Read off a real Word 6 file on the audit machine (nFib 0x68, csw 0x0D1C,
    flags 0); Word 6 keeps its tables in the WordDocument stream itself.
    """
    word = bytearray(0x1000)
    struct.pack_into("<HHHHHH", word, 0, 0xA5DC, 0x0068, 0, 0x0407, 0, flags)
    return bytes(word)


@pytest.mark.parametrize(("flags", "reason"), [(0x0000, Reason.UNSUPPORTED_VARIANT), (0x0100, Reason.ENCRYPTED)])
def test_a_word_6_or_95_file_is_an_unsupported_variant_and_not_a_damaged_one(
    flags: int, reason: Reason, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    # D-31-03 names Word 6 and 95 skipped(unsupported_variant), and the docstring
    # of legacy_doc.py says so; the identifier of their FIB is not the one of 97.
    data = build_cfb({"WordDocument": _word6_stream(flags)})

    ran, _ = _corpus_case(worker, tmp_path, "word95.doc", data, DOC)

    _expect(ran, State.SKIPPED, reason)


# Excel: BIFF8 records ([MS-XLS] 2.4), one sheet of LABELSST cells.


def _record(opcode: int, data: bytes = b"") -> bytes:
    return struct.pack("<HH", opcode, len(data)) + data


def _bof(kind: int, version: int) -> bytes:
    return _record(0x0809, struct.pack("<HHHHII", version, kind, 0x0DBB, 0x07CC, 0, 0x0006))


def _short_string(text: str) -> bytes:
    raw = text.encode("latin-1")
    return struct.pack("<HB", len(raw), 0) + raw


def _sst(strings: Sequence[str], unique: int | None) -> bytes:
    """SST and CONTINUE records, split between strings, each at most 8224 bytes."""
    records = [struct.pack("<II", len(strings), len(strings) if unique is None else unique)]
    for text in strings:
        piece = _short_string(text)
        if len(records[-1]) + len(piece) > 8224:
            records.append(b"")
        records[-1] += piece
    return _record(0x00FC, records[0]) + b"".join(_record(0x003C, more) for more in records[1:])


def build_workbook(
    cells: Sequence[tuple[int, int, int]],
    strings: Sequence[str],
    *,
    unique: int | None = None,
    after_bof: bytes = b"",
    version: int = 0x0600,
    edit: Callable[[Layout], None] | None = None,
) -> bytes:
    """Globals (BOF, BOUNDSHEET, SST, EOF) and one sheet of LABELSST cells, in a compound file."""
    sheet_name = struct.pack("<BB", len("blattgeheim"), 0) + b"blattgeheim"
    sst = _sst(strings, unique)
    head = _bof(0x0005, version) + after_bof
    sheet_at = len(head) + 4 + 6 + len(sheet_name) + len(sst) + 4
    head += _record(0x0085, struct.pack("<IBB", sheet_at, 0, 0) + sheet_name) + sst + _record(0x000A)
    sheet = _bof(0x0010, version)
    sheet += b"".join(_record(0x00FD, struct.pack("<HHHI", row, col, 0, index)) for row, col, index in cells)
    return build_cfb({"Workbook": head + sheet + _record(0x000A)}, edit)


def _workbook_minifat_cycle() -> bytes:
    return build_workbook([(0, 0, 0)], ["zellgeheim"], edit=_minifat_cycle)


_CHAIN_WORDS = [f"kettenwort{index:05d}" for index in range(1500)]

_XLS_CASES: dict[str, tuple[Callable[[], bytes], tuple[State, Reason | None], str]] = {
    "control": (lambda: build_workbook([(0, 0, 0)], ["zellgeheim"]), (State.INDEXED, None), "zellgeheim"),
    "filepass-behind-the-bof": (
        lambda: build_workbook([(0, 0, 0)], ["zellgeheim"], after_bof=_record(0x002F, b"\x01\x00" + b"\0" * 52)),
        (State.SKIPPED, Reason.ENCRYPTED),
        "",
    ),
    "continue-chain-across-sectors": (
        lambda: build_workbook([(index, 0, index) for index in range(0, 1500, 7)], _CHAIN_WORDS),
        (State.INDEXED, None),
        "kettenwort01498",
    ),
    "sst-with-a-lying-count": (
        lambda: build_workbook([(0, 0, 0)], ["zellgeheim"], unique=2**31 - 1),
        (State.FAILED, Reason.CORRUPT),
        "",
    ),
    "cell-at-65535-255": (lambda: build_workbook([(65535, 255, 0)], ["fernzelle"]), (State.INDEXED, None), "fernzelle"),
    "unknown-biff-version": (
        lambda: build_workbook([(0, 0, 0)], ["zellgeheim"], version=0x0700),
        (State.SKIPPED, Reason.UNSUPPORTED_VARIANT),
        "",
    ),
    "string-index-past-the-table": (
        lambda: build_workbook([(0, 0, 5)], ["zellgeheim"]),
        (State.FAILED, Reason.CORRUPT),
        "",
    ),
    "minifat-cycle-under-the-workbook": (_workbook_minifat_cycle, (State.FAILED, Reason.CORRUPT), ""),
}


@pytest.mark.parametrize("case", list(_XLS_CASES))
def test_every_excel_file_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    build, (state, reason), word = _XLS_CASES[case]

    ran, _ = _corpus_case(worker, tmp_path, "korpus.xls", build(), XLS)

    _expect(ran, state, reason, contains=word)


# -- HEIC: encoded by pillow-heif, then cut or patched box by box ----------------------


def _heic(size: tuple[int, int] = (640, 200), *, thumbnail: bool = False) -> bytes:
    """A HEIC from pillow-heif's encoder, without registering its opener in this process.

    Registering would change the options image.py set for every later test in
    this process (thumbnails, depth and auxiliary pictures back on).
    """
    import pillow_heif
    from PIL import Image

    picture = Image.new("RGB", size, (200, 30, 30))
    if thumbnail:
        picture.info["thumbnails"] = [32]
    out = io.BytesIO()
    pillow_heif.from_pillow(picture).save(out, quality=50)
    return out.getvalue()


def _boxes(data: bytes, start: int = 0, end: int | None = None) -> Iterator[tuple[int, int, bytes]]:
    """Offset, header length and type of every box, into meta, iprp and ipco."""
    end = len(data) if end is None else end
    at = start
    while at + 8 <= end:
        size, kind = struct.unpack_from(">I4s", data, at)
        if size < 8 or at + size > end:
            return
        yield at, 8, kind
        if kind == b"meta":
            yield from _boxes(data, at + 12, at + size)
        elif kind in (b"iprp", b"ipco"):
            yield from _boxes(data, at + 8, at + size)
        at += size


def _declaring(data: bytes, width: int, height: int) -> bytes:
    """The same HEIC with another declared size and no clean aperture box that would crop it back."""
    out = bytearray(data)
    for at, header, kind in _boxes(data):
        if kind == b"ispe":
            struct.pack_into(">II", out, at + header + 4, width, height)
        elif kind == b"clap":
            out[at + 4 : at + 8] = b"free"
    return bytes(out)


def _heic_with_jpeg_inside() -> bytes:
    from PIL import Image

    jpeg = io.BytesIO()
    Image.new("RGB", (64, 48)).save(jpeg, format="JPEG")
    return struct.pack(">I4s4sI4s4s", 24, b"ftyp", b"heic", 0, b"mif1", b"heic") + jpeg.getvalue()


# Without an engine (this machine, python.yml) the readable picture ends as
# failed(ocr_unavailable); with one (the image) as indexed or empty_text. All
# three are names; the point here is the decoder, not the engine.
_READABLE = {(State.FAILED, Reason.OCR_UNAVAILABLE), (State.INDEXED, None), (State.SKIPPED, Reason.EMPTY_TEXT)}

_HEIC_CASES: dict[str, tuple[Callable[[], bytes], set[tuple[State, Reason | None]]]] = {
    "control": (_heic, _READABLE),
    "declares-100000-by-100000": (
        lambda: _declaring(_heic(), 100_000, 100_000),
        {(State.SKIPPED, Reason.TOO_LARGE)},
    ),
    "cut-after-the-ftyp": (lambda: _heic()[:12], {(State.FAILED, Reason.CORRUPT)}),
    "cut-inside-meta": (lambda: _heic()[:40], {(State.FAILED, Reason.CORRUPT)}),
    "cut-in-the-middle": (lambda: (data := _heic())[: len(data) // 2], {(State.FAILED, Reason.CORRUPT)}),
    "cut-ten-bytes-before-the-end": (lambda: _heic()[:-10], {(State.FAILED, Reason.CORRUPT)}),
    "ftyp-heic-with-jpeg-inside": (_heic_with_jpeg_inside, {(State.FAILED, Reason.CORRUPT)}),
    "with-a-thumbnail": (lambda: _heic(thumbnail=True), _READABLE),
}


@pytest.mark.parametrize("case", list(_HEIC_CASES))
def test_every_heic_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    build, allowed = _HEIC_CASES[case]

    ran, _ = _corpus_case(worker, tmp_path, "korpus.heic", build(), HEIC)

    assert (ran.outcome.state, ran.outcome.reason) in allowed, ran.outcome.detail


def test_only_the_primary_picture_of_a_heic_is_opened(tmp_path: Path) -> None:
    # The registration of image.py, read in a process of its own as the
    # extraction child has it: no thumbnail, no depth and no auxiliary picture
    # reaches Pillow. pillow-heif 1.8 cannot write a depth or an auxiliary
    # picture, so a thumbnail stands for the three.
    path = tmp_path / "vorschau.heic"
    path.write_bytes(_heic(thumbnail=True))
    probe = (
        "import sys, pillow_heif\n"
        "from PIL import Image\n"
        "import findling.extract.image\n"
        "o = pillow_heif.options\n"
        "picture = Image.open(sys.argv[1])\n"
        "print(o.THUMBNAILS, o.DEPTH_IMAGES, o.AUX_IMAGES, picture.size[0], picture.size[1],"
        " getattr(picture, 'n_frames', 1), bool(picture.info.get('thumbnails')),"
        " bool(picture.info.get('depth_images')))\n"
    )
    result = subprocess.run(  # noqa: S603 - fixed argument list
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, check=True, timeout=120
    )
    assert result.stdout.split() == ["False", "False", "False", "640", "200", "1", "False", "False"]
    # The control: the file does carry a thumbnail for a reader that asks for one.
    assert b"thmb" in path.read_bytes()


# -- nothing of the content reaches a log -----------------------------------------


def _log_corpus() -> dict[str, tuple[bytes, str]]:
    attachment = (
        b"From: absendergeheim@b.de\r\nTo: c@d.de\r\nSubject: betreffgeheim\r\nMIME-Version: 1.0\r\n"
        b'Content-Type: multipart/mixed; boundary="g"\r\n\r\n--g\r\nContent-Type: text/plain\r\n\r\ntext\r\n'
        b'--g\r\nContent-Type: application/octet-stream\r\nContent-Disposition: attachment; filename="anhanggeheim.pdf"'
        b"\r\n\r\nAAAA\r\n--g--\r\n"
    )
    return {
        "member.zip": (
            build_zip([Member(b"mitgliedgeheim.txt", b"x"), Member(b"mitgliedgeheim.pdf", b"%PDF-kaputt")]),
            ZIP,
        ),
        "overlap.zip": (_same_offset_twice(b"ueberlappgeheim.txt", b"x"), ZIP),
        "inner.zip": (build_zip([Member(b"innen.zip", _same_offset_twice(b"ueberlappgeheim.txt", b"x"))]), ZIP),
        "attachment.eml": (attachment, MAIL),
        "nested.eml": (b"Subject: betreffgeheim\r\n" + _nested_rfc822(1000), MAIL),
        "broken.doc": (build_doc(edit=_minifat_cycle), DOC),
        "word.doc": (build_doc(), DOC),
        "sheet.xls": (build_workbook([(0, 0, 0)], ["zellgeheim"]), XLS),
        "encrypted.xls": (build_workbook([(0, 0, 0)], ["zellgeheim"], after_bof=_record(0x002F, b"\x01\x00")), XLS),
        "broken.xls": (build_workbook([(0, 0, 9)], ["zellgeheim"]), XLS),
    }


# A HEIC between the pixel cap of image.py (50 MP) and twice the cap: Pillow
# warns about a possible decompression bomb, with numbers and nothing else.
_CONTROL_WARNING = "DecompressionBombWarning"


def test_no_line_of_the_corpus_run_carries_a_name_a_subject_or_an_address(
    tmp_path: Path, capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    # A worker of its own, so that the warning filters of a fresh child apply
    # and no case of another test has already used up a "print once" warning.
    fresh = sandbox.ExtractionWorker(max_files=1000, timeout_seconds=CORPUS_DEADLINE_SECONDS)
    try:
        for name, (data, mime) in _log_corpus().items():
            path = tmp_path / name
            path.write_bytes(data)
            assert fresh.run(str(path), mime, len(data)).reason is not Reason.TIMEOUT
        control = tmp_path / "control.heic"
        control.write_bytes(_declaring(_heic(), 8000, 7500))
        assert fresh.run(str(control), HEIC, control.stat().st_size).reason is Reason.TOO_LARGE
    finally:
        fresh.stop()
    out, err = capfd.readouterr()

    # The positive control: the child's stderr reaches this probe.
    assert _CONTROL_WARNING in err
    seen = "\n".join((out, err, *(record.getMessage() for record in caplog.records)))
    assert [secret for secret in SECRETS if secret in seen] == []


# -- the codes on the wire towards every companion generation ------------------------

# The codes each generation added (nc/queue.py, 31-02): a companion of an older
# generation must never receive them unchanged.
_NEW_IN_GENERATION_2 = frozenset({"system_file", "legacy_format", "unsupported_variant"})
_NEW_IN_GENERATION_3 = frozenset({"archive_limit"})


@pytest.mark.parametrize("generation", [None, 0, 1, 2, 3, 4, 99])
def test_no_code_reaches_a_companion_that_does_not_know_it(generation: int | None) -> None:
    unknown = {
        2: _NEW_IN_GENERATION_3,
        3: frozenset[str](),
    }.get(cast("int", generation), _NEW_IN_GENERATION_2 | _NEW_IN_GENERATION_3)
    for tables, state in (
        (_SKIPPED_FALLBACK_BY_GENERATION, State.SKIPPED),
        (_FAILED_FALLBACK_BY_GENERATION, State.FAILED),
    ):
        for reason in Reason:
            sent = _wire_reason(reason.value, generation, tables)
            assert sent not in unknown, (generation, reason)
            if reason in STATE_REASONS[state] and reason.value not in unknown:
                assert sent == reason.value
    # archive_limit never reaches a generation 2 companion unchanged, in either list.
    if generation == 2:
        assert _wire_reason("archive_limit", 2, _SKIPPED_FALLBACK_BY_GENERATION) == "too_large"
        assert _wire_reason("archive_limit", 2, _FAILED_FALLBACK_BY_GENERATION) == "corrupt"


# -- the catch-up mark under manipulation ------------------------------------------------


class _Queue:
    """Records every requeue; answers not ok from the band number ``fail_at`` on."""

    def __init__(self, *, fail_at: int | None = None) -> None:
        self.requeues: list[tuple[list[int], str]] = []
        self.fail_at = fail_at

    async def requeue(self, file_ids: Sequence[int], *, kind: str) -> CallResult:
        self.requeues.append((list(file_ids), kind))
        if self.fail_at is not None and len(self.requeues) >= self.fail_at:
            return CallResult(ok=False)
        return CallResult(ok=True, count=len(file_ids))

    async def stats(self) -> QueueStats:
        return QueueStats(scheduled=0)

    def content(self) -> list[int]:
        return [file_id for band, kind in self.requeues for file_id in band if kind == KIND_CONTENT]


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    opened.write_meta(RECHECK_MARK, "done")
    yield opened
    opened.close()


_STORAGE = 3
_ROOT = 17


def _record_stuck(store: Store, file_id: int) -> None:
    meta = FileMeta(
        storage_id=_STORAGE,
        root_id=_ROOT,
        path=f"files/akte-{file_id}.pdf",
        title=f"akte-{file_id}.pdf",
        mime="application/pdf",
        size=1024,
        mtime=1_700_000_000,
    )
    store.record(file_id, meta, "failed", "repeatedly_stuck")


@pytest.mark.parametrize(
    ("mark", "finding"),
    [
        ("-5", None),
        ("", None),
        ("text", None),
        (" 12", None),
        ("99999999999999999999", "L-31-01"),
        (chr(0x00B2), "L-31-01"),  # superscript two: isdigit, but int() refuses it
        (chr(0x0661) + chr(0x0662), "L-31-01"),  # Arabic-Indic twelve: isdigit and int(), never written by us
    ],
)
async def test_a_manipulated_cursor_of_part_a_starts_again_at_zero(
    store: Store, mark: str, finding: str | None
) -> None:
    del finding  # the finding the value stands for, for the report
    _record_stuck(store, 7)
    store.write_meta(CATCHUP_MARK, mark)
    queue = _Queue()

    finished = await catchup_step(store, cast("Any", queue))

    assert finished is True
    if mark.isascii() and mark.isdigit():
        return
    assert queue.content() == [7]
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_RECONCILE


async def test_a_companion_falling_back_to_generation_2_pauses_part_a_and_breaks_nothing(
    store: Store, tmp_path: Path
) -> None:
    import test_poller
    from findling.index.open import open_index
    from findling.index.writer import IndexBatchWriter

    class _SecondBandFails(test_poller._FakeQueue):
        async def requeue(self, file_ids: Any, *, kind: str) -> CallResult:
            self.requeues.append((list(file_ids), kind))
            return CallResult(ok=len(self.requeues) != 2, count=len(file_ids))

    for file_id in range(1, 451):
        test_poller._refused_zip(store, file_id)
    index_dir = tmp_path / "index"
    index = open_index(index_dir, test_poller.CONSTITUENTS)
    writer = IndexBatchWriter(index, directory=index_dir, min_free_bytes=0)
    try:
        queue = _SecondBandFails()
        poller = test_poller._poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

        queue.verdicts_answer = 3
        await poller.run_once()
        cursor = store.read_meta()[CATCHUP_MARK]
        assert cursor == "200"
        for _ in range(3):
            queue.verdicts_answer = 2
            await poller.run_once()
        # Paused: no band, the cursor where the failed band left it.
        assert len(queue.requeues) == 2
        assert store.read_meta()[CATCHUP_MARK] == cursor

        queue.verdicts_answer = 3
        await poller.run_once()
    finally:
        writer.close()

    bands = [band for band, _ in queue.requeues]
    assert [len(band) for band in bands] == [200, 200, 200, 50]
    assert bands[1] == bands[2]
    assert sorted({file_id for band in bands for file_id in band}) == list(range(1, 451))
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_RECONCILE


@pytest.mark.parametrize("mark", ["99999999999999999999", chr(0x00B2), chr(0x0661) + chr(0x0662)])
async def test_a_manipulated_cursor_of_the_re_check_of_1_4_starts_again_at_zero(tmp_path: Path, mark: str) -> None:
    # Part A waits for the re-check of 1.4, so a cursor that stops the re-check
    # stops the catch-up of 1.5 as well.
    from findling.worker.recheck import recheck_step

    store = open_store(tmp_path / "state.db")
    try:
        meta = FileMeta(
            storage_id=_STORAGE,
            root_id=_ROOT,
            path="files/kaputt.pdf",
            title="kaputt.pdf",
            mime="application/pdf",
            size=1024,
            mtime=1_700_000_000,
        )
        store.record(7, meta, "failed", "corrupt")
        store.write_meta(RECHECK_MARK, mark)
        queue = _Queue()

        assert await recheck_step(store, cast("Any", queue)) is True
        assert queue.content() == [7]
    finally:
        store.close()


# -- part B: the mark in the middle of a cycle, the restart, the one cycle ------------------


def _written_off(file_id: int, *, mime: str = "application/pdf") -> FileRow:
    return FileRow(
        file_id=file_id,
        etag=f"e{file_id}",
        size=1024,
        mtime=1_700_000_000,
        mime=mime,
        state=GIVEN_UP_STATE,
        reason=GIVEN_UP_REASON,
    )


class _Files:
    """One mount and a scripted list of pages, with a hook before every page."""

    def __init__(self, pages: Sequence[Sequence[FileRow]], hook: Callable[[int], Any] | None = None) -> None:
        self._pages = [tuple(page) for page in pages]
        self._hook = hook
        self.asked: list[int] = []

    async def mounts(self) -> MountResult:
        return MountResult(mounts=(Mount(storage_id=_STORAGE, root_id=_ROOT, overridden_root=_ROOT + 1),))

    async def page(self, *, storage: int, root: int, after: int, limit: int) -> SliceResult:
        del storage, root, limit
        self.asked.append(after)
        index = next((i for i, page in enumerate(self._pages) if page and page[0].file_id > after), None)
        if index is None:
            return SliceResult(final=True)
        if self._hook is not None:
            outcome = self._hook(index)
            if asyncio.iscoroutine(outcome):
                await outcome
        return SliceResult(files=self._pages[index], final=index == len(self._pages) - 1)


def _reconcile(store: Store, files: _Files, queue: _Queue, *, now: list[float] | None = None) -> Reconcile:
    clock = now if now is not None else [1_800_000_000.0]
    return Reconcile(
        store=store,
        client_factory=lambda: cast("AsyncNextcloudApp", None),
        files_factory=lambda nc: cast("Any", files),
        queue_factory=lambda nc: cast("Any", queue),
        slice_size=50,
        quiet_max=100,
        hour=2,
        min_interval_hours=24,
        pause_seconds=0.0,
        tick_seconds=0.01,
        clock=lambda: clock[0],
        hour_of=lambda: 2,
    )


async def test_a_hand_switch_to_done_in_the_middle_of_the_cycle_ends_the_second_chance(store: Store) -> None:
    store.write_meta(CATCHUP_MARK, CATCHUP_RECONCILE)

    def switch(index: int) -> None:
        if index == 1:
            store.write_meta(CATCHUP_MARK, CATCHUP_DONE)

    queue = _Queue()
    files = _Files([[_written_off(10)], [_written_off(20)]], switch)

    result = await _reconcile(store, files, queue).run_once()

    assert result.state == ROUND_WALKED
    # File 10 got its second chance under the mark, file 20 after "done" did not,
    # and its give-up was written as before the upgrade: none of them twice.
    assert queue.content() == [10]
    row = store.file_row(20)
    assert row is not None
    assert (row["state"], row["reason"]) == (GIVEN_UP_STATE, GIVEN_UP_REASON)
    assert store.file_row(10) is None
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_DONE


async def test_the_mark_turning_to_reconcile_inside_an_ordinary_round_gives_every_file_one_chance(
    store: Store,
) -> None:
    # The ordinary round starts before part A, part A runs to its end while the
    # round walks (the poller and the reconcile are two tasks), the round goes on.
    part_a = _Queue()

    async def part_a_ends(index: int) -> None:
        if index == 1:
            assert await catchup_step(store, cast("Any", part_a)) is True

    queue = _Queue()
    pages = [[_written_off(10)], [_written_off(20)]]
    first = await _reconcile(store, _Files(pages, part_a_ends), queue).run_once()
    assert first.state == ROUND_WALKED
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_RECONCILE

    # The catch-up cycle itself, a new round of the same object.
    second = await _reconcile(store, _Files(pages), queue).run_once()
    assert second.state == ROUND_WALKED
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_DONE

    handed = part_a.content() + queue.content()
    assert sorted(handed) == [10, 20], handed


async def test_a_give_up_while_part_a_is_under_way_is_not_lost(store: Store) -> None:
    # Part A stopped after a band that did not arrive; its cursor stands behind
    # file 10. An ordinary round then meets file 10, written off over there.
    store.write_meta(CATCHUP_MARK, "50")
    queue = _Queue()
    pages = [[_written_off(10)]]

    await _reconcile(store, _Files(pages), queue).run_once()
    part_a = _Queue()
    assert await catchup_step(store, cast("Any", part_a)) is True
    await _reconcile(store, _Files(pages), queue).run_once()

    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_DONE
    assert part_a.content() + queue.content() == [10]


async def test_a_restart_in_the_middle_of_the_cycle_walks_it_again_from_the_front(store: Store) -> None:
    store.write_meta(CATCHUP_MARK, CATCHUP_RECONCILE)
    store.set_reconcile_cursor(_STORAGE, 0, finished=True, at=1_700_000_000)
    pages = [[_written_off(10)], [_written_off(20)], [_written_off(30)]]
    stop = asyncio.Event()
    first_queue = _Queue()

    def stop_after_the_first_page(index: int) -> None:
        if index == 1:
            raise asyncio.CancelledError

    first = _reconcile(store, _Files(pages, stop_after_the_first_page), first_queue)
    with pytest.raises(asyncio.CancelledError):
        await first.run_once()
    del stop
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_RECONCILE
    assert store.reconcile_cursor(_STORAGE).after_file_id == 10

    files = _Files(pages)
    second_queue = _Queue()
    await _reconcile(store, files, second_queue).run_once()

    # The new process starts at the front, walks every page once and ends the
    # catch-up; file 10 is handed again, which is the documented price of a
    # restart (metadata only, and requeueAs refreshes a row it already has).
    assert files.asked[0] == 0
    assert first_queue.content() == [10]
    assert second_queue.content() == [10, 20, 30]
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_DONE


async def test_with_the_reconcile_off_exactly_one_cycle_runs_and_then_none(store: Store) -> None:
    store.write_meta(CATCHUP_MARK, CATCHUP_RECONCILE)
    now = [1_800_000_000.0]
    files = _Files([[_written_off(10)]])
    queue = _Queue()
    once = _reconcile(store, files, queue, now=now)
    rounds: list[int] = []
    walk = once.run_once

    async def counted() -> Any:
        rounds.append(1)
        return await walk()

    once.run_once = counted  # type: ignore[method-assign]
    once.arm()
    stop = asyncio.Event()

    await asyncio.wait_for(once.run(stop, once=True), timeout=10)

    assert rounds == [1]
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_DONE
    # A clock moved two days on changes nothing: the task is over, and a new one
    # (the next start of the container) ends at once without a round.
    now[0] += 2 * 86_400
    again = _reconcile(store, _Files([[_written_off(10)]]), queue, now=now)
    again.run_once = counted  # type: ignore[method-assign]
    again.arm()
    await asyncio.wait_for(again.run(stop, once=True), timeout=10)
    assert rounds == [1]
    assert queue.content() == [10]


async def test_a_restart_inside_the_one_cycle_runs_it_once_more_and_ends(store: Store) -> None:
    store.write_meta(CATCHUP_MARK, CATCHUP_RECONCILE)

    def stop_after_the_first_page(index: int) -> None:
        if index == 1:
            raise asyncio.CancelledError

    pages = [[_written_off(10)], [_written_off(20)]]
    first = _reconcile(store, _Files(pages, stop_after_the_first_page), _Queue())
    first.arm()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(first.run(asyncio.Event(), once=True), timeout=10)
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_RECONCILE

    queue = _Queue()
    second = _reconcile(store, _Files(pages), queue)
    second.arm()
    await asyncio.wait_for(second.run(asyncio.Event(), once=True), timeout=10)

    assert queue.content() == [10, 20]
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_DONE


def test_the_one_cycle_is_never_the_active_reconcile() -> None:
    import findling.main as main_module

    source = Path(main_module.__file__).read_text(encoding="utf-8")
    # The one cycle has a variable of its own; active_reconcile reads the regular one only.
    body = source[source.index("def active_reconcile") :]
    body = body[: body.index("\ndef ", 1)]
    assert "_CATCHUP_RECONCILE" not in body
    assert main_module.active_reconcile() is None


# -- part B: the targeted re-judging of the mixed window ----------------------------------


def _skip_row(store: Store, file_id: int, reason: str, etag: str) -> None:
    meta = FileMeta(
        storage_id=_STORAGE,
        root_id=_ROOT,
        path=f"files/f-{file_id}",
        title=f"f-{file_id}",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size=1024,
        mtime=1_700_000_000,
        etag=etag,
    )
    store.record(file_id, meta, "skipped", reason)


async def test_a_mixed_page_hands_back_exactly_the_pairs_of_a_substitute(store: Store) -> None:
    store.write_meta(CATCHUP_MARK, CATCHUP_RECONCILE)
    rows: list[FileRow] = []
    expected: list[int] = []
    file_id = 100
    for ours, substitute in SKIPPED_FALLBACK_WITHOUT_SIGNAL.items():
        for theirs in (substitute, ours, "too_large"):
            file_id += 1
            _skip_row(store, file_id, ours, f"e{file_id}")
            rows.append(
                FileRow(
                    file_id=file_id,
                    etag=f"e{file_id}",
                    size=1024,
                    mtime=1_700_000_000,
                    mime="application/pdf",
                    state="skipped",
                    reason=theirs,
                )
            )
            if theirs == substitute:
                expected.append(file_id)
    # A real code of ours against the substitute of another one, and a changed etag.
    file_id += 1
    _skip_row(store, file_id, "too_large", f"e{file_id}")
    rows.append(FileRow(file_id, f"e{file_id}", 1024, 1_700_000_000, "application/pdf", "skipped", "mime_not_allowed"))
    queue = _Queue()

    await _reconcile(store, _Files([rows]), queue).run_once()

    assert queue.content() == expected


# -- the mirror check of the corresponding source ---------------------------------------


def _verify(*args: str) -> subprocess.CompletedProcess[str]:
    # No network: every proxy points at a closed port, and --verify-only must not need one.
    environment = {**os.environ, "HTTPS_PROXY": "http://127.0.0.1:9", "HTTP_PROXY": "http://127.0.0.1:9"}
    return subprocess.run(  # noqa: S603 - fixed argument list
        [sys.executable, str(CORRESPONDING_SOURCE), "--verify-only", *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env=environment,
    )


def _archive(directory: Path, name: str, data: bytes) -> str:
    import hashlib

    (directory / name).write_bytes(data)
    return f"{name}={hashlib.sha256(data).hexdigest()}"


def test_the_mirror_check_passes_the_genuine_archive(tmp_path: Path) -> None:
    expect = _archive(tmp_path, "quelle.tar.gz", b"echt")
    assert _verify(str(tmp_path), "--expect", expect).returncode == 0


def test_the_mirror_check_refuses_a_manipulated_and_a_missing_archive(tmp_path: Path) -> None:
    expect = _archive(tmp_path, "quelle.tar.gz", b"echt")
    (tmp_path / "quelle.tar.gz").write_bytes(b"falsch")
    assert _verify(str(tmp_path), "--expect", expect).returncode != 0
    (tmp_path / "quelle.tar.gz").unlink()
    assert _verify(str(tmp_path), "--expect", expect).returncode != 0


def test_the_mirror_check_refuses_a_foreign_archive_beside_the_expected_ones(tmp_path: Path) -> None:
    expect = _archive(tmp_path, "quelle.tar.gz", b"echt")
    (tmp_path / "fremd.tar.gz").write_bytes(b"fremd")
    assert _verify(str(tmp_path), "--expect", expect).returncode != 0


def test_the_mirror_check_refuses_a_name_that_leaves_the_directory(tmp_path: Path) -> None:
    mirror = tmp_path / "spiegel"
    mirror.mkdir()
    expect = _archive(tmp_path, "draussen.tar.gz", b"echt")
    result = _verify(str(mirror), "--expect", f"../{expect}")
    assert result.returncode != 0


# -- the search process loads no reader ------------------------------------------------


def test_the_search_module_loads_no_reader_of_phase_31() -> None:
    probe = (
        "import sys, findling.index.search\n"
        "names = ('findling.extract.', 'olefile', 'xlrd', 'pillow_heif', 'email.parser', 'zipfile')\n"
        "print(sorted(m for m in sys.modules if m.startswith(names)))\n"
    )
    result = subprocess.run(  # noqa: S603 - fixed argument list
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True, timeout=120
    )
    assert result.stdout.strip() == "[]"


# -- deploy-harp: the pattern checks in front of GITHUB_ENV --------------------------------


def test_no_pattern_check_of_the_upgrade_steps_matches_line_by_line() -> None:
    # grep -E matches a line, so "335\n412" passes ^[0-9]+$; [[ =~ ]] holds the
    # whole value. The checks of 31-12 used the first, those of 31-13 the second.
    workflow = DEPLOY_HARP.read_text(encoding="utf-8")
    assert re.findall(r"printf '%s(?:\\n)?' \"\$\{[a-z_]+\}\" \| grep -Eq", workflow) == []
