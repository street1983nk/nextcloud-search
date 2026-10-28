"""The gate over the seed of the upgrade proof in ``.github/workflows/deploy-harp.yml``.

The upgrade proof starts from v1.5.0 since plan 40-03 (REL-06): the release the
store carried before 1.5.1, whose backend/src and PHP files are byte identical
to 1.5.1. Before that it started from v1.4.3 (plan 36-13, D-36-13), v1.4.2
(plan 30-06, D-30-07) and v1.3.2 (plan 29-11, D-29-01). The seed of "Store
upgrade 2b" is the same set of real files as before, and the released container
judges every one of them itself now: the AppleDouble sidecar is
skipped(system_file) before its first byte (worker/poller.py:1499 of v1.5.0),
the grey TIFF is read through the shim of plan 29-07 (extract/image.py:118),
the six new types are on the allowlist of the tag
(php/lib/Service/StorageService.php:133 of v1.5.0) and indexed, the ZIP bomb
ends skipped(archive_limit) (extract/archive.py), the Word file under .docx is
read by content (extract/cfb.py:122, extract/legacy_doc.py) and the stale file
is accepted at its first delivery (POL-02, worker/poller.py:2036 of v1.5.0: two
short reads with the same count and hash). Both marks, recheck_1_4_0
(worker/recheck.py:146) and recheck_1_5_0 (worker/reconcile.py:469), read done
on the released installation, so the upgrade to this code must move nothing at
all: no counter, no verdict, no vector, no mark. If a part of this seed or of
these assurances got lost in an edit, the proof would not turn red; it would
stay green and prove less, and nobody reads a missing line. That is the whole
reason this module exists. Since plan 31-12 (FMT-06) the same step sows the
seed of the new formats where phase 31 was announced, and "Store upgrade 3c"
records both marks and the old stock before the upgrade; their gate is the last
section of this module. Every derivation per assurance stands in
.planning/phases/40-haertung-und-store-einreichung-1-6-0/40-03-ABLEITUNG.md.

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


def test_the_proof_starts_from_v1_5_0() -> None:
    # Since plan 40-03 (REL-06): v1.5.0 is the release the store carried before
    # 1.5.1, and 1.5.1 only renamed the store name of the companion, so a start
    # on v1.5.0 proves the path of every 1.5.x installation. Every assurance
    # that names the behaviour of the start was derived anew for 1.5.0 in
    # 40-03-ABLEITUNG.md, none softened.
    assert _workflow()["env"]["UPGRADE_FROM_TAG"] == "v1.5.0"


@pytest.mark.parametrize("old_start", ["1.3.2", "1.4.2", "1.4.3"])
def test_the_old_start_stands_in_comments_only(old_start: str) -> None:
    # An earlier start may stay in the chronicle of the comments, never in a
    # value or a line a shell runs.
    for number, line in enumerate(WORKFLOW.read_text(encoding="utf-8").splitlines(), start=1):
        if old_start in line:
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


def test_the_seed_step_asserts_the_verdict_of_the_start_fail_closed() -> None:
    # Both halves, the state database of the container and findling_file_state
    # of Nextcloud, and a red end in the branch that sees anything else. 1.5.0
    # judges rightly, exactly as 1.4.2 did: the sidecar skipped(system_file) on
    # both sides (worker/poller.py:1499 of v1.5.0), the picture indexed with no
    # verdict left in Nextcloud (only skipped and failed are recorded there,
    # php/lib/Command/IndexCommand.php:140).
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

# The derivation of the comment above "Store upgrade 5". Since plan 40-03 the
# start is v1.5.0, which indexed the whole seed itself: the recheck of D-29-10
# and the catch-up of 1.5 both read done before the upgrade (recheck.py:146 and
# reconcile.py:469 of v1.5.0, 40-03-ABLEITUNG.md), recheck_step and catchup_step
# return at once on done, so the upgrade moves not one counter. From plan 31-13
# to 40-03 the catch-up moved docs and indexed by +7 and Nextcloud's failed
# files by -1; every step is a nought now and compared with unchanged().
DERIVED_STEPS = {
    ".container.docs": 0,
    ".container.indexed": 0,
    ".container.skipped": 0,
    ".container.failed": 0,
    ".nextcloud.skipped": 0,
    ".nextcloud.failed": 0,
    ".nextcloud.scheduled": 0,
    ".nextcloud.running": 0,
    ".container.rebuildState": 0,
}

_UNCHANGED = re.compile(r"^\s*unchanged '([^']+)' ", re.MULTILINE)
_MOVED = re.compile(r"^\s*moved '([^']+)' ([+-][0-9]+) ", re.MULTILINE)


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
    # v1.5.0 stamps 3 at the fresh directory (config.py:58 of v1.5.0) and this
    # code stamps 3 after a rebuild, so the demand is 3 on both sides of "Store
    # upgrade 6" and of the way back in "Store upgrade 7"; what proves the
    # rebuild stamped at all is the languages mark, which only stamp_after_swap
    # writes into an existing directory. From plan 30-06 to 40-03 the start
    # carried 2 and the demand was 2 before and 3 after (run 37455892381 for
    # the 2/2 era before that). A schema bump in config.py has to turn this
    # gate red again.
    from findling.config import SCHEMA_VERSION

    assert SCHEMA_VERSION == 3
    run = _run("Store upgrade 6,")
    assert 'if [ "${was}" = "3" ] && [ "${now}" = "3" ]; then' in run
    assert '[ "${was}" = "2" ]' not in run
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
    # 1.5.0 ran its recheck to the end before the upgrade (worker/recheck.py:146
    # of v1.5.0, an empty scan still ends in done).
    assert 'if [ "${recheck}" != "done" ]; then' in run
    assert "seed_probe meta embedding_version" in run
    # The whole stock, the picture and the seed of the new formats included:
    # all of it was embedded under 1.5.0 and none of it may be embedded again.
    assert "seed_probe stock 0" in run
    assert '"${tiff_chunks}" = "0"' in run
    assert '"${sidecar_chunks}" != "0"' in run
    # The seven indexed files of the new formats carry their vectors before the
    # stock is recorded, or the digest would move when the poller catches up.
    assert 'for id in ${new_indexed_ids}; do' in run
    assert 'if [ -n "${unembedded}" ]; then' in run
    # The stored schema mark of the start, read out of the snapshot of "Store
    # upgrade 3": 3 is what a fresh directory of v1.5.0 is stamped with.
    assert """'.marks.schemaVersion == "3"' "${RUNNER_TEMP}/upgrade-before.json\"""" in run
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


