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

Plan 43-24 (OE-5 a) adds the format of the document key to both directions and
a gate in front of the count: a body without docKeyFormat 2 is a 422 before any
database, and while the meta value doc_key_backfill_after does not carry
generation 2 the answer says counting for every living row of the request,
whether the backfill ran, waits for its arming or is held by a backup pause. A
key of the format of 1.6.3-rc.1 never reaches a figure.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from findling.api import coverage
from findling.config import settings
from findling.main import APP
from findling.nc.files import DocKeyAnswer
from findling.store import repo
from findling.worker import doc_keys
from test_coverage_counts import _build, _by_storage, _key, _topology

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
        "docKeyFormat",
    }
)


@pytest.fixture(autouse=True)
def _fresh_cache() -> Any:
    coverage._reset_coverage_cache_for_tests()
    yield
    coverage.join_coverage_refresh()
    coverage._reset_coverage_cache_for_tests()


def _send(client: TestClient, headers: dict[str, str], body: object) -> Any:
    """The body exactly as given, for the tests about the body itself."""
    return client.post("/coverage", content=json.dumps(body), headers={**headers, "Content-Type": "application/json"})


def _post(client: TestClient, headers: dict[str, str], body: object) -> Any:
    """The body as a 1.6.3 companion sends it: an object gets docKeyFormat 2 unless it names one.

    So every test about a bound of the body fails on that bound alone, and not
    on a missing format (plan 43-24).
    """
    if isinstance(body, dict) and "docKeyFormat" not in body:
        body = {**body, "docKeyFormat": 2}
    return _send(client, headers, body)


def _format_two(body: Mapping[str, Any]) -> dict[str, Any]:
    """The body of a 1.6.3 companion: the same lists plus the format of its keys."""
    return {**body, "docKeyFormat": 2}


def _set_mark(volume: Path, value: str | None) -> None:
    """Write the meta value of the document key backfill, or take it away."""
    store = repo.open_store(volume / "state.db")
    try:
        if value is None:
            store._conn.execute("DELETE FROM meta WHERE key = ?", (doc_keys.DOC_KEY_MARK,))
        else:
            store.write_meta(doc_keys.DOC_KEY_MARK, value)
    finally:
        store.close()


def _topology_on(volume: Path) -> dict[str, Any]:
    """The topology with keys of format 2: the backfill of generation 2 has run."""
    data = _topology()
    _build(volume, data["rows"])
    _set_mark(volume, "2:0:0")
    return data


def _keys_of_format_one(volume: Path) -> None:
    """Give every row the key of 1.6.3-rc.1, sha256 over a path alone.

    The reshare (1102, 1202) and the two mount points (1104, 1204) get two
    keys each this way, so a count over these keys gives 15 documents and not
    the 13 of the truth: a figure from them would show.
    """
    store = repo.open_store(volume / "state.db")
    try:
        rows = store._conn.execute("SELECT file_id, path FROM files").fetchall()
        store._conn.executemany(
            "UPDATE files SET doc_key = ? WHERE file_id = ?",
            [(hashlib.sha256(str(path).encode()).hexdigest(), int(file_id)) for file_id, path in rows],
        )
    finally:
        store.close()


def _living(data: Mapping[str, Any], mounted: Sequence[int] | None = None) -> int:
    """Living rows of the listed storages, counted from the fixture and not by the store."""
    listed = set(data["mounted"] if mounted is None else mounted)
    return sum(1 for row in data["rows"] if not row["deleted"] and row["storage_id"] in listed)


FIGURES = (
    "documents",
    "embeddedDocuments",
    "judgedDocuments",
    "documentsByGroup",
    "judgedByGroup",
    "documentsByStorage",
    "judgedByStorage",
)


def _assert_counting_without_a_figure(answer: Mapping[str, Any]) -> None:
    assert answer["counting"] is True
    for key in FIGURES:
        assert answer[key] is None, key


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
    # docKeysMissing counts the whole state: 3106 of the single storage 31 and
    # row 1 of storage 0 have no key, and neither holds the figure back.
    assert answer["docKeysMissing"] == 2
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
    # Another request above the ceiling as well: another key, still no start.
    _post(client, sign("admin"), {"mounted": data["mounted"], "groups": []})
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


# -- a count without a vector stock (F-43B-03) -----------------------------


_NO_VECTOR_STOCK = "coverage count without a vector stock, the vector figure is 0"


