"""Two schema generations at once, and the proof that no search falls between them.

Phase 18 raises the index schema from nine fields to thirteen. From the moment
that code ships until the rebuild of a given instance has run, two schema
generations are in the world at the same time, and every search on an instance
that has not rebuilt yet runs against the old one. This file is the argument
that those searches are safe, and it is made in two parts.

**The set inclusion.** ``parse_query_lenient`` is handed a list of field names,
and measured on tantivy 0.26.2 it answers a name the schema does not know with
``ValueError: Field `body_es` is not defined in the schema.`` The search path has
no branch for that: the exception leaves the query builder, the route answers
without a lexical half, and the search bar stays empty until somebody rebuilds.
So the whole question is whether the field list of the query can ever name a
field that a stock index lacks, and the answer is a set inclusion rather than an
integration test: the four names of ``LEGACY_PLAN.fields`` stand in both
generations, therefore no input can reach the failing path.

**The staged old index.** The inclusion is an argument about names. The second
half runs a real query against a real index of the old schema, because an
argument about names says nothing about the eight analyzer chains that
``index/open.py`` now registers over a schema that knows two body fields.

The fixtures for that index live in ``conftest.py``; the reason they are not
built from ``build_schema()`` is written there.

**What the third part was, and why it is gone.** Until phase 19 a syntax tree
guard stood at the bottom of this file. It read ``query/rewrite.py`` as text,
pulled the three module constants ``DEFAULT_FIELDS``, ``TITLE_ONLY_FIELDS`` and
``FIELD_BOOSTS`` out of its syntax tree and reported every body field in them
that a stock index does not have. It was written to be thrown away and it said
so: a check over constants has nothing left to check once the field list depends
on what the index says about itself, which is the whole point of phase 19. Plan
19-01 made those three constants one value, :class:`findling.query.rewrite.FieldPlan`,
so the guard lost its subject in the very commit that deleted it.

**What took its place**, named here because saying it in the same commit is the
handover condition the guard itself set: ``backend/tests/test_query_fields_plan.py``.
It is the stronger of the two statements, because it asks the engine instead of
the names. The field list and the boost mapping of a plan travel together into a
real ``parse_query_lenient`` call against a real index of each generation, and a
counter probe adds one boost on ``body_es`` so that the call the plan survives is
known to be a call that can fail.
"""

from __future__ import annotations

import pytest
from tantivy import Index

from conftest import FIXTURE_DOCUMENTS
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_BODY_ES,
    FIELD_BODY_IT,
    FIELD_BODY_NL,
    FIELD_BODY_PT,
    FIELDS,
)
from findling.query.rewrite import LEGACY_PLAN

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
    missing = sorted(set(LEGACY_PLAN.fields) - set(FIELDS_SCHEMA_1))
    assert not missing, f"the legacy plan searches {missing}, which an index of the old schema does not have"


def test_the_default_field_list_exists_in_the_new_schema() -> None:
    missing = sorted(set(LEGACY_PLAN.fields) - set(FIELDS))
    assert not missing, f"the legacy plan searches {missing}, which the current schema does not have"


def test_the_file_name_field_list_exists_in_the_old_schema() -> None:
    missing = sorted(set(LEGACY_PLAN.title_only) - set(FIELDS_SCHEMA_1))
    assert not missing, f"the legacy plan names {missing} for the file name filter, which the old schema lacks"


def test_the_boosted_field_list_exists_in_the_old_schema() -> None:
    # The boosts travel into the same call as the default fields, under their own
    # keyword, and a name in there is looked up in the schema just as the default
    # ones are. A boost for a field nobody searches would therefore be the same
    # ValueError as a default field for it.
    missing = sorted(set(LEGACY_PLAN.boosts) - set(FIELDS_SCHEMA_1))
    assert not missing, f"the legacy plan boosts {missing}, which an index of the old schema does not have"


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
    for field in sorted(set(LEGACY_PLAN.fields) | set(LEGACY_PLAN.title_only) | set(LEGACY_PLAN.boosts)):
        parsed, errors = schema_1_index.parse_query_lenient("vertrag", default_field_names=[field])

        assert errors == []
        assert parsed is not None
