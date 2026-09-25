"""The analysis chains. The order of the filters is the design decision.

German chain, and every position was measured rather than reasoned about:

    | # | Filter                  | Why exactly here                            |
    |---|-------------------------|---------------------------------------------|
    | 0 | Tokenizer.simple        | Splits on non alphanumeric, keeps digits    |
    | 1 | lowercase               | Everything after this compares strings      |
    |   |                         | exactly, and the constituent list is        |
    |   |                         | lowercase                                   |
    | 2 | split_compound(list)    | Needs the raw, unstemmed, unfolded token;   |
    |   |                         | the list lies in exactly that form          |
    | 3 | custom_stopword(FUGEN)  | Without it a bare token "s" reaches the     |
    |   |                         | index. Measured: Kuendigungsfrist gives     |
    |   |                         | kundig, frist with it and kundig, s, frist  |
    |   |                         | without it                                  |
    | 4 | stopword("german")      | The built in list carries real umlauts and  |
    |   |                         | compares exactly, so it has to see unfolded |
    |   |                         | tokens                                      |
    | 5 | remove_long(48)         | AFTER the splitter, see below               |
    | 6 | stemmer("german")       | Last. A stemmed compound matches no          |
    |   |                         | dictionary entry any more                   |

The Snowball chain of every other language, built by one factory, and every
position of it was measured on 2026-09-23 against tantivy tag 0.26.2:

    | # | Filter                  | Why exactly here                            |
    |---|-------------------------|---------------------------------------------|
    | 0 | Tokenizer.simple        | Splits on non alphanumeric, keeps digits    |
    | 1 | lowercase               | Everything after this compares strings      |
    |   |                         | exactly, including both stop word filters   |
    | 2 | ascii_fold              | In front of the stop word list and thereby  |
    |   |                         | in front of the stemmer. The only position  |
    |   |                         | that keeps the accented and the flat        |
    |   |                         | spelling of a word on one term: measured    |
    |   |                         | 467 of 573 ordered surface form pairs,      |
    |   |                         | against 463 with a late fold                |
    | 3 | stopword(lang)          | The built in Snowball list of the language  |
    | 4 | custom_stopword(folded) | Directly behind it, because the built in    |
    |   |                         | list compares exactly and carries real      |
    |   |                         | accents, so the fold has just made it miss. |
    |   |                         | Without this filter 77 Spanish, 10 Italian  |
    |   |                         | and 30 Portuguese stop words reach the      |
    |   |                         | index as terms, in both spellings           |
    | 5 | remove_long(48)         | Same limit as the German chain. Nothing     |
    |   |                         | splits here, so there is no splitter to     |
    |   |                         | stand behind                                |
    | 6 | stemmer(lang)           | Last, as in every other chain                |

Two positions carry the whole file.

*remove_long stands after the splitter.* Measured: at position two with a limit
of 40, the 63 character compound
"Rindfleischetikettierungsueberwachungsaufgabenuebertragungsgesetz" produces the
empty token list. The word is then gone, and the document is findable under none
of its six parts. Behind the splitter the same word produces six clean tokens.
tantivy's own default analyzer makes exactly this mistake, which is why the
default analyzer is not used here.

*The German branch has no folding filter.* The Snowball stemmer for German folds
umlauts and sharp s by itself: Mueller with umlaut and Muller both end as "mull",
Strasse with sharp s and Strasse both end as "strass". Folding in front of the
splitter would additionally devalue the constituent list, which carries umlauts,
and the splitting would then fail silently while every shallow test stays green.
English and the file name branch do fold, because there a different algorithm
stems or nothing stems at all.

Cost and lifetime: building the automaton over the 276496 entry list costs 0.44 s
and roughly 23 MB of resident memory that never comes back. That is acceptable
exactly once per process and never twice, so the factory below is a per process
singleton keyed on the digest of the list, and a counter makes the number of
builds testable. On the 4 GB box this project targets, a second build is not an
untidiness, it is the difference between a search service and a memory problem.
For the same reason the extraction child of plan 02-05 must not import this
module at all: it would pay the megabytes for every file it looks at.

Any change to a chain below has to raise ANALYZER_VERSION. Tokenisation is part
of the data: an index written with one chain and queried with another disagrees
with itself, and the only correct answer to that is a visible reindex.

The other half of that sentence, and it is just as load bearing: a chain that is
added here but registered nowhere changes no tokenisation, so it does not move
the mark either. index/open.py registers four tokenizer names and the factory
below is reached by exactly one of them, the English one, token identically.
Raising the mark out of caution would order a reindex on every installation in
the field for a change no index can see. The mark rises in phase 18, together
with the schema that first names the new languages.

And one named exception to the sentence, just as load bearing: the Dutch
splitter chain of phase 21 does not move ANALYZER_VERSION. It is carried by a
mark of its own, wordlist_hash_nl, whose value is the digest of the Dutch list
together with DUTCH_CHAIN_VERSION from findling.index.wordlist_nl, and which
reads "off" while nl is not configured. Raising ANALYZER_VERSION instead would
order a full reindex of roughly 19 h on every installation in the field, with
or without Dutch, for a chain only the Dutch field sees (D-05). A change to
dutch_analyzer below raises DUTCH_CHAIN_VERSION, not ANALYZER_VERSION.

Dutch chain, recipe B 4-14, the Snowball chain above with the splitter put in
directly behind the fold:

    | # | Filter                        | Why exactly here                      |
    |---|-------------------------------|---------------------------------------|
    | 0 | Tokenizer.simple              | As in every chain                     |
    | 1 | lowercase                     | The list is lowercase                 |
    | 2 | ascii_fold                    | Where phase 17 measured it. The list  |
    |   |                               | is folded, so the splitter must see   |
    |   |                               | folded tokens: coordinatiecentrum     |
    |   |                               | without the trema comes apart too     |
    | 3 | split_compound(list)          | Unstemmed, folded tokens              |
    | 4 | custom_stopword(TUSSENKLANKEN)| No bare "s" in the index              |
    | 5 | stopword("dutch")             | As in the Snowball chain              |
    | 6 | custom_stopword(folded)       | As in the Snowball chain, empty for   |
    |   |                               | Dutch                                 |
    | 7 | remove_long(48)               | Behind the splitter, German reasons   |
    | 8 | stemmer("dutch")              | Last                                  |
"""

