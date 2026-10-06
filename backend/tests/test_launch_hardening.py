"""The gaps of the hardening matrix of 1.4.0, success criterion 1 (plan 29-04).

docs/audits/2026-10-phase-29/haertungsmatrix.md lists, per scenario, the tests
that already exist and what they really assert. The cases below close the gaps
that list found, one case per gap row, and nothing else:

1. two children killed in one pass under four slots, one of them guilty;
2. an OCR slot and the embed track killed in the same run, then a restart;
3. a restart on a smaller box with Performance chosen;
4. a profile change while the redelivery of the vector stock is running;
5. a second precision change before the first rewrite of the stock is through;
6. a set admin variable against the chosen profile, as the wire reports it.

No harness is new. The poller cases stand on the stand-ins of tests/test_poller.py
(the killing extractor, the slot poller, the scripted queue), the stock cases on
the ones of tests/test_embedding_track.py (the arithmetic model, the fixed width
chunker, the watched drift chain), and the profile cases on the module state of
findling.profile, which the autouse fixture of conftest.py resets on both sides.
A restart is what those files call it too: a second poller on the same volume,
with the module state of the process put back to rest.

Nothing here changes product code. None of the six cases showed a product
fault (no finding H-29-NN), and plan 29-14 ran the matrix again before the
owner acceptance: every case is an ordinary test without an expected failure
marker, and a new fault found here is fixed in the product, not marked.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import pytest
from tantivy import Index

from findling import guard, lane, precision, profile
from findling.api.status import _profile_report
from findling.embed.model import EmbedOutcome
from findling.hardware import Hardware
from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter
from findling.nc.client import AsyncNextcloudApp
from findling.nc.queue import KIND_EMBED, ClaimResult, QueueJob
from findling.profile import SOURCE_ENV, SOURCE_PROFILE, Profile, resolve
from findling.store.repo import EMBEDDING_BACKLOG_MARK, EMBEDDING_MARK, Store, open_store
from findling.store.vectors import WEIGHTS_FP32, WEIGHTS_INT8, VectorStore, open_vectors
from findling.worker import embedding as embedding_module
from findling.worker.poller import ROUND_WORKED, Poller
from test_embedding_track import (
    ANOTHER_MARK,
    MARK_OF_FP32,
    MARK_OF_V1_3,
    _drift_chain,
    _fill,
    _judged,
    _wanted_mark,
    _watched,
)
from test_embedding_track import _cut as track_cut
from test_embedding_track import _FakeModel as TrackModel
from test_embedding_track import _FakeQueue as TrackQueue
from test_embedding_track import _poller as track_poller
from test_poller import (
    BODY,
    CONSTITUENTS,
    _FakeGatewayClient,
    _FakeQueue,
    _gateway,
    _job,
    _killing_poller,
    _KillingExtractor,
    _ocr_row,
    _slot_poller,
    _SlotExtractor,
    _stored_ids,
)

GIB = 1024**3

# Far above what any slot count of these cases needs, the value of test_poller.
ROOM_FOR_EVERY_SLOT = 1 << 40


def _big_box() -> Hardware:
    """16 cores and 64 GiB: Performance fits, and its slot formula reaches 15."""
    return Hardware(
        cpu_count=16,
        cpu_quota=None,
        cores=16,
        memory_limit_bytes=None,
        memory_available_bytes=64 * GIB,
        memory_total_bytes=64 * GIB,
        architecture="x86_64",
        cgroup="none",
    )


def _smaller_box() -> Hardware:
    """8 cores and 8 GB: Standard is the largest level that fits (D-24-06)."""
    return Hardware(
        cpu_count=8,
        cpu_quota=None,
        cores=8,
        memory_limit_bytes=None,
        memory_available_bytes=8_000_000_000,
        memory_total_bytes=8_000_000_000,
        architecture="aarch64",
        cgroup="none",
    )


def _restart() -> None:
    """The module state of a fresh process; the volume stays as it is.

    The same reset conftest.py runs around every case, called in the middle of
    one, because a restart forgets exactly these: the hardware reading, the
    chosen profile, the precision, the lane and the guard.
    """
    profile.reset()
    precision.reset()
    lane.reset()
    guard.reset()


# -- fixtures, the shapes of test_poller.py and test_embedding_track.py ------


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


# -- 1. OOM in the middle of N slots ------------------------------------------


async def test_two_children_killed_in_one_pass_are_retried_alone_and_only_the_guilty_one_is_out_of_memory(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path
) -> None:
    # D-26-08 and D-26-16 with two kills at once. Scan 300 is the guilty one, it
    # dies alone as well; scan 302 only stood beside it and dies once. Both run
    # again alone behind the barrier, only 300 ends as out_of_memory, and every
    # other document is in the index exactly once.
    jobs = tuple(_ocr_row(offset) for offset in range(4))
    queue = _FakeQueue(ClaimResult(jobs=jobs))
    extract = _KillingExtractor(kills={300: 5, 302: 1})
    poller = _killing_poller(store, writer, tmp_path, queue, extract, slots=4)

    result = await poller.run_once()

    assert result.state == ROUND_WORKED
    assert result.indexed == 3
    assert len(queue.acknowledged) == 1
    done, failed = queue.acknowledged[0]
    assert sorted(done) == [301, 302, 303]
    assert failed == {300: "out_of_memory"}
    assert len(extract.calls_for(300)) == 2, "one run beside the others, one alone, no third"
    assert len(extract.calls_for(302)) == 2
    assert len(extract.calls_for(301)) == 1
    assert len(extract.calls_for(303)) == 1
    assert guard.take_child_kills() == 2, "the two kills of the shared round, the solo death is no report"
    assert sorted(_stored_ids(index)) == [7001, 7002, 7003], "every survivor exactly once, the guilty one never"
    for file_id in (7001, 7002, 7003):
        row = store.file_row(file_id)
        assert row is not None
        assert row["state"] == "indexed"
    guilty = store.file_row(7000)
    assert guilty is None or guilty["state"] != "indexed"


# -- 2. both tracks killed ----------------------------------------------------


class _Killed(BaseException):
    """The death of the process, seen from inside it.

    A BaseException, because a SIGKILL is not an error any handler of the
    poller could answer: nothing below the pass may turn it into a verdict.
    """


class _DyingModel:
    """The arithmetic model of test_embedding_track that dies at its n-th call."""

    def __init__(self, dies_at: int) -> None:
        self._dies_at = dies_at
        self._inner = TrackModel()
        self.calls = 0

    def embed_passages(self, texts: Sequence[str]) -> EmbedOutcome:
        self.calls += 1
        if self.calls == self._dies_at:
            raise _Killed
        return self._inner.embed_passages(texts)


def _both_tracks_poller(
    *,
    store: Store,
    writer: IndexBatchWriter,
    tmp_path: Path,
    queue: _FakeQueue,
    vectors: VectorStore,
    extract: Any,
    model: Any,
) -> Poller:
    """The slot poller of test_poller with the second track of test_embedding_track wired in."""
    return Poller(
        store=store,
        writer=writer,
        tmp_dir=tmp_path / "tmp",
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        gateway_factory=lambda: cast("Any", _FakeGatewayClient()),
        queue_factory=lambda nc: cast("Any", queue),
        fetch=_gateway({}),
        extract=extract,
        ocr_slots=4,
        headroom=lambda: ROOM_FOR_EVERY_SLOT,
        vectors=vectors,
        chunker=track_cut,
        model=model,
    )


def _embed_row(file_id: int) -> QueueJob:
    return _job(400 + file_id - 7000, file_id, kind=KIND_EMBED, title=f"Scan{file_id}.pdf")


async def test_an_ocr_slot_and_the_embed_track_killed_in_one_run_leave_every_verdict_and_every_vector_after_the_restart(
    store: Store, writer: IndexBatchWriter, index: Index, vectors: VectorStore, tmp_path: Path
) -> None:
    file_ids = [7000, 7001, 7002, 7003]
    scans = tuple(_ocr_row(offset) for offset in range(4))
    embeds = tuple(_embed_row(file_id) for file_id in file_ids)
    first_queue = _FakeQueue(ClaimResult(jobs=scans), ClaimResult(jobs=embeds))
    # The child of scan 301 is killed beside the others, and the engine of the
    # second track dies at its third document: the process is gone.
    first = _both_tracks_poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=first_queue,
        vectors=vectors,
        extract=_KillingExtractor(kills={301: 1}),
        model=_DyingModel(dies_at=3),
    )

    ocr_pass = await first.run_once()

    assert ocr_pass.indexed == 4
    handed = sorted(file_id for ids, kind in first_queue.requeues if kind == KIND_EMBED for file_id in ids)
    assert handed == file_ids, "every scan went on to the second track"

    with pytest.raises(_Killed):
        await first.run_once()

    assert 0 < vectors.document_count() < len(file_ids), "the second track died in the middle of its rows"
    assert first_queue.unlocked == [], "a dead process hands nothing back, only the lease does"

    # The restart. Nextcloud gives back every embed row the dead process held
    # and never acknowledged, after the lease, the way claimBatch does.
    acknowledged = {queue_id for done, failed in first_queue.acknowledged for queue_id in (*done, *failed)}
    redelivered = tuple(job for job in embeds if job.queue_id not in acknowledged)
    assert redelivered, "the death took at least the row in work with it"
    _restart()
    second_queue = _FakeQueue(ClaimResult(jobs=redelivered))
    second = _both_tracks_poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=second_queue,
        vectors=vectors,
        extract=_KillingExtractor(kills={}),
        model=TrackModel(),
    )

    await second.run_once()

    assert sorted(_stored_ids(index)) == file_ids, "every scan exactly once in the index"
    for file_id in file_ids:
        row = store.file_row(file_id)
        assert row is not None
        assert row["state"] == "indexed"
    assert vectors.document_count() == len(file_ids), "every document carries its vectors"
    chunks_per_document = len(track_cut(BODY))
    assert vectors.chunk_count() == len(file_ids) * chunks_per_document, "no document carries its chunks twice"


# -- 3. the box shrank --------------------------------------------------------


async def test_a_restart_on_a_smaller_box_lowers_the_effective_level_and_the_slots_and_loses_no_document(
    store: Store, writer: IndexBatchWriter, index: Index, tmp_path: Path
) -> None:
    # D-24-07 across a restart: the chosen Performance stays, the effective
    # level falls to the largest one the new box fits, the slot target of the
    # pass follows it, and the stock written on the big box is all still there.
    profile.note_hardware(_big_box())
    big_queue = _FakeQueue(ClaimResult(jobs=tuple(_ocr_row(offset) for offset in range(4))))
    big_queue.profile_answer = "performance"
    big = _slot_poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=big_queue,
        extract=_SlotExtractor(seconds=0.01),
        ocr_slots=None,
    )

    await big.run_once()

    slots_on_the_big_box = guard.snapshot().slots_target
    assert slots_on_the_big_box == resolve(Profile.PERFORMANCE, _big_box()).values.ocr_slots
    assert profile.snapshot().effective is Profile.PERFORMANCE

    _restart()
    profile.note_hardware(_smaller_box())
    small_queue = _FakeQueue(ClaimResult(jobs=tuple(_ocr_row(offset) for offset in range(4, 8))))
    small_queue.profile_answer = "performance"
    small = _slot_poller(
        store=store,
        writer=writer,
        tmp_path=tmp_path,
        queue=small_queue,
        extract=_SlotExtractor(seconds=0.01),
        ocr_slots=None,
    )

    result = await small.run_once()

    report = _profile_report()
    assert report.chosen == "performance", "the choice of the admin is never rewritten"
    assert report.effective == "standard"
    assert report.downgraded, "the status page says that a smaller level runs"
    expected_slots = resolve(Profile.STANDARD, _smaller_box()).values.ocr_slots
    assert report.values["ocrSlots"] == expected_slots
    assert guard.snapshot().slots_target == expected_slots
    assert 1 <= expected_slots < slots_on_the_big_box
    assert result.indexed == 4
    stored = sorted(_stored_ids(index))
    assert stored == list(range(7000, 7008)), "every document of both boxes exactly once"
    for file_id in range(7000, 7004):
        row = store.file_row(file_id)
        assert row is not None
        assert row["state"] == "indexed", "the stock of the big box survives the restart"


# -- 4. a profile change in the middle of the vector reindex ------------------


async def test_a_profile_change_during_the_redelivery_lets_the_cursor_run_to_the_end_without_losing_a_band(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # One document per band, so the sweep takes three passes for three
    # documents. The admin moves Economy to Standard after the first band and
    # back down after the second: the cursor in the meta table does not care,
    # every document is handed back exactly once, and the sweep ends.
    monkeypatch.setattr("findling.worker.embedding.VECTOR_BACKLOG_BAND", 1)
    profile.note_hardware(_big_box())
    store.write_meta(EMBEDDING_MARK, ANOTHER_MARK)
    for file_id in (4711, 4712, 4713):
        _judged(store, file_id)
    queue = TrackQueue()
    queue.profile_answer = "economy"
    poller = track_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)

    await poller.run_once()

    assert profile.snapshot().effective is Profile.ECONOMY
    assert store.read_meta()[EMBEDDING_BACKLOG_MARK] == "4711"

    queue.profile_answer = "standard"
    await poller.run_once()

    assert profile.snapshot().effective is Profile.STANDARD
    assert store.read_meta()[EMBEDDING_BACKLOG_MARK] == "4712"

    queue.profile_answer = "economy"
    for _ in range(3):
        await poller.run_once()

    handed = [file_id for ids, kind in queue.requeues if kind == KIND_EMBED for file_id in ids]
    assert handed == [4711, 4712, 4713], "every band exactly once, none lost and none twice"
    assert store.read_meta()[EMBEDDING_BACKLOG_MARK] == "", "the sweep ended"
    assert store.read_meta()[EMBEDDING_MARK] == _wanted_mark()


# -- 5. a model change in the middle of the vector reindex --------------------


async def test_a_second_precision_change_before_the_first_rewrite_ends_leaves_a_consistent_stock_under_the_right_mark(
    store: Store, writer: IndexBatchWriter, vectors: VectorStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # int8 to fp32, and back to int8 while the fp32 rewrite has handed out one
    # band of two. The second change is a drift of its own: the chain runs
    # again from the top, the fp32 vectors written meanwhile leave with it, the
    # mark ends on int8, and the sweep after it hands every document back.
    monkeypatch.setattr("findling.worker.embedding.VECTOR_BACKLOG_BAND", 1)
    store.write_meta(EMBEDDING_MARK, MARK_OF_V1_3)
    _judged(store, 4711)
    _judged(store, 4712)
    _fill(vectors, 4711)
    _fill(vectors, 4712)
    queue = TrackQueue()
    poller = track_poller(store=store, writer=writer, tmp_path=tmp_path, queue=queue, vectors=vectors)
    events = _watched(monkeypatch, store, vectors, queue)

    monkeypatch.setattr(embedding_module, "engine_precision", lambda: WEIGHTS_FP32)
    await poller.run_once()

    assert store.read_meta()[EMBEDDING_MARK] == MARK_OF_FP32
    assert store.read_meta()[EMBEDDING_BACKLOG_MARK] == "4711"
    assert vectors.chunk_count() == 0
    # The first band was embedded again under fp32 before the second change.
    _fill(vectors, 4711)
    requeues_before = len(queue.requeues)

    monkeypatch.setattr(embedding_module, "engine_precision", lambda: WEIGHTS_INT8)
    for _ in range(4):
        await poller.run_once()

    chain = _drift_chain(events)
    drift = ["forget_all", f"write:{EMBEDDING_MARK}", f"requeue:{KIND_EMBED}"]
    assert chain[:3] == drift, "the first change"
    assert chain[3:6] == drift, "the second change runs the whole chain again"
    assert set(chain[6:]) <= {f"requeue:{KIND_EMBED}"}, "after it only the sweep, no third emptying"
    assert store.read_meta()[EMBEDDING_MARK] == MARK_OF_V1_3, "the mark says int8"
    assert vectors.chunk_count() == 0, "no fp32 vector survives under the int8 mark"
    after = [file_id for ids, kind in queue.requeues[requeues_before:] if kind == KIND_EMBED for file_id in ids]
    assert after == [4711, 4712], "after the second change every document is asked for once"
    assert store.read_meta()[EMBEDDING_BACKLOG_MARK] == "", "the sweep ended"


# -- 6. an admin variable against the chosen profile --------------------------


def test_a_set_variable_beats_the_chosen_profile_in_the_snapshot_and_survives_a_profile_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # PROF-03 through the process state and the wire, not only through
    # resolve(): the admin set two variables, chose Performance on a big box,
    # and then changed the profile twice. The variables win every time and the
    # status page names their source; every other value stays the profile's.
    monkeypatch.setenv("FINDLING_OCR_MAX_PAGES", "29")
    monkeypatch.setenv("FINDLING_OCR_DPI", "200")
    profile.note_hardware(_big_box())

    for chosen in ("performance", "economy", "standard"):
        profile.note_chosen(chosen)
        report = _profile_report()

        assert report.effective == chosen
        assert report.values["ocrMaxPages"] == 29
        assert report.values["ocrDpi"] == 200
        assert report.sources["ocrMaxPages"] == SOURCE_ENV
        assert report.sources["ocrDpi"] == SOURCE_ENV
        others = {key: source for key, source in report.sources.items() if key not in {"ocrMaxPages", "ocrDpi"}}
        assert set(others.values()) == {SOURCE_PROFILE}, chosen
        assert report.values["ocrSlots"] == resolve(Profile(chosen), _big_box()).values.ocr_slots
