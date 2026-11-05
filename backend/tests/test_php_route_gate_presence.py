"""The structural gate over the route attribute gate of the PHP half (plan 42-02).

php/tests/Unit/RouteSecurityTest.php holds every controller route and its
attributes against php/tests/route-security.json, and it does so inside the
PHPUnit job of php.yml. That job proves the gate ran: its step "The route
attribute gate ran" reads the JUnit log and requires the test suite
RouteSecurityTest with a floor of cases and nothing skipped, failed or broken.

This file holds the shape of all three pieces from the Python side, because
python.yml runs on every backend commit and weekly by schedule, while php.yml
starts only on php/**. A gate that can be removed in the same commit that
removes what it guards is no gate, so each piece is checked here:

1. The test file exists, lies in the directory the testsuite of phpunit.xml
   names, ends on Test.php and declares exactly
   ``final class RouteSecurityTest extends TestCase``.
2. It carries nothing that skips it: no markTestSkipped, no markTestIncomplete,
   no abstract class, no Requires attribute in short or fully qualified form and
   no ``@requires`` annotation, which PHPUnit 11 still evaluates.
3. The allowlist is valid JSON and has as many entries under "routes" as the
   controllers have fully qualified ApiRoute and FrontpageRoute lines, and since
   plan 42-07 an object "classes" with one entry per controller file, each
   with ``"final": true``.
4. The JUnit step of php.yml exists, takes the file and the floor only from its
   env, keeps the floor at 34 or above, equal to the number of test methods,
   and runs exactly one ``php -r`` expression without a fixed file name and
   without a single quote. Since plan 42-04 the floor of php.yml, MIN_FLOOR
   below and the count of ``public function test`` lines in
   RouteSecurityTest.php move in lockstep, so a plan that adds a test cannot
   forget the floor, and a floor cannot run ahead of the tests.

**The limit.** This reads text and YAML. Whether the PHP expression is correct
is proven by running it, which plan 42-02 did locally and php.yml does on
every PHP commit.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PHP_ROOT = REPO_ROOT / "php"
GATE_TEST = PHP_ROOT / "tests" / "Unit" / "RouteSecurityTest.php"
ALLOWLIST = PHP_ROOT / "tests" / "route-security.json"
PHPUNIT_XML = PHP_ROOT / "phpunit.xml"
CONTROLLER_ROOT = PHP_ROOT / "lib" / "Controller"
PHP_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "php.yml"

CLASS_LINE = "final class RouteSecurityTest extends TestCase"
SUITE_NAME = "OCA\\Findling\\Tests\\Unit\\RouteSecurityTest"
STEP_NAME = "The route attribute gate ran"
MIN_FLOOR = 34

SKIP_MARKERS = (
    "markTestSkipped",
    "markTestIncomplete",
    "abstract class",
    "#[Requires",
    "#[\\PHPUnit\\Framework\\Attributes\\Requires",
    "@requires",
)

_ROUTE_LINE = re.compile(r"#\[\\OCP\\AppFramework\\Http\\Attribute\\(?:ApiRoute|FrontpageRoute)\(")
_PHP_R = "php -r '"
_TEST_METHOD = re.compile(r"^\s*public function test", re.MULTILINE)


def scan_test_source(source: str) -> list[str]:
    """Findings about the content of RouteSecurityTest.php."""
    findings: list[str] = []
    if CLASS_LINE not in source:
        findings.append(f"RouteSecurityTest.php does not declare '{CLASS_LINE}'")
    findings.extend(
        f"RouteSecurityTest.php carries {marker!r}, which can skip the gate"
        for marker in SKIP_MARKERS
        if marker in source
    )
    return findings


def count_test_methods(source: str) -> int:
    """The number of test methods, the way the floors count them."""
    return len(_TEST_METHOD.findall(source))


def workflow_floor(text: str) -> object:
    """ROUTE_GATE_MIN_TESTS of the JUnit step of php.yml, None when absent."""
    step = _gate_step(yaml.safe_load(text))
    env = step.get("env") if step is not None else None
    return env.get("ROUTE_GATE_MIN_TESTS") if isinstance(env, dict) else None


def count_route_lines(sources: list[str]) -> int:
    """Fully qualified ApiRoute and FrontpageRoute attribute lines over all controllers."""
    return sum(len(_ROUTE_LINE.findall(source)) for source in sources)


def scan_allowlist(text: str, route_count: int, controller_count: int | None = None) -> list[str]:
    """Findings about route-security.json against the number of route lines.

    With controller_count, the object "classes" has to hold exactly that many
    entries, each of them with ``"final": true``.
    """
    try:
        data: Any = json.loads(text)
    except json.JSONDecodeError as error:
        return [f"route-security.json is not valid JSON: {error}"]
    routes = data.get("routes") if isinstance(data, dict) else None
    if not isinstance(routes, dict):
        return ["route-security.json has no routes object"]
    if len(routes) != route_count:
        return [f"route-security.json has {len(routes)} entries, the controllers declare {route_count} routes"]
    if controller_count is None:
        return []
    classes = data.get("classes")
    if not isinstance(classes, dict):
        return ["route-security.json has no classes object"]
    findings: list[str] = []
    if len(classes) != controller_count:
        findings.append(
            f"route-security.json has {len(classes)} class entries, lib/Controller has {controller_count} controllers"
        )
    findings.extend(
        f"the class entry {name} is not final"
        for name, entry in sorted(classes.items())
        if not isinstance(entry, dict) or entry.get("final") is not True
    )
    return findings


def _gate_step(workflow: Any) -> dict[str, Any] | None:
    jobs = workflow.get("jobs") if isinstance(workflow, dict) else None
    job = jobs.get("phpunit") if isinstance(jobs, dict) else None
    steps = job.get("steps") if isinstance(job, dict) else None
    if not isinstance(steps, list):
        return None
    for step in steps:
        if isinstance(step, dict) and step.get("name") == STEP_NAME:
            return step
    return None


def scan_workflow(text: str) -> list[str]:
    """Findings about the JUnit step of the phpunit job in php.yml."""
    step = _gate_step(yaml.safe_load(text))
    if step is None:
        return [f"the phpunit job of php.yml has no step '{STEP_NAME}'"]

    findings: list[str] = []
    env = step.get("env")
    env = env if isinstance(env, dict) else {}
    junit = env.get("JUNIT_FILE")
    if not isinstance(junit, str) or not junit:
        findings.append("the step sets no JUNIT_FILE in its env")
    floor = env.get("ROUTE_GATE_MIN_TESTS")
    if "ROUTE_GATE_MIN_TESTS" not in env:
        findings.append("the step sets no ROUTE_GATE_MIN_TESTS in its env")
    elif isinstance(floor, bool) or not isinstance(floor, int) or floor < MIN_FLOOR:
        findings.append(f"ROUTE_GATE_MIN_TESTS is {floor!r}, it has to be an integer of at least {MIN_FLOOR}")

    run = step.get("run")
    run = run if isinstance(run, str) else ""
    if run.count(_PHP_R) != 1:
        findings.append("the step does not run exactly one php -r expression")
        return findings
    start = run.index(_PHP_R) + len(_PHP_R)
    end = run.rfind("'")
    expression = run[start:end] if end > start else ""
    if "'" in expression:
        findings.append("the php -r expression contains a single quote")
    if SUITE_NAME not in expression:
        findings.append(f"the php -r expression does not name {SUITE_NAME}")
    for name in ("JUNIT_FILE", "ROUTE_GATE_MIN_TESTS"):
        if f'getenv("{name}")' not in expression:
            findings.append(f'the php -r expression does not read getenv("{name}")')
    if "junit.xml" in expression:
        findings.append("the php -r expression names a fixed junit.xml instead of reading JUNIT_FILE")
    return findings


# The real tree.


def test_the_gate_test_lies_where_phpunit_looks() -> None:
    assert GATE_TEST.is_file(), GATE_TEST
    assert GATE_TEST.name.endswith("Test.php")
    phpunit = PHPUNIT_XML.read_text(encoding="utf-8")
    assert "<directory>tests/Unit</directory>" in phpunit
    assert GATE_TEST.parent == PHP_ROOT / "tests" / "Unit"


def test_the_gate_test_cannot_skip_itself() -> None:
    assert scan_test_source(GATE_TEST.read_text(encoding="utf-8")) == []


def test_the_allowlist_has_one_entry_per_route() -> None:
    sources = [path.read_text(encoding="utf-8") for path in sorted(CONTROLLER_ROOT.glob("*.php"))]
    route_count = count_route_lines(sources)
    assert route_count >= 20  # plan 42-02: twenty routes in seven controllers on 2026-11-04
    controller_count = len(list(CONTROLLER_ROOT.glob("*Controller.php")))
    assert controller_count == 7  # plan 42-07: seven controllers, all final, on 2026-11-05
    assert scan_allowlist(ALLOWLIST.read_text(encoding="utf-8"), route_count, controller_count) == []


def test_php_yml_proves_the_gate_ran() -> None:
    assert scan_workflow(PHP_WORKFLOW.read_text(encoding="utf-8")) == []


def test_the_floors_equal_the_number_of_test_methods() -> None:
    source = GATE_TEST.read_text(encoding="utf-8")
    methods = count_test_methods(source)
    assert methods == workflow_floor(PHP_WORKFLOW.read_text(encoding="utf-8")) == MIN_FLOOR
    # Negative probe: one test method more breaks the equality.
    grown = source + "\n\tpublic function testOneMore(): void {\n\t}\n"
    assert count_test_methods(grown) == methods + 1 != MIN_FLOOR


# Probes: every finding is reported.

_CLEAN_TEST = """<?php
namespace OCA\\Findling\\Tests\\Unit;
use PHPUnit\\Framework\\TestCase;
final class RouteSecurityTest extends TestCase {
\tpublic function testSomething(): void {
\t\t$this->assertTrue(true);
\t}
}
"""


def test_a_clean_test_source_is_clean() -> None:
    assert scan_test_source(_CLEAN_TEST) == []


def test_mark_test_skipped_is_reported() -> None:
    source = _CLEAN_TEST.replace("$this->assertTrue(true);", "$this->markTestSkipped('later');")
    findings = scan_test_source(source)
    assert len(findings) == 1
    assert "markTestSkipped" in findings[0]


def test_mark_test_incomplete_is_reported() -> None:
    source = _CLEAN_TEST.replace("$this->assertTrue(true);", "$this->markTestIncomplete('later');")
    findings = scan_test_source(source)
    assert len(findings) == 1
    assert "markTestIncomplete" in findings[0]


def test_a_requires_annotation_is_reported() -> None:
    source = _CLEAN_TEST.replace("\tpublic function", "\t/** @requires PHP 99 */\n\tpublic function")
    findings = scan_test_source(source)
    assert len(findings) == 1
    assert "@requires" in findings[0]


def test_a_short_requires_attribute_is_reported() -> None:
    source = _CLEAN_TEST.replace("\tpublic function", "\t#[RequiresPhp('99')]\n\tpublic function")
    findings = scan_test_source(source)
    assert len(findings) == 1
    assert "#[Requires" in findings[0]


def test_a_fully_qualified_requires_attribute_is_reported() -> None:
    source = _CLEAN_TEST.replace(
        "\tpublic function",
        "\t#[\\PHPUnit\\Framework\\Attributes\\RequiresOperatingSystem('Plan9')]\n\tpublic function",
    )
    findings = scan_test_source(source)
    assert len(findings) == 1
    assert "Attributes\\\\Requires" in findings[0]


def test_an_abstract_class_is_reported() -> None:
    source = _CLEAN_TEST.replace("final class RouteSecurityTest", "abstract class RouteSecurityTest")
    findings = scan_test_source(source)
    assert any("abstract class" in finding for finding in findings)
    assert any(CLASS_LINE in finding for finding in findings)


def test_a_missing_class_line_is_reported() -> None:
    source = _CLEAN_TEST.replace("final class RouteSecurityTest", "final class RouteSecurityCheck")
    findings = scan_test_source(source)
    assert len(findings) == 1
    assert CLASS_LINE in findings[0]


def test_a_wrong_entry_count_is_reported() -> None:
    text = json.dumps({"_comment": ["x"], "routes": {"A::b": {"route": "r", "attributes": []}}})
    assert scan_allowlist(text, 1) == []
    findings = scan_allowlist(text, 2)
    assert len(findings) == 1
    assert "1 entries" in findings[0]


def _with_classes(count: int, *, final: bool = True) -> str:
    classes = {
        f"C{index}Controller": {"final": final, "parents": [], "traits": [], "interfaces": []} for index in range(count)
    }
    return json.dumps({"routes": {"A::b": {"route": "r", "attributes": []}}, "classes": classes})


def test_a_complete_class_allowlist_is_clean() -> None:
    assert scan_allowlist(_with_classes(2), 1, 2) == []


def test_a_missing_class_entry_is_reported() -> None:
    findings = scan_allowlist(_with_classes(1), 1, 2)
    assert findings == ["route-security.json has 1 class entries, lib/Controller has 2 controllers"]


def test_an_extra_class_entry_is_reported() -> None:
    findings = scan_allowlist(_with_classes(3), 1, 2)
    assert findings == ["route-security.json has 3 class entries, lib/Controller has 2 controllers"]


def test_a_class_entry_that_is_not_final_is_reported() -> None:
    findings = scan_allowlist(_with_classes(2, final=False), 1, 2)
    assert findings == [
        "the class entry C0Controller is not final",
        "the class entry C1Controller is not final",
    ]


def test_a_missing_classes_object_is_reported() -> None:
    text = json.dumps({"routes": {"A::b": {"route": "r", "attributes": []}}})
    assert scan_allowlist(text, 1, 2) == ["route-security.json has no classes object"]


def test_invalid_json_is_reported() -> None:
    findings = scan_allowlist("{", 1)
    assert len(findings) == 1
    assert "not valid JSON" in findings[0]


def test_route_lines_are_counted_fully_qualified_only() -> None:
    source = (
        "\t#[\\OCP\\AppFramework\\Http\\Attribute\\ApiRoute(verb: 'GET', url: '/a')]\n"
        "\t#[\\OCP\\AppFramework\\Http\\Attribute\\FrontpageRoute(verb: 'GET', url: '/b')]\n"
        "\t#[\\OCP\\AppFramework\\Http\\Attribute\\NoCSRFRequired]\n"
    )
    assert count_route_lines([source, source]) == 4


_CLEAN_WORKFLOW = f"""
jobs:
  phpunit:
    steps:
      - name: Run the unit suite
        run: vendor/bin/phpunit --log-junit junit.xml
      - name: The route attribute gate ran
        working-directory: apps/findling
        env:
          JUNIT_FILE: junit.xml
          ROUTE_GATE_MIN_TESTS: {MIN_FLOOR}
        run: |
          php -r '
            $file = getenv("JUNIT_FILE");
            $min = getenv("ROUTE_GATE_MIN_TESTS");
            $name = "OCA\\Findling\\Tests\\Unit\\RouteSecurityTest";
          '
          rm -f junit.xml
