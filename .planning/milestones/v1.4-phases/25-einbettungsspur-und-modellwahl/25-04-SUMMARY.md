---
phase: 25-einbettungsspur-und-modellwahl
plan: 04
subsystem: php-adminseite
tags: [admin, l10n, modellwahl, praezision, neueinbettung]
requires: []
provides:
  - "AdminViewService::backend() liefert precisionActive und reembedRunning (Vertrag Plan 25-12)"
  - "Statuszeile findling-semantic-model in Template und Poll-Skript"
  - "Zwei neue Katalogschlüssel in allen 16 Dateien, Gate auf 207"
affects:
  - "Plan 25-12 (Container muss model.precisionActive und model.reembedRunning liefern)"
  - "Plan 25-05 (PHP-Pins neu messen nach Welle 1)"
tech-stack:
  added: []
  patterns: ["geschlossene Menge statt Cast (engineState-Muster)", "Modellname seitenseitig gebaut"]
key-files:
  created: []
  modified:
    - php/lib/Service/AdminViewService.php
    - php/tests/Unit/AdminViewServiceTest.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/*.json, php/l10n/*.js (16 Dateien)
    - backend/tests/test_admin_ui_contract.py
decisions:
  - "Fortschrittsteil der Zeile nur mit Nenner (hasEmbeddedFraction); ohne Nenner zeigt die Zeile nur das Modell"
  - "nl 'Model: %1$s' ist als begründete G2-Ausnahme eingetragen (gleiches Wort im Niederländischen)"
  - "Neueinbettung übersetzt als Neuberechnung der Vektoren (fr recalcul des vecteurs, es/pt recálculo, it ricalcolo, nl vectoren opnieuw berekenen), da kein Katalog ein Wort für Einbettung führte"
metrics:
  duration: "ca. 35 min"
  completed: 2026-09-28
  tasks: 2
  files: 21
---

# Phase 25 Plan 04: Modellzeile auf der Statusfläche Summary

Die Adminseite zeigt im Block "Auffindbar nach Bedeutung" eine Zeile "Modell: e5-small fp32, Neueinbettung 42 % (12.300 von 29.100)", gespeist aus `model.precisionActive` und `model.reembedRunning` der Container-Antwort, geprüft gegen geschlossene Mengen und bei älteren Containern verborgen.

## Was gebaut wurde

- **Task 1** (`77acf6a` RED, `ae47384` GREEN): `AdminViewService` bekommt `PRECISIONS = ['int8', 'fp32']` und drei statische Helfer: `modelField()` (robust gegen fehlendes oder nicht-array `model`), `precision()` (geschlossene Menge, kein Cast) und `strictFlag()` (nur echtes bool, sonst null). `backend()` liefert jetzt 27 Schlüssel; der Null-Zweig läuft über denselben Codepfad und ergibt für beide neuen Felder null. Der Docblock nennt den Vertrag von Plan 25-12. PHPUnit-Fälle für gültige Werte, fehlendes model-Objekt und ungültige Werte (fp16, 3, '', 'yes', 1, ...).
- **Task 2** (`c49a61a`): Template-Zeile `<p class="settings-hint" id="findling-semantic-model">` nach der Subline, hidden bei fehlender Präzision, Ausgabe über `p()`. Der Modellname wird auf der PHP- und JS-Seite aus `{int8, fp32}` gebaut, nie roh durchgereicht (T-25-14). Prozent im Format der semantischen Kennzahl (` %`), Zähler über `$count` bzw. `numbers.format`. In `admin.js` neue Funktion `modelLine()`, aufgerufen aus `coverageBlock()`. Zwei Schlüssel in allen 16 Katalogen, Gate von 205 auf 207 mit Begründungsabsatz.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Korrektheit] Fingerprint des Polls um die zwei Felder erweitert**
- **Found during:** Task 2
- **Issue:** `render()` wird übersprungen, wenn sich der Fingerprint nicht ändert; ein Start oder Ende der Neueinbettung bei sonst stehenden Zahlen hätte die Zeile nie aktualisiert.
- **Fix:** `precisionActive` und `reembedRunning` in `fingerprint()` aufgenommen.
- **Commit:** c49a61a

**2. [Rule 3 - Blocker] G2-Ausnahme für nl "Model: %1$s"**
- **Found during:** Task 2
- **Issue:** Das Vollständigkeitsgate G2 meldet Werte, die ihrem englischen Schlüssel gleichen; im Niederländischen ist "Model: %1$s" korrekt und gleich.
- **Fix:** Begründeter Eintrag in `VALUES_THAT_MAY_EQUAL_THEIR_KEY["nl"]`.
- **Commit:** c49a61a

**3. [Rule 2] Zusätzliche Kontrakttests**
- `test_both_halves_of_the_page_carry_the_model_line` (Id, Schlüssel, Modellnamen, Fingerprint, alle 16 Kataloge) und die zwei neuen Schlüssel in `test_every_new_status_key_has_exactly_one_line_in_the_service`.
- **Commits:** ae47384, c49a61a

**4. [Rule 1] Geschütztes Leerzeichen als Escape**
- Das Edit-Werkzeug hatte in `admin.js` ein literales U+00A0 geschrieben; das Gate IN-03 verlangt die Escape-Schreibweise. Auf `' %'` korrigiert vor dem Commit.

## Deferred Issues

- Die Tabellen in `docs/l10n-spanish.md`, `docs/l10n-italian.md`, `docs/l10n-dutch.md`, `docs/l10n-portuguese.md` und `docs/l10n-french.md` führen die zwei neuen Zeilen noch nicht (nicht in `files_modified` des Plans; im Gate-Absatz vermerkt). Die Übersetzungen außerhalb Deutsch/Englisch sind maschinell, unter demselben Vorbehalt wie der Rest.
- PHPUnit läuft nur in CI; lokal nur `php -l` (Docker, php:8.3-cli) für Service, Test und Template, sowie `node --check` für `admin.js`.

## Verification

- `uv run pytest -q tests/test_admin_ui_contract.py`: 55 passed
- Volle Suite mit `--deselect tests/test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_php_half`: 3495 passed, 15 skipped
- ruff check, ruff format, pyright auf der geänderten Testdatei grün
- Akzeptanz-greps: `'precisionActive'` 2x, `'reembedRunning'` 2x, `twenty-five` 0x, `findling-semantic-model` 1x Template / 2x JS, 16 Katalogdateien mit dem Schlüssel, `== 207` 1x
- PHP-Pins nicht geändert (Plan 25-05 misst nach Welle 1 neu)

## Known Stubs

Keine. Die Zeile bleibt verborgen, bis der Container (Plan 25-12) die Felder liefert; das ist die geplante Rückwärtsverträglichkeit, kein Stub.

## TDD Gate Compliance

RED `77acf6a` (test), GREEN `ae47384` (feat) für Task 1. Task 2 als ein feat-Commit, der Kontrakttest kam mit der Umsetzung, da der Gleichstand der Kataloge sonst zwischen zwei Commits rot wäre.

## Self-Check: PASSED

- FOUND: php/lib/Service/AdminViewService.php, php/templates/admin.php, php/js/admin.js, 16 Katalogdateien
- FOUND: 77acf6a, ae47384, c49a61a
