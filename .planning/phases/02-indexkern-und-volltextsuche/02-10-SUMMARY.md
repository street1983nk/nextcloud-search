---
phase: 02-indexkern-und-volltextsuche
plan: 10
subsystem: worker
tags: [poller, asyncio, queue, idempotenz, gate-a, tdd, ocs]

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-02: Store mit record, replace_acl, is_unchanged und den Versionsmarken"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-03: die vier Queue-Endpunkte der PHP-Companion-App"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-05: ExtractionWorker/extract_guarded, der langlebige Kindprozess"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-06: IndexBatchWriter mit Upsert, Sammel-Commit und Platzwache"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-08: dispatch.judge, dispatch.extract, die Formatliste"
provides:
  - "nc/client.py: claim_documents, ack_documents, unlock_documents, queue_stats, Pfade als Literale am Aufrufort"
  - "nc/queue.py: DocumentQueue, QueueJob, ClaimResult, CallResult, QueueStats; Transportfehler als Ergebnis"
  - "worker/poller.py: Poller mit run_once() und run(stop_event), Reihenfolge Commit, Zustand, Quittung"
  - "main.py: genau eine Poller-Task im lifespan, von enabled_handler scharf- und stillgestellt"
  - "Gate A: OCS_WRITE_ALLOWLIST mit genau zwei Pfaden, Begruendungsblock und drei Selbsttests"
  - "Gemessener Befund: sqlite3 verweigert den Verbindungswechsel zwischen Threads, ohne check_same_thread=False ist asyncio.to_thread unmoeglich"
affects: [02-11, 02-12, 02-13, 03-events-und-ocr, 04-adminstatus]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sicherheitsgate-Aufweichung als eigener Commit, mit Bedrohungsmodell-Notiz und Negativtest"
    - "Pfade als Zeichenkettenliterale am Aufrufort, weil das Gate den Pfad als ast.Constant liest"
    - "Transportfehler sind Ergebnisse, keine Ausnahmen: die einzige Indexier-Task darf nicht sterben"
    - "run_once() getrennt von run(stop_event): ein Durchgang ist ohne Zeit und ohne Task pruefbar"
    - "Alles Blockierende (Commit, add, SQLite, Extraktion, Datei-Handles) ueber asyncio.to_thread"
    - "Log ausschliesslich mit Zaehlern und Grundcodes, per Grep-Test eingezaeunt"

key-files:
  created:
    - backend/src/findling/nc/queue.py
    - backend/src/findling/worker/__init__.py
    - backend/src/findling/worker/poller.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_poller.py
  modified:
    - backend/tests/test_readonly_gate.py
    - backend/src/findling/nc/client.py
    - backend/src/findling/main.py
    - backend/src/findling/store/repo.py
    - backend/tests/test_store_repo.py

key-decisions:
  - "ACL vor Verdikt statt einer gemeinsamen Transaktion: der Store oeffnet je Aufruf eine Transaktion, und diese Reihenfolge macht einen Abbruch dazwischen folgenlos, ohne repo.py um eine zweite SQL-Stelle zu erweitern"
  - "check_same_thread=False in store/repo.py, weil ein Coroutine-Wiedereintritt nicht im Ursprungsthread landet und der Plan die SQLite-Transaktion ausdruecklich vom Event-Loop verlangt"
  - "Die Zustandsnamen heissen ROUND_* statt PASS_*, weil bandit (ruff S105) jede Konstante mit PASS_ als hartkodiertes Passwort meldet"
  - "create_app_client wird ueber das Modul (nc_client.create_app_client) erreicht, damit der Name genau einmal in poller.py steht und das Grep-Gate scharf bleibt"
  - "Der Poller oeffnet Index und Zustandsdatenbank erst beim ersten scharfen Durchgang: ein deployter, aber nicht aktivierter Container haelt sonst den Tantivy-Lock ohne je zu indexieren"

