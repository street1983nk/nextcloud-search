"""The reading half of the container: one index, one read-only store, opened once.

The three endpoints need the same two handles, and both are expensive to open in
different ways. The index registers four analyzer chains, one of which builds a
23 MB automaton out of the constituent list, and configuring the reader costs
twenty times what a search costs. The state database is opened with
``query_only``, which is the structural half of the read/write split: a defect in
the search path cannot change the operating state, whatever it tries.

Two decisions about the caching are worth stating, because both are the answer to
a failure that is invisible from the outside.

*Absence is never cached.* A container is deployed before it has indexed
anything, so the first searches legitimately find neither an index nor a state
database. Caching that "no" would mean the process keeps answering "nothing
found" for as long as it runs, while the poller quietly fills a volume nobody
reads. Only a successful open is kept.

*What is cached is keyed by the path it was opened from.* One process only ever
has one volume, so in production the key never changes. In a test suite it
changes with every temporary directory, and without the key the second test would
search the index of the first one and be green for the wrong reason.

Nothing here decides anything. Whether a version drift means a reindex, and
whether a degraded answer should be shown or hidden, is decided by the callers;
this module reports.
"""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from tantivy import Index

from findling.config import settings
from findling.index.open import expected_versions, open_index, open_reader
from findling.index.wordlist import build_artifact
from findling.store.repo import Store, open_read_only

LOGGER = logging.getLogger("findling.api.resources")

# The mark that stands for "we cannot show that the index agrees with the query
# parser". Reported like a real difference, because an unprovable match is worth
# exactly as much as a proven mismatch (pitfall 14).
UNPROVEN_WORDLIST = "wordlist_hash"


@dataclass(frozen=True, slots=True)
class ReadSide:
    """The two handles a search needs, plus the path they were opened from."""

    index: Index
    store: Store
    index_dir: Path


_OPEN: ReadSide | None = None
_MARKS: tuple[Path, dict[str, str]] | None = None


def expected_marks() -> dict[str, str] | None:
    """The version marks an index built by this code carries, or None.

    None means the constituent list could not be read at all, which is a
    container that cannot index either. A copy is handed out rather than the
    cached mapping itself: a caller that edited it would silently move the
    comparison this whole mechanism exists for.

    Cached under the directory the list was read from, for the same reason the
    handles below are: one process has one volume, but a suite has one per test,
    and a digest carried over from the previous volume would report a drift that
    does not exist.
    """
    global _MARKS
    dictionary = settings().dict_dir
    if _MARKS is not None and _MARKS[0] == dictionary:
        return dict(_MARKS[1])
    try:
        marks = expected_versions(build_artifact().digest)
    except OSError:
        LOGGER.warning("the constituent list is unavailable, version marks cannot be compared")
        return None
    _MARKS = (dictionary, marks)
    return dict(marks)


def version_drift(store: Store) -> list[str]:
    """Names of the marks the existing index disagrees with, empty when it agrees.

    This is the counter-measure to the quietest failure of a search app: an image
    update brings a different word list or a different tantivy release, queries
    are tokenised differently than the documents were, and hits disappear with
    nothing anywhere saying why.
    """
    marks = expected_marks()
    if marks is None:
        return [UNPROVEN_WORDLIST]
    return store.version_mismatch(marks)


def _existing_directory(path: Path) -> Path | None:
    """The path itself or its nearest existing ancestor, None when there is none."""
    for candidate in (path, *path.parents):
        if candidate.is_dir():
            return candidate
    return None


def low_disk() -> bool:
    """True when the volume has less free space than a commit needs.

    Asked on the reading side because the indexer pauses in that situation, so
    the index stops growing while searches keep answering. The user has to be
    told that the answer is incomplete; they cannot be told why by a page that
    does not know.
    """
    directory = _existing_directory(settings().index_dir)
    if directory is None:
        return False
    try:
        return shutil.disk_usage(directory).free < settings().min_free_bytes
    except OSError:
        # Not measurable is not the same as low, and a container whose volume
        # cannot be stated is going to fail louder elsewhere.
        LOGGER.warning("free space of the volume could not be read")
        return False


