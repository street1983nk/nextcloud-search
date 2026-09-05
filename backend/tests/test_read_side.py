"""The cached read side: one open per volume, one lock, and nothing left behind.

The module under test holds process wide state, and every search reaches it from
a worker thread: the search endpoint runs its round in ``asyncio.to_thread`` and
the unified search asks all providers at the same moment, so two requests really
do arrive in here at once. That makes three properties worth asserting rather
than assuming (audit M7, phase 4 finding IN-06):

* two threads must not each open their own read side, because the loser of the
  assignment leaves a SQLite connection nobody can close any more,
* a run that fails after the state database was opened has to close it,
* the degraded verdict must not be measured on every single search, because it
  costs a meta read plus a disk_usage call and a search costs 0.005 ms.

The fixtures come from conftest, so the volume these tests open is a real index
with a real state database rather than a stand-in.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from collections.abc import Callable
from pathlib import Path

import pytest

from conftest import Corpus, write_index, write_state, write_wordlist
from findling.api import resources
from findling.config import settings
from findling.store.repo import EMBEDDING_MARK, Store, open_store

THREADS = 4


def _in_four_threads(work: Callable[[], None]) -> None:
    """Run one callable in four threads that start as simultaneously as they can.

    The gate is what makes the test worth writing. Started one after another the
    threads would mostly serialise on their own, the first one would fill the
    cache and the other three would never reach the branch this file is about.
    """
    gate = threading.Event()

    def gated() -> None:
        gate.wait(30)
        work()

    workers = [threading.Thread(target=gated) for _ in range(THREADS)]
    for worker in workers:
        worker.start()
    gate.set()
    for worker in workers:
        worker.join(60)


def test_four_threads_open_the_read_side_exactly_once(
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Without the lock all four threads pass the "nothing cached yet" check,
    # all four open a connection, and three of them are dropped on the floor
    # when the fourth wins the assignment.
    opened: list[Store] = []
    real_open = resources.open_read_only

    def counting_open(path: Path | str) -> Store:
        store = real_open(path)
        opened.append(store)
        return store

    monkeypatch.setattr(resources, "open_read_only", counting_open)

    answers: list[resources.ReadSide | None] = []
    lock = threading.Lock()

    def ask() -> None:
        side = resources.read_side()
        with lock:
            answers.append(side)

    _in_four_threads(ask)

    assert len(answers) == THREADS, "every thread has to have answered"
    assert all(side is not None for side in answers)
    assert len({id(side) for side in answers}) == 1, "four threads, one read side"
    assert len(opened) == 1, "a second connection would be one nobody can close again"
    assert indexed_volume.root.is_dir()


def test_a_failed_open_leaves_no_state_connection_behind(
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The state database is the last thing the open does, so a failure behind it
    # used to keep the connection for the lifetime of the process. Simulated by
    # letting the assembly step fail, because that is the only step after it.
    opened: list[Store] = []
    real_open = resources.open_read_only

    def counting_open(path: Path | str) -> Store:
        store = real_open(path)
        opened.append(store)
        return store

    def refuse_to_assemble(**_: object) -> resources.ReadSide:
        raise RuntimeError("the read side could not be assembled")

    monkeypatch.setattr(resources, "open_read_only", counting_open)
    monkeypatch.setattr(resources, "ReadSide", refuse_to_assemble)

    with caplog.at_level(logging.WARNING):
        assert resources.read_side() is None

    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError):
        opened[0].read_meta()
    # The log line carries the type of the failure and never a path.
    assert str(indexed_volume.root) not in caplog.text


def test_a_volume_that_is_replaced_closes_the_handle_it_had(
    indexed_volume: Corpus,
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The path a test suite walks on every single test and a container walks
    # when its volume is remounted: the cached handle belongs to a directory
    # that is no longer the one the settings name. It has to be closed, not
    # merely forgotten.
    first = resources.read_side()
    assert first is not None

    empty = tmp_path_factory.mktemp("nothing-indexed-yet")
    monkeypatch.setenv("APP_PERSISTENT_STORAGE", str(empty))
    settings.cache_clear()

    assert resources.read_side() is None

    with pytest.raises(sqlite3.ProgrammingError):
        first.store.read_meta()


def test_the_degraded_verdict_is_not_measured_on_every_search(
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Two measurements per search, a meta read and a disk_usage call, against a
    # search that costs 0.005 ms. The verdict is remembered for a named window
    # instead, and the window is short enough that a backend which fell over is
    # still reported as such.
    side = resources.read_side()
    assert side is not None
    measurements = 0

    def counting_low_disk() -> bool:
        nonlocal measurements
        measurements += 1
        return False

    monkeypatch.setattr(resources, "low_disk", counting_low_disk)

    assert resources.degraded(side) is False
    assert resources.degraded(side) is False
    assert resources.degraded(side) is False

    assert measurements == 1, "the verdict was measured once and answered three times"


def test_a_drift_that_appears_is_seen_again_after_the_window(
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The other half of the cache, and the reason the window is seconds rather
    # than minutes: a state that turns bad has to become visible without a
    # restart. With the window closed the next call measures again.
    side = resources.read_side()
    assert side is not None

    assert resources.degraded(side) is False

    writable = open_store(indexed_volume.root / "state.db")
    writable.write_meta("analyzer_version", "99")
    writable.close()

    monkeypatch.setattr(resources, "DEGRADED_TTL_SECONDS", 0.0)

    assert resources.degraded(side) is True


def test_a_container_without_an_index_is_degraded_without_a_measurement(volume: Path) -> None:
    # No index means degraded, and that answer needs neither a cache nor a
    # measurement. Kept as its own case because it is the state a fresh
    # container is in for its first few minutes.
    assert not (volume / "index").exists()

    assert resources.degraded(None) is True


def test_the_version_marks_survive_four_threads(volume: Path) -> None:
    # The second piece of module state, and it is written from the same worker
    # threads. Four threads, one mapping, and every one of them has to get a
    # complete answer rather than a half filled dictionary.
    write_wordlist(volume)
    answers: list[dict[str, str] | None] = []
    lock = threading.Lock()

    def ask() -> None:
        marks = resources.expected_marks()
        with lock:
            answers.append(marks)

    _in_four_threads(ask)

    assert len(answers) == THREADS
    assert all(marks for marks in answers)
    assert len({tuple(sorted((marks or {}).items())) for marks in answers}) == 1


def test_the_expected_marks_carry_the_embedding_version(volume: Path) -> None:
    # The mark that phase 6 adds. It is composed here and not in
    # expected_versions(), because that function feeds start_rebuild_on_drift.
    write_wordlist(volume)

    marks = resources.expected_marks()

    assert marks is not None
    assert marks[EMBEDDING_MARK] == "multilingual-e5-small/int8/384/1024"


def test_an_embedding_drift_is_reported_but_forces_no_reindex(volume: Path) -> None:
    # The property D-21 asks for, at the place that decides what a difference
    # means. The stored mark is the one an older model wrote; the index side of
    # the marks agrees, so the only divergence is the vector one.
    digest = write_wordlist(volume)
    corpus = Corpus(root=volume, digest=digest)
    write_index(volume, corpus.documents)
    write_state(volume, corpus)

    store = open_store(volume / "state.db")
    try:
        store.write_meta(EMBEDDING_MARK, "multilingual-e5-small/int8/384/512")
        marks = resources.expected_marks()

        assert marks is not None
        assert EMBEDDING_MARK in store.version_mismatch(marks)
        assert resources.version_drift(store) == []
    finally:
        store.close()


def test_a_fresh_volume_gets_its_own_marks(volume: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    # The cache of the marks is keyed on the dictionary directory for the same
    # reason the handles are keyed on the index directory: a digest carried over
    # from another volume reports a drift that does not exist.
    digest = write_wordlist(volume)
    corpus = Corpus(root=volume, digest=digest)
    write_index(volume, corpus.documents)
    write_state(volume, corpus)

    first = resources.expected_marks()

    assert first is not None
    assert first["wordlist_hash"] == digest


def test_a_volume_without_a_vector_stock_still_has_a_read_side(indexed_volume: Corpus) -> None:
    # Criterion 3 at the place where it would be lost first. A missing
    # vectors.db must cost the semantic half and nothing else, so read_side has
    # to answer a ReadSide with vectors set to None and never None itself.
    (indexed_volume.root / "vectors.db").unlink()
    settings.cache_clear()

    side = resources.read_side()

    assert side is not None
    assert side.vectors is None
    assert side.index is not None


def test_a_vector_file_that_is_not_a_database_costs_only_the_semantics(
    indexed_volume: Corpus,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The second shape of a broken stock, and the one an ordinary open would
    # let through: a file that exists and is not a database.
    broken = indexed_volume.root / "vectors.db"
    broken.write_bytes(b"this is not a database")
    settings.cache_clear()

    with caplog.at_level(logging.WARNING):
        side = resources.read_side()

    assert side is not None
    assert side.vectors is None
    # The log line carries a type name and nothing else: not the path, which is
    # a file name, and not the library message, which quotes what it read.
    assert str(broken) not in caplog.text
    assert "this is not a database" not in caplog.text


def test_a_missing_vector_stock_is_a_degraded_container(indexed_volume: Corpus) -> None:
    # The fourth cause of the flag. A container that answers lexically answers
    # correctly, it just does not answer with everything it promises.
    (indexed_volume.root / "vectors.db").unlink()
    settings.cache_clear()

    side = resources.read_side()

    assert side is not None
    assert resources.degraded(side) is True


def test_a_missing_vector_stock_with_embedding_off_is_not_degraded(
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # An instance whose admin switched the second track off is not missing
    # anything, so the fourth cause is asked only while it is on.
    (indexed_volume.root / "vectors.db").unlink()
    monkeypatch.setenv("FINDLING_EMBED_ENABLED", "false")
    settings.cache_clear()

    side = resources.read_side()

    assert side is not None
    assert side.vectors is None
    assert resources.degraded(side) is False


def test_a_present_vector_stock_is_opened_read_only(indexed_volume: Corpus) -> None:
    side = resources.read_side()

    assert side is not None
    assert side.vectors is not None
    with pytest.raises(sqlite3.OperationalError):
        side.vectors.forget_all()


def test_the_query_model_is_built_once(volume: Path) -> None:
    # The wrapper remembers a failed load, so a container without a model looks
    # for it once instead of once per search. Two wrappers would look twice.
    assert volume.is_dir()

    first = resources.query_model()
    second = resources.query_model()

    assert first is second
    assert first.loaded is False


def test_the_embedding_mark_follows_the_token_cap(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The cap is a setting an operator may raise, and raising it really does
    # make every stored vector incomparable with a freshly computed one. A mark
    # that kept claiming 1024 would hide exactly the drift it exists to show.
    monkeypatch.setenv("FINDLING_EMBED_TOKEN_CAP", "2048")
    settings.cache_clear()
    write_wordlist(volume)

    marks = resources.expected_marks()

    assert marks is not None
    assert marks[EMBEDDING_MARK] == "multilingual-e5-small/int8/384/2048"
