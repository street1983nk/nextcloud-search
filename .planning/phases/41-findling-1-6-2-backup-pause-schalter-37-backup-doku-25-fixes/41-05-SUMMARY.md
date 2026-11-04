---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
plan: 05
subsystem: php companion (settings, profile route, occ)
tags: [issue-37, backup-pause, occ, profile, tree-hash]
requires:
  - 41-04 (Backend liest paused über /profile, /status meldet pause/pausedSince)
provides:
  - SettingsService::KEY_PAUSED = 'paused', paused(), setPaused()
  - /profile-Feld paused im selben try (Lesefehler -> 500 ohne Feld)
  - occ findling:pause [--wait[=SEKUNDEN]] (Vorgabe 2400, Poll 5 s), occ findling:resume
  - PauseCommand::pauseOf() (geschlossene Menge, strikter Vergleich), PauseCommand::adminUserId()
affects:
  - 41-06 (Admin-Seite schreibt denselben Schlüssel über setPaused)
  - 41-08 (PHPUnit-Beleg im CI)
tech-stack:
  added: []
  patterns:
    - "Sleeper als überschreibbare protected-Methode sleepFor(), Uhr über ITimeFactory; Test mit anonymer Unterklasse"
key-files:
  created:
    - php/lib/Command/PauseCommand.php
    - php/lib/Command/ResumeCommand.php
    - php/tests/Unit/PauseCommandTest.php
  modified:
    - php/lib/Service/SettingsService.php
    - php/lib/Controller/ProfileController.php
    - php/appinfo/info.xml
    - php/tests/Unit/SettingsServiceTest.php
    - php/tests/Unit/ProfileControllerTest.php
    - backend/tests/test_profile_wire.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Kein Purge-Listeneintrag nötig: PurgeService::run() löscht mit appConfig->deleteApp() alle Schlüssel der App (php/lib/Service/PurgeService.php:167), KEY_PAUSED geht damit mit"
  - "Sleeper als protected sleepFor() statt Konstruktorparameter: der NC-DI-Container kann einen Closure-Parameter nicht sicher autowiren; Uhr über ITimeFactory"
  - "Mit --wait führt ein stummes Backend sofort zu Exit 1 (kein Weiterpollen), ohne --wait zu Exit 0"
  - "Ungültiger --wait-Wert (0, negativ, Wort, Bruch, leer) -> Exit 2 (INVALID) mit '--wait takes a number of seconds.', bevor der Wunsch gespeichert wird"
  - "resume endet immer mit Exit 0 und Statuszeile; ohne Antwort oder ohne Feld 'Status: unknown'"
metrics:
  duration: "ca. 45 min"
  completed: 2026-11-04
  tasks: 2
  commits: 5
---

# Phase 41 Plan 05: Backup-Pause, Companion-Teil 1 (occ) Summary

Der Pause-Wunsch liegt im appconfig-Schlüssel `findling/paused`, reist über /profile zum Backend, und `occ findling:pause --wait` endet erst mit Exit 0, wenn /status exakt `paused` meldet; `occ findling:resume` löscht den Wunsch.

## Commits (RED vor feat)

