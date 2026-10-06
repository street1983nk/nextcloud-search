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

import ast
import asyncio
import hashlib
import re
import shutil
import sqlite3
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import IO, Any, cast

import pytest
from fastapi.testclient import TestClient
from tantivy import Index

from conftest import write_wordlist, write_wordlist_nl
from findling import guard, lane
from findling.config import OCR_SLOT_COST_BYTES, SCHEMA_VERSION, settings
from findling.extract.dispatch import Route
from findling.extract.dispatch import extract as dispatch_extract
from findling.extract.errors import ChildKilled, ExtractionOutcome, Reason
from findling.extract.pool import SlotPool
from findling.hardware import Hardware
from findling.index.open import DUTCH_MARK, LANGUAGES_MARK, REBUILD_MARK, SCHEMA_MARK, expected_versions, open_index
from findling.index.schema import FIELD_BODY_DE, FIELD_FILE_ID, FIELD_NAME
from findling.index.wordlist_nl import dutch_mark
from findling.index.writer import IndexBatchWriter
from findling.main import APP, active_poller, enabled_handler
from findling.nc.client import AsyncNextcloudApp, NextcloudException
from findling.nc.queue import (
    LANE_INDEX,
    TOPUP_IDLE,
    TOPUP_SUPPLIED,
    TOPUP_UNAVAILABLE,
    CallResult,
    ClaimResult,
    CompanionChoice,
    DocumentQueue,
    QueueJob,
    QueueStats,
)
from findling.profile import Profile, note_hardware, snapshot
from findling.store.repo import FileMeta, Store, open_store
from findling.worker import poller as poller_module
from findling.worker.poller import (
    RETREAT_AFTER_ROUNDS,
    RETREAT_MAX_SECONDS,
    ROUND_EMPTY,
    ROUND_GATEWAY_UNAVAILABLE,
    ROUND_PAUSED_LOW_DISK,
    ROUND_PAUSED_STORE_ERROR,
    ROUND_QUEUE_UNAVAILABLE,
    ROUND_WAITING_FOR_RUNNER,
    ROUND_WORKED,
    STAND_DOWN_TICK_SECONDS,
    Poller,
    _open_state,
    _open_writer,
    _raise_generation_for_lost_index,
)

POLLER_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "worker" / "poller.py"
MAIN_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "main.py"

# The two PHP files that own the work stock. They are read as text and never
# imported, the same way tests/test_reconcile.py reads the list ceiling: a PHP
# constant has no import into this process, and the rules below are one
# agreement between the two halves with nothing but a docblock holding it.
PHP_LIB = Path(__file__).resolve().parents[2] / "php" / "lib"
PHP_QUEUE_MAPPER = PHP_LIB / "Db" / "QueueMapper.php"
PHP_QUEUE_SERVICE = PHP_LIB / "Service" / "QueueService.php"

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


class _SessionWithoutProfileRoute:
    """The session of a 1.3.x companion: the profile route is not there."""

    async def ocs(self, method: str, path: str, **kwargs: Any) -> Any:
        del method, kwargs
        raise NextcloudException(404, reason=f"no route {path}")


class _AppWithoutProfileRoute:
    """Carries the session above and nothing else, which is all the read needs."""

    def __init__(self) -> None:
        self._session = _SessionWithoutProfileRoute()


class _FakeQueue:
    """The four queue calls, answered from a script and recorded."""

    def __init__(self, *batches: ClaimResult) -> None:
        self._batches = list(batches)
        self.claims = 0
        self.acknowledged: list[tuple[list[int], dict[int, str]]] = []
        # The third list of the acknowledgement, recorded next to the other two
        # rather than inside their tuple: three dozen assertions in this file
        # spell the pair out, and widening the tuple would rewrite all of them
        # for a list most of those tests do not care about.
        self.skips: list[dict[int, str]] = []
        self.unlocked: list[list[int]] = []
        self.requeues: list[tuple[list[int], str]] = []
        self.requeue_fails = False
        # What the top-up of an empty pass answers, and how often it was asked.
        # Idle by default, because that is the state every existing test means:
        # a queue whose script ran out has nothing left to crawl.
        self.topups = 0
        self.topup_answer = TOPUP_IDLE
        # What the profile read of a round answers. None by default, which is
        # a companion without a stored choice: Economy stays in force, the
        # state every existing test means (D-24-02).
        self.profile_answer: str | None = None
        # The precision out of the same answer (D-25-02). None by default, a
        # 1.3 companion without the field.
        self.precision_answer: str | None = None
        # The guard's confirmation token out of the same answer (D-26-04).
        # None by default, a companion before plan 26-02.
        self.confirmed_answer: str | None = None
        # A companion older than 1.4.0: the read goes through the real
        # DocumentQueue.companion_choice over a session that answers 404, so the
        # test proves the error path the poller really meets and not a fake
        # raising where production code never raises.
        self.profile_route_missing = False
        self.profile_asks = 0
        # The order of the calls that matter for D-24-01: profile before claim.
        self.order: list[str] = []
        # The lane of every claim, None for a claim that asked for none (T13).
        self.lanes: list[str | None] = []

    async def companion_choice(self) -> CompanionChoice:
        self.profile_asks += 1
        self.order.append("profile")
        if self.profile_route_missing:
            return await DocumentQueue(cast("AsyncNextcloudApp", _AppWithoutProfileRoute())).companion_choice()
        return CompanionChoice(
            profile=self.profile_answer, precision=self.precision_answer, confirmed=self.confirmed_answer
        )

    async def claim(self, *, limit: int, max_bytes: int, lane: str | None = None) -> ClaimResult:
        del limit, max_bytes
        self.lanes.append(lane)
        self.claims += 1
        self.order.append("claim")
        return self._batches.pop(0) if self._batches else ClaimResult()

    async def top_up(self) -> str:
        self.topups += 1
        return self.topup_answer

    async def acknowledge(self, done: Any, failed: Any, skipped: Any = None) -> CallResult:
        self.acknowledged.append((list(done), dict(failed)))
        self.skips.append(dict(skipped or {}))
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
    marks_stamped: Callable[[], None] | None = None,
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
        marks_stamped=marks_stamped,
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
    # And every one of those empty passes asked whether the crawl was done,
    # because "empty" alone cannot tell starving from finished (DI-10-04).
    assert queue.topups == 6


