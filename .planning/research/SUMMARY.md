# Project Research Summary

**Project:** Findling (Nextcloud Zero-Config-Suche ExApp)
**Domain:** Nextcloud-ExApp fuer Volltext-, OCR- und Semantiksuche, Zielgruppe Selfhoster und kleine Organisationen auf 4-8 GB RAM (oft ARM)
**Researched:** 2026-08-15
**Confidence:** HIGH

## Executive Summary

Findling repariert die kaputte Nextcloud-Suche mit einem einzigen ExApp-Container (OCR, deutsches Volltext-Stemming, semantische Suche) plus einer schlanken PHP-Companion-App, die den Unified-Search-Provider registriert und an den Container proxied. Das ist notwendig, weil AppAPI selbst keine Suchanbieter registrieren kann, wie die Recherche aus dem Nextcloud-Quellcode zweifelsfrei bestaetigt. Vorbild fuer das Proxy-Muster ist Context Chat, das aber selbst keinen Search-Provider registriert. Die Kombination "IProvider in PHP ruft eine ExApp per exAppRequest" existiert nirgends im Oekosystem als fertiges Beispiel und ist damit das groesste Integrationsrisiko des Projekts, weshalb sie im Bauplan konsequent an erster Stelle steht.

Die Recherche empfiehlt eine embedded Volltext-Engine statt eines zweiten Serverprozesses. Nach Owner-Entscheid ist das Tantivy (deutsches Snowball-Stemming, Kompositabehandlung, eingebaute Snippets), nicht FTS5, weil FTS5 kein deutsches Stemming beherrscht und Meilisearch als Sidecar das Zero-Config-Versprechen bricht. Vektorspeicher und Zugriffsrechte bleiben in SQLite mit sqlite-vec: der ACL-Filter wird als Kandidaten-Vorfilter direkt in SQL gezogen, und die letzte Instanz ueber Sichtbarkeit bleibt ein finaler Recheck in der PHP-Companion-App gegen getUserFolder()->getFirstNodeById(). Das trennt sauber zwei Fragen: Tantivy und SQLite liefern schnelle Kandidaten, Nextcloud selbst entscheidet endgueltig, wer was sehen darf. OCR laeuft als direkter Tesseract-Subprozessaufruf auf pypdfium2-gerenderten Seiten, nie als Rueckschreib-Operation auf die Originaldatei, weil genau das die Vorgaenger-App (files_fulltextsearch_tesseract) zum Datenverlust gebracht hat. Embeddings sind lokal, CPU-only, quantisiert (multilingual-e5-small, int8, MIT-lizenziert, ins Image gebacken).

Das groesste Risiko ist nicht fehlende Funktionalitaet, sondern Betriebsrobustheit: Das offizielle fulltextsearch-Framework ist nicht an Features gestorben, sondern an haengenden Indexlaeufen ohne Fortschrittsspeicher, stillen Ausfaellen, Datenverlust durch die OCR-Zusatzapp und verpassten Nextcloud-Major-Releases. Diese Fehlermodi sind fuer Findling keine "Polish spaeter"-Punkte, sondern Kernfunktionalitaet: Fortschritt gehoert von Tag eins in eine Datenbank statt in den Prozessspeicher, jedes Ergebnis muss vor der Snippet-Ausgabe eine Rechtepruefung durchlaufen, und Events sind ein Beschleuniger, niemals die Wahrheitsquelle, sie muessen durch einen periodischen Abgleichlauf gegen oc_filecache abgesichert werden. Ein zweiter, gleichrangiger Risikoblock ist die Nextcloud-Produktentwicklung selbst: Das fulltextsearch-Oekosystem wurde am 12.08.2026 von Nextcloud GmbH reaktiviert (35.0.0beta1), womit "wir sind die einzige lebende Suche" als Positionierung entfaellt. Was traegt: kein Elasticsearch, eingebautes OCR, kleines RAM-Budget, sichtbarer Indexstatus und Pro-Datei-Diagnose, Punkte, die weder das reaktivierte Framework noch Context Chat (12 GB RAM-Bedarf, kein OCR, respektiert files_accesscontrol nicht) liefern.

