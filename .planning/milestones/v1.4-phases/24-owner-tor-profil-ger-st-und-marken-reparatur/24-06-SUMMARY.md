---
phase: 24-owner-tor-profil-ger-st-und-marken-reparatur
plan: 06
subsystem: backend-status, docs
tags: [profile, hardware, status-route, owner-gate]
requires: [24-02, 24-03]
provides:
  - "GET /status Block profile (chosen, suggested, effective, downgraded, hardware, values, sources) in beiden Zweigen"
  - "Vierte Startaussage note_hardware(await asyncio.to_thread(detect)) im Lifespan"
  - "docs/profiles.md mit datiertem Owner-Tor und woertlichem Store-Satz"
affects: [24-05 (Baumhash nach Merge neu messen), Phase 25/26 (Slots), Phase 27 (Anzeige auf der Seite)]
tech-stack:
  added: []
  patterns: ["Prozesswert in _volume() setzen und in _of() uebertragen (Pitfall 2)"]
key-files:
  created:
    - docs/profiles.md
  modified:
    - backend/src/findling/api/status.py
    - backend/src/findling/main.py
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_main_lifespan.py
    - backend/tests/test_measurement_scripts.py
    - docs/admin-page.md
decisions:
  - "Wire-Schluessel der Profilwerte als ausgeschriebene Abbildung PROFILE_VALUE_KEYS statt automatischer camelCase-Umwandlung"
  - "Hardware-Erkennung laeuft auch auf einem geteilten Volume (die Box ist die Box)"
metrics:
  duration: "ca. 25 min"
  completed: 2026-09-27
  tasks: 2
  files: 7
---

# Phase 24 Plan 06: Melde-Seite des Profil-Gerüsts Summary

Hardware-Erkennung einmal je Start im Lifespan (per `asyncio.to_thread`, fehlertolerant) und ein Block `profile` in der ADMIN-Statusroute mit gewählt, vorgeschlagen, wirksam, Rückstufung, Hardware, Werten und Quelle je Wert; das Owner-Tor vom 27.09.2026 steht datiert in `docs/profiles.md`.

## Tasks

| Task | Name | Commits | Dateien |
| ---- | ---- | ------- | ------- |
| 1 | Hardware im Lifespan und Profilblock in der Statusroute (TDD) | e484b7e (RED), c96e3c2 (GREEN) | api/status.py, main.py, test_status_endpoint.py, test_main_lifespan.py, test_measurement_scripts.py |
| 2 | Owner-Tor und Profil-Gerüst in docs/profiles.md, Verweis in docs/admin-page.md | 4f8bdad | docs/profiles.md, docs/admin-page.md |

## Umsetzung

- `api/status.py`: `PROFILE_VALUE_KEYS`, `HardwareReport`, `ProfileReport`, `_profile_report()` liest ausschließlich `snapshot()`; `StatusResponse.profile`; `profile=_profile_report()` in `_volume()`, `profile=volume.profile` in `_of()` mit Begründungskommentar.
- `main.py`: nach `warn_on_uncovered_languages`, vor `stop_indexing = asyncio.Event()`, außerhalb des Shared-Volume-Zweigs: `note_hardware(await asyncio.to_thread(detect))` in `try/except Exception`, Warnung nennt nur den Ausnahmetyp.
- Tests: `"profile"` in FIELDS; fünf Profilfälle je in beiden Zweigen (Ruhezustand = Sparsam-Zeile, Leistung 16 Kerne/64 GiB = 15 Slots, Schrumpfung chosen performance/effective standard, Env 29 = Quelle env, Env 30 = 100/profile); drei Lifespan-Tests (Zustand trägt die Fake-Hardware, werfendes detect stoppt den Start nicht und loggt ohne Pfad, statischer Test auf `to_thread(detect)` vor dem Poller).

## Verifikation

- `uv run pytest -q`: 3475 passed, 15 skipped vor dem Baumhash-Nachzug; danach test_measurement_scripts 435 passed, Statustests und Lifespan-Tests grün.
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber.
- Acceptance-Greps: `profile=volume.profile` 1, `profile=_profile_report()` 1, `to_thread(detect)` 1 und vor `stop_indexing`; Store-Satz exakt 1 Treffer; 8 verschiedene D-24-0x; occ-Zeile vorhanden; 0 Em-/En-Dashes; `test_store_metadata.py` unverändert.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Baumhash der Python-Paketbäume nachgezogen**
- **Found during:** Task 1 (Gesamtsuite)
- **Issue:** `test_measurement_scripts.py` pinnt den Hash über `backend/src/findling`; main.py und api/status.py haben neue Bytes.
- **Fix:** `PACKAGE_TREE_HASH_TODAY` auf `705bcb9b...e5e8411` mit Begründungskommentar, Anzahl bleibt 59. Der parallele Plan 24-05 ändert denselben Baum; nach dem Merge neu messen.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Commit:** c96e3c2

**2. [Rule 1 - Testfehler] Erwarteter Vorschlag im Lifespan-Test korrigiert**
- 8 Kerne/16 GB erfüllen die Leistungs-Schwelle (12 GB, 6 Kerne), der Test erwartete fälschlich standard. Vor dem GREEN-Commit korrigiert.

## TDD Gate Compliance

RED `e484b7e` (test) vor GREEN `c96e3c2` (feat); kein Refactor nötig.

## Known Stubs

Keine. Die Anzeige des Blocks auf der Adminseite ist bewusst Phase 27 (im Plan-Objective festgelegt).

## Self-Check: PASSED

- FOUND: docs/profiles.md, backend/src/findling/api/status.py, backend/src/findling/main.py
- FOUND: e484b7e, c96e3c2, 4f8bdad
