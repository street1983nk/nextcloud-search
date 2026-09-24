---
phase: 18-schema-marken-und-umbauweg
plan: 01
subsystem: database
tags: [tantivy, schema, snowball, analyzer, index, migration]

# Dependency graph
requires:
  - phase: 17-owner-tor-und-analyseketten
    provides: "snowball_analyzer (einarmige Kettenfabrik), FOLDED_STOPWORDS, LANGUAGE_ALLOWLIST, SUPPORTED_LANGUAGES, SNOWBALL_NAME, gelockerte tantivy-Vergleichsregel"
provides:
  - "Dreizehn Schemafelder: body_es, body_it, body_nl, body_pt neben body_de und body_en, alle vier ungespeichert"
  - "BODY_FIELD: geschlossene Abbildung Sprachcode auf Feldname, die einzige Stelle dieser Umsetzung"
  - "open_index registriert acht Ketten, unbedingt, unabhaengig von FINDLING_LANGUAGES"
  - "SCHEMA_VERSION = 2 mit Begruendung im Code"
  - "GOLD_V1_3 neben GOLD_V1_0_AND_V1_1, Ein-Stufen-Test, drift_findings liest gegen beide Tabellen"
  - "AST-Waechter in test_index_open.py: acht register_tokenizer-Aufrufe, keiner unter einem ast.If"
affects: [18-02, 18-03, 18-04, 19-frageseite, 22-messphase]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Registrierung haengt nie an der aktiven Sprachmenge, Befuellung schon"
    - "Zweite Goldtabelle neben der alten statt Edit an der alten (umgedrehte Sperrklinke)"
    - "AST-Waechter mit gestellter Selbstprobe statt Textsuche"

key-files:
  created: []
  modified:
    - backend/src/findling/index/analyzer.py
    - backend/src/findling/index/schema.py
    - backend/src/findling/index/open.py
    - backend/src/findling/config.py
    - backend/tests/test_index_open.py
    - backend/tests/test_upgrade_compatibility.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Die vier register_tokenizer-Zeilen sind mit Task 1 statt mit Task 2 gelandet, weil ein Schemafeld ohne registrierte Kette jeden add_document mit ValueError beendet und der Baum sonst zwischen zwei Commits rot gewesen waere"
  - "drift_findings bekommt die Goldtabelle als Parameter mit dem alten Vorgabewert, statt eine zweite Kopie der Vergleichsschleife fuer GOLD_V1_3 anzulegen"
  - "ALL_MARKS bleibt bei fuenf Eintraegen; der sechste Merker (Sprachmenge) gehoert nach Plan 18-04"
  - "Zahlen und Daten in Codekommentaren in der Schreibweise der Datei (0.40, 2026-09-23), nicht in der deutschen Schreibweise der Abnahmekriterien"

patterns-established:
  - "BODY_FIELD und SNOWBALL_NAME werden durch einen Test gegeneinander gestellt, nach Schluessel und nach Reihenfolge"
  - "Ein Gate liest Quelltext als Text und parst ihn, importiert ihn nie, und traegt eine gestellte Probe gegen einen geloeschten Rumpf"

requirements-completed: [LEX-02]

# Metrics
duration: 42min
completed: 2026-09-24
---

# Phase 18 Plan 01: Schema, Marken und Umbauweg Summary

**Dreizehn Tantivy-Felder mit vier neuen Koerperfeldern fuer es/it/nl/pt, acht unbedingt registrierte Ketten und SCHEMA_VERSION 2 mit umgedrehter statt gruen gemachter Sperrklinke.**

## Performance

