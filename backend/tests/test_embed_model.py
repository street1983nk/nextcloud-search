"""Text becomes vectors, a missing model becomes a verdict, and no line carries content.

Three claims, and the test file is split along them.

**The prefixes.** ``fastembed`` adds ``query: `` and ``passage: `` for its built
in models and this project registers its own, so nothing sets them unless this
module does, and forgetting them costs retrieval quality without failing
anything (06-RESEARCH.md, pitfall 3). Plan 06-03 measured that they matter: 21 to
31 of 42 German cases and 104 of 120 French ones get a different rank with and
without them. Two kinds of test hold it here. The stand in records the strings
the encoder really saw, so the prefix is proven on every machine; the ranking
test needs the real 118 MB model and runs where there is one.

**The verdict.** A missing or broken model is a state and not an error, exactly
like a missing tesseract in ``extract/ocr.py``: the search keeps its lexical half
(criterion 3), and it can only do that if this module answers with
``embedding_unavailable`` instead of an exception. Those tests run everywhere,
through the stand in, because a failure path that is only tested where it never
happens is not tested.

**The silence.** The text that goes in here is user content. No log line of this
module may carry an excerpt, a file name or the message of a foreign library, and
the test for it writes a marker into the broken model file and looks for it in
the captured log (T-06-20).

The stand in is deliberate and it is the same construction ``tests/test_ocr.py``
uses between a present and an absent engine. It replaces the two functions that
reach for the artifacts on disk and nothing else, so everything above them is the
real code path.
"""

from __future__ import annotations

import ast
import inspect
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy
import pytest

from findling.embed import model as model_module
from findling.embed.model import (
    DIMENSIONS,
    EMBEDDING_UNAVAILABLE,
    PASSAGE_PREFIX,
    QUERY_PREFIX,
    EmbeddingModel,
    load_count,
    to_int8,
    unload_count,
)

SEMANTIK = Path(__file__).resolve().parents[2] / "testdata" / "semantik" / "de.jsonl"

MODEL_ENV = "FINDLING_EMBED_MODEL_DIR"


def _shipped_model() -> Path | None:
    """The model directory of the image, or None where there is none."""
    configured = os.environ.get(MODEL_ENV, "").strip()
    if not configured:
        return None
    directory = Path(configured)
    if (directory / "model.onnx").is_file() and (directory / "tokenizer.json").is_file():
        return directory
    return None


needs_model = pytest.mark.skipif(
    _shipped_model() is None,
    reason=f"{MODEL_ENV} carries no model, so the ranking of the real engine cannot be measured here",
)


# ---------------------------------------------------------------------------
# The stand in: two fakes that replace the two functions touching the disk.
# ---------------------------------------------------------------------------


@dataclass
class FakeEncoding:
    ids: list[int]
    attention_mask: list[int]


@dataclass
class FakeTokenizer:
    """Records every text it is asked to encode, and pads inside its batch."""

    seen: list[str] = field(default_factory=list)
    truncation: int | None = None

    def encode_batch(self, texts: list[str]) -> list[FakeEncoding]:
        self.seen.extend(texts)
        encodings = []
        for text in texts:
            ids = [ord(character) % 97 + 1 for character in text[: self.truncation or 512]]
            encodings.append(FakeEncoding(ids=ids, attention_mask=[1] * len(ids)))
        width = max(len(one.ids) for one in encodings)
        for one in encodings:
            missing = width - len(one.ids)
            one.ids = one.ids + [0] * missing
            one.attention_mask = one.attention_mask + [0] * missing
        return encodings


@dataclass
class FakeInput:
    name: str


@dataclass
class FakeSession:
    """Answers with a deterministic hidden state derived from the token ids."""

    batches: list[int] = field(default_factory=list)
    widths: list[int] = field(default_factory=list)

    def get_inputs(self) -> list[FakeInput]:
        return [FakeInput("input_ids"), FakeInput("attention_mask")]

    def get_outputs(self) -> list[FakeInput]:
        return [FakeInput("last_hidden_state")]

    def run(self, _outputs: list[str], feed: dict[str, Any]) -> list[Any]:
        ids = feed["input_ids"]
        self.batches.append(int(ids.shape[0]))
        self.widths.append(int(ids.shape[1]))
        base = ids.astype(numpy.float32)[:, :, None]
        ramp = numpy.arange(1, DIMENSIONS + 1, dtype=numpy.float32)[None, None, :]
        return [numpy.sin(base / (ramp + 1.0))]


