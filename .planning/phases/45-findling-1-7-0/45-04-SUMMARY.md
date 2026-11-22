---
phase: 45-findling-1-7-0
plan: 04
subsystem: php-companion (ExclusionService, Admin-Seite Regelblock, Kataloge, Sprachtabellen)
tags: [excl-05, excl-06, admin-page, l10n, zh_TW, tdd]
requires: [45-01, 45-03]
provides:
  - "ExclusionService::ERROR_WILDCARD = 'wildcard': neuer Ordnereintrag mit * oder ? abgewiesen, gespeicherter geduldet (Vergleich gegen prefixes() wie newPrefixes())"
  - "Zähler #findling-rules-slots und #findling-rules-patterns-slots (Server-Startwert, Script aktualisiert, Klasse findling-rules__slots--low bei 1 und 0, einmalige Ansage in #findling-rules-announce)"
  - "Markierung findling-rules__row-warning für gespeicherte Ordnerzeilen mit * oder ? (Server) und versteckt in der Zeilenvorlage (Script zeigt sie nach Neuaufbau)"
  - "Neuer no_wildcard-Satz; alter Schlüssel aus allen 18 Katalogen und 6 Sprachtabellen entfernt"
affects: [45-05, 45-10]
tech-stack:
  added: []
  patterns: ["Fehlercode nur für noch nicht gespeicherte Einträge (Duldung beim Upgrade)", "Zählersätze als t() im Script-Gate-Bereich, nicht als data-Attribute"]
