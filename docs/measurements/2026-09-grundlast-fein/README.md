# Feinmessung der Grundlast, 08.09.2026

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

| Was | amd64 | arm64 |
|---|---|---|
| Abbild | `ghcr.io/street1983nk/findling_backend:dev` | dasselbe, arm64-Hälfte des Manifests |
| Digest | `sha256:8e1f64bd068819dc6447513bc6ee14c78c93d3a03cd5ffdfdf2aba8e95183a6b` | `sha256:8d49814ce631cd226da40785b8aaed0384b4ce933965a31b3bcdf236c9fa428b` |
| Architektur laut Prozess | `x86_64` | `aarch64` |
| Python im Abbild | 3.13.15 | 3.13.15 |
| `tokenizers` | 0.23.2 | 0.23.2 |
| Vokabular des Tokenizers | 250.002 Einträge | 250.002 Einträge |
| Ausführung | nativ, Docker, `--network none` | QEMU-Emulation, Docker, `--network none` |
| Rohdatei | `rohdaten/01-grundlast-fein-amd64.txt` | `rohdaten/01-grundlast-fein-arm64.txt` |

**Der arm64-Lauf ist emuliert, und das steht hier statt in einer Fußnote.** Für
diese Phase gibt es keine native ARM-Maschine: die AWS-Box ist angehalten, ihr
Datenträger ist teilweise zerstört, und sie gehört Phase 10. Die Emulation
verschiebt die Grundlinie sichtbar nach oben (Schritt 00 liegt bei 43,2 MB statt
bei 13,3 MB), weil der Übersetzer selbst im Prozess sitzt. Die **Zuwächse
zwischen zwei Schritten** verschiebt sie nicht nennenswert, und genau das lässt
sich hier nachprüfen statt behaupten:

| Posten | arm64 emuliert | arm64 nativ (Nachmessung, grob) | Abweichung |
|---|---|---|---|
| Schritt 11 gesamt (11a + 11b) | 252,6 MB | 269,4 MB | -16,8 MB |
| Schritt 12 gesamt (12a + 12b + 12c) | 297,5 MB | 274,3 MB | +23,2 MB |
| Beide zusammen | 550,1 MB | 543,7 MB | +6,4 MB |

Die Summe liegt 1,2 Prozent neben der nativen Messung derselben Schritte. Das
reicht für die Frage, um die es hier geht, und es reicht nicht für eine Zahl in
einer Store-Aussage. Der Messschritt in `.github/workflows/measure.yml` läuft
deshalb trotzdem in beiden Matrixästen: ein `workflow_dispatch` auf
`ubuntu-24.04-arm` liefert dieselbe Skriptdatei nativ, und die Rohdatei dieses
Laufs kann die emulierte hier ohne weitere Änderung ersetzen.

**Das Skript sendet nichts.** Es liest `/proc/self/status`, das Modellverzeichnis
und die Wortliste des Abbilds und gibt Zahlen aus. Der Text, mit dem gechunkt
wird, steht im Skript. Beide Läufe standen auf `--network none`.

---

## 2. Die Zahlen, Schritt für Schritt

Die Schritte 00 bis 10 und 13 bis 15 sind wortgleich aus
`docs/measurements/2026-09-05-semantiklauf-m7g/skripte/52-woher-die-grundlast.py`
übernommen. Neu sind die fünf Kandidaten dazwischen und der informative
Schritt 16.

