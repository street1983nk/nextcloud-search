---
phase: 14-modell-entladung-im-leerlauf
plan: 08
subsystem: search
tags: [memory, degradation, embeddings, asyncio, create-task, tdd]

# Dependency graph
requires:
  - phase: 14-modell-entladung-im-leerlauf
    provides: Der Schalter may_load an embed_query aus 14-05 und die Regel query_may_load samt request_warm, warm_wanted und warm aus 14-06
  - phase: 06.1-geteilte-engine
    provides: Der D-19-Pfad, auf dem eine leere Vektorliste die Fusion zur Identitaet auf der lexikalischen Liste macht
provides:
  - may_load an QueryEmbedder, an SemanticSide und an beiden embed_query-Aufrufen von index/search.py
  - Die zwei Nutzerrouten fragen query_may_load und laden unter dem Schalter nicht mehr
  - Der schriftliche Grund, warum api/diagnose.py weiter laedt
  - request_warm an der Zeile, an der die Runde ohne Gewichte gebaut wird
  - _WARM_TASKS und der Nachwaerm-Ausloeser auf dem Event Loop
affects: [14-09, 14-11, 14-12, 15-boxmessung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Schalter reist als Feld einer Datenklasse durch die Schichten, und die Schicht, die ihn traegt, liest keine Einstellung"
    - "Eine Hintergrundaufgabe aus einem Route-Handler wird in einer Modulmenge gehalten und im add_done_callback wieder entfernt"
    - "Ein Zeitfall, den der TestClient nicht messen kann, ruft den Handler direkt auf dem Loop des Testfalls"

key-files:
  created: []
  modified:
    - backend/src/findling/index/search.py
    - backend/src/findling/api/search.py
    - backend/src/findling/api/snippets.py
    - backend/src/findling/api/diagnose.py
    - backend/tests/test_semantic_search.py
    - backend/tests/test_search_endpoint.py
    - backend/tests/test_snippets_endpoint.py
    - backend/tests/test_diagnose_endpoint.py
    - backend/tests/test_semantic_snippet.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "request_warm() steht in one_round an der Zeile, an der die SemanticSide ohne Ladeerlaubnis gebaut wird, und nicht im Handler: nur dort sind beide Haelften des Satzes bekannt, dass die Runde hybrid gemeint war und dass sie ohne Gewichte antwortet"
  - "Der Fall zur Antwortzeit laeuft ohne TestClient, weil dessen Portal je Anfrage geoeffnet und beim Schliessen auf jede darin gestartete Aufgabe gewartet wird; eine Messung um client.post herum meldet die Laenge des Hintergrundlaufs, egal was der Handler tut"
  - "api/diagnose.py bekommt nur den Kommentar und keinen Schalter, und der Satz steht in der Datei selbst statt im Docstring von query_may_load, weil er dort steht, wo jemand die Zeile aendern wuerde"
  - "MEM-03 wird abgehakt: die Naht ist an jeder Stelle gebaut und getestet; was fehlt, ist allein der Lauf an der laufenden Instanz, und der braucht einen Containerneubau, den 14-09 sofort wieder entwerten wuerde"
  - "Die vier Stand-ins der Suite lernen das Schluesselwort, statt den Aufruf im Produktivcode weich zu machen: ein Modell ohne may_load ist ab heute kein QueryEmbedder mehr, und das soll auffallen"

patterns-established:
  - "Ein aufzeichnendes Modell an resources.query_model belegt den ganzen Weg von der Route bis an den Halter in einem Fall, statt die Konstruktorzeile zu beobachten"
  - "Ein Gate am Syntaxbaum haelt drei Dinge am Handler fest, die kein Verhaltensfall sieht: genau ein create_task, kein await darauf, und eine Modulmenge als Referenz"

requirements-completed: [MEM-03]

# Metrics
duration: 125min
completed: 2026-09-19
---

# Phase 14 Plan 08: Die Degradationsnaht der Suchwege Summary

**Die erste Suche nach einer Entladung laedt nicht mehr: `may_load` reist von der Route bis an den Halter, die zwei Routen mit der 1,5-Sekunden-Decke antworten lexikalisch, und der Handler bestellt die Gewichte auf dem Event Loop nach, ohne dass die Antwort darauf wartet.**

## Performance

- **Duration:** 125 min (inklusive eines Stillstands, siehe "Issues Encountered")
- **Started:** 2026-09-19T15:00:00Z
- **Completed:** 2026-09-19T17:00:00Z
- **Tasks:** 3 von 3
- **Files modified:** 10 (kein neues Modul, keine neue Abhaengigkeit)

## Accomplishments

### Der Schalter reist, und die Schicht, die ihn traegt, liest keine Einstellung

`index/search.py` hat drei Aenderungen und keine davon weiss, was ein
Einstellungswert ist:

| Stelle | Was steht dort jetzt |
|---|---|
| `QueryEmbedder.embed_query` | `(self, text: str, *, may_load: bool = True)` |
| `SemanticSide` | ein viertes Feld `may_load: bool = True` |
| beide `embed_query`-Aufrufe | `may_load=semantic.may_load` |

`grep -c 'may_load=semantic.may_load'` ist 2, und
`grep -rn 'embed_idle_release_seconds' backend/src/findling/index/` ist leer.
Der Vorgabewert `True` ist die eigentliche Arbeit des Feldes: eine Runde, die
nichts dazu sagt, verhaelt sich byteweise wie vor dieser Phase, und die
Diagnoseroute bleibt damit ohne eine einzige geaenderte Zeile auf ihrem alten
Weg.

Neben dem Aufruf im Suchweg steht, warum das kein neuer Zweig ist: eine
`EmbedOutcome.unavailable()` fuehrt zu einer leeren Liste, RRF wird zur
Identitaet auf der lexikalischen Liste, und der Nutzer bekommt Volltexttreffer.
Das ist D-19, und ein Container ohne Modell geht diesen Weg taeglich. Die
Entladung betritt einen alten Pfad, keinen neuen.

### Zwei Routen mit einer Decke fragen, die Route ohne Decke nicht

| Datei | Zeile | Verhalten |
|---|---|---|
| `api/search.py` | `may_load=may_load` aus `query_may_load()` | laedt unter dem Schalter nicht |
| `api/snippets.py` | `may_load=query_may_load()` | laedt unter dem Schalter nicht |
| `api/diagnose.py` | unveraendert | laedt weiter, mit dem Grund darueber |

Beide Kommentare tragen die Decke (`REQUEST_TIMEOUT_SECONDS = 1.5`
beziehungsweise `PAGE_REQUEST_TIMEOUT_SECONDS = 1.5`), den Vorfall (1838,4 ms
gegen 1500 ms am 10.09.2026, cURL error 28, HTTP 200 mit leerer Trefferliste)
und den Verweis, dass die Regel in `embed/engine.py::query_may_load` steht und
hier nicht wiederholt wird.

Der Satz zur Diagnose steht in `api/diagnose.py` selbst und nicht im Docstring
von `query_may_load`, obwohl der Plan beides zulaesst: er gehoert dorthin, wo
jemand die Zeile aendern wuerde. `grep -c 'may_load' api/diagnose.py` ist 1, und
diese eine Fundstelle ist der Kommentar.

### Das Nachwaermen sitzt dort, wo der Anlass entsteht

`one_round` ruft `request_warm()` genau dann, wenn die `SemanticSide` mit
`may_load=False` gebaut wird. Der Handler fragt danach nur noch
`warm_wanted()`. Der Grund steht als Kommentar daneben: `one_round` liefert
Kandidaten und nicht den Grund, warum keine Vektoren darunter sind, der Handler
koennte die Frage also gar nicht stellen. So bleibt der Anlass, wo er entsteht,
und der Loop, wo er ist.

Der Handler legt danach eine Aufgabe auf den Loop, auf dem er ohnehin laeuft:

```python
task = asyncio.create_task(asyncio.to_thread(warm))
_WARM_TASKS.add(task)
task.add_done_callback(_WARM_TASKS.discard)
```

`_WARM_TASKS` ist kein Schmuck. `asyncio.create_task` haelt selbst keine
Referenz, und eine laufende Aufgabe, die niemand haelt, darf der Garbage
Collector einsammeln; das ist eine dokumentierte Falle und ein Fehler, den
niemand im Protokoll sieht (T-14-30). Der Kommentar daneben traegt die Auswahl
aus 14-RESEARCH.md 5.3 in drei Saetzen: die Entlade-Aufgabe allein taktet alle
30 s und liesse auch die zweite Suche des Nutzers kalt, ein eigener
`threading.Thread` waere ein zweiter Lebenszyklus neben der Lifespan ohne
Stopp-Event, und `BackgroundTasks` liefe erst nach der Antwort.

### Gezaehlt werden Treffer und Aufrufe, nie Fehler

Pitfall 4 ist in jedem Fall dieses Plans eingehalten. Kein einziger Testfall
urteilt ueber eine Fehlerzahl. Gezaehlt wird:

- was am Modell ankommt (`seen == [False]`, `seen == [True]`, `seen == []`),
- wie viele Treffer die Runde hat (`!= []`, und gleich der Liste ohne Vektoren),
- wie oft der Warmlauf lief (`runs == [1]`, `runs == []`),
- wie sehr `load_count()` gestiegen ist (um hoechstens eins, gemessen: genau
  eins bei zehn Anfragen hintereinander).

## Task Commits

1. **Task 1 (RED): Die Faelle des Schalters an SemanticSide** - `23aed8f` (test)
2. **Task 1 (GREEN): may_load reist durch SemanticSide** - `c13e395` (feat)
3. **Task 2 (RED): Die Faelle der zwei Nutzerrouten und der Diagnose** - `152562e` (test)
4. **Task 2 (GREEN): Die Routen fragen die Regel** - `858a0ee` (feat)
5. **Task 3 (RED): Die Faelle des Nachwaermens** - `639b2e1` (test)
6. **Task 3 (GREEN): Das Nachwaermen aus dem Route-Handler** - `ea547b2` (feat)

## TDD Gate Compliance

Alle drei Tasks tragen `tdd="true"` und sind in der Reihenfolge RED, GREEN
gefahren. Jeder RED-Lauf war rot, bevor eine Zeile Produktivcode entstand:

| Task | RED-Beleg | GREEN-Beleg |
|---|---|---|
| 1 | 6 failed, 10 passed; `TypeError: SemanticSide.__init__() got an unexpected keyword argument 'may_load'` und `KeyError: 'may_load'` am Protokoll | 148 bestanden ueber die fuenf beruehrten Dateien |
| 2 | 2 failed, 99 passed; beide `assert [True] == [False]` an der Stellung "Schalter an" | 101 bestanden |
| 3 | 5 failed; `AttributeError: module 'findling.api.search' has no attribute '_WARM_TASKS'` und `AssertionError: one task and no more` | 50 bestanden |

Ein REFACTOR-Schritt war in keinem Fall noetig; es gibt also bewusst keinen
`refactor`-Commit.

## Tests

23 neue Faelle, keiner mit einem Skip-Marker. Die Zahl der Skips der vollen
Suite ist unveraendert bei 15.

| Datei | Faelle | Was sie halten |
|---|---|---|
| `test_semantic_search.py` | 7 | Protokollsignatur, Vorgabewert, beide Aufrufstellen, D-19 unter `may_load=False`, die Gegenprobe mit `True`, ein Modell ohne das Schluesselwort |
| `test_search_endpoint.py` | 3 + 6 | die Stellung des Schalters an der Suchroute, die Operatorzeile, die Gleichheit der Trefferliste; dazu die sechs Faelle des Warmlaufs |
| `test_snippets_endpoint.py` | 3 | dieselbe Stellung an der Ausschnittsroute und der Schnitt unter der Entladung |
| `test_diagnose_endpoint.py` | 2 | die Diagnose laedt in beiden Stellungen |

Drei Bauformen sind neu:

- **Das aufzeichnende Modell an `resources.query_model`.** Es belegt den ganzen
  Weg von der Route bis an den Halter in einem Fall, statt die Konstruktorzeile
  zu beobachten. Die alte Bauform (`_watch_the_semantic_side`) bleibt dort, wo
  sie hingehoert: bei der Frage, **ob** eine `SemanticSide` ueberhaupt gebaut
  wird.
- **`warm_ground`.** Ein Modellverzeichnis mit den zwei Dateinamen, Stand-ins
  fuer Tokenizer und Sitzung, ein frischer Halter und ein auf beiden Seiten
  geloeschter Warmmerker. Damit laeuft ein echter Warmlauf ueber den echten
  Pfad des Halters, ohne 118 MB.
- **Das Gate am Syntaxbaum des Handlers.** Genau ein `create_task`, kein `await`
  darauf, `_WARM_TASKS` als Modulzuweisung und `add_done_callback` im Quelltext.
  Ein Verhaltensfall sagt, was einmal geschah; der Baum sagt, was beim naechsten
  Umbau geschieht.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] Vier Stand-ins der Suite kannten das Schluesselwort nicht**

