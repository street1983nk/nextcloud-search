# Stack Research

**Domain:** Nextcloud-ExApp fuer Volltext-, OCR- und Semantiksuche (Python, CPU-only, 4-8 GB RAM, amd64 + arm64)
**Researched:** 2026-08-15
**Confidence:** HIGH fuer Versionen, Lizenzen, Plattform-Wheels und die Nextcloud-Seite; MEDIUM fuer RAM-Schaetzungen und Qualitaetsaussagen zu deutschen Embeddings

---

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

---

## 1. Suchmaschine: Tantivy statt FTS5 oder Meilisearch

### Entscheidung

**Tantivy 0.26.0** (PyPI-Paket `tantivy`, offizielle Bindings von quickwit-oss), Index auf Platte, im selben Prozess wie die ExApp.

### Warum

**Deutsche Sprachanalyse ist der Ausschlaggeber.** Die Python-Bindings exponieren seit 0.26.0 den kompletten Analyzer-Baukasten. Verifiziert in `tantivy/tantivy.pyi` und `src/tokenizer.rs` am Tag 0.26.0:

```python
# ASCII-Bezeichner, wie in der Projektregel gefordert
from tantivy import Tokenizer, Filter, TextAnalyzerBuilder

analyzer_de = (
    TextAnalyzerBuilder(Tokenizer.simple())
    .filter(Filter.lowercase())
    .filter(Filter.remove_long(40))
    .filter(Filter.ascii_fold())
    .filter(Filter.stopword("german"))
    .filter(Filter.stemmer("german"))
    .build()
)
index.register_tokenizer("de_stem", analyzer_de)
```

`parse_language` in `src/tokenizer.rs` kennt `"german"` (Snowball-Stemmer) explizit, ebenso `Filter.stopword("german")`. Zusaetzlich existiert `Filter.split_compound(constituent_words)` fuer deutsche Komposita, das aber eine eigene Wortliste braucht (siehe unten).

**Snippets sind eingebaut.** `SnippetGenerator.create(searcher, query, schema, "body")` liefert `.fragment()` und `.to_html()` mit `<b>`-Markierung. Das ist genau das, was die Unified Search als Untertitel pro Treffer braucht, ohne Eigenbau.

**RAM-Verhalten passt zu 4-GB-Boxen.** Tantivy legt den Index bei angegebenem `path` in einem MmapDirectory ab. Gelesen wird ueber Memory-Mapping, das heisst der Index darf deutlich groesser sein als der Arbeitsspeicher; die Aufloesung uebernimmt der Page-Cache des Kernels und faellt nicht in den RSS-Bedarf des Containers. Echter Heap-Verbrauch entsteht nur beim Schreiben und ist explizit gedeckelt: `index.writer(heap_size=128_000_000, num_threads=0)` ist die Vorgabe, wir setzen `heap_size=50_000_000, num_threads=1`. Kleinere Werte bedeuten haeufigere Segment-Commits, nicht Fehler.

**ARM ist abgedeckt.** 0.26.0 liefert `manylinux_2_17_aarch64`-Wheels fuer cp310 bis cp314, inklusive cp313 und cp313t. Kein Rust-Toolchain-Zwang im Docker-Build, kein sdist-Kompilat auf dem Build-Runner.

**Loeschen und inkrementell schreiben geht.** `delete_documents_by_term(field, value)` und `delete_documents_by_query(query)` sind vorhanden, ebenso `commit()` und `index.reload()`. Damit laesst sich die Event-getriebene Reindexierung pro `fileid` sauber bauen.

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

**Warum nicht FTS5:** FTS5 kann kein deutsches Stemming. Der `porter`-Tokenizer ist englisch, `unicode61` normalisiert nur. Praktisch heisst das: "Rechnungen" findet "Rechnung" nicht. Der uebliche Ausweg waere ein eigener Python-Tokenizer, den FTS5 ueber die C-API zwar unterstuetzt, die CPython-`sqlite3`-Standardbibliothek aber nicht durchreicht. Damit muesste vor dem Schreiben in Python gestemmt und die Query identisch vorverarbeitet werden, inklusive selbst gebauter Snippet-Logik auf gestemmten Tokens. Das ist mehr Eigenbau als Tantivy einzubinden, bei schlechterem Ergebnis. FTS5 bleibt trotzdem im Stack, aber als Metadaten- und Vektorspeicher, nicht als Volltext-Engine.

**Warum nicht Meilisearch:** Meilisearch ist sprachlich fuer Deutsch sogar interessant, `charabia/src/segmenter/german.rs` mit einer mitgelieferten `dictionaries/fst/german/words.fst` zerlegt Komposita, und `ae_oe_normalizer.rs` normalisiert Umlaute. Ein Stemmer fehlt aber komplett (kein einziges `stem`-Modul im Repo), Meilisearch kompensiert bewusst mit Prefix-Suche und Typo-Toleranz. Der eigentliche Ausschlussgrund ist das Betriebsmodell: ein zweiter langlaufender Serverprozess im ExApp-Container widerspricht dem Zero-Config-Versprechen und dem RAM-Budget, und AppAPI verwaltet nur einen Container pro ExApp. Meilisearch bleibt der dokumentierte Fallback, falls Tantivy in der Praxis an Skalierungsgrenzen scheitert.

**Typesense** wurde bereits im PROJECT.md ausgeschlossen (GPLv3, Index vollstaendig im RAM). Diese Recherche bestaetigt den Ausschluss ohne Einschraenkung.

### Konkrete Ausgestaltung fuer Deutsch

