"""The gate over the certificate rotation probe of ``deploy-harp.yml`` and its doc.

ZERT-02 after owner decision D-37-09 asks for proof that a reissued HaRP CA is
survived without unregister and register: HaRP really issues a new CA "harp.nc"
in CI, the tunnel is shown dead without new files (the positive control), the
three files are copied into the running backend container, and the canary search
answers again without a re-register and without a container restart.

That proof is carried by one step, and the statement it makes depends on that
step having no ``if:``. The matrix has four legs, arm64 among them, and a
condition copied over from the gated store upgrade steps would leave a green run
that proves the rotation on one leg out of four. So the absence of the condition
is asserted here, and "Store upgrade 5, the ten assurances after the upgrade" is
read as the counter sample: if the scanner could not see that step's ``if:``, it
could not see one on the probe either, and that finding says "this gate is
broken" rather than "the workflow is broken".

What else is held:

1. The step stands exactly once, right after "Search over the ordinary OCS
   route" (a fresh installation with a healthy tunnel) and right before the
   language proof (every later step builds on a healed tunnel).
2. Its run block names the commands that make the proof a proof: the real
   reissue (``rm -rf /certs/frp`` in HaRP plus a restart), the CA digest before
   and after, the restart count and start time of the backend container, the
   log lines of the watcher of plan 38-01, the copy through ``docker exec -i``
   into a temporary name moved over with ``mv -f`` under ``umask 077``, the
   canary search and the app list.
3. Outside comment lines the run block never copies with ``docker cp`` (the
   files would belong to root and client.key would be unreadable for the app
   user), never re-registers and never restarts the backend container. Each of
   those would make the probe green for a reason that is not the claim.
4. The run block parses in bash.

And about the admin doc the remedy line of ``harp_connect.sh`` points to: the
anchor in that line exists as a heading of ``docs/harp-tunnel.md``, the doc has
its seven sections, and its copy command has the same shape as the probe. Every
test about the doc carries ``doc`` in its name and no test about the step does,
so ``-k "not doc"`` selects the step half alone.

**Why text and not a YAML parser.** As in ``test_language_proof_steps.py``: the
backend has no yaml dependency. The scanner relies on six spaces for a step and
eight for its keys, and a source in which it finds no step is a finding.

**The gate falls closed.** A missing workflow, a renamed step or a missing doc
costs one finding per statement it silences, never zero.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy-harp.yml"
HARP_CONNECT = REPO_ROOT / "backend" / "docker" / "harp_connect.sh"
HARP_DOC = REPO_ROOT / "docs" / "harp-tunnel.md"

STEP = "Certificate rotation, a reissued HaRP CA heals after the three files are copied in"
BEFORE = "Search over the ordinary OCS route"
AFTER = "Language proof, the four new chains answer on the ordinary search route"
COUNTER_SAMPLE = "Store upgrade 5, the ten assurances after the upgrade"

REQUIRED_SNIPPETS = (
    "docker exec appapi-harp rm -rf /certs/frp",
    "docker restart appapi-harp",
    "_ping",
    "sha256sum /certs/frp/ca.crt",
    "RestartCount",
    "StartedAt",
    "docker logs --since",
    "x509: ",
    "no longer accepted by HaRP (x509)",
    "the certificate files in",
    "login to server success",
    "docker exec -i",
    "mv -f",
    "umask 077",
    "findling-canary",
    "app_api:app:list",
    "rotation-dead.code",
    "seq 1 90",
)

FORBIDDEN_SNIPPETS = (
    "docker cp",
    "app_api:app:register",
    "app_api:app:unregister",
    'docker restart "${EXAPP_CONTAINER}"',
)

ANCHOR = "docs/harp-tunnel.md#repair-without-re-registering"
REPAIR_HEADING = "## Repair without re-registering"
DOC_HEADINGS = (
    "## Cause",
    "## Recognising it",
    "## Prevention",
    REPAIR_HEADING,
    "## Fallback: re-register without --rm-data",
    "## Limits",
    "## Proof",
)
DOC_COPY_SNIPPETS = (
    "docker exec -i nc_app_findling_backend",
    "umask 077",
    "mv -f",
    "ca.crt",
    "client.crt",
    "client.key",
)

_STEP_START = re.compile(r"^ {6}- name:[ \t]*(?P<name>.+?)[ \t]*$")
_STEP_END = re.compile(r"^ {0,6}(?:#|- name:|[A-Za-z0-9_.-]+:)")
_STEP_IF = re.compile(r"^ {8}if:[ \t]*\S", re.MULTILINE)
_RUN_KEY = re.compile(r"^ {8}run:[ \t]*\|[ \t]*$")

CLAIMS = (
    "the rotation step carries no if: condition",
    "the rotation step stands right after the canary search and right before the language proof",
    "the rotation step names every command its proof rests on",
    "the rotation step neither copies with docker cp nor re-registers nor restarts the backend container",
)
DOC_CLAIMS = (
    "the doc carries every section",
    "the doc carries the repair heading exactly once",
    "the doc copies the three files the way the probe does",
    "the doc mentions docker cp only to advise against it",
)


class Step(NamedTuple):
    """One step of a workflow job, reduced to what the claims above need."""

    name: str
    line: int
    body: str


def collect_steps(source: str) -> list[Step]:
    """Every step of the source, in file order, each with its own body."""
    lines = source.splitlines()
    starts: list[tuple[int, str]] = []
    for number, line in enumerate(lines):
        found = _STEP_START.match(line)
        if found is not None:
            starts.append((number, found.group("name")))

    steps: list[Step] = []
    for index, (number, name) in enumerate(starts):
        end = len(lines)
        for candidate in range(number + 1, len(lines)):
            if _STEP_END.match(lines[candidate]):
                end = candidate
                break
        if index + 1 < len(starts):
            end = min(end, starts[index + 1][0])
        steps.append(Step(name, number + 1, "\n".join(lines[number:end])))
    return steps


def run_block(step: Step) -> str:
    """The run block of a step, with the indentation of the block removed."""
    lines = step.body.splitlines()
    for number, line in enumerate(lines):
        if _RUN_KEY.match(line):
            block = lines[number + 1 :]
            indents = [len(item) - len(item.lstrip(" ")) for item in block if item.strip()]
            if not indents:
                return ""
            cut = min(indents)
            return "\n".join(item[cut:] for item in block) + "\n"
    return ""


def code_lines(run: str) -> list[str]:
    """The lines of a run block that are not comments."""
    return [line for line in run.splitlines() if not line.lstrip().startswith("#")]


def _named(steps: list[Step], name: str) -> list[Step]:
    return [step for step in steps if step.name == name]


def scan_counter_sample(steps: list[Step]) -> list[str]:
    """The gated step still carries its condition, so the scanner can see one."""
    found = _named(steps, COUNTER_SAMPLE)
    if not found:
        return [
            (
                f"the counter sample '{COUNTER_SAMPLE}' is not in the file any more, "
                "so this gate can no longer show that it is able to see a condition"
            )
        ]
    if any(_STEP_IF.search(step.body) is None for step in found):
        return [
            (
                f"the counter sample '{COUNTER_SAMPLE}' carries no if:, "
                "so this gate is broken and would pass an ungated probe for the wrong reason"
            )
        ]
    return []


def scan_rotation_step(steps: list[Step]) -> list[str]:
    """Every claim about the probe. Fail closed: a missing step costs one finding per claim."""
    found = _named(steps, STEP)
    if len(found) != 1:
        return [
            f"the step '{STEP}' stands {len(found)} times in the workflow and not once",
            *(f"unchecked, because the step is not there: {claim}" for claim in CLAIMS),
        ]
    step = found[0]
    findings: list[str] = []
    if _STEP_IF.search(step.body) is not None:
        findings.append(
            f"the step '{STEP}' carries an if: at line {step.line}, so the rotation is proven on part of "
            "the matrix only and D-37-09 asks for every leg, arm64 included"
        )
    names = [item.name for item in steps]
    index = names.index(STEP)
    if index == 0 or names[index - 1] != BEFORE or index + 1 >= len(names) or names[index + 1] != AFTER:
        findings.append(f"the step '{STEP}' does not stand between '{BEFORE}' and '{AFTER}'")
    run = run_block(step)
    findings.extend(
        f"the step '{STEP}' does not contain '{snippet}'" for snippet in REQUIRED_SNIPPETS if snippet not in run
    )
    code = "\n".join(code_lines(run))
    findings.extend(
        f"the step '{STEP}' contains '{snippet}' outside a comment, so it could heal for a reason that is not the claim"
        for snippet in FORBIDDEN_SNIPPETS
        if snippet in code
    )
    return findings


def scan(source: str) -> list[str]:
    """Every finding of the step half of this gate over one workflow source."""
    steps = collect_steps(source)
    if not steps:
        return [
            "the scanner found no step at all in this source, so its indentation assumption no longer holds",
            *(f"unchecked, because no step was found: {claim}" for claim in CLAIMS),
        ]
    return [*scan_rotation_step(steps), *scan_counter_sample(steps)]


def scan_doc(text: str | None) -> list[str]:
    """Every claim about docs/harp-tunnel.md. Fail closed on a missing file."""
    if text is None:
        return [
            "docs/harp-tunnel.md is not there, so the remedy line of harp_connect.sh points nowhere",
            *(f"unchecked, because the doc is not there: {claim}" for claim in DOC_CLAIMS),
        ]
    lines = text.splitlines()
    findings = [f"the doc has no heading '{heading}'" for heading in DOC_HEADINGS if heading not in lines]
    repairs = lines.count(REPAIR_HEADING)
    if repairs != 1:
        findings.append(f"the doc carries '{REPAIR_HEADING}' {repairs} times and not once, so the anchor is ambiguous")
    findings.extend(
        f"the copy command of the doc does not contain '{snippet}'"
        for snippet in DOC_COPY_SNIPPETS
        if snippet not in text
    )
    findings.extend(
        f"the doc mentions docker cp without advising against it: {line.strip()}"
        for line in lines
        if "docker cp" in line and "not" not in line.lower()
    )
    return findings


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


def _real_steps() -> list[Step]:
    return collect_steps(WORKFLOW.read_text(encoding="utf-8"))


def _real_doc() -> str | None:
    return HARP_DOC.read_text(encoding="utf-8") if HARP_DOC.is_file() else None


# -- the real tree, the step half -----------------------------------------


def test_the_workflow_is_there_and_the_scanner_can_read_it() -> None:
    assert WORKFLOW.is_file()
    steps = _real_steps()
    assert len(steps) >= 40
    assert _named(steps, BEFORE)
    assert _named(steps, AFTER)


def test_the_rotation_step_stands_exactly_once() -> None:
    assert len(_named(_real_steps(), STEP)) == 1


def test_the_rotation_step_carries_no_condition() -> None:
    found = _named(_real_steps(), STEP)
    assert len(found) == 1
    assert _STEP_IF.search(found[0].body) is None


def test_the_counter_sample_still_carries_its_condition() -> None:
    assert scan_counter_sample(_real_steps()) == []


def test_the_rotation_step_stands_after_the_canary_search_and_before_the_language_proof() -> None:
    names = [step.name for step in _real_steps()]
    assert STEP in names
    index = names.index(STEP)
    assert names[index - 1] == BEFORE
    assert names[index + 1] == AFTER


def test_the_rotation_step_names_every_command_of_its_proof() -> None:
    found = _named(_real_steps(), STEP)
    assert len(found) == 1
    run = run_block(found[0])
    assert [snippet for snippet in REQUIRED_SNIPPETS if snippet not in run] == []


def test_the_rotation_step_never_takes_a_shortcut() -> None:
    found = _named(_real_steps(), STEP)
    assert len(found) == 1
    code = "\n".join(code_lines(run_block(found[0])))
    assert [snippet for snippet in FORBIDDEN_SNIPPETS if snippet in code] == []


def test_the_rotation_step_parses_in_bash(tmp_path: Path) -> None:
    found = _named(_real_steps(), STEP)
    assert len(found) == 1
    answer = _bash_parses(run_block(found[0]), tmp_path)
    assert answer.returncode == 0, answer.stderr


def test_the_real_workflow_produces_no_finding() -> None:
    assert scan(WORKFLOW.read_text(encoding="utf-8")) == []


# -- the real tree, the doc half ------------------------------------------


def test_doc_anchor_stands_in_the_remedy_line() -> None:
    remedy = [line for line in HARP_CONNECT.read_text(encoding="utf-8").splitlines() if "(x509)" in line]
    assert remedy
    assert all(ANCHOR in line for line in remedy)


def test_doc_anchor_is_the_slug_of_the_repair_heading() -> None:
    slug = REPAIR_HEADING.removeprefix("## ").lower().replace(" ", "-")
    assert ANCHOR.endswith(f"#{slug}")


def test_doc_exists_with_every_section() -> None:
    text = _real_doc()
    assert text is not None
    lines = text.splitlines()
    assert [heading for heading in DOC_HEADINGS if heading not in lines] == []
    assert lines.count(REPAIR_HEADING) == 1


def test_doc_copy_command_has_the_shape_of_the_probe() -> None:
    text = _real_doc()
    assert text is not None
    assert [snippet for snippet in DOC_COPY_SNIPPETS if snippet not in text] == []


def test_doc_mentions_docker_cp_only_to_advise_against_it() -> None:
    text = _real_doc()
    assert text is not None
    assert [line for line in text.splitlines() if "docker cp" in line and "not" not in line.lower()] == []


def test_doc_produces_no_finding() -> None:
    assert scan_doc(_real_doc()) == []


# -- self tests: every claim has to be able to go red -----------------------

_CLEAN = """name: Sample

