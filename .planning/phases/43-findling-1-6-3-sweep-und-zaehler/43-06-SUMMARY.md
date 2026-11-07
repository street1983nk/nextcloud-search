---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 06
subsystem: php/companion (Admin-Seite, Migration, l10n)
tags: [coverage, issue-25, d-43-06, d-43-11, d-43-12, w10, l10n, migration]
requires:
  - 43-01 (freigegebene Wortlaute in 43-TEXTE.md, Freigabe: ja, Zitat: Go)
  - 43-05 (coverage-Schlüssel counting, perDocument, notReadable, legacyCount, legacyReason)
provides:
  - "SettingsService: KEY_COVERAGE_PER_DOCUMENT_HINT = 'coverage_per_document_hint', COVERAGE_HINT_SECONDS = 7 * 86400, COVERAGE_HINT_PENDING = 1, coveragePerDocumentHintState, setCoveragePerDocumentHintPending, stampCoveragePerDocumentHint, clearCoveragePerDocumentHint, statisch coverageHintVisible"
  - "Migration Version001603Date20261108000000 (postSchemaChange, IDBConnection + IAppConfig, kein Schemaschritt)"
  - "AdminViewService::perDocumentHintNow(kind, now) und coverage-Schlüssel perDocumentHint"
  - "Template/admin.js: findling-coverage-per-document, -counting, -not-readable, -legacy"
affects:
  - 43-07 (PHPUnit im CI, erster Push)
  - 43-08 (Upgrade-Zusicherungen: Migration setzt den Schlüssel nur auf Bestandsinstanzen)
tech-stack:
  added: []
  patterns:
    - "Drei Zustände in einem Int-Schlüssel: 0 aus, 1 wartet, > 1 Zeitstempel"
    - "Tabellenzeile als Signal für Bestandsinstanz statt installed_version (A4)"
key-files:
  created:
    - php/lib/Migration/Version001603Date20261108000000.php
    - php/tests/Unit/Version001603Date20261108000000Test.php
  modified:
    - php/lib/Service/SettingsService.php
    - php/lib/Service/AdminViewService.php
    - php/tests/Unit/SettingsServiceTest.php
    - php/tests/Unit/AdminViewServiceTest.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{json,js}
    - docs/l10n-{french,spanish,italian,dutch,portuguese}.md
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Satz L nur bei legacyReason = limits (43-TEXTE.md Block L, kein L-missing-Satz); missing hat das Lockstep-Banner. Abweichung vom Plantext 'sichtbar bei legacyCount'"
  - "Stempel nur bei kind ok (perDocumentAnswer geprüft, counting false); counting, legacy (missing, limits) und fallback stempeln nie"
  - "Migration: ist der Schlüssel schon != 0, tut sie nichts (idempotent, liest die Tabelle dann nicht); Lesefehler = Warnung ohne Wert, nichts gesetzt"
  - "Uninstall/Purge: PurgeService::deleteApp räumt alle App-Schlüssel, kein Zusatz nötig"
  - "Während counting auch der semantische Satz 'cannot be worked out ... backend does not answer' verborgen (Template und admin.js)"
metrics:
  duration: "ca. 80 min"
  completed: 2026-11-07
  tasks: 2
  files: 31
---

# Phase 43 Plan 06: Hinweis, Zählsatz, nicht lesbare Dateien und Rückfall Summary

Einmaliger Hinweis nach dem Update auf Bestandsinstanzen (AppConfig `coverage_per_document_hint`, gesetzt von der Migration Version001603Date20261108000000, gestempelt bei der ersten vollständigen /coverage-Zählung, nach 7 Tagen auf 0), dazu die Sätze Z (Zählung läuft), U (nicht lesbar, mit Zahl) und L (Rückfall über den Grenzen), zeichengleich mit 43-TEXTE.md in 16 Katalogen und 5 Glossaren.

## Umsetzung

- **SettingsService**: drei Zustände, `stampCoveragePerDocumentHint` schreibt nur von 1 aus (mindestens 2), `clearCoveragePerDocumentHint` nur bei != 0, negative Werte lesen als 0. `coverageHintVisible(state, now)`: 1 sichtbar, > 1 sichtbar solange `now - state < 7 * 86400`.
- **Migration**: `SELECT storage_id FROM findling_scan_stats LIMIT 1`; Zeile da: Schlüssel = 1; keine Zeile oder Lesefehler: nichts. Kommentar mit D-43-06 und A4.
- **AdminViewService::overview()**: `perDocumentHintNow($perDocument['kind'], $now)` direkt nach perDocumentCoverage, Ergebnis als `coverage.perDocumentHint`.
- **Template und admin.js** (gleiche Regeln): H bei perDocumentHint, Z genau bei counting, U bei notReadable > 0 (`%s` mit numbers.format bzw. `$count`), L bei legacyReason limits. Bei counting: `hasFraction` false, recounting- und unknown-Satz verborgen (auch der semantische unknown-Satz). Fingerprint um counting, perDocumentHint, notReadable, legacyReason erweitert.
- **Kataloge**: vier Schlüssel hinter der Unterzeile in allen 16 Dateien; de/de_DE/fr aus den Maschinenzeilen, es/it/nl/pt_BR/pt_PT maschineller Entwurf; Glossare je vier Zeilen plus Nachtrag 07.11.2026 mit Vorbehalt.
- **Vertragstest**: de-Schlüsselzahl 361 auf 365 (der Plan nannte 354 als Stand, tatsächlich 361 seit 41-06) mit Absatz; neuer Test `test_the_per_document_count_shows_its_four_sentences_in_both_halves` (IDs in Template und Skript, Schaltregeln, Fingerprint, EN/DE/FR gegen 43-TEXTE.md); zwei bestehende Zusicherungen an die neuen Schaltregeln angepasst.

