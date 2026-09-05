---
phase: 06-semantische-suche
plan: 07
subsystem: backend
tags: [zweitspur, backfill, warteschlange, paritaet, loeschweg, d-15, d-21, kind-rank, plattenpause]

# Dependency graph
requires:
  - phase: 06-semantische-suche
    provides: "06-04: replace_chunks, drop_vectors, forget_all, chunks_of und open_vectors"
  - phase: 06-semantische-suche
    provides: "06-05: chunk_spans, make_splitter, embed_passages, to_int8 und das Verdikt embedding_unavailable"
  - phase: 06-semantische-suche
    provides: "06-06: die Leseseite, die den Bestand ohne weitere Codeaenderung findet, sobald er gefuellt ist"
  - phase: 03-aktualit-t-und-ocr
    provides: "die OCR-Zweitspur als strukturelles Vorbild: _goes_to_the_ocr_track, _hand_over, die Reihenfolge 3b"
  - phase: 02-store-und-index
    provides: "stored_body als die eine gespeicherte Kopie des Textes, und die Ordnung Commit, Verdikt, Quittierung"
provides:
  - "nc/queue.py::KIND_EMBED und die sechste Auftragsart in KINDS"
  - "QueueMapper: KIND_EMBED in KINDS, LOCK_TIMEOUTS (1800 s) und KIND_RANK (unten, neben acl)"
  - "QueueService: KIND_BATCH[embed] = 8, hergeleitet aus der gemessenen Rate"
  - "config.py: EMBED_LOCK_TIMEOUT_SECONDS und EMBED_CLAIM_BATCH als Spiegel mit Paritaetstest"
  - "poller: _goes_to_the_embedding_track, _needs_vectors, _embed_the_body, _wire_the_second_track"
  - "poller: _hand_over mit der Auftragsart als Argument, zwei Aufrufe in Schritt 3b"
  - "writer: free_bytes und disk_is_tight als der eine Plattenplatzvorbehalt fuer Index und Vektorbestand"
  - "store/vectors.py::VectorSink, die Gestalt, die der Loeschweg annimmt"
  - "der Loeschweg an vier Stellen: drop_document, tombstone, reset_for_reindex, replace_chunks"
affects: [06-08 Statusseite und Deckungsgrad, 06-09 Snippet fuer rein semantische Treffer, 06-11 Lasttest und A5]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine zweite Spur bekommt ihre eigene Auftragsart auf beiden Seiten der Warteschlange, nie einen Sonderfall in einer bestehenden"
    - "Ein Lock-Timeout wird nicht aus der Arbeit hergeleitet, die es deckt, sondern aus der laengsten Arbeit, mit der es einen Anspruch teilt"
    - "Ein billiger Ausgang, der ein Endverdikt quittiert, muss die Frage der Zweitspur trotzdem stellen, sonst macht er einen verlorenen Uebergang dauerhaft"
    - "Ein Plattenplatzvorbehalt gehoert an das Objekt, das das Verzeichnis kennt; zwei Kopien davon sind zwei Antworten ueber einen Datentraeger"
    - "Ein Verdikt, das nichts ueber den Dateizustand sagt, wird nie an Store.record gereicht"

key-files:
  created:
    - backend/tests/test_embedding_track.py
  modified:
    - backend/src/findling/worker/poller.py
    - backend/src/findling/index/writer.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/store/vectors.py
    - backend/src/findling/nc/queue.py
    - backend/src/findling/config.py
    - php/lib/Db/QueueMapper.php
    - php/lib/Service/QueueService.php
    - backend/tests/test_config.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_rrf_fusion.py
    - .planning/phases/06-semantische-suche/deferred-items.md

