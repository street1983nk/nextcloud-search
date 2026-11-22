---
phase: 45-findling-1-7-0
plan: 03
subsystem: php-companion (ExternalMountService, SettingsController, AdminViewService, Settings\Admin)
tags: [excl-04, external-storage, files_external, admin-page, rules-route, tdd]
requires: [45-02]
provides:
  - "ExternalMountService::enabled() (isEnabledForAnyone('files_external')) und adminMounts(): list<{id, mountPoint, backend, duplicate}>, nur type = StorageService::ADMIN_MOUNT_TYPE"
  - "ExternalMountService::BACKEND_NAMES (Kennung -> Anzeigename, Texte von stable33), unbekannte Kennung = Kennung selbst"
  - "SettingsController::saveRules(..., mixed $excludedExternalMounts = null): alles oder nichts mit Cap, Präfixen, Mustern; null = unverändert"
  - "AdminViewService::rules()['excludedExternalMounts'] (list<int>), ruleSet() zählt die Speicherauswahl als Regeländerung"
  - "Template-Parameter externalMounts = {enabled, mounts} aus Admin::getForm(), nicht im Initial State, nicht im Poll"
affects: [45-05, 45-06]
tech-stack:
  added: []
  patterns: ["Lese-Service ohne Fremd-App-Klassen, Collator mit strcasecmp-Rückfall, Template-Parameter statt Initial State für Admin-Daten"]
key-files:
  created:
    - php/lib/Service/ExternalMountService.php
    - php/tests/Unit/ExternalMountServiceTest.php
    - php/tests/Unit/AdminSettingsTest.php
  modified:
    - php/lib/Controller/SettingsController.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Settings/Admin.php
    - php/tests/Unit/SettingsControllerTest.php
    - php/tests/Unit/AdminViewServiceTest.php
    - backend/tests/test_measurement_scripts.py
decisions:
  - "BACKEND_NAMES nimmt die setText()-Texte von stable33 (kurz, passen zu den UI-SPEC-Beispielen SMB/CIFS, SFTP, Local); stable34/35 verlängern die meisten Texte, eine Tabelle muss das ganze Fenster 33 bis 35 bedienen"
  - "duplicate vergleicht Einhängepunkt und Anzeigenamen (was der Admin sieht), nicht die rohe Kennung"
  - "Eine Nicht-Liste in excludedExternalMounts wird unter fields.excludedExternalMounts mit out_of_range abgewiesen, nicht unter exclusions"
  - "Vorschau-Route bleibt unverändert; Begründung als Absatz im Docblock von previewRules()"
  - "Fehler beim Lesen der Mountliste in Admin::getForm(): Warnung nur mit ['failed' => 1], Rückfall {enabled: false, mounts: []}"
metrics:
  duration: "ca. 70 min Wanduhr laut Systemzeit (bis 02:19 UTC), größtenteils Docker-Läufe und die PHP-lesenden Python-Tests"
  completed: 2026-11-22
---

# Phase 45 Plan 03: Schreib- und Lesepfad der Speicherauswahl (EXCL-04) Summary

Neuer Lese-Service `ExternalMountService` liefert die Admin-Mounts von files_external (ohne eine einzige files_external-Klasse), `POST /admin/rules` nimmt `excludedExternalMounts` alles-oder-nichts mit den übrigen Feldern an, `rules()` trägt nur die ausgeschlossenen IDs, und die volle Liste geht als Template-Parameter `externalMounts` an die Admin-Seite, nie in Initial State oder Poll.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | ExternalMountService mit Tests | 873c3e9d | ExternalMountService.php, ExternalMountServiceTest.php, test_measurement_scripts.py |
| 2 | Route, rules() und Template-Parameter | 42d3985b | SettingsController.php, AdminViewService.php, Admin.php, SettingsControllerTest.php, AdminViewServiceTest.php, AdminSettingsTest.php, test_measurement_scripts.py |

## BACKEND_NAMES mit Quelle

Geprüft gegen `nextcloud/server`, Branches stable33, stable34, stable35, Datei `apps/files_external/lib/Lib/Backend/<Datei>.php` (`setIdentifier` / `addIdentifierAlias` / `setText`). Übernommen ist jeweils der stable33-Text.

