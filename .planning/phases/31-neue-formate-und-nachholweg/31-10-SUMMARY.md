---
phase: 31-neue-formate-und-nachholweg
plan: 10
subsystem: Extraktion (extract/dispatch.py), Suche (query/rewrite.py), PHP-Companion (StorageService, StorageCrawlJob, Migration)
tags: [fmt-01, fmt-02, fmt-03, fmt-04, fmt-05, d-31-05, pitfall-3, allowlist, migration]
requires:
  - phase: 31-04
    provides: "mail.extract_eml"
  - phase: 31-05
    provides: "legacy_doc.extract_msword"
  - phase: 31-06
    provides: "legacy_xls.extract_msexcel"
  - phase: 31-07
    provides: "pillow-heif im Bildpfad (image.extract_image)"
  - phase: 31-08
    provides: "archive.extract_zip"
  - phase: 31-09
    provides: "Auszug eines ZIP-Treffers nennt die innere Datei"
provides:
  - "Beide Allowlists mit message/rfc822, application/zip, application/msword, application/vnd.ms-excel, image/heic, image/heif (24 Typen je Seite)"
  - "Routen MAIL, ZIP, DOC, XLS; HEIC/HEIF auf Route.OCR über IMAGE_MIMETYPES"
  - "Gemeinsamer Begründungsabsatz an beiden Listen, vom Paritätstest verglichen"
  - "OCR_CERTAIN_MIMETYPES zählt HEIC/HEIF"
  - "TYPE_GROUPS: doc/dot, xls/xlt, heic/heif; zip in keiner Gruppe (D-31-05), Grenze in docs/search-filters.md"
  - "Minor-Migration Version001500Date20261012000000 (backend_app_version verwerfen, markScanStale)"
affects: [31-11 Nachholweg, 31-12 Upgrade-CI-Beweis, 31-14 docs/formats.md, 31-15 Audit, 36 Versionssprung 1.5.0]
tech-stack:
  added: []
  patterns:
    - "Gemeinsamer Absatz neben zwei Listen, per Test aus Kommentar und Docblock gelesen und verglichen"
    - "Migration ruft SettingsService (final, nicht mockbar) echt auf gemocktem IAppConfig"
key-files:
  created:
    - php/lib/Migration/Version001500Date20261012000000.php
    - php/tests/Unit/Version001500Date20261012000000Test.php
  modified:
    - backend/src/findling/extract/dispatch.py
    - backend/src/findling/query/rewrite.py
    - php/lib/Service/StorageService.php
    - php/lib/BackgroundJobs/StorageCrawlJob.php
    - php/tests/Unit/StorageCrawlJobTest.php
    - backend/tests/test_allowlist_parity.py
    - backend/tests/test_extract_documents.py
    - backend/tests/test_extract_errors.py
    - backend/tests/test_extract_edge_paths.py
    - backend/tests/test_image_heic.py
    - backend/tests/test_query_rewrite.py
    - backend/tests/test_measurement_scripts.py
    - docs/search-filters.md
decisions:
  - "Ein Commit für beide Allowlists (Pitfall 3), Typgruppen und Migration"
  - "Begründungsabsatz wörtlich gleich an beiden Listen; der Paritätstest liest ihn ab 'Since 1.5 (plan 31-10) the allowlist reads' bis zur ersten Zeile ohne Kommentarwort"
  - "zip in keiner Typgruppe (D-31-05); 'alle sechs Gruppen' findet daher weniger als 'keine Gruppe', als Grenze dokumentiert"
  - "Migration markiert den Nenner immer als veraltet, auch ohne aufgezeichnete Version (frische Instanz kann unter alter Liste gezählt haben)"
  - "Neue Typgruppen-Endungen am Ende der Tupel angehängt, Reihenfolge der bisherigen bleibt"
metrics:
  duration: "ca. 150 min, davon ca. 70 min CI-Wartezeit"
  completed: 2026-10-12
  tasks: 2
  files: 15
---

# Phase 31 Plan 10: Freischaltung der fünf Formate Summary

