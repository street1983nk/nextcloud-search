---
phase: 14-modell-entladung-im-leerlauf
plan: 06
subsystem: infra
tags: [memory, embeddings, single-flight, degradation, threading, tdd]

# Dependency graph
requires:
  - phase: 14-modell-entladung-im-leerlauf
    provides: Der Schalter embed_idle_release_seconds aus 14-03 und die Mechanik release(), last_use(), unload_count(), may_load aus 14-05
  - phase: 06.1-geteilte-engine
    provides: Der Halter _ENGINE mit seinem re-entranten _LOCK, _held() und die Zustandsfrage engine_state()
provides:
  - query_may_load(), die eine Stelle, an der steht, ob eine Suche laden darf
  - release_if_idle(), die Freigabe mit ihren zwei Bedingungen und der Identitaetspruefung
  - released_count(), die Durchreichung des Entladezaehlers ohne Import von model.py
  - request_warm(), warm_wanted() und warm(), das Nachwaermen mit Single-Flight
  - WARM_TEXT, die feste Zeile, die ein Warmlauf einbettet
affects: [14-07, 14-08, 14-09, 14-10, 14-11, 15-boxmessung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Die Mechanik steht in embed/model.py, die Politik in embed/engine.py: der Halter entscheidet, das Objekt fuehrt aus"
    - "Eine Regel, die drei Aufrufer brauchen, steht an einer Stelle und wird gefragt, nicht wiederholt"
    - "Eine Zusage, die strukturell erfuellt ist, wird im Docstring von dem Flag getrennt, das nur ihre Kosten senkt"

key-files:
  created: []
  modified:
    - backend/src/findling/embed/engine.py
    - backend/tests/test_embed_engine.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Die Degradation haengt am Schalter und gilt nicht generell: der Generalfall waere eine Verhaltensaenderung ausserhalb des Schalters und wuerde die eine Box-Anfahrt der Phase 15 zwei Aenderungen auf einmal messen lassen"
  - "api/diagnose.py fragt query_may_load bewusst nicht und laedt weiter, weil ein Messwerkzeug messen koennen muss; die Kehrseite, dass ein Diagnoseaufruf den Container aufwaermt, gehoert ins Runbook 14-11"
  - "Die Identitaetspruefung aus der Uebergabe von 14-05 ist in engine.py gelandet und nicht in release(): die Mechanik bleibt unten, die Politik steht oben"
  - "ttl <= 0 und last_use() is None antworten beide False, ohne den Halter zu fragen: Null ist das Wort fuer aus, und ein Halter, der nie gearbeitet hat, ist kein Leerlauf"
  - "Das Single-Flight-Flag _WARMING ist im Docstring ausdruecklich als Effizienz und nicht als Zusage benannt, weil _load() die Zusage schon strukturell haelt"
  - "ENGINE_STATES bleibt unveraendert: das sechste Wort unloaded kommt geschlossen mit seiner PHP-Haelfte in 14-09"

patterns-established:
  - "Ein Gate am Syntaxbaum haelt fest, wo ein Aufruf steht, nicht nur was er tut: release() ausserhalb von with _LOCK, _held statt shared_model, is statt Wertvergleich"
  - "Ein Rennen wird gefahren, indem die Frage selbst den Zustand aendert: die Uhrabfrage des alten Halters tauscht den Halter aus"

requirements-completed: []  # MEM-01 stand schon, MEM-02 und MEM-03 fehlen die Aufrufer, Begruendung im Abschnitt Requirements

# Metrics
duration: 25min
completed: 2026-09-19
---

# Phase 14 Plan 06: Der Halter bekommt die Politik Summary

**`embed/engine.py` weiss ab jetzt, wann eine Suche nicht laden darf, wann freigegeben wird und wann nachgewaermt wird: die Regel steht an genau einer Stelle, die Freigabe prueft unter dem Lock mit `is`, ob es noch dieselbe Instanz ist, und zehn gleichzeitige Warmlaeufe zahlen fuer genau ein Laden.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-19T14:05:00Z
- **Completed:** 2026-09-19T14:30:00Z
- **Tasks:** 3 von 3
- **Files modified:** 3 (kein neues Modul, keine neue Abhaengigkeit, ein neuer Stdlib-Import in den Tests)

## Accomplishments

### Sechs Zugaenge, und wieder ruft sie keiner

`embed/engine.py` hat sechs neue oeffentliche Funktionen und null neue Aufrufer
im Produktivcode. Das ist wie in 14-05 die ausgeschriebene Absicht des Plans:
der Takt kommt in 14-07, die Suchroute in 14-08.

| Zugang | Was er ist | Wer ihn rufen wird |
|---|---|---|
| `query_may_load() -> bool` | die Regel, ob eine Suche laden darf | `api/search.py` und `api/snippets.py` (14-08) |
| `release_if_idle(ttl) -> bool` | die Freigabe mit ihren zwei Bedingungen | die dritte Lifespan-Aufgabe (14-07) |
| `released_count() -> int` | der Entladezaehler ohne Import von `model.py` | die A/B-Messung der Phase 15 |
| `request_warm() -> None` | eine Suche meldet, dass sie ohne Gewichte geantwortet hat | `api/search.py` (14-08) |
| `warm_wanted() -> bool` | die vier Bedingungen eines Warmlaufs | der Aufrufer des Warmlaufs (14-08) |
| `warm() -> bool` | das Laden im Vordergrund des rufenden Threads | derselbe, ueber `asyncio.to_thread` |

### Die Regel steht einmal und haengt am Schalter

`query_may_load()` ist ein Einzeiler: `settings().embed_idle_release_seconds ==
0`. Der Docstring traegt die Entscheidung, die 14-RESEARCH.md als offene Frage 1
gestellt hat, ausformuliert und mit dem Vorfall: 1838,4 ms gegen eine Decke von
1500 ms am 10.09.2026, cURL error 28, eine Ergebnisgruppe ohne Containerteil,
null Treffer, und das alles von aussen unsichtbar, weil die Route mit HTTP 200
antwortet. Eine Naht ohne Schalter wuerde genau diesen Vorfall generell
abstellen und waere damit die bessere Ware, aber sie waere auch eine
Verhaltensaenderung an der ersten Suche jedes Containers ausserhalb des
Schalters. Die eine bezahlte Box-Anfahrt der Phase 15 wuerde dann zwei
Aenderungen auf einmal messen. Der Generalfall ist Backlog und steht im
Docstring, damit er nicht verloren geht.

`grep -rn --include='*.py' 'embed_idle_release_seconds' backend/src/findling/`
nennt genau zwei Dateien: `config.py` und `embed/engine.py`. Die drei Stellen,
die eine `SemanticSide` bauen, fragen die Regel, statt sie zu wiederholen.

Im Rumpf steht als Kommentar die Entscheidung zur zweiten offenen Frage:
`api/diagnose.py::ranked_sides` ruft `query_may_load()` **nicht** und laedt
weiter, weil ein Messwerkzeug messen koennen muss und die Route keine
1,5-Sekunden-Decke traegt. Die Kehrseite, dass ein Diagnoseaufruf den Container
aufwaermt und vor einer Kaltmessung deshalb nicht gemacht werden darf, ist dort
benannt und gehoert ins Runbook 14-11.

### Das Rennen, das wirklich zaehlt, ist entschieden

`release_if_idle(ttl)` laeuft in sechs Schritten, und zwei davon sind die
eigentliche Arbeit:

1. `ttl <= 0` antwortet `False`, ohne den Halter zu fragen. Null ist das Wort
   fuer aus, nicht eine Frist von null Sekunden.
2. Der Halter kommt ueber `_held(...)` und nie ueber `shared_model()`: ein
   leerer Halter wird mit `None` beantwortet und nicht gefuellt (T-14-21).
3. Kein Halter oder keine geladene Engine: `False`.
4. `last_use() is None` oder juenger als die Frist: `False`. Die `None` ist die
   Uebergabe aus 14-05 und bekommt ihre eigene Regel: ein Halter, der geladen
   hat und nie eingebettet hat, hat nichts loszulassen.
5. **Die Identitaetspruefung.** Unter `_LOCK` wird der Halter ein zweites Mal
   gelesen und mit `is` gegen die Instanz aus Schritt 2 gehalten. Das Nachwaermen
   laeuft neben der Entlade-Aufgabe, und eine Freigabe, die mit einem
   gleichzeitigen Laden kollidiert, wuerde das Ladepaar wegwerfen, das eine
   Millisekunde vorher bezahlt wurde (T-14-20).
6. `model.release()` **ausserhalb** von `_LOCK`, weil `release` seine eigene
   Sperre nimmt und danach den blockierenden Trim ruft; ein gehaltenes `_LOCK`
   wuerde jede gleichzeitige `shared_model()`-Frage mitblockieren (T-14-16).

Der Auftrag aus der Uebergabe von 14-05 ist damit erledigt, und er ist in
`engine.py` gelandet und nicht in `release()`: die Mechanik bleibt unten, die
Politik steht oben.

### Die Zusage und das Flag sind zwei verschiedene Dinge

Erfolgskriterium 5 der Phase verlangt woertlich "genau ein Laden je warmem
Fenster". Der Docstring von `warm()` trennt die zwei Ebenen, damit sie spaeter
nicht verwechselt werden:

| Ebene | Was sie leistet |
|---|---|
| `_load()` unter dem Lock des Halters, mit Rueckkehr am Kopf | die Zusage selbst, strukturell, unabhaengig von jedem Flag |
| `_WARMING` | spart die neun Threadpool-Threads, die sonst am Lock warten |

Der Zehn-Threads-Fall misst deshalb den Zuwachs von `load_count()` und nie ein
Byte: eine Spitzendifferenz ist nicht die Summe der Ladevorgaenge, die sie
erzeugt haben.

Dass `warm()` die Leerlauf-Uhr mitsetzt, ist die Bedingung und kein
Nebeneffekt. Der Lauf geht ueber `embed_query` und damit durch `_embed`, das
`_last_use` schreibt. Ohne die Uhr faende der naechste Takt einen Halter, dessen
letzte Nutzung aelter als die Frist ist, und fraesse das gerade bezahlte
Ladepaar. Ein Testfall belegt beides in einem: nach `warm()` ist die Uhr juenger,
und `release_if_idle(900)` antwortet direkt danach `False`.

### Was dieser Plan nicht angefasst hat

`ENGINE_STATES` ist byteweise unveraendert, `grep -c` gibt vor und nach dem Plan
dieselbe 1. Das sechste Wort `unloaded` kommt geschlossen mit seiner PHP-Haelfte
und seinen sechs Katalogen in 14-09. `tests/test_admin_ui_contract.py` ist mit
45 Faellen gruen, also ist kein Katalog-Gate beruehrt.

## Task Commits

1. **Task 1 (RED): Die Faelle der Regel** - `e3ebe33` (test)
2. **Task 1 (GREEN): query_may_load** - `e163d1b` (feat)
3. **Task 2 (RED): Die Faelle der Freigabe und der Identitaetspruefung** - `ff901c4` (test)
4. **Task 2 (GREEN): release_if_idle und released_count** - `601e9a4` (feat)
5. **Task 3 (RED): Die Faelle des Nachwaermens** - `cc60197` (test)
6. **Task 3 (GREEN): request_warm, warm_wanted und warm** - `9609dc2` (feat)
7. **Nachzug: Testnamen fuer den Pruefbefehl des Plans** - `59bc467` (test)

## TDD Gate Compliance

Alle drei Tasks tragen `tdd="true"` und sind in der Reihenfolge RED, GREEN
gefahren. Jeder RED-Lauf war rot, bevor eine Zeile Produktivcode entstand:

| Task | RED-Beleg | GREEN-Beleg |
|---|---|---|
| 1 | `ImportError: cannot import name 'query_may_load'` | 3 bestanden |
| 2 | `ImportError: cannot import name 'release_if_idle'` | 42 bestanden |
| 3 | `ImportError: cannot import name 'WARM_TEXT'` | 52 bestanden |

Ein REFACTOR-Schritt war in keinem Fall noetig; es gibt also bewusst keinen
`refactor`-Commit.

## Tests

25 neue Faelle, alle in `tests/test_embed_engine.py`, und **keiner** traegt
einen Skip-Marker. Die Zahl der Skips der vollen Suite ist unveraendert bei 15.

| Block | Faelle |
|---|---|
| `query_may_load` | 3 |
| `release_if_idle`, Verhalten | 8 |
| `release_if_idle`, Gates am Syntaxbaum | 3 |
| Zaehlerdurchreichung und Erhalt ueber `reset` | 1 |
| Nachwaermen | 10 |

Drei Bauformen sind neu in dieser Datei:

- **Der Austausch unter der laufenden Freigabe.** Die Uhrabfrage des alten
  Halters tauscht selbst den Halter aus. Das ist der einzige Weg, genau den
  Moment zu treffen, gegen den die Identitaetspruefung schuetzt, ohne einen
  echten Thread mit einer Wette auf das Scheduling zu fahren.
- **Drei Gates am Syntaxbaum.** `release_if_idle` wird als Quelltext gelesen und
  daran gehalten, dass `release()` genau einmal und nie innerhalb eines `with`
  gerufen wird, dass `_held` vorkommt und `shared_model` nicht, und dass die
  zweite Lesung des Halters genau einmal stattfindet und ein `is` benutzt. Eine
  Verhaltenspruefung sagt, was einmal geschah; der Baum sagt, was beim naechsten
  Mal geschieht.
- **Zehn Warmlaeufe aus einem `ThreadPoolExecutor`.** Gemessen wird der Zuwachs
  von `load_count()`, und er ist genau eins.

Dazu eine kleine Fixture `no_warm_request`, die den Modulmerker vor und nach
jedem Fall loescht, im Muster der `forget_the_cutter_notice`-Fixture der
conftest: ein Merker, der einen Fall ueberlebt, macht die Laufreihenfolge der
Suite an einer Antwort ablesbar.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] Baumhash der Messwerkstatt dreimal nachgezogen**

