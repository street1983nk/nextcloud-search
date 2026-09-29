"""The model child of the check: one load of int8 or fp32, measured, bounded and thrown away.

**What it is for.** PRUEF-01 asks, before an admin switches to fp32, whether the
box can carry the weights (D-27-02). The answer is two numbers and a rate: the
anonymous resident memory before the load and after the first batch, and how
many passages a second the weights embed. The rate also feeds the reindex
estimate of D-27-18.

**Why a child of its own and never the engine of this process.** The main
process holds exactly one engine, and the one_load gate
(:mod:`findling.tools.one_load`) holds it to that: never two engines at once. A
probe through the engine swap of :mod:`findling.embed.engine` would load fp32 next to the int8 the search is
using, or worse, answer searches with fp32 weights the admin has not chosen
yet. A spawn child loads, measures and ends, and the counters of
:mod:`findling.embed.model` in this process never move.

**The hardening is the sandbox's, imported and not copied.** Before anything
heavy is imported the child becomes a session leader (so the deadline kill
takes the whole group), lowers its nice level, volunteers as the first victim
of the OOM killer (``oom_score_adj`` 1000) and drops the AppAPI credentials it
has no use for. The one part it leaves out is the ``RLIMIT_AS`` cap of the
extraction children: onnxruntime reserves far more virtual address space than
it touches, so a cap sized for resident memory would fail the load itself
(27-RESEARCH.md, assumption A2). Memory is bounded instead by the admission of
the orchestrator (``MODEL_PROBE_CHILD_BYTES`` plus the reserve) and by the OOM
score, which makes this child the one that goes.

**The method is the one of docs/measurements/2026-09-fp32-speicher, sections 3
and 4.** ``RssAnon`` from ``/proc/self/status``, because the weights of a
session live in anonymous memory and file backed library pages would blur the
comparison. The first reading is taken after onnxruntime, numpy and the
tokenizer are loaded, so the delta shows weights and activations only. The
session is opened by the product's own ``_open_session`` and the batch runs
through the product's own encoding and graph path, eight fixed passages that
are all truncated at sequence length 512, the worst case for the activations.

**Four ways out, and the parent tells them apart.** ``ok`` and ``no_memory``
and ``failed`` are what the child says. ``timeout`` is the parent's own kill at
the deadline; ``killed`` is a death by SIGKILL the parent did not send, which on
a tight box is the kernel. No exception text crosses the pipe, and nothing is
logged but closed codes and class names: the passages are neutral text, but a
library message could quote a path.

**Import hygiene.** Nothing at module level pulls in onnxruntime, numpy,
tokenizers or fastembed; the parent imports this module and must stay light.
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys
import time
from dataclasses import dataclass
from multiprocessing.context import SpawnProcess
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from findling.extract.errors import KILLED_EXIT_CODE
from findling.extract.sandbox import (
    SANDBOX_NICE,
    SPAWN_CONTEXT,
    PipeEnd,
    _kill_child_tree,
    _lower_own_standing,
    _shed_secrets,
)

if TYPE_CHECKING:
    from collections.abc import Callable

LOGGER = logging.getLogger("findling.embed.model_probe")

MEASURE_OK: Final = "ok"
MEASURE_TIMEOUT: Final = "timeout"
MEASURE_KILLED: Final = "killed"
MEASURE_FAILED: Final = "failed"
MEASURE_NO_MEMORY: Final = "no_memory"
MEASURE_OUTCOMES: Final = frozenset({MEASURE_OK, MEASURE_TIMEOUT, MEASURE_KILLED, MEASURE_FAILED, MEASURE_NO_MEMORY})

# What a child may say about itself. timeout and killed are the parent's words
# and never the child's, so an answer carrying them is malformed.
_CHILD_OUTCOMES: Final = frozenset({MEASURE_OK, MEASURE_FAILED, MEASURE_NO_MEMORY})

Precision = Literal["int8", "fp32"]
_PRECISIONS: Final = frozenset({"int8", "fp32"})

# The fixed batch of the measurement method, section 3.
PROBE_BATCH: Final = 8
PROBE_SEQUENCE_LEN: Final = 512

_SENTENCES: Final = (
    "The quarterly report lists every invoice that was paid after its due date. ",
    "A tenant may terminate the lease with three months of notice in writing. ",
    "The meeting minutes record who attended and which decisions were taken. ",
    "Scanned receipts are kept for ten years to satisfy the tax authority. ",
    "The maintenance contract covers the heating system and the water pipes. ",
    "Every employee receives the updated travel policy by the end of the month. ",
    "The project plan names the milestones, the owners and the open risks. ",
    "Insurance claims need a copy of the police report and a list of damages. ",
)
# Long enough that every passage is truncated at the sequence length.
PASSAGES: Final = tuple(sentence * 60 for sentence in _SENTENCES)

# How long a finished or killed child is given to leave, as in the sandbox.
_JOIN_GRACE_SECONDS: Final = 5.0

_STATUS_FILE: Final = Path("/proc/self/status")

# The rehearsals a test can ask for instead of a load. Reached only through
# _measure and never through measure, so no caller of the product can pick one.
_REHEARSALS: Final = frozenset({"sleep", "no_memory", "fail"})


@dataclass(frozen=True, slots=True)
class ModelMeasure:
    """What one probe child reported, or the parent's word for why it did not.

    Memory in bytes of ``RssAnon``, the rate in milli passages per second. On
    every outcome but ``ok`` the three numbers are nought.
    """

    outcome: str
    rss_before: int
    rss_after: int
    rate_milli: int

    @property
    def delta(self) -> int:
        """What the load and the first batch added to the anonymous memory."""
        return self.rss_after - self.rss_before


def _nothing(outcome: str) -> ModelMeasure:
    return ModelMeasure(outcome, 0, 0, 0)


def _is_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _read_answer(answer: object) -> ModelMeasure:
    """Judge what came over the pipe; anything that is not a clean answer is failed."""
    if not isinstance(answer, tuple) or len(answer) != 4:
        return _nothing(MEASURE_FAILED)
    outcome, before, after, rate = answer
    if outcome not in _CHILD_OUTCOMES or not all(_is_count(value) for value in (before, after, rate)):
        return _nothing(MEASURE_FAILED)
    if outcome != MEASURE_OK:
        return _nothing(outcome)
    if after < before or rate <= 0:
        return _nothing(MEASURE_FAILED)
    return ModelMeasure(outcome, before, after, rate)


def _rate_milli(batch_ms: int) -> int:
    """Milli passages per second for one batch of eight, never nought and never a division by it."""
    return max(1, PROBE_BATCH * 1000 * 1000 // max(1, batch_ms))


def _rss_anon_bytes() -> int:
    """RssAnon of this process in bytes, or -1 where there is no /proc to read it from."""
    try:
        for line in _STATUS_FILE.read_text(encoding="ascii").splitlines():
            if line.startswith("RssAnon:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        return -1
    return -1


def _weights_of(precision: str, models_dir: Path, embed_model_dir: Path) -> Path:
    """The weights a precision names: the int8 of the image, or the fp32 on the volume."""
    from findling.embed.model import MODEL_FILE
    from findling.embed.weights import fp32_weights_path

    if precision == "fp32":
        return fp32_weights_path(models_dir)
    return embed_model_dir / MODEL_FILE


def _rehearse(rehearsal: str | None) -> None:
    """Stand in for a model that hangs, runs out of memory or throws, on a test's request."""
    if rehearsal is None:
        return
    if rehearsal == "sleep":
        time.sleep(3600)
    elif rehearsal == "no_memory":
        raise MemoryError
    raise RuntimeError("rehearsed failure")


