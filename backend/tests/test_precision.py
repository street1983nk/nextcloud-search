"""The precision state machine: when which weights apply, when to fetch, what to report.

Pure state, no I/O. The cases pin the owner decisions of phase 25: never switch
before the first read and the settled start (D-25-03, D-25-14), fetch only on a
change from int8 to fp32 seen in this process and only once (D-25-04), fp32 only
under Standard or Performance (D-25-01, D-25-10), activate a verified file
without a download (D-25-06), and int8 is always the way back (D-25-09).
"""

import pytest

from findling import precision, profile
from findling.hardware import Hardware
from findling.precision import (
    VERDICT_ACTIVE_IN_ECONOMY,
    VERDICT_DOWNLOADING,
    VERDICT_NONE,
    VERDICT_NOT_IN_ECONOMY,
    VERDICT_TIGHT_BOX,
    VERDICT_UNAVAILABLE,
    VERDICTS,
    Precision,
    PrecisionDecision,
)
from findling.profile import Profile

GIB = 1024**3


def big_box() -> Hardware:
    """A box that fits Performance, so the chosen profile is also the effective one."""
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


def tight_box() -> Hardware:
    """A box that only fits economy."""
    return Hardware(
        cpu_count=2,
        cpu_quota=None,
        cores=2,
        memory_limit_bytes=None,
        memory_available_bytes=4 * GIB,
        memory_total_bytes=4 * GIB,
        architecture="aarch64",
        cgroup="none",
    )


@pytest.fixture
def standard() -> None:
    profile.note_hardware(big_box())
    profile.note_chosen("standard")


@pytest.fixture
def economy() -> None:
    profile.note_hardware(big_box())
    profile.note_chosen("economy")


def test_the_verdicts_are_a_closed_set() -> None:
    assert frozenset(
        {
            VERDICT_NONE,
            VERDICT_DOWNLOADING,
            VERDICT_UNAVAILABLE,
            VERDICT_NOT_IN_ECONOMY,
            VERDICT_TIGHT_BOX,
            VERDICT_ACTIVE_IN_ECONOMY,
        }
    ) == VERDICTS


def test_the_resting_state_decides_nothing() -> None:
    """Pitfall 6: before anything was read there is no target at all."""
    state = precision.snapshot()
    assert state.chosen is None
    assert state.active is None
    assert state.verdict == VERDICT_NONE
    assert not state.procuring
    assert not state.settled
    assert precision.decide(fp32_ready=False) == PrecisionDecision(target=None, procure=False)


def test_a_settled_start_without_a_read_decides_nothing() -> None:
    """D-25-14: a fp32 start state alone never moves anything before the first read."""
    precision.settle(Precision.FP32)
    assert precision.snapshot().settled
    assert precision.decide(fp32_ready=True).target is None
    assert precision.decide(fp32_ready=False).target is None


def test_a_read_without_a_settled_start_decides_nothing() -> None:
    """D-25-14: the start state comes from mark plus verified file, never from a guess."""
    precision.note_chosen_precision("int8")
    assert precision.decide(fp32_ready=False).target is None


def test_only_the_first_settle_counts() -> None:
    precision.settle(Precision.INT8)
    precision.settle(Precision.FP32)
    assert precision.snapshot().active is Precision.INT8


@pytest.mark.usefixtures("standard")
def test_fp32_on_the_first_read_never_downloads() -> None:
    """D-25-14: the first read is no observed change, so it never fetches."""
    precision.note_chosen_precision("fp32")
    precision.settle(Precision.INT8)
    decision = precision.decide(fp32_ready=False)
    assert decision == PrecisionDecision(target=Precision.INT8, procure=False)
    assert precision.snapshot().verdict == VERDICT_UNAVAILABLE


@pytest.mark.usefixtures("standard")
def test_a_change_to_fp32_downloads_once_and_a_failure_is_not_retried() -> None:
    """D-25-04: one fetch per observed int8 to fp32 change, no retry after a failure."""
    precision.note_chosen_precision("int8")
    precision.settle(Precision.INT8)
    precision.note_chosen_precision("fp32")

    assert precision.decide(fp32_ready=False) == PrecisionDecision(target=Precision.INT8, procure=True)
    assert not precision.decide(fp32_ready=False).procure

    precision.begin_procurement()
    assert precision.snapshot().procuring
    assert precision.snapshot().verdict == VERDICT_DOWNLOADING

    precision.end_procurement(succeeded=False)
    assert not precision.snapshot().procuring
    assert precision.snapshot().verdict == VERDICT_UNAVAILABLE
    for _ in range(3):
        precision.note_chosen_precision("fp32")
        assert not precision.decide(fp32_ready=False).procure

    # A fresh admin action: back to int8, then fp32 again.
    precision.note_chosen_precision("int8")
    assert precision.snapshot().verdict == VERDICT_NONE
    precision.note_chosen_precision("fp32")
    assert precision.decide(fp32_ready=False).procure


@pytest.mark.usefixtures("standard")
def test_a_successful_download_activates_fp32() -> None:
    """D-25-04: the fetched and verified file is taken up on the next decision."""
    precision.note_chosen_precision("int8")
    precision.settle(Precision.INT8)
    precision.note_chosen_precision("fp32")
    assert precision.decide(fp32_ready=False).procure
    precision.begin_procurement()
    precision.end_procurement(succeeded=True)
    assert precision.decide(fp32_ready=True) == PrecisionDecision(target=Precision.FP32, procure=False)
    precision.note_active(Precision.FP32)
    assert precision.snapshot().active is Precision.FP32
    assert precision.snapshot().verdict == VERDICT_NONE


