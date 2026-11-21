"""The structural gate over the static analysis gates of phase 44.

Phase 44 added four gates to CI: the Psalm taint analysis of the companion app
(job psalm-taint of php.yml, once per nextcloud/ocp major the app supports), the
php-cs-fixer dry run with nextcloud/coding-standard (job php-cs of php.yml), and
zizmor and actionlint over every workflow (jobs zizmor and actionlint of
workflow-lint.yml). Each of them is only worth something while it is there and
while it can still turn red. A gate that is quietly removed, or kept but
defused, is worse than no gate, because the green check mark still reads as a
verdict. This file runs in "Python gates" on every commit that touches the
backend, the scripts, the PHP half or a workflow (owner decision E-06), and
holds the shape:

1. php.yml has a job psalm-taint whose matrix ``ocp`` lists exactly three tags
   ``v<major>.<minor>.<patch>``, and the set of their majors equals the range
   min-version to max-version of the nextcloud dependency in
   php/appinfo/info.xml, read at run time. The job runs
   ``bash scripts/ci/psalm_taint_gate.sh``.
2. php.yml has a job php-cs that runs ``bash scripts/ci/php_cs_gate.sh``.
3. workflow-lint.yml has a job zizmor and a job actionlint, each running
   scripts/ci/workflow_lint_gate.sh in its own mode, and both its push and its
   pull_request trigger name ``.github/**`` in their paths. The file never
   names the shellcheck options variable and never passes a severity to
   shellcheck (owner decision E-03).
4. Every job of rules 1 to 3 carries ``timeout-minutes``, and neither the job
   nor the step that runs the gate is defused by ``continue-on-error: true`` or
   ``|| true``.
5. The gate scripts keep their teeth. psalm_taint_gate.sh counts the SARIF
   results with ``[.runs[].results[]]`` and requires TaintedHtml from its
   probe; php_cs_gate.sh runs ``--dry-run`` and its probe with
   ``--path-mode=intersection``; workflow_lint_gate.sh runs zizmor offline with
   ``--min-severity medium`` and the persona auditor (owner decision E-04) for
   the real pass and for the probe, removes an inherited shellcheck options
   variable with ``unset SHELLCHECK_OPTS`` and requires SC2086 from the probe
   (the proof that shellcheck runs with info and style, E-03). None of them
   carries ``--no-exit-codes``, a SARIF output format, an ``-ignore`` pattern,
   ``|| true``, the persona regular or pedantic, a severity for shellcheck or
   an assignment to the shellcheck options variable.
6. php/psalm.xml loads the AppFrameworkTainter plugin, has no errorBaseline and
   no issueHandlers entry for a Tainted issue, and there is no
   php/psalm-baseline.xml. The files Psalm analyses carry no
   ``@psalm-suppress`` and no ``@psalm-taint-escape``.
7. There is no zizmor configuration file, and every ``# shellcheck disable`` or
   ``# zizmor: ignore`` line under .github names an exception the owner
   granted: an E-ID listed in OWNER_EXCEPTIONS, for the file and the rule it
   was granted for. Today that is exactly one line, E-13 in php.yml.

**The limit.** This gate reads text and structure, not the result of a run.
Whether Psalm, php-cs-fixer, zizmor and actionlint really turn red is proven by
the positive controls inside the gate scripts on every CI run, and once by the
red proof on the throwaway branch of plan 44-10. What this file proves is that
the jobs, the controls and the thresholds are still in place.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
GITHUB_DIR = REPO_ROOT / ".github"
PHP_WORKFLOW = GITHUB_DIR / "workflows" / "php.yml"
LINT_WORKFLOW = GITHUB_DIR / "workflows" / "workflow-lint.yml"
PSALM_GATE = REPO_ROOT / "scripts" / "ci" / "psalm_taint_gate.sh"
CS_GATE = REPO_ROOT / "scripts" / "ci" / "php_cs_gate.sh"
LINT_GATE = REPO_ROOT / "scripts" / "ci" / "workflow_lint_gate.sh"
PSALM_CONFIG = REPO_ROOT / "php" / "psalm.xml"
PSALM_BASELINE = REPO_ROOT / "php" / "psalm-baseline.xml"
INFO_XML = REPO_ROOT / "php" / "appinfo" / "info.xml"
ZIZMOR_CONFIGS = (
    REPO_ROOT / "zizmor.yml",
    REPO_ROOT / "zizmor.yaml",
    GITHUB_DIR / "zizmor.yml",
    GITHUB_DIR / "zizmor.yaml",
)
# The files Psalm analyses, as listed in projectFiles of php/psalm.xml.
PSALM_SOURCE_DIRS = (REPO_ROOT / "php" / "lib", REPO_ROOT / "php" / "templates")
PSALM_SOURCE_FILES = (REPO_ROOT / "php" / "appinfo" / "routes.php",)

DEFUSERS = ("|| true", "||true")
# Forms that keep a tool running but stop its verdict from reaching the exit
# code, or narrow what it looks at.
LINT_DEFUSERS = ("--no-exit-codes", "--format sarif", "--format=sarif", "-ignore")
WEAKER_PERSONAS = ("regular", "pedantic")

PSALM_SCRIPT = "bash scripts/ci/psalm_taint_gate.sh"
CS_SCRIPT = "bash scripts/ci/php_cs_gate.sh"
LINT_SCRIPT = "scripts/ci/workflow_lint_gate.sh"
PROBE_NAME = "workflow-lint-probe.yml"

PSALM_NAMESPACE = "{https://getpsalm.org/schema/config}"

# Inline exceptions the owner granted, by E-ID: the workflow file and the rule
# each one covers. Anything else under .github is a finding.
OWNER_EXCEPTIONS: dict[str, tuple[str, str]] = {
    # E-13 (route-a): the route attribute gate of php.yml keeps its PHP code in
    # single quotes, where the dollar sign is wanted.
    "E-13": ("php.yml", "SC2016"),
}

_TAG = re.compile(r"^v(\d+)\.\d+\.\d+$")
_EXCEPTION_LINE = re.compile(r"#\s*(shellcheck\s+disable|zizmor:\s*ignore)")
_E_ID = re.compile(r"\bE-\d+\b")
_SHELLCHECK_OPTS_ASSIGNMENT = re.compile(r"SHELLCHECK_OPTS\s*[:=]")
_PERSONA = re.compile(r"--persona[ =]+(\S+)")


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _defused(holder: dict[str, Any]) -> bool:
    return holder.get("continue-on-error") is True


def _load_workflow(text: str) -> dict[Any, Any]:
    loaded: Any = yaml.safe_load(text)
    return loaded if isinstance(loaded, dict) else {}


def expected_ocp_majors(info_xml: str) -> set[int]:
    """The Nextcloud majors the app supports, from min-version to max-version."""
    root = ET.fromstring(info_xml.encode("utf-8"))  # noqa: S314 - a file of this repository, not foreign input
    nextcloud = root.find("dependencies/nextcloud")
    if nextcloud is None:
        return set()
    low = nextcloud.get("min-version", "")
    high = nextcloud.get("max-version", "")
    if not (low.isdigit() and high.isdigit()):
        return set()
    return set(range(int(low), int(high) + 1))


def _check_gate_job(jobs: dict[str, Any], job_name: str, command: str, workflow: str) -> list[str]:
    """The shared rules for a job that runs one gate script."""
    if job_name not in jobs:
        return [f"{workflow} has no job {job_name}"]
    job = _mapping(jobs[job_name])
    findings: list[str] = []
    if _defused(job):
        findings.append(f"job {job_name} carries continue-on-error: true")
    timeout = job.get("timeout-minutes")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
        findings.append(f"job {job_name} has no timeout-minutes")
    steps = job.get("steps")
    homes = [
        _mapping(step)
        for step in (steps if isinstance(steps, list) else [])
        if isinstance(_mapping(step).get("run"), str) and command in _mapping(step)["run"]
    ]
    if not homes:
        findings.append(f"job {job_name} does not run '{command}'")
    for step in homes:
        run = str(step["run"])
        if any(defuser in run for defuser in DEFUSERS) or _defused(step):
            findings.append(f"the step running '{command}' in job {job_name} is defused")
    return findings


def scan_php_workflow(text: str, info_xml: str) -> list[str]:
    """Findings about the jobs psalm-taint and php-cs of php.yml."""
    jobs = _mapping(_load_workflow(text).get("jobs"))
    findings = _check_gate_job(jobs, "psalm-taint", PSALM_SCRIPT, "php.yml")
    if "psalm-taint" in jobs:
        matrix = _mapping(_mapping(_mapping(jobs["psalm-taint"]).get("strategy")).get("matrix"))
        raw_tags = matrix.get("ocp")
        tags = [str(tag) for tag in raw_tags] if isinstance(raw_tags, list) else []
        if len(tags) != 3:
            findings.append(f"the ocp matrix of job psalm-taint lists {len(tags)} tags, expected 3")
        majors: set[int] = set()
        for tag in tags:
            match = _TAG.match(tag)
            if match is None:
                findings.append(f"the ocp matrix entry {tag!r} is not v<major>.<minor>.<patch>")
            else:
                majors.add(int(match.group(1)))
        expected = expected_ocp_majors(info_xml)
        findings.extend(f"the ocp matrix lacks major {major} of info.xml" for major in sorted(expected - majors))
        findings.extend(f"the ocp matrix has major {major} outside info.xml" for major in sorted(majors - expected))
    findings.extend(_check_gate_job(jobs, "php-cs", CS_SCRIPT, "php.yml"))
    return findings


def scan_lint_workflow(text: str) -> list[str]:
    """Findings about the jobs zizmor and actionlint of workflow-lint.yml."""
    workflow = _load_workflow(text)
    findings: list[str] = []
    # YAML 1.1 reads the bare key on as True.
    triggers = _mapping(workflow.get(True, workflow.get("on")))
    for event in ("push", "pull_request"):
        paths = _mapping(triggers.get(event)).get("paths")
        if not isinstance(paths, list) or ".github/**" not in paths:
            findings.append(f"the {event} trigger of workflow-lint.yml does not name '.github/**'")
    jobs = _mapping(workflow.get("jobs"))
    for mode in ("zizmor", "actionlint"):
        findings.extend(_check_gate_job(jobs, mode, f"{LINT_SCRIPT} {mode}", "workflow-lint.yml"))
    if "SHELLCHECK_OPTS" in text:
        findings.append("workflow-lint.yml names SHELLCHECK_OPTS")
    if "--severity" in text:
        findings.append("workflow-lint.yml passes a severity to shellcheck")
    findings.extend(f"workflow-lint.yml carries '{form}'" for form in LINT_DEFUSERS if form in text)
    return findings


def _require(name: str, text: str, needles: tuple[str, ...]) -> list[str]:
    return [f"{name} lacks '{needle}'" for needle in needles if needle not in text]


def _scan_lint_gate(text: str) -> list[str]:
    findings = _require(
        "workflow_lint_gate.sh",
        text,
        ("--min-severity medium", "auditor", "unset SHELLCHECK_OPTS", "SC2086", PROBE_NAME),
    )
    # The real pass and the probe, each with the same threshold and persona.
    for needle in ("--min-severity medium", "--offline", "--persona", PROBE_NAME):
        if 0 < text.count(needle) < 2:
            findings.append(f"workflow_lint_gate.sh names '{needle}' once, expected the real pass and the probe")
    findings.extend(f"workflow_lint_gate.sh carries '{form}'" for form in LINT_DEFUSERS if form in text)
    findings.extend(
        f"workflow_lint_gate.sh names the persona {persona}" for persona in WEAKER_PERSONAS if persona in text
    )
    for value in _PERSONA.findall(text):
        if value.strip("\"'") not in ("auditor", "${ZIZMOR_PERSONA}"):
            findings.append(f"workflow_lint_gate.sh runs zizmor with the persona {value}")
    if "${ZIZMOR_PERSONA}" in text and 'ZIZMOR_PERSONA="auditor"' not in text:
        findings.append("workflow_lint_gate.sh sets ZIZMOR_PERSONA to something else than auditor")
    if "--severity" in text:
        findings.append("workflow_lint_gate.sh passes a severity to shellcheck")
    if _SHELLCHECK_OPTS_ASSIGNMENT.search(text):
        findings.append("workflow_lint_gate.sh assigns SHELLCHECK_OPTS")
    return findings


def scan_gate_script(name: str, text: str) -> list[str]:
    """Findings about one gate script, by its file name."""
    if name == "psalm_taint_gate.sh":
        findings = _require(name, text, ("[.runs[].results[]]", "TaintedHtml", "env -u GITHUB_WORKFLOW"))
    elif name == "php_cs_gate.sh":
        findings = _require(name, text, ("--dry-run", "--path-mode=intersection"))
    elif name == "workflow_lint_gate.sh":
        findings = _scan_lint_gate(text)
    else:
        return [f"{name} is not a gate script of phase 44"]
    findings.extend(f"{name} carries '{defuser}'" for defuser in DEFUSERS if defuser in text)
    return findings


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def scan_psalm_config(text: str, baseline_exists: bool) -> list[str]:
    """Findings about php/psalm.xml and a baseline file next to it."""
    root = ET.fromstring(text.encode("utf-8"))  # noqa: S314 - a file of this repository, not foreign input
    findings: list[str] = []
    plugins = [
        plugin.get("filename", "")
        for plugin in root.iter(f"{PSALM_NAMESPACE}plugin")
        if plugin.get("filename", "").endswith("AppFrameworkTainter.php")
    ]
    if not plugins:
        findings.append("psalm.xml does not load the AppFrameworkTainter plugin")
    if root.get("errorBaseline") is not None:
        findings.append("psalm.xml names an errorBaseline")
    for handlers in root.iter(f"{PSALM_NAMESPACE}issueHandlers"):
        for handler in handlers.iter():
            if _local_name(handler.tag).startswith("Tainted") or handler.get("name", "").startswith("Tainted"):
                findings.append(f"psalm.xml handles the issue {_local_name(handler.tag)} in issueHandlers")
    if baseline_exists:
        findings.append("php/psalm-baseline.xml exists")
    return findings


def scan_psalm_sources(texts: dict[str, str]) -> list[str]:
    """Findings about suppressions in the files Psalm analyses."""
    return [
        f"{name} carries '{marker}'"
        for name, text in sorted(texts.items())
        for marker in ("@psalm-suppress", "@psalm-taint-escape")
        if marker in text
    ]


def scan_lint_exceptions(texts: dict[str, str], zizmor_config_exists: bool) -> list[str]:
    """Findings about inline exceptions under .github and a zizmor configuration."""
    findings: list[str] = []
    if zizmor_config_exists:
        findings.append("a zizmor configuration file exists")
    for name, text in sorted(texts.items()):
        for number, line in enumerate(text.splitlines(), start=1):
            if not _EXCEPTION_LINE.search(line):
                continue
            granted = False
            for e_id in _E_ID.findall(line):
                grant = OWNER_EXCEPTIONS.get(e_id)
                if grant is not None and name.endswith(grant[0]) and grant[1] in line:
                    granted = True
            if not granted:
                findings.append(f"{name}:{number} carries an exception without a granted E-ID: {line.strip()}")
    return findings


def _github_texts() -> dict[str, str]:
    return {
        path.relative_to(REPO_ROOT).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(GITHUB_DIR.rglob("*"))
        if path.is_file() and path.suffix in (".yml", ".yaml")
    }


def _psalm_source_texts() -> dict[str, str]:
    paths = [path for folder in PSALM_SOURCE_DIRS for path in sorted(folder.rglob("*.php"))]
    paths.extend(PSALM_SOURCE_FILES)
    return {path.relative_to(REPO_ROOT).as_posix(): path.read_text(encoding="utf-8") for path in paths}


# The real tree.


def test_php_yml_runs_the_taint_and_style_gates() -> None:
    info_xml = INFO_XML.read_text(encoding="utf-8")
    assert scan_php_workflow(PHP_WORKFLOW.read_text(encoding="utf-8"), info_xml) == []


def test_matrix_majors_match_info_xml() -> None:
    jobs = _mapping(_load_workflow(PHP_WORKFLOW.read_text(encoding="utf-8")).get("jobs"))
    tags = _mapping(_mapping(_mapping(jobs["psalm-taint"]).get("strategy")).get("matrix"))["ocp"]
    majors = {int(str(tag)[1:].split(".")[0]) for tag in tags}
    expected = expected_ocp_majors(INFO_XML.read_text(encoding="utf-8"))
    assert expected, "info.xml names no Nextcloud version window"
    assert majors == expected


def test_workflow_lint_yml_runs_zizmor_and_actionlint() -> None:
    assert scan_lint_workflow(LINT_WORKFLOW.read_text(encoding="utf-8")) == []


def test_the_gate_scripts_keep_their_controls() -> None:
    findings: list[str] = []
    for path in (PSALM_GATE, CS_GATE, LINT_GATE):
        findings.extend(scan_gate_script(path.name, path.read_text(encoding="utf-8")))
    assert findings == []


def test_psalm_config_has_the_plugin_and_no_baseline() -> None:
    assert scan_psalm_config(PSALM_CONFIG.read_text(encoding="utf-8"), PSALM_BASELINE.exists()) == []


def test_the_analysed_php_files_suppress_nothing() -> None:
    texts = _psalm_source_texts()
    assert any(name.startswith("php/lib/") for name in texts)
    assert scan_psalm_sources(texts) == []


def test_github_carries_only_granted_exceptions() -> None:
    texts = _github_texts()
    assert any(name.endswith("workflows/php.yml") for name in texts)
    assert scan_lint_exceptions(texts, any(path.exists() for path in ZIZMOR_CONFIGS)) == []


def test_the_only_exception_today_is_e13_in_php_yml() -> None:
    lines = [
        (name, line)
        for name, text in _github_texts().items()
        for line in text.splitlines()
        if _EXCEPTION_LINE.search(line)
    ]
    assert len(lines) == 1
    name, line = lines[0]
    assert name.endswith("workflows/php.yml")
    assert "E-13" in line
    assert "SC2016" in line


# Probes over php.yml: every finding is reported.

_INFO_XML = """<?xml version="1.0"?>
<info>
\t<dependencies>
\t\t<php min-version="8.2"/>
\t\t<nextcloud min-version="33" max-version="35"/>
\t</dependencies>
</info>
"""

_CLEAN_PHP_WORKFLOW = """
on:
  push:
    paths:
      - 'php/**'
