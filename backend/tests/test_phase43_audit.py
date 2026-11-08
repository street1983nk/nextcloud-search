"""The audit probes of plan 43-09 over the 1.6.3 delta (v1.6.2..audited_head).

One probe per hypothesis of 43-09-PLAN.md that no test of plans 43-01 to 43-20
already drives; 43-AUDIT.md names the existing test for every other one. Each
probe carries its own positive control where the scan could silently see
nothing, and none of them reuses the pattern of the implementation it judges
(owner rule "Gegenprobe nie mit dem Muster der Umsetzung").
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from findling.api import coverage
from findling.main import APP
from findling.nc.files import GoneResult, MountResult
from findling.nc.queue import KIND_DELETE, QueueStats
from findling.store.repo import (
    CATCHUP_MARK,
    CATCHUP_RECONCILE,
    RECHECK_MARK,
    SWEEP_MARK,
    FileMeta,
    Store,
    coverage_counts,
    open_store,
)
from findling.worker.reconcile import REQUEUE_BAND
from test_coverage_endpoint import _body, _post, _topology_on
from test_reconcile_vanished import (
    CONTROL,
    CONTROL_FILES,
    CRAWLING,
    START,
    _control_kept,
    _Files,
    _Queue,
    _reconcile,
    _record_all,
    _stamp,
    _sweep_stamp,
)

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

DAY = 86_400

BACKEND_INFO = Path(__file__).resolve().parents[1] / "appinfo" / "info.xml"
PHP_ROOT = Path(__file__).resolve().parents[2] / "php"


@pytest.fixture(autouse=True)
def _fresh_coverage_cache() -> Iterator[None]:
    coverage._reset_coverage_cache_for_tests()
    yield
    coverage.join_coverage_refresh()
    coverage._reset_coverage_cache_for_tests()


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    opened.write_meta(RECHECK_MARK, "done")
    _record_all(opened, CONTROL, CONTROL_FILES)
    yield opened
    opened.close()


# -- security: the route surface and the body bounds (hypotheses S-a, S-b) ----


def test_every_declared_route_is_mounted_with_its_exact_case_and_verb() -> None:
    """The case trap of the 42-10 gap: declaration and route have to be one spelling.

    HaRP matches the declared pattern with re.match against the target path,
    case sensitively, so a declared route that differs from the mounted path in
    a single letter guards a path that does not exist while the real path
    stays unguarded. Every declared route of the manifest must therefore be a
    mounted path of the app, character for character, with its verb.
    """
    manifest = BACKEND_INFO.read_text(encoding="utf-8")
    routes = manifest[manifest.index("<routes>") : manifest.index("</routes>")]
    declared = re.findall(
        r"<url>\^(/[^$]+)\$</url>\s*<verb>([A-Z]+)</verb>\s*<access_level>([A-Z]+)</access_level>",
        routes,
    )
    paths: dict[str, Any] = APP.openapi()["paths"]

    assert len(declared) == 6
    assert ("/coverage", "POST", "ADMIN") in declared
    for url, verb, access in declared:
        assert access == "ADMIN", f"{url} is declared {access}, and the reviewed surface is ADMIN only"
        assert url in paths, f"{url} is declared but not mounted under this exact spelling"
        assert verb.lower() in paths[url], f"{url} is mounted without the declared verb {verb}"
    # Positive control for the case trap: the other spelling is not mounted, so
    # a declaration in that case would guard nothing at all.
    assert "/Coverage" not in paths
    assert "/coverage" in paths


def test_a_boolean_is_not_a_storage_id(client: TestClient, sign: Sign, volume: Path) -> None:
    """Strict mode holds: True reads as 1 only in lax mode, and lax would let bool through."""
    del volume
    answer = _post(client, sign("admin"), {"mounted": [True], "groups": []})
    assert answer.status_code == 422

    # Positive control on the same route and environment: the honest neighbour
    # of the refused body is answered, so the 422 is about the value.
    control = _post(client, sign("admin"), {"mounted": [1], "groups": []})
    assert control.status_code == 200


def test_a_nested_list_a_fraction_a_huge_number_and_an_extra_field_are_refused(
    client: TestClient, sign: Sign, volume: Path
) -> None:
    del volume
    bodies: list[dict[str, Any]] = [
        {"mounted": [1, 2], "groups": [[1, [2]]]},
        {"mounted": [1.5], "groups": []},
        {"mounted": [10**18], "groups": []},
        {"mounted": [int("9" * 400)], "groups": []},
        {"mounted": [1], "groups": [], "surprise": 1},
        {"mounted": [-5], "groups": []},
        {"mounted": [0], "groups": []},
    ]
    for body in bodies:
        answer = _post(client, sign("admin"), body)
        assert answer.status_code == 422, body


# -- bugs: the sweep around its gate, its pause and its clock (B-a, B-b, B-c, B-d, B-e) ----


class _FlippingQueue(_Queue):
    """Answers the first stats call with one state and every later one with another."""

    def __init__(self, first: QueueStats, then: QueueStats) -> None:
        super().__init__(state=first)
        self.then = then
        self.stat_calls = 0

    async def stats(self) -> QueueStats:
        self.stat_calls += 1
        answer = self.state
        self.state = self.then
        return answer


async def test_a_queue_that_turns_busy_in_the_round_stops_the_walk_before_its_next_slice(store: Store) -> None:
    """The gate is re-asked before every slice, so a mid-round flip to busy yields at once.

    The sweep has already run at that point, in front of the walk, so the flip
    costs the round nothing but the walk it must not take.
    """
    files = _Files(store, [CONTROL])
    queue = _FlippingQueue(QueueStats(scheduled=0), CRAWLING)
    round_of = _reconcile(store, files, queue, [START])

    await round_of.run_once()

    assert queue.stat_calls == 2
    assert files.page_calls == 0
    assert _sweep_stamp(store) is not None


async def test_a_queue_that_turns_calm_after_the_gate_read_still_waits_for_the_next_round(store: Store) -> None:
    """The gate is a snapshot: the walk of a round that began busy starts in the next round."""
    files = _Files(store, [CONTROL])
    queue = _FlippingQueue(CRAWLING, QueueStats(scheduled=0))
    round_of = _reconcile(store, files, queue, [START])

    await round_of.run_once()
    assert queue.stat_calls == 1
    assert files.page_calls == 0
    assert _sweep_stamp(store) is not None

    await round_of.run_once()
    assert files.page_calls >= 1


async def test_the_once_cycle_sweeps_only_under_the_catch_up_mark(store: Store) -> None:
    """The catch-up task of 1.5 compares nothing before part A, the sweep included."""
    files = _Files(store, [CONTROL])
    queue = _Queue(state=CRAWLING)
    round_of = _reconcile(store, files, queue, [START])
    round_of.arm()
    stop = asyncio.Event()

    task = asyncio.create_task(round_of.run(stop, once=True))
    await asyncio.sleep(0.05)
    stop.set()
    await task
    assert files.mount_calls == 0
    assert _sweep_stamp(store) is None

    store.write_meta(CATCHUP_MARK, CATCHUP_RECONCILE)
    second = _reconcile(store, _Files(store, [CONTROL]), queue, [START])
    second.arm()
    stop = asyncio.Event()
    task = asyncio.create_task(second.run(stop, once=True))
    await asyncio.sleep(0.05)
    stop.set()
    await task
    assert _sweep_stamp(store) is not None


class _PausingFiles(_Files):
    """Runs a hook right after the mount list was handed out."""

    def __init__(self, store: Store, listed: list[int], answer: GoneResult) -> None:
        super().__init__(store, listed, answer)
        self.after_mounts: Callable[[], None] | None = None

    async def mounts(self) -> MountResult:
        answer = await super().mounts()
        if self.after_mounts is not None:
            self.after_mounts()
        return answer


async def test_a_pause_between_the_mount_list_and_the_first_storage_ends_the_round_clean(store: Store) -> None:
    """A backup pause in the one gap the 41 audit hunted: after the list, before the sweep.

    No delete order, no stamp, no back-off and not even the storage question;
    the next round after the release sweeps the same storage.
    """
    _record_all(store, 9, (30, 31))
    files = _PausingFiles(store, [CONTROL], GoneResult(gone=frozenset({9})))
    queue = _Queue(state=CRAWLING)
    round_of = _reconcile(store, files, queue, [START])
    files.after_mounts = round_of.hold_for_backup

    await round_of.run_once()

    assert queue.requeues == []
    assert files.events == ["mounts"]
    assert _sweep_stamp(store) is None
    assert round_of._cooldown == 0

    files.after_mounts = None
    round_of.release_backup_hold()
    await round_of.run_once()

    assert sorted(queue.deleted()) == [30, 31]
    assert _sweep_stamp(store) is not None
    _control_kept(queue)


async def test_a_sweep_with_nothing_absent_stamps_and_rests_for_its_cadence(store: Store) -> None:
    """An instance where nothing vanished must not read the mount list every tick."""
    clock = [START]
    files = _Files(store, [CONTROL])
    queue = _Queue(state=CRAWLING)
    round_of = _reconcile(store, files, queue, clock)

    await round_of.run_once()
    assert _sweep_stamp(store) == str(int(START))
    assert files.mount_calls == 1

    clock[0] += 300.0
    await round_of.run_once()
    assert files.mount_calls == 1


async def test_a_sweep_stamp_in_the_future_waits_and_a_past_stamp_is_due(store: Store) -> None:
    """A clock that jumped back silences the sweep until the wall clock passes the stamp.

    The behaviour of finding F-43A-02 (LOW, accepted): the same cadence rule
    the walk has always had, no data is lost, and the sweep catches up as soon
    as real time passes the stored moment. The positive control is the same
    round against a stamp of the past.
    """
    store.write_meta(SWEEP_MARK, str(int(START + 10 * DAY)))
    files = _Files(store, [CONTROL])
    queue = _Queue(state=CRAWLING)
    round_of = _reconcile(store, files, queue, [START])

    await round_of.run_once()
    assert files.mount_calls == 0

    store.write_meta(SWEEP_MARK, str(int(START - 2 * DAY)))
    await round_of.run_once()
    assert files.mount_calls == 1


# -- D-43-11: one document, one place in the denominator (hypothesis C-a) ----


def test_a_document_first_indexed_and_later_unreadable_counts_once_on_the_container_side(tmp_path: Path) -> None:
    """The container figures never hold a document the PHP side owns after a 422.

    A row that moves from indexed to skipped(unreadable) leaves documents and
    judged; a group where one member stays indexed keeps the document exactly
    once in both. The PHP half (phpOnly with N1) is held by PHPUnit
    (FileStateServiceCoverageTest), so together the denominator carries the
    document once and never twice.
    """
    state = tmp_path / "state.db"
    vectors = tmp_path / "vectors.db"
    opened = open_store(state)
    try:
        key = hashlib.sha256(b"files/akte.pdf").hexdigest()
        reader_a = FileMeta(
            storage_id=7,
            root_id=70,
            path="files/akte.pdf",
            title="akte.pdf",
            mime="application/pdf",
            size=10,
            mtime=1,
            etag="e1",
            doc_key=key,
        )
        opened.record(50, reader_a, "indexed")

        single_before = coverage_counts(state, vectors, [7], [])
        assert single_before.documents_by_storage == {7: 1}
        assert single_before.judged_by_storage == {7: 1}

        opened.record(50, reader_a, "skipped", "unreadable")
        single_after = coverage_counts(state, vectors, [7], [])
        assert single_after.documents_by_storage == {}
        assert single_after.judged_by_storage == {}
        assert single_after.doc_keys_missing == 0

        # The group case: the same document under another reader path on a
        # second member, one row indexed and one unreadable.
        opened.record(50, reader_a, "indexed")
        reader_b = FileMeta(
            storage_id=8,
            root_id=80,
            path="files/anders/akte.pdf",
            title="akte.pdf",
            mime="application/pdf",
            size=10,
            mtime=1,
            etag="e2",
            doc_key=key,
        )
        opened.record(51, reader_b, "skipped", "unreadable")
        grouped = coverage_counts(state, vectors, [7, 8], [[7, 8]])
        assert grouped.documents_by_group == (1,)
        assert grouped.judged_by_group == (1,)
    finally:
        opened.close()


# -- performance: the backlog of issue #25 in one round (hypothesis P-c) ----


async def test_the_delete_backlog_of_the_issue_goes_through_in_one_round_of_bands(
    store: Store, capsys: pytest.CaptureFixture[str]
) -> None:
    """31,571 rows on 13 storages whose grace ran out go in one round, band by band."""
    sizes = [2429] * 12 + [2423]
    storages = list(range(101, 114))
    rows: list[tuple[int, int, int, str, str, str, int, int, str]] = []
    fid = 10_000
    for sid, n in zip(storages, sizes, strict=True):
        for _ in range(n):
            rows.append((fid, sid, sid * 10, f"p/{fid}", f"t{fid}", "text/plain", 1, 1, f"e{fid}"))
            fid += 1
    with store._conn:
        store._conn.executemany(
            "INSERT INTO files (file_id, storage_id, root_id, path, title, mime, size, mtime, etag,"
            " state, reason, attempts, ocr_used, indexed_at, index_version)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'indexed', NULL, 1, 0, 1, 1)",
            rows,
        )
    old = int(START) - 31 * DAY
    for sid in storages:
        store.mark_vanished(sid, old)
    files = _Files(store, [CONTROL], GoneResult())
    queue = _Queue(state=CRAWLING)
    round_of = _reconcile(store, files, queue, [START])

    started = time.perf_counter()
    await round_of.run_once()
    took = time.perf_counter() - started

    assert len(queue.deleted()) == 31_571
    bands = [band for band, kind in queue.requeues if kind == KIND_DELETE]
    assert len(bands) == 13 * 13
    assert max(len(band) for band in bands) == REQUEUE_BAND
    assert _sweep_stamp(store) == str(int(START))
    # The rows stay living until the delete branch of the poller turns them
    # into tombstones; the sweep's own book keeping is gone for every storage.
    assert all(_stamp(store, sid) is None for sid in storages)
    _control_kept(queue)
    with capsys.disabled():
        print(f"\n31,571 delete orders in one round: {len(bands)} bands of <= {REQUEUE_BAND}, {took:.2f} s")


# -- bugs: the background count never wedges (hypothesis B-h) ----


def test_an_unexpected_error_in_the_background_count_does_not_wedge_the_single_flight(
    client: TestClient, sign: Sign, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure of a type no except clause names still frees the single flight.

    The finally of the refresh thread gives the slot back for every way out,
    so the next request starts a fresh count instead of saying counting for
    good while no thread runs any more.
    """
    data = _topology_on(volume)
    monkeypatch.setattr(coverage, "COVERAGE_SYNC_CEILING", 0)
    real = coverage.coverage_counts
    calls: list[int] = []

    def flaky(*args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        if len(calls) == 1:
            message = "a failure no except clause names"
            raise ValueError(message)
        return real(*args, **kwargs)

    monkeypatch.setattr(coverage, "coverage_counts", flaky)
    monkeypatch.setattr(threading, "excepthook", lambda _args: None)

    first = _post(client, sign("admin"), _body(data)).json()
    coverage.join_coverage_refresh()
    second = _post(client, sign("admin"), _body(data)).json()
    coverage.join_coverage_refresh()
    third = _post(client, sign("admin"), _body(data)).json()

    assert first["counting"] is True
    assert second["counting"] is True
    assert third["counting"] is False
    assert third["documents"] == data["expected"]["documents"]
    assert len(calls) == 2


# -- the PHP half, read where it stands (hypotheses D-e, C-b, F-43A-01) ----


def _attributes_before(source: str, method: str) -> str:
    """The attribute lines between the end of the docblock and the method."""
    head = source[: source.index(f"public function {method}(")]
    return head.rsplit("*/", 1)[1]


def test_the_doc_key_route_stands_behind_the_exapp_attributes_before_any_lookup() -> None:
    """Only the signed backend reads document keys, and the id check comes first."""
    source = (PHP_ROOT / "lib" / "Controller" / "ReconcileController.php").read_text(encoding="utf-8")
    attributes = _attributes_before(source, "docKeys")
    lines = [line.strip() for line in attributes.strip().splitlines()]

    # The window really is the attribute block: three lines, each an attribute,
    # so a dropped or added attribute changes this count (positive control).
    assert len(lines) == 3
    assert all(line.startswith("#[") for line in lines)
    assert any("ExAppRequired" in line for line in lines)
    assert any("NoCSRFRequired" in line for line in lines)
    assert any("ApiRoute(verb: 'GET', url: '/reconcile/doc-keys')" in line for line in lines)

    body = source[source.index("public function docKeys(") :]
    body = body[: body.index("public function", 1)]
    assert body.index("rejectForeignCaller") < body.index("fileIdList")
    assert body.index("fileIdList") < body.index("docKeyService->docKeysFor")


def _php_int(source: str, name: str) -> int:
    found = re.search(rf"{name} = (\d+);", source)
    assert found is not None, f"{name} is not in the PHP source"
    return int(found.group(1))


def test_the_coverage_bounds_of_both_halves_are_the_same_numbers() -> None:
    """The companion must never build a body the container refuses as too large."""
    php = (PHP_ROOT / "lib" / "Service" / "AdminViewService.php").read_text(encoding="utf-8")

    assert _php_int(php, "COVERAGE_MAX_MOUNTED") == coverage.COVERAGE_MAX_MOUNTED
    assert _php_int(php, "COVERAGE_MAX_MEMBERS") == coverage.COVERAGE_MAX_MEMBERS
    assert 2 <= _php_int(php, "COVERAGE_MAX_SINGLES") <= coverage.COVERAGE_MAX_MOUNTED


def test_the_sync_ceiling_keeps_a_slow_box_under_the_admin_timeout_of_the_companion() -> None:
    """Finding F-43A-01 of 43-AUDIT.md, held down for good.

    POST /coverage counts in the request up to COVERAGE_SYNC_CEILING living
    rows, and the companion hangs up after ADMIN_REQUEST_TIMEOUT_SECONDS on
    every admin call. Probe P-b of 43-09 measured 102,311 rows in 0.738 s,
    best of three on the x86 development machine, 7.3 us per row; factor 5
    for ARM is the precedent of 41-AUDIT.md (probe V). Half the timeout stays
    for the HTTP hop, the AppAPI signature check and the three small reads
    beside the count. At the old ceiling of 100,000 an ARM box with about
    56,000 rows or more answered after the companion had hung up, and the page
    fell back to the figure of 1.6.2 for good, without a word: the very figure
    1.6.3 replaces.
    """
    php = (PHP_ROOT / "lib" / "Service" / "ExAppService.php").read_text(encoding="utf-8")
    found = re.search(r"ADMIN_REQUEST_TIMEOUT_SECONDS = ([0-9.]+);", php)
    assert found is not None
    timeout = float(found.group(1))
    measured_seconds_per_row_on_arm = 7.3e-6 * 5

    assert coverage.COVERAGE_SYNC_CEILING * measured_seconds_per_row_on_arm <= timeout / 2
