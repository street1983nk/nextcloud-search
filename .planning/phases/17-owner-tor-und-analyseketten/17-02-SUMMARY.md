---
phase: 17-owner-tor-und-analyseketten
plan: 02
subsystem: config
tags: [tantivy, snowball, allowlist, stopwords, stemmer, parity-test, config]

# Dependency graph
requires:
  - phase: 03-extraktion-und-ocr
    provides: "OCR_LANGUAGE_ALLOWLIST plus _ocr_languages() und test_ocr_languages.py als Positivlisten- und Paritaetsmuster"
  - phase: 16-launch-haertung
    provides: "die Erweiterung derselben Positivliste auf neun OCR-Sprachen, samt Doppelrichtungs-Gate"
provides:
  - "LANGUAGE_ALLOWLIST: geschlossenes frozenset der 13 Sprachnamen, die tantivy in beiden Haelften bedient"
  - "SUPPORTED_LANGUAGES: die sechs Produktsprachen in Schemafeldreihenfolge"
  - "SNOWBALL_NAME: die einzige Abbildung von Feldkuerzel auf tantivy-Sprachnamen"
  - "backend/tests/test_language_allowlist.py: Doppelrichtungs-Paritaetsgate gegen das laufende tantivy mit gestellter Mutation"
affects: [18-kettenfabrik, analyzer, index-schema, versionsmarken]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Positivliste als Schnittmenge zweier gemessener Faehigkeiten einer Fremdbibliothek, nicht als gepflegte Wunschliste"
    - "Paritaetsgate gegen die laufende Bibliothek statt gegen eine zweite Liste im Test"
    - "builds()-Helfer, der die Analyzer-Kette bis zum Ende baut und einen bool statt eines Ausnahmetyps zurueckgibt"

key-files:
  created:
    - backend/tests/test_language_allowlist.py
  modified:
    - backend/src/findling/config.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Die Panic-Klasse ist gemessen und nicht geschaetzt: 18 Sprachen mit Stemmer, 13 mit eingebauter Stoppwortliste, Differenz arabic, greek, romanian, tamil, turkish"
  - "builds() faengt BaseException, weil pyo3_runtime.PanicException in tantivy 0.26.0 direkt von BaseException erbt und ein except Exception genau den Fall durchliesse, fuer den die Datei existiert"
  - "Der Test behauptet nie einen Ausnahmetyp, nur True oder False, damit er unter 0.26.0 (Panic) und 0.26.2 (ValueError) gleich haelt"
  - "Kein Produktionspfad liest die drei Konstanten in Phase 17: DEFAULT_LANGUAGES, _languages() und Settings.languages bleiben unberuehrt"
  - "Der ruff-Regelsatz dieses Repos kennt weder B036 noch BLE001, das vom Plan verlangte noqa waere selbst ein Verstoss (RUF100/RUF102) gewesen und wurde durch einen Begruendungskommentar ersetzt"

patterns-established:
  - "Messung vor Konstante: die 18/13-Aufteilung wurde vor dem Schreiben gegen das eingebaute tantivy nachgezaehlt"
  - "Gestellte Mutation im Gate: romanian baut mit Stemmer durch und faellt, sobald die Stoppwortliste verlangt wird"

requirements-completed: [LEX-07]

# Metrics
duration: 40min
completed: 2026-09-23
---

# Phase 17 Plan 02: Sprach-Positivliste und Paritaetsgate Summary

**Geschlossene Sprach-Positivliste (13 Namen, Schnittmenge aus tantivy-Stemmern und eingebauten Stoppwortlisten) in `config.py`, abgesichert durch ein Gate, das beide Richtungen gegen das laufende tantivy prueft und seinen eigenen roten Zustand vorfuehrt.**

## Performance

- **Duration:** ca. 40 min
- **Started:** 2026-09-23T16:56Z
- **Completed:** 2026-09-23T17:36Z
- **Tasks:** 2
- **Files modified:** 3 (2 geplant, 1 Abweichung)

## Accomplishments

- `LANGUAGE_ALLOWLIST` als `frozenset` der 13 Namen, die tantivy in beiden Haelften bedient, mit einem Kommentar, der die Messung (18 Stemmer, 13 Stoppwortlisten), die fuenf Differenznamen, das Messdatum und die Gegenstelle nennt.
- `SUPPORTED_LANGUAGES` in Schemafeldreihenfolge und `SNOWBALL_NAME` als einzige Uebersetzung von Feldkuerzel auf tantivy-Namen.
- `backend/tests/test_language_allowlist.py` mit vier Tests: beide Paritaetsrichtungen, die gestellte Mutation und die Zahlenbehauptung.
- Die Panic-Klasse wurde vor dem Schreiben nachgemessen, nicht aus dem RESEARCH uebernommen. Ergebnis deckungsgleich: `Filter.stemmer` bedient 18, `Filter.stopword` 13, die Differenz ist genau arabic, greek, romanian, tamil, turkish.
- Eine Bestandsinstallation sieht davon nichts: der Diff an `config.py` besteht aus 66 hinzugefuegten und null geaenderten Zeilen.