Mails (.eml), ZIP-Dateien, Word und Excel 97 bis 2003 (.doc/.xls) sowie HEIC/HEIF-Fotos stehen jetzt in beiden Allowlists, und zwar im selben Commit (a14c03c3, Pitfall 3). Der Container leitet jeden Typ auf seinen Leser (Routen MAIL, ZIP, DOC, XLS, HEIC/HEIF über Route.OCR), die Companion reiht die Typen ein und zählt HEIC/HEIF als OCR-Kandidaten. Die Typgruppen kennen doc/dot, xls/xlt und heic/heif. zip steht in keiner Gruppe (D-31-05), das ist in docs/search-filters.md als Grenze beschrieben. Die Minor-Migration 1.5 verwirft `backend_app_version` und markiert den Nenner der Abdeckung als veraltet.

## Umsetzung

- `extract/dispatch.py`: `Route.MAIL/ZIP/DOC/XLS`, `IMAGE_MIMETYPES` + `image/heic`, `image/heif`, `ALLOWED_MIMETYPES` + vier Dokumenttypen (24 Typen). `_run_format_of_1_5` importiert den jeweiligen Leser lazy im Zweig, also nach dem bestehenden Muster: `mail.extract_eml`, `archive.extract_zip`, `legacy_doc.extract_msword`, `legacy_xls.extract_msexcel`. Der Modul-Docstring ist angepasst (ZIP, Altformate Word/Excel, HEIC), der alte Absatz "HEIC, BMP and GIF stay out" ist weg.
- Gemeinsamer Absatz "Since 1.5 (plan 31-10) the allowlist reads ..." steht wortgleich vor `ALLOWED_MIMETYPES` in dispatch.py und im Docblock von `StorageService::ALLOWED_MIMETYPES`. Er beschreibt, was 1.5 liest und was draußen bleibt (BMP/GIF, PowerPoint-Altformat, 7z/rar/tar/gz, .msg).
- `StorageService.php`: sechs Typen in der Konstante. `StorageCrawlJob.php`: `OCR_CERTAIN_MIMETYPES` + HEIC/HEIF.
- `query/rewrite.py`: TYPE_GROUPS ergänzt, mit Kommentar zu D-31-05. `docs/search-filters.md`: Tabelle, Zahl 18 auf 24, Abschnitt "The limits" mit dritter Grenze "A ZIP file belongs to no group".
- `Version001500Date20261012000000`: zuerst `SettingsService::markScanStale()`, dann wird `backend_app_version` verworfen, wenn vorhanden. Bei einem zweiten Lauf passiert nichts. Die Migration ruft den Container nicht auf. Der Klassenkommentar verweist auf 31-11 (Nachholweg im Container, unabhängig von der Migration).
- Baumhash im selben Commit: `PACKAGE_TREE_HASH_TODAY` abba4c46... (78 Dateien), `PHP_TREE_HASH_TODAY` bad993f8... und `PHP_FILES_TODAY` 90 auf 92, Journalabsätze "Plan 31-10".

## RED

Nach dem Anlegen der Route-Member (ohne Allowlist): **20 failed, 196 passed**. Darunter:
- Parität: sechs Bildtypen, Formate 1.5, Absatz, alter HEIC-Satz (`assert 'HEIC, BMP and GIF stay out' not in ...`)
- `test_a_format_of_1_5_is_judged_onto_its_own_route` x4 und `..._indexed_through_judge_with_its_word` x4
- `test_a_heic_is_judged_onto_the_picture_branch` x2
- `test_an_allowed_mimetype_yields_its_route` x6 (`KeyError: 'message/rfc822'`, `Extra items ... 'image/heic'`)

Vorher kam ein Sammelfehler `AttributeError: Route has no attribute 'MAIL'`.

test_query_rewrite.py vor der Änderung an TYPE_GROUPS: **6 failed**. Betroffen: Gruppen von 1.5, documents/spreadsheets/images je ein Fund, alle sechs Gruppen ohne zip, Erweiterungstupel von documents.

