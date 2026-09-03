"""The gate over the workflow files: pinning, comment fidelity and deadlines.

Every ``uses:`` line in this repository runs third party code inside a job that
holds a Nextcloud instance, a registry credential or both. The defence is a
commit SHA rather than a tag, because a tag can be moved. That defence has a
soft spot nobody sees by reading: the SHA is forty characters of hexadecimal and
the only human readable thing next to it is a comment. A comment that says
``# v5.0.0`` behind a SHA that is really v7.0.1 is worse than no comment, and
that was the state of this repository until phase 5. Both checkouts carried the
comment ``v5.0.0``, one of them was v7.0.1 and the other v5.1.0, and neither was
the version they named.

The five rules this gate holds, each of them a shape a human eye slides over:

1. Comment fidelity. Within one action a version comment points at exactly one
   SHA, and a SHA carries exactly one comment. Two SHAs behind the same comment
   means one of the two comments is a lie.
2. A pinned SHA carries a version comment, and the comment names an exact
   version rather than a major. ``# v6`` behind a SHA is the shape the owner rule
   forbids since setup-uv v8: it reads like a floating major and hides which
   release is really being run.
3. No movable reference. A branch or a tag in a ``uses:`` line is arbitrary code
   execution the day somebody moves it. Actions of this repository, addressed by
   a relative path, are exempt: they move with the commit that is checked out.
4. Every job of every workflow file carries ``timeout-minutes``. Without it the
   ceiling is the GitHub default of 360 minutes, and a hung job holds a runner
   for six hours.
5. One pin per action across the whole repository. The same action at two
   different SHAs means two different versions run depending on which file was
   entered, and a version window nobody chose.

**The limit of this gate, and it is a real one.** It cannot know whether a SHA
really belongs to the version its comment names. Resolving that means asking
GitHub, and this gate runs offline next to the unit tests, on a machine that may
have no network and certainly has no token. What it does prove is internal
consistency: the same claim is made about the same SHA everywhere, every pin is
a pin, and no pin is undocumented. The external half is done by hand with
``gh api repos/<owner>/<repo>/tags`` when a pin is introduced or moved, and the
resolved values belong in the plan summary that moved them.

**Why text and not a YAML parser.** The comment behind a ``uses:`` value is the
subject of rule 1 and rule 2, and a YAML parser throws comments away before the
document reaches the caller. Reading the files as text is therefore not the
cheap way here, it is the only way that can see the thing being judged. The job
scanner relies on the indentation these six files use, two spaces for a job and
four for its keys, and says so rather than pretending to understand YAML: a file
whose ``jobs:`` block it cannot find is a finding and not a silent pass.

Self tests against staged samples belong to the shape of every textual gate in
this repository (Gate A, Gate B, Gate C). A gate whose only assertion is "the
current tree is clean" stays green on the day somebody deletes its body, so
every rule above has a sample that has to make it fire.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
ACTIONS = REPO_ROOT / ".github" / "actions"

# A uses line, with the optional trailing comment as its own group. The comment
# is what rules 1 and 2 judge, so it is captured rather than stripped.
_USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<ref>\S+)(?:[ \t]+#[ \t]*(?P<comment>.*?))?[ \t]*$")

# Forty characters of lowercase hexadecimal. Anything else in that position is a
# branch or a tag, which is to say a name somebody else can repoint.
_SHA = re.compile(r"^[0-9a-f]{40}$")

# An exact version names at least a major and a minor. The optional leading v
# covers actions/checkout style tags, the absence of it covers setup-php style
# tags, and the trailing part covers a patch level or a prerelease suffix.
_EXACT_VERSION = re.compile(r"^v?\d+\.\d+(?:\.\d+)?[0-9A-Za-z.+-]*$")

# The structural assumption of the job scanner, stated as two patterns instead of
# as a hope: a job is a key at two spaces, and its own keys sit at four.
_JOB = re.compile(r"^ {2}(?P<name>[A-Za-z0-9_.-]+):[ \t]*$")
_JOB_TIMEOUT = re.compile(r"^ {4}timeout-minutes:[ \t]*\d+[ \t]*$")
_TOP_LEVEL = re.compile(r"^[A-Za-z0-9_.-]+:")


class Use(NamedTuple):
    """One ``uses:`` line, reduced to the four things the rules care about."""

    file: str
    line: int
    action: str
    ref: str
    comment: str | None


def collect_uses(name: str, source: str) -> list[Use]:
    """Every ``uses:`` line of one file, split into action, reference and comment.

    A reference that starts with a dot addresses an action of this repository and
    carries no ``@`` at all; it is collected with an empty reference so that the
    rules below can recognise and skip it instead of tripping over it.
    """
    uses: list[Use] = []
    for number, line in enumerate(source.splitlines(), start=1):
        match = _USES.match(line)
        if match is None:
            continue
        value = match.group("ref")
        comment = match.group("comment")
        if value.startswith("."):
            uses.append(Use(name, number, value, "", comment))
            continue
        action, _, ref = value.partition("@")
        uses.append(Use(name, number, action, ref, comment))
    return uses


def scan_uses(uses: list[Use]) -> list[str]:
    """Rules 2 and 3: every pin is a SHA, and every SHA says which version it is."""
    violations: list[str] = []
    for use in uses:
        if use.action.startswith("."):
            # An action of this repository. It moves with the checked out commit,
            # so there is no third party and nothing to pin against.
            continue
        if not _SHA.match(use.ref):
            violations.append(
                f"{use.file}:{use.line}: {use.action} is pinned to the movable reference "
                f"'{use.ref}' instead of a commit SHA"
            )
            continue
        if use.comment is None:
            violations.append(
                f"{use.file}:{use.line}: {use.action} is pinned to a SHA that says nowhere which version it is"
            )
            continue
        if not _EXACT_VERSION.match(use.comment):
            violations.append(
                f"{use.file}:{use.line}: {use.action} is commented '{use.comment}', which is not an exact version"
            )
    return violations


def scan_comment_fidelity(uses: list[Use]) -> list[str]:
    """Rule 1: within one action a comment means one SHA and a SHA means one comment."""
    violations: list[str] = []
    by_comment: dict[tuple[str, str], dict[str, str]] = {}
    by_sha: dict[tuple[str, str], dict[str, str]] = {}
    for use in uses:
        if use.action.startswith(".") or use.comment is None or not _SHA.match(use.ref):
            continue
        where = f"{use.file}:{use.line}"
        by_comment.setdefault((use.action, use.comment), {}).setdefault(use.ref, where)
        by_sha.setdefault((use.action, use.ref), {}).setdefault(use.comment, where)

    for (action, comment), seen in sorted(by_comment.items()):
        if len(seen) > 1:
            named = ", ".join(f"{sha} at {where}" for sha, where in sorted(seen.items()))
            violations.append(f"{action}: the comment '{comment}' sits on more than one SHA, namely {named}")

    for (action, sha), seen in sorted(by_sha.items()):
        if len(seen) > 1:
            named = ", ".join(f"'{comment}' at {where}" for comment, where in sorted(seen.items()))
            violations.append(f"{action}@{sha[:12]}: the same SHA is commented in more than one way, namely {named}")

    return violations


def scan_single_pin(uses: list[Use]) -> list[str]:
    """Rule 5: one action, one SHA, across every file of the repository."""
    by_action: dict[str, dict[str, str]] = {}
    for use in uses:
        if use.action.startswith(".") or not _SHA.match(use.ref):
            continue
        by_action.setdefault(use.action, {}).setdefault(use.ref, f"{use.file}:{use.line}")

    violations: list[str] = []
    for action, seen in sorted(by_action.items()):
        if len(seen) > 1:
            named = ", ".join(f"{sha[:12]} at {where}" for sha, where in sorted(seen.items()))
            violations.append(f"{action}: pinned to more than one SHA in this repository, namely {named}")
    return violations


def scan_jobs(name: str, source: str) -> list[str]:
    """Rule 4: every job carries its own deadline.

    The block is found by indentation, and a file whose ``jobs:`` block cannot be
    found that way is reported rather than skipped. A scanner that returns an
    empty list for a file it did not understand is the failure mode this project
    calls a vacuous gate.
    """
    lines = source.splitlines()
    starts = [index for index, line in enumerate(lines) if line.rstrip() == "jobs:"]
    if not starts:
        return [f"{name}: no jobs block at the top level, so this gate cannot see whether its jobs have a deadline"]

    violations: list[str] = []
    found_a_job = False
    for start in starts:
        current: str | None = None
        has_timeout = False
        for line in [*lines[start + 1 :], "END:"]:
            job = _JOB.match(line)
            leaves_the_block = _TOP_LEVEL.match(line) is not None
            if job is None and not leaves_the_block:
                if current is not None and _JOB_TIMEOUT.match(line):
                    has_timeout = True
                continue
            if current is not None and not has_timeout:
                violations.append(
                    f"{name}: the job '{current}' has no timeout-minutes, so its ceiling is the default 360"
                )
            if leaves_the_block:
                break
            current = job.group("name") if job is not None else None
            has_timeout = False
            found_a_job = True

    if not found_a_job:
        violations.append(f"{name}: the jobs block contains no job this gate could recognise")
    return violations


def _sources() -> list[tuple[str, str]]:
    """Every workflow file and every composite action, as (name, text)."""
    paths = sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))
    paths += sorted(ACTIONS.glob("*/action.yml")) + sorted(ACTIONS.glob("*/action.yaml"))
    return [(str(path.relative_to(REPO_ROOT)).replace("\\", "/"), path.read_text(encoding="utf-8")) for path in paths]


def _all_uses() -> list[Use]:
    return [use for name, source in _sources() for use in collect_uses(name, source)]


# -- the real tree ---------------------------------------------------------


def test_both_directories_exist_and_carry_files() -> None:
    # The anti vacuity clause. Every scanner above returns an empty list for a
    # file that is not there, so a gate that lost its input would look perfect.
    # A directory that was renamed, a glob that stopped matching and a repository
    # checked out without .github all end in the same place: zero findings over
    # zero files.
    assert WORKFLOWS.is_dir()
    assert ACTIONS.is_dir()

    names = [name for name, _ in _sources()]

    assert len([name for name in names if name.startswith(".github/workflows/")]) >= 5
    assert len([name for name in names if name.startswith(".github/actions/")]) >= 1


def test_every_file_carries_at_least_one_uses_line() -> None:
    # The second half of the anti vacuity clause, one level down: a file that is
    # read but whose uses lines are not recognised produces no finding either.
    # Every workflow of this repository checks something out, so an empty result
    # means the pattern stopped matching and not that the file stopped using
    # third party code.
    without = [name for name, source in _sources() if not collect_uses(name, source)]

    assert without == []


def test_no_pin_is_movable_and_every_pin_says_which_version_it_is() -> None:
    violations = scan_uses(_all_uses())

    assert violations == []


def test_no_version_comment_sits_on_two_shas() -> None:
    violations = scan_comment_fidelity(_all_uses())

    assert violations == []


def test_no_action_is_pinned_twice() -> None:
    violations = scan_single_pin(_all_uses())

    assert violations == []


def test_every_job_of_every_workflow_has_a_deadline() -> None:
    violations = [
        message for name, source in _sources() if "/workflows/" in name for message in scan_jobs(name, source)
    ]

    assert violations == []


# -- self tests: every rule has to be able to go red -----------------------

_CLEAN = """name: Sample

