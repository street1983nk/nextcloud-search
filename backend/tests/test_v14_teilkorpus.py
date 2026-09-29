"""The boxless promises of the offline ground of the acceptance trip, plan 28-01.

01-teilkorpus.py fixes the part of the snapshot corpus every cell of phase 28
measures (D-28-06, D-28-09). None of the tools of this plan has run on a box
yet, and section 7.1 of the runbook says no tool is changed during the paid
trip, so what can be held without a box is held here.

The house rules of the directory (shebang, no carriage return, no dash, no
machine path, no password on a command line) come from test_measurement_scripts
through NARROW_SCOPE_DIRS; this file holds what is particular to each tool.
"""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from test_measurement_scripts import REPO_ROOT, V14_RUN_DIR

SUBSET = V14_RUN_DIR / "01-teilkorpus.py"
CORPUS_BUILDER = REPO_ROOT / "scripts" / "dev" / "build_load_corpus.py"

# The rule of D-28-09, written down and not read from the script: a test that
# recomputes the rule it guards agrees with itself whatever the rule says.
EXPECTED_COUNTS = {
    "scan_single": 1800,
    "scan_multi": 100,
    "text_pdf": 1500,
    "ooxml": 900,
    "opendocument": 400,
    "plain_text": 200,
    "image": 100,
    "oversize": 0,
}
EXPECTED_RANGES = {
    "scan_single": (1, 1800),
    "scan_multi": (9917, 10016),
    "text_pdf": (10017, 11516),
    "ooxml": (32553, 33452),
    "opendocument": (42569, 42968),
    "plain_text": (47577, 47776),
    "image": (49881, 49980),
}
EXPECTED_FILES = 5000
EXPECTED_PAGES = 2691


def load(path: Path, name: str) -> ModuleType:
    """A script as a module; its file name begins with a digit, so no import statement reaches it."""
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def subset() -> ModuleType:
    return load(SUBSET, "teilkorpus_01")


@pytest.fixture(scope="module")
def builder() -> ModuleType:
    return load(CORPUS_BUILDER, "build_load_corpus_for_v14")


