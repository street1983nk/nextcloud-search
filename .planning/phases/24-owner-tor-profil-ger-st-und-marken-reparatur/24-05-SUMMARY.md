---
phase: 24-owner-tor-profil-ger-st-und-marken-reparatur
plan: 05
subsystem: container-profile-wire
tags: [profile, poller, ocs, prof-03]
requires: ["24-01", "24-03", "24-04"]
provides:
  - "read_profile(nc): GET /ocs/v2.php/apps/findling/profile"
  - "DocumentQueue.profile() -> str | None"
  - "Profilabfrage je Poller-Runde vor claim (note_chosen)"
  - "Gleichstandstest PHP PROFILES/PROFILE_DEFAULT gegen PROFILE_NAMES/Profile.ECONOMY"
affects: [backend/src/findling/worker/poller.py, backend/src/findling/nc/queue.py]
tech-stack:
  added: []
  patterns: ["fehlertoleranter Queue-Wrapper nach Muster top_up()", "Fehlerpfad-Test über echte DocumentQueue statt werfendem Fake"]
key-files:
  created:
    - backend/tests/test_profile_wire.py
  modified:
    - backend/src/findling/nc/client.py
    - backend/src/findling/nc/queue.py
    - backend/src/findling/worker/poller.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_poller.py
    - backend/tests/test_embedding_track.py
    - backend/tests/test_acl_prefilter.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Queue-Fakes werfen nicht aus profile(): die Fehlertoleranz liegt in DocumentQueue.profile, ein werfender Fake würde run_once zerreißen und einen Pfad testen, den Produktion nie nimmt; der 1.3-Fall läuft stattdessen über die echte DocumentQueue mit 404-Session"
  - "test_reconcile.py unverändert: ihr _FakeQueue kennt nur stats/requeue und erreicht nie Poller.run_once"
metrics:
  duration: "~10 min"
  completed: 2026-09-27
  tasks: 2
  files: 9
---

# Phase 24 Plan 05: Profilweg B, Container-Hälfte Summary

Der Container liest das vom Admin gespeicherte Profil je Poller-Runde über GET `/ocs/v2.php/apps/findling/profile` in den Prozess-Zustand (`note_chosen`). Jede Ausnahme (auch der 404 eines 1.3-Companions) und jeder Wert außerhalb von `PROFILE_NAMES` ergibt None. Der zuletzt gelesene Wert bleibt stehen, vor dem ersten Lesen gilt Sparsam. Kein Profilwert steuert bisher Batch, Writer, Sandbox oder Einbettung.

## Tasks

| Task | Name | Commits | Files |
|------|------|---------|-------|
| 1 | read_profile, DocumentQueue.profile, Gleichstandstest | d73a4c2 (RED), 3e4cac4 (GREEN) | nc/client.py, nc/queue.py, test_queue_client.py, test_profile_wire.py, test_measurement_scripts.py |
| 2 | Profilabfrage je Poller-Runde, Fakes | be2d6bd | worker/poller.py, test_poller.py, test_embedding_track.py, test_acl_prefilter.py, test_measurement_scripts.py |

## Verifikation

- Gesamtsuite: 3480 passed, 15 skipped
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture --min-confidence 80 sauber
- `"/ocs/v2.php/apps/findling/profile"` genau einmal in client.py; OCS_WRITE_ALLOWLIST unberührt, test_readonly_gate.py grün
- poller.py: Zeile 742 `_open`, 751 `note_chosen(await queue.profile())`, 753 `queue.claim(`; Diff enthält außer Kommentaren nur Import und diese Zeile
- Gegenprobe: mit entfernter Poller-Zeile sind alle drei neuen Poller-Tests rot
- index/extract/embed ohne Diff

## Deviations from Plan

**1. [Rule 1 - Bug im Testentwurf] Kein `profile_error` in den Queue-Fakes**
- **Gefunden bei:** Task 2
- **Problem:** Der Plan sah einen Fake vor, der aus `profile()` wirft, und erwartete, dass die Runde normal endet. Der Poller fängt dort nichts (Plan verbietet weitere Poller-Änderungen), die Toleranz liegt in `DocumentQueue.profile`. Ein werfender Fake hätte run_once abgebrochen.
- **Lösung:** `_FakeQueue` in test_poller.py hat `profile_route_missing`; ist es gesetzt, läuft die Abfrage über die echte `DocumentQueue.profile` mit einer Session, die `NextcloudException(404)` wirft. So prüfen die Tests genau den Fehlerpfad der Produktion. Die übrigen Fakes haben nur `profile_answer`/`profile_asks` (der Stock-Fake gibt fest None zurück).
- **Commit:** be2d6bd

**2. [Rule 3 - Blocking] Baumhash nachgezogen**
- test_measurement_scripts.py `PACKAGE_TREE_HASH_TODAY` zweimal mit Begründungskommentar nachgezogen (nach Task 1 und Task 2), Anzahl bleibt 59. Der Orchestrator misst nach dem Merge mit 24-06 neu.

## TDD Gate Compliance

- Task 1: RED (d73a4c2) vor GREEN (3e4cac4). test_profile_wire.py war im RED bereits grün, weil Plan 04 die PHP-Konstanten schon lieferte (reiner Gleichstandstest, erwartet).
- Task 2: kein separater test-Commit; RED wurde nachgewiesen, indem die Poller-Zeile vorübergehend entfernt wurde (3 Tests rot), dann Commit mit Code und Tests zusammen.

## Threat Model

T-24-16 bis T-24-20 umgesetzt: geschlossene Menge in `DocumentQueue.profile`, jede Exception wird None, letzter Wert bleibt, debug-Zeile ohne Wert und ohne Ausnahmetext (per Test geprüft), GET ohne Allowlist-Eintrag.

## Known Stubs

Keine. Der Profilwert wird bewusst noch nicht verdrahtet (Plan-Vorgabe, Verdrahtung ab Phase 26).

## Self-Check: PASSED

- backend/tests/test_profile_wire.py vorhanden
- Commits d73a4c2, 3e4cac4, be2d6bd vorhanden
