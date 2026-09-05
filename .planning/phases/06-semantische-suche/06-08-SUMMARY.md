---
phase: 06-semantische-suche
plan: 08
subsystem: backend
tags: [snippet, d-13, confused-deputy, zeichen-statt-bytes, vierte-operation, abstraktionsschnitt, degradieren]

# Dependency graph
requires:
  - phase: 06-semantische-suche
    provides: "06-04: store/vectors.py, die Zeichen-Offsets neben jedem Vektor und die Bandung zu 1000"
  - phase: 06-semantische-suche
    provides: "06-05: embed_query, EmbedOutcome.available und to_int8"
  - phase: 06-semantische-suche
    provides: "06-06: SemanticSide, QueryEmbedder und resources.query_model als die Herkunft des Modells der Leseseite"
  - phase: 06-semantische-suche
    provides: "06-07: die Zweitspur, die den Bestand ueberhaupt erst fuellt"
  - phase: 02-store-und-index
    provides: "snippets_for mit prefilter_visible als erster Handlung, char_ranges und die gemessene Byte-gegen-Zeichen-Abweichung"
provides:
  - "store/vectors.py::best_chunk_for, die vierte Operation: gegebene Dateien, ihr bester Chunk"
  - "store/vectors.py::BestChunk, drei Zahlen und kein Abstand"
  - "store/vectors.py::VectorStore.trace, der Beleg fuer Bandung und fuer die nicht gestellte Abfrage"
  - "store/vectors.py::_DISTANCE_EXPRESSION, die Metrik des Bestands als eine Zeile"
  - "index/search.py::_rank_chunks und _passage_of, der zweite Ausschnittsweg"
  - "index/search.py::snippets_for mit dem Schluesselwortparameter semantic"
  - "api/snippets.py: die Route reicht den rohen Anfragetext und den Vektorbestand weiter"
