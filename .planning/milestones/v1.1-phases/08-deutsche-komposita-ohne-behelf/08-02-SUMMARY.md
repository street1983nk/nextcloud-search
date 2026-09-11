---
phase: 08-deutsche-komposita-ohne-behelf
plan: 02
subsystem: testing
tags: [tantivy, split_compound, ast, regressionswaechter, qual-02]

# Dependency graph
requires:
  - phase: 02-index-und-suche
    provides: german_analyzer, cached_german_analyzer, open_index, die registrierte deutsche Kette
  - phase: 08-deutsche-komposita-ohne-behelf
    plan: 01
    provides: die gemessenen Token je Fall in docs/measurements/2026-09-komposita-rezept-a/, der Owner-Entscheid a
provides:
  - Negativkontrolle: dieselbe Kette ohne Filter.split_compound findet den Konstituenten nicht
  - Praefix-Gegenprobe, die bei einem Prefix-, Wildcard- oder Fuzzy-Behelf rot wird
  - Termgleichheit von Index- und Frageseite, mit dem Build-Zaehler als Identitaetsbeweis
  - filter_chain, ein Waechter ueber die Filterreihenfolge im Syntaxbaum von index/analyzer.py
  - Waechter, der tools/index_status.py als einzigen Oeffner ohne Wortliste und als Nicht-Frager festnagelt
affects: [08-03, 08-04, 08-05, query-rewrite, index-analyzer]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Den Weg beweisen statt das Ergebnis: eine Negativkontrolle ohne den Filter neben dem Trefferzaehler"
    - "Strukturwaechter ueber ast.parse, nach dem Vorbild von normalize_callers, mit synthetischen Rotbeweisen daneben"
    - "Eine Ausnahme im Produktionscode wird von aussen gehalten, nicht nur im Kommentar begruendet"

key-files:
  created: []
  modified:
    - backend/tests/test_index_open.py
    - backend/tests/test_analyzer.py
    - backend/src/findling/tools/index_status.py

key-decisions:
  - "Der Termgleichheitstest nimmt wordlist_hash(CONSTITUENTS) statt der Platzhalter-Konstante DIGEST, sonst waere seine eigene Behauptung ueber die Objektidentitaet falsch"
  - "Die splitterlose Kette wird VOR dem Schreiben registriert, damit Schreib- und Frageseite dieselbe Kette benutzen"
  - "Der Waechter ueber index_status.py prueft beide Haelften in einem Test: keine Frage dort, und kein zweiter Oeffner ohne Liste"

patterns-established:
  - "Ein Trefferzaehler allein gilt in diesem Projekt nicht mehr als Beweis fuer die Zerlegung"
  - "Jeder neue Strukturwaechter bringt seine Rotbeweise gegen synthetische Quelltexte mit"
  - "Rotbeweise werden von Hand gefahren und mit ihrer Fehlermeldung im Summary festgehalten"

requirements-completed: [QUAL-02]

# Metrics
duration: 45min
completed: 2026-09-08
---

# Phase 8 Plan 02: Der Wegbeweis fuer die Zerlegung Summary

**Vier neue Waechter nageln fest, dass die deutsche Zerlegung ueber `Filter.split_compound` in der registrierten Kette laeuft und nicht ueber einen Behelf: eine Negativkontrolle ohne den Splitter, eine Praefix-Gegenprobe, die Termgleichheit beider Suchseiten und ein Strukturwaechter ueber die Filterreihenfolge im Syntaxbaum, dazu der eine Aufrufer mit leerer Wortliste, der nachweislich keine Frage stellen kann.**

## Performance

- **Duration:** rund 45 min
- **Tasks:** 3 von 3
- **Files modified:** 3 (zwei Testdateien, ein Kommentar im Produktionscode)
- **Tests:** 1722 passed, 15 skipped (vorher 1713 passed), Laufzeit 3 min 14 s
- **Rotbeweise von Hand gefahren:** 3, alle drei mit dem erwarteten Ergebnis

## Accomplishments

