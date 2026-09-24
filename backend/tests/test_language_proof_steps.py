"""The gate over the language proof step of ``.github/workflows/deploy-harp.yml``.

Success criterion 1 of phase 19 says that the four new chains answer on a real
Nextcloud "over the green arm64 CI leg". That sentence is carried by one thing
and one thing only: the proof step has no ``if:``. The matrix of this workflow
has four legs, and the two steps that would have been the obvious home for a
language proof, "Store upgrade 5" and "Store upgrade 6", both carry
``matrix.server-version == 'stable34' && matrix.runner == 'ubuntu-24.04' &&
env.RELEASE_TAG == ''``. A proof put there runs on one leg out of four, appears
in the run summary once instead of four times, and says nothing whatever about
arm64 while looking perfectly green.

Nobody reads a missing line. Somebody adding a condition to the proof step out
of a wish to save runner minutes would be making a change that no review catches
by eye and that no red run reports, because the run stays green. That is the
whole reason this module exists, and it is the reason the two gated steps are
read here as well: they are the counter sample. If they ever lost their
condition, the scanner below would be unable to tell a gated step from an
ungated one, and a gate that cannot see the thing it forbids is a gate that
passes for the wrong reason. So their condition is asserted too, and a finding
there says "this gate is broken" rather than "the workflow is broken".

The other four statements, in the order they matter:

1. The proof step exists exactly once. Twice would be two proofs drifting apart,
   never would be the criterion with no evidence behind it.
2. The step asserts on ``entries | length`` and never on the subline of the first
   entry. A hit found through a new language field alone comes back WITHOUT an
   excerpt, measured on 2026-09-24 (19-RESEARCH M-4): the snippet is cut out of
   ``body_de`` because that is the only stored copy of the text, and a question
   that meets the document term only through the Spanish chain has nothing to
   mark in the German one. A probe that asserted on the excerpt would go red on a
   working search, which is the most expensive kind of wrong.
3. The step names all four documents and all four questions. A proof that lost a
   language would be a proof of three languages with the name of four.
4. The step calls the result page four times, once per language. That route had
   never been touched by any CI step of this repository before phase 19, and the
   second half of the criterion is written about it.

And one statement about the matrix rather than about the step: it still carries
an entry on ``ubuntu-24.04-arm``. Without that entry "no condition" buys nothing,
because there would be no arm64 leg for the step to run on.

**Why text and not a YAML parser.** The reason ``test_workflow_pins.py`` gives at
length and ``test_lockstep_versions.py`` repeats: this backend has no yaml
dependency, and a gate that needed one would be a gate that does not run next to
the unit tests. The step scanner relies on the indentation this file uses, six
spaces for a step and eight for its keys, and says so rather than pretending to
understand YAML: a source in which it finds no step at all is a finding and not a
silent pass.

**The gate falls closed.** A workflow file that is gone, a step name that was
renamed and a scanner whose patterns stopped matching all end in the same place
under a naive implementation: zero findings over zero input. So a proof step that
cannot be found does not produce one finding, it produces one finding per
statement that can no longer be checked. Self tests against staged samples belong
to the shape of every textual gate in this repository, and every statement above
has a sample that has to make it fire.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy-harp.yml"

# The step this gate is about, by its full name. A rename is a finding here
# rather than a silent loss of the proof, which is the point of naming it.
PROOF_STEP = "Language proof, the four new chains answer on the ordinary search route"

# The two steps that carry the condition, read as the counter sample. They are
# named by their prefix rather than in full, because their tails describe what
# they assert and those tails are allowed to change.
GATED_STEPS = ("Store upgrade 5,", "Store upgrade 6,")

# The four languages, named through the file name of their proof document. A
# bare "es" would be found inside "these" and inside half the English prose of
# that step, so it would be a check that cannot go red.
DOCUMENTS = ("language-proof-es.txt", "language-proof-it.txt", "language-proof-nl.txt", "language-proof-pt.txt")

# The four questions, each named twice: once as the term the OCS route is asked
# with and once as the query the result page is asked with. Asserting the bare
# word would be weaker than it looks, because "pais" stands inside the accented
# "paises" of the Portuguese document as well.
QUESTIONS = ("alemanes", "informazioni", "beinvloeden", "pais")

# The call of the result page. The parameter is "query" and not "term":
# PageController::term() reads getParam('query'), and a call with ?term= answers
# 200 with the empty landing page.
PAGE_CALL = "apps/findling/?query="
PAGE_CALLS_EXPECTED = 4

# The assertion that has to survive and the one that must not appear.
COUNT_ASSERTION = "entries | length"
EXCERPT_ASSERTION = "entries[0].subline"

# A step opens at six spaces, and its keys sit at eight. The body of a run block
# is indented by ten, which is why the end pattern can afford to look for a hash
# at six spaces or less: the comments inside a run block never reach that far
# left.
_STEP_START = re.compile(r"^ {6}- name:[ \t]*(?P<name>.+?)[ \t]*$")
_STEP_END = re.compile(r"^ {0,6}(?:#|- name:|[A-Za-z0-9_.-]+:)")
_STEP_IF = re.compile(r"^ {8}if:[ \t]*\S", re.MULTILINE)

# The arm64 leg of the matrix, as the include list writes it: a runner key among
# the keys of one entry, which sit at twelve spaces.
_ARM_ENTRY = re.compile(r"^ {12}runner:[ \t]*ubuntu-24\.04-arm[ \t]*$", re.MULTILINE)

# What this gate claims, one line per claim. The list is what the fail closed
# path returns when the step cannot be found at all, so that a lost step costs
# as many findings as it silences.
CLAIMS = (
    "the proof step carries no if: condition",
    "the proof step asserts on the number of entries",
    "the proof step does not assert on the excerpt of the first entry",
    "the proof step names all four proof documents",
    "the proof step names all four questions, on both routes",
    f"the proof step calls the result page {PAGE_CALLS_EXPECTED} times",
)


class Step(NamedTuple):
    """One step of a workflow job, reduced to what the claims above need."""

    name: str
    line: int
    body: str


def collect_steps(source: str) -> list[Step]:
    """Every step of the source, in file order, each with its own body.

    The body is everything below the ``- name:`` line up to the next step, the
    next comment block between steps or the next top level key, whichever comes
    first. The ``if:`` of a step therefore belongs to the step it stands in and
    to no other, which is the whole question this module asks.
    """
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
        # A step never swallows the one that follows it, whatever the end
        # pattern did or did not match: an overrun would let the condition of a
        # later step count as the condition of this one.
        if index + 1 < len(starts):
            end = min(end, starts[index + 1][0])
        steps.append(Step(name, number + 1, "\n".join(lines[number:end])))
    return steps


def _named(steps: list[Step], name: str) -> list[Step]:
    return [step for step in steps if step.name == name]


def _prefixed(steps: list[Step], prefix: str) -> list[Step]:
    return [step for step in steps if step.name.startswith(prefix)]


def scan_counter_sample(steps: list[Step]) -> list[str]:
    """The two gated steps still carry their condition.

    A finding here is a finding about this gate and not about the workflow: if
    no step of the file carries an ``if:`` any more, then "the proof step has
    none" is true of every step and asserts nothing.
    """
    findings: list[str] = []
    for prefix in GATED_STEPS:
        found = _prefixed(steps, prefix)
        if not found:
            findings.append(
                f"the counter sample '{prefix}' is not in the file any more, "
                "so this gate can no longer show that it is able to see a condition"
            )
            continue
        without = [step for step in found if _STEP_IF.search(step.body) is None]
        if without:
            findings.append(
                f"the counter sample '{prefix}' carries no if: at line {without[0].line}, "
                "so this gate would report an ungated proof step as gated and pass for the wrong reason"
            )
    return findings


def scan_proof_step(steps: list[Step]) -> list[str]:
    """Every claim above, against the steps of one source.

    Fail closed: a step that is not there once costs one finding per claim it
    silences, never zero.
    """
    findings: list[str] = []
    found = _named(steps, PROOF_STEP)
    if len(found) != 1:
        findings.append(
            f"the step '{PROOF_STEP}' stands {len(found)} times in the workflow and not once, "
            "so the criterion it carries has no evidence behind it"
        )
        findings.extend(f"unchecked, because the step is not there: {claim}" for claim in CLAIMS)
        return findings

    step = found[0]
    body = step.body

    if _STEP_IF.search(body) is not None:
        findings.append(
            f"the step '{PROOF_STEP}' carries an if: at line {step.line}, so it runs on part of the matrix. "
            "Success criterion 1 of phase 19 is written about the arm64 leg by name, and a condition on "
            "matrix.runner is exactly what takes that leg away."
        )
    if COUNT_ASSERTION not in body:
        findings.append(
            f"the step '{PROOF_STEP}' does not assert on '{COUNT_ASSERTION}', "
            "so it no longer says that anything was found"
        )
    if EXCERPT_ASSERTION in body:
        findings.append(
            f"the step '{PROOF_STEP}' asserts on '{EXCERPT_ASSERTION}'. A hit found through a new "
            "language field alone comes back without an excerpt (19-RESEARCH M-4), so this assertion "
            "goes red on a working search."
        )
    for document in DOCUMENTS:
        if document not in body:
            findings.append(f"the step '{PROOF_STEP}' does not name {document}, so that language is unproven")
    for question in QUESTIONS:
        if f"term={question}" not in body:
            findings.append(f"the step '{PROOF_STEP}' does not ask the search route for '{question}'")
        if f"{PAGE_CALL}{question}" not in body:
            findings.append(f"the step '{PROOF_STEP}' does not ask the result page for '{question}'")
    calls = body.count(PAGE_CALL)
    if calls != PAGE_CALLS_EXPECTED:
        findings.append(
            f"the step '{PROOF_STEP}' calls the result page {calls} times and not {PAGE_CALLS_EXPECTED}, "
            "so the second half of criterion 1 does not stand for every language"
        )
    return findings


def scan_matrix(source: str) -> list[str]:
    """The matrix still runs a leg on arm64.

    Without it "the proof step has no condition" buys nothing, because there
    would be no arm64 leg left for the step to run on.
    """
    if _ARM_ENTRY.search(source) is None:
        finding = (
            "the matrix carries no entry on ubuntu-24.04-arm, so the proof step has no arm64 leg to run on "
            "and success criterion 1 of phase 19 has lost its subject"
        )
        return [finding]
    return []


def scan(source: str) -> list[str]:
    """Every finding of this gate over one workflow source."""
    steps = collect_steps(source)
    if not steps:
        return [
            "the scanner found no step at all in this source, so its indentation assumption no longer holds",
            *(f"unchecked, because no step was found: {claim}" for claim in CLAIMS),
        ]
    return [*scan_proof_step(steps), *scan_counter_sample(steps), *scan_matrix(source)]


# -- the real tree ---------------------------------------------------------


def test_the_workflow_is_there_and_the_scanner_can_read_it() -> None:
    # The anti vacuity clause. Every scanner above returns nothing useful for a
    # source it cannot read, so a gate that lost its input would look perfect.
    assert WORKFLOW.is_file()

    steps = collect_steps(WORKFLOW.read_text(encoding="utf-8"))

    assert len(steps) >= 40
    # And the extraction really splits: no step body may contain the opening
    # line of another one, or a condition three steps down would count as this
    # one's.
    for step in steps:
        opens = [line for line in step.body.splitlines() if _STEP_START.match(line)]
        assert len(opens) == 1, step.name


def test_the_language_proof_step_stands_exactly_once() -> None:
    steps = collect_steps(WORKFLOW.read_text(encoding="utf-8"))

    assert len(_named(steps, PROOF_STEP)) == 1


def test_the_language_proof_step_carries_no_condition() -> None:
    # The statement this module exists for, and the one no run reports: a
    # conditional proof step stays green and stops proving.
    steps = collect_steps(WORKFLOW.read_text(encoding="utf-8"))

    assert _STEP_IF.search(_named(steps, PROOF_STEP)[0].body) is None


def test_the_two_gated_steps_still_carry_theirs() -> None:
    # The counter sample, read as a statement about this gate rather than about
    # the workflow.
    steps = collect_steps(WORKFLOW.read_text(encoding="utf-8"))

    assert scan_counter_sample(steps) == []


def test_the_step_asserts_on_the_count_and_never_on_the_excerpt() -> None:
    body = _named(collect_steps(WORKFLOW.read_text(encoding="utf-8")), PROOF_STEP)[0].body

    assert COUNT_ASSERTION in body
    assert EXCERPT_ASSERTION not in body


def test_the_step_names_all_four_documents_and_all_four_questions() -> None:
    body = _named(collect_steps(WORKFLOW.read_text(encoding="utf-8")), PROOF_STEP)[0].body

    assert [document for document in DOCUMENTS if document not in body] == []
    assert [question for question in QUESTIONS if f"term={question}" not in body] == []
    assert [question for question in QUESTIONS if f"{PAGE_CALL}{question}" not in body] == []


def test_the_step_calls_the_result_page_once_per_language() -> None:
    body = _named(collect_steps(WORKFLOW.read_text(encoding="utf-8")), PROOF_STEP)[0].body

    assert body.count(PAGE_CALL) == PAGE_CALLS_EXPECTED


def test_the_matrix_still_runs_a_leg_on_arm64() -> None:
    assert scan_matrix(WORKFLOW.read_text(encoding="utf-8")) == []


def test_the_real_workflow_produces_no_finding_at_all() -> None:
    assert scan(WORKFLOW.read_text(encoding="utf-8")) == []


# -- self tests: every claim has to be able to go red -----------------------

# A miniature of the shape this gate judges: one ungated proof step, two gated
# counter samples and a matrix with the arm64 entry. Short on purpose, and every
# line of it is a line one of the samples below breaks.
_CLEAN = """name: Sample

