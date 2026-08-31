---
phase: 02-indexkern-und-volltextsuche
plan: 11
subsystem: api
tags: [zweistufig, endpunkte, comp-04, srch-02, srch-03, idx-06, degraded, kanarienvogel, tdd]

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-09: candidates, snippets_for und char_ranges, alle drei synchron"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-10: main.py mit Lifespan, Poller und dem 400-Handler aus Phase 1"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-02: prefilter_visible, counts, version_mismatch, die Nur-Lese-Verbindung"
provides:
  - "POST /search: Kandidaten ohne Textfeld, seitenweise, mit degraded"
  - "POST /snippets: Klartextausschnitte mit Zeichenoffsets, nur fuer bestaetigte Kennungen"
  - "GET /status: Zaehler, ACL-Groesse und Versionsmarken, ohne eine Zeile Nutzerinhalt"
  - "api/resources.py: die Lesehaelfte des Containers, einmal geoeffnet, Abwesenheit nie gecacht"
  - "store.acl_totals(): Zeilen und Dokumente der ACL-Tabelle aus einer Abfrage"
  - "Gemessener Befund: fastapi 0.141.1 haengt Router als privates Huellenobjekt in APP.routes"
affects: [02-12, 02-13, 02-14, phase-04-statusseite]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Die Sicherheitszusage steht im Typ: ein gewoehnlicher Kandidat hat kein Textfeld, der Kanarienvogel ist eine Unterklasse"
    - "Abwesenheit wird nie gecacht, Vorhandenes wird unter dem Pfad gecacht, aus dem es kam"
    - "Jeder Endpunkt antwortet im Zweifel leer und wohlgeformt, nie mit einer Ausnahme"
    - "Ein reservierter Suchbegriff wird exakt verglichen und in docs/ benannt"
    - "Ein Testhaken, der nicht in info.xml steht, sagt im Docstring, dass er keine Einstellung ist"

key-files:
  created:
    - backend/src/findling/api/resources.py
    - backend/src/findling/api/snippets.py
    - backend/src/findling/api/status.py
    - backend/tests/conftest.py
    - backend/tests/test_search_endpoint.py
    - backend/tests/test_snippets_endpoint.py
    - backend/tests/test_status_endpoint.py
  modified:
    - backend/src/findling/api/search.py
    - backend/src/findling/main.py
    - backend/src/findling/store/repo.py
    - docs/dev-setup.md

key-decisions:
  - "Der Kanarienvogel ist eine eigene Modellklasse statt zweier optionaler Felder: so kann ein gewoehnlicher Kandidat auch versehentlich keinen Text tragen"
  - "Kein zweiter Ueberfetch im Endpunkt: die PHP-Seite ueberfetcht bereits um vier, ein zweiter Faktor waere sechzehnfache Ranking-Kosten und eine Seitenmarke in Spruengen, die der Aufrufer nicht kennt"
  - "Die Lesehaelfte cached nur den Erfolgsfall: ein Container wird vor seinem ersten Index ausgeliefert, und ein gecachtes Nein waere eine Suche, die bis zum Neustart nichts findet"
  - "Der Cache-Schluessel ist der Pfad, aus dem geoeffnet wurde: eine Testsuite hat ein Volume je Test, und ohne den Schluessel durchsucht der zweite Test den Index des ersten"
  - "/status oeffnet seine Nur-Lese-Verbindung je Aufruf statt sie zu halten: eine Adminseite fragt selten, und eine eigene Verbindung ist immer aktuell ohne Cache, den jemand ungueltig machen muss"
  - "docs ist die Zahl der Dokumente mit Berechtigungszeilen, nicht die Dokumentzahl des Index: zusammen mit aclRows ist das die Kennzahl aus repo.py, und es entsteht keine zweite Zaehllogik"
  - "Die Verzoegerung wird vor der Arbeit gewartet, damit sie auch fuer die leeren Antworten gilt, die der Zeitbudget-Nachweis gerade braucht"

patterns-established:
  - "Zusagen ueber Abwesendes als Test ueber die Feldmenge einer Antwort, nicht ueber einzelne Felder"
  - "Testfixtures bauen das echte Volume: Wortlisten-Artefakt, Index und Zustandsdatenbank statt Attrappen"

requirements-completed: [COMP-04, SRCH-02, SRCH-03, IDX-06]

# Metrics
duration: 33 min
completed: 2026-08-31
---