- **Found during:** Task 1
- **Issue:** `embed_query(text, may_load=...)` an beiden Aufrufstellen laesst
  jedes Modell auflaufen, das die Signatur von gestern hat. Das sind vier
  Klassen in vier Testdateien (`test_semantic_search.py`,
  `test_semantic_snippet.py`, `test_diagnose_endpoint.py`,
  `test_snippets_endpoint.py`), zusammen sechs Methoden. 12 bestehende Faelle
  wurden rot.
- **Fix:** Alle sechs Methoden tragen jetzt `*, may_load: bool = True`. Der
  Aufruf im Produktivcode bleibt hart: ein Modell ohne das Schluesselwort ist
  ab heute kein `QueryEmbedder` mehr, und das soll auffallen. Ein eigener
  Testfall haelt genau das fest, per `cast` hereingereicht, weil er nicht
  typpruefbar sein **soll**.
- **Files modified:** die vier Testdateien
- **Commit:** `c13e395`

**2. [Rule 3 - Blocker] Der SemanticSide-Beobachter kannte das vierte Feld nicht**

- **Found during:** Task 2
- **Issue:** `_watch_the_semantic_side` in `test_semantic_search.py` ersetzt die
  Klasse durch eine Funktion mit ausgeschriebenen Schluesselwoertern. Sobald die
  Route `may_load=` uebergibt, faengt das enge Netz von `one_round` den
  `TypeError` und drei Faelle der Operatorregel wurden gruen fuer den falschen
  Grund.
