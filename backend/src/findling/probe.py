"""The pre-check of a profile change: codes, calculation and state (PRUEF-01).

Before a profile or a precision that costs more is stored, the container
measures on its own box whether it holds. This module is the part without I/O:

* The codes (D-27-20). Steps, verdicts, causes, states, start codes and the
  keys of the numbers form closed sets, so that the admin page can say them
  without inventing words. Every setter checks its input against its set and
  raises ValueError on a foreign word; decode drops a record with one.
* The calculation (D-27-07, D-27-08). need(N) = N x max(measured, constant) +
  pending load costs against the headroom. A measured slot below
  OCR_SLOT_COST_BYTES counts as the constant, because the throttle counts with
  the constant. The distance between narrow and fits is GUARD_RESERVE_BYTES,
  the reserve the throttle and the escalation of the guard already use, so a
  profile that fits here is neither throttled nor lowered right after saving.
* The gates (SC3). The check must never be the out of memory itself: the first
  slot starts only with its cost plus the reserve free, the model child only
  with its peak plus the reserve, and an unreadable headroom is never admitted.
* The hold flag (D-27-05). Its own flag, apart from the silence and arm of the
  poller, which belong to the enabled handler and the lifespan.

The state of this process is one reference to a frozen snapshot that every
setter swaps as a whole, so a reader in another thread never sees a torn mix
(lesson IN-01 of the phase 26 review).

The module is neutral like findling/guard.py: standard library,
findling.config and findling.profile only. It logs nothing.
"""

import json
import math
import re
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from types import MappingProxyType
from typing import Final, NamedTuple

from findling.config import (
    CUTTER_LOAD_BYTES,
    EMBED_ACTIVATION_BYTES,
    EMBED_LANE_RESERVE_BYTES,
    EMBED_WEIGHTS_LOAD_BYTES,
    FP32_EXTRA_BYTES,
    GUARD_RESERVE_BYTES,
    MODEL_PROBE_CHILD_BYTES,
    OCR_SLOT_COST_BYTES,
)
from findling.profile import PROFILE_NAMES

STEPS: Final = ("pause", "download", "digest", "model", "ocr_one", "calc", "ocr_n", "cleanup")
_STEP_SET: Final = frozenset(STEPS)

VERDICT_FITS: Final = "fits"
VERDICT_NARROW: Final = "narrow"
VERDICT_NOFIT: Final = "nofit"
VERDICTS: Final = frozenset({VERDICT_FITS, VERDICT_NARROW, VERDICT_NOFIT})

CAUSE_NONE: Final = ""
CAUSE_RESERVE_THIN: Final = "reserve_thin"
CAUSE_MEMORY_SHORT: Final = "memory_short"
CAUSE_MODEL_MEMORY: Final = "model_memory"
CAUSE_MEMORY_UNKNOWN: Final = "memory_unknown"
CAUSES_NARROW: Final = frozenset({CAUSE_RESERVE_THIN})
CAUSES_NOFIT: Final = frozenset(
    {
        CAUSE_MEMORY_SHORT,
        CAUSE_MODEL_MEMORY,
        CAUSE_MEMORY_UNKNOWN,
        "slot_killed",
        "timeout",
        "pause_timeout",
        "download_failed",
        "download_slow",
        "digest_mismatch",
        "disk_short",
        "interrupted",
        "probe_failed",
    }
)
CAUSES: Final = CAUSES_NARROW | CAUSES_NOFIT

STATE_IDLE: Final = "idle"
STATE_RUNNING: Final = "running"
STATE_DONE: Final = "done"
STATES: Final = frozenset({STATE_IDLE, STATE_RUNNING, STATE_DONE})

# The refusals of a start, apart from the causes of a finished check.
START_BUSY: Final = "busy"
START_REBUILDING: Final = "rebuilding"

NUMBER_KEYS: Final = frozenset({"slots", "need", "available", "reserve", "required", "seconds", "rateInt8", "rateFp32"})

# The precision names as findling.precision spells them, repeated like in
# findling/profile.py, because an import of precision.py would break neutrality.
PRECISIONS: Final = frozenset({"int8", "fp32"})