| Hash | Nachricht |
|------|-----------|
| 0ad1aa51 | test(41-05): the profile route must carry the pause wish (#37) |
| d7847322 | feat(41-05): the companion stores the pause wish and hands it to the backend (#37) |
| 76ddb9e7 | test(41-05): occ pause and resume (#37) |
| 92cb31b4 | feat(41-05): occ findling:pause and findling:resume (#37) |
| 0307c283 | test(41-05): the php tree hash follows the pause commands |

Alle als street1983nk <k.cherif@outlook.de>, ohne Trailer. Kein Push.

## Task 1: Schlüssel und /profile

- SettingsService: `KEY_PAUSED = 'paused'` mit Docblock (D-41-05, D-41-07, keine Migration), `paused()` über `getValueBool(..., false)`, `setPaused()` über `setValueBool`.
- ProfileController: `'paused' => $this->settingsService->paused()` im selben try hinter `verdicts`; Docblock ergänzt.
- Purge/Uninstall: keine Schlüsselliste vorhanden; `PurgeService::run()` ruft `deleteApp(Application::APP_ID)` (PurgeService.php:167), damit ist KEY_PAUSED abgedeckt.
- Tests: SettingsServiceTest (3 Fälle), ProfileControllerTest `testTheProfileAnswerCarriesPaused` (true/false) und `testAnUnreadablePauseKeyIsA500WithoutTheField`; zusätzlich Drahttest in test_profile_wire.py (Name auf beiden Seiten).

## Task 2: Commands, info.xml, Baumhash

- PauseCommand: `findling:pause`, `--wait` VALUE_OPTIONAL (ohne Wert 2400 s), Poll 5 s, strikter Vergleich gegen `running|pausing|paused|unknown`, alles andere `unknown`; fehlendes Feld -> Exit 1 mit Aktualisierungssatz.
- ResumeCommand: `findling:resume`, `Already running.` bzw. `Resumed. Indexing continues.` plus `Status: <pause>`.
- info.xml: beide Commands in derselben `<commands>`-Zeile. test_store_metadata.py prüft die Commands-Liste nicht, unverändert; 117 passed.
- Sätze zeichengleich (`grep -F` je Satz in PauseCommand.php/ResumeCommand.php): alle 8 gefunden.
- PauseCommandTest: 9 Fälle des behavior-Blocks plus Namen, Vorgabe-Wartezeit, ungültige --wait-Werte und resume bei stummem Backend; kein echtes sleep (anonyme Unterklasse, Uhr wird nur weitergestellt).
- PHP-Baumhash: eb7fd98f... (110) -> 2822347360e64a68... (113 Dateien: 2 unter lib/, 1 unter tests/). Rezept und find/sort/tr/sha256sum unabhängig gleich. `-k tree_hash` 4 passed.

## Verifikation

- Alle 33 Backend-Testdateien, die php/ lesen: 2223 passed / 243 skipped, einziger Fehler war der erwartete Baumhash vor dem Nachziehen.
- ruff check und ruff format --check über backend grün (Python nur in Tests geändert, pyright/vulture ohne Quelländerung nicht neu gelaufen).
- `php -l` (Docker php:8.2-cli) für alle 7 geänderten/neuen PHP-Dateien: keine Syntaxfehler.
- PHPUnit lokal nicht lauffähig (kein vendor, Suite braucht den Bootstrap von nextcloud/server). Kein Zwischen-Push (Owner-Vorgabe: nicht pushen): PHPUnit-Beleg in 41-08.
- Keine U+2013/U+2014 in den geänderten Dateien.

## Deviations from Plan

**1. [Rule 1] Bestehende Gleichheitstests in ProfileControllerTest um `'paused' => false` erweitert**
- Sieben `assertSame` auf die volle Antwort hätten mit dem neuen Feld gebrochen; Inhalt sonst unverändert.

**2. [Rule 2] Drahttest test_profile_wire.py**
- Hält den Namen `paused` auf PHP- und Python-Seite zusammen, wie bei `confirmed` und `verdicts`.

**3. Sleeper als protected-Methode statt Konstruktorparameter**
- Siehe Entscheidungen (DI-Autowiring). Test bleibt ohne echtes Warten.

**4. Ungültiger --wait-Wert wird abgelehnt (Rule 2, Eingabeprüfung)**
- Nicht im Plan; verhindert einen gespeicherten Wunsch, auf den niemand wartet.

**5. Baumhash-Zahl 113 statt 112**
- Das Rezept zählt php/**/*.php inklusive tests/, daher drei neue Dateien.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche: kein neuer Endpunkt, /profile bleibt ExAppRequired + rejectForeignCaller (T-41-20); geschlossene Menge mit Test (T-41-21); altes Backend -> Exit 1 mit Test (T-41-22); occ-Ausgabe nur Zustandswörter (T-41-23).

## Self-Check: PASSED

- Dateien vorhanden: PauseCommand.php, ResumeCommand.php, PauseCommandTest.php.
- Commits 0ad1aa51, d7847322, 76ddb9e7, 92cb31b4, 0307c283 vorhanden.
