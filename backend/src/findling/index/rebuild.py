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
lives. The swap is plan 18-07, the rule is written down here because it decides
how a run of this module ends: the writer waits for its merging threads, the
reference is dropped, and nothing is handed out that still holds the target.

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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from tantivy import Document, FieldType, Index, Order, Query

from findling.config import settings
from findling.index.open import open_index, open_reader
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
from findling.store.repo import index_bytes

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
    """
    active = tuple(settings().languages if languages is None else languages)
    source = open_index(source_dir, constituents)
    target = open_index(target_dir, constituents)
    reader = open_reader(source)
    cursor = _resume_cursor(target)
    written = 0
    writer = target.writer(heap_size=settings().writer_heap_bytes, num_threads=1)
    try:
        while True:
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
    finally:
        # Whatever ended this loop, the merging threads are waited for and the
        # lock goes back. The swap of plan 18-07 cannot rename a directory a
        # writer still holds, and on Windows it refuses with WinError 5 rather
        # than succeeding quietly.
        writer.wait_merging_threads()
    LOGGER.info("carried %d documents over into the new index directory", written)
    target.reload()
    return RebuildRun(
        documents_written=written,
        source_documents=reader.num_docs,
        target_documents=target.searcher().num_docs,
        complete=counts_match(source, target),
    )
