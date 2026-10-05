---
phase: 28-abnahme-anfahrt
plan: 11
subsystem: messung
status: "checkpoint erreicht: Owner-Entscheid SC4/C5 (Task 2) offen"
tags: [abnahme-anfahrt, auswertung, slotkosten, sc4, mess-10]
requires:
  - phase: 28-09
    provides: Matrix komplett, 18 Zellen, Rohdaten aller Boxen, Kosten 34,09 von 59,43 USD
provides:
  - "auswertung.txt: eine Zeile je Zelle (18) aus 12-slotkosten.py mit Urteil getragen ja/nein und Gegenprobe"
  - "README.md des Messordners: Bericht mit Abbild-Digests gegen den c87a0239-Pin, Tabellen je Zelle, Kandidaten OCR_SLOT_COST_BYTES, SC4-Fallliste, Abschnitt Owner-Entscheide leer"
affects: [28-12, 29]
tech-stack:
  added: []
  patterns:
    - "Hauptprozess-Anteil der Rechnung = Rechnung minus Slots x 235; Vergleich mit dem Hauptprozess-Maximum trennt Slot- von Hauptprozessposten"
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/auswertung.txt
    - docs/measurements/2026-10-abnahme-anfahrt/README.md
  modified: []
decisions:
  - "Keine Entscheidung getroffen; Task 2 (checkpoint:decision, blocking) liegt beim Owner, Task 3 nicht begonnen"
metrics:
  duration: "05.10.2026, rund 1,5 h, keine Boxzeit"
  completed: 2026-10-05
requirements: [MESS-10]
---

# Phase 28 Plan 11: Auswertung und Bericht der Abnahme-Anfahrt Summary

**Status: checkpoint erreicht: Owner-Entscheid SC4/C5 (Task 2) offen.** Task 1 ist fertig und committet, Task 2 wartet auf das Owner-Signal, Task 3 (Kapitel in docs/performance.md) ist nicht begonnen.

Alle 18 Zellen mit `12-slotkosten.py` ausgewertet: 12 getragen, 6 nicht getragen (S-voll +19,9 %, neu bewertet; dazu 11, 16, 17, 20, 21 auf x86), alle 11 Proben `fits` und von der Messung bestätigt, C1 743,9 MB im Band. Der Hauptprozess wächst mit der Slotzahl, die Slots selbst liegen bei mehreren Slots unter 235 MiB.

## Task-Stand

### Task 1: Auswertung aller Zellen und Bericht (Commit 91357168)

- `auswertung.txt`: Kopf mit Felddefinitionen, je Zelle eine Zeile (anon, peak, Rechnung, Grenze, Abweichung, getragen, VmHWM-Paar, RssAnon-Paar, anon je Slot, Hauptprozess, r, OCR-Fenster, Seiten/s, Dateien/h, Laufzeiten, Leerlauf, Wächter, OOM, Probe, erzwungen, Reserve-Ersatzmaß, Gegenprobe), Kandidatenblock, Hauptprozess-Block, SC4-Liste, C1, darunter die Rohausgaben von `12-slotkosten.py slots`, `rechnung --gemessen-bytes` und `fp32`.
- `README.md`: 14 Abschnitte im Hausstil der v1.3-Messung; Abschnitt 14 "Owner-Entscheide" leer.
- Gates: `test_public_artifacts.py` 55 grün; die drei Tests am Messordner (`test_v14_typwechsel.py`, `test_v14_zelle.py`, `test_measurement_scripts.py`) 594 grün; keine Em- oder En-Dashes; keine Adressen.

### Task 2: Owner-Entscheide SC4 und Store-Zahl (offen)

Vorlage steht in README Abschnitt 8 bis 11. Resume-Signal laut Plan: "wert-bestaetigt" oder "je-fall: <Zelle>=<nachziehen|nicht-anbieten>, ..., wert=<MiB>, store=<Entscheid>". Store-Zahl-Fall (C4) entsteht nicht, C1 liegt innerhalb.

### Task 3: nicht begonnen

## Abweichungen vom Plan

1. **18 statt 21 Zellen:** Zellen 3, 4, 10 vom Owner gestrichen (Quick 261003-d3y), Grund im README Abschnitt 1.
2. **Abbild-Stand:** drei Stände statt c87a0239 durchgehend (c87a0239 für 1 und 2, f73566c1 für 5 und 6, 18602c48 für 7 bis 21), Digests, Baumhashes und Änderungsumfang (nur Probe-Schwellen, Reconcile, Crawl) im README Abschnitt 2.
3. **[Befund] S-voll nicht getragen:** anon 1.788,9 gegen Grenze 1.641,8 MiB (+19,9 %). 28-06 hatte die Zahl nicht gegen die Grenze gestellt; das ist ein sechster SC4-Fall, den die Close-outs nicht nannten.
4. **[Befund] Maß des Kandidaten:** Die Plan-Regel nennt das VmHWM-Paar "dasselbe Maß wie B2", B2 ist aber ein RssAnon-Paar (docs/performance.md). Beide Kandidaten (448 und 391 MiB) stehen im README, dazu 250 MiB als kleinster Wert, der alle 17 Teilkorpus-Zellen trägt. Nicht entschieden.
5. **Reserve am Tiefpunkt nicht gesampelt:** für die Gegenprobe ein Ersatzmaß (Box-RAM minus 1 GiB minus anon), im README offen benannt.
6. **Leerlaufanteil über 10 % in 8 Zellen:** nur im Anlauf (10 bis 14 min bis zur ersten indexierten Datei, cron-gebunden), nach dem Anlauf 0; als "im Anlauf zulaufgebunden" benannt.
7. **Kosten:** Schlusstabelle nach Runbook 2.6 fehlt (gehört zu 28-10); Aufschlüsselung je Typ aus den Stempeln ergibt dieselben 34,09 USD.
8. **Helfer:** Die Ableitungen über `12-slotkosten.py` hinaus (Durchsatz, r, Leerlauf, Kandidatentabelle) lief über ein temporäres Hilfsskript im Worktree, das nicht committet und danach gelöscht wurde; die Definitionen stehen im Kopf von `auswertung.txt`.

## Known Stubs

README Abschnitt 14 "Owner-Entscheide" ist absichtlich leer; Task 3 füllt ihn nach dem Owner-Signal.

## Self-Check: PASSED

- docs/measurements/2026-10-abnahme-anfahrt/auswertung.txt: FOUND
- docs/measurements/2026-10-abnahme-anfahrt/README.md: FOUND
- Commit 91357168: FOUND
