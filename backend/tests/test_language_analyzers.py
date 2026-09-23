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

What this file does NOT prove: that the built in stop word lists are airtight
under the fold. That measurement runs over all 891 built in entries of the four
languages, needs stopwords.rs, and is the promise of plans 17-05 and 17-06. What
stands here is the necessity of every supplement entry, which is the other
direction and cheap enough to run offline.

Accents appear only inside string literals. They are data here, the words the
product has to handle; the identifiers stay ASCII as the project rules require.
"""

from tantivy import Filter, TextAnalyzerBuilder, Tokenizer

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
