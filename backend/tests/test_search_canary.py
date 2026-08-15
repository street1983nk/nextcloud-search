"""POST /search: the container proof and the identity rules around it.

Six claims, one test each. Three of them are security claims rather than feature
claims: a body may not name a user, a request without an identity gets 401, and
the snippet stays free of markup because the unified search UI interpolates the
subline as text and would show any tag verbatim to the user.

The requests carry a real AppAPI header. The header is base64 of
``username:app_secret`` and the middleware compares that secret against the
environment, so the tests exercise the same code path a proxied request takes,
including the empty user name in the unauthorized case.
"""

from base64 import b64encode
from datetime import datetime
from socket import gethostname

import pytest
from fastapi.testclient import TestClient

from findling.api.search import build_canary_hits
from findling.main import APP

APP_ID = "findling_backend"
APP_VERSION = "0.1.0"
# Not a real credential: the middleware only checks equality against the
# environment it is given, so any value works as long as both sides agree.
APP_CREDENTIAL = "unit-test-credential"


@pytest.fixture(autouse=True)
def _appapi_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ID", APP_ID)
    monkeypatch.setenv("APP_VERSION", APP_VERSION)
    monkeypatch.setenv("APP_SECRET", APP_CREDENTIAL)
    monkeypatch.setenv("NEXTCLOUD_URL", "http://localhost:8080")


@pytest.fixture
def client() -> TestClient:
    # No context manager on purpose: the lifespan belongs to the handshake tests,
    # the router is mounted at import time and needs nothing from it.
    return TestClient(APP)


def appapi_headers(user_id: str) -> dict[str, str]:
    """Build the signed header AppAPI would send for this user."""
    authorization = b64encode(f"{user_id}:{APP_CREDENTIAL}".encode()).decode()
    return {
        "EX-APP-ID": APP_ID,
        "EX-APP-VERSION": APP_VERSION,
        "AUTHORIZATION-APP-API": authorization,
    }


def test_canary_hit_carries_host_time_and_user() -> None:
    hits = build_canary_hits("alice")

    assert len(hits) == 1
    snippet = hits[0].snippet
    assert gethostname() in snippet
    assert "alice" in snippet
    # Read the timestamp back independently instead of rebuilding the format
    # string of the implementation: a shared pattern would prove nothing.
    stamp = snippet.split(" at ", maxsplit=1)[1].split(" for user ", maxsplit=1)[0]
    assert datetime.fromisoformat(stamp).tzinfo is not None


def test_snippet_has_no_markup() -> None:
    snippet = build_canary_hits("alice")[0].snippet

    # The unified search UI renders the subline as Vue text interpolation, so a
    # tag would reach the user literally instead of being rendered.
    assert "<" not in snippet
    assert ">" not in snippet


def test_user_id_in_the_body_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/search",
        json={"query": "contract", "userId": "bob"},
        headers=appapi_headers("alice"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "user identity is taken from the AppAPI header only"


@pytest.mark.parametrize("limit", [0, 101])
def test_limit_out_of_range_is_rejected(client: TestClient, limit: int) -> None:
    response = client.post(
        "/search",
        json={"query": "contract", "limit": limit},
        headers=appapi_headers("alice"),
    )

    assert response.status_code == 422


def test_missing_user_id_is_unauthorized(client: TestClient) -> None:
    # A signed header without a user name: the signature checks out, the identity
    # does not exist. Answering with results here would be the actual bug.
    response = client.post("/search", json={"query": "contract"}, headers=appapi_headers(""))

    assert response.status_code == 401


def test_response_carries_the_frozen_protocol_fields(client: TestClient) -> None:
    response = client.post("/search", json={"query": "contract"}, headers=appapi_headers("alice"))

    assert response.status_code == 200
    hit = response.json()["results"][0]
    assert {"fileId", "title", "snippet", "highlights"} <= set(hit)
    assert hit["highlights"] == []