async def test_a_starved_container_asks_for_a_slice_and_keeps_the_short_pause(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The runtime finding of the v1.1 comparison run, DI-10-04.

    The container sat starved for 5.85 of 26.6 hours because the crawl advanced
    only with the system cron, and on top of every supply gap the empty-queue
    ladder grew the pause to 120 s. When the top-up says a slice was run, the
    pause has to stay at the start value: the rows it asked for are arriving
    right now, and a rung of the ladder would be the old defect kept.
    """
    queue = _FakeQueue()
    queue.topup_answer = TOPUP_SUPPLIED
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    poller.arm()

    with caplog.at_level("INFO", logger="findling.worker.poller"):
        for _ in range(4):
            result = await poller.run_once()
            assert result.state == ROUND_EMPTY
            assert poller.cooldown == 15

    assert queue.topups == 4
    # One line per starvation streak, not one per pass (the T-05-30 rule), and
    # no idle line at all: a waiting container is not an idle one.
    starved = [line for line in _poller_lines(caplog) if "asked for the next slice" in line]
    assert len(starved) == 1
    assert not [line for line in _poller_lines(caplog) if "armed and the work stock is empty" in line]


async def test_a_top_up_without_an_answer_walks_the_ordinary_ladder(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # An old companion without the route answers 404 down there, and that must
    # cost exactly what an idle answer costs: the backoff ladder, never a crash
    # and never a short pause on a promise nobody made.
    queue = _FakeQueue()
    queue.topup_answer = TOPUP_UNAVAILABLE
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    seen: list[float] = []

    for _ in range(4):
        result = await poller.run_once()
        assert result.state == ROUND_EMPTY
        seen.append(poller.cooldown)

    assert seen == [15, 30, 60, 120]


async def test_the_profile_is_read_once_per_round_before_the_claim(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # D-24-01: one read per round, and before the claim, because from phase 26
    # on the size of the claim depends on the profile.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    queue.profile_answer = "standard"
    queue.precision_answer = "fp32"
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: BODY_BYTES})

    await poller.run_once()
    await poller.run_once()

    assert queue.profile_asks == 2
    assert queue.order == ["profile", "claim", "profile", "claim"]
    assert snapshot().chosen is Profile.STANDARD


async def test_the_poller_claims_without_a_lane(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # T13 and K6: the economy poller speaks the 1.3 wire, a claim without a lane,
    # also when the companion answers a profile and a precision.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    queue.profile_answer = "standard"
    queue.precision_answer = "fp32"
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: BODY_BYTES})

    await poller.run_once()
    await poller.run_once()

    assert queue.lanes == [None, None]


def _standard_box() -> None:
    """Four cores and 16 GiB, the smallest box Standard is suggested on (Pitfall 11)."""
    note_hardware(
        Hardware(
            cpu_count=4,
            cpu_quota=None,
            cores=4,
            memory_limit_bytes=None,
            memory_available_bytes=16 * 1024**3,
            memory_total_bytes=16 * 1024**3,
            architecture="x86_64",
            cgroup="none",
        )
    )


@dataclass(slots=True)
class _StubRunner:
    """Only the part of the embed runner the poller reads: the parked event."""

    parked: asyncio.Event = field(default_factory=asyncio.Event)


async def test_a_parallel_runner_moves_the_claim_onto_the_index_lane(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # PAR-01: with the runner in parallel mode the loop asks for the index lane;
    # in Economy it asks for no lane, whatever the lane state says.
    _standard_box()
    queue = _FakeQueue()
    queue.profile_answer = "standard"
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    lane.note_mode(lane.MODE_PARALLEL, lane.REASON_NONE)

    await poller.run_once()
    queue.profile_answer = "economy"
    await poller.run_once()

    assert queue.lanes == [LANE_INDEX, None]


async def test_the_echo_of_every_claim_reaches_the_lane_state(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    queue = _FakeQueue(ClaimResult(lane_honored=True), ClaimResult())
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    assert lane.snapshot().supported is True
    await poller.run_once()
    assert lane.snapshot().supported is False


async def test_economy_waits_for_the_runner_to_park_before_it_claims(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # T4, the loop side: no claim, and therefore no OCR, while the runner is in
    # the middle of a round.
    queue = _FakeQueue()
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    runner = _StubRunner()
    poller.attach_runner(cast("Any", runner))

    task = asyncio.ensure_future(poller.run_once())
    await asyncio.sleep(0.05)
    assert queue.claims == 0
    runner.parked.set()
    result = await asyncio.wait_for(task, timeout=5)

    assert result.state == ROUND_EMPTY
    assert queue.lanes == [None]


async def test_a_runner_that_does_not_park_costs_the_pass_its_claim(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(poller_module, "RUNNER_PARK_WAIT_SECONDS", 0.05)
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    poller.attach_runner(cast("Any", _StubRunner()))

    result = await poller.run_once()

    assert result.state == ROUND_WAITING_FOR_RUNNER
    assert queue.claims == 0
    assert poller.cooldown > 0


async def test_without_a_runner_the_poller_never_waits(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    queue = _FakeQueue()
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    poller.attach_runner(None)

    assert (await poller.run_once()).state == ROUND_EMPTY
    assert poller.track is poller._track


async def test_a_store_error_in_the_indexing_lane_hands_the_rows_back_without_a_verdict(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Pitfall 3: "database is locked" used to end in the catch-all of run(), the
    # rows ran into the lock timeout and spent a delivery each. Now it is the
    # _abort of the disk pause: unlock, backoff, no acknowledgement at all.
    queue = _FakeQueue(ClaimResult(jobs=(_job(91, 4711), _job(92, 4712))))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    def locked(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(store, "record", locked)

    result = await poller.run_once()

    assert result.state == ROUND_PAUSED_STORE_ERROR
    assert queue.unlocked == [[91, 92]]
    assert queue.acknowledged == []
    assert not poller.busy
    assert poller.cooldown > 0


@pytest.mark.parametrize("requeue_fails", [False, True])
async def test_a_row_handed_to_another_track_leaves_the_held_rows(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, requeue_fails: bool
) -> None:
    # Pattern 5.3: after a successful requeue the row belongs to the next track,
    # so an unlock_held between the requeue and the acknowledgement must not
    # hand it back. A failed requeue leaves the row held, as before.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    queue.requeue_fails = requeue_fails
    poller = _poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=queue,
        extract=_Extractor(outcome=ExtractionOutcome.skipped(Reason.NO_TEXT_LAYER)),
    )
    acknowledge = queue.acknowledge

    async def unlock_first(done: Any, failed: Any, skipped: Any = None) -> CallResult:
        await poller.unlock_held()
        return await acknowledge(done, failed, skipped)

    monkeypatch.setattr(queue, "acknowledge", unlock_first)

    await poller.run_once()

    assert queue.requeues == [([4711], "ocr")]
    assert queue.unlocked == ([[91]] if requeue_fails else [])


async def test_a_companion_without_the_profile_route_leaves_economy_in_force(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # K6: a new container next to a 1.3.x companion. The 404 goes through the
    # real DocumentQueue.profile, the round ends as an ordinary empty round and
    # Economy stays in force because nothing was ever readable (D-24-02).
    queue = _FakeQueue()
    queue.profile_route_missing = True
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    with caplog.at_level("DEBUG"):
        result = await poller.run_once()

    assert result.state == ROUND_EMPTY
    assert queue.order == ["profile", "claim"]
    assert snapshot().chosen is None
    assert snapshot().effective is Profile.ECONOMY
    assert "unexpected" not in caplog.text
    assert "could not read the profile" in caplog.text


async def test_a_failed_read_keeps_the_last_profile(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # T-24-18: a gateway hiccup must not flap the profile back to Economy. The
    # last name read stays for the life of the process, through a round that
    # reads nothing and through a round whose read fails outright.
    queue = _FakeQueue()
    queue.profile_answer = "standard"
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    assert snapshot().chosen is Profile.STANDARD

    queue.profile_answer = None
    await poller.run_once()
    assert snapshot().chosen is Profile.STANDARD

    queue.profile_route_missing = True
    await poller.run_once()
    assert snapshot().chosen is Profile.STANDARD
    assert queue.profile_asks == 3


async def test_an_armed_container_with_an_empty_work_stock_says_so_once_per_arming(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """DI-05-36, the observability half: armed and idle must not look silenced.

    Reproduced from run 34056709826. The resilience gate decides whether a
    restarted container arms itself by counting "pass finished" lines, and that
    line is written only for a pass that claimed rows. The whole corpus had
    reached a terminal verdict before the restart, so the correctly armed
    container had nothing to claim, wrote nothing at all, and the gate reported
    the very defect it was written to catch.

    One line per arming and not one per pass: an instance with an empty work
    stock polls for ever, and a line per poll would fill the log of a four
    gigabyte box exactly the way the retreat announcement must not (T-05-30).
    """
    queue = _FakeQueue()
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    poller.arm()

    with caplog.at_level("INFO", logger="findling.worker.poller"):
        for _ in range(4):
            assert (await poller.run_once()).state == ROUND_EMPTY

    idle = [line for line in _poller_lines(caplog) if "armed and the work stock is empty" in line]

    assert len(idle) == 1
    # And nothing that a reader could mistake for work that was done.
    assert not [line for line in _poller_lines(caplog) if line.startswith("pass finished")]

    # A container that is switched off and on again owes the answer a second
    # time, because the line of the previous arming says nothing about this one.
    poller.silence()
    poller.arm()

    with caplog.at_level("INFO", logger="findling.worker.poller"):
        await poller.run_once()

    assert len([line for line in _poller_lines(caplog) if "armed and the work stock is empty" in line]) == 2


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


# -- the disk pause and the delivery budget (DI-05-23) ------------------------
#
# The heaviest finding of the full run of plan 05-14, and it needed ten hours on
# a four gigabyte box to show itself. The pause works, the index stays intact,
# the search keeps answering, and the work stock is written off while the banner
# says the opposite. The mechanism is spread over both halves, which is why the
# reproduction below is a simulation of the Nextcloud side driven by the real
# poller rather than a test of either half on its own:
#
#   1. QueueMapper counts the retry when it HANDS A ROW OUT, in the claim.
#   2. The container pauses below the free space floor and gives the whole load
#      back unjudged, which is the _abort with ROUND_PAUSED_LOW_DISK below.
#   3. A pass takes seconds, so QueueService::MAX_DELIVERIES = 3 is spent after
#      roughly twenty seconds of a tight disk.
#   4. The fourth claim writes the row off as failed(repeatedly_stuck) and never
#      hands it to the container at all.
#
# Measured twice on the box, with the same ratio both times: 2 of 2 rows in the
# first pass of drill 3 and 30 of 30 in the second, 28 of those 30 written off
# without ever having been delivered (docs/performance.md, "Drill 3, Nachtrag").

# The rows that were with the worker when the disk went tight in the second pass
# of the drill. The number is taken from the measurement and not rounded: it is
# what makes the reproduction the one that happened rather than one like it.
ROWS_IN_FLIGHT = 30

# How many passes the pause lasts here. The drill paused for 98 seconds at a few
# seconds per pass; ten is comfortably past the budget of three deliveries and
# short enough to stay a unit test.
PASSES_OF_THE_PAUSE = 10


def _php_source(path: Path) -> str:
    """One PHP file as text, and a missing one is red rather than green.

    The anti-vacuity clause every text gate of this project carries
    (docs/testing.md): a gate that silently passes because its source moved
    proves nothing at all.
    """
    assert path.is_file(), f"the gate looks for {path.name} and it is not there any more"
    return path.read_text(encoding="utf-8")


def _max_deliveries() -> int:
    """QueueService::MAX_DELIVERIES, read out of the PHP source."""
    limit = re.search(r"const MAX_DELIVERIES = (\d+);", _php_source(PHP_QUEUE_SERVICE))

    assert limit is not None, "the delivery ceiling is no longer where this gate looks for it"
    return int(limit.group(1))


def _unlock_body(source: str) -> str:
    """The body of QueueMapper::unlock, cut out of the source.

    Ends at the first closing brace on one tab of indentation, which is the end
    of the method and not the end of a block inside it. Cutting at the next
    ``public function`` instead would take the docblock of the following method
    along, and a sentence of that docblock would then answer for this one.
    """
    start = source.index("public function unlock(")
    end = source.index("\n\t}\n", start)

    return source[start:end]


def _hands_the_delivery_back(unlock_body: str) -> bool:
    """Whether handing a row back through unlock gives its delivery back.

    The one question this simulation cannot answer for itself. The counter lives
    in a database column on the other side of the boundary, so the rule is read
    where it is written: a decrement of ``retries`` inside the body of
    ``unlock``. Written as a helper with a self test below rather than inline,
    because a gate that reads a foreign source has to be able to say what it
    would look like if the rule were gone.
    """
    return re.search(r"'retries',\s*\$\w+->createFunction\('retries - 1'\)", unlock_body) is not None


@dataclass(slots=True)
class _StockRow:
    """One row of the work stock, with the counter the give-up rule reads."""

    job: QueueJob
    retries: int = 0
    claimed: bool = False


class _WorkStock:
    """The Nextcloud work stock, modelled after the two PHP files that own it.

    Not a script of answers like :class:`_FakeQueue` above but a small state
    machine, because the defect this class exists for is a sequence: the same
    rows are handed out again and again, and what matters is what the counter
    does between the hand-outs.

    Three rules and every one of them is read out of the PHP source rather than
    chosen here, so that a change over there turns this red instead of leaving a
    simulation that models a system nobody runs any more:

    * the retry is counted when the row is HANDED OUT (``claimBatch``),
    * a row above ``MAX_DELIVERIES`` is written off as failed(repeatedly_stuck)
      and never delivered (``QueueService::claim``),
    * a row handed back through ``unlock`` does or does not get its delivery
      back, which is exactly the fix this file is the gate for.
    """

    def __init__(self, jobs: tuple[QueueJob, ...], *, max_deliveries: int, refunds: bool) -> None:
        self._rows = {job.queue_id: _StockRow(job=job) for job in jobs}
        self._max_deliveries = max_deliveries
        self._refunds = refunds
        self.written_off: list[int] = []
        self.claims = 0

    async def companion_choice(self) -> CompanionChoice:
        # The stock simulation is about deliveries, never about the profile:
        # no stored choice, Economy and int8 in force, no guard confirmation.
        return CompanionChoice(profile=None, precision=None, confirmed=None)

    async def top_up(self) -> str:
        # The stock is the whole crawl in these tests: nothing is ever pending
        # behind it.
        return TOPUP_IDLE

    async def claim(self, *, limit: int, max_bytes: int, lane: str | None = None) -> ClaimResult:
        del max_bytes, lane
        self.claims += 1
        handed: list[QueueJob] = []
        for row in list(self._rows.values()):
            if row.claimed or len(handed) >= limit:
                continue
            row.retries += 1
            if row.retries > self._max_deliveries:
                # The give-up, and the row is gone from the stock with it: the
                # PHP side records failed(repeatedly_stuck) and acknowledges the
                # row away without the container ever seeing it.
                self.written_off.append(row.job.file_id)
                del self._rows[row.job.queue_id]
                continue
            row.claimed = True
            handed.append(row.job)
        return ClaimResult(jobs=tuple(handed))

    async def acknowledge(self, done: Any, failed: Any, skipped: Any = None) -> CallResult:
        del skipped
        gone = list(done) + list(dict(failed))
        for queue_id in gone:
            self._rows.pop(queue_id, None)
        return CallResult(ok=True, count=len(gone))

    async def unlock(self, ids: Any) -> CallResult:
        released = 0
        for queue_id in ids:
            row = self._rows.get(queue_id)
            if row is None:
                continue
            row.claimed = False
            if self._refunds:
                row.retries = max(0, row.retries - 1)
            released += 1
        return CallResult(ok=True, count=released)

    async def requeue(self, file_ids: Any, *, kind: str) -> CallResult:
        del kind
        return CallResult(ok=True, count=len(list(file_ids)))

    async def stats(self) -> QueueStats:
        return QueueStats(scheduled=len(self._rows))

    def waiting(self) -> list[int]:
        """The file ids still in the stock, in queue order."""
        return [row.job.file_id for row in self._rows.values()]

    def deliveries_spent(self) -> list[int]:
        """The retry counter of every row still in the stock."""
        return [row.retries for row in self._rows.values()]


def _work_stock(jobs: tuple[QueueJob, ...]) -> _WorkStock:
    unlock = _unlock_body(_php_source(PHP_QUEUE_MAPPER))

    return _WorkStock(jobs, max_deliveries=_max_deliveries(), refunds=_hands_the_delivery_back(unlock))


async def test_a_disk_pause_does_not_spend_the_delivery_budget_of_the_rows_it_hands_back(
    index: Index, index_dir: Path, store: Store, tmp_path: Path
) -> None:
    """DI-05-23, reproduced: thirty rows, a tight disk, and nothing written off.

    The banner says "Little disk space left. Indexing is paused so the index
    stays intact." That was true of the index and false of the work stock, and
    the difference cost thirty of sixty uploaded files in the drill. A pause has
    to be free: the rows that were with the worker when it started are the same
    rows that are waiting when it ends, with the same budget in front of them.
    """
    jobs = tuple(_job(90 + offset, 5000 + offset) for offset in range(ROWS_IN_FLIGHT))
    stock = _work_stock(jobs)
    paused = IndexBatchWriter(index, directory=index_dir, min_free_bytes=1 << 60)
    poller = _poller(store=store, writer=paused, tmp_path=tmp_path, queue=cast("Any", stock))

    try:
        for _ in range(PASSES_OF_THE_PAUSE):
            paused_round = await poller.run_once()

            # Never ROUND_EMPTY. An empty claim in the middle of a pause means
            # the stock handed nothing out, and the only reason it would not is
            # that it wrote the rows off.
            assert paused_round.state == ROUND_PAUSED_LOW_DISK

        assert stock.written_off == []
        assert stock.waiting() == [5000 + offset for offset in range(ROWS_IN_FLIGHT)]
        # And the budget is not merely unspent, it is untouched: every row stands
        # where it stood before the pause, so the give-up rule keeps its meaning
        # for the deliveries that really were attempts.
        assert set(stock.deliveries_spent()) == {0}

        # The disk frees up, and nobody does anything about it. No occ command,
        # no restart, no reindex: the second half of the promise of the banner.
        paused._min_free_bytes = 0
        resumed = await poller.run_once()
    finally:
        paused.close()

    assert resumed.state == ROUND_WORKED
    assert resumed.indexed == ROWS_IN_FLIGHT
    assert stock.written_off == []
    assert stock.waiting() == []


def test_the_work_stock_simulation_reads_its_rules_out_of_the_php_source() -> None:
    """The anti-vacuity clause of the simulation above.

    A model that hard coded its rules would stay green on the day the rules
    move, and it would prove nothing about the halves that actually run. Both
    numbers are therefore read, and the helper that reads the harder one is
    shown a body with the rule and a body without it.
    """
    assert _max_deliveries() == 3

    without = "public function unlock(array $ids): int {\n\t\t$qb->set('locked_at', $free);\n"
    with_refund = without + "\t\t$r->set('retries', $r->createFunction('retries - 1'));\n"

    assert _hands_the_delivery_back(without) is False
    assert _hands_the_delivery_back(with_refund) is True


def test_a_row_handed_back_unjudged_does_not_count_as_a_delivery() -> None:
    """The fix itself, where it is written: QueueMapper::unlock.

    The give-up rule exists for a row that is handed out and never comes back,
    because nothing ever reports a failure for such a row and without a ceiling
    it would circle forever. A row that IS handed back is the opposite of that
    case: the container said out loud that it did not judge the file. Counting
    that hand-out against the file is what turned a disk pause into thirty
    write-offs.
    """
    body = _unlock_body(_php_source(PHP_QUEUE_MAPPER))

    assert _hands_the_delivery_back(body), (
        "unlock has to give the delivery back, otherwise a pause spends the budget of the rows it protects"
    )
    # And the refund happens while the row is still claimed. Releasing first
    # would let another collector take the row and count its own delivery, and
    # this decrement would then take that one away.
    assert body.index("retries - 1") < body.index("'locked_at'")


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


async def test_an_unexpected_error_in_a_pass_hands_the_held_rows_back(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Review WR-01: the catch-all of run() logged and backed off, but never gave
    # the held rows back; the next claim then replaced _held and the rows paid
    # the full lock timeout WITHOUT their delivery being refunded (the other
    # half refunds only at an unlock). Three such passes wrote healthy files off
    # as failed(repeatedly_stuck). The unlock in the catch-all is what this test
    # pins: the rows go back before the loop claims again, so no delivery is
    # spent and no verdict is written for them.
    queue = _FakeQueue(ClaimResult(jobs=(_job(), _job(92, 4712))))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    def dying_record(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise OSError("stopped in the middle")

    monkeypatch.setattr(store, "record", dying_record)
    poller.arm()
    stop = asyncio.Event()
    task = asyncio.create_task(poller.run(stop))
    try:
        for _ in range(200):
            if queue.unlocked:
                break
            await asyncio.sleep(0.01)
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=5)

    assert queue.unlocked == [[91, 92]], "the catch-all has to hand the held rows back"
    assert not poller.busy
    assert queue.acknowledged == [], "no verdict for a row the pass could not judge"
    assert poller.cooldown > 0


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


async def _until(condition: Callable[[], bool], *, seconds: float = 5.0) -> None:
    """Wait until ``condition`` holds, failing after ``seconds``."""
    for _ in range(int(seconds / 0.01)):
        if condition():
            return
        await asyncio.sleep(0.01)
    assert condition()


async def test_a_probe_hold_lets_the_pass_in_flight_end_with_its_acknowledgement(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # D-27-05: the hold starts no new pass, but the pass already running works
    # its claim to the end and acknowledges it. No unlock, no writer close.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)), ClaimResult(jobs=(_job(92, 4712),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    real = poller.run_once
    started = asyncio.Event()
    gate = asyncio.Event()
    calls: list[int] = []

    async def gated() -> Any:
        calls.append(1)
        if len(calls) == 1:
            started.set()
            await gate.wait()
        return await real()

    monkeypatch.setattr(poller, "run_once", gated)
    poller.arm()
    stop = asyncio.Event()
    task = asyncio.create_task(poller.run(stop))
    try:
        await asyncio.wait_for(started.wait(), timeout=5)
        poller.hold_for_probe()
        assert poller.probe_held
        gate.set()
        await _until(lambda: not poller.pass_in_flight and bool(queue.acknowledged))
        await asyncio.sleep(0.05)

        assert queue.acknowledged == [([91], {})]
        assert queue.unlocked == []
        assert len(calls) == 1
        assert poller.armed

        poller.release_probe_hold()
        assert not poller.probe_held
        await _until(lambda: len(queue.acknowledged) == 2)
        assert queue.acknowledged[1] == ([92], {})
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=5)


async def test_a_stop_during_a_probe_hold_ends_the_loop(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    poller.arm()
    poller.hold_for_probe()
    stop = asyncio.Event()

    task = asyncio.create_task(poller.run(stop))
    await asyncio.sleep(0.05)
    assert queue.claims == 0

    stop.set()
    await asyncio.wait_for(task, timeout=2)
    assert queue.claims == 0


async def test_a_probe_hold_neither_arms_nor_silences(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # T-27-12: the enable and disable of AppAPI stay in force across a hold.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    assert not poller.probe_held

    poller.hold_for_probe()
    poller.release_probe_hold()
    assert not poller.armed

    poller.arm()
    poller.hold_for_probe()
    assert poller.armed
    stop = asyncio.Event()
    task = asyncio.create_task(poller.run(stop))
    try:
        await asyncio.sleep(0.05)
        poller.silence()
        poller.release_probe_hold()
        await asyncio.sleep(0.05)

        assert not poller.armed
        assert queue.claims == 0
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=2)


@pytest.mark.usefixtures("volume")
def test_the_enabled_handler_arms_and_silences_the_poller() -> None:
    # Its own volume, because the handler now leaves the arming mark of DI-05-36
    # behind. Without the fixture the mark would land in the shared fallback
    # directory, and a run that ended between the enable and the disable would
    # hand every later lifespan of this machine an armed poller.
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
    for blocking in ("_writer_or_die().flush", "_writer_or_die().add", "_record_verdicts"):
        lines = [line for line in source.splitlines() if blocking in line and "to_thread" in line]

        assert lines, blocking
    # Since phase 26 the extraction runs in the executor of the slot pool and
    # never in the default one the search shares (Pitfall 5, issue #19).
    assert "self._pool.call(self._extract" in source
    assert "to_thread(self._extract" not in source
    assert "self._pool.call(self._writer_or_die().add" in source


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
        assert opened.version_mismatch(expected_versions(digest, ",".join(settings().languages))) == []
    finally:
        opened.close()


def test_a_fresh_volume_carries_the_two_marks_of_the_directory_it_builds(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The installation that has no index yet, and the leg of the CI that asked.

    The neighbour above says the seed leaves the state database agreeing with
    this code. It cannot say anything about the two marks of a directory,
    because the seed is forbidden to write the language one and because the
    schema one it writes is a fact about a directory that does not exist at the
    moment of the seed.

    So this case walks the path a container really walks on a fresh volume: the
    state database is opened, the writer is opened, and the writer is what
    creates the index directory. Afterwards both marks have to stand, because
    since phase 19 they are what
    :func:`findling.api.resources.field_plan_for` computes the field list of a
    search out of. Without them an installation that switched four languages on
    searches ``body_de`` and ``body_en`` for the rest of its life, whatever
    FINDLING_LANGUAGES says, and nothing anywhere says so. That is what the CI
    leg "Language proof, the four new chains answer on the ordinary search
    route" of deploy-harp run 36086044755 measured on all four legs.

    Six languages and not the factory pair on purpose: with ``de,en`` the absent
    mark is excused by ``_languages_are_legacy`` and the case would be green
    without a mark being written anywhere.
    """
    monkeypatch.setenv("FINDLING_LANGUAGES", "de,en,es,it,nl,pt")
    settings.cache_clear()
    digest = write_wordlist(volume)
    digest_nl = write_wordlist_nl(volume)
    languages = ",".join(settings().languages)
    assert languages == "de,en,es,it,nl,pt"
    dutch = dutch_mark(settings().languages)

    store = _open_state()
    writer = _open_writer(store)
    try:
        marks = store.read_meta()

        assert marks.get(SCHEMA_MARK) == str(SCHEMA_VERSION)
        assert marks.get(LANGUAGES_MARK) == languages
        # The third mark of a directory, stamped with the list on the volume.
        assert marks.get(DUTCH_MARK) == dutch
        assert dutch.endswith(digest_nl)
        assert store.version_mismatch(expected_versions(digest, languages, dutch_mark=dutch)) == []
    finally:
        writer.close()
        store.close()


def _a_volume_built_under_the_factory_pair(volume: Path, monkeypatch: pytest.MonkeyPatch) -> int:
    """Walk the path of a fresh container under de,en, close it, and name its generation.

    The state database is opened and the writer is opened, because the writer is
    what creates the directory and stamps its two marks. What the three cases
    below then change is what an admin or an update changes between two starts.
    """
    monkeypatch.setenv("FINDLING_LANGUAGES", "de,en")
    settings.cache_clear()
    write_wordlist(volume)
    store = _open_state()
    writer = _open_writer(store)
    try:
        assert store.read_meta().get(LANGUAGES_MARK) == "de,en"
        return store.index_version
    finally:
        writer.close()
        store.close()


def _switch_dutch_on(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Switch nl on the way a container does it: the setting and the Dutch list on the volume."""
    monkeypatch.setenv("FINDLING_LANGUAGES", "de,en,nl")
    settings.cache_clear()
    write_wordlist_nl(volume)


def test_a_drift_the_band_rebuild_answers_does_not_raise_the_generation(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A new language is answered by the band run, not by a full reindex.

    Planning probe of 2026-09-25 and the protocol of CI run 36072411846 ("Store
    upgrade 5") saw the same thing: a volume built under de,en, a container
    started under de,en,nl, and the opening of the state database raised the
    generation from 1 to 2. A raised generation makes every stored verdict stale,
    so the next crawl read every file again, which is the full reindex of about
    19 hours that the band run of phase 17 exists to spare. The language drift
    has to stay on record, because it is what starts the band run.
    """
    before = _a_volume_built_under_the_factory_pair(volume, monkeypatch)
    _switch_dutch_on(volume, monkeypatch)

    store = _open_state()
    try:
        after = store.index_version
        marks = store.read_meta()
        drift = store.version_mismatch(expected_versions(write_wordlist(volume), ",".join(settings().languages)))
    finally:
        store.close()

    assert after == before
    assert not marks.get(REBUILD_MARK)
    assert LANGUAGES_MARK in drift


def test_a_drift_only_a_crawl_answers_still_raises_the_generation(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The counter direction of the case above (T-21-01-01).

    A moved analyzer version needs the documents read again, and the raised
    generation is what orders that read. Exempting it along with the language
    mark would leave an index tokenised by code nobody can query it with.
    """
    before = _a_volume_built_under_the_factory_pair(volume, monkeypatch)
    aged = _open_state()
    aged.write_meta("analyzer_version", "0")
    aged.close()

    store = _open_state()
    try:
        after = store.index_version
    finally:
        store.close()

    assert after == before + 1


def test_a_drift_of_both_kinds_raises_the_generation(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A language drift does not shield a crawl drift that arrives with it."""
    before = _a_volume_built_under_the_factory_pair(volume, monkeypatch)
    aged = _open_state()
    aged.write_meta("analyzer_version", "0")
    aged.close()
    _switch_dutch_on(volume, monkeypatch)

    store = _open_state()
    try:
        after = store.index_version
    finally:
        store.close()

    assert after == before + 1


def test_a_dutch_drift_does_not_raise_the_generation(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A Dutch list that moved is answered by the band run, not by a full reindex (T-21-06-02).

    An index built under de,en,nl carries the mark of a list this container no
    longer holds. Opening the state database has to leave the generation where
    it was, because the band run analyses body_nl again out of the stored text,
    and a raised generation would order the crawl of every file behind it. The
    drift itself stays on record, since it is what starts the band run.
    """
    _switch_dutch_on(volume, monkeypatch)
    write_wordlist(volume)
    built = _open_state()
    writer = _open_writer(built)
    writer.close()
    built.write_meta(DUTCH_MARK, "1:alt")
    before = built.index_version
    built.close()

    store = _open_state()
    try:
        after = store.index_version
        marks = store.read_meta()
        expected = expected_versions(
            write_wordlist(volume), ",".join(settings().languages), dutch_mark=dutch_mark(settings().languages)
        )
        drift = store.version_mismatch(expected)
    finally:
        store.close()

    assert after == before
    assert not marks.get(REBUILD_MARK)
    assert drift == [DUTCH_MARK]


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


# -- the skip verdicts of the acknowledgement (DI-04-03) ---------------------
#
# Four reasons are decided by this container and by nothing else: encrypted, no
# text layer, empty text and a picture without a readable word. Until this plan
# they never crossed the boundary, so the error list of the status page grouped
# the half of the truth that Nextcloud had decided itself, and an admin read a
# scanned archive as "no errors". The tests below pin the shape of the crossing:
# one entry per file id, a code out of the closed list, and nothing else at all.


def _skip_job(queue_id: int, file_id: int, mime: str) -> QueueJob:
    """A job whose title and path are worth leaking, so that a leak is visible."""
    return _job(
        queue_id,
        file_id,
        mime=mime,
        size=len(BODY_BYTES),
        title="Gehaltsabrechnung Mueller.pdf",
        path="Personal/Loehne/Gehaltsabrechnung Mueller.pdf",
    )


async def test_a_skipped_file_travels_with_its_file_id_and_its_reason(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The verdict belongs to this container alone, and without this list the
    # Nextcloud half never learns it: the error list groups findling_file_state,
    # and that table only ever saw what Nextcloud itself had decided (DI-04-03).
    job = _skip_job(91, 4711, "video/mp4")
    queue = _FakeQueue(ClaimResult(jobs=(job,)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    result = await poller.run_once()

    assert result.skipped == 1
    assert queue.skips == [{4711: "mime_not_allowed"}]
    # And the row still leaves the queue the ordinary way: the skip list is a
    # second statement about it, never a replacement for the acknowledgement.
    assert queue.acknowledged == [([91], {})]


async def test_a_skip_verdict_carries_neither_path_nor_title_nor_text(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # T-05-45. The job carries a telling name and a telling path, and the whole
    # point of the list is that neither of them travels with the verdict.
    job = _skip_job(91, 4711, "video/mp4")
    queue = _FakeQueue(ClaimResult(jobs=(job,)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()

    payload = repr(queue.skips)
    assert "Gehaltsabrechnung" not in payload
    assert "Personal" not in payload
    assert queue.skips == [{4711: "mime_not_allowed"}]


async def test_an_empty_text_document_reports_its_reason(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # One of the four container reasons, produced by the real extractor instead
    # of a stand-in: a readable file that carries no word at all.
    job = _skip_job(91, 4711, "text/plain")
    queue = _FakeQueue(ClaimResult(jobs=(job,)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: b"   \n\t \n"})

    await poller.run_once()

    assert queue.skips == [{4711: "empty_text"}]


async def test_a_file_handed_to_the_ocr_track_sends_no_skip_verdict(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # skipped(no_text_layer) with OCR on is the handover point and not an end
    # state. Reporting it would put every scan of the instance into the error
    # list under "no text in the document", and nothing would ever take it out
    # again: indexed is the container's number and is never written into that
    # table. The rule is the one the done list already follows.
    job = _job(mime="application/pdf", size=len(SCAN_BYTES))
    queue = _FakeQueue(ClaimResult(jobs=(job,)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SCAN_BYTES})

    await poller.run_once()

    assert queue.requeues == [([4711], "ocr")]
    assert queue.skips == [{}]


@pytest.mark.usefixtures("ocr_off")
async def test_the_same_verdict_travels_once_it_is_an_end_state(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # With OCR switched off nothing is handed over, so the very same verdict is
    # final and belongs in the list. The distinction is the handover and never
    # the reason code.
    job = _job(mime="application/pdf", size=len(SCAN_BYTES))
    queue = _FakeQueue(ClaimResult(jobs=(job,)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: SCAN_BYTES})

    await poller.run_once()

    assert queue.requeues == []
    assert queue.skips == [{4711: "no_text_layer"}]


async def test_a_pass_without_a_skip_behaves_exactly_as_before(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The regression guard of this change: an ordinary indexing pass sends an
    # empty third list and is otherwise the pass of yesterday.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    result = await poller.run_once()

    assert result.indexed == 1
    assert queue.acknowledged == [([91], {})]
    assert queue.skips == [{}]


async def test_a_failure_stays_in_the_failure_list_and_out_of_the_skip_list(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The two lists carry two different states, and a file belongs to exactly
    # one of them. A verdict in both would be recorded twice inside the same
    # transaction, and the second write would decide what the admin sees.
    broken = b"PK not really a package at all"
    job = _job(mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", size=len(broken))
    queue = _FakeQueue(ClaimResult(jobs=(job,)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: broken})

    await poller.run_once()

    assert queue.acknowledged == [([], {91: "corrupt"})]
    assert queue.skips == [{}]


async def test_every_skipped_file_of_a_batch_gets_its_own_entry(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # One entry per file id and not one per batch: the groups of the error list
    # are counted from these rows, so a batch that reported only its first skip
    # would undercount every group by the length of the batch.
    jobs = (
        _skip_job(91, 4711, "video/mp4"),
        _skip_job(92, 4712, "video/mp4"),
        _skip_job(93, 4713, "text/plain"),
    )
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4713: b"  \n "})

    await poller.run_once()

    assert queue.skips == [{4711: "mime_not_allowed", 4712: "mime_not_allowed", 4713: "empty_text"}]


async def test_a_file_judged_again_carries_its_new_reason(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The upsert on the receiving side needs a second verdict for the same file
    # id to work on. The container produces one whenever the row comes back, and
    # the reason may well differ from the one before.
    queue = _FakeQueue(
        ClaimResult(jobs=(_skip_job(91, 4711, "video/mp4"),)),
        ClaimResult(jobs=(_skip_job(92, 4711, "text/plain"),)),
    )
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, bodies={4711: b"   "})

    await poller.run_once()
    await poller.run_once()

    assert queue.skips == [{4711: "mime_not_allowed"}, {4711: "empty_text"}]


# -- the whole chain of the reindex banner (DI-04-04) ------------------------


def _aged_state(volume: Path) -> None:
    """A state database whose index was built by an older text analysis.

    One indexed file and marks that do not match this code, which is what a
    container update leaves behind on a volume that has been indexing for weeks.
    """
    aged = open_store(settings().state_db, meta=expected_versions("older-digest", ",".join(settings().languages)))
    aged.record(
        4711,
        FileMeta(
            storage_id=3,
            root_id=2,
            path="Vertraege/Kuendigung.txt",
            title="Kuendigung.txt",
            mime="text/plain",
            size=len(BODY_BYTES),
            mtime=1_756_600_000,
            etag="5d41402abc4b2a76b9719d911017c592",
        ),
        "indexed",
        None,
        content_hash=hashlib.sha256(BODY_BYTES).hexdigest(),
    )
    aged.close()


async def test_the_restart_rebuilds_and_the_banner_goes_by_itself(
    volume: Path, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    """DI-04-04 end to end: the remedy the banner names actually clears it.

    The chain is the one an admin walks: the container comes up after an update,
    the marks disagree, ``occ findling:index --restart`` puts every file back
    into the queue, the pass reads them again, and the moment the queue runs dry
    the marks are written and the drift is gone. Nobody stamped anything.
    """
    digest = write_wordlist(volume)
    expected = expected_versions(digest, ",".join(settings().languages))
    _aged_state(volume)

    store = _open_state()
    try:
        # The state an admin sees as the banner, and the raised generation that
        # is what makes the restart do anything at all.
        assert store.version_mismatch(expected) != []
        assert store.is_unchanged(4711, hashlib.sha256(BODY_BYTES).hexdigest()) is False

        queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
        poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

        worked = await poller.run_once()
        assert worked.indexed == 1
        # Still up: the queue has not been proven empty yet, so the rebuild is
        # not through and nothing may be declared current.
        assert store.version_mismatch(expected) != []

        empty = await poller.run_once()

        assert empty.state == ROUND_EMPTY
        assert store.version_mismatch(expected) == []
    finally:
        store.close()


async def test_an_unfinished_rebuild_keeps_the_banner_up(
    volume: Path, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # T-05-48. The queue is empty because the crawl has not been queued yet, not
    # because the work is done, and the old row is the proof: a mark written
    # here would call an index of the old analysis current and take away the one
    # line telling the admin why hits are missing.
    digest = write_wordlist(volume)
    expected = expected_versions(digest, ",".join(settings().languages))
    _aged_state(volume)

    store = _open_state()
    try:
        poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=_FakeQueue())

        result = await poller.run_once()

        assert result.state == ROUND_EMPTY
        assert store.version_mismatch(expected) != []
    finally:
        store.close()


async def test_an_index_that_never_drifted_is_left_alone(
    volume: Path, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The ordinary instance, which is every instance most of the time. Nothing
    # is raised, nothing is written, and the generation stays where it was.
    digest = write_wordlist(volume)
    expected = expected_versions(digest, ",".join(settings().languages))

    store = _open_state()
    try:
        before = store.index_version
        poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=_FakeQueue())

        await poller.run_once()

        assert store.index_version == before
        assert store.version_mismatch(expected) == []
    finally:
        store.close()


async def test_a_rebuild_survives_a_restart_of_the_container(
    volume: Path, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # A rebuild of fifty thousand files on a four gigabyte box runs for days, and
    # such a box restarts. A container that raised the generation again on every
    # start would make the work of every day stale on the next morning, so the
    # second start has to find the rebuild it is already in.
    write_wordlist(volume)
    _aged_state(volume)

    first = _open_state()
    generation = first.index_version
    first.close()

    second = _open_state()
    try:
        assert second.index_version == generation
    finally:
        second.close()


async def test_a_pass_that_stamps_the_marks_tells_the_reading_side_once(
    volume: Path, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    """Audit finding H-19-01, the half of it that carries no time window at all.

    Since phase 19 the field list of a search is computed out of the stored
    marks, once per opening of the reading side, and this pass writes those
    marks while that side is wide open. A poller that said nothing would leave
    the process answering out of the list it computed before the rebuild was
    through: the marks would promise six language chains, the directory would
    carry them, and the search would reach two of them until somebody restarted
    the container.

    The three passes are the three things this has to get right: nothing is said
    while there is still work, it is said the moment the marks are current, and
    it is not said again afterwards, because the flag behind the stamp makes
    this one release per process rather than one per idle pass.
    """
    digest = write_wordlist(volume)
    expected = expected_versions(digest, ",".join(settings().languages))
    _aged_state(volume)
    told: list[str] = []

    store = _open_state()
    try:
        queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
        poller = _poller(
            store=store,
            writer=writer,
            tmp_path=tmp_path,
            queue=queue,
            marks_stamped=lambda: told.append("let go"),
        )

        worked = await poller.run_once()
        assert worked.indexed == 1
        assert told == [], "the queue has not run dry, so nothing is stamped and nothing is said"

        empty = await poller.run_once()

        assert empty.state == ROUND_EMPTY
        assert store.version_mismatch(expected) == []
        assert told == ["let go"]

        await poller.run_once()

        assert told == ["let go"], "the flag behind the stamp is down, so this costs one release per process"
    finally:
        store.close()


async def test_a_pass_that_may_not_stamp_yet_tells_nobody(
    volume: Path, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The other side of H-19-01, and the reason the release hangs off the answer
    # of the stamp rather than off the idle pass: an unfinished rebuild writes
    # no mark, so there is nothing anybody has to be told about, and a reading
    # side dropped here would cost every search of this container a reopen for
    # as long as the rebuild runs.
    write_wordlist(volume)
    _aged_state(volume)
    told: list[str] = []

    store = _open_state()
    try:
        poller = _poller(
            store=store,
            writer=writer,
            tmp_path=tmp_path,
            queue=_FakeQueue(),
            marks_stamped=lambda: told.append("let go"),
        )

        result = await poller.run_once()

        assert result.state == ROUND_EMPTY
        assert told == []
    finally:
        store.close()


async def test_a_pass_that_cannot_write_the_marks_still_ends(
    volume: Path, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Bookkeeping about the index is not the index. A locked database here must
    # not end a pass whose documents are durable, and the next idle poll asks
    # again rather than the container falling over.
    write_wordlist(volume)
    _aged_state(volume)
    store = _open_state()
    try:
        poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=_FakeQueue())
        monkeypatch.setattr(
            "findling.worker.poller.stamp_after_rebuild",
            lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("locked")),
        )

        result = await poller.run_once()

        assert result.state == ROUND_EMPTY
    finally:
        store.close()


# The two doors plan 14-07 knocks on: "are you working" and "let go". Both are
# read and called from a lifespan task on the event loop, and neither of them is
# called anywhere in the product yet. That is deliberate: the release itself is
# one plan, the clock that triggers it is another.


def test_a_freshly_built_poller_is_not_busy() -> None:
    # The shape a container is in for most of its life, and the shape the idle
    # release of MEM-02 is built for: nothing claimed, nothing held.
    assert Poller().busy is False


def test_a_poller_that_holds_queue_rows_says_it_is_busy() -> None:
    worker = Poller()
    worker._held = {91, 92}

    assert worker.busy is True


async def test_a_pass_that_gave_its_rows_back_is_not_busy_any_more(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Both halves of the answer against a real pass rather than against an
    # assignment: busy while the pass is between the claim and the
    # acknowledgement, not busy once the rows are gone.
    queue = _FakeQueue(ClaimResult(jobs=(_job(),)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)
    seen: list[bool] = []
    real_record = store.record

    def record(*args: Any, **kwargs: Any) -> None:
        seen.append(poller.busy)
        real_record(*args, **kwargs)

    monkeypatch.setattr(store, "record", record)

    assert poller.busy is False

    await poller.run_once()

    assert seen == [True], "a pass between the claim and the acknowledgement is at work"
    assert poller.busy is False, "and the pass that acknowledged its rows is not"


def test_a_silenced_poller_with_an_empty_work_stock_is_not_busy() -> None:
    # The distinction the lifespan task lives on: armed is not the question, and
    # a container that was switched off is not at work either.
    worker = Poller()
    worker.arm()
    worker.silence()

    assert worker.armed is False
    assert worker.busy is False


async def test_stand_down_waits_for_the_pass_in_flight_before_it_answers() -> None:
    """H-18-01 in one case: silencing returns at once, standing down does not.

    The condition ``transfer_documents`` names in its own docstring is that the
    poller may not write into the source index while the band run is going, and
    until the audit of this phase the caller did not establish it: ``silence()``
    cleared a flag and came straight back while the pass in flight worked its
    claim to the end and committed. A document that arrives below the cursor in
    that window is never carried over, and on the first indexing of a mount the
    file ids are spread over the whole range, so below the cursor is the
    ordinary case and not the corner.

    The wait hangs off the pass and not off the held rows, and this case says so
    by holding a row the whole time: a pass that ended in an exception leaves its
    rows held until the next pass claims again, and on a poller that has just
    been silenced there is no next pass.
    """
    queue = _FakeQueue()
    worker = Poller()
    worker._queue = cast("Any", queue)
    worker.arm()
    worker._in_flight = True
    worker._held = {91}

    standing_down = asyncio.create_task(worker.stand_down())
    # Several ticks of the wait, and still nothing on the clock worth naming.
    await asyncio.sleep(STAND_DOWN_TICK_SECONDS * 4)

    assert worker.armed is False, "the flag is cleared at once, whatever the pass is doing"
    assert standing_down.done() is False, "and the answer waits for the pass"

    worker._in_flight = False

    assert await standing_down is True
    assert queue.unlocked == [[91]], "the held row went back with the stand down"
    assert worker.busy is False


async def test_stand_down_gives_the_index_handle_back_and_the_next_pass_opens_a_new_one(
    volume: Path, store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    """C-18-01 at the poller: the writer is the thing that has to go, not a flag.

    It is built once in ``_open()`` and was handed back only in ``aclose()``, so
    it outlived every pass and held the live directory right through the
    directory swap; on Linux the swap then succeeded and the poller went on
    writing into inodes with no name. Standing down closes it and sets it to
    None, and the next ``_open()`` builds a fresh one.

    The queue, the client and the connection pool stay exactly as they were, and
    that is asserted rather than assumed: none of them ever pointed at an index
    directory, so a swap cannot have invalidated them, and dropping them here
    would pay a Nextcloud bootstrap for nothing.
    """
    write_wordlist(volume)
    worker = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=_FakeQueue(ClaimResult(jobs=())))
    queue = await asyncio.to_thread(worker._open)
    assert worker._writer is writer

    assert await worker.stand_down() is True

    assert worker._writer is None, "the handle is gone, so a rename can have the directory"
    assert worker._queue is queue, "and the companion half is untouched by an index swap"

    again = await asyncio.to_thread(worker._open)

    assert again is queue
    assert worker._writer is not None
    assert worker._writer is not writer, "a fresh handle, on whatever directory the settings now name"


async def test_stand_down_answers_false_when_the_pass_outlasts_the_budget(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A budget that ran out may not look like a poller that went quiet.

    False is what stops the rebuild in front of the first rename. A stand down
    that answered True here would hand the swap a live writer on the directory
    it is about to remove, which is the whole of C-18-01.
    """
    worker = Poller()
    worker.arm()
    worker._in_flight = True

    with caplog.at_level("WARNING", logger="findling.worker.poller"):
        answer = await worker.stand_down(budget=0.0)

    assert answer is False
    assert worker.armed is False, "it is silenced all the same, because that half always works"
    assert "is not standing down" in caplog.text


def test_reading_busy_twice_gives_the_same_answer_and_moves_nothing() -> None:
    # A property the release asks before it does anything must not be the reason
    # the release happens. Reading it is reading, and the held set is untouched.
    worker = Poller()
    worker._held = {91}

    first, second = worker.busy, worker.busy

    assert first is True
    assert second is True
    assert worker._held == {91}


def _with_a_built_cutter() -> Poller:
    """A poller whose cutter is in place, without reading a single artifact.

    The pair is what the release is about, and the two objects behind it are
    never called here: 544,3 MB of tokenizer and splitter would be the one thing
    this suite must not pay to ask whether a field is None.
    """
    worker = Poller()
    worker._track._cutter_absent = False
    worker._track._chunker = cast("Any", lambda _text: [])
    worker._track._model = cast("Any", object())
    return worker


def test_a_poller_with_a_built_cutter_lets_go_of_both_halves() -> None:
    worker = _with_a_built_cutter()

    assert worker.release_cutter() is True
    assert worker._track._chunker is None
    assert worker._track._model is None


def test_a_poller_without_a_built_cutter_has_nothing_to_release() -> None:
    # The state the lifespan task finds on most of its rounds: the release runs
    # every tick, and a container that never indexed anything has never built
    # the pair. False is the answer that keeps the counter of 14-07 honest.
    worker = Poller()

    assert worker.release_cutter() is False
    assert worker._track._chunker is None
    assert worker._track._model is None


def test_a_cutter_release_while_the_pass_holds_rows_does_nothing() -> None:
    """Pitfall 3 of the phase research, held as a behaviour.

    The weights fall and the next row loads them again six seconds later. Over a
    full run the release turns into a cost instead of a saving, and the run time
    grows without anything going red anywhere. The warning sign is named in the
    research: ``unload_count`` rising more than once during a full run.
    """
    worker = _with_a_built_cutter()
    worker._held = {91, 92}

    assert worker.busy is True
    assert worker.release_cutter() is False
    assert worker._track._chunker is not None, "the pair stays while the pass is at work"
    assert worker._track._model is not None


def test_the_first_cutter_build_after_a_release_puts_the_pair_back(monkeypatch: pytest.MonkeyPatch) -> None:
    # The rebuild needs no new code: the top of _build_the_cutter returns when
    # both fields are set and builds otherwise, and poller.py:1130 already calls
    # it conditionally for every row that needs a cutter.
    monkeypatch.setattr("findling.worker.embedding.open_tokenizer", lambda _directory: object())
    monkeypatch.setattr("findling.worker.embedding.make_splitter", lambda *args, **kwargs: object())
    monkeypatch.setattr("findling.worker.embedding.shared_model", lambda: cast("Any", object()))
    worker = Poller()
    worker._track._cutter_absent = False

    assert worker._track._build_the_cutter() is True
    assert worker.release_cutter() is True
    assert worker._track._chunker is None
    assert worker._track._model is None

    assert worker._track._build_the_cutter() is True
    assert worker._track._chunker is not None, "the next row that needs a cutter gets one"
    assert worker._track._model is not None


def test_a_release_leaves_the_permanent_no_about_the_cutter_alone() -> None:
    """Pitfall 8, first half: ``_cutter_absent`` is a property of the installation.

    A container without a model that forgets this marker starts stating every
    row again, twelve times an hour instead of once per process. Resetting it
    would be anti pattern 7 of ARCHITECTURE.md: a fact that was established once
    is thrown away by an unrelated operation.
    """
    absent = Poller()
    absent._track._chunker = cast("Any", lambda _text: [])
    absent._track._model = cast("Any", object())

    assert absent._track._cutter_absent is True

    assert absent.release_cutter() is True
    assert absent._track._cutter_absent is True, "the installation did not change because memory was handed back"

    present = _with_a_built_cutter()

    assert present.release_cutter() is True
    assert present._track._cutter_absent is False, "and the other answer survives just as unchanged"


def test_a_cutter_release_does_not_cut_a_running_cooldown_short() -> None:
    """Pitfall 8, second half: ``_cutter_failed_at`` is the running cooldown.

    A build that threw is remembered with a timestamp and tried again after
    LOAD_RETRY_SECONDS. A release that clears the stamp ends that waiting time
    silently, and the broken graph is opened once per document again instead of
    twelve times an hour.
    """
    worker = _with_a_built_cutter()
    stamp = time.monotonic()
    worker._track._cutter_failed_at = stamp

    assert worker.release_cutter() is True
    assert worker._track._cutter_failed_at == stamp, "the moment that failed is not this operation's business"
    assert worker._track._cutter_cooling_down is True, "and the waiting time keeps running"


def test_the_release_never_leaves_half_a_cutter_behind() -> None:
    """Never half, as a property of the source rather than of one run.

    ``_embed_ready`` and the top of ``_build_the_cutter`` both read the pair, so
    a cutter with exactly one field at None would answer "built" to both of them
    and hand rows to a spur that cannot run. The method is read here for every
    attribute it assigns: the pair and nothing else, which is the same statement
    as the two marker tests above make one behaviour at a time.
    """
    # The pair lives in the embedding track since plan 25-07, and the poller
    # only delegates to it; so the track's source is the one that is read.
    source = (POLLER_SOURCE.parent / "embedding.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    bodies = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "release_cutter"]

    assert len(bodies) == 1, "one release and not two spellings of it"

    assigned = [
        target.attr
        for node in ast.walk(bodies[0])
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Attribute)
    ]

    assert sorted(assigned) == ["_chunker", "_model"]


def test_after_a_cutter_release_no_half_pair_promises_the_track() -> None:
    """The half that would be invisible, asked through the property that reads the pair.

    ``_embed_ready`` says yes for two different reasons: the pair is built, or it
    can still be built. This poller has the permanent no about the artifacts, so
    only the first reason is left, and after the release the answer has to be no.
    Had the release cleared exactly one of the two fields, the answer would still
    be yes here, rows would be handed to a spur that cannot run, and nothing
    would raise anywhere.
    """
    worker = Poller()
    worker._track._vectors = cast("Any", object())
    worker._track._chunker = cast("Any", lambda _text: [])
    worker._track._model = cast("Any", object())

    assert worker._track._cutter_absent is True, "no artifacts, so a built pair is the only yes left"
    assert worker._track._embed_ready is True

    assert worker.release_cutter() is True
    assert worker._track._embed_ready is False, "the pair is gone whole, so nothing promises the track"


# -- the pass under N slots (plan 26-06, PAR-02) ------------------------------


@dataclass(slots=True)
class _SlotExtractor:
    """An extractor that takes its time and counts how many run beside it.

    Thread safe, because under several slots it is called from the threads of
    the pool at once. It writes down the order of the calls, the thread names
    and, per call, how many rows had been handed back by then, which is what
    the test of "handed back before the first extraction" reads.
    """

    seconds: float = 0.2
    error: BaseException | None = None
    queue: _FakeQueue | None = None
    poller: Poller | None = None
    release: threading.Event | None = None
    running: int = 0
    most: int = 0
    finished: int = 0
    paths: list[str] = field(default_factory=list)
    threads: list[str] = field(default_factory=list)
    unlocked_at_call: list[int] = field(default_factory=list)
    held_at_call: list[set[int]] = field(default_factory=list)
    # Called once per extraction, in the thread of the pool: what a test wants
    # to see from inside a running pass, the mark in state.db above all.
    probe: Callable[[], None] | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def __call__(
        self,
        path: str,
        mime: str,
        size: int,
        *,
        route: Route | None = None,
        timeout_seconds: float | None = None,
    ) -> ExtractionOutcome:
        del mime, size, route, timeout_seconds
        with self.lock:
            self.running += 1
            self.most = max(self.most, self.running)
            self.paths.append(path)
            self.threads.append(threading.current_thread().name)
            if self.queue is not None:
                self.unlocked_at_call.append(len(self.queue.unlocked))
            if self.poller is not None:
                self.held_at_call.append(set(self.poller._held))
        if self.probe is not None:
            self.probe()
        try:
            if self.release is not None:
                self.release.wait(timeout=10)
            else:
                time.sleep(self.seconds)
            if self.error is not None:
                raise self.error
            return ExtractionOutcome.indexed(BODY)
        finally:
            with self.lock:
                self.running -= 1
                self.finished += 1


# Headroom far above what any slot count of these tests needs, so the throttle
# of plan 26-09 lets every slot run unless a test says otherwise.
_ROOM_FOR_EVERY_SLOT = 1 << 40


def _ocr_row(offset: int) -> QueueJob:
    return _job(
        300 + offset,
        7000 + offset,
        kind="ocr",
        mime="application/pdf",
        title=f"Scan{offset}.pdf",
        path=f"Scans/Scan{offset}.pdf",
    )


def _slot_poller(
    *,
    store: Store,
    writer: IndexBatchWriter,
    tmp_path: Path,
    queue: _FakeQueue,
    extract: Any,
    ocr_slots: int | None,
    bodies: dict[int, bytes | BaseException | None] | None = None,
    headroom: Callable[[], int | None] = lambda: _ROOM_FOR_EVERY_SLOT,
) -> Poller:
    return Poller(
        store=store,
        writer=writer,
        tmp_dir=tmp_path / "tmp",
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        gateway_factory=lambda: cast("Any", _FakeGatewayClient()),
        queue_factory=lambda nc: cast("Any", queue),
        fetch=_gateway(bodies or {}),
        extract=extract,
        ocr_slots=ocr_slots,
        headroom=headroom,
    )


async def test_economy_reads_its_scans_one_after_the_other_on_the_same_wire(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # D-26-09, SC3: no hardware known, no choice stored, so Economy with one
    # slot. The claim asks for no lane, nothing is handed back, and the two
    # scans run one at a time in claim order, exactly as before phase 26.
    jobs = (_ocr_row(0), _ocr_row(1))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.05)
    poller = _slot_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=None)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert queue.lanes == [None]
    assert queue.unlocked == []
    assert extract.most == 1
    assert [Path(path).name for path in extract.paths] == ["job-300.part", "job-301.part"]
    assert queue.acknowledged == [([300, 301], {})]


async def test_four_slots_read_eight_scans_four_at_a_time_and_index_each_once(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # SC1 and T-26-19: at most four at once, every scan exactly once in the
    # index, one commit for the whole pass and the acknowledgement behind it.
    jobs = tuple(_ocr_row(offset) for offset in range(8))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.2)
    poller = _slot_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=4)
    flushes: list[int] = []
    real_flush = writer.flush

    def counting_flush() -> Any:
        flushes.append(len(queue.acknowledged))
        return real_flush()

    monkeypatch.setattr(writer, "flush", counting_flush)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert result.indexed == 8
    assert extract.most == 4
    assert extract.finished == 8
    assert sorted(_stored_ids(index)) == [7000 + offset for offset in range(8)]
    assert flushes == [0], "one commit, and no acknowledgement before it"
    assert len(queue.acknowledged) == 1
    assert queue.acknowledged[0][0] == [300 + offset for offset in range(8)]
    assert queue.unlocked == []


async def test_rows_beyond_two_per_slot_go_back_before_the_first_extraction(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # D-26-13, T-26-18: two slots keep four scans; the six after them go back
    # through unlock before a single child starts, and leave the held set.
    jobs = tuple(_ocr_row(offset) for offset in range(10))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.02, queue=queue)
    poller = _slot_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=2)
    extract.poller = poller

    result = await poller.run_once()

    handed_back = [300 + offset for offset in range(4, 10)]
    assert queue.unlocked == [handed_back]
    assert extract.unlocked_at_call
    assert set(extract.unlocked_at_call) == {1}
    assert all(not (held & set(handed_back)) for held in extract.held_at_call)
    assert result.claimed == 4
    assert extract.finished == 4
    assert queue.acknowledged == [([300, 301, 302, 303], {})]


async def test_the_slots_never_outnumber_the_scans_the_claim_delivered(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # D-26-07: an old companion hands out two OCR rows, so two slots at most,
    # and a content row beside them waits for one of the two.
    jobs = (
        _ocr_row(0),
        _ocr_row(1),
        _job(401, 8001, mime="text/plain"),
        _job(402, 8002, mime="text/plain"),
    )
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.1)
    poller = _slot_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=4)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert extract.most == 2
    assert extract.finished == 4


