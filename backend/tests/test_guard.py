"""The memory guard decides without I/O: throttle, trigger, lower, way back (PAR-03).

Everything here is pure logic over numbers a test hands in. The kernel reader
has its own suite (tests/test_memory_guard.py); the task that ticks the guard
and the persistence in state.db follow in later plans. What this suite pins:

* the slot throttle is a sum against the headroom, slot 1 always runs (D-26-02);
* a rising memory.events max only counts under real pressure, and two such
  events at least a minute apart within ten minutes lower the level (D-26-03,
  D-26-15, 26-RESEARCH.md Pitfall 2);
* a kill lowers at once (D-26-16);
* the lowering caps the effective level, never the chosen profile, and economy
  is the floor (D-26-01, D-24-07);
* only the admin lifts the cap, by the token or by another profile (D-26-04).
"""

from __future__ import annotations

import re
import threading

import pytest

from findling import guard, profile
from findling.config import GUARD_RESERVE_BYTES, OCR_SLOT_COST_BYTES
from findling.guard import (
    CAUSE_MEMORY_MAX_REPEATED,
    CAUSE_NONE,
    CAUSE_OOM_KILL,
    CAUSE_UNCLEAN_END,
    CAUSES,
    Escalation,
    throttled_slots,
)
from findling.hardware import Hardware
from findling.profile import Profile

MIB = 1024 * 1024
GIB = 1024 * MIB
TIGHT = 100 * MIB
ROOMY = 1 * GIB


def _events(max_count: int = 0, oom_kill: int = 0) -> dict[str, int]:
    return {"low": 0, "high": 0, "max": max_count, "oom": 0, "oom_kill": oom_kill}


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


def _performance_box() -> None:
    profile.note_hardware(_big_box())
    profile.note_chosen("performance")


# --- the closed set ------------------------------------------------------------


def test_the_causes_are_a_closed_set_without_the_empty_word() -> None:
    assert frozenset({CAUSE_MEMORY_MAX_REPEATED, CAUSE_OOM_KILL, CAUSE_UNCLEAN_END}) == CAUSES
    assert CAUSE_NONE not in CAUSES
    assert CAUSE_MEMORY_MAX_REPEATED == "memory_max_repeated"
    assert CAUSE_OOM_KILL == "oom_kill"
    assert CAUSE_UNCLEAN_END == "unclean_end"


def test_the_meta_keys_are_the_agreed_spelling() -> None:
    assert guard.META_CAP == "guard_cap"
    assert guard.META_CAUSE == "guard_cause"
    assert guard.META_SINCE == "guard_since"
    assert guard.META_TOKEN == "guard_token"  # noqa: S105 - a meta key name
    assert guard.META_CHOSEN == "guard_chosen"
    assert guard.META_MULTI_SLOT_PASS == "multi_slot_pass"  # noqa: S105 - a meta key name
    assert guard.META_MULTI_SLOT_CHOSEN == "multi_slot_chosen"


# --- the throttle (D-26-02) ----------------------------------------------------


def test_the_throttle_keeps_slot_one_always() -> None:
    assert throttled_slots(4, None) == 1
    assert throttled_slots(1, 10 * GIB) == 1
    assert throttled_slots(0, 10 * GIB) == 1
    assert throttled_slots(4, 0) == 1


def test_the_throttle_grants_a_slot_per_cost_above_the_reserve() -> None:
    assert throttled_slots(4, OCR_SLOT_COST_BYTES) == 1
    assert throttled_slots(4, OCR_SLOT_COST_BYTES * 3) == 3
    assert throttled_slots(4, GUARD_RESERVE_BYTES + OCR_SLOT_COST_BYTES - 1) == 1
    assert throttled_slots(4, GUARD_RESERVE_BYTES + OCR_SLOT_COST_BYTES) == 2
    assert throttled_slots(4, 100 * GIB) == 4


# --- the escalation (D-26-03, D-26-15, D-26-16) -------------------------------


def test_the_first_tick_only_sets_the_base() -> None:
    escalation = Escalation()

    assert escalation.observe(0.0, _events(max_count=500, oom_kill=3), TIGHT, 0) == CAUSE_NONE


def test_a_rising_max_with_room_to_spare_is_never_an_event() -> None:
    # Pitfall 2: max is counted before the reclaim and rises with the page cache.
    escalation = Escalation()
    escalation.observe(0.0, _events(), ROOMY, 0)

    for tick in range(1, 200):
        assert escalation.observe(tick * 15.0, _events(max_count=tick * 10), ROOMY, 0) == CAUSE_NONE


def test_a_rising_max_with_an_unreadable_headroom_is_no_event() -> None:
    escalation = Escalation()
    escalation.observe(0.0, _events(), None, 0)

    assert escalation.observe(60.0, _events(max_count=5), None, 0) == CAUSE_NONE
    assert escalation.observe(200.0, _events(max_count=10), None, 0) == CAUSE_NONE


def test_two_qualified_events_a_minute_apart_lower_the_level() -> None:
    escalation = Escalation()
    escalation.observe(-15.0, _events(), TIGHT, 0)

    assert escalation.observe(0.0, _events(max_count=1), TIGHT, 0) == CAUSE_NONE
    assert escalation.observe(90.0, _events(max_count=2), TIGHT, 0) == CAUSE_MEMORY_MAX_REPEATED


