"""POST /probe and GET /probe/state: the door of the pre-check (PRUEF-01, SC3).

The check itself is tested in ``test_probe_run.py``; here the door: the codes it
answers with, the closed sets of its body, the field set of its state answer
and the two ADMIN routes of the manifest. A fake check stands in for ProbeRun,
installed through the dependency the route reads, so no lifespan is needed.
"""

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from findling import probe
from findling.api.probe import probe_run
from findling.main import APP

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

BACKEND_INFO = Path(__file__).resolve().parents[2] / "backend" / "appinfo" / "info.xml"

FIELDS = {
    "id",
    "state",
    "step",
    "bytesDone",
    "bytesTotal",
    "verdict",
    "cause",
    "numbers",
    "targetProfile",
    "targetPrecision",
    "fp32Fetched",
    "fp32Deleted",
    "startedAt",
    "finishedAt",
}

PROBE_ID = "0123456789abcdef"


class FakeRun:
    """A check that answers what it is told and records its starts."""

    def __init__(self, answer: tuple[str, str] = ("started", PROBE_ID)) -> None:
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    async def start(self, profile_name: str, precision: str) -> tuple[str, str]:
        self.calls.append((profile_name, precision))
        return self.answer


@pytest.fixture(autouse=True)
def _resting_probe() -> Iterator[None]:
    probe.reset()
    yield
    probe.reset()
    APP.dependency_overrides.pop(probe_run, None)


def _install(run: FakeRun | None) -> None:
    APP.dependency_overrides[probe_run] = lambda: run


def _start(client: TestClient, sign: Sign, body: object, user: str = "admin") -> tuple[int, dict[str, object]]:
    response = client.post("/probe", json=body, headers=sign(user))
    return response.status_code, response.json()


def test_a_start_answers_202_with_the_id_of_the_check(client: TestClient, sign: Sign) -> None:
    run = FakeRun()
    _install(run)

    code, answer = _start(client, sign, {"profile": "standard", "precision": "int8"})

    assert code == 202
    assert answer == {"id": PROBE_ID}
    assert run.calls == [("standard", "int8")]


def test_a_second_start_while_one_runs_is_busy_with_the_running_id(client: TestClient, sign: Sign) -> None:
    _install(FakeRun(("busy", PROBE_ID)))

    code, answer = _start(client, sign, {"profile": "performance", "precision": "fp32"})

    assert code == 409
    assert answer == {"state": "busy", "id": PROBE_ID}


def test_a_start_during_a_rebuild_is_refused_as_rebuilding(client: TestClient, sign: Sign) -> None:
    _install(FakeRun(("rebuilding", "")))

    code, answer = _start(client, sign, {"profile": "standard", "precision": "int8"})

    assert code == 409
    assert answer == {"state": "rebuilding"}


@pytest.mark.parametrize(
    "body",
    [
        {"profile": "turbo", "precision": "int8"},
        {"profile": "standard", "precision": "fp16"},
        {"profile": "standard"},
        {"profile": "standard", "precision": "int8", "path": "/etc/passwd"},
        {"profile": ["standard"], "precision": "int8"},
    ],
)
def test_a_foreign_value_is_422_and_never_reaches_the_check(
    client: TestClient, sign: Sign, body: dict[str, object]
) -> None:
    run = FakeRun()
    _install(run)

    code, _ = _start(client, sign, body)

    assert code == 422
    assert run.calls == []


def test_without_a_lifespan_the_start_is_503(client: TestClient, sign: Sign) -> None:
    _install(None)

    code, answer = _start(client, sign, {"profile": "standard", "precision": "int8"})

    assert code == 503
    assert answer == {"state": "unavailable"}


def test_without_any_override_the_start_outside_a_lifespan_is_503(client: TestClient, sign: Sign) -> None:
    # The real dependency, and no lifespan entered: main holds no check.
    code, _ = _start(client, sign, {"profile": "standard", "precision": "int8"})

    assert code == 503


def test_a_start_that_breaks_is_503_and_not_a_500(client: TestClient, sign: Sign) -> None:
    class Broken(FakeRun):
        async def start(self, profile_name: str, precision: str) -> tuple[str, str]:
            raise RuntimeError(profile_name + precision)

    _install(Broken())

    code, answer = _start(client, sign, {"profile": "standard", "precision": "int8"})

    assert code == 503
    assert answer == {"state": "unavailable"}