# Phase 02 Plan 11: Die drei Endpunkte Summary

**Der erste Aufruf gibt heraus, was die PHP-Seite fuer den Recheck braucht und keinen Buchstaben mehr; der zweite gibt Textausschnitte heraus, aber nur zu Kennungen, die der Vorfilter selbst noch einmal bestaetigt hat; und der dritte sagt, wie es dem Container geht, ohne einen einzigen Dateinamen zu nennen.**

## Performance

- **Duration:** 33 min
- **Started:** 2026-08-31T21:25Z
- **Completed:** 2026-08-31T21:58Z
- **Tasks:** 3 von 3
- **Files created:** 7, **modified:** 4

## Accomplishments

- `POST /search` liefert `candidates`, `hasMore`, `nextOffset` und `degraded`. Ein Kandidat traegt `fileId`, `score`, `mtime` und `ext`, und das Modell hat **strukturell** kein Textfeld: der Kanarienvogel ist eine eigene Unterklasse, ein gewoehnlicher Kandidat kann Titel und Text also nicht einmal versehentlich tragen.
- `POST /snippets` schneidet Klartextausschnitte mit Zeichenoffsets und ruft den ACL-Vorfilter als erste Handlung, obwohl die PHP-Seite ohnehin nur ueberlebende Kennungen schickt. Eine fehlende Kennung ist eine vollstaendige Antwort; es gibt keine Meldung, die einem Aufrufer verraet, ob eine Datei existiert.
- `GET /status` liefert die drei Zustandszaehler, die Groesse der ACL-Tabelle, drei Versionsmarken und zwei Flaggen. Die Feldmenge wird als Ganzes getestet, damit ein spaeterer Plan, der "die zuletzt fehlgeschlagene Datei" ergaenzen will, diesen Test absichtlich aendern muss.
- Alle drei Endpunkte laufen ueber `asyncio.to_thread` und antworten im Zweifel leer und wohlgeformt. Kein Pfad wirft: die Unified Search ruft alle Anbieter parallel, und der werfende kostet den Nutzer die ganze Suche.
- Der Kanarienvogel ist eingesperrt: exakter Vergleich nach dem Trimmen, sonst nichts. `findling-canary contract` findet Dokumente und nicht ihn. Er antwortet auch **ohne** Index, was genau die Lage ist, in der jemand ihn benutzt.
- 48 neue Tests, alle fuenf Python-Gates lokal gruen (420 Tests, ruff check, ruff format, pyright, vulture).

## Task Commits

1. **Task 1: POST /search liefert Kandidaten statt Ergebnisse**
   - RED `bc9ae6e` (test), GREEN `fd9b0a1` (feat)
2. **Task 2: POST /snippets, der zweite Aufruf nach dem Rechtecheck**
   - RED `f1669ff` (test), GREEN `4119ad2` (feat)
3. **Task 3: GET /status und die Verdrahtung der drei Router**
   - RED `52b8d87` (test), GREEN `eef7395` (feat)

Dazu `7665049` (docs): `findling-canary` als reservierter Begriff, siehe Deviation 3.

## TDD Gate Compliance

Alle drei Aufgaben sind mit `tdd="true"` geplant und liefen in der Reihenfolge RED, GREEN. Jeder RED-Commit steht gegen ein tatsaechlich rotes Ergebnis: `ImportError` fuer `Candidate` bei Task 1, 13 von 14 rot bei Task 2, 9 von 10 rot bei Task 3. Die jeweils eine gruene Zusage im RED-Lauf ist in beiden Faellen `test_a_request_without_any_appapi_header_is_unauthorized`, und sie ist zu Recht gruen: sie prueft die Middleware, die eine Anfrage ohne Kopfzeile abweist, bevor der Router ueberhaupt befragt wird. Eine REFACTOR-Runde war in keiner Aufgabe noetig.

## Das Wire-Format, an der laufenden Anwendung abgelesen

Nicht aus dem Plan abgeschrieben, sondern durch die Anwendung geschickt und ausgegeben (Wegwerfskript ausserhalb des Repos, `TestClient` gegen ein echtes Volume):

