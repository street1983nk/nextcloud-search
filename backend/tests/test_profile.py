"""The profile core: suggestion, effective level, value table and the economy pin.

Phase 24 only computes and reports. Nothing here reaches the poller, the writer
or the sandbox; these cases pin the arithmetic of PROF-01, the value-for-value
promise of PROF-02 and the fallback of HW-01 before anything is wired.
"""

import math
from pathlib import Path

import pytest

from findling import profile
from findling.config import (
    EMBED_ACTIVATION_BYTES,
    EMBED_BATCH_SIZE,
    EMBED_THREADS,
    FP32_EXTRA_BYTES,
    INDEX_WORKERS,
    MAIN_PROCESS_BASELINE_BYTES,
    MIB,
    OCR_CLAIM_BATCH,
    OCR_DPI,
    OCR_MAX_PAGES,
    OCR_SLOT_COST_BYTES,
    WRITER_HEAP_BYTES,
    WRITER_THREADS,
)
from findling.embed import model as model_module
from findling.hardware import Hardware
from findling.precision import Precision
from findling.profile import PROFILE_NAMES, Profile, effective, resolve, suggest

GIB = 1024**3
SRC = Path(__file__).resolve().parents[1] / "src" / "findling"

OVERRIDE_NAMES = (
    "FINDLING_OCR_MAX_PAGES",
    "FINDLING_OCR_DPI",
    "FINDLING_EMBED_BATCH_SIZE",
    "FINDLING_WRITER_HEAP_BYTES",
)


