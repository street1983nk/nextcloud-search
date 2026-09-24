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
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import cast

import pytest
from tantivy import Index

from conftest import Corpus, write_index, write_state, write_wordlist
from findling.api import resources
from findling.config import settings
from findling.index.open import LANGUAGES_MARK
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


# -- the explicit reset, which is what the directory swap of plan 18-07 needs ---
#
# The three caches above are keyed on a path, and the swap does not move a path:
# it puts the rebuilt directory under the very name the live one had. The
# invalidation branch inside read_side() therefore never fires, and without an
# explicit reset the container would go on answering out of the directory that
# was renamed away, silently on Linux and until the next restart (pitfall 3 of
# the phase research).


def test_the_read_side_is_dropped_although_the_path_did_not_move(indexed_volume: Corpus) -> None:
    # The one case the existing release branch cannot reach. Same index_dir
    # before and after, and still a different instance, because the directory
    # behind that name is a different directory now.
    first = resources.read_side()
    assert first is not None
    assert first.vectors is not None

    resources.reset_read_side()
    second = resources.read_side()

    assert second is not None
    assert second is not first
    assert second.index_dir == first.index_dir == indexed_volume.root / "index"
    with pytest.raises(sqlite3.ProgrammingError):
        first.store.read_meta()
    with pytest.raises(sqlite3.ProgrammingError):
        first.vectors.chunk_count()


def test_the_degraded_verdict_is_dropped_with_the_read_side(indexed_volume: Corpus) -> None:
    # A verdict that stayed would report the state of the retired directory for
    # up to DEGRADED_TTL_SECONDS after the swap, which is exactly the window in
    # which an admin looks at the status page.
    side = resources.read_side()
    assert side is not None
    assert resources.degraded(side) is False

    writable = open_store(indexed_volume.root / "state.db")
    writable.write_meta("analyzer_version", "99")
    writable.close()

    # The window is deliberately left alone: this case is about the reset and
    # not about the TTL, so the stale answer below proves the cache was warm.
    assert resources.degraded(side) is False

    resources.reset_read_side()
    fresh = resources.read_side()

    assert fresh is not None
    assert resources.degraded(fresh) is True