| Kennung | Anzeigename (stable33) | Quelldatei | stable34/35 |
|---|---|---|---|
| amazons3, \OC\Files\Storage\AmazonS3 | S3 Storage | AmazonS3.php | S3-Compatible Object Storage |
| dav, \OC\Files\Storage\DAV | WebDAV | DAV.php | WebDAV |
| ftp, \OC\Files\Storage\FTP | FTP | FTP.php | FTP/FTPS |
| local, \OC\Files\Storage\Local | Local | Local.php | Local (server storage) |
| owncloud, \OC\Files\Storage\OwnCloud | Nextcloud | OwnCloud.php | Nextcloud (WebDAV) |
| sftp, \OC\Files\Storage\SFTP | SFTP | SFTP.php | SFTP (SSH file transfer) |
| \OC\Files\Storage\SFTP_Key | SFTP with secret key login | SFTP_Key.php | SFTP with public key authentication |
| smb, \OC\Files\Storage\SMB | SMB/CIFS | SMB.php | SMB/CIFS (Windows network share) |
| \OC\Files\Storage\SMB_OC | SMB/CIFS using OC login | SMB_OC.php | SMB/CIFS using Nextcloud login |
| swift, \OC\Files\Storage\Swift | OpenStack Object Storage | Swift.php | OpenStack Swift Object Storage |

Die `\OC\...`-Zeilen sind die Legacy-Aliase aus `addIdentifierAlias()` bzw. die beiden Backends ohne kurze Kennung (SFTP_Key, SMB_OC). Die Anzeigenamen sind Englisch und unübersetzt; ob 45-05 sie über den eigenen Katalog übersetzt, entscheidet die UI.

## Umsetzung

- **ExternalMountService:** `enabled()` über `isEnabledForAnyone(self::APP_ID_FILES_EXTERNAL)`; `adminMounts()` ohne aktivierte App ohne Abfrage, sonst eine Abfrage `mount_id, mount_point, storage_backend` aus `external_mounts` mit `type = StorageService::ADMIN_MOUNT_TYPE`, IDs <= 0 übersprungen, Cursor im finally geschlossen; Sortierung `\Collator` der Sprache aus `IFactory::findLanguage()` (Konstruktor gefangen), Rückfall `strcasecmp`, Gleichstand nach ID; `duplicate` bei gleichem Einhängepunkt und Anzeigenamen. DB-Fehler: `[]` plus Warnung `Findling: could not read the external storage set up by an admin` mit `['failed' => 1]`.
- **saveRules:** neuer letzter Parameter `mixed $excludedExternalMounts = null`. Nicht null -> `listOf()`; Nicht-Liste -> `fields = {excludedExternalMounts: out_of_range}`; sonst geht die Liste zusammen mit dem Cap in `settingsService->validate()` und in denselben `settingsService->save()`-Aufruf. Beide Warnzeilen zählen zusätzlich `excludedExternalMounts` (Anzahl). Docblocks von saveRules ("four switches" nachgezogen, sechster Wert) und previewRules (Absatz zur Vorschau-Zahl) ergänzt, Route-Attribute unverändert.
- **ruleSet()** um `excludedExternalMounts` ergänzt; **rules()** liefert `settingsService->excludedExternalMounts()` plus Phpdoc-Shape.
- **Admin::getForm():** `ExternalMountService` injiziert; Template-Parameter `$overview + ['externalMounts' => ...]`, `provideInitialState('bootstrap', $overview)` unverändert; Klassen-Docblock begründet, warum die Liste nicht im Initial State reist.
- **Gate test_admin_ui_contract.py:** blieb grün, keine Änderung nötig.
- **Baumhash PHP-Hälfte:** Task 1 135 Dateien `4d13bae1…`, Task 2 136 Dateien `c0a27412…`; je unabhängige Pipeline (find, sort, sed, sha256sum) gleich, Positivkontrolle über `git archive` des Vorgänger-Commits (b60ee646 -> a7d7a5c7/133, 873c3e9d -> 4d13bae1/135).

## Verifikation