@pytest.fixture(autouse=True)
def _no_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every case starts without an admin override, whatever the shell carries."""
    for name in OVERRIDE_NAMES:
        monkeypatch.delenv(name, raising=False)


def box(
    cores: float | None,
    formula_gib: float | None = None,
    *,
    limit: int | None = None,
    total: int | None = None,
) -> Hardware:
    """A fake reading. ``formula_gib`` becomes MemAvailable, so it feeds the formula."""
    available = None if formula_gib is None else int(formula_gib * GIB)
    return Hardware(
        cpu_count=None if cores is None else max(1, int(cores)),
        cpu_quota=None,
        cores=cores,
        memory_limit_bytes=limit,
        memory_available_bytes=available,
        memory_total_bytes=total,
        architecture="x86_64",
        cgroup="none",
    )


def threshold_box(threshold: float | None, cores: float | None) -> Hardware:
    """A fake reading for the suggestion, which reads MemTotal (no limit set)."""
    total = None if threshold is None else int(threshold)
    return Hardware(
        cpu_count=None,
        cpu_quota=None,
        cores=cores,
        memory_limit_bytes=None,
        memory_available_bytes=total,
        memory_total_bytes=total,
        architecture="aarch64",
        cgroup="none",
    )


# --- the closed set -------------------------------------------------------------


def test_three_profiles_with_wire_names() -> None:
    assert frozenset({"economy", "standard", "performance"}) == PROFILE_NAMES
    assert [p.value for p in profile.PROFILE_ORDER] == ["economy", "standard", "performance"]


# --- the OCR slot formula -------------------------------------------------------


def test_standard_slots_follow_the_core_term() -> None:
    assert resolve(Profile.STANDARD, box(4, 16)).values.ocr_slots == 1
    assert resolve(Profile.STANDARD, box(5, 16)).values.ocr_slots == 2
    assert resolve(Profile.STANDARD, box(8, 16)).values.ocr_slots == 3


def test_standard_slots_stop_at_the_cap() -> None:
    assert resolve(Profile.STANDARD, box(9, 16)).values.ocr_slots == 4


def test_standard_slots_have_a_floor_of_one_when_memory_binds() -> None:
    assert resolve(Profile.STANDARD, box(8, 4)).values.ocr_slots == 1


def test_performance_slots() -> None:
    assert resolve(Profile.PERFORMANCE, box(16, 64)).values.ocr_slots == 15
    assert resolve(Profile.PERFORMANCE, box(8, 8)).values.ocr_slots == 7
    assert resolve(Profile.PERFORMANCE, box(6, 12)).values.ocr_slots == 5


def test_performance_slots_when_memory_binds() -> None:
    assert resolve(Profile.PERFORMANCE, box(16, 4)).values.ocr_slots == 3


def test_performance_slots_stop_at_the_cap() -> None:
    assert resolve(Profile.PERFORMANCE, box(24, 128)).values.ocr_slots == 16


@pytest.mark.parametrize("level", [Profile.STANDARD, Profile.PERFORMANCE])
def test_unknown_hardware_gives_one_slot(level: Profile) -> None:
    assert resolve(level, None).values.ocr_slots == 1
    assert resolve(level, box(None, 64)).values.ocr_slots == 1
    assert resolve(level, box(16, None)).values.ocr_slots == 1


def test_text_slots_are_twice_the_ocr_slots_up_to_the_cap() -> None:
    standard = resolve(Profile.STANDARD, box(8, 16)).values
    assert standard.text_slots == min(2 * standard.ocr_slots, 8)
    assert resolve(Profile.STANDARD, box(9, 16)).values.text_slots == 8
    performance = resolve(Profile.PERFORMANCE, box(8, 8)).values
    assert performance.text_slots == 14
    assert resolve(Profile.PERFORMANCE, box(24, 128)).values.text_slots == 16


def test_embed_slots_per_profile() -> None:
    assert resolve(Profile.ECONOMY, box(16, 64)).values.embed_slots == 0
    assert resolve(Profile.STANDARD, box(16, 64)).values.embed_slots == 1
    assert resolve(Profile.PERFORMANCE, box(16, 64)).values.embed_slots == 2


def test_performance_onnx_threads_follow_the_cores() -> None:
    assert resolve(Profile.PERFORMANCE, box(8, 64)).values.onnx_threads == 2
    assert resolve(Profile.PERFORMANCE, box(16, 64)).values.onnx_threads == 4
    assert resolve(Profile.PERFORMANCE, box(24, 64)).values.onnx_threads == 4
    assert resolve(Profile.PERFORMANCE, None).values.onnx_threads == EMBED_THREADS
    assert resolve(Profile.STANDARD, box(24, 64)).values.onnx_threads == EMBED_THREADS


def test_standard_and_performance_table_values() -> None:
    standard = resolve(Profile.STANDARD, box(8, 16)).values
    assert standard.writer_heap_bytes == 128_000_000
    assert standard.writer_threads == 2
    assert standard.ocr_max_pages == 100
    assert standard.memory_reserve_share == 0.20
    assert standard.embed_batch_size == EMBED_BATCH_SIZE
    assert standard.ocr_dpi == OCR_DPI
    performance = resolve(Profile.PERFORMANCE, box(8, 16)).values
    assert performance.writer_heap_bytes == 256_000_000
    assert performance.writer_threads == 2
    assert performance.ocr_max_pages == 150
    assert performance.memory_reserve_share == 0.15


# --- the economy pin (PROF-02) --------------------------------------------------


@pytest.mark.parametrize(
    "hardware",
    [None, box(None, None), box(1, 1), box(4, 8), box(64, 512)],
)
def test_economy_is_todays_constants_value_for_value(hardware: Hardware | None) -> None:
    """Economy is today's container, whatever the box. Literal and constant per row."""
    resolution = resolve(Profile.ECONOMY, hardware)
    values = resolution.values
    assert resolution.profile == Profile.ECONOMY

    assert values.ocr_slots == 1
    assert values.ocr_slots == INDEX_WORKERS
    assert values.text_slots == 1
    assert values.text_slots == INDEX_WORKERS
    assert values.embed_slots == 0
    assert values.onnx_threads == 2
    assert values.onnx_threads == EMBED_THREADS
    assert values.writer_heap_bytes == 50_000_000
    assert values.writer_heap_bytes == WRITER_HEAP_BYTES
    assert values.writer_threads == 1
    assert values.writer_threads == WRITER_THREADS
    assert values.embed_batch_size == 2
    assert values.embed_batch_size == EMBED_BATCH_SIZE
    assert values.ocr_max_pages == 30
    assert values.ocr_max_pages == OCR_MAX_PAGES
    assert values.ocr_dpi == 300
    assert values.ocr_dpi == OCR_DPI
    assert values.memory_reserve_share is None
    assert set(resolution.sources.values()) == {"profile"}


