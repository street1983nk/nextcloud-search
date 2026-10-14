---
phase: 33-ausschlussmuster-und-admin-feinschliff
plan: 05
subsystem: admin-ui, exclusions
tags: [exclusions, patterns, admin-page, refusal-codes, confirmation, phpunit, tdd]
requires:
  - "33-02: ExclusionService mit validatePatterns(), savePatterns(), newPatterns(), FIELD_PATTERNS, MAX_PATTERNS, MAX_PATTERN_LENGTH, elf ERROR_*-Codes"
  - "33-04: savePatterns() plant den Kehrjob (Weg A)"
provides:
  - "POST /admin/rules und GET /admin/rules/preview mit exclusionPatterns, beide Listen vor jedem Schreiben geprüft, Antwort nur mit Codes"
  - "AdminViewService::rules() mit exclusionPatterns, maxPrefixes, maxPrefixLength, maxPatterns, maxPatternLength"
  - "Admin-Seite: Liste Excluded patterns, Meldung je Code je Liste (folderErrorSentences, patternErrorSentences), zahlenlose Bestätigung mit code-Element"
  - "Diagnose-Abhilfe nennt beide Listen"
affects: [33-06, 33-07, 33-08, 33-10, 33-11]
tech-stack:
  added: []
  patterns:
    - "Fehlercodes je Liste als Map in Template und Skript, Codes im Vertragstest aus ExclusionService.php gelesen"
    - "Zwei Code-Marker (U+E001, U+E002) im übersetzten Hilfesatz, Beispiele als code-Element"
    - "Bestätigungssatz am Platzhalter geschnitten, Muster als Textknoten in einem code-Element"
key-files:
  created:
    - php/tests/Unit/SettingsControllerTest.php
  modified:
    - php/lib/Controller/SettingsController.php
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/css/admin.css
    - php/tests/Unit/AdminViewServiceTest.php
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "33-05: Die Ordnerliste trägt die Sätze der Codes, die ExclusionService::validate() vergeben kann (fünf), die Musterliste alle elf; die sechs reinen Muster-Codes entfallen für Ordner (33-WORTLAUT.md B)"
  - "33-05: Eine vom Server abgelehnte Vorschau zeigt die Sätze je Code und keine Bestätigung; eine Vorschau mit Serverfehler fällt wie bisher auf die Bestätigung ohne Zahl zurück"
  - "33-05: Die Regel-Ansicht trägt auch die zwei Präfixgrenzen (64, 256), weil die Sätze too_long und too_many der Ordnerliste die Zahl nennen"
  - "33-05: Die Antwort trägt Codes ohne Index (Vertrag von ExclusionService), deshalb steht der Satz am Fehlerelement der Liste und keine Zeile wird markiert"
requirements-completed: []
metrics:
  duration: "ca. 110 min inkl. ca. 14 min Volltestlauf, Sichtprobe und ca. 30 min CI"
  completed: 2026-10-14
  tasks: 2
  files: 9
---

# Phase 33 Plan 05: Musterliste auf der Admin-Seite Summary

Die Admin-Seite führt unter "Excluded folders" eine zweite Liste "Excluded patterns" im selben Stil. Beide Regelrouten nehmen `exclusionPatterns` neben `exclusions` an, prüfen beide Listen vor jedem Schreiben und antworten nur mit Codes; die Seite zeigt jeden Code als eigenen Satz neben der Liste, zu der er gehört. Neue Muster werden mit dem zahlenlosen Satz bestätigt, das Muster steht dabei in einem eigenen code-Element. Die Diagnose-Abhilfe nennt beide Listen.

EXCL-01 und EXCL-03 bleiben laut Plan offen bis 33-11 (Übersetzung in 33-07, Abnahme in 33-10).

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Regelrouten mit zwei Listen und Diagnose-Abhilfe | 2aa25e56 | SettingsController.php, AdminViewService.php, SettingsControllerTest.php, AdminViewServiceTest.php |
| 2 | Zweite Liste, Meldung je Code, zahlenlose Bestätigung, Hash, CI | 2aa25e56 | admin.php, admin.js, admin.css, test_admin_ui_contract.py, test_measurement_scripts.py |

Task 1 und 2 laufen laut Plan in einem Commit.

## Routen

