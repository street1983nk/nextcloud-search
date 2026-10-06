"""Performance profiles: suggestion, effective level and the value table.

A profile is a share of the detected cores and memory with caps, not a fixed
number of slots (PROF-01, D-24-03). Three levels form a closed set:

* ``economy`` is today's container, value for value, on any hardware (PROF-02).
  Its row is built from the existing constants only, so it cannot drift from
  what the running code does.
* ``standard`` and ``performance`` derive their OCR slots from the formula

      slots = max(1, min(core term,
                         floor((share x M_free - reserve - baseline) / cost),
                         cap))

  with the core term ``floor(0.5 x C - 0.25)`` for standard and ``floor(C - 1)``
  for performance (D-24-03, D-24-08).

The suggestion (HW-01, D-24-06) compares memory.max, else MemTotal, and the
cores against two thresholds; an unknown reading suggests economy. The
effective level is the smaller of the chosen one and the fitting one (D-24-07):
the chosen profile is never rewritten, a shrunk box only lowers the effective
level. A chosen profile that was never read counts as economy (D-24-02).

An admin variable that differs from its declared default overrules the profile
value and is reported with the source "env" (PROF-03). Slots have no variable
on purpose: INDEX_WORKERS stays a constant, the profile is the only way to move
them.

Phase 24 computes and reports only. No value is wired into the poller, the
writer or the sandbox yet. Phase 26 adds the cap of the memory guard
(note_cap): after repeated memory pressure or an OOM kill findling.guard caps
the effective level one below where it stood, as a third term of the minimum
(D-26-01). The chosen profile is never touched; the cap is handed in as a
Profile, this module never imports the guard (cycle). Note for phases 25 and 26: profile values such as
ocr_max_pages do not reach the spawn child of extract/sandbox.py through
settings(); the child reads its own environment, so the values have to be
handed over at spawn time (24-RESEARCH.md, Pitfall 6).

Phase 25 adds the precision in force (note_weights): fp32 takes FP32_EXTRA_BYTES
off the memory term of the formula (D-25-01), and the snapshot says whether a
parallel embed lane fits beside the OCR slots (embed_lane_fits, PAR-04).

Quick 261005-vit adds the full index term (owner decision of 2026-10-05): the
main process grows by MAIN_PROCESS_PER_FILE_BYTES per indexed file
(main_process_bytes), and the memory term takes it off (index_files). Since
plan 29-10 (D-29-12) the poller hands the count in (note_index_files, the
living indexed documents of the state database, rounded down to whole
thousands), so Standard and Performance lose slots as the stock grows. Economy
has no memory term at all and stays value for value; the probe and the guard
read the free memory live, where the growth is already contained.

The module is neutral: stdlib, findling.config and findling.hardware only, so
that both the worker and the api may import it. It logs nothing, neither
profile names nor environment values.
"""

import enum
import math
from collections.abc import Mapping
from dataclasses import dataclass, fields, replace
from types import MappingProxyType
from typing import Final

