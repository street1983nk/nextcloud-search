---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 01
subsystem: extract/sandbox
tags: [sandbox, oom, nice, childkilled, ocr]
requires: []
provides:
  - SANDBOX_NICE, _lower_own_standing, _JOB_PRIORITY, ExtractionWorker.priority()
  - ExtractionWorker.halt()
  - ChildKilled, EngineKilled, KILLED_EXIT_CODE in extract/errors.py
affects:
  - Plan 26-04 (Pool hält N ExtractionWorker, fängt ChildKilled, nutzt halt())
  - Plan 26-09 (Solo-Wiederholung nach ChildKilled)
  - Plan 26-11 (Kill-Test)
tech-stack:
  added: []
  patterns:
    - "Kind stuft sich nach setsid selbst herab (nice, oom_score_adj, autogroup), best effort"
    - "Fremd-SIGKILL als Ausnahme statt Verdikt; eigener Kill über Flag ausgenommen"
key-files:
  created: []
  modified:
    - backend/src/findling/extract/sandbox.py
    - backend/src/findling/extract/errors.py
    - backend/src/findling/extract/ocr.py
    - backend/src/findling/extract/image.py
    - backend/tests/test_sandbox.py
    - backend/tests/test_ocr.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_extract_edge_paths.py
decisions:
  - "KILLED_EXIT_CODE zentral in errors.py (win32: -9, sonst -signal.SIGKILL), weil signal.SIGKILL unter Windows fehlt und die Tests dort laufen"
  - "extract_guarded bildet ChildKilled auf das Vor-Phase-26-Verdikt ab (engine -> ocr_failed, sonst corrupt)"
  - "run() zählt eine Datei mit getötetem Engine als bearbeitet (Leck-Schranke), Kind bleibt"
metrics:
  duration: "ca. 45 min"
  completed: 2026-09-28
  tasks: 2
  files: 8
---

# Phase 26 Plan 01: Kind-Härtung und Kill-Erkennung Summary

Jedes Sandbox-Kind läuft mit nice 10, oom_score_adj 1000 und autogroup 10 direkt nach setsid. Ein Kind oder tesseract, das von außen per SIGKILL beendet wird, liefert jetzt ChildKilled und kein Endverdikt mehr. Eigener Timeout-Kill und halt() behalten ihre Verdikte.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | nice 10, oom_score_adj 1000 und Prioritäts-Probe im Kind | dbf8af19 |
| 2 | ChildKilled, EngineKilled und halt() statt falscher Verdikte | 1cfe4537 |

## Was gebaut wurde

- `_child_main`: Reihenfolge setsid, `os.nice(SANDBOX_NICE)`, `_lower_own_standing()`, Geheimnisabwurf, RLIMIT_AS, Pool-Pinning, erst dann der Dispatcher-Import. Das ist per Quelltext-Reihenfolge-Test abgesichert.
- `_JOB_PRIORITY` und `ExtractionWorker.priority()` liefern `(os.nice(0), oom_score_adj)` aus dem Kind, unter Windows `(0, -1)`.
- `_ask` liest bei Sende-Fehler und EOF über `_bury()` erst join, dann exitcode und erst danach `_recycle()`. Bei `KILLED_EXIT_CODE` ohne Halt-Flag folgt `ChildKilled(engine=False)`.
- Das Kind fängt `EngineKilled` vor `except Exception` ab und antwortet mit dem Sentinel `("engine_killed",)`. `run()` und `probe()` machen daraus `ChildKilled(engine=True)`, das Kind bleibt dabei am Leben.
- `halt()`: setzt zuerst das Flag, dann folgt der Gruppen-Kill. Die Methode ist thread-sicher gegen einen wartenden `_ask` (ValueError bei bereits geschlossenem Prozess wird geschluckt). `_start_child` setzt das Flag zurück.
- `extract_guarded` fängt `ChildKilled` ab. Die Docstrings sind nachgezogen: Modul und Fassade gelten für Sparsam und Werkzeuge, der Pool aus 26-04 hält N Worker.
- Kein neuer Reason-Code. Das sichert der Test `test_a_killed_child_carries_no_reason_code`.

## Verifikation

- Windows: gesamte Suite 3726 passed / 18 skipped. Der eine rote Test (Schreib-Ratchet) ist behoben, siehe Abweichungen.
- Linux (Docker, python3.13-trixie-slim): test_sandbox + test_ocr 84 passed, darunter die POSIX-Tests mit Priorität (10, 1000), Vererbung an den Enkel und Fremd-SIGKILL. Gesamte Suite: 3732 passed. Einziger Fehlschlag ist `test_every_sampler_started_through_sudo_directly_is_executable_in_the_index`, weil im Container kein git vorhanden ist. Das ist umgebungsbedingt, auf Windows grün und nicht Teil dieses Plans.
- Gates: ruff check, ruff format --check, pyright latest (Windows und `--pythonplatform Linux`) mit 0 Fehlern, vulture sauber.
- `git diff --stat -- php backend/src/findling/worker backend/src/findling/config.py` ist leer.

## Abweichungen vom Plan

### Automatisch behoben

**1. [Rule 3 - Blockierend] Schreib-Ratchet in test_extract_edge_paths.py**
- **Gefunden in:** Task 2 (volle Suite)
- **Problem:** `test_the_file_travel_path_writes_in_exactly_the_pinned_places` zählt jede `write_text` im Paket. Die zwei best-effort-Schreibzugriffe nach `/proc/self/oom_score_adj` und `/proc/self/autogroup` sind neu.
- **Fix:** Beide Einträge in `EXPECTED_TRAVEL_PATH_WRITES` aufgenommen und mit den drei Ratchet-Fragen begründet: Verzeichnis `/proc/self`, feste Default-Namen, vom Code gewählt, nie aus einer Queue-Zeile.
- **Commit:** 1cfe4537

**2. [Rule 3 - Blockierend] Zähler der Kill-Stellen**
- `test_every_kill_goes_through_the_group_kill` erwartete 3 Vorkommen von `_kill_child_tree(`. Mit `halt()` sind es 4. Der Test ist mit Kommentar angepasst.

**3. [Rule 1 - Plattform] KILLED_EXIT_CODE statt `-signal.SIGKILL` direkt**
- `signal.SIGKILL` gibt es unter Windows nicht, dort laufen Tests und pyright. Die Konstante liegt deshalb plattformgetrennt in `errors.py` und wird von `sandbox.py` und `ocr.py` genutzt. Unter Linux ist der Wert identisch `-signal.SIGKILL`.

**4. image.py: nur Kommentar**
- `EngineKilled` ist eine Schwesterklasse, kein except-Zweig in ocr.py, image.py oder dispatch.py fängt sie ab (keiner fängt `Exception`). Ein vorgeschaltetes `except EngineKilled: raise` war daher unnötig. Tests belegen den Durchlauf durch alle drei Module.

## Threat Flags

Keine neuen Flags. Die Schreibzugriffe nach `/proc/self` sind durch T-26-02 abgedeckt.

## Known Stubs

Keine.

## Self-Check: PASSED
