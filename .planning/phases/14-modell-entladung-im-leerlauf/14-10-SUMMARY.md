---
phase: 14-modell-entladung-im-leerlauf
plan: 10
subsystem: ci-gate
tags: [one-load, gate, counters, mutation-testing, resilience-workflow, tdd]

# Dependency graph
requires:
  - phase: 14-modell-entladung-im-leerlauf
    provides: release() und der monotone unload_count() aus 14-05
  - phase: 14-modell-entladung-im-leerlauf
    provides: release_if_idle(), warm() und das Single-Flight des Halters aus 14-06
  - phase: 14-modell-entladung-im-leerlauf
    provides: query_may_load() und die Degradationsnaht aus 14-08, die der Werkslauf mit ausgeschaltetem Schalter durchlaeuft
  - phase: 06.1-speicher-und-doppelte-last
    provides: der Halter in embed/engine.py und die Zaehler load_count()/read_count(), auf denen dieses Gate steht
provides:
  - Die neu formulierte Zusage, an drei Stellen gleichlautend, Modulkopf, findings() und resilience.yml
  - Die vierte Phase des Werkzeugs, entladen und nachladen durch den echten Aufrufweg
  - Zwei Felder mehr im Report, engine_unloads_after_release und engine_loads_after_rewarm
  - Zwei Zweige mehr in findings(), einer davon die Anti-Leerlauf-Klausel der vierten Phase
  - Fuenf Mutationsfaelle statt drei