from findling.config import (
    EMBED_ACTIVATION_BYTES,
    EMBED_BATCH_SIZE,
    EMBED_BATCH_SIZE_RANGE,
    EMBED_THREADS,
    FP32_EXTRA_BYTES,
    INDEX_WORKERS,
    MAIN_PROCESS_BASELINE_BYTES,
    MAIN_PROCESS_PER_FILE_BYTES,
    NEXTCLOUD_CORE_LOAD,
    OCR_DPI,
    OCR_DPI_RANGE,
    OCR_MAX_PAGES,
    OCR_MAX_PAGES_RANGE,
    OCR_SLOT_COST_BYTES,
    PROFILE_PERFORMANCE_CORES_KEPT_FREE,
    PROFILE_PERFORMANCE_EMBED_SLOTS,
    PROFILE_PERFORMANCE_MEMORY_SHARE,
    PROFILE_PERFORMANCE_OCR_MAX_PAGES,
    PROFILE_PERFORMANCE_OCR_SLOTS_MAX,
    PROFILE_PERFORMANCE_ONNX_THREADS_MAX,
    PROFILE_PERFORMANCE_RESERVE_SHARE,
    PROFILE_PERFORMANCE_TEXT_SLOTS_MAX,
    PROFILE_PERFORMANCE_WRITER_HEAP_BYTES,
    PROFILE_PERFORMANCE_WRITER_THREADS,
    PROFILE_STANDARD_CORE_SHARE,
    PROFILE_STANDARD_EMBED_SLOTS,
    PROFILE_STANDARD_MEMORY_SHARE,
    PROFILE_STANDARD_OCR_MAX_PAGES,
    PROFILE_STANDARD_OCR_SLOTS_MAX,
    PROFILE_STANDARD_RESERVE_SHARE,
    PROFILE_STANDARD_TEXT_SLOTS_MAX,
    PROFILE_STANDARD_WRITER_HEAP_BYTES,
    PROFILE_STANDARD_WRITER_THREADS,
    SUGGEST_PERFORMANCE_CORES,
    SUGGEST_PERFORMANCE_MEMORY_BYTES,
    SUGGEST_STANDARD_CORES,
    SUGGEST_STANDARD_MEMORY_BYTES,
    WRITER_HEAP_BYTES,
    WRITER_THREADS,
    explicit_int_from_environment,
)
from findling.hardware import Hardware


class Profile(enum.StrEnum):
    """The wire names. Display texts come from the catalogues (phase 27)."""

    ECONOMY = "economy"
    STANDARD = "standard"
    PERFORMANCE = "performance"


PROFILE_ORDER: Final = (Profile.ECONOMY, Profile.STANDARD, Profile.PERFORMANCE)
PROFILE_NAMES: Final = frozenset(p.value for p in Profile)

SOURCE_PROFILE: Final = "profile"
SOURCE_ENV: Final = "env"

# Onnx threads of performance grow by one per four cores (D-24-03).
_CORES_PER_ONNX_THREAD: Final = 4

# The precision names as findling.precision spells them. Repeated here and not
# imported, because precision.py reports to this module and an import back
# would close a cycle; a test keeps both spellings equal.
_INT8: Final = "int8"
_FP32: Final = "fp32"
_WEIGHT_NAMES: Final = frozenset({_INT8, _FP32})


@dataclass(frozen=True, slots=True)
class ProfileValues:
    """The numbers a profile stands for. embed_slots 0 means: in the same loop (IDX-08)."""

    ocr_slots: int
    text_slots: int
    embed_slots: int
    onnx_threads: int
    writer_heap_bytes: int
    writer_threads: int
    embed_batch_size: int
    ocr_max_pages: int
    ocr_dpi: int
    memory_reserve_share: float | None


@dataclass(frozen=True, slots=True)
class Resolution:
    """A profile, its values and per field whether the profile or the env set it."""

    profile: Profile
    values: ProfileValues
    sources: Mapping[str, str]


def suggest(hardware: Hardware | None) -> Profile:
    """The largest level the box fits, economy when anything is unknown (D-24-06)."""
    if hardware is None:
        return Profile.ECONOMY
    memory = hardware.threshold_memory_bytes
    cores = hardware.cores
    if memory is None or cores is None:
        return Profile.ECONOMY
    if memory >= SUGGEST_PERFORMANCE_MEMORY_BYTES and cores >= SUGGEST_PERFORMANCE_CORES:
        return Profile.PERFORMANCE
    if memory >= SUGGEST_STANDARD_MEMORY_BYTES and cores >= SUGGEST_STANDARD_CORES:
        return Profile.STANDARD
    return Profile.ECONOMY


