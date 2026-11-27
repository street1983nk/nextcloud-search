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
SCRIPT_PATH = "scripts/ci/apt_install.sh"
CALL = f"bash findling-src/{SCRIPT_PATH}"
HARNESS_CALL = f"bash findling-harness/{SCRIPT_PATH}"

# File of the scope, the call it has to use, and how many steps in it call the
# script with which first package. coverage-e2e.yml checks findling-src out at
# the tree a leg starts from (matrix.src, as old as v1.6.2), which has no such
# script; the head of the repository is the harness there (findling-harness).
# The first push of 46-04 called findling-src in that file and every leg ended
# with exit 127 (run 45966198418), the reason for checkout_findings below.
SCOPE = {
    ACTION: (CALL, {"wngerman": 1}),
    WORKFLOWS / "integration.yml": (CALL, {"tesseract-ocr": 3}),
    WORKFLOWS / "coverage-e2e.yml": (HARNESS_CALL, {"tesseract-ocr": 1}),
}
PYTHON_WORKFLOW = WORKFLOWS / "python.yml"
SHELLCHECK_STEP = "Shell check of the tunnel scripts"
NEW_SCRIPTS = (SCRIPT_PATH, "scripts/ci/apt_install_selftest.sh")
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


def call_findings(name: str, text: str, expected: dict[str, int], call: str = CALL) -> list[str]:
    """How often the script is called with which first package, against the scope."""
    findings: list[str] = []
    for package, count in expected.items():
        found = len(re.findall(re.escape(f"{call} {package}") + r"\b", text))
        if found != count:
            findings.append(f"{name}: {found} call(s) of the script for {package}, {count} expected")
    return findings


def checkout_findings(name: str, document: dict[str, object]) -> list[str]:
    """A call of the script through a checkout that is not the head of the repository.

    Every job that runs ``bash <dir>/scripts/ci/apt_install.sh`` has to check
    out ``<dir>`` without a ``ref`` or with ``github.sha``: a tree of an older
    release has no script, and the step ends with exit 127.
    """
    findings: list[str] = []
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return findings
    for job_name, job in jobs.items():
        steps = job.get("steps") if isinstance(job, dict) else None
        if not isinstance(steps, list):
            continue
        checkouts: dict[str, str] = {}
        for step in steps:
            uses = str(step.get("uses", ""))
            options = step.get("with") or {}
            if uses.startswith("actions/checkout@") and isinstance(options, dict) and "path" in options:
                checkouts[str(options["path"])] = str(options.get("ref", ""))
        for step in steps:
            for directory in re.findall(r"bash (\S+)/" + re.escape(SCRIPT_PATH), str(step.get("run", ""))):
                ref = checkouts.get(directory)
                if ref is None:
                    findings.append(f"{name}:{job_name}: {directory} is not checked out in this job")
                elif ref not in ("", "${{ github.sha }}"):
                    findings.append(f"{name}:{job_name}: {directory} is checked out at {ref}, not at the head")
    return findings


def shellcheck_findings(document: dict[str, object], base: Path) -> list[str]:
    """Every file the shellcheck step names exists from its working directory."""

    def working_directory(holder: object, fallback: str) -> str:
        defaults = holder.get("defaults") if isinstance(holder, dict) else None
        run = defaults.get("run") if isinstance(defaults, dict) else None
        return str(run.get("working-directory", fallback)) if isinstance(run, dict) else fallback

    top = working_directory(document, ".")
    findings: list[str] = []
    jobs = document.get("jobs")
    found = [
        (step, working_directory(job, top))
        for job in (jobs.values() if isinstance(jobs, dict) else [])
        for step in job.get("steps", [])
        if step.get("name") == SHELLCHECK_STEP
    ]
    if len(found) != 1:
        return [f"{len(found)} steps named {SHELLCHECK_STEP!r}, expected one"]
    step, directory = found[0]
    # The run block also prints "shellcheck --version"; the files stand on the
    # line that names no option.
    calls = [text for text in str(step.get("run", "")).splitlines() if text.strip().startswith("shellcheck ")]
    files = [word for text in calls for word in text.split()[1:] if not text.split()[1].startswith("-")]
    workdir = base / str(step.get("working-directory", directory))
    findings.extend(f"{file} does not exist from {workdir.name}/" for file in files if not (workdir / file).is_file())
    for script in NEW_SCRIPTS:
        if not any((workdir / file).resolve() == (base / script).resolve() for file in files):
            findings.append(f"{script} is not checked by shellcheck")
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
            runs_it = any(
                str(step.get("uses", "")) == ACTION_USE or SCRIPT_PATH in str(step.get("run", "")) for step in steps
            )
            if runs_it:
                limits[f"{path.name}:{job_name}"] = job.get("timeout-minutes", DEFAULT_JOB_MINUTES)
    return limits


def test_no_step_of_the_scope_calls_apt_get_itself() -> None:
    """E-46-04 a: the dictionary and the OCR engine are installed through the script only."""
    findings: list[str] = []
    for path, (call, expected) in SCOPE.items():
        text = path.read_text(encoding="utf-8")
        findings.extend(direct_apt_findings(path.name, text))
        findings.extend(call_findings(path.name, text, expected, call))
    assert findings == []


def test_every_call_of_the_script_goes_through_the_head_of_the_repository() -> None:
    """A call through a checkout of an older release finds no script (run 45966198418, exit 127)."""
    findings: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        findings.extend(checkout_findings(path.name, yaml.safe_load(path.read_text(encoding="utf-8"))))
    assert findings == []


def test_the_checkout_gate_sees_the_call_of_the_first_push() -> None:
    """Positive control: coverage-e2e.yml calling through findling-src (matrix.src) is a finding."""
    path = WORKFLOWS / "coverage-e2e.yml"
    first_push = path.read_text(encoding="utf-8").replace(HARNESS_CALL, CALL)
    findings = checkout_findings(path.name, yaml.safe_load(first_push))
    assert len(findings) == 1
    assert "matrix.src" in findings[0]


def test_shellcheck_reads_the_two_scripts_from_its_working_directory() -> None:
    """python.yml runs in backend/, so the scripts are ../scripts/ci/... from there (run 45966177681)."""
    document = yaml.safe_load(PYTHON_WORKFLOW.read_text(encoding="utf-8"))
    assert shellcheck_findings(document, REPO_ROOT) == []


def test_the_shellcheck_gate_sees_the_paths_of_the_first_push() -> None:
    """Positive control: the paths relative to the root, as the first push had them, are findings."""
    text = PYTHON_WORKFLOW.read_text(encoding="utf-8").replace("../" + NEW_SCRIPTS[0], NEW_SCRIPTS[0])
    text = text.replace("../" + NEW_SCRIPTS[1], NEW_SCRIPTS[1])
    findings = shellcheck_findings(yaml.safe_load(text), REPO_ROOT)
    assert len([finding for finding in findings if "does not exist" in finding]) == 2


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