## Task Commits

1. **Task 1: Die drei Konstanten in config.py** , `ede2907` (feat)
2. **Abweichung: Baumhash-Register fortgeschrieben** , `34f8b47` (chore)
3. **Task 2: Doppelrichtungs-Paritaetsgate** , `8931dd4` (test)

## Files Created/Modified

- `backend/src/findling/config.py` , drei neue Konstanten direkt hinter `DEFAULT_LANGUAGES`, jede mit Begruendungskommentar nach dem Muster von `OCR_LANGUAGE_ALLOWLIST`. 66 Zeilen hinzugefuegt, keine geaendert.
- `backend/tests/test_language_allowlist.py` , 123 Zeilen, vier Tests plus `builds()`-Helfer.
- `backend/tests/test_measurement_scripts.py` , `PACKAGE_TREE_HASH_TODAY` auf `8df3aeee...` fortgeschrieben, mit dem fuenfzehnten Eintrag der Kommentarkette. `PACKAGE_FILES` bleibt bei 54.

## Decisions Made

- **Messung vor Uebernahme.** Die Zahlen aus RESEARCH 5.1 wurden gegen das eingebaute tantivy 0.26.0 nachgezaehlt, bevor die Konstante geschrieben wurde. Ein Nebenbefund praezisiert die Forschung: die Panic feuert in 0.26.0 bereits beim Anhaengen des Filters an den Builder (`.filter(...)`), nicht erst beim `build()`. Die Aussage des Plans bleibt richtig, denn `Filter.stopword("romanian")` allein konstruiert klaglos, ein Test, der nur konstruiert, ist gruen und beweist nichts. `builds()` baut deshalb immer bis zum Ende durch; der Modulkopf sagt die praezisere Fassung.
- **`except BaseException` statt `except Exception`.** `pyo3_runtime.PanicException` hat die MRO `PanicException -> BaseException -> object` und ist keine `Exception`. Ein enger Fang wuerde den ValueError von 0.26.2 auffangen und die Panic von 0.26.0 als Testfehler durchlassen, also genau den Fall, fuer den die Datei existiert.
- **Kein Ausnahmetyp in der Behauptung.** `builds()` gibt einen bool zurueck, damit derselbe Test unter beiden tantivy-Fassungen haelt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Baumhash-Register `PACKAGE_TREE_HASH_TODAY` fortgeschrieben**

- **Found during:** Task 2 (voller Suitendurchlauf)
- **Issue:** `tests/test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_python_package` haelt einen gepinnten Baumhash ueber `backend/src/findling/**/*.py` gegen das laufende Verzeichnis. Jede Aenderung an einer der 54 Dateien bewegt ihn. Die Suite war nach Task 1 rot (`7d0e5857...` erwartet, `8df3aeee...` gemessen). Gegenprobe: mit der Basisfassung von `config.py` im Baum lief dieselbe Datei mit 376 bestandenen Tests gruen, die Ursache ist also eindeutig Task 1 und kein Altbefund.
- **Fix:** Neuer Wert plus fuenfzehnter Eintrag der Kommentarkette, genau in der Form, die die vierzehn vorherigen Eintraege vorgeben (was sich geaendert hat, und dass keine Datei kam und keine ging). `PACKAGE_FILES` bleibt bei 54. Die historische Messkonstante `PACKAGE_TREE_HASH` wurde nicht angefasst, denn sie ist eine veroeffentlichte Messzahl.
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Verification:** `uv run python -m pytest tests/test_measurement_scripts.py -q` , 376 passed. Volle Suite 2495 passed, 15 skipped.
- **Committed in:** `34f8b47`
- **Hinweis zum Abnahmekriterium:** Das Kriterium von Task 2 verlangt, dass `git status --porcelain` genau zwei Pfade listet. Das kollidiert mit der Plan-Verifikation "volle Suite gruen", weil das Register bei jeder Aenderung im Paket mitwandert. Die Suite hat Vorrang, die dritte Datei ist die dokumentierte Folge davon.

**2. [Rule 3 - Blocking] Das verlangte `noqa` durch einen Begruendungskommentar ersetzt**

