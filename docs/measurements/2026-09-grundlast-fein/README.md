# Feinmessung der Grundlast, 08.09.2026

**Nachgezogen am 09.09.2026:** die arm64-Spalten dieses Berichts stammten
zunächst aus einer Messung unter QEMU. Sie stehen jetzt auf der nativen Messung
des ersten `workflow_dispatch` von `measure.yml` auf `main`, Lauf
34325000302, Artefakt `welle0-arm64`, Rohdatei
`rohdaten/01-grundlast-fein-arm64.txt`. Die emulierte Reihe bleibt als
`rohdaten/01-grundlast-fein-arm64-emuliert.txt` lesbar und ist unter jeder
nachgezogenen Tabelle als Vorläufer genannt. Betroffen sind die Abschnitte 1, 2,
3 und 4.

Die Nachmessung vom 07.09.2026
(`docs/measurements/2026-09-nachmessung-m7g/rohdaten/63-grundlast.txt`) hat die
Grundlast des Containers Schritt für Schritt aufgeschrieben und dabei **543,7 MB
von 678 MB in genau zwei Zeilen** gelegt: `11-tokenizer-gelesen` kostet
269,4 MB, `12-chunker-gebaut-und-gefahren` weitere 274,3 MB. Keine der beiden
Zeilen sind die Modellgewichte; die kommen mit Schritt 14 und kosten noch einmal
391,9 MB.

Zwei Zeilen dieser Größe sind ein Besitzer, den niemand benannt hat. Dieser
Bericht benennt ihn, bevor irgendjemand daraus einen Umbau macht. Er wiederholt
die Form der Nachmessung, damit die Zahlen vergleichbar sind statt nur
nebeneinander zu stehen, und er zerlegt die beiden groben Schritte in fünf
einzeln benannte Kandidaten.

---

## 1. Die Umgebung, und was an ihr belastbar ist

| Was | amd64 | arm64 (nativ) |
|---|---|---|
| Abbild | `ghcr.io/street1983nk/findling_backend:dev` | dasselbe, arm64-Hälfte des Manifests |
| Digest | `sha256:8e1f64bd068819dc6447513bc6ee14c78c93d3a03cd5ffdfdf2aba8e95183a6b` | `sha256:eed6a5fcb152373e7bf6d7725da774844d4012cfe0cbe02b261f31a865e4cce3`, arm64-Hälfte `sha256:ae58d93005dc18849c3bd128cef51bea0530c143f5719a284fd694b6f9e09d44` |
| Architektur laut Prozess | `x86_64` | `aarch64` |
| Python im Abbild | 3.13.15 | 3.13.15 |
| `tokenizers` | 0.23.2 | 0.23.2 |
| Vokabular des Tokenizers | 250.002 Einträge | 250.002 Einträge |
| Ausführung | nativ, Docker, `--network none` | nativ auf ARM-Hardware, GitHub-Runner `ubuntu-24.04-arm`, `--network none` |
| Rohdatei | `rohdaten/01-grundlast-fein-amd64.txt` | `rohdaten/01-grundlast-fein-arm64.txt` |

Vorläufer der arm64-Spalte, bis zum 09.09.2026 die einzige, die es gab:
`rohdaten/01-grundlast-fein-arm64-emuliert.txt`, Abbild
`sha256:8d49814ce631cd226da40785b8aaed0384b4ce933965a31b3bcdf236c9fa428b`,
gemessen unter QEMU-Emulation.

**Zwei Bemerkungen zum Digest, weil er die einzige feste Größe an einem
wandernden Zeiger ist.** Erstens: die beiden Digests in der Tabelle sind nicht
dasselbe Ding. Die amd64-Zeile nennt einen Plattform-Digest, wie ihn
`docker image inspect` auf einer lokalen Maschine liefert; die arm64-Zeile nennt
den Digest des **Manifestindex**, weil der Schritt "Resolve the image to a
digest" von `measure.yml` `RepoDigests` nach einem `docker pull` auf den Tag
liest. Die arm64-Hälfte dieses Index steht daneben, damit ein späterer Lauf auf
der Box gegen dieselbe Zeichenkette prüfen kann. Zweitens: dieser Index gehört
zum Bau aus Commit `b6426ed`. Unter `backend/src` und `php/` liegt zwischen
diesem Commit und dem Stand, aus dem die amd64-Datei stammt, keine Änderung; die
beiden Abbilder tragen denselben Quellstand, nur aus zwei Bauläufen.

