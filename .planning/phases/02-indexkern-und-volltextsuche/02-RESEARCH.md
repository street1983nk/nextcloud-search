# Phase 2: Indexkern und Volltextsuche - Research

**Researched:** 2026-08-15
**Domain:** Tantivy 0.26 embedded (deutscher Analyzer, Snippets), Pull-Queue ueber die PHP-Companion-App, Crawl pro Mount, ACL-Vorfilter in SQLite, Textextraktion in reinem Python
**Confidence:** HIGH fuer Tantivy-API, Analyzer-Verhalten, Queue- und Crawl-Muster, Mount- und ACL-Aufloesung (Quellcode gelesen, Tantivy-Verhalten lokal mit `tantivy==0.26.0` ausgefuehrt und gemessen); MEDIUM fuer Wortlistengroesse, RAM-Kosten des Kompositasplitters und WAL-Verhalten im AppAPI-Volume

---

## Summary

Die Phase hat drei technische Kerne, und alle drei sind jetzt mechanisch geklaert statt vermutet.

**Erstens der deutsche Analyzer.** Die Filterkette aus CONTEXT.md ist mit `tantivy==0.26.0` lokal gebaut und mit echten deutschen Testfaellen gemessen worden. Zwei Befunde aendern die Planung. Der Kompositasplitter `Filter.split_compound` **ersetzt** das Kompositum durch seine Teile und splittet nur, wenn das Wort **vollstaendig** in aufeinanderfolgende Woerterbucheintraege zerfaellt. Ohne Fugenformen im Woerterbuch passiert daher gar nichts: mit der Liste `["kundigung", "frist"]` bleibt "Kuendigungsfrist" ungeteilt und ist ueber "Frist" nicht auffindbar, mit `["kundigungs", "frist"]` funktioniert es sofort. Die Wortliste zu bauen ist also nicht "eine Datei besorgen", sondern ein Aufbereitungsschritt mit Fugen-s, Normalisierung und Mindestlaenge. Der zweite Befund ist unangenehmer: der Snowball-Stemmer "german" vereinheitlicht Verbformen nicht. Gemessen: "suchen" und "Suche" werden beide zu `such`, "suchte" wird zu `sucht`, "gesucht" bleibt `gesucht`. Der in CONTEXT.md genannte Testfall "suchte/suchen" ist mit Tantivy-Bordmitteln **nicht erfuellbar** und muss ersetzt oder als dokumentierte Grenze gefuehrt werden. Nominalflexion dagegen funktioniert einwandfrei (Haus/Haeuser, Buch/Buecher, Vertrag/Vertraege, Kanzlei/Kanzleien jeweils identisch gestemmt), und Umlaute plus Eszett sind sauber (Strasse == Strasse, gross == gross).

**Zweitens die Snippets.** `Snippet.highlighted()` liefert **Byte**-Bereiche relativ zu `Snippet.fragment()`, nicht Zeichenpositionen. Bei deutschem Text ist das nie dasselbe: gemessen wurde `byte ranges=[(4, 20)]` fuer "Kuendigungsfrist" gegenueber den korrekten `char ranges=[(4, 19)]`, und ein naives Slicen mit den Bytewerten schneidet sichtbar falsch. Die ExApp muss umrechnen, bevor sie Offsets ins Protokoll gibt (Phase-1-Feld `highlights`). Zusaetzlich liefert der Generator bei gesplitteten Komposita mehrfach denselben Bereich, weil alle Teiltoken die Offsets des Originalworts erben. Die Bereiche muessen dedupliziert und verschmolzen werden.

**Drittens Queue, Crawl und ACL.** Das Betriebsmodell ist im Quellcode von `nextcloud/context_chat` vollstaendig belegt: ein `IRepairStep` beim Install legt einmalig einen `SchedulerJob` an, der pro Mount einen `StorageCrawlJob` einreiht, der sich mit `last_file_id` selbst nachplant. Fuer uns wichtig und neu gegenueber der Projektrecherche: die dafuer noetige Server-API `OCP\Files\Cache\IFileAccess` mit `getDistinctMounts()` und `getByAncestorInStorage()` ist **@since 32.0.0**, also genau unser Mindestfenster. Der ganze `getMountsOld`-Rueckfallpfad von context_chat entfaellt fuer uns ersatzlos. Bei der ACL ist context_chats Umsetzung dagegen der teuerste Teil: `IUserMountCache::getMountsForFileId()` kostet pro Datei zwei Abfragen plus einen `userExists`-Aufruf. Wir crawlen ohnehin pro Mount und koennen die Nutzerliste einmal je Mount holen und im Crawl-Batch per Pfadpraefix zuordnen, was exakt die Logik ist, die `UserMountCache` sonst pro Datei in SQL macht.

**Primary recommendation:** Ein Index, ein Schreiber, ein Worker. Tantivy-Schema mit `body_de`/`body_en` und genau einer gespeicherten Textkopie (`body_de` als `stored=True`, sie speist auch den SnippetGenerator, ein zweiter Textspeicher in SQLite entfaellt). Analyzer-Kette `simple -> lowercase -> stopword(german) -> ascii_fold -> split_compound -> remove_long(48) -> stemmer(german)`, registriert in genau einer Factory, die bei **jedem** Oeffnen des Index aufgerufen wird. Wortliste aus dem Debian-Paket `wngerman` (GPL-2+, `Architecture: all`, 4,6 MB) beim Image-Bau zu einer normalisierten Substantivliste mit Fugenformen destillieren, Feature per Umgebungsvariable abschaltbar. Queue und Crawl eins zu eins nach dem context_chat-Muster, aber mit kurzem Lock-Timeout und einem Nack-Endpunkt, weil `docker kill` sonst 24 Stunden lang Zeilen blockiert. Suche als **zwei** Aufrufe: `/search` liefert nur Kandidaten mit Score, `/snippets` liefert Textausschnitte fuer die vom PHP-Recheck ueberlebenden IDs. Das macht SRCH-02 strukturell wahr statt nur behauptet.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Engine und Sprache**
- Volltext-Engine: Tantivy 0.26 embedded, mmap; Writer-Heap 50 MB, num_threads=1 (4-GB-Budget)
- Deutsch: Snowball-Stemmer "german" + deutsche Stopwoerter + ascii_fold (Umlaut-Folding) + split_compound (Komposita; Wortliste beschaffen ist Teil der Phase, Lizenz pruefen); Englisch als zweites Feld/Pipeline
- Snippets: Klartext + Zeichenoffsets (Subline rendert kein HTML, Phase-1-Befund); Hervorhebung macht die PHP-Seite bzw. der Client mit den Offsets; Snippet-Erzeugung erst NACH bestandener Rechtepruefung (SRCH-02)
- Suchoperatoren: Phrasen, +/-, Filter Dateiname vs. Inhalt, Dateityp (SRCH-03)

**Berechtigungskette (Sicherheitsgrenze unveraendert)**
- SQLite-ACL-Tabelle (access_list: uid, fileid) als VORFILTER auf Kandidatenlisten (Ueberfetch + iteratives Nachfassen), finaler Recheck bleibt in PHP via getUserFolder()->getFirstNodeById() (COMP-04); NIE ein eigenes Rechtemodell in Python
- ACL gehoert ins ERSTE Schema (nie nachruesten); Schema fuehrt eine Indexversion (Tantivy-Upgrades koennen Reindex erzwingen)

**Indexer-Betriebsmodell (die Anti-fulltextsearch-Invarianten)**
- Pull-Queue: PHP fuehrt die Queue (Tabelle), Worker der ExApp pollen, verarbeiten, quittieren; Zeilen-Locks; Backpressure natuerlich (Muster context_chat, Quellcode-verifiziert)
- Crawl pro Mount, Cursor = fileid-Integer im Job-Zustand; jede Datei genau EINMAL egal wie viele Nutzer sie sehen (IDX-01); User-Homes + Team Folders default AN, External Storage default AUS
- Fortschritt in der DB, nie im Prozessspeicher: docker kill mitten im Lauf, Neustart, Fortsetzung an der Zustandsmarke = Abnahmetest (IDX-02)
- INDEX_WORKERS=1 als Architektur (IDX-08); OCR-/Embedding-Spuren kommen spaeter in dieselbe Ein-Worker-Disziplin
- failed/skipped sind sichtbare Erstklasse-Zustaende mit Grund (zu gross, Typ, Fehler); nie stumm (IDX-06); diese Zustaende sind die Datenbasis fuer die Phase-4-Diagnose
- Zero-Config-Leitplanken: Dokument-Allowlist (PDF, Office, OpenDocument, Text/Markdown, RTF, HTML), 50-MB-Extraktions-Cap, openpyxl read_only + Zellcap 200k, keine Videos/Archive

**Extraktion (Stack-Research, gepinnt)**
- pypdfium2 (PDF-Text), pypdf (Metadaten/Verschluesselungs-Erkennung VOR pypdfium2), python-docx, python-pptx, openpyxl read_only, ODF via zipfile+lxml (KEIN odfpy), lxml.html, striprtf, charset-normalizer; passwortgeschuetzte PDFs -> skipped mit Grund
- Inhalte fliessen ausschliesslich ueber das Content-Gateway aus Phase 1 (fetch_file_stream, download2stream); Gate A (Nur-Lesen) und Gate B (Korpus-Pruefsummen) bleiben aktiv und duerfen nie verletzt werden

**Qualitaet und Umgebung**
- Alle 5 Python-Gates vor jedem Commit lokal gruen; CI-Erweiterungen folgen dem Phase-1-Muster (walking-skeleton + readonly-gate bleiben gruen, neue Jobs fuer Index/Suche-E2E)
- Referenzkorpus testdata/corpus/ erweitern statt ersetzen (byteidentisch generiert, -text in .gitattributes beachten)
- KEIN lokales PHP; PHP-Verifikation via CI; lokale E2E-Proben ueber scripts/dev/ (FINDLING_PORT beachten, 8080 ist von der parallelen MCP-Session belegt, 8090 nehmen)

### Claude's Discretion

- Tantivy-Schema-Detail (Felder, DE/EN-Doppelfeld vs. Sprach-Erkennung), Chunking fuers Snippet-Fenster
- Queue-Schema und Quittungs-Protokoll im Detail; Wahl SQLite-Datei-Layout im Container-Volume
- Wie der Erstindex angestossen wird (occ-Kommando der PHP-App vs. Auto-Start nach Registrierung; Zero-Config spricht fuer Auto-Start mit Vorab-Schaetzungs-Hook fuer Phase 4)
- Umgang mit dem Kanarien-Treffer aus Phase 1

### Deferred Ideas (OUT OF SCOPE)

- Events + ETag-Reconcile + Loeschpfad: Phase 3 (aber: Schema soll Deletions-Verarbeitung nicht verbauen)
- OCR: Phase 3; Embeddings/RRF: Phase 6 (Schema embedding-ready, kein Umbau)
- Statusseite/Diagnose-UI: Phase 4 (aber failed/skipped-Daten entstehen JETZT)
- Lasttest 100k+: Phase 5
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Beschreibung | Research Support |
|----|--------------|------------------|
| COMP-04 | Suchfluss: ExApp liefert Kandidaten-fileids mit Scores, PHP macht den finalen Recheck pro Treffer, erst danach Snippets | Pattern 4 (Zwei-Aufruf-Protokoll), Antwort auf Frage 1d, Code-Beispiel 5 und 6 |
| IDX-01 | Erstindex crawlt pro Mount, jede Datei genau einmal | Pattern 2 (Crawl pro Mount ueber `IFileAccess`, @since 32), Antwort auf Frage 3, Code-Beispiel 7 |
| IDX-02 | Indexer ueberlebt `docker kill`, Fortschritt in der DB | Pattern 5 (Commit-Reihenfolge), Antwort auf Frage 5, Pitfall 3 und 4, Tantivy-Writer-Lock ist ein OS-Lock und wird beim Prozesstod freigegeben |
| IDX-03 | Pull-Queue mit Zeilen-Locks, natuerliche Backpressure | Pattern 1 (Queue-Schema und Endpunkte, Quellcode-verifiziert), Antwort auf Frage 3 |
| IDX-06 | Zero-Config-Leitplanken, failed/skipped sichtbar mit Grund | Antwort auf Frage 6 (Fehlerklassen-Mapping), SQLite-Schema `files.state`/`files.reason`, Pitfall 6 |
| IDX-08 | INDEX_WORKERS=1 als Architektur | Pattern 5, Abschnitt "Prozess- und Threadmodell im Container" |
| SRCH-01 | Volltextsuche mit deutschem Stemming, Stoppwoertern, Komposita, Umlaut-Folding, plus Englisch | Antwort auf Frage 1a und 1b, gemessene Analyzer-Ergebnisse, Wortlisten-Rezept aus `wngerman` |
| SRCH-02 | Snippets erst nach bestandener Rechtepruefung | Pattern 4, Antwort auf Frage 1c (Byte- gegen Zeichenoffsets), Code-Beispiel 4 |
| SRCH-03 | Suchoperatoren: Phrase, +/-, Dateiname/Inhalt, Dateityp | Antwort auf Frage 1d, gemessene Query-Faelle, `IFilteringProvider` mit dem eingebauten Filter `title-only` |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

