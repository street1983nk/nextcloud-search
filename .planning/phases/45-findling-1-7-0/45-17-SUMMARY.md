---
phase: 45-findling-1-7-0
plan: 17
subsystem: php-companion
tags: [issue-59, secure-view, richdocuments, reader-order, content-gateway, tdd]
requires: [45-09]
provides: [Owner-Entscheide zu #59 und V-45-10-02/03, Nachbau M1 bis M5 auf v1.6.5, ReaderCandidates (Besitzer zuerst), GatewayReader (zweites Öffnen in actAs nur nach Secure-View-Ablehnung), 403 mit X-Findling-Refusal policy]
affects: [45-18, 45-19, 45-20, 45-21, 45-22, 45-10]
tech-stack:
  added: []
  patterns: [Erkennung einer Fremd-Ausnahme über Klasse, exakte Nachricht und getTrace()[0] als Strings ohne die Fremdklasse zu laden, eine Lesereihenfolge für Claim und Gateway, Test-Trace per ReflectionProperty auf Exception::trace]
key-files:
  created:
    - php/lib/Service/ReaderCandidates.php
    - php/lib/Service/GatewayReader.php
    - php/tests/Unit/ReaderCandidatesTest.php
    - php/tests/Unit/GatewayReaderTest.php
    - php/tests/Unit/SecureViewRefusal.php
    - .planning/phases/45-findling-1-7-0/45-ANTWORTEN.md
  modified:
    - php/lib/Service/QueueService.php
    - php/lib/Controller/GatewayController.php
    - php/tests/Unit/QueueServiceTest.php
    - php/tests/Unit/QueueServiceReaderTest.php
    - php/tests/Unit/GatewayControllerTest.php
    - backend/tests/test_measurement_scripts.py
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
    - .planning/phases/45-findling-1-7-0/45-AUDIT.md
decisions:
  - "Owner 2026-11-22 11:52 UTC 'Go  und für foolfitz auch': Texte 1 bis 7 wie im Entwurf, V-45-10-02 Form i, allGroups G1, Gate c1, Wartezeit d1, Korrektur des #59-Satzes ('If the secure view policy refuses the fetch, Findling retries it as the file's owner before giving up.')"
  - "Besitzer = Mount-Point exakt '/<uid>/' mit OC\\Files\\Mount\\LocalHomeMountProvider oder ObjectHomeMountProvider (stable33/34/35 belegt); Node::getOwner() verworfen"
  - "Die Kappung von 500 Mounts beendet die Schleife auch für den Besitzer; dahinter kein Besitzer, alphabetisch wie in 1.6.5"
  - "asked zählt die Leser der zweiten Runde einschließlich übersprungener; ohne Besitzer wird auch die benannte Person in actAs erneut gefragt (eine Reihenfolge für Claim und Gateway)"
metrics:
  duration: "Task 2 und 3 ca. 190 min laut Systemzeit (ca. 11:55 bis 15:05 UTC), davon ca. 90 min PHPUnit, PHP-Gates und Mutationsläufe in Docker"
  completed: 2026-11-22
---

# Phase 45 Plan 17: #59, Besitzer zuerst und zweites Öffnen bei Secure View Summary

Der Lesepfad fragt den Besitzer einer Datei zuerst (Claim und Gateway über ReaderCandidates::readingOrder), öffnet eine Datei nur nach einer nachgewiesenen Secure-View-Ablehnung von richdocuments erneut in actAs (Besitzer allein, ohne Besitzer bis 20 Leser) und antwortet bei einer Sperre für alle Gefragten mit 403 und `X-Findling-Refusal: policy`; jede andere ForbiddenException endet fail-closed ebenso.

## Tasks

| Task | Inhalt | Commits |
|---|---|---|
| 1 | Freigaben, #59-Antworttext, Quellen am Tag, Nachbau M1 bis M5 auf v1.6.5 | 15fef4aa, 838c7c30, Checkpoint-Stand 7fd0ba8c |
| 2 | Owner-Checkpoint: sechs Zeilen plus Korrektur 59 in 45-FREIGABEN.md, Satz in 45-ANTWORTEN.md ersetzt | 89cc8ddf |
| 3 | Refactor (ReaderCandidates), RED, GREEN, fünf Mutationen | 92a662c7 (refactor), 4ede2575 (fix) |

## Ergebnisse

- Refactor vor dem ersten neuen Test: volle Suite `OK (1302 tests, 8363 assertions)`, PHP-Gates Exit 0, Strukturgates 819 passed, ruff, ruff format, pyright, vulture grün.
- RED gegen ein Gerüst mit dem Verhalten von 1.6.5: `Tests: 75, Errors: 12, Failures: 12`, nur neue Fälle, wörtlich in 45-AUDIT.md `### RED und GREEN 45-17`.
- GREEN: gefiltert `OK (75 tests, 492 assertions)`, voll `OK (1342 tests, 8601 assertions)`; PHP-Gates (Psalm-Taint gegen ocp v33.0.9, v34.0.6, v35.0.3, php-cs-fixer, zizmor, actionlint) Exit 0; Strukturgates 819 passed; ruff, ruff format, pyright latest, vulture grün.
- Mutationen (je rot, Dateien danach byte-gleich): Frame-Bedingung entfernt, irgendein Frame statt `getTrace()[0]`, kein Abbruch nach dem Besitzer, kein Besitzer-Vorzug, fopen außerhalb von actAs.
- Baumhash php/ ef4f5a19 mit 141 Dateien (Positivkontrolle 92a662c7 -> 5b54386c mit 137).
- findling-59 lief in Task 2 und 3 nie; `docker ps -q` am Ende leer.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] RED gegen ein Gerüst statt ohne GatewayReader**
- **Found during:** Task 3, Schritt 2
- **Issue:** Ohne die Klasse GatewayReader wären auch alle bestehenden Fälle von GatewayControllerTest rot gewesen (Konstruktor), die Vorgabe verlangt RED nur mit den neuen Fällen.
- **Fix:** RED lief gegen ein nicht committetes Gerüst mit dem Öffnen von 1.6.5 (keine Erkennung, kein zweites Öffnen); im Audit benannt.
- **Commit:** keiner (nur lokal, GREEN ersetzte das Gerüst in 4ede2575)

