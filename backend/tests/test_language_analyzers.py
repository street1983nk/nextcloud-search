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

Accents appear only inside string literals. They are data here, the words the
product has to handle; the identifiers stay ASCII as the project rules require.
"""

from tantivy import Filter, TextAnalyzerBuilder, Tokenizer

from findling.index.analyzer import ANALYZER_VERSION, english_analyzer, snowball_analyzer
from findling.index.stopwords import FOLDED_STOPWORDS


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
        .filter(Filter.remove_long(48))
        .filter(Filter.stemmer("english"))
        .build()
    )
    now = english_analyzer()

    for word in ("the", "running", "Kündigung", "café", "Straße", "documents", "a"):
        assert now.analyze(word) == before.analyze(word), word


def test_the_analyzer_version_did_not_move() -> None:
    # Four chains were added and none of them was registered anywhere, so no
    # index that exists today tokenises differently than it did yesterday. The
    # mark rises in phase 18, together with the schema.
    assert ANALYZER_VERSION == 1