| Direktive | Wirkung auf Phase 2 |
|---|---|
| Python 3.13 + uv, System-Python gilt als defekt | Jede Python-Aktion ueber `uv run`/`uv sync --frozen`, auch die Wortlisten-Aufbereitung und alle lokalen Proben |
| Qualitaetsgates: ruff-Vollregelsatz, pyright basic, vulture 80, pytest, lokal gruen vor Commit | Neue Module (storage, pipeline, retrieval, workers) fallen unter dieselben Gates; `filterwarnings = ["error::DeprecationWarning"]` bleibt scharf |
| Keine Em-Dashes, echte Umlaute nur in deutscher Prosa, nie in Code | Feldnamen, Tokenizer-Namen, Zustaende, Fehlergruende, Log-Texte alle ASCII; die Wortliste ist Daten und darf Umlaute tragen, wird aber ohnehin ascii-gefaltet |
| Code und README Englisch, Projektkommunikation Deutsch | Alle neuen Bezeichner und Kommentare Englisch |
| Security/Privacy: Berechtigungs-Durchgriff strikt, keine Inhalte verlassen den Server, keine Telemetrie | Nutzer-ID nur aus dem AppAPI-Header; Snippets nur nach Recheck; keine Dateinamen und keine Inhalte in Logs |
| Hardware-Ziel 4-8 GB RAM, ARM-tauglich, CPU-only | Writer-Heap 50 MB, ein Worker, Extraktions-Caps, Wortlisten-Automat gemessen statt geschaetzt |
| AGPL-3.0 | Die Wortliste ist GPL-2+ und damit vertraeglich, aber Lizenztext und Herkunft muessen ins Image und in die Doku |
| GSD-Workflow-Zwang | Betrifft die Ausfuehrung, nicht die Recherche |

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Mount-Aufzaehlung, Datei-Enumeration, Crawl-Cursor | Nextcloud-PHP-App (BackgroundJob) | Nextcloud-Datenbank | `IFileAccess` und `oc_filecache` existieren nur im PHP-Prozess; der Cursor lebt im Job-Argument und ueberlebt jeden Neustart |
| Arbeitsvorrat und Zeilen-Locks | Nextcloud-PHP-App (eigene `oc_`-Tabelle) | - | Transaktional zum Dateisystem-Zustand; Backpressure entsteht dadurch, dass niemand pusht |
| Ermittlung "wer darf diese Datei sehen" | Nextcloud-PHP-App (`IUserMountCache`) | - | Einzige nicht driftende Quelle; Gruppenordner und externe Mounts sind darin enthalten, die Share-API allein waere unvollstaendig |
| Autoritative Rechteentscheidung pro Treffer | Nextcloud-PHP-App (`getUserFolder()->getFirstNodeById()`) | - | Unveraenderte Sicherheitsgrenze aus Phase 1, COMP-04 |
| ACL-Vorfilter auf Kandidatenlisten | ExApp (SQLite) | - | Nur ein Beschleuniger, nie eine Entscheidung; darf falsch-positiv sein, nie falsch-negativ ohne Nachfassen |
| Byteabruf der Dateien | Nextcloud-PHP-App (Content-Gateway) | ExApp (`fetch_file_stream`) | Phase 1, unveraendert; strukturell nur lesend |
| Textextraktion | ExApp (Python) | - | Ausschliesslich im Container, mit harten Caps und ohne Rueckschreibpfad |
| Volltextindex, Ranking, Snippet-Erzeugung | ExApp (Tantivy im Prozess) | - | Eingebettete Engine, kein zweiter Serverprozess |
| Fortschritt, failed/skipped, Indexversion | ExApp (SQLite im Volume) | - | Der Index ist ein Cache, der Betriebszustand gehoert daneben und ueberlebt einen Neuaufbau |
| Suchoperatoren-Syntax und Filterabbildung | ExApp (Query-Bau) | Nextcloud-PHP-App (`IFilteringProvider`) | Die Query-Grammatik gehoert zur Engine; `title-only` und Dateityp reichen als Filter von aussen herein |
| Darstellung und Hervorhebung | Browser (Vue) | Nextcloud-PHP-App | Die Subline ist Text, Markup wird woertlich angezeigt (Phase-1-Befund) |

---

## Standard Stack

### Core

| Library | Version | Zweck | Warum Standard |
|---------|---------|-------|----------------|
| `tantivy` | 0.26.0 (PyPI, 29.04.2026) | Volltextindex, Analyzer, Snippets | Einzige eingebettete Engine mit Snowball-Stemmer, Stoppwortlisten und Kompositasplitter; cp313-Wheels fuer `manylinux_2_17_aarch64` vorhanden [VERIFIED: PyPI JSON-API, Wheel-Liste, lokal ausgefuehrt] |
| `pypdfium2` | 5.13.0 (13.08.2026) | PDF-Textextraktion, spaeter auch Rasterung fuer OCR | PDFium-Kern, BSD/Apache, `py3-none-manylinux_2_17_aarch64` [VERIFIED: PyPI] |
| `pypdf` | 6.16.1 (14.08.2026) | Verschluesselungs- und Metadatenerkennung VOR pypdfium2 | Pur Python, erkennt passwortgeschuetzte Dateien, bevor der C-Kern stolpert [VERIFIED: PyPI] |
| `python-docx` | 1.2.0 | DOCX-Text | MIT, stabil; Kopf-/Fusszeilen fehlen bekanntermassen [VERIFIED: PyPI] |
| `python-pptx` | 1.0.2 | PPTX-Text | MIT; OOXML ist eingefroren, das alte Release ist kein Risiko [VERIFIED: PyPI] |
| `openpyxl` | 3.1.5 | XLSX-Text, zwingend `read_only=True, data_only=True` | MIT; ohne read_only baut es die Mappe komplett im RAM auf [VERIFIED: PyPI] |
| `lxml` | 6.1.1 | ODF (`content.xml`) und HTML | aarch64-Wheels fuer cp313 vorhanden; ersetzt odfpy vollstaendig [VERIFIED: PyPI] |
| `striprtf` | 0.0.32 | RTF-Text | BSD, ein Zweck, `py3-none-any` [VERIFIED: PyPI] |
| `charset-normalizer` | 3.5.0 empfohlen (3.5.1 seit 15.08.2026) | Encoding-Erkennung fuer Alttexte (cp1252, latin-1) | MIT; 3.5.1 ist am Recherchetag erschienen, deshalb erst nach gruener CI hochziehen [VERIFIED: PyPI] |

### Supporting

| Library / Artefakt | Version | Zweck | Wann |
|---------|---------|-------|------|
| Debian-Paket `wngerman` | igerman98 20161207-15 (trixie), `Architecture: all`, 4,6 MB installiert | Quelle der Kompositawortliste, Datei `/usr/share/dict/ngerman` | Nur im Image-Build-Stage: installieren, Liste destillieren, Paket wieder entfernen [VERIFIED: sources.debian.org, packages.debian.org Dateiliste] |
| `python-magic` oder Nextcloud-Mimetype | - | Typerkennung nach Inhalt statt Endung | Der Queue-Eintrag traegt bereits den Nextcloud-Mimetype; ein zweiter Erkenner ist erst noetig, wenn der erste luegt |
| stdlib `sqlite3` | Python 3.13 | Zustand, ACL, Fortschritt | Keine externe Abhaengigkeit, WAL und `busy_timeout` sind Pragmas |
| stdlib `zipfile` | Python 3.13 | ODF-Container | Zusammen mit lxml die vollstaendige ODF-Loesung |

### Alternatives Considered

| Statt | Moeglich waere | Abwaegung |
|-------|----------------|-----------|
| Zwei Felder `body_de` und `body_en` | Ein Feld plus Spracherkennung pro Dokument | Spracherkennung kostet eine weitere Abhaengigkeit und ist bei gemischten Dokumenten (deutsches Anschreiben, englisches Anhangzitat) systematisch falsch. Zwei Felder kosten Indexgroesse, aber die ist per Umgebungsvariable abschaltbar. Empfehlung: zwei Felder, `FINDLING_LANGS=de,en` als Schalter |
| Gespeichertes Tantivy-Feld als Textquelle fuer Snippets | Textkopie in SQLite | Tantivy speichert Dokumentfelder komprimiert im Doc-Store; eine zweite Kopie in SQLite verdoppelt den Platzbedarf ohne Gegenwert. `SnippetGenerator.snippet_from_doc()` nimmt jedes `Document`, die Quelle ist also frei waehlbar. Empfehlung: eine Kopie, im Index |
| Kompositasplitter mit Wortliste | Kein Splitten, dafuer `Query.regex_query` oder ngram-Feld | Regex-Queries scannen das Term-Dictionary linear, ngram-Felder vervielfachen die Indexgroesse. Beides ist auf der Zielhardware falsch. Empfehlung: Splitter mit abschaltbarem Feature-Flag, sonst dokumentierte Grenze |
| ACL-Vorfilter in SQLite | `acl_uid` als Mehrfachfeld im Tantivy-Dokument | Im Tantivy-Dokument waere jede Freigabeaenderung ein vollstaendiges Neuschreiben des Dokuments. In CONTEXT.md ist SQLite gesetzt, und die Begruendung traegt |
| Zwei Aufrufe fuer Suche und Snippets | Ein Aufruf mit Snippets im Ergebnis | Ein Aufruf verletzt SRCH-02 im Wortsinn (Snippets entstehen vor dem Recheck). Zwei Aufrufe kosten eine zweite Proxy-Runde, sind aber zustandslos und billig, weil der zweite Aufruf nur `parse_query` plus Doc-Store-Lesen ist |

**Installation:**

```bash
cd backend
uv add "tantivy==0.26.0" "pypdfium2==5.13.0" "pypdf==6.16.1" "python-docx==1.2.0" \
       "python-pptx==1.0.2" "openpyxl==3.1.5" "lxml==6.1.1" "striprtf==0.0.32" \
       "charset-normalizer==3.5.0"
```

**Version verification:** Alle Versionen am 15.08.2026 gegen die PyPI-JSON-API geprueft (`info.version`, `urls[].filename` auf `aarch64` und `cp313`). `tantivy` 0.26.0 liefert `cp313` und `cp313t` fuer `manylinux_2_17_aarch64` und zusaetzlich `win_amd64`, weshalb lokale Proben auf dieser Maschine ueberhaupt moeglich waren.

---

## Package Legitimacy Audit

Ausgefuehrt am 15.08.2026 mit `slopcheck install tantivy pypdfium2 pypdf python-docx python-pptx openpyxl lxml striprtf charset-normalizer`. Ergebnis: `scanned 9 packages, 9 OK`. (Der anschliessende Abbruch von slopcheck ist ein Windows-Artefakt beim Nachstarten von `pip` und betrifft die Bewertung nicht.)

| Package | Registry | Alter | Source Repo | slopcheck | Disposition |
|---------|----------|-------|-------------|-----------|-------------|
| `tantivy` | PyPI | seit 2021 | github.com/quickwit-oss/tantivy-py | [OK] | Approved |
| `pypdfium2` | PyPI | seit 2022 | github.com/pypdfium2-team/pypdfium2 | [OK] | Approved |
| `pypdf` | PyPI | seit 2022 (PyPDF2 seit 2012) | github.com/py-pdf/pypdf | [OK] | Approved |
| `python-docx` | PyPI | seit 2013 | github.com/python-openxml/python-docx | [OK] | Approved |
| `python-pptx` | PyPI | seit 2013 | github.com/scanny/python-pptx | [OK] | Approved |
| `openpyxl` | PyPI | seit 2010 | foss.heptapod.net/openpyxl | [OK] | Approved |
| `lxml` | PyPI | seit 2005 | github.com/lxml/lxml | [OK] | Approved |
| `striprtf` | PyPI | seit 2019 | github.com/joshy/striprtf | [OK] | Approved |
| `charset-normalizer` | PyPI | seit 2019 | github.com/jawah/charset_normalizer | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** keine
**Packages flagged as suspicious [SUS]:** keine

Nicht-PyPI-Artefakt: das Debian-Paket `wngerman` (Quellpaket `igerman98`, Version 20161207-15 in trixie). Kein Registry-Slopcheck moeglich, dafuer im Debian-Quellbaum verifiziert: Upstream `https://www.j3e.de/ispell/igerman98/dict/`, Copyright Bjoern Jacke, Lizenz GPL-2+, Binaerpaket liefert `/usr/share/dict/ngerman`. Version und Pfad im Dockerfile pinnen, nicht `latest` ziehen.

---

## Architecture Patterns

### System Architecture Diagram

```
                       PHP-SEITE (Nextcloud-Prozess)
  Install-RepairStep --> SchedulerJob --> pro Mount ein StorageCrawlJob
                                              |  IFileAccess::getByAncestorInStorage
                                              |  (storage, root, cursor fileid, mime-Filter)
                                              v
                                     oc_findling_queue
                                     (file_id, storage_id, root_id,
                                      update, locked_at)
                                              |
   Nutzer tippt                               |
        |                                     |
        v                                     |
   IProvider::search                          |
        |                                     |
        v                                     |
   ExAppService (einzige exAppRequest-Stelle) |
        |  1) POST /search   -> Kandidaten    |
        |  2) Recheck je Treffer:             |
        |     getUserFolder(uid)              |
        |       ->getFirstNodeById(fileId)    |
        |  3) POST /snippets -> Textstellen   |
        v                                     v
  ============ AppAPI-Proxy / HaRP ==========================
        |                                     ^
        v                                     |   GET  /queues/documents  (holen, sperrt)
   ExApp-CONTAINER                            |   DELETE /queues/documents (quittieren)
   +-------------------------------------+    |   POST /queues/documents/unlock (nack)
   | HTTP: /search  /snippets  /status   |    |   GET  /files/{fileId}?userId= (Bytes)
   +-------------------------------------+    |
   | genau EIN Indexer-Thread            |----+
   |   poll -> fetch -> extract ->       |
   |   add_document -> commit -> mark    |
   +-------------------------------------+
   | Tantivy Index (mmap, ein Writer)    |
   |   file_id, storage_id, name_de/en,  |
   |   body_de(stored)/body_en, ext,mtime|
   +-------------------------------------+
   | SQLite state.db (WAL)               |
   |   files(state, reason, attempts)    |
   |   acl(uid, file_id)                 |
   |   mounts(cursor), meta(versions)    |
   +-------------------------------------+
     alles unter $APP_PERSISTENT_STORAGE
```

