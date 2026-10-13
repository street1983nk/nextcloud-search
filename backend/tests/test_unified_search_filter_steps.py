"""The gate over the unified search filter step of ``.github/workflows/deploy-harp.yml``.

Plan 32-06 puts the three success criteria of phase 32 on a real Nextcloud, on
every leg of the matrix: NC 33, 34 and 35 on amd64 and NC 34 on arm64. PHPUnit
runs against stable34 only (32-RESEARCH pitfall 7), so the mechanics the core
supplies around the filters (FilterDefinition, StringFilter, the HTTP 400 for
an empty value) are proved on the other two branches by this step and by no
other. That statement is carried by one thing: the step has no ``if:``. The
reason is the one ``test_language_proof_steps.py`` gives at length, and this
module reuses its step scanner rather than writing a second one.

What the step has to carry, one claim per line of ``CLAIMS``:

1. It stands exactly once, after the language proof and before the drift probe,
   because the drift probe redeploys the container and the language proof is
   the step whose cleanup this one mirrors.
2. It carries no ``if:``.
3. It reads the filter map of the provider list and asks for ``types`` and
   ``folder`` as strings.
4. It asks every positive probe: ``types=pdf``, ``types=text``, the seed folder
   and its sub folder, and a date next to a type and next to a folder.
5. It asks every manipulated value of criterion 3 and compares it with the
   search without a filter: an unknown group, an overlong value, a folder that
   does not exist, one with ``..``, one that is a file, the root and a doubled
   slash.
6. It asks both empty values and expects HTTP 400 from the core (D-32-01).
7. It sows the seed PDF of the repository and takes the seed away again.

The gate falls closed: a step that cannot be found costs one finding per claim.
Every claim has a staged sample that makes it fire.
"""

from __future__ import annotations

import re

from test_language_proof_steps import WORKFLOW, Step, collect_steps

STEP = "Unified search filters, type and folder on the ordinary search route"
BEFORE = "Language proof, the four new chains answer on the ordinary search route"
AFTER = "The drift probe both directions share"

# A step key at eight spaces, the same shape the language proof gate reads.
_STEP_IF = re.compile(r"^ {8}if:[ \t]*\S", re.MULTILINE)

FILTER_MAP = ('.filters.types == "string"', '.filters.folder == "string"')
PROVIDER_LIST = "/ocs/v2.php/search/providers'"
POSITIVE = (
    "'types=pdf'",
    "'types=text'",
    "'folder=/Filterprobe32'",
    "'folder=/Filterprobe32/Innen'",
    '"since=${before}"',
    '"until=${before}"',
    '"since=${after}"',
)
FAIL_OPEN = (
    "'types=videos'",
    "'types=pdf,videos'",
    "seq 1 5000",
    "'folder=/gibtsnicht'",
    "'folder=/../../'",
    "'folder=/Filterprobe32/Oben.txt'",
    "'folder=/'",
    "'folder=//'",
)
REFUSED = ("refused empty-types 'types='", "refused empty-folder 'folder='")
REFUSED_STATUS = '!= "400"'
SEED = ("findling-src/testdata/corpus/01-text-layer.pdf", "-X DELETE")

CLAIMS = (
    "the step stands once between the language proof and the drift probe",
    "the step carries no if: condition",
    "the step reads the filter map",
    "the step asks every positive probe",
    "the step asks every manipulated value",
    "the step asks both empty values and expects HTTP 400",
    "the step sows the seed PDF and takes the seed away again",
)


def _index(steps: list[Step], name: str) -> list[int]:
    return [number for number, step in enumerate(steps) if step.name == name]


def scan(source: str) -> list[str]:
    """Every finding of this gate over one workflow source."""
    steps = collect_steps(source)
    found = _index(steps, STEP)
    if len(found) != 1:
        return [
            f"the step '{STEP}' stands {len(found)} times and not once",
            *(f"unchecked, because the step is not there: {claim}" for claim in CLAIMS[1:]),
        ]

    findings: list[str] = []
    here = found[0]
    before, after = _index(steps, BEFORE), _index(steps, AFTER)
    if len(before) != 1 or len(after) != 1 or not before[0] < here < after[0]:
        findings.append(f"the step does not stand between '{BEFORE}' and '{AFTER}'")

    body = steps[here].body
    if _STEP_IF.search(body) is not None:
        findings.append(f"the step carries an if: at line {steps[here].line}, so it runs on part of the matrix")
    missing = [part for part in (PROVIDER_LIST, *FILTER_MAP) if part not in body]
    if missing:
        findings.append(f"the step does not read the filter map: {missing}")
    missing = [part for part in POSITIVE if part not in body]
    if missing:
        findings.append(f"the step lacks the positive probes {missing}")
    missing = [part for part in FAIL_OPEN if part not in body]
    if missing:
        findings.append(f"the step lacks the manipulated values {missing}")
    missing = [part for part in (*REFUSED, REFUSED_STATUS) if part not in body]
    if missing:
        findings.append(f"the step lacks the HTTP 400 probe of D-32-01: {missing}")
    missing = [part for part in SEED if part not in body]
    if missing:
        findings.append(f"the step does not sow or remove its seed: {missing}")
    return findings


