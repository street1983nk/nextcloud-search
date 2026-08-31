"""The one module in Findling that contains SQL.

Everything the container knows about its own operating state lives here: which
file carries which verdict, which user may see which file, and which versions the
index was built with. Three properties are worth stating before the first line of
code, because each of them is an answer to a way this class of app has failed
before.

**There is no pending state and no work queue.** A file is either judged
(``indexed``, ``skipped`` or ``failed``) or it is not in the ``files`` table at
all. What is still to do lives in Nextcloud, and how far the crawl got lives in
the argument of the next background job. The obvious extension of this module
would be a ``pending`` row, and it would create a second place claiming to know
the backlog. After the first hard kill the two would disagree, and the app would
be back at the failure it was written to avoid: documents that are silently never
indexed.

**Reasons come from a closed list.** ``state`` and ``reason`` are validated
against :data:`STATE_REASONS` on every write. These values are rendered on an
admin page in phase 4, and a free text field is the shortest path to a file name
appearing in a place where no file name may appear.

**The prefilter is not a security boundary.** See :meth:`Store.prefilter_visible`.

This module deliberately does not import ``findling.config``. Every path arrives
as an argument, which keeps the store testable without an environment and lets
the callers decide where their database lives.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final
from uuid import uuid4

_LOG = logging.getLogger(__name__)

_SCHEMA_FILE: Final = Path(__file__).with_name("schema.sql")

# Bumped when schema.sql changes in a way that an existing database cannot simply
# absorb. It is a mark, not a migration: this module reports the difference and
# lets the caller decide, because "reset a subset" and "throw the index away" are
# not decisions a storage layer gets to make.
SCHEMA_VERSION: Final = "1"

# The value a version mark carries when nobody named it. It compares unequal to
# every real version, so an index built by an analyzer that never identified
# itself shows up as a mismatch on the next start. That is the intended answer:
# an unnamed analyzer is exactly as trustworthy as a wrong one.
UNKNOWN_VERSION: Final = "unknown"

# Written once, when the database is created, and never touched again. A caller
# that knows better hands its values to open_store; anything it leaves out gets
# the placeholder above.
_DEFAULT_META: Final[Mapping[str, str]] = {
    "schema_version": SCHEMA_VERSION,
    "index_version": "0",
    "analyzer_version": UNKNOWN_VERSION,
    "wordlist_hash": UNKNOWN_VERSION,
    "tantivy_version": UNKNOWN_VERSION,
}

# Ten seconds. The writer holds its transactions for milliseconds, so a reader
# that waits longer than this is not contending, it is looking at a stuck writer.
_BUSY_TIMEOUT_MS: Final = 10_000

# Candidates per prefilter query. SQLITE_LIMIT_VARIABLE_NUMBER is 250000 in the
# build this was measured against, so the old 999 rule does not apply and a band
# of 1000 is not needed to stay legal. It is here so that the function does not
# depend on a build option at all: the limit is compile time, our candidate lists
# are not, and splitting costs nothing measurable next to the Tantivy query that
# produced them.
_ACL_BAND: Final = 1000

# The closed list, taken from the measured taxonomy in the phase research. A file
# is judged exactly once and carries one of these pairs; there is no fourth state,
# because a file that is still to be done has no row at all.
#
# The split between skipped and failed is about meaning, not about severity:
# skipped is "we decided not to index this", failed is "we wanted to and could
# not". Only failed is an error on the status page, and only skipped/no_text_layer
# is the list phase 3 reads to learn which PDFs need OCR. Getting a file into the
# wrong bucket makes both numbers lie, which is why record refuses to guess.
#
# Adding a reason is a deliberate act: it shows up in the admin UI and needs a
# German label there. Reasons are never composed at runtime and never carry a
# path, a file name or an exception message.
STATE_REASONS: Final[Mapping[str, frozenset[str | None]]] = {
    "indexed": frozenset({None, "truncated"}),
    "skipped": frozenset(
        {
            "too_large",
            "mime_not_allowed",
            "encrypted",
            "no_text_layer",  # the bridge to phase 3: these are the OCR candidates
            "empty_text",
            "too_many_cells",
            "gone",
        }
    ),
    "failed": frozenset(
        {
            "empty_file",
            "corrupt",
            "xml_invalid",
            "encoding_unknown",
            "timeout",
            "out_of_memory",
            "gateway_error",
            "repeatedly_stuck",
        }
    ),
}


# One upsert for both cases. A second attempt on the same file overwrites the
# verdict and the metadata, because the crawl may have handed over a moved or
# renamed file, and raises attempts, which is the only counter that must survive
# the overwrite.
_RECORD_SQL: Final = """
INSERT INTO files (file_id, storage_id, root_id, path, title, mime, size, mtime,
                   content_hash, text_chars, state, reason, attempts, indexed_at, index_version)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
