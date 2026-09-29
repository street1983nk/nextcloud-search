"""N extraction children behind one resizable gate and one executor of their own.

**Why a pool of our own and not a process pool of the futures module.** The
guard in :mod:`findling.extract.sandbox` exists because a hanging call inside a
C extension cannot be cancelled from Python, only killed with its process. A
process pool of the standard library cannot do that for a single task, it knows
no ``RLIMIT_AS`` per child, and it has none of the four recycling rules. So the
pool holds N unchanged :class:`~findling.extract.sandbox.ExtractionWorker`
objects, each with its own child, its own pipe and its own file count, the same
shape ``scripts/ops/ocr_slot_probe.py`` measured: N threads, and every thread
holds its own worker. Workers are built on first demand only, so a pool of four
that never sees more than one OCR file at a time starts one child and not four.

**Why an executor of its own.** Waiting on a child pipe blocks a thread for as
long as the scan takes, up to the hard OCR deadline. The default executor of
the event loop is the one the ``to_thread`` helper of asyncio uses, and ``/search``,
``/snippets`` and ``/status`` share it; N slots parked there starve the Unified
Search, which is the mechanism behind issue #19 inside the main process (phase
26, pitfall 5). The waits therefore run in a ``ThreadPoolExecutor`` named
``findling-slot`` and never in the default one.

**The gate.** :class:`SlotGate` bounds how many extractions run at once, and its
limit can change at runtime: the memory guard lowers it, a shrink takes effect at
the next acquisition, and a running child is never killed for a throttle.
Waiters are served in arrival order, so work is stolen from one shared queue
instead of being dealt out to fixed slots. With a limit of one this is the
container as it was before phase 26.

**What the pool leaves to its caller.** :class:`~findling.extract.errors.ChildKilled`
travels through :meth:`SlotPool.run` unchanged; whether a file is run again on
its own is the poller's decision. The pool does not import the dispatcher, for
the same import hygiene the sandbox keeps.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import logging
import threading
from collections import deque
from collections.abc import AsyncIterator, Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Final

from findling.extract.errors import ExtractionOutcome
from findling.extract.sandbox import ExtractionWorker

# Slot 1 always runs: a limit below one would stop the indexing for good.
_MIN_LIMIT: Final = 1

# The one refusal a closed pool gives, whichever path finds it closed.
_CLOSED: Final = "this SlotPool is closed"

LOGGER = logging.getLogger("findling.extract.pool")


class SlotGate:
    """A semaphore whose size can change while it is held.

    ``asyncio.Semaphore`` cannot shrink, so this is a counter under an
    ``asyncio.Condition``. Growing wakes the waiters at once; shrinking only
    moves the bar the next acquisition has to clear, and the slots already
    taken run to their end.
    """

    def __init__(self, limit: int) -> None:
        self._limit = max(_MIN_LIMIT, limit)
        self._in_use = 0
        self._condition = asyncio.Condition()

    @property
    def limit(self) -> int:
        """How many slots may be taken at once."""
        return self._limit

    @property
    def in_use(self) -> int:
        """How many slots are taken right now."""
        return self._in_use

    async def set_limit(self, limit: int) -> None:
        """Move the limit, never below one; waiters recheck at once."""
        async with self._condition:
            self._limit = max(_MIN_LIMIT, limit)
            self._condition.notify_all()

    @contextlib.asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        """Hold one slot for the body of the ``async with``.

        Every waiter rechecks the bar after every wake-up, which is what makes
        a shrink effective without touching a running holder. asyncio locks
        hand themselves on in arrival order and a waiter that has to wait again
        queues behind the ones that were already there, so the order holds.
        """
        async with self._condition:
            await self._condition.wait_for(lambda: self._in_use < self._limit)
            self._in_use += 1
        try:
            yield
        finally:
            async with self._condition:
                self._in_use -= 1
                self._condition.notify_all()


class SlotPool:
    """Up to ``size`` extraction workers, built lazily and shared by whoever is free.

    :meth:`run` and :meth:`run_probe` block; they are meant to be handed to
    :meth:`call`, which runs them in the pool's own executor. The free list and
    the set of busy workers live under one ``threading.Lock``, and a caller
    that finds every worker busy waits on a condition of that lock rather than
    spinning.
    """

    def __init__(self, size: int, *, worker_factory: Callable[[], ExtractionWorker] = ExtractionWorker) -> None:
        self._size = max(_MIN_LIMIT, size)
        self._factory = worker_factory
        self._lock = threading.Lock()
        self._available = threading.Condition(self._lock)
        self._free: deque[ExtractionWorker] = deque()
        self._busy: set[ExtractionWorker] = set()
        self._built = 0
        self._closed = False
        self._executor: ThreadPoolExecutor | None = None

    @property
    def size(self) -> int:
        """The most workers this pool will ever build."""
        return self._size

    def run(
        self,
        path: str,
        mime: str,
        size: int,
        *,
        route: str | None = None,
        timeout_seconds: float | None = None,
    ) -> ExtractionOutcome:
        """Extract one file on a free worker; the signature of ``extract_guarded``.

        The same keywords as the facade, so that the poller's ``ExtractFile``
        and the fakes of its tests fit either one. ChildKilled is not caught.
        """
        worker = self._take()
        try:
            return worker.run(path, mime, size, route=route, timeout_seconds=timeout_seconds)
        finally:
            self._give(worker)

    def run_probe(self, kind: str, amount: float, *, timeout_seconds: float | None = None) -> ExtractionOutcome:
        """Run a diagnostic job on a free worker, for the tests and the kill harness."""
        worker = self._take()
        try:
            return worker.probe(kind, amount, timeout_seconds=timeout_seconds)
        finally:
            self._give(worker)

    def call[T](self, fn: Callable[..., T], /, *args: object, **kwargs: object) -> Awaitable[T]:
        """Run a blocking callable in the pool's executor and await it.

        Never the ``to_thread`` helper of asyncio: that is the default executor the search
        shares. Refused with RuntimeError once the pool is closed.
        """
        loop = asyncio.get_running_loop()
        job = functools.partial(fn, *args, **kwargs)
        # The submission happens under the lock, so close() cannot shut the
        # executor down between the check and the hand over (26-REVIEW IN-02).
        # Only the future is created here; the wait happens outside.
        with self._lock:
            if self._closed:
                raise RuntimeError(_CLOSED)
            if self._executor is None:
                self._executor = ThreadPoolExecutor(max_workers=self._size, thread_name_prefix="findling-slot")
            try:
                return loop.run_in_executor(self._executor, job)
            except RuntimeError as error:
                # An executor that refuses anyway says so in its own words; the
                # caller should read the pool's.
                raise RuntimeError(_CLOSED) from error

    def pids(self) -> tuple[int, ...]:
        """The process ids of the children that exist right now, free or busy."""
        with self._lock:
            workers = [*self._free, *self._busy]
        return tuple(pid for pid in (worker.pid for worker in workers) if pid is not None)

    def close(self) -> None:
        """End every child now, busy ones included. Idempotent.

        A busy worker is halted, not stopped: stop would wait for a job that may
        be a thirty second scan, and halt kills the group at once while its
        waiting call ends with failed(corrupt), never with ChildKilled. Free
        workers are stopped politely. Calls that still wait for a worker are
        woken and refused.
        """
        with self._lock:
            if self._closed:
                return
            self._closed = True
            busy = list(self._busy)
            free = list(self._free)
            self._busy.clear()
            self._free.clear()
            executor = self._executor
            self._executor = None
            self._available.notify_all()
        for worker in busy:
            worker.halt()
        for worker in free:
            worker.stop()
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)

    def shed_idle(self) -> int:
        """Stop every free child and return how many; a busy one is never touched.

        The latency probe measures its base H0 without resting children
        (27-RESEARCH Pitfall 5): a child kept warm from the last pass would
        count as used memory and bend the base. The pool builds new workers on
        the next demand, as after the start. A no-op on a closed pool. The
        children are stopped outside the lock, so a slow stop never holds up
        a caller.
        """
        with self._lock:
            if self._closed:
                return 0
            idle = list(self._free)
            self._free.clear()
            self._built -= len(idle)
            # Room to build again: wake a caller that waited on the size bound.
            self._available.notify_all()
        for worker in idle:
            try:
                worker.stop()
            # One stubborn child must not keep the others running.
            except Exception as error:
                LOGGER.warning("an idle extraction child did not stop cleanly, an %s", type(error).__name__)
        return len(idle)

    def _take(self) -> ExtractionWorker:
        with self._available:
            self._available.wait_for(lambda: self._closed or bool(self._free) or self._built < self._size)
            if self._closed:
                raise RuntimeError(_CLOSED)
            if self._free:
                worker = self._free.popleft()
            else:
                # Lazy: the constructor starts no child, the first job does.
                worker = self._factory()
                self._built += 1
            self._busy.add(worker)
            return worker

    def _give(self, worker: ExtractionWorker) -> None:
        with self._available:
            closed = self._closed
            self._busy.discard(worker)
            if not closed:
                self._free.append(worker)
                self._available.notify()
        if closed:
            # Closed while this job ran: the child goes with the pool.
            worker.stop()
