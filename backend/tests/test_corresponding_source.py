"""The gate over the corresponding source of the GPL and LGPL libraries.

The backend image distributes x265 (GPL-2.0-or-later), libheif and libde265
(LGPL-3.0) inside the pillow-heif wheel. The source duty is met with four exact
archives, named twice: as the constant ``ARCHIVES`` of
``scripts/release/corresponding_source.py``, which downloads, checks and
mirrors them, and as the table "Corresponding source of the native libraries in
the image" in THIRD-PARTY.md, which is what a reader finds. Two lists of the
same thing drift unless something holds them together, and this gate does:

1. Every row of the table is an entry of ``ARCHIVES`` with the same name,
   version, URL, SHA-256 and licence, and the other way round.
2. The list holds the pillow-heif sdist of the pinned version plus x265,
   libheif and libde265; every SHA-256 is 64 hex characters, every URL https.
3. ``--verify-only`` fails on a manipulated file (offline, with ``--expect``)
   and passes on the genuine one, so the check is seen to fire.
4. ``publish --dry-run`` uploads exactly the four archives, creates the release
   as a pre-release that is never latest, carries notes that list every archive
   with its SHA-256 and no dash or emoji outside ASCII, and refuses a tag that
   looks like a store release.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import tomllib
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "release" / "corresponding_source.py"
THIRD_PARTY = REPO_ROOT / "THIRD-PARTY.md"
PYPROJECT = REPO_ROOT / "backend" / "pyproject.toml"
MODULE = "findling_corresponding_source"
TABLE_HEADING = "### Corresponding source of the native libraries in the image"


def _load() -> ModuleType:
    specification = importlib.util.spec_from_file_location(MODULE, SCRIPT)
    if specification is None or specification.loader is None:  # pragma: no cover
        raise RuntimeError(f"the script is not at {SCRIPT}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def script() -> ModuleType:
    return _load()


def _table_rows() -> set[tuple[str, str, str, str, str]]:
    text = THIRD_PARTY.read_text(encoding="utf-8")
    assert TABLE_HEADING in text
    section = text.split(TABLE_HEADING, 1)[1].split("\n#", 1)[0]
    rows: set[tuple[str, str, str, str, str]] = set()
    for line in section.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == 5, line
        name, version, url, digest, licence = cells
        rows.add((name.strip("`"), version, url, digest.strip("`"), licence))
    return rows


def _pin(package: str) -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    for spec in data["project"]["dependencies"]:
        name, _, version = spec.partition("==")
        if name == package:
            return version
    raise AssertionError(f"{package} is not pinned")


def test_table_and_script_are_the_same_four_archives(script: ModuleType) -> None:
    from_script = {(a.name, a.version, a.url, a.sha256, a.licence) for a in script.ARCHIVES}
    assert len(from_script) == 4
    assert _table_rows() == from_script


def test_the_list_holds_the_sdist_and_the_three_libraries(script: ModuleType) -> None:
    projects = {a.project: a for a in script.ARCHIVES}
    assert set(projects) == {"pillow-heif", "x265", "libheif", "libde265"}
    assert projects["pillow-heif"].version == _pin("pillow-heif")
    assert projects["pillow-heif"].name == f"pillow_heif-{_pin('pillow-heif')}.tar.gz"
    # The versions LICENSES_bundled.txt of the pinned wheel names.
    assert projects["libheif"].version == "1.23.4"
    assert projects["libde265"].version == "1.1.3"
    assert projects["x265"].version == "4.2"
    assert projects["x265"].licence == "GPL-2.0-or-later"
    for archive in script.ARCHIVES:
        assert re.fullmatch(r"[0-9a-f]{64}", archive.sha256), archive.name
        assert archive.url.startswith("https://"), archive.name
        assert archive.url.endswith("/" + archive.name), archive.name


def test_verify_only_fails_on_a_manipulated_file(script: ModuleType, tmp_path: Path) -> None:
    genuine = b"genuine archive bytes"
    digest = hashlib.sha256(genuine).hexdigest()
    (tmp_path / "x265_4.2.tar.gz").write_bytes(genuine)
    expect = ["--expect", f"x265_4.2.tar.gz={digest}"]
    # Positive control: the genuine file passes.
    assert script.main(["--verify-only", str(tmp_path), *expect]) == 0
    (tmp_path / "x265_4.2.tar.gz").write_bytes(genuine + b"x")
    assert script.main(["--verify-only", str(tmp_path), *expect]) != 0


def test_verify_only_fails_on_a_missing_file(script: ModuleType, tmp_path: Path) -> None:
    assert script.main(["--verify-only", str(tmp_path)]) != 0


def test_verify_only_rejects_a_malformed_hash(script: ModuleType, tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        script.main(["--verify-only", str(tmp_path), "--expect", "a.tar.gz=XYZ"])


def _dry_run(script: ModuleType, capsys: pytest.CaptureFixture[str], tag: str, directory: Path) -> list[list[str]]:
    code = script.main(["publish", "--tag", tag, "--source-dir", str(directory), "--dry-run"])
    assert code == 0
    return [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]


def test_publish_uploads_exactly_the_four_archives(
    script: ModuleType, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    (tmp_path / "stray.txt").write_text("not an archive", encoding="utf-8")
    commands = _dry_run(script, capsys, "source-1.5-dev", tmp_path)
    uploads = [c for c in commands if c[:3] == ["gh", "release", "upload"]]
    assert len(uploads) == 1
    files = [arg for arg in uploads[0] if arg.startswith(str(tmp_path))]
    assert sorted(Path(f).name for f in files) == sorted(a.name for a in script.ARCHIVES)
    assert "--clobber" in uploads[0]


def test_publish_creates_a_prerelease_that_is_never_latest(
    script: ModuleType, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    commands = _dry_run(script, capsys, "source-1.5-dev", tmp_path)
    creates = [c for c in commands if c[:3] == ["gh", "release", "create"]]
    assert len(creates) == 1
    create = creates[0]
    assert create[3] == "source-1.5-dev"
    assert "--prerelease" in create
    assert "--latest=false" in create
    assert create[create.index("--title") + 1].startswith("Source mirror")
    notes = create[create.index("--notes") + 1]
    for archive in script.ARCHIVES:
        assert f"{archive.project} {archive.version}" in notes
        assert archive.sha256 in notes
    assert "THIRD-PARTY.md" in notes
    assert chr(0x2013) not in notes
    assert chr(0x2014) not in notes
    assert notes.isascii()


@pytest.mark.parametrize("tag", ["v1.5.0", "v1.4.2", "v10.0.1"])
def test_publish_refuses_a_store_release_tag(
    script: ModuleType, capsys: pytest.CaptureFixture[str], tmp_path: Path, tag: str
) -> None:
    code = script.main(["publish", "--tag", tag, "--source-dir", str(tmp_path), "--dry-run"])
    assert code != 0
    assert capsys.readouterr().out == ""
    with pytest.raises(ValueError, match="store release"):
        script.publish_commands(tag, tmp_path, release_exists=False, target="main")
