"""The pre-check of a profile change as a task of its own (PRUEF-01, SC3).

findling.probe holds the codes, the calculation and the state without I/O; this
module is the I/O around it. A check runs as one background task in the fixed
order of probe.STEPS and reports every step through probe.note_step, so no
caller ever waits for the verdict (D-27-04):

1. **pause** holds the poller and the embed runner with their own hold signal
   (never silence or arm, those belong to the enabled handler and the
   lifespan), sets probe.hold, gives the idle children of the pool back and
   waits at most PROBE_PAUSE_SECONDS for the pass and the round in flight
   (D-27-05, D-27-16). The hold is lifted in the finally of the task, on every
   way out, a cancellation included.
2. **download** or **digest**, only for fp32 as the target while int8 is in
   force: a file the admin placed is checked with fp32_verified, otherwise
   procure_fp32 fetches it under PROBE_DOWNLOAD_SECONDS with a byte count
   (D-27-02, D-27-06). The procurement state of the embedding track stays
   untouched: this fetch is the check's own, not the one of the track.
3. **model**, **ocr_one**, **calc**, **ocr_n** under one cap of
   PROBE_MEASURE_SECONDS: the model children int8 and fp32 behind their gate,
   one fresh OCR child on the shipped scan page with headroom samples in a
   daemon thread, the calculation of probe.judge, and N fresh children in
   parallel only when the calculation fits (D-27-06, D-27-07). Every child gets
   the time left as its own deadline, so the sandbox kills it itself.
4. **cleanup** deletes an fp32 file the check fetched itself when the verdict is
   narrow or nofit, and never one the admin placed (D-27-17). On fits the file
   stays; PHP activates it through the key (D-27-02).

A child the kernel kills is nofit slot_killed. The check never writes the pass
mark of the guard and never lowers the chosen profile (D-27-15); the guard
suspends its lowering while probe.held() (findling/worker/watch.py).

**Restart.** State and result live in the meta table of state.db. A start that
finds the state running says nofit interrupted (restore). An fp32 file the check
fetched is deleted only after the first successful read of the companion, and
only when the key then says int8 (recover, 27-RESEARCH.md Pitfall 7).

House rules of the guard task (findling/worker/watch.py): nothing is opened in
the constructor, every reader and clock is injectable, every exception is
caught and logged with its type name only. State.db is reached through a
connection of its own under a lock through asyncio.to_thread, never through the
connection of the poller, and never created here. Waits on children run in
threads of their own and never in the default executor (findling/extract/pool.py,
issue #19). Logs carry step and cause codes, never a path, a URL or a token.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import contextlib
import hashlib
import logging
import math
import re
import secrets
import threading
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import replace
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Protocol

from findling import memory_guard, probe, profile
from findling.config import (
    FP32_EXTRA_BYTES,
    GUARD_RESERVE_BYTES,
    MODEL_PROBE_CHILD_BYTES,
    OCR_SLOT_COST_BYTES,
    PROBE_DOWNLOAD_SECONDS,
    PROBE_MEASURE_SECONDS,
    PROBE_PAUSE_SECONDS,
    PROBE_SAMPLE_SECONDS,
    settings,
)
from findling.embed import model_probe, weights
from findling.extract.errors import ChildKilled, ExtractionOutcome, Reason, State
from findling.extract.sandbox import ExtractionWorker
from findling.nc.client import fetch_release_asset
from findling.profile import Profile
from findling.store.repo import Store, open_store

if TYPE_CHECKING:
    from importlib.resources.abc import Traversable

    from findling.hardware import Hardware
    from findling.nc.queue import CompanionChoice

LOGGER = logging.getLogger("findling.worker.probe_run")

START_STARTED: Final = "started"

_INT8: Final = "int8"
_FP32: Final = "fp32"

# The tick of the pause loop, the one Poller.stand_down waits with.
_TICK_SECONDS: Final = 0.05

# How long recover waits between two reads of the companion that gave nothing.
RECOVER_RETRY_SECONDS: Final = 5.0

# The scan page is a PDF, and it takes the OCR route of the poller.
_SCAN_MIME: Final = "application/pdf"
_OCR_ROUTE: Final = "ocr"

_ID_PATTERN: Final = re.compile(r"[0-9a-f]{16}")

# The model child: the parent's words for its end, mapped onto the causes.
_MODEL_CAUSES: Final = MappingProxyType(
    {
        model_probe.MEASURE_TIMEOUT: "timeout",
        model_probe.MEASURE_KILLED: "slot_killed",
        model_probe.MEASURE_NO_MEMORY: probe.CAUSE_MODEL_MEMORY,
        model_probe.MEASURE_FAILED: "probe_failed",
    }
)

# procure_fp32 outcomes other than procured, mapped onto the causes.
_PROCURE_CAUSES: Final = MappingProxyType(
    {
        weights.UNAVAILABLE: "download_failed",
        weights.WRONG_DIGEST: "digest_mismatch",
        weights.NO_ROOM: "disk_short",
    }
)


class _Holdable(Protocol):
    def hold_for_probe(self) -> None: ...

    def release_probe_hold(self) -> None: ...


class PollerLike(_Holdable, Protocol):
    """What the check needs of the poller."""

    @property
    def pass_in_flight(self) -> bool: ...


class RunnerLike(_Holdable, Protocol):
    """What the check needs of the embed runner."""

    parked: asyncio.Event


class PoolLike(Protocol):
    """What the check needs of the slot pool."""

    def shed_idle(self) -> int: ...


class WorkerLike(Protocol):
    """What the check needs of an extraction worker."""

    def run(
        self, path: str, mime: str, size: int, *, route: str | None = None, timeout_seconds: float | None = None
    ) -> ExtractionOutcome: ...

    def halt(self) -> None: ...

    def stop(self) -> None: ...


class ModelMeasureFn(Protocol):
    """The shape of findling.embed.model_probe.measure."""

    def __call__(
        self, precision: model_probe.Precision, models_dir: Path, *, timeout_seconds: float
    ) -> model_probe.ModelMeasure: ...


class _Ended(Exception):
    """A step reached a verdict; the rest of the steps is skipped."""

    def __init__(self, verdict: probe.Verdict) -> None:
        super().__init__(verdict.cause)
        self.verdict = verdict


def _nofit(cause: str, numbers: Mapping[str, int] | None = None) -> _Ended:
    return _Ended(probe.Verdict(probe.VERDICT_NOFIT, cause, MappingProxyType(dict(numbers or {}))))


def _seconds(value: float) -> int:
    return max(1, math.ceil(value))


def _in_thread[T](function: Callable[..., T], *args: object) -> concurrent.futures.Future[T]:
    """Run ``function`` in a daemon thread of its own, never in the default executor."""
    future: concurrent.futures.Future[T] = concurrent.futures.Future()

    def body() -> None:
        if not future.set_running_or_notify_cancel():
            return
        try:
            future.set_result(function(*args))
        # Deliberately everything, the future carries it to the awaiting side.
        except BaseException as error:
            future.set_exception(error)

    threading.Thread(target=body, name="findling-probe", daemon=True).start()
    return future


async def _off_loop[T](function: Callable[..., T], *args: object) -> T:
    return await asyncio.wrap_future(_in_thread(function, *args))


async def _settle(futures: Sequence[concurrent.futures.Future[Any]]) -> None:
    """Wait until every thread of a step has returned, whatever the step did."""
    pending = [future for future in futures if not future.done()]
    if pending:
        await _off_loop(concurrent.futures.wait, pending)


class _Sampler:
    """Headroom samples in a daemon thread: the lowest value and whether one was unreadable."""

    def __init__(self, headroom: Callable[[], int | None], interval: float) -> None:
        self._headroom = headroom
        self._interval = interval
        self._stop = threading.Event()
        self.minimum: int | None = None
        self.unreadable = False
        self._thread = threading.Thread(target=self._loop, name="findling-probe-sampler", daemon=True)

    def _take(self) -> None:
        try:
            value = self._headroom()
        # A reader that throws is an unreadable headroom, never a crash of the thread.
        except Exception:
            value = None
        if value is None:
            self.unreadable = True
        elif self.minimum is None or value < self.minimum:
            self.minimum = value

    def _loop(self) -> None:
        while True:
            self._take()
            if self._stop.wait(self._interval):
                break
        self._take()

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join()


def _child_cause(result: object) -> str:
    """The cause a finished OCR child stands for, "" when it read the page."""
    if isinstance(result, ChildKilled):
        return "slot_killed"
    if isinstance(result, ExtractionOutcome):
        if result.reason is Reason.OUT_OF_MEMORY:
            return "slot_killed"
        if result.reason is Reason.TIMEOUT:
            return "timeout"
        if result.state is State.INDEXED:
            return ""
    return "probe_failed"


def _worst(causes: Sequence[str]) -> str:
    for cause in ("slot_killed", "timeout", "probe_failed"):
        if cause in causes:
            return cause
    return ""


def _default_hardware() -> Hardware | None:
    return profile.snapshot().hardware


class ProbeRun:
    """The pre-check task: start, run, restore after a restart, recover, close.

    ``persist`` False keeps the result in memory only, for a volume that
    belongs to another instance (DI-06.1-22), like GuardWatch.
    """

    def __init__(
        self,
        *,
        poller: PollerLike,
        runner: RunnerLike,
        pool: PoolLike,
        models_dir: Path,
        rebuild_may_start: Callable[[], bool],
        engine_loaded: Callable[[], bool],
        cutter_built: Callable[[], bool],
        embed_slots: Callable[[], int],
        # The fetch of the release asset by default; it runs only inside a
        # check an admin started, never at the start of the container (D-24-05).
        fetch: weights.FetchAsset = fetch_release_asset,
        state_path: Path | None = None,
        persist: bool = True,
        headroom: Callable[[], int | None] = memory_guard.headroom_bytes,
        worker_factory: Callable[[], WorkerLike] = ExtractionWorker,
        model_measure: ModelMeasureFn = model_probe.measure,
        hardware: Callable[[], Hardware | None] = _default_hardware,
        scan: Callable[[], Traversable] = probe.probe_scan_path,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], float] = time.time,
        pause_seconds: float = PROBE_PAUSE_SECONDS,
        download_seconds: float = PROBE_DOWNLOAD_SECONDS,
        measure_seconds: float = PROBE_MEASURE_SECONDS,
        sample_seconds: float = PROBE_SAMPLE_SECONDS,
        min_free_bytes: int | None = None,
    ) -> None:
        self._poller = poller
        self._runner = runner
        self._pool = pool
        self._models_dir = models_dir
        self._fetch = fetch
        self._rebuild_may_start = rebuild_may_start
        self._engine_loaded = engine_loaded
        self._cutter_built = cutter_built
        # The parallel embed slots the box runs right now; their activations
        # are held already, so only a growth counts as pending.
        self._embed_slots = embed_slots
        self._state_path = state_path
        self._persist = persist
        self._headroom = headroom
        self._worker_factory = worker_factory
        self._model_measure = model_measure
        self._hardware = hardware
        self._scan = scan
        self._clock = clock
        self._wall_clock = wall_clock
        self._pause_seconds = pause_seconds
        self._download_seconds = download_seconds
        self._measure_seconds = measure_seconds
        self._sample_seconds = sample_seconds
        self._min_free_bytes = min_free_bytes
        self._start_lock = asyncio.Lock()
        self._closed = asyncio.Event()
        self._store: Store | None = None
        self._store_lock = threading.Lock()
        # Whether the running check fetched the fp32 file itself.
        self._fetched = False
        self.task: asyncio.Task[None] | None = None

    # -- state.db --------------------------------------------------------

    def _path(self) -> Path:
        return self._state_path if self._state_path is not None else settings().state_db

    def _open(self) -> Store | None:
        if not self._persist:
            return None
        if self._store is None:
            path = self._path()
            if not path.exists():
                return None
            self._store = open_store(path)
        return self._store

    def _read_meta_sync(self) -> dict[str, str]:
        with self._store_lock:
            store = self._open()
            return {} if store is None else store.read_meta()

    def _write_meta_sync(self, values: Mapping[str, str]) -> None:
        with self._store_lock:
            store = self._open()
            if store is None:
                return
            for key, value in values.items():
                store.write_meta(key, value)

    async def _read_meta(self) -> dict[str, str]:
        try:
            return await asyncio.to_thread(self._read_meta_sync)
        except Exception as error:
            LOGGER.warning("the pre-check could not read its state, %s", type(error).__name__)
            return {}

    async def _write_meta(self, values: Mapping[str, str]) -> None:
        try:
            await asyncio.to_thread(self._write_meta_sync, values)
        except Exception as error:
            LOGGER.warning("the pre-check could not write its state, %s", type(error).__name__)

    # -- start and stop ----------------------------------------------------

    def _running(self) -> bool:
        return self.task is not None and not self.task.done()

    async def start(self, profile_name: str, precision: str) -> tuple[str, str]:
        """Start a check; ("started", id), ("busy", running id) or ("rebuilding", "")."""
        async with self._start_lock:
            if self._running():
                return (probe.START_BUSY, probe.snapshot().id)
            if not self._rebuild_may_start():
                return (probe.START_REBUILDING, "")
            probe_id = secrets.token_hex(8)
            probe.begin(probe_id, profile_name, precision, self._wall_clock())
            self._fetched = False
            await self._write_meta(
                {
                    probe.META_PROBE_STATE: probe.STATE_RUNNING,
                    probe.META_PROBE_ID: probe_id,
                    probe.META_PROBE_FP32_FETCHED: "",
                    probe.META_PROBE_RESULT: probe.encode(probe.snapshot()),
                }
            )
            LOGGER.info("a pre-check started")
            self.task = asyncio.create_task(self._run(Profile(profile_name), precision))
            return (START_STARTED, probe_id)

    async def close(self) -> None:
        """Cancel a running check; its finally lifts the hold. Idempotent."""
        self._closed.set()
        task = self.task
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        with self._store_lock:
            store, self._store = self._store, None
        if store is not None:
            store.close()

    # -- the run -----------------------------------------------------------

    async def _run(self, target: Profile, precision: str) -> None:
        try:
            try:
                verdict = await self._steps(target, precision)
            except _Ended as ended:
                verdict = ended.verdict
            except asyncio.CancelledError:
                raise
            # Deliberately every exception: a broken check ends as a verdict,
            # never as an unretrieved task exception with the hold still set.
            except Exception as error:
                LOGGER.error("the pre-check ended in an unexpected %s", type(error).__name__)
                verdict = probe.Verdict(probe.VERDICT_NOFIT, "probe_failed", MappingProxyType({}))
            await self._finish(verdict)
        finally:
            # Every way out lifts the hold: verdict, exception, cancellation.
            self._poller.release_probe_hold()
            self._runner.release_probe_hold()
            probe.release()

    async def _finish(self, verdict: probe.Verdict) -> None:
        probe.note_step("cleanup")
        deleted = False
        if self._fetched and verdict.verdict != probe.VERDICT_FITS:
            # Only a file the check fetched itself; a placed one stays (D-27-17).
            try:
                await asyncio.to_thread(weights.remove_fp32_weights, self._models_dir)
                deleted = True
            except OSError as error:
                LOGGER.warning("the pre-check could not remove its fp32 file, %s", type(error).__name__)
        probe.finish(
            verdict.verdict,
            verdict.cause,
            verdict.numbers,
            fp32_fetched=self._fetched,
            fp32_deleted=deleted,
            now=self._wall_clock(),
        )
        await self._write_meta(
            {
                probe.META_PROBE_STATE: probe.STATE_DONE,
                # A fetched file that stays is swept by recover after a restart
                # when the key then says int8.
                probe.META_PROBE_FP32_FETCHED: "1" if self._fetched and not deleted else "",
                probe.META_PROBE_RESULT: probe.encode(probe.snapshot()),
            }
        )
        LOGGER.info("the pre-check ended: verdict=%s cause=%s", verdict.verdict, verdict.cause or "none")

    async def _steps(self, target: Profile, precision: str) -> probe.Verdict:
        await self._pause()
        switch_to_fp32 = precision == _FP32 and profile.snapshot().weights != _FP32
        if switch_to_fp32:
            await self._weights()
        return await self._measure(target, precision, switch_to_fp32=switch_to_fp32)

    # -- pause ---------------------------------------------------------------

    async def _pause(self) -> None:
        probe.note_step("pause")
        self._poller.hold_for_probe()
        self._runner.hold_for_probe()
        probe.hold()
        await _off_loop(self._pool.shed_idle)
        deadline = self._clock() + self._pause_seconds
        while self._poller.pass_in_flight or not self._runner.parked.is_set():
            if self._clock() >= deadline:
                raise _nofit("pause_timeout", {"seconds": _seconds(self._pause_seconds)})
            await asyncio.sleep(_TICK_SECONDS)
        # The children of the pass that just ended are idle now.
        await _off_loop(self._pool.shed_idle)

    # -- download or digest --------------------------------------------------

    async def _weights(self) -> None:
        target = weights.fp32_weights_path(self._models_dir)
        if await asyncio.to_thread(target.exists):
            probe.note_step("digest")
            if not await asyncio.to_thread(weights.fp32_verified, self._models_dir):
                # A placed file that is not the recorded one; it is the admin's and stays.
                raise _nofit("digest_mismatch")
            return
        total = weights.FP32_BYTES
        probe.note_step("download", 0, total)
        self._fetched = True
        await self._write_meta({probe.META_PROBE_FP32_FETCHED: "1"})
        received = 0
        fetch = self._fetch

        async def counted(url: str, write: Callable[[bytes], Awaitable[None]], *, cap: int) -> None:
            async def counting(chunk: bytes) -> None:
                nonlocal received
                await write(chunk)
                received += len(chunk)
                probe.note_step("download", min(received, total), total)

            await fetch(url, counting, cap=cap)

        min_free = settings().min_free_bytes if self._min_free_bytes is None else self._min_free_bytes
        try:
            async with asyncio.timeout(self._download_seconds):
                outcome = await weights.procure_fp32(self._models_dir, counted, min_free_bytes=min_free)
        except TimeoutError:
            # procure_fp32 drops the .part on the cancellation.
            raise _nofit("download_slow", {"seconds": _seconds(self._download_seconds)}) from None
        if outcome != weights.PROCURED:
            raise _nofit(_PROCURE_CAUSES.get(outcome, "download_failed"))

    # -- the measurement -----------------------------------------------------

    def _left(self, deadline: float) -> float:
        return max(0.1, deadline - self._clock())

    async def _admitted_headroom(self) -> int:
        """The headroom now, after the gate of the first OCR slot."""
        headroom = await asyncio.to_thread(self._headroom)
        if headroom is None:
            raise _nofit(probe.CAUSE_MEMORY_UNKNOWN)
        if not probe.first_slot_admitted(headroom):
            raise _nofit(
                probe.CAUSE_MEMORY_SHORT,
                {"slots": 1, "need": OCR_SLOT_COST_BYTES + GUARD_RESERVE_BYTES, "available": headroom},
            )
        return headroom

    async def _measure(self, target: Profile, precision: str, *, switch_to_fp32: bool) -> probe.Verdict:
        deadline = self._clock() + self._measure_seconds
        try:
            async with asyncio.timeout(self._measure_seconds):
                return await self._measured(target, precision, switch_to_fp32=switch_to_fp32, deadline=deadline)
        except TimeoutError:
            raise _nofit("timeout", {"seconds": _seconds(self._measure_seconds)}) from None

    async def _measured(
        self, target: Profile, precision: str, *, switch_to_fp32: bool, deadline: float
    ) -> probe.Verdict:
        headroom = await self._admitted_headroom()
        rates: dict[str, int] = {}
        model_extra = 0
        if switch_to_fp32:
            model_extra = await self._model_step(headroom, deadline, rates)
            headroom = await self._admitted_headroom()

        with resources.as_file(self._scan()) as scan_path:
            data = await asyncio.to_thread(scan_path.read_bytes)
            probe.note_step("ocr_one")
            if hashlib.sha256(data).hexdigest() != probe.PROBE_SCAN_SHA256:
                LOGGER.warning("the scan page of the pre-check does not match its digest")
                raise _nofit("probe_failed")
            minimum = await self._ocr(scan_path, len(data), 1, deadline)
            slot_cost = max(0, headroom - minimum)

            probe.note_step("calc")
            state = profile.snapshot()
            resolution = profile.resolve(target, self._hardware(), weights=precision)
            slots = resolution.values.ocr_slots
            # Pitfall 6: the children read DPI and page cap from the same
            # environment the resolution reads; the page count barely moves the
            # peak, the DPI does, and the measured slot cost carries it.
            pending = probe.pending_load_bytes(
                cutter_built=self._cutter_built(),
                engine_loaded=self._engine_loaded(),
                # The fp32 part of a switch is model_extra; fp32 in force and
                # unloaded is a load of its own that is pending.
                fp32=precision == _FP32 and not switch_to_fp32,
                embed_slots=resolution.values.embed_slots - self._embed_slots(),
                writer_heap_delta=resolution.values.writer_heap_bytes - state.resolution.values.writer_heap_bytes,
            )
            verdict = probe.judge(
                slots=slots, headroom=headroom, slot_cost=slot_cost, pending=pending, model_extra=model_extra
            )
            if verdict.verdict != probe.VERDICT_FITS or slots == 1:
                return probe.Verdict(verdict.verdict, verdict.cause, MappingProxyType({**verdict.numbers, **rates}))

            probe.note_step("ocr_n")
            minimum = await self._ocr(scan_path, len(data), slots, deadline)
        run = probe.judge_run(min_headroom=minimum, pending=pending + model_extra)
        return probe.Verdict(run.verdict, run.cause, MappingProxyType({**run.numbers, "slots": slots, **rates}))

    async def _model_step(self, headroom: int, deadline: float, rates: dict[str, int]) -> int:
        """Both model children, int8 first; returns the extra of fp32 over int8."""
        probe.note_step("model")
        measured: dict[str, model_probe.ModelMeasure] = {}
        current = headroom
        for name, key in ((_INT8, "rateInt8"), (_FP32, "rateFp32")):
            if not probe.model_child_admitted(current):
                raise _nofit(
                    probe.CAUSE_MODEL_MEMORY,
                    {"need": MODEL_PROBE_CHILD_BYTES + GUARD_RESERVE_BYTES, "available": current or 0},
                )
            precision: model_probe.Precision = "int8" if name == _INT8 else "fp32"
            future = _in_thread(self._call_model, precision, self._left(deadline))
            try:
                result = await asyncio.wrap_future(future)
            finally:
                # A cancelled wait leaves the child to its own deadline; the
                # thread is waited for, so no model child outlives the check.
                await _settle([future])
            if result.outcome != model_probe.MEASURE_OK:
                raise _nofit(_MODEL_CAUSES.get(result.outcome, "probe_failed"))
            measured[name] = result
            rates[key] = result.rate_milli
            current = await asyncio.to_thread(self._headroom)
            if current is None:
                raise _nofit(probe.CAUSE_MEMORY_UNKNOWN)
        return max(measured[_FP32].delta - measured[_INT8].delta, FP32_EXTRA_BYTES)

    def _call_model(self, precision: model_probe.Precision, left: float) -> model_probe.ModelMeasure:
        return self._model_measure(precision, self._models_dir, timeout_seconds=left)

    async def _ocr(self, scan_path: Path, size: int, count: int, deadline: float) -> int:
        """``count`` fresh children on the scan page in parallel; the lowest headroom seen."""
        workers = [self._worker_factory() for _ in range(count)]
        sampler = _Sampler(self._headroom, self._sample_seconds)
        sampler.start()
        futures: list[concurrent.futures.Future[ExtractionOutcome]] = []
        try:
            left = self._left(deadline)
            futures = [_in_thread(self._read_scan, worker, str(scan_path), size, left) for worker in workers]
            results = await asyncio.gather(*(asyncio.wrap_future(f) for f in futures), return_exceptions=True)
        finally:
            with contextlib.suppress(Exception):
                await self._stop_children(workers, futures, sampler)
        cause = _worst([_child_cause(result) for result in results])
        if cause == "timeout":
            raise _nofit("timeout", {"seconds": _seconds(self._measure_seconds)})
        if cause:
            raise _nofit(cause)
        if sampler.unreadable or sampler.minimum is None:
            raise _nofit(probe.CAUSE_MEMORY_UNKNOWN)
        return sampler.minimum

    @staticmethod
    def _read_scan(worker: WorkerLike, path: str, size: int, left: float) -> ExtractionOutcome:
        return worker.run(path, _SCAN_MIME, size, route=_OCR_ROUTE, timeout_seconds=left)

    @staticmethod
    async def _stop_children(
        workers: Sequence[WorkerLike],
        futures: Sequence[concurrent.futures.Future[ExtractionOutcome]],
        sampler: _Sampler,
    ) -> None:
        if any(not future.done() for future in futures):
            # A cancelled step: kill what still runs, as the pool does at shutdown.
            for worker in workers:
                worker.halt()
        await _settle(futures)
        await _off_loop(sampler.stop)
        for worker in workers:
            await _off_loop(worker.stop)

    # -- restart -------------------------------------------------------------

    async def restore(self) -> None:
        """Bring the last result back; a check the restart cut off is nofit interrupted."""
        meta = await self._read_meta()
        if not meta:
            return
        state = meta.get(probe.META_PROBE_STATE, "")
        decoded = probe.decode(meta.get(probe.META_PROBE_RESULT, ""))
        if state == probe.STATE_RUNNING:
            base = decoded if decoded is not None else probe.snapshot()
            probe_id = meta.get(probe.META_PROBE_ID, "")
            interrupted = replace(
                base,
                id=probe_id if _ID_PATTERN.fullmatch(probe_id) else base.id,
                state=probe.STATE_DONE,
                verdict=probe.VERDICT_NOFIT,
                cause="interrupted",
                numbers=MappingProxyType({}),
                fp32_fetched=meta.get(probe.META_PROBE_FP32_FETCHED, "") == "1",
                fp32_deleted=False,
                finished_at=self._wall_clock(),
            )
            probe.restore(interrupted)
            await self._write_meta(
                {probe.META_PROBE_STATE: probe.STATE_DONE, probe.META_PROBE_RESULT: probe.encode(interrupted)}
            )
            LOGGER.info("the pre-check was cut off by a restart: verdict=nofit cause=interrupted")
        elif state == probe.STATE_DONE and decoded is not None and decoded.state == probe.STATE_DONE:
            probe.restore(decoded)

    async def recover(
        self, read_choice: Callable[[], Awaitable[CompanionChoice | None]], *, retry: float = RECOVER_RETRY_SECONDS
    ) -> None:
        """Sweep an fp32 file a check fetched, once the companion has been read (Pitfall 7).

        Deleted only when the key says int8; kept when it says fp32; nothing is
        decided without a successful read, which is tried again every ``retry``
        seconds until one comes or :meth:`close` is called.
        """
        meta = await self._read_meta()
        if meta.get(probe.META_PROBE_FP32_FETCHED, "") != "1":
            return
        owner = meta.get(probe.META_PROBE_ID, "")
        while not self._closed.is_set():
            if not self._running():
                if (await self._read_meta()).get(probe.META_PROBE_ID, "") != owner:
                    return  # a later check owns the mark now
                precision = await self._read_precision(read_choice)
                if precision == _INT8:
                    await self._sweep(owner)
                    return
                if precision == _FP32:
                    await self._write_meta({probe.META_PROBE_FP32_FETCHED: ""})
                    return
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self._closed.wait(), timeout=retry)

    @staticmethod
    async def _read_precision(read_choice: Callable[[], Awaitable[CompanionChoice | None]]) -> str | None:
        try:
            choice = await read_choice()
        except Exception as error:
            LOGGER.warning("the pre-check could not read the companion, %s", type(error).__name__)
            return None
        return None if choice is None else choice.precision

    async def _sweep(self, owner: str) -> None:
        try:
            await asyncio.to_thread(weights.remove_fp32_weights, self._models_dir)
        except OSError as error:
            LOGGER.warning("the pre-check could not remove its fp32 file, %s", type(error).__name__)
            return
        values = {probe.META_PROBE_FP32_FETCHED: ""}
        snap = probe.snapshot()
        if snap.id == owner and snap.fp32_fetched:
            swept = replace(snap, fp32_deleted=True)
            probe.restore(swept)
            values[probe.META_PROBE_RESULT] = probe.encode(swept)
        await self._write_meta(values)
        LOGGER.info("the pre-check removed the fp32 file it had fetched")


__all__ = [
    "RECOVER_RETRY_SECONDS",
    "START_STARTED",
    "ModelMeasureFn",
    "PollerLike",
    "PoolLike",
    "ProbeRun",
    "RunnerLike",
]