def _warnings_without_a_vector_stock(caplog: pytest.LogCaptureFixture) -> int:
    return sum(
        1
        for record in caplog.records
        if record.name == "findling.store.repo"
        and record.levelno >= logging.WARNING
        and record.getMessage() == _NO_VECTOR_STOCK
    )


@pytest.mark.parametrize("ceiling", [coverage.COVERAGE_SYNC_CEILING, 5], ids=["in the request", "in the background"])
def test_no_warning_per_count_while_embeddings_are_switched_off(
    client: TestClient,
    sign: Sign,
    volume: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    ceiling: int,
) -> None:
    """Audit finding F-43B-03: no vectors.db is the normal state of FINDLING_EMBED_ENABLED=false.

    Such an instance never builds a vector stock, and the admin page asks for
    the figures with every look. The count must not write a warning for a
    state the admin chose; the vector figure is 0 and the rest is right.
    """
    data = _topology_on(volume)
    (volume / "vectors.db").unlink()
    monkeypatch.setenv("FINDLING_EMBED_ENABLED", "false")
    monkeypatch.setattr(coverage, "COVERAGE_SYNC_CEILING", ceiling)
    settings.cache_clear()
    caplog.set_level(logging.DEBUG, logger="findling.store.repo")

    answers = []
    for _ in range(3):
        _post(client, sign("admin"), _body(data))
        coverage.join_coverage_refresh()
        answers.append(_post(client, sign("admin"), _body(data)).json())

    assert [answer["counting"] for answer in answers] == [False, False, False]
    assert [answer["embeddedDocuments"] for answer in answers] == [0, 0, 0]
    assert [answer["documents"] for answer in answers] == [data["expected"]["documents"]] * 3
    assert _warnings_without_a_vector_stock(caplog) == 0


