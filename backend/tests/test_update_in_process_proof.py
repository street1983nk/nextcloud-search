"""The probe of the update proof of issue #51 and its control 2 (plan 45-26).

scripts/ci/update_in_process_driver.php plants the recorded container version
before it swaps the files and demands it gone after every minor step, because
a recorded version that survives a minor step makes SearchService answer no
hits until somebody opens the settings page. scripts/ci/update_in_process_proof.sh
runs control 2, the candidate without the migrations of its own release from
the newest FROM_TAG, and demands that it fails on exactly that message.

Three things tie the two files to the rest of the tree, and each is held here
with a checker over text and a counter sample (B8): the key the driver plants
is the key ExAppService records, the message control 2 waits for is the one
the driver prints, and the newest FROM_TAG is the release before the
candidate, so control 2 starts where the store update of the candidate starts.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DRIVER = REPO_ROOT / "scripts" / "ci" / "update_in_process_driver.php"
PROOF = REPO_ROOT / "scripts" / "ci" / "update_in_process_proof.sh"
EXAPP_SERVICE = REPO_ROOT / "php" / "lib" / "Service" / "ExAppService.php"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
INFO_XML = REPO_ROOT / "php" / "appinfo" / "info.xml"


def key_findings(service: str, driver: str) -> list[str]:
    """What keeps the planted key from being the key the service records."""
    service_keys = re.findall(r"public const KEY_BACKEND_VERSION = '([^']*)';", service)
    driver_keys = re.findall(r"\$recordKey = '([^']*)';", driver)
    findings: list[str] = []
    if len(service_keys) != 1:
        findings.append(f"ExAppService names KEY_BACKEND_VERSION {len(service_keys)} times, not once")
    if len(driver_keys) != 1:
        findings.append(f"the driver sets $recordKey {len(driver_keys)} times, not once")
    if not findings and service_keys[0] != driver_keys[0]:
        findings.append(f"the driver plants {driver_keys[0]!r}, the service records {service_keys[0]!r}")
    return findings


def message_findings(proof: str, driver: str) -> list[str]:
    """What keeps control 2 from waiting for the failure the probe prints."""
    messages = re.findall(r'^CONTROL2_MESSAGE="([^"]*)"$', proof, re.MULTILINE)
    if len(messages) != 1 or not messages[0]:
        return [f"the proof sets CONTROL2_MESSAGE {len(messages)} times or empty, not once"]
    failures = re.findall(r'proofFail\("([^"]*)"\)', driver)
    if not any(messages[0] in failure for failure in failures):
        return [f"no proofFail of the driver carries {messages[0]!r}"]
    return []


def from_tag_findings(changelog: str, proof: str, info_xml: str) -> list[str]:
    """What keeps the newest FROM_TAG from being the release before the candidate.

    The first two version headings of the changelog count; ``## [Unreleased]``
    does not match the pattern and so is never one of them.
    """
    versions = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.MULTILINE)
    defaults = re.findall(r'^FROM_TAGS="\$\{FROM_TAGS:-([^}"]*)\}"$', proof, re.MULTILINE)
    infos = re.findall(r"<version>(\d+\.\d+\.\d+)</version>", info_xml)
    findings: list[str] = []
    if len(versions) < 2:
        findings.append("the changelog carries fewer than two version headings")
    if len(defaults) != 1 or not defaults[0].split():
        findings.append("the proof sets no single default of FROM_TAGS")
    if len(infos) != 1:
        findings.append(f"info.xml carries {len(infos)} versions, not one")
    if findings:
        return findings
    newest = defaults[0].split()[-1]
    if newest != f"v{versions[1]}":
        findings.append(f"the newest FROM_TAG is {newest}, the release before the candidate is v{versions[1]}")
    if infos[0] != versions[0]:
        findings.append(f"info.xml carries {infos[0]}, the newest changelog heading is {versions[0]}")
    return findings


_PLANT = "Server::get(IAppConfig::class)->setValueString($appId, $recordKey, $oldVersion);"
_READ_BACK = re.compile(
    r"if \(Server::get\(IAppConfig::class\)->getValueString\(\$appId, \$recordKey, ''\) !== \$oldVersion\) \{\s*"
    r'proofFail\("[^"]*planted[^"]*"\);\s*\}'
)


def read_back_findings(driver: str) -> list[str]:
    """What keeps the driver from proving the planted value before the swap (R-45-21-03).

    Without the read back a plant that silently did not take leaves the ok line
    of a minor step saying "dropped" for a value that was never there (M35 of
    plan 45-26); only control 2 caught that.
    """
    plant = driver.find(_PLANT)
    swap = driver.find("removeTree($appPath);")
    if plant < 0 or swap < 0:
        return ["the driver has no plant or no swap"]
    check = _READ_BACK.search(driver, plant)
    if check is None or check.start() > swap:
        return ["the driver does not read the planted value back before the swap"]
    return []


def test_the_driver_reads_the_planted_value_back_before_the_swap() -> None:
    driver = DRIVER.read_text(encoding="utf-8").replace("\r\n", "\n")

    assert read_back_findings(driver) == []

    # Counter samples (B8): the read back gone, and the read back after the swap.
    match = _READ_BACK.search(driver)
    assert match is not None
    without = driver.replace(match.group(0), "", 1)
    assert read_back_findings(without) == ["the driver does not read the planted value back before the swap"]
    late = without.replace("removeTree($appPath);", match.group(0) + "\nremoveTree($appPath);", 1)
    late = late.replace(match.group(0) + "\nremoveTree($appPath);", "removeTree($appPath);\n" + match.group(0), 1)
    assert read_back_findings(late) == ["the driver does not read the planted value back before the swap"]


def test_the_driver_plants_the_key_the_service_records() -> None:
    service = EXAPP_SERVICE.read_text(encoding="utf-8")
    driver = DRIVER.read_text(encoding="utf-8")

    assert key_findings(service, driver) == []

    # Counter sample: a driver that plants another key is refused.
    wrong = driver.replace("$recordKey = 'backend_app_version';", "$recordKey = 'backend_version';")
    assert wrong != driver
    assert key_findings(service, wrong) != []


def test_the_probe_and_its_control_name_the_same_failure() -> None:
    proof = PROOF.read_text(encoding="utf-8")
    driver = DRIVER.read_text(encoding="utf-8")

    assert message_findings(proof, driver) == []
    assert "survived the minor step" in driver

    # Counter sample: control 2 waiting for a message the driver never prints.
    wrong = proof.replace('CONTROL2_MESSAGE="survived the minor step"', 'CONTROL2_MESSAGE="outlived the minor step"')
    assert wrong != proof
    assert message_findings(wrong, driver) != []


def test_the_newest_from_tag_is_the_release_before_the_candidate() -> None:
    changelog = CHANGELOG.read_text(encoding="utf-8")
    proof = PROOF.read_text(encoding="utf-8")
    info_xml = INFO_XML.read_text(encoding="utf-8")

    assert from_tag_findings(changelog, proof, info_xml) == []

    # Counter sample (a): the newest FROM_TAG one release too old.
    old_default = 'FROM_TAGS="${FROM_TAGS:-v1.3.2 v1.4.3 v1.5.1 v1.6.2 v1.6.3 v1.6.4 v1.6.4}"'
    sample_a = "#!/usr/bin/env bash\n" + old_default + "\n"
    sample_changelog = "# Changelog\n\n## [Unreleased]\n\n## [1.7.0] - 2026-11-22\n\n## [1.6.5] - 2026-11-16\n"
    sample_info = "<info>\n\t<version>1.7.0</version>\n</info>\n"
    assert from_tag_findings(sample_changelog, sample_a, sample_info) != []

    # Counter sample (b): FROM_TAGS ending on the candidate itself. A checker
    # that counted "## [Unreleased]" as the first heading would take [1.7.0]
    # as the second and let it pass.
    candidate_default = 'FROM_TAGS="${FROM_TAGS:-v1.6.5 v1.7.0}"'
    sample_b = "#!/usr/bin/env bash\n" + candidate_default + "\n"
    assert from_tag_findings(sample_changelog, sample_b, sample_info) != []

    # And the samples are built right: the same changelog with v1.6.5 passes.
    sample_ok = "#!/usr/bin/env bash\n" + 'FROM_TAGS="${FROM_TAGS:-v1.6.4 v1.6.5}"' + "\n"
    assert from_tag_findings(sample_changelog, sample_ok, sample_info) == []
