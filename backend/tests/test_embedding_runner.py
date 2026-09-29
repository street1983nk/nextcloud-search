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
import os
import sqlite3
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator, Sequence
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
from findling.extract.errors import ExtractionOutcome
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
    ROUND_GATEWAY_UNAVAILABLE,
    ROUND_PAUSED,
    ROUND_WORKED,
    EmbeddingTrack,
    EmbedRunner,
)
from findling.worker.poller import Poller

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


def _counting_rows(track: EmbeddingTrack, monkeypatch: pytest.MonkeyPatch, pause: float) -> list[int]:
    """Replace embed_row by one that sleeps; answer [rows in work now, the peak]."""
    counts = [0, 0]

    async def embed_row(job: QueueJob, done: list[int]) -> str:
        counts[0] += 1
        counts[1] = max(counts[1], counts[0])
        try:
            await asyncio.sleep(pause)
        finally:
            counts[0] -= 1
        done.append(job.queue_id)
        return embedding_module.EMBED_WRITTEN

    monkeypatch.setattr(track, "embed_row", embed_row)
    return counts


async def test_performance_embeds_up_to_two_rows_at_a_time(
    track: EmbeddingTrack, monkeypatch: pytest.MonkeyPatch
) -> None:
    # D-25-12, wired since phase 26: embed_slots rows of one round side by
    # side, and never more, even with two rounds started together (the track
    # lock keeps the rounds apart).
    _performance()
    lane.note_echo(True)
    assert profile.snapshot().effective is profile.Profile.PERFORMANCE
    assert profile.snapshot().resolution.values.embed_slots == 2
    queue = _LaneQueue(*(_job(index, 100 + index) for index in range(1, 7)))
    runner = _runner(track, queue)
    counts = _counting_rows(track, monkeypatch, 0.2)

    await asyncio.gather(runner.run_once(), runner.run_once())

    assert counts[1] == 2
    assert sorted(queue_id for batch, _ in queue.acknowledged for queue_id in batch) == [1, 2, 3, 4, 5, 6]
    assert queue.unlocked == []
    assert not runner.busy


async def test_standard_embeds_one_row_at_a_time(track: EmbeddingTrack, monkeypatch: pytest.MonkeyPatch) -> None:
    _standard()
    lane.note_echo(True)
    assert profile.snapshot().resolution.values.embed_slots == 1
    queue = _LaneQueue(*(_job(index, 100 + index) for index in range(1, 5)))
    runner = _runner(track, queue)
    counts = _counting_rows(track, monkeypatch, 0.02)

    assert await runner.run_once() == ROUND_WORKED

    assert counts[1] == 1
    assert queue.acknowledged == [([1, 2, 3, 4], {})]


async def test_economy_in_the_middle_of_a_performance_round_starts_no_new_row(
    track: EmbeddingTrack, monkeypatch: pytest.MonkeyPatch
) -> None:
    # IDX-08 with two slots: the rows in work end, no further row starts, and
    # the rest goes back per unlock.
    _performance()
    lane.note_echo(True)
    queue = _LaneQueue(*(_job(index, 100 + index) for index in range(1, 7)))
    runner = _runner(track, queue)
    started: list[int] = []

    async def embed_row(job: QueueJob, done: list[int]) -> str:
        started.append(job.queue_id)
        if job.queue_id == 1:
            await asyncio.sleep(0.01)
            profile.note_chosen("economy")
        else:
            await asyncio.sleep(0.05)
        done.append(job.queue_id)
        return embedding_module.EMBED_WRITTEN

    monkeypatch.setattr(track, "embed_row", embed_row)

    assert await runner.run_once() == LANE_PARKED
    assert started == [1, 2]
    assert queue.acknowledged == [([1, 2], {})]
    assert queue.unlocked == [[3, 4, 5, 6]]
    assert lane.snapshot().reason == lane.REASON_ECONOMY
    assert not runner.busy


