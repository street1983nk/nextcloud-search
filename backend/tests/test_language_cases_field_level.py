"""The four language cases of plan 18-04, with the reason they carry anything.

LEX-08 asks for one case per language of the v1.3 build out, and it asks for it
in this phase, so the cases run ON THE FIELD: phase 19 opens the question side,
which is why every query below goes through
``parse_query_lenient(..., default_field_names=[BODY_FIELD[code]])`` against one
body field and never through ``build_query``, whose ``DEFAULT_FIELDS`` this phase
does not touch.

Two things decide whether such a case proves anything at all.

*The word pair.* A probe written on 2026-09-24 found a Spanish document through
the ENGLISH chain, because Porter strips a plural s just as happily, and reported
the Spanish chain as proven. A pair whose two forms the English chain merges by
itself therefore says nothing about the chain of the field it was written into.
So the pairs here are not picked by the author: they are read out of the
measurement fixtures of plan 17-06, and the criterion that picks them is an
assertion in this file and not a sentence in a comment. The whole point of the
plan is that the strength of a case is part of the suite.

*The stock of the index.* Lehre A4 of milestone v1.1: with 52111 foreign
documents carrying the same tokens, a proof carries nothing any more. Every case
therefore gets an index of its own with a handful of documents of one language,
and that the other five body fields stay empty is asserted rather than intended.

No form of any case stands in this file as a literal, and a test holds that line.
The words live in ``tests/fixtures/chain_cases_<code>.txt``, the same fixtures the
measurement of 2026-09-23 ran on, so a later rebuild of a chain moves this file
in one place instead of two. The fixture reader is not rebuilt here either; it
comes out of ``scripts/dev/chain_probe.py`` through the sibling module that
already loads it, because a second reader is a second format.
"""

import re
from collections.abc import Iterator, Sequence
from pathlib import Path
from types import ModuleType
from typing import Final, NamedTuple

import pytest
from tantivy import TextAnalyzer

from findling.config import SNOWBALL_NAME
from findling.index.analyzer import english_analyzer, snowball_analyzer
from test_language_analyzers import CASES as CASE_FIXTURES
from test_language_analyzers import CODES, _load_chain_probe

# How far the measured fixture of a language lets its case go, and why the
# selection below lands where it lands. One line per language, as the plan asks,
# and none of them names a form: the words are data in the fixtures, and
# test_no_form_of_the_case_stands_in_this_file keeps them there.
#
# es: the -es plural of the adjective for "German" against its feminine
#     singular. Snowball Spanish puts both on one stem; the English chain stems
#     the plural the same way but leaves the feminine form standing, so only the
#     Spanish chain brings the two together.
# nl: the infinitive of the Dutch verb for "to influence" against its past
#     participle, both in the spelling with the diaeresis. Snowball Dutch puts
#     both on the participle stem; the English chain writes two terms, and one
#     of them it invents by stemming a Dutch ending it does not know.
# pt: the Portuguese noun for "country", singular against plural. Snowball
#     Portuguese puts both on one stem; the English chain folds the accent as
#     well and then strips the s of the singular, which takes the two forms
#     apart instead of together.
# it: the fourteen Italian families of the 2026-09-23 measurement are accent
#     pairs and nothing else, so NO Italian pair exists that the English chain
#     keeps apart: both chains fold, and after the fold the two spellings are one
#     string. The Italian case rests on the term instead of on the merge, and
#     test_the_fixture_of_a_folded_language_offers_no_such_pair holds that
#     exception against the fixture: an Italian inflection family added later
#     turns it red, and then the case gets promoted instead of staying the weak
#     one by accident.
SEPARATED: Final = ("es", "nl", "pt")
FOLDED: Final = ("it",)

# This file, read once, for the gate that keeps every form of every case out of
# it. Words and not substrings: "region" stands in the Spanish fixture and in
# ordinary English prose, so a substring gate would be a trap rather than a rule.
SOURCE_WORDS: Final = frozenset(re.findall(r"[^\W\d_]+", Path(__file__).read_text(encoding="utf-8").lower()))


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


def _separated_pairs(chain: TextAnalyzer, english: TextAnalyzer, families: Sequence[Sequence[str]]) -> list[Pair]:
    """The pairs the target chain merges AND the English chain keeps on two terms.

    This is the strong criterion, the one the failed probe of 2026-09-24 did not
    apply. A pair out of this list can only be brought together by the chain of
    its own language.
    """
    return [
        pair
        for forms in families
        for pair in _pairs(forms)
        if _share_a_term(chain, pair) and not _share_a_term(english, pair)
    ]


def _distinguished_pairs(chain: TextAnalyzer, english: TextAnalyzer, families: Sequence[Sequence[str]]) -> list[Pair]:
    """The pairs the target chain merges onto terms the English chain never writes.

    The weaker criterion, for a language whose fixture holds accent pairs only.
    It does not say "the English chain would not find this", it says "the English
    chain would not have written these terms", and that is what the term
    dictionary of the field is held against further down.
    """
    found: list[Pair] = []
    for forms in families:
        for pair in _pairs(forms):
            if not _share_a_term(chain, pair):
                continue
            ours = _terms(chain, pair.typed) | _terms(chain, pair.written)
            theirs = _terms(english, pair.typed) | _terms(english, pair.written)
            if ours != theirs:
                found.append(pair)
    return found