def test_the_version_marks_are_dropped_with_the_read_side(
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The third cache, and the one whose staleness is hardest to see. It is
    # keyed on the dictionary directory, which a rebuild does not move either,
    # and the language set is the one mark a rebuild exists to change.
    before = resources.expected_marks()
    assert before is not None
    assert before[LANGUAGES_MARK] == "de,en"

    monkeypatch.setenv("FINDLING_LANGUAGES", "de,en,es")
    settings.cache_clear()

    assert resources.expected_marks() == before, "the mapping is cached under a directory that did not move"

    resources.reset_read_side()
    after = resources.expected_marks()

    assert after is not None
    assert after[LANGUAGES_MARK] == "de,en,es"


def test_a_reset_on_an_empty_state_does_nothing_and_says_nothing(volume: Path) -> None:
    # Idempotent, because the caller of the swap runs it in front of the first
    # rename whatever the process did before, and a container whose first
    # indexing pass never finished has nothing cached at all.
    assert not (volume / "index").exists()

    resources.reset_read_side()
    resources.reset_read_side()

    assert resources.read_side() is None


def test_four_threads_may_drop_the_read_side_at_once(indexed_volume: Corpus) -> None:
    # The reset takes the same lock the three caches are guarded by, so a search
    # that arrives in the middle of a swap waits instead of reading a handle
    # that is being closed underneath it.
    assert resources.read_side() is not None
    failures: list[Exception] = []
    lock = threading.Lock()

    def drop() -> None:
        try:
            resources.reset_read_side()
            resources.read_side()
        except Exception as error:
            with lock:
                failures.append(error)

    _in_four_threads(drop)

    assert failures == []


def test_a_state_database_without_an_index_directory_is_none_and_not_an_error(volume: Path) -> None:
    """The branch that used to raise out of a function that must not raise.

    Found on 2026-09-24 while plan 18-10 made the status route ask this
    function: ``Index.exists`` raises ``ValueError("Directory does not exist")``
    for a path that is not there, it does not answer False, and the short circuit
    of the condition reaches it as soon as a state database exists. A volume in
    exactly that state is an ordinary one, a kill between the first state write
    and the first commit leaves it behind, and the unified search calls every
    provider in parallel: a provider that raises costs the user the whole
    search.
    """
    write_wordlist(volume)
    write_state(volume, Corpus(root=volume, digest=""))
    assert (volume / "state.db").is_file()
    assert not (volume / "index").exists()

    assert resources.read_side() is None
    assert resources.filled_languages() == ()


def test_the_read_side_answers_nothing_while_a_directory_swap_is_between_its_renames(
    indexed_volume: Corpus,
) -> None:
    """M-18-03: the window the reset alone could not close.

    Emptying the caches and renaming the directory are two moments, and a search
    that arrived between them opened the live directory again and kept the
    handle. A moment later that directory was renamed and removed, and on Linux
    both calls succeed, so the cached handle went on answering every search out
    of a directory that has no name, for as long as the process lived. That is
    pitfall 3 of the phase research, and it is the very thing the reset was
    written against.

    The bar answers it: while it is up there is no reading side at all, and the
    reading half already treats that as "this container has no index yet". It
    lasts two rename system calls.
    """
    del indexed_volume
    assert resources.read_side() is not None

    resources.hold_the_read_side_shut()
    try:
        # In a finally, because the bar is process wide: a case that raised with
        # it up would leave every later case in this suite without a read side.
        assert resources.read_side() is None, "no handle is handed out and none is opened"
        assert resources.read_side() is None, "and asking twice does not open one either"
    finally:
        resources.let_the_read_side_open()

    assert resources.read_side() is not None, "and the next search opens the directory that is there now"


def test_the_bar_lets_the_side_open_again_even_when_the_swap_threw(indexed_volume: Corpus) -> None:
    """The pair is a pair, and the second half belongs in a finally.

    A swap that raises leaves a container that can answer out of whatever the
    clean up path of the next start makes of the volume. A bar nobody lowered
    would leave one that answers nothing until it is restarted, which would turn
    a recoverable fault into a dead container.
    """
    del indexed_volume
    resources.hold_the_read_side_shut()
    try:
        raise OSError("the rename refused")
    except OSError:
        resources.let_the_read_side_open()

    assert resources.read_side() is not None


def test_a_verdict_measured_before_a_reset_is_answered_and_not_remembered(
    indexed_volume: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M-18-02: the side is taken outside the lock and the cache is written inside it.

    A reset that lands between the two used to leave the later writer filling
    the cache it had just emptied, with a reading from the directory that was
    retired a moment ago. The path key cannot catch it, because the swap puts
    the rebuilt directory under the very name the live one had, so the key
    matches and the entry looks current: the admin page reported the state from
    before the rebuild for the whole window, which is exactly the moment those
    lines were written for.

    Staged where the race really is, by resetting while the measurement is
    running. The reading is still handed out, because it was true when it was
    taken and the caller asked about the handles it holds; what may not happen
    is that it survives in the cache.
    """
    stale = resources.read_side()
    assert stale is not None
    honest = resources.low_disk

    def reset_while_the_verdict_is_being_measured() -> bool:
        resources.reset_read_side()
        return honest()

    monkeypatch.setattr(resources, "low_disk", reset_while_the_verdict_is_being_measured)

    assert resources.degraded(stale) is False

    monkeypatch.setattr(resources, "low_disk", honest)
    del indexed_volume

    assert resources._DEGRADED is None, "the reading of the retired directory was not written back"


def test_a_fill_level_measured_before_a_reset_is_answered_and_not_remembered(
    indexed_volume: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same race at the other measurement, and the more expensive one of the two.

    This is the reading a rebuild exists to move. A cache entry filled from the
    retired directory has the admin page report the old chains for the whole
    thirty second window, right after the run that filled the new ones.
    """
    del indexed_volume
    real = resources.read_side()
    assert real is not None

    class _AChainThatResetsWhileItIsAsked:
        def terms_with_prefix(self, field: str, prefix: str, limit: int | None = None) -> Sequence[object]:
            resources.reset_read_side()
            return real.index.searcher().terms_with_prefix(field, prefix, limit=limit)

    class _AnIndexThatMovesUnderTheProbe:
        def searcher(self) -> _AChainThatResetsWhileItIsAsked:
            return _AChainThatResetsWhileItIsAsked()

    staged = resources.ReadSide(
        index=cast("Index", _AnIndexThatMovesUnderTheProbe()),
        store=real.store,
        index_dir=real.index_dir,
        vectors=real.vectors,
        generation=real.generation,
    )
    monkeypatch.setattr(resources, "read_side", lambda: staged)

    assert resources.filled_languages() == ("de",), "the reading is handed out"
    assert resources._FILLED is None, "and it is not remembered"
