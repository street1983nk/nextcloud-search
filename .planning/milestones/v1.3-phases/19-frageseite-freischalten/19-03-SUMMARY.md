---
phase: 19-frageseite-freischalten
plan: 03
subsystem: api
tags: [feldplan, schema-marke, sprachmarke, tantivy, readside, fail-closed]

# Dependency graph
requires:
  - phase: 19-frageseite-freischalten
    provides: "FieldPlan, LEGACY_PLAN, NAME_BOOST/TITLE_BOOST/BODY_BOOST, build_query(plan=...) aus Plan 19-01"
  - phase: 18-schema-und-umbau
    provides: "Dreizehn-Felder-Schema, schema_version-Marke, languages-Marke, schema_1_index/schema_2_index-Fixturen"
provides:
  - "SCHEMA_MARK: der Schemaschluessel als oeffentlicher Name neben LANGUAGES_MARK"
  - "field_plan_for(marks, index): der Feldplan aus den zwei gespeicherten Marken, faellt geschlossen, wirft nie"
  - "ReadSide.field_plan: einmal je Oeffnung gerechnet, mit den Handles verworfen"
  - "plan=side.field_plan an allen drei vorhandenen build_query-Aufrufstellen"
  - "backend/tests/test_query_fields_plan.py: die gerechnete Haelfte, jedes Tor mit Gegenprobe"
affects: [19-04 Rangprobe, 19-05 Anti-Feature-Waechter, 19-06 Sprachfaelle auf dem Suchweg, 19-07 CI-Strecke]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Marke hat genau eine Lesart: LEGACY_LANGUAGES wird importiert, nie abgeschrieben"
    - "Das Tor faellt geschlossen: alles, was nicht woertlich die aktuelle Marke ist, ist der Bestandsplan"
    - "Marke als Vertrag, doc_freq-Sonde als Gegenprobe am Verzeichnis selbst"
    - "Kein dritter Prozesscache: der Wert haengt an den Handles, deren Invalidierung es schon gibt"

key-files:
  created: []
  modified:
    - backend/src/findling/index/open.py
    - backend/src/findling/api/resources.py
    - backend/src/findling/api/search.py
    - backend/src/findling/api/snippets.py
    - backend/src/findling/api/diagnose.py
    - backend/tests/test_query_fields_plan.py
    - backend/tests/test_read_side.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Der Plan haengt an ReadSide und bekommt keinen eigenen Cache: die Invalidierung (reset_read_side) und der Generationsschutz (M-18-02) existieren dort bereits"
  - "settings().languages ist als Quelle ausgeschlossen: das ist der Wunsch des Containers, nicht die Wahrheit des Verzeichnisses (T-18-05-01)"
  - "'Befuellt' ist die gespeicherte languages-Marke, nicht filled_languages(): ein Woerterbuchlauf gehoert nicht in den Anfragepfad"
  - "Der Meta-Lesevorgang in read_side() bekommt ein eigenes try, damit der Feldplan nicht verengt, welche Lesehaelfte ueberhaupt aufgeht"

requirements-completed: []
# LEX-05 ist der Auftrag dieses Plans und mit ihm zur Haelfte eingeloest: die Anfrage durchsucht
# genau die aktiven Felder und die Boosts der vier Zusatzsprachen liegen unterhalb body_en. Der
# Haken in REQUIREMENTS.md bleibt offen, bis 19-04 die Rangprobe und 19-05 den Anti-Feature-Waechter
# geliefert haben; erst dann ist auch die zweite Haelfte des Satzes bewiesen statt behauptet.

# Metrics
duration: 74min
completed: 2026-09-24
---

# Phase 19 Plan 03: Feldplan aus den zwei Marken Summary

**Welche Felder eine Anfrage erreicht, entscheidet ab hier das geoeffnete Verzeichnis selbst, gelesen aus seinen zwei gespeicherten Marken, einmal je Oeffnung der Lesehaelfte und mit einem Tor, das geschlossen faellt**