import gc
import logging
import threading
import time
import unicodedata
from collections.abc import Sequence
from pathlib import Path

from tantivy import Filter, TextAnalyzer, TextAnalyzerBuilder, Tokenizer

from findling.config import DEFAULT_COMPOUND_DICT, LANGUAGE_ALLOWLIST, SNOWBALL_NAME, settings
from findling.index.stopwords import FOLDED_STOPWORDS
from findling.index.wordlist import FUGEN, SYSTEM_WORDLIST, load_constituents, rss_bytes, wordlist_hash
from findling.index.wordlist_nl import TUSSENKLANKEN, build_artifact_nl

LOGGER = logging.getLogger("findling.index.analyzer")

# Raise this whenever a chain below changes. It lives here, next to the chains it
# describes, and not in findling.config, because a version number kept away from
# the thing it versions is a version number that stops being raised.
ANALYZER_VERSION = 1

# The schema stores the NAME of a tokenizer, never the tokenizer. Opening an
# index without registering exactly these names fails at the first parse_query
# with "the tokenizer 'de' for the field 'body_de' is unknown", which reads like
# a broken index and is a missing line of setup. Plan 02-06 reads them from here.
TOKENIZER_DE = "de"
TOKENIZER_EN = "en"
# The four chains of the v1.3 language build out, named after the field codes of
# findling.config.SNOWBALL_NAME and never after the Snowball language, because
# the schema field is body_es and the name a schema persists has to be readable
# next to the field it belongs to. All four are built by snowball_analyzer, which
# is one armed and looks its own supplement up: there is no second factory here
# and there must not be one.
TOKENIZER_ES = "es"
TOKENIZER_IT = "it"
TOKENIZER_NL = "nl"
TOKENIZER_PT = "pt"
TOKENIZER_NAME = "name"

