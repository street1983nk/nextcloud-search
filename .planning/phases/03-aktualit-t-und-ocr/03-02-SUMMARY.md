---
phase: 03-aktualit-t-und-ocr
plan: 02
subsystem: api
tags: [tantivy, nextcloud, php, event-listener, queue, rename, python]

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: Tantivy-Index mit stored body_de, Poller mit is_unchanged-Schnellpfad, Zustandsspeicher
  - phase: 03-aktualit-t-und-ocr
    provides: "Plan 03-01, Spalte kind, Claim-Reihenfolge, FileEventListener, QueueService::enqueueFile"
provides:
  - "IndexBatchWriter::stored_body(file_id), der gespeicherte Text eines Dokuments ohne Nextcloud"
  - "QueueJob.kind mit geschlossener Liste und Rueckfall auf content"
  - "Metadaten-Zweig im Poller: kein Gateway-Aufruf, kein is_unchanged, Text aus dem Index"
  - "Uebernahme von content_hash und truncated beim Metadaten-Job, der Schnellpfad bleibt heil"
  - "NodeRenamedEvent im Listener und in Application::register"
  - "Der Ordner-Fall der Umbenennung ist begruendet ausgelassen, mit Verweis auf Plan 03-04"
affects: [03-03 Delete, 03-04 Share und Subtree, 03-05 OCR, 03-07 requeueAs, 03-12 ETag-Abgleich]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Der Index als Textquelle: body_de ist die einzige gespeicherte Textkopie und damit ohne Netz lesbar"
    - "Job-Art als Wegwahl mit geschlossener Liste, unbekannte Werte fallen auf content zurueck"
    - "Rueckfall statt Wiedereinreihung: ein Metadaten-Job ohne Text laeuft als Inhaltsjob weiter"

key-files:
  created: []
  modified:
    - backend/src/findling/index/writer.py
    - backend/src/findling/nc/queue.py
    - backend/src/findling/worker/poller.py
    - backend/tests/test_index_writer.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_poller.py
    - php/lib/Listener/FileEventListener.php
    - php/lib/AppInfo/Application.php
    - php/lib/Service/QueueService.php

key-decisions:
  - "Der Metadaten-Job uebernimmt content_hash und truncated aus der vorhandenen Zustandszeile, sonst haette die naechste Inhaltsrunde eine unveraenderte Datei erneut heruntergeladen und extrahiert"
  - "kind steht als letztes Feld von QueueJob mit Default content, damit user_ids, fetch_as und is_update ohne Default bleiben"
  - "Die geschlossene Liste KINDS kennt nur content und metadata; delete, acl und ocr fallen bis zu ihren Plaenen auf content zurueck statt einen Zweig zu waehlen, den es nicht gibt"
  - "stored_body ruft index.reload(), damit ein Metadaten-Job den Stand des letzten Commits sieht und nicht den eines aelteren Searchers"
  - "describe() bekommt fuer metadata keinen eigenen Rueckgabezweig, weil das Quellobjekt identisch ist; stattdessen haelt der Kommentar fest, dass title und path aus dem Knoten kommen muessen"

patterns-established:
  - "Umbenennungstests suchen nach dem neuen Dateinamen ueber FIELD_NAME, nie nach dem Inhalt"
  - "Ein Zaehler in der Gateway-Attrappe belegt, dass ein Job keinen Byteabruf ausgeloest hat"
  - "Ausgelassene Faelle tragen ihren Grund und die Nummer des Plans, der sie nachholt"

requirements-completed: [COMP-03]

# Metrics
duration: 12min
completed: 2026-09-01
---

# Phase 3 Plan 02: Umbenennen und Verschieben als billiger Metadaten-Job Summary

**Eine umbenannte Datei ist unter ihrem neuen Namen auffindbar, und der Weg dorthin kostet kein einziges Byte ueber das Netz: der Container liest den gespeicherten Text aus dem Tantivy-Index zurueck und schreibt das Dokument mit neuen Metadaten erneut.**

## Performance

