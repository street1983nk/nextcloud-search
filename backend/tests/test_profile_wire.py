"""The profile names are one agreement between the two halves.

The companion stores the choice (``SettingsService::PROFILES``), the container
accepts only ``PROFILE_NAMES``. Neither side can import the other across the
AppAPI boundary, so this test reads the PHP source as text and holds the two
lists together: a name added on one side only would be stored by the admin and
then silently discarded by the container, which reads exactly like Economy.
"""

from __future__ import annotations

import re
from pathlib import Path

from findling.profile import PROFILE_NAMES, Profile

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_SERVICE = REPO_ROOT / "php" / "lib" / "Service" / "SettingsService.php"

_PROFILES = re.compile(r"public const PROFILES = \[(.*?)\];", re.DOTALL)
_DEFAULT = re.compile(r"public const PROFILE_DEFAULT = '(\w+)';")
_QUOTED = re.compile(r"'(\w+)'")


def _source() -> str:
    return SETTINGS_SERVICE.read_text(encoding="utf-8")


def test_each_constant_is_found_exactly_once() -> None:
    # Anti-vacuity: a renamed or duplicated constant must fail loudly here
    # instead of letting the comparisons below compare nothing.
    source = _source()

    assert len(_PROFILES.findall(source)) == 1
    assert len(_DEFAULT.findall(source)) == 1


def test_the_php_profile_set_matches_profile_names() -> None:
    match = _PROFILES.search(_source())
    assert match is not None

    names = _QUOTED.findall(match.group(1))

    assert names, "PROFILES in SettingsService.php lists no name"
    assert len(names) == len(set(names))
    assert frozenset(names) == PROFILE_NAMES


def test_the_php_default_is_economy() -> None:
    match = _DEFAULT.search(_source())
    assert match is not None

    assert match.group(1) == Profile.ECONOMY.value