**Der arm64-Lauf ist nativ, und der Vorläufer war es nicht.** Am 08.09.2026 gab
es für diese Phase keine ARM-Maschine: die AWS-Box war angehalten, ihr
Datenträger ist teilweise zerstört, und sie gehört Phase 10. Gemessen wurde
deshalb unter QEMU, mit dem sichtbaren Preis einer verschobenen Grundlinie
(Schritt 00 lag bei 43,2 MB statt bei den 13,3 MB der amd64-Messung). Am
09.09.2026 hat der erste `workflow_dispatch` von `measure.yml` auf `main`
(Lauf 34325000302, Ast `arm64`, Runner `ubuntu-24.04-arm`) dieselbe Skriptdatei
auf echter ARM-Hardware gefahren. Schritt 00 liegt dort bei **13,0 MB**, also
neben der amd64-Zahl und rund 30 MB unter dem emulierten Wert. Die
**Zuwächse zwischen zwei Schritten** hatte die Emulation nicht nennenswert
verschoben, und das ist mit der nativen Datei jetzt nachgeprüft statt behauptet:

| Posten | arm64 (nativ), Lauf 34325000302 | arm64 nativ (Nachmessung, grob) | Abweichung |
|---|---|---|---|
| Schritt 11 gesamt (11a + 11b) | 269,4 MB | 269,4 MB | 0,0 MB (275.912 kB in beiden Läufen) |
| Schritt 12 gesamt (12a + 12b + 12c) | 274,3 MB | 274,3 MB | -0,008 MB (280.840 gegen 280.848 kB) |
| Beide zusammen | 543,7 MB | 543,7 MB | -0,008 MB |

Vorläufer, emuliert (`rohdaten/01-grundlast-fein-arm64-emuliert.txt`):
Schritt 11 gesamt 252,6 MB, Schritt 12 gesamt 297,5 MB, beide zusammen
550,1 MB, also +6,4 MB gegen die grobe native Messung.

Die Summe liegt jetzt **8 kB** neben der nativen Messung derselben Schritte,
das sind 0,001 Prozent; die emulierte Messung lag mit 1,2 Prozent daneben. Zwei
Kilobyte-Seiten Unterschied über 544 MB auf zwei verschiedenen ARM-Maschinen
(AWS Graviton3 und der Runner) sind so nah, wie zwei Läufe desselben Vorgangs
kommen können. Für die Frage dieses Berichts hätte die emulierte Zahl gereicht;
für eine Erwartung, gegen die der Lauf auf der Box in Phase 10 seine Grundlast
hält, ist die native die richtige.

**Die Kontrolle, die derselbe Lauf mitgeliefert hat.** `measure.yml` fährt beide
Matrixäste, also ist neben der arm64-Datei auch eine zweite amd64-Messung
entstanden, auf einem `ubuntu-24.04`-Runner statt auf Docker Desktop und aus
einem anderen Baulauf desselben Quellstands. Sie liegt als
`rohdaten/01-grundlast-fein-amd64-runner.txt` daneben und **ersetzt die
amd64-Datei nicht**: `01-grundlast-fein-amd64.txt` ist die Datei, auf die der
Entscheid in Abschnitt 4 sich stützt, und die bleibt, wie sie war.

| Posten | amd64 (Docker Desktop) | amd64 (Runner, Lauf 34325000302) | Abweichung |
|---|---:|---:|---:|
| 11a-tokenizers-modul-importiert | 4,25 MB | 3,86 MB | -0,39 MB, -9,2 % |
| 11b-erste-tokenizer-instanz | 265,75 MB | 265,48 MB | -0,27 MB, -0,1 % |
| 12a-splitter-gebaut | 273,51 MB | 273,20 MB | -0,31 MB, -0,1 % |
| 12b-erster-chunkerlauf | 0,75 MB | 0,96 MB | +0,21 MB, +28,1 % |
| 12c-zweiter-chunkerlauf | 0,00 MB | 0,00 MB | 0,00 MB |
| **Summe** | **544,3 MB** | **543,5 MB** | **-0,76 MB, -0,14 %** |

