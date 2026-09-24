"""The four language cases of the build out, asked the way a request asks them.

``test_language_cases_field_level.py`` is the sibling of this module and its
template. There the question runs against ONE body field, through
``parse_query_lenient`` with ``default_field_names=[BODY_FIELD[code]]``, and the
header of that file says why: those cases belong to phase 18, which had no
question side to put them on. Phase 19 opened it, so here the question runs
through ``build_query`` with a field plan, which is the one path every search of
the product takes. Three things follow from that, and each of them is an
assertion below rather than a sentence here.

**Every active field is in the list, so a foreign chain can answer.** The write
side puts the extracted text into ``body_de`` whatever the language set says,
because that is the only stored copy, and into every switched on chain beside it
(``index/writer.py``). A case index of this module therefore carries the stock an
instance with the language set ``de,en,<code>`` writes: the same text in three
body fields. A pair of forms that the German or the English chain merges by
itself would then be found through a chain nobody meant to ask, and the case
would be green for a reason that has nothing to do with the language it names.
The selection here carries a THIRD exclusion for that reason, one the field level
does not need: the pair has to be merged by its own chain and kept on two terms
by the English one AND by the German one. That failure is a measured one and not
a worry: a probe written on 2026-09-24 found a Spanish document through the
English chain and reported the Spanish chain as proven.

**The choice of the pair is an assertion and not a comment.** ``_case_pair``
takes the FIRST pair of the fixture that qualifies, not the nicest one, and one
case per language claims that such a pair exists at all. A noun class whose
singular and plural the English chain strips exactly the way the Spanish chain
does is explicitly no case here, and the two forms of that class do not even
share a stem in their own chain; the whole class stands in
``docs/language-analyzers.md`` under "Known limits".

**Every case has its counter probe.** The same question with the body field of
its own language taken out of the plan reaches the document that carries the
OTHER form no longer. Without that probe a green case would be just as green for
a field list that has no effect at all. It does not fall to nothing, and that is
the shape of the search path rather than a weakness of the probe: the document
that carries the typed form carries it in ``body_de`` as well, so the question
still answers with itself. What disappears is the merge, and the merge is the
whole subject.

No text extract is asked for anywhere below, and that is deliberate. A hit found
through a language field alone comes back without one, because the snippet is cut
out of ``body_de`` (``index/search.py:875``), the only stored copy, where a
question that only the Spanish chain answers has nothing to mark (19-RESEARCH
measurement M-4). A hit without a snippet is still a hit, and the cases below
claim the hit.

No form of any case stands in this file as a literal, and a test holds that line.
The words live in ``tests/fixtures/chain_cases_<code>.txt``, the same fixtures the
measurement of 2026-09-23 and its rerun of 2026-09-24 ran on, so a later rebuild
of a chain moves this file in one place instead of two. The fixture reader is not
rebuilt here either; it comes out of ``scripts/dev/chain_probe.py`` through the
sibling module that already loads it, because a second reader is a second format.
"""

import re
from collections.abc import Iterator, Sequence
from pathlib import Path
from types import ModuleType
from typing import Final, NamedTuple

import pytest
from tantivy import Document, Index, Searcher, TextAnalyzer

from findling.api.resources import field_plan_for
from findling.config import SNOWBALL_NAME
from findling.index.analyzer import cached_german_analyzer, english_analyzer, snowball_analyzer
from findling.index.open import LANGUAGES_MARK, SCHEMA_MARK, expected_versions, open_index, open_reader
from findling.index.schema import (
    BODY_FIELD,
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)
from findling.index.wordlist import wordlist_hash
from findling.query.rewrite import BODY_BOOST, LEGACY_PLAN, NAME_BOOST, TITLE_BOOST, FieldPlan, build_query
from findling.store.repo import open_store
from test_language_analyzers import CASES as CASE_FIXTURES
from test_language_analyzers import CODES, _load_chain_probe

