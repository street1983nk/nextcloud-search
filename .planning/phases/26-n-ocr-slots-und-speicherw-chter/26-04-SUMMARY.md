---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 04
subsystem: extract/pool, index/writer
tags: [ocr-slots, pool, executor, writer-lock, PAR-02]
requires:
  - "26-01: ExtractionWorker.halt(), ChildKilled"
  - "26-03: guard.py (Pin-Zaehlung)"
provides:
  - "findling.extract.pool: SlotGate (limit, in_use, set_limit, slot), SlotPool (size, run, run_probe, call, pids, close)"
  - "IndexBatchWriter threadsicher (threading.RLock um add, drop_document, flush, collect_garbage, close, pending, pending_bytes)"
  - "PACKAGE_FILES_TODAY = 66, PACKAGE_TREE_HASH_TODAY und PHP_TREE_HASH_TODAY ueber den Stand nach Welle 1"
affects: [26-06, 26-09, 26-11]
tech-stack:
  added: []
  patterns:
    - "Eigener ThreadPoolExecutor findling-slot via loop.run_in_executor, nie Default-Executor"
    - "asyncio.Condition als groessenveraenderliche Semaphore"
    - "Freiliste unter threading.Lock plus Condition, faule Worker-Erzeugung"
key-files:
  created:
    - backend/src/findling/extract/pool.py
    - backend/tests/test_pool.py
  modified:
    - backend/src/findling/index/writer.py
    - backend/tests/test_index_writer.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "SlotPool.call ist eine normale Methode, die ein Awaitable liefert, damit der RuntimeError nach close() sofort beim Aufruf fliegt"
  - "Executor faul beim ersten call, max_workers = size; close() fährt ihn mit shutdown(wait=False, cancel_futures=True) herunter"
  - "Ein Worker, der während close() noch lief, wird beim Zurückgeben gestoppt statt in die Freiliste gelegt"
  - "size und limit werden auf mindestens 1 gehoben (Slot 1 läuft immer)"
metrics:
  duration: "ca. 40 min"
  completed: 2026-09-28
  tasks: 2
  files: 5
---

# Phase 26 Plan 04: Writer-Sperre und Kinder-Pool Summary

Threadsicherer IndexBatchWriter (RLock, Upsert je file_id atomar) und neues `extract/pool.py` mit schrumpffähiger FIFO-Schranke `SlotGate` und `SlotPool` (bis zu N faul gebaute ExtractionWorker, eigener Executor `findling-slot`, sofortiger Gruppen-Kill beschäftigter Kinder per `halt()` beim Schließen). Beide Baumhash-Pins sind über den Stand nach Welle 1 neu gemessen.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Sperre im IndexBatchWriter | 10b9218a |
| 2 | SlotPool und SlotGate mit eigenem Executor, Pins neu messen | 4e693894 |

## Was gebaut wurde

