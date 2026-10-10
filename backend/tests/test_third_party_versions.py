"""The gate between THIRD-PARTY.md and the pins in backend/pyproject.toml.

THIRD-PARTY.md is the narrative account of what the image distributes, and a
licence account that names the wrong version is an account of something that
is not shipped. Until plan 31-01 it had drifted behind the pins without anybody
noticing: pypdf, charset-normalizer, lxml and striprtf in the extraction table,
numpy and semantic-text-splitter in the semantic table and fastapi in the table
of the rest, each one or more releases behind ``backend/pyproject.toml``.
Dependabot moves the pin and nothing moved the prose.

What this gate holds:

1. Every table row of THIRD-PARTY.md whose place in the image lies under
   ``/app/.venv`` names a Python package, and its version is exactly the
   ``name==version`` pin of ``[project].dependencies``. A row without a pin is a
   finding as well, because it claims something is installed that no pin
   decides.
2. Every pin of ``[project].dependencies`` has such a row. A package that is
   installed into the image and has no licence account is the other half of
   the same drift.
3. The libraries the pillow-heif wheels carry are named, together with the
   licence that reaches furthest, GPL-2.0-or-later through x265.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
THIRD_PARTY = REPO_ROOT / "THIRD-PARTY.md"
PYPROJECT = REPO_ROOT / "backend" / "pyproject.toml"

_PIN = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+)(?:\[[^\]]*\])?==(?P<version>[^\s;]+)$")
_CELL_NAME = re.compile(r"^`(?P<name>[A-Za-z0-9_.-]+)(?:\[[^\]]*\])?`$")


def _normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _pins() -> dict[str, str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    pins: dict[str, str] = {}
    for spec in data["project"]["dependencies"]:
        match = _PIN.match(spec.strip())
        assert match, f"not an exact pin: {spec!r}"
        pins[_normalise(match["name"])] = match["version"]
    return pins


def _split(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _venv_rows(text: str) -> dict[str, str]:
    """Every table row whose place in the image is under /app/.venv."""
    rows: dict[str, str] = {}
    header: list[str] | None = None
    for line in text.splitlines():
        if not line.startswith("|"):
            header = None
            continue
        cells = _split(line)
        if header is None:
            header = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if "Version" not in header or "Place in the image" not in header:
            continue
        place = cells[header.index("Place in the image")]
        if not place.startswith("`/app/.venv"):
            continue
        match = _CELL_NAME.match(cells[0])
        assert match, f"a /app/.venv row without a package name: {line}"
        name = _normalise(match["name"])
        assert name not in rows, f"two rows for {name}"
        rows[name] = cells[header.index("Version")]
    return rows


def test_the_scan_sees_the_three_python_tables() -> None:
    rows = _venv_rows(THIRD_PARTY.read_text(encoding="utf-8"))
    # One package of each table: extraction, semantic, the rest.
    assert {"pypdf", "onnxruntime", "nc-py-api"} <= set(rows)


def test_every_row_names_the_pinned_version() -> None:
    pins = _pins()
    rows = _venv_rows(THIRD_PARTY.read_text(encoding="utf-8"))
    wrong = {name: (version, pins.get(name, "no pin")) for name, version in rows.items() if pins.get(name) != version}
    assert not wrong, f"THIRD-PARTY.md version against pin: {wrong}"


def test_every_pin_has_a_row() -> None:
    rows = _venv_rows(THIRD_PARTY.read_text(encoding="utf-8"))
    missing = sorted(set(_pins()) - set(rows))
    assert not missing, f"pinned but not accounted for in THIRD-PARTY.md: {missing}"


def test_the_new_formats_are_pinned() -> None:
    pins = _pins()
    assert pins.get("olefile") == "0.47"
    assert pins.get("xlrd") == "2.0.2"
    assert "pillow-heif" in pins


def test_the_libraries_of_the_heif_wheel_are_accounted_for() -> None:
    text = THIRD_PARTY.read_text(encoding="utf-8")
    for word in ("libheif", "libde265", "x265", "GPL-2.0-or-later", "LGPL-3.0"):
        assert word in text, word


def test_the_gate_fires_on_a_stale_row() -> None:
    sample = (
        "| Package | Version | Licence | Source repository | Place in the image |\n"
        "|---|---|---|---|---|\n"
        "| `pypdf` | 0.0.1 | BSD-3-Clause | x | `/app/.venv/lib/pypdf` |\n"
        "| `nc-py-api[app]` | 9.9.9 | BSD-3-Clause | x | `/app/.venv` |\n"
        "\n"
        "| Item | Version | Licence | Origin | Place in the image |\n"
        "|---|---|---|---|---|\n"
        "| `frpc` | frp 0.61.1 | Apache-2.0 | x | `/usr/local/bin/frpc` |\n"
    )
    rows = _venv_rows(sample)
    assert rows == {"pypdf": "0.0.1", "nc-py-api": "9.9.9"}
    pins = _pins()
    assert rows["pypdf"] != pins["pypdf"]
