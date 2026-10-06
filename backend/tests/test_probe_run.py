"""The pre-check task of plan 27-09: steps, gates, caps, kill, cleanup, restart.

Every case runs against fakes for the poller, the runner, the pool, the fetch,
the headroom and the children, and against a state.db in tmp_path; no case
reads the memory of the machine the suite runs on. One case at the bottom runs
a real extraction child on the shipped scan page, on Linux with tesseract only.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import shutil
import sys
import threading
import time
from collections.abc import Awaitable, Callable, Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from findling import guard, probe, profile
from findling.config import (
    FP32_EXTRA_BYTES,
    GUARD_RESERVE_BYTES,
    MODEL_PROBE_CHILD_BYTES,
    OCR_SLOT_COST_BYTES,
    PROBE_TAKEOVER_SECONDS,
)
from findling.embed import model_probe, weights
from findling.extract.errors import ChildKilled, ExtractionOutcome, Reason
from findling.extract.sandbox import ExtractionWorker
from findling.hardware import Hardware
from findling.nc.queue import CompanionChoice
from findling.profile import Profile
from findling.store.repo import open_store
from findling.worker.probe_run import ProbeRun

MIB = 1024 * 1024
GIB = 1024 * MIB
BIG = 32 * GIB
PAYLOAD = b"fp32 weights of the test, not a model " * 64

ModelMeasure = model_probe.ModelMeasure


def _big_box() -> Hardware:
    return Hardware(
        cpu_count=None,
        cpu_quota=None,
        cores=16,
        memory_limit_bytes=None,
        memory_available_bytes=int(64e9),
        memory_total_bytes=int(64e9),
        architecture="aarch64",
        cgroup="none",
    )


def _reference_box() -> Hardware:
    """m7g.large with the 2 GiB limit of run 6: below the standard thresholds (D-24-06)."""
    return Hardware(
        cpu_count=2,
        cpu_quota=None,
        cores=2,
        memory_limit_bytes=2 * GIB,
        memory_available_bytes=2 * GIB,
        memory_total_bytes=8 * GIB,
        architecture="aarch64",
        cgroup="v2",
    )


@pytest.fixture(autouse=True)
def _clean_probe_state() -> Iterator[None]:
    probe.reset()
    weights.forget_verdicts()
    yield
    probe.reset()
    weights.forget_verdicts()


@pytest.fixture
def small_weights(monkeypatch: pytest.MonkeyPatch) -> bytes:
    """The recorded fp32 identity shrunk to a payload of a few kilobytes."""
    monkeypatch.setattr(weights, "FP32_BYTES", len(PAYLOAD))
    monkeypatch.setattr(weights, "FP32_SHA256", hashlib.sha256(PAYLOAD).hexdigest())
    return PAYLOAD


# -- fakes -----------------------------------------------------------------


class FakePoller:
    def __init__(self) -> None:
        self.pass_in_flight = False
        self.holds = 0
        self.releases = 0

    def hold_for_probe(self) -> None:
        self.holds += 1

    def release_probe_hold(self) -> None:
        self.releases += 1


class FakeRunner:
    def __init__(self) -> None:
        self.parked = asyncio.Event()
        self.parked.set()
        self.holds = 0
        self.releases = 0

    def hold_for_probe(self) -> None:
        self.holds += 1

    def release_probe_hold(self) -> None:
        self.releases += 1


class FakePool:
    def __init__(self) -> None:
        self.sheds = 0

    def shed_idle(self) -> int:
        self.sheds += 1
        return 0


class FakeHeadroom:
    """A headroom the fake children lower while they run."""

    def __init__(self, base: int | None = BIG) -> None:
        self.base = base
        self._load = 0
        self._lock = threading.Lock()

    def __call__(self) -> int | None:
        if self.base is None:
            return None
        with self._lock:
            return self.base - self._load

    def add(self, amount: int) -> None:
        with self._lock:
            self._load += amount


class FakeWorker:
    def __init__(self, factory: Workers, index: int) -> None:
        self._factory = factory
        self.index = index
        self.halted = threading.Event()
        self.stopped = 0

    def run(
        self, path: str, mime: str, size: int, *, route: str | None = None, timeout_seconds: float | None = None
    ) -> ExtractionOutcome:
        factory = self._factory
        factory.calls.append((path, mime, size, route, timeout_seconds))
        factory.env.append(os.environ.get("FINDLING_OCR_DPI"))
        cost = factory.cost(self.index)
        factory.headroom.add(cost)
        try:
            if factory.hang:
                self.halted.wait(5.0)
                return ExtractionOutcome.failed(Reason.CORRUPT)
            time.sleep(factory.seconds)
            result = factory.result(self.index)
        finally:
            factory.headroom.add(-cost)
        if isinstance(result, BaseException):
            raise result
        return result

    def halt(self) -> None:
        self._factory.halts += 1
        self.halted.set()

    def stop(self) -> None:
        self.stopped += 1


class Workers:
    """The worker factory: counts the children and says what each one does."""

    def __init__(self, headroom: FakeHeadroom) -> None:
        self.headroom = headroom
        self.made: list[FakeWorker] = []
        self.calls: list[tuple[str, str, int, str | None, float | None]] = []
        self.env: list[str | None] = []
        self.halts = 0
        self.hang = False
        self.seconds = 0.05
        self.costs: Callable[[int], int] = lambda _index: 300 * MIB
        self.results: Callable[[int], ExtractionOutcome | BaseException] = lambda _index: ExtractionOutcome.indexed(
            "text"
        )

    def __call__(self) -> FakeWorker:
        worker = FakeWorker(self, len(self.made))
        self.made.append(worker)
        return worker

    def cost(self, index: int) -> int:
        return self.costs(index)

    def result(self, index: int) -> ExtractionOutcome | BaseException:
        return self.results(index)


class Measures:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.answers: dict[str, ModelMeasure] = {
            "int8": ModelMeasure(model_probe.MEASURE_OK, 300 * MIB, 450 * MIB, 4000),
            "fp32": ModelMeasure(model_probe.MEASURE_OK, 300 * MIB, 950 * MIB, 1500),
        }

    def __call__(self, precision: model_probe.Precision, models_dir: Path, *, timeout_seconds: float) -> ModelMeasure:
        del models_dir, timeout_seconds
        self.calls.append(precision)
        return self.answers[precision]


class Fetch:
    """A fake fetch_release_asset: hands the payload over in chunks."""

    def __init__(self, payload: bytes = PAYLOAD, *, hang: bool = False, error: bool = False) -> None:
        self.payload = payload
        self.hang = hang
        self.error = error
        self.calls = 0

    async def __call__(self, url: str, write: Callable[[bytes], Awaitable[None]], *, cap: int) -> None:
        del url, cap
        self.calls += 1
        if self.error:
            raise RuntimeError("unreachable")
        await write(self.payload[:100])
        if self.hang:
            await asyncio.sleep(3600)
        for start in range(100, len(self.payload), 500):
            await write(self.payload[start : start + 500])


class Rig:
    """One ProbeRun with its fakes."""

    def __init__(self, tmp_path: Path, **overrides: object) -> None:
        self.state = tmp_path / "state.db"
        open_store(self.state).close()
        self.models = tmp_path / "models"
        self.models.mkdir()
        self.poller = FakePoller()
        self.runner = FakeRunner()
        self.pool = FakePool()
        self.headroom = FakeHeadroom()
        self.workers = Workers(self.headroom)
        self.measures = Measures()
        self.fetch = Fetch()
        self.rebuild_may_start = True
        kwargs: dict[str, object] = {
            "poller": self.poller,
            "runner": self.runner,
            "pool": self.pool,
            "models_dir": self.models,
            "fetch": self.fetch,
            "rebuild_may_start": lambda: self.rebuild_may_start,
            "engine_loaded": lambda: True,
            "cutter_built": lambda: True,
            "embed_slots": lambda: 0,
            "state_path": self.state,
            "headroom": self.headroom,
            "worker_factory": self.workers,
            "model_measure": self.measures,
            "hardware": _big_box,
            "sample_seconds": 0.005,
            "min_free_bytes": 0,
        }
        kwargs.update(overrides)
        self.run = ProbeRun(**kwargs)  # type: ignore[arg-type]

    def meta(self) -> dict[str, str]:
        store = open_store(self.state)
        try:
            return store.read_meta()
        finally:
            store.close()

    def write_meta(self, values: dict[str, str]) -> None:
        store = open_store(self.state)
        try:
            for key, value in values.items():
                store.write_meta(key, value)
        finally:
            store.close()

    async def check(self, target: str = "standard", precision: str = "int8") -> probe.ProbeSnapshot:
        answer, probe_id = await self.run.start(target, precision)
        assert answer == "started"
        assert self.run.task is not None
        await asyncio.wait_for(self.run.task, timeout=20)
        snap = probe.snapshot()
        assert snap.id == probe_id
        return snap

    def released(self) -> bool:
        return self.poller.releases >= 1 and self.runner.releases >= 1 and not probe.held()


@pytest.fixture
def steps(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    seen: list[str] = []
    original = probe.note_step

    def note(step: str, bytes_done: int = 0, bytes_total: int = 0, *, slots: int = 0) -> None:
        if not seen or seen[-1] != step:
            seen.append(step)
        original(step, bytes_done, bytes_total, slots=slots)

    monkeypatch.setattr(probe, "note_step", note)
    return seen


def _placed(rig: Rig, payload: bytes) -> Path:
    target = weights.fp32_weights_path(rig.models)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return target


async def _wait_for(condition: Callable[[], bool], seconds: float = 5.0) -> None:
    deadline = time.monotonic() + seconds
    while not condition():
        assert time.monotonic() < deadline, "condition not reached"
        await asyncio.sleep(0.01)


# -- task 1: start, pause, download, cleanup, persistence, restart ------------


async def test_a_second_start_while_running_is_busy(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.poller.pass_in_flight = True
    first, probe_id = await rig.run.start("standard", "int8")
    task = rig.run.task
    second = await rig.run.start("performance", "int8")
    assert first == "started"
    assert second == ("busy", probe_id)
    assert rig.run.task is task
    rig.poller.pass_in_flight = False
    assert task is not None
    await asyncio.wait_for(task, timeout=20)
    assert probe.snapshot().verdict == probe.VERDICT_FITS


async def test_a_start_during_a_rebuild_is_refused(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.rebuild_may_start = False
    assert await rig.run.start("standard", "int8") == ("rebuilding", "")
    assert rig.run.task is None
    assert probe.snapshot().state == probe.STATE_IDLE


async def test_the_id_is_sixteen_hex_digits(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    snap = await rig.check()
    assert len(snap.id) == 16
    int(snap.id, 16)


async def test_the_steps_of_an_int8_check_run_in_order(tmp_path: Path, steps: list[str]) -> None:
    rig = Rig(tmp_path)
    snap = await rig.check("standard", "int8")
    assert steps == ["pause", "ocr_one", "calc", "ocr_n", "cleanup"]
    assert snap.verdict == probe.VERDICT_FITS
    assert snap.cause == ""
    assert rig.measures.calls == []
    assert rig.fetch.calls == 0


async def test_the_pause_holds_both_and_waits_for_the_pass_in_flight(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.poller.pass_in_flight = True
    rig.runner.parked.clear()
    await rig.run.start("standard", "int8")
    await _wait_for(lambda: probe.snapshot().step == "pause")
    await asyncio.sleep(0.1)
    assert rig.poller.holds == 1
    assert rig.runner.holds == 1
    assert probe.held()
    # The guard keeps watching the pass the pause waits for (review WR-09).
    assert not probe.measuring()
    assert rig.pool.sheds >= 1
    assert rig.workers.made == []
    rig.poller.pass_in_flight = False
    await asyncio.sleep(0.1)
    assert rig.workers.made == []  # the runner is still in its round
    rig.runner.parked.set()
    assert rig.run.task is not None
    await asyncio.wait_for(rig.run.task, timeout=20)
    assert rig.pool.sheds >= 2
    assert probe.snapshot().verdict == probe.VERDICT_FITS
    assert rig.released()
    assert not probe.measuring()


async def test_the_guard_is_suspended_while_the_children_of_the_check_run(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    seen: list[bool] = []
    rig.workers.results = lambda _index: (seen.append(probe.measuring()), ExtractionOutcome.indexed("text"))[1]
    await rig.check("economy", "int8")
    assert seen == [True]
    assert not probe.measuring()


# -- the threshold gate before the pause (D-24-07, owner decision 03.10.2026) --


@pytest.mark.parametrize("target", ["standard", "performance"])
async def test_a_box_below_the_thresholds_ends_hardware_short_without_measuring(
    tmp_path: Path, steps: list[str], target: str
) -> None:
    rig = Rig(tmp_path, hardware=_reference_box)
    snap = await rig.check(target, "int8")
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "hardware_short")
    assert dict(snap.numbers) == {}
    # No pause, no download, no model and no OCR child: only the end.
    assert steps == ["cleanup"]
    assert rig.poller.holds == 0
    assert rig.runner.holds == 0
    assert rig.pool.sheds == 0
    assert rig.workers.made == []
    assert rig.measures.calls == []
    assert rig.fetch.calls == 0
    assert rig.released()
    assert rig.meta()[probe.META_PROBE_STATE] == probe.STATE_DONE


async def test_a_box_below_the_thresholds_still_measures_economy(tmp_path: Path, steps: list[str]) -> None:
    rig = Rig(tmp_path, hardware=_reference_box)
    await rig.check("economy", "int8")
    assert steps[0] == "pause"
    assert probe.snapshot().cause != "hardware_short"


async def test_a_pass_that_outlasts_the_pause_cap_is_pause_timeout(tmp_path: Path) -> None:
    rig = Rig(tmp_path, pause_seconds=0.1)
    rig.poller.pass_in_flight = True
    snap = await rig.check()
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "pause_timeout")
    assert snap.numbers["seconds"] == 1
    assert rig.workers.made == []
    assert rig.released()


async def test_an_exception_in_the_measurement_is_probe_failed_and_lifts_the_hold(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.workers.results = lambda _index: RuntimeError("boom")
    snap = await rig.check()
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "probe_failed")
    assert rig.released()


async def test_a_broken_calculation_is_probe_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rig = Rig(tmp_path)

    def broken(**_kwargs: int) -> probe.Verdict:
        raise ArithmeticError

    monkeypatch.setattr(probe, "judge", broken)
    snap = await rig.check()
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "probe_failed")
    assert rig.released()


async def test_a_cancellation_lifts_the_hold(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.poller.pass_in_flight = True
    await rig.run.start("standard", "int8")
    await _wait_for(probe.held)
    await rig.run.close()
    assert rig.run.task is not None
    assert rig.run.task.cancelled()
    assert rig.released()
    # No verdict: the next start reads it as interrupted.
    assert probe.snapshot().state == probe.STATE_RUNNING
    assert rig.meta()[probe.META_PROBE_STATE] == probe.STATE_RUNNING


async def test_the_fp32_download_counts_its_bytes(
    tmp_path: Path, small_weights: bytes, steps: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = Rig(tmp_path)
    progress: list[tuple[int, int]] = []
    original = probe.note_step

    def note(step: str, bytes_done: int = 0, bytes_total: int = 0, *, slots: int = 0) -> None:
        if step == "download":
            progress.append((bytes_done, bytes_total))
        original(step, bytes_done, bytes_total, slots=slots)

    monkeypatch.setattr(probe, "note_step", note)
    snap = await rig.check("standard", "fp32")
    assert steps == ["pause", "download", "model", "ocr_one", "calc", "ocr_n", "cleanup"]
    assert progress[0] == (0, len(small_weights))
    assert progress[-1] == (len(small_weights), len(small_weights))
    assert [done for done, _ in progress] == sorted(done for done, _ in progress)
    assert snap.verdict == probe.VERDICT_FITS
    assert snap.fp32_fetched is True
    assert snap.fp32_deleted is False
    assert weights.fp32_weights_path(rig.models).read_bytes() == small_weights
    assert rig.meta()[probe.META_PROBE_FP32_FETCHED] == "1"


async def test_a_hanging_download_is_download_slow_without_a_part(tmp_path: Path, small_weights: bytes) -> None:
    del small_weights
    rig = Rig(tmp_path, download_seconds=0.2)
    rig.run._fetch = Fetch(hang=True)
    snap = await rig.check("standard", "fp32")
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "download_slow")
    target = weights.fp32_weights_path(rig.models)
    assert not target.exists()
    assert not target.with_name(target.name + weights.PART_SUFFIX).exists()
    assert rig.released()


@pytest.mark.parametrize(
    ("fetch", "min_free", "cause"),
    [
        (Fetch(b"not the recorded weights" * 100), 0, "digest_mismatch"),
        (Fetch(error=True), 0, "download_failed"),
        (Fetch(), 1 << 62, "disk_short"),
    ],
)
async def test_the_procure_outcomes_map_onto_the_causes(
    tmp_path: Path, small_weights: bytes, fetch: Fetch, min_free: int, cause: str
) -> None:
    del small_weights
    rig = Rig(tmp_path, fetch=fetch, min_free_bytes=min_free)
    snap = await rig.check("standard", "fp32")
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, cause)
    assert not weights.fp32_weights_path(rig.models).exists()
    assert rig.measures.calls == []


async def test_a_placed_file_is_checked_by_digest_and_stays_on_nofit(
    tmp_path: Path, small_weights: bytes, steps: list[str]
) -> None:
    rig = Rig(tmp_path)
    target = _placed(rig, small_weights)
    rig.measures.answers["fp32"] = ModelMeasure(model_probe.MEASURE_KILLED, 0, 0, 0)
    snap = await rig.check("standard", "fp32")
    assert steps[:3] == ["pause", "digest", "model"]
    assert "download" not in steps
    assert rig.fetch.calls == 0
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "slot_killed")
    assert snap.fp32_fetched is False
    assert snap.fp32_deleted is False
    assert target.exists()


async def test_a_placed_file_with_another_digest_is_digest_mismatch_and_stays(
    tmp_path: Path, small_weights: bytes
) -> None:
    rig = Rig(tmp_path)
    target = _placed(rig, bytes(len(small_weights)))
    snap = await rig.check("standard", "fp32")
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "digest_mismatch")
    assert target.exists()
    assert rig.fetch.calls == 0


async def test_a_fetched_file_goes_again_on_nofit(tmp_path: Path, small_weights: bytes) -> None:
    del small_weights
    rig = Rig(tmp_path)
    rig.workers.results = lambda _index: ChildKilled(engine=False)
    snap = await rig.check("standard", "fp32")
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "slot_killed")
    assert snap.fp32_fetched is True
    assert snap.fp32_deleted is True
    assert not weights.fp32_weights_path(rig.models).exists()
    assert rig.meta()[probe.META_PROBE_FP32_FETCHED] == ""


async def test_a_fetched_file_goes_again_on_narrow(
    tmp_path: Path, small_weights: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    del small_weights
    rig = Rig(tmp_path)
    narrow = probe.Verdict(probe.VERDICT_NARROW, probe.CAUSE_RESERVE_THIN, {"reserve": 1, "required": 2})
    monkeypatch.setattr(probe, "judge", lambda **_kwargs: narrow)
    snap = await rig.check("standard", "fp32")
    assert snap.verdict == probe.VERDICT_NARROW
    assert snap.fp32_deleted is True
    assert not weights.fp32_weights_path(rig.models).exists()


async def test_fp32_in_force_needs_neither_download_nor_model(tmp_path: Path, steps: list[str]) -> None:
    profile.note_weights("fp32")
    rig = Rig(tmp_path)
    snap = await rig.check("standard", "fp32")
    assert steps == ["pause", "ocr_one", "calc", "ocr_n", "cleanup"]
    assert snap.verdict == probe.VERDICT_FITS
    assert rig.measures.calls == []


async def test_the_start_answers_before_the_state_is_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review WR-07 of phase 27: a slow state.db write never delays the 202.

    PHP cuts the start off after two seconds; a start that waited for a write
    behind the SQLite writer of the poller answered too late, PHP recorded
    nothing, and the probe ran without anybody taking its verdict over.
    """
    rig = Rig(tmp_path)
    gate = threading.Event()
    original = ProbeRun._write_meta_sync

    def slow(self: ProbeRun, values: dict[str, str]) -> None:
        gate.wait(10)
        original(self, values)

    monkeypatch.setattr(ProbeRun, "_write_meta_sync", slow)
    started = time.monotonic()
    answer, probe_id = await asyncio.wait_for(rig.run.start("standard", "int8"), timeout=5)
    assert answer == "started"
    assert time.monotonic() - started < 1.0
    gate.set()
    assert rig.run.task is not None
    await asyncio.wait_for(rig.run.task, timeout=20)
    assert rig.meta()[probe.META_PROBE_ID] == probe_id