Schon vorher grün und daher per Gegenprobe belegt: `test_zip_stands_in_no_group`, `test_no_group_finds_a_zip_file`, `test_without_a_group_the_zip_file_is_found`, `test_what_1_5_leaves_out_*`, `test_a_format_of_1_5_is_indexed_in_the_extraction_child` (nachgereicht in 2a5ad6a5).

PHP (StorageCrawlJobTest HEIC-Fall, Migrationstest) läuft nur in CI. Lokal geprüft: `php -l` im Container php:8.3-cli und dass beide Zusicherungen im Test stehen (deleteKey, setValueInt mit KEY_SCAN_STALE_SINCE). Der Beleg ist CI-Lauf 38223115697: OK (598 tests), vorher 589 (Lauf 38216336217). +9 = acht Migrationsfälle und ein Crawl-Fall.

## Gegenproben

Bei jeder Probe genau ein Eingriff, Datei danach aus der Sicherung zurück, `cmp` gleich:

| Probe | Eingriff | Ergebnis |
|---|---|---|
| G1 | Zweig `Route.MAIL/ZIP/DOC/XLS` in `_run_route` entfernt | 4 rot |
| G2 | ZIP-Route ruft den Mail-Leser | 2 rot |
| G3 | `image/heic` aus der PHP-Liste entfernt | 3 rot |
| G4 | ein Wort im PHP-Absatz geändert | 1 rot (Absatzvergleich) |
| G5 | HEIC/HEIF nicht in IMAGE_MIMETYPES | 7 rot |
| G6 | `zip` unter documents | 5 rot |
| G7 | heic/heif nicht unter images | 3 rot |
| G8 | wie G1, nur der Kind-Test | 3 von 4 rot (die .eml läuft dann über den RTF-Leser und enthält ihr Wort trotzdem; G1 und der Allowlist-Gang decken das ab) |

## Gates und CI

- Lokal vor a14c03c3: ruff check (backend und ../scripts), ruff format (233 Dateien), pyright latest 0 Fehler, vulture grün. Volle Suite mit `-x` komplett durchgelaufen, 5344 Tests gesammelt, kein Fehler. Plan-Prüfbefehl grün.
- Push `61d34030..a14c03c3`, alle acht Läufe success:
  - Python gates **38223115485** (5327 passed, 17 skipped)
  - PHP and store metadata gates **38223115697** (598 PHPUnit-Tests, php -l der Migration)
  - Integration **38223115628**
  - HaRP deploy **38223115654** (Store upgrade 0 bis 7 success im Upgrade-Job)
  - Resilience 38223115549, Multi-arch image 38223115496, Security scans 38223115550, Scorecard 38223115600
- Push `a14c03c3..2a5ad6a5` (nur Test):
  - success: Python gates **38226547734** (5331 passed, 17 skipped), Integration 38226547735, Multi-arch 38226547747, Security 38226547723, Scorecard 38226547721
  - HaRP deploy 38226547724 und Resilience 38226547746 wurden **cancelled**, weil die Dependabot-Merges #28/#29 auf main neue Läufe ausgelöst haben (Concurrency), nicht wegen eines Fehlers.