## Key Findings

### Recommended Stack

Die Engine-Entscheidung ist per Owner-Grilling final aufgeloest: Tantivy als Volltext-Engine im ExApp-Prozess (nicht FTS5, nicht Meilisearch), kombiniert mit einem SQLite-ACL-Vorfilter auf Kandidatenlisten und einem finalen PHP-Recheck als Sicherheitsgrenze. Die urspruengliche STACK-Empfehlung (Tantivy wegen deutschem Stemming) und die urspruengliche ARCHITECTURE-Empfehlung (FTS5 in einer Einzeldatei wegen des SQL-Joins fuer ACL) sind damit zusammengefuehrt: Tantivy liefert die Sprachqualitaet, SQLite bleibt Traeger von Vektoren, Metadaten und der ACL-Tabelle, und der ACL-Join findet als Vorfilter auf Kandidaten-IDs statt, nicht als Tantivy-interner Join. Alle anderen Architekturmuster (Pull-Queue, Mount-Crawl, Content-Gateway, deklarative Access-Aktionen, Bauteihenfolge) bleiben unveraendert gueltig.

**Core technologies:**
- Tantivy 0.26.0 (Python-Bindings): Volltext-Engine mit deutschem Snowball-Stemming, Stoppwoertern, Komposita-Filter und eingebautem SnippetGenerator, der einzige Kandidat, der deutsche Sprachqualitaet ohne Eigenbau liefert
- SQLite + sqlite-vec 0.1.9: Vektorspeicher (int8, brute-force-KNN) plus ACL-Tabelle und Statusdaten, ein Datenbankfile, ACL-Filter als SQL-Join beziehungsweise Vorfilter, kein zweites Konsistenzsystem
- fastembed 0.8.0 + intfloat/multilingual-e5-small (384 dim, MIT): lokale, CPU-only Embeddings, selbst int8-quantisiert und ins Image gebacken (kein Laufzeit-Download, HF_HUB_OFFLINE=1)
- Tesseract 5.5.0 (Subprozess) + pypdfium2 5.13.0: OCR nur wo noetig (Text-Layer-Erkennung pro Seite), kein OCRmyPDF im Indexpfad, Original bleibt bitweise unveraendert
- nc_py_api[app] >= 0.30.3 (async-only) + FastAPI + uvicorn: ExApp-Geruest, Sync-API faellt in 0.31.0 weg
- python:3.13-slim-trixie (glibc, nicht Alpine): einziges Basisimage mit Wheels fuer alle Kernabhaengigkeiten auf aarch64 und cp313 ohne Compiler im Build
- PHP-Companion-App (IProvider, nie IExternalProvider) + IFilteringProvider: einziger Weg zur Unified Search, da AppAPI selbst keine Suchanbieter registrieren kann

### Expected Features

Das offizielle fulltextsearch-Framework wurde am 12.08.2026 reaktiviert, was die reine "wir leben noch"-Positionierung entwertet. Die verbleibenden Differenzierer sind eingebautes OCR ohne Originaldatei-Risiko, semantische Suche im 4-8-GB-Budget, und radikale Transparenz ueber den Indexstatus.

**Must have (table stakes):**
- Volltextsuche ueber PDF/Office/ODF/Text/Markdown inklusive Dateiname und Pfad
- Berechtigungsfilter zur Suchzeit inklusive Nutzer-Shares, Gruppen-Shares, Team Folders, der haeufigste Funktionsbruch der Altapp
- Inkrementelle Indexierung ueber Datei-Events inklusive Loeschen, Umbenennen, Verschieben, Papierkorb, Share-Aenderung
- Sichtbarer Indexstatus (laeuft/pausiert/Fortschritt/Fehler) und Reindex-/Reset-Werkzeuge, fehlte bei der Altapp komplett
- Ressourcendeckel (Worker-Anzahl, OCR-Drosselung, Resume nach Abbruch, kein OOM-Loop)
- Minimale Query-Syntax (Phrase, +, -) und Unicode-/Umlaut-Robustheit

