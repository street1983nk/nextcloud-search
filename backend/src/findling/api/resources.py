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
import sqlite3
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from tantivy import Index

from findling.config import SCHEMA_VERSION, settings
from findling.embed.engine import shared_model
from findling.embed.model import EmbeddingModel
from findling.index.open import LANGUAGES_MARK, SCHEMA_MARK, expected_versions, open_index, open_reader
from findling.index.schema import BODY_FIELD, FIELD_NAME, FIELD_TITLE
from findling.index.wordlist import build_artifact
from findling.index.wordlist_nl import dutch_digest_for, dutch_mark
from findling.query.rewrite import BODY_BOOST, EMPTY_PLAN, LEGACY_PLAN, NAME_BOOST, TITLE_BOOST, FieldPlan
from findling.store.repo import EMBEDDING_MARK, LEGACY_LANGUAGES, VECTOR_ONLY_MARKS, Store, open_read_only
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
    # Which generation of the reading side these handles belong to, and the
    # whole reason the field exists is audit finding M-18-02.
    #
    # The two measurements below, degraded() and filled_languages(), take the
    # side OUTSIDE the lock and write their cache entry INSIDE it. A
    # reset_read_side() that lands between the two used to leave the later
    # writer filling the cache it had just emptied, with a reading taken from
    # the directory that was retired a moment ago. The path key cannot catch
    # that, because the swap puts the rebuilt directory under the very name the
    # live one had, so the key matches and the entry looks current: the admin
    # page then reported the state from before the rebuild for up to thirty
    # seconds, which is exactly the moment those two lines were written for.
    #
    # A number next to the caches answers it. It moves on every reset, the
    # handles carry the number they were opened under, and a writer whose side
    # is of an older generation hands its verdict out and keeps it out of the
    # cache.
    generation: int = 0
    # What a bare word searches on the directory behind these handles, computed
    # once from its two stored marks by field_plan_for below. It is not the wish
    # of this container and it is not derived from the settings: an index answers
    # the fields it was built with, whatever the environment currently asks for.
    #
    # It hangs here rather than in a cache of its own, and that is the whole
    # point of the field. The invalidation a separate cache would have to build
    # exists here already: reset_read_side() drops the handles in front of the
    # directory swap, and ReadSide.generation is the guard that audit finding
    # M-18-02 cost. A third cache beside _DEGRADED and _FILLED would be a third
    # place to get that race wrong, for a value that changes exactly when these
    # handles do. The plan needs no generation branch of its own either, because
    # it is computed inside _LOCK together with the handles it describes rather
    # than measured outside it afterwards.
    #
    # The default is the legacy plan and never a computed one, the same fail
    # closed line build_query draws for its own parameter: a side assembled
    # without a plan searches the four fields every release up to 1.2.0 searched,
    # which every index of both generations answers.
    field_plan: FieldPlan = LEGACY_PLAN
    # Whether that plan reaches fewer fields than the stored marks promise, which
    # is the one state the two language values of the admin page cannot show
    # (audit finding M-19-03). Both of them would go on saying "six chains are
    # switched on and filled" while a question reaches two, because one is read
    # out of the marks and the other out of the term dictionary, and neither is
    # read out of the plan. It is measured here, beside the plan and out of the
    # same marks, because that is the one moment both are in hand; degraded()
    # reads it without measuring anything.
    plan_is_short: bool = False


_OPEN: ReadSide | None = None
_MARKS: tuple[Path, dict[str, str]] | None = None
_DEGRADED: tuple[Path, float, bool] | None = None
_FILLED: tuple[Path, float, tuple[str, ...]] | None = None

# How often the reading side has been let go in this process. Read the reasoning
# at ReadSide.generation; what matters here is only that it never goes backwards
# and that it moves under the same lock as the caches it guards.
_GENERATION: int = 0

# Whether a directory swap is happening right now, in which case there is no
# reading side at all.
#
# Audit finding M-18-03. Between drop_read_side() and swap_in() stood two
# ordinary statements without a common lock, and a search that arrived in that
# window did the one thing the whole reset exists to prevent: it found the cache
# empty, opened the live directory and put the handle back. A moment later that
# directory was renamed and removed, and on Linux both calls succeed, so the
# cached handle went on answering every search out of a directory that has no
# name, silently and until the container was restarted. That is pitfall 3 of the
# phase research, and reset_read_side alone could not close it, because the
# emptying and the rename are two separate moments.
#
# The bar is raised by hold_the_read_side_shut() and lowered by
# let_the_read_side_open(). While it is up read_side() answers None, which the
# whole reading half already handles as "this container has no index yet": a
# search answers empty. That lasts two rename system calls, and answering empty
# for the length of two system calls is the documented state of that window
# anyway.
_SWAPPING: bool = False

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
            languages = settings().languages
            marks = expected_versions(build_artifact().digest, ",".join(languages), dutch_mark=dutch_mark(languages))
        # A missing Dutch artifact under a language set with nl lands here as
        # well, since FileNotFoundError is an OSError: no comparison rather than
        # a reading side that fails (T-21-06-04).
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


