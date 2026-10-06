---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 10
subsystem: backend/profile, worker/poller, Messskripte
tags: [slots, profile, vollindex-term, D-29-12, REL-04]
requires: [29-09]
provides:
  - profile.note_index_files (Tausender-Rundung, Neuberechnung nur bei Änderung)
  - ProfileSnapshot.index_files, resolve(..., index_files=)
  - Poller meldet indexed_alive() beim Start und nach Pässen mit Verdikten
  - 12-slotkosten.py rechnung --dateien N
affects: [probe_run (Vorprüfung rechnet mit dem Bestand), Statusroute (Snapshot)]
tech-stack:
  added: []
  patterns: [note_*-Setter mit Neuberechnung nur bei Änderung]
key-files:
  created: []
  modified:
    - backend/src/findling/profile.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/worker/probe_run.py
    - backend/tests/test_profile.py
    - backend/tests/test_poller.py
    - backend/tests/test_probe_run.py
    - backend/tests/test_v14_teilkorpus.py
    - backend/tests/test_measurement_scripts.py
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/12-slotkosten.py
decisions:
  - "D-29-12 umgesetzt: Vollindex-Term (6 KiB/Datei) wirkt zur Laufzeit über note_index_files, auf ganze Tausend abgerundet"
  - "Die Lane-Zulassung (embed_lane_fits) rechnet mit demselben Hauptprozess inkl. Vollindex-Term wie die Slots"
  - "probe_run löst das Zielprofil mit dem Bestand des Snapshots auf (index_files=state.index_files)"
  - "OCR_SLOT_COST_BYTES bleibt 250 MiB, CELLS-Tabelle des Skripts bleibt unverändert (Dateizahl je Zelle nicht ergänzt)"
metrics:
  duration: "ca. 45 min"
  completed: 2026-10-06
  tasks: 2
  files: 9
---

# Phase 29 Plan 10: Vollindex-Term zur Laufzeit Summary

Der Vollindex-Term (MAIN_PROCESS_PER_FILE_BYTES, 6 KiB je indexierter Datei) wirkt jetzt in der Laufzeit-Slotrechnung: Der Poller meldet `store.indexed_alive()` über `profile.note_index_files`, Standard und Leistung verlieren mit wachsendem Bestand Slots, Sparsam bleibt Wert für Wert gleich; `12-slotkosten.py rechnung` kennt den Term über `--dateien N`.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | note_index_files im Profilmodul und Aufruf im Poller | 2af66bf2 | profile.py, poller.py, probe_run.py, test_profile.py, test_poller.py, test_probe_run.py |
| 2 | --dateien im Slotkosten-Skript, Pins | eb71da96 | 12-slotkosten.py, test_v14_teilkorpus.py, test_measurement_scripts.py |

## Umsetzung

- `profile.py`: Modulzustand `_INDEX_FILES`, Setter `note_index_files(count)` (None/negativ ignoriert, `count // 1000 * 1000`, Neuberechnung nur bei Änderung), `_compute`/`resolve`/`_profile_values` reichen `index_files` an `ocr_slots` durch, `ProfileSnapshot.index_files`, `reset()` setzt 0. Docstring "No caller hands a file count in yet" ersetzt.
- `poller.py`: `_note_index_files()` zählt `indexed_alive` per `asyncio.to_thread`; einmal pro Prozess vor dem Profil-Lesen des ersten Passes (damit Claim und Slots des ersten Passes den Term schon kennen) und nach jedem Pass, der Verdikte geschrieben hat. Ein `sqlite3.Error` beim Zählen ist eine Warnzeile mit Klassennamen, der letzte Wert bleibt.
- `12-slotkosten.py`: `calculation(..., *, files=0)` addiert `files * MAIN_PROCESS_PER_FILE_BYTES`; `--dateien` (Default "0", nur ASCII-Ziffern, sonst Exit 2). Die Zeile `dateien N` erscheint nur bei N > 0, damit die Ausgabe ohne Term bytegleich bleibt.

## Slotzahlen auf den Referenz-Hardwarestufen (selbst gemessen)

Formel mit MemAvailable = MemTotal minus 1 GiB, wie in performance.md (Kapitel aus 28-11/28-12):

| Box | Profil | 0 | 5.000 | 52.000 | 200.000 | 1.000.000 Dateien |
|---|---|---:|---:|---:|---:|---:|
| m7g.4xlarge | Standard / Leistung | 4 / 15 | 4 / 15 | 4 / 15 | 4 / 15 | 4 / 15 |
| c7a.xlarge | Standard / Leistung | 1 / 3 | 1 / 3 | 1 / 3 | 1 / 3 | 1 / 1 |
| c7a.2xlarge | Standard / Leistung | 3 / 7 | 3 / 7 | 3 / 7 | 3 / 7 | 1 / 2 |
| c7a.4xlarge | Standard / Leistung | 4 / 15 | 4 / 15 | 4 / 15 | 4 / 15 | 4 / 15 |
| c7a.8xlarge | Standard / Leistung | 4 / 16 | 4 / 16 | 4 / 16 | 4 / 16 | 4 / 16 |

Ergebnis: Bis 200.000 Dateien ändert der Term keine Slotzahl einer gemessenen Zelle, alle Zellen der performance.md-Tabelle bleiben, wie sie sind. Erst bei rund einer Million Dateien fallen die kleinen x86-Boxen (c7a.xlarge Leistung 3 auf 1, c7a.2xlarge Standard 3 auf 1, Leistung 7 auf 2). Keine bestehende Test-Erwartung einer Slotzahl wurde geändert; der Default `index_files=0` lässt alle bisherigen Pins stehen.

