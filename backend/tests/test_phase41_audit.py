"""Probes of the audit 1.6.2 (plan 41-09) over the changes v1.6.1..738a1373.

The report with the commands, the results and the decision on every finding is
``.planning/phases/41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes/41-AUDIT.md``.
This module keeps the probes that a checkout can run on its own, one block per
probe letter of that report (P to V), and a probe that showed a finding names
it by its id. A probe of a LOW finding that stays open pins what happens today
and says so in its docstring; the fix turns it red on purpose.

The probes deliberately take another road than the tests of the building plans
(test_backup_pause.py, test_status_leave_out.py, test_poller.py): the pause is
judged by what lies on disk, every file of the volume with its size, its
modification time and its sha256, and not by the flags of the coordinator; the
retry cap is read off the rows of a real state database instead of the
reconcile; the outage grid is driven through the real streaming fetch over the
whole range of 400 to 599; the access rules of the PHP routes are read off the
attribute lines in front of each method.

Only ASCII in this file, like the other audit modules.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import io
import re
import sqlite3
import threading
import time
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from fastapi.testclient import TestClient
from tantivy import Index

import test_poller
from conftest import Corpus, wish_reader
from findling import guard
from findling import main as findling_main
from findling.api import status
from findling.config import settings
from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter
from findling.nc import client as nc_client
from findling.nc.client import GatewayRefused, NextcloudException
from findling.nc.files import FileRow, Mount, MountResult, SliceResult
from findling.nc.queue import CallResult, ClaimResult, QueueStats
from findling.store.repo import CATCHUP_MARK, CATCHUP_RECONCILE, FileMeta, Store, open_store
from findling.worker import poller as poller_module
from findling.worker.pause import (
    PAUSE_PAUSED,
    PAUSE_PAUSING,
    PAUSE_POLL_SECONDS,
    PAUSE_RETREAT_MAX_SECONDS,
    PAUSE_RUNNING,
    PAUSE_UNKNOWN,
    PAUSE_UNREADABLE_WARN_AFTER,
    PauseCoordinator,
)
from findling.worker.poller import RETREAT_AFTER_ROUNDS, RETREAT_MAX_SECONDS, Poller
from findling.worker.reconcile import GATEWAY_ERROR_RETRIES, Reconcile
from findling.worker.watch import GuardWatch

REPO = Path(__file__).resolve().parents[2]
PHP_LIB = REPO / "php" / "lib"

Sign = Callable[[str], dict[str, str]]
Snapshot = dict[str, tuple[int, int, str]]
META_PASS = guard.META_MULTI_SLOT_PASS
META_CHOSEN = guard.META_MULTI_SLOT_CHOSEN


def _snapshot(root: Path) -> Snapshot:
    """Every file below ``root``: size, modification time in ns, sha256 of the content."""
    seen: Snapshot = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            found = path.stat()
            digest = hashlib.sha256(data).hexdigest()
            seen[path.relative_to(root).as_posix()] = (found.st_size, found.st_mtime_ns, digest)
    return seen


def _changed(before: Snapshot, after: Snapshot) -> dict[str, str]:
    """What moved between two snapshots, by relative path."""
    moved: dict[str, str] = {}
    for name in sorted(set(before) | set(after)):
        if name not in before:
            moved[name] = "created"
        elif name not in after:
            moved[name] = "removed"
        elif before[name] != after[name]:
            moved[name] = "changed"
    return moved


def _data_moved(before: Snapshot, after: Snapshot) -> dict[str, str]:
    """What moved, without the shared memory files and logs of zero bytes readers make.

    A reader of a WAL database creates ``-shm`` (an index in memory, never data)
    and an empty ``-wal``; neither holds a byte of the stock, and a copy of
    either is rebuilt by SQLite. Everything else counts, a ``-wal`` with bytes
    in it above all.
    """
    moved = _changed(before, after)
    return {
        name: how
        for name, how in moved.items()
        if not name.endswith("-shm") and not (name.endswith("-wal") and after.get(name, (0, 0, ""))[0] == 0)
    }


def _meta_rows(path: Path) -> dict[str, str]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return {str(key): str(value) for key, value in connection.execute("SELECT key, value FROM meta")}
    finally:
        connection.close()


def _meta(storage_id: int, file_id: int) -> FileMeta:
    return FileMeta(
        storage_id=storage_id,
        root_id=storage_id,
        path=f"/Probe/probe-{file_id}.txt",
        title=f"probe-{file_id}.txt",
        mime="text/plain",
        size=10,
        mtime=1_700_000_000 + file_id,
        etag=f"etag-{file_id}",
    )


# == P the writers stand still on disk =================================================


@pytest.mark.usefixtures("appapi_environment")
def test_p_a_paused_volume_stands_still_through_three_ticks_a_search_and_a_status(
    indexed_volume: Corpus, sign: Sign, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hypothesis: once "paused" is reported, nothing of the volume moves while the container runs.

    The real lifespan, every writer built and attached, the wish "paused". After
    "paused" three more ticks of the coordinator, a search and a status report
    run, and then every file of the volume is compared byte by byte.
    """
    monkeypatch.setattr(findling_main, "pause_wish_reader", wish_reader(True))
    settings().armed_marker.write_text("", encoding="utf-8")
    root = indexed_volume.root

    with TestClient(findling_main.APP) as running:
        pause = findling_main._PAUSE
        assert pause is not None
        assert pause.state == PAUSE_PAUSED
        before = _snapshot(root)
        portal = running.portal
        assert portal is not None
        for _ in range(3):
            portal.call(pause.tick)
        found = running.post("/search", json={"query": "x"}, headers=sign(indexed_volume.bob))
        assert found.status_code == 200, found.text
        report = status.report()
        assert report.pause == PAUSE_PAUSED
        after = _snapshot(root)

    assert _data_moved(before, after) == {}
    assert all(after[name][0] == 0 for name in after if name.endswith("-wal")), "every log is empty"


