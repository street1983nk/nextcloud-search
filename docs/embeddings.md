# Einbettungen: Abdeckung, Modell, Schema und der Platz, den sie kosten

Diese Seite hält fest, was die semantische Suche abdeckt, mit welchem Modell und
in welchem Schema sie das tut, was dieses Schema an Platz kostet und welche zwei
Auswege es gibt, falls sqlite-vec eines Tages nicht mehr trägt.

Sie steht zu den Zahlen des Vektorzweigs so, wie `docs/ocr.md` zu den
OCR-Deckeln steht: jede Zahl mit ihrer Herkunft, mit Datum und, wo sie
nachgemessen werden kann, mit der Kommandozeile. Wo eine Messung eine
Startannahme ersetzt, stehen beide da.

**Wo die Konstanten leben.** Die Breite eines Vektors und sein Elementtyp stehen
in `backend/src/findling/store/vectors.py`, das Schema selbst in
`backend/src/findling/store/vectors.sql`. Der Tokendeckel und der Modellname
stehen bis Plan 06-06 als Konstanten in `backend/src/findling/api/resources.py`,
genau dort, wo aus ihnen die Marke `embedding_version` gebildet wird; mit 06-06
wandert der Deckel als Einstellung nach `config.py`, und die Marke wird dann aus
der Einstellung gebildet statt aus dem Literal. Diese Seite erfindet keine Zahl,
die nicht an einer dieser Stellen steht.

## 1. Was die semantische Suche abdeckt und was nicht

Eingebettet werden die **ersten 1.024 Token je Dokument**, also rund eine Seite
Text (D-01). Der Rest des Dokuments bekommt keinen Vektor.

Der ehrliche Satz dazu, und er gehört genau so in den Store-Text (D-17b):

> Die semantische Suche deckt den Anfang jedes Dokuments ab, die Volltextsuche
> weiterhin alles.

Was "der Anfang" in Zahlen heisst:

| Grösse | Wert | Herkunft |
|---|---|---|
| Textzeichen je Dokument | 27.067 | **gemessen**, Volllauf 04.09.2026, `docs/performance.md` |
| Zeichen je Token, deutsche Prosa | 3,2972 | **gemessen**, Welle 0, aarch64 |
| Token je Dokument im Mittel | 8.209 | gerechnet aus den beiden Zeilen darüber |
| Anteil, den 1.024 Token abdecken | **12,5 Prozent** | gerechnet; geschätzt waren 13,2 |

Der Deckel ist eine Einstellung und nach oben aufdrehbar. Ein Betreiber mit Zeit
und Hardware kann auf volle Chunkung gehen; auf der Admin-Seite wird das nicht
beworben, weil die Kosten dafür (Erstindexdauer und Platz, siehe Abschnitt 4)
nichts sind, was man nebenbei anklickt.

Der Anteil gehört als Anteil in jeden Text und nie als Tokenzahl. "1.024 Token"
sagt niemandem etwas, "der Anfang jedes Dokuments, gemessen 12,5 Prozent eines
durchschnittlichen Dokuments dieses Korpus" schon.

## 2. Das Modell

`intfloat/multilingual-e5-small`, MIT-Lizenz, 384 Dimensionen, im Abbild als
selbst quantisierte int8-Datei (118.101.091 Byte, **gemessen** in Plan 06-01).
Die vom Modellrepositorium mitgelieferte int8-Datei wird ausdrücklich **nicht**
verwendet: sie ist AVX512-VNNI-spezifisch und auf ARM unbrauchbar.

Die Qualität ist dreisprachig gemessen und nicht behauptet. Vollständiger
Bericht: [`docs/measurements/2026-09-05-modellqualitaet/README.md`](measurements/2026-09-05-modellqualitaet/README.md).
Die ausgelieferte Kombination ist int8-Modell mit int8-Vektoren, MRR relativ zur
fp32-Fassung:

