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


# ---------------------------------------------------------------------------
# 02-rechenblatt.py, the cap out of the items (D-28-01, D-28-11, D-28-14).
# ---------------------------------------------------------------------------

SHEET = V14_RUN_DIR / "02-rechenblatt.py"
SLOT_COSTS = V14_RUN_DIR / "12-slotkosten.py"

# The box hours of variant A in 28-RESEARCH.md, "Summe und Deckel", and the
# rates read on 29.09.2026, written down here and not read from the script.
RESEARCH_HOURS = {
    "m7g.large": 33.5,
    "m7g.4xlarge": 500 / 60,
    "c7a.xlarge": 19.0,
    "c7a.2xlarge": 500 / 60,
    "c7a.4xlarge": 620 / 60,
    "c7a.8xlarge": 485 / 60,
}
RATES_OF_29_09 = {
    "m7g.large": 0.115841,
    "m7g.4xlarge": 0.800141,
    "c7a.xlarge": 0.252301,
    "c7a.2xlarge": 0.486561,
    "c7a.4xlarge": 0.955081,
    "c7a.8xlarge": 1.892121,
    "geparkt": 0.013041,
}
# 45.75 h of the parked ARM disk during the x86 half, and one hour of take
# down with both disks parked.
PARKED_HOURS = 45.75 + 2.0
ANCHOR_HOURS = 275 / 60


def sheet_sum(rates: dict[str, float], *, anchor: bool = False) -> float:
    total = sum(hours * rates[box] for box, hours in RESEARCH_HOURS.items()) + PARKED_HOURS * rates["geparkt"]
    return total + (ANCHOR_HOURS * rates["m7g.large"] if anchor else 0.0)


@pytest.fixture(scope="module")
def sheet() -> ModuleType:
    return load(SHEET, "rechenblatt_02")


@pytest.fixture(scope="module")
def slot_costs() -> ModuleType:
    return load(SLOT_COSTS, "slotkosten_12")


def test_the_research_figures_come_out_of_the_items() -> None:
    """The sum of the research and the cap of D-28-01, reproduced from the items."""
    assert round(sheet_sum(RATES_OF_29_09), 2) == 45.18
    assert round(sheet_sum(RATES_OF_29_09) * 1.3, 2) == 58.74
    assert round(sheet_sum(RATES_OF_29_09, anchor=True), 2) == 45.71


def test_deckel_prints_45_18_and_58_74_with_the_rates_of_29_09() -> None:
    answer = run(SHEET, "deckel")
    assert answer.returncode == 0, answer.stderr
    lines = answer.stdout.splitlines()
    assert "summe 87.58 h 45.18 USD" in lines
    assert "deckel 113.86 h 58.74 USD" in lines
    assert "mit anker summe 92.17 h 45.71 USD" in lines
    assert "mit anker deckel 119.82 h 59.43 USD" in lines


def test_deckel_carries_one_row_per_box_and_the_anchor_as_its_own_row() -> None:
    answer = run(SHEET, "deckel")
    boxes = [line.split()[1] for line in answer.stdout.splitlines() if line.startswith("box ")]
    assert boxes == [*RESEARCH_HOURS, "geparkt"]
    assert [line for line in answer.stdout.splitlines() if line.startswith("anker ")] == [
        "anker m7g.large 4.58 h 0.53 USD"
    ]


def test_a_changed_rate_moves_the_cap() -> None:
    changed = {**RATES_OF_29_09, "c7a.8xlarge": 2.0}
    answer = run(SHEET, "deckel", "--satz", "c7a.8xlarge=2.0")
    assert answer.returncode == 0, answer.stderr
    total = sheet_sum(changed)
    assert f"summe 87.58 h {total:.2f} USD" in answer.stdout.splitlines()
    assert f"deckel 113.86 h {total * 1.3:.2f} USD" in answer.stdout.splitlines()
    assert "58.74 USD" not in answer.stdout