- **Found during:** Task 1, Task 2 und Task 3
- **Issue:** `tests/test_measurement_scripts.py` haelt einen sha256 ueber alle 54
  Dateien des Python-Pakets. `embed/engine.py` hat in allen drei Tasks seine
  Bytes geaendert; die Datei steht wieder nicht in `files_modified` des Plans,
  aber die Projektregel verlangt den Nachzug im selben Commit. Das ist der
  vierte Plan in Folge, in dem das passiert.
- **Fix:** `PACKAGE_TREE_HASH_TODAY` auf
  `f12f0766c01e2b521fa98a6aa53b0440c727847ae457a4e6d4e5b7386a323b0b` (Task 1),
  `33ec126633fb86de2b358ac311dbab6b1fbca9095982cb9a64217ce0bc64716a` (Task 2)
  und `c340cc629f3f4c2af433b86bce327aa44cd28777df6a2a97ef945ef7f4770424`
  (Task 3), je mit einem Absatz in der Form der sieben vorhergehenden Eintraege.
  Die Dateizahl bleibt 54.
- **Verification:** `uv run pytest tests/test_measurement_scripts.py -q` nach
  jedem Nachzug, 230 bestanden.
- **Committed in:** `e163d1b`, `601e9a4`, `9609dc2`

**2. [Rule 1 - Bug] Die Pruefbefehle des Plans waehlten keinen Fall aus**