## Performance

- **Duration:** rund 74 min
- **Started:** 2026-09-24T23:05:00Z
- **Completed:** 2026-09-25T00:19:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- `index/open.py` traegt `SCHEMA_MARK: Final = "schema_version"` neben `LANGUAGES_MARK`, und
  `expected_versions` nennt ab hier den Namen statt des Literals. Der Kommentar sagt, warum der Name
  oeffentlich wurde (der Feldplan ist der zweite Leser derselben Marke) und warum `store/repo.py`
  sein eigenes `_SCHEMA_MARK` behaelt (jenes Modul importiert die Indexseite grundsaetzlich nicht).
- `api/resources.py` hat `field_plan_for(marks, index)`. Die Torreihenfolge ist die aus RESEARCH
  Pattern 1: Schemamarke gegen `str(SCHEMA_VERSION)`, Sprachmenge mit der Legacy-Regel aus
  `store/repo.py` gelesen, Feldliste durch Iteration ueber `BODY_FIELD`, Boosts aus `NAME_BOOST`,
  `TITLE_BOOST` und `BODY_BOOST`, Gegenprobe ueber `doc_freq(field, "")` je Koerperfeld. Die Funktion
  wirft unter keiner Eingabe und nimmt keinen Parameter entgegen, dessen Name Text bedeutet.
- `ReadSide` traegt `field_plan: FieldPlan = LEGACY_PLAN` als letztes Feld, und der Plan wird an
  genau der Stelle gerechnet, an der heute `vectors = _read_only_vectors(...)` steht: nach den beiden
  Handles, aus `store.read_meta()` und `index`, innerhalb desselben `_LOCK`. Es entsteht keine neue
  Modulvariable und damit kein dritter Prozesscache neben `_DEGRADED` und `_FILLED`.
- Die drei Aufrufstellen (`api/search.py:255`, `api/snippets.py:194`, `api/diagnose.py:205`) reichen
  `plan=side.field_plan` durch und nichts sonst. Keine der drei Dateien rechnet den Plan selbst,
  keine importiert `field_plan_for`, und `build_query` hat weiterhin genau drei Aufrufstellen unter
  `api/`, also bleibt `store.prefilter_visible` die eine Aufrufstelle, die `test_semantic_boundary.py`
  zaehlt.
- `test_query_fields_plan.py` ist von fuenf auf 29 bestandene Faelle gewachsen, null uebersprungen.
  Jede Aussage des behavior-Blocks hat einen Fall, und die tragenden haben ihre Gegenprobe: der
  Bestandsbeweis gegen den echten Schema-1-Index steht neben dem Fall, der denselben gerechneten Plan
  durch `build_query` schickt; das Tor steht neben der Probe, die dieselbe Marke auf "1" setzt und
  trotz dreizehnfeldrigem Index den Bestandsplan bekommt; die Sonde steht neben der Probe, die eine
  aktuelle Marke gegen einen Schema-1-Index haelt und die Warnzeile ueber `caplog` liest.
- Ein Fall liest die Marken aus einer echten `state.db` ueber `store.read_meta()` und beweist dabei
  zwei Dinge auf einmal: dass die Schluesselnamen beider Seiten zueinander passen, und dass die Saat
  die Sprachmarke ausdruecklich nicht schreibt (T-18-05-01). Erst der Stempel, den ein Rebuild setzt,
  oeffnet die Feldliste.
- `test_read_side.py` bekommt den Fall, der den Verzicht auf einen eigenen Cache traegt: die
  geoeffnete Lesehaelfte traegt ihren Plan, eine Markenaenderung ohne `reset_read_side()` bewegt ihn
  nicht (er wird also wirklich nicht je Anfrage gerechnet), und nach dem Zuruecksetzen traegt die neu
  geoeffnete Haelfte `body_es` mit einem Boost unterhalb `body_en`.
