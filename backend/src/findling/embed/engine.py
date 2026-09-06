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

**What this does not do.** It does not make the engine thread safe. That belongs
to the object, holds for every caller including the ones that build their own,
and lives in :class:`~findling.embed.model.EmbeddingModel` with the arithmetic
that justifies the lock.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from findling.config import settings
from findling.embed.model import EmbeddingModel

if TYPE_CHECKING:
    from pathlib import Path

# The directory the wrapper was built for, and the wrapper. One entry, because
# one process reads one model.
_ENGINE: tuple[Path, EmbeddingModel] | None = None

# Re-entrant for the reason the read side lock is: the cost of proving that no
# path below ever takes it twice is higher than the cost of the flag inside it.
_LOCK = threading.RLock()


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