**Ein Befund, und zwar einer über das Maß und nicht über die Sache.** Zwei der
fünf Posten weichen um mehr als 5 Prozent ab, und beide sind Posten, bei denen
ein Prozentsatz nichts mehr aussagt: 11a weicht um 0,39 MB ab und 12b um
0,21 MB. Ein Prozentsatz auf einer Zahl unter einem Megabyte misst die
Speicherverwaltung der C-Bibliothek und nicht den gemessenen Vorgang. Die drei
Posten, um die es geht, weichen um 0,1 Prozent ab, und die Summe um
0,14 Prozent. Außerhalb der fünf Posten ist die größte Abweichung der Kontrolle
-4,38 MB am informativen Schritt 16 (-2,0 %) und -2,32 MB an Schritt 15
(-5,8 %); beide gehören der Einbettung und nicht dem Tokenizer.

**Das Skript sendet nichts.** Es liest `/proc/self/status`, das Modellverzeichnis
und die Wortliste des Abbilds und gibt Zahlen aus. Der Text, mit dem gechunkt
wird, steht im Skript. Alle drei Läufe standen auf `--network none`.

---

## 2. Die Zahlen, Schritt für Schritt

Die Schritte 00 bis 10 und 13 bis 15 sind wortgleich aus
`docs/measurements/2026-09-05-semantiklauf-m7g/skripte/52-woher-die-grundlast.py`
übernommen. Neu sind die fünf Kandidaten dazwischen und der informative
Schritt 16.

| Schritt | amd64 RSS | amd64 Zuwachs | arm64 (nativ) RSS | arm64 (nativ) Zuwachs |
|---|---:|---:|---:|---:|
| 00-leerer-prozess | 13,3 MB | | 13,0 MB | |
| 01-config-importiert | 16,5 MB | 3,2 MB | 16,3 MB | 3,3 MB |
| 02-settings-gelesen | 16,7 MB | 0,1 MB | 16,3 MB | 0,1 MB |
| 03-index-module-importiert | 24,2 MB | 7,5 MB | 23,4 MB | 7,1 MB |
| 04-embed-module-importiert | 26,4 MB | 2,2 MB | 25,5 MB | 2,1 MB |
| 05-store-vectors-importiert | 28,0 MB | 1,6 MB | 27,1 MB | 1,6 MB |
| 06-poller-importiert | 69,7 MB | 41,6 MB | 68,4 MB | 41,3 MB |
| 07-api-resources-importiert | 69,7 MB | 0,0 MB | 68,4 MB | 0,0 MB |
| 08-findling-main-importiert | 71,9 MB | 2,3 MB | 70,7 MB | 2,3 MB |
| 09-wortliste-gelesen-276496 | 94,1 MB | 22,1 MB | 92,6 MB | 21,9 MB |
| 10-deutscher-automat-gebaut | 136,7 MB | 42,6 MB | 134,7 MB | 42,1 MB |
| **11a-tokenizers-modul-importiert** | 140,9 MB | **4,2 MB** | 138,9 MB | **4,2 MB** |
| **11b-erste-tokenizer-instanz** | 406,7 MB | **265,8 MB** | 404,2 MB | **265,2 MB** |
| **12a-splitter-gebaut** | 680,2 MB | **273,5 MB** | 677,5 MB | **273,4 MB** |
| **12b-erster-chunkerlauf-2** | 680,9 MB | **0,8 MB** | 678,4 MB | **0,9 MB** |
| **12c-zweiter-chunkerlauf-2** | 680,9 MB | **0,0 MB** | 678,4 MB | **0,0 MB** |
| 13-modell-objekt-gebaut-lazy | 680,9 MB | 0,0 MB | 678,4 MB | 0,0 MB |
| 14-erste-einbettung-gewichte-geladen | 1.076,3 MB | 395,4 MB | 1.079,2 MB | 400,8 MB |
| 15-lange-einbettung-aktivierungen | 1.116,2 MB | 39,9 MB | 1.105,6 MB | 26,4 MB |
| 16-zweite-tokenizer-instanz (informativ) | 1.332,8 MB | 216,6 MB | 1.330,8 MB | 225,2 MB |

Vorläufer der arm64-Spalten, emuliert
(`rohdaten/01-grundlast-fein-arm64-emuliert.txt`): Schritt 00 lag dort bei
43,2 MB, Schritt 11a bei 6,0 MB, 11b bei 246,6 MB, 12a bei 294,0 MB, 12b bei
3,5 MB und 12c bei 0,0 MB, die Endspitze an Schritt 16 bei 1.527,5 MB. Die
ganze Reihe steht in der Datei; sie ist nicht gelöscht, sondern umbenannt.