ON CONFLICT(file_id) DO UPDATE SET
    storage_id    = excluded.storage_id,
    root_id       = excluded.root_id,
    path          = excluded.path,
    title         = excluded.title,
    mime          = excluded.mime,
    size          = excluded.size,
    mtime         = excluded.mtime,
    content_hash  = excluded.content_hash,
    text_chars    = excluded.text_chars,
    state         = excluded.state,
    reason        = excluded.reason,
    attempts      = files.attempts + 1,
    indexed_at    = excluded.indexed_at,
    index_version = excluded.index_version
"""

# deleted_at is NULL throughout phase 2. The condition is here so that the phase 3
# tombstone cannot make a deleted file look unchanged and therefore untouchable.
_IS_UNCHANGED_SQL: Final = """
SELECT 1 FROM files
 WHERE file_id = ? AND content_hash = ? AND state = 'indexed'
   AND index_version = ? AND deleted_at IS NULL
"""

_RECORD_MOUNT_SQL: Final = """
INSERT INTO mounts (storage_id, root_id, cursor_file_id, files_seen, updated_at)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(storage_id) DO UPDATE SET
    root_id        = excluded.root_id,
    cursor_file_id = excluded.cursor_file_id,
    files_seen     = excluded.files_seen,
    updated_at     = excluded.updated_at
