---
phase: 40-haertung-und-store-einreichung-1-6-0
plan: 02
subsystem: release
tags: [version, migration, changelog, lockstep, ci-gate]
requires:
  - 40-01 (auditierter, grüner Kopf, scripts/ci/head_green.sh)
provides:
  - Version 1.6.0 in beiden Apps (zwei info.xml, image-tag)
  - php/lib/Migration/Version001600Date20261028000000.php mit Test
  - CHANGELOG [1.6.0] - 2026-10-28
affects:
  - 40-03 (Starttag UPGRADE_FROM_TAG v1.4.3 -> v1.5.0, Baum ist jetzt neuer als jeder Starttag)
  - 40-05 (Tag-Link-Prüfung blob/v1.6.0 nach dem Tag)
tech-stack:
  added: []
  patterns:
    - "Minor-Migration nur mit IAppConfig, wenn keine Nachzählung nötig ist"
key-files:
  created:
    - php/lib/Migration/Version001600Date20261028000000.php
    - php/tests/Unit/Version001600Date20261028000000Test.php
  modified:
    - backend/appinfo/info.xml
    - php/appinfo/info.xml
    - CHANGELOG.md
    - docs/store-listing.md
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Kein markScanStale() in 001600: ScanStatsService::totals() gruppiert beim Lesen (php/lib/Service/ScanStatsService.php:432 `$totals['grouped'] = self::summed($rows, $leftOut['ids']);`), die gespeicherten Zähler bleiben gültig"
  - "CHANGELOG Security nennt nur filelock 4.2.4 (CVE-2026-112907/112913/112940, belegt im PR #34); fastapi, pypdf, striprtf stehen unter Changed: Dependencies"
metrics:
  duration: ca. 75 min inkl. ca. 40 min CI
  completed: 2026-10-28
  tasks: 2
  files: 7
---

# Phase 40 Plan 02: Version 1.6.0 und Minor-Migration Summary

Beide Apps stehen auf 1.6.0 (zwei `<version>`, ein `<image-tag>`), die
Minor-Migration Version001600Date20261028000000 verwirft `backend_app_version`
wie ihre Vorgänger, der CHANGELOG hat `[1.6.0] - 2026-10-28`, die sechs
Doku-Links der Beschreibungen zeigen auf `blob/v1.6.0`; alle acht Workflows auf
dem gepushten Kopf 631763b5 grün, Store upgrade 4 belegt den Sprung 1.4.3 auf
1.6.0.

## Commits

| Commit | Inhalt |
|---|---|
| 6a057133 | test(40-02): minor migration 1.6 drops the recorded backend version (RED, PHP-Baumhash d3ab4f7d, 109 Dateien) |
| bcdc4777 | feat(40-02): minor migration for 1.6.0 (PHP-Baumhash 73bae603, 110 Dateien) |
| 631763b5 | chore(40-02): version 1.6.0 in both apps |

## Verifikation

- `head_green.sh 631763b5 "Python gates" "PHP and store metadata gates" "HaRP
  deploy" "Integration" "Resilience" "Multi-arch image" "Security scans"`:
  Exit 0. Läufe: Python gates 40750963014, PHP and store metadata gates
  40750963023, HaRP deploy 40750963299, Integration 40750963000, Resilience
  40750963030, Multi-arch image 40750963547, Security scans 40750963004,
  OpenSSF Scorecard 40750962997, alle success.
- HaRP deploy 40750963299, Job stable34 amd64 (ubuntu-24.04), Schritt "Store
  upgrade 4, the upgrade itself, in two halves", wörtlich:
  - `the companion of this commit carries version 1.6.0`
  - `installed_version went from 1.4.3 to 1.6.0`
- PHPUnit (PHP and store metadata gates 40750963023): `OK (895 tests, 3949
  assertions)`, darin der neue Migrationstest; `php -l` meldet "No syntax
  errors detected in php/lib/Migration/Version001600Date20261028000000.php".
  Die Migration liegt im Store-Archiv aller drei Beine (Schritt "Store install
  1 content proof").
- RED des Tests nur in CI sichtbar (lokal kein PHP); der Test wurde ohne
  eigenen CI-Lauf zusammen mit der Migration gepusht.
- Lokal: `-k tree_hash` grün nach beiden PHP-Commits (Hash je zweimal
  gerechnet, Rezept und find/sort/tr/sha256sum); test_store_metadata,
  test_lockstep_versions, test_migration_path, test_measurement_scripts,
  test_phase36_audit, test_phase40_audit, test_admin_ui_contract: 1008 passed,
  7 skipped; ruff, ruff format, pyright (latest), vulture sauber.
- Konsistenz-grep: `blob/v1.6.0` außerhalb der erlaubten Dateien leer;
  `blob/v1.5.1` nur noch im historischen Abschnitt von docs/store-listing.md;
  `blob/v1.5.0` nur in php/templates/admin.php (unverändert), den bekannten
  Teststellen und historischen Abschnitten von docs/store-listing.md.

## Deviations from Plan

### Abweichungen im Vorgehen

- **Lokale Volltestsuite nicht durchgelaufen:** der Lauf mit den sechs
  `--ignore` wurde vom System wegen Speichermangel beendet (nicht vom Test
  verursacht) und gemäß Hinweis nicht neu gestartet. Ersatz: die betroffenen
  Testdateien lokal (siehe oben), die Volltestsuite lief grün in Python gates
  40750963014.
- **Kein Baumhash in Task 2:** das Rezept liest nur `*.php` bzw. `*.py`;
  php/appinfo/info.xml und backend/appinfo verschieben weder PHP- noch
  Paket-Baumhash (Präzedenz Plan 31-14). Der Plan hatte einen Journalabsatz
  für info.xml vorgesehen.
- **Test-Fälle:** die vier behavior-Fälle stehen in fünf Methoden (zusätzlich
  "nur IAppConfig im Konstruktor" als Beleg für "asks the container for
  nothing").
- **CHANGELOG Fixed:** WR-36-01 (XML-Element "amplification" nicht mehr als
  bösartig blockiert) aufgenommen, IN-01 bis IN-05 nicht, weil nicht
  nutzersichtbar.

## Known Stubs

Keine.

## Threat Flags

Keine. T-40-07 (Migration verwirft den Stand), T-40-08 (Zitat 1.4.3 -> 1.6.0
im Zweig verschiedener Versionen) und T-40-09 (zweiter Lauf No-op, Test)
sind belegt.

## Self-Check: PASSED

- Dateien vorhanden: Version001600Date20261028000000.php, ihr Test,
  40-02-SUMMARY.md.
- Commits vorhanden auf origin/main: 6a057133, bcdc4777, 631763b5.
