"""The watchmen over the run script, the fetch script and the run plan of the v1.3 trip, plan 22-05.

00-lauf.sh drives the whole trip on the box without anybody watching: the hard
stop of D-01 and D-02 as a shutdown timer that is read back, the order of the
blocks, the strike order of D-05, and the separation of BL-F03 and BL-F04 (no
BL-F04 block changes an environment variable of the product container).
00-abholen.sh fetches the raw data to the development machine every ten
minutes, so that a hard stop loses nothing that was already written.
00-ablauf.md carries the expectations, the abort catalogue and the rules, and
it has to be committed before the first box minute (pattern 5 of the research).

None of the three has run on a box, and section 7.1 of the runbook forbids a
change during the paid trip, so what can be held without a box is held here.
The house rules of the directory (shebang, no carriage return, no dash, no
machine path, no password on a command line) come from test_measurement_scripts
through NARROW_SCOPE_DIRS; this file holds what is particular to each file.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from test_measurement_scripts import V13_RUN_DIR, a_boxless_run

RUN_SCRIPT = V13_RUN_DIR / "00-lauf.sh"
FETCH_SCRIPT = V13_RUN_DIR / "00-abholen.sh"
RUN_PLAN = V13_RUN_DIR / "00-ablauf.md"
REPORT = V13_RUN_DIR.parent / "README.md"

A_DIGEST = "sha256:" + "0" * 64

# The three rebuilds of the product container the run may do, and no fourth.
THE_THREE_REBUILDS = {
    "FINDLING_EMBED_IDLE_RELEASE_SECONDS=120",
    "FINDLING_EMBED_IDLE_RELEASE_SECONDS=0",
    "FINDLING_LANGUAGES=de,en,es,it,nl,pt",
}

# The blocks of way a in their order, each with the call that proves the block
# is the one the plan names. The order is the one of must_haves in 22-05.
WAY_A = (
    ("block_marken", '90e-einzelliste.py" marken'),
    ("block_92d", '92d-wechsel.sh"'),
    ("block_cron_vorher", '97-cron-vorpruefung.sh" vorher'),
    ("indexgroesse de-en", "index-bytes"),
    ("block_m01", '"$LAST"'),
    ("block_bodensatz", '94c-bodensatz-zyklen.sh"'),
    ("block_99d", '99d-filter-sortierung.sh"'),
    ("block_b2", '"$ADRESSE/remote.php/dav/files/$BENUTZER"'),
    ("block_umbau", "FINDLING_LANGUAGES=de,en,es,it,nl,pt"),
    ("block_98d", "98d-dismax-probe.py"),
    ("block_b3", '00-wegwerf.sh" b3'),
    ("block_b5", '00-wegwerf.sh" b5'),
    ("block_endmessungen", '90-bestand.sh"'),
    ("block_92c", '92c-wechsel.sh"'),
)


def code_of(text: str) -> str:
    """The lines of a shell file that are not comments."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def function_of(code: str, name: str) -> str:
    """The body of one shell function, from its head to the closing brace."""
    start = code.index(f"{name}() {{")
    return code[start : code.index("\n}\n", start)]


def run_code() -> str:
    return code_of(RUN_SCRIPT.read_text(encoding="utf-8"))


def in_order(text: str, needles: list[str]) -> None:
    """Every needle is in the text, each one after the one before it."""
    position = -1
    for needle in needles:
        found = text.find(needle, position + 1)
        assert found > position, (needle, needles)
        position = found


def body_of_the_block(code: str, block: str) -> str:
    """The function a call in a way names, or the helper the call goes to."""
    name = block.split()[0]
    return function_of(code, name)


