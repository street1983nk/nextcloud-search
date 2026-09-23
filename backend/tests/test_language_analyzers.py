"""The Snowball chains of the four new languages, asserted term by term.

These cases assert WHAT the chain produces, not THAT something came back. The
whole value of the file sits in that difference: a test that only checks "a
token appeared" stays green while the fold has wandered behind the stemmer and
every user who does not type accents has stopped finding anything.

The fold position is measured and not reasoned about. Measured on 2026-09-23
against tantivy tag 0.26.2: folding in front of the stop word filter keeps 467
of 573 ordered surface form pairs on a shared term, folding behind the stemmer
keeps 463, and only the front position keeps the accented and the flat spelling
of a stop word out of the index in both spellings.

The syntax tree reader comes from the sibling module and is not copied here.
``from test_analyzer import ANALYZER_SOURCE, filter_chain`` works because
backend/tests carries no __init__.py and pytest imports in prepend mode. A
second reader would be a second gate, and a gate written on the day of the
change agrees with that change by construction, which is the one thing a guard
must not do.

Since plan 17-06 the measurement itself is the acceptance. The lower half of
this file holds the form family score of every language against the number the
run of 2026-09-23 wrote into
``docs/measurements/2026-09-analyseketten/rohdaten/kennzahlen.txt``, and it holds
the measured losses in both directions: a pair that starts to fall apart is red,
and a pair that stops falling apart is just as red, because it means the chain
moved and a moved chain moves every term of every index written with it.

The fixture reader and the metric are not rebuilt here. Both are loaded out of
``scripts/dev/chain_probe.py``, the tool that produced the report, because a
second reader is a second format and a second metric is a second number.

The same plan closed the one hole plan 17-03 had to leave open. The density gate
runs all 891 built in Snowball entries of the four languages through the shipped
chain, each of them twice, accented and folded, and demands the empty token list
every time. Not a sample: a stop word in the index is a silent quality loss with
no error message anywhere, so the claim has to cover the whole list.

The merged case table underneath it is the acceptance of LEX-01, twelve rows out
of the fifteen of the report; rows 10 to 12 are "all accented stop words of es,
pt and it" and the density gate is exactly that claim, only larger.

Accents appear only inside string literals. They are data here, the words the
product has to handle; the identifiers stay ASCII as the project rules require.
"""

import importlib.util
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import NamedTuple

import pytest
from tantivy import Filter, TextAnalyzer, TextAnalyzerBuilder, Tokenizer

from findling.config import LANGUAGE_ALLOWLIST, SNOWBALL_NAME
from findling.index.analyzer import ANALYZER_VERSION, MAX_TOKEN_CHARS, english_analyzer, snowball_analyzer
from findling.index.stopwords import FOLDED_STOPWORDS, folded_stopwords_hash
from test_analyzer import ANALYZER_SOURCE, filter_chain

# The shipped Snowball order. Every one of the six positions carries a measured
# reason, and the test below names them one by one:
# lowercase first, because everything after it compares strings exactly, and
# both stop word filters are exact comparisons against lowercase lists.
# ascii_fold second, in front of the stop word list and thereby in front of the
# stemmer: measured 467 of 573 ordered pairs against 463 for a late fold.
# stopword(lang) third, the built in Snowball list of the language.
# custom_stopword(folded) directly behind it, because the fold has just made the
# built in list miss its own accented entries: 77 es, 10 it, 30 pt would leak.
# remove_long(48) fifth, the same limit as every other chain; nothing splits
# here, so there is no splitter it would have to stand behind.
# stemmer(lang) last, as in every chain of this module.
EXPECTED_SNOWBALL_CHAIN = [
    "lowercase",
    "ascii_fold",
    "stopword",
    "custom_stopword",
    "remove_long",
    "stemmer",
]

# The digest of the shipped supplement, produced by
# scripts/dev/stopword_supplement.py against tantivy tag 0.26.2 on 2026-09-23.
#
# It stands here and deliberately not in expected_versions() of
# findling.index.open. There it would be a sixth version mark, a sixth mark
# exists on no installation in the field, and Store.version_mismatch reads a
# missing mark as a difference: every stock installation would reindex, measured
# at 19 h 20 min, for a constant that changes no tokenisation of any index
# already written.
#
# When this test goes red: run scripts/dev/stopword_supplement.py again, write
# the difference into the measurement report, THEN ANSWER THE MARK QUESTION
# BELOW, and only then pull this value after it. Never the other way round.
#
# The mark question, and it is the step the procedure was missing until the
# audit of 2026-09-23 (M-17-04): does the difference touch a supplement that a
# REGISTERED chain reads. Today exactly one does, the English one through
# english_analyzer(), and it is empty, which is why nothing here is a version
# mark. A tag that gives the English list one accented entry moves the
# tokenisation of every index in the field while this digest is the only thing
# that changes, so pulling the constant without raising ANALYZER_VERSION ships a
# drifted chain onto a stock installation with no mark and no reindex. Phase 18
# registers es, it, nl and pt, and from then on the question covers their
# supplements too. The answer is enforced one assertion further down, in
# test_a_non_empty_english_supplement_would_move_the_shipped_chain.
FOLDED_SUPPLEMENT_SHA256 = "d056d4597f989c7e03113c529c92cef980254f72c4d4e5deace4588ea033311a"

