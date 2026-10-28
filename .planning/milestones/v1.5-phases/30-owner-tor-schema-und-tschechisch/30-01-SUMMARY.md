---
phase: 30-owner-tor-schema-und-tschechisch
plan: 01
subsystem: index/analyzer
tags: [czech, stopwords, lucene, analyzer, cz-02, licence]
requires: []
provides:
  - "findling.index.stopwords_cs: CZECH_STOPWORDS_FOLDED (167), CZECH_EXCEPTIONS (byt, jez)"
  - "findling.index.analyzer: TOKENIZER_CS, czech_analyzer()"
  - "scripts/dev/czech_stopwords.py: Generator mit SHA-256-Sperre"
affects: [30-04 body_cs, Schema 3, Tokenizer-Registrierung]
tech-stack:
  added: []
  patterns: ["stemmerlose Kettenfabrik außerhalb SNOWBALL_NAME", "vendiertes Original mit -text und SHA-256-Pin"]
key-files:
  created:
    - backend/src/findling/index/stopwords_cs.py
    - backend/tests/test_czech_analyzer.py
    - backend/tests/fixtures/lucene_cz_stopwords_10_5_2.txt
    - scripts/dev/czech_stopwords.py
  modified:
    - backend/src/findling/index/analyzer.py
    - backend/tests/test_measurement_scripts.py
    - THIRD-PARTY.md
    - REUSE.toml
    - .gitattributes
decisions:
  - "D-30-05 umgesetzt: zwei benannte Ausnahmen, byt (Wohnung) und jez (Wehr); 65 übrige neue Formen keep"
  - "Kein achtes Versionsmerkmal, ANALYZER_VERSION bleibt 1; Digest nur als CZECH_FOLDED_SHA256 im Test"
metrics:
  duration: "ca. 21 min (davon 10,6 min volle Suite)"
  completed: 2026-10-10
  tasks: 3
  files: 9
---

# Phase 30 Plan 01: Tschechische Stoppliste und Kette cs Summary

Gefaltete Lucene-10.5.2-Stoppliste (167 ASCII-Einträge, Ausnahmen `byt` und `jez`) plus stemmerlose Kette `czech_analyzer()` mit SHA-256-gesperrtem Generator, Apache-2.0-Beleg und nachgezogenem Paket-Baumhash.

## Ergebnis

- Original byte-gleich vendiert, SHA-256 `61f06aa1...ad915` geprüft (172 Zeilen, 171 eindeutig, 169 gefaltet).
- `czech_analyzer()`: simple, lowercase, ascii_fold, custom_stopword, remove_long(48). Kein Stemmer, kein `Filter.stopword`; per AST-Test festgehalten.
- Gemessen: `Smlouvě smlouve SMLOUVĚ smlouva` ergibt `smlouve` x3 + `smlouva`; `Nájemní smlouva na byt` ergibt `najemni, smlouva, byt`; `smluvní strana` ergibt `smluvni`; jeder Listeneintrag in beiden Schreibweisen leer (außer Ausnahmen).
- Digest der Liste: `624ac83b125c1ff3bffdddd7b97cfd1979217c08f2fb964b03a17c1cf26d0455` (nur im Test).
- Baumhash `85d26511...f295`, `PACKAGE_FILES_TODAY` 73 auf 74.
- Gates: volle Suite 4728 passed / 25 skipped, ruff, ruff format, pyright (auch Generator), vulture, `reuse lint` (3.3 konform) grün.

## Prüftabelle und Ausnahmen

67 neu entstandene Formen, jede per en.wiktionary.org (10.10.2026, Batch-Abfrage der akzentlosen Form) geprüft. Czech-Einträge der akzentlosen Form gab es nur bei vier Formen:

| Form | Original | Urteil | Grund |
|---|---|---|---|
| byt | být (sein) | exception | `byt` = Wohnung, häufig in Mietverträgen |
| jez | jež (welcher, Relativpronomen) | exception | `jez` = Wehr, eigenständiges Inhaltswort |
| mate | máte (ihr habt) | keep | auch 3. Sg. von mást (verwirren), selten |
| pres | přes (über) | keep | auch umgangssprachlich "Presse", selten |

Alle übrigen 63 sind nur die akzentlose Schreibweise desselben Wortes (keep). Volle Tabelle im Docstring von `stopwords_cs.py` (ASCII, Akzente ausgeschrieben) und in THIRD-PARTY.md (mit Akzenten); ein Test hält sie gegen die Generator-Ausgabe und die exception-Zeilen gegen `CZECH_EXCEPTIONS`.

**Ausnahme außer `byt`: `jez`** (aus `jež`, Bedeutung der akzentlosen Form "Wehr"). Owner kann per Veto zurückdrehen: Eintrag aus `EXCEPTIONS` im Generator entfernen, Generator laufen lassen, Digest nachziehen.

## Commits

| Commit | Inhalt |
|---|---|
| 094885e3 | test(30-01): RED, nur `test_czech_analyzer.py` (ImportError `TOKENIZER_CS`) |
| cf49e6db | feat(30-01): GREEN-Bündel mit allen übrigen Dateien und Baumhash |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Messabweichung] 67 statt 66 neu entstandene Formen**
- **Found during:** Task 1
- **Issue:** Research nannte 66; Generator (tantivy-Faltung) und unabhängige unicodedata-Gegenzählung ergeben beide 67.
- **Fix:** Tabelle hat 67 Zeilen; Abnahmekriterium ist "gleich Generator-Ausgabe", per Test gesichert. Zahl in THIRD-PARTY.md begründet.
- **Commit:** cf49e6db

**2. [Rule 1 - Bug im Test] Grenze von remove_long**
- **Found during:** Task 2 (GREEN)
- **Issue:** tantivy `remove_long(48)` behält nur Tokens mit weniger als 48 Zeichen; der RED-Test erwartete 48 als behalten.
- **Fix:** Test prüft 47 bleibt, 48 und 49 fallen (gemessen). Die Testdatei reist deshalb mit einer 5-Zeilen-Korrektur auch in Commit B.
- **Commit:** cf49e6db

**3. [Rule 2 - Integrität] `.gitattributes`-Regel `-text` für das Original**
- **Found during:** Task 1
- **Issue:** `core.autocrlf=true` auf der Entwicklungsmaschine hätte beim nächsten Checkout CRLF eingesetzt und den SHA-256-Pin gebrochen (Generator bricht dann ab).
- **Fix:** Regel nach Muster `testdata/corpus/** -text`; `git ls-files --eol` zeigt `i/lf w/lf attr/-text`.
- **Commit:** cf49e6db

**4. [Ergänzung] zweite Ausnahme `jez`** nach dem festgelegten Kriterium (siehe oben); Ergebnis 167 statt 168 Einträge.

## Nicht erledigt / bewusst ausgelassen

- `requirements.mark-complete CZ-02` NICHT ausgeführt: der Plan liefert nur den Stoppwort-Teil von CZ-02 (Erfolgskriterium "CZ-02 Teil Stoppwörter"); Feld und Registrierung folgen in 30-04. Zudem trägt `.planning/REQUIREMENTS.md` eine fremde, nicht committete Änderung (STR-02-Pflichtpunkte, Owner-Frage 10.10.), die ich nicht mitcommitte.
- Kein Push (Plan verlangt keinen CI-Beweis).

## Self-Check: PASSED

- Dateien vorhanden: stopwords_cs.py, czech_stopwords.py, Fixture, test_czech_analyzer.py
- Commits 094885e3 und cf49e6db im Log
