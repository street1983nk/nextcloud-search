"""The field plan as one value, asked of the engine instead of of its names.

**What goes wrong.** ``Index.parse_query_lenient`` takes the field list under
``default_field_names`` and the weights under ``field_boosts``, and measured on
tantivy 0.26.2 it raises ``ValueError: Field `body_es` is not defined in the
schema.`` for a name it does not know in either of the two (19-RESEARCH
measurement M-1). The search path has no branch for that exception: it leaves
``build_query``, the route answers without its lexical half, and the search bar
of an instance that has not rebuilt yet stays empty until somebody rebuilds it.
Two halves held apart would therefore be two ways into that one failure, and only
one of them would look like the subject, because the message names a field and
the reflex looks for it in the field list.

**What this file proves.** That the two halves of a plan survive one real call
against a real index of each schema generation, and that the call they survive is
a call which can fail: the counter probe adds a single boost on ``body_es`` to
the very same arguments and expects the exception by field name.

This file is what took the place of the syntax tree guard that stood at the
bottom of ``test_schema_generations.py`` until phase 19. That guard read the
three module constants of ``query/rewrite.py`` out of the syntax tree and
compared names; plan 19-01 made those constants one value and the guard lost its
subject. The replacement is the stronger statement in the one way that matters
here, because what decides whether a search answers is tantivy and not a set.

**What this file does not prove.** Nothing about ranking, nothing about what a
plan computed from the stored marks of an instance will contain, and nothing
about the analyzer chains behind the fields. The first of those belongs to the
ranking probe, the second to the plans that compute a plan at all, and the third
to ``test_language_analyzers.py``.
"""

from __future__ import annotations

import pytest
from tantivy import Index

from findling.index.schema import FIELD_BODY_ES
from findling.query.rewrite import BODY_BOOST, LEGACY_PLAN


def test_the_legacy_plan_passes_the_old_index_as_one_value(schema_1_index: Index) -> None:
    # Both halves in one call, which is the shape build_query gives them. A plan
    # that is sound in its field list and unsound in its boosts is not a sound
    # plan, and asking the two halves separately would report precisely that
    # state as health.
    parsed, errors = schema_1_index.parse_query_lenient(
        "vertrag",
        default_field_names=list(LEGACY_PLAN.fields),
        field_boosts=dict(LEGACY_PLAN.boosts),
    )

    assert errors == []
    assert parsed is not None


def test_the_file_name_half_of_the_legacy_plan_passes_the_old_index(schema_1_index: Index) -> None:
    # The other answer of the same value, and it reaches the engine through the
    # same keyword. A plan whose file name list named a field of the build out
    # would break the search of everybody who ticks the Nextcloud filter for
    # "file name instead of content" and nobody else, which is the kind of
    # failure that gets reported as "the filter is broken".
    parsed, errors = schema_1_index.parse_query_lenient(
        "vertrag",
        default_field_names=list(LEGACY_PLAN.title_only),
        field_boosts=dict(LEGACY_PLAN.boosts),
    )

    assert errors == []
    assert parsed is not None


def test_a_boost_on_a_field_the_old_index_lacks_raises_like_a_field_name_does(schema_1_index: Index) -> None:
    # The counter probe, and it is what makes the two cases above cases at all.
    # The field list is the one that just passed, the single difference is one
    # entry in the other half, and the expectation is on the field name rather
    # than on the wording around it: the sentence tantivy builds is not ours and
    # may be rephrased, the field name in it is the finding.
    with pytest.raises(ValueError, match=FIELD_BODY_ES):
        schema_1_index.parse_query_lenient(
            "vertrag",
            default_field_names=list(LEGACY_PLAN.fields),
            field_boosts={**LEGACY_PLAN.boosts, FIELD_BODY_ES: BODY_BOOST["es"]},
        )


def test_the_boosts_of_the_legacy_plan_stay_inside_its_field_list() -> None:
    # 19-RESEARCH pitfall 1 written as the set statement it is. Inclusion and not
    # equality: a field may be searched without being weighted, and it then
    # counts at the weight tantivy gives an unboosted field. The reverse is the
    # accident this file is about, a weight for a field nothing searches, which
    # is at best dead and at worst the exception above.
    assert set(LEGACY_PLAN.boosts) <= set(LEGACY_PLAN.fields)


def test_the_legacy_plan_passes_the_index_of_the_new_generation_too(schema_2_index: Index) -> None:
    # The frozen plan has to go on working after the rebuild, because the rebuild
    # is not what changes which fields are searched: the plan is. The new schema
    # is a superset of the old one, so the four names still stand, and this case
    # is what would notice if a rebuild ever dropped one of them.
    parsed, errors = schema_2_index.parse_query_lenient(
        "vertrag",
        default_field_names=list(LEGACY_PLAN.fields),
        field_boosts=dict(LEGACY_PLAN.boosts),
    )

    assert errors == []
    assert parsed is not None
