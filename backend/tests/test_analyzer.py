"""The German chain, asserted token by token.

This table asserts WHAT is split, not THAT something was split. The difference is
the whole value of the file: a test that only checks "more than one token came
back" stays green while the splitter produces confetti, and that is exactly how
the naive recipe passed review elsewhere.

Every expectation below was measured against the real Debian list
(/usr/share/dict/ngerman, 276496 entries after recipe A) inside the container
image the app ships on. The fixture in tests/fixtures/constituents_de.txt is the
subset of that list whose entries occur inside the test inputs; the generator
verified that the subset produces byte identical tokens for every input here, so
the table is the behaviour of the real list, not of a convenient miniature. A
developer machine has no Debian word list, and a test that skips itself when the
list is missing is a test that never runs.

Umlauts appear only inside string literals. They are data here, the words the
product has to handle; the identifiers stay ASCII as the project rules require.
"""

from pathlib import Path

import pytest
from tantivy import TextAnalyzer

from findling.index.analyzer import (
    ANALYZER_VERSION,
    TOKENIZER_DE,
    TOKENIZER_EN,
    TOKENIZER_NAME,
    build_count,
    cached_german_analyzer,
    english_analyzer,
    german_analyzer,
    name_analyzer,
)
from findling.index.wordlist import wordlist_hash

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"

# The 63 character one. Its own name below, because it is the cheapest insurance
# this project can buy: with remove_long in front of the splitter it yields the
# empty token list and the document becomes unfindable under any of its parts.
RINDFLEISCH = "Rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz"

# Sixteen real administrative compounds with the tokens the full Debian list
# produces. Fourteen of them become findable through one of their parts; the last
# two are the honest limit of the recipe and are listed for exactly that reason.
COMPOUNDS = [
    ("Grundstücksverkehrsgenehmigung", ["grundstuck", "verkehr", "genehm"]),
    ("Kündigungsfrist", ["kundig", "frist"]),
    ("Sitzungsvorlage", ["sitzung", "vorlag"]),
    ("Haushaltssatzung", ["haushalt", "satzung"]),
    ("Jahresabschluss", ["jahr", "abschluss"]),
    ("Betriebskostenabrechnung", ["betriebskost", "abrechn"]),
    ("Krankenversicherung", ["krank", "versicher"]),
    ("Rechnungsnummer", ["rechnung", "numm"]),
    ("Datenschutzgrundverordnung", ["datenschutz", "grund", "verordn"]),
    ("Bundesausbildungsförderungsgesetz", ["bund", "ausbild", "forder", "gesetz"]),
    (RINDFLEISCH, ["rindfleisch", "etikettier", "uberwach", "aufgab", "ubertrag", "gesetz"]),
    ("Dampfschifffahrt", ["dampfschiff", "fahrt"]),
    ("Aufenthaltserlaubnis", ["aufenthalt", "erlaubnis"]),
    ("Gewerbeanmeldung", ["gewerb", "anmeld"]),
    # Eleven and thirteen characters, both stand in the list themselves, and a
    # compound in the list is never split. "Mietvertrag" is not findable through
    # "Vertrag". Documented in docs/german-analyzer.md, not a defect.
    ("Mietvertrag", ["mietvertrag"]),
    ("Bebauungsplan", ["bebauungsplan"]),
]

# Ten everyday words that must survive whole. A recipe that splits any of them
# produces nonsense terms instead of better recall.
UNSPLIT = [
    ("Information", "information"),
    ("Vertrag", "vertrag"),
    ("Rechnung", "rechnung"),
    ("Sitzung", "sitzung"),
    ("Kunde", "kund"),
    ("Formular", "formular"),
    ("Termin", "termin"),
    ("Ordnung", "ordnung"),
    ("Beamter", "beamt"),
    ("Genehmigung", "genehm"),
]


@pytest.fixture(scope="module")
def constituents() -> list[str]:
    """The measured constituent subset, read once for the whole module."""
    return FIXTURE.read_text(encoding="utf-8").split()


@pytest.fixture(scope="module")
def german(constituents: list[str]) -> TextAnalyzer:
    """One German analyser for the whole module; building it is not free."""
    return german_analyzer(constituents)


@pytest.mark.parametrize(("text", "expected"), COMPOUNDS, ids=[text for text, _ in COMPOUNDS])
def test_the_sixteen_compounds_produce_the_measured_tokens(german: TextAnalyzer, text: str, expected: list[str]) -> None:
    assert german.analyze(text) == expected


def test_the_sixty_three_character_compound_does_not_disappear(german: TextAnalyzer) -> None:
    tokens = german.analyze(RINDFLEISCH)

    # Measured: with remove_long(40) at position two this is []. The word is then
    # gone from the index and the document is unfindable under any of its parts.
    # tantivy's own default analyzer makes exactly this mistake.
    assert tokens != []
    assert len(tokens) == 6
    assert "gesetz" in tokens