- ExternalMountServiceTest: 8 Tests grün (sechs Fälle aus `<behavior>` plus Zeile ohne positive ID und Tabellenabdeckung). Mutationen: `enabled()`-Prüfung entfernt -> Fall "ohne files_external" rot; Collator aus und `strcmp` statt `strcasecmp` -> Sortierfall rot; `> 1` zu `>= 1` beim Duplikat -> zwei Fälle rot. Datei danach byte-gleich wiederhergestellt (cmp).
- Task 2 Mutationen: ruleSet-Zeile entfernt, Feld nicht an save() gegeben, Liste in den Initial State statt in die Template-Parameter -> 5 Fälle rot (drei AdminSettingsTest, Datenzeile "the external storage kept out", Speichern-und-Antworten); danach wiederhergestellt (cmp).
- Volle PHPUnit-Suite: Task 1 `OK (1255 tests, 7920 assertions)`, Task 2 `OK (1267 tests, 8050 assertions)`.
- `php_gates_docker.sh all` nach beiden Tasks: Psalm-Taint v33.0.9, v34.0.6, v35.0.3 je 0 Befunde (Probe 3), php-cs-fixer 0 Verstöße, zizmor und actionlint ohne Befund.
- Python: ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün; `test_admin_ui_contract.py test_php_trust_boundary.py test_measurement_scripts.py` 807 passed; alle 46 Testdateien, die PHP-Quellen lesen, 2928 passed, 243 skipped (nach jedem Task).
- `git diff v1.6.5 -- php/tests/route-security.json` leer; keine neue Route.
- Keine U+2013/U+2014 und keine Umlaute in den geänderten PHP-Dateien.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Baumhash-Test rot durch neue und geänderte PHP-Dateien**
- **Found during:** Task 1 und Task 2 (vom Plan vorgesehen)
- **Fix:** PHP_FILES_TODAY und PHP_TREE_HASH_TODAY je Task auf dem dokumentierten Weg nachgezogen, mit Kommentar, unabhängiger Pipeline und Positivkontrolle.
- **Commits:** 873c3e9d, 42d3985b

Sonst keine Abweichung. Hinweise:
- Der Plan nannte als Beispiele "Amazon S3" und "FTP"; keine der drei Nextcloud-Versionen setzt "Amazon S3". Übernommen sind die belegten stable33-Texte (Tabelle oben).
- TDD: Tests und Implementierung sind je Task in einem Commit (der Plan sieht je Task einen feat-Commit vor). Den Rot-Beweis liefern die Mutationen oben statt eines eigenen RED-Commits.
- Zusätzliche Testfälle über den Plan hinaus: Zeile mit mount_id <= 0, Tabellenabdeckung von BACKEND_NAMES, Datenprovider mit fünf unbrauchbaren Auswahlwerten (String, Zahl, 0, negativ, numerischer String), Rückfall ohne files_external im Formular.

## TDD Gate Compliance

Kein separater `test(...)`-Commit: Der Plan schreibt je Task genau einen `feat(45-03)`-Commit vor. Die RED-Gegenprobe liegt als Mutationsläufe vor (siehe Verifikation).

## Threat-Abdeckung

- T-45-10: keine neue Route, route-security.json unverändert, Trust-Boundary-Gate grün.
- T-45-11: `listOf()` plus `SettingsService::validate()` (positive int, höchstens 1000), alles oder nichts; Testfälle mit fünf unbrauchbaren Werten schreiben nichts.
- T-45-12: Liste nur als Template-Parameter, `rules()` nur IDs, Logs nur Zähler (AdminSettingsTest prüft Initial State ohne `externalMounts` und ohne Einhängepunkt).
- T-45-13: Service gibt den Rohwert zurück (Testfall mit `<img src=x onerror=alert(1)>`); Escaping über `p()` folgt in 45-05.
- T-45-14: Default null = unverändert, Testfall "ohne Feld".

## Known Stubs

Keine. Template, Script und Kataloge folgen planmäßig in 45-05; bis dahin rendert die Seite den neuen Parameter nicht.

## Self-Check: PASSED

- Dateien vorhanden: ExternalMountService.php, ExternalMountServiceTest.php, AdminSettingsTest.php, SettingsController.php, AdminViewService.php, Admin.php, SettingsControllerTest.php, AdminViewServiceTest.php, test_measurement_scripts.py.
- Commits vorhanden: 873c3e9d, 42d3985b.