@pytest.mark.usefixtures("standard")
def test_a_sideloaded_file_is_activated_without_a_download() -> None:
    """D-25-06: a verified file placed by the admin needs no fetch."""
    precision.note_chosen_precision("fp32")
    precision.settle(Precision.INT8)
    assert precision.decide(fp32_ready=True) == PrecisionDecision(target=Precision.FP32, procure=False)


@pytest.mark.usefixtures("economy")
def test_fp32_under_economy_is_refused_and_not_caught_up_later() -> None:
    """D-25-10: a wish under economy is used up; a later profile switch fetches nothing."""
    precision.note_chosen_precision("int8")
    precision.settle(Precision.INT8)
    precision.note_chosen_precision("fp32")

    assert precision.decide(fp32_ready=False) == PrecisionDecision(target=Precision.INT8, procure=False)
    assert precision.snapshot().verdict == VERDICT_NOT_IN_ECONOMY

    profile.note_chosen("standard")
    assert precision.decide(fp32_ready=False) == PrecisionDecision(target=Precision.INT8, procure=False)
    assert precision.decide(fp32_ready=True).target is Precision.INT8
    assert precision.snapshot().verdict == VERDICT_NOT_IN_ECONOMY


@pytest.mark.usefixtures("economy")
def test_fp32_on_the_first_read_under_economy_is_refused() -> None:
    """D-25-10: a verified file does not lift the economy rule either."""
    precision.note_chosen_precision("fp32")
    precision.settle(Precision.INT8)
    assert precision.decide(fp32_ready=True) == PrecisionDecision(target=Precision.INT8, procure=False)
    assert precision.snapshot().verdict == VERDICT_NOT_IN_ECONOMY


@pytest.mark.usefixtures("economy")
def test_an_active_fp32_stays_under_economy() -> None:
    """D-25-10: fp32 once active stays until the key says int8, and the status says so."""
    precision.note_chosen_precision("fp32")
    precision.settle(Precision.FP32)
    assert precision.decide(fp32_ready=True) == PrecisionDecision(target=Precision.FP32, procure=False)
    assert precision.snapshot().verdict == VERDICT_ACTIVE_IN_ECONOMY


def test_an_active_fp32_stays_on_a_shrunk_box() -> None:
    """D-25-03: Standard chosen, economy in effect after the box shrank: fp32 stays."""
    profile.note_hardware(tight_box())
    profile.note_chosen("standard")
    assert profile.snapshot().effective is Profile.ECONOMY
    precision.note_chosen_precision("fp32")
    precision.settle(Precision.FP32)
    assert precision.decide(fp32_ready=True).target is Precision.FP32
    assert precision.snapshot().verdict == VERDICT_TIGHT_BOX


@pytest.mark.usefixtures("standard")
def test_int8_is_the_way_back() -> None:
    """D-25-09: int8 chosen while fp32 runs gives the target int8."""
    precision.note_chosen_precision("fp32")
    precision.settle(Precision.FP32)
    precision.note_chosen_precision("int8")
    assert precision.decide(fp32_ready=True) == PrecisionDecision(target=Precision.INT8, procure=False)


@pytest.mark.usefixtures("standard")
def test_none_or_unknown_change_nothing() -> None:
    """D-24-02 semantics: a missing or tampered value keeps what was read before."""
    precision.note_chosen_precision("int8")
    precision.settle(Precision.INT8)
    precision.note_chosen_precision(None)
    precision.note_chosen_precision("fp16")
    assert precision.snapshot().chosen is Precision.INT8
    # Garbage between int8 and fp32 does not break the observed change.
    precision.note_chosen_precision("fp32")
    assert precision.decide(fp32_ready=False).procure


def test_the_precision_in_force_is_reported_to_the_profile() -> None:
    """The slot formula sees fp32 while it runs, is fetched or is chosen and allowed."""
    profile.note_hardware(big_box())
    profile.note_chosen("standard")
    assert profile.snapshot().weights == "int8"
    precision.note_chosen_precision("int8")
    precision.settle(Precision.INT8)
    assert profile.snapshot().weights == "int8"
    precision.note_chosen_precision("fp32")
    assert profile.snapshot().weights == "fp32"
    precision.decide(fp32_ready=False)
    precision.begin_procurement()
    assert profile.snapshot().weights == "fp32"
    precision.end_procurement(succeeded=False)
    assert profile.snapshot().weights == "int8"
    precision.note_chosen_precision("int8")
    precision.note_chosen_precision("fp32")
    precision.note_active(Precision.FP32)
    precision.note_chosen_precision("int8")
    assert profile.snapshot().weights == "fp32"
    precision.note_active(Precision.INT8)
    assert profile.snapshot().weights == "int8"


@pytest.mark.usefixtures("economy")
def test_fp32_chosen_under_economy_is_not_in_force() -> None:
    precision.note_chosen_precision("fp32")
    assert profile.snapshot().weights == "int8"


def test_reset_restores_the_resting_state() -> None:
    profile.note_hardware(big_box())
    profile.note_chosen("standard")
    precision.note_chosen_precision("fp32")
    precision.settle(Precision.FP32)
    precision.begin_procurement()
    precision.reset()
    state = precision.snapshot()
    assert state.chosen is None
    assert state.active is None
    assert not state.procuring
    assert state.verdict == VERDICT_NONE
    assert profile.snapshot().weights == "int8"
    # settle works again after a reset.
    precision.settle(Precision.INT8)
    assert precision.snapshot().active is Precision.INT8
