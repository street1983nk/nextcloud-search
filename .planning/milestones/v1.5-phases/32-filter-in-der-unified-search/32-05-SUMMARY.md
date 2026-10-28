---
phase: 32-filter-in-der-unified-search
plan: 05
subsystem: l10n (16 Kataloge, 5 Sprachdokus), Backend-Tests (Vertrag Skript gegen Katalog)
tags: [usrch-01, usrch-02, d-32-04, l10n, unified-search]
requires:
  - phase: 32
    provides: "32-04: php/js/unified-search.js mit den vier neuen Schlüsseln, NEW_KEYS/ALLOWED_KEYS im Vertragstest"
provides:
  - "vier Schlüssel (File contents: %s, File contents in a folder, File contents in %s, Choose the folder to search in) in allen 16 Katalogdateien, direkt hinter File contents"
  - "je eine Tabellenzeile pro Schlüssel in docs/l10n-french/spanish/italian/dutch/portuguese.md, datierter Nachtrag 13.10.2026"
  - "Vertragsfall: jeder Schlüssel, den unified-search.js über t('findling', ...) oder TYPE_ENTRIES nutzt, steht in jeder der 16 Dateien"
affects: [32-07 Owner-Abnahme des Wortlauts per Playwright, 32-08 Audit]
tech-stack:
  added: []
  patterns: ["Schlüssel des Skripts gegen jeden Katalog, nicht nur Kataloge untereinander"]
