"""The fp32 weights: one fixed release asset, fetched on an admin action only (MOD-02).

Two halves, one per module. The first half is the network side in
``findling.nc.client``: redirects are followed by hand so that every hop is
checked against the two GitHub hosts before a request leaves the container, no
AppAPI credential and no cookie travels along, and the byte cap is counted
while the body streams (T-25-21, T-25-22, T-25-23). The second half is the file
side in ``findling.embed.weights``: a download lands in a ``.part`` file and only
becomes ``model.onnx`` after length and sha256 match, every failure is a value
out of a closed set, and a file the admin placed by hand is verified without a
single request (D-25-04, D-25-06, D-25-09).

Every request here goes to a mock transport. No test touches the network.
"""

from __future__ import annotations

import errno
import hashlib
import os
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import IO, Any, cast

import httpx
import pytest

from findling.embed import weights
from findling.nc.client import ASSET_HOSTS, AssetRefused, fetch_release_asset

START = "https://github.com/street1983nk/nextcloud-search/releases/download/tag/asset.onnx"
ASSET = "https://release-assets.githubusercontent.com/github-production-release-asset/1/asset?sig=x"
PAYLOAD = b"onnx weights, byte for byte " * 64


@pytest.fixture(autouse=True)
def _appapi_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The credential environment AppAPI hands the container.

    Set on purpose: if the release fetch ever reached for the AppAPI headers,
    they would be filled from here and the header test would see them.
    """
    monkeypatch.setenv("APP_ID", "findling_backend")
    monkeypatch.setenv("APP_VERSION", "0.1.0")
    monkeypatch.setenv("APP_SECRET", "unit-test-credential")
    monkeypatch.setenv("NEXTCLOUD_URL", "http://localhost:8080")


Route = tuple[int, dict[str, str], bytes]


class _Release:
    """Answers each URL from a prepared table and records every request."""

    def __init__(self, routes: dict[str, Route]) -> None:
        self._routes = routes
        self.requests: list[httpx.Request] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        status, headers, body = self._routes[str(request.url)]
        return httpx.Response(status, headers=headers, content=body)

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self.handle))


class _Sink:
    """The write callback of a caller, collecting what it was handed."""

    def __init__(self) -> None:
        self.chunks: list[bytes] = []

    async def write(self, chunk: bytes) -> None:
        self.chunks.append(chunk)

    @property
    def data(self) -> bytes:
        return b"".join(self.chunks)


def _redirect(location: str, **headers: str) -> Route:
    return (302, {"location": location, **headers}, b"")


def _ok(body: bytes = PAYLOAD) -> Route:
    return (200, {}, body)


# ---------------------------------------------------------------------------
# The network side: fetch_release_asset
# ---------------------------------------------------------------------------


async def test_a_redirect_to_the_asset_host_delivers_every_byte_in_order() -> None:
    release = _Release({START: _redirect(ASSET), ASSET: _ok()})
    sink = _Sink()

    async with release.client() as client:
        await fetch_release_asset(START, sink.write, cap=len(PAYLOAD), client=client)

    assert sink.data == PAYLOAD
    assert [str(request.url) for request in release.requests] == [START, ASSET]
    assert all(request.method == "GET" for request in release.requests)


async def test_a_redirect_to_a_foreign_host_is_refused_before_the_request() -> None:
    evil = "https://evil.example/asset.onnx"
    release = _Release({START: _redirect(evil), evil: _ok()})
    sink = _Sink()

    async with release.client() as client:
        with pytest.raises(AssetRefused):
            await fetch_release_asset(START, sink.write, cap=len(PAYLOAD), client=client)

    assert [request.url.host for request in release.requests] == ["github.com"]
    assert sink.chunks == []


async def test_a_redirect_to_plain_http_is_refused() -> None:
    plain = ASSET.replace("https://", "http://")
    release = _Release({START: _redirect(plain), plain: _ok()})

    async with release.client() as client:
        with pytest.raises(AssetRefused):
            await fetch_release_asset(START, _Sink().write, cap=len(PAYLOAD), client=client)

    assert len(release.requests) == 1


async def test_a_start_url_outside_the_allowlist_sends_nothing() -> None:
    evil = "https://evil.example/asset.onnx"
    release = _Release({evil: _ok()})

    async with release.client() as client:
        with pytest.raises(AssetRefused):
            await fetch_release_asset(evil, _Sink().write, cap=len(PAYLOAD), client=client)

    assert release.requests == []


async def test_three_redirects_are_followed_and_a_fourth_is_refused() -> None:
    hops = [f"https://github.com/hop/{number}" for number in range(4)]
    three = _Release({START: _redirect(hops[0]), hops[0]: _redirect(hops[1]), hops[1]: _redirect(ASSET), ASSET: _ok()})
    sink = _Sink()

    async with three.client() as client:
        await fetch_release_asset(START, sink.write, cap=len(PAYLOAD), client=client)

    assert sink.data == PAYLOAD

    four = _Release(
        {
            START: _redirect(hops[0]),
            hops[0]: _redirect(hops[1]),
            hops[1]: _redirect(hops[2]),
            hops[2]: _redirect(ASSET),
            ASSET: _ok(),
        }
    )

    async with four.client() as client:
        with pytest.raises(AssetRefused):
            await fetch_release_asset(START, _Sink().write, cap=len(PAYLOAD), client=client)

    assert ASSET not in [str(request.url) for request in four.requests]


async def test_more_bytes_than_the_cap_are_refused() -> None:
    release = _Release({START: _redirect(ASSET), ASSET: _ok(PAYLOAD + b"x")})
    sink = _Sink()

    async with release.client() as client:
        with pytest.raises(AssetRefused):
            await fetch_release_asset(START, sink.write, cap=len(PAYLOAD), client=client)

    assert len(sink.data) <= len(PAYLOAD)


@pytest.mark.parametrize("status", [404, 500])
async def test_an_error_status_is_refused_with_the_code_and_without_the_url(status: int) -> None:
    release = _Release({START: _redirect(ASSET), ASSET: (status, {}, b"refused")})

    async with release.client() as client:
        with pytest.raises(AssetRefused) as caught:
            await fetch_release_asset(START, _Sink().write, cap=len(PAYLOAD), client=client)

    message = str(caught.value)
    assert str(status) in message
    assert "github" not in message
    assert "http" not in message


async def test_no_request_carries_a_credential_or_a_cookie() -> None:
    second = "https://github.com/street1983nk/nextcloud-search/releases/download/tag/second"
    release = _Release(
        {
            START: _redirect(second, **{"set-cookie": "session=secret; Path=/"}),
            second: _redirect(ASSET),
            ASSET: _ok(),
        }
    )

    async with release.client() as client:
        await fetch_release_asset(START, _Sink().write, cap=len(PAYLOAD), client=client)

    assert len(release.requests) == 3
    for request in release.requests:
        names = {name.lower() for name in request.headers}
        assert not any(name.startswith(("aa-", "ex-app")) for name in names), names
        assert not any("authorization" in name for name in names), names
        assert "cookie" not in names, names
        assert "ocs-apirequest" not in names, names


async def test_the_own_client_follows_no_redirect_and_ignores_the_nextcloud_certificate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # NPA_NC_CERT names the CA of the Nextcloud, not of GitHub. A bundle path
    # that does not exist would break the client at construction if the release
    # fetch borrowed that setting.
    monkeypatch.setenv("NPA_NC_CERT", str(Path("does-not-exist") / "ca.pem"))
    from findling.nc import client as nc_client

    async with nc_client._asset_client() as client:
        assert client.follow_redirects is False
        names = {name.lower() for name in client.headers}
        assert not any("authorization" in name for name in names)


def test_the_host_allowlist_names_exactly_the_two_github_hosts() -> None:
    assert frozenset({"github.com", "release-assets.githubusercontent.com"}) == ASSET_HOSTS


# ---------------------------------------------------------------------------
# The file side: findling.embed.weights
# ---------------------------------------------------------------------------

WEIGHTS = b"stand-in for the fp32 onnx file\n" * 40
WEIGHTS_SHA256 = hashlib.sha256(WEIGHTS).hexdigest()


@pytest.fixture
def small_release(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the recorded digest and length at the small stand-in file."""
    monkeypatch.setattr(weights, "FP32_SHA256", WEIGHTS_SHA256)
    monkeypatch.setattr(weights, "FP32_BYTES", len(WEIGHTS))


