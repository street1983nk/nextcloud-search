"""The content gateway seen from the container side (COMP-02).

Every test here runs against a mock transport, never against a real Nextcloud.
That is on purpose: the integration workflow proves the wire, these tests prove
the behaviour that a green wire would still hide.

Two tests carry more weight than the rest. The one with PDF bytes: the JSON aware
entry point of the client library would die with a decode error on the first real
document, and a test written with a TXT file passes anyway because plain text
survives far enough. And the one where the sink raises in the middle of the body:
the answer has to be closed even then, which is the defect this file was extended
for. A response left open dangles in the connection pool, and the next call gets
it.
"""

from __future__ import annotations

import io
import re
from base64 import b64decode
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

import httpx
import pytest

from findling.nc.client import (
    CHUNK_SIZE,
    GATEWAY_PATH,
    AsyncNextcloudApp,
    NextcloudException,
    app_api_headers,
    fetch_file_stream,
    gateway_url,
)
from findling.tools.read_corpus import (
    STATUS_ERROR,
    STATUS_NOT_ACCESSIBLE,
    STATUS_READ,
    format_report,
    read_files,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"

# A short PDF header plus a byte sequence that no JSON parser accepts. If the
# implementation ever routes through a JSON aware entry point again, this is the
# payload that says so.
PDF_BYTES = b"%PDF-1.7\n\xde\xad\xbe\xef{not json at all\n%%EOF\n"

APP_ID = "findling_backend"
APP_VERSION = "0.1.0"
# Not a real credential. The gateway compares it on the PHP side; here it only has
# to end up in the header, which is what the first test asserts.
APP_CREDENTIAL = "unit-test-credential"
NEXTCLOUD_URL = "http://localhost:8080"


@pytest.fixture(autouse=True)
def _appapi_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The environment AppAPI hands the container, which is what the client reads."""
    monkeypatch.setenv("APP_ID", APP_ID)
    monkeypatch.setenv("APP_VERSION", APP_VERSION)
    monkeypatch.setenv("APP_SECRET", APP_CREDENTIAL)
    monkeypatch.setenv("NEXTCLOUD_URL", NEXTCLOUD_URL)


class _TrackingStream(httpx.AsyncByteStream):
    """A response body that yields prepared blocks and records its own closing."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks
        self.closed = False

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self._chunks:
            yield chunk

    async def aclose(self) -> None:
        self.closed = True


class _Gateway:
    """Answers every call with a prepared status and body, and records the request."""

    def __init__(self, *, status: int = 200, chunks: list[bytes] | None = None) -> None:
        self._status = status
        self._chunks = [PDF_BYTES] if chunks is None else chunks
        self.requests: list[httpx.Request] = []
        # One body per call, so a second file is not served an exhausted stream.
        self.streams: list[_TrackingStream] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self._status >= 400:
            return httpx.Response(self._status, text="refused")
        stream = _TrackingStream(list(self._chunks))
        self.streams.append(stream)
        return httpx.Response(self._status, stream=stream)

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self.handle))


class _FakeApp:
    """The only part of ``AsyncNextcloudApp`` the gateway helper touches."""

    def __init__(self, user: str = "") -> None:
        self._user = user

    @property
    async def user(self) -> str:
        return self._user


class _CountingBuffer(io.BytesIO):
    """A sink that remembers how often it was written to and with how much."""

    def __init__(self) -> None:
        super().__init__()
        self.block_sizes: list[int] = []

    def write(self, data: Any) -> int:
        self.block_sizes.append(len(data))
        return super().write(data)


class _FailingSink(io.BytesIO):
    """A sink that breaks halfway through, like a full disk."""

    def write(self, data: Any) -> int:
        del data
        raise OSError("no space left on device")


def _app(user: str = "") -> Any:
    return cast(AsyncNextcloudApp, _FakeApp(user))


async def test_the_gateway_path_carries_the_file_id_and_the_user_id() -> None:
    gateway = _Gateway()
    sink = io.BytesIO()

    async with gateway.client() as client:
        await fetch_file_stream(_app(), 4711, "testuser", sink, client=client)

    request = gateway.requests[0]
    assert request.url.path == GATEWAY_PATH.format(file_id=4711)
    assert request.url.params["userId"] == "testuser"
    assert request.method == "GET"


async def test_the_request_carries_the_appapi_credential() -> None:
    # The gateway is locked to this app id and refuses anything else with a 403,
    # so a missing header here is a 403 in production, not a 500.
    gateway = _Gateway()

    async with gateway.client() as client:
        await fetch_file_stream(_app(), 1, "testuser", io.BytesIO(), client=client)

    headers = gateway.requests[0].headers
    assert headers["EX-APP-ID"] == APP_ID
    assert headers["EX-APP-VERSION"] == APP_VERSION
    # Without this one Nextcloud refuses every call on an /ocs/ route.
    assert headers["OCS-APIRequest"] == "true"
    assert headers["AUTHORIZATION-APP-API"]


