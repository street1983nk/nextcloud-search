---
phase: 06-semantische-suche
plan: 06
subsystem: backend
tags: [rrf, hybrid-suche, durchstich, degradieren, acl-kette, zaehl-orakel, fenster, nachlauf, d-19, d-20]

# Dependency graph
requires:
  - phase: 06-semantische-suche
    provides: "06-04: store/vectors.py mit nearest, open_vectors(read_only) und dem Deckel als Argument"
  - phase: 06-semantische-suche
    provides: "06-05: embed_query mit den E5-Praefixen, to_int8 und EmbedOutcome.available als Bedingung des engen try"
  - phase: 02-store-und-index
    provides: "index/search.py::candidates mit prefilter_visible, der Offset-Semantik (T-02-93) und dem Deckelzweig"
  - phase: 05-betriebsbeweis
    provides: "der Paritaetstest ueber die eine Suchroute, der den Vektorzweig durch D-20 automatisch mit abdeckt"
provides:
  - "index/fusion.py: documents_from_chunks und reciprocal_rank_fusion als reine Funktionen, dazu origins fuer die Diagnose"
  - "index/search.py::candidates mit Verschmelzungsfenster und Nachlauf, an genau einer Vorfilterstelle"
  - "index/search.py::SemanticSide, das Buendel aus Vektorspeicher, Modell und rohem Anfragetext"
  - "config.py: SEARCH_RRF_K, SEARCH_RRF_WINDOW, die zwei Gewichte, VECTOR_SCAN_MAX und ein vectors_db-Pfad"
  - "config.py::_bounded_float_from_environment, der Leser, bei dem die Null eine Antwort ist"
  - "api/resources.py: ReadSide.vectors, query_model() und die vierte degraded-Ursache"
affects: [06-07 Zweitspur und Loeschweg, 06-08 Statusseite, 06-09 Snippet fuer rein semantische Treffer, Diagnose-Route D-14]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Rangliste wird als Fenster gebildet, weil ein Rang nur relativ zu einer Liste existiert: beide Quellen sind vollstaendig, bevor ein einziger Score entsteht"
    - "Der Nachlauf hinter dem Fenster rechnet auf derselben Skala weiter (lexical_weight durch k plus rank) statt auf den rohen Maschinen-Score zurueckzufallen"
    - "Ein Gewicht von 0,0 entfernt seine Liste, statt sie mit Null zu bewerten: sonst waere die Einstellung keine Daempfung, sondern eine Umsortierung"
    - "Ein enger try/except liegt genau so tief, wie seine Antwort verlangt: eine Ebene hoeher haette die ganze Runde geleert"
    - "Zwei Aufrufstellen einer Sicherheitsfrage werden zu einer Funktion zusammengezogen, damit ihre Anzahl als Grep-Test behauptbar bleibt"

key-files:
  created:
    - backend/src/findling/index/fusion.py
    - backend/tests/test_rrf_fusion.py
    - backend/tests/test_semantic_search.py
  modified:
    - backend/src/findling/index/search.py
    - backend/src/findling/api/search.py
    - backend/src/findling/api/resources.py
    - backend/src/findling/config.py
    - backend/tests/conftest.py
    - backend/tests/test_config.py
    - backend/tests/test_read_side.py
    - backend/tests/test_search_library.py
    - docs/embeddings.md

