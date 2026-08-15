# Phase 2: Indexkern und Volltextsuche - Research

**Researched:** 2026-08-15
**Domain:** Tantivy-0.26-Volltextindex mit deutscher Analysekette, Pull-Queue nach dem context_chat-Muster, Crawl pro Mount, SQLite-ACL-Vorfilter, Textextraktion mit Fehlerklassen
**Confidence:** HIGH fuer Analysekette, Filterreihenfolge, Snippet-Offsets, Absturzfestigkeit, Queue- und Crawl-Muster und ACL-Groessen (am 15.08.2026 im Container gegen `tantivy==0.26.0` und das echte Debian-Woerterbuch gemessen bzw. im Quellcode gelesen); MEDIUM fuer die Hochrechnung auf 100k Dateien und fuer die Latenz der zwei Proxy-Roundtrips auf echter Hardware

> **Hinweis zur Entstehung.** Diese Fassung fuehrt zwei unabhaengige Rechercheläufe zusammen. Wo sie sich widersprachen, wurde nicht abgewogen, sondern gemessen; die entscheidenden Faelle stehen mit Messergebnis in Frage 1. Drei Aussagen des ersten Laufs sind dadurch **widerlegt** (Wortlistenrezept, Position von `ascii_fold`, Wirkung von `remove_long`), vier weitere sind **bestaetigt** und waren im zweiten Lauf uebersehen worden (Stemmer-Luecke bei Verbformen, ue/oe/ae-Luecke, Tokenizer-Registrierung nach `Index.open`, Writer-Lock).

---

## Summary

Die drei riskanten Fragen dieser Phase sind beantwortet, und zwei davon anders als erwartet.

**Erstens, deutsche Komposita.** `Filter.split_compound()` funktioniert, aber nur mit einer Wortliste, die ausschliesslich **Bestandteile** enthaelt. Mit der rohen igerman98-Liste (`/usr/share/dict/ngerman`, 356.010 Woerter) wird ausgerechnet der Vorzeigefall nicht zerlegt: "Kündigungsfrist" steht selbst in der Liste, der Aho-Corasick-Automat greift mit `LeftmostLongest` das ganze Wort ab, und eine Suche nach "Frist" findet nichts. Vier Aufbereitungsrezepte wurden gegen 16 echte Komposita gemessen; das beste (**alle** Woerter im Laengenfenster 4 bis 14 plus die Fugenelemente als eigene Eintraege) erreicht 14 von 16 bei null Fehlzerlegungen. Das naheliegende Rezept "nur Substantive, Fugenformen an jedes Wort anhaengen, ASCII falten" erreicht nur 7 von 16 und produziert echte Fehler wie `haushaltss | atzung`.

**Zweitens, zwei Zusagen aus CONTEXT.md sind mit Tantivy-Bordmitteln nicht erfuellbar.** Der Snowball-Stemmer "german" vereinheitlicht Nominalflexion sauber (Haus/Häuser, Vertrag/Verträge, Straße/Strasse jeweils identisch), aber **keine Verbformen**: `suchen` und `Suche` werden beide zu `such`, `suchte` wird zu `sucht`, `gesucht` bleibt `gesucht`. Und die ausgeschriebene Umlautform trifft nicht: `Müller` und `Muller` werden beide zu `mull`, `Mueller` zu `muell`. Beide Faelle stehen woertlich als Abnahmekriterium in CONTEXT.md. Der zweite ist auf der Query-Seite loesbar (Suchbegriff mit `ue/oe/ae/ss` zusaetzlich in der Umlautvariante veroden), der erste nicht ohne Austausch des Stemmers. Das braucht eine Owner-Entscheidung vor dem Bau.

**Drittens, Snippet-Offsets.** Der Phase-1-Befund "Subline ist Klartext" bleibt gueltig und bekommt eine Fortsetzung: `Snippet.highlighted()` liefert **UTF-8-Byte-Offsets**. Gemessen an "... die Kündigungsfrist für ..." liefert Tantivy `(35, 51)`, korrekt in Zeichen waere `(35, 50)`. Ein naives `snippet[start:end]` verschiebt die Hervorhebung bei jedem Umlaut vor der Fundstelle, still. Zusaetzlich erben die Teiltoken eines zerlegten Kompositums die Offsets des Originalworts, weshalb Bereiche mehrfach und ueberlappend auftreten und vor dem Versand verschmolzen werden muessen.

**Absturzfestigkeit ist keine Eigenleistung, sondern eine Konsequenz.** Gemessen: `kill -9` mitten im Schreiben, der Index oeffnet danach auf dem Stand des letzten Commits (56.000 Dokumente), die zurueckgebliebene `.tantivy-writer.lock` ist bedeutungslos und ein neuer Writer wird sofort erteilt. Der Crawl-Fortschritt liegt gar nicht im Container, sondern als Queue-Zeile in der Nextcloud-Datenbank und als `last_file_id` im Job-Argument. IDX-02 ist damit ein Ergebnis der Architektur, kein Mechanismus, den man vergessen kann.

Ein Befund vereinfacht zusaetzlich erheblich: `OCP\Files\Cache\IFileAccess::getDistinctMounts()` und `getByAncestorInStorage()` sind `@since 32.0.0`, unser Fenster faengt bei 32 an. Der komplette Legacy-Pfad, den context_chat mit handgeschriebenem `CacheQueryBuilder`-SQL vorhaelt, entfaellt ersatzlos.

**Primary recommendation:** Ein Index, ein Schreiber, ein Worker. Wortliste `wngerman` ins Image, beim Start auf das Laengenfenster 4 bis 14 reduziert und um die Fugenelemente ergaenzt. Deutsche Kette `simple -> lowercase -> split_compound -> custom_stopword(fugen) -> stopword(german) -> remove_long(48) -> stemmer(german)`, **ohne** `ascii_fold` und mit `remove_long` **nach** dem Splitter, beides gemessen begruendet. Genau eine Factory oeffnet den Index und registriert dabei den Tokenizer. Queue und Crawl eins zu eins nach dem context_chat-Muster, aber mit 15 Minuten Lock-Timeout und einem Unlock-Endpunkt fuer den geordneten Neustart. Suche als **zwei** Proxy-Aufrufe: `/search` liefert nur fileIds und Scores, PHP recheckt, `/snippets` liefert erst danach Text. Extraktion in einem kurzlebigen Kindprozess mit `RLIMIT_AS` und hartem `kill()`-Timeout.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Engine und Sprache**
- Volltext-Engine: Tantivy 0.26 embedded, mmap; Writer-Heap 50 MB, num_threads=1 (4-GB-Budget)
- Deutsch: Snowball-Stemmer "german" + deutsche Stopwörter + ascii_fold (Umlaut-Folding) + split_compound (Komposita; Wortliste beschaffen ist Teil der Phase, Lizenz prüfen); Englisch als zweites Feld/Pipeline
- Snippets: Klartext + Zeichenoffsets (Subline rendert kein HTML, Phase-1-Befund); Hervorhebung macht die PHP-Seite bzw. der Client mit den Offsets; Snippet-Erzeugung erst NACH bestandener Rechteprüfung (SRCH-02)
- Suchoperatoren: Phrasen, +/-, Filter Dateiname vs. Inhalt, Dateityp (SRCH-03)

**Berechtigungskette (Sicherheitsgrenze unverändert)**
- SQLite-ACL-Tabelle (access_list: uid, fileid) als VORFILTER auf Kandidatenlisten (Überfetch + iteratives Nachfassen), finaler Recheck bleibt in PHP via getUserFolder()->getFirstNodeById() (COMP-04); NIE ein eigenes Rechtemodell in Python
- ACL gehört ins ERSTE Schema (nie nachrüsten); Schema führt eine Indexversion (Tantivy-Upgrades können Reindex erzwingen)

**Indexer-Betriebsmodell (die Anti-fulltextsearch-Invarianten)**
- Pull-Queue: PHP führt die Queue (Tabelle), Worker der ExApp pollen, verarbeiten, quittieren; Zeilen-Locks; Backpressure natürlich (Muster context_chat, Quellcode-verifiziert)
- Crawl pro Mount, Cursor = fileid-Integer im Job-Zustand; jede Datei genau EINMAL egal wie viele Nutzer sie sehen (IDX-01); User-Homes + Team Folders default AN, External Storage default AUS
- Fortschritt in der DB, nie im Prozessspeicher: docker kill mitten im Lauf, Neustart, Fortsetzung an der Zustandsmarke = Abnahmetest (IDX-02)
- INDEX_WORKERS=1 als Architektur (IDX-08); OCR-/Embedding-Spuren kommen später in dieselbe Ein-Worker-Disziplin
- failed/skipped sind sichtbare Erstklasse-Zustände mit Grund (zu groß, Typ, Fehler); nie stumm (IDX-06); diese Zustände sind die Datenbasis für die Phase-4-Diagnose
- Zero-Config-Leitplanken: Dokument-Allowlist (PDF, Office, OpenDocument, Text/Markdown, RTF, HTML), 50-MB-Extraktions-Cap, openpyxl read_only + Zellcap 200k, keine Videos/Archive

**Extraktion (Stack-Research, gepinnt)**
- pypdfium2 (PDF-Text), pypdf (Metadaten/Verschlüsselungs-Erkennung VOR pypdfium2), python-docx, python-pptx, openpyxl read_only, ODF via zipfile+lxml (KEIN odfpy), lxml.html, striprtf, charset-normalizer; passwortgeschützte PDFs -> skipped mit Grund
- Inhalte fließen ausschließlich über das Content-Gateway aus Phase 1 (fetch_file_stream, download2stream); Gate A (Nur-Lesen) und Gate B (Korpus-Prüfsummen) bleiben aktiv und dürfen nie verletzt werden

**Qualität und Umgebung**
- Alle 5 Python-Gates vor jedem Commit lokal grün; CI-Erweiterungen folgen dem Phase-1-Muster (walking-skeleton + readonly-gate bleiben grün, neue Jobs für Index/Suche-E2E)
- Referenzkorpus testdata/corpus/ erweitern statt ersetzen (byteidentisch generiert, -text in .gitattributes beachten)
- KEIN lokales PHP; PHP-Verifikation via CI; lokale E2E-Proben über scripts/dev/ (FINDLING_PORT beachten, 8080 ist von der parallelen MCP-Session belegt, 8090 nehmen)

### Claude's Discretion

- Tantivy-Schema-Detail (Felder, DE/EN-Doppelfeld vs. Sprach-Erkennung), Chunking fürs Snippet-Fenster
- Queue-Schema und Quittungs-Protokoll im Detail; Wahl SQLite-Datei-Layout im Container-Volume
- Wie der Erstindex angestoßen wird (occ-Kommando der PHP-App vs. Auto-Start nach Registrierung; Zero-Config spricht für Auto-Start mit Vorab-Schätzungs-Hook für Phase 4)
- Umgang mit dem Kanarien-Treffer aus Phase 1

### Deferred Ideas (OUT OF SCOPE)

- Events + ETag-Reconcile + Löschpfad: Phase 3 (aber: Schema soll Deletions-Verarbeitung nicht verbauen)
- OCR: Phase 3; Embeddings/RRF: Phase 6 (Schema embedding-ready, kein Umbau)
- Statusseite/Diagnose-UI: Phase 4 (aber failed/skipped-Daten entstehen JETZT)
- Lasttest 100k+: Phase 5
</user_constraints>

### Drei Abweichungen von Locked Decisions, die eine Owner-Entscheidung brauchen

Alle drei sind gemessen, nicht gemeint. Details und Zahlen in Frage 1.

| # | Locked Decision | Befund | Vorschlag |
|---|---|---|---|
| **D1** | "ascii_fold (Umlaut-Folding)" in der deutschen Kette | Der Snowball-Stemmer "german" faltet Umlaute und ß selbst (`Müller` und `Muller` beide zu `mull`, `Straße` und `Strasse` beide zu `strass`). `ascii_fold` **vor** `split_compound` wuerde zusaetzlich die Wortliste entwerten, solange die Umlaute enthaelt | `ascii_fold` aus dem deutschen Zweig entfernen. Im englischen Zweig und im Dateinamenfeld bleibt es, dort stemmt nichts |
| **D2** | Testfall "Stemming (suchte/suchen)" | Nicht erfuellbar: `suchen` und `Suche` zu `such`, `suchte` zu `sucht`, `gesucht` zu `gesucht`. Snowball fuer Deutsch behandelt Praeteritum und Partizip nicht | Abnahmekriterium auf Nominalflexion umstellen (Haus/Häuser, Vertrag/Verträge, Kündigung/Kündigungen, alle gemessen erfuellt) und die Verbgrenze dokumentieren |
| **D3** | Testfall "Umlaut-Varianten (Muller/Müller/Mueller)" | Zwei von drei erfuellt. `Mueller` faellt heraus, weil die Faltung aus einem Zeichen eines macht und die ausgeschriebene Form zwei Zeichen bleibt | Auf der Query-Seite loesen: enthaelt der Suchbegriff `ue`, `oe`, `ae` oder `ss`, zusaetzlich die Umlautvariante bilden und beide mit `Occur.Should` veroden. Rund ein Dutzend Zeilen, kein Indexplatz, wirkt nur auf Anfragen |

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| COMP-04 | Suchfluss: ExApp liefert Kandidaten-fileIds mit Scores, PHP macht den finalen Recheck, erst danach Snippets | Pattern 1 und Frage 7b. Zwei Proxy-Aufrufe, beide zusaetzlich ACL-vorgefiltert (Confused-Deputy-Schutz), begrenztes Nachfassen. Messwerte: Suche 0,1 ms, Vorfilter 0,18 ms, 20 Snippets 4,2 ms |
| IDX-01 | Crawl pro Mount, jede Datei genau einmal | Frage 3. `IFileAccess::getDistinctMounts(...)` ab NC 32 verifiziert, Mount-Provider-Klassen inklusive Team Folders benannt, External Storage per Default draussen, Unique-Index auf `file_id` als Deduplizierung |
| IDX-02 | Ueberlebt docker kill, Fortschritt in der DB | Pattern 2 und Pitfall 4. Gemessen: `kill -9` waehrend des Schreibens, Index oeffnet auf dem letzten Commit (56.000 Dokumente), Writer wird sofort wieder erteilt, keine Aufraeumarbeit noetig |
| IDX-03 | Pull-Queue mit Zeilen-Locks, natuerliche Backpressure | Frage 2. Vollstaendiges Tabellen-, Endpunkt- und Quittungsschema aus `context_chat` verifiziert, mit fuenf benannten Abweichungen |
| IDX-06 | Zero-Config-Leitplanken, failed/skipped sichtbar mit Grund | Frage 5. Gemessene Ausnahmetabelle je Bibliothek und Fehlerfall, daraus die Zustandsmaschine mit Grundcode |
| IDX-08 | INDEX_WORKERS=1 als Architektur | Frage 5 und Pattern 3. Ein asyncio-Poller plus genau ein Extraktions-Kindprozess mit `RLIMIT_AS`; gemessen: `RLIMIT_AS` greift als MemoryError, `Process.kill()` beendet einen haengenden Extraktor sicher |
| SRCH-01 | Deutsches Stemming, Stopwoerter, Komposita, Umlaute | Frage 1. Vier Wortlistenrezepte gegen 16 Komposita gemessen, Filterreihenfolge bewiesen, zwei Stemmer-Grenzen benannt (D2, D3), Lizenzkette der Wortliste belegt |
| SRCH-02 | Snippets erst nach bestandener Rechtepruefung | Pattern 1 und Frage 7a. Getrennter `/snippets`-Endpunkt ohne Textfeld in `/search`; dazu der Byte-gegen-Zeichen-Offset-Befund und das Verschmelzen ueberlappender Bereiche |
| SRCH-03 | Operatoren: Phrase, +/-, Dateiname vs. Inhalt, Dateityp | Frage 1, Abschnitt "Query-Syntax". Alle vier Faelle gegen einen echten Index gemessen, plus die Anbindung an Nextclouds eingebauten Filter `title-only` samt der Falle, dass ein Provider bei unbekanntem Filter uebergangen wird |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

