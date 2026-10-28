---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 03
subsystem: PHP-Companion / Reconcile
tags: [hart-06, d-36-14, m-32-02, reconcile, storages, ocs-route, phpunit]
requires: [36-02]
provides:
  - "StorageService::classifyAbsent(list<int>): {gone, deselected} über oc_storages und oc_mounts, Bänder zu 200"
  - "GET /ocs/v2.php/apps/findling/storages/gone (ExAppRequired plus rejectForeignCaller, höchstens 256 IDs)"
affects: [36-04]
tech-stack:
  added: []
  patterns:
    - "Abwahl-Erkennung über oc_mounts.mount_provider_class, Mountliste bleibt in providers()"
    - "Provider-Filter in SQL plus zweite Prüfung je Zeile in PHP"
key-files:
  created:
    - php/tests/Unit/StorageServiceTest.php
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-03-SUMMARY.md
  modified:
    - php/lib/Service/StorageService.php
    - php/lib/Controller/ReconcileController.php
    - php/tests/Unit/ReconcileControllerTest.php
    - backend/tests/test_readonly_gate.py
    - backend/tests/test_php_trust_boundary.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "deselected nur, wenn eine oc_mounts-Zeile den abgeschalteten Provider trägt UND isIndexedStorage() false ist; sonst Karenzfall"
  - "selectDistinct(storage_id, mount_provider_class) mit Provider-Filter in SQL, damit ein Team-Ordner mit vielen Mitgliedern eine Zeile bleibt"
  - "Beide Schalter an: oc_mounts wird gar nicht gefragt"
  - "Routen-Untergrenze in test_php_trust_boundary von 16 auf 19 (war hinter dem Ist von 18 zurück)"
metrics:
  duration: "ca. 105 min (davon etwa 40 min lokale Gate-Läufe, drei volle Läufe)"
  completed: 2026-10-20
  tasks: 2
  files: 7
requirements: [HART-06]
---

# Phase 36 Plan 03: Lese-Route für gelöschte und abgewählte Storages Summary

PHP beantwortet dem eigenen Container jetzt, welche seiner nicht mehr gelisteten Storages gelöscht sind (keine Zeile in `oc_storages`) und welche nur ein per Findling-Schalter abgewählter Provider noch trägt (D-36-14). `GET /storages/gone?ids[]=...` nimmt höchstens 256 positive IDs, antwortet nur `findling_backend` und gibt nur die gefragten Zahlen zurück.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | StorageService::classifyAbsent | 1299272f | StorageService.php, StorageServiceTest.php (neu), test_measurement_scripts.py |
| 2 | Route GET /storages/gone, Grenztests, Ratsche, Push | b0429c80, Nachbesserung cd111208 | ReconcileController.php, ReconcileControllerTest.php, test_readonly_gate.py, test_php_trust_boundary.py, test_measurement_scripts.py, StorageServiceTest.php |

## Belege

**Task 1:**
- Lokale Rauchprobe auf php:8.3-cli mit eigenen Stubs und einer Fake-DB, die die IN-Listen selbst auswertet (Scratch, nicht im Repo). Gegen den Stand von `git show HEAD:` bricht sie ab (Konstruktor ohne IDBConnection, keine Methode). Mit dem neuen Code sind alle 7 Prüfungen ok: Fall 1 gibt gone [14, 15] und deselected [9] zurück, bei Schalter an ist deselected [], leere Eingabe macht keine Abfrage, 300 IDs gehen in Bändern 200/100 an storages und 150 an mounts, alle Cursor werden geschlossen, und keine Storage-Kennung steht in der Antwort.
- Gegenprobe: Ohne die Prüfung `isIndexedStorage()` wird Fall 4 rot (244 landet in deselected).
- `getDistinctMounts` kommt vorher und nachher je einmal vor. test_exclusion_path_space.py und test_allowlist_parity.py sind grün (47 passed).

