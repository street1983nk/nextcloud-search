---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
plan: 06
subsystem: php companion (admin page, settings route, l10n)
tags: [issue-37, backup-pause, admin-page, l10n, tree-hash]
requires:
  - 41-05 (SettingsService::paused()/setPaused(), occ pause/resume)
  - 41-04 (/status meldet pause/pausedSince)
provides:
  - POST /apps/findling/admin/pause (SettingsController::setPause), nur Admin + CSRF, nur bool
  - Overview-Felder pause (running|pausing|paused|unknown|unsupported), pausedSince, pauseWished
  - AdminViewService::pauseState(), pausedSince(), quietInPause(), RUN_PAUSED, PAUSE_*-Konstanten
  - Schalter findling-pause-toggle und Statuszeile findling-pause-state (Template + admin.js)
  - sechs neue Sätze in 16 Katalogen und fünf docs/l10n-Tabellen (de 355 -> 361)
  - Abschnitt "Backup-Pause" in docs/admin-page.md
affects:
  - 41-07 (docs/backup.md, auf das admin-page.md verweist)
  - 41-08 (PHPUnit-Beleg im CI)
  - 41-10 (Owner-Abnahme der Wortlaute de/fr)
tech-stack:
  added: []
  patterns:
    - "Zustand aus geschlossener Menge in PHP, Satz im Template und in admin.js aus dem Katalog, nur textContent"
    - "quietInPause() als statische Nachbearbeitung des Overviews, ohne Doubles testbar"
