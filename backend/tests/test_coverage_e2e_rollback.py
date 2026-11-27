"""The rollback to 1.6.2 of scripts/ci/coverage_e2e.sh opens the admin overview (V-46-06-03).

The legs upgrade and upgrade-rc1 swap both halves for 1.6.2 after the head ran.
The head wrote its own version as the recorded version of the other half
(``findling`` / ``backend_app_version``), and a 1.6.2 companion compares major
and minor of that record with its own (D-11) and answers every search with no
hit while they differ. On a 1.6.x head that never showed; on the 1.7 head the
changed file was indexed by 1.6.2 and the search stayed empty (run
45973279674: "the two halves report different versions", companion 1.6.2,
backend 1.7.1). In 1.6.2 only the admin overview refreshes the record, the
request the admin page polls, so the step now makes that request once, the way
an admin does after a manual rollback, and checks that the record says 1.6.2
before the changed file is written.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ci" / "coverage_e2e.sh"
STEP_START = 'step "rollback to 1.6.2"'
STEP_END = 'step "rename under 1.6.2"'
OLD_BACKEND = 'start_backend "${OLD_BACKEND_DIR}"'
OVERVIEW = 'overview || fail "the admin overview of the 1.6.2 companion did not answer 200"'
RECORD = "recorded=$(nc_occ config:app:get findling backend_app_version || true)"
CHECK = 'check "rollback: version of the other half the admin overview of 1.6.2 records" 1.6.2 "${recorded}"'
CHANGE = "code=$(dav alice PUT notiz.txt"


def rollback_findings(script: str) -> list[str]:
    """What keeps the rollback step from refreshing the recorded version before it tests."""
    if script.count(STEP_START) != 1 or script.count(STEP_END) != 1:
        return ["the rollback step cannot be found"]
    block = script[script.index(STEP_START) : script.index(STEP_END)]
    findings: list[str] = []
    for part in (OLD_BACKEND, OVERVIEW, RECORD, CHECK, CHANGE):
        if block.count(part) != 1:
            findings.append(f"the rollback step carries {part!r} {block.count(part)} times, expected once")
    if findings:
        return findings
    order = [block.index(part) for part in (OLD_BACKEND, OVERVIEW, RECORD, CHECK, CHANGE)]
    if order != sorted(order):
        findings.append("start of 1.6.2, admin overview, record, check and the change of notiz.txt are out of order")
    return findings


def test_the_rollback_refreshes_the_recorded_version_before_it_tests() -> None:
    assert rollback_findings(SCRIPT.read_text(encoding="utf-8")) == []


def test_the_rollback_gate_sees_the_step_without_the_overview() -> None:
    """Positive control: the step as it ran red, without the request, is a finding; so is a late request."""
    script = SCRIPT.read_text(encoding="utf-8")
    without = script.replace(OVERVIEW + "\n", "", 1)
    assert any(OVERVIEW in finding for finding in rollback_findings(without))
    if rollback_findings(script):
        return
    block_start = script.index(STEP_START)
    late = script[:block_start] + script[block_start:].replace(OVERVIEW + "\n", "", 1)
    change = late.index(CHANGE, block_start)
    line_start = late.rindex("\n", 0, change) + 1
    late = late[:line_start] + "  " + OVERVIEW + "\n" + late[line_start:]
    assert rollback_findings(late) == [
        "start of 1.6.2, admin overview, record, check and the change of notiz.txt are out of order"
    ]
