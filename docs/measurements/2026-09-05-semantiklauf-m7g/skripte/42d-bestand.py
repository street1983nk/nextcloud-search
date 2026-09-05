#!/usr/bin/env python3
"""Measure the vector stock inside the container, after both tracks are done.

The one number this exists for is bytes per document, MEASURED. Plan 06-04
computed it, and a computation that turns out right is evidence for the method
while one that was off is a warning for next time; either way the measured one
has to stand next to it.

Bytes per document counts the database file AND its write ahead log, because a
stock whose WAL has not been checkpointed is a stock whose size is spread over
two files, and reporting only the smaller one would be the cheaper half of the
truth again.

It runs inside the container because that is where the volume, the vec0
extension and the interpreter are. It prints JSON and nothing else, so the
report can quote it without a human retyping a number.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

WURZEL = Path("/nc_app_findling_backend_data")


def main() -> int:
    bericht: dict[str, object] = {}

    vdb = next(iter(WURZEL.rglob("vectors.db")), None)
    if vdb is not None:
        neben = sum(p.stat().st_size for p in vdb.parent.glob(vdb.name + "-*"))
        bericht["vectors_db_pfad"] = str(vdb)
        bericht["vectors_db_byte"] = vdb.stat().st_size
        bericht["vectors_db_wal_byte"] = neben
        verbindung = sqlite3.connect(f"file:{vdb}?mode=ro", uri=True)
        verbindung.enable_load_extension(True)
        verbindung.load_extension(os.environ["FINDLING_VEC0_PATH"].removesuffix(".so"))
        chunks = verbindung.execute("select count(*) from chunks").fetchone()[0]
        dokumente = verbindung.execute("select count(distinct file_id) from chunks").fetchone()[0]
        bericht["chunks"] = chunks
        bericht["dokumente_mit_vektor"] = dokumente
        if dokumente:
            bericht["byte_je_dokument"] = round((vdb.stat().st_size + neben) / dokumente, 1)
            bericht["chunks_je_dokument"] = round(chunks / dokumente, 3)

    sdb = next(iter(WURZEL.rglob("state.db")), None)
    if sdb is not None:
        bericht["state_db_byte"] = sdb.stat().st_size
        zustand = sqlite3.connect(f"file:{sdb}?mode=ro", uri=True)
        bericht["verdikte"] = dict(zustand.execute("select verdict, count(*) from files group by verdict"))
        spalten = {r[1] for r in zustand.execute("pragma table_info(files)")}
        if "text_chars" in spalten:
            bericht["zeichen_gesamt"] = zustand.execute(
                "select coalesce(sum(text_chars), 0) from files"
            ).fetchone()[0]

    for name in ("index", "tantivy"):
        verzeichnis = WURZEL / name
        if verzeichnis.is_dir():
            bericht["tantivy_pfad"] = str(verzeichnis)
            bericht["tantivy_byte"] = sum(
                p.stat().st_size for p in verzeichnis.rglob("*") if p.is_file()
            )
            break

    if "tantivy_byte" in bericht and "vectors_db_byte" in bericht:
        gesamt = int(bericht["vectors_db_byte"]) + int(bericht["vectors_db_wal_byte"])
        bericht["vektor_anteil_am_tantivy_prozent"] = round(
            100 * gesamt / int(bericht["tantivy_byte"]), 2
        )

    print(json.dumps(bericht, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