| Sprache | Fälle | MRR ausgeliefert | gegenüber fp32/fp32 |
|---|---|---|---|
| Deutsch | 42 | 0,6419 | +0,33 Prozent |
| Englisch | 42 | 0,4880 | +5,01 Prozent |
| Französisch | 120 | 0,2767 | -3,59 Prozent |

Die absoluten Werte sind eine Untergrenze und nicht mit NDCG@10 auf MIRACL
vergleichbar: das Testset verbietet lexikalische Brücken ausdrücklich, während im
Betrieb die Tantivy-Liste danebensteht und genau diese Fälle gewinnt.

Die französische Zeile hat die 5-Prozent-Abbruchregel von Plan 06-03 zur
Owner-Entscheidung gemacht. Der Entscheid vom 05.09.2026: die Regel misst die
ausgelieferte Kombination, und die liegt mit -3,59 Prozent unter der Grenze.
D-02 gilt damit als bestanden, die Grenze selbst steht unverändert. Die isolierte
Modellfassung bei fp32-Vektoren bleibt mit -6,87 Prozent gemessen und steht im
Bericht.

Die E5-Präfixe `"query: "` und `"passage: "` werden gesetzt. fastembed setzt sie
bei einem selbst registrierten Modell nicht von allein, und dass sie wirken, ist
gemessen: mit und ohne Präfix bekommen 21 von 42 deutschen, 29 von 42 englischen
und 104 von 120 französischen Fällen einen anderen Rang (D-05).

Die Vektorquantisierung, also die zweite Stufe (int8 in vec0 statt fp32), kostet
auf diesem Testset nichts Messbares: keiner der sechs Vergleiche erreicht den
doppelten Standardfehler, die Vorzeichen wechseln zwischen den Sprachen.

## 3. Das Schema

Zwei Tabellen, beide in `backend/src/findling/store/vectors.sql`:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vectors USING vec0(embedding int8[384]);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id   INTEGER PRIMARY KEY,          -- equals the rowid in chunk_vectors
    file_id    INTEGER NOT NULL,
    ordinal    INTEGER NOT NULL,
    char_start INTEGER NOT NULL,             -- characters, not bytes
    char_end   INTEGER NOT NULL              -- characters, not bytes
);