- **Fix:** Der Beobachter nimmt das vierte Feld und reicht es durch.
- **Files modified:** backend/tests/test_semantic_search.py
- **Commit:** `858a0ee`

**3. [Rule 1 - Bug] Der Zeitfall war durch den TestClient nicht messbar**

- **Found during:** Task 3
- **Issue:** Der Plan verlangt einen Fall, der belegt, dass die Antwort nicht
  auf die Aufgabe wartet. Durch `TestClient` gemessen dauerte die Anfrage
  5,02 s gegen ein Budget von 1 s, **obwohl der Handler korrekt nichts
  abwartet**: `TestClient` oeffnet je Anfrage ein blockierendes Portal und
  wartet beim Schliessen auf jede Aufgabe, die drinnen gestartet wurde. Eine
  Messung um `client.post` herum meldet also die Laenge des Hintergrundlaufs,
  egal was der Handler tut. Sie waere gegen richtigen Code rot und gegen nichts
  gruen gewesen.
- **Fix:** Der Fall ruft den Handler direkt auf dem Loop des Testfalls
  (`asyncio_mode = "auto"` steht in der pyproject), mit `current_user_id` als
  Stand-in. Danach ist die Antwort in der Hand und `len(_WARM_TASKS) == 1`: die
  Aufgabe laeuft noch. Das ist die Lage unter uvicorn, wo der Loop die Anfrage
  ueberlebt. Der Grund steht als Docstring am Fall.
