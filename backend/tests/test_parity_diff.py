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


def _with_entry_point(answer: str, term: str = "parityown") -> str:
    """The same answer with the last entry the search dialog shows since 09-06.

    It is a door into the result page and not a hit, so it carries no fileId
    attribute, and its attribute list is the empty JSON list PHP serialises an
    empty array to. Written out here in the shape the real answer has, because
    the whole point of the case below is that a reader recognises this entry by
    its address and never by the attribute it does not carry.
    """
    document = json.loads(answer)
    document["ocs"]["data"]["entries"].append(
        {
            "thumbnailUrl": "",
            "title": "Show all results",
            "subline": "Opens the Findling results page",
            "resourceUrl": f"http://localhost:8080/index.php/apps/findling/?query={term}",
            "icon": "icon-search",
            "attributes": [],
        }
    )
    return json.dumps(document)


def _page(file_ids: list[str]) -> str:
    """The result page with one hit row per fileid, in the shape it renders in.

    The path and the title are in the row for the same reason they are in the
    JSON fixture: they are what a careless message would leak into a public log.
    """
    rows = "\n".join(
        f'\t\t\t\t<li class="findling-hit" id="findling-hit-{file_id}">\n'
        f'\t\t\t\t\t<a class="findling-hit__link" href="/index.php/apps/files/files/{file_id}">\n'
        f'\t\t\t\t\t\t<span class="findling-hit__title">{PRIVATE_TITLE}</span>\n'
        f'\t\t\t\t\t\t<span class="findling-hit__path">{PRIVATE_PATH}</span>\n'
        "\t\t\t\t\t</a>\n"
        "\t\t\t\t</li>"
        for file_id in file_ids
    )
    return (
        '<div class="findling-search">\n'
        '\t<h1 class="findling-search__title">Results for "parityown"</h1>\n'
        '\t<ol class="findling-hits" aria-label="Search results">\n'
        f"{rows}\n"
        "\t</ol>\n"
        "</div>\n"
    )


def _page_empty_state() -> str:
    """The page that was asked and answers nothing, which is a legal empty set."""
    return (
        '<div class="findling-search">\n'
        '\t<h1 class="findling-search__title">Results for "parityown"</h1>\n'
        '\t<div class="findling-empty">\n'
        '\t\t<h2 class="findling-empty__heading">No file contains "parityown"</h2>\n'
        '\t\t<p class="findling-empty__text">Try another word.</p>\n'
        "\t</div>\n"
        "</div>\n"
    )


def _page_error_block() -> str:
    """The page that could not ask, with the empty state below it, as it renders."""
    return (
        '<div class="findling-search">\n'
        '\t<div class="findling-banner findling-banner--error">\n'
        '\t\t<p class="findling-banner__heading">The search is not answering right now</p>\n'
        "\t</div>\n"
        '\t<div class="findling-empty">\n'
        '\t\t<h2 class="findling-empty__heading">No file contains "parityown"</h2>\n'
        "\t</div>\n"
        "</div>\n"
    )