def test_a_rate_file_replaces_every_rate(tmp_path: Path) -> None:
    rates = {**RATES_OF_29_09, "m7g.large": 0.2}
    rate_file = tmp_path / "saetze.txt"
    rate_file.write_text("".join(f"{box} {rate}\n" for box, rate in rates.items()), encoding="utf-8")
    answer = run(SHEET, "deckel", "--satzdatei", str(rate_file))
    assert answer.returncode == 0, answer.stderr
    assert f"deckel 113.86 h {sheet_sum(rates) * 1.3:.2f} USD" in answer.stdout.splitlines()


def test_a_missing_rate_ends_the_sheet_instead_of_counting_zero(tmp_path: Path, sheet: ModuleType) -> None:
    rate_file = tmp_path / "saetze.txt"
    rate_file.write_text(
        "".join(f"{box} {rate}\n" for box, rate in RATES_OF_29_09.items() if box != "c7a.4xlarge"),
        encoding="utf-8",
    )
    answer = run(SHEET, "deckel", "--satzdatei", str(rate_file))
    assert answer.returncode == sheet.EXIT_MISSING_RATE
    assert "c7a.4xlarge" in answer.stderr
    assert "USD" not in answer.stdout


@pytest.mark.parametrize("override", ["c7a.9xlarge=1.0", "m7g.large", "m7g.large=abc", "m7g.large=-1"])
def test_a_rate_override_of_the_wrong_shape_is_refused(sheet: ModuleType, override: str) -> None:
    answer = run(SHEET, "deckel", "--satz", override)
    assert answer.returncode == sheet.EXIT_USAGE


def write_stamps(path: Path) -> Path:
    path.write_text(
        "# typ start ende\n"
        "m7g.large 2026-10-01T00:00:00Z 2026-10-01T10:00:00Z\n"
        "c7a.xlarge 2026-10-02T00:00:00Z laeuft\n",
        encoding="utf-8",
    )
    return path


def test_stand_sums_the_stamps_and_counts_the_minutes_to_the_cap(tmp_path: Path) -> None:
    stamps = write_stamps(tmp_path / "stempel.txt")
    answer = run(SHEET, "stand", str(stamps), "--deckel", "10.00", "--jetzt", "2026-10-02T02:00:00Z")
    assert answer.returncode == 0, answer.stderr
    lines = answer.stdout.splitlines()
    assert "bisher 1.66 USD" in lines
    assert "rest 8.34 USD" in lines
    assert "satz jetzt 0.252301 USD/h" in lines
    assert "minuten bis deckel 1982" in lines
    assert "minuten bis sicherheitsstopp 2458" in lines


def test_stand_names_the_reached_cap_with_its_own_code(tmp_path: Path, sheet: ModuleType) -> None:
    stamps = write_stamps(tmp_path / "stempel.txt")
    answer = run(SHEET, "stand", str(stamps), "--deckel", "1.50", "--jetzt", "2026-10-02T02:00:00Z")
    assert answer.returncode == sheet.EXIT_CAP_REACHED
    lines = answer.stdout.splitlines()
    assert "minuten bis deckel 0" in lines
    assert "minuten bis sicherheitsstopp 32" in lines
    assert "deckel erreicht" in lines


def test_stand_names_the_safety_stop_with_its_own_code(tmp_path: Path, sheet: ModuleType) -> None:
    stamps = write_stamps(tmp_path / "stempel.txt")
    answer = run(SHEET, "stand", str(stamps), "--deckel", "1.00", "--jetzt", "2026-10-02T02:00:00Z")
    assert answer.returncode == sheet.EXIT_SAFETY_STOP
    assert "sicherheitsstopp erreicht" in answer.stdout.splitlines()


@pytest.mark.parametrize(
    "line",
    [
        "m7g.large 2026-10-01T00:00:00Z",
        "m7g.large gestern laeuft",
        "c7a.9xlarge 2026-10-01T00:00:00Z laeuft",
        "m7g.large 2026-10-01T10:00:00Z 2026-10-01T00:00:00Z",
    ],
)
def test_stand_refuses_a_malformed_stamp(tmp_path: Path, sheet: ModuleType, line: str) -> None:
    stamps = tmp_path / "stempel.txt"
    stamps.write_text(line + "\n", encoding="utf-8")
    answer = run(SHEET, "stand", str(stamps), "--deckel", "10.00", "--jetzt", "2026-10-02T02:00:00Z")
    assert answer.returncode == sheet.EXIT_BAD_STAMP