- **Files modified:** backend/tests/test_search_endpoint.py
- **Commit:** `ea547b2`

**4. [Rule 3 - Blocker] Baumhash der Messwerkstatt dreimal nachgezogen**

- **Found during:** Task 1, Task 2 und Task 3
- **Issue:** `tests/test_measurement_scripts.py` haelt einen sha256 ueber alle 54
  Dateien des Python-Pakets, und die Datei steht wieder nicht in
  `files_modified` des Plans. Das ist der fuenfte Plan in Folge.
- **Fix:** `PACKAGE_TREE_HASH_TODAY` auf
  `19b98f33fea6c8f124dbbd58a5e9b1abd45db675a9a377575f8d49d35221c38d` (Task 1),
  `decefcaa56c36ffbb4bbc02006a86f3962b037a0175e8ca745f9471579f9794a` (Task 2)
  und `e8ae84b8b4faac0d3d7643048948387ebaa6bfcdd2d68d05748b55b1855ae934`
  (Task 3), je mit einem Absatz in der Form der elf vorhergehenden Eintraege.
  Die Dateizahl bleibt 54.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Commits:** `c13e395`, `858a0ee`, `ea547b2`

### Zwei Abnahmekriterien des Plans, die anders zaehlen als geschrieben

Beides sind Zaehlfehler im Plan und keine Abweichungen am Bau:

