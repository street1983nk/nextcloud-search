"""The one time catch-up after the upgrade to 1.5 (FMT-06, D-31-01, D-31-02).

Part A walks state.db and hands back, in bands, the rows 1.5 judges
differently: Word and Excel under an OOXML name that 1.4 called legacy_format,
every row of the six new types that is not indexed (the window in which a 1.5
companion queued them in front of a 1.4.2 container), and once every file
Nextcloud wrote off as repeatedly_stuck. Part B is one reconcile cycle that is
due at once and reads metadata only; it finds the files of the new types that
never had a row here, and the files Nextcloud wrote off after the last 1.4.2
cycle, which have no row here either.

Nothing in here may touch an indexed row, the index generation or a vector
mark: a catch-up that re-read the whole instance would cost a weak box days.
"""

from __future__ import annotations

import ast
import hashlib
import logging
import sqlite3
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from findling.extract.dispatch import ALLOWED_MIMETYPES
from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import FileRow, Mount, MountResult, SliceResult
from findling.nc.queue import KIND_CONTENT, CallResult, DocumentQueue, QueueStats
from findling.store.repo import (
    CATCHUP_DONE,
    CATCHUP_MARK,
    CATCHUP_RECONCILE,
    EMBEDDING_BACKLOG_MARK,
    RECHECK_MARK,
    FileMeta,
    Store,
    open_store,
)
from findling.worker import catchup as catchup_module
from findling.worker.catchup import NEW_MIMETYPES, catchup_step, select_catchup_candidates
from findling.worker.reconcile import GIVEN_UP_REASON, GIVEN_UP_STATE, REQUEUE_BAND, ROUND_WALKED, Reconcile

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

STORAGE = 3
ROOT = 17
NOW = 1_800_000_000.0
HOUR = 3600.0


class _Queue:
    """Records every requeue; answers not ok from the band number ``fail_at`` on."""

    def __init__(self, *, fail_at: int | None = None) -> None:
        self.requeues: list[tuple[list[int], str]] = []
        self.fail_at = fail_at

    async def requeue(self, file_ids: Sequence[int], *, kind: str) -> CallResult:
        self.requeues.append((list(file_ids), kind))
        if self.fail_at is not None and len(self.requeues) >= self.fail_at:
            return CallResult(ok=False)
        return CallResult(ok=True, count=len(file_ids))

    async def stats(self) -> QueueStats:
        return QueueStats(scheduled=0)

    def handed(self) -> list[int]:
        return [file_id for band, _ in self.requeues for file_id in band]


def _as_queue(queue: _Queue) -> DocumentQueue:
    return cast("DocumentQueue", queue)


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    # The 1.4 re-check is over on every stock this run meets in the field.
    opened.write_meta(RECHECK_MARK, "done")
    yield opened
    opened.close()


def _meta(path: str, mime: str = "application/pdf", etag: str | None = None) -> FileMeta:
    return FileMeta(
        storage_id=STORAGE,
        root_id=ROOT,
        path=path,
        title=path.rsplit("/", 1)[-1],
        mime=mime,
        size=1024,
        mtime=1_700_000_000,
        etag=etag,
    )


def _stuck(store: Store, file_id: int, path: str | None = None) -> None:
    store.record(file_id, _meta(path or f"files/doc-{file_id}.pdf"), "failed", "repeatedly_stuck")


def _digest(db: Path) -> str:
    """Every row and every meta value apart from the mark of this run, hashed."""
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute("SELECT * FROM files ORDER BY file_id").fetchall()
        meta = conn.execute("SELECT key, value FROM meta WHERE key != ? ORDER BY key", (CATCHUP_MARK,)).fetchall()
    finally:
        conn.close()
    return hashlib.sha256(repr((rows, meta)).encode()).hexdigest()


# -- the selection of part A ----------------------------------------------------


def test_word_and_excel_called_legacy_format_are_chosen_and_powerpoint_is_not() -> None:
    rows: list[tuple[int, str, str | None, str, str]] = [
        (1, "skipped", "legacy_format", "a/old.docx", DOCX),
        (2, "skipped", "legacy_format", "a/old.xlsx", XLSX),
        (3, "skipped", "legacy_format", "a/old.pptx", PPTX),
    ]

    assert select_catchup_candidates(rows) == [1, 2]


