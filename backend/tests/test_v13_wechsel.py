"""The watchmen over the box tools of the v1.3 trip, plan 22-02.

Four tools live in docs/measurements/2026-09-v13-messung/skripte/ and none of
them has run yet: the image switch 92d that keeps the volume of the snapshot,
the environment rebuild 92e, the single list and mark reader 90e and the reader
of the slow backend calls 91m. Section 7.1 of the runbook says no tool is
changed during the paid trip, so everything about them that can be held without
a box is held here, before the box stands.

The house rules of the directory (shebang, no carriage return, no dash, no
machine path, no password on a command line) come from test_measurement_scripts
through NARROW_SCOPE_DIRS; this file holds what is particular to each tool.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

from test_measurement_scripts import (
    NOT_DRIVEN,
    PIPELINE_CUT,
    SUCCESSOR_IMAGE_SWITCH,
    V13_RUN_DIR,
    a_boxless_run,
    aborts_of,
    switches_that_run,
    the_three_parts_of,
)

IMAGE_SWITCH = V13_RUN_DIR / "92d-wechsel.sh"
ENVIRONMENT_REBUILD = V13_RUN_DIR / "92e-umgebung.sh"
SINGLE_LIST = V13_RUN_DIR / "90e-einzelliste.py"
SLOW_CALL_READER = V13_RUN_DIR / "91m-langsame-aufrufe.py"

# The one refusal line of 92e that may name the OCR languages. The variable is
# the anti pattern of this trip: the OCR languages are no subject of it.
OCR_LANGUAGES = "FINDLING_OCR_LANGUAGES"
ALLOWED_SWITCHES = ("FINDLING_LANGUAGES", "FINDLING_EMBED_IDLE_RELEASE_SECONDS")

# The count that has to stand right above every unregister, and how many code
# lines above it may stand at most. The same distance test_measurement_scripts
# grants the count above --rm-data.
THE_COUNT = 'nextclouds_zaehlen >"$WORK/'
THE_UNREGISTER = "occ app_api:app:unregister"
THE_COUNT_IS_IMMEDIATE = 10

# A value the fake docker hands out as APP_SECRET, and which must never reach
# standard output, standard error or any file of the run.
FAKE_SECRET = "geheimnis-das-niemand-sehen-darf-4711"  # noqa: S105 - a planted value, the point of the test


def code_of(text: str) -> str:
    """The lines of a shell file that are not comments."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


# ---------------------------------------------------------------------------
# 92d, the image switch that keeps the volume.


def test_the_image_switch_names_its_predecessor_and_lives_elsewhere() -> None:
    """92d follows 92c, says so with the full path, and says that it never ran."""
    text = IMAGE_SWITCH.read_text(encoding="utf-8")
    assert "docs/measurements/2026-09-nachfolgefassungen/skripte/92c-wechsel.sh" in text
    assert NOT_DRIVEN in text
    assert IMAGE_SWITCH.parent != SUCCESSOR_IMAGE_SWITCH.parent
    assert "Die zwei Aenderungen gegen 92c" in text
    assert "Was ausdruecklich gleich bleibt" in text


def test_the_image_switch_runs_no_rm_data() -> None:
    """Change 1: the volume of the snapshot stays, so no line runs the switch.

    The acceptance criterion of the plan is stricter than the helper: no line
    that is not a comment carries the switch at all, not even an echo.
    """
    code = code_of(IMAGE_SWITCH.read_text(encoding="utf-8"))
    assert switches_that_run(code) == []
    assert "--rm-data" not in code


def test_the_image_switch_counts_the_nextclouds_right_above_every_unregister() -> None:
    """Without the switch an unregister still hits the ExApp of every instance."""
    code = code_of(IMAGE_SWITCH.read_text(encoding="utf-8"))
    lines = code.splitlines()
    unregisters = [index for index, line in enumerate(lines) if THE_UNREGISTER in line]
    counts = [index for index, line in enumerate(lines) if THE_COUNT in line]
    assert unregisters, "92d runs no unregister at all"
    for unregister in unregisters:
        above = [count for count in counts if count < unregister]
        assert above, lines[unregister]
        assert unregister - max(above) <= THE_COUNT_IS_IMMEDIATE, lines[unregister]


