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
import time
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from findling.store.repo import (
    _ACL_DOCUMENTS_SQL,
    _ACL_ROWS_SQL,
    _DEFAULT_META,
    EMBEDDING_MARK,
    SCHEMA_VERSION,
    STATE_REASONS,
    STORE_SCHEMA_MARK,
    UNKNOWN_VERSION,
    VECTOR_ONLY_MARKS,
    FileMeta,
    Store,
    enable_wal,
    index_bytes,
    open_read_only,
    open_store,
)


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


def a_file(file_id: int = 1, *, storage_id: int = 2, etag: str | None = None) -> FileMeta:
    """The metadata one crawled file arrives with. Values are irrelevant here.

    ``storage_id`` and ``etag`` are keyword arguments with the values every older
    test in this file relied on, so the reconcile tests below can vary the two
    fields their comparison runs on without touching a single existing case.
    """
    return FileMeta(
        storage_id=storage_id,
        root_id=3,
        path=f"files/report-{file_id}.pdf",
        title=f"report-{file_id}.pdf",
        mime="application/pdf",
        size=1024,
        mtime=1_700_000_000,
        etag=etag,
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

    assert meta[STORE_SCHEMA_MARK] == SCHEMA_VERSION
    assert meta["index_version"] == "0"
    assert meta["analyzer_version"] == UNKNOWN_VERSION
    assert meta["tantivy_version"] == UNKNOWN_VERSION
    assert int(meta["created_at"]) > 0


def test_only_the_layout_of_this_file_is_seeded_with_a_value_of_its_own() -> None:
    # The one number this module owns is the layout of schema.sql. The tantivy
    # schema layout, the analyzer, the word list and the tantivy release belong
    # to the index side, so a database created without being told carries the
    # placeholder for them and reads as a divergence on the next comparison.
    # Before phase 6 the two schema numbers shared one key and happened to be
    # equal; raising this one under that key would have claimed a new tantivy
    # layout and forced exactly the reindex D-21 rules out.
    assert _DEFAULT_META[STORE_SCHEMA_MARK] == SCHEMA_VERSION
    assert _DEFAULT_META["schema_version"] == UNKNOWN_VERSION
    assert _DEFAULT_META[EMBEDDING_MARK] == UNKNOWN_VERSION


def test_the_embedding_mark_is_a_vector_mark_and_the_others_are_not(store: Store) -> None:
    # The split the callers ask about. A drift of the embedding mark is a real
    # difference with a different remedy: the vector stock is recomputed and the
    # tantivy index is not touched.
    assert EMBEDDING_MARK in VECTOR_ONLY_MARKS
    assert VECTOR_ONLY_MARKS.isdisjoint(
        {"schema_version", STORE_SCHEMA_MARK, "index_version", "analyzer_version", "wordlist_hash", "tantivy_version"}
    )
    assert store.read_meta()[EMBEDDING_MARK] == UNKNOWN_VERSION


def test_an_embedding_drift_is_reported_and_is_no_full_text_drift(store: Store) -> None:
    # version_mismatch reports everything, which is what its docstring promises,
    # and the separation of what a difference means happens at the caller.
    store.write_meta(EMBEDDING_MARK, "multilingual-e5-small/int8/384/512")

    diverging = store.version_mismatch({EMBEDDING_MARK: "multilingual-e5-small/int8/384/1024"})

    assert diverging == [EMBEDDING_MARK]
    assert [mark for mark in diverging if mark not in VECTOR_ONLY_MARKS] == []


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

    expected = {"analyzer_version": "8", "tantivy_version": "0.26.0", STORE_SCHEMA_MARK: SCHEMA_VERSION}

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


def test_refresh_meta_moves_the_crawl_facts_and_leaves_the_verdict_alone(store: Store) -> None:
    # The write behind the fast path of the poller (review finding WR-02). A
    # touch moves the etag without moving a byte; without this narrow update the
    # stored mark stays behind the live one and the reconcile re-downloads the
    # file every cycle, forever.
    store.record(1, a_file(1, etag="old"), "indexed", content_hash="cafe", text_chars=42)

    touched = replace(a_file(1, etag="new"), mtime=1_700_000_999, path="files/moved-1.pdf", title="moved-1.pdf")
    changed = store.refresh_meta(1, touched)

    row = store.file_row(1)
    assert changed == 1
    assert row is not None
    assert row["etag"] == "new"
    assert row["mtime"] == 1_700_000_999
    assert row["path"] == "files/moved-1.pdf"
    assert row["title"] == "moved-1.pdf"
    # The verdict, the hash and the attempts counter are none of its business:
    # nothing was extracted, so no attempt may be counted and no state changed.
    assert row["state"] == "indexed"
    assert row["content_hash"] == "cafe"
    assert row["text_chars"] == 42
    assert row["attempts"] == 1


def test_refresh_meta_makes_the_file_read_as_unchanged_by_the_reconcile(store: Store) -> None:
    # The property the whole fix is for: after the refresh, known_etags answers
    # with the live mark and _stale_of stops proposing the file as work.
    store.record(1, a_file(1, etag="old"), "indexed", content_hash="cafe")

    store.refresh_meta(1, a_file(1, etag="new"))

    assert store.known_etags([1]) == {1: "new"}


def test_refresh_meta_leaves_a_tombstoned_file_alone(store: Store) -> None:
    # Lifting a tombstone is the business of the upsert in record() alone. A
    # refresh that revived a deleted file would make the deletion silently
    # disappear from the state.
    store.record(1, a_file(1, etag="old"), "indexed", content_hash="cafe")
    store.tombstone(1, at=1_700_000_500)

    changed = store.refresh_meta(1, a_file(1, etag="new"))

    row = store.file_row(1)
    assert changed == 0
    assert row is not None
    assert row["etag"] == "old"
    assert row["deleted_at"] == 1_700_000_500


def test_refresh_meta_on_a_file_that_was_never_judged_changes_nothing(store: Store) -> None:
    # Zero is an answer, not a failure: a file without a row has nothing to
    # refresh, and inventing one here would be a second entry point next to
    # record() that every future caller would have to remember.
    assert store.refresh_meta(404, a_file(404, etag="new")) == 0
    assert store.file_row(404) is None


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


def _give_up(store: Store, file_id: int, *, etag: str, state: str = "failed", reason: str = "repeatedly_stuck") -> None:
    """The verdict handover of the reconcile, with the fields a page carries."""
    store.give_up(
        file_id,
        storage_id=2,
        root_id=3,
        mime="application/pdf",
        size=1024,
        mtime=1_700_000_000,
        etag=etag,
        state=state,
        reason=reason,
    )


def test_give_up_stores_the_verdict_against_the_etag_of_the_page(store: Store) -> None:
    # The write that makes a give-up final (review finding IN-03 of phase 3). It
    # carries the etag because the verdict belongs to the version of the file it
    # was reached on, and the path stays empty because the reconcile never sees
    # one.
    _give_up(store, 1, etag="aaa")

    row = store.file_row(1)
    assert row is not None
    assert (row["state"], row["reason"], row["etag"]) == ("failed", "repeatedly_stuck", "aaa")
    assert row["path"] == ""
    assert store.known_etags([1]) == {1: "aaa"}


def test_give_up_leaves_the_attempt_counter_of_this_container_alone(store: Store) -> None:
    # attempts counts what this process tried. The give-up was reached on the
    # other side of the boundary, so counting it here would make the per file
    # diagnosis claim work that never happened in this container.
    store.record(1, a_file(1, etag="aaa"), "failed", "gateway_error")

    _give_up(store, 1, etag="bbb")

    row = store.file_row(1)
    assert row is not None
    assert row["attempts"] == 1
    assert (row["state"], row["reason"], row["etag"]) == ("failed", "repeatedly_stuck", "bbb")


def test_give_up_keeps_a_path_an_earlier_verdict_knew(store: Store) -> None:
    # The empty path is the value of a row this write creates, never an erasure
    # of one the poller already filled in.
    store.record(1, a_file(1, etag="aaa"), "indexed", content_hash="cafe")

    _give_up(store, 1, etag="aaa")

    row = store.file_row(1)
    assert row is not None
    assert row["path"] == "files/report-1.pdf"


def test_give_up_lifts_a_tombstone(store: Store) -> None:
    # A file that turns up in a page again is present. Leaving the mark would
    # keep the row out of known_etags, so every single cycle would write this
    # verdict again instead of reading an unchanged file.
    store.record(1, a_file(1, etag="aaa"), "indexed", content_hash="cafe")
    store.tombstone(1, 1_700_000_500)

    _give_up(store, 1, etag="aaa")

    row = store.file_row(1)
    assert row is not None
    assert row["deleted_at"] is None
    assert store.known_etags([1]) == {1: "aaa"}


def test_give_up_refuses_a_pair_outside_the_closed_list(store: Store) -> None:
    # Same rule as record(), and here it guards a value that arrived over the
    # wire: these two codes are rendered on an admin page, and a companion app
    # with a defect must not be able to put free text into that column.
    with pytest.raises(ValueError, match="reason"):
        _give_up(store, 1, etag="aaa", reason="could not read /files/anna/Kuendigung.pdf")
    with pytest.raises(ValueError, match="reason"):
        _give_up(store, 1, etag="aaa", reason="too_large")
    with pytest.raises(ValueError, match="state"):
        _give_up(store, 1, etag="aaa", state="pending")

    assert store.file_row(1) is None


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


# ---------------------------------------------------------------------------
# The reconcile: which files are gone, which etag we hold, and where the walk
# stopped. Every test below is about the same danger from a different side. The
# reconcile concludes "deleted" from an absence, and an absence is the cheapest
# thing in the world to produce by accident: a page that ended early, a row the
# client refused, a storage nobody asked about. So the range is bounded, the
# bound only falls away on a final page, and a tombstone is never rediscovered.
# ---------------------------------------------------------------------------


def test_gone_in_range_names_the_known_files_the_page_does_not_carry(store: Store) -> None:
    store.record(10, a_file(10), "indexed", content_hash="a")
    store.record(20, a_file(20), "indexed", content_hash="b")
    store.record(30, a_file(30), "indexed", content_hash="c")

    gone = store.gone_in_range(2, 0, 30, final=False, present={10, 30})

    assert gone == [20]


def test_gone_in_range_respects_the_page_end(store: Store) -> None:
    # The load bearing one, and the reason the page carries a final mark at all.
    # File 40 lies behind the last row of the page, so nothing is known about it
    # yet; calling it deleted here would drop a document that exists because a
    # page happened to end.
    store.record(10, a_file(10), "indexed", content_hash="a")
    store.record(40, a_file(40), "indexed", content_hash="d")

    gone = store.gone_in_range(2, 0, 30, final=False, present={10})

    assert gone == []


def test_gone_in_range_drops_the_upper_bound_on_a_final_page(store: Store) -> None:
    # Same two files, and now the page says there is nothing behind it. Only then
    # does the absence of 40 mean anything.
    store.record(10, a_file(10), "indexed", content_hash="a")
    store.record(40, a_file(40), "indexed", content_hash="d")

    gone = store.gone_in_range(2, 0, 30, final=True, present={10})

    assert gone == [40]


def test_gone_in_range_ignores_already_deleted_files(store: Store) -> None:
    # A tombstone is an answer, not a question. Without this condition every
    # cycle would rediscover the same deletion and produce a delete job for a
    # document that left the index months ago.
    store.record(10, a_file(10), "indexed", content_hash="a")
    store.record(20, a_file(20), "indexed", content_hash="b")
    store.tombstone(20, 1_700_000_500)

    gone = store.gone_in_range(2, 0, 30, final=True, present={10})

    assert gone == []


def test_gone_in_range_only_looks_at_the_storage_it_was_asked_about(store: Store) -> None:
    # The walk runs mount by mount. A file of another storage is simply not part
    # of this page, and reading that as a deletion would empty the index of every
    # mount the round has not reached yet.
    store.record(10, a_file(10), "indexed", content_hash="a")
    store.record(11, a_file(11, storage_id=9), "indexed", content_hash="b")

    gone = store.gone_in_range(2, 0, 30, final=True, present={10})

    assert gone == []


def test_gone_in_range_ignores_everything_at_or_below_the_cursor(store: Store) -> None:
    # What lies before the cursor was judged by an earlier page of this same
    # walk. Looking at it again would turn every page into a verdict about the
    # whole mount.
    store.record(10, a_file(10), "indexed", content_hash="a")
    store.record(20, a_file(20), "indexed", content_hash="b")

    gone = store.gone_in_range(2, 10, 30, final=True, present={20})

    assert gone == []


def test_known_etags_answers_with_the_version_marks_it_holds(store: Store) -> None:
    store.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    store.record(20, a_file(20, etag="bbb"), "indexed", content_hash="b")

    assert store.known_etags([10, 20, 30]) == {10: "aaa", 20: "bbb"}


def test_known_etags_leaves_out_a_file_with_a_tombstone(store: Store) -> None:
    # A deleted file that turns up in a page again is a restore, and a restore
    # has to be indexed even though its bytes never changed. Answering with the
    # stored etag here would compare equal and the file would stay gone.
    store.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    store.tombstone(10, 1_700_000_500)

    assert store.known_etags([10]) == {}


def test_known_etags_asks_nothing_for_an_empty_list(store: Store) -> None:
    statements: list[str] = []
    store.trace(statements.append)
    try:
        assert store.known_etags([]) == {}
    finally:
        store.trace(None)

    assert statements == []


def test_known_etags_splits_a_long_list_into_bands(store: Store) -> None:
    # The same property the prefilter has, for the same reason: the parameter
    # limit of a SQLite build is a compile time option and our lists are not.
    statements: list[str] = []
    store.trace(statements.append)
    try:
        store.known_etags(list(range(1, 1501)))
    finally:
        store.trace(None)

    assert len([line for line in statements if line.lstrip().startswith("SELECT")]) == 2


def test_the_reconcile_cursor_of_an_unknown_storage_starts_at_zero(store: Store) -> None:
    cursor = store.reconcile_cursor(4711)

    assert cursor.after_file_id == 0
    assert cursor.finished_at is None


def test_the_reconcile_cursor_can_be_advanced(store: Store) -> None:
    store.set_reconcile_cursor(2, 500)
    store.set_reconcile_cursor(2, 1000)

    cursor = store.reconcile_cursor(2)

    assert cursor.after_file_id == 1000
    assert cursor.started_at is not None
    assert cursor.finished_at is None


def test_finishing_a_mount_resets_the_cursor_and_stamps_the_time(store: Store) -> None:
    # Zero and a finish stamp together are what "this mount is done" means. The
    # next cycle starts at the beginning again, which is the whole point of a
    # bookmark that may be lost without losing work.
    store.set_reconcile_cursor(2, 1000)
    store.set_reconcile_cursor(2, 0, finished=True)

    cursor = store.reconcile_cursor(2)

    assert cursor.after_file_id == 0
    assert cursor.finished_at is not None


def test_reconcile_state_reports_a_walk_that_stopped_in_the_middle(store: Store) -> None:
    store.set_reconcile_cursor(2, 1000)

    state = store.reconcile_state()

    assert state.unfinished == 1
    assert state.last_finished_at is None


def test_reconcile_state_reports_the_end_of_the_last_cycle(store: Store) -> None:
    store.set_reconcile_cursor(2, 0, finished=True, at=1_700_000_100)
    store.set_reconcile_cursor(3, 0, finished=True, at=1_700_000_900)

    state = store.reconcile_state()

    assert state.unfinished == 0
    assert state.last_finished_at == 1_700_000_900


def test_the_schema_applies_to_an_existing_database_without_losing_anything(tmp_path: Path) -> None:
    # open_store runs schema.sql on every start, so a new table has to arrive on
    # a database that is already full. Every statement in that file is
    # IF NOT EXISTS, which is why a schema change of this kind is additive.
    path = tmp_path / "state.db"
    first = open_store(path)
    first.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    first.set_reconcile_cursor(2, 700)
    first.close()

    second = open_store(path)
    try:
        row = second.file_row(10)
        assert row is not None
        assert row["etag"] == "aaa"
        assert second.reconcile_cursor(2).after_file_id == 700
        assert second.read_meta()[STORE_SCHEMA_MARK] == SCHEMA_VERSION
    finally:
        second.close()


def test_a_database_of_layout_one_opens_and_keeps_its_stock(tmp_path: Path) -> None:
    # The claim of D-21, checked rather than asserted in prose: phase 6 only
    # adds, so a state database written by the code before it opens, gets the
    # new mark and loses nothing. The starting point is built by hand, because
    # the only honest stand-in for "written by the older code" is a database
    # that carries the older marks and none of the newer ones.
    path = tmp_path / "state.db"
    older = open_store(path)
    older.record(10, a_file(10, etag="aaa"), "indexed", content_hash="a")
    older.replace_acl(10, ["alice", "bob"])
    older._conn.execute("DELETE FROM meta WHERE key IN (?, ?)", (STORE_SCHEMA_MARK, EMBEDDING_MARK))
    older.write_meta("schema_version", "1")
    older.close()

    reopened = open_store(path)
    try:
        meta = reopened.read_meta()

        # The new marks are there ...
        assert meta[STORE_SCHEMA_MARK] == SCHEMA_VERSION
        assert meta[EMBEDDING_MARK] == UNKNOWN_VERSION
        # ... the old ones were not rewritten ...
        assert meta["schema_version"] == "1"
        # ... and the stock is untouched, which is what "no reindex" means.
        row = reopened.file_row(10)
        assert row is not None
        assert row["state"] == "indexed"
        assert reopened.prefilter_visible("alice", [10]) == {10}
        assert reopened.acl_rows() == 2
    finally:
        reopened.close()


def test_index_bytes_sums_every_file_below_the_directory(tmp_path: Path) -> None:
    # The base of the space estimate on the admin page. Tantivy keeps its
    # segments in subdirectories, so a sum over the top level alone would report
    # a fraction of the real size and the estimate built on it would be wrong in
    # the direction that fills a volume.
    directory = tmp_path / "index"
    (directory / "segments").mkdir(parents=True)
    (directory / "meta.json").write_bytes(b"m" * 100)
    (directory / "segments" / "0.store").write_bytes(b"s" * 23)

    assert index_bytes(directory) == 123


def test_index_bytes_reports_zero_for_a_directory_that_is_not_there(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # A container that has not indexed anything yet has no index directory, and
    # the honest answer to that is zero WITHOUT a warning. The admin page polls
    # this figure, so a warning for the ordinary fresh state wrote one line per
    # poll into the log and made every other warning of this module worthless
    # (IN-01).
    with caplog.at_level(logging.WARNING):
        assert index_bytes(tmp_path / "index") == 0

    assert caplog.records == []


def test_index_bytes_warns_when_something_is_there_but_not_a_directory(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The state that really is unexpected: the index path exists and is a file,
    # so the volume is not laid out the way this container needs it. That is
    # worth a warning, and the warning names no path for the same reason nothing
    # else in this project logs one (T-04-07).
    occupied = tmp_path / "index"
    occupied.write_bytes(b"not a directory")

    with caplog.at_level(logging.WARNING):
        assert index_bytes(occupied) == 0

    assert caplog.records
    assert str(tmp_path) not in caplog.text


def _fill_acl(store: Store, documents: int, users: int) -> None:
    """Write a permission table large enough for a runtime statement."""
    for file_id in range(1, documents + 1):
        store.replace_acl(file_id, [f"user{index}" for index in range(users)])


def test_acl_totals_answers_the_same_numbers_on_a_large_table(
    store: Store,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The numbers are the contract, the query form is not. 6.000 rows over 2.000
    # documents is above the 5.000 the plan asks for and still cheap enough for
    # a unit suite; the reference below is the form that was replaced.
    _fill_acl(store, documents=2_000, users=3)

    started = time.perf_counter()
    rows, documents = store.acl_totals()
    elapsed_ms = (time.perf_counter() - started) * 1000

    reference = store._conn.execute("SELECT COUNT(*), COUNT(DISTINCT file_id) FROM acl").fetchone()

    assert (rows, documents) == (int(reference[0]), int(reference[1]))
    assert (rows, documents) == (6_000, 2_000)
    # Logged rather than asserted. A threshold on wall clock time in a unit suite
    # is a flaky test on a busy machine; the number belongs in the record of the
    # change, and the structural guarantee is the query plan asserted below.
    logging.getLogger(__name__).info("acl_totals over %d rows took %.3f ms", rows, elapsed_ms)


def test_acl_totals_builds_no_temporary_b_tree(store: Store) -> None:
    # The structural half of the statement above, and the one that matters on a
    # 4 GB box: COUNT(DISTINCT file_id) made SQLite materialise one ephemeral
    # index entry per document on every admin poll. The plan of the replacement
    # scans the covering index in order, so the distinct step costs a comparison
    # and no memory at all.
    _fill_acl(store, documents=200, users=3)

    plans = "\n".join(
        str(row)
        for sql in (_ACL_DOCUMENTS_SQL, _ACL_ROWS_SQL)
        # Both statements are module constants of the store, never anything a
        # caller composed, which is what makes the concatenation here harmless.
        for row in store._conn.execute(f"EXPLAIN QUERY PLAN {sql}")
    )

    assert "TEMP B-TREE" not in plans.upper()
    assert "COVERING INDEX acl_file" in plans


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
