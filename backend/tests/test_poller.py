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
import hashlib
import re
import shutil
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import IO, Any, cast

import pytest
from fastapi.testclient import TestClient
from tantivy import Index

from conftest import write_wordlist
from findling.config import settings
from findling.extract.dispatch import Route
from findling.extract.dispatch import extract as dispatch_extract
from findling.extract.errors import ExtractionOutcome, Reason
from findling.index.open import expected_versions, open_index
from findling.index.schema import FIELD_BODY_DE, FIELD_FILE_ID, FIELD_NAME
from findling.index.writer import IndexBatchWriter
from findling.main import APP, active_poller, enabled_handler
from findling.nc.client import AsyncNextcloudApp, NextcloudException
from findling.nc.queue import CallResult, ClaimResult, QueueJob, QueueStats
from findling.store.repo import FileMeta, Store, open_store
from findling.worker.poller import (
    RETREAT_AFTER_ROUNDS,
    RETREAT_MAX_SECONDS,
    ROUND_EMPTY,
    ROUND_GATEWAY_UNAVAILABLE,
    ROUND_PAUSED_LOW_DISK,
    ROUND_QUEUE_UNAVAILABLE,
    ROUND_WORKED,
    Poller,
    _open_state,
    _raise_generation_for_lost_index,
)

POLLER_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "worker" / "poller.py"
MAIN_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "main.py"

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()

BODY = "Die Kündigungsfrist beträgt drei Monate.\n"
BODY_BYTES = BODY.encode("utf-8")

# A scanned PDF out of the reference corpus, pixels and no text layer. It is read
# here rather than built, because the verdict this file is about,
# skipped(no_text_layer), is produced by the real extractor and a hand written
# stand-in would only prove that the stand-in says so.
SCAN_BYTES = (Path(__file__).resolve().parents[2] / "testdata" / "corpus" / "02-scan-no-text-layer.pdf").read_bytes()

CORPUS = Path(__file__).resolve().parents[2] / "testdata" / "corpus"

# Three A4 pages of council prose that exist only as pixels. Bebauungsplan stands
# in no other file of the corpus and in none of them as text, so a search that
# finds this document through that word found it because OCR read the pixels.
COUNCIL_SCAN_BYTES = (CORPUS / "13-ratsvorlage-scan.pdf").read_bytes()
COUNCIL_SCAN_TERM = "Bebauungsplan"

# The counterpart, a PDF that carries its text as text (D-06).
TEXT_LAYER_BYTES = (CORPUS / "01-text-layer.pdf").read_bytes()

needs_engine = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="no tesseract on this machine; the container runs this test for real",
)

# The same file after a rename. Neither word occurs in the body, so a search that
# finds the document under this name found it through FIELD_NAME and nothing else.
RENAMED_TITLE = "Aufhebungsvertrag.txt"
RENAMED_PATH = "Vertraege/2026/Aufhebungsvertrag.txt"


def _job(
    queue_id: int = 91,
    file_id: int = 4711,
    *,
    mime: str = "text/plain",
    size: int | None = None,
    kind: str = "content",
    title: str = "Kuendigung.txt",
    path: str = "Vertraege/Kuendigung.txt",
    users: tuple[str, ...] = ("alice", "bob"),
) -> QueueJob:
    return QueueJob(
        queue_id=queue_id,
        file_id=file_id,
        storage_id=3,
        root_id=2,
        path=path,
        title=title,
        mime=mime,
        size=len(BODY_BYTES) if size is None else size,
        mtime=1_756_600_000,
        etag="5d41402abc4b2a76b9719d911017c592",
        kind=kind,
        user_ids=users,
        fetch_as=users[0] if users else "",
        is_update=False,
    )


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

    async def acknowledge(self, done: Any, failed: Any) -> CallResult:
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
    """Stands in for the pooled HTTP client; only its closing is observable."""

    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


