"""The AppAPI handshake of the ExApp.

Five claims, one test each. The first two are Pitfall 7 from the phase research:
``set_handlers`` inspects the handler with ``asyncio.iscoroutinefunction``, and a
synchronous handler only produces a DeprecationWarning today while it breaks hard
in nc_py_api 0.31.0. Since pytest runs with ``filterwarnings = error``, the
mistake cannot reach a commit unnoticed.

The last claim keeps the nc_py_api seam honest at the file level, which is the
same property Gate A proves through the AST.
"""

import asyncio
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from conftest import Corpus
from findling.config import settings
from findling.main import (
    APP,
    active_poller,
    active_reconcile,
    enabled_handler,
    unusable_startup_variables,
)
from findling.nc.client import AppAPIAuthMiddleware, AsyncNextcloudApp

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"

Sign = Callable[[str], dict[str, str]]


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A client that runs the lifespan for as long as the test uses it.

    The yield has to sit inside the with block. Returning the client from inside
    it hands the test a client whose lifespan has already been shut down, so the
    test would prove that the routes survive their own shutdown rather than that
    the lifespan registers them.
    """
    with TestClient(APP) as running_client:
        yield running_client


def test_enabled_handler_is_a_coroutine_function() -> None:
    assert asyncio.iscoroutinefunction(enabled_handler)


async def test_enabled_handler_reports_no_error_when_enabled() -> None:
    # AppAPI reads the return value as an error text; the empty string means "fine".
    # The handler must not touch nc, so passing None through a cast is safe here.
    result = await enabled_handler(True, cast("AsyncNextcloudApp", None))

    assert result == ""


def test_app_carries_the_appapi_auth_middleware() -> None:
    assert any(middleware.cls is AppAPIAuthMiddleware for middleware in APP.user_middleware)


def test_heartbeat_answers_without_an_auth_header(client: TestClient) -> None:
    # AppAPIAuthMiddleware always excludes /heartbeat, otherwise registration
    # could never complete: AppAPI polls it before any secret is exchanged.
    response = client.get("/heartbeat")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_the_lifespan_registers_the_appapi_routes_exactly_once() -> None:
    # APP is a module level object, so it outlives every single lifespan run. Each
    # run used to call set_handlers again, which added a second /enabled,
    # /heartbeat and /init to the router. The first run below may still register,
    # the second one must change nothing.
    with TestClient(APP):
        pass
    after_first = [getattr(route, "path", "") for route in APP.routes]

    with TestClient(APP):
        pass
    after_second = [getattr(route, "path", "") for route in APP.routes]

    assert after_first == after_second
    assert after_first.count("/heartbeat") == 1


def test_a_missing_app_port_is_named_instead_of_raising_a_key_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # nc_py_api does int(environ["APP_PORT"]) while the server is binding, so the
    # unchecked case is a KeyError several frames deep that never names the
    # variable. That is the single most common reason a manual run does not come up.
    monkeypatch.delenv("HP_SHARED_KEY", raising=False)
    monkeypatch.delenv("APP_PORT", raising=False)

    assert unusable_startup_variables() == ["APP_PORT"]


def test_a_non_numeric_app_port_is_named_too(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HP_SHARED_KEY", raising=False)
    monkeypatch.setenv("APP_PORT", "ten")

    assert unusable_startup_variables() == ["APP_PORT"]


def test_harp_needs_no_app_port(monkeypatch: pytest.MonkeyPatch) -> None:
    # Under HaRP the server binds a unix socket and the port is never read, so
    # demanding it would refuse to start exactly the deployment AppAPI recommends.
    monkeypatch.setenv("HP_SHARED_KEY", "not-a-real-key")
    monkeypatch.delenv("APP_PORT", raising=False)

    assert unusable_startup_variables() == []


def test_a_numeric_app_port_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HP_SHARED_KEY", raising=False)
    monkeypatch.setenv("APP_PORT", "10035")

    assert unusable_startup_variables() == []


# ---------------------------------------------------------------------------
# The reconcile beside the poller. Two tasks, one process, and the whole point of
# the arrangement is that the second one cannot take the first one with it: the
# search is what a user sees, and a repair that failed must never cost it.
# ---------------------------------------------------------------------------


class _FakeReconcile:
    """A reconcile that only records what the lifespan did to it."""

    def __init__(self) -> None:
        self.armed = False
        self.closed = False
        self.rounds = 0

    def arm(self) -> None:
        self.armed = True

    def silence(self) -> None:
        self.armed = False

    async def run(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            self.rounds += 1
            await asyncio.sleep(0.001)

    async def aclose(self) -> None:
        self.closed = True


class _ExplodingReconcile(_FakeReconcile):
    """A reconcile that ends the way an unhandled bug would end it."""

    async def run(self, stop_event: asyncio.Event) -> None:
        del stop_event
        raise RuntimeError("the file list could not be read")


def _install(monkeypatch: pytest.MonkeyPatch, replacement: _FakeReconcile) -> _FakeReconcile:
    monkeypatch.setattr("findling.main.default_reconcile", lambda: replacement)
    return replacement


def test_the_reconcile_runs_as_a_task_beside_the_poller(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _install(monkeypatch, _FakeReconcile())

    with TestClient(APP):
        assert active_reconcile() is fake
        assert active_poller() is not None

    assert fake.closed


def test_reconcile_task_is_not_started_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    # A backend whose admin switched the comparison off must not walk the file
    # list anyway, and the switch has to be read where the task is created rather
    # than inside a round that already opened a connection.
    fake = _install(monkeypatch, _FakeReconcile())
    monkeypatch.setenv("FINDLING_RECONCILE_ENABLED", "false")
    settings.cache_clear()
    try:
        with TestClient(APP):
            assert active_reconcile() is None
            assert active_poller() is not None
    finally:
        settings.cache_clear()

    assert fake.rounds == 0


def test_the_reconcile_task_ends_with_the_lifespan(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _install(monkeypatch, _FakeReconcile())

    with TestClient(APP):
        pass

    assert active_reconcile() is None
    assert fake.closed


def test_failing_reconcile_does_not_stop_the_poller(monkeypatch: pytest.MonkeyPatch) -> None:
    # The property the whole arrangement exists for. An exception in the repair
    # task is a log line, never a dead container and never a stopped indexer.
    _install(monkeypatch, _ExplodingReconcile())

    with TestClient(APP) as client:
        assert client.get("/heartbeat").status_code == 200
        poller = active_poller()
        assert poller is not None


async def test_the_enabled_handler_arms_and_silences_the_reconcile(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _install(monkeypatch, _FakeReconcile())

    with TestClient(APP):
        await enabled_handler(True, cast("AsyncNextcloudApp", None))
        assert fake.armed is True

        await enabled_handler(False, cast("AsyncNextcloudApp", None))
        assert fake.armed is False


@pytest.mark.usefixtures("appapi_environment")
def test_the_search_answers_while_a_reconcile_round_is_running(
    monkeypatch: pytest.MonkeyPatch,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The reconcile is repair work beside the search, not in front of it. A round
    # that held the event loop would be invisible in every counter and would show
    # up as a search that hangs.
    fake = _install(monkeypatch, _FakeReconcile())

    with TestClient(APP) as client:
        answer: dict[str, Any] = client.post(
            "/search",
            json={"query": "Kündigungsfrist"},
            headers=sign(indexed_volume.bob),
        ).json()

    assert answer["candidates"]
    assert fake.rounds > 0


def test_only_the_client_module_imports_nc_py_api() -> None:
    importers = sorted(
        path.relative_to(PACKAGE_ROOT).as_posix()
        for path in PACKAGE_ROOT.rglob("*.py")
        if "nc_py_api" in path.read_text(encoding="utf-8")
    )

    assert importers == ["nc/client.py"]
