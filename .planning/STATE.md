---
gsd_state_version: 1.0
milestone: v1.5
milestone_name: Umsteiger-Release
status: executing
stopped_at: Completed 31-12-PLAN.md
last_updated: "2026-10-12T12:10:00.000Z"
last_activity: 2026-10-12 -- Plan 31-12 abgeschlossen (Workflow-Commit lokal), als Nächstes 31-13
progress:
  total_phases: 7
  completed_phases: 1
  total_plans: 24
  completed_plans: 21
  percent: 14
---

# Project State

## Project Reference

Siehe .planning/PROJECT.md (Stand nach Phase 29, Milestone v1.5 gestartet) und .planning/MILESTONES.md (v1.0 bis v1.4).

**Core Value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 31, Formate, Nachholweg und POL-02

## Current Position

Phase: 31 von 30-36 (Formate, Nachholweg und POL-02)
Plan: 12 von 15 erledigt (31-01 bis 31-12), nächster Plan 31-13
Status: Phase 31 in Ausführung; 31-12 abgeschlossen (Saat der neuen Formate unter v1.4.2 in Store upgrade 2b, repeatedly_stuck in fester Reihenfolge, Aufzeichnung in 3c; 8cf62567 gepusht und CI grün, Workflow-Commit b021f16c LOKAL, Push nur zusammen mit 31-13 Task 1). FMT-01 bis FMT-06 Pending bis zum E2E-Beweis in 31-13 (Owner-Linie)
Last activity: 2026-10-12 -- Plan 31-12 abgeschlossen

Progress: [█░░░░░░] 1/7 Phasen; Phase 31: 12/15 Pläne

## Performance Metrics

- v1.4: 6 Phasen, 78 Plaene in 10 Tagen (Referenz)
- v1.5: 30-01 in ca. 21 min (3 Tasks, 9 Dateien)
- v1.5: 30-02 in ca. 35 min (2 Tasks, 7 Dateien)
- v1.5: 30-03 in ca. 45 min (2 Tasks, 7 Dateien)
- v1.5: 30-04 in ca. 40 min (3 Tasks, 14 Dateien)
- v1.5: 30-05 in ca. 75 min (2 Tasks, 3 Dateien)
- v1.5: 30-06 in ca. 60 min (2 Tasks, 2 Dateien)
- v1.5: 30-07 in ca. 55 min (2 Tasks, 3 Dateien)
- v1.5: 30-08 in ca. 50 min (2 Tasks, 10 Dateien)
- v1.5: 30-09 in ca. 75 min (3 Tasks, 4 Dateien)
- v1.5: 31-01 in ca. 105 min (4 Tasks, 15 Dateien)
- v1.5: 31-02 in ca. 85 min (2 Tasks, 39 Dateien)
- v1.5: 31-03 in ca. 85 min (2 Tasks, 8 Dateien)
- v1.5: 31-04 in ca. 75 min (2 Tasks, 5 Dateien)
- v1.5: 31-05 in ca. 90 min (2 Tasks, 9 Dateien)
- v1.5: 31-06 in ca. 230 min (2 Tasks, 15 Dateien; davon ca. 175 min ein swappender Gegenproben-Lauf)
- v1.5: 31-07 in ca. 130 min ohne Checkpoint-Wartezeit (3 Tasks, 10 Dateien)
- v1.5: 31-08 in ca. 120 min (2 Tasks, 6 Dateien)
- v1.5: 31-09 in ca. 75 min (1 Task, 6 Dateien)
- v1.5: 31-10 in ca. 150 min inkl. ca. 70 min CI (2 Tasks, 15 Dateien)
- v1.5: 31-11 in ca. 70 min inkl. ca. 25 min CI (3 Tasks, 12 Dateien)
- v1.5: 31-12 in ca. 55 min inkl. ca. 30 min Testläufe und CI (3 Tasks, 15 Dateien)