**Should have (competitive):**
- OCR automatisch, ohne Workflow-Konfiguration, Originaldatei bleibt unveraendert (starkes Vertrauensargument nach der Tesseract-App-Vorgeschichte)
- Semantische Suche hybrid mit BM25 (RRF), findet Umschreibungen und deutsche Komposita
- Zero-Config mit RAM-Deckel und ARM-Tauglichkeit als explizites Produktversprechen (Context Chat verlangt 12 GB)
- Pro-Datei-Diagnose ("warum ist diese Datei nicht auffindbar") und Vorab-Schaetzung vor dem Erstindex

**Defer (v2+):**
- Eigene Ergebnisseite mit Paginierung, Pfadfilter, Tags als Filter (v1.x, ausgeloest durch Nutzerfeedback)
- Sprung zur Fundstelle im Viewer, weitere OCR-Sprachen, Mehrmandantenfaehigkeit, Federated Search (v2+)
- Explizit Anti-Feature: RAG-Chat, Elasticsearch-Backend-Option, volle Lucene-Syntax, Rueckschreiben des OCR-Textlayers in die Originaldatei, Index komplett im RAM

### Architecture Approach

Sechs Muster tragen das System: Pull- statt Push-Indexierung (Container holt Arbeit aus einer OCS-Queue ab, PHP-Cron kann nicht timeouten), Crawl pro Mount statt pro Nutzer mit Integer-Cursor auf fileid (Groupfolder werden einmal statt N-mal verarbeitet), Berechtigungen als schmale ACL-Tabelle im Index mit finalem PHP-Recheck (Zugriffsaenderungen kosten nur Zeilen-Inserts, keine Neuextraktion), ein Content-Gateway in der PHP-App statt WebDAV-Impersonation aus dem Container, sowie IProvider (nie IExternalProvider, das ist in der Unified Search standardmaessig ausgeschaltet).

**Major components:**
1. PHP-Companion-App (SearchProvider, Event-Listener, Crawl-Jobs, OCS-Queue-API, Content-Gateway), winzige, stabile Flaeche gegen NC-Major-Bruch
2. ExApp-Container (Fetcher/Extract/OCR/Embed-Worker-Pools, getrennt von der HTTP-Ebene), Tantivy plus SQLite (Vektoren, ACL-Vorfilter, Status) im selben Prozess
3. Reconcile-Job (periodischer ETag-/mtime-Abgleich), die Wahrheitsquelle, wenn Events verloren gehen
4. Hybrid-Retrieval (Tantivy-Kandidaten + Vektor-Kandidaten, RRF-Fusion, ACL-Vorfilter, finaler PHP-Sichtbarkeitscheck vor jeder Snippet-Ausgabe)

### Critical Pitfalls

1. Haengender Indexlauf ohne Fortschrittsspeicher: Fortschritt gehoert in eine Datenbank-Zustandsmaschine (pending/claimed/done/failed), nie in den Prozess-RAM; Stale-Claim-Reaper und harte Subprozess-Timeouts sind Pflicht, nicht Kuer
2. OCR-Pipeline zerstoert Nutzerdaten: der Indexer darf Nutzerdateien ausschliesslich lesen, OCR arbeitet auf einer Scratch-Kopie und liefert Text statt einer neuen Datei; per Grep-Gate und Pruefsummenlauf ueber ein Korpus mit defekten PDFs durchsetzen
3. Berechtigungsleck ueber Treffer, Snippets, Trefferzahlen: einziges K.-o.-Kriterium des Projekts, Snippet-Erzeugung erst nach bestandener Rechtepruefung, Trefferzahlen erst nach dem Filtern, Nutzer-ID ausschliesslich aus dem AppAPI-Header, nie aus dem Request-Body
4. Event-Luecken erzeugen unbemerkten Index-Drift: AppAPI-Events sind laut Doku ausdruecklich asynchron ohne Zustellgarantie; ein periodischer Abgleichlauf gegen oc_filecache ist die Wahrheitsquelle, Events nur ein Beschleuniger
5. Multi-Arch-Falle beim Image-Bau: Alpine/musl hat fuer Tantivy, onnxruntime und sqlite-vec keine Wheels; glibc-Basisimage (python:3.13-slim-trixie) und Modelle ins Image backen sind nicht verhandelbar

