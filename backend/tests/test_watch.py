"""The memory guard task of plan 26-10: tick, escalation, persistence, restore.

Every case runs against a state.db in tmp_path and fake readers; no case reads
the cgroup of the machine the suite runs on, and no case waits for the tick.
"""

import asyncio
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from findling import guard, probe, profile
from findling.hardware import Hardware
from findling.profile import Profile
from findling.store.repo import open_store
from findling.worker.watch import GuardWatch

MIB = 1024 * 1024
_TOKEN = "0123456789abcdef0123456789abcdef"  # noqa: S105 - a well formed guard token for the test, no secret


def _big_box() -> Hardware:
    """A box that fits Performance, so the effective level follows the chosen one."""
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


def _at_level(chosen: str) -> None:
    profile.note_hardware(_big_box())
    profile.note_chosen(chosen)


@pytest.fixture
def state_db(tmp_path: Path) -> Path:
    path = tmp_path / "state.db"
    open_store(path).close()
    return path


def _meta(path: Path) -> dict[str, str]:
    store = open_store(path)
    try:
        return store.read_meta()
    finally:
        store.close()


def _write(path: Path, values: dict[str, str]) -> None:
    store = open_store(path)
    try:
        for key, value in values.items():
            store.write_meta(key, value)
    finally:
        store.close()


class _Clock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


class _Readings:
    """memory.events and headroom as a test sets them, tick by tick."""

    def __init__(self, events: dict[str, int] | None, headroom: int | None) -> None:
        self.events = events
        self.headroom = headroom

    def read_events(self) -> dict[str, int] | None:
        return None if self.events is None else dict(self.events)

    def read_headroom(self) -> int | None:
        return self.headroom


def _watch(state_db: Path, readings: _Readings, clock: _Clock) -> GuardWatch:
    return GuardWatch(
        state_path=state_db,
        events=readings.read_events,
        headroom=readings.read_headroom,
        clock=clock,
        wall_clock=lambda: 1_700_000_000.0,
        tick=0.0,
    )


# -- restore ---------------------------------------------------------------


async def test_restore_on_an_empty_state_db_leaves_the_guard_resting(state_db: Path) -> None:
    watch = _watch(state_db, _Readings(None, None), _Clock())
    try:
        await watch.restore()
    finally:
        await watch.aclose()

    assert guard.snapshot().cap is None
    assert guard.snapshot().cause == guard.CAUSE_NONE


async def test_restore_without_a_state_db_creates_none(tmp_path: Path) -> None:
    missing = tmp_path / "state.db"
    watch = GuardWatch(state_path=missing)
    await watch.restore()
    await watch.note_shutdown_begins()
    await watch.aclose()

    assert not missing.exists()
    assert guard.snapshot().cap is None


async def test_restore_brings_a_stored_cap_back(state_db: Path) -> None:
    _at_level("performance")
    _write(
        state_db,
        {
            guard.META_CAP: "standard",
            guard.META_CAUSE: "oom_kill",
            guard.META_SINCE: "1700000000.5",
            guard.META_TOKEN: _TOKEN,
            guard.META_CHOSEN: "performance",
        },
    )
    watch = _watch(state_db, _Readings(None, None), _Clock())
    try:
        await watch.restore()
    finally:
        await watch.aclose()

    state = guard.snapshot()
    assert (state.cap, state.cause, state.since, state.token, state.chosen) == (
        Profile.STANDARD,
        "oom_kill",
        1700000000.5,
        _TOKEN,
        Profile.PERFORMANCE,
    )
    assert profile.PROFILE_ORDER.index(profile.snapshot().effective) <= profile.PROFILE_ORDER.index(Profile.STANDARD)


async def test_restore_answers_an_unclean_end_with_a_lowering(state_db: Path) -> None:
    _at_level("performance")
    _write(state_db, {guard.META_MULTI_SLOT_PASS: "performance", guard.META_MULTI_SLOT_CHOSEN: "performance"})
    watch = _watch(state_db, _Readings(None, None), _Clock())
    try:
        await watch.restore()
    finally:
        await watch.aclose()

    state = guard.snapshot()
    assert state.cap is Profile.STANDARD
    assert state.cause == guard.CAUSE_UNCLEAN_END
    meta = _meta(state_db)
    assert meta[guard.META_CAP] == "standard"
    assert meta[guard.META_CAUSE] == guard.CAUSE_UNCLEAN_END
    assert meta[guard.META_CHOSEN] == "performance"
    assert len(meta[guard.META_TOKEN]) == 32
    assert meta[guard.META_MULTI_SLOT_PASS] == ""
    assert meta[guard.META_MULTI_SLOT_CHOSEN] == "", "the stale choice leaves with the mark (review WR-02)"


@pytest.mark.parametrize("mark", ["economy", ""])
async def test_restore_ignores_a_pass_mark_at_economy_or_empty(state_db: Path, mark: str) -> None:
    _at_level("performance")
    _write(state_db, {guard.META_MULTI_SLOT_PASS: mark, guard.META_MULTI_SLOT_CHOSEN: "performance"})
    watch = _watch(state_db, _Readings(None, None), _Clock())
    try:
        await watch.restore()
    finally:
        await watch.aclose()

    assert guard.snapshot().cap is None
    assert _meta(state_db).get(guard.META_CAP, "") == ""