def test_the_sheet_imports_the_standard_library_only_and_makes_no_aws_call() -> None:
    import ast

    text = SHEET.read_text(encoding="utf-8")
    packages: set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            packages.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            packages.add(node.module.split(".")[0])
    assert packages <= set(sys.stdlib_module_names)
    assert "subprocess" not in packages


# ---------------------------------------------------------------------------
# 12-slotkosten.py, the cost of a slot out of a proc_anon series (D-28-08).
# ---------------------------------------------------------------------------

MIB = 1024 * 1024

# epoch, pid, name, rssanon_kb, vmhwm_kb: a main process, two sandbox children,
# two tesseract, and the shells of the sampler itself, which must not count.
STAGED_SERIES = (
    (1000, 1, "init.sh", 820, 3548),
    (1000, 8, "python", 1_000_000, 1_100_000),
    (1000, 100, "python", 100_000, 120_000),
    (1000, 101, "python", 110_000, 130_000),
    (1000, 200, "tesseract", 90_000, 95_000),
    (1000, 201, "tesseract", 80_000, 85_000),
    (1000, 300, "sh", 112, 1544),
    (1001, 1, "init.sh", 820, 3548),
    (1001, 8, "python", 1_200_000, 1_250_000),
    (1001, 100, "python", 130_000, 140_000),
    (1001, 101, "python", 120_000, 135_000),
    (1001, 200, "tesseract", 100_000, 110_000),
    (1001, 201, "tesseract", 95_000, 100_000),
    (1001, 301, "sh", 112, 1544),
    (1002, 1, "init.sh", 820, 3548),
    (1002, 8, "python", 1_100_000, 1_250_000),
    (1002, 100, "python", 50_000, 140_000),
    (1002, 201, "tesseract", 60_000, 100_000),
)


def write_series(path: Path, rows: tuple[tuple[int, int, str, int, int], ...] = STAGED_SERIES) -> Path:
    lines = ["findling-anon epoch,pid,name,rssanon_kb,vmhwm_kb"]
    lines += [f"findling-anon {epoch},{pid},{name},{anon},{hwm}" for epoch, pid, name, anon, hwm in rows]
    lines.append("findling-anon summary samples=3 rows=18 max_rssanon_kb=[python=1200000] reason=signal")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_slots_reports_the_three_figures_of_the_series(tmp_path: Path) -> None:
    series = write_series(tmp_path / "anon.csv")
    answer = run(SLOT_COSTS, "slots", str(series), "--slots", "2")
    assert answer.returncode == 0, answer.stderr
    lines = answer.stdout.splitlines()
    # (a) the VmHWM pair, child plus tesseract, the measure of B2 as upper bound
    assert "slot-paar-vmhwm-kb 250000" in lines
    # the RssAnon pair, the shape of the 235 MiB of B2
    assert "slot-paar-rssanon-kb 230000" in lines
    # (b) the anon sum of children and tesseract per point in time, over the slots
    assert "slot-anon-je-slot-kb 222500 slots 2" in lines
    # (c) the main process on its own
    assert "hauptprozess-max-kb 1200000" in lines


def test_slots_reads_the_slot_count_from_the_cell_metadata(tmp_path: Path) -> None:
    series = write_series(tmp_path / "anon.csv")
    meta = tmp_path / "zelle.txt"
    meta.write_text("profil standard\npraezision int8\nslotsInForce 5\nembed_slots 1\n", encoding="utf-8")
    answer = run(SLOT_COSTS, "slots", str(series), "--meta", str(meta))
    assert answer.returncode == 0, answer.stderr
    assert "slot-anon-je-slot-kb 89000 slots 5" in answer.stdout.splitlines()


def test_slots_refuses_a_series_without_rows(tmp_path: Path, slot_costs: ModuleType) -> None:
    empty = tmp_path / "anon.csv"
    empty.write_text("findling-anon epoch,pid,name,rssanon_kb,vmhwm_kb\n", encoding="utf-8")
    answer = run(SLOT_COSTS, "slots", str(empty), "--slots", "1")
    assert answer.returncode == slot_costs.EXIT_NO_SERIES