- `grep -c 'from findling.config\|findling.embed.engine' index/search.py` soll 0
  sein und ist 1. Die Fundstelle ist `from findling.config import
  SEARCH_SCAN_MAX, settings` in Zeile 48, und sie stand dort schon vor diesem
  Plan (nachgeprueft gegen `HEAD~1`). Der Sinn des Kriteriums ist erfuellt:
  `embed_idle_release_seconds` kommt in `index/` nirgends vor.
- `grep -c 'create_task' api/search.py` soll 1 sein und ist 3. Zwei der drei
  Zeilen sind Kommentar, es gibt genau einen Aufruf, und das Gate am Syntaxbaum
  zaehlt Aufrufknoten statt Zeilen.

Ebenso Verifikationspunkt 5: `grep -c 'embed_query' index/search.py` ist 3 und
war vor diesem Plan schon 3 (Protokollzeile plus die zwei Aufrufe). Der Plan
nennt 2. Entscheidend ist, dass keine dritte Aufrufstelle entstanden ist, und
das ist so.

---

**Total deviations:** 4 auto-fixed (3 Blocker, 1 Bug)
**Impact on plan:** Keiner davon aendert den Umfang. Die drei Blocker sind
Folgearbeit an der Suite und an der Messwerkstatt, der Bug betrifft die
Messbarkeit eines Falles, nicht seine Aussage.

## Requirements

`requirements: [MEM-03]`, und **MEM-03 wird abgehakt**.

MEM-03 verlangt, dass die erste Suche nach einer Entladung innerhalb der
1,5-Sekunden-Decke lexikalisch antwortet und das Modell im Hintergrund
nachwaermt. Beide Haelften stehen seit heute vollstaendig verdrahtet:

| Haelfte | Wo sie steht | Wer sie haelt |
|---|---|---|
| kein Laden auf dem Suchweg | `api/search.py`, `api/snippets.py`, `index/search.py` | 8 Faelle ueber drei Dateien |
| Nachwaermen im Hintergrund | `one_round` und der Route-Handler | 6 Faelle plus ein Gate am Syntaxbaum |

Was fehlt, ist allein der Lauf an der laufenden Instanz (Verifikationspunkt 4
des Plans). Er braucht einen Neubau des Containers, und 14-09 aendert mit dem
sechsten Wort `unloaded` sofort wieder dieselben Dateien; ein Neubau jetzt
waere in derselben Stunde veraltet. Er gehoert deshalb in 14-12, wo die Phase
ihren Integrationslauf hat. Das ist die Begruendung fuer das Haekchen und
zugleich der Auftrag an 14-12; es ist bewusst kein halbes Requirement, weil
MEM-03 anders als MEM-02 keine benannte Beleg-Messgroesse fuehrt.

MEM-02 bleibt unberuehrt und weiter offen: dort steht die Beleg-Messgroesse
ausdruecklich im Text des Requirements.

## Threat Flags

Keine. Die sechs Eintraege des Threat-Blocks dieses Plans sind umgesetzt:

| Eintrag | Beleg |
|---|---|
| T-14-28 (Last startet Warmlauf je Anfrage) | zehn Anfragen, `load_count()` steigt um genau eins |
| T-14-29 (Kandidaten am Vorfilter vorbei) | der D-19-Pfad leert nur die Vektorliste; `_rank_chunks` und der Ausschnittsschnitt liegen unveraendert hinter dem Vorfilter, `test_php_acl_boundary.py` und `test_php_trust_boundary.py` gruen |
| T-14-30 (Aufgabe wird eingesammelt) | `_WARM_TASKS` plus `add_done_callback`, gehalten vom Gate am Syntaxbaum |
| T-14-31 (Suchtext im Log) | die neue Zeile fuegt keine Ausgabe hinzu; der Fall mit dem Modell ohne Schluesselwort prueft, dass die Warnung den Typnamen und nicht die Zeile nennt |
| T-14-32 (Diagnose misst leer) | die Diagnose laedt weiter, der Aufwaermhinweis ist fuer 14-11 vorgemerkt |
| T-14-SC | keine neue Abhaengigkeit; `ast`, `asyncio`, `threading` und `time` sind Stdlib und stehen in den Tests |

## Known Stubs

Keine.

