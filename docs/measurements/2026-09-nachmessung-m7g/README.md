# Nachmessung auf der ARM-Box, 07.09.2026

Der Semantiklauf vom 05./06.09.2026
(`docs/measurements/2026-09-05-semantiklauf-m7g/`) hat die Zahl gemessen, die
seither in der Store-Aussage steht: **1.837,8 MB** anon-Spitze auf 4 GB ARM.
Plan 06.1-02 hat danach die zweite Modellinstanz beseitigt, Plan 06.1-04 die
Regressionsratsche auf amd64 dafür gebaut, Plan 06.1-21 die OCR-Vorgabe von
`deu+eng` auf `deu+eng+fra` gesetzt. Keiner der drei kann sagen, was davon auf
der Zielhardware ankommt.

Dieser Bericht sagt es. Er wiederholt die Form des Semantiklaufs, damit die
Zahlen vergleichbar sind statt nur nebeneinander zu stehen, und er stellt jede
Zahl neben ihre Entsprechung aus 06-11, auch die, die nicht besser geworden
ist.

---

## 1. Die Umgebung, und der Beweis des gemessenen Standes

| Was | Wert |
|---|---|
| Instanz | `i-06b1d913f5c6f669b`, m7g.large, 2 vCPU Graviton3, eu-central-1c |
| Speicher | 3,8 GiB nutzbar, `mem=4G` als Kernel-Parameter, zurückgelesen aus `/proc/cmdline` |
| Architektur | `aarch64`, Ubuntu 24.04 |
| Datenträger | `vol-04c5b59fe9417babd`, 60 GB gp3, `/mnt/findling`, 30 GB belegt |
| Nextcloud | 33.0.8.2, All-in-One, HaRP |
| Harte Speichergrenze des Containers | `memory.max = 2147483648` (2,0 GiB), aus der cgroup gelesen, nicht aus dem Docker-Klienten |
| Abbild | `ghcr.io/street1983nk/findling_backend:dev`, Digest `sha256:00111fd090f437a00678f6fc0a562807a5ad0b35082db235ea52ee86c63454c9`, `arm64`, gebaut 2026-09-06T23:27:11Z |
| Baumhash `backend/src/findling` im Abbild | `278fab52c60b7697a747ac4b434800bf9cdb5ed0e929c08e6c4929336ecd3d9a`, 53 Dateien |
| Baumhash `backend/src/findling` im Arbeitsbaum | `278fab52c60b7697a747ac4b434800bf9cdb5ed0e929c08e6c4929336ecd3d9a`, 53 Dateien |
| Baumhash `php` | `c203da5739592a8734da17cb6ad0394b3085f1c9f71ea556457c247ac4e62769`, 47 Dateien |
| OCR-Sprachen im Abbild | `deu`, `eng`, `fra`, dazu `osd`, aus `tesseract --list-langs` gelesen |
| Bestand auf dem Datenträger | 51.961 indexiert, 37 übersprungen, 145.854 Chunks, aus 06-11 weiterbenutzt |
| Laufzeit der Box | Start 2026-09-07T05:00:15Z, Anhalten siehe Abschnitt 12 |

**Das Abbild wurde nicht auf der Box gebaut, und das ist eine bewusste
Abweichung vom Plan.** Der Arbeitsbaum dieses Laufs trägt seit dem Commit, den
der Multi-Arch-Ablauf zuletzt gebaut hat (`9645799`), keine Änderung an
`backend/`; der Commit darüber (`93c021f`) berührt nur `.planning/STATE.md`. Das
Abbild in der Registry **ist** damit der Auslieferungsstand, und ein zweiter Bau
auf der Box hätte vierzig Minuten einer gedeckelten Laufzeit gekostet, um
denselben Code mit einem anderen Schichtenhash zu erzeugen. Was der Bericht
braucht, ist der Beweis, dass Abbild und Arbeitsbaum übereinstimmen, und dieser
Beweis ist der Baumhash. Er ist zeichengleich, in beiden Richtungen, über
dieselben 53 Dateien.

---

## 2. Die Kernaussage, in der Form aus D-H2

> Auf einer 4-GB-ARM-Box mit 51.961 indexierten Dokumenten und aktiver
> semantischer Suche hat der Container in diesem Lauf eine anon-Spitze von
> **1.812,7 MB** gegen eine harte Grenze von 2,0 GiB gehalten. `oom`, `oom_kill`
> und `oom_group_kill` stehen auf **null**. Die vierte Kennzahl `max`, die zählt,
> wie oft der Kern den Container gegen seine Grenze zurückdrängen musste, steht
> in diesem Lauf ebenfalls auf **null**; im Semantiklauf vom 05.09.2026 stand sie
> auf **2.796**.