async def test_the_meta_carries_running_and_then_the_result(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.poller.pass_in_flight = True
    _, probe_id = await rig.run.start("standard", "int8")
    # The task writes the running state before its first step.
    await _wait_for(lambda: rig.meta().get(probe.META_PROBE_STATE) == probe.STATE_RUNNING)
    meta = rig.meta()
    assert meta[probe.META_PROBE_STATE] == probe.STATE_RUNNING
    assert meta[probe.META_PROBE_ID] == probe_id
    # No start clears the ownership mark of a fetched file (review WR-08).
    assert meta.get(probe.META_PROBE_FP32_FETCHED, "") == ""
    rig.poller.pass_in_flight = False
    assert rig.run.task is not None
    await asyncio.wait_for(rig.run.task, timeout=20)
    meta = rig.meta()
    assert meta[probe.META_PROBE_STATE] == probe.STATE_DONE
    stored = probe.decode(meta[probe.META_PROBE_RESULT])
    assert stored is not None
    assert (stored.id, stored.verdict, stored.target_profile) == (probe_id, probe.VERDICT_FITS, "standard")


async def test_the_fetched_mark_is_written_before_the_download(tmp_path: Path, small_weights: bytes) -> None:
    del small_weights
    rig = Rig(tmp_path)
    seen: list[str] = []

    class Peek(Fetch):
        async def __call__(self, url: str, write: Callable[[bytes], Awaitable[None]], *, cap: int) -> None:
            seen.append(rig.meta()[probe.META_PROBE_FP32_FETCHED])
            await super().__call__(url, write, cap=cap)

    rig.run._fetch = Peek()
    await rig.check("standard", "fp32")
    assert seen == ["1"]


async def test_a_restart_in_the_middle_reads_as_interrupted(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.poller.pass_in_flight = True
    _, probe_id = await rig.run.start("performance", "int8")
    await _wait_for(lambda: rig.meta().get(probe.META_PROBE_STATE) == probe.STATE_RUNNING)
    # The container dies: the task is gone, the meta says running.
    assert rig.run.task is not None
    rig.run.task.cancel()
    await asyncio.gather(rig.run.task, return_exceptions=True)
    probe.reset()
    restarted = ProbeRun(
        poller=FakePoller(),
        runner=FakeRunner(),
        pool=FakePool(),
        models_dir=rig.models,
        fetch=Fetch(),
        rebuild_may_start=lambda: True,
        engine_loaded=lambda: True,
        cutter_built=lambda: True,
        embed_slots=lambda: 0,
        state_path=rig.state,
    )
    await restarted.restore()
    snap = probe.snapshot()
    assert (snap.id, snap.state) == (probe_id, probe.STATE_DONE)
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "interrupted")
    assert snap.target_profile == "performance"
    meta = rig.meta()
    assert meta[probe.META_PROBE_STATE] == probe.STATE_DONE
    stored = probe.decode(meta[probe.META_PROBE_RESULT])
    assert stored is not None
    assert stored.cause == "interrupted"


async def test_a_restart_after_a_finished_check_brings_its_result_back(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    done = await rig.check()
    probe.reset()
    await rig.run.restore()
    assert probe.snapshot() == done


async def test_restore_without_a_state_db_does_nothing(tmp_path: Path) -> None:
    run = ProbeRun(
        poller=FakePoller(),
        runner=FakeRunner(),
        pool=FakePool(),
        models_dir=tmp_path,
        fetch=Fetch(),
        rebuild_may_start=lambda: True,
        engine_loaded=lambda: True,
        cutter_built=lambda: True,
        embed_slots=lambda: 0,
        state_path=tmp_path / "missing.db",
    )
    await run.restore()
    assert probe.snapshot().state == probe.STATE_IDLE
    assert not (tmp_path / "missing.db").exists()


def _choices(*answers: CompanionChoice | None) -> tuple[Callable[[], Awaitable[CompanionChoice | None]], list[int]]:
    calls = [0]

    async def read() -> CompanionChoice | None:
        index = min(calls[0], len(answers) - 1)
        calls[0] += 1
        return answers[index]

    return read, calls


def _fetched_mark(rig: Rig, payload: bytes) -> Path:
    target = _placed(rig, payload)
    rig.write_meta(
        {
            probe.META_PROBE_STATE: probe.STATE_DONE,
            probe.META_PROBE_ID: "0123456789abcdef",
            probe.META_PROBE_FP32_FETCHED: "1",
        }
    )
    return target


async def test_recover_removes_the_fetched_file_when_the_key_says_int8(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    target = _fetched_mark(rig, PAYLOAD)
    read, calls = _choices(CompanionChoice(profile="standard", precision="int8"))
    await asyncio.wait_for(rig.run.recover(read, retry=0.01), timeout=5)
    assert calls[0] == 1
    assert not target.exists()
    assert rig.meta()[probe.META_PROBE_FP32_FETCHED] == ""


async def test_recover_keeps_the_file_when_the_key_says_fp32(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    target = _fetched_mark(rig, PAYLOAD)
    read, _ = _choices(CompanionChoice(profile="standard", precision="fp32"))
    await asyncio.wait_for(rig.run.recover(read, retry=0.01), timeout=5)
    assert target.exists()
    assert rig.meta()[probe.META_PROBE_FP32_FETCHED] == ""


async def test_recover_waits_for_a_read_and_deletes_nothing_before(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    target = _fetched_mark(rig, PAYLOAD)
    read, calls = _choices(None)
    task = asyncio.create_task(rig.run.recover(read, retry=0.01))
    await _wait_for(lambda: calls[0] >= 3)
    assert target.exists()
    await rig.run.close()
    await asyncio.wait_for(task, timeout=5)
    assert target.exists()
    assert rig.meta()[probe.META_PROBE_FP32_FETCHED] == "1"


async def test_recover_retries_after_a_failed_read(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    target = _fetched_mark(rig, PAYLOAD)
    calls = [0]

    async def read() -> CompanionChoice | None:
        calls[0] += 1
        if calls[0] == 1:
            raise ConnectionError
        return CompanionChoice(profile=None, precision="int8")

    await asyncio.wait_for(rig.run.recover(read, retry=0.01), timeout=5)
    assert calls[0] == 2
    assert not target.exists()


async def test_a_later_start_keeps_the_mark_and_a_nofit_removes_the_kept_file(
    tmp_path: Path, small_weights: bytes
) -> None:
    """Review WR-08 (b): the mark of a fetched file outlives the check that set it.

    A later start used to clear probe_fp32_fetched, so the next fp32 check found
    the file, took the digest path, called it placed by the admin and never
    removed it on nofit, against D-27-17.
    """
    rig = Rig(tmp_path)
    target = _fetched_mark(rig, small_weights)
    snap = await rig.check("standard", "int8")
    assert snap.verdict == probe.VERDICT_FITS
    assert rig.meta()[probe.META_PROBE_FP32_FETCHED] == "1"

    rig.measures.answers["fp32"] = ModelMeasure(model_probe.MEASURE_KILLED, 0, 0, 0)
    snap = await rig.check("standard", "fp32")
    assert snap.verdict == probe.VERDICT_NOFIT
    assert rig.fetch.calls == 0
    assert not target.exists()
    assert snap.fp32_deleted
    assert rig.meta()[probe.META_PROBE_FP32_FETCHED] == ""


async def test_a_placed_file_without_the_mark_still_stays_on_nofit(tmp_path: Path, small_weights: bytes) -> None:
    rig = Rig(tmp_path)
    target = _placed(rig, small_weights)
    rig.measures.answers["fp32"] = ModelMeasure(model_probe.MEASURE_KILLED, 0, 0, 0)
    snap = await rig.check("standard", "fp32")
    assert snap.verdict == probe.VERDICT_NOFIT
    assert target.exists()
    assert not snap.fp32_deleted


async def test_the_sweep_follows_a_fits_that_kept_a_fetched_file(tmp_path: Path, small_weights: bytes) -> None:
    """Review WR-08 (a): a kept file is swept after the check, not only at the next start.

    Once the grace for the take-over is over and the key still says int8, the
    file goes; before that it stays for PHP to store fp32.
    """
    del small_weights
    rig = Rig(tmp_path, takeover_seconds=0.3, takeover_poll=0.02)
    read, calls = _choices(CompanionChoice(profile="standard", precision="int8"))
    # The lifespan read the companion once, with nothing to sweep.
    await rig.run.recover(read, retry=0.01)
    assert calls[0] == 0

    snap = await rig.check("standard", "fp32")
    assert snap.verdict == probe.VERDICT_FITS
    target = weights.fp32_weights_path(rig.models)
    assert target.exists()
    await _wait_for(lambda: calls[0] >= 1)
    assert target.exists(), "removed inside the grace of the take-over"
    await _wait_for(lambda: not target.exists())
    # The sweep removes the file first and clears the mark after it, so the
    # mark can trail the file by one write.
    await _wait_for(lambda: rig.meta()[probe.META_PROBE_FP32_FETCHED] == "")
    assert probe.snapshot().fp32_deleted
    await rig.run.close()


async def test_the_sweep_clears_the_mark_when_php_stored_fp32(tmp_path: Path, small_weights: bytes) -> None:
    del small_weights
    rig = Rig(tmp_path, takeover_seconds=60, takeover_poll=0.02)
    answers = [CompanionChoice(profile="standard", precision="int8")]
    calls = [0]

    async def read() -> CompanionChoice | None:
        calls[0] += 1
        return answers[-1]

    await rig.run.recover(read, retry=0.01)
    await rig.check("standard", "fp32")
    await _wait_for(lambda: calls[0] >= 1)
    answers.append(CompanionChoice(profile="standard", precision="fp32"))
    await _wait_for(lambda: rig.meta()[probe.META_PROBE_FP32_FETCHED] == "")
    assert weights.fp32_weights_path(rig.models).exists()
    await rig.run.close()


async def test_recover_after_a_restart_keeps_a_fits_php_may_still_take_over(tmp_path: Path) -> None:
    """Review WR-08 (c): a restart between "fits" and the take-over deletes nothing."""
    rig = Rig(tmp_path, takeover_seconds=3000)
    target = _fetched_mark(rig, PAYLOAD)
    fits = replace(
        probe.snapshot(),
        id="0123456789abcdef",
        state=probe.STATE_DONE,
        verdict=probe.VERDICT_FITS,
        target_profile="standard",
        target_precision="fp32",
        fp32_fetched=True,
        started_at=time.time() - 60,
        finished_at=time.time() - 30,
    )
    rig.write_meta({probe.META_PROBE_RESULT: probe.encode(fits)})
    probe.reset()
    await rig.run.restore()
    read, calls = _choices(CompanionChoice(profile="standard", precision="int8"))
    task = asyncio.create_task(rig.run.recover(read, retry=0.01))
    await _wait_for(lambda: calls[0] >= 1)
    await asyncio.sleep(0.05)
    assert target.exists()
    await rig.run.close()
    await asyncio.wait_for(task, timeout=5)
    assert target.exists()
    assert rig.meta()[probe.META_PROBE_FP32_FETCHED] == "1"


def test_the_grace_of_the_take_over_is_the_stale_bound_of_php() -> None:
    """PROBE_TAKEOVER_SECONDS and PENDING_STALE_SECONDS of ProbeService.php are one figure."""
    php = (TEMPLATE.parents[1] / "lib" / "Service" / "ProbeService.php").read_text(encoding="utf-8")
    bound = re.search(r"private const PENDING_STALE_SECONDS = (\d+);", php)
    assert bound is not None
    assert int(bound.group(1)) == PROBE_TAKEOVER_SECONDS


async def test_recover_without_the_mark_reads_nothing(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    target = _placed(rig, PAYLOAD)
    read, calls = _choices(CompanionChoice(profile=None, precision="int8"))
    await rig.run.recover(read, retry=0.01)
    assert calls[0] == 0
    assert target.exists()


async def test_the_check_never_writes_the_pass_mark(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    profile.note_hardware(_big_box())
    profile.note_chosen("economy")
    before = profile.snapshot()
    await rig.check("performance", "int8")
    meta = rig.meta()
    assert meta.get(guard.META_MULTI_SLOT_PASS, "") == ""
    assert meta.get(guard.META_MULTI_SLOT_CHOSEN, "") == ""
    assert profile.snapshot() == before
    assert guard.snapshot().cap is None


async def test_without_persistence_nothing_is_written(tmp_path: Path) -> None:
    rig = Rig(tmp_path, persist=False)
    await rig.check()
    assert probe.META_PROBE_STATE not in rig.meta()


# -- task 2: model children, samples, calculation, the N run, the cap --------


async def test_an_unreadable_headroom_starts_no_child(tmp_path: Path, small_weights: bytes) -> None:
    del small_weights
    rig = Rig(tmp_path)
    rig.headroom.base = None
    snap = await rig.check("standard", "fp32")
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, probe.CAUSE_MEMORY_UNKNOWN)
    assert rig.workers.made == []
    assert rig.measures.calls == []


async def test_too_little_headroom_for_the_first_slot_starts_no_child(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.headroom.base = OCR_SLOT_COST_BYTES + GUARD_RESERVE_BYTES - 1
    snap = await rig.check()
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, probe.CAUSE_MEMORY_SHORT)
    assert rig.workers.made == []


async def test_too_little_headroom_for_the_model_child_starts_none(tmp_path: Path, small_weights: bytes) -> None:
    rig = Rig(tmp_path)
    _placed(rig, small_weights)
    rig.headroom.base = MODEL_PROBE_CHILD_BYTES + GUARD_RESERVE_BYTES - 1
    snap = await rig.check("standard", "fp32")
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, probe.CAUSE_MODEL_MEMORY)
    assert rig.measures.calls == []
    assert rig.workers.made == []


class JudgeSpy:
    def __init__(self) -> None:
        self.calls: list[dict[str, int]] = []
        self._judge = probe.judge

    def __call__(self, **kwargs: int) -> probe.Verdict:
        self.calls.append(kwargs)
        return self._judge(**kwargs)


@pytest.fixture
def judge(monkeypatch: pytest.MonkeyPatch) -> JudgeSpy:
    spy = JudgeSpy()
    monkeypatch.setattr(probe, "judge", spy)
    return spy


async def test_the_model_children_run_int8_then_fp32_and_feed_the_calculation(
    tmp_path: Path, small_weights: bytes, judge: JudgeSpy
) -> None:
    rig = Rig(tmp_path)
    _placed(rig, small_weights)
    rig.measures.answers["fp32"] = ModelMeasure(model_probe.MEASURE_OK, 300 * MIB, 1_000 * MIB, 1500)
    snap = await rig.check("standard", "fp32")
    assert rig.measures.calls == ["int8", "fp32"]
    assert judge.calls[0]["model_extra"] == max((700 - 150) * MIB, FP32_EXTRA_BYTES)
    assert snap.numbers["rateInt8"] == 4000
    assert snap.numbers["rateFp32"] == 1500


async def test_a_small_fp32_delta_counts_as_the_constant(tmp_path: Path, small_weights: bytes, judge: JudgeSpy) -> None:
    rig = Rig(tmp_path)
    _placed(rig, small_weights)
    rig.measures.answers["fp32"] = ModelMeasure(model_probe.MEASURE_OK, 300 * MIB, 500 * MIB, 1500)
    await rig.check("standard", "fp32")
    assert judge.calls[0]["model_extra"] == FP32_EXTRA_BYTES


@pytest.mark.parametrize(
    ("outcome", "cause"),
    [
        (model_probe.MEASURE_TIMEOUT, "timeout"),
        (model_probe.MEASURE_KILLED, "slot_killed"),
        (model_probe.MEASURE_NO_MEMORY, probe.CAUSE_MODEL_MEMORY),
        (model_probe.MEASURE_FAILED, "probe_failed"),
    ],
)
async def test_the_end_of_a_model_child_maps_onto_a_cause(
    tmp_path: Path, small_weights: bytes, outcome: str, cause: str
) -> None:
    rig = Rig(tmp_path)
    _placed(rig, small_weights)
    rig.measures.answers["int8"] = ModelMeasure(outcome, 0, 0, 0)
    snap = await rig.check("standard", "fp32")
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, cause)
    assert rig.measures.calls == ["int8"]
    assert rig.workers.made == []


TEMPLATE = Path(__file__).resolve().parents[2] / "php" / "templates" / "admin.php"


def _cause_needs() -> dict[str, list[str]]:
    """The figures each cause sentence needs, read out of $probeCauseNeeds of the template."""
    block = re.search(r"\$probeCauseNeeds = \[(.*?)\];", TEMPLATE.read_text(encoding="utf-8"), re.DOTALL)
    assert block is not None
    return {
        code: re.findall(r"'([a-zA-Z0-9]+)'", keys)
        for code, keys in re.findall(r"'([a-z_]+)' => \[([^\]]*)\]", block.group(1))
    }


def _assert_the_cause_can_be_said(snap: probe.ProbeSnapshot) -> None:
    """A verdict whose cause sentence would have a hole is a verdict without a named cause."""
    assert snap.cause != ""
    missing = [key for key in _cause_needs().get(snap.cause, []) if key not in snap.numbers]
    assert missing == [], (snap.cause, missing)


@pytest.mark.parametrize("child", ["int8", "fp32"])
@pytest.mark.parametrize(
    "outcome",
    [
        model_probe.MEASURE_TIMEOUT,
        model_probe.MEASURE_KILLED,
        model_probe.MEASURE_NO_MEMORY,
        model_probe.MEASURE_FAILED,
    ],
)
async def test_the_end_of_a_model_child_carries_the_figures_of_its_sentence(
    tmp_path: Path, small_weights: bytes, child: str, outcome: str
) -> None:
    rig = Rig(tmp_path)
    _placed(rig, small_weights)
    rig.measures.answers[child] = ModelMeasure(outcome, 0, 0, 0)
    snap = await rig.check("standard", "fp32")
    assert snap.verdict == probe.VERDICT_NOFIT
    _assert_the_cause_can_be_said(snap)


async def test_every_nofit_path_of_the_orchestrator_carries_the_figures_of_its_sentence(
    tmp_path: Path, small_weights: bytes
) -> None:
    """The paths outside the model child, one rig each, held against the same map."""

    def unreadable(rig: Rig) -> None:
        rig.headroom.base = None

    def short_for_the_first_slot(rig: Rig) -> None:
        rig.headroom.base = OCR_SLOT_COST_BYTES + GUARD_RESERVE_BYTES - 1

    def short_for_the_model_child(rig: Rig) -> None:
        _placed(rig, small_weights)
        rig.headroom.base = MODEL_PROBE_CHILD_BYTES + GUARD_RESERVE_BYTES - 1

    def hanging_child(rig: Rig) -> None:
        rig.workers.hang = True

    def timed_out_child(rig: Rig) -> None:
        rig.workers.results = lambda _index: ExtractionOutcome.failed(Reason.TIMEOUT)

    def killed_child(rig: Rig) -> None:
        rig.workers.results = lambda _index: ChildKilled(engine=False)

    def foreign_placed_file(rig: Rig) -> None:
        _placed(rig, b"not the recorded weights")

    def nothing(rig: Rig) -> None:
        del rig

    scenarios: list[tuple[str, Callable[[Rig], None], str, dict[str, object]]] = [
        ("memory_unknown", unreadable, "int8", {}),
        ("first_slot", short_for_the_first_slot, "int8", {}),
        ("model_gate", short_for_the_model_child, "fp32", {}),
        ("ocr_timeout", hanging_child, "int8", {"measure_seconds": 0.3}),
        ("ocr_sandbox_timeout", timed_out_child, "int8", {}),
        ("ocr_killed", killed_child, "int8", {}),
        ("digest", foreign_placed_file, "fp32", {}),
        ("download_slow", nothing, "fp32", {"download_seconds": 0.2, "fetch": Fetch(hang=True)}),
    ]
    for name, prepare, precision, overrides in scenarios:
        probe.reset()
        weights.forget_verdicts()
        where = tmp_path / name
        where.mkdir()
        rig = Rig(where, **overrides)
        prepare(rig)
        snap = await rig.check("standard", precision)
        assert snap.verdict == probe.VERDICT_NOFIT, name
        _assert_the_cause_can_be_said(snap)


async def test_the_one_child_reads_the_verified_scan_page(tmp_path: Path, judge: JudgeSpy) -> None:
    rig = Rig(tmp_path)
    rig.workers.costs = lambda index: 400 * MIB if index == 0 else 300 * MIB
    await rig.check("standard", "int8")
    path, mime, size, route, timeout = rig.workers.calls[0]
    assert Path(path).name == probe.PROBE_SCAN_NAME
    assert (mime, size, route) == ("application/pdf", probe.PROBE_SCAN_BYTES, "ocr")
    assert timeout is not None
    assert 0 < timeout <= 120
    # The slot cost is the headroom before the child less the lowest sample.
    assert judge.calls[0]["slot_cost"] == 400 * MIB
    assert judge.calls[0]["headroom"] == BIG


async def test_a_scan_page_with_another_digest_is_probe_failed(tmp_path: Path) -> None:
    forged = tmp_path / "forged.pdf"
    forged.write_bytes(b"%PDF-1.4 not the shipped page")
    rig = Rig(tmp_path, scan=lambda: forged)
    snap = await rig.check()
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "probe_failed")
    assert rig.workers.calls == []


async def test_a_narrow_calculation_ends_without_the_n_run(
    tmp_path: Path, steps: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = Rig(tmp_path)
    monkeypatch.setattr(
        probe,
        "judge",
        lambda **_kwargs: probe.Verdict(probe.VERDICT_NARROW, probe.CAUSE_RESERVE_THIN, {"reserve": 1, "required": 2}),
    )
    snap = await rig.check()
    assert "ocr_n" not in steps
    assert snap.verdict == probe.VERDICT_NARROW
    assert len(rig.workers.made) == 1


async def test_a_short_calculation_is_memory_short_without_the_n_run(tmp_path: Path, steps: list[str]) -> None:
    rig = Rig(tmp_path)
    # One slot fits, four do not.
    rig.headroom.base = 2 * (OCR_SLOT_COST_BYTES + GUARD_RESERVE_BYTES)
    rig.workers.costs = lambda _index: OCR_SLOT_COST_BYTES
    snap = await rig.check("standard", "int8")
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, probe.CAUSE_MEMORY_SHORT)
    assert snap.numbers["slots"] == 4
    assert "ocr_n" not in steps


async def test_one_slot_skips_the_n_run(tmp_path: Path, steps: list[str]) -> None:
    rig = Rig(tmp_path)
    snap = await rig.check("economy", "int8")
    assert steps == ["pause", "ocr_one", "calc", "cleanup"]
    assert snap.verdict == probe.VERDICT_FITS
    assert len(rig.workers.made) == 1


async def test_the_n_run_starts_n_fresh_children_in_parallel(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.workers.seconds = 0.2
    started = time.monotonic()
    snap = await rig.check("standard", "int8")
    slots = profile.resolve(Profile.STANDARD, _big_box()).values.ocr_slots
    assert len(rig.workers.made) == 1 + slots
    assert all(worker.stopped == 1 for worker in rig.workers.made)
    assert time.monotonic() - started < 0.2 * (1 + slots)
    assert snap.verdict == probe.VERDICT_FITS
    assert snap.numbers["slots"] == slots


@pytest.mark.parametrize(
    "result",
    [ChildKilled(engine=False), ChildKilled(engine=True), ExtractionOutcome.failed(Reason.OUT_OF_MEMORY)],
)
async def test_a_killed_child_in_the_n_run_is_slot_killed(
    tmp_path: Path, result: ExtractionOutcome | BaseException
) -> None:
    rig = Rig(tmp_path)
    rig.workers.results = lambda index: result if index == 2 else ExtractionOutcome.indexed("text")
    snap = await rig.check("standard", "int8")
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "slot_killed")
    assert guard.take_child_kills() == 0


async def test_a_deep_dip_in_the_n_run_is_narrow(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.headroom.base = 4 * GIB
    # The one child costs little, the parallel ones far more than it said.
    rig.workers.costs = lambda index: 300 * MIB if index == 0 else 900 * MIB
    # The dip only shows while the parallel children overlap; 50 ms each let a
    # loaded runner start them one after the other and miss it (seen once in a
    # full run), so they hold their cost long enough to overlap for certain.
    rig.workers.seconds = 0.5
    snap = await rig.check("standard", "int8")
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NARROW, probe.CAUSE_RESERVE_THIN)
    assert snap.numbers["required"] == GUARD_RESERVE_BYTES


async def test_a_child_over_the_measure_cap_is_timeout_and_every_child_stops(tmp_path: Path) -> None:
    rig = Rig(tmp_path, measure_seconds=0.3)
    rig.workers.hang = True
    snap = await rig.check()
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "timeout")
    assert snap.numbers["seconds"] == 1
    assert rig.workers.halts >= 1
    assert all(worker.stopped == 1 for worker in rig.workers.made)
    assert rig.released()


async def test_a_child_the_sandbox_timed_out_is_timeout(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.workers.results = lambda _index: ExtractionOutcome.failed(Reason.TIMEOUT)
    snap = await rig.check()
    assert (snap.verdict, snap.cause) == (probe.VERDICT_NOFIT, "timeout")


async def test_the_slots_come_from_the_resolution_and_the_children_inherit_the_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, judge: JudgeSpy
) -> None:
    without = profile.resolve(Profile.STANDARD, _big_box()).values.ocr_slots
    monkeypatch.setenv("FINDLING_OCR_DPI", "200")
    rig = Rig(tmp_path)
    await rig.check("standard", "int8")
    assert judge.calls[0]["slots"] == without
    assert rig.workers.env == ["200"] * (1 + without)
    assert os.environ["FINDLING_OCR_DPI"] == "200"


async def test_the_pre_check_judges_the_slots_of_the_stock_in_force(tmp_path: Path, judge: JudgeSpy) -> None:
    # D-29-12, wanted: after the wiring the pre-check sees the smaller slot
    # count of a big stock. Three million files are 17,578 MiB of main process,
    # which leaves the 64 GB box two Standard slots instead of four.
    without = profile.resolve(Profile.STANDARD, _big_box()).values.ocr_slots
    profile.note_index_files(3_000_000)
    with_stock = profile.resolve(Profile.STANDARD, _big_box(), index_files=3_000_000).values.ocr_slots
    assert (without, with_stock) == (4, 2)
    rig = Rig(tmp_path)
    await rig.check("standard", "int8")
    assert judge.calls[0]["slots"] == with_stock


async def test_the_pending_costs_count_the_growth_of_the_writer_heap(tmp_path: Path, judge: JudgeSpy) -> None:
    rig = Rig(tmp_path, embed_slots=lambda: 1, engine_loaded=lambda: False, cutter_built=lambda: False)
    await rig.check("performance", "int8")
    values = profile.resolve(Profile.PERFORMANCE, _big_box()).values
    in_force = profile.snapshot().resolution.values
    expected = probe.pending_load_bytes(
        cutter_built=False,
        engine_loaded=False,
        fp32=False,
        embed_slots=values.embed_slots - 1,
        writer_heap_delta=values.writer_heap_bytes - in_force.writer_heap_bytes,
    )
    assert judge.calls[0]["pending"] == expected
    assert judge.calls[0]["model_extra"] == 0


ONLY_LINUX_WITH_TESSERACT = pytest.mark.skipif(
    sys.platform != "linux" or shutil.which("tesseract") is None,
    reason="a real OCR child needs Linux and tesseract, as in the container",
)


@ONLY_LINUX_WITH_TESSERACT
async def test_a_real_child_reads_the_scan_page(tmp_path: Path) -> None:
    outcomes: list[ExtractionOutcome] = []

    class Recording(ExtractionWorker):
        def run(
            self, path: str, mime: str, size: int, *, route: str | None = None, timeout_seconds: float | None = None
        ) -> ExtractionOutcome:
            outcome = super().run(path, mime, size, route=route, timeout_seconds=timeout_seconds)
            outcomes.append(outcome)
            return outcome

    rig = Rig(tmp_path, worker_factory=Recording)
    snap = await rig.check("economy", "int8")
    assert snap.verdict == probe.VERDICT_FITS
    assert len(outcomes) == 1
    assert outcomes[0].text.strip()