def test_the_credential_is_the_base64_of_user_and_secret() -> None:
    # Read back independently instead of rebuilding the expression of the
    # implementation: a shared expression would prove nothing.
    decoded = b64decode(app_api_headers("alice")["AUTHORIZATION-APP-API"]).decode()

    assert decoded == f"alice:{APP_CREDENTIAL}"


def test_the_url_is_built_from_the_environment() -> None:
    assert gateway_url(7) == f"{NEXTCLOUD_URL}/ocs/v2.php/apps/findling/files/7"


async def test_pdf_bytes_arrive_unchanged_and_raise_no_json_error() -> None:
    gateway = _Gateway(chunks=[PDF_BYTES])
    sink = io.BytesIO()

    async with gateway.client() as client:
        written = await fetch_file_stream(_app(), 1, "testuser", sink, client=client)

    assert written == len(PDF_BYTES)
    assert sink.getvalue() == PDF_BYTES


async def test_a_file_the_user_may_not_see_returns_none() -> None:
    gateway = _Gateway(status=404)
    sink = io.BytesIO()

    async with gateway.client() as client:
        assert await fetch_file_stream(_app(), 1, "stranger", sink, client=client) is None

    assert sink.getvalue() == b""


async def test_an_unexpected_error_is_not_swallowed() -> None:
    gateway = _Gateway(status=500)

    async with gateway.client() as client:
        with pytest.raises(NextcloudException):
            await fetch_file_stream(_app(), 1, "testuser", io.BytesIO(), client=client)


async def test_the_body_arrives_in_blocks_of_at_most_the_chunk_size() -> None:
    # A bounded block size is what keeps a multi gigabyte file out of the heap of
    # a 4 GB box. The payload is deliberately larger than one block and not a
    # multiple of it, so the last, shorter block is exercised too.
    payload = bytes(CHUNK_SIZE * 2 + 17)
    gateway = _Gateway(chunks=[payload])
    sink = _CountingBuffer()

    async with gateway.client() as client:
        written = await fetch_file_stream(_app(), 1, "testuser", sink, client=client)

    assert written == len(payload)
    assert len(sink.block_sizes) == 3
    assert max(sink.block_sizes) <= CHUNK_SIZE


async def test_the_answer_is_closed_when_the_sink_breaks_mid_body() -> None:
    # The defect this test exists for: the answer used to be held open without a
    # context manager, so an exception in the middle of a file left the response
    # dangling in the connection pool and the next call inherited it.
    gateway = _Gateway(chunks=[PDF_BYTES])

    async with gateway.client() as client:
        with pytest.raises(OSError, match="no space left"):
            await fetch_file_stream(_app(), 1, "testuser", _FailingSink(), client=client)

    assert gateway.streams[0].closed


async def test_read_corpus_reports_one_line_per_file() -> None:
    gateway = _Gateway()

    async with gateway.client() as client:
        results = await read_files(_app(), "testuser", [11, 12], client=client)

    assert [result.status for result in results] == [STATUS_READ, STATUS_READ]
    assert [result.bytes_read for result in results] == [len(PDF_BYTES), len(PDF_BYTES)]

    report = format_report(results)
    assert f"file 11 {STATUS_READ}" in report
    assert f"summary files=2 {STATUS_READ}=2 {STATUS_NOT_ACCESSIBLE}=0 {STATUS_ERROR}=0" in report
    # No content, ever: the report is what the CI log keeps (T-01-32).
    assert "PDF" not in report


async def test_read_corpus_marks_a_forbidden_file_as_not_accessible() -> None:
    gateway = _Gateway(status=404)

    async with gateway.client() as client:
        results = await read_files(_app(), "stranger", [11, 12], client=client)

    assert [result.status for result in results] == [STATUS_NOT_ACCESSIBLE, STATUS_NOT_ACCESSIBLE]
    assert sum(result.bytes_read for result in results) == 0
    summary = f"summary files=2 {STATUS_READ}=0 {STATUS_NOT_ACCESSIBLE}=2 {STATUS_ERROR}=0 bytes=0"
    assert summary in format_report(results)


async def test_read_corpus_keeps_going_after_an_unexpected_error() -> None:
    gateway = _Gateway(status=500)

    async with gateway.client() as client:
        results = await read_files(_app(), "testuser", [11, 12], client=client)

    assert [result.status for result in results] == [STATUS_ERROR, STATUS_ERROR]


def test_nc_py_api_is_named_in_the_client_module_only() -> None:
    """Gate A restated as a text scan, deliberately not reusing its AST parser.

    A cross check that shares the implementation of the thing it checks proves
    nothing. This one greps, and it greps for the HTTP client as well: a module
    with its own client could write without naming the Nextcloud library once.
    """
    pattern = re.compile(r"\bnc_py_api\b|\bhttpx\b")
    offenders = sorted(
        path.relative_to(PACKAGE_ROOT).as_posix()
        for path in PACKAGE_ROOT.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    )

    assert offenders == ["nc/client.py"]
