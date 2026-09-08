---
phase: 02-indexkern-und-volltextsuche
plan: 13
subsystem: ci
tags: [kill-resume, idx-02, gate, messung, throttling, rss, tantivy, workflow]

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-02: Store mit counts, reasons_by_state, read_meta und open_read_only"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-06: open_index als einzige Oeffnungsstelle, bench.py als Messstelle"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-10: die eine Poller-Task, die den Kill ueberleben muss"
  - phase: 01-integrationsbeweis
    provides: "01-xx: setup-test-nc, der komplette Aufbau bis zur registrierten ExApp"
provides:
  - "tools/index_status.py: Zaehler, Gruende, aclRows, docs und die Versionsmarken als JSON, ohne Auth-Header"
  - "store/repo.py: Store.acl_rows(), die absolute Zahl neben dem Durchschnitt"
  - ".github/workflows/resilience.yml, Job kill-resume: der Abnahmetest der Phase als Dauergate"
  - ".github/workflows/resilience.yml, Job measurements: Suchlatenz auf gedrosselter Platte und RSS um die erste Suche"
  - "Gemessener Befund: die gedrosselte Platte kostet die Suche nichts, batch_max_bytes bleibt bei 64 MB"
  - "Gemessener Befund: der Kompositaautomat kostet im ausgelieferten Image 43 MB dauerhaft, nicht 23 MB"
