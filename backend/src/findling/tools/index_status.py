"""The operating state of one container as JSON, without an authenticated header.

Why this exists next to the HTTP status route: that route sits behind the signed
AppAPI header, so a waiting loop in a workflow cannot ask it without building a
signature first. This tool reads the very same numbers over the read only
connection of the state database, which makes it usable from a shell script and,
more importantly, keeps the proof honest.

That second half is the actual reason. The kill-resume job of plan 02-13 asserts
that a hard kill costs no progress, and a proof that reads a log line this project
writes itself proves the log line. Everything printed below comes out of the
database and out of the index, so the assertion runs against the data the app
actually holds.

``docs`` is the one number that does **not** come from the database. It is the
document count of the tantivy index, and the comparison of ``docs`` against
``indexed`` is what makes a doubled document visible: the two are equal only when
the upsert did its job, and they are read from two different places on purpose.

A missing database is not an error. It is a container that has not indexed
anything yet, which is precisely the state the first round of a waiting loop
finds, so the answer is zeroes and exit 0.

Run it with::

    uv run python -m findling.tools.index_status --db "$APP_PERSISTENT_STORAGE/state.db"
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from findling.index.open import open_index
from findling.store.repo import STATE_REASONS, Store, open_read_only

# The layout of the persistent volume, mirrored from findling.config: the state
# database and the index directory sit next to each other. Mirrored rather than
# imported, because this tool is pointed at a path by hand and must not depend on
# the environment of a container it is looking at from the outside.
INDEX_DIRNAME: Final = "index"

# tantivy writes this file when it creates an index. Its absence is how a volume
# that has never been indexed is told apart from a broken one, and it is also what
# keeps this tool from creating an empty index directory as a side effect of a
# question.
INDEX_MARKER: Final = "meta.json"

# The key an end state without a reason appears under. The breakdown travels as
# JSON, JSON object keys are strings, and a null key would arrive as the four
# letters "null" without anybody deciding that.
NO_REASON: Final = "none"

# Version marks, mapped from the storage names to the names of the report. The
# report speaks camelCase because it is read by a workflow and by the PHP side,
# the meta table speaks snake_case because it is a database.
_VERSION_KEYS: Final = {
    "schemaVersion": "schema_version",
    "indexVersion": "index_version",
    "analyzerVersion": "analyzer_version",
    "wordlistHash": "wordlist_hash",
    "tantivyVersion": "tantivy_version",
}

# A version mark this tool could not read at all. Deliberately different from
# repo.UNKNOWN_VERSION ("unknown"), which means "the database has no value for
# this": an empty string here says the database was not there to be asked.
_NO_VALUE: Final = ""


def index_directory(db: Path, override: Path | None) -> Path:
    """Return where the index lies: next to the database unless it is named."""
    return override if override is not None else db.parent / INDEX_DIRNAME


def empty_report() -> dict[str, object]:
    """Return the report of a container that has not indexed anything.

    Every key of a full report appears here as well. A status output that leaves
    a counter out when it is zero makes "nothing failed" and "the counter is
    broken" look identical, and telling those two apart is the whole point.
    """
    report: dict[str, object] = {
        "databaseFound": False,
        "indexFound": False,
        "docs": 0,
        "aclRows": 0,
        "reasons": {state: {} for state in STATE_REASONS},
    }
    report.update(dict.fromkeys(STATE_REASONS, 0))
    report.update(dict.fromkeys(_VERSION_KEYS, _NO_VALUE))
    return report


def documents_in_index(directory: Path) -> tuple[int, bool]:
    """Return the document count of the index and whether there is one at all.

    Reading needs no lock: tantivy locks the index directory for the writer, and
    a searcher is a snapshot of the last commit. So this may run while the poller
    is writing, which is exactly what the waiting loop does.
    """
    if not (directory / INDEX_MARKER).is_file():
        return 0, False
    # The constituent list decides how German text is split and therefore what a
    # query matches. Nothing here queries, it counts, so the empty list is both
    # correct and cheap: building the real automaton costs 0.44 s and roughly
    # 23 MB, and a waiting loop calls this every few seconds.
    index = open_index(directory, ())
    return index.searcher().num_docs, True


def _breakdown(store: Store) -> dict[str, dict[str, int]]:
    """Reasons per state, with the reason-less end state under a readable key."""
    return {
        state: {NO_REASON if reason is None else str(reason): total for reason, total in reasons.items()}
        for state, reasons in store.reasons_by_state().items()
    }


def collect(db: Path, index_dir: Path) -> dict[str, object]:
    """Return the whole report for one volume, zeroes included."""
    report = empty_report()
    report["docs"], report["indexFound"] = documents_in_index(index_dir)

    if not db.is_file():
        return report

    store = open_read_only(db)
    try:
        report["databaseFound"] = True
        report.update(store.counts())
        report["reasons"] = _breakdown(store)
        report["aclRows"] = store.acl_rows()
        meta = store.read_meta()
        for name, key in _VERSION_KEYS.items():
            report[name] = meta.get(key, _NO_VALUE)
    finally:
        store.close()
    return report


def main(argv: Sequence[str] | None = None) -> int:
    """Print the report and return an exit code.

    Always 0 for a state this tool can read, including the empty one. The waiting
    loops of the resilience workflow run this on every round and decide on the
    numbers; an exit code that turned "nothing indexed yet" into a failure would
    make the very first round of such a loop red.
    """
    parser = argparse.ArgumentParser(description="Report the operating state of one Findling volume as JSON.")
    parser.add_argument("--db", type=Path, required=True, help="path of state.db inside APP_PERSISTENT_STORAGE")
    parser.add_argument("--index", type=Path, default=None, help="index directory, by default next to the database")
    args = parser.parse_args(argv)

    report = collect(args.db, index_directory(args.db, args.index))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