key-decisions:
  - "Die Schleife von Phase 2 konnte nicht um eine zweite Quelle wachsen, sondern musste in zwei Abschnitte zerfallen: ein Rang existiert nur relativ zu einer Liste, also muessen beide Listen vollstaendig sein, bevor ein einziger Score entsteht"
  - "prefilter_visible wird in candidates() aus genau einem Helfer heraus gerufen (_permit), damit die Zahl der Aufrufstellen in dieser Datei 2 bleibt und als Grep-Test behauptbar ist"
  - "Der Nachlauf hinter dem Fenster vergibt RRF-Scores auf der lexikalischen Rangfortsetzung statt roher BM25-Werte; sonst waeren die Zahlen einer Antwort ueber die Fenstergrenze hinweg nicht mehr vergleichbar"
  - "SEARCH_LEXICAL_WEIGHT darf nicht 0 sein (Bereich ab 0,1), SEARCH_SEMANTIC_WEIGHT darf es (Bereich ab 0,0). Ein lexikalisches Gewicht von Null waere ein zweiter, undokumentierter Ausschalter fuer genau die Haelfte, die Kriterium 3 traegt"
  - "VECTOR_SCAN_MAX = 300, also Fenstertiefe 100 mal drei Chunks je gedeckeltem Dokument (gemessen 06-05); der Deckel ist an der Wave-0-Scanlatenz bemessen und mit SEARCH_ROUNDS = 3 begruendet"
  - "SemanticSide traegt drei Felder statt der zwei aus dem Plan: den Vektorspeicher, den rohen Text UND das Modell, weil candidates() einbetten muss und der Plan keine Herkunft fuer das Modell nennt"
  - "Das Modell der Leseseite lebt als query_model() in api/resources.py und nicht in ReadSide: es ist kein Handle auf dem Datentraeger, es haelt keine Verbindung, und es wird unter dem Modellverzeichnis gecacht statt unter dem Indexverzeichnis"
  - "Ein file_id, das im Vektorbestand steht und im Index nicht mehr, wird verworfen statt ausgeliefert: ein Treffer, den die PHP-Seite nie aufloesen kann, ist kein Treffer"
  - "Die Zeitstempel rein semantischer Treffer kommen aus EINER booleschen Oder-Abfrage ueber ihre file_ids, nicht aus einer Termabfrage je Dokument"
  - "conftest::indexed_volume legt eine leere vectors.db an, weil ein fehlender Vektorbestand ab jetzt degraded bedeutet und die ganze Endpunkt-Suite sonst gegen einen anderen Container liefe als den, um den es ihr geht"
  - "embedding_version liest den Tokendeckel aus den Einstellungen statt ihn als Literal zu behaupten; der Kommentar an der Stelle hatte diese Umstellung diesem Plan zugewiesen"

patterns-established:
  - "Wenn eine Sicherheitseigenschaft als Zahl von Aufrufstellen behauptet wird, bekommt die Frage eine Funktion, damit ein zweiter Aufruf keine zweite Zeile ist"
  - "Ein Bereich, der die Null zulaesst, und einer, der sie verbietet, stehen nebeneinander und die Asymmetrie wird an Ort und Stelle begruendet"

requirements-completed: [SEM-01, SEM-02]

# Metrics
duration: 35min
completed: 2026-09-05
---

# Phase 6 Plan 06: Der Durchstich Summary

**Die Phase löst ihr Versprechen ein: eine Anfrage, deren Wörter im Dokument nicht vorkommen, findet es trotzdem, auf demselben Weg, durch dieselbe Rechtekette und in derselben Antwortform wie jeder Volltexttreffer. Die Verschmelzung liegt an genau einer Stelle, oberhalb des einen Vorfilteraufrufs; die PHP-Hälfte ist unverändert; und fällt der Vektorzweig aus, kostet das die Semantik und nicht die Suche.**

## Performance

- **Duration:** rund 35 min
- **Started:** 2026-09-05T07:05:00Z
- **Completed:** 2026-09-05T07:40:00Z
- **Tasks:** 3 von 3
- **Files modified:** 12 (3 neu, 9 geändert)

## Accomplishments