Neue, ausgerechnete Erwartungen in Tests:
- `test_standard_loses_slots_on_a_tight_box_as_the_stock_grows`: 16 Kerne, 8 GiB frei (16 GiB total), Standard 4 Slots bei 0 Dateien, 1 Slot bei 200.000 (1.363,9 MiB Raum minus 1.171,9 MiB Term = 192,1 MiB, unter einem Slot). Erwartung über `main_process_bytes` ausgerechnet.
- `test_the_pre_check_judges_the_slots_of_the_stock_in_force`: `_big_box` (64 GB) Standard 4 Slots leer, 2 Slots bei 3 Mio. Dateien (17.578 MiB Term); probe_run übergibt dem Urteil die 2.
- `test_the_embed_lane_check_counts_the_stock`: lane_box(5000) passt leer, bei 50.000 Dateien nicht mehr.

## Messung Pins

- Baumhash Python-Paket: `38dab3268b8df758298a567b4af762a151102c4952b9608c4e6507c271fe61c9`, 73 Dateien (unverändert 73, keine Datei kam oder ging). Abweichung zum Plan: Neben profile.py und poller.py hat sich auch `worker/probe_run.py` geändert (siehe Abweichung 2), der Pin-Kommentar nennt alle drei.
- PHP-Pin unverändert (php/ nicht berührt).
- Skript 12 ohne `--dateien`: Tabelle md5 `e7023978...` vor und nach der Änderung identisch, Standardzelle `rechnung-bytes 2473471872` unverändert; mit `--dateien 52137` genau `52137 * 6144` Byte mehr (2.793.801.600).

## Verifikation

- `pytest` voll: 4670 passed, 25 skipped (PYTHONUTF8=1).
- ruff check, ruff format --check, pyright (latest, 0 errors), vulture (min-confidence 80): sauber.
- Pin-Test `test_economy_is_todays_constants_value_for_value` grün, zusätzlich `test_economy_ignores_the_stock_value_for_value` mit 10 Mio. Dateien.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Korrektheit] embed_lane_fits rechnet mit dem Vollindex-Term**
- **Found during:** Task 1
- **Issue:** Die statische Lane-Zulassung hätte sonst mit einem leeren Hauptprozess gerechnet, während die Slots den Bestand schon abziehen; eine Lane hätte auf einer vollen Box als passend gegolten.
- **Fix:** `_embed_lane_fits(..., index_files)` übergibt den Term an `_memory_term`; bei 0 Dateien unverändert.
- **Commit:** 2af66bf2

**2. [Rule 1 - Bug] probe_run hätte die Slotzahl ohne Term gesehen**
- **Found during:** Task 1
- **Issue:** `probe_run._measured` ruft `profile.resolve(target, ...)` direkt und nicht den Snapshot; die Plan-Wahrheit "probe_run sieht nach der Verdrahtung die kleinere Slotzahl" wäre ohne Änderung falsch gewesen.
- **Fix:** `resolve(..., index_files=state.index_files)`; Test in `test_probe_run.py`.
- **Files modified:** backend/src/findling/worker/probe_run.py, backend/tests/test_probe_run.py
- **Commit:** 2af66bf2

**3. [Rule 3 - Blockierend] Skript-12-Tests liegen in test_v14_teilkorpus.py**
- **Issue:** Der Plan nennt `test_measurement_scripts.py`, die Tests von `12-slotkosten.py` (Fixture `slot_costs`) stehen aber in `test_v14_teilkorpus.py`. Die neuen Tests stehen dort; `test_measurement_scripts.py` trägt nur den Baumhash-Pin.
- **Commit:** eb71da96

### Auslegung

- "Gesetzte Override-Variable der Slots gewinnt": Slots haben bewusst keine Umgebungsvariable (`test_slots_have_no_variable`, INDEX_WORKERS-Tabu). Getestet sind deshalb (a) Admin-Variablen wie `FINDLING_OCR_MAX_PAGES` bleiben `env` bei gesetztem Term, `FINDLING_INDEX_WORKERS` bewegt nichts, und (b) der einzige Slot-Override, der `ocr_slots=`-Pin des Pollers (Kill-Harness/Messleiter), gewinnt gegen einen Bestand von 1 Mio. Dateien (`test_a_pinned_slot_count_wins_over_the_full_index_term`).
- CELLS-Tabelle nicht um Dateizahlen ergänzt (optional laut Plan); die Zellen der Fahrt wurden ohne Term festgeschrieben und bleiben ihre Rechnung.

## Threat Flags

Keine neue Angriffsfläche. T-29-33 (Term verdrahtet, Test mit 200.000 Dateien), T-29-34 (Tausender-Rundung, `snapshot() is before`-Test), T-29-35 (Sparsam-Pin Wert für Wert) sind abgedeckt.

## Known Stubs

Keine.

## Self-Check: PASSED

- backend/src/findling/profile.py enthält `def note_index_files`: FOUND
- backend/src/findling/worker/poller.py enthält `note_index_files`: FOUND
- 12-slotkosten.py enthält `--dateien`: FOUND
- Commits 2af66bf2, eb71da96: FOUND
