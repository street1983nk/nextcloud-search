"""The Dutch splitter chain, asserted rather than trusted.

Recipe B 4-14 folds the list, so the splitter has to stand behind the fold, and
that one neighbourship is what separates the measured 21 of 28 from 20 of 28 and
a flat spelling that silently stays whole. The guard below reads the order out
of the syntax tree of index/analyzer.py, exactly as the German and the Snowball
guards do, and the token cases run the shipped factory over miniature lists.
The measured tables below run the shipped factory over the fixture of plan
21-04, which the probe generated from the real list and proved token for token
against it (docs/measurements/2026-09-komposita-nl/).

The chain is not wired into the running app by this plan. A chain registered
nowhere changes no tokenisation, which is why ANALYZER_VERSION stays at 1 and
the Dutch mark carries its own chain version instead (D-05).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from findling.config import settings
from findling.index import analyzer
from findling.index.analyzer import (
    ANALYZER_VERSION,
    cached_dutch_analyzer,
    dutch_analyzer,
    dutch_build_count,
    dutch_chain_for,
    snowball_analyzer,
)
from findling.index.wordlist_nl import DUTCH_CHAIN_VERSION, TUSSENKLANKEN, build_artifact_nl
from test_analyzer import ANALYZER_SOURCE, filter_chain

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tantivy import TextAnalyzer

# The shipped Dutch order. The Snowball chain of phase 17 with the splitter and
# its linking element filter put in directly behind the fold.
EXPECTED_DUTCH_CHAIN = [
    "lowercase",
    "ascii_fold",
    "split_compound",
    "custom_stopword",
    "stopword",
    "custom_stopword",
    "remove_long",
    "stemmer",
]

# What each of the two custom stopword filters is fed with, in chain order.
EXPECTED_CUSTOM_STOPWORD_ARGUMENTS = [
    "list(TUSSENKLANKEN)",
    "list(FOLDED_STOPWORDS[SNOWBALL_NAME['nl']])",
]

# Miniature lists in the folded form the recipe produces.
GEMEENTE_LIST = sorted(["gemeente", "belasting", "coordinatie", "centrum", *TUSSENKLANKEN])
WATERSCHAP_LIST = sorted(["waterschap", "belasting", *TUSSENKLANKEN])


FIXTURES = Path(__file__).resolve().parent / "fixtures"

# The case list the probe ran, and the subset of the real list it generated.
CASES_NL = FIXTURES / "compound_cases_nl.txt"
CONSTITUENTS_NL = FIXTURES / "constituents_nl.txt"

# The command that produced every token below, named in the failure messages.
MEASURE_COMPOUNDS_NL = "scripts/dev/measure_compounds_nl.sh"

# The 21 compounds found via their constituent, with the tokens measured on
# 2026-09-25 (docs/measurements/2026-09-komposita-nl/rohdaten/tokens-rezept-b.tsv).
# Each row: compound, constituent, tokens of the compound.
COMPOUNDS_NL = (
    ("gemeentebelastingen", "belasting", ["gemeent", "belast"]),
    ("gemeentebelasting", "belasting", ["gemeent", "belast"]),
    ("inkomstenbelasting", "belasting", ["inkomst", "belast"]),
    ("waterschapsbelasting", "belasting", ["waterschap", "belast"]),
    ("belastingaangifte", "aangifte", ["belast", "aangift"]),
    ("huurovereenkomst", "overeenkomst", ["hur", "overeenkomst"]),
    ("arbeidsovereenkomst", "overeenkomst", ["arbeid", "overeenkomst"]),
    ("koopovereenkomst", "overeenkomst", ["kop", "overeenkomst"]),
    ("bestemmingsplan", "bestemming", ["bestemm", "plan"]),
    ("omgevingsvergunning", "vergunning", ["omgev", "vergunn"]),
    ("parkeervergunning", "vergunning", ["parker", "vergunn"]),
    ("zorgverzekering", "verzekering", ["zorg", "verzeker"]),
    ("ziektekostenverzekering", "verzekering", ["ziektekost", "verzeker"]),
    ("kinderopvangtoeslag", "toeslag", ["kinderopvang", "toeslag"]),
    ("gemeenteraadsvergadering", "vergadering", ["gemeenterad", "vergader"]),
    ("begrotingswijziging", "wijziging", ["begrot", "wijzig"]),
    ("afvalstoffenheffing", "heffing", ["afvalstoff", "heffing"]),
    ("subsidieaanvraag", "aanvraag", ["subsidie", "aanvrag"]),
    ("vergaderverslag", "verslag", ["vergader", "verslag"]),
    ("coördinatiecentrum", "centrum", ["coordinatie", "centrum"]),
    ("coordinatiecentrum", "centrum", ["coordinatie", "centrum"]),
)

# The seven named limits, with their measured tokens. Six stand in the list
# themselves and an entry is never split; onroerendezaakbelasting meets the
# longer entry zaakbelasting, so belast never comes out.
UNSPLIT_NL = (
    ("onroerendezaakbelasting", ["onroer", "zaakbelast"]),
    ("bouwvergunning", ["bouwvergunn"]),
    ("huurtoeslag", ["huurtoeslag"]),
    ("verkeersboete", ["verkeersboet"]),
    ("jaarrekening", ["jaarreken"]),
    ("factuurnummer", ["factuurnummer"]),
    ("opzegtermijn", ["opzegtermijn"]),
)

# The one guard that comes apart, and a real compound: belasting plus plichtig.
SPLIT_GUARD = "belastingplichtige"

# Measured over the whole case list.
EXPECTED_FOUND = 21
EXPECTED_COMPOUNDS = 28
EXPECTED_GUARDS = 33

# A case line with two words is a compound and its constituent.
COMPOUND_LINE_WORDS = 2


def case_lines() -> list[list[str]]:
    """Return the data lines of the case list, split into words."""
    lines = [line.strip() for line in CASES_NL.read_text(encoding="utf-8").split("\n")]
    return [line.split() for line in lines if line and not line.startswith("#")]


def guards() -> list[str]:
    """Return the guard words: the lines of the case list with one word."""
    return [words[0] for words in case_lines() if len(words) == 1]


def compounds() -> list[tuple[str, str]]:
    """Return the compounds of the case list with their constituent."""
    return [(words[0], words[1]) for words in case_lines() if len(words) == COMPOUND_LINE_WORDS]


def found_via_constituent(chain: TextAnalyzer, compound: str, constituent: str) -> bool:
    """Return whether the one token of the constituent stands among the tokens of the compound."""
    wanted = chain.analyze(constituent)
    return len(wanted) == 1 and wanted[0] in chain.analyze(compound)


def custom_stopword_arguments(source: str, function: str) -> list[str]:
    """Return the source of the argument of every custom_stopword filter, in tree order."""
    arguments: list[str] = []
    for definition in ast.walk(ast.parse(source)):
        if not isinstance(definition, ast.FunctionDef) or definition.name != function:
            continue
        for call in ast.walk(definition):
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "custom_stopword"
                and call.args
            ):
                arguments.append(ast.unparse(call.args[0]))
    # ast.walk visits the nested builder outside in, so the last filter comes first.
    arguments.reverse()
    return arguments


@pytest.fixture
def storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A volume the settings point at, with the settings cache cleared on both sides."""
    root = tmp_path / "volume"
    root.mkdir(parents=True)
    monkeypatch.setenv("APP_PERSISTENT_STORAGE", str(root))
    settings.cache_clear()
    yield root
    settings.cache_clear()


