---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 02
subsystem: php-companion
tags: [queue, claim, ocr, profile, appconfig]
requires: []
provides:
  - "QueueService::KIND_BATCH_INDEX_LANE (KIND_OCR => 32, nur Lane index)"
  - "SettingsService::KEY_PROFILE_CONFIRMED und profileConfirmed(): ?string"
  - "GET /profile liefert zusätzlich confirmed (32 Hex oder null)"
affects:
  - "Plan 26-04 (PHP-Pins neu messen nach Merge der Welle 1)"
  - "Plan 26-06 (Python-Parität test_config.py für 32, test_profile_wire.py für confirmed)"
tech-stack:
  added: []
  patterns:
    - "Lane-spezifische Obergrenze je Art als eigene Konstante neben KIND_BATCH"
    - "Validierung beim Lesen mit reject() und null, wie modelPrecision()"
key-files:
  created: []
  modified:
    - php/lib/Service/QueueService.php
    - php/lib/Service/SettingsService.php
    - php/lib/Controller/ProfileController.php
    - php/tests/Unit/QueueServiceTest.php
    - php/tests/Unit/ProfileControllerTest.php
decisions:
  - "Token-Regex mit /D-Modifier: ohne ihn akzeptiert PCRE-$ einen angehängten Zeilenumbruch"
  - "32 OCR-Zeilen nur im Lane index; Lane all bleibt 2, Lane embed 8, LOCK_TIMEOUTS unverändert"
metrics:
  duration: "ca. 20 min"
  completed: 2026-09-28
  tasks: 2
  files: 5
requirements: [PAR-02, PAR-03]
---

# Phase 26 Plan 02: OCR-Anspruch 32 im Lane index und Bestätigungs-Token Summary

Companion liefert im Lane index bis zu 32 OCR-Zeilen (2 je Slot bei höchstens 16 Slots) und reicht den vom Admin gespeicherten 32-Hex-Token `profile_confirmed` validiert über GET /profile an den Container.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | KIND_BATCH_INDEX_LANE mit 32 OCR-Zeilen im Lane index | c9f0f803 | QueueService.php, QueueServiceTest.php |
| 2 | profile_confirmed als Rückweg-Token in der Profil-Route | 3340d14c | SettingsService.php, ProfileController.php, ProfileControllerTest.php |

## Umsetzung

- `claim()` wählt die Obergrenze je Art: im Lane index `KIND_BATCH_INDEX_LANE[$kind]`, falls gesetzt, sonst `KIND_BATCH[$kind] ?? $limit`; danach unverändert `min(..., $rows)`. Zeilenform `QueueMapper::KIND_OCR => 32,` für den Paritäts-Regex beibehalten; `KIND_BATCH` bleibt eigener Block (Regex `const KIND_BATCH = \[` trifft die neue Konstante nicht).
- Docblocks von KIND_BATCH und claim() korrigiert (Obergrenze nicht mehr in jedem Lane gleich, Begründung D-26-05/D-26-13/D-26-14).
- `QueueServiceTest`: neuer Helfer `limitsAskedFor($lane, $limit)` zeichnet das Limit je Art auf; `kindsAskedFor` baut darauf. Tests: index 32, all 2 (mit und ohne Parameter), embed nur `[embed => 8]`, andere Arten im Lane index 128/128/64/32 bei Anspruch 256, und 32 weicht weiterhin einem kleineren Anspruchslimit (16).
- `profileConfirmed()`: '' ergibt null ohne Warnung; sonst nur `/^[0-9a-f]{32}$/D`, alles andere `reject()` plus null. Controller-Antwort um `'confirmed'` ergänzt, Docblocks erweitert.
- `ProfileControllerTest`: alle bestehenden `assertSame`-Antworten um `'confirmed' => null` ergänzt; neue Fälle: gespeicherter Token, fehlender Schlüssel ohne Warnung, DataProvider (nicht hex, 31, 33, Großbuchstaben, angehängter Zeilenumbruch) mit Warnung ohne Wert im Log, Fehlerpfad 500 nur mit error-Feld.

## Verifikation

- Python-Suite mit deselektiertem PHP-Pin: 3710 passed, 16 skipped, 1 deselected.
- Akzeptanz-Greps: alle 1 (siehe Hinweis unten zum Regex-Grep).
- `git diff -- backend/src php/lib/Db`: leer (QueueMapper::LOCK_TIMEOUTS unverändert).
- PHPUnit (php.yml): läuft in CI nach Push, Ergebnis wird in Plan 26-14 eingesammelt.
- `backend/tests/test_profile_wire.py` liest keine Antwortschlüssel des Controllers, keine Anpassung nötig.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Security] Strikter Zeilenende-Anker im Token-Regex**
- **Gefunden in:** Task 2
- **Problem:** PCRE-`$` passt auch vor einem abschließenden `\n`; ein Token mit angehängtem Zeilenumbruch wäre durchgereicht worden (T-26-05).
- **Fix:** Modifier `/D`, zusätzlicher Testfall "trailing newline".
- **Dateien:** php/lib/Service/SettingsService.php, php/tests/Unit/ProfileControllerTest.php
- **Commit:** 3340d14c

### Hinweis zum Akzeptanzkriterium

Der Plan-Grep `grep -c "\^\[0-9a-f\]{32}\$"` in doppelten Anführungszeichen macht aus `\$` einen Zeilenende-Anker und trifft deshalb auch die im Plan vorgesehene Schreibweise nicht. Mit einfachen Anführungszeichen (`grep -c '\^\[0-9a-f\]{32}\$'`) ergibt er 1.

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: php/lib/Service/QueueService.php, php/lib/Service/SettingsService.php, php/lib/Controller/ProfileController.php, php/tests/Unit/QueueServiceTest.php, php/tests/Unit/ProfileControllerTest.php
- FOUND: c9f0f803, 3340d14c
