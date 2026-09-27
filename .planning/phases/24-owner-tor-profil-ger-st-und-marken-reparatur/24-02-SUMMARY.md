---
phase: 24-owner-tor-profil-ger-st-und-marken-reparatur
plan: 02
subsystem: backend/config, backend/hardware
tags: [profiles, cgroup, config, appapi, bl-f04]
requires: []
provides:
  - "Profilkonstanten (Standard/Leistung/Sparsam-Spiegel, r, Slotkosten, Vorschlags-Schwellen) in findling/config.py"
  - "explicit_int_from_environment (Überstimmungsleser, ignoriert injizierte AppAPI-Defaults)"
  - "findling/hardware.py: Hardware, detect(), cpu_quota(), memory_limit(), meminfo_bytes(), CGROUP_ROOT, MEMINFO"
  - "Gleichstandstest info.xml gegen config.py"
affects:
  - "backend/tests/test_measurement_scripts.py (PACKAGE_FILES_TODAY 57 -> 58, neuer Baumhash)"
tech-stack:
  added: []
  patterns: ["injizierbare Kernelpfade + nie werfende Parser", "frozen slots dataclass als Momentaufnahme"]
key-files:
  created:
    - backend/src/findling/hardware.py
    - backend/tests/test_hardware.py
    - backend/tests/test_info_xml_defaults.py
  modified:
    - backend/src/findling/config.py
    - backend/tests/test_config.py
    - backend/appinfo/info.xml
    - backend/tests/test_measurement_scripts.py
decisions:
  - "FINDLING_LOG_LEVEL hat keine config.py-Konstante; der Gleichstand wird über den Leser findling.main.log_level() bei ungesetzter Variable belegt"
  - "cpu.max mit Quote <= 0 oder Periode <= 0 gilt als keine Quote (None), memory.max <= 0 als keine Grenze"
  - "cgroup v1 wird nur gelesen, wenn weder cpu.max noch memory.max existiert; v1-Speichergrenze >= MemTotal gilt als keine Grenze"
metrics:
  duration: "ca. 35 min"
  completed: 2026-09-27
  tasks: 3
  files: 7
---

# Phase 24 Plan 02: Profil-Zahlen- und Messfundament Summary

Profilkonstanten mit Herleitung (Standard 50 %/40 %/max. 4 OCR, Leistung Kerne minus 1/60 %/max. 16, r = 0,25, 235 MiB je OCR-Slot, Schwellen 6 GB/3 Kerne und 12 GB/6 Kerne), ein Überstimmungsleser, der von AppAPI injizierte Defaults ignoriert, das cgroup-bewusste Modul `findling/hardware.py` und ein Gleichstandstest info.xml gegen config.py. Nichts davon ist in den Betrieb verdrahtet.

## Tasks

| Task | Name | Commits | Dateien |
|------|------|---------|---------|
| 1 | Profilkonstanten + explicit_int_from_environment | f971a81 (RED), ab2cb37 (GREEN) | config.py, test_config.py |
| 2 | findling/hardware.py | 5d557db (RED), b8ddc20 (GREEN) | hardware.py, test_hardware.py |
| 3 | Gleichstandstest + Überstimmungssatz | 43555d7 | test_info_xml_defaults.py, info.xml, test_measurement_scripts.py |

## Verification

- `uv run pytest -q`: 3408 passed, 15 skipped; einziger Fehlschlag war der Baumhash-Test (siehe Abweichung 1), nach dem Fix grün (754 passed in den betroffenen Dateien)
- ruff check, ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest, 0 Fehler), vulture --min-confidence 80: alle grün
- `settings()`/`Settings` unverändert (Diff von config.py enthält nur Zusatzzeilen), `test_store_metadata.py` unverändert
- info.xml: genau ein Satz ergänzt, keine `<default>`-Zeile geändert

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Baumhash des Python-Pakets nachgezogen**
- **Found during:** Gesamtlauf nach Task 3
- **Issue:** `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` pinnt Anzahl und Hash aller Dateien unter `backend/src/findling`; das neue `hardware.py` und die geänderte `config.py` bewegen beides (57 -> 58).
- **Fix:** `PACKAGE_FILES_TODAY = 58` und neuer `PACKAGE_TREE_HASH_TODAY` mit Begründungsabsatz im Hausstil ("Moved on 2026-09-27 by plan 24-02").
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Commit:** 43555d7
- **Hinweis für den Orchestrator:** Ändert ein paralleler Plan derselben Welle ebenfalls Dateien unter `backend/src/findling`, muss der Hash nach dem Merge einmal neu berechnet werden (Merge-Konflikt in genau diesen zwei Zeilen erwartbar).

**2. [Rule 1 - Stil] noqa-Marker entfernt**
- ruff meldete RUF100 für PLR2004/BLE001/FBT001 (im Projekt nicht aktiv); Begründungen als normale Kommentare behalten.

## Known Stubs

Keine. Die Konstanten und `detect()` sind bewusst noch nicht verdrahtet (Planziel, spätere Pläne der Phase).

## Threat Flags

Keine neuen Flächen: `detect()` liest nur lokale Kernel-Dateien, loggt nichts und sendet nichts (T-24-05/T-24-06); der neue Leser loggt nicht (T-24-07).

## Self-Check: PASSED

- FOUND: backend/src/findling/hardware.py, backend/tests/test_hardware.py, backend/tests/test_info_xml_defaults.py
- FOUND: f971a81, ab2cb37, 5d557db, b8ddc20, 43555d7