key-decisions:
  - "EMBED_LOCK_TIMEOUT_SECONDS = 1800, nicht aus der Einbettungsarbeit hergeleitet: ein embed-Auftrag reist im selben Anspruch wie eine volle OCR-Charge und wartet hinter ihr, also braucht er das Timeout der laengsten Art, mit der er sich einen Anspruch teilen kann"
  - "EMBED_CLAIM_BATCH = 8, hergeleitet aus der Passdauer und nicht aus dem RAM: die Aktivierungsspitze setzt EMBED_BATCH_SIZE = 2, nicht die Chargengroesse der Warteschlange; 8 Zeilen sind rund 18 s im schlechtesten hergeleiteten Fall gegen 73 s bei 32"
  - "KIND_RANK stellt embed auf 0, neben acl: embed verdraengt nichts, wird aber auch von einer Rechteaenderung nicht verdraengt, und dafuer schreibt der embed-Zweig die Rechte seiner Zeile (bug audit M1)"
  - "Die vier Endzustaende eines embed-Auftrags sind benannte Konstanten in poller.py und werden NIE an Store.record gereicht: ein Dokument ohne Vektoren ist trotzdem indexiert (D-15), und ein Verdikt dort haette es aus dem Index gemeldet"
  - "_needs_vectors fragt den Vektorbestand und nicht die Zustandsdatenbank: das gespeicherte Verdikt sagt indexiert und ueber Vektoren nichts, und eine Spalte dafuer waere eine zweite Wahrheit"
  - "Der Schnellpfad (unveraenderte Bytes) und der Umbenennungspfad uebergeben nur, wenn die Datei noch keine Vektoren hat; der gewoehnliche Uebergang fragt das nicht, weil ein frischer Text die alten Vektoren falsch macht"
  - "Der Plattenplatzvorbehalt zieht auf den IndexBatchWriter (free_bytes, disk_is_tight), damit Index und Vektorbestand ein Verzeichnis gegen eine Zahl fragen"
  - "VectorSink ist ein Protocol in store/vectors.py: repo.py wird von vectors.py importiert und kann deshalb zur Laufzeit nicht zurueckimportieren, also nimmt der Loeschweg die Gestalt und nie die Sache"
  - "Store.attach_vectors ist ein Setter und kein Konstruktorargument, weil open_store das Volumeverzeichnis anlegt und open_vectors keines anlegen darf (Gate A)"

patterns-established:
  - "Wenn eine neue Auftragsart eine Spur eroeffnet, wird zuerst gefragt, welcher bestehende Ausgang sie still verschluckt, bevor die Spur selbst gebaut wird"
  - "Eine Zahl, die aus einem Messbericht kommt, nennt die Kombination, den Perzentil und den Sicherheitsfaktor, mit dem sie gerechnet wurde, und nie nur das Ergebnis"

requirements-completed: [SEM-01]

# Metrics
duration: 38min
completed: 2026-09-05
---

# Phase 6 Plan 07: Embedding-Zweitspur und Löschweg Summary

**Der ganze Bestand bekommt jetzt Vektoren, ohne dass eine einzige Datei ein zweites Mal geladen wird: eine sechste Auftragsart auf beiden Seiten der Warteschlange, ein Zweitspurzweig nach dem Vorbild der OCR-Spur, dessen einziger struktureller Unterschied die fehlende Download-Zeile ist, und ein Löschweg, der die Vektoren an vier Stellen mitnimmt. Zwei Löcher hat der Bau selbst aufgedeckt: ein verlorener Übergang wäre nie wiederholt worden, weil der Schnellpfad ihn verschluckt, und eine Rechteänderung hätte eine wartende Embedding-Zeile mitgenommen.**

## Performance

- **Duration:** rund 38 min
- **Started:** 2026-09-05T07:45:52Z
- **Completed:** 2026-09-05T08:24:00Z
- **Tasks:** 3 von 3
- **Files modified:** 12 (1 neu, 11 geändert)

## Accomplishments

- **Die Zweitspur ist eine Spur und kein Schritt, und der Unterschied ist eine Zeile, die fehlt.** `_read_the_scan` ruft `self._fetch_file(job)`; `_embed_the_body` tut das nicht und darf es nicht, weil `body_de` die einzige gespeicherte Kopie des extrahierten Textes im ganzen System ist. Zwei Tests halten das fest: einer zählt die Byte-Abrufe eines Durchgangs, der eingebettet hat (null), der andere liest den Quelltext des Zweigs und erwartet weder `_fetch_file` noch `_stream_into` darin.
- **Zwei Löcher sind gefunden worden, bevor sie entstehen konnten, und beide gehören zur selben Familie.** Der Schnellpfad quittiert eine Datei, deren Bytes sich nicht geändert haben, ohne einen einzigen Schreibvorgang. Für die OCR-Spur ist das harmlos, weil deren Verdikt `skipped(no_text_layer)` lautet und `is_unchanged` daran scheitert. Für die Embedding-Spur lautet das Verdikt `indexed`, also hätte der Schnellpfad jeden wiederzugestellten Auftrag quittiert, und ein Übergang, der Nextcloud nicht erreicht hat, wäre nie wiederholt worden: wörtlich der CR-02-Defekt eine Spur weiter. Das zweite Loch liegt in `KIND_RANK`: eine Rechteänderung, die auf eine wartende Embedding-Zeile trifft, hätte sie entweder verdrängt (Vektoren für immer weg) oder wäre von ihr verschluckt worden (Freigabe für immer weg).
- **Das Paritätsband hat jetzt eine Gegenprobe.** Der bestehende OCR-Test liest zwei Zahlen aus den PHP-Quellen und vergleicht sie. Was er nicht belegt hat, ist, dass er das noch kann: ein Regex, der nicht mehr trifft, hätte am `assert is not None` scheitern müssen, aber niemand hat das je gefahren. Ein neuer Fall kopiert die PHP-Datei, ändert eine Zahl darin und verlangt, dass derselbe Leser widerspricht.
- **Der Löschweg ist an vier Stellen verdrahtet und an sechs Fällen belegt**, darunter die zwei, die kein Löschen sind: eine Instanz ohne Vektorbestand läuft unverändert durch, und ein Bestand, der nicht mehr antwortet, kostet eine Warnung mit dem Typnamen und nie die Löschung des Dokuments.