def effective(chosen: Profile | None, fitting: Profile, cap: Profile | None = None) -> Profile:
    """min(chosen, fitting, cap); never read counts as economy, never switches up (D-24-07).

    ``cap`` is the cap of the memory guard (D-26-01), None when there is none.
    """
    wanted = Profile.ECONOMY if chosen is None else chosen
    if cap is None:
        return min(wanted, fitting, key=PROFILE_ORDER.index)
    return min(wanted, fitting, cap, key=PROFILE_ORDER.index)


def main_process_bytes(index_files: int, *, weights: str = _INT8) -> int:
    """The main process of the calculation: baseline, full index term, fp32 extra.

    MAIN_PROCESS_BASELINE_BYTES plus index_files x MAIN_PROCESS_PER_FILE_BYTES
    (quick 261005-vit), plus FP32_EXTRA_BYTES while fp32 is in force (D-25-01).
    The OCR slots come on top, slots x OCR_SLOT_COST_BYTES.
    """
    return MAIN_PROCESS_BASELINE_BYTES + max(0, index_files) * MAIN_PROCESS_PER_FILE_BYTES + _weights_bytes(weights)


def _memory_term(profile: Profile, hardware: Hardware | None, *, extra_bytes: int, index_files: int = 0) -> int:
    """How many OCR slots the memory share holds after ``extra_bytes``, unclamped.

    floor((share x M_free - reserve - baseline - files x per file - extra) / cost)
    of D-24-03 with the full index term of quick 261005-vit. Not clamped to one:
    the lane admission needs to see a term of zero or below. Economy has no
    memory share and an unknown memory holds no known room, both answer 0.
    """
    memory = None if hardware is None else hardware.formula_memory_bytes
    if profile is Profile.ECONOMY or memory is None:
        return 0
    if profile is Profile.STANDARD:
        share = PROFILE_STANDARD_MEMORY_SHARE
        reserve_share = PROFILE_STANDARD_RESERVE_SHARE
    else:
        share = PROFILE_PERFORMANCE_MEMORY_SHARE
        reserve_share = PROFILE_PERFORMANCE_RESERVE_SHARE
    budget = share * memory
    reserve = reserve_share * budget
    main_process = main_process_bytes(index_files)
    return math.floor((budget - reserve - main_process - extra_bytes) / OCR_SLOT_COST_BYTES)


def _weights_bytes(weights: str) -> int:
    """The extra memory of the weights in force: FP32_EXTRA_BYTES for fp32, else 0 (D-25-01)."""
    return FP32_EXTRA_BYTES if weights == _FP32 else 0


def ocr_slots(profile: Profile, hardware: Hardware | None, *, weights: str = _INT8, index_files: int = 0) -> int:
    """The OCR slots of a profile on a box, after the formula of D-24-03.

    With fp32 in force the memory term loses FP32_EXTRA_BYTES (D-25-01), with
    ``index_files`` the full index term (quick 261005-vit). Economy ignores both.
    """
    if profile is Profile.ECONOMY:
        return INDEX_WORKERS
    cores = None if hardware is None else hardware.cores
    memory = None if hardware is None else hardware.formula_memory_bytes
    if cores is None or memory is None:
        return 1
    if profile is Profile.STANDARD:
        core_term = math.floor(PROFILE_STANDARD_CORE_SHARE * cores - NEXTCLOUD_CORE_LOAD)
        cap = PROFILE_STANDARD_OCR_SLOTS_MAX
    else:
        # D-24-08: performance keeps whole cores free instead of subtracting the
        # Nextcloud load share; the admin chose the box for Findling.
        core_term = math.floor(cores - PROFILE_PERFORMANCE_CORES_KEPT_FREE)
        cap = PROFILE_PERFORMANCE_OCR_SLOTS_MAX
    memory_term = _memory_term(profile, hardware, extra_bytes=_weights_bytes(weights), index_files=index_files)
    return max(1, min(core_term, memory_term, cap))