**Zwei Analyzer-Felder statt Spracherkennung.** Der Body wird in zwei Felder indexiert: `body_de` (Kette oben) und `body_en` (`Filter.stemmer("english")` plus englische Stoppwoerter). Gesucht wird ueber beide mit gleicher Gewichtung, das Maximum gewinnt. Kosten: rund 1,6-fache Indexgroesse auf Platte, kein RAM-Zuwachs. Nutzen: kein Spracherkennungs-Fehlerfall bei kurzen oder gemischtsprachigen Dokumenten und keine zusaetzliche Abhaengigkeit (`lingua-language-detector`, `py3langid`). Falls die Indexgroesse spaeter stoert, ist Spracherkennung pro Dokument der Nachruestpfad.

**Komposita in v1 bewusst nicht ueber `split_compound`.** Der Filter braucht eine explizite Liste von Bestandteilswoertern (`Filter.split_compound(constituent_words: list[str])`). Eine brauchbare deutsche Liste zu beschaffen, zu lizenzieren und mitzuliefern ist ein eigenes kleines Teilprojekt. v1 loest den Fall pragmatisch:
1. automatische Prefix-Query auf dem letzten Suchbegriff, damit "Rechnung" auch "Rechnungsnummer" trifft,
2. die semantische Spur faengt den umgekehrten Fall ("Nummer" gegen "Rechnungsnummer") teilweise ab.
Ehrlich benannte Restluecke: Suffix-Treffer in Komposita sind lexikalisch nicht abgedeckt. `split_compound` mit einer mitgelieferten Wortliste ist der geplante Ausbau, Vorbild fuer die Liste ist charabias `words.fst`.

**Offen fuer die Bauphase (LOW-Konfidenz, muss gemessen werden):** ob `ascii_fold()` die Byte-Offsets fuer den `SnippetGenerator` bei Umlauten sauber haelt. Ein Test mit echten deutschen Dokumenten gehoert in die Volltext-Phase.

---

## 2. Vektorspeicher und Hybrid-Ranking

### Entscheidung

**SQLite (Standardbibliothek) + sqlite-vec 0.1.9**, Vektoren als `int8`, brute-force-KNN in einer `vec0`-Virtualtabelle. Fusion mit dem Tantivy-Ergebnis per **Reciprocal Rank Fusion**.

### Warum

SQLite ist ohnehin im Stack (Job-Queue, Datei-Metadaten, Indexstatus, Resume-Punkte). sqlite-vec ist reines C ohne Abhaengigkeiten, liefert Wheels fuer `manylinux_2_17_aarch64` und `x86_64`, speichert `float`, `int8` und `binary` und unterstuetzt Partitions- und Metadatenspalten, mit denen sich Mandanten- oder Ordnerfilter direkt in die Suche ziehen lassen. Ein Datenbankfile, ein Backup, keine zweite Konsistenzquelle.

Rechnung fuer die Zielgroesse: 200 000 Chunks * 384 Dimensionen * 1 Byte (int8) = **77 MB Vektordaten**. Ein voller Scan liest das aus dem Page-Cache, das liegt im unteren dreistelligen Millisekundenbereich. Fuer die Zielgruppe (Selfhoster, kleine Organisationen) reicht das.

### Grenzen und Ausweg

sqlite-vec ist **pre-v1**. Stabil ist v0.1.9 (31.03.2026), danach nur Alphas (`v0.1.10-alpha.4`, 18.05.2026). Das Repo enthaelt IVF- und DiskANN-Arbeit, im stabilen Release ist aber brute force die Realitaet. Konsequenz: **exakt pinnen**, nicht `>=`, und ein Upgrade nur mit Reindex-Pfad.

Ab grob 250 000 Chunks (Schaetzung, MEDIUM) wird brute force spuerbar. Ausweichpfad ist **usearch 2.26.0** (Apache-2.0, HNSW, aarch64- und cp313-Wheels, mmap-faehiger Index, int8- und binaere Quantisierung). Der Preis ist ein zweiter Persistenzpfad neben SQLite plus eigene ID-Verwaltung, deshalb nicht in v1.

Explizit nicht: **faiss-cpu** (zu gross, zu viel BLAS-Gepaeck fuer 4 GB), **hnswlib** (letztes Release 12/2023, keine aarch64- und keine cp313-Wheels), **LanceDB** (eigenes Datenformat und Arrow-Stack, deutlich zu schwer fuer den Anwendungsfall).

### Hybrid-Ranking: RRF

RRF ist der richtige Standardgriff, weil BM25-Scores und Cosinus-Aehnlichkeiten nicht auf einer Skala liegen und jede Normalisierung korpusabhaengig kalibriert werden muesste. RRF ignoriert die Scores und nutzt nur die Raenge:

```python
# score = sum ueber alle Listen: weight / (k + rank)
RRF_K = 60
weights = {"lexical": 1.0, "semantic": 1.0}
```

k=60 ist der etablierte Vorgabewert aus der Originalarbeit (Cormack et al., 2009) und der Wert, den Elasticsearch und OpenSearch als Default fahren. Beide Gewichte konfigurierbar halten, damit Admins die Semantik daempfen koennen, ohne sie abzuschalten.

Ein **Cross-Encoder-Reranker** waere qualitativ der naechste Schritt, kostet aber pro Query eine weitere Transformer-Inferenz auf CPU. Auf 4-GB-ARM-Boxen ist das nicht vertretbar: bewusst ausgeschlossen.

---

## 3. OCR

### Entscheidung

**Tesseract 5.5.0** aus Debian trixie, Sprachpakete `tesseract-ocr-deu`, `tesseract-ocr-eng`, `tesseract-ocr-osd`. Aufruf als Subprozess. Seiten-Rasterung mit **pypdfium2 5.13.0**. **OCRmyPDF nicht im Indexpfad.**

### Warum kein OCRmyPDF, obwohl es der naheliegende Kandidat ist

