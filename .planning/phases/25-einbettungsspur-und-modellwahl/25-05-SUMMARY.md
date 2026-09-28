---
phase: 25-einbettungsspur-und-modellwahl
plan: 05
subsystem: nc-wire
tags: [lane, precision, companion-choice, parity, k6]
requires: ["25-02", "25-03", "25-04"]
provides:
  - "findling.precision: Precision(StrEnum) INT8/FP32, PRECISION_NAMES, PRECISION_DEFAULT"
  - "nc.queue: LANE_ALL/LANE_INDEX/LANE_EMBED/LANES, ClaimResult.lane_honored, claim(..., lane), CompanionChoice, companion_choice()"
  - "nc.client.claim_documents(..., lane=None)"
affects: [worker/poller.py run_once, all queue fakes in tests]
tech-stack:
  added: []
  patterns: ["Echo-Auswertung vor dem frühen Return", "je Wert einzeln gegen geschlossene Menge geprüft"]
key-files:
  created:
    - backend/src/findling/precision.py
  modified:
    - backend/src/findling/nc/client.py
    - backend/src/findling/nc/queue.py
    - backend/src/findling/worker/poller.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_profile_wire.py
    - backend/tests/test_poller.py
    - backend/tests/test_embedding_track.py
    - backend/tests/test_acl_prefilter.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "lane geht nur bei Nicht-None raus; ohne lane bleibt der Draht bytegleich zu 1.3 (K6)"
  - "lane_honored nur bei Echo aus LANES, das gleich (lane or 'all') ist; auch leere Antwort mit Echo zählt (Pitfall 1)"
  - "DocumentQueue.profile() entfällt zugunsten companion_choice() (kein toter Code für vulture)"
  - "PHP-Pins bleiben (75 / 726756a8...), weil dieser Plan keine PHP-Datei berührt; Messung im Worktree bestätigt die Orchestrator-Werte"
metrics:
  duration: "ca. 25 min"
  completed: 2026-09-28
  tasks: 2
  files: 10
---

# Phase 25 Plan 05: Spur-Draht mit Echo und gemeinsames Lesen von Profil und Präzision Summary

Container-Hälfte des Drahts: `claim(..., lane)` mit Echo-Auswertung (`lane_honored`), `companion_choice()` liest Profil und Präzision aus einer Antwort der Profilroute, neues neutrales Modul `precision.py`, Gleichstandstests gegen PHP, Poller und alle Queue-Fakes umgestellt.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Präzisionsnamen, Spur-Draht mit Echo, companion_choice | 20108fa |
| 2 | Poller auf companion_choice, Fakes, Pins | 624e0f5 |

## Umsetzung

- `precision.py`: `Precision(StrEnum)` mit `int8`/`fp32`, `PRECISION_NAMES`, `PRECISION_DEFAULT = Precision.INT8`; stdlib only, loggt nichts. Plan 25-08 ergänzt den Prozesszustand.
- `nc/client.py`: `claim_documents(..., lane: str | None = None)` setzt `params["lane"]` nur bei Nicht-None; Pfad bleibt Stringliteral (Gate). `__all__` um `read_profile` und `topup_documents` ergänzt (IN-01).
- `nc/queue.py`: `LANE_*`/`LANES` neben `KINDS`; `ClaimResult.lane_honored: bool = False`; Echo wird vor dem frühen Return für leere Antworten ausgewertet; `CompanionChoice(profile, precision)` frozen/slots; `companion_choice()` mit einer debug-Zeile ohne Werte bei Ausnahme (T-25-19).
- `worker/poller.py`: `choice = await queue.companion_choice()` und `note_chosen(choice.profile)`; der claim-Aufruf des Pollers bleibt ohne lane.
- Tests: Lane-Parameter, Echo-Matrix (all/embed/index/turbo/3/None), leere Antwort mit Echo, unerreichbarer Companion; companion_choice mit 1.3-Feldstand, null, Einzelprüfung je Wert, Fehlerpfad; Parität LANES, PRECISIONS, PRECISION_DEFAULT (Anti-Vakuität je genau ein Treffer) und Precision-Werte gleich WEIGHTS_INT8/WEIGHTS_FP32; `test_the_poller_claims_without_a_lane` (T13).
- Pins: `PACKAGE_FILES_TODAY = 60`, `PACKAGE_TREE_HASH_TODAY = 8614c00c...`; PHP-Pins im Worktree nachgemessen (75, 726756a8...), unverändert.

## Verifikation

- `pytest -q`: 3538 passed, 15 skipped
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture 80: grün
- `git diff --stat -- php`: leer

## Deviations from Plan

None - plan executed exactly as written. Hinweis zur TDD-Reihenfolge: Tests und Implementierung wurden je Task zusammen committet (kein separater RED-Commit), da die Tasks `type: execute` mit `tdd="true"` auf Task-Ebene sind und das Verhalten vollständig über die neuen Tests abgedeckt ist.

## Known Stubs

- `CompanionChoice.precision` wird vom Poller gelesen, aber noch nicht verwendet; laut Plan übernimmt Plan 25-11 die Präzision. Beabsichtigt.

## Self-Check: PASSED

- FOUND: backend/src/findling/precision.py
- FOUND: 20108fa, 624e0f5