def _profile_values(profile: Profile, hardware: Hardware | None, weights: str, index_files: int) -> ProfileValues:
    if profile is Profile.ECONOMY:
        # Existing constants only, no new literal: this row is today's container.
        return ProfileValues(
            ocr_slots=INDEX_WORKERS,
            text_slots=INDEX_WORKERS,
            embed_slots=0,
            onnx_threads=EMBED_THREADS,
            writer_heap_bytes=WRITER_HEAP_BYTES,
            writer_threads=WRITER_THREADS,
            embed_batch_size=EMBED_BATCH_SIZE,
            ocr_max_pages=OCR_MAX_PAGES,
            ocr_dpi=OCR_DPI,
            memory_reserve_share=None,
        )
    slots = ocr_slots(profile, hardware, weights=weights, index_files=index_files)
    if profile is Profile.STANDARD:
        return ProfileValues(
            ocr_slots=slots,
            text_slots=min(2 * slots, PROFILE_STANDARD_TEXT_SLOTS_MAX),
            embed_slots=PROFILE_STANDARD_EMBED_SLOTS,
            onnx_threads=EMBED_THREADS,
            writer_heap_bytes=PROFILE_STANDARD_WRITER_HEAP_BYTES,
            writer_threads=PROFILE_STANDARD_WRITER_THREADS,
            embed_batch_size=EMBED_BATCH_SIZE,
            ocr_max_pages=PROFILE_STANDARD_OCR_MAX_PAGES,
            ocr_dpi=OCR_DPI,
            memory_reserve_share=PROFILE_STANDARD_RESERVE_SHARE,
        )
    cores = None if hardware is None else hardware.cores
    onnx_threads = (
        EMBED_THREADS
        if cores is None
        else max(EMBED_THREADS, min(PROFILE_PERFORMANCE_ONNX_THREADS_MAX, math.floor(cores / _CORES_PER_ONNX_THREAD)))
    )
    return ProfileValues(
        ocr_slots=slots,
        text_slots=min(2 * slots, PROFILE_PERFORMANCE_TEXT_SLOTS_MAX),
        embed_slots=PROFILE_PERFORMANCE_EMBED_SLOTS,
        onnx_threads=onnx_threads,
        writer_heap_bytes=PROFILE_PERFORMANCE_WRITER_HEAP_BYTES,
        writer_threads=PROFILE_PERFORMANCE_WRITER_THREADS,
        embed_batch_size=EMBED_BATCH_SIZE,
        ocr_max_pages=PROFILE_PERFORMANCE_OCR_MAX_PAGES,
        ocr_dpi=OCR_DPI,
        memory_reserve_share=PROFILE_PERFORMANCE_RESERVE_SHARE,
    )


# The four fields an admin variable may overrule: (field, variable, declared
# default, bounds). Slots are deliberately absent (INDEX_WORKERS taboo).
_OVERRIDES: Final[tuple[tuple[str, str, int, tuple[int, int] | None], ...]] = (
    ("ocr_max_pages", "FINDLING_OCR_MAX_PAGES", OCR_MAX_PAGES, OCR_MAX_PAGES_RANGE),
    ("ocr_dpi", "FINDLING_OCR_DPI", OCR_DPI, OCR_DPI_RANGE),
    ("embed_batch_size", "FINDLING_EMBED_BATCH_SIZE", EMBED_BATCH_SIZE, EMBED_BATCH_SIZE_RANGE),
    ("writer_heap_bytes", "FINDLING_WRITER_HEAP_BYTES", WRITER_HEAP_BYTES, None),
)

_FIELDS: Final = tuple(item.name for item in fields(ProfileValues))


