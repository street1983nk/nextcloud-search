---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 11
subsystem: tests/kill-harness
tags: [ocr-slots, sigkill, sc2, guard, solo-retry, unclean-end, PAR-02, PAR-03]
requires:
  - "26-04: SlotPool, threadsicherer IndexBatchWriter"
  - "26-06: Staffel unter N Slots, Barriere"
  - "26-09: Solo-Wiederholung, multi_slot_pass-Merker"
  - "26-10: GuardWatch.restore/run_once, unclean_end"
provides:
  - "tests/slots_kill_harness.py: FileQueue (SQLite, PHP-Lease-Semantik) und Harness-Einstieg run/restore"
  - "tests/test_slots_kill.py: beide Kill-Fälle von D-26-08 als Linux-Test"
affects: [26-14 (CI-Beleg nach Push einsammeln)]
tech-stack:
  added: []
  patterns:
    - "Harness als eigener Prozess über sys.executable, gemeinsames tmp-Volume (queue.db, state.db, index, marks, pids.json)"
    - "Markerdateien started/added je file_id als Uhr für den Kill-Zeitpunkt"
    - "pids.json per Hintergrund-Thread atomar (tmp + replace)"
key-files:
  created:
    - backend/tests/slots_kill_harness.py
    - backend/tests/test_slots_kill.py
  modified: []
decisions:
  - "file_id reist als Inhalt der Scratch-Datei (fetch schreibt sie), nicht im Dateinamen: den Scratch-Namen job-<queue_id>.part vergibt der Poller, der Fetch sieht nur den Sink"
  - "Harness setzt lane.note_mode(parallel), damit der Anspruch die Index-Lane mit KIND_BATCH_INDEX_LANE[ocr] = 32 nimmt; auf Lane all kämen nur 2 OCR-Zeilen und damit nur 2 Slots"
  - "Der Lauf ruft GuardWatch.restore vor dem ersten Durchgang (wie der Lifespan) und am Ende GuardWatch.run_once; die Kill-Zahl wird vorher genommen und zurückgemeldet, damit sie ausgegeben und vom echten Tick gesehen wird"
  - "Nach dem Kill des Hauptprozesses killt der Test die verwaisten Kinder aus pids.json (Containertod nimmt sie mit), bevor der zweite Lauf startet"
  - "Pins nicht bewegt: der Orchestrator hat PACKAGE_TREE_HASH_TODAY/PACKAGE_FILES_TODAY nach dem Welle-4-Merge schon neu gemessen (67 Dateien, bb0c2382...), Nachmessung hier ergibt dieselben Werte"
metrics:
  duration: "ca. 45 min"
  completed: 2026-09-29
  tasks: 2
  files: 2
---

# Phase 26 Plan 11: Kill-Test für SC2 unter vier Slots Summary

Der Kill-Test von SC2 für beide Fälle aus D-26-08 läuft jetzt als pytest-Harness. Er nutzt den echten Poller mit injizierten `ocr_slots=4`, vier echte Sandbox-Kinder (sleep-Probe 1,5 s), den echten tantivy-Writer und die echte state.db. Die Warteschlange ist eine SQLite-Datei mit den Lease-Regeln der PHP-Seite und übersteht einen SIGKILL.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Datei-Warteschlange mit PHP-Lease-Semantik und Harness-Einstieg | 4299390a |
| 2 | Kill-Tests für beide Fälle (Pin-Messung ohne Änderung) | 5cc1a527 |

## Was gebaut wurde

- **FileQueue** (`tests/slots_kill_harness.py`): Tabelle queue (queue_id, file_id UNIQUE, kind, mime, size, retries, locked_at, verdict), dazu `failures` und `handovers`. Jede Methode läuft in einer eigenen `BEGIN IMMEDIATE`-Transaktion mit Commit. Die Regeln:
  - `claim` nimmt freie oder abgelaufene Zeilen in queue_id-Reihenfolge und zählt dabei retries hoch.
  - Pro Lane gilt ein eigenes KIND_BATCH aus der config: Index-Lane ocr 32, Lane all ocr 2.
  - Oberhalb von MAX_DELIVERIES wird eine Zeile als `failed(repeatedly_stuck)` abgeschrieben. Der Wert steht im PHP-Quelltext.
  - `claim` liefert das Lane-Echo zurück.
  - `unlock` gibt die Zeile frei und erstattet retries.
  - `acknowledge` löscht die erledigten Zeilen und schreibt failed nach `failures`.
  - `requeue` legt die Zeile nach `handovers` ab.
  - `top_up` meldet idle.
- **Harness-Einstieg** `main(argv)`, Aufruf `<volume> run|restore`:
  - `run` setzt Hardware auf 16 Kerne und 64 GiB, der Companion meldet "performance" und die Lane steht auf parallel.
  - Danach `GuardWatch.restore`, dann `Poller(..., pool=SlotPool(4), ocr_slots=4, headroom=64 GiB)`.
  - Der Lauf geht höchstens 20 Runden, bis die Warteschlange leer ist, und wartet den Lease-Ablauf ab, wenn nur noch gesperrte Zeilen übrig sind.
  - Am Ende laufen der Wächter-Tick und eine JSON-Zeile `{"cause", "kills", "waiting"}`.
  - `restore` gibt die Ursache als JSON aus.
  - `pids.json` wird laufend geschrieben, die Markerdateien `started-<id>` und `added-<id>` liegen unter `marks/`.
