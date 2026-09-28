"""The precision of the embedding model in the running track (MOD-02, plan 25-11).

Every building block exists on its own: the engine holder with its swap, the
weights file with its digest, the precision state machine and the track that
owns the mark. This file holds them together where they meet, the mark step of
:class:`~findling.worker.embedding.EmbeddingTrack`, against a real state
database and a real vector stock in ``tmp_path``.

The stand-ins are the ones the rest of the suite uses for the same reason: a
chunker and a passage model that answer arithmetic, and a fetch that hands over
a few bytes whose digest the case patched in, instead of 470 MB from GitHub.
"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Awaitable, Callable, Iterator, Sequence
from pathlib import Path
from typing import IO, Any, cast

import pytest
from tantivy import Index

from findling import precision, profile
from findling.config import settings
from findling.embed import weights as weights_module
from findling.embed.chunker import ChunkSpan
from findling.embed.engine import engine_precision
from findling.embed.engine import reset as engine_reset
from findling.embed.model import DIMENSIONS, EmbedOutcome
from findling.extract.errors import ExtractionOutcome
from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter, IndexRecord
from findling.nc.client import AsyncNextcloudApp
from findling.nc.queue import (
    KIND_EMBED,
    TOPUP_IDLE,
    CallResult,
    ClaimResult,
    CompanionChoice,
    QueueJob,
    QueueStats,
)
from findling.precision import Precision
from findling.store.repo import EMBEDDING_MARK, FileMeta, Store, open_store
from findling.store.vectors import (
    EMBEDDING_MODEL,
    WEIGHTS_FP32,
    WEIGHTS_INT8,
    Chunk,
    VectorStore,
    embedding_mark,
    open_vectors,
)
from findling.worker import embedding as embedding_module
from findling.worker.embedding import EmbeddingTrack
from findling.worker.poller import Poller

CONSTITUENTS = (
    (Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt").read_text(encoding="utf-8").split()
)

# The stand-in for the fp32 weights: a few bytes whose digest and length the
# cases patch into embed/weights.py, so the real verification and the real
# download path run end to end without 470 MB on the machine.
PAYLOAD = b"fp32 weights, as far as this suite is concerned" * 64
PAYLOAD_SHA256 = hashlib.sha256(PAYLOAD).hexdigest()


def _mark(weights: str) -> str:
    return embedding_mark(EMBEDDING_MODEL, tokens=settings().embed_token_cap, weights=weights)


def _cut(text: str) -> list[ChunkSpan]:
    return [ChunkSpan(ordinal=0, char_start=0, char_end=len(text))] if text.strip() else []


class _FakeModel:
    """A passage model that answers arithmetic."""

    def embed_passages(self, texts: Sequence[str]) -> EmbedOutcome:
        return EmbedOutcome.ready([[0.001] * DIMENSIONS for _ in texts])


class _FakeQueue:
    """The queue calls the mark step and one pass of the poller make."""

    def __init__(self) -> None:
        self.requeues: list[tuple[list[int], str]] = []
        self.precision_answer: str | None = None

    async def companion_choice(self) -> CompanionChoice:
        return CompanionChoice(profile=None, precision=self.precision_answer)

    async def claim(self, *, limit: int, max_bytes: int, lane: str | None = None) -> ClaimResult:
        del limit, max_bytes, lane
        return ClaimResult()

    async def top_up(self) -> str:
        return TOPUP_IDLE

    async def acknowledge(self, done: Any, failed: Any, skipped: Any = None) -> CallResult:
        del done, failed, skipped
        return CallResult(ok=True)

    async def unlock(self, ids: Any) -> CallResult:
        return CallResult(ok=True, count=len(ids))

    async def requeue(self, file_ids: Any, *, kind: str) -> CallResult:
        self.requeues.append((list(file_ids), kind))
        return CallResult(ok=True, count=len(list(file_ids)))

    async def stats(self) -> QueueStats:
        return QueueStats()


class _Fetch:
    """The release fetch, answered from memory and counted.

    ``gate`` holds the transfer until the case lets it go, which is how a case
    looks at the state while the download is running. ``fails`` makes it raise
    the way an unreachable host does.
    """

    def __init__(self, *, fails: bool = False) -> None:
        self.calls = 0
        self.fails = fails
        self.gate = asyncio.Event()
        self.gate.set()
        self.entered = asyncio.Event()

    async def __call__(self, url: str, write: Callable[[bytes], Awaitable[None]], *, cap: int) -> None:
        del url, cap
        self.calls += 1
        self.entered.set()
        await self.gate.wait()
        if self.fails:
            raise OSError("no route to the release host")
        await write(PAYLOAD)


# -- fixtures ---------------------------------------------------------------


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A volume of its own, a free space floor of one byte, and the small stand-in weights."""
    monkeypatch.setenv("APP_PERSISTENT_STORAGE", str(tmp_path))
    monkeypatch.setenv("FINDLING_MIN_FREE_BYTES", "1")
    monkeypatch.setattr(weights_module, "FP32_SHA256", PAYLOAD_SHA256)
    monkeypatch.setattr(weights_module, "FP32_BYTES", len(PAYLOAD))
    settings.cache_clear()
    engine_reset()
    weights_module.forget_verdicts()
    yield tmp_path
    engine_reset()
    weights_module.forget_verdicts()
    settings.cache_clear()


