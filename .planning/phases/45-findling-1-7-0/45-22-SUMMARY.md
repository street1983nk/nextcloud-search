---
phase: 45-findling-1-7-0
plan: 22
subsystem: php-companion-search
tags: [e3, secure-view, watermark, richdocuments, snippets, tdd, security]
requires: [45-19]
provides: [SnippetPolicy (S3 mit öffentlichen OCP-APIs, fail-closed), SearchService fragt Ausschnitte nur für die Antwort der Policy an, Gate Regel 8 auf den Snippet-Aufruf, ACL-Gate SnippetPolicy ohne eigene Auflösung, Baumhash PHP 143/ff141406]
affects: [45-23, 45-20, 45-21, 45-10, 45-14]
tech-stack:
  added: []
  patterns: [eigene DI je Entscheidungsklasse, Regeln einmal je Request, Abfragen gebändert je Seite, Knoten nur über SearchService::readableFile, fail-closed mit Logzeile nur aus Zähler und Klassenname]
key-files:
  created:
    - php/lib/Service/SnippetPolicy.php
    - php/tests/Unit/SnippetPolicyTest.php
    - .planning/phases/45-findling-1-7-0/45-22-SUMMARY.md
  modified:
    - php/lib/Service/SearchService.php
    - php/tests/Unit/SearchServiceTest.php
    - backend/tests/test_php_static_gates.py
    - backend/tests/test_php_acl_boundary.py
    - backend/tests/test_measurement_scripts.py
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
    - .planning/phases/45-findling-1-7-0/45-AUDIT.md
decisions:
  - "Owner 2026-11-23 02:42 UTC 'Go': E3-Weg S3, unter shareDisabledDownload S1 genau wie richdocuments, sonst Rückfall auf S3; (a)+(b) unter shareRead; unbekannte Modi über getKeys('files'); fail-closed; CHANGELOG E3 ja (EN/DE/FR wie vorgelegt); Altbestand A1; kein neuer Oberflächensatz"
  - "S1 für shareDisabledDownload nicht umgesetzt, Rückfall auf S3: richdocuments prüft die Super-Freigabe des Mounts (belegt), die ist mit öffentlichen OCP-APIs nicht erreichbar (nur über das private Wrapper::__call oder eine Psalm-Unterdrückung, die der Gate verbietet)"
  - "watermark_enabled wird nicht-lazy gelesen wie in Application::addStorageWrapper; nur hinter einem eingeschalteten Schalter liest die Policy getKeys und die übrigen Schlüssel (mit isLazy)"
metrics:
  duration: "ca. 55 min laut Systemzeit (ca. 02:40 bis 03:35 UTC), davon ca. 35 min Docker (RED, GREEN, elf Mutationen, zwei volle Verify-Läufe)"
  completed: 2026-11-23
---

# Phase 45 Plan 22: E3, keine Textausschnitte unter Secure View Summary

Treffer einer Datei, die die suchende Person nur unter dem Wasserzeichen von Nextcloud Office sehen darf, bleiben mit Name und Pfad stehen, ihre Id geht aber nicht an den Snippet-Aufruf (SnippetPolicy nach S3, öffentliche OCP-APIs, fail-closed, auch für Altbestand nach failed(gateway_error) und failed(policy_blocked)).

## Tasks

| Task | Inhalt | Commit |
|---|---|---|
| 1 | Quellenbericht `### E3 Erkennung an der Quelle` (S1 bis S4), Stand am Checkpoint | 5505989d, 95ebb5f3 (Vorgänger) |
| 2 | Owner-Entscheid E3-Weg S3 (mit S1-Auftrag für shareDisabledDownload), CHANGELOG E3 EN/DE/FR, Altbestand A1 in 45-FREIGABEN.md | d57bd962 |
| 3 | SnippetPolicy per TDD, SearchService-Hunks, Gates, S1-Prüfung mit Rückfall im Audit, Baumhash | 143d0bf8 |

## Ergebnisse