jobs:
  deploy-harp:
    timeout-minutes: 45
    strategy:
      matrix:
        include:
          - server-version: stable34
            php-version: '8.2'
            runner: ubuntu-24.04
          - server-version: stable34
            php-version: '8.2'
            runner: ubuntu-24.04-arm
    steps:
      - name: Language proof, the four new chains answer on the ordinary search route
        run: |
          for lang in es it nl pt; do
            case "${lang}" in
              es) term=alemanes ;;
              it) term=informazioni ;;
              nl) term=beinvloeden ;;
              pt) term=pais ;;
            esac
            curl "http://localhost:8080/ocs/v2.php/search/providers/findling/search?term=${term}"
            jq -e '.ocs.data.entries | length >= 1' "hit-${lang}.json"
            jq -e '.title == "language-proof-es.txt"' one.json
            jq -e '.title == "language-proof-it.txt"' two.json
            jq -e '.title == "language-proof-nl.txt"' three.json
            jq -e '.title == "language-proof-pt.txt"' four.json
          done
          curl 'http://localhost:8080/index.php/apps/findling/?query=alemanes'
          curl 'http://localhost:8080/index.php/apps/findling/?query=informazioni'
          curl 'http://localhost:8080/index.php/apps/findling/?query=beinvloeden'
          curl 'http://localhost:8080/index.php/apps/findling/?query=pais'

      - name: Store upgrade 5, the six assurances after the upgrade
        if: matrix.server-version == 'stable34' && matrix.runner == 'ubuntu-24.04'
        run: |
          echo the gated one

      - name: Store upgrade 6, the rebuild a changed language set orders
        if: matrix.server-version == 'stable34' && matrix.runner == 'ubuntu-24.04'
        run: |
          echo the other gated one