# The measured sizes per language, from the same run.
EXPECTED_SUPPLEMENT_SIZES = {"english": 0, "spanish": 77, "italian": 10, "dutch": 0, "portuguese": 30}

# The vocabulary the no-op proof runs. English stop words, ordinary words, a
# word longer than MAX_TOKEN_CHARS, an accented one and a digit group, because a
# filter that is a no-op for nouns and not for numbers is not a no-op.
NO_OP_WORDS = (
    "the",
    "and",
    "with",
    "documents",
    "running",
    "invoices",
    "Kuendigung",
    "café",
    "Straße",
    "2026",
    "report2026",
    "a" * (MAX_TOKEN_CHARS + 5),
    "x",
)


def _folder():
    """Return an analyser that folds one whole word and does nothing else."""
    return TextAnalyzerBuilder(Tokenizer.raw()).filter(Filter.ascii_fold()).build()


def _builtin_only(language: str):
    """Return lowercase plus the BUILT IN stop word list, and nothing after it.

    The supplement is missing on purpose. A word this chain still turns into a
    token is a word the built in list does not carry, which is exactly what
    makes a supplement entry necessary rather than decorative.
    """
    return TextAnalyzerBuilder(Tokenizer.simple()).filter(Filter.lowercase()).filter(Filter.stopword(language)).build()


def test_the_spanish_chain_puts_both_spellings_on_one_term() -> None:
    # The case the whole fold position exists for: a user who does not type
    # accents and a scan that lost them have to reach the same document.
    chain = snowball_analyzer("spanish")

    assert chain.analyze("información") == chain.analyze("informacion")
    assert chain.analyze("informacion") != []


def test_an_italian_stop_word_is_dropped_in_both_spellings() -> None:
    # "perche" is in the built in list with its accent only. Without the
    # supplement the flat spelling survives the fold and lands in the index.
    chain = snowball_analyzer("italian")

    assert chain.analyze("perché") == []
    assert chain.analyze("perche") == []


def test_the_dutch_accent_case_leaves_no_rubbish_token() -> None:
    # Dutch has no accented entry in its built in list, so its supplement is
    # empty, and the built in entry "een" has to catch the folded form on its own.
    chain = snowball_analyzer("dutch")

    assert chain.analyze("één") == []
    assert chain.analyze("een") == []


def test_the_factory_refuses_a_language_outside_the_allowlist() -> None:
    # The refusal names the language, because a chain factory that answers a
    # typo in an environment variable with a bare KeyError or with a panic out
    # of the Rust side leaves the reader with nothing to act on.
    with pytest.raises(ValueError, match="klingon"):
        snowball_analyzer("klingon")


def test_the_factory_refuses_an_allowlisted_language_without_a_supplement() -> None:
    # French is the loud case of the silent one: allowlisted, accented, and
    # without a measured supplement. Built with an empty supplement it puts the
    # accented stop words of French into the index as ordinary terms and nothing
    # goes red anywhere, so the missing supplement has to be the refusal.
    assert "french" in LANGUAGE_ALLOWLIST
    assert "french" not in FOLDED_STOPWORDS

    with pytest.raises(ValueError, match="french"):
        snowball_analyzer("french")


def test_the_factory_reads_the_language_name_regardless_of_its_spelling() -> None:
    # tantivy takes the name in any case, the mapping and the allowlist compare
    # exactly and are lowercase. Before the factory lowered the name itself, the
    # capitalised spelling built a working chain that let all 77 Spanish
    # supplement entries through, and no test saw it because every test wrote
    # lowercase.
    upper = snowball_analyzer("Spanish")
    lower = snowball_analyzer("spanish")

    for word in ("estáis", "estais", "información", "informacion", "documento"):
        assert upper.analyze(word) == lower.analyze(word), word
    assert upper.analyze("estais") == []


