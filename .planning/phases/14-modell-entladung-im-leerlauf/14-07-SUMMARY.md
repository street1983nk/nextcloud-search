---
phase: 14-modell-entladung-im-leerlauf
plan: 07
subsystem: infra
tags: [memory, lifespan, asyncio, to-thread, shutdown, tdd]

# Dependency graph
requires:
  - phase: 14-modell-entladung-im-leerlauf
    provides: Der Schalter embed_idle_release_seconds aus 14-03, busy und release_cutter aus 14-04, die Uhr und release() aus 14-05, release_if_idle, warm_wanted und warm aus 14-06
  - phase: 05-indexlauf
    provides: Das Muster der zwei langlebigen Aufgaben der Lifespan samt Stopp-Event, shield, Timeout, cancel und gather
provides:
  - _release_when_idle, die dritte langlebige Aufgabe der Lifespan
  - RELEASE_TICK_SECONDS, die Aufloesung der Leerlauf-Uhr
  - RELEASE_STOP_SECONDS, das Budget des Herunterfahrens fuer diese Aufgabe
  - Das vierte Stopp-Event und sein Aufraeumblock im finally
  - Der erste und einzige Aufrufer von release_if_idle und release_cutter
affects: [14-08, 14-10, 14-11, 14-12, 15-boxmessung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine blockierende Fremdfunktion wird auf dem Event Loop nie direkt gerufen, und dass sie es nicht wird, haelt ein Gate am Syntaxbaum statt eines Verhaltenstests"
    - "Ein Takt prueft das Stopp-Event ein zweites Mal direkt hinter der Pause, damit das Herunterfahren keine Arbeit mehr anfaengt, die niemand mehr braucht"
    - "Eine Fehlerzeile sagt, welche der beiden Ebenen geendet hat: der Takt oder die Aufgabe"

key-files:
  created:
    - backend/tests/test_main_lifespan.py
  modified:
    - backend/src/findling/main.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Kein else-Zweig mit Logzeile bei ausgeschaltetem Schalter: der Werksstand ist aus, und eine Zeile bei jedem Start ueber eine Funktion, die niemand eingeschaltet hat, ist Rauschen; der Behavior-Block des Plans verlangte das Gegenteil, der Action-Block mit seiner Begruendung hat Vorrang bekommen"
  - "Ein zweiter Blick auf das Stopp-Event direkt hinter _pause: ohne ihn liefe im Herunterfahren noch ein voller Takt, und ein dort gestarteter Warmlauf haelt den Prozessausgang sekundenlang im Threadpool fest (T-14-26)"
  - "Die Fehlerzeile sagt 'a tick of the release task ended', nicht 'the release task ended': die Aufgabe laeuft weiter, und wer die Zeile liest, soll nicht nach einer toten Aufgabe suchen"
  - "_pause wird privat importiert, mit dem Grund daneben: eine zweite Kopie der drei Zeilen waere eine zweite Wahrheit ueber das Stoppverhalten, und _pause oeffentlich zu machen waere eine Aenderung an poller.py, die dieser Plan sonst nicht anfasst"
  - "Eine eigene Testdatei test_main_lifespan.py statt eines Anbaus an test_lifecycle.py: der Plan nennt sie in must_haves und in beiden Pruefbefehlen, und test_lifecycle.py bleibt die Datei des AppAPI-Handschlags"

patterns-established:
  - "Die Attrappe von _pause zaehlt ihre Aufrufe, setzt nach n Takten das Stopp-Event und gibt die abgefragten Sekunden zurueck: so haelt ein Fall die Taktlaenge fest, ohne dass ein Fall sie abwartet"
  - "Die Reihenfolge zweier Freigaben wird in einem gemeinsamen Journal gefuehrt, das beide Attrappen beschreiben"

requirements-completed: []  # MEM-02 hat ab jetzt ihren Aufrufer, es fehlt nur noch die benannte Beleg-Messung, Begruendung im Abschnitt Requirements

# Metrics
duration: 20min
completed: 2026-09-19
---

# Phase 14 Plan 07: Die dritte Aufgabe der Lifespan Summary

**Der Container hat ab jetzt einen Takt: alle 30 Sekunden fragt `_release_when_idle`, ob gewaermt, ob gewartet oder ob losgelassen wird, gibt im dritten Fall beide Speicherhalter zusammen frei, und keiner der drei blockierenden Aufrufe beruehrt jemals den Event Loop.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-09-19T14:33:00Z
- **Completed:** 2026-09-19T14:53:00Z
- **Tasks:** 2 von 2
- **Files modified:** 3 (eine neue Testdatei, kein neues Modul, keine neue Abhaengigkeit)

## Accomplishments

### Aus sechs ungerufenen Zugaengen wird eine Funktion

Drei Plaene in Folge endeten mit dem Satz "gerufen wird es hier von niemandem".
Das ist seit diesem Plan nicht mehr wahr:

| Zugang | Gebaut in | Gerufen seit |
|---|---|---|
| `engine.release_if_idle(ttl)` | 14-06 | diesem Plan, ueber `asyncio.to_thread` |
| `poller.release_cutter()` | 14-04 | diesem Plan, ueber `asyncio.to_thread` |
| `poller.busy` | 14-04 | diesem Plan, als zweite Bedingung |
| `engine.warm_wanted()` | 14-06 | diesem Plan, als erste Frage jedes Takts |
| `engine.warm()` | 14-06 | diesem Plan, ueber `asyncio.to_thread` |
| `engine.request_warm()` | 14-06 | weiterhin niemand, das ist 14-08 |

Der Takt selbst hat vier Ausgaenge, und die Reihenfolge ist keine Geschmacksfrage:

1. **Warmlauf faellig** -> waermen und `continue`. Waermen und Entladen teilen
   sich nie einen Takt, sonst wuerfe der Durchgang das Ladepaar weg, das er
   gerade bezahlt hat.
2. **Poller an Arbeit** -> `continue`. Pitfall 3: zwischen zwei Batches
   loszulassen heisst, die Gewichte Sekunden spaeter erneut zu bezahlen, und
   nichts wird dabei irgendwo rot.
3. **Kein Poller** -> es wird trotzdem gefragt. Kein Poller heisst, dass kein
   Indexlauf laufen kann; die Abwesenheit beantwortet dieselbe Frage wie das
   Property.
4. **Freigabe wahr** -> und nur dann faellt auch der Cutter.

### Beide Halter fallen zusammen, und in dieser Reihenfolge

`release_cutter` steht hinter einer Freigabe, die `True` geliefert hat, und
nicht daneben. `release_if_idle` traegt die Uhr und die Identitaetspruefung,
`release_cutter` traegt keine eigene Frist. Ein `release_cutter` ohne eine
vorangegangene Freigabe wuerde den Cutter nach jeder Ruhephase wegwerfen, auch
in den Ruhephasen, in denen die Suchseite gerade eingebettet hat. Ein eigener
Testfall haelt beide Haelften fest: bei `release_if_idle -> False` bleibt der
Cutter stehen, bei `True` lautet das gemeinsame Journal
`["warm_wanted", "release_if_idle", "release_cutter"]`.

### Kein blockierender Aufruf auf dem Event Loop, und das steht im Baum

`gc.collect()`, `malloc_trim(0)` und ein Ladevorgang liegen im Bereich von
Sekunden. Ein blockierter Loop ist ein Container, der aufhoert, `/heartbeat` zu
beantworten, waehrend sein eigenes Protokoll kerngesund aussieht (T-14-23).
Alle drei Aufrufe laufen deshalb ueber `asyncio.to_thread`, und dass sie es tun,
haelt nicht nur ein Verhaltenstest, sondern ein Gate am Syntaxbaum:

- kein `Call`-Knoten in `_release_when_idle`, dessen Ziel `warm`,
  `release_if_idle` oder `release_cutter` heisst,
- genau drei `to_thread`-Uebergaben,
- und deren erste Argumente sind genau diese drei Namen.

Ein Verhaltenstest sagt, was einmal geschah; der Baum sagt, was beim naechsten
Umbau geschieht. Dazu ein zweites Gate: `except asyncio.CancelledError: raise`
steht vor dem allgemeinen Zweig, abgelesen an der Reihenfolge der
`ExceptHandler`-Knoten, samt der Pruefung, dass der erste Zweig ein `raise` ist.

### Die Aufgabe endet mit dem Container, und sie faengt nichts mehr an

Im `finally` steht `stop_release.set()` neben den zwei bestehenden, und der
Aufraeumblock folgt dem Muster von `repairing`: `shield` mit
`RELEASE_STOP_SECONDS` (5,0 s), danach `cancel` und `gather`.

Dazu eine Zeile, die der Plan nicht verlangt hat und die der Aufraeumblock
braucht, um sein Budget halten zu koennen: direkt hinter `_pause` wird das
Stopp-Event ein zweites Mal gelesen und der Takt abgebrochen. `_pause` kehrt
zurueck, sobald das Stopp-Event gesetzt ist, also liefe ohne diesen Blick im
Herunterfahren noch ein vollstaendiger Takt. Dessen teuerster Ausgang ist ein
Warmlauf: ein Laden, das niemand mehr benutzt, in einem Threadpool-Thread, den
der Prozessausgang abwarten muss. Das ist genau die Form von T-14-26, gegen die
das vierte Stopp-Event gebaut ist.

### Der Schalter ist ab Werk aus, und das bleibt still

Ohne `FINDLING_EMBED_IDLE_RELEASE_SECONDS` wird die Aufgabe nicht erzeugt, und
es erscheint auch keine Zeile darueber. Der Kommentar an der Stelle sagt
ausdruecklich, dass hier kein `else`-Zweig hingehoert und warum der
Reconcile-Block daneben einen hat: der Abgleich ist ab Werk AN, deshalb ist
seine Aus-Zeile ihren Platz wert; die Entladung ist ab Werk AUS, und eine Zeile
bei jedem Start ueber eine ausgeschaltete Funktion ist Rauschen.

## Task Commits

| Schritt | Commit | Inhalt |
|---|---|---|
| Task 1 (ROT) | `b6b8a54` | `tests/test_main_lifespan.py`, zehn Faelle zum Behavior-Block, ROT mit `ImportError: cannot import name 'RELEASE_TICK_SECONDS'` |
| Task 1 (GRUEN) | `d78032c` | `RELEASE_TICK_SECONDS`, `RELEASE_STOP_SECONDS`, `_release_when_idle`, das vierte Stopp-Event und sein Aufraeumblock, dazu der Baumhash |
| Task 2 | `42a80c9` | sieben weitere Faelle: Reihenfolge, Frist aus den Einstellungen, zwei Quelltext-Gates, abgebrochener Takt, Ende mit der Lifespan, Heartbeat mit der echten Aufgabe |

Eine REFACTOR-Stufe gab es nicht: die Funktion ist in ihrer ersten gruenen Form
geblieben.

## TDD Gate Compliance

Task 1 traegt `tdd="true"` und ist in der Reihenfolge ROT, GRUEN gefahren.

| Tor | Beleg |
|---|---|
| ROT | `ImportError: cannot import name 'RELEASE_TICK_SECONDS' from 'findling.main'`, Sammlung abgebrochen, kein Fall gelaufen |
| GRUEN | 10 bestanden in 0,06 s |

## Tests

17 Faelle in der neuen Datei, keiner mit einem Skip-Marker, keiner langsamer als
0,02 s (`--durations=5`: 0,02 s Setup, 0,01 s Aufruf, der Rest unter 0,005 s).
Die Zahl der Skips der vollen Suite bleibt bei 15.

| Block | Faelle |
|---|---|
| Ob die Aufgabe ueberhaupt entsteht (aus, an) | 2 |
| Der Takt und seine vier Bedingungen | 6 |
| Fehler, Abbruch und Stopp | 3 |
| Reihenfolge und Frist | 2 |
| Gates am Syntaxbaum | 2 |
| Lifespan: Ende der Aufgabe, Heartbeat mit der echten Aufgabe | 2 |

Drei Bauformen tragen die Datei:

- **Die Attrappe von `_pause`.** Sie kehrt sofort zurueck, zaehlt ihre Aufrufe,
  setzt nach `n` Takten das Stopp-Event und gibt die abgefragten Sekunden
  zurueck. Kein Fall wartet also den 30-Sekunden-Takt ab, und ein Fall haelt die
  Taktlaenge trotzdem fest.
- **Ein gemeinsames Journal.** Motor-Spion und Poller-Attrappe schreiben in
  dieselbe Liste, sonst waere die Reihenfolge der zwei Freigaben nur indirekt
  ueber zwei Zaehler ablesbar.
- **Zwei Gates am Syntaxbaum**, wie in 14-04 und 14-06 eingefuehrt.

Kein Fall misst Speicher. Alle pruefen Aufrufe und Rueckgabewerte, mit der
Begruendung, die im Kopf von `tools/one_load.py` steht: eine Speicherschwelle
auf einem geteilten Runner geht fuer Runner-Last rot und nicht fuer die benannte
Sache.

## Files Created/Modified

- `backend/src/findling/main.py` , zwei Konstanten, die Funktion
  `_release_when_idle` hinter `_guarded_reconcile`, der bedingte Block in der
  Lifespan, `stop_release.set()` und der Aufraeumblock im `finally`, dazu drei
  Importzeilen (`Final`, die drei Engine-Funktionen, `_pause`)
- `backend/tests/test_main_lifespan.py` , neu, 17 Faelle
- `backend/tests/test_measurement_scripts.py` , `PACKAGE_TREE_HASH_TODAY` auf
  `059379c2...`, mit dem Begruendungsabsatz in der Hausform der Datei; 54
  Dateien unveraendert

## Decisions Made

- **Kein `else`-Zweig mit Logzeile.** Der Behavior-Block des Plans verlangt bei
  ausgeschaltetem Schalter "eine Info-Zeile, die einmal sagt, dass die Entladung
  aus ist"; der Action-Block desselben Tasks verbietet genau diese Zeile und
  begruendet es. Der Action-Block hat gewonnen, weil er der spezifischere und
  der begruendete der beiden ist, und weil die Abnahmekriterien die Zeile nicht
  nennen. Der Testfall haelt die getroffene Wahl fest: bei ausgeschaltetem
  Schalter gibt es keinen Protokolleintrag, der das Wort `release` enthaelt.

- **Der zweite Blick auf das Stopp-Event.** Siehe oben; ohne ihn kann der
  Aufraeumblock sein eigenes Budget nicht halten.

- **Die Fehlerzeile nennt den Takt, nicht die Aufgabe.** Der Plan gibt den
  Wortlaut von `_guarded_reconcile` vor ("the release task ended in an
  unexpected %s"). Dort ist er wahr, denn dort ist die Aufgabe wirklich zu Ende;
  hier laeuft der naechste Takt weiter, und genau das verlangt der Behavior-Block.
  Eine Zeile, die den Betreiber eine tote Aufgabe suchen laesst, die es nicht
  gibt, ist eine falsche Zeile.

- **`_pause` privat importiert**, mit dem Grund im Docstring: eine zweite Kopie
  derselben drei Zeilen waere eine zweite Wahrheit ueber das Stoppverhalten
  dieses Containers. Die Alternative, `_pause` oeffentlich zu machen, waere eine
  Aenderung an `worker/poller.py`, die dieser Plan sonst nicht anfasst. Die
  Werkzeuge stoert der Import nicht: ruff fuehrt keine Regel dagegen, und
  pyright meldet `reportPrivateUsage` im `basic`-Modus nicht.

- **Eine eigene Testdatei.** `must_haves.artifacts` und beide `verify`-Befehle
  des Plans nennen `tests/test_main_lifespan.py`; die bestehende
  `tests/test_lifecycle.py` ist die Datei des AppAPI-Handschlags und der
  Armierungsmarke. Die neue Datei ist die Datei der langlebigen Aufgaben.

- **Ein Fall fuer Verifikationspunkt 3 statt eines Containerstarts.** Der Punkt
  verlangt, dass der Backend-Prozess mit gesetztem Schalter startet und
  `/heartbeat` weiter antwortet. Der letzte Fall der Datei faehrt genau das ohne
  Attrappen: Schalter an, echte Aufgabe im Lauf, `GET /heartbeat` gibt 200 und
  `{"status": "ok"}`. Ein blockierter Loop wuerde hier auffallen und in keinem
  anderen Fall der Datei, weil alle anderen den Takt von Hand treiben.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] Der Baumhash des Pakets musste mitwandern**

- **Found during:** Task 1 (GRUEN)
- **Issue:** `tests/test_measurement_scripts.py` haelt einen sha256 ueber alle 54
  Dateien des Python-Pakets. `main.py` ist eine davon. Die Datei steht wieder
  nicht in `files_modified` des Plans, und Verifikationspunkt 5 verlangt sogar
  ausdruecklich, dass nur zwei Dateien veraendert sind. Das ist der fuenfte Plan
  in Folge.
- **Fix:** `PACKAGE_TREE_HASH_TODAY` mit dem Originalrezept
  (`docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.py`) neu
  gelesen: `059379c29a82542dbf6642e36fa8a39208d4921e5980b14c1827b7530dbb6836`,
  54 Dateien, mit Begruendungsabsatz in der Hausform der Datei.
- **Verification:** `uv run pytest tests/test_measurement_scripts.py -q`, 230
  bestanden.
- **Committed in:** `d78032c`

**2. [Rule 1 - Bug] Widerspruch im Plan: die Logzeile bei ausgeschaltetem Schalter**

- **Found during:** Task 1
- **Issue:** Der Behavior-Block verlangt eine Info-Zeile, der Action-Block
  desselben Tasks verbietet sie mit Begruendung. Gebaut werden kann nur eines
  von beiden.
- **Fix:** Der Action-Block ist umgesetzt (keine Zeile), der Testfall prueft die
  Abwesenheit statt der Anwesenheit.
- **Files modified:** `backend/src/findling/main.py`,
  `backend/tests/test_main_lifespan.py`
- **Committed in:** `b6b8a54` und `d78032c`

**3. [Rule 2 - Fehlende kritische Funktion] Der Takt faengt im Herunterfahren nichts Neues mehr an**

- **Found during:** Task 1
- **Issue:** Der Rumpf des Plans prueft das Stopp-Event nur am Kopf der
  Schleife. `_pause` kehrt zurueck, sobald das Stopp-Event gesetzt wird, also
  liefe im Herunterfahren noch ein vollstaendiger Takt. Ein dort gestarteter
  Warmlauf ist ein Laden, das niemand benutzt, in einem Threadpool-Thread, den
  der Prozessausgang abwarten muss; `RELEASE_STOP_SECONDS` von 5,0 s waere damit
  planmaessig ueberschritten. Das ist T-14-26 in seiner konkreten Form.
- **Fix:** Ein `if stop_event.is_set(): break` direkt hinter `_pause`, mit der
  Begruendung als Kommentar. Ein Testfall (`_ticks(monkeypatch, 0)`) haelt fest,
  dass nach dem Stopp kein Takt mehr laeuft.
- **Files modified:** `backend/src/findling/main.py`
- **Committed in:** `d78032c`

**4. [Rule 1 - Bug] Der Wortlaut der Fehlerzeile**

- **Found during:** Task 1
- **Issue:** Der vom Plan vorgegebene Text sagt "the release task ended in an
  unexpected %s". Die Aufgabe endet dort aber gerade nicht, das ist die
  ausdrueckliche Zusage des Behavior-Blocks.
- **Fix:** "a tick of the release task ended in an unexpected %s; the next tick
  runs, search and indexing continue".
- **Committed in:** `d78032c`

### Nebenbefund, mit korrigiert

**5. [Rule 1 - Bug] `14-06` war in der ROADMAP nicht abgehakt**

Der Fahrplan fuehrte 14-06 nach dessen Abschluss weiterhin als offen und zaehlte
"5/12 plans executed". Beide Stellen sind mit diesem Plan nachgezogen (jetzt
7/12, Welle 4 und die erste Haelfte von Welle 5 abgehakt).

### Bewusst nicht getan

- **`REQUIREMENTS.md` unberuehrt**, siehe naechster Abschnitt.
- **Kein `request_warm()`-Aufruf.** Der gehoert auf die Suchroute und ist 14-08.
- **Nichts an `worker/poller.py`,** obwohl `_pause` privat ist.

---

**Total deviations:** 5 auto-fixed (1 Blocker, 3 Bugs, 1 fehlende kritische
Funktion)
**Impact on plan:** Keine Umfangserweiterung. Befund 1 ist die seit 14-03
bekannte Luecke der Planvorlage, Befund 2 loest einen Selbstwiderspruch des
Plans auf, Befund 3 ist eine Zeile, die eine Zusage des Plans erst haltbar
macht, Befund 4 ist Wortlaut, Befund 5 betrifft nur den Fahrplan.

## Requirements

**MEM-02 wird auch hier nicht abgehakt, und diesmal fehlt nur noch eines.**

Der Wortlaut: "Die Entladung gibt BEIDE Speicherhalter frei (EmbeddingModel-Engine
UND Poller-Cutter/Tokenizer); die Beleg-Messgroesse ist 'Rueckkehr zur Grundlast
nach einem Indexlauf', nicht 'Grundlast minus X'."