key-files:
  created: []
  modified:
    - php/lib/Controller/SettingsController.php
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/*.json, php/l10n/*.js (16)
    - docs/l10n-{french,spanish,italian,dutch,portuguese}.md
    - docs/admin-page.md
    - php/tests/Unit/SettingsControllerTest.php
    - php/tests/Unit/AdminViewServiceTest.php
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_php_trust_boundary.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Schalter-Text folgt dem gespeicherten Wunsch (pauseWished), der Statussatz dem Backend-Zustand; damit ist 'unsupported ohne Wunsch' kein Fall mehr (ohne Wunsch und ohne Feld = running)"
  - "Backend stumm (keine Antwort) + Wunsch = 'unknown', nicht 'unsupported': ein schweigendes Backend ist kein altes Backend"
  - "In der Pause wird runState running/stalled zu 'paused' und die Laufzustandszeile ausgeblendet; idle und never_run bleiben"
  - "/rates wird in der Pause nicht abgefragt (estimate(..., timeLeftWanted: false)), secondsLeft null"
  - "Kein eigener Überschrift-Schlüssel 'Backup' im Block, damit genau sechs neue Schlüssel"
  - "Formularwerte nur exakt 'true'/'false', alles andere (1, 'yes', 'TRUE', fehlend, Liste) 400 ohne Schreiben"
metrics:
  duration: "ca. 75 min"
  completed: 2026-11-04
  tasks: 2
  commits: 6
---

# Phase 41 Plan 06: Backup-Pause, Companion-Teil 2 (Admin-Seite) Summary

Die Admin-Seite hat einen Schalter "Pause indexing"/"Resume indexing", der über POST /admin/pause (nur Admin, CSRF) denselben appconfig-Schlüssel wie occ setzt, und zeigt den Backend-Zustand paused/pausing/unknown/unsupported je mit einem Katalogsatz; in der Pause verschwinden Restzeit, Gateway-Satz und Stillstands-Satz.

## Commits (RED vor feat)

| Hash | Nachricht |
|------|-----------|
| 1fe09623 | test(41-06): the admin page must switch and show the pause (#37) |
| 6d604a4d | feat(41-06): a pause switch on the admin page (#37) |
| 6b3e15c7 | test(41-06): the pause sentences must be in every catalogue (#37) |
| 9d4cbfe1 | feat(41-06): pause switch and sentences on the admin page (#37) |
| 30833d3d | docs(41-06): the admin page doc names the backup pause |
| 60f46890 | test(41-06): the php tree hash follows the pause switch |

Alle als street1983nk <k.cherif@outlook.de>, ohne Trailer, kein Push.

## Task 1: Route und Overview

- `SettingsController::setPause(mixed $paused = null)` mit FrontpageRoute POST `/admin/pause`, ohne NoAdminRequired/NoCSRFRequired; bool oder exakt "true"/"false", sonst 400 `paused must be a boolean`, nichts gespeichert; Antwort `['paused' => bool]`. Klassen-Docblock auf fünf Adressen nachgezogen (Attributname nicht in Prosa, Anti-Vacuity-Klausel).
- AdminViewService: `pauseState()` (strikter Vergleich gegen running/pausing/paused/unknown, Fremdwert -> unknown, Feld fehlt + Wunsch -> unsupported), `pausedSince()` nur bei paused, `quietInPause()` (secondsLeft null, gatewayUnavailableSince null, running/stalled -> paused).
- PHPUnit: 4 Fälle SettingsControllerTest (Stores True/False, RejectsANonBool mit 8 Werten, IsAdminOnly per Reflection), 4 Fälle AdminViewServiceTest (behavior-Block).
- Statische Logik zusätzlich per Docker php:8.2-cli mit einem Wegwerf-Skript geprüft (15 Zusicherungen, alle OK).

## Task 2: Template, JS, l10n, Doku, Baumhash

- admin.php: Block `findling-pause` unter der Laufzustandszeile, Statuszeile `findling-pause-state` (role=status) und Button `findling-pause-toggle`; Laufzustandszeile im Zustand paused hidden.
- admin.js: `ROUTE_PAUSE`, `pauseBlock(view)` (Sätze über t() und text()), `setupPause()` (send() mit requesttoken, danach schedule(0)), Fingerprint um pause/pauseWished erweitert; bestehender Polling-Takt.
- 16 Kataloge + 5 Tabellen je 6 Zeilen; es/it/nl/pt_PT/pt_BR maschineller Entwurf unter Vorbehalt; fr mit normalem Leerzeichen vor ":" wie die bestehenden 36 Stellen.
- docs/admin-page.md: Abschnitt "Backup-Pause" mit Verweis auf `docs/backup.md` (in Backticks, die Datei entsteht in 41-07).
- PHP-Baumhash 28223473... -> 54627d39... (113 Dateien), Rezept und find/sort/tr/sha256sum gleich.

## Verifikation

- Plan-verify-Schleife: alle sechs Sätze in 16 Katalogen, 5 Tabellen und admin.js.
- test_admin_ui_contract.py, test_php_acl_boundary.py, test_php_trust_boundary.py grün; `-k tree_hash` 4 passed.
- Alle 69 Backend-Testdateien, die php/ oder docs/ lesen: 3941 passed, 253 skipped, 0 failed.
- ruff check, ruff format --check, pyright (0 errors), vulture grün.
- `php -l` (Docker php:8.2-cli) für SettingsController.php, AdminViewService.php, admin.php und beide Testdateien; `node --check php/js/admin.js` grün.
- Keine U+2013/U+2014 in den geänderten Dateien.
- PHPUnit lokal nicht lauffähig (kein vendor, Suite braucht den Bootstrap von nextcloud/server). Der PHPUnit-Beleg kommt im CI in 41-08.

## Deviations from Plan

**1. [Rule 2] Routen-Ratchet in test_php_trust_boundary.py auf 20**
- Die Klausel verlangt, dass jeder Plan, der eine Route hinzufügt, die Schranke anhebt; sonst verliert sie ihre Ratchet-Wirkung.

**2. Overview-Feld `pauseWished` zusätzlich**
- Der Schalter-Text hängt am gespeicherten Wunsch, nicht am Zustand; sonst wäre nach "Resume" bis zum nächsten Profil-Lesen des Backends der falsche Knopf sichtbar.

**3. runState `paused` statt nur Satz-Unterdrückung**
- Der Stillstands-Satz ist der runState-Satz; in der Pause wäre auch "Indexing is running." falsch. Neuer fünfter Laufzustand, Zeile hidden, der Pause-Satz steht direkt darunter.

**4. Satz-Rendering auch im Template**
- Die Seite rendert serverseitig vollständig (Muster der Datei), daher die vier Zustandssätze und beide Button-Texte auch über `$l->t()` im Template; admin.js übernimmt ab dem ersten Poll.

**5. Kein Heading "Backup" im Block**
- Hätte einen siebten Schlüssel gebraucht; Plan fordert genau 361.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche außerhalb des Plans: POST /admin/pause ist im threat_model (T-41-24 bis T-41-28) mit Tests abgedeckt.

## Self-Check: PASSED

- Commits 1fe09623, 6d604a4d, 6b3e15c7, 9d4cbfe1, 30833d3d, 60f46890 vorhanden.
- Geänderte Dateien vorhanden; SUMMARY liegt im Phasenordner.
