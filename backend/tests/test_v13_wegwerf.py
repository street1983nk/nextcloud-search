"""The watchmen over the throwaway blocks and the type switch of the v1.3 trip, plan 22-04.

00-wegwerf.sh drives B3, B5 and B4 of the BL-F04 groundwork on the box, each in
a throwaway container of the same digest, and 00-typwechsel.sh switches the
instance type for B4 on the development machine and checks beforehand that a
shutdown from inside the box is a stop and not a terminate (D-02, assumption
A2). Neither has run yet, and section 7.1 of the runbook says no tool is
changed during the paid trip, so what can be held without a box is held here.

The house rules of the directory (shebang, no carriage return, no dash, no
machine path, no password on a command line) come from test_measurement_scripts
through NARROW_SCOPE_DIRS; this file holds what is particular to each tool.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from test_measurement_scripts import (
    V13_RUN_DIR,
    a_boxless_run,
    aborts_of,
    the_two_halves_of,
)

THROWAWAY = V13_RUN_DIR / "00-wegwerf.sh"

# A digest of the right shape. It names no image anywhere, and none of the
# boxless runs below gets as far as asking for one.
A_DIGEST = "sha256:" + "0" * 64


def code_of(text: str) -> str:
    """The lines of a shell file that are not comments."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def commands_of(code: str) -> list[str]:
    """The code as commands: every backslash continuation joined into one line."""
    return code.replace("\\\n", " ").splitlines()


def function_of(code: str, name: str) -> str:
    """The body of one shell function, from its head to the closing brace."""
    start = code.index(f"{name}() {{")
    return code[start : code.index("\n}\n", start)]


