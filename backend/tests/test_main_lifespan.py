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
import gc
import inspect
import logging
import time
from functools import partial
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import Corpus
from findling.api import resources
from findling.config import settings
from findling.index.open import LANGUAGES_MARK, open_index
from findling.index.rebuild import POLLER_STILL_WRITING, REBUILD_THROUGH
from findling.index.wordlist import build_artifact
from findling.index.writer import IndexBatchWriter, IndexLockedError
from findling.main import (
    APP,
    REBUILD_STOP_SECONDS,
    RELEASE_TICK_SECONDS,
    _arm_the_poller,
    _rebuild_the_index_directory,
    _release_when_idle,
    _run_the_rebuild,
    _stand_the_poller_down,
)
from findling.store.repo import Store, open_store
from findling.worker.poller import Poller, default_poller


def _a_writer_on_the_live_directory() -> IndexBatchWriter:
    """The writer the poller builds, built the same way and on the same path."""
    resolved = settings()
    return IndexBatchWriter(
        open_index(resolved.index_dir, build_artifact().entries),
        directory=resolved.index_dir,
    )


def _documents_in_the_live_directory() -> int:
    """How many documents the live index directory holds right now."""
    index = open_index(settings().index_dir, build_artifact().entries)
    index.reload()
    return index.searcher().num_docs


def _make_the_marks_ask_for_a_rebuild() -> None:
    """Write the one drifted mark a directory rebuild answers, and nothing else.

    The language mark and not the schema mark, for the reason the fixture of the
    rebuild suite states: a stored schema generation of 1 is the legitimate
    state of every installation coming from 1.2.0, and the store stopped calling
    it a drift for exactly that reason.
    """
    store = open_store(settings().state_db)
    try:
        store.write_meta(LANGUAGES_MARK, "de,en,es")
    finally:
        store.close()


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


# ---------------------------------------------------------------------------
# The fourth long lived task: the rebuild of the index directory. Same shape as
# the third one above, same questions asked of it: does it exist only when it
# should, does it end with the lifespan, and does the blocking work reach a
# worker thread. Two questions come on top, and both of them are about wiring
# rather than about behaviour: the clean up path has to run before anything else
# opens the volume, and the callbacks the run is led by have to be the methods of
# the real poller rather than something that merely looks like them.
# ---------------------------------------------------------------------------

MAIN_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "main.py"


class _FakeIndexingTask:
    """A poller or a reconcile, as far as the lifespan is concerned."""

    def __init__(self) -> None:
        self.armed = False
        self.closed = False

    def arm(self) -> None:
        self.armed = True

    def silence(self) -> None:
        self.armed = False

    async def run(self, stop_event: asyncio.Event) -> None:
        await stop_event.wait()

    async def unlock_held(self) -> int:
        return 0

    async def aclose(self) -> None:
        self.closed = True


class _FakeRebuildTask:
    """A stand in for the fourth task, which records the task object it runs as.

    ``current_task`` is how the shutdown case gets at the very object the
    lifespan created: the task is a local of the context manager, and asserting
    that it is done afterwards is the whole claim of that case.
    """

    def __init__(self) -> None:
        self.starts = 0
        self.stops = 0
        self.task: asyncio.Task[None] | None = None

    async def run(self, stop_event: asyncio.Event) -> None:
        self.starts += 1
        self.task = asyncio.current_task()
        await stop_event.wait()
        self.stops += 1


def _install_the_three_tasks(monkeypatch: pytest.MonkeyPatch, rebuild: _FakeRebuildTask) -> _FakeIndexingTask:
    """Keep the real poller and reconcile out, and put the recording rebuild in.

    The real poller would open the index and the state database the moment it is
    armed, and every case below arms it: the mark on the volume is what lets the
    fourth task start at all.
    """
    poller = _FakeIndexingTask()
    monkeypatch.setattr("findling.main.default_poller", lambda: poller)
    monkeypatch.setattr("findling.main.default_reconcile", lambda: _FakeIndexingTask())
    monkeypatch.setattr("findling.main._rebuild_the_index_directory", rebuild.run)
    return poller


def _mark_the_index_as_built_for_another_language_set(volume: Path) -> None:
    """Store a language set the container does not run, which is the drift a rebuild answers.

    It used to move the schema mark back instead, and that stopped being a drift
    on 2026-09-24: a stored schema generation of 1 against the expected 2 is the
    state every installation upgrading from 1.2.0 is in, and calling it a drift
    sent the whole field into a reindex nobody ordered
    (:func:`findling.store.repo._schema_is_legacy`, deploy-harp run
    35989391950). The language mark is the drift this phase is about, and the
    stored value here names a language the container has switched off, which is
    case four of plan 18-05.
    """
    store = open_store(volume / "state.db")
    store.write_meta(LANGUAGES_MARK, "de,en,es")
    store.close()