Die vier Zahlen zusammen, wörtlich aus `memory.events` am Ende der letzten
Messphase gelesen:

```
low 0
high 0
max 0
oom 0
oom_kill 0
oom_group_kill 0
sock_throttled 0
```

Dazu `OOMKilled=false` und `RestartCount=0` aus `docker inspect`.

**Was `max = 0` bedeutet, in einem Satz.** Im Semantiklauf lag der Dateicache
des Index bei 1,5 bis 1,8 GB anon gegen die 2-GB-Grenze an, und der Kern hat
2.796 mal zurückgedrängt: keine Tötung, aber Arbeit, die der Container nicht
sieht und der Nutzer als Verzögerung merkt. In diesem Lauf ist das nicht ein
einziges Mal passiert. Das ist der eigentliche Gewinn dieses Laufs, nicht die
25,1 MB an der Spitze.

---

## 3. Die Grundlast, aufgeschlüsselt, neben der aus 06-11

Gemessen an einem Container, der über AppAPI frisch gestartet und bewaffnet
wurde und der noch keine Suche gesehen hat. Rohdaten: `rohdaten/63-grundlast.txt`.

| Posten | 06-11 | Nachmessung | Differenz |
|---|---|---|---|
| anon im Leerlauf, Modell nie geladen | 691,8 MB | **693,4 MB** | +1,6 MB |
| dasselbe nach einem Maschinenneustart | nicht getrennt gemessen | 687,9 MB | |
| Tokenizer gelesen | +268,8 MB | **+269,4 MB** | +0,6 MB |
| Chunker gebaut und gefahren | +272,8 MB | **+274,3 MB** | +1,5 MB |
| Gewichte bei der ersten Einbettung | +397,1 MB | **+391,9 MB** | -5,2 MB |
| Aktivierungen einer langen Einbettung | nicht getrennt gemessen | +26,4 MB | |
| deutscher Automat aus 276.496 Einträgen | | +42,1 MB | |
| Wortliste gelesen | | +21,9 MB | |
| Poller importiert | | +41,2 MB | |

**Die Grundlast hat der Fix nicht zurückgegeben, und das ist erwartbar.** Die
zweite Modellinstanz war faul geladen: sie entstand erst, wenn eine Einbettung
lief, also nicht im Leerlauf. Wer aus 06-11 gelesen hat, die 595 MB der
Semantik würden schrumpfen, hat den Posten an der falschen Stelle vermutet. Die
Grundlast ist im Rahmen der Messstreuung unverändert, und die Aufschlüsselung
weist an jeder einzelnen Stelle dieselbe Größenordnung aus wie 06-11. Das ist
zugleich die Gegenprobe darauf, dass hier dieselbe Sache gemessen wurde.

---

## 4. Die anon-Spitze, getrennt nach Phase, mit dem Zeitpunkt

| Phase | 06-11 | Nachmessung | Differenz |
|---|---|---|---|
| **Höchster anon-Wert des ganzen Laufs** | **1.837,8 MB** | **1.812,7 MB** | **-25,1 MB** |
| Zeitpunkt dieser Spitze | begann auf die Sekunde mit der ersten semantischen Suche | 2026-09-07T05:55:53Z, in der OCR-Phase | |
| Phase der ersten semantischen Suche | 1.837,8 MB | **1.125,2 MB** | -712,6 MB |
| anon unmittelbar vor der ersten Suche | | 694,3 MB | |
| anon unmittelbar nach der ersten Suche | | 1.116,6 MB | |
| Phase mit OCR | 1.562,7 MB | **1.812,7 MB** | +250,0 MB |
| `memory.peak` des Containers (mit Dateicache) | | 1.990,3 MB | |

### Der Zeitpunkt ist die Aussage, und er hat sich verschoben

Die Spitze aus 06-11 begann auf die Sekunde mit der ersten semantischen Suche.
Genau dieser Zusammenhang ist weg. Der Ablauf ist als Ereignis geprüft und
nicht angenommen: Skript `64-spitze.sh` liest `memory.events` und die drei
Speicherposten, fährt dann **eine einzige** Suche gegen einen Container, der
noch nie eine gesehen hat, und liest danach wieder.

