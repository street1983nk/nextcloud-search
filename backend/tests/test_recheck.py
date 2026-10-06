"""The re-check of the old stock after the upgrade to 1.4.0 (D-29-10, REL-04).

The release promised publicly that the files of the fix classes are "re-checked
after the upgrade, no manual cleanup". These tests hold the promise to its
shape: the selection reads the real codes in state.db, the handover travels in
bands below the list ceiling of the PHP controller, the cursor moves only after
a band really arrived, and the run ends in a mark that keeps it from ever
coming back. Nothing here may touch the index generation or the vector marks,
because a re-check that triggered a full reindex would cost a weak box days.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from findling.nc.queue import KIND_CONTENT, CallResult, DocumentQueue
from findling.store.repo import EMBEDDING_BACKLOG_MARK, RECHECK_MARK, FileMeta, Store, open_store
from findling.worker.reconcile import REQUEUE_BAND
from findling.worker.recheck import recheck_step, select_candidates


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


def _as_queue(queue: _Queue) -> DocumentQueue:
    return cast("DocumentQueue", queue)


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


def _meta(path: str) -> FileMeta:
    return FileMeta(
        storage_id=2,
        root_id=3,
        path=path,
        title=path.rsplit("/", 1)[-1],
        mime="application/pdf",
        size=1024,
        mtime=1_700_000_000,
    )


def _failed(store: Store, file_id: int, reason: str = "corrupt", path: str | None = None) -> None:
    store.record(file_id, _meta(path or f"files/doc-{file_id}.pdf"), "failed", reason)


# -- the selection ------------------------------------------------------------


def test_select_candidates_takes_the_fix_classes_and_every_sidecar_name() -> None:
    rows: list[tuple[int, str, str | None, str]] = [
        (1, "failed", "corrupt", "a/report.pdf"),
        (2, "failed", "out_of_memory", "a/scan.jpg"),
        (3, "skipped", "system_file", "a/x.docx"),
        (4, "skipped", "legacy_format", "a/old.xlsx"),
        (5, "skipped", "unsupported_variant", "a/fax.tif"),
        (6, "indexed", None, "a/._x.docx"),
        (7, "skipped", "mime_not_allowed", "a/~$Bericht.docx"),
        (8, "failed", "ocr_failed", "a/scan.pdf"),
        (9, "indexed", None, "a/report.pdf"),
        (10, "indexed", None, "a/.hidden"),
        (11, "indexed", None, "a/a._b"),
        (12, "failed", "timeout", "a/big.pdf"),
        (13, "skipped", "mime_not_allowed", "a/movie.mp4"),
        (14, "indexed", None, "a/._dir/real.pdf"),
    ]

    assert select_candidates(rows) == [1, 2, 3, 4, 5, 6, 7]


def test_ocr_failed_is_never_selected() -> None:
    # Research Open Question 4: an engine failure is not one of the fixed
    # classes, re-running it would only burn OCR time for the same verdict.
    assert select_candidates([(8, "failed", "ocr_failed", "a/scan.pdf")]) == []


# -- bands and cursor ---------------------------------------------------------


async def test_450_candidates_travel_in_three_bands_of_content(store: Store) -> None:
    for file_id in range(1, 451):
        _failed(store, file_id)
    queue = _Queue()

    finished = await recheck_step(store, _as_queue(queue))

    assert finished is True
    assert [len(band) for band, _ in queue.requeues] == [200, 200, 50]
    assert {kind for _, kind in queue.requeues} == {KIND_CONTENT}
    assert all(len(band) <= REQUEUE_BAND for band, _ in queue.requeues)
    assert [file_id for band, _ in queue.requeues for file_id in band] == list(range(1, 451))
    assert store.read_meta()[RECHECK_MARK] == "done"


async def test_a_failed_band_ends_the_run_and_the_next_one_resumes_behind_band_one(store: Store) -> None:
    for file_id in range(1, 451):
        _failed(store, file_id)
    queue = _Queue(fail_at=2)

    finished = await recheck_step(store, _as_queue(queue))

    assert finished is False
    assert store.read_meta()[RECHECK_MARK] == "200"

    retry = _Queue()
    assert await recheck_step(store, _as_queue(retry)) is True
    assert retry.requeues[0][0][0] == 201
    assert [len(band) for band, _ in retry.requeues] == [200, 50]


async def test_a_new_process_resumes_at_the_cursor(store: Store, tmp_path: Path) -> None:
    for file_id in range(1, 451):
        _failed(store, file_id)
    await recheck_step(store, _as_queue(_Queue(fail_at=3)))
    store.close()

    fresh = open_store(tmp_path / "state.db")
    try:
        queue = _Queue()
        assert await recheck_step(fresh, _as_queue(queue)) is True
        assert [file_id for band, _ in queue.requeues for file_id in band] == list(range(401, 451))
    finally:
        fresh.close()


async def test_after_done_the_run_never_hands_anything_over_again(store: Store) -> None:
    _failed(store, 1)
    await recheck_step(store, _as_queue(_Queue()))
    _failed(store, 2)
    queue = _Queue()

    for _ in range(3):
        assert await recheck_step(store, _as_queue(queue)) is True

    assert queue.requeues == []
    assert store.read_meta()[RECHECK_MARK] == "done"


async def test_a_fresh_install_without_candidates_writes_done_in_one_call(store: Store) -> None:
    store.record(1, _meta("a/report.pdf"), "indexed", content_hash="abc", text_chars=3)
    queue = _Queue()

    assert await recheck_step(store, _as_queue(queue)) is True

    assert queue.requeues == []
    assert store.read_meta()[RECHECK_MARK] == "done"


async def test_a_hand_edited_cursor_starts_from_zero(store: Store) -> None:
    _failed(store, 1)
    _failed(store, 2)
    store.write_meta(RECHECK_MARK, "abc")
    queue = _Queue()

    assert await recheck_step(store, _as_queue(queue)) is True

    assert queue.requeues == [([1, 2], KIND_CONTENT)]


async def test_deleted_rows_and_documents_stay_where_they_are(store: Store) -> None:
    _failed(store, 1)
    store.tombstone(1)
    store.record(2, _meta("a/report.pdf"), "indexed", content_hash="abc", text_chars=3)
    store.record(3, _meta("a/._x.docx"), "indexed", content_hash="def", text_chars=3)
    queue = _Queue()

    await recheck_step(store, _as_queue(queue))

    assert queue.requeues == [([3], KIND_CONTENT)]


async def test_the_index_generation_and_the_vector_marks_stay_untouched(store: Store) -> None:
    for file_id in range(1, 6):
        _failed(store, file_id)
    store.record(6, replace(_meta("a/._x.docx")), "indexed", content_hash="abc", text_chars=3)
    before = store.read_meta()
    versions_before = store.verdicts_older_than(10**9)

    await recheck_step(store, _as_queue(_Queue()))

    after = store.read_meta()
    assert after.pop(RECHECK_MARK) == "done"
    assert after == before
    assert after.get(EMBEDDING_BACKLOG_MARK, "") == before.get(EMBEDDING_BACKLOG_MARK, "")
    assert store.verdicts_older_than(10**9) == versions_before


async def test_the_log_carries_numbers_and_no_path(store: Store, caplog: pytest.LogCaptureFixture) -> None:
    _failed(store, 1, path="Vertraege/geheim/._Kuendigung.docx")
    _failed(store, 2, path="Vertraege/geheim/Kuendigung.pdf")
    caplog.set_level(logging.INFO, logger="findling.worker.recheck")

    await recheck_step(store, _as_queue(_Queue(fail_at=1)))
    await recheck_step(store, _as_queue(_Queue()))

    lines = [record.getMessage() for record in caplog.records if record.name == "findling.worker.recheck"]
    assert lines
    assert all("Vertraege" not in line and "Kuendigung" not in line for line in lines)
    assert any("re-checked 2 files of the fix classes in 1 bands" in line for line in lines)


def test_the_band_is_the_one_of_the_reconcile() -> None:
    # Imported, not copied: the PHP controller refuses a list over 256 whole
    # (T-29-29), and the parity test of the reconcile holds REQUEUE_BAND to it.
    from findling.worker import recheck  # noqa: PLC0415

    assert cast("Any", recheck).REQUEUE_BAND is REQUEUE_BAND
