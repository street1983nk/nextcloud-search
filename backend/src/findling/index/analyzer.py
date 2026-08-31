"""The three analysis chains. The order of the filters is the design decision.

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
"""

import gc
import logging
import time
from collections.abc import Sequence
from pathlib import Path

from tantivy import Filter, TextAnalyzer, TextAnalyzerBuilder, Tokenizer

from findling.config import DEFAULT_COMPOUND_DICT, settings
from findling.index.wordlist import FUGEN, SYSTEM_WORDLIST, load_constituents, rss_bytes, wordlist_hash

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

# How often the automaton was really built in this process. Read by the test that
# proves the singleton works; a counter is the only way to tell a cache hit from
# a cheap rebuild from the outside.
_BUILD_COUNT = 0


def build_count() -> int:
    """Return how many German automata this process has built."""
    return _BUILD_COUNT


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
    """Build the English chain: fold, drop stopwords, stem with Porter."""
    return (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())
        .filter(Filter.stopword("english"))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer("english"))
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
    """
    cached = _CACHED_GERMAN.get(digest)
    if cached is not None:
        return cached
    analyzer = german_analyzer(constituents)
    _CACHED_GERMAN.clear()
    _CACHED_GERMAN[digest] = analyzer
    return analyzer


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
