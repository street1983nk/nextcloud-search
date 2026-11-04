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
    PAUSE_RUNNING,
    PAUSE_UNKNOWN,
    PauseCoordinator,
)
from findling.worker.poller import RETREAT_MAX_SECONDS, Poller
from findling.worker.reconcile import GATEWAY_ERROR_RETRIES, Reconcile
from findling.worker.watch import GuardWatch

REPO = Path(__file__).resolve().parents[2]
PHP_LIB = REPO / "php" / "lib"

Sign = Callable[[str], dict[str, str]]
Snapshot = dict[str, tuple[int, int, str]]


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
def test_p_f_41a_01_a_stop_in_the_pause_writes_two_meta_rows_into_the_log(
    indexed_volume: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-41A-01 (LOW, open): the shutdown of a paused container writes state.db.

    GuardWatch.note_shutdown_begins() clears the two pass marks of the memory
    guard with a write of its own, past suspend_persist(). Measured: 16 512
    bytes of log, the keys multi_slot_pass and multi_slot_chosen set to "".
    The next start checkpoints that log into state.db before it says "paused"
    again. Pins today's behaviour; the fix turns this red.
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

    moved = _data_moved(before, after)
    # Either the log keeps the two rows (16 512 bytes measured) or the close of
    # the last connection has already checkpointed them into state.db itself.
    assert moved, "the stop of a paused container wrote nothing"
    assert set(moved) <= {"state.db", "state.db-wal"}
    rows = _meta_rows(root / "state.db")
    assert rows.get("multi_slot_pass") == ""
    assert rows.get("multi_slot_chosen") == ""


@pytest.mark.usefixtures("appapi_environment")
def test_p_without_the_shutdown_write_a_restart_in_the_pause_moves_no_data(
    indexed_volume: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hypothesis: apart from F-41A-01, a stop and a start in the pause leave the stock as it was.

    Control of F-41A-01: the one write stood in for by nothing, the volume after
    the stop and after a new start that reached "paused" again is byte for byte
    the volume of the first "paused", logs of zero bytes and shared memory aside.
    """

    async def nothing(self: GuardWatch) -> None:
        del self

    monkeypatch.setattr(GuardWatch, "note_shutdown_begins", nothing)
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
def test_p_f_41a_04_the_sweep_of_a_pre_check_writes_and_deletes_in_the_pause(
    indexed_volume: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-41A-04 (LOW, open): the fp32 sweep of a pre-check is no writer the pause knows.

    A pre-check that fetched the fp32 weights leaves probe_fp32_fetched=1; the
    sweep in the lifespan (ProbeRun.recover) removes the file and clears the
    mark once the companion says int8, whatever the pause says. Here a start
    in the pause with such a mark, the companion answering only after "paused":
    the sweep deletes the weights and writes state.db inside the pause. The fetch of the
    fp32 weights (EmbeddingTrack._procure) is the same kind of task and is not
    asked either. Pins today's behaviour; the fix turns this red.
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

    def companion() -> Callable[[], Awaitable[CompanionChoice | None]]:
        async def read() -> CompanionChoice | None:
            # The answer comes only once the pause has said "paused", so the
            # sweep below runs inside the pause and not in the start before it.
            for _ in range(500):
                pause = findling_main._PAUSE
                if pause is not None and pause.state == PAUSE_PAUSED:
                    break
                await asyncio.sleep(0.01)
            return CompanionChoice(profile=None, precision="int8")

        return read

    monkeypatch.setattr(findling_main, "companion_reader", companion)
    monkeypatch.setattr(findling_main, "pause_wish_reader", wish_reader(True))
    settings().armed_marker.write_text("", encoding="utf-8")

    with TestClient(findling_main.APP) as running:
        pause = findling_main._PAUSE
        assert pause is not None
        portal = running.portal
        assert portal is not None
        portal.call(pause.tick)
        assert pause.state == PAUSE_PAUSED
        deadline = time.monotonic() + 5
        while weights.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert pause.state == PAUSE_PAUSED

    assert not weights.exists(), "the sweep deleted a file of the volume while paused"
    assert _meta_rows(root / "state.db").get(META_PROBE_FP32_FETCHED) == ""


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


async def test_p_f_41a_02_the_catch_up_can_write_after_paused_when_the_hold_lands_in_its_mark_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-41A-02 (LOW, open): a hold that lands while the catch-up reads its mark is seen too late.

    Reconcile.run(once=True) asks the hold, then awaits _catchup_mark() in a
    thread, and only then raises in_flight. A pause that settles inside that
    await sees no round in flight and reports "paused"; the round then starts
    and its first catch-up round rewinds the bookmarks, a write into state.db.
    The read is made to wait here so the window is hit every time. Pins
    today's behaviour; the fix turns this red.
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
        assert coordinator.state == PAUSE_PAUSED, "no round in flight while the mark is read"
        let_go.set()
        await test_poller._until(lambda: bool(rewinds))
        await test_poller._until(lambda: not reconcile.in_flight)
    finally:
        let_go.set()
        stop.set()
        await asyncio.wait_for(task, timeout=5)
        store.close()

    assert rewinds == [1], "a write into state.db after paused"


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


async def test_v_the_coordinator_reads_the_wish_once_per_poll_and_no_more() -> None:
    """Hypothesis: the reads are paced by the poll, idle or not; 3600 / 15 = 240 an hour.

    Run with a poll of 50 ms for one second: about twenty reads, and the
    default poll gives the hourly figure. The same pace holds in "unknown"
    with no companion behind the route (F-41A-03): there is no back-off like
    the retreat of the poller, which ends at one claim every RETREAT_MAX_SECONDS.
    """
    for answer in (False, None):
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
        assert 15 <= reads <= 22, (answer, reads)
    assert 3600 / PAUSE_POLL_SECONDS == 240
    assert 3600 / RETREAT_MAX_SECONDS == 12