def throwaway_code() -> str:
    return code_of(THROWAWAY.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 00-wegwerf.sh, the throwaway blocks.


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("arguments", [[], ["b6"], ["B3"], ["b3", "b4"]], ids=["none", "b6", "B3", "two"])
def test_the_throwaway_runner_names_three_blocks_and_refuses_everything_else(
    tmp_path: Path, arguments: list[str]
) -> None:
    """No block, an unknown one or two of them end with 2, before any docker call and any file."""
    answer = a_boxless_run(THROWAWAY, tmp_path, arguments, umgebung={"ABBILD_DIGEST": A_DIGEST})
    assert answer.returncode == 2, answer
    assert "Benutzung:" in answer.stderr
    for block in ("b3", "b5", "b4"):
        assert block in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize(
    "digest",
    [None, "", "latest", "sha256:", "sha256:" + "0" * 63, "sha256:" + "g" * 64, "sha256:" + "0" * 65],
    ids=["absent", "empty", "tag", "bare", "short", "not-hex", "long"],
)
def test_the_throwaway_runner_refuses_a_run_without_a_digest(tmp_path: Path, digest: str | None) -> None:
    """A throwaway container of another digest measures another image."""
    answer = a_boxless_run(THROWAWAY, tmp_path, ["b3"], umgebung={"ABBILD_DIGEST": digest})
    assert answer.returncode == 2, answer
    assert "ABBILD_DIGEST" in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


def test_the_throwaway_runner_isolates_every_docker_run() -> None:
    """--network none, an explicit cpu set and the one image, at every docker run (T-22-16)."""
    runs = [command for command in commands_of(throwaway_code()) if "docker run" in command]
    assert len(runs) >= 5, runs
    for command in runs:
        assert "--network none" in command, command
        assert "--cpuset-cpus" in command, command
        assert '"$IMAGE"' in command, command
    text = THROWAWAY.read_text(encoding="utf-8")
    assert text.count("--network none") >= text.count("docker run")
    assert 'IMAGE="$ABBILD_REPO@$ABBILD_DIGEST"' in text


def test_the_throwaway_runner_drives_b3_on_two_cores_under_2g() -> None:
    """N 1 and 2 on cpu set 0,1 under 2g with three rounds, then the single mode."""
    code = throwaway_code()
    b3 = function_of(code, "b3_fahren")
    assert "for slots in 1 2; do" in b3
    assert 'slots_fahren "$slots" 0,1 "$OUT/b3-slots-$slots.txt" --memory 2g' in b3
    single = next(command for command in commands_of(b3) if "--mode single" in command)
    assert "--cpuset-cpus 0,1 --memory 2g" in single
    assert "--rounds 3" in single
    assert '"$OUT/b3-single.txt"' in single
    probe = next(command for command in commands_of(function_of(code, "slots_fahren")) if "docker run" in command)
    assert "/ops/ocr_slot_probe.py --slots" in probe
    assert "--rounds 3 --scan /scan/scan-8.pdf" in probe


def test_the_throwaway_runner_drives_b5_in_four_combinations_beside_the_sampler() -> None:
    """threads 1 and 2, batch 2 and 8, sequence 512, cpu set 0,1, rss_sampler.sh on the bench name."""
    text = THROWAWAY.read_text(encoding="utf-8")
    assert 'SAMPLER="${SAMPLER:-$REPO/scripts/ops/rss_sampler.sh}"' in text
    code = code_of(text)
    b5 = function_of(code, "b5_fahren")
    assert "for threads in 1 2; do" in b5
    assert "for batch in 2 8; do" in b5
    combination = function_of(code, "kombination_fahren")
    run = next(command for command in commands_of(combination) if "docker run" in command)
    assert '--name "$bank"' in run
    assert "--cpuset-cpus 0,1" in run
    assert '--batch "$batch" --sequence 512 --threads "$threads"' in run
    assert "-m findling.embed.bench --mode tokens-per-second" in run
    # The sampler is called as it is, against exactly the name of the bench.
    assert 'sudo "$SAMPLER" "$bank" "$ABTASTINTERVALL" "$reihe"' in combination
    assert '"$OUT/b5-max-anon-threads-$threads-batch-$batch.txt"' in combination
    assert 'datei="$OUT/b5-threads-$threads-batch-$batch.txt"' in combination


def test_the_throwaway_runner_drives_b4_up_to_the_visible_cores_and_says_where_it_cut() -> None:
    """N 1 to 16 and T 1 to 8, trimmed to nproc, the trim as a line, no memory limit."""
    text = THROWAWAY.read_text(encoding="utf-8")
    assert 'B4_SLOTS="1 2 4 8 12 16"' in text
    assert 'B4_THREADS="1 2 4 8"' in text
    code = code_of(text)
    b4 = function_of(code, "b4_fahren")
    assert "kerne=$(nproc)" in b4
    assert 'if [ "$slots" -le "$kerne" ]; then' in b4
    assert 'if [ "$threads" -le "$kerne" ]; then' in b4
    assert 'protokoll "b4-gekuerzt-auf $kerne"' in b4
    assert 'protokoll "b4-grenze keine"' in b4
    assert 'slots_fahren "$slots" "$(cpuset_bis "$slots")" "$OUT/b4-slots-$slots.txt"' in b4
    bench = next(command for command in commands_of(b4) if "docker run" in command)
    assert '--cpuset-cpus "$kerne_t"' in bench
    assert "--memory" not in bench
    assert '--batch 2 --sequence 512 --threads "$threads"' in bench
    assert '"$OUT/b4-bench-$threads.txt"' in bench
    assert "--memory" not in b4
    assert "B4-FERTIG" in code


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize(("width", "expected"), [(1, "0"), (2, "0-1"), (8, "0-7"), (16, "0-15")])
def test_the_throwaway_runner_builds_the_cpu_set_from_zero(tmp_path: Path, width: int, expected: str) -> None:
    """cpuset_bis, run as it stands in the file, and not a copy of it."""
    code = throwaway_code()
    helper = function_of(code, "cpuset_bis") + "\n}\n"
    script = tmp_path / "helfer.sh"
    script.write_text(f'{helper}cpuset_bis "$1"\n', encoding="utf-8", newline="\n")
    answer = a_boxless_run(script, tmp_path / "out", [str(width)])
    assert answer.returncode == 0, answer
    assert answer.stdout.strip() == expected


def test_the_throwaway_runner_checks_the_idle_product_before_b3_and_b5_and_ends_with_50() -> None:
    """Work stock 0 and runState idle before the first probe, 50 below the tee (Pitfall 12)."""
    text = THROWAWAY.read_text(encoding="utf-8")
    code = code_of(text)
    check = function_of(code, "leerlauf_pruefen")
    assert "occ findling:index" in check
    assert 'if [ "$vorrat" = 0 ] && [ "$zustand" = idle ]; then' in check
    assert '>>"$WORK/nicht-im-leerlauf"' in check
    assert '"runState"' in function_of(code, "laufzustand")
    for block, first_probe in (("b3_fahren", "slots_fahren"), ("b5_fahren", "kombination_fahren")):
        body = function_of(code, block)
        assert body.index("leerlauf_pruefen") < body.index(first_probe), block
    above, below = the_two_halves_of(text)
    assert below, "00-wegwerf lost its pipeline"
    assert aborts_of(above) == {"exit 2"}
    assert {"exit 50", "exit 51"} <= aborts_of(below)
    block = below[below.index('if [ -f "$WORK/nicht-im-leerlauf" ]; then') :]
    assert block.split("\nfi\n")[0].rstrip().endswith("exit 50")
    block = below[below.index('if [ -f "$WORK/b4-nicht-frei" ]; then') :]
    assert block.split("\nfi\n")[0].rstrip().endswith("exit 51")
    assert 'if [ "$laufend" != 0 ]; then' in function_of(code, "b4_fahren")


def test_the_throwaway_runner_ends_red_without_a_number_or_its_end_mark() -> None:
    """A probe without its closing number and a block without its end mark never end with 0."""
    text = THROWAWAY.read_text(encoding="utf-8")
    code = code_of(text)
    assert 'probe_pruefen "$datei" pages_per_second_median' in code
    assert "tokens_per_second_p50" in function_of(code, "bench_pruefen")
    _, below = the_two_halves_of(text)
    assert 'if [ -f "$WORK/probe-ohne-zahl" ]; then' in below
    assert 'if [ ! -f "$WORK/block-durchgelaufen" ]; then' in below
    assert below.index("block-durchgelaufen") < below.index("B4-FERTIG")


def test_the_throwaway_runner_leaves_the_product_container_alone() -> None:
    """No create, no restart, no rebuild, no environment tool, and rm only for the bench."""
    code = throwaway_code()
    for forbidden in (
        "docker create",
        "docker restart",
        "docker update",
        "docker stop",
        "docker start",
        "docker kill",
        "92e",
        "92d",
        "app_api:app",
        "findling:index --restart",
    ):
        assert forbidden not in code, forbidden
    removals = [command for command in commands_of(code) if "docker rm" in command]
    assert removals
    for command in removals:
        assert '"$bank"' in command, command
        assert "$CONTAINER" not in command, command
    touching = [command for command in commands_of(code) if "$CONTAINER" in command]
    assert touching
    for command in touching:
        assert "docker inspect" in command, command


def test_the_throwaway_runner_builds_its_scan_out_of_the_generator_and_never_a_user_file() -> None:
    """build_load_corpus.py with a fixed seed in a throwaway container; no user path is mounted."""
    text = THROWAWAY.read_text(encoding="utf-8")
    code = code_of(text)
    scan = function_of(code, "scan_bauen")
    assert "import build_load_corpus as corpus" in scan
    assert "corpus._scan_pdf(corpus.Rng('$SCAN_SEED', 'scan-8'), 8)" in scan
    assert 'SCAN_SEED="${SCAN_SEED:-phase-22-w4}"' in text
    assert "/mnt/ncdata" not in text
    mounts = [piece for command in commands_of(code) for piece in command.split(" -v ")[1:]]
    assert mounts
    for mount in mounts:
        assert "files/" not in mount, mount
        assert "ncdata" not in mount, mount
    assert 'SCAN_DIR=$(mktemp -d "$WORK/scan.XXXXXX")' in code
