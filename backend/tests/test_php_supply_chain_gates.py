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

import re
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


# The lint images of CI and of the local recipe (plan 45-09, hint of
# 44-SECURITY.md). workflow-lint.yml pulls zizmor and actionlint by digest, and
# scripts/dev/php_gates_docker.sh pulls the same two tools for the local run of
# the gates. Both carry the full reference written out, so a digest moved in one
# file and not in the other would leave the local run green with another tool
# than the one CI judges with. This gate reads the two references out of each
# file on its own way (the workflow as YAML, the recipe line by line) and holds
# them equal, character for character, digest included.

WORKFLOW_LINT = REPO_ROOT / ".github" / "workflows" / "workflow-lint.yml"
LOCAL_RECIPE = REPO_ROOT / "scripts" / "dev" / "php_gates_docker.sh"
LINT_IMAGE_VARIABLES = ("ZIZMOR_IMAGE", "ACTIONLINT_IMAGE")
DIGEST_SUFFIX = re.compile(r"@sha256:[0-9a-f]{64}\Z")


def _workflow_env_values(text: str, name: str) -> list[str]:
    """Every value of ``name`` in an env mapping of the workflow, its top, a job or a step."""
    loaded: Any = yaml.safe_load(text)
    workflow = _mapping(loaded)
    holders: list[dict[str, Any]] = [workflow]
    for job in _mapping(workflow.get("jobs")).values():
        holders.append(_mapping(job))
        steps = _mapping(job).get("steps")
        if isinstance(steps, list):
            holders.extend(_mapping(step) for step in steps)
    values: list[str] = []
    for holder in holders:
        env = _mapping(holder.get("env"))
        if name in env:
            values.append(str(env[name]))
    return values


def _recipe_values(text: str, name: str) -> list[str]:
    """Every top level assignment ``NAME="value"`` of the shell recipe."""
    pattern = re.compile(rf'^{re.escape(name)}="([^"]*)"\s*$')
    return [found.group(1) for line in text.splitlines() if (found := pattern.match(line))]


def scan_lint_image_pins(workflow_text: str, recipe_text: str) -> list[str]:
    """Findings where the lint images of workflow-lint.yml and of the local recipe part ways."""
    findings: list[str] = []
    for name in LINT_IMAGE_VARIABLES:
        in_workflow = _workflow_env_values(workflow_text, name)
        in_recipe = _recipe_values(recipe_text, name)
        if len(in_workflow) != 1:
            findings.append(f"{name} is set {len(in_workflow)} times in workflow-lint.yml, expected once")
        if len(in_recipe) != 1:
            findings.append(f"{name} is set {len(in_recipe)} times in the local recipe, expected once")
        if len(in_workflow) != 1 or len(in_recipe) != 1:
            continue
        if in_workflow[0] != in_recipe[0]:
            findings.append(f"{name} differs between workflow-lint.yml and the local recipe")
            continue
        if not DIGEST_SUFFIX.search(in_workflow[0]):
            findings.append(f"{name} is not pinned by a sha256 digest")
    return findings


def test_the_lint_images_carry_the_same_digest_in_ci_and_in_the_local_recipe() -> None:
    workflow = WORKFLOW_LINT.read_text(encoding="utf-8")
    recipe = LOCAL_RECIPE.read_text(encoding="utf-8")
    assert scan_lint_image_pins(workflow, recipe) == []


_ZIZMOR = "ghcr.io/zizmorcore/zizmor:1.32.0@sha256:3014cc8f68f663935f69b3c3e0e41f5ce102b268d97db13db0f62208747f860d"
_ACTIONLINT = "rhysd/actionlint:1.7.12@sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667"
_OTHER_DIGEST = "sha256:" + "0" * 64