```
erste-suche-vor  2026-09-07T05:35:56Z   anon 728018944   = 694,3 MB
erste-suche-nach 2026-09-07T05:35:59Z   anon 1170829312  = 1116,6 MB
```

Die erste semantische Suche kostet also **+422,3 MB**, und das sind die
Modellgewichte, die vorher faul lagen. Sie kostet nicht mehr die 1.837,8 MB von
06-11, weil dort zwei Instanzen dieser Gewichte entstanden sind. Die
Suchphase erreicht in diesem Lauf über alle Nebenläufigkeitsstufen hinweg
**1.125,2 MB** und keinen Punkt darüber.

### Die Spitze gehört jetzt der OCR-Phase, und die ist teurer geworden

Der höchste Wert des Laufs, 1.812,7 MB, entsteht in der OCR-Phase, nicht in der
Suche. Er liegt 250,0 MB **über** dem OCR-Wert aus 06-11. Zwei Gründe, und
beide gehören genannt:

1. **Die dritte OCR-Sprache.** `deu+eng+fra` statt `deu+eng` kostet je
   tesseract-Aufruf 15,5 MB mehr Spitzen-RSS (Abschnitt 8).
2. **Die Reihenfolge der Phasen ist nicht dieselbe.** In 06-11 lief die
   OCR-Phase, **bevor** die erste semantische Suche die Gewichte geladen hatte.
   In diesem Lauf lief sie danach, also auf einer Grundlinie, die die Gewichte
   schon trug: 1.136,1 MB unmittelbar vor der Charge. Die OCR selbst hat darauf
   677 MB aufgeschlagen; in 06-11 waren es rechnerisch rund 871 MB auf eine
   Grundlinie ohne Gewichte. Der Aufschlag der OCR ist also gesunken, die
   Grundlinie darunter gestiegen, und die Summe ist trotzdem höher.

**Die 250,0 MB sind kein Messfehler und werden hier nicht weggerechnet.** Wer
die Zahl 1.812,7 MB liest, liest den ungünstigsten Fall dieses Laufs: Semantik
geladen, drei OCR-Sprachen, OCR und Einbettung am selben Bestand. Genau dieser
Fall ist der, den die Store-Aussage tragen muss.

### Die OCR-Phase im Einzelnen

120 Dateien der Kategorie `scan_single` wurden über WebDAV in einen eigenen
Ordner geladen, also auf dem Weg, den ein Nutzer geht, und die Ereigniskette hat
sie aufgenommen. Rohdaten: `rohdaten/71-ocrphase.txt`, `rohdaten/ocrphase.csv`
(375 Messpunkte im Zweisekundentakt).

| Was | Wert |
|---|---|
| Hochgeladen | 120, alle mit HTTP 201 |
| Verdikt | 120 indexiert, 0 übersprungen, 0 fehlgeschlagen |
| Dauer der Phase | 2026-09-07T05:47:20Z bis 05:55:56Z, 8 min 36 s |
| Je Datei | rund 4,3 s, inklusive Abholen, OCR, Einbettung und Schreiben |
| anon vor der Charge | 1.136,1 MB |
| anon-Spitze | 1.812,7 MB um 05:55:53Z |
| `memory.events` danach | alle sieben Zähler auf null |

**Warum eine frische Charge und nicht der Bestand.** Die 51.961 Dokumente auf
dem Datenträger sind indexiert und tragen einen Inhaltshash, überspringen also
die ganze Kette. Eine OCR-Phase lässt sich nicht an Dateien messen, die nicht
wieder gelesen werden, und ein `findling:index --restart` hätte alle 51.961
gelesen: das ist der Neunzehnstundenlauf, den dieser Plan vermeidet.

---

## 5. Die Suchlast, und die Nebenläufigkeitszusage, die daraus folgt

Gemessen mit `scripts/ops/search_load.py` über die OCS-Route, also den Weg eines
Nutzers, mit zehn Runden je Stufe und 410 Anfragen insgesamt. Rohdaten:
`rohdaten/67-nebenlaeufigkeit.txt`, `rohdaten/67-stufe-*.json`,
`rohdaten/nebenlaeufigkeit.csv`.

