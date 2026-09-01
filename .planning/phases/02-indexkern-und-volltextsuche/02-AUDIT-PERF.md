# Performance-Audit Findling Phase 2 (01.09.2026, Stand c17a362)

Kurzfazit: Architektur-Grundentscheidungen richtig (Cursor-Paginierung, Streaming-Fetch, 1 Client/Writer/Kind je Prozess, Baenderung, Deckel vor teurer Arbeit). 43-MB-Automat: KEIN Problem (1,05% von 4 GB; existiert exakt 1x je Prozess, register_tokenizer teilt per Arc-Clone, gemessen; Phase-5-Risiko sind OCR 300-600 MB/Seite + Embeddings, nicht der Automat). Empfehlung: Budgetzeile 43 MB festschreiben, nouns-Schalter existiert, mmap in tantivy-py nicht machbar.

## HIGH
- H1 index/search.py:120: candidates() laedt via searcher.doc() den KOMPLETTEN gespeicherten Volltext je Treffer (body_de stored), braucht aber nur file_id/mtime/ext. Gemessen: Suche 0,014 ms, +doc() bei 512k-Cap 20,5 ms (99,9%); limit=64 -> 98 ms. Fix: Searcher.fast_field_values (file_id/mtime sind fast=True) -> groessenunabhaengig 0,02 ms (Faktor 394x); ext aus Candidate streichen (PHP kennt Namen/Endung ohnehin aktueller; ext wird nur im Index fuer type:-Filter gebraucht). Kein Reindex noetig.
- H2 StorageCrawlJob.php:114 -> QueueMapper.php:90: 2000 Einzeltransaktionen je Slice (kein beginTransaction) -> 2-6 s reine Commit-Zeit von 30 s Budget auf eMMC/SD; 100-300 s ueber 100k Dateien. Fix: Slice klammern oder Baender von 200-500.
- H3 QueueMapper.php:129-134: claimBatch (locked_at IS NULL OR locked_at<=?) ORDER BY id hat keinen passenden Index (findling_q_locked nur locked_at) -> PK-Scan waechst mit gehaltenem Queue-Kopf. Fix: locked_at NOT NULL DEFAULT epoch als Frei-Marke + Index (locked_at,id), freeRowCondition wird Single-Range.
- H4 QueueMapper.php:139-165/305-313: 32 Einzel-UPDATEs + bumpRetries je Claim = 34 Roundtrips; ~106k Statements ueber 100k Dateien. Fix: UPDATE ... SET locked_at=?, retries=retries+1 WHERE id IN(...) AND frei; dann SELECT WHERE locked_at=?.
- H5 Provider.php:190 vs ExAppService.php:52: Deadline-Check nur VOR dem Call; 2,49 s bestanden + 1,5 s Call = real ~4,0 s statt dokumentierter 2,5 s; Unified Search wartet auf alle Provider. Fix: Timeout je Call = min(1.5, Restbudget), Calls unter ~0,3 s Rest gar nicht absetzen.