## Task Commits

1. **Task 1 (RED): Das Gatter über der Auftragsart embed und ihrem Paritätsband** - `359fd2c` (test)
2. **Task 1 (GREEN): Beide Hälften der Warteschlange kennen embed** - `3858e50` (feat)
3. **Zwischendurch, auf Zuruf des Orchestrators: ruff I001 aus 06-06** - `721bef3` (fix)
4. **Task 2/3 (RED): Das Gatter über der Zweitspur und dem Löschweg** - `6d265da` (test)
5. **Task 2 (GREEN): Die Zweitspur, Backfill ohne zweiten Download** - `2c544bf` (feat)
6. **Task 3 (GREEN): Der Löschweg nimmt die Vektoren an allen vier Stellen mit** - `af9be03` (feat)

## Files Created/Modified

- `backend/tests/test_embedding_track.py` - 30 Fälle gegen einen echten Vektorspeicher, einen echten Index und eine echte Zustandsdatenbank; die einzigen Attrappen sind Chunker und Modell
- `backend/src/findling/worker/poller.py` - `KIND_EMBED`-Zweig, `_goes_to_the_embedding_track`, `_needs_vectors`, `_embed_the_body`, `_wire_the_second_track`, `_embed_ready`, `_DiskTight`, `PassageEmbedder`, `Chunker`, die drei neuen Konstruktorargumente, `_hand_over` mit Auftragsart, zwei Aufrufe in Schritt 3b und `RoundResult.embedded`
- `backend/src/findling/index/writer.py` - `free_bytes` und `disk_is_tight` als der geteilte Vorbehalt, das Vektorargument am Konstruktor, der Vektorabwurf in `drop_document` samt der allgemeinen Form der Regel, plus `from __future__ import annotations`
- `backend/src/findling/store/repo.py` - `attach_vectors`, `_forget_vectors_of`, `_forget_all_vectors`, die Verdrahtung in `tombstone` und `reset_for_reindex`
- `backend/src/findling/store/vectors.py` - `VectorSink` als Protocol mit genau zwei Aufrufen
- `backend/src/findling/nc/queue.py` - `KIND_EMBED` und die sechste Auftragsart in `KINDS`
- `backend/src/findling/config.py` - `EMBED_LOCK_TIMEOUT_SECONDS` und `EMBED_CLAIM_BATCH` mit der Herleitung daneben
- `php/lib/Db/QueueMapper.php` - Konstante, `KINDS`, `LOCK_TIMEOUTS`, `KIND_RANK`, jede mit ihrer Begründung
- `php/lib/Service/QueueService.php` - `KIND_BATCH[embed] = 8` mit der Rechnung daneben
- `backend/tests/test_config.py` - der erweiterte Paritätstest, die gestellte Gegenprobe und die Invariante der Chargendauer
- `backend/tests/test_queue_client.py` - die Auftragsart über die Grenze, der Requeue mit ihr, die geschlossene Liste gegen `QueueMapper::KINDS` und die Prüfung im Controller
- `backend/tests/test_rrf_fusion.py` - eine Leerzeile, Zuruf des Orchestrators, siehe unten

## Die gewählten Zahlen und woher sie kommen

