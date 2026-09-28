---
phase: 25-einbettungsspur-und-modellwahl
plan: 08
subsystem: backend/precision-profile
tags: [precision, fp32, state-machine, slot-formula, ram, embed-lane]
requires:
  - 25-01 (FP32_EXTRA_BYTES = 367 * MIB gemessen)
  - 25-05 (Precision-Enum, companion_choice)
provides:
  - precision.py Zustandsautomat (note_chosen_precision, settle, note_active, decide, begin/end_procurement, snapshot, reset, Verdikte)
  - profile.note_weights, ProfileSnapshot.weights und embed_lane_fits, fp32-Term im Speicherterm
  - config.FP32_EXTRA_BYTES, EMBED_ACTIVATION_BYTES, EMBED_WEIGHTS_LOAD_BYTES, CUTTER_LOAD_BYTES, EMBED_LANE_RESERVE_BYTES, Settings.models_dir
affects:
  - 25-09 (Live-Teil der RAM-Bedingung nutzt die Konstanten)
  - 25-11 (Poller verdrahtet decide/settle/Beschaffung)
  - 25-12 (Status meldet weights, embed_lane_fits, Verdikt)
tech-stack:
  added: []
  patterns: [Modulzustand mit reset() nur für Tests, Verdikt beim Lesen abgeleitet, Namensspiegel statt Import gegen Zyklus]
key-files:
  created:
    - backend/tests/test_precision.py
  modified:
    - backend/src/findling/config.py
    - backend/src/findling/precision.py
    - backend/src/findling/profile.py
    - backend/tests/conftest.py
    - backend/tests/test_config.py
    - backend/tests/test_profile.py
decisions:
  - "resolve() und ocr_slots() bekommen weights als Keyword mit Default int8; bestehende Aufrufer bleiben unverändert"
  - "_memory_term liefert 0 für Economy und unbekannten Speicher, ungeklammert sonst (auch negativ)"
  - "Unter Sparsam verbraucht jeder fp32-Wunsch (auch Erstlesen) den Wunsch und setzt fp32_not_in_economy; auch eine verifizierte Datei wird danach per Profilwechsel nicht aktiviert (T-25-34)"
  - "Nach fp32_unavailable darf eine verifizierte, selbst abgelegte Datei weiter aktiviert werden (D-25-06); note_active(FP32) löscht den Fehlschlag"
  - "Neues internes Flag _ASKED: ein gewünschter, noch nicht begonnener Download setzt kein fp32_unavailable"
metrics:
  duration: ca. 35 min
  completed: 2026-09-28
  tasks: 3
  files: 7
---

# Phase 25 Plan 08: Präzisions-Automat, fp32-Slotterm und RAM-Konstanten Summary

Reiner Zustandsautomat der Präzision ohne I/O (D-25-01/03/04/06/09/10/14), der die Präzision in Kraft an das Profil meldet; die Slotformel zieht bei fp32 gemessene 367 MiB ab, und die Profil-Momentaufnahme sagt statisch, ob die parallele Einbettungsspur passt.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | RAM-Konstanten und models_dir in config.py | 895277f (RED), 3812b3d (GREEN) |
| 3 | fp32-Term in der Slotformel, embed_lane_fits | ea18a88 (RED), 6f7cba7 (GREEN) |
| 2 | Zustandsautomat in precision.py | 87eb631 (RED), 87efc5c (GREEN) |

## Was gebaut wurde

- **config.py:** `FP32_EXTRA_BYTES = 367 * MIB` (Test liest die Zahl aus `docs/measurements/2026-09-fp32-speicher/README.md`), `EMBED_ACTIVATION_BYTES = 27 * MIB`, `EMBED_WEIGHTS_LOAD_BYTES = 392 * MIB`, `CUTTER_LOAD_BYTES = 545 * MIB`, `EMBED_LANE_RESERVE_BYTES = OCR_SLOT_COST_BYTES`, je mit Herleitung; `Settings.models_dir = root / "models"`; D-25-12-Kommentar an den Embed-Slots (Werte unverändert).
- **profile.py:** `_memory_term(profile, hardware, *, extra_bytes)` ungeklammert, `ocr_slots`/`resolve` mit `weights`-Keyword, `note_weights`, `_WEIGHTS`-Zustand, `ProfileSnapshot.weights` und `embed_lane_fits` (Hardware bekannt, wirksam Standard/Leistung, Speicherterm nach Aktivierung plus ggf. fp32 mindestens OCR-Slots und mindestens 1). Kein Import von precision.py; `_INT8`/`_FP32` gespiegelt und per Test gegen `Precision` gesichert.
- **precision.py:** sechs Verdikte plus `VERDICTS`, `PrecisionSnapshot` (mit `settled`), `PrecisionDecision`, Automat nach den Regeln des Plans. Jede Zustandsänderung und jedes `decide` meldet über `profile.note_weights` die Präzision in Kraft.
- **conftest.py:** `precision.reset()` im autouse-Fixture nach `profile.reset()`.

## Deviations from Plan

### Reihenfolge

- Task 3 vor Task 2 ausgeführt: der Automat aus Task 2 ruft `profile.note_weights`, das erst Task 3 liefert. Inhalt beider Tasks unverändert.

### Auto-fixed Issues

**1. [Rule 2 - Korrektheit] Internes Flag `_ASKED`**
- **Gefunden in:** Task 2
- **Problem:** Ohne Flag hätte ein zweites `decide` zwischen Download-Wunsch und `begin_procurement` fälschlich `fp32_unavailable` gesetzt.
- **Fix:** `_ASKED` merkt den offenen Wunsch; gelöscht durch `end_procurement` und durch ein neues int8.
- **Commit:** 87efc5c

**2. [Rule 2 - Sicherheit, T-25-34] Sparsam-Sperre auch für Erstlesen und verifizierte Datei**
- Ein unter Sparsam gelesenes fp32 setzt `fp32_not_in_economy` auch ohne beobachteten Wechsel, und nach dieser Sperre aktiviert auch eine verifizierte Datei nach einem Profilwechsel nichts. Erst int8 und dann fp32 hebt die Sperre auf.

Quellabgleich der Konstanten: keine Abweichung (docs/embeddings.md +26,4 / +391,9 MB, CLAUDE.md 544,3 MB, Messung 25-01 367 MiB).

## Verifikation

- `pytest --deselect tests/test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_python_package`: 3572 passed, 15 skipped, 1 deselected.
- Der deselektierte Paket-Pin-Test schlägt im Worktree erwartungsgemäß fehl (Bytes von config.py, precision.py, profile.py geändert); Pin-Eigentümer dieser Welle ist Plan 25-07.
- ruff check, ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest), vulture --min-confidence 80: grün.
- `git diff --stat ebf6f74 -- php backend/src/findling/worker backend/src/findling/api backend/tests/test_measurement_scripts.py`: leer. api/status.py meldet die neuen Felder noch nicht (Plan 25-12).

## Known Stubs

Keine. Die neuen Zustände sind noch nicht im Poller verdrahtet (Plan 25-11) und nicht im Status gemeldet (Plan 25-12); das ist der Planschnitt, kein Stub.

## Self-Check: PASSED

- Dateien vorhanden: backend/tests/test_precision.py, backend/src/findling/precision.py, profile.py, config.py
- Commits vorhanden: 895277f, 3812b3d, ea18a88, 6f7cba7, 87eb631, 87efc5c
