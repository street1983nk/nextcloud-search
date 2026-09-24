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

**What this file proves.** Two things so far, and the rest arrives with the
ranking probe.

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

**What this file does not prove.** Nothing about an installation. Three documents
are not a corpus. It proves nothing about the analyzer chains themselves, which
is ``test_language_analyzers.py``, and nothing about which fields a plan names,
which is ``test_query_fields_plan.py``. It prepares no change of query shape
either: that decision is bound to a measurement on real data in phase 22
(REQUIREMENTS MESS-09).
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
