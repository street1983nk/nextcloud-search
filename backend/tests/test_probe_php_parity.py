"""The closed sets of the probe are one agreement between the two halves.

The container reports state, step, verdict, cause and numbers out of the sets
in ``findling.probe``; the companion judges every field of that answer against
its own copy in ``ProbeService.php`` and drops what it does not know (T-27-22).
Neither side can import the other across the AppAPI boundary, so this test
reads the PHP source as text and holds the sets together: a word added on one
side only would either be dropped by the companion, a verdict nobody takes
over, or accepted by it without the container ever sending it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from findling import probe

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE_SERVICE = REPO_ROOT / "php" / "lib" / "Service" / "ProbeService.php"

_CONSTANT = re.compile(r"private const PROBE_(STATES|STEPS|VERDICTS|CAUSES|NUMBERS) = \[([^\]]*)\];")
_QUOTED = re.compile(r"'([A-Za-z0-9_]*)'")

EXPECTED: dict[str, frozenset[str]] = {
    "STATES": frozenset(probe.STATES),
    "STEPS": frozenset(probe.STEPS),
    "VERDICTS": frozenset(probe.VERDICTS),
    "CAUSES": frozenset(probe.CAUSES),
    "NUMBERS": frozenset(probe.NUMBER_KEYS),
}


def _php_sets() -> dict[str, list[str]]:
    source = PROBE_SERVICE.read_text(encoding="utf-8")
    found: dict[str, list[str]] = {}
    for name, body in _CONSTANT.findall(source):
        assert name not in found, f"ProbeService.php declares PROBE_{name} twice"
        found[name] = _QUOTED.findall(body)
    return found


def test_every_set_is_found_exactly_once() -> None:
    # Anti-vacuity: a renamed constant or one split over several lines must
    # fail here instead of letting the comparison below compare nothing.
    assert sorted(_php_sets()) == sorted(EXPECTED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_the_php_set_equals_the_python_set(name: str) -> None:
    words = _php_sets()[name]

    assert len(words) == len(set(words)), f"PROBE_{name} repeats a word"
    assert set(words) == EXPECTED[name]


def test_the_steps_keep_their_order() -> None:
    # The page draws the steps in this order, so the order is part of it.
    assert _php_sets()["STEPS"] == list(probe.STEPS)


def test_the_empty_cause_of_fits_is_not_a_cause() -> None:
    # "fits" carries the empty cause; it is not a member of the set on either
    # side, so an empty word never passes as a reason.
    assert "" not in _php_sets()["CAUSES"]
    assert probe.CAUSE_NONE not in probe.CAUSES