| Direktive | Wirkung auf Phase 2 |
|---|---|
| Python 3.13 + uv, lokales System-Python gilt als defekt | Jede Python-Aktion ueber `uv run` / `uv sync`; neue Extraktionspakete als exakte Pins, `uv.lock` mitcommitten |
| AGPL-3.0 | Die Komposita-Wortliste muss AGPL-vertraeglich sein. `wngerman` ist GPL-2+ (Debian-Copyright zu `igerman98`), also auf GPLv3 hochziehbar und mit AGPLv3 vereinbar. Herkunft, Lizenztext und das Aufbereitungsskript gehoeren ins Repo und ins Image |
| Code/README Englisch, Projektkommunikation Deutsch | Feldnamen, Zustaende und Fehlergruende englisch (`skipped_too_large`), Planungsartefakte deutsch |
| Keine Em-Dashes, echte Umlaute nur in deutscher Prosa, nie in Code | Betrifft besonders die Testdaten: der Korpustext traegt Umlaute (deutsche Prosa in einem PDF), die Bezeichner drumherum nicht |
| Globale Qualitaetsgates | `ASYNC` wird hier zum ersten Mal scharf: der Queue-Poller ist eine asyncio-Task, blockierende Aufrufe im Event-Loop sind der Standardfehler. `filterwarnings = ["error::DeprecationWarning"]` macht aus `IndexWriter.delete_documents` einen Testfehler |
| Security/Privacy | Nutzer-ID weiterhin nur aus `AUTHORIZATION-APP-API`; kein Suchbegriff, kein Snippet, kein Dateiname im Log |
| Hardware-Ziel 4-8 GB RAM, ARM-tauglich | Der Komposita-Automat kostet dauerhaft rund 23 MB RSS im selben Prozess wie Suche und Indexierung; das ist im Budget zu fuehren, und es gibt eine gemessene Sparvariante |
| GSD-Workflow-Zwang | Betrifft die Ausfuehrung, nicht die Recherche |

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Mount-Aufzaehlung und Crawl je Mount | Nextcloud-PHP-App (BackgroundJob) | Nextcloud-DB | `IFileAccess` existiert nur im PHP-Prozess; der Crawl ist eine Datenbankabfrage, kein Netzwerkverkehr |
| Arbeitsvorrat und Fortschrittsmarke | Nextcloud-DB (Queue-Tabelle) | PHP-Job-Argument (`last_file_id`) | Transaktional zum Dateisystemzustand; der Container haelt bewusst keinen Crawl-Zustand |
| Ermittlung "wer sieht diese Datei" | Nextcloud-PHP-App (`IUserMountCache`) | - | Einzige belastbare Quelle; ueber die Share-API rekonstruiert verfehlt man Team Folders und externe Mounts |
| Bytes einer Datei | Nextcloud-PHP-App (Content-Gateway aus Phase 1) | Nextcloud-Storage | Rechtepruefung passiert kostenlos mit; kein zweiter Zugriffsweg |
| Textextraktion | ExApp-Kindprozess | - | CPU-lastig und absturzgefaehrdet; gehoert hinter eine Prozessgrenze mit RAM- und Zeitdeckel |
| Volltextindex und Ranking | ExApp (Tantivy im Prozess) | Volume `$APP_PERSISTENT_STORAGE` | Eingebettete Engine, mmap, kein zweiter Serverprozess |
| ACL-Vorfilter auf Kandidatenlisten | ExApp (SQLite) | - | Beschleunigung, ausdruecklich **keine** Sicherheitsgrenze |
| Finale Rechteentscheidung je Treffer | Nextcloud-PHP-App (`getFirstNodeById`) | - | Einzige Sicherheitsgrenze, unveraendert aus Phase 1 |
| Snippet-Erzeugung | ExApp (Tantivy `SnippetGenerator`) | - | Nur dort liegt der Dokumenttext; laeuft erst nach dem PHP-Recheck |
| Query-Umschreibung (Umlautvarianten, Filter) | ExApp | - | Muss dieselbe Analysekette sehen wie der Index; in PHP waere es ein zweites, driftendes Sprachmodell |
| Hervorhebung im UI | Browser bzw. PHP-Seite | - | Die Subline ist Klartext, Markup wuerde woertlich erscheinen |
| Persistenter Indexzustand, Schema- und Analyzerversion | Volume `$APP_PERSISTENT_STORAGE` | - | Tantivy- und Wortlisten-Aenderungen koennen einen Reindex erzwingen; das muss beim Start pruefbar sein |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `tantivy` | 0.26.0 (PyPI, 29.04.2026), meldet sich als `tantivy v0.26.0, index_format v7` | Volltextindex, Analysekette, Query-Parser, Snippets | Einzige eingebettete Engine mit deutschem Snowball-Stemmer, deutschen Stopwoertern und Komposita-Filter; Wheels fuer cp313 und `manylinux_2_17_aarch64` [VERIFIED: PyPI-JSON-API, Wheelliste 15.08.2026; Verhalten im Container gemessen] |
| `wngerman` (Debian) | 20161207-15 in trixie, `Architecture: all` | Wortliste `/usr/share/dict/ngerman` fuer `split_compound` | 356.010 Woerter, 4.725.887 Byte, GPL-2+, per `apt-get` im Basisimage, kein Download zur Laufzeit, identisch auf amd64 und arm64 [VERIFIED: in `debian:trixie-slim` installiert und ausgezaehlt; Lizenz aus `debian/copyright` von `igerman98`] |
| `pypdfium2` | 5.13.0 (13.08.2026), pdfium 153.0.7999.0 | PDF-Textextraktion | Gegen den Referenzkorpus gemessen, klare Fehlerklassen [VERIFIED] |
| `pypdf` | 6.16.1 (14.08.2026) | Verschluesselungserkennung und Metadaten **vor** pypdfium2 | `is_encrypted` erlaubt ein sauberes `skipped`, bevor pdfium anfaengt [VERIFIED] |
| `python-docx` | 1.2.0 | DOCX | Bekannte Luecke Kopf- und Fusszeilen, siehe Frage 5 |
| `python-pptx` | 1.0.2 | PPTX | OOXML ist eingefroren, Releasealter unkritisch |
| `openpyxl` | 3.1.5 | XLSX, zwingend `read_only=True, data_only=True` | Ohne read_only baut openpyxl die Mappe im RAM auf |
| `striprtf` | 0.0.32 (27.04.2026) | RTF | Ein Zweck, BSD, pur Python |
| `charset-normalizer` | 3.5.1 (15.08.2026) | Encoding-Erkennung fuer TXT/MD/CSV | Deutsche Altbestaende sind cp1252 und latin-1 |
| `lxml` | 6.1.1 | HTML und ODF (`zipfile` plus XPath) | Kein odfpy (Release von 2020, faellt durch pyright) |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `sqlite3` (stdlib) | SQLite 3.46.1 im Image | ACL-Vorfilter, Dokumentzustand, Metatabelle | Immer; kein ORM, handgeschriebene Statements in genau einem Modul [VERIFIED: im Image ausgelesen] |
| `multiprocessing` + `resource` (stdlib) | - | Extraktion mit RAM-Deckel und hartem Timeout | Nur `Process.kill()` beendet eine haengende C-Extension zuverlaessig; `ProcessPoolExecutor` kann eine laufende Aufgabe nicht abbrechen [VERIFIED: gemessen] |
| `python-magic` | optional | Typerkennung, falls der Nextcloud-Mimetype nicht reicht | Erst wenn die Allowlist ueber den Filecache-Mimetype nachweislich danebengreift |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Wortliste "alle Woerter, Laenge 4 bis 14" (276.496 Eintraege, 14/16 Treffer, ~23 MB RSS) | "nur Substantive, Laenge 4 bis 14" (86.345 Eintraege, 12/16, Bauzeit 0,18 s statt 0,44 s) | Die Sparvariante kostet zwei von sechzehn Komposita und spart geschaetzt zwei Drittel des Automaten-RAM. Als `FINDLING_COMPOUND_DICT=full|nouns` anbieten, Vorgabe `full` |
| dieselbe | "nur Substantive, Fugenformen angehaengt, ASCII gefaltet" (222.708 Eintraege) | Gemessen nur 7/16 und erzeugt echte Fehlzerlegungen (`haushaltss | atzung`). **Verworfen** |
| `wngerman` (GPL-2+) | `hunspell-de-de` mit Affix-Expansion | Braucht `unmunch` im Build und liefert denselben Korpus. Nur, wenn Flexionsformen fehlen |
| `wngerman` | Wiktionary- oder DWDS-Ableitungen (CC BY-SA 4.0) | Share-alike auf Datenebene, keine Distributionspaketierung, kein Vorteil |
| `split_compound` | `CharSplit` / `compound-split` (statistisch, Python) | Wuerde nur die Indexseite zerlegen, nicht die Anfrage. Der eingebaute Filter zerlegt beide Seiten mit derselben Regel |
| Zwei Sprachfelder `body_de` und `body_en` | Spracherkennung je Dokument | Erkennung ist eine Abhaengigkeit und eine Fehlerquelle mehr und liegt bei gemischten Dokumenten strukturell falsch. Der nicht gespeicherte Indexanteil kostet gemessen nur 0,076 x des Textes |
| `body_de` mit `stored=True` | Extrahierten Text in SQLite legen | Gemessen: mit Store 0,374 x des Textes, ohne 0,076 x. Der Unterschied ist der Textspeicher, den man in SQLite genauso bezahlt, dort aber mit einer zweiten Konsistenzgrenze |
| Ein Suchaufruf mit Snippets | Zwei Aufrufe | Ein Aufruf ist schneller, verletzt aber SRCH-02 woertlich |
| ACL per `getMountsForFileId()` je Datei | Einmal je Mount holen und per Pfadpraefix zuordnen | Die Optimierung spart bei 100k Dateien rund 200.000 Abfragen, baut aber die Praefixlogik von `UserMountCache` nach, und ein Fehler darin macht den Vorfilter systematisch zu weit. Im Erstindex dominiert ohnehin der Byteabruf. **Empfehlung: erst die einfache, korrekte Variante, Optimierung nur nach Messung in Phase 5** |
| SQLite-ACL mit `uid TEXT` | Integer-Nutzer-Mapping | Gemessen 12,0 MB gegen 7,4 MB bei 335k Zeilen. Der Join kostet mehr Code als die 4,6 MB wert sind |

**Installation:**

```bash
cd backend
uv add "tantivy==0.26.0" "pypdfium2==5.13.0" "pypdf==6.16.1" \
       "python-docx==1.2.0" "python-pptx==1.0.2" "openpyxl==3.1.5" \
       "striprtf==0.0.32" "charset-normalizer==3.5.1" "lxml==6.1.1"
```

```dockerfile
RUN apt-get update \
 && apt-get install -y --no-install-recommends wngerman \
 && rm -rf /var/lib/apt/lists/*
# /usr/share/dict/ngerman, 356010 Zeilen, 4725887 Byte, GPL-2+
```

**Version verification:** Alle Versionen am 15.08.2026 gegen die PyPI-JSON-API geprueft (`info.version` plus `upload_time`). `wngerman` in `debian:trixie-slim` installiert und ausgezaehlt.

---

## Package Legitimacy Audit

`slopcheck install tantivy pypdfium2 pypdf python-docx python-pptx openpyxl striprtf charset-normalizer lxml` am 15.08.2026: **scanned 9 packages, 9 OK**.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `tantivy` | PyPI | seit 2021 | hoch | github.com/quickwit-oss/tantivy-py | [OK] | Approved |
| `pypdfium2` | PyPI | seit 2022 | sehr hoch | github.com/pypdfium2-team/pypdfium2 | [OK] | Approved |
| `pypdf` | PyPI | seit 2022 (PyPDF2 seit 2012) | sehr hoch | github.com/py-pdf/pypdf | [OK] | Approved |
| `python-docx` | PyPI | seit 2013 | sehr hoch | github.com/python-openxml/python-docx | [OK] | Approved |
| `python-pptx` | PyPI | seit 2013 | hoch | github.com/scanny/python-pptx | [OK] | Approved |
| `openpyxl` | PyPI | seit 2010 | sehr hoch | foss.heptapod.net/openpyxl/openpyxl | [OK] | Approved |
| `striprtf` | PyPI | seit 2019 | mittel | github.com/joshy/striprtf | [OK] | Approved |
| `charset-normalizer` | PyPI | seit 2019 | sehr hoch | github.com/jawah/charset_normalizer | [OK] | Approved |
| `lxml` | PyPI | seit 2005 | sehr hoch | github.com/lxml/lxml | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

Ausserhalb von PyPI: `wngerman` kommt aus dem Debian-Archiv der Basisdistribution, Quellpaket `igerman98`, in Debian seit ueber zwanzig Jahren, Maintainer Roland Rosenfeld [VERIFIED: sources.debian.org, `debian/control` und `debian/copyright`]. Kein Postinstall-Risiko: alle neun Python-Pakete liefern Wheels, es laeuft kein `setup.py` zur Installationszeit.

---

## Architecture Patterns

### System Architecture Diagram

```
                    INDEXWEG (Pull, langsam, ohne HTTP-Zeitdruck)
+---------------------------------------------------------------------------+
| NEXTCLOUD (PHP)                                                           |
|                                                                           |
|  IRepairStep (install)  ->  SchedulerJob (einmalig)                       |
|     | fuer jeden Mount aus IFileAccess::getDistinctMounts(PROVIDERS,true) |
|     v                                                                     |
|  StorageCrawlJob (QueuedJob, ein Job je Mount)                            |
|     | IFileAccess::getByAncestorInStorage(storage, root, cursor, 2000,    |
|     |     mimeTypeIds, e2e=false, sse=true)                               |
|     | Groessendeckel pruefen, sonst direkt skipped(too_large)             |
|     | INSERT INTO oc_findling_queue ... ON CONFLICT (file_id) DO UPDATE   |
|     | scheduleAfter(self, now+interval, ['last_file_id' => n])            |
|     v                                                                     |
|  oc_findling_queue  (id, file_id, storage_id, root_id, is_update,         |
|                      size, locked_at, retries)                            |
|     ^                                                                     |
|     | GET  /queues/documents?n=32&max_bytes=64000000    [ExAppRequired]   |
|     |      -> sperrt Zeilen, liefert je Zeile Metadaten + userIds         |
|     | GET  /files/{fileId}?userId=...                   [ExAppRequired]   |
|     |      -> StreamResponse mit den Bytes  (Gateway aus Phase 1)         |
|     | DELETE /queues/documents  {files:[...], failed:[{id,reason}]}       |
|     | POST /queues/documents/unlock  {ids:[...]}   (SIGTERM-Pfad)         |
+-----|---------------------------------------------------------------------+
      |
      v
+---------------------------------------------------------------------------+
| ExApp-CONTAINER (ein Prozess, INDEX_WORKERS=1)                            |
|                                                                           |
|  asyncio-Task "poller"  (im lifespan gestartet, von /enabled gesteuert)   |
|     |  1. Batch holen         5. writer.commit()   <-- Absturzgrenze      |
|     |  2. Bytes streamen      6. SQLite: files + acl COMMIT               |
|     |  3. Extraktion im       7. DELETE-Quittung an PHP                   |
|     |     Kindprozess                                                     |
|     |     (RLIMIT_AS, kill-Timeout)                                       |
|     |  4. delete_documents_by_term(file_id) + add_document                |
|     v                                                                     |
|  $APP_PERSISTENT_STORAGE/                                                 |
|     index/            Tantivy, mmap, atomare Commits                      |
|     state.db          SQLite: files, acl, mounts, meta                    |
|     dict/de.txt       aufbereitete Wortliste (Artefakt, gehasht)          |
|     tmp/              Scratch der Extraktion, beim Start geleert          |
+---------------------------------------------------------------------------+

                    SUCHWEG (Push, schnell, zwei Roundtrips)
Nutzer -> Unified Search -> OCA\Findling\Search\Provider
   |
   | 1. exAppRequest('/search', uid, {query, limit, offset, filters}, timeout 1.5s)
   v
ExApp: Query umschreiben (Umlautvarianten, ext-Filter) -> parse_query_lenient
       -> Tantivy Top-K (Ueberfetch)
       -> SQLite-ACL-Vorfilter fuer uid  (Beschleuniger, KEINE Grenze)
       -> {candidates:[{fileId,score,mtime,ext}], hasMore, nextOffset}
   |
   | 2. PHP: je fileId getUserFolder(uid)->getFirstNodeById(fileId)
   |    -> EINZIGE Sicherheitsgrenze; zu wenige Treffer -> Schritt 1 erneut,
   |       hoechstens zweimal, und nur solange das Zeitbudget reicht
   v
   | 3. exAppRequest('/snippets', uid, {query, fileIds}, timeout 1.5s)
   v
ExApp: erneut ACL-Vorfilter auf fileIds (Confused-Deputy-Schutz)
       -> SnippetGenerator -> fragment() + verschmolzene Zeichenoffsets
   |
   v
PHP: SearchResultEntry, subline = snippet (Klartext), Offsets als JSON in
     attributes; SearchResult::paginated(..., nextCursor)
```

### Recommended Project Structure

Erweiterung des bestehenden Baums, keine Umbenennung von Phase-1-Dateien:

```
php/
├── lib/
│   ├── AppInfo/Application.php          # + AddMissingIndicesEvent-Listener
│   ├── Search/Provider.php              # + zweistufiger Suchpfad, paginated()
│   ├── Service/
│   │   ├── ExAppService.php             # + searchCandidates() und snippets();
│   │   │                                #   weiterhin die EINZIGE exAppRequest-Stelle
│   │   ├── StorageService.php           # NEU: Mounts, Dateien je Mount, userIds
│   │   └── QueueService.php             # NEU: einreihen, deduplizieren, zaehlen
│   ├── Db/QueueFile.php  QueueMapper.php            # NEU
│   ├── BackgroundJobs/SchedulerJob.php  StorageCrawlJob.php   # NEU
│   ├── Controller/
│   │   ├── GatewayController.php        # unveraendert aus Phase 1
│   │   └── QueueController.php          # NEU
│   ├── Command/IndexCommand.php         # NEU: occ findling:index [--restart|--status]
│   ├── Repair/AppInstallStep.php        # NEU: plant den SchedulerJob beim Install
│   ├── Listener/AddMissingIndicesListener.php       # NEU
│   └── Migration/Version001000Date2026....php       # NEU
│
backend/src/findling/
├── main.py                              # + Poller-Lebenszyklus, SIGTERM-Unlock
├── nc/client.py                         # + fetch_queue_batch, ack_batch, unlock_batch
├── api/
│   ├── search.py                        # POST /search: Kandidaten, KEIN Textfeld
│   ├── snippets.py                      # NEU: POST /snippets
│   └── status.py                        # NEU: GET /status (Zaehler, Phase 4 nutzt sie)
├── index/
│   ├── wordlist.py                      # NEU: Aufbereitung + Hash
│   ├── analyzer.py                      # NEU: die Filterkette, ANALYZER_VERSION
│   ├── schema.py                        # NEU: Felder
│   ├── open.py                          # NEU: die EINZIGE Stelle mit Index(...)/open()
│   └── writer.py                        # NEU: die EINZIGE Stelle mit IndexWriter
├── query/rewrite.py                     # NEU: Umlautvarianten, Filteruebersetzung
├── store/
│   ├── schema.sql                       # NEU: als Datei, nicht im Code
│   └── repo.py                          # NEU: die EINZIGE Stelle mit SQL
├── extract/
│   ├── dispatch.py  pdf.py  office.py  odf.py  text.py       # NEU
│   ├── errors.py                        # NEU: Zustaende und Gruende
│   └── sandbox.py                       # NEU: Kindprozess, RLIMIT_AS, Timeout
└── worker/poller.py                     # NEU: die asyncio-Task
```

Zwei Kapselungen aus Phase 1 bleiben unangetastet und bekommen je eine Erweiterung (`ExAppService.php`, `nc/client.py`). Drei neue kommen dazu: `index/open.py` (jedes Oeffnen registriert den Tokenizer, sonst wirft schon das Parsen einer Query), `index/writer.py` (Tantivy laesst pro Verzeichnis genau einen Writer zu) und `store/repo.py` (SQL an einer Stelle).

### Pattern 1: Der zweistufige Suchpfad

**Was:** Zwei Proxy-Aufrufe. Der erste liefert `fileId` und `score`, kein Byte Dateiinhalt. Dazwischen macht PHP den `getFirstNodeById`-Recheck. Der zweite liefert Snippets fuer die ueberlebenden Treffer.

**Warum so:** SRCH-02 verlangt woertlich, dass Snippets erst nach bestandener Rechtepruefung entstehen, und ein Snippet ist Dateiinhalt. Bei einem einzigen Aufruf laege der Inhalt aller Kandidaten schon im PHP-Prozess, bevor die Sicherheitsgrenze gelaufen ist; ein Fehler in der Filterschleife waere dann ein Inhaltsleck statt eines Treffers zu viel. Das Antwortmodell von `/search` hat deshalb **kein** Textfeld, damit kein Refactoring versehentlich eines einfuegt.