async def test_every_extraction_runs_in_the_threads_of_the_pool(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # Pitfall 5: never the default executor the search shares, neither under
    # several slots nor in the serial loop of a content row.
    jobs = (_ocr_row(0), _ocr_row(1), _job(401, 8001, mime="text/plain"))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.01)
    poller = _slot_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=2)

    await poller.run_once()

    assert len(extract.threads) == 3
    assert all(name.startswith("findling-slot") for name in extract.threads), extract.threads


async def test_a_gateway_that_fails_in_a_task_gives_every_row_back_behind_the_barrier(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    jobs = (_ocr_row(0), _ocr_row(1), _ocr_row(2))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.1)
    poller = _slot_poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=queue,
        extract=extract,
        ocr_slots=2,
        bodies={7001: OSError("gateway down")},
    )

    result = await poller.run_once()

    assert result.state == ROUND_GATEWAY_UNAVAILABLE
    # The scans that did run had ended before the rows went back.
    assert extract.running == 0
    assert queue.unlocked == [[300, 301, 302]]
    assert queue.acknowledged == []
    assert store.file_row(7000) is None
    assert store.file_row(7002) is None
    assert poller.busy is False


@pytest.mark.parametrize(("engine", "reason"), [(False, "corrupt"), (True, "ocr_failed")])
async def test_a_killed_child_in_economy_keeps_its_verdict_of_before_phase_26(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, engine: bool, reason: str
) -> None:
    # One slot is Sparsam unchanged: the old verdict, no solo run and no
    # report to the guard (D-26-16 applies to several slots only).
    jobs = (_ocr_row(0), _ocr_row(1))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.01, error=ChildKilled(engine=engine))
    poller = _slot_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=1)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert queue.acknowledged == [([], {300: reason, 301: reason})]
    assert extract.finished == 2
    assert guard.take_child_kills() == 0


