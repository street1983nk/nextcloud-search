"""The document key of every row, filled in for the rows of before 1.6.3 (plan 43-16).

The coverage of 1.6.3 counts documents and not reader paths (D-43-14, issue
#25). A file that one user reads under Daten/x.pdf and another under
Shared/x.pdf, or that two mount points show twice, is one document, and the key
that says so is sha256 over the internal path of the file in the file cache.
The companion computes it (plan 43-15) and sends it with every job; this
container never hashes anything, it only keeps what arrives in the shape of 64
lower case hex digits (T-43-49).

The rows indexed before 1.6.3 have no key, about 190,000 of them on the
instance of issue #25, and this task asks the companion for them:

**Bounded.** One band of DOC_KEY_BAND file ids per request, at most
DOC_KEY_BACKFILL_BANDS_PER_ROUND bands per round, a pause between two bands
and one round per tick. A backup pause ends the round between two bands.

**Resumable.** The cursor lives in the meta value doc_key_backfill_after as
``<generation>:<cursor>:<verify>``, written after every band, so a restart goes
on where the last band ended. A full pass that still leaves rows without a key
(a row that arrived under the cursor later) goes back to the front (R2).

**Honest about missing answers.** A companion of 1.6.2 answers 404: one log
line per step of a cooldown that doubles up to an hour, and the first call of
the coverage route ends it, because only a 1.6.3 companion asks that (W3,
W11). An answer that leaves an asked id out is no answer: no sentinel, no
cursor step (W8). The third such answer for the same band bisects it, and an
id that stays unanswered alone is set aside with the sentinel '' so that the
coverage does not wait for it forever (W12, W15).

**Verified.** Once no row is missing a key the stored keys are asked again,
just as slowly, and a stale one is replaced: the key of a file renamed while a
1.6.2 companion was in place, or an empty one the companion knows by now (G1).
A full verify pass without a single correction rests for a day.

The task never reads the document queue, so a busy crawl does not hold it.
Every log line carries numbers only, never a path and never a key (T-43-52).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import threading
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any, Final

from findling.config import settings
from findling.nc import client as nc_client
from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import DOC_KEY_BAND, DocKeyAnswer, FileList
from findling.store.repo import DOC_KEY_NONE, Store, open_store

LOGGER = logging.getLogger("findling.worker.doc_keys")

# The meta key of the cursor, the one meta key plan 43-16 adds (STOPP rule of
# phase 43). Its value is ``<generation>:<cursor>:<verify>``, where verify is
# the cursor of the verify pass or ``idle<epoch seconds>`` while it rests. The
# older two part form ``<generation>:<cursor>`` is read with a verify cursor of
# zero and written back in three parts.
DOC_KEY_MARK: Final = "doc_key_backfill_after"

# Bands per round and the pause between two of them. 25 bands of 200 are 5,000
# rows per round, and one round per tick of 300 s puts 190,000 rows at about
# 38 rounds, a little over three hours, with the companion answering one short
# file cache query per band.
DOC_KEY_BACKFILL_BANDS_PER_ROUND: Final = 25
DOC_KEY_BACKFILL_PAUSE_SECONDS: Final = 1.0
DOC_KEY_TICK_SECONDS: Final = 300.0

# The format of the key, and only that. A different stored generation, or none
# (every database of before 1.6.3), forgets every key once and builds them
# again. It is raised on a deliberate change of what the companion hashes and
# never for anything else; a way back to 1.6.2 does not touch the value at all,
# which is why the verify pass exists (G1).
DOC_KEY_GENERATION: Final = 1

# How often the same band may come back incomplete before it is bisected (W12).
DOC_KEY_INCOMPLETE_RETRIES: Final = 3

# The cooldown after a 404 of a companion without the route (W3).
DOC_KEY_COOLDOWN_START_SECONDS: Final = 300.0
DOC_KEY_COOLDOWN_MAX_SECONDS: Final = 3_600.0

# The rest of the verify pass after a full pass without a correction, within one
# running process: a new process verifies at once (plan 43-07, G1).
DOC_KEY_VERIFY_REST_SECONDS: Final = 86_400

_IDLE: Final = "idle"

# How many incomplete band counters are kept before they are dropped. A band
# that completes drops its own; this only bounds a pathological companion.
_INCOMPLETE_KEEP: Final = 1_000

ROUND_NO_STATE: Final = "no_state"
ROUND_HELD: Final = "held"
ROUND_WAITING: Final = "waiting"
ROUND_UNAVAILABLE: Final = "unavailable"
ROUND_FILLED: Final = "filled"
ROUND_VERIFIED: Final = "verified"
ROUND_RESTING: Final = "resting"

ClientFactory = Callable[[], AsyncNextcloudApp]
FileListFactory = Callable[[AsyncNextcloudApp], FileList]
Clock = Callable[[], float]

# Set by the coverage route on every call (W11, plan 43-04): a companion that
# asks for the per document coverage is a 1.6.3 one, so the route exists now
# and the cooldown of a 404 may end at once. A threading event, because the
# route may run in a worker thread.
_COVERAGE_SEEN = threading.Event()

# Corrections of the verify pass since the start of this process, for the
# coverage route (docKeysCorrected).
_CORRECTED_TOTAL = [0]


def note_coverage_call() -> None:
    """Say that the companion called the coverage route; ends a 404 cooldown."""
    _COVERAGE_SEEN.set()


def doc_keys_corrected() -> int:
    """How many keys the verify pass replaced since this process started."""
    return _CORRECTED_TOTAL[0]


@dataclass(frozen=True, slots=True)
class DocKeyRound:
    """What one round did, numbers only."""

    state: str
    done: int = 0
    missing: int = 0
    unresolved: int = 0
    checked: int = 0
    corrected: int = 0


@dataclass(frozen=True, slots=True)
class _Mark:
    generation: int | None
    cursor: int = 0
    verify: int = 0
    idle_until: int | None = None

    def render(self) -> str:
        verify = f"{_IDLE}{self.idle_until}" if self.idle_until is not None else str(self.verify)
        return f"{DOC_KEY_GENERATION}:{self.cursor}:{verify}"


def _read_mark(value: str | None) -> _Mark:
    """The parts of the meta value; anything unreadable reads as no generation."""
    parts = (value or "").split(":")
    if len(parts) not in (2, 3) or not all(part.isdigit() for part in parts[:2]):
        return _Mark(generation=None)
    generation, cursor = int(parts[0]), int(parts[1])
    if len(parts) == 2:
        return _Mark(generation=generation, cursor=cursor)
    verify = parts[2]
    if verify.isdigit():
        return _Mark(generation=generation, cursor=cursor, verify=int(verify))
    if verify.startswith(_IDLE) and verify[len(_IDLE) :].isdigit():
        return _Mark(generation=generation, cursor=cursor, idle_until=int(verify[len(_IDLE) :]))
    return _Mark(generation=generation, cursor=cursor)


@dataclass(frozen=True, slots=True)
class _Resolved:
    """The usable part of one or more answers, plus the ids set aside."""

    keys: dict[int, str]
    absent: frozenset[int] = frozenset()
    set_aside: frozenset[int] = frozenset()

    @classmethod
    def of(cls, answer: DocKeyAnswer) -> _Resolved:
        return cls(keys=dict(answer.keys), absent=answer.absent)

    def merge(self, other: _Resolved) -> _Resolved:
        return _Resolved(
            keys={**self.keys, **other.keys},
            absent=self.absent | other.absent,
            set_aside=self.set_aside | other.set_aside,
        )


def _open_state() -> Store | None:
    """The state database, or None while there is none; never created here.

    Same rule as the reconcile: only the poller creates and seeds it.
    """
    path = settings().state_db
    if not path.exists():
        return None
    return open_store(path)


class DocKeyBackfill:
    """The background task that keeps a document key on every living row.

    Built like the reconcile so that the lifespan, the enable and the backup
    pause treat it like one: armed and silenced with the others, held by the
    pause coordinator through hold_for_backup, and ``in_flight`` while a round
    runs. Nothing is opened in the constructor.
    """

    def __init__(
        self,
        *,
        store: Store | None = None,
        client_factory: ClientFactory = nc_client.create_app_client,
        files_factory: FileListFactory = FileList,
        bands_per_round: int = DOC_KEY_BACKFILL_BANDS_PER_ROUND,
        pause_seconds: float = DOC_KEY_BACKFILL_PAUSE_SECONDS,
        tick_seconds: float = DOC_KEY_TICK_SECONDS,
        clock: Clock = time.time,
    ) -> None:
        self._store = store
        self._owns_store = store is None
        self._client_factory = client_factory
        self._files_factory = files_factory
        self._files: FileList | None = None
        self._bands = max(1, bands_per_round)
        self._pause = pause_seconds
        self._tick = tick_seconds
        self._clock = clock
        self._armed = asyncio.Event()
        self._backup_release = asyncio.Event()
        self._backup_release.set()
        self._in_flight = False
        self._cooldown = 0.0
        self._retry_at: float | None = None
        self._incomplete: dict[tuple[int, ...], int] = {}
        self._pass_corrected = False
        self._corrected = 0
        # The rest after a clean verify pass belongs to one running process. A
        # stored rest is read as nothing on the first round of a new process,
        # because a process start is exactly when keys may have gone stale
        # behind this container: a rollback to 1.6.2 keeps the meta value and
        # renames files without a key (plan 43-07, G1 of plan 43-16).
        self._stored_rest_checked = False

    # -- lifecycle -------------------------------------------------------

    def arm(self) -> None:
        """Let the rounds run."""
        self._armed.set()

    def silence(self) -> None:
        """Stop asking without ending the task (the backend was disabled)."""
        self._armed.clear()

    def hold_for_backup(self) -> None:
        """Start no further band; the round in flight ends after its band (issue #37)."""
        self._backup_release.clear()

    def release_backup_hold(self) -> None:
        """Let the rounds go on. Arms nothing."""
        self._backup_release.set()

    @property
    def backup_held(self) -> bool:
        """True while a backup pause holds this task."""
        return not self._backup_release.is_set()

    @property
    def in_flight(self) -> bool:
        """True while a round runs; the pause coordinator waits for it to drop."""
        return self._in_flight

    @property
    def corrected(self) -> int:
        """Keys the verify pass of this object replaced."""
        return self._corrected

    @property
    def retry_at(self) -> float:
        """When a companion without the route is asked again, 0 while none waits."""
        return 0.0 if self._retry_at is None else self._retry_at

    async def aclose(self) -> None:
        """Give back the state connection, if this object opened one."""
        if not self._owns_store:
            return
        store, self._store = self._store, None
        if store is not None:
            store.close()

    # -- the loop --------------------------------------------------------

    async def run(self, stop_event: asyncio.Event) -> None:
        """Round after round until the stop event, silent while not armed or held."""
        while not stop_event.is_set():
            if not self._armed.is_set():
                await _first_of(self._armed.wait(), stop_event.wait())
                continue
            if not self._backup_release.is_set():
                await _first_of(self._backup_release.wait(), stop_event.wait())
                continue
            try:
                await self.run_once()
            # Every exception, the type name only: a message may carry a path.
            except Exception as error:
                LOGGER.error("doc key round ended in an unexpected %s", type(error).__name__)
            await _pause(self._tick, stop_event)

    async def run_once(self) -> DocKeyRound:
        """One round: the backfill while rows miss a key, the verify pass otherwise."""
        if self.backup_held:
            return DocKeyRound(ROUND_HELD)
        self._in_flight = True
        try:
            return await self._round()
        finally:
            self._in_flight = False

    async def _round(self) -> DocKeyRound:
        if self._store is None:
            self._store = await asyncio.to_thread(_open_state)
        store = self._store
        if store is None:
            return DocKeyRound(ROUND_NO_STATE)
        if self._files is None:
            self._files = self._files_factory(self._client_factory())
        files = self._files

        now = self._clock()
        if self._retry_at is not None:
            if _COVERAGE_SEEN.is_set():
                _COVERAGE_SEEN.clear()
                self._retry_at = None
                self._cooldown = 0.0
            elif now < self._retry_at:
                return DocKeyRound(ROUND_WAITING)

        mark = _read_mark((await asyncio.to_thread(store.read_meta)).get(DOC_KEY_MARK))
        if mark.generation != DOC_KEY_GENERATION:
            await asyncio.to_thread(store.reset_doc_keys)
            mark = _Mark(generation=DOC_KEY_GENERATION)
            await asyncio.to_thread(store.write_meta, DOC_KEY_MARK, mark.render())

        if not self._stored_rest_checked:
            self._stored_rest_checked = True
            if mark.idle_until is not None:
                await self._write_mark(store, mark, verify=0)
                mark = _Mark(generation=DOC_KEY_GENERATION, cursor=mark.cursor)

        if await asyncio.to_thread(store.doc_keys_missing) > 0:
            return await self._backfill(store, files, mark)
        return await self._verify(store, files, mark, now)

    # -- the backfill ----------------------------------------------------

    async def _backfill(self, store: Store, files: FileList, mark: _Mark) -> DocKeyRound:
        cursor = mark.cursor
        done = 0
        asked = 0
        rewound = False
        state = ROUND_FILLED
        while asked < self._bands:
            if asked:
                await asyncio.sleep(self._pause)
            if self.backup_held:
                state = ROUND_HELD
                break
            ids = await asyncio.to_thread(store.missing_doc_keys, after=cursor, limit=DOC_KEY_BAND)
            if not ids:
                if cursor == 0 or rewound:
                    break
                # A full pass behind us and rows still without a key: they
                # arrived under the cursor, so back to the front (R2).
                cursor, rewound = 0, True
                await self._write_mark(store, mark, cursor=cursor)
                continue
            resolved = await self._resolve(files, ids)
            asked += 1
            if isinstance(resolved, str):
                state = resolved
                break
            await asyncio.to_thread(store.set_doc_keys, resolved.keys, resolved.absent | resolved.set_aside)
            if resolved.set_aside:
                LOGGER.warning("doc key backfill set aside %d ids that stayed unanswered", len(resolved.set_aside))
            done += len(ids)
            cursor = ids[-1]
            await self._write_mark(store, mark, cursor=cursor)

        missing = await asyncio.to_thread(store.doc_keys_missing)
        unresolved = await asyncio.to_thread(store.doc_keys_unresolved)
        if state != ROUND_WAITING:
            LOGGER.info("doc key backfill, done=%d missing=%d unresolved=%d", done, missing, unresolved)
        return DocKeyRound(state, done=done, missing=missing, unresolved=unresolved)

    # -- the verify pass ---------------------------------------------------

    async def _verify(self, store: Store, files: FileList, mark: _Mark, now: float) -> DocKeyRound:
        if mark.idle_until is not None and now < mark.idle_until:
            return DocKeyRound(ROUND_RESTING)
        cursor = 0 if mark.idle_until is not None else mark.verify
        checked = 0
        corrected = 0
        asked = 0
        finished = False
        state = ROUND_VERIFIED
        while asked < self._bands:
            if asked:
                await asyncio.sleep(self._pause)
            if self.backup_held:
                state = ROUND_HELD
                break
            rows = await asyncio.to_thread(store.existing_doc_keys, after=cursor, limit=DOC_KEY_BAND)
            if not rows:
                finished = True
                break
            ids = [file_id for file_id, _ in rows]
            resolved = await self._resolve(files, ids)
            asked += 1
            if isinstance(resolved, str):
                state = resolved
                break
            stored = dict(rows)
            changed = {file_id: key for file_id, key in resolved.keys.items() if stored.get(file_id) != key}
            gone = [file_id for file_id in resolved.absent if stored.get(file_id) != DOC_KEY_NONE]
            # Ids set aside keep what they have: a key is not dropped because
            # the companion could not name it this time.
            await asyncio.to_thread(store.set_doc_keys, changed, gone)
            corrected += len(changed) + len(gone)
            checked += len(ids)
            cursor = ids[-1]
            if len(rows) < DOC_KEY_BAND:
                finished = True
                break
            await self._write_mark(store, mark, verify=cursor)

        self._pass_corrected = self._pass_corrected or corrected > 0
        if finished:
            if self._pass_corrected:
                await self._write_mark(store, mark, verify=0)
            else:
                await self._write_mark(store, mark, idle_until=int(now) + DOC_KEY_VERIFY_REST_SECONDS)
            self._pass_corrected = False
        self._corrected += corrected
        _CORRECTED_TOTAL[0] += corrected
        if state != ROUND_WAITING:
            LOGGER.info("doc key verify, checked=%d corrected=%d", checked, corrected)
        return DocKeyRound(state, checked=checked, corrected=corrected)

    # -- asking ----------------------------------------------------------

    async def _resolve(self, files: FileList, ids: Sequence[int]) -> _Resolved | str:
        """The answer for one band, or the state that ends the round.

        An incomplete answer ends the round as unavailable (W8). The third one
        for the same band bisects it at once (W12).
        """
        answer = await files.doc_keys(ids)
        if answer is None:
            return ROUND_UNAVAILABLE
        stop = self._stop_reason(answer)
        if stop is not None:
            return stop
        band = tuple(ids)
        if answer.complete:
            self._incomplete.pop(band, None)
            return _Resolved.of(answer)
        seen = self._incomplete.get(band, 0) + 1
        if seen < DOC_KEY_INCOMPLETE_RETRIES:
            if len(self._incomplete) >= _INCOMPLETE_KEEP:
                self._incomplete.clear()
            self._incomplete[band] = seen
            return ROUND_UNAVAILABLE
        self._incomplete.pop(band, None)
        if len(ids) == 1:
            return _Resolved(keys={}, set_aside=frozenset(ids))
        middle = len(ids) // 2
        left = await self._bisect(files, ids[:middle])
        if isinstance(left, str):
            return left
        right = await self._bisect(files, ids[middle:])
        if isinstance(right, str):
            return right
        return left.merge(right)

    async def _bisect(self, files: FileList, ids: Sequence[int]) -> _Resolved | str:
        """Ask a part of a band that stayed incomplete; halve again until single ids."""
        if self.backup_held:
            return ROUND_HELD
        answer = await files.doc_keys(ids)
        if answer is None:
            return ROUND_UNAVAILABLE
        stop = self._stop_reason(answer)
        if stop is not None:
            return stop
        if answer.complete:
            return _Resolved.of(answer)
        if len(ids) == 1:
            return _Resolved(keys={}, set_aside=frozenset(ids))
        middle = len(ids) // 2
        left = await self._bisect(files, ids[:middle])
        if isinstance(left, str):
            return left
        right = await self._bisect(files, ids[middle:])
        if isinstance(right, str):
            return right
        return left.merge(right)

    def _stop_reason(self, answer: DocKeyAnswer) -> str | None:
        """ROUND_WAITING for a 404, None to go on; a real answer ends any cooldown."""
        if answer.route_missing:
            self._wait_for_the_route()
            return ROUND_WAITING
        self._cooldown = 0.0
        self._retry_at = None
        return None

    def _wait_for_the_route(self) -> None:
        """Double the cooldown up to an hour; one log line per step (W3)."""
        before = self._cooldown
        self._cooldown = (
            DOC_KEY_COOLDOWN_START_SECONDS if before <= 0 else min(before * 2, DOC_KEY_COOLDOWN_MAX_SECONDS)
        )
        self._retry_at = self._clock() + self._cooldown
        # Only a coverage call after this 404 ends the cooldown (W11).
        _COVERAGE_SEEN.clear()
        if self._cooldown != before:
            LOGGER.info(
                "doc key backfill waits, the companion has no doc key route, next try in %d s", int(self._cooldown)
            )

    async def _write_mark(
        self,
        store: Store,
        mark: _Mark,
        *,
        cursor: int | None = None,
        verify: int | None = None,
        idle_until: int | None = None,
    ) -> None:
        """Write the meta value, reading the other parts back first."""
        current = _read_mark((await asyncio.to_thread(store.read_meta)).get(DOC_KEY_MARK))
        base = current if current.generation == DOC_KEY_GENERATION else mark
        updated = _Mark(
            generation=DOC_KEY_GENERATION,
            cursor=base.cursor if cursor is None else cursor,
            verify=base.verify if verify is None else verify,
            idle_until=idle_until if idle_until is not None else (None if verify is not None else base.idle_until),
        )
        await asyncio.to_thread(store.write_meta, DOC_KEY_MARK, updated.render())


async def _first_of(*waits: Awaitable[Any]) -> None:
    """Wait until the first of these finishes, then let the others go."""
    tasks = [asyncio.ensure_future(wait) for wait in waits]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def _pause(seconds: float, stop_event: asyncio.Event) -> None:
    """Wait out the pause, or return at once when the stop event arrives."""
    if seconds <= 0:
        await asyncio.sleep(0)
        return
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)


__all__ = [
    "DOC_KEY_BACKFILL_BANDS_PER_ROUND",
    "DOC_KEY_BACKFILL_PAUSE_SECONDS",
    "DOC_KEY_GENERATION",
    "DOC_KEY_INCOMPLETE_RETRIES",
    "DOC_KEY_MARK",
    "DocKeyBackfill",
    "DocKeyRound",
    "doc_keys_corrected",
    "note_coverage_call",
]
