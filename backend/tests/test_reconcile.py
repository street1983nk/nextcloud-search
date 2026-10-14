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
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from findling.config import settings
from findling.extract import errors
from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import FileRow, Mount, MountResult, SliceResult
from findling.nc.queue import KIND_CONTENT, KIND_DELETE, CallResult, QueueStats
from findling.store import repo
from findling.store.repo import FileMeta, Store, open_store
from findling.worker.reconcile import (
    EXCLUDED_REASON,
    EXCLUDED_STATE,
    GIVEN_UP_REASON,
    GIVEN_UP_STATE,
    REQUEUE_BAND,
    ROUND_NOT_DUE,
    ROUND_QUEUE_BUSY,
    ROUND_QUEUE_UNAVAILABLE,
    ROUND_UNAVAILABLE,
    ROUND_WALKED,
    Reconcile,
)

RECONCILE_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "worker" / "reconcile.py"
PHP_LIB = Path(__file__).resolve().parents[2] / "php" / "lib"
PHP_QUEUE_CONTROLLER = PHP_LIB / "Controller" / "QueueController.php"
PHP_QUEUE_SERVICE = PHP_LIB / "Service" / "QueueService.php"
PHP_RECONCILE_CONTROLLER = PHP_LIB / "Controller" / "ReconcileController.php"

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


