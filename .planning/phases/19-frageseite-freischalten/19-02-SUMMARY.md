---
phase: 19-frageseite-freischalten
plan: 02
subsystem: tests
tags: [messfixture, analysekette, tantivy, snowball, italienisch, zaehlgate]

# Dependency graph
requires:
  - phase: 17-sprachketten
    provides: "chain_cases_<code>.txt, measure_chains.sh, chain_probe.py, der Messbericht 2026-09-analyseketten"
  - phase: 18-schema-und-umbau
    provides: "test_language_cases_field_level.py mit SEPARATED/FOLDED und der Beförderungsanweisung in der Fehlermeldung"
provides:
  - "Eine italienische Flexionsfamilie in chain_cases_it.txt: das erste it-Formenpaar, das nur die italienische Kette zusammenfuehrt"
  - "Gemessene Zahlen des Nachlaufs vom 24.09.2026 in rohdaten/ und im Messbericht (Abschnitt 9)"
  - "EXPECTED_FAMILY_SCORES auf den gemessenen Zahlen, it (60, 60)"
  - "it in SEPARATED: der italienische Fall laeuft auf dem starken Kriterium"
affects: [19-06 Sprachfaelle auf dem normalen Suchweg, 19-09 Doku der Frageseite]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Erst messen, dann berichten, dann die Konstante nachziehen; nie umgekehrt"
    - "Ein leer parametrisierter Fall wird eine unparametrisierte Zusicherung, sonst ist er ein stiller Uebersprung"
    - "Rohdaten gehoeren zum Baum, wie er steht: der Nachlauf schreibt in dasselbe Verzeichnis und bekommt einen datierten Abschnitt"

key-files:
  created: []
  modified:
    - backend/tests/fixtures/chain_cases_it.txt
    - scripts/dev/measure_chains.sh
    - docs/measurements/2026-09-analyseketten/README.md
    - docs/measurements/2026-09-analyseketten/rohdaten/familien.tsv
    - docs/measurements/2026-09-analyseketten/rohdaten/kennzahlen.txt
    - docs/language-analyzers.md
    - backend/tests/test_language_analyzers.py
    - backend/tests/test_language_cases_field_level.py

key-decisions:
  - "Fixture-Erweiterung statt Instanz ohne Englisch (RESEARCH Open Question 1): eine Konfiguration, die kein Nutzer faehrt, beweist weniger"
  - "Die Familie steht am Ende der Datei, damit die vierzehn Akzentfamilien der Messung vom 23.09.2026 in Reihenfolge und Inhalt unberuehrt bleiben"
  - "Das Verdikt zur Faltposition aus dem Lauf vom 23.09.2026 bleibt woertlich stehen; der Nachlauf bekommt einen eigenen Abschnitt 9 statt eine Umschrift"
  - "FOLDED bleibt als leeres Tupel stehen und wird nicht geloescht: die Klassifizierung als Begriff traegt die Aussage, dass niemand mehr auf dem schwaecheren Kriterium laeuft"

requirements-completed: [LEX-05]

# Metrics
duration: 38min
completed: 2026-09-24
---

# Phase 19 Plan 02: it-Fixture, Nachlauf und Zaehlgate Summary

**Die italienische Messfixture traegt seit dem Nachlauf vom 24.09.2026 eine Flexionsfamilie, und damit laeuft der italienische Sprachfall auf demselben starken Kriterium wie die drei anderen Sprachen**

## Performance

- **Duration:** rund 38 min
- **Started:** 2026-09-24T22:00:00Z
- **Completed:** 2026-09-24T22:38:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- `chain_cases_it.txt` traegt die Familie `informazione informazioni` als Datenzeile mit eigenem
  Kommentarblock in der Form der vorhandenen Bloecke. Gemessen und nicht behauptet: die italienische
  Kette legt beide Formen auf `inform`, die englische laesst `informazion` und `informazioni` stehen,
  die deutsche ebenso. Sie ist damit das erste italienische Paar, das nur die eigene Kette verbindet.