jobs:
  deploy-harp:
    steps:
      - name: Search over the ordinary OCS route
        run: |
          curl 'http://localhost:8080/ocs/v2.php/search/providers/findling/search?term=findling-canary'

      # A comment block between the steps.
      - name: Certificate rotation, a reissued HaRP CA heals after the three files are copied in
        timeout-minutes: 10
        run: |
          # never docker cp, never app_api:app:register
          restarts_before=$(docker inspect --format '{{.RestartCount}}' "${EXAPP_CONTAINER}")
          started_before=$(docker inspect --format '{{.State.StartedAt}}' "${EXAPP_CONTAINER}")
          ca_before=$(docker exec appapi-harp sha256sum /certs/frp/ca.crt | cut -d' ' -f1)
          timeout 30 ./occ app_api:app:list
          docker exec appapi-harp rm -rf /certs/frp
          docker restart appapi-harp
          curl http://localhost:8780/exapps/app_api/v1.44/_ping
          for _ in $(seq 1 90); do
            docker logs --since "${rotated}" "${EXAPP_CONTAINER}" 2>&1 | grep -c 'x509: '
          done
          echo > rotation-dead.code
          grep -c 'no longer accepted by HaRP (x509)' log.txt
          grep -c 'the certificate files in' log.txt
          grep -c 'login to server success' log.txt
          docker exec appapi-harp cat /certs/frp/ca.crt \\
            | docker exec -i "${EXAPP_CONTAINER}" sh -c 'umask 077; cat > /certs/frp/.n && mv -f /certs/frp/.n x'
          echo findling-canary

      - name: Language proof, the four new chains answer on the ordinary search route
        run: |
          echo proof

      - name: Store upgrade 5, the ten assurances after the upgrade
        if: matrix.server-version == 'stable34'
        run: |
          echo gated