- **Duration:** rund 12 min reine Ausfuehrung
- **Started:** 2026-09-01T11:20Z
- **Completed:** 2026-09-01T11:32Z
- **Tasks:** 3 (zwei davon nach RED/GREEN, also 5 Commits)
- **Files modified:** 9 (0 neu, 9 geaendert)

## Accomplishments

- `IndexBatchWriter.stored_body(file_id)` holt den gespeicherten Text eines Dokuments zurueck. Der Term wird ueber das Schema gebildet, genau wie die Term-Loeschung im Upsert, weil ein Term aus dem Feldnamen ein I64 waere und die U64-Spalte `file_id` nie trifft. Der Fehler wuerde nichts werfen, sondern fuer jede Datei `None` liefern und jede Umbenennung still auf den teuren Weg zurueckfallen lassen.
- `QueueJob` traegt `kind`. Ein fehlender Wert (Zeile aus einer aelteren PHP-Fassung) und ein unbekannter Wert (`delete`, `acl`, `ocr` vor ihren Plaenen) werden beide zu `content`: die Job-Art waehlt einen Zweig, und sie kommt von aussen (T-03-201).
- Der Poller verzweigt in Schritt 1 seiner Runde nach `kind`. Der Metadaten-Zweig ruft kein Gateway an, oeffnet keine Scratch-Datei, startet kein Sandbox-Kind und fragt kein `is_unchanged`. Er liest den Text aus dem Index, baut denselben `IndexRecord` wie `_record_of` mit neuem `name`, `title`, `path`, `ext` und `mtime` und laesst `writer.add` per Term-Loeschung ersetzen.
- Fehlt der gespeicherte Text, faellt der Auftrag in den Inhaltszweig. Kein Fehler, keine Wiedereinreihung: die Zeile ist ohnehin schon da und nimmt den Weg, den eine Erstindexierung genommen haette (T-03-203).
- `FileEventListener` nimmt `NodeRenamedEvent` entgegen und reiht den Zielknoten als `kind=metadata` ein, mit denselben drei Vorpruefungen wie in Plan 03-01. Ein umbenannter Ordner erzeugt keine Zeile, und der Grund steht vollstaendig im Code: `FIELD_PATH` wird geschrieben, aber von keiner Abfrage gelesen und im Provider nie angezeigt.
- Die Verifikation laeuft ueber den neuen **Dateinamen** und nicht ueber den Inhalt. Ein Inhaltstest waere gruen und wuerde nichts beweisen, weil der Inhalt sich nicht geaendert hat.

## Task Commits

Jeder Task wurde einzeln committet, die beiden TDD-Tasks in RED und GREEN:

1. **Task 1: Gespeicherten Text zurueckholen**
   - `cf13e99` (test) , vier fehlschlagende Tests fuer `stored_body`
   - `069c9cd` (feat) , `stored_body` plus `self._index` im Writer
2. **Task 2: Metadaten-Job im Container, ohne Download**
   - `417bd93` (test) , sieben Behauptungen in `test_poller.py`, drei `kind`-Tests in `test_queue_client.py`
   - `9ed471f` (feat) , `QueueJob.kind`, `_kind()`, Metadaten-Zweig und `_rewrite_metadata`
3. **Task 3: Rename-Ereignisse im Listener, Ordner bewusst ausgelassen** , `723db49` (feat)

**Plan-Metadaten:** dieses SUMMARY (docs-Commit im selben Branch)

## Files Created/Modified