async def test_a_store_error_in_one_of_two_rows_hands_every_row_back_without_a_verdict(
    track: EmbeddingTrack, monkeypatch: pytest.MonkeyPatch
) -> None:
    # T-26-24: the abort semantics of phase 25 behind the barrier. The other
    # row in work ends, nothing further starts, and every held row goes back.
    _performance()
    lane.note_echo(True)
    queue = _LaneQueue(*(_job(index, 100 + index) for index in range(1, 5)))
    runner = _runner(track, queue, tick=15.0)
    started: list[int] = []

    async def embed_row(job: QueueJob, done: list[int]) -> str:
        started.append(job.queue_id)
        if job.queue_id == 2:
            raise sqlite3.OperationalError("database is locked")
        await asyncio.sleep(0.05)
        done.append(job.queue_id)
        return embedding_module.EMBED_WRITTEN

    monkeypatch.setattr(track, "embed_row", embed_row)

    assert await runner.run_once() == ROUND_PAUSED
    assert started == [1, 2]
    assert queue.unlocked == [[1, 2, 3, 4]]
    assert queue.acknowledged == []
    assert runner.cooldown == 15.0
    assert not runner.busy


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


async def test_a_queue_that_does_not_answer_leaves_the_lane_inline(track: EmbeddingTrack) -> None:
    # Code review WR-02, first path: the mode is published before the claim, so
    # this way out used to keep saying parallel for the whole backoff while no
    # runner claims the embed lane and the poller keeps filtering to the index
    # lane; embed rows were claimed by nobody for up to 300 s per cycle.
    _standard()
    lane.note_echo(True)
    queue = _LaneQueue(_job(1, 11))
    queue.unavailable = True
    runner = _runner(track, queue, tick=15.0)

    assert await runner.run_once() == ROUND_GATEWAY_UNAVAILABLE

    assert lane.snapshot().mode == lane.MODE_INLINE
    assert lane.snapshot().reason == lane.REASON_RUNNER_FAILED
    assert runner.cooldown == 15.0
    assert runner.parked.is_set()

    # The next answered round republishes the lane; nothing is sticky here.
    queue.unavailable = False
    assert await runner.run_once() == ROUND_WORKED
    assert lane.snapshot().mode == lane.MODE_PARALLEL
    assert lane.snapshot().reason == lane.REASON_NONE


async def test_an_unexpected_failure_of_a_round_leaves_the_lane_inline(
    track: EmbeddingTrack, writer: IndexBatchWriter, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Code review WR-02, second path: run() catches the exception of a round
    # that broke between its note_mode and its park, and the mode has to go
    # back with the rows, or the status lies for the whole backoff.
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
    assert lane.snapshot().mode == lane.MODE_INLINE
    assert lane.snapshot().reason == lane.REASON_RUNNER_FAILED


async def test_stand_down_waits_for_the_round_and_hands_the_rows_back(track: EmbeddingTrack) -> None:
    runner = _runner(track, _LaneQueue())
    assert await runner.stand_down(budget=1.0)
    assert await runner.unlock_held() == 0
    await runner.aclose()


async def _until(condition: Callable[[], bool], *, seconds: float = 5.0) -> None:
    """Wait until ``condition`` holds, failing after ``seconds``."""
    for _ in range(int(seconds / 0.01)):
        if condition():
            return
        await asyncio.sleep(0.01)
    assert condition()


async def test_a_probe_hold_lets_the_round_end_parks_and_goes_on_after_release(
    track: EmbeddingTrack, monkeypatch: pytest.MonkeyPatch
) -> None:
    # D-27-05: no new round while held; the round in flight ends and parked is
    # set, which is what the pre-check waits for.
    runner = _runner(track, _LaneQueue(), tick=0.0)
    real = runner.run_once
    started = asyncio.Event()
    gate = asyncio.Event()
    calls: list[int] = []

    async def gated() -> str:
        calls.append(1)
        if len(calls) == 1:
            started.set()
            await gate.wait()
        return await real()

    monkeypatch.setattr(runner, "run_once", gated)
    runner.arm()
    stop = asyncio.Event()
    task = asyncio.ensure_future(runner.run(stop))
    try:
        await asyncio.wait_for(started.wait(), timeout=5)
        runner.hold_for_probe()
        gate.set()
        await _until(runner.parked.is_set)
        await asyncio.sleep(0.05)
        assert len(calls) == 1
        assert runner.parked.is_set()

        runner.release_probe_hold()
        await _until(lambda: len(calls) >= 2)
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=5)


async def test_a_probe_hold_of_the_runner_arms_nothing_and_stops_cleanly(track: EmbeddingTrack) -> None:
    queue = _LaneQueue()
    runner = _runner(track, queue)
    runner.arm()
    runner.hold_for_probe()
    stop = asyncio.Event()
    task = asyncio.ensure_future(runner.run(stop))
    await asyncio.sleep(0.05)
    runner.silence()
    runner.release_probe_hold()
    await asyncio.sleep(0.05)

    assert queue.lanes == []
    assert runner.parked.is_set()
    stop.set()
    await asyncio.wait_for(task, timeout=2)