- `scripts/dev/measure_chains.sh` ist neu gefahren, Rueckgabecode 0, in das Vorgabeverzeichnis
  `docs/measurements/2026-09-analyseketten/rohdaten/`. Die Gegenprobe der Siegerkette gegen
  `snowball_analyzer()` meldete wieder null abweichende Formen, also misst der Bericht weiter das
  Produkt und nicht sich selbst.
- Die gemessenen Zahlen, Zeile fuer Zeile: `it_families` 14 auf 15, `it_pairs` 56 auf 60,
  `it_A_hits`/`it_Aplus_hits`/`it_B_hits`/`it_Bplus_hits`/`it_Dplus_hits` 56 auf 60,
  `it_C_hits`/`it_Cplus_hits` 54 auf 58, `total_families` 65 auf 66, `total_pairs` 573 auf 577,
  `total_Aplus_hits` 467 auf 471, `total_Cplus_hits` 463 auf 467. Alles uebrige steht unveraendert,
  einschliesslich der vier Ergaenzungslisten, des Digests `d056d459...` und aller acht Leck-Zahlen.
- Der Messbericht bekommt Abschnitt 9 "Nachlauf vom 24.09.2026": Eingabeaenderung, Umgebung des Laufs,
  eine Tabelle alte Zahl gegen neue Zahl, was gleich geblieben ist und was der Nachlauf ausdruecklich
  nicht anfasst. Die Kopftabelle (Abschnitt 1) und die Kandidatentabelle (Abschnitt 2, it-Zeile und
  Summenzeile) stehen auf dem neuen Stand.
- `docs/language-analyzers.md` nennt in beiden Herkunftsangaben jetzt beide Daten und traegt die
  bewegten Zahlen: die it-Zeile und die Summenzeile der Messtabelle sowie die Begruendung der
  Filterposition 2 (471 von 577 gegen 467 fuer die spaete Faltung).
- `EXPECTED_FAMILY_SCORES` steht auf den gemessenen Zahlen, `it` auf `(60, 60)`. Der Kommentarblock
  darueber sagt, welches der vier Zahlenpaare sich bewegt hat und dass die drei uebrigen unberuehrt
  auf dem Wert vom 23.09.2026 stehen. Die Regel des Blocks gilt unveraendert: Gleichheit statt
  "mindestens", und erst messen, dann berichten, dann die Konstante nachziehen.
- `it` ist von `FOLDED` nach `SEPARATED` gewandert, genau wie die Fehlermeldung von
  `test_the_fixture_of_a_folded_language_offers_no_such_pair` es selbst anweist. `_separated_pairs`
  waehlt die neue Familie, `_case_pair` nimmt sie als erstes qualifizierendes Paar, und die fuenf
  Faelle, die bisher nur die drei anderen Sprachen abdeckten, decken jetzt auch Italienisch ab.
- Der leer gewordene parametrisierte Fall ist durch
  `test_no_language_of_the_build_out_rests_on_the_weaker_criterion` ersetzt, eine unparametrisierte
  Zusicherung mit dem Grund im Docstring. Kein stiller Uebersprung: `pytest -rs` ueber beide Module
  meldet 83 bestanden und null uebersprungen.
- Die drei Prosastellen in `test_language_cases_field_level.py`, die noch den in 19-01 gefallenen
  Namen `DEFAULT_FIELDS` nannten, sind mitgenommen (STATE-Kleinigkeit, siehe Deviation 2).

## Task Commits

Beide Tasks stehen in einem gemeinsamen Commit, siehe Deviation 1:

1. **Task 1: Die Fixture waechst, und die Messung wird neu gefahren** - `10917a0` (test)
2. **Task 2: Zaehlgate und Klassifizierung nachziehen** - `10917a0` (test)

**Plan metadata:** siehe docs-Commit unten

## Files Created/Modified

- `backend/tests/fixtures/chain_cases_it.txt` - eine Flexionsfamilie mit eigenem Kommentarblock am
  Dateiende, Kopfzeile "Erwartet" auf die gemessenen 15 Familien und 60 geordneten Paare gesetzt