- **Duration:** 42 min
- **Started:** 2026-09-24T05:05:00Z
- **Completed:** 2026-09-24T05:47:00Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Das Schema traegt sechs Koerperfelder, unabhaengig von `FINDLING_LANGUAGES`. Die vier neuen stehen ungespeichert zwischen `body_en` und `mtime`, jedes mit eigener Begruendungszeile; der Modulkopf sagt statt "nine fields" jetzt, was die vier leeren Felder gemessen kosten (+0.40 Prozent Verzeichnisgroesse ueber 2000 Dokumente, 2026-09-24) und was vier befuellte Ketten kosten (0.086 mal die Textmenge je Kette).
- `BODY_FIELD` ist die einzige Stelle, an der ein Sprachcode zu einem Feldnamen wird. Ein Test stellt sie nach Schluessel und Reihenfolge gegen `SNOWBALL_NAME`, damit die beiden Abbildungen nicht auseinanderlaufen koennen.
- `open_index` registriert acht Ketten, ohne jede Bedingung. Ein AST-Waechter liest den Syntaxbaum von `open.py` und wird rot, sobald eine Registrierung verschwindet oder unter ein `if` wandert; er traegt drei gestellte Proben, damit ein geloeschter Waechterrumpf nicht null Befunde ueber null Zeilen meldet.
- Zwei Verhaltenstests unter `FINDLING_LANGUAGES=de` belegen die gemessene Falle aus 18-RESEARCH Pitfall 2: das Dokument geht hinein und kommt zurueck, und `body_es` antwortet weiterhin auf der spanischen Kette.
- `SCHEMA_VERSION` steht auf 2. `GOLD_V1_0_AND_V1_1` ist unveraendert stehen geblieben und `GOLD_V1_3` steht daneben, mit Begruendungsabsatz nach der Bauart des `TANTIVY_PIN`-Absatzes; ein Test haelt den Sprung auf genau eine Stufe fest und einer haelt die vier uebrigen Marken am Stillstand.
- Die Baumhash-Ratsche traegt den neuen Hash `a1c7e518...` mit einem Absatz, der die vier bewegten Dateien einzeln nennt. `PACKAGE_FILES_TODAY` bleibt bei 55.

## Task Commits

1. **Task 1: Vier Kettennamen und dreizehn Felder** - `ca739b1` (feat)
2. **Task 2: Acht Ketten, unbedingt registriert** - `964a0d8` (test)
3. **Task 3: SCHEMA_VERSION 2 und die umgedrehte Sperrklinke** - `5156218` (feat)

## Files Created/Modified

- `backend/src/findling/index/analyzer.py` - `TOKENIZER_ES/IT/NL/PT` neben den beiden vorhandenen, benannt nach den Feldcodes, keine neue Fabrik
- `backend/src/findling/index/schema.py` - vier Felder, `BODY_FIELD`, fortgeschriebener Modulkopf mit der Messung vom 2026-09-24
- `backend/src/findling/index/open.py` - vier `register_tokenizer`-Zeilen durch `snowball_analyzer(SNOWBALL_NAME[...])`, mit dem Absatz, der die gemessene Falle und die Kostenfreiheit benennt
- `backend/src/findling/config.py` - `SCHEMA_VERSION = 2` mit Datum, Entscheidnummern und dem Satz, warum es genau eine Stufe ist
- `backend/tests/test_index_open.py` - dreizehn Felder, Abbildungsparitaet, Dokument ueber alle sechs Koerper, AST-Waechter mit Selbstproben, zwei Tests unter `FINDLING_LANGUAGES=de`
- `backend/tests/test_upgrade_compatibility.py` - `GOLD_V1_3`, Goldtabelle als Parameter von `drift_findings`, umgedrehter Versprechenstest, Ein-Stufen-Test
- `backend/tests/test_measurement_scripts.py` - neunzehnter Ratschenabsatz, neuer `PACKAGE_TREE_HASH_TODAY`

## Decisions Made

- **Registrierung wandert in Task 1.** Die Messung aus 18-RESEARCH Pattern 5 sagt, dass ein Textfeld ohne registrierte Kette jeden `writer.add_document` mit `ValueError` beendet, auch fuer Dokumente, die das Feld nicht tragen. Ein Commit mit dreizehn Feldern und vier Ketten haette also die gesamte Suite rot hinterlassen, was gegen die Hausregel "lokal gruen vor dem Commit" steht. Die Zeilen sind deshalb mit dem Schema zusammen gelandet; Task 2 haelt dafuer das Verhalten fest, das sie tragen muessen, und die gestellten Proben des Waechters sind der rote Beweis, den der TDD-Schritt verlangt.
- **`drift_findings` bekommt einen Parameter statt einer Zwillingsfunktion.** Zwei Vergleichsschleifen waeren zwei Arten zu vergleichen, und am Tag einer Korrektur an der einen bliebe die andere gruen. Der Vorgabewert ist die alte Tabelle, also aendert sich an keiner vorhandenen Aufrufstelle etwas.
- **`ALL_MARKS` bleibt bei fuenf.** Der Plan weist den sechsten Merker ausdruecklich Plan 18-04 zu; 18-RESEARCH Pitfall 5 nennt ihn im selben Atemzug wie die Goldtabelle, aber die Planvorgabe geht vor.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die vier Kettenregistrierungen mussten mit dem Schema zusammen landen**
- **Found during:** Task 1 (Vier Kettennamen und dreizehn Felder)
- **Issue:** Der Plan legt die Felder in Task 1 an und die Registrierungen in Task 2. Zwischen den beiden Commits wirft jeder `writer.add_document` eine `ValueError` "Error getting tokenizer for field: body_es" (gemessen 2026-09-24, tantivy 0.26.2, in 18-RESEARCH Pattern 5 protokolliert), also faellt praktisch jeder Test mit einem Schreibvorgang aus, samt der `<verify>`-Zeile von Task 1 selbst.
- **Fix:** Die vier `register_tokenizer`-Zeilen und ihr Begruendungsabsatz sind in den Task-1-Commit gewandert. Task 2 traegt unveraendert das, was ihn ausmacht: den AST-Waechter mit gestellter Probe und die beiden Verhaltenstests unter `FINDLING_LANGUAGES=de`.
- **Files modified:** backend/src/findling/index/open.py
- **Verification:** `uv run python -m pytest -q tests/test_index_open.py tests/test_language_analyzers.py` nach Task 1 gruen (81 Tests), volle Suite nach Task 3 gruen
- **Committed in:** `ca739b1` (Task-1-Commit)