def _of_the_marks(marks: Mapping[str, str]) -> FieldPlan | None:
    """The plan the two stored marks describe, None when they give no permission.

    The two gates of :func:`field_plan_for` in one place, so that what follows
    them reads as the cascade it is. Both of them answer None rather than a plan
    of their own: a gate that picked the fallback itself would be a second place
    deciding what the fallback is, and the caller is the one place that probes
    it.

    The reasoning of both gates is in the docstring of the caller. In short: a
    schema mark that is not literally the current one is no permission, and a
    language mark that names no code this schema knows leaves nothing to search
    in.
    """
    if marks.get(SCHEMA_MARK) != str(SCHEMA_VERSION):
        return None

    stored = marks.get(LANGUAGES_MARK, "")
    # Stripped and lowered, audit finding L-19-01. The write side cannot produce
    # "de, en" or "DE,EN" today, because config._languages iterates over
    # SUPPORTED_LANGUAGES, but this reads a file that can come out of a backup,
    # out of an older release or out of a hand. Unstripped, "de, en" loses a
    # whole language without a word anywhere; unlowered, "DE,EN" keeps nothing
    # at all and falls back. Every other unsharpness of this mark is treated
    # tolerantly here, and these two are the cheapest of them.
    active = {code.strip().lower() for code in stored.split(",") if code.strip()} or set(LEGACY_LANGUAGES)
    # Iterated over BODY_FIELD and never over the mark, because that mapping
    # IS the schema field order and because a code nobody knows has no field
    # to contribute. body_de gets no exception of any kind: it is written
    # unconditionally, but an instance that switched German off did not mean
    # a question against the German chain (19-RESEARCH pitfall 7).
    bodies = tuple(BODY_FIELD[code] for code in BODY_FIELD if code in active)
    if not bodies:
        return None

    boosts = {BODY_FIELD[code]: BODY_BOOST[code] for code in BODY_FIELD if code in active}
    boosts[FIELD_NAME] = NAME_BOOST
    boosts[FIELD_TITLE] = TITLE_BOOST
    # Behind a read only view like the frozen plan next door, and for the reason
    # written there (L-19-02): the dict above is finished at this line and a plan
    # that can be edited from anywhere is not a plan.
    return FieldPlan(
        fields=(*bodies, FIELD_NAME, FIELD_TITLE),
        boosts=MappingProxyType(boosts),
        title_only=(FIELD_NAME,),
    )


def _probed(plan: FieldPlan, index: Index) -> FieldPlan | None:
    """The plan without the names this directory does not carry, None when nothing is left.

    Audit finding M-19-01. The probe used to run over the body fields of the
    computed plan alone and answered one field that raised with the whole legacy
    plan, which left two holes in a gate that is otherwise closed: ``name`` and
    ``title`` went out unprobed although they travel in the same two parameters
    and raise in the same way, and the plan that was fallen back to had never
    been held against the directory at all. A fallback nobody probed is the one
    plan that is guaranteed to raise on the day one of those four names moves,
    and a gate with an unprobed back side is not a gate.

    So every name that reaches the parser is asked for here, out of both halves
    of the value and out of the file name answer as well, and what cannot be
    asked for is left out instead of taking the rest of the plan with it. A plan
    of four fields costs four ``doc_freq(field, "")`` calls at 0.26 us each
    (19-RESEARCH measurement M-2), a plan of six languages costs eight, and all
    of them are paid once per opening of the reading side rather than once per
    keystroke.

    One warning per dropped name, with the field name and the type of the
    exception in it and nothing else: no path, no search term, and no search term
    reaches this function in the first place. It is a warning and not the debug
    line of :func:`filled_languages`, because a name the marks promise and the
    directory does not carry means the two halves of a volume do not belong
    together.

    None and not an empty plan, so that the caller can tell "this plan kept
    nothing" from "this plan is the answer" in one branch. The empty plan is what
    it decides on afterwards, and :func:`findling.query.rewrite.build_query`
    turns that one into an empty answer rather than into a raising parser call.
    """
    searcher = index.searcher()
    kept: list[str] = []
    # Asked once per name and not once per mention. Every name of a plan stands
    # in at least two of the three halves, so a set of what has been asked is
    # what keeps one missing field to one log line instead of two.
    asked: set[str] = set()
    for field in (*plan.fields, *plan.boosts, *plan.title_only):
        if field in asked:
            continue
        asked.add(field)
        try:
            searcher.doc_freq(field, "")
        # Deliberately every exception: the measured one is a ValueError out of
        # tantivy, and a directory that answers a lookup with something else is
        # no better a place to search in.
        except Exception as error:
            LOGGER.warning(
                "the field %s is not in the directory the marks describe, an %s, it is left out of the search",
                field,
                type(error).__name__,
            )
            continue
        kept.append(field)
    fields = tuple(name for name in plan.fields if name in kept)
    if not fields:
        return None
    return FieldPlan(
        fields=fields,
        boosts=MappingProxyType({name: weight for name, weight in plan.boosts.items() if name in kept}),
        title_only=tuple(name for name in plan.title_only if name in kept),
    )