affects: [06-09 Statusseite und Diagnose, 06-10 Gates, 06-11 Lasttest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Frage an den Vektorbestand wird in der Richtung gestellt, in der der Vorfilter fragt: gegebene Kandidaten, welche davon passen, nie der ganze Bestand mit einem Filter dahinter"
    - "Wo eine Metrik ausserhalb der Engine gerechnet werden muss, steht sie als eine benannte Zeile, damit der Wechsel des Spaltentyps eine Zeile bleibt"
    - "Ein zweiter Weg zu demselben Ausgabewert entsteht im Rumpf der bestehenden Schleife, damit er die Pruefungen davor erbt statt sie erneut zu brauchen"
    - "Ein optionales Buendel ist der Ausfallpfad und der Normalzustand einer Installation ohne die Funktion, in einem Parameter"

key-files:
  created:
    - backend/tests/test_semantic_snippet.py
  modified:
    - backend/src/findling/store/vectors.py
    - backend/src/findling/index/search.py
    - backend/src/findling/api/snippets.py
    - backend/tests/test_snippets_endpoint.py
    - .planning/phases/06-semantische-suche/deferred-items.md

key-decisions:
  - "best_chunk_for ist keine KNN-Abfrage und kann keine sein: k ist eine Bedingung der vec0-Tabelle ueber den ganzen Bestand, also waere ein nachtraeglich gefiltertes KNN wieder die umgekehrte Richtung und wuerde ausserdem weniger Dokumente beantworten als gefragt wurden"
  - "Die Metrik steht als _DISTANCE_EXPRESSION (vec_distance_l2) in einer Zeile, weil best_chunk_for sie im Gegensatz zu nearest nicht von vec0 waehlen lassen kann; am 05.09.2026 gegen dieses Schema geprueft, beide Wege liefern dieselben Zahlen"
  - "BestChunk traegt weder Abstand noch chunk_id: beide haben keinen Leser, und ein Abstand waere eine Aussage darueber, wie gut ein Dokument gepasst hat (D-14)"
  - "snippets_for bekommt EINEN Parameter (semantic: SemanticSide | None) statt der zwei des Plans, weil ohne Modell nichts eingebettet werden kann und das Buendel aus 06-06 genau die drei Angaben traegt"
  - "Der Anfragevektor entsteht erst, nachdem der Vorfilter geantwortet hat: die Einbettung ist Arbeit, und Arbeit fuer abgelehnte Dokumente ist der Anfang eines Confused Deputy"
  - "Die Schleife laeuft ab jetzt ueber die bestaetigte Liste statt ueber alle gefragten ids mit einem continue darin, damit sichtbar ist, dass alles darunter bestaetigt ist"
  - "Der zweite Ausschnitt wird auf snippet_chars ZEICHEN gekuerzt, obwohl set_max_num_chars Bytes vergleicht; die Abweichung geht in die harmlose Richtung und steht als Kommentar an der Stelle"
  - "VectorStore.trace kommt dazu, nach dem Vorbild von Store.trace: die Bandung und die nicht gestellte Abfrage sind Eigenschaften des Aufrufmusters und im Ergebnis unsichtbar"

patterns-established:
  - "Ein Testfall, der eine Reihenfolge behauptet, belegt sie ueber Attrappen, die mitschreiben, statt ueber ein Ergebnis, das bei falscher Reihenfolge gleich aussaehe"
  - "Zu jedem semantischen Ausschnittsfall gehoert ein Bodenfall, der belegt, dass die Zeile lexikalisch nichts trifft"

requirements-completed: [SEM-01]

# Metrics
duration: 16min
completed: 2026-09-05
---

# Phase 6 Plan 08: Der Ausschnitt rein semantischer Treffer Summary

**Ein Treffer, den nur die Semantik gefunden hat, zeigt jetzt die Stelle, die gepasst hat: geschnitten aus dem gespeicherten body_de zwischen den zwei Zeichen-Offsets seines Rang-Chunks, ohne Markierungen, weil es nichts zu markieren gibt, und erst nachdem derselbe Vorfilter und derselbe PHP-Recheck ihn bestaetigt haben wie jeden anderen Ausschnitt. Faellt der Vektorzweig aus, ist das Verhalten Element fuer Element das von vorher.**

## Performance

- **Duration:** rund 16 min
- **Started:** 2026-09-05T08:32:39Z
- **Completed:** 2026-09-05T08:48:00Z
- **Tasks:** 2 von 2
- **Files modified:** 6 (1 neu, 5 geaendert)
- **Tests:** 1.312 bestanden, 13 uebersprungen (vorher 1.286), also 26 neue Faelle

## Accomplishments

- **Die Richtung ist die Aussage, und sie ist als Fall belegt.** `best_chunk_for` fragt so, wie `prefilter_visible` fragt: gegebene Dateien, welcher ihrer Chunks passt am besten. Ein Fall legt einen Chunk, der exakt auf dem Anfragevektor sitzt, in eine Datei, nach der nicht gefragt wurde, und verlangt, dass die Antwort ihn nicht kennt. Der umgekehrte Weg waere nicht nur teurer gewesen, er waere falsch: `k` ist eine Bedingung der vec0-Tabelle ueber den ganzen Bestand, also haette ein nachtraeglich gefiltertes KNN fuer eine Seite bestaetigter Treffer regelmaessig weniger Dokumente beantwortet als gefragt wurden.
- **Die Reihenfolge ist ueber Attrappen belegt und nicht ueber ein Ergebnis.** Ein Ausschnittsweg, der zuerst den Vektorbestand fragt und die abgelehnten Dokumente danach wegwirft, liefert dieselbe Antwort und hat den Text trotzdem gelesen. Zwei Faelle schreiben deshalb mit, wonach `best_chunk_for` und `_document_for` gefragt wurden: die abgelehnte Datei steht in keiner der beiden Listen, und ein Nutzer, dem der Vorfilter alles verweigert, loest gar keine Chunkfrage aus (T-06-37, T-06-38).
- **Zeichen statt Bytes ist an zwei Alphabeten geprueft.** Vor der deutschen Passage stehen zehn Umlaute, vor der franzoesischen ein Akzent und eine Cedille. Ein Schnitt auf Bytes haette den deutschen Ausschnitt zehn Zeichen zu weit rechts begonnen und waere in den Nachsatz gelaufen; der Fall haelt zusaetzlich fest, dass die zwei Konventionen an dieser Stelle wirklich auseinanderlaufen (T-06-40).
- **Der Ausfall kostet die Semantik und nie die Antwort.** Ohne Buendel, ohne Modell, mit einem Modell, das das ehrliche Verdikt gibt, und mit einem Modell, das kracht: vier Wege in dieselbe leere Chunkabbildung, und die Funktion verhaelt sich dann Element fuer Element wie vor diesem Plan. Der krachende Zweig traegt den Anfragetext in seiner Ausnahmemeldung, damit die Log-Zusicherung etwas zu verlieren hat (T-06-39).
- **`grep -c 'prefilter_visible'` ist weiterhin 2.** Der zweite Ausschnittsweg liegt im Rumpf derselben Schleife wie der erste und erbt die eine Pruefung, statt eine zweite zu brauchen.

## Task Commits

1. **Task 1 (RED): Das Gatter ueber best_chunk_for und der Richtung, in der es fragt** - `3d82e3e` (test)
2. **Task 1 (GREEN): best_chunk_for, die vierte Operation des Vektorspeichers** - `dcf8c63` (feat)
3. **Task 2 (RED): Das Gatter ueber dem zweiten Ausschnittsweg und seiner Reihenfolge** - `13a6adb` (test)
4. **Task 2 (GREEN): Der zweite Ausschnittsweg, hinter dem Vorfilter und dem Recheck** - `ac7e2db` (feat)
5. **Der Zeiger von DI-06-03 auf den Plan, der den Deckungsgrad wirklich rechnet** - `f747ae2` (docs)

## Files Created/Modified

- `backend/tests/test_semantic_snippet.py` - 23 Faelle gegen einen echten Vektorspeicher, einen echten Index und eine echte Zustandsdatenbank; die einzigen Attrappen sind das Modell und die zwei mitschreibenden Umhuellungen der Reihenfolgefaelle
- `backend/src/findling/store/vectors.py` - `BestChunk`, `best_chunk_for`, `trace`, `_DISTANCE_EXPRESSION` und ein Modulkopf, der von vier Operationen spricht und begruendet, warum die vierte keine eigene Datei bekommt
- `backend/src/findling/index/search.py` - `_rank_chunks`, `_passage_of`, der Schluesselwortparameter `semantic` an `snippets_for`, die Schleife ueber die bestaetigte Liste und der Absatz zum Confused Deputy mit dem Satz zum zweiten Weg
- `backend/src/findling/api/snippets.py` - das Buendel aus Vektorbestand, Modell und rohem Text, ein Kopfabsatz zum zweiten Ausschnittsweg und sonst nichts
- `backend/tests/test_snippets_endpoint.py` - drei Faelle ueber die Route: der Bodenfall, die Verdrahtung Ende zu Ende und der Rechtefall am zweiten Weg
- `.planning/phases/06-semantische-suche/deferred-items.md` - der berichtigte Zeiger von DI-06-03

## Wie der Rang-Chunk gefunden wird, und warum nicht mit einem KNN

| Weg | Was er tut | Warum nicht |
|---|---|---|
| KNN ueber den Bestand, danach filtern | `nearest(vector, k)` und dann auf die bestaetigten ids reduzieren | `k` gilt fuer den ganzen Bestand, also fehlen bestaetigte Dokumente, sobald mehr als `k` Chunks naeher liegen; ausserdem Rechenzeit fuer Dokumente, die der Recheck abgelehnt hat |
| Rang-Chunk aus `candidates()` mitreichen | die `chunk_id` aus `documents_from_chunks` weitergeben | eine vierte Angabe an `Candidate`, also eine Aussage ueber ein Dokument, das der Recheck noch nicht bestaetigt hatte (D-14) |
| **gewaehlt:** Abstand je Zeile ueber die genannten Dateien | `vec_distance_l2` ueber die Chunks der bestaetigten Dokumente, kleinster gewinnt | dieselbe Richtung wie der Vorfilter, dieselbe Metrik wie die KNN-Abfrage, Preis ist eine Einbettung der kurzen Anfrage je Snippet-Aufruf (T-06-41, akzeptiert) |

## Decisions Made

- **`best_chunk_for` rechnet den Abstand selbst, und deshalb steht die Metrik als benannte Zeile da.** `nearest` laesst vec0 die Metrik waehlen: eine `int8[384]`-Spalte rankt unter der Vorgabemetrik, und das Modul muss sie nicht kennen. Sobald der Abstand je Zeile gebraucht wird, muss er sie nennen. `_DISTANCE_EXPRESSION` ist diese eine Zeile, mit dem Beleg daneben, dass beide Wege am 05.09.2026 gegen dieses Schema dieselben Zahlen liefern, und mit dem Hinweis, dass sie bei einem Wechsel auf `bit[384]` zu `vec_distance_hamming` wird. Zwei Wege mit zwei Metriken waeren die Sorte Fehler, die nie auffaellt: das Dokument steht richtig in der Liste und zeigt die falsche Stelle.
- **`snippets_for` bekommt einen Parameter und nicht zwei.** Der Plan nennt "den Vektorspeicher und den rohen Anfragetext". Mit diesen beiden allein kann nichts eingebettet werden, und die zwei Alternativen zur Herkunft des Modells hat 06-06 fuer die Leseseite bereits verworfen (ein Modul-Singleton in der Indexschicht oder ein Import aus der API-Schicht). `SemanticSide` traegt genau die drei Angaben, wird in `api/snippets.py` gebaut wie in `api/search.py::one_round`, und "fehlt einer von beiden" ist damit `semantic is None`, also derselbe Zustand wie eine Installation ohne Semantik.
- **Die Einbettung passiert nach dem Vorfilter, nicht davor.** Naheliegend waere gewesen, den Anfragevektor gleich am Anfang zu rechnen, weil er von den Dateien nicht abhaengt. Er ist aber Arbeit, und Arbeit fuer Dokumente, die gleich abgelehnt werden, ist der erste Schritt zu genau dem Muster, das dieser Pfad nicht sein darf. Die Kosten sind ausserdem asymmetrisch: der Vorfilter kostet gemessen 0,2 ms, eine Einbettung ein Vielfaches davon.
- **Die Schleife laeuft ueber die bestaetigte Liste.** Vorher lief sie ueber alle gefragten ids mit einem `continue` fuer die abgelehnten. Beides ist funktional gleich, aber die neue Form macht die Zusicherung sichtbar: `confirmed` entsteht direkt unter dem Vorfilter, wird an `_rank_chunks` gereicht und traegt die Schleife, also gibt es unterhalb dieser Zeile keinen Zweig mehr, der eine nicht bestaetigte id sehen koennte.
- **`BestChunk` traegt drei Zahlen und keinen Abstand.** Ein Abstand haette einen Leser gebraucht und keinen gehabt. Er waere ausserdem eine Aussage darueber, wie gut ein Dokument gepasst hat, und dieses Projekt haelt solche Zahlen aus allem heraus, was den Container verlaesst (D-14). Ein Test prueft die Feldmenge, so wie er es fuer `Neighbour` tut.
- **Der zweite Ausschnitt wird in Zeichen gekuerzt, der erste in Bytes.** `set_max_num_chars` vergleicht trotz seines Namens Bytes im Fragmenter. Beide auf dieselbe Zahl zu setzen ist trotzdem richtig: es ist die eine Groesse, die ein Betreiber stellt, und die Abweichung geht in die harmlose Richtung, weil ein Ausschnitt dieses Weges nie mehr Zeichen hat als die gesetzte Zahl. Der Unterschied steht als Kommentar an `_passage_of`, damit niemand ihn spaeter fuer einen Fehler haelt.
- **`VectorStore.trace` ist dazugekommen.** Zwei Eigenschaften von `best_chunk_for` sind im Ergebnis unsichtbar: dass eine leere Dateiliste keine Abfrage stellt und dass eine lange in Baender zerfaellt. `Store.trace` existiert seit Phase 2 aus genau diesem Grund fuer `prefilter_visible`, und die zweite Datenbank bekommt denselben Beleg statt einer Vermutung.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktion] Zwei Parameter koennen nichts einbetten**