CREATE INDEX IF NOT EXISTS chunks_file ON chunks (file_id);
```

**Warum `char_start` und `char_end`.** Ein rein semantischer Treffer hat per
Definition keine wörtliche Übereinstimmung mit der Anfrage. Der
SnippetGenerator liefert für ihn also ein leeres Fragment, und ohne die zwei
Zahlen sähe der Nutzer einen Treffer ohne jede Textvorschau. Bei semantischen
Treffern ist das der Normalfall und nicht die Ausnahme. Mit ihnen wird der
Ausschnitt aus dem gespeicherten `body_de` geschnitten, und zwar ausschliesslich
in `snippets_for()`, also nach dem Vorfilter und nach dem PHP-Recheck (D-13).

Es sind **Zeichen** und keine Bytes. Die Verwechslung ist in diesem Projekt schon
einmal gemessen worden (`index/search.py`: die Engine meldet (35, 51), wo der
Zeichenbereich (35, 50) ist), und ein Offset in der falschen Einheit schneidet
jedes semantische Snippet an der falschen Stelle, still und nur in Dokumenten mit
Nicht-ASCII-Text, was auf Deutsch alle sind.

**Warum kein Fremdschlüssel auf `files`.** Weil er nicht durchsetzbar wäre: die
Vektoren liegen in einer anderen Datenbankdatei. Die Löschwege sind deshalb
ausdrückliche Aufrufe (`replace_chunks`, `drop_vectors`, `forget_all`), und ihre
Verdrahtung in den Löschweg des Containers ist Plan 06-07.

**Warum eine eigene Datei `vectors.db`** neben `state.db`, statt zweier Tabellen
darin. Drei Gründe, alle im Bestand belegt:

1. Sie ist verwerfbar, ohne einen einzigen Volltextbefund zu verlieren. "Bau die
   semantische Hälfte neu" ist damit ein `rm` und keine Migration.
2. Sie hält die Ladefähigkeit für Erweiterungen von `state.db` fern. Nur die
   Vektorverbindung muss vor ihrer ersten Frage eine Bibliothek mit
   Maschinencode laden; `state.db` hat dazu keinen Anlass, und `repo.py::_connect`
   ist deshalb unverändert geblieben, obwohl die Recherche das Gegenteil erwartet
   hatte.
3. `vectors.py` nimmt ihren Pfad als Argument, wie `repo.py` es tut. Die
   Entscheidung bleibt damit ohne Umbau kippbar.

**Die Schemafassung.** `SCHEMA_VERSION` in `repo.py` steht auf `"2"`. Der Sprung
ist rein additiv: zwei Tabellen in einer eigenen Datei und ein weiterer
Schlüssel in `meta`, dessen Namensraum genau dafür offengehalten wurde. Ein
Reindex des Volltextbestands ist **nicht** nötig, und diese Eigenschaft wird
bewusst erhalten (D-21). Damit sie erhalten bleibt, trägt die Fassung von
`schema.sql` seit Phase 6 eine eigene Marke `store_schema_version`: der
Schlüssel `schema_version` gehört der Tantivy-Schemafassung, und ein Sprung
unter diesem Schlüssel hätte genau den stundenlangen Neuaufbau erzwungen, den
D-21 ausschliesst.

**Die Marke `embedding_version`** sagt, welcher Vektorbestand neben dem
Zustand liegt: Modell, Quantisierung, Dimensionszahl und Tokendeckel, zum
Beispiel `multilingual-e5-small/int8/384/1024`. Ändert sich eine der vier
Grössen, passt ein gespeicherter Vektor nicht mehr zu einem frisch gerechneten
Anfragevektor. Ihr Drift wird gemeldet und löst **keinen** Volltext-Reindex aus;
die Folge gehört in den Vektorweg.

## 4. Die Kennzahl: Byte je Dokument (Erfolgskriterium 4)

### Der Rechenweg

| Zeile | Wert | gemessen oder gerechnet | Fundstelle |
|---|---|---|---|
| Byte je Vektor | 384 | gerechnet: 384 Dimensionen mal 1 Byte (int8) | `vectors.sql` |
| Chunks je Dokument beim Deckel aus D-01 | 2 | gerechnet: 1.024 Token bei 512 Token je Chunk | Welle-0-Bericht, Ableitung 1 |
| Dokumente im Messkorpus | 50.068 | **gemessen**, Volllauf 04.09.2026 | `docs/performance.md` |
| Chunks insgesamt | 100.136 | gerechnet aus den zwei Zeilen darüber | Welle-0-Bericht, Ableitung 1 |
| Dateigrösse `vectors.db` bei dieser Chunkzahl | **43.859.968 Byte** | **gemessen**, 05.09.2026 | Kommandozeile unten |
| **Byte je Chunk** | **438,0** | gerechnet aus der gemessenen Dateigrösse | |
| **Byte je Dokument** | **876,0** | gerechnet aus der gemessenen Dateigrösse | |
| Verwaltungsanteil je Chunk | 54,0 Byte | gerechnet: 438,0 minus 384 | |
| Tantivy-Index desselben Korpus | 761.374.910 Byte | **gemessen**, Volllauf 04.09.2026 | `docs/performance.md` |
| **Zuwachs gegenüber dem heutigen Index** | **5,8 Prozent** | gerechnet | |

### Nachtrag vom 05.09.2026: die Zeile "Chunks je Dokument" ist ein Boden

Die zweite Zeile der Tabelle war gerechnet, nicht gemessen: 1.024 Token geteilt
durch 512 Token je Chunk ergibt zwei. Plan 06-05 hat den Chunker gegen den
ausgelieferten Tokenizer laufen lassen, und dabei sind es **zwei bis drei**
geworden. Der Grund ist die Arbeitsweise des Splitters: er schneidet an
Satzgrenzen, und was nach dem letzten vollen Chunk uebrig bleibt, wird ein
eigener kleiner Chunk. Gemessen an einem Dokument von 18.240 Token, gedeckelt
auf 1.024: drei Chunks mit 500, 507 und 17 Token.

Zwei Zahlen der Tabelle sind damit Untergrenzen und keine Punktwerte:

| Groesse | bei 2 Chunks je Dokument | bei 3 Chunks je Dokument |
|---|---|---|
| Chunks insgesamt | 100.136 | 150.204 |
| `vectors.db` | 43.859.968 Byte | rund 65.789.352 Byte |
| Byte je Dokument | 876,0 | rund 1.314,0 |
| Zuwachs gegenueber dem Tantivy-Index | 5,8 Prozent | rund 8,6 Prozent |

Die gemessene Groesse je Chunk (438,0 Byte) aendert sich dadurch nicht; sie ist
gegen das ausgelieferte Schema gemessen und gilt je Chunk. Was sich aendert, ist
die Zahl der Chunks, und das Abnahmekriterium 4 haelt auch am oberen Ende: bei
150.000 Chunks liegt die Scan-Latenz auf nativem aarch64 interpoliert bei rund
56 ms p95 warm und rund 186 ms p95 kalt, gegen ein Abbruchkriterium von 300 ms
je Runde (Welle-0-Bericht, Messung C).

Die Chunkgroesse steht seit Plan 06-05 ausserdem auf **510** und nicht auf 512:
der Tokenizer setzt zwei Sondertoken um jeden Text, gemessen am ausgelieferten
Artefakt, und ein Chunk mit 512 eigenen Token kaeme als 514 an der Sitzung an
und verloere seine letzten beiden, ohne dass irgendetwas fehlschlaegt.

Die Schätzung aus der Phasenrecherche (06-RESEARCH.md 4.3) lag bei 432 Byte je
Chunk, 864 Byte je Dokument, 48 Byte Verwaltung und 5,7 Prozent. Sie war also um
1,4 Prozent zu niedrig, im Wesentlichen weil der Verwaltungsanteil je Chunk mit
54,0 statt 48 Byte etwas höher ausfällt. Das ist der seltene Fall einer
Schätzung, die die Messung fast getroffen hat, und sie wird hier trotzdem durch
die Messung ersetzt, weil eine Zahl, die man nachrechnen kann, keine Schätzung
bleiben muss.

### Die Kommandozeile

Gemessen wurde gegen genau das Schema, das ausgeliefert wird, über die drei
Operationen des Moduls und nicht über handgeschriebenes SQL. Die Verbindung
wird vor der Messung geschlossen, damit der WAL-Anteil in die Datei
zurückgeschrieben ist und die gemessene Grösse die Grösse auf der Platte ist.

```bash
cd backend && uv run python - <<'PY'
import hashlib, tempfile
from pathlib import Path
from findling.store.vectors import EMBEDDING_DIMENSIONS, Chunk, open_vectors

