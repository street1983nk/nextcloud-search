"""The pre-check of a profile change decides without I/O (PRUEF-01).

Everything here is pure logic over numbers a test hands in; the orchestrator
that pauses, downloads and starts the children follows in later plans. What
this suite pins:

* need(N) = N x max(measured, OCR_SLOT_COST_BYTES) + pending load costs against
  the headroom, with GUARD_RESERVE_BYTES as the distance between narrow and
  fits (D-27-07, D-27-08);
* the gates before the first slot and the model child, and an unreadable
  headroom never admitted (SC3);
* the pending load costs spelled like EmbedRunner._need;
* steps, verdicts, causes and number keys as closed sets, foreign words raise
  (D-27-20);
* the hold flag of its own, apart from silence/arm of the poller;
* the ceilings (D-27-06, D-27-16).
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import pytest

from findling import probe
from findling.config import (
    CUTTER_LOAD_BYTES,
    EMBED_ACTIVATION_BYTES,
    EMBED_LANE_RESERVE_BYTES,
    EMBED_WEIGHTS_LOAD_BYTES,
    FP32_EXTRA_BYTES,
    GUARD_RESERVE_BYTES,
    MODEL_PROBE_CHILD_BYTES,
    OCR_LOCK_TIMEOUT_SECONDS,
    OCR_SLOT_COST_BYTES,
    PROBE_DOWNLOAD_SECONDS,
    PROBE_MEASURE_SECONDS,
    PROBE_PAUSE_SECONDS,
)
from findling.probe import (
    CAUSES,
    CAUSES_NARROW,
    CAUSES_NOFIT,
    NUMBER_KEYS,
    STATES,
    STEPS,
    VERDICT_FITS,
    VERDICT_NARROW,
    VERDICT_NOFIT,
    VERDICTS,
    ProbeSnapshot,
    first_slot_admitted,
    judge,
    judge_run,
    model_child_admitted,
    pending_load_bytes,
)

MIB = 1024 * 1024
PROBE_ID = "0123456789abcdef"


@pytest.fixture(autouse=True)
def _fresh() -> None:
    probe.reset()


def _headroom_for(reserve: int, *, slots: int = 2, pending: int = 0, extra: int = 0) -> int:
    return slots * OCR_SLOT_COST_BYTES + pending + extra + reserve


# -- the closed sets ------------------------------------------------------


def test_steps_are_the_eight_steps_in_order() -> None:
    assert STEPS == ("pause", "download", "digest", "model", "ocr_one", "calc", "ocr_n", "cleanup")


def test_causes_are_exactly_the_thirteen_codes() -> None:
    assert CAUSES_NARROW == frozenset({"reserve_thin"})
    assert CAUSES_NOFIT == frozenset({
        "memory_short",
        "model_memory",
        "memory_unknown",
        "slot_killed",
        "timeout",
        "pause_timeout",
        "download_failed",
        "download_slow",
        "digest_mismatch",
        "disk_short",
        "interrupted",
        "probe_failed",
    })
    assert CAUSES == CAUSES_NARROW | CAUSES_NOFIT
    assert len(CAUSES) == 13


def test_verdicts_states_start_codes_and_number_keys() -> None:
    assert VERDICTS == frozenset({"fits", "narrow", "nofit"})
    assert STATES == frozenset({"idle", "running", "done"})
    assert probe.START_BUSY == "busy"
    assert probe.START_REBUILDING == "rebuilding"
    assert NUMBER_KEYS == frozenset({
        "slots",
        "need",
        "available",
        "reserve",
        "required",
        "seconds",
        "rateInt8",
        "rateFp32",
    })


def test_meta_keys() -> None:
    assert probe.META_PROBE_STATE == "probe_state"
    assert probe.META_PROBE_ID == "probe_id"
    assert probe.META_PROBE_FP32_FETCHED == "probe_fp32_fetched"
    assert probe.META_PROBE_RESULT == "probe_result"


# -- the calculation ------------------------------------------------------


def test_one_byte_short_is_nofit_memory_short() -> None:
    headroom = _headroom_for(-1)
    result = judge(slots=2, headroom=headroom, slot_cost=0, pending=0, model_extra=0)
    assert result.verdict == VERDICT_NOFIT
    assert result.cause == "memory_short"
    assert dict(result.numbers) == {"slots": 2, "need": headroom + 1, "available": headroom}


@pytest.mark.parametrize("reserve", [0, GUARD_RESERVE_BYTES - 1])
def test_a_thin_reserve_is_narrow(reserve: int) -> None:
    result = judge(slots=2, headroom=_headroom_for(reserve), slot_cost=0, pending=0, model_extra=0)
    assert result.verdict == VERDICT_NARROW
    assert result.cause == "reserve_thin"
    assert dict(result.numbers) == {"reserve": reserve, "required": GUARD_RESERVE_BYTES}


def test_exactly_the_reserve_fits() -> None:
    result = judge(slots=2, headroom=_headroom_for(GUARD_RESERVE_BYTES), slot_cost=0, pending=0, model_extra=0)
    assert result.verdict == VERDICT_FITS
    assert result.cause == ""


def test_a_light_measurement_counts_as_the_constant() -> None:
    headroom = _headroom_for(GUARD_RESERVE_BYTES)
    light = judge(slots=2, headroom=headroom, slot_cost=OCR_SLOT_COST_BYTES // 2, pending=0, model_extra=0)
    assert light.verdict == VERDICT_FITS
    heavy = judge(slots=2, headroom=headroom, slot_cost=OCR_SLOT_COST_BYTES + 1, pending=0, model_extra=0)
    assert heavy.verdict == VERDICT_NARROW
    assert heavy.numbers["reserve"] == GUARD_RESERVE_BYTES - 2


def test_pending_load_costs_count() -> None:
    pending = 500 * MIB
    headroom = _headroom_for(GUARD_RESERVE_BYTES, pending=pending)
    assert judge(slots=2, headroom=headroom, slot_cost=0, pending=pending, model_extra=0).verdict == VERDICT_FITS
    assert judge(slots=2, headroom=headroom, slot_cost=0, pending=pending + 1, model_extra=0).verdict == (
        VERDICT_NARROW
    )


@pytest.mark.parametrize("reserve_without_model", [0, GUARD_RESERVE_BYTES])
def test_short_only_by_the_model_is_model_memory(reserve_without_model: int) -> None:
    extra = FP32_EXTRA_BYTES
    headroom = _headroom_for(reserve_without_model)
    result = judge(slots=2, headroom=headroom, slot_cost=0, pending=0, model_extra=extra)
    assert result.verdict == VERDICT_NOFIT
    assert result.cause == "model_memory"
    assert dict(result.numbers) == {"need": headroom - reserve_without_model + extra, "available": headroom}


def test_short_without_the_model_stays_memory_short() -> None:
    headroom = _headroom_for(-1)
    result = judge(slots=2, headroom=headroom, slot_cost=0, pending=0, model_extra=FP32_EXTRA_BYTES)
    assert result.cause == "memory_short"


def test_judge_run_after_ocr_n() -> None:
    pending = 100 * MIB
    thin = judge_run(min_headroom=pending + GUARD_RESERVE_BYTES - 1, pending=pending)
    assert thin.verdict == VERDICT_NARROW
    assert thin.cause == "reserve_thin"
    assert dict(thin.numbers) == {"reserve": GUARD_RESERVE_BYTES - 1, "required": GUARD_RESERVE_BYTES}
    below = judge_run(min_headroom=0, pending=pending)
    assert below.verdict == VERDICT_NARROW
    assert below.numbers["reserve"] == 0
    fits = judge_run(min_headroom=pending + GUARD_RESERVE_BYTES, pending=pending)
    assert fits.verdict == VERDICT_FITS
    assert fits.cause == ""


def test_the_gates_before_the_children() -> None:
    assert not first_slot_admitted(None)
    assert not model_child_admitted(None)
    slot_gate = OCR_SLOT_COST_BYTES + GUARD_RESERVE_BYTES
    assert not first_slot_admitted(slot_gate - 1)
    assert first_slot_admitted(slot_gate)
    model_gate = MODEL_PROBE_CHILD_BYTES + GUARD_RESERVE_BYTES
    assert not model_child_admitted(model_gate - 1)
    assert model_child_admitted(model_gate)


def _need_like_the_runner(*, cutter_built: bool, engine_loaded: bool, fp32: bool) -> int:
    need = EMBED_ACTIVATION_BYTES + EMBED_LANE_RESERVE_BYTES
    if not cutter_built:
        need += CUTTER_LOAD_BYTES
    if not engine_loaded:
        need += EMBED_WEIGHTS_LOAD_BYTES
        if fp32:
            need += FP32_EXTRA_BYTES
    return need


@pytest.mark.parametrize(("cutter_built", "engine_loaded", "fp32"), list(itertools.product([False, True], repeat=3)))
def test_pending_load_bytes_is_the_runner_formula(cutter_built: bool, engine_loaded: bool, fp32: bool) -> None:
    base = _need_like_the_runner(cutter_built=cutter_built, engine_loaded=engine_loaded, fp32=fp32)
    kwargs = {"cutter_built": cutter_built, "engine_loaded": engine_loaded, "fp32": fp32}
    assert pending_load_bytes(**kwargs, embed_slots=0, writer_heap_delta=0) == base
    assert pending_load_bytes(**kwargs, embed_slots=2, writer_heap_delta=78_000_000) == (
        base + 2 * EMBED_ACTIVATION_BYTES + 78_000_000
    )
    assert pending_load_bytes(**kwargs, embed_slots=-1, writer_heap_delta=-78_000_000) == base


# -- the state ------------------------------------------------------------


def test_the_resting_state_is_idle() -> None:
    snap = probe.snapshot()
    assert isinstance(snap, ProbeSnapshot)
    assert snap.state == "idle"
    assert snap.id == ""
    assert snap.verdict == ""


def test_a_run_from_begin_to_finish() -> None:
    probe.begin(PROBE_ID, "standard", "fp32", 100.0)
    running = probe.snapshot()
    assert running.state == "running"
    assert running.target_profile == "standard"
    assert running.target_precision == "fp32"
    assert running.started_at == 100.0
    probe.note_step("download", 10, 20)
    step = probe.snapshot()
    assert (step.step, step.bytes_done, step.bytes_total) == ("download", 10, 20)
    probe.finish("narrow", "reserve_thin", {"reserve": 1, "required": 2}, fp32_fetched=True, fp32_deleted=True, now=130.0)
    done = probe.snapshot()
    assert done.state == "done"
    assert done.verdict == "narrow"
    assert done.cause == "reserve_thin"
    assert dict(done.numbers) == {"reserve": 1, "required": 2}
    assert done.fp32_fetched
    assert done.fp32_deleted
    assert done.finished_at == 130.0
    # The earlier snapshot is untouched: each setter swaps one reference.
    assert running.state == "running"


def test_foreign_words_raise() -> None:
    with pytest.raises(ValueError, match="profile"):
        probe.begin(PROBE_ID, "turbo", "int8", 1.0)
    with pytest.raises(ValueError, match="precision"):
        probe.begin(PROBE_ID, "standard", "fp16", 1.0)
    with pytest.raises(ValueError, match="id"):
        probe.begin("../etc", "standard", "int8", 1.0)
    probe.begin(PROBE_ID, "standard", "int8", 1.0)
    with pytest.raises(ValueError, match="step"):
        probe.note_step("sleep")
    with pytest.raises(ValueError, match="cause"):
        probe.finish("nofit", "gremlins", {}, fp32_fetched=False, fp32_deleted=False, now=2.0)
    with pytest.raises(ValueError, match="cause"):
        probe.finish("nofit", "reserve_thin", {}, fp32_fetched=False, fp32_deleted=False, now=2.0)
    with pytest.raises(ValueError, match="cause"):
        probe.finish("fits", "memory_short", {}, fp32_fetched=False, fp32_deleted=False, now=2.0)
    with pytest.raises(ValueError, match="verdict"):
        probe.finish("maybe", "", {}, fp32_fetched=False, fp32_deleted=False, now=2.0)
    with pytest.raises(ValueError, match="number"):
        probe.finish("nofit", "timeout", {"path": 1}, fp32_fetched=False, fp32_deleted=False, now=2.0)
    assert probe.snapshot().state == "running"


def test_encode_decode_is_lossless() -> None:
    probe.begin(PROBE_ID, "performance", "fp32", 5.0)
    probe.finish(
        "nofit",
        "memory_short",
        {"slots": 3, "need": 900 * MIB, "available": 800 * MIB, "rateFp32": 4},
        fp32_fetched=True,
        fp32_deleted=False,
        now=9.5,
    )
    snap = probe.snapshot()
    text = probe.encode(snap)
    assert probe.decode(text) == snap
    probe.reset()
    probe.restore(snap)
    assert probe.snapshot() == snap
    assert probe.decode(probe.encode(probe.snapshot())) == snap


@pytest.mark.parametrize(
    "garbage",
    [
        "",
        "not json",
        "[]",
        "{}",
        json.dumps({"id": PROBE_ID}),
    ],
)
def test_decode_of_garbage_is_none(garbage: str) -> None:
    assert probe.decode(garbage) is None


def test_decode_drops_a_foreign_field_value() -> None:
    probe.begin(PROBE_ID, "standard", "int8", 1.0)
    good = json.loads(probe.encode(probe.snapshot()))
    for key, value in (
        ("state", "sleeping"),
        ("step", "sleep"),
        ("cause", "gremlins"),
        ("target_profile", "turbo"),
        ("numbers", {"path": 1}),
        ("numbers", {"slots": "3"}),
        ("bytes_done", -1),
        ("started_at", "soon"),
        ("fp32_fetched", "yes"),
        ("extra", 1),
    ):
        bad = dict(good)
        bad[key] = value
        assert probe.decode(json.dumps(bad)) is None, key


def test_hold_release_held() -> None:
    assert not probe.held()
    probe.hold()
    assert probe.held()
    probe.release()
    assert not probe.held()


def test_probe_stays_neutral() -> None:
    # The module loads without the worker; silence/arm of the poller are not its business.
    assert "findling.probe" in sys.modules
    source = Path(probe.__file__).read_text(encoding="utf-8")
    imports = [line for line in source.splitlines() if line.startswith(("import ", "from "))]
    allowed = ("findling.config", "findling.profile", "findling import profile")
    for line in imports:
        if "findling" in line:
            assert any(name in line for name in allowed), line
    assert "logging" not in source
    assert "LOGGER" not in source


def test_the_ceilings() -> None:
    assert PROBE_MEASURE_SECONDS == 120
    assert PROBE_DOWNLOAD_SECONDS == 600
    assert PROBE_PAUSE_SECONDS == OCR_LOCK_TIMEOUT_SECONDS == 1800