def test_the_codes_of_the_mixed_window_are_left_to_part_b() -> None:
    # system_file and unsupported_variant are right in state.db already; only
    # the Nextcloud row can be wrong, and only part B can see that row.
    rows: list[tuple[int, str, str | None, str, str]] = [
        (1, "skipped", "system_file", "a/._x.docx", DOCX),
        (2, "skipped", "unsupported_variant", "a/fax.tif", "image/tiff"),
    ]

    assert select_catchup_candidates(rows) == []


@pytest.mark.parametrize(
    ("path", "mime"),
    [
        ("a/mail.eml", "message/rfc822"),
        ("a/pack.zip", "application/zip"),
        ("a/brief.doc", "application/msword"),
        ("a/tabelle.xls", "application/vnd.ms-excel"),
        ("a/foto.heic", "image/heic"),
        ("a/foto.heif", "image/heif"),
    ],
)
def test_a_new_type_a_1_4_2_container_refused_is_chosen(path: str, mime: str) -> None:
    assert select_catchup_candidates([(1, "skipped", "mime_not_allowed", path, mime)]) == [1]


@pytest.mark.parametrize("path", ["a/mail.eml", "a/pack.zip", "a/brief.doc", "a/vorlage.dot", "a/t.xls", "a/t.xlt"])
def test_without_a_stored_mimetype_the_extension_decides(path: str) -> None:
    assert select_catchup_candidates([(1, "failed", "corrupt", path, "")]) == [1]


def test_a_failed_new_type_is_chosen_as_well() -> None:
    assert select_catchup_candidates([(1, "failed", "corrupt", "a/pack.zip", "application/zip")]) == [1]


def test_every_file_written_off_as_repeatedly_stuck_is_chosen() -> None:
    rows: list[tuple[int, str, str | None, str, str]] = [
        (1, "failed", "repeatedly_stuck", "a/report.pdf", "application/pdf"),
        # A give-up row of the reconcile carries no path, only the mimetype.
        (2, "failed", "repeatedly_stuck", "", "text/plain"),
    ]

    assert select_catchup_candidates(rows) == [1, 2]


def test_what_1_5_judges_the_same_stays_where_it_is() -> None:
    rows: list[tuple[int, str, str | None, str, str]] = [
        (1, "indexed", None, "a/brief.doc", "application/msword"),
        (2, "failed", "corrupt", "a/report.pdf", "application/pdf"),
        (3, "skipped", "too_large", "a/big.pdf", "application/pdf"),
        (4, "skipped", "mime_not_allowed", "a/movie.mp4", "video/mp4"),
        (5, "failed", "ocr_failed", "a/scan.pdf", "application/pdf"),
        (6, "indexed", None, "a/foto.heic", "image/heic"),
    ]

    assert select_catchup_candidates(rows) == []


def test_the_six_new_types_are_types_the_allowlist_reads() -> None:
    assert len(NEW_MIMETYPES) == 6
    assert set(ALLOWED_MIMETYPES) >= NEW_MIMETYPES


# -- bands, cursor and marks of part A -------------------------------------------


async def test_450_candidates_travel_in_three_bands_of_content(store: Store) -> None:
    for file_id in range(1, 451):
        _stuck(store, file_id)
    queue = _Queue()

    finished = await catchup_step(store, _as_queue(queue))

    assert finished is True
    assert [len(band) for band, _ in queue.requeues] == [200, 200, 50]
    assert {kind for _, kind in queue.requeues} == {KIND_CONTENT}
    assert all(len(band) <= REQUEUE_BAND for band, _ in queue.requeues)
    assert queue.handed() == list(range(1, 451))


async def test_after_part_a_the_mark_asks_for_the_cycle_and_is_not_done(store: Store) -> None:
    _stuck(store, 1)

    await catchup_step(store, _as_queue(_Queue()))

    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_RECONCILE


async def test_a_failed_band_ends_the_run_and_the_next_one_resumes_behind_band_one(store: Store) -> None:
    for file_id in range(1, 451):
        _stuck(store, file_id)

    assert await catchup_step(store, _as_queue(_Queue(fail_at=2))) is False
    assert store.read_meta()[CATCHUP_MARK] == "200"

    retry = _Queue()
    assert await catchup_step(store, _as_queue(retry)) is True
    assert retry.handed() == list(range(201, 451))