**Task 2:**
- Rauchprobe des Controllers mit Stubs: Gegen den alten Stand bricht sie ab (`undefined method goneStorages`). Mit dem neuen Code sind alle 21 Prüfungen ok: fremder Aufrufer 403 ohne Dienstaufruf, acht Fehlformen 400 ohne Werte im Log, 256 IDs werden angenommen, eine gültige Liste kommt dedupliziert beim Dienst an, eine Ausnahme gibt 500 mit dem statischen Satz, und im Log steht nur der Schlüssel `exception`.
- Gegenprobe: Mit Grenze 1000 statt 256 und `< 0` statt `<= 0` werden genau zwei Fälle rot (257 IDs, "0").
- PHPUnit (nur CI): vorher 837 Tests (Lauf 39439252828, 03a45248), nachher **846 Tests, 3478 Assertions** (Lauf 39456264840, cd111208). Die 9 neuen sind StorageServiceTest 5 (die vier Planfälle plus "Mountliste trägt den Storage noch") und ReconcileControllerTest 4. Rot war vor der Umsetzung nur als Textprüfung belegbar (neue Methode, neuer Konstruktorparameter).
- Baumhash-Ratsche PHP: 9aa79bb7 (106 Dateien) auf d6e456ef (107, 1299272f), dann d809c215 (b0429c80) und c5642f59 (cd111208). Jeder Stand ist doppelt gerechnet: mit 40b-baumhash.py und unabhängig mit find/sort/tr/sha256sum, beide Wege gleich.
- Volle Suite lokal vor jedem der drei Commits: 5927 passed, 264 skipped. ruff, ruff format, pyright, vulture und reuse sind grün.
- CI-Block für cd111208, alle acht Läufe success: Python gates 39456264688, Integration 39456264709, Security scans 39456264677, OpenSSF Scorecard 39456264633, Multi-arch image 39456264814, PHP and store metadata gates 39456264840, Resilience 39456264659, HaRP deploy 39456264694.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Ratsche schon in Task 1 bewegt**
- Nach Plan sollte die Ratsche erst in Task 2 nachgezogen werden. Die Vorgabe "Ratschen im selben Commit wie der Code" und das grüne Gate vor jedem Commit verlangen das aber schon bei Task 1, weil StorageServiceTest.php neu ist (106 auf 107). Darum gibt es drei Journalabsätze.

**2. [Rule 1 - Bug] TestCase::result() ist in PHPUnit 11 final**
- **Found during:** CI-Block nach b0429c80 (Lauf 39449358560 rot, Fatal error, die Suite lief gar nicht an)
- **Fix:** Der Helfer heißt jetzt `resultOf`, die Ratsche ist nachgezogen. `php -l` kann das nicht sehen.
- **Commit:** cd111208

**3. [Rule 1] Routen-Untergrenze im Trust-Boundary-Gate stand veraltet**
- Die Untergrenze lag bei 16, im Quelltext stehen aber schon 18 Routen. Sie steht jetzt auf 19 (18 im Zweig ohne PageController), die Begründung steht im Testkommentar.

**4. Docblock-Nachzug in ReconcileController**
- Der Klassen-Docblock spricht jetzt von drei lesenden Routen. Die Stellen "either route" und "both methods above" (rejectForeignCaller) sind auf alle Routen erweitert, T-36-09 ist ergänzt.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche über das Register hinaus. Die neue Route ist in T-36-09 bis T-36-12 erfasst. Gemindert durch ExAppRequired plus rejectForeignCaller als erste Anweisung (Gate test_php_trust_boundary), die Grenze 256 mit Bändern zu 200, gone nur bei fehlender oc_storages-Zeile, 400 ohne Werte und 500 mit statischem Satz.

## Offen

- `docs/reconcile.md` nennt die neue Route noch nicht. Die Container-Seite und die Doku kommen mit 36-04, dort wird auch die Antwort mit den gefragten IDs geschnitten.
- HART-06 reicht über weitere Pläne und wird hier nicht abgehakt.
- Die Commit-Nachricht von b0429c80 enthält das deutsche Wort "nachgezogen" in einer englischen Aufzählung. Sie ist schon gepusht und bleibt so.

## Self-Check: PASSED