OCRmyPDF 17.10.0 (05.08.2026, MPL-2.0, `requires-python >= 3.11`) ist ein hervorragendes Werkzeug, aber sein Produkt ist eine **durchsuchbare PDF-Datei**. Wir brauchen nur den Text. Was wir dafuer mitbezahlen wuerden:

- ein komplettes PDF-Rewrite pro Datei ueber pikepdf, mit Temp-Dateien in Groessenordnung des Originals,
- eigene Parallelisierung (`--jobs`), die mit unserem Backpressure-Konzept kollidiert,
- eine grosse Abhaengigkeitskette (`pikepdf>=10`, `img2pdf`, `fpdf2`, `uharfbuzz`, `pi-heif`, `pdfminer-six`, `pypdfium2`),
- historisch Ghostscript. Positiv und pruefenswert: laut Installations-Doku ist Ghostscript inzwischen **optional**, pypdfium2 kann die Rasterung uebernehmen. Das entschaerft das AGPL-Argument, macht OCRmyPDF aber nicht leichter.

Der direkte Pfad ist schlanker und praezise steuerbar:

```
PDF -> pypdfium2 render(seite, scale=300/72) -> PIL Image
    -> tesseract stdin stdout -l deu+eng --psm 3
    -> Text
```

Damit bekommen wir pro Seite ein eigenes Timeout, eine eigene RAM-Obergrenze, sauberes Resume nach Abbruch und keine Zwischen-PDF. Genau das verlangt die Anforderung "robust gegen Abbrueche (Resume, Backpressure)".

OCRmyPDF bleibt eine sinnvolle **spaetere** Zusatzfunktion ("Textebene in die Originaldatei zurueckschreiben"). Das schreibt allerdings in Nutzerdateien und ist eine eigene Produktentscheidung, nicht v1.

### Text-Layer-Erkennung: OCR nur wenn noetig

Kein OCRmyPDF-`--skip-text` noetig, die Heuristik ist trivial und billig, weil pypdfium2 den Text ohnehin extrahiert:

1. Seite mit pypdfium2 `get_textpage()` auslesen.
2. Wenn die Seite mehr als N verwertbare Zeichen liefert (Startwert N=100, konfigurierbar): fertig, kein OCR.
3. Sonst Seite rastern und Tesseract aufrufen.

Die Entscheidung faellt **pro Seite**, nicht pro Dokument. Das deckt den in der Praxis haeufigsten Fall ab: digitales Dokument mit eingescannten Anhangseiten. Zusaetzlich ein Deckel: maximale Seitenzahl pro Datei fuer OCR (Startwert 100), sonst frisst ein 900-Seiten-Scan die Queue.

### ARM64 und Sprachpakete

Verifiziert gegen Debian:

| Paket | Version in trixie | Anmerkung |
|---|---|---|
| `tesseract` (Quellpaket) | 5.5.0-1 | aktuellster 5.x-Zweig ist 5.5.3 (24.07.2026) |
| `tesseract-lang` (liefert `-deu`, `-eng`, `-osd`) | 1:4.1.0-2 | `Architecture: all`, also identisch auf arm64 |
| `python3-defaults` | 3.13.5-1 | passt zur Projektvorgabe Python 3.13 |

Sprachdaten sind architekturunabhaengig, ARM ist damit kein Sonderfall. Debian liefert die schnellen Integer-Modelle (tessdata_fast), was auf ARM-CPUs die richtige Wahl ist. Wer mehr Genauigkeit will, kann `tessdata_best` per Volume nachlegen, das gehoert in die Doku, nicht in den Default.

`-l deu+eng` als Vorgabe kostet grob 1,3 bis 1,6-fache Laufzeit gegenueber einer Einzelsprache, ist fuer deutsche Selfhoster aber die richtige Zero-Config-Einstellung. `tesseract-ocr-osd` mitliefern, damit `--psm 0`-basierte Rotationskorrektur moeglich ist.

### Verworfene OCR-Alternativen

| Kandidat | Version | Warum nicht |
|---|---|---|
| RapidOCR | 3.9.2 (21.07.2026) | PP-OCR-Modelle als ONNX, Apache-2.0, teilt sich onnxruntime mit den Embeddings. Auf Fotos und schraeg fotografierten Belegen besser als Tesseract, bei sauberen deutschen Scans schlechter (Umlaute, lange Woerter). Interessanter Zusatzpfad fuer Bilddateien in einer spaeteren Phase, nicht als Standard. |
| `rapidocr-onnxruntime` | 1.4.4 (01/2025) | Vorgaengerpaket, `requires-python <3.13`, damit fuer uns tot. |
| PaddleOCR, docTR, Surya | n/a | Modelle und Laufzeiten sprengen 4 GB, teils Torch-Zwang. Unvereinbar mit dem Hardware-Ziel. |
| VLM-basiertes OCR | n/a | Braucht GPU oder mehrere GB RAM. Widerspricht dem Kernversprechen. |

`pytesseract` (0.3.13, 08/2024) ist ein duenner Wrapper um denselben Subprozessaufruf. Bei einem einzigen Aufrufmuster ist `subprocess.run` mit Timeout klarer und liefert uns die Fehlerbehandlung, die wir ohnehin selbst brauchen. Keine Abhaengigkeit noetig.

---

## 4. Lokale Embeddings

### Entscheidung

**fastembed 0.8.0** als Laufzeit, Modell **intfloat/multilingual-e5-small** (384 Dimensionen, MIT), beim Image-Build dynamisch auf **int8** quantisiert und in das Image gebacken. `onnxruntime 1.28.0`.

### Warum dieses Modell

fastembeds eingebaute mehrsprachige Auswahl ist duenn und passt schlecht (verifiziert in `fastembed/text/pooled_embedding.py` und `pooled_normalized_embedding.py`):