| Nebenläufigkeit | Anfragen | Fehler | p50 | p95 | max | Budget 2.500 ms | anon | `memory.current` |
|---|---|---|---|---|---|---|---|---|
| 1 | 10 | 0 | 376,4 ms | **481,6 ms** | 481,6 ms | gehalten | 1.127,3 MB | 1.213,1 MB |
| 4 | 40 | 0 | 885,1 ms | **1.009,4 ms** | 1.058,8 ms | gehalten | 1.128,4 MB | 1.214,5 MB |
| 8 | 80 | 0 | 1.792,9 ms | **1.915,0 ms** | 2.042,2 ms | gehalten | 1.129,2 MB | 1.215,1 MB |
| 12 | 120 | 0 | 2.724,0 ms | **3.045,4 ms** | 3.117,7 ms | gerissen | 1.132,7 MB | 1.219,7 MB |
| 16 | 160 | 0 | 3.476,0 ms | **3.782,7 ms** | 4.070,2 ms | gerissen | 1.133,7 MB | 1.219,8 MB |

`memory.current` steht neben anon, weil ein Brute-Force-Scan den Vektorbestand
in den Seitencache derselben cgroup zieht und anon ihn nicht zählt. Der Abstand
zwischen den beiden Spalten ist über alle Stufen rund 86 MB und wächst mit der
Nebenläufigkeit nicht: der Scan liest denselben Bestand, egal wie viele gerade
lesen.

### Die Zusage

**Acht gleichzeitige Suchen.** Das ist die höchste Stufe, deren p95 unter dem
Budget von 2.500 ms bleibt (1.915 ms, also 76,6 Prozent des Budgets), und in der
alle drei Schadenszähler auf null geblieben sind. Ab zwölf reißt das Budget.

Die Zahl wurde **nach** der Messung festgelegt und nicht vorher; das war Open
Question 5 aus Plan 06.1-11, und `scripts/ops/search_load.py` hat in seinem
Modulkopf ausdrücklich nichts zugesagt, bis diese Reihe vorlag.

**Der Vorbehalt, und er ist nicht klein.** Die Unified Search fragt alle
Provider gleichzeitig und wartet auf alle. Damit setzt der PHP-Prozesspool der
Instanz genauso eine Grenze wie diese App, und dieser Pool ist in jeder
Installation anders groß. Acht ist eine Zahl über *diese* Box und *diese*
Instanz: zwei Graviton3-Kerne, All-in-One mit seinem eigenen Pool, 51.961
Dokumente, 145.854 Chunks. Eine Instanz mit mehr Kernen trägt mehr, eine mit
einem kleineren PHP-Pool weniger, und in beiden Fällen ist nicht diese App die
Grenze.

Zum Vergleich mit 06-11: dort wurde p95 1.129 ms während des Nachlaufs und
524 ms danach gemessen, sequenziell, also bei Nebenläufigkeit eins. Die
entsprechende Zahl dieses Laufs ist 481,6 ms.

---

## 6. `memory.events`, vollständig, an jeder Ablesestelle

Die Regel aus 06-11: **vor** jedem Eingriff lesen, sonst misst man den
Aufräumvorgang mit. Sie ist in jedem Skript dieses Laufs als erster Schritt
umgesetzt und hier vollständig belegt.

| Ablesestelle | low | high | max | oom | oom_kill | oom_group_kill | sock_throttled |
|---|---|---|---|---|---|---|---|
| Nach dem Maschinenstart, altes Abbild, vor jedem Eingriff | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Nach dem Wechsel auf das gemessene Abbild, vor der Grundlast | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Nach der Grundlastmessung | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Vor der ersten semantischen Suche | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Nach jeder Nebenläufigkeitsstufe (1, 4, 8, 12, 16) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Vor der OCR-Charge | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Nach der OCR-Charge | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Vergleich 06-11: `oom 0`, `oom_kill 0`, `oom_group_kill 0`, **`max 2796`**.

---

## 7. Der Endungsvergleich, nachgeholt

Seit 06-11 offen (Annahme A10), und nur solange möglich, wie der Datenträger mit
`state.db` existiert. Er gehört deshalb vor den Abbau und nicht danach.

**Der Weg zur Endung, ausdrücklich benannt.** Das Schema wurde nachgesehen,
bevor das Skript gebaut wurde. `files` trägt `path`, `state` und `reason` und
**keine** Endungsspalte, also kommt die Endung aus dem Pfad. Die Falle aus 06-11
ist damit auch geschlossen: die Spalte heißt `state` und nicht `verdict`, und
jedes Leseskript dieses Laufs wurde einmal trocken gegen das echte Schema
gefahren, bevor es scharf lief.

