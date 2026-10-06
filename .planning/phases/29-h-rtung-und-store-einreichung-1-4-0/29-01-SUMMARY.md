---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 01
subsystem: verdict-taxonomy, queue-wire
tags: [K6, reasons, l10n, profile, acknowledge]
requires: []
provides:
  - "Reason.SYSTEM_FILE, Reason.LEGACY_FORMAT, Reason.UNSUPPORTED_VARIANT (skipped) in allen fünf Kopien"
  - "Fähigkeitssignal verdicts (ProfileController::VERDICTS_GENERATION = 2, CompanionChoice.verdicts)"
  - "_wire_reason mit _SKIPPED_FALLBACK / _FAILED_FALLBACK in DocumentQueue.acknowledge"
affects: [29-05, 29-07, 29-08, 29-09, 29-12]
tech-stack:
  added: []
  patterns: ["Fähigkeitssignal in der Profilantwort, Rückfall je Liste auf zustandsgültigen Code"]
key-files:
  created: []
  modified:
    - backend/src/findling/extract/errors.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/nc/queue.py
    - php/lib/Service/FileStateService.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Controller/ProfileController.php
    - php/tests/Unit/ProfileControllerTest.php
    - php/l10n/*.js, php/l10n/*.json (16 Dateien)
    - docs/l10n-{french,spanish,italian,dutch,portuguese}.md
    - backend/tests/test_extract_errors.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_profile_wire.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Ein fehlgeschlagener Profil-Read setzt das gemerkte Signal auf None zurück (Rückfallseite), das Signal gilt pro Runde"
  - "Rückfall skipped: system_file/legacy_format -> mime_not_allowed, unsupported_variant -> image_not_ocrable; failed (defensiv): alle drei -> corrupt"
metrics:
  duration: "ca. 45 min"
  completed: 2026-10-06
  tasks: 2
  files: 38
---

# Phase 29 Plan 01: Drei skipped-Reasons und Fähigkeitssignal verdicts Summary

Drei neue skipped-Codes (system_file, legacy_format, unsupported_variant) in Python, PHP und 16 Katalogen, gekoppelt an das Profilfeld `verdicts` = 2; ohne Signal fällt der Draht je Liste auf einen Code zurück, den FileStateService::record für diesen Zustand annimmt.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Drei skipped-Reasons in allen fünf Kopien und 16 l10n-Dateien | 84747afd |
| 2 | Fähigkeitssignal verdicts und Rückfall-Abbildung (K6), Baumhash-Pins | 39b95aa1 |

## Was gebaut wurde

- errors.py/repo.py/FileStateService (REASONS + STATE_REASONS)/AdminViewService REASON_TEXT: drei Codes unter skipped, `excluded` unberührt.
- Label und Abhilfe (vorläufiger Wortlaut, Abnahme in 29-02, Übernahme 29-12) in de, de_DE, es, fr, it, nl, pt_BR, pt_PT, je .js und .json.
- ProfileController: `VERDICTS_GENERATION = 2`, Feld `'verdicts'` in der Antwort; QueueController unverändert.
- queue.py: `VERDICTS_GENERATION`, `_verdicts()` (nur exakt int 2, bool/str/float -> None), `CompanionChoice.verdicts`, `DocumentQueue._companion_verdicts`, `_wire_reason`, `_SKIPPED_FALLBACK`, `_FAILED_FALLBACK`.
- Tests: Paritätstest der drei Codes über alle Kopien; Draht-Tests ohne/mit Signal; Rückfall-Paritätstest gegen PHP STATE_REASONS je Zustand und repo.STATE_REASONS; Namens-/Wertparität `verdicts` PHP <-> Python.
- Baumhash-Pins: PHP_TREE_HASH_TODAY a2986165..., PACKAGE_TREE_HASH_TODAY 1ff0c5ca... (Dateizahlen 88/71 unverändert), per Rezept gemessen.

## Verifikation

- Volle Suite: 4463 passed, 25 skipped (PYTHONUTF8=1).
- ruff check, ruff format --check, pyright (latest) 0 errors, vulture sauber.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Sprachtabellen in docs/ nachgezogen und Schlüsselzahl angehoben**
- **Found during:** Task 1
- **Issue:** test_admin_ui_contract prüft die Tabellen in docs/l10n-{french,spanish,italian,dutch,portuguese}.md gegen die Kataloge und pinnt die Schlüsselzahl von de.json (292).
- **Fix:** sechs Zeilen je Tabelle aus den Katalogwerten ergänzt, Pin auf 298 mit Kommentar.
- **Files modified:** docs/l10n-*.md (5), backend/tests/test_admin_ui_contract.py
- **Commit:** 84747afd

**2. [Rule 2 - Correctness] Signal wird bei fehlgeschlagenem Profil-Read zurückgesetzt**
- Ein Read-Fehler setzt `_companion_verdicts` auf None, damit nie ein veraltetes Signal neue Codes an eine inzwischen ersetzte Companion schickt. Test `test_a_failed_read_after_the_signal_falls_back_again`.
- **Commit:** 39b95aa1

## Deferred Issues

- `php -l` per Docker nicht ausführbar: Docker Desktop lief nicht, kein lokales PHP. Die PHP-Änderungen sind kleine Konstanten-/Array-Ergänzungen; PHPUnit und Lint belegt CI php.yml beim Push in 29-11.
- Docblock von AdminViewService::REASON_TEXT nennt weiterhin "Twenty codes" (schon vor diesem Plan veraltet), nicht angefasst.

## Known Stubs

Keine. Die neuen Codes werden in diesem Plan noch von keiner Stelle erzeugt; das tun 29-05, 29-07, 29-08.

## Threat Flags

Keine neue Angriffsfläche über das Threat-Register hinaus (T-29-01..04 umgesetzt bzw. akzeptiert).

## Self-Check: PASSED

- Commits 84747afd und 39b95aa1 vorhanden, alle geänderten Dateien vorhanden.