def resolve(profile: Profile, hardware: Hardware | None, *, weights: str = _INT8, index_files: int = 0) -> Resolution:
    """The value table of a profile on a box, with the admin overrides applied.

    ``weights`` is the precision in force; only fp32 moves a number (the slots
    of Standard and Performance, D-25-01). ``index_files`` is the full index
    term (D-29-12) and moves the same slots. Economy stays value for value.
    """
    base = _profile_values(profile, hardware, weights, index_files)
    sources = dict.fromkeys(_FIELDS, SOURCE_PROFILE)
    overridden: dict[str, int] = {}
    for field, name, default, bounds in _OVERRIDES:
        value = explicit_int_from_environment(name, default, bounds)
        if value is not None:
            overridden[field] = value
            sources[field] = SOURCE_ENV
    values = replace(base, **overridden)
    return Resolution(profile=profile, values=values, sources=MappingProxyType(sources))


@dataclass(frozen=True, slots=True)
class ProfileSnapshot:
    """What this process knows about its profile: chosen, suggested, effective, values."""

    hardware: Hardware | None
    chosen: Profile | None
    suggested: Profile
    effective: Profile
    # The cap of the memory guard in force (D-26-01), None when there is none.
    cap: Profile | None
    resolution: Resolution
    # The precision in force as findling.precision reports it, "int8" or "fp32".
    weights: str
    # The living indexed files the slot formula counts (D-29-12), rounded down
    # to whole thousands by note_index_files; 0 until the poller reports.
    index_files: int
    # Whether a parallel embed lane fits in memory beside the OCR slots, the
    # static part of the RAM condition of PAR-04. Plan 25-09 adds the live part.
    embed_lane_fits: bool

    @property
    def downgraded(self) -> bool:
        """True when a smaller level than the chosen one runs: the box or the guard cap."""
        return self.chosen is not None and self.effective != self.chosen


def _embed_lane_fits(level: Profile, hardware: Hardware | None, weights: str, slots: int, index_files: int) -> bool:
    """True when the memory term after the activations still holds every OCR slot.

    Research pattern 4, static part: known hardware, Standard or Performance in
    effect, and floor((budget - reserve - main process - activations - fp32
    extra) / cost) at least the OCR slots of the effective values and at least
    one. The main process carries the full index term (D-29-12), the same one
    the slots were computed with.
    """
    if hardware is None or level not in {Profile.STANDARD, Profile.PERFORMANCE}:
        return False
    term = _memory_term(
        level, hardware, extra_bytes=EMBED_ACTIVATION_BYTES + _weights_bytes(weights), index_files=index_files
    )
    return term >= max(1, slots)


def _compute(
    hardware: Hardware | None,
    chosen: Profile | None,
    weights: str,
    cap: Profile | None = None,
    index_files: int = 0,
) -> ProfileSnapshot:
    suggested = suggest(hardware)
    level = effective(chosen, suggested, cap)
    resolution = resolve(level, hardware, weights=weights, index_files=index_files)
    return ProfileSnapshot(
        hardware=hardware,
        chosen=chosen,
        suggested=suggested,
        effective=level,
        cap=cap,
        resolution=resolution,
        weights=weights,
        index_files=index_files,
        embed_lane_fits=_embed_lane_fits(level, hardware, weights, resolution.values.ocr_slots, index_files),
    )


# The state of this process, held at module level and nowhere else, after the
# build of rebuild_progress in findling.index.rebuild.
#
# The hardware is read once per start (the lifespan of plan 06 calls
# note_hardware) and never measured again per round: Findling's own model load
# lowers MemAvailable, so a second reading would let the profile flap against
# itself (24-RESEARCH.md, Pitfall 3). If the box grows, the chosen profile
# applies again from the next start on (D-24-07).
#
# The snapshot is computed only in the note_* setters and reset.
# resolve() reads the environment, which is fixed per process; computing it on
# write means the status route never reads the environment on a poll.
_HARDWARE: Hardware | None = None
_CHOSEN: Profile | None = None
_WEIGHTS: str = _INT8
_CAP: Profile | None = None
_INDEX_FILES: int = 0
_SNAPSHOT: ProfileSnapshot = _compute(None, None, _INT8)

