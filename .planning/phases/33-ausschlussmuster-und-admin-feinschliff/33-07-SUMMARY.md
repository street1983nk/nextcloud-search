---
phase: 33-ausschlussmuster-und-admin-feinschliff
plan: 07
subsystem: admin-ui, l10n
tags: [pol-03, l10n, catalogues, language-tables, rules-block-gate, hardware-hint, tdd]
requires:
  - "33-01: abgenommener Wortlaut en/de/fr (33-WORTLAUT.md), G5 (c)"
  - "33-05: Musterliste, Fehlersätze je Code, zahlenlose Bestätigung, Diagnose-Abhilfe (englische Schlüssel)"
  - "33-06: Grenzblock Limits per file, Änderungshinweis, B3-Satz (englische Schlüssel)"
provides:
  - "Alle Sätze der Phase 33 in 16 Katalogen und 5 Sprachtabellen, Schlüsselzahl 334"
  - "hardware_short und die sechs weiteren box-Sätze unter neuen Schlüsseln (POL-03, G5 c)"
  - "Gate test_every_sentence_of_the_rules_block_is_in_every_catalogue mit Anti-Leere-Klausel und Selbsttest"
  - "Gate test_no_sentence_of_the_page_says_box_any_more über 23 Dateien und die Schlüssel von de.json"
affects: [33-08, 33-10, 33-11, 36]
tech-stack:
  added: []
  patterns:
    - "Regelblock-Schnitt in zwei Stücken je Datei (Variablen von Block fünf plus Markup bis Dateiende; Regelfunktionen bis zum Profilblock plus Grenzzeilen hinter render())"
    - "Katalogwechsel zeilengenau: Rundlaufprüfung des Zeilenformats vor dem Schreiben, Umbenennung an derselben Stelle, neue Schlüssel hinter einem Ankerschlüssel in .json und .js gleich"
key-files:
  created:
    - .planning/phases/33-ausschlussmuster-und-admin-feinschliff/deferred-items.md
  modified:
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/de.js
    - php/l10n/de.json
    - php/l10n/de_DE.js
    - php/l10n/de_DE.json
    - php/l10n/fr.js
    - php/l10n/fr.json
    - php/l10n/es.js
    - php/l10n/es.json
    - php/l10n/it.js
    - php/l10n/it.json
    - php/l10n/nl.js
    - php/l10n/nl.json
    - php/l10n/pt_PT.js
    - php/l10n/pt_PT.json
    - php/l10n/pt_BR.js
    - php/l10n/pt_BR.json
    - docs/l10n-french.md
    - docs/l10n-spanish.md
    - docs/l10n-italian.md
    - docs/l10n-dutch.md
    - docs/l10n-portuguese.md
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "33-07: Schlüsselzahl 306 auf 334 (28 neu); zehn Sätze wechselten den Schlüssel ohne Zahl: Ordnerhilfe, Diagnose-Abhilfe, B3-Satz, hardware_short und sechs weitere box-Sätze"
  - "33-07: es, it, nl, pt_PT, pt_BR als maschineller Entwurf aus verwandten Katalogwerten (Muster = patrón/modello/patroon/padrão, Deploy = despliegue/distribuzione/uitrol/implementação/implantação), Anrede je Doku wie beim Geschwistersatz"
  - "33-07: Store-Text (info.xml) sagt noch half of the box; nicht geändert, weil Store-Text Owner-Abnahme braucht, als Fund für Phase 36 in deferred-items.md"
requirements-completed: []
metrics:
  duration: "ca. 85 min inkl. Volltestlauf (14:40 min) und ca. 35 min CI"
  completed: 2026-10-14
  tasks: 2
  files: 25
---

# Phase 33 Plan 07: Hardware-Hinweis und alle Sätze der Phase in 16 Katalogen Summary

Der Hardware-Hinweis sagt jetzt, was Findling sieht, welches Profil gemeint ist und dass eine Grenze des Backend-Containers zählt; mit ihm sind die sechs weiteren "box"-Sätze ersetzt (G5 c). Alle 28 neuen Sätze aus 33-05 und 33-06 und die drei geänderten (Ordnerhilfe, Diagnose-Abhilfe, B3) stehen in allen 16 Katalogen und den fünf Sprachtabellen; ein neues Gate liest jeden Satz des Regelblocks gegen jeden Katalog.

POL-03, EXCL-01, EXCL-03 und POL-01 bleiben laut Phasenplan offen bis 33-11 (Abnahme auf der Seite in 33-10).

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | POL-03: Hardware-Satz und sechs box-Sätze in Template, Skript, Test, 16 Katalogen, 5 Dokus | 0fb85deb | admin.php, admin.js, 16 Kataloge, 5 Dokus, test_admin_ui_contract.py |
| 2 | Regelblock-Gate, alle neuen Sätze, Schlüsselzahl, Hash, Commit und CI | 0fb85deb | 16 Kataloge, 5 Dokus, test_admin_ui_contract.py, test_measurement_scripts.py |

