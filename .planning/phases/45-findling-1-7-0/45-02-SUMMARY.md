---
phase: 45-findling-1-7-0
plan: 02
subsystem: php-companion (SettingsService, StorageService)
tags: [excl-04, external-storage, files_external, mount-list, tdd]
requires: []
provides:
  - "SettingsService::KEY_EXCLUDED_EXTERNAL_MOUNTS ('excluded_external_mounts'), FIELD_EXCLUDED_EXTERNAL_MOUNTS ('excludedExternalMounts'), MAX_EXCLUDED_EXTERNAL_MOUNTS (1000)"
  - "SettingsService::excludedExternalMounts(): list<int>, defensiv gelesen, pro Request gecacht"
  - "SettingsService::validate()/save() mit excludedExternalMounts (null oder fehlend = unverändert)"
  - "StorageService::ADMIN_MOUNT_TYPE = 1 (public, für 45-03)"
  - "StorageService::excludedStorageIds() (privat), Filter in getMounts(), Erweiterung von deselected()"
  - "Struktur-Gate test_the_mount_list_drops_the_storages_of_excluded_admin_mounts mit Positivkontrollen"
affects: [45-03, 45-05, 45-06]
tech-stack:
  added: []
  patterns: ["Opt-out-Liste in appconfig, gebänderte Lesefragen mit Zeilenprüfung, Zähler statt Werte im Log"]
key-files:
  created: []
  modified:
    - php/lib/Service/SettingsService.php
    - php/lib/Service/StorageService.php
    - php/tests/Unit/SettingsServiceTest.php
    - php/tests/Unit/StorageServiceTest.php
    - backend/tests/test_exclusion_path_space.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "ADMIN_MOUNT_TYPE = 1 geprüft gegen nextcloud/server stable33, stable34, stable35: apps/files_external/lib/Service/DBConfigService.php :34 (MOUNT_TYPE_ADMIN = 1, :35 MOUNT_TYPE_PERSONAL = 2); oc_mounts.mount_id = Konfigurations-ID über ConfigAdapter storageConfigToMount (stable33 :197, stable34 :193, stable35 :194, $storageConfig->getId())"
  - "Ein Storage fällt nur heraus, wenn ALLE seine oc_mounts-Zeilen vom files_external-Provider mit einer ausgeschlossenen Admin-Mount-ID stammen; jede andere Zeile (anderer Provider, andere mount_id, NULL) hält ihn im Index"
  - "Leere Liste oder Schalter aus: excludedStorageIds() stellt keine einzige Abfrage"
  - "save(): leere Liste [] leert die Ausschlüsse, null/fehlend lässt sie stehen"
metrics:
  duration: "ca. 20 min Wanduhr laut Systemzeit (01:09 bis 01:28 UTC), davon der größte Teil Docker-Läufe"
  completed: 2026-11-22
---

# Phase 45 Plan 02: Ausschluss einzelner externer Admin-Speicher serverseitig (EXCL-04) Summary

Neuer appconfig-Schlüssel `excluded_external_mounts` (Opt-out-Liste von files_external-Konfigurations-IDs); `StorageService::getMounts()` nimmt die Storages ausgeschlossener Admin-Mounts hinter dem unveränderten einen `getDistinctMounts($this->providers(), true)`-Aufruf heraus, und `classifyAbsent()` meldet sie als `deselected`, also Entfernen ohne Gnadenfrist. Python unverändert.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | RED, PHPUnit-Fälle für Liste, Filter und Abwahl | fa288361 | SettingsServiceTest.php, StorageServiceTest.php |
| 2 | GREEN, Schlüssel, Filter und Abwahl, Struktur-Gate | 5445be3c | SettingsService.php, StorageService.php, test_exclusion_path_space.py, test_measurement_scripts.py |

## Umsetzung