def test_p_the_snapshot_sees_a_single_meta_write(tmp_path: Path) -> None:
    """Positive control of the snapshot above: one meta row written is one file that moved."""
    store = open_store(tmp_path / "state.db")
    try:
        before = _snapshot(tmp_path)
        store.write_meta("probe", "1")
        after = _snapshot(tmp_path)
    finally:
        store.close()
    assert _data_moved(before, after) != {}


@pytest.mark.usefixtures("appapi_environment")
def test_p_f_41a_01_a_stop_in_the_pause_writes_nothing(indexed_volume: Corpus, monkeypatch: pytest.MonkeyPatch) -> None:
    """F-41A-01 (LOW, fixed): the shutdown of a paused container leaves the volume as it was.

    Before the fix GuardWatch.note_shutdown_begins() cleared the two pass marks
    of the memory guard with a write of its own, past suspend_persist(): 16 512
    bytes of log, multi_slot_pass and multi_slot_chosen set to "". Now a
    suspended watch reads the marks first and writes only a mark that is set;
    in "paused" no pass runs, so both are empty and nothing is written.
    """
    monkeypatch.setattr(findling_main, "pause_wish_reader", wish_reader(True))
    settings().armed_marker.write_text("", encoding="utf-8")
    root = indexed_volume.root

    with TestClient(findling_main.APP):
        pause = findling_main._PAUSE
        assert pause is not None
        assert pause.state == PAUSE_PAUSED
        before = _snapshot(root)
    after = _snapshot(root)

    assert _data_moved(before, after) == {}, "the stop of a paused container wrote the volume"


def _guard_volume(tmp_path: Path, marks: dict[str, str]) -> Path:
    path = tmp_path / "state.db"
    store = open_store(path)
    for key, value in marks.items():
        store.write_meta(key, value)
    store.close()
    return path


@pytest.mark.parametrize(
    ("suspended", "marks", "writes"),
    [
        (False, {}, True),
        (True, {}, False),
        (True, {META_PASS: "standard", META_CHOSEN: "standard"}, True),
        (True, {META_PASS: "", META_CHOSEN: "standard"}, True),
    ],
    ids=["running_writes_positive_control", "paused_writes_nothing", "pausing_clears_a_mark", "lone_choice"],
)
async def test_p_f_41a_01_the_shutdown_mark_writes_only_outside_the_pause_or_for_a_set_mark(
    tmp_path: Path, suspended: bool, marks: dict[str, str], writes: bool
) -> None:
    """F-41A-01, the same path with and without the pause, judged by sha256 on disk.

    Positive control: without the pause the shutdown clears the marks with a
    write, and the snapshot sees state.db move. With the pause and no mark set
    the snapshot stays byte for byte. A mark that is still set while pausing (a
    pass in flight) is cleared all the same: an ordered stop must never read as
    an unclean end at the next start (Pitfall 9).
    """
    path = _guard_volume(tmp_path, marks)
    watch = GuardWatch(state_path=path, events=lambda: None, headroom=lambda: None)
    try:
        if suspended:
            watch.suspend_persist()
        before = _snapshot(tmp_path)
        await watch.note_shutdown_begins()
    finally:
        await watch.aclose()
    after = _snapshot(tmp_path)

    assert bool(_data_moved(before, after)) is writes, _changed(before, after)
    rows = _meta_rows(path)
    assert rows.get(META_PASS, "") == ""
    assert rows.get(META_CHOSEN, "") == ""


