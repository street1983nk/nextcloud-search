"""The one writer of the index: idempotent, batched, and awake to a full volume.

Exactly one IndexWriter exists in this project, and it lives here. tantivy takes
an OS lock on the index directory, so a second one anywhere answers "Failed to
acquire Lockfile: LockBusy" (measured), which reads like a corrupt index and is
two pieces of code that each built their own writer.

*What this module deliberately does not do: recovery.* Measured with kill -9 in
the middle of a write: the index opens again on the state of the last commit
(56000 documents), the .tantivy-writer.lock left behind is meaningless, and a new
writer is granted immediately, because the lock hangs off a file handle the dead
process gave back. There is no cleanup mechanism to build here, and none should
grow. :meth:`IndexBatchWriter.collect_garbage` removes orphaned segment files;
that is housekeeping, not repair. The exception is NFS, where the lock semantics
do not hold.

*Why the batch and not the document is the unit.* Every commit writes a segment
and does an fsync. A commit per document turns the index into thousands of tiny
segments and the disk into the bottleneck, so the commit follows the batch, and
the batch is therefore the crash granularity: whatever was added and not yet
committed comes back through the queue and is written again. That is exactly what
the upsert below is for.

*Field by field, never through keyword arguments.* Measured on tantivy 0.26.0:
a document built from the keyword argument ``file_id=42`` and ``add_integer`` on
an unsigned field both put an I64 into the U64 column, whereupon the indexing
thread panics with "Input type
forbidden. This column has been forced to type U64, received I64(42)" while the
Python call reports success. The failure therefore does not arrive where it was
caused. Field names come from :mod:`findling.index.schema` for the same class of
reason: ``Document.from_dict`` silently drops a name the schema does not know.

*And the same I64 against U64 mismatch decides how the upsert deletes.* The
obvious call, ``delete_documents_by_term("file_id", 42)``, builds an I64 term
from a Python integer, and the U64 column of ``file_id`` holds no such term. It
raises nothing, it deletes nothing, and the second write of a file leaves two
documents in the index. Measured on tantivy 0.26.0, and the deprecated older name
behaves identically, so this is about the value type and not about the name:

    file_id as unsigned, delete by term  -> 2 documents after the second write
    file_id as integer,  delete by term  -> 1 document
    file_id as unsigned, delete by query -> 1 document

The schema keeps the unsigned key, because the field type is written into every
index on every installation while the deletion call is ours to choose. So the
upsert deletes through ``Query.term_query``, which builds the term from the
schema and therefore gets the type right by construction. It is also the sturdier
of the two: it would still be correct if the key ever changed its type.
"""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from tantivy import Document, Index, IndexWriter, Query, Schema

from findling.config import settings
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)

LOGGER = logging.getLogger("findling.index.writer")

# The three answers of a flush. Strings rather than an enum because they travel
# on to the status page and into the operating state, where a closed list of
# readable names is worth more than a type.
FLUSH_COMMITTED: Final = "committed"
FLUSH_NOTHING_PENDING: Final = "nothing_pending"
FLUSH_PAUSED_LOW_DISK: Final = "paused_low_disk"

# The marker tantivy puts into the message when another writer holds the lock.
_LOCK_BUSY: Final = "LockBusy"


@dataclass(frozen=True, slots=True)
class IndexRecord:
    """One file as the index sees it.

    ``body`` is the extracted text, already capped and already decided upon. The
    writer does not judge, it writes: everything that could reject a file has
    happened before a record exists.
    """

    file_id: int
    storage_id: int
    name: str
    title: str
    path: str
    ext: str
    body: str
    mtime: int


@dataclass(frozen=True, slots=True)
class FlushResult:
    """What a flush did, in a form the caller can put on a status page."""

    state: str
    documents: int
    free_bytes: int


class IndexLockedError(RuntimeError):
    """Another writer holds the lock on this index directory.

    Its own type because the caller has to tell it apart from a damaged index:
    the answer to this one is "find the other writer", never "throw the index
    away and build it again".
    """


