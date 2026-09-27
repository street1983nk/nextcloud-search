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
writer or the sandbox yet. Note for phases 25 and 26: profile values such as
ocr_max_pages do not reach the spawn child of extract/sandbox.py through
settings(); the child reads its own environment, so the values have to be
handed over at spawn time (24-RESEARCH.md, Pitfall 6).

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
    EMBED_BATCH_SIZE,
    EMBED_BATCH_SIZE_RANGE,
    EMBED_THREADS,
    INDEX_WORKERS,
    MAIN_PROCESS_BASELINE_BYTES,
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


def effective(chosen: Profile | None, fitting: Profile) -> Profile:
    """min(chosen, fitting); never read counts as economy, never switches up (D-24-07)."""
    wanted = Profile.ECONOMY if chosen is None else chosen
    return min(wanted, fitting, key=PROFILE_ORDER.index)


def ocr_slots(profile: Profile, hardware: Hardware | None) -> int:
    """The OCR slots of a profile on a box, after the formula of D-24-03."""
    if profile is Profile.ECONOMY:
        return INDEX_WORKERS
    cores = None if hardware is None else hardware.cores
    memory = None if hardware is None else hardware.formula_memory_bytes
    if cores is None or memory is None:
        return 1
    if profile is Profile.STANDARD:
        core_term = math.floor(PROFILE_STANDARD_CORE_SHARE * cores - NEXTCLOUD_CORE_LOAD)
        share = PROFILE_STANDARD_MEMORY_SHARE
        reserve_share = PROFILE_STANDARD_RESERVE_SHARE
        cap = PROFILE_STANDARD_OCR_SLOTS_MAX
    else:
        # D-24-08: performance keeps whole cores free instead of subtracting the
        # Nextcloud load share; the admin chose the box for Findling.
        core_term = math.floor(cores - PROFILE_PERFORMANCE_CORES_KEPT_FREE)
        share = PROFILE_PERFORMANCE_MEMORY_SHARE
        reserve_share = PROFILE_PERFORMANCE_RESERVE_SHARE
        cap = PROFILE_PERFORMANCE_OCR_SLOTS_MAX
    budget = share * memory
    reserve = reserve_share * budget
    memory_term = math.floor((budget - reserve - MAIN_PROCESS_BASELINE_BYTES) / OCR_SLOT_COST_BYTES)
    return max(1, min(core_term, memory_term, cap))


def _profile_values(profile: Profile, hardware: Hardware | None) -> ProfileValues:
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
    slots = ocr_slots(profile, hardware)
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


def resolve(profile: Profile, hardware: Hardware | None) -> Resolution:
    """The value table of a profile on a box, with the admin overrides applied."""
    base = _profile_values(profile, hardware)
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
    resolution: Resolution

    @property
    def downgraded(self) -> bool:
        """True when a chosen profile does not fit the box and a smaller one runs."""
        return self.chosen is not None and self.effective != self.chosen


def _compute(hardware: Hardware | None, chosen: Profile | None) -> ProfileSnapshot:
    suggested = suggest(hardware)
    level = effective(chosen, suggested)
    return ProfileSnapshot(
        hardware=hardware,
        chosen=chosen,
        suggested=suggested,
        effective=level,
        resolution=resolve(level, hardware),
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
# The snapshot is computed only in note_hardware, note_chosen and reset.
# resolve() reads the environment, which is fixed per process; computing it on
# write means the status route never reads the environment on a poll.
_HARDWARE: Hardware | None = None
_CHOSEN: Profile | None = None
_SNAPSHOT: ProfileSnapshot = _compute(None, None)


def note_hardware(hardware: Hardware) -> None:
    """Publish the reading of this start. Called once from the lifespan."""
    global _HARDWARE, _SNAPSHOT
    _HARDWARE = hardware
    _SNAPSHOT = _compute(_HARDWARE, _CHOSEN)


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
    _SNAPSHOT = _compute(_HARDWARE, _CHOSEN)


def snapshot() -> ProfileSnapshot:
    """The profile state of this process right now.

    Read by the status route and by nothing that decides anything in phase 24.
    Nothing is opened and nothing is measured here.
    """
    return _SNAPSHOT


def reset() -> None:
    """Back to the resting state. For tests only; the container never forgets."""
    global _HARDWARE, _CHOSEN, _SNAPSHOT
    _HARDWARE = None
    _CHOSEN = None
    _SNAPSHOT = _compute(None, None)