# Longest token that may reach the index. Generous on purpose: it exists to stop
# base64 blobs and minified assets, not German words. Applied after the splitter
# in the German chain, where the longest real part is far below it.
MAX_TOKEN_CHARS = 48

# File names are not split into constituents, so their limit is higher. Nothing
# stems them either, so a long name stays one long term.
MAX_NAME_CHARS = 60

# Per process singleton, keyed on the digest of the constituent list. The digest
# is the right key: two lists with the same digest tokenise identically, and two
# with different digests must never share an automaton (T-02-11). At most one
# entry lives in here, so a changed list frees the old automaton instead of
# stacking a second 23 MB next to it.
_CACHED_GERMAN: dict[str, TextAnalyzer] = {}

# One lock around lookup and build, for each of the two caches (review finding
# WR-01 of phase 21). The reading side opens under its own lock in
# api/resources.py, but the poller and the band run open in threads of their own
# without it, and the build between a miss and the insert takes 0.4 to 0.8 s. Two
# openings inside that window each missed the cache and each built an automaton,
# and the loser stayed resident through the tokenizer registration of its index
# object: exactly the second 23 MB this cache exists to prevent. Two locks and
# not one, so that a German build does not hold a Dutch lookup that is a hit, and
# plain locks, because nothing below takes either of them twice.
_GERMAN_LOCK = threading.Lock()

# How often the automaton was really built in this process. Read by the test that
# proves the singleton works; a counter is the only way to tell a cache hit from
# a cheap rebuild from the outside.
_BUILD_COUNT = 0


def build_count() -> int:
    """Return how many German automata this process has built."""
    return _BUILD_COUNT


# The Dutch counterpart of the two above, keyed on the digest of the Dutch list.
# A second automaton of roughly 17.6 MB, paid only while nl is configured, and
# never twice for the same list.
_CACHED_DUTCH: dict[str, TextAnalyzer] = {}

# The Dutch half of the pair of locks above. dutch_chain_for holds it across the
# read of the artifact as well, so two threads also never put the list into
# memory twice.
_DUTCH_LOCK = threading.Lock()

_DUTCH_BUILD_COUNT = 0


def dutch_build_count() -> int:
    """Return how many Dutch automata this process has built."""
    return _DUTCH_BUILD_COUNT


def normalize(text: str) -> str:
    """Return the one Unicode spelling this index uses. Called on both sides.

    A file name with an umlaut has two spellings that look identical on screen.
    macOS clients hand the name over decomposed, as a letter followed by a
    combining diaeresis (NFD), while Linux clients and the web interface hand it
    over composed, as one character (NFC). tantivy compares bytes, and the
    folding filter of the file name chain folds ASCII only, so a combining
    diaeresis survives every filter this module has.

    Measured, and it is worse than "the two tokenise differently": the simple
    tokenizer splits on the combining character, so ``Kündigung.pdf`` written by
    a Mac becomes ``ku``, ``ndigung``, ``pdf`` while the same name typed into the
    search bar of the web interface becomes ``kundigung``, ``pdf``. The two share
    no term at all. The user sees an empty result list with no reason in it,
    which is the one kind of defect nobody reports, because it looks like the
    file simply is not there.

    NFC and not NFD, because NFC is the form Nextcloud and its web interface
    deliver, so the composed spelling is the majority of the stock and the
    cheaper of the two to converge on.

    It lives here, next to the analysers, because it belongs to the tokenisation
    chain: it decides what a term is, exactly as the filters above do. It is
    called from two places and a test holds that number. Two callers, one helper;
    a third normalisation somewhere else would be a third text space, and a text
    space that disagrees with the index is the failure this whole module is
    arranged against.

    It is deliberately not a filter of the chains above. A filter runs after the
    tokenizer, and the tokenizer is what splits on the combining character in the
    first place, so a filter would arrive one step too late.
    """
    return unicodedata.normalize("NFC", text)