- `scripts/dev/measure_chains.sh` - Kopfkommentar auf `total_families=66 total_pairs=577
  total_Aplus_hits=471 total_Cplus_hits=467`, mit dem Satz, dass der Nachlauf vom 24.09.2026 eine
  italienische Flexionsfamilie hinzubekommen hat; die Ergaenzungslisten-Zeile steht unveraendert
- `docs/measurements/2026-09-analyseketten/rohdaten/kennzahlen.txt` - Ergebnis des Laufs, 13 Zeilen bewegt
- `docs/measurements/2026-09-analyseketten/rohdaten/familien.tsv` - Ergebnis des Laufs, 14 Zeilen neu
  (die zwei Formen der Familie in allen sieben Kandidatenketten)
- `docs/measurements/2026-09-analyseketten/rohdaten/verluste.tsv` - UNVERAENDERT, siehe unten
- `docs/measurements/2026-09-analyseketten/README.md` - Abschnitt 9 neu, Abschnitt 1 und Abschnitt 2
  auf dem neuen Stand; Abschnitt 4 (Verdikt) und Abschnitt 5 (Testfall-Tabelle) woertlich unveraendert
- `docs/language-analyzers.md` - beide Herkunftsangaben nennen beide Daten, Messtabelle und die
  Begruendung der Filterposition 2 auf den neuen Zahlen; die uebrigen Abschnitte gehoeren 19-09 und
  sind nicht angefasst
- `backend/tests/test_language_analyzers.py` - `EXPECTED_FAMILY_SCORES["it"] = (60, 60)`, Kommentarblock
  um den Nachlauf-Absatz erweitert, Modulkopf auf 471 von 577 gegen 467, der zweite Verweis auf
  Abschnitt 5 sagt jetzt ausdruecklich, dass der Nachlauf dort nichts bewegt hat
- `backend/tests/test_language_cases_field_level.py` - `SEPARATED = ("es", "it", "nl", "pt")`,
  `FOLDED = ()`, der it-Absatz der Klassifizierungsbegruendung neu geschrieben, der leer parametrisierte
  Fall durch eine unparametrisierte Zusicherung ersetzt, drei `DEFAULT_FIELDS`-Prosastellen berichtigt

## Decisions Made

- **Die Familie steht am Dateiende, nicht vorn.** So bleiben die vierzehn Akzentfamilien des Laufs vom
  23.09.2026 in Reihenfolge und Inhalt unberuehrt, und der Diff der Fixture ist ein reiner Zuwachs.
  Auf die Auswahl des Fallpaares hat die Position keinen Einfluss: `_separated_pairs` liefert genau ein
  Paar, und `_distractor` landet so oder so auf der ersten Form der ersten Akzentfamilie.
- **`FOLDED` bleibt als leeres Tupel stehen.** Es zu loeschen waere sauberer im Sinne von "kein toter
  Name", nimmt aber der Suite die Aussage. Der Klassifizierungsfall
  `test_every_language_of_the_build_out_is_classified_exactly_once` haelt beide Listen gegen `CODES`,
  und die neue unparametrisierte Zusicherung haelt `FOLDED == ()` mit der Anweisung in der
  Fehlermeldung. Faellt einer Fixture spaeter die Flexionsfamilie weg, ist das dann ein roter Fall und
  keine stille Ruecknahme.
- **`chain_known_losses_it.txt` bleibt unveraendert.** `verluste.tsv` ist nach dem Lauf Zeile fuer
  Zeile dieselbe Datei, Git meldet sie gar nicht erst als geaendert. Die neue Familie erzeugt keinen
  italienischen Verlust, weil beide Formen unakzentuiert sind und die italienische Kette sie auf
  denselben Stamm legt. Italienisch steht damit weiter auf null Verlusten, und der Plan hat diesen
  Ausgang ausdruecklich vorgesehen.
- **Abschnitt 5 des Messberichts wurde nicht um eine Zeile ergaenzt.** Die Tabelle ist die Abnahme von
  LEX-01 und listet die dort benannten Faelle; die neue Familie ist kein LEX-01-Fall. Eine
  sechzehnte Zeile haette `MERGED_CASES` und dessen "zwoelf von fuenfzehn"-Begruendung mitbewegt,
  ohne eine Aussage zu gewinnen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Beide Tasks in einem Commit statt in zweien**