**Der zweite Aufruf ist zustandslos.** `SnippetGenerator.create(searcher, query, schema, "body_de")` braucht nur die erneut geparste Query und das Dokument aus dem Doc-Store. Kein Query-Cache zwischen den Aufrufen, also keine Cache-Invalidierung und kein Speicherleck.

**Kosten, gemessen:** Tantivy-Suche 0,1 ms, ACL-Vorfilter fuer 400 Kandidaten 0,18 ms, 20 Snippets 4,2 ms, Ueberfetch von 400 Kandidaten 4,2 ms. Der Aufwand liegt vollstaendig im Proxy-Roundtrip und im PHP-Recheck.

**Drei Feinheiten, die in den Plan gehoeren:**
1. `/snippets` bekommt fileIds von aussen und muss denselben ACL-Vorfilter anwenden wie `/search`, sonst ist er ein Confused Deputy: wer den Proxy erreicht, koennte Snippets beliebiger Dateien anfordern. Kostet 0,2 ms.
2. Der Recheck kann so viele Kandidaten verwerfen, dass zu wenige bleiben. `/search` liefert `hasMore` und `nextOffset`, und PHP darf **hoechstens zweimal** nachfassen. Eine unbegrenzte Schleife ist genau der Fehler, der abfragezeitliche Rechtefilterung unbrauchbar macht.
3. Zeitbudget als Wanduhr im Provider. Ist es nach dem Recheck aufgebraucht, wird `/snippets` gar nicht mehr gerufen: **ein Treffer ohne Snippet ist besser als kein Treffer.** Die Subline faellt dann auf den Pfad zurueck.

### Pattern 2: Die Fortschrittsmarke liegt in Nextcloud, nicht im Container

**Was:** Der Container speichert keinen Crawl-Zustand. Was noch zu tun ist, steht als Zeile in `oc_findling_queue`; wie weit der Crawl je Mount gekommen ist, steht als `last_file_id` im Argument des naechsten `StorageCrawlJob`. Die `mounts`-Tabelle in `state.db` ist nur ein Spiegel fuer die Anzeige.

**Warum so:** IDX-02 wird damit zur Konsequenz statt zum Mechanismus. Ein `docker kill` beendet den Container mitten in einem Batch, die betroffenen Zeilen bleiben gesperrt, laufen nach dem Lock-Timeout ab und werden erneut ausgeliefert. Alles, was der Container leisten muss, ist Idempotenz: `delete_documents_by_term("file_id", fileId)` vor `add_document`.

**Die Reihenfolge, die nicht verhandelbar ist:**

```
1. Bytes holen, extrahieren, delete_documents_by_term + add_document
2. writer.commit()                    <- ab hier ist der Index dauerhaft
3. SQLite: files.state, reason, indexed_at und acl (eine Transaktion)
4. DELETE /queues/documents           <- Quittung an PHP
```

Bricht es vor 2 ab, ist nichts passiert. Zwischen 2 und 3 ist das Dokument im Index und gilt in SQLite als offen: die Wiederholung ueberschreibt es idempotent. Zwischen 3 und 4 kommt die Queue-Zeile erneut, der Worker sieht `state='indexed'` bei gleichem `content_hash` und quittiert sofort ohne Arbeit. Die umgekehrte Reihenfolge verliert Dokumente stillschweigend und ist die Fehlerklasse aus PITFALLS Nr. 2.

**Nach einem harten Kill ist nichts aufzuraeumen.** Gemessen: `kill -9` waehrend des Schreibens, danach oeffnet `Index.open()` auf dem letzten Commit (56.000 Dokumente), die Datei `.tantivy-writer.lock` liegt noch da und ist bedeutungslos, ein neuer Writer wird sofort erteilt und das naechste Dokument geschrieben. Der Lock ist ein OS-Lock am Dateihandle, und ein getoeteter Prozess gibt seine Handles ab. Der Vorbehalt: auf NFS gilt das nicht.

### Pattern 3: Extraktion hinter einer Prozessgrenze

**Was:** Jede Extraktion laeuft in einem Kindprozess, der zu Beginn `resource.setrlimit(RLIMIT_AS, cap)` setzt. Der Elternprozess wartet mit `join(timeout)`; laeuft der Timeout ab, folgen `kill()` und `join()`.

**Warum so:** `pypdfium2` und `lxml` sind C-Erweiterungen. Ein Thread mit einem haengenden C-Aufruf laesst sich in Python nicht abbrechen, `signal.alarm` wirkt nur im Hauptthread, und `ProcessPoolExecutor` kann eine laufende Aufgabe nicht toeten (`future.result(timeout=...)` gibt nur dem Wartenden auf). Gemessen: `RLIMIT_AS` von 300 MB liefert im Kind einen sauberen `MemoryError`, `kill()` auf eine Endlosschleife liefert Exitcode -9. Damit sind Zeit- und RAM-Deckel aus IDX-06 und IDX-08 mit der Standardbibliothek erreichbar.

**Ein Kindprozess, nicht ein Pool.** Das ist kein Widerspruch zu IDX-08: es laeuft weiterhin genau eine Extraktion zur Zeit, sie liegt nur in einem anderen Adressraum. Der Startkontext sollte explizit `spawn` sein statt des Linux-Standards `fork`, weil `fork` in einem Prozess mit laufendem Event-Loop und offenen Sockets eine bekannte Fehlerquelle ist und Python ohnehin dorthin wandert.

**Tantivy und der Event-Loop.** Tantivy gibt in `add_document`, `commit` und `search` die GIL frei. Der Indexer bremst die Suche also nicht spuerbar. Trotzdem gehoeren die Tantivy-Aufrufe der HTTP-Endpunkte in `asyncio.to_thread`, damit ein langer Commit den Event-Loop nicht stehen laesst und `/heartbeat` weiter antwortet.

### Pattern 4: Eine Wortliste ist ein Build-Artefakt, keine Laufzeitentscheidung

**Was:** Beim Start wird `/usr/share/dict/ngerman` einmal gelesen, auf das Laengenfenster reduziert, kleingeschrieben, um die Fugenelemente ergaenzt und als `dict/de.txt` im Volume abgelegt, zusammen mit einem SHA-256. Existiert die Datei mit passendem Hash, wird sie direkt geladen.

**Warum so:** Der Aufbau kostet gemessen 0,44 s und rund 23 MB dauerhaftes RSS. Verkraftbar, aber nicht pro Anfrage, und die konkrete Liste bestimmt das Suchergebnis. `wordlist_hash` und `analyzer_version` gehoeren deshalb neben `schema_version` und `tantivy_version` in die Metatabelle: aendert sich eines davon, aendert sich die Tokenisierung, und der Index ist nicht mehr konsistent mit dem Query-Parser.

### Anti-Patterns to Avoid

- **Die rohe Wortliste in `split_compound` kippen.** Gemessen: "Kündigungsfrist" wird dann nicht zerlegt, weil es selbst in der Liste steht, und "Frist" findet das Dokument nicht.
- **`remove_long` vor `split_compound` setzen.** Gemessen: "Rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz" ergibt mit `remove_long(40)` an Position zwei **`[]`**, das Wort verschwindet ersatzlos. Mit `remove_long(48)` nach dem Splitter ergibt es sechs saubere Teile. Tantivys eingebauter `default`-Analyzer nutzt `RemoveLongFilter::limit(40)` und verschluckt damit lange deutsche Komposita stillschweigend.
- **`ascii_fold()` vor `split_compound` mit einer nicht gefalteten Wortliste.** Dann greift der Automat nie und die Zerlegung faellt still aus.
- **Den Tokenizer nach `Index.open()` nicht registrieren.** Gemessen: `ValueError: The tokenizer '"de_findling"' for the field '"body_de"' is unknown`, und zwar schon beim Parsen der Query. Das Schema speichert nur den **Namen**. Deshalb genau eine Funktion `open_index()`, die oeffnet **und** registriert, und nirgends sonst ein `Index(...)`.
- **Numerische Felder ueber Schluesselwortargumente fuellen.** Gemessen: `Document(file_id=42)` auf einem `unsigned`-Feld ergibt `ValueError: Schema error: 'Expected a U64 for field "file_id"'`. Immer `doc.add_unsigned(...)` bzw. `Document.from_dict(payload, schema)`.
- **`highlighted()`-Bereiche als Zeichenpositionen weitergeben.** Gemessen `(35, 51)` in Bytes gegen `(35, 50)` in Zeichen.
- **Ueberlappende Hervorhebungsbereiche ungeprueft versenden.** Die Teiltoken eines Kompositums erben die Offsets des Originals, also kommt derselbe Bereich mehrfach. Vor dem Versand sortieren und verschmelzen.
- **`index.parse_query()` auf Nutzereingabe.** Ein unpaariges Anfuehrungszeichen wirft, und die Ergebnisgruppe verschwindet ohne Meldung. `parse_query_lenient()` liefert `(Query, errors)`.
- **Die Standard-Disjunktion behalten.** `conjunction_by_default=False` macht aus einem zerlegten Kompositum ein Oder ueber drei Allerweltsteile. Nutzer erwarten UND.
- **Einen zweiten `IndexWriter` erzeugen.** Gemessen: zwei `Index.open()` auf dasselbe Verzeichnis, der zweite Writer liefert `ValueError: Failed to acquire Lockfile: LockBusy`.
- **Einen Commit je Dokument.** Jeder Commit erzeugt ein Segment und einen fsync. Sammel-Commits je Batch, und der Batch ist die Absturzgranularitaet.
- **Den ACL-Vorfilter fuer die Sicherheitsgrenze halten.** Er ist eine Ueberapproximation, weil `IUserMountCache` die erweiterten Berechtigungen der Team Folders nicht aufloest.
- **Snippets aus einem einzigen Suchaufruf mitliefern und in PHP wegfiltern.** Verletzt SRCH-02, und der Filterfehler ist ein Inhaltsleck.
- **Alle sichtbaren fileIds eines Nutzers materialisieren.** Der context_chat-Anti-Pattern. Immer `WHERE uid = ? AND file_id IN (Kandidaten)`, nie umgekehrt.
- **`update` als Spaltenname.** Reservierter Bezeichner in mehreren Dialekten; `is_update` kostet nichts.
- **Die Legacy-Filecache-Abfragen aus context_chat kopieren.** `IFileAccess` ist ab NC 32 da, unser Fenster faengt bei 32 an.

---

## Antworten auf die Research-Fragen

### Frage 1: Tantivy-0.26-Schema fuer Deutsch

#### Die Bausteine, verifiziert

`tantivy.Filter` bietet `alphanum_only`, `ascii_fold`, `lowercase`, `remove_long(n)`, `stemmer(lang)`, `stopword(lang)`, `custom_stopword(list)` und `split_compound(list)`. `parse_language` akzeptiert unter anderem `"german"` und `"english"` [VERIFIED: `tantivy-py`, `tantivy/tantivy.pyi` und `src/tokenizer.rs`].

`Filter.split_compound(constituent_words)` baut einen Aho-Corasick-Automaten mit `MatchKind::LeftmostLongest`. Ein Token wird **nur dann** zerlegt, wenn es sich **vollstaendig** in aufeinanderfolgende Treffer zerlegen laesst, die luekenlos bei Position 0 beginnen und exakt am Tokenende enden. Sonst bleibt das Originaltoken stehen. Die Teiltoken erben Offsets und Position des Originals (`Token { text: tail.to_owned(), ..*token }`) [VERIFIED: `tantivy/src/tokenizer/split_compound_words.rs`].

Daraus folgen drei Eigenschaften, die den Entwurf bestimmen:

1. **Greedy und nicht rekursiv.** Steht das Kompositum selbst in der Wortliste, wird es nie zerlegt.
2. **Fugenelemente muessen erreichbar sein**, sonst reisst die Kette bei "Grundstück|s|verkehr|s|genehmigung".
3. **Die Hervorhebung trifft immer das ganze Kompositum**, und derselbe Bereich kommt mehrfach.

#### Die Wortliste: Herkunft, Lizenz, Rezept

| Eigenschaft | Wert |
|---|---|
| Debian-Paket | `wngerman` 20161207-15, `Architecture: all` |
| Quellpaket | `igerman98`, Upstream Björn Jacke, Maintainer Roland Rosenfeld |
| Datei | `/usr/share/dict/ngerman` |
| Umfang | 356.010 Zeilen, 4.725.887 Byte |
| Lizenz | **GPL-2+** laut `debian/copyright` (`Files: *`, `Copyright: 1999-2016 Björn Jacke`); Upstream nennt zusaetzlich eine OASIS-Distributionslizenz als Alternative |
| AGPL-Vertraeglichkeit | **ja**. GPL-2+ erlaubt den Uebergang auf GPLv3, GPLv3 ist mit AGPLv3 kombinierbar. Lizenztext und Herkunft ins Image und in `THIRD-PARTY.md`, das Aufbereitungsskript bleibt im Repo |

[VERIFIED: sources.debian.org API fuer `igerman98/20161207-16/debian/copyright` und `debian/control`; Paket in `debian:trixie-slim` installiert und ausgezaehlt]

**Vier Rezepte, gegen 16 echte Komposita und 10 Woerter gemessen, die **nicht** zerfallen duerfen** (Information, Vertrag, Rechnung, Sitzung, Kunde, Formular, Termin, Ordnung, Beamter, Genehmigung):

| Rezept | Eintraege | Bauzeit | Kompositum ueber ein Teilwort findbar | Fehlzerlegungen |
|---|---|---|---|---|
| **A: alle Woerter, Laenge 4 bis 14, Fugen als eigene Eintraege** | 276.496 | 0,44 s | **14 / 16** | **0** |
| B: nur Substantive, Fugenformen angehaengt, ASCII gefaltet | 222.708 | 0,36 s | 7 / 16 | 0, aber echte Fehler wie `haushaltss | atzung` |
| C: nur Substantive, Laenge 4 bis 14, Fugen als eigene Eintraege | 86.345 | 0,18 s | 12 / 16 | 0 |
| D: nur Substantive, Laenge 4 bis 12 | 65.693 | 0,11 s | 12 / 16 | 0, aber `betrieb | kost | abrechn` statt `betriebskost | abrechn` |

**Empfehlung: Rezept A**, mit C als gemessener Sparvariante hinter `FINDLING_COMPOUND_DICT=full|nouns`. Rezept B ist das naheliegende und **messbar schlechteste**; es scheitert genau an den langen Behoerdenkomposita, um die es geht.

Ergebnisse mit Rezept A:

| Eingabe | Tokens | Findbar ueber |
|---|---|---|
| Grundstücksverkehrsgenehmigung | `grundstuck, verkehr, genehm` | Grundstück, Verkehr, **Genehmigung** |
| Kündigungsfrist | `kundig, frist` | Kündigung, **Frist** |
| Sitzungsvorlage | `sitzung, vorlag` | Sitzung, Vorlage |
| Haushaltssatzung | `haushalt, satzung` | Haushalt, Satzung |
| Jahresabschluss | `jahr, abschluss` | Jahr, Abschluss |
| Betriebskostenabrechnung | `betriebskost, abrechn` | Betriebskosten, Abrechnung |
| Krankenversicherung | `krank, versicher` | krank, Versicherung |
| Rechnungsnummer | `rechnung, numm` | Rechnung, Nummer |
| Datenschutzgrundverordnung | `datenschutz, grund, verordn` | jedes Teil |
| Bundesausbildungsförderungsgesetz | `bund, ausbild, forder, gesetz` | jedes Teil |
| Rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz | `rindfleisch, etikettier, uberwach, aufgab, ubertrag, gesetz` | jedes Teil |
| Dampfschifffahrt | `dampfschiff, fahrt` | Dampfschiff, Fahrt |
| Mietvertrag | `mietvertrag` | **nur als Ganzes** (11 Zeichen, steht in der Liste) |
| Bebauungsplan | `bebauungsplan` | nur als Ganzes |
| Straße | `strass` | ß wird zu ss |

**Ehrliche Grenze:** Komposita bis 14 Zeichen, die selbst in der Liste stehen, werden nicht zerlegt. "Mietvertrag" ist ueber "Vertrag" nicht findbar. Ein kleineres Fenster zerlegt mehr und riskiert Ueberzerlegung (Rezept D). Das Fenster gehoert als Konstante an eine Stelle, mit Testfaellen in beide Richtungen.

**Kosten, gemessen:** Wortliste laden und filtern 0,1 s, Analyzer bauen 0,44 s, dauerhaftes RSS des Automaten rund 23 MB (60 MB nach dem Freigeben der Python-Liste gegen 37 MB davor), Durchsatz rund 2,3 Mio. Token/s. Der Automat wird pro Token-Stream geklont, aber der Klon ist billig; der Durchsatz belegt es.

#### Die Filterreihenfolge, bewiesen statt begruendet

```python
de = (TextAnalyzerBuilder(Tokenizer.simple())
      .filter(Filter.lowercase())               # die Wortliste ist kleingeschrieben
      .filter(Filter.split_compound(dict_de + FUGEN))
      .filter(Filter.custom_stopword(FUGEN))    # das uebrige "s" wieder entfernen
      .filter(Filter.stopword("german"))        # sieht ungefaltete Tokens, trifft also
      .filter(Filter.remove_long(48))           # NACH dem Splitter, sonst Totalverlust
      .filter(Filter.stemmer("german"))         # faltet Umlaute und ss selbst
      .build())
```

| Position | Filter | Beweis fuer genau diese Stelle |
|---|---|---|
| 1 | `lowercase` | Alles Weitere vergleicht Zeichenketten exakt |
| 2 | `split_compound` | Braucht das ungestemmte, ungefaltete Token; die Wortliste liegt in genau dieser Form vor |
| 3 | `custom_stopword(FUGEN)` | Ohne diesen Schritt landet ein Token `s` im Index. Gemessen: mit ihm `Kündigungsfrist -> kundig, frist`, ohne ihn `kundig, s, frist` |
| 4 | `stopword("german")` | Die eingebaute Liste enthaelt echte Umlaute und vergleicht exakt. Gemessen: `"für über während könnte und der die das"` ergibt `[]` |
| 5 | `remove_long(48)` | **Gemessen:** an Position 1 mit Limit 40 ergibt das 63-Zeichen-Kompositum `[]`, an dieser Position sechs Teile |
| 6 | `stemmer("german")` | Zuletzt; ein gestemmtes Kompositum findet keine Woerterbucheintraege mehr |

`ascii_fold` kommt **nicht** vor (Abweichung D1). Gemessen: der Stemmer faltet selbst, und zwei konsistente Varianten liefern identische Ergebnisse, naemlich (a) Wortliste mit Umlauten ohne `ascii_fold` und (b) gefaltete Wortliste mit `ascii_fold`. Variante (a) ist einfacher, weil die Liste dann byteweise dem Debian-Paket entspricht.

