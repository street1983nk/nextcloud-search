"""The two request models of the search protocol, held against one another.

Both ``SearchRequest`` and ``SnippetsRequest`` carry ``extra="forbid"``, and
that is a security control rather than tidiness: it is what keeps a caller from
smuggling an identity past the signed AppAPI header. It has a second effect, and
that one is the reason this gate exists. A field the result page sends and only
one of the two models declares is an extra field to the other, so the excerpt
call answers 422, ``ExAppService::call()`` turns a 422 into ``null``, and the
page shows "Die Suche antwortet gerade nicht" instead of excerpts, for hits it
had already found and displayed. The search works, the snippets do not, and
nothing in either log says why.

The statement this gate makes is therefore not "both models carry the same
fields". They do not, and should not: paging belongs to the candidate call and a
list of file ids belongs to the excerpt call. The statement is that every field
which touches the query builder arrives in both, and that every field which
stands on one side alone is named here with the argument for its being alone.

The shape is the shape of ``test_search_limits_lockstep.py`` and of the other
textual gates of this repository: it reads the sources as text rather than
importing them, so that a model which does not even import any more is a red
gate and not an error in collection; it fails closed, so a file that moved
produces a finding for every field that should have come out of it; and it
carries self tests against staged samples, so that a gate whose body was deleted
cannot report zero findings over zero fields and look healthy.

**What this gate does not prove.** It says nothing about whether a field is a
good idea, whether its bounds are the right ones, or whether the route does
anything with it. Those arguments stand at the fields themselves and at the
constants in ``backend/src/findling/config.py``. This gate insists on one thing
only: that a decision about the wire is made once and arrives in both models,
and that the sort names are spelled the same in the model and in the engine.

The second subject is that last half sentence, and it is here rather than in a
file of its own because it is the same failure wearing a different coat.
``SearchRequest.sort`` declares its three names as a ``Literal``, and
``findling.index.search.SORT_MODES`` declares them a second time as the keys of
the table the engine looks the order up in. ``SORT_MODES.get`` answers ``None``
for a name it does not know, and ``None`` is the relevance branch, on purpose:
the route has already validated, and a second exception would turn a typo into
an HTTP 500. The price of that quiet fallback is that two lists which drifted
apart produce no error anywhere. The page would go back to relevance while the
address bar still says "newest", which is the kind of defect that gets reported
as "sorting sometimes does not work".
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SEARCH_MODULE = REPO_ROOT / "backend" / "src" / "findling" / "api" / "search.py"
SNIPPETS_MODULE = REPO_ROOT / "backend" / "src" / "findling" / "api" / "snippets.py"
ENGINE_MODULE = REPO_ROOT / "backend" / "src" / "findling" / "index" / "search.py"

# How the two sides are named in a finding. A side without its file name sends
# the reader looking for the second half of the pair.
SEARCH_MODEL = "SearchRequest in backend/src/findling/api/search.py"
SNIPPETS_MODEL = "SnippetsRequest in backend/src/findling/api/snippets.py"
SORT_FIELD = "the Literal of SearchRequest.sort in backend/src/findling/api/search.py"
SORT_TABLE = "SORT_MODES in backend/src/findling/index/search.py"

# Every field that stands in one model alone, with the argument for its being
# alone. A mapping of name to reason, and deliberately not a count: a number
# saying "this many fields may differ" covers a forgotten field exactly as well
# as an intended one, while a list names four and nothing else. The reason
# travels with the key, so a fifth entry has to be argued rather than counted.
#
# Three of the four were one sided before this phase and are one sided because
# the two calls ask different questions. The fourth is the one FILT-02 adds and
# the one this gate was written for.
FIELDS_THAT_MAY_DIFFER = {
    "sort": (
        "SearchRequest only: it changes the order of an answer and not the "
        "question. The excerpt call asks about named fileIds and answers a "
        "mapping, so it has no order; a sort field over there would be a field "
        "that does nothing today and something at the next rebuild"
    ),
    "limit": "SearchRequest only: how large a page of candidates is, which the excerpt call does not produce",
    "offset": "SearchRequest only: where that page starts, which the excerpt call does not produce",
    "fileIds": "SnippetsRequest only: the subject of the excerpt call, which the candidate call is asked to find",
}

# A model class and everything indented under it, up to the first line that
# starts in column one again. Both models are declared at module level, so the
# end of the body is the end of the class.
_CLASS = r"^class {name}\([^)]*\):\n(?P<body>(?:(?:[ \t].*)?\n)*)"

# The leading docstring of a class body. Cut before the fields are read, because
# a line of prose that happens to carry a word and a colon would otherwise read
# as a field declaration.
_DOCSTRING = re.compile(r'\A\s*"""(?:.|\n)*?"""', re.MULTILINE)

# One annotated field of a model: a name at exactly four spaces of indentation,
# followed by a colon. An assignment without an annotation, such as
# model_config, is not a field of the wire and does not match.
_FIELD = re.compile(r"^ {4}(\w+)\s*:", re.MULTILINE)

# The quoted members of a Literal, wherever the annotation wraps it. The
# expression stops at the first closing bracket, which is the one of the Literal
# itself in both list[Literal[...]] and a bare Literal[...].
_LITERAL = r"{field}\s*:\s*[^=\n]*?Literal\[([^\]]*)\]"

# The body of the SORT_MODES mapping, and then its keys. The annotation between
# the name and the equals sign is deliberately not spelled out: this gate is
# about the names in the table, not about how the table is typed.
_SORT_MODES = re.compile(r"SORT_MODES[^=\n]*=\s*\{(.*?)\}", re.DOTALL)
_MAPPING_KEY = re.compile(r'"([^"]*)"\s*:')

_QUOTED = re.compile(r'"([^"]*)"')


def read(path: Path) -> str:
    """The text of one file, or an empty string when it is not there.

    The empty string produces a finding for every field that should have come
    out of it, which is the fail closed direction: a gate whose sources moved
    has to go red rather than quiet.
    """
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def class_body(source: str, name: str) -> str:
    """Everything indented under one class declaration, without its docstring.

    An empty string when the class is not in the source at all, for the same
    reason :func:`read` answers one: a model that was renamed has to look like a
    model whose fields are all missing.
    """
    found = re.search(_CLASS.format(name=name), source, re.MULTILINE)
    if found is None:
        return ""
    return _DOCSTRING.sub("", found.group("body"))


def model_fields_of(source: str, name: str) -> set[str]:
    """The declared field names of one request model, read as text."""
    return set(_FIELD.findall(class_body(source, name)))


def literal_values(source: str, class_name: str, field: str) -> tuple[str, ...]:
    """The quoted members of the Literal one field is annotated with.

    An empty tuple when the field, the Literal or the whole class cannot be
    found, which is a finding rather than agreement with an empty table.
    """
    found = re.search(_LITERAL.format(field=field), class_body(source, class_name))
    return () if found is None else tuple(_QUOTED.findall(found.group(1)))


def sort_mode_names(source: str) -> tuple[str, ...]:
    """The keys of the SORT_MODES table, in the order they are written."""
    found = _SORT_MODES.search(source)
    return () if found is None else tuple(_MAPPING_KEY.findall(found.group(1)))


def findings(search_fields: set[str], snippets_fields: set[str]) -> list[str]:
    """Every field that stands on one side without an argument for standing there.

    A side that could not be read at all is reported as that and never a second
    time as a difference: the unreadable model is the defect, and every missing
    field is what follows from it.
    """
    unreadable = [
        f"{side} could not be read at all"
        for side, fields in ((SEARCH_MODEL, search_fields), (SNIPPETS_MODEL, snippets_fields))
        if not fields
    ]
    if unreadable:
        return unreadable

    one_sided = (
        (SEARCH_MODEL, search_fields - snippets_fields),
        (SNIPPETS_MODEL, snippets_fields - search_fields),
    )
    return [
        f"{name} stands in {side} alone and is not named in FIELDS_THAT_MAY_DIFFER"
        for side, only in one_sided
        for name in sorted(only - set(FIELDS_THAT_MAY_DIFFER))
    ]


def order_findings(declared: tuple[str, ...], tabled: tuple[str, ...]) -> list[str]:
    """Every sort name the model and the engine do not agree on.

    Compared as sets and not as sequences: the order of three names in a Literal
    is a matter of reading, and demanding it would be a second statement this
    gate never argued for. An empty side is reported as unreadable first, for
    the same reason :func:`findings` does.
    """
    unreadable = [
        f"{side} could not be read at all"
        for side, names in ((SORT_FIELD, declared), (SORT_TABLE, tabled))
        if not names
    ]
    if unreadable:
        return unreadable

    return [
        f"{name} stands in {side} and not in {other}"
        for side, other, only in (
            (SORT_FIELD, SORT_TABLE, set(declared) - set(tabled)),
            (SORT_TABLE, SORT_FIELD, set(tabled) - set(declared)),
        )
        for name in sorted(only)
    ]


def of_the_tree() -> tuple[set[str], set[str], tuple[str, ...], tuple[str, ...]]:
    """The four readings this gate judges, as they stand in this checkout."""
    search_source = read(SEARCH_MODULE)
    return (
        model_fields_of(search_source, "SearchRequest"),
        model_fields_of(read(SNIPPETS_MODULE), "SnippetsRequest"),
        literal_values(search_source, "SearchRequest", "sort"),
        sort_mode_names(read(ENGINE_MODULE)),
    )


# -- the real tree ---------------------------------------------------------


def test_all_three_sources_are_where_this_gate_looks_for_them() -> None:
    # The anti vacuity clause. Without it a gate whose files were renamed would
    # read three empty strings, and three missing readings must be a finding
    # rather than a quiet pass.
    missing = [str(path) for path in (SEARCH_MODULE, SNIPPETS_MODULE, ENGINE_MODULE) if not path.is_file()]

    assert missing == []


def test_all_four_readings_carry_something() -> None:
    # The second half of the same clause: the files exist and the expressions
    # still find something in them. A pattern that stopped matching would leave
    # the comparisons below comparing nothing with nothing.
    search_fields, snippets_fields, declared, tabled = of_the_tree()

    assert search_fields != set()
    assert snippets_fields != set()
    assert declared != ()
    assert tabled != ()


def test_every_field_that_touches_the_query_arrives_in_both_models() -> None:
    # No field is demanded by name anywhere in this file, and that is
    # deliberate: which fields the wire carries is a decision of its own, and a
    # gate that listed them would be the first file edited by whoever adds one,
    # without the two models ever being compared.
    search_fields, snippets_fields, _, _ = of_the_tree()

    assert findings(search_fields, snippets_fields) == []


def test_the_sort_names_of_the_model_are_the_keys_of_the_engine_table() -> None:
    _, _, declared, tabled = of_the_tree()

    assert order_findings(declared, tabled) == []


def test_the_field_that_is_allowed_to_differ_carries_its_reason_with_it() -> None:
    # The entry this phase added, and the one the whole exception list exists
    # for. A key without a reason would be a threshold with a name.
    assert "sort" in FIELDS_THAT_MAY_DIFFER
    assert "order" in FIELDS_THAT_MAY_DIFFER["sort"]
    assert all(reason.strip() != "" for reason in FIELDS_THAT_MAY_DIFFER.values())


def test_the_excerpt_call_really_has_no_sort_field() -> None:
    # The other half of that entry, read off the tree rather than trusted. The
    # exception says sort may be missing over there; this says it is.
    _, snippets_fields, _, _ = of_the_tree()

    assert "sort" not in snippets_fields


# -- self tests: the gate has to report every shape it judges --------------


def test_a_pair_that_agrees_produces_no_finding() -> None:
    # The counter sample of everything below. Without it a gate that reported
    # every tree as broken would pass all the failure tests as well.
    both = {"query", "titleOnly", "types", "since", "until"}

    assert findings(both, both) == []


def test_a_field_missing_from_the_excerpt_model_is_reported_with_both_sides_named() -> None:
    # The realistic accident, and the one the page pays for: somebody adds a
    # filter field to the candidate call and the excerpt call answers 422 for
    # every hit the page had already shown.
    found = findings({"query", "types", "language"}, {"query", "types"})

    assert len(found) == 1
    assert found[0].startswith("language")
    assert SEARCH_MODEL in found[0]


def test_a_field_that_only_the_excerpt_model_carries_is_reported_as_well() -> None:
    found = findings({"query"}, {"query", "highlightMode"})

    assert len(found) == 1
    assert found[0].startswith("highlightMode")
    assert SNIPPETS_MODEL in found[0]


def test_a_named_exception_produces_no_finding() -> None:
    # sort on one side and nothing on the other is the tree as it stands, and
    # the list is what makes that a decision instead of an oversight.
    assert findings({"query", "sort"}, {"query"}) == []


def test_a_model_that_could_not_be_read_is_a_finding_and_never_a_match() -> None:
    found = findings(set(), {"query"})

    assert found == [f"{SEARCH_MODEL} could not be read at all"]


def test_two_sort_lists_that_drifted_apart_are_reported_from_both_sides() -> None:
    found = order_findings(("relevance", "newest", "largest"), ("relevance", "newest", "oldest"))

    assert len(found) == 2
    assert any(line.startswith("largest") and SORT_FIELD in line for line in found)
    assert any(line.startswith("oldest") and SORT_TABLE in line for line in found)


def test_a_sort_list_that_could_not_be_read_is_a_finding() -> None:
    assert order_findings((), ("relevance",)) == [f"{SORT_FIELD} could not be read at all"]


def test_the_expressions_read_the_shapes_these_two_files_really_have() -> None:
    # Against the real shapes: a docstring with a colon in it, a comment above a
    # field, an annotation wrapped in list[...] and one that is not, and a
    # trailing assignment that is not a field of the wire at all.
    staged = (
        "class SearchRequest(BaseModel):\n"
        '    """Request body of the candidate call.\n'
        "\n"
        "    Note: a line of prose that carries a colon is not a field.\n"
        '    """\n'
        "\n"
        '    model_config = ConfigDict(extra="forbid")\n'
        "\n"
        "    query: str = Field(min_length=1)\n"
        "    # A closed set and never free text.\n"
        '    types: list[Literal["pdf", "images"]] = Field(default_factory=list)\n'
        '    sort: Literal["relevance", "newest"] = "relevance"\n'
        "    since: int | None = Field(default=None, ge=0)\n"
        "\n"
        "\n"
        "class Candidate(BaseModel):\n"
        "    fileId: int\n"
    )

    assert model_fields_of(staged, "SearchRequest") == {"query", "types", "sort", "since"}
    assert literal_values(staged, "SearchRequest", "sort") == ("relevance", "newest")
    assert literal_values(staged, "SearchRequest", "types") == ("pdf", "images")
    assert literal_values(staged, "SearchRequest", "limit") == ()
    assert model_fields_of(staged, "SnippetsRequest") == set()


def test_the_expression_reads_the_shape_the_engine_table_really_has() -> None:
    staged = (
        "SORT_MODES: Final[Mapping[str, Order | None]] = {\n"
        '    "relevance": None,\n'
        '    "newest": Order.Desc,\n'
        '    "oldest": Order.Asc,\n'
        "}\n"
    )

    assert sort_mode_names(staged) == ("relevance", "newest", "oldest")
    assert sort_mode_names("nothing of the sort in here") == ()
