# Findling (Nextcloud Zero-Config-Suche)

## What This Is

Findling ist eine Nextcloud-ExApp, die die kaputte Suche repariert: ein Container mit OCR, klassischer Volltextsuche und semantischer Suche, per Klick aus dem Nextcloud App Store installierbar, ohne Elasticsearch-Gebastel. Ergebnisse erscheinen in der normalen Unified Search (via schlanker PHP-Companion-App) und seit v1.1 zusaetzlich auf einer eigenen Ergebnisseite mit Paginierung, seit v1.2 dort mit Dateityp-Filter, Zeitraumfilter und Datums-Sortierung. Optional gibt der Container sein Modell im Leerlauf frei (Schalter ab Werk aus). Seit v1.3 beherrscht die lexikalische Suche neben Deutsch und Englisch auch Spanisch, Italienisch, Niederlaendisch und Portugiesisch (Sprachwechsel per Re-Analyse-Umbau statt Vollreindex), die Oberflaeche spricht acht Sprachen (EN/DE/FR/ES/IT/NL/pt_PT/pt_BR). Seit v1.5 (Umsteiger-Release) kommen Tschechisch, sechs neue Dateitypen (DOC, XLS, Mails, ZIP-Inhalte, HEIC/HEIF), Typ- und Ordnerfilter direkt in der Unified Search, Ausschlussmuster, eine Aehnliche-Dokumente-Ansicht und ein dokumentierter Umstiegsweg vom fulltextsearch-Framework dazu. Zielgruppe: Selfhoster und kleine Organisationen auf typischer Hardware (4-8 GB RAM, oft ARM), für die das offizielle fulltextsearch-Framework (jahrelang verwaist, weiterhin Elasticsearch-gekoppelt) keine Option ist.

## Core Value

Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.

## Current State (nach v1.5, 2026-10-28)

**Shipped:** Findling 1.5.0 im Nextcloud App Store (beide Apps signiert, Submission 21.10.2026, Lauf 39598694849, 2x HTTP 201, Tag v1.5.0 auf 6c953a76; 1.5.1 als Nachzuegler im Store). Milestone v1.5 am 28.10.2026 geschlossen und archiviert (.planning/milestones/v1.5-*): Phasen 30 bis 36, 79 Plaene, Phase 36 mit Code-Review (0 Critical, 2 Warnings gefixt) und Verifier passed 5/5 abgeschlossen. Offen fuer v1.6: L-36-05/L-36-06 (Ausschluss-Anzeigetexte), #25-Dedup-Rest, Umlaut-Fixes in drei docs-Dateien, Zert-Rotation Issue #33, discussion-Link auf Forum-Thread 249775, UPGRADE_FROM_TAG auf v1.5.0. Naechster Schritt: /gsd:new-milestone v1.6.

## Frueherer Stand (nach Phase 35, 2026-10-20)

**Phase 35 komplett (Stretch, Verifier passed, 14/13 Plaene inkl. Nachmessung 35-04B):** Aehnlich-Ansicht geliefert (STR-01: Link je Treffer, Serveransicht ?similar=fileId, POST /similar als undeklarierte Inhaltsroute, PHP-Recheck vor und nach dem Containeraufruf, SIMILAR_CEILING 54,5 aus Fassungspaar-Messung, Owner-Playwright-Abnahme 20.10.); granite-Messbericht mit Verdikt (STR-02: Bedingung (a) verfehlt bei p=0,0944, Ursache int8-Quantisierung, Empfehlung "Wechsel nur mit Bedingung", e5-small bleibt in v1.5; arm64 auf m7g.large fuer 0,0362 USD, Box abgebaut); Dedup-Entscheidungsvorlage (STR-03, Empfehlung Weg B, Owner-Fragen D1-D4 offen fuer v1.6). Audit 35-12: 0 CRIT/HIGH/MEDIUM, 6 LOW alle behandelt (u. a. unknown-Marke liefert bei leerem Vektorbestand jetzt nach). Validated in Phase 35: STR-01, STR-02, STR-03. Naechster Schritt: Phase 36 (Haertung + Store-Einreichung 1.5.0, REL-05, HART-06, M-32-02).

## Frueherer Stand (nach Phase 29, 2026-10-06)