Englisch und Dateiname behalten `ascii_fold`, dort stemmt entweder ein anderer Algorithmus oder gar keiner:

```python
en   = simple -> lowercase -> ascii_fold -> stopword("english") -> remove_long(48) -> stemmer("english")
name = simple -> lowercase -> ascii_fold -> remove_long(60)      # kein Stemming
```

#### Was der Stemmer leistet und was nicht

| Gruppe | Ergebnis | Bewertung |
|---|---|---|
| `Haus` / `Häuser` | `haus` / `haus` | Nominalflexion sauber |
| `Vertrag` / `Verträge` | `vertrag` / `vertrag` | sauber |
| `Straße` / `Strasse` | `strass` / `strass` | ß normalisiert |
| `Müller` / `Muller` | `mull` / `mull` | Umlaut gefaltet, ohne `ascii_fold` |
| `Mueller` | `muell` | **Luecke D3**, ausgeschriebene Form trifft nicht |
| `suchen` / `Suche` | `such` / `such` | Infinitiv und Nomen zusammengefuehrt |
| `suchte` / `gesucht` | `sucht` / `gesucht` | **Luecke D2**, Praeteritum und Partizip nicht |

**Umgang mit D3, auf der Query-Seite:** enthaelt der Suchbegriff `ue`, `oe`, `ae` oder `ss`, zusaetzlich die Umlautvariante bilden und beide Zweige mit `Occur.Should` veroden. Das kostet keinen Indexplatz, wirkt nur auf Anfragen, und eine gelegentlich sinnlose Variante ("neue" wird zu "neü") erzeugt nur einen leeren Zweig. Der umgekehrte Weg, beide Formen zu indexieren, waere ebenfalls moeglich, kostet aber Indexplatz fuer einen selteneren Fall.

**Umgang mit D2:** nicht loesbar, ohne den Stemmer auszutauschen. Das Abnahmekriterium gehoert auf Nominalflexion umgestellt und die Grenze dokumentiert.

#### Empfohlenes Schema

| Feld | Typ | stored | indexed | fast | Tokenizer | Zweck |
|---|---|---|---|---|---|---|
| `file_id` | unsigned | ja | ja | ja | - | Schluessel, Ziel von `delete_documents_by_term`, Rueckgabewert |
| `storage_id` | unsigned | ja | ja | ja | - | Reserve fuer den Mount-Vorfilter (Phase 5), Diagnose |
| `name` | text | ja | ja | nein | `name` | Dateiname, SRCH-03 "Dateiname statt Inhalt" |
| `title` | text | ja | ja | nein | `de` | Dokumenttitel aus den Metadaten, hoeher gewichtet |
| `path` | text | ja | nein | nein | - | Anzeige und Diagnose, nicht durchsuchbar |
| `ext` | text | ja | ja | nein | `raw` | SRCH-03 Dateityp, exakte Terme, gemessen als `ext:pdf` |
| `body_de` | text | **ja** | ja | nein | `de` | Inhalt und **einzige** gespeicherte Textkopie, Quelle des SnippetGenerators |
| `body_en` | text | nein | ja | nein | `en` | derselbe Text, englische Pipeline, nicht gespeichert |
| `mtime` | integer | ja | nein | ja | - | Anzeige, spaeter Sortierung und `since`/`until` |

`body_de` muss `stored=True` sein, weil `snippet_from_doc(doc)` den Text aus dem gespeicherten Dokument liest. Gemessene Kosten: Index mit gespeichertem Body 0,374 x des extrahierten Textes, ohne 0,076 x, also rund 2.100 Byte je Dokument bei 600-Wort-Dokumenten, und 1.675 Dokumente/s beim Schreiben.

**Hochrechnung fuer 100.000 Dateien** mit im Mittel 15 kB Text: 1,5 GB Text, rund 560 MB Indexverzeichnis auf Platte, mmap-gelesen, also kaum RSS. Ein Deckel auf den extrahierten Text je Dokument (Vorschlag 512 kB, danach Zustand `truncated`) begrenzt den Ausreisser, den ein 50-MB-PDF sonst produziert.

**Versionierung in `meta`:** `schema_version`, `index_version`, `analyzer_version`, `wordlist_hash`, `tantivy_version`. Beim Start pruefen; jede Abweichung erzwingt einen Reindex, und der ist ein sichtbarer Zustand.

#### Query-Syntax, gegen einen echten Index gemessen

| Eingabe | Wirkung | Ergebnis |
|---|---|---|
| `frist` | einfacher Term ueber Komposita hinweg | findet "Kündigungsfrist" und "Frist" |
| `"drei Monate"` | Phrase | nur das Dokument mit der Wortfolge |
| `vertrag +frist` | Pflichtterm | wie erwartet |
| `vertrag -frist` | Ausschluss | wie erwartet |
| `name:kündigung` | Feldsuche Dateiname | nur Dateinamentreffer |
| `ext:pdf AND frist` | Dateityp plus Inhalt | wie erwartet |
| `muller` / `müller` | Umlaut-Aequivalenz | beide finden beide Schreibweisen |

```python
query, errors = index.parse_query_lenient(
    rewritten_input,
    default_field_names=["body_de", "body_en", "name", "title"],
    field_boosts={"name": 3.0, "title": 2.0, "body_de": 1.0, "body_en": 0.8},
    conjunction_by_default=True,
)
```

`allow_regexes` bleibt `False`: eine Regex aus der Suchleiste ist ein Denial of Service auf die eigene Instanz. `searcher.search(query, limit, offset=..., count=True)` liefert `hits` und `count`; `offset` ist der Weg fuer das begrenzte Nachfassen. `Index.config_reader(reload_policy="commit")` ist die Vorgabe, der Reader sieht neue Commits mit Verzoegerung, fuer deterministische Tests `index.reload()` aufrufen.

**Anbindung an Nextclouds Filter (SRCH-03):** der eingebaute Filter `title-only` (`IFilter::BUILTIN_TITLE_ONLY`) ist genau "Dateiname statt Inhalt" und kostet nur `getSupportedFilters()` in einem `IFilteringProvider`. Fuer den Dateityp gibt es keinen eingebauten Filter, er reist als `type:pdf` in der Suchzeile und wird in der ExApp in eine `Occur.Must`-Termquery auf `ext` uebersetzt. **Falle:** ein Provider wird laut Interfacedokumentation **uebergangen**, wenn ein Client einen Filter sendet, den `getSupportedFilters()` nicht nennt. Die Liste muss also vollstaendig sein, nicht sparsam.

**`heap_size`:** unter 15.000.000 Byte je Thread wird der Writer hart abgelehnt ("The memory arena in bytes per thread needs to be at least 15000000"). Die 50 MB aus CONTEXT.md sind gueltig.

**Voller Datentraeger:** ein `commit()` schlaegt mit einem IO-Fehler fehl, der Index bleibt auf dem letzten erfolgreichen Stand, weil `meta.json` zuletzt ersetzt wird. Trotzdem aktiv wachen: vor jedem Sammel-Commit `shutil.disk_usage()` pruefen und unterhalb einer Schwelle in den Zustand `paused_low_disk` gehen. Die Suche bleibt dabei lesend verfuegbar. Nach einem Absturz raeumt `writer.garbage_collect_files()` verwaiste Segmentdateien auf.

### Frage 2: Pull-Queue nach dem Vorbild context_chat

#### Das verifizierte Original

`context_chat` fuehrt `context_chat_queue` mit `id` (bigint, autoincrement), `file_id`, `storage_id`, `root_id`, `update` (boolean) und `locked_at`. Indizes: Primaerschluessel auf `id`, Index auf `file_id`, zusammengesetzter auf `(storage_id, root_id)` [VERIFIED: `lib/Migration/Version001000000Date20231102094721.php`, `lib/Db/QueueFile.php`].

Abholprotokoll (`QueueMapper`, `QueueController`):

1. `getFromQueue(n)` waehlt Zeilen mit `locked_at IS NULL` **oder** `locked_at <= now - LOCK_TIMEOUT`, sortiert nach `id ASC, update ASC`.
2. Fuer jede Zeile einzeln `lock($id)`: ein UPDATE mit derselben Bedingung im WHERE. Nur `executeStatement() >= 1` gewinnt die Zeile. Das ist die Zeilensperre, ohne `SELECT FOR UPDATE` und ohne Dialektabhaengigkeit.
3. Fuer jede gewonnene Zeile baut der Controller ein `Source`-Objekt und legt es unter der **Queue-ID** in die Antwort.
4. Wirft der Aufbau (Datei weg, Mount weg), wird die Zeile geloescht statt gesperrt zu bleiben.
5. Quittung per `DELETE /queues/documents` mit Queue-IDs, transaktional, in Baenden von 1.000.
6. `GET /queues/documents/stats` liefert `{scheduled, running}`.

#### Unser Schema, mit fuenf begruendeten Abweichungen

```php
$table = $schema->createTable('findling_queue');
$table->addColumn('id',         'bigint',  ['autoincrement' => true, 'notnull' => true, 'length' => 64]);
$table->addColumn('file_id',    'bigint',  ['notnull' => true,  'length' => 64]);
$table->addColumn('storage_id', 'bigint',  ['notnull' => true,  'length' => 64]);
$table->addColumn('root_id',    'bigint',  ['notnull' => true,  'length' => 64]);
$table->addColumn('is_update',  'boolean', ['notnull' => true,  'default' => false]);
$table->addColumn('size',       'bigint',  ['notnull' => false, 'length' => 64]);
$table->addColumn('locked_at',  'datetime',['notnull' => false]);
$table->addColumn('retries',    'smallint',['notnull' => true,  'default' => 0]);
$table->setPrimaryKey(['id'], 'findling_q_id');
$table->addUniqueIndex(['file_id'], 'findling_q_fileid');
$table->addIndex(['storage_id', 'root_id'], 'findling_q_stor');
$table->addIndex(['locked_at'], 'findling_q_locked');
```

Tabellen- und Indexnamen bleiben unter der Nextcloud-Grenze (Tabellen 27 Zeichen inklusive `oc_`, Indexnamen 30).

| # | Abweichung | Original | Unser Wert | Begruendung |
|---|---|---|---|---|
| 1 | Lock-Timeout | 24 Stunden | **15 Minuten** | Nach einem `docker kill` wartet der Batch sonst einen Tag. 15 Minuten sind weit mehr als die laengste Verarbeitung ohne OCR. Mit OCR in Phase 3 steigt der Wert oder wird pro Auftragsart unterschiedlich |
| 2 | Unlock | nicht vorhanden | `POST /queues/documents/unlock` mit ID-Liste, gerufen im SIGTERM-Handler | Ein geordneter Neustart ist sofort wieder produktiv; nur ein hartes Kill wartet den Timeout ab |
| 3 | Dedup | Select vor dem Insert | **Unique-Index auf `file_id`** plus `ON CONFLICT (file_id) DO UPDATE SET is_update = ?, locked_at = NULL` | Der Vorher-Select ist ein Race zwischen parallelen Crawl-Jobs |
| 4 | Batchgrenze | nur `n` | zusaetzlich `max_bytes`, dafuer `size` in der Zeile | Ein Batch aus 32 grossen PDFs sprengt das RAM-Budget einer 4-GB-Box |
| 5 | Retry | TODO-Kommentar | Spalte `retries`, Abbruch bei 3 als `failed(repeatedly_stuck)` | IDX-06 verlangt sichtbare Endzustaende statt ewig kreisender Zeilen |

Zusaetzlich `update` zu `is_update` umbenannt (reservierter Bezeichner).

**Endpunkte (alle `#[ExAppRequired]`):**

| Endpunkt | Verb | Parameter | Antwort |
|---|---|---|---|
| `/queues/documents` | GET | `n` (max 256), `max_bytes` | `{files: {queueId: Source}}` |
| `/queues/documents` | DELETE | `{files: [queueId], failed: [{queueId, reason}]}` | leer |
| `/queues/documents/unlock` | POST | `{ids: [queueId]}` | leer |
| `/queues/documents/stats` | GET | - | `{scheduled, running, failed}` |
| `/files/{fileId}` | GET | `userId` | StreamResponse (unveraendert aus Phase 1) |

Die `failed`-Liste im DELETE ist neu gegenueber context_chat und traegt IDX-06: der Container sagt beim Quittieren, welche Dateien er **nicht** verarbeiten konnte und warum, und die PHP-Seite schreibt das in eine Tabelle, aus der Phase 4 die Diagnose baut. Ohne diesen Rueckkanal muesste die Statusseite spaeter den Container fragen, und das waere ein zweiter Wahrheitsort.

**Das `Source`-Objekt** (Metadaten, kein Inhalt):

```json
{
  "files": {
    "8123": {"fileId": 4711, "storageId": 3, "rootId": 12,
             "path": "Documents/vertrag.pdf", "title": "vertrag.pdf",
             "mime": "application/pdf", "size": 184320, "mtime": 1755200000,
             "etag": "a1b2c3d4", "userIds": ["alice", "bob"],
             "fetchAs": "alice", "isUpdate": false}
  }
}
```

Der Schluessel ist die Queue-Zeilen-ID, weil genau die beim Quittieren zurueckgeht. `content` fehlt bewusst: Metadaten und Bytes reisen getrennt, damit die Queue-Antwort klein bleibt und der teure Abruf erst passiert, wenn ein Worker frei ist. `userIds` ist die ACL-Nutzlast, `fetchAs` der Nutzer, in dessen Kontext die Bytes geholt werden. **Wer lesen darf, um zu indexieren, und wer finden darf, sind zwei verschiedene Fragen** und bleiben zwei Felder. `etag` ist in Phase 2 ohne Funktion, gehoert aber jetzt ins Protokoll, damit Phase 3 nichts umbauen muss.

**Fehler- und Rueckstau-Semantik:**

| Situation | Container | PHP-Seite |
|---|---|---|
| Queue leer | Cooldown (Start 15 s, exponentiell bis 120 s) | - |
| Gateway 404 | als `skipped(gone)` quittieren | Zeile loeschen, Grund vermerken |
| Gateway 5xx oder Timeout | **nicht** quittieren, Batch abbrechen, Cooldown verdoppeln | Lock laeuft nach 15 min ab, Zeile kommt wieder |
| Extraktion wirft | als `failed(reason)` quittieren | Zeile loeschen, Fehlertabelle schreiben |
| Extraktion im Timeout | als `failed(timeout)` quittieren | wie oben |
| Datei zu gross oder Typ nicht erlaubt | gar nicht erst in der Queue | Filter sitzt im Crawl, Zustand wird trotzdem geschrieben |
| SIGTERM | offene IDs per `unlock` freigeben, dann beenden | Zeilen sofort wieder abholbar |
| Container aus | nichts | Queue waechst, `stats` zeigt es |

**Poller-Lebenszyklus.** Die Task startet im FastAPI-`lifespan` und wird von `enabled_handler` scharf- bzw. stillgestellt. Ein deaktiviertes Backend, das weiterpollt, ist der Klassiker aus der Integrationsliste.

**Gate-A-Konsequenz, die in den Plan muss.** Der bestehende AST-Test verbietet jeden `PUT/POST/PATCH/DELETE` gegen Nextcloud, ausser der Pfad steht in `OCS_WRITE_ALLOWLIST`, und die ist heute leer. Quittung und Unlock sind Schreibaufrufe:

```python
OCS_WRITE_ALLOWLIST = frozenset({
    "/ocs/v2.php/apps/findling/queues/documents",
    "/ocs/v2.php/apps/findling/queues/documents/unlock",
})
```

Das ist eine Aenderung an einem Sicherheitsgate und braucht laut Kommentar im Test eine Bedrohungsmodell-Notiz: beide Pfade schreiben ausschliesslich in die App-eigene Queue-Tabelle, nie in Nutzerdateien, und sie sind der einzige Rueckkanal. Die Erweiterung gehoert in einen eigenen, benannten Schritt, nicht als Nebeneffekt in einen Feature-Task.

### Frage 3: ACL-Befuellung und Crawl durch die PHP-Seite

#### Die Quelle

`IUserMountCache::getMountsForFileId(int $fileId)`, daraus `->getUser()->getUID()`. Das ist die einzige Stelle, die Freigaben, Gruppenfreigaben und Team Folders in einem Aufruf aufloest [VERIFIED: `context_chat/lib/Service/StorageService.php::getUsersForFileId`].

Warum nicht `IShareManager::getAccessList()`: braucht ein `Node`, arbeitet rekursiv ueber Elternordner und kennt nur Freigaben. Team Folders und externe Mounts fehlen darin, und fuer einen Crawl ueber Zehntausende Dateien ist es zu teuer.

**Kostenhinweis und die bewusste Entscheidung dagegen.** `UserMountCache::getMountsForFileId()` macht laut Quellcode zwei Abfragen plus ein `userExists()` je Datei. Bei 100.000 Dateien sind das rund 200.000 Abfragen. Die Optimierung waere, einmal je Mount `getMountsForStorageId()` zu holen und danach per Pfadpraefix zuzuordnen. **Empfehlung: in Phase 2 nicht.** Im Erstindex dominiert der Byteabruf jeder Datei ueber HTTP um Groessenordnungen, und die Praefixlogik nachzubauen ist genau die Art von Cleverness, die einen systematisch zu weiten Vorfilter erzeugt und damit die Ueberfetch-Strategie wirkungslos macht. Die Optimierung gehoert hinter eine Messung in Phase 5, mit einem Paritaetstest gegen die einfache Variante.

#### Die Mount-Allowlist

```php
private const MOUNT_PROVIDERS = [
    'OC\Files\Mount\LocalHomeMountProvider',      // User-Home, Datei-Backend
    'OC\Files\Mount\ObjectHomeMountProvider',     // User-Home, S3-Backend
    'OCA\GroupFolders\Mount\MountProvider',       // Team Folders
    // 'OCA\Files_External\Config\ConfigAdapter'  // External Storage: default AUS
];
```

Team Folders heissen seit NC 31 so, die App-ID ist weiterhin `groupfolders` und die Mount-Provider-Klasse unveraendert [VERIFIED: `nextcloud/groupfolders`, `appinfo/info.xml`: `<id>groupfolders</id>`, `<name>Team Folders</name>`]. Ob die App installiert ist, muss nicht geprueft werden: ist sie es nicht, gibt es keine Mounts dieser Klasse. External Storage bleibt draussen und wird in Phase 4 zu einem Schalter (ADM-04).

#### Die moderne Crawl-API, die den halben Legacy-Code spart

