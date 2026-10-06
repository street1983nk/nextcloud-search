---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 05
subsystem: worker
tags: [probe, poller, embed-runner, guard, pause]
requires:
  - phase: 27-02
    provides: probe.hold/release/held, probe.pending_load_bytes
  - phase: 27-03
    provides: guard.Escalation.rebase
provides:
  - Poller.hold_for_probe / release_probe_hold / probe_held
  - EmbedRunner.hold_for_probe / release_probe_hold
  - EmbedRunner._need über probe.pending_load_bytes
  - GuardWatch setzt die Absenkung während der Probe plus einem Nachlauf-Tick aus
affects: [27-09]
tech-stack:
  added: []
  patterns: ["eigenes asyncio.Event als Haltesignal neben _armed, bei Geburt gesetzt"]
key-files:
  created: []
  modified:
    - backend/src/findling/worker/poller.py
    - backend/src/findling/worker/embedding.py
    - backend/src/findling/worker/watch.py
    - backend/tests/test_poller.py
    - backend/tests/test_embedding_runner.py
    - backend/tests/test_watch.py
key-decisions:
  - "Haltezweig in run steht NACH dem Armed-Check, sodass ein silence während des Halts nach release wirksam bleibt"
  - "pending_load_bytes deckt EMBED_ACTIVATION_BYTES + EMBED_LANE_RESERVE_BYTES bereits ab; _need ruft es mit embed_slots=0, writer_heap_delta=0 und ist bitgleich"
  - "Gehaltener Wächter-Tick gibt guard.CAUSE_NONE zurück und ruft _persist_if_changed weiter, damit eine Admin-Bestätigung auch während der Probe persistiert"
requirements-completed: [PRUEF-01]
duration: 25min
completed: 2026-09-29
---

# Phase 27 Plan 05: Indexierungs-Pause und Wächter-Aussetzung für die Probe Summary

Poller und EmbedRunner halten per eigenem Event für die Vorab-Prüfung an, ohne laufende Staffeln abzubrechen; der Wächter verschiebt während der Probe und einen Tick danach nur die Basis und verwirft Kind-Kills.

## Accomplishments
- Poller: `_probe_release`-Event, `hold_for_probe`, `release_probe_hold`, `probe_held`; `run` wartet bei Halt auf Freigabe oder Stop, die laufende Runde quittiert regulär (kein `unlock_held`, kein Writer-Close), `arm`/`silence` unverändert.
- EmbedRunner: gleiches Muster; `parked` bleibt während des Halts gesetzt.
- `EmbedRunner._need` rechnet über `probe.pending_load_bytes`; die fünf Einzelkonstanten-Importe in embedding.py entfallen.
- GuardWatch: Merker `_probe_trailing`; bei `probe.held()` oder Nachlauf `rebase(events)`, `take_child_kills()` verworfen, kein `observe`. Slot-Drossel im Poller unberührt.

## Task Commits
1. Task 1: Haltesignal in Poller und EmbedRunner, `_need` über neutrale Rechnung: `f5c419c3`
2. Task 2: Wächter setzt die Absenkung während der Probe aus: `ea0dec9f`

## Tests
- test_poller.py: Halt lässt laufende Runde mit Quittung enden, danach Weiterlauf; Stop während Halt; Halt armt/stillt nicht, silence bleibt nach release wirksam.
- test_embedding_runner.py: Halt, parked, Weiterlauf; Halt armt nicht; Paritätstest `_need` gegen die alte Formel (vier Fälle).
- test_watch.py: Kill während Halt verworfen; Nachlauf-Tick ausgesetzt, danach zählt `oom_kill` wieder; Kind-Kill zählt ab dem zweiten Tick wieder.
- Gates grün: ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture; test_poller/test_embedding_runner/test_probe 233 passed, test_watch/test_guard 65 passed.

## Deviations from Plan
- `wait_idle` aus der Artefaktliste nicht gebaut: steht in keiner Schnittstelle (auch nicht in 27-09, das auf `pass_in_flight` und `parked` wartet) und wäre toter Code für vulture.
- TDD: Tests und Umsetzung je Task in einem Commit statt getrenntem RED/GREEN-Commit.

## Known Issues
- `tests/test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_python_package` ist rot, weil sich das Python-Paket geändert hat. Pin bewusst nicht angefasst; der Orchestrator misst nach dem Wellen-Merge nach.

## Self-Check: PASSED
- Dateien vorhanden, Commits `f5c419c3` und `ea0dec9f` im Log.