@pytest.fixture
def store(home: Path) -> Iterator[Store]:
    opened = open_store(home / "state.db")
    yield opened
    opened.close()


@pytest.fixture
def vectors(home: Path) -> Iterator[VectorStore]:
    stock = open_vectors(home / "vectors.db")
    yield stock
    stock.close()


@pytest.fixture
def fetch(monkeypatch: pytest.MonkeyPatch) -> _Fetch:
    fake = _Fetch()
    monkeypatch.setattr(embedding_module, "fetch_release_asset", fake)
    return fake


def _place_the_file(home: Path, payload: bytes = PAYLOAD) -> Path:
    """Put fp32 weights into the volume by hand, the sideload of D-25-06."""
    target = weights_module.fp32_weights_path(settings().models_dir)
    assert target.is_relative_to(home)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return target


def _judged(store: Store, file_id: int) -> None:
    store.record(
        file_id,
        FileMeta(
            storage_id=3,
            root_id=2,
            path=f"Akten/{file_id}.txt",
            title=f"{file_id}.txt",
            mime="text/plain",
            size=10,
            mtime=1_756_600_000,
        ),
        "indexed",
        content_hash="5d41402abc4b2a76b9719d911017c592",
        text_chars=10,
    )


def _fill(stock: VectorStore, file_id: int) -> None:
    stock.replace_chunks(file_id, [Chunk(ordinal=0, char_start=0, char_end=10, embedding=bytes(DIMENSIONS))])


def _stocked(store: Store, vectors: VectorStore, mark: str, file_ids: Sequence[int] = (4711, 4712)) -> None:
    """A whole stock under a mark, the state of an instance that caught up."""
    for file_id in file_ids:
        _judged(store, file_id)
        _fill(vectors, file_id)
    store.write_meta(EMBEDDING_MARK, mark)


def _track(store: Store, vectors: VectorStore) -> EmbeddingTrack:
    track = EmbeddingTrack(vectors=vectors, chunker=_cut, model=_FakeModel(), store=store)
    track.open(wire=False)
    return track