- **Found during:** Task 2, beim Entwurf der Signatur
- **Issue:** Der Plan verlangt "zwei zusaetzliche Schluesselwortparameter: den Vektorspeicher und den rohen Anfragetext". Der Ablauf, den derselbe Plan vorschreibt, verlangt in Schritt 2 "den Anfragetext einbetten", und dafuer gibt es in beiden Parametern keine Herkunft. `snippets_for` haette sich das Modell selbst besorgen muessen, also aus einem Modul-Singleton in der Indexschicht (verborgener Prozesszustand, in einer Suite nicht ersetzbar) oder ueber einen Import aus der API-Schicht (eine Kante von der Indexschicht nach oben). Beides hat 06-06 fuer dieselbe Frage schon verworfen.
- **Fix:** Ein Parameter, `semantic: SemanticSide | None`, also genau das Buendel, das `candidates()` seit 06-06 nimmt und das den Vektorspeicher, das Modell und den rohen Text traegt. Gebaut wird es in `api/snippets.py` nach dem Muster von `api/search.py::one_round`, aus `side.vectors` und `resources.query_model()`.
- **Files modified:** backend/src/findling/index/search.py, backend/src/findling/api/snippets.py
- **Verification:** `test_without_the_vector_half_the_answer_is_what_it_was_before_this_plan` vergleicht den Aufruf ohne Parameter mit dem Aufruf mit `semantic=None` und mit dem Stand von vorher; die drei Endpunktfaelle belegen die Verdrahtung ueber die Route.
- **Committed in:** `ac7e2db`

