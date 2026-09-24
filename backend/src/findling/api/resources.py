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
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from tantivy import Index

from findling.config import settings
from findling.embed.engine import shared_model
from findling.embed.model import EmbeddingModel
from findling.index.open import expected_versions, open_index, open_reader
from findling.index.schema import BODY_FIELD
from findling.index.wordlist import build_artifact
from findling.store.repo import EMBEDDING_MARK, VECTOR_ONLY_MARKS, Store, open_read_only
from findling.store.vectors import EMBEDDING_MODEL, VectorStore, embedding_mark, open_vectors

LOGGER = logging.getLogger("findling.api.resources")

# The mark that stands for "we cannot show that the index agrees with the query
# parser". Reported like a real difference, because an unprovable match is worth
# exactly as much as a proven mismatch (pitfall 14).
UNPROVEN_WORDLIST = "wordlist_hash"

# The full value of the embedding mark is model, quantisation, dimensions and
# token cap. Three of the four come from findling.store.vectors, which owns
# them, and the token cap comes from the settings. A change to any of the four
# makes a stored vector incomparable with a freshly computed query vector, and
# the mark is what turns that into a visible drift instead of into quietly worse
# results.
#
# The cap is read rather than written out, which it used to be, so that an
# operator who raises it sees the drift the raise really causes instead of a
# mark that keeps claiming 1024.
#
# EMBEDDING_MODEL was a constant of this module until plan 06.1-10 and moved to
# findling.store.vectors when the poller became the second place that composes
# the mark. It is imported rather than spelled again, because two spellings of
# one model name is exactly the drift this mark exists to make visible.

# How long a degraded verdict stays valid before it is measured again.
#
# Five seconds, and the number is a trade between two costs that are both real.
# Measured for phase 2: a search costs 0.005 ms, while the verdict behind it is a
# meta read plus a disk_usage call on the volume. Paying that on every keystroke
# of a unified search is the expensive half. The other half is that a state which
# turns bad has to become visible without a restart, and five seconds is shorter
# than any admin page poll and shorter than the patience of somebody who just
# filled a volume. Above roughly a minute the flag would stop being an operating
# signal and become a stale value; below a second it stops saving anything.
DEGRADED_TTL_SECONDS: Final = 5.0

# How long the fill level of the body chains stays valid before it is measured
# again.
#
# Thirty seconds, and the number is not the five above because the measurement
# behind it is a different size and the question behind it changes at a
# different speed. ``terms_with_prefix`` with an empty prefix walks the whole
# term dictionary of a field by its own documentation, and the limit cuts only
# afterwards; six chains means six such walks. What it answers is which chains
# carry terms at all, and that is a property of an index directory: it changes
# when a rebuild swaps a directory in, which this module is told about through
# reset_read_side(), and otherwise only while the very first documents of a new
# chain are being written. So the window is generous on purpose, and the one
# event that would make it stale invalidates it directly rather than waiting.
FILLED_TTL_SECONDS: Final = 30.0


@dataclass(frozen=True, slots=True)
class ReadSide:
    """The handles a search needs, plus the path they were opened from."""

    index: Index
    store: Store
    index_dir: Path
    # The vector stock, and it may be None while the other two are open. That is
    # the whole statement of this field and it is criterion 3 of phase 6: a
    # missing, empty or unopenable vectors.db must not make read_side() answer
    # None, because a broken vector stock would then switch the full text search
    # off with it. So the open below sits in a try of its own, its failure sets
    # this to None and writes one log line with a type name, and the search
    # answers the unchanged lexical ranking (D-19, T-06-29).
    vectors: VectorStore | None = None


_OPEN: ReadSide | None = None
_MARKS: tuple[Path, dict[str, str]] | None = None
_DEGRADED: tuple[Path, float, bool] | None = None
_FILLED: tuple[Path, float, tuple[str, ...]] | None = None

