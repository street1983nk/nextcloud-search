"""No language detector: the absence of that path, read out of the sources.

The anti-feature of this milestone, and it was decided unanimously: Findling
detects no language, neither of a document nor of a query. ``STATE.md`` carries
it among the decisions the milestone rests on, the grundsatz paper of phase 17
repeats it, and success criterion 4 of phase 19 in ``ROADMAP.md`` asks for
exactly this file: "there is no language detection path, neither on the document
nor on the query side; a test holds the anti-feature."

**Why this file is a source reader and not a functional test.** A functional
test cannot prove the absence of a path. It exercises what exists; a detector
would sit beside everything such a test touches and every single assertion would
stay green. A search that guesses the language of a query is also not a crash:
it answers, it answers plausibly, and it answers wrong only for the documents
the user never gets to see. So the statements below read the sources, in the
shape ``test_semantic_boundary.py`` invented for the boundary of the semantic
half and ``test_search_fields_lockstep.py`` repeated for the wire.

**Four statements, and the first one is the strongest.**

1. The function that builds the field plan takes no query text, in any shape.
   Read off its signature: no parameter named after a search line, and none that
   could carry one. A detector of the query is therefore not forbidden here, it
   has nothing to attach to.
2. ``build_query`` takes its field plan out of its parameter and never out of
   the configuration or out of a module constant. The three constants that fell
   in plan 19-01 are named too, because a detector needs somewhere to write its
   answer into and those three were that place.
3. Neither ``backend/pyproject.toml`` nor ``backend/uv.lock`` carries a package
   of the detection family. Checked against both files on 2026-09-24, and the
   result was empty.
4. The wire carries no language field either. That one is held by
   ``test_search_fields_lockstep.py`` already, through ``extra="forbid"`` and the
   field lists of both request models, and this file names that gate rather than
   repeating its statement.

**Hygiene is the job here, not a detail.** This very module spells out every
forbidden word in its prose in order to explain it, and so do the staged samples
below. A counting assertion that trips over its own explanatory text is an
assertion somebody deletes, and they would be right to. Every count therefore
runs over the code of a source with comments and string literals removed, taken
from ``test_semantic_boundary.py`` rather than written a second time, and two of
the cases prove that the filter does what it says.

**What this file does not prove.** It says nothing about whether the field plan
that does get built is the right one. That is the job of
``test_query_fields_plan.py``, of the ranking probe in
``test_field_plan_ranking.py`` and of the language cases on the search path.
"""

from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path

from test_semantic_boundary import code_mentions

TESTS_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = TESTS_ROOT.parent
PACKAGE_ROOT = BACKEND_ROOT / "src" / "findling"
RESOURCES_SOURCE = PACKAGE_ROOT / "api" / "resources.py"
REWRITE_SOURCE = PACKAGE_ROOT / "query" / "rewrite.py"

# Statement 4 lives there and stays there. Named rather than repeated: two gates
# holding one claim are two gates that drift apart, and that one is older.
WIRE_FORMAT_GATE = TESTS_ROOT / "test_search_fields_lockstep.py"
WIRE_MODELS = ("SearchRequest", "SnippetsRequest")

# The function that answers "which fields does a bare word reach", and the one
# that turns a search line into a query. The first must not know the line, the
# second must not know a plan from anywhere but its parameter.
PLAN_BUILDER = "field_plan_for"
QUERY_BUILDER = "build_query"
PLAN_PARAMETER = "plan"

# The configuration accessor, held as a string so that this module can talk
# about it without its own counters seeing a mention of it in their own gate.
CONFIGURATION = "settings"

# The three module constants plan 19-01 turned into one value. They are named
# here because they are the shape the mistake would take: a detector needs
# somewhere to put its answer, and a module level field list is that somewhere.
FALLEN_CONSTANTS = ("DEFAULT_FIELDS", "TITLE_ONLY_FIELDS", "FIELD_BOOSTS")

# A parameter carrying one of these words is a search line, whatever the
# docstring above it says. Closed on purpose, and compared part by part after
# splitting on underscores so that search_text, query_line and raw_query are
# caught without a regular expression nobody can read.
FORBIDDEN_PARAMETER_NAMES = frozenset(
    {
        "text",
        "texts",
        "q",
        "query",
        "queries",
        "term",
        "terms",
        "line",
        "search",
        "needle",
        "phrase",
        "words",
        "input",
    }
)

# And the other half of "or could be one": a parameter annotated as plain text
# can carry a search line under any name at all.
TEXT_ANNOTATIONS = ("str", "str | None", "bytes", "bytes | None")

