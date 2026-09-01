"""The state database: opening it, splitting read from write, and the version marks.

The predecessor this project replaces died because nobody could say why a
document was not findable. That answer lives in this database, so the tests here
are about the properties that keep the answer trustworthy rather than about SQL.

Three of them are worth naming up front:

* ``open_store`` never overwrites a meta value it finds. The whole point of the
  version marks is to notice that the analyzer changed while the index did not,
  and a store that helpfully "repairs" the value on open destroys the evidence.
* the read connection refuses writes. A bug in the search path must not be able
  to change the operating state, and that is a structural property here, not a
  review habit.
* a journal mode other than WAL is a warning and not an error. WAL needs shared
  memory, some network file systems do not have it, and a container that refuses
  to start there would be a worse outcome than a slower one.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

from findling.store.repo import (
    SCHEMA_VERSION,
    STATE_REASONS,
    UNKNOWN_VERSION,
    FileMeta,
    Store,
    enable_wal,
    open_read_only,
    open_store,
)


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


def a_file(file_id: int = 1) -> FileMeta:
    """The metadata one crawled file arrives with. Values are irrelevant here."""
    return FileMeta(
        storage_id=2,
        root_id=3,
        path=f"files/report-{file_id}.pdf",
        title=f"report-{file_id}.pdf",
        mime="application/pdf",
        size=1024,
        mtime=1_700_000_000,
    )


def test_open_store_creates_the_database_and_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "state.db"

    first = open_store(path)
    first.write_meta("marker", "kept")
    first.close()

    second = open_store(path)
    try:
        assert path.exists()
        assert second.read_meta()["marker"] == "kept"
    finally:
        second.close()


def test_journal_mode_is_wal_after_open(store: Store) -> None:
    assert store.journal_mode == "wal"


def test_a_journal_mode_other_than_wal_warns_and_does_not_raise(caplog: pytest.LogCaptureFixture) -> None:
    # An in-memory database is the honest stand-in for a file system without
    # shared memory: it answers "memory" to the same pragma a network share
    # would answer "delete" to. Either way the container has to keep running.
    connection = sqlite3.connect(":memory:", autocommit=True)
    try:
        with caplog.at_level(logging.WARNING, logger="findling.store.repo"):
            mode = enable_wal(connection)
    finally:
        connection.close()

    assert mode != "wal"
    assert "journal_mode" in caplog.text


def test_the_read_connection_refuses_a_write(tmp_path: Path) -> None:
    path = tmp_path / "state.db"
    writer = open_store(path)
    writer.close()

    reader = open_read_only(path)
    try:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            reader.write_meta("schema_version", "999")
    finally:
        reader.close()


def test_the_read_connection_can_read(tmp_path: Path) -> None:
    path = tmp_path / "state.db"
    writer = open_store(path)
    writer.write_meta("wordlist_hash", "cafebabe")
    writer.close()

    reader = open_read_only(path)
    try:
        assert reader.read_meta()["wordlist_hash"] == "cafebabe"
    finally:
        reader.close()


def test_open_read_only_on_a_missing_file_raises(tmp_path: Path) -> None:
    # Without this the connect call would create an empty database and every
    # search would answer "no results" instead of "the state is gone".
    with pytest.raises(FileNotFoundError):
        open_read_only(tmp_path / "absent.db")


def test_meta_carries_the_version_marks_after_the_first_open(store: Store) -> None:
    meta = store.read_meta()

    assert meta["schema_version"] == SCHEMA_VERSION
    assert meta["index_version"] == "0"
    assert meta["analyzer_version"] == UNKNOWN_VERSION
    assert meta["tantivy_version"] == UNKNOWN_VERSION
    assert int(meta["created_at"]) > 0


def test_open_store_seeds_the_marks_the_caller_names(tmp_path: Path) -> None:
    opened = open_store(tmp_path / "state.db", meta={"analyzer_version": "3", "wordlist_hash": "abc"})
    try:
        assert opened.version_mismatch({"analyzer_version": "3", "wordlist_hash": "abc"}) == []
    finally:
        opened.close()


def test_open_store_never_overwrites_an_existing_mark(tmp_path: Path) -> None:
    # The load bearing one. If a second open silently wrote the new analyzer
    # version, the mismatch it is supposed to reveal would be gone by the time
    # anybody looks.
    path = tmp_path / "state.db"
    first = open_store(path, meta={"analyzer_version": "3"})
    first.close()

    second = open_store(path, meta={"analyzer_version": "4"})
    try:
        assert second.read_meta()["analyzer_version"] == "3"
        assert second.version_mismatch({"analyzer_version": "4"}) == ["analyzer_version"]
    finally:
        second.close()


def test_version_mismatch_names_only_the_diverging_keys(store: Store) -> None:
    store.write_meta("analyzer_version", "7")
    store.write_meta("tantivy_version", "0.26.0")

    expected = {"analyzer_version": "8", "tantivy_version": "0.26.0", "schema_version": SCHEMA_VERSION}

    assert store.version_mismatch(expected) == ["analyzer_version"]


def test_version_mismatch_reports_a_mark_that_was_never_written(store: Store) -> None:
    assert store.version_mismatch({"embedding_version": "1"}) == ["embedding_version"]


def test_version_mismatch_is_empty_when_everything_matches(store: Store) -> None:
    assert store.version_mismatch(store.read_meta()) == []


def test_a_generation_raised_past_the_baseline_is_not_a_drift(store: Store) -> None:
    # A lost index directory raises the local generation to force a reindex;
    # that is a healthy state and must not read as reindexRequired forever.
    store.write_meta("index_version", "3")

    assert store.version_mismatch({"index_version": "1"}) == []


def test_a_generation_behind_the_baseline_is_a_drift(store: Store) -> None:
    store.write_meta("index_version", "1")

    assert store.version_mismatch({"index_version": "2"}) == ["index_version"]


def test_an_unreadable_generation_is_a_drift(store: Store) -> None:
    store.write_meta("index_version", "unknown")

    assert store.version_mismatch({"index_version": "1"}) == ["index_version"]


def test_record_writes_state_and_reason_and_stamps_the_verdict(store: Store) -> None:
    store.record(7, a_file(7), "skipped", "too_large")

    row = store.file_row(7)

    assert row is not None
    assert row["state"] == "skipped"
    assert row["reason"] == "too_large"
    assert row["indexed_at"] > 0
    assert row["path"] == "files/report-7.pdf"


def test_indexed_carries_no_reason_and_may_carry_truncated(store: Store) -> None:
    store.record(1, a_file(1), "indexed", content_hash="abc", text_chars=42)
    store.record(2, a_file(2), "indexed", "truncated", content_hash="def", text_chars=524_288)

    assert store.counts()["indexed"] == 2
    assert store.reasons_by_state()["indexed"] == {None: 1, "truncated": 1}


def test_a_reason_outside_the_closed_list_is_rejected(store: Store) -> None:
    # The reason codes are rendered on an admin page in phase 4. Free text is the
    # shortest path to a file name standing in a place where no file name may
    # stand, so the store refuses it rather than trusting every caller.
    with pytest.raises(ValueError, match="reason"):
        store.record(1, a_file(1), "failed", "could not read /files/anna/Kuendigung.pdf")

    assert store.file_row(1) is None


def test_a_reason_that_does_not_fit_its_state_is_rejected(store: Store) -> None:
    # too_large is a decision not to index, never an attempt that went wrong.
    # Mixing the two would make the failure counter of the status page lie.
    with pytest.raises(ValueError, match="reason"):
        store.record(1, a_file(1), "failed", "too_large")

    assert store.file_row(1) is None


def test_an_unknown_state_is_rejected(store: Store) -> None:
    with pytest.raises(ValueError, match="state"):
        store.record(1, a_file(1), "pending")


def test_skipped_and_failed_need_a_reason(store: Store) -> None:
    with pytest.raises(ValueError, match="reason"):
        store.record(1, a_file(1), "skipped")
    with pytest.raises(ValueError, match="reason"):
        store.record(2, a_file(2), "failed")


def test_no_text_layer_is_a_skip_and_the_bridge_to_phase_three(store: Store) -> None:
    # Without this reason phase 3 would need a full reindex just to learn which
    # PDFs need OCR.
    store.record(1, a_file(1), "skipped", "no_text_layer")

    assert "no_text_layer" in STATE_REASONS["skipped"]
    assert store.reasons_by_state()["skipped"] == {"no_text_layer": 1}


def test_counts_names_every_state_even_the_empty_ones(store: Store) -> None:
    # A missing key in a status output is the kind of gap where zero and error
    # look the same.
    store.record(1, a_file(1), "failed", "corrupt")

    assert store.counts() == {"indexed": 0, "skipped": 0, "failed": 1}


def test_reasons_by_state_breaks_the_counters_down(store: Store) -> None:
    store.record(1, a_file(1), "failed", "corrupt")
    store.record(2, a_file(2), "failed", "corrupt")
    store.record(3, a_file(3), "failed", "timeout")

    assert store.reasons_by_state()["failed"] == {"corrupt": 2, "timeout": 1}
    assert store.reasons_by_state()["skipped"] == {}


def test_record_increments_attempts(store: Store) -> None:
    # The data behind giving up after three tries.
    store.record(1, a_file(1), "failed", "gateway_error")
    store.record(1, a_file(1), "failed", "gateway_error")

    row = store.file_row(1)

    assert row is not None
    assert row["attempts"] == 2


def test_is_unchanged_is_true_for_the_same_hash_in_state_indexed(store: Store) -> None:
    store.record(1, a_file(1), "indexed", content_hash="cafe")

    assert store.is_unchanged(1, "cafe") is True
    assert store.is_unchanged(1, "beef") is False


def test_is_unchanged_is_false_for_an_unknown_file_and_an_unknown_hash(store: Store) -> None:
    assert store.is_unchanged(404, "cafe") is False

    store.record(1, a_file(1), "indexed", content_hash=None)

    assert store.is_unchanged(1, "cafe") is False


def test_is_unchanged_is_false_for_a_file_that_was_not_indexed(store: Store) -> None:
    store.record(1, a_file(1), "failed", "gateway_error", content_hash="cafe")

    assert store.is_unchanged(1, "cafe") is False


def test_is_unchanged_is_false_after_the_index_version_moved(store: Store) -> None:
    # Same bytes, different analyzer. Answering True here would let an index
    # version bump skip every file it was raised to rebuild.
    store.record(1, a_file(1), "indexed", content_hash="cafe")
    store.write_meta("index_version", "2")

    assert store.is_unchanged(1, "cafe") is False


def test_reset_for_reindex_removes_only_the_stale_rows(store: Store) -> None:
    store.record(1, a_file(1), "indexed", content_hash="cafe")
    store.write_meta("index_version", "2")
    store.record(2, a_file(2), "indexed", content_hash="beef")

    removed = store.reset_for_reindex(2)

    assert removed == 1
    assert store.file_row(1) is None
    assert store.file_row(2) is not None


def test_tombstone_marks_the_file_as_deleted_and_keeps_the_verdict_readable(store: Store) -> None:
    # The row stays. Phase 4 has to be able to say "it was there and it is gone",
    # and a deleted row could only say "never heard of it".
    store.record(1, a_file(1), "indexed", content_hash="cafe")

    marked = store.tombstone(1, 1_700_000_500)

    row = store.file_row(1)
    assert marked == 1
    assert row is not None
    assert row["deleted_at"] == 1_700_000_500
    assert (row["state"], row["reason"]) == ("indexed", None)
    assert row["attempts"] == 1


def test_a_tombstone_stamps_the_current_time_when_none_is_given(store: Store) -> None:
    store.record(1, a_file(1), "indexed", content_hash="cafe")

    store.tombstone(1)

    row = store.file_row(1)
    assert row is not None
    assert row["deleted_at"] > 0


def test_a_file_with_a_tombstone_is_not_unchanged(store: Store) -> None:
    # The condition that makes the tombstone work at all. Same bytes, same
    # generation, and still work to do: without it a deleted file would look
    # unchanged forever and no requeue could ever touch it again.
    store.record(1, a_file(1), "indexed", content_hash="cafe")
    assert store.is_unchanged(1, "cafe") is True

    store.tombstone(1, 1_700_000_500)

    assert store.is_unchanged(1, "cafe") is False


def test_recording_a_file_again_lifts_its_tombstone(store: Store) -> None:
    # The restore from the trash bin, seen from this side. It is the ordinary
    # upsert and not a method of its own: a file that is being judged again is by
    # definition not deleted, and a second entry point would be a second place
    # that has to remember to clear the mark.
    store.record(1, a_file(1), "indexed", content_hash="cafe")
    store.tombstone(1, 1_700_000_500)

    store.record(1, a_file(1), "indexed", content_hash="cafe")

    row = store.file_row(1)
    assert row is not None
    assert row["deleted_at"] is None
    assert store.is_unchanged(1, "cafe") is True


def test_a_tombstone_on_a_file_that_was_never_judged_changes_nothing(store: Store) -> None:
    # Not an error. A file nobody ever looked at has nothing to remember, and a
    # delete job carries no proof that the file was ever indexed.
    assert store.tombstone(4711) == 0
    assert store.file_row(4711) is None


def test_record_mount_mirrors_the_crawl_progress(store: Store) -> None:
    # A mirror for the display. The original of the cursor lives in the argument
    # of the next background job in Nextcloud.
    store.record_mount(2, 3, 900, 120)
    store.record_mount(2, 3, 1800, 240)

    assert store.mount_rows() == [{"storage_id": 2, "root_id": 3, "cursor_file_id": 1800, "files_seen": 240}]


def test_the_connection_may_cross_a_worker_thread(store: Store) -> None:
    """The property the indexing worker rests on, checked rather than assumed.

    The worker writes its verdicts in ``asyncio.to_thread``, because a blocking
    SQLite transaction on the event loop is a ``/heartbeat`` that hangs while
    ``/enabled`` still answers. That only holds while the connection may be used
    from another thread, so the guard is off and the library serialises instead.
    A build that reports less than serialised mode would make the poller unsafe
    in a way nothing else would notice, hence this tripwire.
    """
    written: list[dict[str, object] | None] = []

    def write_from_another_thread() -> None:
        store.record(4711, a_file(4711), "indexed", content_hash="cafe")
        written.append(store.file_row(4711))

    assert sqlite3.threadsafety == 3
    worker = threading.Thread(target=write_from_another_thread)
    worker.start()
    worker.join()

    assert len(written) == 1
    assert written[0] is not None
