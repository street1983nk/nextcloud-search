"""The gate of the parity gate: can ``scripts/ci/parity_diff.py`` go red, and how.

The parity job of ``integration.yml`` asks two providers the same question as the
same user and compares two sets of fileids. Everything that job asserts rests on
this one tool, so the tool needs its own suite: a comparison that cannot fail is
a comparison that proves nothing, and a comparison that fails without saying in
which direction sends somebody diffing two OCS answers by hand.

The two directions are not the same finding, which is why they are asserted
separately below. A fileid the native search shows and findling does not is a
functional defect: a user does not find a file he may see. A fileid findling
shows and the native search does not show the same user is the case that touches
the permission boundary, and it has to be named as such.

The tool is driven as a subprocess rather than imported. It lives outside the
``src`` layout of this package, next to ``slow_backend.py``, and it is invoked in
CI as a plain script with the system python of the runner. What the workflow
depends on is its exit code and the words in its output, so that is what these
cases assert; an import would test a function and leave the contract the job
actually uses untested.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
TOOL = REPOSITORY / "scripts" / "ci" / "parity_diff.py"

# The three exit codes the workflow can tell apart. Only "not zero" is load
# bearing for the job, which stops at the first failure either way, but the
# distinction is what turns a red run into a diagnosis without reading the log
# twice: a parity violation is a statement about the app, a vacuous comparison
# and a malformed answer are statements about the test setup.
EXIT_OK = 0
EXIT_PARITY = 1
EXIT_VACUOUS = 2
EXIT_MALFORMED = 3

# A path and a title in every entry, on purpose. The privacy contract of this
# project is that the container side of a search sees fileids and nothing else,
# and a CI log is the cheapest place to break it: an answer carries the full path
# of a private document, and a tool that echoes the answer puts it into a public
# workflow log. So the fixtures below carry both fields, and one case asserts
# that neither ever reaches the output.
PRIVATE_PATH = "/Personal/salary-2026-confidential.pdf"
PRIVATE_TITLE = "salary-2026-confidential.pdf"


def _answer(file_ids: list[str]) -> str:
    """An OCS answer of a search provider, in the shape both providers return."""
    return json.dumps(
        {
            "ocs": {
                "meta": {"status": "ok", "statuscode": 200},
                "data": {
                    "name": "Findling",
                    "isPaginated": False,
                    "entries": [
                        {
                            "thumbnailUrl": "",
                            "title": PRIVATE_TITLE,
                            "subline": PRIVATE_PATH,
                            "resourceUrl": f"http://localhost:8080/f/{file_id}",
                            "attributes": {"fileId": file_id, "path": PRIVATE_PATH},
                        }
                        for file_id in file_ids
                    ],
                },
            }
        }
    )


def _run(
    tmp_path: Path,
    scenario: str,
    native: str,
    findling: str,
    expect_min: int,
) -> subprocess.CompletedProcess[str]:
    """Write both answers next to each other and run the tool over them."""
    native_file = tmp_path / f"{scenario}-native.json"
    findling_file = tmp_path / f"{scenario}-findling.json"
    native_file.write_text(native, encoding="utf-8")
    findling_file.write_text(findling, encoding="utf-8")

    return subprocess.run(  # noqa: S603 - an argument list, never a shell
        [
            sys.executable,
            str(TOOL),
            "--scenario",
            scenario,
            "--native",
            str(native_file),
            "--findling",
            str(findling_file),
            "--expect-min",
            str(expect_min),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_two_equal_sets_pass_and_name_the_scenario_and_the_count(tmp_path: Path) -> None:
    result = _run(tmp_path, "own-files", _answer(["11", "12", "13"]), _answer(["13", "12", "11"]), 3)

    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    # The scenario name and the number of compared fileids, because a job with
    # six scenarios needs to be readable as a list of six answered questions.
    assert "own-files" in result.stdout
    assert "3" in result.stdout


def test_a_fileid_only_the_native_search_shows_is_a_missing_functional_defect(tmp_path: Path) -> None:
    result = _run(tmp_path, "received-share", _answer(["11", "12", "13"]), _answer(["11", "13"]), 3)

    output = result.stdout + result.stderr
    assert result.returncode != EXIT_OK, output
    assert result.returncode == EXIT_PARITY, output
    assert "missing" in output
    # The fileid itself, so the failure is actionable without a second run.
    assert "12" in output
    # And the direction spelled out, because "parity failed" alone leaves the
    # reader to work out which of the two findings this is.
    assert "functional" in output


def test_a_fileid_only_findling_shows_is_an_extra_security_defect(tmp_path: Path) -> None:
    result = _run(tmp_path, "revoked-share", _answer(["11"]), _answer(["11", "99"]), 1)

    output = result.stdout + result.stderr
    assert result.returncode == EXIT_PARITY, output
    assert "extra" in output
    assert "99" in output
    assert "security" in output


def test_both_directions_are_reported_separately(tmp_path: Path) -> None:
    result = _run(tmp_path, "group-change", _answer(["11", "12"]), _answer(["11", "99"]), 2)

    output = result.stdout + result.stderr
    assert result.returncode == EXIT_PARITY, output
    # Two findings, two lines, and the ids on the side they were found on. A
    # single merged line would be the moment the diagnosis is lost.
    missing_lines = [line for line in output.splitlines() if "missing" in line]
    extra_lines = [line for line in output.splitlines() if "extra" in line]
    assert len(missing_lines) == 1, output
    assert len(extra_lines) == 1, output
    assert "12" in missing_lines[0]
    assert "12" not in extra_lines[0]
    assert "99" in extra_lines[0]
    assert "99" not in missing_lines[0]


def test_two_empty_sets_are_not_a_success_unless_nothing_was_expected(tmp_path: Path) -> None:
    # The anti vacuity clause, and the whole reason --expect-min is mandatory. A
    # search that answers nothing at all makes every scenario of the job agree
    # with every other, and that run would be green while proving nothing.
    result = _run(tmp_path, "team-folder", _answer([]), _answer([]), 1)

    output = result.stdout + result.stderr
    assert result.returncode == EXIT_VACUOUS, output
    assert "team-folder" in output

    # Nought expected is the one case where two empty sets are the answer, and
    # scenario 3 of the job needs it: after the share was revoked the recipient
    # is supposed to find nothing on either side.
    allowed = _run(tmp_path, "revoked-share", _answer([]), _answer([]), 0)
    assert allowed.returncode == EXIT_OK, allowed.stdout + allowed.stderr


def test_agreeing_sets_below_the_expectation_are_a_vacuous_comparison(tmp_path: Path) -> None:
    # The same thought one step further. Three marker files per scenario means
    # three fileids, so two agreeing ids are not the scenario that was built:
    # something dropped out of the fixture, and the comparison is thinner than
    # the question it claims to answer.
    result = _run(tmp_path, "own-files", _answer(["11", "12"]), _answer(["11", "12"]), 3)

    output = result.stdout + result.stderr
    assert result.returncode == EXIT_VACUOUS, output
    # The scenario name as well as the number, so an interpreter that fell over
    # before reaching the comparison cannot pass this case by its exit code.
    assert "own-files" in output
    assert "3" in output


def test_a_broken_answer_is_its_own_error_and_never_an_empty_set(tmp_path: Path) -> None:
    # This is the failure mode that would otherwise turn the whole job green:
    # an answer that cannot be read becomes an empty set, an empty set agrees
    # with the other empty set, and a broken instance passes as a proven one.
    broken = _run(tmp_path, "own-files", "<html>502 Bad Gateway</html>", _answer(["11"]), 1)

    output = broken.stdout + broken.stderr
    assert broken.returncode == EXIT_MALFORMED, output
    assert "native" in output

    # The same for an answer that is valid JSON in the wrong shape, which is
    # what an OCS error body looks like: meta is there, data.entries is not.
    wrong_shape = _run(
        tmp_path,
        "own-files",
        json.dumps({"ocs": {"meta": {"statuscode": 998}}}),
        _answer(["11"]),
        1,
    )
    assert wrong_shape.returncode == EXIT_MALFORMED, wrong_shape.stdout + wrong_shape.stderr
    assert "entries" in wrong_shape.stdout + wrong_shape.stderr

    # And an entry without the one attribute the comparison is made of. Silently
    # skipping it would shrink a set by one and be read as a parity violation of
    # the other side.
    without_attribute = _run(
        tmp_path,
        "own-files",
        json.dumps({"ocs": {"data": {"entries": [{"title": PRIVATE_TITLE}]}}}),
        _answer(["11"]),
        1,
    )
    assert without_attribute.returncode == EXIT_MALFORMED, without_attribute.stdout + without_attribute.stderr
    assert "fileId" in without_attribute.stdout + without_attribute.stderr


def test_no_output_of_any_case_carries_a_path_or_a_title(tmp_path: Path) -> None:
    # Both fixtures carry a path and a title in every entry, so this is a
    # measurement and not a restatement of the intention.
    runs = [
        _run(tmp_path, "own-files", _answer(["11", "12"]), _answer(["11", "12"]), 2),
        _run(tmp_path, "own-files", _answer(["11", "12"]), _answer(["11"]), 2),
        _run(tmp_path, "own-files", _answer(["11"]), _answer(["11", "12"]), 1),
        _run(tmp_path, "own-files", _answer([]), _answer([]), 2),
        _run(tmp_path, "own-files", "not json at all", _answer(["11"]), 1),
    ]

    for result in runs:
        output = result.stdout + result.stderr
        # Every one of the five said something about the scenario, so a run that
        # never got as far as producing a message cannot pass this case by
        # having produced nothing to leak.
        assert "own-files" in output, output
        assert PRIVATE_PATH not in output, output
        assert PRIVATE_TITLE not in output, output
        assert "Personal" not in output, output


def test_the_tool_imports_nothing_but_the_standard_library() -> None:
    # It runs with the system python of the runner, next to curl and occ, and
    # never inside the locked environment of this package. A third party import
    # would be a dependency nobody installs there, so the tool would fail on the
    # runner and pass here, where the locked environment happens to have it.
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
            imported.add(node.module.split(".")[0])

    foreign = sorted(name for name in imported if name not in sys.stdlib_module_names)
    assert foreign == [], f"the tool would need these installed on the runner: {foreign}"