**2. [Rule 3 - Blocking] Zusätzliche Testhilfe SecureViewRefusal.php**
- **Found during:** Task 3, Schritt 2
- **Issue:** richdocuments liegt nicht im Autoload der Test-Checkout, und der echte Trace (Ursprungs-Frame SecureViewWrapper::checkFileAccess) muss in drei Testdateien gleich gebaut werden.
- **Fix:** `php/tests/Unit/SecureViewRefusal.php` (nicht in files_modified des Plans) setzt den Trace per ReflectionProperty; keine Klasse im Namensraum von richdocuments. PHP-Dateizahl 141 statt 140.
- **Commit:** 4ede2575

**3. [Rule 3 - Tooling] verify-grep auf den Klassennamen nur aus einer Skriptdatei prüfbar**
- **Found during:** Task 3, verify
- **Issue:** Die Werkzeugschicht des Ausführers halbiert Backslashes einer Befehlszeile, der grep `OCA\\\\Richdocuments...` wird dadurch falsch.
- **Fix:** Dieselbe Zeile wörtlich aus `<scratchpad>/verify_greps.sh`: `GREPS_OK`; Bytes per `od -c` geprüft. Kein Codeeingriff.

**4. [Hinweis] Owner-Freigabe Korrektur 59 schon in 45-17 eingetragen**
- Auf Anweisung des Koordinators mit dem Owner-Zitat von 11:52; 45-21 setzt sonst erst den Abgleich. Freigegebener Wortlaut steht unter der Zeile in 45-FREIGABEN.md, der Satz in 45-ANTWORTEN.md ist ersetzt, alles andere byte-gleich.

## Befunde

- I-45-17-06 (INFO): `path` eines Auftrags folgt jetzt dem Leser (Besitzer), in 45-20 an einem echten Treffer gegenprüfen.
- I-45-17-07 (INFO): `asked` zählt übersprungene Leser mit; die benannte Person wird ohne Besitzer in actAs erneut gefragt; Zeitmessung in 45-20 (T-45-61).

## Threat Flags

Keine neue Fläche außerhalb des Threat-Registers: das zweite Öffnen (T-45-57, -58, -59, -61, -67, -74, -76) ist im Plan geführt; neue Logzeilen tragen nur `fileId`, `asked` und Klassennamen.

## Known Stubs

Keine.

## Offene Punkte

- 45-18 setzt Vokabular, Urteil policy_blocked, Texte 1 bis 7 und das Lesen des Kopfs im Backend um.
- 45-21 prüft "tries the next one" gegen das Endverhalten; die Korrekturzeile ist schon da, dort bleiben nur der Abgleich und die übrigen Prüfpunkte.
- Der Zusatz "und für foolfitz auch" im Owner-Zitat ist in 45-17 nicht ausgelegt; der Koordinator klärt, worauf er sich bezieht.

## Self-Check: PASSED

Dateien vorhanden: ReaderCandidates.php, GatewayReader.php, ReaderCandidatesTest.php, GatewayReaderTest.php, SecureViewRefusal.php, 45-ANTWORTEN.md. Commits vorhanden: 89cc8ddf, 92a662c7, 4ede2575.