def disk_bytes() -> tuple[int, int]:
    """Free and total bytes of the volume, both 0 when it cannot be measured.

    The measurement next to the verdict of :func:`low_disk` above, and kept
    apart from it on purpose. The flag carries a threshold this container
    decided; these two carry what the file system said, and the admin page needs
    them raw because a space requirement is a division and a boolean cannot be
    divided.

    ``low_disk`` deliberately keeps its own call. Deriving the flag from these
    numbers would move its behaviour, and a value that is reported and a value
    that pauses the indexer are worth being able to change apart.
    """
    directory = _existing_directory(settings().index_dir)
    if directory is None:
        return (0, 0)
    try:
        usage = shutil.disk_usage(directory)
    except OSError:
        # Same rule as low_disk above: not measurable is not the same as full,
        # and the log line names neither the path nor the volume.
        LOGGER.warning("the size of the volume could not be read")
        return (0, 0)
    return (usage.free, usage.total)


def read_side() -> ReadSide | None:
    """The index and the state database of this container, None while either is absent.

    Never raises. A damaged index, an unreadable word list and a state database
    that disappeared under the process all end in None, because the unified
    search calls every provider in parallel: a provider that raises costs the
    user the whole search, and a provider that answers empty costs one result
    group.
    """
    global _OPEN
    resolved = settings()
    if _OPEN is not None and _OPEN.index_dir == resolved.index_dir:
        return _OPEN

    if not resolved.state_db.is_file() or not Index.exists(str(resolved.index_dir)):
        # Nothing to open yet, which is an ordinary state: the container is
        # deployed and the first indexing pass has not finished. Asking again on
        # the next request costs two stat calls.
        return None

    previous, _OPEN = _OPEN, None
    if previous is not None:
        previous.store.close()

    try:
        index = open_index(resolved.index_dir, build_artifact().entries)
        # Once per index, not once per query: configuring the reader costs
        # 0.10 ms while a whole search costs 0.005 ms. The searcher it returns is
        # a snapshot and deliberately not kept; the reload policy is what makes
        # a later commit of the poller visible to this process at all.
        open_reader(index)
        _OPEN = ReadSide(index=index, store=open_read_only(resolved.state_db), index_dir=resolved.index_dir)
    # Deliberately every exception, for the reason in the docstring above.
    except Exception as error:
        # The type name and nothing else. A traceback here would carry whatever
        # a library put into its message, and a path is the usual content.
        LOGGER.warning("the read side could not be opened, an unexpected %s", type(error).__name__)
        return None
    return _OPEN


def degraded(side: ReadSide | None) -> bool:
    """True when this container is answering, but not from a complete index.

    Three causes, one flag: there is no index yet, the index was built by a
    different tokenisation, or the volume is too full for the indexer to commit.
    The PHP side gets one boolean out of it so that it can stay quiet instead of
    guessing, and phase 4 builds the status page out of the same three answers.
    """
    if side is None:
        return True
    return bool(version_drift(side.store)) or low_disk()


def report_version_drift() -> None:
    """Log a version drift once at startup, and decide nothing about it.

    What follows from a drift is the poller's business: resetting one storage and
    throwing the whole index away are both defensible and neither is a decision a
    read path gets to make. What is not defensible is a drift nobody ever hears
    about.
    """
    resolved = settings()
    if not resolved.state_db.is_file():
        return
    try:
        store = open_read_only(resolved.state_db)
    except OSError as error:
        LOGGER.warning("the state database could not be read at startup, an %s", type(error).__name__)
        return
    try:
        drift = version_drift(store)
    finally:
        store.close()
    if drift:
        LOGGER.warning(
            "the index was built with different versions than this build produces, a reindex is required: %s",
            ", ".join(sorted(drift)),
        )