- `backend/src/findling/index/writer.py` , `self._index` im Konstruktor, neue Methode `stored_body`. Der Docstring nennt den Grund ihrer Existenz und wiederholt die I64/U64-Messung fuer die Suche.
- `backend/src/findling/nc/queue.py` , Konstanten `KIND_CONTENT`, `KIND_METADATA`, `KINDS`, Helfer `_kind()`, Feld `kind` in `QueueJob` und in `_job()`.
- `backend/src/findling/worker/poller.py` , Verzweigung nach `job.kind` in `_handle`, neue Methode `_rewrite_metadata`. Die vier nummerierten Schritte der Runde und ihre Kommentare sind unangetastet.
- `backend/tests/test_index_writer.py` , vier Tests: Text zurueck, `None` fuer Unbekanntes, Lesen nach Neuoeffnen, statische Pruefung der Term-Bildung ueber das Schema.
- `backend/tests/test_queue_client.py` , `kind` im Quellobjekt `SOURCE` (das jetzt wieder genau der Ausgabe von `describe()` entspricht), drei Tests fuer getragene, fehlende und unbekannte Art.
- `backend/tests/test_poller.py` , sechs Tests fuer den Metadaten-Job, ein Zaehler in der Gateway-Attrappe, `_by_name()` als Suche ueber `FIELD_NAME`.
- `php/lib/Listener/FileEventListener.php` , Zweig fuer `NodeRenamedEvent`, neue private Methode `queueRename`, `queue()` nimmt die Job-Art als Argument.
- `php/lib/AppInfo/Application.php` , `NodeRenamedEvent` in der Ereignisschleife, Kommentar auf den neuen Stand gebracht.
- `php/lib/Service/QueueService.php` , der Verzweigungspunkt in `describe()` benennt jetzt auch `metadata` und die Eigenschaft, die jeder Umbau erhalten muss.

## Decisions Made

- **`content_hash` und `truncated` werden uebernommen.** Der Metadaten-Job schreibt `store.record` mit den neuen Metadaten. Ohne die Uebernahme aus der vorhandenen Zeile waere `content_hash` danach `NULL`, `is_unchanged` wuerde fuer immer `False` antworten, und die naechste Inhaltsrunde haette eine unveraenderte Datei vollstaendig heruntergeladen und extrahiert. Ein `indexed(truncated)` waere zusaetzlich zu `indexed` geworden, also ein stiller Verlust der Diagnoseinformation aus D-08.
- **`kind` steht als letztes Feld von `QueueJob`.** Ein Default mitten in der Dataclass haette `user_ids`, `fetch_as` und `is_update` ebenfalls Defaults gegeben, und ein Auftrag ohne Lesenutzer muss unbaubar bleiben.
- **`KINDS` kennt nur zwei Arten.** Der Container faellt fuer `delete`, `acl` und `ocr` auf `content` zurueck, statt einen Zweig zu waehlen, den es noch nicht gibt. Die Plaene 03-03 bis 03-05 erweitern die Liste zusammen mit ihrem Zweig, und die Konstante liegt an genau einer Stelle.
- **`stored_body` ruft `index.reload()`.** Der Searcher-Pool von Tantivy steht auf den Segmenten des letzten Reloads. Ohne den Aufruf saehe ein Metadaten-Job den Stand von vor dem letzten Commit und liefe unnoetig in den Inhaltszweig.
- **`describe()` bekommt fuer `metadata` keinen eigenen Rueckgabezweig.** Das Quellobjekt ist identisch, ein Zweig, der dasselbe zurueckgibt, waere Laerm. Was der Kommentar statt dessen festhaelt: `title` und `path` muessen aus dem aufgeloesten Knoten kommen und nicht aus der Queue-Zeile, sonst schriebe eine Umbenennung den alten Namen zurueck in den Index, ohne dass irgendwo ein Fehler auftauchte.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] `content_hash` und `truncated` beim Metadaten-Job uebernommen**
- **Found during:** Task 2 (Metadaten-Job im Container)
- **Issue:** Der Plan schreibt "store.record mit den neuen Metadaten und unveraendertem Verdikt indexed". `_RECORD_SQL` setzt im Konfliktzweig aber `content_hash = excluded.content_hash`. Ein `record` ohne Hash haette die Spalte auf `NULL` gesetzt. Das Verdikt haette weiterhin `indexed` gelautet, aber `is_unchanged` prueft `content_hash` mit, also waere der Schnellpfad fuer diese Datei dauerhaft tot gewesen: jede spaetere Inhaltsrunde und jeder ETag-Abgleich haetten eine unberuehrte Datei vollstaendig heruntergeladen und extrahiert. Dasselbe gilt fuer `reason`: aus `indexed(truncated)` waere `indexed` geworden.
- **Fix:** `_rewrite_metadata` liest die vorhandene Zeile ueber `store.file_row` (im Worker-Thread, wie jeder blockierende Aufruf dort) und gibt `content_hash` sowie `truncated` an den neuen Datensatz weiter.
- **Files modified:** `backend/src/findling/worker/poller.py`
- **Verification:** `test_a_rename_updates_the_state_row_and_keeps_the_verdict` prueft Pfad, Titel, Verdikt, unveraenderten Hash und dass `is_unchanged` danach weiterhin `True` antwortet.
- **Committed in:** `9ed471f`

