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

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from test_measurement_scripts import (
    V13_RUN_DIR,
    a_boxless_run,
    aborts_of,
    the_two_halves_of,
)

THROWAWAY = V13_RUN_DIR / "00-wegwerf.sh"
TYPE_SWITCH = V13_RUN_DIR / "00-typwechsel.sh"

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


# ---------------------------------------------------------------------------
# 00-typwechsel.sh, the type switch on the development machine.

# Two values that stand for the credentials in the runs below. They are no
# credentials of any account; the runs prove that neither reaches an output.
ACCESS_STAND_IN = "zugang-attrappe-0815"
SIGNING_STAND_IN = "geheim-attrappe-4711"
# The identifier the stub state file carries, and an address of a private
# range: neither may reach the raw file, where only placeholders stand.
STUB_INSTANCE = "i-attrappe"
STUB_ADDRESS = "10.0.0.1"

# The AWS command line, played by a shell script. It logs every call, keeps the
# instance type in a file and answers the queries of the tool in text form.
STUB_AWS = """#!/bin/sh
printf '%s\\n' "$*" >>"$STUB/aufrufe"
case "$*" in
*describe-instance-attribute*) printf '%s\\n' "$STUB_SHUTDOWN"; exit 0 ;;
*modify-instance-attribute*)
    [ "${STUB_KLEBT:-}" = 1 ] && exit 0
    for a in "$@"; do
        case "$a" in Value=*) printf '%s\\n' "${a#Value=}" >"$STUB/typ" ;; esac
    done
    exit 0 ;;
*InstanceType*) cat "$STUB/typ"; exit 0 ;;
*State.Name*) printf '%s\\n' "${STUB_ZUSTAND:-stopped}"; exit 0 ;;
*PublicIpAddress*) printf '%s\\n' "$STUB_ADRESSE"; exit 0 ;;
*pricing*) [ -n "${STUB_PREIS:-}" ] && cat "$STUB_PREIS"; exit 0 ;;
esac
exit 1
"""

# aws_box.sh, played the same way: stop always works, start fails for every
# type named in STUB_OHNE_KAPAZITAET, which is what a capacity shortage does.
STUB_AWS_BOX = """#!/bin/sh
printf 'aws_box %s\\n' "$1" >>"$STUB/aufrufe"
case "$1" in
stop) exit 0 ;;
start)
    typ=$(cat "$STUB/typ")
    case " ${STUB_OHNE_KAPAZITAET:-} " in *" $typ "*) exit 1 ;; esac
    exit 0 ;;
esac
exit 2
"""


def a_stubbed_switch(
    tmp_path: Path,
    arguments: list[str],
    umgebung: dict[str, str | None] | None = None,
) -> tuple[subprocess.CompletedProcess[str], Path, list[str]]:
    """00-typwechsel.sh against a stub CLI and a stub aws_box.sh, and what it left."""
    stub = tmp_path / "stub"
    stub.mkdir(parents=True)
    (stub / "typ").write_text("m7g.large\n", encoding="utf-8", newline="\n")
    (stub / "aufrufe").write_text("", encoding="utf-8", newline="\n")
    aws = tmp_path / "aws"
    aws.write_text(STUB_AWS, encoding="utf-8", newline="\n")
    aws.chmod(0o755)
    aws_box = tmp_path / "aws_box.sh"
    aws_box.write_text(STUB_AWS_BOX, encoding="utf-8", newline="\n")
    state = tmp_path / "zustand"
    state.mkdir()
    (state / "box.env").write_text(f"BOX_INSTANCE_ID={STUB_INSTANCE}\n", encoding="utf-8", newline="\n")
    out = tmp_path / "out"
    environment: dict[str, str | None] = {
        "AWS_ACCESS_KEY_ID": ACCESS_STAND_IN,
        "AWS_SECRET_ACCESS_KEY": SIGNING_STAND_IN,
        "AWS_CLI": aws.as_posix(),
        "AWS_BOX": aws_box.as_posix(),
        "FINDLING_LOADTEST_DIR": state.as_posix(),
        "STUB": stub.as_posix(),
        "STUB_SHUTDOWN": "stop",
        "STUB_ADRESSE": STUB_ADDRESS,
        **(umgebung or {}),
    }
    answer = a_boxless_run(TYPE_SWITCH, out, arguments, umgebung=environment)
    calls = (stub / "aufrufe").read_text(encoding="utf-8").splitlines()
    return answer, out / "00-typwechsel.txt", calls