| Schritt | amd64 RSS | amd64 Zuwachs | arm64 RSS | arm64 Zuwachs |
|---|---:|---:|---:|---:|
| 00-leerer-prozess | 13,3 MB | | 43,2 MB | |
| 01-config-importiert | 16,5 MB | 3,2 MB | 48,9 MB | 5,8 MB |
| 02-settings-gelesen | 16,7 MB | 0,1 MB | 48,9 MB | 0,0 MB |
| 03-index-module-importiert | 24,2 MB | 7,5 MB | 60,4 MB | 11,5 MB |
| 04-embed-module-importiert | 26,4 MB | 2,2 MB | 62,6 MB | 2,1 MB |
| 05-store-vectors-importiert | 28,0 MB | 1,6 MB | 63,9 MB | 1,4 MB |
| 06-poller-importiert | 69,7 MB | 41,6 MB | 117,4 MB | 53,5 MB |
| 07-api-resources-importiert | 69,7 MB | 0,0 MB | 117,4 MB | 0,0 MB |
| 08-findling-main-importiert | 71,9 MB | 2,3 MB | 120,7 MB | 3,2 MB |
| 09-wortliste-gelesen-276496 | 94,1 MB | 22,1 MB | 160,5 MB | 39,8 MB |
| 10-deutscher-automat-gebaut | 136,7 MB | 42,6 MB | 189,7 MB | 29,3 MB |
| **11a-tokenizers-modul-importiert** | 140,9 MB | **4,2 MB** | 195,7 MB | **6,0 MB** |
| **11b-erste-tokenizer-instanz** | 406,7 MB | **265,8 MB** | 442,4 MB | **246,6 MB** |
| **12a-splitter-gebaut** | 680,2 MB | **273,5 MB** | 736,3 MB | **294,0 MB** |
| **12b-erster-chunkerlauf-2** | 680,9 MB | **0,8 MB** | 739,8 MB | **3,5 MB** |
| **12c-zweiter-chunkerlauf-2** | 680,9 MB | **0,0 MB** | 739,8 MB | **0,0 MB** |
| 13-modell-objekt-gebaut-lazy | 680,9 MB | 0,0 MB | 739,8 MB | 0,0 MB |
| 14-erste-einbettung-gewichte-geladen | 1.076,3 MB | 395,4 MB | 1.248,7 MB | 508,9 MB |
| 15-lange-einbettung-aktivierungen | 1.116,2 MB | 39,9 MB | 1.291,8 MB | 43,1 MB |
| 16-zweite-tokenizer-instanz (informativ) | 1.332,8 MB | 216,6 MB | 1.527,5 MB | 235,6 MB |

Die Gegenprobe gegen die grobe Messung stimmt auf der Nachkommastelle: amd64
zahlt für Schritt 11 gesamt 270,0 MB und für Schritt 12 gesamt 274,3 MB, die
Nachmessung auf nativem ARM 269,4 MB und 274,3 MB. Es ist derselbe Vorgang, nur
feiner aufgeschrieben.

---

## 3. Was die Zahlen sagen

**Der Modulimport ist nicht das Problem.** `import tokenizers` kostet 4,2 MB auf
amd64 und 6,0 MB emuliert. Wer die 269 MB von Schritt 11 für Importkosten
gehalten hat, hat sich um zwei Größenordnungen geirrt. Der Import einer
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

| Posten | amd64 | arm64 emuliert |
|---|---:|---:|
| 11a-tokenizers-modul-importiert | 4,2 MB | 6,0 MB |
| 11b-erste-tokenizer-instanz | 265,8 MB | 246,6 MB |
| 12a-splitter-gebaut | 273,5 MB | 294,0 MB |
| 12b-erster-chunkerlauf | 0,8 MB | 3,5 MB |
| 12c-zweiter-chunkerlauf | 0,0 MB | 0,0 MB |
| **Summe** | **544,3 MB** | **550,1 MB** |

Nicht dazu gehört der Vektorbestand: `open_vectors` bleibt eifrig, weil
`attach_vectors` und der Löschpfad der Zustandsdatenbank denselben Handle
brauchen (D-21). Er steht in keiner der fünf Zeilen und wird von keiner
verschoben. Nicht dazu gehören ferner die Modellgewichte: die werden schon heute
faul geladen und fallen erst mit Schritt 14 an.

> **Entschieden wird gegen 544,3 MB auf amd64 und 550,1 MB auf emuliertem arm64,
> gegen eine Schwelle von 100 MB. Die Ersparnis liegt beim Fünffachen der
> Schwelle. Der faule Bau wird gebaut.**

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
Writer". Einen Posten "Tokenizer und Splitter" kennt sie nicht. Gemessen ist
dieser Posten mit 544 MB **größer als das Modell**, und er ist heute nicht
faul. Ob die Tabelle nachgezogen wird, entscheidet der Owner; dieser Bericht
ändert `CLAUDE.md` nicht.

---

## 6. Nach dem Bau

Die tatsächliche Ersparnis wird mit demselben Skript nachgemessen und hier neben
die erwartete Zahl gestellt. Siehe Abschnitt 7.
