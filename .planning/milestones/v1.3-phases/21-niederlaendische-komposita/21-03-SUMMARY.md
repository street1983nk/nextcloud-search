---
phase: 21-niederlaendische-komposita
plan: 03
subsystem: index/analyzer, index/wordlist_nl
tags: [komposita, nl, splitter, rezept-b, d-02, d-05]
requires: ["21-01"]
provides:
  - wordlist_nl.py (Rezept B 4-14, Artefakt fail closed, Digest-Cache, Sprachgate, dutch_mark)
  - analyzer.dutch_analyzer, cached_dutch_analyzer, dutch_build_count, dutch_chain_for
affects: [21-04, 21-05, 21-06, 21-07]
tech-stack:
  added: []
  patterns: [Geschwistermodul statt Umbau, Liste per tantivy-Fold gefaltet, nur Digest gecacht, eigene Kettenversion statt ANALYZER_VERSION]
key-files:
  created:
    - backend/src/findling/index/wordlist_nl.py
    - backend/tests/test_wordlist_nl.py
    - backend/tests/test_dutch_analyzer.py
  modified:
    - backend/src/findling/index/analyzer.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_readonly_gate.py
decisions:
  - "dutch_digest_for liest SYSTEM_WORDLIST_NL zur Aufrufzeit (nicht als Default gebunden), damit Tests und Messwerkzeuge die Quelle umlenken können"
  - "build_artifact_nl liest bei jedem Aufruf (Einträge werden nie gecacht, D-02); nur dutch_digest_for antwortet aus dem Cache"
  - "Read-only-Gate: (index/wordlist_nl.py, mkdir) als geprüfte Ausnahme, gleiche Begründung wie wordlist.py"
metrics:
  duration: ca. 45 min
  completed: 2026-09-25
  tasks: 2 von 2
---

# Phase 21 Plan 03: Niederländisches Rezept und Splitterkette Summary

Rezept B 4-14 (gefaltete Liste plus Tussenklanken s, e, en) als isoliertes Modul `wordlist_nl.py` und die niederländische Splitterkette hinter der Faltung in `analyzer.py`; kein Aufrufer im Container benutzt beides bisher, `ANALYZER_VERSION` bleibt 1.

## Task 1: wordlist_nl.py (RED 6972d0d, GREEN 9f69621)

- Faltung ausschließlich über einen modulweiten tantivy-Analyzer `simple -> lowercase -> ascii_fold`, genau ein Token je Zeile; kein `unicodedata`.
- Quelle zeilenweise (`split("\n")`), Fenster 4 bis 14 auf die ungefaltete Länge, `isalpha`, dann `TUSSENKLANKEN`.
- Artefakt `dict/nl-full.txt` plus `.sha256`, fail closed wie im deutschen Modul; Cache `_CACHED_DIGESTS` hält nur den Digest unter `(path, digest, size, mtime_ns)`.
- `dutch_digest_for` ohne nl: `None`, kein Dateizugriff; `dutch_mark`: `off` oder `1:<digest>`; `measure()` gibt nur Zahlen aus.
- Importgrenze: `wordlist_nl` importiert das Analyzer-Modul nicht (grep 0).
- Baumhash: 57 Dateien, datierter Kommentarabsatz.
- 14 Tests (die neun aus dem Plan plus Fensterrand, Artefaktpfad, Erstbau).

## Task 2: Splitterkette (RED 2c40037, GREEN 0d4ba89)

- `dutch_analyzer`: lowercase, ascii_fold, split_compound, custom_stopword(TUSSENKLANKEN), stopword("dutch"), custom_stopword(FOLDED_STOPWORDS["dutch"]), remove_long(48), stemmer("dutch"), mit Logzeile und Zähler.
- `cached_dutch_analyzer` (ein Eintrag), `dutch_chain_for(None)` gibt die unveränderte `snowball_analyzer("dutch")`, ein Digest, den das Volume nicht trägt, wirft `ValueError` ohne Pfad.
- Modul-Docstring: benannte Ausnahme `wordlist_hash_nl` plus `DUTCH_CHAIN_VERSION` statt ANALYZER_VERSION (D-05, rund 19 h Vollreindex), dazu die Kettentabelle.
- 8 Tests: AST-Wächter mit Reihenfolge UND Argumenten beider custom_stopword-Filter, Gegenprobe Splitter vor Fold, `gemeentebelastingen -> gemeent, belast` (auch großgeschrieben), `coördinatiecentrum` gleich der flachen Schreibung, kein Tussenklank-Rest bei `waterschapsbelasting`, Singleton, Snowball-Fallback, fail closed, Versionspin.

## Verifikation

- Volle Backend-Suite: 2911 passed, 15 skipped.
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün.
- `wordlist.py` seit 7793907 byteidentisch; kein Treffer für `wordlist_nl`/`dutch_chain_for` außerhalb der zwei Module in `backend/src`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Read-only-Gate kannte wordlist_nl.py nicht**
- **Found during:** Vollsuite nach Task 2
- **Issue:** `test_the_real_package_has_no_violations` meldete `index/wordlist_nl.py: invariant 2, writing identifier mkdir` (Artefaktverzeichnis auf dem eigenen Volume).
- **Fix:** geprüfte Ausnahme `("index/wordlist_nl.py", "mkdir")` mit Begründungsabsatz und Zusicherung in `test_the_reviewed_exception_covers_exactly_the_named_modules`.
- **Files modified:** backend/tests/test_readonly_gate.py
- **Commit:** f51d6f9 (Commit 9f69621 war dadurch in der Vollsuite kurz rot; Einzeltests des Plans waren grün)

**2. Akzeptanzkriterium grep "findling.index.analyzer" = 0:** zwei Kommentarstellen in `wordlist_nl.py` umformuliert (vor dem Commit).

## Threat Flags

Keine neuen Oberflächen. T-21-03-01 (Test a_tampered_artifact), T-21-03-02 (ValueError-Test), T-21-03-03 (Singleton, Sprachgate, Liste nicht gehalten), T-21-03-04 (measure nur Zahlen) mitigiert.

## Self-Check: PASSED

- FOUND: backend/src/findling/index/wordlist_nl.py, backend/tests/test_wordlist_nl.py, backend/tests/test_dutch_analyzer.py
- FOUND: Commits 6972d0d, 9f69621, 2c40037, f51d6f9, 0d4ba89