@dataclass
class StandIn:
    tokenizer: FakeTokenizer
    session: FakeSession


@pytest.fixture
def model_dir(tmp_path: Path) -> Path:
    """A directory that looks like a model directory from the outside."""
    (tmp_path / "model.onnx").write_bytes(b"not a real graph")
    (tmp_path / "tokenizer.json").write_text("{}", encoding="utf-8")
    return tmp_path


@pytest.fixture
def stand_in(monkeypatch: pytest.MonkeyPatch) -> StandIn:
    tokenizer = FakeTokenizer()
    session = FakeSession()

    def open_encoder(_directory: Path, *, sequence_len: int) -> FakeTokenizer:
        tokenizer.truncation = sequence_len
        return tokenizer

    def open_session(_path: Path, *, threads: int) -> FakeSession:
        assert threads >= 1
        return session

    monkeypatch.setattr(model_module, "_open_encoder", open_encoder)
    monkeypatch.setattr(model_module, "_open_session", open_session)
    return StandIn(tokenizer=tokenizer, session=session)


def _model(directory: Path, **kwargs: int) -> EmbeddingModel:
    settings = {"batch_size": 2, "sequence_len": 256, **kwargs}
    return EmbeddingModel(directory, batch_size=settings["batch_size"], sequence_len=settings["sequence_len"])


# ---------------------------------------------------------------------------
# The prefixes
# ---------------------------------------------------------------------------


def test_the_two_prefixes_are_the_ones_the_model_was_trained_with() -> None:
    # Named constants rather than literals at the call site, in the shape of the
    # OCR language allowlist: two places that spell a prefix are two places that
    # can disagree, and the disagreement would be invisible.
    assert QUERY_PREFIX == "query: "
    assert PASSAGE_PREFIX == "passage: "


def test_a_passage_reaches_the_encoder_with_its_prefix(model_dir: Path, stand_in: StandIn) -> None:
    outcome = _model(model_dir).embed_passages(["Die Kuendigungsfrist betraegt drei Monate."])

    assert outcome.available
    assert stand_in.tokenizer.seen == ["passage: Die Kuendigungsfrist betraegt drei Monate."]


def test_a_query_reaches_the_encoder_with_its_prefix(model_dir: Path, stand_in: StandIn) -> None:
    outcome = _model(model_dir).embed_query("Wie lange dauert die Kuendigung?")

    assert outcome.available
    assert stand_in.tokenizer.seen == ["query: Wie lange dauert die Kuendigung?"]


def test_every_vector_has_the_width_of_the_model(model_dir: Path, stand_in: StandIn) -> None:
    outcome = _model(model_dir).embed_passages(["erster Text", "zweiter Text", "dritter Text"])

    assert len(outcome.vectors) == 3
    assert all(len(vector) == DIMENSIONS for vector in outcome.vectors)
    assert DIMENSIONS == 384


def test_a_vector_is_normalised(model_dir: Path, stand_in: StandIn) -> None:
    outcome = _model(model_dir).embed_query("eine Anfrage")

    # e5 is trained with cosine similarity, and the vec0 column of plan 06-04
    # declares L2. On normalised vectors the two produce the same order, and
    # that equivalence is the reason the column may declare either.
    length = sum(value * value for value in outcome.vectors[0]) ** 0.5
    assert length == pytest.approx(1.0, abs=1e-5)


# ---------------------------------------------------------------------------
# The verdict
# ---------------------------------------------------------------------------


def test_a_missing_model_is_a_verdict_and_not_an_exception(tmp_path: Path) -> None:
    outcome = _model(tmp_path).embed_passages(["ein Text"])

    # The whole of criterion 3 rests on this line: the vector half answers with
    # a named state, the caller turns it into an empty vector list, and the
    # lexical answer stands.
    assert outcome.verdict == EMBEDDING_UNAVAILABLE
    assert outcome.available is False
    assert outcome.vectors == ()


def test_a_missing_model_answers_the_same_way_for_a_query(tmp_path: Path) -> None:
    outcome = _model(tmp_path).embed_query("eine Anfrage")

    assert outcome.verdict == EMBEDDING_UNAVAILABLE
    assert outcome.vectors == ()


def test_a_broken_model_is_the_same_verdict_and_not_a_library_error(tmp_path: Path) -> None:
    (tmp_path / "model.onnx").write_bytes(b"MARKERTEXT-4711 not a graph")
    (tmp_path / "tokenizer.json").write_text("MARKERTEXT-4711 not json", encoding="utf-8")

    outcome = _model(tmp_path).embed_passages(["ein Text"])

    assert outcome.verdict == EMBEDDING_UNAVAILABLE