def _assurance_comment() -> str:
    """The YAML comment right above "Store upgrade 5", where the table stands."""
    text = WORKFLOW.read_text(encoding="utf-8")
    start = text.index("      - name: " + ASSURANCE_STEP)
    return text[text.rindex('} >> "${GITHUB_ENV}"', 0, start) : start]


def test_every_counter_is_unchanged_or_moved_by_its_derived_step() -> None:
    # Since plan 40-03 every derived step is a nought: the start v1.5.0 indexed
    # the whole seed itself, so a counter that moves at all is a finding. The
    # moved() helper of plan 31-13 is gone with the last moved counter; a new
    # seed that moves one has to bring the helper back with its exact step.
    run = _run(ASSURANCE_STEP)
    unchanged = _UNCHANGED.findall(run)
    moved = _MOVED.findall(run)
    for counter, step in DERIVED_STEPS.items():
        assert step == 0, counter
        assert unchanged.count(counter) == 1, counter
        assert counter not in [path for path, _ in moved], counter
    assert moved == []


def test_the_table_of_the_derived_steps_stands_above_the_step() -> None:
    comment = _assurance_comment()
    for counter, step in DERIVED_STEPS.items():
        written = "0" if step == 0 else f"{step:+d}"
        pattern = rf"^\s*#\s+{re.escape(counter.lstrip('.'))}\s+{re.escape(written)}\s"
        assert re.search(pattern, comment, re.MULTILINE), counter


def test_no_counter_is_compared_with_at_least() -> None:
    run = _run(ASSURANCE_STEP)
    assert " -ge " not in run
    assert ">=" not in run
    assert 'if [ "${was}" != "${now}" ]; then' in run


def test_the_assurance_step_demands_no_rebuild_and_schema_3() -> None:
    # A plain upgrade under de,en rebuilds nothing, so the stored schema mark
    # stays the 3 a fresh directory of v1.5.0 was stamped with (config.py:58 and
    # index/open.py:256 of v1.5.0); a 2 after the upgrade would be a start that
    # was never 1.5.0. The rebuild state stays idle (T-30-26).
    run = _run(ASSURANCE_STEP)
    assert '.marks.schemaVersion == "3"' in run
    assert '.marks.schemaVersion == "2"' not in run
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
    # Since plan 40-03 the WHOLE stock, the seed of the new formats included:
    # every one of its files was embedded under v1.5.0 before "Store upgrade
    # 3c" recorded the stock, so not one vector may move across the upgrade.
    # From plan 31-13 to 40-03 the eight new seed ids stood outside the digest,
    # because the catch-up embedded them only after the upgrade.
    assert 'stock=$(seed_probe stock 0 || echo "unreadable")' in run
    assert 'seed_probe stock "${new_seed_ids}"' not in run
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
# FMT-06. "Store upgrade 2b" sows eight more files where phase 31 was announced.
# Since plan 40-03 the start is v1.5.0, which reads every one of them itself:
# the six new types are indexed (allowlist of StorageService.php:133 of v1.5.0),
# the ZIP bomb ends skipped(archive_limit), the Word 97 file under the .docx
# name is read by content (cfb.py:122, legacy_doc.py), and the stale file of
# the fixed order is accepted at its first delivery (POL-02, poller.py:2036 of
# v1.5.0) and indexed. No verdict is written by hand. "Store upgrade 3c"
# records both marks, the vectors of the seed and a digest of the old stock.
# Until 40-03 the start was 1.4.x, the six were never queued, the Word file was
# skipped(legacy_format) and the stale file failed(repeatedly_stuck); the
# catch-up after the upgrade was what indexed them.

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