async def test_an_embed_row_of_lane_all_waits_until_the_scans_are_through(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # IDX-08, D-25-11: in lane all the embedding runs inline, and it must not
    # overlap with OCR, so the embed row starts behind the barrier.
    jobs = (_ocr_row(0), _job(501, 9001, kind="embed"), _ocr_row(1))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.15)
    poller = _slot_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=2)
    seen: list[tuple[int, int]] = []

    async def embed_row(self: object, job: QueueJob, done: list[int]) -> str:
        del self
        seen.append((extract.running, extract.finished))
        done.append(job.queue_id)
        return "no_stored_text"

    monkeypatch.setattr(type(poller.track), "embed_row", embed_row)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert extract.most == 2
    assert seen == [(0, 2)]


async def test_a_cancelled_pass_cancels_its_scans_and_the_rows_go_back(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    jobs = (_ocr_row(0), _ocr_row(1))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    release = threading.Event()
    extract = _SlotExtractor(release=release)
    poller = _slot_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=2)

    running = asyncio.create_task(poller.run_once())
    try:
        for _ in range(500):
            if extract.running == 2:
                break
            await asyncio.sleep(0.01)
        assert extract.running == 2
        running.cancel()
        with pytest.raises(asyncio.CancelledError):
            await running
        scans = [task for task in asyncio.all_tasks() if "_scan_in_a_slot" in repr(task.get_coro())]
        assert all(task.done() for task in scans)
        assert await poller.unlock_held() == 2
        assert queue.unlocked == [[300, 301]]
    finally:
        release.set()
    for _ in range(500):
        if extract.running == 0:
            break
        await asyncio.sleep(0.01)
    # The cancelled scans never reach the writer, whatever their children did.
    assert writer.pending == 0
    assert queue.acknowledged == []