@pytest.mark.parametrize(
    ("engine", "built", "weights"),
    [(ENGINE_LOADED, True, "int8"), ("cold", True, "int8"), ("cold", True, "fp32"), (ENGINE_LOADED, False, "fp32")],
)
def test_the_need_through_the_neutral_calculation_equals_the_old_sum(
    store: Store, vectors: VectorStore, writer: IndexBatchWriter, engine: str, built: bool, weights: str
) -> None:
    # One spelling for one calculation (D-27-07): bit for bit the sum _need
    # spelled out before it went through probe.pending_load_bytes.
    track = EmbeddingTrack(
        vectors=vectors,
        chunker=_cut if built else None,
        model=_FakeModel() if built else None,
        store=store,
        index=writer.index,
        index_dir=writer.directory,
    )
    old = EMBED_ACTIVATION_BYTES + EMBED_LANE_RESERVE_BYTES
    if not built:
        old += CUTTER_LOAD_BYTES
    if engine != ENGINE_LOADED:
        old += EMBED_WEIGHTS_LOAD_BYTES
        if weights == "fp32":
            old += FP32_EXTRA_BYTES
    runner = _runner(track, _LaneQueue(), engine=engine)

    assert runner._need(weights) == old


# -- the indexing loop and the runner together (T1, T2, T4) ------------------


class _Recorder:
    """Start and end of every OCR run and every embedding, on one clock."""

    def __init__(self) -> None:
        self.intervals: list[tuple[str, float, float]] = []
        self._lock = threading.Lock()

    def note(self, kind: str, start: float, end: float) -> None:
        with self._lock:
            self.intervals.append((kind, start, end))

    def of(self, kind: str) -> list[tuple[float, float]]:
        return [(start, end) for name, start, end in self.intervals if name == kind]

    def overlaps(self) -> bool:
        return any(
            ocr_start < embed_end and embed_start < ocr_end
            for ocr_start, ocr_end in self.of("ocr")
            for embed_start, embed_end in self.of("embed")
        )


@dataclass(slots=True)
class _RecordingModel:
    """A model that writes down when it ran, and may wait or signal on the way."""

    recorder: _Recorder
    seconds: float = 0.05
    started: threading.Event = field(default_factory=threading.Event)
    hold_first: threading.Event | None = None
    calls: int = 0

    def embed_passages(self, texts: Sequence[str]) -> EmbedOutcome:
        begin = time.monotonic()
        self.calls += 1
        self.started.set()
        if self.hold_first is not None and self.calls == 1:
            self.hold_first.wait(timeout=5)
        time.sleep(self.seconds)
        self.recorder.note("embed", begin, time.monotonic())
        return EmbedOutcome.ready([[0.001] * DIMENSIONS for _ in texts])


@dataclass(slots=True)
class _RecordingOcr:
    """The guarded extractor on the OCR route, replaced by a timed stand-in."""

    recorder: _Recorder
    seconds: float = 0.05
    wait_for: threading.Event | None = None
    saw_the_embedding: list[bool] = field(default_factory=list)

    def __call__(
        self, path: str, mime: str, size: int, *, route: Any = None, timeout_seconds: float | None = None
    ) -> ExtractionOutcome:
        del path, mime, size, route, timeout_seconds
        begin = time.monotonic()
        if self.wait_for is not None:
            self.saw_the_embedding.append(self.wait_for.wait(timeout=5))
        time.sleep(self.seconds)
        self.recorder.note("ocr", begin, time.monotonic())
        return ExtractionOutcome.indexed("Gescannter Bescheid ueber die Kuendigungsfrist")


class _FakeGatewayClient:
    async def aclose(self) -> None:
        return None


async def _fetch(nc: Any, file_id: int, user_id: str, fp: Any, *, client: Any = None) -> int:
    del nc, file_id, user_id, client
    fp.write(b"%PDF-1.4 pixels only")
    return 20


def _scan(queue_id: int, file_id: int) -> QueueJob:
    return _job(queue_id, file_id, kind=KIND_OCR, mime="application/pdf")