def run(script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """The script as a program, the way the box runs it."""
    return subprocess.run(  # noqa: S603 - an argument list, never a shell
        [sys.executable, str(script), *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


# ---------------------------------------------------------------------------
# 01-teilkorpus.py, the rule.
# ---------------------------------------------------------------------------


def test_the_rule_counts_are_those_of_d_28_09(subset: ModuleType) -> None:
    counts = {key: len(indices) for key, indices in subset.selection().items()}
    assert counts == EXPECTED_COUNTS
    assert sum(counts.values()) == EXPECTED_FILES


def test_the_rule_takes_the_first_n_of_each_category(subset: ModuleType) -> None:
    chosen = subset.selection()
    for key, (first, last) in EXPECTED_RANGES.items():
        assert chosen[key] == list(range(first, last + 1)), key
    assert chosen["oversize"] == []


def test_the_ranges_of_the_script_are_those_of_allocate(subset: ModuleType, builder: ModuleType) -> None:
    """The box has no Pillow, so the script carries the ranges; they must be allocate(50000)."""
    counts = builder.allocate(50000)
    start = 1
    expected: dict[str, tuple[int, int]] = {}
    for category in builder.CATEGORIES:
        expected[category.key] = (start, start + counts[category.key] - 1)
        start += counts[category.key]
    assert dict(subset.SNAPSHOT_RANGES) == expected
    assert [key for key, _ in subset.SNAPSHOT_RANGES] == [category.key for category in builder.CATEGORIES]


def test_the_ocr_pages_add_up_to_2691(subset: ModuleType) -> None:
    assert subset.ocr_pages() == EXPECTED_PAGES


def test_the_page_draw_of_the_script_is_that_of_the_builder(subset: ModuleType, builder: ModuleType) -> None:
    """The copied draw has to agree with the generator file by file, not only in the sum."""
    assert tuple(subset.SCAN_PAGE_BANDS) == tuple(builder.SCAN_PAGE_BANDS)
    first, last = EXPECTED_RANGES["scan_multi"]
    for index in range(first, last + 1):
        rng = builder.Rng(subset.SEED, "scan_multi", index)
        rng.pick(("pdf",))
        rng.pick(builder.SLUGS)
        assert subset.multi_page_count(index) == builder._scan_page_count(rng), index


def test_auswahl_names_5000_files_and_2691_pages_in_its_last_line() -> None:
    answer = run(SUBSET, "auswahl")
    assert answer.returncode == 0, answer.stderr
    lines = answer.stdout.splitlines()
    assert lines[-1] == "teilkorpus dateien 5000 ocr-seiten 2691"
    prefixes = [line for line in lines if line.isdigit()]
    assert len(prefixes) == EXPECTED_FILES
    assert prefixes[0] == "00001"
    assert prefixes[-1] == "49980"


# ---------------------------------------------------------------------------
# liste, hardlinks, zaehltor against a staged corpus.
# ---------------------------------------------------------------------------


def stage_corpus(root: Path, subset: ModuleType, *, leave_out: str | None = None) -> None:
    """Every file of the rule plus a few outside it, as tiny files with the snapshot's name shape."""
    root.mkdir(parents=True)
    for prefix in subset.prefixes():
        if prefix == leave_out:
            continue
        (root / f"{prefix}-akte.pdf").write_bytes(prefix.encode("ascii"))
    for outside in ("01801", "49981", "50000"):
        (root / f"{outside}-akte.pdf").write_bytes(b"outside")


def test_liste_writes_a_sorted_list_and_its_checksum(tmp_path: Path, subset: ModuleType) -> None:
    root = tmp_path / "loadtest"
    stage_corpus(root, subset)
    answer = run(SUBSET, "liste", str(root))
    assert answer.returncode == 0, answer.stderr
    lines = answer.stdout.splitlines()
    assert lines[0] == "name,bytes,sha256"
    rows = lines[1:-1]
    assert len(rows) == EXPECTED_FILES
    assert rows == sorted(rows)
    first = rows[0].split(",")
    assert first == ["00001-akte.pdf", "5", hashlib.sha256(b"00001").hexdigest()]
    checksum = hashlib.sha256("\n".join(rows).encode("ascii")).hexdigest()
    assert lines[-1] == f"listen-pruefsumme {checksum}"
    # Only file names leave the tool, never the path of the machine.
    assert str(tmp_path) not in answer.stdout
    assert tmp_path.as_posix() not in answer.stdout


def test_liste_ends_with_its_own_code_when_a_file_of_the_rule_is_missing(tmp_path: Path, subset: ModuleType) -> None:
    root = tmp_path / "loadtest"
    stage_corpus(root, subset, leave_out="09950")
    answer = run(SUBSET, "liste", str(root))
    assert answer.returncode == subset.EXIT_MISSING
    assert answer.returncode not in {0, 1, 2}
    assert "09950" in answer.stderr


def test_liste_refuses_a_prefix_that_matches_two_files(tmp_path: Path, subset: ModuleType) -> None:
    root = tmp_path / "loadtest"
    stage_corpus(root, subset)
    (root / "00002-doppelt.txt").write_bytes(b"x")
    answer = run(SUBSET, "liste", str(root))
    assert answer.returncode == subset.EXIT_AMBIGUOUS


def test_hardlinks_links_exactly_the_rule(tmp_path: Path, subset: ModuleType) -> None:
    source = tmp_path / "loadtest"
    target = tmp_path / "teilkorpus"
    stage_corpus(source, subset)
    answer = run(SUBSET, "hardlinks", str(source), str(target))
    assert answer.returncode == 0, answer.stderr
    linked = sorted(path.name for path in target.iterdir())
    assert len(linked) == EXPECTED_FILES
    assert "01801-akte.pdf" not in linked
    one = target / "00001-akte.pdf"
    assert one.stat().st_ino == (source / "00001-akte.pdf").stat().st_ino or sys.platform == "win32"
    assert one.read_bytes() == b"00001"
    assert answer.stdout.splitlines()[-1] == "hardlinks angelegt 5000"


def test_hardlinks_dry_run_prints_the_cp_commands_and_touches_nothing(tmp_path: Path, subset: ModuleType) -> None:
    source = tmp_path / "loadtest"
    target = tmp_path / "teilkorpus"
    stage_corpus(source, subset)
    answer = run(SUBSET, "hardlinks", "--trocken", str(source), str(target))
    assert answer.returncode == 0, answer.stderr
    commands = [line for line in answer.stdout.splitlines() if line.startswith("cp -al ")]
    assert len(commands) == EXPECTED_FILES
    assert not target.exists()


def test_hardlinks_refuses_a_target_that_is_not_empty(tmp_path: Path, subset: ModuleType) -> None:
    source = tmp_path / "loadtest"
    target = tmp_path / "teilkorpus"
    stage_corpus(source, subset)
    target.mkdir()
    (target / "fremd.txt").write_bytes(b"x")
    answer = run(SUBSET, "hardlinks", str(source), str(target))
    assert answer.returncode == subset.EXIT_TARGET_NOT_EMPTY


def test_hardlinks_ends_with_the_missing_code_before_linking_anything(tmp_path: Path, subset: ModuleType) -> None:
    source = tmp_path / "loadtest"
    target = tmp_path / "teilkorpus"
    stage_corpus(source, subset, leave_out="49980")
    answer = run(SUBSET, "hardlinks", str(source), str(target))
    assert answer.returncode == subset.EXIT_MISSING
    assert not target.exists() or not any(target.iterdir())


@pytest.mark.parametrize(("count", "passes"), [("5000", True), ("4999", False), ("5001", False), ("0", False)])
def test_zaehltor_passes_exactly_5000(subset: ModuleType, count: str, passes: bool) -> None:
    answer = run(SUBSET, "zaehltor", count)
    if passes:
        assert answer.returncode == 0, answer.stderr
        assert answer.stdout.strip() == "zaehltor bestanden 5000"
    else:
        assert answer.returncode == subset.EXIT_COUNT_GATE
        assert "zaehltor verfehlt" in answer.stdout


@pytest.mark.parametrize("count", ["", "fuenf", "-1", "5000.0"])
def test_zaehltor_refuses_what_is_not_a_count(subset: ModuleType, count: str) -> None:
    answer = run(SUBSET, "zaehltor", count)
    assert answer.returncode == subset.EXIT_USAGE


def test_the_exit_codes_are_named_in_the_head_of_the_file(subset: ModuleType) -> None:
    head = SUBSET.read_text(encoding="utf-8").split('"""')[1]
    for code in (subset.EXIT_USAGE, subset.EXIT_MISSING, subset.EXIT_AMBIGUOUS, subset.EXIT_TARGET_NOT_EMPTY):
        assert f"\n  {code} " in head, code
    assert f"\n  {subset.EXIT_COUNT_GATE} " in head


def test_the_subset_tool_imports_the_standard_library_only() -> None:
    """The host python of the box runs it, and it carries no third party package."""
    import ast

    tree = ast.parse(SUBSET.read_text(encoding="utf-8"))
    packages: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            packages.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            packages.add(node.module.split(".")[0])
    assert packages <= set(sys.stdlib_module_names)