async def test_the_pass_line_carries_the_slots_and_nothing_about_a_file(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    jobs = (_ocr_row(0), _ocr_row(1))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.01)
    poller = _slot_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=2)

    with caplog.at_level("INFO", logger="findling.worker.poller"):
        await poller.run_once()

    finished = [line for line in _poller_lines(caplog) if line.startswith("pass finished")]
    assert len(finished) == 1
    assert finished[0].endswith("slots=2 throttled=0")
    for line in _poller_lines(caplog):
        assert "Scan" not in line
        assert ".pdf" not in line


async def test_a_poller_closes_the_pool_it_built_and_leaves_a_handed_in_one_open(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    handed_in = SlotPool(2)
    own = Poller(store=store, writer=writer, tmp_dir=tmp_path / "tmp")
    borrowed = Poller(store=store, writer=writer, tmp_dir=tmp_path / "tmp", pool=handed_in)
    try:
        await own.aclose()
        await borrowed.aclose()

        with pytest.raises(RuntimeError):
            own._pool.call(len, "x")
        assert await handed_in.call(len, "abc") == 3
    finally:
        handed_in.close()


# -- the throttle, the way back and the pass mark (plan 26-09, PAR-03) --------


class _CountingHeadroom:
    """A headroom that answers a fixed value and counts how often it was asked."""

    def __init__(self, value: int | None) -> None:
        self.value = value
        self.calls = 0

    def __call__(self) -> int | None:
        self.calls += 1
        return self.value


async def test_a_short_headroom_throttles_four_slots_to_three_and_keeps_six_rows(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # D-26-02: slot 1 always, slot k needs (k - 1) x 250 MiB plus the reserve of
    # 250 MiB. Three times 250 MiB therefore carries three slots, and the rows
    # kept follow the slots allowed: two per slot, six of eight.
    jobs = tuple(_ocr_row(offset) for offset in range(8))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.15)
    poller = _slot_poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=queue,
        extract=extract,
        ocr_slots=4,
        headroom=lambda: 3 * OCR_SLOT_COST_BYTES,
    )

    with caplog.at_level("INFO", logger="findling.worker.poller"):
        result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert extract.most == 3
    assert extract.finished == 6
    assert queue.unlocked == [[306, 307]]
    state = guard.snapshot()
    assert (state.slots_target, state.slots_in_force, state.throttled) == (4, 3, True)
    finished = [line for line in _poller_lines(caplog) if line.startswith("pass finished")]
    assert finished[0].endswith("slots=3 throttled=1")