## Implications for Roadmap

Die Bauteihenfolge aus der Architektur-Recherche folgt einem klaren Prinzip: das unbewiesenste Stueck zuerst (die IProvider-ExApp-Proxy-Kombination hat kein Vorbild im Oekosystem), das teuerste, aber gut kalkulierbare Stueck zuletzt (Embeddings). Diese Reihenfolge wird unten uebernommen und um Admin-Sichtbarkeit, Haertung und Store-Einreichung ergaenzt. Sie deckt sich mit dem Owner-Entscheid, v1.0 (Volltext + OCR) vor v1.1 (Semantik, 4-6 Wochen spaeter) auszuliefern: Phasen 1-4 plus 6-8 bilden v1.0, Phase 5 wird fuer v1.1 nachgezogen.

### Phase 1: Foundations & Integrationsbeweis
Rationale: Die Kombination IProvider (PHP) ruft exAppRequest (ExApp) existiert nirgends als fertiges Beispiel im Oekosystem, das groesste Integrationsrisiko muss zuerst entkraeftet werden, mit minimalem Code (fest verdrahteter Treffer).
Delivers: ExApp-Skeleton (nc_py_api async, FastAPI, HaRP-Handshake), PHP-Companion-App mit registriertem IProvider, ein Treffer aus dem Container erscheint nachweislich in der Unified Search. App-ID und Anzeigename ("Findling") eingefroren vor dem ersten produktiven Commit. Basisimage-Entscheidung (glibc, python:3.13-slim-trixie) getroffen. Architekturinvariante "nur lesend auf Nutzerdateien" als Testgate verankert.
Addresses: Zero-Config-Grundgeruest, PHP-Companion-App registriert den Unified-Search-Provider (aus PROJECT.md Requirements)
Avoids: Pitfall 9 (Deployment/Deploy-Daemon: von Anfang an gegen HaRP, nicht DSP), Pitfall 11 (Multi-Arch-Falle), Pitfall 13 (Store-/Zertifikatspipeline: ID vor Bau-Commit), Pitfall 12 (Kompatibilitaetsspirale: PHP-Flaeche bewusst winzig halten)

### Phase 2: Indexkern
Rationale: Der komplette Transportweg (Queue, Crawl, Content-Gateway) muss ohne jede Suchintelligenz beweisen, dass Dateien vollstaendig und wiederaufsetzbar ankommen, bevor Volltextsuche darauf aufbaut. Die ACL-Tabelle gehoert in diese Phase, nicht spaeter: Berechtigungen nachtraeglich in ein Schema zu ziehen ist ein Neuschreiben, kein Feature.
Delivers: Queue-Tabellen, OCS-Queue-API, Content-Gateway (GET /files/{fileId}?userId=), Crawl-Job pro Mount mit fileid-Cursor, Fetcher-Thread mit Backpressure, Storage-Schema inklusive acl-Tabelle, Tantivy-Index mit deutschem/englischem Analyzer, funktionierender /search-Endpoint mit ACL-Vorfilter + finalem PHP-Recheck, Statuszaehler als Nebenprodukt.
Uses: Tantivy 0.26.0, SQLite (WAL, ein Schreiber-Thread), pypdfium2/pypdf/python-docx/python-pptx/openpyxl/lxml fuer Textextraktion
Implements: Pull-Queue, Mount-Crawl mit Integer-Cursor, ACL-Join-Tabelle, Content-Gateway
Addresses: Volltextsuche ueber Dateiinhalte, Dateiname/Pfad-Gewichtung, Berechtigungsfilter, Ausschlussregeln (.noindex, Groessenlimit, Mimetype-Allowlist), minimale Query-Syntax
Avoids: Pitfall 1 (haengender Indexlauf), Pitfall 6 (Berechtigungsleck, Grundgeruest), Pitfall 7 (Zero-Config-Defaults ohne Grenzen), Pitfall 8 (Index als nicht rekonstruierbarer Zustand)

