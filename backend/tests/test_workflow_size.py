"""Every workflow file stays under the size cap of GitHub Actions (plan 41-08).

GitHub refuses a workflow file above 500 KB before any job starts: the push of
plan 41-08 got run 41792857387 with "exceeds the maximum allowed size of 500
KB" and no job at all, so deploy-harp.yml proved nothing for that commit. The
cap is read here as 500 * 1024 bytes; 508782 bytes ran on 91bd49f8, 524483 did
not. A step that grows long moves its run into scripts/ci/ instead, as
"Backup pause" and "Store install 6" did in plan 41-08.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
CAP_BYTES = 500 * 1024

MOVED_STEPS = {
    "Backup pause, across restarts of the backend and of Nextcloud": "scripts/ci/backup_pause_proof.sh",
    "Store install 6, the ExApp out of the archive, image out of the registry": "scripts/ci/store_install_register.sh",
    # Moved in plan 43-10: the bounded wait of assurance 18 (run 42530680761)
    # needed room in a file that stood 36 bytes under the cap.
    "Store upgrade 1, both halves out of the release assets of the previous version": (
        "scripts/ci/upgrade_from_release_assets.sh"
    ),
}


def test_every_workflow_file_is_under_the_cap() -> None:
    files = sorted(WORKFLOWS.glob("*.yml"))
    assert files
    too_large = [f"{path.name}: {path.stat().st_size} bytes" for path in files if path.stat().st_size >= CAP_BYTES]
    assert too_large == []


def test_the_moved_steps_call_their_script_and_the_script_exists() -> None:
    document = yaml.safe_load((WORKFLOWS / "deploy-harp.yml").read_text(encoding="utf-8"))
    steps = {step["name"]: step for step in document["jobs"]["deploy-harp"]["steps"] if "name" in step}
    for name, script in MOVED_STEPS.items():
        assert steps[name]["run"] == f"bash findling-src/{script}", name
        text = (REPO_ROOT / script).read_text(encoding="utf-8")
        assert "set -eo pipefail" in text, script
        assert "${{" not in text, script