Die Gegenprobe gegen die grobe Messung stimmt auf der Nachkommastelle: amd64
zahlt für Schritt 11 gesamt 270,0 MB und für Schritt 12 gesamt 274,3 MB, die
Nachmessung auf nativem ARM 269,4 MB und 274,3 MB, und die native Feinmessung
auf ARM 269,4 MB und 274,3 MB. Es ist derselbe Vorgang, nur feiner
aufgeschrieben, und auf ARM ist das jetzt nicht mehr nur die Rundung, sondern
die Zahl in Kilobyte: 275.912 kB gegen 275.912 kB in Schritt 11 und 280.840
gegen 280.848 kB in Schritt 12.

**Die zwei Zeilen, die jetzt auffallen, und was von ihnen bleibt.** Die beiden
Spalten liegen so nah beieinander, dass zwei Zeilen herausstehen, und beide
gehören der Einbettung und nicht dem Tokenizer. Schritt 14 kostet auf ARM
400,8 MB gegen 395,4 MB der amd64-Datei; davon bleibt fast nichts übrig, denn
der amd64-Ast desselben Laufs zahlt 399,4 MB, der Abstand ist also ein
Unterschied zweier amd64-Läufe und nicht der Architektur. Schritt 15 kostet auf
ARM 26,4 MB gegen 39,9 MB und gegen 37,6 MB im amd64-Ast desselben Laufs; diese
gut 11 MB bleiben stehen. Es ist eine Beobachtung über die Aktivierungen von
onnxruntime, sie ist mit einem Lauf je Architektur nicht mehr als eine
Beobachtung, und die fünf Posten, um die es hier geht, sind davon nicht
berührt.

---

## 3. Was die Zahlen sagen

**Der Modulimport ist nicht das Problem.** `import tokenizers` kostet 4,2 MB auf
amd64 und 4,2 MB auf nativem arm64 (emulierter Vorläufer,
`rohdaten/01-grundlast-fein-arm64-emuliert.txt`: 6,0 MB). Wer die 269 MB von
Schritt 11 für Importkosten gehalten hat, hat sich um zwei Größenordnungen
geirrt. Der Import einer
Rust-Erweiterung ist eine Datei im Adressraum, nicht ein Datenmodell im Speicher.

**Die erste Tokenizer-Instanz kostet 265,8 MB.** Das ist die Antwort auf
Schritt 11. Die mitgelieferte `tokenizer.json` wiegt 17 MB auf der Platte und
trägt ein Vokabular von 250.002 Einträgen; die materialisierte Form davon, mit
allen Zeichenketten, Vereinigungsregeln und Nachschlagetabellen, ist rund das
Fünfzehnfache. Das ist eine Eigenschaft des Modells und nicht dieses Projekts:
`multilingual-e5-small` ist klein in den Gewichten und groß im Wortschatz.

**Die Hypothese aus der Recherche zu Schritt 12 ist bestätigt.** Der Bericht
`07-RESEARCH.md` hatte vermutet, die 274,3 MB seien zu einem großen Teil eine
**zweite Materialisierung desselben Tokenizers auf der Rust-Seite des
Splitters** und nicht der Preis der Chunkerläufe. Die Zerlegung entscheidet das
eindeutig:

- `12a-splitter-gebaut`, also `TextSplitter.from_huggingface_tokenizer`, kostet
  **273,5 MB** von 274,3 MB.
- Der erste Chunkerlauf über 3.720 Zeichen kostet **0,8 MB**, der zweite **0,0 MB**.

Der Bau des Splitters reicht den ganzen Tokenizer über die Sprachgrenze, und auf
der anderen Seite entsteht er noch einmal. Der Modulkopf von
`backend/src/findling/embed/chunker.py` sagt das seit Plan 06-04 voraus; die Zahl
dazu steht erst jetzt daneben.