"""


def test_the_clean_sample_is_clean() -> None:
    # The counter sample of everything below. Without it a scanner that reported
    # every source as broken would pass all the failure tests too.
    assert collect_steps(_CLEAN) != []
    assert scan(_CLEAN) == []


# The two mistakes the plan of 19-07 names by hand, each as a staged sample of
# its own rather than as a line inside a test. They are the two changes that
# would leave a run green and the criterion unproven, which is to say the two
# nobody would catch by reading the summary of a run:
#
#   _GATED   the proof step with the condition of the step next door, copied
#            over in a wish to save runner minutes
#   _EXCERPT the proof step asking for the excerpt of a hit that has none by
#            construction (19-RESEARCH M-4)
_GATED = _CLEAN.replace(
    "      - name: Language proof, the four new chains answer on the ordinary search route\n",
    "      - name: Language proof, the four new chains answer on the ordinary search route\n"
    "        if: matrix.server-version == 'stable34' && matrix.runner == 'ubuntu-24.04'\n",
    1,
)

_EXCERPT = _CLEAN.replace(
    "jq -e '.ocs.data.entries | length >= 1' \"hit-${lang}.json\"",
    'jq -e \'.ocs.data.entries[0].subline != ""\' "hit-${lang}.json"',
    1,
)


def test_the_two_staged_samples_really_differ_from_the_clean_one() -> None:
    # Without this line a replace that stopped matching would leave both samples
    # equal to the clean one, and the two tests below would then assert that a
    # clean source is clean.
    assert _GATED != _CLEAN
    assert _EXCERPT != _CLEAN


def test_a_condition_on_the_proof_step_is_reported() -> None:
    # The statement this module exists for.
    findings = scan(_GATED)

    assert len(findings) == 1
    assert "carries an if:" in findings[0]


def test_an_assertion_on_the_excerpt_is_reported() -> None:
    # The second mistake that stays green in a run and is wrong in the world:
    # a probe that asks for the excerpt of a hit that has none by construction.
    findings = scan(_EXCERPT)

    assert len(findings) == 2
    assert any("does not assert on 'entries | length'" in finding for finding in findings)
    assert any("asserts on 'entries[0].subline'" in finding for finding in findings)


def test_a_missing_proof_step_costs_one_finding_per_claim() -> None:
    # The fail closed clause. A renamed step must not buy silence.
    source = _CLEAN.replace("Language proof, the four new chains", "Language proof, something else entirely", 1)

    findings = scan(source)

    assert len(findings) == len(CLAIMS) + 1
    assert findings[0].startswith("the step '")
    assert all(finding.startswith("unchecked, because the step is not there:") for finding in findings[1:])


def test_a_result_page_call_that_went_missing_is_reported() -> None:
    source = _CLEAN.replace(
        "          curl 'http://localhost:8080/index.php/apps/findling/?query=pais'\n",
        "",
        1,
    )

    findings = scan(source)

    assert len(findings) == 2
    assert any("does not ask the result page for 'pais'" in finding for finding in findings)
    assert any("calls the result page 3 times and not 4" in finding for finding in findings)


def test_a_language_that_lost_its_document_is_reported() -> None:
    source = _CLEAN.replace("jq -e '.title == \"language-proof-nl.txt\"' three.json\n", "", 1)

    findings = scan(source)

    assert len(findings) == 1
    assert "does not name language-proof-nl.txt" in findings[0]


def test_a_counter_sample_without_its_condition_is_reported() -> None:
    # A finding about this gate rather than about the workflow, and the message
    # has to say so: if nothing in the file is gated any more, "the proof step
    # is not gated" is true of everything and asserts nothing.
    source = _CLEAN.replace(
        "      - name: Store upgrade 6, the rebuild a changed language set orders\n"
        "        if: matrix.server-version == 'stable34' && matrix.runner == 'ubuntu-24.04'\n",
        "      - name: Store upgrade 6, the rebuild a changed language set orders\n",
        1,
    )

    findings = scan(source)

    assert len(findings) == 1
    assert "pass for the wrong reason" in findings[0]


def test_a_matrix_without_the_arm64_leg_is_reported() -> None:
    source = _CLEAN.replace("            runner: ubuntu-24.04-arm\n", "            runner: ubuntu-24.04\n", 1)

    findings = scan(source)

    assert len(findings) == 1
    assert "ubuntu-24.04-arm" in findings[0]


def test_a_source_without_any_step_falls_closed() -> None:
    findings = scan("name: Sample\n")

    assert len(findings) == len(CLAIMS) + 1
    assert findings[0].startswith("the scanner found no step at all")
