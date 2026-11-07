"""The gate over the contexts a workflow reads where GitHub does not offer them.

GitHub Actions evaluates the ``env`` block of a workflow and the ``env`` block
of a job before any runner is assigned, so only a fixed set of contexts exists
there: ``github``, ``secrets``, ``inputs`` and ``vars`` at workflow level, and
additionally ``needs``, ``strategy`` and ``matrix`` at job level. ``runner``,
``env``, ``steps`` and ``job`` exist only inside a step. A workflow that reads
``${{ runner.temp }}`` in a job level ``env`` is not rejected by any linter of
this repository, it is rejected by GitHub at the moment it is started, and a
dispatch only workflow then fails on the day it is needed (a sister repository
lost a run to exactly this on 07.11.2026). The job level keys ``if``,
``runs-on``, ``timeout-minutes``, ``continue-on-error``, ``concurrency``,
``environment`` and ``name`` are evaluated at the same moment and get the same
check.

The step level keys are deliberately left alone: there every context is
available, and ``${{ runner.temp }}`` in the ``env`` of a step is the shape
this repository uses throughout.

Like every textual gate of this repository the rule carries self tests on
staged samples, so a gate whose body was emptied does not stay green.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

# The contexts that exist only once a runner runs a step.
_STEP_ONLY = ("runner", "env", "steps", "job")

# One expression, the text between the two braces.
_EXPRESSION = re.compile(r"\$\{\{(?P<body>.*?)\}\}", re.DOTALL)

# A context reference inside an expression body: the name, a dot or a bracket.
_CONTEXT = re.compile(r"(?<![A-Za-z0-9_.-])(?P<name>" + "|".join(_STEP_ONLY) + r")\s*(?:\.|\[)")

# Job keys GitHub evaluates before the job has a runner.
_JOB_SCALAR_KEYS = ("if", "runs-on", "timeout-minutes", "continue-on-error", "concurrency", "environment", "name")


def _strings(value: Any) -> list[str]:
    """Every string inside a loaded YAML value, keys and values alike."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_strings(key))
            found.extend(_strings(item))
        return found
    if isinstance(value, list):
        found = []
        for item in value:
            found.extend(_strings(item))
        return found
    return []


def _step_only_contexts(text: str, *, bare: bool = False) -> set[str]:
    """The step only contexts one string reads. ``bare`` is the ``if`` form without braces."""
    bodies = [match.group("body") for match in _EXPRESSION.finditer(text)]
    if bare and not bodies:
        bodies = [text]
    return {match.group("name") for body in bodies for match in _CONTEXT.finditer(body)}


def findings_of(document: Any) -> list[str]:
    """Every place of one loaded workflow that reads a step only context too early."""
    findings: list[str] = []
    if not isinstance(document, dict):
        return ["the file is not a mapping"]
    for text in _strings(document.get("env", {})):
        for name in sorted(_step_only_contexts(text)):
            findings.append(f"workflow env reads {name}")
    jobs = document.get("jobs", {})
    if not isinstance(jobs, dict):
        return [*findings, "jobs is not a mapping"]
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        for text in _strings(job.get("env", {})):
            for name in sorted(_step_only_contexts(text)):
                findings.append(f"job {job_name}: env reads {name}")
        for key in _JOB_SCALAR_KEYS:
            if key not in job:
                continue
            for text in _strings(job[key]):
                for name in sorted(_step_only_contexts(text, bare=key == "if")):
                    findings.append(f"job {job_name}: {key} reads {name}")
    return findings


def _workflow_files() -> list[Path]:
    return sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])


def test_the_scan_sees_the_workflows_it_judges() -> None:
    names = {path.name for path in _workflow_files()}
    # A scan that globbed the wrong directory would pass on nothing.
    assert {"integration.yml", "smb-acl-measure.yml", "coverage-e2e.yml"} <= names


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda path: path.name)
def test_no_workflow_reads_a_step_only_context_before_its_steps(path: Path) -> None:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert findings_of(document) == [], path.name


# -- self tests on staged samples -------------------------------------------


def _load(text: str) -> Any:
    return yaml.safe_load(text)


def test_the_gate_fires_on_runner_in_a_job_env() -> None:
    sample = _load(
        "jobs:\n  one:\n    runs-on: ubuntu-24.04\n    env:\n      RESULT: ${{ runner.temp }}/out.md\n    steps: []\n"
    )
    assert findings_of(sample) == ["job one: env reads runner"]


def test_the_gate_fires_on_runner_in_a_workflow_env() -> None:
    sample = _load("env:\n  WORK: ${{ runner.temp }}\njobs: {}\n")
    assert findings_of(sample) == ["workflow env reads runner"]


def test_the_gate_fires_on_env_and_steps_in_a_job_env_and_on_a_bare_if() -> None:
    sample = _load(
        "jobs:\n"
        "  one:\n"
        "    if: steps.a.outcome == 'success'\n"
        "    env:\n"
        "      A: ${{ env.B }}\n"
        "      C: ${{ steps['x'].outputs.y }}\n"
        "    steps: []\n"
    )
    assert findings_of(sample) == ["job one: env reads env", "job one: env reads steps", "job one: if reads steps"]


def test_the_gate_leaves_the_allowed_contexts_and_the_step_level_alone() -> None:
    sample = _load(
        "env:\n"
        "  A: ${{ github.sha }}\n"
        "jobs:\n"
        "  one:\n"
        "    runs-on: ubuntu-24.04\n"
        "    if: github.event_name == 'workflow_dispatch'\n"
        "    env:\n"
        "      B: ${{ matrix.variant }}-${{ inputs.x }}-${{ vars.y }}\n"
        "      C: runner.temp written as text is no expression\n"
        "      D: ${{ github.event.inputs.runner }}\n"
        "    steps:\n"
        "      - run: echo\n"
        "        env:\n"
        "          E: ${{ runner.temp }}\n"
    )
    assert findings_of(sample) == []