**Der informative Schritt 16, und was er ausdrücklich nicht bedeutet.** Eine
zweite Tokenizer-Instanz aus derselben Datei kostet 216,6 MB. Damit ist der Preis
einer Instanz getrennt vom Preis des Modulimports sichtbar, und damit ist auch
sichtbar, dass die zwei Instanzen dieses Projekts zusammen deutlich mehr als eine
kosten. **Das ist eine Messung und kein Vorschlag.** Die zwei Instanzen sind eine
gesetzte Entscheidung (`.planning/STATE.md:159`): `Tokenizer.enable_truncation`
ist eine Eigenschaft des Objekts, eine geteilte Instanz hätte den
1.024-Token-Deckel aus D-01 still auf 512 halbiert, und das Verhalten ist vom
Projekt `semantic-text-splitter` ausdrücklich so dokumentiert. Eine hohe Zahl auf
Schritt 16 hebt diese Sperre nicht auf. Sie steht hier, damit ein späterer Leser
sie nicht selbst nachmisst und dann als Einladung liest.

**Wer diese 544 MB bezahlt.** Alle fünf Posten hängen an
`worker/poller.py::_wire_the_second_track`, und dieser Aufruf steht im ersten
Durchlauf des Pollers (`worker/poller.py:1420`). Die Leseseite fasst weder den
Splitter noch diesen Tokenizer an: `index/search.py::_rank_chunks` arbeitet über
`vectors.best_chunk_for` und kommt ohne beides aus. Ein Container, dessen zweite
Spur durchgelaufen ist und der seither nur noch sucht, trägt die 544 MB also
ohne Gegenwert. Das ist der Normalfall einer laufenden Installation und nicht
der Randfall.

---

## 4. Der Entscheid, gegen die Schwelle von 100 MB

Die Schwelle stand vor der Messung fest und steht in `07-03-PLAN.md`, Task 2:
**liegt die realistische Ersparnis eines faulen Baus unter 100 MB, wird nicht
gebaut**, und der faule Bau bekommt einen Eintrag in `deferred-items.md` statt
einer Zeile im Baum.

Die realistische Ersparnis ist die Summe der Posten, die ein Container, der nur
noch sucht, dann nicht mehr bezahlt. Das sind genau die fünf Kandidaten:

| Posten | amd64 | arm64 (nativ) |
|---|---:|---:|
| 11a-tokenizers-modul-importiert | 4,2 MB | 4,2 MB |
| 11b-erste-tokenizer-instanz | 265,8 MB | 265,2 MB |
| 12a-splitter-gebaut | 273,5 MB | 273,4 MB |
| 12b-erster-chunkerlauf | 0,8 MB | 0,9 MB |
| 12c-zweiter-chunkerlauf | 0,0 MB | 0,0 MB |
| **Summe** | **544,3 MB** | **543,7 MB** |

Vorläufer der arm64-Spalte, emuliert
(`rohdaten/01-grundlast-fein-arm64-emuliert.txt`): 6,0 MB, 246,6 MB, 294,0 MB,
3,5 MB, 0,0 MB, Summe **550,1 MB**. Gegen diese Summe ist der Entscheid unten
am 08.09.2026 gefallen.

Nicht dazu gehört der Vektorbestand: `open_vectors` bleibt eifrig, weil
`attach_vectors` und der Löschpfad der Zustandsdatenbank denselben Handle
brauchen (D-21). Er steht in keiner der fünf Zeilen und wird von keiner
verschoben. Nicht dazu gehören ferner die Modellgewichte: die werden schon heute
faul geladen und fallen erst mit Schritt 14 an.

> **Entschieden wurde am 08.09.2026 gegen 544,3 MB auf amd64 und 550,1 MB auf
> emuliertem arm64, gegen eine Schwelle von 100 MB. Die Ersparnis liegt beim
> Fünffachen der Schwelle. Der faule Bau wird gebaut.**

Die native arm64-Messung vom 09.09.2026 setzt an die Stelle der 550,1 MB
**543,7 MB** und ändert am Entscheid nichts: die Schwelle liegt bei 100 MB, und
beide Zahlen liegen beim Fünffachen davon. Sie ändert etwas anderes, und darum
ging es: die Erwartung, gegen die der Lauf auf der Box in Phase 10 seine
Grundlast hält, stammt jetzt von derselben Architektur wie die Box.

