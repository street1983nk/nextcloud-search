"""The reconcile round, against a real state database and fakes for Nextcloud.

Eight claims, and every one of them is a way this round could quietly do damage
rather than repair. The reconcile is the only part of the system that concludes
something from an absence, and an absence is the cheapest thing in the world to
produce by accident: a page that ended early, a row the client refused, a
transport failure halfway through a mount.

*The deletion tests* are therefore the centre of this file. A file has to be
locally known, inside the range the page covers and missing from a page that is
complete before it becomes a delete job, and the round has to hand that job to
the queue rather than write the index itself.

*The gate tests* are the other half. A reconcile that runs against the initial
index doubles the load on the box it was supposed to keep usable, and one that
runs on every tick never lets an instance rest. Both gates are checked from the
outside, by watching that no page is ever asked for.

*The resume test* stages the abort that matters: the second slice of a mount
fails in transport. The bookmark has to stand where the first slice ended, and
the next round has to start exactly there.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest

from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import FileRow, Mount, MountResult, SliceResult
from findling.nc.queue import KIND_CONTENT, KIND_DELETE, CallResult, QueueStats
from findling.store.repo import FileMeta, Store, open_store
from findling.worker.reconcile import (
    ROUND_NOT_DUE,
    ROUND_QUEUE_BUSY,
    ROUND_QUEUE_UNAVAILABLE,
    ROUND_UNAVAILABLE,
    ROUND_WALKED,
    Reconcile,
)

RECONCILE_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "worker" / "reconcile.py"

STORAGE = 3
ROOT = 17

# A fixed point in time, so that the cadence is decided by the test and not by
# the clock of whoever runs it. Every stamp below is derived from this one.
NOW = 1_800_000_000.0
HOUR = 3600.0


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


def a_file(file_id: int, *, etag: str) -> FileMeta:
    return FileMeta(
        storage_id=STORAGE,
        root_id=ROOT,
        path=f"files/report-{file_id}.pdf",
        title=f"report-{file_id}.pdf",
        mime="application/pdf",
        size=1024,
        mtime=1_700_000_000,
        etag=etag,
    )


def a_row(file_id: int, *, etag: str) -> FileRow:
    return FileRow(file_id=file_id, etag=etag, size=1024, mtime=1_700_000_000, mime="application/pdf")


class _FakeQueue:
    """The two queue calls the reconcile makes, answered from a script."""

    def __init__(self, *, scheduled: int = 0, ok: bool = True) -> None:
        self.scheduled = scheduled
        self.ok = ok
        self.stats_calls = 0
        self.requeues: list[tuple[list[int], str]] = []
        self.requeue_fails = False

    async def stats(self) -> QueueStats:
        self.stats_calls += 1
        return QueueStats(scheduled=self.scheduled, ok=self.ok)

    async def requeue(self, file_ids: Any, *, kind: str) -> CallResult:
        ids = list(file_ids)
        self.requeues.append((ids, kind))
        if self.requeue_fails:
            return CallResult(ok=False)
        return CallResult(ok=True, count=len(ids))

    def kinds_of(self, kind: str) -> list[int]:
        """Every file id handed over under this kind, in order."""
        return [file_id for ids, handed in self.requeues if handed == kind for file_id in ids]


class _FakeFiles:
    """The mount list and a scripted sequence of pages."""

    def __init__(self, *pages: SliceResult, mounts: tuple[Mount, ...] | None = None, unavailable: bool = False) -> None:
        self._pages = list(pages)
        self._mounts = MountResult(
            mounts=(Mount(storage_id=STORAGE, root_id=ROOT, overridden_root=ROOT + 1),) if mounts is None else mounts,
            unavailable=unavailable,
        )
        self.asked: list[tuple[int, int, int, int]] = []

    async def mounts(self) -> MountResult:
        return self._mounts

    async def page(self, *, storage: int, root: int, after: int, limit: int) -> SliceResult:
        self.asked.append((storage, root, after, limit))
        return self._pages.pop(0) if self._pages else SliceResult(final=True)


def _reconcile(store: Store, files: _FakeFiles, queue: _FakeQueue, *, now: float = NOW) -> Reconcile:
    """A round wired to fakes, with the clock and the hour under test control."""
    return Reconcile(
        store=store,
        client_factory=lambda: cast("AsyncNextcloudApp", None),
        files_factory=lambda nc: cast("Any", files),
        queue_factory=lambda nc: cast("Any", queue),
        slice_size=2,
        quiet_max=100,
        hour=2,
        min_interval_hours=24,
        pause_seconds=0.0,
        clock=lambda: now,
        hour_of=lambda: 2,
    )


# -- what the comparison finds ---------------------------------------------


async def test_reconcile_hands_an_unknown_file_to_the_content_track(store: Store) -> None:
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert result.state == ROUND_WALKED
    assert queue.kinds_of(KIND_CONTENT) == [10]
    assert queue.kinds_of(KIND_DELETE) == []


async def test_reconcile_hands_a_file_with_a_moved_etag_to_the_content_track(store: Store) -> None:
    store.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    store.record(11, a_file(11, etag="bbb"), "indexed", content_hash="b")
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"), a_row(11, etag="ccc")), final=True))
    queue = _FakeQueue()

    await _reconcile(store, files, queue).run_once()

    # 10 is unchanged and costs nothing; only the moved mark is work.
    assert queue.kinds_of(KIND_CONTENT) == [11]


async def test_reconcile_hands_a_file_that_is_gone_to_the_delete_track(store: Store) -> None:
    store.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    store.record(11, a_file(11, etag="bbb"), "indexed", content_hash="b")
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.kinds_of(KIND_DELETE) == [11]
    assert result.missing == 1


async def test_an_incomplete_page_never_produces_a_deletion(store: Store) -> None:
    # The contract of SliceResult.complete, seen from this side. A row the client
    # had to refuse is missing from the page, and missing from the page is
    # exactly the shape of a deletion (T-03-1201).
    store.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    store.record(11, a_file(11, etag="bbb"), "indexed", content_hash="b")
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True, discarded=1))
    queue = _FakeQueue()

    await _reconcile(store, files, queue).run_once()

    assert queue.kinds_of(KIND_DELETE) == []


# -- the gates --------------------------------------------------------------


async def test_reconcile_does_nothing_while_the_queue_is_busy(store: Store) -> None:
    # D-03. An instance working off an initial index or an OCR backlog must not
    # also be walking its whole file list.
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue(scheduled=5000)

    result = await _reconcile(store, files, queue).run_once()

    assert result.state == ROUND_QUEUE_BUSY
    assert files.asked == []
    assert queue.requeues == []


async def test_a_queue_that_cannot_be_counted_stops_the_round(store: Store) -> None:
    # An unreadable counter is not a quiet queue. Walking anyway would be the
    # worst possible reading of "we do not know".
    files = _FakeFiles(SliceResult(final=True))
    queue = _FakeQueue(ok=False)

    result = await _reconcile(store, files, queue).run_once()

    assert result.state == ROUND_QUEUE_UNAVAILABLE
    assert files.asked == []


async def test_a_second_round_inside_the_minimum_pause_does_nothing(store: Store) -> None:
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    first = await _reconcile(store, files, queue).run_once()
    second = await _reconcile(store, _FakeFiles(SliceResult(final=True)), queue).run_once()

    assert first.state == ROUND_WALKED
    assert second.state == ROUND_NOT_DUE


async def test_a_round_after_the_minimum_pause_walks_again(store: Store) -> None:
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()
    await _reconcile(store, files, queue).run_once()

    later = _FakeFiles(SliceResult(final=True))
    result = await _reconcile(store, later, queue, now=NOW + 25 * HOUR).run_once()

    assert result.state == ROUND_WALKED


# -- the walk ---------------------------------------------------------------


async def test_reconcile_resumes_at_the_cursor(store: Store) -> None:
    # The abort that costs the most: the first slice is through and its findings
    # are in the queue, the second one dies in transport. The bookmark has to
    # stand behind the first slice, and the next round has to start there.
    first_walk = _FakeFiles(
        SliceResult(files=(a_row(10, etag="aaa"), a_row(11, etag="bbb"))),
        SliceResult(unavailable=True),
    )
    queue = _FakeQueue()

    result = await _reconcile(store, first_walk, queue).run_once()

    assert result.state == ROUND_UNAVAILABLE
    assert store.reconcile_cursor(STORAGE).after_file_id == 11
    assert [asked[2] for asked in first_walk.asked] == [0, 11]

    second_walk = _FakeFiles(SliceResult(files=(a_row(12, etag="ccc"),), final=True))
    await _reconcile(store, second_walk, queue, now=NOW + 25 * HOUR).run_once()

    assert [asked[2] for asked in second_walk.asked] == [11]


async def test_a_transport_failure_leaves_the_bookmark_where_it_was(store: Store) -> None:
    files = _FakeFiles(SliceResult(unavailable=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert result.state == ROUND_UNAVAILABLE
    assert store.reconcile_cursor(STORAGE).after_file_id == 0
    assert store.reconcile_cursor(STORAGE).finished_at is None


async def test_a_requeue_that_fails_does_not_move_the_bookmark(store: Store) -> None:
    # Moving the cursor here would drop the findings of this slice until the next
    # full cycle, which on the default cadence is a day of a stale index.
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),)), SliceResult(final=True))
    queue = _FakeQueue()
    queue.requeue_fails = True

    result = await _reconcile(store, files, queue).run_once()

    assert result.state == ROUND_UNAVAILABLE
    assert store.reconcile_cursor(STORAGE).after_file_id == 0


async def test_a_finished_walk_closes_the_mount_and_stamps_the_time(store: Store) -> None:
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    await _reconcile(store, files, queue).run_once()

    cursor = store.reconcile_cursor(STORAGE)
    assert cursor.after_file_id == 0
    assert cursor.finished_at == int(NOW)


async def test_the_quiet_gate_is_checked_before_every_slice(store: Store) -> None:
    # A round that starts on a calm instance and runs into the working day has to
    # stop, and it stops at the slice boundary because nothing after that point
    # cannot simply be done again.
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),)), SliceResult(final=True))
    queue = _FakeQueue()

    class _BusyAfterTheFirstSlice(_FakeQueue):
        async def stats(self) -> QueueStats:
            self.stats_calls += 1
            return QueueStats(scheduled=0 if self.stats_calls < 3 else 5000)

    queue = _BusyAfterTheFirstSlice()
    result = await _reconcile(store, files, queue).run_once()

    assert result.state == ROUND_QUEUE_BUSY
    assert len(files.asked) == 1


async def test_run_survives_an_exception_and_ends_on_the_stop_event(store: Store) -> None:
    class _Exploding(_FakeFiles):
        async def mounts(self) -> MountResult:
            raise RuntimeError("no mounts today")

    round_under_test = _reconcile(store, _Exploding(), _FakeQueue())
    round_under_test.arm()
    stop = asyncio.Event()

    task = asyncio.create_task(round_under_test.run(stop))
    await asyncio.sleep(0)
    stop.set()
    await asyncio.wait_for(task, timeout=5)

    assert task.done()


# -- the properties a grep has to keep --------------------------------------


def test_the_reconcile_opens_no_second_index_writer() -> None:
    # There is exactly one index writer in the process and it belongs to the
    # poller; a second one is a tantivy lock conflict that would stop the
    # indexing task for good (T-03-1203).
    source = RECONCILE_SOURCE.read_text(encoding="utf-8")

    assert re.search(r"open_index|IndexBatchWriter|IndexWriter", source) is None


def test_the_reconcile_log_carries_no_path_and_no_name() -> None:
    # T-03-1205. The file list is the most private thing this container reads.
    source = RECONCILE_SOURCE.read_text(encoding="utf-8")

    assert re.findall(r"LOGGER\.[a-z]+\(.*(?:path|name|title)", source) == []