- **Found during:** Task 1 (nach dem Messlauf, vor dem Commit)
- **Issue:** Der Plan schreibt die Reihenfolge messen, berichten, Konstante nachziehen ausdruecklich
  vor. Genau diese Reihenfolge laesst nach Task 1 einen roten Baum zurueck: die Verifikation von
  Task 1 (`uv run pytest -q tests/test_language_analyzers.py`) meldet wie vorgesehen
  `AssertionError: it scores 60 of 60 ordered pairs, measured was (56, 56)`, weil das Zaehlgate erst
  in Task 2 nachgezogen wird. Ein Commit an dieser Stelle waere ein Commit mit rotem Gate und damit
  ein Verstoss gegen die bindende Projektregel "Qualitaetsgates lokal gruen VOR jedem Commit".
- **Fix:** Beide Tasks in der Planreihenfolge ausgefuehrt und einzeln gegen ihre Akzeptanzkriterien
  geprueft, danach ein gemeinsamer atomarer Commit `10917a0` ueber alle acht Dateien.
- **Files modified:** keine zusaetzlichen
- **Verification:** Der rote Lauf nach Task 1 ist der Beleg, dass die Reihenfolge eingehalten wurde:
  das Gate hat die Aenderung gefangen, bevor die Konstante bewegt wurde, und genau das ist die
  Mitigation T-19-02-01.
- **Committed in:** `10917a0`

**2. [Rule 2 - Missing] Drei Prosastellen nannten weiter `DEFAULT_FIELDS`**
- **Found during:** Task 2
- **Issue:** `test_language_cases_field_level.py` nannte im Modul-Docstring und im Docstring von
  `_found` den Namen `DEFAULT_FIELDS`, den Plan 19-01 aufgeloest hat. Ein Name, den es nicht mehr
  gibt, in der Begruendung eines Tests ist eine Falle fuer den naechsten Leser. STATE.md fuehrt genau
  diese Stellen als mitzunehmende Kleinigkeit und nennt 19-02 als den Plan, der die Datei ohnehin
  anfasst.
- **Fix:** Beide Stellen nennen jetzt den Feldplan und `LEGACY_PLAN` mit der Herkunftsangabe
  "seit Plan 19-01"; der Modul-Docstring nennt zusaetzlich 19-06 als den Plan, der diese Faelle auf
  den normalen Suchweg hebt.
- **Files modified:** `backend/tests/test_language_cases_field_level.py`
- **Verification:** `grep -n "DEFAULT_FIELDS" backend/tests/test_language_cases_field_level.py` liefert
  keine Zeile mehr; die zwei Stellen in `backend/src/findling/store/repo.py` bleiben offen, weil der
  Fussabdruck dieses Plans keine Datei unter `backend/src/findling` beruehren darf.
- **Committed in:** `10917a0`

---

**Total deviations:** 2 auto-fixed (Rule 3 blockierend, Rule 2 Korrektheit der Begruendung)
**Impact on plan:** Kein Scope-Zuwachs. Deviation 1 aendert nur die Commit-Granularitaet;
Deviation 2 ist die vom STATE ausdruecklich diesem Plan zugewiesene Kleinigkeit.

## Threat Flags

Keine. Der Plan legt keine Route an, oeffnet keinen Netzpfad und beruehrt weder
`backend/src/findling` noch `php/`. `backend/pyproject.toml` und `backend/uv.lock` stehen nicht im
Diff, T-19-02-SC ist damit mangels Gegenstand erfuellt. Die drei uebrigen Eintraege des
Threat-Registers sind umgesetzt und jeweils belegt:

- **T-19-02-01 (Tampering am Zaehlgate):** Die Reihenfolge ist eingehalten und belegt, siehe
  Deviation 1. Die Werte in `EXPECTED_FAMILY_SCORES` stehen wortgleich in
  `rohdaten/kennzahlen.txt` (`it_Aplus_hits=60`, `it_pairs=60`).
- **T-19-02-02 (Repudiation am Messbericht):** Der Nachlauf hat einen eigenen datierten Abschnitt mit
  alter und neuer Zahl. Abschnitt 4 (Verdikt zur Faltposition) und Abschnitt 5 sind woertlich
  unveraendert.