def _gateway(bodies: dict[int, bytes | BaseException | None], fetched: list[int] | None = None) -> Callable[..., Any]:
    """A fetch_file_stream doppelganger driven by a table of file ids.

    ``fetched`` records every file id whose bytes were asked for. That counter is
    the only way to prove a job stayed off the network: a metadata job that
    quietly downloaded the file would produce exactly the same index.
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
        if fetched is not None:
            fetched.append(file_id)
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
def ocr_off(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """An instance whose admin switched OCR off, through the documented variable.

    The cache is cleared on both sides, exactly like the volume fixture does it:
    the settings are resolved once per process by design, and a test that changed
    the environment without clearing would hand its answer to the next one.
    """
    monkeypatch.setenv("FINDLING_OCR_ENABLED", "false")
    settings.cache_clear()
    yield
    settings.cache_clear()


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


@dataclass(slots=True)
class _Extractor:
    """The guarded extractor, replaced by one that writes down how it was called.

    With ``outcome`` unset it hands the file to the real dispatcher, which is what
    keeps the verdicts, the reasons and the character cap the real ones. With an
    outcome set it answers that instead, which is the only way to reach a verdict
    of the OCR route on a machine without an engine.

    The recorded ``route`` and ``timeout_seconds`` are the subject of two tests on
    their own: a job that quietly took the text route with the short deadline
    would produce exactly the same index as one that did neither.
    """

    outcome: ExtractionOutcome | None = None
    error: BaseException | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __call__(
        self,
        path: str,
        mime: str,
        size: int,
        *,
        route: Route | None = None,
        timeout_seconds: float | None = None,
    ) -> ExtractionOutcome:
        self.calls.append({"path": path, "mime": mime, "size": size, "route": route, "timeout": timeout_seconds})
        if self.error is not None:
            raise self.error
        if self.outcome is not None:
            return self.outcome
        return dispatch_extract(path, mime, size, route)


def _poller(
    *,
    store: Store,
    writer: IndexBatchWriter,
    tmp_path: Path,
    queue: _FakeQueue,
    bodies: dict[int, bytes | BaseException | None] | None = None,
    clients: list[object] | None = None,
    fetched: list[int] | None = None,
    extract: _Extractor | None = None,
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
        fetch=_gateway(bodies or {}, fetched),
        extract=_Extractor() if extract is None else extract,
    )


def _documents(index: Index) -> int:
    index.reload()
    searcher = index.searcher()
    return len(searcher.search(index.parse_query("frist", [FIELD_BODY_DE]), 10).hits)


def _stored_ids(index: Index) -> list[int]:
    index.reload()
    searcher = index.searcher()
    hits = searcher.search(index.parse_query("frist", [FIELD_BODY_DE]), 10).hits
    return [int(searcher.doc(address)[FIELD_FILE_ID][0]) for _, address in hits]


def _by_name(index: Index, term: str) -> list[int]:
    """The file ids a search over FIELD_NAME finds. The field a rename changes."""
    index.reload()
    searcher = index.searcher()
    hits = searcher.search(index.parse_query(term, [FIELD_NAME]), 10).hits
    return [int(searcher.doc(address)[FIELD_FILE_ID][0]) for _, address in hits]


async def test_a_job_is_indexed_committed_recorded_and_only_then_acknowledged(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path
) -> None:
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
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
    fetch = poller._fetch_file

    async def counting_fetch(*args: Any, **kwargs: Any) -> Any:
        reads.append(1)
        return await fetch(*args, **kwargs)

    poller._fetch_file = counting_fetch

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


def _scan_job() -> QueueJob:
    """One scanned PDF, the shape that hands over to the OCR track (D-07)."""
    return _job(mime="application/pdf", size=len(SCAN_BYTES), title="Ratsvorlage.pdf", path="Rat/Ratsvorlage.pdf")


async def test_no_text_layer_is_requeued_and_not_acknowledged(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The handover of D-07. Without it a scanned PDF is skipped for good, and the
    # verdict that phase 2 built as the bridge to OCR would be a dead end.
    #
    # The second assertion is the one that matters as much as the first: a row
    # that is handed over must not travel in the acknowledgement as well.
    # Acknowledging is deleting, so the row would be gone from the queue at the
    # same moment the requeue put work on it, and the file would never be read.
    queue = _FakeQueue(ClaimResult(jobs=(_scan_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SCAN_BYTES})

    result = await poller.run_once()

    assert queue.requeues == [([4711], "ocr")]
    assert queue.acknowledged == [([], {})]
    assert result.requeued == 1
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("skipped", "no_text_layer")


async def test_no_text_layer_stays_skipped_when_ocr_is_off(
    ocr_off: None, store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # An instance without OCR gets the honest verdict instead of rows waiting for
    # a track that does not exist. Nothing is requeued, and the row leaves the
    # queue the way it did before this plan.
    del ocr_off
    queue = _FakeQueue(ClaimResult(jobs=(_scan_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SCAN_BYTES})

    result = await poller.run_once()

    assert queue.requeues == []
    assert queue.acknowledged == [([91], {})]
    assert result.requeued == 0
    assert result.skipped == 1
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("skipped", "no_text_layer")


async def test_a_failed_handover_is_handed_over_again_when_the_row_comes_back(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The scenario of review finding CR-02. The requeue fails transiently, the
    # row stays claimed, runs into the lock timeout and is redelivered as a
    # content job. The stored skipped(no_text_layer) verdict with the same hash
    # used to block the second handover: the row went into done, was
    # acknowledged away, and the scan stayed skipped forever although OCR is
    # switched on. The second pass has to hand over again, because a successful
    # requeue would have turned the row into kind=ocr and it would never have
    # come back as content.
    queue = _FakeQueue(
        ClaimResult(jobs=(_scan_job(),)),
        ClaimResult(jobs=(_scan_job(),)),
    )
    queue.requeue_fails = True
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SCAN_BYTES})

    first = await poller.run_once()
    queue.requeue_fails = False
    second = await poller.run_once()

    assert first.requeued == 0
    assert second.requeued == 1
    assert queue.requeues == [([4711], "ocr"), ([4711], "ocr")]
    # And in neither pass does the row travel in the acknowledgement: a handover
    # that also acknowledged would delete the row the requeue put work on.
    assert queue.acknowledged == [([], {}), ([], {})]


async def test_a_stored_no_text_layer_verdict_does_not_block_the_handover(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The other window of CR-02: the container died between step 3 (the verdict
    # is durable) and step 3b (the requeue never ran). After the restart the row
    # comes back as a content job, the text pass finds the same missing text
    # layer over the same bytes, and the stored verdict must not turn that into
    # an end state.
    scan_hash = hashlib.sha256(SCAN_BYTES).hexdigest()
    store.record(
        4711,
        FileMeta(
            storage_id=3,
            root_id=2,
            path="Rat/Ratsvorlage.pdf",
            title="Ratsvorlage.pdf",
            mime="application/pdf",
            size=len(SCAN_BYTES),
            mtime=1_756_600_000,
            etag="5d41402abc4b2a76b9719d911017c592",
        ),
        "skipped",
        "no_text_layer",
        content_hash=scan_hash,
    )
    queue = _FakeQueue(ClaimResult(jobs=(_scan_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SCAN_BYTES})

    result = await poller.run_once()

    assert result.requeued == 1
    assert queue.requeues == [([4711], "ocr")]
    assert queue.acknowledged == [([], {})]


async def test_a_requeue_that_does_not_reach_nextcloud_does_not_end_the_pass(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The row stays claimed and runs into the lock timeout, which costs one more
    # text layer check and nothing else. The pass itself finishes, because the
    # index is already committed and the verdict already written.
    queue = _FakeQueue(ClaimResult(jobs=(_scan_job(),)))
    queue.requeue_fails = True
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SCAN_BYTES})

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert result.requeued == 0
    assert queue.acknowledged == [([], {})]


async def test_the_handover_happens_after_the_commit_and_before_the_acknowledgement(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Same reasoning as the order test above. An abort before the requeue costs
    # one repeated text layer check; an acknowledgement before it would delete
    # the row that the requeue was about to put work on.
    events: list[str] = []
    queue = _FakeQueue(ClaimResult(jobs=(_scan_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SCAN_BYTES})

    real_flush = writer.flush
    real_record = store.record
    real_requeue = queue.requeue
    real_acknowledge = queue.acknowledge

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


def _ocr_job(size: int) -> QueueJob:
    """The row that comes back from the requeue, now on the second track."""
    return _job(
        mime="application/pdf",
        size=size,
        kind="ocr",
        title="Ratsvorlage.pdf",
        path="Rat/Ratsvorlage.pdf",
    )


async def test_an_ocr_job_runs_the_ocr_route_with_the_long_deadline(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path
) -> None:
    # The three differences to the content branch, in one assertion each: the
    # bytes are fetched, the route is forced rather than derived from the
    # mimetype, and the deadline is the hard one of docs/ocr.md and not the 120 s
    # of a text job. A run that quietly took the text route would build exactly
    # the same index (T-03-902).
    queue = _FakeQueue(ClaimResult(jobs=(_ocr_job(len(SCAN_BYTES)),)))
    engine = _Extractor(outcome=ExtractionOutcome.indexed(BODY))
    fetched: list[int] = []
    poller = _poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=queue,
        bodies={4711: SCAN_BYTES},
        fetched=fetched,
        extract=engine,
    )

    result = await poller.run_once()

    assert fetched == [4711]
    assert len(engine.calls) == 1
    assert engine.calls[0]["route"] is Route.OCR
    assert engine.calls[0]["timeout"] == float(settings().ocr_hard_deadline_seconds)
    assert engine.calls[0]["timeout"] > float(settings().ocr_job_seconds)
    assert result.indexed == 1
    assert _documents(index) == 1
    # An OCR job is the end of the line: handing it over again is the loop that
    # T-03-704 closes from the other side.
    assert queue.requeues == []
    assert queue.acknowledged == [([91], {})]


@needs_engine
async def test_scanned_pdf_is_findable_after_ocr(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path
) -> None:
    # The second acceptance criterion of the whole phase, end to end through the
    # pass: a word that exists in exactly one corpus file and there only as
    # pixels is searchable afterwards, without an admin having configured OCR.
    queue = _FakeQueue(ClaimResult(jobs=(_ocr_job(len(COUNCIL_SCAN_BYTES)),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: COUNCIL_SCAN_BYTES})

    result = await poller.run_once()

    assert result.indexed == 1
    index.reload()
    searcher = index.searcher()
    hits = searcher.search(index.parse_query(COUNCIL_SCAN_TERM, [FIELD_BODY_DE]), 10).hits
    assert [int(searcher.doc(address)[FIELD_FILE_ID][0]) for _, address in hits] == [4711]
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["ocr_used"]) == ("indexed", 1)


async def test_ocr_used_is_recorded_even_when_the_scan_carried_no_text(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The flag says that the time was spent, not that it paid off. Without it
    # phase 4 cannot tell a document nobody looked at from one that went through
    # the engine and came back empty.
    queue = _FakeQueue(ClaimResult(jobs=(_ocr_job(len(SCAN_BYTES)),)))
    engine = _Extractor(outcome=ExtractionOutcome.skipped(Reason.EMPTY_TEXT))
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SCAN_BYTES}, extract=engine
    )

    result = await poller.run_once()

    assert result.skipped == 1
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("skipped", "empty_text")
    assert row["ocr_used"] == 1


async def test_a_text_job_leaves_ocr_used_alone(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # The other half of the flag: it is written by the OCR branch and by nothing
    # else, so a plain text file never claims that an engine ran over it.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()

    row = store.file_row(4711)
    assert row is not None
    assert row["ocr_used"] == 0


async def test_the_etag_of_the_job_reaches_the_state_row(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # Empty since phase 2 and written here for the first time. Without it the
    # reconcile of plan 03-12 has nothing to compare and would have to fetch every
    # file to find out that none of them changed.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()

    row = store.file_row(4711)
    assert row is not None
    assert row["etag"] == "5d41402abc4b2a76b9719d911017c592"


async def test_a_document_with_a_text_layer_never_reaches_the_ocr_route(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # D-06 through the poller. The decision falls in pdf.py with the measured
    # threshold, and this plan must not undo it by running OCR in addition: a
    # text PDF that is rasterised anyway costs up to 600 seconds of CPU for text
    # that was already there (T-03-906).
    queue = _FakeQueue(ClaimResult(jobs=(_job(mime="application/pdf", size=len(TEXT_LAYER_BYTES)),)))
    engine = _Extractor()
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: TEXT_LAYER_BYTES}, extract=engine
    )

    result = await poller.run_once()

    assert result.indexed == 1
    assert [call["route"] for call in engine.calls] == [None]
    assert queue.requeues == []


async def test_the_scratch_file_is_gone_after_a_failing_ocr_run(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The scratch file holds user content. Leaving one behind is a disclosure,
    # and leaving one behind per job fills the volume (T-03-905). The error path
    # is where that cleanup is forgotten, so the error path is what is asserted.
    queue = _FakeQueue(ClaimResult(jobs=(_ocr_job(len(SCAN_BYTES)),)))
    engine = _Extractor(error=RuntimeError("the engine went up in smoke"))
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SCAN_BYTES}, extract=engine
    )

    with pytest.raises(RuntimeError):
        await poller.run_once()

    assert list((tmp_path / "tmp").glob("*.part")) == []


async def test_an_ocr_job_keeps_the_order_commit_then_state_then_acknowledge(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The order of the module docstring is not a property of the content branch,
    # it is a property of the pass. A second branch that wrote its verdict before
    # the commit would lose documents in exactly the same silent way.
    events: list[str] = []
    queue = _FakeQueue(ClaimResult(jobs=(_ocr_job(len(SCAN_BYTES)),)))
    engine = _Extractor(outcome=ExtractionOutcome.indexed(BODY))
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SCAN_BYTES}, extract=engine
    )

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


# -- pictures ------------------------------------------------------------
#
# Three pictures out of the reference corpus, read rather than built for the
# reason the scan above is read: the verdicts of this branch come out of the
# real extractor, and a hand written stand-in would only prove that the stand-in
# says so. A slip that carries readable text, a three page TIFF of the shape a
# fax archive has, and an icon that is refused before the engine ever starts.
SLIP_BYTES = (CORPUS / "17-beleg.jpg").read_bytes()
FAX_BYTES = (CORPUS / "21-sendebericht.tif").read_bytes()
ICON_BYTES = (CORPUS / "22-icon.png").read_bytes()


def _picture_job(
    size: int,
    *,
    mime: str = "image/jpeg",
    kind: str = "content",
    title: str = "Beleg.jpg",
    path: str = "Belege/Beleg.jpg",
) -> QueueJob:
    """One picture, as the crawl queues it: an ordinary content row.

    ``kind`` is what the requeue turns the row into afterwards, so the same
    helper describes both halves of the journey a picture makes.
    """
    return _job(mime=mime, size=size, kind=kind, title=title, path=path)


@dataclass(slots=True)
class _PagesUnderTheDeadline:
    """An extractor that answers the way the engine would under the deadline it got.

    A three page fax costs more than the 120 s of a text job and less than the
    660 s of an OCR job. Asking the real engine that question in a unit test
    would mean spending the seconds, so this stand-in encodes the measured
    relation instead: under the short deadline the parent kills the child and the
    verdict is failed(timeout), under the long one the page loop hands over what
    it read and the verdict is indexed(truncated), which is the outcome D-08 asks
    for.
    """

    calls: list[dict[str, Any]] = field(default_factory=list)

    def __call__(
        self,
        path: str,
        mime: str,
        size: int,
        *,
        route: Route | None = None,
        timeout_seconds: float | None = None,
    ) -> ExtractionOutcome:
        del path, mime, size
        self.calls.append({"route": route, "timeout": timeout_seconds})
        short = float(settings().extract_timeout_seconds)
        if timeout_seconds is None or float(timeout_seconds) <= short:
            return ExtractionOutcome.failed(Reason.TIMEOUT)
        return ExtractionOutcome.indexed(BODY, truncated=True)


async def test_a_picture_is_handed_to_the_ocr_track_instead_of_the_text_route(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # A picture has no text layer to measure, so the text track has nothing to do
    # with it: the pass hands it straight to the second track instead of running
    # an extraction under the short deadline. The first assertion is the whole
    # point: not a single extraction happened on the text pass.
    queue = _FakeQueue(ClaimResult(jobs=(_picture_job(len(SLIP_BYTES)),)))
    engine = _Extractor()
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SLIP_BYTES}, extract=engine
    )

    result = await poller.run_once()

    assert engine.calls == []
    assert queue.requeues == [([4711], "ocr")]
    # Acknowledging is deleting, so a handed over row must not travel in the
    # acknowledgement of the same pass.
    assert queue.acknowledged == [([], {})]
    assert result.requeued == 1
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("skipped", "no_text_layer")


async def test_a_picture_carries_ocr_used_once_the_second_track_read_it(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The whole journey of a single page picture: handed over by the text pass,
    # read by the OCR pass, and indexed with the flag that says an engine ran.
    # Without the flag the OCR share of the measurement report has a hole exactly
    # where the picture heavy half of a typical instance is.
    queue = _FakeQueue(
        ClaimResult(jobs=(_picture_job(len(SLIP_BYTES)),)),
        ClaimResult(jobs=(_picture_job(len(SLIP_BYTES), kind="ocr"),)),
    )
    engine = _Extractor(outcome=ExtractionOutcome.indexed(BODY))
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SLIP_BYTES}, extract=engine
    )

    first = await poller.run_once()
    second = await poller.run_once()

    assert first.requeued == 1
    assert second.indexed == 1
    assert engine.calls[0]["route"] is Route.OCR
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["ocr_used"]) == ("indexed", 1)


async def test_a_many_paged_picture_runs_under_the_ocr_deadline_and_ends_truncated(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The position of the deferred list, in one test. Under the content deadline
    # of 120 s a fax archive ends as failed(timeout) although the page cap of the
    # module provides for indexed(truncated); under the OCR deadline it ends the
    # way it should. A run that quietly took the short deadline would produce the
    # same index for a single page picture and the wrong verdict for this one.
    queue = _FakeQueue(
        ClaimResult(jobs=(_picture_job(len(FAX_BYTES), mime="image/tiff"),)),
        ClaimResult(jobs=(_picture_job(len(FAX_BYTES), mime="image/tiff", kind="ocr"),)),
    )
    engine = _PagesUnderTheDeadline()
    poller = _poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=queue,
        bodies={4711: FAX_BYTES},
        extract=cast("Any", engine),
    )

    await poller.run_once()
    result = await poller.run_once()

    assert len(engine.calls) == 1
    assert engine.calls[0]["route"] is Route.OCR
    assert engine.calls[0]["timeout"] == float(settings().ocr_hard_deadline_seconds)
    assert engine.calls[0]["timeout"] > float(settings().extract_timeout_seconds)
    assert result.indexed == 1
    assert result.failed == 0
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("indexed", "truncated")


async def test_a_picture_without_readable_text_is_skipped_and_not_a_failure(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The icon of the corpus, through the real extractor and without an engine on
    # this machine: it is refused by the plausibility rules of the picture module
    # and keeps the verdict that exists for exactly this case. A folder full of
    # avatars must not fill the error list of the admin page.
    icon = _picture_job(len(ICON_BYTES), mime="image/png", title="Symbol.png", path="Bilder/Symbol.png")
    queue = _FakeQueue(ClaimResult(jobs=(icon,)), ClaimResult(jobs=(replace(icon, kind="ocr"),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: ICON_BYTES})

    await poller.run_once()
    result = await poller.run_once()

    assert result.skipped == 1
    assert result.failed == 0
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("skipped", "image_not_ocrable")


async def test_the_ocr_share_of_the_counters_contains_pictures(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The number the measurement report of this phase rests on. throughput()
    # splits what was indexed into text and OCR along ocr_used, so a picture that
    # never sets the flag is counted as a text document and makes the OCR share
    # of a picture heavy corpus look like zero.
    queue = _FakeQueue(
        ClaimResult(jobs=(_picture_job(len(SLIP_BYTES)),)),
        ClaimResult(jobs=(_picture_job(len(SLIP_BYTES), kind="ocr"),)),
        ClaimResult(jobs=(_job(92, 4712),)),
    )
    engine = _Extractor(outcome=ExtractionOutcome.indexed(BODY))
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SLIP_BYTES}, extract=engine
    )

    await poller.run_once()
    after_the_text_pass = store.throughput(3600, int(time.time()))
    await poller.run_once()
    await poller.run_once()
    counted = store.throughput(3600, int(time.time()))

    # The defect this test is about: the text pass must not put the picture into
    # the index as a text document, because from there no later run can tell how
    # much engine time it cost.
    assert (after_the_text_pass["text"], after_the_text_pass["ocr"]) == (0, 0)
    assert counted["ocr"] == 1
    assert counted["text"] == 1


async def test_a_picture_stays_skipped_when_ocr_is_off(
    ocr_off: None, store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # An instance whose admin switched OCR off gets the honest verdict, and the
    # engine is not started behind their back. Nothing is requeued, and the row
    # leaves the queue in the same pass.
    del ocr_off
    queue = _FakeQueue(ClaimResult(jobs=(_picture_job(len(SLIP_BYTES)),)))
    engine = _Extractor()
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SLIP_BYTES}, extract=engine
    )

    result = await poller.run_once()

    assert engine.calls == []
    assert queue.requeues == []
    assert queue.acknowledged == [([91], {})]
    assert result.requeued == 0
    assert result.skipped == 1
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("skipped", "no_text_layer")


async def test_a_text_document_keeps_the_text_route_and_the_short_deadline(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The other side of the same line. Only pictures move; a text document stays
    # a content job with the derived route and the deadline of a text job, and it
    # is never handed to the second track.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    engine = _Extractor()
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=engine)

    result = await poller.run_once()

    assert [(call["route"], call["timeout"]) for call in engine.calls] == [(None, None)]
    assert queue.requeues == []
    assert result.indexed == 1


async def test_an_unchanged_picture_is_not_handed_over_a_second_time(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # What the detour through the text pass buys, and the reason a picture is not
    # queued as an OCR row by Nextcloud in the first place: the fast path lives on
    # the content route. A second crawl over the same mount finds the same bytes,
    # acknowledges the row without work and hands nothing over, so occ
    # findling:index does not repeat days of engine time on every run.
    queue = _FakeQueue(
        ClaimResult(jobs=(_picture_job(len(SLIP_BYTES)),)),
        ClaimResult(jobs=(_picture_job(len(SLIP_BYTES), kind="ocr"),)),
        ClaimResult(jobs=(_picture_job(len(SLIP_BYTES)),)),
    )
    engine = _Extractor(outcome=ExtractionOutcome.indexed(BODY))
    poller = _poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SLIP_BYTES}, extract=engine
    )

    await poller.run_once()
    await poller.run_once()
    third = await poller.run_once()

    assert third.unchanged == 1
    assert third.requeued == 0
    assert queue.requeues == [([4711], "ocr")]
    assert queue.acknowledged[2] == ([91], {})


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

    assert result.state == ROUND_GATEWAY_UNAVAILABLE
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


async def test_the_fast_path_carries_the_new_etag_into_the_state_row(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # Review finding WR-02. A touch or a sync with identical bytes moves the
    # etag without moving a byte; the fast path used to acknowledge without
    # updating the stored mark, so the nightly reconcile read the file as stale
    # and re-downloaded it every cycle, forever. After the pass the stored etag
    # has to be the live one, and no attempt may have been counted, because
    # nothing was extracted.
    touched = replace(_job(), etag="ffffffffffffffffffffffffffffffff")
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(touched,)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    second = await poller.run_once()

    assert second.unchanged == 1
    row = store.file_row(4711)
    assert row is not None
    assert row["etag"] == "ffffffffffffffffffffffffffffffff"
    assert row["attempts"] == 1
    # The comparison of the reconcile is closed with this: known_etags answers
    # the live mark, so _stale_of stops proposing the file as work.
    assert store.known_etags([4711]) == {4711: "ffffffffffffffffffffffffffffffff"}


def _renamed(queue_id: int = 92) -> QueueJob:
    """The same file id under a new name, as a rename reaches the container."""
    return _job(queue_id, kind="metadata", title=RENAMED_TITLE, path=RENAMED_PATH)


async def test_rename_makes_the_file_findable_under_the_new_name(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path
) -> None:
    # Searching for the CONTENT after a rename is green and proves nothing,
    # because the content did not change. FIELD_NAME is the field that did, and
    # it is the one carrying boost 3.0 in the query, so this is the search a user
    # actually performs after renaming a file.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_renamed(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    result = await poller.run_once()

    assert result.indexed == 1
    assert _by_name(index, "aufhebungsvertrag") == [4711]
    assert _by_name(index, "kuendigung") == []
    assert queue.acknowledged[1] == ([92], {})


async def test_metadata_job_does_not_fetch_bytes(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # The whole point of the kind. The text is already in the index, so a rename
    # costs no gateway call, no scratch file and no extraction.
    fetched: list[int] = []
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_renamed(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, fetched=fetched)

    await poller.run_once()
    assert fetched == [4711]

    await poller.run_once()

    assert fetched == [4711]


async def test_a_rename_leaves_the_content_findable(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path
) -> None:
    # The other half of the promise: the cheap route must not lose the text it
    # did not fetch. Exactly one document, and it still answers on the body.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_renamed(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    await poller.run_once()

    assert _documents(index) == 1
    assert _stored_ids(index) == [4711]


async def test_a_rename_updates_the_state_row_and_keeps_the_verdict(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The verdict stays indexed and the content hash stays what it was: the bytes
    # did not change, and dropping the hash would send the next content job into
    # a full download and extraction of a file nobody touched.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_renamed(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    before = store.file_row(4711)
    assert before is not None
    await poller.run_once()

    row = store.file_row(4711)
    assert row is not None
    assert (row["path"], row["title"]) == (RENAMED_PATH, RENAMED_TITLE)
    assert (row["state"], row["reason"]) == ("indexed", None)
    assert row["content_hash"] == before["content_hash"]
    assert store.is_unchanged(4711, str(before["content_hash"])) is True


async def test_a_metadata_job_without_stored_text_runs_as_a_content_job(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path
) -> None:
    # A file that was never indexed, or one that ended as skipped, has no stored
    # text. That is not an error and not a requeue: the row is already here, so
    # it takes the content route it would have taken on a first indexing.
    fetched: list[int] = []
    queue = _FakeQueue(ClaimResult(jobs=(_renamed(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, fetched=fetched)

    result = await poller.run_once()

    assert result.indexed == 1
    assert fetched == [4711]
    assert _by_name(index, "aufhebungsvertrag") == [4711]
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("indexed", None)
    assert row["content_hash"]


async def test_a_metadata_job_keeps_the_order_commit_then_state_then_acknowledge(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The cheap branch sits inside step 1 of a pass and not next to it, so the
    # three steps after it stay in the only order in which every abort is
    # harmless.
    events: list[str] = []
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_renamed(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    await poller.run_once()

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


def _deletion(queue_id: int = 93, file_id: int = 4711) -> QueueJob:
    """A delete job as it leaves the queue: a file id, a storage, nothing else.

    No mimetype, no size, no user list and no fetch user, because the file is
    gone and no node can be asked for any of them. A container that needs one of
    these fields to run a deletion cannot run one at all (pitfall 3).
    """
    return QueueJob(
        queue_id=queue_id,
        file_id=file_id,
        storage_id=3,
        root_id=0,
        path="",
        title="",
        mime="",
        size=0,
        mtime=0,
        etag="",
        kind="delete",
        user_ids=(),
        fetch_as="",
        is_update=False,
    )


async def test_deleted_file_is_gone_for_another_user(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path
) -> None:
    # The proof is led from the outside on purpose. Searching as the user who
    # deleted the file proves nothing: the PHP recheck resolves the node through
    # getFirstNodeById and filters the hit away for that user whatever the index
    # holds. Only a second user who still has an entry in the prefilter can tell
    # "the recheck hid it" apart from "it is really out of the index", and the
    # second is what IDX-05 asks for.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_deletion(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    assert _documents(index) == 1
    assert store.prefilter_visible("bob", [4711]) == {4711}

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert _documents(index) == 0
    assert store.prefilter_visible("alice", [4711]) == set()
    assert store.prefilter_visible("bob", [4711]) == set()
    assert queue.acknowledged[1] == ([93], {})


async def test_a_delete_job_reads_no_bytes_and_extracts_nothing(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # No gateway call, no scratch file, no sandbox child. A deletion that
    # downloaded the file first would ask the gateway for bytes that are gone and
    # take the 404 for a verdict.
    fetched: list[int] = []
    extracted: list[str] = []
    queue = _FakeQueue(ClaimResult(jobs=(_deletion(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, fetched=fetched)
    poller._extract = lambda path, mime, size: extracted.append(path)  # type: ignore[assignment,func-returns-value]

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert fetched == []
    assert extracted == []
    assert sorted(entry.name for entry in (tmp_path / "tmp").iterdir()) == []
    # And no verdict either. Without a branch of its own the empty mimetype of a
    # delete job would fall to the allowlist and be written down as
    # skipped(mime_not_allowed), which is a lie about a file that is simply gone.
    assert store.file_row(4711) is None


async def test_a_delete_job_does_not_run_through_record(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # store.record counts attempts up and overwrites the verdict, and there is
    # nothing left to judge here. Three deletions of the same file would
    # otherwise walk straight into the give-up rule. The tombstone is the state.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_deletion(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    await poller.run_once()

    row = store.file_row(4711)
    assert row is not None
    assert row["attempts"] == 1
    assert (row["state"], row["reason"]) == ("indexed", None)
    assert row["deleted_at"] > 0


async def test_a_delete_job_is_durable_before_it_is_acknowledged(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The order of a pass survives the new branch. The prefilter is cleared
    # inside step 1, so the file stops being a candidate at once, and the
    # acknowledgement stays the last thing that happens: an abort before the
    # commit hands the row back and the whole deletion runs again, which is
    # harmless because every one of its three writes is idempotent.
    events: list[str] = []
    queue = _FakeQueue(ClaimResult(jobs=(_deletion(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    real_forget = store.forget_acl
    real_tombstone = store.tombstone
    real_flush = writer.flush
    real_acknowledge = queue.acknowledge

    def forget(*args: Any, **kwargs: Any) -> int:
        events.append("forget_acl")
        return real_forget(*args, **kwargs)

    def tombstone(*args: Any, **kwargs: Any) -> int:
        events.append("tombstone")
        return real_tombstone(*args, **kwargs)

    def flush() -> Any:
        events.append("commit")
        return real_flush()

    async def acknowledge(*args: Any, **kwargs: Any) -> CallResult:
        events.append("acknowledge")
        return await real_acknowledge(*args, **kwargs)

    monkeypatch.setattr(store, "forget_acl", forget)
    monkeypatch.setattr(store, "tombstone", tombstone)
    monkeypatch.setattr(writer, "flush", flush)
    monkeypatch.setattr(queue, "acknowledge", acknowledge)

    await poller.run_once()

    assert events == ["forget_acl", "tombstone", "commit", "acknowledge"]


async def test_a_delete_job_for_a_file_nobody_ever_indexed_is_acknowledged(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # A deletion carries no proof that the file was ever indexed, and it must not
    # need one. Dropping an absent document, forgetting rows that are not there
    # and marking a row that does not exist are all no-ops, and the row still has
    # to leave the queue rather than circle into the give-up rule.
    queue = _FakeQueue(ClaimResult(jobs=(_deletion(file_id=999),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert store.file_row(999) is None
    assert queue.acknowledged == [([93], {})]


def _permission_change(
    queue_id: int = 94,
    file_id: int = 4711,
    users: tuple[str, ...] = ("alice", "bob"),
) -> QueueJob:
    """An acl job as it leaves the queue: a file id, a storage, a user list.

    No mimetype, no size and no fetch user, because nothing is read. The user
    list is the whole payload, and after an unshare it may legitimately be empty:
    that is the target state and not a broken row (pitfall 4).
    """
    return QueueJob(
        queue_id=queue_id,
        file_id=file_id,
        storage_id=3,
        root_id=0,
        path="",
        title="",
        mime="",
        size=0,
        mtime=0,
        etag="",
        kind="acl",
        user_ids=users,
        fetch_as="",
        is_update=False,
    )


async def test_an_acl_job_writes_the_permissions_without_reading_bytes(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # A permission change costs a row and not a download, and that is the whole
    # reason it may overtake a content backlog (D-04). A gateway call here would
    # make the cheap kind as expensive as the one it is meant to jump over, and
    # on top of that ask for a file whose mimetype the job does not even carry.
    fetched: list[int] = []
    extracted: list[str] = []
    queue = _FakeQueue(ClaimResult(jobs=(_permission_change(users=("alice", "bob", "carol")),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, fetched=fetched)
    poller._extract = lambda path, mime, size: extracted.append(path)  # type: ignore[assignment,func-returns-value]

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert fetched == []
    assert extracted == []
    assert sorted(entry.name for entry in (tmp_path / "tmp").iterdir()) == []
    assert store.prefilter_visible("carol", [4711]) == {4711}
    assert queue.acknowledged == [([94], {})]


async def test_an_acl_job_does_not_run_through_record(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # store.record counts attempts up and overwrites the verdict, and a
    # permission change judges nothing. Three unshares of the same file would
    # otherwise walk into the give-up rule and end as failed(repeatedly_stuck)
    # although every one of them worked.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_permission_change(users=("alice",)),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    await poller.run_once()

    row = store.file_row(4711)
    assert row is not None
    assert row["attempts"] == 1
    assert (row["state"], row["reason"]) == ("indexed", None)
    assert row["deleted_at"] is None
    assert store.prefilter_visible("alice", [4711]) == {4711}
    assert store.prefilter_visible("bob", [4711]) == set()


async def test_an_acl_job_keeps_the_order_commit_then_state_then_acknowledge(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The new branch does not bend the order of a pass. The permissions are
    # written inside step 1 so the change takes effect at once, and the
    # acknowledgement stays the last thing that happens: an abort before it hands
    # the row back and replace_acl simply runs again with the same target state.
    events: list[str] = []
    queue = _FakeQueue(ClaimResult(jobs=(_permission_change(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    real_replace = store.replace_acl
    real_flush = writer.flush
    real_acknowledge = queue.acknowledge

    def replace_acl(*args: Any, **kwargs: Any) -> None:
        events.append("replace_acl")
        real_replace(*args, **kwargs)

    def flush() -> Any:
        events.append("commit")
        return real_flush()

    async def acknowledge(*args: Any, **kwargs: Any) -> CallResult:
        events.append("acknowledge")
        return await real_acknowledge(*args, **kwargs)

    monkeypatch.setattr(store, "replace_acl", replace_acl)
    monkeypatch.setattr(writer, "flush", flush)
    monkeypatch.setattr(queue, "acknowledge", acknowledge)

    await poller.run_once()

    assert events == ["replace_acl", "commit", "acknowledge"]


async def test_unchanged_file_still_updates_the_acl(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # Bug audit M1, due in this phase. The fast path acknowledges a file whose
    # bytes did not change without writing anything at all, and a permission
    # change that arrives as a content job carries the new user list in exactly
    # that row. Without this write it would never reach the prefilter, and bob
    # would keep being offered a file he lost access to until the next reindex.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_job(92, users=("alice",)),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    assert store.prefilter_visible("bob", [4711]) == {4711}

    second = await poller.run_once()

    assert second.unchanged == 1
    assert second.indexed == 0
    assert store.prefilter_visible("alice", [4711]) == {4711}
    assert store.prefilter_visible("bob", [4711]) == set()


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


async def test_a_file_that_cannot_be_processed_is_acknowledged_with_its_reason(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # A file the parser cannot open must leave the queue with a reason attached,
    # otherwise it circles until the give-up rule ends it three attempts later and
    # the status page names no cause. The reason travels to Nextcloud, where an
    # admin can still read it while the container is down.
    broken = b"PK not really a package at all"
    job = _job(mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", size=len(broken))
    queue = _FakeQueue(ClaimResult(jobs=(job,)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: broken})

    result = await poller.run_once()

    assert result.failed == 1
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("failed", "corrupt")
    assert queue.acknowledged == [([], {91: "corrupt"})]


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
        assert result.state == ROUND_EMPTY
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

    assert result.state == ROUND_PAUSED_LOW_DISK
    assert queue.acknowledged == []
    assert queue.unlocked == [[91]]
    assert store.file_row(4711) is None


async def test_an_unreachable_queue_is_a_state_and_not_a_crash(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    queue = _FakeQueue(ClaimResult(unavailable=True))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    result = await poller.run_once()

    assert result.state == ROUND_QUEUE_UNAVAILABLE
    assert poller.cooldown == 15


def _poller_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """What this module logged, without the lines of any other one."""
    return [record.getMessage() for record in caplog.records if record.name == "findling.worker.poller"]


async def test_a_queue_that_stops_answering_grows_the_pause_up_to_the_retreat_cap(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # D-17: the Nextcloud half can be removed while the container keeps running,
    # and then there is nobody left to call it. That is a state of operation, and
    # the pause of that state has its own ladder: it starts where the ordinary one
    # starts and climbs past the cap of an empty queue up to the named one.
    queue = _FakeQueue(*([ClaimResult(unavailable=True)] * 7))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    seen: list[float] = []

    for _ in range(7):
        result = await poller.run_once()
        assert result.state == ROUND_QUEUE_UNAVAILABLE
        seen.append(poller.cooldown)

    assert seen == [15, 30, 60, 120, 240, RETREAT_MAX_SECONDS, RETREAT_MAX_SECONDS]


async def test_one_unanswered_pass_is_not_a_retreat(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # A single failure is a restart of Nextcloud, a lost packet or a request that
    # took too long, and it has to keep behaving as it always did: one line, the
    # ordinary pause, no verdict about the installation.
    queue = _FakeQueue(ClaimResult(unavailable=True))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    with caplog.at_level("WARNING", logger="findling.worker.poller"):
        await poller.run_once()

    lines = _poller_lines(caplog)

    assert len(lines) == 1
    assert "passes" not in lines[0]
    assert poller.cooldown == 15


async def test_the_retreat_is_announced_once_and_then_the_container_keeps_quiet(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # The point of the whole mechanism. A container whose caller is gone must not
    # report it per attempt: a log that says the same thing every few seconds
    # fills the disk of a four gigabyte box and hides the lines that matter
    # (T-05-30). One line when the state is reached, and silence after it.
    rounds = 8
    queue = _FakeQueue(*([ClaimResult(unavailable=True)] * rounds))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    with caplog.at_level("WARNING", logger="findling.worker.poller"):
        for _ in range(rounds):
            await poller.run_once()

    lines = _poller_lines(caplog)
    announcements = [line for line in lines if "passes" in line]

    assert len(announcements) == 1
    # Two ordinary lines for the two failures before the state is reached, one
    # announcement, and nothing for the five attempts after it.
    assert len(lines) == RETREAT_AFTER_ROUNDS


async def test_an_answering_queue_ends_the_retreat_at_once(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # The way back has to be immediate, because it is the way an admin takes: the
    # companion is reinstalled, and the next pass has to work rather than sit out
    # a five minute pause. A second disappearance is announced again, because it
    # is a second event and not a repetition of the first.
    queue = _FakeQueue(
        *([ClaimResult(unavailable=True)] * RETREAT_AFTER_ROUNDS),
        ClaimResult(jobs=(_job(),)),
        *([ClaimResult(unavailable=True)] * RETREAT_AFTER_ROUNDS),
    )
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    with caplog.at_level("WARNING", logger="findling.worker.poller"):
        for _ in range(RETREAT_AFTER_ROUNDS):
            await poller.run_once()

        assert poller.cooldown == 60

        worked = await poller.run_once()

        assert worked.state == ROUND_WORKED
        assert poller.cooldown == 0

        again = await poller.run_once()

        assert again.state == ROUND_QUEUE_UNAVAILABLE
        assert poller.cooldown == 15

        for _ in range(RETREAT_AFTER_ROUNDS - 1):
            await poller.run_once()

    assert len([line for line in _poller_lines(caplog) if "passes" in line]) == 2


async def test_an_empty_answer_ends_the_retreat_as_well(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # An empty queue is an answer. It says "the companion is there and has
    # nothing for you", so the retreat is over and the ordinary ladder starts
    # again at its beginning rather than at the retreat cap.
    queue = _FakeQueue(*([ClaimResult(unavailable=True)] * 5), ClaimResult())
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    for _ in range(5):
        await poller.run_once()

    assert poller.cooldown == 240

    empty = await poller.run_once()

    assert empty.state == ROUND_EMPTY
    assert poller.cooldown == 15


async def test_a_retreat_neither_stops_the_indexing_nor_the_container(
    index: Index, store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The retreat is a pause and nothing else. It does not silence the poller, it
    # does not close the index and it does not end the task, so the batch that
    # arrives after a reinstallation is indexed like any other one and the search
    # of the container answers the whole time.
    queue = _FakeQueue(*([ClaimResult(unavailable=True)] * 4), ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    poller.arm()

    for _ in range(4):
        await poller.run_once()

    assert poller.armed is True

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert result.indexed == 1
    assert _documents(index) == 1
    assert poller.armed is True


def test_the_retreat_cap_is_a_named_constant_with_its_reason_next_to_it() -> None:
    """A bare number in a loop is a mystery in six months.

    The cap decides how long a container without a companion stays unnoticed and
    how long a reinstallation takes to be picked up, which is a trade-off and not
    a detail. So it is named, it sits above the cap of an empty queue, and the
    line above it is the reason it has that value.
    """
    source = POLLER_SOURCE.read_text(encoding="utf-8").splitlines()
    where = next(number for number, line in enumerate(source) if line.startswith("RETREAT_MAX_SECONDS"))

    assert RETREAT_MAX_SECONDS == 300
    assert settings().poll_cooldown_max_seconds < RETREAT_MAX_SECONDS
    assert source[where - 1].lstrip().startswith("#")
    assert "backoff" in "\n".join(source).lower()


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


async def test_the_scratch_file_is_gone_after_every_job(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
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

    commit = source.index("self._writer_or_die().flush")
    record = source.index("self._record_verdicts")
    acknowledge = source.index("queue.acknowledge(")

    assert commit < record < acknowledge


def test_the_blocking_work_runs_off_the_event_loop() -> None:
    """The tantivy calls and the SQLite transaction belong in a worker thread.

    The warning sign of the mistake is in the phase research: /heartbeat hangs
    while /enabled still answers, because a long commit sits on the event loop.
    """
    source = POLLER_SOURCE.read_text(encoding="utf-8")

    assert source.count("to_thread") >= 2
    for blocking in ("_writer_or_die().flush", "_writer_or_die().add", "_record_verdicts", "self._extract"):
        lines = [line for line in source.splitlines() if blocking in line and "to_thread" in line]

        assert lines, blocking


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
    """One creation in the file, so a second one is a visible change.

    Counted as code lines, with comments taken out first: the reason for this
    gate is written down next to it and names the factory, and a rule that
    punishes its own explanation gets deleted rather than obeyed.
    """
    code = [
        line for line in POLLER_SOURCE.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#")
    ]

    assert sum("create_app_client" in line for line in code) == 1


def test_the_shutdown_path_releases_what_the_container_holds() -> None:
    """The lifespan has to hand the rows back, otherwise a restart waits."""
    assert "unlock" in MAIN_SOURCE.read_text(encoding="utf-8")


def test_an_empty_index_next_to_indexed_verdicts_raises_the_generation(index: Index, store: Store) -> None:
    """A lost tantivy directory must not leave the search empty for good.

    With the state database still saying "indexed", the fast path would skip
    every requeued file and the counters would claim success over an empty
    index forever (bug audit H5). Raising the generation makes every stored
    verdict stale, so the next crawl actually rebuilds.
    """
    meta = FileMeta(storage_id=1, root_id=2, path="files/a.txt", title="a.txt", mime="text/plain", size=3, mtime=4)
    store.record(1, meta, "indexed", None, content_hash="abc")
    assert store.is_unchanged(1, "abc") is True

    _raise_generation_for_lost_index(index, store)

    assert store.is_unchanged(1, "abc") is False


def test_a_fresh_volume_does_not_raise_the_generation(index: Index, store: Store) -> None:
    before = store.index_version

    _raise_generation_for_lost_index(index, store)

    assert store.index_version == before


def test_a_state_database_created_by_the_poller_carries_the_version_marks(volume: Path) -> None:
    """Freshly created state must agree with the index this code builds.

    Without the seed the marks stay unknown/0 forever: every answer says
    degraded, /status reports reindexRequired, and the drift alarm becomes
    permanent noise (bug audit H1). The seed fills only missing keys, so an
    existing database keeps the marks of the index it actually belongs to.
    """
    digest = write_wordlist(volume)

    opened = _open_state()
    try:
        assert opened.version_mismatch(expected_versions(digest)) == []
    finally:
        opened.close()


async def test_the_resources_open_off_the_event_loop(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    """Perf audit M1: opening must not stall the loop that answers /heartbeat.

    ``_open`` connects SQLite and applies the schema, builds the word list
    artifact over 276k entries including its checksum, opens the tantivy index
    and sweeps the scratch directory. Measured on ARM that adds up to an
    estimated 1.5 to 3 seconds, and every one of those seconds is a heartbeat
    the platform does not get an answer to while ``/enabled`` still replies.
    AppAPI reads a missing heartbeat as a dead container and restarts it, so
    this is not a latency question but a boot loop.

    What is asserted is the property, not the seconds: the factories of ``_open``
    run on a worker thread. The measurement is a measurement and belongs in the
    audit, the thread is a decision and belongs in a test.
    """
    loop_thread = threading.current_thread()
    threads: list[threading.Thread] = []

    def client_factory() -> AsyncNextcloudApp:
        threads.append(threading.current_thread())
        return cast("AsyncNextcloudApp", object())

    poller = Poller(
        store=store,
        writer=writer,
        tmp_dir=tmp_path / "tmp",
        client_factory=client_factory,
        gateway_factory=lambda: cast("Any", _FakeGatewayClient()),
        queue_factory=lambda nc: cast("Any", _FakeQueue()),
    )

    result = await poller.run_once()

    assert result.state == ROUND_EMPTY
    assert threads != []
    assert threads[0] is not loop_thread


async def test_the_resources_are_opened_only_once(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # The thread must not cost the invariant it was wrapped around: one client
    # for the whole run. A second creation is a connection setup and a Nextcloud
    # bootstrap per pass, which is the difference between an initial index and a
    # weekend.
    clients: list[object] = []
    queue = _FakeQueue()
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, clients=clients)

    await poller.run_once()
    await poller.run_once()

    assert len(clients) == 1
    assert queue.claims == 2


def test_the_verdict_list_does_not_hold_the_document_text() -> None:
    """Perf audit M2: the text is gone once the writer has it.

    ``verdicts`` lives until after the commit, and at a batch of 32 documents at
    the character cap that is 16.8 to 33.6 MB of strings held for the whole pass
    on a box with four gigabytes. ``_record_verdicts`` never reads the text; it
    writes the state, the reason, the character count and the hash. So the text
    is dropped on the way into the list, and everything the later steps do read
    survives untouched.
    """
    verdicts: list[Any] = []
    outcome = ExtractionOutcome.indexed(BODY * 100)

    Poller._collect(_job(), outcome, [], {}, verdicts, "abc")

    assert verdicts[0].outcome.text == ""
    # The count is stored at extraction time and never recomputed, which is what
    # makes dropping the text harmless for the status page.
    assert verdicts[0].outcome.text_chars == outcome.text_chars
    assert verdicts[0].outcome.state is outcome.state
    assert verdicts[0].outcome.reason is outcome.reason
    # The caller keeps its own outcome: the writer is handed the text before this
    # call, and a mutation would be a document without a body in the index.
    assert outcome.text != ""


def test_a_truncated_verdict_keeps_its_reason_without_its_text() -> None:
    # truncated is a reason, not a property of the string, so it has to survive
    # the drop. If it did not, a renamed file would later be re-recorded as
    # indexed without the mark, and the status page would stop reporting that
    # the document is only partly in the index.
    verdicts: list[Any] = []
    outcome = ExtractionOutcome.indexed(BODY, truncated=True)

    Poller._collect(_job(), outcome, [], {}, verdicts, "abc")

    assert verdicts[0].outcome.text == ""
    assert verdicts[0].outcome.truncated is True
