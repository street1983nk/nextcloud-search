---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 11
subsystem: api
tags: [probe, pruef-01, sc3, lifespan, status, info-xml]
requires:
  - phase: 27-02
    provides: probe.snapshot, Codes, START_BUSY/START_REBUILDING
  - phase: 27-09
    provides: worker/probe_run.ProbeRun (start, restore, recover, close)
provides:
  - "POST /probe (202 id, 409 busy mit id, 409 rebuilding, 503 ohne Lifespan, 422, 401) und GET /probe/state (immer 200, feste Feldmenge)"
  - "Status-Block probe {supported, running, step} und model.chunks"
  - "main.build_the_probe, main.companion_reader, main.active_probe_run, Poller.pool"
affects: [27-12, 27-14, 27-15]
tech-stack:
  added: []
  patterns: ["Zugriff des Routers auf den Lifespan-Zustand über eine FastAPI-Dependency mit spätem Import, in Tests per dependency_overrides ersetzbar"]
key-files:
  created:
    - backend/src/findling/api/probe.py
    - backend/tests/test_probe_endpoint.py
  modified:
    - backend/src/findling/api/status.py
    - backend/src/findling/main.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/worker/probe_run.py
    - backend/appinfo/info.xml
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_semantic_boundary.py
    - backend/tests/conftest.py
key-decisions:
  - "numbers im Zustand trägt nur die vorhandenen Schlüssel aus NUMBER_KEYS, keine Nullen für fehlende; startedAt/finishedAt als ganze Epoch-Sekunden, 0 statt null"
  - "Ein Start, der wirft, antwortet 503 unavailable mit Typnamen im Log, nie 500"
  - "Der Companion-Leser für recover baut seinen Client erst beim ersten Lesen; recover liest nur, wenn eine Probe eine fp32-Datei hinterlassen hat, ein gewöhnlicher Start baut also nichts"
  - "Shutdown: close() direkt nach note_shutdown_begins, dann bis PROBE_STOP_SECONDS (5 s) auf recover warten, danach cancel; erst dann stop_indexing"
  - "fetch von ProbeRun hat fetch_release_asset als Default, damit main den Download-Namen nicht trägt (Quelltext-Tor D-24-05 bleibt wörtlich grün)"
requirements-completed: [PRUEF-01]
metrics:
  duration: "ca. 60 min"
  completed: 2026-09-29
  tasks: 2
  files: 10
---

# Phase 27 Plan 11: Probe-Routen und Lifespan-Verdrahtung Summary

Die Vorab-Prüfung ist im Container erreichbar: POST /probe und GET /probe/state als ADMIN-Routen, der Status meldet probe {supported, running, step} und model.chunks, und ProbeRun lebt mit dem Lifespan (restore beim Start, recover als eigener Task, close vor Poller und Runner).

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Router api/probe.py, zwei ADMIN-Routen in info.xml, Routen-Ratsche | 17a854a5 |
| 2 | Statusblock probe, model.chunks, Lifespan-Verdrahtung, Tests | 5ee190a7 |

## Belege

- Acceptance-Greps: `<url>^/probe$</url>` 1, `<url>^/probe/state$</url>` 1, "Five routes|these five" 0, `class ProbeReport` 1, `chunks: int = 0` 1, `ProbeRun(` in main 1, `include_router(PROBE_ROUTER)` 1.
- test_probe_endpoint.py: 26 Fälle (Codes 202/409/409/422/503/401, Feldmenge, Messfreiheit, info.xml je Block, Lifespan-Aufbau, Reihenfolge restore/recover/close vor Poller-Stopp, Bau-Fehler kostet nur die Probe (K6), unterbrochene Probe nach Neustart nofit interrupted, Companion-Leser baut Client erst beim ersten Lesen).
- Volle Suite: 4100 passed, 25 skipped, 1 failed = erwarteter Baumhash-Pin `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` (neue Paketdatei api/probe.py; laut Auftrag nicht angefasst).
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Routenzähl-Ratsche mitgezogen**
- **Found during:** Task 1
- **Issue:** `test_semantic_boundary.py::KNOWN_ROUTES` zählt alle Routen der API-Schicht als Anti-Vakuitäts-Klausel.
- **Fix:** `/probe` und `/probe/state` ergänzt (der Plan verlangt, einen Routenzähl-Test zu nennen).
- **Commit:** 17a854a5

**2. [Rule 3 - Blocking] Poller.pool als öffentliche Eigenschaft**
- **Found during:** Task 2
- **Issue:** ProbeRun braucht den SlotPool des Pollers (shed_idle), der Poller hielt ihn nur privat.
- **Fix:** Nur lesende Eigenschaft `pool` in worker/poller.py (Datei nicht im Plan).
- **Commit:** 5ee190a7

**3. [Rule 3 - Blocking] fetch-Default in ProbeRun statt Übergabe in main**
- **Found during:** Task 2
- **Issue:** `test_the_start_downloads_nothing_and_asks_no_precision` verbietet `fetch_release_asset` im Quelltext von main.py (D-24-05).
- **Fix:** ProbeRun bekommt `fetch=fetch_release_asset` als Default; main übergibt nichts. Der Download läuft weiter nur in einer vom Admin gestarteten Probe.
- **Commit:** 5ee190a7

**4. [Rule 2 - Testhygiene] probe.reset im conftest**
- **Found during:** Task 2
- **Issue:** Der Lifespan stellt den Probe-Zustand wieder her (etwa interrupted); ohne Reset wäre er in Folgefällen sichtbar.
- **Fix:** `probe_module.reset()` im autouse-Fixture neben profile/precision/lane/guard.
- **Commit:** 5ee190a7

**5. [Rule 2 - Korrektheit] Warten auf recover im Shutdown**
- **Found during:** Task 2
- **Issue:** Ein sofortiges cancel nach close() hätte recover mitten in einer Companion-Antwort abgebrochen.
- **Fix:** Nach close() bis PROBE_STOP_SECONDS (5 s) warten, dann cancel.
- **Commit:** 5ee190a7

### Weitere Abweichungen

- `active_probe_run`, `_PROBE_RUN` und die Router-Einbindung kamen schon mit Task 1, weil die Routentests den gemounteten Router brauchen; Task 2 baute den Lifespan-Teil dazu.
- TDD: Tests und Umsetzung je Task in einem Commit, kein getrennter RED-Commit.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche über T-27-34 bis T-27-38 hinaus. Die Routen antworten nur mit Codes, Zahlen und der Id; der Companion-Leser von recover ruft nur die bestehende Profilroute.

## Offene Punkte für den Orchestrator

- Baumhash-Pin in test_measurement_scripts.py nach dem Merge neu messen (neue Datei api/probe.py, geänderte main.py, status.py, poller.py, probe_run.py).

## Self-Check: PASSED

- FOUND: backend/src/findling/api/probe.py, backend/tests/test_probe_endpoint.py
- FOUND: 17a854a5, 5ee190a7
