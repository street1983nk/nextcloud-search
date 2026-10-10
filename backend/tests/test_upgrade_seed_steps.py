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


# --- The assurances that read the seed (task 3 of plan 29-11) ---------------

SNAPSHOT_STEP = "Store upgrade 3,"
SHIPPED_STEP = "Store upgrade 3b,"
RECORD_STEP = "Store upgrade 3c,"
UPGRADE_STEP = "Store upgrade 4,"
ASSURANCE_STEP = "Store upgrade 5,"

# The length of the run block of "Store upgrade 3" before plan 29-11 touched it,
# measured with yaml on the tree of b013af40. STATE.md carries the deferred item
# that this block must not grow; the growth of this plan went into "Store
# upgrade 3c" instead, and this bound keeps it there.
SNAPSHOT_RUN_MAX = 20726

# The derivation of the comment above "Store upgrade 5": every counter of the
# snapshot that the recheck of the two seed files moves, with its exact step.
# Every other counter of the snapshot is compared with unchanged().
DERIVED_STEPS = {
    ".container.docs": 1,
    ".container.indexed": 1,
    ".container.skipped": 1,
    ".container.failed": -2,
    ".nextcloud.skipped": 1,
    ".nextcloud.failed": -2,
}
UNCHANGED_COUNTERS = (".nextcloud.scheduled", ".nextcloud.running", ".container.rebuildState")

_MOVED = re.compile(r"^\s*moved_by_seed '([^']+)' (-?\d+) ", re.MULTILINE)
_UNCHANGED = re.compile(r"^\s*unchanged '([^']+)' ", re.MULTILINE)


def test_the_new_steps_stand_exactly_once() -> None:
    for prefix in (SNAPSHOT_STEP, SHIPPED_STEP, RECORD_STEP, UPGRADE_STEP, ASSURANCE_STEP):
        assert len(_named(prefix)) == 1, prefix


def test_no_step_of_the_before_state_carries_a_gone_assurance() -> None:
    for prefix in (SNAPSHOT_STEP, SHIPPED_STEP, RECORD_STEP, ASSURANCE_STEP):
        run = _run(prefix)
        assert "'gone'" not in run, prefix
        assert "skipped(gone)" not in run, prefix
        assert "UPGRADE_SEED_FILE_ID" not in run, prefix


def test_the_snapshot_step_did_not_grow() -> None:
    assert len(_run(SNAPSHOT_STEP)) <= SNAPSHOT_RUN_MAX


def test_the_snapshot_expects_the_stamped_languages_mark() -> None:
    # 1.3.2 stamps a fresh directory with its language set (deploy-harp run
    # 37452332294 read de,en); null was the 1.2.0 reading and empty the wrong
    # guess of plan 29-11, both red on a healthy installation.
    run = _run(SNAPSHOT_STEP)
    assert "'.marks.languages == \"de,en\"'" in run
    assert "'.marks.languages == \"\"'" not in run
    assert "'.marks.languages == null'" not in run


def test_the_rebuild_step_demands_the_schema_of_the_running_code() -> None:
    # From plan 29-13 to 30-04 v1.3.2 and this code shared schema 2, so the
    # language jump of "Store upgrade 6" moved no schema mark (deploy-harp run
    # 37455892381). Plan 30-04 raised SCHEMA_VERSION to 3 (body_cs, D-30-08):
    # the start still carries 2, the rebuild builds and stamps the schema of
    # this code, so the demand is 2 before and 3 after. A further schema bump in
    # config.py has to turn this gate red again.
    from findling.config import SCHEMA_VERSION

    assert SCHEMA_VERSION == 3
    run = _run("Store upgrade 6,")
    assert 'if [ "${was}" = "2" ] && [ "${now}" = "3" ]; then' in run
    assert '[ "${now}" = "2" ]; then' not in run
    assert "which is exactly one step" not in run


def test_the_assurances_demand_the_languages_mark_unchanged() -> None:
    # The set the upgrade registers is de,en, so the mark has to read the same
    # on both sides; any other value after the upgrade is a restamp.
    run = _run(ASSURANCE_STEP)
    assert 'if [ "${was}" != "de,en" ] || [ "${now}" != "${was}" ]; then' in run
    assert 'if [ -n "${was}" ] || [ -n "${now}" ]; then' not in run


def test_the_record_step_reads_the_before_state_of_the_seed() -> None:
    run = _run(RECORD_STEP)
    assert '. "${RUNNER_TEMP}/seed-probe.sh"' in run
    assert "seed_probe meta recheck_1_4_0" in run
    assert 'if [ "${recheck}" != "absent" ]; then' in run
    assert "seed_probe meta embedding_version" in run
    assert 'seed_probe stock "${UPGRADE_SEED_TIFF_ID}"' in run
    assert 'echo "UPGRADE_EMBEDDING_MARK=${embedding}"' in run
    assert 'echo "UPGRADE_VECTOR_STOCK=${stock}"' in run