@pytest.mark.usefixtures("appapi_environment")
def test_p_a_stop_and_a_restart_in_the_pause_move_no_data(
    indexed_volume: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hypothesis: a stop and a start in the pause leave the stock as it was.

    Until the fix of F-41A-01 this held only with the shutdown write stood in
    for by nothing; now it is the real path. The volume after the stop and
    after a new start that reached "paused" again is byte for byte the volume
    of the first "paused", logs of zero bytes and shared memory aside.
    """
    monkeypatch.setattr(findling_main, "pause_wish_reader", wish_reader(True))
    settings().armed_marker.write_text("", encoding="utf-8")
    root = indexed_volume.root

    with TestClient(findling_main.APP):
        assert findling_main._PAUSE is not None
        assert findling_main._PAUSE.state == PAUSE_PAUSED
        first = _snapshot(root)
    stopped = _snapshot(root)
    with TestClient(findling_main.APP):
        assert findling_main._PAUSE is not None
        assert findling_main._PAUSE.state == PAUSE_PAUSED, "the restart reads the wish and pauses again (D-41-05)"
        restarted = _snapshot(root)

    assert _data_moved(first, stopped) == {}
    assert _data_moved(stopped, restarted) == {}


@pytest.mark.usefixtures("appapi_environment")
def test_p_f_41a_04_the_sweep_of_a_pre_check_waits_for_the_end_of_the_pause(
    indexed_volume: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-41A-04 (LOW, fixed): the fp32 sweep of a pre-check is a writer the pause holds.

    A pre-check that fetched the fp32 weights leaves probe_fp32_fetched=1; the
    sweep in the lifespan (ProbeRun.recover) removes the file and clears the
    mark once the companion says int8. Before the fix it did so inside the
    pause. Here a start in the pause with such a mark, the companion ready to
    answer int8 once "paused" is reached: the sweep does not even ask it, and
    the volume stands still byte for byte while paused. Positive control on the
    same path: once the wish turns to "not paused" the same sweep asks, deletes
    the weights and clears the mark. The read of the companion spanning the
    arrival of the pause is forced in the probe after this one.
    """
    from findling.embed.weights import fp32_weights_path
    from findling.nc.queue import CompanionChoice
    from findling.probe import META_PROBE_FP32_FETCHED

    root = indexed_volume.root
    store = open_store(root / "state.db")
    store.write_meta(META_PROBE_FP32_FETCHED, "1")
    store.close()
    weights = fp32_weights_path(settings().models_dir)
    weights.parent.mkdir(parents=True, exist_ok=True)
    weights.write_bytes(b"fp32")
    answered = threading.Event()

    def companion() -> Callable[[], Awaitable[CompanionChoice | None]]:
        async def read() -> CompanionChoice | None:
            # The answer comes only once the pause has said "paused", so the
            # sweep below would run inside the pause and not in the start before it.
            for _ in range(500):
                pause = findling_main._PAUSE
                if pause is not None and pause.state == PAUSE_PAUSED:
                    break
                await asyncio.sleep(0.01)
            answered.set()
            return CompanionChoice(profile=None, precision="int8")

        return read

    wishes: list[bool] = [True]

    def wish_factory() -> Callable[[], Awaitable[bool | None]]:
        async def wish() -> bool | None:
            return wishes[0]

        return wish

    monkeypatch.setattr(findling_main, "companion_reader", companion)
    monkeypatch.setattr(findling_main, "pause_wish_reader", wish_factory)
    settings().armed_marker.write_text("", encoding="utf-8")

    with TestClient(findling_main.APP) as running:
        pause = findling_main._PAUSE
        assert pause is not None
        portal = running.portal
        assert portal is not None
        portal.call(pause.tick)
        assert pause.state == PAUSE_PAUSED
        before = _snapshot(root)
        time.sleep(1.0)
        portal.call(pause.tick)
        assert pause.state == PAUSE_PAUSED
        after = _snapshot(root)
        assert weights.exists(), "the sweep deleted a file of the volume while paused"
        assert _data_moved(before, after) == {}
        assert _meta_rows(root / "state.db").get(META_PROBE_FP32_FETCHED) == "1"
        assert not answered.is_set(), "the sweep asked the companion inside the pause"

        wishes[0] = False
        portal.call(pause.tick)
        assert pause.state == PAUSE_RUNNING
        deadline = time.monotonic() + 15
        while weights.exists() and time.monotonic() < deadline:
            time.sleep(0.05)

    assert answered.is_set()
    assert not weights.exists(), "positive control: outside the pause the same sweep removes the file"
    assert _meta_rows(root / "state.db").get(META_PROBE_FP32_FETCHED) == ""


async def test_p_f_41a_04_a_pause_that_arrives_during_the_read_of_the_companion_holds_the_sweep(
    tmp_path: Path,
) -> None:
    """F-41A-04 (LOW, fixed): the pause is asked again after the read that may span its arrival.

    The interleaving is forced: the pause turns on inside the read of the
    companion, which then answers int8. The sweep deletes nothing and writes
    nothing (sha256 of every file), and it never raised ``sweeping``. Positive
    control on the same ProbeRun: the pause lifted, the next attempt sweeps.
    """
    from findling.nc.queue import CompanionChoice
    from findling.probe import META_PROBE_FP32_FETCHED
    from test_probe_run import PAYLOAD, Rig, _fetched_mark

    wanted = [False]
    rig = Rig(tmp_path, pause_wanted=lambda: wanted[0])
    target = _fetched_mark(rig, PAYLOAD)
    reads = [0]
    sweeping_seen: list[bool] = []

    async def read() -> CompanionChoice | None:
        reads[0] += 1
        if reads[0] == 1:
            wanted[0] = True
        return CompanionChoice(profile="standard", precision="int8")

    before = _snapshot(tmp_path)
    task = asyncio.create_task(rig.run.recover(read, retry=0.05))
    await test_poller._until(lambda: reads[0] >= 1)
    for _ in range(10):
        sweeping_seen.append(rig.run.sweeping)
        await asyncio.sleep(0.02)
    after = _snapshot(tmp_path)
    assert target.exists(), "the sweep deleted the weights in the pause"
    assert _data_moved(before, after) == {}
    assert reads[0] == 1, "no further read while the pause holds"
    assert not any(sweeping_seen)

    wanted[0] = False
    await asyncio.wait_for(task, timeout=5)
    assert not target.exists(), "positive control: without the pause the same sweep removes the file"
    assert rig.meta()[META_PROBE_FP32_FETCHED] == ""
    await rig.run.close()


@pytest.mark.usefixtures("appapi_environment")
@pytest.mark.parametrize("fetching", [True, False], ids=["fetch_in_flight", "control_no_fetch"])
async def test_p_f_41a_04_a_running_fp32_fetch_keeps_the_pause_on_pausing_until_it_ended(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fetching: bool
) -> None:
    """F-41A-04 (LOW, fixed): a fetch of the fp32 weights that began before the pause is waited for.

    The fetch (EmbeddingTrack._procure) writes a .part file into models/ for as
    long as it runs, and it reports its run to findling.precision. The
    coordinator the lifespan builds (main._build_the_pause) counts it as a
    writer: while it runs the state stays "pausing", "paused" comes only after
    its end. Control: the same coordinator without a fetch says "paused" on the
    first tick. No writer is attached, so nothing else can hold it.
    """
    from findling import precision

    del tmp_path
    monkeypatch.setattr(findling_main, "pause_wish_reader", wish_reader(True))
    coordinator = findling_main._build_the_pause(shared_volume=True)
    if fetching:
        precision.begin_procurement()
        try:
            for _ in range(3):
                await coordinator.tick()
                assert coordinator.state == PAUSE_PAUSING, "paused while the fetch still writes into models/"
        finally:
            precision.end_procurement(succeeded=True)
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSED


class _CalmQueue:
    async def stats(self) -> Any:
        return QueueStats(scheduled=0, ok=True, crawling=False)

    async def requeue(self, file_ids: Any, *, kind: str) -> Any:
        del kind
        return CallResult(ok=True, count=len(list(file_ids)))


class _OneMount:
    async def mounts(self) -> Any:
        return MountResult(mounts=(Mount(storage_id=3, root_id=17, overridden_root=18),))

    async def page(self, *, storage: int, root: int, after: int, limit: int) -> Any:
        del storage, root, after, limit
        return SliceResult(
            files=(FileRow(file_id=10, etag="a", size=1, mtime=1, mime="text/plain", state="", reason=""),),
            final=True,
        )


async def test_p_f_41a_02_a_hold_that_lands_in_the_mark_read_of_the_catch_up_keeps_pausing_and_nothing_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-41A-02 (LOW, fixed): a hold that lands while the catch-up reads its mark is seen in time.

    Before the fix Reconcile.run(once=True) asked the hold, awaited
    _catchup_mark() in a thread and only then raised in_flight; a pause that
    settled inside that await reported "paused", and the round then rewound the
    bookmarks in state.db. Now in_flight goes up in the same step as the hold
    check, with no await between them, and the hold is asked again after the
    read. The read is made to wait here so the interleaving is forced every
    time: the coordinator stays "pausing" while the read is open, the round
    never starts, and "paused" follows only once the read is over.
    """
    path = tmp_path / "state.db"
    store = open_store(path)
    store.write_meta(CATCHUP_MARK, CATCHUP_RECONCILE)
    reconcile = Reconcile(
        store=store,
        client_factory=lambda: cast("Any", None),
        files_factory=lambda nc: cast("Any", _OneMount()),
        queue_factory=lambda nc: cast("Any", _CalmQueue()),
        slice_size=1,
        quiet_max=100,
        hour=2,
        min_interval_hours=24,
        pause_seconds=0.0,
        tick_seconds=60.0,
        clock=lambda: 1_800_000_000.0,
        hour_of=lambda: 2,
    )
    reconcile.arm()
    in_the_read = asyncio.Event()
    let_go = asyncio.Event()
    real_mark = reconcile._catchup_mark

    async def slow_mark() -> str:
        in_the_read.set()
        await let_go.wait()
        return await real_mark()

    monkeypatch.setattr(reconcile, "_catchup_mark", slow_mark)
    wishes = [False]

    async def wish() -> bool | None:
        return wishes[0]

    coordinator = PauseCoordinator(read_wish=wish, databases=(path,), clock=lambda: 1_800_000_000.0)
    coordinator.attach_reconcile(reconcile)
    await coordinator.tick()
    assert coordinator.state == PAUSE_RUNNING
    rewinds: list[int] = []
    real_rewind = store.rewind_reconcile_walk

    def counted_rewind() -> None:
        rewinds.append(1)
        real_rewind()

    monkeypatch.setattr(store, "rewind_reconcile_walk", counted_rewind)
    stop = asyncio.Event()
    task = asyncio.create_task(reconcile.run(stop, once=True))
    try:
        await asyncio.wait_for(in_the_read.wait(), timeout=5)
        wishes[0] = True
        await coordinator.tick()
        assert reconcile.in_flight, "the mark read counts as a round in flight"
        assert coordinator.state == PAUSE_PAUSING, "no paused while the catch-up may still start a round"
        let_go.set()
        await test_poller._until(lambda: not reconcile.in_flight)
        await coordinator.tick()
        assert coordinator.state == PAUSE_PAUSED
        before = _snapshot(tmp_path)
        await asyncio.sleep(0.2)
        after = _snapshot(tmp_path)
    finally:
        let_go.set()
        stop.set()
        await asyncio.wait_for(task, timeout=5)
        store.close()

    assert rewinds == [], "a write into state.db after the hold"
    assert _data_moved(before, after) == {}


async def test_p_f_41a_02_control_without_the_hold_the_same_catch_up_rewinds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Positive control of the probe above: with no pause the same round does rewind."""
    path = tmp_path / "state.db"
    store = open_store(path)
    store.write_meta(CATCHUP_MARK, CATCHUP_RECONCILE)
    reconcile = Reconcile(
        store=store,
        client_factory=lambda: cast("Any", None),
        files_factory=lambda nc: cast("Any", _OneMount()),
        queue_factory=lambda nc: cast("Any", _CalmQueue()),
        slice_size=1,
        quiet_max=100,
        hour=2,
        min_interval_hours=24,
        pause_seconds=0.0,
        tick_seconds=60.0,
        clock=lambda: 1_800_000_000.0,
        hour_of=lambda: 2,
    )
    reconcile.arm()
    rewinds: list[int] = []
    real_rewind = store.rewind_reconcile_walk

    def counted_rewind() -> None:
        rewinds.append(1)
        real_rewind()

    monkeypatch.setattr(store, "rewind_reconcile_walk", counted_rewind)
    stop = asyncio.Event()
    task = asyncio.create_task(reconcile.run(stop, once=True))
    try:
        await test_poller._until(lambda: bool(rewinds))
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=5)
        store.close()
    assert rewinds == [1]