# -- the real tree ---------------------------------------------------------


def test_the_real_workflow_produces_no_finding_at_all() -> None:
    assert WORKFLOW.is_file()
    assert scan(WORKFLOW.read_text(encoding="utf-8")) == []


def test_the_step_carries_no_condition() -> None:
    steps = collect_steps(WORKFLOW.read_text(encoding="utf-8"))
    (here,) = _index(steps, STEP)

    assert _STEP_IF.search(steps[here].body) is None


# -- self tests: every claim has to be able to go red -----------------------

_CLEAN = """name: Sample

jobs:
  deploy-harp:
    steps:
      - name: Language proof, the four new chains answer on the ordinary search route
        run: |
          echo proof

      - name: Unified search filters, type and folder on the ordinary search route
        run: |
          curl 'http://localhost:8080/ocs/v2.php/search/providers'
          jq -e '.filters.types == "string" and .filters.folder == "string"' providers.json
          upload findling-src/testdata/corpus/01-text-layer.pdf Filterprobe32/Bericht.pdf
          probe pdf "${id_pdf}" pdf 'types=pdf'
          probe text "${id_txt}" text 'types=text'
          probe folder "${id_txt}" none 'folder=/Filterprobe32'
          probe inner "${id_md}" none 'folder=/Filterprobe32/Innen'
          probe pdf-since "${id_pdf}" pdf 'types=pdf' "since=${before}"
          probe pdf-until "" pdf 'types=pdf' "until=${before}"
          probe folder-future "" none 'folder=/Filterprobe32' "since=${after}"
          same unknown 'types=videos'
          same mixed 'types=pdf,videos'
          same long "types=$(printf 'a%.0s' $(seq 1 5000))"
          same missing 'folder=/gibtsnicht'
          same dots 'folder=/../../'
          same file 'folder=/Filterprobe32/Oben.txt'
          same root 'folder=/'
          same doubled 'folder=//'
          refused empty-types 'types='
          refused empty-folder 'folder='
          if [ "${code}" != "400" ]; then exit 1; fi
          curl -X DELETE "${dav}/Filterprobe32"

      - name: The drift probe both directions share
        run: |
          echo drift
"""


def test_the_clean_sample_is_clean() -> None:
    # The positive control of every sample below.
    assert scan(_CLEAN) == []


def test_a_condition_on_the_step_is_reported() -> None:
    gated = _CLEAN.replace(
        f"      - name: {STEP}\n",
        f"      - name: {STEP}\n        if: matrix.server-version == 'stable34'\n",
        1,
    )

    assert gated != _CLEAN
    findings = scan(gated)
    assert len(findings) == 1
    assert "carries an if:" in findings[0]


def test_a_step_without_the_400_probe_is_reported() -> None:
    lost = _CLEAN.replace("          refused empty-folder 'folder='\n", "", 1)

    assert lost != _CLEAN
    findings = scan(lost)
    assert len(findings) == 1
    assert "HTTP 400 probe of D-32-01" in findings[0]


def test_a_step_that_lost_a_manipulated_value_is_reported() -> None:
    lost = _CLEAN.replace("          same dots 'folder=/../../'\n", "", 1)

    assert lost != _CLEAN
    findings = scan(lost)
    assert len(findings) == 1
    assert "'folder=/../../'" in findings[0]


def test_a_step_in_the_wrong_place_is_reported() -> None:
    drift = "      - name: The drift probe both directions share\n        run: |\n          echo drift\n"
    moved = _CLEAN.replace(drift, "", 1).replace(
        f"      - name: {STEP}\n",
        f"{drift}\n      - name: {STEP}\n",
        1,
    )

    assert moved != _CLEAN
    findings = scan(moved)
    assert len(findings) == 1
    assert "does not stand between" in findings[0]


def test_a_missing_step_costs_one_finding_per_claim() -> None:
    renamed = _CLEAN.replace(STEP, "Unified search filters, something else", 1)

    findings = scan(renamed)
    assert len(findings) == len(CLAIMS)
    assert findings[0].startswith("the step '")