```php
foreach ($this->fileAccess->getDistinctMounts(self::MOUNT_PROVIDERS, true) as $mount) { ... }

foreach ($this->fileAccess->getByAncestorInStorage(
        $storageId, $overriddenRoot, $lastFileId, 2000, $mimeTypeIds, false, true) as $entry) { ... }
```

Beide `@since 32.0.0`, unser `min-version` ist 32 [VERIFIED: `nextcloud/server` `stable32` und `stable34`, `lib/public/Files/Cache/IFileAccess.php`]. Damit entfaellt der gesamte `getMountsOld`/`getFilesInMountOld`-Zweig samt der Reflection-Pruefung `isFileAccessAvailable()`, rund 150 Zeilen handgeschriebenes SQL und die dazugehoerige Dialektpflege.

`onlyUserFilesMounts: true` uebernimmt genau die Aufgabe, die context_chat sonst per Extraabfrage erledigt: der Home-Root wird auf den `files`-Ordner umgebogen, sodass `files_versions` und `files_trashbin` gar nicht erst auftauchen. Die beiden Booleans am Ende bedeuten "Ende-zu-Ende-verschluesselte nicht mitnehmen" (daraus bekaeme man nur Chiffrat) und "serverseitig verschluesselte mitnehmen" (die liefert das Gateway entschluesselt).

Der Groessenfilter fehlt in `getByAncestorInStorage`, nur Mimetypes werden gefiltert. Der 50-MB-Deckel wird also beim Einreihen geprueft; die Groesse liegt im `ICacheEntry`, kostet also nichts. Dateien darueber werden **nicht** stillschweigend uebergangen, sondern direkt als `skipped(too_large)` verbucht, sonst fehlt Phase 4 die Datenbasis.

#### Uebertragung und Invalidierung

**Phase 2 braucht keinen eigenen ACL-Weg.** Die Nutzerliste reist als `userIds` im `Source`-Objekt mit und wird im Container deklarativ geschrieben:

```sql
BEGIN;
DELETE FROM acl WHERE file_id = :file_id;
INSERT INTO acl (uid, file_id) VALUES (:uid, :file_id);  -- je Nutzer
COMMIT;
```

**Deklarativ, nicht inkrementell**, ist die entscheidende Eigenschaft: der Auftrag transportiert den Sollzustand, nicht die Aenderung. Ein verlorener Auftrag heilt sich bei der naechsten Zustellung, ein verlorenes Delta nie. Ein eigener Aktions-Endpunkt fuer reine Zugriffsaenderungen ohne Neuindexierung gehoert in Phase 3, wo Share-Events entstehen; das Schema traegt ihn ohne Aenderung.

**Bekannte Ueberapproximation, die dokumentiert gehoert:** Team Folders kennen erweiterte Berechtigungen auf Unterordnerebene, `IUserMountCache` loest sie nicht auf. Der Vorfilter kann also Kandidaten durchlassen, die der Nutzer im Team Folder nicht sehen darf. Das ist unschaedlich, weil der PHP-Recheck die Sicherheitsgrenze ist und **vor** jeder Snippet-Erzeugung laeuft, aber es ist der Grund, warum der Vorfilter nie als Grenze bezeichnet werden darf. In Phase 5 ist "Team Folder mit erweiterten Berechtigungen" ein Paritaets-Testfall, und zwar in beide Richtungen.

#### Anstoss des Erstindex (Claude's Discretion)

Empfehlung Auto-Start: ein `IRepairStep`, in `info.xml` unter `<repair-steps><install>` registriert, legt beim ersten Install einen `SchedulerJob` in die Jobliste und merkt sich das per App-Config, damit ein Deaktivieren und wieder Aktivieren nicht alles neu einreiht. Genau dieses Muster steht in `context_chat/lib/Repair/AppInstallStep.php`. Zusaetzlich `occ findling:index [--restart|--status]` als Notfallhebel fuer Support und CI.

**Wichtig fuer die Erwartung:** Hintergrundjobs brauchen einen laufenden Cron. Bei der Voreinstellung "AJAX" laufen sie nur, wenn jemand die Weboberflaeche benutzt, und der Erstindex tropft vor sich hin. Ein Zeitstempel "letzter Cron-Lauf gesehen" gehoert deshalb schon jetzt in die Datenbank, auch wenn die Anzeige Phase 4 ist.

### Frage 4: SQLite-Layout fuer den ACL-Vorfilter

#### Schema

```sql
-- $APP_PERSISTENT_STORAGE/state.db
PRAGMA journal_mode = WAL;
PRAGMA synchronous  = NORMAL;
PRAGMA busy_timeout = 10000;
PRAGMA foreign_keys = ON;

CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
-- schema_version, index_version, analyzer_version, wordlist_hash,
-- tantivy_version, instance_id, created_at

CREATE TABLE files (
    file_id       INTEGER PRIMARY KEY,          -- Nextcloud fileid
    storage_id    INTEGER NOT NULL,
    root_id       INTEGER NOT NULL,
    path          TEXT    NOT NULL,
    title         TEXT,
    mime          TEXT    NOT NULL,
    size          INTEGER NOT NULL,
    mtime         INTEGER NOT NULL,
    etag          TEXT,                         -- Phase 3 fuellt es
    content_hash  TEXT,                         -- ueberspringt unveraenderte Inhalte
    text_chars    INTEGER NOT NULL DEFAULT 0,
    state         TEXT    NOT NULL,             -- indexed | skipped | failed
    reason        TEXT,                         -- Grundcode, nie ein Dateiname
    attempts      INTEGER NOT NULL DEFAULT 0,
    ocr_used      INTEGER NOT NULL DEFAULT 0,   -- Phase 3, jetzt anlegen
    indexed_at    INTEGER,
    index_version INTEGER NOT NULL DEFAULT 0,
    deleted_at    INTEGER                       -- Phase 3 (Tombstone), bleibt NULL
);
CREATE INDEX files_state   ON files (state);
CREATE INDEX files_storage ON files (storage_id);

CREATE TABLE acl (
    uid     TEXT    NOT NULL,
    file_id INTEGER NOT NULL,
    PRIMARY KEY (uid, file_id)
) WITHOUT ROWID;
CREATE INDEX acl_file ON acl (file_id);          -- fuer den Loeschpfad

CREATE TABLE mounts (
    storage_id     INTEGER PRIMARY KEY,
    root_id        INTEGER NOT NULL,
    cursor_file_id INTEGER NOT NULL DEFAULT 0,   -- Spiegel, PHP fuehrt das Original
    files_seen     INTEGER NOT NULL DEFAULT 0,
    updated_at     INTEGER NOT NULL
);
```

`WITHOUT ROWID` bei `acl` ist der Kern: der zusammengesetzte Primaerschluessel **ist** die Tabelle, es gibt keinen zweiten B-Baum. Der Index auf `file_id` ist fuer den Loeschpfad noetig.

**Anschlussfaehigkeit:** Phase 3 braucht `etag` und `deleted_at`, beide sind da. Phase 6 haengt `chunks(chunk_id, file_id REFERENCES files(file_id) ON DELETE CASCADE, ...)` an, der Fremdschluessel funktioniert. `index_version` und `analyzer_version` sind der Hebel, mit dem ein Upgrade gezielt Teilmengen auf offen zuruecksetzt, statt alles zu loeschen.

#### Gemessene Groessen und Zeiten

100.000 Dateien, 50 Nutzer, im Mittel 3,36 Nutzer je Datei, SQLite 3.46.1:

| Variante | Zeilen | Datei | Byte/Zeile | Vorfilter 400 Kandidaten | Alle acl-Zeilen einer Datei loeschen |
|---|---|---|---|---|---|
| `uid TEXT` | 335.515 | **12,0 MB** | 35,7 | **0,18 ms** | 0,05 ms |
| Integer-Mapping | 335.500 | 7,4 MB | 22,0 | 0,21 ms | 0,12 ms |

Hochrechnung: 1 Mio. Dateien ergaeben rund 120 MB bei TEXT-uid, und das liegt jenseits der Zielhardware. **Empfehlung `uid TEXT`**, Integer-Mapping als dokumentierte Reserve.

**`SQLITE_LIMIT_VARIABLE_NUMBER` ist 250.000** in diesem Build, `IN`-Listen mit 40.000 Parametern laufen durch. Die alte 999er-Grenze aus vielen Anleitungen gilt hier nicht.

#### Die Abfrage

```sql
SELECT file_id FROM acl WHERE uid = ? AND file_id IN (?, ?, ...);
```

Das Ergebnis ist eine Menge, die Reihenfolge macht der Aufrufer nach dem Tantivy-Score. Kein `ORDER BY`, kein Join gegen `files` im heissen Pfad.

**Selektivitaet, ehrlich:** im synthetischen Testfall ueberlebten nur 31 von 400 Kandidaten. In der Realitaet sieht ein Nutzer den grossen Teil dessen, was in seinen Mounts liegt. Aber der Fall existiert, und die Antwort ist das begrenzte Nachfassen, nicht eine groessere erste Anfrage. Dokumentierte Reserve fuer Phase 5: ein `storage_id`-Filter in der Tantivy-Query aus den Mounts des Nutzers. Das ist eine Obermenge der sichtbaren Dateien, also sicher, und verbessert die Selektivitaet genau im Mehrnutzerfall.

#### Ein Schreiber, zwei Stores

Alle Schreibzugriffe laufen ueber eine Verbindung im Poller. Der Suchpfad bekommt eine eigene Verbindung mit `PRAGMA query_only = 1`, damit ein Fehler im Suchcode strukturell nichts kaputtmachen kann. WAL sorgt dafuer, dass die Suche waehrend der Indexierung nicht blockiert.

Zwei Vorbehalte gehoeren in den Code, nicht in die Doku. Erstens setzt WAL Shared Memory voraus, was auf manchen Netzwerkdateisystemen fehlschlaegt: `PRAGMA journal_mode=WAL` auswerten, bei abweichendem Rueckgabewert warnen und weiterlaufen. Zweitens der lokale Entwicklungsfall auf Windows: `scripts/dev/` startet die ExApp als Hostprozess, `APP_PERSISTENT_STORAGE` liegt auf NTFS. SQLite kann das, Tantivy hat dort aber eine dokumentierte Schwaeche (memory-mapped Dateien lassen sich unter Windows nicht loeschen, die Segment-Aufraeumung hinterlaesst Reste). Fuer lokale Proben kosmetisch, fuer belastbare Aussagen zu Indexgroesse und Aufraeumung ist die CI zustaendig.

### Frage 5: Fehlerklassen der Textextraktion

#### Gemessene Ausnahmen

Gegen `testdata/corpus/` und gegen praeparierte kaputte Eingaben, in `python:3.13-slim-trixie`:

| Eingabe | pypdf 6.16.1 | pypdfium2 5.13.0 (pdfium 153.0.7999.0) | Klassifikation |
|---|---|---|---|
| `01-text-layer.pdf` | `pages=1 encrypted=False` | `pages=1`, 63 Zeichen | `indexed` |
| `02-scan-no-text-layer.pdf` | `pages=1 encrypted=False` | `pages=1`, **0 Zeichen** | `skipped(no_text_layer)`, OCR-Kandidat fuer Phase 3 |
| `06-zero-bytes.pdf` | `pypdf.errors.EmptyFileError` | `PdfiumError: Data format error` | `failed(empty_file)` |
| `07-password-protected.pdf` | `pypdf.errors.FileNotDecryptedError` | `PdfiumError: Incorrect password error` | `skipped(encrypted)` |
| `%PDF-1.7` plus Muell | `pypdf.errors.PdfStreamError` | `PdfiumError: Data format error` | `failed(corrupt)` |
| abgeschnittene DOCX | `docx.opc.exceptions.PackageNotFoundError` | - | `failed(corrupt)` |
| XLSX, die kein ZIP ist | `zipfile.BadZipFile` (aus openpyxl) | - | `failed(corrupt)` |
| TXT (UTF-8) | - | `charset_normalizer` erkennt `utf_8` | `indexed` |

Wichtig fuer die Reihenfolge: `PdfReader(path)` wirft bei der passwortgeschuetzten Datei noch nicht, der Fehler kommt beim Zugriff auf `.pages`. Deshalb **zuerst `reader.is_encrypted` abfragen** und bei `True` sofort `skipped(encrypted)` melden, ohne pypdfium2 anzufassen. Genau so verlangt es CONTEXT.md.

#### Extraktoren je Format

| Format | Aufruf | Fehlerklassen |
|---|---|---|
| PDF | `pypdf.PdfReader` und `.is_encrypted`, dann `pypdfium2.PdfDocument`, je Seite `get_textpage().get_text_bounded()`, Seite und Textpage schliessen | `skipped(encrypted)`, `failed(corrupt)`, `skipped(no_text_layer)` |
| DOCX | `python-docx`, Absaetze plus Tabellenzellen | `failed(corrupt)` |
| PPTX | `python-pptx`, Shapes mit `has_text_frame` | `failed(corrupt)` |
| XLSX | `openpyxl.load_workbook(read_only=True, data_only=True)`, `iter_rows(values_only=True)`, harte Zellgrenze 200.000 | `skipped(too_many_cells)`, `failed(corrupt)` |
| ODT/ODS/ODP | `zipfile` oeffnen, `content.xml` lesen, per lxml alle `text:p` und `text:h` einsammeln, **nie** `extractall()` | `failed(corrupt)`, `failed(xml_invalid)` |
| HTML | `lxml.html.fromstring`, `script` und `style` entfernen, `text_content()` | `failed(xml_invalid)` |
| RTF | `striprtf.rtf_to_text(text, errors="ignore")` | `skipped(empty_text)` bei Unsinn |
| TXT/MD/CSV | `charset_normalizer.from_bytes(...).best()`, bei `None` UTF-8 mit `errors="replace"` | `failed(encoding_unknown)` |

#### Die Zustaende

`state` und `reason` in `files`. Englische Bezeichner, weil sie Code sind; die deutsche Beschriftung entsteht in Phase 4.

| state | reason | Bedeutung | Erneut versuchen? |
|---|---|---|---|
| `indexed` | NULL | Text im Index | - |
| `indexed` | `truncated` | Text ueber dem Zeichendeckel abgeschnitten | nein |
| `skipped` | `too_large` | ueber dem 50-MB-Deckel | nur nach Aenderung des Deckels |
| `skipped` | `mime_not_allowed` | nicht in der Allowlist | nur nach Aenderung der Allowlist |
| `skipped` | `encrypted` | passwortgeschuetzt | nein |
| `skipped` | `no_text_layer` | PDF ohne Textebene | **ja, in Phase 3 durch OCR** |
| `skipped` | `empty_text` | Extraktion lief, lieferte nichts | nein |
| `skipped` | `too_many_cells` | Zellgrenze ueberschritten | nein |
| `skipped` | `gone` | Datei zwischen Einreihen und Abruf verschwunden | nein |
| `failed` | `empty_file` | 0 Byte | nein |
| `failed` | `corrupt` | Parser-Ausnahme | nein |
| `failed` | `xml_invalid` | XML- bzw. HTML-Parserfehler | nein |
| `failed` | `encoding_unknown` | Kodierung nicht bestimmbar | nein |
| `failed` | `timeout` | Kindprozess ueber dem Zeitdeckel | einmal, dann nie |
| `failed` | `out_of_memory` | `RLIMIT_AS` gegriffen | einmal, dann nie |
| `failed` | `gateway_error` | Content-Gateway hat nicht geliefert | **ja**, Transportfehler |
| `failed` | `repeatedly_stuck` | dreimal gesperrt, nie quittiert | nein |

Die Trennung ist inhaltlich: `skipped` heisst "wir haben entschieden, das nicht zu indexieren", `failed` heisst "wir wollten, konnten aber nicht". Nur `failed` ist ein Fehler im Sinne der Statusseite, nur `skipped(no_text_layer)` ist eine offene Zukunftsaufgabe. Diese Unterscheidung ist die eigentliche Nutzlast von IDX-06.

`no_text_layer` ist die Bruecke zu Phase 3 und **muss** jetzt entstehen, sonst braucht Phase 3 einen vollstaendigen Reindex, nur um zu erfahren, welche PDFs OCR brauchen.

#### Deckel und ihre Durchsetzung

| Deckel | Startwert | Durchgesetzt wo |
|---|---|---|
| Dateigroesse | 50 MB | Crawl (PHP), beim Einreihen |
| Batchgroesse | 32 Dateien **oder** 64 MB | `GET /queues/documents?n&max_bytes` |
| Extraktionszeit je Datei | 120 s | `Process.join(timeout)` plus `kill()` |
| Adressraum des Kindprozesses | 512 MB | `resource.setrlimit(RLIMIT_AS, ...)` |
| Extrahierter Text je Dokument | 512 kB Zeichen | im Extraktor, danach `truncated` |
| XLSX-Zellen je Datei | 200.000 | Zaehler in der `iter_rows`-Schleife |
| PDF-Seiten je Datei | 500 | Schleifenabbruch, danach `truncated` |
| Freier Platz vor dem Commit | 500 MB bzw. 5 Prozent | `shutil.disk_usage()`, sonst `paused_low_disk` |

Gemessen: `RLIMIT_AS` von 300 MB liefert im Kind einen `MemoryError` (Exitcode 0, weil abgefangen), `kill()` auf einen haengenden Prozess liefert Exitcode -9. Der Elternprozess unterscheidet beide Faelle.

**Nur-Lesen bleibt strukturell wahr:** die Temporaerdatei liegt in `$APP_PERSISTENT_STORAGE/tmp/`, wird im `finally` geloescht, und beim Start werden Reste des letzten Absturzes entfernt. Keine Bibliothek bekommt je einen Pfad in den Nextcloud-Speicher zu sehen, denn den gibt es im Container nicht.

#### Bekannte Luecken, die dokumentiert und nicht behoben werden

- `python-docx` liefert keine Kopf- und Fusszeilen, keine Fussnoten, keine Textfelder. Wenn es stoert, `word/header*.xml` und `word/footnotes.xml` per lxml nachlesen. Nicht in Phase 2.
- `striprtf` wirft nicht, es liefert bei kaputtem RTF Unsinn. Ein Plausibilitaetsdeckel (Anteil nicht druckbarer Zeichen) ist die einzige Verteidigung, `empty_text` der ehrliche Zustand.
- Legacy-Formate (DOC, XLS, PPT) sind ausserhalb v1 und landen als `skipped(mime_not_allowed)`. Dokumentierte Nicht-Unterstuetzung ist ehrlicher als eine wacklige Kruecke.

### Frage 6: E2E-Test in der bestehenden CI