- `PACKAGE_TREE_HASH_TODAY` steht auf `9718e223...`, gemessen aus dem Lauf des Falls
  `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` und nicht geraten;
  `PACKAGE_FILES_TODAY` bleibt 56, `PHP_TREE_HASH_TODAY` ist unberuehrt.

## Task Commits

Die drei Tasks stehen in einem gemeinsamen Commit, siehe Deviation 1:

1. **Task 1: field_plan_for, die zwei Marken und die Gegenprobe am Verzeichnis** - `354ef27` (feat)
2. **Task 2: Die drei Aufrufstellen reichen den Plan durch** - `354ef27` (feat)
3. **Task 3: Der Feldplan als Einheit, gegen echte Verzeichnisse und echte Marken** - `354ef27` (feat)

**Plan metadata:** siehe docs-Commit unten

## Files Created/Modified

- `backend/src/findling/index/open.py` - `SCHEMA_MARK` mit Begruendungsabsatz, `expected_versions`
  nennt den Namen statt des Literals; der zurueckgegebene Schluesselname ist unveraendert
- `backend/src/findling/api/resources.py` - `field_plan_for`, `ReadSide.field_plan`, die Berechnung
  in `read_side()` mit eigenem `try` um den Meta-Lesevorgang; neue Importe `SCHEMA_VERSION`,
  `SCHEMA_MARK`, `LANGUAGES_MARK`, `FIELD_NAME`, `FIELD_TITLE`, `LEGACY_LANGUAGES` und die fuenf
  Namen aus `query/rewrite.py`
- `backend/src/findling/api/search.py` - `plan=side.field_plan` im `build_query`-Aufruf
- `backend/src/findling/api/snippets.py` - dasselbe
- `backend/src/findling/api/diagnose.py` - dasselbe, `title_only=False` unveraendert
- `backend/tests/test_query_fields_plan.py` - zweite Haelfte, 14 neue Testfunktionen (29 Faelle mit
  Parametrisierung), Modulkopf sagt, was ab 19-03 hinzugekommen ist und was die Datei weiterhin nicht
  beweist
- `backend/tests/test_read_side.py` - `test_the_field_plan_is_dropped_with_the_read_side`
- `backend/tests/test_measurement_scripts.py` - siebenunddreissigster Absatz der Ratschenkette plus
  neuer Baumhash

## Decisions Made

- **Der Plan haengt an `ReadSide`, nicht in einem eigenen Cache.** Ein dritter Cache neben `_DEGRADED`
  und `_FILLED` waere die dritte Stelle, an der die Wettlaufsituation aus Audit M-18-02 falsch gemacht
  werden kann, und zwar fuer einen Wert, der sich genau dann aendert, wenn die Handles sich aendern.
  Der Plan braucht auch keinen eigenen Generationszweig, weil er innerhalb des `_LOCK` zusammen mit
  den Handles entsteht statt danach ausserhalb gemessen zu werden. Der neue Fall in
  `test_read_side.py` belegt beide Haelften: er bewegt sich ohne `reset_read_side()` nicht und mit
  ihm schon.
- **Der Meta-Lesevorgang bekommt ein eigenes `try`.** `store.read_meta()` steht im Aufrufer und nicht
  in `field_plan_for`, weil die Signatur `marks` entgegennimmt. Ohne eigenes `try` waere der Lesevorgang
  in dem `try` gelandet, das ueber `read_side()` entscheidet, und eine `state.db`, die sich oeffnen
  laesst und die erste Abfrage verweigert (Null-Byte-Datei nach einem harten Kill), waere ab hier ein
  Container ohne Lesehaelfte gewesen. Das waere eine Verengung dessen, was heute aufgeht, also eine
  Verhaltensaenderung ohne Auftrag. Eine leere Abbildung faellt durch das geschlossene Tor von
  `field_plan_for` und ergibt den Bestandsplan.