jobs:
  psalm-taint:
    timeout-minutes: 15
    strategy:
      matrix:
        ocp:
          - v33.0.9
          - v34.0.6
          - v35.0.3
    steps:
      - name: Psalm taint gate with positive control
        run: bash scripts/ci/psalm_taint_gate.sh
  php-cs:
    timeout-minutes: 10
    steps:
      - name: php-cs-fixer dry run with positive control
        run: bash scripts/ci/php_cs_gate.sh
"""


def test_expected_ocp_majors_reads_the_window() -> None:
    assert expected_ocp_majors(_INFO_XML) == {33, 34, 35}


def test_a_clean_php_workflow_is_clean() -> None:
    assert scan_php_workflow(_CLEAN_PHP_WORKFLOW, _INFO_XML) == []


def test_a_missing_psalm_job_is_reported() -> None:
    source = _CLEAN_PHP_WORKFLOW.replace("  psalm-taint:", "  psalm-other:")
    assert scan_php_workflow(source, _INFO_XML) == ["php.yml has no job psalm-taint"]


def test_a_matrix_without_v34_is_reported() -> None:
    source = _CLEAN_PHP_WORKFLOW.replace("          - v34.0.6\n", "")
    assert scan_php_workflow(source, _INFO_XML) == [
        "the ocp matrix of job psalm-taint lists 2 tags, expected 3",
        "the ocp matrix lacks major 34 of info.xml",
    ]


def test_a_matrix_with_an_extra_v32_is_reported() -> None:
    source = _CLEAN_PHP_WORKFLOW.replace("          - v33.0.9\n", "          - v32.0.9\n          - v33.0.9\n")
    assert scan_php_workflow(source, _INFO_XML) == [
        "the ocp matrix of job psalm-taint lists 4 tags, expected 3",
        "the ocp matrix has major 32 outside info.xml",
    ]


def test_a_matrix_tag_without_patch_is_reported() -> None:
    source = _CLEAN_PHP_WORKFLOW.replace("v35.0.3", "v35")
    assert scan_php_workflow(source, _INFO_XML) == [
        "the ocp matrix entry 'v35' is not v<major>.<minor>.<patch>",
        "the ocp matrix lacks major 35 of info.xml",
    ]


def test_max_version_36_reports_the_missing_major() -> None:
    info_xml = _INFO_XML.replace('max-version="35"', 'max-version="36"')
    real = PHP_WORKFLOW.read_text(encoding="utf-8")
    assert scan_php_workflow(real, info_xml) == ["the ocp matrix lacks major 36 of info.xml"]


def test_min_version_34_reports_the_surplus_major() -> None:
    info_xml = _INFO_XML.replace('min-version="33"', 'min-version="34"')
    real = PHP_WORKFLOW.read_text(encoding="utf-8")
    assert scan_php_workflow(real, info_xml) == ["the ocp matrix has major 33 outside info.xml"]


def test_an_or_true_on_the_psalm_step_is_reported() -> None:
    source = _CLEAN_PHP_WORKFLOW.replace("psalm_taint_gate.sh\n", "psalm_taint_gate.sh || true\n")
    assert scan_php_workflow(source, _INFO_XML) == [
        f"the step running '{PSALM_SCRIPT}' in job psalm-taint is defused",
    ]


def test_continue_on_error_on_the_psalm_step_is_reported() -> None:
    source = _CLEAN_PHP_WORKFLOW.replace(
        "      - name: Psalm taint gate with positive control\n",
        "      - name: Psalm taint gate with positive control\n        continue-on-error: true\n",
    )
    assert scan_php_workflow(source, _INFO_XML) == [
        f"the step running '{PSALM_SCRIPT}' in job psalm-taint is defused",
    ]


def test_continue_on_error_on_the_cs_job_is_reported() -> None:
    source = _CLEAN_PHP_WORKFLOW.replace(
        "    timeout-minutes: 10\n",
        "    timeout-minutes: 10\n    continue-on-error: true\n",
    )
    assert scan_php_workflow(source, _INFO_XML) == ["job php-cs carries continue-on-error: true"]


def test_a_psalm_job_without_a_deadline_is_reported() -> None:
    source = _CLEAN_PHP_WORKFLOW.replace("    timeout-minutes: 15\n", "")
    assert scan_php_workflow(source, _INFO_XML) == ["job psalm-taint has no timeout-minutes"]


def test_a_missing_cs_job_is_reported() -> None:
    source = _CLEAN_PHP_WORKFLOW.replace("  php-cs:", "  php-style:")
    assert scan_php_workflow(source, _INFO_XML) == ["php.yml has no job php-cs"]


def test_a_cs_job_without_the_script_is_reported() -> None:
    source = _CLEAN_PHP_WORKFLOW.replace("bash scripts/ci/php_cs_gate.sh", "echo skipped")
    assert scan_php_workflow(source, _INFO_XML) == [f"job php-cs does not run '{CS_SCRIPT}'"]


# Probes over workflow-lint.yml.

_CLEAN_LINT_WORKFLOW = """
on:
  push:
    branches:
      - '**'
    paths:
      - '.github/**'
      - 'scripts/ci/workflow_lint_gate.sh'
  pull_request:
    paths:
      - '.github/**'
      - 'scripts/ci/workflow_lint_gate.sh'