**2. [Rule 2 - Fehlende kritische Funktion] Ohne trace waeren zwei Abnahmekriterien nicht belegbar gewesen**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt einen Fall, der die Bandung ueber den Trace zaehlt, "wie in test_store_repo.py fuer prefilter_visible", und einen Fall, der belegt, dass eine leere Dateiliste keine Abfrage ausloest. `Store` hat dafuer seit Phase 2 die Methode `trace`; `VectorStore` hatte keine, und ein Test haette entweder die private Verbindung angefasst oder die Eigenschaft nur behauptet.
- **Fix:** `VectorStore.trace(callback)`, wortgleich zu `Store.trace`, mit dem Grund im Docstring.
- **Files modified:** backend/src/findling/store/vectors.py
- **Verification:** `test_best_chunk_for_bands_long_id_lists` zaehlt drei SELECT-Anweisungen fuer 2.500 ids, `test_best_chunk_for_without_file_ids_asks_nothing` zaehlt null Anweisungen.
- **Committed in:** `dcf8c63`

### Abweichungen, die keine Autoreparatur sind, sondern eine Auslegung des Plans

**3. Der Schnitt liest den Text aus dem Dokument, das die Schleife schon haelt**

Der Plan sagt: "Der Schnitt aus dem gespeicherten Text folgt writer.stored_body,
das den body_de-Wert bereits genau so ausliest." `stored_body` lebt auf dem
`IndexBatchWriter`, den die Leseseite nicht hat und nicht haben soll: die
Methode oeffnet einen Schreibpfad, macht ein `reload` und sucht das Dokument
selbst. `snippets_for` haelt das Dokument an dieser Stelle bereits in der Hand,
weil `_document_for` es fuer den Generator geholt hat. `_passage_of` liest
daraus denselben Wert auf demselben Weg (`to_dict().get(FIELD_BODY_DE)`), also
folgt es `stored_body` in der Form und nicht im Aufruf, und spart eine zweite
Suche je Ausschnitt.