- **Die Sprachmenge wird gelesen, nicht geraten.** `LEGACY_LANGUAGES` kommt per Import aus
  `store/repo.py`; eine dritte Schreibweise von `("de", "en")` waere genau die Drift, gegen die dieses
  Repo die Konstante zweimal mit Kommentar und einem Fall festhaelt.
- **`body_de` bekommt keinen Sonderfall** (RESEARCH Pitfall 7). Der Schreibvorgang ist unbedingt, die
  Frage nicht: eine Instanz mit `FINDLING_LANGUAGES=es` durchsucht `body_es`, `name` und `title` und
  nicht die deutsche Kette. Ein eigener Fall haelt das fest.
- **Die Warnzeile der Sonde ist eine Warnung und keine Debugzeile.** Der Unterschied zu
  `filled_languages` steht im Kommentar: dort ist ein fehlendes Feld auf einem Verzeichnis der alten
  Generation der erwartete Zustand, hier heisst dieselbe Ausnahme, dass die zwei Haelften eines Volumes
  nicht zusammengehoeren. Sie fuehrt den Feldnamen und `type(error).__name__` und weder einen Pfad
  noch einen Suchbegriff; der `caplog`-Fall prueft das Zeichen fuer Zeichen.
- **Der Plan haelt sich an das Tor und nicht an den Index.** Die Gegenprobe
  `test_the_mark_and_not_the_directory_decides_which_fields_are_searched` setzt die Marke auf "1"
  gegen den dreizehnfeldrigen Index und belegt in derselben Funktion gegen die Maschine, dass
  `body_es` dort wirklich vorhanden waere. Ohne diesen Fall waere der Bestandsbeweis auch fuer ein Tor
  gruen, das gar nichts prueft.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Alle drei Tasks in einem Commit statt in dreien**