## Lokale Checks

- Kein PHP lokal: PHPUnit (SettingsServiceTest +8 inkl. 9 Grenzfälle, AdminViewServiceTest +6 inkl. Datenprovider mit 3 Fällen, Version001603...Test 6) läuft erst im CI von 43-07. `git diff --check` sauber, keine U+2013/U+2014 in den Zusätzen, alle JSON-Kataloge gültig.
- Python: test_admin_ui_contract + test_measurement_scripts 774 passed; PHP-lesende Module (phase34/40/41-Audit, public_artifacts, store_metadata, unified_search_plugin, coverage_counts, php_*, migration_path, exapp_surface, probe_php_parity) 558 passed, 25 skipped. Ein breiter Lauf über 3672 Tests vor Task 2 zeigte 1 Fehler in `test_poller.py::test_two_broken_storages_in_a_row_only_charge_the_rows_at_the_border` unter Last; einzeln und als Modul grün (242 passed), keine Python-Quelle geändert: Timing-Flake, nicht von diesem Plan.
- Gates: ruff check, ruff format --check (253 Dateien), pyright latest 0 errors, vulture leer.
- Baumhash PHP, je zweimal (Rezept 40b-baumhash.py und find | LC_ALL=C sort | tr -d '\r' | sha256sum), Positivkontrolle über git archive HEAD vor dem Schritt:
  - 13819d06: 122 -> 124 Dateien, df3a2adc -> 2423b3a6198fe1b96bc4e4e956ccac857a1d70777a6899ea4ff71739d94b3a44 (Kontrolle df3a2adc; zusätzlich über den gestagten Baum per git write-tree geprüft).
  - 40f92864: 124 Dateien, 2423b3a6 -> 932719613f3b8e87120297365d36e4cad9d2cf04bb40ece08c136539461c29d5 (Kontrolle 2423b3a6; nach dem Commit über HEAD erneut 93271961).
  - PACKAGE-Paar und eingefrorenes PHP_FILES/PHP_TREE_HASH unberührt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Semantischer "backend does not answer"-Satz während der Zählung**
- **Found during:** Task 2
- **Issue:** Bei counting ist embeddedPercent null; der Satz `findling-semantic-unknown` hätte behauptet, das Backend antworte nicht.
- **Fix:** Template `|| $counting`, admin.js `&& coverage.counting !== true`, Vertragstest angepasst.
- **Commit:** 40f92864

**2. Satz L nur bei limits**
- Plan-Text: "sichtbar bei legacyCount". 43-TEXTE.md (freigegeben) sagt "nur bei legacyReason = limits" und kein L-missing-Satz; der freigegebene Text geht vor. Bei missing steht das Lockstep-Banner.

**3. Schlüsselzahl 365 statt "354 + 4"**
- Der Plan ging von 354 aus; seit 41-01 und 41-06 steht sie bei 361.

**4. Form**
- `text()` auch für die statischen Sätze H, Z und L (wie beim Gateway-Satz), damit der Plan-verify (EN-Satz in admin.js) und die Erstanzeige/Aktualisierung gleich bleiben.
- `hasFraction` in Template und admin.js schließt counting selbst aus, statt jede shown-Zeile einzeln.

## Offene Punkte für den CI-Lauf (43-07)

- PHPUnit-Mocks: `IQueryBuilder::from` per Callback (zweites Argument alias wird ignoriert), `IOutput::warning` mit `logicalNot(stringContains(...))`, `ReflectionMethod::getDeclaringClass` für changeSchema (SimpleMigrationStep).
- Upgrade-E2E (43-08): auf der 1.6.2-Saat muss nach `occ upgrade` `coverage_per_document_hint = 1` stehen, auf der Frischinstallation fehlen.

## Threat Flags

Keine neue Oberfläche: die Migration liest nur und schreibt einen AppConfig-Wert (T-43-17 mit Test für Lesefehler); der Hinweistext ist statisch (T-43-18); Wortlaute zeichengleich per Vertragstest gegen 43-TEXTE.md (T-43-19).

## Known Stubs

Keine.

## Self-Check: PASSED

- php/lib/Migration/Version001603Date20261108000000.php und php/tests/Unit/Version001603Date20261108000000Test.php vorhanden; `ls php/lib/Migration | grep -c '^Version0016'` = 2.
- Commits 13819d06 (feat Task 1) und 40f92864 (feat Task 2), Autor street1983nk <k.cherif@outlook.de>, kein Trailer, 0 Treffer für closes/fixes/resolves #N, keine Löschungen. Nichts gepusht.