| Eingebautes Modell | Dim | Groesse | Bewertung |
|---|---|---|---|
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 | 0,22 GB | Klein, aber ein STS-/Paraphrase-Modell von 2021, nicht auf Retrieval trainiert. Schwach bei "Frage gegen Dokumentabschnitt". |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | 768 | 1,00 GB | Zu gross fuer 4 GB, gleiches Trainingsproblem. |
| `intfloat/multilingual-e5-large` | 1024 | 2,24 GB | Qualitativ top, auf der Zielhardware indiskutabel. |
| `jinaai/jina-embeddings-v2-base-de` | 768 | 0,32 GB (Angabe) | Deutsch-englisch bilingual, Apache-2.0, 8k Kontext. **Aber:** fastembed warnt im Code explizit, dass dieses Modell wegen onnxruntime-Aenderungen inzwischen im **fp32-Original** statt fp16 laeuft, der reale Fussabdruck ist also rund doppelt so gross wie ausgewiesen. Dazu 768 statt 384 Dimensionen, also doppelter Vektorspeicher und doppelte Scan-Kosten. |
| `jinaai/jina-embeddings-v3` | 1024 | n/a | **Lizenz CC BY-NC**. Fuer eine verteilte AGPL-App im App Store nicht nutzbar. Ausschluss. |

`multilingual-e5-small` (118M Parameter, MIT) ist gezielt auf Retrieval trainiert, deckt Deutsch gut ab und bleibt bei 384 Dimensionen. Es ist in fastembed nicht eingebaut, laesst sich aber sauber registrieren, die API ist verifiziert:

```python
from fastembed import TextEmbedding
from fastembed.common.model_description import ModelSource, PoolingType

TextEmbedding.add_custom_model(
    model="local/multilingual-e5-small-int8",
    pooling=PoolingType.MEAN,
    normalization=True,
    sources=ModelSource(hf="intfloat/multilingual-e5-small"),
    dim=384,
    model_file="onnx/model.onnx",
    license="mit",
)
embedder = TextEmbedding(
    model_name="local/multilingual-e5-small-int8",
    cache_dir="/models",
    threads=2,
    lazy_load=True,
)
```

### Quantisierung: selbst quantisieren, nicht fremdquantisiert ziehen

Zwei Fallstricke, beide verifiziert am HuggingFace-Dateibestand:

- `intfloat/multilingual-e5-small` liefert `onnx/model_qint8_avx512_vnni.onnx`. Das ist **x86-only** (AVX512-VNNI). Auf ARM entweder unbrauchbar oder pathologisch langsam. Nicht verwenden.
- `Xenova/multilingual-e5-small` liefert plattformneutrale `onnx/model_quantized.onnx`, `model_int8.onnx`, `model_uint8.onnx`, hat aber **kein Lizenzfeld** in der Modellkarte. Fuer ein App-Store-Release mit AGPL-Anspruch ist das eine unnoetige Unschaerfe.

Sauberer Weg: im Docker-Build `onnx/model.onnx` von `intfloat` (MIT, eindeutig) ziehen und mit `onnxruntime.quantization.quantize_dynamic` selbst nach int8 wandeln. Ergebnis: reproduzierbar, klare Herkunft, rund 120 MB statt rund 470 MB im Image, laeuft auf amd64 und arm64 identisch.

Zwingend: Das Modell muss **im Image liegen**. Ein Runtime-Download von HuggingFace beim ersten Start bricht das Zero-Config-Versprechen (Firewalls, Rate-Limits, Offline-Installationen). `HF_HUB_OFFLINE=1` und ein fester `cache_dir` gehoeren in das Dockerfile. Als Sicherheitsnetz zum Vergleich: nc_py_api hat genau fuer diesen Schmerz in 0.30.4 Retry-Logik fuer Modell-Downloads nachgeruestet, das ist ein Symptom des Problems, nicht die Loesung.

### E5-Praefixe nicht vergessen

E5-Modelle erwarten `"query: "` vor der Suchanfrage und `"passage: "` vor dem Dokumentabschnitt. Ohne die Praefixe faellt die Retrieval-Qualitaet messbar ab. fastembed bietet dafuer `query_embed()` und `passage_embed()`, die Praefixbehandlung greift aber nur bei bekannten Modellen. Bei einem selbst registrierten Modell die Praefixe **explizit im eigenen Code** setzen. Das ist die haeufigste stille Fehlerquelle in diesem Baustein.

### Sparsam-Modus fuer sehr schwache Boxen

`minishlab/potion-multilingual-128M` (model2vec, MIT, statische Embeddings, ONNX vorhanden) braucht keine Transformer-Inferenz, ist um Groessenordnungen schneller und praktisch RAM-frei. Qualitativ deutlich unter e5-small, aber besser als keine semantische Spur. Als optionale Stufe fuer 2-GB-Boxen oder als Notausgang, falls die Erstindexierung auf einem Raspberry Pi 4 nicht in vertretbarer Zeit durchlaeuft. Nicht Default.

### Chunking

**semantic-text-splitter 0.32.0** (MIT, Rust, `cp310-abi3`-Wheels auch fuer `manylinux_2_28_aarch64`). Kann direkt gegen einen HuggingFace-Tokenizer chunken, und `tokenizers` ist ueber fastembed ohnehin installiert. Damit trifft man das 512-Token-Fenster von e5-small exakt, statt es ueber Zeichenzahl zu raten. Alternative waere ein eigener Splitter, der Aufwand lohnt bei dieser Paketgroesse nicht. **chonkie** hat keine aarch64-Wheels, faellt raus.

---

## 5. Textextraktion in reinem Python

Kein Java, kein Tika, keine LibreOffice-Konvertierung. Alles unten hat aarch64-Wheels oder ist pures Python.

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

