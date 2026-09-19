"""The third long lived task of the lifespan: the tick that lets both holders go.

The nine claims of the behaviour block of plan 14-07, one case each, and the
cases the plan asks for on top of them: the order of the two releases, the
source level gates, and the end of the task with the lifespan.

**No case waits a second.** ``_pause`` is replaced by a stand in that returns at
once and sets the stop event after a fixed number of ticks, so the cadence of
the container (30 s) never reaches the suite. A test that ran for half a minute
is a test somebody switches off, and the tick length itself is asserted in one
case rather than waited out in all of them.

**No case measures memory.** All of them count calls and read return values. A
memory threshold on a shared runner goes red for the load of the runner and not
for the thing it names, and that reasoning is already written down in the head
of ``tools/one_load.py``.
"""

import ast
import asyncio
import inspect
import logging

import pytest
from fastapi.testclient import TestClient

from findling.config import settings
from findling.main import APP, RELEASE_TICK_SECONDS, _release_when_idle


class _FakeReleaseTask:
    """A stand in for the third task, so the lifespan cases need no tick at all."""

    def __init__(self) -> None:
        self.starts = 0
        self.stops = 0

    async def run(self, stop_event: asyncio.Event) -> None:
        self.starts += 1
        await stop_event.wait()
        self.stops += 1


class _EngineSpy:
    """The three engine functions of the tick, counting instead of loading."""

    def __init__(self, *, warm_is_wanted: bool = False, releases: bool = False) -> None:
        self._warm_is_wanted = warm_is_wanted
        self._releases = releases
        self.warm_runs = 0
        self.ttls: list[int] = []
        self.order: list[str] = []
        self.fail_once_with: BaseException | None = None

    def warm_wanted(self) -> bool:
        self.order.append("warm_wanted")
        return self._warm_is_wanted

    def warm(self) -> bool:
        self.order.append("warm")
        self.warm_runs += 1
        return True

    def release_if_idle(self, ttl_seconds: int) -> bool:
        self.order.append("release_if_idle")
        self.ttls.append(ttl_seconds)
        if self.fail_once_with is not None:
            failure, self.fail_once_with = self.fail_once_with, None
            raise failure
        return self._releases

    def install(self, monkeypatch: pytest.MonkeyPatch) -> "_EngineSpy":
        monkeypatch.setattr("findling.main.warm_wanted", self.warm_wanted)
        monkeypatch.setattr("findling.main.warm", self.warm)
        monkeypatch.setattr("findling.main.release_if_idle", self.release_if_idle)
        return self


class _FakePoller:
    """A poller that answers the one question the release task asks it.

    ``armed`` is carried here and never read by the task under test. It exists
    so that the silenced case can say in an assertion what it is about instead
    of only in its name.
    """

    def __init__(self, *, busy: bool = False, armed: bool = True, journal: list[str] | None = None) -> None:
        self._busy = busy
        self.armed = armed
        self.journal = journal if journal is not None else []
        self.cutter_releases = 0

    @property
    def busy(self) -> bool:
        return self._busy

    def release_cutter(self) -> bool:
        self.journal.append("release_cutter")
        self.cutter_releases += 1
        return True


def _ticks(monkeypatch: pytest.MonkeyPatch, count: int) -> list[float]:
    """Let exactly ``count`` ticks run, then stop, and never wait for anything.

    The returned list carries the cadence every call was asked for, which is how
    one case can assert the tick length without any case sleeping through it.
    """
    seconds_asked_for: list[float] = []

    async def instant_pause(seconds: float, stop_event: asyncio.Event) -> None:
        seconds_asked_for.append(seconds)
        if len(seconds_asked_for) > count:
            stop_event.set()
        # Still a suspension point, exactly like the pause it stands in for.
        await asyncio.sleep(0)

    monkeypatch.setattr("findling.main._pause", instant_pause)
    return seconds_asked_for


async def _run_the_task() -> None:
    """Run the task to its end, and fail loudly instead of hanging the suite."""
    await asyncio.wait_for(_release_when_idle(asyncio.Event()), timeout=5.0)


# The three calls that block. Two of them collect and trim, the third one loads,
# and every one of them has to reach a worker thread (T-14-23).
BLOCKING_CALLS = frozenset({"warm", "release_if_idle", "release_cutter"})


def _the_tick_as_a_tree() -> ast.AsyncFunctionDef:
    """The task read as source, so a gate can hold what the next edit may do."""
    parsed = ast.parse(inspect.getsource(_release_when_idle)).body[0]
    assert isinstance(parsed, ast.AsyncFunctionDef)
    return parsed


def _name_behind(node: ast.expr) -> str:
    """The bare name of a call target or of a function passed as an argument."""
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