- `previewRules(array $exclusions = [], array $exclusionPatterns = [])` und `saveRules(..., array $exclusionPatterns = [])` (`grep -c` = 2): erst `validate()` und `validatePatterns()` (beim Speichern dazu die Felder), bei einem Fehler HTTP 400 mit `exclusions`, `exclusionPatterns` und dem bisherigen `error`-Satz, nichts geschrieben. Danach `SettingsService::save()`, `ExclusionService::save()` und zuletzt `savePatterns()`, diese nur, wenn die zwei Schreibvorgänge davor gehalten haben.
- Logzeilen zählen beide Listen getrennt (`exclusions`, `exclusionPatterns`), nie Werte.
- Vorschau: `newPatterns` neben `newPrefixes`, `affectedDocuments`, `capped`; keine Zahl für Muster (PE-5).
- Speichern nur von Mustern: Die Präfixliste wird wie heute bei unveränderter Liste einmal mit gleichem Inhalt geschrieben; kein SubtreeExpandJob, genau ein ExclusionSweepJob (aus `savePatterns()`, 33-04).
- `AdminViewService::rules()`: `exclusionPatterns`, `maxPrefixes`, `maxPrefixLength`, `maxPatterns`, `maxPatternLength` aus den Konstanten von ExclusionService, Docblock-Typ nachgezogen. Abhilfe von `excluded` auf den Satz aus 33-WORTLAUT.md (D), Schlüsselzahl gleich.

## Seite

- Template: Liste `findling-rules-patterns-*` (Label, Hilfe, Leer-Satz, Liste, Eingabe mit `maxlength` 60 und Datenattributen für beide Grenzen, Knopf, Fehlerelement) unter der Ordnerliste, Zeilen aus derselben Zeilenvorlage. Hilfesatz mit zwei Code-Markern (U+E001, U+E002); die Beispiele `*.photoslibrary` und `*/node_modules/*` stehen als code-Elemente außerhalb des übersetzten Satzes, auch bei vertauschter Reihenfolge in einer Sprache. Ordnerhilfe auf den neuen Schlüssel. Maps `$folderErrorSentences` (5 Codes) und `$patternErrorSentences` (11 Codes), alles mit `p()`.
- Skript: dieselben Maps `folderErrorSentences()` und `patternErrorSentences()`; Musterliste lesen und senden (`exclusionPatterns` im POST, `exclusionPatterns[]` in der Vorschau); lokale Vorprüfung leer, doppelt, zu lang (Zeichen nach NFC), zu viele, Grenzen aus den Datenattributen; Serverantwort je Code als Satz am Fehlerelement der jeweiligen Liste, nur `textContent`. Die Kopfzeile "The rules were not saved. Nothing changed." bleibt. Lehnt der Server schon die Vorschau ab, zeigt die Seite die Sätze und keine Bestätigung.
- Bestätigung: Satz für neue Ordner wie bisher, darunter der zahlenlose Satz für neue Muster (Einzahl oder Mehrzahl), am Platzhalter geschnitten, Muster als Textknoten im code-Element `findling-rules-confirm-patterns-value`. CSS `.findling-rules__confirm-line` (Block nur, solange sichtbar).
- Alle neuen Sätze zeichengleich mit den englischen Schlüsseln aus 33-WORTLAUT.md (A bis D). Die Kataloge folgen in 33-07; kein Gate dieses Plans verlangte einen Satz vorab im Katalog, die Katalogregel des Plans kam also nicht zum Zug.

## Belege

**Vertragsfälle (Task 2), neu in test_admin_ui_contract.py:**

- (a) `test_the_rules_block_carries_the_pattern_list_under_the_folder_list`
- (b) `test_both_halves_name_every_refusal_code_of_both_lists_alike` (Codes aus `ERROR_*` von ExclusionService.php, Ordnercodes aus dem Körper von `validate()` gelesen)
- (c) `test_no_refusal_sentence_carries_a_placeholder_but_the_bound`
- (d) `test_the_script_sends_the_pattern_list_and_cuts_the_confirmation_around_it`
- (e) `test_a_refusal_map_without_a_code_is_one_finding` (sauber still, fehlender Code genau ein Befund, Platzhalter mit Wert genau ein Befund, ungleiche Hälften plus fehlender Code zwei)
- dazu `test_the_remedy_of_an_excluded_file_names_both_lists`

RED ohne `git stash`: Template, Skript und AdminViewService per `git show HEAD:` eingesetzt, die sechs Fälle: **5 failed, 1 passed** (der Selbsttest (e) bleibt grün, wie er soll); eigene Kopien zurück, `cmp` gleich. Mutation am echten Skript (Zeile `no_wildcard` aus `patternErrorSentences()` gelöscht): (b) rot mit "the template and the script word the codes differently" und "has no sentence for the code no_wildcard"; Datei zurück, `cmp` gleich. Gate C (Markup, Escaping, Striche, Emojis) unverändert grün.