def test_every_language_a_field_code_maps_to_carries_a_supplement() -> None:
    # The mapping SNOWBALL_NAME is what phase 18 turns a field code into. A name
    # in it without a supplement is a ValueError at the moment a chain is asked
    # for, so the gate has to stand here and not at the first index that opens.
    #
    # German is out of it and only German: it has a factory of its own, with the
    # compound splitter and without a fold, so it never reaches this one.
    reachable = set(SNOWBALL_NAME.values()) - {"german"}

    assert reachable == set(FOLDED_STOPWORDS), "the factory serves exactly the languages a field code maps to"

    missing = sorted(name for name in reachable if name not in FOLDED_STOPWORDS)

    assert missing == [], (
        f"{missing} can be reached through SNOWBALL_NAME and has no folded supplement; "
        "derive one with scripts/dev/stopword_supplement.py before phase 18 asks for the chain"
    )


def test_the_english_chain_did_not_move_when_it_joined_the_factory() -> None:
    # The chain as it stood before the factory existed, built by hand here so
    # that the comparison is against the old shape and not against itself.
    before = (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())
        .filter(Filter.stopword("english"))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer("english"))
        .build()
    )
    now = english_analyzer()

    for word in NO_OP_WORDS:
        assert now.analyze(word) == before.analyze(word), word


def test_the_analyzer_version_did_not_move() -> None:
    # Four chains were added and none of them was registered anywhere, so no
    # index that exists today tokenises differently than it did yesterday. The
    # mark rises in phase 18, together with the schema.
    assert ANALYZER_VERSION == 1


def test_the_snowball_chain_stands_in_the_measured_order() -> None:
    # Read out of the source of index/analyzer.py, not out of a built analyser:
    # a built analyser tells nobody in which order it was built.
    chain = filter_chain(ANALYZER_SOURCE.read_text(encoding="utf-8"), "snowball_analyzer")

    assert chain == EXPECTED_SNOWBALL_CHAIN


def test_the_guard_tells_two_chains_apart() -> None:
    # Without this, a guard that always returned the same list would look green
    # for the Snowball chain and prove nothing at all.
    chain = filter_chain(ANALYZER_SOURCE.read_text(encoding="utf-8"), "german_analyzer")

    assert chain != EXPECTED_SNOWBALL_CHAIN
    assert "split_compound" in chain


def test_the_guard_sees_the_fold_pushed_behind_the_stemmer() -> None:
    # The anti pattern with a name. A token table alone would report this as
    # "the accented spelling suddenly has its own term" and leave the reader to
    # work out why; the guard reports the filter that moved.
    source = (
        "def snowball_analyzer(language):\n"
        "    return (\n"
        "        TextAnalyzerBuilder(Tokenizer.simple())\n"
        "        .filter(Filter.lowercase())\n"
        "        .filter(Filter.stopword(name))\n"
        "        .filter(Filter.custom_stopword(list(folded)))\n"
        "        .filter(Filter.remove_long(MAX_TOKEN_CHARS))\n"
        "        .filter(Filter.stemmer(name))\n"
        "        .filter(Filter.ascii_fold())\n"
        "        .build()\n"
        "    )\n"
    )

    chain = filter_chain(source, "snowball_analyzer")

    assert chain.index("ascii_fold") > chain.index("stemmer")
    assert chain != EXPECTED_SNOWBALL_CHAIN


def test_a_comment_that_names_a_filter_does_not_enter_the_chain() -> None:
    source = (
        "def snowball_analyzer(language):\n"
        "    # ascii_fold used to stand here, see Filter.ascii_fold below.\n"
        '    """And Filter.custom_stopword was once documented in this line."""\n'
        "    return (\n"
        "        TextAnalyzerBuilder(Tokenizer.simple())\n"
        "        .filter(Filter.lowercase())\n"
        "        .build()\n"
        "    )\n"
    )

    chain = filter_chain(source, "snowball_analyzer")

    assert chain == ["lowercase"]


def test_an_empty_custom_stopword_filter_is_a_no_op() -> None:
    # The condition under which english_analyzer was allowed into the shared
    # factory at all. Two chains, identical except for the empty filter, and the
    # claim is token list equals token list, not equal length and not "both non
    # empty".
    without = (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())
        .filter(Filter.stopword("english"))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer("english"))
        .build()
    )
    with_empty = (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())
        .filter(Filter.stopword("english"))
        .filter(Filter.custom_stopword([]))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer("english"))
        .build()
    )
    shipped = english_analyzer()

    assert len(NO_OP_WORDS) >= 13
    for word in NO_OP_WORDS:
        assert with_empty.analyze(word) == without.analyze(word), word
        assert shipped.analyze(word) == without.analyze(word), word


