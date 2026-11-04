---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
plan: 04
subsystem: backend (lifespan, queue, status, probe)
tags: [issue-37, backup-pause, lifespan, status, probe, tree-hash]
requires:
  - 41-03 (PauseCoordinator, Holds in allen Schreibern, Baumhash 9465a3ab)
provides:
  - CompanionChoice.paused (True nur bei JSON true, False bei lesbarer Antwort ohne Feld, None bei gescheitertem Lesen)
  - main._PAUSE, pause_wish_reader(), _a_pause_is_wanted(), _resume_after_the_pause(), attach_* vor jedem create_task
  - erster Wunsch-Lesevorgang in der Lifespan (PAUSE_READ_SECONDS = 5), danach Pause-Task mit PAUSE_STOP_SECONDS = 5
  - Rebuild should_stop = Shutdown oder Pause (D-41-20), kein Rebuild-Start in der Pause
  - /status pause (running|pausing|paused|unknown) und pausedSince
  - probe.START_PAUSED, ProbeRun(pause_wanted=...), POST /probe 409 {"state": "paused"}
  - pause.publish()/pause.pause_state() als Brücke zur Statusroute ohne Importzyklus
affects:
  - 41-05/41-06 (Companion setzt den Wunsch, Admin-Seite zeigt pause/pausedSince)
tech-stack:
  added: []
  patterns:
    - "Koordinator in der Lifespan vor dem ersten Schreiber, Anmeldung direkt nach der Konstruktion jedes Schreibers"
    - "conftest: BackupHoldDouble-Mixin für Schreiber-Doubles, autouse the_companion_wants_no_pause"
key-files:
  created: []
  modified:
    - backend/src/findling/nc/queue.py
    - backend/src/findling/main.py
    - backend/src/findling/worker/pause.py
    - backend/src/findling/worker/probe_run.py
    - backend/src/findling/probe.py
    - backend/src/findling/api/probe.py
    - backend/src/findling/api/status.py
    - backend/tests/conftest.py
    - backend/tests/test_backup_pause.py
    - backend/tests/test_main_lifespan.py
    - backend/tests/test_lifecycle.py
    - backend/tests/test_instance_marker.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_probe_endpoint.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Der erste Wunsch wird in der Lifespan vor dem yield gelesen (begrenzt auf PAUSE_READ_SECONDS = 5 s), nicht erst im Task: so ist der Start deterministisch, ein Rebuild startet bei 'nicht pausiert' wie bisher beim Start, und ein Nextcloud ohne Antwort hält den Heartbeat höchstens 5 s auf"
  - "on_resume = _resume_after_the_pause: fragt den Rebuild nur mit Arm-Marker und eigenem Volume (wie Enable und Lifespan), Fehler nur geloggt"
  - "Auf einem fremden Volume checkpointet der Koordinator nichts (databases=()), die Schreiber sind dort ohnehin stumm"
  - "pausedSince nur im Zustand paused, auch wenn der Koordinator noch einen Wert trägt; ohne Koordinator meldet /status running/null"
  - "ProbeRun fragt die Pause vor dem Rebuild: eine Pause, die einen Rebuild hält, heißt 'paused', nicht 'rebuilding'"
  - "CompanionChoice.paused hat den Default False (lesbare Antwort ohne Wunsch), nur der Fehlerpfad setzt None"
metrics:
  duration: "ca. 60 min"
  completed: 2026-11-04
  tasks: 2
  commits: 5
---

# Phase 41 Plan 04: Backup-Pause, Verdrahtung im Backend Summary

Das Backend liest den Pause-Wunsch über /profile, hält nach jedem Start alle Schreiber bis zum ersten Lesen, stoppt einen Rebuild zwischen zwei Bändern, meldet `pause`/`pausedSince` in /status und verweigert eine Probe in der Pause mit 409 `paused`; die Suche antwortet in der Pause weiter.

## Commits (RED vor feat)

