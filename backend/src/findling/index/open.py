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

import hashlib
import logging
from collections.abc import Mapping, Sequence
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
from findling.store.repo import Store

LOGGER = logging.getLogger("findling.index.open")

# The mark that says which set of expected versions a rebuild is aimed at.
#
# It is not a version of anything and never compared against the code; it is a
# fingerprint, and its only job is to tell "a rebuild for exactly this code is
# already under way" from "the code changed again". Without it a container that
# restarts during a rebuild would raise the generation on every start and make
# the work of the previous start stale each time, which on a box that restarts
# often is a rebuild that never ends.
REBUILD_MARK: Final = "rebuild_for"

# The one mark that is never written by the stamp below, spelled out here so
# that the exception is visible next to the function that has to make it.
_LOCAL_GENERATION: Final = "index_version"

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
        _LOCAL_GENERATION: str(INDEX_VERSION),
        "analyzer_version": str(ANALYZER_VERSION),
        "wordlist_hash": digest,
        "tantivy_version": TANTIVY_VERSION,
    }


def _fingerprint(expected: Mapping[str, str]) -> str:
    """One short name for a whole set of expected marks.

    Only equality is ever asked of it, so any stable function of the values will
    do; a hash is used rather than the values themselves so that the mark stays
    one short row whatever a future mark carries.
    """
    material = "\n".join(f"{key}={expected[key]}" for key in sorted(expected))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def start_rebuild_on_drift(store: Store, expected: Mapping[str, str]) -> int | None:
    """Raise the local generation when the index was built by other code.

    Returns the new generation, or None when there is nothing to rebuild.

    **Why raising the generation is the rebuild.** The remedy the reindex banner
    names is ``occ findling:index --restart``, which queues a crawl of every
    mount, and until this plan that crawl did nothing at all: the fast path of
    the poller asks :meth:`findling.store.repo.Store.is_unchanged`, which
    compares the content hash and the generation, and an analyzer drift moves
    neither of them. Every file came back, matched, and was acknowledged without
    a byte being read. Raising the generation makes every stored verdict stale
    at once, so the crawl the admin asked for actually reads the documents again.

    **Why it happens once per drift and not once per start.** The fingerprint of
    the marks being rebuilt towards is written next to the generation. A
    container that restarts in the middle of a two day rebuild finds its own
    fingerprint, leaves the generation alone and carries on; a container whose
    code changed again finds a different one and starts a rebuild for the new
    code. Without that distinction a box that restarts nightly would make the
    work of every day stale on the next morning.

    **What it does not do is declare anything current.** The marks stay as they
    are, so the banner stays up for as long as the work is not through. That is
    :func:`stamp_after_rebuild`'s job and nobody else's.
    """
    if not store.version_mismatch(expected):
        return None

    wanted = _fingerprint(expected)
    if store.read_meta().get(REBUILD_MARK) == wanted:
        return None

    generation = store.index_version + 1
    store.write_meta(_LOCAL_GENERATION, str(generation))
    store.write_meta(REBUILD_MARK, wanted)
    LOGGER.warning(
        "the index was built by different code; raised the generation to %d so the next crawl rebuilds it",
        generation,
    )
    return generation


def stamp_after_rebuild(store: Store, expected: Mapping[str, str]) -> bool:
    """Write the marks of the running code once the rebuild is through.

    Returns True when the marks are current afterwards, which includes the
    ordinary case of an index that never drifted, and False while there is still
    work to do. A caller that polls this may stop the moment it answers True.

    **What "through" means here, exactly.** Not the end of the command and not
    an empty queue: the state in which no living file carries a verdict of an
    earlier generation any more, which is what
    :meth:`findling.store.repo.Store.verdicts_older_than` counts. Every writer
    of a verdict stamps the generation that is running, so a file that ends as
    indexed, skipped or failed under this code leaves the count, and a file that
    was never touched again keeps it above zero.

    **The limit of that definition, named as the plan requires.** It is the
    second best form, because it can only see files this container has heard of.
    A file that was deleted in Nextcloud without a delete job reaching the
    container keeps its old row and holds the count above zero until the nightly
    reconcile turns it into a tombstone, which the count leaves out. So the
    stamp can be a night late on an instance where documents were deleted during
    an update. That is the direction to be late in: a mark written too early
    declares half an index complete and takes away the one banner that told the
    admin why hits are missing (T-05-48).

    **The generation is deliberately not written back.** ``index_version`` in
    the expected marks is the baseline of the code, while the stored one is the
    local generation, and after a rebuild the local one stands above it. The
    store reads that mark as a floor rather than as an equality for exactly this
    reason. Writing the baseline back would make every row of the rebuild that
    just finished look stale and start the whole thing over.

    **This is not the seed and must never move into it.** ``_seed_meta`` fills
    in a mark that is missing and touches nothing that is there, because an
    existing database has to keep the marks its index was really built with.
    This function is the opposite operation and therefore a separate one.
    """
    stored = store.read_meta()
    if not store.version_mismatch(expected) and not stored.get(REBUILD_MARK):
        # Nothing drifted and nothing is being rebuilt, so there is nothing to
        # write. Said here rather than at the call site because a caller that
        # had to know this would be a second place deciding what a current index
        # looks like, and it saves the count below on every ordinary instance.
        return True

    generation = store.index_version
    remaining = store.verdicts_older_than(generation)
    if remaining > 0:
        return False

    for key, value in expected.items():
        if key == _LOCAL_GENERATION:
            continue
        store.write_meta(key, value)
    store.write_meta(REBUILD_MARK, "")
    LOGGER.info("the rebuild is through at generation %d; the version marks are current again", generation)
    return True