def test_the_supplement_has_the_measured_sizes_and_digest() -> None:
    sizes = {language: len(entries) for language, entries in FOLDED_STOPWORDS.items()}

    assert sizes == EXPECTED_SUPPLEMENT_SIZES

    flat = [word for language in sorted(FOLDED_STOPWORDS) for word in FOLDED_STOPWORDS[language]]

    assert len(flat) == sum(EXPECTED_SUPPLEMENT_SIZES.values())
    assert folded_stopwords_hash(flat) == FOLDED_SUPPLEMENT_SHA256, (
        "the supplement drifted away from the measured run; rerun "
        "scripts/dev/stopword_supplement.py, record the difference, ASK WHETHER THE DIFFERENCE TOUCHES A "
        "REGISTERED CHAIN AND THEREFORE ANALYZER_VERSION (see the comment at FOLDED_SUPPLEMENT_SHA256), "
        "and only then pull this constant after it"
    )


def test_a_non_empty_english_supplement_would_move_the_shipped_chain() -> None:
    # The one supplement a registered tokenizer reads today, and the reason the
    # nachzieh procedure above has to ask about ANALYZER_VERSION at all.
    # english_analyzer() is registered in index/open.py as the tokenizer "en", so
    # its chain writes the terms of every index in the field. An empty custom
    # stop word filter is a measured no-op, which is what keeps ANALYZER_VERSION
    # at 1 today; one accented entry in this tuple ends the no-op and moves the
    # tokenisation of every existing index, while the only constant that changes
    # is the digest above, which is deliberately not a version mark.
    #
    # When this goes red, the supplement is not simply pulled after: either the
    # entry is refused, or ANALYZER_VERSION rises by one with it.
    assert FOLDED_STOPWORDS["english"] == (), (
        "english_analyzer() is registered as the tokenizer 'en': a non empty English supplement moves the "
        "tokenisation of every index in the field and needs ANALYZER_VERSION + 1, not a pulled digest"
    )


def test_every_supplement_entry_is_needed_and_is_its_own_folded_form() -> None:
    # Two directions, and a supplement entry has to survive both. An entry the
    # built in list already catches would be ballast that only grows the digest;
    # an entry that is not its own folded form can never be reached at all,
    # because the fold runs one filter before the supplement sees it.
    folder = _folder()

    for language, entries in FOLDED_STOPWORDS.items():
        builtin = _builtin_only(language)
        for entry in entries:
            assert builtin.analyze(entry) != [], (
                f"{entry} is already in the built in {language} list and does not belong in the supplement"
            )
            assert folder.analyze(entry) == [entry], (
                f"{entry} is not its own folded form, so the {language} chain can never reach it"
            )
        assert len(set(entries)) == len(entries), f"the {language} supplement carries a duplicate"


# ---------------------------------------------------------------------------
# The measured acceptance. Everything below turns the run of 2026-09-23 into a
# gate: the form family score per language, and the known losses in both
# directions. Plan 17-06.
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# The two letter codes the fixtures and the phase documents speak. The Snowball
# names they belong to are deliberately NOT spelled out here; they come from
# findling.config.SNOWBALL_NAME, the one place in the tree where a field code
# turns into a tantivy language name. A second mapping inside a test would be a
# second truth, and on the day somebody corrects one of the two this gate would
# still be green while the product speaks a different language than the test.
CODES = ("es", "it", "nl", "pt")

CASES = {code: FIXTURES / f"chain_cases_{code}.txt" for code in CODES}
LOSSES = {code: FIXTURES / f"chain_known_losses_{code}.txt" for code in CODES}

# The measurement probe. It is a script and not a package, so it is loaded by
# path, the same way conftest.py loads scripts/dev/build_corpus.py.
CHAIN_PROBE = Path(__file__).resolve().parents[2] / "scripts" / "dev" / "chain_probe.py"
CHAIN_PROBE_MODULE = "chain_probe_under_test"

# The command that produced every number below, named in every failure message
# so that nobody has to look for it while a gate is red.
MEASURE_CHAINS = "scripts/dev/measure_chains.sh"

# Hits and possible ordered pairs per language, read out of
# docs/measurements/2026-09-analyseketten/rohdaten/kennzahlen.txt, run of
# 2026-09-23 against tantivy tag 0.26.2: es_Aplus_hits 174 of es_pairs 208,
# it 56 of 56, nl 57 of 81, pt 180 of 228, together 467 of 573.
#
# Equality and not "at least". A chain that suddenly scores higher has moved
# exactly as far as one that scores lower, and a moved chain moves every term of
# every index written with it. When one of these numbers falls, run
# scripts/dev/measure_chains.sh first, write the finding into the measurement
# report, and only then pull the constant here after it. Never the other way
# round: a number corrected in this file first is a gate agreeing with the
# change it was built to catch.
EXPECTED_FAMILY_SCORES = {"es": (174, 208), "it": (56, 56), "nl": (57, 81), "pt": (180, 228)}


