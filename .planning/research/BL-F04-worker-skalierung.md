# BL-F04 Vorab-Recherche (v1.4): Leistungsprofile und Worker-Skalierung

**Erstellt:** 2026-09-24
**Status:** Vorab-Recherche fuer den Milestone v1.4, VOR `/gsd:new-milestone`. Kein Plan, keine
Entscheidung, kein Code. Alles hier ist Lesearbeit am Stand von `main` vom 24.09.2026 plus den
committeten Messberichten.
**Geltung:** Beantwortet die sieben Fragen des Auftrags. Wo eine Zahl gemessen ist, steht die
Fundstelle daneben. Wo sie gerechnet ist, steht das Wort "gerechnet". Wo sie geraten ist, steht
ANNAHME.
**Nicht committet, nichts geaendert.** Parallel laeuft ein Executor auf Phase 18.

---

## 0. Auf einen Blick

- Der Flaschenhals der Erstindexierung ist die OCR-Spur, und zwar mit **85 Prozent der Laufzeit
  fuer 19 Prozent der Dateien** (gerechnet aus `docs/performance.md`, Abschnitt "Die beiden Spuren,
  getrennt gemessen": 39.285 s OCR gegen 6.842 s Text bei 9.525 gegen 40.524 Verdikten).
- Die Achse, auf der Findling wirklich skaliert, ist **die Kernzahl, nicht der Arbeitsspeicher**.
  Die OCR-Spur ist rechengebunden und laeuft je Seite mit genau einem Thread. RAM schaltet nur
  frei, was Kerne tragen koennen.
- `INDEX_WORKERS` ist heute kein Schalter, sondern eine Zusage in Schriftform: **keine einzige
  Stelle liest den Wert** (`backend/src/findling/config.py:81`, belegt durch die A/B-Messung in
  `docs/performance.md`, "Die Zusatzmessung: was ein zweiter Indexarbeiter bringt": 802 s gegen
  799 s, Unterschied null).
- Auf der 4-GB-Box ist **kein Platz fuer einen zweiten Arbeiter**: gemessene Spitze 1.812,7 MB
  gegen den Deckel von 2.048 MB, also 235 MB Luft, und ein zweiter Arbeiter kostet gerechnet
  250 bis 680 MB.
- Es gibt eine **billige erste Stufe**, die heute schon Geschwindigkeit bringt und keinen
  Nebenlaeufigkeits-Umbau braucht: die onnxruntime-Threads (heute hart auf 2), der
  Tantivy-Schreibhaufen und die Seiten-Parallelitaet innerhalb eines Dokuments.
- Und eine strukturelle Huerde, die vor jeder Settings-UI geloest werden muss: `config.settings()`
  ist `@lru_cache` (`backend/src/findling/config.py:1204`), alle Containerwerte kommen aus
  Umgebungsvariablen und sind fuer die Lebensdauer des Prozesses eingefroren. Ein Profil aus einer
  Nextcloud-Seite erreicht den Container heute auf keinem Weg ohne Neustart.

---

## 1. Flaschenhals-Befund

### 1.1 Wo die Zeit hingeht

Der ARM-Volllauf vom 04./05.09.2026 (m7g.large, 2 vCPU Graviton3, auf 4 GB gedeckelt, 50.049
Dateien) trennt die beiden Spuren am Zeitstempel und nicht rechnerisch
(`docs/performance.md`, "Die beiden Spuren, getrennt gemessen"):

| Abschnitt | Dauer | Verdikte | je Verdikt |
|---|---|---|---|
| Textspur und Crawl | 6.842 s | 40.524 | 0,169 s |
| reine OCR-Spur | 39.285 s | 9.525 | **4,133 s** |
| Summe | 46.127 s (12 h 49 min) | 50.049 | |

**85,2 Prozent der Uhr fuer 19,0 Prozent der Dateien** (gerechnet). Jede Verbesserung, die die
Textspur betrifft, kann bestenfalls 15 Prozent der Erstindexierung heben. Das ist die wichtigste
einzelne Zahl dieser Recherche.

### 1.2 Woraus die 4,13 s je OCR-Datei bestehen

| Posten | Wert | Fundstelle |
|---|---|---|
| tesseract je Seite, ARM, `deu+eng` | 3.473,7 ms Median | `docs/performance.md`, "Was die dritte OCR-Sprache kostet, auf dieser Box" |
| tesseract je Seite, ARM, `deu+eng+fra` (heutiger Default) | 3.556,9 ms Median | ebenda |
| tesseract je Seite, x86-Mietbox | 2.517 ms Median | `docs/performance.md`, "Der OCR-Faktor auf dieser Maschine" |
| Rasterung der Seite allein (x86) | 276 ms | ebenda |
| tesseract je Seite, amd64-Laptop | 1.984 ms Median | `docs/ocr.md`, Messung 3 |

Gerechnet: von 4,13 s je OCR-Datei entfallen rund 3,5 s auf tesseract, also **rund 84 Prozent
reine Rechenzeit in einem Kindprozess mit genau einem Thread**. Der Rest ist Abholen, Hashen,
Rastern, Schreiben, Quittieren. Daraus folgt unmittelbar: auf zwei Kernen bringt ein zweiter
Arbeiter fast nichts, weil zwei tesseract-Prozesse sich dieselben zwei Kerne teilen wuerden; der
ueberlappbare Anteil ist die restlichen 16 Prozent.

### 1.3 Die Einbettung als zweiter, kleinerer Posten

Der Semantik-Volllauf (`docs/performance.md`, "Der Semantik-Volllauf"):

- erste Spur 12 h 49 min ohne Semantik gegen **18 h 04 min mit Semantik**, also plus 41 Prozent,
  "weil `INDEX_WORKERS=1` beide Spuren durch denselben Arbeiter zieht".
- Einbettung neben der OCR: rund 43 Dokumente je Minute. Einbettung allein: rund 170 je Minute.
- Nachlauf nach dem Ende der ersten Spur: 52 Minuten.

Das ist der zweite Hebel und er ist billiger als er aussieht: die Einbettung ist Matrizenrechnung
in onnxruntime, sie skaliert mit Threads, und die Sitzung ist laut Modulkommentar ohne externe
Synchronisation aus mehreren Threads aufrufbar (`backend/src/findling/embed/model.py:703-707`).

### 1.4 Was NICHT der Flaschenhals ist

- **Der Tantivy-Commit.** Gemessen auf einer auf 2 MB/s gedrosselten Platte: p95 der Suche 0,196 ms
  im Leerlauf gegen 0,166 bis 0,216 ms unter Schreiblast, ununterscheidbar; die Drosselung senkt
  nur die Zahl der Commits im Fenster von 19 auf 12 (`backend/src/findling/config.py:200-214`).
- **Die Textspur je Datei.** 0,169 s je Verdikt einschliesslich Download ueber den Gateway.
- **Der Speicher der Einbettung.** Seit v1.1 haelt der Prozess genau eine Engine
  (`backend/src/findling/embed/engine.py`, Beleg in `docs/performance.md`, "Die eine Engine"),
  Gewichte 397,1 MB einmal. Mehr Arbeiter vervielfachen diesen Posten NICHT, wenn sie Threads im
  selben Prozess sind.

---

## 2. Was "mehr Worker" im heutigen Code heisst

### 2.1 Die heutige Form

Es gibt genau einen Nebenlaeufer. `Poller.run()` (`backend/src/findling/worker/poller.py:563`)
laeuft in einer Schleife, jede Runde ist `run_once()` (Zeile 585), und darin steht die eine
Schleife, an der alles haengt:

```
for job in claim.jobs:            # poller.py:666
    counted = await self._handle(job, ...)
```

Alles Blockierende darin geht durch `asyncio.to_thread`, aber **jedes `await` wird abgewartet**:
es ist ein Nebenlaeufer, kein Parallelismus. Die Reihenfolge einer Runde ist fest
(`poller.py:663-720`): 1. je Datei beurteilen, holen, extrahieren, an den Schreibpuffer, 2. ein
Commit fuer den ganzen Stapel, 3. Verdikte und Rechte, 3b. Uebergabe an die nachlaufenden Spuren
(OCR, embed), 4. Quittierung als letzter Schritt.

Die Extraktion laeuft in einem eigenen, langlebigen Kindprozess
(`backend/src/findling/extract/sandbox.py`, Startmethode `spawn`, `RLIMIT_AS` 512 MB, `setsid`
plus `killpg`), und tesseract ist ein Enkel davon
(`backend/src/findling/extract/ocr.py:196`). Ein "Arbeiter" ist also heute die Kette
Ereignisschleife, ein Sandbox-Kind, ein tesseract-Enkel je Seite.

### 2.2 Was strukturell zu aendern waere

| Baustein | heute | fuer N Arbeiter |
|---|---|---|
| Arbeitsschleife | `for job in claim.jobs` (`poller.py:666`) | `asyncio.TaskGroup` mit Semaphore, getrennt fuer OCR- und Textspur |
| Ergebnislisten | sechs Listen, von `_handle` per Anhaengen gefuellt (`poller.py:749-760`) | je Task ein Ergebnisobjekt, Zusammenfuehren nach dem Gather |
| Extraktionskind | genau eines, recycelt nach 200 Dateien (`config.py:230`) | N Kinder, je eigene Pipe, eigener Zaehler, eigenes `RLIMIT_AS` |
| Schreibpuffer | genau ein `IndexWriter`, OS-Sperre auf dem Verzeichnis (`index/writer.py:3-16`) | bleibt einer, aber `add()` braucht eine Sperre (unbewachte Zaehler in `writer.py:298,307,340`) |
| Zustands-DB | WAL, `busy_timeout` 10 s, `check_same_thread=False` (`store/repo.py:167,579-587`) | traegt parallele Schreiber, aber ungeprueft; heisse Meta-Zeilen sind die Kollisionsstelle |
| Abbruchpfade | `_GatewayDown` und `_DiskTight` verlassen die Schleife und geben den ganzen Stapel zurueck (`poller.py:667-684`) | Abbruchsemantik der Geschwister muss definiert werden, sonst halbe Stapel |
| Scratch-Dateien | `job-{queue_id}.part` (`poller.py:1371`) | schon kollisionsfrei, keine Aenderung noetig |

### 2.3 Invarianten, die dem entgegenstehen, und was sie wirklich verbieten

1. **Ein Tantivy-Writer je Indexverzeichnis.** Ein zweiter antwortet "Failed to acquire Lockfile:
   LockBusy" (gemessen, `index/writer.py:3-8`). Das ist KEIN Hindernis fuer mehr Arbeiter, solange
   alle denselben Writer benutzen; es verbietet nur, je Arbeiter einen eigenen zu oeffnen. Der
   Stapel-Commit bleibt die Dauerhaftigkeitszusage.
2. **IDX-08, OCR und Einbettung nie gleichzeitig.** Steht als Begruendung an
   `config.py:57-81`. Der Kern der Regel ist nicht "seriell", sondern "die beiden Spitzen duerfen
   sich auf 4 GB nicht treffen". Auf einer 8-GB-Box ist die Regel eine Einstellung und keine
   Physik. Sie muss aber als Default-Profil woertlich erhalten bleiben.
3. **Die Sperrfrist der Warteschlange.** `QueueMapper::LOCK_TIMEOUTS[ocr] = 1800`
   (`php/lib/Db/QueueMapper.php:136-142`), OCR-Anspruch `KIND_BATCH[ocr] = 2`
   (`php/lib/Service/QueueService.php:146-152`), und daraus abgeleitet die Obergrenze des
   Job-Budgets `OCR_JOB_SECONDS_MAX = 1800 // 2 - 2*60 = 780` (`config.py:444`). Wichtig fuer v1.4:
   **N parallele Arbeiter entspannen diese Rechnung, sie verschaerfen sie nicht.** Werden die zwei
   Zeilen eines Anspruchs gleichzeitig bearbeitet, faellt der Divisor weg. Umgekehrt: wer den
   OCR-Anspruch von 2 auf 2N erhoehen will, muss die PHP-Konstante mit anfassen, sie ist `private
   const`.
4. **Nur-Lesen.** Weder der Poller noch die Extraktion schreiben je eine Nutzerdatei
   (`extract/ocr.py`, Modulkopf, IDX-07). Nebenlaeufigkeit beruehrt das nicht.
5. **Mindestens einmal ausliefern, hoechstens einmal indexieren.** Haelt, solange die Quittierung
   der letzte Schritt bleibt und Verdikte erst nach dem Commit geschrieben werden. Im Volllauf
   ungeplant geprueft: zwei Zeilen mit `attempts = 3`, null Fehlschlaege
   (`docs/performance.md`, "Die eine Warnung aus dreizehn Stunden").
6. **`MAX_DELIVERIES`.** Eine Zeile, die zu oft zurueckkommt, endet als
   `failed(repeatedly_stuck)` (`php/lib/Service/QueueService.php:221-235`). Das ist der
   Schadenspfad eines falsch gesetzten Profils: OOM-Kill, Sperrfrist, Wiederauslieferung, und nach
   dem Deckel steht ein sauberes Dokument auf "fehlgeschlagen".

### 2.4 Der Befund, den die Messung schon hat

`docs/performance.md`, "Die Zusatzmessung: was ein zweiter Indexarbeiter bringt": zweihundert
einseitige Scans, Runde A mit `INDEX_WORKERS=1`, Runde B mit `INDEX_WORKERS=2` in einem
Wegwerf-Abbild. 802 s gegen 799 s, Textzeichen auf das Zeichen identisch. Fazit des Berichts:
"Eine Definition und zwei Kommentare. Keine einzige Stelle liest den Wert." Notiert als DI-05-37.

**Konsequenz fuer v1.4:** BL-F04 baut den Schalter erst, den die Nutzer schon zu sehen glauben.
Der Meilenstein muss diesen Befund ausdruecklich schliessen, sonst steht dieselbe Zeile in einem
Jahr noch einmal in einem Messbericht.

---

## 3. Stufe 1: was ohne Nebenlaeufigkeits-Umbau sofort skaliert

Nach erwartetem Gewinn geordnet, alles ohne Aenderung an der Schleifenform.

| # | Hebel | heute | Stellwert | erwarteter Gewinn | Risiko |
|---|---|---|---|---|---|
| S1 | onnxruntime `intra_op_num_threads` | hart 2 (`embed/model.py:113`, `_open_session` Zeile 337) | Profilwert, min(Kerne-1, 8) | Einbettung ist auf 2 Kernen mit 170 Dok/min allein gemessen; auf 8 Kernen ungemessen, aber der Posten ist reine Matrizenrechnung | gering, `inter_op` bleibt 1 |
| S2 | Seiten-Parallelitaet in EINEM Arbeiter | Seitenschleife seriell (`extract/ocr.py:154`) | 2 bis 4 gleichzeitige tesseract-Enkel, jeder weiter mit `OMP_THREAD_LIMIT=1` | bei mehrseitigen Scans nahe linear zur Kernzahl | mittel: Timeout je Seite, `killpg`-Baum, Speicher im Kind |
| S3 | Tantivy `heap_size` | 50 MB (`config.py:249`, env-faehig) | 128 MB nach der 8-GB-Schablone | klein, weniger Segmente und Merges | gering |
| S4 | Tantivy `num_threads` | hart 1 (`index/writer.py:176`) | 2 | klein, Commit ist nicht der Flaschenhals | gering |
| S5 | `FINDLING_EMBED_BATCH_SIZE` | 2 (`config.py:598`), Bereich 1 bis 32 | 8 | **gemessen null** auf aarch64 bei 2 Kernen (Welle 0, Messung B: Batch 2 und 8 liegen 1,3 Prozent auseinander, `config.py:591-598`); auf mehr Kernen ungemessen | gering, kostet Aktivierungsspeicher |
| S6 | `FINDLING_OCR_MAX_PAGES` | 30 (`config.py:400`), Bereich 1 bis 500 | 100 | kein Zeitgewinn, sondern Vollstaendigkeit: lange Scans bleiben nicht bei Seite 30 stehen | gering, siehe Rechnung unten |
| S7 | `FINDLING_BATCH_FILES` / `BATCH_MAX_BYTES` | 32 / 64 MB (`config.py:215-216`) | unveraendert | keiner, das ist Anspruchsgroesse und keine Rechenleistung | - |

### 3.1 Der Hebel, den man NICHT ziehen darf

**tesseract mehr Threads geben.** `OMP_THREAD_LIMIT=1` (`extract/ocr.py:73`) ist doppelt begruendet
und beides ist gemessen (`docs/ocr.md`, Messungen 2 und 3):

- Ein Thread ist **18 Prozent schneller** als die Vorgabe, obwohl zwoelf Kerne sichtbar sind
  (Median 1.984 ms gegen 2.424 ms).
- Ohne die Variable stirbt dieselbe Seite bei 128 MB Adressraum mit Exitcode 134, weil OpenMP je
  Thread Stack und Arena reserviert und `RLIMIT_AS` virtuellen Adressraum zaehlt.

Die Variable ist Teil der Speicherzusage. Der richtige Weg zu mehr OCR-Leistung sind **mehr
Prozesse mit je einem Thread**, nicht mehr Threads je Prozess.

### 3.2 Rechnung zu S6, damit der Seitendeckel nicht zum Stolperstein wird

Bei 3,5 s je Seite (ARM, gemessen) und dem weichen Job-Budget von 600 s (`config.py:411`) sind
rechnerisch **171 Seiten** drin, bevor das Budget greift. Die harte Elterndeadline liegt bei
660 s, zwei Jobs eines Anspruchs also bei 1.320 s gegen die Sperrfrist von 1.800 s. Ein Deckel von
100 Seiten ist damit heute schon zulaessig, ohne eine einzige andere Zahl anzufassen. Der Grund
fuer die 30 steht in `docs/ocr.md`, "Abweichung von STACK.md", und stammt aus der alten
900-s-Rechnung; seit `LOCK_TIMEOUTS[ocr] = 1800` ist die Begruendung ueberholt. **Das gehoert
nachgerechnet und dann im Profil "Leistung" gehoben.**

### 3.3 Zu S2, die eine ehrliche Einschraenkung

Der Messkorpus besteht aus 9.900 einseitigen Scans und 100 mehrseitigen zu 8 Seiten
(`docs/performance.md`, "Die Prognose fuer den Volllauf"). **Auf diesem Korpus wuerde
Seiten-Parallelitaet fast nichts zeigen.** Echte Instanzen haben mehrseitige Scans, aber die
Messung dazu braucht einen anderen Korpus. Wer S2 baut, muss den Korpus vorher umbauen, sonst misst
er sein eigenes Testmaterial und nicht den Hebel.

---

## 4. Stufe 2: der echte Mehr-Worker-Umbau

### 4.1 Die Form, die dazu passt

Nicht ein Prozess-Pool, sondern **getrennte Schleusen in derselben Ereignisschleife**:

- `ocr_slots`: `asyncio.Semaphore(n_ocr)`. Jeder Slot haelt ein eigenes Sandbox-Kind. Das ist der
  teure Posten, RAM und Kerne haengen daran.
- `text_slots`: `asyncio.Semaphore(n_text)`. Billig, ueberwiegend Warten auf den Gateway. Darf
  deutlich hoeher stehen als `n_ocr`.
- `embed`: bleibt an der geteilten Engine, ohne eigene Schleuse. Die Sitzung ist threadsicher
  (`embed/model.py:703-707`), die Gewichte werden nicht vervielfacht. **Das ist die Dividende von
  v1.1 (EFF-01/02) und der Grund, warum mehr Arbeiter hier nicht 400 MB je Stueck kosten.**

Ein Prozess-Pool waere der falsche Schnitt: jeder Prozess braeuchte eigene Modellgewichte
(gemessen 397,1 MB, `docs/performance.md`, "Wo die 1,4 GB Unterschied herkommen") und koennte den
einen Tantivy-Writer nicht teilen. Genau dieser Fehler ist im Semantiklauf schon einmal passiert,
innerhalb eines Prozesses, und hat 276 MB dauerhaft gekostet.

### 4.2 Was zusaetzlich zu bauen ist

1. **Ein Speicherwaechter.** Der Container liest sein eigenes `memory.current` und drosselt die
   OCR-Schleuse, wenn der Abstand zur Grenze unter eine Reserve faellt. Ohne das ist jedes Profil
   eine Wette. Das Muster gibt es schon als Skript (`scripts/ops/rss_sampler.sh:128-134`, liest
   `memory.current` und `anon` aus `memory.stat`), nur nicht im Container.
2. **Eine Sperre um `IndexBatchWriter.add()`** oder ein einzelner Schreib-Thread mit Warteschlange.
3. **N Sandbox-Kinder** mit je eigenem Recycling-Zaehler.
4. **Ein Nebenlaeufigkeitstest der Zustands-DB**: N Threads, dieselben Meta-Zeilen, gegen
   `busy_timeout` 10 s.
5. **Abbruchsemantik**: `_GatewayDown` muss weiterhin den ganzen Anspruch unbeurteilt
   zurueckgeben, auch wenn drei Geschwister-Tasks gerade mitten in einer Seite stehen.

### 4.3 Was der Umbau NICHT anfassen darf

Reihenfolge Commit, Verdikte, Uebergabe, Quittierung (`poller.py:678-718`). Diese vier Schritte
sind die Zusage "mindestens einmal ausliefern, hoechstens einmal indexieren" und sie sind unter
Last geprueft. Sie bleiben sequenziell am Ende einer Runde, parallel wird nur der Teil davor.

---

## 5. Profil-Rechnungen

### 5.1 Die gemessene Ausgangslage (4 GB, ARM, AIO, Semantik an)

Alles aus `docs/performance.md`, Nachmessung vom 07.09.2026 und Semantiklauf vom 05.09.2026:

| Posten | Wert | Art |
|---|---|---|
| nutzbarer Speicher der Box | 3.814 MB | gemessen (`free -m`) |
| Grundlast AIO plus HaRP | 345 MB | gemessen |
| Grenzwert fuer den Findling-Container | 2.048 MB | Festlegung |
| Rest fuer Kernel und Seitencache | 1.421 MB | gerechnet |
| Grundlast Findling im Leerlauf (seit v1.1) | 103,2 MB | gemessen |
| Modellgewichte, einmal je Prozess | 397,1 MB (Ladesprung 422,3 MB) | gemessen |
| Grundlinie mit geladenen Gewichten | 1.136,1 MB | gemessen |
| **hoechstes `anon` des ganzen Laufs (OCR-Phase)** | **1.812,7 MB** | gemessen |
| Luft bis zum Deckel | **235,3 MB** | gerechnet |
| `memory.events max` | 0 (nach dem Fix), vorher 2.796 | gemessen |

Einzelposten eines OCR-Arbeiters, soweit getrennt gemessen:

| Posten | Wert | Fundstelle |
|---|---|---|
| tesseract-Kindprozess, Spitzen-RSS je Seite, `deu+eng` | 90,6 MB | "Was die dritte OCR-Sprache kostet" |
| dasselbe mit `deu+eng+fra` | 106,1 MB | ebenda |
| Sandbox-Kind (Python, ohne Gewichte) | 69 MB | "Die eine Engine" |
| Rasterung pypdfium2 | 50 bis 150 MB | STACK-Tabelle in CLAUDE.md, ungemessen |
| Adressraum je Enkel, gemessener Bedarf | unter 128 MB bei 512 MB Limit | `docs/ocr.md`, Messung 2 |

**Der Aufschlag der ganzen OCR-Phase gegen die Grundlinie ist 1.812,7 minus 1.136,1 = 676,6 MB**
(gerechnet), waehrend die Summe der einzeln gemessenen Posten nur 225 bis 325 MB ergibt. Die
Differenz ist nicht aufgeschluesselt. Deshalb steht in allen Profilrechnungen unten ein **Band von
250 bis 680 MB je zusaetzlichem Arbeiter**, und deshalb ist die Messung je Stufe eine
Vorbedingung und keine Formalie. Das ist genau die Stelle, die der Owner mit "RAM-Messung je
Stufe, BEVOR die Settings-UI ihn anbietet" gemeint hat.

### 5.2 Die drei Profile, durchgerechnet

Gerechnet, nicht gemessen. `A` ist der optimistische Rand des Bandes (250 MB je Arbeiter), `B` der
pessimistische (680 MB).

**Sparsam, 4 GB, 2 Kerne (heutiger Default, unveraendert)**

| Groesse | Wert |
|---|---|
| OCR-Slots / Text-Slots | 1 / 1 |
| onnx-Threads | 2 |
| Tantivy heap / threads | 50 MB / 1 |
| Embed-Batch | 2 |
| OCR: Seiten / DPI / s je Seite / s je Job | 30 / 300 / 30 / 600 |
| erwartete Spitze | 1.812,7 MB gemessen |
| Deckel | 2.048 MB |
| Laufzeit 50k Dateien | 18 h 04 min gemessen (mit Semantik) |

**Standard, 8 GB, 4 Kerne**

| Groesse | Wert |
|---|---|
| OCR-Slots / Text-Slots | 2 / 4 |
| onnx-Threads | 3 |
| Tantivy heap / threads | 128 MB / 2 |
| Embed-Batch | 8 |
| OCR: Seiten / DPI | 60 / 300 |
| erwartete Spitze | A 2,06 GB, B 2,49 GB (gerechnet) |
| empfohlener Deckel | 3,0 GB |
| Rest fuer Kernel und Seitencache bei 7,8 GB nutzbar | 4,5 GB |
| erwartete Laufzeit | OCR-Spur rund halbiert, Gesamt rund 8 bis 11 h (gerechnet, ANNAHME: 4 echte Kerne) |

**Leistung, 16 GB, 8 Kerne**

| Groesse | Wert |
|---|---|
| OCR-Slots / Text-Slots | 4 / 8 |
| onnx-Threads | 4 |
| Tantivy heap / threads | 256 MB / 2 |
| Embed-Batch | 8 |
| OCR: Seiten / DPI | 100 / 300 |
| erwartete Spitze | A 2,56 GB, B 3,85 GB (gerechnet) |
| empfohlener Deckel | 5,0 GB |
| erwartete Laufzeit | OCR-Spur rund geviertelt, Gesamt rund 4 bis 6 h (gerechnet) |

### 5.3 Die Kernregel, die ueber allem steht

```
OCR-Slots = min( (verfuegbare Kerne) - 1 ,  (Deckel - Grundlinie - Reserve) / Aufschlag_je_Arbeiter )
```

Die linke Haelfte ist die Geschwindigkeitsgrenze, die rechte die Speichergrenze. **Heute kennt der
Container keine der beiden Eingangsgroessen.** Beide sind billig zu beschaffen (Abschnitt 6), und
solange sie fehlen, waere jedes Profil eine Zahl, die der Admin raet.

Zwei Faelle, die die Regel sofort richtig behandelt und eine reine RAM-Staffelung falsch machen
wuerde:

- 16 GB, 2 Kerne (haeufig bei kleinen VPS-Tarifen): ein OCR-Slot, weil mehr nichts bringt.
  Gestuetzt auf die A/B-Messung aus 2.4.
- 4 GB, 8 Kerne (ARM-Board, Pi 5 mit 8 GB oder aehnlich): weiter ein OCR-Slot, weil der Speicher
  fehlt, aber onnx-Threads hoch.

---

## 6. Vorab-Pruefung: was "Test vor dem Speichern" messbar pruefen kann

### 6.1 Was der Container ueber sich selbst herausfinden kann

| Frage | Weg | Bemerkung |
|---|---|---|
| Wie viel RAM darf ich? | `/sys/fs/cgroup/memory.max` (cgroup v2). Steht dort `max`, gibt es keine Grenze, dann `/proc/meminfo` `MemTotal` | im Container mit cgroup-Namensraum liegt die Datei direkt in der Wurzel, nicht unter dem Host-Pfad, den `scripts/ops/rss_sampler.sh:81-89` von aussen bauen muss |
| cgroup v1 als Rueckfall | `/sys/fs/cgroup/memory/memory.limit_in_bytes` | ANNAHME der Relevanz: AIO-Installationen auf aktuellen Distributionen fahren v2, aber der Rueckfall kostet drei Zeilen |
| Wie viel brauche ich gerade? | `/sys/fs/cgroup/memory.current` plus `anon` aus `memory.stat` | genau die Methode des Projekts, begruendet in `scripts/ops/rss_sampler.sh:4-22`: `anon` und nicht `current`, weil der Seitencache des mmap-Index mitzaehlt |
| Wurde ich schon zurueckgedraengt? | `memory.events`, Feld `max` | im Semantiklauf 2.796, nach dem Fix 0. Ein Profil, das `max` wieder hochtreibt, ist zu gross, auch ohne OOM |
| Wie viele Kerne darf ich? | `os.process_cpu_count()` (neu in Python 3.13) fuer die Affinitaetsmaske, zusaetzlich `/sys/fs/cgroup/cpu.max` fuer die Quote (`"max 100000"` = unbegrenzt, `"200000 100000"` = 2 Kerne). Das Minimum nehmen | `os.cpu_count()` meldet die Hostkerne und ist im Container die falsche Zahl |

Beleg fuer `os.process_cpu_count()`: Python 3.13 What's New, "Add `process_cpu_count()` function to
get the number of logical CPU cores usable by the calling thread of the current process", beide
Funktionen ueberschreibbar via `PYTHON_CPU_COUNT` und `-X cpu_count`
(docs.python.org/3/whatsnew/3.13.html, abgerufen 24.09.2026). Ob die Funktion die cgroup-Quote
beruecksichtigt oder nur die Affinitaetsmaske, ist dort nicht ausdruecklich gesagt: **deshalb
`cpu.max` zusaetzlich lesen und das Minimum nehmen.**

### 6.2 Die vier Proben, die eine Vorab-Pruefung fahren kann

1. **Grenze und Kerne lesen.** Kostet nichts, beantwortet die haeufigste Fehlkonfiguration allein
   (Profil "Leistung" auf einer Zwei-Kern-Box).
2. **Eine Probeseite OCR mit den neuen Werten.** Rastern mit dem gewaehlten DPI, `read_page()`
   aufrufen (`extract/ocr.py:177`), Zeit und Spitzen-RSS des Enkels melden. Das ist woertlich das
   Rezept aus `docs/ocr.md`, Messung 3, nur zur Laufzeit. Der Container hat dafuer schon alles:
   eine Testseite muesste ins Abbild (ANNAHME: heute keine drin, `testdata/` erreicht das Abbild
   nicht).
3. **Modell laden und einen Satz einbetten.** Beantwortet "laedt das Modell ueberhaupt" und liefert
   den `anon`-Sprung. **Vorsicht, das ist die teuerste Probe:** der Ladesprung ist gemessen
   422,3 MB und bleibt danach im Prozess stehen. Auf einer engen Box waere die Pruefung selbst das
   Risiko. Ausweg: nur pruefen, wenn die Engine ohnehin geladen ist, oder danach die
   Leerlauf-Entladung anstossen, die gemessen rund 100 Prozent des Modellspeichers zurueckgibt
   (v1.2, 376 MB nach 75 s, `.planning/MILESTONES.md`, v1.2).
4. **Die Rechnung aus 5.3 mit den eben gelesenen Zahlen** und ein Verdikt in drei Stufen: passt,
   passt knapp, passt nicht. Kein stilles Abschneiden, sondern eine benannte Ablehnung, wie
   `config.py` es schon fuer jede Umgebungsvariable tut.

### 6.3 Es gibt schon eine Messkultur, an die das andockt

Die Admin-Seite rechnet ihre Schaetzung bereits aus gemessenen Raten statt aus Konstanten hoch,
ueber `GET /rates`, getrennt nach Text- und OCR-Spur, und beschriftet ungemessene Werte als
"Startwert, wird gemessen" (`docs/admin-page.md`, "Die Schaetzung: was sie ist und was nicht").
Eine Vorab-Pruefung ist dieselbe Haltung, nur vor der Aenderung statt danach.

### 6.4 Die strukturelle Huerde, die vor der UI geloest werden muss

Das ist der wichtigste nicht offensichtliche Befund dieser Recherche.

- `config.settings()` ist `@lru_cache(maxsize=1)` (`config.py:1204-1210`), ausdruecklich mit der
  Begruendung, dass sich die Umgebung waehrend des Prozesses nicht aendert.
- Alle Containerwerte kommen aus Umgebungsvariablen, deklariert in
  `backend/appinfo/info.xml:337-473`, dort auch der Satz "These are the settings, and there is no
  settings page".
- Der Container ruft die PHP-Seite nur fuer Warteschlange, Mounts und Dateien
  (`backend/src/findling/nc/client.py:327-490`). **Es gibt keine Route, ueber die Admin-Einstellungen
  in den Container kommen.** Die vier Schalter der Admin-Seite wirken PHP-seitig im Crawl, deshalb
  reicht dort "der naechste Lauf haelt sich daran" (`docs/admin-page.md`, "Die vier Schalter").

Daraus folgen genau zwei Wege:

| Weg | Form | Kosten | Folge |
|---|---|---|---|
| A | Eine Umgebungsvariable `FINDLING_PROFILE`, gesetzt in den ExApp-Einstellungen von AppAPI | sehr klein, passt ins heutige Modell | Neustart des Containers noetig, Vorab-Pruefung nur als Text ohne Messung |
| B | Neue OCS-Route auf der PHP-Seite (Muster `queues/documents/stats`), der Container fragt einmal je Runde, plus eine Probe-Route im Container fuer die Vorab-Pruefung | mittel, beruehrt `config.settings()` | Live-Aenderung, echte Vorab-Pruefung, echte Settings-Seite |

**Weg B ist ohnehin teilweise noetig**, denn die Vorab-Pruefung kann nur im Container laufen: nur
er hat tesseract, das Modell und die cgroup-Dateien. Eine Route braucht es also so oder so. Wenn
sie da ist, ist der Rest von B klein. Empfehlung: **B, mit der Regel, dass eine gesetzte
Umgebungsvariable das Profil ueberstimmt** (sonst gibt es zwei Wahrheiten, und das ist genau der
Fehler, den `config.py` im Modulkopf als "operational fault in slow motion" beschreibt).

### 6.5 Was die Admin-Seite dabei nicht verlieren darf

`docs/admin-page.md`, "Was die Seite bewusst nicht kann": "Keinen Erweitert-Bereich mit zwanzig
Optionen. Die Zielgruppe sind Selbsthoster und kleine Organisationen, und die Optionsflut ist einer
der Gruende, an denen das Vorgaengerprojekt gescheitert ist. Es bleibt bei vier Schaltern."

Ein Profil-Auswahlfeld ist **ein** Bedienelement, kein Erweitert-Bereich. Die Einzelwerte dahinter
bleiben Umgebungsvariablen und stehen nicht auf der Seite. Damit bleibt ADM-04 gewahrt. Wer
stattdessen acht Schieberegler baut, verletzt die Entscheidung.

---

## 7. Konkurrenz-Blick

| Projekt | Wie es skaliert | Was davon passt |
|---|---|---|
| **paperless-ngx** | `PAPERLESS_TASK_WORKERS` (Celery-Prozesse) mal `PAPERLESS_THREADS_PER_WORKER`; ohne Angabe `max(floor(cpu_count / TASK_WORKERS), 1)` Threads je Worker, damit Worker mal Threads die Kernzahl nicht uebersteigt. Die Doku nennt ausdruecklich, dass jeder Worker die ganze Anwendung noch einmal in den Speicher laedt, und empfiehlt auf kleinen Systemen 2 Worker mit 1 Thread | Die **Formel** passt und ist genau die Regel aus 5.3. Die **Form** passt nicht: separate Prozesse wuerden bei uns die Modellgewichte vervielfachen (gemessen 397,1 MB je Instanz), und der Tantivy-Writer laesst sich nicht teilen. Also Threads und Subprozesse statt Worker-Prozesse |
| **Nextcloud context_chat_backend** | Konfiguration in `config.yaml` unter `$APP_PERSISTENT_STORAGE`, Abschnitt `embedding` mit `workers` und `request_timeout`; Anforderung laut Admin-Handbuch 2 GB RAM plus 500 MB je gleichzeitiger Anfrage, 4 und mehr Kerne fuer das Embedding-Modell, AVX Pflicht | Zwei Dinge sind uebernehmenswert: die **additive Formel** "Grundlast plus X je Nebenlaeufigkeit" als Form der Store-Aussage, und die Ablage der Konfiguration im **persistenten Verzeichnis** statt in Umgebungsvariablen. Letzteres ist ein dritter Weg zu 6.4 und umgeht den Neustart, ohne eine OCS-Route zu brauchen. Nicht uebernehmenswert: die Hardware-Huerde selbst, das ist der Markt, den Findling gerade unterbietet |

Quellenlage: beide Angaben aus WebSearch gegen die jeweilige offizielle Doku, nicht gegen den
Quelltext geprueft. Konfidenz MEDIUM.

---

## 8. Risiken

| # | Risiko | Bewertung | Gegenmittel |
|---|---|---|---|
| R1 | **OOM-Kill des Containers durch ein zu grosses Profil** | Der Schaden ist nicht der Neustart, sondern die Kette danach: gesperrte Zeilen laufen in die Sperrfrist (bis 1.800 s), zaehlen einen Versuch, und nach `MAX_DELIVERIES` enden gesunde Dokumente als `failed(repeatedly_stuck)` (`QueueService.php:221-235`). Der Neustart selbst ist geprueft, Drill 1 `docker kill` mitten im OCR-Lauf auf beiden Architekturen | Vorab-Pruefung als Pflicht, Speicherwaechter zur Laufzeit, Profil faellt bei wiederholtem `memory.events max` selbsttaetig eine Stufe zurueck |
| R2 | **Stilles Zurueckdraengen statt Toetung** | Gemessen: 2.796 Rueckforderungen an der Grenze im Semantiklauf, ohne einen einzigen Kill, spuerbar nur als Verzoegerung | `memory.events max` ist die Kennzahl, die ein Profil bewerten muss, nicht nur `oom_kill` |
| R3 | **SQLite-Sperren bei parallelen Schreibern** | WAL und `busy_timeout` 10 s sind gesetzt (`store/repo.py:167,579-587`), parallele Schreiber sind unter WAL zulaessig (`repo.py:1433`), aber nie unter Last gefahren | Nebenlaeufigkeitstest mit N Threads auf dieselben Meta-Zeilen als Wave-0-Aufgabe |
| R4 | **Tantivy-Einzel-Writer** | Harte Grenze, kein Umgehungsweg. `add()` fuehrt unbewachte Zaehler (`writer.py:298,307,340`) | Eine Sperre oder ein Schreib-Thread; Test, der zwei Writer gleichzeitig oeffnet und `IndexLockedError` erwartet, gibt es schon der Form nach (`writer.py:125`) |
| R5 | **Windows und WSL2 sind nicht testbar** | `RLIMIT_AS`, `setsid`, `killpg` und die cgroup-Dateien sind Linux; die Sandbox importiert `resource` nur auf POSIX (`extract/sandbox.py:79`) | Alles Neue gehoert in den Container und in den arm64-Ast der CI (`.github/workflows/resilience.yml`, Job `measurements`). Auf der Entwicklermaschine bleibt nur der Einheitstest |
| R6 | **Der Default rutscht** | Das 4-GB-Versprechen ist eine Store-Aussage mit einer Zahl (1.812,7 MB). Ein Profil-Umbau, der den Default um 50 MB verschiebt, macht die Store-Aussage falsch | Ein Test, der das Profil "Sparsam" Wert fuer Wert gegen die heutigen Konstanten pinnt, so wie heute `backend/tests/test_config.py` die Eins von `INDEX_WORKERS` bewacht |
| R7 | **Zwei Wahrheiten ueber die Konfiguration** | Profil aus der UI und Umgebungsvariable koennen sich widersprechen | Vorrangregel schriftlich festlegen und testen; der Modulkopf von `config.py` verlangt das ausdruecklich |
| R8 | **Modellwechsel (Teil 2 von BL-F04)** | fp32 statt int8 sind 470.268.510 gegen 118.101.091 Byte (`config.py`, Kommentar an `INDEX_WORKERS`), also rund plus 350 MB dauerhaft, PLUS ein Vektor-Reindex, den die Umbau-Mechanik aus Phase 18 nicht abdeckt | Eigene Phase, nach der Worker-Arbeit, nicht in denselben Schnitt |
| R9 | **Messkorpus passt nicht zur Frage** | 9.900 von 10.000 Scans sind einseitig; Seiten-Parallelitaet und hohe Seitendeckel sind daran nicht messbar | Korpus vor der Messphase um mehrseitige Scans ergaenzen, sonst misst die Messung das Testmaterial |

---

## 9. Empfehlung fuer den Milestone-Schnitt

Vier Phasen, in dieser Reihenfolge. Der Schnitt ist so gelegt, dass nach **jeder** Phase etwas
Lieferbares dasteht und die teuerste Phase erst nach ihrer eigenen Messung kommt.

**Phase 1: Profil-Geruest und die billigen Hebel (kein Nebenlaeufigkeits-Umbau)**
Profil als Objekt, drei Stufen, "Sparsam" ist Wert fuer Wert der heutige Zustand und per Test
gepinnt. Die zwei hart verdrahteten Zahlen werden Profilwerte: onnx-Threads (`embed/model.py:113`)
und Tantivy `num_threads` (`index/writer.py:176`). Dazu Heap und Embed-Batch aus dem Profil.
Erkennung von Kernen und Speichergrenze im Container. Der Weg, auf dem das Profil in den Container
kommt (Entscheidung A gegen B gegen die context-chat-Variante Konfigurationsdatei im persistenten
Verzeichnis), ist ein **Owner-Tor am Phasenanfang**. Ergebnis: auf jeder Box mit mehr als zwei
Kernen wird die Einbettung schneller, ohne ein einziges Nebenlaeufigkeitsrisiko.

**Phase 2: Settings-Seite mit Vorab-Pruefung**
Ein Auswahlfeld, kein Erweitert-Bereich. Probe-Route im Container mit den vier Proben aus 6.2.
Verdikt in drei Stufen, Ablehnung benannt. Damit ist die Nutzerfrage aus dem Reddit-Kommentar
beantwortet, auch bevor es mehr Arbeiter gibt.

**Phase 3: Messphase auf einer groesseren Box (Vorbedingung des Owners)**
Eine bezahlte Anfahrt nach dem Muster von Phase 15, aber auf 8 und 16 Kernen. Zu messen:
(a) der Aufschlag je zusaetzlichem Arbeiter, um das Band von 250 bis 680 MB auf eine Zahl zu
bringen, (b) die Wirkung der onnx-Threads oberhalb von 2, (c) Seiten-Parallelitaet an einem Korpus
mit mehrseitigen Scans. **Kill-Kriterium vorher aufschreiben:** liegt der Aufschlag je Arbeiter
ueber 500 MB oder der Gewinn auf vier Kernen unter Faktor 1,5, wird Phase 4 gestrichen und der
Meilenstein liefert Stufe 1 allein. Das waere immer noch ein Produkt, das schneller wird, wenn die
Hardware groesser ist.

**Phase 4: der echte Mehr-Worker-Umbau**
Getrennte Schleusen fuer OCR und Text, Sperre um den Schreibpuffer, N Sandbox-Kinder,
Speicherwaechter, Abbruchsemantik, PHP-seitig der OCR-Anspruch. Erst nach Phase 3, mit gemessenen
Zahlen im Profil.

**Ausdruecklich nicht in diesem Meilenstein:** die Modellwahl (R8). Sie haengt an einem
Vektor-Reindex und ist ein eigenes Vorhaben.

**Nebenbei mitzunehmen:** DI-05-37 schliessen (dass `INDEX_WORKERS` heute nichts steuert, steht
nirgends), und die veraltete Fundstelle `config.py:57` in `docs/performance.md` auf 81 berichtigen.

---

## 10. Annahmen-Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | Der Aufschlag je zusaetzlichem Arbeiter liegt zwischen 250 und 680 MB | 5.1, 5.2 | Die ganze Profilrechnung. Genau deshalb ist Phase 3 Vorbedingung |
| A2 | Eine 8-GB-Box hat 4 Kerne, eine 16-GB-Box 8 | 5.2 | Die Zeitprognosen. Die Regel aus 5.3 faengt den Fall aber ab, weil sie Kerne liest statt sie anzunehmen |
| A3 | pypdfium2-Rasterung kostet 50 bis 150 MB | 5.1 | Kleiner Posten, aus CLAUDE.md uebernommen und dort ungemessen |
| A4 | AIO-Installationen fahren cgroup v2 | 6.1 | Nur der Rueckfallpfad, drei Zeilen |
| A5 | Im Abbild liegt heute keine Testseite fuer eine OCR-Probe | 6.2 | Eine Datei mehr im Abbild |
| A6 | `os.process_cpu_count()` liest die Affinitaetsmaske, nicht zwingend die cgroup-Quote | 6.1 | Abgefangen, weil `cpu.max` zusaetzlich gelesen wird |
| A7 | Mehrseitige Scans sind in echten Instanzen haeufig genug, dass Seiten-Parallelitaet lohnt | 3.3 | S2 waere umsonst gebaut. Vor dem Bau am Korpus einer echten Instanz pruefen |
| A8 | Die Angaben zu paperless-ngx und context_chat stimmen so, wie die Doku sie beschreibt | 7 | Nur Orientierung, keine Entscheidung haengt daran |

---

## 11. Offene Fragen an den Owner

1. **Wie kommt das Profil in den Container?** Umgebungsvariable mit Neustart (A), OCS-Route mit
   Live-Uebernahme (B), oder Konfigurationsdatei im persistenten Verzeichnis nach dem Muster von
   context_chat (C). Das ist die Weiche, an der der Aufwand der ganzen Phase 1 haengt.
2. **Darf der Deckel steigen?** Die 2,0 GB sind eine Festlegung aus der 4-GB-Rechnung. Fuer groessere
   Boxen muss die Store-Aussage zwei Zahlen tragen, eine je Profil. Das beruehrt den Store-Text.
3. **Wieviel Messgeld?** Phase 3 ist eine bezahlte Anfahrt auf eine groessere Maschine als bisher.
   Der Deckel gehoert vorher festgelegt, wie bei Phase 15.
4. **Bekommt "Sparsam" einen neuen Namen?** Wenn es drei Profile gibt, heisst das heutige
   Verhalten nicht mehr "der Default", sondern "eine von drei Stufen". Die Store-Beschreibung muss
   das tragen, ohne dass 4-GB-Nutzer glauben, sie bekaemen jetzt weniger.

---

## 12. Quellen

**Primaer, Quelltext (HIGH), Stand 24.09.2026**

- `backend/src/findling/config.py`: 81 (`INDEX_WORKERS`, Begruendung 57 bis 81), 200-216
  (`BATCH_FILES`, Commit-Messung), 225 (`EXTRACT_ADDRESS_SPACE_BYTES`), 230, 249
  (`WRITER_HEAP_BYTES`), 400-455 (OCR-Deckel und Bereiche, `OCR_JOB_SECONDS_MAX`), 591-599
  (`EMBED_BATCH_SIZE` samt Welle-0-Begruendung), 1204-1210 (`@lru_cache` auf `settings()`)
- `backend/src/findling/worker/poller.py`: 563, 585, 646, 663-720, 749, 1371, 1491
- `backend/src/findling/extract/ocr.py`: 56-73 (`_ENGINE_OPTIONS`, `_THREAD_LIMIT`), 141-175
  (Seitenschleife), 177-212 (`read_page`)
- `backend/src/findling/extract/sandbox.py`: Modulkopf, 58-59, 79-105, 219-231, 421-431
- `backend/src/findling/embed/model.py`: 109-113 (`THREADS`), 319-340 (`_open_session`), 703-707
  (Threadsicherheit der Sitzung)
- `backend/src/findling/embed/engine.py`: Halter `_ENGINE`, `shared_model()`
- `backend/src/findling/index/writer.py`: 3-21, 125, 135-180, 298, 307, 340, 411-440
- `backend/src/findling/store/repo.py`: 167, 526-588, 1433-1501
- `backend/src/findling/nc/client.py`: 327-490
- `backend/appinfo/info.xml`: 330-473 (Umgebungsvariablen, "there is no settings page")
- `php/lib/Db/QueueMapper.php`: 75-142 (`KINDS`, `LOCK_TIMEOUT`, `LOCK_TIMEOUTS`)
- `php/lib/Service/QueueService.php`: 120-235 (`KIND_BATCH`, Claim-Schleife, `MAX_DELIVERIES`)
- `scripts/ops/rss_sampler.sh`: 4-22, 81-89, 116-146

**Primaer, Messberichte des Projekts (HIGH)**

- `docs/performance.md`: "Der OCR-Faktor auf dieser Maschine", "Der Grenzwert, jetzt aus gemessenen
  Groessen", "Die beiden Spuren, getrennt gemessen", "Die eine Warnung aus dreizehn Stunden", "Die
  Zusatzmessung: was ein zweiter Indexarbeiter bringt", "Der Semantik-Volllauf", "Wo die 1,4 GB
  Unterschied herkommen", "Die Nachmessung", "Die Spitze hat den Besitzer gewechselt", "Die
  Nebenlaeufigkeitszusage", "Was die dritte OCR-Sprache kostet", "Die eine Engine"
- `docs/ocr.md`: "Die Deckel-Kaskade", "Abweichung von STACK.md", Messung 2 (Adressraum), Messung 3
  (`OMP_THREAD_LIMIT`)
- `docs/admin-page.md`: "Die Schaetzung", "Die vier Schalter", "Was die Seite bewusst nicht kann"
- `.planning/MILESTONES.md`: v1.1 (geteilte Engine, 691,8 auf 103,2 MB), v1.2 (Entladung, 376 MB
  nach 75 s)
- `.planning/BACKLOG.md`: BL-F04, Owner-Zielbild vom 24.09.2026

**Sekundaer (MEDIUM), abgerufen 24.09.2026**

- docs.python.org/3/whatsnew/3.13.html, `os.process_cpu_count()`, `PYTHON_CPU_COUNT`
- docs.paperless-ngx.com/configuration/ und /setup/, `PAPERLESS_TASK_WORKERS`,
  `PAPERLESS_THREADS_PER_WORKER`
- github.com/nextcloud/context_chat_backend README und
  docs.nextcloud.com Admin-Handbuch "App: Context Chat", `config.yaml`, `embedding.workers`,
  Hardware-Anforderungen

**Konfidenz**

| Bereich | Stufe | Grund |
|---|---|---|
| Flaschenhals-Befund | HIGH | zwei unabhaengige Messungen auf der Zielarchitektur, plus die A/B-Gegenprobe |
| Heutige Codeform und Invarianten | HIGH | am Quelltext gelesen, Zeilen genannt |
| Stufe-1-Hebel | MEDIUM-HIGH | Wirkung der onnx-Threads oberhalb von 2 ist ungemessen |
| Profil-Rechnungen | LOW-MEDIUM | der Aufschlag je Arbeiter ist ein Band, kein Wert. Genau dafuer ist Phase 3 da |
| Vorab-Pruefung | MEDIUM-HIGH | die Mechanik ist belegt, die Probeseite und die Kostenfrage der Modellprobe sind ungemessen |
| Konkurrenz-Blick | MEDIUM | offizielle Doku, kein Quelltextabgleich |

**Gueltig bis:** rund 30 Tage, oder bis Phase 18/19 die Analysekette oder den Indexpfad aendern.