# == Q nothing but the wish lifts the pause ============================================


@pytest.fixture
def poller_parts(tmp_path: Path) -> Iterator[tuple[Store, IndexBatchWriter]]:
    index_dir = tmp_path / "index"
    index: Index = open_index(index_dir, test_poller.CONSTITUENTS)
    writer = IndexBatchWriter(index, directory=index_dir, min_free_bytes=0)
    store = open_store(tmp_path / "state.db")
    yield store, writer
    writer.close()
    store.close()


async def test_q_enable_disable_probe_end_and_rebuild_end_do_not_lift_the_pause(
    tmp_path: Path, poller_parts: tuple[Store, IndexBatchWriter], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hypothesis: of every signal that reaches the poller, only the wish ends the pause.

    A real poller with a queue that would hand out a job at once, held by a
    coordinator in "paused". Then: arm (enable), silence and arm (disable and
    enable), a probe hold and its release (end of a pre-check), arm once more
    (the end of a rebuild arms the poller). Not one claim. Then the wish
    "not paused", and the first claim follows.
    """
    store, writer = poller_parts
    queue = test_poller._FakeQueue(ClaimResult(jobs=(test_poller._job(),)))
    poller = test_poller._poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    # The quiesce would give the injected test writer and index handle back, and
    # the resume would rebuild both from the system word list of production;
    # both steps are proven on their own (P above, test_backup_pause.py), so
    # here they are left out and the holds alone are under test.

    async def nothing() -> None:
        return None

    monkeypatch.setattr(poller, "quiesce_for_backup", nothing)
    monkeypatch.setattr(poller, "reopen_after_backup", nothing)
    wishes: list[bool | None] = [True]

    async def wish() -> bool | None:
        return wishes[0]

    coordinator = PauseCoordinator(read_wish=wish, databases=(), clock=lambda: 1_800_000_000.0)
    coordinator.attach_poller(poller)
    poller.arm()
    stop = asyncio.Event()
    task = asyncio.create_task(poller.run(stop))
    try:
        await coordinator.tick()
        assert coordinator.state == PAUSE_PAUSED
        poller.silence()
        poller.arm()
        poller.hold_for_probe()
        poller.release_probe_hold()
        poller.arm()
        for _ in range(3):
            await coordinator.tick()
            await asyncio.sleep(0.05)
        assert coordinator.state == PAUSE_PAUSED
        assert poller.backup_held
        assert queue.claims == 0

        wishes[0] = False
        await coordinator.tick()
        assert coordinator.state == PAUSE_RUNNING
        await test_poller._until(lambda: queue.claims >= 1)
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=5)


@pytest.mark.parametrize(
    ("answers", "final"),
    [
        ((None, None, None), PAUSE_UNKNOWN),
        ((None, True), PAUSE_PAUSED),
        ((None, False), PAUSE_RUNNING),
        ((False, None, None), PAUSE_RUNNING),
        ((True, None, None), PAUSE_PAUSED),
    ],
    ids=["never_read", "read_late_paused", "read_late_running", "running_keeps_running", "paused_keeps_paused"],
)
async def test_q_a_failed_read_changes_nothing_but_a_waiting_start(
    answers: tuple[bool | None, ...], final: str
) -> None:
    """Hypothesis (D-41-19 and its edge): a failed read holds a start and stops nothing later on.

    A new coordinator is a restart: born "unknown", it waits for the first
    answer. Once an answer was read, failed reads leave the last one in force,
    a running instance running, a paused one paused.
    """
    remaining = list(answers)

    async def wish() -> bool | None:
        return remaining.pop(0) if remaining else None

    coordinator = PauseCoordinator(read_wish=wish, databases=(), clock=lambda: 1_800_000_000.0)
    assert coordinator.state == PAUSE_UNKNOWN
    for _ in answers:
        await coordinator.tick()
    assert coordinator.state == final


# == R the checkpoint before "paused" ==================================================


def _wal_database(path: Path) -> None:
    connection = sqlite3.connect(path, autocommit=True)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA wal_autocheckpoint=0")
        connection.execute("CREATE TABLE t (v TEXT)")
        connection.executemany("INSERT INTO t VALUES (?)", [("x" * 100,)] * 50)
    finally:
        connection.close()


async def test_r_a_reader_in_a_long_transaction_keeps_pausing_and_its_end_brings_paused(tmp_path: Path) -> None:
    """Hypothesis: a reader that holds the log keeps the state on pausing, never a false paused.

    Real files, the real checkpoint with a short busy timeout. A second
    connection writes after the reader began, so the log has frames the reader
    still needs.
    """
    path = tmp_path / "state.db"
    _wal_database(path)
    reader = sqlite3.connect(path, autocommit=False)  # a transaction from the first statement on
    reader.execute("SELECT count(*) FROM t").fetchone()
    writer = sqlite3.connect(path, autocommit=True)
    writer.execute("PRAGMA wal_autocheckpoint=0")
    writer.execute("INSERT INTO t VALUES ('y')")
    writer.close()

    def quick(target: Path) -> bool:
        from findling.worker.pause import checkpoint_wal

        return checkpoint_wal(target, busy_timeout_ms=50)

    async def wish() -> bool | None:
        return True

    coordinator = PauseCoordinator(read_wish=wish, databases=(path,), checkpoint=quick)
    try:
        await coordinator.tick()
        await coordinator.tick()
        assert coordinator.state == PAUSE_PAUSING
        assert path.with_name("state.db-wal").stat().st_size > 0
    finally:
        reader.rollback()
        reader.close()
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSED
    wal = path.with_name("state.db-wal")
    assert not wal.exists() or wal.stat().st_size == 0


async def test_r_a_rollback_journal_and_a_missing_vector_file_still_reach_paused(tmp_path: Path) -> None:
    """Hypothesis: the NFS fallback without WAL is paused, and a missing vectors.db is not created."""
    state = tmp_path / "state.db"
    connection = sqlite3.connect(state, autocommit=True)
    connection.execute("PRAGMA journal_mode=DELETE")
    connection.execute("CREATE TABLE t (v TEXT)")
    connection.close()
    vectors = tmp_path / "vectors.db"

    async def wish() -> bool | None:
        return True

    coordinator = PauseCoordinator(read_wish=wish, databases=(state, vectors))
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSED
    assert not vectors.exists()
    assert sorted(_snapshot(tmp_path)) == ["state.db"]


# == S who may pause ===================================================================


def _attributes_before(source: str, signature: str) -> str:
    """The attribute and docblock lines right in front of a method, up to the previous member."""
    head = source.split(signature, 1)[0]
    return re.split(r"\n\t(?:public|private|protected) function [^\n]*\n|\n\t}\n", head)[-1]


def test_s_the_pause_route_is_admin_only_and_needs_the_request_token() -> None:
    """Hypothesis: POST /admin/pause has no attribute that opens it to users or drops CSRF.

    Nextcloud treats a controller method without NoAdminRequired as admin only
    and one without NoCSRFRequired as token bound. Read off the source in front
    of the method and of the class, with a positive control on a route of the
    same app that does carry NoCSRFRequired.
    """
    controller = (PHP_LIB / "Controller" / "SettingsController.php").read_text(encoding="utf-8")
    block = _attributes_before(controller, "public function setPause(")
    assert "FrontpageRoute(verb: 'POST', url: '/admin/pause')" in block
    for opener in ("NoAdminRequired", "NoCSRFRequired", "PublicPage", "AuthorizedAdminSetting", "ExAppRequired"):
        assert opener not in block, opener
    class_head = controller.split("final class SettingsController", 1)[0].split("*/")[-1]
    assert "NoAdminRequired" not in class_head
    assert "NoCSRFRequired" not in class_head

    profile = (PHP_LIB / "Controller" / "ProfileController.php").read_text(encoding="utf-8")
    profile_block = _attributes_before(profile, "public function profile(")
    assert "NoCSRFRequired" in profile_block, "positive control: the reader sees an attribute that is there"
    assert "ExAppRequired" in profile_block


def test_s_only_the_backend_exapp_reads_the_wish() -> None:
    """Hypothesis: a foreign ExApp cannot read /profile, so the wish does not leak or get spoofed."""
    profile = (PHP_LIB / "Controller" / "ProfileController.php").read_text(encoding="utf-8")
    body = profile.split("public function profile(", 1)[1].split("\n\t}\n", 1)[0]
    assert "rejectForeignCaller" in body
    first = body.index("rejectForeignCaller")
    assert first < body.index("paused"), "the caller is checked before the wish is read"


def test_s_the_admin_page_sends_the_switch_with_the_request_token() -> None:
    script = (REPO / "php" / "js" / "admin.js").read_text(encoding="utf-8")
    assert "await send(ROUTE_PAUSE, { paused: !pauseWished })" in script
    send = script.split("function send (", 1)[1].split("\n  }\n", 1)[0]
    assert "requesttoken" in send


# == T the left out count of #25 ========================================================


def _left_out_volume(root: Path, documents: int) -> None:
    store = open_store(root / "state.db")
    try:
        for file_id in range(1, documents + 1):
            store.record(file_id, _meta(1 + file_id % 10, file_id), "indexed")
    finally:
        store.close()
    from findling.store.vectors import EMBEDDING_DIMENSIONS, Chunk, open_vectors

    stock = open_vectors(root / "vectors.db")
    try:
        for file_id in range(1, documents + 1, 2):
            stock.replace_chunks(
                file_id, [Chunk(ordinal=0, char_start=0, char_end=10, embedding=bytes(EMBEDDING_DIMENSIONS))]
            )
    finally:
        stock.close()


def test_t_ten_lists_in_a_row_run_one_count_at_a_time_and_keep_four(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hypothesis: ever new leaveOut lists neither pile up threads nor grow the cache.

    Each count is made to take a while and records how many count threads are
    alive inside it. Ten lists one after the other, each asked twice with a
    join between: never more than one living thread, never more than four
    cached lists, and every list gets its figure on its second ask.
    """
    _left_out_volume(volume, 200)
    alive: list[int] = []
    real = status.embedded_in_storages

    def counting(state_db: Path, vectors_db: Path, storage_ids: Any) -> int:
        alive.append(sum(1 for thread in threading.enumerate() if thread.name == "findling-left-out-refresh"))
        time.sleep(0.02)
        return real(state_db, vectors_db, storage_ids)

    monkeypatch.setattr(status, "embedded_in_storages", counting)
    vectors_db = settings().vectors_db
    figures: list[int | None] = []
    for storage in range(1, 11):
        status._cached_left_out(vectors_db, [storage])
        status._cached_left_out(vectors_db, [storage, 99])  # a second list while the first counts
        status.join_left_out_refresh()
        figures.append(status._cached_left_out(vectors_db, [storage]))
        assert len(status._LEFT_OUT_CACHE) <= status.LEFT_OUT_CACHE_KEYS
    assert max(alive) == 1
    assert all(figure is not None for figure in figures)


def test_t_the_background_count_writes_nothing(volume: Path) -> None:
    """Hypothesis: the count in the pause leaves both databases as the checkpoint left them."""
    _left_out_volume(volume, 200)
    from findling.worker.pause import checkpoint_wal

    assert checkpoint_wal(volume / "state.db")
    assert checkpoint_wal(volume / "vectors.db")
    before = _snapshot(volume)
    status._cached_left_out(settings().vectors_db, [3])
    status.join_left_out_refresh()
    assert status._cached_left_out(settings().vectors_db, [3]) is not None
    after = _snapshot(volume)
    assert _data_moved(before, after) == {}


# == U the fixes of the post audit 1.6.0 ===============================================


def _poller_for_refusals(tmp_path: Path, parts: tuple[Store, IndexBatchWriter]) -> Poller:
    store, writer = parts
    queue = test_poller._FakeQueue()
    return test_poller._poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)


