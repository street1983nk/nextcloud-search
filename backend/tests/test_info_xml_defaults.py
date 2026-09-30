"""Every default declared in info.xml equals its constant in config.py.

Before v1.4 a drift between the two was a cosmetic fault: the admin form showed
one number and the container used another. With the profiles it becomes a
functional one. AppAPI injects every declared default as a real environment
variable (ExAppEnvVarsHelper::normalizeAndValidate, research pitfall 1), and
the profile layer treats a value that differs from the config.py default as an
admin override (explicit_int_from_environment). A default in info.xml that has
drifted away from config.py would therefore overrule the profile on every box,
without anybody having chosen anything. This test is what keeps the two equal.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

import pytest

from findling import config
from findling.config import explicit_int_from_environment
from findling.main import log_level

BACKEND_INFO = Path(__file__).resolve().parents[1] / "appinfo" / "info.xml"


def _wire(value: bool) -> str:
    return "true" if value else "false"


# Variables without a constant in config.py: the literal default lives in the
# reader, so the reader itself is called with the variable unset.
READER_WITNESSED = frozenset({"FINDLING_LOG_LEVEL"})

# Name of every other declared variable, mapped to the wire form of the
# config.py constant used when the variable is unset.
EXPECTED: dict[str, str] = {
    "FINDLING_LANGUAGES": ",".join(config.DEFAULT_LANGUAGES),
    "FINDLING_COMPOUND_DICT": config.DEFAULT_COMPOUND_DICT,
    "FINDLING_MAX_FILE_BYTES": str(config.MAX_FILE_BYTES),
    "FINDLING_OCR_ENABLED": _wire(config.OCR_ENABLED),
    "FINDLING_OCR_LANGUAGES": "+".join(config.OCR_DEFAULT_LANGUAGES),
    "FINDLING_OCR_MAX_PAGES": str(config.OCR_MAX_PAGES),
    "FINDLING_OCR_PAGE_SECONDS": str(config.OCR_PAGE_SECONDS),
    "FINDLING_OCR_JOB_SECONDS": str(config.OCR_JOB_SECONDS),
    "FINDLING_OCR_DPI": str(config.OCR_DPI),
    "FINDLING_RECONCILE_ENABLED": _wire(config.RECONCILE_ENABLED),
    "FINDLING_RECONCILE_HOUR": str(config.RECONCILE_HOUR),
    "FINDLING_RECONCILE_MIN_INTERVAL_HOURS": str(config.RECONCILE_MIN_INTERVAL_HOURS),
    "FINDLING_RECONCILE_QUIET_MAX": str(config.RECONCILE_QUIET_MAX),
    "FINDLING_RECONCILE_SLICE": str(config.RECONCILE_SLICE),
    "FINDLING_EMBED_IDLE_RELEASE_SECONDS": str(config.EMBED_IDLE_RELEASE_SECONDS),
    "FINDLING_EXTRACT_ADDRESS_SPACE_BYTES": str(config.EXTRACT_ADDRESS_SPACE_BYTES),
}

# The variables a profile can raise, with the default and range their reader
# uses. A declared default here must never read as an override.
PROFILE_RELEVANT: dict[str, tuple[int, tuple[int, int]]] = {
    "FINDLING_OCR_MAX_PAGES": (config.OCR_MAX_PAGES, config.OCR_MAX_PAGES_RANGE),
    "FINDLING_OCR_DPI": (config.OCR_DPI, config.OCR_DPI_RANGE),
}


def _declared() -> dict[str, str]:
    info = ElementTree.fromstring(BACKEND_INFO.read_text(encoding="utf-8"))  # noqa: S314
    declared: dict[str, str] = {}
    for variable in info.iter("variable"):
        name = variable.findtext("name")
        default = variable.findtext("default")
        assert name is not None, "every <variable> carries a <name>"
        assert default is not None, f"{name} declares no <default>"
        declared[name.strip()] = default.strip()
    return declared


def test_the_log_level_reader_falls_back_to_info(monkeypatch: pytest.MonkeyPatch) -> None:
    # The log level has no constant in config.py; its reader is the witness.
    monkeypatch.delenv("FINDLING_LOG_LEVEL", raising=False)

    assert log_level() == _declared()["FINDLING_LOG_LEVEL"]


def test_every_declared_default_equals_the_constant_in_config() -> None:
    declared = _declared()

    for name, default in declared.items():
        if name in READER_WITNESSED:
            continue
        assert default == EXPECTED[name], f"{name}: info.xml says {default!r}, config.py says {EXPECTED[name]!r}"


def test_every_declared_variable_is_in_the_map() -> None:
    declared = _declared()

    # Anti vacuity: sixteen variables are declared today; a parser that found
    # none would pass every comparison above.
    assert len(declared) >= 16
    assert set(declared) == set(EXPECTED) | READER_WITNESSED


@pytest.mark.parametrize("name", sorted(PROFILE_RELEVANT))
def test_a_declared_default_never_counts_as_an_override(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    default, bounds = PROFILE_RELEVANT[name]
    monkeypatch.setenv(name, _declared()[name])

    assert explicit_int_from_environment(name, default, bounds) is None


def test_the_extraction_address_space_is_declared() -> None:
    # AppAPI hands an ExApp only the variables its info.xml declares
    # (ExAppEnvVarsHelper::normalizeAndValidate); an undeclared --env is
    # dropped without a word. The sandbox limit was readable from the
    # environment since phase 2 but never declared, so an admin whose large
    # photos end as failed(out_of_memory) had no way to raise it short of a
    # private manifest. Measured 2026-09-29 on a 29 user instance: 45 JPEGs of
    # 1.3 to 11.2 MB burst the 512 MB child; 1 GiB takes them.
    assert "FINDLING_EXTRACT_ADDRESS_SPACE_BYTES" in _declared()
