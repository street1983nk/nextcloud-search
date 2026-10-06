"""The gate over the seed of the upgrade proof in ``.github/workflows/deploy-harp.yml``.

The upgrade proof starts from v1.3.2 since plan 29-11 (D-29-01), and the seed of
"Store upgrade 2b" is the only place where the recheck of D-29-10 (plan 29-09)
meets real files on a real instance: an AppleDouble sidecar and a grey TIFF with
an unspecified extra channel, both judged failed(corrupt) by the released
container, both to be judged again by 1.4.0 without a reindex. Every unit test
of the recheck runs against fakes. If a part of this seed got lost in an edit,
the proof would not turn red; it would stay green and prove less, and nobody
reads a missing line. That is the whole reason this module exists.

The workflow is loaded with yaml and every step is found by the start of its
name, so a statement is about the step it names and not about a string that
happens to stand somewhere in five thousand lines. The run blocks are checked
as text, and every one this gate watches is handed to ``bash -n`` as well,
because a YAML file that loads can still carry a shell block that does not
parse, and that is a red run an hour into the job.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy-harp.yml"
GENERATOR = REPO_ROOT / "scripts" / "ci" / "make_upgrade_seed_tiff.py"

JOB = "deploy-harp"
SEED_STEP = "Store upgrade 2b,"


def _workflow() -> dict[str, Any]:
    loaded = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _steps() -> list[dict[str, Any]]:
    steps = _workflow()["jobs"][JOB]["steps"]
    assert isinstance(steps, list)
    return steps


def _named(prefix: str) -> list[dict[str, Any]]:
    return [step for step in _steps() if str(step.get("name", "")).startswith(prefix)]


def _run(prefix: str) -> str:
    """The run block of the one step whose name starts with ``prefix``."""
    found = _named(prefix)
    assert len(found) == 1, f"{len(found)} steps start with {prefix!r}, expected exactly one"
    run = found[0].get("run")
    assert isinstance(run, str)
    return run


def _seed_word() -> str:
    spec = importlib.util.spec_from_file_location("make_upgrade_seed_tiff", GENERATOR)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    word = module.SEED_WORD
    assert isinstance(word, str)
    return word


def _bash_parses(run: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("no bash on this machine, the syntax check of the run block cannot be made here")
    script = tmp_path / "run.sh"
    script.write_text(run, encoding="utf-8", newline="\n")
    return subprocess.run(  # noqa: S603 - an argument list, never a shell
        [bash, "-n", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_proof_starts_from_v1_3_2() -> None:
    assert _workflow()["env"]["UPGRADE_FROM_TAG"] == "v1.3.2"


def test_the_seed_word_is_the_same_in_script_and_workflow() -> None:
    assert _workflow()["jobs"][JOB]["env"]["SEED_WORD"] == _seed_word()


def test_the_seed_step_stands_exactly_once() -> None:
    assert len(_named(SEED_STEP)) == 1


def test_the_seed_step_sows_both_files() -> None:
    run = _run(SEED_STEP)
    assert "findling-src/.github/fixtures/${tiff_name}" in run
    assert "tiff_name=upgrade-seed-grey-extra.tif" in run
    assert "sidecar_name=._seed-notes.docx" in run


def test_the_sidecar_carries_the_apple_double_header() -> None:
    # 00 05 16 07 in octal, as printf writes it, and the check of the written
    # bytes next to it.
    run = _run(SEED_STEP)
    assert r"printf '\000\005\026\007" in run
    assert '"${magic}" != "00051607"' in run


def test_the_seed_step_scans_and_lets_the_old_container_judge() -> None:
    run = _run(SEED_STEP)
    assert 'files:scan --path="/testuser/files/fix-seed"' in run
    assert "findling:index --restart --no-interaction" in run
    # No verdict is written by hand any more: the released container judges.
    assert "INSERT INTO oc_findling_file_state" not in run
    assert "docker pause" not in run


def test_the_seed_step_asserts_failed_corrupt_fail_closed() -> None:
    # Both halves, the state database of the container and findling_file_state
    # of Nextcloud, and a red end in the branch that sees anything else.
    run = _run(SEED_STEP)
    assert '"${verdict}" != "failed/corrupt"' in run
    assert '"${recorded}" != "failed/corrupt"' in run
    assert 'for seed in "picture:${tiff_id}" "sidecar:${sidecar_id}"; do' in run
    assert re.search(r'if \[ "\$\{fail\}" -ne 0 \]; then\s+exit 1', run)
    # The seed word finds nothing before and after sowing.
    assert run.count('if [ "${hits}" != "0" ]; then') == 2


def test_the_seed_step_exports_both_file_ids() -> None:
    run = _run(SEED_STEP)
    assert 'echo "UPGRADE_SEED_TIFF_ID=${tiff_id}"' in run
    assert 'echo "UPGRADE_SEED_SIDECAR_ID=${sidecar_id}"' in run
    assert '} >> "${GITHUB_ENV}"' in run


def test_the_gone_seed_is_gone() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "upgrade-gone-seed" not in text
    # The old name may stand in the history of a comment, never as a value.
    assert "${SEED_TERM}" not in text
    assert "SEED_TERM:" not in text


def test_the_seed_step_parses_in_bash(tmp_path: Path) -> None:
    answer = _bash_parses(_run(SEED_STEP), tmp_path)
    assert answer.returncode == 0, answer.stderr
