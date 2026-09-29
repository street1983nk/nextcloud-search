"""The memory guard as a task of the lifespan: tick, escalation, persistence (PAR-03).

findling.guard decides without I/O; this module is the I/O around it. Every
GUARD_TICK_SECONDS it reads memory.events and the anon headroom of the cgroup,
takes the child kills the pool reported, and hands all three to
:class:`findling.guard.Escalation`. A cause at an effective level above economy
lowers the level by one (D-26-03, D-26-15, D-26-16); the cap goes into the meta
table of state.db and comes back at the next start, before the first pass of
the poller, so that a container killed for memory does not start into the same
kill again (D-26-01).

**Why max alone is no event (26-RESEARCH.md, Befund A).** The kernel counts
memory.events max before the reclaim, and the page cache of the memory mapped
index is charged to the cgroup, so max rises on a healthy box that merely reads
its index. A tick counts only when max rose AND the anon headroom is below the
reserve; two such ticks at least a minute apart inside ten minutes lower. A
rising oom_kill counter or a child kill the pool reports lowers at once.

**Who dies at a kill.** The OCR children carry a raised oom_score_adj, so the
kernel picks a child and not the main process; the pool sees the SIGKILL of a
child it did not send and reports it through guard.report_child_kill. That is
why the child kills reach this task and why a kill does not end the container.

**cgroup v1.** There is no memory.events there, the reader answers None, and
only the child kills and the unclean end remain as causes.

**The pass mark.** Before a pass with more than one slot the poller writes the
effective level into META_MULTI_SLOT_PASS and the chosen profile into
META_MULTI_SLOT_CHOSEN, and "" once the pass is through. A start that finds the
mark set died without SIGTERM inside such a pass: that is the unclean end, and
the level is lowered from the stored one. An ordered shutdown clears the mark
as its very first act (:meth:`GuardWatch.note_shutdown_begins`), because docker
sends SIGKILL after its stop budget while the lifespan still waits for the
pass, and an update must never read as an unclean end.

**The way back** is the admin alone (D-26-04): guard.note_confirmation lifts the
cap, and the next tick writes the empty values. The guard never raises by
itself, and in economy it only shows, it never lowers.

**The pre-check (D-27-15).** While findling.probe.measuring() and one tick
after it, a tick only moves the base of the escalation and drops the child
kills: the check drives memory on purpose, and its load is no pressure on the
profile. Not while it merely holds the indexing (review WR-09 of phase 27): its
pause waits up to PROBE_PAUSE_SECONDS for the regular pass, which still runs
with its slots, and a kill in that pass is real pressure.

House rules of the runner (findling/worker/embedding.py): nothing is opened in
the constructor, every reader and clock is injectable, every exception of a tick
is caught and logged with its type name only. State.db is reached through a
connection of its own with the busy timeout of open_store, never through the
connection of the poller, and it is never created here: that belongs to the
poller, which seeds the version marks. No line logs the token.
"""

import asyncio
import contextlib
import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

from findling import guard, memory_guard, probe, profile
from findling.config import GUARD_TICK_SECONDS, settings
from findling.profile import PROFILE_NAMES, Profile
from findling.store.repo import Store, open_store

LOGGER = logging.getLogger("findling.worker.watch")

Events = Callable[[], "dict[str, int] | None"]
Headroom = Callable[[], "int | None"]
Clock = Callable[[], float]


def _level(value: str | None) -> Profile | None:
    """A stored level name as a Profile, None for anything outside the closed set."""
    if value is None or value not in PROFILE_NAMES:
        return None
    return Profile(value)


def _meta_of(state: guard.GuardSnapshot) -> dict[str, str]:
    """The guard_* meta values of a guard state; empty strings without a cap."""
    if state.cap is None:
        return {
            guard.META_CAP: "",
            guard.META_CAUSE: "",
            guard.META_SINCE: "",
            guard.META_TOKEN: "",
            guard.META_CHOSEN: "",
        }
    return {
        guard.META_CAP: state.cap.value,
        guard.META_CAUSE: state.cause,
        guard.META_SINCE: "" if state.since is None else repr(state.since),
        guard.META_TOKEN: state.token,
        guard.META_CHOSEN: "" if state.chosen is None else state.chosen.value,
    }