Der einzige Pfad, auf dem Dateibytes fliessen, bleibt das Content-Gateway aus Phase 1. Der einzige Pfad, auf dem die ExApp in Nextcloud schreibt, ist das Quittieren von Queue-Zeilen, und genau dafuer muss Gate A eine Ausnahme bekommen (siehe Pitfall 7).

### Recommended Project Structure

```
backend/src/findling/
  api/
    search.py        # POST /search (nur Kandidaten) und POST /snippets
    status.py        # GET /status: Zaehler fuer Phase 4, schon jetzt befuellt
  nc/
    client.py        # UNVERAENDERTE Grenze: einziges Modul mit nc_py_api
    queue.py         # OCS-Aufrufe der Queue, ruft ausschliesslich client.py
  workers/
    indexer.py       # der eine Worker-Thread: poll, fetch, extract, index, ack
  pipeline/
    detect.py        # Allowlist, Groessen-Cap, Typentscheidung
    extract.py       # Dispatcher auf die Formatmodule
    formats/         # pdf.py, ooxml.py, odf.py, html.py, rtf.py, plain.py
  index/
    analyzer.py      # die eine Analyzer-Factory (DE und EN)
    schema.py        # Schemadefinition plus Indexversion
    writer.py        # einziger Tantivy-Writer, Sammel-Commit
    search.py        # Query-Bau, Ueberfetch, Snippet-Erzeugung
  storage/
    schema.sql       # SQLite-Schema als Datei, nicht im Code
    state_repo.py    # files, mounts, meta
    acl_repo.py      # acl
  wordlist/
    build_wordlist.py  # Build-Stage-Werkzeug, nicht Laufzeitcode

php/lib/
  BackgroundJobs/SchedulerJob.php
  BackgroundJobs/StorageCrawlJob.php
  Controller/QueueController.php     # #[ExAppRequired] Queue-Endpunkte
  Db/QueueFile.php, QueueFileMapper.php
  Migration/Version000200Date20260815xxxxxx.php
  Repair/AppInstallStep.php
  Service/StorageService.php         # Mounts, Dateien, Nutzer je Mount
  Service/QueueService.php
```

Zwei Kapselungen sind nicht verhandelbar. `nc/client.py` bleibt das einzige Modul mit `nc_py_api`, sonst faellt Gate A. Und `index/writer.py` ist die einzige Stelle, die einen `IndexWriter` erzeugt, weil Tantivy pro Verzeichnis genau einen zulaesst.

### Pattern 1: Pull-Queue in der PHP-App

**Was:** Eine eigene `oc_`-Tabelle mit den Spalten `id, file_id, storage_id, root_id, update, locked_at`. `GET /queues/documents?n=64` holt ungesperrte Zeilen, sperrt sie per `UPDATE ... SET locked_at=now WHERE id=? AND (locked_at IS NULL OR locked_at <= now-timeout)` und liefert je Zeile ein Quellobjekt mit Metadaten, aber **ohne** Inhalt. `DELETE /queues/documents` quittiert. Beide Endpunkte tragen `#[ExAppRequired]`.

**Wann:** Fuer jeden Arbeitsvorrat, den die ExApp abarbeitet, jetzt und in Phase 3.

**Quellcode-Vorbild, woertlich gelesen** (`context_chat/lib/Db/QueueMapper.php`): das Sperren ist ein bedingtes `UPDATE`, dessen Rueckgabewert (`executeStatement() >= 1`) entscheidet, ob die Zeile ausgeliefert wird. Damit ist die Sperre auch bei zwei gleichzeitigen Pollern eindeutig, ohne `SELECT ... FOR UPDATE` und ohne dialektspezifische Klauseln.

**Zwei bewusste Abweichungen von context_chat:**

1. `LOCK_TIMEOUT` steht dort auf `60*60*24`, also 24 Stunden. Fuer IDX-02 waere das toedlich: nach einem `docker kill` blieben die gerade bearbeiteten Zeilen einen Tag unsichtbar. Empfehlung 15 Minuten, als Konstante, plus
2. ein zusaetzlicher Endpunkt `POST /queues/documents/unlock` mit einer ID-Liste, den der Worker im SIGTERM-Handler ruft. Damit ist ein geordneter Neustart sofort wieder produktiv und nur ein hartes Kill wartet den Timeout ab.

**Kostenbasierte Batchgroesse:** zusaetzlich zu `n` ein Parameter `max_bytes`. context_chat hat das nicht und begrenzt nur die Einzeldateigroesse. Auf einer 4-GB-Box ist ein Batch aus 64 Dateien zu je 40 MB der Unterschied zwischen laufen und sterben.

### Pattern 2: Crawl pro Mount mit Integer-Cursor

**Was:** `IRepairStep` beim Install legt einmalig `SchedulerJob` an. Dieser laeuft einmal, zaehlt die Mounts auf und legt je Mount einen `StorageCrawlJob` mit `{storage_id, root_id, overridden_root, last_file_id: 0}` an. Der Crawl-Job liest einen Batch (2000), reiht ein, entfernt sich selbst aus der Jobliste und plant sich per `scheduleAfter()` mit dem neuen `last_file_id` neu ein.

**Der entscheidende neue Befund:** `OCP\Files\Cache\IFileAccess::getDistinctMounts(array $mountProviders, bool $onlyUserFilesMounts)` und `getByAncestorInStorage(int $storageId, int $folderId, int $fileIdCursor, int $maxResults, array $mimeTypeIds, bool $endToEndEncrypted, bool $serverSideEncrypted)` sind **@since 32.0.0** [VERIFIED: `nextcloud/server` stable34, `lib/public/Files/Cache/IFileAccess.php`]. Unser Mindestfenster ist NC 32. Der gesamte `getMountsOld`/`getFilesInMountOld`-Zweig von context_chat, inklusive der Reflection-Pruefung `isFileAccessAvailable()`, entfaellt fuer uns. Das spart etwa 120 Zeilen handgeschriebenes SQL gegen `oc_filecache` und die dazugehoerige Dialektpflege.

**Mount-Typen (CONTEXT: Homes und Team Folders an, External Storage aus):**

```php
// Team Folders sind die umbenannten Group Folders; die Klasse heisst unveraendert so.
private const MOUNT_PROVIDERS = [
    'OC\Files\Mount\LocalHomeMountProvider',
    'OC\Files\Mount\ObjectHomeMountProvider',
    'OCA\GroupFolders\Mount\MountProvider',
];
// bewusst NICHT: 'OCA\Files_External\Config\ConfigAdapter'
```

`onlyUserFilesMounts: true` uebernimmt genau die Aufgabe, die context_chat sonst per Extraabfrage auf den `files`-Unterordner erledigt: der Home-Root wird auf den `files`-Ordner umgebogen, sodass `files_versions` und `files_trashbin` gar nicht erst im Crawl auftauchen.

**Mimetype-Filter im SQL:** `getByAncestorInStorage` nimmt eine Liste numerischer Mimetype-IDs (`IMimeTypeLoader::getId()`). Die Allowlist gehoert damit in die Abfrage und nicht in einen Python-Filter nach dem Netzwerktransfer.

### Pattern 3: ACL einmal pro Mount statt einmal pro Datei

**Was:** Die Nutzerliste zu einer Datei wird nicht mit `getMountsForFileId()` je Datei geholt, sondern einmal je Crawl-Batch aus `IUserMountCache::getMountsForStorageId($storageId)`, und danach im Speicher per Pfadpraefix zugeordnet.

**Warum:** `UserMountCache::getMountsForFileId()` macht laut Quellcode zuerst eine Abfrage fuer `(storage, internalPath)` der Datei, dann eine zweite mit Join auf `filecache` und einer `substring`-Bedingung, die prueft, ob der Mount-Root ein **Pfadpraefix** der Datei ist, und zusaetzlich pro Ergebniszeile ein `userExists()`. Bei 100.000 Dateien sind das mindestens 200.000 Abfragen fuer eine Information, die sich pro Mount genau einmal aendert. Die Praefixlogik ist trivial nachzubilden, weil der Crawl den Pfad ohnehin kennt.

**Wichtig, damit es korrekt bleibt:** Die Praefixpruefung ist der Kern, nicht der Storage. Ein Nutzer mit einer Freigabe auf einen Unterordner hat einen Mount, dessen Root dieser Unterordner ist. Wer nur "alle Nutzer dieses Storage" nimmt, baut ein Rechteleck in den Vorfilter. Der Vorfilter ist zwar nicht die Sicherheitsgrenze, aber ein systematisch zu weiter Vorfilter macht die Ueberfetch-Strategie wirkungslos und laesst PHP jede Suche leerlaufen.

**Uebertragungsweg:** Die Nutzerliste reist **mit dem Queue-Eintrag** (Feld `userIds`), nicht ueber einen eigenen Endpunkt. Begruendung: sie wird genau dann gebraucht, wenn das Dokument indexiert wird, sie ist klein (Handvoll UIDs), und ein zweiter Endpunkt waere ein zweiter Weg mit eigener Fehlerbehandlung fuer denselben Zweck. Der eigene Aktions-Endpunkt fuer reine Zugriffsaenderungen ohne Neuindexierung gehoert in Phase 3, wo Share-Events entstehen; das Schema (`acl(uid, file_id)`) traegt ihn ohne Aenderung.

### Pattern 4: Suche in zwei Aufrufen, Snippets zuletzt

**Was:**

```
1. POST /search    {query, limit, cursor, filters}
   -> {candidates: [{fileId, score, storageId, mtime, ext}], cursor, degraded}
2. PHP: pro fileId getUserFolder(uid)->getFirstNodeById(fileId), verwerfen was fehlt
3. POST /snippets  {query, fileIds: [ueberlebende]}
   -> {snippets: {fileId: {text, highlights: [[start,end], ...]}}}
```

**Warum zwei Aufrufe:** SRCH-02 sagt, Snippets entstehen erst nach bestandener Rechtepruefung. Mit einem Aufruf ist das unmoeglich, weil die Pruefung in PHP stattfindet. Der zweite Aufruf ist billig und **zustandslos**: `SnippetGenerator.create(searcher, query, schema, "body_de")` braucht nur die geparste Query und das Dokument aus dem Doc-Store. Es ist kein Query-Cache noetig, also auch keine Cache-Invalidierung und kein Speicherleck.

**Absicherung des zweiten Aufrufs:** `/snippets` wendet denselben SQLite-ACL-Vorfilter fuer die Header-Nutzer-ID an. Der Endpunkt ist damit auch dann nicht als Leseprimitiv missbrauchbar, wenn jemand ihn mit fremden fileIds ruft.

**Zeitbudget:** Der Proxy-Timeout aus Phase 1 steht auf 2 Sekunden pro Aufruf. Zwei Aufrufe koennen also im schlechtesten Fall 4 Sekunden kosten. Empfehlung: `/search` behaelt 2 Sekunden, `/snippets` bekommt 1 Sekunde und faellt bei Timeout auf leere Snippets zurueck. Ein Treffer ohne Textausschnitt ist ein brauchbares Ergebnis, ein haengender Provider nicht.

