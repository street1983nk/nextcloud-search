"""Where the embedding runs right now: in the indexing loop or beside it (PAR-01).

Two modes form a closed set. ``inline`` is today's container: the indexing loop
claims every kind of row and embeds the embed rows itself, after the OCR of the
same pass and never beside it (IDX-08). ``parallel`` says the embed runner of
:mod:`findling.worker.embedding` claims the embed rows on a lane of its own, and
the indexing loop asks for the index lane only.

Why the runner parks is a closed set as well, so that the status page (plan
25-12) can say it without inventing words: the effective level is economy, the
companion never echoed the lane filter, the memory condition of PAR-04 is not
met, or the last round of the runner failed (a queue that did not answer, or an
unexpected exception) and the lane goes back to the loop for the backoff (code
review WR-02 of phase 25). The empty reason belongs to the parallel mode.

``supported`` says the companion of this process echoed a lane. A refusal, an
answer without the echo to the runner's own lane request, is sticky for the
life of the process: a companion that ignored the filter once is one from
before the filter, and asking again would hand out rows of every kind to a
runner that only embeds (Pitfall 1).

The module is neutral like findling/profile.py: standard library only, so that
the worker and the api may both import it. It logs nothing.
"""

from dataclasses import dataclass
from typing import Final

MODE_INLINE: Final = "inline"
MODE_PARALLEL: Final = "parallel"
MODES: Final = frozenset({MODE_INLINE, MODE_PARALLEL})

REASON_NONE: Final = ""
REASON_ECONOMY: Final = "economy"
REASON_OLD_COMPANION: Final = "companion_without_lane"
REASON_MEMORY: Final = "waiting_for_memory"
REASON_RUNNER_FAILED: Final = "runner_failed"
REASONS: Final = frozenset({REASON_NONE, REASON_ECONOMY, REASON_OLD_COMPANION, REASON_MEMORY, REASON_RUNNER_FAILED})


@dataclass(frozen=True, slots=True)
class LaneSnapshot:
    """The lane state of this process: mode, why it parks, and whether the echo was seen."""

    mode: str
    reason: str
    supported: bool


# The state of this process, at module level after the build of profile.py.
# Before any runner round the container is today's container: inline, and the
# effective level before the first profile read is economy (D-24-02).
_MODE: str = MODE_INLINE
_REASON: str = REASON_ECONOMY
_SUPPORTED: bool = False
_REFUSED: bool = False


def note_echo(honored: bool) -> None:
    """Publish whether the last claim answer echoed the lane that was asked for.

    Ignored after a refusal, which holds for the life of the process.
    """
    global _SUPPORTED
    if _REFUSED:
        return
    _SUPPORTED = honored


def note_refused() -> None:
    """The runner asked for its lane and the answer carried no echo: an old companion."""
    global _SUPPORTED, _REFUSED
    _REFUSED = True
    _SUPPORTED = False


def note_mode(mode: str, reason: str) -> None:
    """Publish where the embedding runs and, when inline, why.

    Only members of the closed sets count; anything else is a programming error
    and raises, because a status field fed from here must never carry a word
    the page does not know.
    """
    global _MODE, _REASON
    if mode not in MODES or reason not in REASONS:
        raise ValueError("unknown lane mode or reason")
    _MODE = mode
    _REASON = reason


def snapshot() -> LaneSnapshot:
    """The lane state of this process right now. Reading changes nothing."""
    return LaneSnapshot(mode=_MODE, reason=_REASON, supported=_SUPPORTED)


def reset() -> None:
    """Back to the resting state. For tests only; the container never forgets."""
    global _MODE, _REASON, _SUPPORTED, _REFUSED
    _MODE = MODE_INLINE
    _REASON = REASON_ECONOMY
    _SUPPORTED = False
    _REFUSED = False


__all__ = [
    "MODES",
    "MODE_INLINE",
    "MODE_PARALLEL",
    "REASONS",
    "REASON_ECONOMY",
    "REASON_MEMORY",
    "REASON_NONE",
    "REASON_OLD_COMPANION",
    "REASON_RUNNER_FAILED",
    "LaneSnapshot",
    "note_echo",
    "note_mode",
    "note_refused",
    "reset",
    "snapshot",
]
