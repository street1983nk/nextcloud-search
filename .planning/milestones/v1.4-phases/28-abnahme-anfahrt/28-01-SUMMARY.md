---
phase: 28-abnahme-anfahrt
plan: 01
subsystem: messung
tags: [abnahme-anfahrt, teilkorpus, rechenblatt, slotkosten, mess-10]
requires: []
provides:
  - "Teilkorpus-Regel D-28-09 als Skript (5.000 Dateien, 2.691 OCR-Seiten)"
  - "Rechenblatt mit Deckel 58,74 USD (mit Anker 59,43 USD) und Unterbefehl stand für den Sicherheitstimer"
  - "Slot-Kosten-Auswertung und Rechnung je Zelle mit der 1,10-Regel"
  - "00-ablauf.md mit den Erwartungen aller 21 Messzellen vor der Messung"
  - "V14_RUN_DIR in NARROW_SCOPE_DIRS"
affects: [28-02, 28-03, 28-05]
tech-stack:
  added: []
  patterns:
    - "Box-Skripte nur mit Standardbibliothek; aus build_load_corpus kopierte Bereiche und Seitenziehung, per Test gegen den Generator gepinnt"
    - "Rechnung_anon über findling.config und probe.pending_load_bytes, nur auf der Entwicklungsmaschine"
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/00-ablauf.md
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/01-teilkorpus.py
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/02-rechenblatt.py
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/12-slotkosten.py
    - backend/tests/test_v14_teilkorpus.py
  modified:
    - backend/tests/test_measurement_scripts.py
decisions:
  - "01-teilkorpus.py importiert build_load_corpus nicht, sondern trägt Bereiche und Seitenziehung als Kopie; Tests halten sie Datei für Datei gegen den Generator"
  - "MAIN_PROCESS_BASELINE_BYTES (B2) enthält Gewichte int8, Schneider, Sparsam-Heap und eine Aktivierung; die Rechnung zählt davon nichts doppelt und zieht die Spurreserve (freier Raum, kein anon) ab"
  - "Rechenblatt: Abbau als 2 h geparkter Satz (zwei Platten je eine Stunde), damit 0,623 USD der Research exakt herauskommt"
  - "Probe-Erwartung auf m7g.large (2g) für Standard und Leistung: nofit oder narrow, dann erzwungen"
metrics:
  duration: "rund 45 min"
  completed: "2026-09-29"
  tasks: 3
  files: 6
---

# Phase 28 Plan 01: Offline-Grundlage der Abnahme-Anfahrt Summary

Feste Teilkorpus-Regel (5.000 Dateien, 2.691 OCR-Seiten), reproduzierbares Rechenblatt (45,18 USD Summe, 58,74 USD Deckel, mit Anker 59,43 USD), Slot-Kosten-Auswertung mit Rechnung je Zelle nach den Posten des Produkts und das Ablaufdokument mit den Erwartungen aller 21 Zellen, alles ohne Box.

## Was gebaut wurde

- **01-teilkorpus.py** (`auswahl`, `liste`, `hardlinks [--trocken]`, `zaehltor`): Regel D-28-09 über die Bereiche von `allocate(50000)`, Liste `name,bytes,sha256` plus Listen-Prüfsumme, Hardlinks mit Vorprüfung aller Dateien, Zähltor exakt 5.000; Rückgabewerte 2 bis 6 im Kopf katalogisiert. Offline: `teilkorpus dateien 5000 ocr-seiten 2691`.
- **02-rechenblatt.py** (`deckel`, `stand`): Posten von Variante A als Daten, Sätze vom 29.09. als Voreinstellung, `--satz TYP=USD` oder `--satzdatei`; fehlender Satz endet mit 3 statt mit null zu rechnen. `stand` rechnet Kostenstempel, Rest, Minuten bis Deckel und bis Deckel x 1,20 (Eingabe des Sicherheitstimers aus 28-02), Rückgabewerte 5 (Deckel) und 6 (Sicherheitsstopp).
- **12-slotkosten.py** (`slots`, `fp32`, `rechnung`): VmHWM-Paar, RssAnon-Paar (B2-Form), anon-Summe je Zeitpunkt durch slotsInForce, Hauptprozess getrennt, fp32-Mehrbedarf; `rechnung` je Zelle oder als Tabelle aller 21 Zellen, Urteil `getragen` genau bis 1,10 x Rechnung (ganze Bytes). Gegenprobe an der echten B2-Reihe der v1.3: RssAnon-Paar 235,2 MiB, Hauptprozess 1.257,5 MiB, deckungsgleich mit docs/performance.md.
- **00-ablauf.md**: Zellenliste in Reihenfolge, je Zelle Slots, Probe-Erwartung, Rechnung, Grenze, Planwert; Toleranzen 1,10 und 715,6 bis 744,8 MB; fp32-Zellen mit Begründung; Gegenprobe der Probe; Deckel und Sicherheitstimer; Messgrößen; Speichergrenzen; Abbild c87a0239; Werkzeugregel.
- **test_measurement_scripts.py**: `V14_RUN_DIR` in `NARROW_SCOPE_DIRS` und in der Gleichheitsprüfung, damit Shebang-, CR-, Dash-, Maschinenpfad- und Passwortregeln greifen.