Der zweite Ast der Abbruchbedingung ist ebenfalls geprüft und trägt nicht: das
`one_load`-Tor ruft `_wire_the_second_track()` direkt und liest danach
`worker._model`, `worker._chunker` und `worker._vectors`
(`backend/src/findling/tools/one_load.py:220-247`). Ein fauler Chunker macht
diese Stelle rot, wenn sie unverändert bleibt, aber sie lässt sich mitziehen,
ohne eine der vier Erwartungen von eins zu lockern und ohne einen der drei
Rotbeweise anzufassen. Ein Tor, das für einen Speicherfix aufgeweicht wird, wäre
teurer als der Fix; hier muss es nicht aufgeweicht werden.

---

## 5. Was das für das RAM-Budget des Projekts heißt

Die Budget-Tabelle in `CLAUDE.md` kennt einen Posten "onnxruntime + e5-small
int8" mit "0 bei lazy_load, 250 bis 400 MB Spitze" und einen Posten "Tantivy
Writer". Einen Posten "Tokenizer und Splitter" kannte sie nicht. Gemessen ist
dieser Posten mit 544 MB **größer als das Modell**, und er war bis zu diesem
Plan nicht faul.

**Nachgetragen am 10.09.2026:** der Owner hat für die Ergänzung entschieden, und
die Zeile "Tokenizer und Splitter" steht seit Plan 10-07 in der Budget-Tabelle
von `CLAUDE.md`, mit "0 bei faulem Bau" im Ruhezustand und 544 MB als Spitze.
Die Vergleichsmessung auf der Box hat dieselben fünf Posten mit 542,8 MB
bestätigt (`docs/measurements/2026-09-vergleichsmessung-m7g/README.md`,
Abschnitt 5.2). **Die Frage ist entschieden und nicht mehr offen.**

---

## 6. Nach dem Bau: die tatsächliche Ersparnis, neben der erwarteten

Der faule Bau ist gebaut. `_wire_the_second_track` öffnet nur noch den
Vektorbestand und prüft mit zwei `stat`-Aufrufen, ob die Artefakte da sind;
Tokenizer, Splitter und Engine entstehen in `_build_the_cutter` an der ersten
Einbettungszeile.

Nachgemessen wird auf dem Weg, den der Arbeiter wirklich geht, und nicht mehr
auf dem Startweg: Skript 01 ruft `open_tokenizer` und `make_splitter` selbst
auf, misst also den Preis der beiden Posten und nicht die Entscheidung darüber,
wann er anfällt. Skript `02-nachmessung-fauler-bau.py` misst die Entscheidung.
Es läuft zweimal im selben Abbild, einmal gegen den veröffentlichten Code und
einmal gegen den geänderten, Rohdatei
`rohdaten/02-nachmessung-fauler-bau-amd64.txt`:

| Station | eifrig (Abbild) | faul (dieser Plan) |
|---|---:|---:|
| 00-leerer-prozess | 13,4 MB | 13,3 MB |
| 06-poller-importiert | 69,2 MB | 69,3 MB |
| **20-zweite-spur-verdrahtet** | **644,7 MB** | **69,9 MB** |
| 21-schneider-gebaut | 644,7 MB | 644,9 MB |

Der Zuwachs an Station 20, also das, was der erste Durchlauf des Pollers kostet,
fällt von **575,6 MB auf 0,6 MB**. Die 0,6 MB sind der Vektorbestand, der
absichtlich eifrig bleibt. **Die nachgemessene Ersparnis eines Containers, der
nur noch sucht, ist damit 575,0 MB**, gegen eine erwartete Ersparnis von
544,3 MB aus Abschnitt 4 und gegen eine Schwelle von 100 MB.

Die nachgemessene Zahl liegt 30,7 MB über der erwarteten, und das ist kein
Widerspruch, sondern ein Unterschied der Vorgeschichte: Skript 01 baut vorher
die Wortliste und den deutschen Automaten (64,7 MB), Skript 02 nicht, und die
Speicherverwaltung der C-Bibliothek gibt für dieselbe Anforderung verschieden
viel neu an das Betriebssystem zurück, je nachdem was vorher schon angefordert
war. Beide Zahlen sagen dasselbe: der Posten ist verschoben, und zwar ganz.

Was der Container an Station 21 zahlt, ist unverändert. Der faule Bau spart
nichts ein, er verschiebt: ein Container, dessen zweite Spur läuft, kommt auf
dieselbe Zahl wie vorher, nur später. Genau das war der Hebel, und die
Nachmessung bestätigt ihn an beiden Enden.
