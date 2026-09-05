#!/usr/bin/env python3
"""Which process in the container holds the memory, and which mapping inside it.

The container image carries no ps, so /proc is read directly. Printed per
process: pid, VmRSS, and the command line; then for the biggest one the
anonymous mappings above 20 MB, because a heap spread over several malloc arenas
looks different from a model mapped into the address space, and the report has
to say which of the two it is.
"""

from __future__ import annotations

import pathlib


def main() -> int:
    prozesse: list[tuple[int, int, str]] = []
    for eintrag in sorted(pathlib.Path("/proc").iterdir()):
        if not eintrag.name.isdigit():
            continue
        try:
            status = (eintrag / "status").read_text(encoding="utf-8")
            befehl = (eintrag / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
        except OSError:
            continue
        for zeile in status.splitlines():
            if zeile.startswith("VmRSS:"):
                prozesse.append((int(eintrag.name), int(zeile.split()[1]), befehl[:80]))
                break

    print("-- Prozesse, RSS in MB --")
    for pid, kb, befehl in sorted(prozesse, key=lambda p: -p[1]):
        print(f"{pid:>6} {kb // 1024:>6} MB  {befehl}")

    if not prozesse:
        return 0
    groesster = max(prozesse, key=lambda p: p[1])[0]
    print(f"-- Anonyme Bereiche ueber 20 MB in Prozess {groesster} --")
    kopf = None
    treffer: list[tuple[int, str]] = []
    for zeile in (pathlib.Path("/proc") / str(groesster) / "smaps").read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        if zeile and not zeile.startswith(" ") and "-" in zeile.split()[0]:
            kopf = zeile
        elif zeile.startswith("Rss:") and kopf is not None:
            kb = int(zeile.split()[1])
            if kb > 20480:
                treffer.append((kb, kopf))
    for kb, zeile in sorted(treffer, reverse=True)[:15]:
        teile = zeile.split()
        pfad = teile[5] if len(teile) > 5 else "(anonym)"
        print(f"{kb // 1024:>6} MB  {teile[1]}  {pfad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