def _run(
    tmp_path: Path,
    scenario: str,
    native: str,
    findling: str,
    expect_min: int,
    page: str | None = None,
    page_file: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Write the answers next to each other and run the tool over them.

    ``page`` is the HTML answer of the result page and is written to a file of
    its own; ``page_file`` names a path instead, which is how the case of a file
    that cannot be read is driven. Without either of them the tool is called the
    way it was called before phase 9, with two answers and no third comparison.
    """
    native_file = tmp_path / f"{scenario}-native.json"
    findling_file = tmp_path / f"{scenario}-findling.json"
    native_file.write_text(native, encoding="utf-8")
    findling_file.write_text(findling, encoding="utf-8")

    arguments = [
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
    ]

    if page is not None:
        page_path = tmp_path / f"{scenario}-page.html"
        page_path.write_text(page, encoding="utf-8")
        arguments += ["--findling-html", str(page_path)]
    elif page_file is not None:
        arguments += ["--findling-html", str(tmp_path / page_file)]

    return subprocess.run(  # noqa: S603 - an argument list, never a shell
        arguments,
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


def test_a_page_with_three_hit_rows_compares_as_three_fileids(tmp_path: Path) -> None:
    # The third comparison of success criterion 4 of phase 9: same user, same
    # question, and the same set of files over the dialog and over the page.
    result = _run(
        tmp_path,
        "own-files",
        _answer(["11", "12", "13"]),
        _answer(["13", "12", "11"]),
        3,
        page=_page(["12", "13", "11"]),
    )

    output = result.stdout + result.stderr
    assert result.returncode == EXIT_OK, output
    # Two verdicts and not one, and the second one names the page as its own
    # side: a red run has to say which of the two ways into the search differs.
    assert "identical on both sides" in output
    assert "the result page compared 3 fileids" in output


def test_a_page_with_the_empty_state_is_an_empty_set_and_not_an_unreadable_answer(tmp_path: Path) -> None:
    # The page was asked, it answered, and its answer is nothing. That is the one
    # case in which no hit row is a result rather than a failure to read, and the
    # empty state is what makes the difference.
    result = _run(tmp_path, "revoked-share", _answer([]), _answer([]), 0, page=_page_empty_state())

    output = result.stdout + result.stderr
    assert result.returncode == EXIT_OK, output
    assert "the result page compared 0 fileids" in output


def test_a_page_without_the_list_and_without_the_empty_state_is_unreadable(tmp_path: Path) -> None:
    # A login form, a proxy error, a redirect body: every one of them is an
    # answer a naive reader turns into "no hits", and a page that shows neither
    # a list nor an empty state is not the result page at all.
    result = _run(
        tmp_path,
        "own-files",
        _answer(["11"]),
        _answer(["11"]),
        1,
        page="<!DOCTYPE html><html><body><form action='/login'></form></body></html>",
    )

    output = result.stdout + result.stderr
    assert result.returncode == EXIT_MALFORMED, output
    assert result.returncode != EXIT_OK, output
    assert "page" in output


def test_a_page_with_the_error_block_is_unreadable_and_never_an_empty_set(tmp_path: Path) -> None:
    # The failure mode this whole reader exists for. The page renders its empty
    # state below the error block, so an answer that only counted rows would
    # read a silent backend as an empty result, and two empty sets agree.
    result = _run(tmp_path, "own-files", _answer([]), _answer([]), 0, page=_page_error_block())

    output = result.stdout + result.stderr
    assert result.returncode == EXIT_MALFORMED, output
    assert "error block" in output


def test_a_page_answer_that_cannot_be_read_is_unreadable(tmp_path: Path) -> None:
    # The file the job would have written if the curl before it had failed.
    result = _run(
        tmp_path,
        "own-files",
        _answer(["11"]),
        _answer(["11"]),
        1,
        page_file="a-page-that-was-never-written.html",
    )

    output = result.stdout + result.stderr
    assert result.returncode == EXIT_MALFORMED, output
    assert "could not be read" in output


def test_the_entry_point_of_the_dialog_is_skipped_by_its_address(tmp_path: Path) -> None:
    # T-09-22. Since 09-06 the findling group ends with a door into the result
    # page: no fileId attribute, and an address that points at the app path. It
    # must not be counted as a hit and it must not make the answer unreadable.
    result = _run(
        tmp_path,
        "own-files",
        _answer(["11", "12", "13"]),
        _with_entry_point(_answer(["11", "12", "13"])),
        3,
        page=_page(["11", "12", "13"]),
    )

    output = result.stdout + result.stderr
    assert result.returncode == EXIT_OK, output
    # Three and not four: the door is not a file.
    assert "compared 3 fileids" in output


def test_an_ordinary_entry_without_the_attribute_still_makes_the_answer_unreadable(tmp_path: Path) -> None:
    # The other half of the same threat, and the reason the entry above is
    # recognised by its address. A rule that skipped every entry without the
    # attribute would switch off the guard the reader exists for: an entry that
    # lost its fileid would shrink one set and be read as a parity violation of
    # the other.
    without_attribute = json.dumps(
        {
            "ocs": {
                "data": {
                    "entries": [
                        {
                            "title": PRIVATE_TITLE,
                            "resourceUrl": "http://localhost:8080/index.php/apps/files/files/11",
                        }
                    ]
                }
            }
        }
    )
    result = _run(tmp_path, "own-files", _answer(["11"]), without_attribute, 1)

    output = result.stdout + result.stderr
    assert result.returncode == EXIT_MALFORMED, output
    assert "fileId" in output


def test_a_page_that_differs_from_the_dialog_fails_in_both_directions(tmp_path: Path) -> None:
    # A hit the dialog shows and the page does not: the same search answers two
    # different sets, which is a functional defect of the page.
    missing = _run(
        tmp_path,
        "team-folder",
        _answer(["11", "12"]),
        _answer(["11", "12"]),
        2,
        page=_page(["11"]),
    )
    output = missing.stdout + missing.stderr
    assert missing.returncode == EXIT_PARITY, output
    assert "page-missing" in output
    assert "12" in output
    assert "functional" in output

    # And the other direction, which is the one that touches the permission
    # boundary: the page shows a file the dialog does not show this user.
    extra = _run(
        tmp_path,
        "team-folder",
        _answer(["11"]),
        _answer(["11"]),
        1,
        page=_page(["11", "99"]),
    )
    output = extra.stdout + extra.stderr
    assert extra.returncode == EXIT_PARITY, output
    assert "page-extra" in output
    assert "99" in output
    assert "security" in output


def test_the_expected_minimum_holds_for_the_page_as_well(tmp_path: Path) -> None:
    # Two agreeing sets below the expectation are a vacuous comparison, and the
    # third set is no exception: a page that answers one row where the scenario
    # was built for three has not compared what it claims to compare.
    result = _run(
        tmp_path,
        "own-files",
        _answer(["11", "12", "13"]),
        _answer(["11", "12", "13"]),
        3,
        page=_page(["11", "12", "13"]),
    )
    assert result.returncode == EXIT_OK, result.stdout + result.stderr

    thin = _run(tmp_path, "own-files", _answer(["11"]), _answer(["11"]), 1, page=_page(["11"]))
    assert thin.returncode == EXIT_OK, thin.stdout + thin.stderr

    # The dialog agrees with the native search over three, the page shows the
    # same three, and the expectation is four: the comparison is thinner than the
    # question it answers, on all three sets at once.
    vacuous = _run(
        tmp_path,
        "own-files",
        _answer(["11", "12", "13"]),
        _answer(["11", "12", "13"]),
        4,
        page=_page(["11", "12", "13"]),
    )
    output = vacuous.stdout + vacuous.stderr
    assert vacuous.returncode == EXIT_VACUOUS, output
    assert "own-files" in output


def test_no_output_of_the_page_comparison_carries_a_path_or_a_title(tmp_path: Path) -> None:
    # The page fixture carries the path and the title in every row, so this is a
    # measurement of the same privacy contract the JSON side is held to.
    runs = [
        _run(tmp_path, "own-files", _answer(["11", "12"]), _answer(["11", "12"]), 2, page=_page(["11", "12"])),
        _run(tmp_path, "own-files", _answer(["11", "12"]), _answer(["11", "12"]), 2, page=_page(["11"])),
        _run(tmp_path, "own-files", _answer(["11"]), _answer(["11"]), 1, page=_page(["11", "12"])),
        _run(tmp_path, "own-files", _answer([]), _answer([]), 0, page=_page_error_block()),
    ]

    for result in runs:
        output = result.stdout + result.stderr
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
