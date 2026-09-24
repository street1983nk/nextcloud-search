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

**The second half of the file, since plan 19-03.** From that plan on a plan is
computed rather than frozen: ``findling.api.resources.field_plan_for`` reads the
two stored marks of a directory and answers what a bare word searches on it. The
cases below the divider hold every gate of that function against a real index of
the generation the marks claim, and each of the load bearing ones carries its
counter probe, because a gate that never refuses anything is green for a reason
that has nothing to do with the gate.

**What this file does not prove.** Nothing about ranking and nothing about the
analyzer chains behind the fields. The first belongs to the ranking probe of plan
19-04, the second to ``test_language_analyzers.py``.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from tantivy import Index

from findling.api.resources import field_plan_for
from findling.config import SCHEMA_VERSION
from findling.index.open import LANGUAGES_MARK, SCHEMA_MARK, expected_versions
from findling.index.schema import (
    BODY_FIELD,
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_BODY_ES,
    FIELD_NAME,
    FIELD_TITLE,
)
from findling.query.rewrite import BODY_BOOST, LEGACY_PLAN, build_query
from findling.store.repo import LEGACY_LANGUAGES, open_store

# The mark a directory carries once the rebuild of phase 18 has run on it. Read
# out of findling.config rather than written as "2", because a literal here would
# be the fourth spelling of one number and would go on claiming the current
# generation on the day the schema takes its next step.
CURRENT_SCHEMA = str(SCHEMA_VERSION)


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


# ---------------------------------------------------------------------------
# The computed plan, from here on. Everything above holds the frozen value of
# plan 19-01 against the engine; everything below holds the function that reads
# two marks off a directory and answers with a plan for that directory.
# ---------------------------------------------------------------------------


def test_a_stock_installation_gets_the_four_field_names_of_today(schema_1_index: Index) -> None:
    # The most important case of this file, and the promise the whole phase is
    # built around: an installation that has not rebuilt yet keeps the search it
    # had. Written as the literal four names rather than as an equality with
    # LEGACY_PLAN, because an equality would go on holding if somebody moved
    # both sides at once.
    plan = field_plan_for({SCHEMA_MARK: "1", LANGUAGES_MARK: "de,en"}, schema_1_index)

    assert plan.fields == (FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE)
    assert dict(plan.boosts) == dict(LEGACY_PLAN.boosts)
    assert plan.title_only == (FIELD_NAME,)


def test_the_computed_plan_of_a_stock_installation_goes_through_the_query_builder(schema_1_index: Index) -> None:
    # Stronger than the guard that fell in plan 19-01, and this is where the
    # strength sits: it is not the names of a plan that are held against a set,
    # it is the plan that was really computed going through the real build_query
    # against the real directory. An empty errors list and a query that is not
    # None together are "the search answers"; either one alone is not.
    plan = field_plan_for({SCHEMA_MARK: "1", LANGUAGES_MARK: "de,en"}, schema_1_index)

    rewritten = build_query(schema_1_index, "vertrag", plan=plan)

    assert rewritten.errors == []
    assert rewritten.query is not None


@pytest.mark.parametrize("stored", ["3", "", "abc", "UNKNOWN_VERSION"])
def test_a_schema_generation_this_code_never_saw_is_no_permission(stored: str, schema_2_index: Index) -> None:
    # The gate falls closed, in the shape of store.repo._schema_is_legacy and for
    # its reason: an index whose schema names a generation nobody wrote could be
    # any schema, and naming a field it does not carry is the ValueError the
    # first half of this file provokes.
    assert field_plan_for({SCHEMA_MARK: stored, LANGUAGES_MARK: "de,en,es"}, schema_2_index) == LEGACY_PLAN


def test_a_directory_without_a_schema_mark_is_no_permission_either(schema_2_index: Index) -> None:
    # An absent mark and an unknown one are one case here, unlike the language
    # mark below, where absence is evidence rather than a gap: no release up to
    # 1.2.0 could write a body field outside the legacy pair, while every release
    # since the beginning wrote a schema mark.
    assert field_plan_for({LANGUAGES_MARK: "de,en,es"}, schema_2_index) == LEGACY_PLAN


