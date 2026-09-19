"""One embedding engine per process, and the falsification that had to come first.

**Why this file opens with a claim that is wrong.** The measurement report of
plan 06-11 split the second load of the search side into three items: the
tokenizer, the onnxruntime session, and "a second German decomposition automaton
built from the word list, 64 MB by the breakdown". The third item does not
exist. ``index/analyzer.py`` holds a process wide cache keyed on the digest of
the constituent list, it counts every real build in ``build_count()``, and
``open_index`` is the only place in the running app that registers an analyzer.
A search gets a cache hit there, not a second automaton.

The falsification belongs in front of the change and not in a document. This
plan takes the second engine out of the process and the memory number will fall.
With the automaton still on the list of causes nobody could split that saving
into its parts afterwards, and a plan whose numbers cannot be accounted for has
to be believed rather than checked (06.1-RESEARCH.md, pitfall 1).

**What the search side really does a second time** is read the word list.
``build_artifact`` has no cache, and the log line "constituent list read from the
volume" of 05:15Z is the evidence the report read as an automaton. That is a
different item, it costs about 21.9 MB, and it belongs to plan 06.1-04. It is
deliberately not touched here, because one change that fixes two items reports
one number for both.

**What the second half of this file is about.** The holder in
``embed/engine.py``: two callers, one object, one load. The measured item is a
counter and an object identity, never a byte. A peak difference is not the sum
of the loads that produced it, and a test that counts resident memory on a
shared runner is a random number generator with an assertion attached.
"""

from __future__ import annotations

import ast
import concurrent.futures
import contextlib
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy
import pytest

from conftest import CONSTITUENTS, Corpus
from findling.api import resources
from findling.config import settings
from findling.embed import engine as engine_module
from findling.embed import model as model_module
from findling.embed.engine import (
    ENGINE_COLD,
    ENGINE_DISABLED,
    ENGINE_LOADED,
    ENGINE_MISSING,
    ENGINE_RETRY_PENDING,
    ENGINE_STATES,
    WARM_TEXT,
    engine_state,
    note_cutter_failure,
    query_may_load,
    release_if_idle,
    released_count,
    request_warm,
    reset,
    shared_model,
    warm,
    warm_wanted,
)
from findling.embed.model import (
    DIMENSIONS,
    LOAD_RETRY_SECONDS,
    MODEL_FILE,
    TOKENIZER_FILE,
    EmbeddingModel,
    load_count,
    unload_count,
)
from findling.index.analyzer import build_count, cached_german_analyzer
from findling.worker import poller as poller_module

if TYPE_CHECKING:
    from collections.abc import Iterator

# Digests of this file only, and three of them for two cases. The cache keeps
# exactly one entry, so a case that reused the digest of the case before it
# would take a cache hit where it expects a build, and the result would depend
# on the order the suite happens to run in.
DIGEST_ONE = "06.1-02-falsification-one"
DIGEST_TWO = "06.1-02-falsification-two"
DIGEST_THREE = "06.1-02-falsification-three"

# How long the second thread of the concurrency case is given to arrive inside
# the load path. It is a barrier timeout and not a sleep on suspicion: when the
# load path is serialised the second thread can never get there, so the wait
# runs out and the case is green in one second; when it is not serialised both
# threads meet at once, the barrier releases immediately and the case is red
# without waiting for anything.
RACE_WINDOW_SECONDS = 1.0


# ---------------------------------------------------------------------------
# The falsification
# ---------------------------------------------------------------------------


def test_a_search_side_open_does_not_build_the_automaton_again(indexed_volume: Corpus) -> None:
    # The fixture wrote the index the way the indexing side does, so the
    # automaton for this word list is already built when the counter is read.
    # What follows is the search side opening the same volume, which is the
    # exact moment the 06-11 report placed the second build at.
    before = build_count()

    side = resources.read_side()

    assert side is not None, "the fixture volume carries an index and a state database"
    assert build_count() == before, "the search side takes a cache hit, it does not build a second automaton"


def test_the_same_word_list_is_a_cache_hit_and_not_a_second_automaton() -> None:
    before = build_count()

    first = cached_german_analyzer(DIGEST_ONE, CONSTITUENTS)
    second = cached_german_analyzer(DIGEST_ONE, CONSTITUENTS)

    assert first is second
    assert build_count() - before == 1


def test_a_different_word_list_does_build_a_second_automaton() -> None:
    # The counterpart, and the reason the two cases above mean anything: this
    # one has to go up. Without it the file would be green against a counter
    # that never moves, which proves a frozen number and not a working cache.
    before = build_count()

    cached_german_analyzer(DIGEST_TWO, CONSTITUENTS)
    cached_german_analyzer(DIGEST_THREE, CONSTITUENTS)

    assert build_count() - before == 2


# ---------------------------------------------------------------------------
# The stand in. Two objects that look like a tokenizer and a session from the
# inside of _run_batch and read nothing from disk, in the shape test_embed_model
# established: only the two functions that touch the artifacts are replaced, so
# everything above them is the real code path.
# ---------------------------------------------------------------------------


@dataclass
class _FakeEncoding:
    ids: list[int]
    attention_mask: list[int]


class _FakeEncoder:
    """One token per text, which is everything the pooling below needs."""

    def encode_batch(self, texts: list[str]) -> list[_FakeEncoding]:
        return [_FakeEncoding(ids=[1], attention_mask=[1]) for _ in texts]


@dataclass
class _FakeInput:
    name: str


