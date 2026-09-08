"""The gate in front of a new German language case in the CI workflow.

A language case in ``.github/workflows/integration.yml`` asserts that one search
term brings back exactly one file. That assertion is only worth something if the
term really stands in exactly one file, and the honest place to find that out is
here, before the case is written, rather than in a red run on ``main`` twenty
minutes later. The workflow itself runs on ``main`` and on pull requests only;
this module is the local half of the same statement and it runs in every suite.

Two gates, and the second one is the one that earns its place.

The first gate runs over **tokens**, because tokens are the question the search
really asks: the term is analysed, every corpus file is analysed, and the term
belongs to a file when the file carries all of its tokens. A term that comes
apart inside a second compound hits that second file too, and no comparison of
plain strings would see it.

The second gate runs over the letters of the term and it exists because the
first one is measured against the fixture, while CI is measured against the
full Debian list of the image. The fixture cannot split a corpus word whose
parts were never part of a measured case, so it can only ever report a term as
more unique than it is, never as less. Whenever a second file merely contains
the letters of the term, some word list can split it there, and the term is
rejected. That is a deliberately conservative rule and it is the rule that
throws out ``Verkehr`` and ``Abgabe`` below.

Umlauts appear only inside string literals, as data. The identifiers stay ASCII
as the project rules require.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
from tantivy import TextAnalyzer

from findling.index.analyzer import german_analyzer

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_CORPUS = REPO_ROOT / "scripts" / "dev" / "build_corpus.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"

# The three constituents the workflow searches for since phase 8, and the file
# each one has to bring back on its own. Every one of them is the second part of
# a compound that stands in that file, every one of them has a measured line in
# docs/measurements/2026-09-komposita-rezept-a/rohdaten/tokens-rezept-a.tsv, and
# the two scanned ones sit on pages that the OCR measurement of 2026-09-06 read
# with a character error rate of zero.
CI_TERMS: dict[str, str] = {
    # Pachtvereinbarung, in the text layer of the file.
    "Vereinbarung": "14-pacht-mit-anhang.pdf",
    # Grundbuchsauszug, pixels only.
    "Auszug": "16-oesterreich-mitteilung.pdf",
    # Zahlungserinnerung, pixels only.
    "Erinnerung": "30-nur-ein-bild.pdf",
}

# The counter proof. Without a term that fails, a gate which is always green
# looks exactly like a gate that works. This word stands in three files of the
# corpus, so it is the shape of term that must never become a language case.
AMBIGUOUS = "Rechnung"

# The two candidates the phase research proposed and this module rejects, with
# the second file that costs them the case. Both pass the token gate against the
# fixture and both fail the letter gate, which is the whole reason the letter
# gate exists.
LETTER_TRAPS: dict[str, str] = {
    # Grundstuecksverkehrsgenehmigung stands in 09-bescheid.pdf, but
    # Parteienverkehr stands in the Austrian notice.
    "Verkehr": "16-oesterreich-mitteilung.pdf",
    # Ersatzabgabe stands in the Swiss permit, Verwaltungsabgabe in the Austrian
    # notice. Measured as finding 1 of the phase measurement.
    "Abgabe": "15-schweiz-baubewilligung.pdf",
}

# What tesseract really reads off the headline of 19-uebermittlung.tif, measured
# in the shipping image on 2026-09-01 and written down in docs/ocr.md: the two
# dots over the capital letter are gone. The word the generator draws is next to
# it. This pair is why "Protokoll" is not among the three terms above.
HEADLINE_AS_DRAWN = "Übermittlungsprotokoll"
HEADLINE_AS_READ = "Ubermittlungsprotokoll"


def _load_build_corpus() -> ModuleType:
    """The corpus generator as a module, because it is a script and not a package."""
    specification = importlib.util.spec_from_file_location("build_corpus_terms_under_test", BUILD_CORPUS)
    if specification is None or specification.loader is None:
        pytest.skip("the corpus generator is not where it is expected to be")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def german() -> TextAnalyzer:
    """One German analyser for the whole module; building it is not free."""
    return german_analyzer(FIXTURE.read_text(encoding="utf-8").split())


@pytest.fixture(scope="module")
def searchable() -> dict[str, str]:
    """Everything a search could find in each corpus file, pixels included.

    Taken from the generator rather than from the built files, because the text
    of a scanned page exists as pixels and a reader of the bytes would find
    nothing there. The generator is the ground truth of that prose.
    """
    module = _load_build_corpus()
    return {name: module._searchable_text(name, payload) for name, payload in module.FILES.items()}


@pytest.fixture(scope="module")
def tokens_per_file(german: TextAnalyzer, searchable: dict[str, str]) -> dict[str, set[str]]:
    """The token set of every corpus file, which is what the index really holds."""
    return {name: set(german.analyze(text)) for name, text in searchable.items()}


def _carriers(german: TextAnalyzer, tokens_per_file: dict[str, set[str]], term: str) -> list[str]:
    """The files whose token set covers every token of the term."""
    wanted = set(german.analyze(term))
    if not wanted:
        return []
    return sorted(name for name, held in tokens_per_file.items() if wanted <= held)


def _letter_carriers(searchable: dict[str, str], term: str) -> list[str]:
    """The files whose searchable text contains the letters of the term at all."""
    return sorted(name for name, text in searchable.items() if term.lower() in text)


@pytest.mark.parametrize(("term", "owner"), sorted(CI_TERMS.items()))
def test_a_ci_term_is_analysed_into_tokens_at_all(german: TextAnalyzer, term: str, owner: str) -> None:
    # The first thing that can go wrong is the least visible one: a term the
    # chain throws away entirely, for instance because it is a stopword, comes
    # back as the empty token list and would then trivially be a subset of every
    # file. The uniqueness assertion below would be green and would mean nothing.
    assert german.analyze(term) != [], f"the chain produces no token for {term!r}, so it cannot find {owner}"


@pytest.mark.parametrize(("term", "owner"), sorted(CI_TERMS.items()))
def test_a_ci_term_stands_in_exactly_one_corpus_file(
    german: TextAnalyzer, tokens_per_file: dict[str, set[str]], term: str, owner: str
) -> None:
    carriers = _carriers(german, tokens_per_file, term)

    assert carriers == [owner], f"{term!r} has to bring back {owner} alone, but its tokens stand in {carriers}"


@pytest.mark.parametrize(("term", "owner"), sorted(CI_TERMS.items()))
def test_a_ci_term_survives_the_list_independent_gate(searchable: dict[str, str], term: str, owner: str) -> None:
    # The gate that does not care which word list is in use. The token gate above
    # runs against the fixture and the workflow runs against the full Debian
    # list, so the token gate can call a term unique that a richer list would
    # split in a second file as well. If no second file even contains the
    # letters, no list can do that.
    assert _letter_carriers(searchable, term) == [owner], (
        f"{term!r} has to be the only file spelling those letters, "
        f"but they stand in {_letter_carriers(searchable, term)}"
    )


def test_an_ambiguous_term_is_rejected_by_the_same_gate(
    german: TextAnalyzer, tokens_per_file: dict[str, set[str]]
) -> None:
    # The counter proof. A gate that cannot say no is not a gate.
    carriers = _carriers(german, tokens_per_file, AMBIGUOUS)

    assert len(carriers) > 1, f"{AMBIGUOUS!r} was expected to be ambiguous, but it only stands in {carriers}"
    assert AMBIGUOUS not in CI_TERMS


@pytest.mark.parametrize(("term", "second_file"), sorted(LETTER_TRAPS.items()))
def test_a_rejected_candidate_passes_the_token_gate_and_fails_the_letter_gate(
    german: TextAnalyzer,
    tokens_per_file: dict[str, set[str]],
    searchable: dict[str, str],
    term: str,
    second_file: str,
) -> None:
    # The two candidates that would have looked perfectly buildable. Against the
    # fixture each of them has exactly one carrier, so a module with only the
    # token gate would have waved both through and the workflow would have gone
    # red on main. The letter gate sees the second file.
    assert len(_carriers(german, tokens_per_file, term)) == 1
    letters = _letter_carriers(searchable, term)
    assert len(letters) > 1, f"{term!r} was expected to be ambiguous by letters, found {letters}"
    assert second_file in letters
    assert term not in CI_TERMS


def test_the_headline_the_engine_really_reads_does_not_come_apart(german: TextAnalyzer) -> None:
    # Why "Protokoll" is not a language case, although the compound it belongs to
    # is measured and although the term stands in one file only. The engine reads
    # the bold headline of 19-uebermittlung.tif without the dots over the capital
    # letter, and the constituent list carries the word with them. So the word
    # that reaches the index is one token, and a search for the second part finds
    # nothing at all. The word as drawn comes apart, the word as read does not,
    # and only the second one is ever indexed.
    assert len(german.analyze(HEADLINE_AS_DRAWN)) == 2
    assert german.analyze(HEADLINE_AS_READ) == [HEADLINE_AS_READ.lower()]


def test_every_ci_term_is_carried_by_the_uniqueness_check_of_the_generator() -> None:
    # The generator has its own uniqueness check and it runs on every build of
    # the corpus. A term that the workflow asserts on but that check does not
    # know is a term that can quietly become ambiguous with the next corpus file.
    module = _load_build_corpus()

    missing = sorted(term for term in CI_TERMS if term not in module.UNIQUE_TERMS)

    assert missing == [], f"add to UNIQUE_TERMS in {BUILD_CORPUS.name}: {missing}"
    for term, owner in CI_TERMS.items():
        assert module.UNIQUE_TERMS[term] == owner