@pytest.mark.parametrize("marks", [{SCHEMA_MARK: CURRENT_SCHEMA}, {SCHEMA_MARK: CURRENT_SCHEMA, LANGUAGES_MARK: ""}])
def test_a_rebuilt_directory_without_a_language_mark_carries_the_legacy_pair(
    marks: dict[str, str],
    schema_2_index: Index,
) -> None:
    # One reading of the language mark and not a second one: absent or empty
    # means LEGACY_LANGUAGES, exactly as store.repo._languages_are_legacy and
    # index.rebuild._new_language_count read it.
    plan = field_plan_for(marks, schema_2_index)

    assert plan.fields == LEGACY_PLAN.fields
    assert {BODY_FIELD[code] for code in LEGACY_LANGUAGES} <= set(plan.fields)


def test_a_spanish_instance_searches_its_body_field_below_the_english_one(schema_2_index: Index) -> None:
    # Success criterion 3 of the roadmap, in the one shape it is provable in: the
    # weight of a build out language lies below body_en. What it does not claim
    # is that the weight settles the ranking, because tantivy sums the field
    # contributions (19-RESEARCH measurement M-3); that is the subject of 19-04.
    plan = field_plan_for({SCHEMA_MARK: CURRENT_SCHEMA, LANGUAGES_MARK: "de,en,es"}, schema_2_index)

    assert plan.fields == (FIELD_BODY_DE, FIELD_BODY_EN, FIELD_BODY_ES, FIELD_NAME, FIELD_TITLE)
    assert plan.boosts[FIELD_BODY_ES] < plan.boosts[FIELD_BODY_EN]

    rewritten = build_query(schema_2_index, "contrato", plan=plan)

    assert rewritten.errors == []
    assert rewritten.query is not None


def test_the_german_body_field_is_no_special_case_of_the_plan(schema_2_index: Index) -> None:
    # 19-RESEARCH pitfall 7. body_de is written unconditionally, which makes it
    # look like a fixed entry, and it is not: an instance running Spanish alone
    # did not mean a question against the German chain, and a hit out of it is a
    # hit nobody can explain.
    plan = field_plan_for({SCHEMA_MARK: CURRENT_SCHEMA, LANGUAGES_MARK: "es"}, schema_2_index)

    assert plan.fields == (FIELD_BODY_ES, FIELD_NAME, FIELD_TITLE)
    assert FIELD_BODY_DE not in plan.fields
    assert FIELD_BODY_DE not in plan.boosts


def test_a_language_code_the_schema_does_not_know_is_passed_over(schema_2_index: Index) -> None:
    # A mark written by a newer release, or by a hand. The codes that have a
    # field keep theirs; the one that has none contributes nothing, because the
    # field list is built by walking BODY_FIELD and never the mark.
    plan = field_plan_for({SCHEMA_MARK: CURRENT_SCHEMA, LANGUAGES_MARK: "es,zz"}, schema_2_index)

    assert plan.fields == (FIELD_BODY_ES, FIELD_NAME, FIELD_TITLE)


def test_a_language_mark_that_names_nothing_known_falls_back(schema_2_index: Index) -> None:
    # The counter probe of the case above, and the reason it matters: a plan of
    # name and title alone would answer every content search with nothing, which
    # is an empty search bar arriving by a second road.
    assert field_plan_for({SCHEMA_MARK: CURRENT_SCHEMA, LANGUAGES_MARK: "zz"}, schema_2_index) == LEGACY_PLAN


def test_the_mark_and_not_the_directory_decides_which_fields_are_searched(schema_2_index: Index) -> None:
    # The counter probe of the stock installation case, and without it that one
    # would be green for a gate that never looks at anything. The directory here
    # carries all thirteen fields, which the second half of this case proves
    # against the engine, and the plan still comes back with the four of 1.2.0,
    # because the mark says the rebuild has not run.
    plan = field_plan_for({SCHEMA_MARK: "1", LANGUAGES_MARK: "de,en,es"}, schema_2_index)

    assert plan == LEGACY_PLAN
    assert FIELD_BODY_ES not in plan.fields

    parsed, errors = schema_2_index.parse_query_lenient("contrato", default_field_names=[FIELD_BODY_ES])

    assert errors == []
    assert parsed is not None


