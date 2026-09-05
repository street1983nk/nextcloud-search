---
phase: 06-semantische-suche
plan: 05
subsystem: backend
tags: [embeddings, e5-praefixe, chunking, semantic-text-splitter, onnxruntime, zeichen-offsets, caps, verdikt, a11]

# Dependency graph
requires:
  - phase: 06-semantische-suche
    provides: "06-01: das int8-Modell (118.101.091 Byte) und der Tokenizer an FINDLING_EMBED_MODEL_DIR, offline im Abbild"
  - phase: 06-semantische-suche
    provides: "06-02: die Messungen hinter Chunkgroesse, Chargengroesse und Sequenzlaenge (Zeichen je Token, Token je Sekunde, Scan-Latenz)"
  - phase: 06-semantische-suche
    provides: "06-03: die gemessene Praefixwirkung, die hier zur Konstante und zum Test wird (D-05)"
  - phase: 06-semantische-suche
    provides: "06-04: die Form eines Chunks (Ordinal, zwei Zeichenoffsets, 384 Byte int8) und die Breitenpruefung"
  - phase: 03-ocr
    provides: "extract/ocr.py als Vorbild fuer die Cap-Kaskade, die Abhaengigkeit ueber ihren Namen und das ehrliche Verdikt"
provides:
  - "config.py: sieben Embedding-Einstellungen mit Herkunft, Bereichspruefung und je einem Test, dazu zwei gekoppelte Pruefungen"
  - "embed/chunker.py: chunk_spans und make_splitter, Zeichen-Spans, Deckel vor dem Splitten"
  - "embed/model.py: EmbeddingModel mit E5-Praefixen, Lazy Load, Chargen aus den Einstellungen und dem Verdikt embedding_unavailable"
  - "embed/model.py::to_int8: die zweite Quantisierungsstufe, mit der Skala am Modell"
  - "die Antwort auf A11, am Quelltext von fastembed 0.8.0 gemessen"
  - "der Rangbeleg fuer D-05 gegen das echte Modell: 9 von 10 deutschen Faellen"