def test_two_events_closer_than_the_minimum_gap_are_one() -> None:
    escalation = Escalation()
    escalation.observe(-15.0, _events(), TIGHT, 0)

    assert escalation.observe(0.0, _events(max_count=1), TIGHT, 0) == CAUSE_NONE
    assert escalation.observe(30.0, _events(max_count=2), TIGHT, 0) == CAUSE_NONE


def test_two_events_further_apart_than_the_window_are_one_each() -> None:
    escalation = Escalation()
    escalation.observe(-15.0, _events(), TIGHT, 0)

    assert escalation.observe(0.0, _events(max_count=1), TIGHT, 0) == CAUSE_NONE
    assert escalation.observe(700.0, _events(max_count=2), TIGHT, 0) == CAUSE_NONE


def test_a_trigger_starts_the_count_afresh() -> None:
    escalation = Escalation()
    escalation.observe(-15.0, _events(), TIGHT, 0)
    escalation.observe(0.0, _events(max_count=1), TIGHT, 0)
    assert escalation.observe(90.0, _events(max_count=2), TIGHT, 0) == CAUSE_MEMORY_MAX_REPEATED

    assert escalation.observe(180.0, _events(max_count=3), TIGHT, 0) == CAUSE_NONE


def test_a_rising_oom_kill_lowers_at_once() -> None:
    escalation = Escalation()
    escalation.observe(0.0, _events(oom_kill=1), ROOMY, 0)

    assert escalation.observe(15.0, _events(oom_kill=2), ROOMY, 0) == CAUSE_OOM_KILL
    assert escalation.observe(30.0, _events(oom_kill=2), ROOMY, 0) == CAUSE_NONE


def test_a_reported_child_kill_lowers_at_once_even_without_events() -> None:
    escalation = Escalation()

    assert escalation.observe(0.0, None, None, 1) == CAUSE_OOM_KILL
    assert escalation.observe(15.0, _events(), ROOMY, 2) == CAUSE_OOM_KILL


def test_cgroup_v1_without_kills_never_triggers() -> None:
    escalation = Escalation()

    for tick in range(100):
        assert escalation.observe(tick * 15.0, None, TIGHT, 0) == CAUSE_NONE


def test_a_counter_that_falls_only_resets_the_base() -> None:
    # A new cgroup after a restart starts at zero; a fall is no event.
    escalation = Escalation()
    escalation.observe(0.0, _events(max_count=50, oom_kill=4), TIGHT, 0)

    assert escalation.observe(90.0, _events(max_count=1, oom_kill=0), TIGHT, 0) == CAUSE_NONE
    assert escalation.observe(105.0, _events(max_count=1, oom_kill=1), TIGHT, 0) == CAUSE_OOM_KILL


# --- lowering (D-26-01, D-24-07) ------------------------------------------------


def test_lowering_caps_the_effective_level_and_keeps_the_chosen_profile() -> None:
    _performance_box()
    before = guard.snapshot().revision

    assert guard.lower(CAUSE_OOM_KILL, now=1000.0, chosen=Profile.PERFORMANCE, effective=Profile.PERFORMANCE)

    state = guard.snapshot()
    assert state.cap == Profile.STANDARD
    assert state.cause == CAUSE_OOM_KILL
    assert state.since == 1000.0
    assert state.chosen == Profile.PERFORMANCE
    assert re.fullmatch(r"[0-9a-f]{32}", state.token)
    assert state.revision == before + 1
    assert profile.snapshot().effective == Profile.STANDARD
    assert profile.snapshot().chosen == Profile.PERFORMANCE
    assert profile.snapshot().cap == Profile.STANDARD


def test_economy_is_the_floor() -> None:
    before = guard.snapshot()

    assert not guard.lower(CAUSE_OOM_KILL, now=1.0, chosen=Profile.ECONOMY, effective=Profile.ECONOMY)
    assert guard.snapshot() == before
    assert profile.snapshot().cap is None


def test_lowering_twice_goes_down_one_level_each_time() -> None:
    _performance_box()

    assert guard.lower(CAUSE_OOM_KILL, now=1.0, chosen=Profile.PERFORMANCE, effective=Profile.PERFORMANCE)
    first_token = guard.snapshot().token
    assert guard.lower(
        CAUSE_MEMORY_MAX_REPEATED, now=2.0, chosen=Profile.PERFORMANCE, effective=profile.snapshot().effective
    )

    assert guard.snapshot().cap == Profile.ECONOMY
    assert guard.snapshot().cause == CAUSE_MEMORY_MAX_REPEATED
    assert guard.snapshot().token != first_token
    assert profile.snapshot().effective == Profile.ECONOMY
    assert not guard.lower(CAUSE_OOM_KILL, now=3.0, chosen=Profile.PERFORMANCE, effective=Profile.ECONOMY)