```
POST /search   {"candidates":[{"fileId":3,"score":0.0873...,"mtime":1700000003,"ext":"pdf"}],
                "hasMore":true,"nextOffset":2,"degraded":false}

canary         {"candidates":[{"fileId":0,"score":0.0,"mtime":1788213366,"ext":"",
                "title":"findling-canary","snippet":"produced inside container ... for user alice"}],
                "hasMore":false,"nextOffset":0,"degraded":false}

POST /snippets {"snippets":{"1":{"text":"Für alle Beschäftigten gilt: die Kündigungsfrist im Vertrag 1 ...",
                "highlights":[[33,48]]}}}

GET /status    {"indexed":12,"skipped":0,"failed":0,"aclRows":18,"docs":12,"indexVersion":1,
                "analyzerVersion":1,"wordlistHash":"bcbc22e7...","reindexRequired":false,
                "lowDisk":false,"note":""}
```

Der Bereich `[33, 48]` ist der Beleg fuer die Zeichenzaehlung: `Kündigungsfrist` beginnt im Text an **Zeichen** 33 und an **Byte** 35, weil `Für` und `Beschäftigten` davor stehen. Ein Aufrufer, der mit 35 schneidet, markiert `ndigungsfrist i`.

Gegen `php/lib/Service/ExAppService.php` gelesen, Feld fuer Feld: `filterCandidates` liest `fileId` als `int`, akzeptiert `title` und `snippet` nur bei `fileId <= 0` und nur unter dem exakten Titel; `filterSnippets` nimmt den Schluessel als Zeichenkette mit `ctype_digit`; `filterHighlights` verlangt zwei `int`. Alles vier passt. Der Kanarienvogel meldet `hasMore` false, was auf der PHP-Seite `SearchResult::complete` statt `paginated` ergibt, also kein Weiterblaettern ins Leere.

## Files Created/Modified

- `backend/src/findling/api/search.py` , `SearchRequest` (jetzt mit `offset` und `titleOnly`), `Candidate`, `CanaryCandidate`, `SearchResponse`, `build_canary_hits`, `one_round`, `search`. Der Modul-Docstring nennt jetzt vier eingefrorene Entscheidungen statt zweier.
- `backend/src/findling/api/snippets.py` , `SnippetsRequest`, `Snippet`, `SnippetsResponse`, `artificial_delay_seconds`, `excerpts`, `snippets`.
- `backend/src/findling/api/status.py` , `StatusResponse`, `report`, `read_status` und zwei Hinweistexte.
- `backend/src/findling/api/resources.py` , `ReadSide`, `expected_marks`, `version_drift`, `low_disk`, `read_side`, `degraded`, `report_version_drift`.
- `backend/src/findling/main.py` , drei Router statt einem, plus die Driftmeldung beim Start.
- `backend/src/findling/store/repo.py` , neue Methode `acl_totals`, siehe Deviation 1.
- `backend/tests/conftest.py` , die geteilten Fixtures: signierte Kopfzeile, leeres Volume, gefuelltes Volume mit Wortlisten-Artefakt, Index und Zustandsdatenbank.
- `backend/tests/test_search_endpoint.py` , 24 Tests. Ersetzt `test_search_canary.py`, siehe Deviation 2.
- `backend/tests/test_snippets_endpoint.py` , 14 Tests.
- `backend/tests/test_status_endpoint.py` , 10 Tests.
- `docs/dev-setup.md` , der reservierte Begriff, siehe Deviation 3.

## Decisions Made

