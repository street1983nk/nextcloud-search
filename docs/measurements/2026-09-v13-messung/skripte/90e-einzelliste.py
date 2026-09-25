#!/usr/bin/env python3
"""The single list of skipped and failed files, and the mark gate of phase 0.

**DIESE FASSUNG IST NICHT GEFAHREN.** No raw file lies next to it; what it reads
on the box is measured on the trip.

Two subcommands against one state.db, and both open it read only
(``?mode=ro``, ``uri=True``): this tool runs against the database of the
snapshot BEFORE any switch, and a reader that could write would be able to
change the very stock it is supposed to certify (T-02-14, T-22-08). No SQL
statement in this file writes.

``liste`` is point 4 of MESS-07: every file in state skipped or failed, one by
one, with its Nextcloud file id, its extension, its size, its state and its
reason code. The full path never leaves this tool, only the extension out of
it, because the raw data of a trip are committed to a public repository
(T-22-07). The reason is a code from the closed list in store/repo.py and never
free text, which is what schema.sql says over the column. Next to the list
stands the count per state over every row that is not a tombstone, so that the
52.111 / 37 / 0 of the snapshot can be read off the same file.

``marken`` is the mark gate of phase 0. It prints every row of the meta table
as ``marke <name> <wert>`` and compares the pairs handed in with --erwartung
NAME=WERT against them:

  0   every expected mark is equal, or the only ones that differ or are missing
      are the three marks a rebuild answers (schema_version, languages,
      wordlist_hash_nl; MARKS_A_REBUILD_ANSWERS in findling/index/rebuild.py).
      Those three are the subject of MESS-08, so a difference there is the
      expected state and not a finding.
  44  a mark outside those three and outside embedding_version differs or is
      missing: the full text index on disk is not the one the rebuild
      measurement assumes. Wins over 45 when both apply, because it is the
      larger finding.
  45  embedding_version differs or is missing: a new embedding of the vector
      stock would run in bands of 500 alongside the rebuild (pitfall 7 of the
      research), and the rebuild time would not be a pure rebuild time.
  2   the database has no meta table, or an --erwartung has no NAME=WERT shape.

Two marks are no equalities in store/repo.py (Store.version_mismatch), and this
reader follows the same two rules instead of reading them as a divergence:
index_version is a floor (a stored generation at or above the expected one is
healthy), and tantivy_version decides on its ``index_format`` half alone. The
legacy step of schema_version (LEGACY_SCHEMA_STEPS, 1 to 2) needs no rule of its
own here, because schema_version is one of the three rebuild marks anyway; the
line ``legacy-schritt`` names it when it applies.

Schema, read against store/schema.sql and store/repo.py on 25.09.2026 (the open
assumption A5 of the research): ``files`` carries ``file_id`` (the Nextcloud
fileid and the primary key), ``path``, ``size``, ``state``, ``reason`` and
``deleted_at``; ``meta`` carries ``key`` and ``value``. The schema is asked
again at every run and a missing column ends with 2.

On the box the database lies on the host at
/mnt/findling/docker/volumes/nc_app_findling_backend_data/_data/state.db, and
that path is handed in as --database; it stands only here, in prose.

Standard library only, because the host python of the box runs it.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import sqlite3
import sys
from collections.abc import Sequence

# The columns the single list needs. Asked, not assumed.
LIST_COLUMNS = ("file_id", "path", "size", "state", "reason", "deleted_at")

# The three marks a rebuild answers, spelled as in findling/index/rebuild.py
# (MARKS_A_REBUILD_ANSWERS). Literals, because this tool runs on the host of the
# box and does not import findling.
REBUILD_MARKS = frozenset({"schema_version", "languages", "wordlist_hash_nl"})
EMBEDDING_MARK = "embedding_version"
# The steps a schema mark may take without a rebuild, as in store/repo.py.
LEGACY_SCHEMA_STEPS = frozenset({("1", "2")})

EXIT_REFUSED = 2

MISSING = "fehlt"


def extension_of(path: str) -> str:
    """The extension out of the path, lower case, without the dot."""
    name = posixpath.basename(path.replace("\\", "/"))
    _, _, suffix = name.rpartition(".")
    return suffix.lower() if suffix and suffix != name else ""


def expectation(text: str) -> tuple[str, str]:
    """One NAME=WERT pair of --erwartung."""
    name, sign, value = text.partition("=")
    if not sign or not name:
        message = f"keine Gestalt NAME=WERT: {text!r}"
        raise argparse.ArgumentTypeError(message)
    return name, value


def open_read_only(database: str) -> sqlite3.Connection:
    """The database, read only, and never created when it is not there."""
    return sqlite3.connect(f"file:{database}?mode=ro", uri=True)


def columns_of(connection: sqlite3.Connection, table: str) -> list[str]:
    """The column names of a table, empty when the table does not exist."""
    return [str(row[1]) for row in connection.execute(f"pragma table_info({table})")]


def single_list(database: str) -> int:
    """Subcommand liste: the count per state and the skipped and failed one by one."""
    connection = open_read_only(database)
    try:
        columns = columns_of(connection, "files")
        for needed in LIST_COLUMNS:
            if needed not in columns:
                print(
                    f"90e-einzelliste: die Spalte {needed} fehlt in files, das Schema hat sich bewegt", file=sys.stderr
                )
                return EXIT_REFUSED
        counts = {
            str(state): int(total)
            for state, total in connection.execute(
                "select state, count(*) from files where deleted_at is null group by state order by state"
            )
        }
        rows = [
            {
                "file_id": int(file_id),
                "endung": extension_of(str(path)),
                "groesse": int(size),
                "state": str(state),
                "reason": None if reason is None else str(reason),
            }
            for file_id, path, size, state, reason in connection.execute(
                "select file_id, path, size, state, reason from files"
                " where state in ('skipped', 'failed') and deleted_at is null order by state, file_id"
            )
        ]
    finally:
        connection.close()
    print(
        json.dumps(
            {
                "datenbank": posixpath.basename(database.replace("\\", "/")),
                "spalten_von_files": columns,
                "zaehlung_je_state": counts,
                "einzelliste_anzahl": len(rows),
                "einzelliste": rows,
            },
            indent=1,
            ensure_ascii=False,
        )
    )
    return 0


def generation_at_least(stored: str | None, expected: str) -> bool:
    """index_version is a floor, as in store/repo.py; anything unparsable diverges."""
    try:
        return stored is not None and int(stored) >= int(expected)
    except ValueError:
        return False


def index_format_matches(stored: str | None, expected: str) -> bool:
    """tantivy_version decides on its index_format half, as in store/repo.py."""
    marker = "index_format "
    if not stored:
        return False
    here = stored.find(marker)
    there = expected.find(marker)
    if here < 0 or there < 0:
        return False
    return stored[here:] == expected[there:]


def mark_is_equal(name: str, stored: str | None, expected: str) -> bool:
    """Equality, with the two loosened comparisons of Store.version_mismatch."""
    if stored == expected:
        return True
    if name == "index_version":
        return generation_at_least(stored, expected)
    if name == "tantivy_version":
        return index_format_matches(stored, expected)
    return False


def mark_gate(database: str, expectations: Sequence[tuple[str, str]]) -> int:
    """Subcommand marken: every mark printed, the expected ones judged."""
    connection = open_read_only(database)
    try:
        if not columns_of(connection, "meta"):
            print("90e-einzelliste: die Tabelle meta fehlt, das ist keine state.db", file=sys.stderr)
            return EXIT_REFUSED
        stored = {str(key): str(value) for key, value in connection.execute("select key, value from meta order by key")}
    finally:
        connection.close()
    for name, value in stored.items():
        print(f"marke {name} {value}")

    index_finding = False
    embedding_finding = False
    rebuild_difference = False
    for name, expected in expectations:
        current = stored.get(name)
        if mark_is_equal(name, current, expected):
            print(f"marke-gleich {name}")
            continue
        shown = MISSING if current is None else current
        if name in REBUILD_MARKS:
            rebuild_difference = True
            print(f"marke-umbau {name} ist {shown} erwartet {expected}")
            if name == "schema_version" and (current, expected) in LEGACY_SCHEMA_STEPS:
                print(f"legacy-schritt {name} {current} nach {expected}")
        elif name == EMBEDDING_MARK:
            embedding_finding = True
            print(f"marke-vektorspur {name} ist {shown} erwartet {expected}")
        else:
            index_finding = True
            print(f"marke-abweichung {name} ist {shown} erwartet {expected}")

    if index_finding:
        print("marken-urteil abweichung")
        return 44
    if embedding_finding:
        print("marken-urteil vektorspur")
        return 45
    print("marken-urteil umbau" if rebuild_difference else "marken-urteil gleich")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Einzelliste und Markentor aus einer state.db, read-only.")
    commands = parser.add_subparsers(dest="befehl", required=True)
    listing = commands.add_parser("liste", help="uebersprungene und fehlgeschlagene Dateien einzeln")
    listing.add_argument("--database", required=True)
    marks = commands.add_parser("marken", help="die Marken der meta-Tabelle, gegen Erwartungen")
    marks.add_argument("--database", required=True)
    marks.add_argument("--erwartung", action="append", default=[], type=expectation, metavar="NAME=WERT")
    arguments = parser.parse_args(argv)

    # A database that is not there or not a database is a refusal with a
    # sentence, never a traceback in a raw file and never an empty list that
    # reads like "nothing was skipped".
    try:
        if arguments.befehl == "liste":
            return single_list(arguments.database)
        return mark_gate(arguments.database, arguments.erwartung)
    except sqlite3.Error as error:
        print(f"90e-einzelliste: die Datenbank ist nicht lesbar ({type(error).__name__})", file=sys.stderr)
        return EXIT_REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
