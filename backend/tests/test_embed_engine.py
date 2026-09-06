"""One embedding engine per process, and the falsification that had to come first.

**Why this file opens with a claim that is wrong.** The measurement report of
plan 06-11 split the second load of the search side into three items: the
tokenizer, the onnxruntime session, and "a second German decomposition automaton
built from the word list, 64 MB by the breakdown". The third item does not
exist. ``index/analyzer.py`` holds a process wide cache keyed on the digest of
the constituent list, it counts every real build in ``build_count()``, and
``open_index`` is the only place in the running app that registers an analyzer.
A search gets a cache hit there, not a second automaton.

The falsification belongs in front of the change and not in a document. This
plan takes the second engine out of the process and the memory number will fall.
With the automaton still on the list of causes nobody could split that saving
into its parts afterwards, and a plan whose numbers cannot be accounted for has
to be believed rather than checked (06.1-RESEARCH.md, pitfall 1).

**What the search side really does a second time** is read the word list.
``build_artifact`` has no cache, and the log line "constituent list read from the
volume" of 05:15Z is the evidence the report read as an automaton. That is a
different item, it costs about 21.9 MB, and it belongs to plan 06.1-04. It is
deliberately not touched here, because one change that fixes two items reports
one number for both.

**What this file does not do.** It measures no bytes. A peak difference is not
the sum of the loads that produced it, and a test that counts resident memory on
a shared runner is a random number generator with an assertion attached.
Everything below is a counter or an object identity.
"""

from __future__ import annotations

from conftest import CONSTITUENTS, Corpus
from findling.api import resources
from findling.index.analyzer import build_count, cached_german_analyzer

# Digests of this file only, and three of them for two cases. The cache keeps
# exactly one entry, so a case that reused the digest of the case before it
# would take a cache hit where it expects a build, and the result would depend
# on the order the suite happens to run in.
DIGEST_ONE = "06.1-02-falsification-one"
DIGEST_TWO = "06.1-02-falsification-two"
DIGEST_THREE = "06.1-02-falsification-three"


def test_a_search_side_open_does_not_build_the_automaton_again(indexed_volume: Corpus) -> None:
    # The fixture wrote the index the way the indexing side does, so the
    # automaton for this word list is already built when the counter is read.
    # What follows is the search side opening the same volume, which is the
    # exact moment the 06-11 report placed the second build at.
    before = build_count()

    side = resources.read_side()

    assert side is not None, "the fixture volume carries an index and a state database"
    assert build_count() == before, "the search side takes a cache hit, it does not build a second automaton"


def test_the_same_word_list_is_a_cache_hit_and_not_a_second_automaton() -> None:
    before = build_count()

    first = cached_german_analyzer(DIGEST_ONE, CONSTITUENTS)
    second = cached_german_analyzer(DIGEST_ONE, CONSTITUENTS)

    assert first is second
    assert build_count() - before == 1


def test_a_different_word_list_does_build_a_second_automaton() -> None:
    # The counterpart, and the reason the two cases above mean anything: this
    # one has to go up. Without it the file would be green against a counter
    # that never moves, which proves a frozen number and not a working cache.
    before = build_count()

    cached_german_analyzer(DIGEST_TWO, CONSTITUENTS)
    cached_german_analyzer(DIGEST_THREE, CONSTITUENTS)

    assert build_count() - before == 2