jobs:
  zizmor:
    timeout-minutes: 10
    steps:
      - name: zizmor
        run: docker run --rm image sh scripts/ci/workflow_lint_gate.sh zizmor
  actionlint:
    timeout-minutes: 10
    steps:
      - name: actionlint
        run: docker run --rm image sh scripts/ci/workflow_lint_gate.sh actionlint
"""


def test_a_clean_lint_workflow_is_clean() -> None:
    assert scan_lint_workflow(_CLEAN_LINT_WORKFLOW) == []


def test_a_lint_workflow_without_zizmor_is_reported() -> None:
    source = _CLEAN_LINT_WORKFLOW.replace("  zizmor:\n", "  audit:\n")
    assert scan_lint_workflow(source) == ["workflow-lint.yml has no job zizmor"]


def test_a_lint_workflow_without_actionlint_is_reported() -> None:
    source = _CLEAN_LINT_WORKFLOW.replace("workflow_lint_gate.sh actionlint", "workflow_lint_gate.sh")
    assert scan_lint_workflow(source) == [f"job actionlint does not run '{LINT_SCRIPT} actionlint'"]


def test_a_lint_workflow_without_the_github_path_is_reported() -> None:
    source = _CLEAN_LINT_WORKFLOW.replace("      - '.github/**'\n", "      - '.github/workflows/**'\n", 1)
    assert scan_lint_workflow(source) == ["the push trigger of workflow-lint.yml does not name '.github/**'"]


def test_a_defused_lint_job_is_reported() -> None:
    source = _CLEAN_LINT_WORKFLOW.replace("gate.sh zizmor\n", "gate.sh zizmor || true\n")
    assert scan_lint_workflow(source) == [
        f"the step running '{LINT_SCRIPT} zizmor' in job zizmor is defused",
    ]


def test_a_lint_job_without_a_deadline_is_reported() -> None:
    source = _CLEAN_LINT_WORKFLOW.replace("    timeout-minutes: 10\n", "", 1)
    assert scan_lint_workflow(source) == ["job zizmor has no timeout-minutes"]


def test_shellcheck_opts_in_the_lint_workflow_is_reported() -> None:
    source = _CLEAN_LINT_WORKFLOW.replace(
        "      - name: actionlint\n",
        "      - name: actionlint\n        env:\n          SHELLCHECK_OPTS: --exclude=SC2086\n",
    )
    assert scan_lint_workflow(source) == ["workflow-lint.yml names SHELLCHECK_OPTS"]


def test_a_shellcheck_severity_in_the_lint_workflow_is_reported() -> None:
    source = _CLEAN_LINT_WORKFLOW.replace(
        "sh scripts/ci/workflow_lint_gate.sh actionlint",
        "sh scripts/ci/workflow_lint_gate.sh actionlint --severity=warning",
    )
    findings = scan_lint_workflow(source)
    assert "workflow-lint.yml passes a severity to shellcheck" in findings


# Probes over the gate scripts.

_CLEAN_PSALM_GATE = """
run_psalm() { env -u GITHUB_WORKFLOW php "${PSALM}" --taint-analysis; }
count() { jq '[.runs[].results[]] | length' "$1"; }
for rule in TaintedHtml TaintedSql; do :; done
"""

_CLEAN_CS_GATE = """
php "${FIXER}" fix --dry-run --diff
php "${FIXER}" fix --dry-run --path-mode=intersection "${PROBE}"
"""

_CLEAN_LINT_GATE = """
ZIZMOR_PERSONA="auditor"
PROBE=".github/fixtures/workflow-lint-probe.yml"
zizmor --offline --no-progress --persona "${ZIZMOR_PERSONA}" --min-severity medium --format plain .
zizmor --offline --no-progress --persona "${ZIZMOR_PERSONA}" --min-severity medium --format plain "${PROBE}"
unset SHELLCHECK_OPTS
actionlint -no-color -oneline
probe_out=$(actionlint -no-color -oneline "${PROBE}" 2>&1)
case "${probe_out}" in *SC2086*) ;; esac
# the probe is .github/fixtures/workflow-lint-probe.yml
"""


def test_clean_gate_scripts_are_clean() -> None:
    assert scan_gate_script("psalm_taint_gate.sh", _CLEAN_PSALM_GATE) == []
    assert scan_gate_script("php_cs_gate.sh", _CLEAN_CS_GATE) == []
    assert scan_gate_script("workflow_lint_gate.sh", _CLEAN_LINT_GATE) == []


def test_an_unknown_gate_script_is_reported() -> None:
    assert scan_gate_script("other.sh", "") == ["other.sh is not a gate script of phase 44"]


def test_a_psalm_gate_without_the_sarif_count_is_reported() -> None:
    source = _CLEAN_PSALM_GATE.replace("[.runs[].results[]]", ".runs")
    assert scan_gate_script("psalm_taint_gate.sh", source) == [
        "psalm_taint_gate.sh lacks '[.runs[].results[]]'",
    ]


def test_a_psalm_gate_without_tainted_html_is_reported() -> None:
    source = _CLEAN_PSALM_GATE.replace("TaintedHtml ", "")
    assert scan_gate_script("psalm_taint_gate.sh", source) == ["psalm_taint_gate.sh lacks 'TaintedHtml'"]


def test_a_psalm_gate_that_keeps_github_workflow_is_reported() -> None:
    # Psalm 6 exits 0 on taint findings with --report when GITHUB_WORKFLOW is set,
    # so the probe would read as blind on every runner (first CI run of phase 44).
    source = _CLEAN_PSALM_GATE.replace("env -u GITHUB_WORKFLOW ", "")
    assert scan_gate_script("psalm_taint_gate.sh", source) == [
        "psalm_taint_gate.sh lacks 'env -u GITHUB_WORKFLOW'",
    ]


def test_a_psalm_gate_with_or_true_is_reported() -> None:
    source = _CLEAN_PSALM_GATE.replace('"$1"; }', '"$1" || true; }')
    assert scan_gate_script("psalm_taint_gate.sh", source) == ["psalm_taint_gate.sh carries '|| true'"]


def test_a_cs_gate_without_dry_run_is_reported() -> None:
    source = _CLEAN_CS_GATE.replace("--dry-run", "")
    assert scan_gate_script("php_cs_gate.sh", source) == ["php_cs_gate.sh lacks '--dry-run'"]


def test_a_cs_gate_without_intersection_is_reported() -> None:
    source = _CLEAN_CS_GATE.replace("--path-mode=intersection", "")
    assert scan_gate_script("php_cs_gate.sh", source) == ["php_cs_gate.sh lacks '--path-mode=intersection'"]


def test_a_lint_gate_without_the_threshold_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace("--min-severity medium", "--min-severity high")
    assert scan_gate_script("workflow_lint_gate.sh", source) == [
        "workflow_lint_gate.sh lacks '--min-severity medium'",
    ]


def test_a_lint_gate_with_the_threshold_only_once_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace("--min-severity medium", "--min-severity high", 1)
    assert scan_gate_script("workflow_lint_gate.sh", source) == [
        "workflow_lint_gate.sh names '--min-severity medium' once, expected the real pass and the probe",
    ]


def test_a_lint_gate_with_no_exit_codes_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace("--format plain .", "--format plain --no-exit-codes .")
    assert scan_gate_script("workflow_lint_gate.sh", source) == ["workflow_lint_gate.sh carries '--no-exit-codes'"]


def test_a_lint_gate_with_the_sarif_format_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace("--format plain .", "--format sarif .")
    assert scan_gate_script("workflow_lint_gate.sh", source) == ["workflow_lint_gate.sh carries '--format sarif'"]


def test_a_lint_gate_with_an_ignore_pattern_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace(
        "actionlint -no-color -oneline\n", "actionlint -no-color -oneline -ignore SC2086\n"
    )
    assert scan_gate_script("workflow_lint_gate.sh", source) == ["workflow_lint_gate.sh carries '-ignore'"]


def test_a_lint_gate_with_the_persona_regular_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace('ZIZMOR_PERSONA="auditor"', 'ZIZMOR_PERSONA="regular"')
    assert scan_gate_script("workflow_lint_gate.sh", source) == [
        "workflow_lint_gate.sh lacks 'auditor'",
        "workflow_lint_gate.sh names the persona regular",
        "workflow_lint_gate.sh sets ZIZMOR_PERSONA to something else than auditor",
    ]


def test_a_lint_gate_with_a_literal_weaker_persona_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace('--persona "${ZIZMOR_PERSONA}"', "--persona pedantic", 1)
    assert scan_gate_script("workflow_lint_gate.sh", source) == [
        "workflow_lint_gate.sh names the persona pedantic",
        "workflow_lint_gate.sh runs zizmor with the persona pedantic",
    ]


def test_a_lint_gate_with_a_shellcheck_severity_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace(
        "unset SHELLCHECK_OPTS\n", "unset SHELLCHECK_OPTS\nshellcheck --severity=warning x\n"
    )
    assert scan_gate_script("workflow_lint_gate.sh", source) == [
        "workflow_lint_gate.sh passes a severity to shellcheck",
    ]


def test_a_lint_gate_assigning_shellcheck_opts_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace("unset SHELLCHECK_OPTS\n", "unset SHELLCHECK_OPTS\nexport SHELLCHECK_OPTS=-e\n")
    assert scan_gate_script("workflow_lint_gate.sh", source) == ["workflow_lint_gate.sh assigns SHELLCHECK_OPTS"]


def test_a_lint_gate_without_unset_shellcheck_opts_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace("unset SHELLCHECK_OPTS", "")
    assert scan_gate_script("workflow_lint_gate.sh", source) == [
        "workflow_lint_gate.sh lacks 'unset SHELLCHECK_OPTS'",
    ]


def test_a_lint_gate_without_sc2086_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace("*SC2086*", "*error*")
    assert scan_gate_script("workflow_lint_gate.sh", source) == ["workflow_lint_gate.sh lacks 'SC2086'"]


def test_a_lint_gate_without_the_probe_is_reported() -> None:
    source = _CLEAN_LINT_GATE.replace(PROBE_NAME, "other.yml")
    assert scan_gate_script("workflow_lint_gate.sh", source) == [f"workflow_lint_gate.sh lacks '{PROBE_NAME}'"]


# Probes over psalm.xml and the analysed sources.

_CLEAN_PSALM_CONFIG = """<?xml version="1.0"?>
<psalm errorLevel="4" findUnusedBaselineEntry="true" xmlns="https://getpsalm.org/schema/config">
\t<plugins>
\t\t<plugin filename="tools/psalm/AppFrameworkTainter.php" />
\t</plugins>
\t<projectFiles>
\t\t<directory name="lib" />
\t</projectFiles>
</psalm>
"""


def test_a_clean_psalm_config_is_clean() -> None:
    assert scan_psalm_config(_CLEAN_PSALM_CONFIG, baseline_exists=False) == []


def test_a_psalm_config_without_the_plugin_is_reported() -> None:
    source = _CLEAN_PSALM_CONFIG.replace('\t\t<plugin filename="tools/psalm/AppFrameworkTainter.php" />\n', "")
    assert scan_psalm_config(source, baseline_exists=False) == [
        "psalm.xml does not load the AppFrameworkTainter plugin",
    ]


def test_a_psalm_config_with_an_error_baseline_is_reported() -> None:
    source = _CLEAN_PSALM_CONFIG.replace('errorLevel="4"', 'errorLevel="4" errorBaseline="psalm-baseline.xml"')
    assert scan_psalm_config(source, baseline_exists=False) == ["psalm.xml names an errorBaseline"]


def test_a_psalm_config_suppressing_a_taint_issue_is_reported() -> None:
    source = _CLEAN_PSALM_CONFIG.replace(
        "</psalm>",
        '\t<issueHandlers>\n\t\t<TaintedHtml errorLevel="suppress" />\n\t</issueHandlers>\n</psalm>',
    )
    assert scan_psalm_config(source, baseline_exists=False) == [
        "psalm.xml handles the issue TaintedHtml in issueHandlers",
    ]


def test_a_psalm_config_with_a_non_taint_handler_is_clean() -> None:
    source = _CLEAN_PSALM_CONFIG.replace(
        "</psalm>",
        '\t<issueHandlers>\n\t\t<MissingReturnType errorLevel="info" />\n\t</issueHandlers>\n</psalm>',
    )
    assert scan_psalm_config(source, baseline_exists=False) == []


def test_a_psalm_baseline_file_is_reported() -> None:
    assert scan_psalm_config(_CLEAN_PSALM_CONFIG, baseline_exists=True) == ["php/psalm-baseline.xml exists"]


def test_a_suppression_in_an_analysed_file_is_reported() -> None:
    texts = {
        "php/lib/A.php": "<?php\n/** @psalm-suppress TaintedHtml */\necho $x;\n",
        "php/lib/B.php": "<?php\n/** @psalm-taint-escape html */\nfunction f() {}\n",
        "php/lib/C.php": "<?php\necho 1;\n",
    }
    assert scan_psalm_sources(texts) == [
        "php/lib/A.php carries '@psalm-suppress'",
        "php/lib/B.php carries '@psalm-taint-escape'",
    ]


# Probes over the exceptions under .github.

_EXCEPTION_WORKFLOW = """
jobs:
  probe:
    steps:
      - run: |
          echo hello