@pytest.fixture(autouse=True)
def _fresh_cache() -> Iterator[None]:
    weights.forget_verdicts()
    yield
    weights.forget_verdicts()


class _Fetch:
    """A fetch double: hands prepared bytes to ``write`` and counts its calls."""

    def __init__(self, body: bytes = WEIGHTS, error: Exception | None = None) -> None:
        self._body = body
        self._error = error
        self.calls = 0

    async def __call__(self, url: str, write: Callable[[bytes], Awaitable[None]], *, cap: int) -> None:
        del url, cap
        self.calls += 1
        half = len(self._body) // 2
        await write(self._body[:half])
        if self._error is not None:
            raise self._error
        await write(self._body[half:])


def _leftovers(models_dir: Path) -> list[str]:
    directory = models_dir / weights.FP32_DIR_NAME
    return sorted(path.name for path in directory.iterdir()) if directory.exists() else []


def _place(models_dir: Path, body: bytes = WEIGHTS) -> Path:
    target = weights.fp32_weights_path(models_dir)
    target.parent.mkdir(parents=True)
    target.write_bytes(body)
    return target


def test_the_recorded_asset_is_the_release_of_plan_25_01() -> None:
    assert weights.FP32_SHA256 == "ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665"
    assert weights.FP32_BYTES == 470_268_510
    assert weights.FP32_ASSET_URL == (
        "https://github.com/street1983nk/nextcloud-search/releases/download/"
        "model-e5-small-fp32-614241f/multilingual-e5-small-fp32-614241f.onnx"
    )
    assert httpx.URL(weights.FP32_ASSET_URL).host in ASSET_HOSTS
    assert frozenset({weights.PROCURED, weights.UNAVAILABLE, weights.WRONG_DIGEST, weights.NO_ROOM}) == (
        weights.PROCURE_OUTCOMES
    )