**Kanarien-Treffer aus Phase 1 (Claude's Discretion):** Empfehlung, den Treffer nur noch bei dem exakten Suchbegriff `findling-canary` zu liefern und ihn aus jeder anderen Antwort zu entfernen. Damit bleibt der Integrationstest aus Phase 1 unveraendert gruen (er sucht genau diesen Begriff), und normale Suchen sind sauber. Der Kanarienvogel wird so zum Diagnosewerkzeug, wie es PITFALLS Nr. 2 verlangt.

### Pattern 5: Reihenfolge von Commit, Zustand und Quittung

**Was:** Fuer jeden Sammel-Commit gilt strikt diese Reihenfolge:

```
1. Bytes holen, extrahieren, add_document (Tantivy, noch nicht sichtbar)
2. writer.commit()                      <- ab hier ist der Index dauerhaft
3. SQLite: files.state = 'done' | 'failed' | 'skipped', reason, indexed_at (eine Transaktion)
4. DELETE /queues/documents             <- Quittung an PHP
```

**Warum genau so:** Jeder Schritt ist der Punkt, an dem ein `docker kill` folgenlos bleiben muss. Bricht es vor 2 ab, ist nichts passiert, die Zeilen laufen nach dem Lock-Timeout erneut ein. Bricht es zwischen 2 und 3 ab, ist das Dokument im Index und gilt in SQLite noch als offen: die Wiederholung ueberschreibt es (`delete_documents` auf `file_id`, dann `add_document`), das ist idempotent. Bricht es zwischen 3 und 4 ab, kommt die Zeile aus der PHP-Queue erneut, und der Worker sieht in SQLite `done` mit gleichem `content_hash` und quittiert sofort ohne Arbeit. Die umgekehrte Reihenfolge, erst Zustand dann Commit, verliert Dokumente stillschweigend und ist genau die Fehlerklasse aus PITFALLS Nr. 2.

**Tantivy-Writer-Lock nach hartem Kill:** kein Problem. `MmapDirectory::acquire_lock` oeffnet `.tantivy-writer.lock` und nimmt einen **OS-Lock** (`try_lock_exclusive`); der Kommentar im Quellcode sagt ausdruecklich, dass das Loslassen des Dateihandles die Sperre freigibt. Ein getoeteter Prozess gibt seine Handles ab, also ist der Index beim naechsten Start sofort beschreibbar. Die Datei bleibt liegen, sie ist bedeutungslos. Nicht darauf verlassen, wenn das Volume je auf NFS liegt.

**INDEX_WORKERS=1 (IDX-08):** ein Thread, der pollt und arbeitet. Tantivy gibt in `add_document`, `commit` und `search` die GIL frei (`py.detach`), deshalb blockiert der Indexer die Suche nicht spuerbar. Die Suchendpunkte sollen ihre Tantivy-Aufrufe trotzdem ueber `asyncio.to_thread` fahren, damit der Event-Loop bei einem langen Commit nicht steht.

### Pattern 6: Die deutsche Analyzer-Kette

**Was:** Genau eine Factory baut den Analyzer und wird bei **jedem** Oeffnen des Index aufgerufen.

```python
ANALYZER_VERSION = 1  # jede Aenderung hier erzwingt Reindex

def german_analyzer(constituents: list[str]) -> TextAnalyzer:
    builder = (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.stopword("german"))   # MUSS vor ascii_fold stehen
        .filter(Filter.ascii_fold())
        .filter(Filter.split_compound(constituents))
        .filter(Filter.remove_long(48))
        .filter(Filter.stemmer("german"))
    )
    return builder.build()
```

**Die Reihenfolge ist begruendet, nicht Geschmack:**

| Position | Filter | Warum genau hier |
|---|---|---|
| 2 | `lowercase` | Alles Weitere vergleicht Zeichenketten exakt |
| 3 | `stopword("german")` | Die eingebaute Liste enthaelt Umlaute (`fuer`, `ueber`, `waehrend`, `koennte` mit echten Umlauten) und vergleicht exakt gegen `token.text`. Nach dem Falten wuerde sie nichts mehr treffen. Gemessen: "fuer ueber das" ergibt mit dieser Reihenfolge `[]` [VERIFIED: lokal ausgefuehrt] |
| 4 | `ascii_fold` | Danach ist alles ASCII, die Wortliste kann ASCII sein, und Muellers Suche nach "Muller" trifft "Mueller mit Umlaut" |
| 5 | `split_compound` | Braucht den normalisierten Token; die Wortliste muss in genau dieser Form vorliegen |
| 6 | `remove_long(48)` | Erst nach dem Splitten, sonst faellt das Kompositum weg, bevor es zerlegt werden kann. Der eingebaute Analyzer `default` von Tantivy nutzt `RemoveLongFilter::limit(40)`, was viele deutsche Komposita stillschweigend verschluckt [VERIFIED: `tantivy/src/tokenizer/tokenizer_manager.rs`] |
| 7 | `stemmer("german")` | Zuletzt; ein gestemmtes Kompositum findet keine Woerterbucheintraege mehr |

**Gemessenes Verhalten** (lokal, `tantivy==0.26.0`, Wortliste mit Fugenformen):

| Eingabe | Tokens | Bewertung |
|---|---|---|
| `Grundstuecksverkehrsgenehmigung` (mit Umlaut) | `['grundstuck', 'verkehr', 'genehm']` | CONTEXT-Testfall erfuellt: ueber "Genehmigung" auffindbar |
| `Dampfschifffahrt` | `['dampf', 'schiff', 'fahrt']` | Splitter arbeitet, Original wird ersetzt |
| `Haus` / `Haeuser` | `haus` / `haus` | Nominalflexion sauber |
| `Vertrag` / `Vertraege` | `vertrag` / `vertrag` | dito |
| `Strasse` / `Strasse mit Eszett` | `strass` / `strass` | Eszett normalisiert |
| `Mueller mit Umlaut` / `Muller` / `Mueller ausgeschrieben` | `mull` / `mull` / `muell` | **Luecke:** die ausgeschriebene Form trifft nicht |
| `suchen` / `Suche` / `suchte` / `gesucht` | `such` / `such` / `sucht` / `gesucht` | **Luecke:** Praeteritum und Partizip werden nicht vereinheitlicht |
| `Information` | `information` | Kein Fehlsplit, solange die Wortliste keine zu kurzen Bausteine enthaelt |

**Umgang mit den zwei Luecken:**

- *ue/oe/ae gegen Umlaut:* nicht im Analyzer loesbar, weil `ascii_fold` Umlaute zu einem Buchstaben faltet und die ausgeschriebene Form zwei bleibt. Loesung auf der **Query**-Seite: aus einem Suchbegriff, der `ue`, `oe`, `ae` oder `ss` enthaelt, zusaetzlich die Umlautvariante erzeugen und beide Varianten mit `Occur.Should` verodern. Das ist ein Dutzend Zeilen, kostet keinen Indexplatz und ist auf Anfragen begrenzt, wo eine gelegentliche Falschvariante ("neue" wird zu "neu-mit-Umlaut") nur einen zusaetzlichen, meist leeren Zweig kostet.
- *Verbformen:* nicht loesbar, ohne den Stemmer zu ersetzen. Der Testfall aus CONTEXT.md ist gegen "Suche/suchen" zu fuehren (funktioniert) und die Grenze bei Praeteritum und Partizip zu dokumentieren. Diese Entscheidung braucht eine kurze Bestaetigung beim Planen, weil sie ein woertlich formuliertes Abnahmekriterium beruehrt.

### Anti-Patterns to Avoid

- **Tokenizer nach dem Oeffnen nicht registrieren.** Gemessen: `Index.open(path)` gefolgt von `parse_query` wirft `ValueError: The tokenizer '"de_findling"' for the field '"body"' is unknown`. Das Schema speichert nur den **Namen** des Analyzers, nie den Analyzer. Deshalb: eine Funktion `open_index()`, die oeffnet und registriert, und nirgendwo sonst ein `Index(...)` oder `Index.open(...)`.
- **`Document(file_id=42, ...)` mit Schluesselwortargumenten fuer numerische Felder.** Gemessen: der Wert wird als I64 abgelegt, das Schemafeld ist U64, und beim `commit()` **panickt** ein Rust-Thread (`Input type forbidden. This column has been forced to type U64, received I64(42)`), was in Python als `ValueError: An error occurred in a thread` ankommt, also erst beim Commit und ohne Bezug zum verursachenden Dokument. Immer `doc.add_unsigned(...)` bzw. `Document.from_dict(payload, schema)` verwenden.
- **`highlighted()`-Bereiche als Zeichenpositionen weitergeben.** Gemessen: `[(4, 20)]` in Bytes gegenueber `[(4, 19)]` in Zeichen, das naive Slicen liefert sichtbar falschen Text.
- **Alle sichtbaren fileIds eines Nutzers materialisieren.** Der context-chat-Anti-Pattern aus ARCHITECTURE.md. Der Vorfilter fragt immer `WHERE uid = ? AND file_id IN (Kandidaten)`, nie umgekehrt.
- **Ein Commit pro Dokument.** Jeder Commit erzeugt ein Segment und einen fsync. Sammel-Commits von 50 bis 200 Dokumenten oder alle 30 Sekunden, je nachdem, was zuerst eintritt.
- **Reine Disjunktion bei mehreren Suchbegriffen.** Mit `conjunction_by_default=False` wird aus einem gesplitteten Kompositum eine Oder-Verknuepfung von drei Allerweltsteilen. Gemessen wurde das Gegenteil mit `conjunction_by_default=True`, dort trifft "Kuendigung" genau das Dokument mit "Kuendigungsfrist".
- **`parse_query` auf rohe Nutzereingabe.** Ein einzelnes `:` oder eine offene Klammer wirft. `parse_query_lenient` liefert Query plus Fehlerliste und ist der richtige Einstieg fuer Text aus einer Suchleiste.
- **Zweiter `IndexWriter`.** Tantivy laesst pro Verzeichnis genau einen zu, der zweite bekommt `LockBusy`.

---

## Antworten auf die offenen Research-Fragen

### Frage 1: Tantivy 0.26 Python konkret

**1a) Schema.** Empfehlung, mit Begruendung je Feld:

| Feld | Typ | Optionen | Zweck |
|---|---|---|---|
| `file_id` | unsigned | `stored=True, indexed=True, fast=True` | Primaerschluessel, Ziel von `delete_documents`, Rueckgabewert der Suche |
| `storage_id` | unsigned | `stored=True, indexed=True, fast=True` | Optionaler Selektivitaetsfilter (Phase 5), Diagnose |
| `name_de` / `name_en` | text | `stored=False, tokenizer_name=de/en` | Dateiname als eigenes Feld, damit `title-only` und Feldgewichte funktionieren |
| `path` | text | `stored=True, tokenizer_name="raw"` | Anzeige und Diagnose, nicht durchsuchbar (Pfade sind keine Suchbegriffe) |
| `body_de` | text | `stored=True, tokenizer_name="de_findling"` | Inhalt; die **einzige** gespeicherte Textkopie, Quelle fuer den SnippetGenerator |
| `body_en` | text | `stored=False, tokenizer_name="en_findling"` | Derselbe Text, englische Pipeline; nicht gespeichert, weil `body_de` ihn schon haelt |
| `ext` | text | `stored=True, tokenizer_name="raw"` | Dateityp-Filter, gemessen funktionierend als `ext:pdf` |
| `mtime` | integer | `stored=True, indexed=True, fast=True` | Sortierung und die spaeteren Filter `since`/`until` |

Doppelfeld statt Spracherkennung, weil Spracherkennung eine Abhaengigkeit und eine Fehlerquelle mehr ist und bei gemischten Dokumenten strukturell falsch liegt. Der Preis ist Indexgroesse; `FINDLING_LANGS` schaltet `body_en` ab.

**1b) Tokenizer-Registrierung.** `index.register_tokenizer(name, analyzer)` ist eine Laufzeiteigenschaft der Index-Instanz, nicht Teil der persistierten Metadaten. Sowohl nach `Index(schema, path=...)` als auch nach `Index.open(path)` muss registriert werden, sonst schlaegt bereits das Parsen einer Query fehl (gemessene Fehlermeldung siehe Anti-Patterns). Der Analyzer ist ueber einen `Arc<RwLock<HashMap>>` an den Index gebunden, das Registrieren nach dem Erzeugen des Readers ist also unproblematisch.

**1c) SnippetGenerator.** `SnippetGenerator.create(searcher, query, schema, field_name)`, dann `set_max_num_chars(n)` (Vorschlag 200 statt der Vorgabe 100, damit ein deutscher Satz hineinpasst), dann `snippet_from_doc(doc)`. Der Generator liest den Feldwert **aus dem uebergebenen Dokument**, nicht aus dem Index; ein Dokument aus `searcher.doc(address)` ist der bequemste Weg, ein selbst gebautes `Document` mit dem Text waere ebenso moeglich. `Snippet.fragment()` liefert den Klartext, `Snippet.highlighted()` eine Liste von `Range` mit `start`/`end` als **Bytepositionen** in diesem Fragment [VERIFIED: `tantivy-py/src/snippet.rs`, Kommentar "the byte ranges within that fragment", plus lokale Messung]. `to_html()` existiert und ist fuer uns verboten, weil die Subline Text rendert.

Zwei Details aus der Messung: die Bereiche koennen sich **wiederholen und ueberlappen**, weil alle Teiltoken eines gesplitteten Kompositums die Offsets des Originalworts erben. Vor dem Versenden zusammenfassen. Und die Hervorhebung deckt bei Komposita das ganze Wort ab, was fuer die Anzeige das gewuenschte Verhalten ist.

**1d) Query-Parser.** `index.parse_query(text, default_field_names, field_boosts, conjunction_by_default, allow_regexes)`. Gemessen an einem echten Index:

| Eingabe | Ergebnis | Anmerkung |
|---|---|---|
| `"drei Monate"` | Phrasentreffer | Anfuehrungszeichen funktionieren wie erwartet |
| `+frist -notiz` | Muss/Darf-nicht korrekt | `+`/`-` funktionieren |
| `ext:pdf` | Feldtreffer | Feldsyntax funktioniert, Feld mit `raw`-Tokenizer |
| `Kuendigung` (mit Umlaut) | trifft das Dokument mit "Kuendigungsfrist" | nur mit Fugenform in der Wortliste |

Empfehlungen: `conjunction_by_default=True`, `allow_regexes=False` (eine Regex-Query vom Nutzer ist ein Denial-of-Service), `field_boosts={"name_de": 3.0, "name_en": 3.0, "body_de": 1.0, "body_en": 1.0}` als Startwert, und `parse_query_lenient` fuer Nutzereingaben, dessen Fehlerliste ins Debug-Log geht.

Abbildung von SRCH-03 nach aussen: Nextclouds eingebauter Filter `title-only` (Typ bool, `IFilter::BUILTIN_TITLE_ONLY`) ist genau "Dateiname statt Inhalt" und kostet uns nur `getSupportedFilters()` in einem `IFilteringProvider` [VERIFIED: `lib/private/Search/SearchComposer.php`, Liste der `commonFilters`]. Fuer den Dateityp gibt es keinen eingebauten Filter; er reist als Praefix `type:pdf` in der Suchzeile und wird in der ExApp in eine `Occur.Must`-Termquery auf `ext` uebersetzt. Achtung: laut Interfacedoku wird ein Provider **uebergangen**, wenn ein Client einen Filter sendet, den `getSupportedFilters()` nicht nennt.

**1e) Reader- und Reload-Semantik.** `Index.config_reader(reload_policy="commit")` ist die Vorgabe von tantivy-py (`OnCommitWithDelay`). Der Reader sieht neue Commits also von selbst, aber mit Verzoegerung. Fuer deterministische Tests nach einem Commit `index.reload()` aufrufen. Mehrere Reader sind unkritisch (mmap, kein Lock), genau ein Writer ist Pflicht.

**1f) Persistenz und voller Datentraeger.** Der Index ist ein Verzeichnis unter `$APP_PERSISTENT_STORAGE/index/`. Bei vollem Datentraeger schlaegt der `commit()` mit einem IO-Fehler fehl; der Index bleibt auf dem Stand des letzten erfolgreichen Commits, weil `meta.json` erst danach ersetzt wird. Verlangt wird trotzdem eine aktive Wache: vor jedem Sammel-Commit `shutil.disk_usage()` pruefen und unterhalb einer Schwelle (Vorschlag 500 MB oder 5 Prozent) in den Zustand `paused_low_disk` gehen, statt in den Fehler zu laufen. Die Suche bleibt dabei lesend verfuegbar. Nach einem Absturz raeumt `writer.garbage_collect_files()` verwaiste Segmentdateien auf.

