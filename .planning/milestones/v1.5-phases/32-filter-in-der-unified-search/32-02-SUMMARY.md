---
phase: 32-filter-in-der-unified-search
plan: 02
subsystem: PHP-Companion (SearchFilters, Search\Provider, SearchService, PageController)
tags: [usrch-02, usrch-03, d-32-06, unified-search, folder-filter, acl]
requires:
  - phase: 32
    provides: "32-01: FilterDefinition types, SearchFilters::typesFrom, Leser im Stil von titleOnly()"
provides:
  - "SearchFilters::folder (fünftes Feld, ohne Default, reist nie über das Netz)"
  - "Provider deklariert den Custom Filter folder (TYPE_STRING) und liest ihn in folderOf() still"
  - "SearchService im Ordnermodus: scopeOf() über Folder::get() plus Enthaltenseinsprüfung, scopeCoordinates() aus IFileAccess und Mountliste, Vorauswahl über Koordinaten, Recheck readableFile($scope ?? $userFolder)"
  - "FOLDER_FETCH_LIMIT 100 und FOLDER_MAX_ROUNDS 6 als Konstanten für die Messung in 32-03"
affects: [32-03 Ordnerbudget, 32-04 Plugin, 32-06 Gruppenordner und Share, 32-08 Audit]
tech-stack:
  added: []
  patterns: ["Ordnerumfang als engerer Wurzelpfad des einen Rechecks; Vorauswahl nur verwerfend"]
key-files:
  created: []
  modified:
    - php/lib/Service/SearchFilters.php
    - php/lib/Search/Provider.php
    - php/lib/Service/SearchService.php
    - php/lib/Controller/PageController.php
    - php/tests/Unit/SearchFiltersTest.php
    - php/tests/Unit/ProviderTest.php
    - php/tests/Unit/SearchServiceTest.php
    - php/tests/Unit/ExAppServiceTest.php
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Rundenzahl und Abrufgröße des Ordnermodus hängen beide an vorhandenen Koordinaten; ohne Koordinaten (Ordnereintrag oder Mountliste fehlt) gelten Rundenzahl der Caps und M4-Formel, der Recheck läuft trotzdem im Unterbaum"
  - "Fehlt die Mountliste, gibt es keine Koordinaten: die Vorauswahl könnte sonst Shares unterhalb des Ordners verwerfen"
  - "Logzeilen des Ordnerwegs ohne Kontext und ohne das Wort folder; die Ausnahme eines Cache-Lookups wird nicht mitgeloggt, ihre Meldung könnte einen Pfad tragen"
  - "Ordner gleich Nutzerordner selbst (Pfad ohne abschließenden Slash) zählt als kein Ordner"
metrics:
  duration: "ca. 120 min inkl. ca. 25 min Volltestläufe und ca. 45 min CI"
  completed: 2026-10-13
  tasks: 2
  files: 9
---

# Phase 32 Plan 02: Ordnerfilter in PHP Summary

Der Findling-Provider deklariert den Custom Filter `folder` (string) und liest ihn still in `folderOf()`; `SearchService` löst den Ordner im Baum des fragenden Nutzers über `Folder::get()` auf, prüft das Enthaltensein im Nutzerordner, verwirft Kandidaten außerhalb billig über Koordinaten (Storage plus Rohpfad) und fragt den einen Recheck auf dem Ordnerknoten. Jeder Fehler beim Ordner ergibt die ungefilterte Suche. Der Ordnerwert verlässt PHP nie.

## Commits

- `39e8eca9` test: the status comparison holds the hardware reading still (Vorab-Auftrag, Flake aus 32-01)
- `53daf104` feat(32-02): the unified search narrows findling hits to a folder in PHP (Task 1 und 2 in einem Commit, wie im Plan vorgegeben)
- Beide gepusht auf origin/main.

## Vorab: Flake in test_main_lifespan

- Ursache belegt: jeder Start liest die Hardware einmal (`findling.main.detect`), `memory_available_bytes` bewegt sich zwischen zwei Starts.
- Fix: der Test setzt `findling.main.detect` auf die feste Lesung `_A_READING`; der Vergleich bleibt vollständig (alle Felder, Hardware eingeschlossen), Zusicherung unverändert.
- Gegenprobe mit einer temporären Testdatei (nicht committet), die `detect` zwei Lesungen nacheinander liefern lässt: gleiche Lesung grün, nur `memory_available_bytes` verschieden rot (der Flake-Mechanismus), andere Kernzahl rot.
- deferred-items.md und STATE.md als erledigt markiert (im selben Commit).

## Task 1: SearchFilters::folder, FilterDefinition folder, folderOf(), Body ohne folder