@pytest.mark.usefixtures("small_release")
async def test_procure_installs_a_matching_download_and_leaves_no_part(tmp_path: Path) -> None:
    outcome = await weights.procure_fp32(tmp_path, _Fetch(), min_free_bytes=0)

    assert outcome == weights.PROCURED
    target = tmp_path / "multilingual-e5-small-fp32" / "model.onnx"
    assert target.read_bytes() == WEIGHTS
    assert _leftovers(tmp_path) == ["model.onnx"]
    assert weights.fp32_verified(tmp_path) is True


@pytest.mark.usefixtures("small_release")
async def test_a_failing_fetch_is_unavailable_and_leaves_nothing(tmp_path: Path) -> None:
    outcome = await weights.procure_fp32(tmp_path, _Fetch(error=OSError("connection reset")), min_free_bytes=0)

    assert outcome == weights.UNAVAILABLE
    assert _leftovers(tmp_path) == []


@pytest.mark.usefixtures("small_release")
async def test_a_refused_asset_is_unavailable_and_leaves_nothing(tmp_path: Path) -> None:
    outcome = await weights.procure_fp32(tmp_path, _Fetch(error=AssetRefused("host")), min_free_bytes=0)

    assert outcome == weights.UNAVAILABLE
    assert _leftovers(tmp_path) == []


@pytest.mark.usefixtures("small_release")
async def test_a_wrong_digest_of_the_right_length_is_refused_and_leaves_nothing(tmp_path: Path) -> None:
    forged = bytes(reversed(WEIGHTS))
    assert len(forged) == len(WEIGHTS)

    outcome = await weights.procure_fp32(tmp_path, _Fetch(forged), min_free_bytes=0)

    assert outcome == weights.WRONG_DIGEST
    assert _leftovers(tmp_path) == []


@pytest.mark.usefixtures("small_release")
async def test_a_short_download_is_refused_and_leaves_nothing(tmp_path: Path) -> None:
    outcome = await weights.procure_fp32(tmp_path, _Fetch(WEIGHTS[:-1]), min_free_bytes=0)

    assert outcome == weights.WRONG_DIGEST
    assert _leftovers(tmp_path) == []


@pytest.mark.usefixtures("small_release")
async def test_a_full_volume_at_the_fsync_is_no_room_and_leaves_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Code review WR-03: the free-space precheck runs before the bytes are
    # written, so the realistic ENOSPC arrives at the fsync in front of the
    # rename. The module contract holds there as well: an outcome out of
    # PROCURE_OUTCOMES, never an exception, and no ``.part`` stays behind.
    def full(sink: IO[bytes]) -> None:
        del sink
        raise OSError(errno.ENOSPC, "no space left on device")

    monkeypatch.setattr(weights, "_seal", full)

    outcome = await weights.procure_fp32(tmp_path, _Fetch(), min_free_bytes=0)

    assert outcome == weights.NO_ROOM
    assert _leftovers(tmp_path) == []


@pytest.mark.usefixtures("small_release")
async def test_any_other_oserror_at_the_fsync_is_unavailable_and_leaves_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing(sink: IO[bytes]) -> None:
        del sink
        raise OSError(errno.EIO, "input/output error")

    monkeypatch.setattr(weights, "_seal", failing)

    outcome = await weights.procure_fp32(tmp_path, _Fetch(), min_free_bytes=0)

    assert outcome == weights.UNAVAILABLE
    assert _leftovers(tmp_path) == []


class _RaisingClose:
    """A sink whose close throws after the bytes are already synced."""

    def __init__(self, inner: IO[bytes]) -> None:
        self._inner = inner

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def close(self) -> None:
        self._inner.close()
        raise OSError(errno.EIO, "close failed")