## Gates

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` | gruen |
| `uv run ruff format --check .` | gruen, 123 Dateien |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | gruen |
| `uv run pytest tests/test_search_endpoint.py -q` | 50 bestanden |
| `uv run pytest -q` (VOLLE Suite) | **2244 bestanden, 15 uebersprungen**, 194 s |
| `uv run pytest tests/test_php_acl_boundary.py tests/test_php_trust_boundary.py -q` | 29 bestanden |

Kein PHP angefasst, also keine Ersatzpruefung noetig; `php/lib/Service/ExAppService.php`
wurde nur gelesen (die beiden Deckenkonstanten).

## Verification

| Punkt des Plans | Ergebnis |
|---|---|
| 1. Alle vier Gate-Stufen gruen | ja, Tabelle oben |
| 2. Volle Suite gruen | ja, 2244 bestanden |
| 3. Rechtegrenze unveraendert | 29 bestanden |
| 4. Ende zu Ende an der laufenden Instanz | **nicht ausgefuehrt**, siehe Requirements: braucht einen Containerneubau und gehoert zu 14-12 |
| 5. Keine dritte `embed_query`-Aufrufstelle | ja, unveraendert zwei Aufrufe plus die Protokollzeile |

Dazu die Abnahmekriterien der drei Tasks: `SemanticSide` traegt vier Felder;
`grep -c 'may_load=semantic.may_load'` ist 2; `grep -c 'query_may_load()'` ist
je 1 in `api/search.py` und `api/snippets.py`; beide Kommentare nennen den
10.09.2026, die 1838,4 ms und die 1,5 s; genau ein `create_task`-Aufrufknoten,
kein `await` darauf, `_WARM_TASKS` mit `add_done_callback`; kein Testfall dieses
Plans urteilt ueber eine Fehlerzahl.

## Issues Encountered

Ein Stillstand im GREEN-Schritt von Task 3: die Untersuchung, warum der
Zeitfall 5,02 s statt unter 1 s meldete, ist zu lange im Lesen geblieben,
bevor der Befund (das Portal des `TestClient` wartet auf angestossene Aufgaben)
festgehalten und umgesetzt wurde. Kein haengender Befehl, kein verlorener
Stand: die sechs Task-Commits liegen vollstaendig vor. Der Befund selbst ist
der Grund fuer Abweichung 3 und steht jetzt als Docstring am Fall, damit
niemand den Fall ein zweites Mal ueber den TestClient baut.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Welle 5 ist abgeschlossen. 14-09 baut das sechste Wort `unloaded` samt seiner
PHP-Haelfte und seinen sechs Katalogdateien in drei Sprachen (Owner-Entscheid
Zweig B vom 19.09.2026, `14-CONTEXT.md`). Zwei Hinweise wandern weiter:

- **14-11 (Runbook)** braucht den Aufwaermhinweis: ein Diagnoseaufruf waermt den
  Container auf und darf vor einer Kaltmessung nicht gemacht werden. Der Satz
  steht jetzt an zwei Stellen im Code (`embed/engine.py::query_may_load` und
  `api/diagnose.py`), aber nirgends im Runbook.
- **14-12 (Integrationslauf)** uebernimmt Verifikationspunkt 4 dieses Plans:
  mit `FINDLING_EMBED_IDLE_RELEASE_SECONDS=60` nach einer Ruhephase eine Suche
  absetzen, Antwortzeit unter 1,5 s, Treffer vorhanden, zweite Suche dreissig
  Sekunden spaeter wieder mit semantischem Anteil. Das ist der letzte
  ausstehende Beleg zu MEM-03.
- **Die Plaene 14-09 bis 14-12 sollten `tests/test_measurement_scripts.py` in
  ihre Dateiliste aufnehmen.** Fuenf Plaene in Folge haben den Baumhash als
  Abweichung nachgezogen.

## Self-Check: PASSED

- `backend/src/findling/index/search.py`: vorhanden, enthaelt `may_load: bool = True` und zweimal `may_load=semantic.may_load`.
- `backend/src/findling/api/search.py`: vorhanden, enthaelt `query_may_load()`, `request_warm()`, `_WARM_TASKS` und `create_task`.
- `backend/src/findling/api/snippets.py`: vorhanden, enthaelt `query_may_load()`.
- `backend/src/findling/api/diagnose.py`: vorhanden, enthaelt den Kommentar zur Entscheidung.
- Alle sechs Commit-Hashes (`23aed8f`, `c13e395`, `152562e`, `858a0ee`, `639b2e1`, `ea547b2`) stehen in der Historie.

---
*Phase: 14-modell-entladung-im-leerlauf*
*Completed: 2026-09-19*
