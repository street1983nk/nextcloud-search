"""Two schema generations at once, and the proof that no search falls between them.

Phase 18 raises the index schema from nine fields to thirteen. From the moment
that code ships until the rebuild of a given instance has run, two schema
generations are in the world at the same time, and every search on an instance
that has not rebuilt yet runs against the old one. This file is the argument
that those searches are safe, and it is made in three parts.

**The set inclusion.** ``parse_query_lenient`` is handed a list of field names,
and measured on tantivy 0.26.2 it answers a name the schema does not know with
``ValueError: Field `body_es` is not defined in the schema.`` The search path has
no branch for that: the exception leaves the query builder, the route answers
without a lexical half, and the search bar stays empty until somebody rebuilds.
So the whole question is whether the field list of the query can ever name a
field that a stock index lacks, and the answer is a set inclusion rather than an
integration test: the four names of ``DEFAULT_FIELDS`` stand in both generations,
therefore no input can reach the failing path.

**The staged old index.** The inclusion is an argument about names. The second
half runs a real query against a real index of the old schema, because an
argument about names says nothing about the eight analyzer chains that
``index/open.py`` now registers over a schema that knows two body fields.

The fixtures for that index live in ``conftest.py``; the reason they are not
built from ``build_schema()`` is written there.

**The syntax tree guard.** The two halves above say that the field list is safe
today. The guard at the bottom of this file says it will still be safe after the
next edit: it reads ``query/rewrite.py`` as text, pulls the three field lists out
of its syntax tree and reports every body field in them that a stock index does
not have. It reads rather than imports, so a module that does not even import
any more is a red gate and not an error in collection, and it fails closed, so a
list it could not find is a finding rather than a quiet zero.

**Why the guard is written to be thrown away.** Phase 19 turns ``DEFAULT_FIELDS``
and ``FIELD_BOOSTS`` into functions of the stored ``schema_version`` mark, and
from that moment a check over constants has nothing left to check: the answer
depends on what the index says about itself, which is the whole point of the
phase. So this guard is not a rule for all time, it is the phase boundary written
as code. It holds the field list still for exactly as long as phase 18 says it
must hold still, and whoever deletes it in phase 19 will have to say in the same
commit what took its place.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tantivy import Index

from conftest import FIXTURE_DOCUMENTS
from findling.index import schema as index_schema
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_BODY_ES,
    FIELD_BODY_IT,
    FIELD_BODY_NL,
    FIELD_BODY_PT,
    FIELDS,
)
from findling.query.rewrite import DEFAULT_FIELDS, FIELD_BOOSTS, TITLE_ONLY_FIELDS

# The index schema of every release up to 1.2.0, written out and frozen.
#
# It is a literal and it may not become anything else. Reading these names out of
# ``findling.index.schema`` would make every assertion below a tautology: that
# module builds the new schema, so a list derived from it would grow whichever
# field the new schema grew, and the inclusion would stay green precisely in the
# case it exists to catch. The nine names are the ones of commit ca739b1~1, the
# last state of the schema before plan 18-01 added the four body fields.
#
# A name disappears from this tuple only when no instance anywhere can still be
# carrying an index that has it, which for a released app means never.
FIELDS_SCHEMA_1: tuple[str, ...] = (
    "file_id",
    "storage_id",
    "name",
    "title",
    "path",
    "ext",
    "body_de",
    "body_en",
    "mtime",
)

# The prefix that marks a body field. The four fields plan 18-01 added all carry
# it, and so do the two that were there before, which is what makes it the right
# thing to test a name against: a body field is the one kind of field a language
# build out adds, and therefore the one kind that can drift out of the old schema.
BODY_PREFIX = "body_"


def test_the_frozen_list_has_the_nine_names_of_the_old_schema() -> None:
    # The guard on the guard. A tuple that lost a name would make every inclusion
    # below stricter than reality and would send somebody hunting for a problem
    # that is not there; a tuple that gained one would make them all weaker.
    assert len(FIELDS_SCHEMA_1) == 9
    assert len(set(FIELDS_SCHEMA_1)) == 9


def test_the_new_schema_is_a_superset_of_the_old_one() -> None:
    # What makes phase 18 an extension rather than a replacement, and the reason
    # an old index can still be searched at all. A field that disappeared from
    # the new schema would mean the opposite problem of the one this file is
    # about: the rebuild would drop a column the query still names.
    lost = sorted(set(FIELDS_SCHEMA_1) - set(FIELDS))
    assert not lost, f"the new schema no longer has {lost}, which every stock index carries"


def test_the_default_field_list_exists_in_the_old_schema() -> None:
    missing = sorted(set(DEFAULT_FIELDS) - set(FIELDS_SCHEMA_1))
    assert not missing, f"DEFAULT_FIELDS names {missing}, which an index of the old schema does not have"


def test_the_default_field_list_exists_in_the_new_schema() -> None:
    missing = sorted(set(DEFAULT_FIELDS) - set(FIELDS))
    assert not missing, f"DEFAULT_FIELDS names {missing}, which the current schema does not have"


def test_the_file_name_field_list_exists_in_the_old_schema() -> None:
    missing = sorted(set(TITLE_ONLY_FIELDS) - set(FIELDS_SCHEMA_1))
    assert not missing, f"TITLE_ONLY_FIELDS names {missing}, which an index of the old schema does not have"


def test_the_boosted_field_list_exists_in_the_old_schema() -> None:
    # The boosts travel into the same call as the default fields, under their own
    # keyword, and a name in there is looked up in the schema just as the default
    # ones are. A boost for a field nobody searches would therefore be the same
    # ValueError as a default field for it.
    missing = sorted(set(FIELD_BOOSTS) - set(FIELDS_SCHEMA_1))
    assert not missing, f"FIELD_BOOSTS names {missing}, which an index of the old schema does not have"


def test_the_body_fields_of_the_language_build_out_are_the_ones_the_old_schema_lacks() -> None:
    # Names the gap rather than leaving it implied. These four are what the query
    # may not reach for while a stock index is still in the field, and phase 19 is
    # the phase that is allowed to reach for them, once the stored schema_version
    # says which generation is on disk.
    absent = sorted(field for field in FIELDS if field.startswith(BODY_PREFIX) and field not in FIELDS_SCHEMA_1)
    assert absent == sorted([FIELD_BODY_ES, FIELD_BODY_IT, FIELD_BODY_NL, FIELD_BODY_PT])

    # And the two that are in both, so that a body field which quietly left the
    # old schema cannot hide inside the difference above.
    assert {FIELD_BODY_DE, FIELD_BODY_EN} <= set(FIELDS_SCHEMA_1)


# -- the staged old index ----------------------------------------------------


def test_the_old_index_rejects_a_body_field_it_does_not_have(schema_1_index: Index) -> None:
    # The failure this whole file is about, provoked once so that the inclusions
    # above are known to be guarding something real rather than nothing at all.
    # Lenient parsing is lenient about the query text; a field name is not text.
    for field in (FIELD_BODY_ES, FIELD_BODY_IT, FIELD_BODY_NL, FIELD_BODY_PT):
        with pytest.raises(ValueError, match=field):
            schema_1_index.parse_query_lenient("vertrag", default_field_names=[field])


def test_the_old_index_carries_terms_in_the_german_body(schema_1_index: Index) -> None:
    # The other side of the same fixture. Without it the case above would also be
    # green for an index that holds no documents, or whose German chain was never
    # registered, and neither of those is a stock installation.
    parsed, errors = schema_1_index.parse_query_lenient("vertrag", default_field_names=[FIELD_BODY_DE])

    assert errors == []
    assert len(schema_1_index.searcher().search(parsed, FIXTURE_DOCUMENTS * 2).hits) == FIXTURE_DOCUMENTS


def test_the_old_index_accepts_every_field_of_the_query(schema_1_index: Index) -> None:
    # The inclusion above, asked of the engine instead of of a set. It is the same
    # statement twice on purpose: the sets say the names match, this says tantivy
    # agrees, and a schema whose fields were spelled differently on disk than in
    # the constants would come apart exactly here.
    for field in sorted(set(DEFAULT_FIELDS) | set(TITLE_ONLY_FIELDS) | set(FIELD_BOOSTS)):
        parsed, errors = schema_1_index.parse_query_lenient("vertrag", default_field_names=[field])

        assert errors == []
        assert parsed is not None


# -- the syntax tree guard over the three field lists ------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]

REWRITE_RELATIVE = "backend/src/findling/query/rewrite.py"
REWRITE_MODULE = REPO_ROOT / REWRITE_RELATIVE

# The three names that end up in a ``parse_query_lenient`` call, two as the
# default fields and one as the boosts. They are spelled here and read out of the
# syntax tree there; the module is never imported for this, because an import
# would answer with the value a broken module could not even produce.
FIELD_LISTS = ("DEFAULT_FIELDS", "TITLE_ONLY_FIELDS", "FIELD_BOOSTS")


def _field_constants() -> dict[str, str]:
    """Every ``FIELD_*`` constant of the schema module, by its identifier.

    This is what lets ``FIELD_BODY_ES`` and ``"body_es"`` be the same finding.
    The field lists are written with the constants today, a future edit may well
    paste a literal, and a guard that only understood one of the two spellings
    would be walked past by the other without anybody meaning to.

    Read off the module rather than listed here on purpose, and it is not the
    tautology that ``FIELDS_SCHEMA_1`` would be if it were read the same way:
    this mapping answers "what does this identifier stand for", never "which
    fields exist". A constant that moved would resolve to its new value and the
    comparison against the frozen nine names would go on unchanged.
    """
    return {
        name: value
        for name, value in vars(index_schema).items()
        if name.startswith("FIELD_") and isinstance(value, str)
    }


def _entries(value: ast.expr) -> list[ast.expr | None] | None:
    """The expressions a field list is built from, or None if it is not one.

    A mapping contributes its keys, because that is where a field name stands in
    ``FIELD_BOOSTS``. A ``None`` key is what ``**other`` parses to and is handed
    on as it is, so that it becomes an unresolvable entry below rather than a
    silently skipped one.
    """
    if isinstance(value, ast.Dict):
        return list(value.keys)
    if isinstance(value, ast.List | ast.Tuple | ast.Set):
        return list(value.elts)
    return None


def _field_name(entry: ast.expr | None, constants: dict[str, str]) -> str | None:
    """The field name an entry stands for, or None when the guard cannot tell."""
    if isinstance(entry, ast.Constant) and isinstance(entry.value, str):
        return entry.value
    if isinstance(entry, ast.Name):
        return constants.get(entry.id)
    return None


def body_fields_outside_the_old_schema(source: str, filename: str = REWRITE_RELATIVE) -> list[str]:
    """Body fields named by the query field lists that a stock index does not have.

    Not a tautology, a ratchet. The set inclusions further up read the values the
    module produces, so they would follow the module wherever it went if somebody
    rewrote the list from constants into something computed; this one reads the
    three assignments as they stand in the file and refuses everything it cannot
    resolve to a plain field name.

    It fails closed in three places, and each of them was a way to make the gate
    look healthy while it checked nothing: a list that is not in the tree at all,
    a list that is not a list, and an entry that is neither a string nor a known
    field constant. All three come back as findings.
    """
    tree = ast.parse(source, filename=filename)
    constants = _field_constants()

    # Module level assignments, annotated (``X: Final = [...]``) or plain. The
    # first one wins: a name that is assigned twice is read the way the reader of
    # the file reads it, from the top.
    assigned: dict[str, ast.expr] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            assigned.setdefault(node.target.id, node.value)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned.setdefault(target.id, node.value)

    findings: list[str] = []
    for list_name in FIELD_LISTS:
        value = assigned.get(list_name)
        if value is None:
            findings.append(f"{filename} does not assign {list_name}, so this gate read nothing")
            continue
        entries = _entries(value)
        if entries is None:
            findings.append(f"{list_name} in {filename} is neither a sequence nor a mapping, so this gate read nothing")
            continue
        for entry in entries:
            field = _field_name(entry, constants)
            if field is None:
                findings.append(f"{list_name} in {filename} carries an entry this gate cannot read as a field name")
                continue
            if field.startswith(BODY_PREFIX) and field not in FIELDS_SCHEMA_1:
                findings.append(f"{list_name} in {filename} names {field}, which an index of the old schema lacks")
    return findings


def test_the_query_field_lists_name_no_field_the_old_schema_lacks() -> None:
    findings = body_fields_outside_the_old_schema(REWRITE_MODULE.read_text(encoding="utf-8"))

    assert findings == []


# The staged samples. Without them a deleted function body would report zero
# findings over zero field lists and pass for a healthy gate.

_CLEAN_SAMPLE = """\
DEFAULT_FIELDS: Final = [FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE]
TITLE_ONLY_FIELDS: Final = [FIELD_NAME]
FIELD_BOOSTS: Final = {FIELD_NAME: 3.0, FIELD_TITLE: 2.0, FIELD_BODY_DE: 1.0, FIELD_BODY_EN: 0.8}
"""

_SAMPLE_WITH_A_NEW_BODY_CONSTANT = """\
DEFAULT_FIELDS: Final = [FIELD_BODY_DE, FIELD_BODY_EN, FIELD_BODY_ES, FIELD_NAME, FIELD_TITLE]
TITLE_ONLY_FIELDS: Final = [FIELD_NAME]
FIELD_BOOSTS: Final = {FIELD_NAME: 3.0, FIELD_TITLE: 2.0, FIELD_BODY_DE: 1.0, FIELD_BODY_EN: 0.8}
"""

_SAMPLE_WITH_A_NEW_BODY_LITERAL = """\
DEFAULT_FIELDS: Final = [FIELD_BODY_DE, FIELD_BODY_EN, "body_es", FIELD_NAME, FIELD_TITLE]
TITLE_ONLY_FIELDS: Final = [FIELD_NAME]
FIELD_BOOSTS: Final = {FIELD_NAME: 3.0, FIELD_TITLE: 2.0, FIELD_BODY_DE: 1.0, FIELD_BODY_EN: 0.8}
"""

_SAMPLE_WITH_A_BOOSTED_NEW_BODY_FIELD = """\
DEFAULT_FIELDS: Final = [FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE]
TITLE_ONLY_FIELDS: Final = [FIELD_NAME]
FIELD_BOOSTS: Final = {FIELD_NAME: 3.0, FIELD_BODY_DE: 1.0, FIELD_BODY_PT: 0.8}
"""

_SAMPLE_WITH_A_COMPUTED_LIST = """\
DEFAULT_FIELDS: Final = fields_for(schema_version)
TITLE_ONLY_FIELDS: Final = [FIELD_NAME]
FIELD_BOOSTS: Final = {FIELD_NAME: 3.0, FIELD_BODY_DE: 1.0}
"""


def test_the_gate_is_quiet_on_a_staged_clean_module() -> None:
    assert body_fields_outside_the_old_schema(_CLEAN_SAMPLE, "staged/clean.py") == []


def test_the_gate_sees_a_new_body_field_written_as_a_constant() -> None:
    findings = body_fields_outside_the_old_schema(_SAMPLE_WITH_A_NEW_BODY_CONSTANT, "staged/constant.py")

    assert len(findings) == 1
    assert "body_es" in findings[0]
    assert "DEFAULT_FIELDS" in findings[0]


def test_the_gate_sees_the_same_field_written_as_a_literal() -> None:
    # The same defect in the other spelling, and it has to read the same. A gate
    # that only understood the constants would be silent the day somebody pastes
    # the string, which is the more likely of the two edits.
    findings = body_fields_outside_the_old_schema(_SAMPLE_WITH_A_NEW_BODY_LITERAL, "staged/literal.py")

    assert len(findings) == 1
    assert "body_es" in findings[0]


def test_the_gate_reads_the_keys_of_the_boost_mapping() -> None:
    findings = body_fields_outside_the_old_schema(_SAMPLE_WITH_A_BOOSTED_NEW_BODY_FIELD, "staged/boosts.py")

    assert len(findings) == 1
    assert "body_pt" in findings[0]
    assert "FIELD_BOOSTS" in findings[0]


def test_the_gate_fails_closed_when_a_field_list_is_gone() -> None:
    # The empty module is the shape of every accident that removes the subject:
    # a renamed constant, a moved module, a file that was split in two. Three
    # findings, one per list, rather than the zero that would look like health.
    findings = body_fields_outside_the_old_schema("", "staged/empty.py")

    assert len(findings) == len(FIELD_LISTS)
    for list_name in FIELD_LISTS:
        assert any(list_name in finding for finding in findings)


def test_the_gate_fails_closed_when_a_field_list_stops_being_a_list() -> None:
    # This is what phase 19 looks like from here, and the gate is meant to fire
    # on it. The field list becomes a function of the stored schema_version, the
    # guard can no longer read it, and it says so instead of going quiet. The
    # commit that makes that change is the commit that has to replace this file.
    findings = body_fields_outside_the_old_schema(_SAMPLE_WITH_A_COMPUTED_LIST, "staged/computed.py")

    assert len(findings) == 1
    assert "DEFAULT_FIELDS" in findings[0]