### Phase 3: Event-Integration & Abgleich
Rationale: Erst wenn der Index inhaltlich stimmt, lohnt es sich, ihn aktuell zu halten. Der Abgleichlauf gehoert zwingend in dieselbe Phase wie die Event-Listener, sonst wird er in der Praxis nie gebaut.
Delivers: Node- und Share-Event-Listener (in PHP, da AppAPI-Events und webhook_listeners keine Share-Events kennen), deklarative Access-Aktionen (Soll- statt Delta-Zustand), Loeschpfad (BeforeNodeDeletedEvent), periodischer Reconcile-Job mit demselben Mount-Cursor-Muster wie der Crawl.
Addresses: Inkrementelle Indexierung ueber Datei-Events, robust gegen Abbrueche
Avoids: Pitfall 5 (Event-Luecken erzeugen unbemerkten Drift), Verifikation: Events komplett blockieren, nach einem Abgleichzyklus muss der Index korrekt sein

### Phase 4: OCR
Rationale: Rein additiv zum bestehenden Kern, faellt OCR aus, funktioniert die Suche unveraendert weiter. Deshalb erst hier, nicht davor, obwohl OCR fachlich der teuerste Baustein ist.
Delivers: Eigene OCR-Worker-Spur (getrennt von Textextraktion, Head-of-Line-Blocking vermeiden), Text-Layer-Erkennung pro Seite (kein OCR auf digitalen PDFs), RAM-/Zeit-Deckel pro Job, Scratch-Verzeichnis im Volume mit Groessengrenze und Aufraeumung.
Uses: Tesseract 5.5.0 (deu+eng+osd) als Subprozess, pypdfium2-Rasterung
Addresses: OCR fuer gescannte PDFs/Bilder, automatisch, Originaldatei bleibt unveraendert
Avoids: Pitfall 3 (OCR zerstoert Nutzerdaten, Grep-Gate + Pruefsummenlauf als Abnahme), Pitfall 4 (OCR frisst CPU/RAM bis zum Server-Stillstand)

### Phase 5: Semantik (v1.1, 4-6 Wochen nach v1.0)
Rationale: Der teuerste und am staerksten hardwareabhaengige Teil baut auf einem Schema auf, das sich in den Phasen 2-4 bereits bewaehrt hat. Owner-Entscheid: als separates Release nach v1.0, damit fruehes Feedback moeglich ist, ohne auf die komplexeste Komponente zu warten.
Delivers: Chunking (semantic-text-splitter), Embeddings (fastembed + multilingual-e5-small int8), sqlite-vec-Vektortabelle mit Ueberfetch-plus-ACL-Nachfilter, RRF-Hybrid-Ranking, saubere Degradation auf reine Tantivy-Suche bei fehlendem Modell.
Uses: fastembed 0.8.0, onnxruntime 1.28.0, sqlite-vec 0.1.9, semantic-text-splitter 0.32.0
Addresses: Semantische Suche lokal, CPU-only, Hybrid-Ranking Volltext+Vektor
Avoids: Pitfall 10 (Vektorindex waechst schneller als die Box), Skalierungstest auf mindestens 50.000 synthetischen Dokumenten vor Freigabe, Kennzahl "Bytes pro Dokument" mitfuehren