**Shipped:** Findling 1.4.0 im Nextcloud App Store (beide Apps signiert, Submission 06.10.2026, Lauf 37473805519, je HTTP 201, Tag v1.4.0 auf 99326ae2). Phase 29 komplett: Launch-Haertung (Audit 0 CRIT / 0 HIGH), alle sechs oeffentlichen #18-Zusagen geliefert (Sidecar-Skip, TIFF-Shim, JPEG-draft + Header-Schaetzung, OLE-Sniff, Fehlerklasse je Datei, Altbestands-Nachpruefung in Baendern hinter dem Companion-Signal), Upgrade-Strecke 1.3.2 auf 1.4.0 in CI Ende zu Ende bewiesen, Vollindex-Term in der Laufzeit-Slotrechnung (D-29-12), K6-Faehigkeitssignal mit Rueckfall je Liste. Offen laut D-29-11: vier box-gebundene Feldbelege (naechste Anfahrt). Milestone v1.4 am 06.10.2026 geschlossen und archiviert (.planning/milestones/v1.4-*).

## Frueherer Stand (nach v1.3, 2026-09-27)

**Shipped (damals):** Findling 1.3.0 im Nextcloud App Store (beide Apps signiert, Submission 27.09.2026, Lauf 36304007154, je HTTP 201, Tag v1.3.0 auf 744d7e4).

- Lexikalische Suche in sechs Sprachen (de, en + es, it, nl, pt): vier neue Analyseketten messend abgenommen, Schema traegt immer sechs Koerperfelder, befuellt wird nur nach FINDLING_LANGUAGES (Werk bleibt de,en; Bestandsinstallationen upgraden ohne Umbau)
- Re-Analyse-Umbau (index/rebuild.py): Sprachwechsel ohne Download, OCR oder Neu-Einbettung; wiederaufnahmefaehig, Platzpruefung vorab, atomarer Tausch, Fortschritt auf der Adminseite; CI beweist beide Richtungen (UPGRADE_FROM_TAG=v1.2.0)
- Niederlaendische Komposita via wdutch/OpenTaal (siebte Marke wordlist_hash_nl, Umbau nur bei aktivem nl); UI-Kataloge es/it/nl/pt_PT/pt_BR mit je 202 Schluesseln, Pluralschluessel-Fix macht DE/FR-Plurale erstmals korrekt
- Kaltstart-Fix: erste Suche antwortet lexikalisch sofort (973 ms MIT Treffern statt 0), Gewichte laden im Hintergrund nur nach Anforderung, kein Vorwaermen beim Start
- Messanfahrt BL-F03 abgeschlossen: alle fuenf offenen v1.2-Zahlen plus Indexgroesse/Umbau-Wandzeit plus BL-F04-Basiszahlen aus einer Anfahrt (Plan 15,95 h / 2,83 USD), dismax auf Messbasis verworfen; Ergebnisse in docs/performance.md
- HART-04: fastembed raus, tokenizers/numpy direkt deklariert, Absenz-Check im Abbild; gone-Reparatur-Migration Version001300Date20260927000000 mit Upgrade-CI-Beweis
- Audit Phase 23: 0 CRIT / 0 HIGH (F-23-01 Reload-Bug seit Phase 14 gefixt); secure-phase 23 SECURED 46/46 (23-SECURITY.md); CI 6/6 gruen inkl. HaRP auf 79ad925
- Korpus-Snapshot snap-03f1d1d9ad9262704 weiter behalten (Standard-Tier, ~2,85 USD/Monat, einzige laufende Box-Kostenstelle); Wiedervorlage beim v1.4-Close

## Requirements

### Validated