on:
  push:

jobs:
  first:
    runs-on: ubuntu-24.04
    timeout-minutes: 12
    steps:
      - name: Check out the repository
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

      - name: Set up the instance
        uses: ./findling-src/.github/actions/setup-test-nc

  second:
    runs-on: ubuntu-24.04
    timeout-minutes: 3
    steps:
      - name: Check out the repository
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
"""


def test_the_clean_sample_is_clean() -> None:
    # The counter sample of everything below. Without it a gate that reported
    # every line as broken would pass all five failure tests too. It also pins
    # the exemption of rule 3: the local action carries no SHA and is not a
    # finding.
    uses = collect_uses("sample.yml", _CLEAN)

    assert len(uses) == 3
    assert scan_uses(uses) == []
    assert scan_comment_fidelity(uses) == []
    assert scan_single_pin(uses) == []
    assert scan_jobs("sample.yml", _CLEAN) == []


def test_a_comment_on_two_shas_is_reported() -> None:
    # Rule 1, and the exact shape this repository was in: two checkouts, two
    # SHAs, one comment. The second SHA is the real v5.1.0.
    source = _CLEAN.replace(
        "@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09",
        1,
    )

    violations = scan_comment_fidelity(collect_uses("sample.yml", source))

    assert len(violations) == 1
    assert "more than one SHA" in violations[0]


def test_a_sha_without_a_version_comment_is_reported() -> None:
    # Rule 2, first half.
    source = _CLEAN.replace(
        "@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1", "@3d3c42e5aac5ba805825da76410c181273ba90b1", 1
    )

    violations = scan_uses(collect_uses("sample.yml", source))

    assert len(violations) == 1
    assert "says nowhere which version it is" in violations[0]


def test_a_major_only_comment_is_reported() -> None:
    # Rule 2, second half, and the owner rule about setup-uv in one line: a
    # comment that names a major reads like a floating pin and hides the release.
    source = _CLEAN.replace("# v7.0.1", "# v7", 1)

    violations = scan_uses(collect_uses("sample.yml", source))

    assert len(violations) == 1
    assert "not an exact version" in violations[0]


def test_a_movable_reference_is_reported() -> None:
    # Rule 3.
    source = _CLEAN.replace("@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1", "@v7 # v7.0.1", 1)

    violations = scan_uses(collect_uses("sample.yml", source))

    assert len(violations) == 1
    assert "movable reference" in violations[0]


def test_a_job_without_a_deadline_is_reported() -> None:
    # Rule 4. The second job loses its deadline, so the finding has to name that
    # job and not the first one.
    source = _CLEAN.replace("    timeout-minutes: 3\n", "")

    violations = scan_jobs("sample.yml", source)

    assert len(violations) == 1
    assert "'second'" in violations[0]


def test_two_pins_of_the_same_action_are_reported() -> None:
    # Rule 5, and the exact shape of Sec-L8: setup-uv at v10.0.1 in one file and
    # at v6.8.0 in another. The comments differ, so rule 1 stays silent and only
    # this rule can see it.
    source = _CLEAN.replace(
        "      - name: Set up the instance\n        uses: ./findling-src/.github/actions/setup-test-nc\n",
        "      - name: Install uv\n"
        "        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1\n"
        "\n"
        "      - name: Install uv again\n"
        "        uses: astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0\n",
    )
    uses = collect_uses("sample.yml", source)

    assert scan_comment_fidelity(uses) == []

    violations = scan_single_pin(uses)

    assert len(violations) == 1
    assert "more than one SHA in this repository" in violations[0]


def test_a_file_without_a_jobs_block_is_reported() -> None:
    # The anti vacuity clause of rule 4, as a sample rather than as a promise:
    # a workflow this scanner cannot read is a finding, never a pass.
    violations = scan_jobs("sample.yml", "name: Sample\non:\n  push:\n")

    assert len(violations) == 1
    assert "no jobs block" in violations[0]