**PHPUnit (nur CI):** Rot war vor der Umsetzung nur als Textprüfung belegbar: Der alte `saveRules` kennt keinen fünften Parameter, PHP verwirft ein überzähliges Argument stillschweigend, also hätte `[0-9]*` mit HTTP 200 gespeichert und der Fall "nichts geschrieben" wäre rot. Vorher 766 Tests (Lauf 38506312552), nachher **777 Tests, 2904 Assertions** (Lauf 38512158095). +11: SettingsControllerTest 10 (beide gespeichert und Präfixliste byte-gleich; ungültiges Muster neben gültigem Präfix schreibt nichts, Code an Position 0; ungültiger Präfix neben gültigem Muster schreibt nichts; ungültige Grenze neben gültigem Muster; nur Muster: Präfixliste einmal gleich geschrieben, kein SubtreeExpandJob, genau ein ExclusionSweepJob; Wert-Abwesenheitsprobe über `json_encode` von Antwort und Logzeilen für beide Richtungen und die Vorschau; alle Muster-Codes ohne Eintrag; Vorschau mit `newPatterns` und ohne Musterzahl; Vorschau lehnt Muster ab; Vorschau lehnt Präfix ab), AdminViewServiceTest 1 (Abhilfe-Satz aus `REASON_TEXT`).

**Baumhash:** `PHP_TREE_HASH_TODAY` von `da53dd88...` auf `48aa61a8304ca59479df8c6d55f38ee2f2b253837bbaab0b838f727a7e9a80b1`, `PHP_FILES_TODAY` 102 auf 103 (SettingsControllerTest.php), Journalabsatz "Moved on 2026-10-14 by Plan 33-05". Beide Rezeptkopien liefern denselben Wert.

**Gates lokal (backend/, PYTHONUTF8=1):** pytest **5672 passed, 159 skipped** (13:42 min); ruff check grün; ruff format --check 222 Dateien; pyright 0 errors (latest); vulture leer; reuse lint 2724/2724; `node --check php/js/admin.js` grün; PHPL-Block vor und nach dem Commit grün. Nach einer reinen Kommentaränderung am Skript liefen Vertrag und Messskripte erneut (656 passed). CI Python gates: 5683 passed, 148 skipped.

## Sichtprobe 8090 (vor dem Commit, Playwright, admin)

Bildschirmfotos im Scratch (`C:/Users/Student/AppData/Local/Temp/claude/C--Users-Student/f6488641-8ddf-4bad-8748-b99f3aecda70/scratchpad/sicht3305/`):

- `1-liste.png`: Regelblock mit beiden Listen, Hilfesatz mit den zwei code-Beispielen, Leer-Satz sichtbar, `maxlength` 60, Ordnerhilfe mit dem neuen Satz.
- `2-bestaetigung.png`: `*.key` hinzugefügt, Speichern zeigt "Remove indexed content? Excluding *.key also removes the already indexed documents that match that pattern from the index. The files themselves stay untouched on disk." ohne Zahl, `*.key` im code-Element, Ordnerzeile verborgen; abgebrochen.
- `3-ablehnung.png`: `[0-9]*` ergibt aus der Vorschau HTTP 400 `{"exclusions":[],"exclusionPatterns":["unsupported_character"],"error":"The rules were not saved."}`; an der Musterliste steht "Brackets, braces and the backslash are not allowed. Only * and ? are wildcards.", darunter die Kopfzeile "nicht gespeichert", keine Bestätigung, kein POST.

Zusätzlich lokal "Enter a pattern." bei leerem Feld und ein Rundweg mit einem Muster, das nichts trifft (`*.sichtprobe-3305-nichts`): gespeichert (Antwort mit `rules.exclusionPatterns` und den vier Grenzen), wieder entfernt und gespeichert; die Ordnerliste blieb `["Archiv"]`. Danach `occ config:app:get findling exclusion_patterns` = `[]`, Schlüssel per `occ config:app:delete` entfernt (erneutes Lesen Exit 1, also leer wie vor der Probe), `exclusions` unverändert `["Archiv"]`, kein ExclusionSweepJob in `occ background-job:list`.

Die neuen Sätze erscheinen auf der deutschen Seite noch englisch; die Übersetzung ist Sache von 33-07.

## CI (2aa25e56)

Alle mit `gh run watch <id> --exit-status` bis zum Ende beobachtet, alle grün:

- PHP and store metadata gates 38512158095 (PHPUnit 777)
- Python gates 38512158170
- Security scans 38512158084
- OpenSSF Scorecard 38512158121
- Resilience 38512158085
- Multi-arch image 38512158143
- Integration 38512158135
- HaRP deploy 38512158083 (zweiter Watch-Aufruf, der erste lief in die lokale Zeitgrenze)