affects: [02-14, 03-events-und-ocr, 04-adminstatus, 05-lasttest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Beweise lesen Daten, nie eigene Logzeilen: jede Zahl des Gates kommt aus der Zustandsdatenbank oder aus dem Index"
    - "Zwei Zahlen aus zwei Quellen, sonst vergleicht der Test sich selbst (docs gegen indexed, Container gegen Nextcloud)"
    - "Vor der Messung wird bewiesen, dass die Drosselung wirkt; eine wirkungslose Drossel meldet einen Leerlauf als Last"
    - "Ein Messjob wird nie wegen einer unbequemen Zahl rot, nur wegen einer ausgefallenen Messung"
    - "Jede Warteschleife hat ein hartes Zeitlimit und gibt beim Abbruch die letzten Zaehler aus"

key-files:
  created:
    - backend/src/findling/tools/index_status.py
    - backend/tests/test_index_status.py
    - .github/workflows/resilience.yml
  modified:
    - backend/src/findling/store/repo.py
    - backend/src/findling/config.py

key-decisions:
  - "Die Summe der Zustaende wird gegen die Zustandstabelle der Nextcloud-Seite geprueft statt gegen eine gezaehlte Dateimenge: der Crawl filtert nach Mimetype, eine Dateizahl aus find waere der falsche Nenner gewesen"
  - "Der Crawl-Worker laeuft im Hintergrund, damit die Warteschlange sich fuellt, waehrend der Container sie leert; nur in dieser Ueberlappung existiert der Zustand, in den der Kill fallen muss"
  - "Nach dem Neustart wird die Indexier-Task ueber occ app_api:app:disable/enable wieder scharfgestellt: ein neu gestarteter Prozess ist still, und das Scharfstellen kommt ausschliesslich ueber den AppAPI-Aufruf"
  - "Das Zeitlimit der Leerlaufschleife liegt mit 1200 s ueber QueueMapper::LOCK_TIMEOUT (900 s), weil genau dann die beim Kill gehaltenen Zeilen zurueckkommen; das ist der Pitfall-7-Test"
  - "batch_max_bytes bleibt bei 64 MB, mit beiden p95-Werten als Kommentar an der Konstante"
  - "Store.acl_rows() kommt in repo.py und nicht in das Werkzeug, weil SQL in genau einem Modul steht"

patterns-established:
  - "Ein Kommandozeilenwerkzeug als Messstelle, wenn die HTTP-Route hinter einer Signatur liegt"
  - "Der Fehlschlagfall eines Gates wird mit gefaelschten Zaehlern gegen den echten Schrittcode gefahren, wenn ein CI-Lauf nicht erreichbar ist"

requirements-completed: [IDX-02, IDX-06, IDX-08]

# Metrics
duration: 35min
completed: 2026-08-31
---

# Phase 02 Plan 13: Kill-Resume als Dauergate und die drei offenen Betriebszahlen Summary

**Der Abnahmetest der Phase ist ein eigener Workflow mit drei datenbasierten Zusicherungen statt einer Behauptung, und die drei Zahlen, die bisher Schaetzungen waren, sind gemessen: die auf 2 MB/s gedrosselte Platte kostet die Suche nichts (p95 0,196 ms im Leerlauf gegen 0,166 bis 0,216 ms unter Schreiblast), und der Kompositaautomat kostet im ausgelieferten Image 43 MB statt der angenommenen 23 MB.**

## Performance

- **Duration:** ca. 35 min
- **Started:** 2026-08-31T21:20Z
- **Completed:** 2026-08-31T21:55Z
- **Tasks:** 3 von 3
- **Files modified:** 5 (3 neu, 2 geaendert)

## Accomplishments

- `tools/index_status.py` beantwortet die Frage "wie steht es um diesen Container" ohne signierten Header: die drei Zustandszaehler, die Aufschluesselung nach Gruenden, die Zahl der Rechtezeilen, die fuenf Versionsmarken und die Dokumentzahl des Index. Die Dokumentzahl kommt aus dem Index, alles andere aus der Zustandsdatenbank, und genau dieser Bruch macht den Doppeleintragstest moeglich.
- Eine fehlende Datenbank ist Exit 0 mit Nullwerten. Die Warteschleife des Workflows fragt, bevor das erste Dokument existiert; ein Fehler an dieser Stelle waere ein rotes Gate ohne Befund.
- `resilience.yml` faehrt den Ablauf aus dem RESEARCH woertlich: Korpus vervielfaeltigen, Crawl deterministisch anstossen, warten bis einige Dokumente fertig und andere offen sind, `kill -9`, Neustart auf demselben Volume, warten bis nichts mehr offen ist, drei Zusicherungen mit je eigener Meldung.
- Der Messjob laeuft nur auf Zeitplan und auf Zuruf, beweist erst die Wirksamkeit der Drosselung und misst dann beide Bench-Modi im selben gedrosselten Container, dazu drei RSS-Messungen um die erste und die zweite Suche.
- Alle fuenf Python-Gates lokal gruen: 391 Tests (9 neu), ruff check, ruff format, pyright, vulture.
- Der Fehlschlagfall des Gates ist gefahren worden, nicht behauptet: alle vier Zusicherungen werden rot, wenn man ihnen die passende falsche Zahl gibt (siehe "Der Beweis, dass das Gate rot werden kann").

## Task Commits

1. **Task 1: Statuswerkzeug fuer Zaehler ohne Auth-Header** , RED `3dc1fbb` (test), GREEN `d791894` (feat)
2. **Task 2: Kill-Resume als Dauergate** , `d66dccc` (feat)
3. **Task 3: Messjob fuer Suchlatenz und Speicherbedarf** , `5df09b4` (feat)

## TDD Gate Compliance

Task 1 ist mit `tdd="true"` geplant und lief in der Reihenfolge RED, GREEN. Der RED-Commit steht gegen ein tatsaechlich rotes Ergebnis (`ImportError: cannot import name 'index_status'` beim Sammeln). Eine REFACTOR-Runde war nicht noetig. Task 2 und Task 3 sind ohne `tdd`-Kennzeichnung geplant und haben je einen `feat`-Commit; ihr Pruefmittel ist der Workflow selbst.

## Die Zahlen, die der Plan im SUMMARY verlangt

Alle Werte gemessen im **ausgelieferten Image** (`docker build ./backend`, `python:3.13-slim-trixie`, amd64), Docker 29.5.2, Wortliste `/usr/share/dict/ngerman` mit 276.496 Bestandteilen, 1000 Basisdokumente zu je rund 600 Woertern, 200 Suchen mit 5 ms Abstand.

### Suchlatenz, Drosselrate 2 MB/s (`--device-write-bps <geraet>:2mb`)

| Groesse | `idle` | `under-write` (drei Laeufe) |
|---|---|---|
| Median je Suche | 0,078 ms | 0,107 / 0,111 / 0,111 ms |
| **p95 je Suche** | **0,196 ms** | **0,207 / 0,216 / 0,187 ms** |
| Maximum je Suche | 0,423 ms | 0,460 / 0,418 / 0,325 ms |
| Commits im Messfenster | 0 | 12 |
| Messfenster | 1,06 s | 1,61 bis 1,69 s |

Zum Vergleich derselbe Container **ohne** Drosselung: p95 0,153 ms im Leerlauf, 0,189 ms unter Schreiblast, 19 Commits im Fenster.

Und mit einer haerteren Drossel von 1 MB/s: p95 0,205 und 0,166 ms, 5 Commits im Fenster.

**Die Drosselung wirkt nachweislich.** Gegenprobe im selben Container: `dd bs=1M count=8 conv=fsync` braucht mit `--device-write-bps :2mb` 4,05 s und ohne 0,03 s. Genau diese Probe steht als Schritt im Messjob, weil eine wirkungslose Drossel einen Leerlauf als Last melden wuerde.

### Entscheidung zu `batch_max_bytes`

**Der Wert bleibt bei 64 MB (67.108.864).** Die Begruendung steht als Kommentar an der Konstante in `config.py`, mit beiden p95-Werten daneben.

Der p95 unter Schreiblast auf gedrosselter Platte liegt bei 0,187 bis 0,216 ms, der p95 im Leerlauf auf derselben gedrosselten Platte bei 0,196 ms. Die beiden sind nicht unterscheidbar. Was die Drossel verlangsamt, ist der **Schreiber**, nicht der Leser: dieselbe Messstrecke haelt 12 Commits statt 19, und bei 1 MB/s nur noch 5. Kleinere Stapel wuerden hier nichts kaufen und mehr Segmente und mehr Verschmelzungen kosten.

Ein Nebenbefund, der nicht im Latenzwert steht und deshalb hier: das Messfenster dehnt sich unter der Drossel von 1,06 s auf rund 1,65 s, obwohl die Summe aller Suchzeiten unter 25 ms liegt. Die Zeit geht nicht in die Suche, sondern in die Pausen zwischen den Suchen, waehrend der Schreiber auf seinen gedrosselten `fsync` wartet. Fuer eine Suche im Sekundentakt ist das folgenlos; fuer die Frage "wie schnell laeuft der Erstindex auf einer langsamen Platte" ist es die eigentliche Zahl, und die gehoert in den Lasttest von Phase 5.

### Speicherbedarf um die erste Suche

| Messpunkt | RSS des Containers |
|---|---|
| vor der ersten Suche | 55,11 MiB |
| nach der ersten Suche | 54,83 MiB |
| nach der zweiten Suche | 54,83 MiB |

**Der erwartete Sprung bleibt aus, und der Grund ist bekannt und ohne Bedeutung fuer den Job:** dieser Zweig traegt noch den Durchstich-Endpunkt der Phase 1. Der antwortet mit dem Kanarienvogel und ruehrt die deutsche Analysekette nicht an, also wird der Automat bei der ersten Suche gar nicht gebaut. Der echte Suchpfad entsteht in Plan 02-11, der in derselben Welle laeuft; ab dem ersten Lauf des Messjobs nach dem Zusammenfuehren stehen die drei Werte fuer den produktiven Endpunkt im Joblog, ohne dass jemand den Job dafuer aendern muss.

Damit die Zahl bis dahin nicht fehlt, misst der Job den Preis zusaetzlich **direkt**, im selben Image mit derselben Wortliste:

| Variante | Bauzeit | RSS-Zuwachs waehrend des Baus | dauerhaftes RSS | Durchsatz |
|---|---|---|---|---|
| `full` (276.496 Eintraege) | 0,30 bis 0,33 s | 33,6 MB | **43,0 MB** | 1,7 bis 2,0 Mio. Token/s |
| `nouns` (86.345 Eintraege) | 0,14 s | 0,45 MB | **10,6 MB** | 1,9 Mio. Token/s |

**Das ist ein Befund gegen eine Planannahme.** RESEARCH und die Docstrings von `index/analyzer.py` und `index/open.py` nennen "rund 23 MB, die nie zurueckkommen". Im ausgelieferten Image sind es gemessen **43 MB** dauerhaft, also fast das Doppelte. Die Differenz zum Zuwachs waehrend des Baus (33,6 MB) sind Allokator-Arenen der 276.496 Python-Zeichenketten, die freigegeben, aber nicht an das Betriebssystem zurueckgegeben werden. Fuer die 4-GB-Box heisst das: der deutsche Automat kostet ein gutes Prozent des Gesamtspeichers, und `FINDLING_COMPOUND_DICT=nouns` spart davon gemessen 32 MB. Die Zahl ist damit belegt, aber die Docstrings, die noch 23 MB behaupten, sind **nicht** angefasst worden (siehe Deviation 5).

Nebenbei: die Grundlast des Containers ohne Index und ohne Suche liegt bei 55 MiB, gemessen an derselben Stelle. Das ist die untere Haelfte der 120 bis 180 MB, die das RAM-Budget fuer Python, FastAPI und uvicorn vorsieht.

## Der Beweis, dass das Gate rot werden kann (T-02-131)

Ein Gate, das nie rot war, ist ein Gate, von dem niemand weiss, ob es haelt. Der Plan verlangt dafuer einen Wegwerf-Branch mit einem absichtlich falschen Vergleich. Ein Push ist aus diesem Worktree nicht moeglich (siehe Deviation 1), deshalb wurde der Schritt anders falsifiziert und nicht weggelassen: der **echte Skripttext des Zusicherungsschritts** wurde aus dem Workflow gezogen und gegen gefaelschte Zaehler gefahren, mit einem Attrappen-`occ` und einer Attrappe an der Stelle des Statuswerkzeugs.

| Fall | Exit | Meldung |
|---|---|---|
| ehrlicher Lauf (210 indiziert, 210 Dokumente, 235 zu 235 beurteilt) | 0 | `kill-resume holds: 235 files judged, 210 documents, nothing lost and nothing doubled` |
| Fortschritt verloren (140 nach dem Kill, 150 davor) | 1 | `the restart lost progress: 140 documents are indexed, 150 were before the kill` |
| Zustaende gehen nicht auf (235 gegen 215) | 1 | `the states do not add up: the container judged 235 files, nextcloud handed over 215` |
| Dokument liegt doppelt (214 Dokumente, 210 indiziert) | 1 | `a document lies twice in the index: 214 documents against 210 indexed files` |
| zu wenig Arbeit fuer eine Aussage (62 beurteilt) | 1 | `too little work was done to prove anything: 62 files judged, at least 200 expected` |

Was damit belegt ist: die Arithmetik und die Verzweigungen des Schritts, jede mit ihrer eigenen Meldung. Was damit **nicht** belegt ist: dass der Gesamtlauf gruen wird, also der Aufbau, der Crawl-Anstoss, das Scharfstellen nach dem Neustart und das Leerlaufen der Warteschlange. Das entscheidet der erste Lauf nach dem Push.

## Files Created/Modified

- `backend/src/findling/tools/index_status.py` , `collect`, `documents_in_index`, `index_directory`, `empty_report`, `main`. Der Modul-Docstring nennt beide Gruende fuer die Existenz des Werkzeugs: die HTTP-Route liegt hinter der Signatur, und ein Beweis, der eine selbst geschriebene Logzeile liest, beweist die Logzeile.
- `backend/tests/test_index_status.py` , 9 Tests gegen `tmp_path`: gueltiges JSON und Exit 0, alle Zaehler und Versionen, Nullwerte statt fehlender Schluessel, fehlende Datenbank ohne Fehler, nur lesender Zugriff (Pruefsumme plus statischer Nachweis), Dokumentzahl aus dem Index, fehlender Index, Gruende je Zustand, Ableitung des Indexpfads.
- `backend/src/findling/store/repo.py` , `Store.acl_rows()`, die absolute Zahl neben dem vorhandenen Durchschnitt.
- `backend/src/findling/config.py` , die Entscheidung zu `batch_max_bytes` mit beiden Messwerten als Kommentar an der Konstante.
- `.github/workflows/resilience.yml` , zwei Jobs, 18 Schritte, alle `uses`-Zeilen per Commit-SHA gepinnt.

## Decisions Made

- **Der Nenner der Zustandssumme ist die Nextcloud-Seite, nicht eine gezaehlte Dateimenge.** Der Plan sagt "Summe der Zustaende gleich der Dateizahl". Eine Dateizahl aus `find` waere der falsche Nenner: der Crawl fragt den Dateicache mit einer Mimetype-Allowlist ab, und das Konto traegt zusaetzlich das Skelett, das Nextcloud bei der Installation anlegt. Verglichen werden deshalb die Zustaende des Containers gegen die Zustandstabelle der PHP-Seite: zwei Datenbanken, von zwei Prozessen gefuellt, und genau deshalb ein Vergleich mit Aussage. Dazu die Untergrenze `judged >= CORPUS_FILES`, damit der Vergleich nicht mit 0 gegen 0 gruen wird.
- **Der Crawl laeuft im Hintergrund weiter, waehrend die Warteschleife pollt.** Der Zustand, den der Kill treffen muss, ist die Ueberlappung von Fuellen und Leeren. Liefe der Crawl-Worker im Vordergrund zu Ende, koennte der Container mit 200 kleinen Dateien schon fertig sein, bevor der erste Blick faellt, und der Job waere aus einem Grund rot, der kein Defekt ist.
- **Nach dem Neustart wird die Indexier-Task ausdruecklich wieder scharfgestellt.** Ein frisch gestarteter Prozess ist still: das Scharfstellen kommt aus `enabled_handler`, und der wird von AppAPI gerufen, nicht vom Volume gelesen. AppAPI weiss nichts davon, dass der Prozess hinter dem Port ausgetauscht wurde. Ohne `occ app_api:app:disable` und `enable` warte die Resume-Haelfte auf einen Container, der laeuft, gesund ist und absichtlich nichts tut. In einem echten Deployment startet AppAPI den Container und schickt denselben Aufruf.
- **Das Zeitlimit der Leerlaufschleife liegt bewusst ueber dem Lock-Timeout.** Ein SIGKILL laesst die gerade gehaltenen Zeilen gesperrt zurueck, und die kommen nach `QueueMapper::LOCK_TIMEOUT` von 900 s wieder. Ein gruener Lauf dauert deshalb ueber eine Viertelstunde. Das ist der Preis eines ehrlichen SIGKILL und zugleich der Pitfall-7-Test: mit dem 24-Stunden-Wert des Vorbilds wuerde dieselbe Schleife nie enden.
- **Der Messjob prueft zuerst die Drossel und dann die Suche.** Eine Drossel, die nicht wirkt, produziert eine zweite Leerlaufmessung, die als Lastmessung im Protokoll steht. Die `dd`-Gegenprobe kostet vier Sekunden und macht den Unterschied zwischen einer Zahl und einer Zahl, der man glauben kann.
- **`docs` kommt aus dem Index und nur von dort.** Waeren beide Zahlen aus der Zustandsdatenbank, verglichen sie sich selbst. Der Preis ist, dass das Werkzeug tantivy oeffnet; das laeuft ueber `open_index` (die einzige erlaubte Stelle) und mit leerer Bestandteilsliste, weil hier gezaehlt und nicht gesucht wird und der echte Automat 0,3 s und 43 MB kosten wuerde, alle paar Sekunden.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die CI-Kriterien sind aus dem Worktree nicht auswertbar**

- **Found during:** Task 2 und Task 3
- **Issue:** Beide Tasks haben `gh run list --workflow=resilience.yml ... == success` als Abnahmekriterium und als `<verify><automated>`. Dieser Executor arbeitet in einem Worktree ohne Push; zu diesem Code existiert kein Lauf, und die Datei `resilience.yml` existiert auf keinem Remote-Branch. Laut Projektregel wird so etwas dokumentiert, nicht simuliert.
- **Fix, soweit lokal moeglich:** (a) Die Datei wurde mit einem YAML-Parser gelesen: zwei Jobs, 12 und 6 Schritte, alle `uses`-Zeilen 40-stellige SHAs. (b) Jeder der 14 `run`-Bloecke wurde als Skript herausgezogen und mit `bash -n` geprueft, danach mit `shellcheck:stable` (ohne SC2086/SC2154/SC2153, die auf die von GitHub gesetzten Job-Variablen zeigen): keine Befunde. (c) Der Zusicherungsschritt wurde gegen gefaelschte Zaehler gefahren, siehe die Tabelle oben. (d) Die Werkzeuge, die der Job aufruft, sind lokal gefahren: `index_status` in der Testsuite und auf der Kommandozeile, `index.bench` und `index.analyzer` im echten Image.
- **Files modified:** keine
- **Verification:** **Offen bis zum Orchestrator-Push.** Danach `gh run list --workflow=resilience.yml --limit 1 --json conclusion -q '.[0].conclusion'` pruefen, fuer `measurements` ueber `workflow_dispatch`, weil der Job auf Push nicht laeuft.
- **Committed in:** keiner (Pruefschritt)

**2. [Rule 3 - Blocking] Der Zaehler der Rechtezeilen existierte nicht, und SQL steht in genau einem Modul**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt `aclRows` in der Ausgabe. `Store` kannte nur `acl_rows_per_document()`, also einen Durchschnitt. Ein Lauf, der Dokumente indiziert und keine einzige Rechtezeile schreibt, ist in einem Durchschnitt unsichtbar, weil ein Durchschnitt ueber nichts ebenfalls 0 ist. Die Abfrage im Werkzeug zu schreiben, haette den Modul-Docstring von `repo.py` ("die eine Stelle mit SQL") zur Luege gemacht.
- **Fix:** `Store.acl_rows()` in `repo.py`, mit der Begruendung im Docstring. `store/repo.py` steht nicht in `files_modified` des Plans.
- **Files modified:** `backend/src/findling/store/repo.py`
- **Verification:** `test_the_report_carries_every_counter_and_every_version` prueft `aclRows == 2` fuer zwei Nutzer auf einer Datei; alle fuenf Gates gruen.
- **Committed in:** `d791894`

**3. [Rule 2 - Korrektheit] Der Neustart allein setzt die Indexierung nicht wieder in Gang**

- **Found during:** Task 2
- **Issue:** Der Plan sagt "ExApp mit demselben APP_PERSISTENT_STORAGE neu starten, auf /heartbeat warten" und danach "warten, bis die Queue leer ist". Zwischen beiden fehlt ein Schritt: seit Plan 02-10 startet die Poller-Task **still** und wird ausschliesslich von `enabled_handler` scharfgestellt, also vom AppAPI-Aufruf `PUT /enabled`. Nach `kill -9` und einem manuellen Neustart schickt niemand diesen Aufruf. Die Warteschleife waere in ihr Zeitlimit gelaufen, gegen einen Container, der laeuft, `/heartbeat` beantwortet und absichtlich nichts tut, und der Befund haette wie ein kaputtes Kill-Resume ausgesehen.
- **Fix:** Ein eigener Schritt "Arm the indexing task again" mit `./occ app_api:app:disable findling_backend` und `./occ app_api:app:enable findling_backend`, samt Kommentar, warum er da ist und was ihn in einem echten Deployment ersetzt.
- **Files modified:** `.github/workflows/resilience.yml`
- **Verification:** Steht aus bis zum ersten Lauf; die beiden occ-Kommandos sind AppAPI-Standard und in der Doku belegt, aber in diesem Projekt bisher nicht gefahren. Wenn beim ersten Lauf etwas klemmt, ist dieser Schritt der wahrscheinlichste Ort.
- **Committed in:** `d66dccc`

**4. [Rule 2 - Korrektheit] Eine Gegenprobe auf die Drosselung, bevor irgendetwas gemessen wird**

- **Found during:** Task 3
- **Issue:** `--device-write-bps` braucht das richtige Blockgeraet. Trifft es das falsche, laeuft der Container ungedrosselt, und der Job meldet eine Leerlaufmessung als Lastmessung. Das ist keine schlechte Zahl, das ist eine falsche, und sie waere durch nichts im Protokoll von einer richtigen zu unterscheiden.
- **Fix:** Ein Schritt ermittelt das Geraet ueber `findmnt` und `lsblk -no PKNAME` und faehrt danach `dd bs=1M count=8 conv=fsync` im gedrosselten Container. Dauert das unter zwei Sekunden, bricht der Job ab, bevor er misst. Gemessen auf dieser Maschine: 4,05 s gedrosselt gegen 0,03 s ungedrosselt.
- **Files modified:** `.github/workflows/resilience.yml`
- **Verification:** Lokal gefahren, beide Zahlen oben.
- **Committed in:** `5df09b4`

**5. [Rule 2 - Korrektheit] Der Kompositaautomat wird direkt gemessen, weil der Sprung um die erste Suche in diesem Zweig ausbleibt**

- **Found during:** Task 3
- **Issue:** Der erwartete Sprung von rund 23 MB entsteht, wenn die erste Suche den Automaten baut. Dieser Zweig traegt noch den Kanarien-Endpunkt aus Phase 1, der die Analysekette nicht anfasst; die drei RSS-Werte liegen deshalb gemessen bei 55,11 / 54,83 / 54,83 MiB und beweisen nur, dass die Messung funktioniert. Ein SUMMARY mit drei gleichen Zahlen und ohne den Preis, um den es geht, waere die Erfuellung des Buchstabens und nicht der Absicht.
- **Fix:** Der Messjob faehrt zusaetzlich `python -m findling.index.analyzer` im selben Image, in beiden Wortlistenvarianten. Das ist der Preis der deutschen Sprachqualitaet als direkt gemessene Zahl statt als Differenz zweier RSS-Werte, und er ist ab sofort in jedem Lauf sichtbar.
- **Befund, der eine Planannahme widerlegt:** gemessen 43,0 MB dauerhaftes RSS fuer die volle Liste, nicht 23 MB. Die frugale Variante `nouns` kostet 10,6 MB.
- **Nicht geaendert:** die Docstrings in `index/analyzer.py` und `index/open.py`, die weiterhin "rund 23 MB" nennen, und die RAM-Budgettabelle. Beide Module gehoeren nicht zu diesem Plan, und `index/open.py` kann in dieser Welle von Plan 02-11 gehalten werden; eine Korrektur von hier aus waere ein Konflikt an einer Datei, die dieser Plan nur liest. Der Befund steht hier, mit Zahl und Verfahren, und die Korrektur gehoert in den naechsten Plan, der eines der beiden Module ohnehin anfasst.
- **Files modified:** `.github/workflows/resilience.yml`
- **Committed in:** `5df09b4`

### Abweichungen in den Abnahmekriterien

| Kriterium | Soll | Ist |
|---|---|---|
| `pytest tests/test_index_status.py -q` | Exit 0 | Exit 0, 9 Tests |
| `index_status --db <leer>/state.db` liefert `indexed == 0` | Exit 0 | Exit 0 |
| `grep -c 'open_read_only' index_status.py` | >= 1 | 2 |
| `grep -c 'def test_' test_index_status.py` | >= 6 | 9 |
| ruff check, ruff format --check, pyright, vulture | Exit 0 | alle vier ohne Befund, 391 Tests gruen |
| `grep -c 'kill -9' resilience.yml` | 1 | 1 |
| `grep -c 'index_status' resilience.yml` | >= 4 | 5 |
| `grep -c 'background-job:worker' resilience.yml` | >= 2 | 2 |
| `grep -c 'indexed_before' resilience.yml` | >= 2 | 4 |
| Zaehler vor und nach dem Kill sichtbar | ja | zwei `::group::`-Bloecke plus eine Zeile je Warteschleifendurchgang |
| Fehlschlagfall einmalig provoziert | ja | siehe eigener Abschnitt, vier Faelle, alle rot mit eigener Meldung |
| `grep -c 'device-write-bps' resilience.yml` | >= 1 | 3 |
| `grep -c 'docker stats' resilience.yml` | >= 3 | 4 |
| `grep -c 'index.bench' resilience.yml` | >= 2 | 2 |
| alle `uses`-Zeilen per SHA gepinnt | ja | drei Zeilen, alle 40-stellige SHAs |
| `gh run list --workflow=resilience.yml` = success | success | siehe Deviation 1 |
| `grep -cE '^  [a-z-]*:$' resilience.yml` | 2 | **4**, siehe unten |

**Zum letzten Kriterium.** Das Muster trifft nicht nur Jobnamen, sondern jeden Schluessel mit zwei Leerzeichen Einrueckung ohne Wert, also auch die Ausloeser `push:` und `schedule:`. Dieselbe Zeile liefert auf der bestehenden `integration.yml` **3** fuer deren zwei Jobs. Die Absicht des Kriteriums (der Workflow fuehrt genau zwei Jobs) ist erfuellt und wurde mit einem YAML-Parser geprueft: `jobs` hat exakt die zwei Schluessel `kill-resume` und `measurements`. Die Einrueckung so zu verbiegen, dass der Grep passt, haette die Datei gegen die Konvention der drei vorhandenen Workflows gestellt, ohne irgendetwas sicherer zu machen.

---

**Total deviations:** 5 auto-fixed (3x Rule 2, 2x Rule 3)
**Impact on plan:** Kein Scope-Zuwachs. Deviation 3 schliesst eine Luecke im vorgegebenen Ablauf, ohne die der Beweis nicht funktioniert haette; Deviation 5 ist ein Messbefund, der eine Zahl aus dem RESEARCH fast verdoppelt.

## Issues Encountered

- **Kein CI-Lauf moeglich.** Der wiederkehrende Befund dieser Phase, siehe Deviation 1. Was hier zusaetzlich daran haengt: `resilience.yml` ist ein **neuer** Workflow, den GitHub erst kennt, wenn er auf einem Branch liegt. Der erste Lauf entsteht mit dem Push des Orchestrators, und `measurements` laeuft dabei nicht mit, weil der Job auf Push ausgeschlossen ist. Er braucht einen `workflow_dispatch`.
- **Ein gruener Lauf dauert ueber eine Viertelstunde.** Der SIGKILL laesst die gehaltenen Queue-Zeilen gesperrt zurueck, und die kommen erst nach 900 s wieder. Das steht als Absatz im Kopfkommentar des Workflows, damit es niemand fuer ein haengendes Gate haelt und den Job leiser stellt.
- **Der Messjob und der Suchpfad laufen in verschiedenen Zweigen.** Die RSS-Messung um die erste Suche ist gegen den Endpunkt gefahren, den dieser Zweig hat, und das ist noch der Kanarienvogel aus Phase 1. Die Messstelle ist richtig, das Messobjekt kommt aus Plan 02-11.
- **Die beiden occ-Kommandos zum Scharfstellen sind hier zum ersten Mal im Projekt.** `app_api:app:disable` und `app_api:app:enable` sind AppAPI-Standard, aber weder in Phase 1 noch bisher in Phase 2 gefahren worden. Sollte der erste Lauf klemmen, ist das die erste Stelle, an der zu schauen ist.
- **Zwei Zahlen des Plans widersprechen der Messung.** Die 23 MB des Automaten (gemessen 43 MB) und die Erwartung, dass eine gedrosselte Platte den p95 der Suche verschlechtert (gemessen: sie tut es nicht, sie verlangsamt den Schreiber). Beide Male ist die Messung im ausgelieferten Image gefahren und beide Male steht das Verfahren daneben.

## Threat Flags

Keine neue Angriffsflaeche. Die vier `mitigate`-Dispositionen des Plans sind umgesetzt, die eine `accept`-Disposition ist unveraendert:

| Threat ID | Umsetzung |
|---|---|
| T-02-131 (ein Gate, das nie rot wird) | Vier Fehlschlagfaelle gegen den echten Skripttext gefahren, jeder rot mit eigener Meldung, Tabelle im eigenen Abschnitt. Der ganze Lauf im Wegwerf-Branch bleibt offen, siehe Deviation 1 |
| T-02-132 (Testzugangsdaten im Workflow) | unveraendert `accept`. Der Job `kill-resume` braucht ueberhaupt keine Zugangsdaten mehr: jede Frage geht ueber `occ` oder ueber das Kommandozeilenwerkzeug, keine einzige ueber eine authentifizierte HTTP-Route. Nur `EXAPP_SECRET` bleibt, ein Wegwerfwert einer Instanz, die mit dem Runner verschwindet |
| T-02-133 (endlos laufende Warteschleifen) | Drei Schleifen, jede mit hartem Zeitlimit aus einer benannten Job-Variablen (`MIDRUN_TIMEOUT`, `DRAIN_TIMEOUT`) und mit Ausgabe der letzten Zaehler beim Abbruch |
| T-02-134 (Beweis stuetzt sich auf ein Log) | Jede Zahl kommt aus `index_status` (Zustandsdatenbank plus Index) oder aus `occ findling:index` (Nextcloud-Datenbank). Keine Zusicherung liest eine Logzeile dieses Projekts |
| T-02-135 (Suche haengt auf langsamer Platte) | Beide Bench-Modi im gedrosselten Container, Drossel vor der Messung nachgewiesen, Entscheidung zu `batch_max_bytes` mit beiden p95-Werten an der Konstante |
| T-02-136 (Speicherbedarf unbemerkt verdoppelt) | Drei RSS-Messungen um die erste und die zweite Suche, dazu die direkte Messung des Automaten in beiden Varianten. Der Befund ist, dass die angenommene Zahl bereits um 20 MB danebenlag |

## Known Stubs

Keine. Das Werkzeug und beide Jobs sind vollstaendig. Was noch fehlt, fehlt planmaessig auf der anderen Seite: der produktive Suchpfad aus Plan 02-11, ohne den die RSS-Messung um die erste Suche drei praktisch gleiche Zahlen liefert. Die Messstelle steht, das Messobjekt kommt.

## User Setup Required

Keine. Nach dem Zusammenfuehren einmal `gh workflow run resilience.yml` (oder der Knopf in der Oberflaeche), damit der Messjob seine Zahlen zum ersten Mal in der CI produziert; auf Push laeuft er absichtlich nicht.

## Next Phase Readiness

- **Fuer 02-14 (Suchbeweis):** `integration.yml` ist von diesem Plan nicht angefasst worden, weder Job noch Zeile. Der Kill-Resume-Beweis liegt in einem eigenen Workflow, wie im Plan begruendet.
- **Fuer Phase 3 (Events und OCR):** `index_status` ist die Messstelle, an der ein OCR-Lauf sichtbar wird: `reasons.skipped.no_text_layer` ist genau die Liste, die Phase 3 abarbeitet, und sie steht in jeder Ausgabe. Der Hinweis aus Pitfall 7, dass OCR den Lock-Timeout anhebt, trifft direkt auf `DRAIN_TIMEOUT` in `resilience.yml`: steigt der eine, muss der andere mitwachsen.
- **Fuer Phase 4 (Statusseite):** Die Aufschluesselung nach Gruenden liegt fertig vor, in denselben Schluesseln, aus denen die Seite ihre Fehlerliste baut.
- **Fuer Phase 5 (Lasttest):** Zwei Zahlen sind jetzt belegt und eine ist neu offen. Belegt: die Suche kostet auf gedrosselter Platte nichts, der Automat kostet 43 MB. Offen: wie lange der Erstindex auf einer gedrosselten Platte **braucht**. Der Messjob sieht die Antwort bereits als Nebenbefund (12 statt 19 Commits im Fenster, bei 1 MB/s nur noch 5), misst sie aber nicht als Durchsatz.
- **Offene Anschlussstelle, hier bewusst nicht entschieden:** Ob `FINDLING_COMPOUND_DICT=nouns` die Vorgabe auf einer 2-GB-Box werden soll. Die Ersparnis ist mit 32 MB jetzt beziffert, der Qualitaetsverlust mit 12 von 16 Komposita gegen 14 von 16 ebenfalls; die Entscheidung gehoert zu den Standardwerten von Phase 5 und nicht in einen Messplan.

## Self-Check: PASSED

- Alle drei neuen und beide geaenderten Dateien liegen im Worktree: `backend/src/findling/tools/index_status.py`, `backend/tests/test_index_status.py`, `.github/workflows/resilience.yml`, `backend/src/findling/store/repo.py`, `backend/src/findling/config.py`.
- Alle vier Commits im Log von `gsd/agent-02-13`: `3dc1fbb`, `d791894`, `d66dccc`, `5df09b4`.
- Keine Loeschung in einem der vier Commits (`git diff --diff-filter=D` je leer).
- Keine Aenderung an STATE.md, ROADMAP.md, REQUIREMENTS.md oder an `backend/src/findling/api/search.py`.
- Abschliessender Lauf: `uv run pytest -q` 391 passed, 1 skipped; `ruff check`, `ruff format --check`, `pyright` und `vulture --min-confidence 80` ohne Befund.

---
*Phase: 02-indexkern-und-volltextsuche*
*Completed: 2026-08-31*
