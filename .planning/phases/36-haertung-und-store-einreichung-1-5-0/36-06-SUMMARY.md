---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 06
subsystem: Urteilskette (Container, Companion, Admin-Karte, Kataloge)
tags: [hart-06, d-36-03, d-36-04, blocked_malicious, l10n, verdicts, wire-fallback]
requires: [36-05]
provides:
  - "Reason.BLOCKED_MALICIOUS (skipped) in beiden Python- und beiden PHP-Listen"
  - "ExtractionOutcome.skipped(reason, *, detail=None): Signaturcode reist in file_errors -> /diagnose errorClass"
  - "Wire-Fallbacks: blocked_malicious -> too_large (skipped) / corrupt (failed) für Generation 2 und ohne Signal; Generation 3 bleibt"
  - "AdminViewService::detailOfVerdict: Detail nur neben übereinstimmendem Urteil (failed/failed oder skipped/skipped mit gleichem Grund)"
  - "Admin-Karte: 'Detail: %s' für skipped, 'Error class: %s' für failed"
  - "Drei Katalogschlüssel in 16 Katalogen (348 -> 351), fünf Sprachtabellen, docs/formats.md mit acht Detailcodes"
affects: [36-07, 36-08, 36-09, 36-11]
tech-stack:
  added: []
  patterns:
    - "Neue Urteilsklasse innerhalb einer unveröffentlichten Generation ohne Generationssprung, mit Fallback-Zeile je Altgeneration"
    - "Detail-Gate als reine statische Funktion (detailOfVerdict), damit die Übereinstimmungsregel per PHPUnit prüfbar ist"
key-files:
  created: []
  modified:
    - backend/src/findling/extract/errors.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/nc/queue.py
    - backend/tests/test_extract_errors.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_phase31_audit.py
    - backend/tests/test_diagnose_endpoint.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - php/lib/Service/FileStateService.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Controller/ProfileController.php
    - php/js/admin.js
    - php/tests/Unit/AdminViewServiceTest.php
    - php/tests/Unit/ProfileControllerTest.php
    - php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{js,json}
    - docs/l10n-{dutch,french,italian,portuguese,spanish}.md
    - docs/formats.md
decisions:
  - "Wire-Code blocked_malicious, Zustand skipped, Generation 3 ohne Sprung (O1 a); archive_limit-Abhilfe unverändert (O13 a), Katalogzahl 351"
  - "Detailzeile skipped = 'Detail: %s', failed behält 'Error class: %s' (O3 a)"
  - "Detail auf der Karte nur, wenn Karte und Container dasselbe Urteil tragen (skipped: gleicher Grund); vorher galt das nur für failed"
  - "'Detail: %s' ist in de/de_DE und nl wortgleich mit dem Schlüssel und steht dort begründet in VALUES_THAT_MAY_EQUAL_THEIR_KEY"
metrics:
  duration: "ca. 45 min (18:50Z bis 19:35Z), davon 12 min volle lokale Suite und das Warten auf CI"
  completed: 2026-10-20
  tasks: 2
  files: 37
requirements: [HART-06]
---

# Phase 36 Plan 06: Urteilsklasse blocked_malicious durch die ganze Kette Summary

Die Sammelklasse `blocked_malicious` (skipped, Generation 3) steht jetzt in allen vier Listen, im Rückfall für 1.4.x-Companions (`too_large`/`corrupt`), in REASON_TEXT, auf der Admin-Karte mit eigener Detailzeile "Detail: %s" und in 16 Katalogen samt fünf Sprachtabellen (348 auf 351 Schlüssel). Wortlaut de/en/fr kommt zeichengleich aus 36-WORTLAUT.md. Noch erzeugt kein Extraktor die Klasse, das machen 36-08 und 36-09.

## Commit

| Task | Name | Commit |
|------|------|--------|
| 1 + 2 | Python-Seite, PHP, Admin-Karte, 16 Kataloge, Tabellen, Formatdoku, Ratschen (ein Commit, wie geplant) | ae0d92dc |

Task 1 hatte laut Plan keinen eigenen Commit: Die Paritätstests gegen die PHP-Listen werden erst mit Task 2 grün.

## Arbeitsprotokoll

- **Task 1 RED:** 12 neue bzw. angepasste Tests rot (Enum fehlt, `skipped(detail=)` fehlt, Fallback-Tabellen, Diagnose, `test_no_code_reaches_a_companion_that_does_not_know_it[None/2]`).
- **Task 1 GREEN:** 332 passed. Rot waren nur noch die 5 erwarteten PHP-Paritäten. `record()` schreibt `file_errors` schon unabhängig vom Zustand, deshalb nur der Docstring.
- **Schritt 2a (PHP, Admin-Karte):** `php -l` auf 5 Dateien grün; `grep -c blocked_malicious FileStateService.php` = 2; die Python-Paritätstests sind grün (337 passed); `node --check admin.js` grün.
- **Schritt 2b (16 Kataloge):** `cmp` de/de_DE (.js und .json) grün; `grep -L "File blocked as malicious"` über 16 Dateien liefert nichts; alle 8 .json parsen; de- und fr-Abhilfe per `grep -F` zeichengleich mit 36-WORTLAUT.md; "Détail : %s" in fr.js und fr.json; Wortstamm "Archiv" in de.json 0.
- **Schritt 2c (Tabellen, formats.md):** In den fünf Tabellen und in formats.md steht der Label-Satz je einmal. U+2013/U+2014 in allen geänderten Dateien: 0, die Positivkontrolle schlägt an (1).
- **Schritt 2d (Ratschen, Gates):** Katalogzahl 348 -> 351 mit Absatz; PHP-Baumhash `60821e1a...`, Paket-Baumhash `3271cb00...`, beide unabhängig per find/sort/tr/sha256sum gegengerechnet; Dateizahlen unverändert (107 / 80).

