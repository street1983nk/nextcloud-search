---
phase: 25-einbettungsspur-und-modellwahl
plan: 10
subsystem: lifespan
tags: [embed-runner, lifespan, rebuild, release-task, PAR-01, PAR-04, SC3]
requires: ["25-09"]
provides:
  - "findling.main: _EMBEDDING, active_embedding(), _guarded_embedding, EMBEDDING_STOP_SECONDS, _wait_for_the_stand_down"
  - "Runner im Lifespan: Start über poller.track, attach_runner, Bewaffnen/Stilllegen mit dem Poller, Abbau vor dem Poller"
  - "Rebuild: Runner vor dem Poller stillgelegt, _arm_the_poller bewaffnet beide"
  - "Freigabe-Task fragt track.busy und ruft track.release_cutter"
affects:
  - "25-11 (Worker-Dateien parallel; Pin nach dem Merge der Welle 5 neu messen)"
  - "25-12 (Status/Endmessung über den verdrahteten Runner)"
tech-stack:
  added: []
  patterns:
    - "Dritter langlebiger Nebenläufer nach dem Muster _guarded_reconcile"
    - "Abbau in der Reihenfolge Rebuild, Runner, Poller, Reconcile, Freigabe"
key-files:
  created: []
  modified:
    - backend/src/findling/main.py
    - backend/tests/test_main_lifespan.py
    - backend/tests/test_lifecycle.py
    - backend/tests/test_instance_marker.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Runner wird vor dem Poller abgebaut, weil poller.aclose den gemeinsamen Track schließt"
  - "Eigenes Stopp-Budget EMBEDDING_STOP_SECONDS = 30 s in main.py (RUNNER_STAND_DOWN_SECONDS = 120 s ist für den Rebuild, nicht für den Abbau)"
  - "Freigabe-Task prüft track.busy UND die gehaltenen Zeilen beider Treiber (Pitfall 3 bleibt gewahrt)"
  - "Beim Rebuild wird der Runner mit STAND_DOWN_SECONDS stillgelegt; ein Nein des Runners heißt wie beim Poller: nichts wird umbenannt"
metrics:
  duration: "ca. 45 min"
  completed: 2026-09-28
  tasks: 2
  files: 5
requirements: [PAR-01, PAR-04]
---

# Phase 25 Plan 10: Runner im Lebenslauf des Containers Summary

Der EmbedRunner läuft jetzt als eigener Task im Lifespan über dem Track des Pollers. Er wird mit dem Poller bewaffnet und stillgelegt, beim Rebuild vor ihm heruntergefahren und beim Abbau vor ihm mit Zeilenrückgabe geschlossen. Der Freigabe-Task fragt den Track statt nur den Poller.

## Umsetzung je Task

**Task 1: Runner-Task im Lifespan** (bc3624f)
- `_EMBEDDING`, `active_embedding()`, `_guarded_embedding` (gebaut wie `_guarded_reconcile`: CancelledError zuerst, sonst nur der Typname im Log).
- Lifespan baut nach dem Poller `EmbedRunner(track=_POLLER.track)` ohne I/O, dann `_POLLER.attach_runner(...)`, eigenes `stop_embedding` und `create_task(_guarded_embedding(...))`. Kein Download und keine Präzisionsfrage im Start (D-24-05).
- Bewaffnen/Stilllegen im `enabled_handler` und im Lifespan über `(active_poller(), active_reconcile(), active_embedding())`.
- Abbau direkt nach dem Rebuild und vor dem Poller: `wait_for(shield(task), EMBEDDING_STOP_SECONDS)`, sonst cancel und gather, dann `suppress(Exception): unlock_held()`, `aclose()`, Global auf None.
- Tests: Start über den Track des Pollers und attach, Bewaffnen/Stilllegen per Enable und per Marke, Economy mit echtem Runner über mindestens drei Runden ohne einen Aufruf der Client-Fabrik (lane inline/economy), Abbau-Journal `unlock_held` vor `aclose` genau einmal, fehlschlagendes unlock hält den Abbau nicht auf, Runner über dem Budget wird abgebrochen und gibt trotzdem zurück, ein Runner mit Ausnahme ist eine Logzeile mit Typname ohne Pfad, statischer Test gegen `fetch_release_asset`/`procure_fp32`.

**Task 2: Rebuild, Freigabe-Task, Pins** (2aaa91c)
- `_stand_the_poller_down`: erst `runner.stand_down(budget=STAND_DOWN_SECONDS)`, dann der Poller, beide über `run_coroutine_threadsafe` und den neuen Helfer `_wait_for_the_stand_down`. Steht der Runner nicht ab, wird nichts umbenannt und der Poller gar nicht erst gefragt. Den Index-Handle gibt danach `poller.stand_down` über `track.close` ab.
- `_arm_the_poller`: bewaffnet Poller und Runner, nur wenn die Marke da ist.
- `_release_when_idle`: `track.busy` oder gehaltene Zeilen eines Treibers verhindern die Freigabe. Nach erfolgreichem `release_if_idle` wird `track.release_cutter` im Thread aufgerufen. Docstring: zwei Treiber, ein Eigentümer, Idle-Guard aus 25-02.
- Tests: Zeile im Track in Arbeit (nicht vom Poller gehalten) blockiert; vom Runner gehaltene Zeilen blockieren; ruhiger Track mit Freigabe ruft `track.release_cutter`; Rebuild mit echtem Poller und Runner legt beide still und bewaffnet beide wieder; ein Runner, der nicht absteht, lässt den Poller bewaffnet (Reihenfolge belegt); ohne Marke wird der Runner nicht wieder bewaffnet.
- Pin: `PACKAGE_FILES_TODAY = 64` unverändert, `PACKAGE_TREE_HASH_TODAY = 8a07deed...c3b4df1` über den eigenen Worktree-Baum, Kommentarzeile im Hausstil.

