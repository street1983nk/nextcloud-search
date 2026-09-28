"""The precision of the embedding model: the wire names and the process state.

The admin chooses the precision in the companion, which stores it next to the
profile and answers both over the same profile route (D-25-02). Two names form a
closed set, int8 and fp32, and the same two strings name the weight files in
findling.store.vectors; a test keeps both spellings equal, and another one keeps
this set equal to SettingsService::PRECISIONS on the PHP side.

int8 is the default. A companion that never answered, or one older than the
field, leaves the container on the weights it ships with today.

The process state is a pure state machine without I/O (plan 25-08). The rules
of the owner decisions:

* Nothing switches before the first successful read and before the start state
  was settled from the mark plus a verified file (D-25-03, D-25-14).
* A download is wished only for a change of the key from int8 to fp32 observed
  in this process, once per change. After a failure nothing is retried until
  the key goes to int8 and back to fp32 (D-25-04).
* fp32 is fetched or activated only while the chosen profile is Standard or
  Performance. A wish under economy is used up with fp32_not_in_economy, so a
  later profile switch never fetches or switches anything (D-25-01, D-25-10).
* An active fp32 stays until the key says int8, also under economy
  (fp32_active_in_economy) or on a box that shrank (fp32_on_a_tight_box,
  D-25-03, D-25-10). int8 is always the way back (D-25-09).
* A verified file the admin placed is activated without a download (D-25-06).

Every change of state reports the precision in force to findling.profile, so
the slot formula takes the fp32 extra into account (D-25-01).

The module is neutral: stdlib and findling.profile only, so that both the
worker and the api may import it. It logs nothing, neither precision names nor
environment values.
"""

import enum
from dataclasses import dataclass
from typing import Final

from findling import profile


class Precision(enum.StrEnum):
    """The wire names. Display texts come from the catalogues (phase 27)."""

    INT8 = "int8"
    FP32 = "fp32"


PRECISION_NAMES: Final = frozenset(p.value for p in Precision)
PRECISION_DEFAULT: Final = Precision.INT8

VERDICT_NONE: Final = ""
VERDICT_DOWNLOADING: Final = "downloading"
VERDICT_UNAVAILABLE: Final = "fp32_unavailable"
VERDICT_NOT_IN_ECONOMY: Final = "fp32_not_in_economy"
VERDICT_TIGHT_BOX: Final = "fp32_on_a_tight_box"
VERDICT_ACTIVE_IN_ECONOMY: Final = "fp32_active_in_economy"

VERDICTS: Final = frozenset(
    {
        VERDICT_NONE,
        VERDICT_DOWNLOADING,
        VERDICT_UNAVAILABLE,
        VERDICT_NOT_IN_ECONOMY,
        VERDICT_TIGHT_BOX,
        VERDICT_ACTIVE_IN_ECONOMY,
    }
)

# The chosen profiles under which fp32 may be fetched or activated (D-25-01).
_FP32_PROFILES: Final = frozenset({profile.Profile.STANDARD, profile.Profile.PERFORMANCE})


@dataclass(frozen=True, slots=True)
class PrecisionSnapshot:
    """What this process knows about its precision: chosen, active, verdict."""

    chosen: Precision | None
    active: Precision | None
    verdict: str
    procuring: bool

    @property
    def settled(self) -> bool:
        """True once the start state is known."""
        return self.active is not None


@dataclass(frozen=True, slots=True)
class PrecisionDecision:
    """The weights to run (None: change nothing) and whether to fetch fp32."""

    target: Precision | None
    procure: bool


# The state of this process, at module level and nowhere else, after the build
# of findling.profile.
_CHOSEN: Precision | None = None
_ACTIVE: Precision | None = None
_SETTLED: bool = False
# A change from int8 to fp32 was observed in this process and not yet used up.
_PENDING: bool = False
# A download was wished by decide and has not ended yet.
_ASKED: bool = False
_PROCURING: bool = False
# VERDICT_NONE, VERDICT_UNAVAILABLE or VERDICT_NOT_IN_ECONOMY.
_FAILURE: str = VERDICT_NONE
# The key went from fp32 back to int8 and the file may still lie on the volume.
_WITHDRAWN: bool = False


def _fp32_allowed() -> bool:
    return profile.snapshot().chosen in _FP32_PROFILES


def _report() -> None:
    """Tell the profile which weights are in force, for the slot formula."""
    in_force = (
        _ACTIVE is Precision.FP32
        or _PROCURING
        or (_CHOSEN is Precision.FP32 and _fp32_allowed() and _FAILURE == VERDICT_NONE)
    )
    profile.note_weights(Precision.FP32 if in_force else Precision.INT8)


def note_chosen_precision(value: str | None) -> None:
    """Publish the precision the admin chose, as read from the companion this round.

    None and anything outside PRECISION_NAMES change nothing (D-24-02 semantics).
    A change from int8 to fp32 is a wish to fetch; the first read is never such
    a change (D-25-14). A new int8 clears the wish and a failure before it.

    A change from fp32 to int8 is the way back (D-25-09), and it is recorded as
    a fact of its own (code review WR-04): the engine swap removes the weights
    only when fp32 was actually active, so a downloaded but never activated
    file needs the mark step to learn about the withdrawal. A fresh fp32 wish
    discards a recorded way back, because the file is wanted again (D-25-06).
    """
    global _CHOSEN, _PENDING, _ASKED, _FAILURE, _WITHDRAWN
    if value is None or value not in PRECISION_NAMES:
        return
    chosen = Precision(value)
    if _CHOSEN is Precision.INT8 and chosen is Precision.FP32:
        _PENDING = True
    if _CHOSEN is Precision.FP32 and chosen is Precision.INT8:
        _WITHDRAWN = True
    if chosen is Precision.FP32:
        _WITHDRAWN = False
    if chosen is Precision.INT8:
        _PENDING = False
        _ASKED = False
        _FAILURE = VERDICT_NONE
    _CHOSEN = chosen
    _report()