| Hash | Nachricht |
|------|-----------|
| ed47ec95 | test(41-04): a restart in pause must not index before the wish is read (#37) |
| f0f5eb5f | feat(41-04): the lifespan holds every writer until the pause wish is read (#37) |
| 6e4aed2c | test(41-04): status names the pause and a check cannot start in it (#37) |
| c3fbaa27 | feat(41-04): status names the pause, a check cannot start in it (#37) |
| 997fa5cb | test(41-04): the package tree hash follows the pause wiring |

Alle als street1983nk <k.cherif@outlook.de>, keine Trailer-Zeilen. Kein Push.

## Task 1: Wunsch lesen, Koordinator in der Lifespan

- queue.py: `CompanionChoice.paused`; gelungene Antwort `payload.get("paused") is True`, Fehlerpfad `None`.
- main.py: `pause_wish_reader()` über `companion_reader()` mit `asyncio.wait_for(..., PAUSE_READ_SECONDS)`; `_build_the_pause` (state.db + vectors.db, rebuild_busy über `_REBUILDING`, probe_busy über `_PROBE_RUN.task`, on_resume `_resume_after_the_pause`); `publish(_PAUSE)`.
- attach vor create_task (`grep -n "attach_\|create_task" backend/src/findling/main.py`): guard_watch 1187 vor 1193, poller 1207 vor 1208, runner 1222 vor 1223, reconcile 1251 vor 1252, catch-up 1271 vor 1272; Pause-Task 1371 nach dem ersten `tick()`.
- Rebuild: `partial(_the_rebuild_should_stop, stop_event)`; `_start_the_rebuild_if_due` prüft `_a_pause_is_wanted()` vor und nach dem Thread-Sprung.
- Abbau: Pause-Task direkt nach der Probe, vor den Schreibern; `publish(None)`, `_PAUSE = None` am Ende.
- `enabled_handler` und `_arm_the_poller` unverändert (git diff ohne Zeile dort); Tests belegen, dass beide die Pause nicht aufheben.
- RED-Beleg: ed47ec95 gegen den alten Quellstand gelaufen, 13 Fehler (fehlendes `pause_wish_reader`, `paused`).

## Task 2: Status, Probe, Suche, Baumhash

- status.py: `pause: Literal[...] = "running"`, `pausedSince: int | None = None`, in `report()` aus `pause.pause_state()` gesetzt (alle Zweige, auch fremdes Volume).
- probe.py `START_PAUSED: Final = "paused"`; probe_run.py `pause_wanted` (Default `lambda: False`), vor `_rebuild_may_start` geprüft; api/probe.py dritter 409-Zweig, Docstring ergänzt; main.py übergibt `_a_pause_is_wanted`.
- test_search_answers_while_paused: echte Lifespan mit `indexed_volume`, Wunsch true, Zustand `paused` (Writer abgegeben, beide Checkpoints), /search liefert Kandidaten, /snippets 200 mit Fragment. Der Test war schon nach Task 1 grün (Beweistest, keine neue Logik nötig).
- Baumhash PACKAGE: 9465a3ab... -> 24580a26... (81 Dateien), mit dem Rezept und unabhängig mit find/sort/sed/sha256sum gerechnet; `-k tree_hash` 4 passed. PHP-Paar unverändert.

## Verifikation

- tests/test_backup_pause.py, test_main_lifespan.py, test_queue_client.py, test_status_endpoint.py, test_probe_endpoint.py, test_probe_run.py, test_status_leave_out.py, test_lifecycle.py, test_instance_marker.py, test_poller.py, test_catchup.py, test_phase40_audit.py grün.
- ruff check, ruff format --check, pyright (latest) 0 errors, vulture 80 grün.
- Kein neuer Meta-Schlüssel (kein `write_meta`/`set_meta` im Delta), keine U+2013/U+2014 im Delta.
- Volltestsuite in zwei Hälften (5,3 GB frei): 3623 passed / 49 skipped / 1 failed und 2889 passed / 254 skipped. Der eine Fehler (`test_extract_edge_paths.py::test_the_file_travel_path_writes_in_exactly_the_pinned_places`) stammt aus 41-03 (`Poller.reopen_after_backup` ruft `self._track.open`), poller.py ist in 41-04 unverändert; eingetragen in deferred-items.md.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Schreiber-Doubles der Lifespan-Suiten brauchen die Hold-Methoden**
- **Issue:** Die Lifespan meldet jetzt jeden Schreiber am Koordinator an; die Doubles in test_main_lifespan.py, test_lifecycle.py und test_instance_marker.py hatten kein `hold_for_backup` usw.
- **Fix:** `BackupHoldDouble`-Mixin in conftest.py; dazu ein autouse-Fixture `the_companion_wants_no_pause`, weil keine Testsuite einen Companion hinter /profile hat und sonst jede Lifespan in "unknown" hängen bliebe. Fälle zur Pause ersetzen es.
- **Commit:** ed47ec95

**2. [Rule 1] Bestehende companion_choice-Tests des Fehlerpfads**
- Zwei Gleichheitstests in test_queue_client.py erwarten jetzt `paused=None` beim gescheiterten Aufruf (gewolltes neues Verhalten, D-41-19).

**3. Erster Lesevorgang in der Lifespan statt nur im Task**
- Siehe Entscheidungen. Der Plan ließ offen, wann gelesen wird; ohne das wäre der Rebuild-Start beim Start nicht mehr deterministisch gewesen.

**4. Zugriffsfunktion in pause.py**
- `publish()`/`pause_state()` in worker/pause.py (vom Plan erlaubt: "in pause.py oder main.py"); pause.py stand nicht in files_modified.

**5. Prüfzeile `START_PAUSED = "paused"`**
- Die Konstante folgt der Hauskonvention `START_PAUSED: Final = "paused"` in findling/probe.py (dort stehen START_BUSY/START_REBUILDING); das wörtliche grep der Plan-Prüfzeile trifft deshalb nicht, `grep -rn 'START_PAUSED: Final = "paused"' backend/src` schon.

## Deferred Issues

- Siehe deferred-items.md: Schreibort-Gate rot seit 41-03 (Track-Öffnen nach dem Backup), vor 41-08 nachziehen.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche: kein neuer Endpunkt, kein Schreibweg für den Wunsch (nur Lesen über das bestehende /profile), zwei neue Statusfelder aus geschlossener Menge bzw. Zahl ohne Pfad. T-41-16 bis T-41-19 mit Tests (nur `is True`, unknown bei unlesbarer Route, 409 paused, laufende Probe hält pausing über probe_busy).

## Self-Check: PASSED

- Commits ed47ec95, f0f5eb5f, 6e4aed2c, c3fbaa27, 997fa5cb vorhanden; alle geänderten Dateien vorhanden; Gates grün.