Task 1 und 2 laufen laut Plan in einem Commit.

## Umsetzung

- Template und Skript: sieben Schlüsselwechsel (Template 7 Stellen, Skript 4), Wortlaut en zeichengleich aus 33-WORTLAUT.md F, `server's` im PHP-String mit `\'`.
- Kataloge: zeilengenau umgeschrieben. Vorher Rundlaufprüfung über alle 16 Dateien (jede Zeile aus `json.dumps(..., ensure_ascii=False)` neu gebaut ergibt die Datei byte-gleich, 0 Abweichungen). Umbenennungen an derselben Stelle, neue Schlüssel hinter Ankern: Musterliste (5) hinter "No folder is excluded.", Grenzblock (8) hinter dem neuen B3-Satz, Fehlersätze (13) hinter "This path is already excluded.", Bestätigungen (2) hinter der zahlenlosen Ordnerbestätigung. .json und .js gleich, de gleich de_DE.
- de und fr: per Skript gegen 33-WORTLAUT.md geprüft, jeder der 38 Werte steht dort als Tabellenzelle (0 Abweichungen).
- es, it, nl, pt_PT, pt_BR: aus verwandten Werten abgeleitet ("Excluded folders", "Largest file to read", die bisherige Fassung von `hardware_short`, "Remove exclusion %s", die Deploy-Sätze), "the backend" als Dienst wie in jeder Doku, Profilnamen wie im Katalog, Anrede wie beim Geschwistersatz (z. B. es "Introduzca un patrón." wie "Introduzca una ruta de carpeta.").
- Dokus: Tabellenzeilen aus den fertigen Katalogen erzeugt (Zellen zeichengleich), in Dateireihenfolge; datierter "Nachtrag 14.10.2026 (Phase 33, Plan 33-07)" hinter dem Nachtrag von 32-05, ein Absatz für beide Teile (Hardware-Hinweis und Sätze der Muster und Grenzen), Abnahme auf der Seite in 33-10, keine Nennung von 33-09.
- Schlüsselzahl 306 auf 334, Docstring-Absatz "It stands at 334 since 14.10.2026 ... plan 33-07" und Kommentarzeile.
- Baumhash: `PHP_TREE_HASH_TODAY` von `2dbfe17d...` auf `1761f54cdf4b5fe5faf5500b7a01565f82f3fd63e8874ca8260fc913ffce03f9`, `PHP_FILES_TODAY` bleibt 103, Journalabsatz "Moved on 2026-10-14 by Plan 33-07". Gegenprobe unabhängig vom Rezeptskript per Shell (`find`, `LC_ALL=C sort`, `tr -d '\r' | sha256sum`, `printf '%s\0%s\n'`): derselbe Wert.

## Belege

**Task 1 RED** (Test :2983 auf den neuen Satz, neuer Fall `test_no_sentence_of_the_page_says_box_any_more`): **2 failed**.

**Zwischenlauf Task 1 nach de, de_DE, fr** (`-k "catalogue or translation or language_table or hardware or placeholder"`):

```
FAILED tests/test_admin_ui_contract.py::test_every_sentence_of_the_profile_block_is_in_every_catalogue
FAILED tests/test_admin_ui_contract.py::test_every_catalogue_carries_the_same_keys
FAILED tests/test_admin_ui_contract.py::test_every_language_table_carries_every_key_with_the_catalogue_wording
3 failed, 96 passed, 86 deselected in 1.31s
```

Rot nur durch die fehlenden Sprachen und Tabellen (l10n-french.md: 7 fehlende Zeilen). Nach den übrigen Sprachen und Tabellen: **100 passed**; Plan-Prüfungen `grep -l "This box has fewer cores" ...` = 0 Dateien, `grep -c '"[^"]*\bbox\b[^"]*":' php/l10n/de.json` = 0.

**Task 2 RED** (Regelblock-Gate, Abhilfe-Fall): **2 failed**, das Gate mit 480 Befunden (30 fehlende Sätze mal 16 Dateien), die Abhilfe mit `de.json`. Die erste Schwelle `>= 60` der Satzzahl war zu hoch gegriffen (53 Sätze im Schnitt), auf `>= 50` gesetzt.

**Zwischenlauf Task 2 nach de, de_DE, fr:**

```
FAILED tests/test_admin_ui_contract.py::test_every_sentence_of_the_rules_block_is_in_every_catalogue
FAILED tests/test_admin_ui_contract.py::test_the_remedy_of_an_excluded_file_is_in_every_catalogue
FAILED tests/test_admin_ui_contract.py::test_the_german_catalogue_covers_both_german_language_codes
FAILED tests/test_admin_ui_contract.py::test_every_catalogue_carries_the_same_keys
FAILED tests/test_admin_ui_contract.py::test_every_language_table_carries_every_key_with_the_catalogue_wording
5 failed, 96 passed, 86 deselected in 0.73s
```

