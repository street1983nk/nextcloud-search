#!/usr/bin/env python3
"""The footprint of the model weights, read in the process that loads them.

Three readings of the same process, in this order: before the model exists,
after the session is built, and after a real embedding has run through it. The
difference between the first and the second is what the weights cost; the
difference between the second and the third is what the activations cost on top
of them, at the batch and sequence this image ships.

Why in the process and not from the cgroup: the cgroup carries uvicorn, the
poller and this process at once, so a difference read there would be the sum of
whatever else moved in the same second. VmRSS of the own process moves for one
reason only.
"""

from __future__ import annotations

import json
from pathlib import Path


def rss_kb() -> int:
    for zeile in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if zeile.startswith("VmRSS:"):
            return int(zeile.split()[1])
    return -1


def main() -> int:
    messung: dict[str, object] = {"vor_dem_import_kb": rss_kb()}

    from findling.api import resources  # noqa: PLC0415

    messung["nach_dem_import_kb"] = rss_kb()

    modell = resources.query_model()
    messung["nach_dem_bau_kb"] = rss_kb()

    ergebnis = modell.embed_query("Wie kuendige ich meinen Vertrag zum Monatsende?")
    messung["nach_einer_einbettung_kb"] = rss_kb()
    messung["verfuegbar"] = ergebnis.available
    messung["dimension"] = len(ergebnis.vectors[0]) if ergebnis.vectors else None

    # Eine zweite, laengere Einbettung: die Aktivierungen haengen an der Sequenz,
    # und eine Anfrage von acht Woertern fuellt sie nicht aus.
    langer_text = "Sehr geehrte Damen und Herren, hiermit kuendige ich den Vertrag. " * 60
    ergebnis2 = modell.embed_query(langer_text)
    messung["nach_langer_einbettung_kb"] = rss_kb()
    messung["dimension2"] = len(ergebnis2.vectors[0]) if ergebnis2.vectors else None

    messung["gewichte_kb"] = messung["nach_dem_bau_kb"] - messung["nach_dem_import_kb"]
    messung["aktivierungen_kb"] = (
        messung["nach_langer_einbettung_kb"] - messung["nach_dem_bau_kb"]
    )
    print(json.dumps(messung, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
