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

**What this does not do.** It does not make the engine thread safe. That belongs
to the object, holds for every caller including the ones that build their own,
and lives in :class:`~findling.embed.model.EmbeddingModel` with the arithmetic
that justifies the lock.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Final

from findling.config import settings
from findling.embed.model import EmbeddingModel, artifacts_present

if TYPE_CHECKING:
    from pathlib import Path

# The directory the wrapper was built for, and the wrapper. One entry, because
# one process reads one model.
_ENGINE: tuple[Path, EmbeddingModel] | None = None

# Re-entrant for the reason the read side lock is: the cost of proving that no
# path below ever takes it twice is higher than the cost of the flag inside it.
_LOCK = threading.RLock()

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
    """
    resolved = settings()
    if not resolved.embed_enabled:
        return ENGINE_DISABLED

    held = _held(resolved.embed_model_dir)
    if held is not None:
        if held.artifacts_absent:
            return ENGINE_MISSING
        if held.load_cooling_down:
            return ENGINE_RETRY_PENDING
        if held.loaded:
            return ENGINE_LOADED

    # Nothing is in memory, so the answer is about what is going to happen, and
    # the artifact question is what decides it: with the two files in place the
    # load is still ahead, without them it never comes. Asked here rather than
    # left at cold, because since plan 07-03 neither half of this container
    # builds the engine before the first row or the first search that needs one.
    # A container without a model would otherwise report cold for its whole
    # life, and cold reads as "the model arrives on first demand", which is the
    # one sentence an admin must not be given in that situation.
    return ENGINE_COLD if artifacts_present(resolved.embed_model_dir) else ENGINE_MISSING
