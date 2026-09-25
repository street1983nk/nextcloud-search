---
phase: 21-niederlaendische-komposita
plan: 04
subsystem: messung, tests
tags: [komposita, nl, messung, fixture, ram, komp-01]
requires: ["21-02", "21-03"]
provides:
  - scripts/dev/measure_compounds_nl.sh (Wegwerf-Container, tantivy==0.26.2, wdutch-Pin, drei RAM-Läufe)
  - scripts/dev/compound_probe_nl.py (nur ausgelieferte Fabriken, Fixture-Erzeugung, --against, --ram)
  - backend/tests/fixtures/compound_cases_nl.txt (28 Komposita, 33 Wächter, Vorbehalt A4)
  - backend/tests/fixtures/constituents_nl.txt (359 Einträge, per --against belegt)
  - docs/measurements/2026-09-komposita-nl/ (Bericht und Rohdaten)
affects: [21-05, 21-06, 21-07, 22]
tech-stack:
  added: []
  patterns: [Sonde ruft ausgelieferte Funktionen, Fold über name_analyzer statt Python-Normalisierung, guard over the guard]
key-files:
  created:
    - scripts/dev/measure_compounds_nl.sh
    - scripts/dev/compound_probe_nl.py
    - backend/tests/fixtures/compound_cases_nl.txt
    - backend/tests/fixtures/constituents_nl.txt
    - docs/measurements/2026-09-komposita-nl/README.md
    - docs/measurements/2026-09-komposita-nl/rohdaten/kennzahlen.txt
    - docs/measurements/2026-09-komposita-nl/rohdaten/tokens-rezept-b.tsv
    - docs/measurements/2026-09-komposita-nl/rohdaten/fixture-subset.txt
    - docs/measurements/2026-09-komposita-nl/rohdaten/ram.txt
  modified:
    - backend/tests/test_upgrade_compatibility.py
    - backend/tests/test_dutch_analyzer.py
    - backend/tests/test_language_analyzers.py
decisions:
  - "RAM-Abweichung (24,2 bis 25,3 MB statt 17,5 bis 17,7 MB) als Befund geführt, nicht nachgebessert; Budget rechnet mit dem höheren, produktnahen Wert 25,3 MB (Summe 1838,0 MB, Reserve 162,0 MB)"
  - "Die Sonde faltet die Fallwörter für die Teilmenge über name_analyzer (simple, lowercase, ascii_fold), damit kein zweiter Fold in Python entsteht"
  - "MB dezimal (10^6 Byte), wie die Research-Sonde"
metrics:
  duration: ca. 60 min
  completed: 2026-09-25
  tasks: 3 von 3
---

# Phase 21 Plan 04: Niederländische Rezeptmessung im Repo Summary

Messskript und Sonde reproduzieren im Wegwerf-Container alle Rezeptzahlen der Research exakt (413288 Zeilen, 316740 Einträge, Digest `ee7f3b83...`, 21/28, 32/33, 0/28 ohne Splitter), erzeugen die Fixture `constituents_nl.txt` (359 Einträge, Token-gleich zur Vollliste) und messen das RAM des zweiten Automaten vor der Verdrahtung; die gemessenen Token stehen als Tabellen-Tests.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Fallliste, Sonde und Messskript | 0f83503 | compound_cases_nl.txt, compound_probe_nl.py, measure_compounds_nl.sh, test_upgrade_compatibility.py |
| 2 | Messung fahren, Fixture erzeugen, Messbericht | a308987 | constituents_nl.txt, docs/measurements/2026-09-komposita-nl/ (README + 4 Rohdaten) |
| 3 | Tabellen-Tests und beide nl-Ketten | ebd0bf0 | test_dutch_analyzer.py, test_language_analyzers.py |

## Messergebnis (kennzahlen.txt)

```
source_lines=413288
entries=316740
digest=ee7f3b8380c752835692db8fbf1350786955d4fca13e94506812a23eece107a2
subset_entries=359
compounds_found_via_constituent=21   (von 28)
compounds_found_without_splitter=0
sentinels_whole=32                   (von 33, belastingplichtige zerfällt)
chain_cases_differing=0
```

Beide Läufe (ohne und mit `--against backend/tests/fixtures/constituents_nl.txt`) endeten mit Exit 0.

## Befund: RAM über dem Research-Wert

| Quelle | nl dauerhaft zusätzlich, Liste freigegeben |
|---|---|
| Repo-Sonde, 6 Läufe in 2 Messungen | 24,22 / 25,25 / 25,14 / 24,22 / 25,25 / 25,19 MB |
| Research-Sonde (Scratchpad) | 17,53 bis 17,66 MB |

