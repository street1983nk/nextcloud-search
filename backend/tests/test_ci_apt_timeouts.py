"""Every apt install of the test jobs has a time limit and retries (plan 46-04).

I-45-10-07 of 45-AUDIT.md (not the item of the same id in 45-VOLLTEST.md,
which is a rendering of Nextcloud and no finding): on 2026-11-26 the step
"Install the German dictionary the analyzer reads" hung for 24 minutes in a
download and took the whole job limit of team-folder-acl with it. The steps
in scope (owner decision E-46-04 a: the dictionary of setup-test-nc and the
OCR engine of integration.yml and coverage-e2e.yml) now go through
scripts/ci/apt_install.sh, which gives every attempt one time budget and tries
three times. This file holds three things against that:

- no ``apt-get update`` or ``apt-get install`` is left in a step of the scope,
- the worst case of the script stays under half the smallest job limit of the
  jobs that run one of those steps, because a limit that is longer than the
  job is no limit at all,
- the self test of the script holds (on Linux in CI; locally when bash with a
  GNU timeout is there).
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ci" / "apt_install.sh"
SELFTEST = REPO_ROOT / "scripts" / "ci" / "apt_install_selftest.sh"
ACTION = REPO_ROOT / ".github" / "actions" / "setup-test-nc" / "action.yml"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
CALL = "bash findling-src/scripts/ci/apt_install.sh"

# File of the scope, and how many steps in it call the script with which
# first package.
SCOPE = {
    ACTION: {"wngerman": 1},
    WORKFLOWS / "integration.yml": {"tesseract-ocr": 3},
    WORKFLOWS / "coverage-e2e.yml": {"tesseract-ocr": 1},
}
DIRECT_APT = re.compile(r"\bapt-get\s+(?:\S+\s+)*?(update|install)\b")
ACTION_USE = "./findling-src/.github/actions/setup-test-nc"
# GitHub ends a job without its own limit after 360 minutes.
DEFAULT_JOB_MINUTES = 360

# The dictionary step as 1.7.0 shipped it, the positive control of the first
# gate.
STEP_OF_1_7_0 = """\
    - name: Install the German dictionary the analyzer reads
      if: inputs.register-exapp == 'true'
      shell: bash
      run: |
        if [ ! -f /usr/share/dict/ngerman ]; then
          sudo apt-get update -qq
          sudo apt-get install -y -qq wngerman
        fi
        wc -l /usr/share/dict/ngerman
"""


def direct_apt_findings(name: str, text: str) -> list[str]:
    """Every line outside a comment that calls apt-get update or install itself."""
    findings: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("#"):
            continue
        if DIRECT_APT.search(line):
            findings.append(f"{name}:{number}: calls apt-get itself: {line.strip()}")
    return findings


def call_findings(name: str, text: str, expected: dict[str, int]) -> list[str]:
    """How often the script is called with which first package, against the scope."""
    findings: list[str] = []
    for package, count in expected.items():
        found = len(re.findall(re.escape(f"{CALL} {package}") + r"\b", text))
        if found != count:
            findings.append(f"{name}: {found} call(s) of the script for {package}, {count} expected")
    return findings


def script_defaults(text: str) -> tuple[int, int, int]:
    """Timeout, attempts and pause the script uses when nothing is set."""
    values: list[int] = []
    for setting in ("APT_INSTALL_TIMEOUT", "APT_INSTALL_ATTEMPTS", "APT_INSTALL_PAUSE"):
        match = re.search(r'="\$\{' + setting + r":-(\d+)\}\"", text)
        assert match, setting
        values.append(int(match.group(1)))
    return values[0], values[1], values[2]


def budget_findings(timeout_s: int, attempts: int, pause_s: int, job_minutes: int) -> list[str]:
    """The worst case of the script against half of the smallest job limit."""
    worst = timeout_s * attempts + pause_s * (attempts - 1)
    if worst >= job_minutes * 60 // 2:
        return [f"the script may take {worst}s, half of the smallest job limit is {job_minutes * 60 // 2}s"]
    return []


def job_minutes_of_the_scope() -> dict[str, int]:
    """The limit of every job that runs the action or calls the script itself."""
    limits: dict[str, int] = {}
    for path in sorted(WORKFLOWS.glob("*.yml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job_name, job in (document.get("jobs") or {}).items():
            steps = job.get("steps") or []
            runs_it = any(str(step.get("uses", "")) == ACTION_USE or CALL in str(step.get("run", "")) for step in steps)
            if runs_it:
                limits[f"{path.name}:{job_name}"] = job.get("timeout-minutes", DEFAULT_JOB_MINUTES)
    return limits


def test_no_step_of_the_scope_calls_apt_get_itself() -> None:
    """E-46-04 a: the dictionary and the OCR engine are installed through the script only."""
    findings: list[str] = []
    for path, expected in SCOPE.items():
        text = path.read_text(encoding="utf-8")
        findings.extend(direct_apt_findings(path.name, text))
        findings.extend(call_findings(path.name, text, expected))
    assert findings == []


def test_the_apt_gate_sees_the_step_of_1_7_0() -> None:
    """Positive control: the dictionary step of 1.7.0 is two findings, and a bare update is one."""
    assert len(direct_apt_findings("action.yml", STEP_OF_1_7_0)) == 2
    assert len(direct_apt_findings("x.yml", "        run: sudo apt-get -qq update\n")) == 1
    assert direct_apt_findings("x.yml", "    # sudo apt-get install -y wngerman\n") == []
    assert call_findings("action.yml", STEP_OF_1_7_0, {"wngerman": 1}) != []


def test_the_worst_case_of_the_script_stays_under_half_of_every_job_limit() -> None:
    """B-3 of the plan check: a limit longer than the job would not end anything."""
    limits = job_minutes_of_the_scope()
    assert limits, "no job of the scope was found"
    bad = [f"{job}: timeout-minutes {value!r}" for job, value in limits.items() if not isinstance(value, int)]
    assert bad == []
    timeout_s, attempts, pause_s = script_defaults(SCRIPT.read_text(encoding="utf-8"))
    assert budget_findings(timeout_s, attempts, pause_s, min(limits.values())) == []


def test_the_budget_gate_sees_a_limit_as_long_as_the_job() -> None:
    """Positive control: 300 s three times against a job of 25 minutes is a finding."""
    assert len(budget_findings(300, 3, 10, 25)) == 1
    assert budget_findings(120, 3, 10, 25) == []


def gnu_bash_with_timeout() -> str | None:
    """A bash whose timeout is the one of GNU coreutils, or None."""
    bash = shutil.which("bash")
    if bash is None:
        return None
    probe = subprocess.run(  # noqa: S603 - an argument list, a fixed command
        [bash, "-c", "timeout --version"], capture_output=True, text=True, check=False
    )
    if probe.returncode != 0 or "GNU coreutils" not in probe.stdout:
        return None
    return bash


def test_the_self_test_of_the_script_holds() -> None:
    """The time limit, the retries and the refusals, seen working without network."""
    bash = gnu_bash_with_timeout()
    if bash is None:
        pytest.skip("no bash with a GNU coreutils timeout on this machine; CI runs it on Linux")
    result = subprocess.run(  # noqa: S603 - an argument list, our own script
        [bash, SELFTEST.relative_to(REPO_ROOT).as_posix()],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all 6 cases hold" in result.stdout
