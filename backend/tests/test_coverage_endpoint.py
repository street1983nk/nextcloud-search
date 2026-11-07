"""POST /coverage: the per document coverage over the wire (plan 43-04, D-43-07, D-43-11, D-43-14).

The companion sends the mount list and the share groups that build its
denominator, and the container answers with numbers only: the three figures of
findling.store.repo.coverage_counts, their parts per group and per single
storage, whether a count is still running, and three counters of the document
key backfill of plan 43-16. A POST and not a parameter of /status, because the
mount list of a large instance does not fit the 8000 characters of leaveOut.

Held here: the topology of tests/fixtures/coverage_topology.json gives the hand
derived numbers through the route; every body outside the bounds is a 422 before
any database is opened; above the synchronous ceiling the count runs in a
background thread with a single flight and a small cache keyed by the canonical
request and the identity of both stocks; a group member without a key keeps the
answer counting; every call ends the 404 cooldown of the backfill; the route is
declared ADMIN; /status?leaveOut= stays as it was for a companion 1.6.2.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from findling.api import coverage
from findling.main import APP
from findling.store import repo
from findling.worker import doc_keys
from test_coverage_counts import _build, _by_storage, _topology

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

BACKEND_INFO = Path(__file__).resolve().parents[1] / "appinfo" / "info.xml"

ANSWER_KEYS = frozenset(
    {
        "documents",
        "embeddedDocuments",
        "judgedDocuments",
        "documentsByGroup",
        "judgedByGroup",
        "documentsByStorage",
        "judgedByStorage",
        "counting",
        "docKeysMissing",
        "docKeysUnresolved",
        "docKeysCorrected",
    }
)


@pytest.fixture(autouse=True)
def _fresh_cache() -> Any:
    coverage._reset_coverage_cache_for_tests()
    yield
    coverage.join_coverage_refresh()
    coverage._reset_coverage_cache_for_tests()


def _post(client: TestClient, headers: dict[str, str], body: object) -> Any:
    return client.post("/coverage", content=json.dumps(body), headers={**headers, "Content-Type": "application/json"})


def _topology_on(volume: Path) -> dict[str, Any]:
    data = _topology()
    _build(volume, data["rows"])
    return data


def _body(data: dict[str, Any]) -> dict[str, Any]:
    return {"mounted": data["mounted"], "groups": data["groups"]}


def _pairs(mapping: dict[str, int]) -> list[list[int]]:
    return sorted([int(key), int(value)] for key, value in mapping.items())


def test_the_topology_gives_the_hand_derived_numbers_through_the_route(
    client: TestClient, sign: Sign, volume: Path
) -> None:
    data = _topology_on(volume)
    expected = data["expected"]

    response = _post(client, sign("admin"), _body(data))

    assert response.status_code == 200, response.text
    answer = response.json()
    assert answer["counting"] is False
    assert answer["documents"] == expected["documents"]
    assert answer["embeddedDocuments"] == expected["embeddedDocuments"]
    assert answer["judgedDocuments"] == expected["judgedDocuments"]
    assert answer["documentsByGroup"] == expected["documentsByGroup"]
    assert answer["judgedByGroup"] == expected["judgedByGroup"]
    assert answer["documentsByStorage"] == _pairs(expected["documentsByStorage"])
    assert answer["judgedByStorage"] == _pairs(expected["judgedByStorage"])
    assert answer["docKeysMissing"] == 0
    assert answer["docKeysUnresolved"] == 1  # the sentinel row 1213


def test_the_answer_carries_numbers_booleans_and_null_only(client: TestClient, sign: Sign, volume: Path) -> None:
    data = _topology_on(volume)

    answer = _post(client, sign("admin"), _body(data)).json()

    assert set(answer) == ANSWER_KEYS
    assert type(answer["counting"]) is bool
    for key in ("documents", "embeddedDocuments", "judgedDocuments", "docKeysMissing", "docKeysUnresolved"):
        assert type(answer[key]) is int
    assert type(answer["docKeysCorrected"]) is int
    for key in ("documentsByGroup", "judgedByGroup"):
        assert all(type(value) is int for value in answer[key])
        assert len(answer[key]) == len(data["groups"])
    for key in ("documentsByStorage", "judgedByStorage"):
        for pair in answer[key]:
            assert len(pair) == 2
            assert all(type(value) is int for value in pair)
            assert pair[0] in data["mounted"]
            assert pair[1] > 0
    assert "/" not in json.dumps(answer)


def test_a_group_of_one_member_counts_as_a_single_storage(client: TestClient, sign: Sign, volume: Path) -> None:
    data = _topology_on(volume)
    # 31 alone is no group: it is dropped from the groups and stays a single
    # storage, so the answer has two groups and 31 among the storages.
    body = {"mounted": data["mounted"], "groups": [data["groups"][0], [31], data["groups"][1]]}

    answer = _post(client, sign("admin"), body).json()

    assert answer["documentsByGroup"] == data["expected"]["documentsByGroup"]
    assert [31, 3] in answer["documentsByStorage"]
    assert answer["documents"] == data["expected"]["documents"]


def test_the_count_follows_the_mount_list_of_the_request(client: TestClient, sign: Sign, volume: Path) -> None:
    data = _topology_on(volume)

    answer = _post(client, sign("admin"), {"mounted": [41], "groups": []}).json()

    # 41 holds one living indexed document; the topology without 41 counts it
    # nowhere (the test above), so the list of the request decides.
    assert answer["documents"] == 1
    assert answer["documentsByStorage"] == [[41, 1]]
    assert data["expected"]["documents"] == 13


# -- the bounds, all of them before any database -------------------------


def _bad_bodies() -> list[tuple[str, object]]:
    many = list(range(1, 50_002))
    members = list(range(1, 1002))
    return [
        ("too many mounted", {"mounted": many, "groups": []}),
        ("too many members", {"mounted": members, "groups": [members[:501], members[501:]]}),
        ("id zero", {"mounted": [0, 1], "groups": []}),
        ("negative id", {"mounted": [-5, 1], "groups": []}),
        ("nineteen digits", {"mounted": [10**18], "groups": []}),
        ("string id", {"mounted": ["5"], "groups": []}),
        ("boolean id", {"mounted": [True], "groups": []}),
        ("float id", {"mounted": [5.0], "groups": []}),
        ("overlapping groups", {"mounted": [1, 2, 3], "groups": [[1, 2], [2, 3]]}),
        ("member not mounted", {"mounted": [1, 2], "groups": [[1, 3]]}),
        ("extra field", {"mounted": [1], "groups": [], "leaveOut": [2]}),
        ("missing groups", {"mounted": [1]}),
        ("groups not a list of lists", {"mounted": [1], "groups": [1]}),
        ("not an object", [1, 2]),
    ]


@pytest.mark.parametrize(("case", "body"), _bad_bodies(), ids=[case for case, _ in _bad_bodies()])
def test_a_body_outside_the_bounds_is_a_422_before_any_database(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch, case: str, body: object
) -> None:
    del case
    _topology_on(volume)
    calls: list[object] = []
    monkeypatch.setattr(coverage, "coverage_counts", lambda *args, **kwargs: calls.append(args))
    monkeypatch.setattr(coverage, "open_read_only", lambda *args, **kwargs: calls.append(args))

    response = _post(client, sign("admin"), body)

    assert response.status_code == 422, response.text
    assert calls == []


def test_the_largest_body_inside_the_bounds_is_answered(client: TestClient, sign: Sign, volume: Path) -> None:
    _topology_on(volume)
    members = list(range(100_001, 101_001))
    mounted = [*range(1, 49_001), *members]
    body = {"mounted": mounted, "groups": [members[:500], members[500:]]}

    response = _post(client, sign("admin"), body)

    assert response.status_code == 200, response.text
    assert len(response.json()["documentsByGroup"]) == 2


def test_the_largest_id_inside_the_bounds_is_answered(client: TestClient, sign: Sign, volume: Path) -> None:
    _topology_on(volume)

    response = _post(client, sign("admin"), {"mounted": [10**18 - 1], "groups": []})

    assert response.status_code == 200, response.text
    assert response.json()["documents"] == 0


# -- the background count ------------------------------------------------


def test_above_the_ceiling_the_count_runs_in_the_background(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = _topology_on(volume)
    monkeypatch.setattr(coverage, "COVERAGE_SYNC_CEILING", 5)

    first = _post(client, sign("admin"), _body(data)).json()

    assert first["counting"] is True
    for key in ("documents", "embeddedDocuments", "judgedDocuments", "documentsByGroup", "judgedByGroup"):
        assert first[key] is None
    assert first["documentsByStorage"] is None
    assert first["judgedByStorage"] is None

    coverage.join_coverage_refresh()
    second = _post(client, sign("admin"), _body(data)).json()

    assert second["counting"] is False
    assert second["documents"] == data["expected"]["documents"]
    assert second["judgedByGroup"] == data["expected"]["judgedByGroup"]


def test_a_second_request_while_the_count_runs_starts_no_second_thread(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = _topology_on(volume)
    monkeypatch.setattr(coverage, "COVERAGE_SYNC_CEILING", 5)
    started: list[int] = []
    real = coverage.coverage_counts
    gate = threading.Event()

    def slow(*args: Any, **kwargs: Any) -> repo.CoverageCounts:
        started.append(1)
        gate.wait(5)
        return real(*args, **kwargs)

    monkeypatch.setattr(coverage, "coverage_counts", slow)

    _post(client, sign("admin"), _body(data))
    _post(client, sign("admin"), _body(data))
    _post(client, sign("admin"), {"mounted": [41], "groups": []})
    gate.set()
    coverage.join_coverage_refresh()

    assert started == [1]


def test_the_cache_key_ignores_the_order_of_the_ids(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = _topology_on(volume)
    monkeypatch.setattr(coverage, "COVERAGE_SYNC_CEILING", 5)
    _post(client, sign("admin"), _body(data))
    coverage.join_coverage_refresh()
    shuffled = {
        "mounted": list(reversed(data["mounted"])),
        "groups": [list(reversed(group)) for group in data["groups"]],
    }

    answer = _post(client, sign("admin"), shuffled).json()

    assert answer["counting"] is False
    assert answer["documents"] == data["expected"]["documents"]
    assert coverage.canonical_key([3, 1, 2], [[2, 1]]) == coverage.canonical_key([1, 2, 3], [[1, 2]])
    assert coverage.canonical_key([1, 2, 3, 4], [[1, 2], [3, 4]]) == coverage.canonical_key(
        [1, 2, 3, 4], [[4, 3], [2, 1]]
    )
    assert coverage.canonical_key([1, 2, 3], [[1, 2]]) != coverage.canonical_key([1, 2, 3], [[1, 3]])


def test_a_replaced_state_database_drops_the_cache(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = _topology_on(volume)
    monkeypatch.setattr(coverage, "COVERAGE_SYNC_CEILING", 5)
    _post(client, sign("admin"), _body(data))
    coverage.join_coverage_refresh()
    assert _post(client, sign("admin"), _body(data)).json()["counting"] is False

    # A new file in place of the old one: another inode.
    replacement = volume / "state.db.new"
    replacement.write_bytes((volume / "state.db").read_bytes())
    for suffix in ("-wal", "-shm"):
        (volume / f"state.db{suffix}").unlink(missing_ok=True)
    os.replace(replacement, volume / "state.db")

    assert _post(client, sign("admin"), _body(data)).json()["counting"] is True


def test_a_fifth_key_lets_the_oldest_go(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _topology_on(volume)
    monkeypatch.setattr(coverage, "COVERAGE_SYNC_CEILING", 0)
    bodies = [{"mounted": [storage_id], "groups": []} for storage_id in (11, 12, 13, 21, 22)]
    for body in bodies:
        _post(client, sign("admin"), body)
        coverage.join_coverage_refresh()

    assert coverage.cached_keys() == 4
    assert _post(client, sign("admin"), bodies[0]).json()["counting"] is True
    coverage.join_coverage_refresh()
    assert _post(client, sign("admin"), bodies[4]).json()["counting"] is False


def test_a_stale_figure_is_answered_and_starts_the_next_count(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = _topology_on(volume)
    monkeypatch.setattr(coverage, "COVERAGE_SYNC_CEILING", 5)
    _post(client, sign("admin"), _body(data))
    coverage.join_coverage_refresh()
    later = time.monotonic() + coverage.COVERAGE_CACHE_SECONDS + 1
    monkeypatch.setattr(coverage, "_monotonic", lambda: later)
    counted: list[int] = []
    real = coverage.coverage_counts
    monkeypatch.setattr(coverage, "coverage_counts", lambda *a, **k: counted.append(1) or real(*a, **k))

    answer = _post(client, sign("admin"), _body(data)).json()
    coverage.join_coverage_refresh()

    assert answer["counting"] is False
    assert answer["documents"] == data["expected"]["documents"]
    assert counted == [1]


def test_a_count_that_fails_in_the_background_leaves_no_entry_and_is_tried_again(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    data = _topology_on(volume)
    monkeypatch.setattr(coverage, "COVERAGE_SYNC_CEILING", 5)

    def broken(*args: Any, **kwargs: Any) -> repo.CoverageCounts:
        raise sqlite3.OperationalError("database /secret/path is locked")

    monkeypatch.setattr(coverage, "coverage_counts", broken)
    _post(client, sign("admin"), _body(data))
    coverage.join_coverage_refresh()

    assert coverage.cached_keys() == 0
    assert "OperationalError" in caplog.text
    assert "/secret/path" not in caplog.text
    monkeypatch.setattr(coverage, "coverage_counts", repo.coverage_counts)
    _post(client, sign("admin"), _body(data))
    coverage.join_coverage_refresh()
    assert _post(client, sign("admin"), _body(data)).json()["counting"] is False


# -- the document key backfill -------------------------------------------


def test_a_group_member_without_a_key_keeps_the_answer_counting(client: TestClient, sign: Sign, volume: Path) -> None:
    data = _topology()
    variant = next(item for item in data["variants"] if item["name"] == "backfill_open")
    _build(volume, [*data["rows"], *variant["extraRows"]])

    answer = _post(client, sign("admin"), _body(data)).json()

    # Never a figure on reader paths (D-43-14): nothing but null while a key
    # is missing, and the missing rows are named.
    assert answer["counting"] is True
    assert answer["documents"] is None
    assert answer["judgedByGroup"] is None
    assert answer["docKeysMissing"] >= variant["expected"]["docKeysMissing"]


def test_a_single_storage_without_a_key_does_not_hold_the_figure_back(
    client: TestClient, sign: Sign, volume: Path
) -> None:
    data = _topology_on(volume)

    # Row 3106 of storage 31 has no key; a single storage counts rows.
    answer = _post(client, sign("admin"), _body(data)).json()

    assert answer["counting"] is False
    assert answer["docKeysMissing"] >= 1


def test_every_call_ends_the_cooldown_of_the_backfill(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = _topology_on(volume)
    calls: list[int] = []
    monkeypatch.setattr(coverage, "note_coverage_call", lambda: calls.append(1))

    _post(client, sign("admin"), _body(data))
    _post(client, sign("admin"), _body(data))

    assert calls == [1, 1]


def test_the_route_reports_the_corrections_of_the_verify_pass(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = _topology_on(volume)
    monkeypatch.setattr(coverage, "doc_keys_corrected", lambda: 7)

    assert _post(client, sign("admin"), _body(data)).json()["docKeysCorrected"] == 7


def test_the_route_imports_the_backfill_hook_itself() -> None:
    assert coverage.note_coverage_call is doc_keys.note_coverage_call
    assert coverage.doc_keys_corrected is doc_keys.doc_keys_corrected


# -- states of the volume ------------------------------------------------


def test_a_volume_without_a_state_answers_zeros(client: TestClient, sign: Sign, volume: Path) -> None:
    del volume

    answer = _post(client, sign("admin"), {"mounted": [1, 2], "groups": [[1, 2]]}).json()

    assert answer["counting"] is False
    assert answer["documents"] == 0
    assert answer["documentsByGroup"] == [0]
    assert answer["documentsByStorage"] == []


def test_an_unreadable_state_is_a_503_without_a_path(
    client: TestClient, sign: Sign, volume: Path, caplog: pytest.LogCaptureFixture
) -> None:
    (volume / "state.db").write_bytes(b"this is no database at all, it only has the name of one")

    response = _post(client, sign("admin"), {"mounted": [1], "groups": []})

    assert response.status_code == 503
    assert str(volume) not in caplog.text
    assert str(volume) not in response.text


# -- the size of the largest answer --------------------------------------


def test_the_answer_for_fifty_thousand_storages_stays_small(capsys: pytest.CaptureFixture[str]) -> None:
    counts = repo.CoverageCounts(
        documents=50_000 * 120,
        embedded_documents=50_000 * 100,
        judged_documents=50_000 * 130,
        documents_by_group=(),
        judged_by_group=(),
        documents_by_storage=dict.fromkeys(range(1000000, 1050000), 120),
        judged_by_storage=dict.fromkeys(range(1000000, 1050000), 130),
        doc_keys_missing=0,
    )
    started = time.perf_counter()
    answer = coverage.answer_of(counts, missing=0, unresolved=0, corrected=0)
    body = APP.router.default_response_class(answer.model_dump(by_alias=True)).body
    took = time.perf_counter() - started

    assert len(body) < 2 * 1024 * 1024
    with capsys.disabled():
        print(f"\n50 000 storages: {len(body)} bytes, {took:.3f} s to build and serialise")


# -- the declaration and the neighbours ----------------------------------


def test_the_route_is_declared_admin_and_post() -> None:
    manifest = BACKEND_INFO.read_text(encoding="utf-8")
    block = manifest[manifest.index("<url>^/coverage$</url>") :]
    block = block[: block.index("</route>")]

    assert "<verb>POST</verb>" in block
    assert "<access_level>ADMIN</access_level>" in block
    assert "<headers_to_exclude>[]</headers_to_exclude>" in block


def test_the_route_is_mounted() -> None:
    assert "/coverage" in set(APP.openapi()["paths"])


def test_status_with_leave_out_still_answers_for_a_companion_1_6_2(
    client: TestClient, sign: Sign, volume: Path
) -> None:
    data = _topology_on(volume)
    del data

    response = client.get("/status", params={"leaveOut": "12,13"}, headers=sign("admin"))

    assert response.status_code == 200, response.text
    assert "indexedLeftOut" in response.json()


def test_the_by_storage_lists_follow_the_storage_ids(client: TestClient, sign: Sign, volume: Path) -> None:
    data = _topology_on(volume)

    answer = _post(client, sign("admin"), _body(data)).json()

    assert answer["judgedByStorage"] == sorted(answer["judgedByStorage"])
    assert dict(map(tuple, answer["judgedByStorage"])) == _by_storage(data["expected"]["judgedByStorage"])