def test_a_state_database_beside_an_older_directory_falls_back_and_says_so(
    schema_1_index: Index,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The one state the mark cannot see: a state.db restored from a backup next
    # to an index directory of the older generation. The mark promises thirteen
    # fields, the directory holds nine, and the probe at the directory itself is
    # what catches it. A warning and not the debug line of filled_languages,
    # because the two halves of this volume do not belong together.
    with caplog.at_level(logging.WARNING, logger="findling.api.resources"):
        plan = field_plan_for({SCHEMA_MARK: CURRENT_SCHEMA, LANGUAGES_MARK: "de,en,es"}, schema_1_index)

    assert plan == LEGACY_PLAN

    lines = [record.getMessage() for record in caplog.records if record.levelno >= logging.WARNING]

    assert len(lines) == 1
    assert FIELD_BODY_ES in lines[0]
    assert "ValueError" in lines[0]
    # The line carries the field name and the type of the exception, and neither
    # a path nor anything a user typed: a path is a file name, and the function
    # that wrote this line is never handed a search term at all.
    assert "/" not in lines[0]
    assert chr(92) not in lines[0]


@pytest.mark.parametrize(
    "languages",
    ["de", "en", "es", "it", "nl", "pt", ",".join(LEGACY_LANGUAGES), ",".join(BODY_FIELD)],
)
def test_every_language_set_weighs_exactly_the_fields_it_searches(languages: str, schema_2_index: Index) -> None:
    # 19-RESEARCH pitfall 1 as the set statement of the computed plan, and here
    # it is equality rather than the inclusion the frozen plan is held to: a
    # weight for a field nothing searches is the ValueError of the first half of
    # this file, and a searched field without a weight would be a language whose
    # rank order nobody ever decided.
    plan = field_plan_for({SCHEMA_MARK: CURRENT_SCHEMA, LANGUAGES_MARK: languages}, schema_2_index)

    assert set(plan.boosts) == set(plan.fields)

    rewritten = build_query(schema_2_index, "vertrag", plan=plan)

    assert rewritten.errors == []
    assert rewritten.query is not None


def test_the_marks_of_a_real_state_database_are_the_ones_the_plan_reads(
    tmp_path: Path,
    schema_2_index: Index,
) -> None:
    # The key names of a hand built mapping agree with themselves whatever they
    # are called. This case takes the marks out of a real state.db, seeded the
    # way every volume is seeded and then stamped the way a rebuild stamps it, so
    # that a rename on either side is a red case here rather than a plan that
    # quietly falls back on every installation in the field.
    store = open_store(tmp_path / "state.db", meta=expected_versions("a-digest", "de,en,es"))
    seeded = store.read_meta()
    # The stamp of findling.index.rebuild.stamp_after_swap, and the only moment
    # the language mark is ever written. The seed above cannot write it: it would
    # put the wish of a container down as a fact about a directory, which is
    # threat T-18-05-01 of phase 18, and store.repo._DEFAULT_META therefore skips
    # the key by name. The assertion below is that omission, read out of the
    # database rather than out of the source.
    store.write_meta(LANGUAGES_MARK, "de,en,es")
    stamped = store.read_meta()
    store.close()

    assert LANGUAGES_MARK not in seeded
    assert seeded[SCHEMA_MARK] == CURRENT_SCHEMA
    assert field_plan_for(seeded, schema_2_index).fields == LEGACY_PLAN.fields

    plan = field_plan_for(stamped, schema_2_index)

    assert plan.fields == (FIELD_BODY_DE, FIELD_BODY_EN, FIELD_BODY_ES, FIELD_NAME, FIELD_TITLE)