key-files:
  created: []
  modified:
    - php/l10n/*.js, php/l10n/*.json (16 Dateien)
    - docs/l10n-french.md
    - docs/l10n-spanish.md
    - docs/l10n-italian.md
    - docs/l10n-dutch.md
    - docs/l10n-portuguese.md
    - backend/tests/test_unified_search_plugin.py
    - backend/tests/test_admin_ui_contract.py
decisions:
  - "Wortlaut es/it/nl/pt folgt der Anredeform des jeweiligen Katalogs: es usted-Imperativ (Elija), it und nl Infinitiv (Scegliere, kiezen), pt_PT und pt_BR Imperativ (Escolha); Ordnerwort wie im Katalog (carpeta, cartella, map, pasta)"
  - "used_keys liest auch die Gruppennamen aus TYPE_ENTRIES, weil sie über eine Variable in t('findling', entry[1]) gehen"
  - "Harte Schlüsselzahl in test_the_german_catalogue_covers_both_german_language_codes 302 auf 306, mit Begründungsabsatz wie der Docstring verlangt"
metrics:
  duration: "ca. 85 min inkl. ca. 13 min Volltestlauf und ca. 25 min CI"
  completed: 2026-10-13
  tasks: 2
  files: 23
---

# Phase 32 Plan 05: l10n der Filtereinträge Summary

Die vier Sätze der Filtereinträge der Unified Search stehen in allen 16 Katalogdateien und in den fünf Sprachtabellen; ein neuer Vertragsfall hält jeden Schlüssel, den `unified-search.js` übersetzt, gegen jede Katalogdatei.

## Commit

- `0f355b0b` feat(32-05): the four strings of the unified search filter entries in all catalogues (Task 1 und 2 in einem Commit; dazwischen wäre das Tabellen-Gate rot), gepusht auf origin/main.

## Wortlaute (Entwurf D-32-04, Abnahme in 32-07)

| Schlüssel | de / de_DE | fr | es | it | nl | pt_PT | pt_BR |
|---|---|---|---|---|---|---|---|
| `File contents: %s` | Dateiinhalte: %s | Contenu des fichiers : %s | Contenido de los archivos: %s | Contenuto dei file: %s | Inhoud van bestanden: %s | Conteúdo dos ficheiros: %s | Conteúdo dos arquivos: %s |
| `File contents in a folder` | Dateiinhalte in einem Ordner | Contenu des fichiers dans un dossier | Contenido de los archivos en una carpeta | Contenuto dei file in una cartella | Inhoud van bestanden in een map | Conteúdo dos ficheiros numa pasta | Conteúdo dos arquivos em uma pasta |
| `File contents in %s` | Dateiinhalte in %s | Contenu des fichiers dans %s | Contenido de los archivos en %s | Contenuto dei file in %s | Inhoud van bestanden in %s | Conteúdo dos ficheiros em %s | Conteúdo dos arquivos em %s |
| `Choose the folder to search in` | Ordner für die Suche wählen | Choisir le dossier où chercher | Elija la carpeta en la que buscar | Scegliere la cartella in cui cercare | De map kiezen om in te zoeken | Escolha a pasta onde pesquisar | Escolha a pasta onde pesquisar |

Deutsch und Französisch zeichengleich zum Plan. Leerzeichen vor dem Doppelpunkt nur im Französischen (docs/l10n-french.md, Typografie).

## Task 1: Vertragsfall und 16 Kataloge

- `used_keys` (literale `t('findling', ...)`-Aufrufe ohne Kommentare, plus Gruppennamen aus `TYPE_ENTRIES`) und `keys_missing_from_catalogues` in test_unified_search_plugin.py.
- `test_every_key_of_the_plugin_stands_in_every_catalogue`: 16 Dateien gelesen, `used_keys == ALLOWED_KEYS` (zehn Schlüssel, gegen leere Menge), keine Lücke.
- `test_a_key_the_catalogue_lacks_is_a_finding`: eigener Testkatalog; Positivkontrolle sauber, fremder Schlüssel einmal je Datei gemeldet, fehlender Gruppenname über TYPE_ENTRIES gemeldet, Aufruf im Kommentar zählt nicht.
- RED: `test_every_key_of_the_plugin_stands_in_every_catalogue` rot mit 64 Befunden (4 Schlüssel x 16 Dateien), Selbsttest grün. GREEN nach dem Einfügen.
- Kataloge per Skript eingefügt, je Datei direkt hinter `"File contents"`, gleiche Einrückung, gleiche Zeilenenden, `.js` und `.json` zeichengleich.
- `test_the_german_catalogue_covers_both_german_language_codes`: 302 auf 306, Begründungsabsatz und Kommentarzeile ergänzt.

## Task 2: Sprachtabellen

- Je Doku vier Zeilen hinter `File contents`, Zellen mechanisch aus den Katalogen; Nachtrag "13.10.2026 (Phase 32, Plan 32-05)" hinter dem Nachtrag vom 29.09.2026.
- Unabhängige Zählung per `grep -cF`: jeder der vier Schlüssel genau einmal je Doku (20 mal 1).

## Gegenproben (Kopien im Scratchpad, danach `cmp` gleich)

- `"File contents in %s"` aus pt_BR.js gelöscht: neuer Vertragsfall rot (`... missing from pt_BR.js`), dazu G1 `test_every_catalogue_carries_the_same_keys` und das Tabellen-Gate rot.
- nl-Tabellenzelle "in een map" auf "in de map" geändert: `test_every_language_table_carries_every_key_with_the_catalogue_wording` rot.

## Gates und CI

- Lokal aus backend/ mit PYTHONUTF8=1: `pytest` 5613 passed, 30 skipped (5611 + 2); `ruff check`, `ruff format --check` grün; `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` 0 Fehler; `vulture src tests --min-confidence 80` ohne Befund. `test_php_acl_boundary.py` unverändert und grün. `test_measurement_scripts.py` grün (l10n bewegt den PHP-Baumhash nicht).
- CI auf 0f355b0b, `gh run watch <id> --exit-status`:
  - PHP and store metadata gates 38334174243: grün (OK, 648 Tests, 2370 Assertions).
  - Python gates 38334174281: grün (5625 passed, 18 skipped).
  - Integration 38334174253: grün.
  - HaRP deploy 38334174230: grün.
  - Außerdem grün (Exitcode 0): Resilience 38334174268, Security scans 38334174283, OpenSSF Scorecard 38334174312, Multi-arch image 38334174251.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Harte Schlüsselzahl im deutschen Katalog-Gate**
- **Found during:** Task 1
- **Issue:** `test_the_german_catalogue_covers_both_german_language_codes` verlangt 302 Schlüssel; test_admin_ui_contract.py stand nicht in `files_modified`.
- **Fix:** 306 mit datiertem Begründungsabsatz (der Docstring verlangt ihn von jedem, der die Zahl bewegt).
- **Commit:** 0f355b0b

### Präzisierungen

- Der Plan nennt den Vertragsfall für `t('findling', '<key>')`; die sechs Gruppennamen gehen über `entry[1]` und wären einer reinen Literal-Lesung entgangen, deshalb liest `used_keys` auch `TYPE_ENTRIES`.
- Im Portugiesischen traf das Einfügeskript zuerst die Wortpaar-Tabelle (Zeile 117, ebenfalls mit `File contents`); von Hand korrigiert, bevor ein Gate lief.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-32-18: Platzhalter- und Seitenbruch-Gates grün über alle 16 Dateien (`%s` in Schlüssel 1 und 3 je genau einmal). T-32-19: Wortlaut als Entwurf in den fünf Dokus vermerkt, Abnahme in 32-07.

## Offene Punkte

- Owner-Abnahme des Wortlauts aller acht Sprachen in 32-07; Änderungen dann in Kataloge und Tabellen.
- USRCH-01/02 bleiben Pending bis 32-06/32-07.

## Self-Check: PASSED

- 16 Kataloge mit "File contents in a folder" und "Choose the folder to search in" (`grep -l` je 16); de.json Zeile 6 und fr.json Zeile 6 treffen die Akzeptanz-Greps.
- Fünf Dokus: jeder Schlüssel genau einmal in der Tabelle.
- Commit 0f355b0b in `git log` und auf origin/main; alle acht CI-Läufe success.