def test_u_storage_id_zero_counts_as_one_storage_and_a_second_storage_escalates(
    tmp_path: Path, poller_parts: tuple[Store, IndexBatchWriter]
) -> None:
    """Hypothesis: rows requeueAs could not resolve (storage 0) never escalate on their own.

    Ten claimed, six refusals of 500 from storage 0: verdicts only. The first
    refusal from another storage, with the count past five, is the outage.
    """
    poller = _poller_for_refusals(tmp_path, poller_parts)
    poller._claimed_in_pass = 10
    for queue_id in range(1, 7):
        poller._count_refusal(GatewayRefused(500, file_id=queue_id), test_poller._job(queue_id, queue_id, storage_id=0))
    with pytest.raises(poller_module._RefusalsPiledUp):
        poller._count_refusal(GatewayRefused(500, file_id=7), test_poller._job(7, 7, storage_id=4))


async def test_u_a_mark_that_cannot_be_written_never_keeps_the_rest_from_going_back(
    tmp_path: Path, poller_parts: tuple[Store, IndexBatchWriter], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hypothesis: _abort hands the unrefused rows back even when every charged mark fails."""
    store, writer = poller_parts
    queue = test_poller._FakeQueue()
    poller = test_poller._poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    poller._open()
    poller._held = {1, 2, 3}
    poller._refused_jobs = {1: test_poller._job(1, 101)}

    def broken(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(store, "record", broken)
    await poller._abort(cast("Any", queue), 3, charged=frozenset({1}))
    assert queue.unlocked == [[2, 3]]


def test_u_the_retry_cap_is_three_refusals_of_one_version(tmp_path: Path) -> None:
    """Hypothesis: the streak counts refusals of one etag, three are retried, a fourth is not.

    Read off the rows of a real state database. Positive control: an indexed
    row on the same etag is no candidate, and a new etag starts a new streak.
    """
    store = open_store(tmp_path / "state.db")
    try:
        meta = _meta(3, 7)
        store.record(7, meta, "indexed")
        assert store.gateway_retry_candidates([7], GATEWAY_ERROR_RETRIES) == set()
        seen: list[bool] = []
        for _ in range(5):
            store.record(7, meta, "failed", "gateway_error")
            seen.append(7 in store.gateway_retry_candidates([7], GATEWAY_ERROR_RETRIES))
        assert seen == [True, True, True, False, False]
        moved = dataclasses.replace(meta, etag="etag-new")
        store.record(7, moved, "failed", "gateway_error")
        assert store.gateway_retry_candidates([7], GATEWAY_ERROR_RETRIES) == {7}
    finally:
        store.close()


@pytest.mark.usefixtures("appapi_environment", "volume")
async def test_u_the_outage_grid_over_every_status_from_400_to_599() -> None:
    """Hypothesis: exactly 408, 429, 502, 503 and 504 are an outage, 404 is not yours, the rest a verdict.

    Driven through the real streaming fetch with a transport that answers the
    status, not through the constant.
    """
    outage: set[int] = set()
    verdict: set[int] = set()
    not_yours: set[int] = set()
    for code in range(400, 600):

        def answer(request: httpx.Request, code: int = code) -> httpx.Response:
            del request
            return httpx.Response(code, content=b"x")

        async with httpx.AsyncClient(transport=httpx.MockTransport(answer), base_url="http://localhost:8080") as http:
            try:
                result = await nc_client._stream_file(http, "alice", 7, "alice", io.BytesIO(), expected=0)
            except GatewayRefused:
                verdict.add(code)
                continue
            except NextcloudException:
                outage.add(code)
                continue
            assert result is None
            not_yours.add(code)
    assert outage == {408, 429, 502, 503, 504}
    assert not_yours == {404}
    assert len(verdict) == 200 - 6


# == V what the pause costs ============================================================


async def test_v_the_coordinator_reads_at_the_pace_of_the_poll_and_backs_off_without_an_answer() -> None:
    """Hypothesis: answered reads are paced by the poll, unanswered ones back off (F-41A-03, fixed).

    Run with a poll of 50 ms for one second. An answering companion gets about
    twenty reads; with no companion behind the route the ladder doubles the
    wait from the poll on (50, 100, 200, 400 ms ...), so about five. Before the
    fix both cases read twenty times, 240 an hour at the default poll.
    """
    for answer, low, high in ((False, 15, 22), (None, 3, 6)):
        reads = 0

        async def wish(answer: bool | None = answer) -> bool | None:
            nonlocal reads
            reads += 1
            return answer

        coordinator = PauseCoordinator(read_wish=wish, databases=(), poll_seconds=0.05)
        stop = asyncio.Event()
        task = asyncio.create_task(coordinator.run(stop))
        await asyncio.sleep(1.0)
        stop.set()
        await asyncio.wait_for(task, timeout=5)
        assert low <= reads <= high, (answer, reads)
    assert 3600 / PAUSE_POLL_SECONDS == 240
    assert 3600 / RETREAT_MAX_SECONDS == 12


@pytest.mark.parametrize("error", [False, True], ids=["no_answer", "read_raises"])
async def test_v_f_41a_03_the_ladder_retreats_to_twelve_reads_an_hour_and_an_answer_resets_it(error: bool) -> None:
    """F-41A-03 (LOW, fixed): the reads of a coordinator without an answer climb a ladder like the poller's.

    At the default poll of 15 s the wait doubles from the poll on and ends at
    RETREAT_MAX_SECONDS of the poller, 300 s, which is 12 reads an hour. The
    state stays "unknown" all the while and every writer stays held (D-41-19,
    D-17). The first answer puts the wait back to the poll and the state
    follows the wish at once.
    """
    answers: list[bool | None] = [None] * 8

    async def wish() -> bool | None:
        if answers:
            value = answers.pop(0)
            if value is None and error:
                raise httpx.ConnectError("no companion")
            return value
        return False

    coordinator = PauseCoordinator(read_wish=wish, databases=(), clock=lambda: 1_800_000_000.0)
    assert coordinator.read_interval == PAUSE_POLL_SECONDS
    seen: list[float] = []
    for _ in range(8):
        await coordinator.tick()
        seen.append(coordinator.read_interval)
        assert coordinator.state == PAUSE_UNKNOWN
        assert coordinator.wants_pause()
    assert seen == [15, 30, 60, 120, 240, 300, 300, 300]
    assert 3600 / seen[-1] == 12
    assert seen[-1] == RETREAT_MAX_SECONDS == PAUSE_RETREAT_MAX_SECONDS
    assert PAUSE_UNREADABLE_WARN_AFTER == RETREAT_AFTER_ROUNDS
    await coordinator.tick()
    assert coordinator.state == PAUSE_RUNNING
    assert coordinator.read_interval == PAUSE_POLL_SECONDS


async def test_v_f_41a_03_one_warning_after_three_unreadable_reads_and_one_info_on_the_way_back(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """F-41A-03 (LOW, fixed): a container without its companion says so once, and says it again only after a recovery.

    Three unreadable reads in a row give one WARNING with the state word and
    the cap of the ladder, never a path; ten more give nothing; the first
    answer gives one INFO line. A new streak warns once more.
    """
    answers: list[bool | None] = [None] * 13 + [True] + [None] * 3

    async def wish() -> bool | None:
        return answers.pop(0) if answers else None

    coordinator = PauseCoordinator(read_wish=wish, databases=(), clock=lambda: 1_800_000_000.0)
    caplog.set_level("DEBUG", logger="findling.worker.pause")

    def warnings() -> list[str]:
        return [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]

    def infos_back() -> list[str]:
        return [r.getMessage() for r in caplog.records if r.levelname == "INFO" and "readable again" in r.getMessage()]

    await coordinator.tick()
    await coordinator.tick()
    assert warnings() == []
    await coordinator.tick()
    assert len(warnings()) == 1
    line = warnings()[0]
    assert "unknown" in line
    assert "300" in line
    assert line.isascii()
    for _ in range(10):
        await coordinator.tick()
    assert len(warnings()) == 1
    assert infos_back() == []
    await coordinator.tick()
    assert len(infos_back()) == 1
    assert coordinator.read_interval == PAUSE_POLL_SECONDS
    for _ in range(3):
        await coordinator.tick()
    assert len(warnings()) == 2
    assert coordinator.state == PAUSE_PAUSED, "the last answer stays in force"
