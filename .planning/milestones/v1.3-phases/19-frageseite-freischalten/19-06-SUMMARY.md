---
phase: 19-frageseite-freischalten
plan: 06
subsystem: tests
tags: [sprachfaelle, suchweg, feldplan, analysekette, gegenprobe, tantivy]

# Dependency graph
requires:
  - phase: 19-frageseite-freischalten
    provides: "FieldPlan, build_query(plan=...), LEGACY_PLAN aus 19-01"
  - phase: 19-frageseite-freischalten
    provides: "field_plan_for(marks, index) und SCHEMA_MARK aus 19-03"
  - phase: 19-frageseite-freischalten
    provides: "die italienische Flexionsfamilie in chain_cases_it.txt aus 19-02"
  - phase: 18-schema-und-umbau
    provides: "test_language_cases_field_level.py als Kopiervorlage, BODY_FIELD, die dreizehn Felder"
provides:
  - "backend/tests/test_language_cases_query_path.py: die vier Sprachfaelle auf dem normalen Suchweg"
  - "Der dritte Ketten-Ausschluss: das Formenpaar muss von der englischen UND der deutschen Kette getrennt werden"
  - "Je Sprache eine Gegenprobe mit einem Plan ohne body_<code> und eine mit der Bestandsmarke"
affects: [19-07 CI-Sprachbeweis, 19-09 Doku der Frageseite]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Der Fallindex traegt den Bestand, den eine echte Instanz schreibt: body_de, body_en und das Feld der Sprache"
    - "Die Auswahl des Formenpaares ist eine Zusicherung, nie ein Kommentar, und sie stellt drei Ketten gegeneinander"
    - "Jede Behauptung auf dem Suchweg hat ihre Gegenprobe am Feldplan: ohne das Feld faellt der Beleg weg"
    - "Kein Textauszug wird geprueft, weil ein reiner Sprachfeld-Treffer gemessen ohne Auszug zurueckkommt"

key-files:
  created:
    - backend/tests/test_language_cases_query_path.py
  modified: []

key-decisions:
  - "Der Fallindex schreibt den Text in drei Koerperfelder statt in eines: genau das tut index/writer.py auf einer Instanz mit de,en,<code>, und nur dann hat der dritte Ausschluss ueberhaupt einen Gegenstand"
  - "Die Gegenprobe behauptet den Verlust der anderen Form und nicht die leere Trefferliste, weil das Dokument mit der getippten Form dieselbe Form in body_de traegt"
  - "Der Hauptfall laeuft unter dem weitesten Feldplan, den das Schema zulaesst (alle sechs Koerperfelder); der gerechnete Plan aus der echten state.db ist der schmalere und steht daneben"
  - "Kein schwaecheres Auswahlkriterium als Rueckfall: auf dem Suchweg beweist ein Paar, das die anderen zwei Ketten zusammenfuehren, gar nichts"

requirements-completed: []
# LEX-05 bleibt ungehakt. Dieser Plan liefert die Testebene der ersten Haelfte des Satzes; die
# CI-Haelfte liefert 19-07, und der Haken gehoert nach dem Stand von STATE.md der
# Phase-Verifikation. Ein Haken hier waere eine Behauptung ueber einen Lauf, den es noch nicht gibt.

# Metrics
duration: 22min
completed: 2026-09-25
---

# Phase 19 Plan 06: Die vier Sprachfaelle auf dem normalen Suchweg Summary

**Die Frage laeuft ab hier durch `build_query` mit einem Feldplan statt gegen ein einzelnes Feld, und damit das etwas beweist, muss das Formenpaar von der eigenen Kette zusammengefuehrt und von der englischen wie der deutschen getrennt werden**

## Performance

- **Duration:** rund 22 min
- **Started:** 2026-09-24T22:03:00Z
- **Completed:** 2026-09-24T22:25:00Z
- **Tasks:** 3
- **Files modified:** 1 (neu)

## Accomplishments

- `backend/tests/test_language_cases_query_path.py` steht mit 549 Zeilen und **37 bestandenen
  Faellen, null uebersprungen**. Die Vorlage ist `test_language_cases_field_level.py`, wie der Plan
  es vorsieht; der Modulkopf sagt in vier Absaetzen, was hier anders ist und warum jeder Unterschied
  eine Zusicherung und keinen Kommentar bekommt.
