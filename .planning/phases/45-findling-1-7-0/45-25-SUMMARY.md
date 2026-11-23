---
phase: 45-findling-1-7-0
plan: 25
subsystem: php-companion-admin-page
tags: [issue-25, locking, i-45-23-03, i-45-23-04, i-45-19-01, admin-page, l10n, tdd]
requires: [45-24]
provides: [Freigabezeilen Text 5 und Platzhalter 45-25, LockingCheckService (APCu und ArrayCache als memcache.locking), Überblicksschlüssel lockingUnshared, Hinweis findling-banner-locking in 18 Katalogen, Doku "Dateisperren und Hintergrundjobs (ab 1.7.0)", Platzhalter des Ordnerfelds der Regeln aus dem Katalog, Schlüsselzahl 386, Baumhash PHP 05797073/143 -> 8eae94a1/145 -> d75974c9/145]
affects: [45-26, 45-20, 45-21, 45-10, 45-15, 45-16]
tech-stack:
  added: []
  patterns: [Dienst hinter einem Banner nach dem Muster von ParallelSearchService, Systemwert über IConfig nur gelesen, Banner nur auf dem Server gerendert, Prüfer mit Katalogen als Argument für Fehl-Samples]
key-files:
  created:
    - php/lib/Service/LockingCheckService.php
    - php/tests/Unit/LockingCheckServiceTest.php
    - .planning/phases/45-findling-1-7-0/45-25-SUMMARY.md
  modified:
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/tests/Unit/AdminSettingsTest.php
    - php/tests/Unit/SettingsControllerTest.php
    - php/l10n/*.js, php/l10n/*.json (18 Dateien)
    - docs/l10n-chinese.md, docs/l10n-dutch.md, docs/l10n-french.md, docs/l10n-italian.md, docs/l10n-portuguese.md, docs/l10n-spanish.md
    - docs/admin-page.md
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - .planning/phases/45-findling-1-7-0/45-AUDIT.md
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
decisions:
  - "Freigabe Text 5 45-25 und Freigabe Platzhalter 45-25: Owner 'Ok' 2026-11-23 02:08 UTC, vom Koordinator im Chat als Freigabe von Text 5 und der Platzhalter Backups/Sicherungen/Sauvegardes benannt, ohne Widerspruch"
  - "Locking l1 umgesetzt: Hinweis nur für APCu und ArrayCache (strcasecmp nach ltrim), Noop ohne eigenen Hinweis mit Verweis auf die Einrichtungsprüfung Transactional File Locking, Grenze NullCache bei Klasse nur in einer SAPI im Docblock und in der Doku"
  - "Ort des Hinweises: Hinweisleiste des Blocks Deckungsgrad direkt nach findling-banner-parallel, kein besser passender Statusbereich"
  - "Platzhalter Ordnerfeld aus dem Katalog, Musterfeld behält *.photoslibrary (stays untranslated), Übersetzungen es/it/nl/pt_BR/pt_PT/zh_TW maschinell"
metrics:
  duration: "ca. 50 min laut Systemzeit (ca. 06:55 bis 07:45 UTC), davon ca. 25 min Docker (PHP RED, GREEN, vier Mutationen, drei volle Verify-Läufe)"
  completed: 2026-11-23
---

# Phase 45 Plan 25: Dateisperren, die Hintergrundjobs nicht trennen, und das Beispiel der Regelfelder Summary

Die Admin-Seite zeigt einen Hinweis, wenn `memcache.locking` APCu oder ArrayCache ist (Cron und Nachschub-Route sehen ihre Locks dann nicht, eine Scheibe kann doppelt laufen); ausgeschaltete Dateisperren bleiben bei der Einrichtungsprüfung von Nextcloud. Das Ordnerfeld der Regeln zeigt sein Beispiel in der Sprache der Seite, das Musterfeld bleibt bei `*.photoslibrary`.

## Tasks

| Task | Inhalt | Commit |
|---|---|---|
| 0 | Freigabezeilen `Freigabe Text 5 45-25` und `Freigabe Platzhalter 45-25` mit Wortlautzeilen und je einer Hinweiszeile | 504cd787 |
| 1 | LockingCheckService, lockingUnshared im Überblick, Banner findling-banner-locking, Text 5 in 18 Katalogen und sechs Sprachtabellen, Schlüsselzahl 385, Doku-Abschnitt, M19/M20/M25/M26, Baumhash | 39b2b436 |
| 2 | Platzhalter des Ordnerfelds über `$l->t('Backups')`, Schlüssel in 18 Katalogen und sechs Sprachtabellen, Kommentar `stays untranslated` am Musterfeld, Schlüsselzahl 386, M27/M28, Baumhash | a6a71478 |

## Ergebnisse

- Task 1: RED PHPUnit gefiltert `Tests: 108, Assertions: 89, Errors: 86.` (Klasse fehlt), pytest Contract `2 failed, 227 passed`; GREEN `OK (108 tests, 935 assertions)`, pytest `398 passed`. Verify wörtlich (`<scratchpad>/v25_t1.sh`, byte-gleich mit dem Plan) -> `VERIFY_EXIT=0`: PHPUnit voll `OK (1416 tests, 8870 assertions)`, Psalm-Taint 0 gegen v33.0.9/v34.0.6/v35.0.3, php-cs-fixer, zizmor, actionlint grün, ruff, ruff format (260), pyright 0/0/0, vulture, pytest `970 passed`.
- Task 2: RED `1 failed, 229 deselected`; GREEN pytest `399 passed`. Verify wörtlich (`<scratchpad>/v25_t2.sh`) -> erster Lauf `VERIFY_EXIT=1` an ruff format, nach dem Formatieren zweiter voller Lauf `VERIFY_EXIT=0`: PHPUnit `OK (1416 tests, 8870 assertions)`, PHP-Gates grün, Python-Gates grün, pytest `971 passed`.
- Mutationen (je rot, Datei danach byte-gleich): M19 APCu-Zweig weg, M20 filelocking.enabled nicht gelesen, M25 strcmp, M26 ArrayCache weg, M27 fester Platzhalter zurück, M28 Schlüssel aus zh_TW.json entfernt.
- Baumhash php/: 05797073/143 -> 8eae94a1/145 (Task 1) -> d75974c9/145 (Task 2); Positivkontrollen über git archive 504cd787 und 39b2b436.
- Docker am Ende leer. Kein Push, kein Tag, kein Kommentar.

## Neue Katalogsätze (für die Bitte an foolfitz in 45-15)

1. `File locking on this server cannot keep background jobs apart: its locks live in a local cache such as APCu, which cron jobs and the web server do not share. Part of the indexing can then run twice at the same time. Redis or the database as the locking backend avoids this.` (zh_TW maschineller Entwurf: 此伺服器的檔案鎖定無法將背景作業彼此區隔：其鎖定存放在 APCu 等本機快取中，而 cron 工作與網頁伺服器並不共用此快取。因此部分索引作業可能會同時執行兩次。改用 Redis 或資料庫作為鎖定後端即可避免此情況。)
2. `Backups` (Beispiel im Feld der ausgeschlossenen Ordner; zh_TW maschineller Entwurf: 備份)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Eigener Fehl-Sample-Prüfer zu nachsichtig**
- **Found during:** Task 1, erster GREEN-Lauf des Contract-Tests
- **Issue:** `scan_locking_banner` prüfte nur Leerraum zwischen parallel-Banner und neuem Banner; ein vor die Schleife verschobener Banner ergab keinen Befund.
- **Fix:** Bedingung `parallel_end <= start < block_end` dazu.
- **Commit:** 39b2b436

**2. [Rule 3 - Blocking] ruff format am neuen Test von Task 2**
- **Found during:** Task 2, erster Verify-Lauf
- **Fix:** formatiert, Kommentar zum Fehl-Sample berichtigt (zwei Befunde), voller Verify-Lauf wiederholt.
- **Commit:** a6a71478

**3. [Hinweis] Fehl-Samples über den Plan hinaus**
- Task 1 prüft zusätzlich "Skript nennt den Banner" und "vor die Schleife verschoben"; Task 2 liefert beim Musterfeld über `$l->t(` zwei Befunde (übersetzt und kein festes Beispiel mehr), der Plan nannte "Befund".

## Neue Befunde

- INFO (im Audit, kein Fix): strcasecmp erkennt auch eine klein geschriebene Klasse `\oc\memcache\apcu`. Lädt der Composer-Autoloader sie nicht (APCu nicht schon über `memcache.local` geladen), fällt Nextcloud auf NullCache und den DB-Provider zurück, und der Hinweis stünde zu Unrecht. Aus dem Autoloader-Verhalten abgeleitet, nicht auf einer Instanz nachgestellt; der Plan verlangt strcasecmp ausdrücklich.
- `filelocking.enabled` steht in config.sample.php von stable33/34/35 nicht (nur `filelocking.ttl`, `filelocking.debug`); Standard true laut Server.php.

## Offene Punkte

- Sichtprüfung beider Änderungen im Browser im Neulauf von 45-10 (P-PLH); der Locking-Hinweis lässt sich dort mit `memcache.locking` auf APCu zeigen.
- Übersetzungen es, it, nl, pt_BR, pt_PT, zh_TW beider Schlüssel sind maschinelle Entwürfe (Bitte an foolfitz in 45-15).
- IDX-09 bleibt offen bis zur Live-Probe in 45-20 (wie nach 45-23).

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche: der Hinweis trägt keinen Wert aus der Konfiguration, nur einen festen Katalogsatz über `p()`; der Platzhalter ist ein fester Katalogwert über `p()`, geprüft von `test_no_catalogue_value_can_break_the_page`.

## Self-Check: PASSED

- Dateien vorhanden: LockingCheckService.php, LockingCheckServiceTest.php, AdminViewService.php, admin.php, AdminSettingsTest.php, SettingsControllerTest.php, 18 Kataloge, sechs Sprachdokus, admin-page.md, test_admin_ui_contract.py, test_measurement_scripts.py, 45-AUDIT.md, 45-FREIGABEN.md, dieses SUMMARY.
- Commits vorhanden: 504cd787, 39b2b436, a6a71478.