def test_a_missing_vector_stock_is_still_a_warning_per_count_while_embeddings_are_on(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The other half of F-43B-03: with embeddings on, a stock that is not there stays visible."""
    data = _topology_on(volume)
    (volume / "vectors.db").unlink()
    monkeypatch.setenv("FINDLING_EMBED_ENABLED", "true")
    settings.cache_clear()
    caplog.set_level(logging.DEBUG, logger="findling.store.repo")

    answers = [_post(client, sign("admin"), _body(data)).json() for _ in range(3)]

    assert [answer["embeddedDocuments"] for answer in answers] == [0, 0, 0]
    assert _warnings_without_a_vector_stock(caplog) == 3


# -- the document key backfill -------------------------------------------


def test_a_group_member_without_a_key_keeps_the_answer_counting(client: TestClient, sign: Sign, volume: Path) -> None:
    data = _topology()
    variant = next(item for item in data["variants"] if item["name"] == "backfill_open")
    _build(volume, [*data["rows"], *variant["extraRows"]])
    _set_mark(volume, "2:0:0")

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


# -- the format of the keys and the generation gate (plan 43-24) ---------


def _no_count(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """Record every count and every look into the cache; the gate allows neither."""
    calls: list[object] = []
    monkeypatch.setattr(coverage, "coverage_counts", lambda *args, **kwargs: calls.append(("count", args)))
    monkeypatch.setattr(coverage, "_cached", lambda *args, **kwargs: calls.append(("cache", args)))
    return calls


def test_coverage_counts_nothing_while_the_mark_is_generation_one(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After 1.6.3-rc.1 every row has a key, of format 1, and no round has run yet (B1)."""
    data = _topology_on(volume)
    _keys_of_format_one(volume)
    _set_mark(volume, "1:400:0")
    calls = _no_count(monkeypatch)

    response = _send(client, sign("admin"), _format_two(_body(data)))

    assert response.status_code == 200, response.text
    answer = response.json()
    _assert_counting_without_a_figure(answer)
    # Not the rows without a key, there are none: the living rows of the request.
    assert _living(data) == 29
    assert answer["docKeysMissing"] == _living(data)
    assert answer["docKeyFormat"] == 2
    assert calls == []

    # Above the ceiling the same: no thread, no cache.
    monkeypatch.setattr(coverage, "COVERAGE_SYNC_CEILING", 0)
    again = _send(client, sign("admin"), _format_two(_body(data))).json()
    _assert_counting_without_a_figure(again)
    assert again["docKeysMissing"] == _living(data)
    assert calls == []

    # Another mount list, another number of waiting rows.
    part = _send(client, sign("admin"), _format_two({"mounted": [21, 22], "groups": [[21, 22]]})).json()
    _assert_counting_without_a_figure(part)
    assert part["docKeysMissing"] == _living(data, [21, 22]) == 6


def test_a_cached_figure_is_not_answered_under_another_generation(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate stands in front of the cache: a figure counted earlier is no way around it."""
    data = _topology_on(volume)
    monkeypatch.setattr(coverage, "COVERAGE_SYNC_CEILING", 5)
    body = _format_two(_body(data))
    _send(client, sign("admin"), body)
    coverage.join_coverage_refresh()
    cached = _send(client, sign("admin"), body)
    assert cached.status_code == 200, cached.text
    assert cached.json()["counting"] is False
    assert coverage.cached_keys() == 1

    _set_mark(volume, "1:0:0")
    gated = _send(client, sign("admin"), body).json()
    coverage.join_coverage_refresh()

    _assert_counting_without_a_figure(gated)
    assert gated["docKeysMissing"] == _living(data)

    _set_mark(volume, "2:0:0")
    assert _send(client, sign("admin"), body).json()["documents"] == data["expected"]["documents"]


@pytest.mark.parametrize("stored", [None, "", "500", "x:1:1", "0:12", "3:0:0"])
def test_coverage_counts_nothing_without_a_mark_on_rows(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch, stored: str | None
) -> None:
    """A state of 1.6.2 has rows and no meta value; an unreadable or foreign one counts the same."""
    data = _topology_on(volume)
    _set_mark(volume, stored)

    # No living row of the request: nothing waits, and nothing is a figure.
    for mounted in ([33], [999], [33, 999]):
        empty = _send(client, sign("admin"), _format_two({"mounted": mounted, "groups": []}))
        assert empty.status_code == 200, empty.text
        assert empty.json()["counting"] is False, mounted
        assert empty.json()["documents"] == 0
        assert empty.json()["documentsByStorage"] == []

    calls = _no_count(monkeypatch)

    response = _send(client, sign("admin"), _format_two(_body(data)))

    assert response.status_code == 200, response.text
    answer = response.json()
    _assert_counting_without_a_figure(answer)
    assert answer["docKeysMissing"] == _living(data)
    assert calls == []


def test_a_state_without_rows_and_without_a_mark_answers_zeros(client: TestClient, sign: Sign, volume: Path) -> None:
    repo.open_store(volume / "state.db").close()

    response = _send(client, sign("admin"), _format_two({"mounted": [1, 2], "groups": [[1, 2]]}))

    assert response.status_code == 200, response.text
    answer = response.json()
    assert answer["counting"] is False
    assert answer["documents"] == 0
    assert answer["documentsByGroup"] == [0]
    assert answer["docKeysMissing"] == 0
    assert answer["docKeyFormat"] == 2


class _Companion:
    """The companion of 1.6.3 for the topology: the format 2 key of every row it knows."""

    def __init__(self, rows: Sequence[Mapping[str, Any]]) -> None:
        self.keys = {int(row["file_id"]): _key(str(row["doc_key"])) for row in rows if row["doc_key"]}
        self.unavailable = False
        self.asked = 0

    async def doc_keys(self, file_ids: Sequence[int]) -> DocKeyAnswer | None:
        self.asked += 1
        if self.unavailable:
            return None
        ids = tuple(file_ids)
        return DocKeyAnswer(
            asked=ids,
            keys={file_id: self.keys[file_id] for file_id in ids if file_id in self.keys},
            absent=frozenset(file_id for file_id in ids if file_id not in self.keys),
        )


def test_coverage_counts_nothing_during_a_backup_pause_before_the_reset(
    client: TestClient, sign: Sign, volume: Path
) -> None:
    """The reset waits behind the pause, the gate does not (B1 of plan 43-21)."""
    data = _topology_on(volume)
    _keys_of_format_one(volume)
    _set_mark(volume, "1:400:0")
    body = _format_two(_body(data))
    companion = _Companion(data["rows"])
    store = repo.open_store(volume / "state.db")
    backfill = doc_keys.DocKeyBackfill(
        store=store,
        client_factory=lambda: cast("Any", None),
        files_factory=lambda nc: cast("Any", companion),
        pause_seconds=0.0,
        clock=lambda: 1_800_000_000.0,
    )
    try:
        backfill.hold_for_backup()
        assert asyncio.run(backfill.run_once()).state == doc_keys.ROUND_HELD
        assert store.read_meta()[doc_keys.DOC_KEY_MARK] == "1:400:0"
        assert store.doc_keys_missing() == 0

        held = _send(client, sign("admin"), body)
        assert held.status_code == 200, held.text
        _assert_counting_without_a_figure(held.json())
        assert held.json()["docKeysMissing"] == _living(data)

        # Released, the companion out of reach: the reset runs, nothing comes back yet.
        backfill.release_backup_hold()
        companion.unavailable = True
        asyncio.run(backfill.run_once())
        assert store.read_meta()[doc_keys.DOC_KEY_MARK] == "2:0:0"
        everything = sum(1 for row in data["rows"] if not row["deleted"])
        assert store.doc_keys_missing() == everything == 32

        after_reset = _send(client, sign("admin"), body).json()
        _assert_counting_without_a_figure(after_reset)
        assert after_reset["docKeysMissing"] == everything

        # The companion answers: one round fills every row, and the figure is the truth.
        companion.unavailable = False
        assert asyncio.run(backfill.run_once()).state == doc_keys.ROUND_FILLED
        assert store.doc_keys_missing() == 0
    finally:
        store.close()

    done = _send(client, sign("admin"), body).json()
    assert done["counting"] is False
    assert done["docKeysMissing"] == 0
    assert done["documents"] == data["expected"]["documents"]
    assert done["judgedDocuments"] == data["expected"]["judgedDocuments"]
    assert done["documentsByGroup"] == data["expected"]["documentsByGroup"]
    assert done["judgedByGroup"] == data["expected"]["judgedByGroup"]
    assert done["documentsByStorage"] == _pairs(data["expected"]["documentsByStorage"])


_ABSENT = object()


@pytest.mark.parametrize(
    "value",
    [_ABSENT, 1, 3, 0, "2", 2.0, True, None, [2]],
    ids=["missing", "1", "3", "0", "string", "float", "boolean", "null", "list"],
)
def test_coverage_without_doc_key_format_is_422_before_any_database(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch, value: object
) -> None:
    """A companion of rc.1 sends no format: refused before anything is opened (A-2).

    The volume has no state.db, and a valid body is answered with zeros on it,
    so a 422 here cannot come from a database.
    """
    body: dict[str, Any] = {"mounted": [1, 2], "groups": [[1, 2]]}
    if value is not _ABSENT:
        body["docKeyFormat"] = value
    opened: list[object] = []
    real_open = coverage.open_read_only
    monkeypatch.setattr(coverage, "open_read_only", lambda *args, **kwargs: opened.append(args) or real_open(*args))

    refused = _send(client, sign("admin"), body)

    assert refused.status_code == 422, refused.text
    assert opened == []
    assert not (volume / "state.db").exists()

    answered = _send(client, sign("admin"), {"mounted": [1, 2], "groups": [[1, 2]], "docKeyFormat": 2})

    assert answered.status_code == 200, answered.text
    assert answered.json()["docKeyFormat"] == 2
    assert type(answered.json()["docKeyFormat"]) is int
    assert answered.json()["documents"] == 0


def test_a_422_does_not_end_the_cooldown(client: TestClient, sign: Sign, volume: Path) -> None:
    """Only a companion that speaks format 2 knows the route the backfill waits for (T-43-73)."""
    data = _topology_on(volume)
    doc_keys._COVERAGE_SEEN.clear()
    try:
        refused = _send(client, sign("admin"), _body(data))
        assert refused.status_code == 422, refused.text
        assert not doc_keys._COVERAGE_SEEN.is_set()

        other = _send(client, sign("admin"), {**_body(data), "docKeyFormat": 1})
        assert other.status_code == 422, other.text
        assert not doc_keys._COVERAGE_SEEN.is_set()

        answered = _send(client, sign("admin"), _format_two(_body(data)))
        assert answered.status_code == 200, answered.text
        assert doc_keys._COVERAGE_SEEN.is_set()
    finally:
        doc_keys._COVERAGE_SEEN.clear()


def test_every_answer_names_the_format_of_the_keys(client: TestClient, sign: Sign, volume: Path) -> None:
    """The companion reads the per document figure only with docKeyFormat 2 in the answer."""
    data = _topology_on(volume)

    figure = _send(client, sign("admin"), _format_two(_body(data)))
    assert figure.status_code == 200, figure.text
    assert figure.json()["counting"] is False
    assert figure.json()["docKeyFormat"] == 2

    _set_mark(volume, "1:0:0")
    waiting = _send(client, sign("admin"), _format_two(_body(data))).json()
    assert waiting["counting"] is True
    assert waiting["docKeyFormat"] == 2
    assert set(waiting) == ANSWER_KEYS | {"docKeyFormat"}


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
    body = JSONResponse(content=answer.model_dump(mode="json")).body
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