def german_analyzer(constituents: Sequence[str]) -> TextAnalyzer:
    """Build the German chain over an already prepared constituent list.

    ``constituents`` comes from :func:`findling.index.wordlist.load_constituents`
    and already contains the linking elements, so they are not added again here.
    They come back out one filter later as custom stopwords, and both uses read
    the same FUGEN constant so that they cannot drift apart.

    Building is expensive. Callers in the running app use
    :func:`cached_german_analyzer`; this function stays public because the tests
    build deliberately and because a caller with its own lifetime management
    should not have to go around the cache.
    """
    global _BUILD_COUNT

    started = time.perf_counter()
    analyzer = (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.split_compound(list(constituents)))
        .filter(Filter.custom_stopword(list(FUGEN)))
        .filter(Filter.stopword("german"))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer("german"))
        .build()
    )
    _BUILD_COUNT += 1
    LOGGER.info(
        "german automaton built from %d entries in %.3f s, build %d in this process",
        len(constituents),
        time.perf_counter() - started,
        _BUILD_COUNT,
    )
    return analyzer


def english_analyzer() -> TextAnalyzer:
    """Build the English chain: fold, drop stopwords, stem with Porter.

    One line, because the chain it used to spell out by hand is exactly the
    chain :func:`snowball_analyzer` builds: the English supplement is empty and
    an empty custom stop word filter is measured to be a no-op. The move is
    therefore token identical, and backend/tests/test_language_analyzers.py
    proves that rather than asserting it, by running the words of this chain
    through a hand built copy of its old shape.

    The signature stays as it was so that index/open.py keeps its line.
    """
    return snowball_analyzer("english")


def snowball_analyzer(language: str) -> TextAnalyzer:
    """Build the chain for one Snowball language other than German.

    The fold stands in front of the stop word filter and therefore in front of
    the stemmer, and that position was measured rather than reasoned about: it
    is the only position that keeps the accented and the flat spelling of a word
    on one term, which is what a user who does not type accents and a scan that
    lost them both need. The price is measured too and it is documented in
    docs/language-analyzers.md: the class of words whose Snowball suffix carries
    an accent loses its number pair.

    One arm and not two. The supplement is no parameter of this factory but a
    property of the language, and it is looked up here rather than handed in,
    because the two parameters it used to take belonged together and nothing
    held them together. Three cases were measured on 2026-09-23 and all three
    are closed by this shape:

    *A language outside the allowlist.* Eight of the thirteen allowlisted
    languages carry no supplement at all (danish, finnish, french, german,
    hungarian, norwegian, russian, swedish), so the caller pattern
    ``snowball_analyzer(name, FOLDED_STOPWORDS[name])`` raised a bare
    ``KeyError`` out of the mapping for them. A name tantivy does not carry at
    all reached ``Filter.stopword`` and cost a panic in tantivy 0.26.0 and a
    ``ValueError`` in 0.26.2. Both now end as one ``ValueError`` that names the
    language and the list it is missing from.

    *A language in the allowlist without a supplement.* French is the loud
    example: it is allowlisted, it carries accents and it has no supplement, so
    a chain built with an empty one turned both accented and flat spellings of
    its accented stop words into ordinary index terms without anything going
    red. That is a refusal now and not a silent leak.

    *A name in another spelling.* tantivy takes the language name regardless of
    case, the mapping and the allowlist are lowercase and compare exactly, so
    ``snowball_analyzer("Spanish")`` used to build a working chain that let all
    77 Spanish supplement entries through. The name is lowered once here and
    every filter below sees the lowered form.

    The supplement is what the fold tears into the built in list. The built in
    lists compare exactly and carry real accents, so once the fold has run in
    front of them they no longer match. It is derived from the same lists by
    scripts/dev/stopword_supplement.py, so it cannot drift away from them. For
    English and Dutch it is empty, and an empty custom stop word filter is
    measured to be a no-op, which is why English can use this factory without
    its tokenisation moving by one byte.

    Deliberately not a cached singleton, unlike the German factory above. The
    German automaton costs 0.44 s and roughly 23 MB that never come back,
    because it carries a 276496 entry word list; the four Snowball chains are
    compiled into tantivy and carry nothing. A cache for them would be ballast,
    and vulture would be right to flag it.
    """
    name = language.lower()
    if name not in LANGUAGE_ALLOWLIST:
        raise ValueError(f"{language} is not in LANGUAGE_ALLOWLIST, so no chain is built for it")
    if name not in FOLDED_STOPWORDS:
        raise ValueError(
            f"{language} has no measured folded supplement; derive one with scripts/dev/stopword_supplement.py "
            "before a chain for it is built"
        )
    folded = FOLDED_STOPWORDS[name]
    return (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())
        .filter(Filter.stopword(name))
        .filter(Filter.custom_stopword(list(folded)))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer(name))
        .build()
    )


