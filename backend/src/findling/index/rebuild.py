"""The rebuild of the index directory: what may start, and what a run carries over.

A schema change never reaches an index that already exists by editing it. The
rebuild writes a second directory beside the live one, document by document, and
the directory swap of plan 18-07 puts it in place. This module is the half that
produces the new directory; it installs nothing and it stamps nothing.

*A run is long enough to be a background job and never a request.* Measured on
2026-09-24 with tantivy 0.26.2 over 3000 documents of roughly 2.5 kB each and
four filled chains: 683 documents per second, 4.39 s for the whole run, and the
field equality of all 3000 documents afterwards True. The German chain with its
276496 entry compound automaton did not run in that probe, because the word list
was not on the measuring machine, so the figure is the ceiling of the speed and
not a promise about a box.

*Every stored value comes back as a list, and the empty string is a value.* Also
measured on 2026-09-24, against the real ``build_schema()``: ``to_dict()`` answers
``dict[str, list[value]]`` even where one value was written, it carries exactly
the eight stored fields (body_de, ext, file_id, mtime, name, path, storage_id,
title), ``body_en`` is absent from it because it was never stored, a field
written as the empty string comes back as ``[""]`` instead of disappearing, a
negative ``mtime`` comes back negative, and a ``storage_id`` of 2 to the 40th
comes back unharmed. A missing key is therefore a finding about a document this
project never wrote, and never a place for a default value.

*Every handle on a directory has to be gone before that directory is renamed.*
Measured on Windows on 2026-09-24: a rename with open mmaps refuses with
PermissionError, WinError 5. On Linux the same call succeeds, and that is the
trap rather than the convenience, because the reading side then answers out of a
directory that has no name anymore, silently and for as long as the process
lives. The rule decides how a run of this module ends as well: the writer waits
for its merging threads, the reference is dropped, and nothing is handed out
that still holds the target.

*The order of the swap, and the order is its whole content.* Six steps, and
every one of them is there because leaving it out is a way of arriving at a
container that answers out of a directory nobody can point at any more:

1. commit the target index, ``wait_merging_threads()`` on its writer, let the
   object go. A writer holds a lock file, and a merging thread holds segments
   that are about to disappear.
2. let the source index go. The poller's writer is closed at this point because
   the first thing :func:`rebuild_the_index` does is to stand the poller down,
   and standing down is what closes it. Until the audit of this phase that
   sentence read "silencing it is the first thing the caller does", and it was
   wrong three times over: ``Poller.silence()`` clears a flag and nothing else,
   the writer is built once per poller and handed back only in ``aclose()``, and
   the lifespan arms the poller twenty two lines before it creates the rebuild
   task. The swap therefore removed a directory a live ``IndexWriter`` was
   holding, and everything the poller indexed afterwards went into inodes with
   no name (C-18-01). The callback now waits for the pass in flight and gives
   the handle back, and a callback that answers False stops the run before
   anything is renamed.
3. drop the reading side with an explicit ``reset_read_side()``, over in
   :mod:`findling.api.resources`.
   That cache is keyed on ``index_dir``, the swap does not move ``index_dir``,
   and the invalidation branch inside ``read_side()`` therefore never fires on
   its own.
4. rename ``index`` to ``index.retired``.
5. rename ``index.rebuild`` to ``index``.
6. remove ``index.retired``.

Steps 4 and 5 are :func:`swap_in`, and there is deliberately nothing between
them: between the two renames the volume holds no directory called ``index`` at
all, and that window is the one state a crash can leave behind (T-18-07-02).
Steps 1 to 3 are led by :func:`rebuild_the_index`, and the two of them that
reach outside this module arrive as callbacks rather than as imports. This
module does not import :mod:`findling.api.resources` and it does not import
:mod:`findling.worker.poller`: the reading half of the container may draw from
the index, never the other way round, and the poller is already the caller of
``expected_versions``, so an import in this direction would close a circle in
both cases.

*A volume is read before it is used, because a crash leaves states behind.* The
three directory names above are the three a container can find at its start, and
their five combinations are the five decisions of
:func:`recover_the_index_directories`. Three of the five put something in order
and two of them deliberately leave the volume as it is, and the difference
between the two groups is not how bad the state looks but whether the container
can still answer a search out of what stands there.

*An index whose chains are not registered raises on the first write.* Measured on
2026-09-24 as well: a schema that carries a text field whose tokenizer is not
registered answers every ``add_document`` with "Schema error: 'Error getting
tokenizer for field: body_es'", and it does so even for a document that does not
carry that field; ``snowball_analyzer`` answers a language outside the measured
allowlist with a ValueError before it gets that far. Registering is what opening
does, so both directories of a rebuild go through
:func:`findling.index.open.open_index` and never through ``Index(...)``.
"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from tantivy import Document, FieldType, Index, Order, Query

from findling.config import FULL_REINDEX_FALLBACK, SCHEMA_VERSION, settings
from findling.index.open import (
    LANGUAGES_MARK,
    REBUILD_MARK,
    expected_versions,
    open_index,
    open_reader,
    start_rebuild_on_drift,
)
from findling.index.schema import (
    BODY_FIELD,
    FIELD_BODY_DE,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)
from findling.index.wordlist import build_artifact
from findling.store.repo import Store, index_bytes

LOGGER = logging.getLogger("findling.index.rebuild")

# What one newly filled chain adds to the index directory, as a share of what the
# directory holds today. The reasoning stands at may_rebuild; the number is 0.40
# because a run that is refused before it starts costs a log line and a run that
# dies halfway costs the whole pass.
GROWTH_PER_LANGUAGE: Final = 0.40

# The two answers of the precheck, as text rather than as an enum, for the reason
# the flush states of findling.index.writer give: they travel on to a banner and
# into an operating report, where a short closed list of readable names is worth
# more than a type.
ROOM_ENOUGH: Final = ""
NOT_ENOUGH_ROOM: Final = "not enough room for two index directories"

# Documents per band. 500 of them at the 15 kB the projection of this project
# works with are 7.5 MB held at once, which is nothing against the 4 GB box and
# far below the writer heap of 50 MB. The figure is two things at the same time:
# the memory of one step and the crash granularity of the whole run, because the
# commit follows the band. A band of one would fsync per document and turn the
# run into thousands of tiny segments; a band of fifty thousand would make a
# crash cost the whole pass.
BAND_DOCUMENTS: Final = 500

# The upper end of the key column. file_id is an unsigned 64 bit field, so this
# is every value it can hold, and the band is therefore bounded from below by the
# cursor alone.
_HIGHEST_FILE_ID: Final = 2**64 - 1

# What the live directory is called while it is on its way out. It is appended to
# the name the live directory already has, so the retired directory is always the
# sibling of the one it came from and never a path anybody handed in
# (T-18-07-04).
RETIRED_SUFFIX: Final = ".retired"

# What the new directory is called while it is being filled. Same construction as
# the suffix above and for the same reason: the three directories of a rebuild
# are siblings of one another, every one of their names is derived from the one
# path findling.config hands out, and none of them is ever assembled out of
# something a caller chose (T-18-08-03).
REBUILD_SUFFIX: Final = ".rebuild"

# The five answers of the clean up path, as text rather than as an enum, for the
# reason the two answers of the precheck give: they travel on into an operating
# report, where a short closed list of readable names is worth more than a type.
# Each of them names one of the five states a container can find in the volume,
# and there is deliberately no sixth: a state this list does not name would be a
# state nobody decided about.
NOTHING_TO_PUT_IN_ORDER: Final = "the volume needs nothing put in order"
HALF_FILLED_TARGET_KEPT: Final = "a half filled target directory is kept for the run that resumes it"
TARGET_RAISED_TO_THE_LIVE_NAME: Final = "the rebuilt directory was raised to the live name"
RETIRED_BROUGHT_BACK: Final = "the retired directory was brought back to the live name"
RETIRED_DISCARDED: Final = "a retired directory beside a live one was discarded"

# The name of the schema mark, spelled once here because there is no constant for
# it anywhere else: findling.index.open writes it as a literal inside
# expected_versions, and findling.store.repo seeds it as a literal as well. A
# second spelling that drifted from the first would be a stamp that writes a mark
# nothing ever compares, so a case in the suite holds the two together by asking
# the expectation for this very key.
_SCHEMA_MARK: Final = "schema_version"

# The two marks this rebuild can do anything about, and the reason the set is
# closed. A rebuilt directory is written under the current schema and filled with
# the current language set, so those two marks become true by the pass itself. A
# moved wordlist hash, a moved analyzer version and a moved tantivy banner are
# real differences with a different remedy: they need the documents read again,
# which is the crawl the generation raise orders, and carrying the old text over
# would leave the very drift the mark reports (18-RESEARCH.md, pitfall 1).
MARKS_A_REBUILD_ANSWERS: Final = frozenset({_SCHEMA_MARK, LANGUAGES_MARK})

# What an index without a language mark was built with. Not a guess and not a
# default: no release up to 1.2.0 could write a body field outside this pair, so
# the absence of the mark is evidence rather than a gap. The same tuple stands in
# findling.store.repo as LEGACY_LANGUAGES, which is where the comparison reads it,
# and a case in the suite holds the two spellings together. It is not imported
# from there because the rebuild takes two names out of the store package and no
# more, and widening that list for a two element tuple would be the wrong trade.
_CARRIED_WITHOUT_A_MARK: Final = ("de", "en")

# The verdicts of the whole run, as text and for the reason the five names of the
# clean up path give: they travel into an operating report and onto the admin
# page, where a short closed list of readable names is worth more than a type.
# NOT_ENOUGH_ROOM above is the sixth of them, handed straight out of the precheck.
NOTHING_TO_REBUILD: Final = "the version marks a rebuild answers agree, so nothing runs"
NO_LIVE_DIRECTORY: Final = "there is no live index directory to carry documents out of"
FALLBACK_TO_FULL_REINDEX: Final = "the generation was raised instead, the reindex banner names the way"
RUN_STOPPED_EARLY: Final = "the run stopped between two bands and keeps its half filled directory"
RUN_INCOMPLETE: Final = "the final probe counted fewer documents than the old directory holds, nothing was swapped"
REBUILD_THROUGH: Final = "the rebuilt directory is in place and the two marks are current again"
POLLER_STILL_WRITING: Final = "the indexing task did not stand down, so nothing was carried over and swapped"


@dataclass(frozen=True, slots=True)
class RebuildVerdict:
    """Whether a rebuild may start, with the numbers the answer rests on.

    The numbers travel with the verdict on purpose. The banner an admin reads has
    to name how much room the rebuild wants and how much there is, and a banner
    that measured the volume a second time would name two figures that were never
    true at the same moment.
    """

    may_start: bool
    reason: str
    needed_bytes: int
    free_bytes: int


def may_rebuild(index_dir: Path, new_language_count: int) -> RebuildVerdict:
    """Answer whether there is room for the old and the new index directory at once.

    ``new_language_count`` is how many body chains the rebuild fills that are not
    filled today, and every one of them is charged 0.40 of what the directory
    holds now. Measured on 2026-09-24 over 2000 documents and 9.88 MB of text: a
    filled chain costs 0.086 times the amount of text, against a base index that
    costs 0.231 times the same text, so a chain is 0.372 of the directory. The
    figure here sits above the measurement deliberately, because the two errors
    are not the same size: a refusal before the start costs one log line, and a
    volume that runs full in the middle of the pass costs the whole run plus a
    half written directory somebody has to reason about.

    ``MIN_FREE_BYTES`` is not lowered for the occasion. It is the floor the
    running indexer pauses at, the vector stock and the state database live on
    the same volume, and a rebuild that ate into that floor would trade a
    refusal now for a paused indexer afterwards. The need of the rebuild is
    therefore added on top of the floor and never taken out of it.

    The directory is expected to exist: every caller asks this after
    :func:`findling.index.open.open_index` has run, which creates it.
    :func:`findling.store.repo.index_bytes` answers 0 for a directory that is
    not there, and a rebuild of an index of zero byte is refused by nothing here
    because there is nothing to carry over.
    """
    current = index_bytes(index_dir)
    needed = int(current * (1 + GROWTH_PER_LANGUAGE * new_language_count))
    # The one measurement of the volume in this module. A second call would be a
    # second answer about one volume, and the verdict below carries the numbers
    # precisely so that nobody has to ask again.
    free = shutil.disk_usage(index_dir).free
    floor = settings().min_free_bytes
    if free < needed + floor:
        # Two figures and no path, as every line of this module (T-18-06-02).
        LOGGER.warning(
            "a rebuild would need %d byte on top of the floor of %d byte and %d byte are free, so it does not start",
            needed,
            floor,
            free,
        )
        return RebuildVerdict(False, NOT_ENOUGH_ROOM, needed, free)
    return RebuildVerdict(True, ROOM_ENOUGH, needed, free)


@dataclass(frozen=True, slots=True)
class RebuildProgress:
    """How far the band run has got: a state and the two numbers behind it.

    ``documents_carried`` counts the directory and not the pass, unlike
    :attr:`RebuildRun.documents_written`: a run that resumed after a break shows
    what stands in the new directory, because that is the number a progress
    display is asked about.
    """

    running: bool
    documents_carried: int
    documents_total: int


# The resting state, and the one the process starts in. A container that never
# rebuilt anything answers with this, and so does one whose run is through: the
# reading of a finished run would otherwise keep a banner up that has nothing
# behind it any more.
_AT_REST: Final = RebuildProgress(running=False, documents_carried=0, documents_total=0)

# The progress of this process, held at module level and nowhere else, after the
# build of engine_state in findling.embed.engine: a function answers the current
# state and there is no second record of it on the volume. A counter in state.db
# would be a number that can disagree with the directory it describes, which is
# the same argument _resume_cursor makes about the cursor, and it would outlive
# the process that wrote it.
_PROGRESS: RebuildProgress = _AT_REST


def rebuild_progress() -> RebuildProgress:
    """What the band run of this process is doing right now.

    Read by the status route of plan 18-10 and by nothing that decides anything.
    Nothing is opened and nothing is measured here: the question is asked while a
    page polls, so an answer that read the directory would put a stat call of the
    volume behind every poll of every open admin page.
    """
    return _PROGRESS


def _note_progress(progress: RebuildProgress) -> None:
    """Publish the reading of the moment. One assignment, called between bands."""
    global _PROGRESS
    _PROGRESS = progress


# How many bytes the precheck was short of, and nought when it did not refuse.
#
# Held next to the progress above and for the same reason: it describes this
# process, it is read by the status route of plan 18-10 and by nothing that
# decides anything, and a number on the volume could disagree with the volume it
# describes. It is deliberately not cleared on a timer. A refusal stands until
# the next start, because nothing between now and then makes it untrue: the
# rebuild is attempted once per start, and the banner an admin reads has to be
# there when they come back to the page rather than having quietly aged out.
_BLOCKED_BYTES: int = 0


def rebuild_blocked_bytes() -> int:
    """How many bytes were missing when the precheck refused, 0 when it did not.

    The figure behind criterion 3 of the phase. A banner that says the volume is
    too full without naming a number leaves the admin to guess how much to free,
    and a page that measured the volume itself would name a figure that was
    never true at the same moment as the refusal.
    """
    return _BLOCKED_BYTES


def _note_blocked_bytes(missing: int) -> None:
    """Publish the shortfall of the precheck. One assignment, two call sites."""
    global _BLOCKED_BYTES
    _BLOCKED_BYTES = missing


@dataclass(frozen=True, slots=True)
class RebuildRun:
    """What one pass of the band run did, in the figures the caller decides on.

    ``documents_written`` counts this pass and not the directory: a run that
    resumed after a break writes the remainder and says so, while
    ``target_documents`` is what stands in the new directory afterwards.
    """

    documents_written: int
    source_documents: int
    target_documents: int
    complete: bool


def counts_match(source: Index, target: Index) -> bool:
    """True while the new directory holds as many documents as the old one.

    The last question before the swap of plan 18-07, and a function of its own
    because it is the one answer that may never be inferred from "the loop ran
    through". A pass that ended on an exception between two bands also reaches
    the end of its function; what it does not reach is this equality. A caller
    that gets False here does not swap, it runs again.

    Both indexes are reloaded first. A searcher is a snapshot, and a snapshot
    taken before the last commit would report the count of the band before the
    last one.
    """
    source.reload()
    target.reload()
    return target.searcher().num_docs == source.searcher().num_docs


def _resume_cursor(target: Index) -> int:
    """The highest file_id already carried over, and 0 on an empty target.

    **Why the half written directory is the whole progress record.** A counter in
    state.db would be a second piece of state beside the index, and a second
    piece of state can disagree with the first one: it is written before the
    commit or after it, and either way a crash in between leaves a number that
    describes a directory that does not exist. The index cannot disagree with
    itself. A band that was added and not committed is gone when tantivy opens
    the directory again, which is the same behaviour the writer module measured
    with kill -9, and the band is written again because the cursor did not move.

    It costs nothing to ask. ``file_id`` is a fast field, so the sort is a column
    read and not a scan, and it is asked exactly once per run.
    """
    target.reload()
    searcher = target.searcher()
    if searcher.num_docs == 0:
        return 0
    top = searcher.search(Query.all_query(), limit=1, order_by_field=FIELD_FILE_ID, order=Order.Desc)
    return int(searcher.doc(top.hits[0][1]).to_dict()[FIELD_FILE_ID][0])


def _document_from(stored: Mapping[str, list[object]], languages: Sequence[str]) -> Document:
    """One document of the old index, built again under the current schema.

    Every value arrives as a one element list and every one of the eight stored
    fields is present, even where it holds the empty string: measured on
    2026-09-24, a document written with ``ext=""`` and ``body_de=""`` comes back
    as ``{"ext": [""], "body_de": [""], ...}``. A missing key is therefore a
    document this project never wrote, and it is a finding rather than a place
    for a default value, which is why nothing below reaches for one.

    ``body_de`` is the only stored copy of the text in the whole system, and
    ``body_en`` was never stored because it carries the same string through
    another chain. So one read feeds every chain that is switched on, and the
    stored field is written whatever the language set says, exactly as the writer
    of the running index does it: an instance on Spanish alone that stopped
    writing it would answer every search without a preview.
    """
    document = Document()
    document.add_unsigned(FIELD_FILE_ID, int(stored[FIELD_FILE_ID][0]))  # pyright: ignore[reportArgumentType]
    document.add_unsigned(FIELD_STORAGE_ID, int(stored[FIELD_STORAGE_ID][0]))  # pyright: ignore[reportArgumentType]
    document.add_text(FIELD_NAME, str(stored[FIELD_NAME][0]))
    document.add_text(FIELD_TITLE, str(stored[FIELD_TITLE][0]))
    document.add_text(FIELD_PATH, str(stored[FIELD_PATH][0]))
    document.add_text(FIELD_EXT, str(stored[FIELD_EXT][0]))
    body = str(stored[FIELD_BODY_DE][0])
    document.add_text(FIELD_BODY_DE, body)
    for code in languages:
        field = BODY_FIELD[code]
        if field == FIELD_BODY_DE:
            # Already written above, and writing it twice would double its
            # postings for nothing. The same line stands in the writer of the
            # running index, for the same reason.
            continue
        document.add_text(field, body)
    document.add_integer(FIELD_MTIME, int(stored[FIELD_MTIME][0]))  # pyright: ignore[reportArgumentType]
    return document


def transfer_documents(
    source_dir: Path,
    target_dir: Path,
    constituents: Sequence[str],
    languages: Sequence[str] | None = None,
    band_documents: int = BAND_DOCUMENTS,
    should_stop: Callable[[], bool] | None = None,
) -> RebuildRun:
    """Carry every document of the old index into the new directory, band by band.

    **The condition without which this is wrong.** The poller may not write into
    the source index while this runs. The cursor only ever moves forward, so a
    document that arrives below it lands in the source after the band that would
    have taken it and is never carried over. Silencing the poller is the job of
    the caller of plan 18-09 and deliberately not of this module: a module that
    silenced it would also have to decide when to arm it again, and that decision
    belongs to whoever owns the run.

    **Why both directories go through open_index.** The schema persists the name
    of an analyzer and never the analyzer, so an index opened without the
    registration answers the first write with a schema error about a tokenizer it
    cannot find. Opening is registering, and there is one module that does it.

    The pass is resumable and repeatable: it starts at the highest file_id the
    target already holds, and a pass with nothing left to do writes nothing and
    says so.

    ``should_stop`` is asked between two bands and never inside one, which is the
    same granularity the commit has. A shutdown that interrupted a band would
    throw away the documents of that band and gain nothing for it, because the
    commit behind it is what the next run finds; a shutdown that waits for the
    whole pass is a container the orchestrator kills. So the answer is read at
    the one point where stopping costs nothing at all.
    """
    active = tuple(settings().languages if languages is None else languages)
    source = open_index(source_dir, constituents)
    target = open_index(target_dir, constituents)
    reader = open_reader(source)
    cursor = _resume_cursor(target)
    # Read after the resume, because the reload it does is what makes the count
    # of a half filled directory the count of what is really committed in it.
    carried = target.searcher().num_docs
    total = reader.num_docs
    written = 0
    _note_progress(RebuildProgress(running=True, documents_carried=carried, documents_total=total))
    writer = target.writer(heap_size=settings().writer_heap_bytes, num_threads=1)
    try:
        while True:
            if should_stop is not None and should_stop():
                LOGGER.info("the band run stops between two bands; the half filled directory keeps what it has")
                break
            # A band over the key column and never a growing offset: measured on
            # 2026-09-24, a search over all documents with a limit of 1000 and an
            # offset of 51000 makes tantivy collect 52000 hits to hand out 1000,
            # which over a whole run is quadratic, while the band over the fast
            # field is linear. The keyword is spelled out rather than written,
            # because the test that holds this line reads the syntax tree.
            band = Query.range_query(
                source.schema,
                FIELD_FILE_ID,
                FieldType.Unsigned,
                cursor + 1,
                _HIGHEST_FILE_ID,
                True,
                True,
            )
            hits = reader.search(band, limit=band_documents, order_by_field=FIELD_FILE_ID, order=Order.Asc).hits
            if not hits:
                break
            for _score, address in hits:
                stored = reader.doc(address).to_dict()
                writer.add_document(_document_from(stored, active))
                cursor = int(stored[FIELD_FILE_ID][0])
            # One commit per band, which is what makes the band the crash
            # granularity: what is committed is what the next run finds.
            writer.commit()
            written += len(hits)
            carried += len(hits)
            _note_progress(RebuildProgress(running=True, documents_carried=carried, documents_total=total))
    finally:
        # Whatever ended this loop, the merging threads are waited for and the
        # lock goes back. The swap of plan 18-07 cannot rename a directory a
        # writer still holds, and on Windows it refuses with WinError 5 rather
        # than succeeding quietly.
        writer.wait_merging_threads()
        # The reading goes back to rest here and not after the swap, because the
        # carrying is what this number is about: the two renames behind it are
        # two system calls, and a progress display that stayed at 100 percent
        # through them would report a directory that is already in place.
        _note_progress(_AT_REST)
    LOGGER.info("carried %d documents over into the new index directory", written)
    target.reload()
    return RebuildRun(
        documents_written=written,
        source_documents=reader.num_docs,
        target_documents=target.searcher().num_docs,
        complete=counts_match(source, target),
    )


def retire_directory(live: Path) -> Path:
    """Move the live index directory out of the way and answer where it went.

    The new name is derived from the old one with
    :meth:`pathlib.Path.with_name`, so the retired directory is the sibling of
    the one it came from. Nothing about that path is handed in, and that is the
    point: the only thing removed further down is a directory this function
    itself named, on the volume the live one already stood on (T-18-07-04).
    """
    retired = live.with_name(live.name + RETIRED_SUFFIX)
    live.rename(retired)
    return retired


def discard_directory(retired: Path) -> None:
    """Remove a retired directory, and refuse to be quiet about a leftover.

    ``ignore_errors`` is False on purpose. A directory that will not go is a
    finding: it stays on the volume, it counts against the free space the next
    precheck measures, and it keeps the clean up path of the next container
    start busy with a state nobody explained. The swap above is through at this
    point, so the exception costs the log line and not the rebuild.
    """
    shutil.rmtree(retired, ignore_errors=False)


def swap_in(target: Path, live: Path) -> None:
    """Put the rebuilt directory in the place of the live one. Order is content.

    Two renames and then the removal, with nothing in between. Between the first
    and the second rename the volume holds no directory under the live name at
    all, which is the one window a crash can be caught in, so the window is kept
    as short as two system calls (T-18-07-02). A container killed inside that
    window finds the state again at its next start, and
    :func:`recover_the_index_directories` is what decides about it there.

    **Every handle on both directories has to be gone before the first rename.**
    Measured on Windows on 2026-09-24: a rename with a live searcher on the
    directory refuses with ``PermissionError``, WinError 5. On Linux the very
    same call succeeds, because POSIX renames over inodes, and that is the trap
    rather than the convenience: the reading side would afterwards answer out of
    a directory that no longer has a name, silently and until the container is
    restarted. The numbered order in the module header is therefore not a
    concession to Windows, it is the only correct order, and Windows merely says
    so out loud. The suite keeps a case for both halves and skips it on neither
    system.

    **Why swap_in and retire rather than move and delete.** Gate A of
    ``backend/tests/test_readonly_gate.py`` forbids the identifiers ``move``,
    ``delete``, ``copy`` and ``trash`` in every module of this package, because
    those are the writing entry points of the Nextcloud file client and a gate
    that waved them through in one module would hide a real write to a user file
    in the next one. The name of that client is not spelled here either: a
    second gate asserts that it appears in ``nc/client.py`` and nowhere else,
    and it reads the text of a module rather than its imports. The names here
    are not a paraphrase of a forbidden word, they are more accurate than it:
    nothing is moved anywhere a caller chose, and what is removed is a directory
    this module named itself.

    **Why the removal is caught and the two renames are not.** The renames are
    the swap; a failure in either of them means the directory the container
    reads from is not the one a stamp would describe, so it has to travel up.
    The removal behind them is housekeeping: the swap is already through, the
    new directory already answers every search, and a leftover the volume will
    not let go of is a state the clean up path of the next start knows by name
    (RETIRED_DISCARDED). Letting it raise here cost the stamp, and an unstamped
    swap is a whole rebuild again at every start (C-18-01).
    """
    try:
        retired = retire_directory(live)
        target.rename(live)
    except OSError as error:
        # The type name and nothing else, as every line of this module: a path
        # is the usual content of an OSError message and the one thing an
        # operating log of this container never carries (T-18-07-05).
        LOGGER.warning("the index directories could not be swapped, an %s", type(error).__name__)
        raise
    try:
        discard_directory(retired)
    except OSError as error:
        LOGGER.warning(
            "the retired index directory could not be discarded, an %s; the swap itself is through and the next "
            "start removes what is left",
            type(error).__name__,
        )


def recover_the_index_directories() -> str:
    """Read what the volume holds at the start and put it in order. Five states.

    Between the two renames of :func:`swap_in` the volume holds no directory
    called ``index`` at all. The window is two system calls wide, and two system
    calls is exactly the width a ``kill -9`` fits into. A container that started
    into that state without this function would open an empty index directory,
    answer every search with nothing and report success while doing it, which is
    the worst of the shapes an integrity fault can take (T-18-08-01). So the
    start reads the volume first, and every state it can find has a decision
    with a reason.

    **The three names come from one path.** ``settings().index_dir`` and twice
    :meth:`pathlib.Path.with_name`. Nothing is handed in, and that is the whole
    protection of the ``rmtree`` further down: the only directory this function
    can remove is one it named itself, beside a live directory that
    :mod:`findling.config` pointed at, on the volume of this container
    (T-18-08-03).

    **The five states.**

    1. Only ``index``: the ordinary start. Nothing is touched, and the function
       says so. Ordinary means every start of every container that never rebuilt
       anything, which is why this is the one branch without a warning.
    2. ``index`` beside ``index.rebuild``: a rebuild was running and did not
       finish. The half filled target stays where it is. The tempting handling
       is the other one, to remove it and start clean, and it would be wrong: the
       half filled directory IS the progress record of that run.
       :func:`_resume_cursor` reads the highest carried over ``file_id`` out of
       it and the next pass carries on there, so removing it would throw away
       every band the broken run had already committed and buy nothing for it.
       This start also does not swap it in, because this start cannot know
       whether the run was through; the only thing that knows is
       :func:`counts_match`, and it is asked by the run and not here.
    3. Only ``index.rebuild``, no ``index``: the swap broke off between its two
       renames. The rebuilt directory is raised to the live name, which is the
       second rename of the swap, and a retired directory found beside it is
       removed, which is the step behind it.

       The reasoning under this branch is the one place in this phase where an
       absence serves as proof, so it is written out. ``index.rebuild`` is NOT
       complete in general: state 2 is the same directory in the middle of being
       filled. What makes it complete here is that ``index`` is gone, because
       only :func:`swap_in` ever removes that name, and :func:`swap_in` is only
       ever called after :func:`counts_match` answered True. The missing live
       directory is therefore the evidence that the final probe had already been
       passed.
    4. Only ``index.retired``, no ``index``: the first rename ran, the second did
       not, and there is no ``index.rebuild`` any more. The retired directory is
       the complete old index, so it comes back under the live name. The
       installation loses the rebuild and keeps its search, which is the right
       way round: a rebuild costs one pass and an index costs the hours of OCR
       that filled it (T-18-08-01).
    5. ``index.retired`` beside an ``index``: the swap itself was through and the
       removal behind it was not, so the retired directory is waste. It is
       removed, because it counts against the free space the next precheck
       measures and because a leftover that nobody explains is the state the next
       start would have to reason about all over again.

    **Why the warning, and why no path.** Four of the five lines below are
    supposed to be unreachable in normal operation, and a line that only ever
    appears after a hard abort is the one line whoever reads that log needs. It
    names the state and never a directory, like every line of this module
    (T-18-08-04).
    """
    live = settings().index_dir
    target = live.with_name(live.name + REBUILD_SUFFIX)
    retired = live.with_name(live.name + RETIRED_SUFFIX)
    if not live.is_dir():
        if target.is_dir():
            LOGGER.warning(
                "no live index directory and a rebuilt one beside it: the swap broke off between its two renames, "
                "raising the rebuilt directory to the live name"
            )
            target.rename(live)
            if retired.is_dir():
                # The step behind the second rename, and it belongs to this
                # branch rather than to a later pass: the retired directory is
                # the old index that the swap had already stood down.
                discard_directory(retired)
            return TARGET_RAISED_TO_THE_LIVE_NAME
        if retired.is_dir():
            LOGGER.warning(
                "no live index directory and a retired one beside it: the swap stood the old index down and never "
                "put the new one in place, bringing the retired directory back"
            )
            retired.rename(live)
            return RETIRED_BROUGHT_BACK
        # No directory at all is the first start of a fresh volume, and
        # findling.index.open creates the live one a moment later. Nothing is
        # missing here, so nothing is said about it.
        LOGGER.debug("the volume holds no index directory yet, which is what a first start looks like")
        return NOTHING_TO_PUT_IN_ORDER
    if retired.is_dir():
        LOGGER.warning(
            "a retired index directory stands beside the live one: the swap was through and its clean up was not, "
            "discarding the retired directory"
        )
        discard_directory(retired)
        return RETIRED_DISCARDED
    if target.is_dir():
        LOGGER.warning(
            "a rebuilt index directory stands beside the live one: a rebuild did not finish, keeping the half "
            "filled directory so that the next pass resumes in it"
        )
        return HALF_FILLED_TARGET_KEPT
    LOGGER.debug("the volume holds one index directory and nothing beside it")
    return NOTHING_TO_PUT_IN_ORDER


def stamp_after_swap(store: Store, languages: str) -> None:
    """Declare the rebuild through, once the swap has really happened.

    Three writes: the schema the new directory was built under, the language set
    it was filled with, and the rebuild mark emptied, which is what takes the
    banner down. ``index_version`` is deliberately not among them, for the same
    reason the other stamp leaves it alone: the stored generation stands above
    the baseline of the code after a rebuild, and writing the baseline back would
    make every verdict of the run that just finished look stale.

    **Why this is a second stamp and not a call into the first one.** The stamp
    in :mod:`findling.index.open` opens on
    ``Store.verdicts_older_than(generation) == 0``, which asks whether every
    living file has been read again under the current generation. That question
    is the right one for a drift that a crawl repairs, and it is the wrong one
    here twice over: this rebuild reads no file at all, so the count it asks
    about never moves, and whether the gate stands open or shut therefore depends
    on what the holdings happened to look like before the rebuild started rather
    than on anything the rebuild did. A gate that answers by accident is worse
    than no gate. Two stampers under one name is the classic way a half finished
    index declares itself complete (T-18-07-03), which is why these are two
    functions with two gates and two call sites.

    **The gate of this one is its call site and nothing else.** It is called
    after :func:`counts_match` said the new directory holds as many documents as
    the old one, and after :func:`swap_in` returned without raising. Called any
    earlier it would write a mark that describes a directory nobody is reading
    from, which is precisely the state the version marks exist to make visible.

    ``languages`` arrives as ``",".join(settings().languages)`` from the caller,
    exactly as it does at the four call sites of
    :func:`findling.index.open.expected_versions`, because the stored mark and
    the expected one have to be the same string or the comparison reports a
    drift on the next start.

    The function that raises the generation on a drift, over in
    :mod:`findling.index.open`, is deliberately not called from this module at
    all: it exists so that a crawl reads the files again, and this rebuild reads
    no file. Raising the generation here would make every stored verdict stale
    and order a full reindex right after the pass that made it unnecessary.
    """
    store.write_meta(_SCHEMA_MARK, str(SCHEMA_VERSION))
    store.write_meta(LANGUAGES_MARK, languages)
    store.write_meta(REBUILD_MARK, "")
    LOGGER.info("the rebuilt index directory is in place; the schema and language marks are current again")


def _new_language_count(store: Store, active: Sequence[str]) -> int:
    """How many body chains this rebuild fills that the old directory does not have.

    The figure the precheck charges 0.40 of the current directory for, so it is
    read out of the index and never out of a wish: the stored language mark says
    what the directory was filled with, the active set says what it will be
    filled with, and the difference is what grows.

    A missing mark is answered with the legacy pair rather than with nothing at
    all. An installation coming from 1.2.0 carries no mark, and reading that as
    "no chain is filled" would charge the rebuild for two chains that are already
    there and refuse runs that fit comfortably.
    """
    stored = store.read_meta().get(LANGUAGES_MARK, "")
    carried = {code for code in stored.split(",") if code} or set(_CARRIED_WITHOUT_A_MARK)
    return len([code for code in active if code not in carried])


def rebuild_the_index(
    store: Store,
    *,
    stand_down: Callable[[], bool],
    arm: Callable[[], None],
    drop_read_side: Callable[[], None],
    should_stop: Callable[[], bool] | None = None,
) -> str:
    """Lead one whole rebuild, in the order of the seven steps and in no other.

    Answers with one of the seven names above, which is what the caller logs and
    what the operating report carries. It raises nothing of its own; what a
    tantivy call or a rename raises travels up to the fourth lifespan task, which
    logs the type name and lets search and indexing carry on.

    **The order is the content of this function**, exactly as it is for
    :func:`swap_in` one level down:

    1. is there a drift this rebuild can do anything about,
    2. is there room for two index directories, or is the named way out switched
       on,
    3. stand the indexing task down, and stop here if it will not go,
    4. carry the documents over, band by band,
    5. ask the final probe,
    6. drop the reading side and swap the directories,
    7. stamp the two marks and let the indexing task go again.

    **Step 3 waits, and the waiting is the whole point of it.** Until the audit
    of this phase it was a ``silence`` that cleared a flag and returned at once,
    which left two things standing that both cost documents: the pass in flight
    went on committing into the source below the cursor (H-18-01), and the
    writer of the poller kept holding the very directory the swap removes
    (C-18-01). The callback now answers whether the task really stood down, and
    a False ends the run in front of the first written document. Nothing is
    created in that case, exactly as in the three refusals above it.

    **Why the poller arrives as a pair of callbacks.** An index module that
    imported the poller would be a circle: the poller is already the caller of
    ``expected_versions`` and of everything else this package hands out. The pair
    is also the smaller interface. This module has to stop the writing and start
    it again; it has no business knowing what else a poller can do, and a test
    can hand in two recorders where it would otherwise have to build a container.

    **Why ``arm`` sits in a ``finally`` that also covers the refusals.** Every way
    out of this function is a way out of a silenced container, and a rebuild that
    refused itself over a full volume must not be the reason an installation
    stops indexing until somebody restarts it. Arming a poller that was never
    silenced costs nothing, arming one that was is the difference between a
    container that carries on and a container that looks healthy and has stopped
    working, and between those two the cheap mistake is the one to make. The
    callback the caller hands in is the one that knows whether arming is allowed
    at all: a container that was switched off while the rebuild ran must stay
    off, and that question belongs to whoever owns the enable.

    **The early exits touch nothing.** Neither the drift branch nor the fallback
    branch nor the refusal of the precheck creates a directory, and that is not
    tidiness: a volume that has no room for two directories must not be given a
    third name to reason about at its next start, and the clean up path of
    :func:`recover_the_index_directories` would then find a state that never had
    a run behind it.
    """
    resolved = settings()
    # Cleared before anything is asked, so that a second call of this function
    # in one process cannot report the refusal of the first one. A run that
    # refuses again writes its own figure four steps down.
    _note_blocked_bytes(0)
    artifact = build_artifact()
    languages = ",".join(resolved.languages)
    expected = expected_versions(artifact.digest, languages)
    drifted = MARKS_A_REBUILD_ANSWERS.intersection(store.version_mismatch(expected))
    if not drifted:
        return NOTHING_TO_REBUILD

    try:
        if resolved.rebuild_fallback == FULL_REINDEX_FALLBACK:
            # The one call of start_rebuild_on_drift in this whole phase, and the
            # one place where it is right. It raises the generation so that every
            # stored verdict goes stale and the crawl the existing banner names
            # actually reads the documents again. Everywhere else in the phase it
            # would be wrong for the same reason, turned around: the band run
            # carries the text over instead of reading it again, so a raised
            # generation would order hours of extraction right behind the pass
            # that made them unnecessary, which is exactly what stamp_after_swap
            # is written to avoid.
            start_rebuild_on_drift(store, expected)
            LOGGER.warning(
                "the rebuild fallback is switched on, so the index is built from the files instead of from itself; "
                "the reindex banner names the command"
            )
            return FALLBACK_TO_FULL_REINDEX

        live = resolved.index_dir
        if not live.is_dir():
            # Nothing to carry over. A container in this state gets its index
            # from the first indexing pass, under the current schema and with
            # every chain of the current set, so there is no drift left to
            # answer either.
            return NO_LIVE_DIRECTORY

        verdict = may_rebuild(live, _new_language_count(store, resolved.languages))
        if not verdict.may_start:
            # may_rebuild has already logged the two figures the refusal rests on.
            # What is published here is the difference between them, because that
            # is the sentence the admin page has to be able to write: not how
            # much the rebuild wants and not how much there is, but how much is
            # missing. The floor is part of the shortfall and not taken out of
            # it, for the reason may_rebuild states: freeing exactly the
            # difference to the need alone would buy a paused indexer.
            _note_blocked_bytes(max(0, verdict.needed_bytes + settings().min_free_bytes - verdict.free_bytes))
            return verdict.reason

        target = live.with_name(live.name + REBUILD_SUFFIX)
        # Step 2 of the order in the module header, and the condition
        # transfer_documents states it cannot check for itself: a document
        # written into the source below the cursor after the band that would have
        # taken it is a document the swap loses. The in flight pass is waited
        # out, which costs one claim of the queue, and the work of the claims
        # behind it waits in Nextcloud rather than being lost (T-18-09-01).
        if not stand_down():
            # The task is still holding the source index, so there is nothing
            # safe left to do this start. Nothing was created, the live
            # directory is untouched, and the finally below arms again.
            LOGGER.warning(
                "the indexing task did not stand down, so no document is carried over and no directory is swapped"
            )
            return POLLER_STILL_WRITING
        # The band size is named here rather than left to the default of the
        # function, because this is the call site that runs in a container: the
        # figure is the memory of one step and the crash granularity of the whole
        # run at the same time, and both of those are decisions of the conductor.
        run = transfer_documents(
            live,
            target,
            artifact.entries,
            resolved.languages,
            band_documents=BAND_DOCUMENTS,
            should_stop=should_stop,
        )
        if should_stop is not None and should_stop():
            # A shutdown, not a fault. The half filled directory is the progress
            # record the next start resumes in, and swapping a directory in while
            # the container is going down would put the one window a crash can be
            # caught in exactly where the crash is.
            return RUN_STOPPED_EARLY
        if not run.complete:
            LOGGER.warning(
                "the new index directory holds %d of %d documents, so nothing is swapped and the next pass resumes",
                run.target_documents,
                run.source_documents,
            )
            return RUN_INCOMPLETE
        # Step 3, immediately in front of the first rename and nowhere else. The
        # swap puts the rebuilt directory under the very name the live one had,
        # so the invalidation branch of the reading side never fires on its own.
        drop_read_side()
        swap_in(target, live)
        stamp_after_swap(store, languages)
        return REBUILD_THROUGH
    finally:
        arm()
