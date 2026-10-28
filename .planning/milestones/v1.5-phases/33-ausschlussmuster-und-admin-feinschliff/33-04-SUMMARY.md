---
phase: 33-ausschlussmuster-und-admin-feinschliff
plan: 04
subsystem: exclusions, background-jobs, reconcile
tags: [exclusions, patterns, sweep, verdicts, weg-a, weg-c, gate-d, phpunit, tdd]
requires:
  - "33-02: ExclusionService mit patterns(), savePatterns(), newPatterns(), hasRules(), isExcluded() über beide Listen"
  - "33-03: Weg C im Abgleich, describe() macht aus der Abholung unter Regel einen Löschauftrag"
provides:
  - "ExclusionSweepJob (Weg A für Muster): Bänder über alle Mounts, Cursor, Wanduhr, Nachfolger, Fingerabdruck des Mustersatzes"
  - "ExclusionService::patternFingerprint() und Planung aus savePatterns() bei jeder Änderung des Satzes"
  - "FileStateService::forgetVerdicts(): löscht jede Urteilszeile der Dateien, no_text_layer eingeschlossen"
  - "forgetVerdicts an vier Räumstellen: Kehrjob, SubtreeExpandJob (kind delete), describe() unter Regel, Abgleichs-Slice"
affects: [33-05, 33-09, 33-11]
tech-stack:
  added: []
  patterns:
    - "Job-Argument mit Fingerabdruck (SHA-256 über sortierte, normalisierte Musterliste); veralteter Lauf endet ohne Nachfolger"
    - "Gate D: Kehrjob als fünfte Aufrufstelle, isExcluded nur direkt verschachtelt mit mountRelativePath"
    - "Uninstall-Gate liest die Jobklassen aus php/lib/BackgroundJobs statt aus einer festen Liste"
key-files:
  created:
    - php/lib/BackgroundJobs/ExclusionSweepJob.php
    - php/tests/Unit/ExclusionSweepJobTest.php
    - php/tests/Unit/SubtreeExpandJobTest.php
  modified:
    - php/lib/BackgroundJobs/SubtreeExpandJob.php
    - php/lib/Controller/ReconcileController.php
    - php/lib/Service/ExclusionService.php
    - php/lib/Service/FileStateService.php
    - php/lib/Service/PurgeService.php
    - php/lib/Service/QueueService.php
    - php/tests/Unit/QueueServiceReaderTest.php
    - php/tests/Unit/ReconcileControllerTest.php
    - backend/tests/test_exclusion_path_space.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_uninstall_contract.py
decisions:
  - "33-04: Weg-C-Urteile räumt das Abgleichs-Slice (ReconcileController), nicht das Crawlband: kein Gate verbietet den Schreibzugriff, die Route läuft über die normale Verbindung, die Antwort bleibt unverändert"
  - "33-04: Das Sweep-Argument trägt neben Storage und Cursor auch die überschriebene Wurzel (root), weil mehrere Mounts eine Storage teilen (Team Folders)"
  - "33-04: Der Scan wird in savePatterns() nicht als veraltet markiert; das tut SettingsService::save() in derselben Formular-Anfrage schon"
  - "33-04: ExclusionSweepJob steht in PurgeService::JOBS (Regel 2), sonst bliebe nach der Deinstallation ein Jobeintrag ohne Klasse"
requirements-completed: []
metrics:
  duration: "ca. 75 min inkl. ca. 14 min Volltestlauf und ca. 30 min CI"
  completed: 2026-10-14
  tasks: 3
  files: 14
---

# Phase 33 Plan 04: Kehrjob für Muster und Urteilsbereinigung in allen Räumwegen Summary

Ein neuer `ExclusionSweepJob` räumt nach jeder Änderung der Musterliste alle bereits indexierten Dateien unter einer Regel aus dem Index (eine Löschzeile je Datei) und löscht ihre Urteilszeilen; ein Fingerabdruck des Mustersatzes im Jobargument lässt veraltete Läufe ohne Nachfolger enden. Dieselbe Urteilsbereinigung (`forgetVerdicts`, auch `no_text_layer`) läuft jetzt im Präfix-Räumen (`SubtreeExpandJob` mit kind delete, Owner-Wort G4), in `describe()` unter Regel und im Abgleichs-Slice für Zeilen mit Marke `skipped(excluded)`.