| Einstellung | Wert | Herkunft |
|---|---|---|
| `QueueMapper::LOCK_TIMEOUTS[embed]` | 1.800 s | **nicht** aus der Einbettungsarbeit: das Timeout der längsten Art, mit der sich ein embed-Auftrag einen Anspruch teilt (OCR) |
| `QueueService::KIND_BATCH[embed]` | 8 | 8 mal 2,3 s = rund 18 s Passdauer im schlechtesten hergeleiteten Fall, ein Prozent des Locks |
| abgeleitet: Zeit je Dokument | 0,29 s auf dem Läufer | 1.024 Token (D-01) gegen 3.581 Token/s p95, Charge 2 / Sequenz 512, aarch64 (Welle-0-Bericht, 05.09.2026) |
| abgeleitet: Sicherheitsfaktor | 8 | die Reserve, die derselbe Bericht der Zielbox gegenüber dem Läufer zubilligt (5,9 bis 8,0) |
| `KIND_RANK[embed]` | 0 | neben `acl`: verdrängt nichts und wird von einer Rechteänderung nicht verdrängt |

## Decisions Made

- **Das Lock-Timeout folgt nicht aus der Arbeit, die es deckt.** Die naheliegende Rechnung ist die des OCR-Vorbilds: Zeit je Auftrag mal Chargengröße plus Reserve, hier rund 18 s, also wäre ein Timeout von 300 s schon üppig gewesen und hätte nach einem harten Kill fünf Minuten statt einer halben Stunde gekostet. Sie ist trotzdem falsch, weil ein Anspruch nicht einer Art gehört: `QueueService::claim` läuft in einem Durchgang über alle Arten, also kann eine embed-Zeile im selben Anspruch wie eine volle OCR-Charge herausgehen und wartet dann hinter ihr. Ein aus 18 s hergeleitetes Timeout hätte genau diese Zeilen ein zweites Mal ausgegeben, während ein Worker rechtmäßig noch am Durchgang ist, also `failed(repeatedly_stuck)` aus T-03-503 für die billigste Zeilenart im System. 1.800 hat außerdem eine zweite Eigenschaft: `max(LOCK_TIMEOUTS)` bewegt sich nicht, also weitet der konservative Zweig von `refreshExisting` sein Schmutzfenster für keine andere Art.
- **Die Chargengröße ist keine RAM-Frage, obwohl der Plan sie so stellt.** Der Plan leitet die Zahl aus dem RAM-Hebel her. Gemessen an der Umsetzung stimmt das nicht: die Aktivierungsspitze setzt `EMBED_BATCH_SIZE = 2` (06-05), jede Zeile wird für sich eingebettet, und das Modell chargiert die Chunks eines Dokuments intern. Eine größere Charge der Warteschlange fügt der Spitze kein Byte hinzu. Was sie wirklich entscheidet, ist die Länge eines Durchgangs, und damit die Latenz jeder Art über ihr: eine Rechteänderung überholt einen Inhaltsstau, indem sie nicht dahinter beansprucht wird (D-04), aber sie wartet den laufenden Durchgang trotzdem ab. 8 Zeilen sind rund 18 s, 32 wären 73 s. Die Herleitung steht in dieser Form am PHP-Konstantenblock.
- **`embed` steht auf Rang 0, neben `acl`, und das ist die Entscheidung mit den meisten Folgen.** Drei Fälle waren zu prüfen. Ein eigener Rang unterhalb von `acl` hätte bedeutet, dass eine Rechteänderung die wartende Embedding-Zeile verdrängt: die acl-Zeile läuft, wird quittiert, und die Datei hat für immer keine Vektoren, weil der Schnellpfad sie danach nie wieder übergibt. Rang 0 löst das, erzeugt aber den umgekehrten Fall: die acl-Zeile wird von der embed-Zeile aufgesogen, und die Freigabe erreicht den Vorfilter nie. Beantwortet ist das mit einem Muster, das in derselben Datei schon steht: der embed-Zweig schreibt die Rechte seiner Zeile, genau wie es der Ausgang für unveränderte Dateien tut (bug audit M1). Der Auftrag trägt die aktuelle Nutzerliste, weil `describe` sie zur Anspruchszeit auflöst, und es ist ein deklarativer Schreibvorgang gegen eine Datei, die der Durchgang ohnehin in der Hand hat.
- **Die vier Endzustände eines embed-Auftrags sind Namen und keine Dateizustände.** `Store.record` zu rufen wäre der naheliegende Weg gewesen und hätte die Phase gekostet: das Verdikt hätte `indexed` überschrieben, die Datei wäre auf der Statusseite aus dem Index verschwunden, der Deckungsgrad gefallen, und `is_unchanged` hätte für immer `False` geantwortet, also einen vollständigen Download je Datei je Crawl. Die vier Namen leben deshalb in `poller.py`, so wie `embedding_unavailable` in `embed/model.py` lebt und aus demselben Grund (06-05): ein Dokument, dessen Vektoren nicht geschrieben werden konnten, ist indexiert und bleibt es (D-15).
- **`_needs_vectors` fragt den Bestand und nicht die Zustandsdatenbank.** Der Bestand ist die einzige Stelle, die es weiß. Das gespeicherte Verdikt sagt `indexed` und über Vektoren nichts, und eine Spalte dafür wäre eine zweite Wahrheit über dieselbe Sache, die am ersten verlorenen Schreibvorgang auseinanderläuft. Der Preis ist eine indizierte Abfrage je unveränderter Datei, und sie fällt nur an, solange das Einbetten eingeschaltet ist.
- **Der Umbenennungspfad übergibt nur, wenn Vektoren fehlen.** Zuerst war er unbedingt gebaut, weil er ein Fenster schließt (eine Umbenennung überholt eine Embedding-Zeile). Das hätte aber jede Umbenennung eine erneute Einbettung eines unveränderten Textes gekostet. Mit `_needs_vectors` ist beides erfüllt: das Fenster bleibt zu, und ein Text, der sich nicht geändert hat, wird nicht noch einmal gerechnet. Der gewöhnliche Übergang fragt bewusst nicht, weil dort der Text frisch ist und die alten Vektoren damit falsch sind.
- **Der Plattenplatzvorbehalt zieht auf den Writer.** Der Vektorbestand wird in Schritt 1 geschrieben, lange vor dem Commit, also braucht der Zweig eine eigene Möglichkeit zu sagen "nicht in diesem Durchgang". Die Zahl und das Verzeichnis dafür aus den Einstellungen ein zweites Mal zu holen wäre zwei Antworten über einen Datenträger gewesen. `IndexBatchWriter.disk_is_tight()` ist jetzt die eine Frage, `flush` und die Zweitspur stellen sie beide, und der Zweig antwortet mit `_DiskTight`, was `_abort` in genau die bestehende Plattenpause führt.
- **`VectorSink` liegt in `vectors.py` und nicht in `repo.py`.** Die Importrichtung entscheidet: `vectors.py` importiert `repo.enable_wal`, also kann `repo.py` zur Laufzeit nicht zurückimportieren. Der Löschweg nimmt deshalb die Gestalt und nie die Sache, unter `TYPE_CHECKING`, und ein Test kann eine Attrappe hineingeben, die kracht.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Fehler] Ein verlorener Übergang wäre nie wiederholt worden**

