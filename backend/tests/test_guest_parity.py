"""The house rules of the guest user probe, as a gate instead of a review note.

``scripts/dev/guest_parity.sh`` is the second half of scenario 6. Decision D-22
splits that scenario in two: the CI job ``search-parity`` carries the groupless
minimal user, and a real guest user over the third party ``guests`` app carries
the rest, as a probe that is run by hand before the submission. The same
decision says the ``guests`` app must not become a dependency of the CI matrix,
which is why the probe is a script under ``scripts/dev`` and not a job.

A probe that nobody can run is a reminder, and a reminder is what this phase
forbids. So the probe is a tool, and the promises the tool carries are checked
here rather than remembered. Six of them are mechanical:

1. The verdict comes from ``scripts/ci/parity_diff.py`` and from nowhere else.
   The probe must not grow a set comparison of its own, because two ways of
   answering the same question sooner or later answer it differently, and the
   CI job and the probe would then disagree about what parity means.
2. The result cap of the instance is raised before the first question and put
   back at the end. ``SearchQuery::LIMIT_DEFAULT`` is five and the cap
   ``unified_search_max_results_per_request`` is twenty five, so without this
   step the probe compares two truncated lists and says nothing (pitfall 6).
3. Every search call carries an explicit ``limit``. That is the other half of
   the same pitfall: a raised cap without a limit still leaves the default of
   five in place.
4. A ``trap`` on EXIT removes the guest account and the share. An aborted probe
   otherwise leaves a guest account standing on the very instance the owner is
   about to walk through by hand.
5. D-22 itself, mechanically: no file under ``.github`` names the ``guests``
   app. A promise that the app stays out of CI is worth what a counter over the
   workflows is worth, and nothing more.
6. No em dash, no en dash and no carriage return, which are the typography rule
   of this project and the reason a POSIX shell refuses a script with an
   invisible character behind its shebang.

The counter of rule 5 filters full line comments before it counts, and the two
staged samples below are what prove it does both halves of that: it fires on a
line that enables the app, and it stays quiet on a comment that explains why
the app is absent. Without the second sample the explanatory paragraph of
``integration.yml``, which says in prose that the guest probe is deliberately
not a dependency of the matrix, would colour its own gate red.

The filter is deliberately narrow. A trailing comment behind a real command is
not stripped, so a line like ``run: ./occ status  # not the guests app`` still
counts as a mention. That direction is the cheap one: a false red costs one
rewritten comment, and a false green costs the decision.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE = REPO_ROOT / "scripts" / "dev" / "guest_parity.sh"
PARITY_DIFF = REPO_ROOT / "scripts" / "ci" / "parity_diff.py"
GITHUB_DIR = REPO_ROOT / ".github"

# Assembled from code points so that this file does not carry the characters it
# forbids and fail on itself.
DASHES = (chr(0x2014), chr(0x2013))

# The app id of decision D-22, as a whole word. A substring search would also
# find "guests" inside an unrelated English sentence, and a plain "guest" would
# find every mention of the probe itself.
_GUESTS_APP = re.compile(r"\bguests\b", re.IGNORECASE)

# The one route the probe asks on. It stands in the script exactly once, inside
# the one function that asks, which is what makes rule 3 a property of every
# call rather than of the calls somebody remembered to look at.
OCS_SEARCH_ROUTE = "/ocs/v2.php/search/providers/"

# The instance setting of pitfall 6.
RESULT_CAP = "unified_search_max_results_per_request"

# The shapes of a second set comparison. Each of them is a way of deciding
# whether two lists of fileids are the same, and the probe may use none of them:
# the decision belongs to parity_diff.py. "diff" is counted separately below,
# because the name of the tool contains it.
COMPARISON_SHAPES = ("sort ", "sort\n", "comm ", "uniq ", "cmp ")


def probe_text() -> str:
    """The script as text, with a message a reader can act on when it is gone."""
    assert PROBE.is_file(), f"{PROBE} does not exist, and the probe is the whole point of this gate"
    return PROBE.read_text(encoding="utf-8")


def shell_function(text: str, name: str) -> str:
    """The body of one shell function, from its opening line to its closing brace.

    Read out of the lines rather than with a parser, because the property being
    judged is which lines stand inside which function and the layout of this one
    script is what says so: a function opens with ``name() {`` at the start of a
    line and closes with a ``}`` alone on a line.
    """
    lines = text.splitlines()
    opening = f"{name}() {{"
    start = next((index for index, line in enumerate(lines) if line.startswith(opening)), None)
    assert start is not None, f"the probe has no function {name}()"
    end = next((index for index in range(start + 1, len(lines)) if lines[index] == "}"), None)
    assert end is not None, f"the function {name}() of the probe is never closed"
    return "\n".join(lines[start : end + 1])


def code_lines(text: str) -> list[str]:
    """Every line that is not a full line comment.

    The pattern the plan asks for, ``grep -v '^#'`` before ``grep -c``, with the
    leading whitespace of a YAML comment taken into account. A workflow explains
    itself in prose, and a gate that reads its own explanation as a violation is
    a gate that gets switched off.
    """
    return [line for line in text.splitlines() if not line.lstrip().startswith("#")]


def guests_mentions(text: str) -> list[str]:
    """Every non comment line of the text that names the guests app."""
    return [line.strip() for line in code_lines(text) if _GUESTS_APP.search(line)]


def github_files() -> list[Path]:
    """Every workflow and every composite action of this repository."""
    return sorted(path for path in GITHUB_DIR.rglob("*") if path.is_file() and path.suffix in {".yml", ".yaml"})


def test_the_probe_exists_and_starts_with_a_posix_shebang() -> None:
    """POSIX sh like every other script of this repository, and no bashism."""
    assert PROBE.read_bytes().startswith(b"#!/bin/sh\n")


def test_the_probe_stops_on_an_error_and_on_an_unset_variable() -> None:
    """set -eu, because a probe that runs on after a failed step writes fiction."""
    assert "\nset -eu\n" in probe_text()


def test_the_probe_carries_neither_a_dash_nor_a_carriage_return() -> None:
    raw = PROBE.read_bytes()
    assert b"\r" not in raw
    text = raw.decode("utf-8")
    for dash in DASHES:
        assert dash not in text, f"{dash!r} in {PROBE.name}"


def test_this_gate_carries_no_dash_either() -> None:
    """The gate is held to the typography rule it holds the script to.

    The carriage return half of that rule is deliberately not asserted here.
    ``.gitattributes`` pins ``*.sh`` to a line feed because a shell reads those
    files and an invisible character behind a shebang is a start that fails; the
    Python of ``backend/`` is imported and never started by its shebang, so it
    is left to the checkout, and on the development machine of this project that
    checkout writes carriage returns. A gate that went red on every fresh clone
    would be switched off within a week.
    """
    text = Path(__file__).read_text(encoding="utf-8")
    for dash in DASHES:
        assert dash not in text, f"{dash!r} in {Path(__file__).name}"


def test_the_probe_lets_parity_diff_decide() -> None:
    """Rule 1, first half: the tool of the CI job is called, by its path."""
    text = probe_text()
    assert PARITY_DIFF.is_file(), "the comparison tool of the CI job is gone, so the probe has no judge"
    assert "parity_diff.py" in text
    assert "--expect-min" in text
    assert "--scenario" in text


def test_the_probe_builds_no_second_set_comparison() -> None:
    """Rule 1, second half, and it is the half that would rot quietly.

    A probe that sorted two lists of fileids and compared them itself would be a
    second definition of parity, and the day the two definitions disagree is the
    day nobody can say which one is right.
    """
    text = probe_text()
    for shape in COMPARISON_SHAPES:
        assert shape not in text, f"{shape!r} in the probe looks like a set comparison of its own"
    # Every occurrence of the word has to belong to the name of the tool.
    assert text.count("diff") == text.count("parity_diff")


def test_the_probe_raises_the_result_cap_and_puts_it_back() -> None:
    """Rule 2. Both halves, and the second one inside the cleanup."""
    text = probe_text()
    assert f"config:app:set core {RESULT_CAP}" in text
    assert f"config:app:get core {RESULT_CAP}" in text
    assert RESULT_CAP in shell_function(text, "cleanup"), "the probe raises the cap and never puts it back"


def test_every_search_call_of_the_probe_carries_an_explicit_limit() -> None:
    """Rule 3, as a property of every call rather than of the ones on view.

    The route stands exactly once, inside the one function that asks, and that
    function sends a limit. A second copy of the call somewhere else in the
    script would break the first half of this assertion before it could break
    the second.
    """
    text = probe_text()
    assert text.count(OCS_SEARCH_ROUTE) == 1, "the probe asks on the search route in more than one place"
    ask = shell_function(text, "ask")
    assert OCS_SEARCH_ROUTE in ask
    assert "limit=" in ask


def test_the_probe_removes_the_guest_and_the_share_on_the_way_out() -> None:
    """Rule 4. A trap on EXIT, and a cleanup that really takes both with it."""
    text = probe_text()
    assert "\ntrap cleanup EXIT\n" in text
    cleanup = shell_function(text, "cleanup")
    assert "user:delete" in cleanup, "the cleanup of the probe leaves the guest account standing"
    assert "shares/" in cleanup, "the cleanup of the probe leaves the share standing"


def test_the_probe_is_run_by_hand_and_names_its_protocol() -> None:
    """The probe says what it writes, because a run without a file is a memory."""
    text = probe_text()
    assert "--log" in text
    assert "usage()" in text


def test_no_file_under_github_names_the_guests_app() -> None:
    """Rule 5, D-22 itself: the guests app stays out of the CI matrix.

    Every workflow and every composite action is read, comments filtered, and a
    single mention is a violation. The count of scanned files is asserted as
    well: a glob that found nothing would pass this test over nothing at all.
    """
    scanned = github_files()
    assert len(scanned) >= 8, "the scan found almost no workflow, so it proves nothing"
    offenders = {
        path.relative_to(REPO_ROOT).as_posix(): guests_mentions(path.read_text(encoding="utf-8"))
        for path in scanned
        if guests_mentions(path.read_text(encoding="utf-8"))
    }
    assert offenders == {}, f"the guests app has reached the CI matrix, against D-22: {offenders}"


def test_the_d22_counter_fires_on_a_workflow_that_enables_the_guests_app() -> None:
    """The staged sample of rule 5. A gate that cannot go red is not a gate."""
    sample = "jobs:\n  probe:\n    steps:\n      - run: ./occ app:enable guests\n"
    assert guests_mentions(sample) == ["- run: ./occ app:enable guests"]


def test_the_d22_counter_stays_quiet_on_a_comment_that_names_the_guests_app() -> None:
    """The other staged sample, and the reason the filter exists at all.

    ``integration.yml`` explains in prose why the guest half of scenario 6 is a
    manual probe. Without the filter that paragraph would colour its own gate
    red, and the first fix anybody reaches for is to delete the explanation.
    """
    sample = "      # the guests app is deliberately not a dependency of this matrix\n      - run: ./occ status\n"
    assert guests_mentions(sample) == []
