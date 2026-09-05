"""The three language files under testdata/semantik, held against the one rule that makes them worth measuring.

A retrieval test set is easy to build and easy to build wrongly, and the wrong
one is not obviously wrong: if the words of the question also stand in the target
passage, then every method finds that passage, the lexical index best of all, and
the resulting number says nothing whatsoever about semantics. Such a set measures
full text search and reports it as proof of an embedding model.

So the rule is mechanical here rather than a paragraph of good intentions: **no
content word of a query may stand verbatim in its own passage**. Function words
are exempt, because a paraphrase cannot avoid articles and prepositions, and a
list of them per language is kept below. A violation is a red test that names the
identifier of the case and never the text of it, which is the same discipline the
measuring tool follows (T-02-14, T-06-11).

The passages of one language are at the same time the distractor set of that
language: every query competes against all the other passages of its file, so a
second list is not needed and cannot drift away from the first.

Two halves live in this file. The first, from plan 06-03 task 1, is the well
formedness of the data. The second, from task 2, is the behaviour of
``scripts/dev/model_quality.py``, which reads exactly these files.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
DATASET_DIR: Final = REPO_ROOT / "testdata" / "semantik"
README_PATH: Final = DATASET_DIR / "README.md"

LANGUAGES: Final = ("de", "en", "fr")
MINIMUM_CASES: Final = 40
FIELDS: Final = ("id", "query", "passage", "note")

# Letters and digits, no underscore, and the apostrophe is a separator rather
# than a letter. That last part is what makes the French cases checkable at all:
# "l'immeuble" has to become "l" and "immeuble", or the elided article would hide
# the noun behind it from the rule.
WORD: Final = re.compile(r"[^\W_]+")

# The function words of the three languages: articles, pronouns, prepositions,
# conjunctions, auxiliaries, modals and question words. They are exempt from the
# rule because a paraphrase cannot be written without them, and because their
# presence in both halves of a case tells nobody anything. Everything that is not
# in these sets counts as content, including numerals, which is deliberate: a
# date that stands in both halves is a lexical bridge like any other.
GERMAN_FUNCTION_WORDS: Final = """
    aber alle allem allen aller alles als also am an auch auf aus bei beim bin bis da dabei dadurch daher damit
    dann daran darf das dass dem den denn der des deshalb dessen die dies diese diesem diesen dieser dieses
    doch dort du durch ein eine einem einen einer eines er es etwas euch für gegen gewesen habe haben hat
    hatte hatten hier ich ihm ihn ihnen ihr ihre ihrem ihren ihrer im in ins ist ja je jede jedem jeden jeder
    jedes jetzt kann kein keine keinen keiner können könnte man mehr mein meine meinem meinen meiner mich mir
    mit muss musste müssen nach nicht nichts noch nun nur ob obwohl oder ohne schon sehr sein seine seinem
    seinen seiner seit sich sie sind so soll sollen sollte sondern um und uns unser unsere unserem unseren
    unter viel vom von vor war waren warum was weil welche welchem welchen welcher welches wem wen wenn wer
    werde werden weshalb wie wieder wir wird wo wobei wodurch womit woran worauf wovon wozu wurde wurden würde
    würden während über ab neben zu zum zur zwischen
    """

ENGLISH_FUNCTION_WORDS: Final = """
    a about above after again against all also am an and any are as at be because been before being below
    between both but by can could did do does doing done down during each every few for from further had has
    have having he her here hers him his how i if in into is it its itself just may me might mine more most
    much must my no nor not now of off on once one only or other our ours out over own per shall she should
    since so some still such than that the their theirs them then there these they this those through to too
    under until up us very was we were what when where which while who whom whose why will with within would
    you your yours
    """

FRENCH_FUNCTION_WORDS: Final = """
    a à ai alors as au aucun aucune aujourd auprès aura auront aux avaient avait avant avec avez avoir avons c
    car ce ceci cela celle celles celui ces cet cette ceux chaque chez combien comme comment d dans de depuis
    des dès doit doivent dois donc dont du durant elle elles en encore es est et étaient était été êtes être
    eux faut il ils j je jusqu l la là le lequel les leur leurs lors lorsque lui m ma mais me même mes mien moins
    mon n ne ni nos notre nous on ont ou où par parce pas peut peuvent plus plusieurs pour pourquoi pouvez
    puis qu quand que quel quelle quelles quels qui quoi s sa sans se sera seront ses si sien soit son sont
    sous suis sur t ta te tes toi ton tous tout toute toutes très trop tu un une vers vos votre vous y
    """

STOPWORDS: Final[Mapping[str, frozenset[str]]] = {
    "de": frozenset(GERMAN_FUNCTION_WORDS.split()),
    "en": frozenset(ENGLISH_FUNCTION_WORDS.split()),
    "fr": frozenset(FRENCH_FUNCTION_WORDS.split()),
}

# Assembled from code points, because this file would otherwise fail on itself.
DASHES: Final = (chr(0x2014), chr(0x2013))


def tokens(text: str) -> list[str]:
    """The words of a text: lowercased, punctuation dropped, digits kept as words of their own."""
    return WORD.findall(text.lower())


def content_words(text: str, language: str) -> set[str]:
    return set(tokens(text)) - STOPWORDS[language]


def overlapping_words(record: Mapping[str, str], language: str) -> set[str]:
    """The content words of the query that also stand in its passage. Empty is the only acceptable answer."""
    return content_words(record["query"], language) & set(tokens(record["passage"]))


@cache
def raw_lines(language: str) -> tuple[str, ...]:
    text = (DATASET_DIR / f"{language}.jsonl").read_text(encoding="utf-8")
    return tuple(text.splitlines())


@cache
def cases(language: str) -> tuple[dict[str, str], ...]:
    return tuple(json.loads(line) for line in raw_lines(language))


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_line_is_one_record_with_the_four_fields(language: str) -> None:
    for number, line in enumerate(raw_lines(language), start=1):
        assert line.strip(), f"{language}.jsonl line {number} is empty"
        record = json.loads(line)
        assert isinstance(record, dict), f"{language}.jsonl line {number}"
        assert tuple(sorted(record)) == tuple(sorted(FIELDS)), f"{language}.jsonl line {number}"
        for field in FIELDS:
            assert isinstance(record[field], str), f"{language}.jsonl line {number} field {field}"
            assert record[field].strip(), f"{language}.jsonl line {number} field {field} is empty"


@pytest.mark.parametrize("language", LANGUAGES)
def test_each_language_carries_at_least_forty_cases(language: str) -> None:
    assert len(cases(language)) >= MINIMUM_CASES


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_identifiers_are_unique_within_a_language(language: str) -> None:
    identifiers = [record["id"] for record in cases(language)]
    duplicates = sorted({identifier for identifier in identifiers if identifiers.count(identifier) > 1})
    assert duplicates == [], f"{language}: {duplicates}"
    assert all(identifier.startswith(f"{language}-") for identifier in identifiers)


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_passages_are_distinct_within_a_language(language: str) -> None:
    """The passages are the distractor set, so two identical ones would make a rank undecidable."""
    passages = [record["passage"] for record in cases(language)]
    repeated = sorted({record["id"] for record in cases(language) if passages.count(record["passage"]) > 1})
    assert repeated == [], f"{language}: {repeated}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_no_content_word_of_a_query_stands_in_its_own_passage(language: str) -> None:
    """The rule. A case that fails here measures the lexical index and claims semantics.

    The failure names identifiers and the offending words, never a query and
    never a passage: this suite is read in CI logs that are more public than the
    corpus behind them.
    """
    offenders = {
        record["id"]: sorted(overlapping_words(record, language))
        for record in cases(language)
        if overlapping_words(record, language)
    }
    assert offenders == {}, f"{language}: word overlap in {offenders}"


def test_the_overlap_check_goes_red_on_a_case_that_would_measure_full_text_search() -> None:
    """The gate is shown to be able to fire, on a case built for the purpose.

    Without this, a rule that silently matched nothing would look exactly like a
    rule that everybody obeyed.
    """
    lexical = {
        "id": "de-probe",
        "query": "Wie hoch ist die Kündigungsfrist?",
        "passage": "Die Kündigungsfrist beträgt drei Monate zum Quartalsende.",
        "note": "A case that shares its content word and therefore proves nothing about semantics.",
    }
    assert overlapping_words(lexical, "de") == {"kündigungsfrist"}

    paraphrase = {
        "id": "de-probe-2",
        "query": "Wie lange vorher muss ich aussteigen?",
        "passage": "Die Kündigungsfrist beträgt drei Monate zum Quartalsende.",
        "note": "The same passage, asked for without any of its words.",
    }
    assert overlapping_words(paraphrase, "de") == set()


def test_the_apostrophe_does_not_hide_a_french_noun_from_the_rule() -> None:
    """l'autorisation has to be seen as autorisation, or the elision would be a loophole."""
    elided = {
        "id": "fr-probe",
        "query": "Quand expire l'autorisation ?",
        "passage": "L'autorisation devient caduque au bout de trois ans.",
        "note": "A case whose only shared word hides behind an elided article.",
    }
    assert overlapping_words(elided, "fr") == {"autorisation"}


