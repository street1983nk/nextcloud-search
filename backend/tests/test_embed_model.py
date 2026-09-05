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

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
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
    to_int8,
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


# ---------------------------------------------------------------------------
# Loading, batching and the empty case
# ---------------------------------------------------------------------------


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
