---
phase: 24-owner-tor-profil-ger-st-und-marken-reparatur
plan: 03
subsystem: backend/profile
tags: [profile, hardware, resolver, economy-pin]
requires: ["24-02"]
provides: ["findling.profile: Profile, PROFILE_NAMES, ProfileValues, Resolution, ProfileSnapshot, suggest, effective, resolve, note_hardware, note_chosen, snapshot, reset"]
affects: ["Plan 24-06 (Statusroute, Lifespan ruft note_hardware)", "Phase 25/26 (Verdrahtung der Werte)"]
tech-stack:
  added: []
  patterns: ["Modul-Global-Zustand nach rebuild_progress", "Momentaufnahme nur beim Schreiben berechnet", "autouse-Reset beidseitig"]
key-files:
  created:
    - backend/src/findling/profile.py
    - backend/tests/test_profile.py
  modified:
    - backend/tests/conftest.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Überstimmung über dataclasses.replace auf der Profilzeile; Quellen als MappingProxyType (unveränderlich)"
  - "Momentaufnahme wird nur in note_hardware/note_chosen/reset berechnet; die Statusroute liest nie die Umgebung"
  - "Baumhash-Pin auf 59 Dateien mit neuem Hash nachgezogen (profile.py neu)"
metrics:
  duration: "ca. 25 min"
  completed: 2026-09-27
  tasks: 2
  files: 4
---

# Phase 24 Plan 03: Profil-Kern Summary

Neutrales Modul `findling/profile.py` mit Anteils-Formel für OCR-Slots (Standard `floor(0,5 x C - 0,25)`, Leistung `floor(C - 1)`, Speicherterm mit Anteil, Reserve, Grundlinie und Slotkosten), Vorschlag nach D-24-06, wirksamer Stufe `min(gewählt, passend)`, Umgebungs-Überstimmung für vier Felder mit Quellenangabe und einem Prozess-Zustand mit unveränderlicher Momentaufnahme; Sparsam ist Wert für Wert gegen die heutigen Konstanten gepinnt.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | Reiner Resolver und Sparsam-Pin | f9b799e (RED), aa5a3b5 (GREEN) |
| 2 | Prozess-Zustand mit Momentaufnahme und Test-Reset | 92d5064 (RED), bd83a67 (GREEN) |

## Verification

- `uv run pytest -q`: 3463 passed, 15 skipped
- ruff check, ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest), vulture 80: alle grün
- `git diff --stat f836d25 HEAD -- backend/src/findling/worker backend/src/findling/index backend/src/findling/extract`: leer (nichts verdrahtet)
- Alle Zahlenfälle des Plans stehen als Asserts in test_profile.py (15, 7, 3, 5, 16; 1/2/3/4 für Standard; onnx 2/4/4; Schwellen; Überstimmung 29/30/100000/64000000)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Baumhash-Pin in test_measurement_scripts.py nachgezogen**
- **Found during:** Task 1 und Task 2
- **Issue:** `PACKAGE_FILES_TODAY`/`PACKAGE_TREE_HASH_TODAY` pinnen alle Dateien unter `backend/src/findling`; profile.py kam neu dazu.
- **Fix:** 58 -> 59, Hash neu gemessen (nach Task 2: `15222184...`), Begründungskommentar im bestehenden Stil.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Commits:** aa5a3b5, bd83a67

Sonst wie geplant. settings()/Settings/lru_cache und test_store_metadata.py wurden nicht angefasst.

## TDD Gate Compliance

Je Task ein `test(...)`-Commit (RED, Import- bzw. Attributfehler) vor dem `feat(...)`-Commit (GREEN). Kein Refactor-Commit nötig.

## Known Stubs

Keine. Dass kein Wert in Poller, Writer oder Sandbox fließt, ist Plan-Absicht (Phase 24 rechnet und meldet nur); die Meldung über die Statusroute folgt in Plan 06.

## Self-Check: PASSED

- FOUND: backend/src/findling/profile.py, backend/tests/test_profile.py
- FOUND: f9b799e, aa5a3b5, 92d5064, bd83a67