- **T-19-02-03 (stiller Uebersprung):** Der leer gewordene Fall ist unparametrisiert neu geschrieben,
  und der Verifikationslauf mit `-rs` meldet null uebersprungene Faelle in beiden Modulen.

## Known Stubs

Keine.

## Issues Encountered

- Der Plan nennt in Task 1 "die Tabellen in Abschnitt 5 (it-Zeile und Summenzeile)". Abschnitt 5 des
  Berichts ist die zusammengefuehrte Testfall-Tabelle und hat weder eine it-Zeile noch eine
  Summenzeile; beide stehen in Abschnitt 2 (Kandidatentabelle). Gemeint war ersichtlich Abschnitt 2,
  und dort sind sie gesetzt. Abschnitt 5 ist unveraendert geblieben, was zur zweiten Vorgabe des
  Plans passt, die Aussagen des Laufs vom 23.09.2026 nicht umzuschreiben.
- `docs/language-analyzers.md` traegt die bewegten Zahlen an einer dritten Stelle, die der Plan nicht
  namentlich nennt: die Begruendung der Filterposition 2 ("Measured 467 of 573 ordered pairs against
  463 for a late fold"). Sie ist mitgezogen worden, weil sie dieselbe Messgroesse nennt; haette sie
  stehen bleiben duerfen, waere die Zusage des Dateikopfes verletzt, dass jede Zahl dieser Seite auf
  eine Zeile von `rohdaten/kennzahlen.txt` zurueckgeht.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Der italienische Fall auf dem normalen Suchweg ist fuer Plan 19-06 schreibbar: `_separated_pairs`
  findet fuer alle vier Sprachen ein Paar, das nur die eigene Kette zusammenfuehrt, und
  `test_no_form_of_the_case_stands_in_this_file` gilt unveraendert weiter, also bleiben die Formen in
  der Fixture und wandern nicht als Literale in eine Testdatei.
- Die Zahlen, auf die 19-09 die Doku der Frageseite stellt, sind die des Nachlaufs: 471 von 577 unter
  A+, 467 unter C+, 66 Familien. Sie stehen an genau drei Stellen ausserhalb der Rohdaten
  (`README.md` des Berichts, `docs/language-analyzers.md`, Kopf von `measure_chains.sh`) und einmal
  als Zaehlgate.
- Die Messfixtures von es, nl und pt sind unberuehrt; wer sie spaeter erweitert, faehrt denselben
  Weg: Fixture, Lauf, Bericht, Konstante.

## Verification

- `sh scripts/dev/measure_chains.sh`: Rueckgabecode 0, `chain_probe: 66 families, 577 ordered pairs,
  53 losses under Aplus`.
- `uv run pytest -q` aus `backend/`: 2751 bestanden, 15 uebersprungen, 0 Fehlschlaege.
- `uv run pytest -q tests/test_language_analyzers.py tests/test_language_cases_field_level.py -rs`:
  83 bestanden, null uebersprungene Faelle.
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 134 files already formatted.
- `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src tests --min-confidence 80`: keine Befunde.
- `git diff --name-only` nennt acht Dateien, keine davon unter `backend/src/findling` oder `php/`;
  `PACKAGE_TREE_HASH_TODAY` und `PHP_TREE_HASH_TODAY` sind unberuehrt geblieben.
- Akzeptanzkriterien einzeln geprueft: `grep -c "informazione"` = 1, die Datenzeile
  `informazione informazioni` genau einmal ausserhalb der Kommentare, `it_families=15`,
  ein Abschnitt "Nachlauf vom 24.09.2026" im Bericht, `total_families=65` im Skriptkopf nicht mehr
  auffindbar.
- Kein Em-Dash in einer der acht Dateien; `test_language_cases_field_level.py` enthaelt weiterhin
  kein einziges Nicht-ASCII-Zeichen, die Akzente stehen ausschliesslich in Fixture- und Prosadateien.

---
*Phase: 19-frageseite-freischalten*
*Completed: 2026-09-24*