def test_the_image_switch_reads_the_return_of_occ_upgrade_outside_the_tee() -> None:
    """Change 2, in the order of the L-03 fix: call, check, filter, mark, refuse."""
    text = IMAGE_SWITCH.read_text(encoding="utf-8")
    code = code_of(text)
    aufruf = code.index('occ upgrade >"$upgradelog" 2>&1 || upgrade_status=$?')
    gefiltert = code.index('cat "$upgradelog"')
    protokolliert = code.index("printf 'occ-upgrade-rueckgabewert %s\\n' \"$upgrade_status\"")
    gemerkt = code.index(': >"$WORK/upgrade-fehlt"')
    unregister = code.index(THE_UNREGISTER)
    register = code.index('occ app_api:app:register "$APP_ID" "$DAEMON"')
    verweigert = code.index('if [ -f "$WORK/upgrade-fehlt" ]; then')
    assert aufruf < gefiltert < protokolliert < gemerkt < unregister < register < verweigert
    # The call itself carries no pipe, it redirects into its own file.
    zeilen = [line for line in code.splitlines() if line.strip().startswith("occ upgrade")]
    assert len(zeilen) == 1, zeilen
    assert "|" not in zeilen[0].split("||")[0], zeilen[0]
    # The refusal stands below the pipeline and carries 40.
    _, _, unten = the_three_parts_of(text)
    block = unten[unten.index('if [ -f "$WORK/upgrade-fehlt" ]; then') :]
    assert block.split("\nfi\n")[0].rstrip().endswith("exit 40")


def test_the_image_switch_keeps_its_old_aborts_and_adds_40_and_41_below_the_pipeline() -> None:
    """36 to 39 stay where 92c put them; 40 and 41 are new and stand below the tee."""
    text = IMAGE_SWITCH.read_text(encoding="utf-8")
    vorlauf, mitte, unten = the_three_parts_of(text)
    assert mitte, "92d lost its phase A pipeline"
    assert unten, "92d lost its phase B pipeline"
    assert {"exit 36", "exit 37", "exit 38", "exit 39", "exit 40", "exit 41"} <= aborts_of(mitte) | aborts_of(unten)
    assert {"exit 36", "exit 37", "exit 39", "exit 40", "exit 41"} <= aborts_of(unten)
    assert aborts_of(vorlauf) == {"exit 2"}
    # Inside the phase B block nothing exits: an exit there leaves the subshell.
    block = text[text.index("# Phase B, und ab hier wird die Box veraendert.") : text.index(PIPELINE_CUT)]
    assert not aborts_of(code_of(block))


def test_the_image_switch_hangs_41_on_the_stock_gate_of_the_snapshot() -> None:
    """The gate reads 52111 / 37 / 0 and fails closed.

    Fail closed means the refusal asks for the mark of PASSING: a block that
    broke off before the gate leaves no mark, and that ends with 41 instead of
    the 0 that L-03 was about.
    """
    text = IMAGE_SWITCH.read_text(encoding="utf-8")
    assert 'BESTAND_INDEXIERT="${BESTAND_INDEXIERT:-52111}"' in text
    assert 'BESTAND_UEBERSPRUNGEN="${BESTAND_UEBERSPRUNGEN:-37}"' in text
    assert 'BESTAND_FEHLGESCHLAGEN="${BESTAND_FEHLGESCHLAGEN:-0}"' in text
    assert "printf 'bestandstor indexiert %s uebersprungen %s fehlgeschlagen %s\\n'" in text
    assert "occ findling:index" in code_of(text)
    # indexed from the state database of the running container, read only.
    assert "?mode=ro" in text
    _, _, unten = the_three_parts_of(text)
    block = unten[unten.index('if [ ! -f "$WORK/bestand-bestanden" ]; then') :]
    assert block.split("\nfi\n")[0].rstrip().endswith("exit 41")
    # 41 is the last refusal: every other finding names itself first.
    assert max(unten.index(line) for line in ("exit 36", "exit 37", "exit 39", "exit 40")) < unten.index("exit 41")