affects: [06-06 Durchstich und Degradieren, 06-07 Embedding-Zweitspur, 06-08 Statusseite, 06-11 Speichermessung, docs/embeddings.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Einstellung, die eine andere begrenzt, wird nach dem Lesen gegen sie geklemmt statt sie zu ignorieren, und die Warnung nennt die Variable, die sich bewegt hat"
    - "Zwei Tokenizer-Instanzen aus derselben Datei, weil enable_truncation eine Eigenschaft des Objekts ist und eine geteilte Instanz den Deckel des Chunkers still halbieren wuerde"
    - "Ein Verdikt, das nicht in die geschlossene Liste der Dateizustaende gehoert, bekommt seinen eigenen Namen im eigenen Modul statt einen Platz in einer Liste, die im Gleichschritt mit PHP steht"
    - "Ein Ladefehler wird einmal gemerkt und nicht je Datei wiederholt: ein Log mit 50.068 gleichen Warnungen ist ein Log ohne Warnungen"
    - "Eine Attrappe belegt, was auf jeder Maschine gelten muss; das echte Artefakt belegt, was nur mit ihm messbar ist"

key-files:
  created:
    - backend/src/findling/embed/chunker.py
    - backend/src/findling/embed/model.py
    - backend/tests/test_chunker.py
    - backend/tests/test_embed_model.py
  modified:
    - backend/src/findling/config.py
    - backend/tests/test_config.py
    - backend/src/findling/store/vectors.sql
    - docs/embeddings.md

key-decisions:
  - "Chunkgroesse 510 statt 512: der ausgelieferte Tokenizer setzt zwei Sondertoken um jeden Text (gemessen 05.09.2026), ein Chunk mit 512 eigenen Token kaeme als 514 an der Sitzung an und verloere seine letzten beiden ohne Fehlermeldung"
  - "Chunkgroesse 510 und nicht 256, obwohl Messung B Charge 2 bei Sequenz 256 als sparsamste UND schnellste Kombination ausweist: 256 haette die Chunkzahl verdoppelt, den Scan jeder Nutzersuche verdoppelt und die 250.000er-Schwelle von 125.000 auf 62.500 Dokumente gezogen. Eine Stunde einmalig gegen Kosten bei jeder Suche"
  - "onnxruntime wird direkt angesteuert und nicht ueber fastembed (A11 beantwortet): fastembed 0.8.0 reicht von den Sitzungsoptionen ausschliesslich enable_cpu_mem_arena durch und die Sequenzlaenge gar nicht, weil sie aus tokenizer_config.json gelesen wird. Hebel 5 waere damit nicht unserer"
  - "enable_cpu_mem_arena=False: die Arena gibt Speicher nicht ans Betriebssystem zurueck, die Aktivierungsspitze der Zweitspur wuerde sonst zur Dauerlast neben der OCR-Spitze"
  - "embedding_unavailable ist eine Konstante in embed/model.py und KEIN neuer Reason in extract/errors.py: jene Liste ist das geschlossene Vokabular eines beurteilten Dateizustands, steht im Gleichschritt mit store/repo.py und der PHP-Beschriftung, und eine ausgebliebene Einbettung sagt nichts darueber, ob die Datei indexiert wurde"
  - "Der Modell-Wrapper haelt drei Zustaende (nie versucht, versucht und gescheitert, geladen), damit ein fehlendes Modell nicht je Dokument gesucht und je Dokument gemeldet wird"
  - "to_int8 lebt im Modellmodul, weil die Skala eine Eigenschaft des Modells ist: e5 liefert normierte Vektoren, also ist 127 der ganze Faktor"
  - "Die geschaetzten 250 bis 400 MB an INDEX_WORKERS werden nicht durch eine andere Schaetzung ersetzt, sondern aufgeteilt: die Modellgewichte sind mit 118.101.091 Byte gemessen, die Aktivierungsspitze ist als ungemessen benannt (A5) und gehoert an den Lasttest der Zweitspur"

patterns-established:
  - "Wenn der Plan eine gemessene Zahl verlangt, die es nicht gibt, wird die Luecke benannt statt eine zweite Schaetzung als Messung auszugeben"
  - "Eine gerechnete Zeile in einem Messbericht wird zur Untergrenze erklaert, sobald die Messung sie ueberholt, und beide Enden stehen daneben"

requirements-completed: [SEM-01]

# Metrics
duration: 30min
completed: 2026-09-05
---

# Phase 6 Plan 05: Chunker und Modell-Wrapper Summary

**Aus Text werden Vektoren: ein Chunker, der in Zeichen rechnet und vor dem Splitten deckelt, ein Modell-Wrapper mit den E5-Präfixen und einem ehrlichen Verdikt statt einer Ausnahme, sieben Einstellungen mit Herkunft und Bereichsprüfung, und drei stille Fehler, die jetzt laut sind: die zwei Sondertoken, die eine Chunkgrösse von 512 unbemerkt beschneiden, die geteilte Tokenizer-Instanz, die den 1.024-Token-Deckel halbiert hätte, und die gerechnete Zeile "zwei Chunks je Dokument", die gemessen zwei bis drei sind.**

## Performance

- **Duration:** rund 30 min
- **Started:** 2026-09-05T06:31:06Z
- **Completed:** 2026-09-05T07:00:24Z
- **Tasks:** 3 von 3
- **Files modified:** 8 (4 neu, 4 geändert)

## Accomplishments

- **D-05 ist nicht nur gesetzt, sondern am ausgelieferten Modell nachgemessen.** Der Präfixtest lief im Abbild `findling-sem-probe:local` gegen die echten 118.101.091 Byte: in **9 von 10** deutschen Fällen ändert sich die Rangfolge, und in einem davon (`de-03`) wechselt sogar der beste Treffer, von der richtigen Passage auf eine falsche. Das Vergessen der Präfixe ist damit nicht mehr ein Qualitätsverlust auf dem Papier, sondern ein belegter Fehltreffer.
- **Zwei stille Verluste sind gefunden worden, bevor sie entstehen konnten.** Der Tokenizer setzt zwei Sondertoken um jeden Text, gemessen am ausgelieferten Artefakt; ein Chunk mit 512 eigenen Token wäre als 514 an der Sitzung angekommen und hätte seine letzten beiden verloren, ohne dass etwas fehlschlägt. Und `enable_truncation` ist eine Eigenschaft der Tokenizer-Instanz, also hätte eine geteilte Instanz den 1.024-Token-Deckel des Chunkers auf 512 halbiert: die zweite Hälfte jedes Dokuments hätte aufgehört zu existieren. Beides ist jetzt getrennt, kommentiert und getestet.
- **A11 ist beantwortet, und zwar am Quelltext.** `fastembed/common/onnx_model.py` führt `EXPOSED_SESSION_OPTIONS = ("enable_cpu_mem_arena",)`, und `fastembed/common/preprocessor_utils.py` liest die Trunkierungslänge aus `tokenizer_config.json`. Die Sitzungsoptionen sind also zur Hälfte erreichbar und die Sequenzlänge gar nicht, und die Sequenzlänge ist der stärkste der vier gemessenen Hebel.
- **Eine gerechnete Zahl aus 06-04 ist von der Messung überholt worden, und beide Enden stehen jetzt da.** Der Chunker gegen den echten Tokenizer ergibt zwei bis drei Chunks je gedeckeltem Dokument statt genau zwei. Kennzahl 4 hält an beiden Enden: 5,8 bis rund 8,6 Prozent des Tantivy-Index, und die interpolierte Scan-Latenz bei 150.000 Chunks liegt mit rund 56 ms p95 warm und rund 186 ms p95 kalt weiter unter dem Abbruchkriterium von 300 ms je Runde.

## Task Commits

1. **Task 1 (RED): Das Gatter über den Embedding-Einstellungen** - `3d008a3` (test)
2. **Task 1 (GREEN): Die Embedding-Caps als geprüfte Einstellungen mit Herkunft** - `562ff97` (feat)
3. **Task 2 (RED): Das Gatter über dem Chunker** - `f642075` (test)
4. **Task 2 (GREEN): Der Chunker, in Zeichen gerechnet und auf die erste Seite gedeckelt** - `290e30a` (feat)
5. **Task 3 (RED): Das Gatter über dem Modell-Wrapper** - `db10dc5` (test)
6. **Task 3 (GREEN): Der Modell-Wrapper mit Präfixen, Caps und einem ehrlichen Verdikt** - `c46f271` (feat)
7. **Die Korrektur an der Kennzahl von 06-04** - `23e9fcb` (docs)

## Files Created/Modified

- `backend/src/findling/config.py` - ein eigener EMBED-Block mit neun Konstanten und fünf Bereichstupeln, die sieben Settings-Felder, ein eigener Leser für die Überlappung (weil dort die Null eine Antwort ist), `_embed_model_dir` ohne Existenzprüfung, zwei gekoppelte Prüfungen in `settings()`, und der korrigierte Kommentar an `INDEX_WORKERS`
- `backend/tests/test_config.py` - 19 neue Fälle, ein Test je Wert plus die zwei Kopplungen und der Leckprüfer
- `backend/src/findling/embed/chunker.py` - `ChunkSpan`, `chunk_spans` und `make_splitter`; der Deckel kommt aus der Offset-Tabelle der Kodierung, der Modulkopf grenzt Zeichen gegen Bytes ab und nennt die Fundstelle in `index/search.py`
- `backend/tests/test_chunker.py` - 16 Fälle über die acht Verhaltensweisen, mit deutschem und französischem Satz, dem Zehnfachen des Deckels und dem Reinheitsbeleg gegen `open`
- `backend/src/findling/embed/model.py` - `EmbeddingModel`, `EmbedOutcome`, `to_int8`, `open_tokenizer`, die zwei Präfixkonstanten und `EMBEDDING_UNAVAILABLE`; der Modulkopf trägt die Cap-Kaskade, das Verdikt-Argument und die A11-Antwort
- `backend/tests/test_embed_model.py` - 17 Fälle, davon zwei am echten Modell (im Abbild gelaufen, lokal übersprungen); die Attrappe ersetzt genau die zwei Funktionen, die die Platte anfassen
- `backend/src/findling/store/vectors.sql` - datierter Zusatz an der Grössenrechnung: zwei bis drei Chunks je Dokument, die Zahlen darunter sind ein Boden
- `docs/embeddings.md` - der Nachtrag mit beiden Enden der Kennzahl und der Scan-Latenz dazu

## Die gewählten Zahlen und woher sie kommen

| Einstellung | Wert | Herkunft |
|---|---|---|
| `EMBED_ENABLED` | True | D-01/D-15, Muster `OCR_ENABLED` |
| `EMBED_TOKEN_CAP` | 1.024 (Bereich 1 bis 8.192) | D-01; die Obergrenze deckt ein durchschnittliches Dokument (6.691 bis 8.215 Token) vollständig ab und liegt beim Tagesmass aus D-04 |
| `EMBED_CONTEXT_TOKENS` | 512 | Modelleigenschaft, kein Regler |
| `EMBED_SPECIAL_TOKENS` | 2 | **gemessen 05.09.2026** am ausgelieferten Tokenizer |
| `EMBED_CHUNK_TOKENS` | 510 (Bereich 16 bis 510) | Fenster minus Sondertoken |
| `EMBED_CHUNK_OVERLAP` | 0 (Bereich 0 bis 256) | jeder überlappende Token ist ein Token, der unter dem Deckel nicht eingebettet wird |
| `EMBED_BATCH_SIZE` | 2 (Bereich 1 bis 32) | Hebel 4; Messung B: auf aarch64 kostet Charge 2 gegenüber Charge 8 nichts Messbares |
| `EMBED_SEQUENCE_LEN` | 512 (Bereich 16 bis 512) | Hebel 5, an die Chunkgrösse gekoppelt |
| `EMBED_MODEL_DIR` | `/usr/local/share/findling/model` | Abbildkonstante aus `backend/Dockerfile` |

## Der Lauf gegen das echte Modell

Gelaufen am 05.09.2026 im Abbild `findling-sem-probe:local` (das Artefakt aus Plan 06-01/06-03), ohne Netzwerk, mit dem Quellbaum als schreibgeschützter Einhängung:

```bash
MSYS_NO_PATHCONV=1 docker run --rm --network none \
  --entrypoint /app/.venv/bin/python \
  -v "C:/Users/Student/nextcloud-search:/work:ro" \
  -v "<scratch>/prefix_check.py:/tmp/prefix_check.py:ro" \
  -e PYTHONPATH=/work/backend/src \
  findling-sem-probe:local /tmp/prefix_check.py
```

| Beleg | Ergebnis |
|---|---|
| Rangunterschied mit gegen ohne Präfixe | **9 von 10** deutschen Fällen, darunter ein gewechselter bester Treffer |
| Vektorbreite | 384, `to_int8` liefert 384 Byte |
| Norm eines Vektors | 1,000000 |
| Laden vor dem ersten Aufruf | `False` |
| Dokument mit 18.240 Token, gedeckelt auf 1.024 | 3 Chunks mit 500, 507 und 17 Token |
| Breitester Chunk mit Sondertoken | 509 gegen ein Fenster von 512 |
| `text[char_start:char_end]` trifft den Chunk | ja, über alle Chunks |
| Fehlendes Modellverzeichnis im selben Prozess | `embedding_unavailable`, keine Ausnahme |

Das Skript liegt bewusst nicht im Repositorium: es ist die Handfassung der zwei
Testfälle, die `tests/test_embed_model.py` unter `needs_model` führt, und die
laufen im Abbild von selbst, sobald dort ein Testlauf stattfindet.

## Decisions Made

- **510 statt 512, und das ist keine Kosmetik.** Der Tokenizer setzt eine öffnende und eine schliessende Marke um jeden Text. Ein Chunk mit 512 eigenen Token käme als 514 an der Sitzung an, würde auf 512 gekappt und verlöre seine letzten beiden Token, still und ausschliesslich in den Dokumenten, deren Chunks das Fenster wirklich füllen. Gemessen liegen die Chunks bei 500 und 507 Token, also nah genug an der Grenze, dass der Fall eintritt.
- **510 statt 256, gegen die Empfehlung der eigenen Messung.** Messung B weist Charge 2 bei Sequenz 256 als sparsamste und zugleich schnellste Kombination aus, und 256 hätte den Erstindex um rund eine Stunde verkürzt. Es hätte aber auch die Chunkzahl verdoppelt (100.136 auf 200.272), die Vektordatei verdoppelt, den Scan verdoppelt, den jede Nutzersuche bis zu dreimal bezahlt, und die 250.000er-Schwelle aus `research/STACK.md` von 125.000 auf 62.500 Dokumente gezogen, also knapp über den Bestand, den dieses Projekt bereits gemessen hat. Eine Stunde einmalig gegen Kosten bei jeder Suche für immer ist die falsche Richtung.
- **onnxruntime direkt, fastembed nicht (A11).** Gemessen am Quelltext der gepinnten Fassung: `EXPOSED_SESSION_OPTIONS = ("enable_cpu_mem_arena",)`, also ist von den zwei Optionen aus Hebel 6 eine erreichbar und `arena_extend_strategy` nicht. Ausschlaggebend ist aber die Sequenzlänge: `preprocessor_utils.load_tokenizer` liest sie aus `tokenizer_config.json` und bietet keinen Weg, sie zu setzen. Der Preis des direkten Weges ist die Mittelung über die Aufmerksamkeitsmaske und die Normierung, zusammen zwanzig Zeilen, beide durch einen Test festgenagelt.
- **`enable_cpu_mem_arena=False`.** Die Arena gibt Speicher nicht ans Betriebssystem zurück. Auf der 4-GB-Box läuft die Zweitspur stundenlang und wird dann still, während derselbe Prozess weiter Suchen beantwortet; eine Spitze, die zur Dauerlast wird, steht dann neben der OCR-Spitze von 300 bis 600 MB, und IDX-08 hält die beiden zeitlich auseinander, nicht räumlich.
- **`embedding_unavailable` ist kein neuer `Reason`.** `extract/errors.py` führt das geschlossene Vokabular eines beurteilten Dateizustands, im Gleichschritt mit `store/repo.py::STATE_REASONS` und mit der Beschriftungstabelle der PHP-Seite (20 Grundcodes seit Plan 04-08). Eine ausgebliebene Einbettung sagt nichts darüber, ob die Datei indexiert ist: sie ist es, seit dem Volltextlauf Stunden vorher (D-15). Das Verdikt lebt deshalb im Vokabular seines eigenen Moduls, wie es Plan 06-06 und 06-07 brauchen werden.
- **Drei Ladezustände statt zwei.** "Nie versucht", "versucht und gescheitert", "geladen". Ohne den mittleren würde ein Container ohne Modell 50.068 mal nach ihm suchen und 50.068 gleiche Warnungen schreiben, und ein Log mit 50.068 gleichen Warnungen ist ein Log ohne Warnungen. Ein Test zählt die Zeilen.
- **`to_int8` gehört ins Modellmodul.** e5 liefert normierte Vektoren, also ist die Skala eine Eigenschaft des Modells und nicht des Speichers, und 127 ist der ganze Faktor. Geklemmt statt vertraut: eine Komponente von genau 1,0 rundete sonst auf 128 und liefe in einem vorzeichenbehafteten Byte auf -128 über.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktion] Die zwei Sondertoken des Tokenizers**