# One lock for the four caches above, and it is not a precaution.
#
# Every search runs its round in asyncio.to_thread and the unified search asks
# all providers at the same moment, so two requests really do arrive in here at
# once. Without the lock both threads see an empty cache, both open an index and
# a state database, and the one that loses the assignment leaves a SQLite
# connection that nothing holds a reference to any more: it is closed whenever
# the garbage collector gets round to it, and until then it is a file handle and
# a WAL reader on a 4 GB box (audit M7, phase 4 finding IN-06).
#
# Re-entrant, because degraded() computes its verdict inside the lock and
# version_drift() below it asks expected_marks(), which takes the same lock. A
# plain Lock would deadlock the first search of every container.
_LOCK = threading.RLock()


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
    with _LOCK:
        if _MARKS is not None and _MARKS[0] == dictionary:
            return dict(_MARKS[1])
        try:
            marks = expected_versions(build_artifact().digest, ",".join(settings().languages))
        except OSError:
            LOGGER.warning("the constituent list is unavailable, version marks cannot be compared")
            return None
        # The one mark that does not come from the index side. It is added here
        # and not in expected_versions() on purpose: that function feeds
        # start_rebuild_on_drift, which answers a difference by raising the index
        # generation, and a vector stock that no longer matches the model must
        # not be able to trigger a rebuild of the full text index (D-21).
        marks[EMBEDDING_MARK] = embedding_mark(EMBEDDING_MODEL, tokens=settings().embed_token_cap)
        _MARKS = (dictionary, marks)
        return dict(marks)


def version_drift(store: Store) -> list[str]:
    """Names of the marks the existing index disagrees with, empty when it agrees.

    This is the counter-measure to the quietest failure of a search app: an image
    update brings a different word list or a different tantivy release, queries
    are tokenised differently than the documents were, and hits disappear with
    nothing anywhere saying why.

    The question is about the **index**, which is why the vector marks are left
    out of the answer. This list reaches the status page as
    ``reindexRequired``, and the remedy behind that flag is a rebuild of the full
    text stock that costs hours on the box this project targets. A vector stock
    computed by an older model is a real difference and a different remedy: the
    vectors are recomputed, the index is not touched (D-21). Store.version_mismatch
    reports both, and this is the caller that decides what a difference means.
    """
    marks = expected_marks()
    if marks is None:
        return [UNPROVEN_WORDLIST]
    return [mark for mark in store.version_mismatch(marks) if mark not in VECTOR_ONLY_MARKS]


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


def _read_only_vectors(path: Path) -> VectorStore | None:
    """Open the vector stock for reading, or answer None and say so once.

    Its own function because it needs its own try, and the try is the point. A
    vectors.db that is absent, that is not a database, or that lies on a box
    where the vec0 extension refuses to load, are three different findings and
    one outcome for the search: no vector list, the merge becomes the identity
    on the lexical ranking, and the user gets full text results instead of
    nothing (D-19).

    ``read_only=True`` refuses a missing file rather than creating an empty one,
    which is what keeps "the vector stock is gone" apart from "nothing similar
    exists". Every failure ends here, and the log line carries the type name and
    nothing else: a path is a file name and a library message quotes what it was
    reading.
    """
    try:
        return open_vectors(path, read_only=True)
    # Deliberately every exception. The three findings above raise three
    # different types, and a fourth one must not reach the caller either.
    except Exception as error:
        LOGGER.warning("the vector stock could not be opened, an %s, the search stays lexical", type(error).__name__)
        return None