def test_the_image_switch_keeps_what_92c_promised_to_keep() -> None:
    """The tree hash, the tools directory, the limit and the switch line."""
    text = IMAGE_SWITCH.read_text(encoding="utf-8")
    assert 'WERKZEUGE="${WERKZEUGE:-$SKRIPTE/../../2026-09-v12-messung/skripte}"' in text
    assert 'sh "$WERKZEUGE/40b-baumhash.sh"' in text
    assert 'OUT="${OUT:-$SKRIPTE/../rohdaten}"' in text
    assert "sudo docker update --memory=2g --memory-swap=2g" in text
    assert "cgroup_wert memory.swap.max" in text
    assert "entladeschalter-ist" in text
    assert "92D-WECHSEL-FERTIG" in text
    assert "92C-WECHSEL-FERTIG" not in text


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("digest", [None, "", "abc123"])
def test_the_image_switch_refuses_a_run_without_a_digest(tmp_path: Path, digest: str | None) -> None:
    """No digest of the right shape, no run, no raw file."""
    answer = a_boxless_run(IMAGE_SWITCH, tmp_path, [], umgebung={"ABBILD_DIGEST": digest})
    assert answer.returncode == 2, answer
    assert "Benutzung:" in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# 92e, the rebuild with one changed environment variable.


def test_the_rebuild_reconstructs_from_docker_inspect_and_sets_the_limit_again() -> None:
    """The shape of the CI rebuild, carried into POSIX sh."""
    code = code_of(ENVIRONMENT_REBUILD.read_text(encoding="utf-8"))
    for needle in (
        "docker inspect",
        "docker create",
        "docker start",
        'docker rm -f "$CONTAINER"',
        "sudo docker update --memory=2g --memory-swap=2g",
        "memory.swap.max",
        "entladeschalter-ist",
        "neubau-fertig",
        "set -- --name",
        "{{.HostConfig.NetworkMode}}",
    ):
        assert needle in code, needle
    assert "--network host" not in code


def test_the_rebuild_knows_two_switches_and_refuses_the_ocr_languages_in_one_line() -> None:
    """Only the two switches of the trip, and the OCR languages are refused by name."""
    code = code_of(ENVIRONMENT_REBUILD.read_text(encoding="utf-8"))
    for switch in ALLOWED_SWITCHES:
        assert f"{switch})" in code, switch
    ocr_lines = [line for line in code.splitlines() if OCR_LANGUAGES in line]
    assert len(ocr_lines) == 1, ocr_lines
    assert "exit 2" in ocr_lines[0]
    assert "verweigert" in ocr_lines[0]


def test_the_rebuild_prints_names_of_the_environment_and_never_whole_lines() -> None:
    """APP_SECRET is in the environment, so the environment is only ever named.

    Statically: the only reading of the new env file that reaches the output is
    cut -d= -f1, no line cats one of the env lists, and nothing calls env or
    printenv. The behaviour test below proves the same with a planted secret.
    """
    code = code_of(ENVIRONMENT_REBUILD.read_text(encoding="utf-8"))
    assert 'cut -d= -f1 "$ENVDATEI"' in code
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("cat "):
            assert "umgebung" not in stripped, stripped
            assert "ENVDATEI" not in stripped, stripped
        assert not stripped.startswith(("env ", "printenv")), stripped
    assert 'chmod 600 "$ENVDATEI"' in code


def test_the_rebuild_keeps_its_aborts_below_the_pipeline() -> None:
    """42 and 43 below the tee, 2 above it, and nothing exits inside the block."""
    text = ENVIRONMENT_REBUILD.read_text(encoding="utf-8")
    code = code_of(text)
    oben, marker, unten = code.partition(PIPELINE_CUT)
    assert marker
    assert aborts_of(unten) == {"exit 42", "exit 43"}
    block = oben[oben.rindex("\n{\n") :]
    assert not aborts_of(block)
    assert aborts_of(oben[: oben.rindex("\n{\n")]) == {"exit 2"}


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["FINDLING_LANGUAGES=de,en", "zwei"],
        ["FINDLING_LANGUAGES"],
        ["=de"],
        ["FINDLING_OCR_LANGUAGES=deu+eng"],
        ["APP_SECRET=x"],
        ["FINDLING_LANGUAGES=de;en"],
        ["FINDLING_LANGUAGES="],
        ["FINDLING_EMBED_IDLE_RELEASE_SECONDS=12s"],
    ],
)
def test_the_rebuild_refuses_every_other_argument(tmp_path: Path, arguments: list[str]) -> None:
    """Wrong arguments end with 2 before the first docker call and before any file."""
    answer = a_boxless_run(ENVIRONMENT_REBUILD, tmp_path, arguments)
    assert answer.returncode == 2, answer
    assert "Benutzung:" in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