- **Erfolgskriterium 2 der Phase ist belegt, und zwar ueber den Weg.** Der bestehende Test `test_the_registered_german_chain_splits_compounds` zaehlt einen Treffer und bliebe gruen, wenn die Zerlegung morgen durch eine Prefix-Query ersetzt wuerde. Die drei neuen Tests daneben machen Aussagen, die nur die Zerlegung erfuellt: ohne `Filter.split_compound` findet `frist` nichts, ein echtes Praefix des Kompositums findet nichts, und beide Suchseiten erzeugen genau `["kundig", "frist"]` und keine weiteren Terme.
- **Eine Umstellung der Filterreihenfolge wird jetzt rot, nicht nur ihr Entfernen.** `filter_chain` liest die Kette aus dem Syntaxbaum von `index/analyzer.py` und haelt sie gegen `["lowercase", "split_compound", "custom_stopword", "stopword", "remove_long", "stemmer"]`. Gemessen im Rotbeweis: mit vorgezogenem `remove_long` meldet der Waechter `At index 1 diff: 'remove_long' != 'split_compound'`, waehrend die Tokentabelle danebenliegend nur meldet, dass das 63-Zeichen-Wort "ploetzlich leer" ist und den Leser die Ursache selbst suchen laesst.
- **Die eine Ausnahme im Produktionscode wird von aussen gehalten.** `tools/index_status.py` oeffnet den Index mit leerer Konstituentenliste, weil es zaehlt und der Automat 0,44 s und rund 23 MB pro Wartelauf kosten wuerde. Der neue Waechter belegt beide Haelften der Zusage: dort steht kein `parse_query`, `parse_query_lenient`, `build_query` oder `search`, und keine zweite Datei des Pakets nimmt dieselbe Abkuerzung.
- **Kein Produktionsverhalten geaendert.** `index/analyzer.py`, `index/open.py` und `query/rewrite.py` sind gegen die Wellen-1-Basis byteweise unveraendert. Die einzige Aenderung ausserhalb der Tests sind sieben Kommentarzeilen in `tools/index_status.py`. `SCHEMA_VERSION`, `ANALYZER_VERSION` und `wordlist_hash` bleiben, wo der Owner-Entscheid a sie stehen laesst: kein Reindex.

## Task Commits

1. **Task 1: Der Wegbeweis, drei Bausteine in test_index_open.py** - `dc60a59` (test)
2. **Task 2: Der Strukturwaechter ueber die Filterreihenfolge** - `ee52ce9` (test)
3. **Task 3: Der eine Aufrufer mit leerer Liste, festgenagelt** - `39b14ab` (test)

## Die drei Rotbeweise, von Hand gefahren

Jeder Waechter ist nur so viel wert wie der Nachweis, dass er faellt. Alle drei Eingriffe wurden nach dem Lauf zurueckgenommen; der Arbeitsbaum steht danach wieder sauber.

**1. `Filter.split_compound` aus `german_analyzer` entfernt.**
Ergebnis: 9 von 33 Tests in `test_index_open.py` rot, darunter die beiden im Plan
benannten. `test_without_the_splitter_the_constituent_finds_nothing` faellt in
seiner zweiten Haelfte (die ausgelieferte Kette liefert dann ebenfalls 0 statt 1),
`test_the_question_side_produces_the_same_terms_as_the_index_side` faellt bei
`analyze("Kündigungsfrist")`. Mit gefallen ist auch die Praefix-Gegenprobe, weil
ihre zweite Zusicherung der Konstituententreffer ist. Danach zurueckgenommen, 33
passed.

**2. `remove_long` vor den Splitter gezogen.**
Ergebnis: 3 von 59 Tests in `test_analyzer.py` rot. Der neue Waechter meldet

```
AssertionError: assert ['lowercase',...d', 'stemmer'] == ['lowercase',...g', 'stemmer']
  At index 1 diff: 'remove_long' != 'split_compound'
```

Die beiden anderen Ausfaelle sind die vorhandenen Tests zum 63-Zeichen-Kompositum,
also genau der gemessene Schaden, den die Reihenfolge anrichtet. Der Unterschied
ist der Punkt dieses Plans: die Tokentabelle zeigt den Schaden, der Waechter nennt
die Ursache. Danach zurueckgenommen, 59 passed.

**3. `index.parse_query("x", ["body_de"])` in `tools/index_status.py` eingefuegt.**
Ergebnis: `test_the_only_index_opened_without_a_word_list_is_never_asked_a_question`
faellt mit

```
AssertionError: tools/index_status.py counts and must never ask:
  tools/index_status.py:119
```

Die Meldung nennt Datei und Zeile, wie der Waechter daneben es tut. Danach
zurueckgenommen, `grep -c parse_query` ergibt wieder 0.

## Was die vier Waechter jeweils abfangen