_ID_PATTERN = '[[ "${value}" =~ ^[0-9]+$ ]]'


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
    # start; then v1.5.0 accepts the file at its first delivery (POL-02,
    # poller.py:2036 of the tag: the download comes back short, is fetched once
    # more, and the same count and hash are taken as the file). No claim is
    # dated back any more, and no give up is waited for.
    block = _new_seed_block()
    stop = block.index('docker stop -t 60 "${container}"')
    upload = block.index('upload "${stale_name}"')
    cache = block.index("UPDATE oc_filecache SET size = ${stale_size}")
    queue = block.index("UPDATE oc_findling_queue SET size = ${stale_size}")
    start = block.index('docker start "${container}"')
    assert stop < upload < cache < start
    assert upload < queue < start
    # The queue row has to exist before the container runs, which is the
    # proof that the listener queued without it.
    assert block.index('if [ "${queued}" != "1:0:content" ]; then') < start
    # The acceptance by the exact log lines of POL-02: one short answer, one
    # acceptance, and never the "stayed short twice" of the old give up path.
    assert "grep -c 'download of one file came back short, fetching it once more'" in block
    assert "grep -c 'the file cache names a stale size, the same'" in block
    assert "grep -c 'download of one file stayed short twice'" in block
    assert 'if [ "${short}:${accepted}:${stuck}" != "1:1:0" ]; then' in block
    # The backdating of the claim is gone with the give up, and no line a
    # shell runs claims the old verdict; the history may stay in comments.
    assert "locked_at = datetime(locked_at" not in block
    for line in _run(SEED_STEP).splitlines():
        if "repeatedly_stuck" in line:
            assert line.lstrip().startswith("#"), line


def test_the_order_waits_for_the_first_reconcile_cycle_first() -> None:
    # The nought in state.db for the stale file holds only if no cycle comes
    # after the give up, and none comes once the first cycle is finished.
    block = _new_seed_block()
    assert block.index("cycle=$(seed_probe reconcile || echo unreadable)") < block.index(
        'docker stop -t 60 "${container}"'
    )
    assert 'elif question == "reconcile":' in _run(SEED_STEP)


def test_the_new_seed_is_asserted_fail_closed_under_the_start() -> None:
    block = _new_seed_block()
    # The six types and the Word file under .docx: indexed in state.db with no
    # verdict in findling_file_state, because 1.5.0 reads all seven itself.
    assert (
        '"mail=${mail_id}" "zip=${zip_id}" "doc=${doc_id}" "xls=${xls_id}" "heic=${heic_id}" "ole=${ole_id}"' in block
    )
    assert 'if [ "${verdict}" != "indexed/" ] || [ "${recorded}" != "0" ]; then' in block
    # The bomb: skipped/archive_limit on both sides, judged by the tag.
    bomb_check = 'if [ "${bomb}" != "skipped/archive_limit" ] || [ "${bomb_recorded}" != "skipped/archive_limit" ]; then'
    assert bomb_check in block
    # The stale file: indexed in state.db, no verdict in Nextcloud and no queue
    # row left, the determined values and not a range.
    assert 'if [ "${stale}" != "indexed/" ] || [ "${stale_recorded}" != "0" ] || [ "${left}" != "0" ]; then' in block
    assert 'stale=$(seed_probe verdict "${stale_id}" || echo unreadable)' in block
    # The seven words find nothing before the seed and exactly their file after
    # it, with a positive control on both sides.
    assert block.count("words_find_nothing ") == 1
    assert "words_exact" in block
    assert 'if [ -z "${words_ok}" ]; then' in block
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


def test_the_record_step_demands_the_catch_up_mark_done() -> None:
    # 1.5.0 knows its own catch-up: part A runs at the first rounds
    # (worker/catchup.py:148-190 of v1.5.0) and part B is the first reconcile
    # cycle, which "Store upgrade 2b" waits out, so the mark reads done before
    # the upgrade (worker/reconcile.py:469 of v1.5.0). Until plan 40-03 the
    # start did not know the mark and the demand was absent.
    run = _run(RECORD_STEP)
    assert "catchup=$(seed_probe meta recheck_1_5_0) || exit 1" in run
    assert 'if [ "${catchup}" != "done" ]; then' in run
    assert '"${catchup}" != "absent"' not in run


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
    assert '[[ "${seed_ids}" =~ ^[0-9]+(,[0-9]+){9}$ ]]' in run


def test_the_digest_and_the_lists_are_checked_before_the_environment() -> None:
    run = _run(RECORD_STEP)
    env_block = run.rindex('} >> "${GITHUB_ENV}"')
    for pattern in (
        '[[ "${old_digest}" =~ ^[0-9a-f]{64}$ ]]',
        '[[ "${list}" =~ ^([0-9]+(,[0-9]+)*)?$ ]]',
        '[[ "${list}" =~ ^([0-9]+=[a-z]+/[a-z_]*(,[0-9]+=[a-z]+/[a-z_]*)*)?$ ]]',
    ):
        assert run.index(pattern) < env_block, pattern
    for name in (
        "UPGRADE_OLD_STOCK_DIGEST",
        "UPGRADE_CATCHUP_CANDIDATES",
        "UPGRADE_CATCHUP_CANDIDATE_STATES",
        "UPGRADE_CATCHUP_CHANGED",
        "UPGRADE_CATCHUP_CHANGED_VERDICTS",
    ):
        assert run.index(f'echo "{name}=') > run.index('[[ "${old_digest}" =~ ^[0-9a-f]{64}$ ]]'), name


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