def test_an_unknown_cause_is_a_programming_error() -> None:
    with pytest.raises(ValueError, match="cause"):
        guard.lower("x", now=1.0, chosen=Profile.PERFORMANCE, effective=Profile.PERFORMANCE)
    with pytest.raises(ValueError, match="cause"):
        guard.lower(CAUSE_NONE, now=1.0, chosen=Profile.PERFORMANCE, effective=Profile.PERFORMANCE)


# --- the way back (D-26-04) -----------------------------------------------------


def _lowered() -> str:
    _performance_box()
    guard.lower(CAUSE_OOM_KILL, now=1.0, chosen=Profile.PERFORMANCE, effective=Profile.PERFORMANCE)
    return guard.snapshot().token


def test_the_matching_token_lifts_the_cap() -> None:
    token = _lowered()
    before = guard.snapshot().revision

    assert guard.note_confirmation(token, "performance")

    state = guard.snapshot()
    assert state.cap is None
    assert state.cause == CAUSE_NONE
    assert state.token == ""
    assert state.since is None
    assert state.revision == before + 1
    assert profile.snapshot().effective == Profile.PERFORMANCE


def test_a_wrong_token_with_the_same_profile_changes_nothing() -> None:
    _lowered()
    before = guard.snapshot()

    assert not guard.note_confirmation("0" * 32, "performance")
    assert not guard.note_confirmation(None, "performance")
    # A tampered appconfig value outside ASCII must not raise either.
    assert not guard.note_confirmation("ä" * 32, "performance")
    assert guard.snapshot() == before


def test_another_profile_lifts_the_cap() -> None:
    _lowered()

    assert guard.note_confirmation(None, "standard")
    assert guard.snapshot().cap is None


def test_a_chosen_profile_that_was_not_read_changes_nothing() -> None:
    # D-24-02: a missing answer keeps what was known.
    token = _lowered()

    assert not guard.note_confirmation(token, None)
    assert not guard.note_confirmation(None, "turbo")
    assert guard.snapshot().cap == Profile.STANDARD


def test_confirming_without_a_cap_changes_nothing() -> None:
    before = guard.snapshot()

    assert not guard.note_confirmation("a" * 32, "standard")
    assert guard.snapshot() == before


def test_restore_brings_a_stored_cap_back() -> None:
    _performance_box()
    token = "0123456789abcdef" * 2

    assert guard.restore("standard", "oom_kill", "1700000000.5", token, "performance")

    state = guard.snapshot()
    assert state.cap == Profile.STANDARD
    assert state.cause == CAUSE_OOM_KILL
    assert state.since == 1700000000.5
    assert state.token == token
    assert state.chosen == Profile.PERFORMANCE
    assert profile.snapshot().effective == Profile.STANDARD


@pytest.mark.parametrize(
    ("cap", "cause", "since", "token", "chosen"),
    [
        ("turbo", "oom_kill", "1.0", "a" * 32, "performance"),
        ("standard", "x", "1.0", "a" * 32, "performance"),
        ("standard", "", "1.0", "a" * 32, "performance"),
        ("standard", "oom_kill", "1.0", "a" * 31, "performance"),
        ("standard", "oom_kill", "1.0", "A" * 32, "performance"),
        ("standard", "oom_kill", "1.0", "g" * 32, "performance"),
        ("standard", "oom_kill", "1.0", "a" * 32, "turbo"),
        ("standard", "oom_kill", "1.0", "a" * 32, None),
        ("standard", "oom_kill", "yesterday", "a" * 32, "performance"),
        ("standard", "oom_kill", "nan", "a" * 32, "performance"),
        ("standard", "oom_kill", None, "a" * 32, "performance"),
        (None, "oom_kill", "1.0", "a" * 32, "performance"),
    ],
)
def test_restore_drops_foreign_words(
    cap: str | None, cause: str | None, since: str | None, token: str | None, chosen: str | None
) -> None:
    before = guard.snapshot()

    assert not guard.restore(cap, cause, since, token, chosen)
    assert guard.snapshot() == before
    assert profile.snapshot().cap is None


# --- slots and kills ------------------------------------------------------------


def test_the_slots_in_force_are_reported() -> None:
    guard.note_slots(4, 2)
    state = guard.snapshot()
    assert state.slots_target == 4
    assert state.slots_in_force == 2
    assert state.throttled

    guard.note_slots(4, 4)
    assert not guard.snapshot().throttled


def test_child_kills_are_counted_across_threads() -> None:
    def report() -> None:
        for _ in range(100):
            guard.report_child_kill()

    threads = [threading.Thread(target=report) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert guard.take_child_kills() == 200
    assert guard.take_child_kills() == 0


def test_the_resting_state() -> None:
    state = guard.snapshot()
    assert state.cap is None
    assert state.cause == CAUSE_NONE
    assert state.since is None
    assert state.token == ""
    assert state.chosen is None
    assert state.slots_target == 1
    assert state.slots_in_force == 1
    assert not state.throttled
    assert state.revision == 0


def test_reset_forgets_the_cap_and_the_kills() -> None:
    _lowered()
    guard.report_child_kill()
    guard.reset()

    assert guard.snapshot().cap is None
    assert guard.take_child_kills() == 0
    assert profile.snapshot().cap is None
