<!-- GSD:project-start source:PROJECT.md -->
## Project

**Findling (Nextcloud Zero-Config-Suche)**

Findling ist eine Nextcloud-ExApp, die die kaputte Suche repariert: ein Container mit OCR, klassischer Volltextsuche und semantischer Suche, per Klick aus dem Nextcloud App Store installierbar, ohne Elasticsearch-Gebastel. Ergebnisse erscheinen in der normalen Unified Search (via schlanker PHP-Companion-App). Zielgruppe: Selfhoster und kleine Organisationen auf typischer Hardware (4-8 GB RAM, oft ARM), für die das offizielle fulltextsearch-Framework (jahrelang verwaist, weiterhin Elasticsearch-gekoppelt) keine Option ist.

**Core Value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.

### Constraints

- **Timeline**: Bau beginnt nach der MCP-Connector-Einreichung (Sept. 2026); HARTES ZIEL: v1.0-Store-Einreichung (Volltext+OCR) vor Jahresende 2026, v1.1 (Semantik) 4-6 Wochen danach; Scope-Kürzung schlägt Termin
- **Kapazität**: Solo-Entwickler; Aufwandsschätzung 10-14 Personenwochen für v1 mit allem
- **Hardware-Ziel**: 4-8 GB RAM, ARM-tauglich , alles CPU-only, kein GPU-Zwang, RAM-Budget hart einplanen
- **Tech stack**: Python 3.13 + uv (lokales System-Python defekt), ExApp via AppAPI/nc_py_api, plus kleine PHP-Companion-App; Docker/WSL2 für Test-Nextcloud
- **Lizenz**: AGPL-3.0 (Ghostscript/OCRmyPDF-AGPL im Container damit kompatibel)
- **Repo**: public auf GitHub street1983nk (privates Konto, NICHT Akara-GitLab)
- **Sprache**: Code/README Englisch, Projektkommunikation Deutsch; keine Em-Dashes; echte Umlaute nur in deutscher Prosa, nie in Code
- **Qualitätsgates**: globale Python-Regel (ruff-Vollregelsatz, pyright basic, vulture, CI-Gates, lokal grün vor Commit)
- **Security/Privacy**: Berechtigungs-Durchgriff strikt; keine Inhalte verlassen den Server; kein Telemetrie-Phoning
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Kernentscheidungen auf einen Blick
| Frage | Entscheidung | Konfidenz |
|-------|--------------|-----------|
| Suchmaschine | **Tantivy 0.26.0 (Python-Bindings), embedded, mmap auf Platte** | HIGH |
| Vektorspeicher | **SQLite + sqlite-vec 0.1.9, int8-Vektoren, brute force** | MEDIUM |
| Hybrid-Ranking | **Reciprocal Rank Fusion (RRF), k=60, selbst implementiert** | HIGH |
| OCR | **Tesseract 5.5.0 (deu+eng+osd) als Subprozess, Rendering via pypdfium2; kein OCRmyPDF im Indexpfad** | MEDIUM-HIGH |
| Embeddings | **fastembed 0.8.0 + eigene Registrierung von intfloat/multilingual-e5-small (384 dim), int8-quantisiert beim Image-Build** | MEDIUM |
| PDF-Text | **pypdfium2 5.13.0** (schnell, permissiv, gleiche Lib fuer Text und Rasterung) | HIGH |
| Office-Text | **python-docx, python-pptx, openpyxl (read_only); ODF direkt via zipfile + lxml** | HIGH |
| ExApp-Geruest | **nc_py_api[app] >= 0.30.3 (Async-API!) + FastAPI 0.141.x + uvicorn** | HIGH |
| Basis-Image | **python:3.13-slim-trixie** (Python 3.13.15, Tesseract 5.5.0 aus Debian trixie) | HIGH |
| Nextcloud-Fenster | **min-version 32, max-version 35** (NC 31 ist Ende 2026 nicht mehr relevant) | HIGH |
| PHP-Companion | Minimal-App, `registerSearchProvider` + `IFilteringProvider`, Proxy via `OCA\AppAPI\PublicFunctions::exAppRequest` | HIGH |
## 1. Suchmaschine: Tantivy statt FTS5 oder Meilisearch
### Entscheidung
### Warum
# ASCII-Bezeichner, wie in der Projektregel gefordert
### Die Alternativen im direkten Vergleich
| Kriterium | Tantivy 0.26.0 | SQLite FTS5 (+ sqlite-vec) | Meilisearch 1.53 (Sidecar) |
|---|---|---|---|
| Prozessmodell | im ExApp-Prozess | im ExApp-Prozess | zweiter Serverprozess |
| Basis-RSS | ~0, nur Writer-Heap (konfigurierbar) | ~0 | ca. 100-200 MB im Leerlauf, Indexierung deutlich mehr |
| Index groesser als RAM | ja, mmap + Page-Cache | ja, B-Tree auf Platte | ja, LMDB-mmap, laut Doku bis ~80 TiB virtuell |
| Deutsches Stemming | ja, Snowball `german` | **nein** (nur `porter` = Englisch) | **nein**, charabia hat keinen Stemmer |
| Deutsche Stoppwoerter | ja, `Filter.stopword("german")` | nein, nur selbst gebaut | teils ueber Normalisierung |
| Komposita | `Filter.split_compound(wortliste)`, Liste selbst mitbringen | nein | ja, `segmenter/german.rs` mit eigener `words.fst` |
| Umlaut-Normalisierung | `Filter.ascii_fold()` | `unicode61 remove_diacritics=2` | `ae_oe_normalizer.rs` |
| Snippets/Highlighting | `SnippetGenerator`, HTML-Ausgabe | `snippet()` und `highlight()` in SQL | `_formatted` in der Antwort |
| Ranking | BM25 | `bm25()` | eigenes Ranking-Regelwerk |
| Phrasen, Prefix, Fuzzy | ja | Phrase und Prefix ja, Fuzzy nein | ja, Typo-Toleranz stark |
| Zero-Config-Tauglichkeit | hoch | sehr hoch | mittel: zweiter Container, zweiter Port, eigenes Datenverzeichnis |
| Lizenz | MIT | Public Domain | MIT |
### Konkrete Ausgestaltung fuer Deutsch
## 2. Vektorspeicher und Hybrid-Ranking
### Entscheidung
### Warum
### Grenzen und Ausweg
### Hybrid-Ranking: RRF
# score = sum ueber alle Listen: weight / (k + rank)
## 3. OCR
### Entscheidung
### Warum kein OCRmyPDF, obwohl es der naheliegende Kandidat ist
- ein komplettes PDF-Rewrite pro Datei ueber pikepdf, mit Temp-Dateien in Groessenordnung des Originals,
- eigene Parallelisierung (`--jobs`), die mit unserem Backpressure-Konzept kollidiert,
- eine grosse Abhaengigkeitskette (`pikepdf>=10`, `img2pdf`, `fpdf2`, `uharfbuzz`, `pi-heif`, `pdfminer-six`, `pypdfium2`),
- historisch Ghostscript. Positiv und pruefenswert: laut Installations-Doku ist Ghostscript inzwischen **optional**, pypdfium2 kann die Rasterung uebernehmen. Das entschaerft das AGPL-Argument, macht OCRmyPDF aber nicht leichter.
### Text-Layer-Erkennung: OCR nur wenn noetig
### ARM64 und Sprachpakete
| Paket | Version in trixie | Anmerkung |
|---|---|---|
| `tesseract` (Quellpaket) | 5.5.0-1 | aktuellster 5.x-Zweig ist 5.5.3 (24.07.2026) |
| `tesseract-lang` (liefert `-deu`, `-eng`, `-osd`) | 1:4.1.0-2 | `Architecture: all`, also identisch auf arm64 |
| `python3-defaults` | 3.13.5-1 | passt zur Projektvorgabe Python 3.13 |
### Verworfene OCR-Alternativen
| Kandidat | Version | Warum nicht |
|---|---|---|
| RapidOCR | 3.9.2 (21.07.2026) | PP-OCR-Modelle als ONNX, Apache-2.0, teilt sich onnxruntime mit den Embeddings. Auf Fotos und schraeg fotografierten Belegen besser als Tesseract, bei sauberen deutschen Scans schlechter (Umlaute, lange Woerter). Interessanter Zusatzpfad fuer Bilddateien in einer spaeteren Phase, nicht als Standard. |
| `rapidocr-onnxruntime` | 1.4.4 (01/2025) | Vorgaengerpaket, `requires-python <3.13`, damit fuer uns tot. |
| PaddleOCR, docTR, Surya | n/a | Modelle und Laufzeiten sprengen 4 GB, teils Torch-Zwang. Unvereinbar mit dem Hardware-Ziel. |
| VLM-basiertes OCR | n/a | Braucht GPU oder mehrere GB RAM. Widerspricht dem Kernversprechen. |
## 4. Lokale Embeddings
### Entscheidung
### Warum dieses Modell
| Eingebautes Modell | Dim | Groesse | Bewertung |
|---|---|---|---|
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 | 0,22 GB | Klein, aber ein STS-/Paraphrase-Modell von 2021, nicht auf Retrieval trainiert. Schwach bei "Frage gegen Dokumentabschnitt". |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | 768 | 1,00 GB | Zu gross fuer 4 GB, gleiches Trainingsproblem. |
| `intfloat/multilingual-e5-large` | 1024 | 2,24 GB | Qualitativ top, auf der Zielhardware indiskutabel. |
| `jinaai/jina-embeddings-v2-base-de` | 768 | 0,32 GB (Angabe) | Deutsch-englisch bilingual, Apache-2.0, 8k Kontext. **Aber:** fastembed warnt im Code explizit, dass dieses Modell wegen onnxruntime-Aenderungen inzwischen im **fp32-Original** statt fp16 laeuft, der reale Fussabdruck ist also rund doppelt so gross wie ausgewiesen. Dazu 768 statt 384 Dimensionen, also doppelter Vektorspeicher und doppelte Scan-Kosten. |
| `jinaai/jina-embeddings-v3` | 1024 | n/a | **Lizenz CC BY-NC**. Fuer eine verteilte AGPL-App im App Store nicht nutzbar. Ausschluss. |
### Quantisierung: selbst quantisieren, nicht fremdquantisiert ziehen
- `intfloat/multilingual-e5-small` liefert `onnx/model_qint8_avx512_vnni.onnx`. Das ist **x86-only** (AVX512-VNNI). Auf ARM entweder unbrauchbar oder pathologisch langsam. Nicht verwenden.
- `Xenova/multilingual-e5-small` liefert plattformneutrale `onnx/model_quantized.onnx`, `model_int8.onnx`, `model_uint8.onnx`, hat aber **kein Lizenzfeld** in der Modellkarte. Fuer ein App-Store-Release mit AGPL-Anspruch ist das eine unnoetige Unschaerfe.
### E5-Praefixe nicht vergessen
### Sparsam-Modus fuer sehr schwache Boxen
### Chunking
## 5. Textextraktion in reinem Python
| Format | Bibliothek | Version | Begruendung |
|---|---|---|---|
| PDF (Text) | **pypdfium2** | 5.13.0 | PDFium (Chrome-Engine), C++-Kern, sehr schnell, BSD-3 und Apache-2.0, `cp310-abi3`-Wheels inklusive `manylinux_2_28_aarch64`. Dieselbe Bibliothek rendert auch die Seiten fuer OCR: ein Abhaengigkeit fuer beide Aufgaben. |
| PDF (Metadaten, Verschluesselung, Seitenzahl) | **pypdf** | 6.16.1 | Pur Python, BSD. Erkennt passwortgeschuetzte PDFs, bevor pypdfium2 stolpert, und liefert Titel und Autor fuer das Suchergebnis. |
| DOCX | **python-docx** | 1.2.0 | MIT, stabil. Bekannte Luecke: Kopf- und Fusszeilen, Fussnoten und Textfelder werden nicht erfasst. Fuer eine Suche ist das meist irrelevant; wenn es stoert, ergaenzend `word/header*.xml` und `word/footnotes.xml` per lxml auslesen. |
| PPTX | **python-pptx** | 1.0.2 | MIT. Letztes Release 08/2024, aber das OOXML-Format ist eingefroren; kein Risiko. |
| XLSX | **openpyxl** | 3.1.5 | MIT. Zwingend `load_workbook(..., read_only=True, data_only=True)` und `iter_rows(values_only=True)`, sonst baut openpyxl die gesamte Mappe im RAM auf. Zusaetzlich eine Zellobergrenze pro Datei setzen (Startwert 200 000), sonst kippt eine einzige Exportdatei den Container. |
| ODT, ODS, ODP | **zipfile + lxml**, kein odfpy | n/a | odfpy steht bei 1.4.1 von **Januar 2020**, ohne Typannotationen und ohne `py.typed`. Das kollidiert mit dem pyright-Gate der globalen Regel und erzeugt eine unbetreute Abhaengigkeit. ODF ist ein dokumentiertes ZIP mit `content.xml`; die Textextraktion ist ein XPath ueber `text:p` und `text:h`, rund 30 Zeilen. lxml wird ohnehin gebraucht. |
| HTML, XHTML | **lxml.html** | aktuell | `text_content()` nach Entfernen von `script` und `style`. |
| RTF | **striprtf** | 0.0.32 | BSD, pur Python, genau ein Zweck. |
| TXT, MD, CSV, Code | stdlib + **charset-normalizer** | 3.5.0 | MIT. Encoding-Erkennung ist bei deutschen Altbestaenden (cp1252, latin-1) unverzichtbar; `chardet` ist LGPL und langsamer. |
| Bilder (JPG, PNG, TIFF, WEBP) | **pillow** | aktuell | Vorstufe fuer Tesseract. |
| HEIC, HEIF | **pi-heif** | aktuell | iPhone-Fotos in Nextcloud sind Alltag. |
| DOC, XLS, PPT (Legacy) | n/a | n/a | **Ausserhalb v1.** Braucht antiword, catdoc oder LibreOffice-Headless. LibreOffice im Container waere ein Vielfaches der Imagegroesse und ein eigener Prozess-Zoo. Dokumentierte Nicht-Unterstuetzung ist ehrlicher als eine wacklige Kruecke. |
### markitdown: nein
- Zielprodukt ist **Markdown fuer LLM-Prompts**, nicht Rohtext fuer einen Index. Tabellenformatierung, Ueberschriftenmarkierung und Bildplatzhalter sind fuer uns Ballast.
- Es zieht `magika~=0.6.1` als **Pflicht**-Abhaengigkeit, und magika bringt eine eigene onnxruntime-Nutzung samt Modell mit, nur zur Dateityperkennung. Wir haben mit dem Nextcloud-Mimetype plus `python-magic` bereits genug Information.
- Der PDF-Pfad haengt an `pdfminer-six` und `pdfplumber`, beide pur Python und um ein Vielfaches langsamer als pypdfium2.
- Es kapselt genau die Bibliotheken, die wir direkt einbinden, und nimmt uns dabei die Kontrolle ueber Limits, Timeouts und Teilausgaben bei Fehlern.
## 6. ExApp-Geruest
### Entscheidung
### Kritischer Punkt: von Tag eins asynchron
- 0.30.2 hebt den Boden auf `starlette>=1.0.1` wegen **CVE-2026-48710 (BadHost)**, einer Pfad-Desynchronisation, die pfadbasierte Autorisierung aushebeln kann, und `fastapi>=0.133`. Fuer eine App mit Berechtigungsdurchgriff ist das keine Formalie: die Untergrenzen nicht unterlaufen.
- 0.30.3 fixt ein PROPFIND-Leck, bei dem sich Property-Listen pro Aufruf aufblaehten und langlaufende Clients dem Server die Worker wegfrassen. Genau unser Nutzungsprofil (Dauerindexierung). **Mindestens 0.30.3.**
### Nextcloud-Versionsfenster
### HaRP statt Docker-Socket-Proxy
### Bestaetigt: AppAPI kann keine Suchanbieter registrieren
### Events Listener fuer inkrementelle Indexierung
- Registrierung: `POST /apps/app_api/api/v1/events_listener` mit `{"eventType": "node_event", "actionHandler": "/action_handler_route", "eventSubtypes": []}`
- Unterstuetzte Subtypen fuer `node_event`: `NodeCreatedEvent`, `NodeTouchedEvent`, `NodeWrittenEvent`, `NodeDeletedEvent`, `NodeRenamedEvent`, `NodeCopiedEvent`
## 7. PHP-Companion-App
### Minimaler Umfang
| API | Datei | Seit |
|---|---|---|
| `IRegistrationContext::registerSearchProvider(string $class)` | `lib/public/AppFramework/Bootstrap/IRegistrationContext.php` | NC 20 |
| `OCP\Search\IProvider` mit `getId()`, `getName()`, `getOrder(string $route, array $routeParameters): ?int`, `search(IUser $user, ISearchQuery $query): SearchResult` | `lib/public/Search/IProvider.php` | NC 20, `getOrder` nullable seit NC 28 |
| `OCP\Search\IFilteringProvider` mit `getSupportedFilters()`, `getAlternateIds()`, `getCustomFilters()` | `lib/public/Search/IFilteringProvider.php` | NC 28 |
| `OCP\Search\IInAppSearch` | `lib/public/Search/IInAppSearch.php` | NC 28 |
| `SearchResult`, `SearchResultEntry` (`thumbnailUrl`, `title`, `subline`, `resourceUrl`, `icon`, `rounded`, `attributes`) | `lib/public/Search/` | NC 20 |
### Der Proxy zur ExApp
- `exAppRequestWithUserInit()` ist **seit AppAPI 3.0.0 deprecated**, nicht verwenden.
- Bei unbekannter ExApp liefert die Methode `['error' => ...]` statt einer Exception: der Rueckgabewert muss geprueft werden, sonst zeigt die Suche stumm nichts an.
- Die PHP-App muss `app_api` als Abhaengigkeit fuehren und bei fehlendem oder gestopptem Backend ein leeres `SearchResult` mit klarer Meldung zurueckgeben, nicht in einen Fehler laufen. Die Unified Search ruft alle Provider parallel; ein haengender Provider verlangsamt die gesamte Suche. **Hartes Timeout** ueber `$options` setzen, Startwert 2 Sekunden.
### Berechtigungsdurchgriff: in PHP filtern, nicht in Python
### App-Store-Verpackung: zwei Eintraege, zwei Zertifikate
| Teil | Store-Bereich | Beispiel |
|---|---|---|
| PHP-Companion | Apps | `context_chat` |
| Python-ExApp | External Apps | `context_chat_backend` |
- Beide Teile fuehren **dieselbe Major- und Minor-Version**, damit Nutzer sie nicht auseinanderlaufen lassen. Das gehoert in die Release-Automatisierung, nicht in die Doku.
- Die ExApp-`info.xml` traegt `<external-app><docker-install><registry>ghcr.io</registry>...</docker-install><routes>...</routes><environment-variables>...</environment-variables></external-app>`. Ueber `<environment-variables>` bekommen Admins Einstellungen (OCR-Sprachen, Modellwahl, Indexpfad), ohne dass wir eine Settings-UI bauen: der guenstigste Weg zu "sinnvolle Defaults, keine Pflichteinstellungen".
- Die ExApp deklariert Routen samt `access_level` (`ADMIN`, `USER`, `PUBLIC`) direkt in der `info.xml`. Die Statusseite laeuft ueber `ADMIN`, die Suchroute wird ausschliesslich von der PHP-App gerufen.
- Fuer die PHP-App: Tarball bauen, mit dem App-Zertifikat signieren (`openssl dgst -sha512 -sign`), Release-Metadaten an `https://apps.nextcloud.com/api/v1/apps/releases` posten. `krankerl` nimmt einem das ab, ist aber nicht zwingend; ein Makefile reicht. (MEDIUM: Prozessdetails vor der Einreichung gegen die dann aktuelle Store-Doku pruefen.)
## RAM-Budget auf einer 4-GB-Box
| Komponente | Ruhezustand | Spitze | Stellschraube |
|---|---|---|---|
| Python 3.13 + FastAPI + uvicorn + nc_py_api | 120-180 MB | n/a | ein Worker |
| Tantivy Suche (mmap) | ~0 RSS | ~0 | Index liegt im Page-Cache |
| Tantivy Writer | n/a | 50-130 MB | `heap_size`, `num_threads=1` |
| SQLite + sqlite-vec | ~10 MB | 80-120 MB bei vollem Vektorscan | `cache_size`, int8 statt float32 |
| onnxruntime + e5-small int8 | 0 bei `lazy_load=True` | 250-400 MB | `threads=2`, Batchgroesse 8-16 |
| Tesseract, eine Seite bei 300 dpi A4 | 0 | 300-600 MB | ein Worker, DPI, Seitendeckel |
| pypdfium2 Rasterung | 0 | 50-150 MB | Skalierung, Seite fuer Seite freigeben |
## Installation
### Systempakete im Image
### Python-Abhaengigkeiten (uv, exakt gepinnt)
### ARM64-Wheel-Matrix (alles verifiziert am 15.08.2026)
| Paket | aarch64-Wheel | cp313 |
|---|---|---|
| tantivy 0.26.0 | `manylinux_2_17_aarch64` | ja, inklusive cp313t |
| onnxruntime 1.28.0 | `manylinux_2_27_aarch64` | ja |
| sqlite-vec 0.1.9 | `manylinux_2_17_aarch64` | `py3-none` |
| pypdfium2 5.13.0 | `manylinux_2_28_aarch64` | `cp310-abi3` |
| tokenizers 0.23.1 (via fastembed) | `manylinux_2_17_aarch64` | `cp310-abi3` |
| semantic-text-splitter 0.32.0 | `manylinux_2_28_aarch64` | `cp310-abi3` |
| fastembed, nc-py-api, fastapi, pypdf, python-docx, python-pptx, openpyxl, striprtf | reines Python | ja |
## Alternatives Considered
| Empfohlen | Alternative | Wann die Alternative besser ist |
|---|---|---|
| Tantivy | SQLite FTS5 als Volltext-Engine | Wenn Deutsch keine Rolle spielt und Abhaengigkeitsfreiheit ueber alles geht. Fuer dieses Projekt ausgeschlossen. |
| Tantivy | Meilisearch 1.53 Sidecar | Wenn Tantivys deutsche Kompositabehandlung in der Praxis versagt und Meilisearchs `german.rs`-Segmenter messbar besser trifft. Preis: zweiter Prozess, Bruch mit Zero-Config. Erst nach einer Messung erwaegen. |
| sqlite-vec (brute force) | usearch 2.26.0 (HNSW, mmap) | Ab grob 250 000 Chunks oder wenn die Vektorsuche ueber 300 ms braucht. |
| e5-small int8 | jina-embeddings-v2-base-de fp32 | Nur auf Boxen mit 8 GB und ausdruecklicher Admin-Entscheidung fuer Qualitaet ueber Geschwindigkeit. |
| e5-small | potion-multilingual-128M (model2vec) | Auf 2-GB-Boxen oder wenn die Erstindexierung sonst Tage braucht. Deutlich schwaechere Qualitaet, aber besser als keine Semantik. |
| Tesseract | RapidOCR 3.9.2 | Fuer fotografierte Belege und schraege Handyaufnahmen. Als Zusatzpfad fuer Bilddateien, nie als Ersatz fuer deutsche Scans. |
| Direkter Tesseract-Aufruf | OCRmyPDF 17.10.0 | Wenn das Ziel eine durchsuchbare PDF-Datei ist, nicht ein Suchindex. Eigenes Feature, eigene Phase. |
| pypdfium2 | PyMuPDF 1.28.2 | Wenn Layoutanalyse, Tabellen oder Anmerkungen gebraucht werden. AGPL-Bindung dann bewusst akzeptieren. |
| Eigene Extraktoren | markitdown 0.1.7 | Wenn das Ziel LLM-taugliches Markdown ist. Fuer einen Suchindex das falsche Produkt. |
## What NOT to Use
| Vermeiden | Konkretes Problem | Stattdessen |
|---|---|---|
| Elasticsearch, OpenSearch, Solr | JVM, mehrere GB RAM, genau die Setup-Qual, die das Produkt beseitigen soll | Tantivy embedded |
| Typesense | GPLv3 und Index vollstaendig im RAM | Tantivy embedded |
| Apache Tika | JVM im Container, verdoppelt Imagegroesse und Speicherbedarf | pypdfium2 plus die Python-Extraktoren |
| `jinaai/jina-embeddings-v3` | **CC BY-NC**: nicht kommerziell nutzbar, im App Store nicht verteilbar | multilingual-e5-small (MIT) |
| `intfloat/.../model_qint8_avx512_vnni.onnx` | AVX512-VNNI ist x86-only, auf ARM unbrauchbar | selbst quantisiertes int8 aus `onnx/model.onnx` |
| `rapidocr-onnxruntime` 1.4.4 | `requires-python <3.13`, veraltetes Vorgaengerpaket | `rapidocr` 3.9.2, falls ueberhaupt |
| `hnswlib` 0.8.0 | letztes Release 12/2023, keine aarch64- und keine cp313-Wheels | sqlite-vec, spaeter usearch |
| `chonkie` 1.7.0 | keine aarch64-Wheels | semantic-text-splitter |
| `odfpy` 1.4.1 | Release von 01/2020, keine Typannotationen, faellt durch das pyright-Gate | zipfile plus lxml |
| `chardet` | LGPL, langsamer | charset-normalizer (MIT) |
| `magika` (via markitdown) | onnxruntime-Modell nur zur Dateityperkennung | Nextcloud-Mimetype plus `python-magic` |
| Sync-API von nc_py_api | wird in 0.31.0 entfernt, erzeugt `DeprecationWarning` | `AsyncNextcloudApp` von Beginn an |
| `exAppRequestWithUserInit()` | deprecated seit AppAPI 3.0.0 | `exAppRequest()` |
| `starlette <= 1.0.0` | CVE-2026-48710 (BadHost), umgeht pfadbasierte Autorisierung | `starlette>=1.0.1`, `fastapi>=0.133` |
| Docker-Socket-Proxy als Zielplattform | AppAPI empfiehlt fuer NC 32+ ausdruecklich HaRP | HaRP-Integration von Anfang an |
| Modelldownload beim ersten Start | bricht Zero-Config bei Firewall, Proxy oder Offline-Installation | Modell ins Image backen, `HF_HUB_OFFLINE=1` |
| Nutzerrechte im Python-Index nachbauen | zweites, driftendes Berechtigungsmodell, Sicherheitsrisiko | Endfilterung in PHP ueber `getUserFolder()->getFirstNodeById()` |
## Stack Patterns by Variant
- `INDEX_WORKERS=1`, OCR und Embedding strikt seriell
- Tantivy `heap_size=50_000_000`, `num_threads=1`
- e5-small int8, `threads=2`, `lazy_load=True`, Batchgroesse 8
- OCR-Deckel: 100 Seiten pro Datei, 300 dpi, 30 s Timeout pro Seite
- `INDEX_WORKERS=2`, weiterhin OCR und Embedding nicht gleichzeitig im selben Worker
- Tantivy `heap_size=128_000_000`, `num_threads=2`
- optional e5-small fp32 statt int8
- Vektorspeicher von sqlite-vec auf usearch HNSW umstellen
- Reindex noetig, deshalb frueh eine Indexversion im Schema fuehren
- `body_en` staerker gewichten oder `body_de` abschalten, spart rund 40 Prozent Indexgroesse
## Version Compatibility
| Paket | Vertraegt sich mit | Anmerkung |
|---|---|---|
| Python 3.13 | tantivy 0.26.0, onnxruntime 1.28.0, ocrmypdf 17.x | onnxruntime verlangt >= 3.11, ocrmypdf >= 3.11: Python 3.13 ist der sichere gemeinsame Nenner |
| fastembed 0.8.0 | onnxruntime > 1.21.0, != 1.24.0, != 1.24.1 (bei Python 3.13) | 1.28.0 passt; 1.24.0 und 1.24.1 sind ausdruecklich ausgeschlossen |
| fastembed 0.8.0 | numpy >= 2.1.0 (bei Python 3.13) | numpy 1.x scheidet aus |
| nc-py-api 0.30.3 | fastapi >= 0.133, starlette >= 1.0.1 | Sicherheitsboden, nicht unterlaufen |
| nc-py-api 0.30.x | AppAPI 32.x bis 34.x | Sync-Entry-Points fallen in 0.31.0 weg |
| PHP-App | PHP >= 8.2, NC 32 bis 34 (max-version 35) | `IFilteringProvider` gibt es seit NC 28, also unkritisch |
| sqlite-vec 0.1.9 | Python-`sqlite3` mit `enable_load_extension` | im offiziellen `python:3.13-slim-trixie` gegeben, in manchen Distro-Builds nicht |
| tantivy 0.26.0 | Index-Format nicht versionsstabil | Tantivy-Upgrades koennen einen Reindex erzwingen: Indexversion persistieren und beim Start pruefen |
## Offene Punkte fuer die Bauphasen
## Sources
- `/quickwit-oss/tantivy-py` , Tokenizer, SnippetGenerator, IndexWriter, Schema (HIGH)
- PyPI JSON-API fuer alle genannten Pakete , Versionen, Release-Daten, `requires_python`, Wheel-Plattformen, Abhaengigkeiten, Stand 15.08.2026
- `quickwit-oss/tantivy-py`, Tag `0.26.0`: `tantivy/tantivy.pyi` , `Filter.stemmer`, `Filter.stopword`, `Filter.split_compound`, `register_tokenizer`, `Index.writer(heap_size=128_000_000)`
- `quickwit-oss/tantivy-py`, `src/tokenizer.rs` , `parse_language` mit `"german"`
- `meilisearch/charabia`, Dateibaum , `segmenter/german.rs`, `dictionaries/fst/german/words.fst`, `normalizer/ae_oe_normalizer.rs`, kein Stemmer-Modul
- `asg017/sqlite-vec`, GitHub Releases , v0.1.9 stabil (31.03.2026), danach nur Alphas
- `qdrant/fastembed`, `fastembed/text/*.py` , Modellregistrierung, `add_custom_model`, `TextEmbedding.__init__`, fp32-Warnung fuer jina-de
- HuggingFace API fuer `intfloat/multilingual-e5-small`, `Xenova/multilingual-e5-small`, `minishlab/potion-multilingual-128M` , Lizenzen und ONNX-Dateibestand
- `cloud-py-api/nc_py_api`, `CHANGELOG.md` und `README.md` , 0.30.x-Aenderungen, Sync-Deprecation, CVE-2026-48710, NC-Badge
- `nextcloud/server`, Branch `stable34`, `lib/public/Search/*` und `lib/public/AppFramework/Bootstrap/IRegistrationContext.php` , Signaturen und `@since`
- `nextcloud/app_api`, `lib/PublicFunctions.php`, `README.md`, `appinfo/info.xml`, Tags , `exAppRequest`, HaRP-Empfehlung, Versionierung
- `nextcloud/documentation`, `developer_manual/exapp_development/tech_details/api/` , vollstaendige API-Liste, `events_listener.rst`
- `nextcloud/context_chat` und `nextcloud/context_chat_backend`, `appinfo/info.xml` , Zwei-App-Muster, Versionsfenster NC 32-35
- `nextcloud/server` GitHub Releases , aktueller Serverstand 34.0.3 vom 13.08.2026
- `docker-library/python`, `3.13/slim-trixie/Dockerfile` , `--enable-loadable-sqlite-extensions`, Python 3.13.15
- sources.debian.org API , tesseract 5.5.0-1 und tesseract-lang 1:4.1.0-2 in trixie, python3 3.13.5
- `ocrmypdf/OCRmyPDF`, `README.md` und `pyproject.toml` , MPL-2.0, `requires-python >=3.11`
- ocrmypdf.readthedocs.io, Installation , Tesseract >= 4.1.1, Ghostscript optional, pypdfium2 als Rasterer
- meilisearch.com Doku, Known Limitations , Indexgroesse und virtueller Adressraum
- `nextcloud/server` Wiki, Releases and PHP versions , PHP-Matrix fuer NC 32 bis 34
- alle RAM-Zahlen der Budgettabelle
- die 250 000-Chunk-Schwelle fuer brute-force-KNN
- der Qualitaetsverlust durch int8-Quantisierung bei e5-small auf Deutsch
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