Erwartet: fehlende Sprachen, Tabellen und die Schlüsselzahl (334 statt 306). Danach `test_admin_ui_contract.py tests/test_public_artifacts.py`: nur die Schlüsselzahl rot (`assert 334 == 306`), nach dem Nachziehen grün.

**Gegenproben (nicht mit dem Muster der Umsetzung):**
- Mutation: Zeile "Steps in the documentation" aus `nl.js` entfernt, das Regelblock-Gate meldet genau `nl.js: lacks 'Steps in the documentation'`; Datei zurück, `cmp` gleich.
- Eigener Quellenscan (Regex über Template, Skript, AdminViewService gegen de.json): kein `t()`-Satz ohne Schlüssel; kein Katalogschlüssel ohne Fundstelle im PHP- oder JS-Quelltext außer den fünf zusammengesetzten Pluralschlüsseln (keine Waisen).
- Zeichenprüfung U+2013, U+2014, U+2019, U+00A0, U+202F über alle geänderten Dateien: 0 Funde, mit Positivkontrolle (je 1 Treffer auf einer Probe mit Geviertstrich und geschütztem Leerzeichen). Französisch damit mit normalem Leerzeichen vor dem Doppelpunkt.
- `grep -n "33-09" docs/l10n-*.md`: leer. `Excluded patterns` in 16 von 16 Katalogdateien, de.json:168 `"Ausgeschlossene Muster"`.

**Gates lokal (backend/, PYTHONUTF8=1):** pytest **5680 passed, 159 skipped** (14:40 min); ruff check im ersten Lauf 3 Befunde ISC004 (implizite Verkettung in Tupeln der neuen Tests) und 1 Datei unformatiert, geklammert und formatiert, danach grün; ruff format --check 222 Dateien; pyright 0 errors (latest); vulture leer; reuse lint 2727/2727; `node --check php/js/admin.js` grün; PHPL-Block (php:8.3-cli) grün. Nach der Klammerung liefen Vertrag und Messskripte erneut: 664 passed.

## CI (0fb85deb)

Alle mit `gh run watch <id> --exit-status` bis zum Ende beobachtet, alle grün:

- PHP and store metadata gates 38527058335 (PHPUnit OK, 789 Tests, 2947 Assertions)
- Python gates 38527058311 (5691 passed, 148 skipped)
- Security scans 38527058262
- OpenSSF Scorecard 38527058461
- Resilience 38527058304 (zweiter Watch-Aufruf)
- Multi-arch image 38527058265
- Integration 38527058337
- HaRP deploy 38527058332 (dritter Watch-Aufruf, die ersten liefen in die lokale Zeitgrenze)

Erste Liste direkt nach dem Push leer, zweiter Aufruf mit 8 Läufen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Regel 1 - Bug] Schwelle der Anti-Leere-Klausel**
- **Gefunden in:** Task 2, RED
- **Problem:** Die erste Schwelle `>= 60` lag über der echten Satzzahl des Regelblocks (53).
- **Fix:** `>= 50`; die Klausel nennt zusätzlich 27 Sätze namentlich, darunter jeden Fehlersatz, beide Bestätigungen und den Grenzblock.
- **Commit:** 0fb85deb

### Weitere Abweichungen

1. **Sieben statt ein Satz in Task 1:** laut Vermerk im Plan (G5 c); dazu ein Fall, der über 23 Dateien jeden der sieben alten Sätze sucht und kein Wort "box" in den Schlüsseln von de.json duldet.
2. **Ein Nachtrag je Doku statt zwei:** Beide Plan-Einträge (Task 1 und Task 2) stehen in einem datierten Absatz, weil sie im selben Commit landen.
3. **Plan-Interfaces mit alten Zeilennummern:** `admin.php:1072` stand nach 33-05/33-06 bei 1183, `admin.js:1449` bei 1709; die Schlüssel wurden über den Satztext gefunden, nicht über die Zeile.
4. **TDD-Reihenfolge:** RED je Task vor der Umsetzung gefahren (Test zuerst, dann Template, Skript, Kataloge); kein `git stash`.

## Deferred Issues

- Store-Text `php/appinfo/info.xml:67` und `backend/appinfo/info.xml` sagen "half of the box"; `docs/store-listing.md:1367` begründet das mit dem nun ersetzten Satz der Seite. Store-Text braucht Owner-Abnahme, deshalb nach `deferred-items.md` für Phase 36.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-33-23: `test_no_catalogue_value_can_break_the_page` und `test_no_catalogue_value_loses_or_invents_a_placeholder` grün über alle 16 Dateien. T-33-24: neues Regelblock-Gate mit Anti-Leere-Klausel, Selbsttest und Mutationsprobe.

## Self-Check: PASSED

- FOUND: backend/tests/test_admin_ui_contract.py (def test_every_sentence_of_the_rules_block_is_in_every_catalogue, == 334)
- FOUND: php/l10n/de.json ("Excluded patterns": "Ausgeschlossene Muster")
- FOUND: .planning/phases/33-ausschlussmuster-und-admin-feinschliff/deferred-items.md
- FOUND: 0fb85deb
