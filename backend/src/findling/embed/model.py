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
import threading
import time
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

# How long an open that threw is left alone before it is tried again.
#
# Not a setting, for the reason THREADS is none: it is a property of the two
# failures it stands between, and neither of them is a decision an operator
# makes. A directory without the artifacts is a state of the installation and is
# remembered for ever; an open that threw is a state of the moment, and the one
# that really happens on the target box is a MemoryError while 118 MB of weights
# arrive under a hard 2 GB limit (the load run of 2026-09-05 measured
# memory.events max at 2796). Until the audit of plan 06.1-17 both ended in the
# same permanent "no", and with the shared engine of plan 06.1-02 that cost the
# whole container its semantics until somebody restarted it, which is exactly
# the warning sign of pitfall 2 of the phase research.
#
# Five minutes is the trade between the two costs. Retrying at once would read a
# broken graph once per document over tens of thousands of them, which is the
# reason the permanent flag existed in the first place; at five minutes a
# genuinely broken graph is opened twelve times an hour and an instance that
# merely ran out of air for a moment is whole again before anybody has finished
# reading the log line.
LOAD_RETRY_SECONDS: Final = 300.0

# How often the artifacts were really read in this process. The counter exists
# for the same reason ``index/analyzer.build_count()`` does: from the outside a
# cache hit and a cheap second load look identical, and the whole claim of plan
# 06.1-02 is that there is exactly one load per process. A counter proves that
# without timing anything and without measuring a byte, which on a shared runner
# is the difference between a test and a random number generator.
_LOAD_COUNT = 0


def load_count() -> int:
    """Return how often this process has read tokenizer and weights."""
    return _LOAD_COUNT


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


def artifacts_present(model_dir: Path) -> bool:
    """The same question from outside this module, and the only way to ask it.

    Two stats and nothing else, which is what makes it usable where the answer
    has to be cheap. The embedding track of the poller asks it before it
    promises a row that it can be embedded: since plan 07-03 the tokenizer and
    the splitter are built at the first row rather than at the first pass, so
    the promise of ``_embed_ready`` can no longer be a side effect of having
    built them, and a promise made on a directory without artifacts would send
    rows to a spur that cannot run.

    A delegation rather than a rename, so that the two suites which count this
    question through :func:`_artifacts_present` keep counting the same calls.
    """
    return _artifacts_present(model_dir)