**4. `test_snippets_endpoint.py` bekommt drei Faelle, die der Plan nicht nennt**

Die Dateiliste des Plans fuehrt die Datei, das Abnahmekriterium nennt aber nur
"die bestehenden Suiten bleiben gruen". Ohne einen Fall ueber die Route waere
die Verdrahtung von `api/snippets.py` von keinem Test beruehrt gewesen: die
Bibliotheksfaelle uebergeben das Buendel selbst. Die drei Faelle sind der
Bodenfall (die Zeile trifft lexikalisch nichts), die Verdrahtung Ende zu Ende
(mit `resources.query_model` als der einen ersetzten Stelle) und der Rechtefall
am zweiten Weg.

**5. Ein Fall des Plans ist enger gefasst worden, als er dasteht**

Das Abnahmekriterium "ein Test belegt: ohne Vektorspeicher und ohne Modell
verhaelt sich snippets_for exakt wie vor diesem Plan, Element fuer Element" ist
zusaetzlich in der Gegenrichtung gebaut: `test_a_fragment_that_is_not_empty_is_left_exactly_as_it_was`
faehrt dasselbe Dokument MIT Buendel und mit einem Chunk und verlangt dieselbe
Antwort, weil der erste Weg ein nicht leeres Fragment geliefert hat. Der erste
Entwurf dieses Falls hat zwei Dokumente verglichen und war rot, und zwar aus dem
richtigen Grund: das zweite Dokument enthaelt die Zeile nicht, sein Fragment ist
leer, und der neue Weg hat es korrekt gefuellt. Der Fall prueft jetzt genau das
Dokument, in dem beide Wege haetten antworten koennen.