# The keys of the probe in the meta table of state.db. Plain names without
# Final, the spelling the plans grep for; nothing rebinds them.
META_PROBE_STATE = "probe_state"
META_PROBE_ID = "probe_id"
META_PROBE_FP32_FETCHED = "probe_fp32_fetched"
META_PROBE_RESULT = "probe_result"

# The scan page the check runs through OCR, shipped in the package next to the
# extractors. A byte exact copy of testdata/corpus/13-ratsvorlage-scan.pdf, a
# synthetic council paper without any user data. One page of this kind is
# representative enough (27-RESEARCH.md A4): a lighter page measures below
# OCR_SLOT_COST_BYTES, and judge counts the constant then. The orchestrator
# checks the digest before use; a test pins digest and size.
PROBE_SCAN_NAME: Final = "probe_scan.pdf"
PROBE_SCAN_SHA256: Final = "320bb1aa17c9192d822ea6b6c570f7d125e113181e05ad62fe1afd728a0a81f3"
PROBE_SCAN_BYTES: Final = 79_506

# 8 random bytes, 16 hex digits: never a path, never a text.
_ID_PATTERN: Final = re.compile(r"[0-9a-f]{16}")

_FIELDS: Final = frozenset(
    {
        "id",
        "state",
        "step",
        "bytes_done",
        "bytes_total",
        "verdict",
        "cause",
        "numbers",
        "target_profile",
        "target_precision",
        "fp32_fetched",
        "fp32_deleted",
        "started_at",
        "finished_at",
    }
)


@dataclass(frozen=True, slots=True)
class ProbeSnapshot:
    """The probe state of this process: the running or the last check."""

    id: str
    state: str
    # "" before the first step.
    step: str
    bytes_done: int
    bytes_total: int
    # "" while no verdict exists; the cause is "" for fits.
    verdict: str
    cause: str
    numbers: Mapping[str, int]
    # "" in the resting state.
    target_profile: str
    target_precision: str
    # The check fetched the fp32 file itself, and deleted it again.
    fp32_fetched: bool
    fp32_deleted: bool
    # Epoch seconds, None when not yet reached.
    started_at: float | None
    finished_at: float | None


class Verdict(NamedTuple):
    """A verdict, its cause and the numbers the sentence of the cause needs."""

    verdict: str
    cause: str
    numbers: Mapping[str, int]


def _numbers(values: Mapping[str, int]) -> Mapping[str, int]:
    return MappingProxyType(dict(values))


_IDLE: Final = ProbeSnapshot(
    id="",
    state=STATE_IDLE,
    step="",
    bytes_done=0,
    bytes_total=0,
    verdict="",
    cause=CAUSE_NONE,
    numbers=_numbers({}),
    target_profile="",
    target_precision="",
    fp32_fetched=False,
    fp32_deleted=False,
    started_at=None,
    finished_at=None,
)


# -- the calculation ------------------------------------------------------


def judge(*, slots: int, headroom: int, slot_cost: int, pending: int, model_extra: int) -> Verdict:
    """The verdict of calc: N slots at the measured cost plus the load costs.

    ``slot_cost`` is the measured cost of one slot and counts at least as
    OCR_SLOT_COST_BYTES. ``pending`` are the load costs the running box still
    has ahead (pending_load_bytes), ``model_extra`` the extra need of the fp32
    weights, kept apart so that a shortfall caused by it alone is named
    model_memory. Pass the fp32 part either here or in ``pending``, not twice.
    """
    cost = max(slot_cost, OCR_SLOT_COST_BYTES)
    need = slots * cost + pending + model_extra
    reserve = headroom - need
    if reserve < 0:
        # Without the fp32 part it would fit or be narrow: the model alone is short.
        if model_extra > 0 and headroom >= need - model_extra:
            return Verdict(VERDICT_NOFIT, CAUSE_MODEL_MEMORY, _numbers({"need": need, "available": headroom}))
        return Verdict(
            VERDICT_NOFIT, CAUSE_MEMORY_SHORT, _numbers({"slots": slots, "need": need, "available": headroom})
        )
    if reserve < GUARD_RESERVE_BYTES:
        return Verdict(VERDICT_NARROW, CAUSE_RESERVE_THIN, _thin(reserve))
    return Verdict(VERDICT_FITS, CAUSE_NONE, _numbers({"slots": slots, "need": need, "available": headroom}))


