# Bug-Audit Findling Phase 2 (01.09.2026, Stand c17a362)

Suite gruen (429 passed, 1 skipped); alle Befunde in Produktionspfaden ohne Testabdeckung.

## HIGH
- H1 poller.py:174 / repo.py:61: _open_state() ohne meta= -> Versionsmarken bleiben unknown/0; degraded:true auf jeder Antwort, /status meldet dauerhaft reindexRequired, Drift-Alarm = Rauschen. Fix: open_store(..., meta=expected_versions(build_artifact().digest)).
- H2 Provider.php:194-197: leere Kandidatenseite (Prefilter entfernt alles) bricht Retry ab obwohl hasMore:true -> Treffer ab Rang N verschwinden lautlos. Fix: bei leerer Seite offset=nextOffset, exhausted=!hasMore, weiterschleifen (MAX_ROUNDS greift dann).
- H3 Provider.php:199/219: offset=nextOffset VOR Recheck-Schleife + Abbruch bei limit -> nicht verbrauchte (besser gerankte) Kandidaten der Seite gehen beim Blaettern verloren. Fix: Cursor auf verbrauchte Roh-Treffer beziehen.
- H4 QueueMapper.php:104-110 + QueueService.php:158: enqueue-Konflikt setzt locked_at=NULL waehrend Verarbeitung laeuft; Ack loescht per id -> neue Fassung verschwindet aus der Queue, Index traegt alte Bytes. Fix: claim_id/version-Spalte, Ack WHERE id AND version; alternativ dirty-Marke statt Unlock, Ack verwandelt dirty in entsperrt.
- H5 IndexCommand.php:91-99 + poller.py:410 + repo.py:400: --restart erhoeht keine Generation; is_unchanged-Schnellpfad verhindert jede Neuindexierung; reset_for_reindex hat keinen Aufrufer; verlorenes tantivy-Verzeichnis bei intakter state.db = dauerhaft leere Suche. Fix: Rebuild hebt index_version an (ExApp-Endpunkt oder Startpruefung: Index leer + files-Tabelle nicht leer -> Generation++).

## MEDIUM
- M1 poller.py:409-412/500-504: replace_acl nur im INDEXED-Zweig; is_unchanged-Schnellpfad schreibt keine ACL -> Rechteaenderungen erreichen Prefilter nie (hart ab Phase 3). Fix: ACL auch im Schnellpfad neu schreiben.
- M2 pdf.py:100: no_text_layer als Dokument-Durchschnitt statt pro Seite; Deckblatt mit 200 Zeichen + 9 Scanseiten -> ganzes Dokument skipped. Fix: pro Seite pruefen, Text indexieren, OCR-Kandidat trotzdem vormerken.
- M3 SchedulerJob.php:53-61: IJobList::add dedupliziert nur identische Argumente -> zwei parallele Crawl-Ketten je Mount moeglich. Fix: SchedulerJob::run beginnt mit jobList->remove(StorageCrawlJob::class).
- M4 StorageCrawlJob.php:104-119: too_large-continue umgeht Deadline-Pruefung -> Slice haelt Cron-Slot beliebig lange. Fix: Deadline an Schleifenanfang.
- M5 main.py:159-169: aclose() schliesst Store/Writer waehrend to_thread-Aufruf noch laeuft (nicht abbrechbar); unlock_held gibt Zeilen frei deren Verdicts gerade geschrieben werden. Fix: Lock/Event ueber den Durchlauf, aclose erst danach.
- M6 odf.py:63-64: archive.read(content.xml) ohne Groessenpruefung -> Zip-Bombe; unter Windows keine RLIMIT-Grenze. Fix: getinfo().file_size gegen max_file_bytes.
- M7 resources.py:139-168: _OPEN/_MARKS Modul-Globals ohne Lock aus to_thread -> doppelter Automatenbau, Store-Verbindungs-Leck, Close-Race im Pfadwechsel. Fix: threading.Lock um Oeffnungspfad.
- M8 queue.py:238-249 + QueueService.php:65: von _job() verworfene Eintraege kreisen ~45min (4 Claims); erreichbar via size=-1 (ungescannt) -> _whole_number(None). Fix: verworfene queue_ids als failed(corrupt) acken; describe() schreibt max(0,(int)$size).

## LOW
- L1 search.py:202: <= verschmilzt angrenzende Highlights ([0,3]+[3,6] -> [0,6]); < genuegt.
- L2 search.py:198: decode ohne errors= wirft bei Byte-Offset mitten im Zeichen; snippets.py:133 faengt fuer GANZE Anfrage -> alle Snippets weg. errors="replace" oder Praefix-Zaehlung.
- L3 errors.py:74/repo.py:115: Reason.GATEWAY_ERROR wird nie erzeugt (toter Code, Phase-4-Label).
- L4 IndexCommand.php:110: --status zeigt immer indexed 0 (record('indexed') wird nie gerufen) -> Admin liest "nichts indexiert".
- L5 QueueMapper.php:133: addOrderBy('is_update','ASC') wirkungslos hinter id-Sortierung.
- L6 text.py:125: Nur-Leerraum-HTML -> ParserError -> failed(corrupt) statt skipped(empty_text); verschluesseltes ZIP -> corrupt statt skipped(encrypted).
- L7 rewrite.py:139: type: nur am Tokenanfang; "muster -type:pdf" laesst Filter wirkungslos im Text.
- L8 sandbox.py:176: _files_handled++ nach _ask() ueberschreibt Recycle-Reset nach Timeout.

## Bestaetigt korrekt
commit->record->acknowledge verlustfrei in allen Fehlerpfaden; Upsert via Query.term_query idempotent; CRLF-Fix verschiebt keine Offsets (mb_strlen beidseitig); claimRow dialektneutral; describe()==null -> skipped(gone); Prefilter vor jedem Byte im /snippets-Pfad; XXE-Schalter gesetzt, kein extractall.