Hälfte eins ist aus dem Samen gerechnet, lokal, ohne Box
(`skripte/66-generator-endungen.py`, Samen `phase5-full`, 50.000 Dateien).
Hälfte zwei ist ein Lesen über `state.db` auf dem Datenträger
(`skripte/68-bestand-endungen.py`).

| Endung | Generator | indexiert | übersprungen | Summe | Abweichung |
|---|---|---|---|---|---|
| pdf | 32.552 | 32.552 | 0 | 32.552 | keine |
| xlsx | 3.345 | 3.345 | 0 | 3.345 | keine |
| pptx | 3.344 | 3.344 | 0 | 3.344 | keine |
| docx | 3.327 | 3.327 | 0 | 3.327 | keine |
| ods | 2.504 | 2.504 | 0 | 2.504 | keine |
| odt | 2.504 | 2.504 | 0 | 2.504 | keine |
| txt | 781 | 781 | 0 | 781 | keine |
| md | 775 | 775 | 0 | 775 | keine |
| csv | 768 | 748 | 20 | 768 | 20 mit Namen, siehe unten |
| jpg | 27 | 27 | 0 | 27 | keine |
| webp | 27 | 27 | 0 | 27 | keine |
| png | 23 | 23 | 0 | 23 | keine |
| tif | 23 | 23 | 0 | 23 | keine |
| **Summe** | **50.000** | **49.980** | **20** | **50.000** | |

**Bestanden.** Jede Endung des Generators taucht im Bestand mit genau der
erwarteten Anzahl auf, dreizehn Endungen, ohne eine einzige unerklärte
Abweichung.

### Jede Abweichung hat einen Namen

| Abweichung | Anzahl | Grund | Bewertung |
|---|---|---|---|
| `csv` übersprungen | 20 | `too_large` | **Absicht.** Das ist die Kategorie `oversize` des Generators: 20 CSV-Dateien bewusst über dem 50-MB-Deckel, damit `too_large` und der gesenkte Nenner des Deckungsgrads geprüft werden. |

### Die 37 Verdikte aus 06-11, vollständig zugeordnet

Der Bericht aus 06-11 nennt 37 übersprungene Dateien: 21 `too_large`, 14
`empty_text`, 2 `image_not_ocrable`. Im Lasttest-Korpus stehen davon nur 20. Die
restlichen 17 liegen ausserhalb: der Index dieser Box trägt neben dem
Lasttest-Korpus auch den Drill-Korpus aus Plan 05-21 und die Dateien, die eine
frische Nextcloud mitbringt, insgesamt 1.998 Zeilen. Über den gesamten Index
gelesen ergeben sich genau die 37:

| Grund | Endung | Anzahl | Woher |
|---|---|---|---|
| `too_large` | csv | 21 | 20 aus dem Lasttest-Korpus (`oversize`), 1 aus dem Drill-Korpus |
| `empty_text` | jpg | 14 | Drill-Korpus |
| `image_not_ocrable` | png | 2 | Drill-Korpus |
| **Summe** | | **37** | deckungsgleich mit 06-11 |

### Ein Nebenbefund, der in kein Kriterium fällt und trotzdem hierher gehört

Während der OCR-Charge der dreißig Dateien aus Abschnitt 9 stand in `state.db`
für 24 von ihnen das Verdikt `skipped:no_text_layer`, und wenige Minuten später
für alle dreißig `indexed`. `no_text_layer` ist also ein **vorübergehendes**
Verdikt: der erste Durchgang stellt fest, dass kein Textlayer da ist, legt die
Datei als OCR-Arbeit wieder vor, und erst der zweite Durchgang indexiert sie.
Wer die Verdikttabelle liest, während Arbeitsvorrat da ist, liest also
Zwischenstände. Der Endungsvergleich oben ist bei leerem Arbeitsvorrat gelesen
und davon nicht betroffen; der Befund steht hier, damit der nächste Leser nicht
über dieselbe Stelle stolpert.

---

## 8. Was die dritte OCR-Sprache kostet

