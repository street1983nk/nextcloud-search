"""Text into vectors, with the prefixes E5 expects, under the caps that were measured.

The engine runs inside this process and not as a child, unlike the OCR engine:
it is a library with a session and 118 MB of weights, and starting a process per
document would pay that load again every time. What it borrows from
``extract/ocr.py`` is the shape of the answer, and that is the important half.

**The cap cascade, and its order is the whole statement.** Four numbers stand
between a document and a vector, and each one is applied before the next:

* the token cap of D-01, the first 1024 tokens of a document, applied in
  ``embed/chunker.py`` before anything is split
* the chunk size, at most the 512 token window of the model
* the batch size, lever 4 of 06-RESEARCH.md 3.6, which shapes the activation peak
* the sequence length, lever 5, whose attention matrix grows with its square

The numbers themselves live in :mod:`findling.config` with the line of reasoning
that produced them, and the measurement protocol is in ``docs/embeddings.md`` and
``docs/measurements/2026-09-05-welle0-arm64/``.

**A missing model is a state, not an error.** That is the same rule
``extract/ocr.py`` follows for a missing tesseract, and here it carries
criterion 3 of the phase: when the model is gone, the vector list is empty, the
RRF merge becomes the identity on the lexical list, and the search still answers.
So every failure of the load path ends as the named verdict
``embedding_unavailable`` and never as an exception, and the load is attempted
once rather than once per document.

**Nothing this module logs carries content.** The texts that pass through here
are user documents and user queries. A warning states the class name of what went
wrong and nothing else: not the message of the library, which quotes what it was
reading, not the path, which is a file name, and never an excerpt (T-06-20).

**What is deliberately not decided here.** Whether a file belongs in the
embedding track at all. That falls in the poller of plan 06-07, in the same way
``extract/ocr.py`` leaves the text layer decision to ``extract/pdf.py``.

**Why onnxruntime directly and not fastembed.** Measured against fastembed 0.8.0
in this repository's own lock file on 2026-09-05, because assumption A11 asked
exactly this question. ``fastembed/common/onnx_model.py`` carries
``EXPOSED_SESSION_OPTIONS = ("enable_cpu_mem_arena",)``: one of the two session
options lever 6 names is reachable and ``arena_extend_strategy`` is not. The
deciding half is a different one though. ``fastembed/common/preprocessor_utils.py``
reads the truncation length out of ``tokenizer_config.json`` and offers no way to
set it, so lever 5 would not be ours at all, and the sequence length is the
strongest of the four measured levers (37 to 40 percent of throughput, wave 0
measurement B). Going around the library costs the pooling and the normalisation,
which are twenty lines and are pinned by a test, and it buys both levers plus the
prefixes we have to set ourselves anyway.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from tokenizers import Tokenizer

LOGGER = logging.getLogger("findling.embed.model")

# The two prefixes intfloat/multilingual-e5-small was trained with, as named
# constants for the same reason the OCR language allowlist is one: a literal at
# the call site is a literal that can be spelled differently in the second call
# site, and here the difference would be invisible.
#
# They have to be set by hand because fastembed adds them for its built in
# models only and this project registers its own (06-RESEARCH.md, pitfall 3).
# Plan 06-03 measured what they are worth: with and without them, 21 of 42
# German, 29 of 42 English and 104 of 120 French cases get a different rank.
# Nothing fails when they are missing, the answers simply get worse, which is
# why there is a test beside these two lines and not only a comment.
QUERY_PREFIX: Final = "query: "
PASSAGE_PREFIX: Final = "passage: "

# The width of the model and of the vec0 column of plan 06-04. A property of the
# artifact, not a knob.
DIMENSIONS: Final = 384

# The verdict. Named like the reasons of extract/errors.py and deliberately not
# added to them: that list is the closed vocabulary of a judged file and it is
# kept in lockstep with the PHP side and with store/repo.py. An embedding that
# could not be produced says nothing about whether the file was indexed, and the
# file was indexed, by the full text pass that ran hours earlier (D-15).
EMBEDDING_UNAVAILABLE: Final = "embedding_unavailable"

# The two artifacts, by name and not by path. Which directory they live in is a
# property of the image and comes from the settings; a hard coded path here
# would make the honest verdict above depend on that path staying true, which is
# the argument extract/ocr.py makes for the engine name.
MODEL_FILE: Final = "model.onnx"
TOKENIZER_FILE: Final = "tokenizer.json"

# The padding marker of the shipped tokenizer, read out of it on 2026-09-05:
# the id behind it is 1. A batch is a rectangle, so the shorter texts in it are
# filled up to the longest, and the attention mask is what keeps that filling
# out of the pooled vector.
PAD_MARKER: Final = "<pad>"
FALLBACK_PAD_MARKER: Final = "[PAD]"

# Two threads, the hardware assumption this phase is written against and the one
# wave 0 produced every throughput number under. Not a setting: the target box
# has two shared vCPU, INDEX_WORKERS is one for the same reason, and a third
# thread would only take turns with itself.
THREADS: Final = 2


@dataclass(frozen=True, slots=True)
class EmbedOutcome:
    """Vectors, or the named state that says why there are none.

    Frozen and built through the two constructors, so that no caller can hand
    out a verdict with vectors attached to it. The vectors are plain floats and
    not a numpy array on purpose: what leaves this module travels into the store
    and into a rank, and both of those are better off not depending on the array
    library of the day.
    """

    vectors: tuple[tuple[float, ...], ...] = ()
    verdict: str | None = None

    @property
    def available(self) -> bool:
        """True when the engine answered, which includes answering nothing."""
        return self.verdict is None

    @classmethod
    def ready(cls, vectors: Sequence[Sequence[float]]) -> EmbedOutcome:
        return cls(vectors=tuple(tuple(float(value) for value in vector) for vector in vectors))

    @classmethod
    def unavailable(cls) -> EmbedOutcome:
        return cls(verdict=EMBEDDING_UNAVAILABLE)


def to_int8(vector: Sequence[float]) -> bytes:
    """The int8 form of one vector, in the width ``store/vectors.sql`` declares.

    The scale lives here and not at the store, because it is a property of the
    model: e5 answers normalised vectors, so every component sits in [-1, 1] and
    127 is the whole factor. Plan 06-03 measured what this second quantisation
    stage costs on a three language test set and found nothing measurable in any
    of six comparisons, which is why it is applied without a switch.

    Clamped rather than trusted: a component of exactly 1.0 would round to 128
    and wrap to -128 in a signed byte, which is a rare input and a spectacular
    answer.
    """
    return bytes((max(-128, min(127, round(value * 127))) & 0xFF) for value in vector)


def open_tokenizer(model_dir: Path) -> Tokenizer:
    """The plain tokenizer, for the chunker, without truncation.

    A second instance next to the one the session is fed with, and the
    separation is not tidiness. ``Tokenizer.enable_truncation`` is a property of
    the object, so one shared instance would carry the 512 token limit of the
    session into ``chunker._first_tokens``, and the 1024 token cap of D-01 would
    silently become 512: the second half of every document would stop existing
    with nothing failing anywhere.
    """
    from tokenizers import Tokenizer as Loader

    return Loader.from_file(str(model_dir / TOKENIZER_FILE))


def _open_encoder(model_dir: Path, *, sequence_len: int) -> Tokenizer:
    """The tokenizer the session is fed with: truncated and padded.

    Truncation is lever 5 and padding is what makes a batch a rectangle. Both
    are set here and never at the call site, so that a batch cannot be built
    with settings the session was not opened for.
    """
    encoder = open_tokenizer(model_dir)
    encoder.enable_truncation(max_length=sequence_len)
    marker = PAD_MARKER
    pad_id = encoder.token_to_id(marker)
    if pad_id is None:  # pragma: no cover - the shipped tokenizer carries the marker
        marker, pad_id = FALLBACK_PAD_MARKER, 0
    encoder.enable_padding(pad_id=pad_id, pad_token=marker)
    return encoder


def _open_session(model_path: Path, *, threads: int) -> Any:
    """The inference session, with the arena switched off.

    ``onnxruntime`` and ``numpy`` are imported inside the function and not at
    the top of the module: together they weigh well over a hundred megabytes,
    and a container whose model never loads should never pay for them.

    ``enable_cpu_mem_arena=False`` is lever 6 of 06-RESEARCH.md 3.6, and the
    trade is stated there: the arena does not hand memory back to the operating
    system, so the activation peak of the second track would stay resident for
    the rest of the container's life. On the 4 GB box this product targets, that
    peak sits beside the OCR peak of 300 to 600 MB, and IDX-08 keeps the two
    apart in time and not in space. A slightly slower allocation is the price,
    and it is paid once per batch rather than once per token.
    """
    import onnxruntime

    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = threads
    options.inter_op_num_threads = 1
    options.enable_cpu_mem_arena = False
    return onnxruntime.InferenceSession(str(model_path), options, providers=["CPUExecutionProvider"])


@dataclass(frozen=True, slots=True)
class _Engine:
    """The two loaded artifacts and what the graph will accept."""

    encoder: Any
    session: Any
    accepted: frozenset[str]
    outputs: tuple[str, ...]


class EmbeddingModel:
    """The wrapper: prefixes in front, caps around, one honest verdict underneath.

    Not a module level singleton. The second track owns one of these for the
    length of its run and the search side may hold another, and a global would
    make the moment of the first load depend on which import ran first.
    """

    def __init__(self, model_dir: Path, *, batch_size: int, sequence_len: int) -> None:
        self._model_dir = model_dir
        self._batch_size = batch_size
        self._sequence_len = sequence_len
        self._engine: _Engine | None = None
        # Three states and not two: never tried, tried and failed, loaded. The
        # middle one is what keeps a missing model from being looked for once
        # per document over tens of thousands of them.
        self._tried = False

    @property
    def loaded(self) -> bool:
        """True once the weights are in memory. False before the first use."""
        return self._engine is not None

    def embed_passages(self, texts: Sequence[str]) -> EmbedOutcome:
        """One vector per document chunk, each one prefixed as a passage."""
        return self._embed(texts, prefix=PASSAGE_PREFIX)

    def embed_query(self, text: str) -> EmbedOutcome:
        """One vector for a search line, prefixed as a query."""
        return self._embed([text], prefix=QUERY_PREFIX)

    def _embed(self, texts: Sequence[str], *, prefix: str) -> EmbedOutcome:
        """The one path both public calls take, so the caps are applied once.

        The prefix is an argument rather than a branch because the ranking test
        of D-05 has to run the very same path with and without it. Everything
        else in here is shared by construction: batching, truncation, pooling
        and normalisation are properties of the model, not of the direction.
        """
        if not texts:
            # No load, and that matters: an empty batch is the normal answer for
            # a document whose text was empty, and it must not be the moment
            # 118 MB of weights arrive.
            return EmbedOutcome.ready(())

        engine = self._load()
        if engine is None:
            return EmbedOutcome.unavailable()

        try:
            vectors: list[list[float]] = []
            for start in range(0, len(texts), self._batch_size):
                window = [f"{prefix}{text}" for text in texts[start : start + self._batch_size]]
                vectors.extend(_run_batch(engine, window))
        except Exception as error:  # a broken graph is a state, see the module head
            _warn(error)
            self._engine = None
            return EmbedOutcome.unavailable()
        return EmbedOutcome.ready(vectors)

    def _load(self) -> _Engine | None:
        """Load once, on first use, and remember a failure as a failure."""
        if self._engine is not None:
            return self._engine
        if self._tried:
            return None
        self._tried = True

        model_path = self._model_dir / MODEL_FILE
        if not model_path.is_file() or not (self._model_dir / TOKENIZER_FILE).is_file():
            # Not an exception and not a path in the log: this is the ordinary
            # state of a container built without the model stage, and the answer
            # to it is a lexical search, not a stack trace.
            LOGGER.warning("no embedding model in the configured directory, the search stays lexical")
            return None

        try:
            encoder = _open_encoder(self._model_dir, sequence_len=self._sequence_len)
            session = _open_session(model_path, threads=THREADS)
            accepted = frozenset(item.name for item in session.get_inputs())
            outputs = tuple(item.name for item in session.get_outputs()[:1])
        except Exception as error:  # see the module head: every failure is one verdict
            _warn(error)
            return None

        self._engine = _Engine(encoder=encoder, session=session, accepted=accepted, outputs=outputs)
        return self._engine


def _warn(error: BaseException) -> None:
    """One warning, one class name, nothing of what the library was reading."""
    LOGGER.warning("the embedding engine failed and the search stays lexical (%s)", type(error).__name__)


def _run_batch(engine: _Engine, texts: list[str]) -> list[list[float]]:
    """One rectangle of tokens through the graph, pooled and normalised.

    Mean pooling over the attention mask and an L2 normalisation afterwards, in
    that order, which is the recipe of the E5 family. The pooling has to respect
    the mask or the padding of the shortest text in the batch would dilute its
    own vector, and the result would depend on which texts happened to travel
    together.
    """
    import numpy

    encodings = engine.encoder.encode_batch(texts)
    ids = numpy.asarray([encoding.ids for encoding in encodings], dtype=numpy.int64)
    mask = numpy.asarray([encoding.attention_mask for encoding in encodings], dtype=numpy.int64)
    feed = {
        "input_ids": ids,
        "attention_mask": mask,
        "token_type_ids": numpy.zeros_like(ids),
    }
    hidden = engine.session.run(
        list(engine.outputs), {name: value for name, value in feed.items() if name in engine.accepted}
    )[0]

    weights = mask[:, :, None].astype(hidden.dtype)
    pooled = (hidden * weights).sum(axis=1) / numpy.clip(weights.sum(axis=1), 1e-9, None)
    lengths = numpy.clip(numpy.linalg.norm(pooled, axis=1, keepdims=True), 1e-12, None)
    return (pooled / lengths).tolist()