- **Found during:** Task 1 und Task 2
- **Issue:** Die `<verify>`-Bloecke nennen `pytest -k "may_load"` und
  `pytest -k "release_if_idle"`. Mit den zuerst geschriebenen, beschreibenden
  Testnamen traf der erste Filter genau einen von drei Faellen und der zweite
  keinen einzigen von zwoelf. Ein `-k`, das nichts auswaehlt, laesst pytest mit
  Code 5 enden oder, schlimmer, mit einer gruenen Zeile ueber null Faellen. Der
  Pruefbefehl des Plans haette also einen Bau abgenommen, den er nie gesehen
  hat.
- **Fix:** Die Faelle tragen den Namen der Funktion, die sie pruefen.
  `-k "may_load"` waehlt jetzt 3 Faelle, `-k "release_if_idle"` 12.
- **Verification:** beide Befehle ausgefuehrt, 3 bestanden und 12 bestanden.
- **Committed in:** `e163d1b` (Task 1, im GREEN-Commit), `59bc467` (Task 2,
  eigener Commit nach dem GREEN-Lauf)

### Bewusst nicht getan

- **`reset()` loescht den Warmmerker nicht.** Die Isolation zwischen den
  Testfaellen kommt aus einer Fixture und nicht aus einer Aenderung am
  Produktivcode, die der Plan nicht verlangt. `reset()` laeuft ausserhalb eines
  Containers, und `tools/one_load.py` waermt nicht.