**markitdown 0.1.7** (MIT, Microsoft, 29.07.2026) sieht auf den ersten Blick attraktiv aus, ist aber das falsche Werkzeug:

- Zielprodukt ist **Markdown fuer LLM-Prompts**, nicht Rohtext fuer einen Index. Tabellenformatierung, Ueberschriftenmarkierung und Bildplatzhalter sind fuer uns Ballast.
- Es zieht `magika~=0.6.1` als **Pflicht**-Abhaengigkeit, und magika bringt eine eigene onnxruntime-Nutzung samt Modell mit, nur zur Dateityperkennung. Wir haben mit dem Nextcloud-Mimetype plus `python-magic` bereits genug Information.
- Der PDF-Pfad haengt an `pdfminer-six` und `pdfplumber`, beide pur Python und um ein Vielfaches langsamer als pypdfium2.
- Es kapselt genau die Bibliotheken, die wir direkt einbinden, und nimmt uns dabei die Kontrolle ueber Limits, Timeouts und Teilausgaben bei Fehlern.

`pdfminer.six` (20260107) waere als Fallback denkbar, wenn pypdfium2 an einem PDF scheitert. Da pypdfium2 die deutlich robustere Engine ist, waere das ein Fallback von gut auf langsamer und nicht besser: weglassen und Fehler sauber protokollieren.

**PyMuPDF** (1.28.2) ist technisch exzellent, aber AGPL-3.0 oder Artifex-Kommerzlizenz. Mit AGPL-3.0 fuer unser Projekt formal vereinbar, trotzdem nicht noetig: pypdfium2 leistet dasselbe unter BSD und Apache und laesst dem Projekt spaetere Lizenzoptionen offen.

---

## 6. ExApp-Geruest

### Entscheidung

**nc_py_api[app] >= 0.30.3** (PyPI-Stand 0.30.3 vom 11.08.2026; das Changelog fuehrt bereits 0.30.4 vom selben Tag) plus **FastAPI 0.141.1** und **uvicorn[standard]**, exakt wie im Schwesterprojekt nextcloud-mcp-connector.

### Kritischer Punkt: von Tag eins asynchron

Aus dem nc_py_api-Changelog, Version 0.30.0 (29.03.2026):

> "All remaining sync entry points (`Nextcloud`, `NextcloudApp`, `TalkBot`, `nc_app`, `talk_bot_msg`, sync `enabled_handler`/`trigger_handler` in `set_handlers`) now emit `DeprecationWarning`; they will be removed in v0.31.0."

Sync ist also in der **naechsten** Minor-Version weg. Alles gegen `AsyncNextcloudApp` bauen. Wer hier synchron startet, schreibt die halbe Integrationsschicht in wenigen Monaten neu. Das ist der wichtigste einzelne Hinweis fuer die erste Bauphase.

Weiter aus dem Changelog relevant:
- 0.30.2 hebt den Boden auf `starlette>=1.0.1` wegen **CVE-2026-48710 (BadHost)**, einer Pfad-Desynchronisation, die pfadbasierte Autorisierung aushebeln kann, und `fastapi>=0.133`. Fuer eine App mit Berechtigungsdurchgriff ist das keine Formalie: die Untergrenzen nicht unterlaufen.
- 0.30.3 fixt ein PROPFIND-Leck, bei dem sich Property-Listen pro Aufruf aufblaehten und langlaufende Clients dem Server die Worker wegfrassen. Genau unser Nutzungsprofil (Dauerindexierung). **Mindestens 0.30.3.**

### Nextcloud-Versionsfenster

Aktueller Serverstand am 13.08.2026: **34.0.3**, gepflegt daneben 33.0.8 und 32.0.14. Nextcloud 31 ist zum geplanten Baustart nicht mehr relevant, die Angabe "NC 31-34" aus PROJECT.md sollte korrigiert werden.

Empfehlung fuer beide `info.xml`:

```xml
<dependencies>
    <php min-version="8.2"/>
    <nextcloud min-version="32" max-version="35"/>
</dependencies>
```

Belege: `context_chat` 5.5.0-beta0 und `context_chat_backend` 5.4.1 deklarieren exakt `min-version="32" max-version="35"`. PHP 8.2 ist der kleinste gemeinsame Nenner ueber NC 32 bis 34 (NC 32: 8.1 bis 8.4; NC 33 und 34: 8.2 bis 8.5).

Kleiner Vorbehalt: das nc_py_api-README fuehrt im Badge noch "Nextcloud 31 | 32 | 33". NC 34 ist dort noch nicht nachgezogen, praktische Probleme sind daraus nicht ableitbar, aber ein NC-34-Smoke-Test gehoert in die CI.

### HaRP statt Docker-Socket-Proxy

Aus dem AppAPI-README:

> "**HaRP** (High-performance AppAPI Reverse Proxy) is the newer and recommended Deploy Daemon" fuer Nextcloud 32+.

HaRP routet direkt zur ExApp am PHP-Prozess vorbei, kann WebSockets und nutzt FRP-Tunnel, sodass der ExApp-Container keine Ports auf dem Host oeffnet. Die Doku hat dafuer eine eigene Seite (`ExAppHarpIntegration.rst`). Von Anfang an HaRP-konform bauen, DSP nicht mehr als Zielplattform behandeln. Deckt sich mit der Lehre aus dem MCP-Connector-Projekt.

AppAPI selbst folgt inzwischen der Serverversionierung: Tags `v34.0.3`, `v34.0.2`, und der `main`-Branch traegt `35.0.0-dev.1` mit `<nextcloud min-version="35" max-version="35"/>`. Beim Testen die zur Serverversion passende AppAPI verwenden.

### Bestaetigt: AppAPI kann keine Suchanbieter registrieren

