"""The backup pause of issue #37: every writer holds, and the pause reports paused late.

The promise of #37 in its own words: indexing stops and everything is flushed to
disk while search keeps working (D-41-06). Two halves carry it. Every writer of
the volume, the poller, the embed runner, the reconcile and the memory guard
watch, has a backup hold of its own that nothing but the pause coordinator lifts:
not an enable of AppAPI (arm), not the end of a pre-check, not a rebuild (D-41-05).
And the coordinator reports "paused" only after the pass in flight ended on its
own (D-41-18), the poller gave its index writer back and both SQLite files were
checkpointed to an empty WAL (D-41-03).
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from findling.worker.pause import (
    PAUSE_PAUSED,
    PAUSE_PAUSING,
    PAUSE_POLL_SECONDS,
    PAUSE_RUNNING,
    PAUSE_SETTLE_SECONDS,
    PAUSE_UNKNOWN,
    PauseCoordinator,
    checkpoint_wal,
)
from tantivy import Index

import test_poller
import test_queue_client
from conftest import write_wordlist
from findling import guard
from findling import main as findling_main
from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter
from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import FileRow, Mount, MountResult, SliceResult
from findling.nc.queue import CallResult, ClaimResult, CompanionChoice, QueueStats
from findling.profile import Profile
from findling.store.repo import Store, open_store
from findling.worker.embedding import EmbedRunner
from findling.worker.poller import Poller
from findling.worker.reconcile import ROUND_HELD, Reconcile
from findling.worker.watch import GuardWatch

_until = test_poller._until


@pytest.fixture
def index_dir(tmp_path: Path) -> Path:
    return tmp_path / "index"


@pytest.fixture
def index(index_dir: Path) -> Index:
    return open_index(index_dir, test_poller.CONSTITUENTS)


@pytest.fixture
def writer(index: Index, index_dir: Path) -> Iterator[IndexBatchWriter]:
    batch_writer = IndexBatchWriter(index, directory=index_dir, min_free_bytes=0)
    yield batch_writer
    batch_writer.close()


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


def _poller(store: Store, writer: IndexBatchWriter, tmp_path: Path, queue: test_poller._FakeQueue) -> Poller:
    return test_poller._poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)


async def _run(worker: Any) -> tuple[asyncio.Task[None], asyncio.Event]:
    stop = asyncio.Event()
    return asyncio.create_task(worker.run(stop)), stop


async def _end(task: asyncio.Task[None], stop: asyncio.Event) -> None:
    stop.set()
    await asyncio.wait_for(task, timeout=5)


# -- the poller ---------------------------------------------------------------


async def test_a_backup_hold_keeps_the_poller_from_its_next_pass(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    queue = test_poller._FakeQueue(ClaimResult(jobs=(test_poller._job(),)))
    poller = _poller(store, writer, tmp_path, queue)
    assert not poller.backup_held, "set at birth, so a poller without a coordinator runs as it always did"
    poller.arm()
    poller.hold_for_backup()
    assert poller.backup_held
    task, stop = await _run(poller)
    try:
        await asyncio.sleep(0.1)
        assert queue.claims == 0

        poller.release_backup_hold()
        await _until(lambda: queue.claims >= 1)
        assert not poller.backup_held
    finally:
        await _end(task, stop)


async def test_arm_does_not_lift_a_backup_hold(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # Pitfall 1: the enabled handler of AppAPI calls arm(), and an enable must
    # not end a backup the admin asked for.
    queue = test_poller._FakeQueue(ClaimResult(jobs=(test_poller._job(),)))
    poller = _poller(store, writer, tmp_path, queue)
    poller.hold_for_backup()
    poller.arm()
    task, stop = await _run(poller)
    try:
        await asyncio.sleep(0.05)
        poller.silence()
        poller.arm()
        await asyncio.sleep(0.1)
        assert queue.claims == 0
        assert poller.backup_held
    finally:
        await _end(task, stop)


async def test_the_end_of_a_probe_does_not_lift_a_backup_hold(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    queue = test_poller._FakeQueue(ClaimResult(jobs=(test_poller._job(),)))
    poller = _poller(store, writer, tmp_path, queue)
    poller.arm()
    poller.hold_for_backup()
    task, stop = await _run(poller)
    try:
        poller.hold_for_probe()
        await asyncio.sleep(0.05)
        poller.release_probe_hold()
        await asyncio.sleep(0.1)
        assert queue.claims == 0
        assert poller.backup_held
        assert not poller.probe_held
    finally:
        await _end(task, stop)


async def test_a_pass_in_flight_finishes_before_the_hold_bites(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # D-41-18: no abort. The pass works its claim to the end and acknowledges
    # it, so no row is charged and none goes back unjudged.
    queue = test_poller._FakeQueue(
        ClaimResult(jobs=(test_poller._job(),)), ClaimResult(jobs=(test_poller._job(92, 4712),))
    )
    poller = _poller(store, writer, tmp_path, queue)
    real = poller.run_once
    started = asyncio.Event()
    gate = asyncio.Event()
    calls: list[int] = []

    async def gated() -> Any:
        calls.append(1)
        if len(calls) == 1:
            started.set()
            await gate.wait()
        return await real()

    monkeypatch.setattr(poller, "run_once", gated)
    poller.arm()
    task, stop = await _run(poller)
    try:
        await asyncio.wait_for(started.wait(), timeout=5)
        poller.hold_for_backup()
        assert poller.pass_in_flight
        gate.set()
        await _until(lambda: not poller.pass_in_flight and bool(queue.acknowledged))
        await asyncio.sleep(0.05)

        assert queue.acknowledged == [([91], {})]
        assert queue.unlocked == []
        assert len(calls) == 1
        assert not poller.pass_in_flight
    finally:
        await _end(task, stop)


async def test_quiesce_for_backup_hands_the_writer_back_without_silencing(
    volume: Path, store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    write_wordlist(volume)
    poller = _poller(store, writer, tmp_path, test_poller._FakeQueue(ClaimResult(jobs=())))
    queue = await asyncio.to_thread(poller._open)
    poller.arm()
    poller._held = {91}
    closes: list[str] = []
    real_close = poller.track.close

    def track_close() -> None:
        closes.append("track")
        real_close()

    poller._track.close = track_close  # type: ignore[method-assign]

    await poller.quiesce_for_backup()

    assert poller._writer is None, "the writer is closed, its merges are done and its lock is free"
    assert writer._writer is None, "close() of the batch writer ran, which waits for the merging threads"
    assert closes == ["track"]
    assert cast("Any", queue).unlocked == [[91]]
    assert poller.armed, "a backup is not a disable"

    await poller.quiesce_for_backup()
    assert closes == ["track"], "a second quiesce has nothing left to give back"

    again = await asyncio.to_thread(poller._open)
    assert again is queue
    assert poller._writer is not None
    assert poller._writer is not writer, "the next pass opens a fresh writer"


async def test_the_quiesced_poller_opens_the_track_again_before_the_runner_goes_on(
    volume: Path, store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The runner drives the same track, and after a resume it may run before
    # the next pass of the poller has opened it again.
    write_wordlist(volume)
    poller = _poller(store, writer, tmp_path, test_poller._FakeQueue(ClaimResult(jobs=())))
    await asyncio.to_thread(poller._open)
    opens: list[bool] = []
    real_open = poller.track.open

    def track_open(*, wire: bool) -> None:
        opens.append(wire)
        real_open(wire=wire)

    poller._track.open = track_open  # type: ignore[method-assign]
    await poller.reopen_after_backup()
    assert opens == [], "nothing was given back, so nothing is opened"

    await poller.quiesce_for_backup()
    await poller.reopen_after_backup()
    assert len(opens) == 1
    await poller.reopen_after_backup()
    assert len(opens) == 1


# -- the embed runner -----------------------------------------------------------


def _runner() -> EmbedRunner:
    return EmbedRunner(
        track=cast("Any", object()),
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        queue_factory=lambda nc: cast("Any", object()),
        tick=0.0,
    )


def _count_rounds(runner: EmbedRunner, monkeypatch: pytest.MonkeyPatch) -> list[int]:
    calls: list[int] = []

    async def counted() -> str:
        calls.append(1)
        await asyncio.sleep(0.01)
        return "empty"

    monkeypatch.setattr(runner, "run_once", counted)
    return calls


async def test_a_backup_hold_keeps_the_runner_from_its_next_round(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _runner()
    calls = _count_rounds(runner, monkeypatch)
    assert not runner.backup_held
    runner.arm()
    runner.hold_for_backup()
    task, stop = await _run(runner)
    try:
        await asyncio.sleep(0.1)
        assert calls == []
        assert runner.parked.is_set()

        runner.release_backup_hold()
        await _until(lambda: len(calls) >= 1)
    finally:
        await _end(task, stop)


async def test_arm_and_the_end_of_a_probe_do_not_lift_the_backup_hold_of_the_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    calls = _count_rounds(runner, monkeypatch)
    runner.hold_for_backup()
    runner.arm()
    task, stop = await _run(runner)
    try:
        runner.silence()
        runner.arm()
        runner.hold_for_probe()
        await asyncio.sleep(0.05)
        runner.release_probe_hold()
        await asyncio.sleep(0.1)
        assert calls == []
        assert runner.backup_held
    finally:
        await _end(task, stop)


# -- the reconcile --------------------------------------------------------------


class _Gate:
    """The quiet gate of the reconcile, answered calm, with a slice that can wait."""

    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.pages = 0

    async def stats(self) -> Any:
        return QueueStats(scheduled=0, ok=True, crawling=False)

    async def requeue(self, file_ids: Any, *, kind: str) -> Any:
        del kind
        return CallResult(ok=True, count=len(list(file_ids)))


class _Files:
    """Two pages for one mount; the first one waits until the test lets it go."""

    def __init__(self, gate: _Gate) -> None:
        self._gate = gate

    async def mounts(self) -> Any:
        return MountResult(mounts=(Mount(storage_id=3, root_id=17, overridden_root=18),))

    async def page(self, *, storage: int, root: int, after: int, limit: int) -> Any:
        del storage, root, limit
        self._gate.pages += 1
        if self._gate.pages == 1:
            self._gate.started.set()
            await self._gate.release.wait()
            return SliceResult(
                files=(FileRow(file_id=10, etag="a", size=1, mtime=1, mime="text/plain", state="", reason=""),),
                final=False,
            )
        del after
        return SliceResult(final=True)


def _reconcile(store: Store, gate: _Gate) -> Reconcile:
    return Reconcile(
        store=store,
        client_factory=lambda: cast("AsyncNextcloudApp", None),
        files_factory=lambda nc: cast("Any", _Files(gate)),
        queue_factory=lambda nc: cast("Any", gate),
        slice_size=1,
        quiet_max=100,
        hour=2,
        min_interval_hours=24,
        pause_seconds=0.0,
        tick_seconds=60.0,
        clock=lambda: 1_800_000_000.0,
        hour_of=lambda: 2,
    )


async def test_the_reconcile_waits_on_a_backup_hold(store: Store) -> None:
    gate = _Gate()
    reconcile = _reconcile(store, gate)
    assert not reconcile.backup_held
    reconcile.arm()
    reconcile.hold_for_backup()
    task, stop = await _run(reconcile)
    try:
        await asyncio.sleep(0.1)
        assert gate.pages == 0
        assert not reconcile.in_flight
        reconcile.release_backup_hold()
        await _until(lambda: gate.pages >= 1)
        gate.release.set()
    finally:
        gate.release.set()
        await _end(task, stop)


async def test_a_backup_hold_ends_the_reconcile_after_the_slice_and_keeps_the_bookmark(
    store: Store, caplog: pytest.LogCaptureFixture
) -> None:
    gate = _Gate()
    reconcile = _reconcile(store, gate)
    assert not reconcile.in_flight
    reconcile.arm()
    with caplog.at_level(logging.INFO, logger="findling.worker.reconcile"):
        task, stop = await _run(reconcile)
        try:
            await asyncio.wait_for(gate.started.wait(), timeout=5)
            assert reconcile.in_flight, "the slice is running"
            reconcile.hold_for_backup()
            gate.release.set()
            await _until(lambda: not reconcile.in_flight)
            await asyncio.sleep(0.05)
        finally:
            gate.release.set()
            await _end(task, stop)

    assert any(f"reconcile round {ROUND_HELD}," in record.getMessage() for record in caplog.records)
    assert gate.pages == 1, "the second slice did not start"
    assert not reconcile.in_flight
    cursor = store.reconcile_cursor(3)
    assert cursor.after_file_id == 10, "the bookmark stands behind the slice that ran"


# -- the memory guard watch -------------------------------------------------------


async def test_the_guard_watch_does_not_persist_while_held(tmp_path: Path) -> None:
    path = tmp_path / "state.db"
    open_store(path).close()
    watch = GuardWatch(state_path=path, events=lambda: None, headroom=lambda: None, tick=0.0)
    writes: list[dict[str, str]] = []
    real_write = watch._write_meta

    def counted(values: dict[str, str]) -> bool:
        writes.append(dict(values))
        return real_write(values)

    watch._write_meta = counted  # type: ignore[method-assign]
    watch.suspend_persist()
    assert guard.lower(guard.CAUSE_OOM_KILL, now=1.0, chosen=Profile.PERFORMANCE, effective=Profile.PERFORMANCE)
    await watch.run_once()
    await watch.run_once()
    assert writes == [], "nothing reaches state.db during the pause"

    await watch.resume_persist()
    assert len(writes) == 1, "the change of the pause is written once afterwards"
    assert writes[0][guard.META_CAUSE] == guard.CAUSE_OOM_KILL
    await watch.resume_persist()
    await watch.run_once()
    assert len(writes) == 1
    await watch.aclose()


# -- the checkpoint -----------------------------------------------------------------


def _wal_database(path: Path) -> sqlite3.Connection:
    """A WAL database with frames in its log, and the connection that keeps the log alive.

    The connection stays open on purpose: the last connection to close
    checkpoints and removes the log itself, and then there would be nothing
    left to prove.
    """
    connection = sqlite3.connect(path, autocommit=True)
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA wal_autocheckpoint = 0")
    connection.execute("CREATE TABLE t (x INTEGER)")
    for value in range(50):
        connection.execute("INSERT INTO t VALUES (?)", (value,))
    return connection


def _wal_of(path: Path) -> Path:
    return path.with_name(path.name + "-wal")


def test_checkpoint_empties_the_wal(tmp_path: Path) -> None:
    path = tmp_path / "state.db"
    connection = _wal_database(path)
    try:
        assert _wal_of(path).stat().st_size > 0
        assert checkpoint_wal(path) is True
        assert _wal_of(path).stat().st_size == 0
        assert connection.execute("SELECT count(*) FROM t").fetchone() == (50,)
    finally:
        connection.close()


def test_checkpoint_with_a_reader_in_a_transaction_is_busy(tmp_path: Path) -> None:
    path = tmp_path / "vectors.db"
    connection = _wal_database(path)
    reader = sqlite3.connect(path, autocommit=True)
    try:
        reader.execute("BEGIN")
        assert reader.execute("SELECT count(*) FROM t").fetchone() == (50,)
        connection.execute("INSERT INTO t VALUES (99)")

        assert checkpoint_wal(path, busy_timeout_ms=0) is False
        assert _wal_of(path).stat().st_size > 0

        reader.execute("COMMIT")
        assert checkpoint_wal(path, busy_timeout_ms=0) is True
        assert _wal_of(path).stat().st_size == 0
    finally:
        reader.close()
        connection.close()


def test_checkpoint_of_a_missing_file_is_true_and_creates_nothing(tmp_path: Path) -> None:
    path = tmp_path / "vectors.db"
    assert checkpoint_wal(path) is True
    assert not path.exists()
    assert not _wal_of(path).exists()


def test_checkpoint_without_wal_mode_is_true(tmp_path: Path) -> None:
    # The NFS fallback of enable_wal: rollback journal, log -1.
    path = tmp_path / "state.db"
    connection = sqlite3.connect(path, autocommit=True)
    try:
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute("CREATE TABLE t (x INTEGER)")
        assert checkpoint_wal(path) is True
        assert not _wal_of(path).exists()
    finally:
        connection.close()


def test_a_broken_file_is_no_checkpoint_and_names_no_path(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    path = tmp_path / "state.db"
    path.write_bytes(b"this is not a database at all, " * 100)
    with caplog.at_level(logging.WARNING, logger="findling.worker.pause"):
        assert checkpoint_wal(path) is False
    assert caplog.records
    for record in caplog.records:
        assert str(tmp_path) not in record.getMessage()
        assert "state.db" not in record.getMessage()


# -- the coordinator ----------------------------------------------------------------


class _Writer:
    """A poller, runner, reconcile and guard watch in one double, as the coordinator sees them."""

    def __init__(self) -> None:
        self.backup_held = False
        self.pass_in_flight = False
        self.in_flight = False
        self.parked = asyncio.Event()
        self.parked.set()
        self.quiesces = 0
        self.reopens = 0
        self.suspended = False
        self.resumes = 0

    def hold_for_backup(self) -> None:
        self.backup_held = True

    def release_backup_hold(self) -> None:
        self.backup_held = False

    async def quiesce_for_backup(self) -> None:
        self.quiesces += 1

    async def reopen_after_backup(self) -> None:
        self.reopens += 1

    def suspend_persist(self) -> None:
        self.suspended = True

    async def resume_persist(self) -> None:
        self.suspended = False
        self.resumes += 1


class _Wish:
    """The wish of the admin as the companion answers it, one answer per read."""

    def __init__(self, *answers: bool | None) -> None:
        self.answers = list(answers)
        self.reads = 0

    def set(self, *answers: bool | None) -> None:
        self.answers = list(answers)

    async def __call__(self) -> bool | None:
        self.reads += 1
        if len(self.answers) > 1:
            return self.answers.pop(0)
        return self.answers[0] if self.answers else None


class _Checkpoints:
    def __init__(self, *answers: bool) -> None:
        self.answers = list(answers)
        self.calls: list[Path] = []

    def __call__(self, path: Path) -> bool:
        self.calls.append(path)
        if len(self.answers) > 1:
            return self.answers.pop(0)
        return self.answers[0] if self.answers else True


class _Flag:
    def __init__(self) -> None:
        self.value = False

    def __call__(self) -> bool:
        return self.value


def _all_held(poller: _Writer, runner: _Writer, reconcile: _Writer, watch: _Writer) -> bool:
    return all((poller.backup_held, runner.backup_held, reconcile.backup_held, watch.suspended))


def _none_held(poller: _Writer, runner: _Writer, reconcile: _Writer, watch: _Writer) -> bool:
    return not any((poller.backup_held, runner.backup_held, reconcile.backup_held, watch.suspended))


DATABASES = (Path("state.db"), Path("vectors.db"))


def _coordinator(
    wish: _Wish,
    checkpoints: _Checkpoints | None = None,
    *,
    rebuild: _Flag | None = None,
    probe: _Flag | None = None,
    resumed: list[int] | None = None,
) -> PauseCoordinator:
    async def on_resume() -> None:
        if resumed is not None:
            resumed.append(1)

    return PauseCoordinator(
        read_wish=wish,
        databases=DATABASES,
        rebuild_busy=rebuild or _Flag(),
        probe_busy=probe or _Flag(),
        on_resume=on_resume,
        clock=lambda: 1_800_000_000.0,
        checkpoint=checkpoints or _Checkpoints(True),
    )


def _attach_all(coordinator: PauseCoordinator) -> tuple[_Writer, _Writer, _Writer, _Writer]:
    poller, runner, reconcile, watch = _Writer(), _Writer(), _Writer(), _Writer()
    coordinator.attach_poller(cast("Any", poller))
    coordinator.attach_runner(cast("Any", runner))
    coordinator.attach_reconcile(cast("Any", reconcile))
    coordinator.attach_guard_watch(cast("Any", watch))
    return poller, runner, reconcile, watch


def test_the_state_words_are_a_closed_set() -> None:
    assert (PAUSE_RUNNING, PAUSE_PAUSING, PAUSE_PAUSED, PAUSE_UNKNOWN) == ("running", "pausing", "paused", "unknown")
    assert PAUSE_POLL_SECONDS == 15
    assert PAUSE_SETTLE_SECONDS == 1


async def test_the_coordinator_is_born_unknown_and_holding() -> None:
    coordinator = _coordinator(_Wish(False))
    assert coordinator.state == PAUSE_UNKNOWN
    assert coordinator.wants_pause()
    assert coordinator.paused_since is None
    poller, runner, reconcile, watch = _attach_all(coordinator)
    assert _all_held(poller, runner, reconcile, watch)

    await coordinator.tick()
    assert coordinator.state == PAUSE_RUNNING
    assert not coordinator.wants_pause()

    late = _Writer()
    coordinator.attach_reconcile(cast("Any", late))
    assert not late.backup_held, "a writer born into a running instance is not held"


async def test_an_unreadable_wish_keeps_the_writers_held() -> None:
    # D-41-19: no answer is no permission.
    wish = _Wish(None)
    coordinator = _coordinator(wish)
    poller, runner, reconcile, watch = _attach_all(coordinator)

    await coordinator.tick()
    await coordinator.tick()
    assert coordinator.state == PAUSE_UNKNOWN
    assert _all_held(poller, runner, reconcile, watch)

    wish.set(False)
    await coordinator.tick()
    assert coordinator.state == PAUSE_RUNNING
    assert _none_held(poller, runner, reconcile, watch)


async def test_a_read_that_raises_counts_as_unreadable() -> None:
    async def broken() -> bool | None:
        raise RuntimeError

    coordinator = PauseCoordinator(read_wish=broken, databases=DATABASES, checkpoint=_Checkpoints(True))
    await coordinator.tick()
    assert coordinator.state == PAUSE_UNKNOWN


async def test_a_failed_read_while_running_does_not_stop_the_indexing() -> None:
    wish = _Wish(False)
    coordinator = _coordinator(wish)
    poller, *_ = _attach_all(coordinator)
    await coordinator.tick()
    wish.set(None)
    await coordinator.tick()
    assert coordinator.state == PAUSE_RUNNING
    assert not poller.backup_held


async def test_pause_waits_for_the_batch_then_checkpoints() -> None:
    wish = _Wish(False)
    checkpoints = _Checkpoints(True)
    coordinator = _coordinator(wish, checkpoints)
    poller, runner, reconcile, watch = _attach_all(coordinator)
    await coordinator.tick()

    poller.pass_in_flight = True
    runner.parked.clear()
    reconcile.in_flight = True
    wish.set(True)
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSING
    assert _all_held(poller, runner, reconcile, watch)
    assert poller.quiesces == 0
    assert checkpoints.calls == []
    assert coordinator.paused_since is None

    poller.pass_in_flight = False
    await coordinator.tick()
    runner.parked.set()
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSING, "the reconcile is still in its slice"
    assert poller.quiesces == 0

    reconcile.in_flight = False
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSED
    assert poller.quiesces == 1
    assert checkpoints.calls == list(DATABASES)
    assert coordinator.paused_since == 1_800_000_000

    await coordinator.tick()
    assert poller.quiesces == 1
    assert checkpoints.calls == list(DATABASES), "paused stays paused without a second checkpoint"


async def test_a_busy_checkpoint_stays_pausing_and_retries() -> None:
    checkpoints = _Checkpoints(True, False, True)
    coordinator = _coordinator(_Wish(True), checkpoints)
    poller, *_ = _attach_all(coordinator)

    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSING, "vectors.db was busy, so nothing is copyable yet"
    assert coordinator.paused_since is None
    assert poller.quiesces == 1

    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSED
    assert poller.quiesces == 1, "the writer was given back once for this entry"
    assert len(checkpoints.calls) == 4


async def test_pause_twice_and_resume_twice_are_idempotent() -> None:
    wish = _Wish(True)
    resumed: list[int] = []
    coordinator = _coordinator(wish, resumed=resumed)
    poller, *_ = _attach_all(coordinator)

    await coordinator.tick()
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSED
    assert poller.quiesces == 1

    wish.set(False)
    await coordinator.tick()
    await coordinator.tick()
    assert coordinator.state == PAUSE_RUNNING
    assert resumed == [1]
    assert poller.reopens == 1
    assert not poller.backup_held


async def test_resume_while_pausing_releases_without_a_checkpoint() -> None:
    wish = _Wish(False)
    checkpoints = _Checkpoints(True)
    coordinator = _coordinator(wish, checkpoints)
    poller, runner, reconcile, watch = _attach_all(coordinator)
    await coordinator.tick()

    poller.pass_in_flight = True
    wish.set(True)
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSING

    wish.set(False)
    await coordinator.tick()
    poller.pass_in_flight = False
    await coordinator.tick()
    assert coordinator.state == PAUSE_RUNNING
    assert checkpoints.calls == []
    assert poller.quiesces == 0
    assert _none_held(poller, runner, reconcile, watch)


async def test_rebuild_and_probe_keep_the_coordinator_pausing() -> None:
    rebuild, probe = _Flag(), _Flag()
    rebuild.value = True
    coordinator = _coordinator(_Wish(True), rebuild=rebuild, probe=probe)
    poller, *_ = _attach_all(coordinator)

    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSING
    rebuild.value = False
    probe.value = True
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSING
    assert poller.quiesces == 0
    probe.value = False
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSED


async def test_resume_after_paused_lifts_all_holds_and_calls_on_resume() -> None:
    wish = _Wish(True)
    resumed: list[int] = []
    coordinator = _coordinator(wish, resumed=resumed)
    poller, runner, reconcile, watch = _attach_all(coordinator)
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSED
    assert resumed == []

    wish.set(False)
    await coordinator.tick()
    assert coordinator.state == PAUSE_RUNNING
    assert coordinator.paused_since is None
    assert resumed == [1]
    assert _none_held(poller, runner, reconcile, watch)
    assert watch.resumes == 1
    assert poller.reopens == 1


async def test_a_writer_without_runner_or_reconcile_counts_as_resting() -> None:
    coordinator = PauseCoordinator(read_wish=_Wish(True), databases=DATABASES, checkpoint=_Checkpoints(True))
    await coordinator.tick()
    assert coordinator.state == PAUSE_PAUSED


async def test_paused_leaves_both_wal_files_empty(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    state, vectors = tmp_path / "state.db", tmp_path / "vectors.db"
    first, second = _wal_database(state), _wal_database(vectors)
    try:
        coordinator = PauseCoordinator(read_wish=_Wish(True), databases=(state, vectors))
        with caplog.at_level(logging.INFO, logger="findling.worker.pause"):
            await coordinator.tick()
        assert coordinator.state == PAUSE_PAUSED
        assert _wal_of(state).stat().st_size == 0
        assert _wal_of(vectors).stat().st_size == 0
        messages = [record.getMessage() for record in caplog.records]
        assert "backup pause: pausing" in messages
        assert "backup pause: paused" in messages
        assert all(str(tmp_path) not in message for message in messages)
    finally:
        first.close()
        second.close()


async def test_the_run_loop_reaches_paused_and_ends_on_stop() -> None:
    coordinator = PauseCoordinator(
        read_wish=_Wish(True),
        databases=DATABASES,
        checkpoint=_Checkpoints(False, True),
        poll_seconds=0.05,
        settle_seconds=0.01,
    )
    stop = asyncio.Event()
    task = asyncio.create_task(coordinator.run(stop))
    try:
        await _until(lambda: coordinator.state == PAUSE_PAUSED)
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=5)


# -- the wish over the profile route (plan 41-04) ------------------------------


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        pytest.param({"profile": "standard", "paused": True}, True, id="true"),
        pytest.param({"profile": "standard", "paused": False}, False, id="false"),
        pytest.param({"profile": "standard"}, False, id="companion-1.6.1"),
        pytest.param({"paused": "yes"}, False, id="string"),
        pytest.param({"paused": 1}, False, id="one"),
        pytest.param({"paused": None}, False, id="null"),
        pytest.param([], False, id="empty-php-array"),
    ],
)
async def test_companion_choice_reads_paused(answer: object, expected: bool) -> None:
    """D-41-05, T-41-17: only a JSON true is a wish to pause; a readable answer without it is not."""
    session = test_queue_client._FakeSession({("GET", test_queue_client.PROFILE_PATH): answer})

    choice = await test_queue_client._queue(session).companion_choice()

    assert choice.paused is expected


async def test_a_failed_profile_read_is_no_wish_at_all() -> None:
    """D-41-19: a call that failed is None, the one value that holds a starting container."""
    session = test_queue_client._FakeSession(error=OSError("no such route"))

    choice = await test_queue_client._queue(session).companion_choice()

    assert choice.paused is None


async def test_the_wish_reader_of_main_maps_the_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    """The reader the lifespan builds: True, False, None, and a read that does not come in time raises."""
    # The suite replaces pause_wish_reader with a stand in (conftest); undo
    # brings the real one back for this case.
    monkeypatch.undo()
    answers: list[CompanionChoice | None] = [
        CompanionChoice(profile=None, precision=None, paused=True),
        CompanionChoice(profile="standard", precision=None),
        None,
    ]

    def companion() -> Callable[[], Awaitable[CompanionChoice | None]]:
        async def read() -> CompanionChoice | None:
            if not answers:
                await asyncio.sleep(1)
                return None
            return answers.pop(0)

        return read

    monkeypatch.setattr(findling_main, "companion_reader", companion)
    monkeypatch.setattr(findling_main, "PAUSE_READ_SECONDS", 0.01)
    wish = findling_main.pause_wish_reader()

    assert await wish() is True
    assert await wish() is False
    assert await wish() is None
    with pytest.raises(TimeoutError):
        await wish()