def laufwerte(path: Path, **werte: str) -> Path:
    """A run value file with the complete set, minus what is handed in as empty."""
    complete = {
        "DECKEL_MINUTEN": "1440",
        "BOX_START_EPOCH": str(int(time.time()) - 600),
        "B4_GEPLANT": "ja",
        "EINZELWEG": "a",
        "ABBILD_DIGEST": A_DIGEST,
        "PWFILE": (path.parent / "kein-pw").as_posix(),
        "PWFILE_LASTTEST": (path.parent / "kein-pw").as_posix(),
    }
    complete.update(werte)
    lines = [f"{name}={wert}" for name, wert in complete.items() if wert != ""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


# ---------------------------------------------------------------------------
# 00-lauf.sh, the run script.


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize(
    "werte",
    [
        {"DECKEL_MINUTEN": ""},
        {"BOX_START_EPOCH": ""},
        {"DECKEL_MINUTEN": "0"},
        {"DECKEL_MINUTEN": "zwoelf"},
        {"BOX_START_EPOCH": "gestern"},
        {"BOX_START_EPOCH": str(int(time.time()) + 86_400)},
        {"B4_GEPLANT": "vielleicht"},
        {"EINZELWEG": "c"},
        {"EINZELWEG": ""},
        {"ABBILD_DIGEST": "latest"},
        {"ABBILD_DIGEST": "sha256:" + "0" * 63},
    ],
    ids=[
        "no-cap",
        "no-start",
        "cap-zero",
        "cap-word",
        "start-word",
        "start-in-the-future",
        "b4-maybe",
        "way-c",
        "no-way",
        "digest-tag",
        "digest-short",
    ],
)
def test_the_run_script_refuses_a_run_without_its_values(tmp_path: Path, werte: dict[str, str]) -> None:
    """Without cap, start, B4 plan, way or digest the run ends with 2, before any file (a_boxless_run)."""
    (tmp_path / "werte").mkdir()
    datei = laufwerte(tmp_path / "werte" / "v13-lauf.env", **werte)
    rohdaten = V13_RUN_DIR.parent / "rohdaten"
    before = rohdaten.exists()
    answer = a_boxless_run(RUN_SCRIPT, tmp_path / "out", ["ablauf"], umgebung={"LAUFWERTE": datei.as_posix()})
    assert answer.returncode == 2, answer
    assert "Benutzung:" in answer.stderr
    assert answer.stdout == ""
    assert not (tmp_path / "out").exists()
    assert rohdaten.exists() == before


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_run_script_refuses_a_run_without_a_value_file(tmp_path: Path) -> None:
    """No file, no cap, no run."""
    answer = a_boxless_run(
        RUN_SCRIPT, tmp_path / "out", ["ablauf"], umgebung={"LAUFWERTE": (tmp_path / "fehlt").as_posix()}
    )
    assert answer.returncode == 2, answer
    assert "DECKEL_MINUTEN" in answer.stderr
    assert "Benutzung:" in answer.stderr


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("arguments", [[], ["los"], ["start", "b3"], ["B4"]], ids=["none", "los", "start-b3", "B4"])
def test_the_run_script_names_four_subcommands_and_refuses_everything_else(
    tmp_path: Path, arguments: list[str]
) -> None:
    """start, ablauf, status and b4, and nothing else."""
    answer = a_boxless_run(RUN_SCRIPT, tmp_path / "out", arguments)
    assert answer.returncode == 2, answer
    for befehl in ("start", "ablauf", "status", "b4"):
        assert befehl in answer.stderr
    assert answer.stdout == ""


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_run_script_b4_needs_the_rest_minutes(tmp_path: Path) -> None:
    """b4 sets its timer out of DECKEL_REST_MINUTEN, so without them it does not start."""
    (tmp_path / "werte").mkdir()
    datei = laufwerte(tmp_path / "werte" / "v13-lauf.env")
    answer = a_boxless_run(RUN_SCRIPT, tmp_path / "out", ["b4"], umgebung={"LAUFWERTE": datei.as_posix()})
    assert answer.returncode == 2, answer
    assert "DECKEL_REST_MINUTEN" in answer.stderr


def test_the_run_script_reads_its_values_without_executing_the_file() -> None:
    """The value file is parsed line by line, never sourced."""
    code = run_code()
    assert 'LAUFWERTE="${LAUFWERTE:-$HOME/work/v13-lauf.env}"' in RUN_SCRIPT.read_text(encoding="utf-8")
    assert '. "$LAUFWERTE"' not in code
    assert "source " not in code
    for name in (
        "DECKEL_MINUTEN",
        "BOX_START_EPOCH",
        "B4_GEPLANT",
        "EINZELWEG",
        "ABBILD_DIGEST",
        "DECKEL_REST_MINUTEN",
        "PWFILE",
    ):
        assert f"$(laufwert {name})" in code, name


def test_the_run_script_sets_the_timer_before_every_block() -> None:
    """shutdown -h +rest, read back out of the systemd file, before the first measuring block."""
    code = run_code()
    timer = function_of(code, "timer_setzen")
    in_order(timer, ['sudo shutdown -h +"$rest"', 'sudo cat "$GEPLANT_DATEI"', "exit 55", "timer-abschaltung"])
    assert timer.count("exit 55") >= 3
    assert '"$OUT/00-timer.txt"' in timer
    ablauf = code[code.index('timer_setzen "$(rest_bis_deckel)"') :]
    in_order(
        ablauf,
        ['timer_setzen "$(rest_bis_deckel)"', "altverzeichnisse_pruefen", "abtaster_neu start", "a) weg_a ;;"],
    )
    deckel = function_of(code, "rest_bis_deckel")
    assert "DECKEL_MINUTEN - (jetzt - BOX_START_EPOCH) / 60" in deckel
    assert "trap signal_abbruch TERM" in code
    assert "00-abbruch-durch-signal" in function_of(code, "signal_abbruch")


# Four stand ins for the box: sudo that runs its command, shutdown that logs and
# optionally plans, git that reports what the test wants, and a notification
# chain that does nothing. None of them reaches a network.
STUB_SUDO = '#!/bin/sh\n[ "${1:-}" = -E ] && shift\nexec "$@"\n'
STUB_SHUTDOWN = """#!/bin/sh
printf '%s\\n' "$*" >>"$STUB/shutdown"
if [ "${STUB_PLANEN:-}" = 1 ] && [ "$1" = -h ]; then
    case "$2" in
    +*)
        minuten=${2#+}
        printf 'USEC=%s\\nMODE=poweroff\\n' "$((($(date +%s) + minuten * 60) * 1000000))" >"$GEPLANT_DATEI"
        ;;
    esac
fi
exit 0
"""
STUB_GIT = '#!/bin/sh\nprintf "%s" "${STUB_GIT:-}"\n'
STUB_CHAIN = '#!/bin/sh\nprintf \'%s\\n\' "$*" >>"$STUB/meldungen"\n'


def a_stubbed_run(tmp_path: Path, umgebung: dict[str, str]) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    """00-lauf.sh ablauf in a copy of its directory, against the stand ins above."""
    skripte = tmp_path / "lauf" / "skripte"
    skripte.mkdir(parents=True)
    shutil.copy(RUN_SCRIPT, skripte / "00-lauf.sh")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, inhalt in (("sudo", STUB_SUDO), ("shutdown", STUB_SHUTDOWN), ("git", STUB_GIT)):
        (bin_dir / name).write_text(inhalt, encoding="utf-8", newline="\n")
        (bin_dir / name).chmod(0o755)
    kette = tmp_path / "kette.sh"
    kette.write_text(STUB_CHAIN, encoding="utf-8", newline="\n")
    stub = tmp_path / "stub"
    stub.mkdir()
    (tmp_path / "werte").mkdir()
    datei = laufwerte(tmp_path / "werte" / "v13-lauf.env")
    environment: dict[str, str | None] = {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "LAUFWERTE": datei.as_posix(),
        "MELDEKETTE": kette.as_posix(),
        "GEPLANT_DATEI": (tmp_path / "scheduled").as_posix(),
        "STUB": stub.as_posix(),
        **umgebung,
    }
    answer = a_boxless_run(skripte / "00-lauf.sh", tmp_path / "out", ["ablauf"], umgebung=environment)
    return answer, tmp_path / "lauf" / "rohdaten", stub


def text_of(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_run_script_ends_with_55_when_the_timer_cannot_be_read_back(tmp_path: Path) -> None:
    """A shutdown that leaves no scheduled file is no cap, and without a cap nothing is measured."""
    answer, rohdaten, stub = a_stubbed_run(tmp_path, {})
    assert answer.returncode == 55, answer
    assert "timer-unlesbar" in text_of(rohdaten / "00-timer.txt")
    lauf = text_of(rohdaten / "00-lauf.txt")
    assert "tor-abbruch p0-timer rueckgabe 55" in lauf
    assert "00-abbruch" in lauf
    assert "altverzeichnisse-sauber" not in lauf
    calls = text_of(stub / "shutdown").splitlines()
    assert calls, calls
    assert re.fullmatch(r"-h \+14[23]\d", calls[0]), calls
    assert "Tor-Abbruch 55" in text_of(stub / "meldungen")


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_run_script_ends_with_54_on_a_dirty_old_directory_after_the_timer(tmp_path: Path) -> None:
    """The timer stands first; a dirty v1.2 directory then ends the run and pulls the timer forward."""
    answer, rohdaten, stub = a_stubbed_run(
        tmp_path, {"STUB_PLANEN": "1", "STUB_GIT": " M docs/measurements/2026-09-v12-messung/rohdaten/90-bestand.txt"}
    )
    assert answer.returncode == 54, answer
    timer = text_of(rohdaten / "00-timer.txt")
    assert "timer-gesetzt" in timer
    assert "timer-abschaltung" in timer
    assert "timer-vorgezogen" in timer
    lauf = text_of(rohdaten / "00-lauf.txt")
    in_order(lauf, ["p0-timer-start", "timer-abschaltung", "p0-timer-ende", "altverzeichnisse-sauber nein"])
    assert "tor-abbruch p0-timer rueckgabe 54" in lauf
    calls = text_of(stub / "shutdown").splitlines()
    assert calls[-1] == "-h +60", calls


def test_the_run_script_drives_way_a_in_the_order_of_the_plan() -> None:
    """Marks, 92d, cron, index size, M-01, cold start, residue, 99d, B2, rebuild, dismax, B3, B5, end, 92c."""
    code = run_code()
    weg = function_of(code, "weg_a")
    in_order(weg, [block for block, _ in WAY_A])
    for block, needle in WAY_A:
        assert needle in body_of_the_block(code, block), (block, needle)
    m01 = function_of(code, "block_m01")
    in_order(m01, ['"$LAST"', '95c-kaltstart.sh"'])
    assert 'LAST="${LAST:-$REPO/scripts/ops/search_load.py}"' in code
    bodensatz = function_of(code, "block_bodensatz")
    in_order(bodensatz, ["=120", '94c-bodensatz-zyklen.sh"', "=0"])
    assert 'block_b2 "$BESTAND_SNAPSHOT"' in weg
    assert 'BESTAND_SNAPSHOT="52137 44 6"' in code
    assert "exit 56" in function_of(code, "block_b2")
    assert weg.rstrip().endswith("block_92c")


def test_the_run_script_way_b_reindexes_first_and_never_switches_with_92d() -> None:
    """Way b: both 92c runs and the full reindex before the single list, no 92d, no 92c at the end."""
    code = run_code()
    weg = function_of(code, "weg_b")
    in_order(weg, ["block_92c", "block_vollreindex", "block_einzelliste", "block_cron_vorher", "block_umbau"])
    assert weg.count("block_92c") == 1
    assert "block_92d" not in weg
    assert "block_marken" not in weg
    assert not weg.rstrip().endswith("block_92c")
    assert "exit 58" in function_of(code, "block_vollreindex")
    assert "a) weg_a ;;" in code
    assert "b) weg_b ;;" in code


def test_the_run_script_restarts_both_samplers_after_every_rebuild() -> None:
    """Every rebuild or restart of the product container is followed by new samplers (pitfall 4)."""
    code = run_code()
    samplers = function_of(code, "abtaster_neu")
    in_order(samplers, ["abtaster_stoppen", '"$CPU_SAMPLER"', '"$RSS_SAMPLER"'])
    text = RUN_SCRIPT.read_text(encoding="utf-8")
    assert 'CPU_SAMPLER="${CPU_SAMPLER:-$REPO/scripts/ops/cpu_sampler.sh}"' in text
    assert 'RSS_SAMPLER="${RSS_SAMPLER:-$REPO/scripts/ops/rss_sampler.sh}"' in text
    assert "$ABTASTTAKT" in samplers
    assert 'ABTASTTAKT="${ABTASTTAKT:-5}"' in text
    # Each call of a tool that rebuilds or restarts the container, and the
    # sampler restart that has to follow it inside the same function.
    for function, tool in (
        ("block_92d", '92d-wechsel.sh"'),
        ("neubau_92e", '92e-umgebung.sh"'),
        ("block_bodensatz", '94c-bodensatz-zyklen.sh"'),
        ("block_m01", '95c-kaltstart.sh"'),
        ("block_92c", '"$NACHFOLGE/92c-wechsel.sh" || rc=$?\n    lauf_zeile "92c-regulaer'),
    ):
        body = function_of(code, function)
        in_order(body, [tool, "abtaster_neu"])
    rebuild_calls = [line for line in code.splitlines() if 'sh "$SKRIPTE/92e-umgebung.sh"' in line]
    assert rebuild_calls == ['    sh "$SKRIPTE/92e-umgebung.sh" "$1" || rc=$?'], rebuild_calls


def test_the_run_script_asks_for_time_only_before_the_blocks_that_may_fall() -> None:
    """zeit_fuer before B2, B3, B5 and B4, before no mandatory block; the reserves follow D-05."""
    code = run_code()
    for weg in ("weg_a", "weg_b"):
        body = function_of(code, weg)
        asked = re.findall(r"if zeit_fuer (b\d) ", body)
        assert asked == ["b2", "b3", "b5"], (weg, asked)
        for block in asked:
            in_order(body, [f"if zeit_fuer {block} ", f"block_{block}"])
    assert "if zeit_fuer b4 " in function_of(code, "abschluss")
    assert set(re.findall(r"zeit_fuer (\w+) ", code)) == {"b2", "b3", "b5", "b4"}
    reserve = function_of(code, "reserve_fuer")
    arms = dict(re.findall(r"^\s+(b\d)\) (.*)$", reserve, flags=re.MULTILINE))
    assert "b4_teil" in arms["b5"]
    assert "b3_teil" in arms["b5"]
    assert "b4_teil" not in arms["b2"]
    assert "b4_teil" not in arms["b3"]
    assert "b4_teil=$PLAN_B4" in reserve
    assert "b3_teil=$PLAN_B3" in reserve
    for name, wert in (("B2", 45), ("B3", 15), ("B5", 12), ("B4", 75), ("ENDE", 15), ("92C", 30), ("ABHOLEN", 20)):
        assert f"PLAN_{name}={wert}\n" in code, name
    streichen = function_of(code, "zeit_fuer")
    assert '"$OUT/00-gestrichen.txt"' in streichen
    assert "gestrichen %s rest %s bedarf %s" in streichen
    assert "return 1" in streichen


def test_the_run_script_never_touches_the_ocr_languages_and_rebuilds_three_ways() -> None:
    """No BL-F04 block changes the product; 92e only with 120, 0 and the six languages."""
    text = RUN_SCRIPT.read_text(encoding="utf-8")
    assert "FINDLING_OCR_LANGUAGES" not in text
    code = code_of(text)
    rebuilds = set(re.findall(r"^\s*neubau_92e (\S+) ", code, flags=re.MULTILINE))
    assert rebuilds == THE_THREE_REBUILDS
    for block in ("block_b3", "block_b5", "block_98d", "block_endmessungen"):
        assert "neubau_92e" not in function_of(code, block), block
        assert "docker update" not in function_of(code, block), block


def test_the_run_script_sets_loglevel_1_for_m01_and_puts_it_back() -> None:
    """Read and logged before, 1 during the stages and the cold start, the read value after; 57 without a line."""
    m01 = function_of(run_code(), "block_m01")
    in_order(
        m01,
        [
            "occ config:system:get loglevel",
            "loglevel-vorher",
            "occ config:system:set loglevel --value=1 --type=integer",
            '"$LAST"',
            '91m-langsame-aufrufe.py"',
            '95c-kaltstart.sh"',
            "--stufe kaltstart",
            'occ config:system:set loglevel --value="$loglevel_vorher" --type=integer',
            "exit 57",
        ],
    )
    assert "occ config:system:delete loglevel" in m01


def test_the_run_script_points_every_tool_at_its_own_run_directory() -> None:
    """OUT is set once and exported; the two old directories must be clean, else 54."""
    code = run_code()
    assignments = [line.strip() for line in code.splitlines() if re.match(r"^\s*OUT=", line)]
    assert assignments == ['OUT="$LAUF/rohdaten"'], assignments
    assert "\nexport OUT\n" in code
    assert 'LAUF=$(cd "$SKRIPTE/.." && pwd)' in code
    guard = function_of(code, "altverzeichnisse_pruefen")
    in_order(guard, ['git -C "$REPO" status --porcelain -- "$ALT_V12" "$ALT_NACHFOLGE"', "exit 54"])
    assert 'ALT_V12="docs/measurements/2026-09-v12-messung"' in code
    assert 'ALT_NACHFOLGE="docs/measurements/2026-09-nachfolgefassungen"' in code
    assert "altverzeichnisse_pruefen" in function_of(code, "abschluss")


def test_the_run_script_waits_for_the_last_fetch_before_it_switches_itself_off() -> None:
    """00-FERTIG, then the fetch mark younger than it for at most ABHOL_WARTE, then shutdown now."""
    code = run_code()
    abschluss = function_of(code, "abschluss")
    in_order(abschluss, ['[ "$B4_GEPLANT" = ja ]', "b4_vorbereiten", '"$OUT/00-FERTIG"', "abholung_abwarten"])
    in_order(abschluss, ['abholung_abwarten "$OUT/00-FERTIG"', "sudo shutdown -h now"])
    warten = function_of(code, "abholung_abwarten")
    in_order(warten, ["ABHOL_WARTE))", 'cat "$ABGEHOLT"', '-gt "$marke"'])
    text = RUN_SCRIPT.read_text(encoding="utf-8")
    assert 'ABGEHOLT="${ABGEHOLT:-$HOME/work/abgeholt}"' in text
    assert re.search(r'ABHOL_WARTE="\$\{ABHOL_WARTE:-\d+\}"', text)
    vorbereiten = function_of(code, "b4_vorbereiten")
    in_order(vorbereiten, ['sudo rm -f "$GRUB_DROPIN"', "sudo update-grub"])
    assert 'GRUB_DROPIN="${GRUB_DROPIN:-/etc/default/grub.d/99-mem4g.cfg}"' in text


def test_the_run_script_b4_resets_the_timer_stops_everything_and_switches_off() -> None:
    """After the type switch: timer out of the rest, every container down, B4, B4-FERTIG, shutdown."""
    code = run_code()
    b4 = code[code.index('if [ "$BEFEHL" = b4 ]; then') : code.index('timer_setzen "$(rest_bis_deckel)"')]
    in_order(
        b4,
        [
            'timer_setzen "$DECKEL_REST_MINUTEN"',
            "sudo docker ps -q",
            "sudo docker stop $laufende",
            '00-wegwerf.sh" b4',
            '"$OUT/B4-FERTIG"',
            'abholung_abwarten "$OUT/B4-FERTIG"',
            "sudo shutdown -h now",
        ],
    )


def test_the_run_script_starts_detached_and_fully_redirected() -> None:
    """start is the 96-volllauf.sh pattern: setsid nohup, nothing holds the ssh session."""
    code = run_code()
    assert 'setsid nohup sh "$SKRIPTE/00-lauf.sh" "$ZIELBEFEHL" >>"$PROTOKOLL" 2>&1 </dev/null &' in code
    enter = function_of(code, "block_betreten")
    leave = function_of(code, "block_verlassen")
    assert '"$1-start $(utc)"' in enter
    assert '"$1-ende $(utc)"' in leave
    assert 'LAUFDATEI="$OUT/00-lauf.txt"' in code
    assert 'chmod 700 "$WORK"' in code


def test_the_run_script_keeps_the_load_password_out_of_99d() -> None:
    """E7: the password of the load account lives in a subshell of the stages only."""
    code = run_code()
    m01 = function_of(code, "block_m01")
    assert '(\n            FINDLING_LOAD_PASSWORD=$(sudo cat "$PWFILE_LAST"' in m01
    assert code.count("export FINDLING_LOAD_PASSWORD") == 1
    d99 = function_of(code, "block_99d")
    in_order(d99, ["unset FINDLING_LOAD_PASSWORD", "99d-umgebung", '99d-filter-sortierung.sh"'])
    assert 'PWFILE="$PWFILE_LAST" sh "$NACHFOLGE/99d-filter-sortierung.sh"' in d99


# ---------------------------------------------------------------------------
# 00-abholen.sh, the fetch script of the development machine.

STUB_SCP = """#!/bin/sh
printf '%s\\n' "$*" >>"$STUB/scp"
runde=$(($(cat "$STUB/runde" 2>/dev/null || echo 0) + 1))
printf '%s\\n' "$runde" >"$STUB/runde"
[ "${STUB_SCP_FEHLER:-}" = 1 ] && exit 1
for a in "$@"; do ziel=$a; done
mkdir -p "$ziel/rohdaten"
printf 'x\\n' >"$ziel/rohdaten/00-lauf.txt"
case "${STUB_FOLGE:-fertig}" in
fertig) printf 'fertig T epoch 1 weg a b4 nicht-geplant\\n' >"$ziel/rohdaten/00-FERTIG" ;;
b4)
    printf 'fertig T epoch 1 weg a b4 vorbereitet\\n' >"$ziel/rohdaten/00-FERTIG"
    [ "$runde" -ge 2 ] && printf 'b4-fertig T epoch 2 rueckgabe 0\\n' >"$ziel/rohdaten/B4-FERTIG"
    ;;
esac
exit 0
"""
STUB_SSH = """#!/bin/sh
printf '%s\\n' "$*" >>"$STUB/ssh"
exit 0
"""

# ssh-keygen -F <host> -f <file>, answered by a plain search for the host.
STUB_SSH_KEYGEN = """#!/bin/sh
printf '%s\\n' "$*" >>"$STUB/ssh-keygen"
[ "$1" = -F ] && [ "$3" = -f ] || exit 2
grep -q "^$2 " "$4"
"""

KNOWN_HOST_LINE = "box.example.invalid ssh-ed25519 AAAAattrappe\n"


def a_stubbed_fetch(
    tmp_path: Path, umgebung: dict[str, str | None]
) -> tuple[subprocess.CompletedProcess[str], Path, Path, Path]:
    """00-abholen.sh against a stub scp and ssh, with its state directory in tmp_path."""
    stub = tmp_path / "stub"
    stub.mkdir()
    scp = tmp_path / "scp"
    scp.write_text(STUB_SCP, encoding="utf-8", newline="\n")
    scp.chmod(0o755)
    ssh = tmp_path / "ssh"
    ssh.write_text(STUB_SSH, encoding="utf-8", newline="\n")
    ssh.chmod(0o755)
    keygen = tmp_path / "ssh-keygen"
    keygen.write_text(STUB_SSH_KEYGEN, encoding="utf-8", newline="\n")
    keygen.chmod(0o755)
    state = tmp_path / "zustand"
    state.mkdir()
    (state / "findling-loadtest").write_text("attrappe\n", encoding="utf-8", newline="\n")
    (state / "known_hosts").write_text(KNOWN_HOST_LINE, encoding="utf-8", newline="\n")
    lokal = tmp_path / "lokal"
    environment: dict[str, str | None] = {
        "BOX_ADRESSE": "box.example.invalid",
        "FINDLING_LOADTEST_DIR": state.as_posix(),
        "LOKAL": lokal.as_posix(),
        "SCP": scp.as_posix(),
        "SSH": ssh.as_posix(),
        "SSH_KEYGEN": keygen.as_posix(),
        "STUB": stub.as_posix(),
        "ABHOLTAKT": "0",
        **umgebung,
    }
    answer = a_boxless_run(FETCH_SCRIPT, tmp_path / "out", [], umgebung=environment)
    return answer, lokal, stub, state


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize(
    "umgebung",
    [{"BOX_ADRESSE": None}, {"BOX_ADRESSE": ""}, {"B4_GEPLANT": "vielleicht"}],
    ids=["no-address", "empty-address", "b4-maybe"],
)
def test_the_fetch_script_refuses_without_address_or_known_b4_plan(
    tmp_path: Path, umgebung: dict[str, str | None]
) -> None:
    """No address, no fetch, and no scp before the refusal."""
    answer, lokal, stub, _ = a_stubbed_fetch(tmp_path, umgebung)
    assert answer.returncode == 2, answer
    assert "Benutzung:" in answer.stderr
    assert not (stub / "scp").exists()
    assert not lokal.exists()


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_fetch_script_refuses_without_the_key_of_the_state_directory(tmp_path: Path) -> None:
    """The key comes out of FINDLING_LOADTEST_DIR, outside the repository."""
    state = tmp_path / "zustand"
    state.mkdir()
    answer = a_boxless_run(
        FETCH_SCRIPT,
        tmp_path / "out",
        [],
        umgebung={
            "BOX_ADRESSE": "box.example.invalid",
            "FINDLING_LOADTEST_DIR": state.as_posix(),
            "LOKAL": (tmp_path / "lokal").as_posix(),
            "SCP": (tmp_path / "kein-scp").as_posix(),
        },
    )
    assert answer.returncode == 2, answer
    assert "FINDLING_LOADTEST_DIR" in answer.stderr
    assert "Benutzung:" in answer.stderr
    assert not (tmp_path / "lokal").exists()


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("known_hosts", ["", "andere.example.invalid ssh-ed25519 AAAAattrappe\n", None])
def test_the_fetch_script_refuses_a_box_its_known_hosts_does_not_know(tmp_path: Path, known_hosts: str | None) -> None:
    """Found in the dress rehearsal of 22-06: no known_hosts in the state directory.

    StrictHostKeyChecking=yes against it failed every round, and the fetch ended
    only after three rounds, while the box waited for its mark. Now it is 2
    before the first scp.
    """
    stub = tmp_path / "stub"
    stub.mkdir()
    keygen = tmp_path / "ssh-keygen"
    keygen.write_text(STUB_SSH_KEYGEN, encoding="utf-8", newline="\n")
    keygen.chmod(0o755)
    state = tmp_path / "zustand"
    state.mkdir()
    (state / "findling-loadtest").write_text("attrappe\n", encoding="utf-8", newline="\n")
    if known_hosts is not None:
        (state / "known_hosts").write_text(known_hosts, encoding="utf-8", newline="\n")
    answer = a_boxless_run(
        FETCH_SCRIPT,
        tmp_path / "out",
        [],
        umgebung={
            "BOX_ADRESSE": "box.example.invalid",
            "FINDLING_LOADTEST_DIR": state.as_posix(),
            "LOKAL": (tmp_path / "lokal").as_posix(),
            "SCP": (tmp_path / "kein-scp").as_posix(),
            "SSH_KEYGEN": keygen.as_posix(),
            "STUB": stub.as_posix(),
        },
    )
    assert answer.returncode == 2, answer
    assert "known_hosts" in answer.stderr
    assert "box.example.invalid" not in answer.stderr
    assert not (tmp_path / "lokal").exists()


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_fetch_script_copies_the_raw_data_and_then_sets_the_mark(tmp_path: Path) -> None:
    """scp -r with key and known_hosts, then ssh writes ~/work/abgeholt; ends on 00-FERTIG."""
    answer, lokal, stub, state = a_stubbed_fetch(tmp_path, {})
    assert answer.returncode == 0, answer
    assert (lokal / "00-FERTIG").is_file()
    assert (lokal / "00-lauf.txt").is_file()
    scp_calls = (stub / "scp").read_text(encoding="utf-8").splitlines()
    assert len(scp_calls) == 1, scp_calls
    call = scp_calls[0]
    assert call.startswith("-q -r -i "), call
    assert f"-i {state.as_posix()}/findling-loadtest" in call
    assert f"UserKnownHostsFile={state.as_posix()}/known_hosts" in call
    assert "StrictHostKeyChecking=yes" in call
    source = (
        "ubuntu@box.example.invalid:/home/ubuntu/work/nextcloud-search/docs/measurements/2026-09-v13-messung/rohdaten"
    )
    assert source in call
    ssh_calls = (stub / "ssh").read_text(encoding="utf-8").splitlines()
    assert len(ssh_calls) == 1, ssh_calls
    assert ssh_calls[0].endswith("ubuntu@box.example.invalid date +%s > ~/work/abgeholt"), ssh_calls
    log = (state / "v13-abholen.log").read_text(encoding="utf-8")
    assert re.search(r"^abgeholt \S+ dateien 2 marke gesetzt$", log, flags=re.MULTILINE), log
    assert "abholen-ende" in log


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_fetch_script_waits_for_b4_when_the_box_prepared_it(tmp_path: Path) -> None:
    """00-FERTIG with b4 vorbereitet is no end; B4-FERTIG is."""
    answer, lokal, stub, _ = a_stubbed_fetch(tmp_path, {"STUB_FOLGE": "b4", "B4_GEPLANT": "ja"})
    assert answer.returncode == 0, answer
    assert (lokal / "B4-FERTIG").is_file()
    assert len((stub / "scp").read_text(encoding="utf-8").splitlines()) == 2


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_fetch_script_ends_after_three_failures_in_a_row(tmp_path: Path) -> None:
    """A stopped box answers nothing; three misses end the fetch with 1 and set no mark."""
    answer, _, stub, state = a_stubbed_fetch(tmp_path, {"STUB_SCP_FEHLER": "1"})
    assert answer.returncode == 1, answer
    assert len((stub / "scp").read_text(encoding="utf-8").splitlines()) == 3
    assert not (stub / "ssh").exists()
    log = (state / "v13-abholen.log").read_text(encoding="utf-8")
    assert log.count("fehlversuch") == 3
    assert "box-nicht-erreichbar" in log


def test_the_fetch_script_never_commits_or_pushes() -> None:
    """No git call at all in the code; the raw data pass the public artifact gate first (T-22-20)."""
    code = code_of(FETCH_SCRIPT.read_text(encoding="utf-8"))
    assert "git " not in code
    assert "MSYS_NO_PATHCONV=1" in code
    assert 'STATE_DIR="${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}"' in code
    assert 'LOG="${LOG:-$STATE_DIR/v13-abholen.log}"' in code
    assert 'ABHOLTAKT="${ABHOLTAKT:-600}"' in code
    assert 'FEHLVERSUCHE_MAX="${FEHLVERSUCHE_MAX:-3}"' in code


# ---------------------------------------------------------------------------
# 00-ablauf.md and README.md, the run plan and the frame of the report.

PLAN_HEADINGS = (
    "## 1. Was dieser Lauf misst",
    "## 2. Die Schrittfolge",
    "## 3. Die Erwartung, vorher aufgeschrieben",
    "## 4. Woran der Lauf abgebrochen wird",
    "## 5. Nach dem Lauf",
    "## 6. Owner-Entscheide",
    "## 7. Streichreihenfolge",
    "## 8. F4 und die B4-Regel",
)
UMLAUTS = "äöüÄÖÜß"
DASHES = (chr(0x2014), chr(0x2013))


def sections_of(text: str) -> dict[str, str]:
    """The run plan cut at its level two headings, heading to body."""
    sections: dict[str, str] = {}
    current = ""
    for line in text.splitlines():
        if line.startswith("## "):
            current = line
            sections[current] = ""
        elif current:
            sections[current] += line + "\n"
    return sections


def plan_sections() -> dict[str, str]:
    return sections_of(RUN_PLAN.read_text(encoding="utf-8"))


def test_the_run_plan_carries_its_eight_sections_without_umlauts_in_the_headings() -> None:
    """The headings are what checks and references point at, so they stay ASCII."""
    headings = tuple(plan_sections())
    assert headings == PLAN_HEADINGS, headings
    for heading in headings:
        assert not set(heading) & set(UMLAUTS), heading


def test_the_run_plan_names_every_abort_value_from_40_to_58_once() -> None:
    """One row per value, with script, condition and consequence (pattern 4, numbers continued)."""
    section = plan_sections()["## 4. Woran der Lauf abgebrochen wird"]
    rows = re.findall(r"^\| \*\*(\d+)\*\* \|(.*)$", section, flags=re.MULTILINE)
    assert sorted(int(value) for value, _ in rows) == list(range(40, 59)), rows
    for value in range(40, 59):
        assert section.count(f"**{value}**") == 1, value
    for value, rest in rows:
        cells = [cell.strip() for cell in rest.strip().strip("|").split("|")]
        assert len(cells) == 3, (value, cells)
        assert re.search(r"\.(sh|py)", cells[0]), (value, cells)
        assert cells[1], value
        assert cells[2], value
    assert "15 bis 39" in section


def test_the_run_plan_catalogue_matches_the_exits_of_the_run_script() -> None:
    """54 to 58 are exits of 00-lauf.sh, and 00-lauf.sh carries no other literal value."""
    section = plan_sections()["## 4. Woran der Lauf abgebrochen wird"]
    own = {int(value) for value in re.findall(r"^\| \*\*(\d+)\*\* \| `00-lauf\.sh`", section, flags=re.MULTILINE)}
    assert own == {54, 55, 56, 57, 58}
    exits = {int(value) for value in re.findall(r"^\s*exit (\d+)$", run_code(), flags=re.MULTILINE)}
    # 143 is the end by signal (the hard stop itself), and the section says so.
    assert exits == {0, 2, 54, 55, 56, 57, 58, 143}, exits
    assert "143" in section
    assert "00-abbruch-durch-signal" in section


def test_the_run_plan_writes_down_e1_to_e14_with_a_number() -> None:
    """Pattern 5: every expectation stands with its figure before the first box minute."""
    section = plan_sections()["## 3. Die Erwartung, vorher aufgeschrieben"]
    names = re.findall(r"^- \*\*(E\d+),", section, flags=re.MULTILINE)
    assert names == [f"E{n}" for n in range(1, 15)], names
    blocks = re.split(r"^- \*\*E\d+,", section, flags=re.MULTILINE)[1:]
    for number, block in enumerate(blocks, start=1):
        assert re.search(r"\d", block), number
    for figure in ("52.111", "1.500", "2.051", "628,0", "2,5", "3 h", "19 h 20 min", "1,05", "8 min 36 s"):
        assert figure in section, figure


def test_the_run_plan_e1_holds_the_constants_of_the_code_and_of_the_run_script() -> None:
    """E1 is read out of the code when written; the gate of 00-lauf.sh hands the same pairs to 90e."""
    from findling.config import EMBED_TOKEN_CAP, INDEX_VERSION, SCHEMA_VERSION
    from findling.index.analyzer import ANALYZER_VERSION
    from findling.index.open import TANTIVY_VERSION
    from findling.store.vectors import EMBEDDING_MODEL, embedding_mark

    section = plan_sections()["## 3. Die Erwartung, vorher aufgeschrieben"]
    e1 = section[section.index("- **E1,") : section.index("- **E2,")]
    from_code = {
        f"analyzer_version={ANALYZER_VERSION}",
        f"index_version={INDEX_VERSION}",
        f"store_schema_version={SCHEMA_VERSION}",
        f"schema_version={SCHEMA_VERSION}",
        f"tantivy_version={TANTIVY_VERSION}",
        f"embedding_version={embedding_mark(EMBEDDING_MODEL, tokens=EMBED_TOKEN_CAP)}",
        "languages=de,en",
    }
    text = RUN_SCRIPT.read_text(encoding="utf-8")
    in_script = set(re.findall(r'^ERWARTUNG_[A-Z]+="([^"]+)"$', text, flags=re.MULTILINE))
    assert from_code <= in_script, from_code - in_script
    wordlist = [pair for pair in in_script if pair.startswith("wordlist_hash=")]
    assert len(wordlist) == 1
    assert len(in_script) == len(from_code) + 1
    flat = " ".join(e1.split())
    for pair in in_script:
        assert pair in flat, pair
    marks = function_of(run_code(), "block_marken")
    for name in re.findall(r"^(ERWARTUNG_[A-Z]+)=", text, flags=re.MULTILINE):
        assert f'--erwartung "${name}"' in marks, name


def test_the_run_plan_quotes_f4_as_the_w4_job_defines_it() -> None:
    """Section 8 carries the definition of measure.yml word for word, and D-03 beside it."""
    workflow = (V13_RUN_DIR.parents[3] / ".github" / "workflows" / "measure.yml").read_text(encoding="utf-8")
    lines = workflow.splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip().startswith("#   F4 = "))
    end = next(index for index in range(start, len(lines)) if "one of w3-slots-1.txt)." in lines[index])
    definition = " ".join(line.strip().lstrip("#").strip() for line in lines[start : end + 1])
    section = plan_sections()["## 8. F4 und die B4-Regel"]
    block = section[section.index("```") + 3 : section.rindex("```")]
    assert " ".join(block.split()) == " ".join(definition.split())
    assert "1,5" in section
    assert "B4_GEPLANT=ja" in section
    assert "B4_GEPLANT=nein" in section


def test_the_run_plan_freezes_the_owner_decisions_of_checkpoint_22_07() -> None:
    """Section 6 carries the owner answer word for word, dated, and the dismax rule with its figures."""
    section = plan_sections()["## 6. Owner-Entscheide"]
    assert "Antwort: offen" not in section
    assert "> machen wir nach deiner empfehlung\n" in section
    assert "> Weg a, Deckel stunden, dismax vorschlag, F4 bestaetigt, freigegeben\n" in section
    assert section.count("Antwort (26.09.2026):") == 3
    for question in ("Frage 1", "Frage 2", "Frage 3"):
        assert question in section, question
    for fixed in ("**Weg a.**", "`EINZELWEG=a`", "**Variante Stunden.**", "`DECKEL_MINUTEN=1354`"):
        assert fixed in section, fixed
    assert "`DECKEL_REST_MINUTEN=86`" in section
    assert "`B4_GEPLANT=ja`" in section
    flat = " ".join(section.split())
    for figure in ("**0,05**", "**1,20-fache**", "**0.0**", "dismax_t00", "dismax_t01", "rbo10_gegen_altplan"):
        assert figure in flat, figure
    e10 = plan_sections()["## 3. Die Erwartung, vorher aufgeschrieben"]
    e10 = " ".join(e10[e10.index("- **E10,") : e10.index("- **E11,")].split())
    for figure in ("**0,05**", "**1,20-fache**", "26.09.2026"):
        assert figure in e10, figure


def test_the_run_plan_strike_order_carries_the_constants_of_the_run_script() -> None:
    """Section 7 names every planning constant with the value 00-lauf.sh computes with."""
    section = plan_sections()["## 7. Streichreihenfolge"]
    constants = re.findall(r"^(PLAN_[A-Z0-9]+=\d+)$", RUN_SCRIPT.read_text(encoding="utf-8"), flags=re.MULTILINE)
    assert len(constants) == 9, constants
    for constant in constants:
        assert f"`{constant}`" in section, constant
    for rank in ("B7", "B5", "B4", "B2 und B3", "B1"):
        assert rank in section, rank


@pytest.mark.parametrize("path", [RUN_PLAN, REPORT], ids=["run-plan", "report"])
def test_the_run_plan_and_the_report_carry_no_dash(path: Path) -> None:
    """The typography rule of this project, for the two documents of the run directory.

    No carriage return check here: Markdown is outside the eol rules of
    .gitattributes, so a checkout with core.autocrlf may legitimately add them.
    """
    text = path.read_text(encoding="utf-8")
    assert not [dash for dash in DASHES if dash in text], path.name


def test_the_run_plan_report_carries_the_release_and_the_run_values() -> None:
    """One release line from checkpoint 22-07, the run values it implies, and the frames of the report."""
    text = REPORT.read_text(encoding="utf-8")
    assert text.count("Anfahrt freigegeben:") == 1
    release = (
        "\nAnfahrt freigegeben: 26.09.2026, Deckel 24 h / 3,76 USD (Variante stunden), "
        "Weg a, B4 gefahren (F4 = 3,955)\n"
    )
    assert release in text
    values = sections_of(text)["## 4. Laufwerte"]
    rows = dict(re.findall(r"^\| `([A-Z0-9_]+)` \| ([^|]+?) \|", values, flags=re.MULTILINE))
    assert rows == {"DECKEL_MINUTEN": "1354", "DECKEL_REST_MINUTEN": "86", "B4_GEPLANT": "ja", "EINZELWEG": "a"}, rows
    assert int(rows["DECKEL_MINUTEN"]) + int(rows["DECKEL_REST_MINUTEN"]) == 24 * 60
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    for name in ("Rechenblatt", "W4-Vorabkurve", "Generalprobe", "Laufwerte", "Offene Owner-Fragen", "Bericht"):
        assert any(name in heading for heading in headings), name
    for heading in headings:
        assert not set(heading) & set(UMLAUTS), heading