class _FakeSession:
    """A graph that answers a constant hidden state of the declared width."""

    def get_inputs(self) -> list[_FakeInput]:
        return [_FakeInput("input_ids"), _FakeInput("attention_mask")]

    def get_outputs(self) -> list[_FakeInput]:
        return [_FakeInput("last_hidden_state")]

    def run(self, _outputs: list[str], feed: dict[str, Any]) -> list[Any]:
        ids = feed["input_ids"]
        return [numpy.ones((ids.shape[0], ids.shape[1], DIMENSIONS), dtype=numpy.float32)]


@pytest.fixture
def model_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A model directory the settings point at, empty until a case fills it.

    The settings cache is cleared on both sides, the way the volume fixture of
    conftest does it: they are resolved once per process by design, and a case
    that changed the environment without clearing would hand its paths to the
    next one.
    """
    home = tmp_path / "model"
    home.mkdir(parents=True)
    monkeypatch.setenv("FINDLING_EMBED_MODEL_DIR", str(home))
    settings.cache_clear()
    yield home
    settings.cache_clear()


def _pretend_a_model(home: Path) -> None:
    """Put the two file names in place that the load path looks for."""
    (home / "model.onnx").write_bytes(b"not a real graph")
    (home / "tokenizer.json").write_text("{}", encoding="utf-8")


def _stand_in(monkeypatch: pytest.MonkeyPatch) -> None:
    def open_encoder(_directory: Path, *, sequence_len: int) -> _FakeEncoder:
        assert sequence_len >= 1
        return _FakeEncoder()

    def open_session(_path: Path, *, threads: int) -> _FakeSession:
        assert threads >= 1
        return _FakeSession()

    monkeypatch.setattr(model_module, "_open_encoder", open_encoder)
    monkeypatch.setattr(model_module, "_open_session", open_session)


# ---------------------------------------------------------------------------
# The holder
# ---------------------------------------------------------------------------


def test_the_search_and_the_track_get_the_same_engine(model_home: Path) -> None:
    # The whole point of the plan in one line. Two callers in one process, one
    # object, so the tokenizer and the session are read once and not twice
    # (06-11: +276 MB that stayed resident, against 210 MB of headroom).
    assert model_home.is_dir()

    first = shared_model()
    second = shared_model()

    assert first is second


def test_another_model_directory_gets_another_engine(
    model_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = shared_model()
    first.embed_passages(["ein Text"])

    # Keyed on the directory for the reason the read side caches are keyed on
    # their path: one container has one model directory, but a suite has one per
    # test, and the remembered refusal of the previous directory would be handed
    # to a test that has a model.
    other = tmp_path / "another-model"
    other.mkdir(parents=True)
    monkeypatch.setenv("FINDLING_EMBED_MODEL_DIR", str(other))
    settings.cache_clear()

    second = shared_model()

    assert second is not first
    assert second.loaded is False


def test_two_threads_get_one_engine_and_pay_for_one_load(model_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)

    # The barrier is the proof, not a sleep on suspicion. Two threads can only
    # meet in here when nothing serialises the load path, so an unserialised one
    # releases the barrier at once and builds twice, and a serialised one lets a
    # single thread in, runs the wait out and builds once.
    barrier = threading.Barrier(2)
    real_open_session = model_module._open_session

    def gated_open_session(path: Path, *, threads: int) -> Any:
        with contextlib.suppress(threading.BrokenBarrierError):
            barrier.wait(timeout=RACE_WINDOW_SECONDS)
        return real_open_session(path, threads=threads)

    monkeypatch.setattr(model_module, "_open_session", gated_open_session)

    seen: list[EmbeddingModel] = []
    guard = threading.Lock()
    gate = threading.Event()

    def ask() -> None:
        gate.wait(30)
        engine = shared_model()
        engine.embed_passages(["ein Text"])
        with guard:
            seen.append(engine)

    before = load_count()
    workers = [threading.Thread(target=ask) for _ in range(2)]
    for worker in workers:
        worker.start()
    gate.set()
    for worker in workers:
        worker.join(60)

    assert len(seen) == 2, "both threads have to have answered"
    assert seen[0] is seen[1], "two threads, one engine"
    assert load_count() - before == 1, "a second session would be the doubled load this plan removes"


def test_the_second_track_and_the_read_side_wire_the_same_object(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The two real callers, not two calls of the holder. The read side asks
    # through resources.query_model and the worker wires its track in
    # _wire_the_second_track and _build_the_cutter, and the whole plan is that
    # those two lines end at one object. Everything the wiring touches besides
    # the engine is replaced, because the vector stock and the 17 MB tokenizer
    # have nothing to do with the question.
    #
    # Both halves are driven since plan 07-03 split them: the first one opens
    # the stock and promises the rest, the second one builds the cutter and asks
    # the holder for the engine, at the first row that needs it.
    _pretend_a_model(model_home)

    class _Stock:
        def close(self) -> None:
            """Nothing was opened, so nothing has to be released."""

    monkeypatch.setattr(poller_module, "open_vectors", lambda _path: _Stock())
    monkeypatch.setattr(poller_module, "open_tokenizer", lambda _directory: object())
    monkeypatch.setattr(poller_module, "make_splitter", lambda *_args, **_kwargs: object())

    worker = poller_module.Poller()
    worker._wire_the_second_track()
    worker._build_the_cutter()

    assert worker._model is not None, "the track has to have been wired"
    assert worker._model is resources.query_model()


# ---------------------------------------------------------------------------
# The two halves the audit of plan 06.1-17 found open: the load path and the
# reach of the lock. Both belong to the shared engine, both were left over from
# a distinction that plan 06.1-02 made for the run path only.
# ---------------------------------------------------------------------------


def _gated_stand_in(monkeypatch: pytest.MonkeyPatch, session: Any) -> None:
    """The stand in of this file, with a session the case brought along."""

    def open_encoder(_directory: Path, *, sequence_len: int) -> _FakeEncoder:
        assert sequence_len >= 1
        return _FakeEncoder()

    def open_session(_path: Path, *, threads: int) -> Any:
        assert threads >= 1
        return session

    monkeypatch.setattr(model_module, "_open_encoder", open_encoder)
    monkeypatch.setattr(model_module, "_open_session", open_session)


def _flaky_session(monkeypatch: pytest.MonkeyPatch, attempts: dict[str, int]) -> None:
    """A session that throws on the first open and answers on every later one.

    MemoryError and not a made up exception: the container runs under a hard 2 GB
    limit, the open pulls 118 MB of weights, and the load run of 2026-09-05
    measured memory.events max at 2796. This is the failure that really happens.
    """
    _stand_in(monkeypatch)
    real_open_session = model_module._open_session

    def flaky(path: Path, *, threads: int) -> Any:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise MemoryError("the box was full for a moment")
        return real_open_session(path, threads=threads)

    monkeypatch.setattr(model_module, "_open_session", flaky)


def test_a_load_that_threw_is_tried_again_after_the_cooldown(model_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The coupling trap of the phase research, seen from the load path. With one
    # engine for both halves a single transient failure used to cost the whole
    # container its semantics until somebody restarted it, and nothing said so.
    _pretend_a_model(model_home)
    attempts = {"count": 0}
    _flaky_session(monkeypatch, attempts)
    clock = {"now": 1000.0}
    monkeypatch.setattr(model_module.time, "monotonic", lambda: clock["now"])

    engine = EmbeddingModel(model_home, batch_size=2, sequence_len=512)

    assert engine.embed_query("bauantrag").available is False, "the throw has to be honest while it is fresh"

    clock["now"] += LOAD_RETRY_SECONDS + 1

    assert engine.embed_query("bauantrag").available is True, "a moment is not a property of the installation"
    assert attempts["count"] == 2, "exactly one retry, and only after the cooldown"


def test_a_load_that_threw_is_not_tried_again_within_the_cooldown(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The other half, and the reason a plain retry would be worse than the bug:
    # the second track walks tens of thousands of documents, so an open per row
    # would read a broken graph tens of thousands of times.
    _pretend_a_model(model_home)
    attempts = {"count": 0}
    _flaky_session(monkeypatch, attempts)
    clock = {"now": 1000.0}
    monkeypatch.setattr(model_module.time, "monotonic", lambda: clock["now"])

    engine = EmbeddingModel(model_home, batch_size=2, sequence_len=512)
    for _ in range(5):
        clock["now"] += LOAD_RETRY_SECONDS / 10
        assert engine.embed_passages(["ein Text"]).available is False

    assert attempts["count"] == 1, "five rows inside one cooldown are one open and not five"


def test_a_directory_without_the_artifacts_is_never_looked_at_again(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The half that is right to remember for ever, and that the cooldown above
    # must not turn into a pair of stat calls per cooldown: a container built
    # without the model stage never grows one while it runs.
    looks = {"count": 0}
    real_present = model_module._artifacts_present

    def counted(directory: Path) -> bool:
        looks["count"] += 1
        return real_present(directory)

    monkeypatch.setattr(model_module, "_artifacts_present", counted)

    engine = EmbeddingModel(model_home, batch_size=2, sequence_len=512)
    for _ in range(5):
        assert engine.embed_passages(["ein Text"]).available is False

    assert looks["count"] == 1, "an absent model is a property of the installation and is asked once"


def test_the_graph_runs_outside_the_lock_so_a_search_does_not_wait_for_a_document(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Measured before the change (07.09.2026, 06.1-AUDIT-PERF.md M1): a search
    # waits 0.561 s behind one document at the default token cap and 2.562 s at
    # the ceiling of the range, because the lock is held over the whole call and
    # not over one batch. The graph does not need it: the onnxruntime maintainer
    # promises thread safety for Run(), the tokenizers maintainer promises
    # nothing, and the tokenizer is one line of the batch.
    _pretend_a_model(model_home)
    inside = threading.Event()
    release = threading.Event()

    class _GatedSession(_FakeSession):
        def run(self, outputs: list[str], feed: dict[str, Any]) -> list[Any]:
            inside.set()
            release.wait(RACE_WINDOW_SECONDS)
            return super().run(outputs, feed)

    _gated_stand_in(monkeypatch, _GatedSession())
    engine = EmbeddingModel(model_home, batch_size=2, sequence_len=512)

    track = threading.Thread(target=lambda: engine.embed_passages(["eins", "zwei", "drei"]))
    track.start()
    try:
        assert inside.wait(30), "the track has to have reached the graph"
        taken = engine._lock.acquire(timeout=RACE_WINDOW_SECONDS)
    finally:
        release.set()
        track.join(30)
    if taken:
        engine._lock.release()

    assert taken, "a search must not wait for a whole document of the second track"


def test_the_tokenizer_is_never_entered_twice_at_once(model_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The property the lock exists for, and the one the change above must not
    # spend: huggingface/tokenizers#1726 gives no promise for a shared
    # tokenizer, so the encoding stays serialised whatever else moves out.
    _pretend_a_model(model_home)

    class _JealousEncoder(_FakeEncoder):
        def __init__(self) -> None:
            self.busy = False
            self.overlapped = False

        def encode_batch(self, texts: list[str]) -> list[_FakeEncoding]:
            if self.busy:
                self.overlapped = True
            self.busy = True
            time.sleep(0.005)
            self.busy = False
            return super().encode_batch(texts)

    encoder = _JealousEncoder()
    monkeypatch.setattr(model_module, "_open_encoder", lambda _directory, *, sequence_len: encoder)
    monkeypatch.setattr(model_module, "_open_session", lambda _path, *, threads: _FakeSession())

    engine = EmbeddingModel(model_home, batch_size=2, sequence_len=512)
    engine.embed_query("aufwaermen")

    def ask() -> None:
        for _ in range(20):
            engine.embed_passages(["eins", "zwei", "drei", "vier"])

    askers = [threading.Thread(target=ask) for _ in range(4)]
    for asker in askers:
        asker.start()
    for asker in askers:
        asker.join(60)

    assert encoder.overlapped is False, "two threads in one tokenizer is the promise nobody made"


# ---------------------------------------------------------------------------
# The state of the engine as one word, for the admin page of plan 07-04.
#
# Five states, and the whole point of the field is that they ask different things
# of an admin: a missing model is a rebuild of the image, a load that threw is a
# wait of five minutes, and cold is the ordinary state of a container nobody has
# asked anything yet. On the page the three used to look identical, because
# "nought per cent findable by meaning" is true in every one of them.
#
# What is measured here is a word and never a byte, for the reason the holder
# above is measured with a counter: a peak difference is not the sum of the
# loads that produced it, and a byte on a shared runner is a random number.
# ---------------------------------------------------------------------------


def _held_for(directory: Path) -> EmbeddingModel | None:
    """The instance the holder carries for that directory, and never a new one.

    Reaches into the holder on purpose. The claim of one case below is that
    asking for the state leaves the holder as it found it, and there is no way
    to see that from the outside: every public way of looking would build the
    very instance whose absence is the assertion.
    """
    held = engine_module._ENGINE
    if held is not None and held[0] == directory:
        return held[1]
    return None


def test_a_container_with_the_second_half_switched_off_says_so_and_not_cold(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The order of the verdicts, held at its first step. Cold reads as "the
    # model arrives on first demand, which is the normal state", and on a
    # container whose semantic half is switched off that demand never comes.
    # The two need different words or the setting is invisible on the page.
    _pretend_a_model(model_home)
    monkeypatch.setenv("FINDLING_EMBED_ENABLED", "false")
    settings.cache_clear()

    assert engine_state() == ENGINE_DISABLED


def test_a_container_that_has_never_built_an_instance_is_cold(model_home: Path) -> None:
    # The ordinary state of a container that has just started: the artifacts are
    # in the image, nothing has asked for a vector yet, and since plan 07-03 the
    # second track does not build the engine before the first row that needs it
    # either.
    _pretend_a_model(model_home)

    assert _held_for(model_home) is None
    assert engine_state() == ENGINE_COLD


def test_an_instance_that_was_built_but_never_loaded_is_cold(model_home: Path) -> None:
    # Building the wrapper reads nothing, which is the promise shared_model
    # makes in its own docstring. An instance in the holder is therefore not a
    # loaded engine, and the page must not report one.
    _pretend_a_model(model_home)

    built = shared_model()

    assert built.loaded is False
    assert engine_state() == ENGINE_COLD


def test_a_container_that_has_embedded_something_reports_loaded(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)

    shared_model().embed_query("bauantrag")

    assert engine_state() == ENGINE_LOADED


def test_a_directory_without_the_artifacts_is_reported_as_missing(model_home: Path) -> None:
    # The state the field exists for. Nought documents with a loaded engine means
    # the track is starting up, nought documents without a model means nothing
    # is coming, and the two used to be one sentence on the page.
    #
    # Asserted twice, before and after an attempt, because the answer has two
    # sources: without an instance it is the artifact question, with one it is
    # the refusal the load path remembered for ever.
    assert engine_state() == ENGINE_MISSING

    shared_model().embed_query("bauantrag")

    assert engine_state() == ENGINE_MISSING


def test_a_load_that_threw_is_reported_as_waiting_until_the_cooldown_is_over(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The third answer of the load path, and the only one an admin can do
    # nothing about except wait. Saying "missing" here would send somebody
    # rebuilding an image that is perfectly whole.
    _pretend_a_model(model_home)
    attempts = {"count": 0}
    _flaky_session(monkeypatch, attempts)
    clock = {"now": 1000.0}
    monkeypatch.setattr(model_module.time, "monotonic", lambda: clock["now"])

    engine = shared_model()

    assert engine.embed_query("bauantrag").available is False
    assert engine_state() == ENGINE_RETRY_PENDING

    clock["now"] += LOAD_RETRY_SECONDS + 1

    # The cooldown is over and nothing has retried yet, which is cold and not
    # loaded: the next row or the next search is what pays for the load.
    assert engine_state() == ENGINE_COLD
    assert attempts["count"] == 1, "asking for the state is not an attempt"


def test_a_cutter_build_that_threw_is_reported_as_waiting_and_not_as_cold(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Bug audit MEDIUM-2 of plan 07-05. The second track builds a tokenizer and
    # a splitter next to the weights, and that build throws before it ever asks
    # for the engine, so the holder stays empty and every source this function
    # reads says "cold". Cold reads as "the model arrives on first demand", and
    # the demand it promises is exactly the one that has just failed.
    _pretend_a_model(model_home)
    clock = {"now": 5000.0}
    monkeypatch.setattr(engine_module.time, "monotonic", lambda: clock["now"])

    assert engine_state() == ENGINE_COLD

    note_cutter_failure(clock["now"])

    assert engine_state() == ENGINE_RETRY_PENDING
    assert _held_for(model_home) is None, "the diagnosis still builds nothing"

    clock["now"] += LOAD_RETRY_SECONDS + 1

    # The cooldown is over and nothing has retried yet, which is the same cold
    # the load path falls back to: the next row is what pays for the build.
    assert engine_state() == ENGINE_COLD


def test_a_cutter_build_that_worked_takes_the_waiting_state_back(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The anti vacuity half: a notice that could only ever be set would leave
    # the page in the waiting state for the life of the container, and the row
    # that repaired the track would change nothing an admin can see.
    _pretend_a_model(model_home)
    clock = {"now": 7000.0}
    monkeypatch.setattr(engine_module.time, "monotonic", lambda: clock["now"])
    note_cutter_failure(clock["now"])

    assert engine_state() == ENGINE_RETRY_PENDING

    note_cutter_failure(None)

    assert engine_state() == ENGINE_COLD


def test_a_container_without_a_model_says_missing_although_the_cutter_failed(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The order of the verdicts, held where the two new sources meet. A missing
    # model does not resolve itself and a cooldown does, so the sentence that
    # sends an admin to rebuild the image has to outrank the one that says wait.
    clock = {"now": 9000.0}
    monkeypatch.setattr(engine_module.time, "monotonic", lambda: clock["now"])
    note_cutter_failure(clock["now"])

    assert engine_state() == ENGINE_MISSING


def test_asking_for_the_state_neither_builds_an_instance_nor_loads_one(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # T-07-04. The admin page polls every few seconds, so a status answer that
    # loaded the engine on the way would be the loading trigger of a container
    # nobody is searching on, and it would report the number it caused itself.
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    before = load_count()

    for _ in range(5):
        assert engine_state() == ENGINE_COLD

    assert _held_for(model_home) is None, "the question must not build the instance it asks about"
    assert load_count() == before

    # And the same promise with the notice of the second track set, because that
    # branch is the newest one and it is asked before the holder is read.
    note_cutter_failure(time.monotonic())
    for _ in range(5):
        assert engine_state() == ENGINE_RETRY_PENDING
    note_cutter_failure(None)

    assert _held_for(model_home) is None
    assert load_count() == before

    shared_model().embed_query("bauantrag")
    for _ in range(5):
        assert engine_state() == ENGINE_LOADED

    assert load_count() - before == 1, "five more questions are still one load"


def test_a_container_without_a_model_asks_the_file_system_once_and_not_once_per_poll(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Perf audit PERF-F2. The empty holder is the state in which nobody else
    # answers the artifact question, and it is also the permanent state of a
    # container built without the model stage: the page polls every few seconds
    # for as long as it is open, and every poll was a pair of stats for an
    # answer that cannot change until another image is deployed.
    asked = {"count": 0}
    real = engine_module.artifacts_present

    def counting(directory: Path) -> bool:
        asked["count"] += 1
        return real(directory)

    monkeypatch.setattr(engine_module, "artifacts_present", counting)

    for _ in range(5):
        assert engine_state() == ENGINE_MISSING

    assert asked["count"] == 1, "the no is remembered, the way EmbeddingModel remembers its own"

    # And the handle of the tools takes the memory with it, so a process that is
    # deliberately started over asks again.
    reset()

    assert engine_state() == ENGINE_MISSING
    assert asked["count"] == 2


def test_a_container_with_a_model_keeps_asking_because_a_model_can_be_taken_away(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The other half of the asymmetry, and the reason the cache above is not
    # simply a cache: a directory that has the two files may lose them, and that
    # has to become visible on the page. The two stats it costs are paid on the
    # state that resolves itself, which is the one worth paying for.
    _pretend_a_model(model_home)
    asked = {"count": 0}
    real = engine_module.artifacts_present

    def counting(directory: Path) -> bool:
        asked["count"] += 1
        return real(directory)

    monkeypatch.setattr(engine_module, "artifacts_present", counting)

    for _ in range(3):
        assert engine_state() == ENGINE_COLD

    assert asked["count"] == 3

    (model_home / MODEL_FILE).unlink()

    assert engine_state() == ENGINE_MISSING, "a model taken out of a running container is not remembered as present"


def test_a_cutter_build_that_worked_forgets_the_remembered_absence(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The consistency clause between PERF-F2 and the notice of the second track.
    # A build that worked read both artifacts, so a remembered "no" about that
    # directory is out of date by the moment the notice arrives, and the page
    # must not go on saying "missing" about a track that is embedding.
    asked = {"count": 0}
    real = engine_module.artifacts_present

    def counting(directory: Path) -> bool:
        asked["count"] += 1
        return real(directory)

    monkeypatch.setattr(engine_module, "artifacts_present", counting)

    assert engine_state() == ENGINE_MISSING
    assert asked["count"] == 1

    _pretend_a_model(model_home)
    note_cutter_failure(None)

    assert engine_state() == ENGINE_COLD
    assert asked["count"] == 2


def test_no_state_of_the_closed_set_names_a_place_on_disk() -> None:
    # T-07-01, and the rule of api/status.py one module over: every note of that
    # answer names a state of this container and never a location. These five
    # words travel in the same answer and are held to the same rule.
    assert len(ENGINE_STATES) == 5

    for state in ENGINE_STATES:
        assert state == state.strip()
        assert "/" not in state
        assert "\\" not in state
        assert "." not in state
        assert MODEL_FILE not in state
        assert TOKENIZER_FILE not in state


def test_every_answer_of_the_state_comes_out_of_the_closed_set(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The anti vacuity clause of the case above: a set nothing is drawn from
    # would keep every promise of this file while the answer said whatever it
    # liked.
    assert engine_state() in ENGINE_STATES

    _pretend_a_model(model_home)
    _stand_in(monkeypatch)

    assert engine_state() in ENGINE_STATES

    shared_model().embed_query("bauantrag")

    assert engine_state() in ENGINE_STATES


# ---------------------------------------------------------------------------
# The rule that says whether a search may pay for the weights (plan 14-06).
#
# One place and not three. The three callers that build a SemanticSide would be
# the same condition written three times over, and three places are the place
# where the fourth one is forgotten.
# ---------------------------------------------------------------------------


def test_query_may_load_stays_true_while_the_release_is_switched_off(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The factory state, and the reason the rule is a function and not a
    # constant: with the release switched off nothing about the first search of
    # a container changes, and that is shipped behaviour this phase must not
    # touch outside its own switch.
    assert model_home.is_dir()
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", "0")
    settings.cache_clear()

    assert query_may_load() is True


def test_query_may_load_turns_false_once_the_release_is_switched_on(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The incident of 2026-09-10 in one line: 1838.4 ms against a ceiling of
    # 1500, because the first search after a cold start paid for the weights
    # itself. With the release switched on that moment would come back after
    # every idle span instead of once per container.
    assert model_home.is_dir()
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", "900")
    settings.cache_clear()

    assert query_may_load() is False


def test_asking_whether_a_search_may_load_builds_nothing_and_loads_nothing(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The promise engine_state makes, made again for the same reason one file
    # over: this question sits on the path of every single search, so a question
    # that loaded the engine on the way would be the loading trigger it exists
    # to prevent.
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", "900")
    settings.cache_clear()
    before = load_count()

    for _ in range(5):
        assert query_may_load() is False

    assert _held_for(model_home) is None, "the question must not build the instance it asks about"
    assert load_count() == before


# ---------------------------------------------------------------------------
# The release in the idle span, and the race it must not lose (plan 14-06).
#
# The mechanics live in embed/model.py since plan 14-05: release() lets go,
# collects, trims and counts. What is decided here is when it is called at all,
# and the identity check is the half that has no counterpart over there: the
# warm run of MEM-03 runs beside the unload task, and a release that collides
# with a concurrent load would throw away the load pair that was just paid for.
# ---------------------------------------------------------------------------


def _an_idle_engine(model_home: Path, monkeypatch: pytest.MonkeyPatch, clock: dict[str, float]) -> EmbeddingModel:
    """A held engine that has embedded something and then sat still for ages."""
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    monkeypatch.setattr(model_module.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(engine_module.time, "monotonic", lambda: clock["now"])

    engine = shared_model()
    engine.embed_query("bauantrag")
    clock["now"] += 10_000.0
    return engine


def test_release_if_idle_leaves_an_empty_holder_alone_and_does_not_fill_it(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The case the caller of plan 14-07 meets far more often than the release
    # itself, because it runs on a tick. It must not cost a heap walk and it
    # must not build the instance it asks about: an unloader that builds while
    # asking is the loading trigger of a container nobody is searching on, which
    # is the same argument engine_state makes for itself.
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    before = load_count()

    assert release_if_idle(900) is False
    assert _held_for(model_home) is None, "the question must not build the instance it asks about"
    assert load_count() == before


def test_release_if_idle_does_nothing_for_an_engine_that_never_loaded(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Building the wrapper reads nothing, so an instance in the holder is not a
    # loaded engine. There is nothing to let go of and nothing to hand back.
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    built = shared_model()
    before = unload_count()

    assert built.loaded is False
    assert release_if_idle(900) is False
    assert unload_count() == before


def test_release_if_idle_keeps_an_engine_that_worked_ten_seconds_ago(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The whole point of an idle span: a container in the middle of a working
    # day keeps its weights. Releasing here would pay the 118 MB back over and
    # over and would be the incident of 2026-09-10 on a tick.
    clock = {"now": 1000.0}
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    monkeypatch.setattr(model_module.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(engine_module.time, "monotonic", lambda: clock["now"])
    engine = shared_model()
    engine.embed_query("bauantrag")
    clock["now"] += 10.0
    before = unload_count()

    assert release_if_idle(900) is False
    assert engine.loaded is True
    assert unload_count() == before


def test_release_if_idle_lets_go_of_an_engine_that_has_been_still_for_longer(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The one case in which anything happens at all, and it is measured with the
    # counter of plan 14-05 and never with a byte: a peak difference is not the
    # sum of the loads that produced it.
    clock = {"now": 1000.0}
    engine = _an_idle_engine(model_home, monkeypatch, clock)
    before = unload_count()

    assert release_if_idle(900) is True
    assert engine.loaded is False
    assert unload_count() - before == 1


def test_release_if_idle_with_a_span_of_nought_never_reaches_the_release(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Nought is the word off, and the switch being off is not a span of nought
    # seconds. A function that answered an unbounded release here would be a
    # function with two truths, so the spy has to stay untouched even though the
    # engine is as idle as it will ever be.
    clock = {"now": 1000.0}
    engine = _an_idle_engine(model_home, monkeypatch, clock)
    calls: list[int] = []

    def spy() -> bool:
        calls.append(1)
        return True

    monkeypatch.setattr(engine, "release", spy)

    assert release_if_idle(0) is False
    assert calls == [], "the switch is off, so nothing is asked of the holder"
    assert engine.loaded is True


def test_release_if_idle_keeps_the_engine_a_warm_run_swapped_in(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The race that really counts (14-RESEARCH.md 5.3). The warm run of MEM-03
    # runs beside the unload task, so between reading the clock and letting go
    # the holder can carry a different instance, and that one has just paid 118
    # MB. Driven here by letting the clock question itself do the swap, which is
    # the one moment ordering alone cannot guard against.
    clock = {"now": 1000.0}
    stale = _an_idle_engine(model_home, monkeypatch, clock)

    fresh = EmbeddingModel(model_home, batch_size=2, sequence_len=512)
    fresh.embed_query("bauantrag")
    assert fresh.loaded is True

    real_last_use = stale.last_use

    def swapping_last_use() -> float | None:
        engine_module._ENGINE = (model_home, fresh)
        return real_last_use()

    monkeypatch.setattr(stale, "last_use", swapping_last_use)
    before = unload_count()

    assert release_if_idle(900) is False
    assert fresh.loaded is True, "the engine that was just paid for stays"
    assert unload_count() == before


def test_release_if_idle_treats_a_holder_that_never_embedded_as_not_idle(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # last_use() answers None for a holder that never worked, and None is not an
    # idle span of infinite length: there is nothing to let go of. The handover
    # note of plan 14-05 asks for this case by name.
    clock = {"now": 1000.0}
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    monkeypatch.setattr(model_module.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(engine_module.time, "monotonic", lambda: clock["now"])

    engine = shared_model()
    # The real load path and not a planted field: _load reads the artifacts and
    # binds the engine, and the clock is set one layer further in, by _embed. A
    # holder that loaded and was never asked for a vector is exactly this.
    with engine._lock:
        engine._load()
    clock["now"] += 10_000.0

    assert engine.loaded is True
    assert engine.last_use() is None
    assert release_if_idle(900) is False


def test_release_if_idle_raises_the_counter_that_released_count_passes_through(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The pass through exists so that a caller can read the figure without
    # reaching into embed/model.py, and it has to be the same figure and not a
    # second one kept beside it.
    clock = {"now": 1000.0}
    _an_idle_engine(model_home, monkeypatch, clock)
    before = released_count()

    assert before == unload_count()
    assert release_if_idle(900) is True
    assert released_count() - before == 1
    assert released_count() == unload_count()


def test_the_counter_of_release_if_idle_survives_a_reset_of_the_holder(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The same property the load counter has and for the same reason (T-14-17):
    # every reader takes a difference against a baseline of its own, nothing
    # needs it zeroed, and a counter that can be zeroed is one a gate could zero
    # itself green with.
    clock = {"now": 1000.0}
    _an_idle_engine(model_home, monkeypatch, clock)

    assert release_if_idle(900) is True
    after = released_count()

    reset()

    assert released_count() == after


def _function_of_the_engine_module(name: str) -> ast.FunctionDef:
    """One function of embed/engine.py, read as source and never imported.

    The same stance the syntax tree gate of test_embed_model.py takes: a
    behaviour test says what happened once, a reading of the tree says what
    happens the next time somebody edits the file.
    """
    tree = ast.parse(Path(engine_module.__file__).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"embed/engine.py has no function {name}")


def _calls_named(node: ast.AST, attribute: str) -> list[ast.Call]:
    """Every call of the shape ``something.attribute(...)`` below that node."""
    return [
        inner
        for inner in ast.walk(node)
        if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute) and inner.func.attr == attribute
    ]


def test_release_if_idle_calls_the_release_outside_the_holder_lock() -> None:
    # T-14-16 one layer up. release() takes its own lock and then runs the
    # blocking trim, and a held _LOCK would block every concurrent shared_model
    # question with it. Read out of the tree, because a behaviour test cannot
    # see where a call sits.
    function = _function_of_the_engine_module("release_if_idle")

    assert len(_calls_named(function, "release")) == 1, "one release and no second spelling of it"

    inside = [
        call for block in ast.walk(function) if isinstance(block, ast.With) for call in _calls_named(block, "release")
    ]

    assert inside == [], "the release blocks, so it must not be called under _LOCK"


def test_release_if_idle_reads_the_holder_and_never_fills_it() -> None:
    # T-14-21. _held answers an empty holder with None; shared_model fills it.
    # An unloader that asked through shared_model would build an instance on a
    # container nobody is searching on, every tick, for ever.
    function = _function_of_the_engine_module("release_if_idle")
    names = {node.id for node in ast.walk(function) if isinstance(node, ast.Name)}

    assert "_held" in names
    assert "shared_model" not in names


def test_release_if_idle_checks_identity_and_never_compares_values() -> None:
    # T-14-20. Two EmbeddingModel instances for the same directory carry the
    # same fields, so a value comparison would be the wrong question: what is
    # asked is whether this is still the very object whose clock was read.
    function = _function_of_the_engine_module("release_if_idle")
    checks = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Compare)
        and any(
            isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id == "_held"
            for inner in ast.walk(node.left)
        )
    ]

    assert len(checks) == 1, "the holder is read a second time exactly once, and that reading is the check"
    assert [type(operator) for operator in checks[0].ops] in ([ast.Is], [ast.IsNot]), (
        "identity and never a value comparison"
    )


# ---------------------------------------------------------------------------
# The warm run after a release, and the promise of one load per warm window
# (plan 14-06, success criterion 5 of the phase).
#
# Two levels hold that promise and only the first of them is correctness:
# _load() runs under the lock of the holder and returns at its head when the
# engine is already there, so ten concurrent warm runs raise the load counter
# once whatever the flag does. The flag saves the nine threadpool threads that
# would otherwise wait at that lock. What is measured below is the counter.
# ---------------------------------------------------------------------------


@pytest.fixture
def no_warm_request() -> Iterator[None]:
    """No case inherits the warm request of the case before it.

    The marker is a module global, because a warm run is a fact about this
    process the way the holder is. In a container that is one fact; in a suite
    it outlives the case that set it, and the order the suite happens to run in
    would then be readable off an answer. Cleared on both sides, like the notice
    of the cutter build in conftest.
    """
    engine_module._WARM_WANTED = False
    yield
    engine_module._WARM_WANTED = False


def _release_is_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """The switch of MEM-01 on, which is the only state a warm run happens in."""
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", "900")
    settings.cache_clear()


@pytest.mark.usefixtures("no_warm_request")
def test_no_warm_run_is_wanted_while_the_release_is_switched_off(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # With the switch off no search was ever refused a load, so nothing is owed
    # a warm run. Asking for one anyway must not start one: that would be the
    # behaviour change outside the switch that query_may_load refuses to make.
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", "0")
    settings.cache_clear()
    shared_model()

    request_warm()

    assert warm_wanted() is False


@pytest.mark.usefixtures("no_warm_request")
def test_no_warm_run_is_wanted_while_the_engine_is_loaded(model_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The window is already warm. A second load would be the doubled load of
    # plan 06.1-02 with a new name.
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    _release_is_on(monkeypatch)
    shared_model().embed_query("bauantrag")

    request_warm()

    assert warm_wanted() is False


@pytest.mark.usefixtures("no_warm_request")
def test_no_warm_run_is_wanted_on_a_container_without_a_model(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A container built without the model stage answers lexically for its whole
    # life, and that is not a cold window waiting to be warmed. Warming it would
    # read a directory that has nothing in it, once per refused search.
    assert model_home.is_dir()
    _release_is_on(monkeypatch)
    held = shared_model()
    held.embed_query("bauantrag")

    request_warm()

    assert held.artifacts_absent is True
    assert warm_wanted() is False


@pytest.mark.usefixtures("no_warm_request")
def test_a_warm_run_is_wanted_after_a_release_when_somebody_has_searched(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The one state that answers True, and the anti vacuity clause of the three
    # cases above: a marker that could only ever say no would keep every promise
    # of this block while the warm run never happened.
    clock = {"now": 1000.0}
    engine = _an_idle_engine(model_home, monkeypatch, clock)
    _release_is_on(monkeypatch)

    assert release_if_idle(900) is True
    assert engine.loaded is False
    assert warm_wanted() is False, "nobody has been refused a load yet"

    request_warm()

    assert warm_wanted() is True


@pytest.mark.usefixtures("no_warm_request")
def test_ten_warm_runs_at_once_pay_for_exactly_one_load(model_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Success criterion 5 of the phase in a counter: one load per warm window.
    # Measured as a difference and never as a byte, for the reason the holder
    # above is measured that way.
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    _release_is_on(monkeypatch)
    before = load_count()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        answers = list(pool.map(lambda _index: warm(), range(10)))

    assert any(answers), "one of the ten has to have done the warm run"
    assert load_count() - before == 1, "ten warm runs at once are one session and not ten"
    assert shared_model().loaded is True


@pytest.mark.usefixtures("no_warm_request")
def test_a_warm_run_sets_the_idle_clock_so_the_next_tick_does_not_undo_it(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Not a side effect but the condition. Without the clock the next tick of
    # the unload task would find a holder whose last use is older than the span
    # and would eat the load pair that was just paid for.
    clock = {"now": 1000.0}
    engine = _an_idle_engine(model_home, monkeypatch, clock)
    _release_is_on(monkeypatch)

    assert release_if_idle(900) is True
    stale = engine.last_use()
    assert stale is not None
    clock["now"] += 5_000.0

    assert warm() is True

    fresh = shared_model().last_use()

    assert fresh is not None
    assert fresh > stale
    assert release_if_idle(900) is False, "the window is warm again and the next tick leaves it alone"


@pytest.mark.usefixtures("no_warm_request")
def test_a_warm_run_on_a_container_without_a_model_does_not_throw(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The same stance the search side takes towards a missing model: a verdict
    # and never an exception. The remembered refusal has to stay standing, or
    # the next warm run would read the empty directory again.
    assert model_home.is_dir()
    _release_is_on(monkeypatch)
    held = shared_model()
    held.embed_query("bauantrag")
    assert held.artifacts_absent is True
    request_warm()

    assert warm() is False
    assert held.artifacts_absent is True
    assert held.loaded is False


@pytest.mark.usefixtures("no_warm_request")
def test_a_warm_run_clears_the_request_it_answers(model_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Otherwise the marker would stay set for the life of the container and
    # every later tick would read a warm run that has already happened.
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    _release_is_on(monkeypatch)
    request_warm()

    assert warm() is True
    assert warm_wanted() is False


@pytest.mark.usefixtures("no_warm_request")
def test_asking_whether_a_warm_run_is_wanted_builds_nothing_and_loads_nothing(
    model_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # T-14-21 again, at the second question of this module that a tick asks: an
    # empty holder is answered and never filled.
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    _release_is_on(monkeypatch)
    request_warm()
    before = load_count()

    for _ in range(5):
        assert warm_wanted() is False

    assert _held_for(model_home) is None, "the question must not build the instance it asks about"
    assert load_count() == before


def test_the_warm_text_carries_nothing_of_a_user_and_nothing_of_the_disk() -> None:
    # T-14-22. The text goes through the very same path a search line goes
    # through, so it must not be a search line: a fixed module constant carries
    # no user content into a log, into a vector or into a report.
    assert isinstance(WARM_TEXT, str)
    assert WARM_TEXT
    assert WARM_TEXT.strip() == WARM_TEXT
    assert len(WARM_TEXT) <= 32
    assert "/" not in WARM_TEXT
    assert "\\" not in WARM_TEXT
    assert MODEL_FILE not in WARM_TEXT
    assert TOKENIZER_FILE not in WARM_TEXT
