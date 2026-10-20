#!/usr/bin/env python3
"""Step 14 of the granite comparison: the re-embedding time of 52.111 documents, extrapolated.

Not a full run (pitfall 16): the rate of step 13 on the fixed sample of 500
documents, per model, scaled to the stock of the comparison run of September
(docs/measurements/2026-09-vergleichsmessung-m7g/, 52.111 documents).

Assumptions, written into the output as well:

1. Linear in the number of documents: the sample is drawn uniformly from the
   load corpus, so its mix of formats and lengths stands for the stock, and the
   chunks per document of the sample hold for the stock.
2. Embedding alone: a re-embedding after a model switch keeps the extracted text
   (the full text index is untouched), so neither extraction nor OCR is paid
   again. The rate is the one of a single process with two threads on the two
   cores of the box, nothing else running, as in the product, which runs the
   embedding track in one worker.
3. The coupled reference of September (26 h 37 min, both tracks together) is a
   different situation, a first indexing with OCR beside it. It is put next to
   the figures, scaled with the ratio of the two embedding rates, as the case in
   which the embedding is the slower track; the scaled figure is an upper bound
   for that case and not a measurement.

    python 14-hochrechnung.py --durchsatz rohdaten/13-arm-durchsatz.txt --out rohdaten/14-hochrechnung.txt
"""

from __future__ import annotations

import argparse
import re
import statistics
from pathlib import Path

STOCK = 52_111
COUPLED_E5_SECONDS = 26 * 3600 + 37 * 60 + 21
EMBED_ALONE_E5_REFERENCE = 170.0
SAMPLE = 500


def duration(minutes: float) -> str:
    total = round(minutes * 60)
    return f"{total // 3600} h {total % 3600 // 60:02d} min"


def per_label(text: str) -> dict[str, dict[str, list[float]]]:
    found: dict[str, dict[str, list[float]]] = {}
    label = ""
    for line in text.splitlines():
        heading = re.match(r"^== (\S+) lauf \d+", line)
        if heading:
            label = heading.group(1)
            continue
        if line.startswith("== zusammenfassung"):
            break
        match = re.match(r"^([a-z_.]+)=([0-9]+(?:\.[0-9]+)?)$", line)
        if label and match:
            found.setdefault(label, {}).setdefault(match.group(1), []).append(float(match.group(2)))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--durchsatz", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    runs = per_label(args.durchsatz.read_text(encoding="utf-8"))
    lines = [
        "schritt 14 hochrechnung der neu-einbettung, aus rohdaten/13-arm-durchsatz.txt",
        f"bestand {STOCK} dokumente (2026-09-vergleichsmessung-m7g), stichprobe {SAMPLE} dokumente",
        "annahme 1: linear in der dokumentzahl, chunks je dokument der stichprobe gelten fuer den bestand",
        "annahme 2: nur einbettung (text bleibt im volltextindex, keine extraktion, keine ocr), ein prozess,",
        "           zwei threads, box sonst leer, --memory 2g",
        "annahme 3: der gekoppelte septemberlauf (26 h 37 min 21 s, erste indexierung mit ocr daneben) ist",
        "           ein anderer fall; er steht skaliert mit dem verhaeltnis der einbettungsraten daneben,",
        "           als obergrenze fuer den fall, dass die einbettung die langsamere spur ist",
        "",
    ]
    rates: dict[str, float] = {}
    for label in sorted(runs):
        values = runs[label]
        rate = statistics.median(values["documents_per_minute"])
        chunks = statistics.median(values["chunks_per_document_mean"])
        rates[label] = rate
        spread = ", ".join(f"{value:.2f}" for value in values["documents_per_minute"])
        lines += [
            f"{label}: dokumente/min median {rate:.2f} (laeufe {spread})",
            f"{label}: chunks/dokument {chunks:.4f}, chunks hochgerechnet {round(chunks * STOCK)}",
            f"{label}: chunks/s median {statistics.median(values['chunks_per_second']):.3f}",
            f"{label}: neu-einbettung {STOCK} dokumente, einbettung allein: {duration(STOCK / rate)}",
        ]
    e5 = rates.get("e5-int8")
    granite = rates.get("granite-int8")
    if e5 and granite:
        ratio = e5 / granite
        lines += [
            "",
            f"verhaeltnis zeit granite / e5 = {ratio:.3f}",
            (
                f"e5-bezug einbettung allein september: rund {EMBED_ALONE_E5_REFERENCE:.0f} dokumente/min"
                f" (diese messung e5 {e5:.2f}, {e5 / EMBED_ALONE_E5_REFERENCE * 100:.0f} prozent davon)"
            ),
            f"e5-bezug gekoppelt september: 26 h 37 min 21 s ({COUPLED_E5_SECONDS} s)",
            (
                "granite gekoppelt, skaliert mit dem verhaeltnis (obergrenze nach annahme 3):"
                f" {duration(COUPLED_E5_SECONDS * ratio / 60)}"
            ),
        ]
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