# This file, read once, for the gate that keeps every form of every case out of
# it. Words and not substrings: a form of one fixture is an everyday word of
# everyday prose somewhere else, so a substring gate would be a trap rather than
# a rule.
SOURCE_WORDS: Final = frozenset(re.findall(r"[^\W\d_]+", Path(__file__).read_text(encoding="utf-8").lower()))

# The same constituent list the rest of the suite opens indexes with, read once
# per session, so that the one expensive chain of this process, the German
# automaton, is built once for the whole run. The field level module loads it to
# open an index; this one needs the chain itself, as the third exclusion of the
# selection, and gets it out of the cache ``open_index`` fills.
CONSTITUENTS: Final = (
    (Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt").read_text(encoding="utf-8").split()
)

# The two documents of a case index the question has to reach, by file id. The
# third one carries a word of the same language that the chain puts on another
# term: without it a query that matched everything would look exactly like a
# query that matched the case.
TYPED_DOCUMENT: Final = 1
WRITTEN_DOCUMENT: Final = 2

# What an instance runs beside the language of the case. Every installation
# carries these two, the write side puts the text into both of them, and that is
# precisely why the selection below has to keep both out of the merge.
STOCK_LANGUAGES: Final = ("de", "en")

# The widest field list the schema allows, weights and all, as one value. This is
# the plan of an instance that switched every chain on, and asking the cases
# under it is the hardest version of the question: whatever else answers, it
# answers here. The weights are read out of the three constants of
# ``query/rewrite.py``, so that no number of the product has a second spelling in
# this file.
FULL_PLAN: Final = FieldPlan(
    fields=(*BODY_FIELD.values(), FIELD_NAME, FIELD_TITLE),
    boosts={
        **{field: BODY_BOOST[code] for code, field in BODY_FIELD.items()},
        FIELD_NAME: NAME_BOOST,
        FIELD_TITLE: TITLE_BOOST,
    },
    title_only=(FIELD_NAME,),
)


class Pair(NamedTuple):
    """Two surface forms of one family, in the order the fixture spells them."""

    typed: str
    written: str


def _pairs(forms: Sequence[str]) -> Iterator[Pair]:
    """Yield the unordered pairs of one family, fixture order kept inside a pair."""
    for position, typed in enumerate(forms):
        for written in forms[position + 1 :]:
            yield Pair(typed, written)


def _terms(analyzer: TextAnalyzer, form: str) -> set[str]:
    return set(analyzer.analyze(form))


def _share_a_term(analyzer: TextAnalyzer, pair: Pair) -> bool:
    """True when a question in one form of the pair reaches the other one."""
    typed, written = _terms(analyzer, pair.typed), _terms(analyzer, pair.written)
    return bool(typed and written and typed & written)


def _separated_pairs(
    chain: TextAnalyzer,
    english: TextAnalyzer,
    german: TextAnalyzer,
    families: Sequence[Sequence[str]],
) -> list[Pair]:
    """The pairs only the chain of their own language brings together.

    Three chains and not two, which is the one difference to the selection of the
    field level module. There the question named one field, so the English chain
    was the only foreign one that could be in the list by accident; here every
    active field of the instance is in it, and the German chain carries the text
    as well because it holds the only stored copy. A pair either of them merges
    would be found without the language this module is about.
    """
    return [
        pair
        for forms in families
        for pair in _pairs(forms)
        if _share_a_term(chain, pair) and not _share_a_term(english, pair) and not _share_a_term(german, pair)
    ]


def _case_pair(
    code: str,
    chain: TextAnalyzer,
    english: TextAnalyzer,
    german: TextAnalyzer,
    families: Sequence[Sequence[str]],
) -> Pair:
    """The pair one case runs on: the first one of the fixture that qualifies.

    First and not "the nicest one", because the choice has to come out of the
    fixture and not out of the taste of whoever wrote the file. There is no
    weaker criterion to fall back on here, and that is deliberate: on the search
    path a pair the other two chains merge proves nothing at all, so a fixture
    that stops offering one is a red case and never a quieter one.
    """
    separated = _separated_pairs(chain, english, german, families)
    assert separated, (
        f"{CASE_FIXTURES[code].name} holds no pair that only the {code} chain merges, so a case on the search "
        f"path has no subject; take an inflection family into that fixture, rerun "
        f"scripts/dev/measure_chains.sh and pull the counting gate after it"
    )
    return separated[0]


def _distractor(chain: TextAnalyzer, families: Sequence[Sequence[str]], pair: Pair) -> str:
    """The first form of the fixture this chain does not put on the case term.

    Out of the fixture for the same reason the pair is, and chosen by a rule
    rather than by hand, so that the third document of a case index is a word of
    the right language and demonstrably not a second spelling of the case.
    """
    shared = _terms(chain, pair.typed) & _terms(chain, pair.written)
    for forms in families:
        for form in forms:
            if not _terms(chain, form) & shared:
                return form
    raise AssertionError("every form of this fixture lands on the term of the case, so nothing can be told apart")


def _write_case_index(root: Path, code: str, texts: Sequence[str]) -> Index:
    """Build the index of one case: the stock an instance of this language writes.

    Through ``open_index`` and never through the tantivy constructor, because
    opening is registering and the guard of ``test_index_open.py`` runs over the
    whole package for exactly that reason; a test module holds the same line.

    Field by field and never through keyword arguments: measured, a keyword built
    document puts an I64 into the U64 column of ``file_id`` and the indexing
    thread of tantivy panics after the Python call has already returned.

    The text goes into three body fields and not into one, which is the whole
    difference to the case index of the field level module. That is what
    ``index/writer.py`` does on an instance whose language set is ``de,en,<code>``:
    ``body_de`` unconditionally, because it is the only stored copy, and every
    switched on chain beside it. Writing the field of the case alone would build
    an index no installation has and would take the subject away from every
    counter probe below.
    """
    index = open_index(root, CONSTITUENTS)
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    fields = tuple(dict.fromkeys((FIELD_BODY_DE, FIELD_BODY_EN, BODY_FIELD[code])))
    for file_id, text in enumerate(texts, start=TYPED_DOCUMENT):
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        for field in fields:
            document.add_text(field, text)
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    index.reload()
    return index


def _without(plan: FieldPlan, field: str) -> FieldPlan:
    """The same plan with one body field taken out of both of its halves.

    Both halves in one step, because that is what a plan is. A counter probe that
    dropped the field from the list and left its weight standing would not
    measure a narrower search at all: it would measure the ``ValueError`` of
    ``parse_query_lenient`` over a weight on a field nobody searches.
    """
    return FieldPlan(
        fields=tuple(name for name in plan.fields if name != field),
        boosts={name: weight for name, weight in plan.boosts.items() if name != field},
        title_only=plan.title_only,
    )


def _found(index: Index, searcher: Searcher, plan: FieldPlan, text: str) -> list[int]:
    """Ask ``text`` the way a request asks it and return the file ids, sorted.

    Through ``build_query`` and therefore through the filter step, the umlaut
    variants and the lenient parser, with the plan as the only thing that decides
    which fields a bare word reaches. This is the search path of ``api/search.py``
    without its permission filter, and it is the whole point of this module.
    """
    rewritten = build_query(index, text, plan=plan)

    assert rewritten.errors == [], f"the query builder reported {rewritten.errors} for a word out of a fixture"
    assert rewritten.query is not None, "the question was rewritten into nothing, so the case asks the engine nothing"
    answers: list[int] = []
    for _, address in searcher.search(rewritten.query, 10).hits:
        value = searcher.doc(address).get_first(FIELD_FILE_ID)
        assert value is not None
        answers.append(int(value))
    return sorted(answers)


def _field_terms(searcher: Searcher, field: str) -> set[str]:
    """Every term the index carries in one field, without their frequencies."""
    return {term for term, _ in searcher.terms_with_prefix(field, "")}


def _marks_of(root: Path, languages: str, schema: str | None = None) -> dict[str, str]:
    """The marks of a real state database, seeded and then stamped.

    Seeded the way every volume is seeded and stamped the way
    ``findling.index.rebuild.stamp_after_swap`` stamps it, because the seed does
    not write the language mark at all: it would put the wish of a container down
    as a fact about a directory, which is threat T-18-05-01 of phase 18.
    ``schema`` overwrites the generation mark, and that is how the counter probe
    below puts a volume of the old build back onto the disk.
    """
    store = open_store(root / "state.db", meta=expected_versions("a-digest", languages))
    store.write_meta(LANGUAGES_MARK, languages)
    if schema is not None:
        store.write_meta(SCHEMA_MARK, schema)
    marks = store.read_meta()
    store.close()
    return marks


@pytest.fixture(scope="module")
def probe() -> ModuleType:
    """The measurement probe, for its fixture reader and for nothing else."""
    return _load_chain_probe()


@pytest.fixture(scope="module")
def families(probe: ModuleType) -> dict[str, list[list[str]]]:
    """The form families of the four fixtures, read through the one reader."""
    return {code: probe.read_families(CASE_FIXTURES[code]) for code in CODES}


@pytest.fixture(scope="module")
def english() -> TextAnalyzer:
    """The shipped English chain, the one the failed probe mistook for another."""
    return english_analyzer()


@pytest.fixture(scope="module")
def german() -> TextAnalyzer:
    """The shipped German chain, the third one of the selection.

    Out of the process wide cache and under the digest ``open_index`` uses, so
    that the automaton of the case indexes and the automaton of the selection are
    one object and the expensive build happens once in the whole session.
    """
    return cached_german_analyzer(wordlist_hash(CONSTITUENTS), CONSTITUENTS)


@pytest.fixture(scope="module")
def chains() -> dict[str, TextAnalyzer]:
    """One shipped Snowball chain per language, built once for the whole module."""
    return {code: snowball_analyzer(SNOWBALL_NAME[code]) for code in CODES}


@pytest.fixture(scope="module")
def pairs(
    families: dict[str, list[list[str]]],
    chains: dict[str, TextAnalyzer],
    english: TextAnalyzer,
    german: TextAnalyzer,
) -> dict[str, Pair]:
    """The pair every case of this module runs on, one per language."""
    return {code: _case_pair(code, chains[code], english, german, families[code]) for code in CODES}


@pytest.fixture(scope="module")
def distractors(
    families: dict[str, list[list[str]]], chains: dict[str, TextAnalyzer], pairs: dict[str, Pair]
) -> dict[str, str]:
    """The third document of every case index, one word per language."""
    return {code: _distractor(chains[code], families[code], pairs[code]) for code in CODES}


@pytest.fixture(scope="module")
def texts(pairs: dict[str, Pair], distractors: dict[str, str]) -> dict[str, tuple[str, ...]]:
    """The three documents of a case index, in file id order."""
    return {code: (pairs[code].typed, pairs[code].written, distractors[code]) for code in CODES}


@pytest.fixture(scope="module")
def indexes(tmp_path_factory: pytest.TempPathFactory, texts: dict[str, tuple[str, ...]]) -> dict[str, Index]:
    """One index per language, built once, each of them the stock of one instance."""
    return {
        code: _write_case_index(tmp_path_factory.mktemp(f"path_{code}") / "index", code, texts[code]) for code in CODES
    }


@pytest.fixture(scope="module")
def searchers(indexes: dict[str, Index]) -> dict[str, Searcher]:
    """One searcher per case index, configured once and not once per question."""
    return {code: open_reader(indexes[code]) for code in CODES}


def test_the_widest_plan_is_one_value_and_holds_every_body_field() -> None:
    # The plan the cases below run under, held against the schema rather than
    # against itself. A body field the schema grows and this list forgets would
    # otherwise leave a whole language untested while every case stayed green.
    assert set(FULL_PLAN.fields) == set(BODY_FIELD.values()) | {FIELD_NAME, FIELD_TITLE}
    assert set(FULL_PLAN.boosts) == set(FULL_PLAN.fields)
    assert FULL_PLAN.title_only == (FIELD_NAME,)


@pytest.mark.parametrize("code", CODES)
def test_the_fixture_offers_a_pair_no_other_shipped_chain_merges(
    code: str,
    families: dict[str, list[list[str]]],
    chains: dict[str, TextAnalyzer],
    english: TextAnalyzer,
    german: TextAnalyzer,
) -> None:
    # The claim that the selection has anything to select. Unlike the field level
    # module this one has no weaker criterion left to fall back on, so the
    # existence of such a pair is the condition of the whole file.
    assert _separated_pairs(chains[code], english, german, families[code]) != [], (
        f"{CASE_FIXTURES[code].name} no longer holds a pair only the {code} chain merges, so the case of this "
        f"language cannot run on the search path; bring an inflection family back into that fixture"
    )


@pytest.mark.parametrize("code", CODES)
def test_the_case_pair_is_one_its_own_chain_merges(
    code: str, pairs: dict[str, Pair], chains: dict[str, TextAnalyzer]
) -> None:
    # Without this the case below could be green because nothing merges anywhere
    # and both documents answered their own form.
    assert _share_a_term(chains[code], pairs[code]), f"the {code} chain does not bring {pairs[code]} together"


@pytest.mark.parametrize("code", CODES)
def test_neither_the_english_nor_the_german_chain_merges_the_case_pair(
    code: str, pairs: dict[str, Pair], english: TextAnalyzer, german: TextAnalyzer
) -> None:
    # The third exclusion as its own case, because it is the one the field level
    # module does not have and the one the search path needs. Both of these
    # chains carry the text of every document of a case index, so either of them
    # merging the pair would answer the question without the language it names.
    pair = pairs[code]

    assert not _share_a_term(english, pair), (
        f"the English chain merges {pair} as well, so a green {code} case would prove nothing about the "
        f"{code} chain; pick a pair out of {CASE_FIXTURES[code].name} that only that chain brings together"
    )
    assert not _share_a_term(german, pair), (
        f"the German chain merges {pair}, and body_de carries the text of every document of the case index, "
        f"so the hit would come out of the stored copy instead of out of {BODY_FIELD[code]}"
    )


@pytest.mark.parametrize("code", CODES)
def test_the_case_index_carries_the_stock_a_real_instance_writes(
    code: str, searchers: dict[str, Searcher], texts: dict[str, tuple[str, ...]]
) -> None:
    # Two claims in one, and the second is the deliberate opposite of the field
    # level module. Three documents of one language and nothing else, which is
    # Lehre A4 of milestone v1.1; and the text in the three fields an instance
    # with this language set writes, so that the counter probes have a subject
    # and the foreign chains really are in the question.
    searcher = searchers[code]
    stock = {FIELD_BODY_DE, FIELD_BODY_EN, BODY_FIELD[code]}

    assert searcher.num_docs == len(texts[code])
    for field in BODY_FIELD.values():
        carried = _field_terms(searcher, field) != set()
        assert carried == (field in stock), f"{field} of the {code} case index does not carry what an instance writes"


@pytest.mark.parametrize("code", CODES)
def test_the_question_in_one_form_finds_the_document_that_carries_the_other(
    code: str, indexes: dict[str, Index], searchers: dict[str, Searcher], pairs: dict[str, Pair]
) -> None:
    # The case itself, on the widest plan the schema allows, and it runs in both
    # directions because a chain that brings two forms together brings them
    # together whichever of them was typed. Equality and not "contains": the
    # third document is a word of the same language, so a query that returned
    # everything would look exactly like a query that worked.
    index, searcher, pair = indexes[code], searchers[code], pairs[code]

    assert _found(index, searcher, FULL_PLAN, pair.typed) == [TYPED_DOCUMENT, WRITTEN_DOCUMENT]
    assert _found(index, searcher, FULL_PLAN, pair.written) == [TYPED_DOCUMENT, WRITTEN_DOCUMENT]


@pytest.mark.parametrize("code", CODES)
def test_a_plan_without_the_field_of_the_language_loses_the_other_form(
    code: str, indexes: dict[str, Index], searchers: dict[str, Searcher], pairs: dict[str, Pair]
) -> None:
    # The counter probe the case above is worth nothing without. One field is
    # taken out of the plan and the document that carries the other form is gone
    # from the answer, which is the proof that the hit came through that field
    # and not through one of the two chains that carry the same text.
    #
    # What stays is the document that carries the typed form: it carries it in
    # body_de as well, and a question always answers with itself. That is the
    # search path and not a hole in the probe, and it is why this case asserts
    # the exact answer rather than an empty one.
    index, searcher, pair = indexes[code], searchers[code], pairs[code]
    narrowed = _without(FULL_PLAN, BODY_FIELD[code])

    assert _found(index, searcher, narrowed, pair.typed) == [TYPED_DOCUMENT], (
        f"{BODY_FIELD[code]} is not in this plan and the other form is still found, so the hit of the {code} "
        f"case comes out of a chain nobody asked and proves nothing about that field"
    )
    assert _found(index, searcher, narrowed, pair.written) == [WRITTEN_DOCUMENT]


@pytest.mark.parametrize("code", CODES)
def test_the_plan_of_a_real_state_database_finds_the_other_form(
    code: str, tmp_path: Path, indexes: dict[str, Index], searchers: dict[str, Searcher], pairs: dict[str, Pair]
) -> None:
    # The seam between this module and plan 19-03. Everything above runs on a
    # plan built by hand, which proves that such a plan works and not that an
    # instance is ever given one. Here the plan is computed out of the marks of a
    # real state database, by the very function api/resources.py calls once per
    # opening of the read side.
    marks = _marks_of(tmp_path, ",".join((*STOCK_LANGUAGES, code)))
    plan = field_plan_for(marks, indexes[code])
    index, searcher, pair = indexes[code], searchers[code], pairs[code]

    assert plan.fields == (FIELD_BODY_DE, FIELD_BODY_EN, BODY_FIELD[code], FIELD_NAME, FIELD_TITLE)
    assert _found(index, searcher, plan, pair.typed) == [TYPED_DOCUMENT, WRITTEN_DOCUMENT]
    assert _found(index, searcher, plan, pair.written) == [TYPED_DOCUMENT, WRITTEN_DOCUMENT]


@pytest.mark.parametrize("code", CODES)
def test_the_legacy_mark_of_a_real_state_database_loses_the_other_form(
    code: str, tmp_path: Path, indexes: dict[str, Index], searchers: dict[str, Searcher], pairs: dict[str, Pair]
) -> None:
    # The safety gate of the roadmap, seen from the language side. The same state
    # database, the same directory and the same question, with only the
    # generation mark back on the stock value: the plan falls back to the frozen
    # one of every release up to 1.2.0, the language of the case is not in it,
    # and the merge is gone. Without this case the file would prove that the new
    # fields work and not that the marks decide whether they are asked at all.
    marks = _marks_of(tmp_path, ",".join((*STOCK_LANGUAGES, code)), schema="1")
    plan = field_plan_for(marks, indexes[code])
    index, searcher, pair = indexes[code], searchers[code], pairs[code]

    assert plan == LEGACY_PLAN
    assert _found(index, searcher, plan, pair.typed) == [TYPED_DOCUMENT], (
        f"an index whose schema mark says 1 answers the {code} question with the other form, so the mark does "
        f"not decide which fields are searched and the gate of phase 19 is open on a stock volume"
    )


@pytest.mark.parametrize("code", CODES)
def test_no_form_of_the_case_stands_in_this_file(
    code: str, pairs: dict[str, Pair], distractors: dict[str, str]
) -> None:
    # T-18-04-02, carried over unchanged. A form copied in here would survive a
    # rebuild of the chains that moves the fixture, and the case would then
    # measure a word the measurement has dropped.
    forms = (*pairs[code], distractors[code])
    standing = sorted(form for form in forms if form.lower() in SOURCE_WORDS)

    assert standing == [], (
        f"{standing} stands in this file as a word; the forms of a case come from "
        f"{CASE_FIXTURES[code].name} and nowhere else, so reword the prose"
    )