def raw_of(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def switch_code() -> str:
    return code_of(TYPE_SWITCH.read_text(encoding="utf-8"))


def test_the_type_switch_says_it_never_runs_on_the_box() -> None:
    """The credentials write to EC2; the box must never see them (T-22-13)."""
    text = TYPE_SWITCH.read_text(encoding="utf-8")
    assert "NIE AUF DER BOX AUSFUEHREN" in text
    assert "die AWS-Zugangsdaten duerfen die Box nie erreichen" in text


def test_the_type_switch_turns_the_windows_path_rewriting_off() -> None:
    """Git for Windows rewrites unix looking arguments; the pattern of aws_box.sh."""
    code = switch_code()
    assert "MSYS_NO_PATHCONV=1" in code
    assert "MSYS2_ARG_CONV_EXCL='*'" in code
    assert "export MSYS_NO_PATHCONV MSYS2_ARG_CONV_EXCL" in code


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize(
    "arguments",
    [[], ["weg"], ["hin", "jetzt"], ["preis"], ["preis", "M7G.large"], ["preis", "m7g large"], ["preis", ".m7g"]],
    ids=["none", "unknown", "hin-extra", "preis-bare", "preis-upper", "preis-space", "preis-dot"],
)
def test_the_type_switch_names_four_steps_and_refuses_everything_else(tmp_path: Path, arguments: list[str]) -> None:
    """2 and the usage, before a credential is asked for and before any file."""
    answer = a_boxless_run(TYPE_SWITCH, tmp_path, arguments)
    assert answer.returncode == 2, answer
    assert "Benutzung:" in answer.stderr
    for step in ("vorpruefung", "hin", "zurueck", "preis"):
        assert step in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


def test_the_type_switch_demands_both_credentials_and_never_prints_them() -> None:
    """Two names, one mention each, and no line that echoes either of them."""
    text = TYPE_SWITCH.read_text(encoding="utf-8")
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        assert f': "${{{name}:?' in text, name
        expanding = [line for line in text.splitlines() if f"${name}" in line or f"${{{name}" in line]
        assert len(expanding) == 1, expanding
        assert not [line for line in text.splitlines() if ("echo" in line or "printf" in line) and name in line]


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("missing", ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"])
def test_the_type_switch_refuses_to_run_without_a_credential(tmp_path: Path, missing: str) -> None:
    """A missing credential ends the run before the raw file and before any call."""
    answer, raw, calls = a_stubbed_switch(tmp_path, ["vorpruefung"], umgebung={missing: None})
    assert answer.returncode != 0, answer
    assert not raw.exists()
    assert calls == []


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("behaviour", ["terminate", "", "unlesbar"])
def test_the_type_switch_ends_with_52_when_a_shutdown_would_not_be_a_stop(tmp_path: Path, behaviour: str) -> None:
    """shutdown -h is the hard stop of D-02 only where the attribute says stop."""
    answer, raw, calls = a_stubbed_switch(tmp_path, ["vorpruefung"], umgebung={"STUB_SHUTDOWN": behaviour})
    assert answer.returncode == 52, answer
    text = raw_of(raw)
    assert "shutdown-ist-stopp nein" in text
    assert "TYPWECHSEL-VORPRUEFUNG-FERTIG" not in text
    assert any("--attribute instanceInitiatedShutdownBehavior" in call for call in calls), calls
    assert not [call for call in calls if "modify-instance-attribute" in call or call.startswith("aws_box")]


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_type_switch_passes_the_precheck_for_stop(tmp_path: Path) -> None:
    answer, raw, _ = a_stubbed_switch(tmp_path, ["vorpruefung"])
    assert answer.returncode == 0, answer
    text = raw_of(raw)
    assert "shutdown-verhalten stop" in text
    assert "shutdown-ist-stopp ja" in text
    assert "TYPWECHSEL-VORPRUEFUNG-FERTIG" in text
    assert "typwechsel-vorpruefung " in text


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_type_switch_goes_there_by_stop_modify_start_and_reads_the_type_back(tmp_path: Path) -> None:
    """hin: precheck, stop, modify to m7g.4xlarge, start, read back; placeholders in the raw file."""
    answer, raw, calls = a_stubbed_switch(tmp_path, ["hin"])
    assert answer.returncode == 0, answer
    stop = calls.index("aws_box stop")
    modify = next(n for n, call in enumerate(calls) if "modify-instance-attribute" in call)
    start = calls.index("aws_box start")
    precheck = next(n for n, call in enumerate(calls) if "describe-instance-attribute" in call)
    assert precheck < stop < modify < start
    assert "Value=m7g.4xlarge" in calls[modify]
    assert any("InstanceType" in call for call in calls[start:]), calls
    text = raw_of(raw)
    for line in ("typ-gefordert m7g.4xlarge", "typ-ist m7g.4xlarge", "TYPWECHSEL-HIN-FERTIG"):
        assert line in text, line
    for step in ("hin-start", "hin-gestoppt", "hin-laeuft", "hin-ende"):
        assert f"typwechsel-{step} " in text, step
    assert "b4-rueckfall" not in text
    assert "instanz <instanzkennung>" in text
    assert "adresse-neu <adresse-der-box>" in text
    assert STUB_INSTANCE not in text
    assert STUB_ADDRESS not in text
    # The address goes to the terminal, because the A record has to follow it.
    assert STUB_ADDRESS in answer.stderr


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_type_switch_falls_back_to_the_2xlarge_without_capacity(tmp_path: Path) -> None:
    """No m7g.4xlarge in the zone: m7g.2xlarge, and the line that says so (Pitfall 9)."""
    answer, raw, calls = a_stubbed_switch(tmp_path, ["hin"], umgebung={"STUB_OHNE_KAPAZITAET": "m7g.4xlarge"})
    assert answer.returncode == 0, answer
    text = raw_of(raw)
    assert "b4-rueckfall m7g.2xlarge" in text
    assert "typ-ist m7g.2xlarge" in text
    assert "start-gescheitert typ m7g.4xlarge zustand stopped" in text
    assert calls.count("aws_box start") == 2


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_type_switch_ends_on_the_reference_type_when_neither_large_type_starts(tmp_path: Path) -> None:
    """B4 falls away (D-05), the box stays stopped on m7g.large, and the run ends with 0."""
    answer, raw, calls = a_stubbed_switch(
        tmp_path, ["hin"], umgebung={"STUB_OHNE_KAPAZITAET": "m7g.4xlarge m7g.2xlarge"}
    )
    assert answer.returncode == 0, answer
    text = raw_of(raw)
    assert "b4-entfallen kapazitaet" in text
    assert "typ-ist m7g.large" in text
    assert calls.count("aws_box start") == 2
    assert "Value=m7g.large" in [call for call in calls if "modify-instance-attribute" in call][-1]


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_type_switch_ends_with_53_when_the_type_read_back_differs(tmp_path: Path) -> None:
    """The modify was accepted and the type did not move: 53 and no end mark."""
    answer, raw, _ = a_stubbed_switch(tmp_path, ["hin"], umgebung={"STUB_KLEBT": "1"})
    assert answer.returncode == 53, answer
    text = raw_of(raw)
    assert "typ-abweichung gefordert m7g.4xlarge ist m7g.large" in text
    assert "TYPWECHSEL-HIN-FERTIG" not in text


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_type_switch_ends_with_53_when_a_failed_start_leaves_the_box_running(tmp_path: Path) -> None:
    """A start that failed with a running box is no capacity case, and no modify may follow."""
    answer, raw, calls = a_stubbed_switch(
        tmp_path, ["hin"], umgebung={"STUB_OHNE_KAPAZITAET": "m7g.4xlarge", "STUB_ZUSTAND": "running"}
    )
    assert answer.returncode == 53, answer
    assert "zustand-abweichung gefordert stopped ist running" in raw_of(raw)
    assert len([call for call in calls if "modify-instance-attribute" in call]) == 1


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_type_switch_comes_back_by_stop_and_modify_without_a_start(tmp_path: Path) -> None:
    """zurueck: stop, m7g.large, read back, no start; the uptime on the large type from the stamps."""
    first, raw, _ = a_stubbed_switch(tmp_path / "hin", ["hin"])
    assert first.returncode == 0, first
    answer, raw_back, calls = a_stubbed_switch(tmp_path / "zurueck", ["zurueck"])
    assert answer.returncode == 0, answer
    assert calls.count("aws_box stop") == 1
    assert "aws_box start" not in calls
    assert "Value=m7g.large" in next(call for call in calls if "modify-instance-attribute" in call)
    text = raw_of(raw_back)
    assert "typ-ist m7g.large" in text
    for step in ("zurueck-start", "zurueck-gestoppt", "zurueck-ende"):
        assert f"typwechsel-{step} " in text, step
    assert "TYPWECHSEL-ZURUECK-FERTIG" in text
    # Without a hin in the same raw file there is no interval to count.
    assert "b4-laufzeit-s unbestimmt" in text
    assert raw.is_file()


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_type_switch_counts_the_uptime_on_the_large_type_from_its_own_stamps(tmp_path: Path) -> None:
    """hin and zurueck into one raw file give a whole number of seconds for the hand arithmetic."""
    out = tmp_path / "gemeinsam"
    first, _, _ = a_stubbed_switch(tmp_path / "a", ["hin"], umgebung={"OUT": out.as_posix()})
    assert first.returncode == 0, first
    answer, _, _ = a_stubbed_switch(tmp_path / "b", ["zurueck"], umgebung={"OUT": out.as_posix()})
    assert answer.returncode == 0, answer
    lines = [line for line in raw_of(out / "00-typwechsel.txt").splitlines() if line.startswith("b4-laufzeit-s ")]
    assert len(lines) == 1, lines
    assert lines[0].split()[1].isdigit(), lines


def test_the_type_switch_asks_the_price_api_with_six_filters_and_loads_no_price_list() -> None:
    code = switch_code()
    command = next(line for line in commands_of(code) if "pricing get-products" in line)
    for field in ("instanceType", "location", "operatingSystem", "tenancy", "preInstalledSw", "capacitystatus"):
        assert f"Field={field}," in command, field
    assert "--service-code AmazonEC2" in command
    assert "PREIS_REGION='us-east-1'" in code
    assert "PREIS_ORT='EU (Frankfurt)'" in code
    for bulk in ("index.csv", "index.json", "offers/v1.0", "curl"):
        assert bulk not in code, bulk


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_type_switch_prints_the_one_rate_the_price_api_answers(tmp_path: Path) -> None:
    product = {
        "terms": {"OnDemand": {"X.Y": {"priceDimensions": {"X.Y.Z": {"pricePerUnit": {"USD": "0.7824000000"}}}}}}
    }
    answer_file = tmp_path / "preis.json"
    answer_file.write_text(json.dumps({"PriceList": [json.dumps(product)]}), encoding="utf-8", newline="\n")
    answer, raw, calls = a_stubbed_switch(
        tmp_path, ["preis", "m7g.4xlarge"], umgebung={"STUB_PREIS": answer_file.as_posix()}
    )
    assert answer.returncode == 0, answer
    text = raw_of(raw)
    assert "preis m7g.4xlarge 0.7824000000" in text
    assert "typwechsel-preis " in text
    assert any("--region us-east-1" in call and "Value=m7g.4xlarge" in call for call in calls), calls


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_type_switch_ends_red_when_the_price_api_gives_no_rate(tmp_path: Path) -> None:
    """The account may lack pricing:GetProducts; then the line says unlesbar and the run is not green."""
    answer, raw, _ = a_stubbed_switch(tmp_path, ["preis", "m7g.4xlarge"])
    assert answer.returncode == 1, answer
    text = raw_of(raw)
    assert "preis m7g.4xlarge unlesbar" in text
    assert "TYPWECHSEL-PREIS-FERTIG" not in text


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("step", [["vorpruefung"], ["hin"], ["zurueck"], ["preis", "m7g.large"]], ids=str)
def test_the_type_switch_never_prints_a_credential(tmp_path: Path, step: list[str]) -> None:
    """Neither value reaches stdout, stderr or the raw file, on any step (T-22-13)."""
    answer, raw, calls = a_stubbed_switch(tmp_path, step)
    for sentinel in (ACCESS_STAND_IN, SIGNING_STAND_IN):
        assert sentinel not in answer.stdout
        assert sentinel not in answer.stderr
        assert sentinel not in raw_of(raw)
        assert not [call for call in calls if sentinel in call]


def test_the_type_switch_goes_through_aws_box_for_stop_and_start() -> None:
    code = switch_code()
    assert 'AWS_BOX="${AWS_BOX:-$REPO/scripts/ops/aws_box.sh}"' in code
    assert 'sh "$AWS_BOX" "$@" >&2' in code
    for forbidden in ("stop-instances", "start-instances", "terminate-instances"):
        assert forbidden not in code, forbidden
    assert {"exit 52", "exit 53"} <= aborts_of(code)
