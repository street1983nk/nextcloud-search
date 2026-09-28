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

from pathlib import Path

import httpx
import pytest

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