- `_separated_pairs` traegt den **dritten Ausschluss**: das Paar muss von der eigenen Kette
  zusammengefuehrt und von der englischen UND der deutschen Kette auf zwei Termen gehalten werden.
  Die deutsche Kette kommt aus `cached_german_analyzer(wordlist_hash(CONSTITUENTS), CONSTITUENTS)`,
  also unter demselben Digest, mit dem `open_index` sie registriert: das teure Automat wird einmal je
  Sitzung gebaut und dieses Modul zahlt nichts dafuer.
- Das Kriterium liefert fuer alle vier Sprachen ein Paar, gemessen im Lauf dieses Plans: es zwei
  Paare, it eines (die Familie, die 19-02 aufgenommen hat), nl zwei, pt zwei. Das deckt sich mit
  RESEARCH Messung M-5 und M-6. `_case_pair` nimmt das ERSTE qualifizierende Paar, und
  `test_the_fixture_offers_a_pair_no_other_shipped_chain_merges` behauptet je Code, dass es ein
  solches ueberhaupt gibt.
- Ein Rueckfall auf das schwaechere Kriterium gibt es hier nicht mehr. `_distinguished_pairs` ist
  bewusst NICHT mitkopiert: auf dem Suchweg beweist ein Paar, das die anderen zwei Ketten
  zusammenfuehren, nichts, also ist eine Fixture ohne Flexionsfamilie ein roter Fall und kein
  leiserer.
- Der Fallindex traegt den Bestand, den eine echte Instanz schreibt: derselbe Text in `body_de`
  (unbedingt, weil es die einzige gespeicherte Kopie ist), in `body_en` und im Feld der Sprache,
  genau wie `index/writer.py` es auf einer Instanz mit `de,en,<code>` tut. Ein eigener Fall behauptet
  diesen Bestand feldweise und behauptet zugleich, dass die drei uebrigen Koerperfelder leer sind.
- Der Hauptfall laeuft unter `FULL_PLAN`, dem weitesten Feldplan, den das Schema zulaesst (alle sechs
  Koerperfelder plus `name` und `title`, Gewichte aus `BODY_BOOST`, `NAME_BOOST` und `TITLE_BOOST`).
  Die Frage in der einen Form findet das Dokument mit der anderen, in beiden Richtungen, mit
  Gleichheit statt "enthaelt", damit ein Treffer auf den Ablenker auffaellt.
- Je Sprache steht die Gegenprobe daneben: derselbe Fall mit einem Plan ohne `body_<code>` verliert
  das Dokument mit der anderen Form. Es bleibt genau das Dokument uebrig, das die getippte Form
  selbst traegt, und der Fall behauptet diese exakte Antwort (siehe Deviation 1).
- Je Sprache rechnet ein Fall seinen Plan ueber `field_plan_for` aus den Marken einer echten
  `state.db`, gesaet mit `expected_versions` und gestempelt mit der Sprachmarke, wie es
  `stamp_after_swap` tut. Daneben steht das Sicherheitstor aus der Sprachrichtung: dieselbe `state.db`
  mit `schema_version` auf "1" ergibt woertlich `LEGACY_PLAN`, und der Fall verliert die andere Form.
- `test_no_form_of_the_case_stands_in_this_file` ist mitkopiert, samt `SOURCE_WORDS`. Die Datei
  enthaelt kein einziges Nicht-ASCII-Zeichen; keine Form und kein Ablenker steht als Wort darin.
- Kein Textauszug wird irgendwo geprueft. Der Modulkopf nennt die Grenze (`SnippetGenerator` haengt an
  `FIELD_BODY_DE`, `index/search.py:875`, RESEARCH M-4) und bezieht sich auf den Treffer, wie Pitfall 4
  es verlangt.

## Task Commits

Die drei Tasks stehen in einem gemeinsamen Commit, siehe Deviation 2:

1. **Task 1: Die Auswahllogik mit dem dritten Ausschluss** - `6c20b11` (test)
2. **Task 2: Die vier Faelle auf dem Suchweg und ihre Gegenprobe** - `6c20b11` (test)
3. **Task 3: Ein Fall rechnet den Plan aus einer echten Marke** - `6c20b11` (test)

**Plan metadata:** siehe docs-Commit unten

## Files Created/Modified

- `backend/tests/test_language_cases_query_path.py` (NEU) - 549 Zeilen, 37 Faelle. Modulkopf,
  `SOURCE_WORDS`, `CONSTITUENTS`, `STOCK_LANGUAGES`, `FULL_PLAN`, die Auswahl (`_pairs`, `_terms`,
  `_share_a_term`, `_separated_pairs`, `_case_pair`, `_distractor`), der Indexaufbau
  (`_write_case_index`), die Planschere `_without`, der Suchweg `_found`, die Markenquelle `_marks_of`,
  neun Fixtures und zehn Testfunktionen