- **Found during:** Task 2, durch den Testfall über den verlorenen Requeue
- **Issue:** Der Plan verlangt: "ein Abbruch genau dort fuehrt dazu, dass die Zeilen nach dem Lock-Timeout erneut kommen und erneut uebergeben werden". Sie kommen erneut, aber sie wurden nicht erneut übergeben. Der Schnellpfad in `_handle` fragt `is_unchanged`, und für eine Datei, die der erste Durchgang als `indexed` mit demselben Inhalts-Hash aufgeschrieben hat, ist die Antwort `True`: die Zeile wird ohne einen einzigen Schreibvorgang quittiert und verlässt die Warteschlange. Die OCR-Spur ist davon nicht betroffen, weil ihr Übergangsverdikt `skipped(no_text_layer)` lautet und `is_unchanged` `state = 'indexed'` verlangt. Für die Embedding-Spur ist das Verdikt gerade `indexed`, also hätte jeder verlorene Übergang das Dokument dauerhaft ohne Vektoren gelassen, mit keinem Zähler, der sich bewegt. Das ist wörtlich der CR-02-Befund aus Phase 3, eine Spur weiter.
- **Fix:** `_needs_vectors(file_id)` fragt den Vektorbestand, und der Schnellpfad übergibt statt zu quittieren, wenn die Datei nichts hat. Derselbe Helfer ersetzt im Umbenennungspfad die zuerst gebaute unbedingte Übergabe.
- **Files modified:** backend/src/findling/worker/poller.py
- **Verification:** `test_a_lost_handover_is_repeated_and_does_not_end_the_pass` war rot und ist grün; der Fall fährt zwei Durchgänge, im ersten scheitert der Requeue.
- **Committed in:** `2c544bf`