def test_the_rebuild_task_is_not_created_when_the_marks_agree(
    indexed_volume: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ordinary start, which is every start of every installation that is current.

    A rebuild costs the size of the index a second time and a pass over every
    document in it, so the evidence has to be there before the task exists at
    all. A task that started and then found nothing to do would open the state
    database on every single start for an answer this question already has.
    """
    del indexed_volume
    fake = _FakeRebuildTask()
    _install_the_three_tasks(monkeypatch, fake)
    settings().armed_marker.write_text("", encoding="utf-8")

    with TestClient(APP):
        pass

    assert fake.starts == 0


def test_the_rebuild_task_is_created_when_the_marks_ask_for_it(
    indexed_volume: object, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other half: a stored language set that is not the one this container runs."""
    del indexed_volume
    fake = _FakeRebuildTask()
    _install_the_three_tasks(monkeypatch, fake)
    _mark_the_index_as_built_for_another_language_set(volume)
    settings().armed_marker.write_text("", encoding="utf-8")

    with TestClient(APP):
        pass

    assert fake.starts == 1


def test_the_rebuild_task_stays_away_from_a_container_that_was_never_enabled(
    indexed_volume: object, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deployed and not switched on: no lock, no volume, and least of all a rebuild.

    The drift is there and it stays unanswered, which is right. Nothing reads out
    of this container yet, so nothing is degraded by the old directory, and the
    largest write this app can make is the last one to happen without an enable.
    """
    del indexed_volume
    fake = _FakeRebuildTask()
    _install_the_three_tasks(monkeypatch, fake)
    _mark_the_index_as_built_for_another_language_set(volume)

    with TestClient(APP):
        pass

    assert fake.starts == 0


def test_the_rebuild_task_ends_with_the_lifespan_and_inside_its_budget(
    indexed_volume: object, volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fourth task dies the way the three beside it do, and it dies in time.

    The budget is asserted against the clock and not only against ``done()``,
    because the failure this guards is a shutdown that hangs: an orchestrator
    that waits for a rebuild of hours kills the container, and then the three
    other tasks lose their ordered shutdown as well (T-18-09-03).
    """
    del indexed_volume
    fake = _FakeRebuildTask()
    _install_the_three_tasks(monkeypatch, fake)
    _mark_the_index_as_built_for_another_language_set(volume)
    settings().armed_marker.write_text("", encoding="utf-8")

    started = time.monotonic()
    with TestClient(APP):
        pass
    took = time.monotonic() - started

    assert fake.starts == 1
    assert fake.stops == 1
    assert fake.task is not None
    assert fake.task.done() is True
    assert took < REBUILD_STOP_SECONDS


def test_the_clean_up_path_runs_before_the_indexing_task_is_created(
    indexed_volume: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Order, and it is the whole content of this case.

    A poller armed onto a volume that a hard abort left halfway through a
    directory swap does not find the fault, it adds to it: it opens whatever
    directory is there, writes into it and commits. So the five states of the
    volume are read and decided before the first task exists.
    """
    del indexed_volume
    journal: list[str] = []
    fake = _FakeRebuildTask()
    monkeypatch.setattr("findling.main._rebuild_the_index_directory", fake.run)
    monkeypatch.setattr("findling.main.default_reconcile", lambda: _FakeIndexingTask())

    def note_the_clean_up() -> str:
        journal.append("clean up")
        return "nothing"

    def note_the_poller() -> _FakeIndexingTask:
        journal.append("poller")
        return _FakeIndexingTask()

    monkeypatch.setattr("findling.main.recover_the_index_directories", note_the_clean_up)
    monkeypatch.setattr("findling.main.default_poller", note_the_poller)

    with TestClient(APP):
        pass

    assert journal == ["clean up", "poller"]


async def test_the_rebuild_hands_the_real_stand_down_and_arm_of_the_poller_into_the_run(
    indexed_volume: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The wiring, asked of the real poller and not of a stand in.

    The run of plan 18-09 takes its callbacks from whoever leads it, and a pair
    that went nowhere would look exactly like a pair that works: the rebuild
    would carry every document over, the counts would match, the swap would
    succeed, and the only difference would be the documents the poller wrote into
    the source directory in the meantime, which are gone after the swap and which
    nothing counts (T-18-09-01). No case inside the rebuild suite can see that,
    because every one of them hands its own recorders in. So this one builds the
    real poller, drives the real entry point of ``main`` and reads the armed flag
    of that object: only ``Poller.stand_down`` clears it here and only
    ``Poller.arm`` sets it, so the two readings are the proof that the two
    methods were reached.

    The run goes through a worker thread because that is where it really runs,
    and because the stand down submits a coroutine back to this loop: a case
    that called it on the loop would wait for a future the loop cannot get to
    (audit finding C-18-01).
    """
    del indexed_volume
    poller = default_poller()
    # Said out loud, because the whole worth of this case is the object: a stand
    # in here would prove that two recorders can be called, which is what the
    # rebuild suite already proves.
    assert isinstance(poller, Poller)
    monkeypatch.setattr("findling.main._POLLER", poller)
    settings().armed_marker.write_text("", encoding="utf-8")
    poller.arm()
    readings: list[tuple[str, bool]] = []
    handed_over: dict[str, object] = {}

    def probe(
        store: Store,
        *,
        stand_down: object,
        arm: object,
        drop_read_side: object,
        should_stop: object,
    ) -> str:
        del store, should_stop
        handed_over["stand_down"] = stand_down
        handed_over["arm"] = arm
        handed_over["drop_read_side"] = drop_read_side
        readings.append(("before", poller.armed))
        assert stand_down() is True  # pyright: ignore[reportCallIssue]
        readings.append(("stood down", poller.armed))
        arm()  # pyright: ignore[reportCallIssue]
        readings.append(("armed again", poller.armed))
        return REBUILD_THROUGH

    monkeypatch.setattr("findling.main.rebuild_the_index", probe)

    loop = asyncio.get_running_loop()
    verdict = await asyncio.to_thread(_run_the_rebuild, lambda: False, loop)

    assert verdict == REBUILD_THROUGH
    assert readings == [("before", True), ("stood down", False), ("armed again", True)]
    # And the callables really are the ones main defines, so that a later edit
    # cannot quietly hand in something that swallows the call. The stand down
    # arrives bound to this loop, so it is the partial rather than the function.
    bound = handed_over["stand_down"]
    assert isinstance(bound, partial)
    assert bound.func is _stand_the_poller_down
    assert bound.args == (loop,)
    assert handed_over["arm"] is _arm_the_poller
    assert handed_over["drop_read_side"] is resources.reset_read_side


async def test_a_real_poller_with_an_open_writer_loses_no_document_over_the_swap(
    indexed_volume: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The timeline of C-18-01, played with a real poller and a real IndexWriter.

    **What was wrong.** The module header of ``index/rebuild.py`` promised that
    the writer of the poller is closed by the time the swap renames the live
    directory. It was not: ``silence()`` cleared a flag, the writer was built
    once per poller and handed back only in ``aclose()``, and the lifespan armed
    the poller twenty two lines before it created the rebuild task. So
    ``shutil.rmtree`` removed a directory a live writer was holding, and every
    document the poller indexed afterwards went into inodes with no name. The
    whole rebuild suite missed it, because every case there hands its own
    recorders in and no recorder holds a tantivy lock.

    **Why this case can see it and the others cannot.** It builds the writer the
    production path builds, on the live directory, and proves it is really open
    before the run by asking for a second one: tantivy answers a held directory
    with :class:`findling.index.writer.IndexLockedError` and answers a free one
    with a writer. The same question after the run is what says the handle came
    back.

    **The two shapes of the failure, and this case catches both.** On Windows
    the first rename refuses with a ``PermissionError`` while the lock is held,
    so the verdict would not be ``REBUILD_THROUGH``. On Linux it succeeds and
    says nothing, so the count of the documents in the live directory afterwards
    is what carries the claim there.
    """
    poller = Poller(store=open_store(settings().state_db), writer=_a_writer_on_the_live_directory())
    # Nothing in this frame may hold the directory, or the rename would refuse
    # for the wrong reason. The writer above is reachable through the poller and
    # through nothing else, which is exactly the production shape.
    gc.collect()
    monkeypatch.setattr("findling.main._POLLER", poller)
    settings().armed_marker.write_text("", encoding="utf-8")
    poller.arm()
    _make_the_marks_ask_for_a_rebuild()
    before = _documents_in_the_live_directory()
    assert before == indexed_volume.documents
    with pytest.raises(IndexLockedError):
        _a_writer_on_the_live_directory()

    verdict = await asyncio.to_thread(_run_the_rebuild, lambda: False, asyncio.get_running_loop())

    assert verdict == REBUILD_THROUGH
    assert _documents_in_the_live_directory() == before, "the swap carried every document over"
    assert not (settings().index_dir.with_name("index.retired")).exists(), "the removal behind the swap ran"
    assert not (settings().index_dir.with_name("index.rebuild")).exists()
    # The handle really came back, so the directory the rmtree removed was held
    # by nobody, and the poller opens a fresh writer on the new directory at its
    # next pass.
    assert poller._writer is None
    _a_writer_on_the_live_directory()
    assert poller.armed is True, "and the indexing task was let go again"


async def test_the_run_stops_before_it_touches_anything_when_the_poller_will_not_stand_down(
    indexed_volume: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other half of C-18-01: a stand down that fails may not become a swap.

    A pass that outlasts the budget leaves the writer open on the live
    directory, which is the state the whole finding is about. The only safe
    answer is to do nothing at all this start: no third directory on the volume,
    no rename, no stamp, and the indexing task armed again so that the container
    goes on doing the work it can do.
    """
    del indexed_volume
    poller = default_poller()
    monkeypatch.setattr("findling.main._POLLER", poller)
    settings().armed_marker.write_text("", encoding="utf-8")
    poller.arm()
    _make_the_marks_ask_for_a_rebuild()
    # A pass that never ends, which is what the budget is measured against.
    poller._in_flight = True
    # A budget below the tick of the wait, so this case spends no wall clock at
    # all on a pass that is never going to end.
    monkeypatch.setattr("findling.main.STAND_DOWN_SECONDS", 0.0)

    verdict = await asyncio.to_thread(_run_the_rebuild, lambda: False, asyncio.get_running_loop())

    assert verdict == POLLER_STILL_WRITING
    assert not (settings().index_dir.with_name("index.rebuild")).exists(), "nothing was created"
    assert not (settings().index_dir.with_name("index.retired")).exists(), "and nothing was renamed"
    assert poller.armed is True, "and the indexing task was let go again"


async def test_the_poller_is_not_armed_again_when_the_app_was_switched_off_meanwhile(
    indexed_volume: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rebuild runs for hours, and an admin may switch the app off inside them.

    The mark on the volume is what the disable removes, so it is what the arming
    asks. Without this the container would come out of a rebuild indexing while
    Nextcloud has the app switched off, which is the failure the mark exists for
    with the two sides swapped.
    """
    del indexed_volume
    poller = default_poller()
    monkeypatch.setattr("findling.main._POLLER", poller)
    poller.arm()

    assert await asyncio.to_thread(_stand_the_poller_down, asyncio.get_running_loop()) is True
    assert poller.armed is False

    # No mark on the volume: this container is disabled as far as Nextcloud is
    # concerned, whatever it was doing when the rebuild started.
    _arm_the_poller()

    assert poller.armed is False


def test_the_blocking_rebuild_never_runs_on_the_event_loop() -> None:
    """Static, because the symptom is a container that looks healthy and is not.

    The run opens two index directories, writes the whole index a second time and
    renames directories, for minutes to hours. On the loop that is a container
    that stops answering ``/heartbeat`` while its own log says nothing at all,
    and AppAPI takes it for dead long before the pass is through (T-14-23, and
    the house rule at the head of ``worker/poller.py``).
    """
    parsed = ast.parse(inspect.getsource(_rebuild_the_index_directory)).body[0]
    assert isinstance(parsed, ast.AsyncFunctionDef)
    calls = [node for node in ast.walk(parsed) if isinstance(node, ast.Call)]

    assert [call for call in calls if _name_behind(call.func) == "_run_the_rebuild"] == []
    handed_over = [call for call in calls if _name_behind(call.func) == "to_thread"]
    assert [_name_behind(call.args[0]) for call in handed_over] == ["_run_the_rebuild"]

    handlers = [handler for node in ast.walk(parsed) if isinstance(node, ast.Try) for handler in node.handlers]
    assert [_name_behind(handler.type) for handler in handlers if handler.type is not None] == [
        "CancelledError",
        "Exception",
    ]
    assert isinstance(handlers[0].body[0], ast.Raise)


def test_the_stop_budget_of_the_rebuild_is_defined_and_used() -> None:
    """Two mentions outside the comments: the definition and the wait that spends it.

    A budget that is only defined is a number nobody honours, and a shutdown that
    waited without one would wait for a run of hours.
    """
    code = [line for line in MAIN_SOURCE.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#")]

    assert sum(line.count("REBUILD_STOP_SECONDS") for line in code) >= 2
