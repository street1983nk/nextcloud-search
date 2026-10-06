---
phase: 24-owner-tor-profil-ger-st-und-marken-reparatur
plan: 01
subsystem: store/vectors (embedding mark)
tags: [MOD-01, embedding_version, upgrade-compat, fp32]
requires: []
provides:
  - "WEIGHTS_INT8, WEIGHTS_FP32, WEIGHT_PRECISIONS in findling.store.vectors"
  - "embedding_mark(model, *, tokens, weights=WEIGHTS_INT8)"
affects:
  - "Phase 25 (Modellschalter): muss weights aus dem tatsächlich geladenen Modell übergeben"
tech-stack:
  added: []
  patterns: ["int8 durch Abwesenheit in der Marke, keine Normalisierungslogik an Vergleichsstellen"]
key-files:
  created: []
  modified:
    - backend/src/findling/store/vectors.py
    - backend/tests/test_vector_store.py
    - backend/tests/test_upgrade_compatibility.py
    - backend/tests/test_embedding_track.py
    - backend/tests/test_measurement_scripts.py
    - docs/embeddings.md
decisions:
  - "int8-Marke bleibt bytegleich zu 1.3.x, fp32 hängt /fp32 an; keine Vergleichs- oder Normalisierungsfunktion"
  - "ValueError bei unbekannter Präzision nennt den Wert nicht (T-24-03)"
metrics:
  duration: "ca. 25 min"
  completed: 2026-09-27
  tasks: 2
  files: 6
---

# Phase 24 Plan 01: Marken-Reparatur (Gewichtspräzision in embedding_version) Summary

`embedding_mark` kennt jetzt die Gewichtspräzision: int8 wird durch Abwesenheit ausgedrückt und liefert byte für byte `multilingual-e5-small/int8/384/1024` wie bis 1.3.x, fp32 hängt `/fp32` an; ein Gold-Ratchet und drei Poller-Verhaltenstests belegen "Upgrade ohne Reindex, Präzisionswechsel mit Reindex".

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | embedding_mark mit Präzisionsparameter, int8 bytegleich (TDD) | 0e6c272 (RED), 3c0ec9b (GREEN) |
| 2 | Verhaltenstests Upgrade/Präzisionswechsel, Doku §8 | 1984b80 |
| Rule 3 | Baumhash des Python-Pakets nachgezogen | cc8eb24 |

## Ergebnis

- `vectors.py`: Konstanten `WEIGHTS_INT8`, `WEIGHTS_FP32`, `WEIGHT_PRECISIONS` neben `ELEMENT_TYPE`; `embedding_mark(model, *, tokens, weights=WEIGHTS_INT8)`; Docstring auf fünf Merkmale erweitert, inkl. Hinweis, dass ab Phase 25 die tatsächlich geladene Präzision maßgeblich ist.
- `test_upgrade_compatibility.py`: `test_the_vector_mark_of_an_int8_build_is_the_mark_of_v1_3` als Literal-Ratchet.
- `test_embedding_track.py`: 1.3-Marke erzeugt keine Kette und kein Requeue; fp32 zu int8 und int8 zu fp32 (per monkeypatch von `poller_module.embedding_mark`) lösen forget_all, Marke schreiben, Requeue embed in dieser Reihenfolge aus.
- `docs/embeddings.md` §8: Nachtrag 1.4 zur Präzision in der Marke; fp32-Nachladeweg kommt mit Phase 25.
- `poller.py` und `resources.py` unverändert (diff leer).

## Verifikation

- `uv run pytest -q`: 3358 passed, 15 skipped
- ruff check, ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest, 0 errors), vulture --min-confidence 80: alle grün
- Keine Em-/En-Dashes in docs/embeddings.md

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Paket-Baumhash in test_measurement_scripts.py nachgezogen**
- **Found during:** Vollsuite nach Task 2
- **Issue:** `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` hasht alle `src/findling/**/*.py`; die Änderung an `vectors.py` verschiebt `PACKAGE_TREE_HASH_TODAY`.
- **Fix:** Hash auf `1eb811ad...18c6` gesetzt, mit Kommentar im etablierten Stil; Dateizahl bleibt 57.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Commit:** cc8eb24
- **Hinweis für den Orchestrator:** Ändern parallele Pläne derselben Welle ebenfalls Dateien unter `src/findling`, muss dieser Hash nach dem Merge einmal über den gemergten Baum neu gemessen werden (wie beim Wave-Merge 17-02/17-03).

## TDD Gate Compliance

RED `0e6c272` (test) vor GREEN `3c0ec9b` (feat) vorhanden. Task 2 sind Verhaltenstests über Baubestand (Poller-Kette), die laut Plan sofort grün sein müssen; kein separates RED.

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: backend/src/findling/store/vectors.py, backend/tests/test_embedding_track.py, docs/embeddings.md
- FOUND commits: 0e6c272, 3c0ec9b, cc8eb24, 1984b80