key-files:
  created: []
  modified:
    - php/lib/Service/ExclusionService.php
    - php/tests/Unit/ExclusionServiceTest.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/css/admin.css
    - php/l10n/*.js, php/l10n/*.json (18 Dateien)
    - docs/l10n-french.md, -spanish.md, -italian.md, -dutch.md, -portuguese.md, -chinese.md
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Zählersätze als t('findling', ...) im Script statt als data-Attribute: dieselbe Zwei-Hälften-Form wie die Fehler-Maps, der Katalog-Gate liest beide Hälften, und Gate C bleibt unberührt (nur text(), classList, Attribute)"
  - "Beispiel im wildcard-Satz Backup* statt Archiv* (Abweichung vom UI-SPEC-Vorschlag, dort ausdrücklich Claude's Discretion): Archiv ist der gesperrte Begriff des Vokabular-Gates in docs/, und die Sprachtabellen tragen den Satz in jeder Spalte"
  - "Zeilenvorlage trägt die Markierung versteckt, damit applyRules() nach dem Speichern die Markierung gespeicherter *-Einträge nicht verliert; gezeigt nur für die Ordnerliste"
  - "Zähler bleibt bei Grenze 0 verborgen (Server und Script), eine Liste über der Grenze zählt als voll"
  - "patternErrorSentences wird gegen die Codes von validatePatterns() und normalisePattern() geprüft (pattern_validation_codes), nicht mehr gegen alle ERROR_*-Konstanten; Ordnercodes jetzt 6, Konstanten gesamt 12"
  - "Schlüsselzahl de.json 366 -> 371 (sechs neu, einer weg), Absatz im Gate-Docstring nachgeschrieben"
metrics:
  duration: "ca. 35 min laut Systemzeit (bis 02:55 UTC), davon ca. 15 min Docker (PHPUnit, Psalm 33/34/35, cs-fixer, zizmor, actionlint) und ca. 5 min PHP-lesende pytest-Läufe"
  completed: 2026-11-22
---

# Phase 45 Plan 04: Freie Plätze und klare Antwort auf * oder ? im Ordnerfeld (EXCL-05, EXCL-06) Summary

Server weist neue Ordnereinträge mit * oder ? mit `wildcard` ab und duldet gespeicherte; beide Listen zeigen freie Plätze (64/32 aus `data-max-entries`), alte *-Einträge sind markiert, `no_wildcard` nennt beide Wege, alles in 9 Sprachen (18 Kataloge, 6 Tabellen) in einem Commit.

## Commit

| Task | Name | Commit |
|------|------|--------|
| 1 bis 3 | Server, Template, Script, Stil, Gates, alle Kataloge und Tabellen (Commit-Schnitt des Plans: ein Commit) | 08eaa058 |

Task 1 und 2 haben ihre Teil-Gates lokal geprüft und nicht committet.

## Server (Task 1)

`validate()` in `php/lib/Service/ExclusionService.php`:

```php
if (str_contains($normalised, self::STAR) || str_contains($normalised, self::ANY)) {
	$inForce ??= $this->prefixes();
	if (!in_array($normalised, $inForce, true)) {
		$errors[] = self::ERROR_WILDCARD;
		continue;
	}
}
```

Gleicher Vergleich wie `newPrefixes()` (normalisiert gegen `prefixes()`), daher wird `/a*b/` neben gespeichertem `a*b` ebenfalls geduldet. `normalisePattern()` unverändert. Antwort und Logzeilen tragen nur den Code bzw. den Zähler (T-45-17).

TDD: RED mit unveränderter Service-Datei (7 Fehler, `ERROR_WILDCARD` fehlt), GREEN 82 Tests / 219 Assertions. Neue Fälle: `Archiv*`, `Proj?kt`, `Team/*/Export` -> `['wildcard']` ohne Wert in Antwort und Log; derselbe Fall wird nicht geschrieben; gespeichertes `a*b` geduldet und mit `Backups` gespeichert; `['a*b', 'c*']` -> nur `wildcard`; `/a*b/` geduldet; `Backups` und `Fotos (2024)/Urlaub` erlaubt. `testStoredPrefixesStayByteForByteAndAStarInThemIsLiteral` grün.

## Seite

- Template: `wildcard` in `$folderErrorSentences`, neuer `no_wildcard`; `$slotsLine()` wählt 0/1/sonst; zwei `p.settings-hint.findling-rules__slots` zwischen `.findling-rules__add` und Feldfehler, `aria-describedby` der Felder nennt sie; `#findling-rules-announce` (`role="status"`, `aria-live="polite"`); Markierung per `str_contains` mit `$alertIcon` und Satz, ohne Klasse `findling-rules__prefix`; Zeilenvorlage mit versteckter Markierung.
- Script: `setupExclusionList()` im Code-Muster (`empty`, `wildcard`, `duplicate`, `too_long` in Bytes per `TextEncoder`, `too_many`), Eingabe bleibt stehen; `fieldError()` setzt, `clearFieldError()` entfernt `aria-invalid`; `refreshSlots()` hängt an `refreshEmptyState()` (also Add, Remove, applyRules, Setup), Funktions-Replacements gegen `$&`, Ansage nur beim Wechsel auf 1 oder 0.
- CSS: `.findling-rules__row` mit `flex-wrap: wrap`, `.findling-rules__row-warning` (volle Breite, `--color-warning-text`, Icon `--color-element-warning`, keine Fläche), `.findling-rules__slots` und `--low`; nur Variablen, keine Farb- oder Pixelliterale (Diff-Grep leer).

## Gates

- `test_admin_ui_contract.py`: `pattern_validation_codes()` mit `method_body()`; Ordnercodes 6, Konstanten 12, Vereinigung beider Listen = alle Konstanten; Selbsttest `test_the_code_readers_see_a_code_the_server_learns` mit handgebautem Fehl-Sample (B8); `test_the_slots_lines_and_the_row_warning_stand_where_the_ui_spec_puts_them` mit drei Fehl-Samples (Zähler unter dem Fehler, Markierung mit Eintragsklasse, fehlende Ansage); `test_the_folder_field_refuses_a_wildcard_and_keeps_what_was_typed`; Anti-Vakuum-Liste auf neue Sätze umgestellt, alter `no_wildcard`-Satz darf weder im Regelblock noch in einem Katalog stehen; Schlüsselzahl 371.
- Baumhash PHP 136/47251647 (Rezept und unabhängige Pipeline find, sort, sed, sha256sum gleich; Positivkontrolle über git archive a6965647 = c0a27412).

Lokal grün vor dem Commit: PHPUnit voll 1277 Tests; `php_gates_docker.sh all` (Exit 0); `test_admin_ui_contract.py` 217, `test_measurement_scripts.py` 572, `test_public_artifacts.py` grün, dazu alle 16 PHP/l10n-lesenden pytest-Dateien (1466 passed vor dem Baumhash- und Vokabular-Fix, danach die zwei betroffenen Dateien erneut grün); ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture.