### Frage 2: Deutsche Kompositawortliste

**Quelle:** Debian-Binaerpaket `wngerman` aus dem Quellpaket `igerman98` (20161207-15 in trixie). Es liefert `/usr/share/dict/ngerman`, eine Wortliste in neuer Rechtschreibung, ein Wort pro Zeile, 4,6 MB installiert, 676 kB Download, `Architecture: all` und damit auf amd64 und arm64 identisch [VERIFIED: sources.debian.org `debian/control`, packages.debian.org Dateiliste und Groessenangabe].

**Lizenz:** GPL-2+ (Copyright Bjoern Jacke, Upstream j3e.de) [VERIFIED: `debian/copyright` des Quellpakets]. "or later" macht sie mit AGPL-3.0 vertraeglich. Pflichten: Lizenztext und Herkunftsangabe mit ins Image, Nennung in der Store-Beschreibung und in `docs/`, und weil abgeleitete Daten weitergegeben werden, das Aufbereitungsskript im Repo lassen.

**Warum die Rohliste allein nicht reicht** (empirisch belegt): ohne Fugenformen splittet der Filter nicht. Gemessen mit dem Woerterbuch `["kundigung", "frist"]` bleibt "Kuendigungsfrist" ein Token und ist ueber "Frist" nicht findbar; mit `["kundigungs", "frist"]` wird es zerlegt und beide Suchen treffen. Dasselbe Bild bei "Quartalsende".

**Aufbereitungsrezept (Build-Stage, Ergebnis ist ein Textartefakt im Image):**

1. `/usr/share/dict/ngerman` zeilenweise lesen, UTF-8.
2. Nur Eintraege behalten, die **gross** beginnen. Das sind im Deutschen im Wesentlichen die Substantive, und Komposita bestehen aus Substantiven. Damit fallen Verbformen, Adverbien und Partikeln weg, die die haesslichen Fehlsplits verursachen.
3. Kleinschreiben und dieselbe ASCII-Faltung anwenden, die der Analyzer an Position 4 macht (Umlaut zu Grundbuchstabe, Eszett zu ss). Reihenfolge und Ergebnis muessen exakt zur Filterkette passen, sonst trifft das Woerterbuch nie.
4. Alles mit weniger als 4 Zeichen und alles mit Nicht-Buchstaben verwerfen. Die Mindestlaenge ist der Schutz gegen Fehlsplits wie "in" plus "formation"; gemessen bleibt "Information" mit dieser Regel ungeteilt.
5. Fugenformen ergaenzen: zu jedem Eintrag zusaetzlich `wort + "s"`, und fuer Eintraege auf `e` zusaetzlich `wort + "n"`. Das deckt die beiden haeufigsten Fugenelemente ab.
6. Deduplizieren, sortieren, als eine Datei je Zeile ablegen, Anzahl und SHA-256 in die Build-Ausgabe schreiben. Der Hash gehoert als `meta.wordlist_hash` in die SQLite-Metatabelle: aendert er sich, aendert sich die Tokenisierung, und das erzwingt einen Reindex.

**Offene Groesse:** wie viele Eintraege nach Schritt 6 uebrig bleiben und wie viel Speicher der daraus gebaute Aho-Corasick-Automat kostet, ist **nicht gemessen** (die Rohliste liegt nicht auf dieser Maschine). Die Groessenordnung ist ein hoher fuenfstelliger bis niedriger sechsstelliger Eintragsbestand. `SplitCompoundWords::from_dictionary` baut daraus einen Automaten mit `MatchKind::LeftmostLongest` [VERIFIED: tantivy 0.26.0 Quellcode]. Der erste Plan-Task in dieser Spur ist deshalb eine **Messung**: Eintragszahl, RSS-Zuwachs beim Bauen des Analyzers, Analysezeit fuer 1 MB Text. Ergebnis entscheidet ueber die endgueltige Mindestlaenge (4 oder 5) und darueber, ob eine Haeufigkeitsgrenze noetig wird.

**Abschaltbarkeit (verlangt von CONTEXT):** `FINDLING_SPLIT_COMPOUND=on|off` als Umgebungsvariable in der `info.xml`. Bei `off` faellt Filterposition 5 weg, `ANALYZER_VERSION` aendert sich mit, und der Index muss neu gebaut werden. Damit ist der Notausgang vorhanden, falls die Messung schlecht ausfaellt, ohne dass jemand Code aendern muss.

**Fallback, falls die Liste unbrauchbar ist:** kein ngram-Feld und keine Regex-Suche. Beides bricht das Speicher- oder Latenzbudget. Der ehrliche Fallback ist die dokumentierte Grenze plus der Hinweis in der Store-Beschreibung, dass Komposita ueber ihre Bestandteile gefunden werden, sofern sie zerlegbar sind.

### Frage 3: Pull-Queue, Erstindex-Anstoss und Mount-Enumeration

**Tabellenschema (Migration in der PHP-App):**

```php
$table = $schema->createTable('findling_queue');
$table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
$table->addColumn('file_id', Types::BIGINT, ['notnull' => true]);
$table->addColumn('storage_id', Types::BIGINT, ['notnull' => true]);
$table->addColumn('root_id', Types::BIGINT, ['notnull' => true]);
$table->addColumn('update', Types::BOOLEAN, ['notnull' => true, 'default' => false]);
$table->addColumn('locked_at', Types::DATETIME, ['notnull' => false]);
$table->setPrimaryKey(['id']);
$table->addUniqueIndex(['file_id'], 'findling_q_fileid');   // Deduplizierung
$table->addIndex(['locked_at'], 'findling_q_locked');
```

Der Tabellenname bleibt unter der Nextcloud-Grenze von 27 Zeichen inklusive `oc_`-Praefix. Der eindeutige Index auf `file_id` ist der Deduplizierungsmechanismus: ein zweites Einreihen derselben Datei ist ein abgefangener Konflikt, kein zweiter Job.

**Endpunkte** (alle `#[ExAppRequired]`, alle in einem `OCSController`):

| Route | Verb | Zweck |
|---|---|---|
| `/queues/documents` | GET | `n` und `max_bytes`, sperrt und liefert Metadaten inklusive `userIds` |
| `/queues/documents` | DELETE | Quittieren, Liste von Zeilen-IDs |
| `/queues/documents/unlock` | POST | Nack: Sperren sofort loesen (SIGTERM-Pfad) |
| `/queues/documents/stats` | GET | Zaehler fuer die Statusanzeige (Phase 4 verbraucht sie, Phase 2 erzeugt sie) |

**Anstoss des Erstindex (Claude's Discretion, Empfehlung Auto-Start):** ein `IRepairStep`, in `info.xml` unter `<repair-steps><install>` registriert, der beim ersten Install einen `SchedulerJob` in die Jobliste legt und sich das per App-Config merkt, damit ein Deaktivieren und wieder Aktivieren nicht alles neu einreiht. Genau dieses Muster ist in `context_chat/lib/Repair/AppInstallStep.php` gelesen worden. Zusaetzlich ein `occ findling:index --restart` als Notfallhebel fuer Support und fuer die CI, denn ohne Kommandozeile ist ein Wiederaufbau nur ueber Deinstallation erreichbar.

**Wichtig fuer die Erwartung:** Hintergrundjobs brauchen einen laufenden Cron. Bei der Standardeinstellung "AJAX" laufen sie nur, wenn jemand die Weboberflaeche benutzt. Der Erstindex tropft dann vor sich hin. Das gehoert in die Store-Beschreibung und in die Statusseite, nicht in eine Fussnote.

**Mount-Enumeration:** `IFileAccess::getDistinctMounts(MOUNT_PROVIDERS, true)` liefert `{storage_id, root_id, overridden_root}`. Team Folders erkennt man an `OCA\GroupFolders\Mount\MountProvider`, External Storage an `OCA\Files_External\Config\ConfigAdapter`; letzteres wird schlicht nicht in die Liste aufgenommen (CONTEXT: default aus). Ob die Groupfolders-App installiert ist, muss nicht geprueft werden: ist sie es nicht, gibt es keine Mounts dieser Klasse.

**Dateien im Mount:** `getByAncestorInStorage($storageId, $overriddenRoot, $lastFileId, 2000, $mimeTypeIds, false, true)`. Die beiden Booleans bedeuten "Ende-zu-Ende-verschluesselte Dateien nicht mitnehmen" (aus denen bekaeme man ohnehin nur Chiffrat) und "serverseitig verschluesselte mitnehmen" (die liefert das Gateway entschluesselt).

### Frage 4: ACL-Befuellung und Uebertragungsformat

**Effiziente Befuellung:** siehe Pattern 3. Pro Crawl-Batch einmal `IUserMountCache::getMountsForStorageId($storageId)`, daraus je Mount `(uid, mountRootPath)` bilden (der Root-Pfad kommt aus `ICachedMountInfo` bzw. einer einzelnen Filecache-Abfrage je Mount), und dann fuer jede Datei alle UIDs sammeln, deren Root-Pfad ein Praefix des Dateipfads ist. Das ist exakt die Semantik, die `UserMountCache::getMountsForFileId()` sonst pro Datei in SQL nachbaut [VERIFIED: `lib/private/Files/Config/UserMountCache.php`, Substring-Bedingung auf `f.path`].

**Warum nicht `IShareManager::getAccessList()`:** die Methode braucht ein `Node`-Objekt, arbeitet rekursiv ueber Elternordner und kennt nur Freigaben. Gruppenordner und externe Mounts fehlen darin. Fuer einen Crawl ueber Zehntausende Dateien ist sie ausserdem viel zu teuer [VERIFIED: `lib/public/Share/IManager.php`, Signatur und Rueckgabeform].

**Uebertragungsformat:** die UIDs reisen im Queue-Eintrag mit.

```json
{
  "files": {
    "8123": {"fileId": 4711, "storageId": 3, "rootId": 12, "userIds": ["alice", "bob"],
             "path": "Documents/vertrag.pdf", "title": "vertrag.pdf",
             "mime": "application/pdf", "size": 184320, "mtime": 1755200000,
             "update": false}
  }
}
```

Der Schluessel der Map ist die Zeilen-ID der Queue, weil genau die beim Quittieren zurueckgeht. `content` fehlt bewusst: Metadaten und Bytes reisen getrennt, damit die Queue-Antwort klein bleibt und der teure Abruf erst passiert, wenn der Worker frei ist.

**Schreibseite in der ExApp:** die ACL ist **deklarativ**. Beim Indexieren `DELETE FROM acl WHERE file_id=?` gefolgt von `INSERT`. Nie inkrementell, denn ein verlorenes Delta ist dauerhaft falsch, waehrend ein Sollzustand sich bei der naechsten Zustellung selbst heilt.

### Frage 5: SQLite-Layout in der ExApp

Eine Datei, `$APP_PERSISTENT_STORAGE/state.db`, daneben das Tantivy-Verzeichnis. Eine Datei, weil CONTEXT es so setzt und weil Zustand und ACL in derselben Transaktion geschrieben werden sollen.

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous  = NORMAL;
PRAGMA busy_timeout = 10000;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);   -- schema_version, index_version, analyzer_version, wordlist_hash,
     -- tantivy_version, instance_id, created_at

CREATE TABLE IF NOT EXISTS files (
    file_id       INTEGER PRIMARY KEY,          -- Nextcloud fileid, global eindeutig
    storage_id    INTEGER NOT NULL,
    root_id       INTEGER NOT NULL,
    path          TEXT    NOT NULL,
    mime          TEXT    NOT NULL,
    size          INTEGER NOT NULL,
    mtime         INTEGER NOT NULL,
    etag          TEXT,                         -- Phase 3 (Reconcile) fuellt es
    content_hash  TEXT,                         -- ueberspringt unveraenderte Inhalte
    state         TEXT    NOT NULL,             -- pending|claimed|done|failed|skipped
    reason        TEXT,                         -- Fehlerklasse, nie ein Dateiname
    attempts      INTEGER NOT NULL DEFAULT 0,
    claimed_at    INTEGER,
    indexed_at    INTEGER,
    index_version INTEGER NOT NULL DEFAULT 0,
    deleted_at    INTEGER                       -- Phase 3 (Tombstone), bleibt jetzt NULL
);
CREATE INDEX IF NOT EXISTS files_state    ON files(state);
CREATE INDEX IF NOT EXISTS files_storage  ON files(storage_id);