Die bestehende `integration.yml` hat zwei Jobs, `walking-skeleton` und `readonly-gate`, beide mit identischem Aufbau. **Beide bleiben unveraendert.** Der Durchstich aus Phase 1 ist die Regressionsprobe fuer die Integration und darf nicht umgebaut werden.

Neu kommt ein dritter Job `index-search-e2e` dazu, der denselben Aufbau wiederverwendet und danach sechs Dinge beweist.

**1. Dateien anlegen.** Weiterhin `cp -r` plus `occ files:scan --all`; ein WebDAV-Upload waere realistischer, kostet aber pro Datei einen Request und bringt fuer die Indexfrage nichts. Der Korpus wird **erweitert**, nicht geaendert (CONTEXT.md): neue Dateien mit deutschem Behoerdentext (Kündigungsfrist, Grundstücksverkehrsgenehmigung, Sitzungsvorlage), dazu DOCX, ODT und XLSX. `testdata/corpus/** -text` in `.gitattributes` gilt weiter. Gemessen: pdfium liest cp1252-Umlaute aus einem stdlib-erzeugten PDF auch ohne `/Encoding` korrekt, trotzdem gehoert `/Encoding /WinAnsiEncoding` explizit hinein, damit die Datei nicht von der Nachsicht des Parsers abhaengt.

**2. Crawl deterministisch anstossen.** Hintergrundjobs laufen in dieser CI nicht von selbst. Verfuegbar sind `background-job:list`, `background-job:execute <id> --force-execute` (ignoriert den geplanten Zeitpunkt, genau das braucht man, weil `scheduleAfter` sonst wartet) und `background-job:worker [job-class]` mit `--once` bzw. `--stop-after` [VERIFIED: `nextcloud/server` `stable34`, `core/Command/Background/*`].

```bash
./occ findling:index --restart
timeout 60  ./occ background-job:worker 'OCA\Findling\BackgroundJobs\SchedulerJob'   --once
timeout 300 ./occ background-job:worker 'OCA\Findling\BackgroundJobs\StorageCrawlJob' --stop-after 120
```

**3. Auf Fertigstellung warten, nicht schlafen.** Pollen auf `GET /queues/documents/stats` und den `/status`-Endpunkt der ExApp, bis Queue leer und nichts mehr offen ist, mit hartem Zeitlimit und dem Ausdruck beider Zaehler beim Fehlschlag.

**4. Deutsche Suchen asserten**, ueber die normale OCS-Suchroute wie in Phase 1, mit `jq -e`. Mindestens: Kompositum ueber ein Teilwort (`Genehmigung` findet die Grundstücksverkehrsgenehmigung), Umlautvariante, Nominalflexion, Phrase, Ausschluss mit `-`, Dateityp, und die Klartextprobe (`subline | contains("<") | not`).

**5. ACL negativ.** Ein zweiter Nutzer ohne Zugriff sucht denselben Begriff und bekommt null Treffer. Das ist die einzige Assertion, die den Unterschied zwischen "Index funktioniert" und "Rechte funktionieren" zeigt.

**6. Kill-Resume statt Behauptung.** In der CI laeuft die ExApp als Prozess, `kill -9 $(cat exapp.pid)` ist semantisch dasselbe wie `docker kill` (SIGKILL, keine Aufraeumarbeit), und `APP_PERSISTENT_STORAGE` bleibt bestehen. Ablauf: Crawl starten, warten bis einige Dokumente fertig und andere offen sind, SIGKILL, neu starten, warten bis nichts mehr offen ist. Danach pruefen: die vor dem Kill erreichte Zahl fertiger Dokumente ist nach dem Neustart nicht kleiner, die Summe der Zustaende entspricht der Dateizahl, und **kein** Dokument liegt doppelt im Index (Zaehlabfrage auf `file_id`).

**Zwei Rahmenpunkte.** Phase 2 fuehrt die erste eigene Tabelle ein, und `IQueryBuilder`-Fehler sind dialektabhaengig: ein zweiter Matrixeintrag mit MariaDB oder PostgreSQL gehoert in diesen Job, notfalls nur im `schedule`-Lauf. Und der Job wiederholt einen kompletten Nextcloud-Aufbau von mehreren Minuten, laeuft also pfadgefiltert wie die anderen; die volle Serverversionsmatrix kommt erst in Phase 5.

### Frage 7a: Snippet-Markup, die Fortsetzung des Phase-1-Befunds

Der Phase-1-Befund gilt unveraendert: die Unified-Search-UI interpoliert die Subline als Text, HTML erscheint woertlich. `SnippetGenerator` bietet `to_html()` mit `<b>`-Auszeichnung; **diese Methode wird nie aufgerufen**. Verwendet werden `fragment()` und `highlighted()`.

**Der neue Befund:** `Snippet.highlighted()` liefert Bereiche in **UTF-8-Bytes**, relativ zum Anfang von `fragment()`.

- Quellcode: tantivy-py dokumentiert es woertlich ("the byte ranges within that fragment that matched the query"), und in Tantivy sind `Token.offset_from` und `offset_to` als "Offset (byte index)" definiert, die Fragmentauswahl macht `&text[fragment.start_offset..fragment.stop_offset]`, also Rust-Byte-Slicing [VERIFIED: `tantivy-py/src/snippet.rs`, `tantivy/src/snippet/mod.rs`, `tantivy/tokenizer-api/src/lib.rs`].
- Messung: fuer `"Sehr geehrte Damen und Herren, die Kündigungsfrist für Ihren Vertrag ..."` liefert Tantivy `(35, 51)`. In Zeichen waere es `(35, 50)`. Ein naives `fragment[35:51]` ergibt `"Kündigungsfrist "` mit einem Leerzeichen zu viel.

**Konsequenz fuer das eingefrorene Protokoll.** `backend/src/findling/api/search.py` dokumentiert `highlights` heute als Zeichenoffsets. Diese Zusage bleibt, und der Container rechnet um. **Der Test dazu muss einen Umlaut vor der Fundstelle haben**, sonst ist er gruen, egal ob umgerechnet wird, und dokumentiert nichts.

**Drei weitere Snippet-Details:**

- Die Bereiche koennen sich **wiederholen und ueberlappen**, weil alle Teiltoken eines zerlegten Kompositums die Offsets des Originals erben. Vor dem Versand sortieren und verschmelzen.
- Weil die Teiltoken die Offsets des Kompositums erben, markiert eine Suche nach "Genehmigung" die vollstaendige "Grundstücksverkehrsgenehmigung" (gemessen `(0, 31)` in Bytes fuer ein 30 Zeichen langes Wort). Das ist gutes Verhalten und gehoert in einen Test, damit es niemand fuer einen Fehler haelt.
- `set_max_num_chars(n)` ist trotz des Namens ein **Byte**-Vergleich im Fragmentierer (`(next.offset_to - fragment.start_offset) > max_num_chars`), obwohl der Doc-Kommentar "characters (not bytes)" behauptet. Bei deutschem Text ist das Fragment also etwas kuerzer als die Zahl vermuten laesst. Vorschlag 200 statt der Vorgabe, damit ein deutscher Satz hineinpasst.

### Frage 7b: AppAPI-Proxy-Timeout, Grenzen und Konfigurierbarkeit

Vollstaendig aus dem Quellcode beantwortet [VERIFIED: `nextcloud/app_api`, `lib/Service/AppAPIService.php`]:

| Frage | Antwort |
|---|---|
| Wo setzt man den Timeout? | Sechster Parameter `$options` von `exAppRequest()`, Schluessel `timeout`, in Sekunden, unveraendert an Guzzle durchgereicht |
| Default | **3 Sekunden**, an zwei Stellen gesetzt |
| Obergrenze in AppAPI | **keine**. AppAPI selbst benutzt 60 s beim Aktivieren und Deaktivieren einer ExApp |
| Was begrenzt sonst? | PHP `max_execution_time` und der Webserver-Timeout, beides Instanzsache und weit ueber unserem Wert |
| Verhalten beim Timeout | Guzzle wirft, AppAPI faengt und liefert `['error' => 'cURL error 28: ...']`. Es fliegt keine Ausnahme nach oben |
| 4xx und 5xx | `http_errors` ist hart `false`, sie kommen als normales `IResponse`. Statuscode explizit pruefen |
| Asynchrone Alternative | `requestToExAppAsync()` mit `IPromise` existiert; fuer Phase 2 unnoetig, aber der Ausweg, falls die zwei Roundtrips zu teuer werden |

**Budgetierung.** Der bisherige Wert von 2 s galt fuer einen Aufruf. Bei zwei Aufrufen waeren es im schlimmsten Fall 4 s. Der Browser stellt pro Provider einen eigenen Request, ein langsamer Provider blockiert also keinen anderen, laesst aber die Ergebnisgruppe drehen und belegt einen PHP-Worker.

| Aufruf | Timeout | Begruendung |
|---|---|---|
| `POST /search` | **1,5 s** | Gemessene Arbeit unter 5 ms; 1,5 s deckt Proxy und Kaltstart |
| `POST /snippets` | **1,5 s** | Gemessene Arbeit 4,2 ms fuer 20 Snippets |
| Gesamtdeckel im Provider | **2,5 s Wanduhr** | Ist das Budget nach dem Recheck aufgebraucht, entfaellt `/snippets` und die Treffer erscheinen ohne Snippet statt gar nicht |