Vollstaendige Liste der ExApp-registrierbaren Nextcloud-APIs, ausgelesen aus dem Verzeichnisbaum von `nextcloud/documentation`, Pfad `developer_manual/exapp_development/tech_details/api/`:

`appconfig`, `events_listener`, `exapp`, `fileactionsmenu`, `logging`, `notifications`, `occ_command`, `other_ocs`, `preferences`, `routes`, `settings`, `talkbots`, `topmenu`, `utils`.

**Keine Suche, keine Unified Search.** Der Kernbefund aus PROJECT.md ist damit auf HIGH-Konfidenz bestaetigt, die PHP-Companion-App ist nicht optional, sondern der einzige Weg.

### Events Listener fuer inkrementelle Indexierung

Verifiziert aus `events_listener.rst`:

- Registrierung: `POST /apps/app_api/api/v1/events_listener` mit `{"eventType": "node_event", "actionHandler": "/action_handler_route", "eventSubtypes": []}`
- Unterstuetzte Subtypen fuer `node_event`: `NodeCreatedEvent`, `NodeTouchedEvent`, `NodeWrittenEvent`, `NodeDeletedEvent`, `NodeRenamedEvent`, `NodeCopiedEvent`

Wichtige Einschraenkung, woertlich aus der Doku:

> "Unlike PHP events, all information from events comes to the ExApp **asynchronously**, more like a notification system in order to not slow down the server."

Konsequenz fuer die Architektur: Events sind ein Hinweis, keine Garantie. Der Indexer braucht zusaetzlich einen periodischen Abgleich ueber ETag oder mtime, sonst laufen verpasste Events dauerhaft aus dem Ruder. `FsNode.etag_unquoted` aus nc_py_api 0.30.3 ist genau dafuer gedacht.

---

## 7. PHP-Companion-App

### Minimaler Umfang

Vier Dateien, kein Composer, kein Build-Schritt, kein JavaScript:

```
appinfo/info.xml
lib/AppInfo/Application.php     -> $context->registerSearchProvider(SearchProvider::class);
lib/Search/SearchProvider.php   -> implements IFilteringProvider
composer.json                   -> nur PSR-4-Autoload-Mapping
```

Alle verwendeten APIs sind gegen `nextcloud/server` Branch `stable34` verifiziert:

| API | Datei | Seit |
|---|---|---|
| `IRegistrationContext::registerSearchProvider(string $class)` | `lib/public/AppFramework/Bootstrap/IRegistrationContext.php` | NC 20 |
| `OCP\Search\IProvider` mit `getId()`, `getName()`, `getOrder(string $route, array $routeParameters): ?int`, `search(IUser $user, ISearchQuery $query): SearchResult` | `lib/public/Search/IProvider.php` | NC 20, `getOrder` nullable seit NC 28 |
| `OCP\Search\IFilteringProvider` mit `getSupportedFilters()`, `getAlternateIds()`, `getCustomFilters()` | `lib/public/Search/IFilteringProvider.php` | NC 28 |
| `OCP\Search\IInAppSearch` | `lib/public/Search/IInAppSearch.php` | NC 28 |
| `SearchResult`, `SearchResultEntry` (`thumbnailUrl`, `title`, `subline`, `resourceUrl`, `icon`, `rounded`, `attributes`) | `lib/public/Search/` | NC 20 |

`IFilteringProvider` lohnt sich sofort: damit unterstuetzt die App die Standardfilter der Unified Search (Person, Datum, Titel) und kann eigene Filter deklarieren, ohne eigenes UI zu bauen. Der Snippet aus Tantivy landet in `subline`.

### Der Proxy zur ExApp

Verifiziert in `nextcloud/app_api`, `lib/PublicFunctions.php`:

```php
public function exAppRequest(
    string $appId,
    string $route,
    ?string $userId = null,
    string $method = 'POST',
    array $params = [],
    array $options = [],
    ?IRequest $request = null,
): array|IResponse
```

Das ist die von AppAPI oeffentlich zugesagte Schnittstelle und genau das Muster, das context_chat ueber seinen `LangRopeService` nutzt. Wichtige Details:

- `exAppRequestWithUserInit()` ist **seit AppAPI 3.0.0 deprecated**, nicht verwenden.
- Bei unbekannter ExApp liefert die Methode `['error' => ...]` statt einer Exception: der Rueckgabewert muss geprueft werden, sonst zeigt die Suche stumm nichts an.
- Die PHP-App muss `app_api` als Abhaengigkeit fuehren und bei fehlendem oder gestopptem Backend ein leeres `SearchResult` mit klarer Meldung zurueckgeben, nicht in einen Fehler laufen. Die Unified Search ruft alle Provider parallel; ein haengender Provider verlangsamt die gesamte Suche. **Hartes Timeout** ueber `$options` setzen, Startwert 2 Sekunden.

### Berechtigungsdurchgriff: in PHP filtern, nicht in Python

Empfehlung mit Nachdruck, weil sie die Sicherheitsanforderung strukturell loest statt sie nachzubauen:

1. Die ExApp bekommt Query plus `userId` und liefert **Kandidaten** zurueck, zum Beispiel die 100 besten `fileid`-Werte mit Score und Snippet.
2. Die PHP-App filtert ueber `IRootFolder::getUserFolder($userId)->getFirstNodeById($fileid)`. Nextcloud selbst entscheidet damit ueber Sichtbarkeit, inklusive Shares, Gruppenordner, externem Speicher und Trashbin.
3. Die ersten 20 ueberlebenden Treffer gehen in das `SearchResult`.

Vorteil: kein zweites, driftendes Berechtigungsmodell im Python-Index, und ein Bug im Index kann keine fremden Dokumente sichtbar machen. Kosten: einige DB-Lookups pro Suche, im Millisekundenbereich. Die ExApp fuehrt trotzdem eine grobe Zugriffsliste, um die Kandidatenmenge vorzufiltern, aber sie ist nicht die Autoritaet.