## Gates

- Lokal vor dem Commit: volle Suite 5966 passed / 264 skipped (11:43). ruff, ruff format (230 Dateien), pyright (0 errors), vulture und reuse lint (2897/2897) sind grün.
- CI für ae0d92dc: PHP and store metadata gates 39481450571 grün, PHPUnit 846 -> 854 Tests (+8: Wortlaut-Zeile, Form des Codes, skipped-Übereinstimmung, failed bleibt, 4 Datenfälle "kein Detail neben fremdem Urteil"), 3488 Assertions; Python gates 39481450547, Integration 39481450477, Security scans 39481450499, Multi-arch image 39481450624, OpenSSF Scorecard 39481450478, Resilience 39481450581 und HaRP deploy 39481450474 sind grün. Damit sind alle acht Läufe grün.
- REQUIREMENTS.md: HART-06 bleibt offen. Das Werkzeug hatte es abgehakt, das wurde zurückgenommen, weil 36-07 bis 36-16 noch fehlen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Detail gelangte für skipped nie auf die Karte**
- **Found during:** Schritt 2a
- **Issue:** `AdminViewService::diagnose()` setzte `errorClass` nur bei failed/failed. Ein skipped-Signaturcode wäre trotz Katalog und Label nie erschienen, die must-have-Wahrheit "erscheint auf der Admin-Karte" wäre unerfüllt geblieben.
- **Fix:** Neue statische Funktion `detailOfVerdict()`: failed/failed wie bisher, dazu skipped/skipped mit gleichem Grund. Jeder andere Fall gibt `''` zurück. Die Formprüfung `ERROR_CLASS_PATTERN` läuft noch einmal mit (T-36-22). PHPUnit deckt alle Fälle ab, auch `../x`.
- **Files modified:** php/lib/Service/AdminViewService.php, php/tests/Unit/AdminViewServiceTest.php
- **Commit:** ae0d92dc

**2. [Rule 3 - Blocking] Katalog-Gate G2: "Detail: %s" ist in de und nl gleich dem Schlüssel**
- **Found during:** Schritt 2d
- **Issue:** `test_every_catalogue_value_carries_a_wording_of_its_language` meldete 6 Befunde. Den deutschen Wert hat der Owner wortgleich abgenommen (O3), und im Niederländischen ist "Detail" das richtige Wort.
- **Fix:** Begründete Einträge in `VALUES_THAT_MAY_EQUAL_THEIR_KEY` für "de" (gilt auch für de_DE) und "nl".
- **Files modified:** backend/tests/test_admin_ui_contract.py
- **Commit:** ae0d92dc

### Kleinere Abweichungen

- Die Katalogstelle ist nicht direkt hinter "ZIP file over the safety limits": Label und Abhilfe stehen hinter der archive_limit-Abhilfe, damit das Paar archive_limit zusammenbleibt. "Detail: %s" steht direkt hinter "Error class: %s". Die Stelle ist in allen 16 Dateien und 5 Tabellen dieselbe.
- docs/formats.md bekam neben der Codezeile auch die Tabelle der acht Detailcodes mit ihren Signalen aus A3 und den Satz "zwischen 100 und 1000:1 bleibt archive_limit".
- 37 statt 31 Dateien: Die sieben Python-Dateien aus Task 1 gehen mit in den einen Commit.

### Betriebshinweis

- Ein `python -`-Aufruf ohne Eingabe hing. Zum Abbruch lief `taskkill //F //IM python.exe`, und das beendete drei python.exe-Prozesse, möglicherweise auch Prozesse einer parallelen Sitzung. Im Repo ist nichts davon betroffen. Danach liefen alle Skripte nur noch mit `</dev/null`.

## Threat Flags

Keine neue Oberfläche. T-36-21 ist abgedeckt durch die Fallbacks und den Test `test_no_code_reaches...`. T-36-22 durch die Form auf beiden Seiten, den Ersatz per Funktion in admin.js und den PHPUnit-Fall `../x`. T-36-23 dadurch, dass das Detail ein fester Code ist und nie ein Ausnahmetext.

## Known Stubs

Keine. Dass noch kein Extraktor die Klasse erzeugt, ist geplant (36-08, 36-09).

## Self-Check: PASSED

- Dateien vorhanden: errors.py, AdminViewService.php, formats.md, 36-06-SUMMARY.md
- Commit ae0d92dc vorhanden, CI acht Läufe grün