- **Found during:** Task 3, beim ersten Lauf gegen das echte Modell
- **Issue:** Der Plan verlangt "EMBED_CHUNK_TOKENS ist nie grösser als das Kontextfenster des Modells (512 Token)". Genau 512 ist aber schon zu viel: `encode` setzt eine öffnende und eine schliessende Marke, gemessen am ausgelieferten Tokenizer sind das zwei Ids, also käme ein voller Chunk als 514 Token an der Sitzung an. Die Trunkierung dort kappt auf 512, und die letzten beiden Token des Chunks verschwinden, ohne dass irgendetwas fehlschlägt. Das ist wörtlich die stille Kürzung, gegen die dieser Plan geschrieben ist, nur zwei Token statt vieler.
- **Fix:** Eine eigene Konstante `EMBED_SPECIAL_TOKENS = 2` mit ihrer Messung, `EMBED_CHUNK_TOKENS = EMBED_CONTEXT_TOKENS - EMBED_SPECIAL_TOKENS`, der Bereich entsprechend, und die Kopplungsprüfung klemmt gegen `sequence_len - EMBED_SPECIAL_TOKENS` statt gegen `sequence_len`.
- **Files modified:** backend/src/findling/config.py, backend/tests/test_config.py
- **Verification:** Die Werte 512 und 511 stehen jetzt im Rückfall-Testfall, weil sie aussehen wie das Fenster und schon eins beziehungsweise zwei Token zu viel sind. Im Abbild gemessen: der breiteste Chunk eines gedeckelten Dokuments trägt mit Sondertoken 509 von 512.
- **Committed in:** `c46f271`