# A docker client that answers like one for exactly one container, behind a
# fake sudo on PATH. It records every call and copies the env file handed to
# docker create, so that the test can read what the new container would carry.
FAKE_SUDO = r"""#!/bin/sh
printf '%s\n' "$*" >>"$FAKE/aufrufe"
if [ "$1" = cat ]; then
    case "$2" in
    *memory.max) printf '%s\n' "${FAKE_GRENZE:-2147483648}" ;;
    *memory.swap.max) printf '0\n' ;;
    *) exit 1 ;;
    esac
    exit 0
fi
[ "$1" = docker ] || exit 1
shift
unterbefehl=$1
if [ "$unterbefehl" = image ]; then
    unterbefehl=image-$2
fi
vorlage=
vorher=
for argument in "$@"; do
    if [ "$vorher" = --format ] || [ "$vorher" = -f ]; then
        vorlage=$argument
    fi
    vorher=$argument
done
case "$unterbefehl" in
inspect)
    case "$vorlage" in
    '') printf '[{}]\n' ;;
    *'.Id'*) printf 'cafe0123\n' ;;
    *'.Config.Env'*)
        if [ -f "$FAKE/env-neu" ]; then
            cat "$FAKE/env-neu"
        else
            printf 'APP_SECRET=%s\n' "$FAKE_SECRET"
            printf 'FINDLING_LANGUAGES=de,en\n'
            printf 'APP_PERSISTENT_STORAGE=/nc_app_findling_backend_data\n\n'
        fi
        ;;
    *'.Config.Image'*) printf 'ghcr.io/street1983nk/findling_backend:dev\n' ;;
    *'NetworkMode'*) printf 'nextcloud-aio\n' ;;
    *'RestartPolicy'*) printf 'unless-stopped\n' ;;
    *'.Config.Entrypoint'*) printf '%s\n' "${FAKE_ENTRYPOINT:-[\"/entrypoint.sh\"]}" ;;
    *'.Config.Cmd'*) printf 'null\n' ;;
    *'.Mounts'*) printf 'volume|nc_app_findling_backend_data||/nc_app_findling_backend_data|true\n\n' ;;
    *'.Config.Labels'*) printf 'com.docker.compose.project=aio\n\n' ;;
    *) exit 1 ;;
    esac
    ;;
image-inspect)
    case "$vorlage" in
    *'.Config.Entrypoint'*) printf '["/entrypoint.sh"]\n' ;;
    *'.Config.Cmd'*) printf 'null\n' ;;
    *) exit 1 ;;
    esac
    ;;
exec) exit 1 ;;
create)
    vorher=
    for argument in "$@"; do
        if [ "$vorher" = --env-file ]; then
            cp "$argument" "$FAKE/env-neu"
        fi
        vorher=$argument
    done
    ;;
rm | start | update | cp) ;;
*) exit 1 ;;
esac
exit 0
"""


def a_rebuild_against_a_fake_docker(
    tmp_path: Path, argument: str, **fake: str
) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    """92e as a program, with a fake sudo in front of PATH and nothing real behind it."""
    shell = shutil.which("sh")
    assert shell is not None
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    sudo = bin_dir / "sudo"
    sudo.write_text(FAKE_SUDO, encoding="utf-8", newline="\n")
    sudo.chmod(sudo.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    state = tmp_path / "fake"
    state.mkdir()
    out = tmp_path / "out"
    environment = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        "OUT": out.as_posix(),
        "FAKE": state.as_posix(),
        "FAKE_SECRET": FAKE_SECRET,
        **fake,
    }
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [shell, ENVIRONMENT_REBUILD.as_posix(), argument],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=environment,
    )
    return answer, state, out