def test_the_constants_behind_economy_are_the_running_ones() -> None:
    """The economy row only means something while the running code uses these numbers."""
    assert INDEX_WORKERS == 1
    assert OCR_CLAIM_BATCH == 2
    assert model_module.THREADS == EMBED_THREADS == 2
    assert "num_threads=1" in (SRC / "index" / "writer.py").read_text(encoding="utf-8")
    assert "num_threads=1" in (SRC / "index" / "rebuild.py").read_text(encoding="utf-8")


# --- the suggestion (D-24-06) ---------------------------------------------------


@pytest.mark.parametrize(
    ("threshold", "cores", "expected"),
    [
        (16e9, 8, Profile.PERFORMANCE),
        (12e9, 6, Profile.PERFORMANCE),
        (11.9e9, 8, Profile.STANDARD),
        (8e9, 2.5, Profile.ECONOMY),
        (6e9, 3, Profile.STANDARD),
        (5.9e9, 4, Profile.ECONOMY),
        (16e9, None, Profile.ECONOMY),
        (None, 8, Profile.ECONOMY),
    ],
)
def test_suggest(threshold: float | None, cores: float | None, expected: Profile) -> None:
    assert suggest(threshold_box(threshold, cores)) == expected


def test_suggest_without_a_reading_is_economy() -> None:
    assert suggest(None) == Profile.ECONOMY


def test_suggest_reads_the_container_limit_before_the_host() -> None:
    container = Hardware(
        cpu_count=8,
        cpu_quota=None,
        cores=8,
        memory_limit_bytes=2 * GIB,
        memory_available_bytes=14_000_000_000,
        memory_total_bytes=16_000_000_000,
        architecture="x86_64",
        cgroup="v2",
    )
    assert suggest(container) == Profile.ECONOMY


# --- the effective level (D-24-07) ----------------------------------------------


def test_effective_never_read_is_economy() -> None:
    assert effective(None, Profile.PERFORMANCE) == Profile.ECONOMY


def test_effective_falls_back_to_what_fits() -> None:
    assert effective(Profile.PERFORMANCE, Profile.STANDARD) == Profile.STANDARD
    assert effective(Profile.PERFORMANCE, Profile.ECONOMY) == Profile.ECONOMY


def test_effective_never_switches_up() -> None:
    assert effective(Profile.STANDARD, Profile.PERFORMANCE) == Profile.STANDARD
    assert effective(Profile.ECONOMY, Profile.PERFORMANCE) == Profile.ECONOMY


# --- the admin override (PROF-03) -----------------------------------------------


def test_a_deliberate_override_wins_and_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_OCR_MAX_PAGES", "29")
    resolution = resolve(Profile.STANDARD, box(8, 16))
    assert resolution.values.ocr_max_pages == 29
    assert resolution.sources["ocr_max_pages"] == "env"


def test_the_injected_default_never_overrules_a_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_OCR_MAX_PAGES", "30")
    resolution = resolve(Profile.STANDARD, box(8, 16))
    assert resolution.values.ocr_max_pages == 100
    assert resolution.sources["ocr_max_pages"] == "profile"


def test_an_out_of_range_override_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_OCR_MAX_PAGES", "100000")
    resolution = resolve(Profile.STANDARD, box(8, 16))
    assert resolution.values.ocr_max_pages == 100
    assert resolution.sources["ocr_max_pages"] == "profile"


def test_an_override_also_moves_economy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_WRITER_HEAP_BYTES", "64000000")
    resolution = resolve(Profile.ECONOMY, None)
    assert resolution.values.writer_heap_bytes == 64_000_000
    assert resolution.sources["writer_heap_bytes"] == "env"
    assert resolution.sources["ocr_max_pages"] == "profile"


def test_dpi_and_batch_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_OCR_DPI", "200")
    monkeypatch.setenv("FINDLING_EMBED_BATCH_SIZE", "8")
    values = resolve(Profile.PERFORMANCE, box(8, 16)).values
    assert values.ocr_dpi == 200
    assert values.embed_batch_size == 8


def test_slots_have_no_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_INDEX_WORKERS", "8")
    resolution = resolve(Profile.ECONOMY, box(16, 64))
    assert resolution.values.ocr_slots == 1
    assert "ocr_slots" not in {key for key, source in resolution.sources.items() if source == "env"}


# --- the process state ----------------------------------------------------------