- Auf dem danach gemeinsamen Stand 5cba95fc (enthält a14c03c3 und 2a5ad6a5 plus #28/#29) alle acht success: Python gates **38227673787** (5331 passed), PHP 38227673842, Integration 38227673793, HaRP deploy **38227673884**, Resilience 38227673807, Multi-arch 38227673849, Security 38227673836, Scorecard 38227673797. Lokal nach `git rebase origin/main` und `uv sync --frozen` (pypdfium2 5.14.0): Plan-Tests 759 passed, 3 skipped.

## Commits

| Commit | Inhalt |
|---|---|
| a14c03c3 | feat(31-10): mail, ZIP, .doc, .xls and HEIC enter both allowlists |
| 2a5ad6a5 | test(31-10): the four document formats of 1.5 are indexed in the extraction child |

## Deviations from Plan

**1. [Rule 1] Bestehende Tests, die die alte Grenze festschrieben, angepasst.**
- test_extract_errors.py: zip/msword/vnd.ms-excel/heic aus der Liste "deliberately not supported" genommen, x-7z-compressed ergänzt.
- test_extract_edge_paths.py: Zeilen zip-called-docx und legacy-office-called-txt auf 7z bzw. PowerPoint umgestellt.
- test_extract_documents.py: aus "old office mimetypes stay outside" wurde "PowerPoint stays outside".
- `test_the_text_syntax_and_the_group_parameter_are_united` erwartet jetzt das Tupel mit doc/dot.

**2. HEIC-Routentest in test_image_heic.py statt in test_extract_documents.py.** Dort stehen schon der HEIC-Erzeuger und der Stand-in der Engine. Damit läuft der Fall auf jedem Rechner. Der Fall mit echter Engine ist `needs_engine` und wird lokal übersprungen.

**3. Absatzvergleich als neuer Test.** Der bisherige Paritätstest verglich nur die Listen. `test_the_paragraph_next_to_both_lists_is_the_same` liest den Absatz aus Python-Kommentar und PHP-Docblock und vergleicht sie.

**4. Zusätzlicher Test im Extraktionskind (2a5ad6a5).** Dient als Beleg für FMT-01 bis FMT-04, dass der Leser auch im echten Kind des Pollers (extract_guarded) geladen wird und indexiert. Er ist ein eigener Commit nach dem Freischalt-Commit.

**5. Migrationsreihenfolge.** markScanStale läuft vor dem Versionszweig und auch dann, wenn keine Version aufgezeichnet ist. Grund: Eine frische Instanz kann ihren Nenner schon unter der alten Liste gezählt haben.

**6. Wortwahl in docs/search-filters.md.** Dort steht "ZIP file" statt des gesperrten Wortstamms (wie in 31-02/31-09).

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche außerhalb des Plans. Umgesetzt:
- T-31-31: ein Commit, Parität von Liste und Absatz, G3 und G4
- T-31-33: Migration mit markScanStale, Test in CI
- T-31-32: Mischfenster, die Aufnahme folgt in 31-11 Teil A (Container-Seite)

## Requirements

**FMT-01 bis FMT-05 Complete.** Beleg für die Durchsuchbarkeit auf einer Instanz mit diesem Stand:
- (a) Beide Allowlists enthalten die Typen. Paritätstest grün in Python gates 38223115485, und die Companion filtert Crawl, Listener und Abgleich über genau diese Konstante.
- (b) Jeder Typ kommt über judge auf seinen Leser und wird mit seinem Suchwort indexiert, auch im echten Extraktionskind (postquendel, zipquendel, wortquendel, zellquendel; HEIC mit Stand-in der Engine, OCR des HEIC im Image seit 31-07, Lauf 38125992894).
- (c) Die Endungen eml/zip/doc/dot/xls/xlt/heic/heif entsprechen der Nextcloud-Zuordnung (31-RESEARCH, mimetypemapping.dist.json).
- (d) Der Typfilter findet .doc/.xls/.heic in ihren Gruppen, ZIP nur ohne Filter.

Einschränkung, offen genannt: Ein Upload-bis-Treffer-Beweis auf einer echten Nextcloud mit diesen Typen fehlt noch. Er kommt mit der Saat in 31-12/31-13. Ältere Bestandsdateien werden erst mit FMT-06 (31-11) nachgeholt. FMT-06 bleibt offen.

## Offene Punkte

- 31-11: Teil A muss nicht indexierte Zeilen mit den sechs neuen Mimetypen aufnehmen (Pitfall 3, Mischfenster mit 1.4.2-Container).
- 31-12/31-13: Saat und Live-Beweis der neuen Typen in deploy-harp.
- Die Migration wirkt erst beim Versionssprung auf 1.5.0 (Phase 36). In der CI-Strecke bleibt die Version 1.4.2 (Gleichstandszweig).

## Self-Check: PASSED

Migration und Test vorhanden; a14c03c3 und 2a5ad6a5 auf origin/main; alle CI-Läufe auf 5cba95fc success. STATE.md, ROADMAP.md und REQUIREMENTS.md von Hand nachgezogen (10/15, nächster Plan 31-11; FMT-01 bis FMT-05 Complete, FMT-06 offen).