**2. [Rule 1 - Fehler] Eine geteilte Tokenizer-Instanz hätte den Deckel aus D-01 halbiert**

- **Issue:** `Tokenizer.enable_truncation` ist eine Eigenschaft des Objekts, nicht des Aufrufs. Der Modell-Wrapper muss auf die Sequenzlänge trunkieren, der Chunker braucht denselben Tokenizer, um den 1.024-Token-Deckel zu finden. Eine gemeinsame Instanz hätte `chunker._first_tokens` nach 512 Token enden lassen, und der Deckel aus D-01 wäre still 512 statt 1.024 gewesen: die zweite Hälfte jedes Dokuments hätte aufgehört zu existieren, mit einer Chunkzahl, die genauso plausibel aussieht.
- **Fix:** Zwei Instanzen aus derselben Datei. `open_tokenizer` liefert die blanke für den Chunker, `_open_encoder` die trunkierende und auffüllende für die Sitzung. Der Grund steht als Absatz an `open_tokenizer` und nicht als Nebensatz.
- **Files modified:** backend/src/findling/embed/model.py
- **Verification:** Im Abbild gemessen: ein Dokument von 18.240 Token ergibt unter dem Deckel 1.024 drei Chunks mit 500, 507 und 17 Token, in Summe 1.024. Mit geteilter Instanz wären es zwei mit zusammen 512 gewesen.
- **Committed in:** `c46f271`

