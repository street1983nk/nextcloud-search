"""The one embedding engine of this process, for the search side and the track.

Both halves of the container embed. The second track turns document chunks into
vectors and every semantic search turns the query into one, and until plan
06.1-02 each of them built its own :class:`~findling.embed.model.EmbeddingModel`.
That is two tokenizers and two onnxruntime sessions in one process. The load run
of 2026-09-05 measured what it costs: the first search with a semantic part
added 276 MB that stayed resident for the rest of the container's life, on a box
with 210 MB of headroom against a hard 2 GB limit, and it is the reason
``memory.events max`` stood at 2796 while every damage counter stayed at zero.

**Why the holder is here and not on either side that uses it.** Not in
``embed/model.py``, because the class comment there argues, correctly, that a
global beside the class would make the moment of the first load depend on which
import ran first; the decision belongs one layer up, where it is a decision.
Not in ``api/resources.py``, although the shape below is copied from
``query_model`` there: that module is the reading half of the container, its own
head says "Nothing here decides anything", and the worker would end up importing
from the API to get its engine. The dependency direction is the point.
``worker/poller.py`` imports from ``embed/``; nothing in ``worker/`` imports from
``findling.api``.

**Why a cache at all, and why keyed on the directory.** Both answers come from
``api/resources.py`` and both still hold. Constructing the wrapper loads
nothing, so this may be called long before it is known whether there is a model
at all, but the wrapper remembers an absent model, so a container without one
looks for it once instead of once per search. And it is keyed on the model
directory because a process has one of those while a test suite has one per
test: without the key the second test would be handed the remembered refusal of
the first. Absence itself is never cached here, only the wrapper is.

**And the question about the engine, next to the holder that answers it.**
:func:`engine_state` says which of five states this process is in, for the
admin page of plan 07-04. It lives here because the holder is what it reads,
and it is the one function in this module that must build nothing: an admin
page polls, so a question that loaded the engine on the way would be the
loading trigger of a container nobody is searching on.

**The one thing this module is told rather than reads.** The second track needs
a tokenizer and a splitter next to the weights, it builds them at the first row
that needs one, and that build can throw for the same reason a load can: 544,3
MB arriving under a hard 2 GB limit. The holder knows nothing of it, because the
build never gets as far as asking for the engine, so before this the page said
"cold" for a track that was lying dead in its cooldown (bug audit MEDIUM-2 of
plan 07-05). :func:`note_cutter_failure` is how the poller says it, and the
stamp it hands over is its own, so the two halves cannot drift into two clocks.
It is a fact about this process, like the holder itself, and it is remembered
in the same place for the same reason.

**What this does not do.** It does not make the engine thread safe. That belongs
to the object, holds for every caller including the ones that build their own,
and lives in :class:`~findling.embed.model.EmbeddingModel` with the arithmetic
that justifies the lock.
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Final

from findling.config import settings
from findling.embed.model import LOAD_RETRY_SECONDS, EmbeddingModel, artifacts_present

if TYPE_CHECKING:
    from pathlib import Path

# The directory the wrapper was built for, and the wrapper. One entry, because
# one process reads one model.
_ENGINE: tuple[Path, EmbeddingModel] | None = None

# Re-entrant for the reason the read side lock is: the cost of proving that no
# path below ever takes it twice is higher than the cost of the flag inside it.
_LOCK = threading.RLock()

# When the second track last failed to build its cutter, on the monotonic clock,
# and None when it never did or not since the last success. Written by the
# poller through :func:`note_cutter_failure` and read by :func:`engine_state`
# alone. A plain module global next to the holder because it describes the same
# thing the holder does, this process, and because the poller keeps its own copy
# as the field its own gates read: this one is the diagnosis and never the gate.
_CUTTER_FAILED_AT: float | None = None

# The directory the artifact question was answered "no" for, once, in this
# process. The same remembered refusal as ``EmbeddingModel._absent`` and for the
# same reason (perf audit PERF-F2): a directory without the two files is a
# property of the installation and not of the moment, the admin page polls every
# few seconds for as long as it is open, and an empty holder is exactly the
# state in which nobody else answers that question. Only the "no" is
# remembered. A "yes" stays a question, because a model that is taken out of a
# running container has to become visible, and because the two stats it costs
# are paid on the state that resolves itself.
_ABSENT: Path | None = None

# The closed set of answers :func:`engine_state` gives, as named constants in
# the shape of the notes of ``api/status.py``: every one of them names a state
# of this container and none of them names a place on disk (T-07-01). The words
# themselves travel to the other half and are the protocol, not a label. What an
# admin reads is decided over there, in the admin's own language.
ENGINE_LOADED: Final = "loaded"
ENGINE_COLD: Final = "cold"
ENGINE_DISABLED: Final = "disabled"
ENGINE_MISSING: Final = "missing"
ENGINE_RETRY_PENDING: Final = "waiting_for_retry"

# The set as a whole, so that the other half can be held against it and so that
# a sixth answer cannot arrive without this line seeing it.
ENGINE_STATES: Final = frozenset({ENGINE_LOADED, ENGINE_COLD, ENGINE_DISABLED, ENGINE_MISSING, ENGINE_RETRY_PENDING})


def shared_model() -> EmbeddingModel:
    """Return the embedding engine of this process, building it on first use.

    Both callers go through here: ``api/resources.py::query_model`` for the
    search side and ``worker/poller.py::_wire_the_second_track`` for the second
    track. Two calls answer the same object as long as the settings name the
    same model directory, which is what makes tokenizer and weights arrive once.

    Nothing is loaded by this call. The artifacts are read on the first text
    that reaches the engine, and whether there are any is answered there with
    the ``embedding_unavailable`` verdict rather than with an exception.
    """
    global _ENGINE

    resolved = settings()
    with _LOCK:
        if _ENGINE is not None and _ENGINE[0] == resolved.embed_model_dir:
            return _ENGINE[1]
        model = EmbeddingModel(
            resolved.embed_model_dir,
            batch_size=resolved.embed_batch_size,
            sequence_len=resolved.embed_sequence_len,
        )
        _ENGINE = (resolved.embed_model_dir, model)
        return model


def note_cutter_failure(stamp: float | None) -> None:
    """The second track says when its cutter build last threw, or that it did not.

    One writer, one reader, one clock. The stamp is the poller's own
    ``_cutter_failed_at``, handed over rather than taken here, so the cooldown
    the track runs on and the state the page shows can never be two different
    moments. None is the whole of the other message: the build worked, or the
    track never got to one.

    Called from ``worker/poller.py`` and from nowhere else. The dependency
    direction of this module holds: ``worker/`` imports from ``embed/``, and
    nothing here knows that a poller exists.
    """
    global _CUTTER_FAILED_AT

    global _ABSENT

    with _LOCK:
        _CUTTER_FAILED_AT = stamp
        if stamp is None:
            # A build that worked read both artifacts, so a remembered "no"
            # about that directory is out of date by the time this arrives. The
            # two facts are kept consistent here rather than by a comment,
            # because they come from the same directory and would otherwise
            # contradict each other on the page.
            _ABSENT = None


def _cutter_cooling_down() -> bool:
    """True while the failed cutter build of the second track is inside its cooldown.

    The same comparison as
    :attr:`~findling.embed.model.EmbeddingModel.load_cooling_down`, against the
    same constant, because it is the same failure one layer up. Reading it has
    no side effect: the clock is read, nothing else.
    """
    stamp = _CUTTER_FAILED_AT
    return stamp is not None and time.monotonic() - stamp < LOAD_RETRY_SECONDS


def reset() -> None:
    """Forget the engine of this process, for a test suite and for one tool.

    Named as what it is and used by nobody in the container: the holder is a
    property of a process, and a running container has exactly one interest in
    it, which is that it stays. Two callers have the opposite interest, and both
    of them run outside a container.

    ``tools/one_load.py`` is the one that needs it (bug audit LOW-7 of plan
    07-05). Its gate asserts that one process pays for exactly one load, and it
    measures that by driving the search side and the second track for real. A
    second call of ``measure()`` in the same process used to find the engine of
    the first one in the holder, take the cache hit, count nought loads and
    report "green for nothing" about a tool that was working perfectly.

    A test suite is the other. It is one process with one model directory per
    case, so the holder is keyed away from most of the trouble, but a case that
    reuses a directory would inherit whatever the case before it loaded.

    **What it does not reset is the load counter.** Every caller of
    :func:`~findling.embed.model.load_count` reads it as a difference against a
    baseline it took itself, so nothing needs it zeroed, and a counter that can
    be zeroed is one a gate could zero itself green with. The evidence of "one
    load per process" stays monotonic for the life of the process.
    """
    global _ENGINE

    with _LOCK:
        _ENGINE = None
        # The notice of the second track goes with it, and the remembered
        # refusal about the artifacts with that: all three say something about
        # this process, and this is the call that says the process starts over.
        note_cutter_failure(None)


def _artifacts_absent(model_dir: Path) -> bool:
    """True when the two files are not in that directory, asked at most once.

    The seam of perf audit PERF-F2, in the shape ``EmbeddingModel._load`` uses
    for the same question: the "no" is remembered for the life of the process
    and the "yes" is not. What makes the asymmetry right is what each answer
    describes. A directory without the artifacts is a container built without
    the model stage, which is the ordinary case outside the shipping image and
    stays true until somebody deploys another image; asking again is a pair of
    stats per poll of an admin page, for ever, for an answer that cannot change.
    A directory with them may lose them, and that has to become visible.
    """
    global _ABSENT

    with _LOCK:
        if model_dir == _ABSENT:
            return True
        if artifacts_present(model_dir):
            return False
        _ABSENT = model_dir
        return True


def _held(model_dir: Path) -> EmbeddingModel | None:
    """The engine of this process if there is one, and never a new one.

    The holder is read under the same lock :func:`shared_model` writes it
    under, and the one difference to that function is the whole point of this
    one: an empty holder is answered with None and not filled.
    """
    with _LOCK:
        if _ENGINE is not None and _ENGINE[0] == model_dir:
            return _ENGINE[1]
        return None


def engine_state() -> str:
    """Which of five states the embedding engine of this process is in.

    For the admin page, which shows how many documents carry a vector and can
    say nothing else about the semantic half. Nought documents is the same
    figure for a model that is not in the image, for a load that threw and is
    still inside its cooldown, and for a track that has not got there yet, and
    the three ask completely different things of an admin: rebuild the image,
    wait five minutes, or do nothing at all.

    **Nothing is built and nothing is loaded here.** An empty holder is
    answered with a state and not with an instance, and no path below reads an
    artifact. That is not tidiness: the page polls every few seconds while it is
    open, so a question that loaded the engine would be the loading trigger of a
    container nobody is searching on, and it would report the 118 MB it had just
    spent itself (T-07-04).

    **The order of the answers is fixed, and it is not the order of the fields
    they come from.** Switched off outranks everything, because a container
    whose semantic half is off would otherwise be reported cold and look like
    one that is about to begin. Then the missing model, the one state that does
    not resolve itself. Then the cooldown, then the loaded engine, and cold
    last, as the state that is left when nothing else is true.

    **The cooldown has two sources and one answer** (bug audit MEDIUM-2 of plan
    07-05). A load of the weights that threw is one of them and the holder knows
    it. A cutter build of the second track that threw is the other, and the
    holder cannot know it: that build fails before it ever asks for the engine,
    so the holder stays empty and the page used to say "cold", which reads as
    "the model arrives on first demand" for a track that is lying dead for five
    minutes. Both are the same sentence to an admin, wait and look again, so
    both give the same word and no sixth one is invented for it.
    """
    resolved = settings()
    if not resolved.embed_enabled:
        return ENGINE_DISABLED

    held = _held(resolved.embed_model_dir)

    # The missing model, asked of whichever source can answer it. With an
    # instance in the holder that is the refusal its load path remembered for
    # ever; without one it is the pair of stats, and it is asked here rather
    # than left at cold because since plan 07-03 neither half of this container
    # builds the engine before the first row or the first search that needs one.
    # A container without a model would otherwise report cold for its whole
    # life, and cold reads as "the model arrives on first demand", which is the
    # one sentence an admin must not be given in that situation.
    absent = held.artifacts_absent if held is not None else _artifacts_absent(resolved.embed_model_dir)
    if absent:
        return ENGINE_MISSING
    if (held is not None and held.load_cooling_down) or _cutter_cooling_down():
        return ENGINE_RETRY_PENDING
    if held is not None and held.loaded:
        return ENGINE_LOADED

    # What is left when nothing else is true: the artifacts are there, nothing
    # threw, and nothing has been read yet.
    return ENGINE_COLD