def judge_run(*, min_headroom: int, pending: int) -> Verdict:
    """The verdict after ocr_n: the lowest headroom during the run less the load costs."""
    reserve = min_headroom - pending
    if reserve < GUARD_RESERVE_BYTES:
        return Verdict(VERDICT_NARROW, CAUSE_RESERVE_THIN, _thin(reserve))
    return Verdict(VERDICT_FITS, CAUSE_NONE, _numbers({"reserve": reserve}))


def _thin(reserve: int) -> Mapping[str, int]:
    # A run can dip below zero; the sentence says what is left, never less than nothing.
    return _numbers({"reserve": max(0, reserve), "required": GUARD_RESERVE_BYTES})


def pending_load_bytes(
    *, cutter_built: bool, engine_loaded: bool, fp32: bool, embed_slots: int, writer_heap_delta: int
) -> int:
    """The load costs the box still has ahead, spelled like EmbedRunner._need.

    Activations and one OCR page of lane reserve always; the cutter when not
    built; the weights when the engine is not loaded, plus the fp32 extra then.
    The idle unload (MEM-01) may have freed model and cutter during the check,
    which is why they count as pending. On top: the activations of the parallel
    embed slots and the growth of the writer heap, neither ever negative.
    """
    need = EMBED_ACTIVATION_BYTES + EMBED_LANE_RESERVE_BYTES
    if not cutter_built:
        need += CUTTER_LOAD_BYTES
    if not engine_loaded:
        need += EMBED_WEIGHTS_LOAD_BYTES
        if fp32:
            need += FP32_EXTRA_BYTES
    return need + max(0, embed_slots) * EMBED_ACTIVATION_BYTES + max(0, writer_heap_delta)


def first_slot_admitted(headroom: int | None) -> bool:
    """The first OCR child of the check starts only with its cost plus the reserve free."""
    return headroom is not None and headroom >= OCR_SLOT_COST_BYTES + GUARD_RESERVE_BYTES


def probe_scan_path() -> Traversable:
    """The shipped scan page. The path is never logged and never handed out."""
    return resources.files("findling.extract") / PROBE_SCAN_NAME


def model_child_admitted(headroom: int | None) -> bool:
    """The model child of the check starts only with its peak plus the reserve free."""
    return headroom is not None and headroom >= MODEL_PROBE_CHILD_BYTES + GUARD_RESERVE_BYTES


# -- the state ------------------------------------------------------------

# One reference, swapped as a whole under the lock by every setter.
_STATE_LOCK = threading.Lock()
_SNAPSHOT: ProbeSnapshot = _IDLE

_HOLD_LOCK = threading.Lock()
_HELD: bool = False


def _check_numbers(numbers: Mapping[str, int]) -> Mapping[str, int]:
    for key, value in numbers.items():
        if key not in NUMBER_KEYS:
            raise ValueError("unknown probe number key")
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("probe number is not an integer")
    return _numbers(numbers)


def _check_verdict(verdict: str, cause: str) -> None:
    if verdict not in VERDICTS:
        raise ValueError("unknown probe verdict")
    allowed = {VERDICT_FITS: frozenset({CAUSE_NONE}), VERDICT_NARROW: CAUSES_NARROW, VERDICT_NOFIT: CAUSES_NOFIT}
    if cause not in allowed[verdict]:
        raise ValueError("probe cause does not belong to the verdict")