- **Die drei Erfolgskriterien sind drei Tests, und zwei davon haben eine Gegenprobe daneben.** Kriterium 1 wird von einem Fall getragen, dem ein zweiter vorausgeht: dieselbe Anfrage ohne Vektorzweig findet nichts. Ohne diese Gegenprobe wäre ein grünes Kriterium 1 auch dann grün, wenn die Zeile am Ende doch lexikalisch getroffen hätte.
- **Kriterium 2 ist strukturell und nicht diszipliniert.** `prefilter_visible` steht in `index/search.py` an genau zwei Zeilen, und die eine davon, die den Suchweg betrifft, liegt in einem Helfer, den beide Abschnitte der Schleife rufen. Ein quellcode-lesender Test hält die Zahl 2 fest, ein zweiter hält fest, dass `fusion.py` die Frage gar nicht kennt. `git diff --stat php/` ist leer.
- **Kriterium 3 ist an drei verschiedenen Ausfallformen belegt.** Modell fehlt (Verdikt statt Ausnahme), Modell kracht (Ausnahme im engen Netz), Vektorbestand fehlt oder ist kaputt (`read_side` antwortet ein ReadSide mit `vectors=None` statt None). Alle drei enden in einer leeren Vektorliste, RRF wird zur Identität, und die Antwort besteht aus den unveränderten Volltexttreffern.
- **Das Zähl-Orakel T-02-93 hat den Umbau überlebt, und zwar gemessen.** Die Schleifenform ist eine andere geworden, weil RRF ein festes Fenster braucht, bevor ein Rang feststeht. Ein Test fährt zwei Seiten zu fünf gegen eine Seite zu zehn, mit aktivem Vektorzweig, und vergleicht sie Element für Element. `CandidatePage` trägt weiterhin kein Total, und `Candidate` weiterhin genau drei Felder.

## Task Commits

1. **Task 1 (RED): Das Gatter über der Verschmelzung** - `0ddbd3f` (test)
2. **Task 1 (GREEN): Die Verschmelzung als reine Funktionen, mit dem Rang ab 1** - `90cc5e5` (feat)
3. **Task 2: Die Leseseite kennt den Vektorspeicher, ohne von ihm abzuhängen** - `37c320a` (feat)
4. **Task 3 (RED): Das Gatter über dem Durchstich** - `e5eef02` (test)
5. **Task 3 (GREEN): candidates() verschmilzt, oberhalb des Vorfilters** - `56c8be5` (feat)
6. **Die offene Metrikfrage aus 06-04, beantwortet soweit belegt** - `d5f76c9` (docs)
7. **Die embedding_version-Marke liest den Tokendeckel statt ihn zu behaupten** - `9ed2fd9` (fix)

## Files Created/Modified

- `backend/src/findling/index/fusion.py` - `ChunkHit`, `DocumentHit`, `documents_from_chunks`, `reciprocal_rank_fusion`, `origins` und die drei Herkunftsmarken; der Modulkopf trägt die Formel als Zitat mit Quelle, der Kommentar über der Schleife den Rangbeginn, und `enumerate(..., start=1)` macht die Warnung zum Schlüsselwort
- `backend/tests/test_rrf_fusion.py` - 21 Fälle mit zwölf Zahlen und ohne Index, darunter der von Hand gerechnete Score, beide Identitätsabbildungen, die feste Reihenfolge bei gleichen Scores und drei Greps über das, was das Modul nicht kennen darf
- `backend/src/findling/index/search.py` - `QueryEmbedder`, `SemanticSide`, `_ranked`, `_permit`, `_semantic_documents`, `_mtimes_of` und die zweiteilige `candidates`; der Modulkopf hat einen vierten Absatz bekommen
- `backend/tests/test_semantic_search.py` - 17 Fälle an echtem Index, echtem Store und echtem Vektorspeicher; die einzige Attrappe ist das Modell
- `backend/src/findling/config.py` - der Block "hybrid read side" mit fünf Werten und vier Bereichstupeln, `_bounded_float_from_environment`, `Settings.vectors_db` und fünf neue Felder
- `backend/src/findling/api/resources.py` - `ReadSide.vectors`, `_read_only_vectors`, `query_model`, die vierte `degraded`-Ursache, die Freigabe des vierten Handles beim Verzeichniswechsel und der gelesene statt behauptete Tokendeckel in der Marke
- `backend/src/findling/api/search.py` - `one_round` bündelt Vektorspeicher, Modell und rohen Text und reicht sie durch; sonst nichts
- `backend/tests/conftest.py` - `write_vectors` und ein `indexed_volume`, das eine leere vectors.db trägt
- `backend/tests/test_config.py` - 15 neue Fälle, ein Test je Wert plus die beiden Bereichsasymmetrien und der Leckprüfer auf das deutsche Dezimalkomma
- `backend/tests/test_read_side.py` - sieben neue Fälle über die vier Zustände des Vektorhandles, das einmal gebaute Modell und die Marke am Tokendeckel
- `backend/tests/test_search_library.py` - die zwei quellcode-lesenden Zusicherungen über die Vorfilterstellen
- `docs/embeddings.md` - der Nachtrag zur Distanzmetrik, den 06-04 diesem Plan zugewiesen hatte