def _load_chain_probe() -> ModuleType:
    """Return ``scripts/dev/chain_probe.py`` as a module, loaded by path.

    The fixture format has exactly one reader in this tree and it lives in the
    probe, so this gate loads :func:`read_families` from there instead of
    rebuilding it. A second reader would be a second format: measurement and
    acceptance would then agree only for as long as nobody edits one of the two,
    and the first divergence would show up as a green gate over a moved chain.
    The metric comes from the same place and for the same reason.

    The direction is the only one available. ``scripts/`` is no package
    (docs/testing.md), so a test may load this file and the product may never
    load it.
    """
    specification = importlib.util.spec_from_file_location(CHAIN_PROBE_MODULE, CHAIN_PROBE)
    if specification is None or specification.loader is None:  # pragma: no cover
        raise RuntimeError(f"the measurement probe is not at {CHAIN_PROBE}, so nothing below measures anything")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def _pairs_apart(terms: dict[str, list[str]], forms: Sequence[str]) -> list[tuple[str, str]]:
    """Return the unordered pairs of one family that share no term.

    ``terms`` is the third return value of the probe's ``family_score``, so the
    tokens counted by the score and the tokens named here are the same tokens.
    Unordered, because sharing a term is symmetric and a loss printed twice is
    still one loss; the order inside a pair is the order of the fixture line,
    which is how ``chain_known_losses_<code>.txt`` spells it.
    """
    apart: list[tuple[str, str]] = []
    for index, left in enumerate(forms):
        for right in forms[index + 1 :]:
            if not (terms[left] and terms[right] and set(terms[left]) & set(terms[right])):
                apart.append((left, right))
    return apart


@pytest.fixture(scope="module")
def probe() -> ModuleType:
    """The measurement probe, loaded once for the whole module."""
    return _load_chain_probe()


@pytest.fixture(scope="module")
def families(probe: ModuleType) -> dict[str, list[list[str]]]:
    """The form families of all four fixtures, read once through the probe."""
    return {code: probe.read_families(CASES[code]) for code in CODES}


@pytest.fixture(scope="module")
def known_losses(probe: ModuleType) -> dict[str, set[tuple[str, str]]]:
    """The measured losses per language, read with the same reader.

    A loss file is a family file whose lines happen to carry exactly two forms,
    so it needs no reader of its own; the shape is asserted rather than assumed.
    """
    out: dict[str, set[tuple[str, str]]] = {}
    for code in CODES:
        pairs: set[tuple[str, str]] = set()
        for forms in probe.read_families(LOSSES[code]):
            assert len(forms) == 2, f"{LOSSES[code].name} carries a line that is not a form pair: {forms}"
            pairs.add((forms[0], forms[1]))
        out[code] = pairs
    return out


@pytest.fixture(scope="module")
def chains() -> dict[str, TextAnalyzer]:
    """One shipped analyser per language, built once for the whole module."""
    return {code: snowball_analyzer(SNOWBALL_NAME[code]) for code in CODES}


@pytest.mark.parametrize("code", CODES)
def test_the_shipped_chain_reaches_the_measured_family_score(
    code: str, families: dict[str, list[list[str]]], chains: dict[str, TextAnalyzer], probe: ModuleType
) -> None:
    hits = 0
    total = 0
    for forms in families[code]:
        family_hits, family_total, _ = probe.family_score(chains[code], forms)
        hits += family_hits
        total += family_total

    assert (hits, total) == EXPECTED_FAMILY_SCORES[code], (
        f"{code} scores {hits} of {total} ordered pairs, measured was {EXPECTED_FAMILY_SCORES[code]}; "
        f"a higher number is as much a finding as a lower one, so run {MEASURE_CHAINS}, record the "
        "difference in docs/measurements/2026-09-analyseketten/ and pull this constant after it"
    )