### App-Store-Verpackung: zwei Eintraege, zwei Zertifikate

Das ist der planungsrelevanteste Befund dieses Abschnitts. Das context_chat-Vorbild zeigt es: **zwei getrennte App-Store-Eintraege**.

| Teil | Store-Bereich | Beispiel |
|---|---|---|
| PHP-Companion | Apps | `context_chat` |
| Python-ExApp | External Apps | `context_chat_backend` |

Jeder Eintrag hat eine eigene App-ID und braucht ein **eigenes Zertifikat**, also **zwei CSR-Vorgaenge** mit jeweils eigener Vorlaufzeit. Das war schon im MCP-Connector-Projekt ein Terminrisiko; hier verdoppelt es sich. Beide App-IDs muessen vor dem ersten Bau-Commit eingefroren werden.

Weitere Punkte aus dem context_chat-Vorbild:
- Beide Teile fuehren **dieselbe Major- und Minor-Version**, damit Nutzer sie nicht auseinanderlaufen lassen. Das gehoert in die Release-Automatisierung, nicht in die Doku.
- Die ExApp-`info.xml` traegt `<external-app><docker-install><registry>ghcr.io</registry>...</docker-install><routes>...</routes><environment-variables>...</environment-variables></external-app>`. Ueber `<environment-variables>` bekommen Admins Einstellungen (OCR-Sprachen, Modellwahl, Indexpfad), ohne dass wir eine Settings-UI bauen: der guenstigste Weg zu "sinnvolle Defaults, keine Pflichteinstellungen".
- Die ExApp deklariert Routen samt `access_level` (`ADMIN`, `USER`, `PUBLIC`) direkt in der `info.xml`. Die Statusseite laeuft ueber `ADMIN`, die Suchroute wird ausschliesslich von der PHP-App gerufen.
- Fuer die PHP-App: Tarball bauen, mit dem App-Zertifikat signieren (`openssl dgst -sha512 -sign`), Release-Metadaten an `https://apps.nextcloud.com/api/v1/apps/releases` posten. `krankerl` nimmt einem das ab, ist aber nicht zwingend; ein Makefile reicht. (MEDIUM: Prozessdetails vor der Einreichung gegen die dann aktuelle Store-Doku pruefen.)

---

## RAM-Budget auf einer 4-GB-Box

Schaetzung, Konfidenz MEDIUM. Die Zahlen sind Planungsgroessen, keine Messwerte, und gehoeren in der ersten Bauphase auf echter ARM-Hardware verifiziert.

| Komponente | Ruhezustand | Spitze | Stellschraube |
|---|---|---|---|
| Python 3.13 + FastAPI + uvicorn + nc_py_api | 120-180 MB | n/a | ein Worker |
| Tantivy Suche (mmap) | ~0 RSS | ~0 | Index liegt im Page-Cache |
| Tantivy Writer | n/a | 50-130 MB | `heap_size`, `num_threads=1` |
| SQLite + sqlite-vec | ~10 MB | 80-120 MB bei vollem Vektorscan | `cache_size`, int8 statt float32 |
| onnxruntime + e5-small int8 | 0 bei `lazy_load=True` | 250-400 MB | `threads=2`, Batchgroesse 8-16 |
| Tesseract, eine Seite bei 300 dpi A4 | 0 | 300-600 MB | ein Worker, DPI, Seitendeckel |
| pypdfium2 Rasterung | 0 | 50-150 MB | Skalierung, Seite fuer Seite freigeben |

**Die entscheidende Regel:** OCR und Embedding-Berechnung duerfen **nie gleichzeitig** laufen. Ein einziger serieller Indexier-Worker mit einer SQLite-Job-Queue haelt die Spitze bei rund 1,2 GB. Zwei parallele Worker reissen ein 4-GB-System mit gleichzeitig laufendem Nextcloud, MariaDB und Redis auf. Das ist eine Architekturentscheidung, keine Optimierung: `INDEX_WORKERS=1` als Default, Erhoehung nur ueber eine ausdrueckliche Admin-Einstellung.

Zweite Regel: alle Speicherfresser sind **Spitzen pro Datei**, nicht Dauerlast. Der Ruhezustand des Containers bleibt bei rund 200-250 MB, was neben einer normalen Nextcloud-Installation vertretbar ist. Zum Vergleich der Wettbewerbsvorteil: Context Chat braucht laut PROJECT-Recherche 12 GB.

---

## Installation

### Systempakete im Image

```dockerfile
FROM python:3.13-slim-trixie

RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-deu \
        tesseract-ocr-eng \
        tesseract-ocr-osd \
    && rm -rf /var/lib/apt/lists/*
```

`python:3.13-slim-trixie` liefert Python 3.13.15 und wird laut offiziellem Dockerfile mit `--enable-loadable-sqlite-extensions` gebaut. Ohne dieses Flag laesst sich sqlite-vec nicht laden: das ist der Grund, warum wir nicht `debian:trixie-slim` plus `apt install python3` nehmen. Debian trixie liefert Tesseract 5.5.0 und die Sprachdaten als `Architecture: all`, damit ist der ARM-Build identisch zum amd64-Build.

### Python-Abhaengigkeiten (uv, exakt gepinnt)

