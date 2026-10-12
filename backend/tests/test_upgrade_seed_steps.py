"""The gate over the seed of the upgrade proof in ``.github/workflows/deploy-harp.yml``.

The upgrade proof starts from v1.4.2 since plan 30-06 (D-30-07); from plan 29-11
(D-29-01) to then it started from v1.3.2. The seed of "Store upgrade 2b" is the
same two real files as before, an AppleDouble sidecar and a grey TIFF with an
unspecified extra channel, but the released container judges them rightly now:
1.4.2 skips the sidecar as skipped(system_file) before its first byte
(worker/poller.py:1480 of v1.4.2) and reads the picture through the shim of plan
29-07 (extract/image.py:127). Its recheck of D-29-10 has already run to "done"
on the released installation (worker/recheck.py:129), so the upgrade to this
code must move nothing at all: no counter, no verdict, no vector, no mark. If a
part of this seed or of these assurances got lost in an edit, the proof would
not turn red; it would stay green and prove less, and nobody reads a missing
line. That is the whole reason this module exists. Since plan 31-12 (FMT-06) the
same step sows the seed of the new formats where phase 31 was announced, and
"Store upgrade 3c" records the catch-up mark and the old stock before the
upgrade; their gate is the last section of this module.

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


def test_the_proof_starts_from_v1_4_2() -> None:
    assert _workflow()["env"]["UPGRADE_FROM_TAG"] == "v1.4.2"


def test_the_old_start_stands_in_comments_only() -> None:
    # v1.3.2 may stay in the chronicle of the comments, never in a value or a
    # line a shell runs.
    for number, line in enumerate(WORKFLOW.read_text(encoding="utf-8").splitlines(), start=1):
        if "1.3.2" in line:
            assert line.lstrip().startswith("#"), f"line {number}: {line.strip()}"


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


def test_the_seed_step_asserts_the_verdict_of_1_4_2_fail_closed() -> None:
    # Both halves, the state database of the container and findling_file_state
    # of Nextcloud, and a red end in the branch that sees anything else. 1.4.2
    # judges rightly: the sidecar skipped(system_file) on both sides, the
    # picture indexed with no verdict left in Nextcloud (only skipped and
    # failed are recorded there, php/lib/Command/IndexCommand.php:140).
    run = _run(SEED_STEP)
    assert '"${sidecar}" != "skipped/system_file"' in run
    assert '"${sidecar_recorded}" != "skipped/system_file"' in run
    assert '"${tiff}" != "indexed/"' in run
    assert '"${tiff_recorded}" != "0"' in run
    assert "failed/corrupt" not in run
    assert re.search(r'if \[ "\$\{fail\}" -ne 0 \]; then\s+exit 1', run)
    # The seed word finds nothing before sowing, and exactly the picture after.
    assert run.count('if [ "${hits}" != "0" ]; then') == 1
    assert ".ocs.data.entries[0].attributes.fileId == $id" in run


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

# The length of the run block of "Store upgrade 3", measured with yaml. Until
# plan 30-07 it was 20726, the length before plan 29-11 touched it (tree of
# b013af40): STATE.md carries the deferred item that this block must not grow,
# and the growth of 29-11 went into "Store upgrade 3c" instead. Plan 30-07
# (D-30-07) raised it on purpose to 20957: the two Czech counts of the snapshot
# (czech, czechStop) have to be read where every other value of a snapshot is
# read, by the one snapshot() both sides of every rebuild share, and a second
# reader would compare two measurements instead of two states. Their
# explanation went into the YAML comment above the step, outside the run block.
# The run carries no expression, so the 21000 character cap of a templated run
# does not apply to it; the bound stays a bound on growth.
SNAPSHOT_RUN_MAX = 20957

# The derivation of the comment above "Store upgrade 5" since plan 30-06: the
# recheck of D-29-10 is done on the released installation, so nothing hands a
# file back across the upgrade and every counter of the snapshot is compared
# with unchanged(). Until plan 30-06 six of them moved by a derived step.
UNCHANGED_COUNTERS = (
    ".container.docs",
    ".container.indexed",
    ".container.skipped",
    ".container.failed",
    ".nextcloud.skipped",
    ".nextcloud.failed",
    ".nextcloud.scheduled",
    ".nextcloud.running",
    ".container.rebuildState",
)

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
    # v1.4.2 stamps 2, this code stamps 3 after a rebuild. From plan 29-13 to
    # 30-04 v1.3.2 and this code shared schema 2, so the language jump of
    # "Store upgrade 6" moved no schema mark (deploy-harp run 37455892381).
    # Plan 30-04 raised SCHEMA_VERSION to 3 (body_cs, D-30-08): the start of
    # the proof (v1.4.2 since plan 30-06) carries 2, the rebuild builds and
    # stamps the schema of this code, so the demand is 2 before and 3 after,
    # and 3 on both sides of the way back in "Store upgrade 7". A further
    # schema bump in config.py has to turn this gate red again.
    from findling.config import SCHEMA_VERSION

    assert SCHEMA_VERSION == 3
    run = _run("Store upgrade 6,")
    assert 'if [ "${was}" = "2" ] && [ "${now}" = "3" ]; then' in run
    assert '[ "${now}" = "2" ]; then' not in run
    assert "which is exactly one step" not in run
    back = _run("Store upgrade 7,")
    assert 'if [ "${was}" = "3" ] && [ "${now}" = "3" ]; then' in back


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
    # 1.4.2 ran its recheck to the end before the upgrade (worker/recheck.py:129).
    assert 'if [ "${recheck}" != "done" ]; then' in run
    assert "seed_probe meta embedding_version" in run
    # The whole stock, the picture included: it was embedded under 1.4.2 and
    # must not be embedded again.
    assert "seed_probe stock 0" in run
    assert '"${tiff_chunks}" = "0"' in run
    assert '"${sidecar_chunks}" != "0"' in run
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


def test_every_counter_is_held_unchanged() -> None:
    run = _run(ASSURANCE_STEP)
    assert "moved_by_seed" not in run
    unchanged = set(_UNCHANGED.findall(run))
    for counter in UNCHANGED_COUNTERS:
        assert counter in unchanged, counter


def test_no_counter_is_compared_with_at_least() -> None:
    run = _run(ASSURANCE_STEP)
    assert " -ge " not in run
    assert ">=" not in run
    assert 'if [ "${was}" != "${now}" ]; then' in run


def test_the_assurance_step_demands_no_rebuild_and_schema_2() -> None:
    # A plain upgrade under de,en rebuilds nothing, so the stored schema mark
    # stays the 2 of 1.4.2 although this code carries 3 (30-RESEARCH pitfall 8),
    # and the rebuild state stays idle (T-30-26).
    run = _run(ASSURANCE_STEP)
    assert '.marks.schemaVersion == "2"' in run
    assert '.container.rebuildState == "idle"' in run


def test_the_assurance_step_waits_for_the_recheck_without_cron() -> None:
    run = _run(ASSURANCE_STEP)
    assert "UPGRADE_DRAIN_BUDGET_SECONDS" in run
    assert "cron.php" not in run
    assert "0:done:indexed/:skipped/system_file:[1-9]*)" in run


def test_the_assurance_step_states_both_seed_files_kept_their_verdict() -> None:
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
    assert "seed_probe stock 0" in run
    assert "for mark in schemaVersion indexVersion analyzerVersion wordlistHash; do" in run
    assert "'.profileEffective'" in run
    assert 'if [ "${profile}" != "economy" ]; then' in run


def test_the_assurance_step_carries_no_expression() -> None:
    # A run with a ${{ }} expression is capped at 21000 characters by GitHub,
    # and this block grew in plan 29-11; the matrix values arrive as env.
    assert "${{" not in _run(ASSURANCE_STEP)


def test_the_old_version_pair_is_gone_from_the_texts() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "1.3.0 against the 1.2.0" not in text
    # No step demands a recheck mark that is absent before the upgrade any more.
    assert '"${recheck}" != "absent"' not in text
    assert "judges wrongly" not in text


# --- cs switched on and off again (plan 30-07, D-30-07) ----------------------

CORPUS_STEP = "Store upgrade 2,"
REBUILD_STEP = "Store upgrade 6,"
BACK_STEP = "Store upgrade 7,"

# The Czech document, as the printf of "Store upgrade 2" writes it: octal UTF-8
# for "Proc je Smlouve o najmu bytu treba podpis." with c caron, e caron, a
# acute and r caron, because the workflow stays ASCII.
CZECH_PRINTF = r"printf 'Pro\304\215 je Smlouv\304\233 o n\303\241jmu bytu t\305\231eba podpis.\n'"
CZECH_SENTENCE = "Proč je Smlouvě o nájmu bytu třeba podpis.\n"


def _job_env() -> dict[str, Any]:
    env = _workflow()["jobs"][JOB]["env"]
    assert isinstance(env, dict)
    return env


def test_the_rebuild_switches_cs_on_without_en_and_back() -> None:
    # 30-RESEARCH pitfall 5: on a set with en, body_en folds the Czech accents
    # and the proof would be green without the Czech chain. Unsorted on
    # purpose, so the normalisation of the mark is measured.
    env = _job_env()
    assert env["REBUILD_LANGUAGES"] == "cs,de"
    assert env["REBUILD_LANGUAGES_NORMALISED"] == "de,cs"
    assert env["REBUILD_LANGUAGES_BACK"] == "de,en"
    assert "en" not in env["REBUILD_LANGUAGES"].split(",")
    assert 'recreate_with_languages "${REBUILD_LANGUAGES}"' in _run(REBUILD_STEP)
    assert 'recreate_with_languages "${REBUILD_LANGUAGES_BACK}"' in _run(BACK_STEP)


def test_the_six_language_proof_is_untouched() -> None:
    # 30-RESEARCH pitfall 7: the language proof stays at six languages, cs is
    # proved on the upgrade path alone. Seven occurrences before plan 30-07.
    text = WORKFLOW.read_text(encoding="utf-8")
    assert text.count("de,en,es,it,nl,pt") == 7
    assert "de,en,es,it,nl,pt,cs" not in text


def test_the_corpus_carries_the_czech_document() -> None:
    run = _run(CORPUS_STEP)
    assert CZECH_PRINTF + " \\\n  > data/testuser/files/upgrade-dopis-cs.txt" in run


def test_the_fill_corpus_keeps_the_de_cs_rebuild_watchable() -> None:
    # Run 38035652649: with 64 fill documents the band run to de,cs was over
    # before Nextcloud reached the restarted container, banner up in 0 rounds.
    # The Czech chain carries the fill text about six times cheaper than the
    # Spanish one, so the window is bought back with four times the text.
    run = _run(CORPUS_STEP)
    assert "for number in $(seq 1 256); do" in run
    assert "seq 1 64" not in run


def test_the_czech_printf_writes_the_sentence_of_the_plan() -> None:
    # The octal escapes decode to the sentence of plan 30-07, so the document
    # really carries Smlouve with a caron and the stop word Proc with one.
    octal = CZECH_PRINTF.removeprefix("printf '").removesuffix("'")
    written = re.sub(r"\\([0-7]{3})", lambda found: chr(int(found.group(1), 8)), octal)
    written = written.replace("\\n", "\n")
    assert written.encode("latin-1").decode("utf-8") == CZECH_SENTENCE


def test_the_snapshot_carries_both_czech_counts_beside_the_terms() -> None:
    run = _run(SNAPSHOT_STEP)
    assert "czech=$(term_hits smlouve) || return 1" in run
    assert "czech_stop=$(term_hits proc) || return 1" in run
    assert "czech: $czech," in run
    assert "czechStop: $czechstop," in run
    start = run.index("terms: {")
    assert "czech" not in run[start : run.index("},", start)]


def test_the_czech_chain_reads_one_one_then_nought_then_one() -> None:
    # smlouve 1, 1, 1, 1 and proc 1, 1, 0, 1 across release, upgrade, cs on and
    # cs off (comment above "Store upgrade 3").
    one_one = "'.czech == 1 and .czechStop == 1'"
    one_nought = "'.czech == 1 and .czechStop == 0'"
    assert one_one + ' "${RUNNER_TEMP}/upgrade-before.json"' in _run(SNAPSHOT_STEP)
    assert one_one + ' "${after}"' in _run(ASSURANCE_STEP)
    rebuild = _run(REBUILD_STEP)
    assert one_one + ' "${before}"' in rebuild
    assert one_nought + ' "${after}"' in rebuild
    back = _run(BACK_STEP)
    assert one_nought + ' "${before}"' in back
    assert one_one + ' "${after}"' in back


def test_the_rebuild_asks_the_reading_side_which_languages_it_searches() -> None:
    # Not only the marks: the reading side of the volume has to search and fill
    # de,cs after the rebuild (no en field asked or filled) and de,en after the
    # way back (body_cs without a term). Every body field is probed, not only
    # the active set plus German, or a left over body_cs would go unseen.
    rebuild = _run(REBUILD_STEP)
    assert "cat > \"${RUNNER_TEMP}/rebuild-languages.py\" <<'PY'" in rebuild
    assert "resources.searched_languages()" in rebuild
    assert "for code, field in BODY_FIELD.items() if searcher.terms_with_prefix(field" in rebuild
    assert '.searched == "de,cs" and .filled == "de,cs"' in rebuild
    assert '.searched == "de,en" and .filled == "de,en"' in _run(BACK_STEP)


def test_the_rebuild_keeps_the_spanish_nought_and_claims_no_spanish_hit() -> None:
    rebuild = _run(REBUILD_STEP)
    assert "'.spanish == 0' \"${after}\"" in rebuild
    assert ".spanish == 1" not in rebuild


def test_the_way_back_stands_exactly_once_right_after_the_rebuild() -> None:
    names = [str(step.get("name", "")) for step in _steps()]
    assert len(_named(BACK_STEP)) == 1
    rebuild = next(number for number, name in enumerate(names) if name.startswith(REBUILD_STEP))
    assert names[rebuild + 1].startswith(BACK_STEP)
    assert _named(BACK_STEP)[0]["if"] == _named(REBUILD_STEP)[0]["if"]


def test_both_rebuilds_share_one_restart_and_one_reader() -> None:
    rebuild = _run(REBUILD_STEP)
    back = _run(BACK_STEP)
    assert "cat > \"${RUNNER_TEMP}/rebuild-probe.sh\" <<'SH'" in rebuild
    for run in (rebuild, back):
        assert '. "${RUNNER_TEMP}/upgrade-probe.sh"' in run
        assert '. "${RUNNER_TEMP}/rebuild-probe.sh"' in run
        assert "take_app_password" in run
    # One restart, written once: the way back does not build a second one.
    assert "docker create" not in back
    assert rebuild.count("docker create") == 1


def test_no_vector_is_written_across_both_rebuilds() -> None:
    rebuild = _run(REBUILD_STEP)
    back = _run(BACK_STEP)
    assert 'echo "REBUILD_VECTORS_BEFORE=${vectors_before}" >> "${GITHUB_ENV}"' in rebuild
    assert 'if [ "${vectors_before}" != "${vectors_after}" ]; then' in rebuild
    assert (
        'if [ "${vectors_after}" != "${vectors_before}" ] '
        '|| [ "${vectors_after}" != "${REBUILD_VECTORS_BEFORE}" ]; then' in back
    )


def test_the_way_back_demands_the_factory_mark_and_no_drift() -> None:
    back = _run(BACK_STEP)
    assert 'if [ "${now}" != "${REBUILD_LANGUAGES_BACK}" ]; then' in back
    assert "'.marks.languages == $set and .marks.schemaVersion == \"3\"'" in back
    assert "grep -c 'built by different code'" in back
    assert 'if [ "${fail}" -ne 0 ]; then' in back


@pytest.mark.parametrize("prefix", [REBUILD_STEP, BACK_STEP])
def test_the_rebuild_steps_carry_no_expression(prefix: str) -> None:
    assert "${{" not in _run(prefix)


@pytest.mark.parametrize(
    "prefix",
    [CORPUS_STEP, SNAPSHOT_STEP, RECORD_STEP, UPGRADE_STEP, ASSURANCE_STEP, REBUILD_STEP, BACK_STEP],
)
def test_the_changed_steps_parse_in_bash(prefix: str, tmp_path: Path) -> None:
    answer = _bash_parses(_run(prefix), tmp_path)
    assert answer.returncode == 0, answer.stderr


# --- The seed of the new formats and the catch-up record (plan 31-12) -------
#
# FMT-06. "Store upgrade 2b" sows eight more files where phase 31 was announced:
# six new types and a ZIP bomb that 1.4.2 never queues, a Word 97 file under a
# .docx name that 1.4.2 books as skipped(legacy_format), and a text file that
# 1.4.2 gives up on as failed(repeatedly_stuck), in a fixed order and with no
# verdict written by hand. "Store upgrade 3c" records the catch-up mark, the
# candidates of the catch-up in the old stock and a digest of that stock.

FORMATS_GENERATOR = REPO_ROOT / "scripts" / "ci" / "make_upgrade_seed_formats.py"

NEW_SEED_IDS = (
    "UPGRADE_SEED_MAIL_ID",
    "UPGRADE_SEED_ZIP_ID",
    "UPGRADE_SEED_BOMB_ID",
    "UPGRADE_SEED_DOC_ID",
    "UPGRADE_SEED_XLS_ID",
    "UPGRADE_SEED_HEIC_ID",
    "UPGRADE_SEED_OLE_ID",
    "UPGRADE_SEED_STALE_ID",
)

# Name parts of the columns a digest of stable state must not read: time
# stamps, counters, locks and cursors.
UNSTABLE_COLUMN_PARTS = ("_at", "updated", "deliver", "lock", "cursor", "attempts", "retries", "index_version")

_ID_PATTERN = "grep -Eq '^[0-9]+$'"


def _formats_generator() -> Any:
    spec = importlib.util.spec_from_file_location("make_upgrade_seed_formats", FORMATS_GENERATOR)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _new_seed_block() -> str:
    """The part of "Store upgrade 2b" after the export of the two earlier ids."""
    run = _run(SEED_STEP)
    return run[run.index('echo "UPGRADE_SEED_SIDECAR_ID=${sidecar_id}"') :]


def _digest_query(run: str) -> str:
    """The SELECT of the digest question of seed-probe.py, up to its FROM."""
    start = run.index('elif question == "digest":')
    select = run.index("SELECT file_id, state", start)
    return run[select : run.index("FROM files", select)]


def test_the_seed_step_sows_the_new_formats_where_phase_31_was_announced() -> None:
    # Replaces test_the_seed_step_leaves_room_for_phase_31 (plan 31-12): the
    # mark was a place holder for exactly this seed, so the mark is gone and
    # the seed stands where it was, after the export of the two earlier ids.
    run = _run(SEED_STEP)
    assert "appends its legacy_format seed here" not in run
    assert "Phase 31 (FMT-06)" not in run
    exported = run.index('echo "UPGRADE_SEED_SIDECAR_ID=${sidecar_id}"')
    assert run.index("The seed of the new formats (plan 31-12, FMT-06)") > exported
    assert run.index("formats_dir=findling-src/.github/fixtures/upgrade-seed-formats") > exported
    assert run.index('echo "UPGRADE_SEED_STALE_ID=${stale_id}"') > exported


def test_the_seed_of_the_new_formats_stands_once_in_the_workflow() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert text.count("formats_dir=findling-src/.github/fixtures/upgrade-seed-formats") == 1
    assert text.count('echo "UPGRADE_SEED_STALE_ID=${stale_id}"') == 1
    assert not _named("Store upgrade 2c")


def test_the_seed_names_the_files_and_words_of_the_generator() -> None:
    module = _formats_generator()
    block = _new_seed_block()
    for name in [*module.SEED_WORDS, module.BOMB]:
        assert f"={name}" in block, name
    words = re.search(r'format_words="([a-z ]+)"', block)
    assert words is not None
    assert words.group(1).split() == list(module.SEED_WORDS.values())


def test_the_new_formats_arrive_by_upload_and_not_by_a_written_verdict() -> None:
    block = _new_seed_block()
    assert '-T "${formats_dir}/$1"' in block
    assert "remote.php/dav/files/testuser/fix-seed/$1" in block
    assert "INSERT INTO oc_findling_file_state" not in block
    assert "INSERT INTO oc_findling_queue" not in block


def test_no_line_writes_a_verdict_into_a_table() -> None:
    # T-31-40b: the give up is written by 1.4.2 and by nothing else.
    for prefix in (SEED_STEP, RECORD_STEP):
        for line in _run(prefix).splitlines():
            if "repeatedly_stuck" in line or "legacy_format" in line:
                upper = line.upper()
                assert "UPDATE " not in upper, line
                assert "INSERT " not in upper, line
                assert "REPLACE " not in upper, line


def test_the_stale_file_follows_the_fixed_order() -> None:
    # Stop, upload, the larger size in oc_filecache and in the queue row,
    # start, then the claim dated back per delivery (plan 31-12, Befund 3).
    block = _new_seed_block()
    stop = block.index('docker stop -t 60 "${container}"')
    upload = block.index('upload "${stale_name}"')
    cache = block.index("UPDATE oc_filecache SET size = ${stale_size}")
    queue = block.index("UPDATE oc_findling_queue SET size = ${stale_size}")
    start = block.index('docker start "${container}"')
    backdate = block.index("UPDATE oc_findling_queue SET locked_at = datetime(locked_at, '-3600 seconds')")
    assert stop < upload < cache < start
    assert upload < queue < start
    assert start < backdate
    # The queue row has to exist before the container runs, which is the
    # proof that the listener queued without it.
    assert block.index('if [ "${queued}" != "1:0:content" ]; then') < start
    # The give up after exactly the deliveries of MAX_DELIVERIES.
    assert 'if [ "${short}" != "3" ] || [ "${left}" != "0" ]; then' in block
    assert "grep -c 'download of one file stayed short twice'" in block


def test_the_order_waits_for_the_first_reconcile_cycle_first() -> None:
    # The nought in state.db for the stale file holds only if no cycle comes
    # after the give up, and none comes once the first cycle is finished.
    block = _new_seed_block()
    assert block.index("cycle=$(seed_probe reconcile || echo unreadable)") < block.index(
        'docker stop -t 60 "${container}"'
    )
    assert 'elif question == "reconcile":' in _run(SEED_STEP)


def test_the_new_seed_is_asserted_fail_closed_under_1_4_2() -> None:
    block = _new_seed_block()
    # The six types and the bomb: no row on either side.
    assert (
        '"eml=${mail_id}" "zip=${zip_id}" "bomb=${bomb_id}" "doc=${doc_id}" "xls=${xls_id}" "heic=${heic_id}"' in block
    )
    assert 'if [ "${rows}" != "0" ] || [ "${recorded}" != "0" ]; then' in block
    # The Word file under .docx: skipped/legacy_format on both sides.
    ole_check = 'if [ "${ole}" != "skipped/legacy_format" ] || [ "${ole_recorded}" != "skipped/legacy_format" ]; then'
    assert ole_check in block
    # The stale file: written off in Nextcloud, no row in state.db, the
    # determined value and not "0 or 1" (Blocker 1).
    assert '|| [ "${stale_recorded}" != "failed/repeatedly_stuck" ]' in block
    assert '[ "${stale}" != "0" ]' in block
    assert 'stale=$(seed_probe rows "${stale_id}" || echo unreadable)' in block
    # The seven words find nothing, before and after, with a positive control.
    assert block.count("words_find_nothing ") == 2
    assert 'if [ "${control}" != "1" ]; then' in block
    assert 'if [ "${fail}" -ne 0 ]; then' in block


def test_every_new_seed_id_is_checked_before_it_goes_into_the_environment() -> None:
    block = _new_seed_block()
    # The last export of the step; the first one in this slice closes the
    # export of the two earlier ids.
    env_block = block.rindex('} >> "${GITHUB_ENV}"')
    check = block.rindex(_ID_PATTERN, 0, env_block)
    for name in NEW_SEED_IDS:
        line = block.index(f'echo "{name}=')
        assert check < line < env_block, name
    for variable in ("mail_id", "zip_id", "bomb_id", "doc_id", "xls_id", "heic_id", "ole_id", "stale_id"):
        assert f'"${{{variable}}}"' in block[block.rindex("for value in", 0, check) : check], variable


def test_the_record_step_demands_the_catch_up_mark_absent() -> None:
    run = _run(RECORD_STEP)
    assert "catchup=$(seed_probe meta recheck_1_5_0) || exit 1" in run
    assert 'if [ "${catchup}" != "absent" ]; then' in run


def test_the_record_step_names_the_mark_of_the_store() -> None:
    from findling.store.repo import CATCHUP_MARK

    assert f"seed_probe meta {CATCHUP_MARK}" in _run(RECORD_STEP)


def test_the_digest_reads_stable_columns_only() -> None:
    probe = _run(SEED_STEP)
    columns = _digest_query(probe)
    for column in ("file_id", "state", "reason", "etag"):
        assert column in columns, column
    for part in UNSTABLE_COLUMN_PARTS:
        assert part not in columns, part
    assert "SELECT file_id, COUNT(*) FROM chunks GROUP BY file_id" in probe
    assert "ORDER BY file_id" in probe[probe.index('elif question == "digest":') :]


def test_the_digest_leaves_out_the_seed_and_the_changed_candidates_only() -> None:
    run = _run(RECORD_STEP)
    call = 'old_stock=$(seed_probe digest "${seed_ids}${expected_changed:+,${expected_changed}}") || exit 1'
    assert call in run
    assert "expected_candidates" not in call
    for name in ("UPGRADE_SEED_TIFF_ID", "UPGRADE_SEED_SIDECAR_ID", *NEW_SEED_IDS):
        assert f"${{{name}}}" in run[run.index("seed_ids=") : run.index(call)], name
    assert "grep -Eq '^[0-9]+(,[0-9]+){9}$'" in run


def test_the_digest_and_the_lists_are_checked_before_the_environment() -> None:
    run = _run(RECORD_STEP)
    env_block = run.rindex('} >> "${GITHUB_ENV}"')
    for pattern in (
        "grep -Eq '^[0-9a-f]{64}$'",
        "grep -Eq '^([0-9]+(,[0-9]+)*)?$'",
        "grep -Eq '^([0-9]+=[a-z]+/[a-z_]*(,[0-9]+=[a-z]+/[a-z_]*)*)?$'",
    ):
        assert run.index(pattern) < env_block, pattern
    for name in (
        "UPGRADE_OLD_STOCK_DIGEST",
        "UPGRADE_CATCHUP_CANDIDATES",
        "UPGRADE_CATCHUP_CANDIDATE_STATES",
        "UPGRADE_CATCHUP_CHANGED",
        "UPGRADE_CATCHUP_CHANGED_VERDICTS",
    ):
        assert run.index(f'echo "{name}=') > run.index("grep -Eq '^[0-9a-f]{64}$'"), name


def test_the_two_candidate_lists_are_disjoint_before_the_environment() -> None:
    # Vierte Runde, Punkt 1: an id in both lists ends the step, and the check
    # stands before anything is written.
    run = _run(RECORD_STEP)
    disjoint = run.index("shared=$(comm -12 <(printf '%s\\n' ${expected_candidates//,/ } | sort)")
    assert 'if [ -n "${shared}" ]; then' in run[disjoint:]
    assert disjoint < run.rindex('} >> "${GITHUB_ENV}"')
    assert disjoint < run.index('echo "UPGRADE_CATCHUP_CANDIDATES=')


def test_the_old_stock_is_held_against_the_determination() -> None:
    run = _run(RECORD_STEP)
    assert 'if [ "${found_sorted}" != "${expected_sorted}" ]; then' in run
    # The determination of 31-12-SUMMARY: no candidate in the old stock.
    assert 'expected_candidates=""' in run
    assert 'expected_changed=""' in run


def test_part_a_of_the_probe_is_the_rule_of_catchup() -> None:
    # The container asked in 3c runs 1.4.2, so the rule is written out in the
    # probe; these are the sets of worker/catchup.py, held equal here.
    from findling.worker import catchup

    probe = _run(SEED_STEP)
    part = probe[probe.index('elif question == "catchup":') : probe.index('elif question == "digest":')]
    for mime in (*catchup.NEW_MIMETYPES, *catchup._POWERPOINT_MIMETYPES):
        assert f'"{mime}"' in part, mime
    for ending in (*catchup._NEW_EXTENSIONS, *catchup._POWERPOINT_EXTENSIONS):
        assert f'"{ending}"' in part, ending
    record = _run(RECORD_STEP)
    for mime in catchup.NEW_MIMETYPES:
        assert f"'{mime}'" in record, mime


def test_the_mixed_window_pairs_are_the_fallback_table() -> None:
    from findling.nc.queue import SKIPPED_FALLBACK_WITHOUT_SIGNAL

    run = _run(RECORD_STEP)
    for real, fallback in SKIPPED_FALLBACK_WITHOUT_SIGNAL.items():
        assert f"{fallback}:skipped/{real}" in run, real


@pytest.mark.parametrize("prefix", [SEED_STEP, RECORD_STEP])
def test_the_seed_and_record_steps_carry_no_expression(prefix: str) -> None:
    assert "${{" not in _run(prefix)


def test_the_record_step_parses_in_bash(tmp_path: Path) -> None:
    answer = _bash_parses(_run(RECORD_STEP), tmp_path)
    assert answer.returncode == 0, answer.stderr