Die Zahlen in `docs/ocr.md` sind am 01.09.2026 mit `-l deu+eng` auf einer
amd64-Entwicklungsmaschine entstanden, und Plan 06.1-21 hat sie bewusst nicht
umgeschrieben. Hier ist die Messung, auf der Zielhardware, mit derselben Seite,
denselben Engine-Optionen wie `findling.extract.ocr` (`--oem 1 --psm 3 -c
tessedit_do_invert=0`, `OMP_THREAD_LIMIT=1`) und derselben Auflösung (300 dpi,
gerendert mit pypdfium2 durch `findling.extract.raster`). Fünf Läufe je Satz,
abwechselnd, damit ein warm werdender Seitencache nicht auf einem der beiden
Sätze landet. Rohdaten: `rohdaten/70-ocr.txt`.

| Sprachsatz | Median | min | max | Spitzen-RSS des Kindprozesses | Zeichen |
|---|---|---|---|---|---|
| `deu+eng` | 3.473,7 ms | 3.467,7 ms | 3.511,8 ms | 92.804 kB = 90,6 MB | 3.472 |
| `deu+eng+fra` | **3.556,9 ms** | 3.547,3 ms | 3.585,8 ms | **108.644 kB = 106,1 MB** | 3.472 |
| **Aufschlag der dritten Sprache** | **+83,2 ms (+2,4 %)** | | | **+15.840 kB (+15,5 MB)** | 0 |

Drei Feststellungen dazu:

1. **Die dritte Sprache ist billig.** 2,4 Prozent Laufzeit und 15,5 MB
   Spitzen-RSS je Aufruf. Bei `INDEX_WORKERS=1` ist immer nur ein Aufruf
   unterwegs, also ist das der volle Preis und nicht der Preis je Kern.
2. **Sie ändert am Ergebnis dieser Seite nichts.** 3.472 Zeichen in beiden
   Sätzen, zeichengleich. Das ist erwartbar für eine deutsche Seite und sagt
   nichts über eine französische; die Seite dieses Tests ist eine deutsche.
3. **Die Sekunden je Seite von `docs/ocr.md` gelten auf dieser Box nicht.** Der
   Median dort ist 1.984 ms, hier 3.473 ms bei zwei Sprachen. Das ist der Preis
   der Zielhardware, nicht der Preis der dritten Sprache, und die alte Zahl
   behält deshalb ihr Datum und ihre Maschine.

---

## 9. Die Gegenprobe zu DI-05-36, an der echten Box

DI-05-36 lautete: nach jedem Start des Containers, der nicht von AppAPI kommt,
auch nach einem Neustart der Maschine, indexiert er nicht mehr; Heilung war
`occ app_api:app:disable` und `enable`. Plan 06.1-01 hat dagegen eine
Bewaffnungsmarke im eigenen Datenspeicher gebaut. Ob die auf echter Hardware
hält, ist die erste Messung dieses Laufs und keine Annahme.

**Die Vorher-Hälfte, am Abbild aus 06-11.** Die Box kam am 07.09. um 05:00:15Z
hoch. Der Container startete um 05:00:11Z mit dem Abbild `06-11-arm`, das vor
dem Fix liegt. Ergebnis: **null** `pass finished`-Zeilen, und das ganze
Protokoll dieses Starts steht in `rohdaten/60-bestand.txt`, damit die Null
lesbar ist statt behauptet.

**Die Nachher-Hälfte, am Abbild dieses Laufs.** Dreißig Dateien wurden als
Arbeitsvorrat vorgelegt, dann die Maschine neu gestartet, und danach wurde
**kein einziger** `occ`-Aufruf gemacht.

| Was | Ergebnis |
|---|---|
| `armed.marker` im Datenspeicher nach dem Maschinenneustart | vorhanden, unverändert vom 05:35 |
| Protokollzeile des Starts | `findling backend was enabled before this start, indexing continues without a switch` |
| Harte Grenze nach dem Maschinenneustart | `memory.max = 2147483648`, unverändert |
| `pass finished`-Zeilen, erste Beobachtung | 0, aus einem Grund, der nicht dem Produkt gehört, siehe unten |
| `pass finished`-Zeilen, nach Behebung dieses Grundes | 4 in 27 Sekunden, `claimed=30` in der ersten |
| Verdikt der dreißig | 30 indexiert, 0 übersprungen, 0 fehlgeschlagen |

**Der Grund für die erste Null, und er gehört der Messumgebung.** Der A-Record
`loadtest.infranode.dev` konnte in diesem Lauf nicht gesetzt werden (Abschnitt
11), deshalb war der Name in `/etc/hosts` der Box auf die Adresse des
Apache-Containers festgenagelt. Ein Maschinenneustart verteilt die Adressen der
Docker-Brücke neu: Apache wanderte von `172.18.0.6` auf `172.18.0.4`, der Pin
zeigte weiter auf die alte. Der Container hat das korrekt und laut gemeldet,