Keine weitere Datei im Diff. `backend/src/findling` ist nicht angefasst, also bleiben
`PACKAGE_TREE_HASH_TODAY`, `PACKAGE_FILES_TODAY` und `PHP_TREE_HASH_TODAY` unberuehrt;
`backend/pyproject.toml` und `backend/uv.lock` stehen nicht im Diff.

## Decisions Made

- **Der Fallindex schreibt den Text in drei Koerperfelder, nicht in eines.** Das ist die einzige
  Bauart, unter der der dritte Ausschluss einen Gegenstand hat. Die Vorlage schreibt ein Feld je Fall,
  weil dort nur ein Feld in der Frage steht; hier stehen alle aktiven Felder in der Frage, und eine
  echte Instanz mit `de,en,<code>` traegt denselben Text in `body_de` (einzige gespeicherte Kopie),
  in `body_en` und im Feld der Sprache. Ein Index, der nur das Sprachfeld befuellt, existiert auf
  keiner Installation, und gegen ihn waere der Ausschluss der deutschen Kette folgenlos: ein leeres
  Feld antwortet nicht. RESEARCH Pitfall 4 misst dieselbe Bauart ("Ein Index mit
  `body_de`/`body_en`/`body_es`, Dokument in allen drei Feldern").
- **Der Hauptfall laeuft unter dem weitesten Plan, der gerechnete steht daneben.** `FULL_PLAN` fuehrt
  alle sechs Koerperfelder, also mehr Felder, als der Index befuellt. Das ist die haerteste Fassung
  der Frage: was hier antwortet, antwortet ueberall. Der Plan, den eine echte Instanz bekaeme, ist der
  schmalere `de,en,<code>`, und den rechnet Task 3 aus den Marken. Beide Faelle stehen nebeneinander,
  weil sie verschiedene Dinge behaupten.
- **Die drei uebrigen Sprachfelder werden absichtlich NICHT befuellt.** Eine Instanz mit allen sechs
  Ketten waere denkbar, aber dann koennte eine Nachbarkette das Paar zusammenfuehren (die
  portugiesische stemmt spanische Pluralformen aehnlich), und der Fall waere aus dem falschen Grund
  gruen. Der Bestand ist deshalb der einer realen Ausbau-Instanz, die Frage dagegen die weiteste.
- **Kein Rueckfall auf `_distinguished_pairs`.** Das schwaechere Kriterium der Feldebene sagt "die
  englische Kette haette diese Terme nicht geschrieben". Auf dem Suchweg ist das ohne Wert: ob ein
  Term geschrieben worden waere, entscheidet nicht, ob ein anderes Feld die Frage beantwortet. Die
  Fehlermeldung von `_case_pair` sagt stattdessen, was zu tun ist (Flexionsfamilie in die Fixture,
  Messung neu fahren, Zaehlgate nachziehen), also derselbe Weg, den 19-02 gegangen ist.
- **`_without` schneidet beide Haelften des Plans.** Eine Gegenprobe, die das Feld aus der Liste
  nimmt und sein Gewicht stehen laesst, misst nicht eine schmalere Suche, sondern die `ValueError`
  aus RESEARCH Messung M-1. Das waere ein gruener Fall ueber einen kaputten Aufruf.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die Gegenprobe behauptet den Verlust der anderen Form, nicht die leere Liste**
- **Found during:** Task 2 (beim Schreiben der Gegenprobe)
- **Issue:** Der Plan schreibt "derselbe Fall mit einem Plan OHNE `body_<code>` findet nichts". Auf
  dem Index, den derselbe Task verlangt (der Bestand einer echten Instanz, also Text auch in
  `body_de` und `body_en`), ist dieser Satz nicht wahr und kann es nicht sein: das Dokument, das die
  getippte Form traegt, traegt dieselbe Zeichenkette in `body_de`, und eine Frage antwortet immer mit
  sich selbst. Eine Zusicherung auf die leere Liste waere rot gewesen, und der einzige Weg, sie gruen
  zu bekommen, waere ein Index ohne deutschen und englischen Bestand gewesen, also genau der Index,
  der den dritten Ketten-Ausschluss gegenstandslos macht.
- **Fix:** Die Gegenprobe behauptet die exakte Antwort `[TYPED_DOCUMENT]` fuer die eine und
  `[WRITTEN_DOCUMENT]` fuer die andere Richtung: was verschwindet, ist die Zusammenfuehrung, und die
  ist der ganze Gegenstand. Der Modulkopf und der Kommentar des Falls sagen beides in drei Saetzen,
  damit der naechste Leser die Abweichung vom Plansatz nicht fuer eine Nachlaessigkeit haelt.
- **Files modified:** keine zusaetzlichen
- **Verification:** Der Fall ist scharf und nicht weichgespuelt: unter `FULL_PLAN` lautet die Antwort
  `[1, 2]`, unter demselben Plan ohne `body_<code>` lautet sie `[1]`. Beide Zusicherungen sind gruen,
  also traegt das Feld den Unterschied.
- **Committed in:** `6c20b11`

**2. [Rule 3 - Blocking] Alle drei Tasks in einem Commit statt in dreien**
- **Found during:** Task 1 (vor dem ersten Commit)
- **Issue:** Die drei Tasks bauen eine einzige neue Datei in drei Schichten, und ihre Begruendung ist
  ein zusammenhaengender Modulkopf. Drei Commits haetten bedeutet, denselben Kopf dreimal zu
  schreiben und zweimal wieder umzuschreiben, weil die Absaetze ueber Gegenprobe und Markenquelle in
  Schicht 1 noch nichts beschreiben. Dazu kommt das Gate: eine Zwischenfassung mit den Importen der
  spaeteren Schichten faellt bei `ruff check` (F401) durch, und ein Commit mit rotem Gate verstoesst
  gegen die bindende Projektregel. Derselbe Grund und dieselbe Loesung wie in 19-01, 19-02 und 19-03.
- **Fix:** Die drei Tasks in der Planreihenfolge gebaut und einzeln gegen ihre Akzeptanzkriterien
  geprueft, danach ein atomarer Commit `6c20b11` ueber die eine Datei.
- **Files modified:** keine zusaetzlichen
- **Verification:** Task 1: das Auswahlkriterium liefert je Code ein Paar (es 2, it 1, nl 2, pt 2),
  `grep -c "german\|CONSTITUENTS"` ist 16, `grep -c "informaciones"` ist 0. Task 2:
  `grep -c "build_query"` ist 4, `grep -c "fragment()\|highlighted()"` ist 0, der Modullauf meldet
  37 bestanden und null uebersprungen. Task 3: `grep -c "field_plan_for"` ist 3, volle Suite und
  vier Gates gruen, siehe Verification unten.
- **Committed in:** `6c20b11`

---

**Total deviations:** 2 auto-fixed (Rule 1 an der Gegenprobe, Rule 3 an der Commit-Granularitaet)
**Impact on plan:** Kein Scope-Zuwachs, keine zusaetzliche Datei. Deviation 1 macht eine Zusicherung
praeziser, statt sie abzuschwaechen; Deviation 2 aendert nur die Commit-Granularitaet.

## Threat Flags

Keine. Der Plan legt keine Route an, oeffnet keinen Netzpfad, fasst weder `backend/src/findling` noch
`php/` an und installiert kein Paket (T-19-06-SC damit mangels Gegenstand erfuellt,
`backend/pyproject.toml` und `backend/uv.lock` stehen nicht im Diff). Die vier uebrigen Eintraege:

- **T-19-06-01 (das Paar ist Geschmack des Autors):** `_case_pair` nimmt das erste Paar, das drei
  Ketten gegeneinander bestehen, und `test_the_fixture_offers_a_pair_no_other_shipped_chain_merges`
  sowie `test_neither_the_english_nor_the_german_chain_merges_the_case_pair` behaupten das je Code.
  Keine Form steht als Literal in der Datei, belegt von `test_no_form_of_the_case_stands_in_this_file`.
- **T-19-06-02 (gruener Fall ohne Wirkung):** zwei Gegenproben je Sprache,
  `test_a_plan_without_the_field_of_the_language_loses_the_other_form` und
  `test_the_legacy_mark_of_a_real_state_database_loses_the_other_form`.
- **T-19-06-03 (Suite-Laufzeit):** das Modul laeuft in 0,51 s, vier kleine Indizes in
  `tmp_path_factory`, die deutsche Kette aus dem Prozesscache. Die volle Suite steht bei 239,91 s.
- **T-19-06-04 (Testdaten):** ausschliesslich Wortformen aus den Messfixturen; keine Nutzerdaten,
  keine Protokollzeile mit einem Suchbegriff.

## Known Stubs

Keine.

## Issues Encountered

- Der Plansatz "findet nichts" der Gegenprobe ist auf dem vom selben Plan verlangten Index nicht
  erfuellbar. Siehe Deviation 1; die Zusicherung ist praeziser geworden statt schwaecher.
- Die Akzeptanzbedingung von Task 3 verlangt "`git diff --name-only` nennt genau
  `backend/tests/test_language_cases_query_path.py`". Vor dem Commit war die Datei unverfolgt, also
  meldete `git diff --name-only` nichts und `git status --short` die eine Zeile `?? ...`. Nach dem
  Commit nennt `git show --name-only 6c20b11` genau diese eine Datei; das ist dieselbe Aussage,
  gelesen am richtigen Werkzeug.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **19-07 (CI-Sprachbeweis)** hat die Testebene von Erfolgskriterium 1 unter sich: je Sprache ist
  belegt, dass die Frage in einer Form das Dokument mit der anderen ueber den normalen Suchweg
  findet, und dass der Beleg mit dem Feld faellt. Was 19-07 nachliefert, ist derselbe Satz gegen eine
  laufende Nextcloud auf allen vier Matrix-Aesten. Die Warnung aus RESEARCH Pitfall 4 gilt dort
  unveraendert: die Probe muss den Treffer behaupten und nicht den Textauszug.
- **19-09 (Doku)** kann den dritten Ketten-Ausschluss als Grenze aufnehmen: welche Paare eine Sprache
  ueberhaupt beweisbar machen, steht jetzt als Kriterium im Code und nicht mehr nur im Messbericht.
- **Offen und bewusst offen:** der leere Textauszug bei einem reinen Sprachfeld-Treffer (Annahme A5).
  Dieses Modul prueft ihn ausdruecklich nicht und nennt den Grund im Kopf.
- **LEX-05** bleibt ungehakt, siehe Frontmatter.

## Verification

- `uv run pytest -q tests/test_language_cases_query_path.py --no-header -rs`: **37 bestanden, null
  uebersprungen**, 0,51 s.
- `uv run pytest -q` aus `backend/`: **2831 bestanden, 15 uebersprungen, 0 Fehlschlaege** (vorher
  2794/15; 37 Faelle dazu).
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 137 files already
  formatted.
- `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src tests --min-confidence 80`: keine Befunde.
- Akzeptanzkriterien einzeln geprueft:
  - `grep -c "german\|CONSTITUENTS"` = 16 (verlangt: groesser 0).
  - `grep -c "build_query"` = 4 (verlangt: mindestens 2).
  - `grep -c "fragment()\|highlighted()"` = 0.
  - `grep -c "informaciones"` = 0.
  - `grep -c "field_plan_for"` = 3 (verlangt: mindestens 1).
  - `grep -c "chain_cases"` = 1 (key_link der Frontmatter).
  - 549 Zeilen (verlangt: mindestens 150).
  - Je Code ein Fall, der das qualifizierende Paar behauptet, und er ist fuer alle vier Codes gruen.
  - Je Code ein Fall ueber `build_query` und je Code eine Gegenprobe ohne das zugehoerige Feld.
  - Ein Fall je Code rechnet den Plan aus einer echten `state.db`, und ein Fall je Code sichert die
    Abwesenheit des Belegs unter Schema 1 zu.
- `git show --name-only 6c20b11` nennt genau `backend/tests/test_language_cases_query_path.py`; der
  Commit loescht keine Datei (`git diff --diff-filter=D HEAD~1 HEAD` ist leer).
- Kein Em-Dash und kein einziges Nicht-ASCII-Zeichen in der neuen Datei, maschinell geprueft; die
  Akzente stehen ausschliesslich in den Fixture-Dateien.

---
*Phase: 19-frageseite-freischalten*
*Completed: 2026-09-25*

## Self-Check: PASSED

Die neue Datei und die SUMMARY liegen auf der Platte, der Commit `6c20b11` steht in der
Historie und nennt genau eine Datei, der Haken fuer 19-06 steht in ROADMAP.md, und STATE.md ist
von Hand nachgezogen (Position, Status, naechster Schritt, Sitzungsfortschreibung, ein neuer
Eintrag unter den Entscheidungen). Das Arbeitsverzeichnis traegt ausser den Planungsdateien
nichts Offenes.
