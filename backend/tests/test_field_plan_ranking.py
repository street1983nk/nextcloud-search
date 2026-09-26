"""The ranking under six body fields: what the weights of the build out languages carry.

**What goes wrong.** tantivy does not take the best field of a document, it sums
the contribution of every field the document matches in. A document that answers
a question through five chains therefore collects five scores while a better
document that answers it through one collects one, and ``field_boosts`` damps
that sum rather than removing it. Measured on tantivy 0.26.2 (19-RESEARCH
measurement M-3), five body fields, document 1 filled in all five, document 2
only in the English one, the same question in every row:

    only body_en searched           doc 1 0.1823   doc 2 0.1823   ratio  1.0
    five fields, every boost 1.0    doc 1 2.1500   doc 2 0.1823   ratio 11.8
    five fields, en 0.8 / new 0.6   doc 1 1.3264   doc 2 0.1459   ratio  9.1
    five fields, en 0.8 / new 0.2   doc 1 0.5394   doc 2 0.1459   ratio  3.7

Success criterion 3 of the roadmap reads "a hit in several language fields does
not push itself in front of a better English hit" and gives the weights as its
reason. Those four lines are why the reason does not carry the claim on its own,
and why nothing below is written as if it did.

**The real case, and it is milder than the table.** The same text goes into ALL
switched on body fields (``index/writer.py:286-293``), so the multi field
multiplication applies to every document rather than to some, and in a comparison
of two documents it largely cancels out. What does not cancel is the part the
chains disagree about: a word every chain passes through unchanged collects one
contribution per field, a word only three chains put on the term of the question
collects three. The probe below is built out of exactly that disagreement,
because that is the only place the distortion lives.

**What this file proves.** Four things, and the last two are what make the
second one mean anything.

1. The weights of the four build out languages lie below ``body_en``, and
   ``body_en`` lies below ``body_de``. Not only in the shipped table but in every
   plan a directory can ask for, which is the literal promise of success
   criterion 3 and the cheap half of this file.
2. The probe index really holds the disagreement it claims to hold: three
   documents, six filled body fields, and one question that the German, English
   and Dutch chains put on the first document while the Spanish, Italian and
   Portuguese chains put it on the second. The distractor is asserted to be in
   the index and asserted not to answer the question, because a third document
   that is missing looks exactly like a third document that keeps quiet.
3. On that index and at the weights that ship, the better English hit stands in
   front of the document that answers the same question through three build out
   chains. Read off a real search through ``build_query`` and a real plan out of
   ``field_plan_for``, not off a score added up by hand.
4. With the four build out weights raised to 1.0 that order turns over. Without
   this run the third statement would be just as green on an index where the
   second document never answers the question at all, which is the one way a
   ranking assertion is worth nothing.

**The number this file was also written for.** ``TIPPING_BOOST`` below is the
weight at which statement 3 stops holding on this probe, found by a sweep and
not by an estimate. Phase 22 weighed a different query shape against the
summation described above, and REQUIREMENTS MESS-09 bound that decision to a
measurement on real data; this is the figure it started from, and plan 19-09
carries it into ``docs/language-analyzers.md`` so that nobody has to look for it.

**What this file does not prove.** Nothing about an installation. Three documents
are not a corpus, and ``TIPPING_BOOST`` is a property of this probe rather than a
threshold of the product. It proves nothing about the analyzer chains themselves,
which is ``test_language_analyzers.py``, and nothing about which fields a plan
names, which is ``test_query_fields_plan.py``. It prepares no change of query
shape either, and none is coming: per word ``disjunction_max`` was measured and
rejected on 2026-09-26 (MESS-09, plan 22-10). On the 52,137 files of the v1.3
measurement box the median RBO@10 against the legacy plan was 0.9531 for the
sum, 0.8399 for dismax at tie 0.0 and 0.9633 at tie 0.1, and the rule fixed
before the trip asked for at least 0.05 above the sum. The summation measured
here is therefore the shipped behaviour, and these four statements guard it.
Source: ``docs/measurements/2026-09-v13-messung/``, section 6.10 of its README.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator
from pathlib import Path
from typing import Final, NamedTuple

import pytest
from tantivy import Document, Index

from findling.api.resources import field_plan_for
from findling.config import SCHEMA_VERSION, SUPPORTED_LANGUAGES
from findling.index.open import LANGUAGES_MARK, SCHEMA_MARK, open_index
from findling.index.schema import (
    BODY_FIELD,
    FIELD_BODY_EN,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)
from findling.query.rewrite import BODY_BOOST, FieldPlan, build_query
from findling.store.repo import LEGACY_LANGUAGES

# The same constituent list the rest of the suite opens indexes with, so the one
# expensive chain of the process, the German automaton, is built once for the
# whole session and this module pays nothing for it.
CONSTITUENTS: Final = (
    (Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt").read_text(encoding="utf-8").split()
)

CURRENT_SCHEMA: Final = str(SCHEMA_VERSION)

# The four languages of the v1.3 build out, read out of the two lists that
# already exist rather than spelled a third time. LEGACY_LANGUAGES is the pair
# every release up to 1.2.0 searched; whatever is in the supported set and not in
# that pair is what this phase added and what these weights are about.
BUILD_OUT: Final = tuple(code for code in SUPPORTED_LANGUAGES if code not in LEGACY_LANGUAGES)

# MEASURED 2026-09-24 against tantivy 0.26.2, by the sweep in
# test_the_boost_at_which_the_ranking_turns_over_is_this_one: one search per
# hundredth between 0.00 and 1.00, the four build out weights moved together and
# everything else held still. Below this value the better English hit stands in
# front, at this value and above it the three chain hit does.
#
# What it is good for. The shipped 0.6 sits 0.21 below the edge on this probe, so
# the promise of success criterion 3 holds here with room rather than by a hair,
# and the counter probe at 1.0 is above the edge, so it really does turn the
# order over instead of failing to notice that it could not. Phase 22 weighed
# Query.disjunction_max_query against the summation this file measures, on real
# data as REQUIREMENTS MESS-09 demands, and rejected it on 2026-09-26 (see the
# module docstring); the summation stays, and so does this figure as its guard.
#
# What it is not. Three documents in a temporary directory. The edge moves with
# the length of the texts and with how many chains reach each document, so this
# is the order of magnitude and the direction, not a constant of the product.
TIPPING_BOOST: Final = 0.81

# The resolution of that sweep. A hundredth is finer than any weight this project
# ships and coarse enough that the whole series is a handful of searches on a
# three document index.
SWEEP_STEPS: Final = 100

# The question, and the two forms the probe documents carry it in. Measured with
# the shipped chains on 2026-09-24:
#
#   "document"  is what is typed. The German, English and Dutch chains put it on
#               the term "document"; the Spanish, Italian and Portuguese chains
#               leave it as it stands.
#   "documents" is what the English note carries. de, en and nl put it on that
#               same term "document", es, it and pt do not.
#   "documento" is what the Spanish note carries. es, it and pt put it on
#               "document", de, en and nl do not.
#
# So one question, two documents, and six chains that split three against three.
# That is the disagreement the docstring above calls the only place where the
# distortion lives, and it is why the pair is these two words and not a pair
# somebody liked the sound of.
QUESTION: Final = "document"

# A word that stands in the distractor and nowhere else, so that "the third
# document is in the index" is a measurement rather than an assumption.
DISTRACTOR_QUESTION: Final = "agreement"

ENGLISH_HIT: Final = 1
MULTI_CHAIN_HIT: Final = 2
DISTRACTOR: Final = 3


class Probe(NamedTuple):
    """One document of the probe index: the three text fields a search can reach."""

    name: str
    title: str
    body: str


# Neither the file name nor the title of any of the three carries the question.
# They weigh 3.0 and 2.0, so a stray "document" in one of them would settle the
# ranking on its own and the body fields, which are the subject here, would never
# be heard. A case below asserts it rather than this comment claiming it.
DOCUMENTS: Final = {
    ENGLISH_HIT: Probe(
        name="lease-note.txt",
        title="Signed lease",
        body="The signed documents of the lease are attached to this message.",
    ),
    MULTI_CHAIN_HIT: Probe(
        name="nota-arrendamiento.txt",
        title="Contrato de arrendamiento",
        body="Adjuntamos el documento del contrato de arrendamiento para su revision.",
    ),
    DISTRACTOR: Probe(
        name="reminder.txt",
        title="Monthly reminder",
        body="The lease agreement runs for another three months without any change.",
    ),
}


@pytest.fixture(scope="module")
def probe_index(tmp_path_factory: pytest.TempPathFactory) -> Index:
    """The probe index: three documents, the same text in all six body fields.

    Through ``open_index`` and never through the tantivy constructor, because
    opening is registering and the guard of ``test_index_open.py`` runs over the
    whole package for exactly that reason; a test module holds the same line.

    Field by field and never through keyword arguments: measured, a keyword built
    document puts an I64 into the U64 column of ``file_id`` and the indexing
    thread of tantivy panics after the Python call has already returned.

    The body goes into every one of the six fields, the way ``index/writer.py``
    writes it on an installation that runs all six languages. A probe that filled
    one field per document would be measuring a shape nobody ships and would make
    the multi field multiplication look far larger than it is.
    """
    index = open_index(tmp_path_factory.mktemp("field-plan-ranking"), CONSTITUENTS)
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    for file_id, probe in DOCUMENTS.items():
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, probe.name)
        document.add_text(FIELD_TITLE, probe.title)
        for field in BODY_FIELD.values():
            document.add_text(field, probe.body)
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    index.reload()
    return index


def _language_sets() -> Iterator[tuple[str, ...]]:
    """Every non empty language set a directory can carry, shortest first."""
    for size in range(1, len(SUPPORTED_LANGUAGES) + 1):
        yield from itertools.combinations(SUPPORTED_LANGUAGES, size)


def _plan_for(index: Index, languages: tuple[str, ...]) -> FieldPlan:
    """The plan this directory really answers with for that language set.

    Through ``field_plan_for`` and not assembled here, so that what is asserted
    below is the plan an installation gets and not a second reading of the same
    table.
    """
    return field_plan_for({SCHEMA_MARK: CURRENT_SCHEMA, LANGUAGES_MARK: ",".join(languages)}, index)


def _shipped_plan(index: Index) -> FieldPlan:
    """The plan of an installation that runs all six languages."""
    return _plan_for(index, tuple(SUPPORTED_LANGUAGES))


def _plan_at(index: Index, weight: float) -> FieldPlan:
    """The shipped plan with the four build out weights moved to ``weight``.

    One knob and one only. The field list, the two leading languages and the file
    name half stay exactly as ``field_plan_for`` computed them, so a run at a
    different weight differs from the shipped run in the four numbers under test
    and in nothing else.
    """
    shipped = _shipped_plan(index)
    boosts = dict(shipped.boosts)
    for code in BUILD_OUT:
        boosts[BODY_FIELD[code]] = weight
    return FieldPlan(fields=shipped.fields, boosts=boosts, title_only=shipped.title_only)


def _multi_chain_hit_leads(index: Index, weight: float) -> bool:
    """Has the order turned over at this weight?

    Both documents have to be in the answer for the question to mean anything, so
    that is asserted here rather than read as a False.
    """
    order = _order(index, QUESTION, _plan_at(index, weight))
    assert {ENGLISH_HIT, MULTI_CHAIN_HIT} <= set(order)
    return order.index(MULTI_CHAIN_HIT) < order.index(ENGLISH_HIT)


def _order(index: Index, text: str, plan: FieldPlan) -> list[int]:
    """The file ids a real search returns, in the order it returns them.

    After the pattern of ``_unfiltered_order`` in ``test_search_library.py``: the
    line goes through ``build_query`` so that the plan under test is read the way
    the three call sites under ``api/`` read it, and the order comes off the
    searcher rather than out of a score somebody added up by hand.
    """
    rewritten = build_query(index, text, plan=plan)
    assert rewritten.errors == []
    assert rewritten.query is not None
    searcher = index.searcher()
    found: list[int] = []
    for _, address in searcher.search(rewritten.query, len(DOCUMENTS)).hits:
        value = searcher.doc(address).get_first(FIELD_FILE_ID)
        assert value is not None
        found.append(int(value))
    return found


def _reached_in(index: Index, field: str, text: str) -> list[int]:
    """The file ids one single field answers with, sorted.

    One field and one chain, which is what makes the disagreement visible: the
    search path puts all six into one query and the sum hides which chain
    contributed what.
    """
    query, errors = index.parse_query_lenient(text, default_field_names=[field])
    assert list(errors) == []
    searcher = index.searcher()
    found: list[int] = []
    for _, address in searcher.search(query, len(DOCUMENTS)).hits:
        value = searcher.doc(address).get_first(FIELD_FILE_ID)
        assert value is not None
        found.append(int(value))
    return sorted(found)


def test_the_four_build_out_weights_lie_below_english_and_english_below_german() -> None:
    # The structural half of success criterion 3, read off the numbers that ship
    # rather than off a sentence about them. It is the cheapest assertion in this
    # file and the only one that is about the promise itself; everything below is
    # about what the promise is worth.
    for code in BUILD_OUT:
        assert BODY_BOOST[code] < BODY_BOOST["en"], f"body_{code} weighs at least as much as body_en"
    assert BODY_BOOST["en"] < BODY_BOOST["de"]


def test_every_producible_plan_keeps_its_build_out_fields_below_english(probe_index: Index) -> None:
    # The same promise over every plan a directory can ask for, and not only over
    # the one set that happens to be in the table. A weight that is right in the
    # mapping and wrong in the plan would be invisible to the case above, because
    # the plan is what the parser is handed.
    checked = 0
    for languages in _language_sets():
        plan = _plan_for(probe_index, languages)
        if FIELD_BODY_EN not in plan.boosts:
            continue
        for code in languages:
            field = BODY_FIELD[code]
            if code not in BUILD_OUT or field not in plan.boosts:
                continue
            assert plan.boosts[field] < plan.boosts[FIELD_BODY_EN], f"{field} weighs at least as much as body_en"
            checked += 1
    # Four build out languages, each of them in half of the sets that carry en:
    # 4 * 2 ** (6 - 2). Written out so that a loop which silently stopped looking
    # cannot pass as a loop that looked and found nothing wrong.
    assert checked == 64


def test_the_two_hits_answer_the_question_through_chains_that_disagree(probe_index: Index) -> None:
    # The whole premise of the ranking probe in one assertion. Three chains reach
    # the English note and three reach the Spanish one, so the comparison that
    # follows is between two documents the engine really does weigh differently
    # and not between a document and a document that simply is not there.
    reached = {code: _reached_in(probe_index, BODY_FIELD[code], QUESTION) for code in SUPPORTED_LANGUAGES}

    assert reached == {
        "de": [ENGLISH_HIT],
        "en": [ENGLISH_HIT],
        "nl": [ENGLISH_HIT],
        "es": [MULTI_CHAIN_HIT],
        "it": [MULTI_CHAIN_HIT],
        "pt": [MULTI_CHAIN_HIT],
    }


def test_the_question_reaches_no_file_name_and_no_title(probe_index: Index) -> None:
    # The two fields that weigh 3.0 and 2.0. If either of them carried the
    # question, the ranking would be settled before a body field was ever
    # consulted and the probe would be measuring file names.
    assert _reached_in(probe_index, FIELD_NAME, QUESTION) == []
    assert _reached_in(probe_index, FIELD_TITLE, QUESTION) == []


def test_the_distractor_is_in_the_index_and_still_does_not_answer_the_question(probe_index: Index) -> None:
    # Both halves, because only the pair says anything: a third document that was
    # never written is silent for a reason that has nothing to do with the chains,
    # and it would make the two document comparison look cleaner than it is.
    assert _order(probe_index, DISTRACTOR_QUESTION, _shipped_plan(probe_index)) == [DISTRACTOR]
    assert DISTRACTOR not in _order(probe_index, QUESTION, _shipped_plan(probe_index))


def test_the_better_english_hit_stands_before_the_three_chain_hit(probe_index: Index) -> None:
    # Success criterion 3 as a measurement instead of as a sentence, and this is
    # the case the roadmap is really asking for. The plan is the one an
    # installation with all six languages gets, the search is the one the three
    # call sites under api/ run, and the order is the order the searcher hands
    # back rather than a comparison of two numbers somebody computed.
    order = _order(probe_index, QUESTION, _shipped_plan(probe_index))

    assert order == [ENGLISH_HIT, MULTI_CHAIN_HIT]
    assert order.index(ENGLISH_HIT) < order.index(MULTI_CHAIN_HIT)


def test_the_same_ranking_turns_over_once_the_four_weights_reach_one(probe_index: Index) -> None:
    # The counter probe, and without it the case above is decoration: it would be
    # just as green on an index where the Spanish note never answers the question,
    # and then the weights would have settled nothing at all. Everything except
    # the four numbers is held still, so what turns the order over is the weights
    # and not a second difference that crept in.
    order = _order(probe_index, QUESTION, _plan_at(probe_index, 1.0))

    assert order == [MULTI_CHAIN_HIT, ENGLISH_HIT]
    assert order.index(MULTI_CHAIN_HIT) < order.index(ENGLISH_HIT)


def test_the_boost_at_which_the_ranking_turns_over_is_this_one(probe_index: Index) -> None:
    # The sweep that produced TIPPING_BOOST, kept in the suite rather than run
    # once and written down, so that the number in the module head stays a
    # measurement of the code that ships instead of a memory of it.
    turned = [
        step / SWEEP_STEPS for step in range(SWEEP_STEPS + 1) if _multi_chain_hit_leads(probe_index, step / SWEEP_STEPS)
    ]

    assert turned, "the order never turns over, so the counter probe above proves nothing"
    assert turned[0] == pytest.approx(TIPPING_BOOST)
    # The two distances that make the pair of cases above worth running: the
    # shipped weight is below the edge, so the promise holds with room, and 1.0
    # is above it, so the counter probe really is a counter probe.
    assert BODY_BOOST[BUILD_OUT[0]] < TIPPING_BOOST < 1.0
