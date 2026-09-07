#!/usr/bin/env python3
"""What the third OCR language costs, on the target hardware, per page.

The gap this closes. The per page figures in docs/ocr.md were taken on
01.09.2026 with ``-l deu+eng`` on an amd64 development machine. Since 06.09.2026
the default is ``deu+eng+fra``, and plan 06.1-21 deliberately did not rewrite the
tables: a third traineddata changes both the run time per page and the memory
peak, and by how much was not measured. This is the measurement, and it runs on
the arm box, so the seconds are seconds of the target hardware and not of a
laptop.

How it is measured. The same rendered page, the same engine options as
``findling.extract.ocr`` (``--oem 1 --psm 3 -c tessedit_do_invert=0``, and
``OMP_THREAD_LIMIT=1``), once with two languages and once with three, five runs
each, alternating so a warming disk cannot land on one of the two sets. The peak
RSS of the child is taken from ``os.wait4`` rather than from a sampler, because
a sampler at any interval misses a peak that lasts a hundred milliseconds.

Alternating and not one block after the other: the first block would pay for the
cold page cache of the traineddata files, and the difference between the two
blocks would then be a disk measurement wearing the label of a language.

Call: 69-ocr-drei-sprachen.py <page.png> [--runs 5]
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import time

ENGINE_OPTIONS = ("--oem", "1", "--psm", "3", "-c", "tessedit_do_invert=0")
SETS = ("deu+eng", "deu+eng+fra")


def one_run(image: str, languages: str) -> tuple[float, int, int]:
    """Wall clock in ms, peak RSS of the child in kB, characters recognised."""
    environment = dict(os.environ, OMP_THREAD_LIMIT="1")
    started = time.perf_counter()
    process = subprocess.Popen(  # noqa: S603
        ["tesseract", image, "stdout", "-l", languages, *ENGINE_OPTIONS],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=environment,
    )
    assert process.stdout is not None
    text = process.stdout.read()
    _, status, usage = os.wait4(process.pid, 0)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    if status != 0:
        message = f"tesseract answered with status {status} for {languages}"
        raise SystemExit(message)
    return elapsed_ms, usage.ru_maxrss, len(text.decode("utf-8", "replace").strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--runs", type=int, default=5)
    arguments = parser.parse_args(argv)

    readings: dict[str, list[tuple[float, int, int]]] = {name: [] for name in SETS}
    for _ in range(arguments.runs):
        for languages in SETS:
            readings[languages].append(one_run(arguments.image, languages))

    result: dict[str, object] = {"bild": arguments.image, "laeufe": arguments.runs, "je_satz": {}}
    per_set = result["je_satz"]
    assert isinstance(per_set, dict)
    for languages, rows in readings.items():
        millis = [row[0] for row in rows]
        rss = [row[1] for row in rows]
        chars = [row[2] for row in rows]
        per_set[languages] = {
            "median_ms": round(statistics.median(millis), 1),
            "min_ms": round(min(millis), 1),
            "max_ms": round(max(millis), 1),
            "median_rss_kb": int(statistics.median(rss)),
            "max_rss_kb": max(rss),
            "zeichen_median": int(statistics.median(chars)),
        }

    two = per_set["deu+eng"]
    three = per_set["deu+eng+fra"]
    assert isinstance(two, dict)
    assert isinstance(three, dict)
    result["aufschlag_der_dritten_sprache"] = {
        "dauer_prozent": round(
            (float(three["median_ms"]) / float(two["median_ms"]) - 1.0) * 100.0, 1
        ),
        "dauer_ms": round(float(three["median_ms"]) - float(two["median_ms"]), 1),
        "spitzen_rss_kb": int(three["max_rss_kb"]) - int(two["max_rss_kb"]),
    }
    print(json.dumps(result, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