**3. [Rule 1 - Fehler] Die Zeile "zwei Chunks je Dokument" aus 06-04 ist gerechnet und nicht wahr**

- **Found during:** Task 3, im Lauf gegen das echte Modell
- **Issue:** `docs/embeddings.md` und `store/vectors.sql` führen "2 Chunks je Dokument" als gerechnete Zeile, und die gemessene Kennzahl von Erfolgskriterium 4 (100.136 Chunks, 876,0 Byte je Dokument, 5,8 Prozent) steht darauf. Gemessen sind es zwei bis drei: der Splitter schneidet an Satzgrenzen, und was nach dem letzten vollen Chunk übrig bleibt, wird ein eigener kleiner Chunk.
- **Fix:** Ein datierter Nachtrag in `docs/embeddings.md` mit beiden Enden (100.136 gegen 150.204 Chunks, 43,9 gegen rund 65,8 MB, 5,8 gegen rund 8,6 Prozent) und der interpolierten Scan-Latenz bei 150.000 Chunks, dazu ein Zusatz im Schemakommentar von `vectors.sql`. Die gemessene Grösse je Chunk (438,0 Byte) bleibt unverändert, weil sie je Chunk gilt und gegen das ausgelieferte Schema gemessen wurde.
- **Files modified:** docs/embeddings.md, backend/src/findling/store/vectors.sql
- **Verification:** Kennzahl 4 hält am oberen Ende: rund 8,6 Prozent Zuwachs, und rund 56 ms p95 warm beziehungsweise rund 186 ms p95 kalt gegen 300 ms je Runde.
- **Committed in:** `23e9fcb`

