"""The memory guard: slot throttle, escalation, cap and way back (PAR-03).

Three decisions live here, all without I/O; the kernel counters come from
findling.memory_guard, the tick and the persistence from the worker.

* The throttle (D-26-02). Before every pass the slots of the profile are cut to
  what the anon headroom holds: slot 1 always runs (D-25-11), slot k needs
  (k - 1) x OCR_SLOT_COST_BYTES plus GUARD_RESERVE_BYTES. An unreadable
  headroom means one slot.
* The escalation (D-26-03, D-26-15, D-26-16). memory.events max is counted by
  the kernel before the reclaim and rises with the page cache of the mmap
  index, so a rise alone is noise. A tick counts as an event only when max
  rose AND the headroom is below the reserve; two such events at least
  GUARD_MIN_GAP_SECONDS apart inside GUARD_WINDOW_SECONDS lower the level. A
  rising oom_kill counter, or a child kill the pool reports, lowers at once.
* The cap (D-26-01, D-26-04). Lowering caps the effective level one below where
  it stood and never below economy; the chosen profile is never rewritten. The
  cap carries a random token. It goes away only when the admin confirms that
  token or chooses another profile; the guard never raises by itself.

The causes form a closed set, so that the status page can say them without
inventing words. The meta keys of state.db are spelled here once, for the
poller and the guard task alike.

The module is neutral like findling/profile.py: standard library,
findling.config and findling.profile only, so that the worker and the api may
both import it. findling.profile never imports this one (cycle); the cap is
handed over through profile.note_cap. It logs nothing, least of all the token.
"""

import math
import re
import secrets
import threading
from collections import deque
from dataclasses import dataclass
from typing import Final

from findling import profile
from findling.config import (
    GUARD_MIN_GAP_SECONDS,
    GUARD_RESERVE_BYTES,
    GUARD_WINDOW_SECONDS,
    OCR_SLOT_COST_BYTES,
)
from findling.profile import PROFILE_NAMES, PROFILE_ORDER, Profile

CAUSE_NONE: Final = ""
CAUSE_MEMORY_MAX_REPEATED: Final = "memory_max_repeated"
CAUSE_OOM_KILL: Final = "oom_kill"
CAUSE_UNCLEAN_END: Final = "unclean_end"
CAUSES: Final = frozenset({CAUSE_MEMORY_MAX_REPEATED, CAUSE_OOM_KILL, CAUSE_UNCLEAN_END})

# The keys of the guard in the meta table of state.db, shared by the poller and
# the guard task. multi_slot_pass holds the effective level while a pass with
# more than one slot runs and "" otherwise; multi_slot_chosen the chosen
# profile at the start of that pass. A start that finds the pass mark set died
# inside such a pass (unclean_end). Plain names without Final, the spelling
# the plans grep for; nothing rebinds them.
META_CAP = "guard_cap"
META_CAUSE = "guard_cause"
META_SINCE = "guard_since"
META_TOKEN = "guard_token"  # noqa: S105 - the name of a meta key, not a secret
META_CHOSEN = "guard_chosen"
META_MULTI_SLOT_PASS = "multi_slot_pass"  # noqa: S105 - the name of a meta key, not a password
META_MULTI_SLOT_CHOSEN = "multi_slot_chosen"

_TOKEN_PATTERN: Final = re.compile(r"[0-9a-f]{32}")

# The two counters of memory.events the escalation reads. The kill cause is
# spelled like the kernel counter on purpose, so the word is not repeated.
_MAX: Final = "max"
_OOM_KILL: Final = CAUSE_OOM_KILL

# Qualified events inside the window that lower the level (D-26-03).
_EVENTS_TO_LOWER: Final = 2


@dataclass(frozen=True, slots=True)
class GuardSnapshot:
    """The guard state of this process: cap, cause, token and the slots in force."""

    cap: Profile | None
    cause: str
    # Epoch seconds of the lowering, None without a cap.
    since: float | None
    token: str
    # The profile the admin had chosen when the level was lowered.
    chosen: Profile | None
    slots_target: int
    slots_in_force: int
    throttled: bool
    # Moves on every change of the cap, so that a writer knows when to persist.
    revision: int