```toml
[project]
requires-python = ">=3.13"
dependencies = [
    # ExApp-Geruest
    "nc-py-api[app]>=0.30.3,<0.31",
    "fastapi>=0.141.1,<0.142",
    "starlette>=1.0.1",

    # Suche
    "tantivy==0.26.0",
    "sqlite-vec==0.1.9",

    # Embeddings
    "fastembed==0.8.0",
    "onnxruntime==1.28.0",
    "semantic-text-splitter==0.32.0",

    # Textextraktion
    "pypdfium2==5.13.0",
    "pypdf==6.16.1",
    "python-docx==1.2.0",
    "python-pptx==1.0.2",
    "openpyxl==3.1.5",
    "lxml>=6,<7",
    "striprtf==0.0.32",
    "charset-normalizer==3.5.0",
    "pillow>=11,<13",
    "pi-heif>=1,<2",

    # Pflicht aus der globalen Python-Regel
    "tzdata>=2026.1",
]

[dependency-groups]
dev = [
    "ruff==0.14.4",
    "pyright==1.1.408",
    "vulture==2.14",
    "pytest==8.4.2",
    "pytest-asyncio==1.2.0",
    "coverage==7.10.7",
]
```

Dev-Versionen sind Platzhalter und beim Projektstart auf den dann aktuellen Stand zu setzen; die globale Regel verlangt exakte Pins, den Regelsatz `["E","F","I","UP","B","ASYNC","S","SIM","C4","RUF","PT","RET","A","ISC"]`, `ruff format --check`, pyright basic, vulture mit min-confidence 80 und alle Gates in der CI.

**Wichtig zu `onnxruntime`:** fastembed 0.8.0 fordert fuer Python 3.13 `onnxruntime>1.21.0, !=1.24.0, !=1.24.1`. 1.28.0 (25.07.2026) erfuellt das, hat `requires-python >=3.11` und liefert `cp313`-Wheels fuer `manylinux_2_27_aarch64` und `x86_64`. Kein Selbstbau auf ARM noetig, was bei onnxruntime frueher der grosse Schmerz war.

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

Kein einziges Paket im Stack braucht einen Compiler im Docker-Build. Das haelt den Multi-Arch-Build ueber QEMU in ertraeglicher Zeit.

---

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

---

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

---

## Stack Patterns by Variant

**Bei 4 GB RAM oder ARM (Default, Zielhardware):**
- `INDEX_WORKERS=1`, OCR und Embedding strikt seriell
- Tantivy `heap_size=50_000_000`, `num_threads=1`
- e5-small int8, `threads=2`, `lazy_load=True`, Batchgroesse 8
- OCR-Deckel: 100 Seiten pro Datei, 300 dpi, 30 s Timeout pro Seite

**Bei 8 GB RAM und amd64:**
- `INDEX_WORKERS=2`, weiterhin OCR und Embedding nicht gleichzeitig im selben Worker
- Tantivy `heap_size=128_000_000`, `num_threads=2`
- optional e5-small fp32 statt int8

**Bei mehr als 250 000 Chunks:**
- Vektorspeicher von sqlite-vec auf usearch HNSW umstellen
- Reindex noetig, deshalb frueh eine Indexversion im Schema fuehren

**Bei ueberwiegend englischen Bestaenden:**
- `body_en` staerker gewichten oder `body_de` abschalten, spart rund 40 Prozent Indexgroesse

---

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

---

## Offene Punkte fuer die Bauphasen

Ehrlich benannte Luecken, die Recherche allein nicht schliessen kann:

1. **Snippet-Offsets mit `ascii_fold()` und Umlauten** (LOW). Muss mit echten deutschen PDFs getestet werden, bevor der Analyzer festgezurrt wird.
2. **Reale RAM-Spitzen auf ARM** (MEDIUM). Alle Zahlen der Budgettabelle sind Schaetzungen. Ein Messlauf auf einem Raspberry Pi 5 mit 4 GB oder vergleichbar gehoert in die erste Bauphase.
3. **Retrieval-Qualitaet von e5-small int8 auf Deutsch** (MEDIUM). Der int8-Qualitaetsverlust liegt bei mehrsprachigen Retrieval-Modellen erfahrungsgemaess im niedrigen einstelligen Prozentbereich, ist aber nicht fuer genau dieses Modell belegt. Kleines deutsches Testset bauen, fp32 gegen int8 vergleichen.
4. **Schwelle, ab der brute-force-KNN kippt** (MEDIUM). Die 250 000 sind gerechnet, nicht gemessen.
5. **Zuverlaessigkeit des AppAPI Events Listener** (MEDIUM). Die Doku nennt die Zustellung ausdruecklich asynchron und benachrichtigungsartig. Wie viele Events unter Last verloren gehen, ist unbekannt: der periodische ETag-Abgleich ist deshalb Pflicht, nicht Kuer.
6. **Store-Einreichungsprozess fuer zwei Apps gleichzeitig** (MEDIUM). Zwei CSR-Vorgaenge, zwei Zertifikate, gekoppelte Versionierung. Vorlaufzeiten frueh klaeren, Erfahrung aus dem MCP-Connector nutzen.
7. **Deutsche Wortliste fuer `split_compound`** (offen). Beschaffung und Lizenz ungeklaert, deshalb bewusst nicht in v1.

---

## Sources

**Context7**
- `/quickwit-oss/tantivy-py` , Tokenizer, SnippetGenerator, IndexWriter, Schema (HIGH)

**Primaerquellen, direkt gelesen (HIGH)**
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

**Sekundaerquellen (MEDIUM)**
- meilisearch.com Doku, Known Limitations , Indexgroesse und virtueller Adressraum
- `nextcloud/server` Wiki, Releases and PHP versions , PHP-Matrix fuer NC 32 bis 34

**Nicht belegbar, als Schaetzung markiert (LOW bis MEDIUM)**
- alle RAM-Zahlen der Budgettabelle
- die 250 000-Chunk-Schwelle fuer brute-force-KNN
- der Qualitaetsverlust durch int8-Quantisierung bei e5-small auf Deutsch

---
*Stack research for: Nextcloud-ExApp mit OCR, Volltext- und Semantiksuche*
*Researched: 2026-08-15*
