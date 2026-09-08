---
phase: 08-deutsche-komposita-ohne-behelf
plan: 05
subsystem: docs
tags: [dokumentation, qual-03, komposita, known-limits, roadmap, requirements]

# Dependency graph
requires:
  - phase: 06.1-nachmessung
    provides: den Endungsvergleich in docs/measurements/2026-09-nachmessung-m7g/, Abschnitt 7
  - phase: 08-deutsche-komposita-ohne-behelf
    plan: 01
    provides: die Messung docs/measurements/2026-09-komposita-rezept-a/ und den Owner-Entscheid a
  - phase: 08-deutsche-komposita-ohne-behelf
    plan: 04
    provides: COMPOUNDS mit 21 gemessenen Zeilen und die zehn deutschen CI-Sprachfaelle
provides:
  - Abschnitt 7 des Nachmessberichts mit den zwei Entscheidungssaetzen, die QUAL-03 formal schliessen
  - docs/german-analyzer.md mit den sieben nicht zerlegbaren Alltagskomposita namentlich
  - Zwei neue benannte Grenzen: ausgeschriebene Umlaute auf der Indexseite, Nicht-Monotonie der Liste
  - Ein neuer Abschnitt ueber den Rangfolge-Preis der Zerlegung
  - Erfolgskriterium 1 der Phase 8 und QUAL-02 in der vom Owner entschiedenen Fassung
