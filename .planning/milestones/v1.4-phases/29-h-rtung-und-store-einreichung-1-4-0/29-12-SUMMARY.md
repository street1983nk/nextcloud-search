---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 12
subsystem: store-texte, l10n, admin-ui
tags: [REL-04, D-24-04, store, l10n, readme]
requires: [29-02, 29-11]
provides:
  - "Store-Texte 1.4.0 in beiden info.xml (sechs Beschreibungen, wörtlich aus dem abgenommenen Entwurf)"
  - "Gate scan_share_sentence auf den D-24-04-Satz (SHARE_SENTENCE_DE/EN/FR)"
  - "Zeile 'Error class: %s' auf der Diagnosekarte, 16 Kataloge"
affects: [29-13, 29-15]
tech-stack:
  added: []
  patterns: ["Owner-Wortlaut als Konstante im Gate, gezählt genau einmal je Beschreibung"]
key-files:
  created: []
  modified:
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - README.md
    - README.en.md
    - README.fr.md
    - php/lib/Service/AdminViewService.php
    - php/js/admin.js
    - php/templates/admin.php
    - php/l10n/*.js, php/l10n/*.json (16 Dateien)
    - docs/l10n-{french,spanish,italian,dutch,portuguese}.md
    - docs/store-listing.md
    - backend/tests/test_store_metadata.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Fehlerklasse auf der Karte als Schlüssel 'Error class: %s' nach dem Muster 'File ID: %s' (abgenommenes Label wörtlich enthalten, FR mit Leerzeichen vor dem Doppelpunkt)"
  - "Übersetzungen der neuen out_of_memory-Abhilfe und von 'Error class' für es/it/nl/pt_BR/pt_PT (und FR-Abhilfe) folgen dem englischen Text wie bisher; abgenommen sind EN und DE (FR-Label aus Teil 4)"
  - "Die sechs Vorlagetexte oben in docs/store-listing.md auf 1.4.0 nachgezogen, damit Vorlage und info.xml wortgleich bleiben"
metrics:
  duration: "ca. 40 min"
  completed: 2026-10-06
---

# Phase 29 Plan 12: Wörtliche Übernahme der Texte 1.4.0 Summary

Die am 06.10.2026 abgenommenen Texte stehen zeichengleich in beiden `info.xml`, den drei READMEs, der Abhilfe von `out_of_memory`, den 16 Katalogen und den zwei Variablentexten; ein neues Gate hält den D-24-04-Satz in allen sechs Beschreibungen und drei READMEs fest.

## Tasks

| # | Task | Commits |
|---|------|---------|
| 1 | Wörtliche Übernahme in info.xml, READMEs, Labels und l10n | d9969a66 |
| 2 | Gate auf den D-24-04-Satz und Pins (TDD) | 6ab3bac3 (RED), 1e743d25 (GREEN) |

## Zeichengleichheit Entwurf zu Ziel

Vergleichsskript (Gegenprobe über XML-Parser und JSON-Loader, nicht über das Ersetzungsmuster), Ausgabe:

```
GLEICH  php description en (1949 Zeichen)
GLEICH  php description de (2040 Zeichen)
GLEICH  php description fr (2225 Zeichen)
GLEICH  backend description en (1715 Zeichen)
GLEICH  backend description de (1781 Zeichen)
GLEICH  backend description fr (1971 Zeichen)
GLEICH  FINDLING_MAX_CELLS (438 Zeichen)
GLEICH  FINDLING_EXTRACT_ADDRESS_SPACE_BYTES (677 Zeichen)
GLEICH  system_file label EN / remedy EN / label DE / remedy DE
GLEICH  legacy_format label EN / remedy EN / label DE / remedy DE
GLEICH  unsupported_variant label EN / remedy EN / label DE / remedy DE
GLEICH  out_of_memory remedy EN (186 Zeichen)
GLEICH  out_of_memory remedy DE (214 Zeichen)
GLEICH  Error class DE (Fehlerklasse: %s), Error class FR (Classe d'erreur : %s)
GLEICH  README.md / README.en.md / README.fr.md: je drei neue Spiegelstriche (whitespace-normalisiert, weil umbrochen)
ERGEBNIS: alle gleich
```

Die Zeichenzahlen der sechs Beschreibungen stimmen mit der Selbstprüfung des Entwurfs überein (1.949 / 2.040 / 2.225 / 1.715 / 1.781 / 1.971).

Akzeptanz-Greps: `grep -c "Ohne Zutun läuft Findling unverändert sparsam wie bisher." php/appinfo/info.xml` = 1; `grep -c "Only one document is read at a time" backend/appinfo/info.xml` = 0. `RESIDENT_FIGURE = "730.2"` unverändert; jede Beschreibung trägt genau eine Messzahl (Store-Gates grün).

## Verifikation

- Task-1-Tests (store_metadata, admin_ui_contract, info_xml_defaults, lockstep_versions): 191 passed
- RED: 5 neue Tests rot (NameError), GREEN: test_store_metadata 81 passed
- Volle Suite: 4710 passed, 25 skipped (PYTHONUTF8=1)
- ruff check, ruff format --check, pyright (latest) 0 errors, vulture: sauber
- PHP-Pin: `PHP_TREE_HASH_TODAY` f22c3b88... auf 49ed9359... (90 Dateien, unverändert). Paket-Pin 38dab326... (73 Dateien) bleibt, `backend/src` nicht angefasst.
- PHP-Syntax lokal nicht prüfbar (kein PHP, kein Docker): AdminViewService.php (eine Stringzeile) und admin.php (ein `<p>`-Element) sind nur von Python-Gates gesehen. CI-Beleg (PHP-Lint, PHPUnit) folgt in 29-13.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] docs/l10n-*.md-Tabellen nachgezogen**
- **Found during:** Task 1
- **Issue:** `test_every_language_table_carries_every_key_with_the_catalogue_wording` hält die fünf Sprachtabellen zeilengleich mit den Katalogen; neuer Schlüssel der Abhilfe und neuer Schlüssel "Error class: %s" hätten das Gate gebrochen.
- **Fix:** Zeile der Abhilfe ersetzt, Zeile "Error class: %s" nach "File ID: %s" ergänzt, in allen fünf Dokumenten.
- **Commit:** d9969a66

**2. [Rule 3 - Blocking] Schlüsselzahl-Pin in test_admin_ui_contract.py 298 auf 299**
- **Found during:** Task 1, mit Kommentar zur Herkunft. **Commit:** d9969a66

**3. [Auftrag Orchestrator] Fehlerklasse auf der Diagnosekarte eingebaut**
- **Issue:** Offener Punkt aus 29-06; Teil 4 des abgenommenen Entwurfs enthält das Label, der Orchestrator hat den Einbau angewiesen.
- **Fix:** `php/templates/admin.php` ein verstecktes `<p id="findling-diagnosis-errorclass">`, `php/js/admin.js` füllt es per Funktions-Ersetzung (WR-04-Muster) und zeigt es nur bei nicht leerem `errorClass`; Schlüssel "Error class: %s" in 16 Katalogen. Dateien außerhalb von files_modified des Plans.
- **Commit:** d9969a66

**4. [Rule 2 - Drift] docs/store-listing.md: sechs Vorlagetexte und "Stand dieser Datei" auf 1.4.0**
- **Issue:** Die Datei erklärt Vorlage und info.xml für wortgleich; nach der Übernahme hätten die sechs Texte oben noch 1.3.2 getragen.
- **Fix:** Die sechs Texte oben durch die abgenommenen Texte aus Teil 2 ersetzt (maschinell kopiert), Stand-Absatz datiert. Der Entwurfsabschnitt selbst ist unverändert.
- **Commit:** d9969a66

**5. [Rule 1 - Veralteter Kommentar] backend/appinfo/info.xml**
- Kommentar über `FINDLING_MAX_CELLS` sagte "provisional until the owner accepts the text draft of plan 29-02"; jetzt: abgenommen am 2026-10-06. **Commit:** d9969a66

## Known Stubs

Keine.

## Hinweise für den Owner

- Die nicht abgenommenen Übersetzungen (FR-Abhilfe von `out_of_memory`; es, it, nl, pt_BR, pt_PT für Abhilfe und "Error class") sind nach dem bisherigen Muster aus dem englischen Text übertragen, Wortwahl angelehnt an die vorhandenen Katalogzeilen (passage/pasada/passata/doorloop, "Gio" im Französischen).
- Kein Push, nur lokale Commits im Worktree.

## Self-Check: PASSED

- FOUND: php/appinfo/info.xml, backend/appinfo/info.xml, README.md, README.en.md, README.fr.md, php/templates/admin.php, php/js/admin.js
- FOUND: d9969a66, 6ab3bac3, 1e743d25