# ---------------------------------------------------------------------------
# Whether the task exists at all. The switch is off in the factory setting, so
# the ordinary container of today must not grow a third task.
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("volume")
def test_the_release_task_is_not_created_when_the_switch_is_off(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    fake = _FakeReleaseTask()
    monkeypatch.setattr("findling.main._release_when_idle", fake.run)
    monkeypatch.delenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", raising=False)
    settings.cache_clear()
    caplog.set_level(logging.INFO, logger="findling")

    with TestClient(APP):
        pass

    assert fake.starts == 0
    # And no line about it either. The factory setting is off, so a line at
    # every start about a feature nobody switched on is noise.
    assert [record for record in caplog.records if "release" in record.getMessage()] == []


@pytest.mark.usefixtures("volume")
def test_the_release_task_is_created_when_the_switch_is_on(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    fake = _FakeReleaseTask()
    monkeypatch.setattr("findling.main._release_when_idle", fake.run)
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", "60")
    settings.cache_clear()
    caplog.set_level(logging.INFO, logger="findling")

    with TestClient(APP):
        pass

    assert fake.starts == 1
    assert [record for record in caplog.records if "release" in record.getMessage()] != []


# ---------------------------------------------------------------------------
# The tick and its four conditions.
# ---------------------------------------------------------------------------


async def test_a_tick_runs_on_the_configured_cadence(monkeypatch: pytest.MonkeyPatch) -> None:
    _EngineSpy().install(monkeypatch)
    monkeypatch.setattr("findling.main._POLLER", None)
    asked = _ticks(monkeypatch, 1)

    await _run_the_task()

    assert asked == [RELEASE_TICK_SECONDS, RELEASE_TICK_SECONDS]


async def test_a_tick_that_warms_does_not_release_in_the_same_tick(monkeypatch: pytest.MonkeyPatch) -> None:
    """Warming and unloading never share a tick.

    The price of the other order is exact: the tick has just paid for the load
    pair, 118 MB of weights and the run that binds them, and the very next two
    lines of the same pass would throw it away again. The ``continue`` is the
    whole guard, so it gets a case of its own.
    """
    spy = _EngineSpy(warm_is_wanted=True, releases=True).install(monkeypatch)
    poller = _FakePoller(journal=spy.order)
    monkeypatch.setattr("findling.main._POLLER", poller)
    _ticks(monkeypatch, 1)

    await _run_the_task()

    assert spy.warm_runs == 1
    assert spy.ttls == []
    assert poller.cutter_releases == 0
    assert spy.order == ["warm_wanted", "warm"]


async def test_a_tick_with_a_busy_poller_releases_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    spy = _EngineSpy(releases=True).install(monkeypatch)
    poller = _FakePoller(busy=True, journal=spy.order)
    monkeypatch.setattr("findling.main._POLLER", poller)
    _ticks(monkeypatch, 1)

    await _run_the_task()

    assert spy.ttls == []
    assert poller.cutter_releases == 0


async def test_a_tick_with_an_idle_poller_releases_both_holders(monkeypatch: pytest.MonkeyPatch) -> None:
    spy = _EngineSpy(releases=True).install(monkeypatch)
    poller = _FakePoller(busy=False, armed=True, journal=spy.order)
    monkeypatch.setattr("findling.main._POLLER", poller)
    _ticks(monkeypatch, 1)

    await _run_the_task()

    assert len(spy.ttls) == 1
    assert poller.cutter_releases == 1
    assert spy.order == ["warm_wanted", "release_if_idle", "release_cutter"]


async def test_a_tick_with_a_silenced_poller_releases_anyway(monkeypatch: pytest.MonkeyPatch) -> None:
    """A silenced poller is the container this whole phase is built for.

    ``silence()`` leaves ``run()`` waiting on ``self._armed`` and ``run_once``
    is never entered again (``poller.py:543-545``). That is why the idle branch
    of the poller was ruled out as the place for this tick: the container that
    does not index and is searched now and then would never reach it, and it is
    exactly the container holding 118 MB it has no use for.
    """
    spy = _EngineSpy(releases=True).install(monkeypatch)
    poller = _FakePoller(busy=False, armed=False, journal=spy.order)
    monkeypatch.setattr("findling.main._POLLER", poller)
    _ticks(monkeypatch, 1)

    await _run_the_task()

    assert poller.armed is False
    assert len(spy.ttls) == 1
    assert poller.cutter_releases == 1


async def test_a_tick_without_a_poller_releases_anyway(monkeypatch: pytest.MonkeyPatch) -> None:
    # No poller means no pass can be running, so the second condition is met by
    # the absence itself.
    spy = _EngineSpy(releases=True).install(monkeypatch)
    monkeypatch.setattr("findling.main._POLLER", None)
    _ticks(monkeypatch, 1)

    await _run_the_task()

    assert len(spy.ttls) == 1


async def test_a_failing_tick_does_not_end_the_task(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    spy = _EngineSpy(releases=True).install(monkeypatch)
    spy.fail_once_with = RuntimeError("the holder could not be read")
    monkeypatch.setattr("findling.main._POLLER", None)
    _ticks(monkeypatch, 2)
    caplog.set_level(logging.ERROR, logger="findling")

    await _run_the_task()

    assert len(spy.ttls) == 2
    failures = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]
    assert len(failures) == 1
    assert "RuntimeError" in failures[0]


async def test_the_stop_event_ends_the_task_within_one_tick(monkeypatch: pytest.MonkeyPatch) -> None:
    spy = _EngineSpy(releases=True).install(monkeypatch)
    monkeypatch.setattr("findling.main._POLLER", None)
    _ticks(monkeypatch, 0)

    await _run_the_task()

    assert spy.order == []


# ---------------------------------------------------------------------------
# The order of the two releases, and the two gates that read the source instead
# of a run: a behaviour case says what happened once, the tree says what happens
# the next time somebody edits the tick.
# ---------------------------------------------------------------------------


async def test_the_cutter_is_let_go_only_behind_a_release_that_happened(monkeypatch: pytest.MonkeyPatch) -> None:
    # release_if_idle carries the clock and the identity check, release_cutter
    # carries no span of its own. A cutter release in front of, or without, a
    # real release would throw the pair away after every quiet stretch.
    spy = _EngineSpy(releases=False).install(monkeypatch)
    poller = _FakePoller(busy=False, journal=spy.order)
    monkeypatch.setattr("findling.main._POLLER", poller)
    _ticks(monkeypatch, 1)

    await _run_the_task()

    assert len(spy.ttls) == 1
    assert poller.cutter_releases == 0
    assert spy.order == ["warm_wanted", "release_if_idle"]


async def test_the_tick_reads_the_span_from_the_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    spy = _EngineSpy().install(monkeypatch)
    monkeypatch.setattr("findling.main._POLLER", None)
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", "120")
    settings.cache_clear()
    _ticks(monkeypatch, 1)

    try:
        await _run_the_task()
    finally:
        settings.cache_clear()

    assert spy.ttls == [120]


def test_every_blocking_call_of_the_tick_runs_in_a_worker_thread() -> None:
    tick = _the_tick_as_a_tree()
    calls = [node for node in ast.walk(tick) if isinstance(node, ast.Call)]

    assert [call for call in calls if _name_behind(call.func) in BLOCKING_CALLS] == []
    handed_over = [call for call in calls if _name_behind(call.func) == "to_thread"]
    assert len(handed_over) == 3
    assert {_name_behind(call.args[0]) for call in handed_over} == BLOCKING_CALLS


def test_the_cancelled_error_is_caught_ahead_of_the_general_failure() -> None:
    tick = _the_tick_as_a_tree()
    handlers = [handler for node in ast.walk(tick) if isinstance(node, ast.Try) for handler in node.handlers]

    assert [_name_behind(handler.type) for handler in handlers if handler.type is not None] == [
        "CancelledError",
        "Exception",
    ]
    assert isinstance(handlers[0].body[0], ast.Raise)


async def test_a_cancelled_tick_is_not_logged_as_an_unexpected_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def cancelled() -> bool:
        raise asyncio.CancelledError

    _EngineSpy().install(monkeypatch)
    monkeypatch.setattr("findling.main.warm_wanted", cancelled)
    monkeypatch.setattr("findling.main._POLLER", None)
    _ticks(monkeypatch, 2)
    caplog.set_level(logging.ERROR, logger="findling")

    with pytest.raises(asyncio.CancelledError):
        await _release_when_idle(asyncio.Event())

    assert [record for record in caplog.records if record.levelno >= logging.ERROR] == []


@pytest.mark.usefixtures("volume")
def test_the_release_task_ends_with_the_lifespan(monkeypatch: pytest.MonkeyPatch) -> None:
    # The third task ends the way its two siblings do: the stop event is set in
    # the finally, and the shutdown waits for it before it gives up on it.
    fake = _FakeReleaseTask()
    monkeypatch.setattr("findling.main._release_when_idle", fake.run)
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", "60")
    settings.cache_clear()

    with TestClient(APP):
        pass

    assert fake.starts == 1
    assert fake.stops == 1


@pytest.mark.usefixtures("volume")
def test_the_container_answers_the_heartbeat_with_the_real_task_running(monkeypatch: pytest.MonkeyPatch) -> None:
    """Step 3 of the verification of the plan, without a container.

    Nothing is patched here, so the task under test is the real one with its
    real tick: the switch is on, the lifespan creates it, and the server has to
    keep answering while it runs. A blocked loop would show up here and nowhere
    else in this file, because every other case drives the tick by hand.

    The shutdown costs nothing either, although the tick is 30 s: the pause
    returns the moment the stop event arrives, which is the one property the
    private import of ``_pause`` exists for.
    """
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", "60")
    settings.cache_clear()

    with TestClient(APP) as client:
        answer = client.get("/heartbeat")

    assert answer.status_code == 200
    assert answer.json() == {"status": "ok"}