affects: [phase-08-verifikation, phase-10-messung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Befund im Messbericht ist entweder an einen rotwerdenden Test gebunden oder ausdruecklich als offen erklaert, ein dritter Zustand ist keiner"
    - "Jeder in der Doku zitierte Testname wird vor dem Schreiben mit grep -n bestaetigt"
    - "Eine Grenze der Doku nennt ihre Messung, nie eine geschaetzte Zahl"

key-files:
  created: []
  modified:
    - docs/measurements/2026-09-nachmessung-m7g/README.md
    - docs/german-analyzer.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Die 20 uebersprungenen CSV sind als Testfall eingezogen: zwei Tests halten die zwei Stellen, an denen der Befund entsteht"
  - "no_text_layer ist im Verhalten eingezogen, die Messregel bleibt bewusst offen: kein Schloss vor der Verdikttabelle, stattdessen die Regel, Verdikte nur bei leerem Arbeitsvorrat zu lesen"
  - "Die Kompositatabelle der Doku traegt ab jetzt echte Umlaute, weil die ASCII-Transkription gemessen eine andere Tokenliste ergibt"
  - "MESS-02 wird mitgezogen, obwohl der Plan nur die Roadmap-Zeile nennt: dieselbe Zahl darf nicht an zwei Stellen verschieden stehen"
  - "Die Kaestchen in REQUIREMENTS.md bleiben ungehakt, das ist Sache des Orchestrators nach der Phasenverifikation"

patterns-established:
  - "Verworfene Kandidaten und nicht baubare Zusagen stehen in der Roadmap mit dem Verweis auf ihre Messung, nicht als stille Streichung"

requirements-completed: [QUAL-01, QUAL-03]

# Metrics
duration: 25min
completed: 2026-09-08
---

# Phase 8 Plan 05: QUAL-03 schliessen und die Grenzen in die Doku ziehen Summary

**QUAL-03 ist formal geschlossen, weil die zwei offenen Befunde des Endungsvergleichs jetzt jeder eine Entscheidung tragen: die 20 uebersprungenen CSV haengen an zwei rotwerdenden Tests, und der `no_text_layer`-Nebenbefund haengt im Verhalten an zwei weiteren, waehrend seine Messregel ausdruecklich offen bleibt; dazu nennt `docs/german-analyzer.md` die sieben nicht zerlegbaren Alltagskomposita namentlich, beschreibt erstmals den ASCII-Fall, die Nicht-Monotonie der Liste und den Rangfolge-Preis der Zerlegung, und Roadmap wie Requirements sagen jetzt denselben Satz wie die Messung.**

## Performance

- **Duration:** rund 25 min
- **Tasks:** 3 von 3
- **Files modified:** 4, created: 0 (ausser diesem Summary)
- **Tests:** 1744 passed, 15 skipped (unveraendert gegenueber 08-04, dieser Plan aendert keinen Code)

## Accomplishments

- **Erfolgskriterium 5 der Phase ist formal geschlossen, ohne eine einzige wiederholte Messung.** Der Endungsvergleich war gefahren und bestanden; was fehlte, waren zwei Saetze, die sagen, was mit den zwei Befunden geschieht. Beide stehen jetzt in Abschnitt 7, beide in der Form "Entscheidung: ...", und beide nennen die Tests, die sie tragen.
- **Kein zitierter Testname stammt aus dem Gedaechtnis.** Alle sechs in der Doku genannten Testfunktionen sind vor dem Schreiben mit `grep -n` gegen die genannte Datei bestaetigt, Zeilennummern unten. Das ist die Minderung zu T-08-16: ein Beleg, den es nicht gibt, waere schlimmer als ein offener Punkt, weil die Phasenverifikation ihn als Beleg nimmt.
- **Die Doku sagt nicht mehr "14 von 16", ohne zu sagen, welche sechzehn.** Die Spaltenueberschrift der Rezepttabelle nennt die sechzehn langen Komposita ausdruecklich, und darunter steht die breitere Messung: von 21 alltaeglichen Verwaltungskomposita zerfallen sieben nicht, und es sind die kurzen, haeufigen.
- **Die sieben stehen namentlich in "Known limits", mit Zeichenzahl, Token und Grund.** Sechs davon, weil sie selbst Eintrag der Liste sind, und `Baukosten`, weil `bau` mit drei Zeichen unter `MIN_LEN` liegt. Genau dieser siebte ist der, den man uebersieht, wenn man nur die Spalte `entry_in_list` liest.
- **Drei Dinge stehen erstmals ueberhaupt in der Doku:** die ASCII-Transkription, die keine Zerlegung bekommt und damit mehr kostet als D3 (D3 kostet einen Term, dieser Fall die ganze Zerlegung); die Nicht-Monotonie, also dass zusaetzliche Listeneintraege eine gelingende Zerlegung in eine Sackgasse fuehren koennen, samt der Regel, dass eine Listenaenderung eine Datenmigration ist; und der Rangfolge-Preis, naemlich dass der Originaltoken bei erfolgreicher Zerlegung verschwindet und die Suche nach dem ganzen Wort eine Konjunktion ueber die Teile ist.
- **Die Planungsartefakte tragen den Owner-Entscheid statt einer ueberholten Zusage.** Erfolgskriterium 1 nennt drei Faelle, die im CI-Set wirklich stehen, und fuehrt den alten Fall als benannte Grenze mit Verweis auf die Messung. Kein Erfolgskriterium der Phase 8 behauptet mehr einen Fall, den `backend/tests/test_analyzer.py` als nicht zerlegbar ausweist.

## Task Commits

1. **Task 1: Die zwei Entscheidungssaetze fuer QUAL-03** - `1d56106` (docs)
2. **Task 2: Die Grenzen der Zerlegung in der Analyzer-Doku nachziehen** - `5934bf2` (docs)
3. **Task 3: Roadmap und Requirements auf den entschiedenen Stand bringen** - `4ccbd39` (docs)

## Der Buchstabe des Owner-Entscheids

Zitiert aus `08-01-SUMMARY.md`, Abschnitt "Der Owner-Entscheid (Task 3)", die
Antwort des Owners woertlich:

> a) Umformulieren + Execute (Recommended)

**Buchstabe a.** Also: Erfolgskriterium 1 wird auf die messbar zerlegbaren
Faelle umformuliert, keine Rezeptaenderung, kein Reindex. Genau das und nichts
darueber hinaus ist in Task 3 umgesetzt. Option b (Wortlaut behalten, Grenze
danebenschreiben) und Option c (Phase neu planen) waren nicht gewaehlt und sind
nicht ausgefuehrt.

## Die Belege, mit `grep -n` bestaetigt

Kein Name in der Doku steht ohne diese Zeile dahinter. Die Bestaetigung lief vor
dem Schreiben, nicht danach.