@pytest.fixture(scope="module")
def measured_chain() -> TextAnalyzer:
    """The shipped Dutch chain over the generated fixture, built once."""
    entries = [line for line in CONSTITUENTS_NL.read_text(encoding="utf-8").split("\n") if line]
    return dutch_analyzer(entries)


def test_the_dutch_chain_stands_in_the_measured_order() -> None:
    # ascii_fold in front of the splitter: the list is folded, so a splitter in
    # front of the fold would compare the raw token and the flat and the accented
    # spelling would part ways. custom_stopword(TUSSENKLANKEN) directly behind
    # the splitter: without it a bare "s" reaches the index. remove_long behind
    # the splitter, stemmer last, both for the German reasons.
    source = ANALYZER_SOURCE.read_text(encoding="utf-8")

    assert filter_chain(source, "dutch_analyzer") == EXPECTED_DUTCH_CHAIN
    assert custom_stopword_arguments(source, "dutch_analyzer") == EXPECTED_CUSTOM_STOPWORD_ARGUMENTS


def test_the_guard_sees_a_splitter_in_front_of_the_fold() -> None:
    source = (
        "def dutch_analyzer(constituents):\n"
        "    return (\n"
        "        TextAnalyzerBuilder(Tokenizer.simple())\n"
        "        .filter(Filter.lowercase())\n"
        "        .filter(Filter.split_compound(list(constituents)))\n"
        "        .filter(Filter.ascii_fold())\n"
        "        .build()\n"
        "    )\n"
    )

    chain = filter_chain(source, "dutch_analyzer")

    assert chain.index("split_compound") < chain.index("ascii_fold")
    assert chain != EXPECTED_DUTCH_CHAIN


def test_the_splitter_stands_behind_the_fold() -> None:
    chain = dutch_analyzer(GEMEENTE_LIST)

    assert chain.analyze("gemeentebelastingen") == ["gemeent", "belast"]
    assert chain.analyze("Gemeentebelastingen") == ["gemeent", "belast"]
    # The case recipe A loses: the list is folded, so both spellings come apart
    # and land on the same terms.
    accented = chain.analyze("coördinatiecentrum")
    assert len(accented) == 2
    assert accented == chain.analyze("coordinatiecentrum")