def everything_the_run_left(out: Path, answer: subprocess.CompletedProcess[str]) -> str:
    """Standard output, standard error and every file under OUT, as one text."""
    files = [path.read_text(encoding="utf-8") for path in sorted(out.rglob("*")) if path.is_file()]
    return "\n".join([answer.stdout, answer.stderr, *files])


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_rebuild_changes_one_line_and_keeps_the_secret_invisible(tmp_path: Path) -> None:
    """The one behaviour this tool promises, against a fake docker.

    The new env file carries the new switch exactly once, keeps APP_SECRET and
    everything else, and the secret shows up nowhere a report could read it.
    """
    answer, state, out = a_rebuild_against_a_fake_docker(tmp_path, "FINDLING_LANGUAGES=de,en,fr")
    assert answer.returncode == 0, answer
    assert "92E-UMGEBUNG-FERTIG" in answer.stdout
    left = everything_the_run_left(out, answer)
    assert FAKE_SECRET not in left
    assert "APP_SECRET" in left  # named, never valued
    neu = (state / "env-neu").read_text(encoding="utf-8").splitlines()
    assert [line for line in neu if line.startswith("FINDLING_LANGUAGES=")] == ["FINDLING_LANGUAGES=de,en,fr"]
    assert f"APP_SECRET={FAKE_SECRET}" in neu
    assert "APP_PERSISTENT_STORAGE=/nc_app_findling_backend_data" in neu
    calls = (state / "aufrufe").read_text(encoding="utf-8")
    create = next(line for line in calls.splitlines() if line.startswith("docker create"))
    assert "--network nextcloud-aio" in create
    assert "--restart unless-stopped" in create
    assert "--mount type=volume,source=nc_app_findling_backend_data,target=/nc_app_findling_backend_data" in create
    assert "--label com.docker.compose.project=aio" in create
    assert "docker update --memory=2g --memory-swap=2g" in calls
    assert "schalter-vorher FINDLING_LANGUAGES de,en" in answer.stdout
    assert "schalter-ist FINDLING_LANGUAGES de,en,fr" in answer.stdout
    assert "speichergrenze-ist 2147483648/0" in answer.stdout
    assert "entladeschalter-ist 0 werksstand" in answer.stdout
    assert "tunnel-zertifikate keine" in answer.stdout


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_rebuild_removes_nothing_when_the_container_overrides_its_entrypoint(tmp_path: Path) -> None:
    """43 before docker rm: an override would be lost silently otherwise."""
    answer, state, _ = a_rebuild_against_a_fake_docker(
        tmp_path, "FINDLING_EMBED_IDLE_RELEASE_SECONDS=120", FAKE_ENTRYPOINT='["/bin/other"]'
    )
    assert answer.returncode == 43, answer
    calls = (state / "aufrufe").read_text(encoding="utf-8")
    assert "docker rm" not in calls
    assert "docker create" not in calls
    assert "entrypoint-gleich nein" in answer.stdout


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
def test_the_rebuild_ends_with_42_when_the_limit_does_not_hold(tmp_path: Path) -> None:
    """The limit is read from the cgroup, and a cgroup without it is 42."""
    answer, _, _ = a_rebuild_against_a_fake_docker(
        tmp_path, "FINDLING_EMBED_IDLE_RELEASE_SECONDS=120", FAKE_GRENZE="max"
    )
    assert answer.returncode == 42, answer
    assert "grenze-gesetzt nein" in answer.stdout
    assert "entladeschalter-ist 120" in answer.stdout


# ---------------------------------------------------------------------------
# 90e and 91m, the two readers. Loaded by path, because a file name that starts
# with a digit is no module name.


def a_script_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def single_list() -> ModuleType:
    return a_script_module(SINGLE_LIST, "findling_v13_single_list")


@pytest.fixture(scope="module")
def slow_call_reader() -> ModuleType:
    return a_script_module(SLOW_CALL_READER, "findling_v13_slow_call_reader")


# The marks of a state database as the snapshot is expected to carry them,
# shortened to what the gate reads. The values are shapes, not the real ones.
MARKS = {
    "schema_version": "1",
    "languages": "de,en",
    "wordlist_hash_nl": "off",
    "embedding_version": "multilingual-e5-small/int8/384/512",
    "index_version": "3",
    "tantivy_version": "tantivy v0.26.0, index_format v7",
    "analyzer_version": "7",
}

# Paths that carry a user name and a folder, so that the test can prove neither
# reaches the output.
FILES = (
    (11, "files/alice/Geheim/Steuer 2025.pdf", 4096, "indexed", None),
    (12, "files/alice/Geheim/scan.TIFF", 99, "skipped", "too_large"),
    (13, "files/bob/Privat/kaputt.docx", 7, "failed", "extract_error"),
    (14, "files/bob/Privat/ohne_endung", 1, "skipped", "unsupported"),
    (15, "files/bob/Privat/weg.pdf", 5, "failed", "extract_error"),
)


def a_state_database(path: Path, *, marks: dict[str, str] | None = None, file_id: bool = True) -> Path:
    """A state.db of the shape store/schema.sql creates, with only the tables read here."""
    connection = sqlite3.connect(path)
    key = "file_id" if file_id else "fid"
    connection.execute(
        f"create table files ({key} integer primary key, path text not null, size integer not null,"
        " state text not null, reason text, deleted_at integer)"
    )
    connection.execute("create table meta (key text primary key, value text not null)")
    for row in FILES:
        connection.execute("insert into files values (?, ?, ?, ?, ?, null)", row)
    # The tombstone of 15: a deleted file is no longer part of the stock.
    connection.execute("update files set deleted_at = 1 where path like '%weg.pdf'")
    for name, value in (MARKS if marks is None else marks).items():
        connection.execute("insert into meta values (?, ?)", (name, value))
    connection.commit()
    connection.close()
    return path