| Zitierter Test | Datei | Zeile |
|---|---|---|
| `test_exactly_twenty_files_lie_above_the_size_cap` | `backend/tests/test_load_corpus.py` | 113 |
| `test_a_file_over_the_size_cap_is_skipped_a_second_time` | `backend/tests/test_extract_errors.py` | 297 |
| `test_no_text_layer_is_requeued_and_not_acknowledged` | `backend/tests/test_poller.py` | 452 |
| `test_a_stored_no_text_layer_verdict_does_not_block_the_handover` | `backend/tests/test_poller.py` | 526 |
| `test_the_transcribed_umlaut_costs_the_split_not_only_the_term` | `backend/tests/test_analyzer.py` | 220 |
| `test_the_stemmer_folds_umlauts_without_a_folding_filter` | `backend/tests/test_analyzer.py` | 194 |
| `test_nominal_inflection_collapses_into_one_term` | `backend/tests/test_analyzer.py` | 190 |
| `no_text_layer` als Uebergabepunkt | `backend/tests/test_reconcile.py` | 289, 300, 361, 399 |
| `conjunction_by_default=True` | `backend/src/findling/query/rewrite.py` | 367 |

**Ein Name des Plans wurde bewusst nicht zitiert.**
`test_the_bomb_of_the_corpus_is_skipped_too_large`
(`backend/tests/test_extract_documents.py:782`) existiert und ist bestaetigt,
steht aber nicht in der Doku: das Akzeptanzkriterium verlangt **zwei** Tests
hinter dem Befund, und die zwei genannten halten die zwei Stellen, an denen er
entsteht (die Verteilung des Generators und das Urteil vor dem ersten gelesenen
Byte). Ein dritter Name haette den Satz laenger und nicht belastbarer gemacht.

**Eine Zeilennummer des Plans stimmt nicht mehr.** Das Interface-Verzeichnis des
Plans nennt `rewrite.py:388` fuer `conjunction_by_default`; gemessen steht die
Zeile bei 367. Die Doku nennt deshalb Datei und Flag, aber keine Zeilennummer:
eine Zeilennummer in Prosa ist beim naechsten Einschub falsch.

## Die zwei Entscheidungen im Wortlaut ihrer Wirkung

**Erstens, die 20 uebersprungenen CSV: eingezogen.** Der Befund entsteht an zwei
Stellen, und beide sind besetzt. `test_exactly_twenty_files_lie_above_the_size_cap`
haelt, dass die Kategorie `oversize` die einzige des Generators ist, deren
Zieldateigroesse ueber `MAX_FILE_BYTES` liegt, und dass sie in einem
50.000-Dateien-Korpus genau 20 Dateien erzeugt. Wer die Verteilung anfasst, macht
diese Zeile rot statt stillschweigend eine andere Zahl in einen spaeteren Bericht
zu schreiben. `test_a_file_over_the_size_cap_is_skipped_a_second_time` haelt, dass
eine Datei ueber dem Deckel `skipped(too_large)` bekommt, bevor ein Byte gelesen
wird.

**Zweitens, `no_text_layer`: Verhalten eingezogen, Messregel bewusst offen.**
Eingezogen ist, was Code halten kann: die Zeile wird wieder vorgelegt und dabei
**nicht** quittiert (Quittieren heisst Loeschen, und geloescht waere genau die
Zeile, auf die der Requeue Arbeit gelegt hat), und ein bereits gespeichertes
Verdikt darf die Uebergabe nach einem Neustart nicht blockieren. Offen bleibt
die Messregel: es gibt keinen Mechanismus, der ein Leseskript daran hindert, die
Verdikttabelle bei vollem Arbeitsvorrat zu lesen, und es soll auch keinen geben.
Die Tabelle ist waehrend der Arbeit nicht falsch, sie ist ein Zwischenstand, und
ein Schloss davor liesse den laufenden Betrieb fuer einen Fehler bezahlen, den
nur ein Messender machen kann. An die Stelle des Mechanismus tritt die Regel:
**Verdikte nur bei leerem Arbeitsvorrat lesen.**

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Fehler] Die Kompositatabelle der Doku stand mit ausgeschriebenen Umlauten da, und das ist seit 08-01 nachweislich falsch**

