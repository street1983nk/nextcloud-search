"""The watchmen over the two cycle tools of the v1.3 trip, plan 22-03.

94c measures the residue of the embedding engine over two cycles in one
container life (MESS-07 point 3), 95c measures the cold start latency with a
first search that has to find something (MESS-07 point 5). Neither of them has
run yet, and section 7.1 of the runbook says no tool is changed during the paid
trip, so everything about them that can be held without a box is held here.

The house rules of the directory (shebang, no carriage return, no dash, no
machine path, no password on a command line) come from test_measurement_scripts
through NARROW_SCOPE_DIRS; this file holds what is particular to each tool.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from test_measurement_scripts import (
    BASELOAD_RETURN_ABORTS,
    NOT_DRIVEN,
    V12_BASELOAD_RETURN,
    V12_REWARM,
    V12_RUN_DIR,
    V13_RUN_DIR,
    a_boxless_run,
    aborts_of,
    the_two_halves_of,
)

RESIDUE_CYCLES = V13_RUN_DIR / "94c-bodensatz-zyklen.sh"
COLD_START = V13_RUN_DIR / "95c-kaltstart.sh"

# The three commands that would make two marks the marks of two container lives.
# A rebuild through the environment tool is the third one, and it is named by
# its file.
REBUILDS = ("docker create", "docker rm", "92e-umgebung")


def code_of(text: str) -> str:
    """The lines of a shell file that are not comments."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def lines_that_run(code: str) -> list[str]:
    """The code lines that are not a message: echo and printf only quote a name."""
    return [line for line in code.splitlines() if not line.strip().startswith(("echo", "printf"))]


# ---------------------------------------------------------------------------
# 94c, the residue over two cycles.


def test_the_residue_cycles_name_their_predecessor_and_say_they_never_ran() -> None:
    """94c follows 94b, says so with the full path, and 94b stays where it is."""
    text = RESIDUE_CYCLES.read_text(encoding="utf-8")
    assert "docs/measurements/2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh" in text
    assert NOT_DRIVEN in text
    assert V12_BASELOAD_RETURN.is_file()
    assert RESIDUE_CYCLES.parent != V12_RUN_DIR


def test_the_residue_cycles_take_three_marks_and_print_both_differences() -> None:
    """Mark A, C1 and C2, and the two lines the verdict of MESS-07 point 3 hangs on."""
    code = code_of(RESIDUE_CYCLES.read_text(encoding="utf-8"))
    for mark in ("marke marke-a", "marke marke-c1", "marke marke-c2"):
        assert mark in code, mark
    assert code.index("marke marke-a") < code.index("zyklus 1") < code.index("marke marke-c1")
    assert code.index("marke marke-c1") < code.index("zyklus 2") < code.index("marke marke-c2")
    assert 'protokoll "zyklus2-minus-a $(differenz_mb "$C2" "$A")"' in code
    assert 'protokoll "zyklus2-minus-c1 $(differenz_mb "$C2" "$C1")"' in code


def test_the_residue_cycles_rebuild_nothing_between_c1_and_c2() -> None:
    """One container life from mark A to mark C2 (T-22-12).

    Between the two marks no line creates, removes or rebuilds the container.
    The rest of the file is held to the same rule, because the cycle between C1
    and C2 is a function defined above both marks: a gate that read only the
    lines between the two calls would read one call and nothing else.
    """
    code = code_of(RESIDUE_CYCLES.read_text(encoding="utf-8"))
    between = code[code.index("marke marke-c1") : code.index("marke marke-c2")]
    for rebuild in REBUILDS:
        assert rebuild not in between, rebuild
    running = "\n".join(lines_that_run(code))
    for rebuild in REBUILDS:
        assert rebuild not in running, rebuild
    # The one restart stands in front of mark A and nowhere else.
    restarts = [line for line in running.splitlines() if "docker restart" in line]
    assert len(restarts) == 1, restarts
    assert running.index("docker restart") < running.index("marke marke-a")


def test_the_residue_cycles_keep_the_aborts_of_94b_and_add_46_and_47() -> None:
    """29, 31, 32, 33 keep their meaning, 46 and 47 are new, all below the tee."""
    above, below = the_two_halves_of(RESIDUE_CYCLES.read_text(encoding="utf-8"))
    assert below, "94c lost its pipeline"
    assert set(BASELOAD_RETURN_ABORTS) <= aborts_of(below)
    assert {"exit 46", "exit 47"} <= aborts_of(below)
    assert aborts_of(above) == {"exit 2"}


def test_the_residue_cycles_want_the_switch_at_120_and_end_with_47_otherwise() -> None:
    """The rest time counts on 120 s, so the switch has to say 120 and not merely more than 0."""
    text = RESIDUE_CYCLES.read_text(encoding="utf-8")
    assert 'ENTLADESCHALTER_SOLL="${ENTLADESCHALTER_SOLL:-120}"' in text
    assert 'RUHEZEIT="${RUHEZEIT:-$ENTLADESCHALTER_SOLL}"' in text
    assert "entladeschalter-ist" in text
    _, below = the_two_halves_of(text)
    block = below[below.index('if [ -f "$WORK/schalter-nicht-soll" ]; then') :]
    assert block.split("\nfi\n")[0].rstrip().endswith("exit 47")