- **SettingsService:** `excludedExternalMounts()` liest wie `ExclusionService::prefixes()`: `AppConfigTypeConflictException` gefangen (leere Liste, Warnung `unusable 1, inForce 0`), nur `is_int && > 0`, dedupliziert, sortiert, pro Request gecacht, Cache in `save()` geleert. `validate()`: Feld vorhanden und nicht null muss `array_is_list` mit positiven int und höchstens 1000 Einträgen sein (keine numerischen Strings, Floats, Bools, Maps), sonst `excludedExternalMounts => out_of_range` über `reject()`; alles oder nichts. `save()` schreibt die sortierte, deduplizierte Liste per `setValueArray` vor `markScanStale()`. Klassen-Docblock auf fünf Regeln nachgezogen.
- **StorageService:** `excludedStorageIds()` mit drei gebänderten Fragen (ABSENT_LOOKUP_BAND): (1) `external_mounts` `mount_id IN … AND type = ADMIN_MOUNT_TYPE`, (2) `mounts` `mount_id IN … AND mount_provider_class = EXTERNAL_STORAGE_MOUNT_PROVIDER` -> Kandidaten, (3) `mounts` `storage_id IN Kandidaten` -> Kandidat fällt heraus bei fremdem Provider, fremder oder NULL-mount_id. Jede Zeile wird nach dem Dialekt nochmals geprüft, jeder Cursor im finally geschlossen, keine Logzeile. `deselected()`: frühes Return nur noch ohne abgeschaltete Provider UND ohne ausgeschlossene Storages; beide Mengen durchlaufen `!isIndexedStorage()`.
- **Gate (B8):** `scan_excluded_mounts()` prüft getMounts (ruft Mount-Query und `excludedStorageIds()`), deselected (ruft `excludedStorageIds()`), excludedStorageIds (nennt `ADMIN_MOUNT_TYPE` und `EXTERNAL_STORAGE_MOUNT_PROVIDER` in Code, nicht in Kommentaren). Clean-Sample plus vier Fehl-Samples (Filter fehlt, Abwahl fehlt, Typ fehlt und Literal statt Konstante, Methode weg) sind rot wie erwartet.
- **Baumhash PHP-Hälfte:** 133 Dateien, `a7d7a5c7…`; unabhängige Pipeline (find, sort, sed, sha256sum) gab `a7d7a5c7` ebenso; Rezept über `git archive a65ba841` (letzter Commit vor dem Plan) gab `033cb708` (Positivkontrolle).

## Verifikation

- RED (Task 1): `phpunit_docker.sh --filter 'StorageServiceTest|SettingsServiceTest'` Exit 2, `Tests: 112, Errors: 7, Failures: 14`; alle 21 roten Fälle sind neue Fälle, alle vorher vorhandenen Methoden grün. Vier neue Fälle waren schon in RED grün, weil sie Wirkungslosigkeit festhalten (Storage mit zweitem, nicht ausgeschlossenem Mount; persönlicher Mount; gelöschter Mount; leere Liste ohne Abfrage); sie sind Regressionswächter, ihr Rot-Beweis ist die Mutation unten.
- Mutation (Positivkontrolle der Abfrage 3): `unset($candidates[...])` auskommentiert -> genau `testAStorageThatAnIncludedMountAlsoCarriesStays` rot; Datei danach wiederhergestellt (0 Treffer für die Markierung).
- GREEN: gefiltert 112 Tests OK; volle Suite `OK (1247 tests, 7877 assertions)`, Floor erfüllt.
- `php_gates_docker.sh all`: Psalm-Taint v33.0.9, v34.0.6, v35.0.3 je 0 Befunde (Probe 3), php-cs-fixer 0 Verstöße, zizmor und actionlint ohne Befund.
- `getDistinctMounts(` kommt in StorageService.php genau einmal vor.
- Python: `pytest tests/test_exclusion_path_space.py tests/test_measurement_scripts.py` 616 passed; alle 45 Testdateien, die PHP-Quellen lesen, 2873 passed, 243 skipped; ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün.
- Log-Review `grep -n "logger->" php/lib/Service/StorageService.php php/lib/Service/SettingsService.php`: neu sind nur SettingsService.php:619 (`['unusable' => 1, 'inForce' => 0]`) und :641 (`['unusable' => $unusable, 'inForce' => count($ids)]`), beide nur Zähler; in StorageService keine neue Logzeile (bestehend :999 Zähler und Klassenname, :1501 Zähler). Keine Mount-IDs, Storage-ID-Listen oder Mountpunkte.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Baumhash-Test rot durch die geänderten PHP-Dateien**
- **Found during:** Task 2 (wie im Plan vorgesehen)
- **Fix:** PHP_TREE_HASH_TODAY auf dem dokumentierten Weg nachgezogen, mit Kommentar, unabhängiger Pipeline und Positivkontrolle.
- **Commit:** 5445be3c

Sonst keine Abweichung. Zusätzlich zum Plan: ein Bandtest (250 IDs -> external_mounts 200/50, mounts 200/50, zweiter getMounts()-Aufruf ohne neue Abfrage) für T-45-06, und ein Datenprovider mit neun unbrauchbaren Feldwerten für validate().

## Threat-Abdeckung

T-45-05 (Lesen defensiv, Tests), T-45-06 (Obergrenze 1000, Bänder, Cache), T-45-07 (nur Zähler, `assertNoLogCarries(['404'])` und leere Logliste), T-45-08 (nur `type = 1`, Abfrage 3), T-45-09 (`!isIndexedStorage()`, Testfall Storage mit zweitem Mount): alle mitigiert.

## Known Stubs

Keine. Route (45-03) und UI (45-05) folgen planmäßig; bis dahin schreibt nur occ die Liste.

## Self-Check: PASSED

- Dateien vorhanden: SettingsService.php, StorageService.php, SettingsServiceTest.php, StorageServiceTest.php, test_exclusion_path_space.py, test_measurement_scripts.py.
- Commits vorhanden: fa288361, 5445be3c.