def _load_and_measure(weights: Path, embed_model_dir: Path) -> tuple[str, int, int, int]:
    """One load, one batch, three numbers. Runs inside the hardened child only."""
    import numpy  # noqa: F401 - loaded before the first reading, see the module head

    from findling.embed.model import (
        PASSAGE_PREFIX,
        THREADS,
        _encode_batch,
        _Engine,
        _open_encoder,
        _open_session,
        _run_encoded,
    )

    if not weights.is_file():
        return (MEASURE_FAILED, 0, 0, 0)
    encoder = _open_encoder(embed_model_dir, sequence_len=PROBE_SEQUENCE_LEN)
    before = _rss_anon_bytes()
    session = _open_session(weights, threads=THREADS)
    engine = _Engine(
        encoder=encoder,
        session=session,
        accepted=frozenset(item.name for item in session.get_inputs()),
        outputs=tuple(item.name for item in session.get_outputs()[:1]),
    )
    started = time.perf_counter()
    _run_encoded(engine, _encode_batch(engine, [f"{PASSAGE_PREFIX}{text}" for text in PASSAGES[:PROBE_BATCH]]))
    batch_ms = round((time.perf_counter() - started) * 1000)
    after = _rss_anon_bytes()
    if before < 0 or after < 0:
        # No /proc, no measurement: a load without its numbers is no answer.
        return (MEASURE_FAILED, 0, 0, 0)
    return (MEASURE_OK, before, after, _rate_milli(batch_ms))


