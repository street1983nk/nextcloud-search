"""The storage sweep of the reconcile (plan 36-04, HART-06, M-32-02, plan 43-02).

Documents of a deleted user, of a removed external storage or of a provider the
admin switched off in Findling used to stay candidates for good: the reconcile
only ever walked the mounts the list carried, and a storage that is no longer
listed has no page that could say "gone". The sweep closes that, and every test
here holds one of its two sides.

*It deletes.* A storage Nextcloud deleted and a storage only a switched off
provider carries lose their documents in the same round (D-36-14); a storage
that merely stopped being listed loses them once its first absence is 30 days
old (D-36-05). Deleting means delete orders through the queue and nothing else,
because nothing in the reconcile writes the index.

*It never deletes from an unsure position.* An empty mount list, a refused
entry, an unreachable Nextcloud, a round that ended early and a failed storage
question all end without a single delete order. A listed control storage is
asserted to keep every document in every test (positive control).
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import re
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import FileRow, GoneResult, Mount, MountResult, SliceResult
from findling.nc.queue import KIND_DELETE, CallResult, QueueStats
from findling.store import repo as repo_module
from findling.store.repo import CATCHUP_MARK, CATCHUP_RECONCILE, RECHECK_MARK, FileMeta, Store, open_store
from findling.worker import reconcile as reconcile_module
from findling.worker.reconcile import (
    REQUEUE_BAND,
    ROUND_QUEUE_BUSY,
    ROUND_QUEUE_UNAVAILABLE,
    ROUND_UNAVAILABLE,
    ROUND_WALKED,
    VANISHED_STORAGE_GRACE_SECONDS,
    Reconcile,
)

DAY = 86_400
START = 1_800_000_000.0

# The control storage: listed in every round, its files on every page, and not
# a single one of them may ever reach a delete order.
CONTROL = 3
CONTROL_FILES = (1, 2)


class _Queue:
    """Records every requeue; answers not ok from the call number ``fail_at`` on.

    ``state`` is the answer of the quiet gate, calm by default; ``on_requeue``
    runs after every requeue, which is how a test lands a backup pause in the
    middle of a sweep.
    """

    def __init__(self, *, fail_at: int | None = None, state: QueueStats | None = None) -> None:
        self.requeues: list[tuple[list[int], str]] = []
        self.fail_at = fail_at
        self.state = state if state is not None else QueueStats(scheduled=0)
        self.on_requeue: Callable[[], None] | None = None

    async def requeue(self, file_ids: Sequence[int], *, kind: str) -> CallResult:
        self.requeues.append((list(file_ids), kind))
        if self.on_requeue is not None:
            self.on_requeue()
        if self.fail_at is not None and len(self.requeues) >= self.fail_at:
            return CallResult(ok=False)
        return CallResult(ok=True, count=len(file_ids))

    async def stats(self) -> QueueStats:
        return self.state

    def deleted(self) -> list[int]:
        return [file_id for band, kind in self.requeues for file_id in band if kind == KIND_DELETE]


class _Files:
    """A scripted mount list, one final page per mount, and a scripted storage answer."""

    def __init__(self, store: Store, listed: Sequence[int], answer: GoneResult | None = None) -> None:
        self._store = store
        self.listed = list(listed)
        self.answer: GoneResult | None = answer if answer is not None else GoneResult()
        self.discarded = 0
        self.unavailable = False
        self.page_unavailable = False
        self.asked: list[list[int]] = []
        # Every call in order: "mounts", "page" and "gone".
        self.events: list[str] = []

    @property
    def mount_calls(self) -> int:
        return self.events.count("mounts")

    @property
    def page_calls(self) -> int:
        return self.events.count("page")

    async def mounts(self) -> MountResult:
        self.events.append("mounts")
        if self.unavailable:
            return MountResult(unavailable=True)
        mounts = tuple(Mount(storage_id=s, root_id=s * 10, overridden_root=s * 10 + 1) for s in self.listed)
        return MountResult(mounts=mounts, discarded=self.discarded)

    async def page(self, *, storage: int, root: int, after: int, limit: int) -> SliceResult:
        del root, after, limit
        self.events.append("page")
        if self.page_unavailable:
            return SliceResult(unavailable=True)
        rows = tuple(
            FileRow(file_id=file_id, etag=f"e{file_id}", size=1024, mtime=1_700_000_000, mime="application/pdf")
            for file_id in self._store.living_file_ids(storage)
        )
        return SliceResult(files=rows, final=True)

    async def gone_storages(self, ids: Sequence[int]) -> GoneResult | None:
        self.events.append("gone")
        self.asked.append(list(ids))
        return self.answer


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    opened.write_meta(RECHECK_MARK, "done")
    _record_all(opened, CONTROL, CONTROL_FILES)
    yield opened
    opened.close()


def _record_all(store: Store, storage_id: int, file_ids: Sequence[int]) -> None:
    for file_id in file_ids:
        meta = FileMeta(
            storage_id=storage_id,
            root_id=storage_id * 10,
            path=f"files/akte-{file_id}.pdf",
            title=f"akte-{file_id}.pdf",
            mime="application/pdf",
            size=1024,
            mtime=1_700_000_000,
            etag=f"e{file_id}",
        )
        store.record(file_id, meta, "indexed")


def _reconcile(
    store: Store, files: _Files, queue: _Queue, clock: list[float], *, tick_seconds: float = 0.01
) -> Reconcile:
    return Reconcile(
        store=store,
        client_factory=lambda: cast("AsyncNextcloudApp", None),
        files_factory=lambda nc: cast("Any", files),
        queue_factory=lambda nc: cast("Any", queue),
        slice_size=500,
        quiet_max=100,
        hour=2,
        min_interval_hours=24,
        pause_seconds=0.0,
        tick_seconds=tick_seconds,
        clock=lambda: clock[0],
        hour_of=lambda: 2,
    )


def _rows(store: Store, table: str) -> list[int]:
    query = f"SELECT storage_id FROM {table} ORDER BY storage_id"  # noqa: S608 - fixed table names of this file
    return [int(row[0]) for row in store._conn.execute(query)]


def _stamp(store: Store, storage_id: int) -> int | None:
    row = store._conn.execute(
        "SELECT first_missing_at FROM vanished_storages WHERE storage_id = ?", (storage_id,)
    ).fetchone()
    return None if row is None else int(row[0])


def _control_kept(queue: _Queue) -> None:
    assert not set(queue.deleted()) & set(CONTROL_FILES)


async def test_a_deleted_storage_loses_its_documents_in_the_same_round(store: Store) -> None:
    _record_all(store, 14, (10, 11))
    store.set_reconcile_cursor(14, 0, finished=True, at=int(START) - DAY)
    store.record_mount(14, 140, 0, 2)
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    queue = _Queue()

    result = await _reconcile(store, files, queue, [START]).run_once()

    assert result.state == ROUND_WALKED
    assert queue.requeues == [([10, 11], KIND_DELETE)]
    assert files.asked == [[14]]
    assert 14 not in _rows(store, "reconcile")
    assert 14 not in _rows(store, "mounts")
    assert _rows(store, "vanished_storages") == []
    _control_kept(queue)


async def test_a_switched_off_storage_loses_its_documents_at_once_without_a_stamp(store: Store) -> None:
    _record_all(store, 9, (20, 21, 22))
    files = _Files(store, [CONTROL], GoneResult(deselected=frozenset({9})))
    queue = _Queue()

    await _reconcile(store, files, queue, [START]).run_once()

    assert queue.deleted() == [20, 21, 22]
    assert _stamp(store, 9) is None
    _control_kept(queue)


async def test_a_vanished_storage_keeps_its_documents_for_thirty_days(store: Store) -> None:
    _record_all(store, 7, (30, 31))
    files = _Files(store, [CONTROL])
    queue = _Queue()
    clock = [START]
    round_of = _reconcile(store, files, queue, clock)

    await round_of.run_once()
    assert _stamp(store, 7) == int(START)
    assert queue.deleted() == []

    clock[0] = START + 29 * DAY
    assert (await round_of.run_once()).state == ROUND_WALKED
    assert _stamp(store, 7) == int(START)
    assert queue.deleted() == []

    clock[0] = START + 31 * DAY
    assert (await round_of.run_once()).state == ROUND_WALKED
    assert queue.deleted() == [30, 31]
    assert _stamp(store, 7) is None
    _control_kept(queue)


async def test_the_grace_is_counted_from_the_stamp_and_a_backdated_stamp_is_due(store: Store) -> None:
    # The rehearsal of D-36-05 without waiting: the stamp moved back by 31 days
    # in SQL, and the next round sweeps.
    _record_all(store, 7, (30, 31))
    files = _Files(store, [CONTROL])
    queue = _Queue()
    clock = [START]
    round_of = _reconcile(store, files, queue, clock)
    await round_of.run_once()

    store._conn.execute(
        "UPDATE vanished_storages SET first_missing_at = first_missing_at - ? WHERE storage_id = 7",
        (31 * DAY,),
    )
    store._conn.commit()
    clock[0] = START + 2 * DAY
    await round_of.run_once()

    assert queue.deleted() == [30, 31]
    assert VANISHED_STORAGE_GRACE_SECONDS == 30 * DAY
    _control_kept(queue)


async def test_a_storage_that_comes_back_loses_its_stamp_and_a_new_absence_starts_over(store: Store) -> None:
    _record_all(store, 7, (30, 31))
    files = _Files(store, [CONTROL])
    queue = _Queue()
    clock = [START]
    round_of = _reconcile(store, files, queue, clock)
    await round_of.run_once()
    assert _stamp(store, 7) == int(START)

    clock[0] = START + 20 * DAY
    files.listed = [CONTROL, 7]
    await round_of.run_once()
    assert _stamp(store, 7) is None

    clock[0] = START + 40 * DAY
    files.listed = [CONTROL]
    await round_of.run_once()

    # 40 days after the first absence, but only the first round of the second.
    assert _stamp(store, 7) == int(START + 40 * DAY)
    assert queue.deleted() == []
    _control_kept(queue)


async def test_no_answer_to_the_storage_question_means_grace_and_never_a_delete(store: Store) -> None:
    # A 1.4.x companion answers 404, FileList turns that into None.
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL])
    files.answer = None
    queue = _Queue()

    await _reconcile(store, files, queue, [START]).run_once()

    assert queue.deleted() == []
    assert _stamp(store, 14) == int(START)
    _control_kept(queue)


@pytest.mark.parametrize("unsure", ["empty", "discarded", "unavailable"])
async def test_an_unsure_round_neither_deletes_nor_stamps(store: Store, unsure: str) -> None:
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    if unsure == "empty":
        files.listed = []
    elif unsure == "discarded":
        files.discarded = 1
    else:
        files.unavailable = True
    queue = _Queue()

    result = await _reconcile(store, files, queue, [START]).run_once()

    assert queue.deleted() == []
    assert files.asked == []
    assert _rows(store, "vanished_storages") == []
    if unsure == "unavailable":
        assert result.state == ROUND_UNAVAILABLE


async def test_a_failed_delete_order_keeps_the_bookmark_and_the_next_round_retries(store: Store) -> None:
    _record_all(store, 14, (10, 11))
    store.set_reconcile_cursor(14, 0, finished=True, at=int(START) - DAY)
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    failing = _Queue(fail_at=1)
    clock = [START]

    await _reconcile(store, files, failing, clock).run_once()

    assert failing.requeues == [([10, 11], KIND_DELETE)]
    assert 14 in _rows(store, "reconcile")

    clock[0] = START + 2 * DAY
    healthy = _Queue()
    await _reconcile(store, files, healthy, clock).run_once()

    assert healthy.deleted() == [10, 11]
    assert 14 not in _rows(store, "reconcile")
    _control_kept(failing)
    _control_kept(healthy)


async def test_a_large_storage_is_handed_over_in_bands(store: Store) -> None:
    ids = list(range(1000, 1000 + 2 * REQUEUE_BAND + 50))
    _record_all(store, 14, ids)
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    queue = _Queue()

    await _reconcile(store, files, queue, [START]).run_once()

    assert [len(band) for band, kind in queue.requeues if kind == KIND_DELETE] == [REQUEUE_BAND, REQUEUE_BAND, 50]
    assert queue.deleted() == ids
    _control_kept(queue)


async def test_a_storage_that_vanished_mid_walk_leaves_no_walk_open_for_good(store: Store) -> None:
    # F4: storage 9 vanished in the middle of its walk, its rows are long gone.
    store.set_reconcile_cursor(9, 4711, at=int(START) - DAY)
    assert store.reconcile_state().unfinished == 1
    files = _Files(store, [CONTROL])
    queue = _Queue()
    clock = [START]
    round_of = _reconcile(store, files, queue, clock)

    await round_of.run_once()

    assert store.reconcile_state().unfinished == 0
    assert 9 not in _rows(store, "reconcile")
    clock[0] = START + 60
    assert round_of._is_due(store) is False
    _control_kept(queue)


async def test_the_sweep_logs_counters_and_storage_ids_and_never_a_path(
    store: Store, caplog: pytest.LogCaptureFixture
) -> None:
    _record_all(store, 14, (10, 11))
    _record_all(store, 7, (31337,))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    queue = _Queue()

    with caplog.at_level(logging.INFO, logger="findling.worker.reconcile"):
        await _reconcile(store, files, queue, [START]).run_once()

    sweep = [record.getMessage() for record in caplog.records if "storage sweep" in record.getMessage()]
    assert len(sweep) == 1
    assert "gone=1" in sweep[0]
    assert "stamped=1" in sweep[0]
    assert "removed=1" in sweep[0]
    for record in caplog.records:
        message = record.getMessage()
        assert "akte-" not in message
        assert "files/" not in message
        assert "31337" not in message
    _control_kept(queue)


def test_the_grace_is_a_fixed_constant_and_no_setting() -> None:
    # D-36-05: fixed, no FINDLING_* switch anywhere in the package.
    assert "VANISHED_STORAGE_GRACE_SECONDS: Final = 30 * 86_400" in inspect.getsource(reconcile_module)
    package = Path(reconcile_module.__file__).resolve().parents[1]
    switch = re.compile(r"FINDLING_\w*(GRACE|VANISH)")
    for path in package.rglob("*.py"):
        assert not switch.search(path.read_text(encoding="utf-8")), path


# -- the sweep behind a busy queue (plan 43-02, D-43-01 to D-43-05) -----------
#
# Issue #25: on an instance with a crawl that never ends the quiet gate held the
# walk back for good, and the sweep only ever followed a walk, so it never ran.
# The sweep keeps its own stamp now, under the cadence rule of the walk, and the
# tests below hold both of its sides again: it runs behind a busy queue once per
# cycle, and it still never runs from an unsure position.

# The meta key of the stamp, written out rather than imported: the test reads
# the value under the name the plan gave it, not under whatever the code calls it.
SWEEP_KEY = "storage_sweep_at"

CRAWLING = QueueStats(scheduled=0, crawling=True)
# quiet_max of _reconcile is 100.
CROWDED = QueueStats(scheduled=100)
UNREADABLE = QueueStats(ok=False)


def _sweep_stamp(store: Store) -> str | None:
    return store.read_meta().get(SWEEP_KEY)


def test_the_stamp_of_the_sweep_is_a_meta_key_of_its_own() -> None:
    assert getattr(repo_module, "SWEEP_MARK", None) == SWEEP_KEY


@pytest.mark.parametrize("busy", [CRAWLING, CROWDED], ids=["crawling", "crowded"])
async def test_a_busy_queue_still_sweeps_and_never_walks(store: Store, busy: QueueStats) -> None:
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    queue = _Queue(state=busy)

    result = await _reconcile(store, files, queue, [START]).run_once()

    assert result.state == ROUND_QUEUE_BUSY
    assert files.mount_calls == 1
    assert files.page_calls == 0
    assert queue.deleted() == [10, 11]
    assert _sweep_stamp(store) == str(int(START))
    _control_kept(queue)


async def test_an_unreadable_queue_never_sweeps(store: Store) -> None:
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    queue = _Queue(state=UNREADABLE)

    result = await _reconcile(store, files, queue, [START]).run_once()

    assert result.state == ROUND_QUEUE_UNAVAILABLE
    assert files.events == []
    assert queue.requeues == []
    assert _sweep_stamp(store) is None


async def test_a_busy_queue_still_sweeps_once_per_cadence(store: Store) -> None:
    # A storage that merely vanished: every sweep asks about it and stamps it,
    # so the number of questions is the number of sweeps.
    _record_all(store, 7, (30, 31))
    files = _Files(store, [CONTROL])
    queue = _Queue(state=CRAWLING)
    clock = [START]
    round_of = _reconcile(store, files, queue, clock)

    for tick in range(0, 2 * DAY, 300):
        clock[0] = START + tick
        assert (await round_of.run_once()).state == ROUND_QUEUE_BUSY

    # Never ran, so due at once; then once more when the 24 hours were up.
    assert files.asked == [[7], [7]]
    assert files.mount_calls == 2
    assert files.page_calls == 0
    assert _sweep_stamp(store) == str(int(START + DAY))
    assert queue.deleted() == []


async def test_the_stamp_waits_for_every_band(store: Store) -> None:
    _record_all(store, 14, (10, 11))
    _record_all(store, 15, (12, 13))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14, 15})))
    failing = _Queue(fail_at=2, state=CRAWLING)
    clock = [START]
    round_of = _reconcile(store, files, failing, clock)

    await round_of.run_once()

    assert failing.requeues == [([10, 11], KIND_DELETE), ([12, 13], KIND_DELETE)]
    assert _sweep_stamp(store) is None
    assert round_of._cooldown > 0

    # The next round tries again, and this time every band arrives.
    clock[0] = START + 300
    healthy = _Queue(state=CRAWLING)
    await _reconcile(store, files, healthy, clock).run_once()

    assert set(healthy.deleted()) == {10, 11, 12, 13}
    assert _sweep_stamp(store) == str(int(START + 300))
    _control_kept(failing)
    _control_kept(healthy)


@pytest.mark.parametrize("unsure", ["empty", "discarded"])
async def test_an_unsure_list_behind_a_busy_queue_neither_sweeps_nor_stamps(store: Store, unsure: str) -> None:
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    if unsure == "empty":
        files.listed = []
    else:
        files.discarded = 1
    queue = _Queue(state=CRAWLING)
    round_of = _reconcile(store, files, queue, [START])

    result = await round_of.run_once()

    assert result.state == ROUND_QUEUE_BUSY
    assert files.asked == []
    assert queue.requeues == []
    assert _sweep_stamp(store) is None
    assert _rows(store, "vanished_storages") == []
    assert round_of._cooldown > 0


async def test_a_list_that_stays_discarded_is_not_read_every_tick(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    # W11: twelve hours of a busy queue and a list with a refused entry. Every
    # round would be due for the sweep, and without the back-off the list would
    # be read every five minutes, 144 times.
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    files.discarded = 1
    queue = _Queue(state=CRAWLING)
    clock = [START]
    round_of = _reconcile(store, files, queue, clock, tick_seconds=300.0)
    round_of.arm()
    stop = asyncio.Event()

    async def _fast_pause(seconds: float, stop_event: asyncio.Event) -> None:
        clock[0] += seconds
        if clock[0] - START >= 12 * 3600:
            stop_event.set()
        await asyncio.sleep(0)

    monkeypatch.setattr(reconcile_module, "_pause", _fast_pause)
    await round_of.run(stop)

    reads = files.mount_calls
    print(f"mount list reads in 12 hours: {reads}")
    assert 1 <= reads <= 12 + 6, reads
    assert queue.requeues == []
    assert _sweep_stamp(store) is None

    # The list is whole again: the next round sweeps and the pause is back to
    # the tick.
    files.discarded = 0
    await round_of.run_once()

    assert queue.deleted() == [10, 11]
    assert _sweep_stamp(store) is not None
    assert round_of._cooldown == 0
    _control_kept(queue)


async def test_a_pause_during_the_sweep_ends_it_without_a_stamp(store: Store) -> None:
    _record_all(store, 14, (10, 11))
    _record_all(store, 15, (12, 13))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14, 15})))
    queue = _Queue(state=CRAWLING)
    round_of = _reconcile(store, files, queue, [START])
    queue.on_requeue = round_of.hold_for_backup

    await round_of.run_once()

    assert queue.deleted() == [10, 11]
    assert _sweep_stamp(store) is None
    assert round_of._cooldown == 0
    _control_kept(queue)


async def test_a_held_pause_starts_no_round_and_no_sweep(store: Store) -> None:
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    queue = _Queue(state=CRAWLING)
    round_of = _reconcile(store, files, queue, [START])
    round_of.arm()
    round_of.hold_for_backup()
    stop = asyncio.Event()

    task = asyncio.create_task(round_of.run(stop))
    await asyncio.sleep(0.05)
    stop.set()
    await task

    assert files.events == []
    assert queue.requeues == []
    assert _sweep_stamp(store) is None


async def test_deleted_homes_without_a_storage_row_go_in_the_first_sweep(store: Store) -> None:
    # D-43-05: the homes of deleted users have no oc_storages row, and the PHP
    # half answers every asked id without a row as gone. The crawl still runs.
    _record_all(store, 215, (2150, 2151))
    _record_all(store, 216, (2160,))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({215, 216})))
    queue = _Queue(state=CRAWLING)

    await _reconcile(store, files, queue, [START]).run_once()

    assert files.asked == [[215, 216]]
    assert queue.deleted() == [2150, 2151, 2160]
    assert _stamp(store, 215) is None
    assert _stamp(store, 216) is None
    _control_kept(queue)


async def test_a_vanished_storage_behind_a_busy_queue_keeps_its_grace(store: Store) -> None:
    _record_all(store, 7, (30, 31))
    files = _Files(store, [CONTROL])
    queue = _Queue(state=CRAWLING)
    clock = [START]
    round_of = _reconcile(store, files, queue, clock)

    await round_of.run_once()
    assert _stamp(store, 7) == int(START)

    clock[0] = START + 29 * DAY
    await round_of.run_once()
    assert queue.deleted() == []
    assert _stamp(store, 7) == int(START)

    clock[0] = START + 30 * DAY
    await round_of.run_once()
    assert queue.deleted() == [30, 31]
    _control_kept(queue)


async def test_storage_ids_below_one_are_never_swept(store: Store) -> None:
    _record_all(store, 0, (40,))
    _record_all(store, -1, (41,))
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({0, -1, 14})))
    queue = _Queue(state=CRAWLING)
    clock = [START]
    round_of = _reconcile(store, files, queue, clock)

    await round_of.run_once()
    clock[0] = START + 31 * DAY
    await round_of.run_once()

    assert files.asked
    assert all(0 not in asked and -1 not in asked for asked in files.asked)
    assert _stamp(store, 0) is None
    assert _stamp(store, -1) is None
    assert not {40, 41} & set(queue.deleted())
    assert set(queue.deleted()) == {10, 11}
    _control_kept(queue)


async def test_a_quiet_round_sweeps_before_it_walks(store: Store) -> None:
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    queue = _Queue()

    result = await _reconcile(store, files, queue, [START]).run_once()

    assert result.state == ROUND_WALKED
    assert files.events == ["mounts", "gone", "page"]
    assert queue.deleted() == [10, 11]
    assert _sweep_stamp(store) == str(int(START))
    _control_kept(queue)


async def test_a_walk_that_ended_early_has_already_swept(store: Store) -> None:
    # The sweep needs a whole mount list, not a whole walk.
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    files.page_unavailable = True
    queue = _Queue()

    result = await _reconcile(store, files, queue, [START]).run_once()

    assert result.state == ROUND_UNAVAILABLE
    assert queue.deleted() == [10, 11]
    assert _sweep_stamp(store) == str(int(START))
    _control_kept(queue)


async def test_the_sweep_leaves_the_catch_up_alone(store: Store) -> None:
    # Catch-up (CATCHUP_MARK, the rewind) stays on the quiet path.
    store.write_meta(CATCHUP_MARK, CATCHUP_RECONCILE)
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    queue = _Queue(state=CRAWLING)
    round_of = _reconcile(store, files, queue, [START])

    result = await round_of.run_once()

    assert result.state == ROUND_QUEUE_BUSY
    assert queue.deleted() == [10, 11]
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_RECONCILE
    assert round_of._catchup_rewound is False


def test_the_sweep_stands_behind_a_whole_list_and_in_front_of_the_walk() -> None:
    # The source probe that replaces the one of plan 36-04: the call sits
    # behind the two conditions of T-36-13 and in front of the walk loop, and
    # there is no second call behind the loop.
    source = inspect.getsource(Reconcile.run_once)
    guard = source.index("found.mounts and not found.discarded")
    call = source.index("_sweep_vanished(")
    loop = source.index("for mount in found.mounts")

    assert guard < call < loop
    assert source.count("_sweep_vanished(") == 1


@pytest.mark.parametrize("raw", ["", "soon", "inf", "nan", "1.5"])
async def test_an_unreadable_stamp_reads_as_never_swept(store: Store, raw: str) -> None:
    store.write_meta(SWEEP_KEY, raw)
    _record_all(store, 14, (10, 11))
    files = _Files(store, [CONTROL], GoneResult(gone=frozenset({14})))
    queue = _Queue(state=CRAWLING)

    await _reconcile(store, files, queue, [START]).run_once()

    assert queue.deleted() == [10, 11]
    assert _sweep_stamp(store) == str(int(START))