- **Der Kanarienvogel ist eine Unterklasse, keine zwei optionalen Felder.** Der Plan erlaubt `title` und `snippet` als optionale Felder an `Candidate`. Umgesetzt ist die strengere Form: `Candidate` hat vier Felder, `CanaryCandidate` erbt und ergaenzt zwei. Damit ist die Zusage aus Pitfall 5 eine Eigenschaft des Typs statt einer Regel, an die sich jemand erinnern muss, und der Test ueber `Candidate.model_fields` haelt sie. Die Antwort deklariert `list[CanaryCandidate | Candidate]`, sonst wuerde Pydantic die beiden Zusatzfelder beim Serialisieren nach dem deklarierten Typ verwerfen.
- **Kein zweiter Ueberfetch.** `config.py` fuehrt `search_overfetch` und `search_rounds`, und `Provider.php` fuehrt dieselben Werte als eigene Konstanten (02-12 laesst die Frage ausdruecklich offen, welche Seite die Wahrheit ist). Der Endpunkt nimmt `limit` und `offset` so, wie sie kommen. Zwei Multiplikatoren waeren sechzehnfache Ranking-Kosten fuer Treffer, die niemand ansieht, und `nextOffset` wuerde in Spruengen laufen, die der Aufrufer nicht kennt. Die Entscheidung ist damit an einer Stelle statt an zwei.
- **Abwesenheit wird nie gecacht.** Ein Container wird ausgeliefert, bevor er indexiert hat, also finden die ersten Suchen zu Recht weder Index noch Zustandsdatenbank. Wuerde dieses Nein gecacht, antwortete der Prozess bis zum Neustart "nichts gefunden", waehrend der Poller ein Volume fuellt, das niemand liest. Gecacht wird nur der Erfolg, und zwar unter dem Pfad, aus dem er kam.
- **`/status` haelt keine Verbindung.** Eine Adminseite fragt selten, und eine Verbindung je Aufruf ist immer aktuell, ohne dass jemand einen Cache ungueltig machen muss. Der Endpunkt liest keine Nutzer-ID: `access_level` ADMIN steht in `info.xml`, dort wird es durchgesetzt, und die Antwort ist fuer alle gleich.
- **`docs` zaehlt Dokumente mit Berechtigungszeilen.** Zusammen mit `aclRows` ergibt das genau die Kennzahl, die `acl_rows_per_document` in `repo.py` schon beschreibt (gemessen 3,36 bei hunderttausend Dateien und fuenfzig Nutzern). Die Dokumentzahl des Tantivy-Index waere die zweite moegliche Lesart gewesen; sie haette den Statuspfad gezwungen, den Index zu oeffnen, und dafuer ist eine Zahl auf einer Seite kein hinreichender Grund.
- **Die Verzoegerung wartet vor der Arbeit.** Andernfalls waeren genau die Frueh-Rueckgaben (kein Index, keine Kennungen) unverzoegert, und das sind die Faelle, die der Zeitbudgetnachweis in 02-14 braucht.
- **`reasons_by_state` bleibt ungenutzt.** Die Aufschluesselung nach Gruenden ist die Fehlerliste der Phase-4-Seite. Das im Plan eingefrorene Antwortformat nennt sie nicht, und ein zusaetzliches Feld haette den Test ueber die Feldmenge gebrochen, der genau dafuer da ist.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] `aclRows` existierte als Zahl nicht**

- **Found during:** Task 3
- **Issue:** Das eingefrorene Antwortformat verlangt `aclRows` und `docs`. `store/repo.py` bot nur `acl_rows_per_document()`, also den Quotienten. Der Plan verlangt ausdruecklich, dass keine zweite Zaehllogik entsteht, und ein `SELECT COUNT(*)` im Endpunkt haette SQL ausserhalb des einen Moduls bedeutet, das SQL enthaelt, entgegen dessen eigenem Docstring.
- **Fix:** Neue Methode `Store.acl_totals()` mit genau der Abfrage, die vorher in `acl_rows_per_document` stand; diese Methode dividiert jetzt das Ergebnis, statt selbst zu fragen. Eine Abfrage, zwei Aufrufer, keine zweite Zaehlung.
- **Files modified:** `backend/src/findling/store/repo.py`
- **Verification:** `test_the_answer_carries_the_counters_the_versions_and_nothing_else` prueft `aclRows == 18` und `docs == 12` gegen ein Volume, dessen ACL-Zeilen die Fixture geschrieben hat; die bestehenden Tests von `acl_rows_per_document` in `tests/test_store_repo.py` bleiben gruen.
- **Committed in:** `eef7395`

**2. [Rule 3 - Blocking] `test_search_canary.py` prueft ein Protokoll, das es nicht mehr gibt**

- **Found during:** Task 1
- **Issue:** Die Phase-1-Datei liest `response.json()["results"][0]` und erwartet `Hit` mit `path`, `title` und `snippet`. Nach dem Umbau ist das kein "fehlgeschlagener Test", sondern ein Test einer verschwundenen Schnittstelle. Der Plan nennt nur `test_search_endpoint.py`, sagt aber nicht, was mit der alten Datei geschieht.
- **Fix:** Die Datei ist geloescht, und **alle sechs** Zusagen der Phase 1 sind namentlich in `test_search_endpoint.py` uebernommen und gegen das neue Protokoll gestellt: Nutzer-ID im Rumpf, Tippfehler bleibt 422, Limit ausserhalb des Bereichs, fehlende Identitaet, fehlende Kopfzeile, falsches Geheimnis, dazu die drei Kanarien-Zusagen und der Markup-Test. Eine Testdatei je Endpunkt.
- **Files modified:** `backend/tests/test_search_canary.py` (geloescht), `backend/tests/test_search_endpoint.py`
- **Verification:** Die Loeschung steht im RED-Commit und ist die einzige des ganzen Plans (`git diff --diff-filter=D` ist bei allen anderen Commits leer). 24 statt 9 Tests.
- **Committed in:** `bc9ae6e`