def test_no_bare_linking_element_reaches_the_index(german: TextAnalyzer) -> None:
    tokens = german.analyze("Kündigungsfrist")

    # Without custom_stopword(FUGEN) this is ["kundig", "s", "frist"], and "s"
    # then matches every second document in the corpus.
    assert tokens == ["kundig", "frist"]
    assert "s" not in tokens


@pytest.mark.parametrize(("text", "expected"), UNSPLIT, ids=[text for text, _ in UNSPLIT])
def test_ten_everyday_words_stay_whole(german: TextAnalyzer, text: str, expected: str) -> None:
    assert german.analyze(text) == [expected]


def test_german_stopwords_leave_nothing_behind(german: TextAnalyzer) -> None:
    # The built in list carries real umlauts and compares exactly, which is why
    # it stands after the splitter and before any folding.
    assert german.analyze("für über während könnte und der die das") == []


@pytest.mark.parametrize(
    ("singular", "plural"),
    [("Haus", "Häuser"), ("Vertrag", "Verträge"), ("Straße", "Strasse")],
)
def test_nominal_inflection_collapses_into_one_term(german: TextAnalyzer, singular: str, plural: str) -> None:
    assert german.analyze(singular) == german.analyze(plural)


def test_the_stemmer_folds_umlauts_without_a_folding_filter(german: TextAnalyzer) -> None:
    # This is why there is no ascii_fold in the German branch. Folding before the
    # splitter would make the list, which carries umlauts, unmatchable, and the
    # splitting would fail silently.
    assert german.analyze("Müller") == german.analyze("Muller") == ["mull"]


def test_documented_limit_d2_past_tense_is_not_unified(german: TextAnalyzer) -> None:
    # Infinitive and noun meet, past tense and participle do not. Not fixable
    # without replacing the stemmer, so the acceptance criterion of CONTEXT.md is
    # restated on nominal inflection. See docs/german-analyzer.md, "Known limits".
    assert german.analyze("suchen") == german.analyze("Suche") == ["such"]
    assert german.analyze("suchte") == ["sucht"]
    assert german.analyze("gesucht") == ["gesucht"]


def test_documented_limit_d3_spelled_out_umlaut_does_not_meet_the_umlaut(german: TextAnalyzer) -> None:
    # "Mueller" and "Müller" are the same name to a human and two terms to the
    # index. The fix belongs on the query side, plan 02-09: a query containing
    # ue, oe, ae or ss also gets the umlaut variant, joined with Occur.Should.
    # See docs/german-analyzer.md, "Known limits".
    assert german.analyze("Mueller") == ["muell"]
    assert german.analyze("Müller") == ["mull"]
    assert german.analyze("Mueller") != german.analyze("Müller")


def test_the_english_analyzer_folds_where_the_german_one_must_not(german: TextAnalyzer) -> None:
    english = english_analyzer()

    # A different algorithm stems here, so folding is safe and useful.
    assert english.analyze("Müller") == ["muller"]
    assert english.analyze("Müller") != german.analyze("Müller")
    assert english.analyze("the running documents") == ["run", "document"]


def test_the_name_analyzer_folds_and_does_not_stem() -> None:
    tokens = name_analyzer().analyze("Kündigungsfrist_2024.pdf")

    # A file name is looked for as it is written. Stemming it would make
    # "Kuendigung.pdf" and "Kuendigungen.pdf" the same file name.
    assert tokens == ["kundigungsfrist", "2024", "pdf"]


def test_analyzer_is_built_once(constituents: list[str]) -> None:
    # A second build in the same process is not a blemish. It is 0.44 s and
    # roughly 23 MB again, which on a 4 GB box is the difference between a search
    # service and a memory problem.
    digest = wordlist_hash(constituents) + "-built-once"
    before = build_count()

    first = cached_german_analyzer(digest, constituents)
    second = cached_german_analyzer(digest, constituents)

    assert first is second
    assert build_count() - before == 1


def test_a_changed_word_list_forces_a_new_automaton(constituents: list[str]) -> None:
    before = build_count()

    cached_german_analyzer("digest-a", constituents)
    cached_german_analyzer("digest-b", constituents)

    # The cache is keyed on the digest of the list, because a changed list is a
    # changed tokenisation (T-02-11).
    assert build_count() - before == 2


def test_the_tokenizer_names_are_the_ones_the_schema_stores() -> None:
    # The schema persists the name of a tokenizer, never the tokenizer. Opening
    # an index without registering these exact names fails at the first query
    # with an error that reads like a broken index.
    assert (TOKENIZER_DE, TOKENIZER_EN, TOKENIZER_NAME) == ("de", "en", "name")


def test_the_analyzer_version_is_pinned_next_to_the_chain() -> None:
    # Tokenisation is part of the data. Every change to the chain above has to
    # raise this number, because the index and the query parser have to agree.
    assert ANALYZER_VERSION == 1