affects: [14-11, 14-12, 15-boxmessung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Zusage, die sich geaendert hat, wird an allen Stellen gleichzeitig umgeschrieben; ein Gate, dessen Text die alte Zusage nennt, ist im Fehlerpfad ein Irrefuehrer"
    - "Eine Phase eines Messwerkzeugs bekommt ihre eigene Anti-Leerlauf-Bedingung: unloads == 0 ist ein Befund und kein stilles Gruen"
    - "Eine Mutation, die ein Verhalten erst ab einer bestimmten Phase aushebeln soll, haengt an einem Zaehlerstand und nicht an der Uhr"
    - "Ein Messwerkzeug greift bewusst unter die Politik, wenn es die Mechanik einer Zusage misst und nicht die Frist, die ein Admin einstellt"

key-files:
  created: []
  modified:
    - backend/src/findling/tools/one_load.py
    - backend/tests/test_one_load.py
    - backend/tests/test_measurement_scripts.py
    - .github/workflows/resilience.yml

key-decisions:
  - "Freigegeben wird ueber shared_model().release() und nicht ueber release_if_idle(): jene Funktion traegt die Frist aus embed_idle_release_seconds, wo null das Wort fuer aus ist, und ein Messlauf hat eine Admin-Einstellung weder auszusitzen noch umzustellen"
  - "Nachgeladen wird ueber drive_the_search_side() und nicht ueber engine.warm(): das Werkzeug misst seit seiner ersten Fassung durch den echten Aufrufweg, damit ein Aufrufer, der aufhoert ueber den Halter zu gehen, auffaellt statt gemessen zu werden"
  - "Die Mutation des Warmfensters haengt am Entladezaehler und beisst deshalb erst in der vierten Phase; ein von Anfang an gebrochenes Single-Flight haette den zweiten Track mitgerissen und den falschen Befund belegt"
  - "Der Worker-Zweig von findings() bleibt in seiner Form und bekommt nur den Zusatz, dass er das Fenster VOR der Freigabe meint: er ist die 276-MB-Meldung, und drei bestehende Faelle pruefen ihren Wortlaut"
  - "Die echo-Zeilen des Schritts in resilience.yml werden mitgezogen, obwohl das Abnahmekriterium nur Kommentarzeilen vorsah: der Fehlerpfad ist genau der Text, den ein Mensch liest, und die must_haves des Plans verlangen ihn ausdruecklich"

patterns-established:
  - "Ein neues Report-Feld wird zuerst in den drei von Hand gebauten Report()-Faellen rot, bevor es im Werkzeug steht: die Feldliste ist die schmalste Stelle, an der ein vergessenes Feld auffaellt"

requirements-completed: [MEM-05]

# Metrics
duration: 50min
completed: 2026-09-19
---

# Phase 14 Plan 10: Die neue one_load-Zusage und ihr Gate Summary

**Das Gate verspricht nicht mehr "genau ein Laden je Prozess", was mit einer Entladung woertlich falsch waere, sondern "nie zwei Engines gleichzeitig, genau ein Laden je warmem Fenster": das Werkzeug gibt in einer vierten Phase frei, laedt ueber eine zweite echte Suchrunde nach, liest die Zusage als Differenz zweier monotoner Zaehler, und zwei neue Mutationsfaelle belegen, dass es dafuer rot werden kann.**

## Performance

- **Duration:** 50 min
- **Started:** 2026-09-19T20:20:00Z
- **Completed:** 2026-09-19T21:10:00Z
- **Tasks:** 3 von 3
- **Files modified:** 4 (kein neues Modul, keine neue Abhaengigkeit, kein neuer Action-Pin)

## Accomplishments

### Die Zusage, an drei Stellen gleichlautend

Der Modulkopf von `tools/one_load.py` sagt jetzt in einem eigenen Absatz, was
das Gate haelt, und er sagt zuerst, was es nicht mehr haelt: "genau ein Laden je
Prozess" waere seit dem Schalter aus MEM-01 rot fuer die Funktion geworden, die
es beaufsichtigen soll, weil ein Container, der einen Tag laeuft, die Gewichte
viermal gelesen haben darf. Die Zusage ist **nie zwei Engines gleichzeitig,
genau ein Laden je warmem Fenster**, und sie steht in Zaehlern und in keinem
Byte:

- nie zwei Engines: `loads - unloads` ist nie ueber eins und nie unter null,
- ein Laden je warmem Fenster: `loads - unloads` steht nach einem Warmlauf auf
  eins und nach dem naechsten immer noch,
- kein Gruennullen: beide Zaehler sind monoton, `engine.reset()` nullt keinen
  von beiden (T-14-17).

Dieselben drei Saetze stehen im Kommentarblock von `resilience.yml`, und die
`findings`-Meldungen benutzen dieselben Woerter. Der Satz `one embedding engine
per process` kommt im Workflow nicht mehr vor.

### Die vierte Phase: entladen und nachladen

`measure()` haengt hinter `drive_the_second_track()` zwei Schritte an. Der erste
ist `shared_model().release()`, und daneben steht, warum das Werkzeug hier unter
die Politik greift: `release_if_idle()` traegt die Uhr, und ihre Frist kommt aus
`settings().embed_idle_release_seconds`, wo null das Wort fuer aus ist. In der
Werksstellung antwortet sie sofort `False` und wuerde nichts messen, und
eingeschaltet wuerde das Werkzeug eine Admin-Einstellung aussitzen. Gemessen
wird die Mechanik der Zusage, nie die Frist.

Der zweite Schritt ist eine zweite echte Suchrunde ueber `drive_the_search_side()`
und ausdruecklich kein `engine.warm()`: das Werkzeug misst seit seiner ersten
Fassung durch den Weg, den ein Aufrufer wirklich geht.

Beide Zahlen sind Differenzen gegen die Grundlinie, die `measure()` selbst nimmt,
wie die vier davor. `unloads_at_start` ist die dritte Grundlinie im Kopf der
Funktion.

### Die Anti-Leerlauf-Klausel, eine Phase weiter

Der Kopf zaehlt vier statt drei Phasen auf, und die vierte hat einen eigenen
Absatz: eine Freigabe, die nichts freigegeben hat, laesst die Engine genau dort,
wo sie war, die Runde dahinter nimmt einen Cache-Treffer, meldet ein Fenster,
das nichts gekostet hat, und jede Zahl danach sagt nichts. `unloads == 0` ist
deshalb hier ein Befund und nie ein stilles Gruen: dieselbe Falle wie die
Speicherdecke, eine Phase weiter.

In `findings()` steht diese Bedingung VOR der Beurteilung des Fensters, damit
niemand eine Null interpretieren muss.

### Neun Zahlen statt sieben

`Report` traegt `engine_unloads_after_release` und `engine_loads_after_rewarm`
hinter `engine_loads_after_worker`; `cold_search_ms` bleibt das letzte Feld und
bleibt in keinem Zweig von `findings()`. `lines()` druckt
`engine-unloads-after-release=` und `engine-loads-after-rewarm=` in der
bestehenden Schreibweise mit Bindestrichen. Ein sauberer Lauf druckt neun
Zahlenzeilen.

### Fuenf Mutationsfaelle statt drei

- `test_it_goes_red_when_a_release_leaves_two_engines_behind` mutiert
  `EmbeddingModel.release` so, dass es den Zaehler erhoeht und die Engine
  behaelt. Die Runde dahinter nimmt einen Cache-Treffer,
  `engine-loads-after-rewarm=1` gegen `engine-unloads-after-release=1` ergibt ein
  Fenster von null Ladevorgaengen, und das Werkzeug endet mit Exit 1 und der
  Zeile "let go of a counter instead of an engine". In der Wirklichkeit waeren
  das die 276 MB aus Plan 06.1-02 im Entladezyklus: die Admin-Seite meldet
  `unloaded`, die A/B-Messung der Phase 15 zaehlt ein Fenster ohne Kosten, und
  die Gewichte liegen die ganze Zeit im Heap.
- `test_it_goes_red_when_the_warm_up_loads_twice` nimmt
  `EmbeddingModel._load` die Rueckkehr am Kopf, also genau das Stueck, das die
  Zusage strukturell traegt (14-RESEARCH.md 5.3), und zwar nur innerhalb des
  Warmfensters. Ergebnis: `engine-loads-after-rewarm=3` gegen ein Entladen, ein
  Fenster von zwei Ladevorgaengen, Exit 1 und die Zeile "two sessions were built
  for one window". Der Fall prueft zusaetzlich `engine-loads-after-worker=1`,
  also dass die drei Phasen davor unberuehrt bleiben.

Beide pruefen den Rueckgabewert von `main()` und den Wortlaut der
`findings`-Zeile, wie die drei bestehenden. Die Gegenprobe ist
`test_the_fourth_phase_releases_the_weights_and_fetches_them_back`: derselbe
Lauf ohne Mutation endet mit `verdict=ok` und Exit 0.

### Der Erklaertext im Fehlerpfad

Der Kommentarblock ueber dem Schritt `One engine and one constituent list per
process` nennt die Zusage im Wortlaut, die drei Invarianten in Zaehlern, die
276 MB aus Plan 06.1-02 als unveraenderten Anlass, der jetzt auch im
Entladezyklus gilt, die vier Phasen und fuenf statt drei Mutationsfaelle. Die
`echo`-Zeilen im Fehlerzweig nennen die zwei neuen Befunde. Aufruf, sed-Praefix,
Exit-Behandlung und Artefakt des Schritts sind unveraendert, es gibt keinen
neuen `uses:`-Eintrag, keine neue Berechtigung und keinen neuen Pin.

## Task Commits

| Task | Name | Commit | Dateien |
| ---- | ---- | ------ | ------- |
| 1 (RED) | Die Faelle der vierten Phase | `4785d87` | backend/tests/test_one_load.py |
| 1 (GREEN) | Die vierte Phase und die Zusage als Differenz | `b9e8bf3` | backend/src/findling/tools/one_load.py, backend/tests/test_measurement_scripts.py |
| 2 | Zwei Mutationsfaelle, die rot werden | `17fc0d4` | backend/tests/test_one_load.py |
| 3 | Der Erklaertext im Fehlerpfad | `1a9fe4d` | .github/workflows/resilience.yml |

`PACKAGE_TREE_HASH_TODAY` ist im selben Commit wie die Quelltextaenderung
nachgezogen: `083bef5e...` auf `f3f1fb13...`, 54 Dateien unveraendert. Die PHP-
Haelfte ist nicht beruehrt, `PHP_TREE_HASH_TODAY` bleibt stehen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] Der RED-Schritt von Task 1 musste `test_one_load.py` anfassen, das der Plan Task 2 zuweist**

