"""The language allowlist, held against the tantivy this build actually runs.

``LANGUAGE_ALLOWLIST`` in ``findling.config`` claims something about a foreign
library: that every name in it is carried by both halves of the analyzer chain,
a Snowball stemmer and a builtin stop word list. The counterpart of that claim
is the running engine and never a second list in this file. A test that repeats
the set it guards agrees with itself on the very day somebody adds a fourteenth
language, which is the only day it matters.

Two ways the claim can go wrong, and both are asserted below.

A name in the allowlist that tantivy cannot carry is a false promise. From
phase 18 on the chain factory reads this set and hands the name straight to
``Filter.stopword``, so a wrong entry is not a warning in a log, it is the
container failing to come up.

A name reachable through ``SNOWBALL_NAME`` that is missing from the allowlist is
the same accident from the other side, one release earlier: it looks harmless
today, because no production path reads either constant yet, and it turns into a
crash on the day the factory is wired up.

The measurement this file rests on, taken on 2026-09-23 against tantivy 0.26.0:
``Filter.stemmer`` serves 18 languages, ``Filter.stopword`` serves 13, and the
five in the difference are arabic, greek, romanian, tamil and turkish. The
failure does not appear where a reader expects it. ``Filter.stopword(name)``
constructs happily for all five; the panic arrives when that filter is attached
to a builder and the chain is finished. So the helper below always builds the
chain to the end, and a test that only constructed a filter would be green and
would prove nothing.
"""

from __future__ import annotations

from tantivy import Filter, TextAnalyzerBuilder, Tokenizer

from findling.config import LANGUAGE_ALLOWLIST, SNOWBALL_NAME, SUPPORTED_LANGUAGES

# The staged mutation of this file, and the reason it is this name: measured on
# 2026-09-23, it has a stemmer and no builtin stop word list, which is exactly
# the shape that brings the Rust side down. Any of the other four would do.
MUTATED_LANGUAGE = "romanian"


def builds(language: str, *, with_stopword: bool, with_stemmer: bool) -> bool:
    """Whether the running tantivy carries this language for the filters asked for.

    The chain is finished, not just assembled, because that is where the failure
    lives. What comes back is a plain bool and never an exception type, so that
    the assertions hold under both versions in play: tantivy 0.26.0 panics on a
    language without a stop word list, 0.26.2 raises a ValueError for the same
    case, and neither belongs in the assertion. That pair of outcomes is also
    why the except clause below is as broad as it is: a panic is not an
    Exception, so the narrow clause would catch one of the two and miss the
    other, which is the one that matters.
    """
    try:
        builder = TextAnalyzerBuilder(Tokenizer.simple())
        if with_stopword:
            builder = builder.filter(Filter.stopword(language))
        if with_stemmer:
            builder = builder.filter(Filter.stemmer(language))
        builder.build()
    # BaseException and not Exception, which is the one place in this tree where
    # that is the correct clause: the 0.26.0 failure is a pyo3 PanicException,
    # which derives straight from BaseException. Narrowing this would let the
    # very case this file exists for escape as a test error instead of the red
    # assertion it is supposed to produce.
    except BaseException:
        return False
    return True


def test_every_offered_language_is_carried_by_the_running_tantivy() -> None:
    # Both halves separately, because the message has to name the language and
    # the side it fails on. "The allowlist and tantivy disagree" would leave the
    # reader building thirteen analyzer chains by hand to find out which one.
    broken: list[str] = []
    for language in sorted(LANGUAGE_ALLOWLIST):
        if not builds(language, with_stopword=True, with_stemmer=False):
            broken.append(f"{language} is offered and the running tantivy has no builtin stop word list for it")
        if not builds(language, with_stopword=False, with_stemmer=True):
            broken.append(f"{language} is offered and the running tantivy has no stemmer for it")

    assert broken == [], f"the allowlist promises languages this engine cannot carry: {broken}"


def test_every_product_language_stands_in_the_allowlist() -> None:
    unmapped = sorted(set(SUPPORTED_LANGUAGES) - set(SNOWBALL_NAME))
    assert unmapped == [], f"these field codes have no tantivy name at all: {unmapped}"

    missing = [
        f"{code} maps to {name}, and {name} is not in LANGUAGE_ALLOWLIST: that is a panic waiting for phase 18"
        for code, name in sorted(SNOWBALL_NAME.items())
        if name not in LANGUAGE_ALLOWLIST
    ]

    assert missing == [], f"the map reaches past the allowlist: {missing}"


def test_the_guard_sees_a_language_with_a_stemmer_but_no_stop_word_list() -> None:
    # A gate whose red state is never produced is a gate nobody has tested. This
    # is that red state, staged rather than described: the same language passes
    # the stemmer half and fails the moment the stop word half is asked for.
    assert builds(MUTATED_LANGUAGE, with_stemmer=True, with_stopword=False) is True
    assert builds(MUTATED_LANGUAGE, with_stemmer=True, with_stopword=True) is False

    # And the conclusion the allowlist draws from it.
    assert MUTATED_LANGUAGE not in LANGUAGE_ALLOWLIST


def test_the_thirteen_hold_and_the_six_are_a_true_subset() -> None:
    # Thirteen, and the number is the assertion. It is not a taste decision that
    # may drift with the next language somebody wants: it is the size of the
    # intersection the engine serves, and a fourteenth entry means the engine
    # grew one, which is a measurement somebody has to redo and defend.
    assert len(LANGUAGE_ALLOWLIST) == 13

    # Six body fields, and a true subset of the thirteen in both directions:
    # the product may never offer a language the engine refuses, and the
    # allowlist has to stay the larger of the two, because it is the set the
    # chain factory of phase 18 validates against and not the set it ships.
    assert len(SUPPORTED_LANGUAGES) == 6
    assert set(SNOWBALL_NAME.values()) < set(LANGUAGE_ALLOWLIST)