CREATE TABLE IF NOT EXISTS acl (
    uid     TEXT    NOT NULL,
    file_id INTEGER NOT NULL,
    PRIMARY KEY (uid, file_id)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS acl_file ON acl(file_id);   -- fuer den Loeschpfad

CREATE TABLE IF NOT EXISTS mounts (
    storage_id     INTEGER PRIMARY KEY,
    root_id        INTEGER NOT NULL,
    cursor_file_id INTEGER NOT NULL DEFAULT 0,   -- Spiegel, PHP fuehrt das Original
    files_seen     INTEGER NOT NULL DEFAULT 0,
    updated_at     INTEGER NOT NULL
);
```

**Warum `WITHOUT ROWID` bei `acl`:** die Tabelle besteht nur aus ihrem Schluessel. Ohne die versteckte Zeilennummer spart sie rund ein Drittel Platz und einen Indexsprung pro Suche. Das ist die Tabelle, die als erste gross wird.

**Anschlussfaehigkeit:** Phase 3 braucht `etag` und `deleted_at`, beide sind da. Phase 6 haengt eine Tabelle `chunks(chunk_id, file_id REFERENCES files(file_id) ON DELETE CASCADE, ...)` an; der Fremdschluessel funktioniert, weil `file_id` schon der Primaerschluessel ist. `index_version` und `analyzer_version` sind der Hebel, mit dem ein Upgrade gezielt Teilmengen auf `pending` zuruecksetzt, statt alles zu loeschen.

**WAL im Container-Volume:** das AppAPI-Volume ist ein normales Docker-Volume auf ext4, WAL funktioniert dort uneingeschraenkt. Zwei Vorbehalte gehoeren in den Code, nicht in die Doku: erstens setzt WAL Shared Memory (`-shm`) voraus, was auf manchen Netzwerkdateisystemen fehlschlaegt, also `PRAGMA journal_mode=WAL` auswerten und bei einem anderen Rueckgabewert eine Warnung loggen und weiterlaufen (`DELETE`-Journal ist langsamer, aber korrekt). Zweitens ist der lokale Entwicklungsfall auf **Windows**: `scripts/dev/register-exapp.sh` startet die ExApp als Hostprozess, `APP_PERSISTENT_STORAGE` liegt also auf NTFS. SQLite mit WAL kann das, Tantivy hat dort aber eine dokumentierte Schwaeche: memory-mapped Dateien lassen sich unter Windows nicht loeschen, weshalb die Segment-Aufraeumung Reste hinterlaesst ("deletion did not work. This typically happens on windows", Kommentar im Tantivy-Quellcode). Fuer lokale Proben ist das kosmetisch, fuer belastbare Aussagen zu Indexgroesse und Aufraeumung ist die CI oder ein Linux-Container zustaendig.

**Ein Schreiber:** alle Schreibzugriffe laufen ueber eine einzige Verbindung im Indexer-Thread. Der Suchpfad bekommt eine eigene Verbindung mit `PRAGMA query_only = 1`, damit ein Fehler im Suchcode strukturell nichts kaputtmachen kann.

### Frage 6: Extraktionspipeline

**Reihenfolge pro Datei:** Allowlist und Groesse pruefen (`skipped: unsupported_type` bzw. `skipped: too_large`, 50-MB-Cap) -> Bytes ueber `fetch_file_stream` in eine Temporaerdatei im Volume -> Format-Dispatcher -> Text kappen (Vorschlag 1 MB extrahierter Text, `truncated`-Vermerk) -> indexieren.

| Format | Aufruf | Fehlerklassen |
|---|---|---|
| PDF | zuerst `pypdf.PdfReader(path)` und `.is_encrypted` pruefen, dann `pypdfium2.PdfDocument(path)`, je Seite `page.get_textpage()` und `get_text_bounded()`, Seite und Textpage schliessen | `skipped: encrypted_pdf`, `failed: pdf_broken` (`PdfiumError`), `skipped: no_text_layer` (leerer Text, in Phase 3 der Einstieg in OCR) |
| DOCX | `python-docx`, Absaetze plus Tabellenzellen | `failed: zip_broken` (`BadZipFile`), `failed: ooxml_invalid` |
| PPTX | `python-pptx`, Shapes mit `has_text_frame` | wie DOCX |
| XLSX | `openpyxl.load_workbook(path, read_only=True, data_only=True)`, `iter_rows(values_only=True)`, harte Zellgrenze 200.000 | `skipped: too_many_cells`, `failed: zip_broken` |
| ODT/ODS/ODP | `zipfile` oeffnen, `content.xml` lesen, mit `lxml.etree` alle `text:p` und `text:h` einsammeln | `failed: zip_broken`, `failed: xml_invalid` (`XMLSyntaxError`) |
| HTML | `lxml.html.fromstring`, `script` und `style` entfernen, `text_content()` | `failed: html_invalid` |
| RTF | `striprtf.rtf_to_text(text, errors="ignore")` | `failed: rtf_invalid` |
| TXT/MD/CSV | `charset_normalizer.from_bytes(...).best()`, bei `None` UTF-8 mit `errors="replace"` | `failed: encoding_unknown` |

**Zeitbudget ohne Prozess-Zoo:** ein Timeout pro Datei ist noetig (eine kaputte XLSX kann in einer C-Schleife haengen), aber ein Prozesspool widerspricht IDX-08. Empfehlung: `signal.alarm` bzw. `signal.setitimer` im Indexer-Thread scheidet aus (Signale kommen nur im Hauptthread an). Stattdessen **ein** wiederverwendeter `concurrent.futures.ProcessPoolExecutor(max_workers=1)`, an den die Extraktion abgegeben wird, mit `future.result(timeout=...)`; laeuft er ab, wird der Kindprozess getoetet und der Pool neu erzeugt. Das ist ein einziger zusaetzlicher Prozess, kein Pool im Sinne von Parallelitaet, und es haelt die RAM-Spitze der Extraktion aus dem Hauptprozess heraus. Zeitgrenze als Startwert 60 Sekunden pro Datei, Fehlerklasse `failed: extract_timeout`.

**Nur-Lesen bleibt strukturell wahr:** die Temporaerdatei liegt in `$APP_PERSISTENT_STORAGE/tmp/`, wird im `finally` geloescht, und beim Start werden Reste des letzten Absturzes entfernt. Keine Bibliothek bekommt je einen Pfad in den Nextcloud-Speicher zu sehen, denn den gibt es im Container nicht.

### Frage 7: E2E-Erweiterung der CI

Das Phase-1-Muster traegt, es wird nur ergaenzt. Was schon da ist und wiederverwendet wird: Server-Checkout, `maintenance:install` mit SQLite, `composer run serve`, ExApp als nativer Prozess, `app_api:daemon:register` mit `manual_install`, `app_api:app:register --wait-finish`, Korpus per `cp -r` nach `data/<user>/files/` plus `occ files:scan --all`, fileids per WebDAV-PROPFIND.

**Neu und konkret:**

1. **Dateien anlegen:** unveraendert `cp -r` plus `occ files:scan --all`. Ein WebDAV-Upload waere realistischer, kostet aber pro Datei einen Request und bringt fuer die Indexfrage nichts. Der erweiterte Korpus braucht deutsche Inhalte mit den Testwoertern.
2. **Crawl deterministisch anstossen:** nicht auf Cron warten. `occ background-job:worker 'OCA\Findling\BackgroundJobs\SchedulerJob' --once` und danach `occ background-job:worker 'OCA\Findling\BackgroundJobs\StorageCrawlJob' --once` [VERIFIED: `core/Command/Background/JobWorker.php`, Optionen `--once`, `--interval`, `--stop_after`]. Fuer Einzelfaelle gibt es `occ background-job:execute <id> --force-execute`, das den geplanten Zeitpunkt ignoriert; genau das braucht man, weil `scheduleAfter` sonst fuenf Minuten Wartezeit setzt.
3. **Auf Fertigstellung warten:** nicht schlafen, sondern pollen. `GET /queues/documents/stats` (offene Zeilen) und der `/status`-Endpunkt der ExApp (`done`, `failed`, `skipped`, `pending`) liefern beide Zahlen; die Schleife endet, wenn die Queue leer und `pending` null ist, mit einem harten Zeitlimit und dem Ausdruck beider Zaehler beim Fehlschlag.
4. **Deutsche Suchen asserten:** ueber die normale OCS-Suchroute, wie in Phase 1, mit `jq -e`. Mindestens: Kompositum ueber ein Teilwort, Umlautvariante, Nominalflexion, Phrase, Ausschluss mit `-`, Dateityp, und ein Negativfall (ein zweiter Nutzer ohne Zugriff findet nichts).
5. **Kill-Resume nachstellen:** in der CI laeuft die ExApp als Prozess, nicht als Container. `kill -9 $(cat exapp.pid)` ist semantisch dasselbe wie `docker kill` (SIGKILL, keine Aufraeumarbeit). Ablauf: Crawl starten, warten bis `done > 0` und `pending > 0`, SIGKILL, Prozess neu starten, warten bis `pending == 0`, danach pruefen, dass die Summe der Zustaende der Dateizahl entspricht und **kein** Dokument doppelt im Index liegt (Zaehlabfrage auf `file_id`). Zusaetzlich der eigentliche Beweis: die vor dem Kill erreichte `done`-Zahl darf nach dem Neustart nicht kleiner sein.
6. **Zweiter Datenbankdialekt:** Phase 2 fuehrt die erste eigene Tabelle ein, und `IQueryBuilder`-Fehler sind dialektabhaengig. Ein zweiter Matrixeintrag mit MariaDB oder Postgres gehoert deshalb in diese Phase, mindestens fuer den Job, der die Migration und den Crawl ausfuehrt.

---

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---|---|---|---|
| Deutsches Stemming | Eigene Suffixregeln | `Filter.stemmer("german")` | Snowball ist der Referenzalgorithmus; eigene Regeln sind schlechter und nie fertig |
| Stoppwoerter | Eigene Liste | `Filter.stopword("german")` | 230 gepflegte Eintraege, im Analyzer an der richtigen Stelle |
| Umlaut-Normalisierung | `str.translate` vor dem Indexieren | `Filter.ascii_fold()` | Muss auf Query- und Indexseite identisch sein; im Analyzer ist es das per Konstruktion |
| Kompositazerlegung | Eigener rekursiver Zerleger | `Filter.split_compound(liste)` | Aho-Corasick in Rust gegen eine Python-Rekursion pro Token; der Unterschied ist Groessenordnungen |
| Snippet-Fenster | Eigene Suche nach Trefferpositionen im Text | `SnippetGenerator` | Kennt die tatsaechlich getroffenen Terme aus der Query inklusive Analyzer, nicht nur die Eingabezeichenkette |
| Zeilen-Locks in der Queue | `SELECT ... FOR UPDATE` oder Anwendungssperren | Bedingtes `UPDATE` mit Zeitstempel, Rueckgabewert auswerten | Dialektfrei, in context_chat im Produktivbetrieb belegt |
| "Wer darf diese Datei sehen" | Rekonstruktion aus der Share-API | `IUserMountCache` | Die Share-API kennt Gruppenordner und externe Mounts nicht |
| Datei-Enumeration je Mount | Eigenes SQL gegen `oc_filecache` | `IFileAccess::getByAncestorInStorage` | @since 32.0.0, also verfuegbar; das eigene SQL waere Pflege ohne Gegenwert |
| Volltext-Persistenz | Eigenes Format oder JSON-Dateien | Tantivy-Verzeichnis | Atomare Commits, mmap, Segment-GC sind gebaut und getestet |
| Encoding-Erkennung | Heuristik auf Basis von Byte-Haeufigkeiten | `charset-normalizer` | Deutsche Altbestaende sind cp1252 und latin-1, das erkennt man nicht nebenbei |

**Key insight:** Fast alles, was in dieser Phase nach eigener Arbeit aussieht, ist in Wahrheit Verdrahtung. Der einzige echte Eigenbau ist die Aufbereitung der Wortliste, und der ist genau deshalb der Ort, an dem eine Messung vor der Entscheidung stehen muss.

---

## Common Pitfalls

### Pitfall 1: Der Kompositasplitter splittet nicht, und niemand merkt es

**Was schiefgeht:** Die Wortliste ist eingebunden, der Index ist gebaut, die Suche nach "Genehmigung" findet die Datei mit "Grundstuecksverkehrsgenehmigung" trotzdem nicht.
**Warum:** Der Filter splittet nur bei **vollstaendiger** Zerlegung in aufeinanderfolgende Woerterbuchtreffer. Fehlt eine Fugenform ("kundigungs" gegenueber "kundigung"), bleibt das ganze Wort ungeteilt. Gemessen und in beide Richtungen belegt.
**Vermeiden:** Fugenformen im Aufbereitungsschritt erzeugen. Und einen Test, der nicht die Suche, sondern direkt `TextAnalyzer.analyze("Grundstuecksverkehrsgenehmigung")` prueft. Der Analyzer-Test braucht keinen Index und laeuft in Millisekunden.
**Warnzeichen:** Suchen nach Teilwoertern liefern konstant null Treffer, waehrend die Suche nach dem ganzen Wort funktioniert.

### Pitfall 2: Byte-Offsets in Zeichen-Offsets umdeuten

**Was schiefgeht:** Die Hervorhebung sitzt einige Zeichen zu weit rechts, und zwar genau um die Anzahl der Umlaute vor der Fundstelle.
**Warum:** `Snippet.highlighted()` gibt Bytepositionen im UTF-8-Fragment zurueck.
**Vermeiden:** Umrechnen (Code-Beispiel 4) und die Bereiche danach deduplizieren und verschmelzen, weil gesplittete Komposita denselben Bereich mehrfach melden.
**Warnzeichen:** Der Fehler ist bei englischem Testtext unsichtbar. Der Test muss deutschen Text mit Umlaut **vor** der Fundstelle verwenden.

### Pitfall 3: Der lange Lock haelt den Neustart auf

**Was schiefgeht:** Nach `docker kill` und Neustart tut der Indexer scheinbar nichts, obwohl die Queue voll ist.
**Warum:** Die zuletzt geholten Zeilen sind gesperrt, und das Vorbild setzt den Timeout auf 24 Stunden.
**Vermeiden:** 15 Minuten Timeout, Nack-Endpunkt im SIGTERM-Pfad, und im Resume-Test explizit pruefen, dass innerhalb weniger Sekunden wieder Fortschritt entsteht.
**Warnzeichen:** `pending` steht still, `locked` ist gross, das Log zeigt leere Batches.

### Pitfall 4: Zustand vor dem Commit schreiben

**Was schiefgeht:** Nach einem Absturz gelten Dokumente als indexiert, sind aber nicht im Index. Die Suche findet sie nie wieder, und kein Zaehler faellt auf.
**Warum:** Der Tantivy-Commit ist der Zeitpunkt der Dauerhaftigkeit, alles davor ist Arbeitsspeicher.
**Vermeiden:** Reihenfolge aus Pattern 5 einhalten, sie ist die halbe Miete fuer IDX-02.
**Warnzeichen:** Der Deckungsgrad ist rechnerisch vollstaendig, aber Stichproben finden nichts.

### Pitfall 5: Zweite Sprache verdoppelt den Index unbemerkt

**Was schiefgeht:** Der Index ist deutlich groesser als erwartet, auf kleinen Instanzen faellt das auf.
**Warum:** `body_de` und `body_en` indexieren denselben Text zweimal.
**Vermeiden:** `body_en` nicht speichern (nur indexieren), `FINDLING_LANGS` als Schalter, und ab Phase 2 die Kennzahl "Bytes pro indexiertem Dokument" mitfuehren. Sie ist auch die Zahl, die der Admin in Phase 4 sehen will.
**Warnzeichen:** Indexgroesse waechst schneller als die Summe der extrahierten Textmengen.

### Pitfall 6: Fehlerzustaende bleiben in der Queue haengen

**Was schiefgeht:** Eine kaputte Datei wird geholt, schlaegt fehl, wird nicht quittiert, kommt nach dem Lock-Timeout zurueck, schlaegt wieder fehl. Der Erstindex endet nie.
**Warum:** `failed` fuehlt sich an wie "nicht fertig", ist aber ein Endzustand.
**Vermeiden:** `failed` und `skipped` werden in SQLite festgehalten **und** in PHP quittiert. `attempts` zaehlt, drei gleiche Fehler bedeuten endgueltig `failed`. Nur wiederholbare Fehler (Netz, 503 vom Gateway) fuehren zum Nack.
**Warnzeichen:** Dieselbe `file_id` erscheint mehrfach im Log, `attempts` steigt ueber drei.

### Pitfall 7: Gate A schlaegt beim ersten Quittieren zu

**Was schiefgeht:** Der Ack-Aufruf ist ein `DELETE`, und `backend/tests/test_readonly_gate.py` haelt `OCS_WRITE_ALLOWLIST` in Phase 1 bewusst leer. Der erste Commit dieser Phase macht das Gate rot.
**Warum:** So ist es entworfen: jeder Schreibweg nach Nextcloud soll eine bewusste Entscheidung sein.
**Vermeiden:** Die Allowlist um die Queue-Pfade erweitern (`/ocs/v2.php/apps/findling/queues/documents` und `.../unlock`), mit einer Begruendung im Kommentar: geschrieben wird ausschliesslich in unsere eigene Queue-Tabelle, nie in Nutzerdateien. Zusaetzlich beachten, dass `FORBIDDEN_IDENTIFIERS` das Wort `delete` enthaelt und `REMOTE_RECEIVERS` die Empfaengernamen `nc`, `ocs`, `_session`, `session`, `adapter` fuehrt: der Tantivy-Writer darf im Code nicht so heissen.
**Warnzeichen:** Rotes Gate A mit einer Meldung ueber einen nicht erlaubten OCS-Schreibpfad, direkt nach dem ersten Queue-Commit.

### Pitfall 8: Analyzer aendern, ohne den Index zu invalidieren

**Was schiefgeht:** Nach einem Update findet die Suche alte Dokumente nicht mehr, neue schon. Niemand kann es erklaeren.
**Warum:** Tokenisierung ist Teil der Daten. Aendert sich die Wortliste, die Filterreihenfolge oder die Tantivy-Version, passen alte Terme nicht mehr zu neuen Anfragen.
**Vermeiden:** `analyzer_version`, `wordlist_hash`, `index_version` und `tantivy_version` in `meta` fuehren, beim Start vergleichen und bei Abweichung entweder gezielt auf `pending` setzen oder den Index verwerfen und neu aufbauen, sichtbar im Status. Das ist die Gegenmassnahme zu fulltextsearch #857, wo ein "Reset" nur halb zuruecksetzte.
**Warnzeichen:** Trefferzahlen aendern sich nach einem Release ohne Reindex.

---

## Code Examples

### 1. Index oeffnen: die einzige erlaubte Form

```python
# index/schema.py
from tantivy import Index, SchemaBuilder

TOKENIZER_DE = "de_findling"
TOKENIZER_EN = "en_findling"

def build_schema() -> Schema:
    builder = SchemaBuilder()
    builder.add_unsigned_field("file_id", stored=True, indexed=True, fast=True)
    builder.add_unsigned_field("storage_id", stored=True, indexed=True, fast=True)
    builder.add_text_field("name_de", stored=False, tokenizer_name=TOKENIZER_DE)
    builder.add_text_field("name_en", stored=False, tokenizer_name=TOKENIZER_EN)
    builder.add_text_field("path", stored=True, tokenizer_name="raw")
    builder.add_text_field("body_de", stored=True, tokenizer_name=TOKENIZER_DE)
    builder.add_text_field("body_en", stored=False, tokenizer_name=TOKENIZER_EN)
    builder.add_text_field("ext", stored=True, tokenizer_name="raw")
    builder.add_integer_field("mtime", stored=True, indexed=True, fast=True)
    return builder.build()

def open_index(path: str, constituents: list[str]) -> Index:
    """The only place that opens an index. Registering the analyzers is part of
    opening: the schema stores the tokenizer NAME, never the tokenizer, and a
    query against an unregistered name raises before it reaches the index."""
    schema = build_schema()
    index = Index(schema, path=path)          # opens when it exists, creates otherwise
    index.register_tokenizer(TOKENIZER_DE, german_analyzer(constituents))
    index.register_tokenizer(TOKENIZER_EN, english_analyzer())
    return index
```

### 2. Dokument schreiben, ohne die Typfalle

```python
# WRONG: keyword arguments infer I64 and the Rust thread panics at commit time
# doc = Document(file_id=4711, body_de=text)

doc = Document()
doc.add_unsigned("file_id", file_id)          # matches add_unsigned_field
doc.add_unsigned("storage_id", storage_id)
doc.add_text("name_de", name)
doc.add_text("name_en", name)
doc.add_text("path", path)
doc.add_text("body_de", body)
doc.add_text("body_en", body)
doc.add_text("ext", extension)
doc.add_integer("mtime", mtime)

writer.delete_documents("file_id", file_id)   # upsert: delete then add
writer.add_document(doc)
```

### 3. Sammel-Commit in der richtigen Reihenfolge

```python
def flush(writer, state, batch) -> None:
    writer.commit()                    # 1. durable in tantivy
    with state.transaction():          # 2. only now the state says done
        for item in batch:
            state.mark(item.file_id, item.outcome, item.reason)
    queue.ack([item.row_id for item in batch])   # 3. only now the queue lets go
```

### 4. Snippet mit korrekten Zeichenpositionen

```python
def snippet_for(searcher, query, schema, doc) -> tuple[str, list[tuple[int, int]]]:
    generator = SnippetGenerator.create(searcher, query, schema, "body_de")
    generator.set_max_num_chars(200)
    snippet = generator.snippet_from_doc(doc)
    fragment = snippet.fragment()
    raw = fragment.encode("utf-8")
    spans = sorted(
        # highlighted() returns BYTE ranges into the fragment. Measured on a
        # German sentence: bytes (4, 20) are characters (4, 19).
        {(len(raw[: r.start].decode("utf-8")), len(raw[: r.end].decode("utf-8")))
         for r in snippet.highlighted()}
    )
    merged: list[tuple[int, int]] = []
    for start, end in spans:           # compound parts inherit the same offsets
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return fragment, merged
```

### 5. Ueberfetch mit ACL-Vorfilter

```python
OVERFETCH = 8
MAX_ROUNDS = 3

def candidates(index, acl, uid: str, query, limit: int) -> list[Hit]:
    fetched = limit * OVERFETCH
    allowed: list[Hit] = []
    for _ in range(MAX_ROUNDS):
        hits = index.searcher().search(query, fetched).hits
        file_ids = [doc_file_id(h) for h in hits]
        # The filter always runs candidates -> permission, never the other way
        # around. Materialising every file a user may see is the anti pattern
        # that made context_chat batch around a parameter limit.
        visible = acl.filter_visible(uid, file_ids)
        allowed = [h for h in hits if doc_file_id(h) in visible]
        if len(allowed) >= limit or len(hits) < fetched:
            break
        fetched *= 2
    return allowed[:limit]
```

```sql
-- acl.filter_visible, chunked to stay below the SQLite parameter limit
SELECT file_id FROM acl WHERE uid = ? AND file_id IN (?, ?, ...);
```

### 6. Der PHP-Recheck, unveraendert aus Phase 1 abgeleitet

```php
$userFolder = $this->rootFolder->getUserFolder($user->getUID());
$entries = [];
foreach ($candidates as $candidate) {
    $node = $userFolder->getFirstNodeById($candidate['fileId']);
    if (!$node instanceof File) {
        continue;   // gone, unshared or never visible: no entry, no snippet
    }
    $entries[$candidate['fileId']] = $node;
}
// Only now, and only for the survivors, the snippets are requested.
$snippets = $this->exApp->snippets($user->getUID(), $term, array_keys($entries));
```

### 7. Crawl-Job gegen die 32er-API

```php
foreach ($this->fileAccess->getDistinctMounts(self::MOUNT_PROVIDERS, true) as $mount) {
    $this->jobList->add(StorageCrawlJob::class, [
        'storage_id'      => $mount['storage_id'],
        'root_id'         => $mount['root_id'],
        'overridden_root' => $mount['overridden_root'],
        'last_file_id'    => 0,
    ]);
}

// inside StorageCrawlJob::run
$mimeIds = array_map(fn (string $m): int => $this->mimeTypes->getId($m), self::ALLOWED_MIMETYPES);
foreach ($this->fileAccess->getByAncestorInStorage(
    $storageId, $overriddenRoot, $lastFileId, self::BATCH_SIZE, $mimeIds, false, true) as $entry) {
    $this->queue->enqueue($entry, $usersByMount);   // ACL comes from the mount list
    $lastSeen = $entry->getId();
}
```

### 8. Analyzer-Testfaelle ohne Index

```python
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Grundstuecksverkehrsgenehmigung", ["grundstuck", "verkehr", "genehm"]),
        ("Haeuser", ["haus"]),
        ("Vertraege", ["vertrag"]),
        ("fuer ueber das", []),
        ("Information", ["information"]),
    ],
)
def test_german_analyzer(text: str, expected: list[str]) -> None:
    # analyze() needs no index, so the German language promise is tested in
    # milliseconds instead of behind a full crawl.
    assert german_analyzer(TEST_WORDS).analyze(text) == expected
