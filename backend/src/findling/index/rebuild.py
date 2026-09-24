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
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from findling.config import settings
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