**6. `deferred-items.md` ist nicht in der Dateiliste des Plans**

DI-06-03 wies seine Schliessform woertlich "Plan 06-08" zu, uebernommen aus den
Zusammenfassungen von 06-06 und 06-07, die die Statusseite unter dieser Nummer
fuehren. Plan 06-08 ist der Ausschnittsplan und rechnet keinen Deckungsgrad; die
Statusseite ist 06-09. Der Zeiger ist berichtigt und mit einem Nachtrag
versehen, der ausdruecklich sagt, dass DI-06-02 und DI-06-03 hier **nicht**
geschlossen sind. Ohne diese Zeile haette der naechste Leser eine Zusage
gefunden, die dieser Plan nie hatte.

---

**Total deviations:** 2 autorepariert (beide fehlende kritische Funktionen), 4 Auslegungen
**Impact on plan:** Keine Ausweitung des Umfangs. Beide Autoreparaturen betreffen die Belegbarkeit dessen, was dieser Plan zusichert: dass der Ausschnitt ueberhaupt entstehen kann, und dass die zwei unsichtbaren Eigenschaften des Aufrufmusters gemessen statt behauptet werden.

## Issues Encountered

- **Der erste Entwurf des Vergleichsfalls war rot, und das war die richtige Antwort auf die falsche Frage.** Siehe Auslegung 5.
- **Ein Fall der Endpunktsuite laesst sich nur ueber `resources.query_model` bauen.** Der Container baut sein Modell selbst, und auf einer Entwicklungsmaschine gibt es das Artefakt nicht, also antwortet der echte Wrapper mit `embedding_unavailable` und der zweite Weg liefe nie. Ersetzt ist genau diese eine Funktion; der Vektorbestand, der Index, die Zustandsdatenbank und die Route sind echt.
- **Die AWS-Box ist nicht angefasst worden.** Dieser Plan misst nichts. Die einzige neue Messung ist eine Gegenprobe am eigenen Schema (die Abstaende von `nearest` und von `vec_distance_l2` sind dieselben Zahlen), lokal gefahren, und sie steht als Kommentar an der Konstante.