**3. [Rule 2 - Missing critical functionality] Der reservierte Begriff stand nirgends, und die Doku nannte einen falschen Titel**

- **Found during:** Abschliessende Verifikation
- **Issue:** Der Research verlangt woertlich: "Der reservierte Begriff gehoert in docs/." Er stand dort nicht als reserviert, sondern nur als Diagnoseschritt. Dazu nannte `docs/dev-setup.md` den erwarteten Eintrag **Findling canary**, waehrend beide Haelften und der CI-Job `findling-canary` verlangen; wer der Doku folgt, sucht nach einem Fehler, der keiner ist. Ab diesem Plan ist die Reservierung ausserdem eine Zusage mit Folgen: der Vergleich ist exakt, also verhaelt sich jede andere Suche anders als vorher.
- **Fix:** Neuer Abschnitt "findling-canary is a reserved search term": exakter Vergleich, keine andere Suche sieht ihn, Dateien mit dem Wort im Namen werden normal gefunden, und er antwortet ohne Index. Der falsche Titel ist berichtigt.
- **Files modified:** `docs/dev-setup.md`
- **Verification:** Der genannte Titel ist derselbe wie in `integration.yml` (`entries[0].title == "findling-canary"`) und in `ExAppService::CANARY_TITLE`.
- **Committed in:** `7665049`

**4. [Rule 3 - Blocking] Ein gemeinsames Modul fuer die Lesehaelfte, und ein gemeinsames conftest**

- **Found during:** Task 1
- **Issue:** Die drei Endpunkte brauchen dieselben zwei Handles, und das Oeffnen ist teuer (Analysekette mit 23-MB-Automat, Reader-Konfiguration zwanzigmal so teuer wie eine Suche). Der Plan nennt nur die drei Endpunktdateien. Die Alternativen waeren gewesen, `snippets.py` aus `search.py` importieren zu lassen (eine Abhaengigkeit zwischen zwei gleichrangigen Endpunkten) oder dreimal dasselbe zu oeffnen. Dieselbe Frage stellt sich fuer die Testfixtures: drei Suiten brauchen dasselbe echte Volume.
- **Fix:** `backend/src/findling/api/resources.py` und `backend/tests/conftest.py`. Beide sind reine Verlagerung, kein neuer Umfang; die Datei mit dem Zustand ist damit eine statt drei, was fuer einen prozessweiten Cache die Voraussetzung ist.
- **Files modified:** `backend/src/findling/api/resources.py` (neu), `backend/tests/conftest.py` (neu)
- **Verification:** `vulture --min-confidence 80` findet nichts Ungenutztes, `pyright` ist ohne Befund, und das Nur-Lesen-Gate laeuft ueber beide Module.
- **Committed in:** `fd9b0a1`

**5. [Rule 1 - Bug] Die erwarteten Versionsmarken waren prozessweit gecacht, ohne Schluessel**

- **Found during:** Task 3
- **Issue:** `expected_marks()` cachte das Ergebnis von `build_artifact()` in einer Modulvariablen. Der Digest haengt an der Wortliste, und die haengt am Volume. Auf einer Maschine, auf der die Debian-Wortliste installiert ist (im Image ist sie es), haette der erste Aufruf einen fremden Digest gecacht und jede spaetere Statusabfrage `reindexRequired` gemeldet, obwohl nichts abweicht. Im Container faellt das nie auf, weil es dort nur ein Volume gibt; in der CI oder im Image waere es ein Fehlalarm auf der Adminseite.
- **Fix:** Derselbe Cache-Schluessel wie bei den Handles daneben: das Verzeichnis, aus dem gelesen wurde.
- **Files modified:** `backend/src/findling/api/resources.py`
- **Verification:** `test_a_matching_index_needs_no_reindex` und `test_a_version_drift_is_reported_as_reindex_required` laufen im selben Prozess gegen zwei verschiedene Volumes und widersprechen sich nicht mehr.
- **Committed in:** `eef7395`