@pytest.mark.usefixtures("small_release")
async def test_a_failing_close_after_the_seal_still_installs_the_matching_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Code review WR-03, the second unmapped call: the close of the outer
    # finally. After a successful fsync the bytes are durable, so a close that
    # throws must neither escape procure_fp32 nor cost the installation.
    original_open = Path.open

    def opening(self: Path, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        handle = original_open(self, mode, *args, **kwargs)
        if self.name.endswith(weights.PART_SUFFIX):
            return _RaisingClose(cast("IO[bytes]", handle))
        return handle

    monkeypatch.setattr(Path, "open", opening)

    outcome = await weights.procure_fp32(tmp_path, _Fetch(), min_free_bytes=0)

    assert outcome == weights.PROCURED
    assert _leftovers(tmp_path) == ["model.onnx"]
    assert weights.fp32_verified(tmp_path) is True


@pytest.mark.usefixtures("small_release")
async def test_too_little_room_is_no_room_and_nothing_is_fetched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reserve = 1000
    free = len(WEIGHTS) + reserve - 1

    def disk_usage(_path: object) -> SimpleNamespace:
        return SimpleNamespace(total=free * 2, used=free, free=free)

    monkeypatch.setattr(weights.shutil, "disk_usage", disk_usage)
    fetch = _Fetch()

    outcome = await weights.procure_fp32(tmp_path, fetch, min_free_bytes=reserve)

    assert outcome == weights.NO_ROOM
    assert fetch.calls == 0
    assert not weights.fp32_weights_path(tmp_path).exists()


@pytest.mark.usefixtures("small_release")
async def test_procure_through_the_real_fetch_over_a_mock_transport(tmp_path: Path) -> None:
    release = _Release({weights.FP32_ASSET_URL: _redirect(ASSET), ASSET: _ok(WEIGHTS)})

    async with release.client() as client:

        async def fetch(url: str, write: Callable[[bytes], Awaitable[None]], *, cap: int) -> None:
            await fetch_release_asset(url, write, cap=cap, client=client)

        outcome = await weights.procure_fp32(tmp_path, fetch, min_free_bytes=0)

    assert outcome == weights.PROCURED
    assert weights.fp32_weights_path(tmp_path).read_bytes() == WEIGHTS
    assert [request.url.host for request in release.requests] == ["github.com", "release-assets.githubusercontent.com"]


@pytest.mark.usefixtures("small_release")
def test_a_sideloaded_file_is_verified_once_and_again_after_a_change(tmp_path: Path) -> None:
    target = _place(tmp_path)
    before = weights.hash_count()

    assert weights.fp32_verified(tmp_path) is True
    assert weights.hash_count() == before + 1

    assert weights.fp32_verified(tmp_path) is True
    assert weights.hash_count() == before + 1

    status = target.stat()
    os.utime(target, ns=(status.st_atime_ns, status.st_mtime_ns + 1_000_000_000))

    assert weights.fp32_verified(tmp_path) is True
    assert weights.hash_count() == before + 2


@pytest.mark.usefixtures("small_release")
def test_a_sideloaded_file_with_a_wrong_digest_is_not_verified(tmp_path: Path) -> None:
    _place(tmp_path, bytes(reversed(WEIGHTS)))

    assert weights.fp32_verified(tmp_path) is False


@pytest.mark.usefixtures("small_release")
def test_a_file_of_the_wrong_size_is_not_verified_and_not_hashed(tmp_path: Path) -> None:
    _place(tmp_path, WEIGHTS + b"x")
    before = weights.hash_count()

    assert weights.fp32_verified(tmp_path) is False
    assert weights.hash_count() == before


@pytest.mark.usefixtures("small_release")
def test_a_missing_file_costs_one_stat_and_no_hash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = weights.fp32_weights_path(tmp_path)
    original = Path.stat
    stats: list[Path] = []

    def counting_stat(self: Path, *, follow_symlinks: bool = True) -> os.stat_result:
        if self == target:
            stats.append(self)
        return original(self, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(Path, "stat", counting_stat)
    before = weights.hash_count()

    assert weights.fp32_verified(tmp_path) is False
    assert len(stats) == 1
    assert weights.hash_count() == before


@pytest.mark.usefixtures("small_release")
def test_remove_drops_a_sideloaded_file(tmp_path: Path) -> None:
    target = _place(tmp_path)
    assert weights.fp32_verified(tmp_path) is True

    assert weights.remove_fp32_weights(tmp_path) is True
    assert not target.exists()
    assert weights.fp32_verified(tmp_path) is False
    assert weights.remove_fp32_weights(tmp_path) is False


def test_clear_leftovers_removes_only_the_part_file(tmp_path: Path) -> None:
    directory = tmp_path / weights.FP32_DIR_NAME
    directory.mkdir()
    (directory / "model.onnx.part").write_bytes(b"half")
    (directory / "model.onnx").write_bytes(b"whole")
    (directory / "notes.txt").write_text("keep", encoding="utf-8")

    assert weights.clear_leftovers(tmp_path) == 1
    assert sorted(path.name for path in directory.iterdir()) == ["model.onnx", "notes.txt"]
    assert weights.clear_leftovers(tmp_path) == 0
