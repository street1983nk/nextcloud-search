"""The house rules of the measurement scripts, as a gate instead of a review note.

docs/measurements holds the scripts of every measurement this project has run,
next to the raw data they produced. They are copied onto a rented Linux box and
started there, which puts them under the same promises as the operating tools of
scripts/ops, and test_ops_scripts.py holds those promises only for that one
directory.

The part of this file that exists first is the recipe of the tree hash. Both
predecessor reports claim that the image and the working tree are the same state,
and in both the raw data of that step is empty: 40-abbild.log line 52 carries the
section title "Baumhash im Abbild" and nothing under it, and 61-wechsel.txt line
4 carries its English counterpart and nothing under it. The cause in 40-abbild.sh
is a docker run without -i, so the python in the image got no standard input and
read EOF at once. The answer of plan 10-01 is a recipe in a file that is called
with arguments, and these assertions are what keeps that recipe from drifting:
the two figures of this commit are written down, and a hash over nothing is a
failure rather than a result.

The rest of this file has two scopes of different width, and the difference is
the point rather than an oversight. Wide, over every .py and .sh under
docs/measurements/**/skripte/: no carriage return and no dash. Both hold for the
whole stock since plan 10-01 renormalised five files and added the checkout rule
that keeps them normalised, so the wide scope is a statement about the tree and
not a wager on it.

Narrow, over the directory of this run alone: a shebang on the first line, no
path of one machine, and no password on a command line. It is narrow because
45-suchlast.py of the semantic run puts "/home/ubuntu/work" into sys.path and
imports drillhelfer from it, drillhelfer does not live in this repository, and
that file is history with its raw data lying next to it. A gate that demanded it
be rewritten would blur the origin of those raw data to buy nothing, so the three
promises that only a new script can keep are asked of the new scripts.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MEASUREMENTS_DIR = REPO_ROOT / "docs" / "measurements"
RUN_DIR = MEASUREMENTS_DIR / "2026-09-vergleichsmessung-m7g" / "skripte"
TREE_HASH = RUN_DIR / "40b-baumhash.py"
TREE_HASH_PROOF = RUN_DIR / "40b-baumhash.sh"
OPS_GATE = Path(__file__).resolve().parent / "test_ops_scripts.py"

# The two files of the full run that can be held to a promise without a box: the
# reader the watchman decides on, and the observer whose recordings are checked
# into this repository.
READER = RUN_DIR / "96c-lesen.py"
OBSERVER = RUN_DIR / "96d-statusbeobachter.py"

# The keys one recording of the observer may carry, and no others. Nine on the
# top level plus the nested one, which is where the counters of both tracks live.
# Written down here rather than read out of the observer, because a gate that
# asks the tool for its own contract agrees with it no matter what it writes.
RECORDING_KEYS = frozenset(
    {
        "at",
        "runState",
        "indexed",
        "indexedPercent",
        "embedded",
        "embeddedPercent",
        "scheduled",
        "running",
        "backendReachable",
        "backend",
    }
)
BACKEND_RECORDING_KEYS = frozenset({"indexed", "embedded"})

# The two kinds of file that are run. A directory of measurement scripts also
# holds other things, for instance the .claude-active of the semantic run, and a
# gate that read every file would fail on the first note somebody leaves there.
SCRIPT_SUFFIXES = frozenset({".py", ".sh"})

# The two shebangs a script of this run may carry.
SHEBANGS = (b"#!/bin/sh\n", b"#!/usr/bin/env python3\n")

# A password belongs in an environment variable, never in an argument, because an
# argument stands in the process list of the box and in every log that records the
# command. The permitted shape is the one search_load.py uses, --password-env,
# which carries the name of the variable and not the value, and which is not
# matched by either of these two because both demand a space or an equals sign
# where it carries a hyphen.
PASSWORD_OPTIONS = ("--password ", "--password=")

# The short form is a different problem. Written as a bare substring, "-p " means
# "create the parent directories" far more often than it means a password, and a
# gate that goes red on mkdir -p is a gate somebody switches off inside a week. So
# it counts only behind a program that really takes a password that way.
PASSWORD_SHORT_FORM = re.compile(r"\b(?:mysql|mariadb|mysqldump|redis-cli|smbclient)\b[^\n]*?\s-p\s*\S")
SHORT_FORM_NAME = "-p behind a program that takes a password"

# A variable with a default is the one place a path of the box may be written
# down, because it is the place a reader can change without reading the body.
DEFAULT_ASSIGNMENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*="?\$\{[A-Za-z_][A-Za-z0-9_]*:-')

# The state this commit measures, nachgerechnet on 2026-09-09. They are written
# down here and not computed, because a test that recomputes the recipe it is
# guarding agrees with itself no matter what the recipe does.
PACKAGE_FILES = 54
PACKAGE_TREE_HASH = "6c47cd219c430bccc9d5d57b1de1d2ff9f8672fa4f42b1160d0a31efb9367476"
PHP_FILES = 58
PHP_TREE_HASH = "26b55908b12f8139b86d8c8a7c391457c550b2584fb8d639a3957e8b6feb91ae"

# Assembled from code points so that this file does not carry the characters it
# forbids and fail on itself. Same construction as in test_ops_scripts.py.
DASHES = (chr(0x2014), chr(0x2013))

# Every diagnosis of the recipe names the tool first. The prefix is asserted and
# not decoration: CPython answers a missing script file with exit code 2 as well,
# so without it the two refusal assertions below would have been satisfied by the
# absence of the very script they are about.
DIAGNOSIS_PREFIX = "40b-baumhash:"


def constant_of_the_ops_gate(name: str) -> tuple[str, ...]:
    """One named tuple constant, read out of the syntax tree of test_ops_scripts.py.

    Read rather than imported, because tests/ is not a package: an import would
    work under pytest and not under pyright. Read rather than copied, because two
    definitions of the same list are two definitions that drift apart, and the
    whole point of taking it from there is that both gates forbid the same shapes.
    """
    tree = ast.parse(OPS_GATE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return tuple(ast.literal_eval(node.value))
    message = f"{name} is not defined in {OPS_GATE.name}"
    raise AssertionError(message)


# The shapes that tie a tool to one machine, from the gate that first wrote them
# down. Not a second copy: one definition, two gates.
MACHINE_SHAPES = constant_of_the_ops_gate("MACHINE_SHAPES")


def imported_packages(text: str) -> set[str]:
    """The top level package of every import in the file.

    Read out of the syntax tree rather than out of the lines, for the reason the
    same reader in test_ops_scripts.py gives: an import inside a function is
    still an import, and a text search for "import " finds the word in every
    second docstring of this repository.
    """
    packages: set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            packages.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            packages.add(node.module.split(".")[0])
    return packages


def run_the_recipe(root: Path, pattern: str) -> subprocess.CompletedProcess[str]:
    """The recipe as a subprocess, in the shape the box runs it.

    Not imported: the file name begins with a digit and is therefore not a valid
    module name. Running it as a program is also the more honest test, because
    the exit code is half of what this script promises.
    """
    return subprocess.run(  # noqa: S603 - an argument list, never a shell
        [sys.executable, str(TREE_HASH), str(root), pattern],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def reading(answer: subprocess.CompletedProcess[str]) -> tuple[int, str]:
    """The two lines the recipe prints, and the promise that there is no third."""
    assert answer.returncode == 0, answer.stderr
    lines = answer.stdout.splitlines()
    assert len(lines) == 2, lines
    assert lines[0].startswith("dateien: "), lines[0]
    assert lines[1].startswith("baumhash: "), lines[1]
    return int(lines[0].removeprefix("dateien: ")), lines[1].removeprefix("baumhash: ")


def stage_a_tree(root: Path, line_ending: bytes) -> None:
    """Three python files over two levels, written with the ending that is asked for."""
    (root / "paket").mkdir(parents=True)
    first = line_ending.join([b"# the head of the file", b"value = 1", b""])
    second = line_ending.join([b"value = 2", b""])
    (root / "eins.py").write_bytes(first)
    (root / "paket" / "zwei.py").write_bytes(first)
    (root / "paket" / "drei.py").write_bytes(second)


def test_the_recipe_ignores_the_line_ending_of_every_file(tmp_path: Path) -> None:
    """The whole reason the recipe normalises: the tree comes from Windows.

    The working tree of this project is checked out with core.autocrlf enabled,
    so the same commit carries CRLF here and LF in the image. Without the
    normalisation the proof of equal state would report two different hashes for
    one state, which is worse than no proof at all.
    """
    crlf = tmp_path / "crlf"
    lf = tmp_path / "lf"
    stage_a_tree(crlf, b"\r\n")
    stage_a_tree(lf, b"\n")

    crlf_count, crlf_hash = reading(run_the_recipe(crlf, "**/*.py"))
    lf_count, lf_hash = reading(run_the_recipe(lf, "**/*.py"))

    assert crlf_count == lf_count == 3
    assert crlf_hash == lf_hash


def test_the_recipe_notices_a_single_changed_byte(tmp_path: Path) -> None:
    """A proof that survives an edited file proves nothing."""
    before = tmp_path / "before"
    after = tmp_path / "after"
    stage_a_tree(before, b"\n")
    stage_a_tree(after, b"\n")
    (after / "paket" / "drei.py").write_bytes(b"value = 3\n")

    _, before_hash = reading(run_the_recipe(before, "**/*.py"))
    _, after_hash = reading(run_the_recipe(after, "**/*.py"))

    assert before_hash != after_hash


def test_the_recipe_notices_a_renamed_file(tmp_path: Path) -> None:
    """The relative path goes into the digest, so a move is a change.

    A recipe over contents alone would call a package with two swapped module
    names the same state, and that is exactly the sort of difference that makes
    an import fail in the image and not in the tree.
    """
    before = tmp_path / "before"
    after = tmp_path / "after"
    stage_a_tree(before, b"\n")
    stage_a_tree(after, b"\n")
    (after / "paket" / "drei.py").rename(after / "paket" / "vier.py")

    before_count, before_hash = reading(run_the_recipe(before, "**/*.py"))
    after_count, after_hash = reading(run_the_recipe(after, "**/*.py"))

    assert before_count == after_count == 3
    assert before_hash != after_hash


def test_the_recipe_reproduces_the_tree_hash_of_the_python_package() -> None:
    """The figure the report quotes, measured against the tree it came from.

    This is the assertion that makes the recipe unchangeable: an improvement to
    it would yield another hash and take the comparability against 278fab52 of
    the follow up measurement with it.
    """
    count, hexdigest = reading(run_the_recipe(REPO_ROOT / "backend" / "src" / "findling", "**/*.py"))
    assert count == PACKAGE_FILES
    assert hexdigest == PACKAGE_TREE_HASH


def test_the_recipe_reproduces_the_tree_hash_of_the_php_half() -> None:
    """The other half of the state, and it is measured with the same recipe."""
    count, hexdigest = reading(run_the_recipe(REPO_ROOT / "php", "**/*.php"))
    assert count == PHP_FILES
    assert hexdigest == PHP_TREE_HASH


def test_the_recipe_refuses_a_root_that_does_not_exist(tmp_path: Path) -> None:
    """A mistyped path must not answer with a hash over nothing.

    This is the failure of both predecessors turned around. There the step
    produced no line at all and the report claimed the equality anyway, so the
    empty result has to cost an exit code.
    """
    answer = run_the_recipe(tmp_path / "nowhere", "**/*.py")
    assert answer.returncode == 2, answer
    assert "baumhash:" not in answer.stdout
    assert answer.stderr.startswith(DIAGNOSIS_PREFIX), answer.stderr


def test_the_recipe_refuses_an_empty_result_instead_of_hashing_nothing(tmp_path: Path) -> None:
    """An existing directory in which the glob matches nothing is the same mistake."""
    empty = tmp_path / "leer"
    empty.mkdir()
    answer = run_the_recipe(empty, "**/*.py")
    assert answer.returncode == 2, answer
    assert "baumhash:" not in answer.stdout
    assert answer.stderr.startswith(DIAGNOSIS_PREFIX), answer.stderr


def test_the_recipe_brings_no_third_party_library() -> None:
    """Standard library only, because it runs inside an image that is offline.

    The image is started with --network none for this step, and backend/uv.lock
    does not move for a measurement script.
    """
    outside = sorted(imported_packages(TREE_HASH.read_text(encoding="utf-8")) - set(sys.stdlib_module_names))
    assert not outside, outside


def test_the_proof_calls_the_recipe_as_an_argument_and_not_over_a_heredoc() -> None:
    """The one line that separates this step from the two empty predecessors.

    40-abbild.sh handed the recipe to the python in the image on standard input
    and forgot -i, so the interpreter read EOF and printed nothing. An argument
    needs no standard input, so the shape itself is the fix.
    """
    text = TREE_HASH_PROOF.read_text(encoding="utf-8")
    assert TREE_HASH.name in text
    assert "<<'PY'" not in text
    assert "docker cp" in text or "-v " in text


def test_the_proof_checks_its_own_raw_file_for_three_tree_hashes() -> None:
    """Nobody looked at the raw file, so the script looks at it.

    Three sections, three hashes: the package inside the image, the package in
    the working tree, and the php half. A run that produced fewer has to end with
    an error rather than with a report that quotes a blank.
    """
    text = TREE_HASH_PROOF.read_text(encoding="utf-8")
    assert "40b-baumhash.txt" in text
    assert "baumhash:" in text
    assert "baumhash-gleich" in text


# The count that guards --rm-data. Pitfall 5 of the research turned into a gate,
# and it is the one assertion of this file that was written after a run had
# already been paid for: the default counted the images of the docker hub, this
# box runs its All-in-One instance from a release channel, and so the count came
# out 0 with exactly one server running. Refusing on 0 was safe. What is not safe
# is the other direction, and it is the reason this test exists: with the second,
# hand rolled Nextcloud of 07.09. on the daemon the old pattern counted exactly
# 1 and would have let --rm-data through, in precisely the situation the count
# was put there to stop.

# The nine images that really ran on the box on 2026-09-09, read out of docker ps.
RUNNING_IMAGES_OF_THE_BOX = (
    "ghcr.io/street1983nk/findling_backend:dev",
    "registry:2",
    "ghcr.io/nextcloud-releases/aio-apache:latest",
    "ghcr.io/nextcloud-releases/aio-nextcloud:latest",
    "ghcr.io/nextcloud-releases/aio-redis:latest",
    "ghcr.io/nextcloud-releases/aio-postgresql:latest",
    "ghcr.io/nextcloud-releases/aio-harp:latest",
    "ghcr.io/nextcloud-releases/aio-notify-push:latest",
    "nextcloud/all-in-one:latest",
)
# The shape the second instance had: a hand rolled server, straight from the hub.
THE_SECOND_INSTANCE_OF_07_09 = "nextcloud:34.0.3-apache"


def server_image_pattern(script: Path) -> str:
    """The SERVER_IMAGES default of a script, as the script really carries it."""
    text = script.read_text(encoding="utf-8")
    found = re.search(r'SERVER_IMAGES="\$\{SERVER_IMAGES:-(.*?)\}"', text)
    assert found is not None, f"{script.name} carries no SERVER_IMAGES default"
    return found.group(1)


@pytest.mark.parametrize("name", ["90-bestand.sh", "92-wechsel.sh"])
def test_the_server_count_finds_the_one_instance_of_this_box(name: str) -> None:
    """One server running has to count as one, on the registry path of this box.

    Both scripts carry the same default and both gate a step on it: 90-bestand.sh
    ends the inventory with 5, and 92-wechsel.sh refuses --rm-data with 5. A
    pattern that names one registry path counts the instance of another one as
    absent.
    """
    pattern = re.compile(server_image_pattern(RUN_DIR / name))
    hits = [image for image in RUNNING_IMAGES_OF_THE_BOX if pattern.search(image)]
    assert hits == ["ghcr.io/nextcloud-releases/aio-nextcloud:latest"], hits


@pytest.mark.parametrize("name", ["90-bestand.sh", "92-wechsel.sh"])
def test_the_server_count_sees_the_second_instance_that_did_the_damage(name: str) -> None:
    """Two servers have to count as two, or the guard passes the disaster.

    On 07.09. a second, hand rolled Nextcloud on the same docker daemon ran an
    unregister --rm-data and took the volume of the FIRST one with it, because the
    volume name of an ExApp follows from its app id alone. The count exists to
    stop exactly that, so the hand rolled shape stays in the pattern next to the
    All-in-One one, and two of them must not read as one.
    """
    pattern = re.compile(server_image_pattern(RUN_DIR / name))
    images = [*RUNNING_IMAGES_OF_THE_BOX, THE_SECOND_INSTANCE_OF_07_09]
    assert len([image for image in images if pattern.search(image)]) == 2


@pytest.mark.parametrize("name", ["90-bestand.sh", "92-wechsel.sh"])
def test_the_server_count_leaves_the_companion_containers_out(name: str) -> None:
    """The other AIO containers carry the word nextcloud and are not servers.

    Counting the mastercontainer, the AppAPI daemon or the notify-push helper as
    an instance would refuse every step of this run on a box that is set up
    correctly, which is the same outage as the bug above with the sign flipped.
    """
    pattern = re.compile(server_image_pattern(RUN_DIR / name))
    for image in (
        "nextcloud/all-in-one:latest",
        "ghcr.io/nextcloud/nextcloud-appapi-harp:release",
        "ghcr.io/nextcloud-releases/aio-notify-push:latest",
        "ghcr.io/nextcloud-releases/aio-harp:latest",
        "ghcr.io/nextcloud-releases/aio-domaincheck:latest",
    ):
        assert not pattern.search(image), image


# The reader of the watchman of the full run. These assertions are pitfall 8 of
# the research turned into a gate: 42c-lesen.py of the semantic run looked for
# indexed and embedded on the top level of the recording, where the indexed of
# the PHP half stands and stays 0 by design and where embedded does not stand at
# all. The watchman logged zeroes for a whole night while the container held
# 47.000 vectors, the search load sample of the trailing run never ran because
# its condition is embedded > 200, and the end of both tracks would have been
# noticed at the round cap some nine hours late. The lesson of the research is to
# drive the reader once against a known number before the run is triggered; here
# it is five known numbers, and none of them needs a box.


def read_a_recording(recording: str) -> list[str]:
    """The reader as a subprocess, fed one recording, split like the shell does.

    Not imported, for the two reasons the recipe above gives as well: the file
    name begins with a digit and is therefore no module name, and what the
    watchman consumes is three whitespace separated words on standard output.
    """
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [sys.executable, str(READER)],
        input=recording,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert answer.returncode == 0, answer.stderr
    return answer.stdout.split()


def read_without_standard_input() -> list[str]:
    """The same call with standard input closed, which must not wait for a line."""
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [sys.executable, str(READER)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert answer.returncode == 0, answer.stderr
    return answer.stdout.split()


def a_recording(**changes: object) -> str:
    """One recording of the admin page, in the shape the observer writes it.

    The two figures under "backend" are the ones the semantic run really stood
    at while its watchman logged zeroes, so a reader that reads the wrong level
    fails against the very numbers that failure cost.
    """
    recording: dict[str, object] = {
        "at": "2026-09-09T12:00:00Z",
        "runState": "running",
        "indexed": 0,
        "indexedPercent": 0,
        "embedded": 0,
        "embeddedPercent": 0,
        "scheduled": 1200,
        "running": 1,
        "backendReachable": True,
        "backend": {"indexed": 47000, "embedded": 12000},
    }
    recording.update(changes)
    return json.dumps(recording)


def test_the_reader_reads_indexed_and_embedded_under_backend() -> None:
    """The one reading the whole night of the semantic run turned on."""
    assert read_a_recording(a_recording()) == ["1201", "47000", "12000"]


def test_the_reader_never_reports_the_indexed_of_the_php_half() -> None:
    """The gate that goes red the moment somebody reads the top level again.

    The recording carries an indexed of eight on the top level and no backend at
    all. A reader that falls back to the top level answers "8" here, which is the
    number of the PHP half and not of the index; the honest answer is that both
    counters are unknown. The work stock stays a number, because scheduled and
    running really do live on the top level.
    """
    without_backend: dict[str, object] = json.loads(a_recording())
    del without_backend["backend"]
    without_backend["indexed"] = 8
    assert read_a_recording(json.dumps(without_backend)) == ["1201", "unklar", "unklar"]


def test_the_reader_answers_unklar_three_times_for_every_unusable_recording() -> None:
    """Not known and zero are two different answers, and the watchman acts on both.

    Three shapes of nothing: no line at all, because the observer has not written
    one yet; a line that is not JSON, because a recording can be cut in half by a
    kill; and a recording that carries the error key of a failed request, which
    is the shape the observer writes rather than leaving a gap.
    """
    assert read_a_recording("") == ["unklar", "unklar", "unklar"]
    assert read_a_recording('{"scheduled": 3, "runni') == ["unklar", "unklar", "unklar"]
    error = json.dumps({"at": "2026-09-09T12:00:00Z", "fehler": "HTTPError"})
    assert read_a_recording(error) == ["unklar", "unklar", "unklar"]


def test_the_reader_adds_scheduled_and_running_to_the_work_stock() -> None:
    """The stock is the sum of the two, and an empty stock is a zero and not a gap."""
    assert read_a_recording(a_recording(scheduled=3, running=1))[0] == "4"
    assert read_a_recording(a_recording(scheduled=0, running=0))[0] == "0"
    # Neither of the two is a number: an assumed zero here would let the watchman
    # declare the end of a run whose stock it never saw.
    assert read_a_recording(a_recording(scheduled=None, running=None))[0] == "unklar"


def test_the_reader_does_not_block_without_standard_input() -> None:
    """A reader that waits for a line it will never get hangs the whole watchman."""
    assert read_without_standard_input() == ["unklar", "unklar", "unklar"]


def observer_module() -> ModuleType:
    """The observer, loaded from its path under a name that is a valid module name.

    Loaded rather than run, because the projection of one answer into one
    recording is the part of it that can be held to a promise without an
    instance to log in to.
    """
    specification = importlib.util.spec_from_file_location("statusbeobachter", OBSERVER)
    assert specification is not None, OBSERVER
    assert specification.loader is not None, OBSERVER
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_the_recording_of_the_observer_carries_no_name_carrier() -> None:
    """T-10-21: the admin page knows example paths, and this file is checked in.

    The answer staged here carries three of them, in the three places the page
    really puts them: the error list of the container, the examples of the
    coverage block and an error list on the top level. None of the three may
    reach the recording, and the way that is kept is a projection onto a closed
    set of keys rather than a list of keys to drop.
    """
    module = observer_module()
    answer = {
        "at": "2026-09-09T11:59:00Z",
        "runState": "running",
        "indexed": 5,
        "indexedPercent": 1,
        "embedded": 3,
        "embeddedPercent": 1,
        "scheduled": 7,
        "running": 1,
        "backendReachable": True,
        "backend": {
            "indexed": 47000,
            "embedded": 12000,
            "errors": [{"path": "corpus/09-bescheid.pdf", "reason": "ocr_failed"}],
        },
        "coverage": {"examples": ["lasttest/files/loadtest/000001.pdf"]},
        "errorList": [{"path": "/lasttest/files/geheim.pdf", "fileid": 4711}],
    }

    recording = module.recording_of(answer)

    assert set(recording) == set(RECORDING_KEYS)
    assert set(recording["backend"]) == set(BACKEND_RECORDING_KEYS)
    text = json.dumps(recording)
    assert ".pdf" not in text
    assert "lasttest" not in text
    assert "/" not in text
    # The figures themselves have to survive the projection, or the observer
    # would be safe and useless at the same time.
    assert recording["backend"] == {"indexed": 47000, "embedded": 12000}
    assert recording["scheduled"] == 7
    assert recording["runState"] == "running"


def test_the_observer_writes_an_error_recording_instead_of_a_gap() -> None:
    """A failed request has to be visible in the row, because a gap is not.

    The watchman reads the last line and only the last line. An answer that is
    not the shape of the overview must therefore produce a recording with the
    error key, which is exactly what the reader above turns into three times
    unklar, and never a line that looks like a measurement.
    """
    module = observer_module()

    recording = module.recording_of("<html>a login form</html>")

    assert "fehler" in recording
    assert set(recording) <= set(RECORDING_KEYS) | {"fehler"}
    assert "indexed" not in recording


# The wide scope. Every .py and .sh under docs/measurements/**/skripte/, read out
# of the directories rather than out of a list of file names: a gate over a list
# covers the files somebody remembered to add to it, and the next measurement
# brings a directory rather than an entry.


def measurement_scripts() -> list[Path]:
    """Every script of every measurement this repository holds."""
    return sorted(path for path in MEASUREMENTS_DIR.glob("**/skripte/*") if path.suffix in SCRIPT_SUFFIXES)


def scripts_of_this_run() -> list[Path]:
    """Every script of the run of phase 10, which is the narrow scope."""
    return sorted(path for path in RUN_DIR.glob("*") if path.suffix in SCRIPT_SUFFIXES)


def carriage_returns_in(raw: bytes) -> int:
    """How many carriage returns the bytes carry, which has to be none.

    A CR behind the shebang makes the kernel look for an interpreter whose name
    ends in an invisible character, and the error message does not name it.
    """
    return raw.count(b"\r")


def dashes_in(text: str) -> list[str]:
    """Every forbidden dash the text carries, sorted, empty when it carries none."""
    return sorted(dash for dash in DASHES if dash in text)


def machine_shapes_in_code(text: str) -> list[str]:
    """Every machine shape the text carries in code, sorted.

    A shape inside a comment is prose and stays allowed, and so is a variable
    default with a comment over it. Those are the two places a path of the box may
    be named: one explains, the other can be changed without reading the body.
    Anywhere else it is a tool that measures one machine and cannot be pointed at
    another, which is the lesson 45-suchlast.py cost.
    """
    lines = text.splitlines()
    found: set[str] = set()
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#") or _is_a_commented_default(lines, index):
            continue
        found.update(shape for shape in MACHINE_SHAPES if shape in line)
    return sorted(found)


def _is_a_commented_default(lines: list[str], index: int) -> bool:
    """A variable default whose nearest non empty line above it is a comment."""
    if not DEFAULT_ASSIGNMENT.match(lines[index].strip()):
        return False
    for earlier in reversed(lines[:index]):
        stripped = earlier.strip()
        if stripped:
            return stripped.startswith("#")
    return False


def passwords_on_a_command_line(text: str) -> list[str]:
    """Every shape that hands a password to an argument, sorted.

    Found while writing this gate: the naive short form fired on mkdir -p "$OUT"
    of the very script it was written for. A false positive on the most common
    option in shell scripting is not a strict gate, it is one that gets deleted,
    so the short form was narrowed to the programs it means something for.
    """
    found = [shape for shape in PASSWORD_OPTIONS if shape in text]
    if PASSWORD_SHORT_FORM.search(text):
        found.append(SHORT_FORM_NAME)
    return sorted(found)


@pytest.fixture(params=measurement_scripts(), ids=lambda path: f"{path.parent.parent.name}/{path.name}")
def measurement_script(request: pytest.FixtureRequest) -> Path:
    return Path(request.param)


@pytest.fixture(params=scripts_of_this_run(), ids=lambda path: path.name)
def script_of_this_run(request: pytest.FixtureRequest) -> Path:
    return Path(request.param)


def test_the_wide_scope_covers_every_measurement_and_skips_what_is_not_a_script() -> None:
    """The gate reads directories, so this says which ones it found.

    Four runs have scripts today. The assertion is a floor and not an equality,
    because the next measurement is supposed to be picked up without an edit
    here, and the named file is the one that proved the suffix filter is needed.
    """
    found = measurement_scripts()
    directories = {path.parent.parent.name for path in found}
    assert directories >= {
        "2026-09-05-semantiklauf-m7g",
        "2026-09-grundlast-fein",
        "2026-09-nachmessung-m7g",
        "2026-09-vergleichsmessung-m7g",
    }
    assert not [path for path in found if path.name == ".claude-active"]
    assert TREE_HASH in found
    assert TREE_HASH_PROOF in found


def test_the_measurement_script_carries_no_carriage_return(measurement_script: Path) -> None:
    """Read as bytes, because a carriage return hides in a text read.

    True for the whole stock since plan 10-01: five files were renormalised and
    .gitattributes now carries the rule that keeps the next checkout from putting
    them back.
    """
    assert carriage_returns_in(measurement_script.read_bytes()) == 0, measurement_script.name


def test_the_measurement_script_carries_no_dash(measurement_script: Path) -> None:
    """The typography rule of this project, over the whole stock."""
    text = measurement_script.read_text(encoding="utf-8")
    assert dashes_in(text) == [], measurement_script.name


def test_the_script_of_this_run_starts_with_a_shebang(script_of_this_run: Path) -> None:
    """It is started on the box as ./<name>, so the first line decides."""
    raw = script_of_this_run.read_bytes()
    assert raw.startswith(SHEBANGS), (script_of_this_run.name, raw[:40])


def test_the_script_of_this_run_carries_no_path_of_one_machine(script_of_this_run: Path) -> None:
    """A tool with a machine path in it is a tool for one machine."""
    text = script_of_this_run.read_text(encoding="utf-8")
    assert machine_shapes_in_code(text) == [], script_of_this_run.name


def test_the_script_of_this_run_puts_no_password_on_a_command_line(script_of_this_run: Path) -> None:
    """An argument stands in the process list, and a log keeps it (T-10-03)."""
    text = script_of_this_run.read_text(encoding="utf-8")
    assert passwords_on_a_command_line(text) == [], script_of_this_run.name


def test_the_machine_shapes_come_from_the_gate_of_scripts_ops() -> None:
    """One definition for both gates, and this says what it currently reads.

    The list lives in test_ops_scripts.py and is read from there. This assertion
    pins what was read, so that widening or narrowing it over there is a decision
    somebody makes here as well instead of a side effect.
    """
    assert MACHINE_SHAPES == ("/home/", "sys.path.insert", "sys.path.append", "drillhelfer")


def test_the_carriage_return_gate_fires_on_a_staged_sample() -> None:
    """A gate whose only assertion is that today is fine stays green when it dies.

    The sample is the shape the five renormalised files had: a shebang that ends
    in a carriage return, which is the failure this whole rule is about.
    """
    staged = b"#!/usr/bin/env python3\r\nprint('hi')\r\n"
    assert carriage_returns_in(staged) == 2
    assert carriage_returns_in(b"#!/usr/bin/env python3\nprint('hi')\n") == 0


def test_the_dash_gate_fires_on_a_staged_sample() -> None:
    """Both dashes, assembled from code points so the sample is not the file."""
    staged = f"# a comment with an em dash {chr(0x2014)} in it\n"
    assert dashes_in(staged) == [chr(0x2014)]
    assert dashes_in(f"# and an en dash {chr(0x2013)} in this one\n") == [chr(0x2013)]
    assert dashes_in("# a comment with a plain hyphen - in it\n") == []


def test_the_machine_path_gate_fires_on_a_staged_sample() -> None:
    """The sample is 45-suchlast.py of the semantic run, in three lines.

    That file is why the narrow scope is narrow, and it is why the gate exists:
    it reached its helper through a directory of the load test box and became a
    tool that could not be pointed anywhere else.
    """
    staged = 'import sys\nsys.path.insert(0, "/home/ubuntu/work")\nfrom drillhelfer import suche\n'
    assert machine_shapes_in_code(staged) == ["/home/", "drillhelfer", "sys.path.insert"]

    # The two places the same shape stays allowed, and they have to stay allowed,
    # or the only way to name the box would be to hide it.
    assert machine_shapes_in_code("# the box keeps the repository under /home/ubuntu/work\n") == []
    assert machine_shapes_in_code('# the default of the box\nREPO="${REPO:-/home/ubuntu/work}"\n') == []
    # The same default without the comment over it is not exempt.
    assert machine_shapes_in_code('REPO="${REPO:-/home/ubuntu/work}"\n') == ["/home/"]


def test_the_password_gate_fires_on_a_staged_sample() -> None:
    """The three forbidden shapes, the way through, and the false positive.

    The last two lines are the ones that matter as much as the first three: the
    permitted --password-env must not be caught, and neither must mkdir -p, which
    is what the first draft of this gate did to the script it was written for.
    """
    assert passwords_on_a_command_line("occ user:resetpassword lasttest --password secret\n") == ["--password "]
    assert passwords_on_a_command_line("occ user:resetpassword --password=secret\n") == ["--password="]
    assert passwords_on_a_command_line('mysql -p "$PW" -e "select 1"\n') == [SHORT_FORM_NAME]

    assert passwords_on_a_command_line("search_load.py --password-env LASTTEST_PW\n") == []
    assert passwords_on_a_command_line('mkdir -p "$OUT"\n') == []