### Phase 6: Admin-Sichtbarkeit & Diagnose
Rationale: Fortschritts- und Fehlerdaten fallen aus Phase 2/3 bereits als Nebenprodukt an; diese Phase macht sie fuer den Admin sichtbar. Kann parallel zu Phase 4/5 laufen, wird hier aber als eigene Phase gefuehrt, weil sie ein eigenes Abnahmekriterium hat.
Delivers: Statusseite (laeuft/pausiert/Fortschritt/Fehleranzahl/Indexgroesse), Pro-Datei-Diagnose mit Grund, Vorab-Schaetzung vor dem Erstindex, occ-Kommandos (Start/Stopp/Resume/Reset/Reindex-Pfad).
Addresses: Admin-Sichtbarkeit, Diagnose pro Datei, Vorab-Schaetzung
Avoids: Pitfall 2 (stiller Ausfall, den erst der Nutzer merkt), Deckungsgrad statt Konnektivitaet anzeigen, Kanarienvogel-Selbsttest

### Phase 7: Haertung
Rationale: Vor der Store-Einreichung muessen alle Betriebsrobustheits-Versprechen auf echter Zielhardware bewiesen sein, nicht nur dokumentiert, genau das hat das Vorgaenger-Oekosystem versaeumt.
Delivers: Multi-Arch-Test auf echter ARM-Hardware (RSS-Kurve, kein OOM), Paritaetstest gegen die native Nextcloud-Suche fuer sechs Rechteszenarien als Dauergate, Disk-Full- und Restore-Simulation, Benchmark-Zahlen fuer die Store-Positionierung ("laeuft in X GB auf einem Raspberry Pi").
Avoids: Pitfall 4 (OCR-Lasttest auf 4-GB-ARM), Pitfall 6 (Paritaetstest als Dauergate), Pitfall 8 (Restore-/Disk-Full-Test), Pitfall 14 (Wettbewerbsrisiko, belegbare Zahlen statt Behauptungen)

### Phase 8: Store-Einreichung
Rationale: Verpackung zum Schluss, aber App-ID und Naming standen bereits seit Phase 1 fest; die CSR-Vorlaufzeit fuer zwei getrennte App-Store-Eintraege (PHP-App + ExApp) muss frueh eingeplant werden.
Delivers: Zwei CSR-Vorgaenge, zwei signierte Releases mit gekoppelter Versionierung, schemavalidierte info.xml, Store-Text mit expliziter Privacy-/Integritaetsaussage ("nichts verlaesst den Server, keine Datei wird veraendert, keine Telemetrie"), oeffentlich kommunizierter Wartungsrhythmus fuer NC-Kompatibilitaet.
Avoids: Pitfall 13 (Store-/Zertifikatspipeline), Pitfall 12 (Kompatibilitaets-Todesspirale, Wartungsrhythmus im README)

### Phase Ordering Rationale

- Die IProvider-ExApp-Kombination wird zuerst bewiesen, weil sie das einzige Integrationsmuster ohne Vorbild im Oekosystem ist; ein spaetes Scheitern hier waere am teuersten.
- Die ACL-Tabelle steht in Phase 2, nicht spaeter, weil Berechtigungen eine Sicherheitseigenschaft sind, die man nicht sauber nachruestet.
- Event-Integration folgt erst nach einem funktionierenden Suchkern, weil ein Abgleichlauf ohne funktionierenden Index nichts zu tun hat.
- OCR steht vor Semantik, obwohl aufwendiger, weil OCR nur den Textkorpus erweitert und am Schema nichts aendert, waehrend Semantik eine neue Tabelle, einen neuen Retrieval-Zweig und die groesste Hardwareabhaengigkeit mitbringt, das gehoert auf einen bereits durch Nutzung erprobten Unterbau.
- Diese Reihenfolge deckt sich mit dem Owner-Entscheid zur gestaffelten Auslieferung: v1.0 (Phasen 1-4, 6-8) liefert Volltext+OCR, v1.1 (Phase 5) liefert Semantik 4-6 Wochen spaeter, ohne Architektur-Umbau, weil das Schema von Anfang an embedding-faehig geschnitten ist.

### Research Flags