# The step note_index_files rounds the file count down to (D-29-12). A pass
# adds a handful of files; a new snapshot per pass would make the status route
# flap and recompute the table for a term worth 6 KiB per file. A thousand
# files are 6 MiB, far below the 250 MiB of one slot.
_INDEX_FILES_STEP: Final = 1000


def note_hardware(hardware: Hardware) -> None:
    """Publish the reading of this start. Called once from the lifespan."""
    global _HARDWARE, _SNAPSHOT
    _HARDWARE = hardware
    _SNAPSHOT = _compute(_HARDWARE, _CHOSEN, _WEIGHTS, _CAP, _INDEX_FILES)


def note_cap(cap: Profile | None) -> None:
    """Publish the cap of the memory guard, None when it was lifted (D-26-01).

    Called by findling.guard on every change of its cap; this module never
    imports that one (cycle). The chosen profile stays as it is, only the
    effective level moves. The snapshot is only recomputed on a change.
    """
    global _CAP, _SNAPSHOT
    if cap is _CAP:
        return
    _CAP = cap
    _SNAPSHOT = _compute(_HARDWARE, _CHOSEN, _WEIGHTS, _CAP, _INDEX_FILES)


def note_weights(value: str | None) -> None:
    """Publish the precision in force, as findling.precision reports it.

    Only "int8" and "fp32" count; None and anything else change nothing. The
    snapshot is only recomputed on a change. Called by findling.precision on
    every change of its state; this module never imports that one (cycle).
    """
    global _WEIGHTS, _SNAPSHOT
    if value not in _WEIGHT_NAMES or value == _WEIGHTS:
        return
    _WEIGHTS = value
    _SNAPSHOT = _compute(_HARDWARE, _CHOSEN, _WEIGHTS, _CAP, _INDEX_FILES)


def note_index_files(count: int | None) -> None:
    """Publish the living indexed files of the state database (D-29-12).

    The full index term of the slot formula: MAIN_PROCESS_PER_FILE_BYTES per
    file comes off the memory term of Standard and Performance, Economy ignores
    it. The count is rounded down to whole thousands; None and a negative count
    change nothing. The snapshot is only recomputed on a change of the rounded
    value. Called by the poller at the start of its work and after every pass
    that wrote verdicts; this module never imports the store.
    """
    global _INDEX_FILES, _SNAPSHOT
    if count is None or count < 0:
        return
    rounded = count // _INDEX_FILES_STEP * _INDEX_FILES_STEP
    if rounded == _INDEX_FILES:
        return
    _INDEX_FILES = rounded
    _SNAPSHOT = _compute(_HARDWARE, _CHOSEN, _WEIGHTS, _CAP, _INDEX_FILES)


def note_chosen(value: str | None) -> None:
    """Publish the profile the admin chose, as read from the companion this round.

    None and anything outside PROFILE_NAMES change nothing (D-24-02): a missing
    or tampered appconfig value must not move a profile that was read before.
    The value is not logged. The snapshot is only recomputed on a change.
    """
    global _CHOSEN, _SNAPSHOT
    if value is None or value not in PROFILE_NAMES:
        return
    chosen = Profile(value)
    if chosen is _CHOSEN:
        return
    _CHOSEN = chosen
    _SNAPSHOT = _compute(_HARDWARE, _CHOSEN, _WEIGHTS, _CAP, _INDEX_FILES)


def snapshot() -> ProfileSnapshot:
    """The profile state of this process right now.

    Read by the status route and by nothing that decides anything in phase 24.
    Nothing is opened and nothing is measured here.
    """
    return _SNAPSHOT


def reset() -> None:
    """Back to the resting state. For tests only; the container never forgets."""
    global _HARDWARE, _CHOSEN, _WEIGHTS, _CAP, _INDEX_FILES, _SNAPSHOT
    _HARDWARE = None
    _CHOSEN = None
    _WEIGHTS = _INT8
    _CAP = None
    _INDEX_FILES = 0
    _SNAPSHOT = _compute(None, None, _INT8)