# --- The catch-up after the upgrade, and L-30-03 (plan 31-13) ---------------
#
# FMT-06, D-31-02, SC2. "Store upgrade 5" keeps two statements apart that fail
# for opposite reasons (31-RESEARCH pitfall 13): the old stock did not move,
# and the seed of the new formats arrived without an admin doing anything. The
# checkpoint of plan 31-12 was not raised (31-12-SUMMARY), so the seed is the
# full one: seven words, the ZIP bomb and the stale file of the fixed order.

ENV_OF_SEED = {
    "seed-mail.eml": "UPGRADE_SEED_MAIL_ID",
    "seed-archive.zip": "UPGRADE_SEED_ZIP_ID",
    "seed-word.doc": "UPGRADE_SEED_DOC_ID",
    "seed-excel.xls": "UPGRADE_SEED_XLS_ID",
    "seed-photo.heic": "UPGRADE_SEED_HEIC_ID",
    "seed-ole-under-docx.docx": "UPGRADE_SEED_OLE_ID",
    "seed-stale-size.txt": "UPGRADE_SEED_STALE_ID",
}

# The steps whose writes into GITHUB_ENV are held to a pattern first (L-30-03
# of 30-AUDIT, T-31-41).
ENV_STEPS = (SEED_STEP, RECORD_STEP, UPGRADE_STEP, ASSURANCE_STEP, REBUILD_STEP, BACK_STEP)

_ENV_LINE = re.compile(r'^\s*echo "([A-Z0-9_]+)=\$\{([a-z_]+)\}"')
_DIGEST_CALL = re.compile(r'seed_probe digest "([^"]+)"')


def _env_writes(run: str) -> list[tuple[int, str, str]]:
    """Every value a run writes into GITHUB_ENV: (offset, name, shell variable)."""
    writes: list[tuple[int, str, str]] = []
    lines = run.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    for number, line in enumerate(lines):
        if '>> "${GITHUB_ENV}"' not in line:
            continue
        if line.strip().startswith("}"):
            opening = max(index for index in range(number) if lines[index].strip() == "{")
            body = lines[opening + 1 : number]
            start = offsets[opening]
        else:
            body = [line]
            start = offsets[number]
        for entry in body:
            found = _ENV_LINE.match(entry)
            assert found is not None, f"a write into GITHUB_ENV that is not one plain variable: {entry.strip()}"
            writes.append((start, found.group(1), found.group(2)))
    return writes


def _checked_before(run: str, variable: str, before: int) -> bool:
    """Whether ``variable`` is held to a pattern somewhere before ``before``.

    Only ``[[ =~ ]]`` counts, because it holds the whole value; printf piped
    into grep -Eq matched line by line, so "335" plus a second line passed
    (L-31-07 of 31-AUDIT), and it is no longer accepted here.
    """
    head = run[:before]
    if f'[[ "${{{variable}}}" =~ ' in head:
        return True
    # A loop over the values, with the check on the loop variable in its body.
    for loop in re.finditer(r"^\s*for (\w+) in ([^\n]*); do\n(.*?)^\s*done$", head, re.MULTILINE | re.DOTALL):
        name, values, body = loop.group(1), loop.group(2), loop.group(3)
        if f'"${{{variable}}}"' not in values:
            continue
        if f'[[ "${{{name}}}" =~ ' in body:
            return True
    return False


@pytest.mark.parametrize("prefix", ENV_STEPS)
def test_every_value_is_checked_before_it_goes_into_the_environment(prefix: str) -> None:
    # L-30-03: a later step reads these values as shell text, so each one is
    # held to its pattern in the step that writes it, before the write.
    run = _run(prefix)
    for start, name, variable in _env_writes(run):
        assert _checked_before(run, variable, start), f"{prefix} {name}"


def test_the_upgrade_step_checks_the_new_container_and_companion() -> None:
    # Named on purpose: L-30-03 named Store upgrade 4, whose two values went in
    # unchecked until plan 31-13, and the restart count and the end time go in
    # beside them now.
    run = _run(UPGRADE_STEP)
    names = {name: variable for _, name, variable in _env_writes(run)}
    for name in ("UPGRADE_NEW_CONTAINER", "UPGRADE_NEW_COMPANION", "UPGRADE_NEW_RESTARTS", "UPGRADE_FINISHED_AT"):
        assert name in names, name
    assert names["UPGRADE_NEW_CONTAINER"] == "container"
    assert names["UPGRADE_NEW_COMPANION"] == "new_companion"
    assert '[[ "${container}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]]' in run
    assert '[[ "${new_companion}" =~ ${version_pattern} ]]' in run
    assert "restarts=$(docker inspect --format '{{.RestartCount}}' \"${container}\")" in run