def test_the_single_list_opens_the_database_read_only_and_writes_nothing() -> None:
    """mode=ro through a URI, and no statement of the file writes."""
    text = SINGLE_LIST.read_text(encoding="utf-8")
    assert 'f"file:{database}?mode=ro", uri=True' in text
    tree = ast.parse(text)
    docstring = ast.get_docstring(tree, clean=False)
    literals = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value != docstring
    ]
    statements = [literal for literal in literals if re.match(r"\s*(select|pragma)\b", literal)]
    assert statements, "the reader carries no SQL at all"
    for literal in literals:
        for word in ("insert", "update", "delete", "drop", "create", "attach", "vacuum"):
            assert not re.search(rf"\b{word}\b", literal), (word, literal)


def test_the_single_list_leaves_a_database_it_read_unchanged(tmp_path: Path, single_list: ModuleType) -> None:
    """The bytes of the database are the same before and after both subcommands."""
    database = a_state_database(tmp_path / "state.db")
    before = database.read_bytes()
    assert single_list.main(["liste", "--database", str(database)]) == 0
    assert single_list.main(["marken", "--database", str(database)]) == 0
    assert database.read_bytes() == before


def test_the_single_list_prints_each_skipped_and_failed_file_without_its_path(
    tmp_path: Path, single_list: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    database = a_state_database(tmp_path / "state.db")
    assert single_list.main(["liste", "--database", str(database)]) == 0
    printed = capsys.readouterr().out
    answer = json.loads(printed)
    assert answer["zaehlung_je_state"] == {"failed": 1, "indexed": 1, "skipped": 2}
    assert answer["einzelliste_anzahl"] == 3
    assert answer["einzelliste"] == [
        {"file_id": 13, "endung": "docx", "groesse": 7, "state": "failed", "reason": "extract_error"},
        {"file_id": 12, "endung": "tiff", "groesse": 99, "state": "skipped", "reason": "too_large"},
        {"file_id": 14, "endung": "", "groesse": 1, "state": "skipped", "reason": "unsupported"},
    ]
    for private in ("alice", "bob", "Geheim", "Privat", "kaputt", "scan", "files/", str(tmp_path)):
        assert private not in printed, private


def test_the_single_list_refuses_a_schema_without_file_id(
    tmp_path: Path, single_list: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    database = a_state_database(tmp_path / "state.db", file_id=False)
    assert single_list.main(["liste", "--database", str(database)]) == 2
    assert "file_id" in capsys.readouterr().err


def test_the_single_list_refuses_a_database_that_is_not_there(
    tmp_path: Path, single_list: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    """Read only never creates, and a missing database is a sentence and a 2."""
    missing = tmp_path / "nicht-da.db"
    assert single_list.main(["liste", "--database", str(missing)]) == 2
    assert "nicht lesbar" in capsys.readouterr().err
    assert not missing.exists()


def expectations_of(marks: dict[str, str]) -> list[str]:
    return [argument for name, value in marks.items() for argument in ("--erwartung", f"{name}={value}")]


def test_the_single_list_passes_the_mark_gate_when_every_mark_is_equal(
    tmp_path: Path, single_list: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    database = a_state_database(tmp_path / "state.db")
    assert single_list.main(["marken", "--database", str(database), *expectations_of(MARKS)]) == 0
    printed = capsys.readouterr().out
    assert "marke embedding_version multilingual-e5-small/int8/384/512" in printed
    assert "marken-urteil gleich" in printed


def test_the_single_list_excuses_the_three_rebuild_marks(
    tmp_path: Path, single_list: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    """schema_version, languages and wordlist_hash_nl are what MESS-08 measures."""
    stored = {name: value for name, value in MARKS.items() if name != "wordlist_hash_nl"}
    database = a_state_database(tmp_path / "state.db", marks=stored)
    expected = {**MARKS, "schema_version": "2", "languages": "de,en,nl", "wordlist_hash_nl": "abc"}
    assert single_list.main(["marken", "--database", str(database), *expectations_of(expected)]) == 0
    printed = capsys.readouterr().out
    assert "marke-umbau wordlist_hash_nl ist fehlt erwartet abc" in printed
    assert "legacy-schritt schema_version 1 nach 2" in printed
    assert "marken-urteil umbau" in printed


@pytest.mark.parametrize(
    ("name", "value"),
    [("analyzer_version", "8"), ("index_version", "4"), ("tantivy_version", "tantivy v0.27.0, index_format v8")],
)
def test_the_single_list_ends_with_44_for_a_foreign_index_mark(
    tmp_path: Path, single_list: ModuleType, name: str, value: str
) -> None:
    database = a_state_database(tmp_path / "state.db")
    assert single_list.main(["marken", "--database", str(database), *expectations_of({**MARKS, name: value})]) == 44


def test_the_single_list_ends_with_44_for_a_missing_index_mark(tmp_path: Path, single_list: ModuleType) -> None:
    stored = {name: value for name, value in MARKS.items() if name != "analyzer_version"}
    database = a_state_database(tmp_path / "state.db", marks=stored)
    assert single_list.main(["marken", "--database", str(database), *expectations_of(MARKS)]) == 44


def test_the_single_list_follows_the_two_loosened_comparisons_of_the_store(
    tmp_path: Path, single_list: ModuleType
) -> None:
    """index_version is a floor and tantivy_version decides on index_format."""
    database = a_state_database(tmp_path / "state.db")
    expected = {**MARKS, "index_version": "2", "tantivy_version": "tantivy v0.26.2, index_format v7"}
    assert single_list.main(["marken", "--database", str(database), *expectations_of(expected)]) == 0


def test_the_single_list_ends_with_45_for_a_foreign_embedding_mark(tmp_path: Path, single_list: ModuleType) -> None:
    database = a_state_database(tmp_path / "state.db")
    expected = {**MARKS, "embedding_version": "multilingual-e5-small/int8/384/256"}
    assert single_list.main(["marken", "--database", str(database), *expectations_of(expected)]) == 45
    # 44 is the larger finding and wins when both apply.
    both = {**expected, "analyzer_version": "8"}
    assert single_list.main(["marken", "--database", str(database), *expectations_of(both)]) == 44


def test_the_single_list_refuses_an_expectation_without_a_name(tmp_path: Path, single_list: ModuleType) -> None:
    database = a_state_database(tmp_path / "state.db")
    with pytest.raises(SystemExit) as refusal:
        single_list.main(["marken", "--database", str(database), "--erwartung", "ohne-gleichheitszeichen"])
    assert refusal.value.code == 2


LOG_LINE = {
    "reqId": "abcDEF123",
    "level": 1,
    "time": "2026-09-30T10:15:00+00:00",
    "remoteAddr": "192.0.2.7",
    "user": "alice",
    "app": "findling",
    "method": "GET",
    "url": "/ocs/v2.php/search/providers/findling/search?term=Steuerbescheid",
    "message": "Findling: slow backend call",
    "userAgent": "Mozilla/5.0",
    "version": "34.0.3.1",
    "data": {"app": "findling", "path": "/search", "innerMs": 1834.2, "ceilingMs": 2000.0},
}


def a_log(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def line_with(**changes: object) -> str:
    return json.dumps({**LOG_LINE, **changes})


def read_the_log(reader: ModuleType, log: Path, capsys: pytest.CaptureFixture[str]) -> list[str]:
    arguments = ["--log", str(log), "--von", "2026-09-30T10:00:00Z", "--bis", "2026-09-30T11:00:00Z"]
    assert reader.main([*arguments, "--stufe", "kalt"]) == 0
    return capsys.readouterr().out.splitlines()


def test_the_slow_call_reader_counts_the_m01_lines_of_its_window(
    tmp_path: Path, slow_call_reader: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    log = a_log(
        tmp_path / "nextcloud.log",
        [
            line_with(),
            line_with(
                time="2026-09-30T10:40:00+00:00", data={"path": "/snippets", "innerMs": 2010.5, "ceilingMs": 2000}
            ),
            # outside the window, before and after
            line_with(time="2026-09-30T09:59:59+00:00"),
            line_with(time="2026-09-30T11:00:01+00:00"),
            # another message and another app
            line_with(message="Findling: something else"),
            json.dumps({"time": "2026-09-30T10:20:00+00:00", "message": "Login failed", "level": 2}),
            # a line that is no JSON and one whose number is a bool
            "{this is not json",
            line_with(data={"path": "/search", "innerMs": True, "ceilingMs": 2000.0}),
        ],
    )
    printed = read_the_log(slow_call_reader, log, capsys)
    assert printed == [
        "stufe kalt langsame-aufrufe 2",
        "aufruf 2026-09-30T10:15:00Z /search innerMs 1834.2 ceilingMs 2000.0",
        "aufruf 2026-09-30T10:40:00Z /snippets innerMs 2010.5 ceilingMs 2000.0",
        "maximum innerMs 2010.5 ceilingMs 2000.0",
        "kaputte-zeilen 2",
    ]


def test_the_slow_call_reader_reads_the_context_where_this_nextcloud_put_it(
    tmp_path: Path, slow_call_reader: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    moved = {key: value for key, value in LOG_LINE.items() if key != "data"}
    log = a_log(
        tmp_path / "nextcloud.log",
        [
            json.dumps({**moved, "context": {"path": "/search", "innerMs": 1200, "ceilingMs": 2000}}),
            json.dumps({**moved, "path": "/search", "innerMs": 1100.0, "ceilingMs": 2000.0}),
        ],
    )
    printed = read_the_log(slow_call_reader, log, capsys)
    assert printed[0] == "stufe kalt langsame-aufrufe 2"


def test_the_slow_call_reader_reads_the_numbers_nextcloud_34_writes_as_strings(
    tmp_path: Path, slow_call_reader: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    """The shape of the dress rehearsal of 22-06: every context value is a string."""
    log = a_log(
        tmp_path / "nextcloud.log",
        [
            line_with(data={"app": "findling", "path": "/search", "innerMs": "1171.2", "ceilingMs": "1500"}),
            # a string that is no number, and one that is no finite number
            line_with(data={"path": "/search", "innerMs": "schnell", "ceilingMs": "1500"}),
            line_with(data={"path": "/search", "innerMs": "nan", "ceilingMs": "1500"}),
        ],
    )
    printed = read_the_log(slow_call_reader, log, capsys)
    assert printed == [
        "stufe kalt langsame-aufrufe 1",
        "aufruf 2026-09-30T10:15:00Z /search innerMs 1171.2 ceilingMs 1500.0",
        "maximum innerMs 1171.2 ceilingMs 1500.0",
        "kaputte-zeilen 2",
    ]


def test_the_slow_call_reader_answers_unklar_for_a_log_it_cannot_read(
    tmp_path: Path, slow_call_reader: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    printed = read_the_log(slow_call_reader, tmp_path / "nicht-da.log", capsys)
    assert printed == ["stufe kalt langsame-aufrufe unklar"]


def test_the_slow_call_reader_says_none_and_not_unklar_for_a_quiet_window(
    tmp_path: Path, slow_call_reader: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    log = a_log(tmp_path / "nextcloud.log", [line_with(time="2026-09-30T08:00:00+00:00")])
    printed = read_the_log(slow_call_reader, log, capsys)
    assert printed == ["stufe kalt langsame-aufrufe 0", "maximum innerMs keins", "kaputte-zeilen 0"]


def test_the_slow_call_reader_prints_no_user_data(
    tmp_path: Path, slow_call_reader: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    """Only time, path, innerMs and ceilingMs leave the reader (T-22-09)."""
    log = a_log(tmp_path / "nextcloud.log", [line_with()])
    printed = "\n".join(read_the_log(slow_call_reader, log, capsys))
    for private in ("alice", "192.0.2.7", "Steuerbescheid", "abcDEF123", "Mozilla", "/ocs/"):
        assert private not in printed, private


def test_the_slow_call_reader_refuses_a_window_that_is_no_time(tmp_path: Path, slow_call_reader: ModuleType) -> None:
    with pytest.raises(SystemExit) as refusal:
        slow_call_reader.main(["--log", str(tmp_path / "x"), "--von", "gestern", "--bis", "heute", "--stufe", "s"])
    assert refusal.value.code == 2


@pytest.mark.parametrize("script", [SINGLE_LIST, SLOW_CALL_READER], ids=lambda path: path.name)
def test_the_two_readers_bring_no_third_party_library(script: Path) -> None:
    """The host python of the box runs them, and it has nothing installed."""
    tree = ast.parse(script.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 0
    }
    assert imported <= {
        "__future__",
        "argparse",
        "collections",
        "datetime",
        "json",
        "math",
        "posixpath",
        "sqlite3",
        "sys",
    }
    assert script.read_text(encoding="utf-8").startswith("#!/usr/bin/env python3\n")
