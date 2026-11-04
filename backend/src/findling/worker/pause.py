"""The backup pause of issue #37: hold every writer, flush, and only then say paused.

The promise of #37 in its own words: indexing stops and everything is flushed to
disk while search keeps working (D-41-06). An admin who copies the volume with
the container running needs a moment in which no file of it changes, and this
module is what makes that moment and tells when it has begun.

**The wish and the state are two things.** The wish of the admin lives in the
appconfig of the companion alone (``findling/paused``) and comes over the
existing ``/profile`` route; nothing of it is kept on the volume, so a restored
backup never comes up paused without anyone knowing (E-41-03-01). The state is
what this process has done about the wish, one word of a closed set:

* ``unknown``: the wish was never read. Every writer is held, because a restart
  in the middle of a backup must not start a pass before it knows (D-41-19).
* ``pausing``: the wish is "paused", the holds are set, and the coordinator
  waits for the pass in flight to end on its own (D-41-18), then gives the index
  writer back and checkpoints both SQLite files.
* ``paused``: both checkpoints came back complete. Only now is the volume
  copyable, and only now does the word appear (D-41-03).
* ``running``: the wish is "not paused" and nothing is held.

**Why every writer has its own hold.** ``arm`` and ``silence`` belong to the
enabled handler of AppAPI and the lifespan, the probe hold is lifted in the
finally of a pre-check, a rebuild arms the poller when it is done. A pause that
shared any of those signals would end the moment one of them came by (D-41-05,
41-RESEARCH.md Pitfall 1), so the poller, the embed runner, the reconcile and
the memory guard watch each carry a backup hold that only this coordinator
touches.

**No abort.** A pass in flight works its claim to the end and acknowledges it;
on an OCR batch that can take up to the lease of the queue, about thirty
minutes. The coordinator has no timeout of its own (E-41-03-03): ``pausing`` is
the honest answer for as long as it takes.

Log lines carry state words and class names only, never a path or a file name.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import sqlite3
import time
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Final, Literal, Protocol

from findling.store.repo import _BUSY_TIMEOUT_MS

LOGGER = logging.getLogger("findling.worker.pause")

PauseState = Literal["running", "pausing", "paused", "unknown"]

PAUSE_RUNNING: Final = "running"
PAUSE_PAUSING: Final = "pausing"
PAUSE_PAUSED: Final = "paused"
PAUSE_UNKNOWN: Final = "unknown"

# How often the wish of the admin is read, in seconds. One small request to the
# companion per read; fifteen seconds keep a pause or a resume within one
# glance of the admin page without the coordinator becoming a load of its own
# (41-RESEARCH.md, assumption A3).
PAUSE_POLL_SECONDS: Final = 15
# How often a pausing coordinator asks again whether the pass in flight has
# ended and the checkpoint went through. Cheap questions about flags in memory
# and, once those agree, one checkpoint per file; a second is short enough that
# "paused" follows the end of the batch closely.
PAUSE_SETTLE_SECONDS: Final = 1

Clock = Callable[[], float]
Checkpoint = Callable[[Path], bool]
WishReader = Callable[[], Awaitable[bool | None]]


class _Poller(Protocol):
    @property
    def pass_in_flight(self) -> bool: ...
    def hold_for_backup(self) -> None: ...
    def release_backup_hold(self) -> None: ...
    async def quiesce_for_backup(self) -> None: ...
    async def reopen_after_backup(self) -> None: ...


class _Runner(Protocol):
    parked: asyncio.Event

    def hold_for_backup(self) -> None: ...
    def release_backup_hold(self) -> None: ...


class _Reconcile(Protocol):
    @property
    def in_flight(self) -> bool: ...
    def hold_for_backup(self) -> None: ...
    def release_backup_hold(self) -> None: ...


class _GuardWatch(Protocol):
    def suspend_persist(self) -> None: ...
    async def resume_persist(self) -> None: ...


def checkpoint_wal(path: Path, *, busy_timeout_ms: int = _BUSY_TIMEOUT_MS) -> bool:
    """True when the WAL of ``path`` is empty afterwards, or the file is not in WAL mode.

    ``PRAGMA wal_checkpoint(TRUNCATE)`` copies every frame of the log into the
    database file and cuts the log to zero bytes, but only once no writer is at
    work and every reader has finished with the log. Its answer row is
    ``(busy, log, checkpointed)``: busy 1 means it could not complete, log -1
    means the file runs a rollback journal (the NFS fallback of enable_wal), and
    then there is no log to empty. Both busy 0 and log -1 are a success.

    A file that does not exist is a success as well and is not created: an
    instance without semantic search has no vectors.db. The connection is a
    plain read-write one, because the checkpoint writes the main file, and it is
    closed in every case. Synchronous; the coordinator runs it in a thread.
    """
    if not path.is_file():
        return True
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(path, autocommit=True, check_same_thread=False)
        connection.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
        row = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    except sqlite3.Error as error:
        LOGGER.warning("backup pause: a checkpoint failed, %s", type(error).__name__)
        return False
    finally:
        if connection is not None:
            connection.close()
    if row is None:
        return False
    busy, log, _ = row
    return busy == 0 or log == -1


async def _never() -> None:
    return None


class PauseCoordinator:
    """Turn the wish of the admin into held writers and a copyable volume.

    The lifespan builds one per process and attaches every writer before it
    starts that writer's task; an attached writer is held at once unless the
    coordinator is already ``running`` (D-41-19). A part that was never
    attached, say no embed runner on an instance without semantic search,
    counts as resting.

    **A failed read in the running state does not stop the indexing.** D-41-19
    is about the restart: before the first answer nothing may run. Once a wish
    was read, the last one read stays in force, and a companion that does not
    answer for one read leaves a running instance running and a paused one
    paused. Turning a passing hiccup of Nextcloud into a halted index would be
    a failure of its own.
    """

    def __init__(
        self,
        *,
        read_wish: WishReader,
        databases: Sequence[Path],
        rebuild_busy: Callable[[], bool] = lambda: False,
        probe_busy: Callable[[], bool] = lambda: False,
        on_resume: Callable[[], Awaitable[None]] | None = None,
        clock: Clock = time.time,
        checkpoint: Checkpoint = checkpoint_wal,
        poll_seconds: float = PAUSE_POLL_SECONDS,
        settle_seconds: float = PAUSE_SETTLE_SECONDS,
    ) -> None:
        self._read_wish = read_wish
        self._databases = tuple(databases)
        self._rebuild_busy = rebuild_busy
        self._probe_busy = probe_busy
        self._on_resume = on_resume or _never
        self._clock = clock
        self._checkpoint = checkpoint
        self._poll = poll_seconds
        self._settle_every = settle_seconds
        self._state: PauseState = PAUSE_UNKNOWN
        self._paused_since: int | None = None
        # Whether the poller gave its writer back on this entry into pausing,
        # so a busy checkpoint retries without a second quiesce.
        self._quiesced = False
        self._pollers: list[_Poller] = []
        self._runners: list[_Runner] = []
        self._reconciles: list[_Reconcile] = []
        self._watches: list[_GuardWatch] = []

    # -- what the rest of the process reads ---------------------------------

    @property
    def state(self) -> PauseState:
        """One of running, pausing, paused, unknown."""
        return self._state

    @property
    def paused_since(self) -> int | None:
        """Epoch seconds of the moment "paused" was reached, None otherwise."""
        return self._paused_since

    def wants_pause(self) -> bool:
        """True while the writers are to stand still: pausing, paused or unknown.

        The rebuild asks this in its ``should_stop`` (D-41-20), so a band run
        ends between two bands instead of writing through a backup.
        """
        return self._state != PAUSE_RUNNING

    # -- attaching the writers ------------------------------------------------

    def _held(self) -> bool:
        return self._state != PAUSE_RUNNING

    def attach_poller(self, poller: _Poller) -> None:
        """Know the indexing loop; held at once unless the state is running."""
        self._pollers.append(poller)
        if self._held():
            poller.hold_for_backup()

    def attach_runner(self, runner: _Runner) -> None:
        """Know the embed runner; held at once unless the state is running."""
        self._runners.append(runner)
        if self._held():
            runner.hold_for_backup()

    def attach_reconcile(self, reconcile: _Reconcile) -> None:
        """Know a reconcile task, the ordinary one or the catch-up; held at once unless running."""
        self._reconciles.append(reconcile)
        if self._held():
            reconcile.hold_for_backup()

    def attach_guard_watch(self, watch: _GuardWatch) -> None:
        """Know the memory guard watch; its writes wait unless the state is running."""
        self._watches.append(watch)
        if self._held():
            watch.suspend_persist()

    # -- the loop ---------------------------------------------------------------

    async def run(self, stop_event: asyncio.Event) -> None:
        """Read the wish every poll interval, settle every second while pausing.

        A failing step is logged with its type name and never ends the task.
        """
        while not stop_event.is_set():
            try:
                await self.tick()
            # Deliberately every exception, the rule of the other workers.
            except Exception as error:
                LOGGER.error("backup pause: a step ended in an unexpected %s", type(error).__name__)
            deadline = time.monotonic() + self._poll
            while self._state == PAUSE_PAUSING and not stop_event.is_set():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                await _wait(stop_event, min(self._settle_every, remaining))
                try:
                    await self._settle()
                except Exception as error:
                    LOGGER.error("backup pause: a step ended in an unexpected %s", type(error).__name__)
            if self._state != PAUSE_PAUSING:
                await _wait(stop_event, max(0.0, deadline - time.monotonic()))

    async def tick(self) -> None:
        """One step: read the wish, act on it, and settle once while pausing."""
        wish = await self._read()
        if wish is False and self._state != PAUSE_RUNNING:
            await self._resume()
        elif wish is True and self._state in (PAUSE_RUNNING, PAUSE_UNKNOWN):
            self._enter_pausing()
        if self._state == PAUSE_PAUSING:
            await self._settle()

    async def _read(self) -> bool | None:
        try:
            return await self._read_wish()
        # Any failure of the read is no answer, which holds a waiting start and
        # changes nothing otherwise.
        except Exception as error:
            LOGGER.warning("backup pause: the wish could not be read, %s", type(error).__name__)
            return None

    # -- the transitions ----------------------------------------------------------

    def _hold_all(self) -> None:
        for poller in self._pollers:
            poller.hold_for_backup()
        for runner in self._runners:
            runner.hold_for_backup()
        for reconcile in self._reconciles:
            reconcile.hold_for_backup()
        for watch in self._watches:
            watch.suspend_persist()

    def _enter_pausing(self) -> None:
        self._hold_all()
        self._quiesced = False
        self._paused_since = None
        self._state = PAUSE_PAUSING
        LOGGER.info("backup pause: pausing")

    def _writers_rest(self) -> bool:
        """True when no writer is inside a pass, a round, a slice, a band or a pre-check."""
        if any(poller.pass_in_flight for poller in self._pollers):
            return False
        if not all(runner.parked.is_set() for runner in self._runners):
            return False
        if any(reconcile.in_flight for reconcile in self._reconciles):
            return False
        return not (self._rebuild_busy() or self._probe_busy())

    async def _settle(self) -> None:
        """Give the writer back once the batch ended, checkpoint, and say paused on success."""
        if self._state != PAUSE_PAUSING or not self._writers_rest():
            return
        if not self._quiesced:
            for poller in self._pollers:
                await poller.quiesce_for_backup()
            self._quiesced = True
        results = [await asyncio.to_thread(self._checkpoint, path) for path in self._databases]
        if not all(results):
            # Stay pausing; the next settle tries again. A reader of the search
            # holds the log only for the length of one statement.
            return
        self._paused_since = int(self._clock())
        self._state = PAUSE_PAUSED
        LOGGER.info("backup pause: paused")

    async def _resume(self) -> None:
        """Lift every hold, open what the backup took away, and say running."""
        for poller in self._pollers:
            # Before the holds go: the runner may start before the next pass of
            # the poller and drives the same track. A failure here costs
            # nothing lasting: the next pass opens the track again in _open().
            try:
                await poller.reopen_after_backup()
            except Exception as error:
                LOGGER.warning("backup pause: the track could not be opened again, %s", type(error).__name__)
        for poller in self._pollers:
            poller.release_backup_hold()
        for runner in self._runners:
            runner.release_backup_hold()
        for reconcile in self._reconciles:
            reconcile.release_backup_hold()
        self._state = PAUSE_RUNNING
        self._paused_since = None
        self._quiesced = False
        LOGGER.info("backup pause: running")
        for watch in self._watches:
            await watch.resume_persist()
        await self._on_resume()


# The coordinator of the running lifespan, published for the status route
# (D-41-06). The route lives in the API package and the coordinator in the
# lifespan of main, and main imports the routes; one module value here is what
# lets the route read the state without an import cycle. None outside a
# lifespan, which reads as "running": a process without a coordinator holds
# nothing.
_ACTIVE: PauseCoordinator | None = None


def publish(coordinator: PauseCoordinator | None) -> None:
    """Make ``coordinator`` the one the status route reads; None at the end of a lifespan."""
    global _ACTIVE
    _ACTIVE = coordinator


def pause_state() -> tuple[PauseState, int | None]:
    """The state word and, only while paused, the epoch second it was reached."""
    coordinator = _ACTIVE
    if coordinator is None:
        return (PAUSE_RUNNING, None)
    state = coordinator.state
    return (state, coordinator.paused_since if state == PAUSE_PAUSED else None)


async def _wait(stop_event: asyncio.Event, seconds: float) -> None:
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)


__all__ = [
    "PAUSE_PAUSED",
    "PAUSE_PAUSING",
    "PAUSE_POLL_SECONDS",
    "PAUSE_RUNNING",
    "PAUSE_SETTLE_SECONDS",
    "PAUSE_UNKNOWN",
    "PauseCoordinator",
    "PauseState",
    "checkpoint_wal",
    "pause_state",
    "publish",
]