**6. [Rule 3 - Blocking] Der Snippet-Router musste in Task 2 eingehaengt werden**

- **Found during:** Task 2
- **Issue:** Der Plan legt die Verdrahtung aller drei Router in Task 3. Ohne sie kann kein einziger Test von Task 2 gruen werden, weil die Route nicht existiert.
- **Fix:** Task 2 haengt den zweiten Router ein, Task 3 den dritten und stellt das Kriterium `include_router` = 3 her.
- **Files modified:** `backend/src/findling/main.py`
- **Verification:** `grep -c 'include_router' main.py` ist 3, und `test_all_three_routes_are_mounted` prueft alle drei Pfade.
- **Committed in:** `4119ad2` und `eef7395`

---

**Total deviations:** 6 auto-fixed (1 Bug, 2 fehlende Notwendigkeiten, 3 blockierende Punkte)
**Impact on plan:** Kein Scope-Zuwachs. Zwei neue Dateien (`resources.py`, `conftest.py`) sind Verlagerung von Code, den sonst drei Stellen doppelt haetten; die Loeschung der Phase-1-Testdatei ist ein Ersatz mit derselben Aussage in groesserem Umfang; die uebrigen drei sind Korrekturen an Stellen, die dieser Plan selbst falsch gemacht haette.

## Eigene Messbefunde

| Beobachtung | Wert |
|---|---|
| Hervorhebung fuer `Kündigungsfrist` mit zwei Umlauten davor | `[33, 48]` in Zeichen; in Bytes waere es `[35, 50]` |
| `APP.routes` bei fastapi 0.141.1 nach `include_router` | drei `fastapi.routing._IncludedRouter` ohne eigenen `path`; die Pfade stehen nur in `APP.openapi()["paths"]` |
| ACL-Zeilen des Testkorpus | 18 Zeilen auf 12 Dokumente, also 1,5 je Dokument |
| Antwort auf `findling-canary` ohne Index | ein Kandidat, `degraded` false, `hasMore` false |
| Gesamtlaufzeit der Suite nach diesem Plan | 420 Tests, 12 s |

## Acceptance Criteria

### Task 1

| Kriterium | Soll | Ist |
|---|---|---|
| `pytest tests/test_search_endpoint.py -q` | Exit 0 | 25 passed (24 Funktionen, eine parametrisiert) |
| `grep -c 'def test_' test_search_endpoint.py` | >= 9 | 24 |
| `grep -c 'to_thread' api/search.py` | >= 1 | 2 |
| `grep -c 'extra="forbid"' api/search.py` | >= 1 | 2 |
| `grep -Ec '"snippet"\|snippet:' api/search.py` | nur am Kanarienvogel | 1, Zeile 111 in `CanaryCandidate` |
| `grep -Ec '== *CANARY_TERM\|CANARY_TERM *==' api/search.py` | >= 1 | 1 |
| `grep -c 'in query' api/search.py` | 0 | 0 |
| `pytest tests/test_readonly_gate.py -q` | gruen | gruen |
| ruff check, ruff format --check, pyright, vulture | Exit 0 | alle vier ohne Befund |

### Task 2

| Kriterium | Soll | Ist |
|---|---|---|
| `pytest tests/test_snippets_endpoint.py -q` | Exit 0 | 14 passed |
| `grep -c 'def test_' test_snippets_endpoint.py` | >= 7 | 14 |
| `grep -c 'snippets_for' api/snippets.py` | 1 | 1 |
| `grep -c 'extra="forbid"' api/snippets.py` | 1 | 1 |
| `grep -c 'FINDLING_ARTIFICIAL_DELAY_MS' api/snippets.py` | >= 1 | 1 |
| `grep -c 'FINDLING_ARTIFICIAL_DELAY_MS' appinfo/info.xml` | 0 | 0 |
| `grep -c 'def test_fragment_has_no_markup' test_snippets_endpoint.py` | 1 | 1 |
| ruff check, ruff format --check, pyright, vulture | Exit 0 | alle vier ohne Befund |

### Task 3