**2. [Rule 2 - Fehlende kritische Funktion] Eine Rechteänderung hätte eine wartende Embedding-Zeile gekostet, oder umgekehrt**

- **Found during:** Task 1, beim Entwurf von `KIND_RANK`
- **Issue:** Der Plan sagt nur, embed gehöre "hinter die bestehenden Arten". Beide Auslegungen davon haben einen Verlust: ein eigener Rang unter `acl` lässt eine Rechteänderung die Embedding-Zeile verdrängen (Datei ohne Vektoren, dauerhaft, weil der Schnellpfad sie danach quittiert), gleicher Rang wie `acl` lässt die Embedding-Zeile die Rechteänderung aufsaugen (eine neue Freigabe erreicht den Vorfilter nie, also findet der neu berechtigte Nutzer die Datei nicht).
- **Fix:** Gleicher Rang wie `acl`, und der embed-Zweig schreibt `replace_acl` mit der Nutzerliste seiner Zeile, nach dem Muster des Ausgangs für unveränderte Dateien (bug audit M1). Der Grund steht an `KIND_RANK` und an der Aufrufstelle.
- **Files modified:** php/lib/Db/QueueMapper.php, backend/src/findling/worker/poller.py
- **Verification:** `test_an_embed_job_writes_the_permissions_of_its_row` gibt einer Datei zuerst nur `alice` und fährt dann einen embed-Auftrag mit `carol` dabei; der Vorfilter lässt `carol` danach durch.
- **Committed in:** `3858e50`, `2c544bf`

**3. [Rule 2 - Fehlende kritische Funktion] Ein Modell, das zu wenige Vektoren liefert, hätte falsche Offsets gespeichert**

- **Found during:** Task 2
- **Issue:** `embed_passages` gibt eine Liste zurück, und der Plan nennt keinen Fall, in dem ihre Länge nicht der Chunkzahl entspricht. Ein `zip` ohne `strict` hätte die überzähligen Spans stillschweigend fallen lassen, ein `zip(strict=True)` hätte den Durchgang mit einer Ausnahme beendet. Beides ist falsch: die erste Variante speichert ein halbes Dokument, und ein halbes Dokument ist schlimmer als keines, weil die Passagen unter den Offsets anderer Passagen landen und nichts im System das je bemerkt.
- **Fix:** Eine Längenprüfung vor dem Schreiben, ein vierter benannter Endzustand `embedding_incomplete`, eine Warnzeile mit zwei Zahlen und ohne Inhalt, und die Zeile wird quittiert. `zip(..., strict=True)` bleibt darunter stehen, jetzt als eine Zusicherung, die nicht mehr auslösen kann.
- **Files modified:** backend/src/findling/worker/poller.py
- **Verification:** `test_a_model_that_answers_short_writes_nothing` und `test_every_ending_of_an_embed_job_has_a_name_of_its_own`.
- **Committed in:** `2c544bf`

**4. [Rule 3 - Blockierend] `index/writer.py` hatte kein `from __future__ import annotations`**

- **Found during:** Task 2, beim ersten Lauf
- **Issue:** Der neue Konstruktorparameter `vectors: VectorSink | None` steht unter `TYPE_CHECKING`, also existiert der Name zur Laufzeit nicht. Ohne die Zukunftsimportzeile werden Annotationen ausgewertet, und das Modul warf beim Import `NameError`, was die ganze Suite an der conftest scheitern ließ.
- **Fix:** Die Zeile ergänzt, wie sie in jedem anderen Modul dieses Pakets steht.
- **Files modified:** backend/src/findling/index/writer.py
- **Committed in:** `2c544bf`

### Abweichungen, die keine Autoreparatur sind, sondern eine Auslegung des Plans

**5. Das Lock-Timeout ist nicht aus der gemessenen Zeit je Dokument hergeleitet**

Der Plan verlangt wörtlich: "Das Lock-Timeout wird aus der gemessenen Zeit je
Dokument hergeleitet, die im Welle-0-Bericht steht, mit einem ausreichenden
Sicherheitsfaktor". Diese Herleitung steht im Kommentar und ergibt rund 18 s je
Charge, aber sie trägt das Timeout nicht: sie beschreibt nur, wie wenig die
Arbeit selbst kostet. Bindend ist der Anspruch, in dem eine embed-Zeile reist,
und der ist von der OCR-Charge begrenzt. Der Kommentar führt beide Rechnungen
und sagt ausdrücklich, welche von ihnen die Zahl entscheidet.