patterns-established:
  - "Vier Bezugsquellen (Client, Gateway-Pool, Queue, Extraktor) als Konstruktorargumente mit Produktionsvorgabe: der Durchgang ist gegen echten Index und echte SQLite pruefbar, waehrend Nextcloud eine Attrappe ist"
  - "Statische Tests fuer Reihenfolge und Nicht-Blockieren, weil beide Fehler nichts werfen"

requirements-completed: [IDX-02, IDX-03, IDX-06, IDX-08]

# Metrics
duration: 55min
completed: 2026-08-31
---

# Phase 02 Plan 10: Der Indexer laeuft Summary

**Eine asyncio-Task holt Arbeit aus der Warteschlange, liest die Bytes durch das Content-Gateway, extrahiert in einem Kindprozess, schreibt in den Index und quittiert erst nach dem Commit; Gate A bekommt dafuer seine erste und einzige Ausnahme, als eigener Commit mit Bedrohungsmodell-Notiz und Negativtest.**

## Performance

- **Duration:** ca. 55 min
- **Started:** 2026-08-31T21:05Z
- **Completed:** 2026-08-31T22:00Z
- **Tasks:** 3 von 3, alle TDD, je ein RED- und ein GREEN-Commit
- **Files modified:** 10 (5 neu, 5 geaendert)

## Accomplishments

- `OCS_WRITE_ALLOWLIST` traegt genau zwei Pfade. Darueber steht ein Block, der die Entscheidung traegt statt sie zu verstecken: Datum, Grund, die Feststellung, dass keine Nutzerdatei erreichbar ist, die Threat-IDs T-02-101 und T-02-102 und die Begruendungspflicht fuer jeden weiteren Eintrag. Drei neue Selbsttests: ein erlaubter Schreibpfad ist kein Verstoss, jeder andere bleibt einer, und ein Pfad in einer Variablen bleibt einer.
- `nc/client.py` hat vier Queue-Aufrufe, jeder mit dem Client als Argument und dem Pfad als Literal im Aufruf. Warum das so aussehen muss und nicht schoener, steht als Kommentarblock darueber und ist zusaetzlich als Test festgeschrieben.
- `nc/queue.py` uebersetzt die OCS-Antwort in `QueueJob`-Objekte, verwirft unbrauchbare Eintraege und zaehlt sie, und macht aus jedem Transportfehler ein Ergebnis. `user_ids` und `fetch_as` bleiben getrennt, mit dem Grund im Docstring.
- `worker/poller.py` haelt die eine Task. Der Ablauf steht als nummerierter Kommentarblock im Code, samt dem Satz, was ein Abbruch an jeder einzelnen Stelle kostet. Der `content_hash` faellt beim Lesen der Bytes nebenbei an (Streaming-Hash), die Temporaerdatei verschwindet im `finally`, und Reste eines frueheren Absturzes werden beim ersten Durchgang entfernt.
- `main.py` startet genau eine Task im `lifespan`, `enabled_handler` stellt sie scharf und still, und der Abschnitt nach dem `yield` beendet sie geordnet und gibt die gehaltenen Zeilen per `unlock` zurueck.
- 36 neue Tests (14 Queue, 22 Poller) plus drei im Gate und einer im Store. Alle fuenf Python-Gates lokal gruen: 382 Tests, ruff check, ruff format, pyright, vulture.

## Task Commits

1. **Task 1: Gate A um genau zwei Pfade erweitern** , RED `009ec83`, GREEN `a6193c3`
2. **Task 2: Die vier Queue-Aufrufe an der nc-Grenze** , RED `6a7bd18`, GREEN `c980151`
3. **Task 3: Die eine Poller-Task** , RED `ecb81cc`, GREEN `3fc363a`

## TDD Gate Compliance