def throttled_slots(target: int, headroom: int | None) -> int:
    """Slot 1 always runs (D-25-11); slot k needs (k - 1) x cost + reserve of headroom.

    Conservative: the headroom already counts resting children as used.
    """
    if target <= 1 or headroom is None:
        return 1
    extra = max(0, (headroom - GUARD_RESERVE_BYTES) // OCR_SLOT_COST_BYTES)
    return min(target, 1 + extra)


class Escalation:
    """Turns successive readings of memory.events into a cause, or CAUSE_NONE.

    One instance per guard task. The first reading only sets the base; a
    counter that falls (a new cgroup after a restart) sets the base anew and
    is no event.
    """

    def __init__(
        self,
        *,
        window: float = GUARD_WINDOW_SECONDS,
        min_gap: float = GUARD_MIN_GAP_SECONDS,
        reserve: int = GUARD_RESERVE_BYTES,
    ) -> None:
        self._window = window
        self._min_gap = min_gap
        self._reserve = reserve
        self._base: dict[str, int] | None = None
        self._counted: deque[float] = deque()

    def observe(self, now: float, events: dict[str, int] | None, headroom: int | None, child_kills: int) -> str:
        """One tick: the readings of now and the child kills since the last tick."""
        base = self._base
        self._base = events
        if child_kills > 0:
            self._counted.clear()
            return CAUSE_OOM_KILL
        if events is None or base is None:
            return CAUSE_NONE
        rise_max = events.get(_MAX, 0) - base.get(_MAX, 0)
        rise_kill = events.get(_OOM_KILL, 0) - base.get(_OOM_KILL, 0)
        if rise_max < 0 or rise_kill < 0:
            return CAUSE_NONE
        if rise_kill > 0:
            self._counted.clear()
            return CAUSE_OOM_KILL
        if rise_max == 0 or headroom is None or headroom >= self._reserve:
            return CAUSE_NONE
        while self._counted and now - self._counted[0] > self._window:
            self._counted.popleft()
        if self._counted and now - self._counted[-1] < self._min_gap:
            return CAUSE_NONE
        self._counted.append(now)
        if len(self._counted) >= _EVENTS_TO_LOWER:
            self._counted.clear()
            return CAUSE_MEMORY_MAX_REPEATED
        return CAUSE_NONE


# The state of this process, at module level after the build of lane.py. Before
# anything is restored there is no cap, and the container runs one slot.
_CAP: Profile | None = None
_CAUSE: str = CAUSE_NONE
_SINCE: float | None = None
_TOKEN: str = ""
_CHOSEN: Profile | None = None
_SLOTS_TARGET: int = 1
_SLOTS_IN_FORCE: int = 1
_REVISION: int = 0

# Child kills are reported from the pool threads and taken by the guard task.
_KILLS_LOCK = threading.Lock()
_KILLS: int = 0


def _set_cap(cap: Profile | None, cause: str, since: float | None, token: str, chosen: Profile | None) -> None:
    global _CAP, _CAUSE, _SINCE, _TOKEN, _CHOSEN, _REVISION
    _CAP = cap
    _CAUSE = cause
    _SINCE = since
    _TOKEN = token
    _CHOSEN = chosen
    _REVISION += 1
    profile.note_cap(cap)


def lower(cause: str, *, now: float, chosen: Profile | None, effective: Profile) -> bool:
    """Cap the effective level one below where it stands; False at the floor.

    ``effective`` is the level in force, ``chosen`` the profile the admin chose.
    An existing cap counts as well, so two lowerings go two levels down. Economy
    is the floor: there nothing changes (D-24-07). An unknown cause is a
    programming error and raises.
    """
    if cause not in CAUSES:
        raise ValueError("unknown guard cause")
    level = effective if _CAP is None else min(effective, _CAP, key=PROFILE_ORDER.index)
    position = PROFILE_ORDER.index(level)
    if position == 0:
        return False
    # 16 random bytes, 32 hex digits: the shape _TOKEN_PATTERN checks.
    _set_cap(PROFILE_ORDER[position - 1], cause, now, secrets.token_hex(16), chosen)
    return True


def _since(value: str | float | None) -> float | None:
    if value is None:
        return None
    try:
        since = float(value)
    except ValueError:
        return None
    return since if math.isfinite(since) else None


def restore(
    cap: str | None, cause: str | None, since: str | float | None, token: str | None, chosen: str | None
) -> bool:
    """Bring a cap back that state.db kept over a restart; False drops foreign values.

    Every value is checked against its closed set: the level and the chosen
    profile against PROFILE_NAMES, the cause against CAUSES, the token against
    32 lower case hex digits, the time against a finite number.
    """
    moment = _since(since)
    if cap is None or cap not in PROFILE_NAMES or chosen is None or chosen not in PROFILE_NAMES:
        return False
    if cause is None or cause not in CAUSES or not _is_token(token) or moment is None:
        return False
    _set_cap(Profile(cap), cause, moment, str(token), Profile(chosen))
    return True


def _is_token(value: str | None) -> bool:
    return value is not None and _TOKEN_PATTERN.fullmatch(value) is not None


def note_confirmation(confirmed: str | None, chosen: str | None) -> bool:
    """Lift the cap when the admin confirmed its token or chose another profile.

    ``chosen`` None or outside PROFILE_NAMES changes nothing (D-24-02), and so
    does a wrong token with the same profile. There is no way up besides this
    one (D-26-04).
    """
    if _CAP is None or chosen is None or chosen not in PROFILE_NAMES:
        return False
    # Only a well formed value is compared: compare_digest refuses non ASCII text.
    token_matches = confirmed is not None and _is_token(confirmed) and secrets.compare_digest(confirmed, _TOKEN)
    if not token_matches and Profile(chosen) is _CHOSEN:
        return False
    _set_cap(None, CAUSE_NONE, None, "", None)
    return True


def note_slots(target: int, in_force: int) -> None:
    """Publish the slots of the profile and the slots the throttle let run."""
    global _SLOTS_TARGET, _SLOTS_IN_FORCE
    _SLOTS_TARGET = target
    _SLOTS_IN_FORCE = in_force


def report_child_kill() -> None:
    """A child died from a kill it did not ask for. Safe from any thread."""
    global _KILLS
    with _KILLS_LOCK:
        _KILLS += 1


def take_child_kills() -> int:
    """The child kills since the last call, and zero from then on."""
    global _KILLS
    with _KILLS_LOCK:
        taken = _KILLS
        _KILLS = 0
    return taken


def snapshot() -> GuardSnapshot:
    """The guard state of this process right now. Reading changes nothing."""
    return GuardSnapshot(
        cap=_CAP,
        cause=_CAUSE,
        since=_SINCE,
        token=_TOKEN,
        chosen=_CHOSEN,
        slots_target=_SLOTS_TARGET,
        slots_in_force=_SLOTS_IN_FORCE,
        throttled=_SLOTS_IN_FORCE < _SLOTS_TARGET,
        revision=_REVISION,
    )


def reset() -> None:
    """Back to the resting state. For tests only; the container never forgets."""
    global _CAP, _CAUSE, _SINCE, _TOKEN, _CHOSEN, _SLOTS_TARGET, _SLOTS_IN_FORCE, _REVISION, _KILLS
    _CAP = None
    _CAUSE = CAUSE_NONE
    _SINCE = None
    _TOKEN = ""
    _CHOSEN = None
    _SLOTS_TARGET = 1
    _SLOTS_IN_FORCE = 1
    _REVISION = 0
    with _KILLS_LOCK:
        _KILLS = 0
    profile.note_cap(None)


__all__ = [
    "CAUSES",
    "CAUSE_MEMORY_MAX_REPEATED",
    "CAUSE_NONE",
    "CAUSE_OOM_KILL",
    "CAUSE_UNCLEAN_END",
    "META_CAP",
    "META_CAUSE",
    "META_CHOSEN",
    "META_MULTI_SLOT_CHOSEN",
    "META_MULTI_SLOT_PASS",
    "META_SINCE",
    "META_TOKEN",
    "Escalation",
    "GuardSnapshot",
    "lower",
    "note_confirmation",
    "note_slots",
    "report_child_kill",
    "reset",
    "restore",
    "snapshot",
    "take_child_kills",
    "throttled_slots",
]