- **Found during:** Task 2 (`uv run ruff check`)
- **Issue:** Der Plan verlangt fuer `except BaseException` ein `# noqa` mit Regelcode und Begruendung. Der ruff-Regelsatz dieses Repos (`E, F, I, UP, B, ASYNC, S, SIM, C4, RUF, PT, RET, A, ISC`) fuehrt weder `BLE001` noch `B036`. Das noqa selbst war damit der einzige Fehler: `RUF100` (unbenutzte Direktive) und `RUF102` (ungueltiger Regelcode).
- **Fix:** Direktive entfernt, die Begruendung steht jetzt als fuenfzeiliger Kommentar unmittelbar ueber der `except`-Zeile und zusaetzlich im Docstring von `builds()`. Der Zweck der Planvorgabe, naemlich dass niemand den breiten Fang ohne Begruendung liest, bleibt erfuellt.
- **Files modified:** `backend/tests/test_language_allowlist.py`
- **Verification:** `uv run ruff check` , All checks passed.
- **Committed in:** `8931dd4`

---

**Total deviations:** 2 auto-fixed (beide Rule 3, blockierend)
**Impact on plan:** Beide waren noetig, um die Gates gruen zu bekommen. Kein Scope Creep: keine Verhaltensaenderung, keine neue Abhaengigkeit, kein Produktionspfad beruehrt.

## Issues Encountered

- Die Ausgabe der aufgefangenen Panic schreibt in 0.26.0 eine Rust-Panic-Zeile auf stderr. Das ist Rauschen im Testlauf und kein Fehler; pytest meldet die vier Tests gruen.

## Verification

- `uv run python -m pytest -q` aus `backend/`: **2495 passed, 15 skipped** (volle Suite).
- `uv run python -m pytest tests/test_language_allowlist.py -q`: **4 passed**.
- `uv run ruff check`: All checks passed. `uv run ruff format --check`: 127 files already formatted.
- `uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture`: still, Exitcode 0. Die drei Konstanten gelten durch den Test als benutzt.
- `uv run python -m pytest tests/test_upgrade_compatibility.py tests/test_lockstep_versions.py -q`: **29 passed**. Keine der fuenf Versionsmarken wurde bewegt.
- `git diff --numstat` fuer `config.py`: `66  0`, also ausschliesslich Ergaenzungen.
- Abnahmegrep: `grep -c finnish` in der Testdatei ergibt 0, es steht kein Mengenliteral im Test.

## Threat Model Coverage

| Threat ID | Disposition | Umsetzung |
|---|---|---|
| T-17-05 | mitigate | `LANGUAGE_ALLOWLIST` als geschlossenes `frozenset`, Schnittmenge beider von tantivy bedienten Mengen |
| T-17-06 | mitigate | `test_language_allowlist.py` prueft beide Richtungen gegen das laufende tantivy, plus gestellte Mutation mit `romanian` |
| T-17-07 | accept | unveraendert, kein Authentifizierungspfad beruehrt |
| T-17-08 | mitigate | `DEFAULT_LANGUAGES`, `_languages()`, `Settings.languages` unangetastet, Diff ist reine Ergaenzung |
| T-17-SC | mitigate | kein Paket installiert, kein Lockfile beruehrt |

Keine neue Angriffsflaeche: kein Netzpfad, kein Dateizugriff, kein Schemafeld. Keine Threat Flags.

## Known Stubs

Keine. Die drei Konstanten sind vollstaendig und bewiesen; dass kein Produktionspfad sie liest, ist die ausdrueckliche Entscheidung des Plans (die Kettenfabrik haengt erst in Phase 18 daran) und steht so im Kommentar von `SUPPORTED_LANGUAGES`.

## Next Phase Readiness

- Phase 18 darf die Kettenfabrik an die Konfiguration haengen: die Positivliste existiert, ist bewiesen und faellt rot, bevor ein unbedienter Sprachname die Rust-Seite erreicht.
- Offen und bewusst nicht in diesem Plan: der Leser, der `FINDLING_LANGUAGES` gegen `SUPPORTED_LANGUAGES` statt gegen `DEFAULT_LANGUAGES` filtert, sowie die Versionsmarke ueber der Sprachmenge (E-17-4). Beides beruehrt D-04 und wartet auf das Owner-Tor.

## Self-Check: PASSED

- Dateien vorhanden: `backend/src/findling/config.py`, `backend/tests/test_language_allowlist.py`, `backend/tests/test_measurement_scripts.py`, `.planning/phases/17-owner-tor-und-analyseketten/17-02-SUMMARY.md`
- Commits vorhanden: `ede2907`, `34f8b47`, `8931dd4`
- Keine Loeschungen in den drei Commits, keine Aenderung an STATE.md oder ROADMAP.md.

---
*Phase: 17-owner-tor-und-analyseketten*
*Completed: 2026-09-23*
