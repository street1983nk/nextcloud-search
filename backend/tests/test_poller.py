"""The one indexing task, against a real index, a real state database and fakes
for everything that would otherwise need a Nextcloud.

The order commit, state, acknowledgement is the subject of this file. It is not a
convention: it is the only arrangement in which every possible moment of an abort
is harmless. Two tests carry that claim, and the rest of them nail down the
conditions under which it holds.

*The order test* watches the three steps happen and asserts the sequence. A
reversed order does not fail anywhere; it loses documents quietly, which is the
failure class that made the predecessor of this app unusable without a single
counter noticing.

*The redelivery test* stages the abort that costs the most: the commit is
through, the state write dies. The queue hands the row back, the second pass does
the work again, and the index has to hold exactly one document afterwards. That
number is the whole promise of the upsert.

*The client test* counts. One client per run is not a matter of taste: a client
per file pays a connection setup per file and, on the PHP side, a Nextcloud
bootstrap including the signature check, and at a hundred thousand files that is
the difference between an initial index and a weekend.

The extractor injected here is the real dispatcher, not a stub. It runs in this
process instead of in the guarded child, which keeps the tests fast while the
verdicts, the reasons and the character cap stay the real ones.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import IO, Any, cast

import pytest
from fastapi.testclient import TestClient
from tantivy import Index

from findling.extract.dispatch import extract as dispatch_extract
from findling.index.open import open_index
from findling.index.schema import FIELD_BODY_DE, FIELD_FILE_ID
from findling.index.writer import IndexBatchWriter
from findling.main import APP, active_poller, enabled_handler
from findling.nc.client import AsyncNextcloudApp, NextcloudException
from findling.nc.queue import CallResult, ClaimResult, QueueJob, QueueStats
from findling.store.repo import Store, open_store
from findling.worker.poller import (
    PASS_EMPTY,
    PASS_GATEWAY_UNAVAILABLE,
    PASS_PAUSED_LOW_DISK,
    PASS_QUEUE_UNAVAILABLE,
    PASS_WORKED,
    Poller,
)

POLLER_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "worker" / "poller.py"
MAIN_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "main.py"

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()

BODY = "Die Kündigungsfrist beträgt drei Monate.\n"
BODY_BYTES = BODY.encode("utf-8")


def _job(queue_id: int = 91, file_id: int = 4711, *, mime: str = "text/plain", size: int | None = None) -> QueueJob:
    return QueueJob(
        queue_id=queue_id,
        file_id=file_id,
        storage_id=3,
        root_id=2,
        path="Vertraege/Kuendigung.txt",
        title="Kuendigung.txt",
        mime=mime,
        size=len(BODY_BYTES) if size is None else size,
        mtime=1_756_600_000,
        etag="5d41402abc4b2a76b9719d911017c592",
        user_ids=("alice", "bob"),
        fetch_as="alice",
        is_update=False,
    )


class _FakeQueue:
    """The four queue calls, answered from a script and recorded."""

    def __init__(self, *batches: ClaimResult) -> None:
        self._batches = list(batches)
        self.claims = 0
        self.acknowledged: list[tuple[list[int], dict[int, str]]] = []
        self.unlocked: list[list[int]] = []

    async def claim(self, *, limit: int, max_bytes: int) -> ClaimResult:
        del limit, max_bytes
        self.claims += 1
        return self._batches.pop(0) if self._batches else ClaimResult()

    async def acknowledge(self, done: Any, failed: Any) -> CallResult:
        self.acknowledged.append((list(done), dict(failed)))
        return CallResult(ok=True, count=len(done) + len(failed))

    async def unlock(self, ids: Any) -> CallResult:
        self.unlocked.append(list(ids))
        return CallResult(ok=True, count=len(ids))

    async def stats(self) -> QueueStats:
        return QueueStats()


class _FakeGatewayClient:
    """Stands in for the pooled HTTP client; only its closing is observable."""

    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


def _gateway(bodies: dict[int, bytes | BaseException | None]) -> Callable[..., Any]:
    """A fetch_file_stream doppelganger driven by a table of file ids."""

    async def fetch(
        nc: AsyncNextcloudApp,
        file_id: int,
        user_id: str,
        fp: IO[bytes],
        *,
        client: Any = None,
    ) -> int | None:
        del nc, user_id, client
        body = bodies.get(file_id, BODY_BYTES)
        if isinstance(body, BaseException):
            raise body
        if body is None:
            return None
        fp.write(body)
        return len(body)

    return fetch


@pytest.fixture
def index_dir(tmp_path: Path) -> Path:
    return tmp_path / "index"


@pytest.fixture
def index(index_dir: Path) -> Index:
    return open_index(index_dir, CONSTITUENTS)


@pytest.fixture
def writer(index: Index, index_dir: Path) -> Iterator[IndexBatchWriter]:
    batch_writer = IndexBatchWriter(index, directory=index_dir, min_free_bytes=0)
    yield batch_writer
    batch_writer.close()


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


def _poller(
    *,
    store: Store,
    writer: IndexBatchWriter,
    tmp_path: Path,
    queue: _FakeQueue,
    bodies: dict[int, bytes | BaseException | None] | None = None,
    clients: list[object] | None = None,
) -> Poller:
    """Wire a poller to fakes, counting client creations when asked to."""

    def client_factory() -> AsyncNextcloudApp:
        made = object()
        if clients is not None:
            clients.append(made)
        return cast("AsyncNextcloudApp", made)

    return Poller(
        store=store,
        writer=writer,
        tmp_dir=tmp_path / "tmp",
        client_factory=client_factory,
        gateway_factory=lambda: cast("Any", _FakeGatewayClient()),
        queue_factory=lambda nc: cast("Any", queue),
        fetch=_gateway(bodies or {}),
        extract=dispatch_extract,
    )


def _documents(index: Index) -> int:
    index.reload()
    searcher = index.searcher()
    return searcher.search(index.parse_query("frist", [FIELD_BODY_DE]), 10).count


def _stored_ids(index: Index) -> list[int]:
    index.reload()
    searcher = index.searcher()
    hits = searcher.search(index.parse_query("frist", [FIELD_BODY_DE]), 10).hits
    return [int(searcher.doc(address)[FIELD_FILE_ID][0]) for _, address in hits]


async def test_a_job_is_indexed_committed_recorded_and_only_then_acknowledged(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path
) -> None:
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    result = await poller.run_once()

    assert result.state == PASS_WORKED
    assert result.indexed == 1
    assert _documents(index) == 1
    row = store.file_row(4711)
    assert row is not None
    assert row["state"] == "indexed"
    assert row["content_hash"]
    assert queue.acknowledged == [([91], {})]


async def test_the_order_is_commit_then_state_then_acknowledge(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The reversed order does not raise anywhere. It loses documents quietly,
    # which is why this sequence is asserted rather than reviewed.
    events: list[str] = []
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    real_flush = writer.flush
    real_record = store.record
    real_acknowledge = queue.acknowledge

    def flush() -> Any:
        events.append("commit")
        return real_flush()

    def record(*args: Any, **kwargs: Any) -> None:
        events.append("record")
        real_record(*args, **kwargs)

    async def acknowledge(*args: Any, **kwargs: Any) -> CallResult:
        events.append("acknowledge")
        return await real_acknowledge(*args, **kwargs)

    monkeypatch.setattr(writer, "flush", flush)
    monkeypatch.setattr(store, "record", record)
    monkeypatch.setattr(queue, "acknowledge", acknowledge)

    await poller.run_once()

    assert events == ["commit", "record", "acknowledge"]


async def test_a_job_the_judge_rejects_is_acknowledged_without_reading_bytes(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # A film has no text. Reading fifty megabytes to find that out would be the
    # most expensive way of learning what the mimetype already says.
    queue = _FakeQueue(ClaimResult(jobs=(_job(mime="video/mp4"),)))
    reads: list[int] = []

    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    fetch = poller._fetch_file  # noqa: SLF001

    async def counting_fetch(*args: Any, **kwargs: Any) -> Any:
        reads.append(1)
        return await fetch(*args, **kwargs)

    poller._fetch_file = counting_fetch  # type: ignore[method-assign]  # noqa: SLF001

    result = await poller.run_once()

    assert reads == []
    assert result.skipped == 1
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("skipped", "mime_not_allowed")
    assert queue.acknowledged == [([91], {})]


async def test_a_gone_file_is_acknowledged_as_skipped_gone(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # 404 is what the gateway answers for "does not exist" and for "not yours"
    # alike, deliberately indistinguishable. Either way there is nothing to index
    # and the row must leave the queue.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: None})

    result = await poller.run_once()

    assert result.skipped == 1
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("skipped", "gone")
    assert queue.acknowledged == [([91], {})]


async def test_a_gateway_error_aborts_the_batch_and_acknowledges_nothing(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # A 500 says nothing about the file. Recording a verdict from it would put a
    # wrong reason on a document that is perfectly fine, and the state store is
    # the thing phase 3 reads to decide what still needs work.
    queue = _FakeQueue(ClaimResult(jobs=(_job(), _job(92, 4712))))
    broken = NextcloudException(500, reason="gateway is down")
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: broken})
    before = poller.cooldown

    result = await poller.run_once()

    assert result.state == PASS_GATEWAY_UNAVAILABLE
    assert queue.acknowledged == []
    assert store.file_row(4711) is None
    assert queue.unlocked == [[91, 92]]
    assert poller.cooldown > before


async def test_an_unchanged_file_is_acknowledged_without_doing_the_work_again(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The cheap exit: same bytes, same generation, nothing to do. Without it every
    # redelivery after a lost acknowledgement would re-extract the file.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    second = await poller.run_once()

    assert second.unchanged == 1
    assert second.indexed == 0
    assert queue.acknowledged[1] == ([91], {})


async def test_crash_between_commit_and_state(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The most expensive moment of an abort: the index is durable, the verdict is
    # not. The row comes back after the lock timeout, the second pass does the
    # work again, and the upsert has to leave exactly one document behind.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    def dying_record(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise OSError("the volume went away between the commit and the verdict")

    monkeypatch.setattr(store, "record", dying_record)
    with pytest.raises(OSError, match="between the commit"):
        await poller.run_once()

    assert _documents(index) == 1
    assert queue.acknowledged == []

    monkeypatch.undo()
    result = await poller.run_once()

    assert result.indexed == 1
    assert _stored_ids(index) == [4711]
    assert _documents(index) == 1


async def test_the_acl_of_a_job_is_written_declaratively(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The crawl and the events both carry the target state, so a lost delivery
    # costs one round of staleness and repairs itself. An incremental variant
    # would be wrong forever after the first lost message and nothing would notice.
    store.replace_acl(4711, ["carol"])
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()

    assert store.prefilter_visible("alice", [4711]) == {4711}
    assert store.prefilter_visible("bob", [4711]) == {4711}
    assert store.prefilter_visible("carol", [4711]) == set()


async def test_one_client_per_run(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # A client per file would pay a connection setup per file and a Nextcloud
    # bootstrap including the signature check on the PHP side, for every one of
    # the hundred thousand files of an initial index.
    jobs = tuple(_job(90 + offset, 5000 + offset) for offset in range(10))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    clients: list[object] = []
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, clients=clients)

    result = await poller.run_once()

    assert result.indexed == 10
    assert len(clients) == 1

    await poller.run_once()

    assert len(clients) == 1


async def test_an_empty_queue_grows_the_cooldown_from_fifteen_to_at_most_one_hundred_twenty(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    queue = _FakeQueue()
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    seen: list[float] = []

    for _ in range(6):
        result = await poller.run_once()
        assert result.state == PASS_EMPTY
        seen.append(poller.cooldown)

    assert seen == [15, 30, 60, 120, 120, 120]


async def test_a_full_volume_ends_the_pass_and_hands_the_rows_back(
    index: Index, index_dir: Path, store: Store, tmp_path: Path
) -> None:
    # A worker that keeps running on a full volume turns a space problem into a
    # data loss. Nothing is committed, nothing is recorded, and the rows become
    # collectable again at once instead of after the lock timeout.
    guarded = IndexBatchWriter(index, directory=index_dir, min_free_bytes=1 << 60)
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=guarded, tmp_path=tmp_path, queue=queue)

    try:
        result = await poller.run_once()
    finally:
        guarded.close()

    assert result.state == PASS_PAUSED_LOW_DISK
    assert queue.acknowledged == []
    assert queue.unlocked == [[91]]
    assert store.file_row(4711) is None


async def test_an_unreachable_queue_is_a_state_and_not_a_crash(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    queue = _FakeQueue(ClaimResult(unavailable=True))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    result = await poller.run_once()

    assert result.state == PASS_QUEUE_UNAVAILABLE
    assert poller.cooldown == 15


async def test_shutdown_releases_the_held_ids(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = _FakeQueue(ClaimResult(jobs=(_job(), _job(92, 4712))))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    def dying_record(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise OSError("stopped in the middle")

    monkeypatch.setattr(store, "record", dying_record)
    with pytest.raises(OSError, match="stopped in the middle"):
        await poller.run_once()

    released = await poller.unlock_held()

    assert released == 2
    assert queue.unlocked == [[91, 92]]


async def test_the_scratch_file_is_gone_after_every_job(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The scratch files hold user content. Leaving one behind after a crash is a
    # disclosure, and leaving one behind on every job fills the volume.
    queue = _FakeQueue(ClaimResult(jobs=(_job(), _job(92, 4712))))
    scratch = tmp_path / "tmp"
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "leftover-4700.part").write_bytes(b"from a crash before this start")
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()

    assert sorted(entry.name for entry in scratch.iterdir()) == []


async def test_the_loop_stops_on_the_stop_event_without_running_while_silenced(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # A disabled backend that keeps polling is the classic of the integration
    # list, and it is invisible: the container looks healthy while it drains the
    # queue of an app the admin switched off.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    stop = asyncio.Event()

    task = asyncio.create_task(poller.run(stop))
    await asyncio.sleep(0.05)

    assert queue.claims == 0

    stop.set()
    await asyncio.wait_for(task, timeout=2)

    assert queue.claims == 0


def test_the_enabled_handler_arms_and_silences_the_poller() -> None:
    with TestClient(APP):
        poller = active_poller()

        assert poller is not None
        assert poller.armed is False

        asyncio.run(enabled_handler(True, cast("AsyncNextcloudApp", None)))
        assert poller.armed is True

        asyncio.run(enabled_handler(False, cast("AsyncNextcloudApp", None)))
        assert poller.armed is False

    assert active_poller() is None


def test_the_source_shows_commit_before_record_before_acknowledge() -> None:
    """The sequence as a property of the file, not only of one run.

    A refactoring that moves the acknowledgement above the commit passes every
    behavioural test that does not look for it, because nothing raises: the batch
    is simply gone from the queue and never in the index.
    """
    source = POLLER_SOURCE.read_text(encoding="utf-8")

    commit = source.index("self._writer.flush")
    record = source.index("self._store.record")
    acknowledge = source.index("queue.acknowledge")

    assert commit < record < acknowledge


def test_the_blocking_work_runs_off_the_event_loop() -> None:
    """The tantivy calls and the SQLite transaction belong in a worker thread.

    The warning sign of the mistake is in the phase research: /heartbeat hangs
    while /enabled still answers, because a long commit sits on the event loop.
    """
    source = POLLER_SOURCE.read_text(encoding="utf-8")

    assert source.count("to_thread") >= 2
    for blocking in ("self._writer.flush", "self._writer.add", "self._record_batch"):
        line = next(text for text in source.splitlines() if blocking in text and "to_thread" in text)

        assert "to_thread" in line, blocking


def test_no_log_call_names_a_path_a_title_or_a_piece_of_text() -> None:
    """Counters and reason codes only (T-02-107).

    A log line that echoes a file name puts user data into a place that is read
    by support, shipped in bug reports and rotated onto disk unencrypted.
    """
    offenders = re.findall(
        r"log(?:ger)?\.[a-z]+\(.*(?:path|title|snippet|text|term)",
        POLLER_SOURCE.read_text(encoding="utf-8"),
        flags=re.IGNORECASE,
    )

    assert offenders == []


def test_the_poller_builds_exactly_one_client() -> None:
    """One creation in the file, so a second one is a visible change."""
    assert POLLER_SOURCE.read_text(encoding="utf-8").count("create_app_client") == 1


def test_the_shutdown_path_releases_what_the_container_holds() -> None:
    """The lifespan has to hand the rows back, otherwise a restart waits."""
    assert "unlock" in MAIN_SOURCE.read_text(encoding="utf-8")