- **Found during:** Task 2
- **Issue:** Die Tabelle unter "The sixteen test compounds" schrieb die
  Testwoerter als `Grundstuecksverkehrsgenehmigung`, `Kuendigungsfrist`,
  `Bundesausbildungsfoerderungsgesetz` und
  `Rindfleischetikettierungsueberwachungsaufgabenuebertragungsgesetz`, also in
  ASCII-Transkription, und behauptete daneben die Token der Umlautfassung. Die
  Messung aus 08-01 (Abschnitt 3.2) und
  `test_the_transcribed_umlaut_costs_the_split_not_only_the_term` zeigen, dass
  die ASCII-Fassung von `Grundstuecksverkehrsgenehmigung` **einen einzigen**
  Token `grundstuecksverkehrsgenehm` ergibt. Die Tabelle sagte damit fuer die
  ASCII-Schreibweise etwas, das gemessen nicht stimmt, und das ausgerechnet in
  dem Abschnitt, der die Zerlegung belegen soll.
- **Fix:** Die 21 Zeilen tragen jetzt die echten Umlaute, genau wie `COMPOUNDS`
  in `backend/tests/test_analyzer.py` und wie
  `rohdaten/tokens-rezept-a.tsv`. Ein Satz unter der Tabelle sagt ausdruecklich,
  warum die Schreibweise hier Teil der Aussage ist, und verweist auf die neue
  Grenze in "Known limits". Die Projektregel ist eingehalten: echte Umlaute
  stehen in deutscher Prosa und in genau diesen gemessenen Wortformen, nicht in
  Bezeichnern.
- **Files modified:** `docs/german-analyzer.md`
- **Verification:** Tabellenzeilen gegen `tokens-rezept-a.tsv` und gegen
  `COMPOUNDS` verglichen, Wort fuer Wort; `grep -c 'sixteen test compounds'`
  ergibt 0.
- **Committed in:** `5934bf2`

**2. [Rule 2 - Fehlende kritische Funktionalitaet] Dieselbe Zahl stand an zwei Stellen und der Plan nannte nur eine**