async def test_a_new_process_resumes_at_the_cursor(store: Store, tmp_path: Path) -> None:
    for file_id in range(1, 451):
        _stuck(store, file_id)
    await catchup_step(store, _as_queue(_Queue(fail_at=3)))
    store.close()

    fresh = open_store(tmp_path / "state.db")
    try:
        queue = _Queue()
        assert await catchup_step(fresh, _as_queue(queue)) is True
        assert queue.handed() == list(range(401, 451))
    finally:
        fresh.close()


async def test_a_hand_edited_cursor_starts_from_zero(store: Store) -> None:
    _stuck(store, 1)
    _stuck(store, 2)
    store.write_meta(CATCHUP_MARK, "abc")
    queue = _Queue()

    assert await catchup_step(store, _as_queue(queue)) is True

    assert queue.requeues == [([1, 2], KIND_CONTENT)]


async def test_part_a_waits_for_the_re_check_of_1_4(store: Store) -> None:
    _stuck(store, 1)
    store.write_meta(RECHECK_MARK, "17")
    queue = _Queue()

    assert await catchup_step(store, _as_queue(queue)) is False

    assert queue.requeues == []
    assert CATCHUP_MARK not in store.read_meta()


async def test_part_a_does_nothing_once_it_is_over(store: Store) -> None:
    _stuck(store, 1)
    for mark in (CATCHUP_RECONCILE, CATCHUP_DONE):
        store.write_meta(CATCHUP_MARK, mark)
        queue = _Queue()

        assert await catchup_step(store, _as_queue(queue)) is True

        assert queue.requeues == []
        assert store.read_meta()[CATCHUP_MARK] == mark


async def test_deleted_rows_stay_where_they_are(store: Store) -> None:
    _stuck(store, 1)
    store.tombstone(1)
    store.record(2, _meta("a/pack.zip", "application/zip"), "skipped", "mime_not_allowed")
    queue = _Queue()

    await catchup_step(store, _as_queue(queue))

    assert queue.requeues == [([2], KIND_CONTENT)]


async def test_part_a_leaves_the_stock_byte_for_byte(store: Store, tmp_path: Path) -> None:
    store.record(1, _meta("a/report.pdf", etag="e1"), "indexed", content_hash="abc", text_chars=3)
    store.record(2, _meta("a/brief.doc", "application/msword", etag="e2"), "indexed", content_hash="d", text_chars=3)
    store.record(3, _meta("a/old.docx", DOCX, etag="e3"), "skipped", "legacy_format")
    store.record(4, _meta("a/pack.zip", "application/zip", etag="e4"), "skipped", "mime_not_allowed")
    _stuck(store, 5)
    store.write_meta(EMBEDDING_BACKLOG_MARK, "")
    before = _digest(tmp_path / "state.db")

    await catchup_step(store, _as_queue(_Queue()))

    assert _digest(tmp_path / "state.db") == before


async def test_the_log_carries_numbers_and_no_path(store: Store, caplog: pytest.LogCaptureFixture) -> None:
    store.record(1, _meta("Vertraege/geheim/Kuendigung.eml", "message/rfc822"), "skipped", "mime_not_allowed")
    _stuck(store, 2, path="Vertraege/geheim/Kuendigung.pdf")
    caplog.set_level(logging.INFO, logger="findling.worker.catchup")

    await catchup_step(store, _as_queue(_Queue(fail_at=1)))
    await catchup_step(store, _as_queue(_Queue()))

    lines = [record.getMessage() for record in caplog.records if record.name == "findling.worker.catchup"]
    assert lines
    assert all("Vertraege" not in line and "Kuendigung" not in line for line in lines)
    assert any("handed 2 files back in 1 bands" in line for line in lines)


def test_the_band_is_the_one_of_the_reconcile() -> None:
    # Imported, not copied: the PHP controller refuses a list over 256 whole
    # (T-31-35). An identity check alone proves nothing for 200, which CPython
    # caches as one object, so the module may not assign the name itself.
    tree = ast.parse(Path(catchup_module.__file__).read_text(encoding="utf-8"))
    assigned = [
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign | ast.AnnAssign)
        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(target, ast.Name)
    ]

    assert "REQUEUE_BAND" not in assigned
    assert catchup_module.REQUEUE_BAND is REQUEUE_BAND


# -- part B, end to end against a real state database -----------------------------