**2. [Rule 3 - Blocking] `self._index` im `IndexBatchWriter`**
- **Found during:** Task 1 (Gespeicherten Text zurueckholen)
- **Issue:** Der Writer hielt bisher nur `index.schema`, nicht den Index. `stored_body` braucht einen Searcher, und ein zweites `Index`-Objekt auf demselben Verzeichnis waere der Weg in genau die `LockBusy`-Meldung, vor der der Modul-Docstring warnt.
- **Fix:** Der Konstruktor haelt den uebergebenen Index, mit Kommentar zum Grund.
- **Files modified:** `backend/src/findling/index/writer.py`
- **Verification:** `test_stored_body_reads_a_document_of_an_earlier_run` oeffnet den Index neu und liest mit einem zweiten Writer; `test_a_second_writer_on_the_same_directory_is_reported_as_locked` bleibt gruen.
- **Committed in:** `069c9cd`

**3. [Rule 1 - Bug] `kind` im Quellobjekt der Queue-Tests nachgezogen**
- **Found during:** Task 2 (Metadaten-Job im Container)
- **Issue:** Die Konstante `SOURCE` in `test_queue_client.py` traegt den Kommentar "One row exactly as QueueService::describe builds it". Seit Plan 03-01 liefert `describe()` das Feld `kind`, `SOURCE` aber nicht. Die Attrappe log also ueber die Form der Antwort, und ein Test gegen sie haette den fehlenden Wert nicht bemerkt.
- **Fix:** `"kind": "content"` in `SOURCE`, entsprechend in der Gleichheitsbehauptung des bestehenden Tests; der Fall "Quellobjekt ohne kind" bekam einen eigenen Test.
- **Files modified:** `backend/tests/test_queue_client.py`
- **Verification:** `test_claim_delivers_jobs_with_ids_metadata_users_and_fetch_as` und `test_a_source_without_a_kind_is_a_content_job` sind beide gruen.
- **Committed in:** `417bd93`

---

**Total deviations:** 3 auto-fixed (1 fehlende kritische Funktion, 1 blockierend, 1 Bug)
**Impact on plan:** Alle drei sind Folgen der geplanten Aenderung selbst. Ohne 1 waere Erfolgskriterium "der Weg kostet keinen Download" fuer die naechste Runde derselben Datei wieder verletzt gewesen, also genau die stille Regression, gegen die dieser Plan gebaut ist.

## Issues Encountered

- **ruff SIM102** verlangte, die verschachtelte Bedingung `if kind == metadata:` / `if await _rewrite_metadata(...)` zu einer zu verbinden. Die Begruendung fuer beide Faelle, den billigen Zweig und den Rueckfall, steht dadurch als ein Kommentarblock ueber der Bedingung statt verteilt darin. Inhaltlich unveraendert.
- **Kein PHP auf der Entwicklungsmaschine** (in `docs/testing.md` dokumentiert). Der Syntaxcheck lief ueber `docker run --rm php:8.3-cli php -l` fuer alle 19 PHP-Dateien der App, fehlerfrei. Die CI prueft dieselbe Menge gegen PHP 8.2.
- **Sichtprobe im Test-Nextcloud steht aus.** Der laufende Container bedient den Hauptcheckout, und dieser Plan lief parallel zu 03-06 in einem eigenen Worktree; ein Deploy waere in den gemeinsamen Container hinein gegangen. Umbenennen einer Datei, Zeile mit `kind=metadata` in `findling_queue` und die anschliessende Suche nach dem neuen Dateinamen gehoeren damit in den Integrationslauf der Phase, wie schon bei Plan 03-01.

