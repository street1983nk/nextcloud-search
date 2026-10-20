---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 11
subsystem: messung-str02
tags: [granite, e5, paarvergleich, vorzeichentest, entscheidungsvorlage, v1.6]
status: komplett
requires: [35-09, 35-10]
provides:
  - "docs/measurements/2026-10-granite-vergleich/skripte/20-paarvergleich.py: exakter einseitiger Vorzeichentest, gepaarter t-Wert, relative MRR je Sprache"
  - "docs/measurements/2026-10-granite-vergleich/rohdaten/20-paarvergleich.txt"
  - "README Abschnitte 8 bis 20 und Block 'Die Verdikte, zuerst'"
affects: [v1.6-Modellentscheid]
tech-stack:
  added: []
  patterns: ["Regel zeilenweise angewandt, Handgegenprobe mit unabhängigem Werkzeug (tr/join/awk)"]
key-files:
  created:
    - docs/measurements/2026-10-granite-vergleich/skripte/20-paarvergleich.py
    - docs/measurements/2026-10-granite-vergleich/rohdaten/20-paarvergleich.txt
  modified:
    - docs/measurements/2026-10-granite-vergleich/README.md
decisions:
  - "Bedingung (a) verfehlt (de int8: 56 nach vorn, 42 nach hinten, p = 0,0944); (b), (c), (d) erfüllt; Ergebnis eindeutig, keine Owner-Frage"
  - "Empfehlung v1.6: Wechsel nur mit Bedingung (genau ein vorab festgelegtes anderes granite-Artefakt besteht die unveränderte Regel in einem Lauf, sonst kein Wechsel)"
  - "Opt-in-Vorschlag: tragfähig mit Bedingung, rund 8 Bauteile plus zwei neue Schwellenmessungen"
  - "Ausgeliefertes Modell bleibt in v1.5 e5-small"
metrics:
  duration: "ca. 35 min"
  completed: 2026-10-20
  tasks_done: 2
  tasks_total: 2
---

# Phase 35 Plan 11: granite-Bericht und v1.6-Empfehlung (STR-02) Summary

Paarvergleich e5 gegen granite aus den Rohdaten von 35-09/35-10, Regel (a) bis (d) mechanisch angewandt: (a) verfehlt mit p = 0,0944 auf Deutsch trotz +19,2 % MRR, (b) bis (d) erfüllt; Empfehlung "Wechsel nur mit Bedingung", Opt-in tragfähig mit Bedingung, e5-small bleibt in v1.5.

## Commits

| Task | Name | Commit |
|---|---|---|
| 1 | Paarvergleich und Ergebnisabschnitte 8 bis 17 | 70b2afb9 |
| 2 | Verdikte, Regelanwendung, Opt-in-Bewertung, Empfehlung | 2ac1f409 |

## Kernzahlen

| Bedingung | Messwert | Grenze | Ergebnis |
|---|---|---|---|
| (a) de int8 Vorzeichentest | 56/42 von 98 bewegt, p = 0,0944 | p < 0,05 | nicht erfüllt |
| (b) MRR-Rückgang | min. +10,07 % (en) | höchstens -5 % | erfüllt |
| (c) arm64 memory.peak | Abstand 1402,5 MiB | mind. 1108,3 MiB | erfüllt |
| (d) arm64 kalt | max 1071,2 ms | 1500 ms | erfüllt |

Zusatz (ohne Gewicht): fp32 gegen fp32 besteht (a) klar (54/23, p = 0,000269); der Verlust sitzt in der int8-Quantisierung (granite -0,1143 MRR, e5 -0,0379).

## Handgegenprobe Deutsch

Unabhängig vom Skript: "per case"-Spalten beider Rohdateien per `tr`/`sort`/`join` zusammengeführt, mit `awk` gezählt: 120 Fälle, 56 besser, 42 schlechter, 22 gleich. p-Wert per `awk` über Logarithmen der Binomialkoeffizienten: 0,0944. Gleich dem Skript.

## Deviations from Plan

1. **Push und CI-Block entfallen** (Vorgabe Orchestrator, paralleler Worktree).
2. **Abweichungsblöcke von 35-09 und 35-10 verschoben**, wortgleich als 17.1 und 17.2 unter Abschnitt 17; nur die Überschriften änderten sich. Abschnitte 1 bis 7 unverändert (README 17.3 Punkt 1).
3. **Zusatzpaare** fp32 und IBM-int8 im Paarvergleich, getrennt ausgewiesen, ohne Gewicht für die Regel.
4. **[Rule 1] Gate `schluesselwort-mit-wert`** schlug auf die Zeile "granite bei 1024 Token:" aus Commit 70b2afb9 an; umformuliert, Fix in 2ac1f409.
5. **[Rule 1] pyright** meldete `__doc__` als optional im Skript; feste Beschreibung, Ausgabe danach byte-gleich nachgefahren (`cmp`).
6. **Plan nennt "Distanzriegel 86,5/14,0 und SIMILAR_CEILING"**: Code geprüft, `SIMILAR_CEILING` = 54,5 (config.py:977), die Riegel sind Umgebungs-Stellschrauben (config.py:952/954); so im Bericht.

## Known Stubs

Keine.

## Gates

ruff check und format, pyright (0 errors), vulture auf `20-paarvergleich.py`; reuse lint grün; `test_measurement_scripts.py` und `test_public_artifacts.py`: 627 passed. T-35-40 `grep -nE "[0-9]{12}|\.pem"` auf den README leer; keine Gedankenstriche. Kein Produktcode geändert.

## Threat Flags

Keine. Reine Doku- und Auswertungsänderung.

## Self-Check: PASSED

- `skripte/20-paarvergleich.py`, `rohdaten/20-paarvergleich.txt`, README mit Abschnitten 8 bis 20 vorhanden
- Commits 70b2afb9 und 2ac1f409 im Log
- STATE.md und ROADMAP.md unangetastet, kein Push
