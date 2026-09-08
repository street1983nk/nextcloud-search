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
    engine_state,
    shared_model,
)
from findling.embed.model import (
    DIMENSIONS,
    LOAD_RETRY_SECONDS,
    MODEL_FILE,
    TOKENIZER_FILE,
    EmbeddingModel,
    load_count,
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

    shared_model().embed_query("bauantrag")
    for _ in range(5):
        assert engine_state() == ENGINE_LOADED

    assert load_count() - before == 1, "five more questions are still one load"


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
