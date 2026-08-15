# Feature Research

**Domain:** Content-Suche für Nextcloud (OCR + Volltext + semantisch), Zielgruppe Selfhoster und kleine Organisationen
**Researched:** 2026-08-15
**Confidence:** MEDIUM-HIGH (Feature-Set der Bestandsapps aus Quellcode und Doku verifiziert = HIGH; Nutzerwünsche aus Foren/Issues = MEDIUM)

## Wichtiger Vorbefund: fulltextsearch ist nicht mehr tot

PROJECT.md geht davon aus, dass das offizielle Framework verwaist ist. Das stimmt für den Zeitraum 2021 bis Mitte 2026, aber nicht mehr für den aktuellen Stand:

| Repo | Letzter Commit | Neues Release | Wer arbeitet daran |
|------|----------------|---------------|--------------------|
| `nextcloud/fulltextsearch` | 2026-08-15 | `35.0.0beta1` (2026-08-12) | Carl Schwan, Kent Delante (Nextcloud GmbH), ArtificialOwl |
| `nextcloud/fulltextsearch_elasticsearch` | 2026-08-12 | `35.0.0beta1` (2026-08-12) | dieselben |
| `nextcloud/files_fulltextsearch` | 2026-08-12 | `35.0.0 beta 1` | dieselben |