**6. Die Chargengröße ist nicht aus dem RAM-Hebel hergeleitet**

Aus demselben Grund. Der Plan sagt "eine Charge, die in einem Durchgang
eingebettet werden kann, ohne dass die Aktivierungsspitze ueber den gemessenen
Wert steigt". Die Spitze hängt an `EMBED_BATCH_SIZE`, nicht an dieser Zahl, und
das steht so im Kommentar, samt dem, was die Zahl stattdessen entscheidet.

**7. Ein vierter benannter Endzustand, und `_needs_vectors` als fünfte Funktion**

Der Plan nennt `_goes_to_the_embedding_track` und `_embed_the_body`. Beide gibt
es unter diesen Namen. Dazu kommen `_needs_vectors` (Abweichung 1),
`_wire_the_second_track` und `_embed_ready`; die letzten beiden, weil der Plan
nicht sagt, woher der Vektorspeicher, der Tokenizer und das Modell im Poller
herkommen, und ein Modul-Singleton oder ein Import aus der API-Schicht die zwei
Alternativen gewesen wären, die 06-06 für die Leseseite bereits verworfen hat.

**8. Der Plattenplatzvorbehalt hat `index/writer.py` verändert, was Task 2 nicht vorsieht**

Task 2 listet nur `poller.py` und die Testdatei. `free_bytes` und
`disk_is_tight` sind trotzdem dort entstanden, weil der Plan "denselben
Plattenplatzvorbehalt, den flush() kennt" verlangt und *derselbe* nur dann
wörtlich stimmt, wenn es eine Definition gibt. `writer.py` steht ohnehin in der
Dateiliste von Task 3.

**9. `deferred-items.md` ist nicht in der Dateiliste des Plans**

Zwei Befunde sind dort abgelegt, die dieser Plan nicht schliesst und nicht
schliessen soll: `reset_for_reindex` hat keinen Aufrufer im Produktivcode
(DI-06-02), und `embedding_version` wird weiterhin von niemandem geschrieben
(DI-06-03, übernommen aus 06-04 und 06-06). Beide gehören an Plan 06-08, wo die
Deckungsgradzahl entsteht, mit der "vollständig" überhaupt erst eine prüfbare
Bedingung wird.

**10. Ein Zuruf des Orchestrators mitten im Plan**

`backend/tests/test_rrf_fusion.py` hat eine Leerzeile bekommen (ruff I001,
Hinterlassenschaft aus 06-06), als eigener Commit `721bef3`. Der Befund war
zunächst nicht reproduzierbar, weil mein `ruff check .` aus dem Cache grün kam;
mit `--no-cache` ist er da. Seitdem laufen alle ruff-Gates dieses Plans mit
`--no-cache`, und das ist der eigentliche Ertrag dieses Zwischenrufs.

---

**Total deviations:** 4 autorepariert (1 Fehler, 2 fehlende kritische Funktionen, 1 blockierend), 6 Auslegungen
**Impact on plan:** Keine Ausweitung des Umfangs. Die zwei fehlenden kritischen Funktionen und der eine Fehler betreffen genau die Eigenschaft, die dieser Plan zusichert: dass der Bestand sich wirklich füllt und keine Zeile auf einer Spur hängen bleibt.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: authorization | backend/src/findling/worker/poller.py | Der embed-Zweig schreibt `replace_acl`, also eine fünfte Schreibstelle in die Rechtetabelle. Sie stand nicht im Bedrohungsregister des Plans, weil dort die Rangentscheidung nicht vorkommt. Die Schreibrichtung ist deklarativ und die Liste kommt aus `_acl_users(job)`, also mit demselben Deckelvermerk wie an den drei bestehenden Stellen; ein Auftrag ohne Nutzerliste erreicht diesen Zweig nicht, weil `nc/queue.py` solche Zeilen verwirft, bevor sie ein Auftrag werden. |

## Issues Encountered