**2. [Rule 3 - Blocking] Tests, die neun Felder festhielten, mussten in Task 1 mitgehen**
- **Found during:** Task 1
- **Issue:** `test_the_schema_carries_exactly_the_nine_documented_fields` und `assert len(FIELDS) == 9` in `test_the_schema_does_not_change_with_the_language_setting` sind Zusicherungen ueber genau die Zahl, die dieser Task bewegt. `backend/tests/test_index_open.py` steht in der Dateiliste des Plans, aber nur bei Task 2.
- **Fix:** Beide Stellen auf dreizehn gehoben, mit Kommentar, seit wann und warum; dazu der vom Plan in Task 1 verlangte Paritaetstest `BODY_FIELD` gegen `SNOWBALL_NAME` und ein Dokument, das alle sechs Koerperfelder fuellt.
- **Files modified:** backend/tests/test_index_open.py
- **Verification:** dieselbe Testfahrt wie oben
- **Committed in:** `ca739b1` (Task-1-Commit)

**3. [Rule 3 - Blocking] `drift_findings` liest jetzt gegen eine uebergebene Goldtabelle**
- **Found during:** Task 3 (SCHEMA_VERSION 2 und die umgedrehte Sperrklinke)
- **Issue:** Die Funktion vergleicht fest gegen `GOLD_V1_0_AND_V1_1`, also gibt es ohne Aenderung keinen Weg, `GOLD_V1_3` mit demselben Leser zu pruefen. Der Ersatztext aus 17-GRUNDSATZ-ENTSCHEID sagt, `drift_findings` bleibe unveraendert, aber das galt dem Aenderungssatz von Plan 17-07.
- **Fix:** Zweiter Parameter `gold_marks` mit dem alten Wert als Vorgabe, die Schleifenvariable bleibt `gold`, der Docstring sagt, warum eine zweite Kopie der Schleife die schlechtere Wahl waere. Keine Aufrufstelle und keine Zeile der alten Goldtabelle bewegt sich.
- **Files modified:** backend/tests/test_upgrade_compatibility.py
- **Verification:** `git diff` entfernt keine Zeile aus `GOLD_V1_0_AND_V1_1` und keine Zeile des Dateikopfs; alle elf Tests der Datei gruen
- **Committed in:** `5156218` (Task-3-Commit)

### Abweichungen in der Schreibweise, nicht in der Sache

- Die Abnahmekriterien verlangen im Modulkopf von `schema.py` die Zahlen "0,40" und "0,086" und im neuen Absatz von `test_upgrade_compatibility.py` das Datum "23.09.2026". Beide Dateien sind englisch und schreiben Zahlen mit Punkt (`0.374`, `0.076` stehen schon dort) und Daten nach ISO (`2026-09-23` steht schon dort, siebenmal). Die Zahlen und das Datum stehen also als `0.40`, `0.086` und `2026-09-23` in den Dateien; die Hausregel "Code, Bezeichner, Kommentare englisch" schlaegt die Schreibweise des Kriteriums.
- Der Modulkopf von `schema.py` enthaelt die Zeichenfolge "zero byte" genau einmal, und zwar in dem Satz, der die Behauptung aus E-17-2 als von dieser Messung korrigiert benennt. Genau das verlangt die Aktionsbeschreibung des Tasks; das Kriterium verbietet die Behauptung, nicht ihre Berichtigung.

