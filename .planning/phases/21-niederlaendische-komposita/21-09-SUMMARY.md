---
phase: 21-niederlaendische-komposita
plan: 09
subsystem: docs, index/schema
tags: [komposita, nl, doku, ram, budget, ci, komp-01]
requires: ["21-02", "21-04", "21-07", "21-08"]
provides:
  - docs/dutch-analyzer.md (Referenz der niederländischen Splitterkette)
  - docs/performance.md Nachtrag 25.09.2026 (RAM-Posten nl, Budget, 23-MB-Richtigstellung)
  - docs/language-analyzers.md "Compounds are German and Dutch"
  - schema.py-Kommentar zu FIELD_BODY_NL, Baumhash Plan 21-09
affects: [22, 23]
tech-stack:
  added: []
  patterns: [Doku zitiert nur Rohdaten-Zahlen mit Quelle]
key-files:
  created:
    - docs/dutch-analyzer.md
  modified:
    - docs/language-analyzers.md
    - docs/performance.md
    - backend/src/findling/index/schema.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "performance.md nennt den produktnahen Wert 24,2 bis 25,3 MB (Budget mit 25,3 MB: 1.838,0 MB, Reserve 162,0 MB), nicht 17,6 MB"
  - "RAM-Posten als eigener Nachtrag vom 25.09.2026 vor 'Reproduzieren' plus Zeile in 'Stand dieses Berichts', weil performance.md keinen Abschnitt mit den deutschen Automatenposten hat"
  - "Deutscher Automat in performance.md mit 42,1 MB (arm64 nativ, grundlast-fein Schritt 10) zitiert, nicht mit den 41,9 MB aus dem Plan"
metrics:
  duration: ca. 30 min bis zum Checkpoint
  completed: offen (Checkpoint Task 3)
  tasks: 2 von 3 (Task 3 wartet auf Owner-Freigabe)
---

# Phase 21 Plan 09: Doku, Schlussprüfung und CI-Beweis Summary

Die niederländische Kompositumkette ist dokumentiert (Referenzseite, RAM-Posten mit Budget gegen 2.000 MB, Richtigstellung der 23 MB), der letzte veraltete Code-Kommentar ist nachgezogen, und lokal sind Suite und alle sieben Gates grün. Push und CI-Beweis warten auf die Owner-Freigabe.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Doku und der letzte Kommentar im Code | 193100e | docs/dutch-analyzer.md, docs/language-analyzers.md, docs/performance.md, schema.py, test_measurement_scripts.py |
| 2 | Schlussprüfung lokal | (kein Codecommit, Ergebnis hier) | keine; der Baumhash passte, test_measurement_scripts.py blieb unberührt |
| 3 | Owner-Freigabe für den Push und der CI-Beweis | OFFEN | 21-09-SUMMARY.md |

## Task 1: Doku

- `docs/dutch-analyzer.md` neu (englisch, Aufbau wie german-analyzer.md): Liste und Provenienz, Rezept B 4-14 mit Vergleichstabelle, Messzahlen (413288 Zeilen, 316740 Einträge, Digest, 21/28, 0/28 ohne Splitter, 32/33), Filterreihenfolge mit Begründung der Faltung vor dem Splitter (D-07), Marke `wordlist_hash_nl` (off oder `<DUTCH_CHAIN_VERSION>:<digest>`, nicht gesät, Legacy-Regel, Auslöser, warum ANALYZER_VERSION nicht steigt, DUTCH_CHAIN_VERSION steigt bei Kettenänderung), Umbauweg (Re-Analyse, kein Download/OCR/Neueinbettung, Poller-Fix 21-01), D-08-Grenze wörtlich nach dem Testergebnis, die sieben benannten Grenzen, Ranking-Kosten, RAM mit Verweis auf performance.md, Lizenz mit Verweis auf THIRD-PARTY.md, Vorbehalt A4 datiert 2026-09-25. Die Kurzstämme `hur`/`kop` sind benannt und gegen die echte Kette geprüft (`huur` wird auf der Frageseite ebenfalls `hur`).
- `docs/language-analyzers.md`: Absatz "Compounds are German only" ersetzt durch "Compounds are German and Dutch", Satz "scheduled for phase 21" entfällt, Verweis auf dutch-analyzer.md.
- `docs/performance.md`: Nachtrag vom 25.09.2026 mit den drei Läufen aus `ram.txt` (24,22 / 25,25 / 25,19 MB), Spanne 24,2 bis 25,3 MB, Bedingung "nur bei aktivem nl", Quelle `docs/measurements/2026-09-komposita-nl/`, Budget 1.812,7 + 25,3 = 1.838,0 MB, Reserve 162,0 MB; Richtigstellung der "rund 23 MB"; Annahme A1 und ARM-Nachmessung in Phase 22. Dazu eine Zeile in "Stand dieses Berichts".
- `schema.py`: nur Kommentar zu `FIELD_BODY_NL`, kein SCHEMA_VERSION-Hub. Baumhash neu `3b5a7383...f048b5`, `PACKAGE_FILES_TODAY` bleibt 57, Kommentar "Plan 21-09".

Akzeptanz: "Compounds are German only" 0, "dutch-analyzer.md" 1, `wordlist_hash_nl` in dutch-analyzer.md 3 und performance.md 1, "316740" 2, "2026-09-komposita-nl" 1, "23 MB" 4, keine U+2013/U+2014 in den drei Dokumenten, README.md/README.en.md/README.fr.md/info.xml unberührt, test_measurement_scripts.py 376 passed.

