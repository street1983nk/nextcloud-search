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
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MEASUREMENTS_DIR = REPO_ROOT / "docs" / "measurements"
RUN_DIR = MEASUREMENTS_DIR / "2026-09-vergleichsmessung-m7g" / "skripte"
TREE_HASH = RUN_DIR / "40b-baumhash.py"
TREE_HASH_PROOF = RUN_DIR / "40b-baumhash.sh"

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


def test_the_recipe_and_the_proof_carry_neither_a_dash_nor_a_carriage_return() -> None:
    """Both files, as bytes, because a CR behind a shebang hides in a text read."""
    for path in (TREE_HASH, TREE_HASH_PROOF):
        raw = path.read_bytes()
        assert b"\r" not in raw, path.name
        text = raw.decode("utf-8")
        for dash in DASHES:
            assert dash not in text, f"{dash!r} in {path.name}"
