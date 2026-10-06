---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 08
subsystem: backend/api-status
tags: [memory-guard, status, contract, PAR-03]
requires:
  - "26-03: guard.snapshot(), guard.CAUSES, profile.snapshot() mit cap"
  - "26-05: guardField-Vertrag der Adminseite"
provides:
  - "GET /status: Objekt guard (chosen, effective, cap, cause, since, token, slotsTarget, slotsInForce, throttled)"
  - "findling.api.status.GuardReport, _guard_report()"
  - "Vertragstest guardField-Schlüssel gegen GuardReport.model_fields, GUARD_CAUSES gegen guard.CAUSES"
affects: [26-10, 26-14, 27]
tech-stack:
  added: []
  patterns: ["Prozesswert-Block nach LaneReport, in _volume gesetzt und in _of übernommen (Pitfall 2)", "scan_*-Funktion mit Rot-Probe auf Kopie im tmp_path"]
key-files:
  created: []
  modified:
    - backend/src/findling/api/status.py
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_admin_ui_contract.py
decisions:
  - "chosen und effective kommen aus profile.snapshot(), nicht aus guard.snapshot().chosen, damit es eine Wahrheit bleibt"
  - "since wird per int() auf die Epoch-Sekunde abgeschnitten (1700000000.5 -> 1700000000)"
  - "Vertragstest prüft zusätzlich die genaue Menge der sieben gelesenen Schlüssel, damit eine leere Regex-Trefferliste nicht still grün ist"
metrics:
  duration: "ca. 20 min"
  completed: 2026-09-28
  tasks: 2
  files: 3
---

# Phase 26 Plan 08: Wächter in der Statusroute Summary

GET /status trägt das Objekt `guard` im Vertrag der Adminseite aus 26-05: gewählt vs. wirksam, Kappe, Ursache aus der geschlossenen Menge, Epoch-Sekunde, 32-Hex-Token für den occ-Rückweg und die Slot-Drosselung; reiner Leser über `guard.snapshot()` und `profile.snapshot()`, gepinnt durch einen Vertragstest mit Rot-Probe.

## Tasks

| Task | Name | Commits | Dateien |
| ---- | ---- | ------- | ------- |
| 1 | GuardReport in der Statusroute | 5ac975ba (RED), 03b559dc (GREEN) | status.py, test_status_endpoint.py |
| 2 | Vertragstest Container gegen Adminseite | df161e38 | test_admin_ui_contract.py |

## Was entstand

- `GuardReport(BaseModel)` mit Vertragsfeldern und Ruhe-Defaults; Feld `guard` in `StatusResponse`, gesetzt in `_volume()` und übernommen in `_of()`.
- `_guard_report()` liest nur die beiden Snapshots; `status.py` importiert `memory_guard` nicht.
- Tests (beide Antwortpfade): Ruhezustand, Absenkung Leistung -> Standard mit Ursache/since/Token, Drosselung 4 -> 2, gepatchte Kernel-Leser (memory_events, headroom_bytes, anon_bytes) schlagen bei Aufruf fehl.
- Vertragstest: Regex `guardField\(\$answer, '([A-Za-z]+)'\)` über AdminViewService.php gegen `GuardReport.model_fields`; `GUARD_CAUSES` gegen `guard.CAUSES`; Rot-Probe mit `slotsNow`.

## Verifikation

- tests/test_status_endpoint.py: 79 passed
- Vollsuite mit `--deselect ...python_package`: 3796 passed, 18 skipped, 1 failed (siehe unten)
- ruff check, ruff format --check, pyright (latest), vulture: grün
- Grep-Kriterien: `class GuardReport` 1, `slotsInForce` 2, `guard.snapshot()` 1, `memory_events|headroom_bytes` 0
- `git diff --stat 5da24aa -- php backend/src/findling/worker` leer

## Deviations from Plan

Keine inhaltlichen. Hinweis zu Task 2: Da die Implementierung aus Task 1 bereits stand, war der RED-Nachweis dieses Tasks die Rot-Probe (Kopie mit `slotsNow`), kein separater roter Commit.

## Deferred Issues

- `tests/test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_php_half` ist rot. Ursache ist der PHP-Baum aus Welle 1 (26-05); dieser Plan fasst `php/` nicht an. Laut Pin-Regel misst Plan 26-04 (Pin-Eigentümer Welle 2) neu. Nicht angefasst.

## Threat Flags

Keine neuen Flächen über das Register hinaus: T-26-26 akzeptiert (Route bleibt ADMIN), T-26-27 mitigiert (reiner Snapshot-Leser, Test mit gepatchtem memory_guard), T-26-28 mitigiert (Vertragstest mit Rot-Probe).

## Self-Check: PASSED

- FOUND: backend/src/findling/api/status.py, backend/tests/test_status_endpoint.py, backend/tests/test_admin_ui_contract.py
- FOUND: 5ac975ba, 03b559dc, df161e38
