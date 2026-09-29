"""The measuring ladder of SC3 (D-26-09), without tesseract and without the image.

scripts/ops/slot_ladder.py runs the real poller inside the product image on
the arm64 runner. What can be held here is everything around that run: the
arguments, the lines it prints, that none of them carries a name or a text,
that the product is imported late, and the fake work stock the poller talks
to, whose trim and hand back decide how many rows a pass gets.
"""

from __future__ import annotations

import ast
import asyncio
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

LADDER = Path(__file__).resolve().parents[2] / "scripts" / "ops" / "slot_ladder.py"
LADDER_MODULE = "findling_slot_ladder"

# A directory and a file name no line of the report may ever repeat.
MARKED_DIR = "Mandant-Beispielhausen-vertraulich"
MARKED_FILE = "Kuendigung-Familie-Beispiel.pdf"


def ladder_module() -> ModuleType:
    """The tool, loaded from its path like test_ops_scripts.py loads the slot probe."""
    specification = importlib.util.spec_from_file_location(LADDER_MODULE, LADDER)
    assert specification is not None, LADDER
    assert specification.loader is not None, LADDER
    module = importlib.util.module_from_spec(specification)
    sys.modules[LADDER_MODULE] = module
    specification.loader.exec_module(module)
    return module


def test_the_arguments_ask_for_slots_and_a_corpus(tmp_path: Path) -> None:
    ladder = ladder_module()
    parsed = ladder.parse_args(["--slots", "4", "--scan-dir", str(tmp_path)])
    assert parsed.slots == 4
    assert parsed.rounds == 3
    assert parsed.mode == "poller"
    assert parsed.scan_dir == tmp_path
    assert ladder.parse_args(["--slots", "2", "--scan-dir", str(tmp_path), "--mode", "embed"]).mode == "embed"
    for broken in (
        ["--scan-dir", str(tmp_path)],
        ["--slots", "0", "--scan-dir", str(tmp_path)],
        ["--slots", "17", "--scan-dir", str(tmp_path)],
        ["--slots", "2"],
        ["--slots", "2", "--scan-dir", str(tmp_path), "--mode", "raw"],
        ["--slots", "2", "--scan-dir", str(tmp_path), "--rounds", "0"],
    ):
        assert ladder.main(broken) == 2, broken


def test_a_round_is_one_line_of_numbers() -> None:
    ladder = ladder_module()
    item = ladder.Round(number=2, slots=4, pages=48, seconds=12.0, failed=0)
    assert ladder.format_round(item) == ("round 2 slots 4 pages 48 seconds 12.000 pages_per_second 4.000 failed 0")


def test_the_median_is_undetermined_after_a_lost_scan() -> None:
    ladder = ladder_module()
    rounds = [
        ladder.Round(number=1, slots=2, pages=48, seconds=24.0, failed=0),
        ladder.Round(number=2, slots=2, pages=48, seconds=16.0, failed=0),
        ladder.Round(number=3, slots=2, pages=48, seconds=12.0, failed=0),
    ]
    assert ladder.summarize(rounds) == "pages_per_second_median 3.000"
    broken = [*rounds[:2], ladder.Round(number=3, slots=2, pages=40, seconds=12.0, failed=1)]
    assert ladder.summarize(broken) == "pages_per_second_median unbestimmt"
    assert ladder.summarize([]) == "pages_per_second_median unbestimmt"


def test_the_embed_mode_reports_one_and_two_slots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ladder = ladder_module()
    asked: list[Any] = []

    def staged(variants: list[int], rounds: int) -> dict[int, list[float]]:
        asked.append((list(variants), rounds))
        return {1: [8.0, 8.0, 8.0], 2: [5.0, 4.0, 6.0]}

    monkeypatch.setattr(ladder, "measure_embed", staged)
    assert ladder.main(["--mode", "embed", "--slots", "2", "--scan-dir", str(tmp_path)]) == 0
    printed = capsys.readouterr().out.splitlines()
    assert asked == [([1, 2], 3)]
    assert "embed_slots 1 passages_per_second 8.000" in printed
    assert "embed_slots 2 passages_per_second 12.800" in printed
    assert ladder.embed_lines("aarch64", 4, 64, {1: [0.0], 2: [0.0]})[-1] == (
        "embed_slots 2 passages_per_second unbestimmt"
    )