```

---

## State of the Art

| Frueher | Heute | Seit wann | Bedeutung fuer uns |
|---|---|---|---|
| Datei-Enumeration per handgeschriebenem SQL auf `oc_filecache` | `IFileAccess::getByAncestorInStorage` und `getDistinctMounts` | NC 32.0.0 | Der Kompatibilitaetszweig von context_chat entfaellt; wir schreiben kein eigenes Filecache-SQL |
| Snippets als HTML aus der Engine | Klartext plus Offsets | Phase-1-Befund zur Unified-Search-UI | `Snippet.to_html()` ist fuer uns tot |
| Suche als ein Aufruf mit fertigem Ergebnis | Kandidaten, Recheck, dann Snippets | COMP-04 und SRCH-02 | Zwei Aufrufe, dafuer keine Snippets ohne Rechtepruefung |
| `exAppRequestWithUserInit()` | `exAppRequest()` | AppAPI 3.0.0 | Unveraendert aus Phase 1 |
| Sync-API von nc_py_api | `AsyncNextcloudApp` | Entfaellt in 0.31.0 | Der Worker-Thread muss den Async-Client benutzen, nicht die alte Fassade |

**Ueberholt oder nicht uebernehmen:**
- Der FTS5-Entwurf aus `.planning/research/ARCHITECTURE.md` (ACL als SQL-Join in derselben Datei) ist durch die Tantivy-Entscheidung in STACK.md und CONTEXT.md ersetzt. Der ACL-Filter ist jetzt Ueberfetch plus Nachfassen, nicht ein Join. Die uebrigen Aussagen dieser Datei (Pull-Queue, Crawl pro Mount, Inhalts-Gateway) gelten unveraendert.
- `LOCK_TIMEOUT = 24h` aus context_chat nicht uebernehmen.
- `getMountsOld` und `getFilesInMountOld` aus context_chat nicht uebernehmen.

---

## Environment Availability

| Abhaengigkeit | Gebraucht von | Vorhanden | Version | Ausweichpfad |
|---|---|---|---|---|
| `uv` | jede Python-Aktion | ja | 0.11.7 | keiner noetig |
| Python 3.13 via uv | Backend | ja | ueber uv verwaltet | System-Python gilt als defekt |
| `tantivy` cp313 win_amd64 | lokale Analyzer- und Indexproben | ja, lokal ausgefuehrt | 0.26.0 | keiner noetig |
| Docker | Test-Nextcloud aus `scripts/dev/compose.yaml` | ja | 29.5.2 (desktop-linux) | keiner |
| PHP / composer / occ | PHP-Companion, Migration, Jobs | **nein** | - | Ausschliesslich CI; lokal nur ueber `docker compose exec app php occ` |
| `slopcheck` | Paketpruefung | ja | Scan lief, `9 OK` | - |
| Debian-Paket `wngerman` | Wortliste | nicht lokal, nur im Image-Build | igerman98 20161207-15 | keiner; der Build-Stage-Schritt ist die einzige Bezugsquelle |
| `jq`, `curl`, `git` | CI und lokale Proben | ja | - | - |

**Fehlend ohne Ausweichpfad:** keines.
**Fehlend mit Ausweichpfad:** PHP. Alles PHP-seitige (Migration, Jobs, Controller) wird ausschliesslich in der CI verifiziert; der Plan muss das als Verifikationsweg ausweisen, statt lokale Ausfuehrung anzunehmen. Lokale Proben laufen mit `FINDLING_PORT=8090`, weil 8080 von der parallelen MCP-Sitzung belegt ist.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Kategorie | Trifft zu | Standardkontrolle in dieser Phase |
|---|---|---|
| V1 Architektur | ja | Sicherheitsgrenze bleibt der PHP-Recheck; die ExApp fuehrt kein eigenes Rechtemodell, der SQLite-Vorfilter ist ausdruecklich nur ein Beschleuniger |
| V2 Authentifizierung | ja | Nutzeridentitaet ausschliesslich aus `AUTHORIZATION-APP-API`; `set_user` bleibt verboten und ist von Gate A abgedeckt |
| V4 Zugriffskontrolle | ja | `#[ExAppRequired]` auf allen Queue-Endpunkten; `/snippets` filtert zusaetzlich ueber den ACL-Vorfilter, damit es kein Leseprimitiv wird |
| V5 Eingabevalidierung | ja | Pydantic mit `extra="forbid"` fuer alle neuen Endpunkte (verhindert eine `userId` im Body); `parse_query_lenient` statt roher Query-Uebernahme; `allow_regexes=False` |
| V7 Fehlerbehandlung und Logging | ja | Fehlergruende sind Klassen (`encrypted_pdf`), niemals Dateinamen oder Inhalte; die Phase-1-Regel "kein Nutzerinhalt im Log" gilt fuer die gesamte Pipeline |
| V12 Dateien und Ressourcen | ja | 50-MB-Cap, Allowlist statt Blocklist, kein Auspacken von Archiven, Scratch im Volume mit Aufraeumen im `finally`, Nur-Lesen-Gates A und B unveraendert |
| V6 Kryptografie | nein | Kein eigener Kryptopfad in dieser Phase |