## Task 2: Schlussprüfung lokal (CI-Form)

| Kommando | Ergebnis |
|---|---|
| `uv run pytest -q` | **2973 passed, 15 skipped** |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 141 files already formatted |
| `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | keine Meldung, rc 0 |
| `uv run ruff check --config pyproject.toml ../scripts` | All checks passed |
| `uv run ruff format --config pyproject.toml --check ../scripts` | 13 files already formatted |

### Entscheid-Checkliste D-02 bis D-09

| Entscheid | Stand | Beleg |
|---|---|---|
| D-02 Liste freigegeben, nur Digest gecacht | hält | `backend/tests/test_wordlist_nl.py:194` `test_the_list_is_not_held_after_the_digest_is_known`; dazu `test_the_digest_is_read_once_per_process` (Z. 182) |
| D-03 Fenster 4-14 | hält | `backend/src/findling/index/wordlist_nl.py:84-85` `MIN_LEN = 4`, `MAX_LEN = 14`; Test `test_the_window_applies_to_the_unfolded_length` (Z. 104) |
| D-04 CC-BY-3.0 | hält | `THIRD-PARTY.md:66` "Licence CC-BY-3.0 (debian/copyright, Files: wordlist/*)"; CI-Gate in `.github/workflows/docker.yml` (21-02) |
| D-05 `ANALYZER_VERSION` bleibt 1 | hält | `backend/src/findling/index/analyzer.py:137` `ANALYZER_VERSION = 1`; `DUTCH_CHAIN_VERSION: Final = 1` in `wordlist_nl.py:105` |
| D-06 Marke nicht gesät, Legacy-Regel | hält | `backend/tests/test_store_repo.py:448` `test_the_dutch_mark_is_never_written_by_the_seed`, Z. 412 `test_an_absent_dutch_mark_is_legacy_while_dutch_is_off`, Z. 465 `test_the_dutch_exception_falls_closed` (Tests aus 21-05) |
| D-07 Splitter hinter der Faltung | hält | `backend/tests/test_dutch_analyzer.py:187` `test_the_dutch_chain_stands_in_the_measured_order`, Z. 217 `test_the_splitter_stands_behind_the_fold`, Gegenprobe Z. 199 |
| D-08 fullreindex stempelt die Verzeichnismarken nicht | festgeschrieben | `backend/tests/test_index_rebuild.py:1484` `test_the_full_reindex_way_out_leaves_the_marks_of_a_directory_as_they_were`, Z. 1544 `..._raises_the_generation_once_per_drift` (21-01); in dutch-analyzer.md dokumentiert |
| D-09 Bestand ohne nl unberührt, Store upgrade 5 unverändert | hält lokal | Schritt "Store upgrade 5, the seven assurances after the upgrade" (`deploy-harp.yml:4118`, 238 Zeilen) byteidentisch gegen `origin/main` (d074075) und gegen den Stand vor der Phase; CI-Beweis steht aus (Task 3) |

## Task 3: Checkpoint (OFFEN)

Wartet auf Owner-Freigabe "approved". Danach: `git push`, `gh run list --limit 10`, `gh run watch` je Lauf, Laufnummern und Ergebnisse der Schritte "Language proof, the four new chains answer on the ordinary search route" (Fall nlc, erste Datei `language-proof-nlc.txt` für `belasting`) und "Store upgrade 5, the seven assurances after the upgrade" hier eintragen. Nicht gepusht: 49 Commits seit `origin/main` (d074075), von `6999581` bis `193100e` plus dieser SUMMARY-Commit.

## Deviations from Plan

**1. Ort des RAM-Postens in performance.md.** Der Plan verortet ihn "dort, wo der deutsche Automat 41,9 MB und die Liste 21,9 MB stehen". Diese Stelle gibt es in performance.md nicht (grep leer). Der Posten steht deshalb als eigener Nachtrag vom 25.09.2026 vor "Reproduzieren", im Stil der übrigen Nachträge, plus eine Zeile in "Stand dieses Berichts".

**2. Deutscher Automat 42,1 MB statt 41,9 MB.** Die Quelle `docs/measurements/2026-09-grundlast-fein/README.md` Z. 140 nennt für "10-deutscher-automat-gebaut" 42,1 MB Zuwachs auf arm64 nativ (42,6 MB amd64); die 41,9 MB aus Plan und aus `docs/measurements/2026-09-komposita-nl/README.md` Abschnitt 4.3 stehen dort nicht. performance.md zitiert den Quellwert 42,1 MB. Der Messbericht 21-04 wurde nicht angefasst (nicht in `files_modified`); der Wert dort ist ein kleiner Zitierfehler, als Befund für eine spätere Korrektur notiert.

## Known Stubs

Keine.

## Threat Flags

Keine neue Oberfläche. T-21-09-01 mitigiert (Werte aus `rohdaten/ram.txt`, Quelle verlinkt, 23-MB-Richtigstellung), T-21-09-03 mitigiert (kein Push vor dem Checkpoint). T-21-09-02 greift erst in Task 3.

## Self-Check: PASSED

- FOUND: docs/dutch-analyzer.md, geänderte Dateien in 193100e
- FOUND: Commit 193100e
- Baumhash-Test grün, Suite 2973 passed / 15 skipped