"""


def test_a_clean_workflow_is_clean() -> None:
    assert scan_workflow(_CLEAN_WORKFLOW) == []


def test_a_workflow_without_the_step_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace(STEP_NAME, "Something else")
    findings = scan_workflow(source)
    assert len(findings) == 1
    assert STEP_NAME in findings[0]


def test_a_step_without_the_floor_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace(f"          ROUTE_GATE_MIN_TESTS: {MIN_FLOOR}\n", "")
    findings = scan_workflow(source)
    assert len(findings) == 1
    assert "sets no ROUTE_GATE_MIN_TESTS" in findings[0]


def test_a_floor_of_zero_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace(f"ROUTE_GATE_MIN_TESTS: {MIN_FLOOR}", "ROUTE_GATE_MIN_TESTS: 0")
    findings = scan_workflow(source)
    assert len(findings) == 1
    assert f"at least {MIN_FLOOR}" in findings[0]


def test_a_floor_below_the_test_count_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace(f"ROUTE_GATE_MIN_TESTS: {MIN_FLOOR}", f"ROUTE_GATE_MIN_TESTS: {MIN_FLOOR - 1}")
    findings = scan_workflow(source)
    assert len(findings) == 1
    assert f"at least {MIN_FLOOR}" in findings[0]


def test_a_fixed_junit_name_in_the_expression_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace('$file = getenv("JUNIT_FILE");', '$file = "junit.xml"; getenv("JUNIT_FILE");')
    findings = scan_workflow(source)
    assert len(findings) == 1
    assert "fixed junit.xml" in findings[0]


def test_a_single_quote_in_the_expression_is_reported() -> None:
    source = _CLEAN_WORKFLOW.replace('getenv("JUNIT_FILE")', "getenv('JUNIT_FILE')")
    findings = scan_workflow(source)
    assert any("single quote" in finding for finding in findings)
