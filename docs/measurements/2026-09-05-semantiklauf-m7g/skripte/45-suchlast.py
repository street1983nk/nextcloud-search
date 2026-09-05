#!/usr/bin/env python3
"""A search load sample while the second track is still filling.

Two questions, and they are not the same one asked twice.

The first: does the search stay usable while the embedding track runs behind it?
The budget is the one Provider.php carries, BUDGET_NANOSECONDS = 2_500_000_000,
and the number to hold against it is the p95 of a real user search over the OCS
route, not a call into the container.

The second: what does the vector scan do to the cgroup that anon does not show?
A brute force scan pulls the vector store into the file cache of the same cgroup.
memory.current counts it, anon does not, and a store claim taken from anon alone
is the cheaper half of the truth (06-RESEARCH 3.4, T-06-57). Both are read here,
before, during and after the load.

Call: 45-suchlast.py <ziel.json> [runden]
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/home/ubuntu/work")

from drillhelfer import suche  # noqa: E402

CONTAINER = "nc_app_findling_backend"

# Umschreibungen und lexikalische Begriffe gemischt: die semantische Haelfte soll
# in der Last vorkommen, sonst misst die Probe die Volltextsuche allein.
BEGRIFFE = [
    "Vertrag+beenden",
    "Kuendigung",
    "Widerspruch+einlegen",
    "Bescheid",
    "Rechnung+bezahlen",
    "Mahnung",
    "Termin+absagen",
    "Mitteilung",
    "Antrag+stellen",
    "Beschluss",
]


def cgroup_zahlen() -> dict[str, int | str]:
    """anon, file und current der cgroup des Containers, in einem Griff."""
    cid = subprocess.run(
        ["sudo", "docker", "inspect", "-f", "{{.Id}}", CONTAINER],
        capture_output=True, check=False, text=True,
    ).stdout.strip()
    pfad = f"/sys/fs/cgroup/system.slice/docker-{cid}.scope"
    werte: dict[str, int | str] = {}
    stat = subprocess.run(
        ["sudo", "cat", f"{pfad}/memory.stat"], capture_output=True, check=False, text=True
    ).stdout
    for zeile in stat.splitlines():
        name, _, wert = zeile.partition(" ")
        if name in {"anon", "file", "slab"}:
            werte[name] = int(wert)
    for datei in ("memory.current", "memory.peak"):
        roh = subprocess.run(
            ["sudo", "cat", f"{pfad}/{datei}"], capture_output=True, check=False, text=True
        ).stdout.strip()
        werte[datei] = int(roh) if roh.isdigit() else roh
    return werte


def jetzt() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    ziel = Path(sys.argv[1])
    runden = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    bericht: dict[str, object] = {"start": jetzt(), "vorher": cgroup_zahlen()}
    proben: list[dict[str, object]] = []
    waehrend: list[dict[str, int | str]] = []

    for runde in range(runden):
        for begriff in BEGRIFFE:
            ergebnis = suche(begriff, limit=5)
            ergebnis["begriff"] = begriff
            ergebnis["runde"] = runde
            ergebnis["at"] = jetzt()
            proben.append(ergebnis)
        waehrend.append(cgroup_zahlen())

    zeiten = sorted(float(p["ms"]) for p in proben if isinstance(p.get("ms"), int))
    bericht["proben"] = proben
    bericht["waehrend"] = waehrend
    bericht["nachher"] = cgroup_zahlen()
    bericht["ende"] = jetzt()
    if zeiten:
        bericht["anzahl"] = len(zeiten)
        bericht["p50_ms"] = statistics.median(zeiten)
        bericht["p95_ms"] = zeiten[min(len(zeiten) - 1, int(round(0.95 * (len(zeiten) - 1))))]
        bericht["max_ms"] = zeiten[-1]
        bericht["budget_ms"] = 2500
        bericht["haelt"] = bericht["p95_ms"] < 2500
    ziel.write_text(json.dumps(bericht, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: bericht.get(k) for k in
                      ("anzahl", "p50_ms", "p95_ms", "max_ms", "budget_ms", "haelt")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