def test_the_resting_state_is_economy() -> None:
    state = profile.snapshot()
    assert state.hardware is None
    assert state.chosen is None
    assert state.suggested == Profile.ECONOMY
    assert state.effective == Profile.ECONOMY
    assert state.resolution.values == resolve(Profile.ECONOMY, None).values
    assert not state.downgraded


def test_a_big_box_runs_what_was_chosen() -> None:
    profile.note_hardware(threshold_box(64e9, 16))
    profile.note_chosen("performance")
    state = profile.snapshot()
    assert state.chosen == Profile.PERFORMANCE
    assert state.suggested == Profile.PERFORMANCE
    assert state.effective == Profile.PERFORMANCE
    assert state.resolution.profile == Profile.PERFORMANCE
    assert not state.downgraded


def test_a_shrunk_box_lowers_only_the_effective_level() -> None:
    """D-24-07: the chosen profile is never rewritten, only the effective one sinks."""
    profile.note_hardware(threshold_box(8e9, 4))
    profile.note_chosen("performance")
    state = profile.snapshot()
    assert state.chosen == Profile.PERFORMANCE
    assert state.effective == Profile.STANDARD
    assert state.resolution.profile == Profile.STANDARD
    assert state.downgraded


def test_a_tiny_box_falls_back_to_economy() -> None:
    profile.note_hardware(threshold_box(4e9, 2))
    profile.note_chosen("performance")
    state = profile.snapshot()
    assert state.chosen == Profile.PERFORMANCE
    assert state.effective == Profile.ECONOMY
    assert state.downgraded


def test_none_or_unknown_never_changes_a_read_profile() -> None:
    """D-24-02: a missing or garbled answer keeps what was read before."""
    profile.note_hardware(threshold_box(64e9, 16))
    profile.note_chosen("standard")
    profile.note_chosen(None)
    assert profile.snapshot().chosen == Profile.STANDARD
    profile.note_chosen("turbo")
    assert profile.snapshot().chosen == Profile.STANDARD
    assert profile.snapshot().effective == Profile.STANDARD


def test_never_read_stays_economy() -> None:
    profile.note_hardware(threshold_box(64e9, 16))
    profile.note_chosen(None)
    state = profile.snapshot()
    assert state.chosen is None
    assert state.suggested == Profile.PERFORMANCE
    assert state.effective == Profile.ECONOMY


def test_reading_does_not_recompute() -> None:
    profile.note_chosen("standard")
    first = profile.snapshot()
    assert profile.snapshot() is first
    profile.note_chosen("standard")
    assert profile.snapshot() is first
    profile.note_chosen("performance")
    assert profile.snapshot() is not first


def test_reset_restores_the_resting_state() -> None:
    profile.note_hardware(threshold_box(64e9, 16))
    profile.note_chosen("performance")
    profile.note_weights("fp32")
    profile.reset()
    state = profile.snapshot()
    assert state.hardware is None
    assert state.chosen is None
    assert state.effective == Profile.ECONOMY
    assert state.weights == "int8"


# --- the fp32 term and the static admission of the embed lane (plan 25-08) ------


def lane_box(available_mib: int) -> Hardware:
    """A box that suggests Standard (16 GiB, four cores) but has ``available_mib`` free."""
    return Hardware(
        cpu_count=4,
        cpu_quota=None,
        cores=4,
        memory_limit_bytes=None,
        memory_available_bytes=available_mib * MIB,
        memory_total_bytes=16 * GIB,
        architecture="x86_64",
        cgroup="none",
    )


def test_the_fp32_name_is_the_precision_name() -> None:
    """profile.py may not import precision.py (cycle), so the spelling is pinned here."""
    assert profile._FP32 == Precision.FP32.value


def test_the_fp32_term_shrinks_the_memory_term() -> None:
    """D-25-01: fp32 in force takes FP32_EXTRA_BYTES off the memory of the formula."""
    hardware = box(4, 16)
    int8 = profile._memory_term(Profile.STANDARD, hardware, extra_bytes=0)
    fp32 = profile._memory_term(Profile.STANDARD, hardware, extra_bytes=FP32_EXTRA_BYTES)
    budget = 0.4 * 16 * GIB * 0.8 - MAIN_PROCESS_BASELINE_BYTES
    assert int8 == math.floor(budget / OCR_SLOT_COST_BYTES) == 16
    assert fp32 == math.floor((budget - FP32_EXTRA_BYTES) / OCR_SLOT_COST_BYTES) == 15