## Commits

| Task | Commit | Art |
|---|---|---|
| 1 RED | c4f8d7ae | test: Teilkorpus-Regel, V14_RUN_DIR |
| 1 GREEN | 77ab4f5d | feat: 01-teilkorpus.py |
| 2 RED | e15aadef | test: Rechenblatt und Slotkosten |
| 2 GREEN | 7f7bd8b8 | feat: 02-rechenblatt.py, 12-slotkosten.py |
| 3 | b8e8c785 | docs: 00-ablauf.md |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Kein Import von build_load_corpus über sys.path**
- **Found during:** Task 1
- **Issue:** Der Plan sah den Import von build_load_corpus über sys.path vor. Das bricht zweimal: build_load_corpus importiert Pillow auf Modulebene (die Box hat kein Pillow), und `sys.path.insert`/`sys.path.append` stehen in MACHINE_SHAPES der Hausregeln (Test würde rot).
- **Fix:** Bereiche von `allocate(50000)`, `SCAN_PAGE_BANDS` und der Rng-Teil als Kopie im Skript; drei Tests halten die Kopie gegen den Generator (Bereiche, Kategoriereihenfolge, Seitenzahl jeder der 100 Mehrseiten-Scans).
- **Commit:** 77ab4f5d

**2. [Rule 3 - Blocking] findling-Import in 12-slotkosten.py ohne sys.path**
- **Found during:** Task 2
- **Issue:** Gleiche Hausregel; der Plan nannte sys.path auf backend/src.
- **Fix:** `findling` wird innerhalb von `calculation` und `command_fp32` importiert und ist über `uv run` in der Backend-Umgebung erreichbar; `slots` bleibt reine Standardbibliothek.
- **Commit:** 7f7bd8b8

**3. [Rule 1 - Bug] MESS-10 nicht als erledigt markiert**
- **Found during:** Zustandsupdate
- **Issue:** `requirements.mark-complete MESS-10` hakte die Anforderung ab, obwohl sie die ganze Phase (14 Pläne, Messung auf der Box) umfasst.
- **Fix:** REQUIREMENTS.md zurückgesetzt; MESS-10 bleibt `Pending` bis zum Phasenabschluss.

## Known Stubs

Keine. Die Liste `name,bytes,sha256` der 5.000 Dateien wird erst auf der Box gelesen (Plan-gemäß, `liste`).

## Threat Flags

Keine neue Angriffsfläche: keine Netzwerkaufrufe, keine AWS-Aufrufe, Ausgaben ohne Maschinenpfade (Test prüft es für `liste`).

## Self-Check: PASSED

- Dateien vorhanden: 00-ablauf.md, 01-teilkorpus.py, 02-rechenblatt.py, 12-slotkosten.py, test_v14_teilkorpus.py
- Commits vorhanden: c4f8d7ae, 77ab4f5d, e15aadef, 7f7bd8b8, b8e8c785
- Skripte im Index 100755, ohne CR
- Gates: pytest test_v14_teilkorpus/test_measurement_scripts/test_public_artifacts 561 passed; ruff check und format grün; pyright (latest) 0 Fehler; vulture grün