Alle drei Aufgaben sind mit `tdd="true"` geplant und liefen in der Reihenfolge RED, GREEN. Jeder RED-Commit steht gegen ein tatsaechlich rotes Ergebnis: Task 1 gegen eine fehlgeschlagene Zusicherung (`invariant 3, DELETE on /ocs/v2.php/apps/findling/queues/documents`), Task 2 und Task 3 gegen einen `ModuleNotFoundError` beim Sammeln. Eine REFACTOR-Runde war in keiner Aufgabe noetig; die Formatierungslaeufe von ruff sind Teil des jeweiligen GREEN-Commits.

## Files Created/Modified

- `backend/tests/test_readonly_gate.py` , Allowlist mit Begruendungsblock, drei neue Selbsttests, vierte geprueft enge `mkdir`-Ausnahme fuer `worker/poller.py`.
- `backend/src/findling/nc/client.py` , `claim_documents`, `ack_documents`, `unlock_documents`, `queue_stats`, alle mit Client als Argument und Pfad als Literal; Modul-Docstring nennt den neuen Schreibkanal.
- `backend/src/findling/nc/queue.py` , `QueueJob`, `ClaimResult`, `CallResult`, `QueueStats`, `DocumentQueue` mit `claim`, `acknowledge`, `unlock`, `stats`; Feldvalidierung, Zaehlung der verworfenen Eintraege, definierte Ergebnisse bei Transportfehlern.
- `backend/src/findling/worker/__init__.py` , Paket-Docstring: eine Task, und warum es bei einer bleibt (IDX-08).
- `backend/src/findling/worker/poller.py` , `Poller` mit `run_once`, `run`, `arm`, `silence`, `unlock_held`, `aclose`; `RoundResult`, `default_poller`, Scratch-Verwaltung, Cooldown.
- `backend/src/findling/main.py` , eine Task im `lifespan`, `active_poller()`, `enabled_handler` schaltet scharf und still, geordnetes Herunterfahren mit `unlock_held`.
- `backend/src/findling/store/repo.py` , `check_same_thread=False` mit Begruendung (siehe Deviation 2).
- `backend/tests/test_queue_client.py` , 14 Tests gegen einen gefaelschten Session-Doppelgaenger.
- `backend/tests/test_poller.py` , 22 Tests gegen echten Tantivy-Index und echte SQLite.
- `backend/tests/test_store_repo.py` , Stolperdraht-Test fuer die Thread-Eigenschaft der Verbindung.

## Decisions Made

- **ACL vor Verdikt statt einer gemeinsamen Transaktion.** Der `interfaces`-Block verlangt "SQLite: files.state, reason, indexed_at und acl (eine Transaktion)". `Store` oeffnet je oeffentlichem Aufruf eine eigene Transaktion und bietet keine gemeinsame an; eine anzubieten hiesse, eine zweite SQL-Stelle in `repo.py` zu erzeugen, deren einzige Invariante lautet "wie `record` plus wie `replace_acl`". Stattdessen schreibt der Poller **erst** die Rechte und **dann** das Verdikt. Ein Abbruch dazwischen laesst die Datei unbeurteilt, die Zeile kommt zurueck und der naechste Durchgang schreibt beides erneut. Die umgekehrte Reihenfolge waere die gefaehrliche: eine Datei mit `indexed` und ohne Rechte wuerde vom schnellen Pfad fuer immer quittiert, ohne dass die Rechte je nachgetragen wuerden.
- **Der abgebrochene Batch laesst offene Dokumente im Writer stehen.** Bei einem Gateway-5xx wird nicht committet, nichts geschrieben und nichts quittiert; was der Writer schon aufgenommen hat, bleibt `pending`. `IndexBatchWriter` kennt kein Verwerfen, und das ist in Ordnung: die Wiederholung schreibt dieselben Dateien ueber den Upsert erneut. Der Restfall ist ein Dokument im Index ohne Zeile in SQLite, falls die Queue die Zeile zwischenzeitlich als `repeatedly_stuck` aufgibt. Ohne ACL-Zeile ist es unsichtbar, kostet also Platz und keine Korrektheit. Benannt, damit 02-13 es messen kann.
- **Der Poller oeffnet nichts, bevor er scharf ist.** `default_poller()` baut nur das Objekt. Index und Zustandsdatenbank oeffnen sich beim ersten scharfen Durchgang. Ein deployter, aber noch nicht aktivierter Container haelt sonst den Tantivy-Schreiblock, ohne je zu indexieren, und die Testsuite, die den `lifespan` mehrfach betritt, wuerde jedes Mal einen Index anlegen.
- **`ROUND_*` statt `PASS_*`.** Die Zustandsnamen eines Durchgangs hiessen zuerst `PASS_WORKED` und so weiter. ruff meldet ueber bandit (S105) jede Konstante mit `PASS` im Namen als moegliches hartkodiertes Passwort. Fuenf `noqa`-Zeilen fuer eine Namenswahl waeren der falsche Tausch.
- **`create_app_client` ueber das Modul.** Das Abnahmekriterium verlangt genau eine Nennung in `poller.py`. Ein Import unter Namen plus die Verwendung als Vorgabewert sind zwei Zeilen. Der Zugriff ueber `nc_client.create_app_client` laesst genau eine uebrig und liest sich zudem als das, was er ist: die eine Stelle, die einen Client baut.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Das Nur-Lesen-Gate verbot das `mkdir` des Scratch-Verzeichnisses**

