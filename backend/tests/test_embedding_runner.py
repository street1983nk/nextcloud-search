"""The embed runner: the second driver of the embedding track (PAR-01, PAR-04).

What is proven here, case by case, is the gate of a round (level, echo,
memory), the mutual exclusion with the indexing loop (track lock and parking),
and the abort semantics: every way out of a round without an acknowledgement
hands the rows back, and no path writes a failure verdict (SC3).

Everything runs against a real track over a real index, a real state database
and a real vector stock. The queue is a fake that hands rows out by lane, the
way the companion does once it knows the filter, and the model and the chunker
are the arithmetic stand-ins of test_embedding_track.py.
"""

from __future__ import annotations

import asyncio
import sqlite3
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import pytest
from tantivy import Index

from findling import lane, profile
from findling.config import (
    CUTTER_LOAD_BYTES,
    EMBED_ACTIVATION_BYTES,
    EMBED_CLAIM_BATCH,
    EMBED_LANE_RESERVE_BYTES,
    EMBED_WEIGHTS_LOAD_BYTES,
    FP32_EXTRA_BYTES,
)
from findling.embed.chunker import ChunkSpan
from findling.embed.engine import ENGINE_LOADED
from findling.embed.model import DIMENSIONS, EmbedOutcome
from findling.hardware import Hardware
from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter, IndexRecord
from findling.nc.client import AsyncNextcloudApp
from findling.nc.queue import (
    KIND_EMBED,
    KIND_OCR,
    LANE_EMBED,
    LANE_INDEX,
    TOPUP_IDLE,
    CallResult,
    ClaimResult,
    CompanionChoice,
    QueueJob,
    QueueStats,
)
from findling.store.repo import Store, open_store
from findling.store.vectors import VectorStore, open_vectors
from findling.worker import embedding as embedding_module
from findling.worker.embedding import (
    LANE_PARKED,
    ROUND_EMPTY,
    ROUND_PAUSED,
    ROUND_WORKED,
    EmbeddingTrack,
    EmbedRunner,
)