@pytest.mark.parametrize("code", CODES)
def test_the_losses_are_exactly_the_measured_ones(
    code: str,
    families: dict[str, list[list[str]]],
    chains: dict[str, TextAnalyzer],
    known_losses: dict[str, set[tuple[str, str]]],
    probe: ModuleType,
) -> None:
    measured: set[tuple[str, str]] = set()
    for forms in families[code]:
        _, _, terms = probe.family_score(chains[code], forms)
        measured.update(_pairs_apart(terms, forms))

    known = known_losses[code]
    appeared = sorted(f"{left} and {right}" for left, right in measured - known)
    vanished = sorted(f"{left} and {right}" for left, right in known - measured)

    assert appeared == [], (
        f"new losses that nobody measured: {'; '.join(appeared)}. Run {MEASURE_CHAINS}, write the finding "
        f"into the measurement report, then carry it into {LOSSES[code].name}"
    )
    assert vanished == [], (
        f"losses that disappeared, which means the chain moved: {'; '.join(vanished)}. A chain that moved "
        f"moves every term of every index, so run {MEASURE_CHAINS} before touching {LOSSES[code].name}"
    )


# ---------------------------------------------------------------------------
# The stop word density gate, run offline against the built in lists of the
# pinned tantivy tag, and the merged test case table of the report. Plan 17-06.
# ---------------------------------------------------------------------------

# The built in Snowball lists as they stand in
# quickwit-oss/tantivy tag 0.26.2, src/tokenizer/stop_word_filter/stopwords.rs,
# generated into a fixture so that this gate needs no Rust checkout and no
# network. Lines are "language<TAB>word".
BUILTIN_STOPWORDS = FIXTURES / "snowball_stopwords_0_26_2.txt"

# The word counts of that tag, from the head comment of the fixture. They are a
# tag mark and not a taste: a fixture with other counts belongs to another
# tantivy than the one this build pins, and a density gate run against the wrong
# list is a gate that measures nothing.
EXPECTED_BUILTIN_SIZES = {"spanish": 308, "italian": 279, "portuguese": 203, "dutch": 101}
EXPECTED_BUILTIN_TOTAL = 891

# The three verdicts a row of the merged table can carry.
SAME = "same"
BOTH_EMPTY = "both_empty"
APART = "apart"


class MergedCase(NamedTuple):
    """One row of the merged test case table.

    ``groups`` holds the spellings that have to behave alike; a row can carry
    more than one group, because rows 14 and 15 of the report name three and two
    word pairs in one line. ``terms`` is filled for ``apart`` rows only and
    holds the measured token list of each form, in the order of the group.
    """

    number: int
    code: str
    expectation: str
    groups: tuple[tuple[str, ...], ...]
    terms: tuple[tuple[str, ...], ...] = ()


# Section 5 of docs/measurements/2026-09-analyseketten/README.md, run of
# 2026-09-23, with the source of each row as a comment. Twelve rows and not
# fifteen: rows 10, 11 and 12 of the report are "the accented stop words of es,
# pt and it, all of them", and all of them is exactly what the density gate
# above runs over the 891 entries of the four built in lists. Repeating three of
# them here as hand picked words would be a smaller claim wearing the same name.
MERGED_CASES = (
    # 1, STACK and LEX-01. The case the fold position exists for.
    MergedCase(1, "es", SAME, (("información", "informacion"),)),
    # 2, PITFALLS and LEX-01. Documented loss, see the apart test below.
    MergedCase(2, "es", APART, (("información", "informaciones"),), (("informacion",), ("inform",))),
    # 3, STACK and LEX-01.
    MergedCase(3, "pt", SAME, (("informação", "informacao"),)),
    # 4, PITFALLS and LEX-01. Documented loss, and it falls in every chain.
    MergedCase(4, "pt", APART, (("informação", "informações"),), (("informaca",), ("informaco",))),
    # 5, STACK.
    MergedCase(5, "pt", SAME, (("informações", "informacoes"),)),
    # 6, PITFALLS and LEX-01. The deliberately bought recall: the accent carries
    # the meaning here and the fold spends it, see docs/language-analyzers.md.
    MergedCase(6, "es", SAME, (("año", "ano"),)),
    # 7, FEATURES, PITFALLS and LEX-01. Built in entry accented, supplement flat.
    MergedCase(7, "it", BOTH_EMPTY, (("perché", "perche"),)),
    # 8, PITFALLS. Same shape as row 7 and the word the researches argued over.
    MergedCase(8, "it", BOTH_EMPTY, (("più", "piu"),)),
    # 9, FEATURES and LEX-01. The stress accent that folds onto a built in entry;
    # the point of the row is that nothing rubbish is left behind either.
    MergedCase(9, "nl", BOTH_EMPTY, (("één", "een"),)),
    # 13, new from this measurement. The report measured "qual" for both, the
    # phase research had guessed "qualit"; the measured value is the one here.
    MergedCase(13, "it", SAME, (("qualità", "qualita"),)),
    # 14, STACK. Three pairs in one row of the report.
    MergedCase(14, "it", SAME, (("città", "citta"), ("società", "societa"), ("università", "universita"))),
    # 15, FEATURES. Two pairs in one row of the report.
    MergedCase(15, "nl", SAME, (("coördinatie", "coordinatie"), ("financiën", "financien"))),
)