- **Tests** (`tests/test_slots_kill.py`, `skipif sys.platform != "linux"`):
  - Fall 1: SIGKILL an den Harness bei mindestens 2 added-Markern und mindestens 2 weiteren started-Markern. Danach gilt `multi_slot_pass == "performance"`, restore meldet `unclean_end`, und der zweite Lauf arbeitet alles ab. Am Ende ist die Warteschlange leer, `failures` ist leer, und jede der 12 file_ids steht genau einmal im Index (Term-Suche, `num_docs == 12`).
  - Fall 2: Sobald 4 pids da sind, 4 started-Marker und 0 added-Marker existieren, geht SIGKILL an genau ein Kind. Ergebnis: `kills == 1`, `cause == "oom_kill"`, die Warteschlange ist leer, `failures` ist leer, und jede Datei steht genau einmal im Index.
  - Harte Fristen: 20 s pro Wartezustand, 25 s pro Harness-Lauf. Im finally werden alle Harness-Prozesse gekillt und für jede pid aus `pids.json` ein killpg geschickt.

## Verifikation

- **Lokale Linux-Vorprüfung** lief im Docker-Container `ghcr.io/astral-sh/uv:python3.13-trixie-slim`, mit `uv sync --frozen` auf einer Kopie von backend/ und php/. Viermal grün, dreimal davon mit `--cpus=4` wie der CI-Runner. Fall 1 brauchte 11 bis 17 s, Fall 2 8 bis 10 s, die Gesamtdauer lag bei 19 bis 25 s. Das gilt nicht als CI-Beleg.
- **CI-Beleg steht aus:** Er kommt erst mit python.yml auf ubuntu-24.04 nach einem Push. Alles ist nur lokal committet, das Einsammeln folgt in Plan 26-14.
- Volle Suite unter Windows: 3880 passed, 22 skipped. Die beiden Kill-Tests sind übersprungen, die Pin-Tests grün.
- ruff check, ruff format --check, pyright latest (Windows sowie `--pythonplatform Linux` für die neuen Dateien) und vulture: alle grün.
- Akzeptanz-Greps: `class FileQueue` 1, `ocr_slots=4` 1, `run_probe("sleep"` 1, `retries` 8, beide Testnamen je 1, `sys.platform != "linux"` 1.
- `git diff --stat -- backend/src php`: leer.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] file_id über den Inhalt statt über den Dateinamen**
- **Found during:** Task 1
- **Issue:** Laut Plan sollte der Fetch-Fake eine Datei mit der file_id im Namen schreiben. Den Scratch-Namen (`job-<queue_id>.part`) vergibt aber der Poller, der Fetch bekommt nur den Hash-Sink.
- **Fix:** Der Fetch schreibt die file_id als Bytes, der Extraktor liest sie aus dem Pfad zurück.
- **Commit:** 4299390a

**2. [Rule 3 - Blockierend] Index-Lane im Harness gesetzt**
- **Found during:** Task 1
- **Issue:** Ohne parallelen Lane-Modus fragt der Poller ohne Lane, also "all". Dort gilt KIND_BATCH[ocr] = 2, das ergibt 2 Zeilen und damit 2 Slots, und N = 4 wird nie erreicht.
- **Fix:** Der Harness ruft `lane.note_mode(MODE_PARALLEL, REASON_NONE)`, das ist der Stand mit Embed-Runner neben der Schleife.
- **Commit:** 4299390a

**3. [Rule 1 - Bug] executescript außerhalb der Transaktion**
- **Found during:** Linux-Vorprüfung
- **Issue:** `executescript` committet selbst, dadurch schlug das anschließende COMMIT fehl.
- **Fix:** Das Schema läuft über eine eigene Verbindung ohne BEGIN.
- **Commit:** 4299390a

**4. Pin-Messung ohne Änderung an test_measurement_scripts.py**
- Die Datei steht in files_modified, aber der Orchestrator-Commit 46572f4 hatte die Pins nach dem Welle-4-Merge schon auf 67 Dateien und `bb0c2382...` gesetzt. Die Nachmessung mit 40b-baumhash.py ergab Paket 67 / `bb0c23829f83...` und PHP 75 / `460e2d6b...`, also identische Werte. Dieser Plan ändert nur Dateien unter tests/, die Pins bewegen sich also nicht.

### TDD-Hinweis

Task 2 ist `tdd="true"`, fügt aber kein Verhalten hinzu. Er ist ein reiner End-zu-End-Beleg für 26-04, 26-06, 26-09 und 26-10. Einen roten Commit gibt es deshalb nicht, die Tests waren nach der Korrektur des Harness-Fehlers sofort grün.

## Deferred Issues

- Das Rennfenster in `sandbox.py` `_start_child` (aus 26-06/26-09) bleibt offen, `sandbox.py` steht nicht in der Dateiliste. In vier Linux-Läufen trat es nicht auf. Fall 2 würde es als `kills == 0` oder als failed-Eintrag sichtbar machen.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. T-26-37 ist umgesetzt: Fristen bei jedem Warten, finally mit killpg, jeder Fall unter 30 s. T-26-38 ebenso: KIND_BATCH aus der paritätsgepinnten config, MAX_DELIVERIES aus dem PHP-Quelltext, retries, unlock und Quittung wie bei _WorkStock, Lease-Ablauf explizit. T-26-39 ist akzeptiert, alle Daten sind synthetisch.

## Self-Check: PASSED

- FOUND: backend/tests/slots_kill_harness.py
- FOUND: backend/tests/test_slots_kill.py
- FOUND: 4299390a
- FOUND: 5cc1a527