CONSTITUENTS = (
    (Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt").read_text(encoding="utf-8").split()
)

BODY = "Die Kuendigungsfrist betraegt drei Monate und gilt fuer alle Beschaeftigten dieses Hauses."
TITLE = "Kuendigung.txt"
CHUNK_WIDTH = 20
GIB = 1024 * 1024 * 1024

# More headroom than any round could ever ask for.
PLENTY = 64 * GIB


# -- the stand-ins ----------------------------------------------------------


def _cut(text: str) -> list[ChunkSpan]:
    """A chunker that cuts every CHUNK_WIDTH characters, offsets included."""
    if not text.strip():
        return []
    return [
        ChunkSpan(ordinal=ordinal, char_start=start, char_end=min(start + CHUNK_WIDTH, len(text)))
        for ordinal, start in enumerate(range(0, len(text), CHUNK_WIDTH))
    ]


@dataclass(slots=True)
class _FakeModel:
    """The engine, replaced by arithmetic."""

    calls: list[list[str]] = field(default_factory=list)

    def embed_passages(self, texts: Sequence[str]) -> EmbedOutcome:
        self.calls.append(list(texts))
        return EmbedOutcome.ready([[(index + 1) / 1000] * DIMENSIONS for index in range(len(texts))])


def _in_lane(job: QueueJob, wanted: str | None) -> bool:
    if wanted == LANE_EMBED:
        return job.kind == KIND_EMBED
    if wanted == LANE_INDEX:
        return job.kind != KIND_EMBED
    return True


class _LaneQueue:
    """A queue that hands rows out by lane, as the companion does since plan 25-05.

    ``echo`` False is a companion from before the filter: it ignores the lane,
    hands out rows of every kind and answers without the echo. Unlocked rows go
    back into the pool, acknowledged ones are gone.
    """

    def __init__(self, *jobs: QueueJob, echo: bool = True) -> None:
        self.pool: dict[int, QueueJob] = {job.queue_id: job for job in jobs}
        self.known: dict[int, QueueJob] = dict(self.pool)
        self.echo = echo
        self.unavailable = False
        self.profile_answer: str | None = None
        self.lanes: list[str | None] = []
        self.acknowledged: list[tuple[list[int], dict[int, str]]] = []
        self.unlocked: list[list[int]] = []
        self.requeues: list[tuple[list[int], str]] = []

    def add(self, *jobs: QueueJob) -> None:
        for job in jobs:
            self.pool[job.queue_id] = job
            self.known[job.queue_id] = job

    async def companion_choice(self) -> CompanionChoice:
        return CompanionChoice(profile=self.profile_answer, precision=None)

    async def claim(self, *, limit: int, max_bytes: int, lane: str | None = None) -> ClaimResult:
        del max_bytes
        self.lanes.append(lane)
        if self.unavailable:
            return ClaimResult(unavailable=True)
        wanted = lane if self.echo else None
        picked = [job for job in self.pool.values() if _in_lane(job, wanted)][:limit]
        for job in picked:
            del self.pool[job.queue_id]
        return ClaimResult(jobs=tuple(picked), lane_honored=self.echo)

    async def acknowledge(self, done: Any, failed: Any, skipped: Any = None) -> CallResult:
        del skipped
        self.acknowledged.append((list(done), dict(failed)))
        return CallResult(ok=True, count=len(done) + len(failed))

    async def unlock(self, ids: Any) -> CallResult:
        self.unlocked.append(list(ids))
        for queue_id in ids:
            self.pool[queue_id] = self.known[queue_id]
        return CallResult(ok=True, count=len(ids))

    async def requeue(self, file_ids: Any, *, kind: str) -> CallResult:
        self.requeues.append((list(file_ids), kind))
        return CallResult(ok=True, count=len(list(file_ids)))

    async def top_up(self) -> str:
        return TOPUP_IDLE

    async def stats(self) -> QueueStats:
        return QueueStats()


def _job(queue_id: int, file_id: int, *, kind: str = KIND_EMBED, mime: str = "text/plain") -> QueueJob:
    return QueueJob(
        queue_id=queue_id,
        file_id=file_id,
        storage_id=3,
        root_id=2,
        path=f"Vertraege/{TITLE}",
        title=TITLE,
        mime=mime,
        size=len(BODY),
        mtime=1_756_600_000,
        etag="5d41402abc4b2a76b9719d911017c592",
        kind=kind,
        user_ids=("alice",),
        fetch_as="alice",
        is_update=False,
    )


def _box(cores: float, memory: int) -> Hardware:
    return Hardware(
        cpu_count=max(1, int(cores)),
        cpu_quota=None,
        cores=cores,
        memory_limit_bytes=None,
        memory_available_bytes=memory,
        memory_total_bytes=memory,
        architecture="x86_64",
        cgroup="none",
    )


def _standard() -> None:
    """A box of four cores and 16 GiB with Standard chosen (Pitfall 11)."""
    profile.note_hardware(_box(4, 16 * GIB))
    profile.note_chosen("standard")


def _performance() -> None:
    profile.note_hardware(_box(16, 64 * GIB))
    profile.note_chosen("performance")


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
def track(store: Store, vectors: VectorStore, writer: IndexBatchWriter) -> EmbeddingTrack:
    return EmbeddingTrack(
        vectors=vectors,
        chunker=_cut,
        model=_FakeModel(),
        store=store,
        index=writer.index,
        index_dir=writer.directory,
    )


def _index_bodies(writer: IndexBatchWriter, *file_ids: int) -> None:
    for file_id in file_ids:
        writer.add(
            IndexRecord(
                file_id=file_id,
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


def _runner(
    track: EmbeddingTrack,
    queue: _LaneQueue,
    *,
    headroom: int | None = PLENTY,
    engine: str = ENGINE_LOADED,
    tick: float = 0.0,
    clock: Any = None,
) -> EmbedRunner:
    extra: dict[str, Any] = {} if clock is None else {"clock": clock}
    return EmbedRunner(
        track=track,
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        queue_factory=lambda nc: cast("Any", queue),
        tick=tick,
        headroom=lambda: headroom,
        engine=lambda: engine,
        **extra,
    )


# -- the gate ---------------------------------------------------------------


async def test_economy_parks_without_a_claim(track: EmbeddingTrack) -> None:
    # No hardware noted and nothing chosen: Economy, today's container. The
    # runner never asks the queue anything (PROF-02).
    lane.note_echo(True)
    queue = _LaneQueue(_job(1, 11))
    runner = _runner(track, queue)

    assert await runner.run_once() == LANE_PARKED
    assert queue.lanes == []
    assert lane.snapshot().mode == lane.MODE_INLINE
    assert lane.snapshot().reason == lane.REASON_ECONOMY
    assert runner.parked.is_set()


async def test_economy_chosen_on_a_big_box_parks_as_well(track: EmbeddingTrack) -> None:
    profile.note_hardware(_box(16, 64 * GIB))
    profile.note_chosen("economy")
    lane.note_echo(True)
    queue = _LaneQueue(_job(1, 11))

    assert await _runner(track, queue).run_once() == LANE_PARKED
    assert queue.lanes == []
    assert lane.snapshot().reason == lane.REASON_ECONOMY


async def test_standard_without_a_seen_echo_parks(track: EmbeddingTrack) -> None:
    _standard()
    queue = _LaneQueue(_job(1, 11))

    assert await _runner(track, queue).run_once() == LANE_PARKED
    assert queue.lanes == []
    assert lane.snapshot().reason == lane.REASON_OLD_COMPANION


@pytest.mark.parametrize("headroom", [None, 0, 100 * 1024 * 1024])
async def test_standard_without_memory_parks_waiting_for_memory(track: EmbeddingTrack, headroom: int | None) -> None:
    # T5, D-25-11: an unreadable headroom is never admitted, a small one neither.
    _standard()
    lane.note_echo(True)
    queue = _LaneQueue(_job(1, 11))

    assert await _runner(track, queue, headroom=headroom).run_once() == LANE_PARKED
    assert queue.lanes == []
    assert lane.snapshot().mode == lane.MODE_INLINE
    assert lane.snapshot().reason == lane.REASON_MEMORY


async def test_a_memory_refusal_is_not_read_again_before_a_full_tick(track: EmbeddingTrack) -> None:
    # Against flapping: after a no, the headroom is read again only once a
    # whole tick has passed.
    _standard()
    lane.note_echo(True)
    now = [100.0]
    reads: list[int] = []
    answers = [0, PLENTY, PLENTY]

    def headroom() -> int:
        reads.append(1)
        return answers[len(reads) - 1]

    queue = _LaneQueue()
    runner = EmbedRunner(
        track=track,
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        queue_factory=lambda nc: cast("Any", queue),
        tick=15.0,
        headroom=headroom,
        engine=lambda: ENGINE_LOADED,
        clock=lambda: now[0],
    )

    assert await runner.run_once() == LANE_PARKED
    now[0] += 5.0
    assert await runner.run_once() == LANE_PARKED
    assert len(reads) == 1
    now[0] += 15.0
    assert await runner.run_once() == ROUND_EMPTY
    assert len(reads) == 2


@pytest.mark.parametrize(
    ("engine", "built", "weights", "need"),
    [
        (ENGINE_LOADED, True, "int8", EMBED_ACTIVATION_BYTES + EMBED_LANE_RESERVE_BYTES),
        ("cold", True, "int8", EMBED_ACTIVATION_BYTES + EMBED_LANE_RESERVE_BYTES + EMBED_WEIGHTS_LOAD_BYTES),
        (
            "cold",
            True,
            "fp32",
            EMBED_ACTIVATION_BYTES + EMBED_LANE_RESERVE_BYTES + EMBED_WEIGHTS_LOAD_BYTES + FP32_EXTRA_BYTES,
        ),
        (ENGINE_LOADED, False, "int8", EMBED_ACTIVATION_BYTES + EMBED_LANE_RESERVE_BYTES + CUTTER_LOAD_BYTES),
    ],
)
async def test_the_live_need_counts_the_load_costs(
    store: Store, vectors: VectorStore, writer: IndexBatchWriter, engine: str, built: bool, weights: str, need: int
) -> None:
    # One byte short is a no, exactly the need is a yes.
    _standard()
    profile.note_weights(weights)
    lane.note_echo(True)
    track = EmbeddingTrack(
        vectors=vectors,
        chunker=_cut if built else None,
        model=_FakeModel() if built else None,
        store=store,
        index=writer.index,
        index_dir=writer.directory,
    )
    assert profile.snapshot().embed_lane_fits

    short = _LaneQueue()
    assert await _runner(track, short, headroom=need - 1, engine=engine).run_once() == LANE_PARKED
    assert short.lanes == []

    enough = _LaneQueue()
    assert await _runner(track, enough, headroom=need, engine=engine).run_once() == ROUND_EMPTY
    assert enough.lanes == [LANE_EMBED]


# -- an open round ----------------------------------------------------------


async def test_an_open_round_claims_the_embed_lane_and_acknowledges(
    track: EmbeddingTrack, writer: IndexBatchWriter, vectors: VectorStore
) -> None:
    _standard()
    lane.note_echo(True)
    _index_bodies(writer, 11, 12)
    queue = _LaneQueue(_job(1, 11), _job(2, 12))
    runner = _runner(track, queue)

    assert await runner.run_once() == ROUND_WORKED
    assert queue.lanes == [LANE_EMBED]
    assert queue.acknowledged == [([1, 2], {})]
    assert queue.unlocked == []
    assert vectors.chunks_of([11])
    assert vectors.chunks_of([12])
    assert lane.snapshot().mode == lane.MODE_PARALLEL
    assert lane.snapshot().reason == lane.REASON_NONE
    assert not runner.busy
    assert runner.parked.is_set()


async def test_the_claim_is_one_batch_of_the_embed_track(track: EmbeddingTrack, writer: IndexBatchWriter) -> None:
    _standard()
    lane.note_echo(True)
    file_ids = list(range(100, 100 + EMBED_CLAIM_BATCH + 3))
    _index_bodies(writer, *file_ids)
    queue = _LaneQueue(*(_job(index + 1, file_id) for index, file_id in enumerate(file_ids)))

    assert await _runner(track, queue).run_once() == ROUND_WORKED
    assert len(queue.acknowledged[0][0]) == EMBED_CLAIM_BATCH


async def test_an_answer_without_the_echo_hands_everything_back_for_good(track: EmbeddingTrack) -> None:
    # T8: the companion ignored the lane of this very request.
    _standard()
    lane.note_echo(True)
    queue = _LaneQueue(_job(1, 11), _job(2, 12, kind=KIND_OCR, mime="application/pdf"), echo=False)
    runner = _runner(track, queue)

    assert await runner.run_once() == LANE_PARKED
    assert queue.unlocked == [[1, 2]]
    assert queue.acknowledged == []
    assert not runner.busy
    assert lane.snapshot().supported is False
    assert lane.snapshot().reason == lane.REASON_OLD_COMPANION

    # Sticky for the life of the process: a later echo of the indexing loop
    # does not open the gate again, and no further claim leaves the runner.
    lane.note_echo(True)
    assert lane.snapshot().supported is False
    assert await runner.run_once() == LANE_PARKED
    assert queue.lanes == [LANE_EMBED]


@pytest.mark.parametrize("failure", ["sqlite", "disk"])
async def test_a_store_error_or_the_disk_floor_hands_every_row_back_without_a_verdict(
    track: EmbeddingTrack, writer: IndexBatchWriter, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    # T7, second half, and Pitfall 3: nothing is judged, the rows go back with
    # their delivery refunded, and the runner backs off.
    _standard()
    lane.note_echo(True)
    _index_bodies(writer, 11, 12, 13)
    queue = _LaneQueue(_job(1, 11), _job(2, 12), _job(3, 13))
    runner = _runner(track, queue, tick=15.0)
    real = track.embed_row
    rows: list[int] = []

    async def embed_row(job: QueueJob, done: list[int]) -> str:
        rows.append(job.queue_id)
        if len(rows) == 2:
            if failure == "sqlite":
                raise sqlite3.OperationalError("database is locked")
            monkeypatch.setattr(embedding_module, "disk_is_tight", lambda *args: True)
        return await real(job, done)

    monkeypatch.setattr(track, "embed_row", embed_row)

    assert await runner.run_once() == ROUND_PAUSED
    assert queue.unlocked == [[1, 2, 3]]
    assert queue.acknowledged == []
    assert runner.cooldown == 15.0
    assert not runner.busy


async def test_economy_between_two_rows_ends_the_round_after_the_row_in_work(
    track: EmbeddingTrack, writer: IndexBatchWriter, monkeypatch: pytest.MonkeyPatch
) -> None:
    # T4, the runner side: the rows not reached go back unjudged.
    _standard()
    lane.note_echo(True)
    _index_bodies(writer, 11, 12, 13)
    queue = _LaneQueue(_job(1, 11), _job(2, 12), _job(3, 13))
    runner = _runner(track, queue)
    real = track.embed_row

    async def embed_row(job: QueueJob, done: list[int]) -> str:
        written = await real(job, done)
        profile.note_chosen("economy")
        return written

    monkeypatch.setattr(track, "embed_row", embed_row)

    assert await runner.run_once() == LANE_PARKED
    assert queue.acknowledged == [([1], {})]
    assert queue.unlocked == [[2, 3]]
    assert lane.snapshot().reason == lane.REASON_ECONOMY
    assert runner.parked.is_set()


async def test_an_empty_answer_runs_the_mark_step_under_the_track_lock(
    track: EmbeddingTrack, monkeypatch: pytest.MonkeyPatch
) -> None:
    _standard()
    lane.note_echo(True)
    queue = _LaneQueue()
    seen: list[bool] = []

    async def step(asked: Any) -> None:
        assert asked is queue
        seen.append(track.lock.locked())

    monkeypatch.setattr(track, "keep_the_vector_stock_in_step", step)

    assert await _runner(track, queue).run_once() == ROUND_EMPTY
    assert seen == [True]


async def test_performance_embeds_one_row_at_a_time(track: EmbeddingTrack, monkeypatch: pytest.MonkeyPatch) -> None:
    # D-25-12: one runner in Standard and in Performance, never two rows at once,
    # even with two rounds started together; the profile value of two slots
    # stays unwired.
    _performance()
    lane.note_echo(True)
    assert profile.snapshot().effective is profile.Profile.PERFORMANCE
    assert profile.snapshot().resolution.values.embed_slots == 2
    queue = _LaneQueue(*(_job(index, 100 + index) for index in range(1, 7)))
    runner = _runner(track, queue)
    in_work = [0]
    peak = [0]

    async def embed_row(job: QueueJob, done: list[int]) -> str:
        in_work[0] += 1
        peak[0] = max(peak[0], in_work[0])
        await asyncio.sleep(0.01)
        in_work[0] -= 1
        done.append(job.queue_id)
        return embedding_module.EMBED_WRITTEN

    monkeypatch.setattr(track, "embed_row", embed_row)

    await asyncio.gather(runner.run_once(), runner.run_once())
    assert peak[0] == 1
    assert sorted(queue_id for batch, _ in queue.acknowledged for queue_id in batch) == [1, 2, 3, 4, 5, 6]


async def test_an_abort_in_the_middle_of_a_round_loses_no_row_and_doubles_no_chunk(
    track: EmbeddingTrack, writer: IndexBatchWriter, vectors: VectorStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    # T6: a cancel after replace_chunks of the first row and before the
    # acknowledgement. unlock_held gives back exactly the held rows, none of
    # which was acknowledged, and embedding the first row again yields one
    # chunk set and not two.
    _standard()
    lane.note_echo(True)
    _index_bodies(writer, 11, 12, 13)
    jobs = (_job(1, 11), _job(2, 12), _job(3, 13))
    queue = _LaneQueue(*jobs)
    runner = _runner(track, queue)
    real = track.embed_row
    second_started = asyncio.Event()

    async def embed_row(job: QueueJob, done: list[int]) -> str:
        if job.queue_id == 2:
            second_started.set()
            await asyncio.Event().wait()
        return await real(job, done)

    monkeypatch.setattr(track, "embed_row", embed_row)

    task = asyncio.ensure_future(runner.run_once())
    await asyncio.wait_for(second_started.wait(), timeout=5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert runner.parked.is_set()
    assert runner.busy
    assert await runner.unlock_held() == 3
    assert queue.unlocked == [[1, 2, 3]]
    assert queue.acknowledged == []
    assert not runner.busy

    chunks = len(_cut(BODY))
    assert len(vectors.chunks_of([11])[11]) == chunks
    done: list[int] = []
    await real(jobs[0], done)
    assert len(vectors.chunks_of([11])[11]) == chunks
    assert done == [1]


async def test_the_loop_hands_the_rows_back_before_it_logs_an_unexpected_failure(
    track: EmbeddingTrack, writer: IndexBatchWriter, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _standard()
    lane.note_echo(True)
    _index_bodies(writer, 11)
    queue = _LaneQueue(_job(1, 11))
    runner = _runner(track, queue, tick=0.01)
    stop = asyncio.Event()

    async def embed_row(job: QueueJob, done: list[int]) -> str:
        del job, done
        raise ValueError(TITLE)

    async def unlock(ids: Any) -> CallResult:
        queue.unlocked.append(list(ids))
        stop.set()
        return CallResult(ok=True, count=len(ids))

    monkeypatch.setattr(track, "embed_row", embed_row)
    monkeypatch.setattr(queue, "unlock", unlock)
    runner.arm()

    await asyncio.wait_for(runner.run(stop), timeout=5)

    assert queue.unlocked == [[1]]
    assert queue.acknowledged == []
    assert "unexpected ValueError" in caplog.text
    assert TITLE not in caplog.text


async def test_stand_down_waits_for_the_round_and_hands_the_rows_back(track: EmbeddingTrack) -> None:
    runner = _runner(track, _LaneQueue())
    assert await runner.stand_down(budget=1.0)
    assert await runner.unlock_held() == 0
    await runner.aclose()