@pytest.mark.parametrize("slots", ["0", "-1", "zwei", ""])
def test_slots_refuses_a_slot_count_that_is_no_count(tmp_path: Path, slot_costs: ModuleType, slots: str) -> None:
    series = write_series(tmp_path / "anon.csv")
    answer = run(SLOT_COSTS, "slots", str(series), "--slots", slots)
    assert answer.returncode == slot_costs.EXIT_USAGE


def test_fp32_reports_the_extra_of_the_main_process(tmp_path: Path) -> None:
    int8 = write_series(tmp_path / "int8.csv")
    heavier = tuple(
        (epoch, pid, name, anon + 375_808 if pid == 8 else anon, hwm) for epoch, pid, name, anon, hwm in STAGED_SERIES
    )
    fp32 = write_series(tmp_path / "fp32.csv", heavier)
    answer = run(SLOT_COSTS, "fp32", str(int8), str(fp32))
    assert answer.returncode == 0, answer.stderr
    lines = answer.stdout.splitlines()
    assert "fp32-mehrbedarf-kb 375808" in lines
    assert "fp32-rechnung-kb 375808" in lines


def test_the_calculation_counts_the_items_of_the_product_once(slot_costs: ModuleType) -> None:
    """Baseline, slots, parallel activations, writer growth, fp32; written out by hand."""
    baseline = 1257 * MIB + MIB // 2
    assert slot_costs.calculation("economy", 1, "int8") == baseline + 235 * MIB
    assert slot_costs.calculation("standard", 4, "int8") == baseline + 4 * 235 * MIB + 27 * MIB + 78_000_000
    assert slot_costs.calculation("performance", 15, "int8") == (baseline + 15 * 235 * MIB + 2 * 27 * MIB + 206_000_000)
    assert slot_costs.calculation("standard", 4, "fp32") == (
        baseline + 4 * 235 * MIB + 27 * MIB + 78_000_000 + 367 * MIB
    )


def test_carried_holds_exactly_at_ten_percent_and_not_one_byte_above(slot_costs: ModuleType) -> None:
    assert slot_costs.verdict(1100, 1000) == "getragen"
    assert slot_costs.verdict(1101, 1000) == "nicht getragen"
    calculation = slot_costs.calculation("standard", 4, "int8")
    limit = calculation * 11 // 10
    assert slot_costs.verdict(limit, calculation) == "getragen"
    assert slot_costs.verdict(limit + 1, calculation) == "nicht getragen"


def test_rechnung_of_one_cell_prints_its_verdict(slot_costs: ModuleType) -> None:
    calculation = slot_costs.calculation("standard", 4, "int8")
    limit = calculation * 11 // 10
    for measured, expected in ((limit, "urteil getragen"), (limit + 1, "urteil nicht getragen")):
        answer = run(
            SLOT_COSTS,
            "rechnung",
            "--profil",
            "standard",
            "--slots",
            "4",
            "--praezision",
            "int8",
            "--gemessen-bytes",
            str(measured),
        )
        assert answer.returncode == 0, answer.stderr
        lines = answer.stdout.splitlines()
        assert f"rechnung-bytes {calculation}" in lines
        assert f"grenze-bytes {limit}" in lines
        assert expected in lines


def test_rechnung_without_a_cell_prints_every_measured_cell(slot_costs: ModuleType) -> None:
    answer = run(SLOT_COSTS, "rechnung")
    assert answer.returncode == 0, answer.stderr
    rows = [line for line in answer.stdout.splitlines() if line.startswith("zelle ")]
    # 21 until 03.10.2026; cells 3, 4 and 10 struck by the owner (D-24-07).
    assert len(rows) == 18
    assert len(slot_costs.CELLS) == 18


def test_the_docstring_of_the_slot_tool_names_what_the_baseline_holds() -> None:
    head = SLOT_COSTS.read_text(encoding="utf-8").split('"""')[1]
    for item in ("MAIN_PROCESS_BASELINE_BYTES", "CUTTER_LOAD_BYTES", "EMBED_WEIGHTS_LOAD_BYTES", "EMBED_LANE_RESERVE"):
        assert item in head, item