## Die gewählten Zahlen und woher sie kommen

| Einstellung | Wert | Bereich | Herkunft |
|---|---|---|---|
| `SEARCH_RRF_K` | 60 | 1 bis 600 | Elasticsearch-Referenz, "Defaults to 60" |
| `SEARCH_RRF_WINDOW` | 100 | 1 bis `SEARCH_SCAN_MAX` | D-12, Fenstertiefe je Quelle |
| `SEARCH_LEXICAL_WEIGHT` | 1,0 | **0,1** bis 10,0 | D-12; die Null ist ausgeschlossen, siehe unten |
| `SEARCH_SEMANTIC_WEIGHT` | 1,0 | **0,0** bis 10,0 | D-12, dämpfen ohne abschalten |
| `VECTOR_SCAN_MAX` | 300 | 1 bis `SEARCH_SCAN_MAX` | 100 Fenster mal 3 Chunks je Dokument (06-05), bemessen an 37,8 ms p95 warm bei 100.136 Chunks |

## Decisions Made

- **Die Schleife musste zerfallen, nicht wachsen.** Ein Rang existiert nur relativ zu einer Liste. Die inkrementelle Schleife aus Phase 2 holt Treffer in Bändern und filtert jedes Band sofort; ein RRF-Score kann darin gar nicht entstehen, weil der Rang eines Dokuments erst feststeht, wenn beide Listen vollständig sind. Daraus folgt die Zweiteilung: Abschnitt 1 bildet beide Listen im Fenster und verschmilzt sie, Abschnitt 2 setzt den inkrementellen Scan dahinter fort. Was den Nachlauf rechtfertigt, ist nicht Vollständigkeit, sondern die gemessene Vorfilter-Selektivität aus dem Vorbehalt zu D-12 (31 von 400).
- **Der Nachlauf rechnet auf der RRF-Skala weiter.** Naheliegend wäre gewesen, hinter dem Fenster den rohen Maschinen-Score zu vergeben. Das hätte zwei Zahlenskalen in einer Antwort gemischt: ein BM25-Wert liegt bei 1,5, ein RRF-Score bei 0,016, und ein Kandidat aus dem Nachlauf hätte damit besser ausgesehen als jeder Treffer aus dem Fenster. Stattdessen zählt der lexikalische Rang über die Fenstergrenze hinweg weiter, und der Score bleibt `lexical_weight / (k + rank)`: monoton fallend über die ganze Antwort, und für rein lexikalische Dokumente exakt der Wert, den die Verschmelzung ihnen gegeben hätte.
- **`_permit` ist eine Funktion, weil die Antwort eine Zahl ist.** Zwei Abschnitte brauchen den Vorfilter, und zwei Aufrufe wären zwei Zeilen gewesen. Die Sicherheitsaussage dieser Datei ist aber eine Zahl von Aufrufstellen, die ein Grep-Test behauptet. Ein Helfer hält beides zusammen: eine Stelle, an der Kandidaten auf Rechte treffen, und ein Test, der rot wird, sobald jemand eine zweite anlegt.
- **Das lexikalische Gewicht darf nicht Null sein, das semantische schon.** Die Asymmetrie steht als Kommentar an den zwei Bereichstupeln. Ein semantisches Gewicht von Null ist das ferne Ende der Dämpfung und genau das, was D-12 verlangt; `fusion.py` beantwortet es mit dem Entfernen der Liste, sodass die Ergebnismenge exakt die eines Containers ohne Vektorbestand ist. Ein lexikalisches Gewicht von Null wäre dagegen ein zweiter, undokumentierter Ausschalter für die Hälfte der Suche, die immer funktioniert, und damit ein Weg, Kriterium 3 still zu brechen.
- **`origins()` existiert und wird vom Suchweg nicht gerufen.** Der Kommentar an der Funktion sagt, wohin sie nicht gehört, und ein Test grept `index/search.py` nach ihrem Namen und erwartet ihn dort nicht. Die Kargheit von `Candidate` ist damit weiterhin die dokumentierte Sicherheitseigenschaft, die sie war (D-14).
- **Ein Vektortreffer ohne Indexdokument wird verworfen.** Die Zeitstempel rein semantischer Treffer kommen aus einer booleschen Oder-Abfrage über ihre file_ids. Deren zweite Aufgabe ist die wichtigere: eine file_id, die im Vektorbestand liegt und im Index nicht mehr, fällt dabei heraus. Sie auszuliefern hiesse, einen Treffer zu versprechen, den die PHP-Seite nie auflösen kann.
- **Der Vektorzweig fragt ohne Ähnlichkeitsschwelle.** Eine brute-force-Nachbarsuche rankt den ganzen Bestand; "nah genug" kennt sie nicht. Der Vektorzweig liefert deshalb immer bis zu `VECTOR_SCAN_MAX` Chunks, und was daraus ein Treffer wird, entscheidet die Verschmelzung über die Ränge und nicht ein Schwellwert. Die Tests sind entsprechend geschrieben: sie prüfen die Reihenfolge, nicht die Anwesenheit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktion] Der Plan nennt keine Herkunft für das Modell, ohne das der Vektorzweig nicht einbetten kann**