EXPECTED_CASE_NUMBERS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 15)


def _rows(expectation: str) -> list[MergedCase]:
    """The rows of the merged table that carry one verdict."""
    return [case for case in MERGED_CASES if case.expectation == expectation]


def _row_ids(cases: list[MergedCase]) -> list[str]:
    """Readable test ids: the row number of the report and its language."""
    return [f"row{case.number}-{case.code}" for case in cases]


@pytest.fixture(scope="module")
def builtin_stopwords(probe: ModuleType) -> dict[str, list[str]]:
    """The built in Snowball lists of the pinned tag, read once.

    Read through the probe for the same reason the families are: the fixture
    format has one reader in this tree, and that reader produced the report.
    """
    return probe.read_builtin(BUILTIN_STOPWORDS)


@pytest.fixture(scope="module")
def folder() -> TextAnalyzer:
    """One folder for the whole module, built from tantivy's own filter.

    The fold of this gate runs through ``Filter.ascii_fold()`` and never through
    a hand written normalisation. A rebuilt fold would check a different chain
    than the one the product ships, which is precisely the failure the gate
    exists to catch.
    """
    return _folder()


def test_the_built_in_lists_are_the_ones_of_the_pinned_tag(builtin_stopwords: dict[str, list[str]]) -> None:
    sizes = {language: len(words) for language, words in builtin_stopwords.items()}

    assert sizes == EXPECTED_BUILTIN_SIZES, (
        f"{BUILTIN_STOPWORDS.name} carries {sizes} instead of {EXPECTED_BUILTIN_SIZES}, so it no longer belongs "
        "to tantivy tag 0.26.2; regenerate it from that tag rather than editing it, because a density gate over "
        "the wrong list proves nothing about the list the chains really filter against"
    )
    assert sum(sizes.values()) == EXPECTED_BUILTIN_TOTAL


@pytest.mark.parametrize("code", CODES)
def test_no_built_in_stop_word_reaches_the_index_in_either_spelling(
    code: str,
    chains: dict[str, TextAnalyzer],
    builtin_stopwords: dict[str, list[str]],
    folder: TextAnalyzer,
) -> None:
    # The promise plan 17-03 could not keep yet, kept here: not a sample but all
    # 891 built in entries of the four languages, each one twice. Both spellings,
    # because a chain can be tight in one and open in the other: folding in front
    # of the built in list lets the accented entry through, folding behind it
    # lets the flat one through, and only the shipped order closes both.
    language = SNOWBALL_NAME[code]
    chain = chains[code]
    leaks: list[str] = []

    for word in builtin_stopwords[language]:
        tokens = chain.analyze(word)
        if tokens:
            leaks.append(f"{language}: {word} accented produces {tokens}")
        folded = folder.analyze(word)
        flat = folded[0] if folded else ""
        if flat and flat != word:
            tokens = chain.analyze(flat)
            if tokens:
                leaks.append(f"{language}: {flat} flat, folded from {word}, produces {tokens}")

    assert leaks == [], (
        f"{len(leaks)} stop words of {language} land in the index as ordinary terms: {'; '.join(leaks)}. "
        f"Run {MEASURE_CHAINS} and check the supplement with scripts/dev/stopword_supplement.py"
    )


def test_the_merged_table_carries_the_rows_of_the_report() -> None:
    # Twelve rows, and the numbers are the ones the report prints, so that a row
    # cannot quietly go missing while the count still looks right.
    assert len(MERGED_CASES) == len(EXPECTED_CASE_NUMBERS)
    assert tuple(case.number for case in MERGED_CASES) == EXPECTED_CASE_NUMBERS


@pytest.mark.parametrize("case", _rows(SAME), ids=_row_ids(_rows(SAME)))
def test_the_spellings_of_a_row_land_on_one_term(case: MergedCase, chains: dict[str, TextAnalyzer]) -> None:
    chain = chains[case.code]

    for group in case.groups:
        tokens = [chain.analyze(form) for form in group]
        assert tokens[0] != [], f"row {case.number}: {group[0]} produces no term at all"
        for form, produced in zip(group, tokens, strict=True):
            assert produced == tokens[0], (
                f"row {case.number} of the merged table: {form} produces {produced}, {group[0]} produces "
                f"{tokens[0]}, so the two spellings no longer meet"
            )


