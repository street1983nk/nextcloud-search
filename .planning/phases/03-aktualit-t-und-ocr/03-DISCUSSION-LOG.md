# Phase 3: Aktualität und OCR - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-01
**Phase:** 03-aktualit-t-und-ocr
**Areas discussed:** Aktualitäts-Kadenz, OCR-Umfang und Reihenfolge, OCR-Deckel und Verdikte, Lösch-Verhalten

**Modus:** Auf Owner-Wunsch verkürzt nach der Kadenz-Runde: nur noch Fragen mit sichtbarem Nutzer-Mehrwert, technische Deckel und Feintuning als dokumentierte Claude-Defaults im CONTEXT.md.

---

## Aktualitäts-Kadenz

| Option | Description | Selected |
|--------|-------------|----------|
| Unter 1 Minute (Empfohlen) | Event -> Queue -> Poller mit bestehender Kadenz, kein Zusatzaufwand | ✓ |
| Unter 10 Sekunden | Bräuchte Push-/Wecksignal-Kanal, mehr Komplexität | |
| Einige Minuten reichen | Poller-Kadenz entspannen, weniger Grundlast | |

| Option | Description | Selected |
|--------|-------------|----------|
| Nächtlich einmal (Empfohlen) | Voller ETag-Abgleich pro Nacht, Events tragen tagsüber | ✓ |
| Stündlich inkrementell | Kleine Scheiben, engere Garantie, mehr Grundlast | |
| Du entscheidest | Claude wählt anhand Phase-2-Messwerten | |

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, Rechte zuerst (Empfohlen) | Entzogener Share verschwindet vor OCR-Rückstau; ACL-Updates billig | ✓ |
| Eine Reihenfolge für alles | Einfacher, Unshares warten hinter OCR-Jobs | |

| Option | Description | Selected |
|--------|-------------|----------|
| Aussetzen bis Queue ruhig (Empfohlen) | Abgleich wartet, bis Erstindex/OCR-Rückstau abgearbeitet | ✓ |
| Immer laufen lassen | Strengste Garantie, kostet Durchsatz | |
| Du entscheidest | | |

---

## OCR-Umfang und Reihenfolge

| Option | Description | Selected |
|--------|-------------|----------|
| PDFs + gängige Bilder (Empfohlen) | JPG/PNG/TIFF/WebP mit Plausibilitäts-Deckel | ✓ |
| Nur PDFs ohne Textlayer | Kleinster Umfang, Bilder unauffindbar | |
| PDFs + alle Bildformate | Auch HEIC/BMP/GIF, mehr Decoder-Angriffsfläche | |

| Option | Description | Selected |
|--------|-------------|----------|
| Text zuerst, OCR-Nachzügler (Empfohlen) | Zwei Spuren, Suche nach Stunden nutzbar | ✓ |
| Streng der Reihe nach | Scan-Ordner am Anfang blockiert alles | |
| Du entscheidest | | |

---

## OCR-Deckel und Verdikte

| Option | Description | Selected |
|--------|-------------|----------|
| Teilindexieren (Empfohlen) | Erste N Seiten auffindbar, indexed(truncated) | ✓ |
| Überspringen | skipped(too_large), komplett unauffindbar | |

Konkrete Deckel-Zahlen (Seiten, Zeit, RAM), deu_frak-Default (aus, per Owner-Auftrag DACH-OCR) und LOCK_TIMEOUT-Anpassung: Claude-Diskretion, siehe CONTEXT.md.

---

## Lösch-Verhalten

| Option | Description | Selected |
|--------|-------------|----------|
| Nein, sofort raus (Empfohlen) | Löschen = weg aus Treffern, Wiederherstellen = wieder auffindbar | ✓ |
| Ja, bis endgültig gelöscht | Papierkorb-Inhalte bleiben auffindbar, überrascht Nutzer | |

---

## Claude's Discretion

- Listener-Mechanik und Event-Liste (ein Ereignisweg gesetzt)
- ETag-Abgleich-Algorithmus, Queue-Ruhe-Schwelle
- OCR-Deckel-Zahlen, Bild-Plausibilitäts-Heuristik, Prioritäts-Mechanik in der Queue
- Kadenz-Feintuning (Cron-Slots, Schwellwerte)

## Deferred Ideas

- Keine neuen — Diskussion blieb im Phasen-Scope. Bestehende Deferrals (Statusseite Phase 4, Embeddings Phase 6, Lasttest Phase 5) unverändert.