"""


def test_a_workflow_without_exceptions_is_clean() -> None:
    assert scan_lint_exceptions({".github/workflows/x.yml": _EXCEPTION_WORKFLOW}, zizmor_config_exists=False) == []


def test_a_zizmor_config_is_reported() -> None:
    texts = {".github/workflows/x.yml": _EXCEPTION_WORKFLOW}
    assert scan_lint_exceptions(texts, zizmor_config_exists=True) == ["a zizmor configuration file exists"]


def test_a_shellcheck_disable_without_e_id_is_reported() -> None:
    source = _EXCEPTION_WORKFLOW.replace(
        "          echo hello", "          # shellcheck disable=SC2086\n          echo $hello"
    )
    findings = scan_lint_exceptions({".github/workflows/x.yml": source}, zizmor_config_exists=False)
    assert len(findings) == 1
    assert findings[0].startswith(".github/workflows/x.yml:6 carries an exception without a granted E-ID")


def test_a_zizmor_ignore_without_e_id_is_reported() -> None:
    source = _EXCEPTION_WORKFLOW.replace("      - run: |", "      - run: | # zizmor: ignore[artipacked]")
    findings = scan_lint_exceptions({".github/workflows/x.yml": source}, zizmor_config_exists=False)
    assert len(findings) == 1
    assert "zizmor: ignore[artipacked]" in findings[0]


def test_an_exception_with_an_unknown_e_id_is_reported() -> None:
    source = _EXCEPTION_WORKFLOW.replace(
        "          echo hello", "          # shellcheck disable=SC2016 # E-99: wanted\n          echo hello"
    )
    findings = scan_lint_exceptions({".github/workflows/php.yml": source}, zizmor_config_exists=False)
    assert len(findings) == 1


def test_a_granted_exception_is_not_reported() -> None:
    source = _EXCEPTION_WORKFLOW.replace(
        "          echo hello",
        "          # shellcheck disable=SC2016 # E-13: PHP-Code im Einzelzitat\n          echo hello",
    )
    assert scan_lint_exceptions({".github/workflows/php.yml": source}, zizmor_config_exists=False) == []


def test_a_granted_e_id_in_another_file_is_reported() -> None:
    source = _EXCEPTION_WORKFLOW.replace(
        "          echo hello",
        "          # shellcheck disable=SC2016 # E-13: PHP-Code im Einzelzitat\n          echo hello",
    )
    findings = scan_lint_exceptions({".github/workflows/other.yml": source}, zizmor_config_exists=False)
    assert len(findings) == 1


def test_a_granted_e_id_for_another_rule_is_reported() -> None:
    source = _EXCEPTION_WORKFLOW.replace(
        "          echo hello",
        "          # shellcheck disable=SC2086 # E-13: borrowed\n          echo $hello",
    )
    findings = scan_lint_exceptions({".github/workflows/php.yml": source}, zizmor_config_exists=False)
    assert len(findings) == 1