def query_model() -> EmbeddingModel:
    """The embedding engine of this process, which the read side shares.

    A pass through and no longer a cache of its own. It used to hold one keyed
    on the model directory, exactly like the handles above, and the second track
    of the poller held another, so a container that indexes and searches, which
    is every installation, carried two tokenizers and two onnxruntime sessions:
    276 MB that stayed resident after the first semantic search, measured on
    2026-09-05 against 210 MB of headroom.

    The holder moved to :mod:`findling.embed.engine` rather than staying here,
    with the reasoning at that module. The short version is the dependency
    direction: this is the reading half of the container, and the worker must
    not import from the API to get an engine. Two halves that draw from one
    holder need it to belong to neither of them.
    """
    return shared_model()


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
    with _LOCK:
        if _OPEN is not None and _OPEN.index_dir == resolved.index_dir:
            return _OPEN

        # The cached handle belongs to a directory that is no longer the one the
        # settings name, so it is released here and not further down. It used to
        # be released after the two checks below, which meant the branch for a
        # volume that has nothing yet walked straight past it: the connection
        # then lived on with nothing referring to it, for as long as the process
        # did.
        previous, _OPEN = _OPEN, None
        if previous is not None:
            previous.store.close()
            if previous.vectors is not None:
                previous.vectors.close()

        if not resolved.state_db.is_file() or not resolved.index_dir.is_dir():
            # Nothing to open yet, which is an ordinary state: the container is
            # deployed and the first indexing pass has not finished. Asking again
            # on the next request costs two stat calls.
            #
            # The directory is asked about before Index.exists and not by it,
            # and that is a fix of plan 18-10 rather than a tidy up. Measured on
            # 2026-09-24: ``Index.exists`` raises ValueError("Directory does not
            # exist") for a path that is not there, it does not answer False,
            # and this branch is the one a container with a state database and
            # no index directory takes. Until this line the second half of the
            # condition therefore raised out of a function whose whole contract
            # is that it never does, and the try below starts one statement too
            # late to catch it.
            return None
        if not Index.exists(str(resolved.index_dir)):
            # The directory is there and holds no index, which is what a volume
            # looks like between the creation of the directory and the first
            # commit. Kept apart from the branch above only in order to ask the
            # question of a path that exists.
            return None

        # Held in a local until the cache owns it. Between the open and the
        # assignment there is a step that can fail, and a connection that failed
        # to reach the cache has to be closed by whoever opened it; nobody else
        # can reach it any more. The vector handle follows the same discipline,
        # because it is cached under the same key and released by the same
        # branch above.
        store: Store | None = None
        vectors: VectorStore | None = None
        try:
            index = open_index(resolved.index_dir, build_artifact().entries)
            # Once per index, not once per query: configuring the reader costs
            # 0.10 ms while a whole search costs 0.005 ms. The searcher it returns
            # is a snapshot and deliberately not kept; the reload policy is what
            # makes a later commit of the poller visible to this process at all.
            open_reader(index)
            store = open_read_only(resolved.state_db)
            # After the two that matter, and outside their fate. Whatever this
            # answers, the read side is opened.
            vectors = _read_only_vectors(resolved.vectors_db)
            _OPEN = ReadSide(index=index, store=store, index_dir=resolved.index_dir, vectors=vectors)
            store = None
            vectors = None
        # Deliberately every exception, for the reason in the docstring above.
        except Exception as error:
            # The type name and nothing else. A traceback here would carry
            # whatever a library put into its message, and a path is the usual
            # content.
            LOGGER.warning("the read side could not be opened, an unexpected %s", type(error).__name__)
            return None
        finally:
            if store is not None:
                store.close()
            if vectors is not None:
                vectors.close()
        return _OPEN


def reset_read_side() -> None:
    """Let go of the three process caches, so that the next search opens again.

    **Who calls this, and when.** The rebuild of
    :mod:`findling.index.rebuild`, once, immediately in front of the first
    rename of the directory swap. Nothing else. It is not a general purpose
    cache reset and it is not a recovery step for a damaged index: a container
    whose index is broken is answered by :func:`read_side` returning None, and
    calling this in a loop would merely reopen the same broken directory.

    **The one difference to the release branch inside read_side, and the whole
    reason this function exists.** That branch releases a handle whose
    ``index_dir`` no longer matches the settings, and it therefore cannot see
    the swap at all: the rebuilt directory is renamed to the very name the live
    one had, so the path is the same before and after and the comparison is
    True. On Linux the rename succeeds with open mmaps as well, because POSIX
    renames over inodes, and the cached handle would then answer out of a
    directory that no longer has a name, silently and for as long as the process
    lives (pitfall 3 of the phase research). This function therefore checks no
    path; it drops what is there.

    ``_MARKS``, ``_DEGRADED`` and ``_FILLED`` go with it, under the same lock
    and for the same reason. All three describe the index directory rather than
    the handle on it, all three outlive a rename, and all three would afterwards
    make a statement about a directory that is gone: the marks are exactly the
    answer a rebuild changes, a degraded verdict that stayed would report the
    state of the retired directory for the rest of
    :data:`DEGRADED_TTL_SECONDS`, and the fill level is the one reading a
    rebuild exists to move, so keeping it would have the admin page report the
    old chains for half a minute after the run that filled the new ones.

    Idempotent. A second call and a call on a container whose first indexing
    pass never finished both find nothing and do nothing.
    """
    global _OPEN, _MARKS, _DEGRADED, _FILLED
    with _LOCK:
        # Taken into a local before the cache is emptied, exactly as the release
        # branch above does it: a handle that is closed while it is still
        # reachable is a handle a search can be holding halfway through.
        previous, _OPEN = _OPEN, None
        _MARKS = None
        _DEGRADED = None
        _FILLED = None
        if previous is not None:
            previous.store.close()
            if previous.vectors is not None:
                previous.vectors.close()