- **Found during:** Task 3
- **Issue:** Der Plan verlangt die Zahlensynchronisation fuer Phase 10,
  Erfolgskriterium 2 in `.planning/ROADMAP.md`. Dieselbe Zusage steht ein
  zweites Mal als MESS-02 in `.planning/REQUIREMENTS.md` ("die 7 deutschen
  CI-Sprachfaelle"). Waere nur die Roadmap gezogen worden, haetten Roadmap und
  Requirements ab sofort verschiedene Zahlen fuer dasselbe Kriterium genannt,
  und die Verifikation der Phase 10 haette sich aussuchen koennen, welche gilt.
  Das ist genau der Widerspruch, den das dritte Erfolgskriterium dieses Plans
  ausschliessen soll.
- **Fix:** MESS-02 steht jetzt auf 10, wie Phase 10, Erfolgskriterium 2 und wie
  `.github/workflows/integration.yml`.
- **Files modified:** `.planning/REQUIREMENTS.md`
- **Verification:** `grep -rn "CI-Sprachfaelle"` ueber `ROADMAP.md` und
  `REQUIREMENTS.md` nennt zweimal zehn und einmal die Planzeile von 08-04;
  `grep -n "German language cases" .github/workflows/integration.yml` nennt
  zweimal `ten`.
- **Committed in:** `4ccbd39`

---

**Total deviations:** 2 auto-fixed (1x Rule 1, 1x Rule 2)
**Impact on plan:** Beide sind Korrektheitsfragen im Rahmen des Plans. Es wurde
kein Produktionscode angefasst, kein Test geaendert, keine Messung wiederholt,
und `STATE.md` ist unberuehrt.

## Issues Encountered

**Keine.** Der Plan war ein reiner Dokumentationsplan, und alle vier Dateien
lagen so vor, wie die Vorwellen sie beschrieben haben. Der offene Punkt aus
08-04 ("`docs/german-analyzer.md` spricht weiterhin von den sechzehn
Testkomposita und von 14 von 16") ist mit Task 2 erledigt.

## Verification

- `cd backend && uv run pytest -q`: **1744 passed, 15 skipped** in 3 min 16 s,
  Zahl gleich der Basis nach 08-04, wie es bei einem Plan ohne Codeaenderung
  sein muss
- `grep -c '^Entscheidung:' docs/measurements/2026-09-nachmessung-m7g/README.md`: 2
- `grep -q "test_exactly_twenty_files_lie_above_the_size_cap"` und
  `grep -q "no_text_layer"` in demselben Bericht: beide treffen
- `grep -c '2026-09-komposita-rezept-a' docs/german-analyzer.md`: 6
- `grep -c 'conjunction' docs/german-analyzer.md`: 2
- `grep -c 'sixteen test compounds' docs/german-analyzer.md`: 0
- Em-Dashes: 0 in allen vier geaenderten Dateien, geprueft mit dem
  `grep -c`-Ausdruck aus den Akzeptanzkriterien des Plans (U+2014 und U+2013)
- Echte Umlaute: 0 in `.planning/ROADMAP.md` und `.planning/REQUIREMENTS.md`,
  wie im Bestand dieser beiden Dateien
- Quervergleich: `ROADMAP.md`, `REQUIREMENTS.md`, `docs/german-analyzer.md` und
  `.github/workflows/integration.yml` nennen dieselbe Zahl (zehn) und dieselben
  drei Beispiele (Vereinbarung, Auszug, Erinnerung)
- Keine Zerlegungszusage der Roadmap widerspricht `COMPOUNDS`: die drei
  genannten Komposita stehen dort mit mehr als einem Token,
  `Baugenehmigung` mit genau einem und wird nur noch als Grenze genannt

## Known Stubs

Keine. Jede neue Aussage der Doku steht auf einer gemessenen Zeile oder auf
einem benannten Test.

## Threat Flags

Keine neue sicherheitsrelevante Flaeche. Die Dispositionen des Plans sind
erfuellt: T-08-16 ueber die Belegtabelle oben (jeder Name vor dem Schreiben
bestaetigt, ein nicht bestaetigter Name wurde nicht geschrieben), T-08-17 ueber
den Verweis auf `docs/measurements/2026-09-komposita-rezept-a/` an jeder neuen
Grenze und den Verzicht auf jede geschaetzte Zahl, T-08-18 bleibt `accept`: die
Aenderungen nennen ausschliesslich Testwoerter und Zahlen, keinen Nutzerinhalt.

## User Setup Required

Keine.

## Next Phase Readiness

- Alle fuenf Erfolgskriterien der Phase 8 haben ab jetzt einen Satz statt einer
  Vermutung: 1 in der entschiedenen Fassung mit drei belegten Faellen, 2 durch
  den Wegbeweis aus 08-02, 3 durch 08-03, 4 durch den Digest neben
  `schema_version`, 5 durch Abschnitt 7 des Nachmessberichts.
- Phase 10 misst gegen zehn deutsche CI-Sprachfaelle, und beide Artefakte, die
  diese Zahl nennen, sagen jetzt dieselbe.
- **Bewusst nicht erledigt:** Die Kaestchen von QUAL-01 bis QUAL-03 in
  `.planning/REQUIREMENTS.md` und die Coverage-Tabelle sind nicht angehakt, und
  der Fortschrittsteil der Roadmap samt der Plan-Liste der Phase 8 ist nicht
  angefasst. Beides pflegt der Orchestrator nach der Phasenverifikation, so wie
  in 08-01 bis 08-04 auch. `STATE.md` ist unberuehrt.

## Self-Check: PASSED

- Alle vier geaenderten Dateien liegen auf der Platte und tragen die
  beschriebenen Aenderungen.
- Alle drei Task-Commits sind in `git log`: `1d56106`, `5934bf2`, `4ccbd39`.
- `git status --short` ausser diesem Summary sauber; `git diff` gegen den
  Wellenstand zeigt keine geloeschte Datei.
- `STATE.md` nicht angefasst.
- Alle Commits als `street1983nk <k.cherif@outlook.de>`, keine Claude-Trailer.

---
*Phase: 08-deutsche-komposita-ohne-behelf*
*Completed: 2026-09-08*