Phasen, die waehrend der Planung tiefere Recherche brauchen (--research-phase):
- Phase 1: Die IProvider-ExApp-Proxy-Kombination hat kein Vorbild; offene Fragen zum Snippet-Markup in SearchResultEntry (entfernt die Unified-Search-UI HTML?) und zur realen Timeout-Obergrenze im AppAPI-Proxy muessen vor dem Bau geklaert werden.
- Phase 2: Zusammenfuehrung von Tantivy (Index) und SQLite (ACL/Vektoren/Status) im ACL-Vorfilter ist die vom Owner aufgeloeste Architekturentscheidung, aber die konkrete Umsetzung (Kandidatenmenge aus Tantivy, Abgleich gegen SQLite-ACL, finaler PHP-Recheck) ist ohne Praezedenzfall und braucht ein durchdachtes Interface-Design.
- Phase 5: sqlite-vec ist pre-v1 (Alpha), die 250.000-Chunk-Schwelle fuer Brute-Force ist gerechnet, nicht gemessen; Kombination aus Partition-Key und Bit-Vektoren ist dokumentiert, aber ohne Praezedenzfall. Skalierungsbenchmark vor Schema-Fixierung noetig.
- Phase 7: Reale RAM-Spitzen auf ARM sind Schaetzungen (STACK.md, MEDIUM confidence), ein Messlauf auf echter Hardware gehoert hierhin, bevor Defaults final festgezurrt werden.

Phasen mit etablierten Mustern (research-phase kann entfallen):
- Phase 3: Event-Listener-Registrierung und Reconcile-Muster sind aus Context Chat vollstaendig im Quellcode verifiziert (HIGH confidence).
- Phase 4: OCR-Subprozessaufruf, Text-Layer-Erkennung und Ressourcendeckel sind Standardmuster mit klarer Werkzeugkette (Tesseract, pypdfium2), gut dokumentiert.
- Phase 6: Statusseiten- und Diagnose-Muster sind konzeptionell einfach, das Datenmodell faellt aus Phase 2/3 bereits ab.
- Phase 8: Store-/Zertifikatsprozess ist im Schwesterprojekt (nextcloud-mcp-connector) bereits vollstaendig recherchiert und dokumentiert.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versionen, Lizenzen, Wheel-Verfuegbarkeit und API-Signaturen direkt aus PyPI, GitHub-Quellcode und Debian-Paketdaten verifiziert (Stand 15.08.2026). RAM-Schaetzungen und Retrieval-Qualitaet von e5-small int8 auf Deutsch bleiben MEDIUM. |
| Features | MEDIUM-HIGH | Bestandsapp-Feature-Sets aus Quellcode/Doku verifiziert (HIGH); Nutzerwuensche und Schmerzpunkte aus Foren/Issues sind MEDIUM, aber durch viele unabhaengige Quellen gestuetzt. |
| Architecture | HIGH fuer Protokoll/Muster (direkt aus context_chat-, app_api- und nc_py_api-Quellcode verifiziert), MEDIUM fuer das konkrete Storage-Layout, weil sqlite-vec noch Alpha ist und die ACL-Vorfilter-Kombination mit Tantivy kein Praezedenzfall im Oekosystem ist. |
| Pitfalls | HIGH fuer die dokumentierten Fehlermodi des Vorgaenger-Oekosystems (Issue-Tracker, offizielle Doku, live gegen PyPI geprueft), MEDIUM fuer AIO-Backup-Abdeckung und die Wettbewerbseinschaetzung. |

Overall confidence: HIGH

### Gaps to Address