def test_the_german_cases_carry_real_umlauts_and_a_sharp_s() -> None:
    text = (DATASET_DIR / "de.jsonl").read_text(encoding="utf-8")
    for character in ("ä", "ö", "ü", "ß"):
        assert character in text, character
    assert "\\u" not in text, "escaped code points instead of the characters themselves"


def test_the_french_cases_carry_accents_and_a_cedilla() -> None:
    text = (DATASET_DIR / "fr.jsonl").read_text(encoding="utf-8")
    for character in ("é", "è", "à", "ç"):
        assert character in text, character
    assert "\\u" not in text, "escaped code points instead of the characters themselves"


def test_no_dash_stands_in_the_five_files() -> None:
    for path in (README_PATH, *(DATASET_DIR / f"{language}.jsonl" for language in LANGUAGES), Path(__file__)):
        text = path.read_text(encoding="utf-8")
        for dash in DASHES:
            assert dash not in text, f"{dash!r} in {path.name}"


def test_the_readme_names_the_rule_the_origin_the_licence_and_the_absence_of_personal_data() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    for phrase in ("Wortüberschneidung", "Herkunft", "Lizenz", "personenbezogene"):
        assert phrase in readme, phrase


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_readme_states_the_true_number_of_cases(language: str) -> None:
    """A count in prose drifts away from the files it counts unless something holds it."""
    rows = [line for line in README_PATH.read_text(encoding="utf-8").splitlines() if f"{language}.jsonl" in line]
    assert rows, f"the README does not mention {language}.jsonl"
    assert any(str(len(cases(language))) in row for row in rows), f"{language}: count not stated"
