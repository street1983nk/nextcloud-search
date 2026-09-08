#!/usr/bin/env python3
"""What the lazy build really saves, measured on the path the container walks.

Script 01 of this directory takes the startup apart and says what each step
costs. It calls ``open_tokenizer`` and ``make_splitter`` itself, so it measures
the price of the two posts and not the decision about when they are paid. This
script measures the decision: it walks the path of the worker instead, in the
order the poller walks it, and reads VmRSS after each station.

  00  the empty process
  06  the poller module imported
  20  the second track wired, which is what the first pass of the poller does
  21  the cutter built, which since plan 07-03 is what the first embedding row
      does and what a container that only searches never does

Run against the image as it is published, station 20 carries the whole 544,3 MB
and station 21 adds nothing, because the old wiring did both in one. Run against
the changed source, station 20 carries the vector stock alone and station 21
carries the 544,3 MB. The difference between the two runs at station 20 is the
saving of a container that only searches.

The script sends nothing and opens no network connection. It reads
/proc/self/status, the model directory and the word list of the image, and it
prints numbers. The volume it points at is a scratch directory of the container
and holds no user content.
"""

from __future__ import annotations

import datetime
import os
import platform
from pathlib import Path

schritte: list[tuple[str, int]] = []


def rss_kb() -> int:
    for zeile in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if zeile.startswith("VmRSS:"):
            return int(zeile.split()[1])
    return -1


def merke(name: str) -> None:
    schritte.append((name, rss_kb()))


def umgebung(name: str) -> str:
    return os.environ.get(name, "") or "unknown"


def main() -> int:
    merke("00-leerer-prozess")

    from findling.worker import poller as poller_module

    merke("06-poller-importiert")

    worker = poller_module.Poller()
    worker._wire_the_second_track()
    merke("20-zweite-spur-verdrahtet")

    # Absent in the published image, present after plan 07-03. Asked for rather
    # than assumed, so the same file can measure both sides of the change.
    bauen = getattr(worker, "_build_the_cutter", None)
    gebaut = bool(bauen()) if callable(bauen) else False
    merke("21-schneider-gebaut")

    jetzt = datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    zeilen = [
        "date=" + jetzt,
        "arch=" + platform.machine(),
        "variante=" + umgebung("FINDLING_MEASURE_VARIANT"),
        "image_ref=" + umgebung("FINDLING_MEASURE_IMAGE"),
        "hat_faulen_bau=" + str(callable(bauen)),
        "schneider_gebaut=" + str(gebaut),
        "vektorbestand_offen=" + str(worker._vectors is not None),
        "",
        "-- schritt rss_kb --",
    ]
    zeilen.extend(name + " " + str(kb) for name, kb in schritte)
    zeilen.append("")
    zeilen.append("-- zuwachs je schritt --")
    for i in range(1, len(schritte)):
        delta = (schritte[i][1] - schritte[i - 1][1]) / 1024
        gesamt = schritte[i][1] / 1024
        zeilen.append(
            schritte[i - 1][0].ljust(28)
            + " "
            + schritte[i][0].ljust(28)
            + " "
            + format(delta, "9.1f")
            + " "
            + format(gesamt, "9.1f")
        )

    print("\n".join(zeilen))
    if worker._vectors is not None:
        worker._vectors.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
