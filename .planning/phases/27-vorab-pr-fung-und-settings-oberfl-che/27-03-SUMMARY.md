---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 03
subsystem: backend/guard, backend/extract
tags: [guard, pool, review-fix, probe]
requires: []
provides:
  - "guard: atomarer Zustand _STATE (frozen _State), Escalation.rebase(events)"
  - "extract.pool: Submit unter Sperre, SlotPool.shed_idle() -> int"
affects:
  - backend/src/findling/api/status.py (liest snapshot() über to_thread, unverändert)
  - Probe-Pläne der Phase 27 (nutzen shed_idle und rebase)
tech-stack:
  added: []
  patterns: ["unveränderliche Zustandsreferenz, Austausch per dataclasses.replace (wie profile.note_cap)"]
key-files:
  created: []
  modified:
    - backend/src/findling/guard.py
    - backend/src/findling/extract/pool.py
    - backend/tests/test_guard.py
    - backend/tests/test_pool.py
decisions:
  - "Auch die Slot-Felder (note_slots) liegen im selben _State, damit snapshot() genau eine Referenz liest"
  - "shed_idle weckt Wartende (notify_all), weil _built sinkt und wieder gebaut werden darf"
metrics:
  duration: "ca. 25 min"
  completed: 2026-09-29
requirements: [PRUEF-01]
---

# Phase 27 Plan 03: IN-01/IN-02-Fixes plus shed_idle und rebase Summary

Der Wächter-Zustand liegt jetzt in einem unveränderlichen `_State`, den jeder Setter in genau einer Zuweisung tauscht; `SlotPool.call` übergibt unter der Sperre und meldet sich im Shutdown-Fenster mit der eigenen Meldung; `shed_idle()` und `Escalation.rebase()` stehen für die Probe bereit.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | IN-01 atomarer Wächter-Snapshot und Escalation.rebase | 0ef21b91 |
| 2 | IN-02 Submit unter der Sperre und SlotPool.shed_idle | 9856693c |

## Belege

- `global`-Zeilen in guard.py: 200 (`_set_cap`: `_STATE`), 280 (`note_slots`: `_STATE`), 286/293 (Kill-Zähler `_KILLS`), 322 (`reset`: `_STATE, _KILLS`). Je Setter genau eine Zustandsreferenz.
- `def rebase` (Zeile 157) und `def shed_idle` je einmal vorhanden.
- RED-Beleg IN-01: der Strukturtest liefert gegen die alte guard.py die Globals `_CAP, _CAUSE, _CHOSEN, _REVISION, _SINCE, _TOKEN` in `_set_cap` und schlägt fehl. Dazu ein Thread-Leser-Test mit Paarprüfung gegen alle geschriebenen Tupel.
- RED-Beleg IN-02: der Executor-Double wirft "cannot schedule new futures after shutdown"; der alte Stand hätte diese Meldung durchgereicht, der Test verlangt exakt "this SlotPool is closed".
- Tests: test_guard/test_watch/test_status_endpoint/test_poller 297 passed, 1 skipped; test_pool/test_poller 171 passed, 3 skipped. ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber.

## Deviations from Plan

None - plan executed exactly as written. Kleinigkeit: die geplanten `noqa`-Kommentare (BLE001, SLF001) sind im Regelsatz nicht aktiv (RUF100), daher als normale Kommentare geschrieben.

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: backend/src/findling/guard.py, backend/src/findling/extract/pool.py, backend/tests/test_guard.py, backend/tests/test_pool.py
- FOUND: 0ef21b91, 9856693c
