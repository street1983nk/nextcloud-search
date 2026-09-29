---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 13
subsystem: l10n
tags: [kataloge, l10n, ui-01, sc4, gate]
requires: ["27-01", "27-10", "27-12"]
provides: ["Sätze des Blocks Leistungsprofil in acht Sprachen, 16 Dateien", "Vollständigkeits-Gate für den Block"]
affects: [php/l10n, backend/tests/test_admin_ui_contract.py]
tech-stack:
  added: []
  patterns: [Schlüsselsammlung per Markerschnitt aus Template und Skript, Abwesenheit per Name]
key-files:
  created: []
  modified:
    - php/l10n/de.js
    - php/l10n/de.json
    - php/l10n/de_DE.js
    - php/l10n/de_DE.json
    - php/l10n/es.js
    - php/l10n/es.json
    - php/l10n/fr.js
    - php/l10n/fr.json
    - php/l10n/it.js
    - php/l10n/it.json
    - php/l10n/nl.js
    - php/l10n/nl.json
    - php/l10n/pt_BR.js
    - php/l10n/pt_BR.json
    - php/l10n/pt_PT.js
    - php/l10n/pt_PT.json
    - backend/tests/test_admin_ui_contract.py
decisions:
  - "Das Gate schneidet das Template ab dem Kommentar 'The performance profile of phase 27' statt ab id=findling-profile, weil die meisten Sätze in den Maps vor dem Markup stehen"
  - "Backend heißt in den Fremdsprachen wie im Bestand service/servicio/servizio/dienst/serviço; box heißt machine/equipo/macchina/machine/máquina"
  - "Keine neuen Ausnahmen in VALUES_THAT_MAY_EQUAL_THEIR_KEY nötig: kein neuer Wert gleicht seinem Schlüssel"
metrics:
  duration: "ca. 35 min"
  completed: "2026-09-29"
  tasks: 2
  files: 17
---

# Phase 27 Plan 13: Kataloge des Leistungsprofils Summary

72 neue Sätze des Blocks Leistungsprofil in allen 16 Katalogdateien (8 Sprachen), der occ-Satz des Wächters gelöscht und ein Gate, das jeden Satz aus Template und Skript des Blocks in jeder Datei verlangt.

## Tasks

| # | Name | Commit | Dateien |
|---|------|--------|---------|
| 1 | Sätze in 16 Katalogdateien, entfallenen Schlüssel löschen | 90a12202 | php/l10n/*.js, *.json |
| 2 | Katalog-Gates nachziehen, Vollständigkeits-Gate | 5b922f3e | backend/tests/test_admin_ui_contract.py |

## Was gebaut wurde

- Schlüssel per Skript aus `$l->t(...)` in admin.php und `t('findling', ...)` in admin.js gesammelt, gegen de.json abgeglichen: genau 72 fehlten, darunter `Check running.`, `OCR with %s slots` und die fünf Nur-Skript-Schlüssel aus 27-12.
- Deutsch wörtlich aus der UI-SPEC (inkl. der sechs Owner-Sätze aus 27-01, "Bei Sparsam bleiben", "Übernehmen und prüfen", "Genaueres Suchmodell (fp32)"), de_DE byte-gleich zu de.
- es, fr, it, nl, pt_BR, pt_PT sinngleich, Profilnamen aus den Bestandsschlüsseln der Sprache, pt_BR und pt_PT getrennt (arquivo/ficheiro, baixar/transferir, em andamento/em curso).
- "To lift the reduction after checking the memory: %1$s" aus allen 16 Dateien entfernt. Schlüsselzahl jetzt 287 (216 + 72 - 1).
- Neues Gate `test_every_sentence_of_the_profile_block_is_in_every_catalogue` mit Anti-Vakuum-Liste und Rot-Probe. Die Abwesenheit des occ-Satzes wird in `test_the_two_translation_files_carry_the_same_keys` per Name für alle 16 Dateien geprüft. Harte Zahl 287 mit Begründungsabsatz im Docstring.

## Verifikation

- test_admin_ui_contract.py: 77 passed
- volle Suite: 4106 passed, 25 skipped
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün
- keine U+2013/U+2014 in php/l10n, Baumhash-Pin nicht angefasst

## Deviations from Plan

**1. [Rule 3 - Blocking] Helfer `cut_between` gibt es schon**
- **Found during:** Task 2 (ruff F811)
- **Fix:** meine Kopie entfernt, die vorhandene Funktion (gleiche Semantik) benutzt
- **Commit:** 5b922f3e

**2. Gate-Schnitt im Template breiter als im Plan**
- Der Plan nennt den Schnitt von id="findling-profile" bis id="findling-rules". Die meisten Sätze stehen aber in den PHP-Maps davor, deshalb beginnt der Schnitt am Kopfkommentar des Blocks. Im Skript geht der Schnitt vom Kopfkommentar "Block Performance profile" bis `function render`, damit sind setupProfile und alle Probe-Maps drin.

Sonst lief der Plan wie geschrieben.

## Known Stubs

Keine.

## Hinweise

- Die Tabellen der fünf Sprachdokumente (docs/l10n-*.md) haben die neuen Zeilen noch nicht. Das ist derselbe Stand wie nach 25-04 und steht so auch im Docstring.
- Die Fremdsprachen sind maschinell übersetzt und fallen unter den bestehenden datierten Vorbehalt (E-17-5).

## Self-Check: PASSED

- 16 Kataloge und Testdatei geändert, Commits 90a12202 und 5b922f3e im Log vorhanden
