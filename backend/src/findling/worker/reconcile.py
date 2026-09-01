"""The ETag reconcile: read the file list, compare, turn differences into work.

Three statements belong at the top of this file, because none of them can be
reconstructed from the code once they are gone.

**Why this exists at all.** Events are an accelerator, never a guarantee. A mass
import over ``occ``, a restore from a backup, a listener that was switched off, a
dispatcher that dropped a message: in every one of these cases nothing arrives,
and without a comparison the index stays wrong forever with no counter anywhere
moving. That is not a hypothetical. It is the failure class the predecessor of
this app died of, and it died of it quietly, which is what made it fatal. So this
round exists to be able to say: after one full cycle the index is correct even if
not a single event was ever delivered (D-02).

**Why the bookmark lives here and not in Nextcloud.** Everywhere else in this
project, progress lives in the database of Nextcloud, because a lost crawl
position is a document nobody ever indexes. This module is the one deliberate
exception to that rule. The reconcile is pure, idempotent repair: it reads,
compares and proposes work, and running it twice over the same mount produces the
same result as running it once. A lost bookmark therefore costs a repetition and
never work, which is the whole justification, and it is written down here so that
it does not later read like an oversight.

**Why nothing here writes the index.** There is exactly one index writer in the
process and it belongs to the poller; a second one is a tantivy lock conflict
that would stop the indexing task outright (T-03-1203). This round therefore
never touches the index. It hands file ids to the queue, as content jobs for what
changed and as delete jobs for what is gone, and the branches of the poller do
the work. The side effect is the one worth having: the deletion path exists once
instead of twice.

**The cadence is ours, not Nextcloud's.** A PHP background job could not wake
this container, and D-01 forbids a second wake channel, so the tick is here: at
most one full cycle per ``FINDLING_RECONCILE_MIN_INTERVAL_HOURS``, preferably in
the hour ``FINDLING_RECONCILE_HOUR``, and only while the queue is quiet (D-03).
The maintenance window of Nextcloud is not a substitute and cannot be relied on;
``docs/reconcile.md`` carries that argument together with the numbers.

**The log carries counters and nothing else.** Not a single field of the file
list reaches it (T-03-1205), and a test greps for that, because this is a rule
that gets broken while adding a helpful detail rather than on purpose.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any, Final

from findling.config import settings
from findling.nc import client as nc_client
from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import FileList, FileRow, Mount
from findling.nc.queue import KIND_CONTENT, KIND_DELETE, DocumentQueue
from findling.store.repo import Store, open_store

LOGGER = logging.getLogger("findling.worker.reconcile")

# What one round came to. Strings rather than an enum for the same reason as in
# the poller: they travel to the status page of phase 4, where a closed list of
# readable names is worth more than a type.
ROUND_WALKED: Final = "walked"
ROUND_NOT_DUE: Final = "not_due"
ROUND_QUEUE_BUSY: Final = "queue_busy"
ROUND_QUEUE_UNAVAILABLE: Final = "queue_unavailable"
ROUND_UNAVAILABLE: Final = "unavailable"
ROUND_NO_STATE: Final = "no_state"

# How long the shutdown waits for a round to end before it stops waiting. Same
# budget as the poller, and for the same reason: a slice is bounded work.
RECONCILE_STOP_SECONDS: Final = 30.0

# How often the loop asks whether a cycle is due. It is not the cadence: the
# cadence is decided against the stamps in the reconcile table. This is only how
# finely the container notices that the configured hour has arrived.
RECONCILE_TICK_SECONDS: Final = 300.0

# Breather between two slices of the same mount. It is what makes the round
# bearable at midday, which is the point of pitfall 5: a reconcile that is only
# tolerable at night is a reconcile an admin switches off.
SLICE_PAUSE_SECONDS: Final = 1.0

# How many file ids one requeue call may carry. The ceiling on the PHP side is
# QueueController::MAX_LIST_LENGTH, 256 since plan 03-14, and intList refuses a
# longer list outright with HTTP 400. A slice exceeds that easily: the default
# slice is 500, and the missing list of a final page is not bounded by the
# slice at all, because gone_in_range runs open ended over the rest of the
# mount there. Handing a slice over in one call therefore wedged the round for
# good (review finding CR-01): the controller answered 400, the round ended
# without moving the bookmark, and the next round read the same page and
# produced the same over-long list again, forever. 200 leaves headroom under
# the controller limit; a parity test in tests/test_reconcile.py reads the PHP
# constant and holds the two numbers together, the same way the allowlist
# parity gate does it.
REQUEUE_BAND: Final = 200

# Everything the round talks to, as a type. The defaults are the production
# wiring and a test replaces them one by one.
ClientFactory = Callable[[], AsyncNextcloudApp]
FileListFactory = Callable[[AsyncNextcloudApp], FileList]
QueueFactory = Callable[[AsyncNextcloudApp], DocumentQueue]
Clock = Callable[[], float]
HourOfDay = Callable[[], int]


@dataclass(frozen=True, slots=True)
class RoundResult:
    """What one round did, in a form the status page can render."""

    state: str
    mounts: int = 0
    seen: int = 0
    stale: int = 0
    missing: int = 0
    slices: int = 0


@dataclass(slots=True)
class _Tally:
    """The counters of a round while it is still running."""

    seen: int = 0
    stale: int = 0
    missing: int = 0
    slices: int = 0


def _local_hour() -> int:
    """The hour of the container clock, which is the only clock this round has."""
    return time.localtime().tm_hour


def _open_state() -> Store | None:
    """The state database of the running container, or None while there is none.

    Deliberately does not create it and deliberately seeds no version marks. Both
    of those belong to the poller: a state database created here would carry
    unknown analyzer marks forever, every answer would report a drift, and the
    alarm that mechanism exists for would become permanent noise (bug audit H1).

    None is a legitimate answer and not a failure. Without a state database this
    container knows no file, so there is nothing to compare and nothing that
    could be missing.
    """
    path = settings().state_db
    if not path.exists():
        return None
    return open_store(path)


class Reconcile:
    """The second asyncio task: repair, beside the poller and never in its way.

    ``run_once`` and ``run`` are separate for the same reason as in the poller.
    One round is testable without time, without a task and without a Nextcloud
    that keeps answering, and the acceptance criterion of IDX-04, one cycle and
    the index is correct, hangs off exactly that call.

    Nothing is opened in the constructor. The lifespan builds this object while
    the backend may still be disabled, and a container that opened a second write
    connection to the state database at that point would hold it without ever
    comparing anything.
    """

    def __init__(
        self,
        *,
        store: Store | None = None,
        client_factory: ClientFactory = nc_client.create_app_client,
        files_factory: FileListFactory = FileList,
        queue_factory: QueueFactory = DocumentQueue,
        slice_size: int | None = None,
        quiet_max: int | None = None,
        hour: int | None = None,
        min_interval_hours: int | None = None,
        pause_seconds: float = SLICE_PAUSE_SECONDS,
        tick_seconds: float = RECONCILE_TICK_SECONDS,
        clock: Clock = time.time,
        hour_of: HourOfDay = _local_hour,
    ) -> None:
        resolved = settings()
        self._store = store
        self._owns_store = store is None
        self._client_factory = client_factory
        self._files_factory = files_factory
        self._queue_factory = queue_factory
        self._slice = resolved.reconcile_slice if slice_size is None else slice_size
        self._quiet_max = resolved.reconcile_quiet_max if quiet_max is None else quiet_max
        self._hour = resolved.reconcile_hour if hour is None else hour
        self._min_interval = float(
            resolved.reconcile_min_interval_hours if min_interval_hours is None else min_interval_hours
        )
        self._pause = pause_seconds
        self._tick = tick_seconds
        self._clock = clock
        self._hour_of = hour_of

        self._client: AsyncNextcloudApp | None = None
        self._files: FileList | None = None
        self._queue: DocumentQueue | None = None
        self._cooldown = 0.0
        self._armed = asyncio.Event()

    # -- lifecycle -------------------------------------------------------

    @property
    def armed(self) -> bool:
        """True while the backend is enabled and the round may compare."""
        return self._armed.is_set()

    def arm(self) -> None:
        """Let the round compare again."""
        self._armed.set()

    def silence(self) -> None:
        """Stop comparing without ending the task.

        A disabled backend that keeps reading the file list is the same classic
        as an indexer that keeps polling: the container looks healthy in its own
        log while it works for an app the admin switched off.
        """
        self._armed.clear()

    async def aclose(self) -> None:
        """Give back the state connection, if this object opened one."""
        if not self._owns_store:
            return
        store, self._store = self._store, None
        if store is not None:
            store.close()

    # -- the loop --------------------------------------------------------

    async def run(self, stop_event: asyncio.Event) -> None:
        """Round after round until the stop event, silent while not armed.

        An exception inside a round is logged and does not end the task, and it
        does not touch the poller either. The search is the part a user sees, and
        a repair that failed must not take it along.
        """
        while not stop_event.is_set():
            if not self._armed.is_set():
                await _first_of(self._armed.wait(), stop_event.wait())
                continue
            try:
                await self.run_once()
            # Deliberately every exception, and only the type name is logged: a
            # traceback would carry whatever a library put into its message.
            except Exception as error:
                kind_of_failure = type(error).__name__
                LOGGER.error("reconcile round ended in an unexpected %s", kind_of_failure)
                self._back_off()
            await _pause(self._tick + self._cooldown, stop_event)

    async def run_once(self) -> RoundResult:
        """One round: the two gates, then mount by mount, slice by slice."""
        opened = self._open()
        if opened is None:
            # No state database, so this container knows no file. There is
            # nothing to compare and, more to the point, nothing that could be
            # missing from a page.
            return RoundResult(ROUND_NO_STATE)
        store, files, queue = opened

        # 1. The quiet gate (D-03), and it stands before everything that costs
        #    anything at all. An instance still working off its initial index or
        #    an OCR backlog must not also be walking its whole file list. Ending
        #    here costs nothing: not a single page has been asked for.
        gate = await self._quiet(queue)
        if gate is not None:
            return RoundResult(gate)

        # 2. The cadence, decided against our own clock and the stamps in the
        #    reconcile table, never against Nextcloud. An interrupted walk
        #    outranks the interval, because a round that was cut in half has to
        #    be finished rather than waited out for another day.
        if not await asyncio.to_thread(self._is_due, store):
            return RoundResult(ROUND_NOT_DUE)

        # 3. The mount list. Unreachable is not empty: an instance without a
        #    single mount is a fresh installation, an unreachable Nextcloud means
        #    this round knows nothing and must conclude nothing.
        found = await files.mounts()
        if found.unavailable:
            self._back_off()
            return RoundResult(ROUND_UNAVAILABLE)

        # 4. Mount by mount. Every early end carries its own state and leaves the
        #    bookmark where the last completed slice put it, so the next round
        #    picks up there instead of at the front.
        tally = _Tally()
        for mount in found.mounts:
            ended = await self._walk(store, files, queue, mount, tally)
            if ended is not None:
                return self._report(ended, len(found.mounts), tally)

        self._reset_cooldown()
        return self._report(ROUND_WALKED, len(found.mounts), tally)

    # -- one mount -------------------------------------------------------

    async def _walk(
        self,
        store: Store,
        files: FileList,
        queue: DocumentQueue,
        mount: Mount,
        tally: _Tally,
    ) -> str | None:
        """Walk one mount to its end. Returns a state when the round has to stop."""
        cursor = await asyncio.to_thread(store.reconcile_cursor, mount.storage_id)
        after = cursor.after_file_id

        while True:
            # The quiet gate again, before every single slice. A round that
            # started on a calm instance and ran into the working day stops here,
            # and it may stop here because everything before this point is either
            # durable or repeatable.
            gate = await self._quiet(queue)
            if gate is not None:
                return gate

            # The page itself. root is the overridden root of the mount, which is
            # the node the file query walks: for a home mount that is the files
            # folder, which is what keeps the trash bin out of the comparison.
            page = await files.page(
                storage=mount.storage_id,
                root=mount.overridden_root,
                after=after,
                limit=self._slice,
            )
            if page.unavailable:
                # A transport failure ends the round without moving the bookmark
                # (T-03-1201). Concluding anything from a page that never arrived
                # is how a reconcile empties an index.
                self._back_off()
                return ROUND_UNAVAILABLE

            tally.slices += 1
            tally.seen += len(page.files)
            upto = max((row.file_id for row in page.files), default=after)

            stale = await asyncio.to_thread(self._stale_of, store, page.files)
            missing = await asyncio.to_thread(self._missing_of, store, mount, after, upto, page)

            # The findings travel before the bookmark does. An abort in between
            # costs one repeated slice, while the reverse order would drop the
            # findings of this slice until the next full cycle, which on the
            # default cadence is a day of a stale index.
            if not await self._hand_over(queue, stale, missing):
                self._back_off()
                return ROUND_UNAVAILABLE
            tally.stale += len(stale)
            tally.missing += len(missing)

            if page.final:
                await asyncio.to_thread(
                    store.set_reconcile_cursor, mount.storage_id, 0, finished=True, at=int(self._clock())
                )
                return None

            if not page.files:
                # A page with no rows that does not claim to be final cannot be
                # walked past: the bookmark would not move and this loop would
                # never end. Ending the mount costs one repetition next cycle.
                LOGGER.warning("a page of the file list came back empty without being final, ending this mount")
                self._back_off()
                return ROUND_UNAVAILABLE

            await asyncio.to_thread(store.set_reconcile_cursor, mount.storage_id, upto, at=int(self._clock()))
            after = upto
            await asyncio.sleep(self._pause)

    @staticmethod
    def _stale_of(store: Store, rows: Sequence[FileRow]) -> list[int]:
        """The files of this page whose version mark this container cannot match.

        A file the store does not answer for is either unknown or carries a
        tombstone, and both are work: the second one is a restore, and a restore
        has exactly the bytes it always had, so it would never be noticed by a
        content comparison.
        """
        known = store.known_etags([row.file_id for row in rows])
        return [row.file_id for row in rows if known.get(row.file_id) != row.etag]

    @staticmethod
    def _missing_of(store: Store, mount: Mount, after: int, upto: int, page: Any) -> list[int]:
        """The files of this range the page does not carry, or nothing at all.

        ``complete`` is the veto and it is checked here rather than in the store,
        because it is a property of the answer and not of the database: a row the
        client had to refuse is missing from the page, and missing from the page
        is precisely the shape of a deletion (T-03-1201, and the contract stated
        in the module docstring of :mod:`findling.nc.files`).
        """
        if not page.complete:
            return []
        return store.gone_in_range(
            mount.storage_id,
            after,
            upto,
            final=page.final,
            present={row.file_id for row in page.files},
        )

    async def _hand_over(self, queue: DocumentQueue, stale: Sequence[int], missing: Sequence[int]) -> bool:
        """Turn the findings of one slice into queue rows. False means: stop.

        Two calls and never one, because the two kinds are two different jobs:
        content re-reads the file, and the delete branch of the poller takes the
        document out of the index, forgets the permissions and sets the
        tombstone. This round writes neither of those itself.

        Each list travels in bands of REQUEUE_BAND, below the list ceiling of
        the PHP controller; the reasoning stands at the constant. A band that
        fails ends the round exactly like a failed call did before, without
        moving the bookmark, and the bands already delivered are harmless: a
        repeated slice hands the same ids over again and requeueAs refreshes
        the rows rather than duplicating them.
        """
        for file_ids, kind in ((stale, KIND_CONTENT), (missing, KIND_DELETE)):
            for start in range(0, len(file_ids), REQUEUE_BAND):
                band = list(file_ids[start : start + REQUEUE_BAND])
                result = await queue.requeue(band, kind=kind)
                if not result.ok:
                    LOGGER.warning("could not hand %d files of kind %s to the queue, ending the round", len(band), kind)
                    return False
        return True

    # -- the two gates ---------------------------------------------------

    async def _quiet(self, queue: DocumentQueue) -> str | None:
        """None while the queue is calm enough, otherwise the state to report.

        An unreadable counter is not a quiet queue. Walking anyway would be the
        worst possible reading of "we do not know".
        """
        stats = await queue.stats()
        if not stats.ok:
            self._back_off()
            return ROUND_QUEUE_UNAVAILABLE
        if stats.scheduled >= self._quiet_max:
            LOGGER.info(
                "reconcile stands down, %d rows are scheduled and the quiet mark is %d",
                stats.scheduled,
                self._quiet_max,
            )
            return ROUND_QUEUE_BUSY
        return None

    def _is_due(self, store: Store) -> bool:
        """Whether a cycle may start now, against our own clock and the stamps.

        Three answers in order. An interrupted walk is always due, because a
        half-finished comparison is worth less than none at all. A container that
        never ran a cycle is due at once, and the quiet gate above is what keeps
        that from colliding with an initial index. Everything else waits out the
        minimum pause and then prefers the configured hour, with one escape: at
        twice the pause it runs whatever the hour is, because a box that is only
        switched on during the day must not lose the guarantee entirely.
        """
        state = store.reconcile_state()
        if state.unfinished:
            return True
        if state.last_finished_at is None:
            return True

        elapsed = self._clock() - state.last_finished_at
        interval = self._min_interval * 3600.0
        if elapsed < interval:
            return False
        if self._hour_of() == self._hour:
            return True
        return elapsed >= 2 * interval

    # -- plumbing --------------------------------------------------------

    def _open(self) -> tuple[Store, FileList, DocumentQueue] | None:
        """Build the client and the two shells exactly once, or report no state.

        One client for the whole round. A walk over a large instance is many
        pages, and a client per page would pay a connection setup plus, on the
        PHP side, a Nextcloud bootstrap including the signature check for every
        single one of them.
        """
        if self._store is None:
            self._store = _open_state()
        if self._store is None:
            return None
        if self._files is None or self._queue is None:
            self._client = self._client_factory()
            self._files = self._files_factory(self._client)
            self._queue = self._queue_factory(self._client)
        return self._store, self._files, self._queue

    @staticmethod
    def _report(state: str, mounts: int, tally: _Tally) -> RoundResult:
        """One log line of counters, and the same numbers as a result."""
        LOGGER.info(
            "reconcile round %s, mounts=%d slices=%d seen=%d stale=%d missing=%d",
            state,
            mounts,
            tally.slices,
            tally.seen,
            tally.stale,
            tally.missing,
        )
        return RoundResult(
            state,
            mounts=mounts,
            seen=tally.seen,
            stale=tally.stale,
            missing=tally.missing,
            slices=tally.slices,
        )

    def _back_off(self) -> None:
        """Grow the extra pause: one tick, doubling up to an hour."""
        self._cooldown = min(self._cooldown * 2, 3600.0) if self._cooldown else self._tick

    def _reset_cooldown(self) -> None:
        """A round that got through has no reason to wait longer than the tick."""
        self._cooldown = 0.0


def default_reconcile() -> Reconcile:
    """The reconcile of the running container; its resources open on the first round."""
    return Reconcile()


# The two helpers below are copies of the ones in worker/poller.py, and the copy
# is deliberate. They are private there, this module may not reach into the
# internals of a sibling, and making them public would be an edit to a module
# this plan does not own. Ten lines twice are cheaper than either.


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
    "RECONCILE_STOP_SECONDS",
    "REQUEUE_BAND",
    "ROUND_NOT_DUE",
    "ROUND_NO_STATE",
    "ROUND_QUEUE_BUSY",
    "ROUND_QUEUE_UNAVAILABLE",
    "ROUND_UNAVAILABLE",
    "ROUND_WALKED",
    "Reconcile",
    "RoundResult",
    "default_reconcile",
]