def test_no_bare_linking_element_reaches_the_index() -> None:
    tokens = dutch_analyzer(WATERSCHAP_LIST).analyze("waterschapsbelasting")

    assert tokens == ["waterschap", "belast"]
    assert [token for token in tokens if len(token) == 1] == []


def test_the_dutch_automaton_is_built_once() -> None:
    digest = "test-digest-built-once"
    before = dutch_build_count()

    first = cached_dutch_analyzer(digest, GEMEENTE_LIST)
    second = cached_dutch_analyzer(digest, GEMEENTE_LIST)

    assert first is second
    assert dutch_build_count() == before + 1


def test_without_dutch_the_chain_is_the_snowball_one() -> None:
    before = dutch_build_count()

    chain = dutch_chain_for(None)

    word = "gemeentebelastingen"
    assert chain.analyze(word) == snowball_analyzer("dutch").analyze(word)
    assert len(chain.analyze(word)) == 1
    assert dutch_build_count() == before


def test_a_chain_for_a_digest_the_volume_does_not_hold_fails_closed(storage: Path, tmp_path: Path) -> None:
    source = tmp_path / "dutch"
    with source.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("gemeente\nbelasting\n")
    held = build_artifact_nl(source)

    with pytest.raises(ValueError, match="digest") as raised:
        dutch_chain_for("falscher-digest")

    # The message names no path of the volume.
    assert str(storage) not in str(raised.value)
    # The digest the volume does hold builds its chain.
    assert dutch_chain_for(held.digest).analyze("gemeentebelasting") == ["gemeent", "belast"]


def test_the_analyzer_version_stays_where_it_was() -> None:
    # D-05: raising ANALYZER_VERSION would order a full reindex of roughly 19 h
    # on every installation, with or without nl. The Dutch mark carries its own
    # chain version instead.
    assert ANALYZER_VERSION == 1
    assert DUTCH_CHAIN_VERSION == 1
    assert "wordlist_hash_nl" in (analyzer.__doc__ or "")


@pytest.mark.parametrize(("compound", "constituent", "tokens"), COMPOUNDS_NL, ids=[row[0] for row in COMPOUNDS_NL])
def test_the_measured_compounds_produce_the_measured_tokens(
    measured_chain: TextAnalyzer, compound: str, constituent: str, tokens: list[str]
) -> None:
    assert measured_chain.analyze(compound) == tokens
    assert found_via_constituent(measured_chain, compound, constituent)


@pytest.mark.parametrize(("word", "tokens"), UNSPLIT_NL, ids=[row[0] for row in UNSPLIT_NL])
def test_the_named_limits_stay_as_measured(measured_chain: TextAnalyzer, word: str, tokens: list[str]) -> None:
    assert measured_chain.analyze(word) == tokens


def test_the_sentinels_stay_whole(measured_chain: TextAnalyzer) -> None:
    words = guards()
    assert len(words) == EXPECTED_GUARDS

    apart = {word: measured_chain.analyze(word) for word in words if len(measured_chain.analyze(word)) != 1}

    assert apart == {SPLIT_GUARD: ["belast", "plichtig"]}


def test_the_measured_hit_count_holds_over_the_whole_case_list(measured_chain: TextAnalyzer) -> None:
    cases = compounds()
    found = [compound for compound, part in cases if found_via_constituent(measured_chain, compound, part)]

    assert len(cases) == EXPECTED_COMPOUNDS
    assert len(found) == EXPECTED_FOUND, (
        f"{len(found)} of {len(cases)} found, measured was {EXPECTED_FOUND}; rerun {MEASURE_COMPOUNDS_NL}"
    )


def test_every_asserted_word_stands_in_the_measured_case_list() -> None:
    # The guard over the guard. Every word this module makes a claim about has to
    # be a word the probe of plan 21-04 really ran against the real Debian list,
    # otherwise the table could grow a line that was never measured.
    measured = {word for words in case_lines() for word in words}
    asserted = [word for row in COMPOUNDS_NL for word in row[:2]] + [row[0] for row in UNSPLIT_NL] + [SPLIT_GUARD]

    missing = sorted(word for word in asserted if word not in measured)

    assert missing == [], (
        f"asserted here but never measured, add to {CASES_NL.name} and rerun {MEASURE_COMPOUNDS_NL}: {missing}"
    )


def test_without_the_splitter_no_compound_is_found_via_its_constituent() -> None:
    # The counter proof of the CI case: the chain every installation has had
    # since phase 17 keeps each compound as one term, so its constituent never
    # finds it. Measured 0 of 28.
    plain = snowball_analyzer("dutch")

    found = [compound for compound, part in compounds() if found_via_constituent(plain, compound, part)]

    assert len(compounds()) == EXPECTED_COMPOUNDS
    assert found == []
