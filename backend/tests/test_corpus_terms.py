"""The gate in front of a new German language case in the CI workflow.

A language case in ``.github/workflows/integration.yml`` asserts that one search
term brings back exactly one file. That assertion is only worth something if the
term really stands in exactly one file, and the honest place to find that out is
here, before the case is written, rather than in a red run on ``main`` twenty
minutes later. The workflow itself runs on ``main`` and on pull requests only;
this module is the local half of the same statement and it runs in every suite.

Three gates, and the second and the third are the ones that earn their place.

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

The third gate runs over the **splitter** and it was added by the audit of phase
8. The first two only ask whether a term is unique; neither of them asks whether
the term needs ``Filter.split_compound`` to find its file at all. A term whose
word also stands on its own in the same document is unique, is green, and proves
nothing about the decomposition, which is exactly what the language case for
``Vereinbarung`` did until it was replaced. So every CI term is analysed a second
time through the shipped chain minus the splitter, and it has to find nothing.

Above all three sits a fourth statement, and it is about this file rather than
about the corpus: every word this module claims anything about has to stand in
``fixtures/compound_cases_de.txt``, the list that
``scripts/dev/measure_compounds.sh`` really ran against the Debian list of the
image. A claim about a word nobody measured is a claim about the fixture, and
the claims here travel straight into a CI step.

Umlauts appear only inside string literals, as data. The identifiers stay ASCII
as the project rules require.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

import pytest
from tantivy import Filter, TextAnalyzer, TextAnalyzerBuilder, Tokenizer

from findling.index.analyzer import MAX_TOKEN_CHARS, german_analyzer
from findling.index.wordlist import FUGEN

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_CORPUS = REPO_ROOT / "scripts" / "dev" / "build_corpus.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
# The list of words scripts/dev/measure_compounds.sh really ran against the
# Debian list of the image. Read here for the same reason test_analyzer.py reads
# it: a claim about a word that was never measured is a claim about nothing.
CASES = Path(__file__).resolve().parent / "fixtures" / "compound_cases_de.txt"

# The three constituents the workflow searches for since phase 8, and the file
# each one has to bring back on its own. Every one of them is the second part of
# a compound that stands in that file, every one of them has a measured line in
# docs/measurements/2026-09-komposita-rezept-a/rohdaten/tokens-rezept-a.tsv, and
# all three sit on scanned pages that the OCR measurement of 2026-09-06 read with
# a character error rate of zero (pages 4, 5 and 6).
CI_TERMS: dict[str, str] = {
    # Rechtsmittelbelehrung, pixels only.
    "Belehrung": "15-schweiz-baubewilligung.pdf",
    # Grundbuchsauszug, pixels only.
    "Auszug": "16-oesterreich-mitteilung.pdf",
    # Zahlungserinnerung, pixels only.
    "Erinnerung": "30-nur-ein-bild.pdf",
}

# The term that was a language case until the audit of phase 8 and is not one
# any more, kept here as the named counter example rather than deleted.
# "Pachtvereinbarung" stands in the lease, so the search looked like the other
# two, but the very same file also writes "Vereinbarung" out twice on its own:
#
#     'Sonnenhang wird die nachstehende Vereinbarung geschlossen.'
#     'Die Anlagen 1 bis 3 dieser Vereinbarung liegen als Kopie der'
#
# The hit therefore stood with or without Filter.split_compound, and a case that
# is green without the filter it exists for proves the filter nothing. This is
# the shape that must never become a CI term again, and the test below is what
# says so out loud.
SPLIT_INDEPENDENT: dict[str, str] = {"Vereinbarung": "14-pacht-mit-anhang.pdf"}

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
    # Parteienverkehr stands in the Austrian notice. Measured as case 47 since
    # the audit of phase 8: one token "verkehr", entry of the list, so the claim
    # about it below stands on a line of the TSV like every other one.
    "Verkehr": "16-oesterreich-mitteilung.pdf",
    # Ersatzabgabe stands in the Swiss permit, Verwaltungsabgabe in the Austrian
    # notice. Measured as finding 1 of the phase measurement.
    "Abgabe": "15-schweiz-baubewilligung.pdf",
}

# What tesseract really reads off the headline of 19-uebermittlung.tif, measured
# in the shipping image on 2026-09-01 and written down in docs/ocr.md: the two
# dots over the capital letter are gone. The word the generator draws is next to
# it. This pair is why "Protokoll" is not among the three terms above.
#
# Both spellings are cases of compound_cases_de.txt, the transcribed one since
# the audit of phase 8 as case 48. That matters more than it looks: the decision
# not to build "Protokoll" as a language case rests on the transcription staying
# one token, and until it was measured that rested on the fixture alone. Against
# the real Debian list it is the single token "ubermittlungsprotokoll", so the
# decision now stands on a measurement.
HEADLINE_AS_DRAWN = "Übermittlungsprotokoll"
HEADLINE_AS_READ = "Ubermittlungsprotokoll"


@pytest.fixture(scope="module")
def german() -> TextAnalyzer:
    """One German analyser for the whole module; building it is not free."""
    return german_analyzer(FIXTURE.read_text(encoding="utf-8").split())


@pytest.fixture(scope="module")
def splitterless() -> TextAnalyzer:
    """The shipped German chain minus Filter.split_compound, filter for filter.

    Everything else stays, in the shipped order: lowercase, the linking elements
    as custom stopwords, the built in German stopwords, the length limit and the
    Snowball stemmer. MAX_TOKEN_CHARS and FUGEN are imported rather than copied,
    so the control cannot drift away from the chain it is a control for. The same
    construction stands in test_index_open.py, where it carries the index level
    proof for one term; here it carries the corpus level proof for all of them.
    """
    return (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.custom_stopword(list(FUGEN)))
        .filter(Filter.stopword("german"))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer("german"))
        .build()
    )


@pytest.fixture(scope="module")
def searchable(corpus_generator: ModuleType) -> dict[str, str]:
    """Everything a search could find in each corpus file, pixels included.

    Taken from the generator rather than from the built files, because the text
    of a scanned page exists as pixels and a reader of the bytes would find
    nothing there. The generator is the ground truth of that prose.

    The generator arrives through the session fixture of conftest.py. Loading it
    builds all thirty nine corpus files, so a second load in this module would
    cost another six seconds for nothing.
    """
    return {name: corpus_generator._searchable_text(name, payload) for name, payload in corpus_generator.FILES.items()}


@pytest.fixture(scope="module")
def tokens_per_file(german: TextAnalyzer, searchable: dict[str, str]) -> dict[str, set[str]]:
    """The token set of every corpus file, which is what the index really holds."""
    return {name: set(german.analyze(text)) for name, text in searchable.items()}


@pytest.fixture(scope="module")
def tokens_per_file_unsplit(splitterless: TextAnalyzer, searchable: dict[str, str]) -> dict[str, set[str]]:
    """The same token sets, produced by the chain without the splitter."""
    return {name: set(splitterless.analyze(text)) for name, text in searchable.items()}


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


@pytest.mark.parametrize(("term", "owner"), sorted(CI_TERMS.items()))
def test_a_ci_term_finds_nothing_once_the_splitter_is_taken_out(
    splitterless: TextAnalyzer, tokens_per_file_unsplit: dict[str, set[str]], term: str, owner: str
) -> None:
    # The gate the audit of phase 8 added, and the only one of the three that
    # asks what the language case is actually for. A term that still finds its
    # file without Filter.split_compound is carried by something else, most
    # likely by the word standing on its own somewhere in the same document, and
    # the CI case built on it would stay green if the filter were deleted
    # tomorrow. Measured against the real Debian list on 2026-09-08, all three
    # terms of CI_TERMS come back empty here and the two older compound cases
    # (Genehmigung, Frist) do as well.
    carriers = _carriers(splitterless, tokens_per_file_unsplit, term)

    assert carriers == [], (
        f"{term!r} still finds {carriers} without Filter.split_compound, "
        f"so the language case for {owner} does not prove the decomposition"
    )


@pytest.mark.parametrize(("term", "owner"), sorted(SPLIT_INDEPENDENT.items()))
def test_a_split_independent_term_is_kept_out_of_the_ci_set(
    german: TextAnalyzer,
    splitterless: TextAnalyzer,
    tokens_per_file: dict[str, set[str]],
    tokens_per_file_unsplit: dict[str, set[str]],
    term: str,
    owner: str,
) -> None:
    # The positive control of the gate above. Without a term that survives the
    # removal of the splitter, a gate that always reported "nothing found" would
    # look exactly like a gate that works, and it would report nothing found for
    # a chain that is simply broken. This term finds its file both ways, which is
    # precisely why it is no language case any more.
    assert _carriers(german, tokens_per_file, term) == [owner]
    assert _carriers(splitterless, tokens_per_file_unsplit, term) == [owner], (
        f"{term!r} was expected to stand on its own in {owner} and to be findable without the splitter"
    )
    assert term not in CI_TERMS


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


def test_every_word_this_module_claims_about_was_measured() -> None:
    # The guard over the guards, mirrored from
    # test_analyzer.py::test_every_asserted_word_stands_in_the_measured_case_list.
    # Everything above is a statement about a word, every statement travels
    # straight into a CI step, and a statement about a word that was never run
    # against the real Debian list is a statement about the fixture. Without this
    # test a fourth entry could walk into CI_TERMS, be green here and turn main
    # red, which is exactly what the whole module is arranged against.
    measured = set(CASES.read_text(encoding="utf-8").split())
    asserted = [
        *CI_TERMS,
        *SPLIT_INDEPENDENT,
        AMBIGUOUS,
        *LETTER_TRAPS,
        HEADLINE_AS_DRAWN,
        HEADLINE_AS_READ,
    ]

    missing = sorted(word for word in asserted if word not in measured)

    assert missing == [], (
        f"asserted here but never measured, add to {CASES.name} and rerun scripts/dev/measure_compounds.sh: {missing}"
    )


def test_every_ci_term_is_carried_by_the_uniqueness_check_of_the_generator(corpus_generator: ModuleType) -> None:
    # The generator has its own uniqueness check and it runs on every build of
    # the corpus. A term that the workflow asserts on but that check does not
    # know is a term that can quietly become ambiguous with the next corpus file.
    missing = sorted(term for term in CI_TERMS if term not in corpus_generator.UNIQUE_TERMS)

    assert missing == [], f"add to UNIQUE_TERMS in {BUILD_CORPUS.name}: {missing}"
    for term, owner in CI_TERMS.items():
        assert corpus_generator.UNIQUE_TERMS[term] == owner