## Offene Verifikation

Keine. Alle Gates sind lokal gruen gelaufen: `pytest` mit 1.312 bestandenen und
13 uebersprungenen Tests, `ruff check . --no-cache`, `ruff format --check .`,
`pyright` mit 0 Fehlern und `vulture` ohne Befund, jeweils im CI-Umfang
`backend`. Dazu die Zusicherungen aus der Verifikationszeile des Plans:
`grep -c 'prefilter_visible'` ergibt 2 in `index/search.py`,
`git diff --stat php/` ist leer, und weder Geviert- noch Halbgeviertstrich
stehen in einer der geaenderten Dateien (als Testfall festgehalten, ueber die
Codepunkte gebaut). Die neun vorbestehenden Markdown-Formatbefunde oberhalb von
`backend` (DI-06-01) sind unveraendert und nicht Gegenstand dieses Plans.

## User Setup Required

None. Ein Container ohne Modell oder ohne Vektorbestand schneidet weiter genau
die Ausschnitte, die er vorher geschnitten hat, und ein rein semantischer
Treffer bleibt dort ein Treffer ohne Vorschau. Kein neuer Wert, keine neue
Einstellung, keine Aenderung an der PHP-Haelfte.

## Next Phase Readiness

- **Plan 06-09 findet die Diagnose-Route vorbereitet.** `origins()` steht seit 06-06 ungerufen bereit, und ab jetzt gibt es mit `best_chunk_for` auch die Antwort auf "welche Stelle des Dokuments hat gepasst", in derselben Richtung und mit derselben Rechtekette.
- **Plan 06-09 erbt weiterhin zwei benannte Luecken**, DI-06-02 (`reset_for_reindex` ohne Aufrufer) und DI-06-03 (`embedding_version` wird von niemandem gestempelt). Der Zeiger in `deferred-items.md` ist berichtigt und zeigt jetzt auf 06-09, wo die Deckungsgradzahl entsteht.
- **Plan 06-10 hat einen weiteren Grep-Kandidaten.** Die Zahl 2 an `prefilter_visible` ist seit 06-06 ein Test; dieser Plan hat sie zum ersten Mal unter Druck gehalten, weil er einen zweiten Ausschnittsweg hinzugefuegt hat, ohne sie zu bewegen.
- **Plan 06-11 hat einen zweiten Messgegenstand an der Snippet-Route.** Je Aufruf entsteht ab jetzt eine Einbettung der Anfrage (T-06-41, bewusst akzeptiert). Der eingebettete Text ist die kurze Nutzeranfrage und nicht ein Dokument, aber es ist die erste Modellarbeit auf dem Leseweg der zweiten Runde.
- **Kein Blocker.**

## Self-Check: PASSED

Die angelegte Datei liegt auf der Platte
(`backend/tests/test_semantic_snippet.py`), alle fuenf Commits (`3d82e3e`,
`dcf8c63`, `13a6adb`, `ac7e2db`, `f747ae2`) stehen in `git log`. Zusaetzlich
geprueft: `grep -c 'prefilter_visible'` ist 2 in `index/search.py`,
`git diff --stat php/` ist leer, und weder Geviert- noch Halbgeviertstrich
stehen in einer der geaenderten Dateien oder in dieser Zusammenfassung.

---
*Phase: 06-semantische-suche*
*Completed: 2026-09-05*