@pytest.mark.parametrize("case", _rows(BOTH_EMPTY), ids=_row_ids(_rows(BOTH_EMPTY)))
def test_a_stop_word_row_leaves_no_token_in_either_spelling(case: MergedCase, chains: dict[str, TextAnalyzer]) -> None:
    chain = chains[case.code]

    for group in case.groups:
        for form in group:
            tokens = chain.analyze(form)
            assert tokens == [], (
                f"row {case.number} of the merged table: {form} produces {tokens} instead of nothing. A term "
                "no question can reach is worse than a missing one, because it only grows the index"
            )


@pytest.mark.parametrize("case", _rows(APART), ids=_row_ids(_rows(APART)))
def test_a_documented_loss_produces_exactly_the_measured_terms(
    case: MergedCase, chains: dict[str, TextAnalyzer]
) -> None:
    # The two rows of the table that are red, asserted rather than skipped.
    #
    # They are not repairable without making another row red. The Spanish
    # Snowball algorithm carries the accented ending in its suffix list and the
    # plural ending without the accent, so the fold that puts "información" and
    # "informacion" on one term is the same fold that takes "informaciones"
    # away from both; Portuguese splits "informação" from "informações" in every
    # one of the seven measured chains. Both stand as known limits in
    # docs/language-analyzers.md and as lines in the loss fixtures.
    #
    # Deliberately not marked as an expected failure. Such a marker stays green
    # when the result changes, and a changed result here means the chain moved,
    # which is the one event this file exists to report. The word itself is kept
    # out of this module so that a search for the marker finds none.
    chain = chains[case.code]
    left, right = case.groups[0]
    left_terms, right_terms = case.terms

    assert chain.analyze(left) == list(left_terms)
    assert chain.analyze(right) == list(right_terms)
    assert set(left_terms) & set(right_terms) == set(), (
        f"row {case.number} of the merged table stopped being a loss: {left} and {right} now share a term. "
        f"That is a finding, not a fix waiting to be pocketed. Run {MEASURE_CHAINS} first"
    )


def _asserted_forms(known_losses: dict[str, set[tuple[str, str]]]) -> dict[str, set[str]]:
    """Every surface form this module makes a form family claim about.

    Deliberately not every word of the module. The English no-op vocabulary
    proves that an empty custom stop word filter changes nothing and belongs to
    a chain with no form family fixture, and the stop word rows of the merged
    table are covered by the provenance gate below instead, against the built in
    lists they are entries of. The hand written cases at the top of the file are
    rows 1, 7 and 9 and arrive through the table.
    """
    asserted: dict[str, set[str]] = {code: set() for code in CODES}
    for code, pairs in known_losses.items():
        for left, right in pairs:
            asserted[code].update((left, right))
    for case in MERGED_CASES:
        if case.expectation != BOTH_EMPTY:
            asserted[case.code].update(form for group in case.groups for form in group)
    return asserted


def test_every_asserted_form_stands_in_the_measured_case_list(
    known_losses: dict[str, set[tuple[str, str]]], families: dict[str, list[list[str]]]
) -> None:
    # The gate over the gate. A claim about a form the probe never ran is a
    # claim about nothing, and it would look exactly like the measured ones.
    asserted = _asserted_forms(known_losses)

    missing: list[str] = []
    for code in CODES:
        measured = {form for forms in families[code] for form in forms}
        missing.extend(
            f"{code}: {form} is asserted here but stands in no family of {CASES[code].name}"
            for form in sorted(asserted[code] - measured)
        )

    assert missing == [], f"{'; '.join(missing)}. Add the form to its fixture and rerun {MEASURE_CHAINS}"


def test_every_stop_word_row_names_a_word_of_a_built_in_list(
    builtin_stopwords: dict[str, list[str]], folder: TextAnalyzer
) -> None:
    # The other half of the gate over the gate. A stop word row has no form
    # family to stand in, so its provenance is the built in list of its language
    # or the supplement derived from it, in one of the two spellings. Without
    # this a row could name a word that is in no list at all, pass because the
    # chain drops it for some other reason, and claim a stop word is handled.
    stray: list[str] = []
    for case in MERGED_CASES:
        if case.expectation != BOTH_EMPTY:
            continue
        language = SNOWBALL_NAME[case.code]
        known = set(builtin_stopwords[language]) | set(FOLDED_STOPWORDS[language])
        for form in (word for group in case.groups for word in group):
            folded = folder.analyze(form)
            flat = folded[0] if folded else ""
            if form not in known and flat not in known:
                stray.append(f"row {case.number}: {form} stands in no built in {language} list and in no supplement")

    assert stray == [], f"{'; '.join(stray)}. A stop word row without a list entry behind it proves nothing"