| Waechter | Wird rot bei | Datei |
|---|---|---|
| `test_without_the_splitter_the_constituent_finds_nothing` | Splitter aus der Kette entfernt | test_index_open.py |
| `test_a_mere_prefix_of_the_compound_does_not_hit` | Prefix-, Wildcard- oder Fuzzy-Umschreibung in query/rewrite.py | test_index_open.py |
| `test_the_question_side_produces_the_same_terms_as_the_index_side` | Frage- und Indexseite laufen auf verschiedenen Analyzern oder Termen | test_index_open.py |
| `test_the_german_chain_stands_in_the_measured_order` | Filterreihenfolge umgestellt, auch ohne Verhaltensbruch im Testsatz | test_analyzer.py |
| `test_the_only_index_opened_without_a_word_list_is_never_asked_a_question` | eine Frage in index_status.py oder ein zweiter Oeffner ohne Wortliste | test_index_open.py |

## Decisions Made

1. **`wordlist_hash(CONSTITUENTS)` statt der Platzhalter-Konstante `DIGEST` im
   Termgleichheitstest.** Der Plan nennt im `<behavior>`-Block
   `cached_german_analyzer(DIGEST, CONSTITUENTS)`. `DIGEST` ist in dieser Datei
   `"0" * 64`, also gerade nicht der Schluessel, unter dem `open_index` den
   Analyzer ablegt. Mit `DIGEST` waere der Test zwar gruen, aber seine eigene
   Begruendung falsch: er wuerde einen zweiten Automaten bauen und ueber ihn
   reden, waehrend der Index mit einem anderen antwortet. Der Cache haelt genau
   einen Eintrag, der fremde Schluessel haette den echten verdraengt und den
   naechsten `open_index`-Aufruf 0,44 s und 23 MB kosten lassen. Mit dem echten
   Digest ist es dasselbe Objekt, und der Build-Zaehler beweist das im Test:
   `build_count()` steht danach unveraendert.
2. **Die splitterlose Kette wird vor dem Schreiben registriert.** Ein
   `register_tokenizer` nach dem Schreiben wuerde nur eine anders tokenisierte
   Frage an einen richtig geschriebenen Index stellen. Das waere ein Test ueber
   die Frageseite allein; die Negativkontrolle soll aber sagen, was der Splitter
   auf beiden Seiten leistet.
3. **`MAX_TOKEN_CHARS` und `FUGEN` werden importiert, nicht abgeschrieben.** Eine
   Kontrollkette mit eigenen Zahlen ist nach der ersten Aenderung der echten
   Kette keine Kontrolle mehr, sondern ein zweites Rezept.
4. **Der Waechter unterscheidet Ketten.** `filter_chain` wird zusaetzlich gegen
   `name_analyzer` gehalten (`["lowercase", "ascii_fold", "remove_long"]`), damit
   ein Waechter, der immer dieselbe Liste zurueckgibt, nicht als gruen durchgeht.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Der Termgleichheitstest haette ueber den falschen Analyzer geredet**