## Verifikation

- `uv run pytest -q`: 3669 passed, 16 skipped (volle Suite inkl. Pins)
- ruff check, ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest, 0 Fehler), vulture `src tests --min-confidence 80`: grün
- Akzeptanz-Greps in main.py: `async def _guarded_embedding` 1, `def active_embedding() -> EmbedRunner | None` 1, `attach_runner(` 1, `fetch_release_asset|procure_fp32` 0, `track.busy` 1, `poller.busy` 0, `track.release_cutter` 1, `stand_down(budget=STAND_DOWN_SECONDS)` 2
- `git diff --stat 9e65150 -- php backend/src/findling/worker`: leer

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fake-Poller in test_instance_marker.py und test_lifecycle.py**
- **Gefunden in:** Task 1
- **Problem:** Der Lifespan fragt den Poller jetzt nach `track` und `attach_runner`. Die Fake-Poller mehrerer Testdateien kannten beides nicht. `test_instance_marker.py` steht nicht in der Dateiliste des Plans.
- **Fix:** `track = EmbeddingTrack()` (Konstruktor ohne I/O) und ein leeres `attach_runner` in den Fakes. Keine Aussage eines bestehenden Tests geändert.
- **Commit:** bc3624f

**2. [Rule 2 - Korrektheit, Pitfall 3] Freigabe fragt zusätzlich die gehaltenen Zeilen beider Treiber**
- **Gefunden in:** Task 2
- **Problem:** Nur `track.busy` zu fragen hätte die bisherige Sperre verloren: Ein Pass zwischen zwei Zeilen seines Anspruchs hält Zeilen, aber der Track ist in dem Moment ruhig. `poller.release_cutter` hatte das bisher mit abgefangen. Mit dem Wechsel auf `track.release_cutter` wäre dieser Schutz weggefallen.
- **Fix:** `track.busy or any(driver.busy for driver in (poller, runner))`. Das Grep-Kriterium `poller.busy` = 0 bleibt erfüllt, die Absicht (der Runner zählt mit) auch. Test `test_rows_held_by_the_runner_keep_both_holders`.
- **Commit:** 2aaa91c

### Zusätze

- `EMBEDDING_STOP_SECONDS = 30.0` als benannte Konstante in main.py. Eine Konstante in worker/embedding.py kam nicht in Frage, weil 25-11 diese Datei in dieser Welle besitzt.
- `_wait_for_the_stand_down` als gemeinsamer Warte-Helfer für Runner und Poller. Die Fehlerzeile nennt jetzt "embed runner" oder "indexing task".
- Die Task-2-Tests liegen in `test_main_lifespan.py` statt in `test_lifecycle.py`. Dort stehen schon die Helfer (`_ticks`, `_EngineSpy`, `_FakePoller`) und die bestehenden Tests zu Rebuild und Freigabe. Eine Kopie der Helfer wäre eine zweite Wahrheit gewesen.

## TDD Gate Compliance

Tests und Umsetzung je Task in einem `feat`-Commit, ohne separaten RED-Commit. Die neuen Tests importieren `active_embedding` und brauchen `track` am Fake-Poller, beides gab es vor der Umsetzung nicht. Geprüft ist: Die Freigabe-Tests schlagen gegen den alten Stand fehl, weil dort `poller.release_cutter` und `poller.busy` gefragt wurden.

## Offene Punkte

- **Pin nach dem Merge der Welle 5:** 25-11 ändert `worker/embedding.py` und `worker/poller.py` parallel. Der Orchestrator misst `PACKAGE_TREE_HASH_TODAY` nach dem Merge neu.
- **Beobachtung für 25-11/25-12 (nicht behoben, Worker-Dateien gehören 25-11):** Nach einem Rebuild oder beim ersten Start in Standard kann eine Runner-Runde laufen, bevor der Poller den Track in `_open` wieder geöffnet hat. `embed_row` wirft dann `RuntimeError`. `run` fängt das ab, gibt die Zeilen per unlock zurück und wartet ab. Es geht keine Zeile verloren, aber im Log steht einmal "embed round ended in an unexpected RuntimeError". Ein Öffnen des Tracks im Runner oder ein Tor auf `track.ready` würde das glätten.
- CI-Nachweis T3 (SC1) weiter offen bis zum nächsten Push (Owner-Entscheid).

## Known Stubs

Keine.

## Threat Flags

Keine neue Oberfläche. Der Runner nutzt die Queue-Routen, die schon in 25-09 im Register stehen. Der Start lädt nichts (T-25-45, statischer Test). Die Logzeilen tragen nur Typnamen.

## Self-Check: PASSED

- FOUND: backend/src/findling/main.py (geändert), backend/tests/test_main_lifespan.py (geändert)
- FOUND: bc3624f, 2aaa91c