- **Found during:** Task 3, beim Entwurf von `SemanticSide`
- **Issue:** Der Plan verlangt, dass der Vektorabruf **einschliesslich des Einbettens** innerhalb von `candidates()` liegt, und beschreibt das Bündel als "den Vektorspeicher und den rohen Anfragetext". Ein Modell steht in keinem der beiden, und `ReadSide` bekommt laut Task 2 genau ein viertes Feld, nämlich `vectors`. Ohne eine dritte Angabe hätte `candidates()` sich das Modell selbst besorgen müssen, also entweder aus einem Modul-Singleton in `index/search.py` (verborgener Prozesszustand, in einer Suite nicht ersetzbar) oder über einen Import aus der API-Schicht (eine Kante von der Indexschicht nach oben).
- **Fix:** `SemanticSide` trägt drei Felder: `vectors`, `model`, `text`. `model` ist ein `Protocol` mit genau einer Methode, nach dem Vorbild von `ByteRange` in derselben Datei, sodass die Schleife ohne 118 MB Gewichte prüfbar bleibt. Gebaut wird das Bündel in `api/search.py::one_round`, und das Modell kommt aus `resources.query_model()`, das es einmal je Modellverzeichnis baut. Es liegt bewusst nicht in `ReadSide`: es ist kein Handle auf dem Datenträger, hält keine Verbindung und wird nicht unter dem Indexverzeichnis gecacht.
- **Files modified:** backend/src/findling/index/search.py, backend/src/findling/api/search.py, backend/src/findling/api/resources.py
- **Verification:** `test_the_query_model_is_built_once` belegt den Cache und dass der Bau nichts lädt; die drei Ausfalltests in `test_semantic_search.py` belegen beide Ausfallformen des Modells.
- **Committed in:** `37c320a`, `56c8be5`

**2. [Rule 1 - Fehler] Die vierte degraded-Ursache hätte die halbe Endpunkt-Suite gegen einen anderen Container laufen lassen**

