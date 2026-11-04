"""The structural gate over the supply chain gates of the PHP half (plan 42-03).

php/composer.lock pins PHPUnit and everything it pulls in, and all of that
runs inside the phpunit job of php.yml. Two commands guard it there, in the
job composer-hygiene: ``composer validate --strict`` turns warnings into errors
and proves that composer.lock still matches composer.json, and
``composer audit --locked`` reads the lock file alone against the advisory
database and fails on any advisory. A weekly schedule in php.yml runs the audit
against an unchanged lock file too, and dependabot keeps the composer
ecosystem under /php moving, with PHPUnit majors left to a human because they
have to move with the server branch.

None of that is worth anything once it is quietly removed or defused, and the
commit that does so would not start php.yml if it touched only the workflow
gate side. So this file, which runs in "Python gates" on every backend commit
and weekly, holds the shape:

1. A job of php.yml runs both commands, each in a step with
   ``working-directory: php``, carries ``timeout-minutes``, and neither the
   steps nor the job are defused by ``|| true`` or ``continue-on-error: true``.
2. php.yml has a schedule with at least one cron entry, and its concurrency
   group contains ``github.event_name``, so a scheduled run on main never
   cancels a push run.
3. dependabot.yml has an update entry for the composer ecosystem in "/php",
   weekly, with semver-major updates of phpunit/phpunit ignored.

**The limit.** This reads YAML. Whether composer really reports an advisory is
proven by running it, which plan 42-03 did locally against a throwaway lock
file with a known vulnerable package.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PHP_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "php.yml"
DEPENDABOT = REPO_ROOT / ".github" / "dependabot.yml"

VALIDATE = "composer validate --strict"
AUDIT = "composer audit --locked"
DEFUSERS = ("|| true", "||true")


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _defused(holder: dict[str, Any]) -> bool:
    return holder.get("continue-on-error") is True


def scan_workflow(text: str) -> list[str]:
    """Findings about the composer job, the schedule and the concurrency of php.yml."""
    loaded: Any = yaml.safe_load(text)
    workflow: dict[Any, Any] = loaded if isinstance(loaded, dict) else {}
    findings: list[str] = []

    # YAML 1.1 reads the bare key on as True.
    triggers = _mapping(workflow.get(True, workflow.get("on")))
    schedule = triggers.get("schedule")
    crons = [entry.get("cron") for entry in schedule if isinstance(entry, dict)] if isinstance(schedule, list) else []
    if not any(isinstance(cron, str) and cron.strip() for cron in crons):
        findings.append("php.yml has no schedule with a cron entry")

    group = _mapping(workflow.get("concurrency")).get("group")
    if not isinstance(group, str) or "github.event_name" not in group:
        findings.append("the concurrency group of php.yml does not contain github.event_name")

    jobs = _mapping(workflow.get("jobs"))
    homes: dict[str, set[str]] = {VALIDATE: set(), AUDIT: set()}
    for job_name, raw_job in jobs.items():
        job = _mapping(raw_job)
        steps = job.get("steps")
        for raw_step in steps if isinstance(steps, list) else []:
            step = _mapping(raw_step)
            run = step.get("run")
            if not isinstance(run, str) or step.get("working-directory") != "php":
                continue
            for command in (VALIDATE, AUDIT):
                if command not in run:
                    continue
                homes[command].add(str(job_name))
                if any(defuser in run for defuser in DEFUSERS) or _defused(step):
                    findings.append(f"the step running '{command}' in job {job_name} is defused")
        if any(str(job_name) in names for names in homes.values()):
            if _defused(job):
                findings.append(f"job {job_name} carries continue-on-error: true")
            timeout = job.get("timeout-minutes")
            if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
                findings.append(f"job {job_name} has no timeout-minutes")

    for command, names in homes.items():
        if not names:
            findings.append(f"no step of php.yml runs '{command}' with working-directory: php")
    if homes[VALIDATE] and homes[AUDIT] and not homes[VALIDATE] & homes[AUDIT]:
        findings.append("the two composer commands do not run in the same job")
    return findings


def scan_dependabot(text: str) -> list[str]:
    """Findings about the composer entry of dependabot.yml."""
    updates = _mapping(yaml.safe_load(text)).get("updates")
    entries = [_mapping(entry) for entry in updates] if isinstance(updates, list) else []
    composer = [entry for entry in entries if entry.get("package-ecosystem") == "composer"]
    if not composer:
        return ["dependabot.yml has no entry for the composer ecosystem"]
    entry = composer[0]

    findings: list[str] = []
    directories = entry.get("directories")
    named = [entry.get("directory")] + (directories if isinstance(directories, list) else [])
    if "/php" not in named:
        findings.append(f"the composer entry of dependabot.yml points at {named!r}, not at /php")
    if _mapping(entry.get("schedule")).get("interval") != "weekly":
        findings.append("the composer entry of dependabot.yml is not weekly")
    ignore = entry.get("ignore")
    majors_ignored = any(
        _mapping(rule).get("dependency-name") == "phpunit/phpunit"
        and "version-update:semver-major" in (_mapping(rule).get("update-types") or [])
        for rule in (ignore if isinstance(ignore, list) else [])
    )
    if not majors_ignored:
        findings.append("the composer entry of dependabot.yml does not leave phpunit/phpunit majors to a human")
    return findings


# The real tree.


def test_php_yml_validates_and_audits_the_composer_lock() -> None:
    assert scan_workflow(PHP_WORKFLOW.read_text(encoding="utf-8")) == []


def test_dependabot_keeps_composer_under_php_moving() -> None:
    assert scan_dependabot(DEPENDABOT.read_text(encoding="utf-8")) == []


# Probes: every finding is reported.

_CLEAN_WORKFLOW = """
on:
  push:
    paths:
      - 'php/**'
  schedule:
    - cron: '50 5 * * 1'