- **Zwei `IndexBatchWriter` auf einem Verzeichnis gehen nicht**, was der erste Entwurf des Plattenplatz-Tests versucht hat (ein zweiter Writer mit hohem Boden neben dem der Fixture). tantivy vergibt eine Sperre je Indexverzeichnis, was der Grund ist, warum diese Klasse überhaupt einmal existiert. Der Fall setzt jetzt `disk_is_tight` auf dem einen Writer und sagt im Kommentar, warum die naheliegende Konstruktion nicht geht.
- **Der ruff-Cache hat einen echten Befund verdeckt.** Siehe Abweichung 10. Alle Gates dieses Plans sind mit `--no-cache` gelaufen.
- **PHPUnit ist lokal nicht fahrbar.** `php/tests/bootstrap.php` läuft im Autoload-Raum von `nextcloud/server`, und `composer.json` sagt ausdrücklich, dass die Abhängigkeit nur in CI installiert wird. `php -l` ist stattdessen über `docker run --rm php:8.3-cli` gelaufen, beide geänderten Dateien ohne Syntaxfehler. Keiner der sechs vorhandenen Unit-Tests berührt `QueueMapper` oder `QueueService`.
- **Die AWS-Box ist nicht angefasst worden.** Dieser Plan misst nichts; alle Zahlen in den Kommentaren stammen aus dem Welle-0-Bericht vom 05.09.2026 und aus Plan 06-05.

## Offene Verifikation

Keine. Alle Gates sind lokal grün gelaufen: `pytest` mit 1.286 bestandenen und 13
übersprungenen Tests, `ruff check . --no-cache`, `ruff format --check .`,
`pyright` mit 0 Fehlern und `vulture` ohne Befund, jeweils im CI-Umfang
`backend`. Dazu `php -l` über beide geänderten PHP-Dateien und die
Abnahmegreps: `KIND_EMBED` steht 4 mal in `QueueMapper.php`, 1 mal in
`QueueService.php` und 2 mal in `nc/queue.py`, `grep -c 'def delete'` ist 0 in
`writer.py` und in `repo.py`, und weder Geviert- noch Halbgeviertstrich stehen
in einer der geänderten Dateien. Die neun vorbestehenden
Markdown-Formatbefunde oberhalb von `backend` (DI-06-01) sind unverändert.

## User Setup Required

None. `FINDLING_EMBED_ENABLED` steht auf `true` und braucht nichts. Ein Container
ohne Modell verdrahtet die Spur gar nicht erst, schreibt genau eine Warnzeile
mit dem Typnamen und übergibt keine Zeile; die Suche antwortet lexikalisch
weiter.

## Next Phase Readiness

- **Plan 06-08 findet den Deckungsgrad rechenbar vor.** `chunk_count` und `vector_count` stehen seit 06-04, und ab jetzt bewegen sie sich auch: die Statusseite kann "so viele Dokumente tragen Vektoren" gegen "so viele sind indexiert" stellen. `RoundResult.embedded` liefert die Rate dazu.
- **Plan 06-08 erbt zwei benannte Lücken**, beide in `deferred-items.md`: DI-06-02 (`reset_for_reindex` ohne Aufrufer, also leert ein Modellwechsel den Bestand heute nicht von selbst) und DI-06-03 (`embedding_version` wird von niemandem gestempelt). Beide werden schliessbar, sobald die Deckungsgradzahl existiert, weil "vollständig" dann eine Bedingung ist und keine Vermutung.
- **Plan 06-09 hat seinen Träger.** Die Chunks tragen jetzt echte Zeichen-Offsets in `body_de`, und `chunks_of` gibt sie hinter dem Vorfilter heraus.
- **Plan 06-11 hat seinen Messgegenstand.** A5, die Aktivierungsspitze, ist ab jetzt an einer laufenden Spur messbar statt an einem Skript, und `EMBED_BATCH_SIZE` ist der Hebel darunter.
- **Kein Blocker.**

---
*Phase: 06-semantische-suche*
*Completed: 2026-09-05*

## Self-Check: PASSED

Die angelegte Datei liegt auf der Platte
(`backend/tests/test_embedding_track.py`), alle sechs Commits (`359fd2c`,
`3858e50`, `721bef3`, `6d265da`, `2c544bf`, `af9be03`) stehen in `git log`.
Zusätzlich geprüft: `grep -c 'KIND_EMBED'` ergibt 4 in `QueueMapper.php`, 1 in
`QueueService.php` und 2 in `nc/queue.py`, `grep -c 'def delete'` ist 0 in
`index/writer.py` und in `store/repo.py`, `_fetch_file` und `_stream_into`
stehen nicht im Rumpf von `_embed_the_body` (als Test festgehalten), und weder
Geviert- noch Halbgeviertstrich stehen in einer der zwölf Dateien.