def test_the_memory_term_is_not_clamped() -> None:
    """Unlike the slots, the term may fall to zero and below: the lane check needs that."""
    assert profile._memory_term(Profile.STANDARD, box(4, 1), extra_bytes=0) < 0
    assert profile._memory_term(Profile.STANDARD, None, extra_bytes=0) == 0
    assert profile._memory_term(Profile.ECONOMY, box(4, 16), extra_bytes=0) == 0


def test_fp32_costs_slots_when_memory_binds() -> None:
    hardware = box(16, 4)
    assert resolve(Profile.PERFORMANCE, hardware).values.ocr_slots == 3
    assert resolve(Profile.PERFORMANCE, hardware, weights="fp32").values.ocr_slots == 1


def test_note_weights_moves_the_slot_formula() -> None:
    profile.note_hardware(threshold_box(64e9, 16))
    profile.note_chosen("performance")
    int8_slots = profile.snapshot().resolution.values.ocr_slots
    profile.note_weights("fp32")
    state = profile.snapshot()
    assert state.weights == "fp32"
    assert state.resolution.values == resolve(Profile.PERFORMANCE, state.hardware, weights="fp32").values
    assert state.resolution.values.ocr_slots <= int8_slots


@pytest.mark.parametrize("weights", ["int8", "fp32"])
def test_economy_ignores_the_weights(weights: str) -> None:
    """The economy pin holds value for value whatever the precision (Sparsam-Pin)."""
    assert resolve(Profile.ECONOMY, box(16, 64), weights=weights).values == resolve(Profile.ECONOMY, None).values


def test_the_weights_rest_on_int8_and_ignore_garbage() -> None:
    assert profile.snapshot().weights == "int8"
    profile.note_weights(None)
    assert profile.snapshot().weights == "int8"
    profile.note_weights("fp16")
    assert profile.snapshot().weights == "int8"
    profile.note_weights("fp32")
    profile.note_weights("fp16")
    assert profile.snapshot().weights == "fp32"
    profile.note_weights("int8")
    assert profile.snapshot().weights == "int8"


def test_the_embed_lane_fits_standard_on_a_roomy_box() -> None:
    """PAR-04, static part: 16 GiB and four cores leave room for a parallel embedding."""
    profile.note_hardware(box(4, 16, total=16 * GIB))
    profile.note_chosen("standard")
    assert profile.snapshot().effective == Profile.STANDARD
    assert profile.snapshot().embed_lane_fits


def test_the_embed_lane_does_not_fit_economy() -> None:
    profile.note_hardware(box(4, 16, total=16 * GIB))
    profile.note_chosen("economy")
    assert not profile.snapshot().embed_lane_fits
    profile.reset()
    profile.note_hardware(threshold_box(4e9, 2))
    profile.note_chosen("performance")
    assert profile.snapshot().effective == Profile.ECONOMY
    assert not profile.snapshot().embed_lane_fits


def test_the_embed_lane_does_not_fit_without_hardware() -> None:
    profile.note_chosen("standard")
    assert not profile.snapshot().embed_lane_fits


def test_the_activations_can_tip_the_lane_over() -> None:
    """One OCR slot fits, but not the activations of the embedding beside it."""
    hardware = lane_box(4680)
    assert profile._memory_term(Profile.STANDARD, hardware, extra_bytes=0) == 1
    assert profile._memory_term(Profile.STANDARD, hardware, extra_bytes=EMBED_ACTIVATION_BYTES) == 0
    profile.note_hardware(hardware)
    profile.note_chosen("standard")
    state = profile.snapshot()
    assert state.effective == Profile.STANDARD
    assert state.resolution.values.ocr_slots == 1
    assert not state.embed_lane_fits


def test_fp32_can_tip_the_lane_over() -> None:
    """With int8 the lane fits, with fp32 in force the same box has no room left."""
    profile.note_hardware(lane_box(5000))
    profile.note_chosen("standard")
    assert profile.snapshot().embed_lane_fits
    profile.note_weights("fp32")
    assert not profile.snapshot().embed_lane_fits