- **Found during:** Task 1 (vor dem ersten Commit)
- **Issue:** Drei getrennte Commits sind hier nicht erreichbar, ohne eine bindende Projektregel zu
  verletzen. Die Arbeitsregel "jede Aenderung unter `backend/src/findling` zieht
  `PACKAGE_TREE_HASH_TODAY` im SELBEN Commit nach" zwingt Task 3 in denselben Commit wie Task 1 und
  Task 2; die Akzeptanzbedingung von Task 3 sagt dasselbe ("`PACKAGE_TREE_HASH_TODAY` ist im Diff
  dieses Plans enthalten"). Ein Commit nach Task 1 allein waere zusaetzlich ein Commit mit rotem Gate
  gewesen, weil der Baumhash dann nicht stimmt und `uv run pytest -q` damit rot ist, was gegen
  "Qualitaetsgates lokal gruen VOR jedem Commit" verstoesst. Derselbe Grund und dieselbe Loesung wie
  in 19-01 und 19-02.
- **Fix:** Tasks 1 bis 3 in der Planreihenfolge ausgefuehrt und je einzeln gegen ihre
  Akzeptanzkriterien und ihre `<verify>`-Laeufe geprueft, danach ein gemeinsamer atomarer Commit
  `354ef27` ueber alle acht Dateien.
- **Files modified:** keine zusaetzlichen
- **Verification:** Task 1: `pytest -q tests/test_read_side.py tests/test_index_open.py
  tests/test_lockstep_versions.py` 94 bestanden. Task 2: `pytest -q tests/test_search_endpoint.py
  tests/test_diagnose_endpoint.py tests/test_semantic_boundary.py` 94 bestanden. Task 3: volle Suite
  und die vier Gates, siehe Verification unten.
- **Committed in:** `354ef27`

**2. [Rule 1 - Bug] Zeilenenden der drei Aufrufstellen mussten nachgezogen werden**
- **Found during:** Task 2 (Gate-Lauf)
- **Issue:** Das Repo hat gemischte Zeilenenden (bekannte Lehre vom 14.08.). Die drei
  `api/*.py`-Dateien liegen als CRLF auf der Platte, die skriptgestuetzte Ersetzung schrieb die acht
  neuen Zeilen je Datei mit LF, und `ruff format --check` meldete daraufhin vier Dateien als
  unformatiert mit einem Diff, der inhaltlich identisch aussah.
- **Fix:** Die vier betroffenen Dateien byte-basiert auf durchgaengiges CRLF gezogen (erst `\r\n` auf
  `\n`, dann `\n` auf `\r\n`), also genau auf den Stand, den sie ohnehin ueberwiegend hatten.
  `resources.py` hatte aus demselben Grund eine einzelne LF-Zeile und ist mitgezogen.
- **Files modified:** keine zusaetzlichen (`api/search.py`, `api/snippets.py`, `api/diagnose.py`,
  `api/resources.py`)
- **Verification:** `ruff format --check .` meldet "134 files already formatted"; die vier Dateien
  zaehlen jetzt gleich viele CRLF wie LF.
- **Committed in:** `354ef27`

**3. [Rule 2 - Missing] Zwei Formulierungen der Prosa mussten den Akzeptanzkriterien weichen**
- **Found during:** Task 1 (Akzeptanzpruefung)
- **Issue:** Der Docstring von `field_plan_for` nannte die ausgeschlossene Quelle woertlich als
  `settings().languages` und die nicht gerufene Funktion woertlich als `filled_languages()`. Beides
  ist Prosa und kein Aufruf, aber `grep -c "settings()"` stieg dadurch von 10 auf 11 und
  `grep -n "filled_languages"` zeigte eine Zeile mit Klammern innerhalb der Funktion. Die zwei
  Akzeptanzkriterien des Plans sind als Greps formuliert; eine Begruendung, die ein Gate ausloest, ist
  eine Falle fuer den naechsten Leser und fuer die Pruefung in 19-05.
- **Fix:** Beide Stellen auf die Sphinx-Verweisform umgeschrieben
  (":func:`findling.config.settings`" und ":func:`filled_languages`"). Die Aussage ist unveraendert,
  die Greps zaehlen wieder 10 und zeigen keinen Aufruf.
- **Files modified:** `backend/src/findling/api/resources.py`
- **Verification:** `grep -c "settings()" backend/src/findling/api/resources.py` ist 10, also nicht
  groesser als vor diesem Plan.
- **Committed in:** `354ef27`

### Befunde, die der Plan nicht vorhergesehen hat

**Die Saat schreibt die Sprachmarke nicht, und der erste Entwurf des state.db-Falls rechnete damit.**
Der Fall `test_the_marks_of_a_real_state_database_are_the_ones_the_plan_reads` erwartete zunaechst,
dass eine mit `expected_versions(digest, "de,en,es")` gesaete `state.db` den Feldplan mit `body_es`
ergibt. Der Lauf war rot, und zwar richtigerweise: `store.repo._DEFAULT_META` laesst `languages`
ausdruecklich aus, weil eine Saat sonst den Wunsch eines Containers als Tatsache ueber ein
Verzeichnis hinschreiben wuerde (T-18-05-01). Der Fall ist daraufhin staerker geworden statt
angepasst: er belegt jetzt beide Seiten, `LANGUAGES_MARK not in seeded` und den Plan nach dem
Stempel, den ein Rebuild setzt. Das ist keine Abweichung vom Plan, sondern ein Beleg fuer dessen
Entscheid, die Marke und nicht die Konfiguration zu lesen.

---

**Total deviations:** 3 auto-fixed (Rule 3 blockierend, Rule 1 Zeilenenden, Rule 2 Prosa gegen Gate)
**Impact on plan:** Kein Scope-Zuwachs. Deviation 1 aendert nur die Commit-Granularitaet, Deviation 2
ist Routine des Qualitaetsgates, Deviation 3 beruehrt nur zwei Formulierungen eines Docstrings.

## Threat Flags

Keine. Der Plan legt keine Route an, oeffnet keinen Netzpfad und fasst weder `backend/pyproject.toml`
noch `backend/uv.lock` an (T-19-03-SC damit mangels Gegenstand erfuellt, im Diff steht keine der
beiden Dateien). Die sechs uebrigen Eintraege des Threat-Registers sind umgesetzt und jeweils von
einem Fall belegt:

- **T-19-03-01 (Schema-Tor):** `test_a_schema_generation_this_code_never_saw_is_no_permission` ueber
  "3", "", "abc" und "UNKNOWN_VERSION", `test_a_directory_without_a_schema_mark_is_no_permission_either`
  und die Gegenprobe `test_the_mark_and_not_the_directory_decides_which_fields_are_searched`.
- **T-19-03-02 (state.db neben aelterem Verzeichnis):** `doc_freq(field, "")` je Koerperfeld;
  `test_a_state_database_beside_an_older_directory_falls_back_and_says_so` belegt Rueckfall und
  Warnzeile.
- **T-19-03-03 (Feldliste aus Nutzereingabe):** `def field_plan_for(marks: Mapping[str, str],
  index: Index)` hat keinen Parameter, dessen Name Text bedeutet. Der Syntaxbaum-Waechter in 19-05
  uebernimmt die Bewachung.
- **T-19-03-04 (zweite Suchroute):** drei `plan=side.field_plan`, weiterhin drei `build_query(`
  unter `api/`, `test_semantic_boundary.py` gruen.
- **T-19-03-05 (Warnzeile):** die Zeile fuehrt Feldnamen und Ausnahmetyp; der `caplog`-Fall prueft
  ausdruecklich, dass weder "/" noch der Rueckschraegstrich darin vorkommt.
- **T-19-03-06 (Term-Woerterbuchlauf):** `filled_languages` wird von `field_plan_for` nicht gerufen;
  `grep` zeigt innerhalb der Funktion nur Verweise in Docstring und Kommentar.

## Known Stubs

Keine.

## Issues Encountered

- Die zwei Prosastellen, die weiter den in 19-01 gefallenen Namen `DEFAULT_FIELDS` nennen
  (`backend/src/findling/store/repo.py` Zeilen 128 und 1448), sind NICHT mitgenommen worden. Der
  Fussabdruck gab es nicht her: `files_modified` nennt acht Dateien, `repo.py` ist keine davon, und
  die Verifikation des Plans verlangt woertlich, dass `git diff --stat` genau diese acht nennt.
  `repo.py` wird von diesem Plan nur gelesen (`LEGACY_LANGUAGES` per Import). Die Kleinigkeit bleibt
  in STATE.md stehen und wartet auf den naechsten Plan, der `store/repo.py` ohnehin anfasst.
- Der Messlauf der Ratsche musste zweimal laufen: einmal, um den neuen Baumhash ueberhaupt zu
  erfahren (der Fall meldet den gemessenen Wert im Assertion-Diff), und einmal zur Bestaetigung nach
  dem Nachziehen. Das ist die vom Plan vorgesehene Reihenfolge ("aus dem Lauf genommen und nicht
  geraten") und kein Fehlschlag.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **19-04 (Rangprobe)** hat alles, was sie braucht: `field_plan_for` liefert fuer jede Sprachmenge
  einen Plan, und die Zusicherung `plan.boosts[body_es] < plan.boosts[body_en]` steht bereits als
  Fall. Was 19-04 nachliefert, ist die gemessene Zahl hinter der 0.6, und der Ort dafuer ist
  unveraendert `BODY_BOOST` in `query/rewrite.py`.
- **19-05 (Anti-Feature-Waechter)** findet die Signatur vor, die es ueber den Syntaxbaum bewachen
  soll: `field_plan_for(marks: Mapping[str, str], index: Index) -> FieldPlan`, ohne einen Parameter,
  dessen Name Text bedeutet. Die zweite Aussage des Waechters (`build_query` liest den Plan nur aus
  seinem Parameter) ist ebenfalls schon wahr.
- **19-06 (Sprachfaelle auf dem Suchweg)** kann ab hier den echten Weg gehen: ein Plan aus einer
  Marke mit dem Sprachcode, durch `build_query` gegen `schema_2_index`. Der Haken aus RESEARCH
  Pattern 4 bleibt bestehen und gehoert dorthin: auf dem normalen Suchweg stehen alle aktiven Felder
  in der Liste, also beweist ein Formenpaar, das die deutsche oder englische Kette selbst
  zusammenfuehrt, dort nichts mehr.
- **Offen und bewusst offen:** der leere Textauszug bei einem reinen Sprachfeld-Treffer
  (`SnippetGenerator` haengt an `FIELD_BODY_DE`, RESEARCH Messung M-4 und Pitfall 4). Dieser Plan hat
  ihn nicht angefasst; er ist als Annahme A5 gefuehrt und gehoert in die Doku von 19-09 oder in einen
  eigenen Plan, falls der Owner ihn als Mangel wertet.

## Verification

- `uv run pytest -q` aus `backend/`: **2776 bestanden, 15 uebersprungen, 0 Fehlschlaege** (vorher
  2751/15; 25 Faelle dazu).
- `uv run pytest -q tests/test_query_fields_plan.py --no-header -rs`: 29 bestanden, null
  uebersprungen (Akzeptanzkriterium "mindestens zehn, keinen uebersprungenen").
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 134 files already
  formatted.
- `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src tests --min-confidence 80`: keine Befunde.
- `git diff --stat` nennt genau die acht Dateien aus `files_modified`; `pyproject.toml` und `uv.lock`
  stehen nicht im Diff, der Commit loescht keine Datei.
- Akzeptanzkriterien einzeln geprueft:
  - `grep -n "SCHEMA_MARK" backend/src/findling/index/open.py` zeigt Definition (Zeile 94) und
    Verwendung in `expected_versions` (Zeile 205).
  - `uv run python -c "from findling.index.open import expected_versions, SCHEMA_MARK, LANGUAGES_MARK; m=expected_versions('d','de,en'); assert SCHEMA_MARK in m and LANGUAGES_MARK in m"`
    endet mit Status 0.
  - `grep -c "settings()" backend/src/findling/api/resources.py` ist 10, unveraendert.
  - `grep -n "def field_plan_for"` zeigt `(marks: Mapping[str, str], index: Index)`.
  - `grep -rn "plan=side.field_plan" backend/src/findling/api/` liefert genau drei Zeilen, je eine in
    search.py, snippets.py und diagnose.py; `grep -rn "build_query(" backend/src/findling/api/`
    weiterhin genau drei; `grep -rn "field_plan_for"` in den drei Dateien keine Zeile.
  - `grep -n "^_[A-Z_]* *[:=]" backend/src/findling/api/resources.py` zeigt dieselben sieben
    Modulvariablen wie vorher, keine neue.
  - `grep -c "caplog"` = 3 und `grep -c "read_meta()"` = 2 in `test_query_fields_plan.py`.
  - `grep -n "PACKAGE_FILES_TODAY = 56"` liefert genau eine Zeile (945).
- Kein Em-Dash und kein einziges Nicht-ASCII-Zeichen in einer der acht Dateien, maschinell geprueft.

---
*Phase: 19-frageseite-freischalten*
*Completed: 2026-09-24*

## Self-Check: PASSED

Alle acht beruehrten Dateien und die SUMMARY liegen auf der Platte, der Commit `354ef27` steht in der
Historie, das Arbeitsverzeichnis traegt ausser den Planungsdateien nichts Offenes.