- `SearchFilters`: fünfter Konstruktorparameter `public readonly ?string $folder` ohne Default, `none()` setzt null, `hasAny()` zählt einen Ordner.
- `Provider`: `FILTER_FOLDER = 'folder'`, `MAX_FOLDER_LENGTH = 4000` (Breite von oc_filecache.path), sechs Namen in `getSupportedFilters()`, zwei Definitionen in `getCustomFilters()`, `folderOf()` nach Pattern 2 (Nicht-String, Überlänge, Steuerzeichen, Wurzel ergeben null). Tür trägt nie `folder`.
- `PageController` übergibt `null` (Ergebnisseite ohne Ordnerfilter).
- Konstruktionsstellen (Sichtprüfung, jede mit fünf Argumenten): PageController.php:526, Provider.php:270, ExAppServiceTest.php:681, SearchServiceTest.php:989 und :1221, SearchFiltersTest.php:111.
- `ExAppService.php` unverändert; `grep -n "'folder'" php/lib/Service/ExAppService.php` leer.

## Task 2: SearchService im Ordnermodus

- `mountsOfUser()` (ein `getMountsForUser` je Lauf, null bei Fehler) plus `storageIdsOf()` ersetzen `storageIdsOfUser()`; dieselbe Liste speist die Koordinaten.
- `scopeOf()`: `Folder::get()` in try, `instanceof Folder`, Pfad muss mit `$userFolder->getPath() . '/'` beginnen; keine `isReadable`-Frage, Log ohne Kontext.
- `scopeCoordinates()`: `IFileAccess::getByFileId($scope->getId())` als erste Koordinate, dazu jede Mount mit Mountpunkt unter dem Ordner (`getStorageId()`, `getRootInternalPath()`); Signaturen gegen nextcloud/server stable34 geprüft (`Folder::get` über `getFullPath` mit `Filesystem::isValidPath`).
- `reduceIds()` mit optionalen Koordinaten: Treffer bei gleicher Storage und `root === ''`, `path === root` oder `str_starts_with(path, root . '/')`; Reduktion, nie Grenze.
- Recheck `self::readableFile($scope ?? $userFolder, ...)`, Anzeigepfad weiter relativ zum Nutzerordner.
- Budget: mit Koordinaten `FOLDER_FETCH_LIMIT = 100` je Runde und `max($caps->maxRounds, FOLDER_MAX_ROUNDS = 6)` Runden, sonst unverändert M4; `MAX_CONTAINER_OFFSET` greift weiter.
- Baumhash im selben Commit: `PHP_FILES_TODAY` bleibt 93, `PHP_TREE_HASH_TODAY` 3b906d4a9ead107332df127a5c16330334071bed876de92af0231d582ab34a29, Journalabsatz "Plan 32-02".

### PHP-Fälle (25 neu)

- SearchFiltersTest (3): none() ohne Ordner, Ordner zählt in hasAny(), fünf Pflichtparameter per Reflection.
- ProviderTest (9 Läufe): vier Werte in kanonischer Form (Datenanbieter), zwölf Werte ohne Ordner ergeben `SearchFilters::none()`, Längengrenze genau 4000, Ordner plus Datum, Ordner plus Typ, Tür ohne folder; zwei bestehende Fälle auf sechs Namen bzw. zwei Definitionen erweitert.
- ExAppServiceTest (3): Body an /search und /snippets ohne `folder` und byte-gleich zum Body mit `folder = null`; Ordner allein lässt den ungefilterten Body unverändert.
- SearchServiceTest (10): Regression ohne Ordner (gleiche IDs an den Nutzerordner, `get()` nie, `getByFileId` nie), Vorauswahl (21, 25, 26 ohne Recheck verworfen, 22/23/24 im Recheck bei Budget genau 3), Recheck ist Grenze, werfendes `getByFileIds`, werfendes `getByFileId` (M4-Limit, Recheck im Unterbaum), sieben Fail-open-Fälle (NotFound, NotPermitted, TypeError, Datei, fremder Baum, Geschwisterbaum mit gleichem Präfix, Nutzerordner selbst; gleiche IDs und gleiche Limits wie ohne Ordner, kein Log mit dem Wert, kein Exception-Kontext), sechs Runden zu 100, Offset-Decke im Ordnermodus, M4-Formel ohne Ordner (60, 57, 54), doppelte Sichtbarkeit.

### PHP-Rot (TDD-Nachweis)

