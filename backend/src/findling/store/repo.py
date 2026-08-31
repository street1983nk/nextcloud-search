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
from collections.abc import Mapping
from pathlib import Path
from typing import Final
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
    """
    connection = sqlite3.connect(path, autocommit=True)
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