### Abweichungen, die keine Autoreparatur sind, sondern eine Auslegung des Plans

**4. Der Kommentar an `INDEX_WORKERS` bekommt keine gemessene Speicherzahl, weil es keine gibt**

Task 1 verlangt: "die geschätzten 250 bis 400 MB weichen der gemessenen Zahl aus
dem Welle-0-Bericht, mit Fundstelle und Datum". Diese Zahl steht dort nicht. Der
Bericht sagt zweimal ausdrücklich das Gegenteil: "Die RAM-Spitze beim Einbetten.
A5 bleibt eine Schätzung. Messung B misst Zeit, nicht Speicher; die Spitze
gehört an den Lasttest der Zweitspur." Eine Schätzung durch eine andere
Schätzung zu ersetzen und "gemessen" darüber zu schreiben, wäre genau die Sorte
Zahl, gegen die diese Phase antritt.

Der Kommentar teilt die Aussage deshalb auf, mit Fundstelle und Datum für beide
Hälften: die **Modellgewichte sind gemessen** (118.101.091 Byte, Plan 06-01,
05.09.2026) und sind eine Dauerlast ab dem ersten Aufruf, nicht eine Spitze; die
**Aktivierungsspitze ist ausdrücklich ungemessen** (A5, Welle-0-Bericht,
05.09.2026) und gehört an Plan 06-11. Was stattdessen durch Messung entschieden
ist, ist die Gestalt, in der die Spitze entsteht, nämlich `EMBED_BATCH_SIZE`.

