"""The embedding track writes through connections of its own, and two writers wait.

Why the track needs its own connections at all: a SQLite connection carries one
transaction at a time, and ``BEGIN IMMEDIATE`` is taken per connection (see the
docstring of :func:`findling.store.repo.open_store`). Two tracks that shared the
connection of the poller would not wait for each other, they would step into
each other's transaction: the second ``BEGIN`` raises, or worse, one track's
rollback takes the other track's rows with it. With one connection per track
the database file is the only thing they share, WAL lets a reader through, and
the busy timeout turns a second writer into a writer that waits.

So this file holds three statements with real files in ``tmp_path``: an opened
track holds other connection objects than the poller, a write through either
one lands while the other holds ``BEGIN IMMEDIATE`` for 200 ms, and the track
never creates a state database that is not there.

The overlap is made deterministic with a barrier: the holding thread has begun
its transaction before the second writer is let go, and five seconds are the
cap after which the case fails instead of hanging.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest

from findling.config import settings
from findling.embed.model import DIMENSIONS, to_int8
from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter
from findling.nc.client import AsyncNextcloudApp
from findling.store.repo import Store, open_store
from findling.store.vectors import Chunk, VectorStore
from findling.worker import poller as poller_module
from findling.worker.embedding import EmbeddingTrack
from findling.worker.poller import Poller

CONSTITUENTS = (
    (Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt").read_text(encoding="utf-8").split()
)

# How long the first writer holds its transaction, and how long a case may take
# before it counts as hanging.
HOLD_SECONDS = 0.2
CAP_SECONDS = 5.0


@dataclass(frozen=True, slots=True)
class _Opened:
    """A poller opened over real files, with the connections of both tracks."""

    poller: Poller
    poller_store: Store
    poller_vectors: VectorStore
    track_store: Store
    track_vectors: VectorStore


@pytest.fixture
def volume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    root = tmp_path / "volume"
    monkeypatch.setenv("APP_PERSISTENT_STORAGE", str(root))
    settings.cache_clear()
    yield root
    settings.cache_clear()


@pytest.fixture
def opened(volume: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[_Opened]:
    """A poller that owns its resources, opened the way a first pass opens it.

    The state database is created by the poller's side, as in production, and
    the writer stands on a directory of its own so that nothing here builds the
    system word list. What is under test is the wiring of the connections.
    """
    del volume
    poller_store = open_store(settings().state_db)
    index_dir = tmp_path / "index"
    writer = IndexBatchWriter(open_index(index_dir, CONSTITUENTS), directory=index_dir, min_free_bytes=0)
    monkeypatch.setattr(poller_module, "_open_state", lambda: poller_store)
    monkeypatch.setattr(poller_module, "_open_writer", lambda _store, *, vectors: writer)
    worker = Poller(
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        gateway_factory=lambda: cast("Any", object()),
        queue_factory=lambda nc: cast("Any", object()),
    )
    worker._open()
    track = worker._track
    try:
        assert worker._vectors is not None
        assert track._store is not None
        assert track._vectors is not None
        yield _Opened(worker, poller_store, worker._vectors, track._store, track._vectors)
    finally:
        track.close()
        if worker._vectors is not None:
            worker._vectors.close()
        poller_store.close()
        writer.close()


def _race(hold: Callable[[threading.Barrier], None], write: Callable[[], None]) -> float:
    """Run the holder and the writer in two threads, the holder first.

    Returns how long the writer took. Any exception of either thread fails the
    case with that exception; a thread still alive after the cap fails it too.
    """
    barrier = threading.Barrier(2, timeout=CAP_SECONDS)
    errors: list[BaseException] = []
    took: list[float] = []

    def holder() -> None:
        try:
            hold(barrier)
        except BaseException as error:
            errors.append(error)

    def writer() -> None:
        try:
            barrier.wait()
            started = time.monotonic()
            write()
            took.append(time.monotonic() - started)
        except BaseException as error:
            errors.append(error)

    threads = [threading.Thread(target=holder), threading.Thread(target=writer)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(CAP_SECONDS)
    assert not any(thread.is_alive() for thread in threads), "a writer hung past the cap"
    assert errors == []
    assert len(took) == 1
    return took[0]


def test_an_opened_track_holds_connections_of_its_own(opened: _Opened) -> None:
    assert opened.track_store is not opened.poller_store
    assert opened.track_store._conn is not opened.poller_store._conn
    assert opened.track_vectors is not opened.poller_vectors
    assert opened.track_vectors._conn is not opened.poller_vectors._conn
    # And the poller's stock is the one the delete path of the state database
    # was handed, so a tombstone still reaches vectors (D-21).
    assert opened.poller_store._vectors is opened.poller_vectors


def test_a_second_writer_on_the_state_database_waits_instead_of_failing(opened: _Opened) -> None:
    held = opened.poller_store._conn

    def hold(barrier: threading.Barrier) -> None:
        held.execute("BEGIN IMMEDIATE")
        held.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('probe_holder', 'written')")
        barrier.wait()
        time.sleep(HOLD_SECONDS)
        held.execute("COMMIT")

    took = _race(hold, lambda: opened.track_store.replace_acl(4711, ("alice",)))

    assert took >= HOLD_SECONDS / 2, "the second writer really waited for the first"
    assert opened.poller_store.read_meta()["probe_holder"] == "written"
    assert opened.poller_store.prefilter_visible("alice", [4711]) == {4711}


def test_a_second_writer_on_the_vector_database_waits_instead_of_failing(opened: _Opened) -> None:
    held = opened.poller_vectors._conn

    def hold(barrier: threading.Barrier) -> None:
        held.execute("BEGIN IMMEDIATE")
        held.execute("DELETE FROM chunks WHERE file_id = -1")
        barrier.wait()
        time.sleep(HOLD_SECONDS)
        held.execute("COMMIT")

    chunk = Chunk(ordinal=0, char_start=0, char_end=5, embedding=to_int8([0.001] * DIMENSIONS))
    took = _race(hold, lambda: opened.track_vectors.replace_chunks(4711, [chunk]))

    assert took >= HOLD_SECONDS / 2, "the second writer really waited for the first"
    assert opened.poller_vectors.chunks_of([4711]) != {}


def test_a_track_never_creates_a_state_database_that_is_not_there(volume: Path) -> None:
    track = EmbeddingTrack()
    track.open(wire=False)
    try:
        assert track._store is None
        assert not settings().state_db.exists()
        assert not settings().index_dir.exists(), "and it creates no index directory either"
    finally:
        track.close()
    assert not volume.exists() or not any(volume.iterdir())