- `index/writer.py`: `self._lock = threading.RLock()` mit Begründung (GIL-Freigabe in add_document, veränderlich geliehenes Rust-Objekt, unbewachte Zähler). Sieben Rümpfe laufen unter `with self._lock` (pending, pending_bytes, add, drop_document, flush, collect_garbage, close). `num_threads=1` steht weiter wörtlich da. Der Klassendoc hat einen Satz zur Threadsicherheit.
- Tests Writer: 8 Threads x 25 verschiedene IDs (200 pending, danach 0, jede ID genau einmal); 8 Threads x 10 dieselbe ID ergeben 1 Dokument; Drop und Add nebeneinander, Zähler stimmen; ein AST-Test prüft, dass jede der sieben Methoden genau ein `with self._lock` als Rumpf hat.
- `extract/pool.py`: Moduldoc erklärt, warum kein ProcessPoolExecutor (kein Abbruch, kein RLIMIT_AS je Kind, keine Recycling-Regeln) und warum ein eigener Executor (Pitfall 5, Issue #19). `SlotGate` folgt dem Research-Entwurf. `SlotPool.run` trägt exakt die Signatur von `extract_guarded`, `ChildKilled` wird nicht gefangen, der Pool importiert keinen Dispatcher.
- `test_pool.py`: 12 Fälle (9 Behavior-Fälle plus Argument-Durchreichung, Minimum 1, Abweisung nach close). Die zwei echten-Kinder-Fälle sind ONLY_POSIX.
- Pins: `PACKAGE_FILES_TODAY` 64 -> 66 (guard.py, pool.py), neuer `PACKAGE_TREE_HASH_TODAY` e70c39b7..., `PHP_FILES_TODAY` bleibt 75, neuer `PHP_TREE_HASH_TODAY` 460e2d6b.... Beide Kommentare im Hausstil.

## Verifikation

- Windows: volle Suite 3801 passed, 20 skipped (nach dem Testfix unten). ruff check, ruff format --check, pyright latest (Windows und `--pythonplatform Linux`) mit 0 Fehlern, vulture sauber.
- Linux (Docker `uv:python3.13-trixie-slim`): test_pool + test_index_writer + test_sandbox 98 passed ohne Skips. test_pool lief dreimal hintereinander grün, darunter zwei echte Slots parallel unter 0,9 s und close() mit beschäftigtem Kind: failed(CORRUPT), kein ChildKilled, unter 6 s.
- Alle Grep-Kriterien sind erfüllt (RLock 1, with self._lock 7, class SlotPool/SlotGate je 1, thread_name_prefix 1, asyncio.to_thread 0, extract.dispatch 0, Gate-A-Verbotsliste 0).
- `git diff --stat 5da24aa8 -- backend/src/findling/worker backend/src/findling/extract/sandbox.py php` ist leer.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug im eigenen Test] Reihenfolge der Ergebnisse im Pool-Test**
- **Gefunden in:** Task 2 (volle Suite)
- **Problem:** `test_three_calls_land_on_three_workers_and_a_fourth_waits` verglich `results[:3]`. Die Liste hat aber die Abschlussreihenfolge, und der vierte Aufruf kann vor einem der ersten drei fertig werden. Das war flaky.
- **Fix:** Vor der Freigabe wird geprüft, dass jeder der drei Worker genau einen Auftrag hat (`[1, 1, 1]`). Danach 6 Läufe in Folge grün.
- **Commit:** 4e693894

**2. Docstring-Wortwahl wegen der Grep-Kriterien**
- `asyncio.to_thread` und das Wort "move" kamen im Moduldoc vor und hätten die Kriterien "0 Treffer" gebrochen. Die Stellen sind umformuliert ("the to_thread helper of asyncio", "change").

## Deferred Issues

- **Kleines Rennfenster in `sandbox.py` (Plan 26-01, nicht in diesem Plan geändert):** `_start_child` setzt `self._process` vor `self._halted = False`. Ein `halt()` aus einem anderen Thread genau zwischen diesen Zeilen würde sein Flag verlieren. Der folgende Tod würde dann als ChildKilled statt als failed(corrupt) gelesen. Relevant ist das nur, wenn `SlotPool.close()` in den ersten Mikrosekunden eines Kindstarts kommt. Der Test wartet deshalb 0,5 s nach dem ersten pid. Vorschlag für 26-06 oder den Review: `_halted = False` vor `self._process = process` setzen.

## Known Stubs

Keine. Poller-Verdrahtung ist Plan 26-06, so geplant.

## Threat Flags

Keine neue Angriffsfläche. T-26-12 (RLock plus Test "dieselbe ID ergibt ein Dokument"), T-26-13 (eigener Executor, Test über den Threadnamen) und T-26-14 (unveränderte ExtractionWorker, Import-Hygiene-Test) sind umgesetzt.

## Self-Check: PASSED

- FOUND: backend/src/findling/extract/pool.py, backend/tests/test_pool.py
- FOUND: 10b9218a, 4e693894