def name_analyzer() -> TextAnalyzer:
    """Build the file name chain: fold, no stopwords, no stemming.

    A file name is looked for the way it is written. Stemming would make
    "Kuendigung.pdf" and "Kuendigungen.pdf" the same name, and dropping stopwords
    would delete the words people actually name their files after.
    """
    return (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())
        .filter(Filter.remove_long(MAX_NAME_CHARS))
        .build()
    )


def cached_german_analyzer(digest: str, constituents: Sequence[str]) -> TextAnalyzer:
    """Return the process wide German analyser for this constituent list.

    The single supported way to get an analyser in the running app. Two calls
    with the same digest return the same object; a different digest replaces it,
    because the old one describes a tokenisation the index no longer uses.

    Lookup and build stand under one lock, so two threads that arrive together
    build one automaton and not two (review finding WR-01 of phase 21).
    """
    with _GERMAN_LOCK:
        cached = _CACHED_GERMAN.get(digest)
        if cached is not None:
            return cached
        analyzer = german_analyzer(constituents)
        _CACHED_GERMAN.clear()
        _CACHED_GERMAN[digest] = analyzer
        return analyzer


def dutch_analyzer(constituents: Sequence[str]) -> TextAnalyzer:
    """Build the Dutch splitter chain over an already folded constituent list.

    ``constituents`` comes from :func:`findling.index.wordlist_nl.load_constituents_nl`,
    is folded and already contains the linking elements. They come back out as
    custom stopwords directly behind the splitter, read from the same
    TUSSENKLANKEN constant. The rest of the chain is the Snowball chain of
    :func:`snowball_analyzer` for Dutch, filter for filter.

    Callers in the running app go through :func:`dutch_chain_for`.
    """
    global _DUTCH_BUILD_COUNT

    name = SNOWBALL_NAME["nl"]
    started = time.perf_counter()
    analyzer = (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())
        .filter(Filter.split_compound(list(constituents)))
        .filter(Filter.custom_stopword(list(TUSSENKLANKEN)))
        .filter(Filter.stopword(name))
        .filter(Filter.custom_stopword(list(FOLDED_STOPWORDS[SNOWBALL_NAME["nl"]])))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer(name))
        .build()
    )
    _DUTCH_BUILD_COUNT += 1
    LOGGER.info(
        "dutch automaton built from %d entries in %.3f s, build %d in this process",
        len(constituents),
        time.perf_counter() - started,
        _DUTCH_BUILD_COUNT,
    )
    return analyzer


def cached_dutch_analyzer(digest: str, constituents: Sequence[str]) -> TextAnalyzer:
    """Return the process wide Dutch analyser for this list, built at most once."""
    with _DUTCH_LOCK:
        return _cached_dutch_analyzer_locked(digest, constituents)


def _cached_dutch_analyzer_locked(digest: str, constituents: Sequence[str]) -> TextAnalyzer:
    """Lookup and build of the Dutch cache. The caller holds ``_DUTCH_LOCK``."""
    cached = _CACHED_DUTCH.get(digest)
    if cached is not None:
        return cached
    analyzer = dutch_analyzer(constituents)
    _CACHED_DUTCH.clear()
    _CACHED_DUTCH[digest] = analyzer
    return analyzer