class IndexBatchWriter:
    """Holds the single IndexWriter of the process and commits in batches.

    The heap comes from :mod:`findling.config`: 50 MB with one thread. tantivy
    refuses anything below 15000000 byte per thread outright, and one thread is
    architecture rather than tuning (IDX-08), because on a 4 GB box the writer
    peak must never meet the OCR peak.
    """

    def __init__(
        self,
        index: Index,
        *,
        directory: Path,
        heap_bytes: int | None = None,
        min_free_bytes: int | None = None,
        batch_files: int | None = None,
        batch_max_bytes: int | None = None,
        index_english: bool | None = None,
    ) -> None:
        resolved = settings()
        self._directory = directory
        self._schema: Schema = index.schema
        self._min_free_bytes = resolved.min_free_bytes if min_free_bytes is None else min_free_bytes
        self._batch_files = resolved.batch_files if batch_files is None else batch_files
        self._batch_max_bytes = resolved.batch_max_bytes if batch_max_bytes is None else batch_max_bytes
        self._index_english = ("en" in resolved.languages) if index_english is None else index_english
        self._pending = 0
        self._pending_bytes = 0
        heap = resolved.writer_heap_bytes if heap_bytes is None else heap_bytes
        try:
            self._writer: IndexWriter | None = index.writer(heap_size=heap, num_threads=1)
        except ValueError as error:
            if _LOCK_BUSY in str(error):
                raise IndexLockedError(
                    "another IndexWriter already holds this index directory; the index itself is intact"
                ) from error
            raise

    @property
    def pending(self) -> int:
        """Documents added since the last committed flush."""
        return self._pending

    @property
    def should_flush(self) -> bool:
        """True once the batch has reached one of the configured caps.

        The byte cap is the one that matters: thirty scanned PDFs are a different
        workload from thirty text files, and the memory the writer holds follows
        the text rather than the file count.
        """
        return self._pending >= self._batch_files or self._pending_bytes >= self._batch_max_bytes

    def add(self, record: IndexRecord) -> None:
        """Write one file into the pending batch, replacing an earlier version.

        The deletion before the insert is what makes a second run harmless: the
        queue redelivers a batch that was interrupted after the commit and before
        the acknowledgement, and without the deletion that redelivery would leave
        the same file in the index twice.
        """
        writer = self._require_open()
        # Through the schema, so the term carries the type of the field. The
        # deletion by term name takes the value as it comes and builds an I64
        # term, which never matches the U64 key and deletes nothing at all; see
        # the module docstring for the measurement. Deletes apply to documents
        # with a lower opstamp only, so the insert right below survives this.
        writer.delete_documents_by_query(Query.term_query(self._schema, FIELD_FILE_ID, record.file_id))

        document = Document()
        document.add_unsigned(FIELD_FILE_ID, record.file_id)
        document.add_unsigned(FIELD_STORAGE_ID, record.storage_id)
        document.add_text(FIELD_NAME, record.name)
        document.add_text(FIELD_TITLE, record.title)
        document.add_text(FIELD_PATH, record.path)
        document.add_text(FIELD_EXT, record.ext)
        # body_de is the only stored copy of the text in the whole system, so it
        # carries the content whatever the language setting says. The setting
        # decides about the second, index only pipeline: with FINDLING_LANGUAGES
        # set to de the English field stays empty and the index shrinks by it.
        document.add_text(FIELD_BODY_DE, record.body)
        if self._index_english:
            document.add_text(FIELD_BODY_EN, record.body)
        document.add_integer(FIELD_MTIME, record.mtime)
        writer.add_document(document)

        self._pending += 1
        self._pending_bytes += len(record.body.encode("utf-8"))

    def flush(self) -> FlushResult:
        """Commit the pending batch, unless the volume is running out of space.

        The free space is checked first and on every flush. A commit on a full
        volume fails with an IO error and the index stays on its last good state,
        but an IO error in the poller is a crash report, while too little disk is
        an operating state somebody can act on. Below the floor nothing is
        written, the batch stays pending and the next flush commits it once there
        is room again.

        The search keeps answering throughout: reading needs no writer, and the
        segments committed so far are untouched.
        """
        writer = self._require_open()
        free_bytes = shutil.disk_usage(self._directory).free
        if free_bytes < self._min_free_bytes:
            LOGGER.warning(
                "index commit paused, free space is below the configured floor of %d byte",
                self._min_free_bytes,
            )
            return FlushResult(FLUSH_PAUSED_LOW_DISK, self._pending, free_bytes)
        if self._pending == 0:
            return FlushResult(FLUSH_NOTHING_PENDING, 0, free_bytes)

        writer.commit()
        committed = self._pending
        self._pending = 0
        self._pending_bytes = 0
        LOGGER.info("committed %d documents", committed)
        return FlushResult(FLUSH_COMMITTED, committed, free_bytes)

    def collect_garbage(self) -> None:
        """Remove segment files no commit refers to any more.

        Housekeeping after a crash, never recovery: the index already opens on
        the last commit by itself, and nothing here brings a document back.
        """
        self._require_open().garbage_collect_files()

    def close(self) -> None:
        """Wait for the merging threads and release the lock. Idempotent.

        This does not commit. Whatever is still pending is lost on purpose: the
        batch is the crash granularity, and a half batch that quietly committed
        itself on shutdown would make the acknowledgement to the queue lie.
        """
        writer = self._writer
        if writer is None:
            return
        self._writer = None
        writer.wait_merging_threads()

    def _require_open(self) -> IndexWriter:
        if self._writer is None:
            raise RuntimeError("this IndexBatchWriter is closed")
        return self._writer