def _case_pair(code: str, chain: TextAnalyzer, english: TextAnalyzer, families: Sequence[Sequence[str]]) -> Pair:
    """The pair one case runs on: the first one of the fixture that qualifies.

    First and not "the nicest one", because the choice has to come out of the
    fixture and not out of the taste of whoever wrote the file. The strong
    criterion is tried first for every language, so a fixture that grows an
    inflection pair for a folded language upgrades that case by itself.
    """
    separated = _separated_pairs(chain, english, families)
    if separated:
        return separated[0]
    distinguished = _distinguished_pairs(chain, english, families)
    assert distinguished, f"{CASE_FIXTURES[code].name} holds no pair this chain merges; the case has no subject"
    return distinguished[0]


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
def chains() -> dict[str, TextAnalyzer]:
    """One shipped Snowball chain per language, built once for the whole module."""
    return {code: snowball_analyzer(SNOWBALL_NAME[code]) for code in CODES}


@pytest.fixture(scope="module")
def pairs(
    families: dict[str, list[list[str]]], chains: dict[str, TextAnalyzer], english: TextAnalyzer
) -> dict[str, Pair]:
    """The pair every case of this module runs on, one per language."""
    return {code: _case_pair(code, chains[code], english, families[code]) for code in CODES}


def test_every_language_of_the_build_out_is_classified_exactly_once() -> None:
    # The two lists above are a claim about the fixtures, so a language that
    # stands in neither of them would silently get no strength statement at all.
    assert set(SEPARATED) | set(FOLDED) == set(CODES)
    assert not set(SEPARATED) & set(FOLDED)


@pytest.mark.parametrize("code", SEPARATED)
def test_the_fixture_offers_a_pair_the_english_chain_keeps_apart(
    code: str, families: dict[str, list[list[str]]], chains: dict[str, TextAnalyzer], english: TextAnalyzer
) -> None:
    assert _separated_pairs(chains[code], english, families[code]) != [], (
        f"{CASE_FIXTURES[code].name} no longer holds a pair only the {code} chain merges, so the case of this "
        f"language has lost its strength; move {code} to FOLDED and say so, or bring the family back"
    )


@pytest.mark.parametrize("code", FOLDED)
def test_the_fixture_of_a_folded_language_offers_no_such_pair(
    code: str, families: dict[str, list[list[str]]], chains: dict[str, TextAnalyzer], english: TextAnalyzer
) -> None:
    # The documented exception, held against the fixture instead of against the
    # memory of the author. Red here is good news, not a defect.
    separated = _separated_pairs(chains[code], english, families[code])

    assert separated == [], (
        f"{CASE_FIXTURES[code].name} now holds {len(separated)} pair(s) the English chain keeps apart, the first "
        f"of them {separated[0] if separated else ()}: move {code} from FOLDED to SEPARATED and let the case run "
        "on the strong criterion"
    )


@pytest.mark.parametrize("code", CODES)
def test_the_case_pair_is_one_its_own_chain_merges(
    code: str, pairs: dict[str, Pair], chains: dict[str, TextAnalyzer]
) -> None:
    # Without this the field level case below could be green because nothing
    # merges anywhere and both documents matched their own form.
    assert _share_a_term(chains[code], pairs[code]), f"the {code} chain does not bring {pairs[code]} together"


@pytest.mark.parametrize("code", SEPARATED)
def test_the_english_chain_puts_the_case_pair_on_two_terms(
    code: str, pairs: dict[str, Pair], english: TextAnalyzer
) -> None:
    # The assertion the probe of 2026-09-24 was missing. Without it a case can be
    # green while the field it questions carries any folding chain at all.
    pair = pairs[code]

    assert not _share_a_term(english, pair), (
        f"the English chain merges {pair} as well, so a green {code} case would prove nothing about the "
        f"{code} chain; pick a pair out of {CASE_FIXTURES[code].name} that only that chain brings together"
    )


@pytest.mark.parametrize("code", CODES)
def test_the_english_chain_writes_other_terms_than_the_chain_of_the_case(
    code: str, pairs: dict[str, Pair], chains: dict[str, TextAnalyzer], english: TextAnalyzer
) -> None:
    # The criterion that also covers the folded language: whatever the English
    # chain would do with these two forms, it would not write these terms. The
    # term dictionary of the field is held against exactly this further down.
    pair = pairs[code]
    ours = _terms(chains[code], pair.typed) | _terms(chains[code], pair.written)
    theirs = _terms(english, pair.typed) | _terms(english, pair.written)

    assert ours != theirs, (
        f"the English chain writes the same terms for {pair} as the {code} chain, so the term of the field "
        "names no language and the case rests on nothing"
    )


@pytest.mark.parametrize("code", CODES)
def test_no_form_of_the_case_stands_in_this_file(code: str, pairs: dict[str, Pair]) -> None:
    # T-18-04-02. A form copied in here would survive a rebuild of the chains
    # that moves the fixture, and the case would then measure a word the
    # measurement has dropped.
    standing = sorted(form for form in pairs[code] if form.lower() in SOURCE_WORDS)

    assert standing == [], (
        f"{standing} stands in this file as a word; the forms of a case come from "
        f"{CASE_FIXTURES[code].name} and nowhere else, so reword the prose"
    )