- **Found during:** Task 1
- **Issue:** Task 1 traegt `tdd="true"`, nennt in `<files>` aber nur
  `tools/one_load.py`. Die drei bestehenden Faelle bauen `Report(...)` von Hand
  mit Schluesselwoertern, also macht jedes neue Feld sie sofort rot. Ein
  RED-Schritt ohne Testdatei ist kein RED-Schritt, und ein GREEN-Commit mit drei
  kaputten Bestandsfaellen waere ein roter Commit gewesen.
- **Fix:** Der RED-Commit `4785d87` fasst ausschliesslich `test_one_load.py` an
  (neue Zusicherungen, die drei Handreports um zwei Felder ergaenzt, ein
  Einheitsfall fuer die Anti-Leerlauf-Klausel, ein Lauf ueber den
  Einstiegspunkt), und er ist belegt rot: 6 von 12 Faellen scheitern. Der
  GREEN-Commit `b9e8bf3` traegt dann die Quelle.
- **Verification:** `uv run pytest tests/test_one_load.py -q` vor `b9e8bf3`:
  6 failed, 6 passed. Danach: 12 passed.
- **Commit:** `4785d87`, `b9e8bf3`

**2. [Rule 2 - Missing critical] Die `echo`-Zeilen des Fehlerpfads sind mitgezogen**

