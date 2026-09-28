"""The profile, precision and lane names are one agreement between the two halves.

The companion stores the choice (``SettingsService::PROFILES`` and
``SettingsService::PRECISIONS``), the container accepts only ``PROFILE_NAMES``
and ``PRECISION_NAMES``. The companion filters a claim by lane
(``QueueService::LANES``), the container asks with ``LANES``. Neither side can
import the other across the AppAPI boundary, so this test reads the PHP source as
text and holds the lists together: a name added on one side only would be stored
by the admin and then silently discarded by the container, which reads exactly
like Economy and int8.
"""

from __future__ import annotations

import re
from pathlib import Path

from findling.nc.queue import LANE_ALL, LANES
from findling.precision import PRECISION_DEFAULT, PRECISION_NAMES, Precision
from findling.profile import PROFILE_NAMES, Profile
from findling.store.vectors import WEIGHTS_FP32, WEIGHTS_INT8

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_SERVICE = REPO_ROOT / "php" / "lib" / "Service" / "SettingsService.php"
QUEUE_SERVICE = REPO_ROOT / "php" / "lib" / "Service" / "QueueService.php"

_PROFILES = re.compile(r"public const PROFILES = \[(.*?)\];", re.DOTALL)
_DEFAULT = re.compile(r"public const PROFILE_DEFAULT = '(\w+)';")
_PRECISIONS = re.compile(r"public const PRECISIONS = \[(.*?)\];", re.DOTALL)
_PRECISION_DEFAULT = re.compile(r"public const PRECISION_DEFAULT = '(\w+)';")
_LANES = re.compile(r"public const LANES = \[(.*?)\];", re.DOTALL)
_QUOTED = re.compile(r"'(\w+)'")


def _source() -> str:
    return SETTINGS_SERVICE.read_text(encoding="utf-8")


def _queue_source() -> str:
    return QUEUE_SERVICE.read_text(encoding="utf-8")


def _names(pattern: re.Pattern[str], source: str) -> list[str]:
    match = pattern.search(source)
    assert match is not None
    return _QUOTED.findall(match.group(1))


def test_each_constant_is_found_exactly_once() -> None:
    # Anti-vacuity: a renamed or duplicated constant must fail loudly here
    # instead of letting the comparisons below compare nothing.
    source = _source()

    assert len(_PROFILES.findall(source)) == 1
    assert len(_DEFAULT.findall(source)) == 1
    assert len(_PRECISIONS.findall(source)) == 1
    assert len(_PRECISION_DEFAULT.findall(source)) == 1
    assert len(_LANES.findall(_queue_source())) == 1


def test_the_php_profile_set_matches_profile_names() -> None:
    names = _names(_PROFILES, _source())

    assert names, "PROFILES in SettingsService.php lists no name"
    assert len(names) == len(set(names))
    assert frozenset(names) == PROFILE_NAMES


def test_the_php_default_is_economy() -> None:
    match = _DEFAULT.search(_source())
    assert match is not None

    assert match.group(1) == Profile.ECONOMY.value


def test_the_php_precision_set_matches_precision_names() -> None:
    names = _names(_PRECISIONS, _source())

    assert names, "PRECISIONS in SettingsService.php lists no name"
    assert len(names) == len(set(names))
    assert frozenset(names) == PRECISION_NAMES


def test_the_php_precision_default_is_int8() -> None:
    match = _PRECISION_DEFAULT.search(_source())
    assert match is not None

    assert match.group(1) == PRECISION_DEFAULT.value == Precision.INT8.value


def test_the_precision_names_are_the_weight_names() -> None:
    # The same two strings name the weight files the engine loads.
    assert {p.value for p in Precision} == {WEIGHTS_INT8, WEIGHTS_FP32}


def test_the_php_lane_set_matches_lanes() -> None:
    names = _names(_LANES, _queue_source())

    assert names, "LANES in QueueService.php lists no name"
    assert len(names) == len(set(names))
    assert frozenset(names) == LANES
    assert LANE_ALL in LANES