async def test_restore_sweeps_a_choice_that_lost_its_pass_mark(state_db: Path) -> None:
    # Review WR-02, the crash the new write order leaves behind: CHOSEN is
    # written first and the container dies before the PASS write. That state
    # must lower nothing, and the leftover choice is swept so it can never sit
    # beside the mark of a LATER staffel run under another profile, which is
    # the pairing that lifted a cap without the admin (D-26-04).
    _at_level("performance")
    _write(state_db, {guard.META_MULTI_SLOT_PASS: "", guard.META_MULTI_SLOT_CHOSEN: "standard"})
    watch = _watch(state_db, _Readings(None, None), _Clock())
    try:
        await watch.restore()
    finally:
        await watch.aclose()

    assert guard.snapshot().cap is None
    meta = _meta(state_db)
    assert meta[guard.META_MULTI_SLOT_PASS] == ""
    assert meta[guard.META_MULTI_SLOT_CHOSEN] == ""


# -- the tick --------------------------------------------------------------


async def test_two_qualified_ticks_lower_performance_to_standard(state_db: Path) -> None:
    _at_level("performance")
    readings = _Readings({"max": 0, "oom_kill": 0}, 100 * MIB)
    clock = _Clock()
    watch = _watch(state_db, readings, clock)
    try:
        assert await watch.run_once() == guard.CAUSE_NONE  # the base
        readings.events = {"max": 3, "oom_kill": 0}
        assert await watch.run_once() == guard.CAUSE_NONE  # the first event
        clock.now += 90
        readings.events = {"max": 7, "oom_kill": 0}
        assert await watch.run_once() == guard.CAUSE_MEMORY_MAX_REPEATED
    finally:
        await watch.aclose()

    assert guard.snapshot().cap is Profile.STANDARD
    assert profile.snapshot().effective is Profile.STANDARD
    meta = _meta(state_db)
    assert meta[guard.META_CAP] == "standard"
    assert meta[guard.META_CAUSE] == guard.CAUSE_MEMORY_MAX_REPEATED
    assert meta[guard.META_CHOSEN] == "performance"
    assert meta[guard.META_TOKEN] == guard.snapshot().token


async def test_a_rising_oom_kill_lowers_at_once(state_db: Path) -> None:
    _at_level("performance")
    readings = _Readings({"max": 0, "oom_kill": 0}, 4000 * MIB)
    watch = _watch(state_db, readings, _Clock())
    try:
        await watch.run_once()
        readings.events = {"max": 0, "oom_kill": 1}
        assert await watch.run_once() == guard.CAUSE_OOM_KILL
    finally:
        await watch.aclose()

    assert guard.snapshot().cap is Profile.STANDARD
    assert _meta(state_db)[guard.META_CAUSE] == guard.CAUSE_OOM_KILL


@pytest.fixture
def probe_hold() -> Iterator[None]:
    """A pre-check runs its own children for the test; released and reset after it."""
    probe.hold()
    probe.measure()
    yield
    probe.reset()


async def test_a_kill_in_the_pass_the_pause_waits_for_still_lowers(state_db: Path) -> None:
    """Review WR-09 of phase 27: the hold alone does not suspend the guard.

    The pause of a check waits up to PROBE_PAUSE_SECONDS for the regular pass,
    which still runs with its slots; a kill in that pass is real pressure.
    """
    probe.hold()
    try:
        assert not probe.measuring()
        _at_level("performance")
        readings = _Readings({"max": 0, "oom_kill": 0}, 4000 * MIB)
        watch = _watch(state_db, readings, _Clock())
        try:
            await watch.run_once()
            readings.events = {"max": 0, "oom_kill": 1}
            assert await watch.run_once() == guard.CAUSE_OOM_KILL
        finally:
            await watch.aclose()
        assert guard.snapshot().cap is Profile.STANDARD
    finally:
        probe.reset()


@pytest.mark.usefixtures("probe_hold")
async def test_a_kill_during_the_pre_check_lowers_nothing_and_is_dropped(state_db: Path) -> None:
    # D-27-15, Pitfall 3: a killed probe child must not lower the chosen profile.
    _at_level("performance")
    readings = _Readings({"max": 0, "oom_kill": 0}, 4000 * MIB)
    watch = _watch(state_db, readings, _Clock())
    try:
        await watch.run_once()
        readings.events = {"max": 0, "oom_kill": 1}
        guard.report_child_kill()
        assert await watch.run_once() == guard.CAUSE_NONE
    finally:
        await watch.aclose()

    assert guard.snapshot().cap is None
    assert guard.take_child_kills() == 0