class GuardWatch:
    """The memory guard task: restore at the start, a tick while it runs, a mark at the end.

    ``persist`` False keeps the guard in memory only; the lifespan passes it on
    a volume that belongs to another instance, whose state.db is not ours to
    read or write (DI-06.1-22).
    """

    def __init__(
        self,
        *,
        state_path: Path | None = None,
        events: Events = memory_guard.memory_events,
        headroom: Headroom = memory_guard.headroom_bytes,
        clock: Clock = time.monotonic,
        wall_clock: Clock = time.time,
        tick: float = GUARD_TICK_SECONDS,
        persist: bool = True,
    ) -> None:
        self._state_path = state_path
        self._events = events
        self._headroom = headroom
        self._clock = clock
        self._wall_clock = wall_clock
        self._tick = tick
        self._persist = persist
        self._escalation = guard.Escalation()
        self._store: Store | None = None
        # One connection, reached from worker threads one after another; the
        # lock keeps the shutdown mark and a tick write from meeting on it.
        self._store_lock = threading.Lock()
        # The guard revision state.db holds, so a tick writes only on a change.
        self._persisted_revision = guard.snapshot().revision
        # Whether the last tick ran while a pre-check held the indexing; the
        # first tick after it is suspended as well (D-27-15).
        self._probe_trailing = False

    # -- state.db --------------------------------------------------------

    def _path(self) -> Path:
        return self._state_path if self._state_path is not None else settings().state_db

    def _open(self) -> Store | None:
        """The own connection, opened at first need; None while there is no state.db."""
        if not self._persist:
            return None
        if self._store is None:
            path = self._path()
            if not path.exists():
                return None
            self._store = open_store(path)
        return self._store

    def _read_meta(self) -> dict[str, str]:
        with self._store_lock:
            store = self._open()
            return {} if store is None else store.read_meta()

    def _write_meta(self, values: dict[str, str]) -> bool:
        """Write the values; False when there is no state.db to write into."""
        with self._store_lock:
            store = self._open()
            if store is None:
                return False
            for key, value in values.items():
                store.write_meta(key, value)
            return True

    async def _persist_if_changed(self) -> None:
        state = guard.snapshot()
        if state.revision == self._persisted_revision:
            return
        if await asyncio.to_thread(self._write_meta, _meta_of(state)):
            self._persisted_revision = state.revision

    # -- lifecycle -------------------------------------------------------

    async def restore(self) -> None:
        """Bring the cap of the last run back, and answer an unclean end (D-26-01, D-26-16).

        Runs before the first pass of the poller. Foreign values are dropped by
        guard.restore against its closed sets (T-26-34).
        """
        meta = await asyncio.to_thread(self._read_meta)
        if not meta:
            return
        guard.restore(
            meta.get(guard.META_CAP),
            meta.get(guard.META_CAUSE),
            meta.get(guard.META_SINCE),
            meta.get(guard.META_TOKEN),
            meta.get(guard.META_CHOSEN),
        )
        self._persisted_revision = guard.snapshot().revision
        stored = _level(meta.get(guard.META_MULTI_SLOT_PASS))
        if stored is not None and stored is not Profile.ECONOMY:
            chosen = _level(meta.get(guard.META_MULTI_SLOT_CHOSEN))
            if guard.lower(guard.CAUSE_UNCLEAN_END, now=self._wall_clock(), chosen=chosen, effective=stored):
                self._log_lowered()
        if meta.get(guard.META_MULTI_SLOT_PASS, "") or meta.get(guard.META_MULTI_SLOT_CHOSEN, ""):
            # Both keys, PASS first (the dict keeps its order): a choice that
            # lost its pass mark to a crash between the two writes is swept
            # here, so it can never sit beside the mark of a later staffel run
            # under another profile (review WR-02, D-26-04).
            await asyncio.to_thread(
                self._write_meta, {guard.META_MULTI_SLOT_PASS: "", guard.META_MULTI_SLOT_CHOSEN: ""}
            )
        await self._persist_if_changed()

    async def run_once(self) -> str:
        """One tick: read, escalate, lower above economy, persist a change. Returns the cause."""
        events = await asyncio.to_thread(self._events)
        headroom = await asyncio.to_thread(self._headroom)
        held = probe.measuring()
        if held or self._probe_trailing:
            # D-27-15, 27-RESEARCH.md Pitfall 3: the pre-check drives memory on
            # purpose, and a probe child the kernel kills must not lower the
            # profile the admin is choosing; the check reports that kill itself
            # as slot_killed. So the base moves on and the kills are dropped,
            # during the hold and one tick after it, because the kernel reports
            # an event late. The slot throttle lives in the poller and stays.
            self._escalation.rebase(events)
            guard.take_child_kills()
            self._probe_trailing = held
            LOGGER.debug("memory guard suspended its lowering for the pre-check")
            await self._persist_if_changed()
            return guard.CAUSE_NONE
        cause = self._escalation.observe(self._clock(), events, headroom, guard.take_child_kills())
        if cause:
            state = profile.snapshot()
            if state.effective is Profile.ECONOMY:
                # Economy is the floor: the guard shows, it does not lower.
                LOGGER.debug("memory guard saw pressure at economy, cause=%s", cause)
            elif guard.lower(cause, now=self._wall_clock(), chosen=state.chosen, effective=state.effective):
                self._log_lowered()
        await self._persist_if_changed()
        return cause

    async def run(self, stop_event: asyncio.Event) -> None:
        """Tick after tick until the stop event; a failing tick never ends the task."""
        while not stop_event.is_set():
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            # Deliberately every exception, the rule of the runner: a broken
            # tick costs one reading and never the search or the indexing.
            except Exception as error:
                LOGGER.error("a tick of the memory guard ended in an unexpected %s", type(error).__name__)
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop_event.wait(), timeout=self._tick)

    async def note_shutdown_begins(self) -> None:
        """Clear the pass mark: an ordered shutdown is never an unclean end (Pitfall 9).

        Both keys go, PASS first, the same order the poller clears with: a
        death between the two deletes leaves a choice without a mark, never
        the reverse (review WR-02).
        """
        try:
            await asyncio.to_thread(
                self._write_meta, {guard.META_MULTI_SLOT_PASS: "", guard.META_MULTI_SLOT_CHOSEN: ""}
            )
        except Exception as error:
            LOGGER.warning("the pass mark of the memory guard could not be cleared, %s", type(error).__name__)

    async def aclose(self) -> None:
        """Let go of the own connection. Idempotent."""
        with self._store_lock:
            store, self._store = self._store, None
        if store is not None:
            store.close()

    @staticmethod
    def _log_lowered() -> None:
        state = guard.snapshot()
        level = "" if state.cap is None else state.cap.value
        LOGGER.warning("memory guard lowered the level, cause=%s level=%s", state.cause, level)


__all__ = ["GuardWatch"]