DOCUMENTS, PER_DOCUMENT = 50068, 2

def vector(seed):
    raw, counter = b"", 0
    while len(raw) < EMBEDDING_DIMENSIONS:
        raw += hashlib.sha256(f"{seed}:{counter}".encode()).digest()
        counter += 1
    return raw[:EMBEDDING_DIMENSIONS]

path = Path(tempfile.mkdtemp()) / "vectors.db"
store = open_vectors(path)
for file_id in range(1, DOCUMENTS + 1):
    store.replace_chunks(file_id, [
        Chunk(ordinal=o, char_start=o * 3376, char_end=o * 3376 + 3376,
              embedding=vector(file_id * PER_DOCUMENT + o))
        for o in range(PER_DOCUMENT)
    ])
chunks = store.chunk_count()
store.close()
size = path.stat().st_size
print(f"chunks {chunks}, bytes {size}, per chunk {size / chunks:.1f}, per document {size / DOCUMENTS:.1f}")
PY
```

Ergebnis am 05.09.2026 auf x86_64 (Python 3.13.13, SQLite 3.50.4):

```
chunks 100136, bytes 43859968, per chunk 438.0, per document 876.0
```

Das SQLite-Dateiformat ist plattformunabhängig, die Zahl gilt also auch für die
ARM-Box. Was sie **nicht** sagt, ist etwas über Geschwindigkeit; dafür ist die
scan-latency-Reihe des Welle-0-Berichts da.

### Was auf diesem Platz gelesen werden muss

Der Platz ist in keiner Variante das Problem. Interessant ist, was ein voller
brute-force-Scan davon liest, und das ist die Nutzlast allein: 38,4 MB.
**Gemessen** auf nativem aarch64 bei 100.000 Chunks (Welle 0, Messung C):

| Cachezustand | p95 je Runde | gegen 300 ms | drei Runden | Anteil an 2,5 s |
|---|---|---|---|---|
| warm | 37,8 ms | 13 Prozent | 113,3 ms | 4,5 Prozent |
| kalt | 153,5 ms | 51 Prozent | 460,6 ms | 18,4 Prozent |

Der Maßstab steht im eigenen Code: `php/lib/Search/Provider.php` führt
`BUDGET_NANOSECONDS = 2_500_000_000` und `MAX_ROUNDS = 3`.

Vollständige Reihen, beide Architekturen, warm und kalt, int8 und bit:
[`docs/measurements/2026-09-05-welle0-arm64/README.md`](measurements/2026-09-05-welle0-arm64/README.md).
Die zwei Fünf-Minuten-Proben, auf denen die Verbindungsentscheidungen dieses
Schemas beruhen:
[`docs/measurements/2026-09-05-welle0-proben/README.md`](measurements/2026-09-05-welle0-proben/README.md).

## 5. Die zwei Ausweichpfade

Beide sind **beschrieben und nicht gebaut** (D-10). Sie stehen hier, weil ein
Ausweg, der erst gesucht wird, wenn er gebraucht wird, keiner ist.

Beide Wechsel fänden am selben Ort statt: in
`backend/src/findling/store/vectors.py`, in einer Datei. Genau dafür liegt der
Vektorspeicher hinter einer Schnittstelle mit drei Operationen (D-08).

### Ausweich 1: Bit-Vektoren, weiterhin in sqlite-vec

| Posten | Bewertung |
|---|---|
| Was sich ändert | Spaltentyp `bit[384]` statt `int8[384]`, Hamming-Distanz statt der heutigen Vorgabemetrik, plus eine Binarisierung des Vektors beim Schreiben und beim Fragen |
| Kosten | gering: ein Datentyp, eine Distanzfunktion, kein zweiter Persistenzpfad, kein neues Paket, dieselbe Datenbank, dasselbe Backup |
| Gewinn Platz | Faktor 8: 48 statt 384 Byte je Vektor, also 4,8 statt 38,4 MB Nutzlast bei 100.000 Chunks (**gemessen**) |
| Gewinn Zeit | Faktor 5,3 bis 7,7, **gemessen** statt geschätzt: bei 100.000 Chunks warm p95 4,9 gegen 37,8 ms auf aarch64, bei 1.000.000 Chunks warm 63,7 gegen 338,5 ms auf dem x86-Notebook. Die Schätzung der Recherche (Faktor 8 bis 20) war zu optimistisch |
| Verlust | Qualität. Wie viel, ist für e5-small auf Deutsch **nicht belegt**: dazu **fehlt** eine Messung, und eine plausible Zahl wird hier nicht erfunden |
| Übliche Gegenmassnahme | zweistufig: binär grob vorsortieren, die besten zehn mal k mit den int8-Vektoren nachrechnen. Das setzt voraus, dass beide Fassungen gespeichert werden, kostet also Platz statt ihn zu sparen, und rettet dafür den Grossteil der Qualität |

Eine Anmerkung zur Metrik, die auch für den heutigen Zustand gilt: die
`int8[384]`-Spalte lässt vec0 seine Vorgabemetrik verwenden, gemessene Distanzen
liegen entsprechend im L2-Bereich. Bei normierten Vektoren ist die Rangfolge
unter L2 und unter Kosinus dieselbe.

**Nachtrag vom 05.09.2026 (Plan 06-06), wo der Anfragevektor entsteht.** Die
offene Frage war, ob die int8-Quantisierung die Normierung ausreichend erhält.
Zwei Belege stehen dazu inzwischen da, und beide zusammen sind die Antwort,
soweit dieses Projekt sie geben kann.

Erstens: der Anfragevektor läuft durch dieselbe Skala wie jeder gespeicherte
Vektor. `embed/model.py::to_int8` ist die einzige Stelle, an der ein Vektor
seine Bytefassung bekommt, und die Leseseite ruft sie genauso wie die
Schreibseite. Beide Seiten verlieren damit denselben Betrag an derselben Stelle,
und ein systematischer Versatz zwischen Anfrage und Bestand kann so nicht
entstehen.

Zweitens, und das ist der Messwert: Plan 06-03 hat genau diese zweite
Quantisierungsstufe auf einem dreisprachigen Testset gegen die unquantisierte
Fassung geprüft. Keiner der sechs Vergleiche erreicht den doppelten
Standardfehler. Der Rangverlust durch die Vektorquantisierung ist auf diesem
Testset also nicht messbar, und das ist die Grösse, um die es geht: nicht die
Norm eines einzelnen Vektors, sondern die Reihenfolge, die aus ihr folgt.

Was weiterhin **nicht** gemessen ist: die Norm eines quantisierten Vektors als
Zahl. Sie ist für die Rangfolge unter L2 nur dann von Belang, wenn sie zwischen
Dokumenten unterschiedlich stark abweicht, und dafür gibt es aus 06-03 keinen
Hinweis. Ein eigener Messlauf dafür wäre eine Zahl ohne Entscheidung dahinter.

### Ausweich 2: usearch

| Posten | Bewertung | Beleg |
|---|---|---|
| Fassung | 2.26.2, hochgeladen 31.08.2026 | PyPI-JSON-API, 04.09.2026 |
| Lizenz | Apache-2.0 | PyPI-Metadaten |
| aarch64 und cp313 | ja, `manylinux_2_28_aarch64`-Rad vorhanden | PyPI-Dateiliste |
| Verfahren | HNSW, also approximativ statt exakt | Projektdokumentation |

**Was der Wechsel kostet:**

- Ein **zweiter Persistenzpfad** neben SQLite. Heute gibt es Betriebszustand in
  Dateien, die SQLite versteht, ein Backup und eine Konsistenzquelle. Danach
  gibt es zwei Sorten, die zueinander passen müssen. Das ist derselbe
  Klassenfehler, gegen den `repo.py` im Kopfkommentar ausdrücklich schreibt.
- **Eigene ID-Verwaltung.** usearch kennt Schlüssel und Vektor; die Zuordnung
  auf `file_id` und Ordinal müsste daneben in SQLite liegen, und beide müssten
  Abbrüche gemeinsam überleben.
- **Crash-Sicherheit selbst zu bauen.** SQLite bringt WAL und
  `synchronous = NORMAL` mit, ein HNSW-Graph im Arbeitsspeicher bringt das
  nicht. Ein `docker kill` mitten im Lauf ist in diesem Projekt ein
  Abnahmekriterium (IDX-02) und keine theoretische Möglichkeit.
- **Grabsteine bei Löschungen.** HNSW-Graphen mögen Löschungen nicht; sie
  hinterlassen Grabsteine, und der Graph muss periodisch neu gebaut werden. Bei
  einer App, deren Kernversprechen "entzogener Share verschwindet zeitnah"
  lautet (IDX-05), ist das ein Entwurfsproblem.

**Was der Wechsel bringt:** logarithmische statt linearer Suchzeit. Bei einer
Million Chunks ist das der Unterschied zwischen 384 MB je Abfrage lesen und ein
paar tausend Vektoren besuchen. Die Schwelle, ab der das zählt, ist gemessen:
bei 250.000 Chunks hält int8 warm mit 93,6 ms p95 bequem, kalt riss dieselbe
Stützstelle auf einer von zwei gemessenen Maschinen mit 372,7 ms das
Abbruchkriterium von 300 ms.

**Die Entschärfung, die ausdrücklich aufzuschreiben ist:** der Vektorindex ist
**nicht** die Sicherheitsgrenze. Der PHP-Recheck ist es. Ein Grabstein zu viel
kostet einen Kandidaten, den der Recheck ohnehin verwirft, und **kein Leck**.
Das gilt heute schon für den SQLite-Vorfilter und würde für usearch genauso
gelten; es ist der Grund, warum ein approximatives Verfahren an dieser Stelle
überhaupt vertretbar wäre.

## 6. Das Wartungsrisiko von sqlite-vec

| Angabe | Wert |
|---|---|
| Letzter Commit im Repositorium | 18.05.2026 |
| Offene Vorgänge | 204 |
| Letzte stabile Fassung | v0.1.9 vom 31.03.2026 |
| Was danach kam | ausschliesslich Alpha-Fassungen der 0.1.10 |
| Wie gepinnt | exakt: `sqlite-vec==0.1.9` in `backend/pyproject.toml`, kein `>=` |
| Wie ausgeliefert | die `.so` liegt im Abbild, je Architektur gegen eine sha256 geprüft (D-09) |

Alle Angaben mit Stand 04.09.2026 aus der Phasenrecherche.

**Warum dieses Projekt das aufschreibt, statt es zu verschweigen.** Findling
existiert, weil `fulltextsearch` jahrelang verwaist war und niemand das dort
stehen hatte. Dieselbe Lage im eigenen Baustein mit einem Absatz zu beantworten,
wäre genau der Fehler, gegen den das Produkt antritt. Die Antwort ist deshalb
keine Absichtserklärung, sondern eine Datei: `store/vectors.py` ist drei
Operationen breit, die zwei Auswege oben sind mit Kosten und Nutzen beziffert,
und der Wechsel wäre eine Datei und kein Umbau.

Was ein Rückzug des Pakets nicht treffen kann: den Bau. Die Bibliothek liegt im
Abbild, nicht auf PyPI.

## 7. Der Betriebsablauf: zwei Spuren nacheinander, nicht nebeneinander

Ein Dokument wird in dieser Reihenfolge behandelt, und die Reihenfolge ist eine
Entscheidung und kein Zufall:

1. **Erste Spur, Volltext und OCR.** Der Crawl übergibt die Datei, der Text wird
   extrahiert, bei einem Scan durch die OCR-Kaskade, das Dokument geht in den
   Tantivy-Index und bekommt sein Verdikt in `files`. Ab diesem Moment ist es
   auffindbar.
2. **Zweite Spur, die Einbettung.** Erst danach reist dieselbe `fileid` als
   `embed`-Zeile auf einer nachlaufenden Spur derselben Warteschlange (Plan
   06-07). Der gespeicherte Text wird in Chunks geschnitten, die Chunks werden
   eingebettet und als int8-Vektoren in `vectors.db` geschrieben.

**Warum nacheinander und nicht zusammen.** Ein Dokument ohne Vektor ist
trotzdem indexiert (D-15), und ein Verdikt der zweiten Spur erreicht
`Store.record` deshalb nie. Die vier Endzustände eines `embed`-Auftrags
(`embedded`, `no_stored_text`, `embedding_incomplete`, `embedding_unavailable`)
sagen nichts darüber, ob die Datei indexiert wurde. Wäre es umgekehrt, hätte ein
fehlendes Modell die Datei aus dem Index gemeldet, und der Volltext wäre am
Ausfall der Semantik gestorben. Das ist genau, was Erfolgskriterium 3 verbietet.

**Was die zweite Spur an Zeit kostet, gemessen.** Der gedeckelte Bestand des
Messkorpus sind 50.068 Dokumente mal 1.024 Token, also 51.269.632 Token. Gegen
die auf nativer aarch64-Hardware gemessenen Durchsätze:

| Kombination | Token/s p50 | Dauer bei p50 | Token/s p95 | Dauer bei p95 |
|---|---|---|---|---|
| Charge 8, Sequenz 512 (ausgeliefert) | 3.519 | 4 h 03 min | 3.437 | 4 h 09 min |
| Charge 8, Sequenz 256 | 4.809 | 2 h 58 min | 4.776 | 2 h 59 min |

Gemessen am 05.09.2026 auf zwei gepinnten Neoverse-N2-Kernen, Messung B des
Welle-0-Berichts. Die Kommandozeile:

```bash
for combo in "2 256" "2 512" "8 256" "8 512"; do
    set -- $combo
    docker run --rm --network none --cpuset-cpus 0,1 \
        --entrypoint python ghcr.io/street1983nk/findling_backend:dev \
        -m findling.embed.bench --mode tokens-per-second \
        --batch "$1" --sequence "$2" --threads 2
