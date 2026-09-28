---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 03
subsystem: backend/guard
tags: [memory-guard, cgroup, profile, ocr-slots, PAR-02, PAR-03]
requires: []
provides:
  - "findling.guard: CAUSE_*, CAUSES, META_* (state.db-Schlüssel), GuardSnapshot, throttled_slots, Escalation, lower, restore, note_confirmation, note_slots, report_child_kill, take_child_kills, snapshot, reset"
  - "findling.memory_guard.memory_events(root) -> dict[str, int] | None"
  - "findling.config: OCR_CLAIM_BATCH_INDEX_LANE = 32, OCR_ROWS_PER_SLOT = 2, ocr_rows_to_keep, GUARD_RESERVE_BYTES, GUARD_WINDOW_SECONDS = 600, GUARD_MIN_GAP_SECONDS = 60, GUARD_TICK_SECONDS = 15.0"
  - "findling.profile: effective(chosen, fitting, cap=None), note_cap, ProfileSnapshot.cap"
affects: [26-06, 26-09, 26-10, 26-04]
tech-stack:
  added: []
  patterns: ["neutrales Zustandsmodul nach lane.py", "Kernel-Leser nach memory_guard.anon_bytes", "Kappe als drittes min-Glied, Zyklus-Regel profile -> guard nie"]
key-files:
  created:
    - backend/src/findling/guard.py
    - backend/tests/test_guard.py
  modified:
    - backend/src/findling/config.py
    - backend/src/findling/memory_guard.py
    - backend/src/findling/profile.py
    - backend/tests/conftest.py
    - backend/tests/test_config.py
    - backend/tests/test_memory_guard.py
    - backend/tests/test_profile.py
decisions:
  - "lower() rechnet von min(effective, bestehende Kappe) aus eine Stufe tiefer, damit zwei Absenkungen auch bei gleichem effective-Argument zwei Stufen ergeben"
  - "restore() verlangt alle fünf Werte gültig (Stufe, Ursache, endliche Zeit, 32 Hex, gewähltes Profil), sonst False ohne Zustandsänderung"
  - "note_confirmation vergleicht den Token nur, wenn er die 32-Hex-Form hat (compare_digest wirft sonst bei Nicht-ASCII)"
  - "revision zählt nur Kappen-Änderungen, nicht note_slots"
  - "META_*-Schlüssel ohne Final-Annotation, damit das Plan-Grep-Kriterium greift"
metrics:
  duration: "ca. 35 min"
  completed: 2026-09-28
  tasks: 2
  files: 9
---

# Phase 26 Plan 03: Neutrales Wächter-Fundament Summary

Zeilen-je-Slot-Anspruchsrechnung (OCR_ROWS_PER_SLOT = 2, ocr_rows_to_keep, Deckel bleibt 780), nie werfender memory.events-Leser und das neue I/O-freie Modul `guard.py` mit Slot-Drossel, qualifizierter max-Eskalation (Reserve 235 MiB, 60 s Abstand, 600 s Fenster), Sofort-Auslöser bei Kills, Kappe per `profile.note_cap` und Rückweg per 32-Hex-Token.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | Konstanten, Zeilenbeschnitt-Formel, memory_events | eced9d86 (RED), db55cd9c (GREEN) |
| 2 | guard.py, Kappe in profile.py, conftest-Reset | 99597a6e (RED), 5a50029f (GREEN) |

## Was entstand

- `config.py`: `OCR_JOB_SECONDS_MAX = OCR_LOCK_TIMEOUT_SECONDS // OCR_ROWS_PER_SLOT - 2 * OCR_HARD_DEADLINE_MARGIN_SECONDS` (780, unverändert), Kommentar zur -64-Falle der alten Herleitung; `ocr_rows_to_keep` mit Schutz gegen Slot 0 und Deckel 0; Wächter-Konstanten ohne Umgebungsvariable.
- `memory_guard.memory_events`: überspringt kaputte Zeilen, leere oder unlesbare Datei ergibt None.
- `guard.py`: `Escalation.observe` setzt beim ersten Tick nur die Basis, ein Zählerrückgang setzt die Basis neu, Kind-Kills lösen auch ohne events aus; `lower` wirft bei unbekannter Ursache, gibt am Sparsam-Boden False zurück.
- `profile.py`: Kappe als drittes Glied in `min(...)`, `note_cap` rechnet nur bei Änderung neu, alle Setter und `reset` tragen die Kappe mit; kein Import von guard.
- `conftest.py`: `guard_module.reset()` vor und nach jedem Test.

## Verifikation

- Vollsuite: 3768 passed, 16 skipped, 1 deselected (Tree-Hash-Test nach Pin-Regel der Phase).
- ruff check, ruff format --check, pyright (latest), vulture: grün.
- Alle Grep-Akzeptanzkriterien beider Tasks erfüllt; `git diff --stat -- php backend/src/findling/worker backend/src/findling/extract` leer.
- Sparsam-Pin in tests/test_profile.py unverändert grün.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Sicherheit] Token-Vergleich nur für wohlgeformte Werte**
- **Found during:** Task 2
- **Issue:** `secrets.compare_digest` wirft `TypeError` bei Nicht-ASCII-Strings; ein manipulierter appconfig-Wert hätte den Wächter-Task werfen lassen.
- **Fix:** Vergleich nur nach `_TOKEN_PATTERN`-Prüfung; Testfall mit `"ä" * 32`.
- **Files modified:** backend/src/findling/guard.py, backend/tests/test_guard.py
- **Commit:** 5a50029f

**2. [Rule 3 - Gate] ruff S105 auf META_TOKEN und META_MULTI_SLOT_PASS**
- **Issue:** ruff hält die Schlüsselnamen für Passwörter.
- **Fix:** gezieltes `# noqa: S105` mit Begründung, wie in tests/test_v13_wechsel.py.
- **Commit:** 5a50029f

Sonst wie geplant.

## Known Stubs

Keine. `guard.py` wird von Poller (26-09) und Wächter-Task (26-10) verdrahtet; das ist so geplant, kein Stub.

## Threat Flags

Keine neue Angriffsfläche über das Threat-Register hinaus (T-26-08 bis T-26-11 umgesetzt: qualifiziertes Ereignis, Drossel gegen Headroom, geschlossene Mengen in restore/note_confirmation, guard.py loggt nichts).

## Self-Check: PASSED

- FOUND: backend/src/findling/guard.py, backend/tests/test_guard.py
- FOUND: eced9d86, db55cd9c, 99597a6e, 5a50029f