def test_the_report_names_no_file_and_quotes_no_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ladder = ladder_module()
    corpus = tmp_path / MARKED_DIR
    corpus.mkdir()
    (corpus / MARKED_FILE).write_bytes(b"%PDF-1.4\n")
    extracted = "Grundstuecksverkehrsgenehmigung der Familie Beispiel"
    seen: list[Any] = []

    def staged(rows: list[Any], slots: int, rounds: int) -> tuple[list[Any], int]:
        seen.append((rows, slots, rounds))
        return [ladder.Round(number=1, slots=slots, pages=1, seconds=2.0, failed=0)], 0

    monkeypatch.setattr(ladder, "measure_ladder", staged)
    assert ladder.main(["--slots", "1", "--rounds", "1", "--scan-dir", str(corpus)]) == 0
    captured = capsys.readouterr()
    report = captured.out + captured.err
    assert seen[0][1:] == (1, 1)
    assert [row.path.name for row in seen[0][0]] == [MARKED_FILE]
    assert MARKED_DIR not in report
    assert MARKED_FILE not in report
    assert "Kuendigung" not in report
    assert extracted not in report
    assert "pages_per_second_median 0.500" in report


def test_the_tool_loads_without_importing_the_product(tmp_path: Path) -> None:
    """In a fresh interpreter, where findling is importable and nothing has imported it yet."""
    code = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location({LADDER_MODULE!r}, {LADDER.as_posix()!r})\n"
        "module = importlib.util.module_from_spec(spec)\n"
        f"sys.modules[{LADDER_MODULE!r}] = module\n"
        "spec.loader.exec_module(module)\n"
        f"code = module.main(['--slots', '0', '--scan-dir', {tmp_path.as_posix()!r}])\n"
        "print(code, 'findling' in sys.modules)\n"
    )
    finished = subprocess.run(  # noqa: S603 - fixed argument list, no shell string
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=60, check=False
    )
    assert finished.returncode == 0, finished.stderr
    assert finished.stdout.split() == ["2", "False"], finished.stdout
    top_level: set[str] = set()
    for node in ast.parse(LADDER.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Import):
            top_level.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            top_level.add(node.module.split(".")[0])
    assert not top_level - set(sys.stdlib_module_names), sorted(top_level)


def test_the_fake_stock_trims_and_hands_back_like_the_companion(tmp_path: Path) -> None:
    ladder = ladder_module()
    rows = [
        ladder.LadderRow(queue_id=1000 + index, file_id=5000 + index, size=100, path=tmp_path / f"{index}.pdf")
        for index in range(6)
    ]
    queue = ladder.LadderQueue(rows)

    async def scenario() -> None:
        first = await queue.claim(limit=32, max_bytes=250)
        # The byte budget cuts after two rows, and the cut is counted.
        assert [job.queue_id for job in first.jobs] == [1000, 1001]
        assert queue.byte_capped == 1
        assert all(job.kind == "ocr" for job in first.jobs)
        # A trimmed row goes back to the front, before the rows never claimed.
        assert (await queue.unlock([1001])).count == 1
        second = await queue.claim(limit=2, max_bytes=10_000)
        assert [job.queue_id for job in second.jobs] == [1001, 1002]
        await queue.acknowledge([1000, 1001], {1002: "ocr_failed"})
        assert queue.failed == {1002: "ocr_failed"}
        # One row alone always comes, whatever the budget.
        lone = await queue.claim(limit=32, max_bytes=1)
        assert [job.queue_id for job in lone.jobs] == [1003]
        assert (await queue.requeue([5003], kind="embed")).count == 1
        rest = await queue.claim(limit=32, max_bytes=10_000)
        await queue.acknowledge([job.queue_id for job in rest.jobs], {})
        assert not queue.pending

    asyncio.run(scenario())
