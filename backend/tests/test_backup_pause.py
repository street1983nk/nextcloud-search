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
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from tantivy import Index

import test_poller
from conftest import write_wordlist
from findling import guard
from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter
from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import FileRow, Mount, MountResult, SliceResult
from findling.nc.queue import CallResult, ClaimResult, QueueStats
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


async def test_a_backup_hold_ends_the_reconcile_after_the_slice_and_keeps_the_bookmark(store: Store) -> None:
    gate = _Gate()
    reconcile = _reconcile(store, gate)
    assert not reconcile.in_flight
    round_task = asyncio.create_task(reconcile.run_once())
    try:
        await asyncio.wait_for(gate.started.wait(), timeout=5)
        assert reconcile.in_flight, "the slice is running"
        reconcile.hold_for_backup()
        gate.release.set()
        result = await asyncio.wait_for(round_task, timeout=5)
    finally:
        gate.release.set()

    assert result.state == ROUND_HELD
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