- **Found during:** Task 3
- **Issue:** Das Abnahmekriterium des Plans sagt, `git diff` solle
  ausschliesslich Kommentar- und Textzeilen zeigen und nichts an `run:`. Die
  `must_haves`-Wahrheit desselben Plans sagt dagegen, "der Erklaertext **im
  Fehlerpfad**, den ein Mensch liest", duerfe die alte Zusage nicht mehr sagen,
  und genau dieser Text sind die vier `echo`-Zeilen innerhalb von `run:`. Sie
  zaehlten drei moegliche Ursachen auf und kannten die zwei neuen nicht.
- **Fix:** Die vier Zeilen sind auf sieben erweitert: die Zusage im Wortlaut und
  fuenf moegliche Ursachen. Aufruf, `sed`-Praefix, Exit-Behandlung und Artefakt
  sind byteweise unveraendert, ebenso jedes `uses:` und jedes `permissions:`.
- **Verification:** `git diff .github/workflows/resilience.yml` zeigt ausser
  Kommentarzeilen nur die acht `echo`-Zeilen; kein `uses:`, kein `permissions:`,
  keine Aenderung an `docker run` oder `exit 1`.
- **Commit:** `1a9fe4d`

**3. [Rule 1 - Bug] Der Wortlaut der Zaehlmeldung im Modulkopf war nach vier Phasen falsch**

- **Found during:** Task 1
- **Issue:** Der Schlusssatz des Modulkopfs lautete "0 when every counter is
  one". Mit der vierten Phase ist `engine_loads_after_rewarm` zwei und trotzdem
  gruen, der Satz haette also jeden Leser in die Irre gefuehrt, der ihn gegen
  die Ausgabe haelt. Ebenso der Absatztitel "The seventh number is a duration",
  der jetzt die neunte ist.
- **Fix:** "0 when every number is what the promise above says it has to be";
  siebte auf neunte, "six counters" auf "eight counters" im `Report`-Docstring.
- **Verification:** Sichtprobe gegen die neun Zeilen von `lines()`.
- **Commit:** `b9e8bf3`

**Total deviations:** 3 auto-fixed (1x Rule 1, 1x Rule 2, 1x Rule 3).
**Impact:** Keine Verhaltensaenderung am Produkt. Alle drei betreffen das
Messwerkzeug und die Texte, die es begleiten.

### Was der Plan vorsah und anders ausfiel

- Der Plan erwartete "drei neue Zweige" in `findings()`. Seine eigene Aufzaehlung
  nennt aber nur zwei neue Bedingungen; der dritte Punkt ist eine Ergaenzung der
  bestehenden Worker-Meldung. Umgesetzt ist genau das: zwei neue `if`-Zweige
  (sechs auf acht) und ein erweiterter Meldungstext.
- Der Plan diskutiert im Action-Block `release_if_idle(0)` und verwirft es
  selbst. Umgesetzt ist der dort empfohlene Weg, `shared_model().release()`.

## Verification

| Nr. | Pruefung | Ergebnis |
| --- | -------- | -------- |
| 1 | `uv run ruff check .` | All checks passed |
| 1 | `uv run ruff format --check .` | 123 files already formatted |
| 1 | `uv run pyright` | 0 errors, 0 warnings |
| 1 | `uv run vulture src tests --min-confidence 80` | keine Ausgabe |
| 2 | `uv run pytest -q` (VOLLE Suite) | **2258 passed, 15 skipped** (vorher 2254) |
| 3 | neun Zahlenzeilen in `lines()` | 9, in der vorgesehenen Reihenfolge |
| 3 | `python -m findling.tools.one_load` | siehe Hinweis unten |
| 4 | `yaml.safe_load` auf `resilience.yml` | parsed |
| 4 | `grep -c 'warm window'` in `resilience.yml` | 5 |
| 4 | `grep -q 'one embedding engine per process'` | kommt nicht mehr vor |
| 5 | `grep -c 'def test_it_goes_red'` | **5** |
| - | `Report`-Felder | 9 |
| - | `cold_search_ms` innerhalb von `findings()` | nur im Docstring, in keinem Zweig |
| - | `uv run pytest tests/test_workflow_pins.py -q` | 14 passed |
| - | `uv run pytest tests/test_measurement_scripts.py -q` | 230 passed |