def _count_calls(monkeypatch: pytest.MonkeyPatch, name: str) -> list[int]:
    """Replace one name of the track module by a wrapper that counts its calls."""
    calls: list[int] = []
    real = getattr(embedding_module, name)

    def counted(*args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(embedding_module, name, counted)
    return calls


def _count_forget_all(monkeypatch: pytest.MonkeyPatch, vectors: VectorStore) -> list[int]:
    calls: list[int] = []
    real = vectors.forget_all

    def counted() -> None:
        calls.append(1)
        real()

    monkeypatch.setattr(vectors, "forget_all", counted)
    return calls


async def _step(track: EmbeddingTrack, queue: _FakeQueue | None = None) -> None:
    async with track.lock:
        await track.keep_the_vector_stock_in_step(cast("Any", queue or _FakeQueue()))


async def _procurement_ended(track: EmbeddingTrack) -> None:
    task = track._procurement
    assert task is not None
    await task


async def _fetch_reached(fetch: _Fetch) -> None:
    """Wait until the task beside the round has reached the fetch itself."""
    async with asyncio.timeout(5):
        await fetch.entered.wait()


# -- the start state (D-25-14, Pitfall 6) -----------------------------------


async def test_a_stored_fp32_mark_and_a_verified_file_start_on_fp32_without_emptying(
    home: Path, store: Store, vectors: VectorStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The profile route did not answer, so nothing was chosen in this process.
    # A start that read that as int8 would empty a stock built with fp32.
    _place_the_file(home)
    _stocked(store, vectors, _mark(WEIGHTS_FP32))
    forgotten = _count_forget_all(monkeypatch, vectors)
    swaps = _count_calls(monkeypatch, "swap_engine")
    track = _track(store, vectors)

    await _step(track)

    assert precision.snapshot().chosen is None
    assert precision.snapshot().active is Precision.FP32
    assert engine_precision() == WEIGHTS_FP32
    assert swaps == [1]
    assert forgotten == []
    assert store.read_meta()[EMBEDDING_MARK] == _mark(WEIGHTS_FP32)
    assert vectors.document_count() == 2


async def test_a_stored_fp32_mark_without_the_file_starts_on_int8(
    home: Path, store: Store, vectors: VectorStore
) -> None:
    # The file is gone, so the stock cannot be continued; int8 is the way back.
    del home
    _stocked(store, vectors, _mark(WEIGHTS_FP32))
    track = _track(store, vectors)

    await _step(track)

    assert precision.snapshot().active is Precision.INT8
    assert engine_precision() == WEIGHTS_INT8
    assert store.read_meta()[EMBEDDING_MARK] == _mark(WEIGHTS_INT8)


async def test_the_start_state_is_settled_before_the_first_row_is_embedded(
    home: Path, store: Store, vectors: VectorStore, tmp_path: Path
) -> None:
    # A row embedded with the int8 of the image under an fp32 mark would be the
    # mixed stock of T-24-02, and nothing afterwards could tell it apart.
    _place_the_file(home)
    _stocked(store, vectors, _mark(WEIGHTS_FP32))
    index = open_index(tmp_path / "index", CONSTITUENTS)
    track = EmbeddingTrack(vectors=vectors, chunker=_cut, model=_FakeModel(), store=store, index=index)
    track.open(wire=False)
    seen: list[str] = []

    class _Watching(_FakeModel):
        def embed_passages(self, texts: Sequence[str]) -> EmbedOutcome:
            seen.append(engine_precision())
            return super().embed_passages(texts)

    track._model = _Watching()
    _write_one_document(index, tmp_path / "index")

    async with track.lock:
        await track.embed_row(_job(), [])

    assert precision.snapshot().active is Precision.FP32
    assert seen == [WEIGHTS_FP32]


# -- no cost without a wish (MOD-02) ------------------------------------------


async def test_without_a_wish_for_fp32_nothing_is_hashed_fetched_or_swapped(
    home: Path, store: Store, vectors: VectorStore, fetch: _Fetch, monkeypatch: pytest.MonkeyPatch
) -> None:
    del home
    _stocked(store, vectors, _mark(WEIGHTS_INT8))
    verified = _count_calls(monkeypatch, "fp32_verified")
    procured = _count_calls(monkeypatch, "procure_fp32")
    swaps = _count_calls(monkeypatch, "swap_engine")
    hashes = weights_module.hash_count()
    profile.note_chosen("performance")
    precision.note_chosen_precision("int8")
    track = _track(store, vectors)

    for _ in range(3):
        await _step(track)

    assert (verified, procured, swaps) == ([], [], [])
    assert fetch.calls == 0
    assert weights_module.hash_count() == hashes
    assert track._procurement is None
    assert precision.snapshot().active is Precision.INT8


# -- the procurement (D-25-04, D-25-05) ---------------------------------------


async def test_a_change_to_fp32_starts_exactly_one_procurement_beside_the_round(
    home: Path, store: Store, vectors: VectorStore, fetch: _Fetch
) -> None:
    _stocked(store, vectors, _mark(WEIGHTS_INT8))
    profile.note_chosen("standard")
    precision.note_chosen_precision("int8")
    track = _track(store, vectors)
    await _step(track)

    precision.note_chosen_precision("fp32")
    fetch.gate.clear()
    await _step(track)
    # The round came back while the download waits at its gate.
    await _fetch_reached(fetch)
    assert fetch.calls == 1
    assert precision.snapshot().verdict == precision.VERDICT_DOWNLOADING
    await _step(track)
    await _step(track)
    assert fetch.calls == 1, "never a second procurement while one runs"

    fetch.gate.set()
    await _procurement_ended(track)

    assert precision.snapshot().procuring is False
    assert weights_module.fp32_verified(settings().models_dir)
    assert weights_module.fp32_weights_path(settings().models_dir).is_relative_to(home)


async def test_a_failed_procurement_keeps_int8_and_is_not_retried(
    home: Path, store: Store, vectors: VectorStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    del home
    failing = _Fetch(fails=True)
    monkeypatch.setattr(embedding_module, "fetch_release_asset", failing)
    _stocked(store, vectors, _mark(WEIGHTS_INT8))
    forgotten = _count_forget_all(monkeypatch, vectors)
    profile.note_chosen("standard")
    precision.note_chosen_precision("int8")
    track = _track(store, vectors)
    await _step(track)

    precision.note_chosen_precision("fp32")
    await _step(track)
    await _procurement_ended(track)
    for _ in range(3):
        await _step(track)

    assert failing.calls == 1
    assert precision.snapshot().active is Precision.INT8
    assert precision.snapshot().verdict == precision.VERDICT_UNAVAILABLE
    assert store.read_meta()[EMBEDDING_MARK] == _mark(WEIGHTS_INT8)
    assert forgotten == []
    assert not weights_module.fp32_weights_path(settings().models_dir).exists()


async def test_a_wish_for_fp32_under_economy_fetches_nothing(
    home: Path, store: Store, vectors: VectorStore, fetch: _Fetch
) -> None:
    del home
    _stocked(store, vectors, _mark(WEIGHTS_INT8))
    profile.note_chosen("economy")
    precision.note_chosen_precision("int8")
    track = _track(store, vectors)
    await _step(track)

    precision.note_chosen_precision("fp32")
    await _step(track)

    assert track._procurement is None
    assert fetch.calls == 0
    assert precision.snapshot().verdict == precision.VERDICT_NOT_IN_ECONOMY


async def test_closing_the_track_cancels_a_running_procurement(
    home: Path, store: Store, vectors: VectorStore, fetch: _Fetch
) -> None:
    _stocked(store, vectors, _mark(WEIGHTS_INT8))
    profile.note_chosen("standard")
    precision.note_chosen_precision("int8")
    track = _track(store, vectors)
    await _step(track)
    precision.note_chosen_precision("fp32")
    fetch.gate.clear()
    await _step(track)
    await _fetch_reached(fetch)
    task = track._procurement
    assert task is not None

    await track.aclose()

    assert task.done()
    assert precision.snapshot().procuring is False
    part = weights_module.fp32_weights_path(settings().models_dir).with_suffix(".onnx.part")
    assert part.is_relative_to(home)
    assert not part.exists()


# -- the poller reads the key every round (D-25-02) ---------------------------


async def test_the_poller_hands_the_precision_of_every_round_to_the_state(
    home: Path, store: Store, vectors: VectorStore, tmp_path: Path
) -> None:
    del home
    index = open_index(tmp_path / "index", CONSTITUENTS)
    writer = IndexBatchWriter(index, directory=tmp_path / "index", min_free_bytes=0)
    queue = _FakeQueue()
    poller = _poller(store=store, writer=writer, vectors=vectors, tmp_path=tmp_path, queue=queue)
    try:
        queue.precision_answer = "int8"
        await poller.run_once()
        assert precision.snapshot().chosen is Precision.INT8

        queue.precision_answer = "fp32"
        await poller.run_once()
        assert precision.snapshot().chosen is Precision.FP32

        # A round without an answer changes nothing (D-24-02).
        queue.precision_answer = None
        await poller.run_once()
        assert precision.snapshot().chosen is Precision.FP32
    finally:
        writer.close()


# -- helpers for the row and the poller ---------------------------------------


def _write_one_document(index: Index, directory: Path) -> None:
    writer = IndexBatchWriter(index, directory=directory, min_free_bytes=0)
    try:
        writer.add(
            IndexRecord(
                file_id=4711,
                storage_id=3,
                name="Akte.txt",
                title="Akte.txt",
                path="Akten/Akte.txt",
                ext="txt",
                body="Die Kuendigungsfrist betraegt drei Monate.",
                mtime=1_756_600_000,
            )
        )
        writer.flush()
    finally:
        writer.close()
    index.reload()


def _job() -> QueueJob:
    return QueueJob(
        queue_id=91,
        file_id=4711,
        storage_id=3,
        root_id=2,
        path="Akten/Akte.txt",
        title="Akte.txt",
        mime="text/plain",
        size=10,
        mtime=1_756_600_000,
        etag="5d41402abc4b2a76b9719d911017c592",
        kind=KIND_EMBED,
        user_ids=("alice",),
        fetch_as="alice",
        is_update=False,
    )


class _FakeGatewayClient:
    async def aclose(self) -> None:
        return None


async def _no_fetch(nc: AsyncNextcloudApp, file_id: int, user_id: str, fp: IO[bytes], *, client: Any = None) -> None:
    del nc, file_id, user_id, fp, client


def _no_extract(path: str, mime: str, size: int, **_: Any) -> ExtractionOutcome:
    del path, mime, size
    raise AssertionError("no file is extracted in these cases")


def _poller(
    *, store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path, queue: _FakeQueue
) -> Poller:
    return Poller(
        store=store,
        writer=writer,
        tmp_dir=tmp_path / "tmp",
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        gateway_factory=lambda: cast("Any", _FakeGatewayClient()),
        queue_factory=lambda nc: cast("Any", queue),
        fetch=cast("Any", _no_fetch),
        extract=cast("Any", _no_extract),
        vectors=vectors,
        chunker=_cut,
        model=_FakeModel(),
    )
