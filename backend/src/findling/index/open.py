"""The one place that opens an index, because opening is registering.

The schema persists the *name* of an analyzer and never the analyzer itself. An
index that is opened without registering those names answers the first
``parse_query`` with ``The tokenizer '"de"' for the field '"body_de"' is
unknown``, which looks like a broken index and is a missing line of setup.
Registration is therefore part of opening, and every other place in this project
that calls ``Index(...)`` or ``Index.open(...)`` is a defect; a test in
``tests/test_index_open.py`` walks the package and says so.

The German automaton costs 0.44 s and roughly 23 MB of resident memory that never
comes back, so this module asks :func:`findling.index.analyzer.cached_german_analyzer`
for it. A second ``open_index`` in the same process therefore reuses the
automaton rather than paying for it twice, which on the 4 GB box this project
targets is the difference between a search service and a memory problem.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Final

import tantivy
from tantivy import Filter, Index, Searcher, TextAnalyzer, TextAnalyzerBuilder, Tokenizer

from findling.config import INDEX_VERSION, SCHEMA_VERSION
from findling.index.analyzer import (
    ANALYZER_VERSION,
    TOKENIZER_DE,
    TOKENIZER_EN,
    TOKENIZER_NAME,
    cached_german_analyzer,
    english_analyzer,
    name_analyzer,
)
from findling.index.schema import TOKENIZER_STORED_ONLY, build_schema
from findling.index.wordlist import wordlist_hash

# Any token of one byte or more is dropped, which is every token there is. See
# stored_only_analyzer below for why that is the wanted behaviour.
_DROP_EVERY_TOKEN: Final = 1

# The banner of the extension module, measured as "tantivy v0.26.0, index_format
# v7". The type stub shipped with tantivy 0.26.0 does not declare the attribute,
# so the read is annotated for pyright rather than replaced by a lookup with a
# default: a fallback value here would turn a renamed attribute into a version
# mark that quietly says the wrong thing.
TANTIVY_VERSION: Final[str] = tantivy.__version__  # pyright: ignore[reportAttributeAccessIssue]


def stored_only_analyzer() -> TextAnalyzer:
    """Return the chain for a field that is stored and never searched.

    tantivy's Python bindings have no unindexed text field: ``index_option``
    accepts basic, freq and position, and nothing else, so every text field is
    indexed. A chain that returns the empty token list is the same thing where it
    matters, and it was measured that way: the value comes back out of the
    document store unchanged, while a query on the field finds nothing, neither
    for a word inside the value nor for the value in full.

    This is what the ``path`` field runs on. Paths are display and diagnosis.
    """
    return TextAnalyzerBuilder(Tokenizer.simple()).filter(Filter.remove_long(_DROP_EVERY_TOKEN)).build()


def open_index(path: Path, constituents: Sequence[str]) -> Index:
    """Create or open the index at ``path`` and register its four analyzers.

    ``constituents`` is the prepared word list from
    :func:`findling.index.wordlist.load_constituents`; it decides how German text
    is split and therefore what the index contains, which is why its digest is
    one of the version marks in :func:`expected_versions`.

    The directory is created when it is missing. It lives inside the container's
    own persistent volume and is never a Nextcloud node; the read-only gate holds
    a reviewed exception for exactly this line.
    """
    path.mkdir(parents=True, exist_ok=True)
    index = Index.open(str(path)) if Index.exists(str(path)) else Index(build_schema(), path=str(path))
    index.register_tokenizer(TOKENIZER_DE, cached_german_analyzer(wordlist_hash(constituents), constituents))
    index.register_tokenizer(TOKENIZER_EN, english_analyzer())
    index.register_tokenizer(TOKENIZER_NAME, name_analyzer())
    index.register_tokenizer(TOKENIZER_STORED_ONLY, stored_only_analyzer())
    return index


def open_reader(index: Index) -> Searcher:
    """Configure the index reader and hand out a first searcher.

    The reload policy is ``commit``: the reader picks up new segments after a
    commit, with a delay. A test that writes and searches in the same breath
    therefore calls ``index.reload()`` and asks for a fresh searcher, otherwise it
    asserts against the state before the commit and is green for the wrong reason.

    Call this once per index, not once per query. Measured on this machine:
    configuring the reader costs 0.10 ms while a whole search costs 0.005 ms, so
    a per query call would spend twenty times the search on the setup for it. A
    searcher is a snapshot; a long lived caller asks ``index.searcher()`` for a
    new one and pays nothing for it.
    """
    index.config_reader(reload_policy="commit")
    return index.searcher()


def expected_versions(digest: str) -> dict[str, str]:
    """Return the version marks an index built by this code must carry.

    The comparison itself lives in :meth:`findling.store.repo.Store.version_mismatch`:
    this module knows what the current code produces, the store knows what the
    existing index was built with, and only the caller that holds both may decide
    what a difference means. A mark that is missing counts as a difference there,
    which is why every value below is a string and none of them is optional.

    ``tantivy_version`` carries the full banner, including the index format, since
    tantivy makes no promise that its on disk format survives its own releases.
    """
    return {
        "schema_version": str(SCHEMA_VERSION),
        "index_version": str(INDEX_VERSION),
        "analyzer_version": str(ANALYZER_VERSION),
        "wordlist_hash": digest,
        "tantivy_version": TANTIVY_VERSION,
    }
