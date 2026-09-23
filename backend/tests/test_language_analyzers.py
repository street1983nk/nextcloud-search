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

Accents appear only inside string literals. They are data here, the words the
product has to handle; the identifiers stay ASCII as the project rules require.
"""

import importlib.util
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

import pytest
from tantivy import Filter, TextAnalyzer, TextAnalyzerBuilder, Tokenizer

from findling.config import SNOWBALL_NAME
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
# the difference into the measurement report, and only then pull this value
# after it. Never the other way round.
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
    chain = snowball_analyzer("spanish", FOLDED_STOPWORDS["spanish"])

    assert chain.analyze("información") == chain.analyze("informacion")
    assert chain.analyze("informacion") != []


def test_an_italian_stop_word_is_dropped_in_both_spellings() -> None:
    # "perche" is in the built in list with its accent only. Without the
    # supplement the flat spelling survives the fold and lands in the index.
    chain = snowball_analyzer("italian", FOLDED_STOPWORDS["italian"])

    assert chain.analyze("perché") == []
    assert chain.analyze("perche") == []


def test_the_dutch_accent_case_leaves_no_rubbish_token() -> None:
    # Dutch has no accented entry in its built in list, so its supplement is
    # empty, and the built in entry "een" has to catch the folded form on its own.
    chain = snowball_analyzer("dutch", FOLDED_STOPWORDS["dutch"])

    assert chain.analyze("één") == []
    assert chain.analyze("een") == []


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
        "def snowball_analyzer(language, folded_stopwords):\n"
        "    return (\n"
        "        TextAnalyzerBuilder(Tokenizer.simple())\n"
        "        .filter(Filter.lowercase())\n"
        "        .filter(Filter.stopword(language))\n"
        "        .filter(Filter.custom_stopword(list(folded_stopwords)))\n"
        "        .filter(Filter.remove_long(MAX_TOKEN_CHARS))\n"
        "        .filter(Filter.stemmer(language))\n"
        "        .filter(Filter.ascii_fold())\n"
        "        .build()\n"
        "    )\n"
    )

    chain = filter_chain(source, "snowball_analyzer")

    assert chain.index("ascii_fold") > chain.index("stemmer")
    assert chain != EXPECTED_SNOWBALL_CHAIN


def test_a_comment_that_names_a_filter_does_not_enter_the_chain() -> None:
    source = (
        "def snowball_analyzer(language, folded_stopwords):\n"
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
        "scripts/dev/stopword_supplement.py, record the difference, then pull this constant after it"
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
    return {code: snowball_analyzer(SNOWBALL_NAME[code], FOLDED_STOPWORDS[SNOWBALL_NAME[code]]) for code in CODES}


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


def _asserted_forms(known_losses: dict[str, set[tuple[str, str]]]) -> dict[str, set[str]]:
    """Every surface form this module makes a form family claim about.

    Deliberately not every word of the module. The English no-op vocabulary
    proves that an empty custom stop word filter changes nothing, it belongs to
    a chain with no form family fixture, and the words of the hand written cases
    at the top are rows of the merged table and arrive through it.
    """
    asserted: dict[str, set[str]] = {code: set() for code in CODES}
    for code, pairs in known_losses.items():
        for left, right in pairs:
            asserted[code].update((left, right))
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
