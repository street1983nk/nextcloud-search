---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 10
subsystem: worker
tags: [memory-guard, lifespan, state-db, PAR-03]
requires: ["26-03", "26-06"]
provides: ["GuardWatch (restore, run, run_once, note_shutdown_begins, aclose)", "Waechter-Task im Lifespan"]
affects: ["backend/src/findling/main.py", "26-11 (Baumhash-Pins neu messen, watch.py ist neu)"]
tech-stack:
  added: []
  patterns: ["EmbedRunner-Lebenszyklus", "eigene state.db-Verbindung ohne Anlegen (wie reconcile._open_state)"]
key-files:
  created:
    - backend/src/findling/worker/watch.py
    - backend/tests/test_watch.py
  modified:
    - backend/src/findling/main.py
    - backend/tests/test_main_lifespan.py
decisions:
  - "GuardWatch legt state.db nie an (Anlegen und Marken-Seeding gehoeren dem Poller); ohne Datei bleibt die Absenkung im Speicher und wird beim naechsten Tick nachgeschrieben"
  - "persist=False auf fremdem Volume (DI-06.1-22): sonst wuerde note_shutdown_begins den Unrein-Merker der anderen Instanz loeschen"
  - "Geschrieben wird nur bei geaenderter guard.snapshot().revision; ein fehlgeschlagener Schreibversuch laesst die Revision offen, der naechste Tick versucht es erneut"
  - "In economy wird der Ausloeser nur auf debug geloggt, keine Absenkung, nichts geschrieben"
metrics:
  duration: "ca. 25 min"
  completed: 2026-09-29
  tasks: 2
  files: 4
---

# Phase 26 Plan 10: Speicherwächter im Lifespan Summary

Der Speicherwächter läuft jetzt als Lifespan-Task. Er senkt bei zwei qualifizierten max-Ereignissen, bei einem steigenden oom_kill oder bei einem gemeldeten Kind-Kill die wirksame Stufe um eine. Die Absenkung wird in state.db (meta guard_*) gespeichert und vor der ersten Poller-Runde wiederhergestellt. Ein gesetzter multi_slot_pass beim Start wird als Unrein-Ende gewertet. Beim geordneten Herunterfahren leert der Wächter den Merker als allererste Handlung.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | GuardWatch mit Tick, Persistenz und Wiederherstellung | 15ec1074 | worker/watch.py, tests/test_watch.py |
| 2 | Wächter im Lifespan | 1ad3bddd | main.py, tests/test_main_lifespan.py |

## Umsetzung

- `GuardWatch(state_path, events, headroom, clock, wall_clock, tick, persist)`: Der Konstruktor macht kein I/O. Die eigene Verbindung wird über `open_store` erst bei Bedarf geöffnet, und nur wenn die Datei schon existiert.
- `restore()`: Liest meta in einem Thread und ruft `guard.restore` auf. Bei einem gültigen multi_slot_pass über economy folgt `guard.lower(CAUSE_UNCLEAN_END, effective=<gespeicherte Stufe>, chosen=<multi_slot_chosen>)`. Danach wird der Merker geleert und die neue Absenkung persistiert.
- `run_once()`: Liest beide Werte per `asyncio.to_thread`, holt `guard.take_child_kills()` und ruft `Escalation.observe` auf. Über economy folgt dann `guard.lower`. Die Log-Zeile trägt nur `cause=… level=…`, kein Token.
- `run()`: Fängt jede Ausnahme und loggt nur den Typnamen. Die Pause endet sofort, wenn das Stop-Ereignis kommt.
- main.py: `_GUARD_WATCH` wird nach `note_hardware` gebaut, `restore()` steht in try/except. Der Task `_guarded_watch` wird vor dem Poller erzeugt. Im finally steht `note_shutdown_begins()` als erste Anweisung. Der Wächter wird nach dem Poller gestoppt: `wait_for` mit `GUARD_STOP_SECONDS = 5.0`, danach `cancel`, `gather` und `aclose`.

## Verifikation

- `pytest tests/test_watch.py tests/test_guard.py`: 55 grün (alle 11 Behavior-Fälle, dazu fehlende state.db und Log ohne Token)
- `pytest tests/test_main_lifespan.py`: 58 grün (4 Behavior-Fälle plus ein statischer Reihenfolge-Test)
- Volle Suite mit `--deselect …tree_hash…`: 3867 passed, 20 skipped
- ruff check, ruff format --check, pyright (latest), vulture: grün
- `git diff --stat -- php backend/src/findling/worker/poller.py`: leer
- Baumhash-Pins nicht angefasst (Pin-Eigentümer 26-09, Nachmessung 26-11)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Korrektheit] persist-Schalter für fremde Volumes**
- **Found during:** Task 2
- **Issue:** Auf einem Volume einer anderen Instanz (DI-06.1-22) hätte der Wächter deren state.db gelesen und beim Herunterfahren ihren multi_slot_pass-Merker geleert. Damit wäre der Unrein-Ende-Beweis der anderen Instanz verloren gegangen.
- **Fix:** Neuer Konstruktor-Parameter `persist: bool = True`. main.py übergibt `persist=not shared_volume.other`. Ohne Persistenz arbeitet der Wächter nur im Speicher.
- **Commit:** 1ad3bddd

**2. [Rule 2 - Korrektheit] state.db wird nie vom Wächter angelegt**
- **Found during:** Task 1
- **Issue:** Laut open_store-Doku dürfen nur der Poller die Datei anlegen und die Versionsmarken säen.
- **Fix:** `_open()` öffnet nur eine bestehende Datei, wie `reconcile._open_state`. Der Test `test_restore_without_a_state_db_creates_none` sichert das ab.
- **Commit:** 15ec1074

### TDD-Hinweis

Tests und Implementierung sind pro Task im selben Commit gelandet. Einen separaten roten test-Commit gibt es nicht. Der Plan ist `type: execute`, deshalb gilt kein Plan-TDD-Gate.

## Known Stubs

Keine.

## Threat Flags

Keine neuen Angriffsflächen. T-26-33 bis T-26-36 sind umgesetzt: restore vor dem Poller, Validierung über guard.restore, Reihenfolge-Test für note_shutdown_begins, keine Token in Logs.

## Self-Check: PASSED

- FOUND: backend/src/findling/worker/watch.py
- FOUND: backend/tests/test_watch.py
- FOUND: 15ec1074
- FOUND: 1ad3bddd