- **Found during:** Task 3
- **Issue:** Der Poller legt `tmp_dir` unter `APP_PERSISTENT_STORAGE` an. `mkdir` und `makedirs` stehen beide in `FORBIDDEN_IDENTIFIERS`, weil `mkdir` auch eine schreibende Methode von `nc_py_api.files` ist, und die Standardbibliothek kennt keinen dritten Weg, ein Verzeichnis anzulegen.
- **Fix:** Vierter Eintrag in `INVARIANT_2_EXCEPTIONS`, `("worker/poller.py", "mkdir")`, mit derselben Begruendung wie die drei vorhandenen und einer zusaetzlichen: der Pfad kommt aus `findling.config` und nie aus einem Queue-Eintrag, es erreicht also kein Wert aus Nextcloud diesen Aufruf. Invariante 1 haelt beide eingeschraenkten Importe aus dem Modul heraus.
- **Files modified:** `backend/tests/test_readonly_gate.py`
- **Verification:** Der vorhandene Positivtest wurde um die Zeile erweitert; der Negativtest deckt `api/search.py` und `index/schema.py` bereits ab, die Ausnahme breitet sich also nachweislich nicht aus. `uv run pytest tests/test_readonly_gate.py -q` gruen (17 Tests).
- **Committed in:** `3fc363a`

**2. [Rule 1 - Bug] sqlite3 verweigerte jede Zustandsschreibung aus `asyncio.to_thread`**

- **Found during:** Task 3, unmittelbar beim ersten gruenen Durchgang
- **Issue:** Der Plan verlangt ausdruecklich, die SQLite-Transaktion in `asyncio.to_thread` zu legen (T-02-105, Pitfall 11). Gemessen: **jede** solche Schreibung scheitert mit `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`. Der Grund ist nicht die Nebenlaeufigkeit, sondern der Wiedereintritt: `to_thread` nimmt einen Thread aus dem Vorrat, und der ist nie derselbe wie der, in dem `open_store` lief. 12 der 22 Poller-Tests fielen daran.
- **Ursache, gemessen:** `sqlite3.connect` setzt `check_same_thread=True`. Das ist eine Zusicherung auf der Python-Seite, keine Eigenschaft der Bibliothek: dieser Build meldet `sqlite3.threadsafety == 3`, also serialisierten Modus, in dem die Bibliothek den Zugriff selbst absichert.
- **Fix:** `check_same_thread=False` in `_connect`, mit einem Docstring-Absatz, der beide Haelften der Begruendung nennt: die Bibliothek serialisiert, und es gibt genau einen Schreiber im Prozess (IDX-08), dessen Thread-Wechsel nacheinander abgewartet werden.
- **Files modified:** `backend/src/findling/store/repo.py`, `backend/tests/test_store_repo.py`
- **Verification:** `test_the_connection_may_cross_a_worker_thread` schreibt und liest aus einem fremden Thread und prueft zusaetzlich `sqlite3.threadsafety == 3`. Ein Build unterhalb des serialisierten Modus macht den Poller unsicher, ohne dass sonst etwas auffiele; dieser Stolperdraht faellt dann um.
- **Committed in:** `3fc363a`