async def test_an_unreadable_headroom_means_one_slot_and_two_rows(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    jobs = tuple(_ocr_row(offset) for offset in range(8))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.02)
    poller = _slot_poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=4, headroom=lambda: None
    )

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert extract.most == 1
    assert extract.finished == 2
    assert queue.unlocked == [[302, 303, 304, 305, 306, 307]]
    assert guard.snapshot().slots_in_force == 1


async def test_economy_never_asks_for_the_headroom(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    jobs = (_ocr_row(0), _ocr_row(1))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _SlotExtractor(seconds=0.01)
    headroom = _CountingHeadroom(None)
    poller = _slot_poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=None, headroom=headroom
    )

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert headroom.calls == 0
    assert extract.most == 1
    assert queue.unlocked == []
    assert queue.acknowledged == [([300, 301], {})]
    state = guard.snapshot()
    assert (state.slots_target, state.slots_in_force, state.throttled) == (1, 1, False)


def _capped_at_standard() -> None:
    """A cap as the guard sets it: chosen Standard, lowered once to Economy."""
    assert guard.lower(guard.CAUSE_OOM_KILL, now=1.0, chosen=Profile.STANDARD, effective=Profile.STANDARD)


async def test_the_confirmed_token_lifts_the_cap(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    # D-26-04: the admin confirms the token the guard handed out.
    _capped_at_standard()
    queue = _FakeQueue()
    queue.profile_answer = "standard"
    queue.confirmed_answer = guard.snapshot().token
    poller = _slot_poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=_SlotExtractor(), ocr_slots=1
    )

    await poller.run_once()

    assert guard.snapshot().cap is None


