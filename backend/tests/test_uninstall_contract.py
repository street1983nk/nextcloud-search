"""The uninstall gate: a disable of this app must never remove anything.

Nextcloud executes ``repair-steps/uninstall`` inside ``AppManager::disableApp()``,
so the uninstall step of this app is reached by every disable and not only by a
removal. ``docs/uninstall.md`` carries the measurement of that on a running
instance. The consequence is the intent mark, and the consequence of the intent
mark is this gate: the separation between "switched off" and "removed" lives in
the order of a handful of lines, and an order is exactly the kind of property
that goes missing in a refactoring without anybody noticing.

What is pinned here, and why each of them would be silent damage:

- The intent is asked before anything is delegated. Turn that around and every
  admin who disables the search for a night loses the exclusion rules, the size
  cap, the coverage counters and the queue.
- The step holds no removal of its own, so there is one routine and not two
  truths about what uninstalling means.
- The step catches everything and never breaks off, because a repair step that
  fails takes the whole operation down with it.
- Every removal of a table is preceded by an existence check, because the step
  runs again and again and possibly before the migrations ever ran.
- The app config goes last, because it carries "enabled", "installed_version"
  and the mark itself.
- The table names come out of the constants that create them and never as a
  literal, so a rename cannot leave this routine pointing at somebody else's
  table.

**Why a Python gate over PHP sources.** There is no PHP on the development
machine and none in this repository; the PHP side is checked with ``php -l``
inside a container and nothing else. This is the same shape as Gate A in
``test_readonly_gate.py`` and Gate C in ``test_admin_ui_contract.py``: read the
sources, judge them, name the file and the reason on every finding, and stage
both a clean and a dirty sample so that the gate has to tell them apart.

**What this gate does not claim.** It says nothing about whether the removal
actually works. That is a measurement against a running instance, and it is
written down in ``docs/uninstall.md`` with the server version it was taken on.
This file only makes sure the properties that measurement relies on cannot come
back changed unnoticed.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

UNINSTALL_STEP = REPO_ROOT / "php" / "lib" / "Repair" / "AppUninstallStep.php"
PURGE_SERVICE = REPO_ROOT / "php" / "lib" / "Service" / "PurgeService.php"
INFO_XML = REPO_ROOT / "php" / "appinfo" / "info.xml"

# The three tables of this app. They belong in this gate as literals and in
# PurgeService as constants: written twice in the removal routine, a rename of
# the original would leave the routine pointing at a table that either no longer
# exists or belongs to somebody else.
TABLE_LITERALS = ("findling_queue", "findling_scan_stats", "findling_file_state")

# The three background jobs. An uninstall that forgets one of them leaves a job
# in the list whose class is gone, and every cron pass afterwards fails on it.
JOB_CLASSES = ("SchedulerJob", "StorageCrawlJob", "SubtreeExpandJob")

_INTENT_QUERY = re.compile(r"getValueBool\([^)]*PURGE_INTENT")
_THROW = re.compile(r"\bthrow\s")


def _first(lines: list[str], needle: str) -> int | None:
    """Index of the first line carrying the needle, None when there is none."""
    for index, line in enumerate(lines):
        if needle in line:
            return index

    return None


def _last(lines: list[str], needle: str) -> int | None:
    """Index of the last line carrying the needle, None when there is none."""
    for index in range(len(lines) - 1, -1, -1):
        if needle in lines[index]:
            return index

    return None


def scan_uninstall_step(name: str, source: str) -> list[str]:
    """Findings of the repair step: the mark, the delegation and the silence."""
    violations: list[str] = []
    lines = source.splitlines()

    intent = next((index for index, line in enumerate(lines) if _INTENT_QUERY.search(line) is not None), None)
    delegation = _first(lines, "purgeService->run(")

    if intent is None:
        violations.append(f"{name}: does not ask for the intent mark, so a disable of the app would remove data")
    elif delegation is not None and delegation < intent:
        violations.append(f"{name}: delegates the removal before it asks for the intent mark")

    for forbidden in ("dropTable", "deleteApp"):
        if forbidden in source:
            violations.append(f"{name}: removes with {forbidden} itself instead of leaving it to the one routine")

    if "catch (\\Throwable" not in source:
        violations.append(f"{name}: does not catch everything, so a failure here takes the whole operation down")
    if _THROW.search(source) is not None:
        violations.append(f"{name}: breaks off with an error, which a repair step must never do")

    return violations


def scan_purge_service(name: str, source: str) -> list[str]:
    """Findings of the removal routine: order, guards and the table names."""
    violations: list[str] = []
    lines = source.splitlines()

    # Every removal of a table needs its own existence check in front of it.
    # The flag is consumed by the removal, so two removals behind one check are
    # reported as well.
    guarded = False
    for line in lines:
        if "tableExists(" in line:
            guarded = True
            continue
        if "dropTable(" in line:
            if not guarded:
                violations.append(f"{name}: removes a table without checking first whether it exists")
            guarded = False

    removals = source.count("deleteApp")
    if removals != 1:
        violations.append(f"{name}: removes the app config {removals} times instead of exactly once")
    else:
        last_table = _last(lines, "dropTable(")
        config = _first(lines, "deleteApp")
        if last_table is not None and config is not None and config < last_table:
            violations.append(
                f"{name}: removes the app config before the last table, "
                "so the intent mark and the version are gone too early"
            )

    first_job = _first(lines, "jobList->remove(")
    first_table = _first(lines, "dropTable(")
    if first_job is None:
        violations.append(f"{name}: removes no background job, so a job of a removed app stays in the list")
    elif first_table is not None and first_table < first_job:
        violations.append(f"{name}: removes a table before the jobs that read it")

    violations.extend(f"{name}: does not remove the background job {job}" for job in JOB_CLASSES if job not in source)
    violations.extend(
        f"{name}: names the table {table} as a literal instead of taking it from its constant"
        for table in TABLE_LITERALS
        if table in source
    )

    return violations


def scan_info_xml(name: str, source: str) -> list[str]:
    """Findings of the registration: both classes, and both blocks on one line."""
    violations: list[str] = []
    lines = source.splitlines()

    uninstall = [line for line in lines if "<uninstall>" in line]
    if not any("AppUninstallStep" in line for line in uninstall):
        violations.append(f"{name}: registers no uninstall step, so a removal leaves the tables behind")

    commands = [line for line in lines if "<commands>" in line]
    if not any("PurgeCommand" in line for line in commands):
        violations.append(f"{name}: registers no purge command, so there is no way to state the intent")

    # The schema pattern for a PHP class name allows no surrounding whitespace,
    # so an indented class name on its own line fails the store validation.
    for opening, closing in (("<repair-steps>", "</repair-steps>"), ("<commands>", "</commands>")):
        holder = [line for line in lines if opening in line]
        if not holder:
            violations.append(f"{name}: has no {opening} block")
            continue
        if closing not in holder[0]:
            violations.append(f"{name}: spreads the {opening} block over several lines, which the store schema rejects")

    return violations


# -- the real tree ---------------------------------------------------------


def test_the_three_sources_of_the_uninstall_exist() -> None:
    # The anti vacuity clause. Every scanner above returns an empty list for a
    # source it never saw, so a gate that lost its files would look perfect.
    missing = [path.name for path in (UNINSTALL_STEP, PURGE_SERVICE, INFO_XML) if not path.is_file()]

    assert missing == []


def test_the_repair_step_asks_for_the_intent_before_it_removes_anything() -> None:
    violations = scan_uninstall_step(UNINSTALL_STEP.name, UNINSTALL_STEP.read_text(encoding="utf-8"))

    assert violations == []


def test_the_removal_routine_keeps_its_order_and_its_guards() -> None:
    violations = scan_purge_service(PURGE_SERVICE.name, PURGE_SERVICE.read_text(encoding="utf-8"))

    assert violations == []


def test_both_halves_are_registered_on_one_line_each() -> None:
    violations = scan_info_xml(INFO_XML.name, INFO_XML.read_text(encoding="utf-8"))

    assert violations == []


def test_the_step_delegates_instead_of_holding_a_second_removal() -> None:
    # Not a prohibition of its own but the mechanism behind one: there is one
    # routine, and the step reaches it instead of repeating it.
    source = UNINSTALL_STEP.read_text(encoding="utf-8")

    assert "PurgeService" in source
    assert "purgeService->run(" in source


# -- self tests: the gate has to report every shape it judges --------------

_CLEAN_STEP = """<?php
class AppUninstallStep implements IRepairStep {
\tpublic const PURGE_INTENT = 'purge_intent';

\tpublic function run(IOutput $output): void {
\t\ttry {
\t\t\tif (!$this->appConfig->getValueBool(Application::APP_ID, self::PURGE_INTENT)) {
\t\t\t\t$output->info('Findling keeps everything.');

\t\t\t\treturn;
\t\t\t}

\t\t\t$this->purgeService->run($output);
\t\t} catch (\\Throwable $e) {
\t\t\t$output->warning('Findling could not finish.');
\t\t}
\t}
}
"""

_CLEAN_SERVICE = """<?php
class PurgeService {
\tpublic function run(?IOutput $output = null): array {
\t\tforeach (self::JOBS as $job) {
\t\t\t$this->jobList->remove($job);
\t\t}

\t\tforeach (self::TABLES as $table) {
\t\t\tif (!$this->db->tableExists($table)) {
\t\t\t\tcontinue;
\t\t\t}

\t\t\t$this->db->dropTable($table);
\t\t}

\t\t$this->appConfig->deleteApp(Application::APP_ID);

\t\treturn [];
\t}
}
"""

_CLEAN_SERVICE_JOBS = "\n".join(f"// {job}" for job in JOB_CLASSES) + "\n"

_CLEAN_INFO = """<?xml version="1.0"?>
<info>
\t<id>findling</id>
\t<repair-steps><install><step>OCA\\Findling\\Repair\\AppInstallStep</step></install>\
<uninstall><step>OCA\\Findling\\Repair\\AppUninstallStep</step></uninstall></repair-steps>
\t<commands><command>OCA\\Findling\\Command\\IndexCommand</command>\
<command>OCA\\Findling\\Command\\PurgeCommand</command></commands>
</info>
"""


def _clean_service() -> str:
    """The clean sample of the routine, with the three job names in it."""
    return _CLEAN_SERVICE + _CLEAN_SERVICE_JOBS


def test_the_clean_samples_are_clean() -> None:
    # The counter sample of everything below. Without it a gate that reported
    # every file as broken would pass all the failure tests too.
    assert scan_uninstall_step("sample.php", _CLEAN_STEP) == []
    assert scan_purge_service("sample.php", _clean_service()) == []
    assert scan_info_xml("sample.xml", _CLEAN_INFO) == []


def test_a_step_without_the_intent_query_is_reported() -> None:
    source = _CLEAN_STEP.replace(
        "if (!$this->appConfig->getValueBool(Application::APP_ID, self::PURGE_INTENT)) {",
        "if (false) {",
    )

    violations = scan_uninstall_step("sample.php", source)

    assert len(violations) == 1
    assert "intent mark" in violations[0]


def test_a_step_that_removes_by_itself_is_reported() -> None:
    source = _CLEAN_STEP.replace("$this->purgeService->run($output);", "$this->db->dropTable('x');")

    violations = scan_uninstall_step("sample.php", source)

    assert len(violations) == 1
    assert "one routine" in violations[0]


def test_a_step_that_breaks_off_is_reported() -> None:
    source = _CLEAN_STEP.replace(
        "$output->warning('Findling could not finish.');",
        "throw $e;",
    )

    violations = scan_uninstall_step("sample.php", source)

    assert len(violations) == 1
    assert "breaks off" in violations[0]


def test_an_unguarded_table_removal_is_reported() -> None:
    source = _clean_service().replace(
        "\t\t\tif (!$this->db->tableExists($table)) {\n\t\t\t\tcontinue;\n\t\t\t}\n\n",
        "",
    )

    violations = scan_purge_service("sample.php", source)

    assert len(violations) == 1
    assert "whether it exists" in violations[0]


def test_the_app_config_removed_before_the_last_table_is_reported() -> None:
    source = (
        _clean_service()
        .replace(
            "\t\t\t$this->db->dropTable($table);",
            "\t\t\t$this->appConfig->deleteApp(Application::APP_ID);\n\t\t\t$this->db->dropTable($table);",
        )
        .replace("\n\t\t$this->appConfig->deleteApp(Application::APP_ID);\n", "\n")
    )

    violations = scan_purge_service("sample.php", source)

    assert len(violations) == 1
    assert "before the last table" in violations[0]


def test_a_table_name_as_a_literal_is_reported() -> None:
    source = _clean_service().replace("self::TABLES as $table", "['findling_queue'] as $table")

    violations = scan_purge_service("sample.php", source)

    assert len(violations) == 1
    assert "as a literal" in violations[0]


def test_a_forgotten_background_job_is_reported() -> None:
    source = _clean_service().replace("// SubtreeExpandJob\n", "")

    violations = scan_purge_service("sample.php", source)

    assert len(violations) == 1
    assert "SubtreeExpandJob" in violations[0]


def test_a_missing_registration_is_reported() -> None:
    without_step = _CLEAN_INFO.replace(
        "<uninstall><step>OCA\\Findling\\Repair\\AppUninstallStep</step></uninstall>", ""
    )
    without_command = _CLEAN_INFO.replace("<command>OCA\\Findling\\Command\\PurgeCommand</command>", "")

    assert len(scan_info_xml("sample.xml", without_step)) == 1
    assert len(scan_info_xml("sample.xml", without_command)) == 1


def test_a_block_spread_over_several_lines_is_reported() -> None:
    source = _CLEAN_INFO.replace("<commands><command>", "<commands>\n\t\t<command>").replace(
        "</command></commands>", "</command>\n\t</commands>"
    )

    violations = scan_info_xml("sample.xml", source)

    assert len(violations) == 2
    assert any("several lines" in message for message in violations)
