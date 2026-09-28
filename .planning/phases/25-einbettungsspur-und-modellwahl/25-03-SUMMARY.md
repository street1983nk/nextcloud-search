---
phase: 25-einbettungsspur-und-modellwahl
plan: 03
subsystem: php-companion
tags: [queue, lane, precision, profile-route, companion-1.4.0]
requires: []
provides:
  - "GET /queues/documents?lane=all|index|embed mit Echo lane"
  - "QueueService::LANES / LANE_ALL / LANE_INDEX / LANE_EMBED"
  - "SettingsService::KEY_MODEL_PRECISION, PRECISIONS, PRECISION_DEFAULT, modelPrecision()"
  - "GET /profile antwortet {profile, precision}"
affects:
  - "Plan 25-05 (Container-Draht: lane-Parameter, Echo-Erkennung, precision-Feld)"
  - "Plan 25-05 misst PHP-Pins (PHP_TREE_HASH_TODAY/PHP_FILES_TODAY) nach Welle 1 neu"
tech-stack:
  added: []
  patterns: ["geschlossene Menge + strikter in_array + statische 400", "Echo des angewandten Parameters gegen stilles Verwerfen durch den Dispatcher"]
key-files:
  created:
    - php/tests/Unit/QueueControllerTest.php
  modified:
    - php/lib/Service/QueueService.php
    - php/lib/Controller/QueueController.php
    - php/lib/Db/QueueMapper.php
    - php/lib/Service/SettingsService.php
    - php/lib/Controller/ProfileController.php
    - php/tests/Unit/QueueServiceTest.php
    - php/tests/Unit/ProfileControllerTest.php
decisions:
  - "Spur-Filter als Überspringen in der bestehenden Artenschleife; Reihenfolge, KIND_BATCH und Budget unverändert, damit lane=all bytegleich zu 1.3 bleibt"
  - "LOCK_TIMEOUTS bleibt je Art, nicht je Spur; embed-Spur mit 1800 s konservativ bedient"
  - "modelPrecision() liefert bei ungültigem Wert null statt Default (bewusste Abweichung von profile(), D-25-03)"
metrics:
  duration: "ca. 20 min"
  completed: 2026-09-28
  tasks: 2
  files: 8
---

# Phase 25 Plan 03: Spur-Filter lane und Präzisionsschlüssel model_precision Summary

Companion-Hälfte der Phase 25: der Anspruch `GET /queues/documents` kennt die Spuren all, index und embed und bestätigt die angewandte Spur im Echo `lane`; die Profilroute liefert zusätzlich den eigenen occ-Schlüssel `model_precision` (int8 | fp32, ungültig ergibt null).

## Umsetzung

**Task 1 (PAR-01):** `QueueService::LANES = ['all', 'index', 'embed']` (eine Zeile, Docblock verweist auf `backend/src/findling/nc/queue.py`). `claim($limit, $maxBytes, $lane = LANE_ALL)` überspringt in der Artenschleife bei index die Art embed, bei embed jede andere. `QueueController::getDocuments` nimmt `string $lane = QueueService::LANE_ALL`, `rejectForeignCaller()` bleibt erste Anweisung, danach strikte Prüfung gegen LANES, `badLane()` mit statischem Logsatz und `['error' => 'Unknown lane.']` (400). Antwort `['files' => ..., 'lane' => $lane]`; Docblock begründet das Echo (Dispatcher verwirft unbekannte Parameter still, K6). QueueMapper: nur Kommentar an LOCK_TIMEOUTS ergänzt, Wert unverändert.

**Task 2 (MOD-02, D-25-02):** `SettingsService::KEY_MODEL_PRECISION = 'model_precision'`, `PRECISIONS = ['int8', 'fp32']` (eine Zeile, Verweis auf `backend/src/findling/precision.py`), `PRECISION_DEFAULT = 'int8'`, occ-Hinweis im Docblock. `modelPrecision(): ?string` liest mit Default int8, verwirft Werte außerhalb der Menge über `reject()` (Zähler, kein Wert im Log) und liefert null. `ProfileController` antwortet im selben try `{profile, precision}`; die 500-Antwort bleibt ohne Namen.

## Tests

- `QueueServiceTest`: embed-Spur fragt nur embed, index-Spur nie embed (Rest in KINDS-Reihenfolge), all und ohne Parameter identisch zu KINDS, LANES geschlossen.
- `QueueControllerTest` (neu): Echo all/embed/index, unbekannte Spur 400 ohne Wert im Log, strikter Vergleich (`Embed`), fremder Aufrufer 403 vor der Spurprüfung.
- `ProfileControllerTest`: Staging über eine Map beider Schlüssel; fp32 wird ausgeliefert; `FP32`, `fp16`, leer ergeben null mit einer Warnung ohne Wert; 500 ohne Profil- und Präzisionsnamen.
- PHPUnit läuft nur in CI (lokal kein PHP, wie in den bisherigen Phasen). RED ließ sich deshalb lokal nicht ausführen; die RED-Commits liegen trotzdem getrennt vor den GREEN-Commits.
- Python: Gate B, Read-only-Gate, test_config: 251 passed. test_php_trust_boundary + test_uninstall_contract: 36 passed. Gesamtsuite mit Deselect des PHP-Pin-Tests: 3494 passed, 15 skipped.
- `git diff --stat -- backend/src` leer; PHP-Pins nicht angefasst (Pin-Eigentümer Plan 25-02, Neumessung in 25-05).

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

RED-Commits `6bc6957`, `8af6993` vor GREEN-Commits `a2743ce`, `0bf9d4b`. Die RED-Ausführung selbst steht aus, weil PHPUnit nur in CI läuft; der Nachweis kommt mit dem CI-Lauf nach dem Push (Push-Entscheid beim Owner).

## Known Stubs

Keine.

## Commits

| Task | Commit | Nachricht |
|------|--------|-----------|
| 1 RED | 6bc6957 | test(25-03): add failing tests for claim lanes and lane echo |
| 1 GREEN | a2743ce | feat(25-03): claim lanes all/index/embed with echo at the queue route |
| 2 RED | 8af6993 | test(25-03): add failing tests for model_precision in the profile answer |
| 2 GREEN | 0bf9d4b | feat(25-03): model_precision key served through the profile route |

## Self-Check: PASSED

- php/tests/Unit/QueueControllerTest.php vorhanden
- Commits 6bc6957, a2743ce, 8af6993, 0bf9d4b im Log
- Akzeptanz-Greps: LANES 1, `string $lane = QueueService::LANE_ALL` 1, `'lane' => $lane` 1, `Unknown lane.` 1, PRECISIONS 1, KEY_MODEL_PRECISION 1, `modelPrecision(): ?string` 1, `'precision' => $this->settingsService->modelPrecision()` 1