"""


@dataclass(frozen=True, slots=True)
class FileMeta:
    """What the crawl knows about a file before anybody looked inside it.

    Carried separately from the verdict because it comes from a different source:
    these values are what Nextcloud handed over with the queue entry, while state
    and reason are what this container concluded.
    """

    storage_id: int
    root_id: int
    path: str
    title: str | None
    mime: str
    size: int
    mtime: int


def enable_wal(connection: sqlite3.Connection) -> str:
    """Ask for WAL, return the journal mode the database actually took.

    WAL is what lets the search path read while the poller writes. It needs
    shared memory, though, and on some network file systems the request falls
    back to DELETE without any error. The fallback costs concurrency and nothing
    else, so this warns and returns; a container that refused to start there
    would be the worse outcome by a wide margin.
    """
    row = connection.execute("PRAGMA journal_mode = WAL").fetchone()
    mode = str(row[0]).lower() if row else "unknown"
    if mode != "wal":
        _LOG.warning(
            "journal_mode is %r instead of wal; search and indexing will block each other. "
            "The usual cause is a file system without shared memory support.",
            mode,
        )
    return mode


def _connect(path: Path, *, read_only: bool) -> sqlite3.Connection:
    """Open one connection with the pragmas that belong to this database.

    ``autocommit=True`` means sqlite3 does not invent transactions around single
    statements; the two places that need one open it explicitly. Every pragma
    below is per connection and therefore set here rather than in schema.sql.

    ``check_same_thread=False`` is what lets the indexing worker do its writes in
    ``asyncio.to_thread`` instead of on the event loop. Blocking SQLite work in
    the loop is a ``/heartbeat`` that hangs while ``/enabled`` still answers, and
    the thread a coroutine is resumed on is not the thread it started on, so the
    default guard refuses the second call of a pass. The guard is a Python side
    assertion and not the actual safety property: CPython reports
    ``sqlite3.threadsafety == 3`` for this build, which means the underlying
    library serialises access itself. On top of that there is exactly one writer
    in the process (IDX-08), and its thread hops are awaited one after another, so
    two threads never hold this connection at the same moment. A guard test in
    ``tests/test_store_repo.py`` fails should a build ever report less than
    serialised mode.
    """
    connection = sqlite3.connect(path, autocommit=True, check_same_thread=False)
    connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA foreign_keys = ON")
    if read_only:
        # The structural half of the read/write split. A bug in the search path
        # cannot change the operating state, whatever it tries.
        connection.execute("PRAGMA query_only = 1")
    else:
        connection.execute("PRAGMA synchronous = NORMAL")
    return connection


class Store:
    """The operating state of one Findling container.

    Instances come from :func:`open_store` or :func:`open_read_only`, never from
    this constructor directly: which connection a caller holds decides whether it
    can write, and that decision belongs at the call site that opens the file.
    """

    def __init__(self, connection: sqlite3.Connection, *, journal_mode: str) -> None:
        self._conn = connection
        self.journal_mode = journal_mode

    def close(self) -> None:
        """Release the connection. Idempotent, so a double close is harmless."""
        self._conn.close()

    def read_meta(self) -> dict[str, str]:
        """All version marks and provenance values as one mapping."""
        return {str(key): str(value) for key, value in self._conn.execute("SELECT key, value FROM meta")}

    def write_meta(self, key: str, value: str) -> None:
        """Set one meta value, overwriting an existing one."""
        self._conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    def version_mismatch(self, expected: Mapping[str, str]) -> list[str]:
        """Names of the marks whose stored value differs from the expected one.

        This is the counter-measure to the quietest failure mode of a search app:
        a container update brings a different word list or a different Tantivy
        release, queries are tokenised differently than the index was, and hits
        disappear with nothing anywhere saying why. A mark that was never written
        counts as diverging, because an index whose analyzer never identified
        itself cannot be shown to match the current one.

        It decides nothing. Whether the answer is a full reindex or resetting one
        storage is a policy question, and a storage layer is the wrong place for
        it.
        """
        stored = self.read_meta()
        return [key for key, value in expected.items() if stored.get(key) != value]

    @property
    def index_version(self) -> int:
        """The index generation new verdicts are stamped with.

        Read through rather than cached, so a caller that raises the version at
        runtime does not have to reopen the store for the change to take effect.
        """
        row = self._conn.execute("SELECT value FROM meta WHERE key = 'index_version'").fetchone()
        return int(row[0]) if row else 0

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

    def record(
        self,
        file_id: int,
        meta: FileMeta,
        state: str,
        reason: str | None = None,
        *,
        content_hash: str | None = None,
        text_chars: int = 0,
    ) -> None:
        """Write the verdict for one file, rejecting anything outside the list.

        The pair of state and reason is checked against :data:`STATE_REASONS`
        before a transaction is opened, so a rejected write leaves no trace and no
        open transaction behind. A free text reason is refused on purpose: these
        strings reach an admin page, and the cheapest way for a file name to end
        up there is a caller that passes an exception message.

        ``attempts`` counts every write, which is the data the give-up rule after
        three tries runs on. There is no state transition to manage: a file is
        judged once per attempt, and a file that is still to be done has no row
        here at all.
        """
        allowed = STATE_REASONS.get(state)
        if allowed is None:
            raise ValueError(f"unknown state {state!r}, expected one of {sorted(STATE_REASONS)}")
        if reason not in allowed:
            raise ValueError(f"reason {reason!r} does not belong to state {state!r}")

        with self._transaction():
            self._conn.execute(
                _RECORD_SQL,
                (
                    file_id,
                    meta.storage_id,
                    meta.root_id,
                    meta.path,
                    meta.title,
                    meta.mime,
                    meta.size,
                    meta.mtime,
                    content_hash,
                    text_chars,
                    state,
                    reason,
                    int(time.time()),
                    self.index_version,
                ),
            )

    def file_row(self, file_id: int) -> dict[str, Any] | None:
        """The whole row for one file, or None when it has never been judged."""
        cursor = self._conn.execute("SELECT * FROM files WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return {column[0]: value for column, value in zip(cursor.description, row, strict=True)}

    def counts(self) -> dict[str, int]:
        """Files per state, always all three keys, zeros included.

        The zeros are the point. A status output that omits an empty state makes
        "no failures" and "the counter is broken" look identical, and telling
        those two apart is the entire promise this app makes.
        """
        counters = dict.fromkeys(STATE_REASONS, 0)
        for state, total in self._conn.execute("SELECT state, COUNT(*) FROM files GROUP BY state"):
            counters[str(state)] = int(total)
        return counters

    def reasons_by_state(self) -> dict[str, dict[str | None, int]]:
        """The breakdown phase 4 builds its error list from.

        Same rule as :meth:`counts`: every state appears, an empty one as an empty
        mapping.
        """
        breakdown: dict[str, dict[str | None, int]] = {state: {} for state in STATE_REASONS}
        for state, reason, total in self._conn.execute(
            "SELECT state, reason, COUNT(*) FROM files GROUP BY state, reason"
        ):
            breakdown.setdefault(str(state), {})[reason] = int(total)
        return breakdown

    def is_unchanged(self, file_id: int, content_hash: str | None) -> bool:
        """True when this file is already indexed with this content and generation.

        The cheap exit of the indexing loop: same bytes, nothing to do, acknowledge
        the queue entry and move on. An unknown hash answers False, because "we
        cannot tell" has to cost work rather than silently skip a document.

        The generation is part of the question on purpose. Without it, raising
        ``index_version`` after an analyzer change would skip every single file
        the bump was made to rebuild.
        """
        if not content_hash:
            return False
        row = self._conn.execute(_IS_UNCHANGED_SQL, (file_id, content_hash, self.index_version)).fetchone()
        return row is not None

    def reset_for_reindex(self, index_version: int) -> int:
        """Forget every verdict older than this generation, return how many.

        Forgetting is the reset: absence means "not judged yet", and the queue
        that hands the file back lives in Nextcloud, so the next crawl picks it up
        without a state in this database standing in for it.

        Rows of a newer generation are left alone. A downgrade is not a stale
        index but an incompatible one, and that decision belongs to the caller
        holding the answer of :meth:`version_mismatch`, not here.
        """
        with self._transaction():
            cursor = self._conn.execute("DELETE FROM files WHERE index_version < ?", (index_version,))
        return cursor.rowcount

    def record_mount(self, storage_id: int, root_id: int, cursor: int, files_seen: int) -> None:
        """Mirror the crawl progress of one mount for the status display.

        A mirror and nothing more. The original of the cursor is the last file id
        in the argument of the next crawl job in Nextcloud, so losing this table
        loses a number on a page and not a single document.
        """
        with self._transaction():
            self._conn.execute(_RECORD_MOUNT_SQL, (storage_id, root_id, cursor, files_seen, int(time.time())))

    def replace_acl(self, file_id: int, uids: Iterable[str]) -> None:
        """Write the permissions of one file as a whole, never as a change.

        DELETE followed by INSERT in one transaction. The crawl and the events
        both transport the target state, so a delivery that gets lost costs one
        round of staleness and repairs itself with the next one. An incremental
        variant would be wrong forever after the first lost message, and nothing
        in the system would ever notice.
        """
        rows = [(uid, file_id) for uid in dict.fromkeys(uids)]
        with self._transaction():
            self._conn.execute("DELETE FROM acl WHERE file_id = ?", (file_id,))
            self._conn.executemany("INSERT INTO acl (uid, file_id) VALUES (?, ?)", rows)

    def prefilter_visible(self, uid: str, file_ids: Sequence[int]) -> set[int]:
        """Drop candidates the user almost certainly cannot see.

        This is a speed-up, never a security boundary. It over-approximates on
        team folders with advanced permissions, because IUserMountCache resolves
        mounts and not per folder rules. The only authority is the PHP recheck
        through getUserFolder()->getFirstNodeById(), and it runs before any
        snippet exists.

        The direction is fixed: given candidates, which of them are permitted.
        Materialising every file a user may see is the inverse, and it is the
        documented anti-pattern of the app this one replaces, because its cost
        grows with the instance rather than with the query.

        The result is a set. Ordering is the caller's business and comes from the
        Tantivy score, which is why there is no ORDER BY and no join against
        ``files`` on this path.
        """
        if not file_ids:
            # No candidates, no question. Worth its own branch: an empty IN list
            # is a syntax error in SQL, and the search path hits this case on
            # every query that Tantivy answers with nothing.
            return set()

        visible: set[int] = set()
        for start in range(0, len(file_ids), _ACL_BAND):
            band = file_ids[start : start + _ACL_BAND]
            placeholders = ",".join("?" * len(band))
            rows = self._conn.execute(
                # The parameters are placeholders, all of them. Only their number
                # is interpolated, and it is a count this function computed.
                f"SELECT file_id FROM acl WHERE uid = ? AND file_id IN ({placeholders})",  # noqa: S608
                (uid, *band),
            )
            visible.update(int(row[0]) for row in rows)
        return visible

    def forget_acl(self, file_id: int) -> int:
        """Drop every permission row of one file, return how many there were.

        Goes through the acl_file index. The composite primary key leads with the
        uid and cannot answer this question, so without that index a single
        deleted file would scan the whole table.
        """
        with self._transaction():
            cursor = self._conn.execute("DELETE FROM acl WHERE file_id = ?", (file_id,))
        return cursor.rowcount

    def acl_rows_per_document(self) -> float:
        """Average permission rows per document, 0.0 while the table is empty.

        The figure the status page uses to make the size of this table
        understandable: measured at 3.36 on a hundred thousand files and fifty
        users, which is where the 12 MB estimate comes from. A value that grows
        far beyond it means the crawl is writing deltas instead of target states.
        """
        row = self._conn.execute("SELECT COUNT(*), COUNT(DISTINCT file_id) FROM acl").fetchone()
        total, documents = int(row[0]), int(row[1])
        return total / documents if documents else 0.0

    def trace(self, callback: Callable[[str], object] | None) -> None:
        """Report every statement this connection runs, or stop reporting.

        The prefilter has two properties that cannot be seen in its result: an
        empty candidate list never reaches the database, and a long one is split
        into bands instead of relying on the parameter limit of this SQLite
        build. Both are properties of the call pattern, so the tests observe the
        calls.
        """
        self._conn.set_trace_callback(callback)

    def mount_rows(self) -> list[dict[str, Any]]:
        """The mirrored crawl progress of every known mount."""
        rows = self._conn.execute(
            "SELECT storage_id, root_id, cursor_file_id, files_seen FROM mounts ORDER BY storage_id"
        )
        return [
            {"storage_id": storage_id, "root_id": root_id, "cursor_file_id": cursor_file_id, "files_seen": files_seen}
            for storage_id, root_id, cursor_file_id, files_seen in rows
        ]


def open_store(path: Path | str, *, meta: Mapping[str, str] | None = None) -> Store:
    """Open the state database for writing, creating it when it is absent.

    Applies schema.sql on every call, which is free on an existing database
    because every statement is IF NOT EXISTS, and fills in the meta keys that are
    missing. Values that are already there are never overwritten: the difference
    between the stored analyzer version and the running one is the evidence
    :meth:`Store.version_mismatch` reports, and an open that silently repaired it
    would destroy that evidence before anybody looked.

    There is exactly one of these connections in a running container, held by the
    poller. Everything else reads through :func:`open_read_only`.
    """
    database = Path(path)
    database.parent.mkdir(parents=True, exist_ok=True)

    connection = _connect(database, read_only=False)
    journal_mode = enable_wal(connection)
    connection.executescript(_SCHEMA_FILE.read_text(encoding="utf-8"))

    store = Store(connection, journal_mode=journal_mode)
    _seed_meta(store, meta)
    return store


def _seed_meta(store: Store, meta: Mapping[str, str] | None) -> None:
    """Write the meta keys that are missing, touch none that are present."""
    stored = store.read_meta()
    seed = dict(_DEFAULT_META)
    seed.update(meta or {})
    # Provenance, generated rather than defaulted: created_at dates the database
    # in a support case, instance_id tells two copies of the same volume apart.
    seed.setdefault("created_at", str(int(time.time())))
    seed.setdefault("instance_id", uuid4().hex)

    for key, value in seed.items():
        if key not in stored:
            store.write_meta(key, value)


def open_read_only(path: Path | str) -> Store:
    """Open the state database for the search path, writes disabled.

    ``PRAGMA query_only = 1`` makes the read/write split structural instead of a
    review habit: an INSERT over this connection fails, whatever code issues it.

    A missing file raises instead of being created. sqlite would happily make an
    empty database here, and every search would then answer "nothing found"
    rather than "the state is gone", which is the difference between a bug that
    is noticed and one that is not.
    """
    database = Path(path)
    if not database.exists():
        raise FileNotFoundError(f"state database {database} does not exist")

    connection = _connect(database, read_only=True)
    row = connection.execute("PRAGMA journal_mode").fetchone()
    return Store(connection, journal_mode=str(row[0]).lower() if row else "unknown")