- **Found during:** Task 2
- **Issue:** Task 2 verlangt, dass ein fehlender Vektorbestand bei eingeschaltetem Einbetten `degraded` setzt. Die Fixture `indexed_volume` legt keinen an, also wäre jeder Endpunkttest ab diesem Commit gegen einen Container gelaufen, der sich selbst als unvollständig meldet, und zwei bestehende Fälle in `test_read_side.py` (`degraded(side) is False`) wären rot geworden. Rot aus dem richtigen Grund, aber am falschen Gegenstand: jene Fälle handeln vom Messfenster des Verdikts und nicht vom Vektorbestand.
- **Fix:** `conftest.py::write_vectors` legt eine leere `vectors.db` an, und `indexed_volume` ruft sie. Leer und vorhanden ist genau der Zustand eines Containers, dessen Zweitspur noch nichts geschrieben hat; das Fehlen der Datei bleibt damit die Aussage, die es sein soll.
- **Files modified:** backend/tests/conftest.py
- **Verification:** Die beiden bestehenden Fälle sind unverändert grün, und vier neue Fälle drehen den Zustand in beide Richtungen (Datei gelöscht, Datei kaputt, Einbetten aus).
- **Committed in:** `37c320a`

**3. [Rule 1 - Fehler] Zwei Vorfilteraufrufe hätten die Abnahmezahl des Plans selbst gerissen**

- **Found during:** Task 3
- **Issue:** Die naheliegende Umsetzung ruft `prefilter_visible` zweimal in `candidates()`, einmal je Abschnitt. Zusammen mit `snippets_for` wären das drei Zeilen, und das Abnahmekriterium des Plans (`grep -c` ergibt 2) wäre von der eigenen Umsetzung gerissen worden. Wichtiger als die Zahl ist, was sie behauptet: dass es eine Stelle gibt, an der Kandidaten auf Rechte treffen.
- **Fix:** `_permit(store, uid, ranked)` als der eine Aufrufer, von beiden Abschnitten benutzt. Der Docstring nennt den Grund ausdrücklich als Zusicherung und nicht als Stil.
- **Files modified:** backend/src/findling/index/search.py
- **Verification:** `grep -c 'prefilter_visible' backend/src/findling/index/search.py` ist 2, in `fusion.py` 0; zwei quellcode-lesende Tests in `test_search_library.py` halten beides fest.
- **Committed in:** `56c8be5`

**4. [Rule 2 - Fehlende kritische Funktion] Die embedding_version-Marke behauptete einen Tokendeckel, statt ihn zu lesen**

- **Found during:** Nach Task 3, beim Durchgehen der offenen Zusagen dieser Phase
- **Issue:** Der Kommentar an `EMBEDDING_TOKEN_CAP` in `api/resources.py` sagt wörtlich, der Wert lebe dort als Literal, "until the cap becomes a setting in plan 06-06". Die Einstellung existiert seit 06-05 (`embed_token_cap`, mit Bereich und Test), und das Literal stand weiter auf 1024. Ein Betreiber, der den Deckel anhebt, macht damit jeden gespeicherten Vektor mit einem frisch gerechneten Anfragevektor unvergleichbar; eine Marke, die trotzdem 1024 behauptet, verbirgt genau den Drift, für den sie existiert.
- **Fix:** `embedding_mark(EMBEDDING_MODEL, tokens=settings().embed_token_cap)`. Das Literal ist weg, der Kommentar sagt jetzt, welche der vier Grössen woher kommt.
- **Files modified:** backend/src/findling/api/resources.py, backend/tests/test_read_side.py
- **Verification:** `test_the_embedding_mark_follows_the_token_cap` setzt den Deckel auf 2048 und erwartet die Marke `multilingual-e5-small/int8/384/2048`; der bestehende Fall über den Vorgabewert bleibt unverändert grün.
- **Committed in:** `9ed2fd9`

### Abweichungen, die keine Autoreparatur sind, sondern eine Auslegung des Plans

**5. `documents_from_chunks` nimmt Distanzen und nicht nur eine Reihenfolge**

Der Plan beschreibt die Aggregation als "Maximum". Der Vektorspeicher liefert
Distanzen, und eine bereits sortierte Liste macht Maximum, Summe und Anzahl
ununterscheidbar: die Funktion wäre ein `dict.fromkeys` gewesen und der Test
hätte nichts belegt. `ChunkHit` trägt deshalb die Distanz, und die Umkehrung
(das Maximum der Ähnlichkeit ist das Minimum der Distanz) steht als der
Kommentar an der Stelle, die genau einmal falsch sein kann.