@pytest.fixture
def ocr_off(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """An instance whose admin switched OCR off, through the documented variable.

    The cache is cleared on both sides, exactly the way tests/test_poller.py
    does it: the settings are resolved once per process by design, and a test
    that changed the environment without clearing would hand its answer to the
    next one.
    """
    monkeypatch.setenv("FINDLING_OCR_ENABLED", "false")
    settings.cache_clear()
    yield
    settings.cache_clear()


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


def a_row(file_id: int, *, etag: str, state: str = "", reason: str = "") -> FileRow:
    return FileRow(
        file_id=file_id,
        etag=etag,
        size=1024,
        mtime=1_700_000_000,
        mime="application/pdf",
        state=state,
        reason=reason,
    )


def a_given_up_row(file_id: int, *, etag: str) -> FileRow:
    """A page row carrying the end state Nextcloud reached for this file.

    The verdict travels in the page and not in a second call per file, which is
    the whole reason this shape exists: the walk works in bands, and a round trip
    per row would make the repair more expensive than the work it saves.
    """
    return a_row(file_id, etag=etag, state=GIVEN_UP_STATE, reason=GIVEN_UP_REASON)


def a_excluded_row(file_id: int, *, etag: str) -> FileRow:
    """A page row the PHP half marked as excluded by an admin rule of today.

    The mark is live: the PHP half works it out from the rules on every page and
    never stores it, so a row only carries it while a rule still matches.
    """
    return a_row(file_id, etag=etag, state=EXCLUDED_STATE, reason=EXCLUDED_REASON)


class _FakeQueue:
    """The two queue calls the reconcile makes, answered from a script."""

    def __init__(self, *, scheduled: int = 0, ok: bool = True, crawling: bool = False) -> None:
        self.scheduled = scheduled
        self.ok = ok
        self.crawling = crawling
        self.stats_calls = 0
        self.requeues: list[tuple[list[int], str]] = []
        self.requeue_fails = False

    async def stats(self) -> QueueStats:
        self.stats_calls += 1
        return QueueStats(scheduled=self.scheduled, ok=self.ok, crawling=self.crawling)

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


def _reconcile(
    store: Store, files: _FakeFiles, queue: _FakeQueue, *, now: float = NOW, slice_size: int = 2
) -> Reconcile:
    """A round wired to fakes, with the clock and the hour under test control."""
    return Reconcile(
        store=store,
        client_factory=lambda: cast("AsyncNextcloudApp", None),
        files_factory=lambda nc: cast("Any", files),
        queue_factory=lambda nc: cast("Any", queue),
        slice_size=slice_size,
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


async def test_a_file_nextcloud_gave_up_on_is_not_requeued_by_two_cycles(store: Store) -> None:
    """The defect this pair of tests exists for (review finding IN-03 of phase 3).

    A row that is handed out and never acknowledged ends on the Nextcloud side as
    failed(repeatedly_stuck), and the queue row is removed with it. The container
    never heard of the file, so every night the comparison found it unindexed,
    requeued it, watched it fail three more times and started over. On fifty
    thousand files that is permanent load with no cause anybody can see, and the
    verdict never becomes final for exactly the files the repair discovered.

    Two cycles rather than one, because the rule may not be bound to a point in
    time. The second round is the one that would go red again if somebody made
    the verdict expire.
    """
    queue = _FakeQueue()

    first = await _reconcile(
        store, _FakeFiles(SliceResult(files=(a_given_up_row(10, etag="aaa"),), final=True)), queue
    ).run_once()
    second = await _reconcile(
        store,
        _FakeFiles(SliceResult(files=(a_given_up_row(10, etag="aaa"),), final=True)),
        queue,
        now=NOW + 25 * HOUR,
    ).run_once()

    assert (first.state, second.state) == (ROUND_WALKED, ROUND_WALKED)
    assert queue.requeues == []
    assert (first.stale, second.stale) == (0, 0)
    # Counted once and never again: after the first round the file is a known,
    # unchanged row like any other, which is what makes the rule cost nothing.
    assert (first.given_up, second.given_up) == (1, 0)

    row = store.file_row(10)
    assert row is not None
    assert (row["state"], row["reason"], row["etag"]) == (GIVEN_UP_STATE, GIVEN_UP_REASON, "aaa")


async def test_a_new_etag_lifts_the_final_verdict_and_requeues_the_file(store: Store) -> None:
    """The counterpart, and the reason the verdict is stored against the etag.

    A final verdict belongs to the version of the file it was reached on, never
    to the file id for good. The Nextcloud row keeps saying repeatedly_stuck
    after the document was replaced, so a rule that only read that row would
    leave the new bytes out of the index forever.
    """
    queue = _FakeQueue()

    await _reconcile(
        store, _FakeFiles(SliceResult(files=(a_given_up_row(10, etag="aaa"),), final=True)), queue
    ).run_once()
    assert queue.kinds_of(KIND_CONTENT) == []

    changed = _FakeFiles(SliceResult(files=(a_given_up_row(10, etag="bbb"),), final=True))
    result = await _reconcile(store, changed, queue, now=NOW + 25 * HOUR).run_once()

    assert result.stale == 1
    assert result.given_up == 0
    assert queue.kinds_of(KIND_CONTENT) == [10]


# -- files an admin rule of today excludes (owner decision 03.10.2026 a) -------
#
# Run 7 of the 28-07 chain found 549 files under excluded folders handed to the
# content track every ~300 s. The page carried them like any other file, the
# container knew no etag for them, describe() answered the claim with a delete
# order, the poller set a tombstone, and the next quiet round found them unknown
# again. The batch of the round itself broke the quiet mark, the round stayed
# unfinished and was due again at once. The PHP half now marks such a row live as
# skipped(excluded), and these tests hold what the container does with the mark.


async def test_an_excluded_unknown_file_is_not_requeued_by_two_cycles(store: Store) -> None:
    """The run 7 shape, over two cycles like the give-up rule above.

    The second cycle is the one that would go red again if the mark were only
    honoured once, and the missing row in the store is what keeps a lifted rule
    from being outlived by a stored verdict.
    """
    queue = _FakeQueue()

    first = await _reconcile(
        store,
        _FakeFiles(SliceResult(files=(a_excluded_row(10, etag="aaa"), a_row(11, etag="bbb")), final=True)),
        queue,
    ).run_once()

    assert first.state == ROUND_WALKED
    assert queue.kinds_of(KIND_CONTENT) == [11]
    assert (first.stale, first.given_up) == (1, 0)
    assert store.file_row(10) is None

    await _reconcile(
        store,
        _FakeFiles(SliceResult(files=(a_excluded_row(10, etag="aaa"),), final=True)),
        queue,
        now=NOW + 25 * HOUR,
    ).run_once()

    assert 10 not in queue.kinds_of(KIND_CONTENT)


async def test_an_excluded_file_behind_a_tombstone_is_not_requeued(store: Store) -> None:
    # The exact state run 7 left behind: the delete order of describe() made the
    # poller set a tombstone, and known_etags does not answer for tombstones.
    store.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    store.tombstone(10)
    files = _FakeFiles(SliceResult(files=(a_excluded_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.requeues == []
    assert result.stale == 0


async def test_a_lifted_rule_makes_the_file_work_again_in_the_next_round(store: Store) -> None:
    """The reason the mark is never stored in this container.

    A stored skipped(excluded) against the etag would meet the next page with the
    same etag in the first branch of the comparison and count as done, and the
    file would stay out of the index for good after the admin lifted the rule.
    """
    queue = _FakeQueue()

    await _reconcile(
        store, _FakeFiles(SliceResult(files=(a_excluded_row(10, etag="aaa"),), final=True)), queue
    ).run_once()
    assert queue.kinds_of(KIND_CONTENT) == []

    lifted = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True))
    result = await _reconcile(store, lifted, queue, now=NOW + 25 * HOUR).run_once()

    assert queue.kinds_of(KIND_CONTENT) == [10]
    assert result.stale == 1


async def test_a_known_excluded_file_with_a_new_etag_stays_content_work(store: Store) -> None:
    # CR-01 stays intact: a file this container holds under another version is
    # content work, and describe() turns the claim into the delete order that
    # takes the document out of the index. The mark must not suppress that.
    store.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    files = _FakeFiles(SliceResult(files=(a_excluded_row(10, etag="bbb"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.kinds_of(KIND_CONTENT) == [10]
    assert result.stale == 1


async def test_a_known_unchanged_excluded_file_becomes_content_work(store: Store) -> None:
    """The defect B1 of phase 33, and the reconcile as the net for exclusions.

    D-33-01 (owner, 13.10.2026): the rule of today decides, also for a known
    unchanged file. Before, the etag branch said "done" first and the file stayed
    in the index for good under a rule set by occ, on a mount that showed up
    later, or after a rename into an excluded folder. The claim of the content
    order is what describe() turns into the delete order.
    """
    store.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    files = _FakeFiles(SliceResult(files=(a_excluded_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.kinds_of(KIND_CONTENT) == [10]
    assert queue.kinds_of(KIND_DELETE) == []
    assert result.stale == 1


async def test_a_living_row_without_an_etag_under_a_rule_becomes_content_work(store: Store) -> None:
    # The membership in known decides, not the stored value: a living row whose
    # etag is None is still a document of this container (W3 of the plan check).
    store.record(10, replace(a_file(10, etag="aaa"), etag=None), "indexed", content_hash="a")
    assert store.known_etags([10]) == {10: None}
    files = _FakeFiles(SliceResult(files=(a_excluded_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.kinds_of(KIND_CONTENT) == [10]
    assert result.stale == 1


async def test_a_known_unchanged_file_without_the_mark_costs_nothing(store: Store) -> None:
    # The positive control of the two tests above: same store, same etag, no mark.
    store.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa", state="indexed"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.requeues == []
    assert result.stale == 0


async def test_an_excluded_file_is_cleared_once_and_then_left_alone(store: Store) -> None:
    # No loop: the first round hands the known file over, the delete order of
    # describe() ends in a tombstone, and the next round reads the file as
    # unknown plus excluded and leaves it where it is.
    store.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    queue = _FakeQueue()

    first = await _reconcile(
        store, _FakeFiles(SliceResult(files=(a_excluded_row(10, etag="aaa"),), final=True)), queue
    ).run_once()
    store.tombstone(10)
    second = await _reconcile(
        store,
        _FakeFiles(SliceResult(files=(a_excluded_row(10, etag="aaa"),), final=True)),
        queue,
        now=NOW + 25 * HOUR,
    ).run_once()

    assert (first.stale, second.stale) == (1, 0)
    assert queue.kinds_of(KIND_CONTENT) == [10]


async def test_150_known_excluded_files_travel_in_one_band_and_the_quiet_gate_holds_the_next_slice(
    store: Store,
) -> None:
    """T-33-09: the new branch adds no path of its own around band and quiet gate.

    One mixed page: 150 known unchanged files under a rule, 20 unknown ones under
    a rule, 10 known unchanged files without a rule and 5 unknown ordinary files.
    The 155 stale ids stay below REQUEUE_BAND and travel as one band; the queue
    then holds 155 rows, above the quiet mark of 100, so the gate before the next
    slice ends the round with the bookmark behind the first page.
    """
    for number in range(1, 151):
        store.record(number, a_file(number, etag="aaa"), "indexed", content_hash="a")
    for number in range(171, 181):
        store.record(number, a_file(number, etag="aaa"), "indexed", content_hash="a")
    rows = (
        *(a_excluded_row(number, etag="aaa") for number in range(1, 151)),
        *(a_excluded_row(number, etag="aaa") for number in range(151, 171)),
        *(a_row(number, etag="aaa", state="indexed") for number in range(171, 181)),
        *(a_row(number, etag="aaa") for number in range(181, 186)),
    )
    files = _FakeFiles(SliceResult(files=rows), SliceResult(files=(a_row(500, etag="aaa"),), final=True))

    class _CountsWhatItIsHanded(_FakeQueue):
        async def requeue(self, file_ids: Any, *, kind: str) -> CallResult:
            result = await super().requeue(file_ids, kind=kind)
            self.scheduled += result.count
            return result

    queue = _CountsWhatItIsHanded()
    result = await _reconcile(store, files, queue, slice_size=500).run_once()

    assert result.state == ROUND_QUEUE_BUSY
    assert queue.kinds_of(KIND_CONTENT) == [*range(1, 151), *range(181, 186)]
    assert [len(ids) for ids, kind in queue.requeues if kind == KIND_CONTENT] == [155]
    assert len(files.asked) == 1
    assert store.reconcile_cursor(STORAGE).after_file_id == 185


async def test_a_round_of_only_excluded_files_closes_the_mount(store: Store) -> None:
    # No batch of its own, so nothing breaks the quiet mark: the round walks
    # through, the mount is closed and the next tick is not due any more.
    rows = (a_excluded_row(10, etag="aaa"), a_excluded_row(11, etag="bbb"))
    queue = _FakeQueue()

    first = await _reconcile(store, _FakeFiles(SliceResult(files=rows, final=True)), queue).run_once()
    second = await _reconcile(store, _FakeFiles(SliceResult(files=rows, final=True)), queue).run_once()

    assert first.state == ROUND_WALKED
    assert (first.stale, first.given_up) == (0, 0)
    assert queue.requeues == []
    assert second.state == ROUND_NOT_DUE


def test_the_excluded_codes_are_the_ones_of_the_closed_list() -> None:
    # Same stance as GIVEN_UP_*: spelled out in the module, held against the
    # vocabulary of the wire here.
    assert (EXCLUDED_STATE, EXCLUDED_REASON) == ("skipped", "excluded")
    assert EXCLUDED_REASON in repo.STATE_REASONS[EXCLUDED_STATE]
    assert errors.Reason(EXCLUDED_REASON) in errors.STATE_REASONS[errors.State(EXCLUDED_STATE)]


# -- the stranded handover (DI-05-23) -----------------------------------------
#
# The pair the disk pause of plan 05-14 left behind on two files: the container
# had already written skipped(no_text_layer), which is the handover point of the
# OCR track and not an end state, and the acknowledgement that would have turned
# it into an OCR job never came, because the rows were written off on the other
# side in the same minute. Both halves then agree that nothing is to be done: the
# etag matches, so the comparison reads a known unchanged file, and the give-up
# verdict of the page is exactly the one that keeps the round from requeueing.
# The scan stays out of the index for good and no counter anywhere moves.


def a_stranded_scan(store: Store, file_id: int, *, etag: str) -> None:
    """The verdict of a text pass that died before the OCR job was created."""
    store.record(file_id, a_file(file_id, etag=etag), "skipped", "no_text_layer", content_hash="h")


async def test_a_scan_stranded_between_verdict_and_acknowledgement_heals_itself(store: Store) -> None:
    """DI-05-23, the half the refund in QueueMapper::unlock does not reach.

    The refund keeps the pause from producing new strandings. It cannot help the
    files that were already stranded when it shipped, and it cannot help a file
    whose container died between step 3 and step 4 of a pass, which is a
    permanent possibility and not a defect. So the round that exists to repair
    what nothing else notices has to notice this one.
    """
    a_stranded_scan(store, 10, etag="aaa")
    files = _FakeFiles(SliceResult(files=(a_given_up_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.kinds_of(KIND_CONTENT) == [10]
    assert result.stale == 1
    # Not counted as a give-up: the point of the branch is that this file is
    # work again, and the counter that says "we respected an end state" would be
    # saying the opposite of what happened.
    assert result.given_up == 0


async def test_the_healed_scan_is_not_requeued_once_it_has_a_verdict_of_its_own(store: Store) -> None:
    """The loop this branch could have become, closed from the other side.

    The requeue puts the file on the content track, the pass finds the same
    missing text layer, hands it to the OCR track and the engine writes a real
    verdict. From then on the container knows something else about the file, and
    the branch has to stop firing: a repair that runs every night forever is a
    download of every scan of the instance every night forever.
    """
    a_stranded_scan(store, 10, etag="aaa")
    queue = _FakeQueue()

    await _reconcile(
        store, _FakeFiles(SliceResult(files=(a_given_up_row(10, etag="aaa"),), final=True)), queue
    ).run_once()
    assert queue.kinds_of(KIND_CONTENT) == [10]

    # What the OCR pass leaves behind, with the etag unchanged: the bytes never
    # moved, only what is known about them.
    store.record(10, a_file(10, etag="aaa"), "indexed", content_hash="h")
    second = await _reconcile(
        store,
        _FakeFiles(SliceResult(files=(a_given_up_row(10, etag="aaa"),), final=True)),
        queue,
        now=NOW + 25 * HOUR,
    ).run_once()

    assert second.stale == 0
    assert queue.kinds_of(KIND_CONTENT) == [10]


async def test_with_ocr_switched_off_the_missing_text_layer_is_an_end_state(store: Store, ocr_off: None) -> None:
    """The one instance where the pair is not a stranding but the truth.

    With ``FINDLING_OCR_ENABLED=false`` there is no second track, so
    skipped(no_text_layer) is what this file gets and keeps. Requeueing it would
    download the document every night to reach the same verdict, which is the
    endless repair the branch above must not become.
    """
    del ocr_off
    a_stranded_scan(store, 10, etag="aaa")
    files = _FakeFiles(SliceResult(files=(a_given_up_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.kinds_of(KIND_CONTENT) == []
    assert result.stale == 0


async def test_a_file_written_off_over_there_and_failed_here_stays_written_off(store: Store) -> None:
    """Only the handover verdict is healed, and the narrowness is the point.

    failed(corrupt) on this side next to failed(repeatedly_stuck) on the other
    is two halves agreeing that the file cannot be read, and a round that
    requeued it would be the permanent load of review finding IN-03 again, only
    through a new door.
    """
    store.record(10, a_file(10, etag="aaa"), "failed", "corrupt", content_hash="h")
    files = _FakeFiles(SliceResult(files=(a_given_up_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.kinds_of(KIND_CONTENT) == []
    assert result.stale == 0


async def test_a_stranded_scan_without_the_write_off_over_there_is_ordinary_unchanged_work(
    store: Store,
) -> None:
    """The other half of the narrowness: no write-off, no repair.

    A scan that carries skipped(no_text_layer) while its queue row is alive is
    simply waiting for its OCR job. Requeueing on the verdict alone would put
    every scan of the instance back on the content track once a night, during
    the very OCR backlog it belongs to.
    """
    a_stranded_scan(store, 10, etag="aaa")
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.kinds_of(KIND_CONTENT) == []
    assert result.stale == 0


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


# -- the handover bands (review finding CR-01) --------------------------------
#
# QueueController::MAX_LIST_LENGTH is 256 and intList answers 400 for anything
# longer, so a slice with more findings than that has to travel in bands. Before
# the bands, such a slice wedged the round for good: the same page produced the
# same over-long list every cycle, the cursor never moved, and the two scenarios
# the reconcile exists for, a restore and a mass deletion, were exactly the ones
# that produced it.


def _php_max_list_length() -> int:
    """The MAX_LIST_LENGTH constant of the PHP controller, read out of its source.

    Read as text because a PHP constant cannot be imported, in the shape of the
    allowlist parity gate: writing the number into this file a second time would
    be the very drift the gate exists to catch.
    """
    source = PHP_QUEUE_CONTROLLER.read_text(encoding="utf-8")
    found = re.search(r"const MAX_LIST_LENGTH = (\d+);", source)
    assert found is not None, "the MAX_LIST_LENGTH constant is no longer where this gate looks for it"
    return int(found.group(1))


def test_the_requeue_band_stays_below_the_php_list_ceiling() -> None:
    # The parity gate. The day somebody lowers the controller limit under the
    # band, every slice with more findings than the new limit wedges the round
    # again, and this is the test that goes red instead.
    assert _php_max_list_length() >= REQUEUE_BAND


async def test_a_slice_with_more_stale_files_than_the_list_ceiling_is_handed_over_in_bands(store: Store) -> None:
    # The restore scenario: a page of 500 files the container does not know, all
    # of them stale at once. One call would carry 500 ids and be refused.
    rows = tuple(a_row(number, etag="aaa") for number in range(1, 501))
    files = _FakeFiles(SliceResult(files=rows, final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue, slice_size=500).run_once()

    assert result.state == ROUND_WALKED
    assert result.stale == 500
    assert queue.kinds_of(KIND_CONTENT) == list(range(1, 501))
    bands = [len(ids) for ids, kind in queue.requeues if kind == KIND_CONTENT]
    assert bands == [200, 200, 100]
    assert all(band <= _php_max_list_length() for band in bands)


async def test_a_mass_deletion_over_the_list_ceiling_is_handed_over_in_bands(store: Store) -> None:
    # The other scenario, and the unbounded one: on the final page gone_in_range
    # runs over the whole rest of the mount, so the missing list is not limited
    # by the slice size at all.
    for number in range(1, 301):
        store.record(number, a_file(number, etag="aaa"), "indexed", content_hash="a")
    files = _FakeFiles(SliceResult(files=(), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert result.state == ROUND_WALKED
    assert result.missing == 300
    assert queue.kinds_of(KIND_DELETE) == list(range(1, 301))
    assert [len(ids) for ids, kind in queue.requeues if kind == KIND_DELETE] == [200, 100]


async def test_a_band_that_fails_ends_the_round_without_moving_the_bookmark(store: Store) -> None:
    # A transport failure in the middle of the bands behaves like the failed
    # single call always did: the round ends, the cursor stands, and the repeated
    # slice hands the earlier bands over again, which requeueAs absorbs.
    rows = tuple(a_row(number, etag="aaa") for number in range(1, 501))
    files = _FakeFiles(SliceResult(files=rows, final=True))

    class _FailsFromTheSecondCall(_FakeQueue):
        async def requeue(self, file_ids: Any, *, kind: str) -> CallResult:
            result = await super().requeue(file_ids, kind=kind)
            if len(self.requeues) >= 2:
                return CallResult(ok=False)
            return result

    queue = _FailsFromTheSecondCall()
    result = await _reconcile(store, files, queue, slice_size=500).run_once()

    assert result.state == ROUND_UNAVAILABLE
    assert len(queue.requeues) == 2
    assert store.reconcile_cursor(STORAGE).after_file_id == 0


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


async def test_reconcile_does_nothing_while_the_crawl_is_unfinished(store: Store) -> None:
    # Run 8 of the 28-07 chain (L-T on m7g.4xlarge, abort 71 at 5427 of 5000).
    # Fifteen slots drained the work stock faster than the cron paced crawl
    # filled it, so the queue counter kept falling below the quiet mark while
    # the first index was still running. The reconcile walked ahead, read every
    # file the crawl had not reached as unknown and requeued it (401 + 9 x 500 +
    # 99 = the whole partial corpus), and the crawl queued the same 5000 files a
    # second time when it got there: 5000 passes ending as "unchanged". An
    # empty queue during a crawl is not a quiet instance.
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue(scheduled=0, crawling=True)

    result = await _reconcile(store, files, queue).run_once()

    assert result.state == ROUND_QUEUE_BUSY
    assert files.asked == []
    assert queue.requeues == []


async def test_a_crawl_that_starts_mid_round_stops_the_round_at_the_next_slice(store: Store) -> None:
    # occ findling:index --restart while a round walks: the gate before every
    # slice is the same gate, so the round ends at the slice boundary.
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),)), SliceResult(final=True))

    class _CrawlAfterTheFirstSlice(_FakeQueue):
        async def stats(self) -> QueueStats:
            self.stats_calls += 1
            return QueueStats(scheduled=0, crawling=self.stats_calls >= 3)

    queue = _CrawlAfterTheFirstSlice()
    result = await _reconcile(store, files, queue).run_once()

    assert result.state == ROUND_QUEUE_BUSY
    assert len(files.asked) == 1


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


# -- the catch-up cycle of 1.5 (FMT-06, D-31-01, D-31-02) -------------------
#
# Part A of worker/catchup.py ends with CATCHUP_MARK on CATCHUP_RECONCILE. From
# then on one cycle is due at once, and two narrow exceptions hold while it
# runs: a file written off over there without a row here is work instead of a
# give-up, and a file whose Nextcloud row carries the 1.3 substitute of the code
# this container holds is judged again. Both end with the mark on done.


def _catchup(store: Store, mark: str | None = repo.CATCHUP_RECONCILE) -> None:
    if mark is not None:
        store.write_meta(repo.CATCHUP_MARK, mark)


def _walked_an_hour_ago(store: Store) -> None:
    store.set_reconcile_cursor(STORAGE, 0, finished=True, at=int(NOW - HOUR))


def test_the_catch_up_mark_makes_a_cycle_due_at_once(store: Store) -> None:
    _walked_an_hour_ago(store)
    round_under_test = Reconcile(store=store, min_interval_hours=24, hour=2, clock=lambda: NOW, hour_of=lambda: 9)

    assert round_under_test._is_due(store) is False
    _catchup(store)
    assert round_under_test._is_due(store) is True


@pytest.mark.parametrize("mark", [None, "done", "17"])
def test_without_the_catch_up_request_the_cadence_is_the_old_one(store: Store, mark: str | None) -> None:
    _walked_an_hour_ago(store)
    _catchup(store, mark)
    round_under_test = Reconcile(store=store, min_interval_hours=24, hour=2, clock=lambda: NOW, hour_of=lambda: 9)

    assert round_under_test._is_due(store) is False


async def test_the_quiet_gate_holds_the_catch_up_cycle_back(store: Store) -> None:
    _catchup(store)
    files = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True))

    result = await _reconcile(store, files, _FakeQueue(scheduled=5000)).run_once()

    assert result.state == ROUND_QUEUE_BUSY
    assert files.asked == []
    assert store.read_meta()[repo.CATCHUP_MARK] == repo.CATCHUP_RECONCILE


async def test_the_catch_up_cycle_hands_over_the_unknown_files_and_not_the_known_ones(store: Store) -> None:
    for file_id in range(1, 51):
        store.record(file_id, a_file(file_id, etag=f"e{file_id}"), "indexed", content_hash="h")
    _walked_an_hour_ago(store)
    _catchup(store)
    rows = tuple(a_row(file_id, etag=f"e{file_id}") for file_id in range(1, 51))
    rows += tuple(a_row(file_id, etag="new") for file_id in (51, 52, 53))
    queue = _FakeQueue()

    result = await _reconcile(store, _FakeFiles(SliceResult(files=rows, final=True)), queue, slice_size=60).run_once()

    assert result.state == ROUND_WALKED
    assert queue.kinds_of(KIND_CONTENT) == [51, 52, 53]
    assert store.read_meta()[repo.CATCHUP_MARK] == repo.CATCHUP_DONE


class _GiveUpSpy:
    """Counts the calls of Store.give_up while letting them through."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.calls: list[int] = []
        original = Store.give_up

        def spy(store: Store, file_id: int, **kwargs: Any) -> None:
            self.calls.append(file_id)
            original(store, file_id, **kwargs)

        monkeypatch.setattr(Store, "give_up", spy)


def test_under_the_catch_up_mark_a_written_off_file_without_a_row_is_work(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Blocker 1 of the plan check of 31-11.

    A file Nextcloud wrote off after the last 1.4.2 cycle has no row here. Part
    A cannot see it, and the ordinary comparison would write it off here too
    instead of giving it the second chance of D-31-02.
    """
    spy = _GiveUpSpy(monkeypatch)
    _catchup(store)
    mount = Mount(storage_id=STORAGE, root_id=ROOT, overridden_root=ROOT + 1)

    stale, given_up = Reconcile._compare(store, mount, [a_given_up_row(10, etag="aaa")])

    assert (stale, given_up) == ([10], 0)
    assert spy.calls == []
    assert store.file_row(10) is None


@pytest.mark.parametrize("mark", [None, "done"])
def test_without_the_catch_up_request_a_written_off_file_is_written_off(
    store: Store, monkeypatch: pytest.MonkeyPatch, mark: str | None
) -> None:
    spy = _GiveUpSpy(monkeypatch)
    _catchup(store, mark)
    mount = Mount(storage_id=STORAGE, root_id=ROOT, overridden_root=ROOT + 1)

    stale, given_up = Reconcile._compare(store, mount, [a_given_up_row(10, etag="aaa")])

    assert (stale, given_up) == ([], 1)
    assert spy.calls == [10]


@pytest.mark.parametrize("mark", [None, "reconcile", "done"])
async def test_the_stranded_handover_heals_under_every_mark(store: Store, mark: str | None) -> None:
    a_stranded_scan(store, 10, etag="aaa")
    _catchup(store, mark)
    files = _FakeFiles(SliceResult(files=(a_given_up_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.kinds_of(KIND_CONTENT) == [10]
    assert result.given_up == 0


async def test_under_the_catch_up_mark_failed_here_and_written_off_there_stays_as_it_is(store: Store) -> None:
    store.record(10, a_file(10, etag="aaa"), "failed", "corrupt", content_hash="h")
    _catchup(store)
    files = _FakeFiles(SliceResult(files=(a_given_up_row(10, etag="aaa"),), final=True))
    queue = _FakeQueue()

    result = await _reconcile(store, files, queue).run_once()

    assert queue.kinds_of(KIND_CONTENT) == []
    assert result.stale == 0


def _judged(store: Store, file_id: int, reason: str, *, etag: str = "aaa") -> None:
    store.record(file_id, a_file(file_id, etag=etag), "skipped", reason)


def _compare_one(store: Store, row: FileRow) -> list[int]:
    mount = Mount(storage_id=STORAGE, root_id=ROOT, overridden_root=ROOT + 1)
    stale, _ = Reconcile._compare(store, mount, [row])
    return stale


@pytest.mark.parametrize(
    ("ours", "substitute"),
    [
        ("system_file", "mime_not_allowed"),
        ("legacy_format", "mime_not_allowed"),
        ("unsupported_variant", "image_not_ocrable"),
    ],
)
def test_the_wrong_upgrade_order_is_judged_again_under_the_mark(store: Store, ours: str, substitute: str) -> None:
    # W2, direction 1: a 1.4.2 container in front of a 1.5 companion stored
    # the 1.3 substitute over there; this container holds the real code.
    _judged(store, 10, ours)
    _catchup(store)

    assert _compare_one(store, a_row(10, etag="aaa", state="skipped", reason=substitute)) == [10]


@pytest.mark.parametrize(
    ("ours", "theirs"),
    [
        ("system_file", "system_file"),
        ("legacy_format", "legacy_format"),
        ("unsupported_variant", "unsupported_variant"),
        ("mime_not_allowed", "mime_not_allowed"),
        ("too_large", "mime_not_allowed"),
        ("too_large", "image_not_ocrable"),
        ("system_file", "image_not_ocrable"),
        ("unsupported_variant", "mime_not_allowed"),
    ],
)
def test_the_right_upgrade_order_is_left_alone_under_the_mark(store: Store, ours: str, theirs: str) -> None:
    # W2, direction 2: both halves agree, or the code over there is not the
    # substitute of the code here. Nothing is judged again.
    _judged(store, 10, ours)
    _catchup(store)

    assert _compare_one(store, a_row(10, etag="aaa", state="skipped", reason=theirs)) == []


def test_the_substitute_on_a_moved_etag_is_ordinary_stale_work(store: Store) -> None:
    _judged(store, 10, "system_file", etag="old")
    _catchup(store, None)

    assert _compare_one(store, a_row(10, etag="aaa", state="skipped", reason="mime_not_allowed")) == [10]


@pytest.mark.parametrize("mark", [None, "done", "17"])
def test_the_substitute_is_only_healed_once(store: Store, mark: str | None) -> None:
    _judged(store, 10, "system_file")
    _catchup(store, mark)

    assert _compare_one(store, a_row(10, etag="aaa", state="skipped", reason="mime_not_allowed")) == []


def test_a_page_of_a_thousand_rows_asks_for_the_stored_reasons_once(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    for file_id in range(1, 1001):
        _judged(store, file_id, "system_file")
    _catchup(store)
    calls: list[int] = []
    original = Store.known_skip_reasons

    def counting(self: Store, file_ids: Any) -> dict[int, str]:
        calls.append(len(file_ids))
        return original(self, file_ids)

    monkeypatch.setattr(Store, "known_skip_reasons", counting)
    mount = Mount(storage_id=STORAGE, root_id=ROOT, overridden_root=ROOT + 1)
    rows = [a_row(file_id, etag="aaa", state="skipped", reason="mime_not_allowed") for file_id in range(1, 1001)]

    stale, _ = Reconcile._compare(store, mount, rows)

    assert len(calls) == 1
    assert stale == list(range(1, 1001))


async def test_an_interrupted_catch_up_cycle_keeps_the_mark_and_a_finished_one_ends_it(store: Store) -> None:
    _catchup(store)
    queue = _FakeQueue()
    first = _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"), a_row(11, etag="bbb"))), SliceResult(unavailable=True))

    interrupted = await _reconcile(store, first, queue).run_once()

    assert interrupted.state == ROUND_UNAVAILABLE
    assert store.read_meta()[repo.CATCHUP_MARK] == repo.CATCHUP_RECONCILE

    finished = await _reconcile(store, _FakeFiles(SliceResult(final=True)), queue).run_once()

    assert finished.state == ROUND_WALKED
    assert store.read_meta()[repo.CATCHUP_MARK] == repo.CATCHUP_DONE


async def test_a_walk_begun_before_the_mark_is_walked_again_from_the_front(store: Store) -> None:
    # The catch-up rules hold for the pages of the cycle that ends with done.
    # A walk that began before the mark carried them for none of its pages, so
    # the first round under the mark goes back to the front of every mount.
    store.set_reconcile_cursor(STORAGE, 11, at=int(NOW - HOUR))
    _catchup(store)
    files = _FakeFiles(SliceResult(files=(a_row(5, etag="aaa"),), final=True))

    result = await _reconcile(store, files, _FakeQueue()).run_once()

    assert result.state == ROUND_WALKED
    assert [asked[2] for asked in files.asked] == [0]
    assert store.read_meta()[repo.CATCHUP_MARK] == repo.CATCHUP_DONE


async def test_after_done_the_cadence_is_the_old_one_again(store: Store) -> None:
    _catchup(store)
    queue = _FakeQueue()
    await _reconcile(store, _FakeFiles(SliceResult(final=True)), queue).run_once()

    again = await _reconcile(store, _FakeFiles(SliceResult(final=True)), queue, now=NOW + HOUR).run_once()

    assert again.state == ROUND_NOT_DUE
    assert store.read_meta()[repo.CATCHUP_MARK] == repo.CATCHUP_DONE


class _CountingReconcile(Reconcile):
    """A reconcile on fakes that counts its rounds and reads a clock under test control."""

    def __init__(self, store: Store, files: _FakeFiles, queue: _FakeQueue, clock: list[float]) -> None:
        super().__init__(
            store=store,
            client_factory=lambda: cast("AsyncNextcloudApp", None),
            files_factory=lambda nc: cast("Any", files),
            queue_factory=lambda nc: cast("Any", queue),
            slice_size=2,
            quiet_max=100,
            hour=2,
            min_interval_hours=24,
            pause_seconds=0.0,
            tick_seconds=0.001,
            clock=lambda: clock[0],
            hour_of=lambda: 2,
        )
        self.rounds = 0

    async def run_once(self) -> Any:
        self.rounds += 1
        return await super().run_once()


async def test_the_one_time_mode_runs_one_cycle_writes_done_and_ends(store: Store) -> None:
    _catchup(store)
    clock = [NOW]
    once = _CountingReconcile(
        store, _FakeFiles(SliceResult(files=(a_row(10, etag="aaa"),), final=True)), _FakeQueue(), clock
    )
    once.arm()
    stop = asyncio.Event()

    await asyncio.wait_for(once.run(stop, once=True), timeout=5)

    assert once.rounds == 1
    assert store.read_meta()[repo.CATCHUP_MARK] == repo.CATCHUP_DONE
    assert not stop.is_set(), "it ended by itself"


async def test_the_one_time_mode_waits_for_part_a_and_starts_no_ordinary_cycle(store: Store) -> None:
    clock = [NOW]
    once = _CountingReconcile(store, _FakeFiles(), _FakeQueue(), clock)
    once.arm()
    stop = asyncio.Event()
    task = asyncio.create_task(once.run(stop, once=True))

    for _ in range(20):
        clock[0] += 49 * HOUR
        await asyncio.sleep(0.002)
    assert once.rounds == 0, "no ordinary cycle, however late it is"

    _catchup(store)
    await asyncio.wait_for(task, timeout=5)

    assert once.rounds == 1
    assert store.read_meta()[repo.CATCHUP_MARK] == repo.CATCHUP_DONE


async def test_the_one_time_mode_keeps_going_until_a_cycle_is_through(store: Store) -> None:
    _catchup(store)
    files = _FakeFiles(
        SliceResult(files=(a_row(10, etag="aaa"),)), SliceResult(unavailable=True), SliceResult(final=True)
    )
    once = _CountingReconcile(store, files, _FakeQueue(), [NOW])
    once._back_off = lambda: None  # type: ignore[method-assign]
    once.arm()

    await asyncio.wait_for(once.run(asyncio.Event(), once=True), timeout=5)

    assert once.rounds == 2
    assert store.read_meta()[repo.CATCHUP_MARK] == repo.CATCHUP_DONE


@pytest.mark.parametrize("mark", ["done"])
async def test_the_one_time_mode_on_a_finished_catch_up_does_nothing(store: Store, mark: str) -> None:
    _catchup(store, mark)
    once = _CountingReconcile(store, _FakeFiles(), _FakeQueue(), [NOW])
    once.arm()

    await asyncio.wait_for(once.run(asyncio.Event(), once=True), timeout=5)

    assert once.rounds == 0


async def test_the_one_time_mode_stays_silent_while_not_armed(store: Store) -> None:
    _catchup(store)
    clock = [NOW]
    once = _CountingReconcile(store, _FakeFiles(), _FakeQueue(), clock)
    stop = asyncio.Event()
    task = asyncio.create_task(once.run(stop, once=True))

    for _ in range(10):
        clock[0] += 49 * HOUR
        await asyncio.sleep(0.002)
    assert once.rounds == 0

    once.arm()
    await asyncio.wait_for(task, timeout=5)
    assert once.rounds == 1


async def test_an_ordinary_cycle_never_writes_the_catch_up_mark(store: Store) -> None:
    await _reconcile(store, _FakeFiles(SliceResult(final=True)), _FakeQueue()).run_once()

    assert repo.CATCHUP_MARK not in store.read_meta()


# -- the properties a grep has to keep --------------------------------------


def _php_source(path: Path) -> str:
    """One PHP file as text, and a missing one is red rather than green.

    The anti-vacuity clause every text gate of this project carries
    (docs/testing.md): a gate that silently passes because its source moved
    proves nothing at all.
    """
    assert path.is_file(), f"the gate looks for {path.name} and it is not there any more"
    return path.read_text(encoding="utf-8")


def test_the_give_up_rule_delivers_three_times_and_not_four() -> None:
    """The delivery count, pinned in the shape of the allowlist parity gate.

    The arithmetic is the part that was shifted by one before (phase 2 perf
    audit) and would be shifted again: the queue raises the counter in the claim
    itself, so the value the rule reads already includes the hand-out that is
    happening. Three deliveries therefore means "greater than three", and
    "greater or equal" would cut them to two.

    Read as text because a PHP constant cannot be imported, and read at all
    because this container is the half that lives with the consequence: a rule
    that never becomes final is a file this round requeues every night.
    """
    source = _php_source(PHP_QUEUE_SERVICE)

    limit = re.search(r"const MAX_DELIVERIES = (\d+);", source)
    assert limit is not None, "the delivery ceiling is no longer where this gate looks for it"
    assert int(limit.group(1)) == 3

    assert re.search(r"getRetries\(\) > self::MAX_DELIVERIES", source) is not None, (
        "the comparison has to be strictly greater than the ceiling, see the docblock of the constant"
    )
    # Never against a literal: the number standing in the condition is how the
    # ceiling and its docblock drifted apart in the first place.
    assert re.search(r"getRetries\(\) >=?\s*\d", source) is None


def test_a_row_that_is_given_up_costs_the_batch_no_slot_and_no_budget() -> None:
    # The second half of the same defect: the give-up claim used to be charged
    # against both ceilings of the batch, so a handful of permanently stuck
    # files made every round of real work smaller. The write-offs are therefore
    # decided before the row is charged, and the order is what this gate holds.
    source = _php_source(PHP_QUEUE_SERVICE)
    claim = source[source.index("public function claim(") : source.index("public function enqueue(")]

    assert claim.index("repeatedly_stuck") < claim.index("$rows--")
    # Since issue #14 the skipped reason of an undeliverable row comes out of
    # describe(), gone or unreadable, so the write-off carries a variable and
    # not the literal; the order it is held to is the same.
    assert claim.index("$this->finish($row, 'skipped', $source)") < claim.index("$budget = max(")


def test_the_slice_route_hands_the_verdict_over_with_the_page() -> None:
    # The channel this round's give-up rule stands on. One query per page and
    # never one per file: the walk works in bands, and a round trip per row
    # would cost more than the work the rule saves.
    source = _php_source(PHP_RECONCILE_CONTROLLER)

    assert "verdictsFor" in source
    assert re.search(r"private function withVerdicts\(array \$files\): array", source) is not None


def test_the_slice_route_marks_excluded_rows_with_the_codes_of_the_closed_list() -> None:
    # The channel the excluded branch of _compare stands on (owner decision of
    # 03.10.2026, part a). The codes are the two this module recognises, and the
    # findling_file_state verdict keeps travelling beside them.
    source = _php_source(PHP_RECONCILE_CONTROLLER)

    assert re.search(r"=\s*'skipped';", source) is not None
    assert re.search(r"=\s*'excluded';", source) is not None
    assert "withVerdicts" in source
    assert "isExcluded" in source


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