Der erste Halbsatz ist seit diesem Plan erfuellt: beide Halter fallen, sie
fallen zusammen, sie fallen auf einem Takt, und der Takt endet mit dem
Container. Was bisher fehlte, war der Aufrufer, und der ist gebaut. Der zweite
Halbsatz benennt die Messgroesse, an der die Anforderung belegt sein will, und
diese Messung hat nicht stattgefunden: sie ist Erfolgskriterium 3 der Phase, sie
wird in 14-12 an der laufenden Instanz nachgesehen und in der einen
Box-Anfahrt der Phase 15 (MESS-05) A/B gefahren.

Die Lehre aus 14-01 steht in STATE.md: eine Anforderung gehoert an den Plan, der
sie belegt, und nicht an den, der ihr Werkzeug baut. Damals wurde MEM-04
verfrueht abgehakt und der Haken musste zurueckgenommen werden. Ein Haken hier
wuerde einen Beleg behaupten, den niemand gemessen hat.

**Fuer 14-12:** MEM-02 ist code-seitig vollstaendig. Sobald die Sichtprobe an
der laufenden Instanz die Rueckkehr zur Grundlast zeigt, ist die Anforderung
abzuhaken; es ist kein Bau mehr noetig.

MEM-01 steht seit 14-03 auf Complete und wird hier nur gelesen.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Registers. Die sechs Eintraege des
Plans sind abgedeckt:

| Threat | Umsetzung |
|---|---|
| T-14-23 (blockierender Aufruf auf dem Loop) | alle drei Aufrufe ueber `asyncio.to_thread`, gehalten von einem Gate am Syntaxbaum |
| T-14-24 (Entladen mitten im Indexlauf) | zweite Bedingung `poller.busy`, plus die Sperre in `release_cutter` selbst |
| T-14-25 (Aufgabe stirbt an einer Ausnahme) | `try/except` um den ganzen Takt, `CancelledError` durchgereicht, nur der Typname geloggt, zwei Testfaelle und ein Gate |
| T-14-26 (Aufgabe ueberlebt den Shutdown) | viertes Stopp-Event, `shield` mit `RELEASE_STOP_SECONDS`, `cancel` plus `gather`, dazu der Abbruch direkt hinter `_pause` |
| T-14-27 (Logzeile der Entladung) | eine Zeile beim Start, ohne Zahl; der Takt selbst schreibt im Erfolgsfall gar nichts |
| T-14-SC (Abhaengigkeiten) | keine neue Abhaengigkeit, `pyproject.toml` unberuehrt |

## Known Stubs

Keine. `request_warm()` hat weiterhin keinen Aufrufer und `query_may_load()`
wird von den zwei Nutzerrouten noch nicht gefragt; beides ist die ausdrueckliche
Absicht von 14-06 und der Auftrag von 14-08, und beides liegt ausserhalb der
Dateiliste dieses Plans.