"""

_STEP_LINE = f"      - name: {STEP}\n"
_CANARY = "          echo findling-canary\n"


def test_the_clean_sample_is_clean() -> None:
    assert collect_steps(_CLEAN) != []
    assert scan(_CLEAN) == []


def test_the_clean_run_block_parses_in_bash(tmp_path: Path) -> None:
    answer = _bash_parses(run_block(_named(collect_steps(_CLEAN), STEP)[0]), tmp_path)
    assert answer.returncode == 0, answer.stderr


def test_a_condition_on_the_rotation_step_is_reported() -> None:
    source = _CLEAN.replace(_STEP_LINE, _STEP_LINE + "        if: matrix.runner == 'ubuntu-24.04'\n", 1)
    assert source != _CLEAN
    findings = scan(source)
    assert len(findings) == 1
    assert "carries an if:" in findings[0]


def test_a_counter_sample_without_its_condition_is_reported() -> None:
    source = _CLEAN.replace("        if: matrix.server-version == 'stable34'\n", "", 1)
    assert source != _CLEAN
    findings = scan(source)
    assert len(findings) == 1
    assert "this gate is broken" in findings[0]


def test_a_missing_rotation_step_costs_one_finding_per_claim() -> None:
    source = _CLEAN.replace(STEP, "Certificate rotation, something else", 1)
    findings = scan(source)
    assert len(findings) == len(CLAIMS) + 1
    assert all(finding.startswith("unchecked, because the step is not there:") for finding in findings[1:])


def test_a_source_without_any_step_falls_closed() -> None:
    findings = scan("name: Sample\n")
    assert len(findings) == len(CLAIMS) + 1
    assert findings[0].startswith("the scanner found no step at all")


def test_a_rotation_step_in_the_wrong_place_is_reported() -> None:
    source = _CLEAN.replace("      - name: Search over the ordinary OCS route\n", "      - name: Some other step\n", 1)
    assert source != _CLEAN
    findings = scan(source)
    assert len(findings) == 1
    assert "does not stand between" in findings[0]


def test_a_missing_reissue_is_reported() -> None:
    source = _CLEAN.replace("          docker exec appapi-harp rm -rf /certs/frp\n", "", 1)
    assert source != _CLEAN
    findings = scan(source)
    assert findings == [f"the step '{STEP}' does not contain 'docker exec appapi-harp rm -rf /certs/frp'"]


def test_a_copy_with_cp_in_code_is_reported() -> None:
    source = _CLEAN.replace(_CANARY, _CANARY + "          docker cp a b\n", 1)
    assert source != _CLEAN
    findings = scan(source)
    assert len(findings) == 1
    assert "'docker cp' outside a comment" in findings[0]


def test_a_re_register_or_a_backend_restart_in_code_is_reported() -> None:
    shortcuts = '          ./occ app_api:app:register x\n          docker restart "${EXAPP_CONTAINER}"\n'
    source = _CLEAN.replace(_CANARY, _CANARY + shortcuts, 1)
    assert source != _CLEAN
    findings = scan(source)
    assert len(findings) == 2


def test_the_forbidden_words_in_a_comment_are_not_reported() -> None:
    # The clean sample carries "docker cp" and "app_api:app:register" in its
    # comment line; this asserts the filter that lets it stay clean.
    run = run_block(_named(collect_steps(_CLEAN), STEP)[0])
    assert "docker cp" in run
    assert "docker cp" not in "\n".join(code_lines(run))


# -- self tests of the doc half --------------------------------------------

_CLEAN_DOC = """# HaRP tunnel certificates