def plan_falls_short(marks: Mapping[str, str], plan: FieldPlan) -> bool:
    """True when this plan reaches fewer fields than these marks promise.

    Audit finding M-19-03, and the value it answers is the one the admin page
    was missing. ``languagesActive`` comes out of the marks and
    ``languagesFilled`` out of the term dictionary, so both of them go on saying
    six while a question reaches two: the fallback happens between them, in the
    plan, and nothing read the plan.

    Inclusion and not equality, because a plan that reaches MORE than the marks
    promise is not a thing this code can produce: every candidate is built out of
    the marks or is the frozen legacy plan, and the probe only ever takes names
    away. Asking for inclusion means a later candidate cannot make this answer
    wrong by being wider.

    Never raises, like everything on this path. A promise that cannot be read at
    all is the fault :func:`field_plan_for` has just written its error line
    about, and a container whose own field list could not be computed is not one
    to call complete.
    """
    try:
        promised = _of_the_marks(marks) or LEGACY_PLAN
    # Deliberately every exception, for the reason in the docstring above.
    except Exception:
        return True
    return not set(promised.fields) <= set(plan.fields)


def searched_languages() -> tuple[str, ...]:
    """The language codes a bare word really reaches, in schema order.

    The third language value of the admin page and the only one that comes out
    of the field plan. ``languagesActive`` is what the marks promise and
    ``languagesFilled`` is what the term dictionary carries; this is what a
    question touches, and until audit finding M-19-03 it was the one of the three
    that nothing reported, although it is the only one a search actually obeys.

    Costs nothing beyond the open: the plan is an attribute of the reading side,
    computed once when the handles were built. An empty answer means there is no
    reading side at all, which is the same shape :func:`filled_languages` uses
    for the same state.
    """
    side = read_side()
    if side is None:
        return ()
    return tuple(code for code, field in BODY_FIELD.items() if field in side.field_plan.fields)


