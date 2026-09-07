#!/usr/bin/env python3
"""The verdicts out of state.db, grouped by extension, state and reason.

Half two of the extension comparison of assumption A10. The schema was read
before this was written, and it settles the question the assumption left open:
``files`` carries ``path``, ``state`` and ``reason``, and it carries NO extension
column, so the extension comes out of the path. That is the way that was taken
and this docstring is where it is recorded.

The second thing the schema settled is the trap of 06-11: the column is called
``state`` and not ``verdict``. The first reading of the run of 05.09.2026 failed
on exactly that name after a long run, which is why every reading script of this
run is driven once against the real schema before it is armed.

Only the rows of the load test corpus are counted. The index of this box also
holds the drill corpus and the files a fresh Nextcloud brings, and a comparison
against the 50.000 files of the generator has to ask about those 50.000 and not
about everything the box ever saw. The filter is the path prefix, and the number
of rows outside it is printed rather than dropped silently.

Call: 68-bestand-endungen.py <state.db> [--prefix files/loadtest]
"""

from __future__ import annotations

import argparse
import collections
import json
import posixpath
import sqlite3
import sys


def extension_of(path: str) -> str:
    """The extension out of the path, lower case, without the dot."""
    name = posixpath.basename(path.replace("\\", "/"))
    _, _, suffix = name.rpartition(".")
    return suffix.lower() if suffix and suffix != name else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database")
    parser.add_argument("--prefix", default="loadtest")
    arguments = parser.parse_args(argv)

    connection = sqlite3.connect(f"file:{arguments.database}?mode=ro", uri=True)

    # The schema is asked rather than assumed, and the answer goes into the
    # output: a report that names a column has to be able to show it existed.
    columns = [row[1] for row in connection.execute("pragma table_info(files)")]
    for needed in ("path", "state", "reason"):
        if needed not in columns:
            print(f"the column {needed} is not in files, the schema moved", file=sys.stderr)
            return 2

    je_endung: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    gruende: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    ausserhalb = 0
    gesamt = 0
    for path, state, reason in connection.execute(
        "select path, state, reason from files where deleted_at is null"
    ):
        gesamt += 1
        if arguments.prefix and arguments.prefix not in path:
            ausserhalb += 1
            continue
        extension = extension_of(path)
        je_endung[extension][state] += 1
        if state != "indexed":
            gruende[extension][f"{state}:{reason}"] += 1

    print(
        json.dumps(
            {
                "datenbank": arguments.database,
                "praefix": arguments.prefix,
                "spalten_von_files": columns,
                "zeilen_gesamt": gesamt,
                "zeilen_ausserhalb_des_praefix": ausserhalb,
                "zeilen_im_praefix": gesamt - ausserhalb,
                "je_endung": {
                    key: dict(sorted(value.items())) for key, value in sorted(je_endung.items())
                },
                "gruende_je_endung": {
                    key: dict(sorted(value.items())) for key, value in sorted(gruende.items())
                },
            },
            indent=1,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