**5. `to_int8` steht nicht im Plan**

Der Plan verlangt Vektoren der Dimension 384 und sagt nichts über die zweite
Quantisierungsstufe. `store/vectors.py::Chunk` erwartet aber 384 Byte int8, also
muss die Umrechnung irgendwo liegen, und ohne sie hätten Plan 06-06 und 06-07 die
Skala je für sich erfinden müssen: zwei Stellen, die sich am Tag ihrer
Entstehung einig sind. Sie steht im Modellmodul, weil e5 normierte Vektoren
liefert und 127 damit eine Eigenschaft des Modells ist. Zehn Zeilen, ein Test,
im Abbild gegengeprüft.

**6. `chunk_spans` nimmt Tokenizer und Splitter als Argumente**

Der Plan nennt `chunk_spans(text, ...)`. Gebaut ist
`chunk_spans(text, *, tokenizer, splitter, token_cap)` plus ein eigenes
`make_splitter`. Der Grund ist eine Kostenrechnung: `from_huggingface_tokenizer`
reicht den ganzen Tokenizer über die Sprachgrenze, und die ausgelieferte
`tokenizer.json` wiegt 17.082.730 Byte. Einmal je Dokument gebaut wäre das eine
einmalige Last, die 50.068 mal bezahlt wird. Die Eigenschaft, um die es dem Plan
geht, bleibt erfüllt und ist sogar strenger: die Funktion öffnet jetzt gar
nichts, nicht einmal den Tokenizer, und ein Test belegt das gegen `open`.

**7. Der Präfixtest läuft nicht in `pytest`, sondern als dessen Handfassung**

Die zwei Fälle unter `needs_model` werden lokal übersprungen, weil auf dieser
Maschine kein Modell liegt, und das Laufzeitabbild trägt kein `pytest`
(`uv sync --no-dev`). Statt eine Testabhängigkeit ins Abbild zu ziehen, ist
dasselbe Verfahren als Skript im Abbild gelaufen, mit dem Quellbaum als
schreibgeschützter Einhängung; die Ausgabe steht oben. Die Testfälle selbst
bleiben im Repositorium und laufen von selbst, sobald ein Testlauf in einem
Abbild mit Modell stattfindet.

---

**Total deviations:** 3 autorepariert (2 Fehler, 1 fehlende kritische Funktion), 4 Auslegungen
**Impact on plan:** Keine Ausweitung des Umfangs. Alle drei Autoreparaturen betreffen genau die Eigenschaft, die dieser Plan zusichern soll: dass kein Text still verschwindet.

## Issues Encountered

- **`onnxruntime` schreibt weiterhin eine Telemetriezeile nach stderr**, auch mit abgeklemmtem Netzwerk (`--network none`): "Failed to persist telemetry device ID; using an in-memory identifier". Es ist ein fehlgeschlagener lokaler Schreibversuch und kein Netzwerkverkehr, derselbe Befund wie in Plan 06-03, und er gehört unverändert an Plan 06-10 (Offline-Test).
- **`fastembed` ist jetzt eine direkte Abhängigkeit, die der Suchpfad nicht mehr ruft.** Sie bleibt im Manifest: sie liefert `tokenizers`, das dieser Plan und `embed/bench.py` direkt importieren, und ein Ausbau berührte `pyproject.toml`, `uv.lock`, `backend/Dockerfile`, die Prüftabelle der Recherche und `THIRD-PARTY.md`. Das ist kein Befund dieses Plans, sondern eine Aufräumfrage für Plan 06-06, wenn feststeht, dass auch die Leseseite ohne sie auskommt.
- **Die AWS-Box ist nicht angefasst worden.** Der Lauf gegen das echte Modell fand in einem lokalen amd64-Abbild statt; über Geschwindigkeit sagt er nichts, über Rangfolge, Breite und Verdikt alles, und alle drei sind plattformunabhängig.