def degraded(side: ReadSide | None) -> bool:
    """True when this container is answering, but not from a complete index.

    Four causes, one flag: there is no index yet, the index was built by a
    different tokenisation, the volume is too full for the indexer to commit, or
    embedding is switched on and there is no vector stock to answer with. The
    PHP side gets one boolean out of it so that it can stay quiet instead of
    guessing, and phase 4 builds the status page out of the same answers.

    The fourth cause is the one phase 6 added, and it is a statement about
    completeness rather than about a fault. A container whose second track has
    not run yet answers lexically and answers correctly; it just does not answer
    with everything it promises, and that is exactly what this flag is for. It
    is asked only while ``embed_enabled`` is on, because an instance that
    switched the second track off is not missing anything.

    The verdict is remembered for :data:`DEGRADED_TTL_SECONDS`, which is five
    seconds, and that number belongs in this docstring because it decides how
    fast a search starts calling itself degraded. Behind the flag sit a meta read
    and a disk_usage call on the volume, and a unified search asks per keystroke;
    without the window the two measurements were the most expensive part of an
    answer that otherwise costs 0.005 ms. Within the window a volume that just
    filled up is reported late by at most those five seconds, and an index that
    was never built is not affected at all: no read side means degraded, and that
    branch is answered without measuring anything.
    """
    if side is None:
        return True

    global _DEGRADED
    now = time.monotonic()
    with _LOCK:
        cached = _DEGRADED
        if cached is not None and cached[0] == side.index_dir and now - cached[1] < DEGRADED_TTL_SECONDS:
            return cached[2]
        missing_vectors = side.vectors is None and settings().embed_enabled
        verdict = missing_vectors or bool(version_drift(side.store)) or low_disk()
        _DEGRADED = (side.index_dir, now, verdict)
        return verdict


def filled_languages() -> tuple[str, ...]:
    """The language codes whose body chain really carries terms, in schema order.

    The other half of the language diagnosis of the admin page, and the only
    half that comes out of the index itself. The stored ``languages`` mark says
    which chains the directory was built under, which is a statement about an
    intention; this says which of them a search can actually hit. The two differ
    for as long as a rebuild runs and they differ for good when a chain was
    switched on and no document was written since, and neither of those is
    visible in a single list.

    Measured with ``terms_with_prefix(field, "", limit=1)``, which answers an
    empty list for a chain whose term dictionary is empty and one entry
    otherwise. That is the whole probe: not how many terms there are, only
    whether there is one.

    **Why the reading is cached, and why the window is its own.** The probe
    walks the entire term dictionary of a field by tantivy's own documentation
    and the limit cuts only afterwards, six chains means six such walks, and the
    administration page polls every few seconds while it is open. So the answer
    is remembered for :data:`FILLED_TTL_SECONDS` under the directory it was
    measured in, in the shape :func:`degraded` above uses and under the same
    lock. The one event that really changes it, the directory swap of a rebuild,
    clears the cache through :func:`reset_read_side` instead of waiting the
    window out.

    Answers an empty tuple for a container that has no index yet and for one
    whose index cannot be read: both are states in which no chain carries
    anything this container can offer, and neither is a reason to fail an
    administration page.
    """
    side = read_side()
    if side is None:
        return ()

    global _FILLED
    now = time.monotonic()
    with _LOCK:
        cached = _FILLED
        if cached is not None and cached[0] == side.index_dir and now - cached[1] < FILLED_TTL_SECONDS:
            return cached[2]
        try:
            searcher = side.index.searcher()
            filled = tuple(code for code, field in BODY_FIELD.items() if searcher.terms_with_prefix(field, "", limit=1))
        # Deliberately every exception, for the reason read_side() states: this
        # value reaches an administration page, and a page that answers 500
        # because one of its lines could not be measured tells an admin less
        # than a page that leaves that line empty. A directory of the old schema
        # has no chain beyond the first two at all, and asking it for one is the
        # realistic shape of this failure.
        except Exception as error:
            LOGGER.warning("the fill level of the body chains could not be read, an %s", type(error).__name__)
            return ()
        _FILLED = (side.index_dir, now, filled)
        return filled


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
