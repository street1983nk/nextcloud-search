---
phase: 46-findling-1-7-1
plan: 01
subsystem: l10n
tags: [excl-07, kataloge, hilfesatz]
requires: []
provides: [Gate Hilfesatz gleich Platzhalter]
affects: [php/l10n, docs/l10n-*.md, docs/admin-page.md]
key-files:
  modified:
    - backend/tests/test_admin_ui_contract.py
    - php/l10n/*.json, php/l10n/*.js (18 Dateien, je eine Zeile)
    - docs/l10n-chinese.md, l10n-dutch.md, l10n-french.md, l10n-italian.md, l10n-portuguese.md, l10n-spanish.md
    - docs/admin-page.md
duration: ca. 35 min
completed: 2026-11-27
---

# 46-01: Hilfesatz der Ordnerliste nennt das Beispiel seines Feldes (EXCL-07)

## Ergebnis

- Task 1 (Entscheide): erledigt durch den Koordinator, Commit 98bd5713. Alle acht Entscheide wie empfohlen (E-46-01 a, E-46-02 a, E-46-03 ja, E-46-04 a, E-46-05 a, E-46-06 a, E-46-07 a, E-46-08 ja).
- Task 2: RED 66570830 `test(46-01): the folder help names the example its own placeholder shows`, GREEN 14b9e0f8 `fix(46-01): the folder help and its field name the same example in every language`.

## RED-Lauf (66570830)

`test_the_folder_help_names_the_example_of_its_own_placeholder`: 18 Funde, erster: `de.json: the help sentence ends on 'enden. Beispiel: Backups', the placeholder reads 'Sicherungen'`. Positivkontrolle `test_the_folder_help_gate_sees_the_old_english_example` grün. Übrige Gates grün (ruff, ruff format, pyright 0 Fehler, vulture); Ausnahme B3 für den RED-Commit.

## GREEN (14b9e0f8)

- 18 Katalogdateien: nur das letzte Wort des Hilfesatzes, msgid unverändert, je Datei eine Zeile (`git diff --numstat`: 18 mal 1/1). Neue Enden: de/de_DE "Beispiel: Sicherungen", fr "Exemple : Sauvegardes", es "Ejemplo: Copias de seguridad", it "Esempio: Backup", nl "Voorbeeld: Back-ups", pt_BR "Exemplo: Backup", pt_PT "Exemplo: Cópias de segurança", zh_TW "範例：備份".
- Sprachtabellen in sechs docs/l10n-*.md (DE-Spalte und Zielspalte), docs/admin-page.md Absatz "Platzhalter der Regelfelder" um einen Satz zu 1.7.1 ergänzt.
- Mutation: fr.js auf "Exemple : Backups" zurück, Gate rot mit 1 Fund (`fr.js: ... the placeholder reads 'Sauvegardes'`), zurückgesetzt.
- Läufe am GREEN-Stand: test_admin_ui_contract, test_phase34_audit, test_phase33_audit, test_public_artifacts, test_admin_locale: 354 passed, 107 skipped; ruff, ruff format, pyright, vulture grün. Gedankenstriche in den geänderten Doku-Dateien: 0.
- Docker-Teil von B3 (phpunit_docker.sh, php_gates_docker.sh): offen, nur Kataloge und Doku geändert; wird vor dem ersten Push (46-06) im freigegebenen Docker-Fenster nachgeholt.

## Abweichungen

- Die Entscheidzeilen tragen die Kennung `46-01` statt `46-00` und hinter dem Wert eine Erläuterung in Klammern; das verify von 46-01 Task 1 und das verify von 46-12 Task 1 (`Entscheid: a$`) passen deshalb nicht wörtlich. Inhaltlich sind alle acht Entscheide belegt; 46-12 prüft beim Ausführen auf `Entscheid E-46-07 46-01: .* Entscheid: a`.
- Hilfsskript als Datei im Scratchpad, gestartet mit `python -I -X utf8 <datei>` (nie `python -c`). Der erste Lauf brach nach zh_TW.json an der Konsolenkodierung ab (Ausgabe, nicht Datei); zh_TW.js im zweiten Lauf, Endergebnis geprüft (18 Dateien, je eine Zeile).

## Befund außerhalb des Plans

- I-46-01-01 (LOW, schon auf origin/main): `test_store_metadata.py::test_the_store_listing_document_avoids_the_blocked_term_counting_every_line` ist rot, auch ohne die Änderungen dieses Plans (Gegenprobe per `git stash`). Ursache: docs/store-listing.md enthält seit 45-14 (Commits 29ba097f, f08317ef) das gesperrte Wort im Abschnitt "# Release 1.7.0" (Z. ~3588 Workflowname "Release archives for the app store", Z. ~3605 und ~3618). In CI fiel es nicht auf, weil python.yml keinen paths-Filter auf docs/ hat. Der nächste Push mit backend/** (spätestens 46-05) macht "Python gates" rot. Owner-Dokument: nicht eigenmächtig geändert; Vorschlag: in 46-05 die drei Zeilen umformulieren (Workflowname in Backticks reicht nicht, die Zählung nimmt jede Zeile), nach Owner-Ok.