async def test_a_foreign_token_leaves_the_cap_in_force(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    _capped_at_standard()
    queue = _FakeQueue()
    queue.profile_answer = "standard"
    queue.confirmed_answer = "0" * 32
    poller = _slot_poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=_SlotExtractor(), ocr_slots=1
    )

    await poller.run_once()

    assert guard.snapshot().cap is Profile.ECONOMY


async def test_another_chosen_profile_lifts_the_cap(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    _capped_at_standard()
    queue = _FakeQueue()
    queue.profile_answer = "performance"
    poller = _slot_poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=_SlotExtractor(), ocr_slots=1
    )

    await poller.run_once()

    assert guard.snapshot().cap is None


def _meta_over_a_second_connection(path: Path) -> dict[str, str]:
    """The meta table as another process would see it, on a connection of its own."""
    connection = sqlite3.connect(path)
    try:
        return {str(key): str(value) for key, value in connection.execute("SELECT key, value FROM meta")}
    finally:
        connection.close()


async def test_a_multi_slot_pass_leaves_a_durable_mark_while_it_runs_and_clears_it_behind(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # D-26-16, T-26-32: the mark is visible to a second connection from inside
    # the first extraction, so it was committed before any task started.
    _standard_box()
    queue = _FakeQueue(ClaimResult(jobs=(_ocr_row(0), _ocr_row(1))))
    queue.profile_answer = "standard"
    seen: list[dict[str, str]] = []
    database = tmp_path / "state.db"
    extract = _SlotExtractor(seconds=0.02, probe=lambda: seen.append(_meta_over_a_second_connection(database)))
    poller = _slot_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=2)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert extract.most == 2
    effective = snapshot().effective.value
    assert len(seen) == 2
    for meta in seen:
        assert meta[guard.META_MULTI_SLOT_PASS] == effective
        assert meta[guard.META_MULTI_SLOT_CHOSEN] == "standard"
    final = _meta_over_a_second_connection(database)
    assert final[guard.META_MULTI_SLOT_PASS] == ""
    assert final[guard.META_MULTI_SLOT_CHOSEN] == "", "the choice leaves with the pass mark (review WR-02)"