EXCL-02 und EXCL-03 bleiben laut Plan offen bis 33-11 (Live-Beleg in 33-09, Abnahme in 33-10).

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | ExclusionSweepJob mit Fingerabdruck und forgetVerdicts, geplant von savePatterns | 14d6b591 | ExclusionSweepJob.php, FileStateService.php, ExclusionService.php, ExclusionSweepJobTest.php |
| 2 | Urteilsbereinigung im Präfix-Räumen, Gate D mit fünfter Aufrufstelle | 14d6b591 | SubtreeExpandJob.php, SubtreeExpandJobTest.php, test_exclusion_path_space.py |
| 3 | Urteilsbereinigung auf Weg C (describe und Slice), Hash, Commit, CI | 14d6b591 | QueueService.php, ReconcileController.php, QueueServiceReaderTest.php, ReconcileControllerTest.php, test_measurement_scripts.py |

Task 1 bis 3 laufen laut Plan in einem Commit. Zusätzlich (Regel 2): PurgeService.php und test_uninstall_contract.py.

## Kehrjob

- Argument `{storage, root, cursor, fingerprint}`; `ExclusionSweepJob::startArgument()` ist die eine Stelle für die Form, `savePatterns()` und der Nachfolger nutzen sie.
- Erster Schritt jedes Laufs: `hash_equals(patternFingerprint(), fingerprint)`, sonst Ende ohne Nachfolger. Danach `hasRules()`, sonst Ende.
- Mounts aus `getMounts()`, sortiert nach Storage-ID und überschriebener Wurzel; je Lauf höchstens `BATCH_SIZE` (1000) Dateien über alle Mounts, Wanduhr 30 s (Prüfung vor jeder Datei), Nachfolger nach 5 s an der Stelle, an der der Lauf stand. Mount erschöpft (weniger als erbeten): weiter mit dem nächsten Mount im selben Lauf.
- Je Treffer `isExcluded($this->exclusionService->mountRelativePath($entry->getPath(), $mountRoot))`; Treffer je Transaktionsband (250): `enqueueFile(..., 0, true, KIND_DELETE)` und `forgetVerdicts($ids)` in einer Transaktion.
- Log: eine Zeile am Ende eines Laufs mit `storage`, `cursor`, `seen`, `cleared`; die Fingerabdruck-Zeile mit `storage`, `cursor`. Kein Pfad, kein Muster, kein Fingerabdruck.
- `savePatterns()`: Fingerabdruck vorher und nachher; bei Abweichung `remove(ExclusionSweepJob::class)` und, wenn der neue Satz nicht leer ist, genau ein `add` mit Startcursor. Unveränderter Satz (andere Reihenfolge, andere Schreibweise derselben Normalform) und Fehlerfall: nichts.

## Entscheidung Slice oder Crawl (PE-9)

Gewählt: **Slice** (`ReconcileController::forgetExcludedVerdicts()`), der Vorrang des Plans. Belege:

- Kein Gate verbietet Schreibzugriffe in der Route: `test_readonly_gate.py` beurteilt nur schreibende HTTP-Aufrufe des Containers (`test_a_reading_route_needs_no_allowlist_entry_and_gets_none`), `test_php_trust_boundary.py` nur Attribute und Fremdaufrufer-Abwehr, `test_reconcile.py` nur `verdictsFor`, `withVerdicts` und die zwei Codes. `grep` über backend/tests nach ReconcileController ergab keine Schreibsperre.
- Die Route läuft über `FileStateService` mit der normalen `IDBConnection`, keine nur lesende Verbindung.
- Die Allowlist (`ExclusionService` Docblock, vier Einträge laut `test_write_allowlist_has_exactly_four_entries`) betrifft Container-Routen, die Index-Inhalt löschen; hier löscht PHP Zeilen der eigenen Tabelle `findling_file_state`.
- Die Antwort des Slice ändert sich nicht (eine ausgeschlossene Zeile trägt `skipped(excluded)` unabhängig vom gespeicherten Urteil), der GET bleibt für den Aufrufer idempotent. IDs nur aus der gelesenen Seite und aus `isExcluded()` (T-33-38).
- Ein Fehler beim Löschen wird geloggt (nur `exception`) und beendet das Slice nicht.

Der Klassen-Docblock ("Nothing here writes") nennt die eine Ausnahme. `StorageCrawlJob.php` und `StorageCrawlJobTest.php` bleiben unverändert und sind aus files_modified gestrichen.

## Belege