**6. Der Vektorzweig deckelt mit `k = k_max` statt mit zwei Zahlen**

`nearest` nimmt `k` und `k_max` getrennt. `candidates()` übergibt beide als
`VECTOR_SCAN_MAX`, damit die Warnzeile in `vectors.py`, die zwei Zahlen nennt,
auf dem Suchweg gar nicht erst ausgelöst werden kann. Der erreichte Deckel wird
stattdessen von `index/search.py` gemeldet, in der Form des bestehenden
Deckelzweigs: nur die Tatsache, keine Anfrage, keine Zahl. Ein Test prüft die
Zeile zeichenweise auf Ziffern.

**7. Der Kriterium-3-Abnahmetest zeigt auf ein leeres Modellverzeichnis, statt eine Datei umzubenennen**

D-19 nennt beide Formen ("Modell fehlt, Erweiterung nicht geladen"). Auf einer
Maschine ohne Modell gibt es keine Datei zum Umbenennen; das leere Verzeichnis
ist derselbe Zustand und braucht kein Artefakt. Die zweite Form, der krachende
Zweig, ist zusätzlich abgedeckt, und zwar mit Nutzerinhalt in der
Ausnahmemeldung, damit die Log-Zusicherung etwas zu verlieren hat.

**8. `docs/embeddings.md` ist nicht in der Dateiliste des Plans**

Der Nachtrag aus 06-04 weist die offene Frage zur Distanzmetrik wörtlich
"Plan 06-06, wo der Anfragevektor entsteht" zu. Sie hier stehen zu lassen hätte
einen dokumentierten offenen Punkt ohne Nachfolger hinterlassen. Der Absatz sagt
jetzt, was belegt ist (dieselbe Skala für beide Seiten, und der Messwert aus
06-03, bei dem keiner von sechs Vergleichen den doppelten Standardfehler
erreicht) und was ungemessen bleibt (die Norm eines quantisierten Vektors als
Zahl, für die es keine Entscheidung gibt, die von ihr abhinge).

---

**Total deviations:** 4 autorepariert (2 Fehler, 2 fehlende kritische Funktionen), 4 Auslegungen
**Impact on plan:** Keine Ausweitung des Umfangs. Alle vier Autoreparaturen betreffen genau die Eigenschaften, die dieser Plan zusichern soll: eine Verschmelzungsstelle, eine Vorfilterstelle, ein Ausfall, der die Semantik kostet und nicht die Suche, und eine Marke, die einen Drift zeigt statt ihn zu verbergen.

## Issues Encountered

- **Der Vektorzweig liefert alles, nicht nur das Nahe.** Drei Testfälle waren zunächst rot, weil sie genau ein Dokument erwarteten. sqlite-vec rankt den ganzen Bestand nach Distanz und kennt kein "nah genug", also stehen alle Dokumente mit Vektoren in der semantischen Liste, geordnet. Das ist das richtige Verhalten und die falsche Erwartung gewesen; die Fälle prüfen jetzt die Reihenfolge. Eine Ähnlichkeitsschwelle wäre ein zusätzlicher, unbelegter Parameter, und RRF verschmilzt Ränge und keine Abstände.
- **`enable_load_extension` in der Testsuite.** `conftest` öffnet jetzt in jeder Endpunkt-Suite eine `vectors.db`, also lädt jede dieser Suiten vec0. Lokal und im Gates-Job ist das gegeben (das Rad steht in `uv.lock`); auf einer Python-Übersetzung ohne ladbare Erweiterungen würde die Fixture scheitern statt zu überspringen. Probe A13 aus Plan 06-01 belegt, dass das Abbild es kann.
- **Die AWS-Box ist nicht angefasst worden.** Dieser Plan misst nichts; alle Zahlen in den Kommentaren stammen aus den Berichten von Welle 0 und aus Plan 06-05.

## Offene Verifikation