def _child_main(pipe: PipeEnd, weights: Path, embed_model_dir: Path, rehearsal: str | None) -> None:
    """The child: harden, then load and measure once, answer, end."""
    if sys.platform != "win32":
        # Its own session first, so the deadline kill reaches the whole group.
        os.setsid()
        os.nice(SANDBOX_NICE)
        _lower_own_standing()
    _shed_secrets()
    try:
        _rehearse(rehearsal)
        # Only now the heavy libraries, inside the hardened process.
        import onnxruntime  # noqa: F401 - the first heavy import sits after the hardening

        answer = _load_and_measure(weights, embed_model_dir)
    except MemoryError:
        answer = (MEASURE_NO_MEMORY, 0, 0, 0)
    except Exception:  # every other failure is one closed code, no text crosses
        answer = (MEASURE_FAILED, 0, 0, 0)
    with contextlib.suppress(BrokenPipeError, OSError):
        pipe.send(answer)
    pipe.close()


def measure(precision: Precision, models_dir: Path, *, timeout_seconds: float) -> ModelMeasure:
    """Load the weights of ``precision`` in a hardened child and report what it cost.

    Blocking. The orchestrator calls it in a thread of its own and never in the
    default executor, where a probe of up to ``timeout_seconds`` would hold a
    worker the searches share. The fp32 weights must have passed their digest
    before this is called (``fp32_verified``); this function loads, it does not
    judge files.
    """
    return _measure(precision, models_dir, timeout_seconds=timeout_seconds)


def _measure(
    precision: str,
    models_dir: Path,
    *,
    timeout_seconds: float,
    embed_model_dir: Path | None = None,
    rehearsal: str | None = None,
    on_start: Callable[[int], None] | None = None,
) -> ModelMeasure:
    """:func:`measure` with the seams the tests need: the tokenizer directory, a rehearsal, the child pid."""
    if precision not in _PRECISIONS:
        raise ValueError("unknown precision")
    if rehearsal is not None and rehearsal not in _REHEARSALS:
        raise ValueError("unknown rehearsal")
    if embed_model_dir is None:
        from findling import config

        embed_model_dir = config.settings().embed_model_dir
    weights = _weights_of(precision, models_dir, embed_model_dir)

    receiver, sender = SPAWN_CONTEXT.Pipe(duplex=False)
    process = SPAWN_CONTEXT.Process(
        target=_child_main,
        args=(sender, weights, embed_model_dir, rehearsal),
        daemon=True,
    )
    process.start()
    # Without this close a dead child would never deliver an end of file.
    sender.close()
    if on_start is not None and process.pid is not None:
        on_start(process.pid)
    try:
        result = _await(process, receiver, timeout_seconds)
    finally:
        receiver.close()
        if process.is_alive():
            _kill_child_tree(process)
        process.join(_JOIN_GRACE_SECONDS)
        process.close()
    LOGGER.info("model probe ended: %s", result.outcome)
    return result


def _await(process: SpawnProcess, receiver: PipeEnd, timeout_seconds: float) -> ModelMeasure:
    """Wait for the answer until the deadline and name the way the child ended."""
    if not receiver.poll(timeout_seconds):
        # Over the deadline: the parent's own kill, of the whole group.
        _kill_child_tree(process)
        process.join(_JOIN_GRACE_SECONDS)
        return _nothing(MEASURE_TIMEOUT)
    try:
        answer = receiver.recv()
    except (EOFError, OSError):
        # The child ended without an answer. SIGKILL is the one death nothing
        # in here sends at this point, so it is the kernel's.
        process.join(_JOIN_GRACE_SECONDS)
        return _nothing(MEASURE_KILLED if process.exitcode == KILLED_EXIT_CODE else MEASURE_FAILED)
    return _read_answer(answer)