Lokal kein PHPUnit; wie in 32-01 über Textprüfung plus grünen CI-Lauf: die neuen Fälle rufen `Provider::FILTER_FOLDER`, `MAX_FOLDER_LENGTH`, den fünften Konstruktorparameter, `Folder::get()` des Nutzerordners und den Recheck auf dem Ordnerknoten, die es vor dem Commit nicht gab (Aufruf unbekannter Konstanten bzw. ArgumentCountError, `get()` nie gerufen und damit leere Recheck-Listen). PHPUnit-Zahl stieg von 620 (Lauf 38309357692, 32-01) auf 645 (Lauf 38316403027), genau die 25 neuen Fälle. Lokal per Docker-Image php:8.3-cli `php -l` über alle acht PHP-Dateien sauber, Steuerzeichen-Regex und `'/' . trim('//', '/')` geprüft.

## Gates und CI

- Lokal aus backend/ mit PYTHONUTF8=1 (vor beiden Commits): `pytest` 5586 passed, 30 skipped; `ruff check`, `ruff format --check` grün; `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` 0 Fehler; `vulture src tests --min-confidence 80` ohne Befund. `test_php_acl_boundary.py` ohne Änderung an der Datei grün (`git diff HEAD --quiet` belegt).
- CI auf 53daf104, jeweils `gh run watch <id> --exit-status` mit Exitcode 0:
  - php.yml 38316403027: grün (PHPUnit OK, 645 Tests, 2359 Assertions).
  - python.yml 38316403112: grün (inklusive des Flake-Fixes 39e8eca9).
  - integration.yml 38316403070: grün (search-parity und team-folder-acl im Lauf).
  - deploy-harp.yml 38316403120: grün.
  - Außerdem grün: Resilience 38316403058, Security scans 38316403095, Multi-arch image 38316403115, OpenSSF Scorecard 38316403111.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Correctness] Keine Koordinaten ohne Mountliste**
- **Found during:** Task 2
- **Issue:** Ohne Mountliste hätte die erste Koordinate (der Ordner selbst) allein Shares unterhalb des Ordners in der Vorauswahl verworfen.
- **Fix:** `mountsOfUser()` liefert null bei Fehler, dann gibt es keine Koordinaten; der Recheck im Unterbaum entscheidet allein.
- **Files modified:** php/lib/Service/SearchService.php
- **Commit:** 53daf104

**2. [Rule 2 - Security, T-32-10] Kein Exception-Kontext im Ordnerweg**
- **Found during:** Task 2
- **Issue:** Die Meldung einer Ausnahme aus `getByFileId` oder `Folder::get()` kann einen Pfad tragen.
- **Fix:** beide Logzeilen ohne Kontext; Testfall prüft, dass keine Zeile `exception` im Kontext oder den Ordnerwert trägt.
- **Commit:** 53daf104

### Präzisierung eines Akzeptanzkriteriums

- `grep -n "logger->.*folder\|logger->.*getPath" php/lib/Service/SearchService.php` ist nicht leer, sondern trifft genau die bestehende Zeile `'Findling: no home folder for this user, dropping every hit'` (seit Phase 9, Wortlaut in `testTheMissingHomeFolderIsLoggedWithoutNamingAnythingTheUserSearchedFor` festgeschrieben, Kontext nur `exception` des fehlenden Nutzerordners, kein Ordnerwert). Die neuen Logzeilen vermeiden das Wort, damit der Grep nur diese Altzeile zeigt; der Zweck des Kriteriums (kein Ordnerpfad im Log) ist erfüllt und zusätzlich per Testfall belegt.

## Threat Flags

Keine neue Fläche außerhalb des Threat Models. T-32-05 (Folder::get plus Enthaltenseinsprüfung, Testfälle fremder Baum und Geschwisterbaum), T-32-06 (gleiche Antwort für jeden Auflösungsfehler, Log ohne Kontext), T-32-07 (werfendes getByFileIds), T-32-08 (Body byte-gleich ohne folder), T-32-09 (Frist und Offset-Decke, Messung in 32-03), T-32-10 (kein Pfad im Log) sind umgesetzt.

## Hinweise für Folgepläne

- 32-03 misst FOLDER_FETCH_LIMIT und FOLDER_MAX_ROUNDS (Annahme A2).
- 32-06 belegt Annahme A1 (Rohpfadraum von IFileAccess und getRootInternalPath bei Gruppenordner und Share).
- Der Files-Provider des Kerns hat eigene Filter `type`/`mime` und einen `path`-Präfixfilter; Findling nutzt `types` und `folder`.

## Self-Check: PASSED

- Commits 39e8eca9 und 53daf104 in `git log` und auf origin/main.
- Akzeptanz-Greps: `new FilterDefinition(` in Provider.php 2; `'folder'` in ExAppService.php leer; `public readonly ?string $folder` vorhanden; `FILTER_FOLDER` vorhanden; `readableFile($scope ?? $userFolder` vorhanden; `FOLDER_FETCH_LIMIT = 100` und `FOLDER_MAX_ROUNDS = 6` vorhanden; Ratchet-Test unverändert und grün.