done
```

Vollständige Reihen und das D-04-Verdikt, das aus ihnen folgt:
[`docs/measurements/2026-09-05-welle0-arm64/README.md`](measurements/2026-09-05-welle0-arm64/README.md).

**Was diese Dauer nicht ist.** Sie ist keine Zusage über die Zielbox. Zwei
gepinnte Neoverse-N2-Kerne sind schneller als zwei geteilte vCPU einer kleinen
Box, und um wie viel, ist ungemessen. Der Store-Text trägt diese Stunden
deshalb nicht (D-17a); was der Bericht belegt, ist, dass die Größe, an der die
Phase hängen könnte, sie nicht zum Kippen bringt.

**Was ein Admin währenddessen sieht.** Die Admin-Seite führt seit Plan 06-09
zwei Deckungszahlen mit demselben Nenner:

| Zahl | Zähler | Woher |
|---|---|---|
| indexiert | Dokumente mit Verdikt `indexed` | `files` in `state.db` |
| auffindbar nach Bedeutung | Dokumente mit mindestens einem Vektor | `COUNT(DISTINCT file_id)` über `chunks` in `vectors.db` |

Beide entstehen aus einem Aufruf derselben Methode mit einem anderen Zähler und
nie aus zwei Rechenwegen; ein Gate zählt genau das. Während die zweite Spur
läuft, steht die erste Zahl still und nur die zweite bewegt sich, weshalb sie im
Fingerabdruck des Pollings steht und der Block bei jedem Durchgang neu
geschrieben wird.

Die Zahl zählt **Dokumente und nicht Chunks**: ein Dokument trägt unter dem
Deckel zwei bis drei Chunks (gemessen 05.09.2026, Plan 06-05), also stünde eine
Chunkzahl neben einer Dokumentzahl auf derselben Seite und wäre um das Zwei- bis
Dreifache zu gross. Sie fehlt als Wert, wenn der Container sie nicht gemeldet
hat, und ist 0, wenn kein Dokument einen Vektor trägt: "nicht gemeldet" und
"null" sind zwei Auskünfte, und 0 Prozent wäre eine Aussage über die zweite.

**Und der Zustand dazwischen heisst `degraded`.** Ist das Einbetten
eingeschaltet und es gibt keinen Vektorbestand, meldet sich der Container als
unvollständig. Das ist eine Aussage über Vollständigkeit und nicht über einen
Fehler: ein Container, dessen zweite Spur noch nicht gelaufen ist, antwortet
lexikalisch und antwortet richtig, er antwortet nur noch nicht mit allem, was er
verspricht.

**Was davon geprüft wird und wie.** Dass das Abbild ohne Netzwerkzugang einbettet
und sucht, und dass es mit fehlendem Modell Volltexttreffer statt einer leeren
Antwort liefert, sind zwei Schritte in `.github/workflows/docker.yml`, die auf
beiden Architekturen laufen. Was jeder von beiden beweist und was nicht, steht in
[`docs/testing.md`](testing.md).