def field_plan_for(marks: Mapping[str, str], index: Index) -> FieldPlan:
    """What a bare word searches on this directory, read out of its two marks.

    The fachliche core of phase 19 and at the same time its safety gate. Up to
    1.2.0 the answer was three module constants; from here it is a function of
    what the directory on disk says about itself, which is the only source that
    can be right about it.

    **The two marks and nothing else.** ``schema_version`` says which layout the
    directory was built under and ``languages`` says which body chains were
    written into it. Both are written by the rebuild, after the work that makes
    them true is through. The language set of :func:`findling.config.settings` is deliberately not
    consulted:
    that is the wish of the container that happens to be running, the index
    answers with what it was built with, and confusing the two is threat
    T-18-05-01 of phase 18, the one that made the seed of
    :mod:`findling.store.repo` skip the language key by name.

    **The gate falls closed**, in the shape of
    :func:`findling.store.repo._schema_is_legacy` and for its reason. Anything
    that is not literally the current mark, which covers an absent mark, the
    intermediate ``"1"`` of every installation that has not rebuilt yet,
    ``UNKNOWN_VERSION`` and any generation this code has never seen, is answered
    with :data:`findling.query.rewrite.LEGACY_PLAN`. A state that cannot be read
    is no permission: an index whose schema never named itself could be any
    schema, and naming a field it does not carry is the ``ValueError`` that
    leaves the search bar of a live installation empty.

    **One reading of the language mark, not a second one.** An absent or empty
    value means ``LEGACY_LANGUAGES``, which is imported from
    :mod:`findling.store.repo` rather than spelled again, exactly as
    ``findling.index.rebuild._new_language_count`` reads it. A code the schema
    does not know is passed over and the remaining ones stand; if nothing
    remains, the legacy plan is the answer again.

    **The counter probe at the directory itself**, and since audit finding
    M-19-01 it stands under every plan that leaves here, the fallback included.
    It catches the one state the mark cannot see: a ``state.db`` restored from a
    backup beside an older index directory, where the mark promises thirteen
    fields and the directory holds nine. What it does with a name that raises is
    written at :func:`_probed`; what this function does with the answer is the
    cascade below. The legacy plan is the second candidate and not the certain
    answer, because it names four fields that a later schema generation may drop
    or rename, and a fallback that raises is a worse failure than the one it was
    reached for.

    **Never raises**, deliberately and with every exception caught. This runs
    inside the try of :func:`read_side`, where an exception would cost the whole
    reading half of the container and answer every search with nothing at all.
    The outer catch says so at ``error`` level and not at ``warning`` level, and
    the reason is M-19-04: a volume whose two halves disagree is answered one
    level down, by name and per field, so what is left for the outer catch is
    this build contradicting itself. One of the two is a message to the operator
    and the other is a bug of ours, and a log an operator ships has to be able to
    tell them apart.

    :func:`filled_languages` is not called and must not be: it walks the entire
    term dictionary of every chain it asks about and carries a TTL of its own for
    that reason, which is the shape of a diagnosis and not of a query path
    (19-RESEARCH open question 2). "Filled" is read here as the stored mark. A
    chain that is switched on, built and still empty costs a search one lookup in
    an empty posting list and returns no wrong hit.

    Takes no search text, in any shape. That is the structural half of the
    anti-feature "no language detection, neither of a document nor of a query":
    a detector is not forbidden here, it has nothing to attach to.
    """
    try:
        computed = _of_the_marks(marks)
        probed = None if computed is None else _probed(computed, index)
        if probed is not None:
            return probed
        # The cascade of M-19-01, and both of its steps are the same question
        # asked of the directory: what is left of the plan the marks describe,
        # and failing that, what is left of the four names every release up to
        # 1.2.0 searched. A directory that answers neither is a directory no
        # search can reach, and the empty plan says exactly that instead of
        # handing the parser a name it will raise on.
        return _probed(LEGACY_PLAN, index) or EMPTY_PLAN
    # Deliberately every exception, for the reason in the docstring above, and
    # deliberately an error line where the lines beside it are warnings
    # (audit finding M-19-04). Everything the two halves of a volume can disagree
    # about is caught one level down, per name and with the name in the line: a
    # field the directory does not carry never reaches this catch. What reaches
    # it is this build contradicting itself, a KeyError between two closed
    # mappings that drifted apart, an AttributeError after a rename, a TypeError
    # after a changed signature. The first is a message to the operator about
    # their volume and the second is a bug of ours, and until this finding both
    # were one warning saying "the marks do not fit", which is the wrong sentence
    # for the second one and unactionable for the first.
    except Exception as error:
        LOGGER.error(
            "the field plan could not be computed at all, an %s in this build, the search keeps the legacy plan",
            type(error).__name__,
        )
        return LEGACY_PLAN


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
        if _SWAPPING:
            # A directory swap is between its two renames, so there is no live
            # index directory to open and no handle worth keeping. See _SWAPPING.
            return None
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
            # The reading side asks body_nl with the same chain the writer
            # filled it with, so it names the Dutch choice out of the same
            # language set; a missing or foreign list lands in the except below.
            index = open_index(resolved.index_dir, build_artifact().entries, dutch=dutch_digest_for(resolved.languages))
            # Once per index, not once per query: configuring the reader costs
            # 0.10 ms while a whole search costs 0.005 ms. The searcher it returns
            # is a snapshot and deliberately not kept; the reload policy is what
            # makes a later commit of the poller visible to this process at all.
            open_reader(index)
            store = open_read_only(resolved.state_db)
            # After the two that matter, and outside their fate. Whatever this
            # answers, the read side is opened.
            vectors = _read_only_vectors(resolved.vectors_db)
            # The same place and the same rule as the line above: computed after
            # the two handles that matter, out of what they carry, and outside
            # their fate. Once per open and not once per query, which is what
            # the whole field plan hangs on ReadSide for.
            #
            # The meta read has a try of its own rather than riding in the one
            # around it, so that this line cannot narrow what opens. A state
            # database that connects and then refuses its first query is a real
            # shape, a zero byte file left by a hard kill, and until here it was
            # not a container without a read side; an empty mapping sends
            # field_plan_for through its own closed gate.
            try:
                marks = store.read_meta()
            # Deliberately every exception, for the reason above.
            except Exception as error:
                LOGGER.warning("the marks of the directory could not be read, an %s", type(error).__name__)
                marks = {}
            plan = field_plan_for(marks, index)
            _OPEN = ReadSide(
                index=index,
                store=store,
                index_dir=resolved.index_dir,
                vectors=vectors,
                generation=_GENERATION,
                field_plan=plan,
                plan_is_short=plan_falls_short(marks, plan),
            )
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

    **The generation moves with it**, and that is the second half of the
    invalidation rather than bookkeeping. The two measurements below take their
    side outside this lock and write their cache entry inside it, so one of them
    can be holding a side from before this call while this call is running; the
    number is what lets it notice. The reasoning stands at
    :attr:`ReadSide.generation`.

    Idempotent. A second call and a call on a container whose first indexing
    pass never finished both find nothing and do nothing.
    """
    global _OPEN, _MARKS, _DEGRADED, _FILLED, _GENERATION
    with _LOCK:
        _GENERATION += 1
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


def hold_the_read_side_shut() -> None:
    """Raise the bar of the directory swap and let go of everything behind it.

    The first of the pair :func:`findling.index.rebuild.rebuild_the_index` calls
    around its two renames, and it is one step and not two on purpose: a bar
    that went up after the caches were emptied would leave the window it exists
    to close (audit finding M-18-03, and the reasoning at :data:`_SWAPPING`).

    While the bar is up :func:`read_side` answers None, so a search that arrives
    inside the window answers empty instead of opening the directory that is
    about to be renamed away under it. The lock is re-entrant, which is what
    lets the bar and the release stand in one block.

    Always paired with :func:`let_the_read_side_open`, and the caller puts that
    one in a finally: a swap that raised leaves a container that answers, and a
    bar nobody lowered would leave one that does not.
    """
    global _SWAPPING
    with _LOCK:
        _SWAPPING = True
        reset_read_side()


def let_the_read_side_open() -> None:
    """Lower the bar, so that the next search opens the directory that is there now.

    The other half of :func:`hold_the_read_side_shut`. Nothing is opened here:
    the first search after it pays the open, exactly as it does after every
    other invalidation.
    """
    global _SWAPPING
    with _LOCK:
        _SWAPPING = False


def degraded(side: ReadSide | None) -> bool:
    """True when this container is answering, but not from a complete index.

    Five causes, one flag: there is no index yet, the index was built by a
    different tokenisation, the volume is too full for the indexer to commit,
    embedding is switched on and there is no vector stock to answer with, or a
    question reaches fewer fields than the marks of the directory promise. The
    PHP side gets one boolean out of it so that it can stay quiet instead of
    guessing, and phase 4 builds the status page out of the same answers.

    The fifth cause is audit finding M-19-03 and it is the cheapest of the five:
    it was measured when the handles were opened and is read off
    :attr:`ReadSide.plan_is_short` here. An instance whose search reaches two
    chains while its marks name six answers demonstrably incompletely, and that
    is what this flag is for; until the finding it was the one incomplete answer
    of this container that nothing anywhere reported.

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
        verdict = side.plan_is_short or missing_vectors or bool(version_drift(side.store)) or low_disk()
        if side.generation == _GENERATION:
            # And not otherwise. The side was taken outside this lock, so a
            # reset may have happened in between, and remembering a verdict
            # measured on the directory that was retired a moment ago is the
            # race of audit finding M-18-02. The verdict is still handed out:
            # it was true when it was measured, and the caller asked about the
            # handles it holds.
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

    **Which chains are asked, and why not all six** (audit finding M-18-08). The
    ones the settings switch on, plus German, and nothing else. The probe walks
    the entire term dictionary of a field by tantivy's own documentation and the
    limit cuts only afterwards, so every field asked is a full walk over the
    dictionary of a directory that the projection of this project puts at 560 MB
    for 100000 files. Six of those every thirty seconds on a 4 GB box, for an
    instance that runs German alone, is a cost that grows with the index and
    buys an answer nobody needs: a chain that is switched off is not filled and
    is not going to be. German is in whatever the settings say, because
    ``body_de`` is the one stored copy of the text and therefore the one chain
    whose emptiness says something about the directory rather than about the
    configuration.

    **Why one try per chain and not one for all of them** (audit finding
    M-18-01). The whole probe used to sit in a single generator inside a single
    ``try``, so one field that raised discarded the measurement of all six. That
    is not a corner: an index of the old generation has nine fields and no
    ``body_es`` at all, ``terms_with_prefix`` raises on it, and the answer was
    an empty tuple for every chain, on exactly the installation this line was
    written for. The administration page then wrote that not a single chain
    carries text while the German one was full of it. Per chain, a failure costs
    that chain and nothing else, and it is a debug line rather than a warning
    because a missing field on an index of the old generation is the expected
    state and not a fault.

    **Why the reading is cached, and why the window is its own.** The walks
    above, and an administration page that polls every few seconds while it is
    open. So the answer is remembered for :data:`FILLED_TTL_SECONDS` under the
    directory it was measured in, in the shape :func:`degraded` above uses and
    under the same lock. The one event that really changes it, the directory
    swap of a rebuild, clears the cache through :func:`reset_read_side` instead
    of waiting the window out.

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
        # Deliberately every exception, for the reason read_side() states: this
        # value reaches an administration page, and a page that answers 500
        # because one of its lines could not be measured tells an admin less
        # than a page that leaves that line empty.
        except Exception as error:
            LOGGER.warning("the fill level of the body chains could not be read, an %s", type(error).__name__)
            return ()
        filled: list[str] = []
        for code in _chains_worth_probing():
            try:
                if searcher.terms_with_prefix(BODY_FIELD[code], "", limit=1):
                    filled.append(code)
            # One chain, one answer. A directory of the old generation has no
            # field beyond the first two, and asking it for one is the realistic
            # shape of this failure rather than a fault worth a warning.
            except Exception as error:
                LOGGER.debug("the chain %s could not be probed, an %s", code, type(error).__name__)
        answer = tuple(filled)
        if side.generation == _GENERATION:
            # The same guard degraded() carries, and for the same race
            # (M-18-02). This is the reading a rebuild exists to move, so a
            # cache entry filled from the retired directory would have the admin
            # page report the old chains for the whole window right after the
            # run that filled the new ones.
            _FILLED = (side.index_dir, now, answer)
        return answer