## Cause
## Recognising it
## Prevention
## Repair without re-registering
for f in ca.crt client.crt client.key; do
  docker exec HARP cat "/certs/frp/$f" | docker exec -i nc_app_findling_backend sh -c 'umask 077; cat > x && mv -f x y'
done
Do not use docker cp.
## Fallback: re-register without --rm-data
## Limits
## Proof
"""


def test_doc_clean_sample_is_clean() -> None:
    assert scan_doc(_CLEAN_DOC) == []


def test_doc_missing_file_falls_closed() -> None:
    findings = scan_doc(None)
    assert len(findings) == len(DOC_CLAIMS) + 1


def test_doc_second_repair_heading_is_reported() -> None:
    findings = scan_doc(_CLEAN_DOC + REPAIR_HEADING + "\n")
    assert len(findings) == 1
    assert "2 times" in findings[0]


def test_doc_recommending_docker_cp_is_reported() -> None:
    findings = scan_doc(_CLEAN_DOC + "Run docker cp HARP:/certs/frp/ca.crt .\n")
    assert len(findings) == 1
    assert "without advising against it" in findings[0]


def test_doc_missing_section_is_reported() -> None:
    findings = scan_doc(_CLEAN_DOC.replace("## Limits\n", "", 1))
    assert findings == ["the doc has no heading '## Limits'"]