## Gates

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` | gruen |
| `uv run ruff format --check .` | gruen, 123 Dateien |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | gruen, keine Funde |
| `uv run pytest tests/test_main_lifespan.py -q --durations=5` | 17 bestanden in 0,12 s |
| `uv run pytest -q` (VOLLE Suite) | **2221 bestanden, 15 uebersprungen**, 187 s |

Kein PHP angefasst, also keine Ersatzpruefung noetig.

## Verification

| Punkt des Plans | Ergebnis |
|---|---|
| 1. Alle vier Gate-Stufen gruen | ja, Tabelle oben |
| 2. Volle Suite gruen | ja, 2221 bestanden (vorher 2204) |
| 3. Mit gesetztem Schalter startet der Prozess und `/heartbeat` antwortet; ohne gesetzte Variable keine Zeile ueber die Entladung | als zwei Testfaelle gefahren statt als Containerstart, siehe "Decisions Made"; beide gruen |
| 4. Jeder Aufruf von `release_if_idle`, `release_cutter` und `warm` steht innerhalb eines `asyncio.to_thread` | ja, `main.py:300`, `310`, `311`; zusaetzlich vom Gate am Syntaxbaum gehalten |
| 5. Nur `main.py` und die Lifespan-Testdatei veraendert | **nicht gehalten**, dazu `tests/test_measurement_scripts.py`, siehe Abweichung 1 |

Abnahmekriterien der zwei Tasks, einzeln nachgefahren:

| Kriterium | Ergebnis |
|---|---|
| `_release_when_idle` existiert und wird nur bei `embed_idle_release_seconds > 0` erzeugt | ja, zwei Lifespan-Faelle |
| Drei neue `to_thread`-Vorkommen innerhalb der Funktion | ja, vom Gate auf genau drei festgelegt |
| Kein Aufruf von `release_if_idle`, `warm` oder `release_cutter` ohne `asyncio.to_thread` | ja, Gate am Syntaxbaum |
| `stop_release.set()` neben den zwei anderen, Aufraeumblock nach dem `repairing`-Muster | ja, `shield`, Timeout, `cancel`, `gather` |
| `except asyncio.CancelledError: raise` vor dem allgemeinen `except` | ja, Gate am Syntaxbaum plus Verhaltensfall |
| Mindestens neun neue Testfaelle, einer je Zeile des Behavior-Blocks | **17** |
| Kein Fall laenger als 2 Sekunden | ja, langsamster 0,02 s |
| Kein Fall misst Speicher | ja, alle zaehlen Aufrufe |
| Der Reihenfolge-Fall ist vorhanden und gruen | ja |

## Issues Encountered

Keine offenen.

Der Hinweis aus Abweichung 1 gilt weiter und gehoert vor 14-08, 14-09 und 14-10
in die Dateiliste: `tests/test_measurement_scripts.py` ist die dritte Datei
jedes Plans, der Python-Produktcode anfasst. Fuenf Plaene in Folge haben sie als
Abweichung nachgezogen.

## User Setup Required

None - keine externe Konfiguration noetig. Wer die Entladung lokal sehen will,
setzt `FINDLING_EMBED_IDLE_RELEASE_SECONDS` auf mindestens 60.

## Next Phase Readiness

Bereit fuer **14-08**, den zweiten Plan der Welle 5. Er naeht die Degradation
auf die zwei Nutzerrouten (`api/search.py`, `api/snippets.py`) und stoesst das
Nachwaermen an. Der Takt, der das Nachwaermen dann ausfuehrt, steht ab jetzt und
fragt `warm_wanted()` als erste Frage jedes Durchgangs; 14-08 muss also nur
`request_warm()` setzen, der Rest laeuft von selbst.

Zwei Hinweise wandern weiter:

- **Erfolgskriterium 3 der Phase ist code-seitig erfuellt.** Was fehlt, ist die
  Sichtprobe an der laufenden Instanz (14-12) und die A/B-Messung der Phase 15.
- **`RELEASE_TICK_SECONDS` ist 30,0 s.** Wer in 14-11 das Runbook schreibt,
  muss diese Aufloesung nennen: eine Entladung faellt nicht zur Sekunde der
  Frist, sondern im ersten Takt danach.

## Self-Check: PASSED

- `backend/src/findling/main.py`: vorhanden, enthaelt `_release_when_idle`,
  `RELEASE_TICK_SECONDS`, `RELEASE_STOP_SECONDS` und `stop_release`.
- `backend/tests/test_main_lifespan.py`: vorhanden, 17 Faelle, enthaelt
  `_release_when_idle`.
- `backend/tests/test_measurement_scripts.py`: vorhanden, neuer Baumhash.
- Die drei Commits `b6b8a54`, `d78032c` und `42a80c9` stehen in der Historie.
- Die fuenf Verifikationspunkte sind einzeln nachgefahren; Punkt 5 ist mit der
  dokumentierten Abweichung 1 offen ausgewiesen statt stillschweigend abgehakt.

---
*Phase: 14-modell-entladung-im-leerlauf*
*Completed: 2026-09-19*