- ✓ Volltextsuche über Dateiinhalte, Ergebnisse in der Unified Search, v1.0
- ✓ OCR für gescannte PDFs und Bilder, automatisch beim Indexieren, strikt index-only, v1.0
- ✓ Semantische Suche (lokale Embeddings, CPU-only) mit Hybrid-Ranking, v1.0
- ✓ Zero-Config: Installation aus dem Store, Indexierung startet selbst, v1.0
- ✓ Inkrementelle Indexierung, robust gegen Abbrüche (Resume, Backpressure), v1.0
- ✓ Berechtigungs-Durchgriff (SQLite-ACL-Vorfilter + finaler PHP-Recheck), v1.0
- ✓ PHP-Companion-App als Unified-Search-Provider mit exAppRequest-Proxy, v1.0
- ✓ Admin-Sichtbarkeit: Indexstatus, Fortschritt, Fehler, v1.0
- ✓ Multi-Arch-Image (amd64 + arm64) auf 4-8-GB-Boxen, v1.0 (v1.1: nativ-arm64-CI)
- ✓ App-Store-Einreichung als signiertes App-Paar, v1.0 (1.0.0), v1.1 (1.1.0)
- ✓ Gemeinsame Embedding-Engine, Modell einmal pro Prozess (EFF-01/02), v1.1
- ✓ Komposita-Zerlegung über lizenzkonforme Wortliste (QUAL-01..03), v1.1
- ✓ Eigene Ergebnisseite mit Paginierung und Rückkehr ohne Listenverlust (UI-01..03), v1.1
- ✓ Vergleichsmessung gegen v1.0-Baseline auf Zielhardware (MESS-01..03), v1.1
- ✓ Dateityp-Filter, Zeitraumfilter und Datums-Sortierung auf der Ergebnisseite, Rechtegrenze unveraendert (FILT-01..05), v1.2
- ✓ Modell-Entladung im Leerlauf, beide Speicherhalter, ab Werk aus, one_load-Zusage neu gefasst (MEM-01..05), v1.2
- ✓ Messwerkzeug + Runbook vor der Anfahrt, eine bezahlte Box-Anfahrt mit allen Messbelegen, Cron-Intervall als erzwungene Messbedingung (MESS-04..06), v1.2
- ✓ Haertungen DI-11-02/03/05/06, BL-F01-Schlusssatz dreisprachig, stable35-Entscheid, Store-Einreichung 1.2.0 mit Upgrade-Beweis (HART-01..03, REL-02), v1.2
- ✓ Lexikalische Suche es/it/nl/pt: Analyseketten, sechs Koerperfelder, Re-Analyse-Umbau, Frageseite (LEX-01..08), v1.3
- ✓ Niederlaendische Komposita ueber ihre Glieder mit eigener Digest-Marke (KOMP-01), v1.3
- ✓ UI-Kataloge es/it/nl/pt_PT/pt_BR im Gleichstand, 202 Schluessel, Pluralfix (KAT-01..02), v1.3
- ✓ Messanfahrt BL-F03: fuenf offene plus zwei neue Zahlen plus BL-F04-Basiszahlen aus einer Anfahrt, dismax-Entscheid auf Messbasis (MESS-07..09), v1.3
- ✓ Aufraeumbefunde fastembed/numpy geschlossen, Grenzen des Sprachausbaus dokumentiert, Store-Einreichung 1.3.0 (HART-04..05, REL-03), v1.3
- ✓ Umstiegsweg von fulltextsearch/Elasticsearch: dreisprachige Doku-Seite + Admin-Banner bei Parallelbetrieb (UMST-01..03), v1.5
- ✓ Typ- und Ordnerfilter in der Unified Search ohne zweites Rechtemodell (USRCH-01..03), v1.5
- ✓ Ausschlussmuster als Einstellung inkl. Mac-Bundles, bitparalleler Matcher, Weg A + Weg C (EXCL, #22), v1.5
- ✓ Neue Formate .eml, ZIP-Inhalte, .doc/.xls ohne LibreOffice, HEIC/HEIF samt Nachholweg (FMT-01..06), v1.5
- ✓ Tschechisch: OCR-Option ces + lexikalisches Feld ohne Stemmer, Schema 3 (CZ, #26), v1.5
- ✓ Grenzwerte auf der Admin-Seite sichtbar, F-29-03, Wortlaut-Feinschliff (POL, #21), v1.5
- ✓ Aehnliche Dokumente ueber vorhandene Vektoren, granite-Messbericht, Dedup-Designnotiz (STR-01..03), v1.5
- ✓ Launch-Haertung mit boesartigem Formatkorpus, M-32-02-Karenz, Store-Einreichung 1.5.0 (HART-06, REL-05), v1.5

### Active

(v1.6 Store-Sichtbarkeit und Betriebs-Feinschliff, gestartet 28.10.2026; REQ-IDs in REQUIREMENTS.md.)

- L-36-05/L-36-06: Anzeigetext "Bewusst ausgelassen: 0" mit Erklaersatz, Zaehler-Verzoegerung nach Ausschlussmuster-Aenderung
- #25-Dedup-Bau (Weg B der Designnotiz, Owner-Fragen D1-D4)
- Umlaut-Fixes in docs/dev-setup.md, docs/embeddings.md, docs/install-check.md (Testkorpus-Begriffe nicht anfassen)
- Zert-Rotation Issue #33 (frpc liest /certs/frp bei x509-Fehler neu ein + Neustart)
- Store-Sichtbarkeit: discussion-Link auf Forum-Thread 249775, Cross-Promo-Satz, Anzeigename "Findling Search" (GO vom 22.10.)
- UPGRADE_FROM_TAG auf v1.5.0 heben
- Review-Infos IN-01 bis IN-06 der Phase 36 pruefen

Vorlaeufig spaeter: granite-Wechsel (nur mit Bedingung, Verdikt 35-11), kleiner Reranker, CLIP-Bildsuche (SigLIP2, Lizenz je Modell), whisper.cpp-Transkription als Opt-in.

Nicht in v1.4 (Wiedervorlage): Franzoesisches Koerperfeld (benannte Luecke); F-23-04; idle-Guard EmbeddingModel.release() (Kandidat, beim Roadmapping pruefen).

Weiter in der Wiedervorlage: Sortierung nach Name/Groesse (Schema-Sprung), Mimetype-Gruppen aus files.mime, geplantes Vorwaermen, Pro-Schiene (Index-Verschluesselung, External Storage, ISV-Entscheid 03.11.).

### Out of Scope

- Elasticsearch/OpenSearch-Backends, genau die Setup-Qual, die das Produkt beseitigt
- RAG/Chat-Antworten über Dokumente, Context-Chat/Assistant-Terrain; wir liefern Suche, keine Antworten
- Externe Cloud-Embeddings/APIs, Privacy-Versprechen: alles lokal im Container
- Indexierung fremder Quellen (Mail-Server, S3 extern, Websites), Nextcloud-Files zuerst
- Kein eigenes MCP-Tool gegen den Index, Unified Search bleibt die einzige Berechtigungsgrenze
- Typesense als Engine, GPLv3 und Index komplett im RAM, passt nicht zu kleinen Boxen

## Context

- Stand 28.10.2026: sechs Milestones geliefert (v1.0 am 07.09., v1.1 am 11.09., v1.2 am 21.09., v1.3 am 27.09., v1.4 am 06.10., v1.5 am 21.10. eingereicht / 28.10. geschlossen), Backend Python 3.13/Tantivy (onnxruntime/tokenizers direkt), Companion PHP, ~6.400 Python-Tests + PHP-Suite (846 Tests), 8 CI-Workflows inkl. Fremdinstallations- und Upgrade-Strecke (deploy-harp), Messberichte unter docs/measurements/.
- ZenDiS hat den Schwester-Connector installiert und praesentiert ihn auf der Smart Country Convention; ISV-Call mit Nextcloud (Fabrice Mous) am 14.09.2026, Findling + Backend + Connector tragen das Enterprise-Flag im Store.
- Kill-Kriterium weiter aktiv: Nextcloud GmbH hat fulltextsearch am 12.08.2026 reaktiviert; kündigt sie eine Elasticsearch-freie Volltextsuche mit OCR an (Nextcloud Conference September), wird neu bewertet. Die Differenzierer bleiben: kein Elasticsearch, OCR eingebaut, Semantik, kleines RAM-Budget, deutsche Komposita, Ergebnisseite.
- Historischer Rechercheteil (Marktlücke 15.08.2026, Stack-Entscheide, Pitfalls des alten fulltextsearch) steht im v1.0-Archiv und in docs/; die nicht verhandelbaren Betriebsregeln gelten weiter: Fortschritt in der DB, failed/skipped sichtbar, Nur-Lesen-Invariante auf Nutzerdateien, Rechteprüfung vor Snippet-Erzeugung, INDEX_WORKERS=1.

## Constraints

- **Kapazität**: Solo-Entwickler
- **Hardware-Ziel**: 4-8 GB RAM, ARM-tauglich, alles CPU-only, RAM-Budget hart einplanen (RAM-Tabelle in CLAUDE.md)
- **Tech stack**: Python 3.13 + uv, ExApp via AppAPI/nc_py_api, PHP-Companion-App; Docker/WSL2 für Test-Nextcloud
- **Lizenz**: AGPL-3.0
- **Repo**: public auf GitHub street1983nk (privates Konto, NICHT Akara-GitLab); Git-Identität nie übersteuern (pre-commit-Hook sperrt)
- **Sprache**: Code/README Englisch, Projektkommunikation Deutsch; keine Em-Dashes; echte Umlaute nur in deutscher Prosa, nie in Code; Kataloge EN/DE/FR im Gleichstand (vier Gates)
- **Qualitätsgates**: ruff-Vollregelsatz, pyright basic, vulture, CI-Gates, lokal grün vor Commit; Audit-Gate nach jeder Phase (MEDIUM+ fixen, LOW dokumentiert entscheiden)
- **Security/Privacy**: Berechtigungs-Durchgriff strikt; keine Inhalte verlassen den Server; keine Telemetrie
- **Store-Regeln**: Kurztext-Regel (Faktenlisten, Owner-Abnahme vor Einreichung); eine Messzahl (730,2 MB); alle Fundstellen hält das Gate test_store_metadata.py (RESIDENT_FIGURE); Tag im Store nie verschieben

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Name: **Findling**; App-IDs `findling` + `findling_backend` | Store frei, context_chat-Muster, nach CSR irreversibel | ✓ Good, zwei Releases im Store, keine Kollision |
| Eine gemeinsame Einreichung 1.0.0 (D-08, ersetzt Staffelung) | Früher sichtbar, Architektur embedding-ready | ✓ Good, 1.0.0 am 07.09. mit allem |
| Engine: Tantivy + SQLite-ACL-Vorfilter + finaler PHP-Recheck | Sprachqualität ist das Produktversprechen; Sicherheitsgrenze ist der PHP-Recheck | ✓ Good, trug durch beide Milestones, keine zweite Grenze aufgemacht |
| Embedded Engine statt Suchserver-Sidecar | Zero-Config + RAM-Budget | ✓ Good, 103,2 MB Grundlast nach v1.1 |
| PHP-Companion für Unified Search (AppAPI kann keine Provider) | context_chat-Muster etabliert | ✓ Good, präzedenzlose Kombination bewiesen |
| OCR strikt index-only, Nutzerdateien nie anfassen | Alt-Tesseract-App hat PDFs gelöscht | ✓ Good |
| Launch-Härtungsphase vor jeder Store-Abgabe | Owner: "perfektes Findling, nicht nur Happy Path" | ✓ Good, fand in 06.1 und 11 echte Produktfehler (u.a. stumme Suche nach Minor-Upgrade) |
| Sprachen v1: DE+EN voll; FR-Katalog ab v1.1 | DACH-Zielgruppe; Owner-Muttersprache FR, Zielmarkt DACH+Frankreich | ✓ Good, 174 Schlüssel, Abnahme ohne Korrektur |
| Gemeinsame Embedding-Engine statt Modell-Entladung (v1.1) | Entladung wäre Bedarfsfall gewesen | ✓ Good, minus 588,6 MB Grundlast, Entladung nicht mehr nötig |
| v1.1 index-kompatibel, kein Reindex (D-04) | Bestandsinstallationen nicht strafen | ✓ Good, Upgrade-Beweis in CI, Indexmarken unverändert |
| Messbox einmal anfahren, danach Snapshot + Abbau (D-01/D-03) | Kosten, Vergleichbarkeit zur Baseline | ✓ Good, 2 Läufe unter Deckel, laufende Kosten auf ~2,9 USD/Monat |
| Kill-Kriterium: NC kündigt ES-freie Volltextsuche mit OCR an -> Neubewertung | fulltextsearch am 12.08. reaktiviert | ✓ Geprüft 21.09.: NICHT ausgelöst (nur ES-Stack-Modernisierung); weiter quartalsweise beobachten |
| Keine Index-Verschlüsselung at rest, transparent dokumentiert | Schutzniveau identisch zum Host |, Pending (Future Requirement) |
| Team Folders default AN, External Storage default AUS | Mount-Crawl billig, External Storage unkalkulierbar | ✓ Good, keine Beschwerden, External Storage bleibt Future |
| Ziel Reputation/Portfolio; Pro-Schiene offen ab v2 | Store hat kein Bezahlmodell |, Pending (Enterprise-Flag + Fake-Door seit 11.09. live, ISV-Spur läuft separat) |
| Eine bezahlte Box-Anfahrt für alle v1.2-Messbelege, Deckel vor dem Start vom Owner freigegeben | Kosten, Runbook-Erstvollzug als Nebenertrag | ✓ Good, 25,75 h / 2,98 USD unter Deckel 46 h / 5,40 USD, alle vier Messaufträge mit Zahl |
| Modell-Entladung hinter TTL-Schalter, ab Werk AUS | Zero-Config-Versprechen, A/B-Beleg brauchte beide Zustände | ✓ Good, 377,5 MB Rückkehr belegt, erste Suche danach lexikalisch statt langsam |
| Sortierung als rein lexikalischer Modus (Score 0.0, RRF aus) | tantivy liefert unter order_by_field den Feldwert statt des Scores | ✓ Good, kein Pseudo-Ranking ausgeliefert |
| 6 OCR-Sprachen (Owner-Entscheid "Mitfahren") | Sprachpakete sind arch-neutral und billig, Positivliste deckelt | ✓ Good, sechs eigene Bau-Prüfungen, Standard bleibt deu+eng+fra |
| stable35-Entscheid als eigener fristgebundener Plan in der ERSTEN Phase | Frist 16.09. lag zwei Tage nach Milestone-Start | ✓ Good, am Stichtag vollzogen, Beweislauf 4/4 grün |
| Re-Analyse-Umbau statt Vollreindex beim Sprachwechsel (Owner-Tor 17, alle acht Entscheide Option a) | Vollreindex kostet 19 h 20 min auf Zielhardware, Re-Analyse nutzt gespeicherte Felder | ✓ Good, Umbau in CI in beide Richtungen bewiesen, Bestandsinstallationen unberuehrt |
| Schema traegt IMMER sechs Koerperfelder, Befuellung nach FINDLING_LANGUAGES | Leere Felder kosten gemessen nichts, ein Schema statt Varianten | ✓ Good, keine Schema-Verzweigung, Sprachmenge als sechster Merker |
| Keine Spracherkennung, weder dokument- noch anfrageseitig (Anti-Feature, einstimmig) | Stiller Totalausfall bei Fehlerkennung, Anfragen im Mittel 2,4 Terme | ✓ Good, als Quelltext-Waechter in der Suite festgehalten |
| Frageseite erst NACH bewiesenem Umbauweg freischalten (17→18→19 als Sicherheitsbedingung) | Zwischenzustands-Fenster haette Totalausfall bedeutet (parse_query_lenient-ValueError) | ✓ Good, kein Zwischenzustand mit leerer Suche erreichbar |
| dismax gegen Score-Summe auf Messbasis entschieden | Rangverschiebung nur auf echten Daten beurteilbar | ✓ Good, gemessen und dokumentiert verworfen (MESS-09) |
| Kein Vorwaermen beim Start, Kaltstart lexikalisch sofort, Ladefenster-Restrisiko akzeptiert (D-03/D-08) | RAM-Budget auf 4-GB-Boxen schlaegt Latenzkomfort | ✓ Good, Kaltsuche 973 ms MIT Treffern statt 0; Restrisiko als AR-23-01 dokumentiert |
| gone-Reparaturlauf als Upgrade-Migration (D-04, Issue #14) | Arbeit ist genau die, die ohne den Bug angefallen waere | ✓ Good, Upgrade-CI-Beweis skipped 8→7; budachst-Bestaetigung steht aus (Issue offen) |
| Re-Analyse-Umbau auch fuer Tschechisch: Schema traegt immer alle Koerperfelder, cs als 14. Feld ohne Stemmer (D-30-04) | Ein Schema statt Varianten, leere Felder kosten nichts | ✓ Good, Umbau in beide Richtungen in CI, Platz 0,29-0,36 unter 0,40-Budget |
| Legacy-Formate in reinem Python statt LibreOffice (FIB/Clx fuer DOC, xlrd mit CFB-Vorpruefung) | LibreOffice = Imagegroesse + Prozess-Zoo | ✓ Good, Endlosschleifen-Befund in xlrd durch eigene Kettenpruefung abgefangen |
| Ordnerfilter nur in PHP, Scope ueber Mountliste + Recheck (D-32-06) | Kein zweites Rechtemodell im Python-Index | ✓ Good, Team-Folder-ACL-Faelle in CI belegt, M-32-02 in Phase 36 geschlossen |
| Ausschlussmuster als geschlossene Sprache ohne fnmatch/preg/eval (Gate methodengenau) | Angriffsflaeche und Laufzeit deckeln | ✓ Good, Differenztest gegen byte-gleiche 1.4.2-Fixture, feindlich 6,1 ms bei 4000 Zeichen |
| e5-small bleibt, granite nur mit Bedingung (Verdikt 35-11, p=0,0944) | Messung vor Modellwechsel | ✓ Good, Wechsel-Hype widerstanden, Bericht liegt fuer v1.6+ vor |
| Boesartiger Formatkorpus deterministisch im Baum, Signaturen als skipped(blocked_malicious) (D-36-01) | Reproduzierbare Haertung statt Einmal-Fuzzing | ✓ Good, 64 Faelle durch das Sandbox-Kind, in 16 l10n-Katalogen erklaert |

## Current Milestone: v1.6 Store-Sichtbarkeit und Betriebs-Feinschliff

**Goal:** Findling uebersteht den HaRP-Zertifikatswechsel ohne Admin-Eingriff (Issue #33), ist im Store besser auffindbar (Anzeigename "Findling Search", discussion-Link, Cross-Promo) und raeumt die aus v1.5 vertagten Feinschliff-Punkte ab.

**Target features (Owner-Ansagen 22.-28.10.2026):**
- Zert-Rotation #33: frpc liest /certs/frp bei x509-Fehler neu ein und startet neu (Zeittreiber des Releases)
- L-36-05: Anzeigetext "Bewusst ausgelassen: 0" mit Erklaersatz; L-36-06: Zaehler-Verzoegerung nach Ausschlussmuster-Aenderung
- #25-Dedup-Rest: Weg B der Designnotiz 35-DEDUP-NOTIZ.md, Owner-Fragen D1-D4 am Owner-Tor
- Umlaut-Fixes in docs/dev-setup.md, docs/embeddings.md, docs/install-check.md (Testkorpus-Begriffe wie Bahnhofstrasse NICHT anfassen)
- Store-Strategie 24.10.: discussion-Link auf Forum-Thread 249775, Cross-Promo-Satz zum MCP Connector, Anzeigename "Findling Search" (GO 22.10.)
- UPGRADE_FROM_TAG auf v1.5.0; Review-Infos IN-01 bis IN-06 der Phase 36 sichten
- Store-Einreichung 1.6.0 nach Owner-Abnahme; Ziel 29.10.2026

**Key context:** Owner verreist, arbeitet ueber Remote Control; Abnahmen laufen remote. Kein neues Feature-Terrain, deshalb keine Domain-Recherche. Docker auf der Entwicklerbox haengt (Audit-Tests nur in CI). Deferred Items aus v1.5 in STATE.md.

<details>
<summary>Archiv: Milestone-Beschreibung v1.5 (abgeschlossen 2026-10-28)</summary>

**Goal:** Wer heute fulltextsearch mit Elasticsearch betreibt, findet keinen Grund mehr zu bleiben: Findling deckt die erwarteten Funktionen (Filter in der Unified Search, Ausschlussmuster, Mail-/Archiv-/Altformate, weitere Sprache) ab und bietet einen klaren Umstiegsweg.

**Target features (Owner-Freigabe 10.10.2026):**
- UMST: Doku-Seite "Von Elasticsearch umsteigen" + Admin-Hinweis, wenn fulltextsearch parallel aktiv ist (Doppeltreffer); Wortlaut "OCR ohne Dateiaenderung und ohne Elasticsearch", NIE "einzige OCR" (workflow_ocr existiert fuer NC 33-35)
- USRCH: Typfilter und "in diesem Ordner" als Custom Filter des Unified-Search-Providers
- EXCL: Ausschlussmuster als Einstellung, Mac-Bundles (#22)
- FMT: .eml (stdlib), ZIP-Inhalte mit Zip-Bomb-Grenzen, .doc/.xls ohne LibreOffice (olefile/xlrd), HEIC
- CZ: ces-OCR (Weg wie dan/est) + tschechisches Koerperfeld ohne Stemmer, Umbau nur bei Aktivierung (#26)
- POL: #21 Grenzwerte nur anzeigen, F-29-03, Wortlaut "This box has fewer cores"
- Stretch: "Aehnliche Dokumente" (Vektoren vorhanden), granite-Messung (nur Messung), #25-Dedup-Design

**Key context:** Recherche 10.10.2026 (ES-Schmerzpunkte, Konkurrenz, Technik-Hebel) liegt vor, Gegenproben gemacht: tantivy-py 0.26.2 ist aktuell; granite r2 = ModernBERT, CLS-Pooling, keine Praefixe, eigener int8-Build noetig (quint8_avx2 ist x86-only); files_fulltextsearch_tesseract endet laut Store-Katalog bei NC 32. Ausgeschlossen: sqlite-vector (ELv2), Jina (CC BY-NC), EmbeddingGemma (Gemma Terms). .eml-Dateien IN Nextcloud sind Nextcloud-Files, kein Verstoss gegen "keine fremden Quellen".

**Ergebnis:** Alles geliefert, 1.5.0 am 21.10.2026 eingereicht (2x HTTP 201, Lauf 39598694849, Tag v1.5.0 auf 6c953a76), 1.5.1 als Nachzuegler. Benannte Vorbehalte: L-36-05/06 und #25-Dedup-Rest nach v1.6 vertagt, Zert-Rotation #33 offen. Details: .planning/milestones/v1.5-ROADMAP.md und MILESTONES.md.

</details>

<details>
<summary>Archiv: Milestone-Beschreibung v1.4 (abgeschlossen 2026-10-06)</summary>

**Goal (v1.4):** Findling passt seine Geschwindigkeit der Hardware an: Wer mehr als die 4-GB-Referenzbox hat, bekommt per Profil-Opt-in Parallelitaet (Einbettungsspur + N OCR-Slots), das 4-GB-Versprechen bleibt der unveraenderte Default.

**Target features (Owner-Entscheide 24./25.09.2026, bestaetigt 27.09.):**
- Leistungsprofile Sparsam/Standard/Leistung als Anteils-Formeln, nicht feste Slotzahlen; Sparsam Wert fuer Wert gegen heute gepinnt (Store-Zahl darf nicht wandern)
- Nebenlaeufigkeit als Kernfall: Einbettungsspur als eigener Nebenlaeufer (H1), dann N OCR-Slots (H2); PHP-Seite zieht mit (Art-Filter am Anspruch, KIND_BATCH)
- Hardware-Erkennung beim ersten Start mit Profil-VORSCHLAG, Admin bestaetigt; kein Zwang
- Vorab-Pruefung "Test vor dem Speichern" (N-Slot-Probe, RAM-Rechnung, Verdikt) plus Laufzeit-Rueckfall bei OOM
- Modellwahl bleibt drin (Owner 25.09. gegen die Research-Empfehlung), inkl. Marken-Reparatur (embedding_version um Gewichtspraezision erweitern, sonst stille Vektormischung)
- Erste echte Admin-Settings-UI (ui-phase-Gate); keine App-Spaltung

**Key context:** Vorarbeit .planning/research/BL-F04-vorarbeit-2026-09-25.md; Basiszahlen B1-B5 aus der Phase-22-Anfahrt (CI-Slot-Faktor F4 = 3,955, Skalierung real); KEINE Entdeckungs-Anfahrt noetig, aber eine Abnahme-Anfahrt am gebauten Produkt (Owner-Auflage: RAM-Messung je Stufe, bevor die UI sie anbietet). Offene Tor-Fragen der ersten Phase: Weg des Profils in den Container (Wege A/B/C), Anteile je Profil im Owner-Wortlaut, fp32-Lieferweg (K7).

**Ergebnis:** Alles geliefert, 1.4.0 am 06.10.2026 eingereicht, danach 1.4.1 und 1.4.2 (Issue #25, 09.10.).

</details>

<details>
<summary>Archiv: Milestone-Beschreibung v1.3 (abgeschlossen 2026-09-27)</summary>

**Goal:** Die lexikalische Suche beherrscht Spanisch, Italienisch, Niederlaendisch und Portugiesisch (Tantivy-Sprachfelder mit sauberer Migration), und die fuenf offenen Boxzahlen aus v1.2 werden nachgemessen.

**Ergebnis:** Alles geliefert, v1.3.0 am 27.09.2026 eingereicht (2x HTTP 201, Lauf 36304007154, Tag v1.3.0 auf 744d7e4). Benannte Vorbehalte: Ladefenster D-08 nur in CI gemessen (AR-23-01), Store-Rendering der Texte nicht nachgesehen. Details: .planning/milestones/v1.3-ROADMAP.md und MILESTONES.md.

</details>

<details>
<summary>Archiv: Milestone-Beschreibung v1.2 (abgeschlossen 2026-09-21)</summary>

**Goal:** Die v1.1-Verbesserungen werden auf der Zielhardware belegt (Wirkungsbeleg, Laststufen, Sprachfaelle) und die Suche baut sichtbar aus: Dateityp-Filter und Sortierung auf der Ergebnisseite plus Modell-Entladung im Leerlauf, abgeschlossen mit gehaerteter Store-Einreichung v1.2.0.

**Ergebnis:** Alles geliefert, v1.2.0 am 21.09.2026 eingereicht (2x HTTP 201, Lauf 35618848300). Benannte Vorbehalte: die Sprachfall-Messung ohne Fremdbestand lief nicht auf der Box (der Korpus-Snapshot IST der Fremdbestand), sondern wurde als Auflage A4 in Phase 16 ueber den gruenen arm64-CI-Ast nacherfuellt (10/10 Sprachfaelle, Owner-Zweig a); A1/A3 ohne Zielhardware-Nachmessung. Details: .planning/milestones/v1.2-ROADMAP.md und MILESTONES.md.

</details>

<details>
<summary>Archiv: Milestone-Beschreibung v1.1 (abgeschlossen 2026-09-11)</summary>

**Goal:** Die Suche wird spuerbar besser und schlanker, belegt durch einen Vergleichslauf gegen die v1.0-Baseline auf derselben Zielhardware.

**Target features:** Gemeinsame Embedding-Engine; lizenzkonforme Komposita-Wortliste; eigene Ergebnisseite mit Paginierung; Endungsvergleich der Verdikte; Vergleichsmessung auf der AWS-Box.

**Ergebnis:** Alles geliefert, v1.1.0 am 11.09.2026 eingereicht (Details: .planning/milestones/v1.1-ROADMAP.md und MILESTONES.md).

</details>

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check, still the right priority?
3. Audit Out of Scope, reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-28 after v1.5 milestone*