def test_the_failure_log_carries_the_type_name_and_nothing_else(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    marker = "MARKERTEXT-4711"
    (tmp_path / "model.onnx").write_bytes(f"{marker} not a graph".encode())
    (tmp_path / "tokenizer.json").write_text(f"{marker} not json", encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="findling.embed.model"):
        _model(tmp_path).embed_passages(["Die Kuendigungsfrist betraegt drei Monate."])

    # T-06-20. Not the message of the foreign library, not the path, not the
    # text that was to be embedded. Only the name of the exception class.
    assert caplog.text
    assert marker not in caplog.text
    assert str(tmp_path) not in caplog.text
    assert "Kuendigungsfrist" not in caplog.text


def test_a_failed_load_is_not_retried_on_every_call(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    engine = _model(tmp_path)

    with caplog.at_level(logging.WARNING, logger="findling.embed.model"):
        engine.embed_passages(["eins"])
        engine.embed_passages(["zwei"])
        engine.embed_passages(["drei"])

    # The second track walks tens of thousands of documents. A model that is not
    # there is not there for all of them, and one warning per file would be a
    # log nobody can read past.
    assert caplog.text.count("embedding") == 1


def test_a_missing_model_is_looked_for_once_and_not_once_per_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The permanent half of the distinction of 06.1-RESEARCH.md, pitfall 2. A
    # directory without the two files is a property of the installation, it is
    # true for the whole life of the process, and looking again would be a stat
    # call per document over tens of thousands of them. Counted at the seam
    # instead of in the log, because the log only says how often it was said.
    looks: list[Path] = []
    real = model_module._artifacts_present

    def counting(directory: Path) -> bool:
        looks.append(directory)
        return real(directory)

    monkeypatch.setattr(model_module, "_artifacts_present", counting)
    engine = _model(tmp_path)

    engine.embed_passages(["eins"])
    engine.embed_passages(["zwei"])
    engine.embed_query("drei")

    assert looks == [tmp_path]


def test_a_run_that_throws_does_not_switch_the_model_off_for_good(
    model_dir: Path, stand_in: StandIn, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The temporary half of the same distinction, and the reason it had to be
    # made before the engine became a shared one. Until 06.1-02 a single batch
    # that threw set _engine to None with _tried still True, so the wrapper was
    # dead for the rest of the process. Shared, that one batch of the worker
    # would have cost the search side its semantics until the next restart, and
    # the symptom is a container that suddenly answers lexically after hours
    # with nothing having changed.
    engine = _model(model_dir)
    real_run = stand_in.session.run
    thrown = 0

    def failing_once(outputs: list[str], feed: dict[str, Any]) -> list[Any]:
        nonlocal thrown
        if thrown == 0:
            thrown += 1
            raise RuntimeError("the batch could not be run")
        return real_run(outputs, feed)

    monkeypatch.setattr(stand_in.session, "run", failing_once)

    first = engine.embed_passages(["eins"])
    second = engine.embed_passages(["zwei"])

    assert first.verdict == EMBEDDING_UNAVAILABLE
    assert second.available, "a thrown run is a state of one batch, not of the installation"
    assert len(second.vectors) == 1


# ---------------------------------------------------------------------------
# Loading, batching and the empty case
# ---------------------------------------------------------------------------


def test_the_load_counter_says_how_often_the_weights_were_read(model_dir: Path, stand_in: StandIn) -> None:
    # The counter exists so that the proof of the shared engine needs no timing
    # and no byte, in the shape analyzer.build_count() established for the
    # automaton. Two calls on one wrapper read the artifacts once.
    before = load_count()
    engine = _model(model_dir)

    engine.embed_passages(["eins"])
    engine.embed_passages(["zwei"])

    assert load_count() - before == 1
    assert stand_in.session.batches == [1, 1]

    # And the counterpart, without which the assertion above would also hold for
    # a number that never moves: a second wrapper really does read them again.
    _model(model_dir).embed_passages(["drei"])

    assert load_count() - before == 2


def test_importing_the_module_loads_no_model(model_dir: Path, stand_in: StandIn) -> None:
    engine = _model(model_dir)

    # Building the object may not reach for the artifacts either: the container
    # starts long before the second track runs, and 118 MB of weights at import
    # time would be resident on every box whether or not anything is embedded.
    assert engine.loaded is False
    assert stand_in.tokenizer.seen == []

    engine.embed_passages(["ein Text"])

    assert engine.loaded is True


def test_an_empty_list_returns_nothing_and_loads_nothing(model_dir: Path, stand_in: StandIn) -> None:
    engine = _model(model_dir)

    outcome = engine.embed_passages([])

    assert outcome.available
    assert outcome.vectors == ()
    assert engine.loaded is False
    assert stand_in.session.batches == []


def test_the_batch_size_comes_from_the_settings_and_not_from_the_library(model_dir: Path, stand_in: StandIn) -> None:
    engine = _model(model_dir, batch_size=2)

    engine.embed_passages([f"Text Nummer {number}" for number in range(7)])

    # Lever 4 of 06-RESEARCH.md 3.6 only works if the number is ours: fastembed
    # picks its own batch size, and a default that quietly grew would raise the
    # activation peak on the box this product is written for.
    assert stand_in.session.batches == [2, 2, 2, 1]


def test_the_sequence_length_comes_from_the_settings_too(model_dir: Path, stand_in: StandIn) -> None:
    engine = _model(model_dir, sequence_len=64)

    engine.embed_passages(["x" * 500])

    assert stand_in.tokenizer.truncation == 64
    assert stand_in.session.widths == [64]


def test_the_int8_form_is_the_width_the_vector_column_declares(model_dir: Path, stand_in: StandIn) -> None:
    outcome = _model(model_dir).embed_query("eine Anfrage")

    raw = to_int8(outcome.vectors[0])

    # store/vectors.sql declares int8[384], and vectors.py refuses anything of a
    # different width. The scale lives here because it is a property of the
    # model: e5 answers normalised vectors, so the range is fixed.
    assert len(raw) == DIMENSIONS
    assert isinstance(raw, bytes)


# ---------------------------------------------------------------------------
# The idle clock, the activity counter and may_load
# ---------------------------------------------------------------------------


class _TickingClock:
    """A monotonic clock that steps one second per reading.

    ``time.monotonic`` can answer twice with the same float on a fast machine,
    and a test that asserts the clock moved would then fail for a reason that
    has nothing to do with this module. Standing in for the whole module is
    safe here because ``monotonic`` is the only member ``embed/model.py`` calls.
    """

    def __init__(self) -> None:
        self.now = 1000.0

    def monotonic(self) -> float:
        self.now += 1.0
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> _TickingClock:
    ticking = _TickingClock()
    monkeypatch.setattr(model_module, "time", ticking)
    return ticking


def test_a_query_moves_the_idle_clock_forward(model_dir: Path, stand_in: StandIn, clock: _TickingClock) -> None:
    """The clock the release policy of plan 14-06 reads, seen from a search.

    A method and not a bare field, because reading a private field from outside
    is how a second spelling of one truth begins.
    """
    engine = _model(model_dir)

    assert engine.last_use() is None, "nothing has been embedded yet, and that is not an idle span"

    engine.embed_query("Wie lange dauert die Kuendigung?")

    marked = engine.last_use()
    assert marked is not None
    assert marked > clock.now - 2.0


def test_a_passage_batch_moves_the_same_clock(model_dir: Path, stand_in: StandIn, clock: _TickingClock) -> None:
    """One line in ``_embed`` covers the search and the index track at once.

    Both public entries come through ``_embed``, so the clock sits there and not
    in the two of them. Were it in ``embed_query`` alone, a container in the
    middle of an index pass would look idle to the release policy and drop the
    weights the next row needs.
    """
    engine = _model(model_dir)

    engine.embed_query("eine Anfrage")
    after_the_query = engine.last_use()
    engine.embed_passages(["ein Abschnitt"])
    after_the_passages = engine.last_use()

    assert after_the_query is not None
    assert after_the_passages is not None
    assert after_the_passages > after_the_query


def test_an_empty_batch_does_not_end_an_idle_span(model_dir: Path, stand_in: StandIn, clock: _TickingClock) -> None:
    """An empty batch is the normal answer for a document without text.

    It must not move the clock: a pass over a directory of images would
    otherwise hold the weights warm with documents that produced no text at all.
    And it must not load, which is the line the empty check already held.
    """
    engine = _model(model_dir)

    outcome = engine.embed_passages([])

    assert outcome.available
    assert engine.last_use() is None
    assert engine.loaded is False

    engine.embed_passages(["ein Abschnitt"])
    marked = engine.last_use()
    engine.embed_passages([])

    assert engine.last_use() == marked


def test_a_query_that_may_not_load_answers_the_verdict_instead_of_loading(model_dir: Path, stand_in: StandIn) -> None:
    """The lower half of MEM-03: a search may be told not to fetch the weights.

    The answer is the same ``embedding_unavailable`` a missing model gives,
    which is the tested path of D-19 into a purely lexical result. Whether the
    switch should ever be false is not decided here; that is plan 14-06.
    """
    engine = _model(model_dir)
    before = load_count()

    outcome = engine.embed_query("eine Anfrage", may_load=False)

    assert outcome.verdict == EMBEDDING_UNAVAILABLE
    assert outcome.available is False
    assert load_count() == before
    assert engine.loaded is False
    assert stand_in.tokenizer.seen == []


def test_a_query_that_may_not_load_answers_normally_on_a_loaded_holder(model_dir: Path, stand_in: StandIn) -> None:
    """The switch forbids the load and nothing else.

    On a warm holder the same call is an ordinary search and has to stay one:
    the degradation of 14-06 is about the 1.5 second ceiling over a cold load,
    not about answering worse while the weights are right there.
    """
    engine = _model(model_dir)
    engine.embed_passages(["ein Abschnitt"])
    before = load_count()

    outcome = engine.embed_query("eine Anfrage", may_load=False)

    assert outcome.available
    assert len(outcome.vectors) == 1
    assert len(outcome.vectors[0]) == DIMENSIONS
    assert load_count() == before


def test_the_index_track_has_no_switch_and_always_loads(model_dir: Path, stand_in: StandIn) -> None:
    """``embed_passages`` does not carry ``may_load``, and that is a decision.

    There is no 1.5 second ceiling over an index pass, and after a release the
    next row of that pass is exactly the right moment to fetch the weights back.
    The default ``True`` on the other two keeps every existing call byte for
    byte what it was.
    """
    assert "may_load" not in inspect.signature(EmbeddingModel.embed_passages).parameters

    query = inspect.signature(EmbeddingModel.embed_query).parameters["may_load"]
    assert query.default is True
    assert query.kind is inspect.Parameter.KEYWORD_ONLY

    shared = inspect.signature(EmbeddingModel._embed).parameters["may_load"]
    assert shared.default is True
    assert shared.kind is inspect.Parameter.KEYWORD_ONLY

    engine = _model(model_dir)
    before = load_count()

    engine.embed_passages(["ein Abschnitt"])

    assert load_count() - before == 1


def test_the_activity_counter_stands_above_zero_while_a_batch_runs(
    model_dir: Path, stand_in: StandIn, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The one new invariant of this phase, read from inside a running batch.

    The existing RLock deliberately does not cover the graph run, and a release
    does more than let go: it calls ``gc.collect()`` and ``malloc_trim``, and
    those two walk the heap this batch is allocating in (14-RESEARCH.md 4.3,
    point 4).
    """
    engine = _model(model_dir)
    seen: list[int] = []
    real_run = stand_in.session.run

    def watching(outputs: list[str], feed: dict[str, Any]) -> list[Any]:
        seen.append(engine._in_flight)
        return real_run(outputs, feed)

    monkeypatch.setattr(stand_in.session, "run", watching)

    assert engine._in_flight == 0

    engine.embed_passages(["eins", "zwei", "drei"])

    assert seen == [1, 1], "one reading per batch, and this holder cuts three texts into two"
    assert engine._in_flight == 0


def test_the_activity_counter_falls_back_to_zero_after_a_batch_that_threw(
    model_dir: Path, stand_in: StandIn, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A thrown batch leaves no standing count behind.

    A counter that a thrown batch leaves at one blocks every later release for
    the life of the process, and the log would say nothing at all: the holder
    would simply never let go again.
    """
    engine = _model(model_dir)

    def throwing(_outputs: list[str], _feed: dict[str, Any]) -> list[Any]:
        raise RuntimeError("the batch could not be run")

    monkeypatch.setattr(stand_in.session, "run", throwing)

    assert engine.embed_passages(["eins"]).verdict == EMBEDDING_UNAVAILABLE
    assert engine._in_flight == 0


# ---------------------------------------------------------------------------
# Letting go: release, the unload counter and the facts that stay
# ---------------------------------------------------------------------------


def _model_source() -> str:
    """The text of ``embed/model.py``, for the gates that read it as source."""
    return inspect.getsource(model_module)


@pytest.fixture
def quiet_pages(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Count the calls to the page return without paying gc and the trim.

    The two steps themselves have their own cases further down, one for each
    way a libc can refuse them and one for their order. Everything that is
    about letting go rather than about the pages is faster and quieter with a
    stand in, and it stays independent of the C library under the test machine.
    """
    calls: list[str] = []
    monkeypatch.setattr(model_module, "_return_free_pages_to_the_system", lambda: calls.append("pages"))
    return calls


def test_a_release_on_a_loaded_holder_lets_go_and_counts_it(
    model_dir: Path, stand_in: StandIn, quiet_pages: list[str]
) -> None:
    """The plain case, and the counter beside the load counter.

    Two numbers rather than one, because a load count of three says nothing on
    its own: on a container that never released it is a bug, on one that
    released twice it is the expected number.
    """
    engine = _model(model_dir)
    engine.embed_passages(["ein Abschnitt"])
    before = unload_count()

    assert engine.release() is True
    assert engine.loaded is False
    assert unload_count() - before == 1
    assert quiet_pages == ["pages"]


def test_a_release_on_a_holder_that_never_loaded_says_so(
    model_dir: Path, stand_in: StandIn, quiet_pages: list[str]
) -> None:
    """False means there was nothing to let go of, and nothing was done.

    The caller of plan 14-07 runs on a tick and will meet this case far more
    often than the other one. It may not cost a heap walk every time, and it
    may not raise the counter that the A/B measurement of phase 15 reads.
    """
    engine = _model(model_dir)
    before = unload_count()

    assert engine.release() is False
    assert unload_count() == before
    assert quiet_pages == []


def test_a_release_during_a_batch_leaves_the_engine_standing(
    model_dir: Path, stand_in: StandIn, monkeypatch: pytest.MonkeyPatch, quiet_pages: list[str]
) -> None:
    """T-14-15, asked from inside the running batch rather than from beside it.

    The local reference in ``_embed`` holds the engine alive whatever this
    answers, so nothing would segfault. What would happen is that gc.collect()
    and malloc_trim walk the heap this batch is allocating in. The next tick
    tries again, and one skipped release is cheaper than that.
    """
    engine = _model(model_dir)
    answers: list[bool] = []
    real_run = stand_in.session.run

    def releasing(outputs: list[str], feed: dict[str, Any]) -> list[Any]:
        answers.append(engine.release())
        return real_run(outputs, feed)

    monkeypatch.setattr(stand_in.session, "run", releasing)

    outcome = engine.embed_passages(["ein Abschnitt"])

    assert answers == [False]
    assert outcome.available, "and the batch it refused to interrupt finished normally"
    assert engine.loaded is True
    assert quiet_pages == []


def test_the_next_batch_after_a_release_reads_the_artifacts_again(
    model_dir: Path, stand_in: StandIn, quiet_pages: list[str]
) -> None:
    """A release is not a switch off: the next row loads, and the counter says so."""
    engine = _model(model_dir)
    engine.embed_passages(["eins"])
    before = load_count()

    assert engine.release() is True
    assert engine.loaded is False

    outcome = engine.embed_passages(["zwei"])

    assert outcome.available
    assert engine.loaded is True
    assert load_count() - before == 1


def test_an_absent_model_directory_survives_a_release(tmp_path: Path, quiet_pages: list[str]) -> None:
    """Pitfall 8, first of the three facts: a property of the installation.

    A directory without the two artifacts stays without them while this process
    runs, and looking again would be a pair of stat calls per document over tens
    of thousands of them. A release that cleared the flag would bring that pair
    back for ever, and nothing would fail anywhere.
    """
    engine = _model(tmp_path)
    engine.embed_passages(["ein Abschnitt"])

    assert engine.artifacts_absent is True
    assert engine.release() is False, "there was never an engine to let go of"
    assert engine.artifacts_absent is True


def test_a_load_that_threw_keeps_its_cooldown_across_a_release(
    model_dir: Path, monkeypatch: pytest.MonkeyPatch, quiet_pages: list[str]
) -> None:
    """Pitfall 8, second fact: the cooldown is a moment that is still running.

    An open that threw is remembered with a timestamp and tried again after
    LOAD_RETRY_SECONDS. A release that cleared the stamp would end that waiting
    silently, and a broken graph would be opened once per document again instead
    of twelve times an hour.
    """

    def throwing(_directory: Path, *, sequence_len: int) -> Any:
        raise RuntimeError("no air for 118 MB of weights")

    monkeypatch.setattr(model_module, "_open_encoder", throwing)
    engine = _model(model_dir)
    engine.embed_passages(["ein Abschnitt"])
    stamp = engine._load_failed_at

    assert stamp is not None
    assert engine.load_cooling_down is True
    assert engine.release() is False

    assert engine._load_failed_at == stamp, "the moment that failed is not this operation's business"
    assert engine.load_cooling_down is True


def test_the_warning_flag_of_a_thrown_batch_survives_a_release(
    model_dir: Path,
    stand_in: StandIn,
    monkeypatch: pytest.MonkeyPatch,
    quiet_pages: list[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Pitfall 8, third fact, and this one is visible in the log.

    The flag says that the one warning about a thrown batch has been said. The
    second track walks tens of thousands of documents, so a release that cleared
    it would hand the log a fresh warning after every idle span, which is the
    flood the flag exists to prevent.
    """
    engine = _model(model_dir)

    def throwing(_outputs: list[str], _feed: dict[str, Any]) -> list[Any]:
        raise RuntimeError("the batch could not be run")

    monkeypatch.setattr(stand_in.session, "run", throwing)

    with caplog.at_level(logging.DEBUG, logger="findling.embed.model"):
        engine.embed_passages(["eins"])
        assert engine.release() is True
        engine.embed_passages(["zwei"])

    said = [record for record in caplog.records if "failed and the search stays lexical" in record.getMessage()]

    assert len(said) == 1, "the second thrown batch speaks at debug level, before and after a release alike"
    assert said[0].levelno == logging.WARNING


def test_the_unload_counter_can_never_be_set_back() -> None:
    """T-14-17, as a property of the source rather than of one run.

    A counter that can be zeroed is a counter a gate could zero itself green
    with, and the A/B measurement of phase 15 reads exactly this number.
    ``engine.reset()`` does not touch it either, which is what this reading
    proves: the module holds one initialisation and one increment and nothing
    else that writes the name.
    """
    tree = ast.parse(_model_source())
    touches: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            written = [target for target in node.targets if isinstance(target, ast.Name)]
        elif isinstance(node, ast.AugAssign):
            written = [node.target] if isinstance(node.target, ast.Name) else []
        else:
            continue
        if any(name.id == "_UNLOAD_COUNT" for name in written):
            touches.append(ast.unparse(node))

    assert sorted(touches) == ["_UNLOAD_COUNT += 1", "_UNLOAD_COUNT = 0"]


# ---------------------------------------------------------------------------
# The two steps of the return, and the libc that may not offer the second
# ---------------------------------------------------------------------------


def test_a_libc_that_cannot_be_opened_does_not_stop_a_release(
    model_dir: Path, stand_in: StandIn, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Pitfall 2, first shape: ``ctypes.CDLL`` throws ``OSError``.

    On musl or any other foreign base the library is simply not there. Without
    the guard the release task dies on the first tick and, depending on the
    shape of the caller, takes the search with it. A test that only runs on the
    base image would never enter this branch: the shipped image is glibc and
    answers every time, so the failure would first appear on somebody else's
    container.

    Two holders and two releases, because the warning is said once per process
    and not once per holder.
    """
    monkeypatch.setattr(model_module, "_TRIM_UNAVAILABLE_WARNED", False)

    def refusing(_name: str) -> Any:
        raise OSError("libc.so.6: cannot open shared object file")

    monkeypatch.setattr(model_module, "ctypes", SimpleNamespace(CDLL=refusing))

    first = _model(model_dir)
    first.embed_passages(["ein Abschnitt"])
    second = _model(model_dir)
    second.embed_passages(["ein Abschnitt"])

    with caplog.at_level(logging.DEBUG, logger="findling.embed.model"):
        assert first.release() is True
        assert second.release() is True

    assert first.loaded is False
    assert second.loaded is False

    said = [record for record in caplog.records if "malloc_trim" in record.getMessage()]

    assert len(said) == 1, "once per process, not once per holder and not once per tick"
    assert said[0].levelno == logging.WARNING
    assert "OSError" in said[0].getMessage(), "the class name and nothing else of what went wrong"


def test_a_libc_without_malloc_trim_does_not_stop_a_release(
    model_dir: Path, stand_in: StandIn, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Pitfall 2, second shape: the library opens and has no such symbol.

    The other half of the narrow catch, and it is a different exception from a
    different line. Four fifths of the return fall away here and the container
    keeps running, which is the same stance ``extract/ocr.py`` takes towards a
    machine without tesseract.
    """
    monkeypatch.setattr(model_module, "_TRIM_UNAVAILABLE_WARNED", False)
    monkeypatch.setattr(model_module, "ctypes", SimpleNamespace(CDLL=lambda _name: SimpleNamespace()))

    engine = _model(model_dir)
    engine.embed_passages(["ein Abschnitt"])
    before = unload_count()

    with caplog.at_level(logging.DEBUG, logger="findling.embed.model"):
        assert engine.release() is True
        engine.embed_passages(["noch ein Abschnitt"])
        assert engine.release() is True

    assert engine.loaded is False
    assert unload_count() - before == 2, "a libc without the symbol does not make a release a non event"

    said = [record for record in caplog.records if "malloc_trim" in record.getMessage()]

    assert len(said) == 1
    assert "AttributeError" in said[0].getMessage()


def test_the_collect_runs_before_the_trim(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pitfall 1: a trim before the collect finds the blocks still referenced.

    The order is the whole recipe. Reversed, the trim walks an arena whose
    blocks are all still in use, hands back nothing, and the collect afterwards
    frees them into an arena nobody trims any more. The warning sign in a
    measurement is a saving under 100 MB, and the pre-check of 2026-09-19 says
    what is at stake: the collect alone is worth 15 to 19 percent of a load, the
    trim the remaining 80 to 85.

    Recorded at run time and read in the source, because a recording proves what
    happened once and the source proves what will happen next time.
    """
    calls: list[str] = []

    class _Libc:
        def malloc_trim(self, pad: int) -> int:
            calls.append(f"malloc_trim({pad})")
            return 1

    monkeypatch.setattr(model_module, "gc", SimpleNamespace(collect=lambda: calls.append("collect")))
    monkeypatch.setattr(model_module, "ctypes", SimpleNamespace(CDLL=lambda _name: _Libc()))

    model_module._return_free_pages_to_the_system()

    assert calls == ["collect", "malloc_trim(0)"]

    body = inspect.getsource(model_module._return_free_pages_to_the_system).split('"""')[2]

    assert body.index("gc.collect()") < body.index("malloc_trim")


def test_a_release_lets_go_of_the_engine_and_writes_nothing_else() -> None:
    """The three remembered facts, as a property of the source rather than of three runs.

    The three cases above each hold one of them, and each one holds it in the
    only situation that can be built: a holder with an absent directory never
    has an engine, and a load that threw leaves none either, so those two can
    only be asked across a release that answers False. This reading closes that
    gap from the other side. The method writes one attribute, and the name of it
    is ``_engine``.
    """
    tree = ast.parse(_model_source())
    bodies = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "release"]

    assert len(bodies) == 1, "one release and not two spellings of it"

    assigned = [
        target.attr
        for node in ast.walk(bodies[0])
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Attribute)
    ]

    assert assigned == ["_engine"]


# ---------------------------------------------------------------------------
# The ranking, against the real model
# ---------------------------------------------------------------------------


def _cases(count: int) -> list[dict[str, str]]:
    lines = SEMANTIK.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[:count]]


def _ranking(engine: EmbeddingModel, query: str, passages: list[str], *, prefixes: bool) -> list[int]:
    if prefixes:
        query_vectors = engine.embed_query(query).vectors
        passage_vectors = engine.embed_passages(passages).vectors
    else:
        query_vectors = engine._embed([query], prefix="").vectors
        passage_vectors = engine._embed(passages, prefix="").vectors
    scores = [sum(a * b for a, b in zip(query_vectors[0], vector, strict=True)) for vector in passage_vectors]
    return sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)


@needs_model
def test_the_prefixes_change_the_ranking_of_the_real_model() -> None:
    directory = _shipped_model()
    assert directory is not None
    cases = _cases(10)
    passages = [case["passage"] for case in cases]
    engine = EmbeddingModel(directory, batch_size=2, sequence_len=512)

    moved = 0
    for case in cases:
        with_prefix = _ranking(engine, case["query"], passages, prefixes=True)
        without = _ranking(engine, case["query"], passages, prefixes=False)
        moved += with_prefix != without

    # D-05, and the number this expects is deliberately the weakest one the
    # measurement supports: plan 06-03 found a changed rank in half of all
    # cases, so one in ten is a floor and not a target. What the test rules out
    # is the alarming case, where the prefixes make no difference at all and
    # somebody removes them as decoration.
    assert moved >= 1


@needs_model
def test_the_real_model_answers_the_declared_width() -> None:
    directory = _shipped_model()
    assert directory is not None
    engine = EmbeddingModel(directory, batch_size=2, sequence_len=512)

    outcome = engine.embed_passages([case["passage"] for case in _cases(3)])

    assert outcome.available
    assert [len(vector) for vector in outcome.vectors] == [DIMENSIONS] * 3
