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
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient

from findling.main import APP, enabled_handler
from findling.nc.client import AppAPIAuthMiddleware, AsyncNextcloudApp

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"


@pytest.fixture
def client() -> TestClient:
    """A client that runs the lifespan, so ``set_handlers`` registers its routes."""
    with TestClient(APP) as running_client:
        return running_client


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


def test_only_the_client_module_imports_nc_py_api() -> None:
    importers = sorted(
        path.relative_to(PACKAGE_ROOT).as_posix()
        for path in PACKAGE_ROOT.rglob("*.py")
        if "nc_py_api" in path.read_text(encoding="utf-8")
    )

    assert importers == ["nc/client.py"]