---

**Total deviations:** 3 auto-fixed (3 blocking)
**Impact on plan:** Keine Scope-Ausweitung. Alle drei Punkte verschieben Arbeit innerhalb des Plans oder machen sie ueberhaupt erst ausfuehrbar; das Ergebnis ist Zeile fuer Zeile das, was der Plan beschreibt.

## Issues Encountered

- Ein mehrzeiliger Teststring, der im Werkzeugaufruf mit `\n` gebaut wurde, kam mit echten Zeilenumbruechen in der Datei an und machte `test_index_open.py` unparsbar. Behoben durch `textwrap.dedent` mit einem echten dreifach zitierten Block, was die gestellte Probe ohnehin lesbarer macht.
- `ruff` PT018 gegen eine zusammengesetzte Zusicherung im neuen Ein-Stufen-Umfeld; in zwei Zusicherungen zerlegt.

## Verification

- Volle Suite: **2556 bestanden, 15 uebersprungen** (319 s), nach Task 3 gefahren.
- `uv run ruff check`: All checks passed. `uv run ruff format --check`: 129 files already formatted. `uv run pyright`: 0 errors, 0 warnings. `uv run vulture`: ohne Befund.
- `grep -c "add_text_field\|add_unsigned_field\|add_integer_field" backend/src/findling/index/schema.py` meldet 13.
- `grep -v '^ *#' backend/src/findling/index/open.py | grep -c register_tokenizer` meldet 8.
- `grep -n "SCHEMA_VERSION = 2" backend/src/findling/config.py` trifft genau einmal.
- Baumhash-Rezept ueber `backend/src/findling` mit `**/*.py`: `dateien: 55`, `baumhash: a1c7e518ccea7879db7cc869fc24f6ff85cc62ea1d3414a8f41fc844f0fd8c0e`, in `PACKAGE_TREE_HASH_TODAY` nachgezogen und von `tests/test_measurement_scripts.py` (376 Tests) bestaetigt.

## Known Stubs

Keine. Der Plan liefert Schema, Ketten und Marken vollstaendig; die Befuellung der vier neuen Felder (`writer.py`), der sechste Versionsmerker, der Umbau selbst und die Frageseite sind ausdruecklich spaetere Plaene (18-02 ff., 18-04, Phase 19) und keine offenen Enden dieses Plans.

## Threat Flags

Keine neue sicherheitsrelevante Flaeche. Die vier neuen Felder sind ungespeichert und tragen denselben Text, den `body_de` schon traegt; kein neuer Endpunkt, kein neuer Rechtepfad, keine neue Vertrauensgrenze. `T-18-01-01` (Feldnamen aus `BODY_FIELD`), `T-18-01-02` (alle Ketten immer registriert) und `T-18-01-03` (Markensprung nur mit Begruendungsabsatz) sind umgesetzt; `T-18-01-04` ist unveraendert an `LANGUAGE_ALLOWLIST` uebergeben, `T-18-01-SC` gilt: kein Paket installiert, `pyproject.toml` und `uv.lock` nicht angefasst, `tantivy`-Pin unveraendert auf 0.26.2.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 18-02 und die folgenden koennen auf `BODY_FIELD` und auf acht registrierten Ketten aufsetzen; die Befuellungsschleife in `writer.py` hat damit alles, was sie braucht.
- Plan 18-04 findet `ALL_MARKS` bei fuenf Eintraegen vor und `GOLD_V1_3` als die Tabelle, in die der sechste Merker einzutragen ist.
- Offen und bewusst nicht in diesem Plan: `.github/workflows/deploy-harp.yml` haelt "Store upgrade 5" weiterhin gegen `schemaVersion` aus dem Bestand; der zweite Schritt daneben (18-RESEARCH, "Die umgedrehte Beweisstrecke") ist noch nicht gebaut. Solange kein Release laeuft, ist das kein roter Lauf, aber es steht vor der Store-Einreichung 1.3.0.
- Bestandsindizes sind von diesem Plan unberuehrt: `Index.open()` liest das persistierte Schema, `build_schema()` wird auf einer Bestandsinstallation nicht mehr gerufen.

---
*Phase: 18-schema-marken-und-umbauweg*
*Completed: 2026-09-24*

## Self-Check: PASSED

Alle sieben geaenderten Dateien liegen auf der Platte, alle drei Task-Commits stehen in
`git log`, und die Datei traegt keine Em-Dashes.