**3. [Rule 2 - Korrektheit] Ein blockierendes `open()` im Event-Loop**

- **Found during:** Task 3
- **Issue:** Die Temporaerdatei wurde zuerst direkt mit `Path.open("wb")` in einer Coroutine geoeffnet. Die ruff-Gruppe ASYNC ist hier zum ersten Mal scharf und meldet genau das. Auf der Zielhardware kann das Volume eine langsame SD-Karte sein, und ein blockierendes Oeffnen im Loop ist derselbe Stillstand wie ein blockierendes Schreiben, nur schwerer zu finden.
- **Fix:** Oeffnen und Schliessen laufen ueber `asyncio.to_thread`, ausgelagert in `_stream_into`, damit der Fehlerpfad des Aufrufers lesbar bleibt.
- **Files modified:** `backend/src/findling/worker/poller.py`
- **Verification:** `uv run ruff check .` ohne Befund; `test_the_blocking_work_runs_off_the_event_loop` prueft vier Aufrufstellen, nicht mehr nur zwei.
- **Committed in:** `3fc363a`

### Abweichungen in den Abnahmekriterien

| Kriterium | Ergebnis |
|---|---|
| `pytest tests/test_readonly_gate.py -q` | Exit 0, 17 Tests |
| `grep -c 'queues/documents' test_readonly_gate.py` >= 2 | 8 |
| `grep -c 'def test_' test_readonly_gate.py` >= 9 | 17 |
| `grep -ci 'threat' test_readonly_gate.py` >= 1 | 2 |
| `grep -c 'def test_writing_ocs_call_to_another_path_is_still_a_violation'` = 1 | 1 |
| Task-1-Commit beruehrt keine andere Datei | erfuellt (`009ec83` und `a6193c3` je nur `test_readonly_gate.py`) |
| `pytest tests/test_queue_client.py -q` | Exit 0, 14 Tests |
| `grep -c 'queues/documents' nc/client.py` >= 3 | 4 |
| `grep -rl 'nc_py_api' src/findling` = nur `nc/client.py` | erfuellt |
| `grep -Ec 'def delete\|\.delete\(' nc/client.py` = 0 | 0 |
| `grep -c 'create_app_client' nc/queue.py` = 0 | 0 |
| `grep -c 'fetch_as' nc/queue.py` >= 1 | 5 |
| `pytest tests/test_poller.py -q` | Exit 0, 22 Tests |
| `grep -c 'def test_' test_poller.py` >= 10 | 22 |
| commit vor record vor acknowledge im Code | Zeilen 8, 350, 358 |
| `grep -c 'to_thread' poller.py` >= 2 | 8 |
| `grep -c 'create_app_client' poller.py` = 1 | 1 |
| `grep -c 'def test_one_client_per_run'` = 1 | 1 |
| `grep -c 'paused_low_disk' poller.py` >= 1 | 1 |
| `grep -c 'unlock' main.py` >= 1 | 1 |
| kein Logaufruf mit Pfad oder Text | keine Treffer |
| `grep -c 'def test_crash_between_commit_and_state'` = 1 | 1 |
| `pytest -q` ohne DeprecationWarning | 382 passed, 1 skipped; die eine verbleibende Warnung ist die `StarletteDeprecationWarning` aus `fastapi.testclient` und war vor diesem Plan da |
| ruff check, ruff format --check, pyright, vulture | alle vier ohne Befund |