**Hinweis zu Pruefung 3, dem freien Lauf.** `uv run python -m
findling.tools.one_load` ist auf der Entwicklermaschine nicht fahrbar und war es
vor diesem Plan auch nicht: die Vorgabe von `--source` ist
`/usr/share/dict/ngerman`, die es unter Windows nicht gibt, und die
Modellartefakte werden erst im Image-Bau gebacken. Der Lauf gehoert in den
Container und wird dort von `resilience.yml` gefahren. Gedeckt ist er in der
Suite durch drei Faelle, die `main()` mit `--volume` und `--source` aufrufen und
Exit 0 samt `verdict=ok` pruefen, darunter der neue
`test_the_fourth_phase_releases_the_weights_and_fetches_them_back`. Das ist
keine Abweichung dieses Plans, sondern die Arbeitsteilung des Werkzeugs seit
06.1-04.

## Known Stubs

Keine. Kein Feld, kein Zweig und keine Meldung ist ein Platzhalter; jede der
neun Zahlen wird gemessen und zwei von ihnen zusaetzlich beurteilt.

## Acceptance Items (Owner, Phasen-Checkpoint 14-12)

- Der erste Lauf des Schritts `One engine and one constituent list per process`
  nach dem naechsten Containerbau: die Ausgabe muss neun Zahlenzeilen und
  `verdict=ok` tragen, mit `engine-unloads-after-release=1` und
  `engine-loads-after-rewarm=2`. Das ist die erste Gegenprobe im echten
  Container statt gegen die Attrappen der Suite.
- Der Werkslauf hat den Schalter aus (`embed_idle_release_seconds == 0`), also
  laedt die zweite Suchrunde wirklich nach. Bliebe der Schalter in einem
  Messcontainer einmal an, wuerde `query_may_load()` die Runde zurueckweisen und
  das Fenster auf null Ladevorgaenge fallen. Das gehoert als Zeile in das
  Runbook von 14-11.

## Threat Flags

Keine neue Angriffsflaeche. Kein neuer Netzpfad, keine neue Route, kein neuer
Dateizugriff, keine Schemaaenderung, keine neue Abhaengigkeit (T-14-SC).

Die vier Dispositionen des Plans sind erfuellt:

| Threat ID | Erfuellt durch |
| --------- | -------------- |
| T-14-37 | Die vierte Phase plus die Klausel `unloads != 1` als eigener Befund vor der Beurteilung des Fensters |
| T-14-38 | Beide Zaehler monoton; der Absatz dazu steht im Modulkopf und im Workflow-Kommentar, `engine.reset()` nullt keinen von beiden |
| T-14-39 | Zwei Mutationsfaelle am echten Baum (`EmbeddingModel.release`, `EmbeddingModel._load`), beide pruefen Exit 1 und den Wortlaut |
| T-14-40 | Die zwei neuen Zeilen sind Zaehler; kein Dateiname, kein Text, keine Bestandsgroesse reist in die CI-Ausgabe |

## Next Phase Readiness

MEM-05 ist vollstaendig: 14-09 hat die Admin-Haelfte geliefert, 14-10 die
Zusage und ihr Gate. Welle 6 ist abgeschlossen. Ready for 14-11 (embeddings.md,
performance.md und das Runbook der Box-Anfahrt); der Hinweis zum Schalter im
Messcontainer oben ist eine Zeile, die dort hineingehoert.

## Self-Check: PASSED

- `backend/src/findling/tools/one_load.py` vorhanden, neun Report-Felder, vierte
  Phase in `measure`, acht Zweige in `findings`.
- `backend/tests/test_one_load.py` vorhanden, fuenf `test_it_goes_red`-Faelle,
  14 Faelle gruen.
- `.github/workflows/resilience.yml` vorhanden, parst, alte Zusage entfernt.
- Alle vier Commits in `git log` gefunden: `4785d87`, `b9e8bf3`, `17fc0d4`,
  `1a9fe4d`.
- Volle Suite 2258 gruen, alle vier Qualitaetsgates gruen.