- **`ENGINE_STATES` nicht angefasst**, wie der Plan es ausdruecklich verlangt.
- **`REQUIREMENTS.md` unberuehrt** (siehe naechster Abschnitt).

---

**Total deviations:** 2 auto-fixed (1 Blocker, 1 Bug)
**Impact on plan:** Beide betreffen die Pruefbarkeit und nicht den Umfang. Kein
Scope Creep, keine zusaetzliche Datei ausser der Messwerkstatt.

## Requirements

`requirements: [MEM-01, MEM-02, MEM-03]` steht im Frontmatter des Plans. Keines
wird hier neu abgehakt:

- **MEM-01** steht bereits seit 14-03 auf Complete (der Schalter samt
  Werksstand und info.xml). Dieser Plan liest ihn nur.
- **MEM-02** verlangt, dass nach Ablauf der Frist beide Halter frei sind, belegt
  an der Rueckkehr zur Grundlast. Beide koennen loslassen, und seit heute gibt es
  die Regel dafuer, aber **niemand ruft sie auf einem Takt**. Der Aufrufer ist
  14-07.
- **MEM-03** verlangt, dass die erste Suche nach einer Entladung innerhalb der
  Decke lexikalisch antwortet und im Hintergrund nachgewaermt wird. Beide
  Haelften sind jetzt gebaut, aber `api/search.py` fragt `query_may_load()` noch
  nicht und ruft `request_warm()` noch nicht. Das ist 14-08.