```
WARNING:findling.nc.queue:could not count the queue
WARNING:findling.worker.poller:the queue has not answered for 3 passes, backing
off to at most one attempt every 300 s; the Nextcloud half looks removed and the
container keeps answering searches
```

und danach weiter Suchen beantwortet, statt zu sterben. Nach Korrektur des Pins
und einem einfachen `docker restart`, wieder ohne `occ`-Aufruf, lief der Poller
sofort an und arbeitete die dreißig ab.

**Bewertung: DI-05-36 ist auf echter Hardware geschlossen.** Die Bewaffnung
überlebt den Maschinenneustart, belegt durch die Marke und die Protokollzeile,
und sie überlebt einen `docker restart`, belegt durch vier Durchgänge und
dreißig Verdikte. Was die erste Beobachtung verhindert hat, war mein Ersatz für
einen fehlenden DNS-Eintrag, und der Container hat auf diesen Ausfall genau so
reagiert, wie Plan 05-08 es vorsieht.

---

## 10. Der Plattendrill: entfallen, mit Beleg

Annahme A5 aus 06.1-RESEARCH lautete: ein GitHub-Runner darf ein Loop-Image
mounten. Plan 06.1-11 konnte sie nicht belegen und hat den Drill für den Fall
ihres Falls auf diese Box übergeben.

**A5 hat gehalten.** Der Ablauf `resilience.yml`, Lauf `34078858260` auf
`c636596`, meldet den Job `disk-full (stable34, 8.2)` als `success`, und das
Protokoll zeigt beides, was zählt:

```
/dev/loop0     909795328 24576 892993536   1% /home/runner/work/_temp/findling
dd: error writing '.../enospc-probe': No space left on device
the kernel refused the write past the end with ENOSPC, so the shortage below is
a real one
```

Also ein echtes Loop-Gerät unter dem Volumen und eine echte ENOSPC-Gegenprobe
davor. Der Drill läuft damit dort, wo er hingehört, bei jedem Lauf, und nicht
einmal auf einer gemieteten Box. Auf der Box wurde er deshalb **nicht**
gefahren.

---

## 11. Was nicht abgedeckt ist

1. **Der arm64-Installationslauf nach E-H5.** Siehe
   `docs/install-check.md`, Abschnitt zum arm64-Lauf, für den Stand und die
   Begründung.
2. **Der A-Record `loadtest.infranode.dev`.** Er zeigt weiter auf die alte
   Adresse `3.77.150.91`; die Box lief in diesem Lauf auf `3.70.17.245`. Die
   Zugangsdaten für die DNS-Zone lagen dieser Ausführung nicht vor. Ersatz war
   ein Eintrag in `/etc/hosts` der Box auf die Adresse des Apache-Containers,
   was für die Messung gleichwertig ist (dieselbe TLS-Kette, derselbe Apache,
   derselbe Weg durch AppAPI) und einmal Kosten verursacht hat, nachvollziehbar
   in Abschnitt 9.
3. **Eine OCR-Phase in Korpusgröße mit drei Sprachen.** Gemessen sind 120
   Scans in einer Charge und der Preis je Seite. Die 9.916 Scans von 06-11
   wurden nicht wiederholt; das wäre der Neunzehnstundenlauf.
4. **Der Deckungsgrad und die Trefferqualität.** Nicht Gegenstand dieses Laufs.
   Der Bestand ist der aus 06-11 und unverändert.
5. **Eine zweite Instanzform.** Alles hier ist All-in-One. Eine
   docker-compose-Instanz hat einen anderen PHP-Pool, und die
   Nebenläufigkeitszusage sagt das ausdrücklich.

---

## 12. Kosten und Verbleib der Box

Die Box wurde über `scripts/ops/aws_box.sh start` angefahren und über
`scripts/ops/aws_box.sh stop` angehalten, also nicht an dem Skript vorbei, das
die Kosten ausrechnet. Die beiden Unterbefehle gab es vorher nicht; sie sind in
diesem Plan entstanden, weil die Box genau zwischen ihnen lebt und jede Anfahrt
von Hand auch an der Kostenrechnung vorbeiging.