# The detection family, closed, held against both dependency files on
# 2026-09-24 with an empty result. Spelled without version bounds and compared
# case insensitively against a name normalised to hyphens, because pypi treats
# an underscore and a hyphen as the same character and a capital letter is not
# a defence.
FORBIDDEN_PACKAGES = (
    "langdetect",
    "lingua",
    "langid",
    "py3langid",
    "fasttext",
    "cld2",
    "cld3",
    "pycld",
)

DEPENDENCY_FILES = ("pyproject.toml", "uv.lock")

# The anti-vacuity clause of the dependency reader: a file that gets read at all
# carries the name of the engine this project is built on. Without it a reader
# pointed at a directory that moved finds no detector in no bytes and looks
# perfectly healthy.
DEPENDENCY_ANCHOR = "tantivy"


# -- the readers -----------------------------------------------------------


def read(path: Path) -> str:
    """One source as text."""
    return path.read_text(encoding="utf-8")


def function_of(source: str, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """The definition of one function of a source, or None when it is not there.

    The shape of ``functions_calling`` in ``test_semantic_boundary.py``, which
    visits both kinds of definition for the same reason: an async def is a def,
    and a gate that only knew the synchronous one would be silent about half of
    this package.
    """
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            return node
    return None


def parameters_of(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.arg]:
    """Every parameter of a definition: positional, keyword only and starred."""
    spec = node.args
    starred = [argument for argument in (spec.vararg, spec.kwarg) if argument is not None]
    return [*spec.posonlyargs, *spec.args, *spec.kwonlyargs, *starred]


def names_in_the_code_of(source: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Every identifier standing in the code of one function, prose gone.

    The tokenizer rather than a line filter, and the line span of the definition
    rather than its source segment: a line filter drops comments and leaves
    docstrings standing, and the docstring of ``build_query`` is exactly where
    the configuration accessor is named, in order to say that it is never read.
    """
    last = node.end_lineno or node.lineno
    return [
        token.string
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.NAME and node.lineno <= token.start[0] <= last
    ]


def signature_findings(source: str, name: str) -> list[str]:
    """Every parameter of one function that is a search line, or could be.

    Fails closed: a function that is not in this source at all is a finding and
    not an empty list, because a gate that reports nothing about nothing is the
    gate that stays green through the rename which removed its subject.
    """
    node = function_of(source, name)
    if node is None:
        return [f"{name}: no function of that name in this source"]
    findings: list[str] = []
    for argument in parameters_of(node):
        if set(argument.arg.lower().split("_")) & FORBIDDEN_PARAMETER_NAMES:
            findings.append(f"{name}({argument.arg}): a parameter named after a search line")
        annotation = ast.unparse(argument.annotation) if argument.annotation else ""
        if annotation in TEXT_ANNOTATIONS:
            findings.append(f"{name}({argument.arg}: {annotation}): a parameter that can carry a search line")
    return findings


def plan_source_findings(source: str) -> list[str]:
    """Every way the query builder could take its field plan from somewhere else."""
    node = function_of(source, QUERY_BUILDER)
    if node is None:
        return [f"{QUERY_BUILDER}: no function of that name in this source"]
    findings: list[str] = []
    if PLAN_PARAMETER not in [argument.arg for argument in parameters_of(node)]:
        findings.append(f"{QUERY_BUILDER}: no {PLAN_PARAMETER} parameter, so the plan arrives some other way")
    mentions = names_in_the_code_of(source, node).count(CONFIGURATION)
    if mentions:
        findings.append(f"{QUERY_BUILDER}: names {CONFIGURATION} {mentions} times in its own code")
    findings.extend(
        f"{constant}: the fallen constant stands in the code of this module again"
        for constant in FALLEN_CONSTANTS
        if code_mentions(source, constant)
    )
    return findings


def detectors_named_in(text: str) -> list[str]:
    """Every package of the detection family the text names, sorted."""
    folded = text.lower().replace("_", "-")
    return sorted(name for name in FORBIDDEN_PACKAGES if name in folded)


def dependency_findings(root: Path) -> list[str]:
    """Every detector named in the two dependency files under a directory.

    Fails closed in the same way: a file that is not there produces a finding
    rather than nothing, so a reader pointed at a directory that moved cannot
    report an empty result and be believed.
    """
    findings: list[str] = []
    for name in DEPENDENCY_FILES:
        path = root / name
        if not path.is_file():
            findings.append(f"{name}: not there to be read, and a file that cannot be read is no permission")
            continue
        findings.extend(f"{name}: names {hit}" for hit in detectors_named_in(read(path)))
    return findings


def wire_format_findings(gate: Path) -> list[str]:
    """Whether the gate holding the wire format of both request models is still there."""
    if not gate.is_file():
        return [f"{gate.name}: the gate that holds the two request models is gone"]
    source = read(gate)
    return [f"{gate.name}: does not name {model} any more" for model in WIRE_MODELS if model not in source]


def every_finding(resources: str, rewrite: str, root: Path, gate: Path) -> list[str]:
    """All four statements at once, for the case that asks what an emptied guard says."""
    return [
        *signature_findings(resources, PLAN_BUILDER),
        *plan_source_findings(rewrite),
        *dependency_findings(root),
        *wire_format_findings(gate),
    ]


# -- statement 1: the field plan never learns what the user typed -----------


def test_the_function_that_builds_the_field_plan_takes_no_search_text() -> None:
    source = read(RESOURCES_SOURCE)

    node = function_of(source, PLAN_BUILDER)

    assert node is not None, f"{PLAN_BUILDER} has to be in {RESOURCES_SOURCE.name} at all, or this case is empty"
    names = [argument.arg for argument in parameters_of(node)]
    findings = signature_findings(source, PLAN_BUILDER)
    assert findings == [], (
        "the anti-feature is structural or it is nothing: a plan builder that took the query text would turn a "
        f"detector of the query into a two line change instead of an impossibility; parameters {names}, {findings}"
    )


_PLAN_FUNCTION_WITH_A_TEXT_PARAMETER = '''

def field_plan_for(marks: Mapping[str, str], index: Index, search_text: str) -> FieldPlan:
    """The shape of the mistake: the field plan learns what the user typed."""
    return LEGACY_PLAN
'''


def test_a_plan_function_with_a_text_parameter_makes_that_check_red() -> None:
    # The red proof of the statement above. Without it the assertion stays green
    # for a reader that lost the ability to see a parameter at all.
    findings = signature_findings(_PLAN_FUNCTION_WITH_A_TEXT_PARAMETER, PLAN_BUILDER)

    assert findings == [
        f"{PLAN_BUILDER}(search_text): a parameter named after a search line",
        f"{PLAN_BUILDER}(search_text: str): a parameter that can carry a search line",
    ], f"a text parameter has to move the finding list, otherwise the assertion above is decoration: {findings}"


# -- statement 2: the query builder reads the plan out of its parameter -----


def test_the_query_builder_takes_its_field_plan_out_of_its_parameter() -> None:
    # The other end of the same wire. The plan builder cannot be handed the query
    # text, and the query builder cannot go and fetch a plan of its own; between
    # the two there is no place left for a detector to sit.
    findings = plan_source_findings(read(REWRITE_SOURCE))

    assert findings == [], (
        "a field plan read out of the configuration or out of a module constant would be a second answer to a "
        f"question the directory already answers, and the place a detector would write into: {findings}"
    )


_PROSE_ONLY_SAMPLE = '''"""A module whose docstring names settings and langdetect on purpose.

It also spells out query, text and search, because this is the text that has to
explain why the field plan may take none of them. Under a naive count that
sentence is indistinguishable from the thing it warns about.
"""

# settings, settings, langdetect: a comment line spelling out the forbidden
# words, which is what the prose of this phase actually looks like.

MESSAGE = "settings and langdetect in a string literal"


def build_query(index: object, text: str, *, plan: object = None) -> object:
    """Reads its plan out of plan and never out of settings() or a constant."""
    return (index, text, plan)
'''


def test_a_docstring_and_a_comment_full_of_the_forbidden_words_move_no_count() -> None:
    # The hygiene, and it is not hypothetical here: this module and the sources
    # it reads name every forbidden word in prose, because somebody has to say
    # out loud what may not exist.
    naive = _PROSE_ONLY_SAMPLE.count(CONFIGURATION)

    assert naive >= 5, f"the sample has to be far off under a naive count, otherwise it proves nothing: {naive}"
    assert plan_source_findings(_PROSE_ONLY_SAMPLE) == [], (
        "a counting gate that trips over its own explanatory text is a gate somebody deletes, and this file "
        f"writes exactly that text; the naive count says {naive}"
    )
    assert sum(code_mentions(_PROSE_ONLY_SAMPLE, name) for name in FORBIDDEN_PACKAGES) == 0, (
        "and the same holds for the detector named twice in that prose: a filter that counted docstrings would "
        "report the explanation as the offence"
    )


# -- statement 3: no detector in the dependency tree ------------------------


def test_no_dependency_file_of_the_backend_names_a_language_detector() -> None:
    findings = dependency_findings(BACKEND_ROOT)

    assert findings == [], (
        "a detector arriving as a dependency would break the anti-feature without a single line of our own code "
        f"changing, which is the one way this gate could be walked past: {findings}"
    )


def test_the_dependency_reader_reads_real_dependency_files() -> None:
    # The anti-vacuity clause of the case above. A reader pointed at a directory
    # that moved finds no detector in no bytes and stays green.
    anchored = [name for name in DEPENDENCY_FILES if DEPENDENCY_ANCHOR in read(BACKEND_ROOT / name)]

    assert anchored == list(DEPENDENCY_FILES), (
        f"both dependency files have to name {DEPENDENCY_ANCHOR}, otherwise the silence above is about the "
        f"wrong directory; the anchor was found in {anchored}"
    )


_DEPENDENCY_FILE_WITH_A_DETECTOR = """[project]
name = "findling"
dependencies = [
    "tantivy==0.26.2",
    "langdetect==1.0.9",
]
"""

_DEPENDENCY_FILE_WITHOUT_ONE = """[project]
name = "findling"
dependencies = [
    "tantivy==0.26.2",
]
"""


def test_a_dependency_file_that_names_a_detector_makes_that_check_red(tmp_path: Path) -> None:
    for name in DEPENDENCY_FILES:
        (tmp_path / name).write_text(_DEPENDENCY_FILE_WITH_A_DETECTOR, encoding="utf-8")

    findings = dependency_findings(tmp_path)

    assert detectors_named_in(_DEPENDENCY_FILE_WITHOUT_ONE) == [], (
        "the clean sample has to stay clean, otherwise the reader answers yes to everything"
    )
    assert findings == [f"{name}: names langdetect" for name in DEPENDENCY_FILES], (
        f"a named detector has to move the finding list, otherwise the case above is decoration: {findings}"
    )


# -- statement 4: named, not repeated ---------------------------------------


def test_the_gate_that_holds_the_two_request_models_is_still_there() -> None:
    # The wire carries no language field, and that is held next door through
    # extra="forbid" and the field lists of both request models. Named here so
    # that deleting it is a red test somewhere, and not repeated here so that
    # there stays exactly one place to change when the wire changes.
    findings = wire_format_findings(WIRE_FORMAT_GATE)

    assert findings == [], (
        "the fourth statement of this anti-feature is somebody else's, and a statement whose owner disappeared "
        f"is a statement nobody makes any more: {findings}"
    )


# -- the guard against an emptied guard -------------------------------------


_AN_EMPTIED_SOURCE = '''"""The module somebody moved everything out of."""
'''


def test_an_emptied_guard_reports_one_finding_per_statement_and_not_zero(tmp_path: Path) -> None:
    # The self proof of all four. A guard whose only evidence is "the tree is
    # clean today" is green on the day somebody empties the sources it reads.
    standing = every_finding(read(RESOURCES_SOURCE), read(REWRITE_SOURCE), BACKEND_ROOT, WIRE_FORMAT_GATE)
    emptied = every_finding(_AN_EMPTIED_SOURCE, _AN_EMPTIED_SOURCE, tmp_path, tmp_path / "gone.py")

    assert standing == [], f"the four statements have to hold against the tree as it stands: {standing}"
    assert len(emptied) >= 4, (
        "every one of the four statements has to fail closed on its own, so that a source which moved produces "
        f"a finding instead of a silence; the emptied guard reported {emptied}"
    )


def test_this_guard_does_not_trip_over_its_own_prose() -> None:
    # The last one, and the reason the tokenizer is here at all: this file names
    # every forbidden word many times over, in its header, in its constants and
    # in five staged samples. None of that may move a counter.
    own = read(Path(__file__).resolve())

    naive = sum(own.count(name) for name in (*FORBIDDEN_PACKAGES, CONFIGURATION))

    # Measured at 20 on 2026-09-24. The bound stays well under that: a ratchet
    # sitting exactly on its own measurement turns red the next time somebody
    # shortens a paragraph, which is not what this case is about.
    assert naive >= 15, f"this file has to name the forbidden words often enough to be a real test: {naive}"
    assert sum(code_mentions(own, name) for name in (*FORBIDDEN_PACKAGES, CONFIGURATION)) == 0, (
        "the guard spells out what may not exist, and every one of those mentions is prose, a comment or a "
        f"string literal; a naive reader counts {naive} of them"
    )