## MEDIUM
- M1 poller.py:313: _open() (SQLite-Connect+Schema, build_artifact 276k Zeilen+SHA, open_index 0,44s Automat, Scratch-Glob) laeuft SYNCHRON auf dem Event-Loop -> ARM geschaetzt 1,5-3 s Heartbeat-Stillstand beim Aktivieren. Fix: await asyncio.to_thread(self._open).
- M2 poller.py:328/481: verdicts haelt outcome.text des GANZEN Batches bis nach Commit (16,8-33,6 MB bei 32 Docs am Cap; ein Eurozeichen verdoppelt den String), text wird in _record_verdicts NIE gelesen. Fix: in _collect dataclasses.replace(outcome, text="").
- M3 text.py:105/113/137 + odf.py:64 + pdf.py:93: ganze Datei in RAM, Cap greift erst danach (50-MB-Text -> 3 Kopien; ODT-content.xml ohne Groessengrenze = Dekompressionsbombe; RLIMIT faengt als out_of_memory statt indexed(truncated), Windows ohne Grenze). Fix: extract_plain liest nur cap*4 Bytes; ODF ZipInfo.file_size pruefen; PDF-Schleife abbrechen sobald Summe > Cap. (Deckt Bug-Audit M6.)
- M4 Provider.php:194 vs 183: Overfetch limit*4 je Runde (240 ueber 3 Runden) vs Recheck-Budget min(64, limit*2)=40 -> 73% der geholten Kandidaten nie pruefbar, jeder kostet H1-doc(). Fix: Limit = min(limit*OVERFETCH, Restbudget+limit). Nebenbefund: SEARCH_OVERFETCH/SEARCH_ROUNDS in config.py:142 werden NIRGENDS gelesen (Doppelablage zu Provider.php:57,75,76).
- M5 QueueService.php:268-289: usersFor() ohne Obergrenze -> instanzweiter Team Folder = komplette Nutzerliste je Datei (5000 Nutzer x 32 Dateien = ~16 MB Heap + 3,5 MB JSON). Fix: Cap (z.B. 500) + Marker userIdsTruncated:true -> Vorfilter darf fuer diese Datei nicht filtern.
- M6 Migration:84: toter Index findling_q_stor (storage_id,root_id) - keine Query nutzt ihn. In H3-Migration entfernen.
- M7 QueueMapper.php:89-96 + FileStateService.php:119-126: Insert-und-Konflikt-fangen im Massenpfad (100k Exceptions beim Re-Crawl). Fix UPDATE-first, bei 0 rows INSERT. WICHTIG-Korrektheit: record() innerhalb offener Transaktion bricht auf PostgreSQL die GANZE Transaktion (aborted) -> Ack schlaegt fehl, Queue nie leer; MariaDB/SQLite nicht betroffen; UPDATE-first erledigt das mit.
- M8 QueueService.php:217: getUserFolder() je Queue-Zeile statt je Nutzer (32 Mount-Setups je Request). Fix: lokaler Folder-Cache je claim().
- M9 QueueService.php:143-159 + MAX_LIST_LENGTH 1000: bis ~2000 Statements in EINER Transaktion blockiert SQLite-Writer der ganzen NC. Fix: MAX_LIST_LENGTH auf 256 oder je Band committen.

## LOW
- writer.py:167 should_flush toter Code (nur bench ruft); _pending_bytes erzeugt UTF-8-Vollkopie je Dokument fuer ungelesenen Zaehler; claim(max_bytes) zaehlt DATEI-Groessen nicht Textgroessen.
- nc/client.py:79/209: CHUNK_SIZE 64k -> 800 to_thread-Hops je 50-MB-Datei (40-120 ms ARM); 1 MiB Chunks.
- repo.py:496 acl_totals COUNT(DISTINCT) Full-Scan (nur Statusseite).
- resources.py:181 degraded() je Suche (read_meta+disk_usage) cachebar.
- search.py:198 char_ranges dekodiert Praefix je Range neu (O(n*m)).
- QueueMapper/Service Off-by-one MAX_ATTEMPTS: 4 Auslieferungen statt 3.
- Provider.php:347 in_array O(n*m) -> array_flip+isset.
- resilience.yml: timeout-minutes fehlt ueberall (Default 360 min); "Wait until nothing open" dauerte 0 s -> misst das Gate den 900-s-Lock-Fall wirklich? Entscheiden. timeout-minutes 15/10 setzen.

## Abarbeitungsreihenfolge (Empfehlung des Auditors)
1. H1 (groesster Hebel, kein Reindex) 2. H5+M4 (gleiche Zeilen) 3. H2 4. M1+M2 (je 1 Zeile) 5. H3+H4+M6 (eine Migration) 6. Rest.
Messskripte im Scratchpad (m_doc.py, m_fast.py, m_snip.py, m_auto2.py, rssmod.py).
