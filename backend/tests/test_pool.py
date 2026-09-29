"""The slot pool: N children behind one resizable gate and one executor of their own.

The gate and the bookkeeping of the pool are tested with a fake worker, because
what they promise (never more than the limit, first come first served, lazy
construction, a worker that always comes back) has nothing to do with a child
process. The POSIX tests at the bottom then use real children for the two
properties that only real children can show: two slots really run side by side,
and closing the pool ends a busy child at once instead of waiting for its scan.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor

import pytest

from findling.extract.errors import ChildKilled, ExtractionOutcome, Reason, State
from findling.extract.pool import SlotGate, SlotPool
from findling.extract.sandbox import ExtractionWorker

ONLY_POSIX = pytest.mark.skipif(
    sys.platform == "win32",
    reason="the children are Linux processes in the container this ships in",
)

UNSUPPORTED = "application/x-findling-not-a-real-type"
NOWHERE = "/nowhere/does-not-exist.bin"


class _FakeWorker(ExtractionWorker):
    """A worker without a child: it records where it ran and blocks on request."""

    def __init__(self, *, release: threading.Event | None = None, error: Exception | None = None) -> None:
        super().__init__(max_files=10, timeout_seconds=5)
        self._release = release
        self._error = error
        self.entered = threading.Event()
        self.jobs = 0

    @property
    def pid(self) -> int | None:
        return None

    def run(
        self,
        path: str,
        mime: str,
        size: int,
        *,
        route: str | None = None,
        timeout_seconds: float | None = None,
    ) -> ExtractionOutcome:
        del path, mime, size, route, timeout_seconds
        self.jobs += 1
        self.entered.set()
        if self._release is not None:
            self._release.wait(5)
        if self._error is not None:
            raise self._error
        return ExtractionOutcome.indexed(str(id(self)))

    def stop(self) -> None:
        return

    def halt(self) -> None:
        return


class _Factory:
    """Builds fake workers and remembers every one of them."""

    def __init__(self, *, release: threading.Event | None = None, error: Exception | None = None) -> None:
        self.release = release
        self.error = error
        self.built: list[_FakeWorker] = []

    def __call__(self) -> ExtractionWorker:
        worker = _FakeWorker(release=self.release, error=self.error)
        self.built.append(worker)
        return worker


async def test_the_gate_never_lets_more_than_its_limit_through() -> None:
    gate = SlotGate(2)
    running = 0
    highest = 0

    async def hold() -> None:
        nonlocal running, highest
        async with gate.slot():
            running += 1
            highest = max(highest, running)
            await asyncio.sleep(0.2)
            running -= 1

    await asyncio.gather(hold(), hold(), hold())

    assert highest == 2
    assert gate.in_use == 0


async def test_a_shrink_lets_the_holders_finish_and_bars_the_next_one() -> None:
    gate = SlotGate(2)
    release_first = asyncio.Event()
    release_second = asyncio.Event()
    third_in = asyncio.Event()

    async def hold(release: asyncio.Event) -> None:
        async with gate.slot():
            await release.wait()

    async def third() -> None:
        async with gate.slot():
            third_in.set()

    first = asyncio.create_task(hold(release_first))
    second = asyncio.create_task(hold(release_second))
    await asyncio.sleep(0.05)
    assert gate.in_use == 2

    await gate.set_limit(1)
    assert gate.in_use == 2, "a throttle never takes a running slot away"
    waiting = asyncio.create_task(third())

    release_first.set()
    await first
    await asyncio.sleep(0.05)
    assert gate.in_use == 1
    assert not third_in.is_set(), "one slot is taken and the limit is one"

    release_second.set()
    await second
    await asyncio.wait_for(waiting, timeout=1)
    assert third_in.is_set()


async def test_a_limit_below_one_is_one() -> None:
    gate = SlotGate(0)
    assert gate.limit == 1

    await gate.set_limit(0)
    assert gate.limit == 1

    await gate.set_limit(-3)
    assert gate.limit == 1


async def test_waiters_are_served_in_arrival_order() -> None:
    gate = SlotGate(1)
    release = asyncio.Event()
    order: list[str] = []

    async def holder() -> None:
        async with gate.slot():
            await release.wait()

    async def waiter(name: str) -> None:
        async with gate.slot():
            order.append(name)
            await asyncio.sleep(0.01)

    held = asyncio.create_task(holder())
    await asyncio.sleep(0.02)
    waiters = []
    for name in ("a", "b", "c", "d"):
        waiters.append(asyncio.create_task(waiter(name)))
        await asyncio.sleep(0.02)

    release.set()
    await asyncio.gather(held, *waiters)

    assert order == ["a", "b", "c", "d"]


def test_three_calls_land_on_three_workers_and_a_fourth_waits() -> None:
    release = threading.Event()
    factory = _Factory(release=release)
    pool = SlotPool(3, worker_factory=factory)
    assert factory.built == [], "no worker before the first demand"

    results: list[ExtractionOutcome] = []

    def job() -> None:
        results.append(pool.run(NOWHERE, UNSUPPORTED, 1))

    threads = [threading.Thread(target=job) for _ in range(3)]
    for thread in threads:
        thread.start()
    for _ in range(100):
        if len(factory.built) == 3 and all(worker.entered.is_set() for worker in factory.built):
            break
        time.sleep(0.02)
    assert len(factory.built) == 3

    fourth = threading.Thread(target=job)
    fourth.start()
    time.sleep(0.2)
    assert len(factory.built) == 3, "the fourth call waits for a worker and builds none"
    assert [worker.jobs for worker in factory.built] == [1, 1, 1], "one call on each worker"

    release.set()
    for thread in [*threads, fourth]:
        thread.join(5)

    assert len(results) == 4
    assert len(factory.built) == 3
    assert sum(worker.jobs for worker in factory.built) == 4
    pool.close()


async def test_call_runs_in_the_pools_own_executor() -> None:
    pool = SlotPool(2, worker_factory=_Factory())
    try:
        name = await pool.call(lambda: threading.current_thread().name)
    finally:
        pool.close()

    assert name.startswith("findling-slot")
    assert not name.startswith("asyncio")


async def test_call_passes_arguments_through() -> None:
    pool = SlotPool(1, worker_factory=_Factory())
    try:
        outcome = await pool.call(pool.run, NOWHERE, UNSUPPORTED, 1, route="ocr", timeout_seconds=3.0)
    finally:
        pool.close()

    assert outcome.state is State.INDEXED


def test_child_killed_reaches_the_caller_and_the_worker_comes_back() -> None:
    factory = _Factory(error=ChildKilled(engine=False))
    pool = SlotPool(1, worker_factory=factory)

    with pytest.raises(ChildKilled) as caught:
        pool.run(NOWHERE, UNSUPPORTED, 1)
    assert caught.value.engine is False

    with pytest.raises(ChildKilled):
        pool.run(NOWHERE, UNSUPPORTED, 1)
    assert len(factory.built) == 1, "the same worker served the second call"
    assert factory.built[0].jobs == 2
    pool.close()


async def test_a_closed_pool_refuses_further_calls() -> None:
    pool = SlotPool(1, worker_factory=_Factory())
    pool.close()
    pool.close()

    with pytest.raises(RuntimeError):
        pool.call(time.sleep, 0)
    with pytest.raises(RuntimeError):
        pool.run(NOWHERE, UNSUPPORTED, 1)


class _ShutDownExecutor(ThreadPoolExecutor):
    """An executor that close() shut down between the check and the submission."""

    def submit[T](self, fn: Callable[..., T], /, *args: object, **kwargs: object) -> Future[T]:
        del fn, args, kwargs
        raise RuntimeError("cannot schedule new futures after shutdown")


async def test_a_call_racing_close_gets_the_pools_own_refusal() -> None:
    # 26-REVIEW IN-02: the executor's words must not reach the poller.
    pool = SlotPool(1, worker_factory=_Factory())
    shut = _ShutDownExecutor(max_workers=1)
    # The double stands for the race window.
    pool._executor = shut
    try:
        with pytest.raises(RuntimeError, match=r"^this SlotPool is closed$"):
            pool.call(time.sleep, 0)
    finally:
        shut.shutdown()
        pool.close()


class _RecordingWorker(_FakeWorker):
    """A fake worker that records its stop and whether the pool lock was held then."""

    def __init__(self, pool_lock: list[threading.Lock], *, release: threading.Event | None = None) -> None:
        super().__init__(release=release)
        self._pool_lock = pool_lock
        self.stopped = False
        self.lock_held_at_stop: bool | None = None

    def stop(self) -> None:
        self.stopped = True
        self.lock_held_at_stop = self._pool_lock[0].locked()


class _BreakingWorker(_FakeWorker):
    def stop(self) -> None:
        raise OSError("the pipe is gone")


def test_shed_idle_stops_only_the_free_children() -> None:
    release = threading.Event()
    lock_box: list[threading.Lock] = []
    built: list[_RecordingWorker] = []

    def factory() -> ExtractionWorker:
        # The first worker blocks until released, the second returns at once.
        worker = _RecordingWorker(lock_box, release=release if not built else None)
        built.append(worker)
        return worker

    pool = SlotPool(2, worker_factory=factory)
    # The test checks that stop runs outside the pool lock.
    lock_box.append(pool._lock)
    busy_job = threading.Thread(target=pool.run, args=(NOWHERE, UNSUPPORTED, 1))
    busy_job.start()
    for _ in range(100):
        if built and built[0].entered.is_set():
            break
        time.sleep(0.02)
    pool.run(NOWHERE, UNSUPPORTED, 1)
    busy, idle = built

    assert pool.shed_idle() == 1
    assert idle.stopped
    assert idle.lock_held_at_stop is False, "a child is stopped outside the pool lock"
    assert not busy.stopped, "a running child is never shed"

    release.set()
    busy_job.join(5)
    pool.run(NOWHERE, UNSUPPORTED, 1)
    assert len(built) == 2, "the busy worker came back to the free list and served again"
    assert busy.jobs == 2
    assert pool.shed_idle() == 1
    assert busy.stopped
    pool.close()


def test_shed_idle_lets_the_pool_build_again() -> None:
    factory = _Factory()
    pool = SlotPool(1, worker_factory=factory)
    pool.run(NOWHERE, UNSUPPORTED, 1)

    assert pool.shed_idle() == 1
    assert pool.shed_idle() == 0
    pool.run(NOWHERE, UNSUPPORTED, 1)
    assert len(factory.built) == 2, "a fresh worker after the shed, within the size bound"
    pool.close()


def test_shed_idle_survives_a_child_that_will_not_stop() -> None:
    pool = SlotPool(2, worker_factory=_BreakingWorker)
    pool.run(NOWHERE, UNSUPPORTED, 1)

    assert pool.shed_idle() == 1
    pool.close()


def test_shed_idle_on_a_closed_pool_is_a_no_op() -> None:
    pool = SlotPool(1, worker_factory=_Factory())
    pool.run(NOWHERE, UNSUPPORTED, 1)
    pool.close()

    assert pool.shed_idle() == 0


def test_importing_the_pool_does_not_load_the_dispatcher() -> None:
    code = "import sys, findling.extract.pool; print('findling.extract.dispatch' in sys.modules)"
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )

    assert answer.stdout.strip().splitlines()[-1] == "False"


@ONLY_POSIX
async def test_two_real_slots_run_side_by_side() -> None:
    pool = SlotPool(2)
    try:
        # Warm up both children first: a spawn costs an interpreter start, and
        # the timing below is about the slots and not about process creation.
        await asyncio.gather(pool.call(pool.run_probe, "sleep", 0.2), pool.call(pool.run_probe, "sleep", 0.2))
        pids = pool.pids()
        assert len(pids) == 2
        assert len(set(pids)) == 2

        started = time.monotonic()
        outcomes = await asyncio.gather(
            pool.call(pool.run_probe, "sleep", 0.5), pool.call(pool.run_probe, "sleep", 0.5)
        )
        elapsed = time.monotonic() - started
    finally:
        pool.close()

    assert [outcome.state for outcome in outcomes] == [State.INDEXED, State.INDEXED]
    assert elapsed < 0.9


@ONLY_POSIX
async def test_close_ends_a_busy_child_at_once_without_child_killed() -> None:
    pool = SlotPool(1)
    job = asyncio.ensure_future(pool.call(pool.run_probe, "sleep", 30))
    for _ in range(200):
        if pool.pids():
            break
        await asyncio.sleep(0.05)
    assert pool.pids()
    # Let the job reach the child, so that the halt meets a running scan.
    await asyncio.sleep(0.5)

    started = time.monotonic()
    pool.close()
    outcome = await asyncio.wait_for(job, timeout=10)
    elapsed = time.monotonic() - started

    assert outcome == ExtractionOutcome.failed(Reason.CORRUPT)
    assert elapsed < 6
    assert pool.pids() == ()
    with pytest.raises(RuntimeError):
        pool.call(pool.run_probe, "sleep", 0)