def settle(active: Precision) -> None:
    """Publish the start state of this process. Only the first call counts.

    The start state comes from the embedding mark plus a verified weights file,
    never from a failed read (D-25-14): a hiccup at start must not discard a
    stock that was built with fp32.
    """
    global _ACTIVE, _SETTLED
    if _SETTLED:
        return
    _SETTLED = True
    _ACTIVE = active
    _report()


def note_active(value: Precision) -> None:
    """Publish the weights the holder of this process runs after a swap."""
    global _ACTIVE, _SETTLED, _FAILURE
    _SETTLED = True
    _ACTIVE = value
    if value is Precision.FP32:
        _FAILURE = VERDICT_NONE
    _report()


def withdrawal_pending() -> bool:
    """True while an observed way back of the key has not removed the file yet.

    Set by :func:`note_chosen_precision` on the change from fp32 to int8 and
    taken back by the caller that removed the file (code review WR-04). Never
    true for an int8 that is merely the default of this process, so a file the
    admin placed for a coming fp32 choice is never read as withdrawn (D-25-06).
    """
    return _WITHDRAWN


def note_withdrawal_handled() -> None:
    """The file of the withdrawn choice is gone, or was never there."""
    global _WITHDRAWN
    _WITHDRAWN = False


def begin_procurement() -> None:
    """The fetch of the fp32 weights started."""
    global _PROCURING
    _PROCURING = True
    _report()


def end_procurement(*, succeeded: bool) -> None:
    """The fetch ended. A failure is not retried until int8 and then fp32 (D-25-04)."""
    global _PROCURING, _ASKED, _FAILURE
    _PROCURING = False
    _ASKED = False
    if not succeeded:
        _FAILURE = VERDICT_UNAVAILABLE
    _report()


def _decide_fp32(*, fp32_ready: bool) -> PrecisionDecision:
    """fp32 chosen, int8 running: fetch, activate or refuse."""
    global _PENDING, _ASKED, _FAILURE
    if _PROCURING:
        return PrecisionDecision(target=Precision.INT8, procure=False)
    if not _fp32_allowed():
        # D-25-10: the wish is used up, so a later profile switch never fetches.
        _PENDING = False
        _ASKED = False
        _FAILURE = VERDICT_NOT_IN_ECONOMY
        return PrecisionDecision(target=Precision.INT8, procure=False)
    if _FAILURE == VERDICT_NOT_IN_ECONOMY:
        return PrecisionDecision(target=Precision.INT8, procure=False)
    if fp32_ready:
        # D-25-06: a verified file is taken up without a download.
        _PENDING = False
        return PrecisionDecision(target=Precision.FP32, procure=False)
    if _PENDING:
        _PENDING = False
        _ASKED = True
        return PrecisionDecision(target=Precision.INT8, procure=True)
    if not _ASKED and _FAILURE == VERDICT_NONE:
        # fp32 read at start without a file: no fetch without an observed change.
        _FAILURE = VERDICT_UNAVAILABLE
    return PrecisionDecision(target=Precision.INT8, procure=False)


def decide(*, fp32_ready: bool) -> PrecisionDecision:
    """Which weights to run and whether to fetch fp32, after the rules above.

    ``fp32_ready`` says that a verified fp32 file lies in the models directory.
    Before the first read and before the settled start the target is None,
    which means: change nothing (Pitfall 6).
    """
    if _CHOSEN is None or _ACTIVE is None:
        return PrecisionDecision(target=None, procure=False)
    if _CHOSEN is Precision.INT8:
        decision = PrecisionDecision(target=Precision.INT8, procure=False)
    elif _ACTIVE is Precision.FP32:
        decision = PrecisionDecision(target=Precision.FP32, procure=False)
    else:
        decision = _decide_fp32(fp32_ready=fp32_ready)
    _report()
    return decision


def _verdict() -> str:
    if _PROCURING:
        return VERDICT_DOWNLOADING
    state = profile.snapshot()
    if _ACTIVE is Precision.FP32:
        if state.chosen not in _FP32_PROFILES:
            return VERDICT_ACTIVE_IN_ECONOMY
        if state.downgraded and state.effective is profile.Profile.ECONOMY:
            return VERDICT_TIGHT_BOX
    if _CHOSEN is Precision.FP32:
        return _FAILURE
    return VERDICT_NONE


def snapshot() -> PrecisionSnapshot:
    """The precision state of this process right now. The verdict is derived on read."""
    return PrecisionSnapshot(chosen=_CHOSEN, active=_ACTIVE, verdict=_verdict(), procuring=_PROCURING)


def reset() -> None:
    """Back to the resting state. For tests only; the container never forgets."""
    global _CHOSEN, _ACTIVE, _SETTLED, _PENDING, _ASKED, _PROCURING, _FAILURE, _WITHDRAWN
    _CHOSEN = None
    _ACTIVE = None
    _SETTLED = False
    _PENDING = False
    _ASKED = False
    _PROCURING = False
    _FAILURE = VERDICT_NONE
    _WITHDRAWN = False
    _report()