async def test_the_pass_mark_is_written_last_and_cleared_first(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Review WR-02: the two mark writes are separate autocommit statements, so
    # the ORDER is the crash safety. CHOSEN first and PASS last makes the pass
    # mark the commit point: a death between the two writes leaves a choice
    # without a mark, which restore never reads. The old order left a fresh
    # PASS beside the CHOSEN of an earlier staffel; after the restart the guard
    # lowered with that stale choice, and the first profile read lifted the cap
    # without a token and without the admin, against D-26-04. On the way out
    # PASS goes first and CHOSEN with it, so nothing stale waits for the next
    # staffel.
    _standard_box()
    queue = _FakeQueue(ClaimResult(jobs=(_ocr_row(0), _ocr_row(1))))
    queue.profile_answer = "standard"
    calls: list[tuple[str, str]] = []
    original = store.write_meta

    def recording(key: str, value: str) -> None:
        calls.append((key, value))
        original(key, value)

    monkeypatch.setattr(store, "write_meta", recording)
    poller = _slot_poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=_SlotExtractor(seconds=0.01), ocr_slots=2
    )

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    marks = [(key, value) for key, value in calls if key in (guard.META_MULTI_SLOT_PASS, guard.META_MULTI_SLOT_CHOSEN)]
    assert marks == [
        (guard.META_MULTI_SLOT_CHOSEN, "standard"),
        (guard.META_MULTI_SLOT_PASS, snapshot().effective.value),
        (guard.META_MULTI_SLOT_PASS, ""),
        (guard.META_MULTI_SLOT_CHOSEN, ""),
    ]


async def test_a_multi_slot_pass_that_aborts_clears_its_mark_as_well(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    jobs = (_ocr_row(0), _ocr_row(1))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    poller = _slot_poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=queue,
        extract=_SlotExtractor(seconds=0.01),
        ocr_slots=2,
        bodies={7001: OSError("gateway down")},
    )

    result = await poller.run_once()

    assert result.state == ROUND_GATEWAY_UNAVAILABLE
    meta = store.read_meta()
    assert meta[guard.META_MULTI_SLOT_PASS] == ""
    assert meta[guard.META_MULTI_SLOT_CHOSEN] == ""


async def test_a_serial_pass_never_writes_the_mark(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    jobs = (_ocr_row(0), _ocr_row(1))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    poller = _slot_poller(
        store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=_SlotExtractor(seconds=0.01), ocr_slots=1
    )

    await poller.run_once()

    meta = store.read_meta()
    assert guard.META_MULTI_SLOT_PASS not in meta
    assert guard.META_MULTI_SLOT_CHOSEN not in meta


# -- a killed child under several slots (plan 26-09, D-26-16) -----------------


@dataclass(slots=True)
class _KillingExtractor:
    """Kills the child of chosen rows a given number of times, then reads them.

    Keyed by the scratch file name, job-<queue id>.part, because that is the
    one thing of the row the extraction sees. It writes down, per call, the
    limit of the gate and how many extractions were running, so a test can
    see that the solo run really ran alone.
    """

    kills: dict[int, int]
    engine: bool = False
    seconds: float = 0.05
    poller: Poller | None = None
    running: int = 0
    most: int = 0
    calls: list[tuple[int, int, int]] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def __call__(
        self,
        path: str,
        mime: str,
        size: int,
        *,
        route: Route | None = None,
        timeout_seconds: float | None = None,
    ) -> ExtractionOutcome:
        del mime, size, route, timeout_seconds
        queue_id = int(Path(path).name.removeprefix("job-").removesuffix(".part"))
        with self.lock:
            self.running += 1
            self.most = max(self.most, self.running)
            limit = self.poller._gate.limit if self.poller is not None else 0
            self.calls.append((queue_id, limit, self.running))
            doomed = self.kills.get(queue_id, 0) > 0
            if doomed:
                self.kills[queue_id] -= 1
        try:
            time.sleep(self.seconds)
            if doomed:
                raise ChildKilled(engine=self.engine)
            return ExtractionOutcome.indexed(BODY)
        finally:
            with self.lock:
                self.running -= 1

    def calls_for(self, queue_id: int) -> list[tuple[int, int, int]]:
        return [call for call in self.calls if call[0] == queue_id]


def _killing_poller(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, queue: _FakeQueue, extract: _KillingExtractor, slots: int
) -> Poller:
    poller = _slot_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, extract=extract, ocr_slots=slots)
    extract.poller = poller
    return poller


@pytest.mark.parametrize("engine", [False, True])
async def test_a_scan_killed_beside_others_runs_again_alone_and_is_indexed(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path, engine: bool
) -> None:
    # D-26-16, T-26-30: no verdict for the first kill, one report to the guard,
    # the file read again behind the barrier and indexed once.
    jobs = tuple(_ocr_row(offset) for offset in range(4))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _KillingExtractor(kills={301: 1}, engine=engine)
    poller = _killing_poller(store, writer, tmp_path, queue, extract, slots=4)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert result.indexed == 4
    assert result.failed == 0
    assert sorted(_stored_ids(index)) == [7000, 7001, 7002, 7003]
    assert guard.take_child_kills() == 1
    assert len(extract.calls_for(301)) == 2
    assert queue.acknowledged == [([300, 302, 303, 301], {})]
    row = store.file_row(7001)
    assert row is not None
    assert row["state"] == "indexed"


async def test_a_scan_that_dies_alone_as_well_ends_as_out_of_memory(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # D-26-08 case 2: dead alone means the cause. One report only, the solo run
    # does not report, and there is no third run (T-26-29).
    jobs = tuple(_ocr_row(offset) for offset in range(4))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _KillingExtractor(kills={301: 5})
    poller = _killing_poller(store, writer, tmp_path, queue, extract, slots=4)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert result.indexed == 3
    assert queue.acknowledged == [([300, 302, 303], {301: "out_of_memory"})]
    assert guard.take_child_kills() == 1
    assert len(extract.calls_for(301)) == 2


async def test_a_content_row_killed_beside_the_scans_runs_again_alone(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path
) -> None:
    jobs = (_ocr_row(0), _ocr_row(1), _job(401, 8001, mime="text/plain"))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _KillingExtractor(kills={401: 1})
    poller = _killing_poller(store, writer, tmp_path, queue, extract, slots=2)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert result.failed == 0
    assert 8001 in _stored_ids(index)
    assert guard.take_child_kills() == 1
    assert len(extract.calls_for(401)) == 2
    assert queue.acknowledged[0][1] == {}


async def test_the_solo_run_holds_the_gate_at_one(store: Store, writer: IndexBatchWriter, tmp_path: Path) -> None:
    jobs = tuple(_ocr_row(offset) for offset in range(4))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _KillingExtractor(kills={300: 1, 302: 1})
    poller = _killing_poller(store, writer, tmp_path, queue, extract, slots=4)

    await poller.run_once()

    assert extract.most >= 2, "the first round ran beside each other"
    solo = [extract.calls_for(300)[1], extract.calls_for(302)[1]]
    assert [call[1] for call in solo] == [1, 1], "gate limit one during the solo runs"
    assert [call[2] for call in solo] == [1, 1], "one extraction at a time"
    assert [call[0] for call in extract.calls[-2:]] == [300, 302], "claim order"
    assert guard.take_child_kills() == 2


# -- sidecars: macOS AppleDouble and Office lock stubs (D-29-02, D-29-05) ------


@pytest.mark.parametrize(
    ("title", "path"),
    [
        ("._IMG_1.jpg", "/u/files/Fotos/._IMG_1.jpg"),
        ("~$Bericht.docx", "/u/files/Berichte/~$Bericht.docx"),
        # No path at all: the title is the fallback for the base name.
        ("._x.pdf", ""),
    ],
)
async def test_a_sidecar_is_skipped_as_system_file_before_a_single_byte(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, title: str, path: str
) -> None:
    # #18 and #22: on the reporting instance 4,486 of 6,685 corrupt verdicts
    # were sidecars. They carry no document content, so the verdict is taken
    # before the download and it is honest about what the file is.
    job = _job(mime="application/pdf", title=title, path=path)
    queue = _FakeQueue(ClaimResult(jobs=(job,)))
    fetched: list[int] = []
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, fetched=fetched)

    result = await poller.run_once()

    assert fetched == []
    assert result.skipped == 1
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("skipped", "system_file")
    assert queue.skips == [{4711: "system_file"}]
    assert queue.acknowledged == [([91], {})]


@pytest.mark.parametrize(
    ("title", "path"),
    [
        (".hidden.txt", "Notizen/.hidden.txt"),
        ("a._b.txt", "Notizen/a._b.txt"),
        ("x~$y.txt", "Notizen/x~$y.txt"),
        ("_x.txt", "Notizen/_x.txt"),
        # A folder that looks like a sidecar does not make its files sidecars.
        ("notes.txt", "._Ordner/notes.txt"),
    ],
)
async def test_a_name_that_only_resembles_a_sidecar_is_indexed(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, index: Index, title: str, path: str
) -> None:
    # T-29-17: the base name has to START with the marker. A hidden file, a
    # marker in the middle of a name and a leading underscore are documents.
    job = _job(title=title, path=path)
    queue = _FakeQueue(ClaimResult(jobs=(job,)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    result = await poller.run_once()

    assert result.indexed == 1
    assert _stored_ids(index) == [4711]


async def test_an_indexed_sidecar_leaves_the_index_with_its_new_verdict(
    store: Store, writer: IndexBatchWriter, tmp_path: Path, index: Index
) -> None:
    # Before 1.4.0 a ._notes.txt with readable bytes was indexed and answered
    # searches with garbage. The new verdict has to take it out again, from the
    # index and from the prefilter, or the sidecar keeps being found.
    first = _job(title="notes.txt", path="Notizen/notes.txt")
    second = _job(92, title="._notes.txt", path="Notizen/._notes.txt")
    queue = _FakeQueue(ClaimResult(jobs=(first,)), ClaimResult(jobs=(second,)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()
    assert _stored_ids(index) == [4711]
    assert store.acl_rows() == 2

    await poller.run_once()

    assert _stored_ids(index) == []
    assert store.acl_rows() == 0
    row = store.file_row(4711)
    assert row is not None
    assert (row["state"], row["reason"]) == ("skipped", "system_file")


async def test_a_delete_job_of_a_sidecar_keeps_its_own_branch(
    store: Store, writer: IndexBatchWriter, tmp_path: Path
) -> None:
    # The kind branches stand before the skip and stay as they were: a delete
    # of a sidecar is still a deletion and never a system_file verdict.
    job = _job(title="._x.pdf", path="._x.pdf", kind="delete")
    queue = _FakeQueue(ClaimResult(jobs=(job,)))
    poller = _poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue)

    await poller.run_once()

    assert queue.skips == [{}]
    assert queue.acknowledged == [([91], {})]


def test_the_sidecar_check_reads_the_base_name_only() -> None:
    assert poller_module._is_sidecar("._IMG_1.jpg")
    assert poller_module._is_sidecar("~$Bericht.docx")
    assert not poller_module._is_sidecar(".hidden.txt")
    assert not poller_module._is_sidecar("a._b.txt")
    assert not poller_module._is_sidecar("x~$y.docx")
    assert not poller_module._is_sidecar("_x.txt")
    assert not poller_module._is_sidecar("")