## Übersetzungen

DE und FR aus dem UI-SPEC (bis auf das Beispiel Backup*), übrige Sprachen nach den Glossaren der docs/l10n-*.md: Ortsangaben mit den Katalogwerten ("Patrones excluidos", "Modelli esclusi", "Uitgesloten patronen", "Padrões excluídos", 「排除的樣式」), Anrede wie im Bestand (es usted, it/nl/pt Infinitiv, zh_TW 請), zh_TW mit Vollbreiten-Zeichensetzung, 「」 und Halbbreiten-Leerzeichen zwischen Han und Latein/Ziffern/Platzhaltern. Platzhalter-Parität per Gate geprüft, keine U+2013/U+2014 in den neuen Werten.

Umlaut-Audit der neuen de/de_DE-Werte (Vorfilter `(ae|oe|ue)[a-z]|ss[^a-z]`): ein Treffer, "neuen" in "Einen Eintrag entfernen, um einen neuen hinzuzufügen.", korrektes ue, kein Ersatz. Umlaute in "enthält", "Für", "hinzuzufügen" echt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Vokabular-Gate in docs/ rot durch das Beispiel Archiv***
- **Found during:** Task 3 (test_public_artifacts.py, Familie vokabular, vier Sprachtabellen)
- **Issue:** Der UI-SPEC-Satz "For a pattern like Archiv* ..." bringt den gesperrten Begriff in jede Tabellenzeile (Schlüssel, DE, Ziel).
- **Fix:** Beispiel in Quelle und allen Übersetzungen auf Backup* gestellt (UI-SPEC Zeile 196: Wortlaut innerhalb D-45-08 ist Claude's Discretion). Keine neuen Ausnahmen.
- **Commit:** 08eaa058

**2. [Rule 3 - Blocking] Schlüsselzahl und Baumhash nachgezogen**
- `test_the_german_catalogue_covers_both_german_language_codes` 366 -> 371 mit Begründungsabsatz; Baumhash-Konstante mit Herkunftsabsatz.

**3. [Rule 2] Markierung auch nach dem Speichern**
- Plan sah die Markierung nur serverseitig vor; `applyRules()` baut die Liste nach dem Speichern neu und hätte sie verloren. Zeilenvorlage trägt sie versteckt, `addRow()` zeigt sie nur in der Ordnerliste.

**4. [Rule 2] Zähler bei fehlender Grenze**
- Grenze 0 (View liefert keine) blendet den Zähler aus, statt "0 frei" zu behaupten.

## Hinweise

- `docs/l10n-chinese.md` nennt in der Zählung vom 15.11.2026 noch 366 Schlüssel und alte Satzzeichen-Zählungen; das ist ein datierter Stand, kein Gate prüft ihn. Nachzählen gehört in die Doku-Runde (45-10 oder Release-Vorbereitung).
- `docs/l10n-chinese.md` Zeile 128 enthält seit PR #56 das Zeichen U+2014 als Beschreibung der verbotenen chinesischen Typografie; daher schlägt die Plan-Verifikation `! grep ... docs/l10n-*.md` an. Bestand, nicht von diesem Plan, nicht geändert.
- Ein Leer-Aufruf `python -I -c "print()"` lief einmal versehentlich bei der Pfadsuche (Owner-Regel "nie python -c"); ohne Wirkung, sonst nur Skriptdateien im Scratchpad.
- Playwright (Zähler bei 2/1/0, Feldfehler wildcard, Markierung, no_wildcard, zh_TW) und impeccable-Audit folgen in 45-10.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche: keine neue Route, kein neuer Lesepfad. T-45-15 (Duldung), T-45-16 (nur p(), Textknoten, Funktions-Replacements), T-45-17 (nur Codes und Zähler) umgesetzt und getestet.

## Self-Check: PASSED

- 08eaa058 vorhanden, Autor street1983nk, keine Session-Zeile, kein offener Diff in php/, docs/, backend/tests/.
- Alle 18 Kataloge enthalten "Folders take no * or ?" und nicht mehr den alten no_wildcard-Satz.