def begin(probe_id: str, profile: str, precision: str, now: float) -> None:
    """A check starts: the target, the id, state running."""
    global _SNAPSHOT
    if _ID_PATTERN.fullmatch(probe_id) is None:
        raise ValueError("malformed probe id")
    if profile not in PROFILE_NAMES:
        raise ValueError("unknown probe profile")
    if precision not in PRECISIONS:
        raise ValueError("unknown probe precision")
    with _STATE_LOCK:
        _SNAPSHOT = ProbeSnapshot(
            id=probe_id,
            state=STATE_RUNNING,
            step="",
            bytes_done=0,
            bytes_total=0,
            verdict="",
            cause=CAUSE_NONE,
            numbers=_numbers({}),
            target_profile=profile,
            target_precision=precision,
            fp32_fetched=False,
            fp32_deleted=False,
            started_at=now,
            finished_at=None,
        )


def note_step(step: str, bytes_done: int = 0, bytes_total: int = 0, *, slots: int = 0) -> None:
    """The check entered a step; the byte counts belong to the download.

    ``slots`` is the figure of ocr_n, carried in ``numbers`` so that the
    progress line can name it ("OCR with 4 slots"); nought leaves the numbers
    as they are.
    """
    global _SNAPSHOT
    if step not in _STEP_SET:
        raise ValueError("unknown probe step")
    if bytes_done < 0 or bytes_total < 0:
        raise ValueError("negative probe byte count")
    if slots < 0:
        raise ValueError("negative probe slot count")
    with _STATE_LOCK:
        current = _SNAPSHOT
        numbers = _numbers({**current.numbers, "slots": slots}) if slots else current.numbers
        _SNAPSHOT = ProbeSnapshot(
            id=current.id,
            state=current.state,
            step=step,
            bytes_done=bytes_done,
            bytes_total=bytes_total,
            verdict=current.verdict,
            cause=current.cause,
            numbers=numbers,
            target_profile=current.target_profile,
            target_precision=current.target_precision,
            fp32_fetched=current.fp32_fetched,
            fp32_deleted=current.fp32_deleted,
            started_at=current.started_at,
            finished_at=current.finished_at,
        )


def finish(
    verdict: str, cause: str, numbers: Mapping[str, int], *, fp32_fetched: bool, fp32_deleted: bool, now: float
) -> None:
    """The check ended with a verdict, a cause of its set and its numbers."""
    global _SNAPSHOT
    _check_verdict(verdict, cause)
    checked = _check_numbers(numbers)
    with _STATE_LOCK:
        current = _SNAPSHOT
        _SNAPSHOT = ProbeSnapshot(
            id=current.id,
            state=STATE_DONE,
            step=current.step,
            bytes_done=current.bytes_done,
            bytes_total=current.bytes_total,
            verdict=verdict,
            cause=cause,
            numbers=checked,
            target_profile=current.target_profile,
            target_precision=current.target_precision,
            fp32_fetched=fp32_fetched,
            fp32_deleted=fp32_deleted,
            started_at=current.started_at,
            finished_at=now,
        )


def restore(snap: ProbeSnapshot) -> None:
    """Bring a snapshot back that state.db kept, for instance from decode."""
    global _SNAPSHOT
    with _STATE_LOCK:
        _SNAPSHOT = snap


def snapshot() -> ProbeSnapshot:
    """The probe state of this process right now. Reading changes nothing."""
    return _SNAPSHOT


def encode(snap: ProbeSnapshot) -> str:
    """The snapshot as compact JSON for the meta table."""
    record = {
        "id": snap.id,
        "state": snap.state,
        "step": snap.step,
        "bytes_done": snap.bytes_done,
        "bytes_total": snap.bytes_total,
        "verdict": snap.verdict,
        "cause": snap.cause,
        "numbers": dict(snap.numbers),
        "target_profile": snap.target_profile,
        "target_precision": snap.target_precision,
        "fp32_fetched": snap.fp32_fetched,
        "fp32_deleted": snap.fp32_deleted,
        "started_at": snap.started_at,
        "finished_at": snap.finished_at,
    }
    return json.dumps(record, separators=(",", ":"), sort_keys=True)