def test_the_checker_of_the_environment_sees_a_missing_check() -> None:
    # The negative sample of the two helpers above, so their green means something.
    unchecked = 'x=$(date)\n{\n  echo "UPGRADE_X=${x}"\n} >> "${GITHUB_ENV}"\n'
    start, name, variable = _env_writes(unchecked)[0]
    assert name == "UPGRADE_X"
    assert not _checked_before(unchecked, variable, start)
    checked = (
        'x=$(date)\nif ! [[ "${x}" =~ ^[0-9]+$ ]]; then exit 1; fi\n{\n  echo "UPGRADE_X=${x}"\n} >> "${GITHUB_ENV}"\n'
    )
    start, _, variable = _env_writes(checked)[0]
    assert _checked_before(checked, variable, start)
    looped = 'for value in "${x}"; do\n  if ! [[ "${value}" =~ ^[0-9]+$ ]]; then exit 1; fi\ndone\n'
    start, _, variable = _env_writes(looped + unchecked)[0]
    assert _checked_before(looped + unchecked, variable, start)


def test_the_assurance_step_does_nothing_an_admin_would_do() -> None:
    # SC4: no restart of the index, no scan, no cron run, no container
    # handling and no hand written row anywhere in the step.
    run = _run(ASSURANCE_STEP)
    for forbidden in (
        "--restart",
        "files:scan",
        "cron.php",
        "app_api:",
        "docker stop",
        "docker start",
        "docker restart",
        "docker create",
        "docker rm",
        "UPDATE ",
        "INSERT ",
        "DELETE ",
    ):
        assert forbidden not in run, forbidden
    calls = re.findall(r'"\$\{RUNNER_TEMP\}/nc-occ\.sh" ([^\n]*)', run)
    assert calls
    for call in calls:
        assert call.startswith("findling:index |"), call


def test_the_step_name_counts_its_assurances() -> None:
    assert _named(ASSURANCE_STEP)[0]["name"] == "Store upgrade 5, the ten assurances after the upgrade"
    run = _run(ASSURANCE_STEP)
    for number in range(1, 11):
        assert f'echo "--- {number}, ' in run, number
    assert 'echo "all ten assurances hold"' in run


def test_every_seed_word_finds_exactly_its_file_within_the_budget() -> None:
    module = _formats_generator()
    run = _run(ASSURANCE_STEP)
    words = run[run.index("seed_words=") : run.index("\n", run.index("seed_words="))]
    for name, word in module.SEED_WORDS.items():
        assert f"{word}=${{{ENV_OF_SEED[name]}}}" in words, word
    assert len(words.split()) == len(module.SEED_WORDS)
    exact = "(.ocs.data.entries | length == 1) and .ocs.data.entries[0].attributes.fileId == $id"
    # The wait for the catch-up, the words and the vectors comes before the
    # snapshot, with the one budget of the drain.
    wait = run.index("while :; do")
    snapshot = run.index('snapshot "${RUNNER_TEMP}/upgrade-after.json" after')
    assert run.index("UPGRADE_DRAIN_BUDGET_SECONDS") < wait < run.index(exact) < snapshot
    assert run.count(exact) >= 2
    # The error names the word and the file ids it brought back, never a text.
    seed_part = run[run.index('echo "--- 9, ') :]
    assert "\\(.attributes.fileId)" in seed_part
    assert ".title)" not in seed_part
    assert ".subline)" not in seed_part