- **Found during:** Task 1
- **Issue:** Der `<behavior>`-Block des Plans schreibt
  `cached_german_analyzer(DIGEST, CONSTITUENTS)`. `DIGEST` ist die
  Platzhalter-Konstante `"0" * 64` fuer die Versionsmarken, nicht der Schluessel
  des Analyzers. Der Aufruf haette den Prozess-Singleton verdraengt, einen
  zweiten Automaten gebaut und die im Plan verlangte Begruendung ("beide Seiten
  benutzen dieselbe Objektidentitaet") in ihr Gegenteil verkehrt.
- **Fix:** Der Test ruft `cached_german_analyzer(wordlist_hash(CONSTITUENTS),
  CONSTITUENTS)`, also exakt den Aufruf aus `index/open.py:98`, und beweist die
  Identitaet ueber `build_count()` vorher und nachher.
- **Files modified:** `backend/tests/test_index_open.py`
- **Verification:** Test gruen; im Rotbeweis 1 faellt er wie gefordert.
- **Commit:** `dc60a59`

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** Keine Scope-Aenderung. Alle Akzeptanzkriterien der drei Tasks
sind erfuellt; der Test ist durch die Korrektur strenger, nicht schwaecher.

## Verification

- `cd backend && uv run pytest -q` : **1722 passed, 15 skipped** in 194 s
- `uv run ruff check .` : All checks passed
- `uv run ruff format --check .` : 116 files already formatted
- `uv run pyright` : 0 errors, 0 warnings, 0 informations
- `uv run vulture src tests --min-confidence 80` : keine Ausgabe

Akzeptanzkriterien einzeln nachgezaehlt:

| Kriterium | Ergebnis |
|---|---|
| drei Testnamen mit `splitter`, `prefix`, `terms` | vorhanden |
| `grep -c register_tokenizer backend/tests/test_index_open.py` | 2 (>= 1) |
| `grep -c parse_query backend/src/findling/tools/index_status.py` | 0 |
| `grep -c split_compound backend/tests/test_index_open.py` | 2 |
| `grep -c ast.parse backend/tests/test_analyzer.py` | 2 |
| `filter_chain` plus Tests, die sie benutzen | 5 |
| Vergleich gegen die echte Datei mit `==` und vollstaendiger Liste | ja |
| Praefixtest mit `== 0` auf ein echtes Praefix (`kündigungsf`) | ja, gemessen ein Token `kundigungsf` |
| neuer Test nennt `tools/index_status.py` woertlich | ja, als Konstante `COUNTING_MODULE` |

Produktionscode unveraendert, gegen die Wellen-1-Basis `45d5f0b` geprueft:

```
backend/src/findling/tools/index_status.py |   7 ++   (nur Kommentar)
backend/tests/test_analyzer.py             | 152 ++++
backend/tests/test_index_open.py           | 168 ++++
```

`index/analyzer.py`, `index/open.py` und `query/rewrite.py` stehen nicht im Diff.

## Threat Model

Drei der vier Eintraege des Plans sind mit diesen Tests abgedeckt:

- **T-08-04 (DoS, Filterreihenfolge):** `test_the_german_chain_stands_in_the_measured_order` haelt `remove_long` hinter dem Splitter. Rotbeweis 2 gefahren.
- **T-08-05 (Tampering, query/rewrite.py):** `test_a_mere_prefix_of_the_compound_does_not_hit` wird rot, sobald eine Prefix-, Wildcard- oder Fuzzy-Umschreibung in den Suchweg gelangt. `allow_regexes=False` in `build_query` ist unangetastet und im Testkommentar als zweite Haelfte derselben Zusage benannt.
- **T-08-06 (Information Disclosure, tools/index_status.py):** `test_the_only_index_opened_without_a_word_list_is_never_asked_a_question` haelt fest, dass das Werkzeug zaehlt und nie fragt. Rotbeweis 3 gefahren.
- **T-08-07 (accept):** unveraendert. Die Sicherheitsgrenze bleibt der finale PHP-Recheck; `test_parity_diff.py` und `test_guest_parity.py` wurden nicht angefasst und laufen im Gesamtlauf gruen mit.

Keine neue Angriffsflaeche: diese Aenderung besteht aus Tests und sieben Kommentarzeilen.

## Known Stubs

Keine. Alle fuenf neuen Tests behaupten gemessene Werte und wurden einzeln zum Fallen gebracht.

## Issues Encountered

**Der Worktree hatte kein `.venv`.** Ein `uv sync` im Worktree-`backend` war noetig, bevor irgendein Gate laufen konnte. Kein Befund, nur eine Minute Anlauf.

## Next Phase Readiness

08-03 bis 08-05 koennen unveraendert weiterlaufen. Sie haben ab jetzt zusaetzlich:

- einen Waechter, der eine Umstellung der Filterkette benennt statt sie nur spuerbar zu machen; wer in Phase 10 an der Kette misst, sieht sofort, welche Position sich bewegt hat,
- die Zusicherung, dass `tools/index_status.py` ein Zaehler bleibt, was den Waechter fuer jede kuenftige Ausnahme "Index ohne Wortliste oeffnen" mitliefert,
- `filter_chain` als wiederverwendbaren Baustein fuer jeden weiteren Strukturwaechter ueber eine Analyzer-Kette.

**Nicht erledigt und bewusst nicht angefasst:** `STATE.md` und `ROADMAP.md` schreibt der Orchestrator nach der Welle. Die Umformulierung der Roadmap-Zeile fuer Erfolgskriterium 1 aus dem Owner-Entscheid a ist damit weiterhin offen.

## Self-Check: PASSED

- Alle drei geaenderten Dateien liegen auf der Platte und stehen im Diff gegen `45d5f0b`.
- Alle drei Task-Commits sind in `git log`: `dc60a59`, `ee52ce9`, `39b14ab`.
- Kein Commit enthaelt eine Loeschung (`git diff --diff-filter=D` leer).
- `STATE.md` und `ROADMAP.md` unberuehrt.
- Alle Commits als `street1983nk <k.cherif@outlook.de>`, keine Claude-Trailer.

---
*Phase: 08-deutsche-komposita-ohne-behelf*
*Completed: 2026-09-08*