def dutch_chain_for(digest: str | None) -> TextAnalyzer:
    """Return the chain for the Dutch field under the given list digest.

    None means nl is not configured, and the field keeps the plain Snowball
    chain it has had since phase 17, without a list and without an automaton.
    A digest answers from the cache when its automaton was already built, and
    otherwise reads the artifact on the volume. When the volume holds another
    list than the one the digest names, this fails closed: a chain over a list
    the mark does not describe would tokenise differently from the index.

    The list is a local here and gone after the build (D-02), so the process
    keeps the automaton and not the roughly 19.6 MB of Python strings behind it.

    The whole miss, read and build included, stands under ``_DUTCH_LOCK``
    (review finding WR-01 of phase 21): the poller, the band run and the reading
    side open in threads of their own, and a lookup outside the lock let two of
    them each read the list and each build an automaton.
    """
    if digest is None:
        return snowball_analyzer(SNOWBALL_NAME["nl"])
    with _DUTCH_LOCK:
        cached = _CACHED_DUTCH.get(digest)
        if cached is not None:
            return cached
        artifact = build_artifact_nl()
        if artifact.digest != digest:
            raise ValueError("the dutch constituent list on the volume does not carry the expected digest")
        return _cached_dutch_analyzer_locked(digest, artifact.entries)


# ---------------------------------------------------------------------------
# Measurement mode. Numbers only, never a token and never a word: this path sees
# user content, and a measurement that prints what it tokenised is the cheapest
# way to leak it (T-02-14). Driven by scripts/dev/measure_wordlist.sh, which runs
# it in a throwaway Debian container.
# ---------------------------------------------------------------------------

# One fixed sentence of German compounds, repeated into a workload large enough
# to time. Fixed text, not user content, so a throughput number reveals nothing.
_SAMPLE_SENTENCE = (
    "Die Grundstuecksverkehrsgenehmigung und die Kuendigungsfrist stehen in der "
    "Sitzungsvorlage zur Haushaltssatzung des Jahresabschlusses."
)
_SAMPLE_REPEATS = 2000


def measure(source: Path = SYSTEM_WORDLIST, *, variant: str = DEFAULT_COMPOUND_DICT) -> dict[str, float | int | str]:
    """Measure the automaton: build time, resident memory, throughput.

    Two memory numbers, because only one of them is the number that matters. The
    growth during the build still carries the Python list; what the process pays
    forever is what is left once that list is gone, and that is the number the
    RAM budget of a 4 GB box has to hold.
    """
    rss_start = rss_bytes()
    entries = load_constituents(source, variant=variant)
    digest = wordlist_hash(entries)
    rss_with_list = rss_bytes()

    build_started = time.perf_counter()
    analyzer = german_analyzer(entries)
    build_seconds = time.perf_counter() - build_started
    rss_with_automaton = rss_bytes()

    tokens = 0
    throughput_started = time.perf_counter()
    for _ in range(_SAMPLE_REPEATS):
        tokens += len(analyzer.analyze(_SAMPLE_SENTENCE))
    throughput_seconds = time.perf_counter() - throughput_started

    entries = []
    gc.collect()
    rss_automaton_only = rss_bytes()

    return {
        "analyzer_version": ANALYZER_VERSION,
        "wordlist_hash": digest,
        "build_seconds": round(build_seconds, 3),
        "rss_growth_during_build_bytes": rss_with_automaton - rss_with_list,
        "rss_permanent_bytes": rss_automaton_only - rss_start,
        "tokens_per_second": round(tokens / throughput_seconds) if throughput_seconds else 0,
        "builds_in_this_process": build_count(),
    }


if __name__ == "__main__":  # pragma: no cover
    for key, value in measure(variant=settings().compound_dict).items():
        print(f"{key}={value}")