## Offene Verifikation

Keine. Alle Gates sind lokal grün gelaufen: `pytest` mit 1.172 bestandenen und 13
übersprungenen Tests, `ruff check .`, `ruff format --check .`, `pyright` mit 0
Fehlern und `vulture` ohne Befund, jeweils im CI-Umfang `backend`. Die zwei
übersprungenen Fälle dieses Plans (`needs_model`) sind im Abbild von Hand
gefahren worden, die Ausgabe steht oben. Die neun vorbestehenden
Markdown-Formatbefunde oberhalb von `backend` (DI-06-01) sind unverändert und
nicht Gegenstand dieses Plans.

**Ungemessen und benannt:** die Aktivierungsspitze beim Einbetten (A5). Sie war
vor diesem Plan eine Schätzung und ist es danach, und der Kommentar an
`INDEX_WORKERS` sagt das jetzt ausdrücklich statt eine Bandbreite als Messung zu
führen. Sie gehört an den Lasttest der Zweitspur.

## User Setup Required

None. Alle Werte haben eine Vorgabe, keiner muss gesetzt werden, und ein
Container ohne Modell startet, sucht lexikalisch und schreibt genau eine
Warnzeile.

## Next Phase Readiness

- **Plan 06-06 kann den Durchstich bauen.** `EmbeddingModel.embed_query` liefert den Anfragevektor mit `query: `, `to_int8` bringt ihn in die Form, die `vectors.nearest` erwartet, und `EmbedOutcome.available` ist genau die Bedingung, die der eigene `try/except` aus D-19 braucht: ist sie falsch, bleibt die Vektorliste leer und RRF wird zur Identität. Die offene Frage von 06-04 zur Distanzmetrik ist beantwortet, soweit dieser Plan sie beantworten kann: die Vektoren sind normiert (im Abbild gemessen, Norm 1,000000), also ordnen L2 und Kosinus gleich.
- **Plan 06-07 hat den ganzen Weg von `body_de` zum Chunk.** `open_tokenizer` plus `make_splitter` einmal je Lauf, `chunk_spans` je Dokument, `embed_passages` je Chunkgruppe, `to_int8` je Vektor, `vectors.replace_chunks` je Datei. Zu entscheiden bleibt dort, welche Dateien in die Spur gehören, und genau das entscheidet dieser Plan ausdrücklich nicht.
- **Plan 06-08 sollte wissen, dass die Chunkzahl je Dokument zwei bis drei ist.** Die zweite Deckungsgrad-Zahl zählt Dateien und nicht Chunks, aber jede Hochrechnung auf Platz oder Dauer, die von genau zwei ausgeht, liegt um bis zu die Hälfte daneben.
- **Plan 06-11 erbt eine benannte Lücke.** A5 ist die letzte ungemessene Grösse dieser Phase, und `EMBED_BATCH_SIZE` ist der Hebel, unter dem sie gemessen werden muss.
- **Kein Blocker.**

## Self-Check: PASSED

Alle vier angelegten Dateien liegen auf der Platte
(`backend/src/findling/embed/chunker.py`, `backend/src/findling/embed/model.py`,
`backend/tests/test_chunker.py`, `backend/tests/test_embed_model.py`), alle
sieben Commits (`3d008a3`, `562ff97`, `f642075`, `290e30a`, `db10dc5`,
`c46f271`, `23e9fcb`) stehen in `git log`. Zusätzlich geprüft: `grep -c 'byte'`
in `chunker.py` ist 3, `grep -c 'sqlite3\|onnxruntime'` dort ist 0,
`grep -c 'QUERY_PREFIX\|PASSAGE_PREFIX'` in `model.py` ist 4,
`grep -c 'EMBED_TOKEN_CAP'` in `config.py` ist 3, und weder Geviert- noch
Halbgeviertstrich stehen in einer der acht Dateien.

---
*Phase: 06-semantische-suche*
*Completed: 2026-09-05*