## Accumulated Context

### Decisions (Roadmap v1.5)

- Alle Schema-/Markenaenderungen des Milestones in Phase 30 in einem Schritt (cs-Koerperfeld, ggf. Archiv-Mitgliedsfeld), damit ein Re-Analyse-Umbau hoechstens einmal faellt; spaetere v1.5-Phasen aendern weder Schema noch Marken.
- Owner-Tor in Phase 30: Ausschlussmuster-Syntax, tschechische Stoppwortquelle/Lizenz, Trefferdarstellung Archiv + innere Datei, Umfang des Nachholwegs FMT-06.
- F-29-03 (POL-02) reist mit den Formaten in Phase 31 (gleicher Indexierpfad).
- Umstiegs-Doku (Phase 34) erst nach den Funktionsphasen, damit der Funktionsvergleich nur Geliefertes nennt.
- Stretch-Phase 35 kann ohne Release-Risiko entfallen; kein Modellwechsel in v1.5.

- 30-01: Tschechische Stoppliste = Lucene 10.5.2 gefaltet (167), Ausnahmen byt (Wohnung) und jez (Wehr), kein achtes Merkmal, ANALYZER_VERSION bleibt 1.
- 30-02: ces nur angeboten, OCR-Standard bleibt deu+eng+fra; Image-Probe CZ-01 auf amd64 und arm64 gruen (Lauf 38027012519).
- 30-03: LEGACY_SCHEMA_STEPS {(1,2),(2,3),(1,3)}; QUERYABLE_SCHEMA_GENERATIONS {2,3} ausgeschrieben, _of_the_marks fragt die Menge statt SCHEMA_VERSION; A5 bestaetigt (Ordnerfilter ueber files.path, kein zweiter Schemaschritt).
- 30-04: cs am Ende von SUPPORTED_LANGUAGES, ausserhalb Snowball (STEMMERLESS_LANGUAGES); body_cs als 14. Feld, neun Ketten unbedingt; SCHEMA_VERSION 3 mit GOLD_V1_5. Store upgrade 6 verlangt bereits Schema 2 vorher, 3 nachher (30-07 nur noch der cs-Teil). CZ-02 bleibt offen bis 30-05 bis 30-07.
- 30-05: Bestand (Schema 2, Schema 1) baut unter Schema-3-Code nicht um, cs an/aus per Bandlauf ohne Neu-Einbettung bewiesen; GROWTH_PER_LANGUAGE bleibt 0.40 (cs gemessen 0.358, es 0.361, 2000 Dokumente). CZ-02 offen bis 30-07, CZ-03 bis zur Doku (30-08/30-09).
- 30-06: Upgrade-Strecke startet von v1.4.2 (D-30-07); 1.4.2 urteilt die Saat richtig (Sidecar skipped/system_file, Bild indexed), recheck_1_4_0 done vor und nach dem Upgrade, Store upgrade 5 haelt alle neun Zaehler unveraendert und verlangt schemaVersion 2 und rebuildState idle per Wert; Andockblock fuer Phase 31 am Ende von Store upgrade 2b. deploy-harp-Lauf 38033629694 gruen ueber Store upgrade 0 bis 6. CZ-02 offen bis 30-07.
- 30-07: Store upgrade 6 schaltet de,en -> de,cs (ohne en, Pitfall 5), neuer Store upgrade 7 zurueck auf de,en; smlouve 1/1/1/1, proc 1/1/0/1, Schema 2 -> 3 -> 3, Lesestelle per Container-Probe de,cs bzw. de,en, vectors.db ueber beide Umbauten gleich. term_hits zaehlt bei Ein-Wort-Fragen keine Vektortreffer (one-term-Regel, api/search.py:307). Fuellkorpus 64 -> 256 (de,cs-Bandlauf sonst unsichtbar, Lauf 38035652649). deploy-harp-Lauf 38036946762 gruen ueber Store upgrade 0 bis 7. CZ-02 abgehakt.
- 30-08: Grenze CZ-03 in docs/language-analyzers.md (Abschnitt Czech, Langform, Lizenz) und als fuenfter Eintrag der Grenzliste in allen sechs Store-Texten, zeichengleich mit der Doku-Kurzliste, LIMITATION_COUNT 5 (D-30-06); Suchsprachen-/OCR-/env-Texte und READMEs nennen cs/ces. Wortlaut ist Entwurf (docs/store-listing.md 'Entwurf v1.5.0 (Teil Phase 30)'), Owner-Abnahme offen bis REL-05. PHP-Baumhash unveraendert (Rezept liest nur *.php). CZ-03 abgehakt.
- 30-09: Audit der Phase 30 (30-AUDIT.md, status fixed): 0 CRITICAL, 0 HIGH, 0 MEDIUM, 3 LOW. L-30-01 gefixt (Lucene-NOTICE und Lizenzpfad im ausgelieferten Modul stopwords_cs.py, 9e9764bf, im Image belegt); L-30-02 accept (Treffer nur über body_cs ohne Auszug, dokumentierte Grenze); L-30-03 accept (Vektordigest ungeprüft in GITHUB_ENV, mitnehmen, wenn Phase 31 deploy-harp anfasst). Platzannahme unabhängig gemessen: cs +0,287/+0,299 unter 0,40. CI Python gates 38042757203, HaRP 38042757174 grün.
- 31-01: olefile 0.47, xlrd 2.0.2, pillow-heif 1.8.0 exakt gepinnt (keine weiteren transitiven Pakete); THIRD-PARTY.md mit libheif 1.23.4, libde265 1.1.3 (LGPL-3.0), x265 4.2 (GPL-2.0-or-later), sieben Altversionen korrigiert, Versionsgate test_third_party_versions.py. Quellpflicht: vier gehashte Quellpakete (scripts/release/corresponding_source.py), Spiegel für :dev = Pre-Release source-1.5-dev.2 (source-1.5-dev blieb leer, unveränderlich). Repo veröffentlicht unveränderliche Releases: REL-05 muss release.yml die Quellpakete im gh release create mitgeben. Kein Nicht-v-Tag startet einen Workflow (test_workflow_tag_triggers.py). Image komprimiert +6,18 MB amd64, +7,29 MB arm64.
- 31-02: Skip-Code archive_limit (skipped, nur ZIP) in allen vier Codelisten; unsupported_variant allgemein gefasst, mime_not_allowed-Hilfe nennt Mails und ZIP-Dateien; fünf Sätze in 16 Katalogen und fünf Dokus (80 einzeln benannte Testfälle). Sichtbarer Wortlaut sagt ZIP file/ZIP-Datei, weil die Vokabelregel E-H2 den Wortstamm in deutscher Prosa und in docs/store-listing.md sperrt; Codename deshalb nur in docs/formats.md (Abschnitt Skip codes). VERDICTS_GENERATION 3 auf beiden Seiten, Container kennt {2, 3}, archive_limit an 2 und ohne Signal als too_large/corrupt; öffentliche SKIPPED_FALLBACK_WITHOUT_SIGNAL für 31-11; recheck_1_4_0 startet bei 2 und 3; Upgrade-Reihenfolge (Backend zuerst) in docs/formats.md. Wortlaut Entwurf, Owner-Abnahme bei REL-05.
- 31-03: POL-02 (F-29-03) im Code: ShortRead trägt written und content_hash (Hash füllt _stream_into aus dem _HashingSink, der Client hasht nicht); _fetch_file nimmt zwei kurze Antworten mit gleicher Länge UND gleichem Hash als die echte Datei (Scratch des zweiten Versuchs, Größe = tatsächliche, kein dritter Download), 0 Bytes zweimal -> failed(empty_file), verschiedene kurze Antworten bleiben D-29-04. Keine Längenausnahme; Restrisiko A8 (Proxy kappt byte-genau gleich) in Docstring, docs/formats.md "Stale file cache size" und SUMMARY, Owner-Veto möglich. Bereits aufgegebene repeatedly_stuck-Zeilen holt 31-11 nach. CI Python gates 38098844595 und sieben weitere grün.
- 31-04: extract/mail.py (extract_eml, noch nicht in Dispatch/Allowlist, Freischaltung 31-10): Subject/From/To/Cc dekodiert, Body plain vor HTML über text.html_to_text (gemeinsame gehärtete Strecke, extract_html unverändert), Anhänge nur als Namen über clean_display_name (Bidi/Steuerzeichen raus, 255 Zeichen; 31-08 nutzt sie für ZIP-Namen). count_parts zählt öffnende Begrenzerzeilen deklarierter Boundaries vor dem Parsen (alle Schreibweisen inkl. RFC 2231, CR-Zeilenenden), über MAX_MAIL_PARTS 1000 nur Kopfzeilen -> indexed(truncated). RecursionError (Parser, get_body, iter_attachments, get_content) -> failed(corrupt) detail RecursionError; kaputte Kopfzeile wird ausgelassen. 2500 multipart-Ebenen enden an der Vorzählung (Plan-Widerspruch dokumentiert). CI Python gates 38101409837 und sechs weitere grün.
- 31-05: extract/legacy_doc.py (extract_msword mit Sniff OLE/RTF/DOCX/HTML, extract_doc, noch nicht in Dispatch/Allowlist, Freischaltung 31-10; 31-06 nutzt extract_doc für OLE unter .docx): olefile mit DEFECT_INCORRECT, Text über FIB/Clx/PlcPcd nach [MS-DOC] 2.4.1, A1 (fcClx 0x01A2/lcbClx 0x01A6) gegen FibRgFcLcb97 und LibreOffice-Dateien belegt, komprimierte Stücke mit Sondertabelle 2.9.73 (nicht cp1252). Urteile: fEncrypted -> encrypted (fObfuscated allein ignoriert, wie FibBase verlangt), nFib < 0x00C1 oder kein WordDocument -> unsupported_variant, sonst CorruptDocument -> failed(corrupt). Eigener Schutz zusätzlich zu olefile: FAT-Größe gegen Dateigröße vor dem Öffnen (20 000 deklarierte FAT-Sektoren kosten olefile 29 s), zweiter Kettenlauf mit Besuchsmenge (olefile liefert Zyklen still als Wiederholung), RecursionError bei tiefem Verzeichnisbaum. Fixtures aus LibreOffice 26.2.4.2 mit Suchwörtern wortquendel/glyphquendel/zellquendel (Saat für 31-12); build_cfb kann Ströme. CI Python gates 38105517809 und sechs weitere grün.
- 31-06: extract/legacy_xls.py (extract_msexcel mit Sniff OLE/XLSX/Markup/Text, extract_xls über xlrd mit on_demand, ragged_rows=True, Logsenke im Speicher, Zellgrenze max_cells; noch nicht in Allowlist für application/vnd.ms-excel, Freischaltung 31-10). Werte zeichengleich mit extract_xlsx derselben Quelle (3 ohne .0, Datum als str(datetime), #DIV/0!). Zählregel wie XLSX (was die Bibliothek liefert, leere Zellen mit), xlrd liefert mit ragged_rows aber nur bis zur letzten Zelle je Zeile, openpyxl das Rechteck. Befund 9: xlrds CFB-Leser folgt einer Ministrom-Kette ohne Besuchsmenge (Zyklus = Endlosschleife mit wachsendem Speicher); deshalb vor xlrd cfb.check_fat_size, olefile, cfb.walk_stream für Workbook und Book, mit ENDOFCHAIN-Pflicht am Kettenende. Kettenprüfungen aus legacy_doc nach cfb.py verschoben (detail bei .doc-Kettenfehlern jetzt cfb.CorruptCompoundFile). cfb.ole_kind ersetzt ole_verdict und entscheidet nach den Strömen an der Spitze des Verzeichnisbaums: Word/Excel unter .docx/.xlsx/.pptx werden nach Inhalt gelesen, legacy_format nur noch PowerPoint und bekannte Namen außerhalb der Baumspitze; OLE ohne bekannten Namen bleibt failed(corrupt) wie bisher. CI Python gates 38119372322 (5198 passed) und sechs weitere grün.
- 31-07: pillow-heif im Bildpfad (thumbnails/depth/aux aus, decode_threads=1), abgeschnittene HEIC -> failed(corrupt), HEIF über der Schätzung -> skipped(too_large). Checkpoint ausgelöst (48 MP too_large, Lauf 38121953472); Owner-Entscheid: MALLOC_ARENA_MAX messen, Fall A eingetreten: mallopt(M_ARENA_MAX, 1) nur im Extraktionskind (sandbox._limit_malloc_arenas), fester HEIF-Anteil 160 -> 32 MiB, 48 MP mit 15,7/17,0 % Rest unter 512 MiB indexed (Lauf 38125992894), Text-/OCR-Weg unverändert; Limit bleibt 512 MiB. HEIF-Schätzung = 80 MiB + 7 B/px (RGB), 9 B/px sonst, statt Faktor. FMT-05 offen bis 31-10. Offen für 31-15: JPEG failed(out_of_memory) gegen HEIF skipped(too_large).
- 31-08: extract/archive.py (extract_zip, noch nicht in Allowlist/Dispatch, Freischaltung 31-10 nach dem Snippet 31-09): Köpfe des Zentralverzeichnisses selbst gezählt nach der Schleife von zipfile (Endsatz und ZIP64-Locator wie CPython _EndRecData/_EndRecData64, Locator wird immer gelesen), Zahl im Endsatz nie geglaubt; ZipFile erst danach. Ein _ArchiveBudget für alle Ebenen (Einträge, Verzeichnisbytes, deklarierte und gelesene Bytes, Mitglieder mit Text, Frist). Grenzen gemessen, alle Startwerte D-31-07 bestätigt: 10 000 Einträge (5,5 MiB), Verzeichnis 8 MiB neu (ZipFile an beiden Grenzen 19,5 MiB), 256 MiB, Rate 100:1 ab 1 MiB (reale Dateien bis 17,9:1, Deflate 1028,6:1), Tiefe 2, 1 000 Mitglieder (11,7 ms je Mitglied), Zeitanteil 0,75. Text = Abschnitte U+001C + bereinigter Name + Zeilenumbruch + Text, auch Namen ohne Text; kein OCR. Mitglieder als <scratch>.m<n>.part (Poller-Sweep räumt Reste). Bombenkorpus mit echtem 720-Byte-Quine, Kind mit Selbstabbruch; 18 Gegenproben rot. CI Python gates 38129929315 (5277 passed) und sechs weitere grün.
- 31-09: Auszug eines ZIP-Treffers beginnt mit "<innere Datei>: " in snippets_for und _passage_of; Name aus dem gespeicherten body_de an der letzten Marke U+001C vor dem ersten Highlight (nicht vor dem Fragmentanfang: tantivy beginnt das Fragment einer kurzen ZIP-Datei im ersten Mitglied, gemessen), Highlights erst in Zeichen umgerechnet, dann um entfernte Marken und den Präfix verschoben. Präfix nur bei gespeichertem ext zip; U+001C aus jedem Auszug entfernt. cap_text(text, *, member_marks=False) entfernt U+001C, nur archive.py setzt member_marks=True (Befund 15). Kein Schemafeld, SCHEMA_VERSION 3 (D-30-08). 10 Gegenproben rot. CI Python gates 38132651127 (70be3383) und 38133773017 (ddaa4c51) samt allen weiteren Läufen grün.
- 31-10: message/rfc822, application/zip, application/msword, application/vnd.ms-excel, image/heic, image/heif in dispatch.ALLOWED_MIMETYPES und StorageService::ALLOWED_MIMETYPES (a14c03c3, ein Commit), Routen MAIL/ZIP/DOC/XLS, HEIC/HEIF über Route.OCR; gemeinsamer Begründungsabsatz an beiden Listen, Paritätstest vergleicht ihn. OCR_CERTAIN_MIMETYPES + HEIC/HEIF. TYPE_GROUPS: doc/dot, xls/xlt, heic/heif; zip in keiner Gruppe (D-31-05), Grenze in docs/search-filters.md. Migration Version001500Date20261012000000: markScanStale, dann backend_app_version verwerfen; kein Containeraufruf. Kind-Test extract_guarded für eml/zip/doc/xls (2a5ad6a5). CI a14c03c3 alle acht grün (Python 38223115485, PHP 38223115697 mit 598 Tests, HaRP 38223115654 Store upgrade 0 bis 7); auf 5cba95fc alle acht grün (HaRP 38227673884). FMT-01 bis FMT-05 Complete, Live-Beweis Upload bis Treffer folgt mit der Saat 31-12/31-13.
- 31-11: Nachholweg FMT-06 im Container. worker/catchup.py Teil A unter recheck_1_5_0 (fehlt/Ziffern/reconcile/done): legacy_format außer PowerPoint, nicht indexierte Zeilen der sechs neuen Typen (Mimetyp, Endung nur ohne Mimetyp), einmal jede repeatedly_stuck-Zeile; Start bei Generation 3 nach recheck_1_4_0. Teil B: Marke reconcile macht den Abgleich sofort fällig (Ruhe-Tor bleibt), der erste Durchgang unter der Marke spult alle Cursor zurück, give_up-Zweig ohne Containerzeile wird Arbeit, Neu-Urteil nur bei exaktem 1.3-Ersatzcode (SKIPPED_FALLBACK_WITHOUT_SIGNAL importiert, known_skip_reasons einmal je Seite), done nur nach einem unter der Marke begonnenen vollständigen Zyklus. Einmal-Modus Reconcile.run(once=True) in main._CATCHUP_RECONCILE bei FINDLING_RECONCILE_ENABLED=false, active_reconcile() bleibt None, _armable_tasks an allen Arm-Stellen. FMT-01 bis FMT-05 auf Owner-Wort zurück auf Pending bis 31-13 (a646061d). CI 1a18e4b2 alle sieben grün (Python 38238806249, HaRP 38238806189 Store upgrade 0 bis 7, Resilience 38238806242).
- 31-12: Saat der neuen Formate (.github/fixtures/upgrade-seed-formats, Generator scripts/ci/make_upgrade_seed_formats.py, ZIPs von Hand, Bombe Tiefe 3 plus Nullbytes 158:1, 7095 Byte). Store upgrade 2b am ehemaligen Andockblock: sieben Dateien per WebDAV (1.4.2 reiht die sechs neuen Typen und die Bombe nie ein, Word-OLE unter .docx skipped/legacy_format), .txt in fester Reihenfolge (docker stop, Upload, Größe in oc_filecache und Queue +4096, docker start, Sperre je Auslieferung um 3600 s zurück; 3 kurze Lesungen, vierter Claim schreibt failed/repeatedly_stuck), vorher Warten auf den ersten Abgleich-Zyklus (sonst give_up-Zeile möglich), danach Größe per sqlite3 zurück; state.db 0 Zeilen. 3c: recheck_1_5_0 absent, Altbestand ohne Nachhol-Kandidaten (gegen die Ermittlung gehalten), UPGRADE_OLD_STOCK_DIGEST über file_id/state/reason/etag/Chunk-Zahl. Checkpoint nicht ausgelöst. CI 8cf62567 alle sieben grün (Python 38244385443, HaRP 38244385580). b021f16c ungepusht.

### Offene Faeden (kein aktiver Auftrag)

- Owner-Veto zu A8 (31-03) möglich: dann Längenausnahme aus dem ersten Planstand.
- 31-13: b021f16c (Workflow 31-12) liegt lokal und darf nur zusammen mit 31-13 Task 1 gepusht werden, vorher nichts pushen. Live-Beweis Upload bis Treffer für die neuen Typen, recheck_1_5_0 in Store upgrade 5 done, Logzitate der 1.4.2-Saat aus 2b/3c übernehmen; STALE "indexed" setzt das Rücksetzen der Dateicache-Größe in 2b voraus. FMT-01 bis FMT-06 stehen bis dahin auf Pending (Owner-Linie).
- 31-15 (Audit): Kosten des gezielten Neu-Urteils (known_skip_reasons je Seite) mit realistischem Anteil messen; erneutes Zurückspulen nach Neustart mitten im Nachholzyklus auf großen Instanzen bewerten.
- 31-14: Kosten von str.find je ZIP-Treffer auf großem ZIP-Text messen (T-31-30).
- 31-15 (Audit): Umbenennungsweg des Pollers (_rewrite_metadata) übernimmt den gespeicherten Text; eine vor 1.5 indexierte .txt mit U+001C, umbenannt zu .zip, bekäme bis zur nächsten Inhaltsextraktion einen Präfix aus der eigenen Zeile; bewerten.
- 31-15 (Audit): Office-Mitglied in einer ZIP-Datei öffnet seine eigene ZipFile ohne Kopfzählung (wie eine einzelne DOCX), begrenzt durch max_file_bytes und Frist; bewerten.
- 31-15 (Audit): ENDOFCHAIN-Pflicht in cfb.walk_stream (gilt seit 31-06 auch für .doc) und FAT-Schranke an echten Bestandsdateien prüfen.

- REL-05 (Phase 36): release.yml muss die vier Quellpakete (corresponding_source.py fetch) im eigenen gh release create mitgeben; ein späteres gh release upload scheitert an unveränderlichen Releases (belegt in 31-01). Leeres Pre-Release source-1.5-dev bleibt mit Verweistext, Löschen nur mit Owner-Wort.

- Owner-Abnahme der fünf Urteilssätze von 31-02 (archive_limit, unsupported_variant, mime_not_allowed) bei REL-05; Entwurf in docs/store-listing.md Teil 4 und docs/formats.md Abschnitt Skip codes.

- Owner-Abnahme des Wortlauts des fuenften Grenz-Eintrags Tschechisch (en/de/fr) samt Suchsprachen-/OCR-/env-Texten bei REL-05 (Phase 36); Entwurf in docs/store-listing.md 'Entwurf v1.5.0 (Teil Phase 30)'.

- Vier box-gebundene Feldbelege warten auf die naechste Anfahrt (D-29-11).
- Issues #15/#18/#19/#21/#22 bleiben offen, bis der Melder bestaetigt; Schliessen nur mit
  Owner-Wort je Issue.

- Reddit-Post-Entwurf liegt verifiziert in Outlook ("Reddit-Entwurf: Findling 1.4.0 + MCP
  Connector"); Konto-Appeal pruefen, Owner postet selbst.

- Dev-Instanz (Port 8090) lief am 06.10. mit Abnahme-Testdateien und Backend-Hostprozess;
  bei Gelegenheit aufraeumen.

### Blockers/Concerns

- Kill-Kriterium Nextcloud (ES-freie Volltextsuche mit OCR angekuendigt -> Neubewertung) weiter beobachten.

## Session Continuity

Last session: 2026-10-12T12:10:00.000Z
Stopped at: Completed 31-12-PLAN.md
Resume file: None