def _chains_worth_probing() -> tuple[str, ...]:
    """The body chains :func:`filled_languages` asks about, in schema order.

    The active set plus German, and the order is the one of ``BODY_FIELD`` and
    never the one of the settings: the list travels to an administration page
    beside the active set, which is ordered the same way, and two lists of the
    same codes in two different orders read like a disagreement.
    """
    active = set(settings().languages) | {"de"}
    return tuple(code for code in BODY_FIELD if code in active)


def report_version_drift() -> None:
    """Log a version drift once at startup, and decide nothing about it.

    What follows from a drift is the poller's business: resetting one storage and
    throwing the whole index away are both defensible and neither is a decision a
    read path gets to make. What is not defensible is a drift nobody ever hears
    about.

    **``sqlite3.Error`` stands next to ``OSError`` on both the open and the
    read.** This runs in the lifespan, so an exception here is a container that
    does not start, and two realistic shapes of a broken state escape an
    ``except OSError``: a file that is not a SQLite database raises
    ``DatabaseError`` from the ``PRAGMA journal_mode`` that
    :func:`findling.store.repo.open_read_only` sends right after connecting, and
    a zero byte ``state.db``, which a hard kill between the connect and the
    schema script leaves behind, opens cleanly and raises ``OperationalError``
    on the first query. ``api/status.py`` has carried that pair since review
    finding WR-01 and this line had not taken the pattern over (audit finding
    M-18-06). A startup statement that cannot be made is a line in the log and
    never a container that will not come up.
    """
    resolved = settings()
    if not resolved.state_db.is_file():
        return
    try:
        store = open_read_only(resolved.state_db)
    except (OSError, sqlite3.Error) as error:
        LOGGER.warning("the state database could not be read at startup, an %s", type(error).__name__)
        return
    try:
        drift = version_drift(store)
    except sqlite3.Error as error:
        LOGGER.warning("the version marks could not be read at startup, an %s", type(error).__name__)
        return
    finally:
        store.close()
    if drift:
        LOGGER.warning(
            "the index was built with different versions than this build produces, a reindex is required: %s",
            ", ".join(sorted(drift)),
        )