Erste Liste leer, zweiter Aufruf mit 8 Läufen, dritter Aufruf gleich (8).

## Deviations from Plan

### Auto-fixed Issues

**1. [Regel 2 - Fehlende kritische Funktion] Präfixgrenzen in der Regel-Ansicht**
- **Gefunden in:** Task 2
- **Problem:** Der Plan nennt nur `maxPatterns` und `maxPatternLength`. Die Sätze `too_long` und `too_many` der Ordnerliste (33-WORTLAUT.md B) tragen die Grenzzahl 256 bzw. 64; ohne die Werte hätte die Seite sie hart codieren müssen.
- **Fix:** `rules()` trägt zusätzlich `maxPrefixes` und `maxPrefixLength` aus den Konstanten; das Ordnerfeld hat dieselben Datenattribute wie das Musterfeld.
- **Dateien:** php/lib/Service/AdminViewService.php, php/templates/admin.php
- **Commit:** 2aa25e56

**2. [Regel 1 - Bug] Bestätigung für eine Liste, die der Server ablehnt**
- **Gefunden in:** Task 2
- **Problem:** `ask()` wirft bei jeder Nicht-OK-Antwort; eine vom Server abgelehnte Vorschau (`[0-9]*`) wäre in den Rückfall "Bestätigung ohne Zahl" gelaufen, die Seite hätte die Löschfolge eines Musters bestätigen lassen, das gar nicht gespeichert werden kann.
- **Fix:** eigene lesende Funktion `preview()` mit Status; bei HTTP 400 die Sätze je Code und die Kopfzeile, keine Bestätigung. Serverfehler (500) fallen wie bisher auf die zahlenlose Bestätigung zurück.
- **Dateien:** php/js/admin.js
- **Commit:** 2aa25e56

### Weitere Abweichungen

1. **Keine Zeilenmarkierung über Index:** Der Plan verlangt "Zeile markiert über Index". Die Antwort trägt nach dem Vertrag von ExclusionService (`validate()`, `validatePatterns()`) eine Codeliste ohne Bezug zur Zeile; einen Index einzuführen hätte die Schnittstelle von 33-02 geändert. Der Satz steht am Fehlerelement der Liste, der Fokus springt in das Feld der Liste.
2. **Ordner-Map mit fünf Codes:** "jeden der elf Codes je Liste" ist so umgesetzt, dass die Musterliste alle elf trägt und die Ordnerliste die Codes, die `validate()` vergibt (laut 33-WORTLAUT.md B "Ordner: entfällt" für die sechs reinen Muster-Codes); der Vertragstest liest beide Codemengen aus dem Quelltext.
3. **admin.css geändert** (nicht in files_modified): zwei Zeilen untereinander neben dem einen Icon der Bestätigung (`.findling-rules__confirm-line`, Block nur ohne `hidden`).
4. **Diagnose-Fall in AdminViewServiceTest.php** über den Tabelleninhalt `REASON_TEXT` (Reflection), weil `diagnose()` ein Dateisystem braucht; laut Plan als Ergänzung dort und hier in key-files nachgetragen.
5. **Kein SPDX-Kopf in SettingsControllerTest.php:** wie in 33-02 und 33-04, keine PHP-Datei des Repos trägt einen, die Lizenz kommt aus `REUSE.toml`; `reuse lint` konform.
6. **TDD-Reihenfolge:** Die Vertragsfälle wurden nach der Umsetzung geschrieben; Rot ist per Gegenprobe mit den alten Ständen aus `git show HEAD:` belegt (5 rot, Selbsttest grün), nicht per `git stash`.

## Known Stubs

Keine. Die neuen Sätze sind noch nicht in den Katalogen; das ist laut Plan Sache von 33-07 und auf der Seite als englischer Text sichtbar, nicht als leere Stelle.

## Threat Flags

Keine neue Fläche über das Threat Register hinaus. T-33-17 (Route ohne `NoAdminRequired`, unverändert; Gate B grün), T-33-18 (Gate C, nur `textContent`, `p()` im Template, Sätze ohne Wert, Muster in der Bestätigung als Textknoten), T-33-19 (beide Listen vor jedem Schreiben geprüft, PHPUnit "nichts geschrieben" in beide Richtungen), T-33-20 (Logzeilen nur Zähler, Wert-Abwesenheitsprobe über Antwort und Log) umgesetzt.

## Self-Check: PASSED

- FOUND: php/tests/Unit/SettingsControllerTest.php, php/templates/admin.php (findling-rules-patterns), php/js/admin.js (exclusionPatterns 5x)
- FOUND: 2aa25e56