def test_the_residue_cycles_end_with_46_for_a_cycle_past_its_deadline() -> None:
    """A deadline per cycle, a work file when it is passed, and 46 below the tee."""
    text = RESIDUE_CYCLES.read_text(encoding="utf-8")
    assert 'ZYKLUS_DECKEL="${ZYKLUS_DECKEL:-900}"' in text
    code = code_of(text)
    assert '"$n" "$ZYKLUS_DECKEL" "$vorrat" >>"$WORK/zyklus-offen"' in code
    _, below = the_two_halves_of(text)
    block = below[below.index('if [ -f "$WORK/zyklus-offen" ]; then') :]
    assert block.split("\nfi\n")[0].rstrip().endswith("exit 46")
    # Fail closed: a block that broke off before its end mark ends with 46 too.
    assert 'if [ ! -f "$WORK/block-durchgelaufen" ]; then' in below


def test_the_residue_cycles_read_the_password_from_the_environment_or_the_file() -> None:
    """Never from an argument; the value goes into a file of mode 600 and curl -K."""
    code = code_of(RESIDUE_CYCLES.read_text(encoding="utf-8"))
    assert 'PWFILE="${PWFILE:-$HOME/work/.pw/admin}"' in code
    assert 'sudo cat "$PWFILE"' in code
    assert '-K "$CURLRC"' in code
    assert 'chmod 600 "$CURLRC"' in code


# ---------------------------------------------------------------------------
# 95c, the cold start with a first search that has to find something.


def test_the_cold_start_names_its_predecessor_and_says_it_never_ran() -> None:
    text = COLD_START.read_text(encoding="utf-8")
    assert "docs/measurements/2026-09-v12-messung/skripte/95b-wiederaufwaermen.sh" in text
    assert NOT_DRIVEN in text
    assert V12_REWARM.is_file()


def test_the_cold_start_asks_the_user_route_with_the_two_word_term_after_drop_caches() -> None:
    text = COLD_START.read_text(encoding="utf-8")
    assert 'BEGRIFF="${BEGRIFF:-Bescheid Antrag}"' in text
    code = code_of(text)
    assert "/ocs/v2.php/search/providers/findling/search" in code
    loop = code[code.index('while [ "$zyklus" -lt "$KALTZYKLEN_MAX" ]; do') :]
    assert loop.index("docker restart") < loop.index("drop_caches") < loop.index('suche "$BEGRIFF" "kalt-$zyklus"')


def test_the_cold_start_never_asks_the_route_that_loads_the_model() -> None:
    """No pre probe over the route of the runbook's abort 30, not even in a comment."""
    text = COLD_START.read_text(encoding="utf-8")
    assert re.search("diagnose", text, flags=re.IGNORECASE) is None


def test_the_cold_start_repeats_the_whole_cycle_at_most_three_times_and_ends_with_48() -> None:
    """Hits > 0 in the first cold search or the whole cycle again; 48 below the tee."""
    text = COLD_START.read_text(encoding="utf-8")
    assert 'KALTZYKLEN_MAX="${KALTZYKLEN_MAX:-3}"' in text
    above, below = the_two_halves_of(text)
    assert 'while [ "$zyklus" -lt "$KALTZYKLEN_MAX" ]; do' in above
    assert 'if [ "$treffer" -gt 0 ]; then' in above
    assert "exit 48" in aborts_of(below)
    assert aborts_of(above) == {"exit 2"}
    block = below[below.index('if [ -f "$WORK/kaltstart-ungueltig" ]; then') :]
    assert block.split("\nfi\n")[0].rstrip().endswith("exit 48")
    assert 'protokoll "kaltzyklus $zyklus ms $ms code $code treffer $treffer"' in above
    assert 'protokoll "kaltstart-gueltig $GUELTIG"' in above


def test_the_cold_start_writes_its_window_for_the_slow_call_reader() -> None:
    code = code_of(COLD_START.read_text(encoding="utf-8"))
    assert 'protokoll "kaltstart-fenster $VON $BIS"' in code
    assert code.count("date -u +%Y-%m-%dT%H:%M:%SZ") == 2


# ---------------------------------------------------------------------------
# Both tools as programs, without a box.


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("script", [RESIDUE_CYCLES, COLD_START], ids=lambda path: path.name)
def test_the_residue_cycles_and_the_cold_start_refuse_an_argument(tmp_path: Path, script: Path) -> None:
    """An argument ends with 2 before any docker call and before any file."""
    answer = a_boxless_run(script, tmp_path, ["zwei"])
    assert answer.returncode == 2, answer
    assert "Benutzung:" in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("zyklen", ["0", "4", "10", "drei"])
def test_the_cold_start_refuses_more_than_three_cycles(tmp_path: Path, zyklen: str) -> None:
    """A fourth cycle would be a search for the one that happens to fit."""
    answer = a_boxless_run(COLD_START, tmp_path, [], umgebung={"KALTZYKLEN_MAX": zyklen})
    assert answer.returncode == 2, answer
    assert "Benutzung:" in answer.stderr
    assert list(tmp_path.iterdir()) == []