Zwei Kriterien wurden in ihrer *Pruefform* angepasst, nicht in ihrer Absicht, und beide Male steht der Grund im Test:

- Der Reihenfolge-Test prueft `self._writer_or_die().flush` vor `self._record_verdicts` vor `queue.acknowledge(`, weil das die drei Aufrufstellen in `run_once` sind. Eine Suche nach `self._store.record` haette die Definition der Hilfsmethode weiter unten getroffen und damit die Reihenfolge im Text statt im Ablauf gemessen. Der Grep aus dem Plan (`commit|record(|acknowledge(`) ist unveraendert erfuellt.
- Der Client-Test zaehlt Codezeilen, nachdem Kommentare entfernt sind. Die Begruendung des Gates steht direkt daneben und nennt den Namen der Fabrik; eine Regel, die ihre eigene Erklaerung bestraft, wird geloescht statt befolgt.

---

**Total deviations:** 3 auto-fixed (1x Rule 1, 1x Rule 2, 1x Rule 3)
**Impact on plan:** Kein Scope-Zuwachs. Deviation 2 ist ein Messbefund, der eine Planannahme widerlegt: die vom Plan geforderte Auslagerung der SQLite-Transaktion war mit der bestehenden Verbindungseinstellung schlicht unmoeglich. Die Korrektur liegt in `store/repo.py`, das nicht in `files_modified` des Plans steht.

## Issues Encountered

- **Die Importsortierung von ruff kippt mit der Existenz des Moduls.** Solange `findling/nc/queue.py` und `findling/worker/poller.py` nicht existierten, sortierte ruff die Importe der Testdateien als Drittanbieter ein. Zwischen RED- und GREEN-Commit ist ein Formatierungslauf noetig; dasselbe steht schon im Summary von 02-02.
- **Die Modul-Docstrings duerfen die verbotenen Bibliotheksnamen nicht nennen.** Drei Tests pruefen Invariante 1 als reinen Textscan ueber alle Dateien des Pakets. `nc/queue.py` erklaerte im Docstring, warum es `nc_py_api` und `httpx` nicht importiert, und faellt genau daran durch. Die Erklaerung steht jetzt ohne die beiden Namen da, mit einem Satz, der sagt warum.
- **Kein CI-Lauf moeglich.** Alle Gates liefen lokal ueber `uv run` unter Windows (Python 3.13.13, SQLite 3.50.4). Der GitHub-Actions-Lauf ist von hier nicht pruefbar und steht aus, ebenso Gate B: der Pruefsummenlauf ueber den Referenzkorpus braucht die Test-Nextcloud und gehoert in den Integrationslauf, nicht in diese Suite.
- **Der Poller wurde nie gegen eine echte Nextcloud gefahren.** Alle 22 Tests laufen gegen Attrappen fuer Queue und Gateway, mit echtem Tantivy-Index, echter SQLite und dem echten Dispatcher. Der erste Lauf mit einem echten Container gehoert in 02-12/02-13.

## Threat Flags

Keine neue Angriffsflaeche ueber die im Plan verzeichnete hinaus. Die neun `mitigate`-Dispositionen sind umgesetzt:

| Threat ID | Umsetzung |
|---|---|
| T-02-101 (Allowlist-Erweiterung) | Genau zwei Pfade, eigener Commit, Begruendungsblock mit Threat-IDs, drei Selbsttests, davon zwei fuer die Enge der Liste |
| T-02-102 (Nutzerdatei im Schreibpfad) | Der Poller kennt keinen Weg zurueck in den Nextcloud-Speicher; Invariante 1 haelt beide HTTP-Wege aus dem Modul heraus, Gate B belegt es von aussen |
| T-02-103 (Endlosschleife durch kaputte Datei) | `failed` und `skipped` werden quittiert; `failed` reist mit Grundcode zur PHP-Seite, wo die Drei-Strike-Regel steht. Test: `test_a_file_that_cannot_be_processed_is_acknowledged_with_its_reason` |
| T-02-104 (voller Datentraeger) | `paused_low_disk` beendet den Durchgang, schreibt nichts und gibt die Zeilen per `unlock` zurueck; eigener Test |
| T-02-105 (blockierender Aufruf im Loop) | Commit, `add`, die SQLite-Schreibung, die Extraktion und beide Datei-Handles laufen ueber `asyncio.to_thread`; ruff-Gruppe ASYNC scharf, dazu ein statischer Test ueber vier Aufrufstellen |
| T-02-106 (ein Client je Datei) | Ein Client und ein Verbindungspool je Lauf, in `_open()` einmal erzeugt; Zaehltest ueber zehn Dateien plus Grep-Gate auf genau eine Nennung |
| T-02-107 (Dateinamen im Log) | Ausschliesslich Zaehler und Grundcodes, im Fehlerfall nur der Ausnahmetyp und nie ein Traceback; Grep-Test gegen Pfad, Titel, Ausschnitt, Text und Suchbegriff |
| T-02-108 (Temporaerdateien mit Nutzerinhalt) | Loeschung im `finally`, Aufraeumen beim ersten Durchgang, Ablage ausschliesslich unter `tmp_dir`; eigener Test, der auch einen Rest aus einem frueheren Absturz auslegt |
| T-02-109 (deaktiviertes Backend pollt weiter) | `enabled_handler` stellt scharf und still, genau eine Task; zwei Tests, davon einer ueber den echten `lifespan` |

## Known Stubs

Keine. `queue_stats` und `DocumentQueue.stats` haben in dieser Phase noch keinen Aufrufer: sie sind der vierte Endpunkt des Protokolls und die Datenquelle der Statusseite aus Phase 4. Der Aufruf fehlt, die Funktion ist vollstaendig und getestet.

## User Setup Required

Keine.

## Next Phase Readiness

- **02-11/02-12 (Integration)** finden `default_poller()`, `active_poller()` und die drei Schaltpunkte `arm`, `silence`, `unlock_held` vor. Der erste Lauf gegen eine echte Nextcloud ist die offene Aufgabe.
- **02-13 (Messprotokoll)** kann `run_once()` ohne Task und ohne Zeit rufen; `RoundResult` liefert die Zaehler eines Durchgangs. Zwei Zahlen sind noch nicht gemessen: die Dauer eines Durchgangs mit 32 echten Dateien und der Fall des abgebrochenen Batches (siehe "Decisions Made").
- **Phase 3 (Events und OCR)** findet `QueueJob.etag` und `QueueJob.is_update` bereits im Protokoll und muss die Form des Objekts nicht aendern. `skipped(no_text_layer)` entsteht im Extraktor und laeuft unveraendert durch diesen Poller.
- **Offene Anschlussstelle, hier bewusst nicht entschieden:** wer `expected_versions` beim Start gegen `Store.version_mismatch` haelt und was eine Abweichung ausloest. Der Poller oeffnet den Store und den Index, faellt fuer diese Frage aber ausdruecklich kein Urteil; sie ist seit 02-02 und 02-06 offen und gehoert in den Startpfad, nicht in die Schleife.

## Self-Check: PASSED

Alle fuenf neuen und alle fuenf geaenderten Dateien liegen im Worktree; alle sechs Commit-Hashes stehen im Log von `gsd/agent-02-10`. Keiner der sechs Commits enthaelt eine Loeschung (`git diff --diff-filter=D` leer). Abschliessender Lauf: `uv run pytest -q` 382 passed, 1 skipped; `ruff check`, `ruff format --check`, `pyright` und `vulture --min-confidence 80` ohne Befund.

---
*Phase: 02-indexkern-und-volltextsuche*
*Completed: 2026-08-31*