Offene PRs von ArtificialOwl heißen "(wip) new sync service" und "(wip) files content provider" (#938, #939), es gibt also eine echte Überarbeitung, nicht nur Versions-Bumps. Zwischen 23.0.0 (2021) und 35.0.0beta1 (2026) gab es auf GitHub keine Releases, die Forenlage vom Juli 2026 ("nicht kompatibel mit NC 34/35, PRs liegen ungemergt") ist also gerade dabei zu kippen.

**Konsequenz für die Feature-Priorisierung:** "Wir sind das einzige Lebende" trägt nicht mehr als Alleinstellungsmerkmal. Was trägt: kein Elasticsearch, OCR eingebaut, semantische Suche, RAM-Budget kleiner Boxen, sichtbarer Indexstatus. Genau die Punkte, die das offizielle Framework auch nach der Wiederbelebung nicht liefert, weil es weiterhin einen externen Suchserver braucht und OCR über die seit Jahren kaputte Tesseract-Provider-App abwickelt.

## Feature Landscape

### Table Stakes (Users Expect These)

Diese Punkte sind der Vergleichsmaßstab, weil fulltextsearch plus Elasticsearch sie hatte oder weil die Nextcloud-Kernsuche sie hat. Fehlen sie, wirkt das Produkt kaputt.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Volltextsuche über Dateiinhalte (PDF, Office/ODF, Text, Markdown) | Kernversprechen, exakt das Set von `files_fulltextsearch` (`files_pdf`, `files_office`, `files_text` Defaults an, `files_zip` aus) | HIGH | Extraktion pro Mimetype, Fehler pro Datei isolieren |
| Dateiname und Pfad mitindexieren, nicht nur Inhalt | Nextclouds Kernsuche kann Dateinamen; eine Contentsuche, die Dateinamen schlechter findet, gilt als Rückschritt | LOW | `files_fulltextsearch` setzt Wildcards explizit auf das Feld `title` |
| Phrasensuche `"..."`, Pflichtterm `+wort`, Ausschluss `-wort` | Kann sowohl das Elasticsearch- als auch das SQL-Backend (MySQL Boolean Mode, PostgreSQL `websearch_to_tsquery`) | MEDIUM | Kleines, dokumentiertes Set statt Lucene-Vollsyntax, siehe Anti-Features |
| Trefferkontext (Snippet) mit hervorgehobenem Suchbegriff | Elasticsearch-Plattform liefert `highlight`; Nutzer beschweren sich nur über die Länge, nicht über die Existenz | MEDIUM | 100 Zeichen waren zu kurz (Issue #118, Forum 54820); Snippet muss um den Treffer zentriert sein, nicht mittendrin abgeschnitten (Kritik von jplitza) |
| Relevanzranking, nicht Datums- oder Namenssortierung | Selbstverständlichkeit jeder Suche; Paperless formuliert es als "scored list of results" | MEDIUM | BM25 aus der Engine; Hybridfusion siehe Differenzierer |
| Berechtigungsfilter zur Suchzeit (Eigentümer, Nutzer-Shares, Gruppen-Shares, Team Folders, Circles) | Harte Sicherheitsanforderung; context_chat verletzt sie ausdrücklich und wird dafür kritisiert | HIGH | Zugriffsrechte am Dokument speichern und bei jeder Query filtern, nie nachträglich in PHP aussieben |
| Treffer in geteilten Ordnern und Team Folders finden | War der häufigste Funktionsbruch der Altapp (Issues #250, #282, Forum 160044) | HIGH | Share-Änderungen müssen die Access-Metadaten rekursiv nachziehen |
| Jedes Dokument genau einmal indexieren, Nutzerbezug nur als ACL | Ein Nutzer berichtet 432.000 indexierte Dateien für 24 Nutzer bei einem geteilten Ordner (Forum 172909) | MEDIUM | Schlüssel ist die Nextcloud `fileid`, nicht der Pfad pro Nutzer |
| Inkrementelle Aktualisierung bei Anlegen, Ändern, Löschen, Umbenennen, Verschieben, Papierkorb, Share-Änderung | Altapp hatte dafür eigene Listener (`FileCreated`, `FileChanged`, `FileDeleted`, `FileRenamed`, `ShareCreated`, `ShareDeleted`, `TagAssigned`) | HIGH | Ohne Delete-Pfad tauchen gelöschte Dateien in Ergebnissen auf, ein klassischer Vertrauenskiller |
| Ausschlussregeln: Ordnermarker `.noindex`, Größenobergrenze, Mimetype-Schalter | Altapp-Verhalten und Standardrat in jedem Tutorial | MEDIUM | Default der Altapp: 20 MB Größenlimit; `.noindex` muss auch in geteilten Ordnern greifen, dort war es defekt |
| Indexstatus sichtbar: läuft, pausiert, Fortschritt, Fehlerzahl, letzter Lauf | Es gab dafür keine UI, Nutzer mussten `ps auxf` interpretieren (Forum 217460) | MEDIUM | Ohne diese Seite fühlt sich Zero-Config wie eine Blackbox an |
| Reindex-, Stop-, Resume- und Fehler-Reset-Werkzeuge | Altapp: `fulltextsearch:index`, `:stop`, `:reset`, `:live`, `index "{\"errors\": \"reset\"}"` | MEDIUM | Fehler müssen resetbar sein, sonst wiederholen sie sich bei jedem Lauf |
| occ-Kommandos für Admins (Index starten, Status, Reindex eines Pfads oder Nutzers) | Selfhoster arbeiten auf der Shell; die Altapp konnte `path`, `user`, `providers` als JSON-Optionen | LOW | Companion-App bietet occ, ExApp macht die Arbeit |
| Filter auf Dateityp beziehungsweise Endung und auf Fundort (Dateiname versus Inhalt) | Altapp bot `files_extension` und `in:filename` / `in:content` | MEDIUM | In der Unified Search als Filter, in der Query als Präfix |
| Nextcloud-Standardfilter `since`, `until`, `person` bedienen | Ab NC 28 über `IFilteringProvider` möglich, die Files-Provider nutzen zusätzlich `min-size`, `max-size`, `mime`, `type` | MEDIUM | Companion-App muss `IFilteringProvider` implementieren, sonst fehlen die Filterchips im neuen Suchdialog |
| Unicode-Robustheit: Groß- und Kleinschreibung, Umlaute, Akzente, Trennzeichen egal | Paperless bewirbt genau das ("accent-insensitive", "separator-agnostic"); deutsche Nutzer erwarten, dass `Grundstueck` und `Grundstück` beide treffen | MEDIUM | ICU-Folding beim Indexieren und beim Suchen identisch anwenden |
| Ergebnis öffnet die Datei oder den umgebenden Ordner, konfigurierbar | Altapp hatte dafür `files_open_result_directly` | LOW | Default: Datei direkt öffnen |
| Kein Endlos-Reindex, kein OOM-Abbruch | AIO-Nutzer berichten Endlosschleifen bis ans Speicherlimit (Discussion #1709, #1694) | HIGH | Fortschritt persistent, Resume nach Abbruch, Marker statt Neustart von vorn |
| Ressourcendeckel: Worker-Anzahl, CPU-Limit, Pausierbarkeit | Auf 4 bis 8 GB Boxen ist ein Indexlauf sonst ein Denial of Service gegen die eigene Cloud; Workflow OCR macht das CPU-Limit deshalb konfigurierbar | MEDIUM | Auch für OCR getrennt, OCR ist der teuerste Schritt |
| Definiertes, sichtbares Verhalten bei External Storage, verschlüsselten und passwortgeschützten Dateien | Altapp hatte `files_external` als eigenen Schalter; context_chat dokumentiert External Storage als unzuverlässig und verschlüsselte Dateien als ausgeschlossen | MEDIUM | Überspringen ist akzeptabel, stilles Überspringen ohne Grund nicht |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| OCR automatisch beim Indexieren, ohne Workflow-Konfiguration | Der dokumentierte Schmerzpunkt schlechthin: "OCR in Nextcloud, giving up after a month" (Forum 240122, 02/2026), Antwort im Thread: die Tesseract-Provider-App ist "broken since years" | HIGH | Text-Layer erkennen und OCR überspringen, wenn schon Text da ist (Issue #28 der Tesseract-App); Sprachen `deu` und `eng` vorinstalliert |
| OCR fasst die Originaldatei nicht an | Die alte Tesseract-App konnte PDFs zerstören, dazu gibt es eine ausdrückliche Warnung im Forum (93151); Workflow OCR schreibt die Datei um und verliert dabei PDF-Metadaten | MEDIUM | Extrahierter Text nur im Index, Originaldatei bleibt bitweise unverändert. Das ist ein Vertrauensargument, das man im App-Store-Text nennen sollte |
| Semantische Suche lokal, CPU-only, hybrid mit BM25 gemischt | Findet "Kündigung Mietvertrag", wenn im Dokument "Aufhebung des Mietverhältnisses" steht; deckt außerdem deutsche Komposita ab, an denen reine Tokensuche scheitert | HIGH | Reciprocal Rank Fusion aus Volltext- und Vektortreffern; Modellgröße ist das RAM-Budget-Risiko |
| Zero Config: ein Container, kein Suchserver, Erstindex startet selbst | Die gesamte Konkurrenz verlangt Elasticsearch (RAM-Fresser), Postgres plus pgvector (context_chat) oder einen zweiten Dienst | MEDIUM | Jede Pflichteinstellung, die man nicht wegbekommt, kostet die Kernaussage |
| RAM-Deckel und ARM-Tauglichkeit als Produktversprechen | context_chat verlangt laut Admin-Doku mindestens 12 GB RAM ohne GPU und rät zu einer dedizierten Maschine; Elasticsearch ist auf einem Raspberry Pi ein Dauerthema im Forum | HIGH | Harte Obergrenze messen und im App-Store-Text nennen, zum Beispiel "läuft in 1,5 GB" |
| Diagnose pro Datei: "Warum ist diese Datei nicht auffindbar?" | Der Aufgeber-Thread beschreibt exakt "silent failures": manuelle Tests klappen, die Automatik nicht, und niemand sieht warum | MEDIUM | Grund je Datei speichern: zu groß, Mimetype aus, `.noindex`, OCR-Timeout, Extraktionsfehler. In der Admin-UI durchsuchbar |
| Ehrliche Statusseite mit Zahlen statt Spinner | indexiert / ausstehend / fehlerhaft, OCR-Warteschlange, Indexgröße auf Platte, Restzeitschätzung | MEDIUM | Baut auf dem Table-Stakes-Statuspunkt auf und zieht ihn weiter |
| Vorab-Schätzung vor dem Erstindex | "42.000 Dateien, davon 3.100 zu OCRen, geschätzt 6 Stunden, etwa 900 MB Index" nimmt genau die Angst, die AIO-Nutzer in die Endlosschleife getrieben hat | MEDIUM | Reiner Zählauf über die Filecache-Tabelle, billig |
| Deutsch und Englisch out of the box, ohne Analyzer-Frickelei | Elasticsearch-Setup verlangt hier eine Analyzer-Entscheidung im Admin-UI; wir erkennen die Sprache pro Dokument | MEDIUM | Deutsches Stemming plus Kompositazerlegung; Semantik als zweites Netz |
| Pfadfilter und Suche im aktuellen Ordner | Recoll (`dir:`) und Paperless (`storage_path`) haben das; Nextcloud-Nutzer fragen es für den Files-Kontext nach | MEDIUM | Als Filter im Files-Suchdialog und als `path:` Präfix |
| Eigene Ergebnisseite mit Paginierung | Die Unified-Search-Liste verliert man beim Öffnen eines Treffers, der Vorgänger Nextant konnte das besser (Forum 29122) | MEDIUM | Kandidat für v1.1, nicht für v1 |
| Nextcloud-Tags als Filter und als Ausschlusskriterium | Die Altapp hörte bereits auf Tag-Events; Selfhoster nutzen Tags stark (Workflow OCR triggert darüber) | MEDIUM | "Ordner mit Tag `privat` nie indexieren" ist ein starkes DSGVO-Argument |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| RAG-Chat beziehungsweise generierte Antworten über Dokumente | "Wenn ihr schon Embeddings habt, macht doch auch Chat" | Braucht ein LLM, sprengt das RAM-Budget vollständig, ist context_chat-Terrain und macht uns für Halluzinationen haftbar | Suche liefern, Rangliste mit Belegstellen. Nextclouds Assistant-Spur bleibt ein anderes Produkt |
| Elasticsearch- oder OpenSearch-Backend als Option | "Große Instanzen brauchen das" | Genau die Setup-Qual, die wir abschaffen; zwei Backends bedeuten doppelte Query-Semantik, doppelte Tests, doppelten Support | Eine eingebettete Engine, klar kommunizierte Obergrenze der Instanzgröße |
| Volle Lucene-Syntax (Range, Proximity, Fuzzy, Boost, Feldsyntax) | Poweruser vergleichen mit Solr; im Forum gibt es einen Thread, der genau danach fragt (Search syntax FAQ) | Die Altapp hat das nie sauber dokumentiert und ist an Wildcard-Sonderfällen gescheitert (ES-Issue #379); jede Zusatzsyntax verdoppelt die Support-Last | Fünf Operatoren, die dokumentiert und getestet sind: Phrase, `+`, `-`, `path:`, `type:`. Alles Weitere über Filterchips |
| OCR schreibt den Textlayer in die Originaldatei zurück | Nutzer wollen die Datei auch außerhalb von Nextcloud durchsuchbar haben (Workflow OCR macht das) | Datenverlustrisiko mit Vorgeschichte (Forum 93151), Verlust von PDF-Metadaten, Versions-Explosion, Sync-Sturm auf allen Clients | Text nur im Index. Für den anderen Wunsch existiert Workflow OCR, wir verweisen darauf statt zu konkurrieren |
| Dokumentenmanagement: Korrespondenten, Dokumenttypen, Auto-Klassifizierung, Workflows | Paperless-Nutzer erwarten das Paket | Das ist ein anderes Produkt, es kollidiert mit Nextclouds Tags und mit Paperless selbst; die Forendiskussion fordert ausdrücklich gute Spezialintegrationen statt halbfertiger Eigenbauten | Nextcloud-Tags lesen und filtern, keine eigene Taxonomie einführen |
| Index in der Nextcloud-Datenbank ablegen | Klingt nach "keine zusätzliche Komponente" | `fulltextsearch_sql` verdoppelt laut eigener Doku die indexierten Inhalte in der DB, kann kein SQLite, kein Office-Format, und MySQL liefert Excerpts nur in Kleinschreibung | Eigener Index im persistenten Volume der ExApp, unabhängig von der Nextcloud-DB |
| Index komplett im RAM (Typesense-Modell) | Schnellste Latenz | Auf 4 bis 8 GB Boxen unmöglich, außerdem GPLv3-Konflikt; bereits als Out of Scope entschieden | On-Disk-Index mit mmap, RAM nur für Caches |
| Pro-Nutzer-Index (jeder Nutzer bekommt seinen eigenen Datensatz) | Wirkt wie die einfachste Umsetzung der Berechtigungen | Skaliert quadratisch mit Shares, siehe 432.000-Dateien-Fall; OCR würde für dieselbe Datei mehrfach laufen | Einmal indexieren, ACL-Filter zur Suchzeit |
| Externe Cloud-Embeddings oder Cloud-OCR als Komfortoption | Bessere Qualität, weniger CPU | Zerstört das Privacy-Versprechen, das bei dieser Zielgruppe das Kaufargument ist; bereits Out of Scope | Alles lokal, dafür kleineres Modell und ehrliche Qualitätsaussage |
| Sofortindex ohne Drosselung bei jeder Dateiänderung | "Es soll sofort auffindbar sein" | Ein Massenupload oder ein Desktop-Client-Erstsync erzeugt einen Sturm, der die Box lahmlegt | Ereignisgesteuerte Queue mit Backpressure, Sekundenlatenz im Normalbetrieb, automatische Drosselung unter Last |
| Treffer im geöffneten Dokument anspringen und markieren | Alter, populärer Wunsch (Issue #150) | Erfordert Viewer-Integration je Dateityp (PDF, Office, Text), also Arbeit in fremden Apps, mit hohem Bruchrisiko bei NC-Updates | Snippet mit Kontext und Seitenzahl bei PDFs anzeigen, Deeplink erst prüfen, wenn v1 steht |
| Weitere Quellen indexieren: Mailserver, externes S3, Webseiten | Naheliegende Erweiterung | Jede Quelle bringt ein eigenes Auth-, Berechtigungs- und Änderungsmodell; verwässert die Kernaussage | v1 nur Nextcloud-Files, wie in PROJECT.md festgelegt |

## Feature Dependencies

```
[Volltextsuche über Dateiinhalte]
    └──requires──> [Extraktionspipeline pro Mimetype]
                       └──requires──> [Ereignisgesteuerte Index-Queue mit Resume]
                                          └──requires──> [Indexstatus-Persistenz]

[OCR]
    └──requires──> [Extraktionspipeline pro Mimetype]
    └──requires──> [Textlayer-Erkennung (sonst OCR auf Digital-PDFs = Verschwendung)]
    └──requires──> [Ressourcendeckel/Throttling]   (OCR ist der teuerste Schritt)

[Semantische Suche]
    └──requires──> [Chunking der extrahierten Texte]
                       └──requires──> [Extraktionspipeline pro Mimetype]
    └──requires──> [Hybrid-Ranking (RRF)]
                       └──requires──> [Volltextsuche über Dateiinhalte]

[Berechtigungsfilter zur Suchzeit]
    └──requires──> [Access-Metadaten am Dokument (Owner, Users, Groups, Teams, Circles)]
                       └──requires──> [Share-Event-Listener mit rekursivem Nachziehen]

[Einmal-Indexierung pro fileid] ──enables──> [Berechtigungsfilter zur Suchzeit]
[Diagnose pro Datei] ──requires──> [Indexstatus-Persistenz mit Fehlergrund]
[Statusseite] ──requires──> [Indexstatus-Persistenz]
[Vorab-Schätzung] ──enhances──> [Zero-Config-Erstindex]
[Snippets] ──requires──> [Positionsdaten im Volltextindex]
[Snippets für Vektortreffer] ──requires──> [Chunk-Rückverweis auf Textstelle]

[NC-Standardfilter since/until/person] ──requires──> [IFilteringProvider in der PHP-Companion-App]
[Eigene Ergebnisseite] ──requires──> [Paginierbare Such-API der ExApp]

[Sofortindex ohne Drosselung] ──conflicts──> [Ressourcendeckel auf 4-8-GB-Boxen]
[OCR schreibt Original um] ──conflicts──> [Originaldatei unverändert lassen]
[Pro-Nutzer-Index] ──conflicts──> [Einmal-Indexierung pro fileid]
[Lucene-Vollsyntax] ──conflicts──> [Zero Config / geringe Support-Last]
```

### Dependency Notes

- **Semantische Suche erfordert Chunking, und Chunking erfordert die Extraktion:** Der Extraktionsschritt ist der gemeinsame Flaschenhals von Volltext, OCR und Semantik. Er gehört in eine frühe Phase und muss von Anfang an Fehler pro Datei isolieren, sonst reißt eine kaputte PDF den ganzen Lauf mit.
- **OCR erfordert Textlayer-Erkennung:** Ohne diesen Test läuft OCR über jedes digital erzeugte PDF und verbrennt auf einer ARM-Box Stunden. Die alte Tesseract-App hatte dafür ein offenes Issue (#28).
- **Berechtigungsfilter erfordert Share-Events mit rekursivem Nachziehen:** Der bekannteste Bug der Altapp war, dass Gruppen-Shares im Index leere Gruppenfelder hatten und Treffer deshalb verschwanden (Issue #250, #282). Das ist kein Detail, sondern die Funktion selbst.
- **Diagnose und Statusseite teilen sich denselben Datenspeicher:** Wer Indexstatus pro Datei mit Fehlergrund speichert, bekommt die Statusseite fast geschenkt. Diese beiden Features sollten in derselben Phase entstehen.
- **Drosselung steht im Konflikt mit gefühlter Sofortverfügbarkeit:** Auflösung ist eine Queue mit Prioritäten: kleine Textdateien sofort, OCR-Jobs in den Hintergrund mit niedriger Priorität.
- **Snippets für Vektortreffer sind nicht dasselbe wie Snippets für Volltexttreffer:** Beim Vektortreffer gibt es keinen wörtlichen Match, den man hervorheben könnte. Der Chunk selbst wird zum Snippet. Das muss die Ergebnisdarstellung aushalten.

## MVP Definition

### Launch With (v1)

- [ ] Volltextsuche über Inhalte von PDF, Office/ODF, Text und Markdown, Ergebnisse in der Unified Search
- [ ] Dateiname und Pfad mitindexiert und gewichtet
- [ ] Query-Syntax minimal: Phrase in Anführungszeichen, `+wort`, `-wort`
- [ ] Snippet mit Trefferkontext, um den Treffer zentriert, konfigurierbare Länge mit brauchbarem Default
- [ ] Relevanzranking, hybride Fusion aus Volltext und Vektor
- [ ] OCR für gescannte PDFs und Bilder mit Textlayer-Erkennung, Originaldatei bleibt unverändert, Sprachen deu und eng
- [ ] Semantische Suche lokal, CPU-only, Modell im Container
- [ ] Berechtigungsfilter zur Suchzeit inklusive Nutzer-Shares, Gruppen-Shares und Team Folders
- [ ] Ein Dokument pro fileid, keine Duplikate pro Nutzer
- [ ] Inkrementelle Indexierung über Dateiereignisse inklusive Löschen, Umbenennen, Verschieben, Papierkorb, Share-Änderung
- [ ] Ausschlüsse: `.noindex`-Ordnermarker, Größenobergrenze, Mimetype-Schalter
- [ ] Statusseite: läuft/pausiert, Fortschritt, Fehleranzahl, letzter Lauf, Indexgröße
- [ ] Diagnose pro Datei mit Ausschluss- oder Fehlergrund
- [ ] occ-Kommandos: Index starten, stoppen, fortsetzen, zurücksetzen, Fehler zurücksetzen, Pfad oder Nutzer neu indexieren
- [ ] Ressourcendeckel: Worker-Anzahl, RAM-Obergrenze, OCR-Drosselung, Resume nach Abbruch, kein OOM-Loop
- [ ] Unicode-Folding für Umlaute und Akzente, identisch bei Index und Query
- [ ] Zero-Config-Defaults: nach der Installation läuft der Erstindex ohne eine einzige Pflichteingabe

### Add After Validation (v1.x)

- [ ] Standardfilter der Unified Search bedienen: `since`, `until`, `person`, `mime`, Größe (Auslöser: Companion-App implementiert `IFilteringProvider`)
- [ ] Pfadfilter `path:` und "nur in diesem Ordner suchen" (Auslöser: erste Nutzer mit mehr als 50.000 Dateien)
- [ ] Vorab-Schätzung vor dem Erstindex (Auslöser: erste Beschwerde über unklare Laufzeit)
- [ ] Eigene Ergebnisseite mit Paginierung (Auslöser: Nachfrage nach mehr als den fünf Treffern der Unified Search)
- [ ] Nextcloud-Tags als Filter und als Ausschlussregel (Auslöser: Datenschutz-Nachfragen)
- [ ] External Storage als bewusst einschaltbare Option mit ehrlicher Warnung (Auslöser: Nachfrage; context_chat dokumentiert hier Probleme, wir sollten nicht in dieselbe Falle laufen)
- [ ] E-Mail-Anhänge und Archivinhalte (`zip`) (Auslöser: Nachfrage, Default bleibt aus)

### Future Consideration (v2+)

- [ ] Sprung zur Fundstelle im Viewer mit Markierung (aufwendige Integration in fremde Apps)
- [ ] Weitere OCR-Sprachen und Handschrifterkennung (Modellgröße gegen RAM-Budget)
- [ ] Mehrmandantenfähigkeit und horizontale Skalierung (widerspricht der Zielhardware)
- [ ] Suche über Nextcloud-Grenzen hinweg, etwa Federated Shares
- [ ] Ähnliche Dokumente finden ("more like this"), fällt bei vorhandenen Embeddings günstig ab, aber nach v1

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Volltextsuche über Inhalte in der Unified Search | HIGH | HIGH | P1 |
| OCR automatisch, ohne Originaldatei anzufassen | HIGH | HIGH | P1 |
| Berechtigungsfilter zur Suchzeit | HIGH | HIGH | P1 |
| Inkrementelle Indexierung mit Resume | HIGH | HIGH | P1 |
| Ressourcendeckel und Drosselung | HIGH | MEDIUM | P1 |
| Snippet mit Trefferkontext | HIGH | MEDIUM | P1 |
| Statusseite und Fehlerliste | HIGH | MEDIUM | P1 |
| Diagnose pro Datei | HIGH | MEDIUM | P1 |
| Semantische Suche mit Hybrid-Ranking | HIGH | HIGH | P1 (Owner-Entscheid: alles in v1) |
| Ausschlussregeln (.noindex, Größe, Mimetype) | MEDIUM | LOW | P1 |
| Minimale Query-Syntax (Phrase, +, -) | MEDIUM | LOW | P1 |
| occ-Kommandos | MEDIUM | LOW | P1 |
| Unicode-Folding, Deutsch und Englisch | HIGH | MEDIUM | P1 |
| NC-Standardfilter since/until/person/mime | MEDIUM | MEDIUM | P2 |
| Pfadfilter und Ordnersuche | MEDIUM | MEDIUM | P2 |
| Vorab-Schätzung | MEDIUM | LOW | P2 |
| Eigene Ergebnisseite mit Paginierung | MEDIUM | MEDIUM | P2 |
| Tags als Filter und Ausschluss | MEDIUM | MEDIUM | P2 |
| External Storage | MEDIUM | HIGH | P2 |
| Archive und Mail-Anhänge | LOW | MEDIUM | P3 |
| Sprung zur Fundstelle im Viewer | MEDIUM | HIGH | P3 |
| Ähnliche Dokumente finden | LOW | LOW | P3 |

## Competitor Feature Analysis

| Feature | fulltextsearch + Elasticsearch (offiziell, seit 08/2026 wieder aktiv) | context_chat (Nextcloud AI) | Paperless-ngx | Unser Ansatz |
|---------|------------------------------------|------------------------------|---------------|--------------|
| Setup | Externer Suchserver plus Ingest-Attachment-Plugin, drei Apps, Admin-Konfiguration | AppAPI plus Assistant plus Backend plus Postgres/pgvector plus Text2Text-Provider | Eigener Stack neben Nextcloud, eigene Ablage | Ein Container plus schlanke PHP-App, keine Pflichteinstellung |
| RAM-Bedarf | Elasticsearch praktisch ab 2 GB aufwärts zusätzlich | laut Admin-Doku min. 12 GB ohne GPU, dedizierte Maschine empfohlen | moderat, aber eigener Stack | Ziel: passt in 4 bis 8 GB Gesamt-Box |
| OCR | Nur über die separate Tesseract-Provider-App, laut Community "broken since years", mit dokumentiertem Datenverlustrisiko | keines | Kern-Feature (OCRmyPDF), erzeugt PDF/A mit Textlayer | Eingebaut, Textlayer-Erkennung, Original bleibt unverändert |
| Keyword-Suche | ja, mit Highlighting, `+`/`-`/Phrase, Wildcards auf `title` | nein, nur semantisch | ja, Whoosh-Index mit Feldsyntax | ja, minimales Operator-Set plus Filter |
| Semantik | nein | ja, aber als Chat-Kontext, nicht als Suchergebnisliste | nein | ja, hybrid mit BM25 fusioniert |
| Query-Syntax | `in:filename`, `in:content`, `is:`, `show:`, `meta:`, Phrasen, `+`/`-`; nie ordentlich dokumentiert | Freitext-Prompt | `type:`, `tag:`, `correspondent:`, `created:[2005 to 2009]`, `added:yesterday`, `AND/OR`, Wildcards | Phrase, `+`, `-`, `path:`, `type:` plus Filterchips der Unified Search |
| Snippets | ja, aber Default 100 Zeichen und mitten im Treffer abgeschnitten | nicht anwendbar | ja, mit Highlighting | ja, um den Treffer zentriert, konfigurierbar |
| Berechtigungen | Access-Metadaten im Index, mit bekannten Lücken bei Gruppen-Shares und Team Folders | folgt Access-Control ausdrücklich nicht | eigenes Rechtemodell, kein Nextcloud-Bezug | Access-Filter zur Suchzeit, Share-Events rekursiv, Testfall Gruppen-Share |
| Indexstatus | occ-Interaktivmodus, keine Admin-UI, Statusfrage im Forum unbeantwortet | `context_chat:stats` auf der Shell | Web-UI mit Aufgabenliste | Statusseite plus Diagnose pro Datei plus occ |
| Ausschlüsse | `.noindex`, Größenlimit (Default 20 MB), Mimetype-Schalter, Chunk-Tiefe | Größenlimit 100 MB, verschlüsselte Dateien ausgeschlossen | Konsumverzeichnis-Regeln | `.noindex`, Größe, Mimetype, später Tags |
| Ergebnisdarstellung | Unified Search plus Files-Integration, Ergebnisliste geht beim Öffnen verloren | Chat-Antwort im Assistant | eigene Web-UI mit gespeicherten Ansichten | v1 Unified Search, v1.x eigene Ergebnisseite |

Recoll und macOS Spotlight sind als Vergleich nur indirekt relevant, liefern aber die Erwartungshaltung an Query-Sprache: Recoll bietet Feldqualifizierer, Phrasen, Proximity, Wildcards und Booleans, Spotlight setzt auf Sofortergebnisse ohne jede Syntax. Für Selfhoster in Nextcloud ist Spotlight das realistischere Vorbild: eintippen, sofort brauchbare Treffer, Verfeinerung über Filterchips statt über Syntax.

## Sources

**Quellcode und offizielle Doku (HIGH confidence)**
- https://github.com/nextcloud/files_fulltextsearch/blob/master/lib/ConfigLexicon.php (Ausschlüsse, Defaults: files_size 20 MB, files_office/pdf an, files_zip aus, files_group_folders aus, files_external 0)
- https://github.com/nextcloud/files_fulltextsearch/blob/master/lib/Service/SearchService.php (Suchoptionen `files_extension`, `files_local`, `files_external`, `files_group_folders`, `in:filename`, `in:content`)
- https://github.com/nextcloud/fulltextsearch/blob/master/lib/Model/SearchRequest.php (Query-Parsing: Phrasen, `is:`, `show:`, `in:`, `meta:`, `and:`)
- https://github.com/nextcloud/fulltextsearch_elasticsearch/blob/master/lib/Service/SearchMappingService.php (Highlighting, Wildcards, Access-Filter)
- https://github.com/nextcloud/fulltextsearch/wiki/Commands (occ-Kommandos index, stop, reset, live, errors reset)
- https://github.com/nextcloud/fulltextsearch/wiki/How-FullTextSearch-indexes-your-cloud (Indexmodell)
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/search.html (IProvider, IFilteringProvider, Filter term/since/until/person, Files nutzt min-size/max-size/mime/type)
- https://docs.nextcloud.com/server/latest/admin_manual/ai/app_context_chat.html (12 GB RAM CPU-Setup, 100-MB-Limit, verschlüsselte Dateien, External Storage unzuverlässig, folgt Access Control nicht, `context_chat:scan`, `context_chat:stats`)
- https://docs.paperless-ngx.com/usage/ (Query-Syntax, Datumsschlüsselwörter, Accent- und Separator-Verhalten, gescorte Ergebnisliste)
- https://github.com/jplitza/fulltextsearch_sql (SQL-Backend: keine Office-Formate, kein SQLite, Inhalt doppelt in der DB, MySQL-Excerpts nur kleingeschrieben)
- https://github.com/R0Wi-DEV/workflow_ocr (CPU-Limit, Timeout, kein Batch für Bestandsdateien, PDF-Metadatenverlust)
- GitHub-API-Abfragen vom 15.08.2026 zu Commits, Releases und offenen PRs der drei fulltextsearch-Repos

**Nutzerwünsche und Schmerzpunkte (MEDIUM confidence, Foren und Issues)**
- https://help.nextcloud.com/t/ocr-in-nextcloud-giving-up-after-a-month/240122 (12.02.2026, silent failures, "broken since years", Ruf nach guten Drittintegrationen)
- https://help.nextcloud.com/t/full-text-search-knowing-index-status/217460 (kein Weg, den Indexstatus zu sehen)
- https://help.nextcloud.com/t/handling-of-shared-folders-in-fulltext-search/172909 (432.000 Dateien bei 24 Nutzern, `.noindex` greift in Shares nicht)
- https://help.nextcloud.com/t/not-possible-to-perform-fulltext-search-in-shared-folders/160044
- https://github.com/nextcloud/fulltextsearch/issues/250 und /282 (Gruppen-Shares im Index leer)
- https://github.com/nextcloud/fulltextsearch_elasticsearch/issues/118 und https://help.nextcloud.com/t/longer-snippets-in-search-results/54820 (Snippetlänge)
- https://github.com/nextcloud/fulltextsearch/issues/150 (Fundstelle im Dokument anspringen)
- https://help.nextcloud.com/t/fulltextsearch-results-behavior-feature-request/29122 (Ergebnisliste bleibt nicht erhalten, Nextant konnte es besser)
- https://help.nextcloud.com/t/search-syntax-faq/20194 (fehlende Syntax-Dokumentation)
- https://github.com/nextcloud/all-in-one/discussions/1709 und /1694 (Endlos-Reindex bis ans Speicherlimit, Marker-Datei als Notbremse)
- https://help.nextcloud.com/t/warning-full-text-search-files-tesseract-ocr-app-w-pdf-enabled-may-delete-your-pdfs/93151 (OCR-App zerstörte PDFs)
- https://github.com/nextcloud/files_fulltextsearch_tesseract/issues/28 (OCR auf Digital-PDFs vermeiden)
- https://help.nextcloud.com/t/fulltextsearch-compatibility-for-nc-34-35/246992 (Nutzer bleiben auf NC 33 wegen der Suche)
- https://jplitza.de/blog/2025/07/22/document-management-2-nextcloud-fulltextsearch.html (Selfhoster-Erfahrungsbericht, Excerpt-Kritik)
- https://github.com/nextcloud/server/issues/48398 (Search in files, geschlossen mit Ziel NC 33)

---
*Feature research for: Nextcloud Content-Suche mit OCR, Volltext und Semantik*
*Researched: 2026-08-15*