## Threat Flags

Keine. Die vier Eintraege des Threat-Blocks dieses Plans sind umgesetzt: T-14-19
(Single-Flight, belegt durch den Zehn-Threads-Fall), T-14-20
(Identitaetspruefung mit `is` unter `_LOCK`), T-14-21 (`release_if_idle` und
`warm_wanted` lesen ueber `_held` und nie ueber `shared_model`, je ein Testfall)
und T-14-22 (`WARM_TEXT` als feste Konstante ohne Nutzerinhalt und ohne
Dateinamen, mit eigenem Testfall). T-14-SC: keine neue Abhaengigkeit;
`concurrent.futures` und `ast` sind Stdlib und stehen nur in den Tests.

## Known Stubs

Keine. Alles, was dieser Plan baut, ist vollstaendig und getestet; dass noch
kein Produktivcode die sechs Funktionen ruft, ist die ausgeschriebene Absicht
des Plans (14-07 und 14-08) und kein Stub.

## Gates

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` | gruen |
| `uv run ruff format --check .` | gruen, 122 Dateien |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | gruen |
| `uv run pytest tests/test_embed_engine.py -q` | 52 bestanden |
| `uv run pytest -q` (VOLLE Suite) | **2204 bestanden, 15 uebersprungen**, 178 s |

Kein PHP angefasst, also keine Ersatzpruefung noetig.

## Verification

| Punkt des Plans | Ergebnis |
|---|---|
| 1. Alle vier Gate-Stufen gruen | ja, Tabelle oben |
| 2. Volle Suite gruen | ja, 2204 bestanden |
| 3. `git diff --name-only` nennt genau die zwei Plandateien | plus `tests/test_measurement_scripts.py`, siehe Abweichung 1 |
| 4. `grep -c 'ENGINE_STATES'` unveraendert | 1 vor dem Plan, 1 danach |
| 5. `pytest tests/test_admin_ui_contract.py -q` | 45 bestanden |

Dazu die Abnahmekriterien der drei Tasks: `query_may_load` gibt `bool` und nennt
den 10.09.2026; `embed_idle_release_seconds` steht in genau zwei Dateien;
`release_if_idle` ruft `_held` und nie `shared_model`, prueft mit `is` und ruft
`release()` ausserhalb des Locks (drei Gates am Syntaxbaum); `release_if_idle(0)`
ruft nie `release()` (Spion); `WARM_TEXT` ist eine Modulkonstante ohne
Nutzerinhalt; der Zehn-Threads-Fall belegt genau ein Laden.

## Issues Encountered

Keine. Die beiden Abweichungen oben sind an der Stelle gefunden und behoben
worden, an der sie auftraten.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

14-07 baut den Takt darueber: die dritte Lifespan-Aufgabe, die
`release_if_idle` und `release_cutter` auf einem Takt ruft, beide ueber
`asyncio.to_thread`, und die `busy`-Auskunft des Pollers aus 14-04 liest. Alles,
was sie braucht, steht.

Zwei Hinweise wandern weiter:

- **14-08** muss `query_may_load()` an den drei `SemanticSide`-Stellen fragen
  (ausser `api/diagnose.py`, das bewusst weiter laedt) und nach einer Suche ohne
  Laden `request_warm()` setzen sowie den Warmlauf anstossen. Die Empfehlung des
  Research dafuer ist `asyncio.create_task(asyncio.to_thread(warm))` im async
  Route-Handler.
- **Die Plaene 14-07 bis 14-11 sollten `tests/test_measurement_scripts.py` in
  ihre Dateiliste aufnehmen.** Vier Plaene in Folge haben den Baumhash als
  Abweichung nachgezogen; das ist kein Ausrutscher mehr, sondern eine Luecke in
  der Planvorlage.

## Self-Check: PASSED

- `backend/src/findling/embed/engine.py`: vorhanden, enthaelt `def
  release_if_idle`, `def query_may_load`, `def warm`, `def warm_wanted`, `def
  request_warm`, `def released_count`, `WARM_TEXT`.
- `backend/tests/test_embed_engine.py`: vorhanden, enthaelt `release_if_idle`.
- Alle sieben Commit-Hashes stehen in der Historie.

---
*Phase: 14-modell-entladung-im-leerlauf*
*Completed: 2026-09-19*