| Kriterium | Soll | Ist |
|---|---|---|
| `pytest tests/test_status_endpoint.py -q` | Exit 0 | 10 passed |
| `grep -c 'include_router' main.py` | 3 | 3 |
| `grep -Ec '"path"\|"title"\|"query"' api/status.py` | 0 | 0 |
| `grep -c 'reindexRequired' api/status.py` | >= 1 | 3 |
| `grep -c 'def test_' test_status_endpoint.py` | >= 6 | 10 |
| `pytest -q` ohne DeprecationWarning | ja | ja, siehe unten |
| ruff check, ruff format --check, pyright, vulture | Exit 0 | alle vier ohne Befund |
| `pytest -q` gesamt | gruen | 420 passed, 1 skipped |

Zur `DeprecationWarning`: `pyproject.toml` erhebt sie ueber `filterwarnings` zum Fehler, ein Lauf mit einer waere also rot. Die eine verbleibende Warnung ist eine `StarletteDeprecationWarning` aus `fastapi/testclient.py` (httpx gegen httpx2), sie stand vor diesem Plan genauso da, sie ist keine `DeprecationWarning` und sie stammt nicht aus unserem Code.

## Threat Flags

Keine neue Angriffsflaeche. Die sechs `mitigate`-Dispositionen des Plans sind umgesetzt, die eine `accept`-Disposition ist unveraendert:

| Threat ID | Umsetzung |
|---|---|
| T-02-111 (Kandidatenantwort vor dem Recheck) | `Candidate` hat vier Felder und keinen Text; `test_the_candidate_model_has_no_text_field` prueft die Feldmenge, `test_a_candidate_carries_no_name_no_path_and_no_text` die tatsaechliche Antwort |
| T-02-112 (`/snippets` als Confused Deputy) | Der Vorfilter ist die erste Handlung des Schnitts, Obergrenze 100 Kennungen, eine fremde Kennung fehlt in der Antwort ohne jede Meldung; drei Tests, darunter der Nutzer ohne Berechtigungszeile |
| T-02-113 (Nutzer-ID im Rumpf) | `extra="forbid"` auf allen drei Rumpfmodellen plus der 400-Handler aus Phase 1; ein eigener Testfall je Endpunkt mit Rumpf |
| T-02-114 (Kanarienvogel in normalen Suchen) | Exakter Vergleich, Grep-Gate gegen eine Enthaltenspruefung, dazu drei Tests: gewoehnliche Suche, Begriff mit dem Wort darin, Begriff mit Leerzeichen aussen herum |
| T-02-115 (Statusendpunkt als Datenquelle) | Nur Zahlen, Marken und Flaggen; die Feldmenge wird als Ganzes geprueft, ein zweiter Test sucht in allen Zeichenketten der Antwort nach einem Schraegstrich; Route mit `access_level` ADMIN |
| T-02-116 (langer Commit blockiert die Suche) | Alle drei Endpunkte gehen ueber `asyncio.to_thread`; jeder Pfad endet im Zweifel in einer leeren Antwort mit `degraded`, keiner wirft |
| T-02-117 (Testhaken als Angriffsflaeche) | unveraendert `accept`: `FINDLING_ARTIFICIAL_DELAY_MS` kann nur verzoegern, wirkt nur in `/snippets`, steht nicht in `info.xml`, Vorgabe 0. Zwei Tests: er kostet Zeit und aendert nichts, und ein unbrauchbarer Wert wird ignoriert |

## Known Stubs

Keine. Die drei Endpunkte sind vollstaendig und lesen echte Daten; die Testsuiten bauen ein echtes Volume mit Wortlisten-Artefakt, Index und Zustandsdatenbank statt einer Attrappe.

Was **planmaessig** fehlt: `search_overfetch` und `search_rounds` aus `config.py` werden von diesem Endpunkt nicht angewendet (siehe Decisions), und `reasons_by_state` bleibt ungelesen, bis Phase 4 die Fehlerliste baut. Beides ist eine Entscheidung, kein unfertiger Code.

## Issues Encountered

