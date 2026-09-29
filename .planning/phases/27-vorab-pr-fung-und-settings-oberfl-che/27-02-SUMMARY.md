---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 02
subsystem: backend
tags: [probe, pruef-01, memory, guard, neutral-module]
requires: []
provides:
  - "findling.probe: STEPS, VERDICTS, CAUSES (13), STATES, NUMBER_KEYS, Start- und Meta-Codes"
  - "judge, judge_run, pending_load_bytes, first_slot_admitted, model_child_admitted"
  - "ProbeSnapshot, begin/note_step/finish/restore/snapshot, encode/decode"
  - "hold/release/held als eigenes Haltesignal"
  - "PROBE_SCAN_NAME/SHA256/BYTES, probe_scan_path(), extract/probe_scan.pdf"
  - "config: PROBE_MEASURE_SECONDS, PROBE_DOWNLOAD_SECONDS, PROBE_PAUSE_SECONDS, MODEL_PROBE_CHILD_BYTES, PROBE_SAMPLE_SECONDS"
affects: [27-05, 27-09, Router, PHP-Parität]
tech-stack:
  added: []
  patterns: ["Modulzustand als eine Referenz auf einen frozen Snapshot, atomarer Austausch unter Lock (IN-01)"]
key-files:
  created:
    - backend/src/findling/probe.py
    - backend/src/findling/extract/probe_scan.pdf
    - backend/tests/test_probe.py
  modified:
    - backend/src/findling/config.py
    - backend/tests/test_measurement_scripts.py
    - .gitattributes
decisions:
  - "judge rechnet need = N x max(Messwert, OCR_SLOT_COST_BYTES) + pending + model_extra; model_memory nur wenn model_extra > 0 und ohne ihn kein Fehlbetrag bliebe; der fp32-Anteil gehört entweder in pending oder in model_extra, nie in beide"
  - "reserve_thin zeigt reserve nie unter 0 (judge_run kann darunter fallen), required = GUARD_RESERVE_BYTES"
  - "pending_load_bytes(embed_slots=0, writer_heap_delta=0) ist exakt EmbedRunner._need; negative Zusätze werden auf 0 geklemmt"
  - "Präzisionsnamen int8/fp32 lokal wiederholt wie in profile.py, um die Neutralität zu halten"
  - "Probe-Id: 16 Hex-Ziffern (secrets.token_hex(8) laut Research), andere Ids werfen ValueError"
metrics:
  duration: "ca. 35 min"
  completed: 2026-09-29
  tasks: 2
  files: 6
---

# Phase 27 Plan 02: Neutraler Probe-Kern Summary

Neutrales Modul `findling/probe.py` mit geschlossenen Codemengen, reiner Rechnung (GUARD_RESERVE_BYTES als Abstand), Vorab-Toren, eigenem Haltesignal, validiertem Snapshot samt JSON-Kodierung und einer mitgelieferten, per sha256 gepinnten Scanseite.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | probe.py mit Mengen, Snapshot, Rechnung, Haltesignal; Konstanten in config.py | 0c0f91ef (RED), 9bb6ac24 (GREEN) |
| 2 | Scanseite als Paketdatei mit Digest-Pin | 915c6dab |

## Verifikation

- `tests/test_probe.py` (inkl. 8 Kombinationen cutter/engine/fp32, Grenzfälle -1, 0, Reserve - 1, Reserve), `test_guard.py`, `test_config.py` grün
- Volle Suite: 3936 passed, 22 skipped
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber
- `cmp` testdata/corpus/13-ratsvorlage-scan.pdf gegen extract/probe_scan.pdf ohne Unterschied; committeter Blob hat sha256 320bb1aa...81f3, 79506 Byte
- `uv build --wheel` enthält `findling/extract/probe_scan.pdf` (uv_build nimmt Nicht-.py-Dateien mit, pyproject.toml unverändert); Dockerfile kopiert `src` vollständig

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Korrektheit] `-text` für die Scanseite in .gitattributes**
- **Found during:** Task 2
- **Issue:** Die Korpus-PDFs sind nur unter `testdata/corpus/** -text` geschützt; die Kopie im Paket wäre bei core.autocrlf=true zeilenendenkonvertiert worden (PDF ohne NUL-Byte gilt Git als Text), Digest-Pin und Querverweistabelle wären kaputt.
- **Fix:** Regel `backend/src/findling/extract/probe_scan.pdf -text` mit Begründung ergänzt.
- **Commit:** 915c6dab

**2. [Rule 3 - Blocker] Baumhash-Pin des Python-Pakets nachgezogen**
- **Found during:** Task 2 (volle Suite)
- **Issue:** `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` pinnt Dateizahl und Baumhash von `src/findling/**/*.py`; probe.py und die config-Änderung bewegen ihn (67 -> 68).
- **Fix:** `PACKAGE_FILES_TODAY = 68`, neuer Hash c304a722..., Chronik-Kommentar im Hausstil. Gemessen im eigenen Worktree; nach dem Merge der Welle 1 muss der Wert erneut gemessen werden, wenn Nachbarpläne ebenfalls Paketdateien ändern.
- **Commit:** 915c6dab

## Hinweise für Folgepläne

- Die Neutralität ist per Test gesichert (Importzeilen nur findling.config/findling.profile, kein logging).
- `probe_scan_path()` importiert `findling.extract` erst beim Aufruf; dessen `__init__` hat keine Importe.
- 27-05 kann `EmbedRunner._need` auf `pending_load_bytes(..., embed_slots=0, writer_heap_delta=0)` umstellen, Gleichheit ist für alle acht Kombinationen getestet.

## Self-Check: PASSED

- FOUND: backend/src/findling/probe.py, backend/src/findling/extract/probe_scan.pdf, backend/tests/test_probe.py
- FOUND: 0c0f91ef, 9bb6ac24, 915c6dab

## TDD Gate Compliance

RED `test(27-02)` 0c0f91ef vor GREEN `feat(27-02)` 9bb6ac24 vorhanden.
