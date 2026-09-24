---
phase: 19-frageseite-freischalten
plan: 05
subsystem: tests
tags: [anti-feature, spracherkennung, ast, tokenize, waechter, gegenprobe, fail-closed]

# Dependency graph
requires:
  - phase: 19-frageseite-freischalten
    provides: "field_plan_for(marks, index) aus 19-03, build_query(plan=...) aus 19-01"
  - phase: 06-semantik-und-grenzen
    provides: "test_semantic_boundary.py: das eingefuehrte Muster des Quelltextlesers samt Hygiene"
provides:
  - "backend/tests/test_no_language_detection.py: der Anti-Feature-Waechter, zehn Faelle"
  - "Der Beleg fuer Erfolgskriterium 4 der Roadmap Phase 19"
  - "signature_findings/plan_source_findings/dependency_findings/wire_format_findings: vier Leser, jeder faellt geschlossen"
affects: [19-09 Doku der Frageseite, Phase-19-Verifikation (LEX-05-Haken)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Die Abwesenheit eines Pfades wird strukturell gelesen, nicht funktional geprueft"
    - "Ein Waechter, dessen Quelle verschwindet, meldet einen Befund und nicht null"
    - "Die Hygiene wird aus dem Nachbargate importiert statt zweitgeschrieben"
    - "Ein Verbot, das nicht anschliessbar ist, ist staerker als ein Verbot, das eingehalten werden muss"

key-files:
  created:
    - backend/tests/test_no_language_detection.py
  modified: []

key-decisions:
  - "code_mentions wird aus test_semantic_boundary.py importiert statt kopiert; nur der funktionsweise Leser ist neu, weil es ihn dort nicht gibt"
  - "Der verbotene Parametername wird Teil fuer Teil nach dem Unterstrich verglichen, nicht per Regulaerausdruck"
  - "Die zweite Haelfte von Aussage 1 ist die Annotation: ein Parameter, der genau str ist, kann unter jedem Namen ein Anfragetext sein"
  - "Aussage 4 wird genannt und nicht wiederholt; der Waechter prueft nur, dass test_search_fields_lockstep.py noch da ist und beide Modellnamen fuehrt"
  - "Der REQUIREMENTS-Haken fuer LEX-05 bleibt offen und gehoert der Phase-Verifikation"

requirements-completed: []
# LEX-05 ist mit diesem Plan inhaltlich vollstaendig: 19-03 die aktiven Felder, 19-04 die
# Boosts unterhalb body_en, 19-05 das Anti-Feature. Der Haken in REQUIREMENTS.md wird hier
# trotzdem NICHT gesetzt. Die Arbeitsregel dieses Laufs erlaubt ihn nur, wenn der Plan ihn
# ausdruecklich vorsieht; 19-05-PLAN.md tut das nicht, und `requirements: [LEX-05]` steht
# wortgleich in allen neun Plaenen der Phase, ist also keine planeigene Anweisung. Dazu
# kommt ein sachlicher Grund: die erste Haelfte des LEX-05-Satzes ("die Anfrage durchsucht
# genau die aktiven Sprachfelder") ist bis hier an gerechneten Plaenen und an einem
# Probenindex belegt, auf dem echten Suchweg und im CI erst durch 19-06 und 19-07. Der
# Haken gehoert der Phase-Verifikation.

# Metrics
duration: 38min
completed: 2026-09-24
---

# Phase 19 Plan 05: Anti-Feature-Waechter gegen die Spracherkennung Summary

**Es gibt keinen Spracherkennungspfad, und das steht ab hier nicht mehr als Beschluss in STATE.md, sondern als Quelltextleser in der Suite: die Funktion, die den Feldplan baut, nimmt keinen Parameter entgegen, der ein Anfragetext ist oder einer sein kann, also ist eine Erkennung der Anfrage nicht verboten, sondern nicht anschliessbar**

## Performance

- **Duration:** rund 38 min
- **Started:** 2026-09-25T02:15:00Z
- **Completed:** 2026-09-25T02:53:00Z
- **Tasks:** 2
- **Files modified:** 1 (neu)

## Accomplishments

- `backend/tests/test_no_language_detection.py` existiert mit 451 Zeilen und **zehn bestandenen
  Faellen, null uebersprungen**. Der Modulkopf nennt in dieser Reihenfolge: die Herkunft des
  Anti-Features (einstimmig, in STATE.md unter den Entscheidungen gefuehrt, die den Milestone
  tragen, im Grundsatzpapier von Phase 17 wiederholt, und woertlich als Erfolgskriterium 4 der
  Roadmap Phase 19), warum diese Datei ein Quelltextleser und kein funktionaler Test ist, die
  vier Aussagen einzeln, warum die Hygiene hier die Arbeit und keine Formalie ist, und was die
  Datei ausdruecklich nicht beweist.
- **Aussage 1, die staerkste:** `field_plan_for` in `api/resources.py` hat keinen Parameter, der
  nach einer Suchzeile benannt ist, und keinen, der einer sein koennte. Gelesen ueber den
  Syntaxbaum nach der Vorlage von `functions_calling`, also mit `ast.FunctionDef` und
  `ast.AsyncFunctionDef` in derselben Pruefung, und ueber alle vier Parameterarten
  (`posonlyargs`, `args`, `kwonlyargs`, `vararg`/`kwarg`). Die verbotene Namensmenge steht als
  geschlossene, benannte Konstante `FORBIDDEN_PARAMETER_NAMES` (dreizehn Namen) im Modul.
- **Die zweite Haelfte derselben Aussage ist die Annotation.** Ein Parameter, der genau `str`
  ist, kann unter jedem Namen eine Suchzeile tragen; `TEXT_ANNOTATIONS` haelt die vier Formen
  fest. `Mapping[str, str]` faellt nicht darunter, und das ist der Grund, warum die Annotation
  entfaltet (`ast.unparse`) und nicht als Text durchsucht wird.
- **Aussage 2:** `build_query` fuehrt einen `plan`-Parameter, nennt `settings` in seinem eigenen
  Code kein einziges Mal, und die drei in 19-01 gefallenen Konstanten (`DEFAULT_FIELDS`,
  `TITLE_ONLY_FIELDS`, `FIELD_BOOSTS`) stehen nirgends mehr im Code von `query/rewrite.py`. Der
  Zaehler laeuft ueber den entkommentierten Quelltext: `settings` steht in `rewrite.py` zweimal,
  einmal im Modulkopf und einmal im Docstring von `build_query` selbst, und genau der zweite
  Fall ist der Grund, warum eine Zeilenfilterung hier rot waere.
- **Aussage 3:** weder `backend/pyproject.toml` noch `backend/uv.lock` fuehrt ein Paket der
  Erkennungsfamilie. `FORBIDDEN_PACKAGES` ist geschlossen und benannt und fuehrt `langdetect`,
  `lingua`, `langid`, `py3langid`, `fasttext`, `cld2`, `cld3` und `pycld`; verglichen wird gegen
  einen auf Kleinschreibung und Bindestriche normalisierten Text, weil pypi Unterstrich und
  Bindestrich gleich behandelt. Am 24.09.2026 gegen beide Dateien geprueft: leer.
- **Aussage 4 wird genannt und nicht wiederholt.** `test_search_fields_lockstep.py` haelt
  `extra="forbid"` und die Feldlisten beider Anfragemodelle bereits fest; der Waechter prueft,
  dass diese Datei noch existiert und beide Modellnamen fuehrt, und dupliziert ihre Aussage
  nicht. Zwei Gates fuer eine Behauptung sind zwei Gates, die auseinanderdriften.
- **Jeder der vier Leser faellt geschlossen.** Eine Funktion, die in der Quelle nicht steht,
  ergibt einen Befund und keine leere Liste; eine Abhaengigkeitsdatei, die nicht da ist, ergibt
  einen Befund; ein verschwundenes Nachbargate ergibt einen Befund. Der Fall
  `test_an_emptied_guard_reports_one_finding_per_statement_and_not_zero` faehrt beide
  Richtungen in einer Funktion: gegen den Baum, wie er steht, null Befunde, gegen geleerte
  Quellen und ein leeres Verzeichnis mindestens vier.
- **Fuenf gestellte Muster, vier Gegenproben.** Eine Planfunktion mit `search_text: str` in der
  Signatur erzeugt genau zwei Befunde (Name und Annotation) und ist auf den Wortlaut zugesichert;
  ein Muster, das `settings` und einen Erkennernamen ausschliesslich in Modul-Docstring,
  Kommentar, Zeichenkettenkonstante und Funktions-Docstring nennt, bewegt keinen Zaehler, und
  dass eine naive Zaehlung daran deutlich danebenliegt, steht als eigene Zusicherung daneben
  (naiv mindestens fuenf, hygienisch null); eine Abhaengigkeitsdatei mit einem Erkennernamen
  macht Aussage 3 rot, und das saubere Gegenstueck bleibt gruen.
- **Die Hygiene wird gelesen, nicht nachgebaut.** `code_mentions` kommt per Import aus
  `test_semantic_boundary.py`, in der Form, die dort seit Phase 6 erprobt ist. Neu ist nur
  `names_in_the_code_of`, weil es den funktionsweisen Leser dort nicht gibt: er tokenisiert das
  ganze Modul und filtert auf den Zeilenbereich der Definition, statt den Quellausschnitt zu
  schneiden, und braucht deshalb beides, den Syntaxbaum fuer die Spanne und den Tokenizer fuer
  die Hygiene.
- **Der Waechter loest sich nicht an seiner eigenen Prosa aus, und das ist zugesichert.**
  `test_this_guard_does_not_trip_over_its_own_prose` liest die eigene Datei: naiv gezaehlt stehen
  die verbotenen Woerter zwanzigmal darin (gemessen am 24.09.2026), im entkommentierten Code
  null. Das ist nicht kosmetisch: dieses Modul ist der einzige Ort des Repos, der jeden
  verbotenen Namen buchstabieren muss.
- **Kein Paket installiert, keine Datei unter `backend/src/findling` beruehrt.** Die Ratsche
  `PACKAGE_TREE_HASH_TODAY` bleibt damit unberuehrt, und `git diff --name-only` nennt genau die
  eine neue Datei aus `files_modified`.

## Task Commits

Beide Tasks stehen in einem gemeinsamen Commit, siehe Deviation 1:

1. **Task 1: Die Hygiene und die zwei strukturellen Aussagen** - `0b59fca` (test)
2. **Task 2: Abhaengigkeitsbaum, Wireformat und die gestellten Gegenproben** - `0b59fca` (test)

Nachgezogen: `367f434` (test), siehe Deviation 3.

**Plan metadata:** siehe docs-Commit unten

## Files Created/Modified

- `backend/tests/test_no_language_detection.py` (neu, 451 Zeilen) - Modulkopf, elf benannte
  Konstanten, acht Leser, fuenf gestellte Muster, zehn Faelle

## Decisions Made

- **`code_mentions` wird importiert, nicht kopiert.** Der Plan verlangt die Helfer "in der dort
  erprobten Form"; die staerkste Form davon ist eine Definition statt zweier. `tests/` ist zwar
  kein Paket, aber `from test_analyzer import ...` in `test_language_analyzers.py` ist dafuer der
  eingefuehrte Weg in diesem Baum und laeuft unter pytest wie unter pyright. `call_sites` und
  `functions_calling` werden nicht importiert, weil dieses Modul sie nicht braucht und ein
  unbenutzter Import durch das ruff-Gate faellt; `functions_calling` ist stattdessen die
  genannte Vorlage von `function_of`.
- **Der verbotene Parametername wird Teil fuer Teil verglichen.** `set(name.split("_")) &
  FORBIDDEN_PARAMETER_NAMES` faengt `search_text`, `query_line` und `raw_query` ohne einen
  regulaeren Ausdruck, den beim naechsten Lesen niemand nachvollzieht. Die Menge bleibt dadurch
  geschlossen und trotzdem nicht naiv.
- **Die Annotation ist die zweite Haelfte von Aussage 1.** Ein Parameter `marks: str` waere unter
  einer reinen Namenspruefung erlaubt und trotzdem genau die Luecke, um die es geht. Geprueft
  wird die entfaltete Annotation auf Gleichheit mit einer der vier Textformen, nicht auf
  Vorkommen: sonst waere `Mapping[str, str]` ein Befund und der Waechter am ersten Tag rot.
- **Der funktionsweise Zaehler filtert auf den Zeilenbereich statt auf den Quellausschnitt.**
  `ast.get_source_segment` haette fuer `build_query` funktioniert (eine Funktion auf oberster
  Ebene), aber fuer jede eingerueckte Methode einen `IndentationError` im Tokenizer erzeugt. Der
  Zeilenbereich kostet nichts und macht den Leser auf Methoden anwendbar, ohne dass jemand ihn
  dafuer erst reparieren muss.
- **Aussage 2 zaehlt `settings` in der Funktion und die drei gefallenen Konstanten im ganzen
  Modul.** So steht es im Plan, und der Unterschied hat einen Grund: `settings` darf in
  `rewrite.py` an anderer Stelle durchaus vorkommen (der Modulkopf spricht von Parser-Optionen),
  die drei Konstanten duerfen ueberhaupt nicht mehr vorkommen, weil sie der Ort waeren, an den
  eine Erkennung ihr Ergebnis schreiben wuerde.
- **Der Anker der Abhaengigkeitspruefung ist `tantivy`.** Ohne ihn waere ein Leser, der auf ein
  verschobenes Verzeichnis zeigt, mit null Erkennern in null Bytes gruen. Der eigene Fall
  `test_the_dependency_reader_reads_real_dependency_files` sichert zu, dass beide Dateien den
  Namen der Suchmaschine fuehren, also wirklich gelesen wurden.
- **Der `LEGACY_PLAN`-Vorgabewert von `build_query` ist kein Befund.** Er steht in der Signatur
  und nicht im Rumpf, er ist der eingefrorene Bestandsplan, und er ist ausdruecklich die
  geschlossen fallende Linie aus 19-RESEARCH Pitfall 6. Aussage 2 fragt, ob der Plan aus dem
  Parameter kommt; ein Vorgabewert ist der Parameter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Beide Tasks in einem Commit statt in zweien**
- **Found during:** Task 1 (vor dem ersten Commit)
- **Issue:** `files_modified` nennt genau eine Datei, und beide Tasks schreiben in sie. Ein
  Commit nach Task 1 waere ein Waechter ohne eine einzige Gegenprobe gewesen, also genau der
  Zustand, den Task 2 woertlich als "Dekoration" bezeichnet, und er haette die
  Erfolgskriterien des Plans ("jede Aussage hat eine gestellte Gegenprobe") im Zwischenstand
  verletzt. Git stellt ausserdem ganze Dateien bereit; die zwei Tasks sind an derselben Datei
  nicht trennbar, ohne die Haelfte nachtraeglich wieder herauszuloeschen und die Historie
  unehrlich zu machen.
- **Fix:** Tasks 1 und 2 in der Planreihenfolge ausgefuehrt und je einzeln gegen ihre
  Akzeptanzkriterien geprueft, danach ein gemeinsamer atomarer Commit `0b59fca`. Derselbe
  Grund und dieselbe Loesung wie in 19-01 und 19-03, dort aus der Ratschenregel statt aus dem
  Fussabdruck.
- **Files modified:** keine zusaetzlichen
- **Verification:** Akzeptanzkriterien beider Tasks einzeln geprueft, siehe Verification unten.
- **Committed in:** `0b59fca`

**2. [Rule 2 - Missing] Der Waechter bekommt eine Annotationspruefung, die der Plan nicht nennt**
- **Found during:** Task 1
- **Issue:** Der Plan verlangt "kein Parameter, der Text heisst **oder Text sein kann**", nennt
  als Umsetzung aber nur die geschlossene Namensmenge. Eine reine Namenspruefung laesst
  `marks: str` durch, und das ist kein theoretischer Fall: der zweite Parameter von
  `field_plan_for` heisst heute `index` und traegt ein Objekt; ein Umbau, der ihn auf einen
  Pfad oder eine Zeile umstellt, waere unter einer Namenspruefung unsichtbar.
- **Fix:** `TEXT_ANNOTATIONS` als zweite, ebenfalls geschlossene Konstante, verglichen gegen die
  entfaltete Annotation. Das gestellte Muster deckt beide Haelften ab und sichert beide Befunde
  woertlich zu.
- **Files modified:** keine zusaetzlichen
- **Verification:** `signature_findings(_PLAN_FUNCTION_WITH_A_TEXT_PARAMETER, "field_plan_for")`
  liefert genau zwei Befunde, den Namensbefund und den Annotationsbefund.
- **Committed in:** `0b59fca`

**3. [Rule 1 - Bug] Die Selbstprobe sass genau auf ihrer eigenen Messung**
- **Found during:** Self-Check nach dem ersten Commit
- **Issue:** `test_this_guard_does_not_trip_over_its_own_prose` sicherte `naive >= 20` zu, und
  die naive Zaehlung der verbotenen Woerter in dieser Datei ergibt exakt 20. Eine Schranke, die
  auf ihrer eigenen Messung sitzt, faellt beim naechsten gekuerzten Absatz des Modulkopfs rot,
  und zwar aus einem Grund, um den dieser Fall nicht geht. Die vergleichbaren Selbstproben des
  Repos (`>= 6`, `>= 5`, `>= 3` in `test_semantic_boundary.py`) halten deshalb Abstand.
- **Fix:** Schranke auf 15 gesenkt, die gemessene 20 mit Datum als Kommentar daneben.
- **Files modified:** keine zusaetzlichen
- **Verification:** vier Gates und volle Suite erneut gruen (2794/15), siehe unten.
- **Committed in:** `367f434`

### Befunde, die der Plan nicht vorhergesehen hat

**Die Selbstprobe des Plans ("ein leeres Modul muss einen Befund je erwarteter Aussage liefern")
braucht einen Aggregator, den es noch nicht gab.** Die vier Leser standen zunaechst nebeneinander,
und jeder einzelne haette seine eigene Leerprobe gebraucht. Statt vier fast gleicher Faelle gibt
es jetzt `every_finding(...)`, das alle vier Aussagen in einer Liste beantwortet; der eine Fall
faehrt damit beide Richtungen (stehender Baum: null, geleerte Quellen: mindestens vier) und ist
dadurch staerker als vier getrennte Leerproben, weil er zusaetzlich zusichert, dass die vier
Leser zusammen wirklich vier Aussagen abdecken.

---

**Total deviations:** 3 auto-fixed (Rule 3 Commit-Granularitaet, Rule 2 fehlende Haelfte einer
Aussage, Rule 1 Schranke auf der eigenen Messung)
**Impact on plan:** Kein Scope-Zuwachs, keine zusaetzliche Datei, kein Paket. Deviation 1 aendert
nur die Commit-Granularitaet, Deviation 2 vervollstaendigt eine Aussage, die der Plan woertlich
so verlangt.

## Threat Flags

Keine. Der Plan legt keine Route an, oeffnet keinen Netzpfad, installiert nichts und fasst keine
Datei unter `backend/src/findling` an. Die fuenf Eintraege des Threat-Registers sind umgesetzt und
jeweils von einem Fall belegt:

- **T-19-05-01 (Signatur von `field_plan_for`):**
  `test_the_function_that_builds_the_field_plan_takes_no_search_text` plus die Gegenprobe
  `test_a_plan_function_with_a_text_parameter_makes_that_check_red`, die auf beide Befunde
  woertlich zusichert.
- **T-19-05-02 (`build_query`):**
  `test_the_query_builder_takes_its_field_plan_out_of_its_parameter` ueber den entkommentierten
  Quelltext, mit `test_a_docstring_and_a_comment_full_of_the_forbidden_words_move_no_count` als
  Beleg, dass der Zaehler wirklich zaehlt und nicht an Prosa haengenbleibt.
- **T-19-05-03 (`pyproject.toml`, `uv.lock`):**
  `test_no_dependency_file_of_the_backend_names_a_language_detector`, dazu die Anti-Leerlaufklausel
  `test_the_dependency_reader_reads_real_dependency_files` und die rote Gegenprobe
  `test_a_dependency_file_that_names_a_detector_makes_that_check_red`.
- **T-19-05-04 (der Waechter selbst):**
  `test_an_emptied_guard_reports_one_finding_per_statement_and_not_zero` und
  `test_this_guard_does_not_trip_over_its_own_prose`.
- **T-19-05-SC (Paketinstallation):** entfaellt mangels Gegenstand. Dieser Plan installiert nichts
  und prueft im Gegenteil, dass nichts aus der Erkennungsfamilie dazukommt; `pyproject.toml` und
  `uv.lock` stehen nicht im Diff.

## Known Stubs

Keine.

## Issues Encountered

- Der erste Entwurf setzte `_AN_EMPTIED_SOURCE` und einen Hilfswerfer unterhalb der Faelle, die
  sie benutzen. Das laeuft (Modulnamen werden zur Aufrufzeit aufgeloest), ist aber eine Falle
  fuer den naechsten Leser; beide sind vor ihre Verwendung gezogen worden, der Hilfswerfer ist
  zugunsten einer direkten Zusicherung ganz entfallen.
- Die Datei ist mit LF geschrieben, wie `test_semantic_boundary.py`, und nicht mit CRLF wie das
  in 19-04 entstandene `test_field_plan_ranking.py`. Beides kommt im Arbeitsverzeichnis vor
  (bekannte Lehre vom 14.08.: gemischte Zeilenenden); entscheidend ist Einheitlichkeit
  innerhalb der Datei, und `ruff format --check` meldet 136 Dateien als formatiert. Git meldet
  beim Bereitstellen die uebliche Normalisierungswarnung.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **19-06 (Sprachfaelle auf dem normalen Suchweg)** ist unberuehrt: dieser Plan fasst nichts an,
  was 19-06 liest, und haengt nicht an ihm.
- **19-09 (Doku der Frageseite)** hat ab hier den Satz, auf den die Dokumentation zeigen kann:
  die Erkennung ist nicht verboten, sie ist nicht anschliessbar, und die Datei, die das haelt,
  heisst `backend/tests/test_no_language_detection.py`.
- **Phase-19-Verifikation:** Erfolgskriterium 4 ist belegt. Der REQUIREMENTS-Haken fuer LEX-05
  ist bewusst offen gelassen (siehe `requirements-completed` oben); er gehoert der Verifikation,
  sobald 19-06 und 19-07 die erste Haelfte des LEX-05-Satzes auf dem echten Suchweg und im CI
  belegt haben.
- **Offen und bewusst offen:** der leere Textauszug bei einem reinen Sprachfeld-Treffer (Annahme
  A5 aus 19-03), unveraendert.

## Verification

- `uv run pytest -q tests/test_no_language_detection.py --no-header -rs`: **10 bestanden, null
  uebersprungen** (Akzeptanzkriterium Task 1: mindestens zwei; Task 2: mindestens sechs und
  keinen uebersprungenen).
- `uv run pytest -q` aus `backend/`: **2794 bestanden, 15 uebersprungen, 0 Fehlschlaege**
  (vorher 2784/15; genau die zehn neuen Faelle dazu). Zweimal gefahren, vor `0b59fca` und nach
  der Korrektur `367f434`, beide Male mit demselben Ergebnis.
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 136 files already
  formatted.
- `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src tests --min-confidence 80`: keine Befunde.
- `git status --short` vor dem Commit nannte genau `backend/tests/test_no_language_detection.py`;
  der Commit loescht keine Datei und fasst weder `pyproject.toml` noch `uv.lock` an.
- Akzeptanzkriterien einzeln geprueft:
  - `grep -c "import ast" backend/tests/test_no_language_detection.py` ist 1.
  - `grep -c "import tokenize" backend/tests/test_no_language_detection.py` ist 1.
  - `grep -c "test_search_fields_lockstep" backend/tests/test_no_language_detection.py` ist 3.
  - `grep -c "langdetect" backend/tests/test_no_language_detection.py` ist 6.
  - `grep -rc "langdetect" backend/pyproject.toml backend/uv.lock` meldet 0 in beiden Dateien;
    dasselbe fuer die sieben uebrigen Namen der Familie, einzeln nachgezaehlt.
  - `grep -c '^_[A-Z_]* = ' backend/tests/test_no_language_detection.py` ist 5, also mindestens
    die vier geforderten gestellten Muster.
  - Die geschlossenen Konstanten stehen benannt im Modul: `FORBIDDEN_PARAMETER_NAMES`
    (dreizehn Namen), `TEXT_ANNOTATIONS` (vier Formen), `FORBIDDEN_PACKAGES` (acht Pakete).
- Kein Em-Dash und kein einziges Nicht-ASCII-Zeichen in der neuen Datei, maschinell geprueft
  (`LC_ALL=C grep -n '[^ -~]'` ohne Treffer); Zeilenenden durchgaengig LF, kein Wagenruecklauf.

---
*Phase: 19-frageseite-freischalten*
*Completed: 2026-09-24*

## Self-Check: PASSED

`backend/tests/test_no_language_detection.py` (451 Zeilen) und diese SUMMARY liegen auf der
Platte; die drei Commits `0b59fca`, `fdd2ad4` und `367f434` stehen in der Historie. Der
Self-Check hat zwei Zahlenangaben dieser Datei korrigiert (Zeilenzahl 428 auf 451, naive
Zaehlung 39 auf 20) und dabei Deviation 3 gefunden.