def test_the_exact_hit_filter_reads_one_entry_of_the_right_file(tmp_path: Path) -> None:
    # Evaluated and not only found: without the parentheses jq binds "and"
    # inside the pipe and fails on the entry list (seen in the stub run of
    # plan 31-13), which in the step reads as "not exactly its file".
    jq = shutil.which("jq")
    if jq is None:
        pytest.skip("no jq on this machine, the filter cannot be evaluated here")
    run = _run(ASSURANCE_STEP)
    found = re.findall(r"jq -e --arg id \"\$\{pair#\*=\}\" '([^']+)'|jq -e --arg id \"\$\{id\}\" '([^']+)'", run)
    filters = {first or second for first, second in found}
    assert len(filters) == 1
    (expression,) = filters
    answer = tmp_path / "answer.json"
    answer.write_text('{"ocs":{"data":{"entries":[{"attributes":{"fileId":"7"}}]}}}', encoding="utf-8")
    for wanted, code in (("7", 0), ("8", 1)):
        done = subprocess.run(  # noqa: S603 - an argument list, never a shell
            [jq, "-e", "--arg", "id", wanted, expression, str(answer)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert done.returncode == code, (wanted, done.stderr)


def test_the_zip_hit_shows_the_inner_file() -> None:
    run = _run(ASSURANCE_STEP)
    assert '.ocs.data.entries[0].subline | startswith("innen/notiz.txt: ")' in run
    assert "archivquendel=${UPGRADE_SEED_ZIP_ID}" in run


def test_the_seven_files_are_indexed_with_vectors_and_no_verdict_left() -> None:
    run = _run(ASSURANCE_STEP)
    start = run.index('indexed_seed="')
    line = run[start : run.index("\n", start)]
    for name in ENV_OF_SEED.values():
        assert f"${{{name}}}" in line, name
    assert "UPGRADE_SEED_BOMB_ID" not in line
    assert 'if [ "${verdict}" != "indexed/" ] || [ "${recorded}" != "0" ]; then' in run
    assert 'chunks=$(seed_probe chunks "${id}"' in run


def test_the_stale_file_is_indexed_after_the_upgrade() -> None:
    # D-31-02 end to end (31-12 was not option-b): the file 1.4.2 wrote off is
    # indexed, and Nextcloud took its failed verdict back.
    run = _run(ASSURANCE_STEP)
    assert "cachequendel=${UPGRADE_SEED_STALE_ID}" in run
    assert 'stale=$(seed_probe verdict "${UPGRADE_SEED_STALE_ID}"' in run
    assert 'if [ "${stale}" != "indexed/" ] || [ "${stale_recorded}" != "0" ]; then' in run


def test_the_bomb_is_skipped_and_the_container_lives() -> None:
    run = _run(ASSURANCE_STEP)
    bomb = run.index(
        'if [ "${bomb}" != "skipped/archive_limit" ] || [ "${bomb_recorded}" != "skipped/archive_limit" ]; then'
    )
    alive = run.index(
        "alive=$(docker inspect --format '{{.State.Running}} {{.RestartCount}}' \"${UPGRADE_NEW_CONTAINER}\""
    )
    assert 'if [ "${alive}" != "true ${UPGRADE_NEW_RESTARTS}" ]; then' in run
    canary = run.index("term=findling-canary")
    assert bomb < alive < canary


def test_the_catch_up_mark_reads_done_and_the_recheck_mark_stays() -> None:
    from findling.store.repo import CATCHUP_MARK, RECHECK_MARK

    run = _run(ASSURANCE_STEP)
    assert f"seed_probe meta {CATCHUP_MARK}" in run
    assert 'if [ "${catchup}" != "done" ]; then' in run
    assert f"seed_probe meta {RECHECK_MARK}" in run
    assert 'if [ "${recheck}" != "done" ]; then' in run
    # The duration of the catch-up, for the performance audit of 31-15.
    assert "UPGRADE_FINISHED_AT" in run


def test_every_catch_up_candidate_is_held_one_by_one() -> None:
    run = _run(ASSURANCE_STEP)
    same = "for entry in ${UPGRADE_CATCHUP_CANDIDATE_STATES//,/ }; do"
    changed = "for entry in ${UPGRADE_CATCHUP_CHANGED_VERDICTS//,/ }; do"
    for loop in (same, changed):
        start = run.index(loop)
        body = run[start : run.index("\ndone", start)]
        assert 'seed_probe verdict "${entry%%=*}"' in body, loop
        assert "oc_findling_file_state WHERE file_id = ${entry%%=*}" in body, loop
        assert "::error::" in body, loop
    # An empty list is a line of its own and not a silent nothing.
    assert "no catch-up candidate of the old stock keeps its verdict" in run
    assert "no catch-up candidate of the old stock changes its verdict" in run


def test_the_digest_after_the_upgrade_leaves_out_what_3c_left_out() -> None:
    record = _run(RECORD_STEP)
    run = _run(ASSURANCE_STEP)
    start = record.index("seed_ids=")
    assert record[start : record.index("\n", start)] in run
    before = _DIGEST_CALL.findall(record)
    after = _DIGEST_CALL.findall(run)
    assert len(before) == 1
    assert len(after) == 1
    assert after[0] == before[0].replace("expected_changed", "UPGRADE_CATCHUP_CHANGED")
    assert 'if [ "${after_stock%%:*}" != "${UPGRADE_OLD_STOCK_DIGEST}" ]; then' in run
    # The candidates are held before the digest is compared.
    assert run.index("for entry in ${UPGRADE_CATCHUP_CANDIDATE_STATES//,/ }; do") < run.index("seed_probe digest")


def test_the_stock_question_takes_a_list() -> None:
    probe = _run(SEED_STEP)
    part = probe[probe.index('elif question == "stock":') : probe.index('elif question == "rows":')]
    assert 'excluded = {int(part) for part in subject.split(",") if part}' in part
    assert "if row[1] not in excluded" in part


def _probe_source() -> str:
    """The seed-probe.py the run of "Store upgrade 2b" writes, dedented."""
    run = _run(SEED_STEP)
    start = run.index("cat > \"${RUNNER_TEMP}/seed-probe.py\" <<'PY'\n") + len(
        "cat > \"${RUNNER_TEMP}/seed-probe.py\" <<'PY'\n"
    )
    return run[start : run.index("\nPY\n", start)] + "\n"


def test_the_probe_answers_the_reconcile_question_without_a_subject(tmp_path: Path) -> None:
    # Run 38250670039 (plan 31-13): "seed_probe reconcile" is asked with one
    # argument, and a probe that read sys.argv[2] for every question failed
    # with IndexError on each round, so the wait for the first reconcile cycle
    # of 1.4.2 read "unreadable" until its budget ran out. Executed here
    # against a state.db with the reconcile table of v1.4.2
    # (store/repo.py:548-569 of the tag), both answers.
    import sqlite3
    import sys

    probe = tmp_path / "seed-probe.py"
    probe.write_text(_probe_source(), encoding="utf-8")
    database = tmp_path / "state.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE reconcile (storage_id INTEGER PRIMARY KEY, after_file_id INTEGER NOT NULL,"
            " started_at REAL, finished_at REAL)"
        )
        connection.execute("INSERT INTO reconcile VALUES (1, 17, 1.0, NULL)")
    environment = {**__import__("os").environ, "APP_PERSISTENT_STORAGE": str(tmp_path)}

    def ask() -> str:
        done = subprocess.run(  # noqa: S603 - an argument list, never a shell
            [sys.executable, str(probe), "reconcile"],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
        assert done.returncode == 0, done.stderr
        return done.stdout.strip()

    assert ask() == "open"
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE reconcile SET after_file_id = 0, finished_at = 2.0")
    assert ask() == "done"


def test_the_probe_answers_every_question_of_3c_and_5(tmp_path: Path) -> None:
    # Every question "Store upgrade 3c" and "Store upgrade 5" ask, executed
    # against databases built from store/schema.sql and the chunks table of
    # store/vectors.sql (both unchanged since v1.4.2: git diff v1.4.2 HEAD of
    # the two files is empty), so a broken question shows here and not an
    # hour into deploy-harp.
    import os
    import sqlite3
    import sys

    store = REPO_ROOT / "backend" / "src" / "findling" / "store"
    probe = tmp_path / "seed-probe.py"
    probe.write_text(_probe_source(), encoding="utf-8")
    with sqlite3.connect(tmp_path / "state.db") as connection:
        connection.executescript((store / "schema.sql").read_text(encoding="utf-8"))
        rows = (
            (1, "/a.txt", "text/plain", "indexed", None, "e1"),
            (2, "/b.docx", "", "skipped", "legacy_format", "e2"),
            (3, "/c.pptx", "", "skipped", "legacy_format", "e3"),
            (4, "/d.txt", "text/plain", "failed", "repeatedly_stuck", "e4"),
            (5, "/e.eml", "message/rfc822", "skipped", "mime_not_allowed", "e5"),
        )
        for file_id, path, mime, state, reason, etag in rows:
            connection.execute(
                "INSERT INTO files (file_id, storage_id, root_id, path, mime, size, mtime, etag, state, reason)"
                " VALUES (?, 1, 1, ?, ?, 10, 1, ?, ?, ?)",
                (file_id, path, mime, etag, state, reason),
            )
        connection.execute("INSERT INTO meta VALUES ('recheck_1_4_0', 'done')")
    vectors = (store / "vectors.sql").read_text(encoding="utf-8")
    chunks = vectors[vectors.index("CREATE TABLE IF NOT EXISTS chunks") :]
    with sqlite3.connect(tmp_path / "vectors.db") as connection:
        connection.execute(chunks[: chunks.index(");") + 2])
        connection.executemany(
            "INSERT INTO chunks VALUES (?, ?, 0, 0, 5)",
            ((1, 1), (2, 1), (3, 4), (4, 9)),
        )
    environment = {**os.environ, "APP_PERSISTENT_STORAGE": str(tmp_path)}

    def ask(*arguments: str) -> str:
        done = subprocess.run(  # noqa: S603 - an argument list, never a shell
            [sys.executable, str(probe), *arguments],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
        assert done.returncode == 0, (arguments, done.stderr)
        return done.stdout.strip()

    assert ask("verdict", "1") == "indexed/"
    assert ask("verdict", "2") == "skipped/legacy_format"
    assert ask("verdict", "8") == "none"
    assert ask("meta", "recheck_1_4_0") == "done"
    assert ask("meta", "recheck_1_5_0") == "absent"
    assert ask("chunks", "1") == "2"
    assert ask("rows", "4") == "1"
    # Part A: legacy_format without PowerPoint, the new type, the written off.
    assert ask("catchup", "0").split() == [
        "2=skipped/legacy_format",
        "4=failed/repeatedly_stuck",
        "5=skipped/mime_not_allowed",
    ]
    assert ask("catchup", "2,5").split() == ["4=failed/repeatedly_stuck"]
    whole = ask("stock", "0")
    assert whole.endswith(":3:4")
    assert ask("stock", "9").endswith(":2:3")
    assert ask("stock", "4,9").endswith(":1:2")
    assert ask("stock", "4,9") != ask("stock", "4")
    digest = ask("digest", "4,5")
    assert re.fullmatch(r"[0-9a-f]{64}:3", digest)
    assert ask("digest", "") != digest


# ---------------------------------------------------------------------------
# The exclusions of the upgrade line (plan 36-10, finding F5 of the phase 36
# research). "Store upgrade 2b" writes a prefix in the shape of the released
# version before it uploads anything, so the listener of the tag refuses the
# file under it; a control and a pattern file are indexed beside it.

EXCLUSION_PREFIX = "Ausschluss36"


def _exclusion_block() -> str:
    """The part of "Store upgrade 2b" from the seed of the exclusions on."""
    run = _run(SEED_STEP)
    return run[run.index("The seed of the exclusions (plan 36-10") :]


def test_the_exclusion_seed_writes_the_prefix_of_the_tag_before_any_upload() -> None:
    block = _exclusion_block()
    write = block.index(
        '"${RUNNER_TEMP}/nc-occ.sh" config:app:set findling exclusions --value="[\\"${excl_folder}\\"]" --type=array'
    )
    assert f"excl_folder={EXCLUSION_PREFIX}" in block
    assert write < block.index("-X MKCOL") < block.index('excl_upload "${RUNNER_TEMP}/excl-a.txt"')
    # The shape is read out of the tag, and the comment says where: prefixes()
    # of v1.5.0 reads the key exclusions with getValueArray and names occ as
    # the documented second writer, exactly as 1.4.2 did.
    assert "v1.5.0:php/lib/Service/ExclusionService.php:236" in block


def test_the_exclusion_seed_is_judged_fail_closed_under_the_tag() -> None:
    block = _exclusion_block()
    assert 'if [ "${excluded_rows}" != "0" ] || [ "${excluded_recorded}" != "0:0" ]; then' in block
    assert 'if [ "${hits_excluded}:${control_ok}:${pattern_ok}" = "0:true:true" ]; then' in block
    assert "0:indexed/:indexed/:[1-9]*:[1-9]*)" in block


def test_the_exclusion_seed_exports_the_list_and_the_three_ids() -> None:
    names = {name: variable for _, name, variable in _env_writes(_exclusion_block())}
    assert names == {
        "UPGRADE_EXCLUSIONS_BEFORE": "exclusions_before",
        "UPGRADE_EXCL_EXCLUDED_ID": "excluded_id",
        "UPGRADE_EXCL_CONTROL_ID": "control_id",
        "UPGRADE_EXCL_PATTERN_ID": "pattern_id",
    }


EXCLUSION_STEP = "Store upgrade 5b,"


def test_the_exclusion_step_stands_once_between_the_assurances_and_the_rebuild() -> None:
    names = [str(step.get("name", "")) for step in _steps()]
    found = [index for index, name in enumerate(names) if name.startswith(EXCLUSION_STEP)]
    assert len(found) == 1
    assert names[found[0] - 1].startswith(ASSURANCE_STEP)
    assert names[found[0] + 1].startswith(REBUILD_STEP)
    assert _named(EXCLUSION_STEP)[0]["if"] == _named(ASSURANCE_STEP)[0]["if"]


def test_the_exclusion_step_asks_the_words_and_the_list_of_the_seed() -> None:
    seed = _exclusion_block()
    run = _run(EXCLUSION_STEP)
    for variable in ("excl_word", "control_word", "pattern_word"):
        line = re.search(rf"^{variable}=([a-z]+)$", seed, re.MULTILINE)
        assert line is not None, variable
        assert f"{variable}={line.group(1)}\n" in run, variable
    assert 'if [ "${exclusions_after}" != "${UPGRADE_EXCLUSIONS_BEFORE}" ]; then' in run
    for name in ("UPGRADE_EXCL_EXCLUDED_ID", "UPGRADE_EXCL_CONTROL_ID", "UPGRADE_EXCL_PATTERN_ID"):
        assert f"${{{name}}}" in run, name


def test_the_exclusion_step_sets_the_pattern_runs_a_cycle_and_takes_it_back() -> None:
    run = _run(EXCLUSION_STEP)
    passive = run.index('echo "--- 11a, ')
    listed = run.index('echo "--- 11b, ')
    written = run.index('config:app:set findling exclusion_patterns --value="[\\"${excl_pattern}\\"]" --type=array')
    first = run.index('one_cycle "pattern set"')
    gone = run.index('if [ "${open}:${patterned}" = "0:none" ] && finds_nothing "${pattern_word}"; then')
    deleted = run.index('"${RUNNER_TEMP}/nc-occ.sh" config:app:delete findling exclusion_patterns')
    second = run.index('one_cycle "pattern taken back"')
    assert passive < listed < written < first < gone < deleted < second
    assert "Reconcile(min_interval_hours=0).run_once()" in run
    assert '.state == "walked" and .stale >= 1' in run
    # The file comes back with its vectors before the rebuild steps run.
    assert "0:indexed/:[1-9]*)" in run[second:]


def test_the_exclusion_step_writes_nothing_into_the_environment_or_a_table() -> None:
    run = _run(EXCLUSION_STEP)
    assert "GITHUB_ENV" not in run
    for forbidden in ("UPDATE ", "INSERT ", "DELETE ", "--restart", "cron.php", "docker restart", "docker stop"):
        assert forbidden not in run, forbidden
    assert "${{" not in run


def test_the_exclusion_step_parses_in_bash(tmp_path: Path) -> None:
    done = _bash_parses(_run(EXCLUSION_STEP), tmp_path)
    assert done.returncode == 0, done.stderr


def test_the_exclusion_seed_parses_in_bash(tmp_path: Path) -> None:
    done = _bash_parses(_run(SEED_STEP), tmp_path)
    assert done.returncode == 0, done.stderr
