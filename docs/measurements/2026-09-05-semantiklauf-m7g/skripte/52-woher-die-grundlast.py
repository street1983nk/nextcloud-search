#!/usr/bin/env python3
"""Which step of the startup buys the 595 MB, measured step by step.

The A/B has already said that the image is the cause and not the state of the
volume: the same volume under the image without the semantic half holds 93,5 MB,
under the image with it 688 MB. What the A/B cannot say is WHICH part of the
semantic half does it, and a report that names 595 MB without naming their owner
invites the next reader to guess.

So the startup is walked in the order the container walks it, and VmRSS is read
after every step. Every step is a candidate and each one is named, so the
difference between two lines is the price of exactly one thing.
"""

from __future__ import annotations

import json
from pathlib import Path

schritte: list[tuple[str, int]] = []


def rss_kb() -> int:
    for zeile in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if zeile.startswith("VmRSS:"):
            return int(zeile.split()[1])
    return -1


def merke(name: str) -> None:
    schritte.append((name, rss_kb()))


def main() -> int:
    merke("00-leerer-prozess")

    from findling.config import settings

    merke("01-config-importiert")
    s = settings()
    merke("02-settings-gelesen")

    from findling.index import analyzer, wordlist

    merke("03-index-module-importiert")

    from findling.embed import chunker, model

    merke("04-embed-module-importiert")

    from findling.store import vectors

    merke("05-store-vectors-importiert")

    from findling.worker import poller

    merke("06-poller-importiert")

    from findling.api import resources

    merke("07-api-resources-importiert")

    from findling import main as hauptmodul

    merke("08-findling-main-importiert")

    # Jetzt die Bauwege, einzeln, in der Reihenfolge des Containers.
    quelle = wordlist.SYSTEM_WORDLIST
    eintraege = wordlist.load_constituents(quelle) if quelle.exists() else []
    if not isinstance(eintraege, list):
        eintraege = list(eintraege)
    schritte.append((f"09-wortliste-gelesen-{len(eintraege)}", rss_kb()))

    if eintraege:
        analyzer.cached_german_analyzer(wordlist.wordlist_hash(eintraege), tuple(eintraege))
    merke("10-deutscher-automat-gebaut")

    tokenizer = model.open_tokenizer(s.embed_model_dir)
    merke("11-tokenizer-gelesen")

    schneider = chunker.make_splitter(tokenizer, chunk_tokens=s.embed_chunk_tokens, overlap=s.embed_chunk_overlap)
    spannen = chunker.chunk_spans(
        "Ein Satz zum Schneiden, damit der Schneider wirklich arbeitet. " * 60,
        tokenizer=tokenizer,
        splitter=schneider,
        token_cap=s.embed_token_cap,
    )
    schritte.append((f"12-chunker-gebaut-und-gefahren-{len(spannen)}", rss_kb()))

    m = resources.query_model()
    merke("13-modell-objekt-gebaut-lazy")

    ergebnis = m.embed_query("Wie kuendige ich meinen Vertrag zum Monatsende?")
    merke("14-erste-einbettung-gewichte-geladen")

    langer = "Sehr geehrte Damen und Herren, hiermit kuendige ich den Vertrag. " * 60
    m.embed_query(langer)
    merke("15-lange-einbettung-aktivierungen")

    bericht = {
        "schritte": [
            {"schritt": n, "rss_kb": k, "rss_mb": round(k / 1024, 1)} for n, k in schritte
        ],
        "zuwaechse_ueber_10_mb": [
            {
                "von": schritte[i - 1][0],
                "nach": schritte[i][0],
                "delta_mb": round((schritte[i][1] - schritte[i - 1][1]) / 1024, 1),
            }
            for i in range(1, len(schritte))
            if abs(schritte[i][1] - schritte[i - 1][1]) > 10240
        ],
        "verfuegbar": ergebnis.available,
        "vectors_modul": vectors.__name__,
        "poller_modul": poller.__name__,
        "haupt_modul": hauptmodul.__name__,
    }
    print(json.dumps(bericht, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