- **Der CI-Lauf ist von hier nicht pruefbar.** Alle Gates liefen lokal ueber `uv run` unter Windows. Der `walking-skeleton`-Job ist der erste gemeinsame Lauf beider Haelften und findet nach dem Zusammenfuehren statt. Der Wire-Format-Abgleich oben ist die staerkste Aussage, die ohne ihn moeglich ist: die Antwort wurde durch die laufende Anwendung geschickt und Feld fuer Feld gegen den PHP-Quelltext gelesen.
- **Pydantic verwirft Felder, die der deklarierte Typ nicht kennt.** Die Antwort deklariert deshalb `list[CanaryCandidate | Candidate]` und nicht `list[Candidate]`. Mit dem einfacheren Typ waeren `title` und `snippet` beim Serialisieren stillschweigend verschwunden, und der Kanarienvogel waere im CI als "Titel stimmt nicht" aufgeschlagen, weit weg von der Ursache.
- **Der Nur-Lese-Test des Statusendpunkts ist statisch.** Ein Laufzeitbeweis haette verlangt, dass der Endpunkt seine Verbindung herausgibt, und das waere eine Schnittstelle, die nur fuer einen Test existiert. Stattdessen prueft ein Quelltexttest, dass das Modul `open_read_only` benutzt und `open_store` nicht, plus ein Laufzeittest, dass die Datei nach einer Abfrage Byte fuer Byte dieselbe ist.
- **Windows-Konsole zeigt Umlaute als Fragezeichen.** Betrifft nur die Ausgabe des Wegwerfskripts, nicht die Antwort: die Tests vergleichen Zeichenketten und sind gruen, und die Offsets in der Tabelle oben belegen die Zeichenzaehlung.

## User Setup Required

Keine.

## Next Phase Readiness

- **Fuer 02-12 (PHP-Seite, bereits gemergt):** Der Container liefert ab jetzt genau das Format, das `ExAppService` erwartet. Damit sollte `walking-skeleton` wieder gruen sein; falls nicht, ist die erste Stelle zum Nachsehen `filterCandidates`, weil dort der Kanarienvogel als einziger Kandidat mit `fileId <= 0` durchgelassen wird.
- **Fuer 02-13 (Messung und Konfiguration):** Die Frage, welche Seite `search_overfetch` und `search_rounds` anwendet, ist weiterhin offen und jetzt einseitig beantwortet: dieser Endpunkt wendet sie **nicht** an, die PHP-Seite fuehrt eigene Konstanten. Wer sie zusammenfuehren will, muss beide Stellen anfassen.
- **Fuer 02-14 (CI-Nachweise):** `FINDLING_ARTIFICIAL_DELAY_MS` ist da, wirkt nur in `/snippets`, gilt auch fuer leere Antworten und ist mit zwei Tests belegt. Ein Wert von 3000 laesst den zweiten Aufruf sicher in das 1,5-s-Zeitlimit laufen, waehrend der erste normal antwortet, was genau die Lage ist, die der Nachweis braucht.
- **Fuer Phase 4 (Statusseite):** `GET /status` liefert alle Zahlen, die der Plan nennt. Was die Seite zusaetzlich brauchen wird, ist die Aufschluesselung nach Gruenden (`Store.reasons_by_state`, existiert bereits) und moeglicherweise die Dokumentzahl des Index; beides ist ein Feld mehr in `StatusResponse` und eine Zeile mehr im Feldmengen-Test.
- **Offene Messung:** die Dauer eines vollstaendigen Suchdurchlaufs unter Last. Die Kostenangaben (Suche 0,1 ms, Vorfilter 0,18 ms, 20 Snippets 4,2 ms) stammen aus dem Research; der Lauf in dieser Groessenordnung gehoert laut CONTEXT.md in Phase 5.

## Self-Check: PASSED

- Alle sieben neuen Dateien liegen im Worktree: `api/resources.py`, `api/snippets.py`, `api/status.py`, `tests/conftest.py`, `tests/test_search_endpoint.py`, `tests/test_snippets_endpoint.py`, `tests/test_status_endpoint.py`.
- Alle sieben Commit-Hashes stehen im Log von `gsd/agent-02-11`: `bc9ae6e`, `fd9b0a1`, `f1669ff`, `4119ad2`, `52b8d87`, `eef7395`, `7665049`.
- Genau eine Loeschung im ganzen Plan, `tests/test_search_canary.py` im RED-Commit von Task 1, beabsichtigt und in Deviation 2 begruendet. `git diff --diff-filter=D HEAD~1 HEAD` ist bei jedem anderen Commit leer.
- Arbeitsverzeichnis sauber, keine unbeobachteten Dateien.
- Keine Aenderung an STATE.md, ROADMAP.md oder REQUIREMENTS.md.

---
*Phase: 02-indexkern-und-volltextsuche*
*Completed: 2026-08-31*