def _artifacts_present(model_dir: Path) -> bool:
    """True when both files a load needs are in the directory.

    Its own function because it is the seam the permanent half of the failure
    distinction hangs on: a directory without them is a property of the
    installation and is looked at once, and a test can count that from here
    rather than from the log, which only says how often it was mentioned.
    """
    return (model_dir / MODEL_FILE).is_file() and (model_dir / TOKENIZER_FILE).is_file()


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

    Still not a module level singleton, and the reason has not changed: a global
    in here would make the moment of the first load depend on which import ran
    first. Which instance the two callers of this process use is decided one
    layer up, in :mod:`findling.embed.engine`, where it can be decided once and
    on purpose.

    **Three failures, and no two of them are the same failure.** A directory
    without ``model.onnx`` and ``tokenizer.json`` is a property of the
    installation: it is the ordinary state of a container built without the
    model stage, it stays true for the whole life of the process, and looking
    again would be a pair of stat calls per document over tens of thousands of
    them. That one is remembered for ever. A batch that threw is not a property
    of anything, so it keeps the engine and the next call runs again. An open
    that threw is neither: the files are there, nothing was computed, and the
    failure that really happens on the target box is a MemoryError while 118 MB
    of weights arrive under a hard 2 GB limit. It is remembered with a timestamp
    and tried again after :data:`LOAD_RETRY_SECONDS`.

    Until plan 06.1-02 the first two ended in the same permanently remembered
    "no", which cost one side of the container its semantics; the third went on
    doing it until the audit of plan 06.1-17. With the single shared instance
    since 06.1-02 either of them costs **both** halves, and the symptom is a
    container that suddenly answers lexically after hours of service with
    nothing having changed (06.1-RESEARCH.md, pitfall 2).
    """

    def __init__(self, model_dir: Path, *, batch_size: int, sequence_len: int) -> None:
        self._model_dir = model_dir
        self._batch_size = batch_size
        self._sequence_len = sequence_len
        self._engine: _Engine | None = None
        # The permanent half of the distinction above, and since the audit of
        # plan 06.1-17 it is only the half it says: the artifacts are not in this
        # directory. That is a state of the installation and does not change
        # while the process runs. An open that threw used to land in here as
        # well, which made a moment permanent; it has its own field below.
        self._absent = False
        # The temporary half of the load path: when an open last threw, on the
        # monotonic clock. None means never, or not since the last success.
        self._load_failed_at: float | None = None
        # One warning for the temporary half, then silence at debug level. A
        # thrown run is retried by design, and the second track walks tens of
        # thousands of documents, so a warning per row would be the log flood
        # the load path avoids with the flag above.
        self._run_failure_warned = False
        # One lock, around the load and around the tokenizer, and around
        # nothing else.
        #
        # The load path needs it whatever else is true: without it two threads
        # of the same pool enter _load at once, both build a session, and the
        # doubled load that plan 06.1-02 removes comes straight back. That is
        # the argument api/resources.py makes for its own lock.
        #
        # The tokenizer needs it because the tokenizers maintainer will not
        # promise thread safety ("if the threads just don't share the tokenizer
        # its better", huggingface/tokenizers#1726).
        #
        # **The graph does not, and until the audit of plan 06.1-17 it was inside
        # anyway.** The onnxruntime maintainer promises Run() on one session from
        # several threads without any external synchronisation, and this build
        # runs the CPU provider alone, which is the case that promise covers. The
        # old shape held the lock over the whole call, so a search waited for
        # every batch of a document of the second track and not for one:
        # measured 0.561 s at the default token cap and 2.562 s at the ceiling of
        # its range, against a budget of 2500 ms for a whole search
        # (06.1-AUDIT-PERF.md M1). The tokenizer is one line of a batch, so
        # holding the lock for that line alone keeps the promise nobody made and
        # gives back the rest.
        #
        # Re entrant because it is cheaper than proving that no path below ever
        # takes it twice.
        self._lock = threading.RLock()

    @property
    def loaded(self) -> bool:
        """True once the weights are in memory. False before the first use."""
        return self._engine is not None

    @property
    def artifacts_absent(self) -> bool:
        """True once the load path found the directory without the artifacts.

        The permanent half of the three answers of :meth:`_load`, made readable
        without asking for a vector first. Nothing is looked at here: the flag
        was set when the load path looked, and looking again would be the pair
        of stat calls per question that the flag exists to avoid.

        Read by :func:`findling.embed.engine.engine_state` for the admin page,
        which needs the difference between "there is no model in this image" and
        "nothing has been embedded yet". Both look like nought documents.
        """
        return self._absent

    @property
    def load_cooling_down(self) -> bool:
        """True while an open that threw is still inside its cooldown.

        The temporary half of the same three answers, and the reason it is a
        property rather than a field: the state is not the timestamp, it is the
        timestamp measured against :data:`LOAD_RETRY_SECONDS`, and that
        comparison has one home. :meth:`_load` asks the same question through
        this property, so the two can never drift into two spellings of one
        rule.

        Reading it has no side effect. The clock is read, nothing else.
        """
        stamp = self._load_failed_at
        return stamp is not None and time.monotonic() - stamp < LOAD_RETRY_SECONDS

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

        # The load under the lock, for the reason stated beside it in __init__.
        with self._lock:
            engine = self._load()
        if engine is None:
            return EmbedOutcome.unavailable()

        try:
            vectors: list[list[float]] = []
            for start in range(0, len(texts), self._batch_size):
                window = [f"{prefix}{text}" for text in texts[start : start + self._batch_size]]
                # The tokenizer inside, the graph outside, and the batch is the
                # unit of both. Whatever else waits here waits for one encoding
                # and never for a whole document.
                with self._lock:
                    encoded = _encode_batch(engine, window)
                vectors.extend(_run_encoded(engine, encoded))
        except Exception as error:  # a thrown batch is a state, see the class head
            # The engine stays. Dropping it would pay 118 MB of weights again
            # for a failure that is usually about the one text that went in,
            # and it was that drop together with the permanent flag that made
            # a single bad batch outlive the batch.
            self._warn_run(error)
            return EmbedOutcome.unavailable()
        return EmbedOutcome.ready(vectors)

    def _warn_run(self, error: BaseException) -> None:
        """Say once that a run failed, then keep saying it at debug level."""
        if self._run_failure_warned:
            LOGGER.debug("the embedding engine failed on a batch again (%s)", type(error).__name__)
            return
        self._run_failure_warned = True
        _warn(error)

    def _load(self) -> _Engine | None:
        """Load once, on first use, and tell the two failures apart.

        Called under the lock, never on its own, so what is guarded is not only
        the assignment below but the whole window between the check and it.

        Two ways to say no, and they are not the same no. A directory without
        the artifacts is answered once and for ever. An open that threw is
        answered until :data:`LOAD_RETRY_SECONDS` have passed and then tried
        again, because the failure that really happens on the target box is a
        moment and not a property (see the constant).
        """
        global _LOAD_COUNT

        if self._engine is not None:
            return self._engine
        if self._absent:
            return None
        if self.load_cooling_down:
            return None

        model_path = self._model_dir / MODEL_FILE
        if not _artifacts_present(self._model_dir):
            # Not an exception and not a path in the log: this is the ordinary
            # state of a container built without the model stage, and the answer
            # to it is a lexical search, not a stack trace.
            self._absent = True
            LOGGER.warning("no embedding model in the configured directory, the search stays lexical")
            return None

        try:
            encoder = _open_encoder(self._model_dir, sequence_len=self._sequence_len)
            session = _open_session(model_path, threads=THREADS)
            accepted = frozenset(item.name for item in session.get_inputs())
            outputs = tuple(item.name for item in session.get_outputs()[:1])
        except Exception as error:  # see the module head: every failure is one verdict
            # Neither of the two other answers. Not an absent model, because the
            # files are there; not a thrown batch either, because nothing was
            # computed. It is remembered with a timestamp and retried after the
            # cooldown: a broken graph is then opened twelve times an hour
            # instead of once per document, and a container that ran out of air
            # for a moment gets its semantics back without a restart
            # (06.1-AUDIT-BUGS.md H1).
            self._load_failed_at = time.monotonic()
            _warn(error)
            return None

        self._load_failed_at = None
        _LOAD_COUNT += 1
        self._engine = _Engine(encoder=encoder, session=session, accepted=accepted, outputs=outputs)
        return self._engine


def _warn(error: BaseException) -> None:
    """One warning, one class name, nothing of what the library was reading."""
    LOGGER.warning("the embedding engine failed and the search stays lexical (%s)", type(error).__name__)


def _encode_batch(engine: _Engine, texts: list[str]) -> list[Any]:
    """The one line of a batch that touches the tokenizer.

    Its own function so that the lock can be exactly this long. Everything
    around it is numpy and onnxruntime, and for the second of those the
    maintainer promises what the first of these does not (see the lock in
    ``EmbeddingModel.__init__``).
    """
    return engine.encoder.encode_batch(texts)


def _run_encoded(engine: _Engine, encodings: list[Any]) -> list[list[float]]:
    """One rectangle of tokens through the graph, pooled and normalised.

    Mean pooling over the attention mask and an L2 normalisation afterwards, in
    that order, which is the recipe of the E5 family. The pooling has to respect
    the mask or the padding of the shortest text in the batch would dilute its
    own vector, and the result would depend on which texts happened to travel
    together.

    Runs outside the lock. ``Run()`` on one session out of several threads is
    safe without external synchronisation by the promise of the onnxruntime
    maintainer, and this build uses the CPU provider alone, which is the case
    that promise covers.
    """
    import numpy

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