**Gate D (Task 2):** Erst die Probe `scan_sweep` und `test_the_sweep_asks_the_helper_on_the_one_path_space` geschrieben, dazu die Datei in `test_the_four_files_of_the_exclusion_exist` und den Kehrjob in der hasRules-Menge (`test_exactly_the_known_call_sites_ask_has_rules`): **3 rot** (Datei fehlt), Selbsttests grün (sauberes Beispiel still; ohne Aufruf, mit selbst gebautem Pfad `$mountRoot . '/' . $entry->getPath()` und mit `fnmatch` je genau ein Befund). Nach dem Anlegen des Jobs 38 grün.

**Uninstall-Gate (Regel 2):** `test_every_background_job_of_the_app_is_removed_by_the_purge` liest die Klassen aus `php/lib/BackgroundJobs`: rot (ExclusionSweepJob fehlt in PurgeService), nach dem Nachtrag 16 grün.

**Lokale Rauchprobe (unabhängig von PHPUnit):** Scratch-Skript mit eigenen Stubs auf php:8.3-cli, echter Job und echter `ExclusionService`: Treffer genau 101 und 201, Urteile genau 101 und 201, kein Nachfolger, Logschlüssel nur Zähler, veralteter Fingerabdruck räumt nichts, Planung bei Hinzufügen, Entfernen, gleichem Satz in anderer Schreibweise und leerem Satz wie verlangt (15 OK). Gegenprobe: alter Stand von `ExclusionService.php` per `git show HEAD:` eingesetzt, Rauchprobe bricht mit "undefined method patternFingerprint" ab; eigene Kopie zurück, `cmp` gleich.

**PHPUnit (nur CI):** Rot war vor dem Commit nur als Textprüfung belegbar (neue Klasse, neue Methode `forgetVerdicts`, neuer Konstruktorparameter). Vorher 743 Tests (Lauf 38450953800, 75f5f29e), nachher **766 Tests, 2769 Assertions** (Lauf 38506312552, 14d6b591). +23: ExclusionSweepJobTest 14 (zwei Treffer, Kontrolle und `.keynote`, voller Band mit Nachfolger und Ende, Wanduhr, Fingerabdruck passt nicht und passt, Fingerabdruck-Definition per Hand gerechnet, ohne Regeln, Logprobe, Planung: erstes Muster, nur entfernt ersetzt den Lauf (N3), leerer Satz entfernt nur, unveränderter Satz, Fehlerfall), SubtreeExpandJobTest 3 (delete vergisst genau das Band; content und acl nie), QueueServiceReaderTest 2 (Abholung unter Regel löscht die `skipped(no_text_layer)`-Zeile über einen echten FileStateService auf einer Tabellen-Attrappe, Kontrollzeile bleibt; Gegenfall ohne Regel ruft `forgetVerdicts` nie), ReconcileControllerTest 4 (Urteil der ausgeschlossenen Zeile weg, Kontrolle behält ihres, Antwort und `final` unverändert; ohne gespeichertes Urteil kein Schreibzugriff; ohne Regel nichts; Fehler beim Löschen beendet das Slice nicht).

Die Tabellen-Attrappe versteht nur `eq`, `neq` und `in` und wertet sie aus; ein `forgetVerdicts` mit Zustandsfilter wie `revokeFailures` hätte die `no_text_layer`-Zeile stehen lassen und den Fall rot gemacht.

**Archivprobe (Task 2):** `bash scripts/release/store-archive.sh stage-companion <scratch>/stage-3304`, danach `find`: `findling/lib/BackgroundJobs/ExclusionSweepJob.php` und `findling/lib/BackgroundJobs/SubtreeExpandJob.php` liegen im Archiv, keine Tests.

**Baumhash:** `PHP_TREE_HASH_TODAY` von `2fb90d37...` auf `da53dd886c8642ea31259ff51d665abf3521ff012ce92c992d2ba60f1e590d71`, `PHP_FILES_TODAY` 99 auf 102 (ExclusionSweepJob.php, ExclusionSweepJobTest.php, SubtreeExpandJobTest.php), Journalabsatz "Moved on 2026-10-14 by Plan 33-04".

**Gates lokal (backend/, PYTHONUTF8=1):** pytest 5666 passed, 159 skipped (13:29 min); ruff check grün; ruff format --check 222 Dateien; pyright 0 errors (latest); vulture leer; reuse lint konform. PHPL-Block vor und nach dem Commit grün (`php -l` je geänderter PHP-Datei).

## CI (14d6b591)

Alle mit `gh run watch <id> --exit-status` bis zum Ende beobachtet, alle grün:

- PHP and store metadata gates 38506312552 (PHPUnit 766, php -l, info.xml)
- Python gates 38506312589
- Security scans 38506312593
- OpenSSF Scorecard 38506312591
- Resilience 38506312602
- Multi-arch image 38506312553
- Integration 38506312565
- HaRP deploy 38506312563 (zweiter Watch-Aufruf, der erste lief in die lokale Zeitgrenze)

Erste Liste leer, zweiter Aufruf mit 8 Läufen, dritter Aufruf gleich.

## Deviations from Plan

### Auto-fixed Issues

**1. [Regel 2 - Fehlende kritische Funktion] ExclusionSweepJob in PurgeService::JOBS**
- **Gefunden in:** Task 1
- **Problem:** `PurgeService::JOBS` nennt die Jobs fest; ohne Nachtrag bliebe nach `occ findling:purge` bzw. der Deinstallation ein ExclusionSweepJob-Eintrag ohne Klasse in der Jobliste, und jeder Cron-Lauf scheiterte daran. Das Uninstall-Gate (`JOB_CLASSES`) hätte es nicht bemerkt.
- **Fix:** Job in `PurgeService::JOBS` (Docblock "five"), neues Gate `test_every_background_job_of_the_app_is_removed_by_the_purge`, das die Klassen aus dem Verzeichnis liest.
- **Dateien:** php/lib/Service/PurgeService.php, backend/tests/test_uninstall_contract.py
- **Commit:** 14d6b591

### Weitere Abweichungen

1. **Argument mit `root`:** Der Plan nennt `{storage, cursor, fingerprint}`. Eine Storage trägt mehrere Mounts (alle Team Folders liegen auf einer Storage), der Cursor ist eine Datei-ID innerhalb eines Mounts; ohne die überschriebene Wurzel wäre die Position nicht eindeutig. Das Argument ist `{storage, root, cursor, fingerprint}`.
2. **BATCH_SIZE 1000 über Mounts hinweg statt 250 je Lauf und Mount:** Ein Lauf liest weiter in den nächsten Mount, wenn einer erschöpft ist, bis 1000 Dateien oder 30 s erreicht sind. Mit einem Band je Mount und Lauf bräuchte eine Instanz mit vielen kleinen Homes je Home einen Cron-Lauf. Die Planfälle (voller Band plant Nachfolger, leerer Rest endet, Wanduhr) gelten unverändert.
3. **hasRules-Menge erweitert:** `test_exactly_the_three_known_call_sites_ask_has_rules` heißt jetzt `test_exactly_the_known_call_sites_ask_has_rules` und kennt den Kehrjob als vierte Stelle, weil der Plan "ohne Regeln endet der Job sofort" verlangt.
4. **Keine SPDX-Köpfe in den neuen PHP-Dateien:** wie in 33-02, die Nachbardateien tragen keinen, die Lizenz kommt aus `REUSE.toml`; `reuse lint` konform.
5. **Scan-Markierung:** Nicht in `savePatterns()` eingebaut; `SettingsController::saveRules` ruft vorher `SettingsService::save()`, das `markScanStale()` für das ganze Formular setzt (eine Stelle, im Docblock vermerkt). 33-05 verdrahtet `savePatterns()` in dieselbe Route.
6. **Gegenproben ohne `git stash`:** alter Stand per `git show HEAD:` eingesetzt, danach eigene Kopie zurück und `cmp`.

## Known Stubs

Keine. `savePatterns()` wird erst ab 33-05 von der Formular-Route gerufen; bis dahin plant nur ein direkter Aufruf den Kehrjob (laut Plan so geschnitten).

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: write-under-get | php/lib/Controller/ReconcileController.php | Die GET-Route des Slice löscht Urteilszeilen der eigenen Tabelle für Zeilen der gelesenen Seite mit Marke excluded (T-33-38, im Plan vorgesehen, Antwort unverändert, nur IDs aus isExcluded) |

T-33-13 (Bänder, Wanduhr, Transaktionsbänder, Nachfolger nach 5 s), T-33-14 (Logprobe im Test und in der Rauchprobe), T-33-15 (Entscheidung nur über `isExcluded(mountRelativePath(...))`, Gate D, Gegenprobe `.keynote`, Fingerabdruck), T-33-16 (`forgetVerdicts` an allen vier Räumstellen, Kontrolldateien behalten ihre Zeile) umgesetzt.

## Self-Check: PASSED

- FOUND: php/lib/BackgroundJobs/ExclusionSweepJob.php, php/tests/Unit/ExclusionSweepJobTest.php, php/tests/Unit/SubtreeExpandJobTest.php
- FOUND: 14d6b591