_CLEAN_LINT_WORKFLOW = f"""
name: Workflow security lint
on:
  push:
jobs:
  zizmor:
    steps:
      - name: zizmor
        env:
          ZIZMOR_IMAGE: {_ZIZMOR}
        run: docker run "${{ZIZMOR_IMAGE}}"
  actionlint:
    steps:
      - name: actionlint
        env:
          ACTIONLINT_IMAGE: {_ACTIONLINT}
        run: docker run "${{ACTIONLINT_IMAGE}}"
"""

_CLEAN_RECIPE = f"""#!/usr/bin/env bash
COMPOSER_IMAGE="composer:2@{_OTHER_DIGEST}"
ZIZMOR_IMAGE="{_ZIZMOR}"
ACTIONLINT_IMAGE="{_ACTIONLINT}"
"""


def test_the_same_lint_images_in_both_files_are_clean() -> None:
    assert scan_lint_image_pins(_CLEAN_LINT_WORKFLOW, _CLEAN_RECIPE) == []


def test_another_zizmor_digest_in_the_recipe_is_reported() -> None:
    recipe = _CLEAN_RECIPE.replace(_ZIZMOR, _ZIZMOR.split("@")[0] + "@" + _OTHER_DIGEST)
    findings = scan_lint_image_pins(_CLEAN_LINT_WORKFLOW, recipe)
    assert len(findings) == 1
    assert "ZIZMOR_IMAGE" in findings[0]


def test_another_actionlint_digest_in_the_workflow_is_reported() -> None:
    workflow = _CLEAN_LINT_WORKFLOW.replace(_ACTIONLINT, _ACTIONLINT.split("@")[0] + "@" + _OTHER_DIGEST)
    findings = scan_lint_image_pins(workflow, _CLEAN_RECIPE)
    assert len(findings) == 1
    assert "ACTIONLINT_IMAGE" in findings[0]


def test_another_tag_with_the_same_digest_is_reported() -> None:
    recipe = _CLEAN_RECIPE.replace("zizmor:1.32.0@", "zizmor:1.33.0@")
    findings = scan_lint_image_pins(_CLEAN_LINT_WORKFLOW, recipe)
    assert len(findings) == 1
    assert "ZIZMOR_IMAGE" in findings[0]


def test_a_lint_image_without_a_digest_is_reported_even_when_both_files_agree() -> None:
    bare = _ACTIONLINT.split("@")[0]
    workflow = _CLEAN_LINT_WORKFLOW.replace(_ACTIONLINT, bare)
    recipe = _CLEAN_RECIPE.replace(_ACTIONLINT, bare)
    findings = scan_lint_image_pins(workflow, recipe)
    assert findings == ["ACTIONLINT_IMAGE is not pinned by a sha256 digest"]


def test_a_lint_image_missing_in_the_recipe_is_reported() -> None:
    recipe = _CLEAN_RECIPE.replace(f'ZIZMOR_IMAGE="{_ZIZMOR}"\n', "")
    findings = scan_lint_image_pins(_CLEAN_LINT_WORKFLOW, recipe)
    assert findings == ["ZIZMOR_IMAGE is set 0 times in the local recipe, expected once"]


def test_a_lint_image_missing_in_the_workflow_is_reported() -> None:
    workflow = _CLEAN_LINT_WORKFLOW.replace(f"          ACTIONLINT_IMAGE: {_ACTIONLINT}\n", "")
    findings = scan_lint_image_pins(workflow, _CLEAN_RECIPE)
    assert findings == ["ACTIONLINT_IMAGE is set 0 times in workflow-lint.yml, expected once"]


def test_a_lint_image_set_twice_in_the_workflow_is_reported() -> None:
    workflow = _CLEAN_LINT_WORKFLOW.replace(
        f"          ZIZMOR_IMAGE: {_ZIZMOR}\n",
        f"          ZIZMOR_IMAGE: {_ZIZMOR}\n          ACTIONLINT_IMAGE: {_ACTIONLINT}\n",
    )
    findings = scan_lint_image_pins(workflow, _CLEAN_RECIPE)
    assert findings == ["ACTIONLINT_IMAGE is set 2 times in workflow-lint.yml, expected once"]