def _count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _moment(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("malformed probe moment")
    return float(value)


def _optional_moment(value: object) -> float | None:
    return None if value is None else _moment(value)


def _decoded(record: dict[str, object]) -> ProbeSnapshot:
    if set(record) != _FIELDS:
        raise ValueError("foreign probe fields")
    probe_id, state, step = record["id"], record["state"], record["step"]
    verdict, cause = record["verdict"], record["cause"]
    target_profile, target_precision = record["target_profile"], record["target_precision"]
    fetched, deleted, numbers = record["fp32_fetched"], record["fp32_deleted"], record["numbers"]
    bytes_done, bytes_total = _count(record["bytes_done"]), _count(record["bytes_total"])
    if not isinstance(probe_id, str) or (probe_id and _ID_PATTERN.fullmatch(probe_id) is None):
        raise ValueError("malformed probe id")
    if state not in STATES or (step != "" and step not in _STEP_SET):
        raise ValueError("unknown probe state or step")
    if target_profile != "" and target_profile not in PROFILE_NAMES:
        raise ValueError("unknown probe profile")
    if target_precision != "" and target_precision not in PRECISIONS:
        raise ValueError("unknown probe precision")
    if not isinstance(fetched, bool) or not isinstance(deleted, bool) or not isinstance(numbers, dict):
        raise ValueError("malformed probe flags")
    if bytes_done is None or bytes_total is None:
        raise ValueError("malformed probe byte count")
    if verdict != "" or cause != "":
        _check_verdict(str(verdict), str(cause))
    return ProbeSnapshot(
        id=probe_id,
        state=str(state),
        step=str(step),
        bytes_done=bytes_done,
        bytes_total=bytes_total,
        verdict=str(verdict),
        cause=str(cause),
        numbers=_check_numbers(numbers),
        target_profile=str(target_profile),
        target_precision=str(target_precision),
        fp32_fetched=fetched,
        fp32_deleted=deleted,
        started_at=_optional_moment(record["started_at"]),
        finished_at=_optional_moment(record["finished_at"]),
    )


def decode(text: str) -> ProbeSnapshot | None:
    """The snapshot of encode, or None for anything else; every field checked against its set."""
    try:
        record = json.loads(text)
    except ValueError:
        return None
    if not isinstance(record, dict):
        return None
    try:
        return _decoded(record)
    except ValueError:
        return None


# -- the hold flag ------------------------------------------------------


def hold() -> None:
    """Hold the indexing for the check. The poller and the runner wait on it."""
    global _HELD
    with _HOLD_LOCK:
        _HELD = True


def release() -> None:
    """Let the indexing go on. Always called in the finally of the check."""
    global _HELD
    with _HOLD_LOCK:
        _HELD = False


def held() -> bool:
    """Whether a check holds the indexing right now."""
    with _HOLD_LOCK:
        return _HELD


def reset() -> None:
    """Back to the resting state. For tests only."""
    global _SNAPSHOT, _HELD
    with _STATE_LOCK:
        _SNAPSHOT = _IDLE
    with _HOLD_LOCK:
        _HELD = False


__all__ = [
    "CAUSES",
    "CAUSES_NARROW",
    "CAUSES_NOFIT",
    "CAUSE_MEMORY_SHORT",
    "CAUSE_MEMORY_UNKNOWN",
    "CAUSE_MODEL_MEMORY",
    "CAUSE_NONE",
    "CAUSE_RESERVE_THIN",
    "META_PROBE_FP32_FETCHED",
    "META_PROBE_ID",
    "META_PROBE_RESULT",
    "META_PROBE_STATE",
    "NUMBER_KEYS",
    "PRECISIONS",
    "PROBE_SCAN_BYTES",
    "PROBE_SCAN_NAME",
    "PROBE_SCAN_SHA256",
    "START_BUSY",
    "START_REBUILDING",
    "STATES",
    "STATE_DONE",
    "STATE_IDLE",
    "STATE_RUNNING",
    "STEPS",
    "VERDICTS",
    "VERDICT_FITS",
    "VERDICT_NARROW",
    "VERDICT_NOFIT",
    "ProbeSnapshot",
    "Verdict",
    "begin",
    "decode",
    "encode",
    "finish",
    "first_slot_admitted",
    "held",
    "hold",
    "judge",
    "judge_run",
    "model_child_admitted",
    "note_step",
    "pending_load_bytes",
    "probe_scan_path",
    "release",
    "reset",
    "restore",
    "snapshot",
]