Reproduzierbar rund 7 MB höher, damit außerhalb des Zielbereichs "17,5 bis 17,7 MB" aus dem Plan. Nicht nachgebessert. Diagnose (nur Scratchpad, im Bericht Abschnitt 4.1): mit `malloc_trim(0)` vor und nach dem Messpunkt hält der Automat selbst 15,1 bis 16,1 MB; der Rest ist freigegebener, aber von glibc nicht zurückgegebener Heap, abhängig von der Prozess-Vorgeschichte (die Research-Sonde lud das Findling-Paket nicht, die Repo-Sonde lädt es wie das Produkt). `wordlist_hash` erklärt den Unterschied nicht. Das Produkt ruft kein `malloc_trim`, deshalb rechnet das Budget mit 25,3 MB: 1812,7 + 25,3 = 1838,0 MB gegen 2000 MB, Reserve 162,0 MB. Das Budget hält.

Folge für spätere Pläne: `docs/performance.md` (falls ein Plan die nl-Zahl einträgt) sollte 24,2 bis 25,3 MB produktnah nennen, nicht 17,6 MB. Die native ARM-Nachmessung in Phase 22 klärt, welcher Wert auf der Box gilt. Die "rund 23 MB" sind im Bericht als überholte Schätzung des deutschen Automaten benannt; dass die gemessene Zahl in der Nähe liegt, ist dort ausdrücklich als Zufall markiert.

## Verifikation

- Task-1-Kriterien: `tantivy==0.26.2` 1x, `0.26.0` 0x, 2 Importzeilen aus analyzer/wordlist_nl, 0x TextAnalyzerBuilder, 61 Datenzeilen; test_upgrade_compatibility 13 passed; ruff check/format über scripts grün; pyright auf der Sonde 0 Fehler
- Task-2-Kriterien: alle grep-Prüfungen auf kennzahlen.txt treffen, `ram_nl_released_mb` 3x in ram.txt, `cmp` ohne Ausgabe, README ohne U+2013/U+2014, "23 MB" im Richtigstellungssatz
- Task 3: test_dutch_analyzer + test_language_analyzers + test_measurement_scripts 463 passed; `"nl": (57, 81)` unverändert; `DUTCH_SPLITTER_DIFFERENCES` 3x
- Gates: ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün
- Volle Suite: 2946 passed, 15 skipped
- Nichts unter backend/src/findling berührt, Baumhash-Ratsche unberührt; STATE.md und ROADMAP.md nicht angefasst

## Deviations from Plan

### Befund statt Abweichung

**1. RAM-Zielwert 17,5 bis 17,7 MB nicht erreicht (24,2 bis 25,3 MB)**
- Gemäß Plan als Befund behandelt: keine Code- oder Zahlenkorrektur, Diagnose im Bericht, Budget mit dem höheren Wert gerechnet. Die Rezeptzahlen (Abbruchkriterium des Plans) stimmen alle exakt, deshalb wurde nicht angehalten.

### Kleinere Anpassungen

**2. [Rule 3] Drei `noqa: PLR2004` in der Sonde entfernt** (Regel im scripts-Profil nicht aktiv, RUF100), vor dem Commit.

**3. Zusatztests über den Plan hinaus:** `test_the_measured_hit_count_holds_over_the_whole_case_list` (21/28 über die ganze Fallliste) und `test_the_dutch_splitter_chain_reaches_the_same_family_score` (Splitterkette erreicht auf den Phase-17-Familien ebenfalls 57/81). Beide sichern gemessene Zahlen, keine neue Behauptung.

**4. Fallliste enthält Kommentare in ASCII-Umschreibung** (Waechter, fuer), wie die Geschwisterdatei chain_cases_nl.txt; die Datei ist Testdaten, keine Prosa-Doku.

## Known Stubs

Keine.

## Threat Flags

Keine neue Oberfläche. T-21-04-01 (Pins im Skript plus Pin-Test, read-only Mounts), T-21-04-02 (Sonde liest nur Falllisten und Paketlisten, RAM-Modus nur Zahlen), T-21-04-03 (Token-Gleichheit je Wort, zweiter Lauf mit --against) umgesetzt.

## Self-Check: PASSED

- FOUND: alle 9 erstellten Dateien, 3 geänderte Testdateien
- FOUND: Commits 0f83503, a308987, ebd0bf0