def _pair(
    store: Store,
    writer: IndexBatchWriter,
    vectors: VectorStore,
    tmp_path: Path,
    queue: _LaneQueue,
    model: _RecordingModel,
    ocr: _RecordingOcr,
) -> tuple[Poller, EmbedRunner]:
    """A real poller and a real runner over one track, attached as plan 25-10 will."""
    poller = Poller(
        store=store,
        writer=writer,
        tmp_dir=tmp_path / "tmp",
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        gateway_factory=lambda: cast("Any", _FakeGatewayClient()),
        queue_factory=lambda nc: cast("Any", queue),
        fetch=_fetch,
        extract=ocr,
        vectors=vectors,
        chunker=_cut,
        model=model,
    )
    runner = _runner(poller.track, queue)
    poller.attach_runner(runner)
    return poller, runner


async def test_t1_economy_never_runs_ocr_beside_an_embedding(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # T1, IDX-08 word for word: a mixed claim of scans and embed rows in
    # Economy, the runner task running along the whole time. It parks, the loop
    # embeds inline after the OCR, and no interval of one overlaps the other.
    recorder = _Recorder()
    _index_bodies(writer, 11, 12)
    queue = _LaneQueue(_scan(1, 21), _job(2, 11), _scan(3, 22), _job(4, 12))
    poller, runner = _pair(store, writer, vectors, tmp_path, queue, _RecordingModel(recorder), _RecordingOcr(recorder))
    stop = asyncio.Event()
    runner.arm()
    loop = asyncio.ensure_future(runner.run(stop))

    result = await poller.run_once()
    stop.set()
    await asyncio.wait_for(loop, timeout=5)

    assert result.state == "worked"
    assert len(recorder.of("ocr")) == 2
    assert len(recorder.of("embed")) == 2
    assert not recorder.overlaps()
    assert queue.lanes == [None]
    assert lane.snapshot().mode == lane.MODE_INLINE


async def test_t2_standard_runs_ocr_and_embedding_side_by_side(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # T2, PAR-01: the OCR of the loop blocks until the runner's embedding has
    # started, five seconds being the failure. The overlap is the proof.
    _standard()
    lane.note_echo(True)
    recorder = _Recorder()
    model = _RecordingModel(recorder, seconds=0.2)
    ocr = _RecordingOcr(recorder, wait_for=model.started)
    _index_bodies(writer, 11)
    queue = _LaneQueue()
    poller, runner = _pair(store, writer, vectors, tmp_path, queue, model, ocr)
    assert await runner.run_once() == ROUND_EMPTY
    assert lane.snapshot().mode == lane.MODE_PARALLEL
    queue.add(_scan(1, 21), _job(2, 11))
    queue.profile_answer = "standard"

    worked, ran = await asyncio.wait_for(asyncio.gather(poller.run_once(), runner.run_once()), timeout=15)

    assert ocr.saw_the_embedding == [True]
    assert recorder.overlaps()
    assert worked.state == "worked"
    assert ran == ROUND_WORKED
    # Which of the two claims goes out first is the scheduler's business.
    assert sorted(str(asked) for asked in queue.lanes[1:]) == [LANE_EMBED, LANE_INDEX]
    assert ([2], {}) in queue.acknowledged


async def test_t4_economy_in_the_middle_of_a_runner_round_ends_the_overlap(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # T4: the runner is embedding its first row when the loop reads Economy.
    # The loop waits for the park before it claims; the runner stops after the
    # row in work and hands the rest back; from the switch on nothing overlaps.
    _standard()
    lane.note_echo(True)
    recorder = _Recorder()
    go = threading.Event()
    model = _RecordingModel(recorder, hold_first=go)
    ocr = _RecordingOcr(recorder)
    _index_bodies(writer, 11, 12, 13)
    queue = _LaneQueue()
    poller, runner = _pair(store, writer, vectors, tmp_path, queue, model, ocr)
    assert await runner.run_once() == ROUND_EMPTY
    queue.add(_scan(1, 21), _job(2, 11), _job(3, 12), _job(4, 13))

    round_task = asyncio.ensure_future(runner.run_once())
    assert await asyncio.to_thread(model.started.wait, 5)
    queue.profile_answer = "economy"
    pass_task = asyncio.ensure_future(poller.run_once())
    await asyncio.sleep(0.1)
    assert queue.lanes == [LANE_EMBED, LANE_EMBED]
    go.set()

    ran, worked = await asyncio.wait_for(asyncio.gather(round_task, pass_task), timeout=15)

    assert ran == LANE_PARKED
    assert worked.state == "worked"
    assert queue.unlocked == [[3, 4]]
    assert queue.lanes == [LANE_EMBED, LANE_EMBED, None]
    assert ([2], {}) in queue.acknowledged
    assert not recorder.overlaps()
    first_embed_end = recorder.of("embed")[0][1]
    assert all(start >= first_embed_end for start, _ in recorder.of("ocr"))
    assert len(recorder.of("embed")) == 3


# -- real CPU on two cores (T3) -----------------------------------------------

# CPU seconds the child of the OCR stand-in burns, and the embedding stand-in
# in its thread. The embedding burns longer, so the child runs inside it.
OCR_BURN_SECONDS = 1.0
EMBED_BURN_SECONDS = 1.5

# The child: a CPU loop in a process of its own, the shape of a tesseract run.
CHILD_LOOP = "import time\nstart = time.process_time()\nwhile time.process_time() - start < {burn}:\n    pass\n"


@dataclass(slots=True)
class _BurningModel:
    """The engine, replaced by a CPU loop in the worker thread that runs it."""

    recorder: _Recorder
    cpu: dict[str, float]
    started: threading.Event = field(default_factory=threading.Event)

    def embed_passages(self, texts: Sequence[str]) -> EmbedOutcome:
        begin = time.monotonic()
        self.started.set()
        spent = time.thread_time()
        while time.thread_time() - spent < EMBED_BURN_SECONDS:
            pass
        self.cpu["embed"] = time.thread_time() - spent
        self.recorder.note("embed", begin, time.monotonic())
        return EmbedOutcome.ready([[0.001] * DIMENSIONS for _ in texts])


@dataclass(slots=True)
class _BurningOcr:
    """The OCR route, replaced by a child process that burns CPU."""

    recorder: _Recorder
    cpu: dict[str, float]
    wait_for: threading.Event

    def __call__(
        self, path: str, mime: str, size: int, *, route: Any = None, timeout_seconds: float | None = None
    ) -> ExtractionOutcome:
        del path, mime, size, route, timeout_seconds
        self.wait_for.wait(timeout=5)
        begin = time.monotonic()
        before = os.times()
        subprocess.run(  # noqa: S603 - an argument list, never a shell
            [sys.executable, "-c", CHILD_LOOP.format(burn=OCR_BURN_SECONDS)], check=True, timeout=30
        )
        after = os.times()
        self.cpu["ocr"] = (after.children_user - before.children_user) + (
            after.children_system - before.children_system
        )
        self.recorder.note("ocr", begin, time.monotonic())
        return ExtractionOutcome.indexed("Gescannter Bescheid ueber die Kuendigungsfrist")


@pytest.mark.skipif(
    sys.platform != "linux" or (os.process_cpu_count() or 1) < 2,
    reason="needs linux with two cores, runs in the gates job",
)
async def test_t3_real_cpu_work_of_both_lanes_overlaps(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path
) -> None:
    # SC1: in Standard on two or more cores the OCR of the loop and the
    # embedding of the runner really run at the same time. The proof is the
    # CPU: both together spent more CPU seconds than the wall time of the window
    # that holds them, which two serial halves never can.
    _standard()
    lane.note_echo(True)
    recorder = _Recorder()
    cpu: dict[str, float] = {}
    model = _BurningModel(recorder, cpu)
    ocr = _BurningOcr(recorder, cpu, wait_for=model.started)
    _index_bodies(writer, 11)
    queue = _LaneQueue()
    poller, runner = _pair(store, writer, vectors, tmp_path, queue, cast("Any", model), cast("Any", ocr))
    assert await runner.run_once() == ROUND_EMPTY
    queue.add(_scan(1, 21), _job(2, 11))
    queue.profile_answer = "standard"

    async with asyncio.timeout(30):
        await asyncio.gather(poller.run_once(), runner.run_once())

    assert recorder.overlaps()
    starts = [start for _, start, _ in recorder.intervals]
    ends = [end for _, _, end in recorder.intervals]
    window = max(ends) - min(starts)
    assert cpu["ocr"] >= OCR_BURN_SECONDS * 0.9
    assert cpu["embed"] >= EMBED_BURN_SECONDS * 0.9
    assert cpu["ocr"] + cpu["embed"] > window
