"""The content gateway seen from the container side (COMP-02).

Every test here runs against a session double, never against a real Nextcloud.
That is on purpose: the integration workflow proves the wire, these tests prove
the behaviour that a green wire would still hide.

The most valuable test in this file is the one with PDF bytes. ``ocs()`` in
nc_py_api parses every answer as JSON, so a gateway call routed through it dies
with a JSONDecodeError on the first real document. A test written with a TXT
file passes anyway, because plain text happens to survive far enough. The
payload below is binary and deliberately not valid JSON.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import IO, Any, cast

import pytest
from findling.tools.read_corpus import (
    STATUS_ERROR,
    STATUS_NOT_ACCESSIBLE,
    STATUS_READ,
    format_report,
    read_files,
)

from findling.nc.client import (
    CHUNK_SIZE,
    GATEWAY_PATH,
    AsyncNextcloudApp,
    NextcloudException,
    fetch_file_stream,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"

# A short PDF header plus a byte sequence that no JSON parser accepts. If the
# implementation ever routes through a JSON aware entry point again, this is the
# payload that says so.
PDF_BYTES = b"%PDF-1.7\n\xde\xad\xbe\xef{not json at all\n%%EOF\n"


class _FakeSession:
    """Stands in for ``AsyncNcSessionApp`` and records how it was called."""

    def __init__(self, chunks: list[bytes] | None = None, error: Exception | None = None) -> None:
        self._chunks = chunks if chunks is not None else [PDF_BYTES]
        self._error = error
        self.calls: list[dict[str, Any]] = []

    async def download2stream(self, url_path: str, fp: IO[bytes], dav: bool = False, **kwargs: Any) -> None:
        self.calls.append({"url_path": url_path, "dav": dav, **kwargs})
        if self._error is not None:
            raise self._error
        for chunk in self._chunks:
            fp.write(chunk)


class _FakeApp:
    """The only part of ``AsyncNextcloudApp`` the gateway helper touches."""

    def __init__(self, session: _FakeSession) -> None:
        self._session = session


class _CountingBuffer(io.BytesIO):
    """A sink that remembers how often it was written to."""

    def __init__(self) -> None:
        super().__init__()
        self.write_calls = 0

    def write(self, data: Any) -> int:
        self.write_calls += 1
        return super().write(data)


def _app(chunks: list[bytes] | None = None, error: Exception | None = None) -> tuple[Any, _FakeSession]:
    session = _FakeSession(chunks=chunks, error=error)
    return cast(AsyncNextcloudApp, _FakeApp(session)), session


async def test_the_gateway_path_carries_the_file_id_and_the_user_id() -> None:
    app, session = _app()
    sink = io.BytesIO()

    await fetch_file_stream(app, 4711, "testuser", sink)

    assert session.calls[0]["url_path"] == GATEWAY_PATH.format(file_id=4711)
    assert session.calls[0]["params"] == {"userId": "testuser"}
    # dav=False keeps the call on the OCS adapter, which is where the ExApp
    # credentials live. The WebDAV adapter would speak as nobody.
    assert session.calls[0]["dav"] is False


async def test_pdf_bytes_arrive_unchanged_and_raise_no_json_error() -> None:
    app, _ = _app(chunks=[PDF_BYTES])
    sink = io.BytesIO()

    written = await fetch_file_stream(app, 1, "testuser", sink)

    assert written == len(PDF_BYTES)
    assert sink.getvalue() == PDF_BYTES


async def test_a_file_the_user_may_not_see_returns_none() -> None:
    app, _ = _app(error=NextcloudException(404, reason="Not found"))
    sink = io.BytesIO()

    assert await fetch_file_stream(app, 1, "stranger", sink) is None
    assert sink.getvalue() == b""


async def test_an_unexpected_error_is_not_swallowed() -> None:
    app, _ = _app(error=NextcloudException(500, reason="Unknown error occurred."))
    sink = io.BytesIO()

    with pytest.raises(NextcloudException):
        await fetch_file_stream(app, 1, "testuser", sink)


async def test_the_body_is_written_block_by_block() -> None:
    blocks = [b"a" * 16, b"b" * 16, b"c" * 8]
    app, session = _app(chunks=blocks)
    sink = _CountingBuffer()

    written = await fetch_file_stream(app, 1, "testuser", sink)

    # A bounded chunk size is what keeps a multi gigabyte file out of the heap
    # of a 4 GB box. Without it nc_py_api reads whatever the server sends.
    assert session.calls[0]["chunk_size"] == CHUNK_SIZE
    assert CHUNK_SIZE > 0
    assert sink.write_calls == len(blocks)
    assert written == sum(len(block) for block in blocks)


async def test_read_corpus_reports_one_line_per_file() -> None:
    session = _FakeSession()
    app = cast(AsyncNextcloudApp, _FakeApp(session))

    results = await read_files(app, "testuser", [11, 12])

    assert [result.status for result in results] == [STATUS_READ, STATUS_READ]
    assert [result.bytes_read for result in results] == [len(PDF_BYTES), len(PDF_BYTES)]

    report = format_report(results)
    assert f"file 11 {STATUS_READ}" in report
    assert f"summary files=2 {STATUS_READ}=2 {STATUS_NOT_ACCESSIBLE}=0 {STATUS_ERROR}=0" in report
    # No content, ever: the report is what the CI log keeps (T-01-32).
    assert "PDF" not in report


async def test_read_corpus_marks_a_forbidden_file_as_not_accessible() -> None:
    session = _FakeSession(error=NextcloudException(404, reason="Not found"))
    app = cast(AsyncNextcloudApp, _FakeApp(session))

    results = await read_files(app, "stranger", [11, 12])

    assert [result.status for result in results] == [STATUS_NOT_ACCESSIBLE, STATUS_NOT_ACCESSIBLE]
    assert sum(result.bytes_read for result in results) == 0
    summary = f"summary files=2 {STATUS_READ}=0 {STATUS_NOT_ACCESSIBLE}=2 {STATUS_ERROR}=0 bytes=0"
    assert summary in format_report(results)


async def test_read_corpus_keeps_going_after_an_unexpected_error() -> None:
    session = _FakeSession(error=NextcloudException(500, reason="Unknown error occurred."))
    app = cast(AsyncNextcloudApp, _FakeApp(session))

    results = await read_files(app, "testuser", [11, 12])

    assert [result.status for result in results] == [STATUS_ERROR, STATUS_ERROR]


def test_nc_py_api_is_named_in_the_client_module_only() -> None:
    """Gate A restated as a text scan, deliberately not reusing its AST parser.

    A cross check that shares the implementation of the thing it checks proves
    nothing. This one greps.
    """
    pattern = re.compile(r"\bnc_py_api\b")
    offenders = sorted(
        path.relative_to(PACKAGE_ROOT).as_posix()
        for path in PACKAGE_ROOT.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    )

    assert offenders == ["nc/client.py"]