class _Files:
    """One mount and a scripted sequence of pages."""

    def __init__(self, *pages: SliceResult) -> None:
        self._pages = list(pages)

    async def mounts(self) -> MountResult:
        return MountResult(mounts=(Mount(storage_id=STORAGE, root_id=ROOT, overridden_root=ROOT + 1),))

    async def page(self, *, storage: int, root: int, after: int, limit: int) -> SliceResult:
        del storage, root, after, limit
        return self._pages.pop(0) if self._pages else SliceResult(final=True)


def _reconcile(store: Store, files: _Files, queue: _Queue, *, now: float = NOW) -> Reconcile:
    return Reconcile(
        store=store,
        client_factory=lambda: cast("AsyncNextcloudApp", None),
        files_factory=lambda nc: cast("Any", files),
        queue_factory=lambda nc: cast("Any", queue),
        slice_size=50,
        quiet_max=100,
        hour=2,
        min_interval_hours=24,
        pause_seconds=0.0,
        clock=lambda: now,
        hour_of=lambda: 9,
    )


def _written_off(file_id: int) -> FileRow:
    return FileRow(
        file_id=file_id,
        etag="aaa",
        size=1024,
        mtime=1_700_000_000,
        mime="application/pdf",
        state=GIVEN_UP_STATE,
        reason=GIVEN_UP_REASON,
    )


async def test_a_file_written_off_after_the_last_1_4_2_cycle_comes_back_exactly_once(store: Store) -> None:
    # The stock 1.4.2 leaves behind: Nextcloud wrote file 10 off as
    # repeatedly_stuck after the last cycle of 1.4.2, so this container has no
    # row for it.
    store.set_reconcile_cursor(STORAGE, 0, finished=True, at=int(NOW - HOUR))
    part_a = _Queue()

    assert await catchup_step(store, _as_queue(part_a)) is True
    assert part_a.requeues == []

    part_b = _Queue()
    walked = await _reconcile(store, _Files(SliceResult(files=(_written_off(10),), final=True)), part_b).run_once()

    assert walked.state == ROUND_WALKED
    assert part_b.handed() == [10]
    assert store.file_row(10) is None
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_DONE

    # It failed again, Nextcloud wrote it off again: the next ordinary cycle
    # writes it off here as well, as before 1.5 (IN-03).
    later = _Queue()
    regular = await _reconcile(
        store, _Files(SliceResult(files=(_written_off(10),), final=True)), later, now=NOW + 49 * HOUR
    ).run_once()

    assert regular.state == ROUND_WALKED
    assert later.requeues == []
    assert regular.given_up == 1
    row = store.file_row(10)
    assert row is not None
    assert (row["state"], row["reason"]) == (GIVEN_UP_STATE, GIVEN_UP_REASON)


async def test_a_fresh_install_reaches_done_with_its_first_cycle_and_no_extra_one(store: Store) -> None:
    queue = _Queue()

    assert await catchup_step(store, _as_queue(queue)) is True
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_RECONCILE

    first = await _reconcile(store, _Files(SliceResult(final=True)), queue).run_once()
    second = await _reconcile(store, _Files(SliceResult(final=True)), queue, now=NOW + HOUR).run_once()

    assert first.state == ROUND_WALKED
    assert store.read_meta()[CATCHUP_MARK] == CATCHUP_DONE
    assert second.state != ROUND_WALKED
    assert queue.requeues == []
    assert await catchup_step(store, _as_queue(queue)) is True
    assert queue.requeues == []


async def test_the_catch_up_cycle_leaves_every_known_row_byte_for_byte(store: Store, tmp_path: Path) -> None:
    store.record(1, _meta("a/report.pdf", etag="e1"), "indexed", content_hash="abc", text_chars=3)
    store.record(2, _meta("a/scan.pdf", etag="e2"), "skipped", "too_large")
    await catchup_step(store, _as_queue(_Queue()))
    before = _digest(tmp_path / "state.db")
    rows = (
        FileRow(file_id=1, etag="e1", size=1024, mtime=1_700_000_000, mime="application/pdf", state="", reason=""),
        FileRow(file_id=2, etag="e2", size=1024, mtime=1_700_000_000, mime="application/pdf", state="", reason=""),
        FileRow(file_id=3, etag="e3", size=1024, mtime=1_700_000_000, mime="message/rfc822", state="", reason=""),
    )
    queue = _Queue()

    await _reconcile(store, _Files(SliceResult(files=rows, final=True)), queue).run_once()

    assert queue.handed() == [3]
    assert _digest(tmp_path / "state.db") == before