**Der Kanarien-Treffer (Claude's Discretion).** Empfehlung: behalten, aber einsperren. Der Container liefert ihn nur noch bei dem exakten Suchbegriff `findling-canary`. Damit bleibt der Phase-1-Job `walking-skeleton` unveraendert gruen (er sucht genau diesen Begriff), normale Suchen sehen ihn nie, und die Diagnose "kommt die Antwort aus dem Container" bleibt fuer immer verfuegbar. Der reservierte Begriff gehoert in `docs/`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Deutsche Komposita zerlegen | Eigener rekursiver Splitter | `Filter.split_compound()` | Zerlegt Index **und** Anfrage mit derselben Regel; Aho-Corasick in Rust gegen eine Python-Rekursion pro Token |
| Deutsches Stemming und Umlaut-Faltung | Eigene Suffixregeln, `str.translate` | `Filter.stemmer("german")` | Snowball ist der Referenzalgorithmus und faltet Umlaute und ß selbst |
| Stoppwoerter | Eigene Liste | `Filter.stopword("german")` | Gepflegt und an der richtigen Stelle der Kette |
| Suchoperatoren (Phrase, +/-, Feld, Typ) | Eigener Parser auf dem Suchbegriff | `Index.parse_query_lenient(...)` | Alle vier Faelle gemessen abgedeckt, plus Fehlertoleranz und Feldgewichte |
| Trefferausschnitt | Eigene Fenstersuche im Text | `SnippetGenerator` | Kennt die tatsaechlich getroffenen Terme aus der Query inklusive Analyzer, nicht nur die Eingabezeichenkette |
| Mounts und Dateien je Mount aufzaehlen | `CacheQueryBuilder`-SQL wie im Legacy-Pfad | `IFileAccess::getDistinctMounts()` und `getByAncestorInStorage()` | Ab NC 32 vorhanden; erspart rund 150 Zeilen SQL samt Home-Root-Umbiegung und E2E-Filter |
| "Wer sieht diese Datei" | Eigene Aufloesung ueber Shares und Gruppen | `IUserMountCache::getMountsForFileId()` | Ein zweites Rechtemodell driftet garantiert und verfehlt Team Folders |
| Zeilensperre in der Queue | `SELECT ... FOR UPDATE` oder eine Lock-Tabelle | UPDATE mit der Sperrbedingung im WHERE | Dialektunabhaengig und atomar; die Zahl betroffener Zeilen ist die Gewinnentscheidung |
| Deduplizierung der Queue | Select vor dem Insert | Unique-Index auf `file_id` plus Upsert | Der Select ist ein Race zwischen parallelen Crawl-Jobs |
| Zeitdeckel fuer die Extraktion | `signal.alarm`, Thread mit Flag | `multiprocessing.Process` plus `join(timeout)` plus `kill()` | Ein haengender C-Aufruf ist aus Python nicht unterbrechbar; Signale kommen nur im Hauptthread an; `ProcessPoolExecutor` kann nicht abbrechen |
| RAM-Deckel fuer die Extraktion | Selbstmessung mit `psutil` | `resource.setrlimit(RLIMIT_AS, ...)` im Kind | Der Kernel entscheidet, nicht die Anwendung |
| Absturzsicherheit des Index | Eigene Journal- oder Markerdateien | Tantivy-Commit plus Queue-Zeile in Nextcloud | Gemessen: `kill -9`, Index oeffnet auf dem letzten Commit, Writer sofort wieder erteilt |
| Encoding-Erkennung | `chardet` oder BOM-Heuristik | `charset-normalizer` | MIT statt LGPL, schneller, und deutsche Altbestaende sind der Regelfall |

**Key insight:** Fast alles, was in dieser Phase schwierig aussieht, ist in Tantivy, in `IFileAccess` oder in der Standardbibliothek geloest. Der Eigenanteil besteht aus vier Dingen: die richtige Wortliste, die richtige Filterreihenfolge, die richtige Reihenfolge der Commits und die Entscheidung, den Suchpfad in zwei Aufrufe zu teilen. Alles andere ist Verdrahtung.

---

## Common Pitfalls

### Pitfall 1: Die Wortliste wird roh benutzt, und "Frist" findet die Kündigungsfrist nicht

**Was schiefgeht:** Die deutsche Suche wirkt zunaechst gut, aber genau die langen Behoerdenkomposita, die das Produktversprechen tragen, sind nur als Ganzes findbar.
**Warum es passiert:** Eine Rechtschreibliste enthaelt tausende Komposita. `LeftmostLongest` greift das laengste Ganzwort ab, und die vollstaendige Zerlegung gelingt dann nicht mehr.
**Vermeidung:** Laengenfenster 4 bis 14, Fugenelemente als eigene Eintraege, und ein Tabellentest mit den sechzehn Komposita aus Frage 1 samt erwartetem Ergebnis.
**Warnzeichen:** Der Analyzer-Test prueft, **dass** zerlegt wird, statt **was**.

### Pitfall 2: `remove_long` steht vor dem Splitter, und lange Woerter verschwinden spurlos

**Was schiefgeht:** Ein 60-Zeichen-Kompositum ergibt eine leere Tokenliste. Das Dokument enthaelt das Wort, der Index nicht, und keine Suche findet es je.
**Warum es passiert:** `remove_long` gehoert intuitiv an den Anfang, und Tantivys eingebauter `default`-Analyzer setzt es mit Limit 40 tatsaechlich dorthin.
**Vermeidung:** `remove_long(48)` nach `split_compound`. Ein Testfall mit "Rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz" ist die billigste Absicherung, die dieses Projekt kaufen kann.
**Warnzeichen:** Die Kette folgt dem Aufbau von Tantivys `default`-Analyzer.

### Pitfall 3: Die Hervorhebung wandert bei Umlauten

**Was schiefgeht:** Bei "Kündigungsfrist" markiert die UI ein Zeichen zu weit rechts, bei mehreren Umlauten entsprechend mehr. Der Text bleibt richtig, nur die Markierung nicht, und niemand meldet es.
**Warum es passiert:** Tantivy zaehlt Bytes, Python und `mb_substr` zaehlen Zeichen.
**Vermeidung:** Umrechnung im Container, plus ein Test mit einem Umlaut **vor** der Fundstelle, plus das Verschmelzen ueberlappender Bereiche.
**Warnzeichen:** Der Snippet-Test benutzt einen englischen Satz.

### Pitfall 4: Der Tokenizer ist nach dem Oeffnen nicht registriert

**Was schiefgeht:** Nach einem Neustart wirft schon das Parsen der ersten Query `ValueError: The tokenizer ... is unknown`. Die Suche ist tot, der Index ist es nicht.
**Warum es passiert:** Das Schema speichert nur den **Namen** des Analyzers. Beim Anlegen registriert man ihn und vergisst es beim Oeffnen.
**Vermeidung:** Genau eine Funktion `open_index()`, die oeffnet und registriert; nirgends sonst ein `Index(...)` oder `Index.open(...)`. Ein Test, der den Index schliesst, neu oeffnet und sucht.
**Warnzeichen:** `Index.open(` kommt an mehr als einer Stelle im Code vor.

### Pitfall 5: Der Suchpfad liefert Snippets vor dem Recheck

**Was schiefgeht:** Ein Nutzer bekommt einen Textausschnitt aus einer Datei, die er nicht sehen darf, weil die Filterschleife einen Randfall hat.
**Warum es passiert:** Ein Aufruf ist einfacher als zwei, und die Verletzung faellt in keinem funktionalen Test auf, weil das Ergebnis am Ende gefiltert ist.
**Vermeidung:** Zwei Endpunkte, und das Antwortmodell von `/search` hat strukturell kein Textfeld.
**Warnzeichen:** Das Pydantic-Modell von `/search` hat ein Feld `snippet`.

### Pitfall 6: Zuerst quittieren, dann commiten

**Was schiefgeht:** Nach einem Absturz gilt eine Datei als indexiert, ist aber nicht im Index. Der stille Ausfall aus PITFALLS Nr. 2, bemerkt erst, wenn jemand etwas nicht findet.
**Warum es passiert:** Die Quittung fuehlt sich wie der Abschluss an.
**Vermeidung:** Feste Reihenfolge Tantivy-Commit, SQLite-Commit, Quittung, mit einem Kommentar an der Stelle. Ein Test, der zwischen Commit und Quittung abbricht und die erneute Zustellung prueft.
**Warnzeichen:** Die Quittung steht im selben `try`-Block wie die Verarbeitung.

### Pitfall 7: Der Lock-Timeout aus dem Vorbild wird uebernommen

**Was schiefgeht:** Der Abnahmetest "docker kill mitten im Lauf" sieht nach dem Neustart aus wie Stillstand: die gesperrten Zeilen kommen 24 Stunden lang nicht zurueck.
**Warum es passiert:** context_chat hat `LOCK_TIMEOUT = 60 * 60 * 24`.
**Vermeidung:** 15 Minuten als benannte Konstante, plus der Unlock-Endpunkt fuer den geordneten Neustart, plus ein Kommentar, dass OCR in Phase 3 den Wert anhebt.
**Warnzeichen:** Der Wert steht als magische Zahl in der Abfrage.

### Pitfall 8: Numerische Felder ueber Schluesselwortargumente

**Was schiefgeht:** `Document(file_id=42)` auf einem `unsigned`-Feld ergibt `ValueError: Schema error: 'Expected a U64 for field "file_id"'`, und je nach Aufrufweg erst spaeter und ohne Bezug zum verursachenden Dokument.
**Vermeidung:** Immer `doc.add_unsigned(...)` bzw. `Document.from_dict(payload, schema)`.
**Warnzeichen:** Dokumente werden aus einem Dict per Schluesselwortargumenten gebaut.

### Pitfall 9: `heap_size` unter 15 MB oder ein zweiter Writer

**Was schiefgeht:** Der Writer wird abgelehnt ("needs to be at least 15000000") oder liefert `LockBusy`.
**Warum es passiert:** Auf einer 4-GB-Box rechnet man den Heap klein, und ein zweiter Writer entsteht, wenn zwei Codestellen unabhaengig einen anlegen.
**Vermeidung:** 50 MB, `num_threads=1`, und der Writer lebt in genau einem Modul.
**Warnzeichen:** `index.writer(` kommt an mehr als einer Stelle vor.

### Pitfall 10: Der ACL-Vorfilter wird als Sicherheitsgrenze behandelt

**Was schiefgeht:** Irgendwann faellt auf, dass der PHP-Recheck Datenbankzugriffe kostet, und er wird "optimiert", weil die ExApp ja schon gefiltert hat.
**Warum es passiert:** Der Vorfilter sieht aus wie eine Rechtepruefung.
**Vermeidung:** Er heisst im Code `prefilter`, nie `check` oder `authorize`, und traegt einen Docstring, der das sagt. Dazu der Team-Folder-Fall als benannte Ueberapproximation.
**Warnzeichen:** Im Code steht "already checked in the backend".

### Pitfall 11: Die Extraktion laeuft im Hauptprozess

**Was schiefgeht:** Ein einziges kaputtes PDF haengt den Container, `/heartbeat` antwortet nicht mehr, AppAPI markiert die ExApp als unerreichbar, und die Suche ist weg.
**Warum es passiert:** Ein Kindprozess je Datei fuehlt sich teuer an.
**Vermeidung:** Prozessgrenze mit Timeout. Der Startaufwand ist gegenueber dem Netzwerkabruf der Datei vernachlaessigbar.
**Warnzeichen:** `/heartbeat` haengt, waehrend `/enabled` noch antwortet.

### Pitfall 12: Der Index waechst am Textdeckel vorbei

**Was schiefgeht:** Eine einzige 50-MB-PDF mit durchgehendem Text erzeugt zig MB gespeicherten Text, und bei einigen solchen Dateien ist das Volume voll.
**Warum es passiert:** Der Groessendeckel gilt fuer die Datei, nicht fuer den extrahierten Text.
**Vermeidung:** Zeichendeckel je Dokument mit sichtbarem Zustand `truncated`, dazu die Plattenwache vor dem Commit.
**Warnzeichen:** Es gibt genau einen Deckel, und der heisst `MAX_FILE_SIZE`.

### Pitfall 13: `parse_query` statt `parse_query_lenient`

**Was schiefgeht:** Ein Nutzer tippt ein Anfuehrungszeichen, der Parser wirft, die ExApp antwortet 500, und fuer den Nutzer ist die Suche kaputt.
**Vermeidung:** `parse_query_lenient` im Suchpfad, die Fehlerliste auf `debug` protokollieren, ohne den Suchbegriff.
**Warnzeichen:** Es gibt keinen Testfall mit unpaarigem Anfuehrungszeichen.

### Pitfall 14: Die Wortliste aendert sich, der Index nicht

**Was schiefgeht:** Ein Image-Update bringt eine andere `ngerman`-Version oder ein geaendertes Fenster. Anfragen werden anders zerlegt als der Index, und Treffer verschwinden ohne erkennbaren Grund.
**Warum es passiert:** Man denkt an die Tantivy-Version, nicht an die Wortliste.
**Vermeidung:** `wordlist_hash` und `analyzer_version` neben `schema_version` und `tantivy_version` in `meta`; Abweichung erzwingt einen Reindex, und der ist ein sichtbarer Zustand.
**Warnzeichen:** `meta` enthaelt nur `schema_version`.

### Pitfall 15: Ein Filter, den `getSupportedFilters()` nicht nennt

**Was schiefgeht:** Ein Client schickt `title-only`, und der Provider erscheint gar nicht im Ergebnis. Es sieht aus wie ein kaputtes Backend, ist aber eine Deklarationsluecke.
**Warum es passiert:** Ein Provider wird laut Interfacedokumentation uebergangen, wenn ein Client einen Filter sendet, den er nicht nennt.
**Vermeidung:** `getSupportedFilters()` vollstaendig fuehren, nicht sparsam, und einen CI-Fall mit gesetztem Filter.
**Warnzeichen:** `IFilteringProvider` ist implementiert, aber die Filterliste ist leer.

---

## Code Examples

### 1. Wortliste und deutsche Analysekette

```python
# backend/src/findling/index/analyzer.py
"""The German analysis chain. The order of the filters is the design decision."""

from pathlib import Path

from tantivy import Filter, TextAnalyzer, TextAnalyzerBuilder, Tokenizer

# Debian package wngerman, /usr/share/dict/ngerman, 356010 words, GPL-2+.
SYSTEM_WORDLIST = Path("/usr/share/dict/ngerman")

# A constituent dictionary, not a spell checker dictionary. Entries longer than
# MAX_LEN are compounds themselves, and a compound in the dictionary is never
# split: "Kuendigungsfrist" is 15 characters, stands in the raw list, and would
# swallow the whole token. Measured: this window scores 14 of 16 test compounds,
# the obvious "nouns plus appended linking forms" recipe only scores 7.
MIN_LEN, MAX_LEN = 4, 14

# German linking elements as entries of their own. Without them the chain of
# matches breaks between the parts and the whole word stays unsplit.
FUGEN = ("s", "es", "n", "en", "er", "ns")

# Any change below invalidates the index, so it is versioned next to the schema.
ANALYZER_VERSION = 1


def load_constituents(path: Path = SYSTEM_WORDLIST) -> list[str]:
    words = {
        word.lower()
        for word in path.read_text(encoding="utf-8", errors="replace").split()
        if word.isalpha() and MIN_LEN <= len(word) <= MAX_LEN
    }
    return sorted(words)


def german_analyzer(constituents: list[str]) -> TextAnalyzer:
    """lowercase -> split_compound -> stopwords -> remove_long -> stem.

    Two positions are load bearing and both are measured, not assumed.

    remove_long comes AFTER split_compound. In front of it, a 63 character
    compound is dropped whole and the document becomes unfindable under any of
    its parts; behind it, the same word yields six clean tokens.

    There is no ascii_fold. The Snowball stemmer for German folds umlauts and
    sharp s by itself, and folding before split_compound would make the
    dictionary, which carries umlauts, unmatchable.
    """
    return (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.split_compound([*constituents, *FUGEN]))
        .filter(Filter.custom_stopword(list(FUGEN)))
        .filter(Filter.stopword("german"))
        .filter(Filter.remove_long(48))
        .filter(Filter.stemmer("german"))
        .build()
    )
```

### 2. Der einzige erlaubte Weg, den Index zu oeffnen

```python
# backend/src/findling/index/open.py
def open_index(path: Path) -> Index:
    """Open the index and register the analyzers. Never call Index() elsewhere.

    The schema persists the *name* of a tokenizer, never the tokenizer. An index
    opened without registering answers the first parse_query with
    ValueError: The tokenizer '"de"' for the field '"body_de"' is unknown,
    which looks like a broken index and is a missing line of setup.
    """
    index = Index.open(str(path)) if Index.exists(str(path)) else Index(build_schema(), path=str(path))
    index.register_tokenizer("de", german_analyzer(load_constituents()))
    index.register_tokenizer("en", english_analyzer())
    index.register_tokenizer("name", name_analyzer())
    return index
```

### 3. Byte-Offsets in Zeichen-Offsets, verschmolzen

```python
# backend/src/findling/api/snippets.py
def char_ranges(fragment: str, snippet_ranges) -> list[tuple[int, int]]:
    """Tantivy reports UTF-8 byte ranges; the wire protocol promises characters.

    The ranges also repeat and overlap, because every part of a split compound
    inherits the offsets of the whole word, so they are merged here.
    """
    data = fragment.encode("utf-8")
    spans = sorted(
        (len(data[: r.start].decode("utf-8")), len(data[: r.end].decode("utf-8")))
        for r in snippet_ranges
    )
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
```

```python
# backend/tests/test_snippet_offsets.py
def test_umlaut_before_the_match_shifts_nothing() -> None:
    # One multi byte character before the match. Without the conversion the
    # naive slice would be off by exactly that one byte.
    fragment = "Die Kündigung betrifft die Frist"
    byte_start = len("Die Kündigung betrifft die ".encode())

    got = char_ranges(fragment, [_Range(byte_start, byte_start + len("Frist"))])

    assert fragment[got[0][0] : got[0][1]] == "Frist"
```

### 4. Query-Umschreibung fuer die ausgeschriebene Umlautform

```python
# backend/src/findling/query/rewrite.py
UMLAUTS = (("ue", "ü"), ("oe", "ö"), ("ae", "ä"), ("ss", "ß"))


def umlaut_variants(term: str) -> list[str]:
    """Return the term plus its umlaut spelling, if the two differ.

    The German stemmer folds umlauts, so "Mueller" and "Müller" both reduce well
    on their own, but they do not reduce to the *same* stem: one character
    against two. This is the query side answer, it costs no index space and a
    nonsensical variant only produces an empty branch.
    """
    variant = term
    for written, umlaut in UMLAUTS:
        variant = variant.replace(written, umlaut)
    return [term] if variant == term else [term, variant]
```

### 5. Die PDF-Reihenfolge: erst pypdf fragen, dann pdfium arbeiten lassen

```python
# backend/src/findling/extract/pdf.py
def extract_pdf(path: str) -> ExtractionOutcome:
    # pypdf answers the encryption question without touching the pages. Reading
    # .pages on a protected file raises FileNotDecryptedError, which would show
    # up as a failure instead of the deliberate decision it is.
    try:
        reader = pypdf.PdfReader(path)
        if reader.is_encrypted:
            return ExtractionOutcome.skipped(Reason.ENCRYPTED)
    except pypdf.errors.EmptyFileError:
        return ExtractionOutcome.failed(Reason.EMPTY_FILE)
    except pypdf.errors.PdfReadError:
        return ExtractionOutcome.failed(Reason.CORRUPT)

    try:
        document = pypdfium2.PdfDocument(path)
    except pypdfium2.PdfiumError:
        return ExtractionOutcome.failed(Reason.CORRUPT)

    try:
        parts = [
            document[i].get_textpage().get_text_bounded()
            for i in range(min(len(document), MAX_PAGES))
        ]
    finally:
        document.close()

    text = "\n".join(parts)
    if len(text.strip()) < NO_TEXT_LAYER_THRESHOLD:
        # Not a failure. This is the queue that phase 3 will work through.
        return ExtractionOutcome.skipped(Reason.NO_TEXT_LAYER)
    return ExtractionOutcome.indexed(text, truncated=len(document) > MAX_PAGES)
```

### 6. Extraktion hinter einer Prozessgrenze

```python
# backend/src/findling/extract/sandbox.py
CTX = mp.get_context("spawn")          # not fork: the parent runs an event loop
ADDRESS_SPACE_CAP = 512 * 1024 * 1024
WALL_CLOCK_CAP_SECONDS = 120


def _run(path: str, mime: str, pipe) -> None:
    # The kernel enforces the cap, not the application.
    resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE_CAP, ADDRESS_SPACE_CAP))
    from findling.extract.dispatch import extract

    try:
        pipe.send(extract(path, mime))
    except MemoryError:
        pipe.send(ExtractionOutcome.failed(Reason.OUT_OF_MEMORY))
    except Exception as error:  # noqa: BLE001 - the taxonomy lives in dispatch
        pipe.send(ExtractionOutcome.from_exception(error))


def extract_guarded(path: str, mime: str) -> ExtractionOutcome:
    """Never let one broken document take the container with it.

    A hanging call inside pypdfium2 or lxml cannot be interrupted from Python,
    signal.alarm only fires on the main thread, and ProcessPoolExecutor cannot
    cancel a running task. Only kill() works, and only on a process of its own.
    """
    parent, child = CTX.Pipe(duplex=False)
    proc = CTX.Process(target=_run, args=(path, mime, child), daemon=True)
    proc.start()
    proc.join(WALL_CLOCK_CAP_SECONDS)
    if proc.is_alive():
        proc.kill()
        proc.join()
        return ExtractionOutcome.failed(Reason.TIMEOUT)
    if not parent.poll():
        return ExtractionOutcome.failed(Reason.OUT_OF_MEMORY)
    return parent.recv()
```

### 7. Der ACL-Vorfilter, benannt als das, was er ist

```python
# backend/src/findling/store/repo.py
def prefilter_visible(self, uid: str, file_ids: list[int]) -> set[int]:
    """Drop candidates the user almost certainly cannot see.

    This is a speed-up, never a security boundary. It over-approximates on team
    folders with advanced permissions, because IUserMountCache resolves mounts
    and not per folder rules. The only authority is the PHP recheck through
    getUserFolder()->getFirstNodeById(), and it runs before any snippet exists.
    """
    if not file_ids:
        return set()
    placeholders = ",".join("?" * len(file_ids))
    rows = self._read.execute(
        f"SELECT file_id FROM acl WHERE uid = ? AND file_id IN ({placeholders})",  # noqa: S608
        (uid, *file_ids),
    )
    return {row[0] for row in rows}
```

### 8. Der Suchpfad in PHP, zweistufig und budgetiert

```php
#[\Override]
public function search(IUser $user, ISearchQuery $query): SearchResult {
    $deadline = hrtime(true) + 2_500_000_000;   // 2.5 s wall clock for this group
    $uid = $user->getUID();
    $approved = [];
    $offset = 0;

    // At most three rounds. An unbounded loop is exactly the failure mode that
    // makes query time permission filtering unusable.
    for ($round = 0; $round < 3 && count($approved) < $query->getLimit(); $round++) {
        $page = $this->exApp->searchCandidates($uid, $query->getTerm(), $query->getLimit() * 4, $offset);
        if ($page === null || $page['candidates'] === []) {
            break;
        }
        $offset = $page['nextOffset'];

        $userFolder = $this->rootFolder->getUserFolder($uid);
        foreach ($page['candidates'] as $candidate) {
            // The one and only security boundary.
            if ($userFolder->getFirstNodeById($candidate['fileId']) instanceof File) {
                $approved[] = $candidate['fileId'];
            }
        }
        if (!$page['hasMore']) {
            break;
        }
    }

    $approved = array_slice($approved, 0, $query->getLimit());
    // A hit without a snippet beats no hit at all.
    $snippets = (hrtime(true) < $deadline) ? $this->exApp->snippets($uid, $query->getTerm(), $approved) : [];

    return SearchResult::paginated($this->getName(), $this->toEntries($approved, $snippets), $offset);
}
```

### 9. Crawl-Job gegen die 32er-API

```php
protected function run($argument): void {
    $storageId  = (int)$argument['storage_id'];
    $rootId     = (int)$argument['overridden_root'];
    $lastFileId = (int)($argument['last_file_id'] ?? 0);
    $seen = 0;

    // getByAncestorInStorage filters mime types in SQL and skips end to end
    // encrypted files; the size cap is ours, because the API has none.
    foreach ($this->fileAccess->getByAncestorInStorage(
            $storageId, $rootId, $lastFileId, self::BATCH, $this->mimeTypeIds(), false, true) as $entry) {
        $lastFileId = max($lastFileId, $entry->getId());
        $seen++;
        if ($entry->getSize() > self::MAX_SIZE) {
            $this->failures->record($entry->getId(), 'skipped', 'too_large');   // never silent
            continue;
        }
        $this->queue->enqueue($entry, $storageId, $rootId);
    }

    if ($seen > 0) {
        $this->jobList->scheduleAfter(self::class, $this->time->getTime() + self::INTERVAL, [
            'storage_id' => $storageId, 'overridden_root' => $rootId, 'last_file_id' => $lastFileId,
        ]);
    }
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Filecache und Mounts per handgeschriebenem `CacheQueryBuilder`-SQL | `IFileAccess::getDistinctMounts()` und `getByAncestorInStorage()` | NC 32.0.0 | Der Legacy-Zweig aus context_chat entfaellt, inklusive Home-Root-Umbiegung, E2E-Filter und Reflection-Weiche |
| "Group Folders" | "Team Folders" (App-ID weiterhin `groupfolders`) | NC 31 | Nur die Beschriftung, nicht die Mount-Provider-Klasse. In Nutzertexten die neue Bezeichnung |
| `SearchResultEntry` mit HTML-Snippet | Klartext plus Offsets | Vue-Umbau der Unified Search | Phase-1-Befund, hier um die Byte-Offset-Falle ergaenzt |
| `IndexWriter.delete_documents(field, value)` | `delete_documents_by_term(...)` bzw. `delete_documents_by_query(...)` | tantivy-py 0.25/0.26 | Der alte Name loest eine `DeprecationWarning` aus, und `filterwarnings = ["error::DeprecationWarning"]` macht daraus einen Testfehler |
| `pypdfium2.get_text_range()` | `get_textpage().get_text_bounded()` | pypdfium2 4.x | Der alte Aufruf ist veraltet |
| SQLite-`IN`-Listen auf 999 Parameter begrenzen | `SQLITE_LIMIT_VARIABLE_NUMBER` liegt bei 250.000 | SQLite 3.32 (2020), im Image 3.46.1 | Die 999er-Regel gilt hier nicht; Bandbildung bleibt guter Stil |

**Deprecated/outdated:**
- `odfpy`: Release von 01/2020, keine Typannotationen, faellt durch das pyright-Gate. ODF per `zipfile` plus lxml-XPath ueber `text:p` und `text:h`.
- `chardet`: LGPL und langsamer als `charset-normalizer`.
- Die Sync-API von `nc_py_api`: faellt in 0.31.0 weg, der Poller ist von Anfang an async.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Docker | Test-Nextcloud, Messungen, Multi-Arch-Build | ja | 29.5.2 | - |
| uv | jede Python-Aktion | ja | 0.11.7 | - |
| git | Repo | ja | 2.54.0 | - |
| jq | lokale OCS-Proben | ja | 1.8.1 | - |
| slopcheck | Paketpruefung | ja | via uv tool | - |
| PHP | PHP-Gates, occ | **nein** | - | Verifikation ausschliesslich in der CI und im Nextcloud-Container, wie in Phase 1 etabliert |
| xmllint / xsltproc | info.xml-Validierung | **nein** | - | laeuft in `php.yml` |
| ctx7 (Context7-CLI) | Bibliotheksdokumentation | **nein** | - | Diese Recherche lief ueber Quellcode, PyPI-JSON-API, sources.debian.org und eigene Messungen. Kein Verlust |
| `wngerman` (Debian) | Komposita-Wortliste | ja im Zielimage | 20161207-15 in trixie | Keiner. Ohne die Liste faellt die Kompositazerlegung aus, das Produktversprechen mit ihr |

**Missing dependencies with no fallback:** keine.
**Missing dependencies with fallback:** PHP und die XML-Werkzeuge, beides in der CI abgedeckt.

Hinweis aus CONTEXT.md fuer lokale Proben: Port 8080 ist von einer parallelen Session belegt, `FINDLING_PORT=8090` verwenden.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V1 Architecture | ja | Genau eine Sicherheitsgrenze (`getUserFolder()->getFirstNodeById()`), im Code benannt; der SQLite-Vorfilter heisst `prefilter` und nirgends `check` |
| V2 Authentication | ja | Unveraendert aus Phase 1: Nutzer-ID nur aus dem signierten `AUTHORIZATION-APP-API`-Header, `AppAPIAuthMiddleware`, `set_user` durch Gate A verboten |
| V3 Session Management | nein | Keine eigene Session; AppAPI-Secret ist das einzige Credential |
| V4 Access Control | **ja, Kern der Phase** | PHP-Recheck je Treffer vor jeder Snippet-Erzeugung; `/snippets` zusaetzlich ACL-vorgefiltert gegen Confused Deputy; `#[ExAppRequired]` auf allen Queue-Endpunkten |
| V5 Input Validation | ja | Pydantic mit `extra="forbid"` auf jedem Request-Modell; `n` und `max_bytes` gedeckelt; `allow_regexes=False` |
| V6 Cryptography | nein | Keine Verschluesselung in v1 (Index-Verschluesselung ist v2-04) |
| V7 Error Handling and Logging | ja | Kein Suchbegriff, kein Dateiname, kein Snippet im Log. Nur Statuscodes, Zaehler und Grundcodes |
| V8 Data Protection | ja | Nur-Lesen-Invariante (Gate A und B) bleibt scharf; der Index liegt im App-Volume, kein Inhalt verlaesst den Server |
| V12 Files and Resources | ja | Allowlist nach Mimetype, Groessendeckel, Zeitdeckel, `RLIMIT_AS`, Plattenwache; kein Pfad reist ueber die Schnittstelle, nur `fileId` als Integer |
| V13 API and Web Service | ja | Alle Container-Endpunkte mit `access_level` USER in `info.xml`, nichts PUBLIC; `bruteforce_protection` nur auf 401 |

### Known Threat Patterns for diesen Stack

| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Nutzer-ID im Request-Body statt im Header | Spoofing / Elevation | `extra="forbid"` plus 400, aus Phase 1 uebernommen und weiterhin getestet |
| Confused Deputy auf `/snippets`: beliebige fileIds anfordern | Information Disclosure | ACL-Vorfilter auch auf `/snippets`, nicht nur auf `/search` |
| SQL-Injection ueber die Kandidatenliste | Tampering | Ausschliesslich Platzhalter; die Liste ist ohnehin intern erzeugt |
| Denial of Service ueber eine Regex-Suchanfrage | Denial of Service | `allow_regexes=False`, `parse_query_lenient`, `remove_long(48)` |
| Denial of Service ueber ein praepariertes Dokument (Zip-Bombe, PDF-Endlosschleife) | Denial of Service | Prozessgrenze mit `RLIMIT_AS` und `kill()`-Timeout; `openpyxl read_only` plus Zellendeckel |
| XML External Entity in ODF und HTML | Information Disclosure / SSRF | lxml-Parser mit `resolve_entities=False`, `no_network=True`, `load_dtd=False` |
| Zip-Slip beim Lesen von ODF und OOXML | Tampering | Nur `read()` aus dem Archiv, nie `extractall()`; es wird nichts entpackt |
| Schreibpfad schleicht sich ueber Quittung oder Unlock ein | Tampering | Gate A: die `OCS_WRITE_ALLOWLIST` bekommt genau zwei Eintraege, in einem eigenen Schritt mit Begruendung |
| Suchbegriffe oder Snippets im Log | Information Disclosure | Log-Regel aus Phase 1 fortschreiben; ein Test, der die Log-Ausgabe eines Suchlaufs auf den Suchbegriff prueft |
| Index-Volume enthaelt Klartext aller Dokumente | Information Disclosure | Bewusst akzeptiert (keine Index-Verschluesselung in v1). Gehoert in den Store-Text und in die Datenschutzaussage, nicht in eine stille Annahme |

Der letzte Punkt verdient eine ausdrueckliche Notiz: mit `stored=True` auf `body_de` liegt der vollstaendige extrahierte Text aller indexierten Dokumente im App-Volume. Fuer Snippets ist das unvermeidbar, aber ein Admin muss es wissen, insbesondere weil AIO-Sicherungen das Volume erfassen koennen (offener Punkt aus der Phase-5-Recherche).

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | Laengenfenster 4 bis 14 ist die richtige Justierung | Frage 1 | Gegen vier Rezepte und 16 Faelle gemessen, aber nicht gegen einen echten Korpus optimiert. Zu weit heisst weniger Zerlegung, zu eng heisst Ueberzerlegung (Rezept D) |
| A2 | Schwelle "unter 100 Zeichen im ganzen Dokument" erkennt ein Scan-PDF | Frage 5 | Ein PDF mit einer Deckblattzeile Text und 40 gescannten Seiten gaelte als `indexed` und wuerde in Phase 3 nie OCR-t. Besser waere eine Schwelle je Seite; Wert ungemessen |
| A3 | 15 Minuten Lock-Timeout reichen fuer jede Datei ohne OCR | Frage 2 | Zu kurz bedeutet Doppelverarbeitung (unschaedlich, weil idempotent, aber verschwenderisch), zu lang verzoegert den Wiederanlauf |
| A4 | 512 kB Zeichendeckel je Dokument ist ein sinnvoller Startwert | Frage 5 | Zu klein schneidet lange Ratsvorlagen ab, zu gross laesst den Index wachsen. `truncated` macht es sichtbar, der Wert ist geraten |
| A5 | 512 MB `RLIMIT_AS` reichen fuer jede erlaubte Extraktion | Frage 5 | Zu klein erzeugt falsche `out_of_memory`-Zustaende bei grossen legitimen Dateien |
| A6 | Zwei Proxy-Roundtrips bleiben in der Unified Search unauffaellig | Frage 7b | Gemessen ist nur die Arbeit im Container (unter 5 ms), nicht die Proxy- und HaRP-Latenz auf echter Hardware. `requestToExAppAsync` ist der Ausweg |
| A7 | 100k-Hochrechnungen fuer Index (560 MB) und ACL (12 MB) | Frage 1, Frage 4 | Aus gemessenen Faktoren hochgerechnet, nicht mit 100k echten Dokumenten gemessen. Lasttest ist Phase 5 |
| A8 | `getMountsForFileId` liefert bei Team Folders mit erweiterten Berechtigungen eine **Obermenge** | Frage 3 | Waere es eine Untermenge, verloeren berechtigte Nutzer Treffer. In Phase 5 in beide Richtungen pruefen |
| A9 | `getFirstNodeById` je Treffer kostet wenige Millisekunden | Frage 7b, Beispiel 8 | Bei 80 Kandidaten in drei Runden koennte das Budget knapp werden. In der CI messbar, hier nicht gemessen |
| A10 | Die Umlautvarianten-Umschreibung erzeugt keine relevanten Falschtreffer | Frage 1, Beispiel 4 | "neue" wird zu "neü"; erwartet ein leerer Zweig, aber ungemessen an einem echten Korpus |
| A11 | `spawn` statt `fork` kostet nur wenige hundert Millisekunden je Datei | Pattern 3 | Bei sehr vielen kleinen Dateien koennte der Startaufwand sichtbar werden. In einem fruehen Task messen |
| A12 | Rezept C (nur Substantive) spart rund zwei Drittel des Automaten-RAM | Alternatives Considered | Eintragszahl und Bauzeit sind gemessen (86.345 gegen 276.496, 0,18 s gegen 0,44 s), der RSS-Anteil ist daraus geschaetzt |

---

## Open Questions

1. **Wird die Verbform-Grenze (D2) akzeptiert oder gegengesteuert?**
   - Was wir wissen: Snowball fuer Deutsch behandelt Praeteritum und Partizip nicht. `suchte` und `gesucht` finden `suchen` nicht.
   - Was unklar ist: ob das Abnahmekriterium aus CONTEXT.md umformuliert wird oder ob ein anderer Stemmer geprueft werden soll.
   - Empfehlung: umformulieren. Der Ersatz eines Stemmers ist eine eigene Recherche mit ungewissem Ertrag, und Nominalflexion, Komposita und Umlaute decken den weit ueberwiegenden Teil deutscher Suchanfragen in Dokumentenbestaenden ab. Owner-Entscheid vor dem Bau.

2. **Wie wird der Erstindex ausgeloest, ohne dass ein kaputter Cron ihn still verhindert?**
   - Was wir wissen: Der Crawl braucht `IFileAccess`, laeuft also als PHP-Hintergrundjob ueber den Nextcloud-Cron. Bei der Voreinstellung "AJAX" laeuft er nur, wenn jemand die Weboberflaeche benutzt.
   - Was unklar ist: Zero-Config heisst, dass nach der Installation von selbst etwas passieren muss.
   - Empfehlung: `IRepairStep` beim Install plant den `SchedulerJob`, dazu `occ findling:index --restart` als Hebel und ein Zeitstempel "letzter Cron-Lauf gesehen" in der Datenbank. Die Anzeige ist Phase 4, die Datenerhebung muss jetzt entstehen.

3. **Welche Wortlistenvariante wird ausgeliefert?**
   - Was wir wissen: Rezept A trifft 14 von 16 und kostet rund 23 MB RSS, Rezept C trifft 12 von 16 bei einem Drittel der Eintraege.
   - Was unklar ist: wie viel RSS auf einer echten 4-GB-ARM-Box tatsaechlich frei ist, wenn OCR (Phase 3) und Embeddings (Phase 6) dazukommen.
   - Empfehlung: A als Vorgabe, C hinter `FINDLING_COMPOUND_DICT=nouns`, und die Entscheidung in Phase 5 gegen die Messung nachziehen.

4. **Wie kommt der `is_update`-Fall mit dem Unique-Index zusammen?**
   - Was wir wissen: Die Deduplizierung gehoert in den Index, nicht in einen Vorher-Select.
   - Was unklar ist: welche Upsert-Variante des Nextcloud-`IQueryBuilder` (`insertOrUpdate`, `insertIgnoreConflict`) ueber SQLite, MariaDB und PostgreSQL gleich traegt.
   - Empfehlung: in einem eigenen Task gegen zwei Dialekte verifizieren, bevor der Crawl gebaut wird.

5. **Braucht `body_en` seinen Platz?**
   - Was wir wissen: der nicht gespeicherte Indexanteil kostet gemessen nur 0,076 x des Textes.
   - Was unklar ist: ob deutsche Instanzen ihn nur mitschleppen.
   - Empfehlung: beide Felder bauen, `FINDLING_LANGUAGES=de,en` als Umgebungsvariable in der `info.xml`. Eine Zeile, und Phase 5 hat eine Stellschraube.

---

## Sources

### Primary (HIGH confidence)

**Eigene Messungen am 15.08.2026** (Container `python:3.13-slim-trixie`, `--memory=3g`, `tantivy==0.26.0`, Debian-Paket `wngerman`):
- Vier Wortlistenrezepte gegen 16 Komposita und 10 Nicht-Zerlege-Woerter; Eintragszahlen, Bauzeiten, Trefferquoten
- Filterreihenfolge: `remove_long(40)` vor dem Splitter loescht ein 63-Zeichen-Kompositum vollstaendig, `remove_long(48)` danach liefert sechs Teile; Stopwoerter greifen ohne `ascii_fold`
- Stemmerverhalten: Nominalflexion, ß, Umlaute, Verbformen, ausgeschriebene Umlautform
- Automaten-RAM (rund 23 MB), Bauzeit 0,44 s, Durchsatz 2,3 Mio. Token/s
- Snippet-Offsets: `(35, 51)` in Bytes gegen `(35, 50)` in Zeichen
- Query-Syntax: Phrase, `+`, `-`, `name:`, `ext:`, Umlaut-Aequivalenz gegen einen echten Index
- Indexgroesse 0,374 x (stored) und 0,076 x (unstored) des Textes; 2.123 Byte je Dokument; 1.675 Dokumente/s
- Suche 0,1 ms, 20 Snippets 4,2 ms, Ueberfetch 400 Kandidaten 4,2 ms
- Absturzfestigkeit: `kill -9` mitten im Schreiben, Index oeffnet auf dem letzten Commit (56.000 Dokumente), `.tantivy-writer.lock` bleibt liegen, Writer wird sofort wieder erteilt
- Fehlermeldungen: `heap_size` unter 15.000.000 abgelehnt, `LockBusy` beim zweiten Writer, `The tokenizer ... is unknown` nach `Index.open` ohne Registrierung, `Expected a U64 for field` bei Schluesselwortargumenten
- SQLite-ACL: 335.515 Zeilen = 12,0 MB (TEXT) bzw. 7,4 MB (Integer); Vorfilter 400 Kandidaten 0,18 ms; `SQLITE_LIMIT_VARIABLE_NUMBER` = 250.000; SQLite 3.46.1
- Extraktions-Fehlertabelle gegen `testdata/corpus/` und praeparierte kaputte Dateien
- `RLIMIT_AS` liefert `MemoryError`, `Process.kill()` liefert Exitcode -9
- pdfium liest cp1252-Umlaute aus einem stdlib-erzeugten PDF korrekt, mit und ohne `/Encoding /WinAnsiEncoding`

**Quellcode, direkt gelesen:**
- `quickwit-oss/tantivy-py`: `tantivy/tantivy.pyi`, `src/tokenizer.rs`, `src/snippet.rs`
- `quickwit-oss/tantivy`: `src/tokenizer/split_compound_words.rs`, `src/snippet/mod.rs`, `src/tokenizer/tokenizer_manager.rs`, `tokenizer-api/src/lib.rs`
- `nextcloud/server` `stable32` und `stable34`: `lib/public/Files/Cache/IFileAccess.php`, `core/Command/Background/*`, `lib/private/Files/Config/UserMountCache.php`, `lib/public/Share/IManager.php`, `lib/private/Search/SearchComposer.php`
- `nextcloud/context_chat`: `lib/Db/QueueFile.php`, `lib/Db/QueueMapper.php`, `lib/Service/QueueService.php`, `lib/Service/StorageService.php`, `lib/Controller/QueueController.php`, `lib/AppInfo/Application.php`, `lib/Repair/AppInstallStep.php`, `lib/Migration/Version001000000Date20231102094721.php`
- `nextcloud/app_api`: `lib/Service/AppAPIService.php`
- `nextcloud/groupfolders`: `appinfo/info.xml`
- Eigenes Repo: `backend/src/findling/{main,nc/client,api/search}.py`, `backend/tests/test_readonly_gate.py`, `php/lib/*`, `.github/workflows/integration.yml`, `scripts/dev/build_corpus.py`

**Registry- und Distributionsdaten:**
- PyPI-JSON-API fuer alle neun Pakete (Versionen, Daten, `requires_python`, Wheel-Plattformen), Stand 15.08.2026
- sources.debian.org: `igerman98/20161207-16/debian/copyright` (GPL-2+) und `debian/control` (Binaerpaket `wngerman`, `Architecture: all`)
- `slopcheck install ...` fuer alle neun Pakete: 9 OK

### Secondary (MEDIUM confidence)

- `.planning/research/ARCHITECTURE.md`, `STACK.md`, `PITFALLS.md`, `SUMMARY.md` (Muster, RAM-Budget, Sterbearten des Vorgaengers)
- `.planning/phases/01-integrationsbeweis/01-RESEARCH.md` (Integrationsprotokoll, Klartext-Subline, exAppRequest-Fehlerfaelle)
- Die vorige Fassung dieser Datei (Commit `c2f226a`), aus der die Befunde zu Stemmer-Grenzen, Tokenizer-Registrierung, Writer-Lock, `title-only`-Filter, `IRepairStep` und Windows-mmap uebernommen und nachgeprueft wurden
- j3e.de/ispell/igerman98 (Upstream-Lizenzhinweis "dual licensed ... GPL ... OASIS")

### Tertiary (LOW confidence)

- Keine. Alle Aussagen stuetzen sich auf Quellcode, Registry-Daten oder eigene Messungen. Was nicht belegt ist, steht im Assumptions Log.

---

## Metadata

**Confidence breakdown:**
- Analysekette, Wortliste und Filterreihenfolge: **HIGH** - vier Rezepte und beide Reihenfolgen gemessen, Lizenzkette aus dem Debian-Copyright belegt
- Stemmer-Grenzen D2 und D3: **HIGH** - direkt gemessen, betreffen zwei woertliche Abnahmekriterien
- Snippet-Offsets: **HIGH** - im Quellcode gelesen und am Beispiel mit Umlaut gemessen
- Tantivy-Betriebsverhalten (Lock, Reopen, Heap, Absturz): **HIGH** - alle vier Fehlermeldungen erzeugt
- Queue-Muster und Endpunkte: **HIGH** - Original im Quellcode gelesen, fuenf Abweichungen einzeln begruendet
- ACL-Beschaffung und Crawl-API: **HIGH** - `@since`-Annotationen und context_chat-Quellcode
- SQLite-Layout und -Groessen: **HIGH** fuer 100k gemessen, **MEDIUM** fuer die Millionen-Hochrechnung
- Extraktions-Fehlerklassen: **HIGH** fuer die gemessenen Faelle, **MEDIUM** fuer die Vollstaendigkeit der Taxonomie
- Zweistufiger Suchpfad und Latenzbudget: **MEDIUM** - die Arbeit im Container ist gemessen, die Proxy- und HaRP-Latenz nicht
- E2E-CI-Erweiterung: **MEDIUM** - die Bausteine sind verifiziert, der Job selbst existiert noch nicht

**Research date:** 2026-08-15
**Valid until:** 2026-09-15 fuer die Bibliotheksversionen (pypdf und charset-normalizer haben in dieser Woche veroeffentlicht); die Aussagen zu Tantivy-Semantik, Nextcloud-APIs und Lizenzen halten laenger

---
*Phase: 02-indexkern-und-volltextsuche*
*Researched: 2026-08-15*
