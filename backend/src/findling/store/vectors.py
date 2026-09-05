"""The vector half of the store, three operations wide.

This is the abstraction cut of D-08. sqlite-vec is the vector store of this
project and it is not a safe bet: the last upstream commit is from 2026-05-18,
204 issues are open, and the approximate nearest neighbour issue has been open
for years. Findling exists because ``fulltextsearch`` was left unmaintained, so
the answer to the same risk in its own building block cannot be a paragraph in a
design document. It is this file. Everything the rest of the container may ask
of a vector store is named here, so exchanging sqlite-vec for bit vectors or for
usearch is a rewrite of one module and not of a subsystem. The costs and the
gains of both fallbacks are written down in ``docs/embeddings.md`` (D-10); they
are deliberately not built.

The three operations, plus the two the delete path of plan 06-07 needs:

* :meth:`VectorStore.replace_chunks` writes the vectors of one document as a
  whole and never as a change,
* :meth:`VectorStore.nearest` answers with numbers, never with text,
* :meth:`VectorStore.drop_vectors` and :meth:`VectorStore.forget_all` are the
  two delete paths, and :meth:`VectorStore.chunks_of` is the read back the
  delete paths and the diagnosis need.

**The delete order is the point of replace_chunks.** It deletes before it
inserts, in one transaction, exactly like :meth:`findling.store.repo.Store.replace_acl`
and :meth:`findling.index.writer.IndexBatchWriter.add`. A batch that is
interrupted after the commit and before the acknowledgement is redelivered by
the queue, and without the deletion that redelivery would quietly double the
chunk stock of every document in it.

**Nothing that leaves this module is text.** :class:`Neighbour` carries six
numbers. A snippet is cut in ``snippets_for``, behind ``prefilter_visible`` and
behind the PHP recheck, which is the authority (T-06-15, D-13). The two
character offsets stored next to each vector are what makes a snippet possible
for a purely semantic hit at all.

**This module deliberately does not import** ``findling.config``, the same rule
:mod:`findling.store.repo` states in its own header. Every path arrives as an
argument, which keeps the store testable without an environment, lets the caller
decide where its database lives, and keeps the decision "vectors.db of its own
or a table inside state.db" reversible without a rewrite.

**It also creates no directory.** Gate A forbids the identifier ``mkdir``
outside a short reviewed list, and the volume layout is created by
:func:`findling.store.repo.open_store` anyway. A missing directory is an error
here and not a repair.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from findling.store.repo import enable_wal

_LOG = logging.getLogger(__name__)

_SCHEMA_FILE: Final = Path(__file__).with_name("vectors.sql")

# The width of one vector, and it is the width of the column in vectors.sql.
# intfloat/multilingual-e5-small produces 384 dimensions; a model with another
# width needs a new column, which is why a mismatch below is an error and never
# a silently empty answer.
EMBEDDING_DIMENSIONS: Final = 384

# One byte per component, which is what makes a vector 384 bytes. The name is
# spelled out because it is half of what the embedding mark says: a stock of
# int8 vectors and a stock of bit vectors are not comparable, and a container
# that read one as the other would answer nonsense rather than nothing.
ELEMENT_TYPE: Final = "int8"

# The environment variable the image sets to the copy of vec0 it baked in.
# Read here and handed to open_vectors as an argument with a default, so that a
# path can never arrive from a request: enable_load_extension loads machine code
# into this process, and the only defensible source of that path is the image
# (T-06-14).
VEC0_PATH_ENV: Final = "FINDLING_VEC0_PATH"

# Ten seconds, the same reasoning as in repo.py: the writer holds its
# transactions for milliseconds, so a reader that waits longer than this is not
# contending, it is looking at a stuck writer.
_BUSY_TIMEOUT_MS: Final = 10_000

# Ids per query when a list of them has to be interpolated as placeholders. The
# band exists for the same reason it does in prefilter_visible: the compile time
# variable limit is a build option, our lists are not, and splitting costs
# nothing measurable next to the query that produced them.
_ID_BAND: Final = 1000

# The default ceiling on k. 100 is the window depth per source from D-12, so a
# caller that asks for more than the fusion can use is asking for scan work that
# nothing will read. It is a default and not a law: every call may name its own
# ceiling, which is what keeps the cap visible at the call site instead of
# hidden in here.
DEFAULT_K_MAX: Final = 100


class VectorStoreError(RuntimeError):
    """Base of the two failures a caller of this module has to be able to name."""


class ExtensionUnavailable(VectorStoreError):
    """The sqlite-vec extension is absent or refused to load.

    A state of this container and not a defect: the search path answers it by
    degrading to the lexical half (D-19), and it can only do that if it does not
    have to know which sqlite message means "no vector search on this box".
    """


class DimensionMismatch(VectorStoreError):
    """A vector of the wrong width reached the store or the query.

    Loud on purpose. A query vector that is silently dropped looks exactly like
    "no similar document exists", and that difference would stay invisible until
    somebody measured recall.
    """


@dataclass(frozen=True, slots=True)
class Chunk:
    """One passage of one document, ready to be stored.

    ``embedding`` is the raw int8 vector, :data:`EMBEDDING_DIMENSIONS` bytes
    long. ``char_start`` and ``char_end`` are character offsets into the stored
    body, never byte offsets.
    """

    ordinal: int
    char_start: int
    char_end: int
    embedding: bytes


@dataclass(frozen=True, slots=True)
class Span:
    """Where one stored chunk sits, without its vector and without its text."""

    chunk_id: int
    ordinal: int
    char_start: int
    char_end: int


@dataclass(frozen=True, slots=True)
class Neighbour:
    """One KNN hit: six numbers, and nothing that could carry content.

    The field set is checked by a test rather than trusted. What this class
    carries is the raw material for everything that later leaves the container,
    and the privacy contract of the search path is that a candidate is an id, a
    score and a timestamp (D-14, T-06-15).
    """

    chunk_id: int
    file_id: int
    ordinal: int
    char_start: int
    char_end: int
    distance: float


_INSERT_CHUNK_SQL: Final = "INSERT INTO chunks (file_id, ordinal, char_start, char_end) VALUES (?, ?, ?, ?)"
_INSERT_VECTOR_SQL: Final = "INSERT INTO chunk_vectors (rowid, embedding) VALUES (?, vec_int8(?))"
_CHUNK_IDS_SQL: Final = "SELECT chunk_id FROM chunks WHERE file_id = ?"
_FORGET_CHUNKS_SQL: Final = "DELETE FROM chunks WHERE file_id = ?"
_FORGET_ALL_CHUNKS_SQL: Final = "DELETE FROM chunks"
_FORGET_ALL_VECTORS_SQL: Final = "DELETE FROM chunk_vectors"

# vec0 answers the KNN itself: k is a constraint of the virtual table and not a
# LIMIT, and the join brings the span of the winning chunk along in the same
# query. The ORDER BY is not decoration; without it the order of a joined vec0
# result is the order of the join and not the order of the distance.
_NEAREST_SQL: Final = """
SELECT v.rowid, c.file_id, c.ordinal, c.char_start, c.char_end, v.distance
FROM chunk_vectors AS v
JOIN chunks AS c ON c.chunk_id = v.rowid
WHERE v.embedding MATCH vec_int8(?) AND k = ?
ORDER BY v.distance
"""


def embedding_mark(model: str, *, tokens: int) -> str:
    """The value of the ``embedding_version`` mark for one build.

    Four things decide whether a stored vector still means what this container
    thinks it means, and all four are in here: the model, the quantisation of
    its output, the number of dimensions, and the token cap the chunks were cut
    at. A change to any one of them makes the stored stock incomparable with a
    freshly computed query vector, and the mark is what makes that visible
    instead of turning it into quietly worse results.

    The mark says nothing about the tantivy index and must not: the vector half
    can be rebuilt on its own, which is the whole reason it lives in a file of
    its own. The rule that keeps the two apart is
    :data:`findling.store.repo.VECTOR_ONLY_MARKS`.
    """
    return f"{model}/{ELEMENT_TYPE}/{EMBEDDING_DIMENSIONS}/{tokens}"


def default_extension_path() -> str:
    """Where vec0 lies, and why the order of the two answers is what it is.

    Inside the image the path is a constant of the image and arrives as
    ``FINDLING_VEC0_PATH``, so that is the value the running container has to
    use. Outside the image there is no such constant and the extension of the
    installed wheel is asked for instead, which is what lets the tests of this
    module run on a development machine and in the gates job.

    Neither branch reads anything a request could reach. ``load_extension``
    executes machine code, and the two sources above are the image and the
    locked dependency set (T-06-14).
    """
    from_env = os.environ.get(VEC0_PATH_ENV)
    if from_env:
        return from_env

    import sqlite_vec

    suffix = ".dll" if sys.platform == "win32" else ".so"
    return sqlite_vec.loadable_path() + suffix


def _load_extension(connection: sqlite3.Connection, path: str) -> None:
    """Load vec0 into this connection and take the ability away again.

    Two properties, and both are deliberate. The path is an argument, so nothing
    a request carries can decide which shared object this process loads. And the
    ability to load one is switched off immediately afterwards, so the
    connection does not stay loadable for the rest of its life; it is needed for
    exactly one known library, at exactly one moment.

    The order matters and cost plan 06-01 half an hour: loading is itself a
    change to the connection state, so it has to happen before
    ``PRAGMA query_only``. Doing it the other way round produces a refusal that
    looks like a negative answer to probe A12 and is none.
    """
    try:
        connection.enable_load_extension(True)
        connection.load_extension(path)
        connection.enable_load_extension(False)
    except (AttributeError, sqlite3.Error) as error:
        # AttributeError covers the interpreter that was built without
        # --enable-loadable-sqlite-extensions, which is a different finding from
        # a missing file and the same outcome for the caller. Probe A13 says the
        # image carries the ability; this branch is what happens on a box where
        # it does not.
        raise ExtensionUnavailable(f"the sqlite-vec extension at {path} could not be loaded: {error}") from error


def _connect(path: Path, *, read_only: bool, extension: str) -> sqlite3.Connection:
    """One connection with the pragmas that belong to this database.

    ``autocommit=True`` and ``check_same_thread=False`` for the reasons written
    out at :func:`findling.store.repo._connect`: the two places that need a
    transaction open one explicitly, and the indexing worker does its writes in
    ``asyncio.to_thread`` rather than on the event loop.

    ``PRAGMA foreign_keys`` is not set here, unlike in repo.py, because this
    database has no foreign key: the only reference that exists points into
    another file. Saying ON would suggest an enforcement that cannot exist.
    """
    connection = sqlite3.connect(path, autocommit=True, check_same_thread=False)
    try:
        connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        _load_extension(connection, extension)
        if read_only:
            # Probe A12, answered on amd64 and on arm64 before this schema
            # existed: vec0 KNN runs under this pragma
            # (docs/measurements/2026-09-05-welle0-proben/). So the vector store
            # is read exactly like the rest of the read side, and a bug in the
            # search path cannot change the stock it reads.
            connection.execute("PRAGMA query_only = 1")
        else:
            connection.execute("PRAGMA synchronous = NORMAL")
    except BaseException:
        connection.close()
        raise
    return connection


class VectorStore:
    """The vector stock of one Findling container.

    Instances come from :func:`open_vectors`, never from this constructor
    directly: whether a caller may write is decided by the connection it holds,
    and that decision belongs at the call site that opens the file.
    """

    def __init__(self, connection: sqlite3.Connection, *, journal_mode: str) -> None:
        self._conn = connection
        self.journal_mode = journal_mode

    def close(self) -> None:
        """Release the connection. Idempotent, so a double close is harmless."""
        self._conn.close()

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        """One explicit transaction. Validation belongs before it, never inside."""
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        self._conn.execute("COMMIT")

    def replace_chunks(self, file_id: int, chunks: Sequence[Chunk]) -> None:
        """Write the vectors of one document as a whole, never as a change.

        Delete followed by insert in one transaction, the form
        :meth:`findling.store.repo.Store.replace_acl` established. The queue
        redelivers a batch that was interrupted after the commit and before the
        acknowledgement, and without the deletion that redelivery would leave
        every chunk of this document in the stock twice. An incremental variant
        would be wrong forever after the first lost message and nothing in the
        system would notice.

        An empty list is not an error: it means this document has no vectors any
        more, and it has to be able to lose them through the same call that
        would have written them.

        The width of every vector is checked before the transaction opens, so a
        refused batch leaves no trace, no half written stock and no open
        transaction.
        """
        for chunk in chunks:
            _check_width(chunk.embedding, "stored vector")

        with self._transaction():
            self._forget_file(file_id)
            for chunk in chunks:
                cursor = self._conn.execute(
                    _INSERT_CHUNK_SQL, (file_id, chunk.ordinal, chunk.char_start, chunk.char_end)
                )
                # One row at a time rather than executemany, because the rowid
                # SQLite assigns here is the key the vector is stored under. A
                # derived id (file_id times a cap plus the ordinal) would be
                # faster and would turn the cap of D-01, which is a setting an
                # operator may raise, into a silent collision between two
                # documents.
                self._conn.execute(_INSERT_VECTOR_SQL, (cursor.lastrowid, chunk.embedding))

    def drop_vectors(self, file_id: int) -> int:
        """Take one document out of the vector stock, return how many chunks it had.

        An unknown file id is not an error, which is what lets the delete path
        call this for every removed, renamed or unshared document without asking
        first. Named drop_vectors because gate A forbids the identifier
        ``delete`` in every module of this package.
        """
        with self._transaction():
            return self._forget_file(file_id)

    def forget_all(self) -> None:
        """Empty both tables, for the rebuild path.

        A rebuild that left the old vectors in place would keep answering
        semantically out of a stock that belongs to another model, and the
        answers would look ordinary while being wrong.
        """
        with self._transaction():
            self._conn.execute(_FORGET_ALL_VECTORS_SQL)
            self._conn.execute(_FORGET_ALL_CHUNKS_SQL)

    def nearest(self, vector: bytes, k: int, *, k_max: int = DEFAULT_K_MAX) -> list[Neighbour]:
        """The k nearest chunks, ascending by distance, as numbers.

        **What the cap is and what it is not.** ``k_max`` bounds the answer, and
        it is an argument so that the ceiling is visible where the call is made.
        What it deliberately does not claim to bound is the number of rows
        visited: sqlite-vec scans the whole stock for every query, and no
        parameter of this query changes that. Capping the visited rows is
        precisely what the two documented fallbacks buy (bit vectors read an
        eighth of the bytes, usearch visits a logarithmic share of the rows),
        and neither is built. The reason it is affordable today is measured: at
        the 100.136 chunks of the 1.024 token cap a full scan reads 38,4 MB and
        costs 37,8 ms p95 warm and 153,5 ms p95 cold on native aarch64, against
        a budget of 300 ms per round.

        A width other than :data:`EMBEDDING_DIMENSIONS` is refused rather than
        answered with an empty list, and ``k`` below one is refused as well: an
        answer of nothing would be indistinguishable from an honest miss.
        """
        _check_width(vector, "query vector")
        if k < 1:
            raise ValueError(f"k has to be at least 1, not {k}")
        if k > k_max:
            _LOG.warning("a query asked for %d neighbours and was capped at %d", k, k_max)
            k = k_max

        rows = self._conn.execute(_NEAREST_SQL, (vector, k))
        return [
            Neighbour(
                chunk_id=int(row[0]),
                file_id=int(row[1]),
                ordinal=int(row[2]),
                char_start=int(row[3]),
                char_end=int(row[4]),
                distance=float(row[5]),
            )
            for row in rows
        ]

    def chunks_of(self, file_ids: Sequence[int]) -> dict[int, list[Span]]:
        """The spans of the named documents, per document and in ordinal order.

        The read back the delete paths and the diagnosis need, and the way a
        semantic hit finds its place in the stored text. Documents without
        vectors are absent from the answer rather than present with an empty
        list, so a caller can tell "no chunks" from "not asked about".

        Banded like :meth:`findling.store.repo.Store.prefilter_visible`, and for
        the same reason: the caller asks about a page of files, most of which
        carry no vectors at all.
        """
        if not file_ids:
            # No ids, no question. Worth its own branch: an empty IN list is a
            # syntax error in SQL, and the delete path reaches this case on
            # every round that had nothing to remove.
            return {}

        spans: dict[int, list[Span]] = {}
        for start in range(0, len(file_ids), _ID_BAND):
            band = file_ids[start : start + _ID_BAND]
            placeholders = ",".join("?" * len(band))
            rows = self._conn.execute(
                # The parameters are placeholders, all of them. Only their
                # number is interpolated, and it is a count this function
                # computed.
                f"SELECT chunk_id, file_id, ordinal, char_start, char_end FROM chunks WHERE file_id IN ({placeholders}) ORDER BY file_id, ordinal",  # noqa: E501, S608
                tuple(band),
            )
            for row in rows:
                spans.setdefault(int(row[1]), []).append(
                    Span(chunk_id=int(row[0]), ordinal=int(row[2]), char_start=int(row[3]), char_end=int(row[4]))
                )
        return spans

    def chunk_count(self) -> int:
        """How many chunks the stock holds. The status page half of the answer."""
        row = self._conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
        return int(row[0]) if row else 0

    def vector_count(self) -> int:
        """How many vectors the stock holds.

        Two numbers that have to agree, and they are counted separately for
        exactly that reason: the tables live in two storage engines, and a
        divergence between them is the shape a broken delete path has.
        """
        row = self._conn.execute("SELECT COUNT(*) FROM chunk_vectors").fetchone()
        return int(row[0]) if row else 0

    def _forget_file(self, file_id: int) -> int:
        """Remove chunks and vectors of one document. Caller holds the transaction."""
        ids = [int(row[0]) for row in self._conn.execute(_CHUNK_IDS_SQL, (file_id,))]
        for start in range(0, len(ids), _ID_BAND):
            band = ids[start : start + _ID_BAND]
            placeholders = ",".join("?" * len(band))
            self._conn.execute(
                # Same rule as above: placeholders only, and the number of them
                # is a count this method computed.
                f"DELETE FROM chunk_vectors WHERE rowid IN ({placeholders})",  # noqa: S608
                tuple(band),
            )
        self._conn.execute(_FORGET_CHUNKS_SQL, (file_id,))
        return len(ids)


def _check_width(vector: bytes, what: str) -> None:
    """Refuse a vector that is not exactly one int8 embedding wide."""
    if len(vector) != EMBEDDING_DIMENSIONS:
        raise DimensionMismatch(f"the {what} is {len(vector)} bytes wide, expected {EMBEDDING_DIMENSIONS}")


def open_vectors(
    path: Path | str,
    *,
    read_only: bool = False,
    extension_path: str | None = None,
) -> VectorStore:
    """Open the vector database, creating it when it is absent.

    Applies vectors.sql on every call, which is free on an existing database
    because every statement is IF NOT EXISTS, exactly like
    :func:`findling.store.repo.open_store` does with schema.sql.

    ``read_only=True`` refuses a missing file instead of creating one. sqlite
    would happily make an empty database here, and every semantic search would
    then answer "nothing similar" rather than "the vector stock is gone", which
    is the difference between a fault that is noticed and one that is not. It
    also applies no schema: the read side never creates anything.

    ``extension_path`` is the one dial that decides which shared object this
    process loads. It defaults to :func:`default_extension_path`, which reads
    the image constant; a path from a request never reaches it (T-06-14).
    """
    database = Path(path)
    if read_only:
        if not database.exists():
            raise FileNotFoundError(f"vector database {database} does not exist")
        connection = _connect(database, read_only=True, extension=extension_path or default_extension_path())
        row = connection.execute("PRAGMA journal_mode").fetchone()
        return VectorStore(connection, journal_mode=str(row[0]).lower() if row else "unknown")

    if not database.parent.is_dir():
        # No mkdir here on purpose (gate A, and the module header). The volume
        # layout is created by open_store, and a vector database in a directory
        # that does not exist is a wiring error rather than something to repair.
        raise FileNotFoundError(f"the directory of the vector database {database} does not exist")

    connection = _connect(database, read_only=False, extension=extension_path or default_extension_path())
    journal_mode = enable_wal(connection)
    connection.executescript(_SCHEMA_FILE.read_text(encoding="utf-8"))
    return VectorStore(connection, journal_mode=journal_mode)