## Known Stubs

Keine. Was dieser Plan bewusst nicht baut, steht als benannter Fall mit Plannummer im Code:

- Die Verschiebung eines Ordners ueber eine Mount-Grenze aendert Rechte und braucht die `acl`-Jobs aus Plan 03-04. Der Fall ist im Docblock von `queueRename` namentlich genannt, damit die Luecke sichtbar bleibt.
- `KINDS` im Container fuehrt `delete`, `acl` und `ocr` noch nicht; die Kommentare nennen die Plaene 03-03 bis 03-05 und den Rueckfall, der bis dahin gilt.
- `describe()` hat weiterhin nur den dokumentierten Verzweigungspunkt und keinen `delete`-Zweig.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Bedrohungsmodells des Plans. Es kommt keine Route, keine Datei und keine Netzverbindung dazu: der Metadaten-Job liest aus dem Index und schreibt in den Index (T-03-202), die Job-Art wird gegen eine geschlossene Liste geprueft (T-03-201), ein Auftrag ohne gespeicherten Text faellt zurueck statt zu kreisen (T-03-203), der eigene Zweig ohne `is_unchanged` ist die Massnahme zu T-03-204, und der Listener loggt weiterhin nur Fehlertypnamen (T-03-205).

## Verification

- `cd backend && uv run python -m pytest -q` , 502 passed, 1 skipped
- `uv run ruff check .` , All checks passed
- `uv run ruff format --check .` , 62 files already formatted
- `uv run pyright` , 0 errors, 0 warnings
- `uv run vulture src tests --min-confidence 80` , ohne Befund
- `php -l` ueber alle 19 PHP-Dateien der App (im Container `php:8.3-cli`) , fehlerfrei
- Abnahme-Greps des Plans: `def stored_body` 1, `term_query` mit `self._schema` als erstem Argument, `metadata` im Poller 3, `stored_body` im Poller 1, `kind` in `nc/queue.py` 10, `to_thread` im Poller 11 gegenueber 8 vor diesem Plan, `NodeRenamedEvent` in `Application.php` 1 und im Listener 2, `'metadata'` im Listener 1, Ordner-Begruendung 2 Treffer.

## User Setup Required

Keine. Es kommt keine Abhaengigkeit, keine Migration und keine Umgebungsvariable hinzu.

## Next Phase Readiness

- Der Weg "Ereignis, Job-Art, eigener Zweig im Container" steht jetzt vollstaendig an einem Beispiel. Die Plaene 03-03 (`delete`) und 03-04 (`acl`) haengen ihre Zweige an dieselben zwei Stellen: `KINDS` samt `_kind()` in `nc/queue.py` und die Verzweigung in `Poller._handle`.
- `stored_body` ist zugleich die halbe Vorarbeit fuer den Loeschpfad: das Gegenstueck `drop_document` aus Plan 03-03 braucht dieselbe Term-Bildung ueber das Schema und darf laut Gate A nicht `delete` heissen.
- Offen und bewusst so: die Sichtprobe im Test-Nextcloud gehoert in den Integrationslauf, und `QueueController` validiert eingehende Arten weiterhin erst ab Plan 03-07.

## Self-Check

- `backend/src/findling/index/writer.py` FOUND
- `backend/src/findling/nc/queue.py` FOUND
- `backend/src/findling/worker/poller.py` FOUND
- `backend/tests/test_index_writer.py`, `backend/tests/test_queue_client.py`, `backend/tests/test_poller.py` FOUND
- `php/lib/Listener/FileEventListener.php`, `php/lib/AppInfo/Application.php`, `php/lib/Service/QueueService.php` FOUND
- Commits `cf13e99`, `069c9cd`, `417bd93`, `9ed471f`, `723db49` FOUND auf `worktree-agent-03-02`
- TDD-Tor-Reihenfolge belegt: `test(...)` vor `feat(...)` in beiden TDD-Tasks

## Self-Check: PASSED

---
*Phase: 03-aktualit-t-und-ocr*
*Completed: 2026-09-01*