@pytest.mark.usefixtures("probe_hold")
async def test_the_first_tick_after_the_pre_check_is_suspended_as_well(state_db: Path) -> None:
    # The kernel reports an event late, so one tick after the release still
    # only moves the base.
    _at_level("performance")
    readings = _Readings({"max": 0, "oom_kill": 0}, 4000 * MIB)
    watch = _watch(state_db, readings, _Clock())
    try:
        await watch.run_once()
        probe.release()
        readings.events = {"max": 0, "oom_kill": 1}
        guard.report_child_kill()
        assert await watch.run_once() == guard.CAUSE_NONE
        assert guard.snapshot().cap is None
        assert guard.take_child_kills() == 0

        # From the second tick after the release an event counts again.
        readings.events = {"max": 0, "oom_kill": 2}
        assert await watch.run_once() == guard.CAUSE_OOM_KILL
    finally:
        await watch.aclose()

    assert guard.snapshot().cap is Profile.STANDARD


@pytest.mark.usefixtures("probe_hold")
async def test_a_child_kill_counts_again_from_the_second_tick_after_the_pre_check(state_db: Path) -> None:
    _at_level("performance")
    watch = _watch(state_db, _Readings(None, None), _Clock())
    try:
        await watch.run_once()
        probe.release()
        await watch.run_once()
        guard.report_child_kill()
        assert await watch.run_once() == guard.CAUSE_OOM_KILL
    finally:
        await watch.aclose()

    assert guard.snapshot().cap is Profile.STANDARD


async def test_a_reported_child_kill_lowers_even_on_cgroup_v1(state_db: Path) -> None:
    _at_level("performance")
    guard.report_child_kill()
    watch = _watch(state_db, _Readings(None, None), _Clock())
    try:
        assert await watch.run_once() == guard.CAUSE_OOM_KILL
    finally:
        await watch.aclose()

    assert guard.snapshot().cap is Profile.STANDARD
    assert guard.snapshot().cause == guard.CAUSE_OOM_KILL
    assert _meta(state_db)[guard.META_CAP] == "standard"


async def test_at_economy_the_guard_does_not_lower_and_writes_nothing(state_db: Path) -> None:
    # No chosen profile: the effective level is economy.
    profile.note_hardware(_big_box())
    guard.report_child_kill()
    watch = _watch(state_db, _Readings(None, None), _Clock())
    try:
        assert await watch.run_once() == guard.CAUSE_OOM_KILL
    finally:
        await watch.aclose()

    assert guard.snapshot().cap is None
    assert guard.META_CAP not in _meta(state_db)


async def test_a_confirmed_cap_is_cleared_in_state_db(state_db: Path) -> None:
    _at_level("performance")
    guard.report_child_kill()
    watch = _watch(state_db, _Readings(None, None), _Clock())
    try:
        await watch.run_once()
        assert _meta(state_db)[guard.META_CAP] == "standard"
        assert guard.note_confirmation(guard.snapshot().token, "performance") is True
        await watch.run_once()
    finally:
        await watch.aclose()

    meta = _meta(state_db)
    assert meta[guard.META_CAP] == ""
    assert meta[guard.META_CAUSE] == ""
    assert meta[guard.META_TOKEN] == ""
    assert profile.snapshot().effective is Profile.PERFORMANCE


async def test_note_shutdown_begins_clears_the_pass_mark(state_db: Path) -> None:
    _write(state_db, {guard.META_MULTI_SLOT_PASS: "performance", guard.META_MULTI_SLOT_CHOSEN: "performance"})
    watch = _watch(state_db, _Readings(None, None), _Clock())
    try:
        await watch.note_shutdown_begins()
    finally:
        await watch.aclose()

    meta = _meta(state_db)
    assert meta[guard.META_MULTI_SLOT_PASS] == ""
    assert meta[guard.META_MULTI_SLOT_CHOSEN] == "", "both keys go together (review WR-02)"


async def test_a_reader_that_throws_does_not_end_the_task(state_db: Path, caplog: pytest.LogCaptureFixture) -> None:
    calls: list[int] = []
    stop = asyncio.Event()

    def throwing() -> dict[str, int] | None:
        calls.append(1)
        if len(calls) >= 3:
            stop.set()
        raise PermissionError("/sys/fs/cgroup/a/path/the/log/must/never/carry")

    watch = GuardWatch(state_path=state_db, events=throwing, headroom=lambda: None, tick=0.0)
    caplog.set_level(logging.ERROR, logger="findling.worker.watch")
    try:
        await asyncio.wait_for(watch.run(stop), timeout=5.0)
    finally:
        await watch.aclose()

    assert len(calls) == 3
    said = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]
    assert len(said) == 3
    assert all("PermissionError" in line for line in said)
    assert all("/sys" not in line for line in said)


async def test_the_lowering_line_carries_cause_and_level_and_no_token(
    state_db: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _at_level("performance")
    guard.report_child_kill()
    watch = _watch(state_db, _Readings(None, None), _Clock())
    caplog.set_level(logging.INFO, logger="findling.worker.watch")
    try:
        await watch.run_once()
    finally:
        await watch.aclose()

    lines = [record.getMessage() for record in caplog.records]
    assert any("cause=oom_kill level=standard" in line for line in lines)
    assert all(guard.snapshot().token not in line for line in lines)