def test_a_start_without_a_user_is_unauthorized(client: TestClient, sign: Sign) -> None:
    run = FakeRun()
    _install(run)

    code, _ = _start(client, sign, {"profile": "standard", "precision": "int8"}, user="")

    assert code == 401
    assert run.calls == []


def test_a_start_without_any_appapi_header_is_unauthorized(client: TestClient) -> None:
    _install(FakeRun())

    response = client.post("/probe", json={"profile": "standard", "precision": "int8"})

    assert response.status_code == 401


def test_the_state_before_any_check_is_idle_with_the_whole_field_set(client: TestClient, sign: Sign) -> None:
    response = client.get("/probe/state", headers=sign("admin"))

    assert response.status_code == 200
    answer = response.json()
    assert set(answer) == FIELDS
    assert answer["state"] == "idle"
    assert answer["id"] == ""
    assert answer["numbers"] == {}
    assert answer["startedAt"] == 0
    assert answer["finishedAt"] == 0


def test_the_state_of_a_running_check_carries_its_step_and_bytes(client: TestClient, sign: Sign) -> None:
    probe.begin(PROBE_ID, "standard", "fp32", 1_800_000_000.5)
    probe.note_step("download", 10, 100)

    answer = client.get("/probe/state", headers=sign("admin")).json()

    assert set(answer) == FIELDS
    assert answer["id"] == PROBE_ID
    assert answer["state"] == "running"
    assert answer["step"] == "download"
    assert (answer["bytesDone"], answer["bytesTotal"]) == (10, 100)
    assert (answer["targetProfile"], answer["targetPrecision"]) == ("standard", "fp32")
    assert answer["startedAt"] == 1_800_000_000


def test_the_state_of_a_finished_check_carries_codes_and_numbers_only(client: TestClient, sign: Sign) -> None:
    probe.begin(PROBE_ID, "performance", "int8", 1_800_000_000.0)
    probe.note_step("calc")
    probe.finish(
        "nofit",
        "memory_short",
        {"slots": 3, "need": 900, "available": 800},
        fp32_fetched=True,
        fp32_deleted=True,
        now=1_800_000_060.0,
    )

    answer = client.get("/probe/state", headers=sign("admin")).json()

    assert set(answer) == FIELDS
    assert (answer["state"], answer["verdict"], answer["cause"]) == ("done", "nofit", "memory_short")
    assert answer["numbers"] == {"slots": 3, "need": 900, "available": 800}
    assert set(answer["numbers"]) <= probe.NUMBER_KEYS
    assert (answer["fp32Fetched"], answer["fp32Deleted"]) == (True, True)
    assert answer["finishedAt"] == 1_800_000_060
    # Codes, numbers, an id and flags; never a path or a text.
    for value in answer.values():
        if isinstance(value, str):
            assert "/" not in value
            assert " " not in value


def test_the_state_measures_nothing_and_changes_nothing(client: TestClient, sign: Sign) -> None:
    before = probe.snapshot()

    client.get("/probe/state", headers=sign("admin"))

    assert probe.snapshot() is before
    assert probe.held() is False


def _block(url: str) -> str:
    manifest = BACKEND_INFO.read_text(encoding="utf-8")
    block = manifest[manifest.index(f"<url>{url}</url>") :]
    return block[: block.index("</route>")]


def test_the_start_route_is_declared_post_and_admin() -> None:
    block = _block("^/probe$")

    assert "<verb>POST</verb>" in block
    assert "<access_level>ADMIN</access_level>" in block
    assert "<bruteforce_protection>[401]</bruteforce_protection>" in block


def test_the_state_route_is_declared_get_and_admin() -> None:
    block = _block("^/probe/state$")

    assert "<verb>GET</verb>" in block
    assert "<access_level>ADMIN</access_level>" in block
    assert "<bruteforce_protection>[401]</bruteforce_protection>" in block


def test_each_probe_route_is_declared_once() -> None:
    manifest = BACKEND_INFO.read_text(encoding="utf-8")

    assert manifest.count("<url>^/probe$</url>") == 1
    assert manifest.count("<url>^/probe/state$</url>") == 1
    assert "Five routes" not in manifest
    assert "these five" not in manifest