Keine. Alle Gates sind lokal grün gelaufen: `pytest` mit 1.249 bestandenen und 13
übersprungenen Tests, `ruff check .`, `ruff format --check .`, `pyright` mit 0
Fehlern und `vulture` ohne Befund, jeweils im CI-Umfang `backend`. Dazu die vier
Zusicherungen aus der Verifikationszeile des Plans: `git diff --stat php/` ist
leer, `grep -c 'prefilter_visible'` ergibt 2 in `index/search.py` und 0 in
`index/fusion.py`, die Suche nach `tantivy` und `sqlite3` in `index/fusion.py`
ergibt 0, und weder Geviert- noch Halbgeviertstrich stehen in einer der
geänderten Dateien. Die neun vorbestehenden Markdown-Formatbefunde oberhalb von
`backend` (DI-06-01) sind unverändert und nicht Gegenstand dieses Plans.

## User Setup Required

None. Alle fünf neuen Werte haben eine Vorgabe, keiner muss gesetzt werden, und
keiner ist auf der Admin-Seite sichtbar (D-12). Ein Container ohne Modell und
ohne Vektorbestand sucht lexikalisch weiter und meldet sich als degraded.

## Next Phase Readiness

- **Plan 06-07 kann die Zweitspur bauen.** Die Leseseite ist fertig verdrahtet: sobald `replace_chunks` Vektoren schreibt, findet die Suche sie ohne eine weitere Codeänderung. Was 06-07 zu entscheiden hat, ist ausschliesslich, welche Dateien in die Spur gehören.
- **Plan 06-08 hat die vierte degraded-Ursache schon.** Die Statusseite kann `vectors=None` bei eingeschaltetem Einbetten als eigenen Zustand darstellen, und `chunk_count`/`vector_count` aus 06-04 liefern die zweite Deckungsgrad-Zahl.
- **Der Snippet-Weg für rein semantische Treffer (D-13) hat seinen Träger.** `documents_from_chunks` liefert zu jedem Dokument die `chunk_id` des Rang-Chunks, also genau den Chunk, dessen Ausschnitt der Nutzer sehen soll. Heute verlässt diese Zahl `candidates()` nicht, weil `Candidate` drei Felder trägt; wer sie in `snippets_for` braucht, holt sie dort über `chunks_of` aus dem Vektorspeicher, hinter dem Vorfilter.
- **Die Diagnose-Route (D-14) findet `origins()` fertig vor.** Sie ist gebaut, getestet und wird vom Suchweg nicht gerufen, und ein Test hält genau das fest.
- **Ein Punkt für 06-07, damit er nicht zweimal gefunden wird:** `embedding_version` wird weiterhin von niemandem geschrieben. Die Marke steht auf `unknown`, ihr Drift wird gemeldet und bleibt folgenlos, bis die Zweitspur sie nach einem abgeschlossenen Lauf stempelt. Ihre Zusammensetzung ist jetzt vollständig (Modell, Quantisierung, Dimensionen, gelesener Tokendeckel), es fehlt nur der Schreibvorgang.
- **Kein Blocker.**

## Self-Check: PASSED

Alle drei angelegten Dateien liegen auf der Platte
(`backend/src/findling/index/fusion.py`, `backend/tests/test_rrf_fusion.py`,
`backend/tests/test_semantic_search.py`), alle sieben Commits (`0ddbd3f`,
`90cc5e5`, `37c320a`, `e5eef02`, `56c8be5`, `d5f76c9`, `9ed2fd9`) stehen in
`git log`. Zusätzlich geprüft: `grep -c 'prefilter_visible'` in
`index/search.py` ist 2 und in `index/fusion.py` 0, `grep -c 'tantivy|sqlite3'`
in `index/fusion.py` ist 0, `grep -c '_bounded_float_from_environment'` in
`config.py` ist 3, `git diff --stat php/` ist leer, und weder Geviert- noch
Halbgeviertstrich stehen in einer der zwölf Dateien.

---
*Phase: 06-semantische-suche*
*Completed: 2026-09-05*