- Reale RAM-Spitzen auf ARM-Hardware sind reine Schaetzungen, Messlauf auf einem Raspberry Pi 5 (4 GB) gehoert in Phase 1/7, bevor Worker-Defaults endgueltig festgezurrt werden.
- Retrieval-Qualitaet von multilingual-e5-small nach int8-Quantisierung auf deutschen Texten ist nicht fuer dieses konkrete Modell belegt, kleines deutsches Testset in Phase 5 bauen, fp32 gegen int8 vergleichen.
- Die 250.000-Chunk-Schwelle, ab der sqlite-vec-Brute-Force kippt, ist gerechnet, nicht gemessen, Benchmark mit synthetischen 100k-Dokumenten in Phase 5, bevor das Vektorschema fest ist.
- Zuverlaessigkeit des AppAPI Events Listener unter Last ist unbekannt (Doku nennt die Zustellung ausdruecklich asynchron und benachrichtigungsartig), der periodische Abgleichlauf in Phase 3 ist deshalb Pflicht, nicht Kuer, und muss unter simulierter Event-Blockade getestet werden.
- Deutsche Wortliste fuer Tantivys split_compound-Filter ist unbeschafft und unlizenziert, bewusst nicht in v1, Komposita-Behandlung laeuft ueber Prefix-Query, Nachbesserung als dokumentierter v1.1-Kandidat.
- Snippet-Offsets mit ascii_fold() bei Umlauten sind ungetestet, vor der endgueltigen Analyzer-Festlegung in Phase 2 mit echten deutschen Dokumenten pruefen.
- Store-Einreichungsprozess fuer zwei parallele Apps (PHP-Companion + ExApp) mit gekoppelter Versionierung ist ein bekanntes Terminrisiko aus dem Schwesterprojekt, Vorlaufzeiten fuer beide CSRs frueh klaeren.
- Ob AIO-Borg-Sicherungen das ExApp-Volume automatisch erfassen, ist unklar (Doku deutet auf Opt-in hin), in Phase 7 am echten AIO nachstellen, Index bleibt als Cache konzipiert, damit das Ergebnis fuer die Roadmap nicht kritisch ist.

## Sources

### Primary (HIGH confidence)
- quickwit-oss/tantivy-py, Tag 0.26.0: Tokenizer/Filter/SnippetGenerator/IndexWriter direkt aus dem Quellcode
- cloud-py-api/nc_py_api, CHANGELOG/README: Async-Migration, CVE-2026-48710, PROPFIND-Fix
- nextcloud/server, Branch stable34, lib/public/Search/* und IRegistrationContext: IProvider/IFilteringProvider/IExternalProvider-Semantik
- nextcloud/app_api, lib/PublicFunctions.php und README: exAppRequest, HaRP-Empfehlung
- nextcloud/context_chat und nextcloud/context_chat_backend, vollstaendiger Quellcode: Zwei-App-Muster, Pull-Queue, Crawl-per-Mount, ACL-Anti-Pattern
- nextcloud/fulltextsearch(_elasticsearch), Issue-Tracker (u.a. #311, #404, #597, #715, #769, #857, #950, #955, #956): dokumentierte Fehlermodi des Vorgaengers
- nextcloud/files_fulltextsearch_tesseract Issue #30 plus Forum-Warnthread: OCR-Datenverlust
- PyPI JSON-API fuer alle genannten Pakete, Stand 15.08.2026: Versionen, Wheel-Plattformen, requires_python
- docs.nextcloud.com: Events-Listener-Semantik, ExApp-Deploy-Konfigurationen, Context-Chat-Admin-Doku (12 GB RAM, kein OCR, files_accesscontrol nicht befolgt)

### Secondary (MEDIUM confidence)
- Nextcloud-Forum-Threads (u.a. "OCR in Nextcloud, giving up after a month", "knowing index status", Snippetlaenge-Diskussionen): Nutzerwuensche und Schmerzpunkte
- alexgarcia.xyz/sqlite-vec: Binaerquantisierung, Partition-Keys, Hybrid-Search-Guides
- github.com/asg017/sqlite-vec Issue #25: ANN-Index als offenes Ziel, aktuell Brute-Force

### Tertiary (LOW confidence)
- Alle RAM-Budgetzahlen (Planungsgroessen, kein Messwert)
- Die 250.000-Chunk-Brute-Force-Schwelle (Hochrechnung)
- Qualitaetsverlust durch int8-Quantisierung bei e5-small auf Deutsch (nicht modell-spezifisch belegt)

---
*Research completed: 2026-08-15*
*Ready for roadmap: yes*
