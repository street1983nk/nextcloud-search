"""The second trailing track, and the delete path that has to keep up with it.

Two subjects, and they belong in one file because each of them is the other
one's safety net.

*The track* fills the vector stock after the text pass is through. What makes it
a track and not a step is the one line it does not contain: the OCR track loads
the file a second time, this one does not. The text it embeds is the copy the
index already stores, which is the whole argument of
``IndexBatchWriter.stored_body``, and a test here holds it by counting the byte
fetches of a pass that embedded a document.

*The delete path* is the reason a vector cannot outlive its document. A vector
that survives its file keeps answering semantic queries out of a stock nobody
expects any more, and the prefilter only catches that for as long as the acl
rows really do disappear. Four places write that rule down, and every one of
them has a case below.

Everything here runs against a real vector store, a real index and a real state
database. The only stand-ins are the two things that would need 118 MB of
weights on the machine that runs the suite: the chunker and the model. What they
replace is arithmetic, and what stays real is every decision this plan is about.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any, cast

import pytest
from tantivy import Index

from findling.config import settings
from findling.embed.chunker import ChunkSpan
from findling.embed.model import DIMENSIONS, EMBEDDING_UNAVAILABLE, EmbedOutcome
from findling.extract.dispatch import Route
from findling.extract.dispatch import extract as dispatch_extract
from findling.extract.errors import ExtractionOutcome, Reason
from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter, IndexRecord
from findling.nc.client import AsyncNextcloudApp
from findling.nc.queue import CallResult, ClaimResult, QueueJob, QueueStats
from findling.store.repo import Store, open_store
from findling.store.vectors import Chunk, VectorStore, open_vectors
from findling.worker.poller import (
    EMBED_INCOMPLETE,
    EMBED_NO_STORED_TEXT,
    EMBED_WRITTEN,
    ROUND_PAUSED_LOW_DISK,
    ROUND_WORKED,
    Poller,
)

POLLER_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "worker" / "poller.py"
PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"

CONSTITUENTS = (
    (Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt").read_text(encoding="utf-8").split()
)

# The text of the file under test. Long enough that the stand-in chunker cuts it
# into more than one piece, because a document with exactly one chunk would make
# the ordinal, the offsets and the replace-before-insert rule untestable.
BODY = "Die Kuendigungsfrist betraegt drei Monate und gilt fuer alle Beschaeftigten dieses Hauses."
BODY_BYTES = BODY.encode("utf-8")

# The name of the file, and one of the words that must never turn up in a log.
TITLE = "Kuendigung.txt"

# How wide the stand-in chunker cuts, and how many chunks that makes of BODY.
CHUNK_WIDTH = 20


# -- the stand-ins ----------------------------------------------------------


def _cut(text: str) -> list[ChunkSpan]:
    """A chunker that cuts every CHUNK_WIDTH characters, offsets included.

    It stands in for ``chunk_spans`` and replaces exactly the part that needs a
    17 MB tokenizer to run: where the cuts fall. What it keeps is the shape the
    store is fed with, three numbers per chunk, so every assertion below is
    about the track and not about the splitter.
    """
    if not text.strip():
        return []
    return [
        ChunkSpan(ordinal=ordinal, char_start=start, char_end=min(start + CHUNK_WIDTH, len(text)))
        for ordinal, start in enumerate(range(0, len(text), CHUNK_WIDTH))
    ]


@dataclass(slots=True)
class _FakeModel:
    """The engine, replaced by one that answers arithmetic and writes it down.

    ``unavailable`` is the state of a container without weights, which is the
    normal state of a developer machine and of every instance whose admin never
    installed the model. ``short_by`` produces the one answer a model must never
    give unnoticed: fewer vectors than there were chunks.
    """

    unavailable: bool = False
    short_by: int = 0
    calls: list[list[str]] = field(default_factory=list)

    def embed_passages(self, texts: Sequence[str]) -> EmbedOutcome:
        self.calls.append(list(texts))
        if self.unavailable:
            return EmbedOutcome.unavailable()
        wanted = max(0, len(texts) - self.short_by)
        return EmbedOutcome.ready([[(index + 1) / 1000] * DIMENSIONS for index in range(wanted)])


class _FakeQueue:
    """The four queue calls, answered from a script and recorded."""

    def __init__(self, *batches: ClaimResult) -> None:
        self._batches = list(batches)
        self.claims = 0
        self.acknowledged: list[tuple[list[int], dict[int, str]]] = []
        self.unlocked: list[list[int]] = []
        self.requeues: list[tuple[list[int], str]] = []
        self.requeue_fails = False

    async def claim(self, *, limit: int, max_bytes: int) -> ClaimResult:
        del limit, max_bytes
        self.claims += 1
        return self._batches.pop(0) if self._batches else ClaimResult()

    async def acknowledge(self, done: Any, failed: Any, skipped: Any = None) -> CallResult:
        del skipped
        self.acknowledged.append((list(done), dict(failed)))
        return CallResult(ok=True, count=len(done) + len(failed))

    async def unlock(self, ids: Any) -> CallResult:
        self.unlocked.append(list(ids))
        return CallResult(ok=True, count=len(ids))

    async def requeue(self, file_ids: Any, *, kind: str) -> CallResult:
        self.requeues.append((list(file_ids), kind))
        if self.requeue_fails:
            return CallResult(ok=False)
        return CallResult(ok=True, count=len(list(file_ids)))

    async def stats(self) -> QueueStats:
        return QueueStats()


class _FakeGatewayClient:
    async def aclose(self) -> None:
        return None


def _gateway(fetched: list[int], body: bytes = BODY_BYTES) -> Callable[..., Any]:
    """A byte fetch that records every file id it was asked for.

    The counter is the whole proof of the sentence this plan is written around:
    an embedding job that quietly downloaded the file would leave exactly the
    same vector stock behind.
    """

    async def fetch(
        nc: AsyncNextcloudApp,
        file_id: int,
        user_id: str,
        fp: IO[bytes],
        *,
        client: Any = None,
    ) -> int | None:
        del nc, user_id, client
        fetched.append(file_id)
        fp.write(body)
        return len(body)

    return fetch


@dataclass(slots=True)
class _Extractor:
    """The guarded extractor, run in this process instead of in a child.

    With ``outcome`` unset it hands the file to the real dispatcher, which keeps
    the verdicts and the character cap the real ones. With an outcome set it
    answers that instead, which is how a verdict is reached here without the
    file that would produce it.
    """

    outcome: ExtractionOutcome | None = None

    def __call__(
        self,
        path: str,
        mime: str,
        size: int,
        *,
        route: Route | None = None,
        timeout_seconds: float | None = None,
    ) -> ExtractionOutcome:
        del timeout_seconds
        if self.outcome is not None:
            return self.outcome
        return dispatch_extract(path, mime, size, route)


def _job(
    queue_id: int = 91,
    file_id: int = 4711,
    *,
    kind: str = "content",
    users: tuple[str, ...] = ("alice", "bob"),
) -> QueueJob:
    return QueueJob(
        queue_id=queue_id,
        file_id=file_id,
        storage_id=3,
        root_id=2,
        path=f"Vertraege/{TITLE}",
        title=TITLE,
        mime="text/plain",
        size=len(BODY_BYTES),
        mtime=1_756_600_000,
        etag="5d41402abc4b2a76b9719d911017c592",
        kind=kind,
        user_ids=users,
        fetch_as=users[0] if users else "",
        is_update=False,
    )


# -- fixtures ---------------------------------------------------------------


@pytest.fixture
def index_dir(tmp_path: Path) -> Path:
    return tmp_path / "index"


@pytest.fixture
def index(index_dir: Path) -> Index:
    return open_index(index_dir, CONSTITUENTS)


@pytest.fixture
def writer(index: Index, index_dir: Path) -> Iterator[IndexBatchWriter]:
    batch = IndexBatchWriter(index, directory=index_dir, min_free_bytes=0)
    yield batch
    batch.close()


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


@pytest.fixture
def vectors(tmp_path: Path) -> Iterator[VectorStore]:
    stock = open_vectors(tmp_path / "vectors.db")
    yield stock
    stock.close()


@pytest.fixture
def embed_off(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """An instance whose admin switched the embedding off, through the variable.

    The cache is cleared on both sides for the reason the OCR fixture next door
    clears it: the settings are resolved once per process by design, and a test
    that changed the environment without clearing would hand its answer on.
    """
    monkeypatch.setenv("FINDLING_EMBED_ENABLED", "false")
    settings.cache_clear()
    yield
    settings.cache_clear()


@pytest.fixture
def tight_disk(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """A free space floor no volume on this planet clears."""
    monkeypatch.setenv("FINDLING_MIN_FREE_BYTES", str(2**62))
    settings.cache_clear()
    yield
    settings.cache_clear()


def _poller(
    *,
    store: Store,
    writer: IndexBatchWriter,
    tmp_path: Path,
    queue: _FakeQueue,
    vectors: VectorStore | None = None,
    model: _FakeModel | None = None,
    fetched: list[int] | None = None,
    extract: _Extractor | None = None,
) -> Poller:
    """A poller whose second track is wired to a real stock and a fake engine."""
    return Poller(
        store=store,
        writer=writer,
        tmp_dir=tmp_path / "tmp",
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        gateway_factory=lambda: cast("Any", _FakeGatewayClient()),
        queue_factory=lambda nc: cast("Any", queue),
        fetch=_gateway([] if fetched is None else fetched),
        extract=_Extractor() if extract is None else extract,
        vectors=vectors,
        chunker=None if vectors is None else _cut,
        model=None if vectors is None else (model or _FakeModel()),
    )


def _index_the_body(writer: IndexBatchWriter, file_id: int = 4711, body: str = BODY) -> None:
    """Put one document into the index and commit it, the way a text pass would."""
    writer.add(
        IndexRecord(
            file_id=file_id,
            storage_id=3,
            name=TITLE,
            title=TITLE,
            path=f"Vertraege/{TITLE}",
            ext="txt",
            body=body,
            mtime=1_756_600_000,
        )
    )
    writer.flush()


# -- the handover -----------------------------------------------------------


async def test_an_indexed_document_goes_to_the_embedding_track(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # D-15 in one pass: the text pass ends, the document is in the index, and
    # the row is put on the second track instead of leaving the queue.
    #
    # The second assertion carries as much as the first, exactly as it does for
    # the OCR handover: acknowledging is deleting, so a row that travelled in
    # both would be gone from the queue in the same pass in which the requeue
    # put work on it, and the document would never get a vector.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    result = await poller.run_once()

    assert queue.requeues == [([4711], "embed")]
    assert queue.acknowledged == [([], {})]
    assert result.requeued == 1
    row = store.file_row(4711)
    assert row is not None
    assert row["state"] == "indexed"


async def test_nothing_goes_to_the_track_when_the_switch_is_off(
    embed_off: None, store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # An instance whose admin switched the embedding off gets the end verdict
    # and no row that waits for a track which does not exist there. This is the
    # sentence the OCR branch already carries, applied to the second track.
    del embed_off
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    result = await poller.run_once()

    assert queue.requeues == []
    assert queue.acknowledged == [([91], {})]
    assert result.requeued == 0
    assert result.indexed == 1


async def test_a_document_without_text_does_not_go_to_the_track(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # A file that ends as skipped has no text to embed, and a chunk of nothing
    # would cost a vector, a row and a rank with a distance nobody can read.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=queue,
        vectors=vectors,
        extract=_Extractor(outcome=ExtractionOutcome.skipped(Reason.EMPTY_TEXT)),
    )

    result = await poller.run_once()

    assert queue.requeues == []
    assert result.skipped == 1
    assert queue.acknowledged == [([91], {})]


async def test_the_handover_happens_after_the_commit_and_before_the_acknowledgement(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The same ordering the OCR handover follows, and for the same reason. An
    # abort right here costs one repeated pass over a document that is already
    # in the index; an acknowledgement before the requeue would delete the row
    # the requeue was about to put work on.
    events: list[str] = []
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    real_flush, real_record = writer.flush, store.record
    real_requeue, real_acknowledge = queue.requeue, queue.acknowledge

    def flush() -> Any:
        events.append("commit")
        return real_flush()

    def record(*args: Any, **kwargs: Any) -> None:
        events.append("record")
        real_record(*args, **kwargs)

    async def requeue(*args: Any, **kwargs: Any) -> CallResult:
        events.append("requeue")
        return await real_requeue(*args, **kwargs)

    async def acknowledge(*args: Any, **kwargs: Any) -> CallResult:
        events.append("acknowledge")
        return await real_acknowledge(*args, **kwargs)

    monkeypatch.setattr(writer, "flush", flush)
    monkeypatch.setattr(store, "record", record)
    monkeypatch.setattr(queue, "requeue", requeue)
    monkeypatch.setattr(queue, "acknowledge", acknowledge)

    await poller.run_once()

    assert events == ["commit", "record", "requeue", "acknowledge"]


async def test_a_lost_handover_is_repeated_and_does_not_end_the_pass(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # The abort between the commit and the acknowledgement, staged as the
    # failure that produces it: the requeue does not reach Nextcloud. The pass
    # finishes, because index and verdict are already durable; the rows are not
    # acknowledged, so they run into the lock timeout and come back; and the
    # second pass hands them over again instead of writing them off.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_job(),)))
    queue.requeue_fails = True
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    first = await poller.run_once()
    queue.requeue_fails = False
    second = await poller.run_once()

    assert first.state == ROUND_WORKED
    assert first.requeued == 0
    assert second.requeued == 1
    assert queue.requeues == [([4711], "embed"), ([4711], "embed")]
    assert queue.acknowledged == [([], {}), ([], {})]


async def test_a_rename_puts_the_document_back_on_the_track(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # The window this closes: a rename outranks an embedding row (KIND_RANK), so
    # a move between the handover and the claim takes the row off the track. The
    # metadata pass writes the same text into the index again and ends indexed,
    # so it hands the file over once more and the vectors are not lost for good.
    # It costs one repeated embedding of an unchanged text, and replace_chunks
    # is what makes that repetition harmless.
    _index_the_body(writer)
    seen: list[int] = []
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="metadata"),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors, fetched=seen)

    result = await poller.run_once()

    assert queue.requeues == [([4711], "embed")]
    assert result.requeued == 1
    assert seen == []


async def test_a_scanned_document_reaches_the_track_after_the_ocr_pass(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # The two trailing tracks in sequence, which is the case the semantics of a
    # typical administration hang off: the text of a scan exists only because
    # OCR read it, and it has to reach the vector stock like any other.
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="ocr"),)))
    poller = _poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=queue,
        vectors=vectors,
        extract=_Extractor(outcome=ExtractionOutcome.indexed(BODY)),
    )

    result = await poller.run_once()

    assert queue.requeues == [([4711], "embed")]
    assert result.requeued == 1


# -- the job itself ---------------------------------------------------------


async def test_an_embed_job_reads_the_stored_text_and_never_the_file(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # The one line this track does not have. The OCR track fetches the file a
    # second time; this one reads body_de, which is the only stored copy of the
    # extracted text in the whole system. A fetch here would produce exactly the
    # same stock, so the byte counter is the only witness there is.
    _index_the_body(writer)
    seen: list[int] = []
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="embed"),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors, fetched=seen)

    result = await poller.run_once()

    assert seen == []
    assert result.embedded == 1
    assert queue.acknowledged == [([91], {})]
    assert vectors.chunk_count() == len(_cut(BODY))
    assert vectors.vector_count() == vectors.chunk_count()


async def test_an_embed_job_stores_the_offsets_of_the_text_it_read(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # The offsets are characters into the stored body, and they are what a
    # snippet is later cut with. A chunk whose span does not address its own
    # passage is a hit that shows the wrong sentence.
    _index_the_body(writer)
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="embed"),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    await poller.run_once()

    spans = vectors.chunks_of([4711])[4711]
    assert [span.ordinal for span in spans] == list(range(len(_cut(BODY))))
    assert BODY[spans[0].char_start : spans[0].char_end] == BODY[:CHUNK_WIDTH]


async def test_an_embed_job_produces_no_second_handover(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # T-06-33, which is T-03-704 seen from the second track: a row that came
    # through the handover must not be put on it again, or the two of them keep
    # each other alive forever.
    _index_the_body(writer)
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="embed"),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    await poller.run_once()

    assert queue.requeues == []


async def test_the_same_embed_job_twice_leaves_the_chunk_count_alone(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # T-06-32. A redelivery is the normal case and not the exception: the rows
    # come back whenever a pass dies between the write and the acknowledgement,
    # and without the delete before the insert the stock of this document would
    # double every single time.
    _index_the_body(writer)
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="embed"),)), ClaimResult(jobs=(_job(kind="embed"),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    await poller.run_once()
    after_one = vectors.chunk_count()
    await poller.run_once()

    assert after_one > 1
    assert vectors.chunk_count() == after_one
    assert vectors.vector_count() == after_one


async def test_a_missing_model_ends_the_job_and_the_pass_carries_on(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # A container without weights is the ordinary state of an instance whose
    # admin never installed the model, and it is not an error: the row leaves
    # the queue, the pass carries on, and nothing is written into the stock.
    _index_the_body(writer)
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="embed"),)))
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors, model=_FakeModel(unavailable=True)
    )

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert result.embedded == 0
    assert queue.acknowledged == [([91], {})]
    assert vectors.chunk_count() == 0


async def test_a_job_whose_document_carries_no_stored_text_is_acknowledged(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # stored_body answers None for a file that was never indexed or ended as
    # skipped. That is an answer and not a failure, and the row has to leave the
    # queue: a row that stayed would circle until the give-up rule ended it as
    # failed(repeatedly_stuck) for a document that is simply not there.
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="embed"),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    result = await poller.run_once()

    assert result.embedded == 0
    assert queue.acknowledged == [([91], {})]
    assert queue.requeues == []


async def test_a_model_that_answers_short_writes_nothing(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # Fewer vectors than chunks is the one wrong answer that looks right: the
    # rows would be written with the offsets of other passages, and nothing in
    # the system would ever notice. Half a document is worse than none of it.
    _index_the_body(writer)
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="embed"),)))
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors, model=_FakeModel(short_by=1)
    )

    result = await poller.run_once()

    assert result.embedded == 0
    assert vectors.chunk_count() == 0
    assert queue.acknowledged == [([91], {})]


async def test_every_ending_of_an_embed_job_has_a_name_of_its_own(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # The four endings are named constants and not booleans, because the status
    # page of plan 06-08 has to be able to tell "no model here" from "this
    # document has no text" without guessing. Driven against the branch itself,
    # since none of them is ever written into findling_file_state: a document
    # that could not be embedded is still indexed (D-15).
    _index_the_body(writer)
    queue = _FakeQueue()
    done: list[int] = []

    written = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)
    no_text = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)
    short = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors, model=_FakeModel(short_by=1)
    )
    missing = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors, model=_FakeModel(unavailable=True)
    )

    assert await written._embed_the_body(_job(kind="embed"), done) == EMBED_WRITTEN
    assert await no_text._embed_the_body(_job(kind="embed", file_id=9999), done) == EMBED_NO_STORED_TEXT
    assert await short._embed_the_body(_job(kind="embed"), done) == EMBED_INCOMPLETE
    assert await missing._embed_the_body(_job(kind="embed"), done) == EMBEDDING_UNAVAILABLE
    # Every one of them acknowledges its row. None of them may leave it behind.
    assert done == [91, 91, 91, 91]


async def test_a_tight_disk_writes_no_vectors_and_hands_the_rows_back(
    tight_disk: None, store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # T-06-36. Below the free space floor the pass behaves the way it already
    # does for the index: nothing is written, the rows go back unjudged, and the
    # operating state says why. Half a vector stock is the alternative.
    del tight_disk
    _index_the_body(writer)
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="embed"),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    result = await poller.run_once()

    assert result.state == ROUND_PAUSED_LOW_DISK
    assert vectors.chunk_count() == 0
    assert queue.acknowledged == []
    assert queue.unlocked == [[91]]


async def test_an_embed_row_on_an_instance_without_the_track_leaves_the_queue(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The row an admin left behind by switching the embedding off, or by
    # removing the model. It has to be acknowledged rather than kept: a row that
    # waits for a track which does not exist on this instance is exactly the
    # failure this plan promises not to produce.
    _index_the_body(writer)
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="embed"),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert result.embedded == 0
    assert queue.acknowledged == [([91], {})]


async def test_an_embed_job_writes_the_permissions_of_its_row(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # The counterpart of the rank decision on the PHP side. An embedding row is
    # not displaced by an acl change (KIND_RANK), so a share that arrives while
    # the row waits travels on the row it upgraded, and this branch is what
    # writes it down, exactly as the unchanged-file exit does (bug audit M1).
    _index_the_body(writer)
    store.replace_acl(4711, ["alice"])
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="embed", users=("alice", "bob", "carol")),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    await poller.run_once()

    assert store.prefilter_visible("carol", [4711]) == {4711}


async def test_no_line_of_the_second_track_names_a_text_or_a_file(
    store: Store,
    writer: IndexBatchWriter,
    vectors: VectorStore,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # T-06-35. A log line is the one place where the content of a private
    # instance leaves the permission model, and it is broken while somebody adds
    # a helpful detail rather than on purpose. A failing pass is driven as well,
    # because a warning is where a file name gets added.
    _index_the_body(writer)
    queue = _FakeQueue(
        ClaimResult(jobs=(_job(kind="embed"),)),
        ClaimResult(jobs=(_job(kind="embed"),)),
    )
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors, model=_FakeModel(short_by=1)
    )

    with caplog.at_level(logging.DEBUG, logger="findling.worker.poller"):
        await poller.run_once()
        await poller.run_once()

    lines = [record.getMessage() for record in caplog.records]
    assert lines != []
    for line in lines:
        assert TITLE not in line
        assert "Kuendigungsfrist" not in line
        assert "Vertraege" not in line


def test_the_second_track_does_not_fetch_a_file_in_the_source() -> None:
    """The property the byte counter proves, held a second time by reading.

    A counter proves it for the paths a test drives. This holds it for the
    branch as a whole: whatever it is given, ``_embed_the_body`` may not grow a
    call to the gateway, and the two names below are the only ways to make one.
    """
    source = POLLER_SOURCE.read_text(encoding="utf-8")
    start = source.index("async def _embed_the_body")
    body = source[start : source.index("\n    def ", start)]

    assert "_fetch_file" not in body
    assert "_stream_into" not in body
    assert "stored_body" in body


# -- the delete path --------------------------------------------------------


def _fill(stock: VectorStore, file_id: int, chunks: int = 2) -> None:
    """Give one file a stock of its own, so a deletion has something to remove."""
    stock.replace_chunks(
        file_id,
        [
            Chunk(ordinal=ordinal, char_start=ordinal * 10, char_end=ordinal * 10 + 10, embedding=bytes(DIMENSIONS))
            for ordinal in range(chunks)
        ],
    )


def test_a_dropped_document_loses_its_chunks_and_its_vectors(
    index: Index, index_dir: Path, vectors: VectorStore
) -> None:
    # D-21 at the index writer. A vector that outlives its document keeps
    # answering semantic queries for a file nobody can open any more, and the
    # neighbour proves the deletion was aimed rather than broad.
    writer = IndexBatchWriter(index, directory=index_dir, min_free_bytes=0, vectors=vectors)
    try:
        _fill(vectors, 4711)
        _fill(vectors, 4712)

        writer.drop_document(4711)
    finally:
        writer.close()

    assert vectors.chunks_of([4711]) == {}
    assert vectors.chunks_of([4712]) != {}
    assert vectors.vector_count() == 2


def test_a_tombstone_loses_its_chunks_and_its_vectors(store: Store, vectors: VectorStore) -> None:
    # D-21 at the state database. The tombstone is what makes a deletion visible
    # to the reconcile, and the vectors have to go with it.
    store.attach_vectors(vectors)
    _fill(vectors, 4711)

    store.tombstone(4711)

    assert vectors.chunks_of([4711]) == {}
    assert vectors.chunk_count() == 0


def test_a_reindex_empties_the_whole_vector_stock(store: Store, vectors: VectorStore) -> None:
    # A rebuild that left the old vectors in place would keep answering out of a
    # stock that belongs to another model, and the answers would look ordinary
    # while being wrong. The stock carries no generation of its own, so there is
    # no half of it that could be kept.
    store.attach_vectors(vectors)
    _fill(vectors, 4711)
    _fill(vectors, 4712)

    store.reset_for_reindex(2)

    assert vectors.chunk_count() == 0
    assert vectors.vector_count() == 0


def test_a_second_write_of_the_same_file_does_not_double_the_stock(vectors: VectorStore) -> None:
    # The fourth of the four places, and the only one that was already built:
    # replace_chunks deletes before it inserts. Held by a test here because the
    # write path is where a redelivery would double the stock in silence.
    _fill(vectors, 4711, chunks=3)
    _fill(vectors, 4711, chunks=3)

    assert vectors.chunk_count() == 3


def test_a_file_that_comes_back_with_new_text_carries_no_chunk_of_the_old_one(vectors: VectorStore) -> None:
    # The same rule from the other side: fewer chunks than before, so a stale row
    # would survive a plain overwrite and answer with an offset into a text that
    # does not exist any more.
    _fill(vectors, 4711, chunks=5)

    _fill(vectors, 4711, chunks=1)

    spans = vectors.chunks_of([4711])[4711]
    assert [span.ordinal for span in spans] == [0]


def test_a_delete_path_without_a_vector_handle_runs_unchanged(store: Store, index: Index, index_dir: Path) -> None:
    # The instance on which the embedding never ran. There is no stock to clean,
    # and the full text path may not depend on one being there.
    writer = IndexBatchWriter(index, directory=index_dir, min_free_bytes=0)
    try:
        writer.add(
            IndexRecord(
                file_id=4711,
                storage_id=3,
                name=TITLE,
                title=TITLE,
                path=f"Vertraege/{TITLE}",
                ext="txt",
                body=BODY,
                mtime=1_756_600_000,
            )
        )
        writer.flush()

        writer.drop_document(4711)
        writer.flush()
    finally:
        writer.close()

    index.reload()
    assert index.searcher().num_docs == 0
    assert store.tombstone(4711) == 0


def test_a_failing_vector_handle_does_not_stop_the_full_text_delete_path(
    store: Store, caplog: pytest.LogCaptureFixture
) -> None:
    # A vector database that has gone away must not take the deletion of the
    # document with it. The failure is reported by type name, which is the whole
    # of what a log line of this project is allowed to say.
    class _Broken:
        def drop_vectors(self, file_id: int) -> int:
            del file_id
            raise OSError("disk gone")

        def forget_all(self) -> None:
            raise OSError("disk gone")

    store.attach_vectors(cast("Any", _Broken()))

    with caplog.at_level(logging.WARNING, logger="findling.store.repo"):
        assert store.tombstone(4711) == 0
        store.reset_for_reindex(2)

    messages = [record.getMessage() for record in caplog.records]
    assert any("OSError" in message for message in messages)
    assert all("disk gone" not in message for message in messages)


def test_a_deletion_of_a_file_without_vectors_is_not_an_error(store: Store, vectors: VectorStore) -> None:
    # The everyday case: the delete path runs for every removed document, and
    # most of them never had a vector. Asking first would be a second query per
    # deletion for an answer the deletion already gives.
    store.attach_vectors(vectors)

    assert store.tombstone(9999) == 0
    assert vectors.drop_vectors(9999) == 0


async def test_the_delete_job_of_the_poller_takes_the_vectors_with_it(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # The four places joined up, driven through the pass that uses them. A
    # NodeDeleted event ends here, and afterwards neither the index nor the
    # stock holds anything of the file.
    _index_the_body(writer)
    _fill(vectors, 4711)
    queue = _FakeQueue(ClaimResult(jobs=(_job(kind="delete"),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    await poller.run_once()

    assert vectors.chunk_count() == 0
    assert vectors.vector_count() == 0
    assert queue.acknowledged == [([91], {})]


def test_no_module_of_the_delete_path_carries_the_forbidden_identifier() -> None:
    """Gate A, held where the new calls were added.

    The identifier ``delete`` is forbidden in every module of this package, and
    a delete path is exactly where somebody would name a helper after what it
    does.
    """
    for module in (PACKAGE_ROOT / "index" / "writer.py", PACKAGE_ROOT / "store" / "repo.py"):
        assert "def delete" not in module.read_text(encoding="utf-8")