concurrency:
  group: php-${{ github.event_name }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  composer-hygiene:
    timeout-minutes: 10
    steps:
      - name: Validate
        working-directory: php
        run: composer validate --strict --no-check-publish
      - name: Audit
        working-directory: php
        run: composer audit --locked --no-interaction
"""


def test_a_clean_workflow_is_clean() -> None:
    assert scan_workflow(_CLEAN_WORKFLOW) == []


def test_a_workflow_without_schedule_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace("  schedule:\n    - cron: '50 5 * * 1'\n", "")
    assert scan_workflow(source) == ["php.yml has no schedule with a cron entry"]


def test_a_concurrency_group_without_the_event_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace("php-${{ github.event_name }}-${{ github.ref }}", "php-${{ github.ref }}")
    assert scan_workflow(source) == ["the concurrency group of php.yml does not contain github.event_name"]


def test_a_missing_audit_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace("composer audit --locked --no-interaction", "composer --version")
    findings = scan_workflow(source)
    assert len(findings) == 1
    assert AUDIT in findings[0]


def test_a_missing_validate_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace("composer validate --strict --no-check-publish", "composer validate")
    findings = scan_workflow(source)
    assert len(findings) == 1
    assert VALIDATE in findings[0]


def test_an_audit_outside_php_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace(
        "        working-directory: php\n        run: composer audit",
        "        working-directory: backend\n        run: composer audit",
    )
    findings = scan_workflow(source)
    assert len(findings) == 1
    assert AUDIT in findings[0]


def test_an_or_true_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace("--no-interaction", "--no-interaction || true")
    findings = scan_workflow(source)
    assert len(findings) == 1
    assert "defused" in findings[0]


def test_continue_on_error_on_a_step_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace("      - name: Audit\n", "      - name: Audit\n        continue-on-error: true\n")
    findings = scan_workflow(source)
    assert len(findings) == 1
    assert "defused" in findings[0]


def test_continue_on_error_on_the_job_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace(
        "    timeout-minutes: 10\n",
        "    timeout-minutes: 10\n    continue-on-error: true\n",
    )
    findings = scan_workflow(source)
    assert len(findings) == 1
    assert "continue-on-error" in findings[0]


def test_a_job_without_a_deadline_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace("    timeout-minutes: 10\n", "")
    assert scan_workflow(source) == ["job composer-hygiene has no timeout-minutes"]


_CLEAN_DEPENDABOT = """
version: 2
updates:
  - package-ecosystem: uv
    directory: "/backend"
    schedule:
      interval: weekly
  - package-ecosystem: composer
    directory: "/php"
    schedule:
      interval: weekly
    ignore:
      - dependency-name: "phpunit/phpunit"
        update-types:
          - version-update:semver-major
"""


def test_a_clean_dependabot_is_clean() -> None:
    assert scan_dependabot(_CLEAN_DEPENDABOT) == []


def test_dependabot_without_composer_is_reported() -> None:
    source = _CLEAN_DEPENDABOT.replace("package-ecosystem: composer", "package-ecosystem: npm")
    assert scan_dependabot(source) == ["dependabot.yml has no entry for the composer ecosystem"]


def test_dependabot_with_the_wrong_directory_is_reported() -> None:
    source = _CLEAN_DEPENDABOT.replace('directory: "/php"', 'directory: "/"')
    findings = scan_dependabot(source)
    assert len(findings) == 1
    assert "not at /php" in findings[0]


def test_dependabot_without_the_phpunit_major_rule_is_reported() -> None:
    source = _CLEAN_DEPENDABOT.replace("version-update:semver-major", "version-update:semver-minor")
    findings = scan_dependabot(source)
    assert len(findings) == 1
    assert "phpunit/phpunit" in findings[0]