### Known Threat Patterns

| Muster | STRIDE | Standardgegenmassnahme |
|---|---|---|
| Nutzer findet Inhalt aus einer Datei ohne Zugriff | Information Disclosure | Zwei-Stufen-Protokoll: Kandidaten, PHP-Recheck, erst dann Snippets (COMP-04, SRCH-02) |
| Snippet aus einer entzogenen Freigabe | Information Disclosure | Snippet entsteht nach dem Recheck; ein veralteter ACL-Eintrag fuehrt hoechstens zu einem Kandidaten, der in PHP verworfen wird |
| Trefferzahl verraet fremde Dokumente | Information Disclosure | Es wird erst nach dem Filtern gezaehlt; die Antwort nennt keine Gesamtzahl aus der Engine |
| Nutzer-ID im Anfragekoerper | Spoofing / Elevation | 400 statt stillem Ignorieren, bereits in Phase 1 umgesetzt, gilt fuer die neuen Endpunkte gleichermassen |
| `/snippets` als Leseprimitiv fuer fremde fileIds | Information Disclosure | ACL-Vorfilter auch in `/snippets` |
| Regex- oder Wildcard-Query als Lastangriff | Denial of Service | `allow_regexes=False`, Ergebnislimit, Timeout auf der PHP-Seite |
| Zip-Bombe oder Riesen-XLSX | Denial of Service | Groessen-Cap vor dem Abruf, Zellcap 200.000, Extraktion im getoeteten Subprozess mit Zeitgrenze |
| Pfad-Traversal beim Dateiabruf | Tampering | Unveraendert strukturell ausgeschlossen: der Abruf kennt nur eine `fileId`, keinen Pfad |

---

## Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | Die destillierte Wortliste bleibt beim Analyzer-Bau unter etwa 50 MB RSS und unter etwa 1 Sekunde Bauzeit | Frage 2 | Kompositasplitten muesste per Flag aus, deutsche Sprachqualitaet sinkt spuerbar. **Erste Messung im Plan einplanen** |
| A2 | Die Gross-/Kleinschreibungsregel (nur grossgeschriebene Eintraege) liefert genug Bausteine fuer typische Verwaltungskomposita | Frage 2 | Zu wenige Splits; Gegenmittel waere die volle Liste plus hoehere Mindestlaenge |
| A3 | Der Kompositasplitter erzeugt keine relevanten Fehlsplits bei Mindestlaenge 4 | Frage 2 | Praezisionsverlust bei Allerweltswoertern; die Messung an echten Ratsvorlagen entscheidet |
| A4 | Zwei Proxy-Aufrufe pro Suche bleiben zusammen unter der Wahrnehmungsschwelle der Suchleiste | Pattern 4 | Suche fuehlt sich zaeh an; Ausweg waere ein Snippet-Cache oder Snippets erst bei Klick |
| A5 | 15 Minuten Lock-Timeout sind fuer alle Dateien ausreichend lang | Pattern 1 | Sehr grosse PDFs wuerden doppelt verarbeitet; Gegenmittel ist ein Heartbeat, der die Sperre verlaengert |
| A6 | Ein `ProcessPoolExecutor(max_workers=1)` bleibt mit dem RAM-Budget vertraeglich | Frage 6 | Zweiter Interpreter kostet etwa 40 bis 60 MB; Ausweg waere Extraktion im Hauptthread ohne harte Zeitgrenze, was PITFALLS Nr. 1 wieder oeffnet |
| A7 | `IUserMountCache::getMountsForStorageId` plus Pfadpraefix bildet dieselbe Menge wie `getMountsForFileId` | Pattern 3 | Zu weiter oder zu enger Vorfilter; ein Paritaetstest gegen `getMountsForFileId` auf einer Stichprobe klaert das billig |
| A8 | Team Folders melden sich weiterhin als `OCA\GroupFolders\Mount\MountProvider` | Frage 3 | Team Folders wuerden nicht gecrawlt; in der CI mit installierter Groupfolders-App pruefbar |
| A9 | `charset-normalizer` 3.5.1 vom 15.08.2026 ist unauffaellig | Standard Stack | Nur Versionsrisiko; deshalb Empfehlung, zunaechst 3.5.0 zu pinnen |
| A10 | Der Testfall "suchte/suchen" darf durch "Suche/suchen" ersetzt und die Grenze dokumentiert werden | Pattern 6 | Beruehrt eine woertliche CONTEXT-Formulierung, braucht eine kurze Bestaetigung beim Planen |

---

## Open Questions

1. **Wie gross wird die Wortliste wirklich, und was kostet sie?**
   - Bekannt: Quelle, Lizenz, Paketgroesse (4,6 MB entpackt), Aufbereitungsrezept, Wirkung (gemessen).
   - Unklar: Eintragszahl nach der Filterung, RSS des Aho-Corasick-Automaten, Analysezeit pro MB Text.
   - Empfehlung: erster Task der Sprachspur ist ein Messskript im Container, das die Zahlen ausgibt und ins Repo protokolliert. Erst danach die endgueltigen Filterschwellen festlegen.

2. **Kanarien-Treffer behalten oder entfernen?**
   - Bekannt: Der Phase-1-Integrationstest sucht nach `findling-canary` und prueft die Subline.
   - Empfehlung: behalten, aber nur noch bei exakt diesem Begriff ausliefern. Damit bleibt der Test unveraendert und normale Suchen sind sauber. Wenn er entfernt wird, muss der Phase-1-Test in derselben Plan-Welle umgeschrieben werden, sonst wird die Regression zur Fehldiagnose.

3. **Wie wird der Suchbegriff fuer `type:`-Filter geparst?**
   - Bekannt: Tantivy kann `ext:pdf`, Nextcloud kennt keinen eingebauten Mimetype-Filter.
   - Unklar: ob der Praefix in der Suchzeile fuer Nutzer auffindbar genug ist oder ob es einen `getCustomFilters()`-Eintrag braucht.
   - Empfehlung: Phase 2 baut die Query-Seite, ein sichtbarer Filter in der UI ist Phase-4-Material.

4. **Reicht `IUserMountCache` bei verschachtelten Team-Folder-Rechten?**
   - Offen seit der Projektrecherche. Fuer den Vorfilter ist ein zu weites Ergebnis unschaedlich (PHP verwirft), ein zu enges dagegen nicht (Treffer fehlen).
   - Empfehlung: ein CI-Szenario mit Team Folder und zwei Nutzern mit unterschiedlichen Rechten, spaetestens im Paritaetstest der Phase 5 vollstaendig.

5. **Ab wann wird die `acl`-Tabelle zum Problem?**
   - Bekannt: Hochrechnung aus ARCHITECTURE.md (etwa 12 MB bei 100.000 Dateien und 3 Nutzern je Datei).
   - Unklar: der reale Fanout bei Team Folders mit vielen Mitgliedern.
   - Empfehlung: Kennzahl "ACL-Zeilen je Dokument" ab Phase 2 mitfuehren, Bewertung in Phase 5.

---

## Sources

### Primaer (HIGH confidence)

**Lokal ausgefuehrt am 15.08.2026, `tantivy==0.26.0` via `uv run --with`:**
- Analyzer-Kette mit allen sechs Filtern, Tokenausgabe fuer 20 deutsche Testfaelle
- Vollstaendiger Index aus zwei Dokumenten, Reopen ueber `Index.open`, sieben Query-Formen, SnippetGenerator mit Byte- gegen Zeichenoffsets
- Fehlerfall "Tokenizer nicht registriert" und Typfalle bei `Document(**kwargs)` auf `unsigned`-Feldern

**Quellcode, direkt gelesen:**
- `quickwit-oss/tantivy-py` 0.26.0: `tantivy/tantivy.pyi`, `src/snippet.rs`, `src/tokenizer.rs`, `src/index.rs`
- `quickwit-oss/tantivy` 0.26.0: `src/tokenizer/split_compound_words.rs`, `src/tokenizer/tokenizer_manager.rs`, `src/tokenizer/stop_word_filter/mod.rs` und `stopwords.rs`, `src/directory/directory_lock.rs`, `src/directory/mmap_directory/mod.rs`, `src/directory/mod.rs`
- `nextcloud/server` stable34: `lib/public/Files/Cache/IFileAccess.php`, `lib/public/Files/Config/IUserMountCache.php`, `lib/private/Files/Config/UserMountCache.php`, `lib/public/Share/IManager.php`, `lib/public/Search/ISearchQuery.php`, `lib/public/Search/IFilteringProvider.php`, `lib/public/Search/FilterDefinition.php`, `lib/private/Search/SearchComposer.php`, `core/Command/Background/JobWorker.php`, `core/Command/Background/Job.php`
- `nextcloud/context_chat` main: `lib/Db/QueueMapper.php`, `lib/Db/QueueFile.php`, `lib/Controller/QueueController.php`, `lib/Service/StorageService.php`, `lib/BackgroundJobs/SchedulerJob.php`, `lib/BackgroundJobs/StorageCrawlJob.php`, `lib/Repair/AppInstallStep.php`
- Eigenes Repo: `backend/tests/test_readonly_gate.py`, `.github/workflows/integration.yml`, `scripts/dev/compose.yaml`, `backend/src/findling/nc/client.py`

**Registry und Distribution:**
- PyPI JSON-API fuer alle neun Pakete (Version, `requires_python`, Wheel-Plattformen, Upload-Datum), Stand 15.08.2026
- sources.debian.org: Quellpaket `igerman98` 20161207-15 (trixie), `debian/copyright` (GPL-2+), `debian/control` (Binaerpaket `wngerman`)
- packages.debian.org: Dateiliste und Groesse von `wngerman` in trixie
- `slopcheck install` ueber alle neun Pakete: `9 OK`

### Sekundaer (MEDIUM confidence)

- docs.rs `tantivy::tokenizer::SplitCompoundWords` (Verhalten und Beispiel, deckt sich mit dem gelesenen Quellcode)
- pypdfium2.readthedocs.io, Python-API (Textextraktion, Passwortparameter, Schliessen von Objekten)
- pypdfium2 `docs/devel/changelog.md` (5.13.0 vom 13.08.2026)

### Tertiaer (LOW confidence, kennzeichnungspflichtig)

- Groessen- und Speicherabschaetzungen zur Wortliste und zum Aho-Corasick-Automaten: Hochrechnung, nicht gemessen (Annahmen A1 bis A3)
- Zeitverhalten der zwei Proxy-Aufrufe in der Suchleiste: Erfahrungswert, nicht gemessen (Annahme A4)

---

## Metadata

**Confidence breakdown:**

| Bereich | Level | Grund |
|---|---|---|
| Tantivy-API und Analyzer-Verhalten | HIGH | Quellcode gelesen und lokal mit der Zielversion ausgefuehrt und gemessen |
| Snippet-Offsets | HIGH | Rust-Kommentar plus eigene Messung an deutschem Text |
| Queue-, Crawl- und Job-Muster | HIGH | Vollstaendig aus produktivem Quellcode gelesen |
| Mount- und ACL-Aufloesung | HIGH fuer die APIs, MEDIUM fuer die Pro-Mount-Optimierung | Interfaces und `UserMountCache`-SQL gelesen; die Optimierung ist logisch abgeleitet, nicht gemessen (A7) |
| Wortliste (Quelle und Lizenz) | HIGH | Debian-Quellpaket und Copyright-Datei gelesen |
| Wortliste (Groesse und Kosten) | LOW | Nicht gemessen, erster Messschritt gehoert in den Plan |
| Extraktionsbibliotheken | HIGH fuer Versionen und Wheels, MEDIUM fuer die konkreten Aufrufmuster | PyPI live geprueft; die Aufrufmuster stammen aus Doku und Vorwissen, nicht aus einem eigenen Lauf |
| CI-Erweiterung | HIGH | Bestehender Workflow gelesen, `occ`-Kommandos im Serverquellcode verifiziert |

**Research date:** 2026-08-15
**Valid until:** etwa 30 Tage fuer Tantivy und die Nextcloud-Interfaces, 7 Tage fuer die PyPI-Versionen (`pypdf` und `charset-normalizer` haben in den letzten 48 Stunden veroeffentlicht)