| Was | Wert |
|---|---|
| Start | 2026-09-07T05:00:15Z |
| Anhalten | siehe `~/.findling-loadtest/box.env`, Zeile `BOX_STOPPED_ISO` |
| Laufzeit und Kosten dieser Laufzeit | siehe `BOX_LAST_UPTIME_HOURS` und `BOX_LAST_UPTIME_COST_USD` in derselben Datei |
| Kosten angehalten | rund 0,31 USD je Tag, nur die Datenträger |
| Verbleib | **angehalten, nicht abgebaut.** Owner-Entscheid vom 07.09.2026: die Box bleibt bis nach der v1.1-Messung bestehen. Der Abbau ist Sache von Plan 06.1-19 und braucht dort eine eigene Freigabe (D-H3). |

Der Datenträger bleibt mit ihr erhalten, und damit Korpus, Index, `state.db`,
`vectors.db` und die Abbilder. Der Endungsvergleich aus Abschnitt 7 wäre nach
einem Abbau unmöglich; er ist deshalb hier gefahren und nicht später.

---

## 13. Die Skripte und die Rohdaten

Alle Skripte liegen unter `skripte/`, alle Rohdaten unter `rohdaten/`.

| Skript | Was es tut |
|---|---|
| `60-bestand.sh` | Der Zustand nach dem Maschinenstart, `memory.events` vor jedem Eingriff, die Vorher-Hälfte von DI-05-36 |
| `61-wechsel.sh` | Der Wechsel auf das Abbild dieses Laufs, der Baumhash-Beweis, die harte Grenze danach |
| `63-grundlast.sh` | Die Grundlast in drei Teilen, mit den beiden Hilfsskripten aus 06-11 unverändert |
| `64-spitze.sh` | Die erste semantische Suche als Ereignis, dann vier Nebenläufigkeitsstufen, mit Sampler |
| `66-generator-endungen.py` | Hälfte eins des Endungsvergleichs, aus dem Samen gerechnet, lokal |
| `67-nebenlaeufigkeit.sh` | Die belastbare Reihe über fünf Stufen und 410 Anfragen |
| `68-bestand-endungen.py` | Hälfte zwei des Endungsvergleichs, über `state.db` |
| `69-ocr-drei-sprachen.py` | Der Preis der dritten OCR-Sprache, je Seite, im Container |
| `70-ocr.sh` | Die Seite rendern und die beiden Sprachsätze gegeneinander fahren |
| `71-ocrphase.sh` | Die OCR-Phase an einer frischen Charge über WebDAV |
| `72-neustart.sh` | Die Nachher-Hälfte von DI-05-36, über einen Maschinenneustart |

| Rohdatei | Inhalt |
|---|---|
| `nachmessung.csv` | Die Reihe des Samplers um die erste Suche, Zweisekundentakt |
| `nebenlaeufigkeit.csv` | Die Reihe des Samplers über die fünf Stufen |
| `ocrphase.csv` | Die Reihe des Samplers über die OCR-Phase, 375 Messpunkte |
| `6*-*.json`, `6*-*.txt`, `7*-*.txt` | Die Ausgaben der Skripte, unverändert |

---

## 14. Was dieser Lauf nicht besser gemacht hat

Eine Nachmessung, die nur die günstigen Zahlen nennt, ist keine. Diese drei
stehen deshalb hier, in eigener Überschrift:

1. **Die Grundlast ist nicht gesunken.** 693,4 MB gegen 691,8 MB. Der Fix an der
   zweiten Modellinstanz gibt im Leerlauf nichts zurück, weil die zweite Instanz
   faul geladen war.
2. **Die OCR-Phase ist um 250,0 MB teurer geworden.** Drei Sprachen und eine
   Grundlinie mit geladenen Gewichten. Die Spitze des Laufs gehört jetzt ihr.
3. **Die Spitze ist nur um 25,1 MB gesunken.** 1.812,7 MB gegen 1.837,8 MB. Wer
   aus dem Fix an der zweiten Modellinstanz eine Entlastung um 276 MB an der
   Spitze erwartet hat, findet sie in der Suchphase (-712,6 MB) und nicht in der
   Gesamtspitze, weil die Gesamtspitze inzwischen an einer anderen Stelle
   entsteht.

Was der Lauf dafür belegt und was in 06-11 nicht so dastand: der Kern musste den
Container in diesem Lauf **nicht ein einziges Mal** gegen seine Grenze
zurückdrängen. `max` steht auf null, nach 2.796 im Semantiklauf.