- Task 2 verify (Skriptdatei `<scratchpad>/v22_t2.sh`): grün; Gegenprobe ohne Altbestand-Zeile rot.
- RED: pytest `2 failed, 83 passed` (die zwei Real-Tree-Fälle der neuen Gates), PHPUnit gefiltert `Tests: 99, Assertions: 277, Errors: 35` (29 SnippetPolicyTest, 6 neue SearchServiceTest, Klasse fehlt).
- GREEN: verify-Zeile wörtlich aus `<scratchpad>/w22/v22_t3.sh` -> `VERIFY_EXIT=0`: PHPUnit `OK (1382 tests, 8690 assertions)`, Psalm-Taint je 0 Befunde gegen drei ocp-Tags (Probe 3), php-cs 0 (Probe gesehen), zizmor und actionlint grün, pytest sieben Dateien `816 passed`, ruff, ruff format (260), pyright latest 0/0/0, vulture ohne Fund.
- Mutationen (je rot, Dateien danach byte-gleich): M1 nur Argument getauscht (Fall alice und Gate), M1b Filter ganz entfernt (beide Altbestand-Fälle, Fall alice, Fall "kein Aufruf", Gate), M2 fail-open, M3 ohne (b), M4 ohne Schutz vor unbekannten Modi, M5 ohne shareDisabledDownload, M6 Schalter nur bei yes, M7 ohne (a), M8 allTags, M9 allGroups, M10 fehlender Eintrag oder Home-Mount als eigen.
- Baumhash php/: a6c5f8d1/141 -> ff141406/143, Rezept und unabhängige Pipeline gleich; Positivkontrolle über git archive d57bd962 -> a6c5f8d1/141, über 143d0bf8 -> ff141406/143.
- Docker am Ende leer, kein Push, kein Tag, kein Kommentar.

## Deviations from Plan

### Auto-fixed Issues

**1. [Owner-Auftrag, Rückfall] S1 für shareDisabledDownload nicht umsetzbar mit öffentlichen APIs**
- **Found during:** Task 3 (Quellenprüfung vor dem Code)
- **Issue:** Der Koordinator hatte im Owner-Entscheid die genaue Prüfung der Freigabe-Attribute verlangt, mit Rückfall auf S3, falls sie sich nicht sauber belegen oder nur mit öffentlichen APIs bauen lässt. Belegt: richdocuments prüft die Super-Freigabe des Mounts (SecureViewService Z. 53 bis 57, Wrapper::__call, SharedStorage::getShare liefert superShare, MountProvider::buildSuperShares/mergeAttributes). Nicht öffentlich erreichbar: kein OCP-Weg zum Auspacken des Wrappers, ISharedMountPoint liegt im App-Namensraum, ein Nachbau über IManager::getSharedWith müsste die private Gruppierung und Zusammenführung nachbilden (Gefahr der Unterunterdrückung).
- **Fix:** reines S3 unter shareDisabledDownload (jede fremde Datei ohne Ausschnitt, auch Freigabe mit Download und Team Folder), Grund mit Zitaten in 45-AUDIT.md, Tests halten das Verhalten fest.
- **Files modified:** php/lib/Service/SnippetPolicy.php, php/tests/Unit/SnippetPolicyTest.php, 45-AUDIT.md
- **Commit:** 143d0bf8

**2. [Rule 3 - Tooling] Gemischte Zeilenenden nach dem Edit von SearchService.php**
- Die Arbeitskopie stand in CRLF, die neuen Zeilen in LF; vor der Mutationsprobe auf LF vereinheitlicht (Git speichert LF, der Diff zeigt nur die zwei Hunks).

**3. [Rule 1 - Format] php-cs und ruff im ersten Lauf**
- Einrückung einer Docblock-Fortsetzungszeile in SearchServiceTest und zwei Zeilen über 120 Zeichen in den Gate-Selbsttests; behoben, Erwartungen unverändert, zweiter voller Verify-Lauf grün.

Der Task-2-Verify passt zur Kombination ohne Anpassung: die Entscheidzeile endet auf `Entscheid: S3`, die Kombination steht im Hinweis darunter.

## Offene Punkte

- 45-20 Schritt D: echter Beleg; die Gegenkontrolle "Freigabe mit Download zeigt den Ausschnitt" gilt nur, wenn kein Modus für fremde Dateien (shareAll, shareRead, shareDisabledDownload) an ist.
- 45-10: Sichtprüfung DE/EN/FR (Treffer ohne Ausschnitt fällt auf den Pfad zurück).
- CHANGELOG-Zeile E3 ist freigegeben, aber noch nicht in CHANGELOG [1.7.0] eingetragen (der Plan nennt CHANGELOG nicht in files_modified); Ort für den Eintrag festlegen (45-14 oder eigener Schritt).

## Threat Flags

Keine neue Angriffsfläche: keine Route, kein neuer Schreibpfad; die Policy liest nur App-Config, Dateicache, Mount-Cache, Tags und Gruppen der suchenden Person.

## Self-Check: PASSED

- php/lib/Service/SnippetPolicy.php, php/tests/Unit/SnippetPolicyTest.php vorhanden; Commits d57bd962 und 143d0bf8 im Log.