def test_the_mark_names_are_the_ones_of_the_store() -> None:
    # A rename in repo.py has to turn this gate red instead of leaving the
    # workflow asking for a key nobody writes.
    from findling.store.repo import EMBEDDING_MARK, RECHECK_MARK

    for prefix in (RECORD_STEP, ASSURANCE_STEP):
        run = _run(prefix)
        assert f"seed_probe meta {RECHECK_MARK}" in run, prefix
        assert f"seed_probe meta {EMBEDDING_MARK}" in run, prefix


def test_the_upgrade_step_keeps_the_app_update_branch_fail_closed() -> None:
    # The ERROR_UP_TO_DATE trap of plan 11-11: exit code 3 with a newer
    # companion on disk has to land in an error, never in a pass.
    run = _run(UPGRADE_STEP)
    assert re.search(
        r'if \[ "\$\{new_companion\}" != "\$\{installed_before\}" \]; then\s+'
        r'if \[ "\$\{installed_after\}" != "\$\{new_companion\}" \]; then\s+'
        r'echo "::error::[^"]*did not perform the app update"\s+exit 1',
        run,
    )
    assert 'echo "the instance performed the app update: ' in run


def test_every_counter_is_moved_by_exactly_the_derived_step() -> None:
    run = _run(ASSURANCE_STEP)
    moved = {path: int(step) for path, step in _MOVED.findall(run)}
    assert moved == DERIVED_STEPS
    unchanged = set(_UNCHANGED.findall(run))
    for counter in UNCHANGED_COUNTERS:
        assert counter in unchanged, counter
    # No counter is moved and held unchanged at the same time.
    assert not unchanged & set(DERIVED_STEPS)


def test_no_counter_is_compared_with_at_least() -> None:
    run = _run(ASSURANCE_STEP)
    assert " -ge " not in run
    assert ">=" not in run
    assert '[ "$(( was + step ))" != "${now}" ]' in run


def test_the_assurance_step_waits_for_the_recheck_without_cron() -> None:
    run = _run(ASSURANCE_STEP)
    assert "UPGRADE_DRAIN_BUDGET_SECONDS" in run
    assert "cron.php" not in run
    assert "0:done:indexed/:skipped/system_file:[1-9]*)" in run


def test_the_assurance_step_states_the_recheck_of_both_seed_files() -> None:
    run = _run(ASSURANCE_STEP)
    assert 'seed_probe verdict "${UPGRADE_SEED_SIDECAR_ID}"' in run
    assert '"${sidecar}" != "skipped/system_file"' in run
    assert '"${sidecar_recorded}" != "skipped/system_file"' in run
    assert 'seed_probe verdict "${UPGRADE_SEED_TIFF_ID}"' in run
    assert '"${tiff}" != "indexed/"' in run
    assert '"${tiff_recorded}" != "0"' in run
    assert 'term_hits "${SEED_WORD}"' in run
    assert ".ocs.data.entries[0].attributes.fileId == $id" in run
    assert 'if [ "${recheck}" != "done" ]; then' in run


def test_the_assurance_step_states_that_nothing_was_embedded_again() -> None:
    run = _run(ASSURANCE_STEP)
    assert 'if [ "${embedding}" != "${UPGRADE_EMBEDDING_MARK}" ]; then' in run
    assert 'if [ "${stock}" != "${UPGRADE_VECTOR_STOCK}" ]; then' in run
    assert "for mark in schemaVersion indexVersion analyzerVersion wordlistHash; do" in run
    assert "'.profileEffective'" in run
    assert 'if [ "${profile}" != "economy" ]; then' in run


def test_the_assurance_step_carries_no_expression() -> None:
    # A run with a ${{ }} expression is capped at 21000 characters by GitHub,
    # and this block grew in plan 29-11; the matrix values arrive as env.
    assert "${{" not in _run(ASSURANCE_STEP)


def test_the_old_version_pair_is_gone_from_the_texts() -> None:
    assert "1.3.0 against the 1.2.0" not in WORKFLOW.read_text(encoding="utf-8")


@pytest.mark.parametrize("prefix", [SNAPSHOT_STEP, RECORD_STEP, UPGRADE_STEP, ASSURANCE_STEP])
def test_the_changed_steps_parse_in_bash(prefix: str, tmp_path: Path) -> None:
    answer = _bash_parses(_run(prefix), tmp_path)
    assert answer.returncode == 0, answer.stderr
